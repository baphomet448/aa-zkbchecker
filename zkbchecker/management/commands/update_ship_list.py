"""Management command to fetch the current list of ship and deployable
structure types from ESI and save it to a local JSON file, used for
the ExcludedShip admin autocomplete field.

Run this once during setup, and again whenever new ships/structures
are added to the game (e.g. after an expansion).
"""

import json
import time
from pathlib import Path

import requests
from django.core.management.base import BaseCommand

ESI_BASE_URL = "https://esi.evetech.net/latest"
USER_AGENT = "ZkbChecker-AA-Plugin/1.0 (contact: baphomet448 via Discord)"

# Ship (kills/losses) and Deployable (mobile depots, warp disruptors,
# tractor units, etc.) categories - both relevant for the excluded
# ships list, since capsules and deployables show up in loss stats
# alongside real ships.
ITEM_CATEGORY_IDS = [6, 22]

OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "ship_list.json"


class Command(BaseCommand):
    help = "Fetch the current list of ship and deployable types from ESI and save it locally."

    def handle(self, *args, **options):
        all_type_ids = []

        for category_id in ITEM_CATEGORY_IDS:
            self.stdout.write(f"Fetching category {category_id} from ESI...")
            category = requests.get(
                f"{ESI_BASE_URL}/universe/categories/{category_id}/",
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            ).json()
            group_ids = category["groups"]

            self.stdout.write(f"Found {len(group_ids)} groups in category {category_id}. Fetching types...")
            for gid in group_ids:
                resp = requests.get(
                    f"{ESI_BASE_URL}/universe/groups/{gid}/",
                    headers={"User-Agent": USER_AGENT},
                    timeout=15,
                ).json()
                if resp.get("published", True):
                    all_type_ids.extend(resp.get("types", []))
                time.sleep(0.1)

        self.stdout.write(f"Found {len(all_type_ids)} types total. Resolving names...")
        ships = []
        for i in range(0, len(all_type_ids), 1000):
            batch = all_type_ids[i:i + 1000]
            response = requests.post(
                f"{ESI_BASE_URL}/universe/names/",
                json=batch,
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            )
            response.raise_for_status()
            for entity in response.json():
                ships.append({"id": entity["id"], "name": entity["name"]})

        ships.sort(key=lambda s: s["name"])

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(ships, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Saved {len(ships)} items to {OUTPUT_PATH}"))