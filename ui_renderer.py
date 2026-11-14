"""
ui_renderer.py
--------------
Renders the unified Root-style Chapter 3 Tabletop UI:
- Wooden Player Board (y = 420..600) with Faction/Rank readout, Recessed
  Dice Sockets, Troop Detachment Splitter, Zero-Army Solo Commando Deck,
  and Brass Boot Token MP Gauge
- Heraldic AI Turn Banner over the Player Board (y = 420..600) showing
  symmetric AI dice rolls, supply status, and live speed controls
- Tabletop Preferences Modal with Starting Month (all 12 Republican
  months) and Victory Mode (100 Pts / 250 Pts / Total Domination)
- Character Status Mannequin, Inventory Satchel, and System Help Popups
"""

from collections import Counter
import json
import math
import os
import pygame

import ch3_board_renderer
import ch3_combat_engine
import ch3_war_engine
import companions_engine
import game_data as db
from map_data import world_map as DEFAULT_WORLD_MAP
from mechanics import (
    format_item_name,
    get_inventory_weight,
    get_max_carry_weight,
    init_ch3_morning_phase as _mechanics_init_morning,
)
from ui_components import draw_fitted_text

# --- SHARED PALETTE CONSTANTS ---
TATE_RED = (168, 50, 35)
DIAL_CREAM = (244, 239, 225)
DIAL_CREAM_HOVER = (220, 215, 200)
CLOCK_BLACK = (28, 28, 24)
GOLD_ACCENT = (195, 148, 48)
GOLD_BRIGHT = (250, 215, 85)
EQUIPPED_GREEN = (38, 125, 60)

OAK_BOARD_BG = (66, 48, 36)
OAK_PANEL_DARK = (46, 33, 25)
OAK_TRIM_GOLD = (188, 146, 58)
SOCKET_WELL_BG = (30, 22, 17)
FELT_GREEN = (32, 78, 52)
FELT_BORDER = (22, 54, 36)

PLAYER_BOARD_RECT = pygame.Rect(0, 420, 800, 180)

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


def init_ch3_morning_phase(player):
    """
    Initialises the Chapter 3 Morning Phase and sets the dice to wait in
    the Leather Cup until the player explicitly clicks 'Roll Dawn Dice'.
    """
    player = _mechanics_init_morning(player)
    player["ch3_dice_rolled_today"] = False
    player["ch3_selected_die_id"] = None
    player["ch3_pending_clashes"] = []
    player["ch3_ai_turn_queue"] = []
    player["ch3_petitioned_today"] = False
    player.setdefault("ch3_victory_mode", "100_PTS")
    player.setdefault("current_month_idx", 1)
    player.setdefault("ch3_show_tooltips", True)
    player.setdefault("ch3_show_ai_moves", True)
    player.setdefault("ch3_ai_pacing", "NORMAL")
    player.setdefault("ch3_confirm_phases", True)
    player.setdefault("ch3_click_to_slot", True)
    return player


# =========================================================================
# 1. STYLISED 3D TUMBLING DICE & WOODEN PLAYER BOARD HELPERS
# =========================================================================
def _draw_3d_die(
    screen, cx, cy, size, value, player, die_salt=0, highlight=False
):
    """
    Renders a 3D bevelled die using the player's equipped dice palette.
    Animates a tumbling bounce while `ch3_dice_anim_until` is active.
    """
    inv = player.get("inventory", [])
    active_style = player.get("equipped_dice", "bone dice").lower()
    if active_style not in DICE_PALETTES:
        active_style = "bone dice"
        for style in DICE_PALETTES:
            if style in inv:
                active_style = style
                break

    now = pygame.time.get_ticks()
    anim_until = player.get("ch3_dice_anim_until", 0)
    disp_val = value
    jitter_x, jitter_y = 0, 0

    if now < anim_until:
        phase = (now // 55) + (die_salt * 3)
        disp_val = (phase % 6) + 1
        jitter_x = int(math.sin(now * 0.04 + die_salt) * 3)
        jitter_y = -abs(int(math.cos(now * 0.05 + die_salt * 2) * 5))

    cx += jitter_x
    cy += jitter_y

    pal = DICE_PALETTES[active_style]
    half = size // 2
    rect = pygame.Rect(cx - half, cy - half, size, size)

    if highlight:
        pygame.draw.rect(
            screen, GOLD_BRIGHT, rect.inflate(6, 6), 2, border_radius=6
        )

    pygame.draw.rect(
        screen, pal["shadow"], rect.move(2, 3), border_radius=5
    )
    pygame.draw.rect(screen, pal["base"], rect, border_radius=5)
    border_col = GOLD_ACCENT if now < anim_until else CLOCK_BLACK
    pygame.draw.rect(screen, border_col, rect, 1, border_radius=5)

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


def _draw_boot_token(screen, cx, cy, fill_ratio, highlight_cost=False):
    """
    Draws a miniature brass Boot Token representing 10 March Points (MP).
    """
    rect = pygame.Rect(cx - 14, cy - 13, 28, 26)
    bg_col = (
        (195, 75, 45)
        if highlight_cost
        else ((175, 135, 45) if fill_ratio > 0 else (45, 38, 32))
    )
    pygame.draw.rect(screen, CLOCK_BLACK, rect.move(1, 2), border_radius=5)
    pygame.draw.rect(screen, bg_col, rect, border_radius=5)

    if 0.0 < fill_ratio < 1.0:
        part_h = int(rect.height * fill_ratio)
        part_r = pygame.Rect(
            rect.x, rect.bottom - part_h, rect.width, part_h
        )
        pygame.draw.rect(screen, GOLD_BRIGHT, part_r, border_radius=4)

    bd_col = (
        GOLD_BRIGHT
        if (fill_ratio >= 1.0 or highlight_cost)
        else (95, 82, 68)
    )
    pygame.draw.rect(screen, bd_col, rect, 1, border_radius=5)

    ink = CLOCK_BLACK if fill_ratio > 0 else (90, 80, 70)
    boot_pts = [
        (cx - 5, cy - 7),
        (cx + 1, cy - 7),
        (cx + 1, cy + 1),
        (cx + 7, cy + 3),
        (cx + 7, cy + 7),
        (cx - 6, cy + 7),
    ]
    pygame.draw.polygon(screen, ink, boot_pts)


def _draw_wooden_player_board_frame(screen, player, small_font):
    """
    Draws the bottom Root-style Wooden Player Board (y = 420..600) with
    Zone A (Faction Identity, Month, & Victory Goal), Zone B (Centre
    Sockets / Command Deck), and Zone C (Felt Dice Tray).
    """
    my_fac = player.get("ch3_faction", "Union")
    my_rank = player.get("ch3_rank", "Private")
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        my_fac, ch3_war_engine.DTESSERA_FACTIONS["Union"]
    )
    fac_col = spec["color"]

    pygame.draw.rect(screen, OAK_BOARD_BG, PLAYER_BOARD_RECT)
    for wy in range(426, 598, 12):
        pygame.draw.line(screen, (58, 42, 31), (0, wy), (800, wy), 1)
    pygame.draw.line(screen, OAK_TRIM_GOLD, (0, 420), (800, 420), 3)
    pygame.draw.rect(
        screen, OAK_TRIM_GOLD, (4, 424, 792, 172), 1, border_radius=6
    )

    # --- ZONE A: FACTION IDENTITY & LIVE PREVIEW (x = 10..196) ---
    zone_a = pygame.Rect(10, 428, 186, 164)
    pygame.draw.rect(screen, OAK_PANEL_DARK, zone_a, border_radius=6)
    pygame.draw.rect(screen, fac_col, (10, 428, 186, 26), border_radius=6)
    pygame.draw.rect(screen, OAK_TRIM_GOLD, zone_a, 1, border_radius=6)

    hdr_txt = f"{my_fac.upper()} — {my_rank.upper()}"
    draw_fitted_text(
        screen,
        hdr_txt,
        pygame.Rect(14, 430, 178, 22),
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    f_data = player.get("ch3_factions", {}).get(my_fac, {})
    leg_pts = f_data.get("legacy_pts", 15)
    tot_pts = f_data.get("total_points", leg_pts)
    sym_val = f_data.get("sympathy", 10)
    sym_name = spec.get("sympathy_type", "Order")
    goal_val, v_mode, _ = ch3_war_engine.get_victory_goal_info(player)
    keeps_held = ch3_war_engine.count_faction_strongholds(player, my_fac)

    if v_mode == "DOMINATION":
        goal_line = f"Keeps: {keeps_held}/7 (Pts: {tot_pts})"
    else:
        goal_line = f"Hegemony: {tot_pts}/{goal_val} (Keeps: {keeps_held})"

    m_idx = player.get("current_month_idx", 1) % 12
    month_name = ch3_war_engine.REPUBLICAN_MONTHS[m_idx]

    dice = player.get("ch3_morning_dice", [])
    slots = player.get("ch3_morning_slots", {})
    unslotted = sum(1 for d in dice if d.get("slotted_in") is None)
    muster_objs = slots.get("muster_troops", {}).get("dice_objs", [])
    muster_sum = sum(d["value"] for d in muster_objs)
    owned_cnt = sum(
        1
        for owner in player.get("territories", {}).values()
        if owner == my_fac
    )
    muster_yield = (
        max(1, (muster_sum // 2) + owned_cnt) if muster_objs else 0
    )
    preview_mp = (
        max(20, unslotted * 10)
        if dice
        else player.get("movement_points", 0)
    )

    info_lines = (
        f"{goal_line}\n"
        f"{sym_name}: {sym_val} | Purse: {player.get('silver', 0)}s\n"
        f"Month: {month_name[:9]} | Lands: {owned_cnt}\n"
        f"Muster Preview: +{muster_yield} Bns\n"
        f"March Pool: {preview_mp} MP"
    )
    draw_fitted_text(
        screen,
        info_lines,
        pygame.Rect(16, 458, 174, 128),
        DIAL_CREAM,
        align="left",
        max_lines=5,
    )

    # --- ZONE B: CENTRE COMMAND MAT CONTAINER (x = 202..536) ---
    zone_b = pygame.Rect(202, 428, 334, 164)
    pygame.draw.rect(screen, OAK_PANEL_DARK, zone_b, border_radius=6)
    pygame.draw.rect(screen, OAK_TRIM_GOLD, zone_b, 1, border_radius=6)

    # --- ZONE C: FELT DICE TRAY CONTAINER (x = 542..790) ---
    tray_rect = pygame.Rect(542, 428, 248, 114)
    pygame.draw.rect(screen, FELT_GREEN, tray_rect, border_radius=6)
    pygame.draw.rect(
        screen, FELT_BORDER, tray_rect.inflate(-4, -4), 2, border_radius=5
    )
    pygame.draw.rect(screen, OAK_TRIM_GOLD, tray_rect, 2, border_radius=6)


def _draw_heraldic_ai_turn_banner(screen, player, small_font):
    """
    Renders the full-width Heraldic AI Turn Banner over the bottom Player
    Board (y = 420..600) while rival factions execute their symmetric
    turns on the unobstructed 3D tabletop map above.
    """
    ai_queue = player.get("ch3_ai_turn_queue", [])
    if not ai_queue:
        return

    ev = ai_queue[0]
    fac = ev.get("faction", "Laydere")
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        fac, ch3_war_engine.DTESSERA_FACTIONS["Laydere"]
    )
    fac_col = spec["color"]
    crest_col = spec["crest"]

    pygame.draw.rect(screen, OAK_BOARD_BG, PLAYER_BOARD_RECT)
    pygame.draw.line(screen, GOLD_BRIGHT, (0, 420), (800, 420), 3)

    # 1. Left Heraldic Crest & Carved Meeple Showcase (x = 12..188)
    left_box = pygame.Rect(12, 428, 176, 162)
    pygame.draw.rect(screen, fac_col, left_box, border_radius=7)
    pygame.draw.rect(screen, GOLD_BRIGHT, left_box, 2, border_radius=7)

    ch3_board_renderer._draw_faction_symbol(
        screen, fac, left_box.left + 26, left_box.top + 22, crest_col
    )
    draw_fitted_text(
        screen,
        fac.upper(),
        pygame.Rect(left_box.left + 46, left_box.top + 10, 122, 24),
        DIAL_CREAM,
        bold=True,
        align="left",
        max_lines=1,
    )

    ped_r = pygame.Rect(left_box.centerx - 36, left_box.top + 104, 72, 24)
    pygame.draw.ellipse(screen, (38, 32, 28), ped_r)
    pygame.draw.ellipse(screen, GOLD_BRIGHT, ped_r, 1)
    ch3_board_renderer._draw_single_carved_meeple(
        screen, left_box.centerx, left_box.top + 114, 1.55, fac
    )

    rem_cnt = len(ai_queue)
    draw_fitted_text(
        screen,
        f"Rival Turn ({7 - rem_cnt} of 6)",
        pygame.Rect(left_box.x + 8, left_box.bottom - 26, 160, 20),
        crest_col,
        bold=True,
        max_lines=1,
    )

    # 2. Centre Symmetric Dice & March Chronicle (x = 198..574)
    mid_box = pygame.Rect(198, 428, 376, 162)
    pygame.draw.rect(screen, DIAL_CREAM, mid_box, border_radius=7)
    pygame.draw.rect(screen, fac_col, mid_box, 3, border_radius=7)

    hdr_bar = pygame.Rect(204, 434, 364, 28)
    pygame.draw.rect(screen, fac_col, hdr_bar, border_radius=4)
    draw_fitted_text(
        screen,
        ev.get("banner_title", f"{fac.upper()}'S TURN"),
        hdr_bar,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    narrative_body = (
        f"• DAWN DICE: {ev.get('muster_text', '')}\n\n"
        f"• AFTERNOON MARCH: {ev.get('action_text', '')}"
    )
    draw_fitted_text(
        screen,
        narrative_body,
        pygame.Rect(212, 468, 348, 114),
        CLOCK_BLACK,
        bold=False,
        align="left",
        max_lines=5,
    )

    # 3. Right Pacing & Step Controls (x = 584..788)
    next_btn = pygame.Rect(584, 428, 204, 52)
    speed_btn = pygame.Rect(584, 488, 204, 46)
    skip_btn = pygame.Rect(584, 542, 204, 48)

    pygame.draw.rect(screen, EQUIPPED_GREEN, next_btn, border_radius=6)
    pygame.draw.rect(screen, GOLD_BRIGHT, next_btn, 2, border_radius=6)
    draw_fitted_text(
        screen,
        "Next Faction Turn >>",
        next_btn,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    cur_speed = player.get("ch3_ai_pacing", "NORMAL")
    pygame.draw.rect(screen, (55, 88, 135), speed_btn, border_radius=6)
    pygame.draw.rect(screen, OAK_TRIM_GOLD, speed_btn, 1, border_radius=6)
    draw_fitted_text(
        screen,
        f"Speed: {cur_speed} (Cycle)",
        speed_btn,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    pygame.draw.rect(screen, TATE_RED, skip_btn, border_radius=6)
    pygame.draw.rect(screen, OAK_TRIM_GOLD, skip_btn, 1, border_radius=6)
    draw_fitted_text(
        screen,
        "Skip All AI Turns >>",
        skip_btn,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    player["ch3_ai_next_rect"] = next_btn
    player["ch3_ai_speed_rect"] = speed_btn
    player["ch3_ai_skip_rect"] = skip_btn


def _draw_tabletop_hover_tooltip(screen, player, mouse_pos):
    """
    Draws a clean Parchment Hover Tooltip Card right above the Player Board
    (y = 352..416) whenever the cursor hovers over a socket, button, or
    map clearing.
    """
    if not player.get("ch3_show_tooltips", True):
        return

    tip_title = None
    tip_body = None

    for h_rect, h_title, h_body in player.get("ch3_hover_zones", []):
        if h_rect and h_rect.collidepoint(mouse_pos):
            tip_title = h_title
            tip_body = h_body
            break

    if not tip_title and player.get("ch3_hovered_details"):
        loc, owner, army, has_bar = player["ch3_hovered_details"]
        loc_title = loc.name if loc.name != "x" else f"{loc.region} Sector"
        tip_title = f"{loc_title} ({loc.region})"
        owner_str = owner if owner else "Unclaimed Neutral Ground"
        army_str = (
            f"{army['count']} {army['faction']} Battalions"
            if army
            else "No garrison"
        )
        bar_str = " | [BARRICADED +2 Pts]" if has_bar else ""
        cost_mp = player.get("ch3_hovered_move_cost")
        cost_str = f" | March Cost: {cost_mp} MP" if cost_mp else ""
        tip_body = (
            f"Controlled by: {owner_str} | Forces: "
            f"{army_str}{bar_str}{cost_str}"
        )

    if not tip_title:
        return

    card_rect = pygame.Rect(14, 354, 712, 60)
    pygame.draw.rect(screen, DIAL_CREAM, card_rect, border_radius=6)
    pygame.draw.rect(screen, TATE_RED, card_rect, 2, border_radius=6)
    pygame.draw.rect(
        screen, CLOCK_BLACK, card_rect.inflate(-4, -4), 1, border_radius=5
    )

    draw_fitted_text(
        screen,
        tip_title,
        pygame.Rect(24, 358, 692, 18),
        TATE_RED,
        bold=True,
        align="left",
        max_lines=1,
    )
    draw_fitted_text(
        screen,
        tip_body,
        pygame.Rect(24, 376, 692, 34),
        CLOCK_BLACK,
        align="left",
        max_lines=2,
    )


# =========================================================================
# 2. UNIFIED MORNING & AFTERNOON TABLETOP RENDERERS
# =========================================================================
def draw_ch3_morning_ui(
    screen, player, font, small_font, world_map=None, mouse_pos=None
):
    """
    Renders the Unified Chapter 3 Morning Tabletop:
    - Top Ribbon (y = 0..44)
    - 3D Tilted Map Board & Camera Sliders (y = 44..420)
    - Wooden Player Board with Recessed Reversible Dice Sockets & Felt Tray
    """
    w_map = world_map if world_map is not None else DEFAULT_WORLD_MAP
    m_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
    player["ch3_hover_zones"] = []

    ch3_board_renderer.draw_3d_tabletop_board(
        screen,
        player,
        w_map,
        small_font,
        m_pos,
        selected_army_pos=None,
        active_phase="MORNING",
    )
    ch3_board_renderer.draw_top_tabletop_ribbon(
        screen, player, small_font, active_phase="MORNING"
    )

    _draw_wooden_player_board_frame(screen, player, small_font)

    slots = player.get("ch3_morning_slots", {})
    dice = player.get("ch3_morning_dice", [])
    rolled = player.get("ch3_dice_rolled_today", False)
    selected_die_id = player.get("ch3_selected_die_id")

    slot_items = list(slots.items())
    col_w = 158
    for idx, (slot_key, slot_data) in enumerate(slot_items[:2]):
        sx = 210 + idx * 162
        sy = 434
        group_rect = pygame.Rect(sx, sy, col_w, 108)
        slot_data["rect"] = group_rect
        slot_data["dice_rects"] = []

        pygame.draw.rect(
            screen, (38, 27, 20), group_rect, border_radius=6
        )
        pygame.draw.rect(
            screen, OAK_TRIM_GOLD, group_rect, 1, border_radius=6
        )

        raw_name = slot_data.get("name", slot_key)
        short_title = raw_name.split("(")[0].strip()
        draw_fitted_text(
            screen,
            short_title.upper(),
            pygame.Rect(sx + 6, sy + 4, col_w - 12, 18),
            GOLD_BRIGHT,
            bold=True,
            max_lines=1,
        )

        req = slot_data.get("req")
        if req == [5, 6]:
            req_tag = "NEEDS 5 OR 6"
            tip_desc = (
                "Drop a 5 or 6 die here to secure your supply lines. "
                "Click a slotted die at any time to take it back!"
            )
        elif req == [6]:
            req_tag = "NEEDS A 6"
            tip_desc = (
                "Drop a 6 die here to scrounge field rations (+1 Meat "
                "Ration). Click a slotted die to return it to the tray."
            )
        elif req == "pair":
            req_tag = "MATCHED PAIR"
            tip_desc = (
                "Place two dice of the same number here to erect "
                "barricades. Click any slotted die to pop it back out!"
            )
        else:
            req_tag = "ANY DICE"
            tip_desc = (
                "Place any command dice here to muster new battalions "
                "at your capital. Click a slotted die to unslot it!"
            )

        draw_fitted_text(
            screen,
            req_tag,
            pygame.Rect(sx + 6, sy + 21, col_w - 12, 14),
            (185, 175, 155),
            max_lines=1,
        )

        slotted_objs = slot_data.get("dice_objs", [])
        for w_idx in range(3):
            wx = sx + 8 + w_idx * 48
            wy = sy + 42
            well_rect = pygame.Rect(wx, wy, 44, 44)
            pygame.draw.rect(
                screen, SOCKET_WELL_BG, well_rect, border_radius=5
            )
            pygame.draw.rect(
                screen, (95, 75, 55), well_rect, 1, border_radius=5
            )

            if w_idx < len(slotted_objs):
                d_obj = slotted_objs[w_idx]
                _draw_3d_die(
                    screen,
                    well_rect.centerx,
                    well_rect.centery,
                    38,
                    d_obj["value"],
                    player,
                    die_salt=d_obj["id"],
                )
                slot_data["dice_rects"].append((d_obj, well_rect))
            else:
                ghost = (
                    "5/6"
                    if req == [5, 6]
                    else (
                        "="
                        if req == "pair"
                        else ("6" if req == [6] else "+")
                    )
                )
                g_surf = small_font.render(ghost, True, (75, 62, 50))
                screen.blit(g_surf, g_surf.get_rect(center=well_rect.center))

        player["ch3_hover_zones"].append((group_rect, short_title, tip_desc))

    rank = player.get("ch3_rank", "Private")
    action_rect = pygame.Rect(210, 548, 158, 38)
    pygame.draw.rect(screen, TATE_RED, action_rect, border_radius=5)
    pygame.draw.rect(screen, OAK_TRIM_GOLD, action_rect, 1, border_radius=5)

    if rank == "General":
        act_short = "Draft Conscripts"
        act_tip = "Re-roll all Dawn Dice at the cost of -10% Global Morale."
    elif rank == "Captain":
        act_short = "Field Promotion"
        act_tip = "Once per dawn, add a bonus '6' Command Die to your tray."
    else:
        act_short = "Subvert Wagon"
        act_tip = "Pocket +5 Silver from the quartermaster's wagon (-1 Rep)."

    draw_fitted_text(
        screen, act_short, action_rect, DIAL_CREAM, bold=True, max_lines=1
    )
    player["ch3_exclusive_action_rect"] = action_rect
    player["ch3_hover_zones"].append((action_rect, act_short, act_tip))

    tools = ch3_war_engine.get_available_ch2_war_tools(player)
    player["ch3_tool_rects"] = {}
    short_tool_names = {
        "ch2_tool_press": (
            "Broadsheets",
            "Print strike-sheets (+4 Sympathy, +5% Confidence).",
        ),
        "ch2_tool_cipher": (
            "Decode Cipher",
            "Intercept enemy orders & gain +1 Tactical Token.",
        ),
        "ch2_tool_ordnance": (
            "Issue Steel",
            "Add a bonus '6' Command Die from your forge/allies.",
        ),
    }
    for idx, (t_key, t_full, t_col) in enumerate(tools[:2]):
        tx = 372 + idx * 80
        t_rect = pygame.Rect(tx, 548, 76, 38)
        pygame.draw.rect(screen, t_col, t_rect, border_radius=5)
        pygame.draw.rect(screen, OAK_TRIM_GOLD, t_rect, 1, border_radius=5)
        s_lbl, s_tip = short_tool_names.get(t_key, ("Use Tool", t_full))
        draw_fitted_text(
            screen, s_lbl, t_rect, DIAL_CREAM, bold=True, max_lines=2
        )
        player["ch3_tool_rects"][t_key] = t_rect
        player["ch3_hover_zones"].append((t_rect, s_lbl, s_tip))

    commit_rect = pygame.Rect(542, 548, 248, 40)
    player["ch3_commit_rect"] = commit_rect

    if not rolled:
        cup_rect = pygame.Rect(636, 446, 60, 68)
        pygame.draw.rect(screen, (92, 54, 32), cup_rect, border_radius=8)
        pygame.draw.rect(screen, OAK_TRIM_GOLD, cup_rect, 2, border_radius=8)
        draw_fitted_text(
            screen,
            f"{len(dice)}d6 CUP",
            cup_rect,
            DIAL_CREAM,
            bold=True,
            max_lines=2,
        )
        draw_fitted_text(
            screen,
            "Click below to cast your Dawn Command Dice!",
            pygame.Rect(548, 516, 236, 22),
            DIAL_CREAM,
            max_lines=1,
        )

        pygame.draw.rect(screen, TATE_RED, commit_rect, border_radius=6)
        pygame.draw.rect(
            screen, GOLD_BRIGHT, commit_rect, 2, border_radius=6
        )
        draw_fitted_text(
            screen,
            f"Roll Dawn Dice ({len(dice)}d6) >>",
            commit_rect,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )
        player["ch3_hover_zones"].append((
            commit_rect,
            "Roll Dawn Command Dice",
            "Cast your daily dice pool into the velvet tray. Nothing "
            "happens until you roll!",
        ))
    else:
        unslotted_dice = [d for d in dice if d["slotted_in"] is None]
        for idx, die_obj in enumerate(unslotted_dice[:12]):
            if not die_obj.get("is_dragging"):
                col = idx % 6
                row = idx // 6
                dx = 548 + col * 39
                dy = 438 + row * 48
                die_obj["rect"] = pygame.Rect(dx, dy, 36, 36)

        for idx, die_obj in enumerate(unslotted_dice[:12]):
            if die_obj.get("is_dragging"):
                continue
            d_rect = die_obj.get("rect")
            if not d_rect:
                continue
            is_sel = die_obj["id"] == selected_die_id
            _draw_3d_die(
                screen,
                d_rect.centerx,
                d_rect.centery,
                34,
                die_obj["value"],
                player,
                die_salt=idx + 1,
                highlight=is_sel,
            )

        for idx, die_obj in enumerate(dice):
            if die_obj.get("is_dragging") and die_obj.get("rect"):
                d_rect = die_obj["rect"]
                _draw_3d_die(
                    screen,
                    d_rect.centerx,
                    d_rect.centery,
                    42,
                    die_obj["value"],
                    player,
                    die_salt=idx + 10,
                    highlight=True,
                )

        pygame.draw.rect(screen, EQUIPPED_GREEN, commit_rect, border_radius=6)
        pygame.draw.rect(
            screen, GOLD_BRIGHT, commit_rect, 2, border_radius=6
        )
        draw_fitted_text(
            screen,
            "Commit & Start March >>",
            commit_rect,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )
        player["ch3_hover_zones"].append((
            commit_rect,
            "Commit Morning Orders",
            "Lock in your slotted dice and convert every unslotted die "
            "in the tray into 10 Afternoon March Points (10 MP).",
        ))

    _draw_tabletop_hover_tooltip(screen, player, m_pos)


def draw_ch3_afternoon_ui(
    screen,
    player,
    world_map,
    font,
    small_font,
    cam_x=0,
    cam_y=0,
    zoom=44,
    mouse_pos=None,
    selected_army_pos=None,
):
    """
    Renders the Unified Chapter 3 Afternoon Tabletop:
    - Top Ribbon (y = 0..44)
    - 3D Tilted Map Board & Camera Sliders (y = 44..420)
    - Either the Heraldic AI Turn Banner (when `ch3_ai_turn_queue` is
      active) OR the Wooden Player Board with Rank/Commando Deck,
      Troop Detachment Splitter, and Brass Boot Token MP Gauge.
    """
    w_map = world_map if world_map is not None else DEFAULT_WORLD_MAP
    m_pos = mouse_pos if mouse_pos is not None else pygame.mouse.get_pos()
    player["ch3_hover_zones"] = []
    player["ch3_splitter_rects"] = {}
    player["ch3_ai_next_rect"] = None
    player["ch3_ai_speed_rect"] = None
    player["ch3_ai_skip_rect"] = None

    ch3_war_engine.prune_empty_armies(player)

    ch3_board_renderer.draw_3d_tabletop_board(
        screen,
        player,
        w_map,
        small_font,
        m_pos,
        selected_army_pos=selected_army_pos,
        active_phase="AFTERNOON",
    )
    ch3_board_renderer.draw_top_tabletop_ribbon(
        screen, player, small_font, active_phase="AFTERNOON"
    )

    if player.get("ch3_ai_turn_queue") and player.get(
        "ch3_show_ai_moves", True
    ):
        _draw_heraldic_ai_turn_banner(screen, player, small_font)
        return

    _draw_wooden_player_board_frame(screen, player, small_font)

    # --- ZONE B TOP: RANK OR ZERO-ARMY COMMANDO DECK (y = 432..492) ---
    my_rank = player.get("ch3_rank", "Private")
    has_armies = ch3_war_engine.player_has_active_armies(player)
    selected_rival = player.get("ch3_selected_rival") or "Click Top Symbol"
    player["ch3_rank_action_rects"] = {}

    if not has_armies and my_rank in ("Captain", "Private"):
        deck_hdr = "ZERO BATTALIONS — PETITION OR SOLO COMMANDO OPS:"
        btn_specs = [
            (
                "petition_general",
                "Petition Troops",
                (45, 95, 155),
                "Dispatch a rider to High Command (2d6 + Standing/Conf "
                "vs 9+) requesting a 3-Bn Relief Column at your capital!",
            ),
            (
                "solo_sabotage",
                "Night Sabotage",
                (112, 48, 142),
                "Cost 8 MP: Infiltrate the nearest enemy garrison on "
                "foot to torch their powder wagons (-50% Enemy Bns, +20s, "
                "and High Command sends +2 Bns)!",
            ),
            (
                "solo_duel",
                "Duel Captain!",
                (165, 38, 38),
                "Cost 10 MP: Challenge the rival garrison commander to "
                "single combat! Winning captures the clearing (+3 Bns) "
                "and awards an immediate Battlefield Promotion!",
            ),
        ]
    elif my_rank == "General":
        deck_hdr = f"GENERAL COMMAND DECK (Target: {selected_rival})"
        btn_specs = [
            (
                "public_alliance",
                "Known Treaty",
                (45, 95, 155),
                "Sign an open treaty with the selected rival faction "
                "(+2 Political Standing).",
            ),
            (
                "secret_pact",
                "Secret Pact",
                (95, 52, 135),
                "Seal a covert non-aggression pact with the selected "
                "faction.",
            ),
            (
                "betray_alliance",
                "Betray Ally",
                (155, 35, 35),
                "Launch a surprise ambush against your ally (+6 Agenda "
                "Pts, -10 Standing).",
            ),
        ]
    elif my_rank == "Captain":
        deck_hdr = f"CAPTAIN COMMAND DECK (Target: {selected_rival})"
        conf = player.get("ch3_confidence", 65)
        can_turncoat = conf <= 35 or player.get("ch3_standing", 10) <= 0
        btn_specs = [
            (
                "petition_general",
                "Request Troops",
                (45, 95, 155),
                "Petition High Command (2d6 + Standing/Confidence vs 9+) "
                "to send +3 reinforcement Battalions to your capital.",
            ),
        ]
        if can_turncoat:
            btn_specs.append((
                "stage_coup",
                "Incite Coup!",
                (165, 35, 35),
                "Depose your failing General and seize Supreme Command!",
            ))
            btn_specs.append((
                "defect_faction",
                "Defect Faction",
                (112, 48, 142),
                "Hand your garrison over to the selected rival faction!",
            ))
        else:
            btn_specs.append((
                "solo_sabotage",
                "Solo Sabotage",
                (95, 52, 135),
                "Cost 8 MP: Lead a commando raid on an enemy camp "
                "(-50% Enemy Bns, +20s, +2 Bns reinforced)!",
            ))
            btn_specs.append((
                "subvert_confidence",
                "Sow Discontent",
                (115, 85, 45),
                "Lower Unit Confidence by -20% (unlocks Coup/Defection "
                "at 35% or below).",
            ))
    else:
        deck_hdr = "PRIVATE COMMAND & SOLO OPERATIONS DECK:"
        btn_specs = [
            (
                "enter_field_mode",
                "RPG Field Mode",
                (45, 115, 68),
                "Step onto the ground in 1st-person RPG mode to complete "
                "your Captain's directive (+2 Tactical Tokens).",
            ),
            (
                "solo_sabotage",
                "Night Sabotage",
                (95, 52, 135),
                "Cost 8 MP: Torch enemy supply wagons (-50% Enemy Bns, "
                "+20 Silver, and +2 Bns reinforced)!",
            ),
            (
                "solo_duel",
                "Duel Officer!",
                (145, 42, 42),
                "Cost 10 MP: Defeat an enemy Captain in single combat to "
                "capture their clearing and win promotion to Captain!",
            ),
        ]

    draw_fitted_text(
        screen,
        deck_hdr,
        pygame.Rect(210, 431, 318, 18),
        GOLD_BRIGHT,
        bold=True,
        align="left",
        max_lines=1,
    )

    for idx, (act_key, act_lbl, b_col, act_tip) in enumerate(btn_specs):
        bx = 210 + idx * 106
        b_rect = pygame.Rect(bx, 452, 100, 38)
        pygame.draw.rect(screen, b_col, b_rect, border_radius=5)
        pygame.draw.rect(screen, OAK_TRIM_GOLD, b_rect, 1, border_radius=5)
        draw_fitted_text(
            screen, act_lbl, b_rect, DIAL_CREAM, bold=True, max_lines=2
        )
        player["ch3_rank_action_rects"][act_key] = b_rect
        player["ch3_hover_zones"].append((b_rect, act_lbl, act_tip))

    # --- ZONE B BOTTOM: TROOP DETACHMENT SPLITTER OR SOLO MILITIA ---
    split_box = pygame.Rect(210, 496, 318, 90)
    pygame.draw.rect(screen, (34, 25, 19), split_box, border_radius=6)
    pygame.draw.rect(screen, OAK_TRIM_GOLD, split_box, 1, border_radius=6)

    armies = player.get("ch3_armies", {})
    if selected_army_pos and selected_army_pos in armies:
        total_bns = max(1, armies[selected_army_pos].get("count", 1))
        split_cnt = max(
            1, min(total_bns, player.get("ch3_split_count", total_bns))
        )
        player["ch3_split_count"] = split_cnt
        clr_name = ch3_combat_engine.resolve_clearing_name(
            selected_army_pos, w_map
        )

        draw_fitted_text(
            screen,
            f"DETACHMENT FROM {clr_name.upper()}:",
            pygame.Rect(218, 500, 302, 18),
            GOLD_BRIGHT,
            bold=True,
            align="left",
            max_lines=1,
        )
        draw_fitted_text(
            screen,
            f"Marching: {split_cnt} / {total_bns} Battalions "
            f"(+{split_cnt} MP Headcount)",
            pygame.Rect(218, 519, 302, 18),
            DIAL_CREAM,
            align="left",
            max_lines=1,
        )

        sp_buttons = [
            ("minus", "-1", 218, 44),
            ("plus", "+1", 268, 44),
            ("one", "1 Bn", 318, 60),
            ("half", "Half", 384, 64),
            ("all", "All", 454, 66),
        ]
        for s_key, s_lbl, sx_b, sw_b in sp_buttons:
            s_rect = pygame.Rect(sx_b, 542, sw_b, 36)
            pygame.draw.rect(screen, (78, 58, 44), s_rect, border_radius=5)
            pygame.draw.rect(
                screen, GOLD_BRIGHT, s_rect, 1, border_radius=5
            )
            draw_fitted_text(
                screen, s_lbl, s_rect, DIAL_CREAM, bold=True, max_lines=1
            )
            player["ch3_splitter_rects"][s_key] = s_rect

        player["ch3_hover_zones"].append((
            split_box,
            "Troop Detachment Splitter",
            "Choose how many battalions to march out of this clearing. "
            "Smaller detachments cost fewer March Points (Base + 1 MP/Bn)!",
        ))
    elif not has_armies:
        draw_fitted_text(
            screen,
            "NO BATTALIONS ON MAP: You have only yourself! Petition the "
            "General above, or click 'Raise Partisans' below:",
            pygame.Rect(218, 500, 302, 38),
            GOLD_BRIGHT,
            align="left",
            max_lines=2,
        )
        mil_btn = pygame.Rect(218, 542, 302, 36)
        pygame.draw.rect(screen, EQUIPPED_GREEN, mil_btn, border_radius=5)
        pygame.draw.rect(screen, GOLD_BRIGHT, mil_btn, 1, border_radius=5)
        draw_fitted_text(
            screen,
            "Solo Mission: Raise Partisan Militia (8 MP) >>",
            mil_btn,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )
        player["ch3_rank_action_rects"]["solo_militia"] = mil_btn
        player["ch3_hover_zones"].append((
            mil_btn,
            "Raise Partisan Militia (8 MP)",
            "Use Charisma, Influence, or your Portable Printing Press to "
            "rally 3 Volunteer Battalions directly at your capital!",
        ))
    else:
        clashes_cnt = len(player.get("ch3_pending_clashes", []))
        if clashes_cnt > 0:
            msg_b = (
                f"PINNED BATTLES: {clashes_cnt} Crossed-Swords ('X') "
                "clearing(s) ready for Dusk!\n"
                "Click another gold-ringed army to keep marching, or "
                "click 'Finish March' on the right."
            )
        else:
            order_desc = player.get("ch3_daily_order", {}).get(
                "description",
                "Click any of your glowing gold-ringed Meeples on the "
                "3D board to select and split forces.",
            )
            msg_b = f"FIELD DIRECTIVE:\n{order_desc}"
        draw_fitted_text(
            screen,
            msg_b,
            split_box.inflate(-14, -8),
            DIAL_CREAM,
            align="left",
            max_lines=4,
        )

    # --- ZONE C: BRASS BOOT TOKENS & MP GAUGE (x = 542..790) ---
    mp_now = player.get("movement_points", 0)
    hov_cost = player.get("ch3_hovered_move_cost")

    hdr_mp = (
        f"MARCH POOL: {mp_now} MP  (Cost: -{hov_cost} MP)"
        if hov_cost
        else f"MARCH POOL: {mp_now} MP  (1 Boot = 10 MP)"
    )
    draw_fitted_text(
        screen,
        hdr_mp,
        pygame.Rect(550, 433, 232, 20),
        GOLD_BRIGHT if hov_cost else DIAL_CREAM,
        bold=True,
        align="left",
        max_lines=1,
    )

    max_boots = max(3, min(6, int(math.ceil(max(mp_now, 30) / 10.0))))
    for b_idx in range(max_boots):
        bx = 566 + b_idx * 38
        by = 472
        token_mp = max(0, min(10, mp_now - b_idx * 10))
        fill_r = token_mp / 10.0
        is_cost_tok = bool(
            hov_cost
            and token_mp > 0
            and (b_idx * 10) >= (mp_now - hov_cost)
        )
        _draw_boot_token(screen, bx, by, fill_r, highlight_cost=is_cost_tok)

    legend_txt = (
        "Green = Sufficient MP | Amber = Forced March\n"
        "Red Border = Pin Crossed-Swords Clash!"
    )
    draw_fitted_text(
        screen,
        legend_txt,
        pygame.Rect(548, 496, 236, 40),
        DIAL_CREAM,
        align="left",
        max_lines=2,
    )

    end_turn_rect = pygame.Rect(542, 548, 248, 40)
    clashes_n = len(player.get("ch3_pending_clashes", []))
    btn_lbl = (
        f"Finish March ({clashes_n} Clash) >>"
        if clashes_n > 0
        else "Finish March & Watch AI >>"
    )
    pygame.draw.rect(screen, TATE_RED, end_turn_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_BRIGHT, end_turn_rect, 2, border_radius=6)
    draw_fitted_text(
        screen,
        btn_lbl,
        end_turn_rect,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )
    player["ch3_end_march_rect"] = end_turn_rect
    player["ch3_hover_zones"].append((
        end_turn_rect,
        "Conclude Player March",
        "Finish your daytime manoeuvres, watch the rival AI factions "
        "make their moves, and resolve all pinned Evening Clashes!",
    ))

    _draw_tabletop_hover_tooltip(screen, player, m_pos)


# =========================================================================
# 3. TABLETOP SETTINGS MODAL (`[Cog]` — WITH MONTH & VICTORY SELECTORS)
# =========================================================================
def draw_ch3_settings_modal(screen, player, font, small_font, mouse_pos):
    """
    Renders the Chapter 3 Tabletop Preferences, Starting Month Selector,
    Victory Condition Selector (100 Pts / 250 Pts / Total Domination),
    Tutorial Launcher, & Rulebook Modal.
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((12, 10, 8, 215))
    screen.blit(overlay, (0, 0))

    card = pygame.Rect(95, 24, 610, 552)
    pygame.draw.rect(screen, DIAL_CREAM, card, border_radius=10)
    pygame.draw.rect(screen, TATE_RED, card, 4, border_radius=10)
    pygame.draw.rect(
        screen, CLOCK_BLACK, card.inflate(-8, -8), 1, border_radius=8
    )

    draw_fitted_text(
        screen,
        "CAMPAIGN & TABLETOP SETTINGS, TUTORIALS & RULEBOOK",
        pygame.Rect(115, 36, 570, 24),
        TATE_RED,
        bold=True,
        max_lines=1,
    )

    m_idx = player.get("current_month_idx", 1) % 12
    month_name = ch3_war_engine.REPUBLICAN_MONTHS[m_idx]
    _, v_mode, v_lbl = ch3_war_engine.get_victory_goal_info(player)

    toggles = [
        (
            "cycle_victory_mode",
            "War Victory Condition",
            v_lbl,
            "Cycle between Standard (100 Pts), Grand Campaign (250 Pts), "
            "and Total Domination (Hold all 7 Strongholds).",
        ),
        (
            "cycle_month",
            "Active Republican Month",
            month_name,
            "Choose any of the 12 Republican Calendar months to experience "
            "autumn rains, winter blizzards, spring thaws, or summer heat.",
        ),
        (
            "toggle_tooltips",
            "Hover Help Tooltips",
            "ON" if player.get("ch3_show_tooltips", True) else "OFF",
            "Pop up parchment explanation cards when hovering over "
            "sockets, buttons, and clearings.",
        ),
        (
            "toggle_show_ai",
            "Show AI Turns on Board",
            "ON" if player.get("ch3_show_ai_moves", True) else "OFF",
            "Watch each computer faction's symmetric dice roll and "
            "march on the 3D board with the Heraldic Turn Banner.",
        ),
        (
            "toggle_ai_pacing",
            "AI Turn Playback Speed",
            player.get("ch3_ai_pacing", "NORMAL"),
            "Cycle between MANUAL (click per faction), SLOW (1.6s), "
            "NORMAL (1.0s), and FAST (0.4s).",
        ),
        (
            "toggle_confirm",
            "Phase Confirmations",
            "ON" if player.get("ch3_confirm_phases", True) else "OFF",
            "Warn before ending a phase if you have unslotted dice or "
            "unspent March Points.",
        ),
        (
            "toggle_click_slot",
            "Dice Control Mode",
            "DRAG + CLICK"
            if player.get("ch3_click_to_slot", True)
            else "DRAG ONLY",
            "Allow clicking a die and clicking a socket in addition to "
            "drag-and-drop.",
        ),
    ]

    rects = {}
    y_cur = 68
    for key, title, state_str, desc in toggles:
        row_rect = pygame.Rect(118, y_cur, 564, 52)
        pygame.draw.rect(screen, (232, 224, 206), row_rect, border_radius=6)
        pygame.draw.rect(screen, CLOCK_BLACK, row_rect, 1, border_radius=6)

        draw_fitted_text(
            screen,
            title,
            pygame.Rect(130, y_cur + 3, 360, 17),
            CLOCK_BLACK,
            bold=True,
            align="left",
            max_lines=1,
        )
        draw_fitted_text(
            screen,
            desc,
            pygame.Rect(130, y_cur + 20, 375, 28),
            (75, 68, 60),
            align="left",
            max_lines=2,
        )

        btn = pygame.Rect(518, y_cur + 8, 152, 36)
        is_on = state_str not in ("OFF", "DRAG ONLY")
        pygame.draw.rect(
            screen,
            EQUIPPED_GREEN if is_on else (110, 95, 85),
            btn,
            border_radius=5,
        )
        pygame.draw.rect(screen, CLOCK_BLACK, btn, 1, border_radius=5)
        draw_fitted_text(
            screen, state_str, btn, DIAL_CREAM, bold=True, max_lines=1
        )
        rects[key] = btn
        y_cur += 56

    pnp_btn = pygame.Rect(118, 468, 182, 40)
    tut_btn = pygame.Rect(309, 468, 182, 40)
    book_btn = pygame.Rect(500, 468, 182, 40)
    close_btn = pygame.Rect(240, 518, 320, 40)

    for b_r, b_txt, b_col in (
        (pnp_btn, "Pass & Play Lobby >>", EQUIPPED_GREEN),
        (tut_btn, "7-Faction Tutorial >>", (45, 95, 155)),
        (book_btn, "War Rulebook >>", (112, 48, 142)),
        (close_btn, "Resume Tabletop Campaign", TATE_RED),
    ):
        pygame.draw.rect(screen, b_col, b_r, border_radius=6)
        pygame.draw.rect(screen, GOLD_BRIGHT, b_r, 1, border_radius=6)
        draw_fitted_text(
            screen, b_txt, b_r, DIAL_CREAM, bold=True, max_lines=1
        )

    rects["open_pnp_lobby"] = pnp_btn
    rects["open_tutorial"] = tut_btn
    rects["open_rulebook"] = book_btn
    rects["close_settings"] = close_btn
    player["ch3_settings_rects"] = rects
    return rects


# =========================================================================
# 4. EVENING CLASH, EPILOGUE & VICTORY GRID RENDERERS
# =========================================================================
def draw_ch3_evening_ui(screen, player, font, small_font, mouse_pos):
    """Delegates Evening Clash rendering to the 5-Stage Battle Diorama."""
    if hasattr(ch3_combat_engine, "draw_ch3_battle_diorama"):
        ch3_combat_engine.draw_ch3_battle_diorama(
            screen, player, font, small_font, mouse_pos
        )
        return


def draw_ch3_epilogue_ui(screen, player, font, small_font, mouse_pos):
    """
    Renders the Tate Britain heritage Epilogue Chronicle screen when a
    faction achieves the active Victory Condition.
    """
    screen.fill((38, 30, 26))
    card_rect = pygame.Rect(40, 35, 720, 530)
    pygame.draw.rect(screen, DIAL_CREAM, card_rect, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, card_rect, 4, border_radius=8)
    pygame.draw.rect(
        screen, GOLD_ACCENT, card_rect.inflate(-12, -12), 1, border_radius=6
    )

    lines = player.get(
        "ch3_epilogue_lines",
        ["THE WAR FOR DTESSERA TERRA HAS CONCLUDED."],
    )
    if lines:
        draw_fitted_text(
            screen,
            lines[0],
            pygame.Rect(60, 52, 680, 30),
            TATE_RED,
            bold=True,
            max_lines=1,
        )

    if len(lines) > 1:
        draw_fitted_text(
            screen,
            lines[1],
            pygame.Rect(60, 86, 680, 26),
            CLOCK_BLACK,
            bold=True,
            max_lines=1,
        )

    body_text = "\n".join(lines[3:])
    body_rect = pygame.Rect(75, 130, 650, 340)
    draw_fitted_text(
        screen,
        body_text,
        body_rect,
        CLOCK_BLACK,
        bold=False,
        align="left",
        max_lines=14,
    )

    btn_rect = pygame.Rect(250, 495, 300, 44)
    pygame.draw.rect(screen, TATE_RED, btn_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_ACCENT, btn_rect, 1, border_radius=6)
    draw_fitted_text(
        screen,
        "View Hall of Hegemony >>",
        btn_rect,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )
    player["ch3_epilogue_btn_rect"] = btn_rect


def draw_victory_grid_ui(screen, font, small_font, mouse_pos, player=None):
    """
    Renders the persistent Hegemony Victory Grid, sorting completed runs
    from easiest (top-left) to hardest (bottom-right).
    """
    screen.fill((38, 30, 26))

    meta_data = {"victory_grid": []}
    if os.path.exists("profile_noburu_meta.json"):
        try:
            with open(
                "profile_noburu_meta.json", "r", encoding="utf-8"
            ) as file_obj:
                meta_data = json.load(file_obj)
        except (OSError, ValueError):
            pass

    grid = meta_data.get("victory_grid", [])

    title_surf = font.render("=== HALL OF HEGEMONY ===", True, TATE_RED)
    screen.blit(title_surf, (400 - title_surf.get_width() // 2, 32))

    sub_surf = small_font.render(
        f"Campaigns Won: {len(grid)} | Ordered Easiest (Top-Left) to "
        "Hardest (Bottom-Right)",
        True,
        DIAL_CREAM,
    )
    screen.blit(sub_surf, (400 - sub_surf.get_width() // 2, 64))

    start_x, start_y = 145, 96
    box_size, padding = 92, 10
    hovered_stamp = None

    for idx in range(20):
        row = idx // 5
        col = idx % 5
        bx = start_x + col * (box_size + padding)
        by = start_y + row * (box_size + padding)
        rect = pygame.Rect(bx, by, box_size, box_size)

        if idx < len(grid):
            stamp = grid[idx]
            fac_col = ch3_war_engine.DTESSERA_FACTIONS.get(
                stamp["faction"], ch3_war_engine.DTESSERA_FACTIONS["Union"]
            )["color"]
            pygame.draw.rect(screen, fac_col, rect, border_radius=6)
            pygame.draw.rect(screen, GOLD_ACCENT, rect, 2, border_radius=6)

            fac_lbl = small_font.render(
                stamp["faction"][:7], True, DIAL_CREAM
            )
            screen.blit(
                fac_lbl,
                fac_lbl.get_rect(center=(rect.centerx, rect.centery - 10)),
            )
            rank_lbl = small_font.render(
                stamp["starting_rank"][:4].upper(), True, DIAL_CREAM
            )
            screen.blit(
                rank_lbl,
                rank_lbl.get_rect(center=(rect.centerx, rect.bottom - 16)),
            )
            if rect.collidepoint(mouse_pos):
                hovered_stamp = stamp
                pygame.draw.rect(screen, DIAL_CREAM, rect, 3, border_radius=6)
        else:
            pygame.draw.rect(screen, (50, 42, 38), rect, border_radius=6)
            pygame.draw.rect(screen, (70, 62, 58), rect, 1, border_radius=6)

    if hovered_stamp:
        tt_rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] - 10, 235, 118)
        if tt_rect.right > 780:
            tt_rect.x = mouse_pos[0] - 250

        pygame.draw.rect(screen, DIAL_CREAM, tt_rect, border_radius=4)
        pygame.draw.rect(screen, TATE_RED, tt_rect, 2, border_radius=4)

        info = (
            f"Faction: {hovered_stamp['faction']}\n"
            f"Starting Rank: {hovered_stamp['starting_rank']}\n"
            f"Days Taken: {hovered_stamp['campaign_days_taken']}\n"
            f"Start Legacy: {hovered_stamp['starting_legacy_points']} Pts\n"
            f"Difficulty Weight: {hovered_stamp['difficulty_score']}/100"
        )
        draw_fitted_text(
            screen,
            info,
            tt_rect.inflate(-16, -12),
            CLOCK_BLACK,
            bold=False,
            align="left",
            max_lines=6,
        )

    btn_rect = pygame.Rect(145, 522, 245, 44)
    pygame.draw.rect(screen, TATE_RED, btn_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_ACCENT, btn_rect, 1, border_radius=6)
    draw_fitted_text(
        screen,
        "Return to Title Screen >>",
        btn_rect,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    wipe_rect = pygame.Rect(410, 522, 245, 44)
    confirm_arm = player.get("_confirm_wipe_grid", False) if player else False
    wipe_col = (185, 30, 30) if confirm_arm else (85, 45, 45)
    wipe_txt = (
        "CLICK AGAIN TO CONFIRM WIPE!"
        if confirm_arm
        else "Wipe Profile Victory Grid"
    )
    pygame.draw.rect(screen, wipe_col, wipe_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_ACCENT, wipe_rect, 1, border_radius=6)
    draw_fitted_text(
        screen, wipe_txt, wipe_rect, DIAL_CREAM, bold=True, max_lines=1
    )

    return btn_rect


# =========================================================================
# 5. CHARACTER STATUS, MANNEQUIN, INVENTORY & SYSTEM HELP POPUPS
# =========================================================================
def get_mannequin_loadout(player):
    """
    Inspects player['inventory'] and equipped state to populate the 8
    Paper-Doll Mannequin slots (including Horse Gear & Barding).
    """
    inv = player.get("inventory", [])

    if "helmet" in inv:
        head = (
            "Head",
            "Steel Nasal Helmet",
            "+3 Defence",
            "A steel nasal helm that deflects glancing blows and head-strikes.",
        )
    elif "crown of the first castellan" in inv:
        head = (
            "Head",
            "Castellan's Crown",
            "+1 Inf / Authority",
            "Ancient silver-and-jet circlet conferring feudal authority.",
        )
    else:
        head = (
            "Head",
            "Bareheaded",
            "No Head Armour",
            "You wear no helmet. Visit a blacksmith to buy or forge a Steel "
            "Helmet.",
        )

    if player.get("disguised_as_guard") or "guard uniform" in inv:
        torso = (
            "Torso",
            "Town Watch Uniform",
            "Guard Disguise (+2 Def)",
            "Blue-and-brass Watch tabard; lets you pass standard guard "
            "checkpoints.",
        )
    elif "gambeson" in inv:
        torso = (
            "Torso",
            "Quilted Gambeson",
            "+3 Torso Defence",
            "Multi-layered linen-and-wool padded armour against cuts and "
            "arrows.",
        )
    elif "leather jerkin" in inv:
        torso = (
            "Torso",
            "Leather Jerkin",
            "+2 Torso Defence",
            "Supple boiled leather vest favoured by scouts and outriders.",
        )
    else:
        torso = (
            "Torso",
            "Linen Shirt & Tunic",
            "0 Defence",
            "Ordinary woven town clothes offering no protection against "
            "blades.",
        )

    has_wax = "waxed jacket" in inv
    has_win = "warm winter coat" in inv
    if has_wax and has_win:
        coat = (
            "Outer Coat",
            "Winter & Waxed Coat",
            "Rain + Frost Immune",
            "Full all-weather protection against Torrential Rain, Snow, and "
            "Sub-Zero Frost!",
        )
    elif has_win:
        coat = (
            "Outer Coat",
            "Warm Winter Coat",
            "Frostproof (<=0°C)",
            "Sheepskin-lined wool greatcoat that insulates against freezing "
            "snow and hail.",
        )
    elif has_wax:
        coat = (
            "Outer Coat",
            "Oiled Waxed Jacket",
            "Rainproof",
            "Linseed-oiled sailcloth coat that keeps you dry in heavy and "
            "torrential rain.",
        )
    else:
        coat = (
            "Outer Coat",
            "Thin Travel Cloak",
            "No Storm Protection",
            "Offers scant shelter against freezing Brumaire downpours or "
            "blizzards.",
        )

    wep = player.get("equipped_weapon", "fists")
    poison = (
        f" [+{player.get('weapon_poison_charges', 0)} Poison]"
        if player.get("weapon_poison_charges", 0) > 0
        else ""
    )
    w_desc = db.item_database.get(wep, {}).get(
        "description", "Your bare knuckles."
    )
    weapon = (
        "Main Hand",
        f"{wep.title()}{poison}",
        f"Max Hit: {db.weapon_max_hit.get(wep, 2)}",
        w_desc,
    )

    t_mins = int(player.get("torch_minutes_left", 0))
    shld = player.get("equipped_shield", "none")
    if "storm lantern" in inv:
        offhand = (
            "Off-Hand",
            "Brass Storm Lantern",
            "Stormproof Light",
            "Whale-oil horn lantern that illuminates darkness and never blows "
            "out in storms.",
        )
    elif t_mins > 0:
        offhand = (
            "Off-Hand",
            f"Lit Torch ({t_mins}m)",
            "Active Night Light",
            f"Resin-soaked torch burning for {t_mins} more decimal minutes.",
        )
    elif shld and shld != "none":
        offhand = (
            "Off-Hand",
            shld.title(),
            "Equipped Shield",
            db.item_database.get(shld, {}).get(
                "description", "Defensive shield."
            ),
        )
    else:
        offhand = (
            "Off-Hand",
            "Empty Off-Hand",
            "No Light / Shield",
            "Carry a Storm Lantern or Use a Torch before travelling at night!",
        )

    if "ice crampons" in inv and "shadow-walker's soft-boots" in inv:
        feet = (
            "Footwear",
            "Spiked Shadow-Boots",
            "Ice-Proof +1 Stealth",
            "Suede night-runner boots fitted with removable iron "
            "ice-crampons.",
        )
    elif "ice crampons" in inv:
        feet = (
            "Footwear",
            "Forged Ice Crampons",
            "Immune to Black Ice",
            "Iron heel-spikes that prevent slips and HP loss on frozen "
            "mountain crags.",
        )
    elif "shadow-walker's soft-boots" in inv:
        feet = (
            "Footwear",
            "Shadow-Walker Boots",
            "+1 Stealth",
            "Suede-soled boots recovered from the catacombs for silent "
            "movement.",
        )
    else:
        feet = (
            "Footwear",
            "Leather Road-Boots",
            "Standard Footing",
            "Sturdy cobbler's boots, though prone to slipping on alpine "
            "black ice.",
        )

    charms = [
        c
        for c in (
            "hare's foot charm",
            "river-stone charm",
            "iron horseshoe charm",
            "owl-feather charm",
        )
        if c in inv
    ]
    dice_name = player.get("equipped_dice", "bone dice").title()
    if charms:
        c_name = charms[0].title()
        c_desc = db.item_database.get(charms[0], {}).get("description", "")
        pocket = (
            "Charm & Dice",
            c_name,
            f"Dice: {dice_name}",
            f"Active Charm: {c_desc} | Equipped Dice: {dice_name}.",
        )
    else:
        pocket = (
            "Charm & Dice",
            dice_name,
            "No Luck Charm",
            f"Equipped Dice: {dice_name}. Find pocket Charms to bend 2d6 "
            "luck and twists!",
        )

    has_horse = (
        ("horse" in inv)
        or player.get("riding_horse")
        or player.get("horse_stabled")
    )
    horse_gear = []
    horse_def = 0
    if "dragon shaffron" in inv:
        horse_gear.append("Dragon Shaffron (+10)")
        horse_def += 10
    if "horse armour" in inv:
        horse_gear.append("Plate Barding (+6)")
        horse_def += 6
    if "heavy winter blanket" in inv:
        horse_gear.append("Winter Blanket")
    if "iron horseshoe charm" in inv:
        horse_gear.append("Horseshoe Charm")

    gear_str = (
        ", ".join(horse_gear) if horse_gear else "No Horse Gear Equipped"
    )
    if has_horse:
        state_tag = (
            "Riding"
            if player.get("riding_horse")
            else ("Stabled" if player.get("horse_stabled") else "Leading")
        )
        h_food = int(player.get("horse_hunger", 100))
        h_wat = int(player.get("horse_thirst", 100))
        title_str = (
            f"Warhorse ({state_tag})"
            if horse_def > 0
            else f"Mount ({state_tag})"
        )
        sub_str = (
            f"+{horse_def} Def | {len(horse_gear)} Gear"
            if horse_gear
            else f"Fd {h_food}% / Wt {h_wat}%"
        )
        desc_str = (
            f"Mount Status: {state_tag} (Food {h_food}%, Water {h_wat}%). "
            f"Equipped Horse Gear: {gear_str}."
        )
        mount = ("Mount & Gear", title_str, sub_str, desc_str)
    else:
        mount = (
            "Mount & Gear",
            "On Foot (No Horse)",
            gear_str[:20],
            f"You have no horse. Carried Horse Gear in pack: {gear_str}.",
        )

    return [head, torso, coat, weapon, offhand, feet, pocket, mount]


def draw_status_popup(screen, player, font, font_bold, mouse_pos=None):
    """
    Renders the Full-Screen Character Status, Faction Standing, & Interactive
    Clothing/Armour Mannequin Window.
    """
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((12, 14, 20, 215))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(30, 20, 740, 560)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    draw_fitted_text(
        screen,
        "CHARACTER DOSSIER, ATTIRE MANNEQUIN & REALM STANDING",
        pygame.Rect(50, 28, 700, 26),
        TATE_RED,
        bold=True,
        align="left",
        max_lines=1,
    )

    man_box = pygame.Rect(48, 60, 348, 378)
    pygame.draw.rect(screen, (252, 248, 238), man_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, man_box, width=2, border_radius=8)
    draw_fitted_text(
        screen,
        "ATTIRE & ARMOUR MANNEQUIN (Hover Slot)",
        pygame.Rect(56, 66, 332, 22),
        TATE_RED,
        bold=True,
        align="left",
        max_lines=1,
    )

    cx, cy = 222, 215
    inv = player.get("inventory", [])

    if "warm winter coat" in inv or "waxed jacket" in inv:
        cloak_col = (
            (75, 95, 115) if "warm winter coat" in inv else (125, 95, 45)
        )
        pts = [
            (cx - 22, cy - 38),
            (cx + 22, cy - 38),
            (cx + 38, cy + 62),
            (cx - 38, cy + 62),
        ]
        pygame.draw.polygon(screen, cloak_col, pts)
        pygame.draw.polygon(screen, CLOCK_BLACK, pts, 2)

    pygame.draw.circle(screen, (215, 195, 170), (cx, cy - 60), 16)
    pygame.draw.circle(screen, CLOCK_BLACK, (cx, cy - 60), 16, 2)
    if "helmet" in inv:
        pygame.draw.arc(
            screen, (110, 120, 130), (cx - 18, cy - 78, 36, 34), 0, 3.14, 6
        )
        pygame.draw.line(
            screen, (90, 95, 105), (cx, cy - 75), (cx, cy - 55), 3
        )

    torso_col = (
        (45, 75, 130)
        if (player.get("disguised_as_guard") or "guard uniform" in inv)
        else (
            (175, 155, 125)
            if "gambeson" in inv
            else (
                (135, 85, 45) if "leather jerkin" in inv else (195, 188, 172)
            )
        )
    )
    pygame.draw.rect(
        screen, torso_col, (cx - 20, cy - 40, 40, 62), border_radius=6
    )
    pygame.draw.rect(
        screen, CLOCK_BLACK, (cx - 20, cy - 40, 40, 62), 2, border_radius=6
    )

    pygame.draw.line(
        screen, torso_col, (cx - 22, cy - 34), (cx - 38, cy + 12), 9
    )
    pygame.draw.line(
        screen, torso_col, (cx + 22, cy - 34), (cx + 38, cy + 12), 9
    )
    if player.get("equipped_weapon", "fists") != "fists":
        pygame.draw.line(
            screen, (180, 190, 205), (cx - 38, cy + 12), (cx - 48, cy - 28), 3
        )
    if "storm lantern" in inv or player.get("torch_minutes_left", 0) > 0:
        pygame.draw.circle(screen, (245, 185, 55), (cx + 40, cy + 16), 8)

    pygame.draw.line(
        screen, (80, 75, 68), (cx - 10, cy + 22), (cx - 12, cy + 78), 10
    )
    pygame.draw.line(
        screen, (80, 75, 68), (cx + 10, cy + 22), (cx + 12, cy + 78), 10
    )
    boot_col = (
        (50, 55, 65) if "shadow-walker's soft-boots" in inv else (95, 60, 35)
    )
    pygame.draw.rect(
        screen, boot_col, (cx - 20, cy + 72, 16, 12), border_radius=3
    )
    pygame.draw.rect(
        screen, boot_col, (cx + 4, cy + 72, 16, 12), border_radius=3
    )
    if "ice crampons" in inv:
        pygame.draw.line(
            screen, (190, 205, 220), (cx - 20, cy + 85), (cx - 4, cy + 85), 3
        )
        pygame.draw.line(
            screen, (190, 205, 220), (cx + 4, cy + 85), (cx + 20, cy + 85), 3
        )

    loadout = get_mannequin_loadout(player)
    hovered_slot = None

    for idx, (s_title, s_item, s_bonus, s_desc) in enumerate(loadout):
        col = 0 if idx < 4 else 1
        row = idx % 4
        sx = 56 if col == 0 else 264
        sy = 94 + row * 82
        s_rect = pygame.Rect(sx, sy, 124, 74)

        is_hov = s_rect.collidepoint(mouse_pos)
        if is_hov:
            hovered_slot = (s_title, s_item, s_bonus, s_desc)

        is_equipped = not any(
            w in s_item
            for w in (
                "Bareheaded",
                "Linen Shirt",
                "Thin Travel",
                "Empty",
                "On Foot",
                "Leather Road",
            )
        )
        bg = (
            (255, 244, 215)
            if is_hov
            else ((234, 244, 232) if is_equipped else (242, 238, 228))
        )
        bd = (
            TATE_RED
            if is_hov
            else (EQUIPPED_GREEN if is_equipped else (150, 145, 135))
        )

        pygame.draw.rect(screen, bg, s_rect, border_radius=6)
        pygame.draw.rect(
            screen, bd, s_rect, width=2 if is_hov else 1, border_radius=6
        )

        draw_fitted_text(
            screen,
            s_title.upper(),
            pygame.Rect(sx + 5, sy + 3, 114, 16),
            TATE_RED if is_hov else (90, 80, 70),
            bold=True,
            align="left",
            max_lines=1,
        )
        draw_fitted_text(
            screen,
            s_item,
            pygame.Rect(sx + 5, sy + 20, 114, 32),
            CLOCK_BLACK,
            bold=True,
            align="left",
            max_lines=2,
        )
        draw_fitted_text(
            screen,
            s_bonus,
            pygame.Rect(sx + 5, sy + 53, 114, 18),
            EQUIPPED_GREEN if is_equipped else (110, 105, 100),
            align="left",
            max_lines=1,
        )

    tip_box = pygame.Rect(48, 444, 348, 80)
    pygame.draw.rect(screen, (32, 36, 44), tip_box, border_radius=8)
    pygame.draw.rect(screen, GOLD_ACCENT, tip_box, width=2, border_radius=8)

    if hovered_slot:
        ht, hi, hb, hd = hovered_slot
        draw_fitted_text(
            screen,
            f"{ht}: {hi} ({hb})",
            pygame.Rect(56, 448, 332, 20),
            (255, 220, 110),
            bold=True,
            align="left",
            max_lines=1,
        )
        draw_fitted_text(
            screen, hd, pygame.Rect(56, 469, 332, 50), DIAL_CREAM, max_lines=3
        )
    else:
        draw_fitted_text(
            screen,
            "MANNEQUIN INSPECTOR:",
            pygame.Rect(56, 448, 332, 20),
            (255, 220, 110),
            bold=True,
            align="left",
            max_lines=1,
        )
        draw_fitted_text(
            screen,
            "Hover your mouse over any of the 8 slots on the mannequin above "
            "to inspect your worn clothing, horse barding, weather "
            "protection, and armour.",
            pygame.Rect(56, 469, 332, 50),
            DIAL_CREAM,
            max_lines=3,
        )

    comp_info = companions_engine.get_companion_info(player)
    comp_bonus_wt = companions_engine.get_companion_carry_bonus(player)

    curr_w = get_inventory_weight(player)
    max_w = get_max_carry_weight(player) + comp_bonus_wt

    v_box = pygame.Rect(410, 60, 342, 134)
    pygame.draw.rect(screen, (252, 248, 238), v_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, v_box, width=2, border_radius=8)
    draw_fitted_text(
        screen,
        "VITALS, PURSE, HORSE & SURVIVAL",
        pygame.Rect(420, 65, 322, 20),
        TATE_RED,
        bold=True,
        align="left",
        max_lines=1,
    )

    aff_list = player.get("afflictions", [])
    aff_str = (
        ", ".join(a.replace("_", " ").title() for a in aff_list)
        if aff_list
        else "Healthy"
    )
    h_gear_items = [
        g.title()
        for g in (
            "dragon shaffron",
            "horse armour",
            "heavy winter blanket",
            "iron horseshoe charm",
        )
        if g in inv
    ]
    h_gear_line = ", ".join(h_gear_items) if h_gear_items else "None"

    v_text = (
        f"HP: {player.get('health', 10)}/{player.get('max_health', 10)} | "
        f"Condition: {aff_str} | Rep: {player.get('reputation', 0)}\n"
        f"Food: {player.get('hunger', 100):.0f}% | "
        f"Water: {player.get('thirst', 100):.0f}% | "
        f"Load: {curr_w:.1f}/{max_w:.1f} lbs\n"
        f"Purse: {player.get('silver', 0)}s | "
        f"Banked: {player.get('banked_silver', 0)}s | "
        f"Chips: {player.get('casino_chips', 0)}\n"
        f"Horse Gear: {h_gear_line}\n"
        f"Skills: "
        f"{', '.join(s.title() for s in player.get('skills', [])) or 'None'}"
    )
    draw_fitted_text(
        screen,
        v_text,
        pygame.Rect(420, 86, 322, 102),
        CLOCK_BLACK,
        align="left",
        max_lines=5,
    )

    a_box = pygame.Rect(410, 200, 342, 120)
    pygame.draw.rect(screen, (252, 248, 238), a_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, a_box, width=2, border_radius=8)
    draw_fitted_text(
        screen,
        "ATTRIBUTES & CAMPAIGN STANDING",
        pygame.Rect(420, 205, 322, 20),
        TATE_RED,
        bold=True,
        max_lines=1,
    )

    route = player.get("chapter_2_route") or (
        f"Ch.1 ({(player.get('current_job') or 'Unemployed').title()})"
    )
    a_text = (
        f"STR: {player.get('strength', 0)} | "
        f"CHA: {player.get('charisma', 0)} | "
        f"STL: {player.get('stealth', 0)} | "
        f"INF: {player.get('influence', 0)} | "
        f"EQU: {player.get('equusense', 0)}\n"
        f"Track: {route}\n"
        f"Position Strength: {player.get('position_strength', 0)}% | "
        f"Exposure Tells: {player.get('exposure_tells', 0)}\n"
        f"Dungeons Conquered: {len(player.get('dungeons_cleared', []))}/4"
    )
    draw_fitted_text(
        screen, a_text, pygame.Rect(420, 226, 322, 88), CLOCK_BLACK, max_lines=4
    )

    f_box = pygame.Rect(410, 326, 342, 198)
    pygame.draw.rect(screen, (252, 248, 238), f_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, f_box, width=2, border_radius=8)
    draw_fitted_text(
        screen,
        "FACTION ALLEGIANCES & ROAD COMPANION",
        pygame.Rect(420, 331, 322, 20),
        TATE_RED,
        bold=True,
        max_lines=1,
    )

    f_text = (
        f"Union / F.A.I.: {player.get('faction_union', 0):+d}  |  "
        f"Town Watch / Crown: {player.get('faction_guard', 0):+d}\n"
        f"Wallmaker / Kokeshi: {player.get('faction_wallmakers', 0):+d}  |  "
        f"Communards: {player.get('faction_communards', 0):+d}\n"
        f"Forest Vanguardists: {player.get('faction_vanguardists', 0):+d}"
    )
    draw_fitted_text(
        screen, f_text, pygame.Rect(420, 352, 322, 58), CLOCK_BLACK, max_lines=3
    )

    comp_rect = pygame.Rect(420, 414, 322, 100)
    pygame.draw.rect(
        screen,
        (232, 244, 234) if comp_info else (242, 238, 228),
        comp_rect,
        border_radius=6,
    )
    pygame.draw.rect(
        screen,
        EQUIPPED_GREEN if comp_info else (150, 145, 135),
        comp_rect,
        width=2,
        border_radius=6,
    )

    if comp_info:
        draw_fitted_text(
            screen,
            f"COMPANION: {comp_info['name']}",
            pygame.Rect(428, 418, 306, 20),
            EQUIPPED_GREEN,
            bold=True,
            max_lines=1,
        )
        comp_desc = (
            f"Weapon: {comp_info['weapon']} "
            f"({comp_info['min_dmg']}-{comp_info['max_dmg']} Bonus Dmg/turn). "
            f"Pack-Mule Bonus: +{comp_info['carry_bonus']:.0f} lbs Max "
            "Carry Weight."
        )
        draw_fitted_text(
            screen,
            comp_desc,
            pygame.Rect(428, 440, 306, 68),
            CLOCK_BLACK,
            max_lines=3,
        )
    else:
        draw_fitted_text(
            screen,
            "ACTIVE ROAD COMPANION: None",
            pygame.Rect(428, 418, 306, 20),
            (105, 100, 95),
            bold=True,
            max_lines=1,
        )
        draw_fitted_text(
            screen,
            "Travel with Bandoka on the New Road, or escort Sister Hilde, "
            "Drover Tadgh, or Corporal Wulfgar for road combat assistance "
            "and pack-mule capacity!",
            pygame.Rect(428, 440, 306, 68),
            (95, 90, 85),
            max_lines=3,
        )


def draw_inventory_popup(screen, player, mouse_pos, font, font_bold):
    """
    Renders the Inventory Popup with fitted item cards and a bottom
    inspector bar.
    """
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(60, 50, 680, 470)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    cw, mw = get_inventory_weight(player), get_max_carry_weight(player)
    draw_fitted_text(
        screen,
        f"INVENTORY SATCHEL  (Carried Load: {cw:.1f} / {mw:.1f} lbs — "
        "Hover Item for Details)",
        pygame.Rect(85, 64, 630, 24),
        TATE_RED,
        bold=True,
        max_lines=1,
    )
    pygame.draw.line(screen, TATE_RED, (85, 92), (715, 92), 2)

    inv_counts = Counter(player.get("inventory", []))
    hovered_item = None

    col_w, row_h = 206, 40
    start_x, start_y = 85, 102

    for idx, (item_key, count) in enumerate(inv_counts.items()):
        col = idx % 3
        row = idx // 3
        gx = start_x + col * col_w
        gy = start_y + row * row_h
        if gy > 430:
            break

        box_rect = pygame.Rect(gx, gy, 198, 34)
        is_hover = box_rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            screen,
            (255, 244, 215) if is_hover else (252, 250, 244),
            box_rect,
            border_radius=5,
        )
        pygame.draw.rect(
            screen,
            TATE_RED if is_hover else (60, 55, 50),
            box_rect,
            width=2 if is_hover else 1,
            border_radius=5,
        )

        lbl = format_item_name(item_key) + (
            f" (x{count})" if count > 1 else ""
        )
        draw_fitted_text(
            screen,
            lbl,
            box_rect.inflate(-10, -4),
            CLOCK_BLACK,
            bold=is_hover,
            max_lines=1,
        )

        if is_hover:
            hovered_item = item_key

    insp_rect = pygame.Rect(85, 452, 630, 54)
    pygame.draw.rect(screen, (32, 36, 44), insp_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_ACCENT, insp_rect, width=2, border_radius=6)

    if hovered_item:
        info = db.item_database.get(hovered_item, {})
        desc = info.get("description", "Standard item.")
        w_lbs = info.get("weight", 0.2)
        val_s = info.get("price", 0)
        full_tip = (
            f"{format_item_name(hovered_item)} "
            f"(Wt: {w_lbs} lbs | Value: {val_s}s): {desc}"
        )
        draw_fitted_text(
            screen,
            full_tip,
            insp_rect.inflate(-14, -8),
            DIAL_CREAM,
            max_lines=2,
        )
    else:
        draw_fitted_text(
            screen,
            "Hover your cursor over any item above to read its weight, "
            "value, and description.",
            insp_rect.inflate(-14, -8),
            (200, 195, 185),
            max_lines=2,
        )


def draw_help_popup(screen, player, font, font_bold, mouse_pos):
    """
    Renders the Tate Britain Parchment Help, Survival Guide & System
    Pop-Out Modal (SYSTEM_MENU).
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((12, 14, 20, 215))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(30, 20, 740, 560)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render(
        "ADVENTURER'S HANDBOOK, SURVIVAL RULES & SYSTEM MENU", True, TATE_RED
    )
    screen.blit(title, (400 - title.get_width() // 2, 32))

    med_b = pygame.font.SysFont(
        "georgia,garamond,dejavuserif,arial", 15, bold=True
    )

    left_box = pygame.Rect(48, 62, 342, 430)
    pygame.draw.rect(screen, (252, 248, 238), left_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, left_box, width=2, border_radius=8)
    screen.blit(
        med_b.render("I. TIME, WEATHER & SURVIVAL RULES", True, TATE_RED),
        (60, 70),
    )

    left_sections = [
        (
            "The 1,000-Minute Decimal Clock",
            "Each day has 10 decimal hours (100 mins/hr). Shops & guilds "
            "keep individual opening hours. Click the clock face to toggle "
            "Analogue/Digital view.",
        ),
        (
            "Weather, Darkness & Elevation",
            "Click the Weather button to inspect the 3-day Barometric "
            "Forecast & Ground Saturation. Heavy rains flood Tier 1 (5m) "
            "hollows—detour via Tier 3 (60m) high ground! Carry a Torch or "
            "Storm Lantern at night.",
        ),
        (
            "Stamina, Spoilage & Afflictions",
            "Walking and working drain Food and Water. Fresh produce spoils "
            "over time. Cure Damp-Chill, Food Poisoning, or Wound Sepsis at "
            "the Apothecary so natural healing can resume.",
        ),
        (
            "Carry Weight, Footlockers & Postal Stabling",
            "Exceeding Max Weight slows travel and drains stamina. Use "
            "'Action -> Stash' at Inns to store gear, and pay Squire "
            "Godspeed's stabling tab from any Postbox across the island!",
        ),
    ]
    cy = 94
    for hdr, body in left_sections:
        screen.blit(med_b.render(f"• {hdr}", True, CLOCK_BLACK), (60, cy))
        cy += 18
        draw_fitted_text(
            screen,
            body,
            pygame.Rect(64, cy, 314, 68),
            (55, 50, 45),
            align="left",
            max_lines=4,
        )
        cy += 72

    right_box = pygame.Rect(404, 62, 348, 430)
    pygame.draw.rect(screen, (252, 248, 238), right_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, right_box, width=2, border_radius=8)
    screen.blit(
        med_b.render("II. CURRENT CAMPAIGN & CONTROLS", True, TATE_RED),
        (416, 70),
    )

    route = player.get("chapter_2_route")
    if player.get("ch3_rank"):
        stage_hdr = "Active Stage: Chapter III"
        stage_body = (
            "Roll Dawn Dice, split and march Faction Meeples across the 3D "
            "board, watch the symmetric AI turns, or launch Solo Commando "
            "Missions if your battalions fall."
        )
    elif route:
        stage_hdr = "Active Stage: Chapter II"
        stage_body = (
            "Investigate regional towns, question locals, and search the "
            "environment to prepare the field before launching each of your "
            "career missions."
        )
    else:
        stage_hdr = "Active Stage: Chapter I"
        stage_body = (
            "Complete 5 shifts in your chosen trade to build your "
            "attributes, skills, and faction standing. At Shift 6, qualify "
            "for one of the 10 regional career tracks on the Town Hall "
            "Noticeboard!"
        )

    right_sections = [
        (stage_hdr, stage_body),
        (
            "Mounts & Travelling Companions",
            "Horses and tamed Mouflins cut wilderness travel time (stable "
            "horses at Murum Stables for 2s/day or pay by post). Recruit "
            "road companions for combat assist!",
        ),
        (
            "D-Pad Look/Move & Optical Scopes",
            "Click the centre of the D-Pad (or the Mode button) to switch "
            "between MOVE and LOOK. In Lignum Forest, carry a Brass Compass "
            "or Carved Yew Wayfinder to prevent disorientation!",
        ),
        (
            "Using Tools, Kits & Shortcuts",
            "• Use 'Action -> Use Item' to light Torches, roll Dice, or "
            "operate the Press & Codewheel.\n"
            "• [C] Status | [I] Inventory | [W] Weather | [T] Topo | "
            "[F10] Fullscreen",
        ),
    ]
    cy = 94
    for hdr, body in right_sections:
        screen.blit(med_b.render(f"• {hdr}", True, CLOCK_BLACK), (416, cy))
        cy += 18
        draw_fitted_text(
            screen,
            body,
            pygame.Rect(420, cy, 320, 68),
            (55, 50, 45),
            align="left",
            max_lines=4,
        )
        cy += 72
        
