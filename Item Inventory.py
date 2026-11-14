"""
Item Inventory.py
-----------------
Dynamically audits all items across `game_data.py` and `crafting_engine.py`
and exports both a universal CSV spreadsheet and (if openpyxl is installed)
a formatted Excel (.xlsx) workbook.
"""

import csv
import game_data as db
import crafting_engine as ce


def build_live_item_rows():
    """Combines `db.item_database` and `ce.EXOTIC_GEAR_DATABASE` into a unified table."""
    merged = {}
    for k, v in db.item_database.items():
        merged[k] = dict(v)
    for k, v in ce.EXOTIC_GEAR_DATABASE.items():
        if k not in merged:
            merged[k] = dict(v)

    rows = []
    for key in sorted(merged.keys()):
        info = merged[key]
        price = info.get("price", 0)
        weight = info.get("weight", 0.2)
        desc = info.get("description", "")

        if key in db.weapon_max_hit or info.get("slot") == "weapon":
            cat = "Weapon"
        elif key in db.shield_defense or info.get("slot") in ("torso", "head", "horse"):
            cat = "Armour / Defence"
        elif "hunger_restore" in info or "thirst_restore" in info:
            cat = "Food & Drink"
        elif "cures_affliction" in info:
            cat = "Medicine"
        elif "map" in key or "scope" in key or "spyglass" in key:
            cat = "Map / Optics"
        elif price == 0:
            cat = "Quest / Key Item"
        else:
            cat = "Tool / Gear"

        rows.append((key.title(), cat, price, weight, desc))
    return rows


def export_inventory_files():
    rows = build_live_item_rows()
    csv_file = "Dtessera_Terra_Master_Item_Inventory.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Item Name", "Category", "Base Price (s)", "Weight (lbs)", "Description"])
        writer.writerows(rows)
    print(f"[+] Exported {len(rows)} items to '{csv_file}' (opens directly in Excel).")


if __name__ == "__main__":
    export_inventory_files()
