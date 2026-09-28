"""Ship type ID lists used by the trigger evaluation logic.

These are public, well-known EVE Online ship type IDs (not sensitive
data), kept separate from the trigger logic itself for readability.
Will move to a database-backed configuration model later.
"""

COVERT_OPS_SHIP_IDS = {
    11192,  # Buzzard
    11188,  # Anathema
    11182,  # Cheetah
    11172,  # Helios
}

FORCE_RECON_SHIP_IDS = {
    11957,  # Falcon
    11963,  # Rapier
    11965,  # Pilgrim
    11969,  # Arazu
}

BLACK_OPS_SHIP_IDS = {
    22428,  # Redeemer
    22430,  # Sin
    22436,  # Widow
    22440,  # Panther
    44996,  # Marshal
}

SHUTTLE_AND_CORVETTE_SHIP_IDS = {
    11132,  # Minmatar Shuttle
    11134,  # Amarr Shuttle
    672,    # Caldari Shuttle
    11129,  # Gallente Shuttle
    601,    # Ibis (Caldari Corvette)
    596,    # Impairor (Amarr Corvette)
    606,    # Velator (Gallente Corvette)
    588,    # Reaper (Minmatar Corvette)
}