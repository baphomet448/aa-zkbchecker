"""App Tasks"""

# Standard Library
import logging
import time

# Third Party
from celery import shared_task
from celery.exceptions import Ignore

from zkbchecker.esi_client import resolve_ids, resolve_names
from zkbchecker import check_control
from zkbchecker.triggers import evaluate_triggers
from zkbchecker.zkb_client import (
    get_excluded_ship_ids,
    get_kills,
    get_losses,
    get_stats,
    get_suspicious_entities,
)

logger = logging.getLogger(__name__)

ZKB_REQUEST_DELAY_SECONDS = 1


def _check_character(
    name: str,
    character_id: int,
    excluded_ship_ids: set[int],
    suspicious_entities: tuple[dict[int, str], dict[int, str]],
) -> dict:
    """Run the zKillboard checks for one resolved character and return
    the finished result row. Raises on network errors; the caller
    decides how to report a failed character."""
    stats = get_stats(character_id)
    time.sleep(ZKB_REQUEST_DELAY_SECONDS)
    losses = get_losses(character_id, excluded_ship_ids)
    time.sleep(ZKB_REQUEST_DELAY_SECONDS)
    kills = get_kills(character_id, suspicious_entities)

    triggers = evaluate_triggers(stats, losses["all_ships"], kills["victim_ships"])

    ids_to_resolve = {stats["corporation_id"], stats["alliance_id"]}
    for ship in stats["all_ships_used"][:3] + losses["top_ships"]:
        ids_to_resolve.add(ship["shipTypeID"])
    ids_to_resolve.discard(0)

    names_by_id = {}
    if ids_to_resolve:
        for entity in resolve_ids(list(ids_to_resolve)):
            names_by_id[entity["id"]] = entity["name"]

    def with_names(ships: list[dict]) -> list[dict]:
        return [
            {
                "name": names_by_id.get(s["shipTypeID"], str(s["shipTypeID"])),
                "count": s["kills"],
            }
            for s in ships
        ]

    return {
        # zKillboard has no profile (and so no name) for characters
        # without any killboard activity, fall back to the ESI name.
        "name": stats["name"] or name,
        "found": True,
        "corporation_name": names_by_id.get(stats["corporation_id"], ""),
        "alliance_name": names_by_id.get(stats["alliance_id"], ""),
        "birthday": stats["birthday"],
        "kills_total": stats["kills_total"],
        "losses_total": stats["losses_total"],
        "solo_kills": stats["solo_kills"],
        "solo_losses": stats["solo_losses"],
        "danger_ratio": stats["danger_ratio"],
        "gang_ratio": stats["gang_ratio"],
        "last_kill_date": kills["last_kill_date"],
        "last_loss_date": losses["last_loss_date"],
        "top_ships_kills": with_names(stats["all_ships_used"][:3]),
        "top_ships_losses": with_names(losses["top_ships"]),
        "triggers": triggers,
        "suspicious_alliance": kills["suspicious_alliance"],
    }


def _run_check(task, names: list[str], watched: bool) -> list[dict]:
    total = len(names)

    # Config lists are read from the DB once per batch, not once per
    # character. Edits made in the settings page while a batch is
    # running apply from the next batch.
    excluded_ship_ids = get_excluded_ship_ids()
    suspicious_entities = get_suspicious_entities()

    resolved = resolve_names(names)
    resolved_by_name_lower = {entry["name"].lower(): entry for entry in resolved}

    results: list[dict] = []

    def progress_meta() -> dict:
        return {"current": len(results), "total": total, "results": results}

    task.update_state(state="PROGRESS", meta=progress_meta())

    for index, name in enumerate(names, start=1):
        if watched and check_control.should_stop(task.request.id):
            logger.info(
                "Check %s interrupted after %s of %s characters",
                task.request.id, len(results), total,
            )
            # Custom final state; Ignore stops Celery from overwriting it.
            task.update_state(state="CANCELLED", meta=progress_meta())
            raise Ignore()

        entry = resolved_by_name_lower.get(name.lower())

        if not entry:
            results.append({"name": name, "found": False})
        else:
            try:
                results.append(
                    _check_character(
                        entry["name"],
                        entry["id"],
                        excluded_ship_ids,
                        suspicious_entities,
                    )
                )
            except Exception:
                logger.exception(
                    "zKillboard check failed for %s (id=%s)", name, entry["id"]
                )
                results.append({"name": name, "found": True, "error": True})

            # Pacing towards zKillboard, not needed after the last one.
            if index < total:
                time.sleep(ZKB_REQUEST_DELAY_SECONDS)

        task.update_state(state="PROGRESS", meta=progress_meta())

    return results


@shared_task(bind=True)
def check_characters_task(
    self, names: list[str], user_id: int | None = None
) -> list[dict]:
    """Run the full ZKB check for a list of character names and return
    a list of result dicts, one per name, in the same order.

    While running, every PROGRESS update carries all rows finished so
    far, so the browser can show them as they arrive.

    A check started from the web page (user_id given) is watched: it
    stops by itself when the page asks for it or stops polling. Direct
    calls without user_id (shell, tests) are never interrupted.
    """
    watched = user_id is not None
    try:
        return _run_check(self, names, watched)
    finally:
        if watched:
            check_control.release(user_id, self.request.id)