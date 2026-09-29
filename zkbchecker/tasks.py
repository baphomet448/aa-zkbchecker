"""App Tasks"""

# Standard Library
import logging
import time

# Third Party
from celery import shared_task

from zkbchecker.esi_client import resolve_names, resolve_ids
from zkbchecker.zkb_client import get_stats, get_losses, get_kills
from zkbchecker.triggers import evaluate_triggers

logger = logging.getLogger(__name__)

ZKB_REQUEST_DELAY_SECONDS = 1


@shared_task(bind=True)
def check_characters_task(self, names: list[str]) -> list[dict]:
    """Run the full ZKB check for a list of character names and return
    a list of result dicts, one per name, ready for template/export use.
    """
    total = len(names)
    resolved = resolve_names(names)
    resolved_by_name_lower = {entry["name"].lower(): entry for entry in resolved}

    results = []
    for index, name in enumerate(names, start=1):
        self.update_state(state="PROGRESS", meta={"current": index, "total": total})

        entry = resolved_by_name_lower.get(name.lower())
        if not entry:
            results.append({"name": name, "found": False})
            continue

        character_id = entry["id"]

        try:
            stats = get_stats(character_id)
            time.sleep(ZKB_REQUEST_DELAY_SECONDS)
            losses = get_losses(character_id)
            time.sleep(ZKB_REQUEST_DELAY_SECONDS)
            kills = get_kills(character_id)
        except Exception:
            logger.exception("zKillboard check failed for %s (id=%s)", name, character_id)
            results.append({"name": name, "found": True, "error": True})
            continue

        triggers = evaluate_triggers(stats, losses["all_ships"], kills["victim_ships"])

        ids_to_resolve = {stats["corporation_id"], stats["alliance_id"]}
        for ship in stats["all_ships_used"][:3] + losses["top_ships"]:
            ids_to_resolve.add(ship["shipTypeID"])
        ids_to_resolve.discard(0)

        names_by_id = {}
        if ids_to_resolve:
            for e in resolve_ids(list(ids_to_resolve)):
                names_by_id[e["id"]] = e["name"]

        top_ships_kills = [
            {"name": names_by_id.get(s["shipTypeID"], str(s["shipTypeID"])), "count": s["kills"]}
            for s in stats["all_ships_used"][:3]
        ]
        top_ships_losses = [
            {"name": names_by_id.get(s["shipTypeID"], str(s["shipTypeID"])), "count": s["kills"]}
            for s in losses["top_ships"]
        ]

        results.append({
            "name": stats["name"],
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
            "top_ships_kills": top_ships_kills,
            "top_ships_losses": top_ships_losses,
            "triggers": triggers,
            "suspicious_alliance": kills["suspicious_alliance"],
        })

        time.sleep(ZKB_REQUEST_DELAY_SECONDS)

    return results