"""Local configuration for suspicious alliances/corporations and excluded
ship types. This file is intentionally excluded from git (see .gitignore)
since it may contain sensitive alliance names not meant for a public repo.

Copy this file to a private location and adjust the values, or provide
your own local_config.py alongside this one when installing the plugin.
"""

# Alliance ID -> label. Populated by the security team.
SUSPICIOUS_ALLIANCES: dict[int, str] = {}

# Corporation ID -> label. Populated by the security team.
SUSPICIOUS_CORPORATIONS: dict[int, str] = {}

# Ship type IDs to exclude when counting loss statistics
# (capsules, mobile structures, etc.). Sensible defaults provided,
# override if needed.
EXCLUDED_SHIP_IDS: set[int] = {
    670,    # Capsule
    33328,  # Capsule (Genolution)
    33474,  # Mobile Depot
    33700,  # 'Packrat' Mobile Tractor Unit
    33475,  # Mobile Tractor Unit
    33702,  # 'Magpie' Mobile Tractor Unit
    33520,  # 'Wetu' Mobile Depot
    33522,  # 'Yurt' Mobile Depot
    26892,  # Mobile Small Warp Disruptor II
    26890,  # Mobile Medium Warp Disruptor II
    26888,  # Mobile Large Warp Disruptor II
    12198,  # Mobile Small Warp Disruptor I
    12199,  # Mobile Medium Warp Disruptor I
    12200,  # Mobile Large Warp Disruptor I
    28774,  # Syndicate Mobile Small Warp Disruptor
    28772,  # Syndicate Mobile Medium Warp Disruptor
    28770,  # Syndicate Mobile Large Warp Disruptor
}