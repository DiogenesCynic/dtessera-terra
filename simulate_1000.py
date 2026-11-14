import os
# Force Headless Pygame Mode (no window pops up)
os.environ["SDL_VIDEODRIVER"] = "dummy"

import copy
import random
import csv
import traceback
from collections import Counter
import pygame

pygame.init()

import game_data as db
from map_data import world_map
import conversation as convo
import mini_games
import encounters
from mechanics import (
    modify_faction,
    advance_time,
    get_time_string,
    calculate_max_hit,
    get_eligible_chapter_2_routes,
    resolve_chapter_2_route,
    mark_shift_completed,
    handle_sleep_morning,
)

# Snapshot pristine global state so we can reset cleanly between runs
INITIAL_NPC_DB = copy.deepcopy(db.npc_database)
INITIAL_READABLES_DB = copy.deepcopy(db.readables_database)
INITIAL_WORLD_OBJECTS = {pos: list(loc.objects) for pos, loc in world_map.items()}

ALL_TRACKED_SKILLS = [
    "climb",
    "ride",
    "forge",
    "master blacksmith",
    "market overseer",
    "stable master",
    "mayor's footman",
    "safe travel",
    "master wallmaker",
    "intelligence officer",
    "radical theory",
    "union steward",
    "archery",
]


def make_fresh_player():
    """Creates a clean starting player dictionary matching Dtessera Terra.py."""
    db.npc_database = copy.deepcopy(INITIAL_NPC_DB)
    db.readables_database = copy.deepcopy(INITIAL_READABLES_DB)
    for pos, objs in INITIAL_WORLD_OBJECTS.items():
        world_map[pos].objects = list(objs)

    return {
        "current_building": "school",
        "x": 8, "y": 14, "prev_x": 8, "prev_y": 14,
        "total_game_minutes": 375,
        "last_heal_minute": 375,
        "last_sleep_minute": 375,
        "story_path": None,
        "health": 10, "max_health": 10,
        "hunger": 100, "thirst": 100,
        "last_sustenance_tick": 375,
        "silver": 10,
        "reputation": 0,
        "strength": 0, "stealth": 0, "charisma": 0,
        "influence": 0, "equusense": 0,
        "chapter_2_unlocked": False,
        "chapter_2_route": None,
        "chapter_2_status": "Pending",
        "eligible_ch2_routes": [],
        "chosen_ch2_route": "None",
        "beers_drank": 0,
        "inventory": ["poster", "reference letter"],
        "storage": [],
        "territories": {},
        "skills": [],
        "equipped_weapon": "fists",
        "equipped_shield": "none",
        "faction_wallmakers": 0, "faction_union": 0, "faction_guard": 0,
        "union_status": None,
        "surveyor_report": None,
        "wallmakers_reported": False,
        "current_job": None,
        "current_tenure": 0,
        "last_job_day": 0,
        "shift_start_day": None,
        "blacksmith_shifts_completed": 0,
        "mayors_house_shifts": 0,
        "market_sweeper_shifts": 0,
        "wall_surveyor_shifts": 0,
        "stable_shifts": 0,
        "free_room_used": False,
        "owes_hopestill": False,
        # Wallmakers
        "active_wallmaker_task": None, "wall_sectors_inspected": [],
        "wallmaker_double_agent": False, "reported_shift_1_to_guard": False,
        "reported_shift_2_to_guard": False, "reported_shift_3_to_guard": False,
        "reported_shift_4_to_guard": False,
        "shift_1_mistakes": 0, "shift_2_mistakes": 0,
        "shift_3_mistakes": 0, "shift_4_mistakes": 0, "shift_5_mistakes": 0,
        "sounding_sector": None, "sounding_grid": [], "sounding_revealed": [], "sounding_chalk": [],
        "sounding_tool": "hammer", "sounding_taps": 0, "sounding_recorded": False, "sounding_wiped": True,
        "breach_grid": [], "breach_pieces": [], "breach_selected": None, "breach_scrapes_left": 2,
        "deduction_locs": [2, 3, 1, 0], "deduction_dmgs": [3, 2, 0, 1],
        "deduction_phase": "deduce", "deduction_swap_sel": None, "sabotaged_route": "through",
        "parapet_phase": "stairs", "stair_step": 0, "lantern_open": True,
        "klotski_blocks": [], "klotski_selected": None, "klotski_slides": 0,
        "smuggle_phase": "contact", "tap_step": 0, "patrol_earshot": False,
        "smuggle_route": None, "transfer_step": 0, "transfer_hazard": 0, "smuggle_clean_success": False,
        # Horse & Quests
        "riding_horse": False, "riding_lessons_completed": 0, "last_riding_lesson_day": 0,
        "horse_hunger": 100, "horse_thirst": 100, "horse_shoe_durability": 0,
        "rosinante_feed_count": 0, "rosinante_last_fed_day": 0, "rosinante_fed": False,
        "horse_stabled": False,
        "active_mayor_task": None, "mayor_task_deadline": 0,
        "hopestill_revealed": False, "wallmakers_quest_active": False, "wallmakers_meeting_day": 0,
        "hopestill_angry": False,
        "active_stable_task": None, "stable_task_deadline": 0,
        "active_blacksmith_task": None, "active_market_task": None,
        "active_enemy": None, "selected_verb": None
    }


def ensure_item(player, item_name):
    if item_name not in player["inventory"]:
        player["inventory"].append(item_name)


def safe_npc_choice(npc_name, choice_label, player):
    """Safely routes NPC choices, resolving naming aliases and required items."""
    handlers = getattr(convo, "NPC_HANDLERS", {})
    if npc_name in ["mayors house manager", "mayor's house manager"]:
        if "mayors house manager" in handlers:
            npc_name = "mayors house manager"
        elif "mayor's house manager" in handlers:
            npc_name = "mayor's house manager"

    required_items = {
        ("blacksmith", "Give Mayor's Letter"): "mayor's horse letter",
        ("blacksmith", "Drop off Stallion"): "mayor's stallion",
        ("stable manager", "Return Mayor's Stallion"): "fed and watered stallion",
        ("stable manager", "Deliver Horseshoes"): "crate of horseshoes",
        ("wealdhere", "Deliver Halberds"): "bundle of halberds",
        ("armourer", "Deliver Breastplate"): "custom breastplate",
        ("wealdhere", "Hand in Radical Pamphlets"): "bundle of radical pamphlets",
        ("apothecary", "Deliver Apothecary's Parcel"): "apothecary's parcel",
        ("coryllus", "Offer cobnuts"): "cobnuts",
        ("stable manager", "Throw Sand on Fire"): "bucket of sand",
    }
    req = required_items.get((npc_name, choice_label))
    if req:
        ensure_item(player, req)

    res = convo.handle_npc_choice(npc_name, choice_label, player)
    if isinstance(res, tuple):
        return res[0]
    return player


def snapshot_shift(player, shift_num, label, prev_snap):
    """Formats a concise per-shift breakdown string showing stat deltas."""
    d_ag = player["silver"] - prev_snap["silver"]
    d_rep = player["reputation"] - prev_snap["reputation"]
    new_skills = [s for s in player["skills"] if s not in prev_snap["skills"]]
    skill_str = f", +{','.join(new_skills)}" if new_skills else ""
    sign_ag = "+" if d_ag >= 0 else ""
    sign_rep = "+" if d_rep >= 0 else ""
    snap = {
        "silver": player["silver"],
        "reputation": player["reputation"],
        "skills": list(player["skills"]),
    }
    return f"S{shift_num}: {label} ({sign_ag}{d_ag}s, {sign_rep}{d_rep}Rep{skill_str})", snap


def rest_overnight(player):
    """Rents a room at the Pub/Tavern (or sleeps in Servants' Quarters) for bed & breakfast."""
    prev_bldg = player.get("current_building")
    if player.get("current_job") == "mayor's house":
        handle_sleep_morning(player)
    elif player.get("current_job") == "wall surveyor" or prev_bldg == "tavern":
        player["current_building"] = "tavern"
        safe_npc_choice("goodtidings", "Rent Room (2s)", player)
    else:
        player["current_building"] = "dog and duck pub"
        safe_npc_choice("landlord", "Rent Room (2s)", player)
    player["current_building"] = prev_bldg
    return player

def evaluate_shift_6_and_chapter_2(player, boss_npc, sloppiness=0.20):
    """
    Advances to Day 6, triggers the Boss's Shift 6 Evaluation, and either:
      - Ends the run in Game Over ('Dismissed (Game Over)') if no routes are met, OR
      - Hands in notice and selects an eligible Chapter 2 route at the Noticeboard.
    """
    rest_overnight(player)

    if player["reputation"] <= -1 and random.random() >= sloppiness:
        if "iron sword" not in player["inventory"] and player["silver"] >= 30:
            player["silver"] -= 30
            player["inventory"].append("iron sword")
            player["equipped_weapon"] = "iron sword"
        if "tent" not in player["inventory"] and player["silver"] >= 15:
            player["silver"] -= 15
            player["inventory"].append("tent")

    if player["reputation"] >= 1 and player["charisma"] >= 5 and "playhouse ticket" not in player["inventory"]:
        if player["silver"] >= 5 and random.random() < 0.35:
            player["silver"] -= 5
            player["inventory"].append("playhouse ticket")

    eligible_before_shift_6 = get_eligible_chapter_2_routes(player)

    if not eligible_before_shift_6:
        if player.get("current_job") is not None:
            convo.handle_npc_choice(boss_npc, "Start Shift (5 Completed)", player)
        player["current_job"] = None
        player["current_tenure"] = 0
        player["chapter_2_status"] = "Dismissed (Game Over)"
        player["eligible_ch2_routes"] = []
        player["chosen_ch2_route"] = "GAME OVER: Dismissed"
        return player

    if player.get("current_job") is not None:
        player, log_msg, next_state = convo.handle_npc_choice(boss_npc, "Start Shift (5 Completed)", player)
        if next_state == "DEAD":
            player["chapter_2_status"] = "Dismissed (Game Over)"
            player["eligible_ch2_routes"] = []
            player["chosen_ch2_route"] = "GAME OVER: Dismissed"
            return player
        player, _, _ = convo.handle_npc_choice(boss_npc, "Hand in notice with immediate effect", player)

    eligible = get_eligible_chapter_2_routes(player)
    player["eligible_ch2_routes"] = list(eligible)
    player["chapter_2_status"] = "Qualified for Chapter 2"
    chosen = random.choice(eligible)
    player, _, _ = resolve_chapter_2_route(chosen, player)
    player["chosen_ch2_route"] = chosen
    return player


# =========================================================================
# 1 & 2. WALLMAKERS CAREER (LOYAL & DOUBLE AGENT) — 5 SHIFTS
# =========================================================================
def simulate_wallmakers_career(be_double_agent=False, sloppiness=None):
    if sloppiness is None:
        sloppiness = random.uniform(0.05, 0.40)

    player = make_fresh_player()
    player["reputation"] = -1
    shift_log = {}

    player["current_building"] = "tavern"
    safe_npc_choice("goodtidings", "Ask about Hopestill", player)
    safe_npc_choice("hopestill", "Accept Job Offer", player)
    rest_overnight(player)
    player["current_building"] = "wallmakers' offices"
    safe_npc_choice("hopestill", "Speak to Wellspring", player)
    snap = {"silver": player["silver"], "reputation": player["reputation"], "skills": list(player["skills"])}

    # --- SHIFT 1: Sounding the 4 Wall Sectors ---
    safe_npc_choice("wellspring", "Start Shift (0 Completed)", player)
    for sector in ["north", "west", "south", "east"]:
        mini_games.init_sounding_minigame(player, sector)
        for y in range(4):
            for x in range(4):
                player["sounding_revealed"][y][x] = True
                player["sounding_chalk"][y][x] = (player["sounding_grid"][y][x] == 2)
        if random.random() < sloppiness:
            player["shift_1_mistakes"] += 1
        mini_games.sounding_button_action("record_ledger", player)
        if sector == "east" and random.random() >= sloppiness:
            mini_games.sounding_button_action("wipe_chalk", player)
        mini_games.sounding_button_action("finish_sector", player)

    safe_npc_choice("wellspring", "Return from Task", player)
    if be_double_agent:
        player["reputation"] = max(0, player["reputation"])
        safe_npc_choice("wealdhere", "Report Wallmaker Intel (Undercover)", player)
    player["current_building"] = "tavern"
    safe_npc_choice("hopestill", "Pay 7s & Report", player)
    shift_log[1], snap = snapshot_shift(player, 1, "Sounding", snap)

    # --- SHIFT 2: Pentomino Breach Repair ---
    rest_overnight(player)
    player["current_building"] = "wallmakers' offices"
    safe_npc_choice("wellspring", "Start Shift (1 Completed)", player)
    mini_games.init_breach_minigame(player)
    if random.random() < sloppiness:
        player["shift_2_mistakes"] += 1
    ensure_item(player, "smugglers' cipher")
    player["active_wallmaker_task"] = "report_breach_repair"
    safe_npc_choice("wellspring", "Return from Task", player)
    if be_double_agent and random.random() >= (sloppiness * 0.6):
        safe_npc_choice("wealdhere", "Report Breach Blueprint (Undercover)", player)
    player["current_building"] = "tavern"
    safe_npc_choice("hopestill", "Pay 7s & Report", player)
    shift_log[2], snap = snapshot_shift(player, 2, "Breach Repair", snap)

    # --- SHIFT 3: 4x4x4 Damage Ledger Deduction ---
    rest_overnight(player)
    player["current_building"] = "wallmakers' offices"
    safe_npc_choice("wellspring", "Start Shift (2 Completed)", player)
    mini_games.init_deduction_minigame(player)
    player["deduction_locs"] = [0, 1, 2, 3]
    player["deduction_dmgs"] = [0, 1, 2, 3]
    if random.random() < sloppiness:
        player["shift_3_mistakes"] += 1
    mini_games.deduction_button_action("verify", player)
    route_choice = random.choice(["under", "over"])
    player["deduction_dmgs"] = [2, 1, 0, 3] if route_choice == "under" else [0, 3, 2, 1]
    mini_games.deduction_button_action("submit_final", player)
    safe_npc_choice("wellspring", "Return from Task", player)
    if be_double_agent and random.random() >= (sloppiness * 0.6):
        safe_npc_choice("wealdhere", "Report True Damage Ledger (Undercover)", player)
    player["current_building"] = "tavern"
    safe_npc_choice("hopestill", "Pay 7s & Report", player)
    shift_log[3], snap = snapshot_shift(player, 3, f"Ledger ({route_choice})", snap)

    # --- SHIFT 4: Secret Stairs & Parapet Dead-Drop ---
    rest_overnight(player)
    player["current_building"] = "wallmakers' offices"
    safe_npc_choice("wellspring", "Start Shift (3 Completed)", player)
    mini_games.init_parapet_minigame(player)
    for step_idx in range(8):
        needed_open = (mini_games.STAIR_LAYOUT[step_idx] == "cant")
        if random.random() < sloppiness:
            needed_open = not needed_open
        if player["lantern_open"] != needed_open:
            mini_games.parapet_button_action("toggle_lantern", player)
        mini_games.parapet_button_action("climb_step", player)
    ensure_item(player, "contraband silk cache")
    player["active_wallmaker_task"] = "report_parapet_walk"
    safe_npc_choice("wellspring", "Return from Task", player)
    if be_double_agent and random.random() >= (sloppiness * 0.6):
        safe_npc_choice("wealdhere", "Let Wealdhere Mark Contraband (Undercover)", player)
    player["current_building"] = "tavern"
    safe_npc_choice("hopestill", "Pay 7s & Report", player)
    shift_log[4], snap = snapshot_shift(player, 4, "Parapet Walk", snap)

    # --- SHIFT 5: Contact 'X' & Smuggling Finale ---
    rest_overnight(player)
    player["current_building"] = "wallmakers' offices"
    safe_npc_choice("wellspring", "Start Shift (4 Completed)", player)
    mini_games.init_smuggle_minigame(player)

    guard_steps = 0
    while player.get("smuggle_phase") == "contact" and guard_steps < 20:
        guard_steps += 1
        if player.get("patrol_earshot") and random.random() >= sloppiness:
            mini_games.smuggle_button_action("wait_patrol", player)
        else:
            beat = mini_games.MASON_CODE_SEQ[player.get("tap_step", 0)]
            mini_games.smuggle_button_action(beat, player)

    if player.get("smuggle_phase") == "route":
        mini_games.smuggle_button_action(player.get("sabotaged_route", "under"), player)

    transfer_tries = 0
    while player.get("smuggle_phase") == "transfer" and player.get("transfer_step", 0) < 3 and transfer_tries < 20:
        transfer_tries += 1
        hazard = player.get("transfer_hazard", 0)
        _, correct_act = mini_games.TRANSFER_PROMPTS[hazard]
        if random.random() < sloppiness:
            wrong_act = "freeze" if correct_act != "freeze" else "advance"
            mini_games.smuggle_button_action(wrong_act, player)
        mini_games.smuggle_button_action(correct_act, player)

    if not be_double_agent:
        safe_npc_choice("wellspring", "Return from Task", player)
        player["current_building"] = "tavern"
        safe_npc_choice("hopestill", "Pay 7s & Report", player)

    if be_double_agent:
        outcome = "Cover Blown" if player.get("hopestill_angry") else "Perfect Rat"
    else:
        outcome = "Clean Success" if player.get("smuggle_clean_success") else "Guard Ambush"

    shift_log[5], snap = snapshot_shift(player, 5, f"Finale ({outcome})", snap)
    player["shift_breakdown"] = shift_log
    player["route_variant"] = f"{'Agent' if be_double_agent else 'Loyal'}: {outcome}"
    player["shifts_completed_total"] = player.get("wall_surveyor_shifts", 5)
    player = evaluate_shift_6_and_chapter_2(player, "wellspring", sloppiness)
    return player


# =========================================================================
# 3. BLACKSMITH CAREER — 5 SHIFTS (WITH SLOPPINESS)
# =========================================================================
def simulate_blacksmith_career(sloppiness=None):
    if sloppiness is None:
        sloppiness = random.uniform(0.05, 0.35)

    player = make_fresh_player()
    player["reputation"] = 3
    ensure_item(player, "reference letter")
    player["current_building"] = "blacksmiths"
    shift_log = {}

    safe_npc_choice("blacksmith", "Apply for Apprenticeship", player)
    snap = {"silver": player["silver"], "reputation": player["reputation"], "skills": list(player["skills"])}

    # --- SHIFT 1: Heavy Deliveries ---
    safe_npc_choice("blacksmith", "Start Shift (0 Completed)", player)
    safe_npc_choice("stable manager", "Deliver Horseshoes", player)
    safe_npc_choice("wealdhere", "Deliver Halberds", player)
    safe_npc_choice("armourer", "Deliver Breastplate", player)
    player["inventory"] = [
        i for i in player["inventory"]
        if i not in ["crate of horseshoes", "bundle of halberds", "custom breastplate"]
    ]
    safe_npc_choice("blacksmith", "Return from Task", player)
    shift_log[1], snap = snapshot_shift(player, 1, "Deliveries", snap)

    # --- SHIFT 2: Taming the Furnace (20 Strikes or Sloppy Failure) ---
    rest_overnight(player)
    player["current_building"] = "blacksmiths"
    safe_npc_choice("blacksmith", "Start Shift (1 Completed)", player)
    safe_npc_choice("blacksmith", "I understand. Begin Forging!", player)

    if random.random() < sloppiness:
        player["forge_mistakes"] = 4
        player["active_blacksmith_task"] = "report_forge_fail"
        safe_npc_choice("blacksmith", "Return from Task", player)
        s2_label = "Forge Ruined"
    else:
        if random.random() < sloppiness * 1.5:
            player["forge_mistakes"] = random.choice([1, 2])
            s2_label = "Forge Flawed"
        else:
            player["forge_mistakes"] = 0
            s2_label = "Forge Perfect"
        while player.get("forge_round", 1) <= 20 and player.get("active_blacksmith_task") == "tame_furnace":
            state = player.get("forge_heat_state", 1)
            act = "pump" if state == 0 else "coal" if state == 1 else "wait"
            mini_games.forge_action(act, player)
        if player.get("active_blacksmith_task") is not None:
            safe_npc_choice("blacksmith", "Return from Task", player)
    shift_log[2], snap = snapshot_shift(player, 2, s2_label, snap)

    # --- SHIFT 3: Wallmakers' Masonry Drill (5x5 Pentomino Jigsaw) ---
    rest_overnight(player)
    player["current_building"] = "blacksmiths"
    safe_npc_choice("blacksmith", "Start Shift (2 Completed)", player)
    ensure_item(player, "package of drill parts")
    ensure_item(player, "leather")
    mini_games.init_jigsaw(player)
    player["jigsaw_grid"] = [[1, 1, 1, 2, 2], [1, 3, 3, 2, 2], [1, 3, 4, 4, 5], [3, 3, 4, 4, 5], [5, 5, 5, 5, 5]]
    for p in player["jigsaw_pieces"]:
        p["placed"] = True
    for raw in ["leather", "package of drill parts", "wallmaker blueprint"]:
        if raw in player["inventory"]:
            player["inventory"].remove(raw)
    ensure_item(player, "masonry drill")
    player["active_blacksmith_task"] = "report_shift_3"
    safe_npc_choice("blacksmith", "Return from Task", player)
    shift_log[3], snap = snapshot_shift(player, 3, "Masonry Drill", snap)

    # --- SHIFT 4: Mercenary Confrontation (Duel vs. Brawl vs. Sloppy Cowardice) ---
    rest_overnight(player)
    player["current_building"] = "blacksmiths"
    safe_npc_choice("blacksmith", "Start Shift (3 Completed)", player)

    if random.random() < sloppiness:
        shift4_branch = random.choice(["Call Guard", "Flee Duel"])
    else:
        shift4_branch = random.choices(["Duel", "Brawl"], weights=[0.80, 0.20])[0]

    if shift4_branch == "Duel":
        safe_npc_choice("blacksmith", "Challenge to a duel", player)
        rest_overnight(player)
        player["equipped_weapon"] = "masterwork steel longsword" if "masterwork steel longsword" in player["inventory"] else "fists"
        safe_npc_choice("mercenary", "Start Duel", player)
        rounds = 0
        while player.get("active_enemy") is not None and rounds < 30:
            rounds += 1
            player["health"] = player["max_health"]
            player, _, next_st = encounters.combat_round(player)
            if next_st == "MAIN":
                break
    elif shift4_branch == "Brawl":
        player["equipped_weapon"] = "masterwork steel longsword" if "masterwork steel longsword" in player["inventory"] else "fists"
        safe_npc_choice("blacksmith", "Fight him!", player)
        rounds = 0
        while player.get("active_enemy") is not None and rounds < 30:
            rounds += 1
            player["health"] = player["max_health"]
            player, _, next_st = encounters.combat_round(player)
            if next_st == "MAIN":
                break
    elif shift4_branch == "Flee Duel":
        safe_npc_choice("blacksmith", "Challenge to a duel", player)
        rest_overnight(player)
        safe_npc_choice("mercenary", "Flee", player)
    else:
        safe_npc_choice("blacksmith", "Call the Guard", player)

    shift_log[4], snap = snapshot_shift(player, 4, f"Mercenary ({shift4_branch})", snap)

    # --- SHIFT 5: Stables Fire Rescue & Secret Ledger ---
    rest_overnight(player)
    player["current_building"] = "blacksmiths"
    safe_npc_choice("blacksmith", "Start Shift (4 Completed)", player)

    if random.random() < (sloppiness * 0.75):
        player["active_blacksmith_task"] = None
        player["blacksmith_shifts_completed"] += 1
        player["current_tenure"] += 1
        player["reputation"] -= 3
        player = mark_shift_completed(player)
        s5_label = "Fire Panic (Failed)"
    else:
        safe_npc_choice("head hostler", "Drag him out of the smoke!", player)
        ensure_item(player, "bucket of sand")
        ensure_item(player, "hidden secret ledger")
        safe_npc_choice("stable manager", "Throw Sand on Fire", player)
        player["fire_extinguished"] = True
        player["current_building"] = "blacksmiths"
        safe_npc_choice("blacksmith", "Return from Task", player)
        s5_label = "Fire & Ledger"

    shift_log[5], snap = snapshot_shift(player, 5, s5_label, snap)
    player["shift_breakdown"] = shift_log
    player["route_variant"] = f"Blacksmith ({shift4_branch} / {s5_label})"
    player["shifts_completed_total"] = player.get("blacksmith_shifts_completed", 5)
    player = evaluate_shift_6_and_chapter_2(player, "blacksmith", sloppiness)
    return player


# =========================================================================
# 4. MARKET SWEEPER CAREER — 5 SHIFTS + 3 MERCHANT SIDE-QUESTS
# =========================================================================
def simulate_market_career(sloppiness=None):
    if sloppiness is None:
        sloppiness = random.uniform(0.05, 0.40)

    player = make_fresh_player()
    player["reputation"] = 2
    player["current_building"] = "town hall"
    shift_log = {}

    safe_npc_choice("market manager", "Apply for Job", player)
    if player["current_job"] != "market":
        player["current_job"] = "market"
    snap = {"silver": player["silver"], "reputation": player["reputation"], "skills": list(player["skills"])}

    # --- SHIFT 1: The Misplaced Master Key (+ Fruiterer Cobnuts Side-Quest) ---
    safe_npc_choice("market manager", "Start Shift (0 Completed)", player)
    safe_npc_choice("postmaster", "Ask about Godwin's Key", player)
    safe_npc_choice("fairlight", "Ask about Godwin's Key", player)
    safe_npc_choice("sigeberht", "Ask about Godwin's Key", player)
    ensure_item(player, "muddy master key")
    player["active_market_task"] = "search_fountain_key"

    if random.random() >= sloppiness:
        safe_npc_choice("fruiterer", "Ask if they need a hand (Side-Quest)", player)
        ensure_item(player, "cobnuts")
        safe_npc_choice("fruiterer", "Deliver Cobnuts to Fruiterer", player)

    copied_key = random.random() < 0.25
    if copied_key:
        safe_npc_choice("hopestill", "Sell Wax Impression of Master Key (30s)", player)

    safe_npc_choice("market manager", "Return from Task", player)
    shift_log[1], snap = snapshot_shift(player, 1, "Key+Cobnuts" if player.get("market_sq1_done") else "Key Only", snap)

    # --- SHIFT 2: The Moving Postie Interception ---
    rest_overnight(player)
    safe_npc_choice("market manager", "Start Shift (1 Completed)", player)
    ensure_item(player, "apothecary's parcel")
    player["active_market_task"] = "deliver_to_apothecary"
    safe_npc_choice("apothecary", "Deliver Apothecary's Parcel", player)
    player["active_market_task"] = "report_market_shift_2"
    safe_npc_choice("market manager", "Return from Task", player)
    shift_log[2], snap = snapshot_shift(player, 2, "Postie Parcel", snap)

    # --- SHIFT 3: Contraband Pamphlets (+ Apothecary Recipe Side-Quest) ---
    rest_overnight(player)
    safe_npc_choice("market manager", "Start Shift (2 Completed)", player)

    if random.random() >= sloppiness and hasattr(mini_games, "RECIPE_TARGET_SEQ"):
        safe_npc_choice("apothecary", "Help mix Fever-Draught (Side-Quest)", player)
        for req_ing, req_qty in mini_games.RECIPE_TARGET_SEQ:
            if random.random() < (sloppiness * 0.5):
                player["recipe_ing_idx"] = (req_ing + 1) % 4
                mini_games.recipe_button_action("add_cauldron", player)
            player["recipe_ing_idx"] = req_ing
            player["recipe_qty"] = req_qty
            mini_games.recipe_button_action("add_cauldron", player)

    ensure_item(player, "bundle of radical pamphlets")
    s3_branch = random.choice(["Read & Keep", "Return to Shareall", "Report to Guard"])

    if s3_branch == "Read & Keep":
        if random.random() >= sloppiness:
            player["charisma"] += 1
            if "radical theory" not in player["skills"]:
                player["skills"].append("radical theory")
        player["active_market_task"] = "contraband_hidden"
        safe_npc_choice("market manager", "Return from Task", player)
        if random.random() < sloppiness:
            if "bundle of radical pamphlets" in player["inventory"]:
                player["inventory"].remove("bundle of radical pamphlets")
            player["reputation"] -= 3
            modify_faction(player, "faction_guard", -3)
            s3_branch = "Stop-and-Search Caught"
    elif s3_branch == "Return to Shareall":
        safe_npc_choice("vegetable stall merchant", "Discreetly return Radical Pamphlets", player)
        player["active_market_task"] = "report_market_shift_3"
        safe_npc_choice("market manager", "Return from Task", player)
    else:
        player["active_market_task"] = "hand_contraband_to_guard"
        safe_npc_choice("wealdhere", "Hand in Radical Pamphlets", player)
        if random.random() < sloppiness:
            safe_npc_choice("wealdhere", "Stammer nervously", player)
        else:
            safe_npc_choice("wealdhere", "Explain calmly that you found it while sweeping", player)
        player["active_market_task"] = "contraband_hidden"
        safe_npc_choice("market manager", "Return from Task", player)

    shift_log[3], snap = snapshot_shift(player, 3, f"Pamphlets ({s3_branch})", snap)

    # --- SHIFT 4: 4x4x4 Fly-Tipping Logic Puzzle (+ Butcher Brawl Side-Quest) ---
    rest_overnight(player)
    player["market_sweeper_shifts"] = 3
    player["active_market_task"] = None
    safe_npc_choice("market manager", "Start Shift (3 Completed)", player)

    if random.random() >= sloppiness:
        safe_npc_choice("butcher", "Ask about Fly-Tipping / Stall Trouble", player)
        if player["charisma"] >= 2 and random.random() < 0.65:
            brawl_choice = "Step between them and talk them down"
        else:
            brawl_choice = "Throw dirty sweep-water over both of them!"
        safe_npc_choice("market manager", brawl_choice, player)
    elif random.random() < 0.5:
        safe_npc_choice("butcher", "Ask about Fly-Tipping / Stall Trouble", player)
        safe_npc_choice("market manager", "Duck behind the stalls and wait for the Guard", player)

    if hasattr(mini_games, "flytip_button_action"):
        player["flytip_locs"] = [0, 1, 2, 3]
        player["flytip_wastes"] = [0, 1, 2, 3]
        mini_games.flytip_button_action("verify", player)
    player["active_market_task"] = "report_market_shift_4"
    player.pop("brawl_prior_task", None)
    safe_npc_choice("market manager", "Return from Task", player)
    shift_log[4], snap = snapshot_shift(player, 4, "FlyTip+Brawl" if player.get("market_sq4_done") else "FlyTip Only", snap)

    # --- SHIFT 5: Stop Thief! (3-Stage Chase Finale) ---
    rest_overnight(player)
    player["market_sweeper_shifts"] = 4
    player["active_market_task"] = None
    safe_npc_choice("market manager", "Start Shift (4 Completed)", player)

    s1_opt = "Scramble blindly through the crowd" if random.random() < sloppiness else "Bellow 'MAKE WAY!'"
    safe_npc_choice("market manager", s1_opt, player)
    if "chase_thief_dir" not in player:
        mini_games.init_chase(player, stage=1, bonus_paces=0)

    steps = 0
    while player.get("market_state") != "chase_stage_2" and steps < 15:
        steps += 1
        d_idx = player.get("chase_thief_dir", 1)
        d_str = {0: "left", 1: "straight", 2: "right"}[d_idx]
        mini_games.chase_action(d_str, player)

    if random.random() < sloppiness:
        safe_npc_choice("market manager", "Shove the heavy cabbage cart out of the way", player)
    else:
        safe_npc_choice("market manager", "Pole-vault over the cabbages using your heavy broom!", player)
    if "chase_thief_dir" not in player:
        mini_games.init_chase(player, stage=2, bonus_paces=0)

    steps = 0
    while player.get("market_state") != "chase_stage_3" and steps < 20:
        steps += 1
        d_idx = player.get("chase_thief_dir", 1)
        d_str = {0: "left", 1: "straight", 2: "right"}[d_idx]
        mini_games.chase_action(d_str, player)

    if random.random() < sloppiness:
        s5_ending = "Thief Escaped"
        player["active_market_task"] = "report_market_shift_5_fail"
    else:
        s5_ending = random.choices(["Javelin Win", "50/50 Bribe", "Syndicate"], weights=[0.75, 0.15, 0.10])[0]
        if s5_ending == "Javelin Win":
            player["chase_mistakes"] = 0
            safe_npc_choice("market manager", "Hurl your broom like a javelin into his legs!", player)
            ensure_item(player, "market lockbox")
            player["active_market_task"] = "report_market_shift_5_win"
        elif s5_ending == "50/50 Bribe":
            safe_npc_choice("market manager", "Cut a 50/50 deal: take 40s and let him over the wall", player)
        else:
            safe_npc_choice("market manager", "Seize the lockbox for the Free-Earth Syndicate!", player)

    safe_npc_choice("market manager", "Return from Task", player)

    shift_log[5], snap = snapshot_shift(player, 5, f"Chase ({s5_ending})", snap)
    player["shift_breakdown"] = shift_log
    player["route_variant"] = f"Market ({s3_branch} / {s5_ending})"
    player["shifts_completed_total"] = player.get("market_sweeper_shifts", 5)
    player = evaluate_shift_6_and_chapter_2(player, "market manager", sloppiness)
    return player


# =========================================================================
# 5. STABLES CAREER — 5 SHIFTS (WITH SLOPPINESS)
# =========================================================================
def simulate_stables_career(sloppiness=None):
    if sloppiness is None:
        sloppiness = random.uniform(0.05, 0.35)

    player = make_fresh_player()
    player["reputation"] = 2
    player["current_building"] = "stables"
    shift_log = {}

    safe_npc_choice("stable manager", "Apply for Job", player)
    if player["current_job"] != "stables":
        player["current_job"] = "stables"
    snap = {"silver": player["silver"], "reputation": player["reputation"], "skills": list(player["skills"])}

    # --- SHIFT 1: Coryllus the Runaway ---
    safe_npc_choice("stable manager", "Start Shift (0 Completed)", player)
    if random.random() < sloppiness:
        safe_npc_choice("coryllus", "Approach with halter", player)
    ensure_item(player, "cobnuts")
    safe_npc_choice("coryllus", "Offer cobnuts", player)
    ensure_item(player, "coryllus (haltered)")
    player["active_stable_task"] = "return_coryllus"
    safe_npc_choice("stable manager", "Return from Task", player)
    shift_log[1], snap = snapshot_shift(player, 1, "Coryllus", snap)

    # --- SHIFT 2: The Foaling Crisis (Supplies + 4-Part Quiz) ---
    rest_overnight(player)
    safe_npc_choice("stable manager", "Start Shift (1 Completed)", player)
    player["silver"] -= 10
    for item in ["birthing tonic", "clean straw", "bucket of hot water", "foaling manual"]:
        ensure_item(player, item)
    player["active_stable_task"] = "gather_supplies"
    safe_npc_choice("stable manager", "Return from Task", player)

    quiz_pairs = [
        ("Wash hands in hot water", "Wipe hands on straw"),
        ("Administer Tonic", "Yell loudly"),
        ("Reposition forelegs", "Pull hind legs"),
        ("Pull in rhythm", "Pull continuously"),
    ]
    for right_ans, wrong_ans in quiz_pairs:
        ans = wrong_ans if random.random() < sloppiness else right_ans
        safe_npc_choice("stable manager", ans, player)
    shift_log[2], snap = snapshot_shift(player, 2, "Foaling Quiz", snap)

    # --- SHIFT 3: The Missing Ledger ---
    rest_overnight(player)
    safe_npc_choice("stable manager", "Start Shift (2 Completed)", player)
    ensure_item(player, "torn ledger page")
    ensure_item(player, "smudged receipt")
    player["active_stable_task"] = "report_manager_1"
    safe_npc_choice("stable manager", "Return from Task", player)
    player["stable_state"] = "solve_puzzle"
    culprit = random.choice(["The Guard", "The Blacksmith"]) if random.random() < sloppiness else "The Mayor"
    safe_npc_choice("stable manager", culprit, player)
    shift_log[3], snap = snapshot_shift(player, 3, f"Ledger ({culprit})", snap)

    # --- SHIFT 4: Fromabove Extortion Confrontation (Boss vs. Union Path) ---
    rest_overnight(player)
    safe_npc_choice("stable manager", "Start Shift (3 Completed)", player)
    union_path = random.random() < 0.50
    if union_path:
        player["union_status"] = "joined"
        modify_faction(player, "faction_union", 3)
        s4_choice = "Cover for Fromabove (Loyal to Union)"
    else:
        s4_choice = "Report Fromabove (Loyal to Boss)"

    player["active_stable_task"] = "report_to_godspeed_4"
    safe_npc_choice("stable manager", "Return from Task", player)
    player["stable_state"] = "shift_4_decision"
    safe_npc_choice("stable manager", s4_choice, player)
    shift_log[4], snap = snapshot_shift(player, 4, "Union Cover" if union_path else "Loyal Report", snap)

    # --- SHIFT 5: The Stall Allocation Crisis ---
    rest_overnight(player)
    safe_npc_choice("stable manager", "Start Shift (4 Completed)", player)

    if random.random() < sloppiness:
        player["stable_state"] = None
        player["active_stable_task"] = None
        player["stable_shifts"] = 5
        player["current_tenure"] += 1
        player["reputation"] -= 4
        if "stable master" in player["skills"]:
            player["skills"].remove("stable master")
        s5_label = "Stall Disaster"
    else:
        player["stable_state"] = "stall_allocation"
        safe_npc_choice("stable manager", "Conclude they cannot fit", player)
        player["stable_state"] = "who_goes_outside"
        safe_npc_choice("stable manager", "Send Union outside", player)

        player["silver"] = max(0, player["silver"] - 20)
        player["active_stable_task"] = "report_manager_5"
        safe_npc_choice("stable manager", "Return from Task", player)
        s5_label = "Stall Allocation"

        if player.get("steward_nomination_eligible") and random.random() >= sloppiness:
            player["current_building"] = "dog and duck pub"
            safe_npc_choice("horse groom", "Meet with Union Council", player)
            safe_npc_choice("horse groom", "Accept Nomination (Run for Steward)", player)

    if random.random() < 0.35 and random.random() >= sloppiness:
        for _ in range(5):
            rest_overnight(player)
            if player["silver"] >= 10:
                safe_npc_choice("stable manager", "Riding Lesson (10s)", player)

    shift_log[5], snap = snapshot_shift(player, 5, s5_label, snap)
    player["shift_breakdown"] = shift_log
    player["route_variant"] = f"{'Union Steward' if union_path else 'Stable Master'} ({s5_label})"
    player["shifts_completed_total"] = player.get("stable_shifts", 5)
    player = evaluate_shift_6_and_chapter_2(player, "stable manager", sloppiness)
    return player


# =========================================================================
# 6. HOUSE STAFF CAREER — 5 SHIFTS (WITH SLOPPINESS)
# =========================================================================
def simulate_house_staff_career(sloppiness=None):
    if sloppiness is None:
        sloppiness = random.uniform(0.05, 0.40)

    player = make_fresh_player()
    player["reputation"] = 3
    ensure_item(player, "reference letter")
    player["current_building"] = "mayor's staff entrance"
    shift_log = {}

    safe_npc_choice("mayors house manager", "Apply for Job", player)
    if player["current_job"] != "mayor's house":
        player["current_job"] = "mayor's house"
    snap = {"silver": player["silver"], "reputation": player["reputation"], "skills": list(player["skills"])}

    # --- SHIFT 1: Mail Exchange, Guard House, Blacksmith & School ---
    safe_npc_choice("mayors house manager", "Start Shift (0 Completed)", player)
    ensure_item(player, "mayor's outgoing letters")
    player["active_mayor_task"] = "post_office"
    safe_npc_choice("postmaster", "Interact", player)

    ensure_item(player, "mayor's incoming post")
    player["active_mayor_task"] = "find_mayor_1"
    safe_npc_choice("mayor", "Interact", player)

    ensure_item(player, "mayor's horse letter")
    player["active_mayor_task"] = "blacksmith"
    safe_npc_choice("blacksmith", "Give Mayor's Letter", player)

    ensure_item(player, "blacksmith's horse report")
    player["active_mayor_task"] = "find_mayor_2"
    safe_npc_choice("mayor", "Interact", player)

    ensure_item(player, "mayor's dinner letter")
    player["active_mayor_task"] = "deliver_dinner_letter"
    safe_npc_choice("mayors house manager", "Return from Task", player)
    shift_log[1], snap = snapshot_shift(player, 1, "Royal Dispatches", snap)

    # --- SHIFT 2: Butter, Flu Medicine, Birthday Cake & Coal Negotiation ---
    rest_overnight(player)
    safe_npc_choice("mayors house manager", "Start Shift (1 Completed)", player)

    player["silver"] -= 5
    ensure_item(player, "butter")
    player["active_mayor_task"] = "buy_butter"
    safe_npc_choice("mayors house manager", "Return from Task", player)

    player["silver"] -= 10
    ensure_item(player, "flu medicine")
    player["active_mayor_task"] = "buy_medicine"
    safe_npc_choice("mayors house manager", "Return from Task", player)

    ensure_item(player, "mayor's birthday cake")
    player["active_mayor_task"] = "deliver_cake"
    safe_npc_choice("mayor", "Interact", player)

    player["active_mayor_task"] = "report_to_praisegod"
    safe_npc_choice("mayors house manager", "Return from Task", player)

    player["active_mayor_task"] = "negotiate_coal"
    coal_options = ["Promise Mayor's Favor", "Threaten with Mayor's wrath"]
    if player["silver"] >= 40 and random.random() >= sloppiness:
        coal_options.append("Pay for horses (40s)")
    coal_choice = random.choice(coal_options)
    safe_npc_choice("wellspring", coal_choice, player)
    ensure_item(player, "sack of coal")
    player["active_mayor_task"] = "return_with_coal"
    safe_npc_choice("mayors house manager", "Return from Task", player)
    shift_log[2], snap = snapshot_shift(player, 2, f"Cake & Coal ({coal_choice.split()[0]})", snap)

    # --- SHIFT 3: The Mayor's Stallion & Paid Riding Lesson ---
    rest_overnight(player)
    safe_npc_choice("mayors house manager", "Start Shift (2 Completed)", player)
    safe_npc_choice("stable manager", "Collect Mayor's Stallion", player)
    ensure_item(player, "mayor's stallion")
    player["active_mayor_task"] = "blacksmith_horse"
    safe_npc_choice("blacksmith", "Drop off Stallion", player)
    player["active_mayor_task"] = "riding_lesson"
    safe_npc_choice("stable manager", "Take Riding Lesson", player)
    player["active_mayor_task"] = "collect_shod_horse"
    safe_npc_choice("blacksmith", "Collect Shod Stallion", player)
    if "mayor's shod stallion" in player["inventory"]:
        player["inventory"].remove("mayor's shod stallion")
    ensure_item(player, "fed and watered stallion")
    player["active_mayor_task"] = "return_horse_to_stables"
    safe_npc_choice("stable manager", "Return Mayor's Stallion", player)
    player["active_mayor_task"] = "report_to_praisegod_3"
    safe_npc_choice("mayors house manager", "Return from Task", player)
    shift_log[3], snap = snapshot_shift(player, 3, "Mayor's Stallion", snap)

    # --- SHIFT 4: Secret Wallmakers Meeting & Playhouse Journalist ---
    rest_overnight(player)
    safe_npc_choice("mayors house manager", "Start Shift (3 Completed)", player)
    ensure_item(player, "mayor's seal")
    player["hopestill_revealed"] = True
    player["active_mayor_task"] = "find_hopestill"
    safe_npc_choice("hopestill", "Show Mayor's Seal", player)
    player["active_mayor_task"] = "wallmakers_matinee"
    safe_npc_choice("wellspring", "Deliver Message", player)
    player["active_mayor_task"] = "playhouse_meet"
    if random.random() < sloppiness:
        journalist_choice = random.choice(["Deny everything", "Threaten him"])
    else:
        journalist_choice = random.choice([
            "Bribe for silence", "Deny everything", "Threaten him",
            "Leak scandal to Union (+Union)", "Hand journalist's notes to Watch (+Guard)"
        ])
    safe_npc_choice("fairlight", journalist_choice, player)
    player["active_mayor_task"] = "report_playhouse"
    safe_npc_choice("mayors house manager", "Return from Task", player)
    shift_log[4], snap = snapshot_shift(player, 4, f"Playhouse ({journalist_choice.split()[0]})", snap)

    # --- SHIFT 5: Union Investigation, Pub Eavesdrop & School Parley ---
    rest_overnight(player)
    safe_npc_choice("mayors house manager", "Start Shift (4 Completed)", player)
    safe_npc_choice("union clerk", "Interact", player)
    safe_npc_choice("mayors house manager", "Return from Task", player)

    safe_npc_choice("landlord", "Order Sustenance", player)
    safe_npc_choice("landlord", "Murky Ale (1s)", player)
    if random.random() < sloppiness:
        pub_choice = "Side with management"
    else:
        pub_choice = random.choice(["Side with management", "Remain neutral", "Side with workers"])
    safe_npc_choice("landlord", pub_choice, player)
    player["active_mayor_task"] = "report_pub"
    safe_npc_choice("mayors house manager", "Return from Task", player)

    ensure_item(player, "mayor's seal")
    player["active_mayor_task"] = "arrange_meeting"
    safe_npc_choice("union clerk", "Interact", player)
    player["active_mayor_task"] = "inform_market"
    safe_npc_choice("mayor", "Interact", player)
    player["active_mayor_task"] = "attend_meeting"
    safe_npc_choice("mayor", "Interact", player)
    if player.get("mayor_dialogue_state") == "union_choice":
        safe_npc_choice("mayor", random.choice(["Side with Mayor", "Side with Truthtale"]), player)
    player["active_mayor_task"] = "finish_shift_5"
    safe_npc_choice("mayors house manager", "Return from Task", player)

    if random.random() < sloppiness:
        player["reputation"] -= 2

    shift_log[5], snap = snapshot_shift(player, 5, f"Union Parley ({pub_choice.split()[0]})", snap)
    player["shift_breakdown"] = shift_log
    player["route_variant"] = f"Footman ({coal_choice.split()[0]}/{journalist_choice.split()[0]}/{pub_choice.split()[0]})"
    player["shifts_completed_total"] = player.get("mayors_house_shifts", 5)
    player = evaluate_shift_6_and_chapter_2(player, "mayors house manager", sloppiness)
    return player


# =========================================================================
# BATCH EXECUTION & FULL CSV EXPORT (1,200 SIMULATIONS)
# =========================================================================
if __name__ == "__main__":
    print("=" * 115)
    print("  RUNNING 1,200 SIMULATIONS ACROSS ALL 6 SHIFT ROUTES & EXPORTING FULL BREAKDOWN TO CSV")
    print("=" * 115)

    csv_filename = "simulation_results.csv"
    summary_csv_filename = "simulation_route_summary.csv"
    csv_rows = []

    career_runners = [
        ("Wallmakers (Loyal)", lambda: simulate_wallmakers_career(False)),
        ("Wallmakers (Agent)", lambda: simulate_wallmakers_career(True)),
        ("Blacksmith",         simulate_blacksmith_career),
        ("Market Sweeper",     simulate_market_career),
        ("Stables Hand",       simulate_stables_career),
        ("House Staff",        simulate_house_staff_career),
    ]

    sim_id = 1
    runs_per_track = 200  # 200 runs x 6 tracks = 1,200 total runs

    route_stats = {name: [] for name, _ in career_runners}

    for career_name, runner in career_runners:
        for _ in range(runs_per_track):
            try:
                p = runner()
                sb = p.get("shift_breakdown", {})
                total_mistakes = (
                    p.get("shift_1_mistakes", 0)
                    + p.get("shift_2_mistakes", 0)
                    + p.get("shift_3_mistakes", 0)
                    + p.get("shift_4_mistakes", 0)
                    + p.get("shift_5_mistakes", 0)
                    + p.get("forge_mistakes", 0)
                    + p.get("chase_mistakes", 0)
                    + p.get("stable_mistakes", 0)
                )
                skills_earned = list(dict.fromkeys(p.get("skills", [])))

                row = {
                    "Simulation_ID": sim_id,
                    "Career_Track": career_name,
                    "Route_Variant": p.get("route_variant", career_name),
                    "Shifts_Completed": p.get("shifts_completed_total", 5),
                    "Shift_1_Breakdown": sb.get(1, "N/A"),
                    "Shift_2_Breakdown": sb.get(2, "N/A"),
                    "Shift_3_Breakdown": sb.get(3, "N/A"),
                    "Shift_4_Breakdown": sb.get(4, "N/A"),
                    "Shift_5_Breakdown": sb.get(5, "N/A"),
                    "Final_Silver": p["silver"],
                    "Reputation": p["reputation"],
                    "Health": p["health"],
                    "Max_Health": p["max_health"],
                    "Hunger": p["hunger"],
                    "Thirst": p["thirst"],
                    "Strength": p.get("strength", 0),
                    "Charisma": p.get("charisma", 0),
                    "Stealth": p.get("stealth", 0),
                    "Influence": p.get("influence", 0),
                    "Equusense": p.get("equusense", 0),
                    "Chapter_2_Status": p.get("chapter_2_status", "Pending"),
                    "Eligible_Ch2_Count": len(p.get("eligible_ch2_routes", [])),
                    "Eligible_Ch2_Routes": "; ".join(p.get("eligible_ch2_routes", [])) if p.get("eligible_ch2_routes") else "None",
                    "Chosen_Ch2_Route": p.get("chosen_ch2_route", "None"),
                    "Wallmakers_Faction": p["faction_wallmakers"],
                    "Union_Faction": p["faction_union"],
                    "Guard_Faction": p["faction_guard"],
                    "Union_Status": p.get("union_status") or "None",
                    "Equipped_Weapon": p.get("equipped_weapon", "fists"),
                    "Riding_Lessons": p.get("riding_lessons_completed", 0),
                    "Total_Mistakes": total_mistakes,
                    "Days_Elapsed": (p["total_game_minutes"] // 1000) + 1,
                    "Skill_Count": len(skills_earned),
                    "Skills_Earned": "; ".join(skills_earned) if skills_earned else "None",
                }
                for sk in ALL_TRACKED_SKILLS:
                    col_name = "Skill_" + sk.replace("'", "").replace(" ", "_").title()
                    row[col_name] = 1 if sk in skills_earned else 0

                csv_rows.append(row)
                route_stats[career_name].append(row)
                sim_id += 1
            except Exception:
                print(f"[!] Error on Sim #{sim_id} ({career_name}):")
                print(traceback.format_exc())

    skill_cols = ["Skill_" + sk.replace("'", "").replace(" ", "_").title() for sk in ALL_TRACKED_SKILLS]
    csv_headers = [
        "Simulation_ID", "Career_Track", "Route_Variant", "Shifts_Completed",
        "Shift_1_Breakdown", "Shift_2_Breakdown", "Shift_3_Breakdown",
        "Shift_4_Breakdown", "Shift_5_Breakdown",
        "Final_Silver", "Reputation", "Health", "Max_Health", "Hunger", "Thirst",
        "Strength", "Charisma", "Stealth", "Influence", "Equusense",
        "Wallmakers_Faction", "Union_Faction", "Guard_Faction",
        "Union_Status", "Equipped_Weapon", "Riding_Lessons",
        "Total_Mistakes", "Days_Elapsed", "Skill_Count", "Skills_Earned",
        "Chapter_2_Status", "Eligible_Ch2_Count", "Eligible_Ch2_Routes", "Chosen_Ch2_Route"
    ] + skill_cols

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_rows)

    summary_headers = [
        "Career_Track", "Runs", "Avg_Silver", "Min_Silver", "Max_Silver",
        "Avg_Rep", "Min_Rep", "Max_Rep", "Avg_Wall_Fac", "Avg_Union_Fac", "Avg_Guard_Fac",
        "Avg_Str", "Min_Str", "Max_Str", "Avg_Cha", "Min_Cha", "Max_Cha",
        "Avg_Stl", "Min_Stl", "Max_Stl", "Avg_Inf", "Avg_Equ",
        "Avg_Skills", "All_Skills_Observed",
        "Qualified_Pct", "Dismissed_Pct", "Avg_Ch2_Routes"
    ]
    summary_rows = []

    print(f"{'Career Track':<20} | {'Silver':<7} | {'Rep':<5} | {'Wall':<5} | {'Union':<5} | {'Guard':<5} | {'Str':<4} | {'Cha':<4} | {'Stl':<4} | {'Inf':<4} | {'Equ':<4} | {'Skills Observed'}")
    print("-" * 115)

    for career_name, rows in route_stats.items():
        if not rows:
            continue
        n = len(rows)
        avg_ag = sum(r["Final_Silver"] for r in rows) / n
        min_ag = min(r["Final_Silver"] for r in rows)
        max_ag = max(r["Final_Silver"] for r in rows)
        avg_rep = sum(r["Reputation"] for r in rows) / n
        min_rep = min(r["Reputation"] for r in rows)
        max_rep = max(r["Reputation"] for r in rows)
        avg_wall = sum(r["Wallmakers_Faction"] for r in rows) / n
        avg_uni = sum(r["Union_Faction"] for r in rows) / n
        avg_grd = sum(r["Guard_Faction"] for r in rows) / n
        avg_str = sum(r["Strength"] for r in rows) / n
        min_str = min(r["Strength"] for r in rows)
        max_str = max(r["Strength"] for r in rows)
        avg_cha = sum(r["Charisma"] for r in rows) / n
        min_cha = min(r["Charisma"] for r in rows)
        max_cha = max(r["Charisma"] for r in rows)
        avg_stl = sum(r["Stealth"] for r in rows) / n
        min_stl = min(r["Stealth"] for r in rows)
        max_stl = max(r["Stealth"] for r in rows)
        avg_inf = sum(r["Influence"] for r in rows) / n
        avg_equ = sum(r["Equusense"] for r in rows) / n
        avg_sk = sum(r["Skill_Count"] for r in rows) / n

        dismissed_cnt = sum(1 for r in rows if r["Chapter_2_Status"] == "Dismissed (Game Over)")
        qual_cnt = n - dismissed_cnt
        avg_ch2 = sum(r["Eligible_Ch2_Count"] for r in rows) / n

        observed_skills = sorted({
            sk.strip()
            for r in rows
            for sk in r["Skills_Earned"].split(";")
            if sk.strip() and sk.strip() != "None"
        })
        skills_str = ", ".join(observed_skills) if observed_skills else "None"

        print(
            f"{career_name:<20} | {avg_ag:<7.1f} | {avg_rep:<5.1f} | "
            f"{avg_wall:<5.1f} | {avg_uni:<5.1f} | {avg_grd:<5.1f} | "
            f"{avg_str:<4.2f} | {avg_cha:<4.2f} | {avg_stl:<4.2f} | "
            f"{avg_inf:<4.2f} | {avg_equ:<4.2f} | {skills_str}"
        )

        summary_rows.append({
            "Career_Track": career_name,
            "Runs": n,
            "Avg_Silver": round(avg_ag, 2),
            "Min_Silver": min_ag,
            "Max_Silver": max_ag,
            "Avg_Rep": round(avg_rep, 2),
            "Min_Rep": min_rep,
            "Max_Rep": max_rep,
            "Avg_Wall_Fac": round(avg_wall, 2),
            "Avg_Union_Fac": round(avg_uni, 2),
            "Avg_Guard_Fac": round(avg_grd, 2),
            "Avg_Str": round(avg_str, 2),
            "Min_Str": min_str,
            "Max_Str": max_str,
            "Avg_Cha": round(avg_cha, 2),
            "Min_Cha": min_cha,
            "Max_Cha": max_cha,
            "Avg_Stl": round(avg_stl, 2),
            "Min_Stl": min_stl,
            "Max_Stl": max_stl,
            "Avg_Inf": round(avg_inf, 2),
            "Avg_Equ": round(avg_equ, 2),
            "Avg_Skills": round(avg_sk, 2),
            "All_Skills_Observed": skills_str,
            "Qualified_Pct": round(qual_cnt / n * 100, 1),
            "Dismissed_Pct": round(dismissed_cnt / n * 100, 1),
            "Avg_Ch2_Routes": round(avg_ch2, 2),
        })

    with open(summary_csv_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_headers)
        writer.writeheader()
        writer.writerows(summary_rows)

    print("=" * 115)
    print(f"[+] Exported {len(csv_rows)} full playthrough rows to '{csv_filename}'")
    print(f"[+] Exported 6-route summary breakdown to '{summary_csv_filename}'")

    
    # =====================================================================
    # CHAPTER 2 QUALIFICATION & SHIFT 6 DISMISSAL TELEMETRY REPORT
    # =====================================================================
    from collections import Counter

    print("\n" + "=" * 85)
    print("  CHAPTER 2 QUALIFICATION vs. SHIFT 6 DISMISSAL (GAME OVER) BY CAREER")
    print("=" * 85)
    print(f"{'Career Track':<22} | {'Runs':<5} | {'Qualified (%)':<16} | {'Dismissed / Game Over (%)':<25} | {'Avg Routes'}")
    print("-" * 85)

    career_Rows = [r for r in csv_rows if r["Career_Track"] != "AI Learning (Survival)"]
    total_career_runs = len(career_Rows)
    total_dismissed = 0

    for track_name in ["Wallmakers (Loyal)", "Wallmakers (Agent)", "Blacksmith", "Market Sweeper", "Stables Hand", "House Staff"]:
        t_rows = [r for r in career_Rows if r["Career_Track"] == track_name]
        if not t_rows:
            continue
        n = len(t_rows)
        dismissed = sum(1 for r in t_rows if r["Chapter_2_Status"] == "Dismissed (Game Over)")
        qualified = n - dismissed
        total_dismissed += dismissed
        avg_routes = sum(r["Eligible_Ch2_Count"] for r in t_rows) / n
        print(
            f"{track_name:<22} | {n:<5} | "
            f"{qualified:>3} ({qualified/n*100:>5.1f}%)     | "
            f"{dismissed:>3} ({dismissed/n*100:>5.1f}%)              | "
            f"{avg_routes:.2f}"
        )

    print("-" * 85)
    if total_career_runs > 0:
        total_qual = total_career_runs - total_dismissed
        print(
            f"{'OVERALL TOTAL':<22} | {total_career_runs:<5} | "
            f"{total_qual:>3} ({total_qual/total_career_runs*100:>5.1f}%)     | "
            f"{total_dismissed:>3} ({total_dismissed/total_career_runs*100:>5.1f}%)              |"
        )
    print("=" * 85)

    print("\n=== CHAPTER 2 STARTING POINT DISTRIBUTION (ACROSS ALL RUNS) ===")
    route_counts = Counter(r["Chosen_Ch2_Route"] for r in career_Rows)
    for route_name, count in route_counts.most_common():
        pct = (count / total_career_runs * 100) if total_career_runs else 0
        print(f"  • {route_name:<42}: {count:>4} runs ({pct:>5.1f}%)")

def simulate_full_chapter_3_war(player, world_map, max_days=25):
    """
    Simulates a complete Chapter 3 campaign from Day 1 until a faction
    reaches 100 Hegemony Points (or max_days is reached).
    """
    import ch3_combat_engine
    import ch3_war_engine
    import mechanics

    player["ch3_rank"], _ = mechanics.evaluate_chapter_3_state(player)
    player = mechanics.init_chapter_3_world_board(player, world_map)
    ch3_war_engine.recalculate_ch3_total_points(player)

    my_fac = player.get("ch3_faction", "Union")
    days_fought = 0

    while days_fought < max_days:
        days_fought += 1
        player["ch3_day"] = days_fought
        player = mechanics.init_ch3_morning_phase(player)

        # Use available Chapter 2 specialist tools in Morning Phase
        for t_key, _, _ in ch3_war_engine.get_available_ch2_war_tools(player):
            ch3_war_engine.execute_ch2_war_tool(player, t_key, world_map)

        # AI Factions Muster & Expand
        player = ch3_war_engine.process_enemy_faction_turns(player, world_map)
        for ai_key, ai_data in player.get("ch3_factions", {}).items():
            if ai_key != my_fac and random.random() < 0.55:
                ch3_war_engine.apply_ai_agenda_balance_step(ai_data)

        # Simulate Evening Engagement
        att_info = {"faction": my_fac, "count": 4}
        def_info = {"faction": "Laydere", "count": 3}
        player = ch3_combat_engine.init_ch3_evening_clash(
            player, att_info, def_info, "10,10", world_map
        )
        player, _ = ch3_combat_engine.execute_ch3_combat_action(
            player, "press_assault"
        )

        is_over, winner = ch3_war_engine.check_ch3_endgame_trigger(player)
        if is_over:
            player["ch3_campaign_days"] = days_fought
            player["ch3_campaign_winner"] = winner
            break

    return player
