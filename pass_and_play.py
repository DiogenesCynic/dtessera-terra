"""
pass_and_play.py
----------------
Manages Full-Campaign Setup & Pass-and-Play Multiplayer from Chapter 1
(Murum Town) through Chapter 2 (Regional Missions) and Chapter 3 (The 3D
Tabletop War):
- In Chapter 1 Setup: Players choose a Travelling Name (preset or typed
  via keyboard), a Traveller Cloak Colour, and a 3D Dice Palette—leaving
  their future Chapter 3 Faction completely undetermined until earned!
- In Chapter 3 Skirmish Setup (Unlocked ONLY after completing the game at
  least once in `profile_noburu_meta.json`): Players choose their
  Chapter 3 Faction Banner and launch directly onto the War Table.
"""

import copy
import json
import os
import pygame

import ch3_board_renderer
import ch3_war_engine
from ui_components import draw_fitted_text
import weather_engine

# --- HERITAGE PALETTE CONSTANTS ---
TATE_RED = (168, 50, 35)
DIAL_CREAM = (244, 239, 225)
CLOCK_BLACK = (28, 26, 24)
GOLD_ACCENT = (195, 148, 48)
GOLD_BRIGHT = (250, 215, 85)
OAK_DARK = (46, 33, 25)
OAK_MID = (66, 48, 36)
EQUIPPED_GREEN = (45, 125, 68)
LOCKED_GREY = (96, 90, 84)

SLICE_OPTIONS = (200, 500, 1000)  # 2h, 5h, or 10h in Decimal Minutes
VICTORY_MODES = ("100_PTS", "250_PTS", "DOMINATION")
DICE_STYLES = (
    "bone dice",
    "brass wallmaker dice",
    "jade kokeshi dice",
    "obsidian vanguard dice",
    "star-iron guild dice",
)
FACTION_KEYS = (
    "Union",
    "Kokeshi",
    "Laydere",
    "Ragmore",
    "FAI",
    "Communards",
    "Vanguardists",
)

# Chapter 1 & 2 Traveller Cloak Colours (Destiny Undetermined!)
TRAVELLER_COLOURS = (
    ("Tate Crimson", (168, 50, 35), (240, 215, 145)),
    ("Woad Blue", (45, 88, 165), (215, 225, 240)),
    ("Lincoln Green", (42, 132, 74), (225, 238, 180)),
    ("Saffron Gold", (185, 132, 34), (250, 238, 195)),
    ("Tyrian Violet", (112, 48, 142), (235, 195, 75)),
    ("Charcoal Slate", (58, 62, 70), (210, 215, 222)),
    ("Russet Ochre", (148, 72, 38), (242, 212, 165)),
)

TRAVELLER_NAMES = (
    "Noburu",
    "Peregrine",
    "Rowan",
    "Alba",
    "Ceara",
    "Osric",
    "Mairead",
    "Bram",
    "Sorrel",
    "Vesper",
    "Tadhg",
    "Linnet",
)

SHARED_WORLD_KEYS = (
    "ch3_world_bits",
    "pnp_claimed_routes",
    "pnp_Everpenitent_map_won",
    "territories",
    "ch3_armies",
    "ch3_barricades",
    "ch3_factions",
    "ch3_pending_clashes",
    "ch3_day",
    "ch3_victory_mode",
    "current_month_idx",
    "weather_condition",
    "ground_saturation",
    "snowpack_level",
)

SAFE_HANDOVER_STATES = ("MAIN", "CHAPTER_2_BOARD")

_PNP_SESSION = {
    "enabled": False,
    "num_players": 1,
    "slice_minutes": 500,
    "outbreak_mode": "RACE",
    "active_idx": 0,
    "handover_pending": False,
    "in_chapter_3": False,
    "ch3_turn_order": [],
    "ch3_order_pos": 0,
    "seats": [],
}

_PNP_LOBBY_CFG = {
    "num_players": 1,
    "slice_minutes": 500,
    "outbreak_mode": "RACE",
    "start_stage": "CH1",  # 'CH1' (Campaign) or 'CH3' (War Table Skirmish)
    "editing_seat_name": None,
    "month_idx": 1,
    "victory_mode": "100_PTS",
    "seats": [
        {
            "name": TRAVELLER_NAMES[i],
            "name_idx": i,
            "color_idx": i % len(TRAVELLER_COLOURS),
            "faction": FACTION_KEYS[i],
            "dice": DICE_STYLES[i % len(DICE_STYLES)],
        }
        for i in range(4)
    ],
}

HANDOVER_BTN_RECT = pygame.Rect(210, 442, 380, 54)


def is_ch3_start_unlocked():
    """
    Returns True ONLY if the player has completed the game at least once
    (recorded in `profile_noburu_meta.json`).
    """
    if not os.path.exists("profile_noburu_meta.json"):
        return False
    try:
        with open(
            "profile_noburu_meta.json", "r", encoding="utf-8"
        ) as file_obj:
            meta = json.load(file_obj)
        if meta.get("total_campaigns_won", 0) >= 1:
            return True
        if len(meta.get("victory_grid", [])) >= 1:
            return True
    except (OSError, ValueError):
        pass
    return False


def _get_lobby_rects():
    """Returns the deterministic dictionary of all clickable Rects in the Lobby."""
    rects = {
        "cycle_count": pygame.Rect(64, 58, 214, 36),
        "cycle_slice": pygame.Rect(288, 58, 218, 36),
        "cycle_month": pygame.Rect(516, 58, 220, 36),
        "cycle_victory": pygame.Rect(64, 100, 330, 34),
        "cycle_stage": pygame.Rect(406, 100, 330, 34),
        "start_pnp_campaign": pygame.Rect(64, 496, 256, 48),
        "start_pnp_ch3": pygame.Rect(332, 496, 256, 48),
        "close_pnp_lobby": pygame.Rect(600, 496, 136, 48),
    }
    for idx in range(4):
        ry = 142 + idx * 86
        rects[f"seat_name_{idx}"] = pygame.Rect(74, ry + 9, 138, 60)
        rects[f"seat_col_or_fac_{idx}"] = pygame.Rect(222, ry + 15, 244, 48)
        rects[f"seat_dice_{idx}"] = pygame.Rect(478, ry + 15, 246, 48)
    return rects


# =========================================================================
# 1. SESSION INITIALISATION & SEAT TEMPLATE BUILDER
# =========================================================================
def is_pnp_enabled(player=None):
    """Returns True if multi-player Pass-and-Play mode (2+ players) is active."""
    return bool(
        _PNP_SESSION.get("enabled") and _PNP_SESSION.get("num_players", 1) > 1
    )


def get_session():
    """Returns the global Pass-and-Play session dictionary."""
    return _PNP_SESSION


def _draw_traveller_cloak_meeple(screen, cx, cy, scale, rgb_col, trim_col):
    """Draws a wooden Traveller Meeple in the player's chosen Cloak Colour."""
    dark = (
        max(0, rgb_col[0] - 55),
        max(0, rgb_col[1] - 55),
        max(0, rgb_col[2] - 55),
    )
    w = max(6, int(10 * scale))
    h = max(10, int(18 * scale))

    sh_rect = pygame.Rect(cx - w, cy - 3, w * 2, 6)
    pygame.draw.ellipse(screen, (25, 20, 16), sh_rect)

    body_pts = [
        (cx - w + 1, cy),
        (cx - 2, cy - int(h * 0.28)),
        (cx + 2, cy - int(h * 0.28)),
        (cx + w - 1, cy),
        (cx + w, cy - int(h * 0.42)),
        (cx + int(w * 0.55), cy - int(h * 0.55)),
        (cx + int(w * 0.95), cy - int(h * 0.72)),
        (cx + int(w * 0.45), cy - int(h * 0.88)),
        (cx - int(w * 0.45), cy - int(h * 0.88)),
        (cx - int(w * 0.95), cy - int(h * 0.72)),
        (cx - int(w * 0.55), cy - int(h * 0.55)),
        (cx - w, cy - int(h * 0.42)),
    ]
    bevel_pts = [(px + 2, py + 2) for px, py in body_pts]
    pygame.draw.polygon(screen, dark, bevel_pts)
    pygame.draw.polygon(screen, rgb_col, body_pts)
    pygame.draw.polygon(screen, trim_col, body_pts, 1)

    head_y = cy - h - max(2, int(2 * scale))
    head_r = max(3, int(4.5 * scale))
    pygame.draw.circle(screen, dark, (cx + 2, head_y + 2), head_r)
    pygame.draw.circle(screen, rgb_col, (cx, head_y), head_r)
    pygame.draw.circle(screen, trim_col, (cx, head_y), head_r, 1)


def _create_fresh_seat_dict(
    template_player, seat_idx, name, dice_style, fac, col_idx=0
):
    """Creates a clean starting state for a human seat."""
    seat = copy.deepcopy(template_player)
    c_name, c_rgb, c_trim = TRAVELLER_COLOURS[col_idx % len(TRAVELLER_COLOURS)]
    seat["pnp_seat_idx"] = seat_idx
    seat["pnp_player_name"] = name
    seat["pnp_colour_name"] = c_name
    seat["pnp_colour_rgb"] = list(c_rgb)
    seat["pnp_colour_trim"] = list(c_trim)
    seat["equipped_dice"] = dice_style
    seat["ch3_faction"] = fac
    seat["pnp_slice_used"] = 0
    seat["pnp_slice_limit"] = _PNP_SESSION["slice_minutes"]
    seat["pnp_enabled"] = _PNP_SESSION["enabled"]

    if dice_style not in seat.get("inventory", []):
        seat.setdefault("inventory", []).append(dice_style)
    return seat


def init_pnp_campaign(
    base_player,
    num_players=1,
    slice_minutes=500,
    outbreak_mode="RACE",
    custom_configs=None,
    start_in_ch3=False,
):
    """
    Initialises a 1-to-4 player campaign from `base_player`.
    In Chapter 1 mode (`start_in_ch3=False`), players start with their
    chosen Travelling Name and Cloak Colour, and their future Chapter 3
    Faction remains undetermined until Chapter 2/3!
    """
    num_p = max(1, min(7, int(num_players)))
    _PNP_SESSION["enabled"] = num_p > 1
    _PNP_SESSION["num_players"] = num_p
    _PNP_SESSION["slice_minutes"] = int(slice_minutes)
    _PNP_SESSION["outbreak_mode"] = outbreak_mode
    _PNP_SESSION["active_idx"] = 0
    _PNP_SESSION["handover_pending"] = False
    _PNP_SESSION["in_chapter_3"] = bool(start_in_ch3)
    _PNP_SESSION["seats"] = []

    base_player.setdefault("ch3_world_bits", {})
    base_player.setdefault("pnp_claimed_routes", {})

    clean_template = {
        k: copy.deepcopy(v)
        for k, v in base_player.items()
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

    for idx in range(num_p):
        cfg = (
            custom_configs[idx]
            if (custom_configs and idx < len(custom_configs))
            else {}
        )
        p_name = cfg.get("name", TRAVELLER_NAMES[idx % len(TRAVELLER_NAMES)])
        d_style = cfg.get("dice", DICE_STYLES[idx % len(DICE_STYLES)])
        col_i = cfg.get("color_idx", idx % len(TRAVELLER_COLOURS))
        f_key = (
            cfg.get("faction", FACTION_KEYS[idx % len(FACTION_KEYS)])
            if start_in_ch3
            else None
        )
        seat = _create_fresh_seat_dict(
            clean_template, idx, p_name, d_style, f_key, col_idx=col_i
        )
        if not start_in_ch3:
            seat.pop("ch3_rank", None)
            if idx > 0:
                seat["x"], seat["y"] = 8, 14
                seat["current_building"] = "school"
                seat["current_job"] = None
                seat["current_tenure"] = 0
                seat["chapter_2_route"] = None
                seat["ch2_mission_step"] = 1
                seat["position_strength"] = 0
                seat["exposure_tells"] = 0
        _PNP_SESSION["seats"].append(seat)

    _load_seat_into_active_player(base_player, 0)
    return base_player


def _sync_shared_keys_from_active(active_player):
    """Copies shared world state from `active_player` into all seats."""
    for s_dict in _PNP_SESSION.get("seats", []):
        for key in SHARED_WORLD_KEYS:
            if key in active_player:
                s_dict[key] = copy.deepcopy(active_player[key])


def _save_active_player_to_seat(active_player, seat_idx):
    """Saves the current `active_player` state back into its seat slot."""
    seats = _PNP_SESSION.get("seats", [])
    if not (0 <= seat_idx < len(seats)):
        return
    _sync_shared_keys_from_active(active_player)

    clean_copy = {
        k: copy.deepcopy(v)
        for k, v in active_player.items()
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
    seats[seat_idx] = clean_copy


def _load_seat_into_active_player(active_player, seat_idx):
    """Loads `seats[seat_idx]` into the live `active_player` dict in-place."""
    seats = _PNP_SESSION.get("seats", [])
    if not (0 <= seat_idx < len(seats)):
        return active_player

    target_seat = copy.deepcopy(seats[seat_idx])
    active_player.clear()
    active_player.update(target_seat)
    active_player["pnp_enabled"] = _PNP_SESSION["enabled"]
    active_player["pnp_seat_idx"] = seat_idx
    active_player["pnp_player_name"] = target_seat.get(
        "pnp_player_name", f"Player {seat_idx + 1}"
    )
    active_player["pnp_slice_limit"] = _PNP_SESSION["slice_minutes"]
    return active_player


# =========================================================================
# 2. DECIMAL-CLOCK TIME-SLICE TRACKER (CHAPTERS 1 & 2)
# =========================================================================
def record_time_advanced(player, minutes_spent):
    """Tracks how many decimal minutes the current human player has used."""
    if not is_pnp_enabled(player) or _PNP_SESSION.get("in_chapter_3"):
        return

    used = player.get("pnp_slice_used", 0) + max(0, int(minutes_spent))
    limit = _PNP_SESSION.get("slice_minutes", 500)
    player["pnp_slice_used"] = used
    player["pnp_slice_limit"] = limit

    if used >= limit:
        _PNP_SESSION["handover_pending"] = True


def should_trigger_ch1_ch2_handover(player, current_menu_state):
    """Returns True when the current player's time slice has expired in 'MAIN'."""
    if not is_pnp_enabled(player) or _PNP_SESSION.get("in_chapter_3"):
        return False
    if not _PNP_SESSION.get("handover_pending"):
        return False
    return current_menu_state in SAFE_HANDOVER_STATES


def rotate_to_next_pnp_player(player):
    """Rotates to the next human player when their Decimal-Hour slice ends."""
    seats = _PNP_SESSION.get("seats", [])
    if len(seats) <= 1:
        _PNP_SESSION["handover_pending"] = False
        return player

    cur_idx = _PNP_SESSION.get("active_idx", 0)
    limit = _PNP_SESSION.get("slice_minutes", 500)
    overtime = max(0, player.get("pnp_slice_used", 0) - limit)
    player["pnp_slice_used"] = min(limit // 2, overtime)

    _save_active_player_to_seat(player, cur_idx)

    next_idx = (cur_idx + 1) % len(seats)
    _PNP_SESSION["active_idx"] = next_idx
    _PNP_SESSION["handover_pending"] = False

    _load_seat_into_active_player(player, next_idx)
    return player


# =========================================================================
# 3. COMPETITIVE NOTICEBOARD CLAIMS & CROSSING PATHS ON THE MAP
# =========================================================================
def filter_unclaimed_ch2_routes(player, eligible_routes):
    """Removes Chapter 2 Noticeboard routes already claimed by another player."""
    if not is_pnp_enabled(player):
        return eligible_routes

    claimed = player.get("pnp_claimed_routes", {})
    my_name = player.get("pnp_player_name", "Player 1")
    filtered = [
        r for r in eligible_routes if claimed.get(r) in (None, my_name)
    ]
    return filtered if filtered else eligible_routes


def claim_ch2_route_for_seat(player, chosen_route):
    """Stamps `chosen_route` as claimed by the active human player."""
    claimed = player.setdefault("pnp_claimed_routes", {})
    my_name = player.get("pnp_player_name", "Player 1")
    claimed[chosen_route] = my_name

    route_to_fac = {
        "Stand for Union Official": "Union",
        "Apply for Town Guard": "Laydere",
        "Join Castellan's House Staff": "Ragmore",
        "Parvus: F.A.I.-C.N.T. Syndicate": "FAI",
        "Parvus: Crown Intelligencers": "Laydere",
        "Parvus: Maritime & Artisans Guild (50s)": "Union",
        "Run for Public Office (50s)": "Union",
        "Join Wallmaker Syndicate": "Kokeshi",
        "Become a Highway Robber": "Vanguardists",
        "Join Fairlight's Acting Troupe": "Communards",
    }
    if chosen_route in route_to_fac:
        player["ch3_faction"] = route_to_fac[chosen_route]
    _sync_shared_keys_from_active(player)


def get_rivals_at_current_tile(player):
    """Returns any other human Pass-and-Play players on the same (x, y) tile."""
    if not is_pnp_enabled(player):
        return []

    my_idx = player.get("pnp_seat_idx", 0)
    mx, my = player.get("x", 10), player.get("y", 15)
    m_bldg = player.get("current_building")
    rivals = []

    for idx, seat in enumerate(_PNP_SESSION.get("seats", [])):
        if idx == my_idx:
            continue
        if (
            seat.get("x") == mx
            and seat.get("y") == my
            and seat.get("current_building") == m_bldg
        ):
            rivals.append((
                idx,
                seat.get("pnp_player_name", f"Player {idx + 1}"),
                seat,
            ))
    return rivals


# =========================================================================
# 4. CHAPTER 3 MULTI-HUMAN SEAT ROTATION & WAR OUTBREAK SYNC
# =========================================================================
def get_human_factions_map():
    """Returns a dict mapping `faction_key -> seat_idx` for all human seats."""
    if not _PNP_SESSION.get("enabled"):
        return {}
    mapping = {}
    used_facs = set()
    for idx, seat in enumerate(_PNP_SESSION.get("seats", [])):
        fac = seat.get("ch3_faction") or FACTION_KEYS[idx % len(FACTION_KEYS)]
        if fac in used_facs:
            for alt_f in FACTION_KEYS:
                if alt_f not in used_facs:
                    fac = alt_f
                    seat["ch3_faction"] = fac
                    break
        used_facs.add(fac)
        mapping[fac] = idx
    return mapping


def is_faction_human(faction_key):
    """Returns True if `faction_key` is controlled by a human player."""
    return faction_key in get_human_factions_map()


def trigger_pnp_chapter_3_outbreak(active_player, world_map, mechanics_mod):
    """Transitions all Pass-and-Play human seats into Chapter 3."""
    cur_idx = _PNP_SESSION.get("active_idx", 0)
    _save_active_player_to_seat(active_player, cur_idx)
    _PNP_SESSION["in_chapter_3"] = True

    for seat in _PNP_SESSION.get("seats", []):
        rank, _ = mechanics_mod.evaluate_chapter_3_state(seat)
        seat["ch3_rank"] = rank
        seat["ch3_start_rank"] = rank

    human_map = get_human_factions_map()
    _PNP_SESSION["ch3_turn_order"] = list(human_map.values())
    _PNP_SESSION["ch3_order_pos"] = 0

    first_seat_idx = _PNP_SESSION["ch3_turn_order"][0]
    _load_seat_into_active_player(active_player, first_seat_idx)
    ch3_war_engine.init_chapter_3_world_board(active_player, world_map)
    _sync_shared_keys_from_active(active_player)
    _PNP_SESSION["active_idx"] = first_seat_idx
    return active_player


def advance_ch3_human_turn(active_player):
    """Rotates to the next human seat in Chapter 3 if more remain today."""
    if not is_pnp_enabled(active_player):
        return False, None, None

    cur_idx = _PNP_SESSION.get("active_idx", 0)
    _save_active_player_to_seat(active_player, cur_idx)

    order = _PNP_SESSION.get("ch3_turn_order") or list(
        range(len(_PNP_SESSION.get("seats", [])))
    )
    pos = _PNP_SESSION.get("ch3_order_pos", 0) + 1

    if pos < len(order):
        _PNP_SESSION["ch3_order_pos"] = pos
        next_seat_idx = order[pos]
        _PNP_SESSION["active_idx"] = next_seat_idx
        _load_seat_into_active_player(active_player, next_seat_idx)
        ch3_board_renderer.centre_camera_on_player_forces(active_player)
        return (
            True,
            active_player.get("pnp_player_name", f"Player {next_seat_idx + 1}"),
            active_player.get("ch3_faction", "Union"),
        )

    _PNP_SESSION["ch3_order_pos"] = 0
    first_idx = order[0] if order else 0
    _PNP_SESSION["active_idx"] = first_idx
    _load_seat_into_active_player(active_player, first_idx)
    return False, None, None


# =========================================================================
# 5. NEW-GAME & PASS-AND-PLAY SETUP PAGE, HUD PILL & HANDOVER CURTAIN
# =========================================================================
def draw_pnp_turn_hud_pill(screen, player, small_font):
    """Draws the top-left Traveller Name, Cloak Colour & Remaining Slice Pill."""
    if not is_pnp_enabled(player) or _PNP_SESSION.get("in_chapter_3"):
        return

    p_name = player.get("pnp_player_name", "Noburu")
    c_rgb = tuple(player.get("pnp_colour_rgb", TATE_RED))
    used = player.get("pnp_slice_used", 0)
    limit = player.get(
        "pnp_slice_limit", _PNP_SESSION.get("slice_minutes", 500)
    )
    rem_mins = max(0, limit - used)
    rem_h = rem_mins // 100
    rem_m = rem_mins % 100

    pill_rect = pygame.Rect(14, 6, 236, 26)
    pygame.draw.rect(screen, c_rgb, pill_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_BRIGHT, pill_rect, 2, border_radius=6)

    txt = f"{p_name.upper()} | {rem_h}h {rem_m:02d}m Left"
    draw_fitted_text(
        screen, txt, pill_rect, DIAL_CREAM, bold=True, max_lines=1
    )


def draw_pnp_handover_curtain(screen, player, font, small_font, mouse_pos):
    """Renders the full-screen Heraldic Turn-Handover Privacy Curtain."""
    screen.fill((28, 22, 18))

    card = pygame.Rect(70, 50, 660, 500)
    pygame.draw.rect(screen, OAK_DARK, card, border_radius=12)
    pygame.draw.rect(screen, GOLD_ACCENT, card, 4, border_radius=12)
    inner = card.inflate(-16, -16)
    pygame.draw.rect(screen, DIAL_CREAM, inner, border_radius=9)

    p_name = player.get("pnp_player_name", "Player 2")
    in_ch3 = _PNP_SESSION.get("in_chapter_3", False)

    if in_ch3:
        fac = player.get("ch3_faction") or "Union"
        spec = ch3_war_engine.DTESSERA_FACTIONS.get(
            fac, ch3_war_engine.DTESSERA_FACTIONS["Union"]
        )
        banner_col = spec["color"]
    else:
        banner_col = tuple(player.get("pnp_colour_rgb", TATE_RED))
        trim_col = tuple(player.get("pnp_colour_trim", GOLD_BRIGHT))

    hdr_rect = pygame.Rect(inner.x + 20, inner.y + 18, inner.width - 40, 44)
    pygame.draw.rect(screen, banner_col, hdr_rect, border_radius=7)
    pygame.draw.rect(screen, GOLD_BRIGHT, hdr_rect, 2, border_radius=7)
    draw_fitted_text(
        screen,
        f"PASS THE MOUSE TO {p_name.upper()}!",
        hdr_rect,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    ped_r = pygame.Rect(340, 212, 120, 36)
    pygame.draw.ellipse(screen, OAK_MID, ped_r)
    pygame.draw.ellipse(screen, GOLD_BRIGHT, ped_r, 2)

    if in_ch3:
        ch3_board_renderer._draw_single_carved_meeple(
            screen, 400, 226, 2.5, fac
        )
        rk = player.get("ch3_rank", "General")
        clashes = len(player.get("ch3_pending_clashes", []))
        sub_txt = (
            f"Commander: {p_name} — {spec['title']} ({rk})\n"
            f"Equipped Dice: {player.get('equipped_dice', 'bone dice').title()}\n"
            f"Pinned Crossed-Swords Clashes on Board: {clashes}\n\n"
            "Cast your Dawn Command Dice, allocate your Wooden Player Board, "
            "and march your battalions across Dtessera Terra!"
        )
    else:
        _draw_traveller_cloak_meeple(
            screen, 400, 226, 2.5, banner_col, trim_col
        )
        slice_h = _PNP_SESSION.get("slice_minutes", 500) // 100
        c_name = player.get("pnp_colour_name", "Tate Crimson")
        route = player.get("chapter_2_route") or (
            f"Chapter I ({(player.get('current_job') or 'Unemployed Apprentice').title()})"
        )
        rivals_here = get_rivals_at_current_tile(player)
        rival_note = (
            f"\n*** ALERT: {rivals_here[0][1]} is standing in your exact "
            "location! ***"
            if rivals_here
            else ""
        )
        sub_txt = (
            f"Traveller: {p_name} ({c_name} Cloak)  |  Turn Slice: {slice_h} Decimal Hrs\n"
            f"Current Path: {route}  |  Purse: {player.get('silver', 0)} Silver\n"
            f"Equipped Dice: {player.get('equipped_dice', 'bone dice').title()}"
            f"{rival_note}"
        )

    draw_fitted_text(
        screen,
        sub_txt,
        pygame.Rect(inner.x + 36, 268, inner.width - 72, 145),
        CLOCK_BLACK,
        align="center",
        max_lines=6,
    )

    pygame.draw.rect(screen, EQUIPPED_GREEN, HANDOVER_BTN_RECT, border_radius=8)
    pygame.draw.rect(
        screen, GOLD_BRIGHT, HANDOVER_BTN_RECT, 2, border_radius=8
    )
    draw_fitted_text(
        screen,
        f"I Am Seated — Begin {p_name}'s Turn >>",
        HANDOVER_BTN_RECT,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )
    player["pnp_handover_btn_rect"] = HANDOVER_BTN_RECT
    return HANDOVER_BTN_RECT


def draw_pnp_lobby_modal(screen, player, font, small_font, mouse_pos):
    """
    Renders the Campaign & Pass-and-Play Setup Page:
    - When `start_stage == 'CH1'`: Players pick a Travelling Name (click
      to cycle OR type on keyboard!) and a Traveller Cloak Colour (their
      future Chapter 3 faction is undetermined!).
    - When `start_stage == 'CH3'` (Unlocked only after 1 Campaign Victory):
      Players pick their Chapter 3 Faction Banner.
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((18, 14, 11, 235))
    screen.blit(overlay, (0, 0))

    card = pygame.Rect(42, 18, 716, 564)
    pygame.draw.rect(screen, DIAL_CREAM, card, border_radius=10)
    pygame.draw.rect(screen, TATE_RED, card, 4, border_radius=10)
    pygame.draw.rect(
        screen, CLOCK_BLACK, card.inflate(-8, -8), 1, border_radius=8
    )

    cfg = _PNP_LOBBY_CFG
    ch3_unlocked = is_ch3_start_unlocked()
    if not ch3_unlocked and cfg["start_stage"] == "CH3":
        cfg["start_stage"] = "CH1"

    is_ch3_mode = cfg["start_stage"] == "CH3"
    hdr_title = (
        "CHAPTER 3 WAR TABLE SKIRMISH SETUP (PICK FACTION BANNERS)"
        if is_ch3_mode
        else "NEW ADVENTURE SETUP — PICK TRAVELLING NAME, CLOAK COLOUR & DICE"
    )
    draw_fitted_text(
        screen,
        hdr_title,
        pygame.Rect(62, 28, 676, 24),
        TATE_RED,
        bold=True,
        max_lines=1,
    )

    rects = _get_lobby_rects()
    num_p = cfg["num_players"]
    m_name = ch3_war_engine.REPUBLICAN_MONTHS[cfg["month_idx"] % 12]
    v_labels = {
        "100_PTS": "100 Pts (Standard)",
        "250_PTS": "250 Pts (Grand War)",
        "DOMINATION": "Total Domination (7 Keeps)",
    }
    v_str = v_labels.get(cfg["victory_mode"], "100 Pts")

    # 1. Row 1: Players Count, Turn Slice, and Starting Month
    p_lbl = (
        "Players: 1 (Solo)"
        if num_p == 1
        else f"Pass & Play: {num_p} Players"
    )
    slice_lbl = (
        "Turn Timer: Solo (None)"
        if num_p == 1
        else f"Turn Slice: {cfg['slice_minutes'] // 100} Decimal Hrs"
    )
    row1_specs = [
        ("cycle_count", p_lbl),
        ("cycle_slice", slice_lbl),
        ("cycle_month", f"Start Month: {m_name}"),
    ]
    for key, lbl in row1_specs:
        r_top = rects[key]
        is_hov = r_top.collidepoint(mouse_pos)
        pygame.draw.rect(
            screen,
            (86, 64, 48) if is_hov else OAK_MID,
            r_top,
            border_radius=6,
        )
        pygame.draw.rect(
            screen, GOLD_BRIGHT, r_top, 2 if is_hov else 1, border_radius=6
        )
        draw_fitted_text(
            screen, lbl, r_top, DIAL_CREAM, bold=True, max_lines=1
        )

    # 2. Row 2: War Victory Goal & Starting Stage (Ch.1 vs Ch.3 if unlocked)
    if ch3_unlocked:
        stage_lbl = (
            "Stage: Ch.3 War Table (Click for Ch.1)"
            if is_ch3_mode
            else "Stage: Ch.1 Murum (Click for Ch.3)"
        )
        stage_bg = TATE_RED if is_ch3_mode else (52, 74, 98)
    else:
        stage_lbl = "Ch.3 Start: LOCKED (Win 1 Game to Unlock)"
        stage_bg = LOCKED_GREY

    row2_specs = [
        ("cycle_victory", f"Victory Goal: {v_str}", (52, 74, 98)),
        ("cycle_stage", stage_lbl, stage_bg),
    ]
    for key, lbl, base_c in row2_specs:
        r_sec = rects[key]
        is_hov = r_sec.collidepoint(mouse_pos)
        pygame.draw.rect(screen, base_c, r_sec, border_radius=6)
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if is_hov else GOLD_ACCENT,
            r_sec,
            2 if is_hov else 1,
            border_radius=6,
        )
        draw_fitted_text(
            screen, lbl, r_sec, DIAL_CREAM, bold=True, max_lines=1
        )

    # 3. Per-Player Seat Rows (1 to 4 Seats)
    editing_idx = cfg.get("editing_seat_name")
    for idx in range(4):
        s_cfg = cfg["seats"][idx]
        ry = 142 + idx * 86
        row_r = pygame.Rect(64, ry, 672, 78)
        is_active_seat = idx < num_p

        bg_c = (234, 226, 210) if is_active_seat else (195, 190, 182)
        pygame.draw.rect(screen, bg_c, row_r, border_radius=7)
        pygame.draw.rect(screen, CLOCK_BLACK, row_r, 1, border_radius=7)

        c_name, c_rgb, c_trim = TRAVELLER_COLOURS[
            s_cfg["color_idx"] % len(TRAVELLER_COLOURS)
        ]
        fac = s_cfg["faction"]
        f_spec = ch3_war_engine.DTESSERA_FACTIONS[fac]

        # Left Travelling Name & Meeple Button
        name_btn = rects[f"seat_name_{idx}"]
        n_hov = name_btn.collidepoint(mouse_pos)
        is_editing = editing_idx == idx
        badge_bg = f_spec["color"] if is_ch3_mode else c_rgb
        pygame.draw.rect(
            screen,
            badge_bg if is_active_seat else LOCKED_GREY,
            name_btn,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if (n_hov or is_editing) else GOLD_ACCENT,
            name_btn,
            3 if is_editing else (2 if n_hov else 1),
            border_radius=6,
        )

        if is_ch3_mode:
            ch3_board_renderer._draw_single_carved_meeple(
                screen, 96, ry + 53, 1.08, fac
            )
        else:
            _draw_traveller_cloak_meeple(
                screen, 96, ry + 53, 1.08, c_rgb, c_trim
            )

        cursor_ch = "_" if is_editing else ""
        disp_name = (
            f"{s_cfg['name']}{cursor_ch}\n(Click/Type Name)"
            if is_active_seat
            else f"Seat {idx + 1}\n(Inactive)"
        )
        draw_fitted_text(
            screen,
            disp_name,
            pygame.Rect(114, ry + 14, 94, 48),
            DIAL_CREAM,
            bold=True,
            max_lines=2,
        )

        # Middle Button: Traveller Cloak Colour (Ch.1) OR Faction Banner (Ch.3)
        mid_btn = rects[f"seat_col_or_fac_{idx}"]
        m_hov = mid_btn.collidepoint(mouse_pos)
        if is_ch3_mode:
            mid_bg = f_spec["color"] if is_active_seat else LOCKED_GREY
            mid_txt = (
                f"Ch.3 Faction: {f_spec['title']}\n(Click to Cycle Faction)"
            )
        else:
            mid_bg = c_rgb if is_active_seat else LOCKED_GREY
            mid_txt = (
                f"Traveller Cloak: {c_name}\n"
                "(Future Faction Undetermined)"
            )

        pygame.draw.rect(screen, mid_bg, mid_btn, border_radius=6)
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if m_hov else CLOCK_BLACK,
            mid_btn,
            2 if m_hov else 1,
            border_radius=6,
        )
        draw_fitted_text(
            screen, mid_txt, mid_btn, DIAL_CREAM, bold=True, max_lines=2
        )

        # Right Button: 3D Dice Palette
        dice_btn = rects[f"seat_dice_{idx}"]
        d_hov = dice_btn.collidepoint(mouse_pos)
        pygame.draw.rect(
            screen,
            (52, 74, 98) if is_active_seat else LOCKED_GREY,
            dice_btn,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if d_hov else CLOCK_BLACK,
            dice_btn,
            2 if d_hov else 1,
            border_radius=6,
        )
        draw_fitted_text(
            screen,
            f"3D Dice: {s_cfg['dice'].title()}\n(Click to Cycle Dice)",
            dice_btn,
            DIAL_CREAM,
            bold=True,
            max_lines=2,
        )

    # 4. Bottom Launch Buttons
    ch1_lbl = (
        "Begin Chapter 1 Adventure >>"
        if not player.get("ch3_rank")
        else "Apply & Resume Campaign >>"
    )
    ch3_lbl = (
        "Launch Ch.3 War Table >>"
        if ch3_unlocked
        else "Ch.3 Locked (Win 1 Campaign)"
    )
    ch3_col = TATE_RED if ch3_unlocked else LOCKED_GREY

    for b_key, b_lbl, b_col in (
        ("start_pnp_campaign", ch1_lbl, EQUIPPED_GREEN),
        ("start_pnp_ch3", ch3_lbl, ch3_col),
        ("close_pnp_lobby", "< Back", (95, 78, 68)),
    ):
        b_r = rects[b_key]
        b_hov = b_r.collidepoint(mouse_pos)
        pygame.draw.rect(screen, b_col, b_r, border_radius=6)
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if (b_key != "start_pnp_ch3" or ch3_unlocked) else CLOCK_BLACK,
            b_r,
            3 if b_hov else 2,
            border_radius=6,
        )
        draw_fitted_text(
            screen, b_lbl, b_r, DIAL_CREAM, bold=True, max_lines=1
        )

    return rects


def handle_pnp_lobby_event(event, player, world_map, ui_renderer_mod):
    """
    Processes mouse clicks AND keyboard typing (for custom Travelling
    Names) inside the Setup Page.
    """
    cfg = _PNP_LOBBY_CFG
    ch3_unlocked = is_ch3_start_unlocked()

    # Support typing a custom Travelling Name when a seat badge is selected
    if event.type == pygame.KEYDOWN and cfg.get("editing_seat_name") is not None:
        s_idx = cfg["editing_seat_name"]
        cur_name = cfg["seats"][s_idx]["name"]
        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            if not cur_name.strip():
                cfg["seats"][s_idx]["name"] = TRAVELLER_NAMES[s_idx]
            cfg["editing_seat_name"] = None
            return True, None
        if event.key == pygame.K_BACKSPACE:
            cfg["seats"][s_idx]["name"] = cur_name[:-1]
            return True, None
        if event.unicode and event.unicode.isprintable() and len(cur_name) < 12:
            cfg["seats"][s_idx]["name"] = cur_name + event.unicode
            return True, None

    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False, None

    rects = _get_lobby_rects()
    pos = event.pos
    cfg["editing_seat_name"] = None

    if rects["cycle_count"].collidepoint(pos):
        cfg["num_players"] = (
            1 if cfg["num_players"] >= 4 else cfg["num_players"] + 1
        )
        return True, None

    if rects["cycle_slice"].collidepoint(pos):
        cur_s = cfg["slice_minutes"]
        nxt_i = (
            (SLICE_OPTIONS.index(cur_s) + 1) % len(SLICE_OPTIONS)
            if cur_s in SLICE_OPTIONS
            else 1
        )
        cfg["slice_minutes"] = SLICE_OPTIONS[nxt_i]
        return True, None

    if rects["cycle_month"].collidepoint(pos):
        cfg["month_idx"] = (cfg.get("month_idx", 1) + 1) % 12
        return True, None

    if rects["cycle_victory"].collidepoint(pos):
        cur_v = cfg.get("victory_mode", "100_PTS")
        nxt_v = (
            (VICTORY_MODES.index(cur_v) + 1) % len(VICTORY_MODES)
            if cur_v in VICTORY_MODES
            else 0
        )
        cfg["victory_mode"] = VICTORY_MODES[nxt_v]
        return True, None

    if rects["cycle_stage"].collidepoint(pos):
        if ch3_unlocked:
            cfg["start_stage"] = (
                "CH3" if cfg["start_stage"] == "CH1" else "CH1"
            )
        return True, None

    for idx in range(4):
        # Click Travelling Name badge -> Cycle preset names & enable keyboard typing!
        if rects[f"seat_name_{idx}"].collidepoint(pos):
            if idx >= cfg["num_players"]:
                cfg["num_players"] = idx + 1
            nxt_n = (cfg["seats"][idx].get("name_idx", idx) + 1) % len(
                TRAVELLER_NAMES
            )
            cfg["seats"][idx]["name_idx"] = nxt_n
            cfg["seats"][idx]["name"] = TRAVELLER_NAMES[nxt_n]
            cfg["editing_seat_name"] = idx
            return True, None

        # Click Middle Button -> Cycle Cloak Colour (Ch.1) OR Faction (Ch.3)
        if rects[f"seat_col_or_fac_{idx}"].collidepoint(pos):
            if idx >= cfg["num_players"]:
                cfg["num_players"] = idx + 1
            if cfg["start_stage"] == "CH3" and ch3_unlocked:
                cur_f = cfg["seats"][idx]["faction"]
                nxt_f = FACTION_KEYS[
                    (FACTION_KEYS.index(cur_f) + 1) % len(FACTION_KEYS)
                ]
                cfg["seats"][idx]["faction"] = nxt_f
            else:
                cfg["seats"][idx]["color_idx"] = (
                    cfg["seats"][idx].get("color_idx", idx) + 1
                ) % len(TRAVELLER_COLOURS)
            return True, None

        # Click Right Button -> Cycle 3D Dice Style
        if rects[f"seat_dice_{idx}"].collidepoint(pos):
            if idx >= cfg["num_players"]:
                cfg["num_players"] = idx + 1
            cur_d = cfg["seats"][idx]["dice"]
            nxt_d = DICE_STYLES[
                (DICE_STYLES.index(cur_d) + 1) % len(DICE_STYLES)
            ]
            cfg["seats"][idx]["dice"] = nxt_d
            return True, None

    # Launch Chapter 1 Campaign
    if rects["start_pnp_campaign"].collidepoint(pos):
        from_title = player.get("ch3_prev_modal_state") == "START_SCREEN"
        m_idx = cfg.get("month_idx", 1) % 12
        player["current_month_idx"] = m_idx
        player["current_month"] = ch3_war_engine.REPUBLICAN_MONTHS[m_idx]
        player["ch3_victory_mode"] = cfg.get("victory_mode", "100_PTS")
        weather_engine.update_weather_on_time_advance(player, 0, world_map=None)

        init_pnp_campaign(
            player,
            num_players=cfg["num_players"],
            slice_minutes=cfg["slice_minutes"],
            outbreak_mode=cfg["outbreak_mode"],
            custom_configs=cfg["seats"],
            start_in_ch3=False,
        )
        return True, ("CHAPTER_1_INTRO" if from_title else "MAIN")

    # Launch Chapter 3 War Table (Only if unlocked by 1+ completed campaign!)
    if rects["start_pnp_ch3"].collidepoint(pos):
        if not ch3_unlocked:
            return True, None

        m_idx = cfg.get("month_idx", 1) % 12
        player["current_month_idx"] = m_idx
        player["current_month"] = ch3_war_engine.REPUBLICAN_MONTHS[m_idx]
        player["ch3_victory_mode"] = cfg.get("victory_mode", "100_PTS")
        player["ch3_rank"] = player.get("ch3_rank") or "General"
        weather_engine.update_weather_on_time_advance(player, 0, world_map=None)

        init_pnp_campaign(
            player,
            num_players=cfg["num_players"],
            slice_minutes=cfg["slice_minutes"],
            outbreak_mode=cfg["outbreak_mode"],
            custom_configs=cfg["seats"],
            start_in_ch3=True,
        )
        _PNP_SESSION["in_chapter_3"] = True
        _PNP_SESSION["ch3_turn_order"] = list(range(cfg["num_players"]))
        _PNP_SESSION["ch3_order_pos"] = 0
        ch3_war_engine.init_chapter_3_world_board(player, world_map)
        ui_renderer_mod.init_ch3_morning_phase(player)
        _sync_shared_keys_from_active(player)
        return True, "CH3_MORNING_PHASE"

    if rects["close_pnp_lobby"].collidepoint(pos):
        prev = player.get("ch3_prev_modal_state", "START_SCREEN")
        return True, prev

    return False, None
