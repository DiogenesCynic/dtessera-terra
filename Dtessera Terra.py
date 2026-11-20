"""
Dtessera Terra.py
-----------------
Main game entry point, state machine, event loop, and UI controller for Dtessera Terra.
"""

import asyncio
import copy
import visual_backdrop
import ch2_castellan
import json
import math
import random
import os
import sys

if getattr(sys, "frozen", False):
    if sys.platform == "darwin":
        # On Mac, save inside ~/Documents/Dtessera_Terra_Saves so Gatekeeper never blocks writes
        _SAVE_DIR = os.path.expanduser("~/Documents/Dtessera_Terra_Saves")
    else:
        # On Windows, save right next to Dtessera_Terra.exe
        _SAVE_DIR = os.path.dirname(sys.executable)
    os.makedirs(_SAVE_DIR, exist_ok=True)
    os.chdir(_SAVE_DIR)
    
import game_data as db
from collections import Counter
import pygame
import world_services
import search_engine
import weather_engine
import cryptography_engine
import printing_press_engine
import crafting_engine
import dice_and_charms
import ch2_easter_eggs
for _k, _v in crafting_engine.EXOTIC_GEAR_DATABASE.items():
    db.item_database.setdefault(_k, _v)
    if _v.get("slot") == "weapon":
        db.weapon_max_hit[_k] = _v.get("damage", 6)
import companions_engine
import meta_progression
import ch3_war_engine
import ch3_combat_engine
import ch3_board_renderer
import ch3_tutorial_book

from map_data import world_map
import conversation as convo
from mechanics import (
    AFFLICTION_INFO,
    advance_time,
    build_playtest_report,
    can_use_storage,
    check_stabling_foreclosure,
    check_territory_and_terrain_access,
    consume_item_helper,
    deposit_silver_helper,
    drink_helper,
    drop_item_helper,
    equip_item_helper,
    evaluate_chapter_3_state,
    feed_animal_helper,
    fill_flask_helper,
    format_item_name,
    get_available_horses,
    get_eligible_chapter_2_routes,
    get_inventory_weight,
    get_max_carry_weight,
    get_player_look_range,
    get_stabling_debt,
    get_tile_territory,
    get_time_string,
    give_gift_helper,
    graze_animal_helper,
    infect_player,
    init_ch3_morning_phase,
    mark_shift_completed,
    mount_dismount_helper,
    process_food_spoilage,
    resolve_chapter_2_route,
    resolve_ch3_combat,
    resolve_wall_climb,
    resolve_wall_walk,
    retrieve_item_helper,
    sell_item_helper,
    stable_horse_helper,
    stash_item_helper,
    steal_letter_map_helper,
    steal_subject_helper,
    water_animal_helper,
    withdraw_silver_helper,
    check_building_open,
    handle_sleep_nap,
    handle_sleep_morning,
)
from ui_components import (
    Button,
    CircleButton,
    DecimalClockUI,
    MAP_CONFIGS,
    RetroDPad,
    TextPanelUI,
    draw_cartographic_map,
    draw_title_or_intro_card,
)
import encounters
import mini_games
import chapter_2
import ch2_union
import ch2_guard
import ui_renderer
import ui_components
import ch2_dungeons
import ch2_parvus
import ch2_election
import ch2_roguery
import pass_and_play

# =========================================================================
# 1. CORE GAME DATA & STATE
# =========================================================================
player = {
    # STARTING POSITION
    "current_building": "school",
    "x": 8,
    "y": 14,
    "prev_x": 8,
    "prev_y": 14,

    "total_game_minutes": 375,
    "last_heal_minute": 375,
    "last_sleep_minute": 375,

    # PLAYER SPECIFIC
    "story_path": None,
    "health": 10,
    "max_health": 10,
    "hunger": 100,
    "thirst": 100,
    "last_sustenance_tick": 375,
    "silver": 10,
    "reputation": 0,
    "strength": 0,
    "stealth": 0,
    "charisma": 0,
    "influence": 0,
    "equusense": 0,
    "beers_drank": 0,
    "inventory": [],
    "storage": [],
    "territories": {},
    "skills": [],
    "equipped_weapon": "fists",
    "equipped_shield": "none",

    # FACTIONS & JOBS
    "faction_wallmakers": 0,
    "faction_union": 0,
    "faction_guard": 0,
    "faction_vanguardists": 0,
    "faction_communards": 0,
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
    "postbox_letter_taken": False,

    # WALLMAKERS
    "active_wallmaker_task": None,
    "wall_sectors_inspected": [],
    "wallmaker_double_agent": False,
    "reported_shift_1_to_guard": False,
    "reported_shift_2_to_guard": False,
    "reported_shift_3_to_guard": False,
    "reported_shift_4_to_guard": False,
    "shift_1_mistakes": 0,
    "shift_2_mistakes": 0,
    "shift_3_mistakes": 0,
    "shift_4_mistakes": 0,
    "shift_5_mistakes": 0,
    "sounding_sector": None,
    "sounding_grid": [],
    "sounding_revealed": [],
    "sounding_chalk": [],
    "sounding_tool": "hammer",
    "sounding_taps": 0,
    "sounding_recorded": False,
    "sounding_wiped": True,
    "breach_grid": [],
    "breach_pieces": [],
    "breach_selected": None,
    "breach_scrapes_left": 2,
    "deduction_locs": [2, 3, 1, 0],
    "deduction_dmgs": [3, 2, 0, 1],
    "deduction_phase": "deduce",
    "deduction_swap_sel": None,
    "sabotaged_route": "through",
    "parapet_phase": "stairs",
    "stair_step": 0,
    "lantern_open": True,
    "klotski_blocks": [],
    "klotski_selected": None,
    "klotski_slides": 0,
    "smuggle_phase": "contact",
    "tap_step": 0,
    "patrol_earshot": False,
    "smuggle_route": None,
    "transfer_step": 0,
    "transfer_hazard": 0,
    "smuggle_clean_success": False,

    # HORSE
    "riding_horse": False,
    "riding_lessons_completed": 0,
    "last_riding_lesson_day": 0,
    "horse_health": 10,
    "horse_hunger": 100,
    "horse_thirst": 100,
    "horse_shoe_durability": 0,
    "rosinante_feed_count": 0,
    "rosinante_last_fed_day": 0,
    "rosinante_fed": False,
    "horse_stabled": False,
    "horse_stabled_day": 0,
    "horse_sold_for_debt": False,
    "afflictions": [],
    "fresh_food_timestamps": {},
    "banked_silver": 0,
    "casino_chips": 0,

    # QUESTS
    "active_mayor_task": None,
    "mayor_task_deadline": 0,
    "hopestill_revealed": False,
    "spoken_to_hopestill": False,
    "wallmakers_quest_active": False,
    "wallmakers_meeting_day": 0,
    "hopestill_angry": False,
    "active_stable_task": None,
    "stable_task_deadline": 0,
    "active_blacksmith_task": None,
    "active_market_task": None,

    # UI & ARCADE STATE
    "forest_spin": 0,
    "robber_compass_obtained": False,
    "forest_tile_allegiance": {},
    "active_enemy": None,
    "selected_verb": None,
    "chapter_2_unlocked": False,
    "arcade_mode": False,
    "high_scores": {
        "forge": 0,
        "jigsaw": 0,
        "chase": 0,
        "flytip": 0,
        "parapet": 0,
        "smuggle": 0,
        "recipe": 0,
        "sounding": 0,
        "archery": 0,
    },
}

# =========================================================================
# 2. PYGAME SETUP, SMOOTH FULLSCREEN SCALING & UI CONSTANTS
# =========================================================================
os.environ["SDL_RENDER_SCALE_QUALITY"] = "2"  # Crisp anisotropic/bilinear scaling
pygame.init()

WIDTH, HEIGHT = 800, 600
display_screen = pygame.display.set_mode((WIDTH, HEIGHT))
screen = pygame.Surface((WIDTH, HEIGHT)).convert()  # Logical 800x600 canvas
is_fullscreen = False
fs_scale = 1.0
fs_offset_x = 0
fs_offset_y = 0


def toggle_fullscreen():
    """Toggles between 800x600 Windowed mode and crisp native-resolution Fullscreen."""
    global display_screen, is_fullscreen, fs_scale, fs_offset_x, fs_offset_y
    if sys.platform == "emscripten":
        return
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        display_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        dw, dh = display_screen.get_size()
        fs_scale = min(dw / float(WIDTH), dh / float(HEIGHT))
        fs_offset_x = int((dw - WIDTH * fs_scale) // 2)
        fs_offset_y = int((dh - HEIGHT * fs_scale) // 2)
    else:
        display_screen = pygame.display.set_mode((WIDTH, HEIGHT))
        fs_scale = 1.0
        fs_offset_x = 0
        fs_offset_y = 0

def get_logical_mouse_pos():
    """Returns mouse coordinates guaranteed to be mapped to the 800x600 canvas."""
    mx, my = pygame.mouse.get_pos()
    win_w, win_h = pygame.display.get_window_size()
    if win_w > 0 and win_h > 0 and (win_w != 800 or win_h != 600) and not is_fullscreen:
        return int(mx * 800 / win_w), int(my * 600 / win_h)
    return mx, my

def to_logical_pos(pos):
    """Maps physical monitor mouse coordinates back to the 800x600 logical canvas."""
    if not is_fullscreen:
        return pos
    lx = int((pos[0] - fs_offset_x) / fs_scale)
    ly = int((pos[1] - fs_offset_y) / fs_scale)
    return (max(0, min(WIDTH - 1, lx)), max(0, min(HEIGHT - 1, ly)))


def present_screen():
    """Blits the 800x600 logical canvas to the window or smooth-scaled fullscreen display."""
    if not is_fullscreen:
        display_screen.blit(screen, (0, 0))
    else:
        display_screen.fill((12, 14, 18))
        scaled_w = int(WIDTH * fs_scale)
        scaled_h = int(HEIGHT * fs_scale)
        scaled_surf = pygame.transform.smoothscale(screen, (scaled_w, scaled_h))
        display_screen.blit(scaled_surf, (fs_offset_x, fs_offset_y))
    pygame.display.flip()

pygame.display.set_caption("Dtessera Terra")
clock = pygame.time.Clock()

# Use crisp anti-aliased system serif/sans fonts instead of Pygame's blocky bitmap font
FONT = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 16)
FONT_BOLD = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 16, bold=True)
TITLE_FONT = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 21, bold=True)

BG_COLOR = (24, 28, 36)
PANEL_BG = (35, 42, 54)
PANEL_BORDER = (55, 65, 81)
BTN_BG = (45, 55, 72)
BTN_HOVER = (66, 84, 112)
TEXT_COLOR = (240, 240, 240)
TEXT_MUTED = (160, 174, 192)
LOCATION_ACCENT = (240, 180, 120)

# =========================================================================
# 3. UI STATE MANAGEMENT
# =========================================================================
menu_state = "START_SCREEN"
selected_target = None
selected_verb = None
log_history = []

dpad_mode = "travel"        # "travel" or "look"
active_map_key = "murum town map"
look_last_dir = None        # Tracks last compass direction clicked in Look mode
look_current_dist = 0       # Tracks how many squares out the player is currently peering

# --- CHAPTER 3 TACTICAL MAP CAMERA ---
ch3_cam_x = 0
ch3_cam_y = 0
ch3_zoom = 48  # Starting tile size (48 pixels is nice and chunky)
ch3_is_panning = False
ch3_pan_start_pos = (0, 0)
ch3_selected_army_pos = None  # Tracks the (map_x, map_y) of the selected chit

loc_typewriter_idx = 0
log_typewriter_idx = 0

def add_log(message):
    if message:
        log_history.append(str(message))
        try:
            log_panel_ui.force_scroll_to_bottom()
        except NameError:
            pass

def set_state(new_state, log_msg=None):
    global menu_state
    menu_state = new_state
    if log_msg:
        add_log(log_msg)

# =========================================================================
# 4. SAVE / LOAD, CHECKPOINTS & PLAYTEST EXPORTER
# =========================================================================
SAVE_FILE = "savegame.json"

INITIAL_PLAYER_TEMPLATE = copy.deepcopy(player)
INITIAL_NPC_LOCATIONS = {k: v.get("location") for k, v in db.npc_database.items()}
INITIAL_READABLES_DB = copy.deepcopy(db.readables_database)
INITIAL_WORLD_OBJECTS = {pos: list(loc.objects) for pos, loc in world_map.items()}
morning_checkpoint = None

def create_morning_checkpoint():
    """Saves an in-memory snapshot each morning so players can retry the day on death."""
    global morning_checkpoint
    morning_checkpoint = {
        "player": copy.deepcopy(player),
        "npc_locations": {k: v.get("location") for k, v in db.npc_database.items()}
    }

def _restore_npc_locations(loc_dict):
    for k, loc in loc_dict.items():
        if k in db.npc_database:
            if isinstance(loc, list) and len(loc) == 2 and isinstance(loc[0], int):
                db.npc_database[k]["location"] = tuple(loc)
            elif isinstance(loc, list):
                db.npc_database[k]["location"] = [
                    tuple(item) if isinstance(item, list) and len(item) == 2 and isinstance(item[0], int) else item
                    for item in loc
                ]
            else:
                db.npc_database[k]["location"] = loc

def save_game_to_disk(slot_file=SAVE_FILE):
    """Saves the current player state, active menu screen, and NPC locations."""
    if menu_state in (
        "CH3_MORNING_PHASE",
        "CH3_AFTERNOON_PHASE",
        "CH3_EVENING_PHASE",
        "CHAPTER_2_COMPLETE",
    ):
        player["saved_menu_state"] = menu_state
    else:
        player["saved_menu_state"] = "MAIN"

    clean_player = {
        k: v
        for k, v in player.items()
        if not k.endswith("_rect")
        and not k.endswith("_rects")
        and k
        not in (
            "ch3_hover_zones",
            "ch3_hovered_details",
            "ch3_morning_dice",
            "ch3_morning_slots",
        )
    }

    data = {
        "player": clean_player,
        "npc_locations": {
            k: v.get("location") for k, v in db.npc_database.items()
        },
    }
    try:
        with open(slot_file, "w", encoding="utf-8") as file_obj:
            json.dump(data, file_obj, indent=2)
        add_log(
            f"*** Game saved successfully to {slot_file}! (Shortcut: F5) ***"
        )
        return True
    except OSError as err:
        add_log(f"*** Save failed: {err} ***")
        return False

def load_game_from_disk(slot_file=SAVE_FILE):
    """Loads a saved game from disk and restores the exact Chapter 1/2/3 screen."""
    global player, loc_typewriter_idx
    if not os.path.exists(slot_file):
        add_log(f"*** No saved game file ({slot_file}) found! ***")
        return False
    try:
        with open(slot_file, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
        if "player" in data:
            player.clear()
            player.update(data["player"])
            _restore_npc_locations(data.get("npc_locations", {}))
        elif "player_state" in data:
            player.clear()
            player.update(data["player_state"])
            npc_locs = {
                k: v.get("location")
                for k, v in data.get("npc_state", {}).items()
            }
            _restore_npc_locations(npc_locs)
        loc_typewriter_idx = 0
        location_panel_ui.scroll_y = 0
        restored_state = player.get("saved_menu_state", "MAIN")
        if (
            restored_state == "CH3_MORNING_PHASE"
            and not player.get("ch3_morning_dice")
        ):
            player = ui_renderer.init_ch3_morning_phase(player)
        set_state(
            restored_state,
            "*** Saved game loaded successfully! (Shortcut: F9) ***",
        )
        return True
    except (OSError, ValueError) as err:
        add_log(f"*** Load failed: {err} ***")
        return False

def save_state():
    save_game_to_disk(SAVE_FILE)

def load_state():
    load_game_from_disk(SAVE_FILE)

def retry_from_morning():
    global player, loc_typewriter_idx
    if morning_checkpoint is None:
        restart_new_game()
        return
    player.clear()
    player.update(copy.deepcopy(morning_checkpoint["player"]))
    _restore_npc_locations(morning_checkpoint["npc_locations"])
    loc_typewriter_idx = 0
    location_panel_ui.scroll_y = 0
    set_state("MAIN", "*** You wake with a start—it was only a nightmare. (Restored to Morning Checkpoint!) ***")

def restart_new_game():
    global player, loc_typewriter_idx, dpad_mode, look_last_dir, look_current_dist
    player.clear()
    player.update(copy.deepcopy(INITIAL_PLAYER_TEMPLATE))
    _restore_npc_locations(INITIAL_NPC_LOCATIONS)
    db.readables_database = copy.deepcopy(INITIAL_READABLES_DB)
    for pos, objs in INITIAL_WORLD_OBJECTS.items():
        world_map[pos].objects = list(objs)
    dpad_mode = "travel"
    look_last_dir = None
    look_current_dist = 0
    retro_dpad.mode_label = "MOVE"
    loc_typewriter_idx = 0
    log_history.clear()
    create_morning_checkpoint()
    player["ch3_prev_modal_state"] = "START_SCREEN"
    set_state("PNP_LOBBY_MODAL")

def export_playtest_report(outcome_title):
    return build_playtest_report(player, outcome_title)

# =========================================================================
# 5. GAME LOGIC CALLBACKS
# =========================================================================
def check_master_clock():
    global player
    time_tick_occurred = False

    # 1. Check Fresh Food Spoilage & Stabling Debt Foreclosure (>20s)
    spoil_msg = process_food_spoilage(player)
    if spoil_msg:
        add_log(spoil_msg)

    foreclose_msg = check_stabling_foreclosure(player)
    if foreclose_msg:
        add_log(foreclose_msg)

    # 2. 100-Minute Survival, Healing & Illness Tick
    while player["total_game_minutes"] - player["last_heal_minute"] >= 100:
        time_tick_occurred = True
        player["last_heal_minute"] += 100
        minutes_awake = player["last_heal_minute"] - player["last_sleep_minute"]
        affs = player.get("afflictions", [])

        if minutes_awake > 1000:
            player["health"] -= 1
            player["strength"] -= 1
            add_log("*** Exhaustion takes its toll! (-1 Health, -1 Strength) ***")
            # Working through the night in the damp Brumaire mist risks catching the Damp-Chill!
            if random.random() < 0.25:
                chill_msg = infect_player(player, "damp_chill")
                if chill_msg:
                    add_log(chill_msg)
        else:
            if player["strength"] < 0 and "damp_chill" not in affs:
                player["strength"] += 1
            # Natural healing ONLY occurs when well-fed, hydrated, and free of illness/poison!
            if not affs and player["health"] < player["max_health"] and player["hunger"] > 0 and player["thirst"] > 0:
                player["health"] += 1

        # Active Affliction Health Drain (1 HP per 100 mins; remedies stop this drain)
        if affs:
            for aff_key in list(affs):
                info = AFFLICTION_INFO.get(aff_key)
                if info:
                    player["health"] -= 1
                    add_log(f"*** [{info['name'].upper()}] {info['symptom']} ***")

        if player["hunger"] <= 0:
            player["health"] -= 1
            add_log("*** You are starving! (-1 Health) ***")
        if player["thirst"] <= 0:
            player["health"] -= 1
            add_log("*** You are dehydrated! (-1 Health) ***")

    if time_tick_occurred:
        add_log(f"*** Time passes... it is now {get_time_string(player['total_game_minutes'])} ***")

    # 3. Quest Deadline Checkers
    if player["wallmakers_quest_active"]:
        current_day = (player["total_game_minutes"] // 1000) + 1
        time_of_day = player["total_game_minutes"] % 1000
        if current_day > player["wallmakers_meeting_day"] or (current_day == player["wallmakers_meeting_day"] and time_of_day >= 500):
            player["wallmakers_quest_active"] = False
            player["hopestill_angry"] = True
            db.npc_database["hopestill"]["location"] = "tavern"
            player["faction_wallmakers"] = max(-10, player["faction_wallmakers"] - 5)
            add_log(f"*** You missed your Wallmakers meeting! (-2 Faction, Total: {player['faction_wallmakers']}) ***")

    if player["active_mayor_task"] and player["total_game_minutes"] > player["mayor_task_deadline"]:
        player["current_job"] = None
        player["current_tenure"] = 0
        player["active_mayor_task"] = None
        player["reputation"] -= 2

        for item in [
            "mayor's outgoing letters", "mayor's incoming post", "mayor's horse letter",
            "blacksmith's horse report", "mayor's dinner letter", "butter", "flu medicine",
            "mayor's birthday cake", "sack of coal", "mayor's stallion", "mayor's shod stallion",
            "watered stallion", "fed and watered stallion", "mayor's seal"
        ]:
            if item in player["inventory"]:
                player["inventory"].remove(item)

        db.npc_database["mayor"]["location"] = None
        if player["current_building"] == "mayor's house":
            player["current_building"] = None
        add_log("*** YOU MISSED YOUR DEADLINE! You have been fired from the Mayor's House! (-2 Reputation) ***")

    if player.get("active_blacksmith_task") == "mercenary_duel":
        current_day = (player["total_game_minutes"] // 1000) + 1
        time_of_day = player["total_game_minutes"] % 1000

        if current_day > player.get("duel_day", 0) or (current_day == player.get("duel_day", 0) and time_of_day > 475):
            player["active_blacksmith_task"] = None
            db.npc_database["mercenary"]["location"] = None
            player["reputation"] -= 3
            player["blacksmith_shifts_completed"] += 1
            player = mark_shift_completed(player)
            add_log("*** You missed your duel! You are branded a coward! (-3 Reputation) ***")

    # Disarm weapons at The House of Games cloakroom
    if player.get("current_building") in ("casino", "the house of games", "house of games"):
        if player.get("equipped_weapon", "fists") != "fists":
            player["inventory"].append(player["equipped_weapon"])
            player["equipped_weapon"] = "fists"
            add_log("*** The House of Games Cloakroom attendant politely checks your weapon at the door. You are now unarmed. ***")

    # Check if the 3-day 60s House of Games Loan is overdue
    due_min = player.get("casino_loan_due_min")
    if player.get("casino_loan_owed", 0) > 0 and due_min is not None:
        if player.get("total_game_minutes", 0) >= due_min and menu_state == "MAIN":
            player, log_msg, next_state = encounters.trigger_casino_enforcer_combat(player, reason="loan")
            set_state(next_state, log_msg)
            return

    if player["health"] <= 0:
        set_state("DEAD", "You collapse to the ground, your body completely broken. Your adventure is over.")

# --- EXPLORATION & D-PAD LOOK / TRAVEL TOGGLE ---
def toggle_dpad_mode():
    global dpad_mode, look_last_dir, look_current_dist
    dpad_mode = "look" if dpad_mode == "travel" else "travel"
    look_last_dir = None
    look_current_dist = 0
    retro_dpad.mode_label = "LOOK" if dpad_mode == "look" else "MOVE"

    if dpad_mode == "look":
        max_range, best_scope = get_player_look_range(player)
        if best_scope:
            add_log(
                f"*** D-Pad switched to LOOK MODE (Using {format_item_name(best_scope)}: "
                f"Range up to {max_range} squares — click a direction repeatedly to peer further!) ***"
            )
        else:
            add_log("*** D-Pad switched to LOOK MODE (Naked Eye: Range 1 square ahead) ***")
    else:
        add_log("*** D-Pad switched to TRAVEL MODE ***")


def action_look_direction(dx, dy, dir_name):
    global look_last_dir, look_current_dist

    if player["current_building"]:
        b_name = db.building_database[player["current_building"]]["name"]
        add_log(f"You are inside {b_name}. Exit the building first to scan the surrounding horizon.")
        return

    max_range, best_scope = get_player_look_range(player)

    if look_last_dir == (dx, dy) and max_range > 1:
        look_current_dist += 1
        if look_current_dist > max_range:
            look_current_dist = 1
    else:
        look_last_dir = (dx, dy)
        look_current_dist = 1

    standing_room = world_map.get((player["x"], player["y"]))
    on_high_ground = standing_room and ("Wall" in standing_room.name or "Mountain" in standing_room.region)

    for step in range(1, look_current_dist):
        mid_pos = (player["x"] + dx * step, player["y"] + dy * step)
        mid_room = world_map.get(mid_pos)
        if mid_room and not on_high_ground:
            if mid_room.name == "The Town Wall" or "Mountain" in mid_room.region:
                add_log(
                    f"--- LOOK {dir_name.upper()} ({look_current_dist} squares) ---\n"
                    f"Your line of sight beyond {step} square(s) is blocked by {mid_room.name}!"
                )
                return

    look_x = player["x"] + (dx * look_current_dist)
    look_y = player["y"] + (dy * look_current_dist)
    look_pos = (look_x, look_y)

    if look_current_dist == 1:
        header = f"--- LOOKING {dir_name.upper()} (1 square ahead) ---"
    else:
        scope_title = format_item_name(best_scope) if best_scope else "Scope"
        header = f"--- LOOKING {dir_name.upper()} ({look_current_dist}/{max_range} squares via {scope_title}) ---"

    if look_pos in world_map:
        seen_loc = world_map[look_pos]
        owner = get_tile_territory(player, look_x, look_y)
        terr_str = f" [{owner} Territory]" if owner else ""
        msg = f"{header}\nYou see: {seen_loc.name} ({seen_loc.region}){terr_str}.\n{seen_loc.description}"

        npcs_there = [
            info["proper_name"]
            for npc_id, info in db.npc_database.items()
            if info["location"] == look_pos or (isinstance(info["location"], list) and look_pos in info["location"])
        ]
        if npcs_there:
            msg += f"\nFigures spotted: {', '.join(npcs_there)}"
        add_log(msg)
    else:
        add_log(f"{header}\nLooking {dir_name.lower()}, you see nothing but the unmapped horizon.")


def handle_dpad_click(dx, dy, dir_name):
    if dpad_mode == "look":
        action_look_direction(dx, dy, dir_name)
    else:
        action_move(dx, dy, dir_name)


def action_move(dx, dy, dir_name):
    global player, loc_typewriter_idx, log_typewriter_idx, look_last_dir, look_current_dist

    if player["current_building"]:
        add_log("You cannot travel from here. You must 'Exit' the building first.")
        return

    look_last_dir = None
    look_current_dist = 0

    # --- FOREST DISORIENTATION: SPIN D-PAD ON EVERY STEP WITHOUT COMPASS ---
    current_pos = (player["x"], player["y"])
    if (
        current_pos in world_map
        and world_map[current_pos].region == "The Forest"
        and "compass" not in player["inventory"]
    ):
        compass_ring = [
            (0, 1, "North"), (1, 1, "North-East"), (1, 0, "East"), (1, -1, "South-East"),
            (0, -1, "South"), (-1, -1, "South-West"), (-1, 0, "West"), (-1, 1, "North-West")
        ]
        spin_offset = random.randint(0, 7)
        player["forest_spin"] = spin_offset
        retro_dpad.trigger_spin()
        for idx, (cx, cy, _) in enumerate(compass_ring):
            if (cx, cy) == (dx, dy):
                dx, dy, dir_name = compass_ring[(idx + spin_offset) % 8]
                break

    target_x = player["x"] + dx
    target_y = player["y"] + dy
    target_pos = (target_x, target_y)

    if target_pos not in world_map:
        add_log("*** You have reached the edge of the mapped world. ***")
        return

    target_room = world_map[target_pos]
    current_room = world_map[(player["x"], player["y"])]
    escort_msg = companions_engine.check_companion_destination_arrival(player)
    if escort_msg:
        add_log(escort_msg)

    # --- WALL & MOUNTAIN MOVEMENT CHECKS ---
    wall_walk_msg = None
    if current_room.name == "The Town Wall":
        if target_room.name == "The Town Wall":
            # Walking along the stone ramparts: roll 1d6 + Strength (or fall off!)
            player, final_pos, wall_walk_msg = resolve_wall_walk(player, world_map, target_pos)
            target_pos = final_pos
            target_x, target_y = target_pos
            target_room = world_map[target_pos]
        else:
            add_log("You are high up on the stone ramparts! Walk along the wall, or use 'Action -> Climb' to climb down.")
            return
    elif target_room.name in ["The Town Wall", "Mountain"] and not (target_room.name == "Mountain" and player.get("riding_mouflin")):
        add_log(f"A towering {target_room.name} blocks your path. You must use the 'Climb' action to scale it (or ride a tamed Mouflin in the mountains).")
        return

    # Dynamic Terrain & Territory Access Check
    allowed, terr_event, terr_msg = check_territory_and_terrain_access(player, target_x, target_y, target_room)
    if not allowed:
        add_log(terr_msg)
        return

    # Weather Check
    can_pass, override_pos, weather_extra_mins, weather_move_msg = weather_engine.check_movement_weather_and_swim(
        player, target_x, target_y, world_map
    )
    if not can_pass:
        add_log(weather_move_msg)
        return
    if override_pos:
        target_x, target_y = override_pos
        target_pos = (target_x, target_y)
    if weather_extra_mins > 0:
        player, w_time_msg = advance_time(weather_extra_mins, player)
        if w_time_msg:
            add_log(w_time_msg)
    if weather_move_msg:
        add_log(weather_move_msg)

    # Move Success
    player["prev_x"], player["prev_y"] = player["x"], player["y"]
    player["x"], player["y"] = target_pos
    log_history.clear()
    location_panel_ui.scroll_y = 0
    loc_typewriter_idx = 0
    log_typewriter_idx = 0

    if wall_walk_msg:
        add_log(wall_walk_msg)
    if terr_msg:
        add_log(terr_msg)

    # Auto-Dismount in Town
    if player["riding_horse"] and "Town" in target_room.region:
        add_log("You climb down from the saddle. Town streets are too crowded to ride.")
        player["riding_horse"] = False

    # Hostile Territory Interception (Off-road in rival faction turf)
    if terr_event and terr_event.startswith("HOSTILE_TERRITORY_"):
        owner_name = terr_event.replace("HOSTILE_TERRITORY_", "").title()
        if random.randint(1, 2) == 1:
            player, log_msg, next_state = encounters.trigger_territory_encounter(player, owner_name)
            set_state(next_state, log_msg)
            return
    
    # --- CHAPTER 2 WILDERNESS TRIAL TRIGGERS ---
    ch2_triggered, ch2_log, ch2_state = chapter_2.check_chapter_2_move_triggers(player, target_pos, target_room)
    if ch2_triggered:
        player, t_log = advance_time(15 if player["riding_horse"] else 50, player)
        if t_log:
            add_log(t_log)
        check_master_clock()
        if menu_state != "DEAD":
            set_state(ch2_state, ch2_log)
        return

    # Ambush: Wallmakers Retribution
    if "Town" in target_room.region and player["wallmakers_reported"] and player["faction_wallmakers"] == -10:
        if random.randint(1, 15) == 1:
            player, log_msg, next_state = encounters.trigger_thug_encounter(player)
            set_state(next_state, log_msg)
            return

    # --- LIGNUM FOREST: COMPASS CHECK, 1/3 KIDNAPPING & 50/50 ANIMAL SCHISM ---
    if target_room.region == "The Forest":
        if "compass" not in player["inventory"]:
            retro_dpad.trigger_spin()
            add_log(
                "The dense canopy of Lignum Forest blots out the sun and every gnarled trunk looks identical—"
                "your sense of direction spins wildly!"
            )
        elif current_room.region != "The Forest":
            add_log(
                "Beneath the dark forest canopy, you flip open your Brass Compass, steady the needle, and hold true to your bearings."
            )

        # 1-in-3 Chance of Vanguardist Forest Interception (Kidnaps ONLY once!)
        if (
            random.randint(1, 3) == 1
            and target_pos != (19, 19)
            and not ch2_easter_eggs.has_forest_wayfinder(player)
        ):
            was_kidnapped, kidnap_log, k_state = (
                ch2_easter_eggs.resolve_vanguard_forest_intercept(player)
            )
            if was_kidnapped:
                player["prev_x"], player["prev_y"] = target_pos
                player["x"], player["y"] = (19, 19)
                k_state = "MENU_FOREST_KIDNAP"
            player, t_log = advance_time(50, player)
            if t_log:
                kidnap_log += "\n" + t_log
            check_master_clock()
            if menu_state != "DEAD":
                set_state(k_state, kidnap_log)
            return

        # If not kidnapped, check if one of the 4 Forest Animal groups inhabits this tile (50% of tiles)
        forest_npcs_here = [
            npc_id for npc_id in ("forest owls", "forest squirrels", "forest deer", "forest armadillo")
            if target_pos in db.npc_database.get(npc_id, {}).get("location", [])
        ]
        if forest_npcs_here:
            animal_id = forest_npcs_here[0]
            animal_name = db.npc_database[animal_id]["proper_name"]
            pos_key = f"{target_x},{target_y}"
            allegiance_map = player.setdefault("forest_tile_allegiance", {})
            if pos_key not in allegiance_map:
                # 50/50 Chance of Vanguardist (Violent) vs. Communard (Peaceful)!
                allegiance_map[pos_key] = random.choice(["vanguardist", "communard"])

            allegiance = allegiance_map[pos_key]
            if allegiance == "vanguardist":
                player.setdefault("territories", {})[pos_key] = "Vanguardists"
                if player.get("faction_vanguardists", 0) >= 5:
                    add_log(f"{animal_name} (Vanguardists) recognize you as an ally of the forest defence and let you pass.")
                else:
                    player, t_log = advance_time(50, player)
                    if t_log:
                        add_log(t_log)
                    check_master_clock()
                    if menu_state != "DEAD":
                        player, c_log, next_state = encounters.trigger_forest_animal_combat(player, animal_id)
                        set_state(next_state, c_log)
                    return
            else:
                player.setdefault("territories", {})[pos_key] = "Communards"
                add_log(
                    f"Among the trees, {animal_name} watch you with gentle curiosity—they belong to the peaceful **Communards** of the Great Schism. "
                    "(Use 'Action -> Talk' to commune with them!)"
                )

    # --- WEIGHT & ENCUMBRANCE CALCULATION ---
    curr_w = get_inventory_weight(player)
    max_w = get_max_carry_weight(player)
    weight_mult = 1.0
    extra_drain = 0

    if not player.get("riding_horse"):
        if curr_w > max_w + 15.0:
            weight_mult = 2.0
            extra_drain = 4
        elif curr_w > max_w:
            weight_mult = 1.5
            extra_drain = 2

    # --- TRAVEL TIME ---
    # Moving through rough wilderness takes 90 minutes per tile on foot!
    if player["riding_horse"]:
        if player["horse_shoe_durability"] > 0:
            player, t_log = advance_time(25, player)
            player["horse_shoe_durability"] -= random.randint(0, 2)
            if player["horse_shoe_durability"] <= 0:
                add_log("*** CLANG! Your horse throws a shoe. Return to the Blacksmith! ***")
                player["horse_shoe_durability"] = 0
        else:
            player, t_log = advance_time(45, player)
    else:
        # 15 mins for town tiles, 90 mins for wilderness!
        base_mins = 15 if "Town" in target_room.region else 90
        mins = int(round(base_mins * weight_mult))
        player, t_log = advance_time(mins, player)

    if t_log:
        add_log(t_log)

    if extra_drain > 0:
        player["hunger"] = max(0, player["hunger"] - extra_drain)
        player["thirst"] = max(0, player["thirst"] - extra_drain)
        add_log(
            f"*** Your heavy pack ({curr_w}/{max_w} lbs) slows your pace and drains your stamina! "
            f"(-{extra_drain} Hunger/Thirst) ***"
        )

    # --- MARKET SHIFT 2: SHORTEST-PATH POSTIE INTERCEPTION ---
    if player.get("active_market_task") == "intercept_postie":
        elapsed = player["total_game_minutes"] - player.get("postie_start_time", 0)
        postie_schedule = {
            (7, 15): (-20, "Murum Stables"),
            (7, 14): (-6, "Murum Guard House"),
            (8, 14): (8, "The School"),
            (9, 14): (22, "Murum Playhouse"),
            (10, 14): (36, "The Wallmakers' Office"),
            (11, 14): (50, "The Blacksmiths"),
            (11, 15): (64, "Union House"),
            (10, 16): (78, "Murum Town Hall"),
            (9, 16): (92, "The Dog and Duck Pub"),
            (8, 16): (106, "Murum Post Office")
        }

        if target_pos == (11, 14) and elapsed == 50:
            db.npc_database["postie"]["location"] = [(11, 14), "blacksmiths"]
            add_log(
                "*** [50m elapsed] PERFECT INTERCEPTION! Just as you reach The Blacksmiths, "
                "Fleetfoot the Postie arrives! Use 'Action -> Talk' to collect the parcel! ***"
            )
        else:
            db.npc_database["postie"]["location"] = None
            if target_pos in postie_schedule:
                p_time, stop_name = postie_schedule[target_pos]
                if elapsed > p_time:
                    add_log(f"*** [{elapsed}m elapsed] You reach {stop_name}, but Fleetfoot the Postie already passed here {elapsed - p_time} minutes ago! ***")
                elif elapsed < p_time:
                    add_log(f"*** [{elapsed}m elapsed] You reach {stop_name}, but Fleetfoot won't arrive here for another {p_time - elapsed} minutes! ***")

            if elapsed > 50:
                add_log(
                    "*** Over 50 minutes have elapsed—you missed the exact interception point! "
                    "Return to the Post Office and speak to the Postmaster to try the next mail run. ***"
                )

    check_master_clock()
    if menu_state == "DEAD":
        return

    # Guard Patrol Check (After moving)
    if player["reputation"] < 0:
        eff_rep = max(0, abs(player["reputation"]) - player["stealth"])
        if eff_rep > 0:
            base = 1/3 if "Town" in target_room.region else (1/6 if any(k in target_room.region for k in ["Road", "Path"]) else 0)
            if random.random() < (base * (1.0 + (0.2 * eff_rep))):
                player, log_msg, next_state = encounters.trigger_guard_encounter(player)
                set_state(next_state, log_msg)
                return

    # --- AMBUSH: HIGHWAY ROBBERS (Forced Compass Drop!) ---
    if target_room.region == "The New Road":
        # If the player doesn't have a compass yet, FORCE the ambush on a 1-in-3 chance regardless of skills/mounts!
        needs_compass = ("compass" not in player["inventory"] and not player.get("robber_compass_obtained"))
        
        if needs_compass and random.randint(1, 3) == 1:
            player, log_msg, next_state = encounters.trigger_robber_encounter(player)
            set_state(next_state, log_msg)
            return
            
        elif not needs_compass:
            if "safe travel" in player["skills"]:
                if random.randint(1, 4) == 1:
                    add_log("Your safe travel skills keep highwaymen at bay.")
            else:
                roll = random.randint(1, 6)
                if (not player["riding_horse"] and roll <= 2) or (player["riding_horse"] and roll == 1):
                    player, log_msg, next_state = encounters.trigger_robber_encounter(player)
                    set_state(next_state, log_msg)
                    return
                elif player["riding_horse"] and random.randint(1, 3) == 1:
                    add_log("You hear rustling, but your swift mount carries you safely past.")

    # Contraband Stop-and-Search Check
    if (
        "bundle of radical pamphlets" in player["inventory"]
        and player.get("active_market_task") not in ["sweep_contraband", "hand_contraband_to_guard"]
        and "Town" in target_room.region
    ):
        if random.randint(1, 5) == 1:
            player["inventory"].remove("bundle of radical pamphlets")
            player["reputation"] -= 3
            player["faction_guard"] -= 3
            player, log_msg, next_state = encounters.trigger_guard_encounter(player)
            contraband_log = (
                "*** RANDOM STOP AND SEARCH! ***\n"
                "A town guard patrol stops you in the street and searches your coat!\n"
                "\"What's this?! Banned anarchist pamphlets?! You're under arrest for sedition!\"\n"
                "The guard confiscates the pamphlets! (-3 Reputation, -3 Guard Faction)\n\n"
            ) + log_msg
            set_state(next_state, contraband_log)

def action_mount_dismount(animal="horse"):
    global player
    player, msg = mount_dismount_helper(player, world_map, animal)
    if msg:
        add_log(msg)
    set_state("MAIN")


def action_climb(target_name, dx=0, dy=0, mode="up"):
    global player, loc_typewriter_idx
    if dx != 0 or dy != 0:
        player, moved, msg = resolve_wall_climb(player, world_map, target_name, dx, dy, mode=mode)
        if moved:
            loc_typewriter_idx = 0
            location_panel_ui.scroll_y = 0
        add_log(msg)
    else:
        add_log(f"You climb the {target_name}.")
    set_state("MAIN")
    check_master_clock()

def action_camp():
    global player
    current_loc = world_map.get((player["x"], player["y"]))

    if player["current_building"]:
        if player["current_building"] in ["tavern", "dog and duck pub"]:
            has_free_room = (
                not player.get("free_room_used", False)
                and (player["market_sweeper_shifts"] > 0 or player["blacksmith_shifts_completed"] > 0 or player["stable_shifts"] > 0)
            )
            if has_free_room:
                player["free_room_used"] = True
                add_log("You mention who sent you. The owner smiles and gives you a room key on the house!")
                set_state("SLEEP_MENU")
            elif player["silver"] >= 2:
                player["silver"] -= 2
                add_log("You pay 2 silver to the innkeeper and head upstairs to a warm bed.")
                set_state("SLEEP_MENU")
            else:
                add_log("You need 2 silver to rent a room here (or you can speak to the owner).")
                set_state("MAIN")
        elif player["current_building"] in ["mayor's house", "mayor's staff entrance"] and player["current_job"] == "mayor's house":
            add_log("You head down to the servants' quarters to rest in your provided cot.")
            set_state("SLEEP_MENU")
        else:
            b_name = db.building_database[player["current_building"]]["name"]
            add_log(f"You cannot camp or sleep inside {b_name}!")
            set_state("MAIN")

    elif current_loc and any(kw in current_loc.region for kw in ["Town", "Castle", "River", "Lake", "Sea"]):
        add_log(f"You cannot pitch a tent here in {current_loc.region}. Find an inn or head into the open wilderness.")
        set_state("MAIN")

    elif "tent" in player["inventory"]:
        import companions_engine
        reg = current_loc.region if current_loc else "the wilderness"
        camp_intro = (
            f"You find a sheltered spot on dry ground in {reg}, unroll your heavy canvas tent, "
            "and drive the wooden pegs tight against the Brumaire wind.\n"
            "A small ring of stones shields your camp-ember as the wilderness settles around you. How long will you rest?"
            + companions_engine.get_companion_campfire_banter(player)
        )
        set_state("SLEEP_MENU", camp_intro)
    else:
        add_log("You cannot sleep here. You need a tent to camp in the wilderness, or a bed at an inn.")
        set_state("MAIN")

def execute_sleep(duration_type):
    global player
    if duration_type == "nap":
        player, sleep_log = handle_sleep_nap(player)
        add_log(sleep_log)
    else:
        # duration_type can be "morning_200", "morning_250", "morning_300", "morning_375", or "morning"
        wake_map = {
            "morning_200": 200,
            "morning_250": 250,
            "morning_300": 300,
            "morning_375": 375,
            "morning": 300,
        }
        target_hr = wake_map.get(duration_type, 300)
        player, sleep_log = handle_sleep_morning(player, target_wake_time=target_hr)
        add_log(sleep_log)
        if player.get("current_building") in ["tavern", "dog and duck pub", "barge and anchor", "salted anchor", "mayor's house", "mayor's staff entrance"]:
            player["hunger"] = 100
            player["thirst"] = 100
            player["last_sustenance_tick"] = player["total_game_minutes"]
            add_log("*** You wake up to a hearty breakfast! (Hunger/Thirst restored) ***")
        create_morning_checkpoint()

    set_state("MAIN")
    check_master_clock()

def action_equip(item_key):
    global player
    player, msg = equip_item_helper(player, item_key)
    if selected_target == "torch":
        player["inventory"].remove("torch")
        player["torch_minutes_left"] = player.get("torch_minutes_left", 0) + 300
        set_state("MAIN", "You strike flint and steel, lighting a resin-soaked pine torch (+300 decimal minutes of light & warmth)!")
        return
    if msg:
        add_log(msg)
    set_state("MAIN")

def action_consume(item):
    global player
    player, msg = consume_item_helper(player, item)
    if msg:
        add_log(msg)

USABLE_ITEM_KEYS = {
    "torch", "storm lantern", "topographic survey map", "dtessera terra world map", "murum town map",
    "career ledger", "codewheel", "bandoka's cipher", "deck of cards",
    "portable printing press", "oak press-frame", "iron screw-spindle", "lead type-case",
    "spool of thread", "woodland drum", "guard uniform", "kokeshi doll",
    "bone dice", "brass wallmaker dice", "jade kokeshi dice", "obsidian vanguard dice", "star-iron guild dice",
    "vial of nightshade poison", "manual of the iron wrist", "treatise on rhetoric", "shadow-walker's soft-boots",
    "map: calluna crypt", "map: parvus catacombs", "map: old path catacombs", "map: caligo silver mine",
    "tent", "water flask", "compass", "rope", "crowbar", "masonry drill",
}


def get_usable_inventory_items(player):
    """Returns all items in player['inventory'] that can be actively used/operated."""
    inv = player.get("inventory", [])
    out = []
    for item in inv:
        info = db.item_database.get(item, {})
        if item in USABLE_ITEM_KEYS or info.get("usable") or item.startswith("map:"):
            out.append(item)
    return out


def action_use(item):
    """
    Unified 'Use Item' dispatcher! Handles maps, torches, kits, cryptography tools,
    printing presses, dice, poisons, stat relics, camping gear, and fallbacks.
    """
    global player
    if item not in player.get("inventory", []):
        return

    # 1. Topographic Survey Map vs Plain Maps
    if item == "topographic survey map":
        msg = weather_engine.toggle_topo_map(player)
        set_state("MAIN", msg)
        return
    if item == "dtessera terra world map":
        set_state("MAP_VIEW", "You unroll the Dtessera Terra World Map.")
        return
    if item == "murum town map":
        set_state("MAP_VIEW", "You unfold the Murum Town Map.")
        return
    if item == "career ledger":
        set_state("MINIGAME_TRACK_TABLE", "You open your Surveyor's Career Ledger.")
        return

    # 2. Torch & Storm Lantern
    if item == "torch":
        player["inventory"].remove("torch")
        player["torch_minutes_left"] = player.get("torch_minutes_left", 0) + 300
        set_state("MAIN", "You strike flint and steel, lighting a resin-soaked pine torch (+300 decimal minutes of light & warmth)!")
        return
    if item == "storm lantern":
        set_state("MAIN", "Your brass Storm Lantern is filled with whale-oil and automatically illuminates the night without blowing out in storms!")
        return

    # 3. Tent & Water Flask shortcuts
    if item == "tent":
        action_camp()
        return
    if item == "water flask":
        action_fill_flask()
        return

    # 4. Phase 5 Cryptography, Printing Press, Knotting, Drum & Disguises
    handled_c, c_state, c_msg = cryptography_engine.use_non_fighting_item(item, player, world_map)
    if handled_c:
        set_state(c_state, c_msg)
        check_master_clock()
        return

    # 5. Phase 6 Stylised Dice, Poisons, Stat-Boosting Relics & Dungeon Maps
    handled_d, d_msg = dice_and_charms.handle_phase6_item_use(item, player)
    if handled_d:
        set_state("MAIN", d_msg)
        check_master_clock()
        return

    # 6. Graceful Fallbacks if player clicked Use on Food or a Weapon
    info = db.item_database.get(item, {})
    if any(k in info for k in ("hunger_restore", "thirst_restore", "cures_affliction")):
        action_consume(item)
        set_state("MAIN")
        check_master_clock()
        return
    if item in db.weapon_max_hit:
        player, eq_msg = equip_item_helper(player, item)
        set_state("MAIN", eq_msg)
        return

    set_state("MAIN", f"You inspect the {format_item_name(item)}—it will be used automatically when the situation calls for it.")

def action_drop(item):
    global player
    player, msg = drop_item_helper(player, item)
    if msg:
        add_log(msg)
    set_state("MAIN")

def action_deposit_silver(amount):
    global player
    player, msg = deposit_silver_helper(player, amount)
    add_log(msg)
    set_state("MAIN")

def action_withdraw_silver(amount):
    global player
    player, msg = withdraw_silver_helper(player, amount)
    add_log(msg)
    set_state("MAIN")

def action_stash_item(item):
    global player
    player, msg = stash_item_helper(player, item)
    add_log(msg)
    set_state("MAIN")

def action_retrieve_item(item):
    global player
    player, msg = retrieve_item_helper(player, item)
    add_log(msg)
    set_state("MAIN")

def action_sell_item(item):
    global player
    player, msg = sell_item_helper(player, item)
    add_log(msg)
    set_state("MAIN")

def get_npcs_at_current_location():
    current_loc = player["current_building"] if player["current_building"] else (player["x"], player["y"])
    found = []
    for npc_id, npc_info in db.npc_database.items():
        loc = npc_info["location"]
        is_here = (loc == current_loc) or (isinstance(loc, list) and current_loc in loc)
        if is_here:
            if npc_id == "hopestill" and not player.get("hopestill_revealed"):
                continue
            if not is_npc_relevant_now(npc_id, player):
                continue
            found.append(npc_id)
    return found

CH2_EXCLUSIVE_NPCS = {
    "outrider_bran", "bran", "corban", "bailiff_seekgrace", "seekgrace",
    "mairie_barge", "fleepride", "beornraed", "aldred_foundry", "ronan_rigger",
    "customs_vance", "harbour_kett", "ceolwulf", "huntmaster_voss", "steward_osric",
    "vanguard_rowan", "diewell", "fence_rattler", "crier_bellman", "skipper_omalley",
}

def is_npc_relevant_now(npc_key, player):
    """Hides Chapter 2 operational NPCs (like Outrider Bran) during Chapter 1 unless relevant."""
    n_low = npc_key.lower()
    # Outrider Bran is only relevant if the player is on the Guard / Castellan / Outlaw road missions in Ch.2
    if n_low in ("outrider_bran", "bran"):
        return bool(player.get("chapter_2_route"))
    if n_low in CH2_EXCLUSIVE_NPCS and not player.get("chapter_2_route"):
        return False
    return True

def action_give_gift(npc_key, gift_item):
    global player
    player, msg = give_gift_helper(player, npc_key, gift_item)
    if msg:
        add_log(msg)
    set_state("MAIN")

def get_local_water_source(player, world_map):
    if player["current_building"]:
        return None
    pos = (player["x"], player["y"])
    if pos in world_map:
        room = world_map[pos]
        objs = [o.lower() for o in room.objects]
        if any("fountain" in o for o in objs):
            return "fountain"
        if any("well" in o for o in objs):
            return "well"
        region_lower = room.region.lower()
        name_lower = room.name.lower()
        if "river" in region_lower or "river" in name_lower:
            return "river"
        if "lake" in region_lower:
            return "lake"
        if "sea" in region_lower or "coast" in region_lower:
            return "sea"
    return None

def action_drink(source):
    global player
    player, msg = drink_helper(player, source)
    if msg:
        add_log(msg)
    set_state("MAIN")
    check_master_clock()

def action_fill_flask(source):
    global player
    player, msg = fill_flask_helper(player, source)
    if msg:
        add_log(msg)
    set_state("MAIN")

def action_enter(building_alias):
    global player, loc_typewriter_idx

    b_id = db.building_aliases.get(building_alias.lower(), building_alias.lower())

    if b_id not in db.building_database:
        add_log(f"There is no {building_alias} here.")
        return

    b_info = db.building_database[b_id]

    if player["current_building"] == b_id:
        add_log(f"You are already inside the {b_info['name']}.")
        return

    if b_info["location"] != (player["x"], player["y"]):
        add_log(f"There is no {b_info['name']} here.")
        return

    required_parent = b_info.get("parent")

    if required_parent is not None and player["current_building"] != required_parent:
        parent_name = db.building_database[required_parent]["name"]
        add_log(f"You cannot reach {b_info['name']} from here. You must be inside {parent_name} first.")
        return

    if required_parent is None and player["current_building"] is not None:
        current_name = db.building_database[player["current_building"]]["name"]
        add_log(f"You are currently inside {current_name}. You must 'Exit' first.")
        return

    # --- HORSE INDOORS RESTRICTION ---
    if "horse" in player["inventory"] and b_id not in ["stables", "stable loft", "tack room"]:
        add_log(
            f"You cannot lead your horse inside {b_info['name']}!\n"
            "Take your horse to Murum Stables to stable it first (Fee: 2 silver)."
        )
        return

    # --- THE TIME CHECK ---
    time_of_day = player["total_game_minutes"] % 1000

    if required_parent is not None:
        player["current_building"] = b_id
        loc_typewriter_idx = 0
        add_log(f"You step into {b_info['name']}.")
        return

    syndicate_night_access = (
        b_id == "stables"
        and "syndicate token" in player.get("inventory", [])
        and 750 <= time_of_day <= 950
    )
    is_open, closed_msg = check_building_open(b_id, player["total_game_minutes"], player)
    if not is_open and not syndicate_night_access and not player.get("active_mayor_task"):
        add_log(closed_msg)
        set_state("MAIN")
        return

    player["current_building"] = b_id
    loc_typewriter_idx = 0
    if syndicate_night_access and not is_open:
        db.npc_database["breakchains"]["location"] = "stable loft"
        add_log("You flash the Red-and-Black Syndicate Token through the side latch. A hooded lookout silently unbars the stable door and gestures toward the Hay Loft above.")
    elif b_id == "mayor's house" and player.get("active_mayor_task") and not is_open:
        add_log("You knock heavily on the ornate doors. Praisegod scowls at the late hour, but unlocks it to let you inside.")
    elif player.get("active_mayor_task") and not is_open:
        add_log("Flashing the Mayor's seal grants you immediate access. The doors are unlocked for you.")
    else:
        add_log(f"You open the door and enter {b_info['name']}.")

def action_exit():
    global loc_typewriter_idx
    loc_typewriter_idx = 0
    if not player["current_building"]:
        return
    parent = db.building_database[player["current_building"]].get("parent")
    if parent:
        player["current_building"] = parent
        add_log(f"You return to the {db.building_database[parent]['name']}.")
    else:
        player["current_building"] = None
        add_log("You step back outside into the fresh air.")


def action_check_status():
    skills_str = ", ".join(player["skills"]).title() if player["skills"] else "None"
    job_raw = player["current_job"]
    job_str = " ".join(w.capitalize() for w in job_raw.split()) if job_raw else "Unemployed"
    curr_w = get_inventory_weight(player)
    max_w = get_max_carry_weight(player)
    affs = [AFFLICTION_INFO[a]["name"] for a in player.get("afflictions", []) if a in AFFLICTION_INFO]
    aff_str = ", ".join(affs) if affs else "Healthy"
    bank_str = f" (Footlocker: {player.get('banked_silver', 0)}s | Chips: {player.get('casino_chips', 0)})" if (player.get("banked_silver", 0) or player.get("casino_chips", 0)) else ""

    status_msg = (
        f"--- CHARACTER STATUS ---\n"
        f"Silver: {player['silver']}s{bank_str} | Reputation: {player['reputation']} | Weight: {curr_w}/{max_w} lbs\n"
        f"Health: {player['health']}/{player['max_health']} ({aff_str}) | Hunger: {player['hunger']:.0f}/100 | Thirst: {player['thirst']:.0f}/100\n"
        f"Strength: {player['strength']} | Charisma: {player['charisma']} | Stealth: {player['stealth']} | Influence: {player['influence']} | Equusense: {player['equusense']}\n"
        f"Faction reputation: Union, {player['faction_union']} | Guard, {player['faction_guard']} | Wallmakers, {player['faction_wallmakers']} |\n"
    )
    if player.get("chapter_2_unlocked"):
        status_msg += f"    Vanguardists, {player['faction_vanguardists']} | Communards, {player['faction_communards']}\n"

    status_msg += (
        f"Employment: {job_str} (Tenure: {player['current_tenure']} shifts) | Union: {player['union_status'] or 'None'}\n"
        f"Weapon: {format_item_name(player['equipped_weapon'])} | Shield: {format_item_name(player.get('equipped_shield', 'none'))}\n"
        f"Skills: {skills_str}"
    )
    
    if "horse" in player["inventory"] or player.get("horse_stabled"):
        if player.get("horse_stabled"):
            debt = get_stabling_debt(player)
            stabled_tag = f" (Stabled at Murum Stables — Tab Owed: {debt}s / 20s max)"
        else:
            stabled_tag = ""
        status_msg += (
            f"\n--- HORSE STATUS{stabled_tag} ---\n"
            f"Horse Hunger: {player['horse_hunger']:.0f}/100 | Horse Thirst: {player['horse_thirst']:.0f}/100 | "
            f"Shoe Durability: {player['horse_shoe_durability']}"
        )
    add_log(status_msg)

def action_talk(target_npc):
    global selected_target
    selected_target = target_npc
    if target_npc == "hopestill":
        if not player.get("spoken_to_hopestill"):
            player["spoken_to_hopestill"] = True
            add_log("Hopestill leans back in the shadowed booth, sizing you up with cold, calculating eyes.\n\"So, you found me.\"")
        else:
            add_log("Hopestill nods subtly from the shadows. \"Speak quickly.\"")
    set_state("NPC_DIALOGUE")

def action_steal_subject(target):
    global player
    player, msg = steal_subject_helper(player, world_map, target)
    if msg:
        add_log(msg)
    set_state("MAIN")

def action_steal_letter_map():
    global player
    player, msg = steal_letter_map_helper(player)
    if msg:
        add_log(msg)
    set_state("MAIN")

def action_show_inventory():
    curr_w = get_inventory_weight(player)
    max_w = get_max_carry_weight(player)
    state_tag = " [HEAVY - SLOWED]" if curr_w > max_w else ""

    if not player["inventory"]:
        add_log(f"--- INVENTORY (Weight: {curr_w}/{max_w} lbs{state_tag}) ---\nYour pockets and pack are completely empty.")
        return

    counts = {}
    for item in player["inventory"]:
        counts[item] = counts.get(item, 0) + 1

    lines = [f"--- INVENTORY (Weight: {curr_w}/{max_w} lbs{state_tag}) ---"]
    for item_key, qty in counts.items():
        display_name = format_item_name(item_key)
        unit_w = db.item_database.get(item_key, {}).get("weight", 0.2)
        total_item_w = round(unit_w * qty, 1)
        qty_str = f" (x{qty})" if qty > 1 else ""
        w_str = f" [{total_item_w} lbs]" if total_item_w > 0 else ""
        desc = db.item_database.get(item_key, {}).get("description", "")
        lines.append(f"• {display_name}{qty_str}{w_str}: {desc}")

    add_log("\n".join(lines))


def open_system_menu():
    """Opens the system help and settings menu with concise, fitted instructions."""
    help_text = (
        "--- DTESSERA TERRA: CONTROLS & GUIDE ---\n"
        "• [Action -> Use Item]: Operate tools, torches, maps, codewheels, cards, dice & presses.\n"
        "• [Action -> Consume / Equip / Read]: Eat food, equip weapons, or read letters.\n"
        "• [C] Character Status & Mannequin  |  [I] Inventory Satchel\n"
        "• [W] or Click Top Bar: Weather Almanac & 3-Day Forecast\n"
        "• [T] Toggle Topo/Flood Overlay (Requires Topographic Survey Map)\n"
        "• [F11] or [Alt+Enter]: Toggle Fullscreen Mode"
    )
    set_state("SYSTEM_MENU", help_text)


def open_arcade_menu():
    set_state(
        "ARCADE_MENU",
        "Welcome to the House of Games Arcade Hall! Step up to any mechanical cabinet (1 Chip per play) or click [View High Scores]."
    )

def action_practice_archery():
    global player
    pos = (player["x"], player["y"])
    room = world_map.get(pos)
    if player.get("current_building") or not room or "Archery Butts" not in room.objects:
        add_log("There are no Archery Butts here to practice on.")
        set_state("MAIN")
        return

    # Free loaner bow at the Guard House if you are in good standing with the Watch (Guard Faction >= 3)
    if pos == (7, 14) and player.get("faction_guard", 0) >= 3:
        fee_note = "The Guard Quartermaster nods respectfully and hands you a practice bow free of charge.\n\n"
    else:
        if player["silver"] < 2:
            add_log("Renting a loaner yew bow and a sheaf of target arrows at the butts costs 2 silver, and you don't have enough coin!")
            set_state("MAIN")
            return
        player["silver"] -= 2
        fee_note = f"You pay 2 silver to rent a loaner yew bow and a sheaf of blunt target arrows. (Remaining Silver: {player['silver']}s)\n\n"

    player["arcade_mode"] = False
    player, log_msg, next_state = mini_games.init_archery_minigame(player)
    set_state(next_state, fee_note + log_msg)

def action_read_subject(alias):
    global player, active_map_key
    if alias in MAP_CONFIGS:
        active_map_key = alias
        set_state("MAP_VIEW")
        return
    item = db.readables_database[alias]
    log_msg = f"--- {format_item_name(alias).upper()} ---\n{item['text']}"

    if alias == "bundle of radical pamphlets" and not player.get("read_proudhon"):
        player["read_proudhon"] = True
        player["charisma"] += 1
        if "radical theory" not in player["skills"]:
            player["skills"].append("radical theory")
        log_msg += "\n\n*** Reading Proudhon's fierce critique sharpens your rhetoric! (+1 Charisma, 'radical theory' skill!) ***"

    # --- CHAPTER 2 NOTICEBOARD TRIGGER ---
    if alias == "noticeboard" and player.get("chapter_2_unlocked"):
        eligible = get_eligible_chapter_2_routes(player)
        if eligible:
            log_msg += (
                "\n\n=== NEW REGIONAL OPPORTUNITIES (CHAPTER 2) ===\n"
                "Scanning the upper tier of the Noticeboard, several prestigious postings catch your eye:\n"
                + "\n".join(f" • {r}" for r in eligible)
                + "\n\nSelect an opportunity on the right to begin Chapter 2 (or step back to prepare):"
            )
            set_state("CHAPTER_2_BOARD", log_msg)
            return

    if selected_target == "career ledger":
        set_state("MINIGAME_TRACK_TABLE", "You open your Surveyor's Career Ledger to inspect the 10 Chapter 2 Career Track requirements.")
        return

    add_log(log_msg)
    set_state("MAIN")

def open_map_viewer():
    """Opens the Chapter 3 War Table if in Chapter 3, or the Regional Map Viewer."""
    global active_map_key
    if player.get("ch3_factions"):
        set_state(
            "CH3_AFTERNOON_PHASE",
            "You unroll the Chapter 3 Strategic War Table.",
        )
        return
    owned_maps = [m for m in MAP_CONFIGS if m in player["inventory"]]
    if not owned_maps:
        add_log("You do not have any maps in your inventory!")
        return
    if (
        not (6 <= player["x"] <= 12 and 12 <= player["y"] <= 17)
        and "dtessera terra world map" in owned_maps
    ):
        active_map_key = "dtessera terra world map"
    elif active_map_key not in owned_maps:
        active_map_key = owned_maps[0]
    set_state("MAP_VIEW")

def action_gather():
    global player, selected_target
    egg_hit, egg_msg = ch2_easter_eggs.check_wilderness_easter_egg_search(
        player, world_map
    )
    if egg_hit:
        add_log(egg_msg)
        check_master_clock()
        return
    
    handled_fluvius, fluvius_msg = ch2_union.handle_fluvius_search(player)
    if handled_fluvius:
        add_log(fluvius_msg)
        check_master_clock()
        return

    handled_guard, guard_msg = ch2_guard.handle_guard_fluvius_search(player)
    if handled_guard:
        add_log(guard_msg)
        check_master_clock()
        return

    handled_castellan, castellan_msg = ch2_castellan.handle_castellan_search(player)
    if handled_castellan:
        add_log(castellan_msg)
        check_master_clock()
        return

    handled_parvus, parvus_msg = ch2_parvus.handle_parvus_search(player)
    if handled_parvus:
        add_log(parvus_msg)
        check_master_clock()
        return

    entered_dung, dung_log, dung_state = ch2_dungeons.check_dungeon_search_entry(player)
    if entered_dung:
        set_state(dung_state, dung_log)
        check_master_clock()
        return

    handled_el, el_msg = ch2_election.handle_election_search(player)
    if handled_el:
        add_log(el_msg)
        check_master_clock()
        return

    handled_rg, rg_msg = ch2_roguery.handle_roguery_search(player)
    if handled_rg:
        add_log(rg_msg)
        check_master_clock()
        return

    handled_crypto, crypto_state, crypto_msg = cryptography_engine.use_non_fighting_item(selected_target, player, world_map)
    if handled_crypto:
        set_state(crypto_state, crypto_msg)
        check_master_clock()
        return

    if "postbox" in str(selected_target).lower():
        _, g_msg, g_state = cryptography_engine.init_gchq_puzzle(player)
        set_state(g_state, g_msg)
        return

    # --- POST OFFICE POSTBOX (8, 16): FIND MISDELIVERED LETTER WITH MURUM MAP ---
    if (player["x"], player["y"]) == (8, 16) and not player["current_building"]:
        if not player.get("postbox_letter_taken"):
            player["postbox_letter_taken"] = True
            player["inventory"].append("misdelivered town hall letter")
            add_log(
                "Checking the wooden Postbox outside the Post Office, you spot a thick parchment envelope sticking halfway out of the slot—accidentally left behind by Fleetfoot the Postie!\n"
                "It is addressed to the **Murum Town Hall** Surveyor's Office, and you can feel something inside.\n\n"
                "*** You found the Misdelivered Town Hall Letter! ***\n"
                "Will you take it to the **Town Hall** and use 'Gather / Search' inside to hand it in to the clerk, "
                "or will you to rip open the letter and keep the contents for yourself?"
            )
        else:
            add_log("You check the Postbox, but there is no other mail sticking out of the slot.")

    # --- TOWN HALL LOBBY: DELIVER MISDELIVERED LETTER FOR 15s + 1 REP ---
    elif player["current_building"] == "town hall" and "misdelivered town hall letter" in player["inventory"]:
        player["inventory"].remove("misdelivered town hall letter")
        player["silver"] += 15
        player["reputation"] += 1
        add_log(
            "You hand the Misdelivered Town Hall Letter to the grateful municipal clerk in the marble lobby.\n"
            "\"Our newly commissioned street plan of Murum! Thank heavens an honest citizen found this before some cutpurse snatched it from the postbox!\n"
            "\"Please take a reward!!\" The clerk counts out **15 silver coins** into your hand!\n\n"
            f"*** Letter Delivered! (+15 Silver, +1 Reputation | Total Silver: {player['silver']}s, Reputation: {player['reputation']}) ***"
        )

    # --- WALLMAKERS SHIFT 1: 4-SECTOR PERIMETER INSPECTION ---
    elif player.get("active_wallmaker_task") == "inspect_perimeter" and not player["current_building"]:
        sector_map = {
            (8, 16): "north", (9, 16): "north",
            (7, 15): "west",
            (8, 13): "south",
            (11, 14): "east"
        }
        pos = (player["x"], player["y"])
        if pos in sector_map:
            sector = sector_map[pos]
            if sector in player.get("wall_sectors_inspected", []):
                add_log(f"You have already inspected and logged the {sector.title()} Wall sector.")
                return
            player, log_msg, next_state = mini_games.init_sounding_minigame(player, sector)
            set_state(next_state, log_msg)
            return

    # --- WALLMAKERS SHIFT 2: PENTOMINO BREACH REPAIR AT EAST WALL (11, 14) ---
    elif player.get("active_wallmaker_task") == "repair_breach" and not player["current_building"]:
        if (player["x"], player["y"]) == (11, 14):
            if "smugglers' cipher" not in player["inventory"]:
                player["inventory"].append("smugglers' cipher")
            player, log_msg, next_state = mini_games.init_breach_minigame(player)
            set_state(next_state, log_msg)
            return
        else:
            add_log("The failed break-in is on the East Wall behind the Blacksmiths.")
            return

    # --- WALLMAKERS SHIFT 4: SECRET STAIRS & PARAPET AT TAVERN CORNER (10, 13) ---
    elif player.get("active_wallmaker_task") == "walk_secret_stairs" and not player["current_building"]:
        if (player["x"], player["y"]) == (10, 13):
            player, log_msg, next_state = mini_games.init_parapet_minigame(player)
            set_state(next_state, log_msg)
            return
        else:
            add_log("The hidden postern door to the secret wall stairs is outside the Murum Tavern.")
            return

    # --- WALLMAKERS SHIFT 5: CONTACT 'X' AT TOWN HALL MILESTONE (10, 16) ---
    elif player.get("active_wallmaker_task") == "smuggle_silk" and not player["current_building"]:
        if (player["x"], player["y"]) == (10, 16):
            player, log_msg, next_state = mini_games.init_smuggle_minigame(player)
            set_state(next_state, log_msg)
            return
        else:
            add_log("Your contact 'X' is waiting by the milestone outside Town Hall.")
            return

    # --- STABLES SHIFT 5: GRAZING FIELD CAMP SETUP (8, 13) ---
    elif (player["x"], player["y"]) == (8, 13) and not player["current_building"] and player.get("active_stable_task") == "setup_grazing_field":
        if "tent" in player["inventory"] and "sack of oats" in player["inventory"]:
            player["inventory"].remove("tent")
            player["inventory"].remove("sack of oats")
            player["active_stable_task"] = "report_manager_5"
            player, _ = advance_time(60, player)
            add_log(
                "You pitch the sturdy canvas tent in the Grazing Field and pour the Sack of Oats into a makeshift trough.\n"
                "The four Union draught horses trot over and begin munching contentedly!\n"
                "*** Camp Set Up! Return to Squire Godspeed at the Stables to complete Shift 5! ***"
            )
            check_master_clock()
        else:
            add_log("You need both a 'Tent' and a 'Sack of Oats' from the Commissary on the High Street and the Corn Chandler at the Food Market")
        return

    # --- TOWN HALL COBNUTS (10, 16) ---
    elif player["x"] == 10 and player["y"] == 16 and not player["current_building"]:
        if "cobnuts" not in player["inventory"]:
            player["inventory"].append("cobnuts")
            player, _ = advance_time(10, player)
            add_log("You gather a handful of fresh cobnuts from beneath the trees.")
            check_master_clock()
        else:
            add_log("You have already gathered all the good cobnuts here.")

    # --- MARKET SHIFTS 1 & 3: THE MARKET SQUARE (8, 15) ---
    elif player["x"] == 8 and player["y"] == 15 and not player["current_building"]:
        if player.get("active_market_task") == "search_fountain_key":
            if "muddy master key" not in player["inventory"]:
                player["inventory"].append("muddy master key")
                player, _ = advance_time(10, player)
                add_log(
                    "You roll up your sleeve and plunge your arm into the icy basin of the market fountain.\n"
                    "Wedged deep in the iron drainage grate, your fingers close around a heavy iron key!\n"
                    "*** You obtained the Master Key! Return it to Godwin (or take it to someone shadier first)! ***"
                )
                check_master_clock()
            else:
                add_log("You already fished the Master Key out of the fountain.")
        elif player.get("active_market_task") == "sweep_contraband":
            player["inventory"].append("bundle of radical pamphlets")
            player["market_state"] = "contraband_confrontation"
            selected_target = "market manager"
            player, _ = advance_time(20, player)
            set_state(
                "NPC_DIALOGUE",
                "While sweeping behind the stalls, your broom dislodges a loose cobblestone beneath a crate.\n"
                "You pull out an oilskin-wrapped Bundle of Radical Pamphlets titled 'What Is Property?'!\n\n"
                "Suddenly, Godwin's shadow falls over you. \"What have you got there, sweeper?!\""
            )
            check_master_clock()
        else:
            add_log("You search around the market stalls and fountain, but find nothing out of the ordinary.")

    # --- SHIFT 5: THE BUCKET OF SAND ---
    elif (player["x"], player["y"]) in [(7, 15), (11, 14)] and not player["current_building"]:
        if "bucket of sand" not in player["inventory"]:
            player["inventory"].append("bucket of sand")
            add_log("You grab one of the heavy buckets of sand that have always sat outside the doors.\n*** You obtained a Bucket of Sand! ***")
        else:
            add_log("You already have a bucket of sand.")

    elif player["current_building"] == "stable loft":
        if player.get("active_stable_task") == "gather_supplies":
            if "clean straw" not in player["inventory"]:
                player["inventory"].append("clean straw")
                add_log("*** You obtained Clean Straw! ***")
            else:
                add_log("You already have enough clean straw.")
        else:
            add_log("You rummage through the hay, but find nothing of use.")

    elif player["current_building"] == "tack room":
        if player.get("active_blacksmith_task") == "stables_fire_rescue":
            if "hidden secret ledger" not in player["inventory"]:
                player["inventory"].append("hidden secret ledger")
                add_log("You pry up the loose floorboards through the thick smoke and find a pristine book!\n*** You obtained the Hidden Secret Ledger! ***")
            else:
                add_log("You already grabbed the ledger! Get out of the smoke!")

        elif player.get("active_stable_task") == "search_tack_room":
            if "torn ledger page" not in player["inventory"]:
                player["inventory"].extend(["torn ledger page", "smudged receipt"])
                player["active_stable_task"] = "report_manager_1"
                add_log("You search the messy tack room. Hidden under a pile of broken stirrups, you find two pieces of paper!\n*** You obtained a Torn Ledger Page and a Smudged Receipt! ***")
            else:
                add_log("You have already searched the desk.")
        elif player.get("active_stable_task") == "gather_supplies":
            if "foaling manual" not in player["inventory"]:
                player["inventory"].append("foaling manual")
                add_log("You search the cluttered desk. Hidden under an empty, sticky ale mug, you find a book.\n*** You obtained the Foaling Manual! ***")
            else:
                add_log("You have already searched the desk.")
        else:
            add_log("There is nothing of value to gather or search for here right now.")
    else:
        foraged, f_log, f_state = chapter_2.trigger_wilderness_forage(player, world_map)
        if foraged:
            set_state(f_state, f_log)
            check_master_clock()
        else:
            player, log_msg, next_state = search_engine.init_search_modal(player, world_map)
            set_state(next_state, log_msg)
            check_master_clock()

# ----------------------------------
# ANIMAL CARE WRAPPERS
# ----------------------------------
def action_stable_horse():
    global player
    player, msg = stable_horse_helper(player)
    if msg:
        add_log(msg)
    set_state("MAIN")


def action_feed_animal(animal):
    global player
    player, msg = feed_animal_helper(player, animal)
    if msg:
        add_log(msg)
    set_state("MAIN")


def action_water_animal(animal):
    global player
    player, msg = water_animal_helper(player, animal)
    if msg:
        add_log(msg)
    set_state("MAIN")


def action_graze_animal(animal):
    global player
    player, msg = graze_animal_helper(player, animal)
    if msg:
        add_log(msg)
    check_master_clock()
    set_state("MAIN")

def get_subjects_for_verb(verb):
    subjects = []
    current_loc = player["current_building"] if player["current_building"] else (player["x"], player["y"])

    if verb == "Enter":
        if player["current_building"]:
            for b_id, b_info in db.building_database.items():
                if b_info.get("parent") == player["current_building"]:
                    subjects.append((f"Enter {b_info['name']}", lambda b=b_id: action_enter(b) or set_state("MAIN")))
        else:
            for b_id, b_info in db.building_database.items():
                if b_info["location"] == current_loc and not b_info.get("parent"):
                    subjects.append((b_info["name"], lambda b=b_id: action_enter(b) or set_state("MAIN")))

    elif verb == "Talk":
        for npc_id in get_npcs_at_current_location():
            npc_info = db.npc_database[npc_id]
            subjects.append((npc_info["proper_name"], lambda n=npc_id: action_talk(n)))

    elif verb == "Read":
        for alias, item in db.readables_database.items():
            if item["location"] == current_loc or (item["location"] == "inventory" and alias in player["inventory"]):
                subjects.append((format_item_name(alias), lambda a=alias: action_read_subject(a)))
                
        # Also let them read any generic objects that sound like signs in the room
        if not player["current_building"]:
            pos = (player["x"], player["y"])
            if pos in world_map:
                for obj in world_map[pos].objects:
                    if "sign" in obj.lower() or "milestone" in obj.lower() or "notice" in obj.lower():
                        # Just output the tile description again as the "reading" text
                        desc = world_map[pos].description
                        subjects.append((f"Read {format_item_name(obj)}", lambda d=desc, o=obj: (add_log(f"--- {o.upper()} ---\n{d}"), set_state("MAIN"))))

    elif verb == "Equip":
        weapons = [i for i in player["inventory"] if i in db.weapon_max_hit and i != "fists"]
        for w in sorted(set(weapons)):
            subjects.append((f"Weapon: {format_item_name(w)}", lambda item=w: action_equip(item)))
        if player["equipped_weapon"] != "fists":
            subjects.append(("Unequip Weapon (Fists)", lambda: action_equip("fists")))

        shields = [i for i in player["inventory"] if i in db.shield_defense and i != "none"]
        for sh in sorted(set(shields)):
            b_val = db.shield_defense[sh]
            subjects.append((f"Shield: {format_item_name(sh)} (-{b_val} Dmg)", lambda item=sh: action_equip(item)))
        if player.get("equipped_shield", "none") != "none":
            subjects.append(("Unequip Shield", lambda: action_equip("unequip_shield")))

    elif verb == "Use Item":
        usables = get_usable_inventory_items(player)
        for item, count in Counter(usables).items():
            label = f"{format_item_name(item)}" if count == 1 else f"{format_item_name(item)} (x{count})"
            subjects.append((label, lambda i=item: action_use(i)))

    elif verb == "Consume":
        consumables = [
            i for i in player["inventory"]
            if any(k in db.item_database.get(i, {}) for k in ["hunger_restore", "thirst_restore", "cures_affliction"])
        ]
        for item, count in Counter(consumables).items():
            label = f"{format_item_name(item)}" if count == 1 else f"{format_item_name(item)} (x{count})"
            subjects.append((label, lambda i=item: (action_consume(i), set_state("MAIN"), check_master_clock())))
         
    elif verb in ["Feed", "Water", "Graze"]:
        for animal in get_available_horses(player):
            display_animal = format_item_name(animal)
            if verb == "Feed":
                subjects.append((display_animal, lambda a=animal: action_feed_animal(a)))
            elif verb == "Water":
                subjects.append((display_animal, lambda a=animal: action_water_animal(a)))
            elif verb == "Graze":
                subjects.append((display_animal, lambda a=animal: action_graze_animal(a)))

    elif verb == "Climb":
        cur_pos = (player["x"], player["y"])
        cur_room = world_map.get(cur_pos)
        on_high_wall = cur_room and cur_room.name in ["The Town Wall", "Mountain"]

        directions = [(0, 1, "North"), (0, -1, "South"), (1, 0, "East"), (-1, 0, "West")]
        for dx, dy, dir_name in directions:
            adj_pos = (player["x"] + dx, player["y"] + dy)
            if adj_pos in world_map:
                adj_room = world_map[adj_pos]
                if adj_room.name in ["The Town Wall", "Mountain"] and not on_high_wall:
                    subjects.append((
                        f"Climb Up {adj_room.name} ({dir_name})",
                        lambda r=adj_room.name, x=dx, y=dy: action_climb(r, x, y, mode="up")
                    ))
                elif on_high_wall and adj_room.name not in ["The Town Wall", "Mountain"]:
                    subjects.append((
                        f"Climb Down to {adj_room.name} ({dir_name})",
                        lambda r=adj_room.name, x=dx, y=dy: action_climb(r, x, y, mode="down")
                    ))
    elif verb in ["Mount / Dismount", "Mount", "Dismount"]:
        known_mounts = ["horse", "giant hairy armadillo", "mouflin", "hippos", "deer"]
        for animal in known_mounts:
            is_riding = player.get("riding_horse", False) if animal == "horse" else player.get(f"riding_{animal}", False)
            if animal in player["inventory"] or is_riding:
                lbl = f"Dismount {format_item_name(animal)}" if is_riding else f"Mount {format_item_name(animal)}"
                subjects.append((lbl, lambda a=animal: action_mount_dismount(a)))

    elif verb == "Drink / Fill":
        if "full water flask" in player["inventory"]:
            subjects.append(("Drink Full Flask", lambda: action_drink("full water flask")))
        if "half-full water flask" in player["inventory"]:
            subjects.append(("Drink Half-Full Flask", lambda: action_drink("half-full water flask")))

        water_source = get_local_water_source(player, world_map)
        if water_source:
            subjects.append((f"Drink from {water_source.title()}", lambda w=water_source: action_drink(w)))
            if water_source != "sea" and ("empty flask" in player["inventory"] or "half-full water flask" in player["inventory"]):
                subjects.append((f"Fill Flask at {water_source.title()}", lambda w=water_source: action_fill_flask(w)))

    elif verb == "Steal":
        if "misdelivered town hall letter" in player["inventory"]:
            subjects.append(("Steal Map from Misdelivered Letter", action_steal_letter_map))
        if not player["current_building"]:
            pos = (player["x"], player["y"])
            if pos in world_map:
                for obj in world_map[pos].objects:
                    if obj.lower() in db.item_database or obj.lower() == "horse":
                        subjects.append((f"Steal {format_item_name(obj)}", lambda o=obj: action_steal_subject(o)))

    elif verb == "Stash / Retrieve":
     if not can_use_storage(player):
         subjects.append(("Go to Tavern/Pub/Workplace to use Footlocker", lambda: set_state("MAIN")))
     else:
         if player["silver"] >= 10:
             subjects.append((f"Deposit 10s (Purse: {player['silver']}s)", lambda: action_deposit_silver(10)))
         if player["silver"] > 0:
             subjects.append((f"Deposit All Silver ({player['silver']}s)", lambda: action_deposit_silver(player["silver"])))
         if player.get("banked_silver", 0) > 0:
             banked = player["banked_silver"]
             subjects.append((f"Withdraw All Silver ({banked}s)", lambda: action_withdraw_silver(banked)))
         for item in sorted(set(player["inventory"])):
             if item not in ["horse", "dtessera terra world map", "murum town map"]:
                 w = db.item_database.get(item, {}).get("weight", 0.2)
                 subjects.append((f"Stash: {format_item_name(item)} ({w} lbs)", lambda i=item: action_stash_item(i)))
         for item in sorted(set(player.get("storage", []))):
             w = db.item_database.get(item, {}).get("weight", 0.2)
             subjects.append((f"Retrieve: {format_item_name(item)} ({w} lbs)", lambda i=item: action_retrieve_item(i)))

    elif verb == "Sell":
        if not (player["x"] == 8 and player["y"] == 15 and not player["current_building"]):
            subjects.append(("Visit Murum Market to sell items", lambda: set_state("MAIN")))
        else:
            for item in sorted(set(player["inventory"])):
                price = db.item_database.get(item, {}).get("price", 0)
                if price > 0:
                    sell_val = max(1, price // 3)
                    subjects.append((f"Sell {format_item_name(item)} (+{sell_val}s)", lambda i=item: action_sell_item(i)))

    elif verb == "Drop":
         droppables = [
             i for i in player["inventory"]
             if db.item_database.get(i, {}).get("price", 0) > 0 or i in ["spoiled food", "cobnuts", "clean straw", "bucket of sand"]
         ]
         for item, count in Counter(droppables).items():
             label = f"{format_item_name(item)}" if count == 1 else f"{format_item_name(item)} (x{count})"
             subjects.append((label, lambda i=item: action_drop(i)))

    elif verb == "Give Gift":
        gifts = [i for i in player["inventory"] if db.item_database.get(i, {}).get("gift")]
        npcs_here = get_npcs_at_current_location()
        for npc_k in npcs_here:
            if npc_k == "horse":
                continue
            for g in sorted(set(gifts)):
                npc_label = db.npc_database[npc_k]["proper_name"]
                label = f"{format_item_name(g)} -> {npc_label}"
                subjects.append((label, lambda n=npc_k, item=g: action_give_gift(n, item)))

    return subjects


# =========================================================================
# 6. DYNAMIC UI GENERATOR
# =========================================================================
def format_arcade_high_scores(player):
    scores = player.get("arcade_high_scores", {})
    lines = ["--- HOUSE OF GAMES: OFFICIAL HIGH SCORES ---"]
    for game_name, val in scores.items():
        lines.append(f"• {game_name}: {val}")
    return "\n".join(lines) if len(lines) > 1 else "No arcade records posted yet—step up to a cabinet to set the first record!"

def get_current_right_buttons():
    global player
    buttons = []
    px, py, bw, bh, vgap = 280, 368, 480, 36, 5
    m_px, m_py, m_bw = 460, 395, 320

    if menu_state == "START_SCREEN":
        bw_card, bh_card = 320, 38
        cx = 400 - bw_card // 2
        buttons.append(
            Button(
                (cx, 380, bw_card, bh_card),
                "Begin New Adventure",
                restart_new_game,
            )
        )
        if os.path.exists(SAVE_FILE):
            buttons.append(
                Button(
                    (cx, 424, bw_card, bh_card),
                    "Continue Saved Game",
                    lambda: load_game_from_disk(SAVE_FILE),
                )
            )
        if os.path.exists("profile_noburu_meta.json"):
            buttons.append(
                Button(
                    (cx, 468, bw_card, bh_card),
                    "Hall of Hegemony (Victory Grid)",
                    lambda: set_state("VICTORY_GRID_MENU"),
                )
            )
        buttons.append(
            Button(
                (cx, 512, bw_card, bh_card),
                "Quit to Desktop",
                lambda: sys.exit(),
            )
        )
        return buttons

    elif menu_state == "CHAPTER_1_INTRO":
        bw_card, bh_card = 360, 42
        cx = 400 - bw_card // 2

        def enter_makepeace_office():
            add_log(
                "Welcome to Dtessera Terra!\n"
                "Dr. Makepeace folds their hands across their desk and "
                "waits for your answer.\n"
            )
            set_state("MAIN")

        buttons.append(
            Button(
                (cx, 510, bw_card, bh_card),
                "Step into Dr. Makepeace's Office >>",
                enter_makepeace_office,
            )
        )
        return buttons

    elif menu_state == "CHAPTER_2_COMPLETE":
        def begin_ch3():
            global player
            if "ch3_factions" not in player:
                player = ch3_war_engine.init_chapter_3_world_board(
                    player, world_map
                )
            player = ui_renderer.init_ch3_morning_phase(player)
            set_state(
                "CH3_MORNING_PHASE",
                "Dawn breaks over Dtessera Terra. The war for hegemony begins.",
            )

        bw_card, bh_card = 360, 42
        cx = 400 - bw_card // 2
        buttons.append(
            Button(
                (cx, 510, bw_card, bh_card),
                "Take Command (Begin Chapter 3) >>",
                begin_ch3,
            )
        )
        return buttons

    elif menu_state == "SYSTEM_MENU":
        by, bh_sys = 508, 36
        buttons.append(Button((48, by, 132, bh_sys), "Save Game (F5)", lambda: save_game_to_disk(SAVE_FILE)))
        buttons.append(Button((188, by, 132, bh_sys), "Load Game (F9)", lambda: load_game_from_disk(SAVE_FILE)))
        buttons.append(Button((328, by, 145, bh_sys), "Fullscreen (F10)", toggle_fullscreen))
        buttons.append(Button((481, by, 145, bh_sys), "Export Report", lambda: add_log(export_playtest_report("Manual Export"))))
        buttons.append(Button((634, by, 118, bh_sys), "Close", lambda: set_state("MAIN")))

    elif menu_state == "ARCADE_MENU":
        arcade_games = [
            ("Blacksmith Forge", "forge"),
            ("Masonry Jigsaw", "jigsaw"),
            ("Market Thief Chase", "chase"),
            ("Fly-Tipping Board", "flytip"),
            ("Parapet Cache", "parapet"),
            ("Smuggler Run", "smuggle"),
            ("Apothecary Recipe", "recipe"),
            ("Sounding Rush", "sounding"),
            ("Sharpshooter Archery", "archery"),
        ]
        col_w, row_h = 235, 29
        for idx, (g_label, g_key) in enumerate(arcade_games):
            col = idx % 2
            row = idx // 2
            def launch_arc(k=g_key):
                global player
                player, msg, st = mini_games.start_arcade_game(player, k)
                set_state(st, msg)
            buttons.append(Button((px + col * 245, py + row * 33, col_w, row_h), g_label, launch_arc))
        back_target = lambda: set_state("MAIN") if player.get("current_building") == "house of games" else open_system_menu()
        buttons.append(Button((px + 245, py + 4 * 33, col_w, row_h), "View High Scores", lambda: add_log(format_arcade_high_scores(player))))
        buttons.append(Button((px + 245, py + 5 * 33, col_w, row_h), "< Leave Cabinets", back_target))

    elif menu_state == "CASINO_CRAPS":
        def cr_act(act):
            global player
            player, log_msg, next_state = mini_games.resolve_craps_action(act, player)
            set_state(next_state, log_msg)

        by, bh = 523, 36
        if "weighted ivory dice" in player.get("inventory", []) and player.get("cr_phase") != "ROLLING":
            ld_on = player.get("cr_use_loaded", False)
            ld_txt = "Loaded Dice: ON" if ld_on else "Loaded Dice: OFF"
            buttons.append(Button((565, 130, 175, 32), ld_txt, lambda: cr_act("toggle_loaded")))

        if player.get("cr_phase") == "ROLLING":
            buttons.append(Button((250, by, 300, bh), "Dice are tumbling...", lambda: None, enabled=False))
        else:
            cur_c = player.get("cr_chip_val", 1)
            buttons.append(Button((38, by, 72, bh), f"{'>' if cur_c==1 else ''}1 Chip", lambda: cr_act("chip_1")))
            buttons.append(Button((115, by, 72, bh), f"{'>' if cur_c==5 else ''}5 Chips", lambda: cr_act("chip_5")))
            buttons.append(Button((192, by, 78, bh), f"{'>' if cur_c==10 else ''}10 Chips", lambda: cr_act("chip_10")))
            buttons.append(Button((275, by, 78, bh), f"{'>' if cur_c==25 else ''}25 Chips", lambda: cr_act("chip_25")))
            buttons.append(Button((360, by, 86, bh), "Clear", lambda: cr_act("clear")))
            buttons.append(Button((451, by, 86, bh), "Rebet", lambda: cr_act("rebet")))
            buttons.append(Button((544, by, 118, bh), "ROLL DICE >>", lambda: cr_act("roll")))
            buttons.append(Button((668, by, 94, bh), "< Leave", lambda: cr_act("clear_all_leave")))

    elif menu_state == "CASINO_BLACKJACK":
        def bj_act(act):
            global player
            player, log_msg, next_state = mini_games.resolve_blackjack_action(act, player)
            set_state(next_state, log_msg)

        phase = player.get("bj_phase", "BETTING")
        by, bh = 523, 36
        if phase in ("BETTING", "ROUND_OVER"):
            buttons.append(Button((45, by, 115, bh), "Stake: 5", lambda: bj_act("stake_5")))
            buttons.append(Button((170, by, 115, bh), "Stake: 10", lambda: bj_act("stake_10")))
            buttons.append(Button((295, by, 115, bh), "Stake: 25", lambda: bj_act("stake_25")))
            buttons.append(Button((430, by, 160, bh), "Deal Hand", lambda: bj_act("deal")))
            buttons.append(Button((605, by, 150, bh), "< Leave Table", lambda: set_state("MAIN")))
        elif phase == "PLAYER_TURN":
            can_double = (len(player.get("bj_player_hand", [])) == 2 and player.get("casino_chips", 0) >= player.get("bj_stake", 5))
            buttons.append(Button((60, by, 160, bh), "Hit (Draw)", lambda: bj_act("hit")))
            buttons.append(Button((240, by, 160, bh), "Stand (Hold)", lambda: bj_act("stand")))
            buttons.append(Button((420, by, 175, bh), "Double Down", lambda: bj_act("double"), enabled=can_double))
            buttons.append(Button((615, by, 140, bh), "< Leave", lambda: set_state("MAIN"), enabled=False))
        else:
            # DEALER_TURN animation in progress
            buttons.append(Button((260, by, 280, bh), "Dealer is drawing...", lambda: None, enabled=False))

    elif menu_state == "CASINO_POKER":
        def pk_act(act):
            global player
            player, log_msg, next_state = mini_games.resolve_poker_action(act, player)
            set_state(next_state, log_msg)

        phase = player.get("poker_phase", "PREFLOP")
        sub = player.get("poker_subphase", "PLAYER_TURN")
        by, bh = 523, 36

        if phase in ("SHOWDOWN", "MATCH_WON", "MATCH_LOST"):
            if phase == "MATCH_LOST":
                buttons.append(Button((280, by, 240, bh), "< Return to Cashier", lambda: set_state("MAIN")))
            elif phase == "MATCH_WON":
                buttons.append(Button((170, by, 230, bh), "New 50-Chip Match", lambda: pk_act("deal")))
                buttons.append(Button((420, by, 200, bh), "< Leave Victorious", lambda: set_state("MAIN")))
            else:
                buttons.append(Button((180, by, 230, bh), "Deal Next Hand (2/4)", lambda: pk_act("deal")))
                buttons.append(Button((430, by, 180, bh), "< Leave Table", lambda: set_state("MAIN")))
        elif sub != "PLAYER_TURN":
            buttons.append(Button((260, by, 280, bh), "Everpenitent is acting...", lambda: None, enabled=False))
        else:
            to_call = player.get("poker_to_call", 0)
            call_lbl = f"Call ({to_call})" if to_call > 0 else "Check"
            min_r, max_r = mini_games.get_poker_raise_bounds(player)
            r_amt = player.get("poker_raise_amt", min_r)

            buttons.append(Button((42, by, 130, bh), call_lbl, lambda: pk_act("check_call")))
            buttons.append(Button((180, by, 52, bh), "-5", lambda: pk_act("raise_minus"), enabled=(max_r > 0)))
            buttons.append(Button((238, by, 175, bh), f"Raise +{r_amt}", lambda: pk_act("raise_custom"), enabled=(max_r > 0)))
            buttons.append(Button((419, by, 52, bh), "+5", lambda: pk_act("raise_plus"), enabled=(max_r > 0)))
            buttons.append(Button((477, by, 92, bh), "All-In", lambda: pk_act("raise_max"), enabled=(max_r > 0)))
            buttons.append(Button((577, by, 175, bh), "Fold Hand", lambda: pk_act("fold")))

    elif menu_state == "CASINO_ROULETTE":
        def rl_act(act):
            global player
            player, log_msg, next_state = mini_games.resolve_roulette_action(act, player)
            set_state(next_state, log_msg)

        by, bh = 523, 36
        if player.get("rl_phase") == "SPINNING":
            buttons.append(Button((250, by, 300, bh), "Wheel is spinning...", lambda: None, enabled=False))
        else:
            cur_c = player.get("rl_chip_val", 1)
            buttons.append(Button((38, by, 72, bh), f"{'>' if cur_c==1 else ''}1 Chip", lambda: rl_act("chip_1")))
            buttons.append(Button((115, by, 72, bh), f"{'>' if cur_c==5 else ''}5 Chips", lambda: rl_act("chip_5")))
            buttons.append(Button((192, by, 78, bh), f"{'>' if cur_c==10 else ''}10 Chips", lambda: rl_act("chip_10")))
            buttons.append(Button((275, by, 78, bh), f"{'>' if cur_c==25 else ''}25 Chips", lambda: rl_act("chip_25")))
            buttons.append(Button((360, by, 86, bh), "Clear", lambda: rl_act("clear")))
            buttons.append(Button((451, by, 86, bh), "Rebet", lambda: rl_act("rebet")))
            buttons.append(Button((544, by, 118, bh), "SPIN >>", lambda: rl_act("spin")))
            buttons.append(Button((668, by, 94, bh), "< Leave", lambda: (mini_games.resolve_roulette_action("clear", player), set_state("MAIN"))))

    elif menu_state == "DEAD":
        if not player.get("_death_exported"):
            player["_death_exported"] = True
            export_playtest_report("GAME OVER / DISMISSED OR DECEASED")
        buttons.append(Button((280, 405, 480, 38), "Retry from Morning Checkpoint", retry_from_morning))
        if os.path.exists(SAVE_FILE):
            buttons.append(Button((280, 450, 480, 38), "Load Last Saved Game", lambda: load_game_from_disk(SAVE_FILE)))
        buttons.append(Button((280, 495, 480, 38), "Restart New Game (Title Screen)", lambda: set_state("START_SCREEN")))
        buttons.append(Button((280, 540, 480, 38), "Quit Game", lambda: sys.exit()))

    elif menu_state == "CHAPTER_1_COMPLETE":
        buttons.append(Button((280, 415, 480, 38), "Continue Exploring Chapter 2 Map (Sandbox Preview)", lambda: set_state("MAIN")))
        buttons.append(Button((280, 460, 480, 38), "Save Completed Chapter 1 Character", lambda: save_game_to_disk("chapter1_complete_save.json")))
        buttons.append(Button((280, 505, 480, 38), "Play Again (Return to Title Screen)", lambda: set_state("START_SCREEN")))

    elif menu_state == "MAIN":
        btn_radius = 30
        status_btn = CircleButton(750, 490, btn_radius, 'status', lambda: set_state("STATUS_MENU"))
        inventory_btn = CircleButton(750, 560, btn_radius, 'inventory', lambda: set_state("INVENTORY_MENU"))
        action_btn = CircleButton(680, 490, btn_radius, 'action', lambda: set_state("ACTION_MENU"))
        help_btn = CircleButton(680, 560, btn_radius, 'help', open_system_menu)

        toggle_font = ui_components.FONT_MD
        mode_lbl = "Mode: LOOK" if dpad_mode == "look" else "Mode: MOVE"
        buttons.append(Button((340, 380, 120, 26), mode_lbl, toggle_dpad_mode, fixed_font=toggle_font))

        # Visible Weather Button (Shows current sky & local temp; opens Almanac Pop-Out when clicked!)
        weather_engine.ensure_weather_initialized(player)
        w_key = player.get("weather_current", "overcast")
        w_short = weather_engine.WEATHER_TYPES.get(w_key, {}).get("name", "Overcast").split()[-1]
        _, _, local_t = weather_engine.get_tile_altitude_and_temp(player, (player["x"], player["y"]), world_map)
        weather_lbl = f"{w_short} ({local_t}°C)"
        buttons.append(Button((655, 420, 120, 26), weather_lbl, lambda: set_state("MINIGAME_WEATHER_REPORT"), fixed_font=toggle_font))

        inv = player.get("inventory", [])
        if any(m in inv for m in MAP_CONFIGS):
            buttons.append(Button((655, 380, 120, 26), "View Map (M)", open_map_viewer, fixed_font=toggle_font))
        buttons.extend([status_btn, inventory_btn, action_btn, help_btn])

    elif menu_state in ["INVENTORY_MENU", "STATUS_MENU"]:
        buttons.append(Button((340, 535, 120, 36), "Close", lambda: set_state("MAIN")))

    elif menu_state == "ACTION_MENU":
        nav_verbs = []
        if get_subjects_for_verb("Enter"):
            nav_verbs.append(("Enter", True))
        if player["current_building"]:
            nav_verbs.append(("Exit", False))
        if not player["current_building"] and get_subjects_for_verb("Climb"):
            nav_verbs.append(("Climb", True))
        if get_subjects_for_verb("Steal"):
            nav_verbs.append(("Steal", True))

        interact_verbs = []
        if get_usable_inventory_items(player):
            interact_verbs.append(("Use Item", True))
        if get_npcs_at_current_location():
            interact_verbs.append(("Talk", True))
        if get_subjects_for_verb("Read"):
            interact_verbs.append(("Read", True))
        interact_verbs.append(("Search", False))
        if not player["current_building"] and (player["x"], player["y"]) in world_map and "Archery Butts" in world_map[(player["x"], player["y"])].objects:
            interact_verbs.append(("Archery", False))
        if get_subjects_for_verb("Give Gift"):
            interact_verbs.append(("Give Gift", True))
        if player.get("current_building") == "house of games":
            interact_verbs.append(("Arcade", False))

        survival_verbs = []
        if get_subjects_for_verb("Consume"):
            survival_verbs.append(("Consume", True))
        if get_subjects_for_verb("Drink / Fill"):
            survival_verbs.append(("Drink / Fill", True))
        survival_verbs.append(("Camp / Sleep", False))
        if get_subjects_for_verb("Equip"):
            survival_verbs.append(("Equip", True))
        if can_use_storage(player):
            survival_verbs.append(("Stash", True))
        if get_subjects_for_verb("Drop"):
            survival_verbs.append(("Drop", True))

        animal_verbs = []
        avail_horses = get_available_horses(player)
        at_stables = (player["current_building"] in ["stables", "tack room", "stable loft"]) or (player["x"] == 7 and player["y"] == 15)
        if avail_horses:
            animal_verbs.append(("Feed", True))
            if "your horse" in avail_horses or "mayor's stallion" in avail_horses:
                animal_verbs.append(("Water", True))
                animal_verbs.append(("Graze", True))
        if get_subjects_for_verb("Mount / Dismount"):
            is_any_mounted = player.get("riding_horse") or player.get("riding_mouflin") or player.get("riding_giant hairy armadillo")
            animal_verbs.append(("Dismount" if is_any_mounted else "Mount", True))
        if at_stables and "horse" in player["inventory"]:
            animal_verbs.append(("Stable (2s)", False))
        if at_stables and player.get("horse_stabled"):
            debt = get_stabling_debt(player)
            animal_verbs.append((f"Unstable ({debt}s)", False))

        def make_cb(v, ns):
            def cb():
                if ns:
                    global selected_verb
                    # Map short display labels back to internal verb keys
                    verb_map = {"Mount": "Mount / Dismount", "Dismount": "Mount / Dismount", "Stash": "Stash / Retrieve"}
                    selected_verb = verb_map.get(v, v)
                    set_state("SUBJECT_MENU")
                else:
                    if v in ["Exit", "Exit / Leave"]:
                        action_exit()
                        set_state("MAIN")
                    elif v in ["Search", "Gather / Search"]:
                        action_gather()
                        if menu_state == "ACTION_MENU":
                            set_state("MAIN")
                    elif v in ["Arcade", "Arcade Machines"]:
                        open_arcade_menu()
                    elif v in ["Archery", "Archery (2s)"]:
                        action_practice_archery()
                    elif v in ["Camp", "Camp / Sleep"]:
                        action_camp()
                    elif v.startswith("Stable") or v.startswith("Collect") or v.startswith("Unstable"):
                        action_stable_horse()
            return cb

        slotted_categories = [
            (0, "ANIMAL CARE", animal_verbs),
            (1, "NAVIGATION", nav_verbs),
            (2, "INTERACT", interact_verbs),
            (3, "SURVIVAL", survival_verbs),
        ]

        start_x = 248
        btn_width = 126
        col_gap = 8
        btn_height = 24
        y_gap = 3
        base_y = 365

        for slot_idx, cat_title, verb_list in slotted_categories:
            if not verb_list:
                continue
            col_x = start_x + slot_idx * (btn_width + col_gap)
            buttons.append(Button((col_x, base_y, btn_width, 20), cat_title, lambda: None, enabled=False))
            cur_y = base_y + 23
            for verb, needs_subject in verb_list:
                buttons.append(Button((col_x, cur_y, btn_width, btn_height), verb, make_cb(verb, needs_subject)))
                cur_y += btn_height + y_gap

        buttons.append(Button((650, 564, 126, 26), "< Back", lambda: set_state("MAIN")))

    elif menu_state == "MAP_VIEW":
        owned_maps = [m for m in MAP_CONFIGS if m in player["inventory"]]
        by = 378
        for m_key in owned_maps:
            prefix = ">> " if m_key == active_map_key else ""
            def switch_map(k=m_key):
                global active_map_key
                active_map_key = k
            buttons.append(Button((530, by, 235, 28), f"{prefix}{format_item_name(m_key)}", switch_map))
            by += 32
        buttons.append(Button((530, 540, 235, 32), "< Close Map (M)", lambda: set_state("MAIN")))
        return buttons

    elif menu_state == "SUBJECT_MENU":
        subjects = get_subjects_for_verb(selected_verb)

        if not subjects:
            buttons.append(Button((px, py, bw, bh), f"Nothing available for '{selected_verb}'.", lambda: None, enabled=False))
            buttons.append(Button((px, py + bh + vgap, bw, bh), "< Back", lambda: set_state("ACTION_MENU")))
        else:
            col_w = 235
            row_h = 30
            gap_x, gap_y = 10, 4
            for idx, (label, callback) in enumerate(subjects[:10]):
                col = idx % 2
                row = idx // 2
                bx = px + col * (col_w + gap_x)
                by = py + row * (row_h + gap_y)
                buttons.append(Button((bx, by, col_w, row_h), label, callback))
            buttons.append(Button((640, 562, 120, 28), "< Back", lambda: set_state("ACTION_MENU")))

    elif menu_state == "SLEEP_MENU":
        buttons.append(Button((480, 230, 280, 32), "Wake at 2:00 (Early Dawn / Bakers)", lambda: execute_sleep("morning_200")))
        buttons.append(Button((480, 268, 280, 32), "Wake at 2:50 (Sunrise Trail)", lambda: execute_sleep("morning_250")))
        buttons.append(Button((480, 306, 280, 32), "Wake at 3:00 (Morning Town Bell)", lambda: execute_sleep("morning_300")))
        buttons.append(Button((480, 344, 280, 32), "Wake at 3:75 (Late Lie-In)", lambda: execute_sleep("morning_375")))
        buttons.append(Button((480, 382, 280, 32), "Take a 2-Hour Nap (+HP)", lambda: execute_sleep("nap")))
        buttons.append(Button((480, 426, 280, 32), "< Cancel", lambda: set_state("MAIN")))

    elif menu_state == "MINIGAME_WEATHER_REPORT":

        def _toggle_topo_from_modal():
            msg = weather_engine.toggle_topo_map(player)
            add_log(msg)
            set_state("MAIN")

        has_topo = "topographic survey map" in player.get("inventory", [])
        buttons.append(Button(
            (75, 475, 315, 38),
            "Toggle Topo / Flood Overlay [T]" if has_topo else "Topo Map Required for Overlay",
            _toggle_topo_from_modal,
            enabled=has_topo
        ))
        buttons.append(Button((410, 475, 315, 38), "Close Almanac", lambda: set_state("MAIN")))

    elif menu_state == "NPC_DIALOGUE":
        options = convo.get_npc_dialogue_options(selected_target, player)
        
        if len(options) <= 5:
            for idx, opt in enumerate(options):
                def make_cb(target, choice_label):
                    def cb():
                        global player, selected_target
                        player, log_msg, next_state = convo.handle_npc_choice(target, choice_label, player)
                        if next_state == "INTERCEPT_MARKET_BRAWL":
                            selected_target = "market manager"
                            next_state = "NPC_DIALOGUE"
                        set_state(next_state, log_msg)
                        check_master_clock()
                    return cb
                buttons.append(Button((px, py + idx * 38, bw, 34), opt, make_cb(selected_target, opt)))
        elif len(options) <= 10:
            col_w = 235
            row_h = 32
            for idx, opt in enumerate(options):
                def make_cb(target, choice_label):
                    def cb():
                        global player, selected_target
                        player, log_msg, next_state = convo.handle_npc_choice(target, choice_label, player)
                        if next_state == "INTERCEPT_MARKET_BRAWL":
                            selected_target = "market manager"
                            next_state = "NPC_DIALOGUE"
                        set_state(next_state, log_msg)
                        check_master_clock()
                    return cb
                col = idx % 2
                row = idx // 2
                buttons.append(Button((px + col * 245, py + row * 36, col_w, row_h), opt, make_cb(selected_target, opt)))
        else:
            # 3-Column layout for massive menus (like the Pawnbroker sell list!)
            col_w = 155
            row_h = 28
            for idx, opt in enumerate(options):
                def make_cb(target, choice_label):
                    def cb():
                        global player, selected_target
                        player, log_msg, next_state = convo.handle_npc_choice(target, choice_label, player)
                        if next_state == "INTERCEPT_MARKET_BRAWL":
                            selected_target = "market manager"
                            next_state = "NPC_DIALOGUE"
                        set_state(next_state, log_msg)
                        check_master_clock()
                    return cb
                col = idx % 3
                row = idx // 3
                # Override font size so it fits the narrower 3-column button
                buttons.append(Button((px + col * 162, py + row * 32, col_w, row_h), opt, make_cb(selected_target, opt), fixed_font=pygame.font.Font(None, 16)))


    elif menu_state == "CHAPTER_2_BOARD":
        options = get_eligible_chapter_2_routes(player) + ["< Step Back"]
        total_opts = len(options)
        if total_opts > 5:
            bh = max(24, (190 - (total_opts - 1) * vgap) // total_opts)

        def select_ch2_route(opt):
            global player
            player, log_msg, next_state = resolve_chapter_2_route(opt, player)
            if opt != "< Step Back":
                report_txt = export_playtest_report(f"CHAPTER 2 QUALIFIED: {opt}")
                beta_banner = (
                    f"{log_msg}\n\n"
                    "=========================================================\n"
                    "   CONGRATULATIONS! YOU COMPLETED THE CHAPTER 1 BETA!    \n"
                    "=========================================================\n"
                    "Your run telemetry has been saved to 'playtest_report.txt'.\n"
                    "Please send 'playtest_report.txt' to the developer with your feedback!\n\n"
                    f"{report_txt}"
                )
                set_state("CHAPTER_1_COMPLETE", beta_banner)
            else:
                set_state(next_state, log_msg)
            check_master_clock()

        for i, opt in enumerate(options):
            buttons.append(Button((px, py + i * (bh + vgap), bw, bh), opt, lambda o=opt: select_ch2_route(o)))

    elif menu_state == "MINIGAME_BRAWL":
        phase = player.get("brawl_phase", "STANDOFF")

        def exec_brawl(act):
            global player
            player, log_msg, next_state = ch2_union.brawl_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "STANDOFF":
            buttons.append(Button((85, 382, 305, 38), "Lock Arms & Raise Fists (Begin Brawl)", lambda: exec_brawl("lock_arms")))
            buttons.append(Button((410, 382, 305, 38), "Call Out to the Caligo Quarry Drivers", lambda: exec_brawl("shout_truth")))
            has_blade = any(i in player.get("inventory", []) for i in db.weapon_max_hit if i != "fists")
            if has_blade:
                buttons.append(Button((85, 428, 630, 34), "Draw Cold Steel to Clear the Road", lambda: exec_brawl("draw_weapon")))

        elif phase == "FIGHT":
            mom = player.get("brawl_momentum", 0)
            buttons.append(Button((85, 380, 305, 36), "Quick Jab Combination (Fast)", lambda: exec_brawl("jab")))
            buttons.append(Button((410, 380, 305, 36), "Brace & Counter-Parry (Read Swing)", lambda: exec_brawl("brace")))
            buttons.append(Button((85, 424, 305, 36), "Heavy Shoulder-Barge (1 Momentum)", lambda: exec_brawl("barge"), enabled=(mom >= 1)))
            buttons.append(Button((410, 424, 305, 36), "Grapple & Hurl into Flooded Ditch!", lambda: exec_brawl("ditch_toss")))

        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Barricade Standoff >>", lambda: exec_brawl("conclude")))

    elif menu_state == "MINIGAME_TRIBUNAL":
        phase = player.get("tribunal_phase", "ACTIVE")

        def exec_tribunal(act):
            global player
            player, log_msg, next_state = ch2_union.tribunal_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            pressed = player.get("tribunal_pressed", False)
            buttons.append(Button((85, 355, 630, 32), "1. Press Witness Under Oath for Specific Details", lambda: exec_tribunal("press"), enabled=(not pressed)))
            buttons.append(Button((85, 393, 305, 34), "Present: Mill-Axle & Sluice Forensics", lambda: exec_tribunal("forensics")))
            buttons.append(Button((410, 393, 305, 34), "Present: Riverbank & Taproom Testimony", lambda: exec_tribunal("testimony")))
            buttons.append(Button((85, 433, 305, 34), "Present: Craft & Masonry Demonstration", lambda: exec_tribunal("trade_demo")))
            buttons.append(Button((410, 433, 305, 34), "Present: Granary Foreclosure & Kickbacks", lambda: exec_tribunal("motive")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Hear Final Verdict >>", lambda: exec_tribunal("conclude")))

    elif menu_state == "MINIGAME_TRAITOR":
        phase = player.get("traitor_phase", "DELIBERATE")

        def exec_traitor(act):
            global player
            player, log_msg, next_state = ch2_union.traitor_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "DELIBERATE":
            buttons.append(Button((85, 368, 305, 32), "1. Cycle Accused Committee Member", lambda: exec_traitor("cycle_suspect")))
            buttons.append(Button((410, 368, 305, 32), "2. Cycle Lockbox Method", lambda: exec_traitor("cycle_method")))
            buttons.append(Button((85, 404, 305, 32), "3. Cycle Kokeshi Leak Channel", lambda: exec_traitor("cycle_leak")))
            buttons.append(Button((410, 404, 305, 32), "4. Cycle Where the 40 Silver Went", lambda: exec_traitor("cycle_motive")))
            buttons.append(Button((85, 442, 415, 34), "Present Formal Indictment to Murum Council >>", lambda: exec_traitor("submit_indictment")))
            buttons.append(Button((515, 442, 200, 34), "< Recess Inquiry", lambda: exec_traitor("leave_council")))
        else:
            buttons.append(Button((190, 410, 420, 42), "Conclude Tribunal & Enter Chapter 3 >>", lambda: exec_traitor("conclude")))

    elif menu_state == "MINIGAME_RIOT":
        phase = player.get("riot_phase", "ACTIVE")

        def exec_riot(act):
            global player
            player, log_msg, next_state = ch2_guard.riot_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            buttons.append(Button((85, 336, 305, 34), "Lock Overlapping Shields & Drum-Beat", lambda: exec_riot("lock_shields")))
            buttons.append(Button((410, 336, 305, 34), "Expose Fairlight's Theatrical Hoax!", lambda: exec_riot("expose_hoax")))
            buttons.append(Button((85, 376, 305, 34), "Open Cooperage Canal-Sluice Hydrant", lambda: exec_riot("flood_sluice")))
            buttons.append(Button((410, 376, 305, 34), "Measured Advance with Flat of Staves", lambda: exec_riot("measured_advance")))
            buttons.append(Button((85, 416, 630, 32), "Order Lethal Pike-Charge (Draws Blood — Costs Discipline & Rep!)", lambda: exec_riot("lethal_charge")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Riot Deployment >>", lambda: exec_riot("conclude")))

    elif menu_state == "MINIGAME_STRIKE_CORDON":
        phase = player.get("cordon_phase", "ACTIVE")
        beat = player.get("cordon_beat", 0)

        def exec_cordon(act):
            global player
            player, log_msg, next_state = ch2_guard.strike_cordon_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if beat == 0:
                buttons.append(Button((85, 336, 305, 36), "Form Double Watch Cordon (Neutral Zone)", lambda: exec_cordon("double_cordon")))
                buttons.append(Button((410, 336, 305, 36), "Halt Convoy for Customs & Axle Audit", lambda: exec_cordon("check_permits")))
                buttons.append(Button((85, 380, 305, 36), "Shove Strikers Back from the Hay-Wains", lambda: exec_cordon("push_strikers")))
                buttons.append(Button((410, 380, 305, 36), "Lock Iron Chains on the Kokeshi Wagons", lambda: exec_cordon("block_convoy")))
            elif beat == 1:
                buttons.append(Button((85, 336, 305, 36), "Intercept & Expose the Planted Blades!", lambda: exec_cordon("disarm_provocateur")))
                buttons.append(Button((410, 336, 305, 36), "Allow Fairlight's Satire to Cool the Crowd", lambda: exec_cordon("let_fairlight_play")))
                buttons.append(Button((85, 380, 630, 36), "Clear the Stage-Wagon by Force", lambda: exec_cordon("clear_stage")))
            elif beat == 2:
                buttons.append(Button((85, 336, 305, 36), "Signal Flank Pickets (Repel Raid & Lancers)", lambda: exec_cordon("secure_flanks")))
                buttons.append(Button((410, 336, 305, 36), "Form Tight Hollow Square Around Brazier", lambda: exec_cordon("shield_square")))
                buttons.append(Button((85, 380, 630, 36), "Split Watch Line to Chase Both Flanks", lambda: exec_cordon("split_line")))
            else:
                buttons.append(Button((85, 336, 630, 34), "Enforce Watch Arbitration (Impound Contraband & Open 1 Provision Lane)", lambda: exec_cordon("escort_truce")))
                buttons.append(Button((85, 376, 305, 34), "Force Barricade Open for Kokeshi Convoy", lambda: exec_cordon("clear_for_convoy")))
                buttons.append(Button((410, 376, 305, 34), "Arrest Kokeshi Escort & Uphold Blockade", lambda: exec_cordon("arrest_kokeshi")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Crossroads Deployment >>", lambda: exec_cordon("conclude")))

    elif menu_state == "MINIGAME_CONVOY":
        phase = player.get("convoy_phase", "ACTIVE")
        stage = player.get("convoy_stage", 0)

        def exec_convoy(act):
            global player
            player, log_msg, next_state = ch2_guard.convoy_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if stage == 0:
                buttons.append(Button((85, 350, 305, 40), "March in Tight Halberd Screen (2d6)", lambda: exec_convoy("steady_screen")))
                buttons.append(Button((410, 350, 305, 40), "Sweep Roadside Gorse with Outriders (2d6)", lambda: exec_convoy("outrider_sweep")))
            elif stage == 1:
                buttons.append(Button((85, 350, 305, 40), "Spring Counter-Ambush on High Bank! (2d6)", lambda: exec_convoy("counter_ambush")))
                buttons.append(Button((410, 350, 305, 40), "Form Shield-Tortoise Around Coach (2d6)", lambda: exec_convoy("shield_tortoise")))
            else:
                buttons.append(Button((85, 350, 305, 40), "Expose Laydere Poison & Swap Flagon! (2d6)", lambda: exec_convoy("foil_poison")))
                buttons.append(Button((410, 350, 305, 40), "Stand Silent Honour-Guard by Table (2d6)", lambda: exec_convoy("stand_guard")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Ragmore Escort >>", lambda: exec_convoy("conclude")))

    elif menu_state == "MINIGAME_WATCH_SPLIT":
        phase = player.get("split_phase", "UNITY")
        addressed = player.get("split_addressed", [])

        def exec_split(act):
            global player
            player, log_msg, next_state = ch2_guard.watch_split_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "UNITY":
            buttons.append(Button((85, 350, 305, 34), "Address Ælfwine's Rank-and-File (2d6)", lambda: exec_split("rally_rank"), enabled=("rally_rank" not in addressed)))
            buttons.append(Button((410, 350, 305, 34), "Address Cenric's Frontier Garrison (2d6)", lambda: exec_split("rally_quartermaster"), enabled=("rally_quartermaster" not in addressed)))
            buttons.append(Button((85, 390, 305, 34), "Address Beornraed's Veterans (2d6)", lambda: exec_split("rally_veterans"), enabled=("rally_veterans" not in addressed)))
            buttons.append(Button((410, 390, 305, 34), "Proceed to Final Banner Vote >>", lambda: exec_split("proceed_banner")))
        else:
            buttons.append(Button((85, 365, 305, 44), "Declare for Castle Ragmore (Loyalist)", lambda: exec_split("declare_ragmore")))
            buttons.append(Button((410, 365, 305, 44), "Defect & Join Castle Laydere (Rebel)", lambda: exec_split("declare_laydere")))

    elif menu_state == "MINIGAME_HERDING":
        phase = player.get("herd_phase", "ACTIVE")
        beat = player.get("herd_beat", 0)

        def exec_herd(act):
            global player
            player, log_msg, next_state = ch2_castellan.herding_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if beat == 0:
                buttons.append(Button((85, 340, 305, 36), "Gallop Outriders Along Cliff-Rim (2d6)", lambda: exec_herd("flank_cliff")))
                buttons.append(Button((410, 340, 305, 36), "Sound Communard Woodland Horn-Call (2d6)", lambda: exec_herd("horn_cadence")))
                buttons.append(Button((85, 384, 630, 34), "Loose Crossbow Volley into Lead Stags (Draws Blood!)", lambda: exec_herd("cull_herd")))
            elif beat == 1:
                buttons.append(Button((85, 340, 305, 36), "Part Riders into Parallel Chutes (2d6)", lambda: exec_herd("part_lanes")))
                buttons.append(Button((410, 340, 305, 36), "Scatter Cobnuts / Oats Downwind (2d6)", lambda: exec_herd("toss_cobnuts")))
                buttons.append(Button((85, 384, 630, 34), "Meet Charging Boars with Levelled Spears", lambda: exec_herd("spear_wall")))
            elif beat == 2:
                buttons.append(Button((85, 340, 305, 36), "Guide Stags Through Cleared Hedge-Gap!", lambda: exec_herd("clear_scent")))
                buttons.append(Button((410, 340, 305, 36), "Crack Stock-Whips Upwind of Herd (2d6)", lambda: exec_herd("windward_drive")))
                buttons.append(Button((85, 384, 630, 34), "Force Herd Straight Into Reeking Hedge", lambda: exec_herd("force_hedge")))
            else:
                buttons.append(Button((85, 340, 305, 36), "Present Laydere Wolf-Gall Stakes!", lambda: exec_herd("expose_laydere")))
                buttons.append(Button((410, 340, 305, 36), "Weave Wattle-Fence & Open Deer-Stile (2d6)", lambda: exec_herd("wattled_gate")))
                buttons.append(Button((85, 384, 630, 34), "Stake Iron Wolf-Traps Along Treeline", lambda: exec_herd("iron_traps")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Report to Castellan Hrothgar >>", lambda: exec_herd("conclude")))

    elif menu_state == "MINIGAME_HUNT":
        phase = player.get("hunt_phase", "ACTIVE")
        stage = player.get("hunt_stage", 0)

        def exec_hunt(act):
            global player
            player, log_msg, next_state = ch2_castellan.hunt_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if stage == 0:
                buttons.append(Button((85, 340, 305, 36), "Steer Down Unmarked Mossy Deer-Run (2d6)", lambda: exec_hunt("take_moss")))
                buttons.append(Button((410, 340, 305, 36), "Take the Lichen-Slashed Oak Trail (2d6)", lambda: exec_hunt("take_lichen")))
                buttons.append(Button((85, 384, 630, 34), "Chart Off-Trail Bearing by Compass (2d6)", lambda: exec_hunt("compass_cut")))
            elif stage == 1:
                buttons.append(Button((85, 340, 305, 36), "Seize Hrothgar's Rein & Halt Before Gorge!", lambda: exec_hunt("halt_deadfall")))
                buttons.append(Button((410, 340, 305, 36), "Shoot Counterweight Vine with Longbow!", lambda: exec_hunt("loose_warning_arrow")))
                buttons.append(Button((85, 384, 630, 34), "Spur Horses Full-Gallop Through Gorge", lambda: exec_hunt("gallop_through")))
            else:
                buttons.append(Button((85, 340, 305, 36), "Dismount & Parley Timber-Boundary Truce!", lambda: exec_hunt("parley_truce")))
                buttons.append(Button((410, 340, 305, 36), "Present Laydere Wolf-Gall Stakes to Elders!", lambda: exec_hunt("expose_laydere_poachers")))
                buttons.append(Button((85, 384, 630, 34), "Form Boar-Spear Ring & Fight Out!", lambda: exec_hunt("fight_glade")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Return to Castle Ragmore >>", lambda: exec_hunt("conclude")))

    elif menu_state == "MINIGAME_LANCERS":
        phase = player.get("lancer_phase", "ACTIVE")
        step = player.get("lancer_step", 0)

        def exec_lancers(act):
            global player
            player, log_msg, next_state = ch2_castellan.lancers_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if step == 0:
                buttons.append(Button((85, 340, 305, 36), "Wheel Across Eastern Oat-Furrow Ridge (2d6)", lambda: exec_lancers("eastern_ridge")))
                buttons.append(Button((410, 340, 305, 36), "Charge Down Sunken Sluice-Gate Lane (2d6)", lambda: exec_lancers("sunken_lane")))
                buttons.append(Button((85, 384, 630, 34), "Dismount Vanguard Scouts to Sound Ditches", lambda: exec_lancers("scout_ditch")))
            elif step == 1:
                buttons.append(Button((85, 340, 305, 36), "Demand & Audit Kokeshi Toll-Charters (2d6)", lambda: exec_lancers("audit_kokeshi")))
                buttons.append(Button((410, 340, 305, 36), "Array Lancers & Summon Both Leaders (2d6)", lambda: exec_lancers("summon_leaders")))
                buttons.append(Button((85, 384, 630, 34), "Couch Lances & Trample the Hay-Wains!", lambda: exec_lancers("couch_lances")))
            else:
                buttons.append(Button((85, 340, 630, 36), "Invoke Feudal Eminent Domain (Impound Contraband & Grant Safe-Conduct!)", lambda: exec_lancers("eminent_domain")))
                buttons.append(Button((85, 384, 305, 34), "Enforce Iron Grain-Levy at Lance-Point", lambda: exec_lancers("iron_levy")))
                buttons.append(Button((410, 384, 305, 34), "Withdraw Lancers to Ragmore", lambda: exec_lancers("withdraw")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Return to Castle Ragmore >>", lambda: exec_lancers("conclude")))

    elif menu_state == "MINIGAME_SUMMIT":
        phase = player.get("summit_phase", "ACTIVE")
        course = player.get("summit_course", 0)

        def exec_summit(act):
            global player
            player, log_msg, next_state = ch2_castellan.summit_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if course == 0:
                buttons.append(Button((85, 340, 305, 36), "Seat Mayor on Equal Velvet Dais (2d6)", lambda: exec_summit("equal_dais")))
                buttons.append(Button((410, 340, 305, 36), "Lavish Dishes on Murum Aldermen (2d6)", lambda: exec_summit("flatter_mayor")))
                buttons.append(Button((85, 384, 630, 34), "Seat Town Delegation Below Baronial Knights", lambda: exec_summit("below_salt")))
            elif course == 1:
                buttons.append(Button((85, 340, 305, 36), "Ambush Spy Behind Barred Tapestry! (2d6)", lambda: exec_summit("trap_spy")))
                buttons.append(Button((410, 340, 305, 36), "Post Halberdiers Before Map-Room Arch", lambda: exec_summit("double_sentries")))
                buttons.append(Button((85, 384, 630, 34), "Ignore Gallery & Focus on High Table", lambda: exec_summit("ignore_spy")))
            else:
                buttons.append(Button((85, 340, 630, 36), "Pour Spiced Cider & Expose Laydere Poisoned Vintage! (2d6)", lambda: exec_summit("serve_cider_expose")))
                buttons.append(Button((85, 384, 305, 34), "Allow Dark Brumaire Vintage Toast", lambda: exec_summit("pour_brumaire")))
                buttons.append(Button((410, 384, 305, 34), "Smash Goblet Without Proof", lambda: exec_summit("smash_goblet")))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Summit Banquet >>", lambda: exec_summit("conclude")))

    elif menu_state == "MINIGAME_LEVY":
        phase = player.get("levy_phase", "ACTIVE")
        step = player.get("levy_step", 0)

        def exec_levy(act):
            global player
            player, log_msg, next_state = ch2_castellan.levy_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            if step == 0:
                buttons.append(Button((85, 340, 305, 36), "Issue Inspected Reserve Steel! (2d6)", lambda: exec_levy("issue_reserve_steel")))
                buttons.append(Button((410, 340, 305, 36), "Purchase Emergency Guild Arms (25s)", lambda: exec_levy("buy_guild_arms")))
                buttons.append(Button((85, 384, 630, 34), "March With Unchecked Contractor Spears", lambda: exec_levy("unchecked_spears")))
            elif step == 1:
                buttons.append(Button((85, 340, 305, 36), "Roll Audited Tithe-Barn Wagons! (2d6)", lambda: exec_levy("roll_tithe_wagons")))
                buttons.append(Button((410, 340, 305, 36), "Issue Silver Promissory Notes for Grain", lambda: exec_levy("fair_commissary")))
                buttons.append(Button((85, 384, 630, 34), "Seize Tenant Seed-Barley by Force", lambda: exec_levy("seize_grain")))
            else:
                buttons.append(Button((85, 340, 305, 36), "Invoke Realm Charter & Chivalric Oath!", lambda: exec_levy("sage_or_charter")))
                buttons.append(Button((410, 340, 305, 36), "Lead First Cavalry Charge Yourself! (2d6)", lambda: exec_levy("lead_vanguard")))
                buttons.append(Button((85, 384, 630, 34), "Threaten Gentry With Estate Forfeiture", lambda: exec_levy("threaten_gentry")))
        else:
            buttons.append(Button((190, 405, 420, 42), "March to War (Enter Chapter 3) >>", lambda: exec_levy("conclude")))

    elif menu_state == "MINIGAME_DUNGEON":
        d_key = player.get("dungeon_key", "parvus_catacombs")
        spec = ch2_dungeons.DUNGEON_SPECS[d_key]
        rm_idx = player.get("dungeon_room", 0)
        rm = spec["rooms"][rm_idx]

        def exec_dung(act):
            global player
            player, log_msg, next_state = ch2_dungeons.dungeon_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if rm["type"] in ("ENTRANCE", "TRAP"):
            buttons.append(Button((85, 336, 630, 32), rm["opt_a"][0], lambda: exec_dung("opt_a")))
            buttons.append(Button((85, 373, 630, 32), rm["opt_b"][0], lambda: exec_dung("opt_b")))
            buttons.append(Button((85, 410, 415, 32), rm["opt_c"][0], lambda: exec_dung("opt_c")))
            buttons.append(Button((515, 410, 200, 32), "< Retreat Up Steps", lambda: exec_dung("retreat_dungeon")))

        elif rm["type"] == "PUZZLE":
            buttons.append(Button((85, 338, 200, 34), "Cycle Left Dial (1)", lambda: exec_dung("dial_0")))
            buttons.append(Button((300, 338, 200, 34), "Cycle Center Dial (2)", lambda: exec_dung("dial_1")))
            buttons.append(Button((515, 338, 200, 34), "Cycle Right Dial (3)", lambda: exec_dung("dial_2")))
            buttons.append(Button((85, 382, 415, 38), "Pull Master Bulkhead Lever! >>", lambda: exec_dung("pull_master_lever")))
            buttons.append(Button((515, 382, 200, 38), "< Retreat", lambda: exec_dung("retreat_dungeon")))

        elif rm["type"] == "COMBAT":
            mom = player.get("dungeon_momentum", 1)
            buttons.append(Button((85, 336, 305, 36), "Quick Thrust / Interrupt Rush (2d6)", lambda: exec_dung("strike_fast")))
            buttons.append(Button((410, 336, 305, 36), "Parry Cleave & Riposte! (2d6)", lambda: exec_dung("parry_counter")))
            buttons.append(Button((85, 378, 305, 36), "Crushing Guard-Breaker (1 Momentum)", lambda: exec_dung("heavy_cleave"), enabled=(mom >= 1)))
            buttons.append(Button((410, 378, 305, 36), "Grapple & Slam into Stone Pillar! (2d6)", lambda: exec_dung("pillar_slam")))
            buttons.append(Button((290, 420, 220, 30), "< Flee Dungeon", lambda: exec_dung("retreat_dungeon")))

        else:
            buttons.append(Button((165, 385, 470, 44), "Claim Vault Treasures & Complete Delve >>", lambda: exec_dung("claim_vault")))

    elif menu_state == "MINIGAME_SEARCH":
        import search_engine
        phase = player.get("search_phase", "SELECT_FEATURE")
        spec = player.get("search_spec", {})
        features = spec.get("features", [])
        style = search_engine.get_search_style(player)
        inv = player.get("inventory", [])

        def exec_srch(act, payload=None):
            global player
            player, log_msg, next_state = search_engine.search_modal_action(act, payload, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "SELECT_FEATURE":
            if style == "CLASSIC":
                # Classic Mode: 4 full-width feature buttons
                y_off = 225
                for ft in features[:4]:
                    buttons.append(Button((85, y_off, 630, 34), ft[0], lambda fk=ft[1]: exec_srch("pick_feature", fk)))
                    y_off += 42
                if "looking glass" in inv and spec.get("spyglass_feature"):
                    s_ft = spec["spyglass_feature"]
                    buttons.append(Button((85, y_off, 630, 34), f"[Looking Glass] {s_ft[0]}", lambda fk=s_ft[1]: exec_srch("pick_feature", fk)))
            else:
                # Architectural Mode: Click directly on the Blueprint hotspots above, or use compact quick-buttons below!
                for idx, ft in enumerate(features[:4]):
                    bx = 85 + (idx % 2) * 320
                    by = 366 + (idx // 2) * 36
                    buttons.append(Button((bx, by, 310, 30), f"[{idx+1}] {ft[0][:34]}", lambda fk=ft[1]: exec_srch("pick_feature", fk)))

            # Bottom Utility Bar: Looking Glass Toggle + View Mode Switch [TAB] + Cancel
            has_glass = "looking glass" in inv
            buttons.append(Button(
                (85, 444, 205, 34),
                "Looking Glass: ON" if player.get("search_tool_mode") == "SPYGLASS" else "Use Looking Glass",
                lambda: exec_srch("toggle_spyglass"),
                enabled=has_glass
            ))
            buttons.append(Button(
                (300, 444, 215, 34),
                f"View: {style.title()} [TAB]",
                lambda: exec_srch("toggle_style")
            ))
            buttons.append(Button((525, 444, 190, 34), "< Leave Search", lambda: exec_srch("cancel")))

        elif phase == "INTERACT_METHOD":
            # Tier 2 Tool & Optical Bar (Works in both Classic & Architectural!)
            y_base = 366 if style == "ARCHITECTURAL" else 240
            buttons.append(Button((85, y_base, 308, 34), "1. Visual Sweep (Safe, 10m)", lambda: exec_srch("tool", "sweep")))
            buttons.append(Button((407, y_base, 308, 34), "2. Rummage (15m, 2d6 Risk/Loot)", lambda: exec_srch("tool", "rummage")))

            buttons.append(Button((85, y_base + 40, 200, 34), "3. Prying Tool (10m)", lambda: exec_srch("tool", "tool")))
            buttons.append(Button(
                (295, y_base + 40, 210, 34),
                "4. Microscope (20x)",
                lambda: exec_srch("tool", "microscope"),
                enabled=("brass microscope" in inv)
            ))
            buttons.append(Button(
                (515, y_base + 40, 200, 34),
                "5. Skeleton Key!",
                lambda: exec_srch("tool", "skeleton_key"),
                enabled=("skeleton key" in inv)
            ))
            buttons.append(Button((240, y_base + 82, 320, 32), "< Inspect Another Feature", lambda: exec_srch("back")))

        else:
            buttons.append(Button((190, 440, 420, 42), "Conclude Investigation >>", lambda: exec_srch("conclude", None)))

    elif menu_state == "MINIGAME_PARVUS":
        phase = player.get("pv_phase", "ACTIVE")
        code = player.get("pv_code", "4a")
        scen = ch2_parvus.PARVUS_SCENARIOS[code]
        st_idx = min(2, player.get("pv_stage", 0))
        opts = scen["stages"][st_idx]["opts"]

        def exec_pv(idx):
            global player
            player, log_msg, next_state = ch2_parvus.parvus_action(idx, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            buttons.append(Button((85, 336, 630, 34), opts[0][0], lambda: exec_pv(0)))
            buttons.append(Button((85, 376, 630, 34), opts[1][0], lambda: exec_pv(1)))
            buttons.append(Button((85, 416, 630, 34), opts[2][0], lambda: exec_pv(2)))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Operation >>", lambda: exec_pv(0)))

    elif menu_state == "MINIGAME_ELECTION":
        phase = player.get("el_phase", "ACTIVE")
        code = player.get("el_code", "7a")
        scen = ch2_election.ELECTION_SCENARIOS[code]
        st_idx = min(2, player.get("el_stage", 0))
        opts = scen["stages"][st_idx]["opts"]

        def exec_el(idx):
            global player
            player, log_msg, next_state = ch2_election.election_action(idx, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            buttons.append(Button((85, 336, 630, 34), opts[0][0], lambda: exec_el(0)))
            buttons.append(Button((85, 376, 630, 34), opts[1][0], lambda: exec_el(1)))
            buttons.append(Button((85, 416, 630, 34), opts[2][0], lambda: exec_el(2)))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Mission >>", lambda: exec_el(0)))

    elif menu_state == "MINIGAME_ROGUERY":
        phase = player.get("rg_phase", "ACTIVE")
        code = player.get("rg_code", "9a")
        scen = ch2_roguery.ROGUERY_SCENARIOS[code]
        st_idx = min(2, player.get("rg_stage", 0))
        opts = scen["stages"][st_idx]["opts"]

        def exec_rg(idx):
            global player
            player, log_msg, next_state = ch2_roguery.roguery_action(idx, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        if phase == "ACTIVE":
            buttons.append(Button((85, 336, 630, 34), opts[0][0], lambda: exec_rg(0)))
            buttons.append(Button((85, 376, 630, 34), opts[1][0], lambda: exec_rg(1)))
            buttons.append(Button((85, 416, 630, 34), opts[2][0], lambda: exec_rg(2)))
        else:
            buttons.append(Button((190, 405, 420, 42), "Conclude Mission >>", lambda: exec_rg(0)))

    elif menu_state == "MINIGAME_CODEWHEEL":

        def exec_cw(act):
            global player
            player, log_msg, next_state = cryptography_engine.codewheel_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        buttons.append(Button((85, 365, 200, 40), "< Rotate Inner Ring Left", lambda: exec_cw("left")))
        buttons.append(Button((300, 365, 200, 40), "Rotate Inner Ring Right >", lambda: exec_cw("right")))
        buttons.append(Button((515, 365, 200, 40), "Close Wheel", lambda: exec_cw("close")))
        buttons.append(Button((165, 420, 470, 42), "Lock In Decoded Message >>", lambda: exec_cw("submit")))

    elif menu_state == "MINIGAME_PONTIFEX":
        step = player.get("pf_step", 0)

        def exec_pf(act):
            global player
            player, log_msg, next_state = cryptography_engine.pontifex_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        if step < 4:
            buttons.append(Button((85, 350, 305, 38), "1. Move Joker A Down 1 Card", lambda: exec_pf("step_ja"), enabled=(step == 0)))
            buttons.append(Button((410, 350, 305, 38), "2. Move Joker B Down 2 Cards", lambda: exec_pf("step_jb"), enabled=(step == 1)))
            buttons.append(Button((85, 400, 305, 38), "3. Triple Cut Around Jokers", lambda: exec_pf("step_triple"), enabled=(step == 2)))
            buttons.append(Button((410, 400, 305, 38), "4. Bottom-Card Count Cut", lambda: exec_pf("step_count"), enabled=(step == 3)))
        else:
            buttons.append(Button((165, 385, 470, 44), "Claim Decoded Pontifex Dispatch >>", lambda: exec_pf("claim")))

    elif menu_state == "MINIGAME_GCHQ":
        puz = cryptography_engine.GCHQ_PUZZLES[player.get("gchq_idx", 0)]

        def exec_gchq(idx):
            global player
            player, log_msg, next_state = cryptography_engine.gchq_action(idx, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        for i, (lbl, _) in enumerate(puz["options"]):
            buttons.append(Button((85, 332 + i * 40, 630, 34), lbl, lambda idx=i: exec_gchq(idx)))
        buttons.append(Button((290, 456, 220, 30), "< Leave Postbox", lambda: exec_gchq(-1)))

    elif menu_state == "MINIGAME_TYPESET":

        def exec_ts(act):
            global player
            player, log_msg, next_state = printing_press_engine.typeset_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)
            check_master_clock()

        buttons.append(Button((85, 422, 195, 36), "1. Ink Forme", lambda: exec_ts("ink")))
        buttons.append(Button((290, 422, 215, 36), "2. Pull Press Lever!", lambda: exec_ts("pull_lever")))
        buttons.append(Button((515, 422, 200, 36), "Clear Type-Stick", lambda: exec_ts("clear")))
        buttons.append(Button((85, 466, 420, 38), "3. Distribute Pamphlets in Street >>", lambda: exec_ts("distribute")))
        buttons.append(Button((515, 466, 200, 38), "< Close Press", lambda: exec_ts("close")))

    elif menu_state == "MINIGAME_DEBATE":
        def exec_debate(idx):
            global player
            player, log_msg, next_state = mini_games.debate_action(idx, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        phase = player.get("debate_phase", "BRIEFING")
        if phase == "BRIEFING":
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Begin 5-Point Persuasion >>", lambda: exec_debate(0)))
        elif phase == "RESULT":
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Conclude Parley >>", lambda: exec_debate(0)))
        else:
            rnd = player.get("debate_round", 1)
            stages = player.get("debate_stages", [])
            if 1 <= rnd <= len(stages):
                for i, opt_tuple in enumerate(stages[rnd - 1]["options"]):
                    opt_text = opt_tuple[0]
                    buttons.append(Button((m_px, m_py + i * (bh + vgap), m_bw, bh), opt_text, lambda idx=i: exec_debate(idx)))

    elif menu_state == "MINIGAME_BARGAIN":
        phase = player.get("bargain_phase", "DOCKET")

        def exec_bargain(act, val=None):
            global player
            player, log_msg, next_state = mini_games.bargain_action(act, val, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        if phase == "DOCKET":
            # Map invisible click zones directly over the 2 columns of 5 rows in the pop-out!
            for i in range(5):
                for col_idx, d in enumerate([mini_games.BARGAIN_DEMANDS[i], mini_games.BARGAIN_DEMANDS[i + 5]]):
                    rx = 85 if col_idx == 0 else 415
                    ry = 146 + i * 42
                    d_id = d["id"]
                    buttons.append(Button((rx, ry, 295, 36), "", lambda item_id=d_id: exec_bargain("select_demand", item_id), invisible=True))

            settled_cnt = sum(1 for v in player.get("bargain_settled", {}).values() if v)
            conclude_lbl = f"Sign & Seal Fluvius Charter ({settled_cnt}/10 Settled)"
            buttons.append(Button((85, 438, 415, 36), conclude_lbl, lambda: exec_bargain("conclude"), enabled=(settled_cnt == 10)))
            buttons.append(Button((515, 438, 200, 36), "< Adjourn Parley", lambda: exec_bargain("leave_table")))

        elif phase == "SLIDER_PLAYER":
            buttons.append(Button((130, 251, 55, 34), "-", lambda: exec_bargain("step_minus")))
            buttons.append(Button((615, 251, 55, 34), "+", lambda: exec_bargain("step_plus")))
            buttons.append(Button((150, 350, 280, 40), "Submit Offer to Seekgrace", lambda: exec_bargain("submit_offer")))
            buttons.append(Button((450, 350, 200, 40), "< Back to Docket", lambda: exec_bargain("back_docket")))

    elif menu_state == "MINIGAME_TRACK_TABLE":

        def exec_unseal():
            global player
            player, msg = meta_progression.unlock_next_ledger_line_with_research(player)
            add_log(msg)

        buttons.append(Button((85, 476, 310, 36), "Unseal Next Locked Line (5 Silver)", exec_unseal))
        buttons.append(Button((415, 476, 300, 36), "Close Career Ledger", lambda: set_state("MAIN")))

    elif menu_state == "MINIGAME_DRILL":
        def exec_drill(act):
            global player
            player, log_msg, next_state = mini_games.drill_action(act, player)
            if log_msg: add_log(log_msg)
            set_state(next_state)

        phase = player.get("drill_phase", "BRIEFING")
        if phase == "BRIEFING":
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Step Into Line & Begin Drill >>", lambda: exec_drill("start")))
        else:
            # Only allow clicking if the bar is actively sweeping!
            is_active = (phase == "SWEEPING")
            buttons.append(Button((m_px, m_py, m_bw, bh), "HIGH GUARD!", lambda: exec_drill("HIGH GUARD!"), enabled=is_active))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "THRUST!", lambda: exec_drill("THRUST!"), enabled=is_active))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "SWEEP!", lambda: exec_drill("SWEEP!"), enabled=is_active))
            buttons.append(Button((m_px, m_py + (bh + vgap)*3, m_bw, bh), "SHIELD WALL!", lambda: exec_drill("SHIELD WALL!"), enabled=is_active))

    elif menu_state == "MINIGAME_FORGE":
        def execute_forge(action):
            global player
            player, log_msg, next_state = mini_games.forge_action(action, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        buttons.append(Button((m_px, m_py, m_bw, bh), "Pump Bellows (Too Cold)", lambda: execute_forge("pump")))
        buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Add Coal (Perfect)", lambda: execute_forge("coal")))
        buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Wait (Too Hot)", lambda: execute_forge("wait")))
        if player.get("arcade_mode"):
            buttons.append(Button((m_px, m_py + (bh + vgap)*3, m_bw, 28), "< Quit Practice", open_arcade_menu))

    elif menu_state == "MINIGAME_CHASE":
        def execute_chase(direction):
            global player, selected_target
            player, log_msg, next_state = mini_games.chase_action(direction, player)
            if log_msg:
                add_log(log_msg)
            if next_state == "NPC_DIALOGUE":
                selected_target = "market manager"
            set_state(next_state)

        buttons.append(Button((m_px, m_py, m_bw, bh), "<< Cut Left (Dart Left)", lambda: execute_chase("left")))
        buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "^^ Sprint Straight (Straight)", lambda: execute_chase("straight")))
        buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Cut Right (Shot Right) >>", lambda: execute_chase("right")))
        if player.get("arcade_mode"):
            buttons.append(Button((m_px, m_py + (bh + vgap)*3, m_bw, 28), "< Quit Practice", open_arcade_menu))

    elif menu_state == "MINIGAME_JIGSAW":
        target_back = "ARCADE_MENU" if player.get("arcade_mode") else "MAIN"
        buttons.append(Button((m_px, 448, m_bw, 34), "< Leave Blueprint", lambda: set_state(target_back)))

    elif menu_state == "MINIGAME_SOUNDING":
        if player.get("arcade_mode"):
            buttons.append(Button((m_px, m_py + (bh + vgap)*3, m_bw, 28), "< Quit Practice", open_arcade_menu))
        def exec_sounding(act):
            global player
            player, log_msg, next_state = mini_games.sounding_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        tool_label = f"Tool: {player.get('sounding_tool', 'hammer').title()} (Switch)"
        buttons.append(Button((m_px, m_py, m_bw, bh), tool_label, lambda: exec_sounding("toggle_tool")))
        buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Wipe Chalk Off Wall", lambda: exec_sounding("wipe_chalk")))

        if not player.get("sounding_recorded"):
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Record Flaw in Ledger", lambda: exec_sounding("record_ledger")))
        else:
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Leave Wall Sector >>", lambda: exec_sounding("finish_sector")))

    elif menu_state == "MINIGAME_BREACH":
        def exec_breach(act):
            global player
            player, log_msg, next_state = mini_games.breach_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        buttons.append(Button((m_px, m_py, m_bw, bh), "Rotate Selected Stone (R-Click)", lambda: exec_breach("rotate")))
        buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Check Architect's Note", lambda: exec_breach("inspect_niche")))
        buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "< Pause Repair", lambda: set_state("MAIN")))

    elif menu_state == "MINIGAME_DEDUCTION":
        def exec_deduct(act):
            global player
            player, log_msg, next_state = mini_games.deduction_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        if player.get("deduction_phase") == "deduce":
            buttons.append(Button((m_px, m_py, m_bw, bh), "Inspect Surveyor Cubbies (Clues)", lambda: exec_deduct("cubbies")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Read Torn Field Notes (Clues)", lambda: exec_deduct("notes")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Verify True Ledger >>", lambda: exec_deduct("verify")))
        else:
            buttons.append(Button((m_px, m_py, m_bw, bh), "Reset Chits to True Ledger", lambda: exec_deduct("reset_sabotage")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Review Field Notes", lambda: exec_deduct("notes")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Submit Final Ledger >>", lambda: exec_deduct("submit_final")))

    elif menu_state == "MINIGAME_PARAPET":
        def exec_parapet(act):
            global player
            player, log_msg, next_state = mini_games.parapet_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        target_back = "ARCADE_MENU" if player.get("arcade_mode") else "MAIN"
        if player.get("parapet_phase") == "stairs":
            shutter_lbl = "Lantern Shutter: OPEN (Click to Close)" if player.get("lantern_open") else "Lantern Shutter: CLOSED (Click to Open)"
            buttons.append(Button((m_px, m_py, m_bw, bh), shutter_lbl, lambda: exec_parapet("toggle_lantern")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Climb Next Step >>", lambda: exec_parapet("climb_step")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "< Step Back Outside", lambda: set_state(target_back)))
        else:
            buttons.append(Button((m_px, m_py, m_bw, bh), "Reset Stone Pins", lambda: exec_parapet("reset_klotski")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Force Cache Loose (+1 Mistake)", lambda: exec_parapet("force_cache")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "< Leave Parapet", lambda: set_state(target_back)))

    elif menu_state == "MINIGAME_SMUGGLE":
        def exec_smuggle(act):
            global player
            player, log_msg, next_state = mini_games.smuggle_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        phase = player.get("smuggle_phase", "contact")
        if phase == "contact":
            buttons.append(Button((m_px, m_py, m_bw, bh), "Tap Light Chisel [ . ]", lambda: exec_smuggle("light")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Strike Heavy Hammer [ - ]", lambda: exec_smuggle("heavy")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Wipe Brow & Wait for Patrol", lambda: exec_smuggle("wait_patrol")))
        elif phase == "route":
            buttons.append(Button((m_px, m_py, m_bw, bh), "Over the Wall (North Tower)", lambda: exec_smuggle("over")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Through the Wall (East Cavity)", lambda: exec_smuggle("through")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Under the Wall (Sluice Gate)", lambda: exec_smuggle("under")))
        else:
            buttons.append(Button((m_px, m_py, m_bw, bh), "1. Advance Silk Parcel (Clear)", lambda: exec_smuggle("advance")))
            buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "2. Freeze in Shadows (Sentry)", lambda: exec_smuggle("freeze")))
            buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "3. Ease & Camouflage (Snag)", lambda: exec_smuggle("camouflage")))

    elif menu_state == "MINIGAME_RECIPE":
        def exec_recipe(act):
            global player
            player, log_msg, next_state = mini_games.recipe_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        ing_name = mini_games.RECIPE_INGREDIENTS[player.get("recipe_ing_idx", 0)]
        qty_val = player.get("recipe_qty", 1)
        buttons.append(Button((m_px, m_py, m_bw, bh), f"Reagent: {ing_name} (Cycle)", lambda: exec_recipe("cycle_ing")))
        buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), f"Measure: {qty_val} dram(s) (Cycle 1-4)", lambda: exec_recipe("cycle_qty")))
        buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Add to Cauldron >>", lambda: exec_recipe("add_cauldron")))

    elif menu_state == "MINIGAME_FLYTIP":
        def exec_flytip(act):
            global player
            player, log_msg, next_state = mini_games.flytip_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        target_back = "ARCADE_MENU" if player.get("arcade_mode") else "MAIN"
        buttons.append(Button((m_px, m_py, m_bw, bh), "Inspect Rubbish Heaps (Clues)", lambda: exec_flytip("heaps")))
        buttons.append(Button((m_px, m_py + bh + vgap, m_bw, bh), "Question Stall Alibis (Clues)", lambda: exec_flytip("alibis")))
        buttons.append(Button((m_px, m_py + (bh + vgap)*2, m_bw, bh), "Issue Citations >>", lambda: exec_flytip("verify")))
        buttons.append(Button((m_px, m_py + (bh + vgap)*3, m_bw, bh), "< Pause & Return", lambda: set_state(target_back)))

    elif menu_state == "MINIGAME_ARCHERY":
        def exec_arch(act):
            global player
            player, log_msg, next_state = mini_games.archery_button_action(act, player)
            if log_msg:
                add_log(log_msg)
            set_state(next_state)

        by, bh_tray = 523, 36
        target_back = open_arcade_menu if player.get("arcade_mode") else (lambda: set_state("MAIN"))
        if not player.get("archery_drawn"):
            buttons.append(Button((140, by, 340, bh_tray), "Draw Longbow (SPACE / Click Target)", lambda: exec_arch("draw")))
            buttons.append(Button((500, by, 230, bh_tray), "< Step Away from Range", target_back))
        else:
            buttons.append(Button((38, by, 185, bh_tray), "LOOSE! (SPACE)", lambda: exec_arch("loose")))
            buttons.append(Button((230, by, 72, bh_tray), "< Left", lambda: exec_arch("nudge_left")))
            buttons.append(Button((307, by, 68, bh_tray), "^ Up", lambda: exec_arch("nudge_up")))
            buttons.append(Button((380, by, 72, bh_tray), "v Down", lambda: exec_arch("nudge_down")))
            buttons.append(Button((457, by, 76, bh_tray), "Right >", lambda: exec_arch("nudge_right")))
            buttons.append(Button((540, by, 105, bh_tray), "Relax Bow", lambda: exec_arch("relax")))
            buttons.append(Button((652, by, 110, bh_tray), "< Leave", target_back))

    elif menu_state == "CH2_TRIAL":
        opts = chapter_2.get_trial_options(player)
        if len(opts) <= 5:
            row_h = 34 if len(opts) == 5 else 36
            gap = 4 if len(opts) == 5 else 5
            for idx, opt in enumerate(opts):
                def make_trial_cb(choice_str=opt):
                    def _cb():
                        global player
                        player, log_msg, next_state = chapter_2.resolve_trial_choice(choice_str, player)
                        set_state(next_state, log_msg)
                        check_master_clock()
                    return _cb
                buttons.append(Button((px, py + idx * (row_h + gap), bw, row_h), opt, make_trial_cb(opt)))
        else:
            col_w, row_h = 235, 32
            for idx, opt in enumerate(opts):
                col = idx % 2
                row = idx // 2
                def make_trial_cb(choice_str=opt):
                    def _cb():
                        global player
                        player, log_msg, next_state = chapter_2.resolve_trial_choice(choice_str, player)
                        set_state(next_state, log_msg)
                        check_master_clock()
                    return _cb
                buttons.append(Button((px + col * 245, py + row * 36, col_w, row_h), opt, make_trial_cb(opt)))

    elif menu_state == "COMBAT":
        def attack_cb():
            global player
            player, log_msg, next_state = encounters.combat_round(player)
            set_state(next_state, log_msg)
            check_master_clock()

        def flee_cb():
            global player
            player, log_msg, next_state = encounters.flee_encounter(player)
            set_state(next_state, log_msg)
            check_master_clock()

        buttons.append(Button((px, py, bw, bh), f"Attack ({format_item_name(player['equipped_weapon'])})", attack_cb))
        buttons.append(Button((px, py + bh + vgap, bw, bh), "Flee", flee_cb))

    elif menu_state == "MENU_ROBBER":
        def pay_cb():
            global player
            player, log_msg, next_state = encounters.pay_robber_toll(player)
            set_state(next_state, log_msg)
            check_master_clock()

        def flee_cb():
            global player
            player, log_msg, next_state = encounters.flee_encounter(player)
            set_state(next_state, log_msg)
            check_master_clock()

        buttons.append(Button((px, py, bw, bh), "Fight Them", lambda: set_state("COMBAT", "You raise your weapon!")))
        buttons.append(Button((px, py + bh + vgap, bw, bh), f"Pay Toll (Silver: {player['silver']})", pay_cb))
        buttons.append(Button((px, py + (bh + vgap)*2, bw, bh), "Make a run for it", flee_cb))

    elif menu_state == "ROBBER_INTERROGATE":
        def pick_interrogate(choice_key):
            global player
            player, log_msg, next_state = encounters.resolve_robber_interrogation(choice_key, player)
            set_state(next_state, log_msg)
            check_master_clock()

        buttons.append(Button((px, py, bw, bh), "Demand the way to Parvus Town", lambda: pick_interrogate("demand_parvus")))
        buttons.append(Button((px, py + bh + vgap, bw, bh), "Loot their coin pouches (+12 Silver)", lambda: pick_interrogate("loot_silver")))
        buttons.append(Button((px, py + (bh + vgap) * 2, bw, bh), "Let them crawl away (+1 Rep)", lambda: pick_interrogate("mercy")))

    elif menu_state == "MENU_FOREST_KIDNAP":
        def pick_kidnap(choice_key):
            global player
            player, log_msg, next_state = encounters.resolve_forest_kidnap(choice_key, player)
            set_state(next_state, log_msg)
            check_master_clock()

        buttons.append(Button((px, py, bw, bh), "Denounce Farmland Encroachment (Equ 2+ / Cha 3+)", lambda: pick_kidnap("sympathise")))
        buttons.append(Button((px, py + bh + vgap, bw, bh), "Offer Food or 10 Silver as Reparations", lambda: pick_kidnap("forfeit")))
        buttons.append(Button((px, py + (bh + vgap) * 2, bw, bh), "Tear Through the Vine-Net & Fight!", lambda: pick_kidnap("fight")))

    elif menu_state == "MENU_THUG":
        def flee_cb():
            global player
            player, log_msg, next_state = encounters.flee_encounter(player)
            set_state(next_state, log_msg)
            check_master_clock()

        buttons.append(Button((px, py, bw, bh), "Fight Them", lambda: set_state("COMBAT", "You raise your weapon!")))
        buttons.append(Button((px, py + bh + vgap, bw, bh), "Make a run for it", flee_cb))

    elif menu_state == "MENU_GUARD":
        def fight_cb():
            global player
            player, log_msg, next_state = encounters.start_combat(player)
            set_state(next_state, log_msg)
            check_master_clock()

        def bribe_cb():
            global player
            player, log_msg, next_state = encounters.bribe_guard(player)
            set_state(next_state, log_msg)
            check_master_clock()

        def flee_cb():
            global player
            player, log_msg, next_state = encounters.flee_encounter(player)
            set_state(next_state, log_msg)
            check_master_clock()

        buttons.append(Button((px, py, bw, bh), "Fight your way out", fight_cb))
        buttons.append(Button((px, py + bh + vgap, bw, bh), "Bribe Guard (15s)", bribe_cb))
        buttons.append(Button((px, py + (bh + vgap)*2, bw, bh), "Make a run for it", flee_cb))

    return buttons


# Build Text Panels
location_panel_ui = TextPanelUI((40, 28, 720, 126))
log_panel_ui = TextPanelUI((40, 164, 720, 204))

# Build D-Pad (Retro Console Style with Center Look/Move Toggle)
retro_dpad = RetroDPad(400, 515, 75, handle_dpad_click, center_callback=toggle_dpad_mode)
retro_dpad.mode_label = "MOVE"
dpad_buttons = [retro_dpad]

# Build Decimal Clock UI
game_clock_ui = DecimalClockUI(128, 520, get_time_string)


# =========================================================================
# 7. DEVELOPER SANDBOX / DEBUG MODE BOOTSTRAPPER
# =========================================================================
DEV_MODE = False  # Set to True to enable F1-F4 Chapter 3 sandbox hotkeys

if DEV_MODE:
    player["silver"] = 500
    player["reputation"] = 10
    player["strength"] = 15
    player["charisma"] = 15
    player["stealth"] = 15
    player["influence"] = 10
    player["equusense"] = 10
    player["union_status"] = "joined"

    player["inventory"].extend([
        "dtessera terra world map",
        "topographic survey map",
        "iron sword",
        "compass",
        "tent",
        "meat ration",
        "weighted ivory dice",
        "syndicate token",
        "reference letter",
        "portable printing press",
        "codewheel",
        "war manual",
    ])
    player["skills"].extend([
        "union steward",
        "radical theory",
        "climb",
        "ride",
        "forge",
        "intelligence officer",
    ])
    player["faction_union"] = 10

    TARGET_TEST = "CH3_MORNING"

    if TARGET_TEST == "CH2_START":
        player["chapter_2_unlocked"] = True
        player["chapter_2_status"] = "Qualified for Chapter 2"
        player["x"], player["y"] = 10, 16
        eligible = get_eligible_chapter_2_routes(player)
        log_msg = (
            "*** DEV MODE: BOOTED INTO CHAPTER 2 START ***\n\n"
            + "\n".join(f" • {r}" for r in eligible)
        )
        set_state("CHAPTER_2_BOARD", log_msg)

    elif TARGET_TEST == "CH3_MORNING":
        player["ch3_rank"] = "General"
        player["ch3_faction"] = "Union"
        player["global_morale"] = 80
        player["ch3_world_bits"] = {f"track_{i}": 1 for i in range(1, 11)}
        player = ch3_war_engine.init_chapter_3_world_board(player, world_map)
        player = ui_renderer.init_ch3_morning_phase(player)
        menu_state = "CH3_MORNING_PHASE"
        add_log("DEV MODE: Booted into Chapter 3 Morning War Ledger.")

# =========================================================================
# 8. MAIN RENDER LOOP
# =========================================================================
async def main():
    global player, loc_typewriter_idx, log_typewriter_idx, selected_target, menu_state, selected_verb, ch3_selected_army_pos, mouse_pos

    while True:
        await asyncio.sleep(0)
        mouse_pos = to_logical_pos(pygame.mouse.get_pos())

        if menu_state == "CASINO_CRAPS" and player.get("cr_kick_to_combat"):
            player["cr_kick_to_combat"] = False
            player, log_msg, next_state = (
                encounters.trigger_casino_enforcer_combat(
                    player, reason="cheating"
                )
            )
            set_state(next_state, log_msg)
    
        # Check if a Private marching in First-Person Field Mode finished their day
        if menu_state == "MAIN" and player.get("ch3_private_field_mode"):
            dusk_ready, p_msg = ch3_war_engine.check_private_afternoon_progress(
                player, world_map, action_taken="check"
            )
            if dusk_ready:
                add_log(p_msg)
                my_fac = player.get("ch3_faction", "Union")
                att = {"faction": my_fac, "count": 4}
                dfn = {"faction": "Laydere", "count": 3}
                t_coord = player.get("ch3_daily_order", {}).get(
                    "target_pos", [10, 10]
                )
                t_key = f"{t_coord[0]},{t_coord[1]}"
                player = ch3_combat_engine.init_ch3_evening_clash(
                    player, att, dfn, t_key, world_map
                )
                set_state("CH3_EVENING_PHASE", p_msg)
    
        active_dpad = dpad_buttons if menu_state == "MAIN" else []
        right_buttons = get_current_right_buttons()
        if menu_state in (
            "CASINO_BLACKJACK",
            "CASINO_POKER",
            "CASINO_ROULETTE",
            "CASINO_CRAPS",
            "MINIGAME_ARCHERY",
        ):
            all_active_buttons = right_buttons
        else:
            all_active_buttons = active_dpad + right_buttons
    
        if pass_and_play.should_trigger_ch1_ch2_handover(player, menu_state):
            player["pnp_resume_state"] = menu_state
            pass_and_play.rotate_to_next_pnp_player(player)
            set_state("PNP_HANDOVER_CURTAIN")
        for event in pygame.event.get():
            if hasattr(event, "pos"):
                event.pos = to_logical_pos(event.pos)
    
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
    
            # --- KEYBOARD EVENT HANDLING ---
            if event.type == pygame.KEYDOWN:
                if menu_state == "PNP_LOBBY_MODAL" and event.key != pygame.K_F10:
                    pass_and_play.handle_pnp_lobby_event(
                        event, player, world_map, ui_renderer
                    )
                    continue
                if event.key == pygame.K_F4:
                    player["ch3_prev_modal_state"] = menu_state
                    set_state("PNP_LOBBY_MODAL")
                    continue
                if event.key == pygame.K_F10 or (
                    event.key == pygame.K_RETURN
                    and (event.mod & pygame.KMOD_ALT)
                ):
                    toggle_fullscreen()
                    continue
    
                if menu_state in (
                    "MAIN",
                    "STATUS_MENU",
                    "INVENTORY_MENU",
                    "MINIGAME_WEATHER_REPORT",
                ):
                    if event.key == pygame.K_c:
                        set_state(
                            "MAIN"
                            if menu_state == "STATUS_MENU"
                            else "STATUS_MENU"
                        )
                        continue
                    if event.key == pygame.K_i:
                        set_state(
                            "MAIN"
                            if menu_state == "INVENTORY_MENU"
                            else "INVENTORY_MENU"
                        )
                        continue
                    if event.key == pygame.K_w:
                        set_state(
                            "MAIN"
                            if menu_state == "MINIGAME_WEATHER_REPORT"
                            else "MINIGAME_WEATHER_REPORT"
                        )
                        continue
                    if event.key == pygame.K_t and menu_state == "MAIN":
                        add_log(weather_engine.toggle_topo_map(player))
                        continue
                    if event.key == pygame.K_ESCAPE and menu_state != "MAIN":
                        set_state("MAIN")
                        continue
    
                # --- DEVELOPER SANDBOX HOTKEYS (F1 - F4) ---
                if DEV_MODE:
                    if event.key == pygame.K_F1:
                        player["ch3_faction"] = player.get("ch3_faction", "Union")
                        player["ch3_rank"] = player.get("ch3_rank", "General")
                        player["ch3_world_bits"] = {
                            f"track_{i}": 1 for i in range(1, 11)
                        }
                        for item in (
                            "portable printing press",
                            "codewheel",
                            "war manual",
                        ):
                            if item not in player["inventory"]:
                                player["inventory"].append(item)
                        player = ch3_war_engine.init_chapter_3_world_board(
                            player, world_map
                        )
                        player = ui_renderer.init_ch3_morning_phase(player)
                        set_state(
                            "CH3_MORNING_PHASE",
                            "[DEV F1] Initialised Chapter 3 Morning War Ledger.",
                        )
                        continue
    
                    if event.key == pygame.K_F2:
                        if "ch3_factions" not in player:
                            player = ch3_war_engine.init_chapter_3_world_board(
                                player, world_map
                            )
                        player["movement_points"] = 6
                        ch3_war_engine.recalculate_ch3_total_points(player)
                        set_state(
                            "CH3_AFTERNOON_PHASE",
                            "[DEV F2] Switched to Chapter 3 Strategic War Table.",
                        )
                        continue
    
                    if event.key == pygame.K_F3:
                        if "ch3_factions" not in player:
                            player = ch3_war_engine.init_chapter_3_world_board(
                                player, world_map
                            )
                        att = {
                            "faction": player.get("ch3_faction", "Union"),
                            "count": 5,
                        }
                        dfn = {"faction": "Ragmore", "count": 4}
                        player = ch3_combat_engine.init_ch3_evening_clash(
                            player, att, dfn, "5,15", world_map
                        )
                        set_state(
                            "CH3_EVENING_PHASE",
                            "[DEV F3] Launched 3-Stage Stronghold Siege!",
                        )
                        continue
    
                    if event.key == pygame.K_F4:
                        if "ch3_factions" not in player:
                            player = ch3_war_engine.init_chapter_3_world_board(
                                player, world_map
                            )
                        my_fac = player.get("ch3_faction", "Union")
                        player["ch3_factions"][my_fac]["agenda_pts"] = 85
                        is_over, winner = ch3_war_engine.check_ch3_endgame_trigger(
                            player
                        )
                        if is_over and not player.get("_victory_recorded"):
                            from mechanics import record_campaign_victory
    
                            record_campaign_victory(player, profile_name="noburu")
                            player["_victory_recorded"] = True
                        set_state(
                            "CH3_EPILOGUE",
                            f"[DEV F4] {winner} achieved 100 Hegemony Points!",
                        )
                        continue
    
            if menu_state == "MINIGAME_TYPESET":
                printing_press_engine.handle_typeset_event(event, player)
    
            # --- PASS-AND-PLAY LOBBY & HERALDIC HANDOVER CURTAIN CLICKS ---
            if menu_state == "PNP_LOBBY_MODAL":
                handled_pnp, next_pnp = pass_and_play.handle_pnp_lobby_event(
                    event, player, world_map, ui_renderer
                )
                if handled_pnp and next_pnp:
                    set_state(
                        next_pnp,
                        "Campaign & Pass-and-Play settings applied!",
                    )
                continue
    
            if menu_state == "PNP_HANDOVER_CURTAIN":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pass_and_play.HANDOVER_BTN_RECT.collidepoint(event.pos):
                        target_st = player.pop("pnp_resume_state", None)
                        if not target_st:
                            target_st = (
                                "CH3_MORNING_PHASE"
                                if pass_and_play.get_session().get("in_chapter_3")
                                else "MAIN"
                            )
                        set_state(
                            target_st,
                            f"=== {player.get('pnp_player_name', 'Player')}'s "
                            "Turn Begins! ===",
                        )
                continue
    
            # --- CHAPTER 3: TABLETOP SETTINGS, RULEBOOK & TUTORIAL MODALS ---
            if menu_state == "CH3_SETTINGS_MODAL":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    s_rects = player.get("ch3_settings_rects", {})
                    if (
                        s_rects.get("open_pnp_lobby")
                        and s_rects["open_pnp_lobby"].collidepoint(event.pos)
                    ):
                        set_state("PNP_LOBBY_MODAL")
                    elif (
                        s_rects.get("cycle_victory_mode")
                        and s_rects["cycle_victory_mode"].collidepoint(event.pos)
                    ):
                        v_modes = ["100_PTS", "250_PTS", "DOMINATION"]
                        cur_v = player.get("ch3_victory_mode", "100_PTS")
                        nxt_v = (
                            (v_modes.index(cur_v) + 1) % len(v_modes)
                            if cur_v in v_modes
                            else 0
                        )
                        player["ch3_victory_mode"] = v_modes[nxt_v]
                        ch3_war_engine.recalculate_ch3_total_points(player)
                    elif (
                        s_rects.get("cycle_month")
                        and s_rects["cycle_month"].collidepoint(event.pos)
                    ):
                        player["current_month_idx"] = (
                            player.get("current_month_idx", 1) + 1
                        ) % 12
                        weather_engine.update_weather_on_time_advance(player, minutes_elapsed, world_map=None)
                    elif (
                        s_rects.get("toggle_tooltips")
                        and s_rects["toggle_tooltips"].collidepoint(event.pos)
                    ):
                        player["ch3_show_tooltips"] = not player.get(
                            "ch3_show_tooltips", True
                        )
                    elif (
                        s_rects.get("toggle_show_ai")
                        and s_rects["toggle_show_ai"].collidepoint(event.pos)
                    ):
                        player["ch3_show_ai_moves"] = not player.get(
                            "ch3_show_ai_moves", True
                        )
                    elif (
                        s_rects.get("toggle_ai_pacing")
                        and s_rects["toggle_ai_pacing"].collidepoint(event.pos)
                    ):
                        modes = ["MANUAL", "SLOW", "NORMAL", "FAST"]
                        cur_p = player.get("ch3_ai_pacing", "NORMAL")
                        nxt_i = (
                            (modes.index(cur_p) + 1) % len(modes)
                            if cur_p in modes
                            else 2
                        )
                        player["ch3_ai_pacing"] = modes[nxt_i]
                    elif (
                        s_rects.get("toggle_confirm")
                        and s_rects["toggle_confirm"].collidepoint(event.pos)
                    ):
                        player["ch3_confirm_phases"] = not player.get(
                            "ch3_confirm_phases", True
                        )
                    elif (
                        s_rects.get("toggle_click_slot")
                        and s_rects["toggle_click_slot"].collidepoint(event.pos)
                    ):
                        player["ch3_click_to_slot"] = not player.get(
                            "ch3_click_to_slot", True
                        )
                    elif (
                        s_rects.get("open_tutorial")
                        and s_rects["open_tutorial"].collidepoint(event.pos)
                    ):
                        set_state("CH3_TUTORIAL_SELECT")
                    elif (
                        s_rects.get("open_rulebook")
                        and s_rects["open_rulebook"].collidepoint(event.pos)
                    ):
                        set_state("CH3_RULEBOOK_MODAL")
                    elif (
                        s_rects.get("close_settings")
                        and s_rects["close_settings"].collidepoint(event.pos)
                    ):
                        set_state(
                            player.get("ch3_prev_modal_state", "CH3_MORNING_PHASE")
                        )
                continue
    
            elif menu_state == "CH3_RULEBOOK_MODAL":
                handled_rb, next_rb = ch3_tutorial_book.handle_ch3_rulebook_event(
                    event, player, world_map
                )
                if handled_rb and next_rb:
                    set_state(next_rb)
                continue
    
            elif menu_state == "CH3_TUTORIAL_SELECT":
                handled_ts, next_ts = (
                    ch3_tutorial_book.handle_ch3_tutorial_select_event(
                        event, player, world_map
                    )
                )
                if handled_ts and next_ts:
                    set_state(next_ts)
                continue
    
            # --- INTERCEPT TUTORIAL OVERLAY & CAMERA RAIL IN CH3 PHASES ---
            if menu_state in (
                "CH3_MORNING_PHASE",
                "CH3_AFTERNOON_PHASE",
                "CH3_EVENING_PHASE",
            ):
                t_click, t_exited = (
                    ch3_tutorial_book.handle_tutorial_overlay_click(event, player)
                )
                if t_click:
                    if t_exited:
                        set_state("CH3_MORNING_PHASE", "Tutorial concluded.")
                    continue
    
            if menu_state in ("CH3_MORNING_PHASE", "CH3_AFTERNOON_PHASE"):
                cam_handled, cam_act = (
                    ch3_board_renderer.handle_board_camera_event(event, player)
                )
                if cam_handled:
                    if cam_act == "OPEN_CH3_SETTINGS":
                        player["ch3_prev_modal_state"] = menu_state
                        set_state("CH3_SETTINGS_MODAL")
                    elif cam_act == "OPEN_CH3_RULEBOOK":
                        player["ch3_prev_modal_state"] = menu_state
                        set_state("CH3_RULEBOOK_MODAL")
                    continue
    
            # --- CHAPTER 3: MORNING PHASE ---
            if menu_state == "CH3_MORNING_PHASE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    commit_rect = player.get("ch3_commit_rect")
                    excl_rect = player.get("ch3_exclusive_action_rect")
                    dice_list = player.get("ch3_morning_dice", [])
                    slots = player.get("ch3_morning_slots", {})
                    rolled = player.get("ch3_dice_rolled_today", False)
    
                    # 1. Explicit Dawn Roll
                    if not rolled:
                        if commit_rect and commit_rect.collidepoint(event.pos):
                            player["ch3_dice_rolled_today"] = True
                            player["ch3_dice_anim_until"] = (
                                pygame.time.get_ticks() + 800
                            )
                            if (
                                player.get("ch3_tutorial_active")
                                and player.get("ch3_tutorial_step") == 3
                            ):
                                player["ch3_tutorial_step"] = 4
                        continue
    
                    # 2. Reversible Slotted Dice (Click Slotted Die -> Unslot!)
                    unslotted_now = False
                    for slot_data in slots.values():
                        for d_obj, well_rect in list(
                            slot_data.get("dice_rects", [])
                        ):
                            if well_rect.collidepoint(event.pos):
                                d_obj["slotted_in"] = None
                                if d_obj in slot_data.get("dice_objs", []):
                                    slot_data["dice_objs"].remove(d_obj)
                                player["ch3_selected_die_id"] = None
                                player["_warned_empty_morning"] = False
                                unslotted_now = True
                                if (
                                    player.get("ch3_tutorial_active")
                                    and player.get("ch3_tutorial_step") == 5
                                ):
                                    player["ch3_tutorial_step"] = 6
                                break
                        if unslotted_now:
                            break
                    if unslotted_now:
                        continue
    
                    # 3. Chapter 2 Specialist War-Table Tool Buttons
                    tool_rects = player.get("ch3_tool_rects", {})
                    clicked_tool = None
                    for t_key, t_rect in tool_rects.items():
                        if t_rect and t_rect.collidepoint(event.pos):
                            clicked_tool = t_key
                            break
    
                    if clicked_tool:
                        msg = ch3_war_engine.execute_ch2_war_tool(
                            player, clicked_tool, world_map
                        )
                        player["ch3_dice_anim_until"] = (
                            pygame.time.get_ticks() + 650
                        )
                        add_log(msg)
                        continue
    
                    # 4. Exclusive Rank Action Button
                    if excl_rect and excl_rect.collidepoint(event.pos):
                        rank = player.get("ch3_rank", "Private")
                        if rank == "General":
                            player["global_morale"] = max(
                                0, player.get("global_morale", 50) - 10
                            )
                            player = ui_renderer.init_ch3_morning_phase(player)
                            player["ch3_dice_rolled_today"] = True
                            player["ch3_dice_anim_until"] = (
                                pygame.time.get_ticks() + 800
                            )
                        elif rank == "Captain" and not player.get(
                            "ch3_promoted_today"
                        ):
                            player["ch3_promoted_today"] = True
                            dice_list.append({
                                "id": len(dice_list),
                                "value": 6,
                                "rect": None,
                                "slotted_in": None,
                                "is_dragging": False,
                            })
                            player["ch3_dice_anim_until"] = (
                                pygame.time.get_ticks() + 650
                            )
                        elif rank == "Private" and not player.get(
                            "ch3_subverted_today"
                        ):
                            player["ch3_subverted_today"] = True
                            player["silver"] += 5
                            player["reputation"] -= 1
                        continue
    
                    # 5. Commit Morning Orders -> Convert Unslotted Dice to 10 MP Each
                    if commit_rect and commit_rect.collidepoint(event.pos):
                        has_slotted = any(
                            d["slotted_in"] is not None for d in dice_list
                        )
                        if (
                            player.get("ch3_confirm_phases", True)
                            and not has_slotted
                            and not player.get("_warned_empty_morning")
                        ):
                            player["_warned_empty_morning"] = True
                            add_log(
                                "No dice are slotted! Click 'Commit & Start "
                                "March >>' again to convert all dice into MP."
                            )
                            continue
    
                        player["_warned_empty_morning"] = False
                        if "ch3_factions" not in player:
                            player = ch3_war_engine.init_chapter_3_world_board(
                                player, world_map
                            )
    
                        unslotted_cnt = sum(
                            1 for d in dice_list if d["slotted_in"] is None
                        )
                        p_fac = player.get("ch3_faction", "Union")
    
                        if player.get("ch3_rank") == "General":
                            if not slots.get("supply_lines", {}).get("dice_objs"):
                                player["global_morale"] = max(
                                    0, player.get("global_morale", 50) - 10
                                )
                            muster_dice = slots.get("muster_troops", {}).get(
                                "dice_objs", []
                            )
                            dice_sum = sum(d["value"] for d in muster_dice)
                            territories = player.get("territories", {})
                            owned_tiles = sum(
                                1
                                for owner in territories.values()
                                if owner == p_fac
                            )
                            if muster_dice:
                                cap = (
                                    player.get("ch3_factions", {})
                                    .get(p_fac, {})
                                    .get("capital", "11,4")
                                )
                                armies = player.setdefault("ch3_armies", {})
                                gain_bns = max(1, (dice_sum // 2) + owned_tiles)
                                if (
                                    cap in armies
                                    and armies[cap]["faction"] == p_fac
                                ):
                                    armies[cap]["count"] += gain_bns
                                else:
                                    armies[cap] = {
                                        "faction": p_fac,
                                        "count": gain_bns,
                                    }
                                player["total_troops"] = (
                                    player.get("total_troops", 0) + gain_bns
                                )
    
                        elif player.get("ch3_rank") == "Captain":
                            barricade_dice = slots.get(
                                "build_barricades", {}
                            ).get("dice_objs", [])
                            if len(barricade_dice) == 2:
                                player["local_barricades_active"] = True
                                pos_k = f"{player['x']},{player['y']}"
                                player.setdefault("ch3_barricades", {})[
                                    pos_k
                                ] = True
                        else:
                            scrounge = slots.get("scrounge", {}).get(
                                "dice_objs", []
                            )
                            if scrounge:
                                player["inventory"].append("meat ration")
    
                        # 10 MP per unslotted die (minimum 20 MP)
                        player["movement_points"] = max(20, unslotted_cnt * 10)
                        player["ch3_promoted_today"] = False
                        player["ch3_subverted_today"] = False
                        player["ch3_pending_clashes"] = []
                        player["ch3_ai_turn_queue"] = []
    
                        player.pop("ch3_morning_dice", None)
                        player.pop("ch3_morning_slots", None)
                        player["ch3_selected_die_id"] = None
    
                        if (
                            player.get("ch3_tutorial_active")
                            and player.get("ch3_tutorial_step") in (4, 5, 6)
                        ):
                            player["ch3_tutorial_step"] = 7
    
                        set_state(
                            "CH3_AFTERNOON_PHASE",
                            "Afternoon March: Select your Meeples, split "
                            "detachments, and pin attacks across the board.",
                        )
                        continue
    
                    # 6. Click-to-Slot Support
                    sel_id = player.get("ch3_selected_die_id")
                    if sel_id is not None and player.get(
                        "ch3_click_to_slot", True
                    ):
                        sel_die = next(
                            (
                                d
                                for d in dice_list
                                if d["id"] == sel_id and d["slotted_in"] is None
                            ),
                            None,
                        )
                        if sel_die:
                            slotted_via_click = False
                            for slot_id, slot_data in slots.items():
                                if slot_data.get("rect") and slot_data[
                                    "rect"
                                ].collidepoint(event.pos):
                                    req = slot_data.get("req")
                                    cur_objs = slot_data.setdefault(
                                        "dice_objs", []
                                    )
                                    valid_drop = len(cur_objs) < 3
                                    if req is not None:
                                        if (
                                            isinstance(req, list)
                                            and sel_die["value"] not in req
                                        ):
                                            valid_drop = False
                                        elif req == "pair":
                                            if (
                                                len(cur_objs) == 1
                                                and sel_die["value"]
                                                != cur_objs[0]["value"]
                                            ):
                                                valid_drop = False
                                            elif len(cur_objs) >= 2:
                                                valid_drop = False
                                    if valid_drop:
                                        sel_die["slotted_in"] = slot_id
                                        cur_objs.append(sel_die)
                                        player["ch3_selected_die_id"] = None
                                        slotted_via_click = True
                                        if (
                                            player.get("ch3_tutorial_active")
                                            and player.get("ch3_tutorial_step")
                                            == 4
                                        ):
                                            player["ch3_tutorial_step"] = 5
                                    break
                            if slotted_via_click:
                                continue
    
                    # 7. Pick Up Unslotted Die from Felt Tray
                    for die_obj in dice_list:
                        if (
                            die_obj["slotted_in"] is None
                            and die_obj.get("rect")
                            and die_obj["rect"].collidepoint(event.pos)
                        ):
                            player["ch3_selected_die_id"] = die_obj["id"]
                            die_obj["is_dragging"] = True
                            die_obj["drag_offset_x"] = (
                                die_obj["rect"].x - event.pos[0]
                            )
                            die_obj["drag_offset_y"] = (
                                die_obj["rect"].y - event.pos[1]
                            )
                            break
    
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for die_obj in player.get("ch3_morning_dice", []):
                        if die_obj.get("is_dragging"):
                            die_obj["is_dragging"] = False
                            for slot_id, slot_data in player.get(
                                "ch3_morning_slots", {}
                            ).items():
                                if (
                                    slot_data.get("rect")
                                    and die_obj.get("rect")
                                    and slot_data["rect"].colliderect(
                                        die_obj["rect"]
                                    )
                                ):
                                    req = slot_data.get("req")
                                    cur_objs = slot_data.setdefault(
                                        "dice_objs", []
                                    )
                                    valid_drop = len(cur_objs) < 3
    
                                    if req is not None:
                                        if (
                                            isinstance(req, list)
                                            and die_obj["value"] not in req
                                        ):
                                            valid_drop = False
                                        elif req == "pair":
                                            if (
                                                len(cur_objs) == 1
                                                and die_obj["value"]
                                                != cur_objs[0]["value"]
                                            ):
                                                valid_drop = False
                                            elif len(cur_objs) >= 2:
                                                valid_drop = False
    
                                    if valid_drop:
                                        die_obj["slotted_in"] = slot_id
                                        cur_objs.append(die_obj)
                                        player["ch3_selected_die_id"] = None
                                        if (
                                            player.get("ch3_tutorial_active")
                                            and player.get("ch3_tutorial_step")
                                            == 4
                                        ):
                                            player["ch3_tutorial_step"] = 5
                                    break
    
                elif event.type == pygame.MOUSEMOTION:
                    for die_obj in player.get("ch3_morning_dice", []):
                        if die_obj.get("is_dragging") and die_obj.get("rect"):
                            die_obj["rect"].x = event.pos[0] + die_obj.get(
                                "drag_offset_x", 0
                            )
                            die_obj["rect"].y = event.pos[1] + die_obj.get(
                                "drag_offset_y", 0
                            )
    
            # --- CHAPTER 3: AFTERNOON PHASE (SPLITTER, PINNING & AI BANNER) ---
            elif menu_state == "CH3_AFTERNOON_PHASE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # 1. If Heraldic AI Turn Banner is Active, Handle Its 3 Buttons
                    ai_queue = player.get("ch3_ai_turn_queue", [])
                    if ai_queue and player.get("ch3_show_ai_moves", True):
                        n_rect = player.get("ch3_ai_next_rect")
                        sp_rect = player.get("ch3_ai_speed_rect")
                        sk_rect = player.get("ch3_ai_skip_rect")
    
                        if sp_rect and sp_rect.collidepoint(event.pos):
                            modes = ["MANUAL", "SLOW", "NORMAL", "FAST"]
                            cur_p = player.get("ch3_ai_pacing", "NORMAL")
                            nxt_i = (
                                (modes.index(cur_p) + 1) % len(modes)
                                if cur_p in modes
                                else 2
                            )
                            player["ch3_ai_pacing"] = modes[nxt_i]
                            player["ch3_ai_step_timer"] = pygame.time.get_ticks()
                            continue
    
                        if sk_rect and sk_rect.collidepoint(event.pos):
                            player["ch3_ai_turn_queue"] = []
                        elif n_rect and n_rect.collidepoint(event.pos):
                            ai_queue.pop(0)
                            if ai_queue:
                                ai_queue[0]["anim_start"] = pygame.time.get_ticks()
                                player["ch3_ai_step_timer"] = (
                                    pygame.time.get_ticks()
                                )
                                ch3_board_renderer.centre_camera_on_tile(
                                    player,
                                    ai_queue[0].get(
                                        "to_pos", ai_queue[0].get("capital")
                                    ),
                                )
                                continue
    
                        # If AI queue is now empty, proceed to Pinned Clashes or Dawn!
                        if not player.get("ch3_ai_turn_queue"):
                            ch3_board_renderer.centre_camera_on_player_forces(
                                player
                            )
                            pending = player.get("ch3_pending_clashes", [])
                            if pending:
                                first_c = pending.pop(0)
                                player = ch3_combat_engine.init_ch3_evening_clash(
                                    player,
                                    first_c["attacker"],
                                    first_c["defender"],
                                    first_c["tile_pos"],
                                    world_map,
                                    origin_pos=first_c.get("origin_pos"),
                                )
                                set_state(
                                    "CH3_EVENING_PHASE",
                                    "Dusk falls: Resolving pinned engagements!",
                                )
                            else:
                                player["ch3_day"] = player.get("ch3_day", 1) + 1
                                player = ui_renderer.init_ch3_morning_phase(player)
                                set_state(
                                    "CH3_MORNING_PHASE",
                                    f"Dawn breaks on Day {player['ch3_day']}.",
                                )
                        continue
    
                    # 2. Check Troop Detachment Splitter Buttons
                    if (
                        ch3_selected_army_pos
                        and ch3_selected_army_pos in player.get("ch3_armies", {})
                    ):
                        tot_bns = max(
                            1,
                            player["ch3_armies"][ch3_selected_army_pos].get(
                                "count", 1
                            ),
                        )
                        cur_split = player.get("ch3_split_count", tot_bns)
                        sp_rects = player.get("ch3_splitter_rects", {})
                        clicked_sp = None
                        for s_key, s_rect in sp_rects.items():
                            if s_rect and s_rect.collidepoint(event.pos):
                                clicked_sp = s_key
                                break
                        if clicked_sp:
                            if clicked_sp == "minus":
                                player["ch3_split_count"] = max(1, cur_split - 1)
                            elif clicked_sp == "plus":
                                player["ch3_split_count"] = min(
                                    tot_bns, cur_split + 1
                                )
                            elif clicked_sp == "one":
                                player["ch3_split_count"] = 1
                            elif clicked_sp == "half":
                                player["ch3_split_count"] = max(1, tot_bns // 2)
                            elif clicked_sp == "all":
                                player["ch3_split_count"] = tot_bns
                            continue
    
                    # 3. Check Rank Command Deck Buttons
                    rank_rects = player.get("ch3_rank_action_rects", {})
                    clicked_rank_act = None
                    for act_key, r_rect in rank_rects.items():
                        if r_rect and r_rect.collidepoint(event.pos):
                            clicked_rank_act = act_key
                            break
    
                    if clicked_rank_act:
                        if clicked_rank_act == "enter_field_mode":
                            player, field_msg, next_st = (
                                ch3_war_engine.start_private_afternoon_march(
                                    player, world_map
                                )
                            )
                            set_state(next_st, field_msg)
                        elif clicked_rank_act == "fulfill_directive":
                            player["ch3_confidence"] = min(
                                100, player.get("ch3_confidence", 65) + 5
                            )
                        elif clicked_rank_act == "subvert_confidence":
                            player["ch3_confidence"] = max(
                                0, player.get("ch3_confidence", 65) - 20
                            )
                        else:
                            my_f = player.get("ch3_faction", "Union")
                            rivals = [
                                f
                                for f in ch3_war_engine.DTESSERA_FACTIONS
                                if f != my_f
                            ]
                            target_f = player.get("ch3_selected_rival")
                            if not target_f or target_f == my_f:
                                target_f = rivals[0]
                            msg = ch3_war_engine.execute_rank_political_action(
                                player,
                                clicked_rank_act,
                                target_faction=target_f,
                                world_map=world_map,
                            )
                            add_log(msg)
                        continue
    
                    # 4. Check "Finish March & Watch AI >>" Button
                    end_rect = player.get("ch3_end_march_rect")
                    if end_rect and end_rect.collidepoint(event.pos):
                        if (
                            player.get("ch3_confirm_phases", True)
                            and player.get("movement_points", 0) >= 6
                            and not player.get("_warned_unspent_mp")
                        ):
                            player["_warned_unspent_mp"] = True
                            player["ch3_daily_order"] = {
                                "description": (
                                    "You still have March Points left! Click "
                                    "'Finish March' again to end your turn."
                                )
                            }
                            continue
    
                        player["_warned_unspent_mp"] = False
                        ch3_selected_army_pos = None
                        player["_warned_unspent_mp"] = False
                        ch3_selected_army_pos = None
    
                        # Pass-and-Play: Rotate to next Human Seat if more remain today!
                        has_next_human, nxt_name, nxt_fac = (
                            pass_and_play.advance_ch3_human_turn(player)
                        )
                        if has_next_human:
                            player = ui_renderer.init_ch3_morning_phase(player)
                            player["pnp_resume_state"] = "CH3_MORNING_PHASE"
                            set_state(
                                "PNP_HANDOVER_CURTAIN",
                                f"Pass the mouse to {nxt_name} ({nxt_fac})!",
                            )
                            continue
                        p_fac = player.get("ch3_faction", "Union")
    
                        # Generate AI turns now so player watches them live!
                        player = ch3_war_engine.process_enemy_faction_turns(
                            player, world_map
                        )
                        for ai_k, ai_d in player.get("ch3_factions", {}).items():
                            if ai_k != p_fac and random.random() < 0.45:
                                ch3_war_engine.apply_ai_agenda_balance_step(ai_d)
    
                        ai_q = player.get("ch3_ai_turn_queue", [])
                        if player.get("ch3_show_ai_moves", True) and ai_q:
                            ai_q[0]["anim_start"] = pygame.time.get_ticks()
                            player["ch3_ai_step_timer"] = pygame.time.get_ticks()
                            ch3_board_renderer.centre_camera_on_tile(
                                player,
                                ai_q[0].get("to_pos", ai_q[0].get("capital")),
                            )
                            continue
    
                        # If AI animations are toggled OFF, go straight to Clashes or Dawn
                        player["ch3_ai_turn_queue"] = []
                        pending = player.get("ch3_pending_clashes", [])
                        if pending:
                            first_c = pending.pop(0)
                            player = ch3_combat_engine.init_ch3_evening_clash(
                                player,
                                first_c["attacker"],
                                first_c["defender"],
                                first_c["tile_pos"],
                                world_map,
                                origin_pos=first_c.get("origin_pos"),
                            )
                            set_state(
                                "CH3_EVENING_PHASE",
                                "Dusk falls: Resolving pinned engagements!",
                            )
                            continue
    
                        is_over, winner = (
                            ch3_war_engine.check_ch3_endgame_trigger(player)
                        )
                        if is_over:
                            if not player.get("_victory_recorded"):
                                from mechanics import record_campaign_victory
    
                                record_campaign_victory(
                                    player, profile_name="noburu"
                                )
                                player["_victory_recorded"] = True
                            set_state(
                                "CH3_EPILOGUE",
                                f"{winner} has achieved 100 Hegemony Points!",
                            )
                        else:
                            player["ch3_day"] = player.get("ch3_day", 1) + 1
                            player = ui_renderer.init_ch3_morning_phase(player)
                            set_state(
                                "CH3_MORNING_PHASE",
                                f"Dawn breaks on Day {player['ch3_day']}.",
                            )
                        continue
    
                    # 5. Map Clearing Click: Select, Split, March, or Pin '⚔' Clash
                    clicked_pos = player.get("ch3_hovered_pos")
                    if clicked_pos:
                        armies = player.setdefault("ch3_armies", {})
                        my_fac = player.get("ch3_faction", "Union")
    
                        if (
                            clicked_pos in armies
                            and armies[clicked_pos]["faction"] in (my_fac, "Player")
                            and clicked_pos == ch3_selected_army_pos
                        ):
                            ch3_selected_army_pos = None
                        elif (
                            clicked_pos in armies
                            and armies[clicked_pos]["faction"] in (my_fac, "Player")
                            and not ch3_selected_army_pos
                        ):
                            ch3_selected_army_pos = clicked_pos
                            player["ch3_split_count"] = armies[clicked_pos][
                                "count"
                            ]
                        elif (
                            ch3_selected_army_pos
                            and ch3_selected_army_pos in armies
                        ):
                            start_x, start_y = map(
                                int, ch3_selected_army_pos.split(",")
                            )
                            click_map_x, click_map_y = map(
                                int, clicked_pos.split(",")
                            )
                            is_adjacent = (
                                abs(click_map_x - start_x) <= 1
                                and abs(click_map_y - start_y) <= 1
                                and (click_map_x, click_map_y)
                                != (start_x, start_y)
                            )
    
                            if (
                                is_adjacent
                                and (click_map_x, click_map_y) in world_map
                            ):
                                origin_army = armies[ch3_selected_army_pos]
                                avail_cnt = max(1, origin_army.get("count", 1))
                                split_cnt = max(
                                    1,
                                    min(
                                        avail_cnt,
                                        player.get("ch3_split_count", avail_cnt),
                                    ),
                                )
    
                                mp_cost, can_pass, hazard_warn = (
                                    ch3_war_engine.calculate_ch3_movement_cost(
                                        player,
                                        my_fac,
                                        clicked_pos,
                                        world_map,
                                        troop_count=split_cnt,
                                    )
                                )
                                if not can_pass:
                                    player["ch3_daily_order"] = {
                                        "description": f"MARCH HALTED: {hazard_warn}"
                                    }
                                    continue
    
                                current_mp = player.get("movement_points", 0)
                                march_ok = True
    
                                if current_mp < mp_cost:
                                    forced_roll = random.randint(1, 6)
                                    player["movement_points"] = 0
                                    if forced_roll <= 2:
                                        origin_army["count"] = max(
                                            1, avail_cnt - 1
                                        )
                                        player["ch3_split_count"] = origin_army[
                                            "count"
                                        ]
                                        player["ch3_daily_order"] = {
                                            "description": (
                                                "FORCED MARCH DISASTER (Rolled "
                                                f"{forced_roll})! Lost 1 Bn."
                                            )
                                        }
                                        march_ok = False
                                else:
                                    player["movement_points"] -= mp_cost
    
                                if march_ok:
                                    prev_origin = ch3_selected_army_pos
                                    if split_cnt < avail_cnt:
                                        origin_army["count"] = (
                                            avail_cnt - split_cnt
                                        )
                                        player["ch3_split_count"] = origin_army[
                                            "count"
                                        ]
                                    else:
                                        armies.pop(ch3_selected_army_pos, None)
                                        ch3_selected_army_pos = None
    
                                    moving_army = {
                                        "faction": my_fac,
                                        "count": split_cnt,
                                    }
                                    pinned_here = next(
                                        (
                                            c
                                            for c in player.get(
                                                "ch3_pending_clashes", []
                                            )
                                            if c["tile_pos"] == clicked_pos
                                        ),
                                        None,
                                    )
    
                                    # Case A: Reinforcing an existing pinned clash
                                    if pinned_here:
                                        ch3_war_engine.pin_ch3_clash(
                                            player,
                                            clicked_pos,
                                            moving_army,
                                            pinned_here["defender"],
                                            origin_pos=prev_origin,
                                        )
                                        continue
    
                                    # Case B: Stepping onto an enemy garrison -> Pin '⚔' Clash!
                                    if (
                                        clicked_pos in armies
                                        and armies[clicked_pos]["faction"]
                                        != my_fac
                                    ):
                                        def_army = armies.pop(clicked_pos)
                                        if player.get("ch3_tutorial_active"):
                                            player["ch3_tutorial_step"] = 9
                                            player = ch3_combat_engine.init_ch3_evening_clash(
                                                player,
                                                moving_army,
                                                def_army,
                                                clicked_pos,
                                                world_map,
                                                origin_pos=prev_origin,
                                            )
                                            set_state(
                                                "CH3_EVENING_PHASE",
                                                "Your forces engage "
                                                f"{def_army['faction']}!",
                                            )
                                        else:
                                            ch3_war_engine.pin_ch3_clash(
                                                player,
                                                clicked_pos,
                                                moving_army,
                                                def_army,
                                                origin_pos=prev_origin,
                                            )
                                        continue
    
                                    # Case C: Stepping onto friendly or empty clearing
                                    if (
                                        clicked_pos in armies
                                        and armies[clicked_pos]["faction"]
                                        == my_fac
                                    ):
                                        armies[clicked_pos]["count"] += (
                                            moving_army["count"]
                                        )
                                    else:
                                        armies[clicked_pos] = moving_army
                                    player.setdefault("territories", {})[
                                        clicked_pos
                                    ] = my_fac
                                    if not ch3_selected_army_pos:
                                        ch3_selected_army_pos = clicked_pos
                                        player["ch3_split_count"] = armies[
                                            clicked_pos
                                        ]["count"]
                                    ch3_war_engine.recalculate_ch3_total_points(
                                        player
                                    )
                            elif (
                                clicked_pos in armies
                                and armies[clicked_pos]["faction"]
                                in (my_fac, "Player")
                            ):
                                ch3_selected_army_pos = clicked_pos
                                player["ch3_split_count"] = armies[clicked_pos][
                                    "count"
                                ]
                            else:
                                ch3_selected_army_pos = None
    
            # --- CHAPTER 3: EVENING TACTICAL CLASH & MULTI-BATTLE QUEUE ---
            elif menu_state == "CH3_EVENING_PHASE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    combat_rects = player.get("ch3_combat_action_rects", {})
                    clicked_combat_act = None
    
                    for act_key, c_rect in combat_rects.items():
                        if c_rect and c_rect.collidepoint(event.pos):
                            clicked_combat_act = act_key
                            break
    
                    if clicked_combat_act:
                        if clicked_combat_act == "press_assault" and player.get(
                            "ch3_combat_resolved"
                        ):
                            if player.get("ch3_tutorial_active"):
                                ch3_tutorial_book.end_faction_tutorial(player)
                                set_state(
                                    "CH3_MORNING_PHASE",
                                    "Tutorial complete! Your real campaign has "
                                    "been restored.",
                                )
                                continue
    
                            # Pop next pinned '⚔' battle if more remain tonight!
                            pending = player.get("ch3_pending_clashes", [])
                            if pending:
                                next_c = pending.pop(0)
                                player = ch3_combat_engine.init_ch3_evening_clash(
                                    player,
                                    next_c["attacker"],
                                    next_c["defender"],
                                    next_c["tile_pos"],
                                    world_map,
                                    origin_pos=next_c.get("origin_pos"),
                                )
                                continue
    
                            is_over, winner = (
                                ch3_war_engine.check_ch3_endgame_trigger(player)
                            )
                            if is_over:
                                if not player.get("_victory_recorded"):
                                    from mechanics import record_campaign_victory
    
                                    record_campaign_victory(
                                        player, profile_name="noburu"
                                    )
                                    player["_victory_recorded"] = True
                                set_state(
                                    "CH3_EPILOGUE",
                                    f"{winner} has achieved 100 Hegemony Points!",
                                )
                                continue
    
                            player["ch3_combat_active"] = False
                            player["ch3_combat_resolved"] = False
                            player["ch3_attacker"] = None
                            player["ch3_defender"] = None
                            player["ch3_combat_log"] = []
                            player["ch3_day"] = player.get("ch3_day", 1) + 1
                            player = ui_renderer.init_ch3_morning_phase(player)
                            set_state(
                                "CH3_MORNING_PHASE",
                                f"Dawn breaks on Day {player['ch3_day']}.",
                            )
                        else:
                            player, log_msg = (
                                ch3_combat_engine.execute_ch3_combat_action(
                                    player, clicked_combat_act
                                )
                            )
                            if (
                                player.get("ch3_tutorial_active")
                                and clicked_combat_act
                                not in ("roll_battle_dice", "press_assault")
                            ):
                                player["ch3_tutorial_step"] = 10
                            add_log(log_msg)
                        continue
    
            # --- CHAPTER 3: EPILOGUE CHRONICLE ---
            elif menu_state == "CH3_EPILOGUE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    ep_rect = player.get("ch3_epilogue_btn_rect")
                    if ep_rect and ep_rect.collidepoint(event.pos):
                        set_state("VICTORY_GRID_MENU", "")
                        continue
    
            # --- CHAPTER 3: HALL OF HEGEMONY (VICTORY GRID) ---
            elif menu_state == "VICTORY_GRID_MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pygame.Rect(145, 522, 245, 44).collidepoint(event.pos):
                        player["_confirm_wipe_grid"] = False
                        set_state("START_SCREEN", "")
                        continue
                    if pygame.Rect(410, 522, 245, 44).collidepoint(event.pos):
                        if not player.get("_confirm_wipe_grid"):
                            player["_confirm_wipe_grid"] = True
                        else:
                            from mechanics import wipe_profile_data
    
                            wipe_profile_data("noburu")
                            player["_confirm_wipe_grid"] = False
                        continue
    
            # Prevent Decimal Clock from intercepting clicks on full-screen modals
            if menu_state not in (
                "START_SCREEN",
                "CHAPTER_1_INTRO",
                "CASINO_BLACKJACK",
                "CASINO_POKER",
                "CASINO_ROULETTE",
                "CASINO_CRAPS",
                "MINIGAME_ARCHERY",
                "MAP_VIEW",
                "CH3_MORNING_PHASE",
                "CH3_AFTERNOON_PHASE",
                "CH3_EVENING_PHASE",
                "CH3_EPILOGUE",
                "VICTORY_GRID_MENU",
                "INVENTORY_MENU",
                "STATUS_MENU",
                "SYSTEM_MENU",
                "CHAPTER_2_COMPLETE",
                "MINIGAME_BARGAIN",
                "MINIGAME_BRAWL",
                "MINIGAME_TRIBUNAL",
                "MINIGAME_TRAITOR",
                "MINIGAME_RIOT",
                "MINIGAME_SEARCH",
                "MINIGAME_DUNGEON",
                "MINIGAME_TYPESET",
                "MINIGAME_WEATHER_REPORT",
                "MINIGAME_CODEWHEEL",
                "MINIGAME_PONTIFEX",
                "MINIGAME_GCHQ",
            ):
                if game_clock_ui.handle_event(event):
                    continue
    
            if menu_state == "CASINO_POKER":
                mini_games.handle_poker_input_event(event, player)
            elif menu_state == "CASINO_ROULETTE":
                mini_games.handle_roulette_event(event, player)
            elif menu_state == "CASINO_CRAPS":
                mini_games.handle_craps_event(event, player)
            elif menu_state == "MINIGAME_ARCHERY":
                player, arch_log, next_state = mini_games.handle_archery_event(
                    event, player
                )
                if arch_log:
                    add_log(arch_log)
                if next_state != "MINIGAME_ARCHERY":
                    set_state(next_state)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    continue
    
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
                if (
                    menu_state == "MINIGAME_BARGAIN"
                    and player.get("bargain_phase") == "SLIDER_PLAYER"
                ):
                    is_drag = (
                        event.type == pygame.MOUSEMOTION
                        and pygame.mouse.get_pressed()[0]
                    )
                    is_click = (
                        event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    )
                    if (
                        is_drag or is_click
                    ) and mini_games.BARGAIN_SLIDER_RECT.inflate(
                        16, 18
                    ).collidepoint(event.pos):
                        d_id = player.get("bargain_selected_id")
                        d_obj = next(
                            (
                                d
                                for d in mini_games.BARGAIN_DEMANDS
                                if d["id"] == d_id
                            ),
                            None,
                        )
                        if d_obj:
                            min_v = 8 if d_id == "u_hours" else 0
                            raw_pct = (
                                event.pos[0] - mini_games.BARGAIN_SLIDER_RECT.x
                            ) / float(mini_games.BARGAIN_SLIDER_RECT.width)
                            clamped_pct = max(0.0, min(1.0, raw_pct))
                            player["bargain_slider_val"] = int(
                                round(
                                    min_v + clamped_pct * (d_obj["max_val"] - min_v)
                                )
                            )
    
            if event.type == pygame.MOUSEBUTTONDOWN:
                button_clicked = False
                if event.button == 1:
                    for btn in all_active_buttons:
                        if btn.handle_event(event):
                            button_clicked = True
                            break
                if button_clicked:
                    continue
    
                if menu_state == "MINIGAME_SEARCH":
                    handled_s, s_log, s_next = (
                        search_engine.handle_search_canvas_event(event, player)
                    )
                    if handled_s:
                        if s_log:
                            add_log(s_log)
                        set_state(s_next)
                        check_master_clock()
                        continue
    
                if menu_state == "MINIGAME_JIGSAW":
                    player, jigsaw_log, next_state = (
                        mini_games.handle_jigsaw_event(event, player)
                    )
                    if jigsaw_log:
                        add_log(jigsaw_log)
                    if next_state != "MINIGAME_JIGSAW":
                        set_state(next_state)
                    continue
    
                elif menu_state == "MINIGAME_SOUNDING":
                    player, sound_log, next_state = (
                        mini_games.handle_sounding_event(event, player)
                    )
                    if sound_log:
                        add_log(sound_log)
                    if next_state != "MINIGAME_SOUNDING":
                        set_state(next_state)
                    if event.pos[1] < 390:
                        continue
    
                elif menu_state == "MINIGAME_BREACH":
                    player, breach_log, next_state = (
                        mini_games.handle_breach_event(event, player)
                    )
                    if breach_log:
                        add_log(breach_log)
                    if next_state != "MINIGAME_BREACH":
                        set_state(next_state)
                    if event.pos[1] < 390:
                        continue
    
                elif menu_state == "MINIGAME_DEDUCTION":
                    player, deduct_log, next_state = (
                        mini_games.handle_deduction_event(event, player)
                    )
                    if deduct_log:
                        add_log(deduct_log)
                    if next_state != "MINIGAME_DEDUCTION":
                        set_state(next_state)
                    if event.pos[1] < 390:
                        continue
    
                elif menu_state == "MINIGAME_PARAPET":
                    player, parapet_log, next_state = (
                        mini_games.handle_parapet_event(event, player)
                    )
                    if parapet_log:
                        add_log(parapet_log)
                    if next_state != "MINIGAME_PARAPET":
                        set_state(next_state)
                    if event.pos[1] < 390:
                        continue
    
                elif menu_state == "MINIGAME_FLYTIP":
                    player, flytip_log, next_state = (
                        mini_games.handle_flytip_event(event, player)
                    )
                    if flytip_log:
                        add_log(flytip_log)
                    if next_state != "MINIGAME_FLYTIP":
                        set_state(next_state)
                    if event.pos[1] < 390:
                        continue
    
            if event.type == pygame.MOUSEWHEEL:
                location_panel_ui.handle_scroll(mouse_pos, event.y)
                log_panel_ui.handle_scroll(mouse_pos, event.y)
    
        # --- FULL-SCREEN RENDERS (TITLE, MAP, AND ALL CHAPTER 3 SCREENS) ---
        if menu_state in ("START_SCREEN", "CHAPTER_1_INTRO"):
            draw_title_or_intro_card(screen, menu_state)
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CHAPTER_2_COMPLETE":
            if "ch3_world_summary" not in player:
                rank, summary = evaluate_chapter_3_state(player)
                player["ch3_rank"] = rank
                player["ch3_world_summary"] = summary
            meta_progression.draw_chapter_2_completion_card(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "MAP_VIEW":
            draw_cartographic_map(
                screen, active_map_key, player, world_map, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CH3_MORNING_PHASE":
            ui_renderer.draw_ch3_morning_ui(
                screen, player, FONT, FONT_BOLD, world_map, mouse_pos
            )
            ch3_tutorial_book.draw_tutorial_spotlight_overlay(
                screen, player, FONT_BOLD
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CH3_AFTERNOON_PHASE":
            ai_q = player.get("ch3_ai_turn_queue", [])
            pacing = player.get("ch3_ai_pacing", "NORMAL")
            if (
                ai_q
                and player.get("ch3_show_ai_moves", True)
                and pacing in ("SLOW", "NORMAL", "FAST")
            ):
                delay_ms = {"SLOW": 1800, "NORMAL": 1150, "FAST": 500}[pacing]
                now_t = pygame.time.get_ticks()
                if now_t - player.get("ch3_ai_step_timer", now_t) >= delay_ms:
                    ai_q.pop(0)
                    player["ch3_ai_step_timer"] = now_t
                    if ai_q:
                        ai_q[0]["anim_start"] = now_t
                        ch3_board_renderer.centre_camera_on_tile(
                            player,
                            ai_q[0].get("to_pos", ai_q[0].get("capital")),
                        )
                    else:
                        ch3_board_renderer.centre_camera_on_player_forces(player)
                        pending = player.get("ch3_pending_clashes", [])
                        if pending:
                            first_c = pending.pop(0)
                            player = ch3_combat_engine.init_ch3_evening_clash(
                                player,
                                first_c["attacker"],
                                first_c["defender"],
                                first_c["tile_pos"],
                                world_map,
                                origin_pos=first_c.get("origin_pos"),
                            )
                            set_state(
                                "CH3_EVENING_PHASE",
                                "Dusk falls: Resolving pinned engagements!",
                            )
                            continue
                        player["ch3_day"] = player.get("ch3_day", 1) + 1
                        player = ui_renderer.init_ch3_morning_phase(player)
                        set_state(
                            "CH3_MORNING_PHASE",
                            f"Dawn breaks on Day {player['ch3_day']}.",
                        )
                        continue
    
            ui_renderer.draw_ch3_afternoon_ui(
                screen,
                player,
                world_map,
                FONT,
                FONT_BOLD,
                ch3_cam_x,
                ch3_cam_y,
                ch3_zoom,
                mouse_pos,
                ch3_selected_army_pos,
            )
            ch3_tutorial_book.draw_tutorial_spotlight_overlay(
                screen, player, FONT_BOLD
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CH3_EVENING_PHASE":
            ui_renderer.draw_ch3_evening_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            ch3_tutorial_book.draw_tutorial_spotlight_overlay(
                screen, player, FONT_BOLD
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CH3_SETTINGS_MODAL":
            ui_renderer.draw_ch3_morning_ui(
                screen, player, FONT, FONT_BOLD, world_map, mouse_pos
            )
            ui_renderer.draw_ch3_settings_modal(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CH3_RULEBOOK_MODAL":
            ui_renderer.draw_ch3_morning_ui(
                screen, player, FONT, FONT_BOLD, world_map, mouse_pos
            )
            ch3_tutorial_book.draw_ch3_rulebook_modal(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "CH3_TUTORIAL_SELECT":
            ui_renderer.draw_ch3_morning_ui(
                screen, player, FONT, FONT_BOLD, world_map, mouse_pos
            )
            ch3_tutorial_book.draw_ch3_tutorial_select_modal(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "PNP_LOBBY_MODAL":
            if pass_and_play.get_session().get("in_chapter_3"):
                ui_renderer.draw_ch3_morning_ui(
                    screen, player, FONT, FONT_BOLD, world_map, mouse_pos
                )
            pass_and_play.draw_pnp_lobby_modal(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "PNP_HANDOVER_CURTAIN":
            pass_and_play.draw_pnp_handover_curtain(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            present_screen()
            clock.tick(60)
            continue
        
        if menu_state == "CH3_EPILOGUE":
            ui_renderer.draw_ch3_epilogue_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            present_screen()
            clock.tick(60)
            continue
    
        if menu_state == "VICTORY_GRID_MENU":
            ui_renderer.draw_victory_grid_ui(
                screen, FONT, FONT_BOLD, mouse_pos, player
            )
            present_screen()
            clock.tick(60)
            continue
    
        # --- STANDARD CHAPTER 1 & 2 RPG RENDER ---
        visual_backdrop.draw_world_backdrop(screen, player, world_map)
        weather_engine.draw_weather_and_darkness_overlay(
            screen, player, FONT, FONT_BOLD, mouse_pos
        )
        weather_engine.draw_topographic_contour_overlay(screen, player, world_map)
    
        loc_typewriter_idx += 4
        total_log_chars = sum(len(str(line)) for line in log_history)
        if log_typewriter_idx < total_log_chars:
            log_typewriter_idx += 4
    
        current_loc = None
        owner = None
        if player["current_building"]:
            current_loc = player["current_building"]
            loc_name = db.building_database[player["current_building"]]["name"]
            loc_desc = db.building_database[player["current_building"]][
                "description"
            ]
        else:
            pos = (player["x"], player["y"])
            current_loc = pos
            if pos in world_map:
                owner = get_tile_territory(player, pos[0], pos[1])
                loc_name = world_map[pos].name
                loc_desc = world_map[pos].description
                current_day = (player["total_game_minutes"] // 1000) + 1
                if player["rosinante_last_fed_day"] == current_day or player.get(
                    "rosinante_fed"
                ):
                    loc_desc = loc_desc.replace(" It looks hungry.", "").replace(
                        "It looks hungry.", ""
                    )
            else:
                loc_name = "Unmapped Wilderness"
                loc_desc = "You have wandered into the unmapped wilderness."
    
        if current_loc == (7, 15):
            if db.npc_database["horse"]["location"] == (7, 15):
                current_day = (player["total_game_minutes"] // 1000) + 1
                if player.get("rosinante_last_fed_day") == current_day:
                    loc_desc += (
                        "\nOne horse stands tethered to a pole outside, munching "
                        "contentedly on the remnants of its snack."
                    )
                else:
                    loc_desc += (
                        "\nOne horse stands tethered to a pole outside, eating "
                        "some hay and awaiting attention. It looks hungry."
                    )
            else:
                loc_desc += (
                    "\nA pole stands upright, a tether blowing in the wind, and "
                    "a pile of half eaten hay at its base."
                )
    
        people_here = [
            db.npc_database[npc_id]["proper_name"]
            for npc_id in get_npcs_at_current_location()
        ]
        if people_here:
            loc_desc += f"\nYou see people: {', '.join(people_here)}."
    
        if not player["current_building"] and current_loc in world_map:
            display_objects = [
                obj
                for obj in world_map[current_loc].objects
                if obj.lower() != "horse"
            ]
            if display_objects:
                loc_desc += f" You see objects: {', '.join(display_objects)}"
    
        if current_loc in [(7, 15), "stables", "tack room", "stable loft"]:
            if player.get(
                "active_blacksmith_task"
            ) == "stables_fire_rescue" and not player.get("fire_extinguished"):
                loc_desc = (
                    "*** THE BARN IS ON FIRE! Thick, choking black smoke billows "
                    "from the stalls! ***\n\n" + loc_desc
                )
    
        if menu_state.startswith("MINIGAME_") or menu_state.startswith("CASINO_"):
            log_panel_ui.rect = pygame.Rect(40, 164, 408, 218)
        else:
            log_panel_ui.rect = pygame.Rect(40, 164, 720, 204)
    
        location_panel_ui.draw_location_panel(
            screen, loc_name, loc_desc, loc_typewriter_idx, territory_owner=owner
        )
        log_panel_ui.draw_log_panel(screen, log_history, log_typewriter_idx)
    
        cur_pos = (player["x"], player["y"])
        blind_in_forest = (
            player.get("current_building") is None
            and cur_pos in world_map
            and world_map[cur_pos].region == "The Forest"
            and "compass" not in player.get("inventory", [])
            and "carved yew wayfinder" not in player.get("inventory", [])
        )
        for btn in dpad_buttons:
            btn.enabled = menu_state == "MAIN"
            btn.show_labels = not blind_in_forest
    
        for btn in all_active_buttons:
            btn.draw(screen, mouse_pos)
    
        # --- COMPACT STATUS HUD BAR ABOVE DECIMAL CLOCK ---
        hud_font = pygame.font.Font(None, 18)
        curr_w = get_inventory_weight(player)
        max_w = get_max_carry_weight(player)
        hud_line1 = (
            f"HP: {player['health']}/{player['max_health']}  |  "
            f"Silver: {player['silver']}s  |  Wt: {curr_w}/{max_w}"
        )
        hud_line2 = (
            f"Food: {player['hunger']:.0f}%  |  "
            f"Water: {player['thirst']:.0f}%  |  Rep: {player['reputation']}"
        )
        screen.blit(hud_font.render(hud_line1, True, TEXT_COLOR), (32, 392))
        screen.blit(hud_font.render(hud_line2, True, TEXT_MUTED), (32, 410))
    
        badges = []
        if player.get("afflictions"):
            badges.append("[ILL/POISONED]")
        if curr_w > max_w:
            badges.append("[HEAVY]")
        if player.get("horse_stabled"):
            badges.append(f"[STABLE TAB: {get_stabling_debt(player)}s]")
        if badges:
            screen.blit(
                hud_font.render(" ".join(badges), True, (235, 95, 95)), (32, 428)
            )
    
        game_clock_ui.draw(screen, player["total_game_minutes"], LOCATION_ACCENT)
        pass_and_play.draw_pnp_turn_hud_pill(screen, player, FONT_BOLD)
    
        # --- MINIGAME UI OVERLAYS ---
        if menu_state == "MINIGAME_FORGE":
            mini_games.draw_forge_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_JIGSAW":
            mini_games.draw_jigsaw_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_CHASE":
            mini_games.draw_chase_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_SOUNDING":
            mini_games.draw_sounding_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_BREACH":
            mini_games.draw_breach_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_DEDUCTION":
            mini_games.draw_deduction_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_PARAPET":
            mini_games.draw_parapet_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_SMUGGLE":
            mini_games.draw_smuggle_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_RECIPE":
            mini_games.draw_recipe_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_FLYTIP":
            mini_games.draw_flytip_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_DRILL":
            mini_games.draw_drill_ui(screen, player, FONT, FONT_BOLD)
        elif menu_state == "MINIGAME_DEBATE":
            mini_games.draw_debate_ui(screen, player, FONT, FONT_BOLD)
    
        if menu_state in (
            "CASINO_BLACKJACK",
            "CASINO_POKER",
            "CASINO_ROULETTE",
            "CASINO_CRAPS",
        ):
            mini_games.draw_casino_card_table(
                screen, player, FONT, FONT_BOLD, TITLE_FONT, menu_state
            )
            for btn in all_active_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_ARCHERY":
            mini_games.draw_archery_ui(
                screen, player, FONT, FONT_BOLD, TITLE_FONT
            )
            for btn in all_active_buttons:
                btn.draw(screen, mouse_pos)
    
        # --- POPUPS ---
        if menu_state == "STATUS_MENU":
            ui_renderer.draw_status_popup(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "INVENTORY_MENU":
            ui_renderer.draw_inventory_popup(
                screen, player, mouse_pos, FONT, FONT_BOLD
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "SYSTEM_MENU":
            ui_renderer.draw_help_popup(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_BARGAIN":
            mini_games.draw_bargain_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_BRAWL":
            ch2_union.draw_brawl_ui(screen, player, FONT, FONT_BOLD, mouse_pos)
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_TRIBUNAL":
            ch2_union.draw_tribunal_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_TRAITOR":
            ch2_union.draw_traitor_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_RIOT":
            ch2_guard.draw_riot_ui(screen, player, FONT, FONT_BOLD, mouse_pos)
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_STRIKE_CORDON":
            ch2_guard.draw_strike_cordon_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_CONVOY":
            ch2_guard.draw_convoy_ui(screen, player, FONT, FONT_BOLD, mouse_pos)
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_WATCH_SPLIT":
            ch2_guard.draw_watch_split_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_HERDING":
            ch2_castellan.draw_herding_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_HUNT":
            ch2_castellan.draw_hunt_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_LANCERS":
            ch2_castellan.draw_lancers_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_SUMMIT":
            ch2_castellan.draw_summit_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_LEVY":
            ch2_castellan.draw_levy_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_DUNGEON":
            ch2_dungeons.draw_dungeon_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_PARVUS":
            ch2_parvus.draw_parvus_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_ELECTION":
            ch2_election.draw_election_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_ROGUERY":
            ch2_roguery.draw_roguery_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_SEARCH":
            search_engine.draw_search_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_TRACK_TABLE":
            meta_progression.draw_track_requirements_table_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_CODEWHEEL":
            cryptography_engine.draw_codewheel_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_PONTIFEX":
            cryptography_engine.draw_pontifex_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_GCHQ":
            cryptography_engine.draw_gchq_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
                
        elif menu_state == "MINIGAME_TYPESET":
            printing_press_engine.draw_typeset_ui(
                screen, player, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
        elif menu_state == "MINIGAME_WEATHER_REPORT":
            weather_engine.draw_weather_report_modal(
                screen, player, world_map, FONT, FONT_BOLD, mouse_pos
            )
            for btn in right_buttons:
                btn.draw(screen, mouse_pos)
    
        present_screen()
    
        # --- REAL-TIME ENGINE TICK ---
        dt = clock.tick(60) / 1000.0
    
        if menu_state == "MINIGAME_FORGE":
            player, mini_log, next_state = mini_games.update_forge_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_FORGE":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_CHASE":
            player, mini_log, next_state = mini_games.update_chase_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_CHASE":
                if next_state == "NPC_DIALOGUE":
                    selected_target = "market manager"
                set_state(next_state)
    
        elif menu_state == "MINIGAME_JIGSAW" and player.get("arcade_mode"):
            player, mini_log, next_state = mini_games.update_jigsaw_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_JIGSAW":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_RECIPE" and player.get("arcade_mode"):
            player, mini_log, next_state = mini_games.update_recipe_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_RECIPE":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_FLYTIP" and player.get("arcade_mode"):
            player, mini_log, next_state = mini_games.update_flytip_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_FLYTIP":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_SOUNDING" and player.get("arcade_mode"):
            player, mini_log, next_state = mini_games.update_sounding_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_SOUNDING":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_ARCHERY":
            player, mini_log, next_state = mini_games.update_archery_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_ARCHERY":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_DRILL":
            player, mini_log, next_state = mini_games.update_drill_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_DRILL":
                set_state(next_state)
    
        elif menu_state == "MINIGAME_DEBATE":
            player, mini_log, next_state = mini_games.update_debate_timer(
                player, dt
            )
            if mini_log:
                add_log(mini_log)
            if next_state != "MINIGAME_DEBATE":
                set_state(next_state)

        await asyncio.sleep(0)


asyncio.run(main())
        

            
