import random
import pygame
import companions_engine
import game_data as db
from mechanics import (
    modify_faction,
    advance_time,
    execute_ch2_mission,
    recalculate_player_max_health,
    calculate_stat_based_hp_loss,
)
from ui_components import draw_fitted_text


# =========================================================================
# 1. THE 4 TRADITIONAL ADVENTURE DUNGEONS DATABASE
# =========================================================================
DUNGEON_SPECS = {
    "parvus_catacombs": {
        "name": "The Under-Parvus Tidal Catacombs",
        "coord": (17, 22),
        "rooms": [
            {
                "title": "ROOM 1/5: THE FLOODED STORM-DRAIN SHAFT",
                "type": "ENTRANCE",
                "desc": (
                    "Descending the rusted iron rungs beneath Upper Parvus, you splash onto a slick catwalk above the roaring tidal culvert. "
                    "Ahead, a rusted iron sluice-gate bars the tunnel—its chain is coated in slippery green sea-kelp."
                ),
                "opt_a": ("Winch the chain with steady muscle (2d6 + Str)", "str"),
                "opt_b": ("Use a blade or crowbar to wedge the pawl (2d6 + Tool)", "tool"),
                "opt_c": ("Squeeze through the narrow overflow grating (2d6 + Stl)", "stl"),
            },
            {
                "title": "ROOM 2/5: THE TRIPWIRE FLASH-POT GALLERY",
                "type": "TRAP",
                "desc": (
                    "The vaulted brick passage narrows. Glinting in your torchbeam are three taut copper tripwires stretched ankle-high above the water, "
                    "wired to earthenware black-powder flash-pots mounted in the masonry niches!"
                ),
                "opt_a": ("Delicately snip the copper wires in sequence (2d6 + Stl)", "stl"),
                "opt_b": ("Douse the flash-pot fuses with bilge-water (2d6 + Equ/Lore)", "lore"),
                "opt_c": ("Raise your shield & sprint through the gallery! (2d6 + Str)", "str"),
            },
            {
                "title": "ROOM 3/5: THE BRASS TIDAL PRESSURE MANIFOLD",
                "type": "PUZZLE",
                "desc": (
                    "Three corroded brass pressure-wheels (LEFT, CENTER, RIGHT) control the iron bulkhead to the inner vault.\n"
                    "Chalked on the brickwork is the engineer's rhyme: 'FIRST THE EBB (LOW), THEN THE FLOOD (HIGH), LAST THE SLACK-TIDE (MID) WHERE THE BARGES LIE.'"
                ),
                "dial_labels": ["LOW", "MID", "HIGH"],
                "solution": [0, 2, 1],  # LOW (0), HIGH (2), MID (1)
            },
            {
                "title": "ROOM 4/5: THE SUBTERRANEAN VAULT-WARDEN",
                "type": "COMBAT",
                "guardian_name": "Madri (Kokeshi Tunnel-Sapper)",
                "guardian_hp": 22,
                "guardian_poise": 14,
                "desc": (
                    "Blocking the arched powder-chamber beneath the Promenade stands Madri—ascarred Kokeshi tunnel-sapper wielding a heavy iron trench-maul and a hooded dark-lantern!"
                ),
            },
            {
                "title": "ROOM 5/5: THE POWDER-VAULT UNDER UPPER PARVUS",
                "type": "VAULT",
                "desc": (
                    "You step into the dry limestone foundation chamber directly beneath Upper Parvus and the Artisans' Guild vaults! "
                    "Barrels of blasting-powder, slow-match fuse-trains, and an iron-bound sapper's chest rest between the load-bearing pillars."
                ),
                "silver_reward": 35,
                "item_reward": "sappers' master-key",
                "stat_reward": ("stealth", 1),
            },
        ],
    },

    "old_path_catacombs": {
        "name": "The Old Path Sapper Catacombs",
        "coord": (3, 12),
        "rooms": [
            {
                "title": "ROOM 1/5: THE SUNKEN WAYSTATION CELLAR",
                "type": "ENTRANCE",
                "desc": (
                    "Prying up the chalk-marked flagstone inside the Ruined Waystation reveals a spiral stair of dressed granite descending into forgotten Castellan sapper tunnels."
                ),
                "opt_a": ("Brace the sagging lintel stone with your shoulder (2d6 + Str)", "str"),
                "opt_b": ("Sound the steps with a mason's eye before descending (2d6 + Tool)", "tool"),
                "opt_c": ("Slide down the central knotted rope-shaft (2d6 + Stl)", "stl"),
            },
            {
                "title": "ROOM 2/5: THE PENDULUM MASONRY CORRIDOR",
                "type": "TRAP",
                "desc": (
                    "Counterweighted granite blocks hang from iron chains in the ceiling, rigged to swing like giant scythes if the wrong floor-slab is depressed!"
                ),
                "opt_a": ("Spot the mortar-wear and step only on load-bearing slabs (2d6 + Stl)", "stl"),
                "opt_b": ("Jam an iron spike or blade into the wall-pulley (2d6 + Tool)", "tool"),
                "opt_c": ("Time the swing and dive beneath the granite block (2d6 + Str)", "str"),
            },
            {
                "title": "ROOM 3/5: THE FOUR-BEAT MASON'S ARCHWAY",
                "type": "PUZZLE",
                "desc": (
                    "Three acoustic keystone levers (LEFT, CENTER, RIGHT) lock the vault portcullis.\n"
                    "Carved into the arch is the Wallmaker motto: 'A SOLID BASE (LOW), A TOWERING SPIRE (HIGH), AND A LEVEL PLUMB-LINE (MID) TO ENDURE THE FIRE.'"
                ),
                "dial_labels": ["LOW", "MID", "HIGH"],
                "solution": [0, 2, 1],
            },
            {
                "title": "ROOM 4/5: THE RENEGADE SAPPER CAPTAIN",
                "type": "COMBAT",
                "guardian_name": "Kazuo (Renegade Wallmaker Captain)",
                "guardian_hp": 24,
                "guardian_poise": 15,
                "desc": (
                    "Out of the shadows steps Kazuo, a disgraced Wallmaker surveyor turned Kokeshi vault-guard, swinging a weighted mason's sledge!"
                ),
            },
            {
                "title": "ROOM 5/5: THE ANCIENT ENGINEER'S SANCTUM",
                "type": "VAULT",
                "desc": (
                    "Inside the dry-stone sanctum sits a drafting table of polished slate holding an oiled vellum cylinder and an iron strongbox of guild bullion!"
                ),
                "silver_reward": 40,
                "item_reward": "ancient sapper's blueprint",
                "stat_reward": ("strength", 1),
            },
        ],
    },

    "calluna_crypt": {
        "name": "The Drowned Castellan's Crypt of Calluna",
        "coord": (7, 1),
        "rooms": [
            {
                "title": "ROOM 1/5: THE SUBMERGED BASALT VESTIBULE",
                "type": "ENTRANCE",
                "desc": (
                    "Wading down the mossy basalt steps from Lake Calluna, you face a bronze-bound crypt door sealed with ancient verdigris and tangled water-reeds."
                ),
                "opt_a": ("Put your back into the bronze ring and heave! (2d6 + Str)", "str"),
                "opt_b": ("Clear the reed-silt from the lower hinge-pin (2d6 + Tool)", "tool"),
                "opt_c": ("Slip through the parted stone transom above (2d6 + Stl)", "stl"),
            },
            {
                "title": "ROOM 2/5: THE MARSH-GAS & PORTCULLIS HALL",
                "type": "TRAP",
                "desc": (
                    "Greenish peat-gas bubbles up through cracks in the flooded floor, and a rusted iron portcullis trembles overhead on a frayed hemp counter-rope!"
                ),
                "opt_a": ("Hold your breath and ghost across the dry plinths (2d6 + Stl)", "stl"),
                "opt_b": ("Lash the frayed counter-rope to a pillar first (2d6 + Lore)", "lore"),
                "opt_c": ("Catch the falling portcullis on your shoulder-guard! (2d6 + Str)", "str"),
            },
            {
                "title": "ROOM 3/5: THE SARCOPHAGUS OF THE THREE HOURS",
                "type": "PUZZLE",
                "desc": (
                    "Three rotating stone sundial rings (DAWN, NOON, CURFEW) rest atop the First Castellan's tomb.\n"
                    "The Latin-script epitaph reads: 'WE WAKE AT THE THIRD HOUR (LOW), WE RULE AT THE FIFTH (MID), WE SLEEP AT THE EIGHTH (HIGH).'"
                ),
                "dial_labels": ["LOW (3)", "MID (5)", "HIGH (8)"],
                "solution": [0, 1, 2],
            },
            {
                "title": "ROOM 4/5: THE TOMB-REAVER CHIEFTAIN",
                "type": "COMBAT",
                "guardian_name": "Wulfstan the Tomb-Reaver",
                "guardian_hp": 25,
                "guardian_poise": 14,
                "desc": (
                    "In the burial rotunda, a heavily mailed outlaw chieftain who broke in through a ceiling fissure whirls around with a notched broadsword!"
                ),
            },
            {
                "title": "ROOM 5/5: THE TREASURY OF THE FIRST CASTELLAN",
                "type": "VAULT",
                "desc": (
                    "Upon a velvet-draped altar rests the tarnished silver **Crown of the First Castellan** surrounded by offerings of ancient silver coin!"
                ),
                "silver_reward": 50,
                "item_reward": "crown of the first castellan",
                "stat_reward": ("influence", 1),
            },
        ],
    },

    "caligo_mine": {
        "name": "The Deep-Delve Silver Mine of Caligo",
        "coord": (15, 2),
        "rooms": [
            {
                "title": "ROOM 1/5: THE COLLAPSED TIMBER ADIT",
                "type": "ENTRANCE",
                "desc": (
                    "Inside the mountain fissure, rotten pine shoring-timbers groan under tons of grey Caligo slate, partially blocking the iron ore-cart track."
                ),
                "opt_a": ("Heave the fallen cross-beam aside with raw brawn (2d6 + Str)", "str"),
                "opt_b": ("Wedge a replacement prop-timber under the cap-stone (2d6 + Tool)", "tool"),
                "opt_c": ("Crawl through the ventilation shaft above the rubble (2d6 + Stl)", "stl"),
            },
            {
                "title": "ROOM 2/5: THE RUNAWAY ORE-CART TRESTLE",
                "type": "TRAP",
                "desc": (
                    "As you step onto the narrow wooden trestle spanning a subterranean chasm, a rusty catch snaps up-slope and a loaded iron ore-cart comes hurtling down the rails straight at you!"
                ),
                "opt_a": ("Throw the iron track-switch lever to derail it into the pit! (2d6 + Stl)", "stl"),
                "opt_b": ("Jam an iron bar into the rail-spokes to brake it! (2d6 + Tool)", "tool"),
                "opt_c": ("Vault over the side-rail and hang from the trestle ties! (2d6 + Str)", "str"),
            },
            {
                "title": "ROOM 3/5: THE COUNTERWEIGHT SMELTING CHUTES",
                "type": "PUZZLE",
                "desc": (
                    "Three iron hopper-gates (SLATE, QUARTZ, SILVER) feed the counterweight bridge across the underground tarn.\n"
                    "The assay-slate reads: 'DUMP THE DROSS (LOW), HALF-FILL THE QUARTZ (MID), BRIM THE PURE ORE (HIGH).'"
                ),
                "dial_labels": ["LOW", "MID", "HIGH"],
                "solution": [0, 1, 2],
            },
            {
                "title": "ROOM 4/5: THE CRAZED CLAIM-JUMPER BOSS",
                "type": "COMBAT",
                "guardian_name": "lorcan 'Iron-Pick' (Claim-Jumper)",
                "guardian_hp": 26,
                "guardian_poise": 16,
                "desc": (
                    "At the bottom of the mother-lode gallery stands Lorcan 'Iron-Pick', a towering mountain claim-jumper brandishing a double-headed miner's pick!"
                ),
            },
            {
                "title": "ROOM 5/5: THE STAR-IRON MOTHER-LODE VAULT",
                "type": "VAULT",
                "desc": (
                    "In a crystalline cavern glittering with native wire-silver, you find the miners' locked assay chest and a gleaming billet of meteoric **Star-Iron**!"
                ),
                "silver_reward": 60,
                "item_reward": "star-iron ingot",
                "stat_reward": ("max_health", 1),
            },
        ],
    },
}

DUNGEON_TELEGRAPHS = {
    "HAYMAKER": "hauls back their weapon for a whistling, bone-crushing overhead cleave!",
    "BULL_RUSH": "lowers their shoulder and charges straight down the narrow flagstone aisle to pin you against the wall!",
    "IRON_GUARD": "sets their back foot against a stone pillar and raises a tight, defensive guard!",
}


# =========================================================================
# 2. DUNGEON DISCOVERY & LAUNCHER
# =========================================================================
def check_dungeon_search_entry(player):
    """
    Called when the player uses 'Search' at one of the 4 dungeon coordinates.
    Returns (handled_bool, log_msg, next_state).
    """
    if player.get("current_building"):
        return False, None, "MAIN"

    pos = (player["x"], player["y"])
    coord_to_key = {spec["coord"]: k for k, spec in DUNGEON_SPECS.items()}
    if pos not in coord_to_key:
        return False, None, "MAIN"

    d_key = coord_to_key[pos]
    cleared = player.setdefault("dungeons_cleared", [])

    # Allow re-entering Parvus Catacombs if on Mission 4D/5D/6D even if visited earlier!
    is_parvus_mission_d = (
        d_key == "parvus_catacombs"
        and player.get("chapter_2_route") in (
            "Parvus: F.A.I.-C.N.T. Syndicate",
            "Parvus: Crown Intelligencers",
            "Parvus: Maritime & Artisans Guild (50s)",
        )
        and player.get("ch2_mission_step") == 4
    )

    if d_key in cleared and not is_parvus_mission_d:
        return True, f"You peer into the entrance of **{DUNGEON_SPECS[d_key]['name']}**—you have already conquered its traps, guardian, and vault!", "MAIN"

    p, log, st = init_dungeon(player, d_key)
    return True, log, st


def init_dungeon(player, dungeon_key="parvus_catacombs"):
    """Initializes a 5-Room Traditional Dungeon Crawl in the MINIGAME_DUNGEON Pop-Out."""
    spec = DUNGEON_SPECS.get(dungeon_key, DUNGEON_SPECS["parvus_catacombs"])
    player["dungeon_key"] = dungeon_key
    player["dungeon_room"] = 0
    player["dungeon_torch"] = 100
    player["dungeon_dials"] = [1, 1, 1]  # Starts at [MID, MID, MID] so puzzle is never pre-solved
    player["dungeon_roll_str"] = "Torchlight: 100% | Ready"

    # Initialize & Scale Room 4 Guardian state
    r4 = spec["rooms"][3]
    recalculate_player_max_health(player)
    days_tier = min(5, (player.get("total_game_minutes", 0) // 3000) + player.get("ch2_mission_step", 1))
    base_g_hp = r4["guardian_hp"]
    scaled_g_hp = base_g_hp + (days_tier * 3) + (6 if player.get("traveling_with_bandoka") or player.get("active_companion") else 0)

    player["dungeon_enemy_name"] = r4["guardian_name"]
    player["dungeon_enemy_hp"] = scaled_g_hp
    player["dungeon_enemy_max_hp"] = scaled_g_hp
    player["dungeon_enemy_poise"] = r4["guardian_poise"]
    player["dungeon_enemy_max_poise"] = r4["guardian_poise"]
    player["dungeon_enemy_staggered"] = False
    player["dungeon_telegraph"] = random.choice(["HAYMAKER", "BULL_RUSH", "IRON_GUARD"])
    player["dungeon_momentum"] = 1

    player["dungeon_feedback"] = (
        f"You light a pitch-torch and descend into **{spec['name']}**! "
        "Survive all 5 chambers—traps, puzzles, and the vault guardian—before your torchlight gutters out!"
    )
    return player, player["dungeon_feedback"], "MINIGAME_DUNGEON"

# Alias so both init_dungeon and init_dungeon_crawl work seamlessly!
init_dungeon_crawl = init_dungeon


# =========================================================================
# 3. DUNGEON ROOM RESOLUTION ENGINE (ROOMS 1 TO 5)
# =========================================================================
def dungeon_action(action, player):
    """Handles all actions across Rooms 1–5 in the MINIGAME_DUNGEON pop-out."""
    d_key = player.get("dungeon_key", "parvus_catacombs")
    spec = DUNGEON_SPECS[d_key]
    rm_idx = player.get("dungeon_room", 0)
    rm = spec["rooms"][rm_idx]

    if action == "retreat_dungeon":
        player["active_ch2_mission"] = None
        return player, f"You retreat up the steps out of {spec['name']} into the fresh air.", "MAIN"

    torch = player.get("dungeon_torch", 100)
    dark_penalty = -2 if torch <= 0 else 0

    # ------------------------------------------------------------------
    # ROOMS 1 & 2: ENTRANCE BREACH & MECHANICAL TRAP (2d6 + STAT/TOOL)
    # ------------------------------------------------------------------
    if rm["type"] in ("ENTRANCE", "TRAP"):
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        has_tool = any(t in player.get("inventory", []) for t in ["iron dagger", "iron sword", "steel longsword", "masonry drill", "rope", "grappling hook"])

        if action == "opt_a":
            stat_kind = rm["opt_a"][1]
        elif action == "opt_b":
            stat_kind = rm["opt_b"][1]
        else:
            stat_kind = rm["opt_c"][1]

        if stat_kind == "str":
            bonus = (player.get("strength", 0) // 2) + (2 if "climb" in player.get("skills", []) else 0)
        elif stat_kind == "stl":
            bonus = (player.get("stealth", 0) // 2) + (2 if "intelligence officer" in player.get("skills", []) else 0)
        elif stat_kind == "tool":
            bonus = (3 if has_tool else 0) + (2 if "forge" in player.get("skills", []) or "master wallmaker" in player.get("skills", []) else 0)
        else:
            bonus = (player.get("equusense", 0) // 2) + (2 if player.get("foraging_lore_learned") else 0)

        tot = d1 + d2 + bonus + dark_penalty
        player["dungeon_roll_str"] = f"Roll: [{d1}]+[{d2}] + {bonus} Bonus = {tot}"
        player["dungeon_torch"] = max(0, torch - 12)

        if tot >= 8:
            win_note = ""
            if d1 + d2 == 12:
                player["silver"] += 8
                win_note = " [WINDFALL (Natural 12!): You also spot a hidden niche holding 8 ancient silver coins! +8s]"
            player["dungeon_room"] = rm_idx + 1
            player["dungeon_feedback"] = (
                f"[{tot}: CLEAN SUCCESS!] You overcome the hazard without a scratch and advance deeper into the dungeon!{win_note}"
            )
        else:
            raw_dmg = 1 if tot >= 5 else 2
            dmg, mit_note = calculate_stat_based_hp_loss(raw_dmg, player, rm["title"])
            player["health"] = max(0, player.get("health", 10) - dmg)
            if player["health"] <= 0:
                return player, f"A deadly dungeon trap claims your life in the dark of {spec['name']}...", "DEAD"
            player["dungeon_room"] = rm_idx + 1
            player["dungeon_feedback"] = (
                f"[{tot}: TRAP TRIGGERED (-{dmg} HP{mit_note})!] You force your way through into the next chamber!"
            )
            
        return player, None, "MINIGAME_DUNGEON"

    # ------------------------------------------------------------------
    # ROOM 3: THE 3-DIAL ANCIENT MECHANISM PUZZLE
    # ------------------------------------------------------------------
    elif rm["type"] == "PUZZLE":
        if action.startswith("dial_"):
            d_i = int(action.split("_")[1])
            player["dungeon_dials"][d_i] = (player["dungeon_dials"][d_i] + 1) % 3
            return player, None, "MINIGAME_DUNGEON"

        if action == "pull_master_lever":
            player["dungeon_torch"] = max(0, torch - 10)
            if player["dungeon_dials"] == rm["solution"]:
                player["dungeon_room"] = 3
                player["dungeon_feedback"] = (
                    "CLUNK-CLANG! All three counterweights lock into alignment! The heavy stone bulkhead grinds upward, revealing the Guardian's Rotunda!"
                )
            else:
                player["health"] = max(0, player.get("health", 10) - 1)
                if player["health"] <= 0:
                    return player, "A poison-dart trap triggered by the wrong dial combination fells you...", "DEAD"
                player["dungeon_feedback"] = (
                    "GRIND-HISS! Wrong dial alignment! A jet of scalding steam/darts vents from the wall (-1 HP, -10% Torchlight)! Read the inscription carefully!"
                )
            return player, None, "MINIGAME_DUNGEON"

    # ------------------------------------------------------------------
    # ROOM 4: THE VAULT GUARDIAN (TACTICAL TELEGRAPH & 2d6 COMBAT)
    # ------------------------------------------------------------------
    elif rm["type"] == "COMBAT":
        tele = player.get("dungeon_telegraph", "HAYMAKER")
        stag = player.get("dungeon_enemy_staggered", False)
        mom = player.get("dungeon_momentum", 1)
        g_name = player.get("dungeon_enemy_name", "Guardian")

        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        roll_sum = d1 + d2 + dark_penalty
        w_bonus = db.weapon_max_hit.get(player.get("equipped_weapon", "fists"), 2) // 2
        str_bonus = max(0, player.get("strength", 0) // 3)
        luck = 2 if roll_sum >= 10 else (-1 if roll_sum <= 4 else 0)

        dmg = 0
        p_dmg = 0
        hp_loss = 0
        notes = [f"[Roll {d1}+{d2}={d1+d2}]"]
        player["dungeon_torch"] = max(0, torch - 6)

        if action == "strike_fast":
            if tele == "BULL_RUSH" or stag:
                dmg = max(3, 5 + w_bonus + str_bonus + luck)
                p_dmg = 5
                player["dungeon_momentum"] = min(5, mom + 1)
                player["dungeon_enemy_staggered"] = False
                notes.append(f"Your quick lunge intercepts {g_name} mid-charge (-{dmg} HP, +1 Momentum)!")
            elif tele == "IRON_GUARD":
                dmg = 2
                p_dmg = 1
                hp_loss = 1 if roll_sum < 8 else 0
                notes.append(f"Your strike glances off {g_name}'s iron guard!")
            else:
                dmg = max(2, 4 + w_bonus + luck)
                p_dmg = 2
                hp_loss = 1 if roll_sum >= 8 else 2
                notes.append(f"You trade blows as {g_name}'s heavy cleave grazes you (-{hp_loss} HP)!")

        elif action == "parry_counter":
            if tele == "HAYMAKER":
                dmg = max(3, 4 + w_bonus + str_bonus + luck)
                p_dmg = 7
                player["dungeon_momentum"] = min(5, mom + 2)
                player["dungeon_enemy_staggered"] = True
                notes.append(f"PARRY! You deflect {g_name}'s overhead cleave into the stone floor and riposte (-{dmg} HP, STAGGERED, +2 Momentum)!")
            elif tele == "BULL_RUSH":
                dmg = 1
                hp_loss = 1
                notes.append(f"{g_name} barges through your high parry (-1 HP)!")
            else:
                player["dungeon_momentum"] = min(5, mom + 1)
                notes.append(f"You circle the torchlit pillars, building focus (+1 Momentum).")

        elif action == "heavy_cleave":
            player["dungeon_momentum"] = max(0, mom - 1)
            if tele == "IRON_GUARD" or stag:
                dmg = max(5, 8 + w_bonus + str_bonus + luck)
                p_dmg = 6
                player["dungeon_enemy_staggered"] = True
                notes.append(f"CRUSHING BLOW! You smash straight through {g_name}'s guard (-{dmg} HP, STAGGERED)!")
            else:
                dmg = max(3, 5 + w_bonus + luck)
                p_dmg = 3
                hp_loss = 1
                notes.append(f"A brutal exchange of heavy strikes echoes through the vault (-{dmg} Enemy HP, -1 Your HP)!")

        elif action == "pillar_slam":
            cur_p = player.get("dungeon_enemy_poise", 10)
            grapple_score = roll_sum + (player.get("strength", 0) // 2) + (4 if stag else 0)
            resist_score = random.randint(1, 6) + cur_p
            if grapple_score >= resist_score:
                dmg = 999
                notes.append(f"[Knockout {grapple_score} vs {resist_score}!] You hurl {g_name} into the stone pillar, knocking them out cold!")
            else:
                dmg = 2
                p_dmg = 3
                hp_loss = 1
                notes.append(f"[{grapple_score} vs {resist_score}] {g_name} braces against the flagstones and shakes off your shove (-1 HP)!")

        c_dmg, c_heal, c_mit, c_log = companions_engine.apply_companion_combat_assist(player)
        dmg += c_dmg
        hp_loss = max(0, hp_loss - c_mit)
        if c_log:
            notes.append(c_log)
            
        player["dungeon_enemy_hp"] = max(0, player.get("dungeon_enemy_hp", 10) - dmg)
        player["dungeon_enemy_poise"] = max(0, player.get("dungeon_enemy_poise", 10) - p_dmg)
        if player["dungeon_enemy_poise"] == 0 and player["dungeon_enemy_hp"] > 0:
            player["dungeon_enemy_staggered"] = True

        if hp_loss > 0:
            actual_loss, mit_note = calculate_stat_based_hp_loss(hp_loss, player, g_name)
            player["health"] = max(0, player.get("health", 10) - actual_loss)
            if mit_note:
                notes.append(mit_note)
            if player["health"] <= 0:
                return player, f"You fall before {g_name} in the depths of {spec['name']}...", "DEAD"

        if player["dungeon_enemy_hp"] <= 0:
            player["dungeon_room"] = 4
            player["dungeon_feedback"] = " ".join(notes) + f" {g_name} collapses! The door to the Inner Sanctum Vault swings open!"
            return player, None, "MINIGAME_DUNGEON"

        choices = ["HAYMAKER", "BULL_RUSH", "IRON_GUARD"]
        if tele in choices:
            choices.remove(tele)
        player["dungeon_telegraph"] = random.choice(choices)
        player["dungeon_feedback"] = " ".join(notes)
        return player, None, "MINIGAME_DUNGEON"

    # ------------------------------------------------------------------
    # ROOM 5: THE INNER SANCTUM VAULT & MISSION 4D/5D/6D INTEGRATION
    # ------------------------------------------------------------------
    elif rm["type"] == "VAULT":
        cleared = player.setdefault("dungeons_cleared", [])
        first_clear = (d_key not in cleared)
        if first_clear:
            cleared.append(d_key)

        silv = rm["silver_reward"] if first_clear else 15
        item = rm["item_reward"]
        stat_k, stat_v = rm["stat_reward"]

        player["silver"] += silv
        item_note = ""
        if item not in player["inventory"]:
            player["inventory"].append(item)
            item_note = f", the **{item.title()}**"

        stat_note = ""
        if first_clear:
            player[stat_k] = player.get(stat_k, 0) + stat_v
            if stat_k == "max_health":
                player["health"] = player["max_health"]
            stat_note = f", and **+{stat_v} {stat_k.replace('_', ' ').title()}**"

        player, _ = advance_time(60, player)

        # Check if this is Mission 4D, 5D, or 6D in the Under-Parvus Catacombs!
        route = player.get("chapter_2_route")
        step = player.get("ch2_mission_step", 1)
        mission_note = ""

        if d_key == "parvus_catacombs" and step == 4:
            if route == "Parvus: F.A.I.-C.N.T. Syndicate":
                player["ch2_mission_step"] = 5
                player["position_strength"] = player.get("position_strength", 0) + 25
                mission_note = (
                    "\n\n=== MISSION COMPLETE: SLOW-MATCH FUSES ROUTED (+25% Position Strength)! ===\n"
                    "In the dry vault beneath Upper Parvus, you splice the waterproof slow-match fuses between the powder-casks and light the timed tallow-candle! "
                    "As you climb back to the street, muffled thunder shakes the wealthy promenade!\n"
                    "*** Final Mission: Speak to Speaktruth at the Rope-Walk (or head to the Promenade Balcony) for the Harbour Festival Climax! ***"
                )
            elif route == "Parvus: Crown Intelligencers":
                player["ch2_mission_step"] = 5
                player["position_strength"] = player.get("position_strength", 0) + 25
                mission_note = (
                    "\n\n=== MISSION COMPLETE: THE UPPER PARVUS BOMB DEFUSED (+25% Position Strength)! ===\n"
                    "Spotting the sputtering slow-match fuse inches from the powder-casks, you slice the cord with your blade and flood the powder-trough from the brass manifold! "
                    "Upper Parvus is saved from destruction!\n"
                    "*** Final Mission: Report to Eadric at the Customs House (or Mayor Holdfast at the Promenade) to guard the Harbour Festival! ***"
                )
            elif route == "Parvus: Maritime & Artisans Guild (50s)":
                player["ch2_mission_step"] = 5
                player["position_strength"] = player.get("position_strength", 0) + 25
                mission_note = (
                    "\n\n=== MISSION COMPLETE: GUILD VAULTS FORTIFIED (+25% Position Strength)! ===\n"
                    "Using the Sappers' Master-Key, you release the counterweights on the massive iron blast-shutters—sealing the Artisans' Guild bullion and blueprints behind three feet of granite just before the tremors shake the cliff!\n"
                    "*** Final Mission: Return to Guildmaster Buildhope at the Guildhall to dictate the Grand War-Fleet Contract! ***"
                )

        log = (
            f"=========================================================\n"
            f"   DUNGEON CONQUERED: {spec['name'].upper()}!   \n"
            f"=========================================================\n"
            f"From the ancient vault, you claim **+{silv} Silver**{item_note}{stat_note}!{mission_note}"
        )
        return player, log, "MAIN"

    return player, None, "MINIGAME_DUNGEON"


# =========================================================================
# 4. DUNGEON POP-OUT UI RENDERER (680 x 480 TATE BRITAIN WINDOW)
# =========================================================================
def draw_dungeon_ui(screen, player, font, font_bold, mouse_pos):
    """Renders the 5-Room Traditional Dungeon Crawl Pop-Out Window."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 195))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    TORCH_AMBER = (215, 135, 35)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    d_key = player.get("dungeon_key", "parvus_catacombs")
    spec = DUNGEON_SPECS[d_key]
    rm_idx = player.get("dungeon_room", 0)
    rm = spec["rooms"][rm_idx]

    title = font_bold.render(f"DUNGEON DELVE — {spec['name'].upper()}", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    # 1. Visual 5-Room Node Progress Map + Torchlight & HP Strip
    map_box = pygame.Rect(85, 76, 630, 38)
    pygame.draw.rect(screen, (32, 35, 42), map_box, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, map_box, width=1, border_radius=6)

    node_labels = ["1.Entry", "2.Trap", "3.Puzzle", "4.Guard", "5.Vault"]
    for i in range(5):
        nx = 100 + i * 76
        ny = 95
        if i < 4:
            pygame.draw.line(screen, (110, 115, 125), (nx + 24, ny), (nx + 52, ny), 2)
        n_col = (55, 145, 70) if i < rm_idx else (TORCH_AMBER if i == rm_idx else (65, 70, 80))
        n_rect = pygame.Rect(nx - 26, ny - 12, 56, 24)
        pygame.draw.rect(screen, n_col, n_rect, border_radius=4)
        pygame.draw.rect(screen, DIAL_CREAM if i == rm_idx else (120, 120, 120), n_rect, width=1, border_radius=4)
        nl = pygame.font.Font(None, 16).render(node_labels[i], True, (250, 248, 240))
        screen.blit(nl, nl.get_rect(center=n_rect.center))

    torch = player.get("dungeon_torch", 100)
    hp_str = f"HP: {player.get('health', 10)}/{player.get('max_health', 10)}  |  Torch: {torch}%"
    screen.blit(font_bold.render(hp_str, True, TORCH_AMBER if torch > 20 else TATE_RED), (485, 86))

    # 2. Main Chamber Display Box
    c_box = pygame.Rect(85, 122, 630, 142)
    pygame.draw.rect(screen, (252, 248, 238), c_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, c_box, width=2, border_radius=8)

    screen.blit(font_bold.render(rm["title"], True, TATE_RED), (100, 130))

    if rm["type"] == "PUZZLE":
        draw_fitted_text(screen, rm["desc"], pygame.Rect(100, 152, 600, 56), CLOCK_BLACK, max_lines=3)
        dials = player.get("dungeon_dials", [1, 1, 1])
        d_labels = rm["dial_labels"]
        for d_i in range(3):
            dx = 145 + d_i * 185
            d_rect = pygame.Rect(dx, 214, 145, 38)
            pygame.draw.rect(screen, (40, 46, 58), d_rect, border_radius=6)
            pygame.draw.rect(screen, TORCH_AMBER, d_rect, width=2, border_radius=6)
            d_txt = f"Dial {d_i+1}: {d_labels[dials[d_i]]}"
            draw_fitted_text(screen, d_txt, d_rect, (250, 245, 230), bold=True)

    elif rm["type"] == "COMBAT":
        g_name = player.get("dungeon_enemy_name", "Guardian")
        g_hp = player.get("dungeon_enemy_hp", 20)
        g_max = max(1, player.get("dungeon_enemy_max_hp", 20))
        g_poise = player.get("dungeon_enemy_poise", 12)
        stag = player.get("dungeon_enemy_staggered", False)
        mom = player.get("dungeon_momentum", 1)

        stat_line = f"{g_name} — HP: {g_hp}/{g_max} | Balance: {g_poise} | Your Momentum: {'★'*mom}{'☆'*(5-mom)}"
        if stag:
            stat_line += " [STAGGERED!]"
        screen.blit(font_bold.render(stat_line, True, CLOCK_BLACK), (100, 154))

        hp_bar = pygame.Rect(100, 176, 595, 14)
        pygame.draw.rect(screen, (40, 35, 35), hp_bar, border_radius=4)
        if g_hp > 0:
            pygame.draw.rect(screen, TATE_RED, (100, 176, int(595 * (g_hp / float(g_max))), 14), border_radius=4)
        pygame.draw.rect(screen, CLOCK_BLACK, hp_bar, width=1, border_radius=4)

        tele_k = player.get("dungeon_telegraph", "HAYMAKER")
        tele_txt = f"GUARDIAN TELEGRAPH: {g_name} {DUNGEON_TELEGRAPHS.get(tele_k, '')}"
        draw_fitted_text(screen, tele_txt, pygame.Rect(100, 198, 600, 56), TATE_RED, bold=True, max_lines=2)

    else:
        draw_fitted_text(screen, rm["desc"], pygame.Rect(100, 158, 600, 92), CLOCK_BLACK, max_lines=4)

    # 3. Transcript & Dice Roll Box
    fb_box = pygame.Rect(85, 270, 630, 58)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("dungeon_feedback", ""), fb_box.inflate(-14, -6), (245, 240, 230), max_lines=2)
