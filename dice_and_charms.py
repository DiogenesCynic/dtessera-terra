"""
dice_and_charms.py
------------------
Standalone module for Collectible Stylised 2d6 Dice, Luck-Bending Charms,
NPC Dungeon Map Exchanges, Blade Poisons, and Permanent Stat-Boosting Relics.
"""

import random
import pygame
import game_data as db


# =========================================================================
# 0. AUTO-REGISTER DICE, CHARMS, MAPS & RELICS INTO game_data.item_database
# =========================================================================
PHASE6_ITEMS = {
    # Stylised Dice Sets
    "bone dice": {
        "price": 5, "weight": 0.1, "usable": True,
        "description": "A pair of carved ox-bone dice with crimson-inked pips."
    },
    "brass wallmaker dice": {
        "price": 35, "weight": 0.3, "usable": True,
        "description": "Heavy, corner-bevelled brass dice favoured by Syndicate masons; the first die never rolls a 1."
    },
    "jade kokeshi dice": {
        "price": 45, "weight": 0.2, "usable": True,
        "description": "Polished green jade dice with gold-leaf pips; rolling doubles awards +3 Silver!"
    },
    "obsidian vanguard dice": {
        "price": 40, "weight": 0.2, "usable": True,
        "description": "Volcanic black glass dice carved in Lignum Forest; grants +1 to stealth and wilderness rolls."
    },
    "star-iron guild dice": {
        "price": 55, "weight": 0.4, "usable": True,
        "description": "Meteoric iron dice forged in Parvus; grants +1 to dungeon trap, lock, and engineering rolls."
    },

    # Luck-Bending Charms
    "hare's foot charm": {
        "price": 25, "weight": 0.1,
        "description": "A lucky upland charm that automatically re-rolls Snake-Eyes (2) on any 2d6 check."
    },
    "river-stone charm": {
        "price": 30, "weight": 0.2,
        "description": "A naturally perforated stone from the River Fluvius that turns random 30% Friction twists into Windfalls."
    },
    "iron horseshoe charm": {
        "price": 20, "weight": 0.4,
        "description": "A miniature farrier's charm that steadies your horse in deep mire and winter frost."
    },
    "owl-feather charm": {
        "price": 25, "weight": 0.1,
        "description": "A silent barn-owl primary feather that halves torchlight consumption underground and at night."
    },

    # NPC Quest Items & Dungeon Maps
    "tarnished silver locket": {
        "price": 10, "weight": 0.1,
        "description": "An heirloom locket engraved 'To Ceolwulf'—lost near the Ragmore pastures."
    },
    "broken brass sextant": {
        "price": 12, "weight": 0.5,
        "description": "A salt-encrusted coastal sextant stamped with Rigger Ronan's mark."
    },
    "mason's plumb-bob": {
        "price": 12, "weight": 0.4,
        "description": "A lead-and-brass surveyor's plumb-bob belonging to The Diewell on the Old Path."
    },
    "prospector's assay-loupe": {
        "price": 15, "weight": 0.2,
        "description": "A folding brass magnifying lens lost by Foundryman Aldred's brother in the Caligo hills."
    },
    "map: calluna crypt": {
        "price": 30, "weight": 0.1, "usable": True,
        "description": "Surveyor's parchment map of the Drowned Crypt of Lake Calluna (7, 1). Reveals the [LOW, MID, HIGH] sundial solution!"
    },
    "map: parvus catacombs": {
        "price": 30, "weight": 0.1, "usable": True,
        "description": "Engineer's map of the Under-Parvus Tidal Catacombs (17, 22). Reveals the [LOW, HIGH, MID] pressure-wheel solution!"
    },
    "map: old path catacombs": {
        "price": 30, "weight": 0.1, "usable": True,
        "description": "Wallmaker blueprint of the Old Path Sapper Catacombs (3, 12). Reveals the [LOW, HIGH, MID] acoustic lever solution!"
    },
    "map: caligo silver mine": {
        "price": 30, "weight": 0.1, "usable": True,
        "description": "Assayer's chart of the Caligo Deep-Delve Silver Mine (15, 2). Reveals the [LOW, MID, HIGH] smelting-chute solution!"
    },

    # Poisons & Permanent Stat-Boosting Relics
    "vial of nightshade poison": {
        "price": 30, "weight": 0.2, "usable": True,
        "description": "Distilled black-nightshade oil; use to coat your equipped weapon (+2 Poison Damage on your next 3 combat strikes!)."
    },
    "manual of the iron wrist": {
        "price": 50, "weight": 0.5, "usable": True,
        "description": "An illustrated swordmaster's treatise; reading/using it permanently increases your Strength by +1!"
    },
    "treatise on rhetoric": {
        "price": 50, "weight": 0.5, "usable": True,
        "description": "A rare parliamentary handbook; reading/using it permanently increases your Charisma by +1!"
    },
    "shadow-walker's soft-boots": {
        "price": 50, "weight": 0.8, "usable": True,
        "description": "Suede-soled night-runner boots; equipping/using them permanently increases your Stealth by +1!"
    },
}

# Automatically merge into game_data.item_database when imported
for _k, _v in PHASE6_ITEMS.items():
    if _k not in db.item_database:
        db.item_database[_k] = _v


# =========================================================================
# 1. COLLECTIBLE STYLISED DICE VISUAL PALETTES & PASSIVE BONUSES
# =========================================================================
DICE_STYLES = {
    "bone dice": {
        "label": "Carved Ox-Bone Dice",
        "bg": (245, 240, 225),
        "border": (90, 75, 60),
        "pip_normal": (28, 28, 28),
        "pip_ace_four": (175, 40, 30),
    },
    "brass wallmaker dice": {
        "label": "Weighted Brass Wallmaker Dice",
        "bg": (195, 155, 55),
        "border": (85, 60, 15),
        "pip_normal": (25, 22, 18),
        "pip_ace_four": (25, 22, 18),
    },
    "jade kokeshi dice": {
        "label": "Imperial Jade Kokeshi Dice",
        "bg": (38, 125, 82),
        "border": (20, 70, 45),
        "pip_normal": (250, 215, 85),
        "pip_ace_four": (255, 240, 150),
    },
    "obsidian vanguard dice": {
        "label": "Volcanic Obsidian Dice",
        "bg": (32, 34, 40),
        "border": (95, 185, 110),
        "pip_normal": (85, 215, 120),
        "pip_ace_four": (165, 245, 185),
    },
    "star-iron guild dice": {
        "label": "Meteoric Star-Iron Dice",
        "bg": (70, 95, 130),
        "border": (215, 140, 65),
        "pip_normal": (240, 245, 255),
        "pip_ace_four": (255, 175, 90),
    },
}

PIP_LAYOUTS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
    6: [(0.25, 0.22), (0.75, 0.22), (0.25, 0.5), (0.75, 0.5), (0.25, 0.78), (0.75, 0.78)],
}


def get_active_dice_style(player):
    """Returns the best stylised dice set the player currently carries or has equipped."""
    eq = player.get("equipped_dice")
    inv = player.get("inventory", [])
    if eq in DICE_STYLES and (eq in inv or eq == "bone dice"):
        return eq
    for style_k in ("star-iron guild dice", "jade kokeshi dice", "brass wallmaker dice", "obsidian vanguard dice"):
        if style_k in inv:
            player["equipped_dice"] = style_k
            return style_k
    return "bone dice"


def roll_stylised_2d6(player, context="general"):
    """Rolls 2d6 applying Stylised Dice bonuses and Luck-Bending Charms."""
    style_k = get_active_dice_style(player)
    inv = player.get("inventory", [])
    notes = []

    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)

    if d1 == 1 and d2 == 1 and "hare's foot charm" in inv:
        d1, d2 = random.randint(2, 6), random.randint(2, 6)
        notes.append("[Hare's Foot Charm: Re-rolled Snake-Eyes!]")

    if style_k == "brass wallmaker dice" and d1 == 1:
        d1 = 2
        notes.append("[Brass Dice: 1->2]")

    if style_k == "jade kokeshi dice" and d1 == d2:
        player["silver"] = player.get("silver", 0) + 3
        notes.append("[Jade Doubles: +3s!]")

    bonus = 0
    if style_k == "obsidian vanguard dice" and context in ("stealth", "hunt", "herding", "outlaw"):
        bonus += 1
        notes.append("[Obsidian Dice +1]")
    elif style_k == "star-iron guild dice" and context in ("dungeon", "guild", "tool"):
        bonus += 1
        notes.append("[Star-Iron Dice +1]")

    player["last_2d6_tuple"] = (d1, d2)
    player["last_2d6_style"] = style_k
    return d1, d2, d1 + d2 + bonus, " ".join(notes)


def draw_stylised_2d6_widget(screen, player, x=625, y=45, size=36):
    """Draws the player's currently equipped pair of Stylised 2d6 Dice at (x, y)."""
    d1, d2 = player.get("last_2d6_tuple", (6, 6))
    style_k = get_active_dice_style(player)
    spec = DICE_STYLES.get(style_k, DICE_STYLES["bone dice"])

    for idx, val in enumerate((d1, d2)):
        dx = x + idx * (size + 8)
        dy = y
        pygame.draw.rect(screen, (20, 20, 20), (dx + 2, dy + 2, size, size), border_radius=7)
        d_rect = pygame.Rect(dx, dy, size, size)
        pygame.draw.rect(screen, spec["bg"], d_rect, border_radius=7)
        pygame.draw.rect(screen, spec["border"], d_rect, width=2, border_radius=7)

        pip_col = spec["pip_ace_four"] if val in (1, 4) else spec["pip_normal"]
        pip_r = 4 if val == 1 else 3
        for px_rel, py_rel in PIP_LAYOUTS.get(val, PIP_LAYOUTS[6]):
            cx = int(dx + px_rel * size)
            cy = int(dy + py_rel * size)
            pygame.draw.circle(screen, pip_col, (cx, cy), pip_r)


# =========================================================================
# 2. NPC PERSONAL ITEMS -> DUNGEON MAP EXCHANGES
# =========================================================================
NPC_DUNGEON_MAP_QUESTS = {
    "ceolwulf": {
        "wanted_item": "tarnished silver locket",
        "map_reward": "map: calluna crypt",
        "speech": (
            "Herdsman Ceolwulf's weathered face lights up with tears of joy as you hand him the **Tarnished Silver Locket**!\n"
            "\"My late wife's portrait! Take this ancient parchment in return: **Map: Calluna Crypt**. "
            "It shows the submerged basalt mausoleum on the shores of **Lake Calluna**, and notes that the **Three-Hour Sarcophagus Dials** must be set to **[LOW (3), MID (5), HIGH (8)]**!\""
        ),
    },
    "ronan_rigger": {
        "wanted_item": "broken brass sextant",
        "map_reward": "map: parvus catacombs",
        "speech": (
            "Rigger Ronan clasps his **Broken Brass Sextant** to his chest!\n"
            "\"My first mate's sextant from the *Sea-Wolf*! Here, comrade—take this **Map: Parvus Catacombs**. "
            "It charts the flooded sluice-tunnels beneath the **Upper Parvus Promenade Storm-Drain Grate**, and records the brass pressure-wheel combination: **[LOW, HIGH, MID]**!\""
        ),
    },
    "diewell": {
        "wanted_item": "mason's plumb-bob",
        "map_reward": "map: old path catacombs",
        "speech": (
            "The Diewell weighs the **Mason's Plumb-Bob** in his palm and nods with rare respect.\n"
            "\"A master surveyor never forgets a favour. Take this **Map: Old Path Catacombs**. "
            "It details the pendulum traps beneath our **Ruined Waystation** cellar stones, and marks the 3-lever keystone alignment as **[LOW, HIGH, MID]**!\""
        ),
    },
    "aldred_foundry": {
        "wanted_item": "prospector's assay-loupe",
        "map_reward": "map: caligo silver mine",
        "speech": (
            "Foundryman Aldred polishes the **Prospector's Assay-Loupe** on his leather apron!\n"
            "\"My brother's lens from the mountain claims! You've earned this **Map: Caligo Silver Mine**. "
            "High on the southern slate crags of the **Caligo Mountain Range**, an abandoned timber mine-adit leads down to a vein of **Star-Iron**—set the three smelting-chutes to **[LOW, MID, HIGH]**!\""
        ),
    },
}


def check_npc_dungeon_map_trade(npc_key, player):
    q = NPC_DUNGEON_MAP_QUESTS.get(npc_key)
    if not q:
        return None
    if q["wanted_item"] in player.get("inventory", []) and q["map_reward"] not in player.get("inventory", []):
        return f"Give {q['wanted_item'].title()} (Receive Dungeon Map!)"
    return None


def resolve_npc_dungeon_map_trade(npc_key, player):
    q = NPC_DUNGEON_MAP_QUESTS[npc_key]
    inv = player.get("inventory", [])
    if q["wanted_item"] in inv:
        inv.remove(q["wanted_item"])
    if q["map_reward"] not in inv:
        inv.append(q["map_reward"])
    player["reputation"] = player.get("reputation", 0) + 1
    return player, q["speech"], "NPC_DIALOGUE"


# =========================================================================
# 3. USING POISONS, STAT-BOOSTING RELICS, DICE & DUNGEON MAPS
# =========================================================================
def handle_phase6_item_use(item_name, player):
    inv = player.get("inventory", [])

    if item_name in DICE_STYLES:
        player["equipped_dice"] = item_name
        d1, d2, tot, note = roll_stylised_2d6(player)
        return True, (
            f"You equip your **{DICE_STYLES[item_name]['label']}** and give them a test roll: "
            f"**[{d1}] + [{d2}] = {tot}** {note}!"
        )

    if item_name == "vial of nightshade poison":
        inv.remove("vial of nightshade poison")
        player["weapon_poison_charges"] = player.get("weapon_poison_charges", 0) + 3
        return True, (
            "=== BLADE ENVENOMED (+3 Poison Strikes)! ===\n"
            "You coat the edge of your weapon with glistening black-nightshade oil (+2 extra Poison Damage on your next 3 combat strikes!)."
        )

    if item_name == "manual of the iron wrist":
        inv.remove("manual of the iron wrist")
        player["strength"] = player.get("strength", 0) + 1
        return True, (
            "=== PERMANENT STAT INCREASE: +1 STRENGTH! ===\n"
            "Studying the illustrations in the **Manual of the Iron Wrist**, you master the leverage of the wrist and forearm!"
        )

    if item_name == "treatise on rhetoric":
        inv.remove("treatise on rhetoric")
        player["charisma"] = player.get("charisma", 0) + 1
        return True, (
            "=== PERMANENT STAT INCREASE: +1 CHARISMA! ===\n"
            "Absorbing the cadences of the **Treatise on Rhetoric**, your voice gains commanding warmth and persuasion!"
        )

    if item_name == "shadow-walker's soft-boots":
        player["stealth"] = player.get("stealth", 0) + (1 if not player.get("soft_boots_bonus_claimed") else 0)
        player["soft_boots_bonus_claimed"] = True
        return True, (
            "=== SHADOW-WALKER'S SOFT-BOOTS EQUIPPED (+1 Stealth)! ===\n"
            "Lacing on the suede-soled boots, your footsteps become as silent as falling snow!"
        )

    if item_name.startswith("map: "):
        desc = db.item_database.get(item_name, {}).get("description", "")
        return True, f"=== DUNGEON SURVEYOR'S CHART ({item_name.upper()}) ===\n{desc}"

    return False, ""
