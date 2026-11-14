"""
search_engine.py
----------------
Dual-Mode Investigation & Search Engine for Dtessera Terra:
  - "CLASSIC" Mode: The clean, text-button Tier 1 & Tier 2 investigation modal.
  - "ARCHITECTURAL" Mode: Interactive 1880s Surveyor's Cross-Section Plate with
    point-and-click hotspots, Night Lantern spotlight, Looking Glass (5th high-angle
    hotspot reveal), 20x Brass Microscope forensic inset, and Skeleton Key bypass.

Switch between modes anytime via DEFAULT_SEARCH_STYLE, the in-modal [View Mode] button,
or by pressing [TAB] while the Search window is open!
"""

import math
import random
import pygame
import game_data as db
from mechanics import advance_time
from ui_components import draw_fitted_text


# =========================================================================
# 0. DEV / PLAYER CONFIGURATION & AUTO-REGISTRATION OF OPTICAL ITEMS
# =========================================================================
# Set to "CLASSIC" to default to your existing text-button search modal,
# or "ARCHITECTURAL" to default to the interactive Surveyor's Blueprint plate!
DEFAULT_SEARCH_STYLE = "ARCHITECTURAL"

PHASE2_SEARCH_ITEMS = {
    "looking glass": {
        "price": 30, "weight": 0.5, "usable": True,
        "description": "A collapsible three-draw brass spyglass. Reveals distant or high-elevation hidden hotspots during investigations."
    },
    "brass microscope": {
        "price": 45, "weight": 1.2, "usable": True,
        "description": "A compound brass field-microscope (20x magnification). Uncovers microscopic forensic evidence on surfaces and documents."
    },
    "skeleton key": {
        "price": 65, "weight": 0.1, "usable": True,
        "description": "A master-filed star-iron ward key. Silently unlocks any padlocked cache, grate, or door during a search without a roll."
    },
}

for _k, _v in PHASE2_SEARCH_ITEMS.items():
    if _k not in db.item_database:
        db.item_database[_k] = _v


def get_search_style(player):
    """Returns 'CLASSIC' or 'ARCHITECTURAL' based on player/dev preference."""
    return player.get("search_ui_style", DEFAULT_SEARCH_STYLE)


def toggle_search_style(player):
    """Flips cleanly between 'CLASSIC' and 'ARCHITECTURAL' search modes."""
    cur = get_search_style(player)
    new_style = "CLASSIC" if cur == "ARCHITECTURAL" else "ARCHITECTURAL"
    player["search_ui_style"] = new_style
    return new_style


# =========================================================================
# 1. MASTER DATABASE OF TILE SEARCH FEATURES, HOTSPOTS & FORENSIC CLUES
# =========================================================================
# Each feature tuple is: (label, key, (rel_x, rel_y, w, h) inside 630x210 canvas)
# Optional "spyglass_feature": A 5th high/distant hotspot only visible with the Looking Glass!
SEARCH_DATABASE = {
    (10, 5): {  # The Sunken Sluice-Gate Lane
        "title": "THE SUNKEN SLUICE-GATE LANE — SURVEY PLATE",
        "archetype": "OUTDOOR_SLUICE",
        "features": [
            ("Inspect the Rusted Sluice-Gate Pin", "sluice",   (70,  68, 125, 85)),
            ("Examine the Loose Boundary Boulders", "boulders",(235, 95, 120, 75)),
            ("Check Red Clay Ruts for Tire Tracks", "ruts",    (385, 130, 140, 55)),
            ("Dredge the Irrigation Shallows",      "shallows",(460, 60, 135, 60)),
        ],
        "spyglass_feature": ("Glass the High Ridge Embankment", "ridge_cache", (260, 14, 150, 38)),
        "correct_feature": "sluice",
        "locked_feature": "sluice",
        "clue_text": (
            "Examining the rusted iron lynch-pin on the ancient irrigation sluice, you find the oak chock wedged tight. "
            "With a stout iron tool, Skeleton Key, or brute strength, you can wrench this free to flood the sunken lane!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: Magnifying the red clay ruts and iron lynch-pin reveals fresh flecks of "
            "Castle Laydere blue wagon-paint and greased axle-tallow—proving heavy supply wagons passed here within the hour!"
        ),
        "spyglass_item": "hare's foot charm",
    },
    (12, 4): {  # Granary Wharf & Teamsters' Yard
        "title": "GRANARY WHARF & TEAMSTERS' YARD — SURVEY PLATE",
        "archetype": "WHARF_STABLES",
        "features": [
            ("Inspect the Padlocked Timber Corral", "corral",    (45,  62, 135, 95)),
            ("Search Behind the Brick Weigh-Beam",  "weighbeam", (215, 58, 135, 98)),
            ("Examine the Drover's Chalk Slate",    "slate",     (380, 68, 110, 75)),
            ("Rummage Through Empty Feed Sacks",    "sacks",     (505, 105, 105, 68)),
        ],
        "spyglass_feature": ("Glass the Granary Hoist Gable", "gable_loft", (230, 12, 145, 36)),
        "correct_feature": "weighbeam",
        "locked_feature": "corral",
        "clue_text": (
            "Behind the brick weigh-beam, where yellow fuller's earth is swept from the granary floor, "
            "you uncover discarded beeswax key-putty and a quayside bar-chit signed by Delegate Faintnot!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: Under 20x magnification, the beeswax key-putty shows the exact ward-notches "
            "of the Teamsters' Padlock AND microscopic grains of imported Parvus sea-coal!"
        ),
    },
    (13, 7): {  # East-Bank Watermill
        "title": "THE EAST-BANK WATERMILL — SURVEY PLATE",
        "archetype": "FORGE_MILL",
        "features": [
            ("Inspect the Shattered Paddles",       "paddles", (55,  48, 135, 115)),
            ("Examine the Splintered Oak Axle",     "axle",    (215, 68, 145, 85)),
            ("Check the Wet Mud Beside the Sluice", "sluice",  (385, 125, 130, 58)),
            ("Climb into the Mill-Loft",            "loft",    (455, 38, 140, 72)),
        ],
        "spyglass_feature": ("Glass the Weir-Gate Across the River", "weir_spy", (220, 12, 155, 36)),
        "correct_feature": "axle",
        "clue_text": (
            "Running your fingers along the broken oak axle, you discover three smooth, cylindrical bore-holes "
            "drilled into the load-bearing mortise with a hollow-core masonry bit—not axe strokes!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: The bore-hole shavings contain spiral brass filings from a **Wallmaker Syndicate "
            "Hollow-Core Auger**, proving the watermill was sabotaged by a professional mason, not farm strikers!"
        ),
    },
    (8, 16): {  # Murum Post Office
        "title": "MURUM POST OFFICE & CHANCERY — SURVEY PLATE",
        "archetype": "CHANCERY_POST",
        "features": [
            ("Check the Wooden Postbox Slot Outside", "postbox",     (50,  64, 115, 105)),
            ("Inspect the Pigeon-Holes Inside",       "pigeonholes", (200, 48, 155, 95)),
            ("Examine the Night-Dispatch Ledger",     "ledger",      (380, 92, 125, 68)),
            ("Sweep the Porch Flagstones",            "porch",       (515, 128, 95, 52)),
        ],
        "spyglass_feature": ("Glass the Telegraph Vane on the Roof", "roof_vane", (215, 10, 150, 34)),
        "correct_feature": "postbox",
        "locked_feature": "postbox",
        "clue_text": (
            "Sticking halfway out of the weathered wooden postbox slot is a misdelivered parchment envelope "
            "addressed to the Murum Town Hall Surveyor's Office (and an encrypted GCHQ dead-drop)!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: Magnifying the paper fibers reveals a watermark from the **Fluvius Tribune Press** "
            "and invisible lemon-juice cipher dots beneath the postage stamp!"
        ),
    },
    (3, 12): {  # Ruined Waystation on the Old Path
        "title": "RUINED WAYSTATION (OLD PATH) — SURVEY PLATE",
        "archetype": "KEEP_GUARD",
        "features": [
            ("Check the Chalk-Marked Stone Lintel",  "lintel", (55,  38, 145, 72)),
            ("Inspect the Stone Horse-Trough",       "trough", (65,  122, 135, 58)),
            ("Search Behind the Ivy-Choked Hearth",  "hearth", (245, 52, 145, 115)),
            ("Pry Up the Cellar Flagstones",         "cellar", (435, 118, 150, 62)),
        ],
        "spyglass_feature": ("Glass the High Watch-Gable Crag", "waystation_crag", (430, 28, 155, 52)),
        "correct_feature": "hearth",
        "locked_feature": "cellar",
        "hidden_item": "mason's plumb-bob",  # Lost NPC Dungeon Map item for The Diewell!
        "clue_text": (
            "Behind the ivy-choked hearth, you uncover a hollow mason's speaking-tube built into the chimney flue, "
            "a cache of crimson 'K-44' wax, and the sunken steps to the **Old Path Sapper Catacombs**!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: The soot inside the speaking-tube contains saltpetre and sulfur crystals—confirming "
            "sapper powder kegs are stored in the catacombs directly beneath your boots!"
        ),
    },
    (17, 22): {  # Upper Parvus Promenade
        "title": "UPPER PARVUS PROMENADE — SURVEY PLATE",
        "archetype": "CHANCERY_POST",
        "features": [
            ("Inspect the Seaward Balcony Railing",     "balcony",   (45,  55, 130, 95)),
            ("Examine the Festival Flower-Boxes",       "flowers",   (200, 88, 135, 72)),
            ("Check the Heavy Iron Storm-Drain Grate",  "grate",     (360, 122, 135, 58)),
            ("Search the Marble Colonnade Bases",       "colonnade", (510, 48, 98, 125)),
        ],
        "spyglass_feature": ("Glass the Brig 'Cormorant' in the Roadstead", "brig_spy", (45, 10, 185, 36)),
        "correct_feature": "grate",
        "locked_feature": "grate",
        "clue_text": (
            "Lifting the heavy iron storm-drain grate on the Promenade reveals rusted rungs descending straight "
            "into the roaring **Under-Parvus Tidal Catacombs**!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: Scrape-marks on the iron grate show trace residues of tarred hemp fuse-cord "
            "and brass boot-brads worn by Syndicate frogmen!"
        ),
    },
    (7, 1): {  # Lake Calluna Crypt
        "title": "LAKE CALLUNA SHORE — SURVEY PLATE",
        "archetype": "OUTDOOR_SLUICE",
        "features": [
            ("Inspect Half-Submerged Basalt Lintel", "lintel", (220, 48, 165, 110)),
            ("Check the Peat-Stained Reeds",         "reeds",  (45,  95, 145, 75)),
            ("Wade into the Mossy Crypt Steps",      "steps",  (405, 110, 130, 68)),
            ("Examine the Rotted Mooring Piles",     "piles",  (470, 42, 120, 58)),
        ],
        "spyglass_feature": ("Glass the Center-Lake Cairn Island", "island_spy", (45, 14, 155, 38)),
        "correct_feature": "lintel",
        "locked_feature": "lintel",
        "clue_text": (
            "Brushing away water-reeds from the sunken basalt lintel reveals carved heraldic shields "
            "and an open stone stairway descending into the **Drowned Crypt of Lake Calluna**!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: Lichen growth inside the carved sundial numerals shows someone recently scraped "
            "the numerals III, V, and VIII clean with a steel blade!"
        ),
    },
    (15, 2): {  # Caligo Mountain Mine-Adit
        "title": "CALIGO CRAGS — MINE-ADIT SURVEY PLATE",
        "archetype": "FORGE_MILL",
        "features": [
            ("Inspect Weathered Timber Mine-Head",   "timber",  (210, 42, 175, 122)),
            ("Examine Rusted Ore-Cart Rails",        "rails",   (45,  125, 150, 55)),
            ("Check Quartz-Veined Fissure Wall",     "fissure", (405, 48, 125, 95)),
            ("Scrutinize Dump-Heap of Grey Slate",   "slate",   (460, 122, 135, 58)),
        ],
        "spyglass_feature": ("Glass the High Eagle-Crag Ledge", "crag_loupe", (405, 10, 175, 34)),
        "correct_feature": "timber",
        "locked_feature": "timber",
        "hidden_item": "prospector's assay-loupe",  # Lost NPC Dungeon Map item for Foundryman Aldred!
        "clue_text": (
            "Clearing loose slate from the timber adit uncovers an uncollapsed rail-line descending into the "
            "**Caligo Deep-Delve Silver Mine** (and Foundryman Aldred's lost **Prospector's Assay-Loupe** in the slate)!"
        ),
        "microscope_text": (
            "[20x MICROSCOPE ANALYSIS]: The grey slate dump-heap glitters with microscopic octahedral crystals of "
            "meteoric **Star-Iron** alloyed with native silver!"
        ),
    },
}

# Hidden Scavenger Items mapped to specific coordinates (Press parts + NPC Dungeon-Map items!)
WORLD_SCAVENGER_CACHES = {
    (18, 21): ("oak press-frame",          "Oak Press-Frame (Printing Press Part 1/3)"),
    (16, 23): ("broken brass sextant",     "Broken Brass Sextant (Rigger Ronan's Lost Item)"),
    (11, 4):  ("iron screw-spindle",       "Iron Screw-Spindle (Printing Press Part 2/3)"),
    (12, 2):  ("lead type-case",           "Lead Type-Case (Printing Press Part 3/3)"),
    (5, 22):  ("tarnished silver locket",  "Tarnished Silver Locket (Herdsman Ceolwulf's Lost Item)"),
    (3, 12):  ("mason's plumb-bob",        "Mason's Plumb-Bob (The Diewell's Lost Item)"),
    (15, 2):  ("prospector's assay-loupe", "Prospector's Assay-Loupe (Foundryman Aldred's Lost Item)"),
}


def _infer_building_archetype(room_obj, player):
    """Maps any building or tile to one of our 6 Surveyor Architectural Cross-Section Templates."""
    b_id = (player.get("current_building") or "").lower()
    r_name = (room_obj.name if room_obj else "").lower()
    reg = (room_obj.region if room_obj else "").lower()
    combined = f"{b_id} {r_name} {reg}"

    if any(w in combined for w in ("blacksmith", "foundry", "ironworks", "mill", "forge", "mine")):
        return "FORGE_MILL"
    if any(w in combined for w in ("tavern", "pub", "anchor", "casino", "playhouse", "inn")):
        return "TAVERN_INN"
    if any(w in combined for w in ("post", "hall", "customs", "union", "print", "chancery", "office")):
        return "CHANCERY_POST"
    if any(w in combined for w in ("guard", "watch", "castle", "keep", "waystation", "armoury", "wall")):
        return "KEEP_GUARD"
    if any(w in combined for w in ("stable", "wharf", "quay", "granary", "corral", "dock", "harbour")):
        return "WHARF_STABLES"
    if any(w in combined for w in ("hospital", "apothecary", "bakery", "market", "shop", "store")):
        return "APOTHECARY_SHOP"
    return "OUTDOOR_SLUICE"


def get_default_search_spec(pos_tuple, room_obj, player):
    """Generates a 4-hotspot Surveyor Plate + 1 Looking-Glass hotspot for any tile in the world."""
    objs = room_obj.objects if (room_obj and room_obj.objects) else ["Timber Wainscot", "Flagstones", "Corner Recess", "Lintel"]
    arch = _infer_building_archetype(room_obj, player)

    # 4 balanced hotspot zones across the 630x210 architectural viewport
    default_boxes = [
        (45,  55, 135, 100),
        (205, 50, 140, 105),
        (365, 85, 125, 85),
        (505, 60, 105, 105),
    ]
    features = []
    for idx in range(4):
        lbl = f"Inspect the {objs[idx]}" if idx < len(objs) else (
            "Search Beneath the Floorboards / Soil" if idx == 3 else "Examine the Structural Stonework"
        )
        fkey = f"obj_{idx}" if idx < len(objs) else "detritus"
        features.append((lbl, fkey, default_boxes[idx]))

    r_title = room_obj.name.upper() if room_obj else "SURVEY SECTOR"
    return {
        "title": f"{r_title} — ARCHITECTURAL SURVEY",
        "archetype": arch,
        "features": features,
        "spyglass_feature": ("Glass the High Rafters / Distant Ridge", "spy_high", (225, 10, 165, 34)),
        "correct_feature": features[0][1],
        "locked_feature": features[0][1],
        "clue_text": f"You examine the {room_obj.name.lower() if room_obj else 'area'} closely, noting the craftsmanship and recent foot-traffic.",
        "microscope_text": (
            f"[20x MICROSCOPE ANALYSIS]: Magnifying the surface dust at {room_obj.name if room_obj else 'this site'} "
            "reveals trace fibers of dyed wool, coal-soot, and distinct local soil granules."
        ),
    }


# =========================================================================
# 2. INITIALIZATION & ACTION HANDLER (SUPPORTS BOTH MODES + 3 NEW TOOLS)
# =========================================================================
def init_search_modal(player, world_map):
    """Initializes the Search Pop-Out Window (works in both CLASSIC and ARCHITECTURAL modes)."""
    pos = (player["x"], player["y"])
    room = world_map.get(pos)

    raw_spec = SEARCH_DATABASE.get(pos)
    if raw_spec:
        # Ensure all features have 3-tuples (label, key, rect_tuple)
        spec = dict(raw_spec)
        norm_feats = []
        default_boxes = [(45, 55, 135, 100), (205, 50, 140, 105), (365, 85, 125, 85), (505, 60, 105, 105)]
        for i, ft in enumerate(spec.get("features", [])):
            if len(ft) == 2:
                norm_feats.append((ft[0], ft[1], default_boxes[i % 4]))
            else:
                norm_feats.append(ft)
        spec["features"] = norm_feats
        if "archetype" not in spec:
            spec["archetype"] = _infer_building_archetype(room, player)
    else:
        spec = get_default_search_spec(pos, room, player)

    player["search_spec"] = spec
    player["search_phase"] = "SELECT_FEATURE"
    player["search_selected_feature"] = None
    player["search_tool_mode"] = "EYE"  # "EYE", "SPYGLASS"
    style = get_search_style(player)

    if style == "ARCHITECTURAL":
        player["search_feedback"] = (
            f"SURVEYOR'S PLATE ({room.name if room else 'Wilderness'}): Move your cursor across the architectural cross-section "
            "and **Click a Hotspot [I–IV]** to inspect it (or press **[TAB]** to switch to Classic Button Mode)."
        )
    else:
        player["search_feedback"] = (
            f"You pause to investigate **{room.name if room else 'Wilderness'}**. "
            "Select which feature of the scene you wish to inspect (or press **[TAB]** for Architectural Blueprint Mode):"
        )
    return player, player["search_feedback"], "MINIGAME_SEARCH"


def handle_search_canvas_event(event, player):
    """
    Handles mouse clicks on the Architectural Blueprint Canvas and the [TAB] mode toggle
    when menu_state == 'MINIGAME_SEARCH'.
    Returns (handled_bool, log_msg, next_state).
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
        new_st = toggle_search_style(player)
        player["search_feedback"] = f"Switched Search Interface to **{new_st} MODE**."
        return True, None, "MINIGAME_SEARCH"

    if get_search_style(player) != "ARCHITECTURAL":
        return False, None, "MINIGAME_SEARCH"

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if player.get("search_phase") != "SELECT_FEATURE":
            return False, None, "MINIGAME_SEARCH"

        mx, my = event.pos
        spec = player.get("search_spec", {})
        # Canvas origin is (85, 148) with size (630, 210)
        cx, cy = 85, 148

        # Check the 4 standard hotspots
        for lbl, f_key, (rx, ry, rw, rh) in spec.get("features", []):
            h_rect = pygame.Rect(cx + rx, cy + ry, rw, rh)
            if h_rect.collidepoint(mx, my):
                _, l_msg, n_st = search_modal_action("pick_feature", f_key, player)
                return True, l_msg, n_st

        # Check the 5th Looking Glass hotspot (if Looking Glass is owned & active/hovered)
        spy_ft = spec.get("spyglass_feature")
        if spy_ft and "looking glass" in player.get("inventory", []):
            s_lbl, s_key, (rx, ry, rw, rh) = spy_ft
            s_rect = pygame.Rect(cx + rx, cy + ry, rw, rh)
            if s_rect.collidepoint(mx, my):
                _, l_msg, n_st = search_modal_action("pick_feature", s_key, player)
                return True, l_msg, n_st

    return False, None, "MINIGAME_SEARCH"


def search_modal_action(action_type, payload, player):
    """Processes choices in the MINIGAME_SEARCH pop-out window (both Classic and Architectural)."""
    phase = player.get("search_phase", "SELECT_FEATURE")
    spec = player.get("search_spec", {})
    pos = (player["x"], player["y"])
    inv = player.get("inventory", [])

    if action_type == "toggle_style":
        new_s = toggle_search_style(player)
        player["search_feedback"] = f"Search View switched to **{new_s} MODE**."
        return player, None, "MINIGAME_SEARCH"

    if action_type == "toggle_spyglass":
        if "looking glass" not in inv:
            player["search_feedback"] = "You do not carry a **Looking Glass (Spyglass)**! Buy one from a provisioner or chandler."
            return player, None, "MINIGAME_SEARCH"
        cur_m = player.get("search_tool_mode", "EYE")
        player["search_tool_mode"] = "EYE" if cur_m == "SPYGLASS" else "SPYGLASS"
        player["search_feedback"] = (
            "LOOKING GLASS ACTIVE: Sweep the brass spyglass lens across the upper elevation to reveal distant/high-angle "
            "hotspots `[ V ]` invisible to the naked eye!"
            if player["search_tool_mode"] == "SPYGLASS"
            else "Lowered your Looking Glass and returned to standard inspection."
        )
        return player, None, "MINIGAME_SEARCH"

    if phase == "SELECT_FEATURE":
        if action_type == "cancel":
            player["active_ch2_mission"] = None
            return player, "You conclude your inspection and step back.", "MAIN"

        if action_type == "pick_feature":
            feat_key = payload
            player["search_selected_feature"] = feat_key
            player["search_phase"] = "INTERACT_METHOD"

            # Check if this hotspot opens one of our 4 Multi-Room Dungeons!
            if pos == (17, 22) and feat_key == "grate":
                import ch2_dungeons
                return ch2_dungeons.init_dungeon_crawl(player, "parvus_catacombs")
            elif pos == (7, 1) and feat_key == "lintel":
                import ch2_dungeons
                return ch2_dungeons.init_dungeon_crawl(player, "calluna_crypt")
            elif pos == (15, 2) and feat_key == "timber":
                import ch2_dungeons
                return ch2_dungeons.init_dungeon_crawl(player, "caligo_mine")
            elif pos == (3, 12) and feat_key in ("hearth", "cellar"):
                import ch2_dungeons
                return ch2_dungeons.init_dungeon_crawl(player, "old_path_catacombs")

            # Looking Glass 5th Hotspot Discovery!
            if feat_key in ("ridge_cache", "gable_loft", "weir_spy", "roof_vane", "waystation_crag", "brig_spy", "island_spy", "crag_loupe", "spy_high"):
                spy_reward = spec.get("spyglass_item")
                bonus_str = ""
                if spy_reward and spy_reward not in inv:
                    inv.append(spy_reward)
                    bonus_str = f" Using your Looking Glass, you also spot and recover a hidden **{spy_reward.title()}**!"
                elif not player.get(f"spy_spotted_{pos[0]}_{pos[1]}"):
                    player[f"spy_spotted_{pos[0]}_{pos[1]}"] = True
                    player["position_strength"] = min(100, player.get("position_strength", 0) + 5)
                    bonus_str = " (+5% Position Strength from high-angle reconnaissance!)"
                player["search_feedback"] = (
                    f"[LOOKING GLASS RECONNAISSANCE]: Training your three-draw brass telescope on the high elevation reveals "
                    f"vantage markings invisible from the floor!{bonus_str}\n"
                    "Choose how you wish to follow up on this discovery:"
                )
                return player, None, "MINIGAME_SEARCH"

            correct = spec.get("correct_feature")
            is_correct = (feat_key == correct or "obj_0" in feat_key or feat_key == "detritus")
            match_str = spec.get("clue_text", "You find notable traces here.") if is_correct else (
                "You inspect that architectural feature closely, noting weathered stonework and settled dust."
            )
            player["search_feedback"] = f"{match_str}\n\nSelect an investigation method or optical instrument below:"
            return player, None, "MINIGAME_SEARCH"

    elif phase == "INTERACT_METHOD":
        if action_type == "back":
            player["search_phase"] = "SELECT_FEATURE"
            player["search_feedback"] = "Select another hotspot on the Surveyor's Plate (or click a feature button):"
            return player, None, "MINIGAME_SEARCH"

        # Roll with Stylised Dice & Charms if available!
        try:
            import dice_and_charms
            d1, d2, tot, charm_note = dice_and_charms.roll_stylised_2d6(player, context="tool")
        except ImportError:
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            tot, charm_note = d1 + d2, ""

        method = payload  # "sweep", "rummage", "tool", "microscope", "skeleton_key"
        has_pry = any(t in inv for t in ["crowbar", "iron dagger", "masonry drill", "rope", "grappling hook"])

        # Check if this tile has a hidden scavenger cache (Press parts or NPC Dungeon-Map items!)
        cache_note = ""
        if pos in WORLD_SCAVENGER_CACHES:
            c_item, c_label = WORLD_SCAVENGER_CACHES[pos]
            flag_k = f"scavenged_{c_item.replace(' ', '_')}"
            if c_item not in inv and not player.get(flag_k):
                inv.append(c_item)
                player[flag_k] = True
                cache_note = f"\n*** DISCOVERY: You uncovered the **{c_label}**! ***"

        # Also check if a Fluvius / Guard Chapter 2 search hook applies on this tile
        ch2_note = ""
        try:
            import ch2_union
            import ch2_guard
            h_u, u_msg = ch2_union.handle_fluvius_search(player)
            if h_u and u_msg:
                ch2_note = f"\n{u_msg}"
            else:
                h_g, g_msg = ch2_guard.handle_guard_fluvius_search(player)
                if h_g and g_msg:
                    ch2_note = f"\n{g_msg}"
        except ImportError:
            pass

        if method == "microscope":
            if "brass microscope" not in inv:
                player["search_feedback"] = "You do not carry a **Brass Microscope**! Purchase one from an apothecary or guild optician."
                return player, None, "MINIGAME_SEARCH"
            player, _ = advance_time(10, player)
            m_txt = spec.get("microscope_text", "[20x MICROSCOPE]: You identify telltale microscopic striations and mineral grains!")
            if not player.get(f"micro_bonus_{pos[0]}_{pos[1]}"):
                player[f"micro_bonus_{pos[0]}_{pos[1]}"] = True
                player["position_strength"] = min(100, player.get("position_strength", 0) + 6)
                m_txt += " (+6% Position Strength from forensic proof!)"
            msg = f"{m_txt}{cache_note}{ch2_note}"

        elif method == "skeleton_key":
            if "skeleton key" not in inv:
                player["search_feedback"] = "You do not possess a **Skeleton Key**!"
                return player, None, "MINIGAME_SEARCH"
            player, _ = advance_time(5, player)
            player["position_strength"] = min(100, player.get("position_strength", 0) + 5)
            msg = (
                "[SKELETON KEY APPLIED (5m — Zero Noise, Automatic Success!)]: Your star-iron master ward key turns the "
                f"lock-tumblers like oiled silk, opening the sealed compartment without leaving a scratch! (+5% Position Strength){cache_note}{ch2_note}"
            )

        elif method == "sweep":
            player, _ = advance_time(10, player)
            msg = (
                f"[Visual Sweep (10m): Roll {d1}+{d2}={tot} {charm_note}] You carefully survey the surface from a safe distance, "
                f"recording all visible markings without disturbing the dust.{cache_note}{ch2_note}"
            )

        elif method == "tool":
            if not has_pry:
                player["search_feedback"] = "You lack a suitable prying tool (Crowbar, Dagger, Masonry Drill, or Rope) in your inventory!"
                return player, None, "MINIGAME_SEARCH"
            player, _ = advance_time(10, player)
            msg = (
                f"[Prying Tool Applied (10m): Roll {d1}+{d2}={tot} {charm_note}] Using your tool's leverage, you force the "
                f"fixture open and expose the interior recess!{cache_note}{ch2_note}"
            )

        else:  # "rummage"
            player, _ = advance_time(15, player)
            if tot <= 4:
                from mechanics import calculate_stat_based_hp_loss
                loss, mit_s = calculate_stat_based_hp_loss(1, player, "Hidden Snag")
                player["health"] = max(1, player.get("health", 10) - loss)
                msg = (
                    f"[Hands-On Rummage (15m): Roll {d1}+{d2}={tot} {charm_note}] Reaching into the dark recess, your hand "
                    f"grazes a rusted iron barb (-{loss} HP{mit_s}), though you pull out the contents!{cache_note}{ch2_note}"
                )
            elif tot >= 10:
                player["silver"] += 6
                msg = (
                    f"[Hands-On Rummage (15m): Roll {d1}+{d2}={tot} {charm_note} (Windfall!)] Searching deep inside the recess, "
                    f"you uncover the hidden traces AND a forgotten pouch containing **6 Silver**!{cache_note}{ch2_note}"
                )
            else:
                msg = (
                    f"[Hands-On Rummage (15m): Roll {d1}+{d2}={tot} {charm_note}] You thoroughly sift through the recess, "
                    f"recovering every physical clue inside.{cache_note}{ch2_note}"
                )

        player["search_phase"] = "RESULT"
        player["search_last_method"] = method
        player["search_feedback"] = msg
        return player, msg, "MINIGAME_SEARCH"

    elif phase == "RESULT":
        player["active_ch2_mission"] = None
        return player, "You close your surveyor's notebook and return to the road.", "MAIN"

    return player, None, "MINIGAME_SEARCH"


# =========================================================================
# 3. 1880s SURVEYOR'S ARCHITECTURAL CROSS-SECTION RENDERER
# =========================================================================
def _draw_architectural_plate(screen, rect, spec, player, mouse_pos):
    """
    Renders a refined 19th-Century Copperplate Surveyor's Architectural Elevation
    with sepia drafting grid, structural cross-hatching, hotspot callout nodes [I-IV],
    Looking Glass [V] high-elevation node, and Night Lantern spotlight!
    """
    PAPER_BG = (242, 236, 220)
    GRID_FAINT = (224, 216, 198)
    SEPIA_INK = (52, 42, 34)
    SEPIA_LIGHT = (120, 105, 88)
    TATE_RED = (168, 50, 35)
    BRASS_GOLD = (195, 145, 45)
    BLUEPRINT_CYAN = (42, 105, 145)

    # 1. Parchment Drafting Sheet & Fine Millimetre Grid
    pygame.draw.rect(screen, PAPER_BG, rect, border_radius=6)
    for gx in range(rect.left + 15, rect.right, 15):
        pygame.draw.line(screen, GRID_FAINT, (gx, rect.top + 2), (gx, rect.bottom - 2), 1)
    for gy in range(rect.top + 15, rect.bottom, 15):
        pygame.draw.line(screen, GRID_FAINT, (rect.left + 2, gy), (rect.right - 2, gy), 1)

    # Double Copperplate Border & Scale Ruler Ticks
    pygame.draw.rect(screen, SEPIA_INK, rect, width=2, border_radius=6)
    pygame.draw.rect(screen, SEPIA_LIGHT, rect.inflate(-6, -6), width=1, border_radius=4)

    tiny_f = pygame.font.Font(None, 14)
    arch = spec.get("archetype", "CHANCERY_POST")
    plate_hdr = f"FIG. 1 — ARCHITECTURAL ELEVATION ({arch.replace('_', ' ')})   |   SCALE 1:24 DECIMAL"
    screen.blit(tiny_f.render(plate_hdr, True, SEPIA_LIGHT), (rect.left + 10, rect.bottom - 14))

    # 2. Draw Structural Elevation Linework by Archetype (Pen-and-Ink Cross-Section)
    ox, oy = rect.left, rect.top
    floor_y = oy + 172
    # Heavy masonry floor line with diagonal earth cross-hatching underneath
    pygame.draw.line(screen, SEPIA_INK, (ox + 12, floor_y), (rect.right - 12, floor_y), 2)
    for hx in range(ox + 16, rect.right - 16, 12):
        pygame.draw.line(screen, SEPIA_LIGHT, (hx, floor_y), (hx - 6, floor_y + 10), 1)

    # Roof trusses / upper cornice line
    pygame.draw.line(screen, SEPIA_INK, (ox + 12, oy + 46), (rect.right - 12, oy + 46), 1)

    if arch == "FORGE_MILL":
        # Waterwheel / Gear-Wheel radial elevation on left + Brick Furnace Arch in center + Timber Loft on right
        wx, wy = ox + 115, oy + 106
        pygame.draw.circle(screen, SEPIA_INK, (wx, wy), 46, 2)
        pygame.draw.circle(screen, SEPIA_INK, (wx, wy), 12, 2)
        for ang in range(0, 360, 30):
            rad = math.radians(ang)
            pygame.draw.line(screen, SEPIA_INK, (wx, wy), (int(wx + 46 * math.cos(rad)), int(wy + 46 * math.sin(rad))), 1)
        # Central Axle Shaft & Brick Hearth Arch
        pygame.draw.rect(screen, SEPIA_INK, (ox + 215, oy + 96, 145, 22), 2)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 455, oy + 46, 140, 126), 1)
        pygame.draw.line(screen, SEPIA_INK, (ox + 455, oy + 105), (ox + 595, oy + 105), 2)

    elif arch == "CHANCERY_POST":
        # Postbox Pillar (Left), Pigeon-Hole Grid (Center-Left), Clerk Desk (Center-Right), Leaded Colonnade (Right)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 68, oy + 72, 75, 100), 2)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 82, oy + 92, 46, 10), 2)  # Post slot
        # Pigeon-holes grid
        for r in range(3):
            for c in range(5):
                pygame.draw.rect(screen, SEPIA_INK, (ox + 205 + c * 28, oy + 58 + r * 24, 28, 24), 1)
        # Clerk Desk & Ledger
        pygame.draw.rect(screen, SEPIA_INK, (ox + 385, oy + 112, 115, 60), 2)
        pygame.draw.polygon(screen, SEPIA_INK, [(ox + 395, oy + 112), (ox + 490, oy + 112), (ox + 475, oy + 96), (ox + 410, oy + 96)], 2)

    elif arch == "KEEP_GUARD":
        # Dressed Ashlar Stone Archway (Left), Central Chimney Hearth & Flue, Flagstone Trapdoor (Right)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 58, oy + 46, 130, 126), 2)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 250, oy + 46, 135, 126), 2)
        pygame.draw.arc(screen, SEPIA_INK, (ox + 265, oy + 95, 105, 80), 0, math.pi, 2)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 440, oy + 148, 140, 24), 2)

    elif arch == "WHARF_STABLES":
        # Timber Corral Fence (Left), Brick Weigh-Beam & Scale (Center), Stacked Sacks (Right)
        for px in range(ox + 52, ox + 175, 22):
            pygame.draw.line(screen, SEPIA_INK, (px, oy + 75), (px, floor_y), 2)
        pygame.draw.line(screen, SEPIA_INK, (ox + 50, oy + 95), (ox + 175, oy + 95), 2)
        pygame.draw.line(screen, SEPIA_INK, (ox + 50, oy + 135), (ox + 175, oy + 135), 2)
        # Weigh-Beam Gallows
        pygame.draw.line(screen, SEPIA_INK, (ox + 280, oy + 62), (ox + 280, floor_y), 3)
        pygame.draw.line(screen, SEPIA_INK, (ox + 230, oy + 78), (ox + 330, oy + 78), 2)

    else:
        # Universal Architectural / Outdoor Cross-Section (Arches, Boulders, Sluice/Counter)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 65, oy + 68, 120, 104), 2)
        pygame.draw.line(screen, SEPIA_INK, (ox + 65, oy + 68), (ox + 185, oy + 172), 1)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 235, oy + 80, 130, 92), 2)
        pygame.draw.rect(screen, SEPIA_INK, (ox + 390, oy + 95, 200, 77), 1)

    # 3. Draw Interactive Hotspot Callout Frames & Roman Numeral Nodes [I - IV]
    romans = ["I", "II", "III", "IV", "V"]
    hovered_label = None
    sel_key = player.get("search_selected_feature")
    bold_sm = pygame.font.Font(None, 17)

    all_feats = list(spec.get("features", []))
    # Include the 5th Looking Glass Hotspot if player is using Looking Glass (or owns it & hovers near top)
    spy_ft = spec.get("spyglass_feature")
    spy_active = (player.get("search_tool_mode") == "SPYGLASS") or ("looking glass" in player.get("inventory", []))
    if spy_ft and spy_active:
        all_feats.append(spy_ft)

    for idx, (f_lbl, f_key, (rx, ry, rw, rh)) in enumerate(all_feats):
        h_rect = pygame.Rect(ox + rx, oy + ry, rw, rh)
        is_hov = h_rect.collidepoint(mouse_pos)
        is_sel = (f_key == sel_key)
        is_spy = (idx == 4)

        if is_hov:
            hovered_label = (f"[LOOKING GLASS NODE V] {f_lbl}" if is_spy else f"[HOTSPOT {romans[idx]}] {f_lbl}") + "  (Click to Inspect)"

        # Subtle architectural dashed/corner bracket frame
        col = BLUEPRINT_CYAN if is_spy else (TATE_RED if (is_hov or is_sel) else SEPIA_LIGHT)
        if is_hov or is_sel:
            fill_s = pygame.Surface((rw, rh), pygame.SRCALPHA)
            fill_s.fill((195, 145, 45, 45) if not is_spy else (42, 105, 145, 45))
            screen.blit(fill_s, h_rect.topleft)
            pygame.draw.rect(screen, col, h_rect, width=2, border_radius=4)
        else:
            pygame.draw.rect(screen, col, h_rect, width=1, border_radius=4)

        # Brass Callout Medallion in top-left of each hotspot
        badge_r = pygame.Rect(h_rect.left + 4, h_rect.top + 4, 24, 18)
        pygame.draw.rect(screen, col if (is_hov or is_sel) else PAPER_BG, badge_r, border_radius=3)
        pygame.draw.rect(screen, col, badge_r, width=1, border_radius=3)
        r_txt = bold_sm.render(romans[idx], True, PAPER_BG if (is_hov or is_sel) else col)
        screen.blit(r_txt, r_txt.get_rect(center=badge_r.center))

        # Concise caption inside bottom of hotspot box
        short_cap = f_lbl.replace("Inspect the ", "").replace("Examine the ", "").replace("Check the ", "")
        draw_fitted_text(screen, short_cap, pygame.Rect(h_rect.left + 5, h_rect.bottom - 20, rw - 10, 18), SEPIA_INK, bold=is_hov, max_lines=1)

    # 4. Night / Underground Lantern Spotlight Effect!
    try:
        import weather_engine as we
        light_info = we.get_daylight_state(player)
        if light_info.get("is_dark") and not player.get("current_building"):
            dark_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            dark_surf.fill((12, 14, 22, 185 if not light_info.get("has_light") else 135))
            if rect.collidepoint(mouse_pos):
                lx, ly = mouse_pos[0] - rect.left, mouse_pos[1] - rect.top
                rad = 95 if light_info.get("has_light") else 42
                pygame.draw.circle(dark_surf, (0, 0, 0, 0), (lx, ly), rad)
                pygame.draw.circle(screen, BRASS_GOLD, mouse_pos, rad, 1)
            screen.blit(dark_surf, rect.topleft)
    except ImportError:
        pass

    # 5. If Looking Glass Mode is toggled ON, draw a Brass Spyglass Reticle around cursor!
    if player.get("search_tool_mode") == "SPYGLASS" and rect.collidepoint(mouse_pos):
        pygame.draw.circle(screen, BLUEPRINT_CYAN, mouse_pos, 38, 2)
        pygame.draw.line(screen, BLUEPRINT_CYAN, (mouse_pos[0] - 44, mouse_pos[1]), (mouse_pos[0] + 44, mouse_pos[1]), 1)
        pygame.draw.line(screen, BLUEPRINT_CYAN, (mouse_pos[0], mouse_pos[1] - 44), (mouse_pos[0], mouse_pos[1] + 44), 1)

    # Hover Banner at top of Blueprint
    if hovered_label:
        banner = pygame.Rect(rect.left + 8, rect.top + 6, rect.width - 16, 22)
        pygame.draw.rect(screen, (32, 36, 44), banner, border_radius=4)
        draw_fitted_text(screen, hovered_label, banner.inflate(-10, -2), (255, 220, 110), bold=True, max_lines=1)


# =========================================================================
# 4. MAIN POP-OUT RENDERER (DRAWS CLASSIC OR ARCHITECTURAL VIEW)
# =========================================================================
def draw_search_ui(screen, player, font, font_bold, mouse_pos=None):
    """Draws the 680x480 Pop-Out Window in either ARCHITECTURAL or CLASSIC mode."""
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 195))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)

    panel = pygame.Rect(60, 30, 680, 510)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    spec = player.get("search_spec", {})
    style = get_search_style(player)

    draw_fitted_text(
        screen, f"{spec.get('title', 'SCENE INVESTIGATION')}  [{style} MODE]",
        pygame.Rect(85, 40, 630, 24), TATE_RED, bold=True, max_lines=1
    )

    # Top Transcript / Feedback Box
    fb_h = 74 if style == "ARCHITECTURAL" else 140
    fb_box = pygame.Rect(85, 68, 630, fb_h)
    pygame.draw.rect(screen, (252, 248, 238), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("search_feedback", ""), fb_box.inflate(-16, -8), CLOCK_BLACK, max_lines=4 if style == "ARCHITECTURAL" else 6)

    # Middle Canvas (Only drawn in ARCHITECTURAL mode!)
    if style == "ARCHITECTURAL":
        canvas_rect = pygame.Rect(85, 148, 630, 210)
        _draw_architectural_plate(screen, canvas_rect, spec, player, mouse_pos)
