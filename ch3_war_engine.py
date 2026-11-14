"""
ch3_war_engine.py
-----------------
Manages Chapter 3 grand strategy initialisation, configurable Victory
Modes (100 Pts, 250 Pts, Total Domination), symmetric AI Dawn Dice &
10-MP turn execution, Zero-Army Captain/Private Solo Commando operations,
0-battalion ghost-unit pruning, and the Epilogue Chronicle.
"""

import random
import pygame
import pass_and_play
import weather_engine

CH3_VICTORY_GOAL = 100
MP_PER_DIE = 10

REPUBLICAN_MONTHS = (
    "Vendémiaire",
    "Brumaire",
    "Frimaire",
    "Nivôse",
    "Pluviôse",
    "Ventôse",
    "Germinal",
    "Floréal",
    "Prairial",
    "Messidor",
    "Thermidor",
    "Fructidor",
)

VICTORY_MODE_SPECS = {
    "100_PTS": {
        "label": "100 PTS (Standard)",
        "goal": 100,
        "territory_pts": 4,
        "stronghold_pts": 15,
    },
    "250_PTS": {
        "label": "250 PTS (Grand War)",
        "goal": 250,
        "territory_pts": 6,
        "stronghold_pts": 25,
    },
    "DOMINATION": {
        "label": "TOTAL DOMINATION (7 Keeps)",
        "goal": 999,
        "territory_pts": 4,
        "stronghold_pts": 15,
    },
}

MAJOR_STRONGHOLD_TILES = (
    "11,4",
    "10,14",
    "15,10",
    "5,15",
    "14,2",
    "5,5",
    "6,8",
)

DTESSERA_FACTIONS = {
    "Union": {
        "sympathy_type": "Fairness",
        "color": (185, 48, 38),
        "crest": (240, 215, 145),
        "title": "The Workers' Union",
        "advantages": ("Barricades", "Strength in Numbers"),
        "agenda_desc": (
            "+4 Pts per Barricaded Town/Farm corridor & +2 Pts per "
            "Fairness surge"
        ),
    },
    "Kokeshi": {
        "sympathy_type": "Wealth",
        "color": (112, 48, 142),
        "crest": (235, 195, 75),
        "title": "Kokeshi Syndicate",
        "advantages": ("Bribery", "Underhand Tactics"),
        "agenda_desc": (
            "+5 Pts per Bribed Garrison & +3 Pts per 40 Silver in "
            "Syndicate Vaults"
        ),
    },
    "Laydere": {
        "sympathy_type": "Order",
        "color": (45, 88, 165),
        "crest": (215, 225, 240),
        "title": "Castle Laydere",
        "advantages": (
            "Superior Weapons (Close Quarters)",
            "Military Expertise",
        ),
        "agenda_desc": (
            "+5 Pts per Walled/Road Checkpoint held & Close-Quarters "
            "victories"
        ),
    },
    "Ragmore": {
        "sympathy_type": "Order",
        "color": (152, 38, 58),
        "crest": (240, 190, 65),
        "title": "Castle Ragmore",
        "advantages": ("Superior Weapons (Long Range)", "Military Expertise"),
        "agenda_desc": (
            "+5 Pts per Fortified High-Ground/Keep & Long-Range Volley "
            "dominance"
        ),
    },
    "FAI": {
        "sympathy_type": "Fairness",
        "color": (52, 52, 58),
        "crest": (215, 68, 45),
        "title": "F.A.I. Revolutionary Syndicate",
        "advantages": ("Guerrilla Warfare", "Underhand Tactics"),
        "agenda_desc": (
            "+5 Pts per Severed Enemy Supply Line & Sabotaged Stronghold"
        ),
    },
    "Communards": {
        "sympathy_type": "Nature",
        "color": (42, 132, 74),
        "crest": (225, 238, 180),
        "title": "Lignum Communards",
        "advantages": ("Fog of War", "Praxis"),
        "agenda_desc": (
            "+5 Pts per Clearing peacefully converted to a Commune via Praxis"
        ),
    },
    "Vanguardists": {
        "sympathy_type": "Nature",
        "color": (28, 85, 48),
        "crest": (140, 220, 148),
        "title": "Wilderness Vanguardists",
        "advantages": ("Fog of War", "Guerrilla Warfare"),
        "agenda_desc": (
            "+5 Pts per Fortification dismantled & Forest Ambush victory"
        ),
    },
}

EPILOGUE_CHRONICLES = {
    "Union": (
        "THE COMMONWEALTH OF THE LOOM AND PLOUGH",
        "Red-and-gold Union standards fly above the guildhalls from Fluvius "
        "to Murum. The feudal toll-bars are dismantled, the watermills and "
        "granaries pass into cooperative worker stewardship, and the Grand "
        "Strike Charter becomes the constitutional law of Dtessera Terra.",
    ),
    "Kokeshi": (
        "THE VELVET DIRECTORATE OF THE SYNDICATE",
        "Not a single royal decree is signed without the violet seal of the "
        "Kokeshi counting-houses. Through debt ledgers, bribed garrisons, and "
        "monopolised wharves, the Wallmaker Syndicate rules Dtessera Terra "
        "from the shadows behind every magistrate's bench.",
    ),
    "Laydere": (
        "THE IRON PAX OF CASTLE LAYDERE",
        "Castellan Eormenhild's steel halberdiers garrison every bridge and "
        "town gate. Standardised weights, strict curfew bells, and military "
        "tribunals replace the old baronial rivalries, forging an austere "
        "and unyielding order across the island.",
    ),
    "Ragmore": (
        "THE RESTORED FEUDAL ASCENDANCY OF RAGMORE",
        "Black-and-crimson banners snap from the high keep of Castle Ragmore "
        "to the southern quays. Castellan Hrothgar's longbowmen and heavy "
        "lancers restore the ancient feudal charters, binding town and "
        "farmland alike to the service of the high seat.",
    ),
    "FAI": (
        "THE FREE SYNDICATES OF THE MARITIME COMMUNE",
        "From the fortified quays of Parvus Town, the Iberian-inspired "
        "federation abolishes prefects, bailiffs, and feudal levies alike. "
        "Federated neighbourhood assemblies and armed worker militias govern "
        "the island in turbulent, fiercely guarded liberty.",
    ),
    "Communards": (
        "THE SYLVAN COMMONS OF LIGNUM GLADE",
        "Fence-stakes and boundary walls are pulled down across the valleys. "
        "Through lived mutual aid and peaceful praxis, townsfolk and woodland "
        "communards share the harvests of orchard, river, and forest without "
        "lord or bailiff.",
    ),
    "Vanguardists": (
        "THE UNTAMED SOVEREIGNTY OF THE DEEP WILDS",
        "The sawmills, silver mines, and stone toll-roads are cracked open "
        "and reclaimed by oak root and briar. The Vanguardist packs patrol a "
        "rewilded Dtessera Terra where the ancient forest rules supreme.",
    ),
}


def get_victory_goal(player):
    """Returns the active Hegemony Point goal (100, 250, or 999 for Domination)."""
    mode = player.get("ch3_victory_mode", "100_PTS")
    return VICTORY_MODE_SPECS.get(mode, VICTORY_MODE_SPECS["100_PTS"])["goal"]


def get_victory_goal_info(player):
    """Returns (goal_int, mode_code, short_label) for ui_renderer.py."""
    mode = player.get("ch3_victory_mode", "100_PTS")
    if mode == "250_PTS":
        return 250, "250_PTS", "250 Pts"
    if mode == "DOMINATION":
        return 7, "DOMINATION", "7/7 Keeps"
    return 100, "100_PTS", "100 Pts"


def player_has_active_armies(player):
    """Returns True if the player's faction has at least 1 army on the map."""
    return not player_has_zero_armies(player)


def count_faction_strongholds(player, faction_key):
    """Returns how many of the 7 Major Strongholds `faction_key` rules."""
    territories = player.get("territories", {})
    return sum(
        1
        for tile_k in MAJOR_STRONGHOLD_TILES
        if territories.get(tile_k) == faction_key
    )


def _landmark_label(pos_key, world_map):
    """Translates a 'x,y' key into a narrative landmark title."""
    if not world_map or not isinstance(pos_key, str) or "," not in pos_key:
        return "the contested sector"
    try:
        gx, gy = map(int, pos_key.split(","))
    except ValueError:
        return "the contested sector"
    loc = world_map.get((gx, gy))
    if not loc:
        return "the frontier approach"
    if loc.name and loc.name != "x":
        return loc.name
    return f"the {loc.region} sector"


def prune_empty_armies(player):
    """
    Dead End 4 Sanitizer: Removes any 0-battalion ghost armies from
    `player['ch3_armies']` and cleans up any orphaned `ch3_pending_clashes`.
    """
    armies = player.get("ch3_armies", {})
    empty_keys = [
        pos for pos, a in armies.items() if not a or a.get("count", 0) <= 0
    ]
    for pos in empty_keys:
        armies.pop(pos, None)

    clashes = player.get("ch3_pending_clashes", [])
    if clashes:
        player["ch3_pending_clashes"] = [
            c
            for c in clashes
            if c.get("attacker", {}).get("count", 0) > 0
            and c.get("defender", {}).get("count", 0) > 0
        ]
    return player


def player_has_zero_armies(player):
    """Returns True if the human player's faction currently has 0 battalions on the board."""
    prune_empty_armies(player)
    my_fac = player.get("ch3_faction", "Union")
    armies = player.get("ch3_armies", {})
    clashes = player.get("ch3_pending_clashes", [])

    on_board = any(
        a.get("faction") in (my_fac, "Player") and a.get("count", 0) > 0
        for a in armies.values()
    )
    in_clash = any(
        c.get("attacker", {}).get("faction") == my_fac
        or c.get("defender", {}).get("faction") == my_fac
        for c in clashes
    )
    return not (on_board or in_clash)


def calculate_ch1_ch2_legacy_points(player, faction_key):
    """
    Calculates starting Legacy Points (10 to 35 pts) from the 10-bit
    vector, Chapter 1 attribute mastery, and Chapter 2 mission standing.
    """
    bits = player.get("ch3_world_bits", {})
    is_player_fac = faction_key == player.get("ch3_faction", "Union")

    bit_alignment = {
        "Union": [
            bits.get("track_1", 0) == 1,
            bits.get("track_7", 0) == 1,
            bits.get("track_10", 0) == 1,
        ],
        "Kokeshi": [
            bits.get("track_8", 0) == 1,
            bits.get("track_3", 0) == 0,
            bits.get("track_1", 0) == 0,
        ],
        "Laydere": [
            bits.get("track_2", 0) == 0,
            bits.get("track_5", 0) == 1,
            bits.get("track_6", 0) == 0,
        ],
        "Ragmore": [
            bits.get("track_2", 0) == 1,
            bits.get("track_3", 0) == 1,
            bits.get("track_9", 0) == 0,
        ],
        "FAI": [
            bits.get("track_4", 0) == 1,
            bits.get("track_6", 0) == 1,
            bits.get("track_10", 0) == 1,
        ],
        "Communards": [
            bits.get("track_10", 0) == 1,
            bits.get("track_1", 0) == 1,
            bits.get("track_9", 0) == 1,
        ],
        "Vanguardists": [
            bits.get("track_9", 0) == 1,
            bits.get("track_3", 0) == 0,
            bits.get("track_10", 0) == 1,
        ],
    }
    vector_pts = sum(4 for cond in bit_alignment.get(faction_key, []) if cond)
    vector_pts += 8

    if not is_player_fac:
        return min(30, vector_pts)

    stat_sum = (
        player.get("strength", 0)
        + player.get("charisma", 0)
        + player.get("stealth", 0)
        + player.get("influence", 0)
        + player.get("equusense", 0)
    )
    ch1_stat_pts = min(8, stat_sum // 3)

    pos_raw = (player.get("position_strength", 50) // 10) - (
        player.get("exposure_tells", 0) * 2
    )
    ch2_pos_pts = max(0, min(12, pos_raw))

    asset_pts = 0
    inv = player.get("inventory", [])
    skills = player.get("skills", [])
    if "portable printing press" in inv:
        asset_pts += 3
    if any(
        s in skills
        for s in (
            "master blacksmith",
            "intelligence officer",
            "mayor's footman",
            "radical theory",
        )
    ):
        asset_pts += 2

    total_legacy = vector_pts + ch1_stat_pts + ch2_pos_pts + asset_pts
    return max(10, min(35, total_legacy))


def init_chapter_3_world_board(player, world_map):
    """
    Translates the 10-bit world state vector into the physical Day 1
    starting board, grants the War Manual, and seeds faction armies.
    """
    bits = player.get("ch3_world_bits", {})

    player["ch3_factions"] = {
        "Union": {"sympathy": 10, "silver": 50, "capital": "11,4"},
        "Kokeshi": {"sympathy": 15, "silver": 200, "capital": "10,14"},
        "Laydere": {"sympathy": 20, "silver": 100, "capital": "15,10"},
        "Ragmore": {"sympathy": 20, "silver": 80, "capital": "5,15"},
        "FAI": {"sympathy": 10, "silver": 40, "capital": "14,2"},
        "Communards": {"sympathy": 15, "silver": 0, "capital": "5,5"},
        "Vanguardists": {"sympathy": 5, "silver": 20, "capital": "6,8"},
    }

    player["ch3_armies"] = {}
    player["ch3_pending_clashes"] = []
    player["ch3_ai_turn_queue"] = []
    player.setdefault("territories", {})
    player.setdefault("ch3_barricades", {})
    player.setdefault("ch3_day", 1)
    player.setdefault("ch3_standing", player.get("reputation", 10))
    player.setdefault("ch3_confidence", 65)
    player.setdefault("ch3_tactical_tokens", 0)
    player.setdefault("ch3_alliances", {})
    player.setdefault("ch3_victory_mode", "100_PTS")

    def spawn_army(pos, faction, count, barricaded=False):
        player["ch3_armies"][pos] = {"faction": faction, "count": count}
        player["territories"][pos] = faction
        if barricaded:
            player["ch3_barricades"][pos] = True

    for f_key, f_info in player["ch3_factions"].items():
        player["territories"][f_info["capital"]] = f_key

    if bits.get("track_1") == 1:
        spawn_army("10,6", "Union", 5, barricaded=True)
        spawn_army("10,10", "Union", 5, barricaded=True)
    else:
        spawn_army("10,6", "Kokeshi", 3)
        spawn_army("10,10", "Ragmore", 4)

    if bits.get("track_2") == 1:
        spawn_army("8,12", "Ragmore", 6, barricaded=True)
    else:
        spawn_army("8,12", "Laydere", 6, barricaded=True)

    if bits.get("track_3") == 1:
        spawn_army("5,15", "Ragmore", 10)
    else:
        spawn_army("5,15", "Ragmore", 4)
        spawn_army("6,14", "Kokeshi", 3)

    if bits.get("track_4") == 1:
        spawn_army("14,2", "FAI", 7, barricaded=True)
        player["ch3_factions"]["FAI"]["sympathy"] += 10
    elif bits.get("track_5") == 1:
        spawn_army("14,2", "Laydere", 6)
    else:
        spawn_army("14,2", "Kokeshi", 5)

    if bits.get("track_6") == 1:
        player["ch3_factions"]["FAI"]["silver"] += 50
    else:
        player["ch3_factions"]["Laydere"]["silver"] += 50
        spawn_army("13,3", "Laydere", 4)

    if bits.get("track_7") == 1:
        spawn_army("10,14", "Union", 6, barricaded=True)
    elif bits.get("track_8") == 1:
        spawn_army("10,14", "Kokeshi", 7)
    else:
        spawn_army("10,14", "Ragmore", 5)

    if bits.get("track_9") == 1:
        spawn_army("9,9", "Vanguardists", 4)
        spawn_army("12,8", "Kokeshi", 3)
    else:
        spawn_army("9,9", "Laydere", 4)
        spawn_army("12,8", "Ragmore", 4)

    if bits.get("track_10") == 1:
        player["ch3_factions"]["Union"]["sympathy"] += 5
        player["ch3_factions"]["Communards"]["sympathy"] += 5
    else:
        player["ch3_factions"]["Laydere"]["sympathy"] += 5
        player["ch3_factions"]["Ragmore"]["sympathy"] += 5

    spawn_army("5,5", "Communards", 5)

    my_fac = player.get("ch3_faction", "Union")
    if not any(
        a.get("faction") == my_fac for a in player["ch3_armies"].values()
    ):
        cap = player["ch3_factions"].get(my_fac, {}).get("capital", "11,4")
        spawn_army(cap, my_fac, 6, barricaded=(my_fac == "Union"))

    inv = player.setdefault("inventory", [])
    if "war manual" not in inv:
        inv.append("war manual")

    assign_daily_orders(player, world_map)
    recalculate_ch3_total_points(player)
    return player


def recalculate_ch3_total_points(player):
    """
    Computes each faction's live score according to the active Victory Mode
    ('100_PTS', '250_PTS', or 'DOMINATION').
    """
    prune_empty_armies(player)
    factions = player.setdefault("ch3_factions", {})
    territories = player.get("territories", {})
    barricades = player.get("ch3_barricades", {})
    mode = player.get("ch3_victory_mode", "100_PTS")
    m_spec = VICTORY_MODE_SPECS.get(mode, VICTORY_MODE_SPECS["100_PTS"])
    pts_per_tile = m_spec["territory_pts"]
    goal = m_spec["goal"]

    for f_key in DTESSERA_FACTIONS:
        f_data = factions.setdefault(
            f_key, {"sympathy": 10, "silver": 50, "capital": "10,14"}
        )
        if "legacy_pts" not in f_data:
            f_data["legacy_pts"] = calculate_ch1_ch2_legacy_points(
                player, f_key
            )
        f_data.setdefault("agenda_pts", 0)

        ruled = [pos for pos, owner in territories.items() if owner == f_key]
        territory_pts = len(ruled) * pts_per_tile
        if f_key == "Union":
            territory_pts += sum(2 for pos in ruled if barricades.get(pos))

        sympathy_cap = 40 if mode == "250_PTS" else 20
        sympathy_pts = min(sympathy_cap, f_data.get("sympathy", 10) // 2)
        total = (
            f_data["legacy_pts"]
            + territory_pts
            + sympathy_pts
            + f_data["agenda_pts"]
        )
        f_data["total_points"] = min(goal, total)
        f_data["strongholds_held"] = count_faction_strongholds(player, f_key)

    return player


def assign_daily_orders(player, world_map):
    """
    Generates a daily frontline objective for Captains and Privates
    using natural landmark names.
    """
    my_faction = player.get("ch3_faction", "Union")
    territories = player.get("territories", {})

    target_coord = (10, 10)
    for pos_str, owner in territories.items():
        if owner != my_faction and "," in pos_str:
            parts = pos_str.split(",")
            target_coord = (int(parts[0]), int(parts[1]))
            break

    loc = world_map.get(target_coord) if world_map else None
    dest_name = (
        loc.name if (loc and loc.name != "x") else "the Fluvius Crossroads"
    )
    dest_region = loc.region if loc else "the Contested Valley"

    missions = [
        (
            "recon_scout",
            f"March to {dest_name} in {dest_region} and Search the "
            "clearing for enemy dispatches.",
        ),
        (
            "plant_barricade",
            f"Advance to {dest_name} in {dest_region} and secure the "
            "perimeter before Dusk.",
        ),
        (
            "cut_supply",
            f"Infiltrate {dest_name} in {dest_region} and sabotage the "
            "rival baggage train.",
        ),
    ]
    m_type, m_desc = random.choice(missions)
    player["ch3_daily_order"] = {
        "type": m_type,
        "target_pos": list(target_coord),
        "description": m_desc,
        "completed": False,
    }
    return player["ch3_daily_order"]


def start_private_afternoon_march(player, world_map):
    """
    Switches a Private from the Chapter 3 War Ledger into the first-person
    'MAIN' RPG view for the Afternoon march.
    """
    order = player.get("ch3_daily_order") or assign_daily_orders(
        player, world_map
    )
    player["ch3_private_field_mode"] = True
    mp_raw = player.get("movement_points", 20)
    dice_equiv = mp_raw // 10 if mp_raw >= 10 else mp_raw
    player["ch3_private_steps_left"] = 4 + max(1, int(dice_equiv))

    log_msg = (
        "=== AFTERNOON PHASE: ON THE MARCH (FIRST-PERSON FIELD MODE) ===\n"
        f"Captain's Directive: \"{order['description']}\"\n"
        "Use the D-Pad, Search, and RPG actions to reach your objective "
        f"before Dusk ({player['ch3_private_steps_left']} march steps "
        "remaining). Completing your field objective awards +2 Tactical "
        "Advantage Tokens for tonight's Evening Clash!"
    )
    return player, log_msg, "MAIN"


def check_private_afternoon_progress(player, world_map, action_taken="move"):
    """
    Checks if a Private marching in 'MAIN' reached their ordered clearing
    or ran out of Afternoon daylight.
    """
    if not player.get("ch3_private_field_mode"):
        return False, ""

    order = player.get("ch3_daily_order", {})
    t_pos = order.get("target_pos", [player["x"], player["y"]])
    tx, ty = int(t_pos[0]), int(t_pos[1])

    if action_taken == "move":
        player["ch3_private_steps_left"] = max(
            0, player.get("ch3_private_steps_left", 4) - 1
        )

    if (player["x"], player["y"]) == (tx, ty) and not order.get("completed"):
        if action_taken in ("search", "move"):
            order["completed"] = True
            player["ch3_tactical_tokens"] = (
                player.get("ch3_tactical_tokens", 0) + 2
            )
            player["ch3_confidence"] = min(
                100, player.get("ch3_confidence", 65) + 10
            )
            player["ch3_private_field_mode"] = False
            return True, (
                "*** FIELD DIRECTIVE ACCOMPLISHED! (+2 TACTICAL TOKENS) ***\n"
                "Your reconnaissance secures the high ground! As dusk "
                "settles, the armies form up for the Evening Clash..."
            )

    if player.get("ch3_private_steps_left", 0) <= 0:
        player["ch3_private_field_mode"] = False
        return True, (
            "*** DUSK FALLS ACROSS THE FRONT! ***\n"
            "Bugles sound across the valley as the Afternoon march ends. "
            "Your company forms up for the Evening Clash!"
        )

    return (
        False,
        f"[Field March: {player['ch3_private_steps_left']} steps before Dusk]",
    )


# =========================================================================
# FIX #5: ZERO-ARMY CAPTAIN / PRIVATE PETITIONS & SOLO COMMANDO MISSIONS
# =========================================================================
def execute_zero_army_action(player, action_key, world_map):
    """
    Executes recovery operations when a Captain or Private has 0 armies on
    the 3D board:
    - `petition_general`: Roll 2d6 + Standing/Confidence to request a
      3-battalion Relief Column from High Command (once per day).
    - `solo_sabotage`: Spend 8 MP to infiltrate an enemy garrison on foot,
      destroying half its battalions, stealing 20s, and earning +2 Bns.
    - `solo_duel`: Spend 10 MP to challenge an enemy garrison Captain to
      single combat—capturing the clearing, rallying +3 Bns, and winning
      an immediate Battlefield Promotion!
    - `solo_militia`: Spend 8 MP to rally a 3-battalion Partisan Militia
      at your faction capital using Charisma/Sympathy/Printing Press.
    """
    my_fac = player.get("ch3_faction", "Union")
    my_rank = player.get("ch3_rank", "Private")
    factions = player.setdefault("ch3_factions", {})
    fac_data = factions.setdefault(
        my_fac, {"sympathy": 10, "silver": 50, "capital": "11,4"}
    )
    cap_pos = fac_data.get("capital", "11,4")
    cap_name = _landmark_label(cap_pos, world_map)
    armies = player.setdefault("ch3_armies", {})
    territories = player.setdefault("territories", {})

    # 1. PETITION HIGH COMMAND FOR A RELIEF COLUMN
    if action_key == "petition_general":
        if player.get("ch3_petitioned_today"):
            return (
                "Your courier has already ridden to High Command today. "
                "Mount a Solo Commando Mission or await tomorrow's dawn!"
            )
        player["ch3_petitioned_today"] = True
        roll = random.randint(1, 6) + random.randint(1, 6)
        bonus = (player.get("ch3_standing", 10) // 4) + (
            player.get("ch3_confidence", 60) // 25
        )
        total = roll + bonus

        if total >= 9:
            armies[cap_pos] = {"faction": my_fac, "count": 3}
            territories[cap_pos] = my_fac
            recalculate_ch3_total_points(player)
            msg = (
                f"*** RELIEF COLUMN DISPATCHED! (Rolled {total} >= 9) ***\n"
                f"High Command heeds your dispatch and marches 3 fresh "
                f"{my_fac} Battalions to {cap_name} under your command!"
            )
        else:
            msg = (
                f"*** PETITION REFUSED (Rolled {total} < 9)! ***\n"
                "The General's courier returns empty-handed: \"High Command "
                "has no reserves to spare—take the field yourself and prove "
                "your mettle in a Solo Commando Operation!\""
            )
        player["ch3_daily_order"] = {"description": msg}
        return msg

    # Find an enemy garrison for Solo Sabotage / Solo Duel
    enemy_targets = [
        (pos, a)
        for pos, a in armies.items()
        if a.get("faction") != my_fac and a.get("count", 0) > 0
    ]
    target_pos, target_army = (
        enemy_targets[0]
        if enemy_targets
        else (cap_pos, {"faction": "Laydere", "count": 3})
    )
    target_name = _landmark_label(target_pos, world_map)
    enemy_fac = target_army.get("faction", "Laydere")

    # 2. SOLO COMMANDO MISSION 1: NIGHT SABOTAGE (8 MP)
    if action_key == "solo_sabotage":
        if player.get("movement_points", 0) < 8:
            return "Requires at least 8 March Points (MP) to infiltrate!"
        player["movement_points"] -= 8

        inv = player.get("inventory", [])
        stl_bonus = player.get("stealth", 0) + (
            3
            if (
                "greek fire" in inv
                or "guard uniform" in inv
                or player.get("disguised_as_guard")
            )
            else 0
        )
        roll = random.randint(1, 6) + random.randint(1, 6) + stl_bonus

        if roll >= 9:
            lost_bns = max(1, target_army.get("count", 2) // 2)
            target_army["count"] = max(1, target_army["count"] - lost_bns)
            player["silver"] = player.get("silver", 0) + 20
            armies[cap_pos] = {
                "faction": my_fac,
                "count": armies.get(cap_pos, {}).get("count", 0) + 2,
            }
            territories[cap_pos] = my_fac
            recalculate_ch3_total_points(player)
            msg = (
                f"*** SOLO NIGHT SABOTAGE SUCCEEDS! (Roll {roll}) ***\n"
                f"Slipping past {enemy_fac} sentries at {target_name}, you "
                f"torch their powder-wagons (-{lost_bns} Enemy Bns, +20s)! "
                f"Impressed, High Command assigns 2 Battalions at {cap_name}!"
            )
        else:
            player["health"] = max(1, player.get("health", 10) - 2)
            msg = (
                f"*** SABOTAGE SPOTTED! (Roll {roll} < 9) ***\n"
                f"Sentries at {target_name} loose a volley as you escape "
                "into the dark (-2 HP)!"
            )
        player["ch3_daily_order"] = {"description": msg}
        return msg

    # 3. SOLO COMMANDO MISSION 2: SINGLE COMBAT FOR THE STANDARD (10 MP)
    if action_key == "solo_duel":
        if player.get("movement_points", 0) < 10:
            return "Requires at least 10 March Points (MP) to challenge!"
        player["movement_points"] -= 10

        str_bonus = player.get("strength", 0) + (
            2 if player.get("equipped_weapon", "fists") != "fists" else 0
        )
        roll = random.randint(1, 6) + random.randint(1, 6) + str_bonus

        if roll >= 10:
            armies[target_pos] = {"faction": my_fac, "count": 3}
            territories[target_pos] = my_fac
            fac_data["agenda_pts"] = fac_data.get("agenda_pts", 0) + 5
            promo_str = ""
            if my_rank == "Private":
                player["ch3_rank"] = "Captain"
                promo_str = " Promoted to CAPTAIN on the spot!"
            elif my_rank == "Captain":
                player["ch3_rank"] = "General"
                promo_str = " Acclaimed SUPREME GENERAL by the troops!"
            recalculate_ch3_total_points(player)
            msg = (
                f"*** SINGLE COMBAT TRIUMPH AT {target_name.upper()}! ***\n"
                f"You best the {enemy_fac} commander in personal combat! "
                f"Their garrison routs, and 3 rallied {my_fac} Battalions "
                f"raise your standard over {target_name}!{promo_str}"
            )
        else:
            player["health"] = max(1, player.get("health", 10) - 3)
            msg = (
                f"*** DUEL REPELLED AT {target_name.upper()} (Roll {roll}) ***\n"
                f"The {enemy_fac} champion parries your lunge and wounds "
                "your shoulder (-3 HP) before you withdraw!"
            )
        player["ch3_daily_order"] = {"description": msg}
        return msg

    # 4. SOLO COMMANDO MISSION 3: RAISE PARTISAN MILITIA (8 MP)
    if action_key == "solo_militia":
        if player.get("movement_points", 0) < 8:
            return "Requires at least 8 March Points (MP) to rally partisans!"
        player["movement_points"] -= 8

        inv = player.get("inventory", [])
        cha_bonus = (
            player.get("charisma", 0)
            + (player.get("influence", 0) // 2)
            + (3 if "portable printing press" in inv else 0)
        )
        roll = random.randint(1, 6) + random.randint(1, 6) + cha_bonus

        if roll >= 8:
            armies[cap_pos] = {
                "faction": my_fac,
                "count": armies.get(cap_pos, {}).get("count", 0) + 3,
            }
            territories[cap_pos] = my_fac
            recalculate_ch3_total_points(player)
            msg = (
                f"*** PARTISAN MILITIA RALLIED AT {cap_name.upper()}! ***\n"
                "Ringing the parish bells and distributing broadsheets, you "
                f"muster 3 volunteer {my_fac} Battalions directly under your "
                "command!"
            )
        else:
            player["ch3_tactical_tokens"] = (
                player.get("ch3_tactical_tokens", 0) + 1
            )
            msg = (
                f"*** CAUTIOUS TOWNSFOLK (Roll {roll} < 8) ***\n"
                "Too few volunteers step forward to form a full battalion, "
                "but local scouts grant you +1 Tactical Advantage Token!"
            )
        player["ch3_daily_order"] = {"description": msg}
        return msg

    return "Order logged."


def execute_rank_political_action(
    player, action_key, target_faction=None, world_map=None
):
    """
    Executes rank-exclusive political actions OR Zero-Army Solo Commando
    operations when the player has 0 battalions on the board.
    """
    if action_key in (
        "petition_general",
        "solo_sabotage",
        "solo_duel",
        "solo_militia",
    ):
        return execute_zero_army_action(player, action_key, world_map)

    rank = player.get("ch3_rank", "Private")
    my_fac = player.get("ch3_faction", "Union")
    alliances = player.setdefault("ch3_alliances", {})
    factions = player.setdefault("ch3_factions", {})

    if rank == "General":
        if action_key == "public_alliance" and target_faction:
            alliances[target_faction] = "known"
            player["ch3_standing"] = player.get("ch3_standing", 10) + 2
            return (
                f"Known Treaty signed with {target_faction}! Shared "
                "corridors open (+2 Political Standing)."
            )
        if action_key == "secret_pact" and target_faction:
            alliances[target_faction] = "secret"
            return (
                f"Secret Non-Aggression Pact sealed with {target_faction}. "
                "Only you and their High Command know."
            )
        if action_key == "betray_alliance" and target_faction:
            alliances.pop(target_faction, None)
            player["ch3_standing"] = player.get("ch3_standing", 10) - 10
            factions.setdefault(my_fac, {})["agenda_pts"] = (
                factions.get(my_fac, {}).get("agenda_pts", 0) + 6
            )
            recalculate_ch3_total_points(player)
            return (
                f"*** TREACHERY! You ambush your ally {target_faction}! ***\n"
                "You seize a surprise tactical advantage (+6 Agenda Pts), "
                "but your Political Standing plummets (-10 Standing)!"
            )

    elif rank == "Captain":
        if action_key == "stage_coup":
            if (
                player.get("ch3_confidence", 65) <= 35
                or player.get("ch3_standing", 10) <= 0
            ):
                player["ch3_rank"] = "General"
                player["ch3_confidence"] = 60
                factions.setdefault(my_fac, {})["agenda_pts"] = (
                    factions.get(my_fac, {}).get("agenda_pts", 0) + 5
                )
                recalculate_ch3_total_points(player)
                return (
                    "*** MILITARY COUP SUCCEEDS! ***\n"
                    "Rallying your disillusioned garrison, you depose the "
                    f"failing General and assume Supreme Command of {my_fac}!"
                )
            return (
                "Your troops are not yet desperate enough to back a mutiny "
                "against High Command."
            )

        if action_key == "defect_faction" and target_faction:
            pos_key = f"{player['x']},{player['y']}"
            player.setdefault("territories", {})[pos_key] = target_faction
            if pos_key in player.get("ch3_armies", {}):
                player["ch3_armies"][pos_key]["faction"] = target_faction
            player["ch3_faction"] = target_faction
            player["ch3_confidence"] = 55
            factions.setdefault(target_faction, {})["agenda_pts"] = (
                factions.get(target_faction, {}).get("agenda_pts", 0) + 6
            )
            recalculate_ch3_total_points(player)
            return (
                "*** TURNCOAT DEFECTION! ***\n"
                "You lower the banner at your garrison and ride out under "
                f"the colours of {target_faction} (+6 Pts to "
                f"{target_faction})!"
            )

    elif rank == "Private":
        if action_key == "nefarious_promotion":
            player["ch3_rank"] = "Captain"
            player["ch3_confidence"] = 50
            return (
                "*** BATTLEFIELD VACANCY & NEFARIOUS PROMOTION! ***\n"
                "After your Captain falls in the chaos of the night "
                "skirmish, you step over the command ledger and assume "
                "Captaincy of the sector!"
            )

    return "Command order logged."


def calculate_ch3_movement_cost(
    player, army_faction, target_pos, world_map, troop_count=1
):
    """
    Calculates Movement Point (MP) cost on the 10-MP scale:
      Total MP Cost = Base Terrain Cost + Battalions Marched (troop_count)
    """
    if isinstance(target_pos, str) and "," in target_pos:
        parts = target_pos.split(",")
        coord = (int(parts[0]), int(parts[1]))
    else:
        coord = target_pos

    dest_room = world_map.get(coord)
    if not dest_room:
        return 999, False, "Impassable terrain."

    reg = dest_room.region
    sat = player.get("ground_saturation", 35)
    snow = player.get("snowpack_level", 0)

    base_cost = 10 if reg in ("Lignum Forest", "The Caligo Mountains") else 5

    fac_spec = DTESSERA_FACTIONS.get(army_faction, {})
    advantages = fac_spec.get("advantages", ())
    if "Fog of War" in advantages and reg == "Lignum Forest":
        base_cost = 5
    if "Military Expertise" in advantages and reg == "The New Road":
        base_cost = 3

    alt, _, local_temp = weather_engine.get_tile_altitude_and_temp(
        player, coord, world_map
    )
    room_title = (
        dest_room.name if dest_room.name != "x" else f"the {reg} approach"
    )
    warning = ""

    if sat >= 75 and alt == 1:
        return (
            999,
            False,
            f"The low basin at {room_title} is submerged under floodwaters!",
        )
    if sat >= 90 and alt == 2 and reg not in ("Fluvius Town", "Parvus Town"):
        return (
            999,
            False,
            f"The floodplain at {room_title} is inundated! Seek high ground.",
        )

    if (sat >= 55 and alt == 1) or (sat >= 70 and alt == 2):
        base_cost += 5
        warning = f"Waterlogged mire slows the column into {room_title} (+5 MP)."

    if (alt >= 4 and local_temp <= 0) or (snow >= 50 and alt >= 3):
        base_cost += 5
        warning = "Blizzards and black ice on the crags slow the column (+5 MP)."

    headcount_burden = max(1, int(troop_count))
    total_cost = base_cost + headcount_burden
    return total_cost, True, warning


def pin_ch3_clash(
    player, tile_pos, attacker_info, defender_info, origin_pos=None
):
    """
    Pins a Crossed-Swords ('⚔') engagement at `tile_pos` during the
    Afternoon 'March' phase so multiple battles can be queued and resolved
    sequentially during the Evening 'Engage' phase.
    """
    clashes = player.setdefault("ch3_pending_clashes", [])
    att_fac = attacker_info.get("faction", "Union")
    att_cnt = max(1, int(attacker_info.get("count", 1)))

    for item in clashes:
        if item.get("tile_pos") == tile_pos:
            if item["attacker"].get("faction") == att_fac:
                item["attacker"]["count"] += att_cnt
                return item
            item["attacker"] = {"faction": att_fac, "count": att_cnt}
            return item

    entry = {
        "tile_pos": tile_pos,
        "attacker": {"faction": att_fac, "count": att_cnt},
        "defender": {
            "faction": defender_info.get("faction", "Laydere"),
            "count": max(1, int(defender_info.get("count", 1))),
        },
        "origin_pos": origin_pos,
    }
    clashes.append(entry)
    return entry


def find_retreat_tile(
    player, losing_faction, contested_pos, world_map, origin_pos=None
):
    """
    Finds an adjacent friendly or unoccupied passable clearing for a
    routed army remnant to retreat into. Falls back to the faction's
    capital if cut off.
    """
    armies = player.get("ch3_armies", {})
    territories = player.get("territories", {})

    if (
        origin_pos
        and origin_pos not in armies
        and territories.get(origin_pos) in (losing_faction, None)
    ):
        return origin_pos

    if isinstance(contested_pos, str) and "," in contested_pos:
        cx, cy = map(int, contested_pos.split(","))
        candidates = []
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = cx + dx, cy + dy
            n_key = f"{nx},{ny}"
            if (nx, ny) not in world_map:
                continue
            _, can_pass, _ = calculate_ch3_movement_cost(
                player, losing_faction, n_key, world_map, troop_count=1
            )
            if not can_pass:
                continue
            if n_key in armies and armies[n_key]["faction"] != losing_faction:
                continue
            score = 2 if territories.get(n_key) == losing_faction else 1
            candidates.append((score, n_key))

        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

    return (
        player.get("ch3_factions", {})
        .get(losing_faction, {})
        .get("capital", "10,14")
    )


def apply_ai_agenda_balance_step(fac_data, captured_stronghold=False):
    """Awards AI factions Agenda Points and Sympathy during expansion."""
    pts = 10 if captured_stronghold else random.choice((3, 4, 5))
    fac_data["agenda_pts"] = fac_data.get("agenda_pts", 0) + pts
    fac_data["sympathy"] = fac_data.get("sympathy", 10) + 1


# =========================================================================
# FIX #4: TRUE SYMMETRIC AI FACTION TURN ENGINE (DICE + SUPPLY + 10-MP)
# =========================================================================
def process_enemy_faction_turns(player, world_map):
    """
    Executes Chapter 3 turns for the 6 rival AI factions using the EXACT
    same rules and faction advantages as the human player:
    1. Rolls a Dawn Command Dice pool (3d6 to 7d6 based on ruled lands &
       Sympathy).
    2. Slots a 5 or 6 into Supply Lines (suffering a supply shortfall if
       none rolled).
    3. Slots dice into Muster Troops (or Barricade Pairs for Union).
    4. Converts unslotted dice into 10 MP per die and pays `Base Terrain +
       1 MP per Battalion` using Faction Terrain Advantages!
    """
    prune_empty_armies(player)
    factions = player.get("ch3_factions", {})
    territories = player.get("territories", {})
    barricades = player.setdefault("ch3_barricades", {})
    armies = player.get("ch3_armies", {})
    player_fac = player.get("ch3_faction", "Union")
    alliances = player.get("ch3_alliances", {})
    log = ["=== ENEMY COMMANDERS ON THE MARCH ==="]
    visual_queue = []
    now = pygame.time.get_ticks()

    for fac_name, fac_data in factions.items():
        if fac_name == player_fac or pass_and_play.is_faction_human(fac_name):
            continue

        spec = DTESSERA_FACTIONS.get(fac_name, DTESSERA_FACTIONS["Union"])
        fac_title = spec["title"]
        advantages = spec.get("advantages", ())
        capital = fac_data.get("capital", "10,14")
        cap_name = _landmark_label(capital, world_map)

        # 1. Roll Symmetric Dawn Command Dice Pool (3d6 to 7d6)
        ruled_tiles = [
            pos for pos, owner in territories.items() if owner == fac_name
        ]
        dice_cnt = max(
            3,
            min(
                7,
                3
                + (len(ruled_tiles) // 2)
                + (fac_data.get("sympathy", 10) // 12),
            ),
        )
        rolls = sorted(
            [random.randint(1, 6) for _ in range(dice_cnt)], reverse=True
        )
        remaining_dice = list(rolls)
        alloc_notes = []

        # 2. Supply Line Requirement (Needs a 5 or 6)
        supplied = False
        if remaining_dice and remaining_dice[0] >= 5:
            sup_die = remaining_dice.pop(0)
            supplied = True
            alloc_notes.append(f"Supply [{sup_die}]")
        else:
            alloc_notes.append("No 5/6 for Supply (-1 Sympathy)")
            fac_data["sympathy"] = max(0, fac_data.get("sympathy", 10) - 1)

        # 3. Faction-Specific Dawn Advantages (Union Barricades / Kokeshi Silver)
        if "Barricades" in advantages and len(remaining_dice) >= 2:
            pair_val = next(
                (v for v in set(remaining_dice) if remaining_dice.count(v) >= 2),
                None,
            )
            if pair_val is not None and len(remaining_dice) >= 3:
                remaining_dice.remove(pair_val)
                remaining_dice.remove(pair_val)
                barricades[capital] = True
                alloc_notes.append(
                    f"Barricade Pair [{pair_val},{pair_val}]"
                )

        if "Bribery" in advantages:
            fac_data["silver"] = (
                fac_data.get("silver", 50) + len(ruled_tiles) * 5
            )

        # 4. Muster Troops Socket (Only if a die is slotted & supplied!)
        muster_yield = 0
        fac_troops = sum(
            a.get("count", 0)
            for a in armies.values()
            if a.get("faction") == fac_name
        )
        if remaining_dice and (
            fac_troops < 10 or len(remaining_dice) >= 3
        ):
            m_die = remaining_dice.pop(0)
            if supplied:
                muster_yield = max(
                    1, (m_die // 2) + min(3, len(ruled_tiles) // 2)
                )
            else:
                muster_yield = 1
            if capital in armies and armies[capital]["faction"] == fac_name:
                armies[capital]["count"] += muster_yield
            elif capital not in armies:
                armies[capital] = {
                    "faction": fac_name,
                    "count": muster_yield,
                }
                territories[capital] = fac_name
            alloc_notes.append(f"Muster [{m_die}] (+{muster_yield} Bns)")
        else:
            alloc_notes.append("Saved Dice for March")

        # 5. Convert Unslotted Dice into Afternoon March Points (10 MP / Die)
        ai_mp = max(10, len(remaining_dice) * 10)
        muster_summary = (
            f"Rolled {rolls} -> {', '.join(alloc_notes)} | "
            f"March Pool: {ai_mp} MP."
        )

        # 6. Afternoon March (Must pay exact Base Terrain + 1 MP/Bn cost!)
        fac_garrisons = [
            pos
            for pos, a in armies.items()
            if a.get("faction") == fac_name and a.get("count", 0) >= 2
        ]
        moved_this_turn = False

        for g_pos in fac_garrisons:
            army = armies.get(g_pos)
            if not army or army["count"] < 2:
                continue

            gx, gy = map(int, g_pos.split(","))
            march_count = max(1, (army["count"] * 2) // 3)
            candidates = []

            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = gx + dx, gy + dy
                target_key = f"{nx},{ny}"
                if (nx, ny) not in world_map:
                    continue

                cost, can_pass, _ = calculate_ch3_movement_cost(
                    player,
                    fac_name,
                    target_key,
                    world_map,
                    troop_count=march_count,
                )
                if not can_pass or cost > ai_mp:
                    continue

                # Respect Known Treaty with player unless betraying
                if (
                    target_key in armies
                    and armies[target_key]["faction"] == player_fac
                    and alliances.get(fac_name) == "known"
                ):
                    continue

                # Score candidate tiles using Faction Terrain & Agenda logic
                loc = world_map[(nx, ny)]
                score = 10
                if territories.get(target_key) != fac_name:
                    score += 15
                if target_key in MAJOR_STRONGHOLD_TILES:
                    score += 20
                if (
                    "Military Expertise" in advantages
                    and loc.region == "The New Road"
                ):
                    score += 12
                if (
                    "Fog of War" in advantages
                    and loc.region == "Lignum Forest"
                ):
                    score += 12
                if (
                    target_key in armies
                    and armies[target_key]["faction"] != fac_name
                ):
                    def_cnt = armies[target_key].get("count", 1)
                    if march_count >= def_cnt:
                        score += 18
                    else:
                        score -= 20

                candidates.append((score, target_key, cost))

            if not candidates:
                continue

            candidates.sort(reverse=True)
            _, target, move_cost = candidates[0]
            if candidates[0][0] < 8:
                continue

            ai_mp -= move_cost
            from_name = _landmark_label(g_pos, world_map)
            t_name = _landmark_label(target, world_map)

            if march_count < army["count"]:
                army["count"] -= march_count
            else:
                armies.pop(g_pos, None)

            # Case 1: AI marches into a clearing held by the PLAYER!
            if target in armies and armies[target]["faction"] == player_fac:
                pin_ch3_clash(
                    player,
                    target,
                    {"faction": fac_name, "count": march_count},
                    armies[target],
                    origin_pos=g_pos,
                )
                msg_line = (
                    f"• {fac_title} ({muster_summary}) marches "
                    f"{march_count} Bns (-{move_cost} MP) from {from_name} "
                    f"to attack your garrison at {t_name}!"
                )
                log.append(msg_line)
                visual_queue.append({
                    "faction": fac_name,
                    "banner_title": f"{fac_title.upper()}'S TURN",
                    "muster_text": muster_summary,
                    "action_text": (
                        f"Spends {move_cost} MP to march {march_count} Bns "
                        f"from {from_name} into {t_name} — PINNING AN "
                        "EVENING CLASH!"
                    ),
                    "event_type": "clash_player",
                    "capital": capital,
                    "muster_gain": muster_yield,
                    "from_pos": g_pos,
                    "to_pos": target,
                    "count": march_count,
                    "anim_start": now,
                })
                moved_this_turn = True
                break

            # Case 2: AI vs AI Skirmish (Uses symmetric dice + faction edges!)
            if target in armies and armies[target]["faction"] != fac_name:
                rival_fac = armies[target]["faction"]
                rival_cnt = max(1, armies[target]["count"])

                # Kokeshi AI Bribery Advantage
                if (
                    "Bribery" in advantages
                    and fac_data.get("silver", 0) >= 25
                    and rival_cnt > 1
                ):
                    fac_data["silver"] -= 25
                    rival_cnt -= 1
                    march_count += 1

                att_str = sum(
                    random.randint(1, 6) for _ in range(min(6, march_count))
                )
                def_str = sum(
                    random.randint(1, 6) for _ in range(min(6, rival_cnt))
                )
                if "Superior Weapons (Close Quarters)" in advantages:
                    att_str += 2
                if "Superior Weapons (Long Range)" in advantages:
                    att_str += 2

                if att_str > def_str:
                    loss = max(
                        0,
                        int(march_count * (def_str / float(att_str)) * 0.5),
                    )
                    survivors = max(1, march_count - loss)
                    armies[target] = {
                        "faction": fac_name,
                        "count": survivors,
                    }
                    territories[target] = fac_name
                    apply_ai_agenda_balance_step(
                        fac_data,
                        captured_stronghold=(
                            target in MAJOR_STRONGHOLD_TILES
                        ),
                    )
                    outcome_str = (
                        f"defeating {rival_fac} ({att_str} vs {def_str}) "
                        f"and seizing {t_name} ({survivors} Bns survive)!"
                    )
                else:
                    loss = max(
                        0,
                        int(rival_cnt * (att_str / float(def_str)) * 0.5),
                    )
                    armies[target]["count"] = max(1, rival_cnt - loss)
                    outcome_str = (
                        f"clashing with {rival_fac} at {t_name} ({att_str} "
                        f"vs {def_str}), but is repelled!"
                    )

                log.append(
                    f"• {fac_name} ({march_count} Bns, -{move_cost} MP) "
                    f"marches on {t_name}, {outcome_str}"
                )
                visual_queue.append({
                    "faction": fac_name,
                    "banner_title": f"{fac_title.upper()}'S TURN",
                    "muster_text": muster_summary,
                    "action_text": (
                        f"Spends {move_cost} MP to march {march_count} Bns "
                        f"from {from_name} to {t_name}, {outcome_str}"
                    ),
                    "event_type": "march",
                    "capital": capital,
                    "muster_gain": muster_yield,
                    "from_pos": g_pos,
                    "to_pos": target,
                    "count": march_count,
                    "anim_start": now,
                })
                moved_this_turn = True
                break

            # Case 3: AI expands into an open clearing
            log.append(
                f"• {fac_name} spends {move_cost} MP to march {march_count} "
                f"Bns into {t_name}."
            )
            if target in armies and armies[target]["faction"] == fac_name:
                armies[target]["count"] += march_count
            else:
                armies[target] = {
                    "faction": fac_name,
                    "count": march_count,
                }
                territories[target] = fac_name
                if random.random() < 0.35:
                    apply_ai_agenda_balance_step(fac_data)

            visual_queue.append({
                "faction": fac_name,
                "banner_title": f"{fac_title.upper()}'S TURN",
                "muster_text": muster_summary,
                "action_text": (
                    f"Spends {move_cost} MP to advance {march_count} Bns "
                    f"from {from_name} and claim {t_name}."
                ),
                "event_type": "march",
                "capital": capital,
                "muster_gain": muster_yield,
                "from_pos": g_pos,
                "to_pos": target,
                "count": march_count,
                "anim_start": now,
            })
            moved_this_turn = True
            break

        if not moved_this_turn:
            visual_queue.append({
                "faction": fac_name,
                "banner_title": f"{fac_title.upper()}'S TURN",
                "muster_text": muster_summary,
                "action_text": (
                    f"Holds its fortified lines around {cap_name}."
                ),
                "event_type": "muster",
                "capital": capital,
                "muster_gain": muster_yield,
                "from_pos": capital,
                "to_pos": capital,
                "count": max(1, muster_yield),
                "anim_start": now,
            })

    prune_empty_armies(player)
    player["ch3_armies"] = armies
    player["territories"] = territories
    player["ch3_ai_log"] = log
    player["ch3_ai_turn_queue"] = visual_queue
    recalculate_ch3_total_points(player)
    return player


def get_available_ch2_war_tools(player):
    """Returns unlocked Chapter 2 specialist war-table actions."""
    inv = player.get("inventory", [])
    skills = player.get("skills", [])
    companions = player.get("companions", [])
    used_today = player.get("ch3_tools_used_today", [])
    tools = []

    has_press = "portable printing press" in inv or (
        "lead type-case" in inv and "bottle of ink" in inv
    )
    if has_press and "press" not in used_today:
        tools.append((
            "ch2_tool_press",
            "Print Wartime Broadsheets (+4 Sympathy)",
            (168, 50, 35),
        ))

    has_cipher = (
        "codewheel" in inv
        or "deck of cards" in inv
        or "intelligence officer" in skills
    )
    if has_cipher and "cipher" not in used_today:
        tools.append((
            "ch2_tool_cipher",
            "Decode Enemy Dispatches (Preview AI Targets)",
            (45, 88, 165),
        ))

    has_ordnance = (
        "master blacksmith" in skills
        or "forge" in skills
        or "greek fire" in inv
        or bool(companions)
    )
    if has_ordnance and "ordnance" not in used_today:
        tools.append((
            "ch2_tool_ordnance",
            "Issue Specialist Ordnance (+1 Command Die [6])",
            (55, 115, 72),
        ))

    return tools


def preview_enemy_ai_targets(player, world_map):
    """Uses the Chapter 2 Codewheel or Deck Cipher to reveal AI targets."""
    armies = player.get("ch3_armies", {})
    my_fac = player.get("ch3_faction", "Union")
    intercepts = []

    for pos_key, army in armies.items():
        fac_name = army.get("faction", "Unknown")
        if fac_name == my_fac or army.get("count", 0) <= 2:
            continue

        gx, gy = map(int, pos_key.split(","))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            loc = world_map.get((gx + dx, gy + dy))
            if loc:
                dest_title = (
                    loc.name if loc.name != "x" else f"the {loc.region} front"
                )
                intercepts.append(
                    f"• {fac_name} column preparing to march on {dest_title}."
                )
                break

    if not intercepts:
        return "Cipher Intercept: Enemy garrisons are holding position today."
    return (
        "=== CRYPTOGRAPHIC INTERCEPT (ENEMY ORDERS DECODED) ===\n"
        + "\n".join(intercepts[:4])
    )


def execute_ch2_war_tool(player, tool_key, world_map):
    """Executes a Chapter 2 specialist tool action during Morning Phase."""
    used = player.setdefault("ch3_tools_used_today", [])
    my_fac = player.get("ch3_faction", "Union")
    factions = player.setdefault("ch3_factions", {})
    fac_data = factions.setdefault(
        my_fac, {"sympathy": 10, "silver": 50, "capital": "11,4"}
    )

    if tool_key == "ch2_tool_press" and "press" not in used:
        used.append("press")
        fac_data["sympathy"] = fac_data.get("sympathy", 10) + 4
        player["ch3_confidence"] = min(
            100, player.get("ch3_confidence", 65) + 5
        )
        recalculate_ch3_total_points(player)
        return (
            "*** WARTIME BROADSHEETS DISTRIBUTED! ***\n"
            "Your flatbed press rolls off hundreds of strike-sheets and "
            f"manifestos (+4 {my_fac} Sympathy, +5% Unit Confidence)!"
        )

    if tool_key == "ch2_tool_cipher" and "cipher" not in used:
        used.append("cipher")
        player["ch3_tactical_tokens"] = (
            player.get("ch3_tactical_tokens", 0) + 1
        )
        report = preview_enemy_ai_targets(player, world_map)
        return (
            f"{report}\n"
            "*** (+1 Tactical Advantage Token for Evening Combat!) ***"
        )

    if tool_key == "ch2_tool_ordnance" and "ordnance" not in used:
        used.append("ordnance")
        dice = player.setdefault("ch3_morning_dice", [])
        dice.append({
            "id": len(dice),
            "value": 6,
            "rect": None,
            "slotted_in": None,
            "is_dragging": False,
        })
        return (
            "*** SPECIALIST ORDNANCE ISSUED! ***\n"
            "Your forged steel and veteran companions bolster the line, "
            "adding a bonus '6' Command Die to your Morning Tray!"
        )

    return "That specialist operation has already been deployed today."


def get_grimwald_options(player):
    """Returns dialogue options when speaking with Sergeant Grimwald."""
    return [
        "Ask how this war will be won (Victory Modes)",
        "Ask about the daily routine (Morning, Afternoon & Dusk)",
        "Ask what to do if a Captain or Private loses their army",
        "Ask about our faction's battlefield advantages",
        "Leave",
    ]


def resolve_grimwald(choice, player):
    """Resolves dialogue choices with Field Sergeant Grimwald."""
    return resolve_quartermaster_war_advice(choice, player)


def resolve_quartermaster_war_advice(choice, player, world_map=None):
    """Delivers diegetic Chapter 3 campaign guidance from Sergeant Grimwald."""
    my_fac = player.get("ch3_faction", "Union")
    my_rank = player.get("ch3_rank", "Private")

    if choice == "Leave":
        return (
            player,
            "Sergeant Grimwald straps his campaign ledger shut and checks "
            "the priming on his pistol.",
            "MAIN",
        )

    if choice.startswith("Ask how this war will be won"):
        return (
            player,
            "Sergeant Grimwald taps a brass calliper against his field map.\n"
            "\"Whether we fight a Standard War to 100 Hegemony Points, a "
            "Grand Campaign to 250 Points across the changing seasons, or a "
            "Total Domination war for all seven Great Strongholds, every "
            "clearing and every ounce of public sympathy counts!\"",
            "NPC_DIALOGUE",
        )

    if choice.startswith("Ask about the daily"):
        return (
            player,
            "\"Three bells govern every day of the campaign,\" Grimwald "
            "growls.\n"
            "\"At Dawn, we cast the command bones—assigning men to the "
            "muster-rolls, the ration wagons, or the breastworks. Whatever "
            "dice you leave unspent in the tray become 10 March Points "
            "apiece for the Afternoon march.\n\n"
            "\"Split detachments to move light and fast, pin the enemy "
            "with Crossed Swords across multiple fronts, and at Dusk, "
            "steel meets steel in every contested clearing!\"",
            "NPC_DIALOGUE",
        )

    if choice.startswith("Ask what to do if a Captain"):
        return (
            player,
            f"Grimwald eyes your {my_rank} insignia and leans in close.\n"
            "\"If your battalions are wiped out in a hard fight, High "
            "Command won't just hand you free regiments out of thin air! "
            "You have two choices: send a dawn rider to **Petition the "
            "General** for a relief column, or take your own blade into "
            "the field on a **Solo Commando Operation**—torch an enemy "
            "baggage train, challenge a rival Captain to single combat for "
            "their standard, or ring the parish bells to raise a Partisan "
            "Militia yourself!\"",
            "NPC_DIALOGUE",
        )

    if choice == "Ask about our faction's battlefield advantages":
        spec = DTESSERA_FACTIONS.get(my_fac, DTESSERA_FACTIONS["Union"])
        adv_1, adv_2 = spec["advantages"]
        sym = spec["sympathy_type"]
        return (
            player,
            f"\"We fight under the banner of {spec['title']},\" Grimwald "
            f"says proudly. \"Our strength flows from {sym}. In the field, "
            f"remember our two edges: **{adv_1}** and **{adv_2}**!\"",
            "NPC_DIALOGUE",
        )

    return player, "Sergeant Grimwald nods toward the frontline.", "MAIN"


def check_ch3_endgame_trigger(player):
    """
    Checks whether any faction has met the active Victory Mode condition:
    - '100_PTS': 100 Hegemony Points
    - '250_PTS': 250 Hegemony Points
    - 'DOMINATION': Rules all 7 Major Strongholds
    """
    recalculate_ch3_total_points(player)
    factions = player.get("ch3_factions", {})
    mode = player.get("ch3_victory_mode", "100_PTS")
    goal = get_victory_goal(player)

    for f_key, f_data in factions.items():
        if mode == "DOMINATION":
            if count_faction_strongholds(player, f_key) >= 7:
                player["ch3_winner"] = f_key
                player["ch3_epilogue_lines"] = build_ch3_epilogue_text(
                    player, f_key
                )
                return True, f_key
        else:
            if f_data.get("total_points", 0) >= goal:
                player["ch3_winner"] = f_key
                player["ch3_epilogue_lines"] = build_ch3_epilogue_text(
                    player, f_key
                )
                return True, f_key

    return False, None


def build_ch3_epilogue_text(player, winning_faction):
    """Builds the personalised Epilogue Chronicle lines."""
    my_fac = player.get("ch3_faction", "Union")
    my_rank = player.get("ch3_rank", "Private")
    bits = player.get("ch3_world_bits", {})
    mode = player.get("ch3_victory_mode", "100_PTS")
    mode_tag = VICTORY_MODE_SPECS.get(
        mode, VICTORY_MODE_SPECS["100_PTS"]
    )["label"]

    title, body = EPILOGUE_CHRONICLES.get(
        winning_faction, EPILOGUE_CHRONICLES["Union"]
    )
    player_won = winning_faction == my_fac
    outcome_banner = (
        f"SUPREME VICTORY FOR {winning_faction.upper()} ({mode_tag})"
        if player_won
        else f"DEFEAT — {winning_faction.upper()} CLAIMS HEGEMONY ({mode_tag})"
    )

    if player_won:
        if my_rank == "General":
            destiny = (
                "As Supreme General, your strategic alliances and battlefield "
                "command are etched into the founding charter of the new era."
            )
        elif my_rank == "Captain":
            destiny = (
                "As Sector Captain, your frontline leadership held the "
                "decisive corridors that made victory possible."
            )
        else:
            destiny = (
                "As a Frontline Private, your boots-on-the-ground grit across "
                "mud, flood, and barricade tipped the scales of history."
            )
    else:
        destiny = (
            f"Though you fought under the banner of {my_fac} as a {my_rank}, "
            f"the tide of {winning_faction} hegemony swept across the island."
        )

    labour_str = (
        "a united labour front" if bits.get("track_1") else "fractured fields"
    )
    port_str = (
        "a free Parvus port" if bits.get("track_4") else "contested quays"
    )
    legacy_echo = (
        f"The seeds planted in Murum and the Fluvius farmlands—{labour_str}, "
        f"{port_str}, and the choices forged before the first bugle sounded—"
        "shaped the final fate of Dtessera Terra."
    )

    return [
        outcome_banner,
        title,
        "",
        body,
        "",
        destiny,
        "",
        legacy_echo,
    ]


def calculate_campaign_difficulty(player):
    """
    Calculates a 1-100 difficulty weight for the Victory Grid.
    """
    rank = player.get("ch3_start_rank", player.get("ch3_rank", "Private"))
    fac = player.get("ch3_faction", "Union")
    fac_data = player.get("ch3_factions", {}).get(fac, {})
    legacy = fac_data.get("legacy_pts", 15)
    mode = player.get("ch3_victory_mode", "100_PTS")

    rank_weight = {"General": 10, "Captain": 40, "Private": 70}.get(rank, 40)
    legacy_weight = max(0, 35 - legacy)
    fac_weight = {"Vanguardists": 5, "FAI": 5, "Kokeshi": 5}.get(fac, 0)
    mode_weight = {"100_PTS": 0, "250_PTS": 10, "DOMINATION": 18}.get(mode, 0)

    return min(100, rank_weight + legacy_weight + fac_weight + mode_weight)
