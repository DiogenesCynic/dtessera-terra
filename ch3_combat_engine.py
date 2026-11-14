"""
ch3_combat_engine.py
--------------------
Manages Chapter 3 Evening Phase tactical clashes, 3-stage stronghold
sieges, proportionate mutual attrition & rout retreats, multi-battle
queue progression, Head-to-Head Pass-and-Play Attacker vs. Defender
controls, per-side 3D dice palettes, and procedural Pygame animations.
"""

import math
import random
import pygame

import ch3_board_renderer
import ch3_war_engine
from map_data import world_map as DEFAULT_WORLD_MAP
import pass_and_play
from ui_components import draw_fitted_text

# --- SHARED BATTLE DIORAMA PALETTE ---
TATE_RED = (168, 50, 35)
DIAL_CREAM = (244, 239, 225)
CLOCK_BLACK = (28, 26, 24)
GOLD_ACCENT = (195, 148, 48)
GOLD_BRIGHT = (250, 215, 85)
OAK_DARK = (46, 33, 25)
OAK_MID = (66, 48, 36)
FELT_ATTLE = (58, 32, 30)
FELT_DEF = (28, 46, 64)
EQUIPPED_GREEN = (45, 125, 68)

MAJOR_STRONGHOLDS = {
    "11,4": {
        "name": "Fluvius Town Guildhall",
        "owner": "Union",
        "fort_bonus": 2,
    },
    "10,14": {
        "name": "Murum Town Citadel",
        "owner": "Kokeshi",
        "fort_bonus": 3,
    },
    "15,10": {
        "name": "Castle Laydere Keep",
        "owner": "Laydere",
        "fort_bonus": 3,
    },
    "5,15": {
        "name": "Castle Ragmore Keep",
        "owner": "Ragmore",
        "fort_bonus": 3,
    },
    "14,2": {
        "name": "Parvus Port Bastion",
        "owner": "FAI",
        "fort_bonus": 2,
    },
    "5,5": {
        "name": "The Deep Glade Sanctuary",
        "owner": "Communards",
        "fort_bonus": 2,
    },
    "6,8": {
        "name": "The Old Path Waystation",
        "owner": "Vanguardists",
        "fort_bonus": 2,
    },
}

SIEGE_STAGE_NAMES = (
    "Stage I: The Outer Works",
    "Stage II: The Gatehouse Breach",
    "Stage III: The Inner Sanctum",
)

FACTION_COMBAT_BUTTONS = {
    "Union": [
        (
            "union_barricade",
            "Barricade Lock",
            (185, 48, 38),
            "Requires a matched pair in your dice pool: locks the line, "
            "upgrades lowest die to 6, and halves casualty attrition!",
        ),
        (
            "union_numbers",
            "Swarm Numbers",
            (155, 58, 35),
            "Requires at least as many dice as your opponent: militia "
            "reserves add +1 bonus die (3-6)!",
        ),
    ],
    "Kokeshi": [
        (
            "kokeshi_sabotage",
            "Sabotage (-10s)",
            (112, 48, 142),
            "Spend 10 Silver (or use Ch.2 Siege Gear) to shatter and "
            "discard the opponent's highest die!",
        ),
        (
            "kokeshi_bribe",
            "Bribe Unit (-15s)",
            (92, 38, 122),
            "Spend 15 Silver to buy off an opposing battalion—stealing "
            "their highest die onto your side!",
        ),
    ],
    "Laydere": [
        (
            "laydere_polearms",
            "Polearm Steel",
            (45, 88, 165),
            "Close-Quarters Superior Weapons: re-roll all 1s and 2s in "
            "your dice pool into 4-6 strikes!",
        ),
        (
            "laydere_discipline",
            "Shield-Wall (+2)",
            (35, 68, 135),
            "Military Expertise: adds +2 to lowest die, reduces "
            "casualties, and automatically wins all tiebreakers!",
        ),
    ],
    "Ragmore": [
        (
            "ragmore_snipe",
            "Longbow Volley",
            (152, 38, 58),
            "Long-Range Superior Weapons: spend a '6' from your pool to "
            "snipe and remove the opponent's highest die!",
        ),
        (
            "ragmore_artillery",
            "Range Sighting",
            (125, 32, 48),
            "Military Expertise: re-rolls your lowest die into a heavy "
            "high-ground strike (4-6)!",
        ),
    ],
    "FAI": [
        (
            "guerrilla_ambush",
            "Guerrilla Strike",
            (52, 52, 58),
            "Adds +1 ambush die (4-6) and guarantees minimal losses "
            "with a safe withdrawal if repelled!",
        ),
        (
            "kokeshi_sabotage",
            "Underhand Sap",
            (95, 42, 42),
            "Spend 10 Silver (or Ch.2 Siege Gear) to blow up the "
            "opponent's highest die!",
        ),
    ],
    "Communards": [
        (
            "communard_praxis",
            "Peaceful Praxis",
            (42, 132, 74),
            "Spend 4 Sympathy to persuade an opposing battalion—converting "
            "their die across the table to your side!",
        ),
        (
            "forest_fog",
            "Canopy Mist",
            (32, 102, 58),
            "Fog of War: woodland mist conceals your lines, nullifying "
            "any opposing die of 5 or 6!",
        ),
    ],
    "Vanguardists": [
        (
            "guerrilla_ambush",
            "Pack Ambush",
            (28, 85, 48),
            "Adds +1 ambush die (4-6) and secures a low-casualty "
            "woodland retreat if the line breaks!",
        ),
        (
            "forest_fog",
            "Canopy Mist",
            (22, 68, 38),
            "Fog of War: thick bough-shadows swallow and nullify the "
            "opponent's highest die (5 or 6)!",
        ),
    ],
}

DICE_PALETTES = {
    "bone dice": {
        "base": (230, 225, 215),
        "shadow": (180, 175, 160),
        "pip": (40, 35, 30),
    },
    "brass wallmaker dice": {
        "base": (205, 165, 60),
        "shadow": (145, 110, 30),
        "pip": (30, 25, 20),
    },
    "brass dice": {
        "base": (205, 165, 60),
        "shadow": (145, 110, 30),
        "pip": (30, 25, 20),
    },
    "jade kokeshi dice": {
        "base": (85, 160, 110),
        "shadow": (45, 100, 65),
        "pip": (240, 250, 240),
    },
    "jade dice": {
        "base": (85, 160, 110),
        "shadow": (45, 100, 65),
        "pip": (240, 250, 240),
    },
    "obsidian vanguard dice": {
        "base": (45, 40, 50),
        "shadow": (20, 18, 25),
        "pip": (200, 100, 220),
    },
    "obsidian dice": {
        "base": (45, 40, 50),
        "shadow": (20, 18, 25),
        "pip": (200, 100, 220),
    },
    "star-iron guild dice": {
        "base": (60, 70, 90),
        "shadow": (30, 35, 50),
        "pip": (230, 240, 255),
    },
    "star-iron dice": {
        "base": (60, 70, 90),
        "shadow": (30, 35, 50),
        "pip": (230, 240, 255),
    },
}


# =========================================================================
# 1. PASS-AND-PLAY SEAT LOOKUP & DYNAMIC BUTTON SPECS
# =========================================================================
def _get_faction_seat_dict(player, faction_key):
    """
    Returns the Pass-and-Play seat dictionary for `faction_key` if a
    human controls it, or falls back to `player`.
    """
    if pass_and_play.is_pnp_enabled(player):
        h_map = pass_and_play.get_human_factions_map()
        if faction_key in h_map:
            seats = pass_and_play.get_session().get("seats", [])
            s_idx = h_map[faction_key]
            if 0 <= s_idx < len(seats):
                return seats[s_idx]
    return player


def _is_head_to_head_human_clash(player):
    """Returns True if BOTH Attacker and Defender are Human Pass-and-Play seats."""
    if not pass_and_play.is_pnp_enabled(player):
        return False
    att_fac = player.get("ch3_attacker", {}).get("faction", "Union")
    def_fac = player.get("ch3_defender", {}).get("faction", "Laydere")
    return pass_and_play.is_faction_human(
        att_fac
    ) and pass_and_play.is_faction_human(def_fac)


def get_evening_combat_buttons(player):
    """Returns (action_key, short_label, rgb_color) for the action slots."""
    specs = get_evening_combat_button_specs(player)
    return [(k, lbl, col) for k, lbl, col, _ in specs]


def get_evening_combat_button_specs(player):
    """
    Returns (action_key, short_label, rgb_color, tooltip_desc) for the
    Battle Diorama buttons:
    - In Single-Player / Human vs. AI: 2 Faction Advantage buttons +
      Ch.2 Siege Relic / Sabotage + Roll / Press Assault.
    - In Head-to-Head Human vs. Human Pass-and-Play:
      Left Column = Attacker's 2 Faction Advantages (`ATT:...`)
      Right Column = Defender's 2 Faction Advantages (`DEF:...`)
      Plus a full-width centre Roll / Press Assault bar!
    """
    my_fac = player.get("ch3_faction", "Union")
    att_fac = player.get("ch3_attacker", {}).get("faction", my_fac)
    def_fac = player.get("ch3_defender", {}).get("faction", "Laydere")

    stage = player.get("ch3_combat_stage", "TACTICAL")
    resolved = player.get("ch3_combat_resolved", False)
    more_clashes = len(player.get("ch3_pending_clashes", []))

    if resolved:
        if more_clashes > 0:
            resolve_btn = (
                "press_assault",
                f"Next Clash ({more_clashes} Left) >>",
                TATE_RED,
                "Advance immediately to the next pinned Crossed-Swords "
                "engagement on the map!",
            )
        else:
            resolve_btn = (
                "press_assault",
                "Next Dawn >>",
                EQUIPPED_GREEN,
                "Conclude tonight's engagements and return to the "
                "Strategic War Table for the next Dawn.",
            )
    elif stage == "PRE_ROLL":
        resolve_btn = (
            "roll_battle_dice",
            "Roll Battle Dice >>",
            TATE_RED,
            "Cast both armies' 3D dice pools across the battle mat to "
            "reveal initial combat strength!",
        )
    else:
        resolve_btn = (
            "press_assault",
            "Press Assault & Resolve Clash >>",
            EQUIPPED_GREEN,
            "Lock in all dice modifiers, clash shields, and calculate "
            "proportionate casualties & routs!",
        )

    # --- HEAD-TO-HEAD HUMAN VS. HUMAN MODE ---
    if _is_head_to_head_human_clash(player):
        att_btns = FACTION_COMBAT_BUTTONS.get(
            att_fac, FACTION_COMBAT_BUTTONS["Union"]
        )
        def_btns = FACTION_COMBAT_BUTTONS.get(
            def_fac, FACTION_COMBAT_BUTTONS["Laydere"]
        )
        return [
            (
                f"ATT:{att_btns[0][0]}",
                f"[ATT] {att_btns[0][1]}",
                att_btns[0][2],
                f"Attacker ({att_fac}): {att_btns[0][3]}",
            ),
            (
                f"DEF:{def_btns[0][0]}",
                f"[DEF] {def_btns[0][1]}",
                def_btns[0][2],
                f"Defender ({def_fac}): {def_btns[0][3]}",
            ),
            (
                f"ATT:{att_btns[1][0]}",
                f"[ATT] {att_btns[1][1]}",
                att_btns[1][2],
                f"Attacker ({att_fac}): {att_btns[1][3]}",
            ),
            (
                f"DEF:{def_btns[1][0]}",
                f"[DEF] {def_btns[1][1]}",
                def_btns[1][2],
                f"Defender ({def_fac}): {def_btns[1][3]}",
            ),
            resolve_btn,
        ]

    # --- HUMAN VS. AI (OR AI DEFENSIVE CLASH) ---
    def_is_human = pass_and_play.is_faction_human(def_fac) or (
        not pass_and_play.is_pnp_enabled(player) and def_fac == my_fac
    )
    side_prefix = "DEF:" if (def_is_human and att_fac != my_fac) else "ATT:"
    active_fac = def_fac if side_prefix == "DEF:" else att_fac
    seat_dict = _get_faction_seat_dict(player, active_fac)

    fac_btns = list(
        FACTION_COMBAT_BUTTONS.get(active_fac, FACTION_COMBAT_BUTTONS["Union"])
    )
    inv = seat_dict.get("inventory", [])
    has_relic = any(
        item in inv
        for item in (
            "greek fire",
            "ancient sapper's blueprint",
            "portable printing press",
        )
    )
    if has_relic:
        third_btn = (
            f"{side_prefix}ch2_siege_breach",
            "Ch.2 Siege Relic",
            (175, 115, 32),
            "Deploy your Chapter 2 specialist gear to shatter and "
            "remove the opponent's highest die for free!",
        )
    else:
        third_btn = (
            f"{side_prefix}kokeshi_sabotage",
            "Sabotage (-10s)",
            (112, 48, 142),
            "Spend 10 Silver to cut enemy supply straps and discard "
            "the opponent's highest die.",
        )

    b0 = (
        f"{side_prefix}{fac_btns[0][0]}",
        fac_btns[0][1],
        fac_btns[0][2],
        fac_btns[0][3],
    )
    b1 = (
        f"{side_prefix}{fac_btns[1][0]}",
        fac_btns[1][1],
        fac_btns[1][2],
        fac_btns[1][3],
    )
    return [b0, b1, third_btn, resolve_btn]


def resolve_clearing_name(tile_pos, world_map=None):
    """
    Translates a coordinate key into a narrative landmark name so raw
    coordinates never leak into player-facing logs.
    """
    w_map = world_map if world_map is not None else DEFAULT_WORLD_MAP
    if tile_pos in MAJOR_STRONGHOLDS:
        return MAJOR_STRONGHOLDS[tile_pos]["name"]
    if w_map and isinstance(tile_pos, str) and "," in tile_pos:
        parts = tile_pos.split(",")
        coord = (int(parts[0]), int(parts[1]))
        loc = w_map.get(coord)
        if loc:
            if loc.name and loc.name != "x":
                return f"{loc.name} ({loc.region})"
            return f"the {loc.region} front"
    return "the contested clearing"


# =========================================================================
# 2. CLASH INITIALISATION & DICE POOL ENGINE
# =========================================================================
def init_ch3_evening_clash(
    player,
    attacker_info,
    defender_info,
    tile_pos,
    world_map=None,
    origin_pos=None,
):
    """
    Initialises an Evening Clash or a 3-Stage Stronghold Siege.
    Starts in 'PRE_ROLL' stage so the player explicitly rolls the dice.
    """
    player["ch3_combat_active"] = True
    player["ch3_combat_resolved"] = False
    player["ch3_combat_tile"] = tile_pos
    player["ch3_combat_origin"] = origin_pos
    player["ch3_attacker"] = {
        "faction": attacker_info.get("faction", "Union"),
        "count": max(1, int(attacker_info.get("count", 1))),
    }
    player["ch3_defender"] = {
        "faction": defender_info.get("faction", "Laydere"),
        "count": max(1, int(defender_info.get("count", 1))),
    }
    player["ch3_att_start_cnt"] = player["ch3_attacker"]["count"]
    player["ch3_def_start_cnt"] = player["ch3_defender"]["count"]
    player["ch3_att_losses"] = 0
    player["ch3_def_losses"] = 0

    clearing_title = resolve_clearing_name(tile_pos, world_map)
    player["ch3_clearing_title"] = clearing_title

    is_siege = tile_pos in MAJOR_STRONGHOLDS
    player["ch3_is_siege"] = is_siege
    player["ch3_siege_stage"] = 0

    _roll_engagement_pools(player)
    player["ch3_combat_stage"] = "PRE_ROLL"
    player["ch3_dice_anim_until"] = 0
    player["ch3_fx_anim"] = None
    return player


def _roll_engagement_pools(player):
    """Rolls dice pools for the current skirmish or siege stage."""
    attacker_info = player.get("ch3_attacker", {"faction": "Union", "count": 3})
    defender_info = player.get(
        "ch3_defender", {"faction": "Laydere", "count": 3}
    )
    att_fac = attacker_info.get("faction", "Union")
    def_fac = defender_info.get("faction", "Laydere")
    tile_pos = player.get("ch3_combat_tile", "10,10")
    clearing_title = player.get("ch3_clearing_title", "the contested front")

    att_count = max(1, attacker_info.get("count", 3))
    def_count = max(1, defender_info.get("count", 3))
    player["ch3_att_start_cnt"] = att_count
    player["ch3_def_start_cnt"] = def_count
    player["ch3_att_losses"] = 0
    player["ch3_def_losses"] = 0

    att_seat = _get_faction_seat_dict(player, att_fac)
    rank = att_seat.get("ch3_rank", "Private")
    rank_bonus = 2 if rank == "General" else (1 if rank == "Captain" else 0)
    token_bonus = att_seat.get("ch3_tactical_tokens", 0)
    att_seat["ch3_tactical_tokens"] = 0

    fort_dice = 0
    if player.get("ch3_is_siege"):
        fort_dice = MAJOR_STRONGHOLDS[tile_pos]["fort_bonus"]

    att_dice_n = min(8, att_count + rank_bonus + token_bonus)
    def_dice_n = min(8, def_count + fort_dice)

    att_rolls = [random.randint(1, 6) for _ in range(att_dice_n)]
    def_rolls = [random.randint(1, 6) for _ in range(def_dice_n)]

    player["ch3_att_rolls"] = sorted(att_rolls, reverse=True)
    player["ch3_def_rolls"] = sorted(def_rolls, reverse=True)
    player["ch3_used_combat_powers"] = []
    player["ch3_safe_retreat"] = False
    player["ch3_combat_stage"] = "TACTICAL"
    player["ch3_dice_anim_until"] = pygame.time.get_ticks() + 850

    rem_q = len(player.get("ch3_pending_clashes", []))
    q_tag = f" (+{rem_q} Queued)" if rem_q > 0 else ""
    header = f"CLASH AT {clearing_title.upper()}{q_tag}"
    if player.get("ch3_is_siege"):
        st_idx = player.get("ch3_siege_stage", 0)
        stage_lbl = SIEGE_STAGE_NAMES[min(2, st_idx)]
        header = f"SIEGE OF {clearing_title.upper()} ({stage_lbl})"

    mode_note = (
        "HEAD-TO-HEAD DUEL: Both Attacker (Left) and Defender (Right) "
        "may trigger their Faction Advantages before Pressing Assault!"
        if _is_head_to_head_human_clash(player)
        else "Deploy Faction Advantages or Press Assault to resolve attrition!"
    )
    player["ch3_combat_log"] = [
        header,
        f"Attacker: {att_fac} ({att_count} Bns) vs Defender: {def_fac} "
        f"({def_count} Bns)",
        mode_note,
    ]
    return player


def _trigger_combat_fx(player, fx_type, badge_text):
    """Starts a 900ms procedural Pygame animation on the Battle Diorama."""
    now = pygame.time.get_ticks()
    player["ch3_fx_anim"] = {
        "type": fx_type,
        "start": now,
        "duration": 900,
        "badge": badge_text,
    }
    player["ch3_dice_anim_until"] = now + 450


# =========================================================================
# 3. TACTICAL INTERVENTIONS (ATTACKER & DEFENDER) & ATTRITION ENGINE
# =========================================================================
def _apply_side_combat_power(
    player, side_prefix, base_action, my_rolls, opp_rolls, my_fac, log
):
    """
    Executes `base_action` for either the Attacker (`side_prefix == 'ATT:'`)
    or the Defender (`side_prefix == 'DEF:'`), drawing Silver/Sympathy
    from that faction's seat!
    Returns (success_bool, feedback_msg).
    """
    seat = _get_faction_seat_dict(player, my_fac)
    side_lbl = "Attacker" if side_prefix == "ATT:" else "Defender"

    if base_action == "ragmore_snipe":
        if 6 in my_rolls and opp_rolls:
            my_rolls.remove(6)
            victim = max(opp_rolls)
            opp_rolls.remove(victim)
            _trigger_combat_fx(
                player,
                "ragmore_snipe",
                f"{my_fac.upper()} VOLLEY! SNIPED OPPONENT [{victim}]!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Volley: Spent a '6' to shatter "
                f"opponent '{victim}' die!"
            )
            return True, ""
        return False, "Requires a '6' in that side's dice pool to snipe."

    if base_action == "ragmore_artillery":
        if my_rolls:
            old_low = my_rolls[-1]
            my_rolls[-1] = random.randint(4, 6)
            _trigger_combat_fx(
                player,
                "laydere_polearms",
                f"{my_fac.upper()} SIGHTING! [{old_low}] -> [{my_rolls[-1]}]!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Range Sighting: Lowest die "
                f"({old_low}) re-sighted to {my_rolls[-1]}!"
            )
            return True, ""
        return False, "No dice in pool to re-sight."

    if base_action == "union_barricade":
        has_pair = any(my_rolls.count(v) >= 2 for v in set(my_rolls))
        if has_pair and my_rolls:
            old_low = my_rolls[-1]
            my_rolls[-1] = 6
            _trigger_combat_fx(
                player,
                "union_barricade",
                f"{my_fac.upper()} BARRICADE! [{old_low}] -> [6]!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Barricade Lock: Matched pair "
                f"upgrades lowest die ({old_low}) to 6 & shields troops!"
            )
            return True, ""
        return False, "Requires a matching pair in that side's dice pool."

    if base_action == "union_numbers":
        if len(my_rolls) >= len(opp_rolls):
            bonus_die = random.randint(3, 6)
            my_rolls.append(bonus_die)
            _trigger_combat_fx(
                player,
                "guerrilla_ambush",
                f"{my_fac.upper()} SWARM! +{bonus_die} BONUS DIE!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Swarm Numbers: Militia reserves "
                f"add a '{bonus_die}' die!"
            )
            return True, ""
        return False, "Requires at least as many dice as the opponent!"

    if base_action == "laydere_polearms":
        low_indices = [i for i, v in enumerate(my_rolls) if v <= 2]
        if low_indices:
            for idx in low_indices:
                my_rolls[idx] = random.randint(4, 6)
            _trigger_combat_fx(
                player,
                "laydere_polearms",
                f"{my_fac.upper()} POLEARMS! {len(low_indices)} DICE REFORGED!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Polearms: All 1s and 2s reforged "
                "into heavy 4-6 strikes!"
            )
            return True, ""
        return False, "No 1s or 2s in that side's pool to re-roll."

    if base_action == "laydere_discipline":
        if my_rolls:
            old_v = my_rolls[-1]
            my_rolls[-1] = min(6, old_v + 2)
            _trigger_combat_fx(
                player,
                "laydere_polearms",
                f"{my_fac.upper()} SHIELD-WALL! [{old_v}] -> [{my_rolls[-1]}]!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Shield-Wall: Lowest die boosted "
                f"to {my_rolls[-1]} and casualty armour raised!"
            )
            return True, ""
        return False, "No dice in pool."

    if base_action == "kokeshi_bribe":
        fac_silv = (
            player.get("ch3_factions", {}).get(my_fac, {}).get("silver", 0)
        )
        if (seat.get("silver", 0) >= 15 or fac_silv >= 15) and opp_rolls:
            if seat.get("silver", 0) >= 15:
                seat["silver"] -= 15
            else:
                player["ch3_factions"][my_fac]["silver"] -= 15
            turned_die = opp_rolls.pop(0)
            my_rolls.append(turned_die)
            _trigger_combat_fx(
                player,
                "turncoat_slide",
                f"{my_fac.upper()} BRIBE! STOLE [{turned_die}] DIE!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Bribery: 15 Silver buys an "
                f"opposing unit—stealing their '{turned_die}' die!"
            )
            return True, ""
        return False, "Requires 15 Silver to bribe an opposing battalion."

    if base_action == "guerrilla_ambush":
        ambush_die = random.randint(4, 6)
        my_rolls.append(ambush_die)
        if side_prefix == "ATT:":
            player["ch3_safe_retreat"] = True
        _trigger_combat_fx(
            player,
            "guerrilla_ambush",
            f"{my_fac.upper()} AMBUSH! +{ambush_die} DIE & SAFE RETREAT!",
        )
        log.append(
            f"{my_fac} ({side_lbl}) Guerrilla Strike: Added a "
            f"'{ambush_die}' ambush die and secured safe withdrawal!"
        )
        return True, ""

    if base_action == "communard_praxis":
        fac_data = player.get("ch3_factions", {}).get(my_fac, {})
        if fac_data.get("sympathy", 0) >= 4 and opp_rolls:
            fac_data["sympathy"] -= 4
            converted = max(4, opp_rolls.pop(-1))
            my_rolls.append(converted)
            _trigger_combat_fx(
                player,
                "turncoat_slide",
                f"{my_fac.upper()} PRAXIS! CONVERTED (+{converted} DIE)!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Peaceful Praxis: Opposing "
                f"conscripts join the Commune (+{converted} Die)!"
            )
            return True, ""
        return False, "Requires at least 4 Faction Sympathy."

    if base_action == "forest_fog":
        if opp_rolls and max(opp_rolls) >= 5:
            removed = max(opp_rolls)
            opp_rolls.remove(removed)
            _trigger_combat_fx(
                player,
                "forest_fog",
                f"{my_fac.upper()} MIST! NULLIFIED [{removed}] DIE!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Canopy Mist: Woodland fog "
                f"swallows the opponent's '{removed}' strike!"
            )
            return True, ""
        return False, "No opposing die of 5 or 6 to obscure in the mist."

    if base_action in ("kokeshi_sabotage", "ch2_siege_breach"):
        inv = seat.get("inventory", [])
        has_siege_relic = any(
            item in inv
            for item in (
                "greek fire",
                "ancient sapper's blueprint",
                "portable printing press",
            )
        )
        fac_silv = (
            player.get("ch3_factions", {}).get(my_fac, {}).get("silver", 0)
        )
        if has_siege_relic and opp_rolls:
            removed = max(opp_rolls)
            opp_rolls.remove(removed)
            _trigger_combat_fx(
                player,
                "kokeshi_sabotage",
                f"{my_fac.upper()} RELIC! SHATTERED [{removed}]!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Ch.2 Siege Relic: Shattered "
                f"opponent's highest die ({removed})!"
            )
            return True, ""
        if (seat.get("silver", 0) >= 10 or fac_silv >= 10) and opp_rolls:
            if seat.get("silver", 0) >= 10:
                seat["silver"] -= 10
            else:
                player["ch3_factions"][my_fac]["silver"] -= 10
            highest_opp = max(opp_rolls)
            opp_rolls.remove(highest_opp)
            _trigger_combat_fx(
                player,
                "kokeshi_sabotage",
                f"{my_fac.upper()} SABOTAGE! SHATTERED [{highest_opp}]!",
            )
            log.append(
                f"{my_fac} ({side_lbl}) Sabotage: 10 Silver spent to "
                f"shatter opponent's highest die ({highest_opp})!"
            )
            return True, ""
        return False, "Requires 10 Silver or specialist siege gear."

    return False, "Manoeuvre unavailable."


def execute_ch3_combat_action(player, action_type):
    """
    Executes explicit dice rolling, Attacker and Defender tactical
    interventions, and proportionate mutual attrition & rout retreats.
    """
    if action_type == "roll_battle_dice":
        player["ch3_combat_stage"] = "TACTICAL"
        player["ch3_dice_anim_until"] = pygame.time.get_ticks() + 850
        _trigger_combat_fx(player, "dice_cast", "DICE CAST ACROSS THE MAT!")
        return player, "The battle dice clatter across the felt!"

    if player.get("ch3_combat_stage") == "PRE_ROLL":
        player["ch3_combat_stage"] = "TACTICAL"

    att_rolls = player.get("ch3_att_rolls", [])
    def_rolls = player.get("ch3_def_rolls", [])
    att_info = player.get("ch3_attacker", {"faction": "Union", "count": 3})
    def_info = player.get("ch3_defender", {"faction": "Laydere", "count": 3})
    att_fac = att_info.get("faction", "Union")
    def_fac = def_info.get("faction", "Laydere")
    log = player.get("ch3_combat_log", [])
    clearing_title = player.get("ch3_clearing_title", "the contested front")
    used_powers = player.setdefault("ch3_used_combat_powers", [])

    if action_type != "press_assault":
        if action_type.startswith("DEF:"):
            side_prefix = "DEF:"
            base_act = action_type[4:]
        elif action_type.startswith("ATT:"):
            side_prefix = "ATT:"
            base_act = action_type[4:]
        else:
            side_prefix = "ATT:"
            base_act = action_type
            action_type = f"ATT:{base_act}"

        if action_type in used_powers:
            return (
                player,
                "That tactical manoeuvre has already been used in this stage!",
            )

        if side_prefix == "ATT:":
            ok, err = _apply_side_combat_power(
                player,
                "ATT:",
                base_act,
                att_rolls,
                def_rolls,
                att_fac,
                log,
            )
        else:
            ok, err = _apply_side_combat_power(
                player,
                "DEF:",
                base_act,
                def_rolls,
                att_rolls,
                def_fac,
                log,
            )

        if not ok:
            return player, err

        used_powers.append(action_type)
        player["ch3_att_rolls"] = sorted(att_rolls, reverse=True)
        player["ch3_def_rolls"] = sorted(def_rolls, reverse=True)
        player["ch3_combat_log"] = log
        return player, "\n".join(log)

    # --- RESOLVE CLASH ('press_assault') ---
    att_start = max(1, int(att_info.get("count", 3)))
    def_start = max(1, int(def_info.get("count", 3)))
    att_total = max(
        1, sum(att_rolls) + max(0, att_start - len(att_rolls))
    )
    def_total = max(
        1, sum(def_rolls) + max(0, def_start - len(def_rolls))
    )

    attacker_won = att_total > def_total
    if att_total == def_total and att_fac == "Laydere":
        attacker_won = True
        log.append("Laydere close-quarters discipline wins the tiebreaker!")

    tile_pos = player.get("ch3_combat_tile", "10,10")
    origin_pos = player.get("ch3_combat_origin")
    armies = player.setdefault("ch3_armies", {})

    if player.get("ch3_is_siege") and attacker_won:
        st_idx = player.get("ch3_siege_stage", 0)
        if st_idx < 2:
            stage_att_loss = int(
                math.floor(
                    att_start * (def_total / float(att_total)) * 0.22
                )
            )
            att_info["count"] = max(1, att_start - stage_att_loss)
            def_info["count"] = max(1, def_start - max(1, def_start // 3))
            player["ch3_siege_stage"] = st_idx + 1
            _roll_engagement_pools(player)
            _trigger_combat_fx(
                player,
                "stage_breach",
                f"STAGE {st_idx + 1} BREACHED! (-{stage_att_loss} ATT BNS)",
            )
            player["ch3_combat_log"].insert(
                1,
                f"Breach Won! Attacker lost {stage_att_loss} Bn(s) "
                f"storming {SIEGE_STAGE_NAMES[st_idx]}!",
            )
            return player, "\n".join(player["ch3_combat_log"])

    player["ch3_attacker_won_last"] = attacker_won
    has_att_armour = any(
        p in used_powers
        for p in ("ATT:union_barricade", "ATT:laydere_discipline")
    )
    has_def_fort = bool(
        player.get("ch3_is_siege")
        or player.get("ch3_barricades", {}).get(tile_pos)
        or any(
            p in used_powers
            for p in ("DEF:union_barricade", "DEF:laydere_discipline")
        )
    )

    if attacker_won:
        ratio = min(1.0, def_total / float(att_total))
        mitigation = 0.38 if has_att_armour else 0.58
        att_losses = int(math.floor(att_start * ratio * mitigation))
        att_survivors = max(1, att_start - att_losses)
        att_losses = att_start - att_survivors

        if att_total >= def_total * 2 or def_start <= 1:
            def_losses = def_start
            def_survivors = 0
            rout_msg = f"All {def_losses} {def_fac} Bns overrun!"
        else:
            def_losses = max(1, int(math.ceil(def_start * 0.65)))
            def_survivors = max(0, def_start - def_losses)
            ret_tile = ch3_war_engine.find_retreat_tile(
                player, def_fac, tile_pos, DEFAULT_WORLD_MAP
            )
            ret_name = resolve_clearing_name(ret_tile, DEFAULT_WORLD_MAP)
            if ret_tile in armies and armies[ret_tile]["faction"] == def_fac:
                armies[ret_tile]["count"] += def_survivors
            elif ret_tile not in armies:
                armies[ret_tile] = {
                    "faction": def_fac,
                    "count": def_survivors,
                }
            rout_msg = (
                f"{def_fac} loses {def_losses} Bns; {def_survivors} "
                f"routed Bn(s) retreat to {ret_name}!"
            )

        att_info["count"] = att_survivors
        def_info["count"] = def_survivors
        armies[tile_pos] = {"faction": att_fac, "count": att_survivors}
        player.setdefault("territories", {})[tile_pos] = att_fac

        pts_gain = 15 if player.get("ch3_is_siege") else 5
        fac_dict = player.setdefault("ch3_factions", {}).setdefault(
            att_fac, {}
        )
        fac_dict["agenda_pts"] = fac_dict.get("agenda_pts", 0) + pts_gain

        _trigger_combat_fx(
            player,
            "clash_victory",
            f"{att_fac.upper()} WINS! (-{att_losses} ATT / -{def_losses} DEF)",
        )
        log.append(
            f"VICTORY ({att_total} vs {def_total})! {att_fac} takes "
            f"{clearing_title} with {att_survivors}/{att_start} Bns "
            f"(-{att_losses} Bns). {rout_msg}"
        )

    else:
        ratio = min(1.0, att_total / float(def_total))
        mitigation = 0.35 if has_def_fort else 0.55
        def_losses = int(math.floor(def_start * ratio * mitigation))
        def_survivors = max(1, def_start - def_losses)
        def_losses = def_start - def_survivors

        if player.get("ch3_safe_retreat"):
            att_losses = max(0, int(math.floor(att_start * 0.20)))
            att_survivors = max(1, att_start - att_losses)
        elif def_total >= att_total * 2 or att_start <= 1:
            att_losses = att_start
            att_survivors = 0
        else:
            att_losses = max(1, int(math.ceil(att_start * 0.65)))
            att_survivors = max(0, att_start - att_losses)

        def_info["count"] = def_survivors
        att_info["count"] = att_survivors
        armies[tile_pos] = {"faction": def_fac, "count": def_survivors}

        if att_survivors > 0:
            ret_tile = ch3_war_engine.find_retreat_tile(
                player,
                att_fac,
                tile_pos,
                DEFAULT_WORLD_MAP,
                origin_pos=origin_pos,
            )
            ret_name = resolve_clearing_name(ret_tile, DEFAULT_WORLD_MAP)
            if ret_tile in armies and armies[ret_tile]["faction"] == att_fac:
                armies[ret_tile]["count"] += att_survivors
            elif ret_tile not in armies:
                armies[ret_tile] = {
                    "faction": att_fac,
                    "count": att_survivors,
                }
            rout_msg = (
                f"{att_fac} loses {att_losses} Bns; {att_survivors} "
                f"Bn(s) retreat to {ret_name}!"
            )
        else:
            rout_msg = f"All {att_losses} attacking {att_fac} Bns overrun!"

        _trigger_combat_fx(
            player,
            "clash_defeat",
            f"{def_fac.upper()} HOLDS! (-{att_losses} ATT / -{def_losses} DEF)",
        )
        log.append(
            f"DEFENCE HOLDS ({def_total} vs {att_total})! {def_fac} "
            f"holds {clearing_title} with {def_survivors}/{def_start} "
            f"Bns (-{def_losses} Bns). {rout_msg}"
        )

    player["ch3_att_losses"] = att_losses
    player["ch3_def_losses"] = def_losses
    ch3_war_engine.prune_empty_armies(player)
    ch3_war_engine.recalculate_ch3_total_points(player)
    player["ch3_combat_resolved"] = True
    player["ch3_combat_stage"] = "RESOLVED"
    return player, "\n".join(log)


# =========================================================================
# 4. PROCEDURAL BATTLE DIORAMA & PER-SIDE DICE PALETTE RENDERER
# =========================================================================
def _draw_diorama_die(
    screen,
    cx,
    cy,
    size,
    value,
    player,
    salt=0,
    is_lifted=False,
    style_override=None,
):
    """Renders a 3D bevelled die using that side's equipped dice palette."""
    active_style = (
        style_override
        or player.get("equipped_dice", "bone dice")
    ).lower()
    if active_style not in DICE_PALETTES:
        active_style = "bone dice"

    now = pygame.time.get_ticks()
    anim_until = player.get("ch3_dice_anim_until", 0)
    disp_val = value
    dx, dy = 0, 0

    if now < anim_until:
        rem = (anim_until - now) / 850.0
        phase = (now // 50) + (salt * 3)
        disp_val = (phase % 6) + 1
        dx = int(math.sin(now * 0.05 + salt) * 6 * rem)
        dy = -abs(int(math.cos(now * 0.025 + salt) * 18 * rem))

    if is_lifted:
        size = int(size * 1.18)
        dy -= 8

    cx += dx
    cy += dy

    pal = DICE_PALETTES[active_style]
    half = size // 2
    rect = pygame.Rect(cx - half, cy - half, size, size)

    sh_off = 6 if is_lifted else 3
    pygame.draw.rect(
        screen,
        (18, 14, 12),
        rect.move(sh_off, sh_off + 1),
        border_radius=5,
    )
    pygame.draw.rect(screen, pal["base"], rect, border_radius=5)
    bd_col = GOLD_BRIGHT if (now < anim_until or is_lifted) else CLOCK_BLACK
    pygame.draw.rect(
        screen, bd_col, rect, 2 if is_lifted else 1, border_radius=5
    )

    p_rad = max(2, size // 9)
    off = max(4, size // 4)
    pips = []
    if disp_val in (1, 3, 5):
        pips.append((cx, cy))
    if disp_val in (2, 3, 4, 5, 6):
        pips.extend([(cx - off, cy - off), (cx + off, cy + off)])
    if disp_val in (4, 5, 6):
        pips.extend([(cx + off, cy - off), (cx - off, cy + off)])
    if disp_val == 6:
        pips.extend([(cx - off, cy), (cx + off, cy)])

    for px, py in pips:
        pygame.draw.circle(screen, pal["pip"], (int(px), int(py)), p_rad)


def _draw_fallen_meeple(screen, cx, cy, faction):
    """Draws a toppled (90-degree fallen) wooden meeple for lost units."""
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        faction, ch3_war_engine.DTESSERA_FACTIONS["Union"]
    )
    col = spec["color"]
    dark = (max(0, col[0] - 60), max(0, col[1] - 60), max(0, col[2] - 60))

    pygame.draw.ellipse(screen, (20, 16, 12), (cx - 14, cy - 2, 28, 7))
    body_rect = pygame.Rect(cx - 10, cy - 8, 18, 9)
    pygame.draw.rect(screen, dark, body_rect.move(2, 2), border_radius=3)
    pygame.draw.rect(screen, col, body_rect, border_radius=3)
    pygame.draw.rect(screen, CLOCK_BLACK, body_rect, 1, border_radius=3)
    pygame.draw.circle(screen, col, (cx + 11, cy - 4), 5)
    pygame.draw.circle(screen, CLOCK_BLACK, (cx + 11, cy - 4), 5, 1)


def _draw_active_combat_fx(screen, player, modal_rect):
    """Renders the procedural Pygame tabletop animation and impact badge."""
    fx = player.get("ch3_fx_anim")
    if not fx:
        return

    now = pygame.time.get_ticks()
    elapsed = now - fx["start"]
    dur = float(fx.get("duration", 900))
    if elapsed >= dur:
        player["ch3_fx_anim"] = None
        return

    t = max(0.0, min(1.0, elapsed / dur))
    fx_type = fx["type"]

    att_box_cx = modal_rect.x + 178
    def_box_cx = modal_rect.x + 522
    dice_y = modal_rect.y + 206

    if fx_type == "union_barricade":
        drop_t = min(1.0, t * 2.2)
        beam_y = int(modal_rect.y + 60 + drop_t * (dice_y - modal_rect.y - 82))
        beam_rect = pygame.Rect(att_box_cx - 70, beam_y, 140, 22)
        pygame.draw.rect(screen, (125, 42, 32), beam_rect, border_radius=4)
        pygame.draw.rect(screen, GOLD_BRIGHT, beam_rect, 2, border_radius=4)
        for sx in range(beam_rect.left + 14, beam_rect.right - 10, 24):
            pygame.draw.line(
                screen,
                GOLD_BRIGHT,
                (sx, beam_rect.top + 2),
                (sx + 8, beam_rect.bottom - 2),
                2,
            )

    elif fx_type == "ragmore_snipe":
        if t < 0.45:
            bolt_t = t / 0.45
            bx = int(att_box_cx + bolt_t * (def_box_cx - att_box_cx))
            by = int(dice_y - math.sin(bolt_t * math.pi) * 28)
            pygame.draw.line(
                screen, GOLD_BRIGHT, (bx - 22, by), (bx + 8, by), 4
            )
            pygame.draw.polygon(
                screen,
                TATE_RED,
                [(bx + 12, by), (bx + 2, by - 5), (bx + 2, by + 5)],
            )
        else:
            shatter_t = (t - 0.45) / 0.55
            rad = int(shatter_t * 48)
            for ang in (45, 135, 225, 315):
                rx = def_box_cx + int(math.cos(math.radians(ang)) * rad)
                ry = dice_y + int(math.sin(math.radians(ang)) * rad)
                tri = [(rx, ry - 7), (rx - 7, ry + 6), (rx + 7, ry + 6)]
                pygame.draw.polygon(screen, DIAL_CREAM, tri)
                pygame.draw.polygon(screen, TATE_RED, tri, 2)

    elif fx_type == "kokeshi_sabotage":
        ring_r = int(12 + t * 58)
        pygame.draw.circle(
            screen, (175, 85, 215), (def_box_cx, dice_y), ring_r, 3
        )
        pygame.draw.circle(
            screen, GOLD_BRIGHT, (def_box_cx, dice_y), max(4, ring_r // 2), 2
        )
        for ang in (30, 110, 200, 290):
            rx = def_box_cx + int(math.cos(math.radians(ang)) * ring_r * 0.8)
            ry = dice_y + int(math.sin(math.radians(ang)) * ring_r * 0.8)
            pygame.draw.rect(screen, DIAL_CREAM, (rx - 5, ry - 5, 10, 10))
            pygame.draw.rect(screen, CLOCK_BLACK, (rx - 5, ry - 5, 10, 10), 1)

    elif fx_type == "turncoat_slide":
        ease = 1.0 - (1.0 - t) ** 3
        cur_x = int(def_box_cx - ease * (def_box_cx - att_box_cx))
        cur_y = int(dice_y - math.sin(ease * math.pi) * 32)
        _draw_diorama_die(
            screen, cur_x, cur_y, 38, 6, player, salt=9, is_lifted=True
        )

    elif fx_type == "laydere_polearms":
        sweep_x = int(modal_rect.x + 40 + t * 280)
        pygame.draw.line(
            screen,
            (220, 235, 255),
            (sweep_x, dice_y - 28),
            (sweep_x + 18, dice_y + 28),
            4,
        )
        pygame.draw.circle(
            screen, GOLD_BRIGHT, (sweep_x + 9, dice_y), 14, 2
        )

    elif fx_type == "forest_fog":
        fog_w = int(280 * min(1.0, t * 1.6))
        fog_rect = pygame.Rect(def_box_cx - fog_w // 2, dice_y - 22, fog_w, 44)
        pygame.draw.rect(screen, (48, 92, 62), fog_rect, border_radius=12)
        pygame.draw.rect(screen, (140, 210, 150), fog_rect, 2, border_radius=12)
        pygame.draw.line(
            screen,
            TATE_RED,
            (def_box_cx - 16, dice_y - 16),
            (def_box_cx + 16, dice_y + 16),
            4,
        )
        pygame.draw.line(
            screen,
            TATE_RED,
            (def_box_cx + 16, dice_y - 16),
            (def_box_cx - 16, dice_y + 16),
            4,
        )

    badge_txt = fx.get("badge", "")
    if badge_txt:
        float_y = int(modal_rect.y + 258 - t * 26)
        b_rect = pygame.Rect(modal_rect.centerx - 190, float_y, 380, 28)
        pygame.draw.rect(screen, CLOCK_BLACK, b_rect, border_radius=6)
        pygame.draw.rect(screen, GOLD_BRIGHT, b_rect, 2, border_radius=6)
        draw_fitted_text(
            screen, badge_txt, b_rect, GOLD_BRIGHT, bold=True, max_lines=1
        )


def draw_ch3_battle_diorama(screen, player, font, small_font, mouse_pos):
    """
    Renders the complete 5-Stage Root-Style Evening Battle Diorama with
    Head-to-Head Pass-and-Play Attacker/Defender buttons, per-side 3D
    dice palettes, and proportionate casualty meeples.
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((14, 11, 9, 185))
    screen.blit(overlay, (0, 0))

    ch3_board_renderer.draw_top_tabletop_ribbon(
        screen, player, small_font, active_phase="EVENING"
    )

    fx = player.get("ch3_fx_anim")
    now = pygame.time.get_ticks()
    sh_x, sh_y = 0, 0
    if fx and (now - fx["start"]) < 160:
        sh_x = random.randint(-4, 4)
        sh_y = random.randint(-3, 3)

    modal_rect = pygame.Rect(45 + sh_x, 46 + sh_y, 710, 534)
    pygame.draw.rect(screen, OAK_DARK, modal_rect, border_radius=10)
    pygame.draw.rect(screen, GOLD_ACCENT, modal_rect, 3, border_radius=10)
    pygame.draw.rect(
        screen,
        DIAL_CREAM,
        modal_rect.inflate(-10, -10),
        border_radius=8,
    )

    clearing_title = player.get("ch3_clearing_title", "The Contested Clearing")
    rem_clashes = len(player.get("ch3_pending_clashes", []))
    queue_str = f"  [+{rem_clashes} MORE QUEUED]" if rem_clashes > 0 else ""

    if player.get("ch3_is_siege"):
        st_idx = player.get("ch3_siege_stage", 0)
        hdr_str = (
            f"SIEGE: {clearing_title.upper()} — "
            f"{SIEGE_STAGE_NAMES[min(2, st_idx)]}{queue_str}"
        )
    else:
        hdr_str = f"EVENING ENGAGEMENT: {clearing_title.upper()}{queue_str}"

    hdr_rect = pygame.Rect(modal_rect.x + 16, modal_rect.y + 10, 678, 28)
    pygame.draw.rect(screen, TATE_RED, hdr_rect, border_radius=5)
    pygame.draw.rect(screen, GOLD_BRIGHT, hdr_rect, 1, border_radius=5)
    draw_fitted_text(
        screen, hdr_str, hdr_rect, DIAL_CREAM, bold=True, max_lines=1
    )

    att_info = player.get("ch3_attacker") or {"faction": "Union", "count": 3}
    def_info = player.get("ch3_defender") or {"faction": "Laydere", "count": 3}
    att_fac = att_info.get("faction", "Union")
    def_fac = def_info.get("faction", "Laydere")

    att_seat = _get_faction_seat_dict(player, att_fac)
    def_seat = _get_faction_seat_dict(player, def_fac)
    att_dice_style = att_seat.get("equipped_dice", "bone dice")
    def_dice_style = def_seat.get("equipped_dice", "bone dice")

    stage = player.get("ch3_combat_stage", "TACTICAL")
    resolved = player.get("ch3_combat_resolved", False)
    is_tumbling = now < player.get("ch3_dice_anim_until", 0)

    att_mat = pygame.Rect(modal_rect.x + 20, modal_rect.y + 42, 326, 192)
    def_mat = pygame.Rect(modal_rect.x + 364, modal_rect.y + 42, 326, 192)

    for mat_rect, info, fac, is_att, d_style in (
        (att_mat, att_info, att_fac, True, att_dice_style),
        (def_mat, def_info, def_fac, False, def_dice_style),
    ):
        mat_col = FELT_ATTLE if is_att else FELT_DEF
        pygame.draw.rect(screen, mat_col, mat_rect, border_radius=7)
        pygame.draw.rect(screen, GOLD_ACCENT, mat_rect, 2, border_radius=7)

        role_lbl = "ATTACKER" if is_att else "DEFENDER"
        start_bns = player.get(
            "ch3_att_start_cnt" if is_att else "ch3_def_start_cnt",
            max(1, info.get("count", 3)),
        )
        losses_bns = player.get(
            "ch3_att_losses" if is_att else "ch3_def_losses", 0
        )
        cur_bns = info.get("count", start_bns)

        if resolved:
            sub_hdr = (
                f"{role_lbl}: {fac.upper()} "
                f"({cur_bns}/{start_bns} Survived | -{losses_bns} Lost)"
            )
        else:
            sub_hdr = f"{role_lbl}: {fac.upper()} ({start_bns} Battalions)"

        draw_fitted_text(
            screen,
            sub_hdr,
            pygame.Rect(mat_rect.x + 8, mat_rect.y + 5, 310, 20),
            GOLD_BRIGHT,
            bold=True,
            max_lines=1,
        )

        meeple_y = mat_rect.y + 70
        shown_m = min(6, max(1, start_bns))
        spacing = 44 if shown_m <= 5 else 38
        start_mx = mat_rect.centerx - ((shown_m - 1) * spacing) // 2

        fallen_m = 0
        if resolved and start_bns > 0 and losses_bns > 0:
            fallen_m = max(
                1,
                min(
                    shown_m,
                    int(round((losses_bns / float(start_bns)) * shown_m)),
                ),
            )
            if cur_bns > 0 and fallen_m == shown_m:
                fallen_m = shown_m - 1

        standing_m = shown_m - fallen_m
        for m_idx in range(shown_m):
            mx = start_mx + m_idx * spacing
            if m_idx >= standing_m:
                _draw_fallen_meeple(screen, mx, meeple_y, fac)
            else:
                ch3_board_renderer._draw_single_carved_meeple(
                    screen, mx, meeple_y, 1.1, fac
                )

        if not is_att and player.get("ch3_is_siege"):
            fort_b = MAJOR_STRONGHOLDS.get(
                player.get("ch3_combat_tile", "15,10"), {}
            ).get("fort_bonus", 2)
            keep_rect = pygame.Rect(
                mat_rect.right - 64, mat_rect.y + 28, 54, 22
            )
            pygame.draw.rect(
                screen, (130, 122, 114), keep_rect, border_radius=3
            )
            pygame.draw.rect(screen, GOLD_BRIGHT, keep_rect, 1, border_radius=3)
            draw_fitted_text(
                screen,
                f"KEEP +{fort_b}d6",
                keep_rect,
                DIAL_CREAM,
                bold=True,
                max_lines=1,
            )

        rolls = player.get("ch3_att_rolls" if is_att else "ch3_def_rolls", [])
        if stage == "PRE_ROLL" and not resolved:
            cup_r = pygame.Rect(mat_rect.centerx - 48, mat_rect.y + 96, 96, 50)
            pygame.draw.rect(screen, (92, 54, 32), cup_r, border_radius=8)
            pygame.draw.rect(screen, GOLD_BRIGHT, cup_r, 2, border_radius=8)
            draw_fitted_text(
                screen,
                f"{len(rolls)}d6 CUP\n(Ready)",
                cup_r,
                DIAL_CREAM,
                bold=True,
                max_lines=2,
            )
            str_txt = "Click 'Roll Battle Dice' below!"
        else:
            d_cnt = min(7, len(rolls))
            d_step = 42 if d_cnt <= 6 else 36
            start_dx = mat_rect.centerx - ((d_cnt - 1) * d_step) // 2
            salt_base = 1 if is_att else 30

            for d_idx, d_val in enumerate(rolls[:7]):
                dx = start_dx + d_idx * d_step
                dy = mat_rect.y + 122
                is_lifted = bool(
                    fx
                    and is_att
                    and d_idx == len(rolls[:7]) - 1
                    and fx["type"] in ("union_barricade", "laydere_polearms")
                )
                _draw_diorama_die(
                    screen,
                    dx,
                    dy,
                    34,
                    d_val,
                    player,
                    salt=salt_base + d_idx,
                    is_lifted=is_lifted,
                    style_override=d_style,
                )

            mass_bonus = max(0, start_bns - len(rolls))
            tot_val = sum(rolls) + mass_bonus
            str_txt = (
                "Rolling Dice..."
                if is_tumbling
                else f"TOTAL STRENGTH: {tot_val}"
            )

        shield_rect = pygame.Rect(
            mat_rect.x + 38, mat_rect.bottom - 28, 250, 23
        )
        pygame.draw.rect(screen, CLOCK_BLACK, shield_rect, border_radius=5)
        pygame.draw.rect(screen, GOLD_ACCENT, shield_rect, 1, border_radius=5)
        draw_fitted_text(
            screen, str_txt, shield_rect, GOLD_BRIGHT, bold=True, max_lines=1
        )

    # 4. Central Tug-of-War Balance Bar
    att_s_cnt = player.get("ch3_att_start_cnt", 3)
    def_s_cnt = player.get("ch3_def_start_cnt", 3)
    att_r = player.get("ch3_att_rolls", [])
    def_r = player.get("ch3_def_rolls", [])
    att_sum = sum(att_r) + max(0, att_s_cnt - len(att_r))
    def_sum = sum(def_r) + max(0, def_s_cnt - len(def_r))

    tug_rect = pygame.Rect(modal_rect.x + 20, modal_rect.y + 240, 670, 22)
    pygame.draw.rect(screen, (35, 32, 30), tug_rect, border_radius=5)

    if stage != "PRE_ROLL" and not is_tumbling and (att_sum + def_sum) > 0:
        att_ratio = att_sum / float(att_sum + def_sum)
        att_w = int(tug_rect.width * att_ratio)
        pygame.draw.rect(
            screen,
            TATE_RED,
            (tug_rect.x, tug_rect.y, att_w, tug_rect.height),
            border_radius=5,
        )
        pygame.draw.rect(
            screen,
            (45, 88, 165),
            (
                tug_rect.x + att_w,
                tug_rect.y,
                tug_rect.width - att_w,
                tug_rect.height,
            ),
            border_radius=5,
        )
        diff = att_sum - def_sum
        lead_str = (
            f"ATTACKER LEADS BY +{diff} ({att_sum} vs {def_sum})"
            if diff > 0
            else (
                f"DEFENDER HOLDS BY +{abs(diff)} ({def_sum} vs {att_sum})"
                if diff < 0
                else (
                    "TIED (Laydere Wins Tie!)"
                    if att_fac == "Laydere"
                    else "DEADLOCK TIED (Defender Holds)"
                )
            )
        )
    else:
        lead_str = "AWAITING DICE ROLL TO MEASURE BATTLELINE BALANCE"

    pygame.draw.rect(screen, GOLD_BRIGHT, tug_rect, 1, border_radius=5)
    draw_fitted_text(
        screen, lead_str, tug_rect, DIAL_CREAM, bold=True, max_lines=1
    )

    # 5. Concise Battle Chronicle Box
    log_rect = pygame.Rect(modal_rect.x + 20, modal_rect.y + 266, 670, 68)
    pygame.draw.rect(screen, (250, 246, 236), log_rect, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, log_rect, 1, border_radius=6)

    raw_log = player.get("ch3_combat_log", ["Ready for engagement."])
    log_lines = (
        raw_log.split("\n") if isinstance(raw_log, str) else list(raw_log)
    )
    draw_fitted_text(
        screen,
        "\n".join(log_lines[-3:]),
        log_rect.inflate(-16, -6),
        CLOCK_BLACK,
        align="left",
        max_lines=3,
    )

    # 6. Action Buttons (Supports 4-Button Standard OR 5-Button Head-to-Head!)
    player["ch3_combat_action_rects"] = {}
    btn_specs = get_evening_combat_button_specs(player)
    used_powers = player.get("ch3_used_combat_powers", [])
    hovered_tip = (
        "Hover over any Tactical Advantage button above to inspect its "
        "exact dice effect, casualty mitigation, and requirements."
    )

    if len(btn_specs) == 5:
        # Head-to-Head Layout: 2x2 Faction Buttons + Full-Width Bottom Resolve Bar
        for idx, (act_key, act_lbl, b_col, act_tip) in enumerate(btn_specs[:4]):
            bx = modal_rect.x + 20 + (idx % 2) * 342
            by = modal_rect.y + 340 + (idx // 2) * 40
            b_rect = pygame.Rect(bx, by, 328, 36)

            is_used = act_key in used_powers
            is_locked = stage == "PRE_ROLL" or resolved
            fill_c = (95, 88, 82) if (is_used or is_locked) else b_col
            pygame.draw.rect(screen, fill_c, b_rect, border_radius=6)
            is_hov = b_rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                screen,
                GOLD_BRIGHT if is_hov else CLOCK_BLACK,
                b_rect,
                2 if is_hov else 1,
                border_radius=6,
            )
            disp_lbl = f"{act_lbl} [USED]" if is_used else act_lbl
            draw_fitted_text(
                screen, disp_lbl, b_rect, DIAL_CREAM, bold=True, max_lines=1
            )
            player["ch3_combat_action_rects"][act_key] = b_rect
            if is_hov:
                hovered_tip = act_tip

        # 5th Button: Full-Width Centre Roll / Press Assault Bar
        r_key, r_lbl, r_col, r_tip = btn_specs[4]
        res_rect = pygame.Rect(modal_rect.x + 20, modal_rect.y + 422, 670, 38)
        pygame.draw.rect(screen, r_col, res_rect, border_radius=6)
        is_hov = res_rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if is_hov else CLOCK_BLACK,
            res_rect,
            2 if is_hov else 1,
            border_radius=6,
        )
        draw_fitted_text(
            screen, r_lbl, res_rect, DIAL_CREAM, bold=True, max_lines=1
        )
        player["ch3_combat_action_rects"][r_key] = res_rect
        if is_hov:
            hovered_tip = r_tip
    else:
        for idx, (act_key, act_lbl, b_col, act_tip) in enumerate(btn_specs):
            bx = modal_rect.x + 20 + (idx % 2) * 342
            by = modal_rect.y + 346 + (idx // 2) * 48
            b_rect = pygame.Rect(bx, by, 328, 42)

            is_used = act_key != "press_assault" and act_key in used_powers
            is_locked = (
                stage == "PRE_ROLL"
                and act_key not in ("roll_battle_dice", "press_assault")
            ) or (resolved and act_key != "press_assault")

            fill_c = (95, 88, 82) if (is_used or is_locked) else b_col
            pygame.draw.rect(screen, fill_c, b_rect, border_radius=6)
            is_hov = b_rect.collidepoint(mouse_pos)
            pygame.draw.rect(
                screen,
                GOLD_BRIGHT if is_hov else CLOCK_BLACK,
                b_rect,
                2 if is_hov else 1,
                border_radius=6,
            )

            disp_lbl = f"{act_lbl} [USED]" if is_used else act_lbl
            draw_fitted_text(
                screen, disp_lbl, b_rect, DIAL_CREAM, bold=True, max_lines=1
            )
            player["ch3_combat_action_rects"][act_key] = b_rect

            if is_hov:
                hovered_tip = f"{act_lbl}: {act_tip}"

    # 7. Bottom Hover Tooltip Bar Inside Diorama
    tip_rect = pygame.Rect(modal_rect.x + 20, modal_rect.y + 468, 670, 48)
    pygame.draw.rect(screen, OAK_MID, tip_rect, border_radius=5)
    pygame.draw.rect(screen, GOLD_ACCENT, tip_rect, 1, border_radius=5)
    draw_fitted_text(
        screen,
        hovered_tip,
        tip_rect.inflate(-14, -6),
        DIAL_CREAM,
        align="left",
        max_lines=2,
    )

    _draw_active_combat_fx(screen, player, modal_rect)
    
