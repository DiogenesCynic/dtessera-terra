"""
ui_components.py
----------------
Reusable Pygame UI widgets and layout helpers for Dtessera Terra (Tate Britain aesthetic):
- Text wrapping and auto-fitting helpers (`draw_wrapped_text`, `draw_fitted_text`, `draw_wrapped_banner`)
- Scrollable location and event log panels (`TextPanelUI`)
- Auto-fitting rectangular and circular buttons (`Button`, `CircleButton`)
- 8-way compass D-Pad with Lignum Forest disorientation spin (`RetroDPad`)
- 1,000-minute Revolutionary Decimal Clock widget (`DecimalClockUI`)
- Interactive regional Cartographic Map viewer (`draw_cartographic_map`)
- Title Screen & Chapter 1 Intro cards (`draw_title_or_intro_card`)
"""

import math
import random
import pygame
from map_data import the_river_fluvius_locations

# --- SHARED THEME & PALETTE CONSTANTS ---
BTN_BG = (45, 55, 72)
BTN_HOVER = (66, 84, 112)
TEXT_COLOR = (240, 240, 240)
TEXT_MUTED = (160, 174, 192)
PANEL_BORDER = (55, 65, 81)

TATE_RED = (168, 50, 35)
DIAL_CREAM = (244, 239, 225)
DIAL_CREAM_HOVER = (220, 215, 200)
CLOCK_BLACK = (28, 28, 28)
ACCENT_CRIMSON = (120, 30, 20)

DISABLED_RED = (100, 40, 30)
DISABLED_CREAM = (180, 175, 160)
DISABLED_BLACK = (100, 100, 100)

FACTION_COLORS = {
    "Guard":        (55, 105, 195),   # Watch Blue
    "Union":        (190, 45, 45),    # Syndicate Crimson
    "Wallmakers":   (135, 65, 170),   # Guild Purple
    "Vanguardists": (40, 125, 70),    # Militant Forest Green
    "Communards":   (205, 130, 40),   # Commune Autumn Gold
}

# Initialize cached fonts so buttons and panels can auto-fit labels without lag
pygame.init()
FONT = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 16)
FONT_SM = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 12)
FONT_MD = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 14)
FONT_XS = pygame.font.SysFont("georgia,garamond,dejavuserif,arial", 11)


# =========================================================================
# 1. TEXT RENDERING & AUTO-FITTING HELPERS
# =========================================================================
def draw_wrapped_text(surface, text, font, color, rect, y_offset=0, char_limit=None):
    """
    Wraps `text` across multiple lines within `rect` (respecting explicit '\\n' breaks)
    and renders up to `char_limit` characters for the typewriter effect.
    Returns the total vertical height consumed by the wrapped lines.
    """
    x = rect.left + 15
    y = rect.top + 15 + y_offset
    max_width = rect.width - 30

    paragraphs = str(text).split("\n")
    lines = []

    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(" ")
        current_line = []
        for word in words:
            current_line.append(word)
            fw, _ = font.size(" ".join(current_line))
            if fw > max_width:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

    chars_drawn = 0
    line_step = font.get_linesize() + 4

    for line in lines:
        if char_limit is not None and chars_drawn >= char_limit:
            break

        text_to_render = line
        if char_limit is not None:
            remaining = int(char_limit) - chars_drawn
            if remaining < len(line):
                text_to_render = line[:remaining]

        if text_to_render:
            line_surf = font.render(text_to_render, True, color)
            surface.blit(line_surf, (x, y))

        y += line_step
        chars_drawn += len(line) + 1

    return len(lines) * line_step


def draw_fitted_text(surface, text, rect, color, bold=False, align="center", max_lines=2):
    """
    Guarantees that `text` fits cleanly inside `rect` (pygame.Rect or 4-tuple)
    by stepping down font sizes, respecting explicit '\\n' line breaks, and
    wrapping cleanly up to `max_lines` (1, 2, 3, 4, 5+ lines!).
    """
    r = pygame.Rect(rect)
    text_str = str(text).strip()
    if not text_str:
        return

    max_w = max(10, r.width - 8)
    candidate_fonts = (FONT, FONT_MD, FONT_SM, FONT_XS) if bold else (FONT_MD, FONT_SM, FONT_XS)

    # 1. Fast path: If no newline and max_lines == 1 (or fits on 1 line), try single-line fit
    if "\n" not in text_str:
        for f in candidate_fonts:
            if f.size(text_str)[0] <= max_w:
                surf = f.render(text_str, True, color)
                if align == "left":
                    pos = (r.left + 4, r.centery - surf.get_height() // 2)
                elif align == "right":
                    pos = (r.right - surf.get_width() - 4, r.centery - surf.get_height() // 2)
                else:
                    pos = (r.centerx - surf.get_width() // 2, r.centery - surf.get_height() // 2)
                surface.blit(surf, pos)
                return

    # 2. Multi-line word-wrapping (supports any max_lines >= 2 AND explicit '\n' paragraphs!)
    paragraphs = text_str.split("\n")
    chosen_font = FONT_XS
    final_lines = []

    for f in candidate_fonts:
        wrapped = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            words = para.split(" ")
            cur_line = words[0]
            for w in words[1:]:
                test = f"{cur_line} {w}"
                if f.size(test)[0] <= max_w:
                    cur_line = test
                else:
                    wrapped.append(cur_line)
                    cur_line = w
            wrapped.append(cur_line)

        lh = f.get_linesize() - 1
        total_h = len(wrapped) * lh
        if len(wrapped) <= max_lines and total_h <= (r.height + 6):
            chosen_font = f
            final_lines = wrapped
            break
        # Keep the smallest font's wrap as fallback
        chosen_font = f
        final_lines = wrapped

    # 3. Render the wrapped lines strictly clipped inside `r`
    surface.set_clip(r)
    final_lines = final_lines[:max_lines]
    lh = chosen_font.get_linesize() - 1
    total_h = len(final_lines) * lh
    start_y = r.top + max(1, (r.height - total_h) // 2)

    for idx, line_s in enumerate(final_lines):
        # If the last allowed line is still slightly wider than max_w, trim cleanly with '...'
        if idx == len(final_lines) - 1 and chosen_font.size(line_s)[0] > max_w:
            while len(line_s) > 3 and chosen_font.size(line_s + "...")[0] > max_w:
                line_s = line_s[:-1]
            line_s = line_s.rstrip() + "..."

        s = chosen_font.render(line_s, True, color)
        if align == "left":
            x_pos = r.left + 4
        elif align == "right":
            x_pos = r.right - s.get_width() - 4
        else:
            x_pos = r.centerx - s.get_width() // 2
        surface.blit(s, (x_pos, start_y + idx * lh))

    surface.set_clip(None)


def draw_wrapped_banner(surface, header_text, body_text, rect, header_color, body_color):
    """Draws a header and auto-wrapped/auto-sized body text strictly clipped inside `rect`."""
    r = pygame.Rect(rect)
    surface.set_clip(r)

    h_surf = FONT_MD.render(str(header_text), True, header_color)
    surface.blit(h_surf, (r.left + 12, r.top + 5))

    body_str = str(body_text)
    max_w = r.width - 24
    if FONT_MD.size(body_str)[0] <= max_w:
        b_surf = FONT_MD.render(body_str, True, body_color)
        surface.blit(b_surf, (r.left + 12, r.top + 25))
    else:
        words = body_str.split(" ")
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if FONT_SM.size(" ".join(cur))[0] > max_w:
                cur.pop()
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        for idx, ln in enumerate(lines[:2]):
            b_surf = FONT_SM.render(ln, True, body_color)
            surface.blit(b_surf, (r.left + 12, r.top + 22 + idx * 14))

    surface.set_clip(None)


# =========================================================================
# 2. THE TEXT PANEL UI (Tate Britain Style)
# =========================================================================
class TextPanelUI:
    """Scrollable cream-and-crimson text panel for location descriptions and game logs."""

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.scroll_y = 0
        self.title_font = pygame.font.Font(None, 28)

    def draw_location_panel(self, screen, loc_name, loc_desc, typewriter_idx, territory_owner=None):
        """Renders the upper location panel with an optional Faction Territory badge."""
        outer_rect = self.rect.inflate(4, 4)
        pygame.draw.rect(screen, TATE_RED, outer_rect, border_radius=8)
        pygame.draw.rect(screen, DIAL_CREAM, self.rect, border_radius=6)
        pygame.draw.rect(screen, CLOCK_BLACK, self.rect, width=1, border_radius=6)

        title_surf = self.title_font.render(loc_name, True, ACCENT_CRIMSON)
        screen.blit(title_surf, (self.rect.left + 15, self.rect.top + 10))

        if territory_owner:
            pill_col = FACTION_COLORS.get(territory_owner, TATE_RED)
            badge_txt = f"{territory_owner.upper()} TERRITORY"
            b_surf = FONT_SM.render(badge_txt, True, (250, 248, 242))
            pw, ph = b_surf.get_width() + 18, 22
            pill_rect = pygame.Rect(self.rect.right - pw - 14, self.rect.top + 9, pw, ph)
            pygame.draw.rect(screen, pill_col, pill_rect, border_radius=6)
            pygame.draw.rect(screen, CLOCK_BLACK, pill_rect, width=1, border_radius=6)
            screen.blit(b_surf, b_surf.get_rect(center=pill_rect.center))

        text_rect = pygame.Rect(self.rect.left, self.rect.top + 40, self.rect.width, self.rect.height - 40)
        screen.set_clip(text_rect)

        total_height = draw_wrapped_text(
            screen, loc_desc, FONT, CLOCK_BLACK, text_rect,
            y_offset=self.scroll_y - 15, char_limit=typewriter_idx
        )
        screen.set_clip(None)

        max_scroll_up = 0
        max_scroll_down = min(0, text_rect.height - total_height - 15)
        self.scroll_y = max(max_scroll_down, min(max_scroll_up, self.scroll_y))

    def draw_log_panel(self, screen, log_history, typewriter_idx):
        """Renders the scrollable middle narrative log panel."""
        outer_rect = self.rect.inflate(4, 4)
        pygame.draw.rect(screen, TATE_RED, outer_rect, border_radius=8)
        pygame.draw.rect(screen, DIAL_CREAM, self.rect, border_radius=6)
        pygame.draw.rect(screen, CLOCK_BLACK, self.rect, width=1, border_radius=6)

        screen.set_clip(self.rect)
        current_y_offset = self.scroll_y
        chars_rendered_so_far = 0

        for line in log_history:
            if not isinstance(line, str):
                line = str(line)

            paragraphs = line.split("\n")
            for p in paragraphs:
                if p.strip() == "":
                    current_y_offset += 15
                    continue

                chars_allowed = max(0, typewriter_idx - chars_rendered_so_far)
                height_used = draw_wrapped_text(
                    screen, p, FONT, CLOCK_BLACK, self.rect,
                    current_y_offset, char_limit=chars_allowed
                )
                current_y_offset += height_used
                chars_rendered_so_far += len(p)

        total_log_height = current_y_offset - self.scroll_y
        screen.set_clip(None)

        max_scroll_up = 0
        max_scroll_down = min(0, self.rect.height - total_log_height - 30)
        self.scroll_y = max(max_scroll_down, min(max_scroll_up, self.scroll_y))

    def handle_scroll(self, mouse_pos, scroll_amount):
        """Scrolls the panel if the mouse cursor is hovering over it."""
        if self.rect.collidepoint(mouse_pos):
            self.scroll_y += scroll_amount * 20
            return True
        return False

    def force_scroll_to_bottom(self):
        """Forces the log panel to jump to the newest message at the bottom."""
        self.scroll_y = -9999


# =========================================================================
# 3. RECTANGULAR & CIRCULAR BUTTONS
# =========================================================================
class Button:
    """Auto-fitting rectangular button with 2-line wrap and invisible click-zone support."""

    def __init__(self, rect, label, callback, enabled=True, fixed_font=None, invisible=False):
        self.rect = pygame.Rect(rect)
        self.label = str(label)
        self.callback = callback
        self.enabled = enabled
        self.fixed_font = fixed_font
        self.invisible = invisible

    def _get_fitted_lines(self, max_w):
        if self.fixed_font is not None:
            return self.fixed_font, [self.label]
        for f in (FONT, FONT_MD):
            if f.size(self.label)[0] <= max_w:
                return f, [self.label]
        words = self.label.split()
        lines, cur = [], ""
        for w in words:
            if FONT_MD.size(cur + w + " ")[0] <= max_w:
                cur += w + " "
            else:
                if cur.strip():
                    lines.append(cur.strip())
                cur = w + " "
        if cur.strip():
            lines.append(cur.strip())
        return FONT_MD, lines or [self.label]

    def draw(self, surface, mouse_pos=None):
        if self.invisible:
            return

        is_hovered = bool(mouse_pos and self.rect.collidepoint(mouse_pos))

        if self.enabled:
            bg_color = DIAL_CREAM_HOVER if is_hovered else DIAL_CREAM
            frame_color = TATE_RED
            text_color = CLOCK_BLACK
        else:
            bg_color = DISABLED_CREAM
            frame_color = DISABLED_RED
            text_color = DISABLED_BLACK

        outer_rect = self.rect.inflate(4, 4)
        pygame.draw.rect(surface, frame_color, outer_rect, border_radius=8)
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, text_color, self.rect, width=1, border_radius=6)

        chosen_font, lines = self._get_fitted_lines(self.rect.width - 14)
        if len(lines) == 1:
            txt_surface = chosen_font.render(lines[0], True, text_color)
            txt_rect = txt_surface.get_rect(center=self.rect.center)
            surface.blit(txt_surface, txt_rect)
        else:
            line_h = chosen_font.get_linesize()
            total_h = line_h * len(lines)
            start_y = self.rect.centery - (total_h // 2) + (line_h // 2)
            for idx, line_str in enumerate(lines):
                txt_surface = chosen_font.render(line_str, True, text_color)
                txt_rect = txt_surface.get_rect(center=(self.rect.centerx, start_y + idx * line_h))
                surface.blit(txt_surface, txt_rect)

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


class CircleButton:
    """Circular icon button for the main HUD (Status, Inventory, Action, Help)."""

    def __init__(self, x, y, radius, icon_type, callback):
        self.x = x
        self.y = y
        self.radius = radius
        self.icon_type = icon_type
        self.callback = callback
        self.rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        self.icon_font = pygame.font.Font(None, int(self.radius * 1.5))

    def draw(self, screen, mouse_pos=None):
        is_hovered = bool(
            mouse_pos
            and math.hypot(mouse_pos[0] - self.x, mouse_pos[1] - self.y) <= self.radius
        )
        fill_col = DIAL_CREAM_HOVER if is_hovered else DIAL_CREAM

        pygame.draw.circle(screen, TATE_RED, (self.x, self.y), self.radius + 2)
        pygame.draw.circle(screen, fill_col, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, CLOCK_BLACK, (self.x, self.y), self.radius, 1)

        if self.icon_type == "help":
            text_surf = self.icon_font.render("?", True, CLOCK_BLACK)
            screen.blit(text_surf, text_surf.get_rect(center=(self.x, self.y)))

        elif self.icon_type == "inventory":
            text_surf = self.icon_font.render("i", True, CLOCK_BLACK)
            screen.blit(text_surf, text_surf.get_rect(center=(self.x, self.y - 2)))

        elif self.icon_type == "status":
            head_radius = self.radius * 0.18
            head_center = (self.x, self.y - self.radius * 0.15)
            pygame.draw.circle(screen, CLOCK_BLACK, head_center, head_radius)

            body_radius = self.radius * 0.35
            base_y = self.y + self.radius * 0.35
            points = []
            for angle in range(180, 361, 10):
                rad = math.radians(angle)
                px = self.x + body_radius * math.cos(rad)
                py = base_y + body_radius * math.sin(rad)
                points.append((px, py))
            pygame.draw.polygon(screen, CLOCK_BLACK, points)

        elif self.icon_type == "action":
            start_y = self.y - self.radius * 0.25
            spacing = self.radius * 0.25
            for i in range(3):
                line_y = start_y + i * spacing
                pygame.draw.circle(screen, CLOCK_BLACK, (int(self.x - self.radius * 0.3), int(line_y)), 3)
                pygame.draw.line(
                    screen,
                    CLOCK_BLACK,
                    (self.x - self.radius * 0.1, line_y),
                    (self.x + self.radius * 0.4, line_y),
                    3,
                )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                distance = math.hypot(event.pos[0] - self.x, event.pos[1] - self.y)
                if distance <= self.radius:
                    self.callback()
                    return True
        return False


# =========================================================================
# 4. THE RETRO D-PAD (8-Way Compass + Visual Forest Spin)
# =========================================================================
class RetroDPad:
    """8-way compass D-Pad with central Move/Look toggle and Lignum Forest spin animation."""

    def __init__(self, center_x, center_y, radius, callback, center_callback=None):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.callback = callback
        self.center_callback = center_callback
        self.mode_label = ""
        self.enabled = True
        self.show_labels = True

        self.spin_angle = 0.0
        self.spin_start_angle = 0.0
        self.spin_target_angle = 0.0
        self.spin_start_tick = 0
        self.spin_duration = 650

        self.font_primary = pygame.font.Font(None, 28)
        self.font_secondary = pygame.font.Font(None, 22)
        self.font_center = pygame.font.Font(None, 16)

    def trigger_spin(self):
        """Triggers a visible multi-revolution whirling animation on the D-Pad disc."""
        self.spin_start_tick = pygame.time.get_ticks()
        self.spin_start_angle = self.spin_angle
        self.spin_target_angle = self.spin_angle + random.uniform(4.2 * math.pi, 6.4 * math.pi)

    def draw(self, screen, mouse_pos=None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()

        now = pygame.time.get_ticks()
        is_spinning = False
        if not self.show_labels:
            elapsed = now - self.spin_start_tick
            if elapsed < self.spin_duration:
                is_spinning = True
                t = elapsed / float(self.spin_duration)
                ease = 1.0 - (1.0 - t) ** 3
                self.spin_angle = self.spin_start_angle + (self.spin_target_angle - self.spin_start_angle) * ease
            else:
                self.spin_angle = self.spin_target_angle % (2.0 * math.pi)
        else:
            self.spin_angle = 0.0

        hovered_dir = self.get_direction(mouse_pos) if self.enabled else None
        dist_from_center = math.hypot(mouse_pos[0] - self.center_x, mouse_pos[1] - self.center_y)
        center_hovered = (dist_from_center <= self.radius * 0.25) and self.enabled

        if self.enabled:
            frame_color = TATE_RED
            face_color = DIAL_CREAM
            text_color = CLOCK_BLACK
            hover_color = DIAL_CREAM_HOVER
        else:
            frame_color = DISABLED_RED
            face_color = DISABLED_CREAM
            text_color = DISABLED_BLACK
            hover_color = DISABLED_CREAM

        pygame.draw.circle(screen, frame_color, (self.center_x, self.center_y), self.radius + 4)
        pygame.draw.circle(screen, face_color, (self.center_x, self.center_y), self.radius)

        directions = [
            (0, -1, "N", "North", 3 * math.pi / 2),
            (1, -1, "NE", "North-East", 7 * math.pi / 4),
            (1, 0, "E", "East", 0),
            (1, 1, "SE", "South-East", math.pi / 4),
            (0, 1, "S", "South", math.pi / 2),
            (-1, 1, "SW", "South-West", 3 * math.pi / 4),
            (-1, 0, "W", "West", math.pi),
            (-1, -1, "NW", "North-West", 5 * math.pi / 4),
        ]

        for _, _, label, d_name, angle in directions:
            draw_ang = angle + self.spin_angle
            is_hover = (hovered_dir == d_name)

            if is_hover and self.enabled and not is_spinning:
                w_start, w_end = angle - math.pi / 8, angle + math.pi / 8
                points = [(self.center_x, self.center_y)]
                for a in range(int(math.degrees(w_start)), int(math.degrees(w_end)) + 1, 5):
                    rad = math.radians(a)
                    points.append((
                        self.center_x + math.cos(rad) * self.radius,
                        self.center_y + math.sin(rad) * self.radius,
                    ))
                if len(points) > 2:
                    pygame.draw.polygon(screen, hover_color, points)

            line_angle = draw_ang + (math.pi / 8)
            lx1 = self.center_x + math.cos(line_angle) * (self.radius * 0.25)
            ly1 = self.center_y + math.sin(line_angle) * (self.radius * 0.25)
            lx2 = self.center_x + math.cos(line_angle) * self.radius
            ly2 = self.center_y + math.sin(line_angle) * self.radius
            pygame.draw.line(screen, text_color, (lx1, ly1), (lx2, ly2), 2)

            if self.show_labels:
                text_x = self.center_x + math.cos(angle) * (self.radius * 0.7)
                text_y = self.center_y + math.sin(angle) * (self.radius * 0.7)
                font = self.font_primary if len(label) == 1 else self.font_secondary
                text_surf = font.render(label, True, text_color)
                screen.blit(text_surf, text_surf.get_rect(center=(int(text_x), int(text_y))))

        if not self.show_labels:
            notch_ang = (3 * math.pi / 2) + self.spin_angle
            nx1 = self.center_x + math.cos(notch_ang) * (self.radius * 0.52)
            ny1 = self.center_y + math.sin(notch_ang) * (self.radius * 0.52)
            nx2 = self.center_x + math.cos(notch_ang) * (self.radius * 0.88)
            ny2 = self.center_y + math.sin(notch_ang) * (self.radius * 0.88)
            pygame.draw.line(screen, TATE_RED, (nx1, ny1), (nx2, ny2), 4)
            pygame.draw.circle(screen, TATE_RED, (int(nx2), int(ny2)), 4)

        pygame.draw.circle(screen, text_color, (self.center_x, self.center_y), self.radius, 2)
        center_fill = hover_color if (center_hovered and self.center_callback) else face_color
        pygame.draw.circle(screen, center_fill, (self.center_x, self.center_y), int(self.radius * 0.25))
        pygame.draw.circle(screen, text_color, (self.center_x, self.center_y), int(self.radius * 0.25), 2)

        if self.mode_label:
            c_col = TATE_RED if self.mode_label == "LOOK" else text_color
            c_surf = self.font_center.render(self.mode_label, True, c_col)
            screen.blit(c_surf, c_surf.get_rect(center=(self.center_x, self.center_y)))

    def get_direction(self, pos):
        dist = math.hypot(pos[0] - self.center_x, pos[1] - self.center_y)
        if dist < self.radius * 0.25 or dist > self.radius:
            return None

        angle = math.atan2(pos[1] - self.center_y, pos[0] - self.center_x)
        if angle < 0:
            angle += 2 * math.pi

        slice_index = int(((angle + math.pi / 8) % (2 * math.pi)) / (math.pi / 4))
        directions = ["East", "South-East", "South", "South-West", "West", "North-West", "North", "North-East"]
        return directions[slice_index]

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dist = math.hypot(event.pos[0] - self.center_x, event.pos[1] - self.center_y)
            if dist <= self.radius * 0.25 and self.center_callback is not None:
                self.center_callback()
                return True
            dir_name = self.get_direction(event.pos)
            if dir_name:
                mapping = {
                    "North": (0, 1),
                    "North-East": (1, 1),
                    "East": (1, 0),
                    "South-East": (1, -1),
                    "South": (0, -1),
                    "South-West": (-1, -1),
                    "West": (-1, 0),
                    "North-West": (-1, 1),
                }
                dx, dy = mapping[dir_name]
                self.callback(dx, dy, dir_name)
                return True
        return False


# =========================================================================
# 5. THE DECIMAL CLOCK UI (Analogue / Digital Toggle)
# =========================================================================
class DecimalClockUI:
    """Renders the 10-hour Revolutionary Decimal Clock (click to toggle analogue/digital)."""

    def __init__(self, center_x, center_y, get_time_func):
        self.center_x = center_x
        self.center_y = center_y
        self.get_time_string = get_time_func
        self.style = "analogue"
        self.rect = pygame.Rect(self.center_x - 100, self.center_y - 70, 200, 140)
        self.tiny_font = pygame.font.Font(None, 16)
        self.big_font = pygame.font.Font(None, 64)

    def draw(self, screen, total_mins, accent_color):
        time_str = self.get_time_string(total_mins)
        date_part, time_part = time_str.split(" - ") if " - " in time_str else (time_str, "")

        if self.style == "analogue":
            radius = 60
            clock_center = (self.center_x, self.center_y - 12)

            pygame.draw.circle(screen, TATE_RED, clock_center, radius + 2)
            pygame.draw.circle(screen, DIAL_CREAM, clock_center, radius)
            pygame.draw.circle(screen, CLOCK_BLACK, clock_center, radius, 1)

            for i in range(1, 11):
                angle = math.radians((i % 10) * 36 - 90)
                tick_x = clock_center[0] + math.cos(angle) * (radius - 4)
                tick_y = clock_center[1] + math.sin(angle) * (radius - 4)
                pygame.draw.circle(screen, CLOCK_BLACK, (int(tick_x), int(tick_y)), 1.5)

                num_surf = self.tiny_font.render(str(i), True, CLOCK_BLACK)
                num_dist = radius - 12
                num_x = clock_center[0] + math.cos(angle) * num_dist
                num_y = clock_center[1] + math.sin(angle) * num_dist
                screen.blit(num_surf, num_surf.get_rect(center=(int(num_x), int(num_y))))

            hour = (total_mins % 1000) // 100
            minute = total_mins % 100

            h_angle = math.radians((hour + minute / 100.0) * 36 - 90)
            m_angle = math.radians(minute * 3.6 - 90)

            h_end = (
                clock_center[0] + math.cos(h_angle) * (radius * 0.45),
                clock_center[1] + math.sin(h_angle) * (radius * 0.45),
            )
            m_end = (
                clock_center[0] + math.cos(m_angle) * (radius * 0.72),
                clock_center[1] + math.sin(m_angle) * (radius * 0.72),
            )

            pygame.draw.line(screen, CLOCK_BLACK, clock_center, h_end, 3)
            pygame.draw.line(screen, CLOCK_BLACK, clock_center, m_end, 1)
            pygame.draw.circle(screen, CLOCK_BLACK, clock_center, 4)
        else:
            time_surf = self.big_font.render(time_part, True, accent_color)
            screen.blit(time_surf, time_surf.get_rect(center=(self.center_x, self.center_y - 12)))

        date_surf = FONT.render(date_part, True, TEXT_MUTED)
        screen.blit(date_surf, date_surf.get_rect(center=(self.center_x, self.center_y + 62)))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.style = "digital" if self.style == "analogue" else "analogue"
                return True
        return False


# =========================================================================
# 6. THE CARTOGRAPHIC MAP OVERLAY UI (Tate Britain Style)
# =========================================================================
MAP_CONFIGS = {
    "murum town map": {
        "title": "STREET PLAN OF THE WALLED TOWN OF MURUM",
        "x_range": (6, 12),
        "y_range": (12, 17),
        "show_labels": True,
    },
    "dtessera terra world map": {
        "title": "GRAND ATLAS OF DTESSERA TERRA",
        "x_range": (1, 20),
        "y_range": (1, 25),
        "show_labels": False,
    },
    "parvus town map": {
        "title": "REGIONAL CHART: PARVUS & THE NORTHERN APPROACH",
        "x_range": (10, 20),
        "y_range": (18, 25),
        "show_labels": True,
    },
    "fluvius town map": {
        "title": "REGIONAL CHART: FLUVIUS TOWN & FARMLANDS",
        "x_range": (7, 15),
        "y_range": (1, 8),
        "show_labels": True,
    },
    "lignum forest map": {
        "title": "FORESTER'S CHART: THE LIGNUM FOREST",
        "x_range": (7, 20),
        "y_range": (6, 25),
        "show_labels": False,
    },
    "caligo mountains map": {
        "title": "TOPOGRAPHICAL CHART: THE CALIGO MOUNTAINS",
        "x_range": (12, 20),
        "y_range": (1, 10),
        "show_labels": True,
    },
}

SHORT_TILE_LABELS = {
    (7, 16): "Town Gate",
    (7, 15): "Stables",
    (7, 14): "Guard",
    (8, 16): "Post Off.",
    (8, 15): "Market",
    (8, 14): "School",
    (9, 13): "Games",
    (9, 16): "Pub",
    (9, 15): "Mayor",
    (9, 14): "Playhouse",
    (8, 13): "Pasture",
    (10, 16): "Town Hall",
    (10, 15): "High Street",
    (10, 14): "Wallmakers",
    (10, 13): "Tavern",
    (11, 15): "Union H.",
    (11, 14): "Smithy",
    (9, 3):  "W. Bridge",
    (10, 4): "Laundry",
    (10, 5): "Sluice Ln",
    (11, 3): "Quay/Post",
    (11, 4): "Hall/Court",
    (11, 6): "Barricade",
    (12, 4): "Wharf Yd",
    (13, 7): "Watermill",
}


def _get_tile_style(loc, coord=None):
    """Returns (fill_rgb, kind_tag) for a Location object on the Cartographic Map."""
    if loc is None:
        return (225, 218, 202), "unmapped"
    name = loc.name.lower()
    region = loc.region.lower()

    if "town wall" in name or "town wall" in region:
        return (92, 90, 88), "wall"
    if "castle" in name or "castle" in region:
        return (180, 140, 135), "castle"
    if coord in the_river_fluvius_locations or "river" in name or "river" in region:
        return (115, 168, 205), "river"
    if "murum town" in region:
        if name == "x":
            return (215, 208, 192), "town_empty"
        if "grazing" in name:
            return (175, 205, 145), "pasture"
        return (228, 198, 165), "town"
    if "parvus" in region or "fluvius town" in region:
        return (222, 188, 155), "town"
    if "road" in region or ("path" in region and "plains" not in region):
        return (212, 192, 150), "road"
    if "lake" in region or "sea" in region:
        return (85, 140, 185), "water"
    if "cliff" in name or "coast" in region:
        return (165, 155, 140), "cliff"
    if "mountain" in region:
        return (150, 142, 135), "mountain"
    if "glade" in region:
        return (165, 202, 135), "glade"
    if "forest" in region:
        return (105, 150, 98), "forest"
    if "farm" in region:
        return (218, 198, 120), "farm"
    if "heath" in region:
        return (182, 165, 128), "heath"
    return (172, 198, 138), "plains"


def _draw_tile_embellishment(screen, rect, kind):
    """Draws miniature procedural cartographic icons inside a map tile."""
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height
    ink = (55, 48, 42)

    if kind == "wall":
        pygame.draw.rect(screen, (60, 58, 55), rect, 1)
        if h >= 12:
            pygame.draw.line(screen, (70, 68, 65), (rect.left + 2, cy), (rect.right - 2, cy), 1)
    elif kind == "castle" and w >= 14:
        bw = max(8, min(18, w - 6))
        bh = max(6, min(12, h - 6))
        bx, by = cx - bw // 2, cy - bh // 2 + 1
        pygame.draw.rect(screen, (95, 40, 35), (bx, by, bw, bh))
        for tx in (bx, cx - 1, bx + bw - 3):
            pygame.draw.rect(screen, (95, 40, 35), (tx, by - 3, 3, 3))
    elif kind == "mountain" and w >= 12:
        p1 = [(cx - 5, cy + 4), (cx - 1, cy - 4), (cx + 3, cy + 4)]
        p2 = [(cx - 1, cy + 4), (cx + 3, cy - 3), (cx + 6, cy + 4)]
        pygame.draw.lines(screen, ink, False, p1, 1)
        pygame.draw.lines(screen, ink, False, p2, 1)
    elif kind == "forest" and w >= 12:
        pygame.draw.circle(screen, (65, 105, 60), (cx, cy - 1), max(3, min(6, w // 4)))
        pygame.draw.rect(screen, (90, 65, 45), (cx - 1, cy + 2, 2, 3))
    elif kind in ("water", "river") and w >= 12:
        pygame.draw.line(screen, (215, 235, 250), (cx - 4, cy), (cx + 4, cy), 1)
    elif kind == "road" and w >= 10:
        pygame.draw.circle(screen, (130, 110, 80), (cx, cy), 2)
    elif kind == "farm" and w >= 12:
        for dy in (-2, 1):
            pygame.draw.line(screen, (170, 145, 75), (cx - 4, cy + dy), (cx + 4, cy + dy), 1)


def draw_cartographic_map(screen, map_key, player, world_map, mouse_pos):
    """Renders the full-screen interactive Cartographic Map and right-hand inspector panel."""
    cfg = MAP_CONFIGS.get(map_key, MAP_CONFIGS["dtessera terra world map"])
    x_min, x_max = cfg["x_range"]
    y_min, y_max = cfg["y_range"]
    cols = x_max - x_min + 1
    rows = y_max - y_min + 1

    # 1. Parchment Background & Double Border
    screen.fill(DIAL_CREAM)
    pygame.draw.rect(screen, TATE_RED, (12, 12, 776, 576), 4, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, (20, 20, 760, 560), 1, border_radius=4)

    # 2. Header Banner
    title_font = pygame.font.Font(None, 28)
    sub_font = pygame.font.Font(None, 18)
    label_font = pygame.font.Font(None, 15)

    t_surf = title_font.render(cfg["title"], True, TATE_RED)
    screen.blit(t_surf, (35, 28))

    # 3. Calculate Grid Cell Size inside Left Map Frame (35..515 x 58..535)
    avail_w, avail_h = 480, 472
    cell_w = avail_w // cols
    cell_h = avail_h // rows
    cell_size = max(16, min(cell_w, cell_h))

    grid_w = cell_size * cols
    grid_h = cell_size * rows
    start_x = 35 + (avail_w - grid_w) // 2
    start_y = 58 + (avail_h - grid_h) // 2

    pygame.draw.rect(screen, (210, 202, 185), (start_x - 4, start_y - 4, grid_w + 8, grid_h + 8))
    pygame.draw.rect(screen, CLOCK_BLACK, (start_x - 4, start_y - 4, grid_w + 8, grid_h + 8), 2)

    hovered_coord = None
    territories = player.get("territories", {})

    # 4. Draw Map Grid (y_max at top -> North is UP)
    for r_idx, map_y in enumerate(range(y_max, y_min - 1, -1)):
        for c_idx, map_x in enumerate(range(x_min, x_max + 1)):
            rx = start_x + c_idx * cell_size
            ry = start_y + r_idx * cell_size
            rect = pygame.Rect(rx, ry, cell_size, cell_size)

            loc = world_map.get((map_x, map_y))
            fill_col, kind = _get_tile_style(loc, (map_x, map_y))

            owner = territories.get(f"{map_x},{map_y}")
            if owner in FACTION_COLORS:
                tc = FACTION_COLORS[owner]
                fill_col = (
                    int(fill_col[0] * 0.72 + tc[0] * 0.28),
                    int(fill_col[1] * 0.72 + tc[1] * 0.28),
                    int(fill_col[2] * 0.72 + tc[2] * 0.28),
                )

            pygame.draw.rect(screen, fill_col, rect)
            pygame.draw.rect(screen, (185, 178, 162), rect, 1)

            _draw_tile_embellishment(screen, rect, kind)

            if owner in FACTION_COLORS:
                b_col = FACTION_COLORS[owner]
                bw = 3 if cell_size >= 24 else 2
                if territories.get(f"{map_x},{map_y + 1}") != owner:
                    pygame.draw.line(screen, b_col, (rect.left, rect.top), (rect.right - 1, rect.top), bw)
                if territories.get(f"{map_x},{map_y - 1}") != owner:
                    pygame.draw.line(screen, b_col, (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1), bw)
                if territories.get(f"{map_x - 1},{map_y}") != owner:
                    pygame.draw.line(screen, b_col, (rect.left, rect.top), (rect.left, rect.bottom - 1), bw)
                if territories.get(f"{map_x + 1},{map_y}") != owner:
                    pygame.draw.line(screen, b_col, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), bw)

            if cfg["show_labels"] and cell_size >= 38:
                short_lbl = SHORT_TILE_LABELS.get((map_x, map_y))
                if not short_lbl and loc and kind in ("town", "castle"):
                    short_lbl = loc.name[:9]
                if short_lbl:
                    l_surf = label_font.render(short_lbl, True, CLOCK_BLACK)
                    screen.blit(l_surf, l_surf.get_rect(center=(rect.centerx, rect.bottom - 8)))

            if player["x"] == map_x and player["y"] == map_y:
                pygame.draw.circle(screen, TATE_RED, rect.center, max(5, cell_size // 4))
                pygame.draw.circle(screen, (255, 230, 120), rect.center, max(3, cell_size // 6))
                pygame.draw.circle(screen, CLOCK_BLACK, rect.center, max(5, cell_size // 4), 1)

            if rect.collidepoint(mouse_pos):
                hovered_coord = (loc, owner)
                pygame.draw.rect(screen, TATE_RED, rect, 2)

    # 5. Right-Hand Inspector & Legend Panel (x = 530..765)
    info_rect = pygame.Rect(530, 58, 235, 310)
    pygame.draw.rect(screen, (236, 230, 214), info_rect, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, info_rect, 1, border_radius=6)

    screen.blit(title_font.render("N", True, TATE_RED), (642, 66))
    pygame.draw.line(screen, CLOCK_BLACK, (648, 88), (648, 112), 2)
    pygame.draw.line(screen, CLOCK_BLACK, (636, 100), (660, 100), 2)

    if hovered_coord is None:
        px, py = player["x"], player["y"]
        hovered_coord = (world_map.get((px, py)), territories.get(f"{px},{py}"))

    h_loc, h_owner = hovered_coord
    y_cursor = 122

    if h_loc:
        screen.blit(FONT.render(h_loc.name[:22], True, TATE_RED), (542, y_cursor))
        y_cursor += 24
        screen.blit(sub_font.render(f"Region: {h_loc.region}", True, (90, 80, 70)), (542, y_cursor))
        y_cursor += 20
        if h_owner:
            screen.blit(sub_font.render(f"Territory: {h_owner}", True, FACTION_COLORS.get(h_owner, TATE_RED)), (542, y_cursor))
        else:
            screen.blit(sub_font.render("Territory: Neutral / Unclaimed", True, (120, 110, 95)), (542, y_cursor))
    else:
        screen.blit(FONT.render("Uncharted Horizon", True, TATE_RED), (542, y_cursor))

    # Legend Key
    y_cursor = 206
    pygame.draw.line(screen, (180, 170, 155), (542, y_cursor), (752, y_cursor), 1)
    y_cursor += 6
    screen.blit(sub_font.render("TERRAIN & FACTION KEY:", True, CLOCK_BLACK), (542, y_cursor))
    y_cursor += 17

    legend_items = [
        (TATE_RED, "Your Position (Red Pin)"),
        ((228, 198, 165), "Town Streets & Buildings"),
        ((92, 90, 88), "The Town Wall (Climb/Walk)"),
        ((212, 192, 150), "Roads & Safe Paths"),
        ((105, 150, 98), "Lignum Forest (Compass)"),
        ((85, 140, 185), "Rivers, Lakes & Sea"),
    ]
    for fac_name in sorted(set(territories.values())):
        if fac_name in FACTION_COLORS:
            legend_items.append((FACTION_COLORS[fac_name], f"{fac_name} Territory"))

    for col_swatch, l_text in legend_items[:8]:
        pygame.draw.rect(screen, col_swatch, (544, y_cursor + 2, 11, 11))
        pygame.draw.rect(screen, CLOCK_BLACK, (544, y_cursor + 2, 11, 11), 1)
        screen.blit(label_font.render(l_text, True, CLOCK_BLACK), (560, y_cursor + 2))
        y_cursor += 16


# =========================================================================
# 7. TITLE SCREEN & CHAPTER 1 INTRO CARDS
# =========================================================================
def draw_title_or_intro_card(screen, state):
    """Draws the full-screen Tate Britain cream/crimson Title Screen or Chapter 1 Intro Card."""
    screen.fill((245, 240, 230))
    pygame.draw.rect(screen, (140, 25, 25), (16, 16, 768, 568), 4)
    pygame.draw.rect(screen, (60, 45, 40), (24, 24, 752, 552), 1)

    title_font = pygame.font.Font(None, 46)
    sub_font = pygame.font.Font(None, 24)
    body_font = pygame.font.Font(None, 21)

    if state == "START_SCREEN":
        t_surf = title_font.render("DTESSERA TERRA", True, (140, 25, 25))
        screen.blit(t_surf, (400 - t_surf.get_width() // 2, 75))

        s_surf = sub_font.render("Chapter I: The Walled Town of Murum (Beta Build)", True, (60, 45, 40))
        screen.blit(s_surf, (400 - s_surf.get_width() // 2, 132))

        pygame.draw.line(screen, (140, 25, 25), (180, 168), (620, 168), 2)

        lore_lines = [
            "A game of labour, intrigue, survival, and faction politics",
            "in a world governed by the 1,000-minute Revolutionary Decimal Clock.",
            "",
            "• Work 5 shifts across Murum's trades to forge your skills and reputation.",
            "• Navigate the rival ambitions of the Guard, the Workers' Union, and the Wallmakers.",
            "• Manage your silver, stamina, carry weight, and mount before curfew falls at 7:50.",
        ]
        y_pos = 195
        for line in lore_lines:
            l_surf = body_font.render(line, True, (40, 35, 30))
            screen.blit(l_surf, (400 - l_surf.get_width() // 2, y_pos))
            y_pos += 28

    elif state == "CHAPTER_1_INTRO":
        t_surf = title_font.render("CHAPTER I: QUINTIDI 5 BRUMAIRE", True, (140, 25, 25))
        screen.blit(t_surf, (400 - t_surf.get_width() // 2, 42))

        s_surf = sub_font.render("The Office of Dr. Makepeace — Escuela Moderna, Murum Town", True, (60, 45, 40))
        screen.blit(s_surf, (400 - s_surf.get_width() // 2, 92))

        pygame.draw.line(screen, (140, 25, 25), (120, 122), (680, 122), 2)

        intro_lines = [
            "Welcome to Dtessera Terra!",
            "",
            "This is the story of Noburu the adventurer. They will become whatever",
            "you make them from your decisions and the roll of the die.",
            "",
            "You begin in the walled town of Murum where you were born and raised.",
            "You enter the office of the headteacher and read the bronze plaque affixed",
            "to the door as you cross the threshold into the domain of the only authority",
            "that you have ever known; it reads: \"Dr. Makepeace, HEADTEACHER\".",
            "",
            "\"Noburu, welcome. Please sit down.\"",
            "\"You will be leaving us soon, I understand. You have completed your studies",
            "and must decide what next to do in your life. This can be a challenging and",
            "frightful time, but also a very rewarding one. Do you know what your next",
            "steps will be?\"",
        ]
        y_pos = 138
        for line in intro_lines:
            l_surf = body_font.render(line, True, (35, 30, 28))
            screen.blit(l_surf, (400 - l_surf.get_width() // 2, y_pos))
            y_pos += 23
            
