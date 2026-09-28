"""Suspicion trigger evaluation for ZKB Checker.

Ports the trigger logic from the original Go implementation, one to one.
"""

from datetime import datetime, timedelta, timezone

from zkbchecker.ship_lists import (
    BLACK_OPS_SHIP_IDS,
    COVERT_OPS_SHIP_IDS,
    FORCE_RECON_SHIP_IDS,
    SHUTTLE_AND_CORVETTE_SHIP_IDS,
)

OLD_BUT_INACTIVE_MIN_AGE_DAYS = 180
OLD_BUT_INACTIVE_MAX_ACTIVITY = 5
SHUTTLE_KILL_THRESHOLD = 15


def _is_old_but_inactive(stats: dict) -> bool:
    """True if the character is old (by birthday) but has very
    little combat activity overall."""
    birthday_str = stats.get("birthday", "")
    if not birthday_str:
        return False
    try:
        birthday = datetime.fromisoformat(birthday_str.replace("Z", "+00:00"))
    except ValueError:
        return False

    age = datetime.now(timezone.utc) - birthday
    total_activity = stats.get("kills_total", 0) + stats.get("losses_total", 0)
    return age >= timedelta(days=OLD_BUT_INACTIVE_MIN_AGE_DAYS) and total_activity < OLD_BUT_INACTIVE_MAX_ACTIVITY


def _is_ganker(stats: dict) -> bool:
    """True if the character has any recorded highsec gank kills."""
    return stats.get("ganked_kills", 0) > 0

def _has_ship_from(ships: list[dict], ship_id_set: set[int]) -> bool:
    """True if any ship in the list belongs to the given set of ship type IDs."""
    return any(ship.get("shipTypeID") in ship_id_set for ship in ships)


def _is_shuttle_farmer(victim_ships: list[dict]) -> bool:
    """True if the character has killed a large number of shuttles/
    corvettes (typically hunting new players) in the recent kills window."""
    count = sum(
        ship.get("kills", 0)
        for ship in victim_ships
        if ship.get("shipTypeID") in SHUTTLE_AND_CORVETTE_SHIP_IDS
    )
    return count >= SHUTTLE_KILL_THRESHOLD

def evaluate_triggers(stats: dict, all_ships_losses: list[dict], kill_victim_ships: list[dict]) -> list[str]:
    """Run all suspicion checks against a character's data and return
    the list of trigger labels that fired.

    Args:
        stats: result of zkb_client.get_stats()
        all_ships_losses: the "all_ships" list from zkb_client.get_losses()
        kill_victim_ships: the "victim_ships" list from zkb_client.get_kills()
    """
    triggers = []

    if _is_old_but_inactive(stats):
        triggers.append("OLD_BUT_INACTIVE")
    if _is_ganker(stats):
        triggers.append("GANKER!")

    ships_used = stats.get("all_ships_used", [])

    if _has_ship_from(ships_used, COVERT_OPS_SHIP_IDS) or _has_ship_from(all_ships_losses, COVERT_OPS_SHIP_IDS):
        triggers.append("Covert Ops!")
    if _has_ship_from(ships_used, FORCE_RECON_SHIP_IDS) or _has_ship_from(all_ships_losses, FORCE_RECON_SHIP_IDS):
        triggers.append("Force Recon!")
    if _has_ship_from(ships_used, BLACK_OPS_SHIP_IDS):
        triggers.append("DROPPER!")

    if _is_shuttle_farmer(kill_victim_ships):
        triggers.append("Shuttles!")

    return triggers