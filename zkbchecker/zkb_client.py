"""Client for the zKillboard API used by ZKB Checker."""

import requests
from collections import Counter
from datetime import datetime, timedelta, timezone

LOSSES_LOOKBACK_MONTHS = 4

SUSPICIOUS_FLEET_LOOKBACK_KILLS = 100
SUSPICIOUS_FLEET_LOOKBACK_MONTHS = 8

ZKB_BASE_URL = "https://zkillboard.com/api"
USER_AGENT = "ZkbChecker-AA-Plugin/1.0 (contact: baphomet448 via Discord)"

def _get_excluded_ship_ids() -> set[int]:
    from zkbchecker.models import ExcludedShip
    return set(ExcludedShip.objects.values_list("ship_type_id", flat=True))


def _get_suspicious_entities() -> tuple[dict[int, str], dict[int, str]]:
    from zkbchecker.models import SuspiciousEntity
    alliances = {}
    corporations = {}
    for entity in SuspiciousEntity.objects.all():
        if entity.entity_type == SuspiciousEntity.EntityType.ALLIANCE:
            alliances[entity.entity_id] = entity.label
        else:
            corporations[entity.entity_id] = entity.label
    return alliances, corporations

def get_stats(character_id: int) -> dict:
    """Fetch character stats from zKillboard.

    Returns a dict with the fields we care about:
    name, corporation_id, alliance_id, birthday,
    kills_total, losses_total, solo_kills, solo_losses,
    danger_ratio, gang_ratio, top_ships_used (all, not just top 3),
    ganked_kills.
    """
    response = requests.get(
        f"{ZKB_BASE_URL}/stats/characterID/{character_id}/",
        headers={"User-Agent": USER_AGENT},
        timeout=15,
        allow_redirects=True,
    )
    response.raise_for_status()
    raw = response.json()

    info = raw.get("info") or {}

    # Extract the "ship" category from topAllTime (all ships used, by kills)
    all_ships_used = []
    for entry in raw.get("topAllTime") or []:
        if entry.get("type") == "ship":
            all_ships_used = entry.get("data", [])
            break

    ganked = (raw.get("labels") or {}).get("ganked") or {}

    return {
        "name": info.get("name", ""),
        "corporation_id": info.get("corporation_id", 0),
        "alliance_id": info.get("alliance_id", 0),
        "birthday": info.get("birthday", ""),
        "kills_total": raw.get("shipsDestroyed", 0),
        "losses_total": raw.get("shipsLost", 0),
        "solo_kills": raw.get("soloKills", 0),
        "solo_losses": raw.get("soloLosses", 0),
        "danger_ratio": raw.get("dangerRatio", 0),
        "gang_ratio": raw.get("gangRatio", 0),
        "all_ships_used": all_ships_used,
        "ganked_kills": ganked.get("shipsDestroyed", 0),
    }

def get_losses(character_id: int) -> dict:
    """Fetch character losses from zKillboard and summarize them.

    Returns a dict with:
    last_loss_date, top_ships (top 3), all_ships (full list,
    both excluding junk ship types and limited to the last
    LOSSES_LOOKBACK_MONTHS months).
    """
    excluded_ship_ids = _get_excluded_ship_ids()
    response = requests.get(
        f"{ZKB_BASE_URL}/losses/characterID/{character_id}/",
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    entries = response.json()

    if not entries:
        return {"last_loss_date": "", "top_ships": [], "all_ships": []}

    last_loss_date = entries[0].get("killmail_time", "")

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * LOSSES_LOOKBACK_MONTHS)
    counts = Counter()
    for entry in entries:
        killmail_time_str = entry.get("killmail_time", "")
        try:
            killmail_time = datetime.fromisoformat(killmail_time_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if killmail_time < cutoff:
            continue

        ship_type_id = entry.get("victim", {}).get("ship_type_id")
        if ship_type_id in excluded_ship_ids:
            continue

        counts[ship_type_id] += 1

    all_ships = [
        {"shipTypeID": ship_id, "kills": count}
        for ship_id, count in counts.most_common()
    ]
    top_ships = all_ships[:3]

    return {
        "last_loss_date": last_loss_date,
        "top_ships": top_ships,
        "all_ships": all_ships,
    }

def get_kills(character_id: int) -> dict:
    """Fetch character kills from zKillboard and summarize them.

    Returns a dict with:
    last_kill_date, victim_ships (ship types of victims, last
    LOSSES_LOOKBACK_MONTHS months), suspicious_alliance (name of
    a suspicious alliance/corporation seen as the final-blow
    attacker on one of the last SUSPICIOUS_FLEET_LOOKBACK_KILLS
    kills, within SUSPICIOUS_FLEET_LOOKBACK_MONTHS months, or
    empty string if none found).
    """
    response = requests.get(
        f"{ZKB_BASE_URL}/kills/characterID/{character_id}/",
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    entries = response.json()

    result = {"last_kill_date": "", "victim_ships": [], "suspicious_alliance": ""}
    if not entries:
        return result

    result["last_kill_date"] = entries[0].get("killmail_time", "")

    # Victim ship types, last LOSSES_LOOKBACK_MONTHS months
    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * LOSSES_LOOKBACK_MONTHS)
    counts = Counter()
    for entry in entries:
        killmail_time_str = entry.get("killmail_time", "")
        try:
            killmail_time = datetime.fromisoformat(killmail_time_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if killmail_time < cutoff:
            continue
        ship_type_id = entry.get("victim", {}).get("ship_type_id")
        counts[ship_type_id] += 1

    result["victim_ships"] = [
        {"shipTypeID": ship_id, "kills": count}
        for ship_id, count in counts.most_common()
    ]

    # Suspicious fleet check: last N kills, within M months
    suspicious_alliances, suspicious_corporations = _get_suspicious_entities()
    fleet_cutoff = datetime.now(timezone.utc) - timedelta(days=30 * SUSPICIOUS_FLEET_LOOKBACK_MONTHS)
    for entry in entries[:SUSPICIOUS_FLEET_LOOKBACK_KILLS]:
        killmail_time_str = entry.get("killmail_time", "")
        try:
            killmail_time = datetime.fromisoformat(killmail_time_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if killmail_time < fleet_cutoff:
            continue

        for attacker in entry.get("attackers", []):
            if not attacker.get("final_blow"):
                continue
            alliance_id = attacker.get("alliance_id")
            corp_id = attacker.get("corporation_id")
            if alliance_id in suspicious_alliances:
                result["suspicious_alliance"] = suspicious_alliances[alliance_id]
                return result
            if corp_id in suspicious_corporations:
                result["suspicious_alliance"] = suspicious_corporations[corp_id]
                return result

    return result