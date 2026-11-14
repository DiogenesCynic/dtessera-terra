"""
ch3_board_renderer.py
---------------------
Renders the Root-inspired Chapter 3 3D Tabletop Map Board (with 12-month
Republican Calendar seasonal terrain tinting), Top Phase & Hegemony
Ribbon (supporting 100-Pt, 250-Pt, and 7-Stronghold Domination modes),
Right-Hand Camera Control Rail, Carved Wooden Faction Meeples, Pinned
Crossed-Swords ('⚔') Battle Tokens, and Animated AI Turn Trajectory Arrows.
"""

import math
import pygame

import ch3_combat_engine
import ch3_war_engine
from ui_components import draw_fitted_text
import weather_engine

# --- TABLETOP & HERITAGE PALETTE CONSTANTS ---
WALNUT_DARK = (32, 24, 19)
WALNUT_GRAIN = (42, 31, 24)
BOARD_EDGE_LIGHT = (198, 178, 142)
BOARD_EDGE_DARK = (118, 98, 72)
PARCHMENT_BASE = (232, 222, 198)
TATE_RED = (168, 50, 35)
DIAL_CREAM = (244, 239, 225)
CLOCK_BLACK = (28, 26, 24)
GOLD_ACCENT = (212, 168, 58)
GOLD_BRIGHT = (250, 215, 85)
VALID_GREEN = (52, 168, 78)
MIRE_AMBER = (215, 142, 38)
CLASH_CRIMSON = (195, 42, 42)

TOP_RIBBON_RECT = pygame.Rect(0, 0, 800, 44)
MAP_VIEWPORT_RECT = pygame.Rect(0, 44, 736, 376)
CAMERA_RAIL_RECT = pygame.Rect(736, 44, 64, 376)

ZOOM_MIN = 20
ZOOM_MAX = 72
LOD_MEEPLE_THRESHOLD = 38
TILT_MIN = 0.55
TILT_MAX = 1.00


# =========================================================================
# 1. CAMERA INITIALISATION, CENTRING & SLIDER EVENT HANDLING
# =========================================================================
def ensure_board_camera(player):
    """Initialises default 3D tabletop camera parameters inside `player`."""
    if "ch3_zoom" not in player:
        player["ch3_zoom"] = 44
    if "ch3_tilt" not in player:
        player["ch3_tilt"] = 0.72
    if "ch3_cam_x" not in player or "ch3_cam_y" not in player:
        centre_camera_on_player_forces(player)


def centre_camera_on_tile(player, pos_key):
    """Centres the 3D tabletop camera smoothly on `pos_key` ('x,y')."""
    try:
        tx, ty = map(int, str(pos_key).split(","))
    except ValueError:
        tx, ty = 10, 14

    zoom = player.get("ch3_zoom", 44)
    tilt = player.get("ch3_tilt", 0.72)
    tile_w = int(zoom)
    tile_h = max(12, int(zoom * tilt))

    target_px = (tx - 1) * tile_w + tile_w // 2
    target_py = (25 - ty) * tile_h + tile_h // 2

    player["ch3_cam_x"] = int(target_px - MAP_VIEWPORT_RECT.width // 2)
    player["ch3_cam_y"] = int(target_py - MAP_VIEWPORT_RECT.height // 2)


def centre_camera_on_player_forces(player):
    """Centres the tabletop camera on the player's capital or lead army."""
    my_fac = player.get("ch3_faction", "Union")
    armies = player.get("ch3_armies", {})
    target_key = (
        player.get("ch3_factions", {})
        .get(my_fac, {})
        .get("capital", "10,14")
    )
    for pos_key, army in armies.items():
        if army.get("faction") == my_fac:
            target_key = pos_key
            break
    centre_camera_on_tile(player, target_key)


def _set_zoom_keeping_centre(player, new_zoom):
    """Updates `ch3_zoom` while keeping the viewport centre anchored."""
    old_zoom = player.get("ch3_zoom", 44)
    clamped_zoom = max(ZOOM_MIN, min(ZOOM_MAX, int(new_zoom)))
    if clamped_zoom == old_zoom:
        return

    ratio = clamped_zoom / float(old_zoom)
    cx = player.get("ch3_cam_x", 0) + MAP_VIEWPORT_RECT.width // 2
    cy = player.get("ch3_cam_y", 0) + MAP_VIEWPORT_RECT.height // 2
    player["ch3_zoom"] = clamped_zoom
    player["ch3_cam_x"] = int(cx * ratio - MAP_VIEWPORT_RECT.width // 2)
    player["ch3_cam_y"] = int(cy * ratio - MAP_VIEWPORT_RECT.height // 2)


def _set_tilt_keeping_centre(player, new_tilt):
    """Updates `ch3_tilt` while keeping the vertical viewport anchored."""
    old_tilt = player.get("ch3_tilt", 0.72)
    clamped_tilt = max(TILT_MIN, min(TILT_MAX, round(float(new_tilt), 2)))
    if abs(clamped_tilt - old_tilt) < 0.005:
        return

    ratio = clamped_tilt / float(old_tilt)
    cy = player.get("ch3_cam_y", 0) + MAP_VIEWPORT_RECT.height // 2
    player["ch3_tilt"] = clamped_tilt
    player["ch3_cam_y"] = int(cy * ratio - MAP_VIEWPORT_RECT.height // 2)


def handle_board_camera_event(event, player):
    """
    Processes mouse clicks and slider drags on the Right-Hand Camera Rail
    and Top Ribbon buttons. Returns (handled_bool, action_tag_or_None).
    """
    ensure_board_camera(player)
    ui_rects = player.get("ch3_board_ui_rects", {})

    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        player["ch3_dragging_slider"] = None
        return False, None

    if event.type == pygame.MOUSEMOTION:
        active_drag = player.get("ch3_dragging_slider")
        if active_drag == "zoom":
            track = ui_rects.get("zoom_track")
            if track:
                pct = 1.0 - (
                    (event.pos[1] - track.top) / float(max(1, track.height))
                )
                pct = max(0.0, min(1.0, pct))
                _set_zoom_keeping_centre(
                    player, ZOOM_MIN + pct * (ZOOM_MAX - ZOOM_MIN)
                )
                return True, None
        elif active_drag == "tilt":
            track = ui_rects.get("tilt_track")
            if track:
                pct = 1.0 - (
                    (event.pos[1] - track.top) / float(max(1, track.height))
                )
                pct = max(0.0, min(1.0, pct))
                _set_tilt_keeping_centre(
                    player, TILT_MIN + pct * (TILT_MAX - TILT_MIN)
                )
                return True, None
        return False, None

    if event.type == pygame.KEYDOWN:
        pan_step = 48
        if event.key == pygame.K_LEFT:
            player["ch3_cam_x"] -= pan_step
            return True, None
        if event.key == pygame.K_RIGHT:
            player["ch3_cam_x"] += pan_step
            return True, None
        if event.key == pygame.K_UP:
            player["ch3_cam_y"] -= pan_step
            return True, None
        if event.key == pygame.K_DOWN:
            player["ch3_cam_y"] += pan_step
            return True, None

    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False, None

    pos = event.pos

    if (
        ui_rects.get("btn_settings")
        and ui_rects["btn_settings"].collidepoint(pos)
    ):
        return True, "OPEN_CH3_SETTINGS"
    if (
        ui_rects.get("btn_rulebook")
        and ui_rects["btn_rulebook"].collidepoint(pos)
    ):
        return True, "OPEN_CH3_RULEBOOK"

    for f_key, f_rect in player.get("ch3_faction_badge_rects", {}).items():
        if f_rect and f_rect.collidepoint(pos):
            if f_key != player.get("ch3_faction", "Union"):
                player["ch3_selected_rival"] = f_key
            return True, f"SELECT_RIVAL_{f_key}"

    if ui_rects.get("zoom_plus") and ui_rects["zoom_plus"].collidepoint(pos):
        _set_zoom_keeping_centre(player, player["ch3_zoom"] + 6)
        return True, None
    if (
        ui_rects.get("zoom_minus")
        and ui_rects["zoom_minus"].collidepoint(pos)
    ):
        _set_zoom_keeping_centre(player, player["ch3_zoom"] - 6)
        return True, None
    if (
        ui_rects.get("zoom_track")
        and ui_rects["zoom_track"].collidepoint(pos)
    ):
        player["ch3_dragging_slider"] = "zoom"
        track = ui_rects["zoom_track"]
        pct = 1.0 - ((pos[1] - track.top) / float(max(1, track.height)))
        _set_zoom_keeping_centre(
            player, ZOOM_MIN + max(0.0, min(1.0, pct)) * (ZOOM_MAX - ZOOM_MIN)
        )
        return True, None

    if ui_rects.get("tilt_plus") and ui_rects["tilt_plus"].collidepoint(pos):
        _set_tilt_keeping_centre(player, player["ch3_tilt"] + 0.08)
        return True, None
    if (
        ui_rects.get("tilt_minus")
        and ui_rects["tilt_minus"].collidepoint(pos)
    ):
        _set_tilt_keeping_centre(player, player["ch3_tilt"] - 0.08)
        return True, None
    if (
        ui_rects.get("tilt_track")
        and ui_rects["tilt_track"].collidepoint(pos)
    ):
        player["ch3_dragging_slider"] = "tilt"
        track = ui_rects["tilt_track"]
        pct = 1.0 - ((pos[1] - track.top) / float(max(1, track.height)))
        _set_tilt_keeping_centre(
            player, TILT_MIN + max(0.0, min(1.0, pct)) * (TILT_MAX - TILT_MIN)
        )
        return True, None

    pan_px = 64
    if ui_rects.get("pan_n") and ui_rects["pan_n"].collidepoint(pos):
        player["ch3_cam_y"] -= pan_px
        return True, None
    if ui_rects.get("pan_s") and ui_rects["pan_s"].collidepoint(pos):
        player["ch3_cam_y"] += pan_px
        return True, None
    if ui_rects.get("pan_w") and ui_rects["pan_w"].collidepoint(pos):
        player["ch3_cam_x"] -= pan_px
        return True, None
    if ui_rects.get("pan_e") and ui_rects["pan_e"].collidepoint(pos):
        player["ch3_cam_x"] += pan_px
        return True, None
    if (
        ui_rects.get("pan_centre")
        and ui_rects["pan_centre"].collidepoint(pos)
    ):
        centre_camera_on_player_forces(player)
        return True, None

    return False, None


# =========================================================================
# 2. CARVED FACTION MEEPLES, CROSSED SWORDS & TACTICAL DISCS
# =========================================================================
def _draw_single_carved_meeple(screen, cx, cy, scale, faction):
    """
    Draws a single carved wooden meeple standing upright at (cx, cy) with
    a faction-specific head/hat silhouette and 3D wooden bevel.
    """
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        faction, ch3_war_engine.DTESSERA_FACTIONS["Union"]
    )
    col = spec["color"]
    crest = spec["crest"]
    dark = (
        max(0, col[0] - 55),
        max(0, col[1] - 55),
        max(0, col[2] - 55),
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
    pygame.draw.polygon(screen, col, body_pts)
    pygame.draw.polygon(screen, CLOCK_BLACK, body_pts, 1)

    head_y = cy - h - max(2, int(2 * scale))
    head_r = max(3, int(4.5 * scale))
    pygame.draw.circle(screen, dark, (cx + 2, head_y + 2), head_r)
    pygame.draw.circle(screen, col, (cx, head_y), head_r)
    pygame.draw.circle(screen, CLOCK_BLACK, (cx, head_y), head_r, 1)

    if faction == "Union":
        cap_rect = pygame.Rect(
            cx - head_r - 2, head_y - head_r - 2, head_r * 2 + 5, 4
        )
        pygame.draw.rect(screen, crest, cap_rect, border_radius=1)
        pygame.draw.rect(screen, CLOCK_BLACK, cap_rect, 1, border_radius=1)

    elif faction == "Laydere":
        pygame.draw.polygon(
            screen,
            crest,
            [
                (cx - 2, head_y - head_r),
                (cx, head_y - head_r - 6),
                (cx + 3, head_y - head_r),
            ],
        )
        pygame.draw.line(
            screen,
            (210, 220, 235),
            (cx + w, cy),
            (cx + w, head_y - 5),
            2,
        )

    elif faction == "Ragmore":
        pygame.draw.polygon(
            screen,
            crest,
            [
                (cx - head_r, head_y - 1),
                (cx, head_y - head_r - 6),
                (cx + head_r, head_y - 1),
            ],
        )

    elif faction == "Kokeshi":
        pygame.draw.line(
            screen,
            crest,
            (cx - head_r - 4, head_y - head_r + 1),
            (cx + head_r + 4, head_y - head_r + 1),
            3,
        )

    elif faction == "FAI":
        pygame.draw.polygon(
            screen,
            crest,
            [
                (cx - head_r, head_y - head_r + 2),
                (cx + head_r + 2, head_y - head_r - 3),
                (cx + head_r, head_y - 1),
            ],
        )
        pygame.draw.line(
            screen,
            crest,
            (cx - 4, cy - int(h * 0.80)),
            (cx + 4, cy - int(h * 0.35)),
            2,
        )

    elif faction in ("Communards", "Vanguardists"):
        pygame.draw.polygon(
            screen,
            crest,
            [
                (cx - head_r, head_y - 2),
                (cx - head_r - 2, head_y - head_r - 5),
                (cx - 1, head_y - head_r),
            ],
        )
        pygame.draw.polygon(
            screen,
            crest,
            [
                (cx + head_r, head_y - 2),
                (cx + head_r + 2, head_y - head_r - 5),
                (cx + 1, head_y - head_r),
            ],
        )


def _draw_crossed_swords_token(screen, cx, cy, zoom):
    """
    Draws a pulsing Crimson & Gold Crossed-Swords ('⚔') Battle Token on a
    contested clearing where an Afternoon attack has been pinned.
    """
    now = pygame.time.get_ticks()
    pulse = 2 if (now // 280) % 2 == 0 else 0
    rad = max(9, int(zoom * 0.26)) + pulse

    pygame.draw.circle(screen, CLOCK_BLACK, (cx + 1, cy + 2), rad)
    pygame.draw.circle(screen, CLASH_CRIMSON, (cx, cy), rad)
    pygame.draw.circle(screen, GOLD_BRIGHT, (cx, cy), rad, 2)

    off = max(4, int(rad * 0.58))
    pygame.draw.line(
        screen, DIAL_CREAM, (cx - off, cy + off), (cx + off, cy - off), 2
    )
    pygame.draw.line(
        screen, DIAL_CREAM, (cx - off, cy - off), (cx + off, cy + off), 2
    )
    pygame.draw.circle(screen, GOLD_BRIGHT, (cx, cy), 2)


def _draw_army_on_tile(
    screen,
    cx,
    cy,
    zoom,
    army,
    is_player_owned,
    is_selected,
    can_move_now,
    small_font,
):
    """
    Renders an army on tile centre (cx, cy).
    Swaps between Tactical Discs (< 38px) and Carved Meeples (>= 38px).
    """
    faction = army.get("faction", "Union")
    count = army.get("count", 1)
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        faction, ch3_war_engine.DTESSERA_FACTIONS["Union"]
    )
    col = spec["color"]
    crest = spec["crest"]
    now = pygame.time.get_ticks()

    if zoom < LOD_MEEPLE_THRESHOLD:
        rad = max(9, int(zoom * 0.38))
        pygame.draw.circle(screen, CLOCK_BLACK, (cx + 1, cy + 2), rad)
        if is_player_owned:
            pulse = 2 if (can_move_now and (now // 350) % 2 == 0) else 0
            pygame.draw.circle(
                screen, GOLD_BRIGHT, (cx, cy), rad + 3 + pulse
            )
            pygame.draw.circle(
                screen, CLOCK_BLACK, (cx, cy), rad + 3 + pulse, 1
            )
        if is_selected:
            pygame.draw.circle(screen, VALID_GREEN, (cx, cy), rad + 5, 2)

        pygame.draw.circle(screen, col, (cx, cy), rad)
        pygame.draw.circle(screen, crest, (cx, cy), rad, 1)

        num_surf = small_font.render(str(count), True, DIAL_CREAM)
        screen.blit(num_surf, num_surf.get_rect(center=(cx, cy)))
        return

    scale = zoom / 48.0
    ped_w = int(zoom * 0.78)
    ped_h = max(10, int(zoom * 0.34))
    ped_rect = pygame.Rect(
        cx - ped_w // 2, cy - ped_h // 2 + 4, ped_w, ped_h
    )

    if is_selected:
        pygame.draw.ellipse(
            screen, GOLD_BRIGHT, ped_rect.inflate(10, 8), 3
        )
    if is_player_owned:
        pulse_w = 2 if (can_move_now and (now // 400) % 2 == 0) else 1
        pygame.draw.ellipse(screen, DIAL_CREAM, ped_rect.inflate(4, 4))
        pygame.draw.ellipse(
            screen, GOLD_ACCENT, ped_rect.inflate(4, 4), pulse_w + 1
        )
    else:
        pygame.draw.ellipse(screen, (52, 46, 42), ped_rect)
        pygame.draw.ellipse(screen, CLOCK_BLACK, ped_rect, 1)

    if count == 1:
        offsets = [(0, 2)]
    elif count == 2:
        offsets = [(-int(8 * scale), 2), (int(8 * scale), 2)]
    elif count <= 5:
        offsets = [
            (-int(9 * scale), -int(3 * scale)),
            (int(9 * scale), -int(3 * scale)),
            (0, int(5 * scale)),
        ]
    else:
        offsets = [
            (-int(10 * scale), -int(4 * scale)),
            (int(10 * scale), -int(4 * scale)),
            (-int(6 * scale), int(5 * scale)),
            (int(6 * scale), int(5 * scale)),
        ]

    for ox, oy in offsets:
        _draw_single_carved_meeple(
            screen, cx + ox, cy + oy, scale * 0.85, faction
        )

    if is_player_owned:
        pole_x = cx + int(13 * scale)
        pole_top = cy - int(26 * scale)
        pygame.draw.line(
            screen, GOLD_BRIGHT, (pole_x, cy), (pole_x, pole_top), 2
        )
        flag_pts = [
            (pole_x, pole_top),
            (pole_x + int(12 * scale), pole_top + int(4 * scale)),
            (pole_x, pole_top + int(8 * scale)),
        ]
        pygame.draw.polygon(screen, col, flag_pts)
        pygame.draw.polygon(screen, GOLD_BRIGHT, flag_pts, 1)

    badge_w = max(18, int(20 * scale))
    badge_h = max(13, int(14 * scale))
    badge_rect = pygame.Rect(
        cx - badge_w // 2, ped_rect.bottom - badge_h // 2 - 2, badge_w, badge_h
    )
    pygame.draw.rect(
        screen,
        CLOCK_BLACK if not is_player_owned else col,
        badge_rect,
        border_radius=4,
    )
    pygame.draw.rect(
        screen,
        GOLD_BRIGHT if is_player_owned else crest,
        badge_rect,
        1,
        border_radius=4,
    )
    cnt_surf = small_font.render(str(count), True, DIAL_CREAM)
    screen.blit(cnt_surf, cnt_surf.get_rect(center=badge_rect.center))


# =========================================================================
# 3. BESPOKE FACTION SYMBOLS, COG ICON & TOP RIBBON (y = 0..44)
# =========================================================================
def _draw_faction_symbol(screen, f_key, cx, cy, crest_col):
    """Draws the bespoke geometric icon for each of the 7 factions."""
    if f_key == "Union":
        pygame.draw.circle(screen, crest_col, (cx - 4, cy), 6, 2)
        pygame.draw.circle(screen, crest_col, (cx + 4, cy), 6, 2)

    elif f_key == "Kokeshi":
        pygame.draw.circle(screen, crest_col, (cx, cy - 5), 4)
        pygame.draw.circle(screen, CLOCK_BLACK, (cx, cy - 5), 4, 1)
        doll_body = [
            (cx - 4, cy - 1),
            (cx + 4, cy - 1),
            (cx + 3, cy + 8),
            (cx - 3, cy + 8),
        ]
        pygame.draw.polygon(screen, crest_col, doll_body)
        pygame.draw.polygon(screen, CLOCK_BLACK, doll_body, 1)
        pygame.draw.line(
            screen, CLOCK_BLACK, (cx - 3, cy + 3), (cx + 3, cy + 3), 2
        )

    elif f_key == "Laydere":
        pygame.draw.rect(screen, crest_col, (cx - 6, cy - 1, 12, 9))
        for mx in (cx - 6, cx - 1, cx + 3):
            pygame.draw.rect(screen, crest_col, (mx, cy - 5, 3, 4))
        pygame.draw.rect(screen, CLOCK_BLACK, (cx - 2, cy + 3, 4, 5))

    elif f_key == "Ragmore":
        pygame.draw.rect(screen, crest_col, (cx - 4, cy - 1, 8, 10))
        pygame.draw.polygon(
            screen,
            crest_col,
            [(cx - 6, cy - 1), (cx, cy - 8), (cx + 6, cy - 1)],
        )
        pygame.draw.line(
            screen, CLOCK_BLACK, (cx, cy + 1), (cx, cy + 5), 2
        )

    elif f_key == "FAI":
        flag_r = pygame.Rect(cx - 8, cy - 6, 16, 12)
        pygame.draw.polygon(
            screen,
            (225, 55, 45),
            [flag_r.topleft, flag_r.topright, flag_r.bottomleft],
        )
        pygame.draw.polygon(
            screen,
            (18, 18, 22),
            [flag_r.topright, flag_r.bottomright, flag_r.bottomleft],
        )
        pygame.draw.rect(screen, DIAL_CREAM, flag_r, 1)

    elif f_key == "Communards":
        pygame.draw.circle(screen, crest_col, (cx, cy), 7, 2)
        pygame.draw.line(
            screen, crest_col, (cx, cy - 7), (cx, cy + 7), 2
        )
        pygame.draw.line(
            screen, crest_col, (cx, cy), (cx - 5, cy + 5), 2
        )
        pygame.draw.line(
            screen, crest_col, (cx, cy), (cx + 5, cy + 5), 2
        )

    elif f_key == "Vanguardists":
        pygame.draw.line(
            screen, crest_col, (cx - 4, cy - 4), (cx + 5, cy + 6), 2
        )
        pygame.draw.line(
            screen, crest_col, (cx - 6, cy - 2), (cx - 1, cy - 6), 3
        )
        arc_rect = pygame.Rect(cx - 6, cy - 7, 13, 13)
        pygame.draw.arc(
            screen, crest_col, arc_rect, -0.7, 2.5, 2
        )
        pygame.draw.line(
            screen, crest_col, (cx - 2, cy + 3), (cx - 6, cy + 7), 2
        )


def _draw_cog_icon(screen, cx, cy, color, bg_color):
    """Draws a crisp 8-toothed universal Settings Cog icon at (cx, cy)."""
    for deg in range(0, 360, 45):
        rad = math.radians(deg)
        x1 = cx + int(math.cos(rad) * 5)
        y1 = cy + int(math.sin(rad) * 5)
        x2 = cx + int(math.cos(rad) * 10)
        y2 = cy + int(math.sin(rad) * 10)
        pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3)

    pygame.draw.circle(screen, color, (cx, cy), 7)
    pygame.draw.circle(screen, bg_color, (cx, cy), 3)
    pygame.draw.circle(screen, color, (cx, cy), 3, 1)


def draw_top_tabletop_ribbon(
    screen, player, small_font, active_phase="MORNING"
):
    """
    Renders the spacious Top Ribbon (y = 0..44):
    - Left (x = 8..126): Single Stage Indicator ("Morning", "March", "Engage")
    - Centre (x = 134..708): 7 Faction Symbol + Score Boxes (with hover popup)
    - Right (x = 716..794): [Cog] Settings & [?] Rulebook Buttons
    """
    ch3_war_engine.recalculate_ch3_total_points(player)
    ui_rects = player.setdefault("ch3_board_ui_rects", {})
    mouse_pos = pygame.mouse.get_pos()
    v_mode = player.get("ch3_victory_mode", "100_PTS")

    pygame.draw.rect(screen, WALNUT_DARK, TOP_RIBBON_RECT)
    pygame.draw.line(screen, GOLD_ACCENT, (0, 43), (800, 43), 2)

    stage_names = {
        "MORNING": "Morning",
        "AFTERNOON": "March",
        "EVENING": "Engage",
    }
    stage_str = stage_names.get(active_phase, "Morning")
    phase_rect = pygame.Rect(8, 6, 118, 32)
    pygame.draw.rect(screen, TATE_RED, phase_rect, border_radius=6)
    pygame.draw.rect(screen, GOLD_BRIGHT, phase_rect, 2, border_radius=6)
    draw_fitted_text(
        screen, stage_str, phase_rect, DIAL_CREAM, bold=True, max_lines=1
    )

    player["ch3_faction_badge_rects"] = {}
    selected_rival = player.get("ch3_selected_rival")
    my_fac = player.get("ch3_faction", "Union")
    hovered_faction_badge = None
    bx = 134

    for f_key, f_spec in ch3_war_engine.DTESSERA_FACTIONS.items():
        f_data = player.get("ch3_factions", {}).get(f_key, {})
        f_pts = f_data.get("total_points", 10)
        keeps_n = f_data.get("strongholds_held", 1)
        disp_num = f"{keeps_n}/7" if v_mode == "DOMINATION" else str(f_pts)

        b_rect = pygame.Rect(bx, 6, 78, 32)
        pygame.draw.rect(screen, f_spec["color"], b_rect, border_radius=5)

        if f_key == my_fac:
            pygame.draw.rect(
                screen, DIAL_CREAM, b_rect, 2, border_radius=5
            )
        elif f_key == selected_rival:
            pygame.draw.rect(
                screen, GOLD_BRIGHT, b_rect, 2, border_radius=5
            )
        else:
            pygame.draw.rect(
                screen, CLOCK_BLACK, b_rect, 1, border_radius=5
            )

        _draw_faction_symbol(
            screen,
            f_key,
            b_rect.left + 20,
            b_rect.centery,
            f_spec["crest"],
        )
        pygame.draw.line(
            screen,
            CLOCK_BLACK,
            (b_rect.left + 38, b_rect.top + 5),
            (b_rect.left + 38, b_rect.bottom - 5),
            1,
        )
        score_rect = pygame.Rect(b_rect.left + 40, b_rect.top + 4, 34, 24)
        draw_fitted_text(
            screen,
            disp_num,
            score_rect,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )

        if b_rect.collidepoint(mouse_pos):
            hovered_faction_badge = (f_key, f_spec, f_pts, keeps_n, b_rect)

        player["ch3_faction_badge_rects"][f_key] = b_rect
        bx += 82

    set_rect = pygame.Rect(716, 6, 36, 32)
    book_rect = pygame.Rect(756, 6, 36, 32)

    pygame.draw.rect(screen, DIAL_CREAM, set_rect, border_radius=5)
    pygame.draw.rect(screen, TATE_RED, set_rect, 2, border_radius=5)
    _draw_cog_icon(
        screen, set_rect.centerx, set_rect.centery, CLOCK_BLACK, DIAL_CREAM
    )

    pygame.draw.rect(screen, DIAL_CREAM, book_rect, border_radius=5)
    pygame.draw.rect(screen, TATE_RED, book_rect, 2, border_radius=5)
    draw_fitted_text(
        screen, "?", book_rect, CLOCK_BLACK, bold=True, max_lines=1
    )

    ui_rects["btn_settings"] = set_rect
    ui_rects["btn_rulebook"] = book_rect

    if hovered_faction_badge:
        hf_key, hf_spec, hf_pts, hf_keeps, hf_rect = hovered_faction_badge
        pop_w, pop_h = 274, 102
        pop_x = max(12, min(720 - pop_w, hf_rect.centerx - pop_w // 2))
        pop_rect = pygame.Rect(pop_x, 48, pop_w, pop_h)

        pygame.draw.rect(
            screen, (18, 14, 10), pop_rect.move(4, 5), border_radius=7
        )
        pygame.draw.rect(screen, DIAL_CREAM, pop_rect, border_radius=7)
        pygame.draw.rect(screen, hf_spec["color"], pop_rect, 3, border_radius=7)

        ped_r = pygame.Rect(pop_rect.left + 14, pop_rect.top + 64, 52, 20)
        pygame.draw.ellipse(screen, (52, 44, 38), ped_r)
        pygame.draw.ellipse(screen, GOLD_ACCENT, ped_r, 1)
        _draw_single_carved_meeple(
            screen, pop_rect.left + 40, pop_rect.top + 72, 1.35, hf_key
        )

        f_data = player.get("ch3_factions", {}).get(hf_key, {})
        leg = f_data.get("legacy_pts", 15)
        war = max(0, hf_pts - leg)
        goal_val = ch3_war_engine.get_victory_goal(player)
        goal_line = (
            f"Strongholds: {hf_keeps}/7 Keeps"
            if v_mode == "DOMINATION"
            else f"Hegemony: {hf_pts}/{goal_val} Pts (Keeps: {hf_keeps}/7)"
        )
        role_note = (
            "Your Faction"
            if hf_key == my_fac
            else "Click to set as diplomatic target"
        )

        draw_fitted_text(
            screen,
            hf_spec["title"],
            pygame.Rect(pop_rect.left + 76, pop_rect.top + 6, 188, 22),
            TATE_RED,
            bold=True,
            align="left",
            max_lines=1,
        )
        body_str = (
            f"{goal_line}\n"
            f"(Legacy: {leg} + War: {war})\n"
            f"Sympathy: {hf_spec['sympathy_type']}\n"
            f"{role_note}"
        )
        draw_fitted_text(
            screen,
            body_str,
            pygame.Rect(pop_rect.left + 76, pop_rect.top + 28, 188, 66),
            CLOCK_BLACK,
            align="left",
            max_lines=4,
        )


# =========================================================================
# 4. RIGHT-HAND CAMERA CONTROL RAIL (ZOOM, TILT & PAN ROSETTE)
# =========================================================================
def draw_camera_control_rail(screen, player, small_font):
    """
    Renders the Right-Hand Camera Control Strip (x = 736..800, y = 44..420).
    """
    ensure_board_camera(player)
    ui_rects = player.setdefault("ch3_board_ui_rects", {})

    pygame.draw.rect(screen, (40, 31, 25), CAMERA_RAIL_RECT)
    pygame.draw.line(
        screen, GOLD_ACCENT, (736, 44), (736, 420), 2
    )

    zoom = player.get("ch3_zoom", 44)
    tilt = player.get("ch3_tilt", 0.72)

    z_lbl = small_font.render("ZM", True, DIAL_CREAM)
    screen.blit(z_lbl, z_lbl.get_rect(center=(753, 56)))

    z_plus = pygame.Rect(742, 68, 22, 20)
    z_track = pygame.Rect(749, 92, 8, 148)
    z_minus = pygame.Rect(742, 244, 22, 20)

    for btn, txt in ((z_plus, "+"), (z_minus, "-")):
        pygame.draw.rect(screen, DIAL_CREAM, btn, border_radius=3)
        pygame.draw.rect(screen, CLOCK_BLACK, btn, 1, border_radius=3)
        s = small_font.render(txt, True, CLOCK_BLACK)
        screen.blit(s, s.get_rect(center=btn.center))

    pygame.draw.rect(screen, (22, 18, 15), z_track, border_radius=4)
    pygame.draw.rect(screen, GOLD_ACCENT, z_track, 1, border_radius=4)

    z_pct = (zoom - ZOOM_MIN) / float(ZOOM_MAX - ZOOM_MIN)
    z_knob_y = int(z_track.bottom - z_pct * z_track.height)
    z_knob = pygame.Rect(741, z_knob_y - 6, 24, 12)
    pygame.draw.rect(screen, TATE_RED, z_knob, border_radius=3)
    pygame.draw.rect(screen, GOLD_BRIGHT, z_knob, 1, border_radius=3)

    ui_rects["zoom_plus"] = z_plus
    ui_rects["zoom_minus"] = z_minus
    ui_rects["zoom_track"] = z_track

    t_lbl = small_font.render("3D", True, DIAL_CREAM)
    screen.blit(t_lbl, t_lbl.get_rect(center=(782, 56)))

    t_plus = pygame.Rect(771, 68, 22, 20)
    t_track = pygame.Rect(778, 92, 8, 148)
    t_minus = pygame.Rect(771, 244, 22, 20)

    for btn, txt in ((t_plus, "^"), (t_minus, "v")):
        pygame.draw.rect(screen, DIAL_CREAM, btn, border_radius=3)
        pygame.draw.rect(screen, CLOCK_BLACK, btn, 1, border_radius=3)
        s = small_font.render(txt, True, CLOCK_BLACK)
        screen.blit(s, s.get_rect(center=btn.center))

    pygame.draw.rect(screen, (22, 18, 15), t_track, border_radius=4)
    pygame.draw.rect(screen, GOLD_ACCENT, t_track, 1, border_radius=4)

    t_pct = (tilt - TILT_MIN) / float(TILT_MAX - TILT_MIN)
    t_knob_y = int(t_track.bottom - t_pct * t_track.height)
    t_knob = pygame.Rect(770, t_knob_y - 6, 24, 12)
    pygame.draw.rect(screen, (55, 105, 165), t_knob, border_radius=3)
    pygame.draw.rect(screen, GOLD_BRIGHT, t_knob, 1, border_radius=3)

    ui_rects["tilt_plus"] = t_plus
    ui_rects["tilt_minus"] = t_minus
    ui_rects["tilt_track"] = t_track

    pan_lbl = small_font.render("PAN", True, GOLD_ACCENT)
    screen.blit(pan_lbl, pan_lbl.get_rect(center=(768, 280)))

    pan_n = pygame.Rect(758, 292, 20, 20)
    pan_w = pygame.Rect(739, 314, 19, 20)
    pan_c = pygame.Rect(758, 314, 20, 20)
    pan_e = pygame.Rect(778, 314, 19, 20)
    pan_s = pygame.Rect(758, 336, 20, 20)

    pan_buttons = [
        ("pan_n", pan_n, "N", DIAL_CREAM),
        ("pan_w", pan_w, "W", DIAL_CREAM),
        ("pan_centre", pan_c, "*", GOLD_BRIGHT),
        ("pan_e", pan_e, "E", DIAL_CREAM),
        ("pan_s", pan_s, "S", DIAL_CREAM),
    ]
    for key, r_p, ch, fill_c in pan_buttons:
        pygame.draw.rect(screen, fill_c, r_p, border_radius=3)
        pygame.draw.rect(screen, CLOCK_BLACK, r_p, 1, border_radius=3)
        s = small_font.render(ch, True, CLOCK_BLACK)
        screen.blit(s, s.get_rect(center=r_p.center))
        ui_rects[key] = r_p

    lod_txt = "Meeple" if zoom >= LOD_MEEPLE_THRESHOLD else "Disc"
    info_s = small_font.render(lod_txt, True, (185, 175, 155))
    screen.blit(info_s, info_s.get_rect(center=(768, 374)))


# =========================================================================
# 5. MAIN 3D TILTED GAME BOARD VIEWPORT & SEASONAL PALETTE RENDERER
# =========================================================================
def _get_season_from_month(month_name):
    """Maps the 12 French Republican months to ('AUTUMN'|'WINTER'|'SPRING'|'SUMMER')."""
    m = str(month_name).lower()
    if any(w in m for w in ("niv", "pluv", "vent")):
        return "WINTER"
    if any(w in m for w in ("germ", "flor", "prair")):
        return "SPRING"
    if any(w in m for w in ("mess", "therm", "fruct")):
        return "SUMMER"
    return "AUTUMN"


def _get_tile_terrain_palette(loc, month_idx=1):
    """
    Returns (top_rgb, cliff_rgb, kind_tag) for a board tile, tinted by
    the active French Republican Calendar season:
    - Autumn (0..2: Vendémiaire, Brumaire, Frimaire)
    - Winter (3..5: Nivôse, Pluviôse, Ventôse)
    - Spring (6..8: Germinal, Floréal, Prairial)
    - Summer (9..11: Messidor, Thermidor, Fructidor)
    """
    reg_low = loc.region.lower()
    name_low = loc.name.lower()
    season = (int(month_idx) % 12) // 3  # 0=Aut, 1=Win, 2=Spr, 3=Sum

    if "town wall" in name_low or "town wall" in reg_low:
        return (108, 102, 96), (68, 64, 60), "wall"
    if "castle" in name_low or "castle" in reg_low:
        return (196, 158, 148), (132, 98, 90), "castle"
    if "river" in name_low or "river" in reg_low:
        return (112, 168, 204), (75, 120, 150), "river"
    if "lake" in name_low or "sea" in reg_low or "lake" in reg_low:
        if season == 1:
            return (175, 205, 225), (110, 140, 165), "water"
        return (88, 142, 182), (58, 98, 130), "water"
    if "forest" in reg_low or "glade" in reg_low:
        if season == 0:
            return (168, 142, 88), (112, 92, 54), "forest"
        if season == 1:
            return (162, 182, 178), (98, 118, 114), "forest"
        if season == 2:
            return (118, 184, 108), (78, 128, 68), "forest"
        return (138, 172, 114), (88, 118, 72), "forest"
    if "mountain" in reg_low:
        if season == 1:
            return (222, 226, 232), (145, 152, 162), "mountain"
        return (172, 162, 148), (112, 104, 94), "mountain"
    if "road" in reg_low or "path" in reg_low:
        return (226, 210, 174), (162, 146, 114), "road"
    if "town" in reg_low or "parvus" in reg_low:
        return (232, 204, 170), (168, 140, 110), "town"
    if "farm" in reg_low:
        if season == 1:
            return (212, 214, 218), (148, 150, 155), "farm"
        if season == 3:
            return (238, 208, 118), (175, 148, 78), "farm"
        return (226, 212, 142), (165, 150, 95), "farm"

    if season == 1:
        return (208, 216, 218), (142, 150, 154), "plains"
    if season == 2:
        return (176, 216, 148), (124, 156, 98), "plains"
    if season == 3:
        return (212, 204, 138), (152, 144, 92), "plains"
    return (192, 208, 154), (135, 148, 102), "plains"


def _draw_active_ai_turn_overlay(screen, player, tile_centres, zoom):
    """
    Draws the Gold Trajectory Arrow, Sliding Wooden AI Meeple, and
    Muster Badge on the 3D board for the currently active AI Turn step.
    """
    ai_queue = player.get("ch3_ai_turn_queue", [])
    if not ai_queue or not player.get("ch3_show_ai_moves", True):
        return

    ev = ai_queue[0]
    fac = ev.get("faction", "Laydere")
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        fac, ch3_war_engine.DTESSERA_FACTIONS["Laydere"]
    )
    now = pygame.time.get_ticks()
    start_t = ev.get("anim_start", now)
    t = max(0.0, min(1.0, (now - start_t) / 700.0))
    ease = 1.0 - (1.0 - t) ** 3

    cap_key = ev.get("capital")
    m_gain = ev.get("muster_gain", 0)
    if cap_key in tile_centres and m_gain > 0:
        cx, cy = tile_centres[cap_key]
        b_rect = pygame.Rect(cx - 26, cy - int(zoom * 0.65), 52, 18)
        pygame.draw.rect(screen, spec["color"], b_rect, border_radius=4)
        pygame.draw.rect(screen, GOLD_BRIGHT, b_rect, 1, border_radius=4)
        draw_fitted_text(
            screen,
            f"+{m_gain} Bns",
            b_rect,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )

    from_k = ev.get("from_pos")
    to_k = ev.get("to_pos")
    if (
        from_k
        and to_k
        and from_k != to_k
        and from_k in tile_centres
        and to_k in tile_centres
    ):
        fx, fy = tile_centres[from_k]
        tx, ty = tile_centres[to_k]

        pygame.draw.line(screen, CLOCK_BLACK, (fx, fy + 2), (tx, ty + 2), 6)
        pygame.draw.line(screen, GOLD_BRIGHT, (fx, fy), (tx, ty), 4)
        ang = math.atan2(ty - fy, tx - fx)
        ah_1 = (
            tx - int(math.cos(ang - 0.5) * 12),
            ty - int(math.sin(ang - 0.5) * 12),
        )
        ah_2 = (
            tx - int(math.cos(ang + 0.5) * 12),
            ty - int(math.sin(ang + 0.5) * 12),
        )
        pygame.draw.polygon(screen, GOLD_BRIGHT, [(tx, ty), ah_1, ah_2])

        cur_x = int(fx + ease * (tx - fx))
        cur_y = int(fy + ease * (ty - fy) - math.sin(ease * math.pi) * 14)
        _draw_single_carved_meeple(
            screen, cur_x, cur_y, max(0.8, zoom / 44.0), fac
        )


def draw_3d_tabletop_board(
    screen,
    player,
    world_map,
    small_font,
    mouse_pos,
    selected_army_pos=None,
    active_phase="AFTERNOON",
):
    """
    Renders the 3D Tilted Game Board inside `MAP_VIEWPORT_RECT` (y = 44..420),
    updates `player['ch3_hovered_pos']` with 100% mouse-to-tile accuracy,
    and draws all Faction Meeples, Strongholds, Pinned Crossed-Swords ('⚔')
    Clashes, and Valid Move Border Highlights.
    """
    ensure_board_camera(player)
    zoom = player.get("ch3_zoom", 44)
    tilt = player.get("ch3_tilt", 0.72)
    cam_x = player.get("ch3_cam_x", 0)
    cam_y = player.get("ch3_cam_y", 0)
    season = _get_season_from_month(player.get("current_month", "Brumaire"))

    tile_w = int(zoom)
    tile_h = max(12, int(zoom * tilt))

    screen.set_clip(MAP_VIEWPORT_RECT)

    pygame.draw.rect(screen, WALNUT_DARK, MAP_VIEWPORT_RECT)
    for gy in range(MAP_VIEWPORT_RECT.top, MAP_VIEWPORT_RECT.bottom, 14):
        pygame.draw.line(
            screen, WALNUT_GRAIN, (0, gy), (MAP_VIEWPORT_RECT.right, gy), 2
        )

    origin_x = MAP_VIEWPORT_RECT.left - cam_x
    origin_y = MAP_VIEWPORT_RECT.top - cam_y
    board_w = 20 * tile_w
    board_h = 25 * tile_h
    lip_h = max(6, int(18 * (1.15 - tilt)))

    board_rect = pygame.Rect(origin_x, origin_y, board_w, board_h)
    frame_rect = board_rect.inflate(16, 16)

    shadow_rect = frame_rect.move(10, lip_h + 8)
    pygame.draw.rect(screen, (16, 12, 9), shadow_rect, border_radius=8)

    lip_rect = pygame.Rect(
        frame_rect.left, frame_rect.bottom - 4, frame_rect.width, lip_h + 4
    )
    pygame.draw.rect(screen, BOARD_EDGE_DARK, lip_rect, border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, lip_rect, 2, border_radius=4)

    pygame.draw.rect(screen, BOARD_EDGE_LIGHT, frame_rect, border_radius=6)
    pygame.draw.rect(screen, TATE_RED, frame_rect, 3, border_radius=6)
    pygame.draw.rect(screen, PARCHMENT_BASE, board_rect)

    my_fac = player.get("ch3_faction", "Union")
    my_mp = player.get("movement_points", 0)
    territories = player.get("territories", {})
    barricades = player.get("ch3_barricades", {})
    armies = player.get("ch3_armies", {})
    pending_clashes = {
        c["tile_pos"]: c for c in player.get("ch3_pending_clashes", [])
    }

    valid_dest_info = {}
    if (
        active_phase == "AFTERNOON"
        and selected_army_pos
        and selected_army_pos in armies
        and not player.get("ch3_ai_turn_queue")
    ):
        avail_cnt = armies[selected_army_pos].get("count", 1)
        split_cnt = max(
            1, min(avail_cnt, player.get("ch3_split_count", avail_cnt))
        )
        try:
            sx_grid, sy_grid = map(int, selected_army_pos.split(","))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = sx_grid + dx, sy_grid + dy
                    if (nx, ny) in world_map:
                        n_key = f"{nx},{ny}"
                        cost, can_pass, _ = (
                            ch3_war_engine.calculate_ch3_movement_cost(
                                player,
                                my_fac,
                                n_key,
                                world_map,
                                troop_count=split_cnt,
                            )
                        )
                        if can_pass:
                            has_enemy = (
                                n_key in armies
                                and armies[n_key]["faction"] != my_fac
                            ) or (n_key in pending_clashes)
                            valid_dest_info[n_key] = (cost, has_enemy)
        except ValueError:
            pass

    player["ch3_hovered_pos"] = None
    player["ch3_hovered_details"] = None
    player["ch3_hovered_move_cost"] = None
    in_viewport = MAP_VIEWPORT_RECT.collidepoint(mouse_pos)
    tile_centres = {}

    for map_y in range(25, 0, -1):
        row_idx = 25 - map_y
        for map_x in range(1, 21):
            loc = world_map.get((map_x, map_y))
            if not loc:
                continue

            sx = origin_x + (map_x - 1) * tile_w
            sy = origin_y + row_idx * tile_h
            pos_key = f"{map_x},{map_y}"

            alt, _, _ = weather_engine.get_tile_altitude_and_temp(
                player, (map_x, map_y), world_map
            )
            lift = int(max(0, alt - 1) * (zoom * 0.11) * (1.0 - tilt))
            tile_rect = pygame.Rect(sx, sy - lift, tile_w, tile_h)
            tile_centres[pos_key] = tile_rect.center

            if (
                sx + tile_w < MAP_VIEWPORT_RECT.left
                or sx > MAP_VIEWPORT_RECT.right
                or sy + tile_h < MAP_VIEWPORT_RECT.top - 30
                or sy - 30 > MAP_VIEWPORT_RECT.bottom
            ):
                continue

            top_col, cliff_col, kind = _get_tile_terrain_palette(loc, player.get("current_month_idx", 1))
            owner = territories.get(pos_key)

            if owner in ch3_war_engine.DTESSERA_FACTIONS:
                fc = ch3_war_engine.DTESSERA_FACTIONS[owner]["color"]
                top_col = (
                    int(top_col[0] * 0.75 + fc[0] * 0.25),
                    int(top_col[1] * 0.75 + fc[1] * 0.25),
                    int(top_col[2] * 0.75 + fc[2] * 0.25),
                )

            if lift > 2:
                cliff_rect = pygame.Rect(
                    sx, tile_rect.bottom, tile_w, lift + 1
                )
                pygame.draw.rect(screen, cliff_col, cliff_rect)
                pygame.draw.rect(screen, (70, 62, 54), cliff_rect, 1)

            pygame.draw.rect(screen, top_col, tile_rect)
            pygame.draw.rect(screen, (150, 140, 122), tile_rect, 1)

            if owner in ch3_war_engine.DTESSERA_FACTIONS:
                f_col = ch3_war_engine.DTESSERA_FACTIONS[owner]["color"]
                pygame.draw.rect(
                    screen, f_col, tile_rect.inflate(-2, -2), 2
                )

            cx, cy = tile_rect.centerx, tile_rect.centery
            if zoom >= 30:
                if kind == "forest":
                    tree_col = (
                        (210, 222, 228)
                        if season == "WINTER"
                        else ((82, 122, 68) if season != "AUTUMN" else (142, 108, 52))
                    )
                    pygame.draw.circle(
                        screen,
                        tree_col,
                        (cx - tile_w // 4, cy),
                        max(3, tile_w // 8),
                    )
                    pygame.draw.circle(
                        screen,
                        tree_col,
                        (cx + tile_w // 4, cy - 2),
                        max(3, tile_w // 8),
                    )
                elif kind == "mountain":
                    m_pts = [
                        (cx - tile_w // 3, cy + tile_h // 4),
                        (cx, cy - tile_h // 3),
                        (cx + tile_w // 3, cy + tile_h // 4),
                    ]
                    pygame.draw.lines(screen, (80, 72, 65), False, m_pts, 2)

            if pos_key in ch3_combat_engine.MAJOR_STRONGHOLDS and zoom >= 28:
                keep_rect = pygame.Rect(
                    tile_rect.left + 3, tile_rect.top + 3, 12, 10
                )
                pygame.draw.rect(screen, GOLD_ACCENT, keep_rect)
                pygame.draw.rect(screen, CLOCK_BLACK, keep_rect, 1)

            if barricades.get(pos_key) and zoom >= 26:
                bar_rect = pygame.Rect(
                    tile_rect.left + 4,
                    tile_rect.bottom - 9,
                    tile_w - 8,
                    6,
                )
                pygame.draw.rect(
                    screen, TATE_RED, bar_rect, border_radius=2
                )
                pygame.draw.rect(
                    screen, DIAL_CREAM, bar_rect, 1, border_radius=2
                )

            if pos_key in valid_dest_info:
                mp_cost, is_clash = valid_dest_info[pos_key]
                hl_col = (
                    CLASH_CRIMSON
                    if is_clash
                    else (VALID_GREEN if my_mp >= mp_cost else MIRE_AMBER)
                )
                pygame.draw.rect(
                    screen, hl_col, tile_rect.inflate(-4, -4), 3
                )

            if in_viewport and tile_rect.collidepoint(mouse_pos):
                player["ch3_hovered_pos"] = pos_key
                player["ch3_hovered_details"] = (
                    loc,
                    owner,
                    armies.get(pos_key),
                    barricades.get(pos_key, False),
                )
                if pos_key in valid_dest_info:
                    player["ch3_hovered_move_cost"] = valid_dest_info[
                        pos_key
                    ][0]
                pygame.draw.rect(screen, GOLD_BRIGHT, tile_rect, 3)

            if pos_key in pending_clashes:
                clash_data = pending_clashes[pos_key]
                att_a = clash_data["attacker"]
                def_a = clash_data["defender"]
                off_x = max(8, tile_w // 4)
                _draw_army_on_tile(
                    screen,
                    cx - off_x,
                    cy + 2,
                    max(24, int(zoom * 0.75)),
                    att_a,
                    (att_a["faction"] == my_fac),
                    False,
                    False,
                    small_font,
                )
                _draw_army_on_tile(
                    screen,
                    cx + off_x,
                    cy + 2,
                    max(24, int(zoom * 0.75)),
                    def_a,
                    (def_a["faction"] == my_fac),
                    False,
                    False,
                    small_font,
                )
                _draw_crossed_swords_token(screen, cx, cy - tile_h // 4, zoom)
            else:
                army_here = armies.get(pos_key)
                if army_here and army_here.get("count", 0) > 0:
                    is_mine = army_here.get("faction") in (my_fac, "Player")
                    _draw_army_on_tile(
                        screen,
                        cx,
                        cy,
                        zoom,
                        army_here,
                        is_mine,
                        (selected_army_pos == pos_key),
                        (active_phase == "AFTERNOON" and my_mp >= 4),
                        small_font,
                    )

    _draw_active_ai_turn_overlay(screen, player, tile_centres, zoom)

    screen.set_clip(None)
    draw_camera_control_rail(screen, player, small_font)
