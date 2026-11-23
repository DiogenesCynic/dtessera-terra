"""
wide_layout.py
--------------
Adaptive 1200x600 (2:1) "Thumb-Friendly Wings" layout manager for Android & wide mobile screens.
- Exploration (`MAIN`) uses all 1200x600 pixels:
    * Left Wing  (x: 8..216)   : Retro D-Pad + Decimal Clock (left thumb)
    * Centre     (x: 225..975) : Weather Pill, Location Panel & double-height Log Panel
    * Right Wing (x: 984..1192): 2x2 HUD Circle Buttons + stacked context buttons (right thumb)
- All other states (Title, Intro, Maps, Popups, Mini-Games, Casino, Chapter 3) render
  their existing 800x600 stage cleanly centered at x=200..1000 with zero hitbox rewrites.
"""

import os
import sys
import pygame

STD_W, STD_H = 800, 600
WIDE_W, WIDE_H = 1200, 600
STAGE_OFFSET_X = (WIDE_W - STD_W) // 2  # 200px left/right margins for centered 800x600 states

# Add any other pure-exploration HUD menu_state names here later if desired
WIDE_HUD_STATES = {"MAIN"}

TATE_RED = (168, 50, 35)
WING_BORDER = (115, 42, 32)


def detect_wide_mode():
    """
    Returns True when running on Android APK (?wide=1), a wide mobile browser
    (aspect ratio >= 1.65), or locally with DTESSERA_WIDE=1 for desktop testing.
    """
    if os.environ.get("DTESSERA_WIDE") == "1":
        return True

    if sys.platform == "emscripten":
        try:
            import platform
            win = platform.window
            search = str(getattr(win.location, "search", "") or "")
            if "wide=1" in search:
                return True
            w = float(getattr(win, "innerWidth", 0) or 0)
            h = float(getattr(win, "innerHeight", 0) or 0)
            if w > 0 and h > 0 and (w / h) >= 1.65:
                return True
        except Exception:
            pass

    return False


class WideLayoutManager:
    """Manages 1200x600 wide surfaces, widget repositioning, touch scrolling, and presentation."""

    def __init__(self, enabled=None):
        self.enabled = detect_wide_mode() if enabled is None else bool(enabled)
        self.display_size = (WIDE_W, WIDE_H) if self.enabled else (STD_W, STD_H)
        self.stage_800 = pygame.Surface((STD_W, STD_H))
        self.wide_1200 = pygame.Surface((WIDE_W, WIDE_H)) if self.enabled else None

        self._orig = {}
        self._last_mode_wide = None

        # Single-finger swipe-to-scroll state for Android text panels
        self._drag_panel = None
        self._drag_last_y = 0

    def is_wide_state(self, menu_state):
        return self.enabled and (menu_state in WIDE_HUD_STATES)

    def get_active_surface(self, menu_state):
        """Returns the 1200x600 surface during wide exploration, or the 800x600 stage otherwise."""
        if self.is_wide_state(menu_state):
            return self.wide_1200
        return self.stage_800

    def to_logical_pos(self, pos, menu_state, is_fullscreen=False, fs_scale=1.0, fs_offset_x=0, fs_offset_y=0):
        """Translates display mouse/touch coordinates into active surface coordinates."""
        if self.enabled:
            if self.is_wide_state(menu_state):
                return (int(pos[0]), int(pos[1]))
            return (int(pos[0] - STAGE_OFFSET_X), int(pos[1]))

        if not is_fullscreen:
            return (int(pos[0]), int(pos[1]))
        lx = int((pos[0] - fs_offset_x) / fs_scale) if fs_scale else int(pos[0])
        ly = int((pos[1] - fs_offset_y) / fs_scale) if fs_scale else int(pos[1])
        return (lx, ly)

    def _snapshot_originals(self, location_panel, log_panel, dpad, clock_ui, circle_buttons, weather_pill_rect):
        if self._orig:
            return
        self._orig["loc_rect"] = pygame.Rect(location_panel.rect)
        self._orig["log_rect"] = pygame.Rect(log_panel.rect)
        if dpad is not None:
            self._orig["dpad"] = (dpad.center_x, dpad.center_y, dpad.radius)
        if clock_ui is not None:
            self._orig["clock"] = (clock_ui.center_x, clock_ui.center_y, pygame.Rect(clock_ui.rect))
        if circle_buttons:
            self._orig["circles"] = [(b.x, b.y, b.radius, pygame.Rect(b.rect)) for b in circle_buttons]
        if weather_pill_rect is not None:
            self._orig["weather_pill"] = pygame.Rect(weather_pill_rect)

    def apply_hud_layout(
        self,
        menu_state,
        location_panel,
        log_panel,
        dpad=None,
        clock_ui=None,
        circle_buttons=None,
        weather_pill_rect=None,
        current_buttons=None,
    ):
        """Repositions HUD panels and thumb widgets for 1200x600 wide exploration, or restores 800x600."""
        if not self.enabled:
            return

        self._snapshot_originals(location_panel, log_panel, dpad, clock_ui, circle_buttons, weather_pill_rect)
        wide_now = self.is_wide_state(menu_state)

        if wide_now:
            # Centre reading column: wider & double-height log panel
            location_panel.rect = pygame.Rect(225, 28, 750, 134)
            log_panel.rect = pygame.Rect(225, 172, 750, 412)

            if weather_pill_rect is not None:
                weather_pill_rect.update(225, 3, 750, 20)

            # Left Wing: generous thumb-sized D-Pad above Decimal Clock
            if dpad is not None:
                dpad.center_x, dpad.center_y, dpad.radius = 112, 210, 86

            if clock_ui is not None:
                clock_ui.center_x, clock_ui.center_y = 112, 468
                clock_ui.rect = pygame.Rect(112 - 96, 468 - 70, 192, 140)

            # Right Wing Top: 2x2 grid for the 4 HUD CircleButtons
            if circle_buttons:
                grid_pos = [(1042, 86), (1138, 86), (1042, 178), (1138, 178)]
                for idx, btn in enumerate(circle_buttons):
                    cx, cy = grid_pos[idx] if idx < len(grid_pos) else (1090, 86 + idx * 80)
                    btn.x, btn.y = cx, cy
                    btn.rect = pygame.Rect(cx - btn.radius, cy - btn.radius, btn.radius * 2, btn.radius * 2)

            # Right Wing Bottom: stack all visible MAIN context buttons into thumb-friendly bars
            if current_buttons:
                visible = [b for b in current_buttons if not getattr(b, "invisible", False)]
                if visible:
                    avail_top = 238
                    avail_h = 584 - avail_top
                    count = len(visible)
                    step = min(50, max(32, avail_h // count))
                    btn_h = max(26, step - 8)
                    for i, b in enumerate(visible):
                        b.rect = pygame.Rect(994, avail_top + i * step, 192, btn_h)

        elif self._last_mode_wide is not False:
            # Restore original 800x600 coordinates whenever entering a centered stage screen
            location_panel.rect = pygame.Rect(self._orig["loc_rect"])
            log_panel.rect = pygame.Rect(self._orig["log_rect"])
            if weather_pill_rect is not None and "weather_pill" in self._orig:
                r = self._orig["weather_pill"]
                weather_pill_rect.update(r.x, r.y, r.w, r.h)
            if dpad is not None and "dpad" in self._orig:
                dpad.center_x, dpad.center_y, dpad.radius = self._orig["dpad"]
            if clock_ui is not None and "clock" in self._orig:
                cx, cy, cr = self._orig["clock"]
                clock_ui.center_x, clock_ui.center_y = cx, cy
                clock_ui.rect = pygame.Rect(cr)
            if circle_buttons and "circles" in self._orig:
                for btn, (bx, by, br, brect) in zip(circle_buttons, self._orig["circles"]):
                    btn.x, btn.y, btn.radius = bx, by, br
                    btn.rect = pygame.Rect(brect)

        self._last_mode_wide = wide_now

    def draw_wide_backdrop(self, target_wide, backdrop_draw_fn, *args, **kwargs):
        """
        Renders your existing 800x600 procedural woodcut backdrop onto stage_800,
        smooth-scales it across the full 1200x600 frame, and draws subtle thumb-wing frames.
        """
        backdrop_draw_fn(self.stage_800, *args, **kwargs)
        scaled = pygame.transform.smoothscale(self.stage_800, (WIDE_W, WIDE_H))
        target_wide.blit(scaled, (0, 0))
        self.draw_wing_chrome(target_wide)

    def draw_wing_chrome(self, target_wide):
        """Adds translucent charcoal-and-crimson folio wings behind Left & Right thumb controls."""
        wing_surf = pygame.Surface((208, 580), pygame.SRCALPHA)
        wing_surf.fill((18, 16, 15, 135))
        for wx in (8, 984):
            target_wide.blit(wing_surf, (wx, 10))
            pygame.draw.rect(target_wide, WING_BORDER, (wx, 10, 208, 580), 2, border_radius=10)

    def handle_touch_scroll(self, event, menu_state, location_panel, log_panel):
        """Allows 1-finger vertical swipe scrolling inside Location and Log panels on mobile."""
        if not self.is_wide_state(menu_state):
            self._drag_panel = None
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for panel in (log_panel, location_panel):
                if panel.rect.collidepoint(event.pos):
                    self._drag_panel = panel
                    self._drag_last_y = event.pos[1]
                    return False  # Do not block taps on links/buttons
        elif event.type == pygame.MOUSEMOTION and self._drag_panel is not None:
            dy = event.pos[1] - self._drag_last_y
            self._drag_last_y = event.pos[1]
            if dy != 0:
                self._drag_panel.scroll_y += dy
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._drag_panel = None

        return False

    def present(
        self,
        display_screen,
        active_surface,
        menu_state,
        is_fullscreen=False,
        fs_scale=1.0,
        fs_offset_x=0,
        fs_offset_y=0,
    ):
        """Presents either the full 1200x600 exploration HUD or the centered 800x600 stage."""
        if self.enabled:
            if self.is_wide_state(menu_state):
                display_screen.blit(active_surface, (0, 0))
            else:
                display_screen.fill((16, 15, 14))
                # Subtle crimson book-folio rails framing the centered 800x600 stage
                pygame.draw.line(display_screen, TATE_RED, (STAGE_OFFSET_X - 2, 0), (STAGE_OFFSET_X - 2, WIDE_H), 3)
                pygame.draw.line(display_screen, TATE_RED, (STAGE_OFFSET_X + STD_W + 1, 0), (STAGE_OFFSET_X + STD_W + 1, WIDE_H), 3)
                display_screen.blit(active_surface, (STAGE_OFFSET_X, 0))
        else:
            if not is_fullscreen:
                display_screen.blit(active_surface, (0, 0))
            else:
                display_screen.fill((12, 14, 18))
                scaled_w = int(STD_W * fs_scale)
                scaled_h = int(STD_H * fs_scale)
                scaled_surf = pygame.transform.smoothscale(active_surface, (scaled_w, scaled_h))
                display_screen.blit(scaled_surf, (fs_offset_x, fs_offset_y))

        pygame.display.flip()
