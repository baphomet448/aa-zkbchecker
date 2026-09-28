"""Client for public ESI endpoints used by ZKB Checker."""

import requests

ESI_BASE_URL = "https://esi.evetech.net/latest"
USER_AGENT = "ZkbChecker-AA-Plugin/1.0 (contact: baphomet448 via Discord)"


def resolve_names(names: list[str]) -> list[dict]:
    """Resolve a list of character names to character IDs.

    Returns a list of dicts like {"id": 123, "name": "Some Name"}
    for names that were found as characters. Names that aren't
    found simply don't appear in the result.
    """
    response = requests.post(
        f"{ESI_BASE_URL}/universe/ids/",
        json=names,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("characters", [])

def resolve_ids(ids: list[int]) -> list[dict]:
    """Resolve a list of IDs (of any entity type - corporation,
    alliance, ship type, etc.) to their names.

    Returns a flat list of dicts like:
    {"id": 123, "name": "Some Name", "category": "corporation"}
    """
    response = requests.post(
        f"{ESI_BASE_URL}/universe/names/",
        json=ids,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()

def search_ship_types(query: str, limit: int = 10) -> list[dict]:
    """Search for ship/item type names matching the query (partial,
    case-insensitive match) and return a list of {"id": ..., "name": ...}.
    """
    if not query or len(query) < 2:
        return []

    response = requests.get(
        f"{ESI_BASE_URL}/search/",
        params={
            "categories": "inventory_type",
            "search": query,
            "strict": "false",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    type_ids = data.get("inventory_type", [])[:limit]
    if not type_ids:
        return []

    return resolve_ids(type_ids)