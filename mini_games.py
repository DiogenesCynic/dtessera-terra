"""
mini_games.py
-------------
Interactive mini-games, Arcade Parlour cabinets, House of Games casino tables
(Blackjack, Texas Hold'em, European Roulette, Craps), First-Person Longbow Archery,
and Chapter 2 Mission 1A/1B/2A interactive systems.
"""

import copy
import itertools
import math
import random
import pygame
from mechanics import (
    modify_faction,
    advance_time,
    mark_shift_completed,
    set_region_territory,
)
from ui_components import draw_fitted_text, draw_wrapped_banner

# --- UI CONSTANTS (Imported to match your theme) ---
PANEL_BG = (35, 42, 54)
PANEL_BORDER = (55, 65, 81)
TEXT_COLOR = (240, 240, 240)
TEXT_MUTED = (160, 174, 192)
LOCATION_ACCENT = (240, 180, 120)

# ==========================================
# BLACKSMITH SHIFT 2: THE FORGE (STORY + 60s ARCADE BLITZ)
# ==========================================

def start_next_forge_round(player):
    player["forge_round"] = player.get("forge_round", 0) + 1

    # Story mode ends at 20 strikes; Arcade mode runs until the 60s master clock expires!
    if not player.get("arcade_mode") and player["forge_round"] > 20:
        return conclude_forge_minigame(player)

    if player.get("arcade_mode"):
        # In 60s Arcade Blitz, the per-strike reaction window tightens from 2.5s down to 0.85s!
        player["forge_time_limit"] = max(0.85, 2.6 - (player["forge_round"] * 0.05))
    else:
        # Story mode: shrinks by 0.2s every round (5.0s down to 1.2s)
        player["forge_time_limit"] = max(1.0, 5.2 - (player["forge_round"] * 0.2))

    player["forge_timer"] = player["forge_time_limit"]
    player["forge_heat_state"] = random.choice([0, 1, 2])
    return player, None, "MINIGAME_FORGE"


def forge_action(action_type, player):
    correct = False
    if player["forge_heat_state"] == 0 and action_type == "pump":
        correct = True
    elif player["forge_heat_state"] == 1 and action_type == "coal":
        correct = True
    elif player["forge_heat_state"] == 2 and action_type == "wait":
        correct = True

    if not correct:
        player["forge_mistakes"] += 1
        if player.get("arcade_mode"):
            player["forge_arcade_time_left"] = max(0.0, player.get("forge_arcade_time_left", 60.0) - 2.0)
            log_msg = f"*** MISSTRIKE! (-2.0s Penalty | Mistakes: {player['forge_mistakes']}/3) ***"
        else:
            log_msg = f"*** WRONG ACTION! (+1 Mistake. Total: {player['forge_mistakes']}/3) ***"

        if player["forge_mistakes"] > 3:
            return fail_forge_minigame(player, log_msg)
        return player, log_msg, "MINIGAME_FORGE"

    if player.get("arcade_mode"):
        player["forge_score"] = player.get("forge_score", 0) + 10

    return start_next_forge_round(player)


def fail_forge_minigame(player, extra_log=""):
    if player.get("arcade_mode"):
        strikes = max(0, player.get("forge_round", 1) - 1)
        score = player.get("forge_score", strikes * 10)
        return finish_arcade_session(
            player, "forge", score,
            f"Arcade Forge Blitz: The blade shattered after {strikes} strikes! (Score: {score} pts)"
        )

    player["active_blacksmith_task"] = "report_forge_fail"
    log = extra_log + "\n\n" if extra_log else ""
    log += "*** The steel is ruined! You must speak to Lovejoy to face the consequences... ***"
    return player, log, "MAIN"


def conclude_forge_minigame(player):
    if player.get("arcade_mode"):
        strikes = max(0, player.get("forge_round", 1) - 1)
        score = player.get("forge_score", strikes * 10)
        return finish_arcade_session(
            player, "forge", score,
            f"*** 60 SECONDS UP! You landed {strikes} clean strikes on the anvil for {score} points! ***"
        )

    player["active_blacksmith_task"] = "report_forge_success"
    log = "*** The steel cools. You have finished hammering. Speak to Lovejoy to have your work evaluated! ***"
    return player, log, "MAIN"


def draw_forge_ui(screen, player, font, font_bold):
    """Draws the thermometer, strike counter, and 60s Arcade Blitz clock."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    if player.get("arcade_mode"):
        strikes = max(0, player.get("forge_round", 1) - 1)
        score = player.get("forge_score", 0)
        t_left = max(0.0, player.get("forge_arcade_time_left", 60.0))
        round_txt = font_bold.render(f"BLITZ: {t_left:04.1f}s LEFT", True, LOCATION_ACCENT)
        score_txt = font_bold.render(f"Strikes: {strikes} ({score} pts)", True, TEXT_COLOR)
        screen.blit(round_txt, (555, 152))
        screen.blit(score_txt, (555, 178))
        mistake_y = 204
    else:
        round_txt = font_bold.render(f"STRIKE: {player['forge_round']}/20", True, TEXT_COLOR)
        screen.blit(round_txt, (565, 160))
        mistake_y = 190

    mistake_txt = font.render(f"Mistakes: {player['forge_mistakes']}/3", True, (220, 80, 80))
    screen.blit(mistake_txt, (565, mistake_y))

    thermo_rect = pygame.Rect(485, 158, 40, 180)
    pygame.draw.rect(screen, (20, 25, 30), thermo_rect, border_radius=10)
    pygame.draw.rect(screen, PANEL_BORDER, thermo_rect, width=2, border_radius=10)

    target_h = 30 if player["forge_heat_state"] == 0 else 100 if player["forge_heat_state"] == 1 else 170
    heat_color = (200, 100, 0) if player["forge_heat_state"] == 0 else (220, 30, 30) if player["forge_heat_state"] == 1 else (255, 255, 255)

    fill_rect = pygame.Rect(485, 158 + (180 - target_h), 40, target_h)
    pygame.draw.rect(screen, heat_color, fill_rect, border_radius=10)

    screen.blit(font.render("HOT (Wait)", True, TEXT_MUTED), (538, 165))
    screen.blit(font.render("PERFECT (Coal)", True, LOCATION_ACCENT), (538, 238))
    screen.blit(font.render("COLD (Pump)", True, TEXT_MUTED), (538, 310))
    pygame.draw.rect(screen, LOCATION_ACCENT, pygame.Rect(480, 228, 50, 40), width=3, border_radius=5)

    # Strike Reaction Timer Bar
    t_limit = max(0.1, player.get("forge_time_limit", 2.0))
    timer_width = int(280 * (max(0.0, player["forge_timer"]) / t_limit))
    pygame.draw.rect(screen, (200, 80, 80), pygame.Rect(480, 352, timer_width, 10), border_radius=5)

    # 60s Arcade Master Clock Bar
    if player.get("arcade_mode"):
        arc_w = int(280 * (max(0.0, player.get("forge_arcade_time_left", 60.0)) / 60.0))
        pygame.draw.rect(screen, (80, 180, 230), pygame.Rect(480, 368, arc_w, 8), border_radius=4)


def update_forge_timer(player, dt):
    """Ticks both the per-strike timer and (in Arcade Mode) the 60-second master blitz timer."""
    if player.get("arcade_mode"):
        player["forge_arcade_time_left"] = player.get("forge_arcade_time_left", 60.0) - dt
        if player["forge_arcade_time_left"] <= 0:
            return conclude_forge_minigame(player)

    player["forge_timer"] -= dt
    if player["forge_timer"] <= 0:
        player["forge_mistakes"] += 1
        log_msg = f"*** TOO SLOW! The metal warps! (+1 Mistake. Total: {player['forge_mistakes']}/3) ***"

        if player["forge_mistakes"] > 3:
            return fail_forge_minigame(player, log_msg)
        else:
            p, next_log, state = start_next_forge_round(player)
            if next_log:
                log_msg += "\n" + next_log
            return p, log_msg, state

    return player, None, "MINIGAME_FORGE"

# ==========================================
# BLACKSMITH SHIFT 3: PENTOMINO JIGSAW (STORY + 60s ARCADE RUSH)
# ==========================================

PENTOMINO_SETS = [
    # Set A: Classic V, P, U, W, L
    [
        {"id": 1, "name": "V-Bit",   "shape": [(0,0), (1,0), (2,0), (0,1), (0,2)], "color": (165, 80, 80)},
        {"id": 2, "name": "P-Bag",   "shape": [(0,0), (1,0), (0,1), (1,1), (1,2)], "color": (80, 155, 90)},
        {"id": 3, "name": "U-Grip",  "shape": [(0,0), (1,0), (0,1), (0,2), (1,2)], "color": (80, 105, 175)},
        {"id": 4, "name": "W-Crank", "shape": [(0,0), (1,0), (1,1), (2,1), (2,2)], "color": (195, 175, 75)},
        {"id": 5, "name": "L-Shaft", "shape": [(0,0), (0,1), (1,1), (2,1), (3,1)], "color": (165, 85, 165)},
    ],
    # Set B: V, N, U, P, Y
    [
        {"id": 1, "name": "V-Frame", "shape": [(0,0), (0,1), (0,2), (1,2), (2,2)], "color": (190, 95, 70)},
        {"id": 2, "name": "N-Brace", "shape": [(0,0), (1,0), (2,0), (2,1), (3,1)], "color": (75, 160, 140)},
        {"id": 3, "name": "U-Core",  "shape": [(0,0), (1,0), (0,1), (0,2), (1,2)], "color": (95, 115, 185)},
        {"id": 4, "name": "P-Block", "shape": [(0,0), (1,0), (0,1), (1,1), (1,2)], "color": (205, 165, 70)},
        {"id": 5, "name": "Y-Spindle","shape": [(1,0), (0,1), (1,1), (1,2), (1,3)], "color": (175, 90, 145)},
    ],
    # Set C: Mirror/Rotated Tiling Variant
    [
        {"id": 1, "name": "L-Plate", "shape": [(0,0), (1,0), (2,0), (3,0), (0,1)], "color": (180, 85, 95)},
        {"id": 2, "name": "P-Gear",  "shape": [(0,0), (1,0), (0,1), (1,1), (0,2)], "color": (85, 165, 105)},
        {"id": 3, "name": "U-Casing","shape": [(0,0), (2,0), (0,1), (1,1), (2,1)], "color": (85, 130, 190)},
        {"id": 4, "name": "W-Cam",   "shape": [(0,0), (0,1), (1,1), (1,2), (2,2)], "color": (200, 155, 65)},
        {"id": 5, "name": "V-Corner","shape": [(0,0), (1,0), (2,0), (2,1), (2,2)], "color": (155, 95, 180)},
    ],
]


def rotate_shape(shape):
    """Rotates an array of local (x,y) coordinates 90 degrees clockwise."""
    new_shape = [(y, -x) for x, y in shape]
    min_x = min(p[0] for p in new_shape)
    min_y = min(p[1] for p in new_shape)
    return [(x - min_x, y - min_y) for x, y in new_shape]


def _spawn_jigsaw_board(player):
    """Creates a fresh 5x5 grid and scrambles a Pentomino piece set."""
    player["jigsaw_grid"] = [[0] * 5 for _ in range(5)]
    if player.get("arcade_mode"):
        chosen_template = random.choice(PENTOMINO_SETS)
    else:
        chosen_template = PENTOMINO_SETS[0]

    pieces = []
    for item in chosen_template:
        sh = list(item["shape"])
        # Randomly rotate pieces in Arcade mode so every board is a fresh spatial challenge!
        rotations = random.randint(1, 3) if player.get("arcade_mode") else 0
        for _ in range(rotations):
            sh = rotate_shape(sh)
        pieces.append({
            "id": item["id"],
            "name": item["name"],
            "shape": sh,
            "color": item["color"],
            "placed": False,
        })
    if player.get("arcade_mode"):
        random.shuffle(pieces)
    player["jigsaw_pieces"] = pieces
    player["jigsaw_selected"] = None


def init_jigsaw(player):
    player["jigsaw_score"] = 0
    player["jigsaw_boards_cleared"] = 0
    player["jigsaw_time_left"] = 60.0
    _spawn_jigsaw_board(player)

    if player.get("arcade_mode"):
        log = (
            "--- ARCADE PENTOMINO RUSH (60.0 SECONDS) ---\n"
            "Assemble as many 5x5 Pentomino frames as you can in 60 seconds!\n"
            "• Each completed 5x5 frame awards **100 points** and immediately spawns a new scrambled board!\n"
            "• Left-Click to Pick Up / Place | Right-Click to Rotate 90°!"
        )
    else:
        log = "*** The blueprint lies before you. Assemble the 5 parts into the 5x5 square frame. (Left-Click: Pickup/Place, Right-Click: Rotate) ***"
    return player, log, "MINIGAME_JIGSAW"


def update_jigsaw_timer(player, dt):
    """Ticks the 60-second clock during Arcade Pentomino Rush."""
    if not player.get("arcade_mode"):
        return player, None, "MINIGAME_JIGSAW"

    player["jigsaw_time_left"] = player.get("jigsaw_time_left", 60.0) - dt
    if player["jigsaw_time_left"] <= 0:
        boards = player.get("jigsaw_boards_cleared", 0)
        # Also award partial credit (15 pts) for each piece placed on the current unfinished board
        placed_now = sum(1 for p in player.get("jigsaw_pieces", []) if p.get("placed"))
        total_score = (boards * 100) + (placed_now * 15)
        return finish_arcade_session(
            player, "jigsaw", total_score,
            f"*** TIME UP! You cleared {boards} full board(s) (+{placed_now} pieces placed) for {total_score} points! ***"
        )
    return player, None, "MINIGAME_JIGSAW"


def handle_jigsaw_event(event, player):
    grid_x, grid_y = 480, 195
    cell_size = 38
    palette_x, palette_y = 695, 180

    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_x, mouse_y = event.pos

        # Right-Click to Rotate Selected Piece
        if event.button == 3 and player["jigsaw_selected"] is not None:
            p_idx = player["jigsaw_selected"]
            player["jigsaw_pieces"][p_idx]["shape"] = rotate_shape(player["jigsaw_pieces"][p_idx]["shape"])
            return player, None, "MINIGAME_JIGSAW"

        # Left-Click to Pickup/Place
        if event.button == 1:
            if grid_x <= mouse_x < grid_x + 5 * cell_size and grid_y <= mouse_y < grid_y + 5 * cell_size:
                cx = (mouse_x - grid_x) // cell_size
                cy = (mouse_y - grid_y) // cell_size

                if player["jigsaw_selected"] is not None:
                    p_idx = player["jigsaw_selected"]
                    piece = player["jigsaw_pieces"][p_idx]
                    anchor_x = min(px for px, py in piece["shape"] if py == 0)

                    can_place = True
                    coords = []
                    for px, py in piece["shape"]:
                        nx, ny = cx + (px - anchor_x), cy + py
                        if nx < 0 or nx >= 5 or ny < 0 or ny >= 5 or player["jigsaw_grid"][ny][nx] != 0:
                            can_place = False
                            break
                        coords.append((nx, ny))

                    if can_place:
                        for nx, ny in coords:
                            player["jigsaw_grid"][ny][nx] = piece["id"]
                        piece["placed"] = True
                        player["jigsaw_selected"] = None

                        # Check Win Condition
                        if all(p["placed"] for p in player["jigsaw_pieces"]):
                            if player.get("arcade_mode"):
                                player["jigsaw_boards_cleared"] = player.get("jigsaw_boards_cleared", 0) + 1
                                player["jigsaw_score"] = player["jigsaw_boards_cleared"] * 100
                                _spawn_jigsaw_board(player)
                                t_rem = max(0.0, player.get("jigsaw_time_left", 0.0))
                                msg = f"*** BOARD #{player['jigsaw_boards_cleared']} COMPLETE (+100 PTS | Total: {player['jigsaw_score']} pts | {t_rem:.1f}s left)! Next board! ***"
                                return player, msg, "MINIGAME_JIGSAW"

                            player["active_blacksmith_task"] = "report_shift_3"
                            for item in ["leather", "package of drill parts", "wallmaker blueprint"]:
                                if item in player["inventory"]:
                                    player["inventory"].remove(item)
                            player["inventory"].append("masonry drill")

                            log = "*** SUCCESS! The pieces snap together perfectly. You have crafted the Masonry Drill! ***\nSelect \"Return from Task\" to show Lovejoy your handiwork."
                            return player, log, "MAIN"

                else:
                    # Pick up placed piece
                    cell_val = player["jigsaw_grid"][cy][cx]
                    if cell_val != 0:
                        for y in range(5):
                            for x in range(5):
                                if player["jigsaw_grid"][y][x] == cell_val:
                                    player["jigsaw_grid"][y][x] = 0
                        for i, p in enumerate(player["jigsaw_pieces"]):
                            if p["id"] == cell_val:
                                p["placed"] = False
                                player["jigsaw_selected"] = i
                                break

            elif palette_x - 10 <= mouse_x <= palette_x + 85:
                for i, p in enumerate(player["jigsaw_pieces"]):
                    if not p["placed"]:
                        by = palette_y + i * 42
                        if by - 5 <= mouse_y <= by + 38:
                            player["jigsaw_selected"] = i
                            break
            elif player["jigsaw_selected"] is not None:
                player["jigsaw_selected"] = None

    return player, None, "MINIGAME_JIGSAW"


def draw_jigsaw_ui(screen, player, font, font_bold):
    minigame_bg = pygame.Rect(460, 140, 320, 295)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    if player.get("arcade_mode"):
        t_left = max(0.0, player.get("jigsaw_time_left", 60.0))
        pts = player.get("jigsaw_score", 0)
        title = font_bold.render(f"PENTOMINO RUSH: {t_left:04.1f}s", True, LOCATION_ACCENT)
        pts_surf = font_bold.render(f"{pts} pts", True, (110, 215, 140))
        screen.blit(title, (475, 150))
        screen.blit(pts_surf, (700, 150))
    else:
        title = font_bold.render("Assemble Blueprint (R-Click Rotate)", True, LOCATION_ACCENT)
        screen.blit(title, (475, 150))

    grid_x, grid_y = 480, 195
    cell_size = 38
    for y in range(5):
        for x in range(5):
            rect = pygame.Rect(grid_x + x * cell_size, grid_y + y * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, (20, 25, 30), rect)
            pygame.draw.rect(screen, PANEL_BORDER, rect, 1)

            val = player["jigsaw_grid"][y][x]
            if val != 0:
                for p in player["jigsaw_pieces"]:
                    if p["id"] == val:
                        pygame.draw.rect(screen, p["color"], rect.inflate(-2, -2), border_radius=3)
                        break

    palette_x, palette_y = 695, 180
    p_cell = 9
    for i, p in enumerate(player["jigsaw_pieces"]):
        if not p["placed"]:
            px, py = palette_x, palette_y + i * 42
            if player["jigsaw_selected"] == i:
                pygame.draw.rect(screen, LOCATION_ACCENT, (px - 5, py - 5, 52, 38), 1, border_radius=3)

            for bx, by in p["shape"]:
                rect = pygame.Rect(px + bx * p_cell, py + by * p_cell, p_cell, p_cell)
                pygame.draw.rect(screen, p["color"], rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 1)

    if player["jigsaw_selected"] is not None:
        mx, my = pygame.mouse.get_pos()
        p = player["jigsaw_pieces"][player["jigsaw_selected"]]
        if grid_x <= mx < grid_x + 5 * cell_size and grid_y <= my < grid_y + 5 * cell_size:
            cx = (mx - grid_x) // cell_size
            cy = (my - grid_y) // cell_size
            anchor_x = min(px for px, py in p["shape"] if py == 0)
            for bx, by in p["shape"]:
                nx, ny = cx + (bx - anchor_x), cy + by
                if 0 <= nx < 5 and 0 <= ny < 5:
                    r = pygame.Rect(grid_x + nx * cell_size, grid_y + ny * cell_size, cell_size, cell_size)
                    pygame.draw.rect(screen, p["color"], r.inflate(-4, -4), width=3, border_radius=3)
        else:
            for bx, by in p["shape"]:
                rect = pygame.Rect(mx + bx * 24, my + by * 24, 24, 24)
                pygame.draw.rect(screen, p["color"], rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)

    if player.get("arcade_mode"):
        bar_w = int(285 * (max(0.0, player.get("jigsaw_time_left", 60.0)) / 60.0))
        pygame.draw.rect(screen, (80, 180, 230), pygame.Rect(478, 415, bar_w, 8), border_radius=4)

# ==========================================
# MARKET SHIFT 5: THE HORIZONTAL THIEF CHASE
# ==========================================

def init_chase(player, stage=1, bonus_paces=0):
    """Initializes or resumes the horizontal thief chase at the given sprint stage."""
    if stage == 1:
        player["chase_distance"] = max(6, 12 - bonus_paces)
        player["chase_mistakes"] = 0
        player["chase_target_distance"] = 8
    elif stage == 2:
        player["chase_distance"] = max(3, player.get("chase_distance", 8) - bonus_paces)
        player["chase_target_distance"] = 4
    elif stage == 3:
        player["chase_distance"] = max(1, player.get("chase_distance", 4) - bonus_paces)
        player["chase_target_distance"] = 0

    player["chase_stage"] = stage
    player["chase_time_limit"] = max(1.2, 2.8 - (stage * 0.4))
    player["chase_timer"] = player["chase_time_limit"]
    player["chase_thief_dir"] = random.choice([0, 1, 2]) # 0: Left, 1: Straight, 2: Right
    return player, None, "MINIGAME_CHASE"

def start_next_chase_step(player):
    """Checks if the player reached the current stage threshold or cornered the thief."""
    dist = player["chase_distance"]
    stage = player.get("chase_stage", 1)

    # In Arcade Practice Mode, run all 3 stages continuously down to 0 paces!
    if player.get("arcade_mode"):
        if dist <= 0:
            score = max(10, 120 - (player.get("chase_mistakes", 0) * 25))
            return finish_arcade_session(player, "chase", score, "Arcade Practice: You caught the Cutpurse at the wall!")
        elif dist <= 4 and stage < 3:
            player["chase_stage"] = 3
        elif dist <= 8 and stage < 2:
            player["chase_stage"] = 2
        stage = player["chase_stage"]
        player["chase_time_limit"] = max(1.1, 2.6 - (stage * 0.35))
        player["chase_timer"] = player["chase_time_limit"]
        player["chase_thief_dir"] = random.choice([0, 1, 2])
        return player, None, "MINIGAME_CHASE"

    if stage == 1 and dist <= 8:
        player["market_state"] = "chase_stage_2"
        log = (
            "*** SPRINT 1 COMPLETE! You're right on his heels (8 paces)! ***\n"
            "The thief ducks into a narrow cobblestone alley and tips over a massive **Cart of Cabbages** directly into your path!\n"
            "Click Godwin / Continue in the dialogue menu to react!"
        )
        return player, log, "NPC_DIALOGUE"

    if stage == 2 and dist <= 4:
        player["chase_stage"] = 3
        player["chase_target_distance"] = 0
        player["chase_time_limit"] = 1.5
        player["chase_timer"] = 1.5
        player["chase_thief_dir"] = random.choice([0, 1, 2])
        log = "*** FINAL SPRINT! He's only 4 paces ahead—match his moves to corner him against the Town Wall! ***"
        return player, log, "MINIGAME_CHASE"

    if stage == 3 and dist <= 0:
        player["market_state"] = "chase_stage_3"
        log = (
            "*** CAUGHT! (0 paces!) ***\n"
            "You corner the breathless Cutpurse against the dead-end stone masonry of the Town Wall as he fumbles with a climbing rope!\n"
            "How do you finish this?!"
        )
        return player, log, "NPC_DIALOGUE"

    # Otherwise, pick the thief's next sudden move!
    player["chase_time_limit"] = max(1.1, 2.6 - (stage * 0.35))
    player["chase_timer"] = player["chase_time_limit"]
    player["chase_thief_dir"] = random.choice([0, 1, 2])
    return player, None, "MINIGAME_CHASE"

def chase_action(action_dir, player):
    """Handles Left (0), Straight (1), or Right (2) button clicks."""
    if "chase_thief_dir" not in player:
        init_chase(player, stage=1, bonus_paces=0)

    dir_map = {"left": 0, "straight": 1, "right": 2}
    chosen = dir_map.get(action_dir, -1)

    if chosen == player["chase_thief_dir"]:
        # Fast reaction (>50% timer remaining) closes 2 paces; normal closes 1 pace
        ratio = player["chase_timer"] / max(0.1, player["chase_time_limit"])
        gain = 2 if ratio >= 0.5 else 1
        player["chase_distance"] = max(0, player["chase_distance"] - gain)
        p, next_log, next_state = start_next_chase_step(player)
        move_lbl = "SURGE!" if gain == 2 else "Good read!"
        log_msg = f"*** {move_lbl} You closed {gain} pace(s)! (Distance: {player['chase_distance']} paces) ***"
        if next_log:
            log_msg += "\n" + next_log
        return p, log_msg, next_state
    else:
        player["chase_mistakes"] += 1
        player["chase_distance"] += 1
        log_msg = f"*** WRONG WAY! The thief jukes past you! (+1 Pace, Mistake {player['chase_mistakes']}/4) ***"
        if player["chase_mistakes"] >= 4 or player["chase_distance"] >= 18:
            return fail_chase_minigame(player, log_msg)
        p, next_log, next_state = start_next_chase_step(player)
        if next_log:
            log_msg += "\n" + next_log
        return p, log_msg, next_state

def update_chase_timer(player, dt):
    """Ticks the horizontal reaction timer down in real time."""
    player["chase_timer"] -= dt
    if player["chase_timer"] <= 0:
        player["chase_mistakes"] += 1
        player["chase_distance"] += 1
        log_msg = f"*** TOO SLOW! The thief pulls ahead! (+1 Pace, Mistake {player['chase_mistakes']}/4) ***"
        if player["chase_mistakes"] >= 4 or player["chase_distance"] >= 18:
            return fail_chase_minigame(player, log_msg)
        p, next_log, next_state = start_next_chase_step(player)
        if next_log:
            log_msg += "\n" + next_log
        return p, log_msg, next_state
    return player, None, "MINIGAME_CHASE"

def fail_chase_minigame(player, extra_log=""):
    if player.get("arcade_mode"):
        score = max(0, (18 - player.get("chase_distance", 18)) * 5)
        return finish_arcade_session(player, "chase", score, "Arcade Practice: The Cutpurse escaped over the wall!")

    player["active_market_task"] = "report_market_shift_5_fail"
    player["market_state"] = None
    log = extra_log + "\n\n" if extra_log else ""
    log += "*** The thief scales the Town Wall and vanishes with Godwin's lockbox! Return to Godwin to report the failure... ***"
    return player, log, "MAIN"

def draw_chase_ui(screen, player, font, font_bold):
    """Draws the horizontal 3-lane gauge, thief direction indicator, and distance bar."""
    minigame_bg = pygame.Rect(460, 140, 320, 240)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    stage = player.get("chase_stage", 1)
    dist = player.get("chase_distance", 12)
    mistakes = player.get("chase_mistakes", 0)

    title_surf = font_bold.render(f"PURSUIT (STAGE {stage}/3) — GAP: {dist} PACES", True, LOCATION_ACCENT)
    mistake_surf = font.render(f"Mistakes: {mistakes}/4", True, (220, 80, 80))
    screen.blit(title_surf, (475, 152))
    screen.blit(mistake_surf, (475, 176))

    gauge_rect = pygame.Rect(475, 205, 290, 65)
    pygame.draw.rect(screen, (20, 25, 30), gauge_rect, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, gauge_rect, width=2, border_radius=8)

    lane_w = 290 // 3
    thief_dir = player.get("chase_thief_dir", 1)
    lane_labels = ["<< DART LEFT", "^^ STRAIGHT ^^", "SHOT RIGHT >>"]
    lane_colors = [(220, 140, 60), (80, 190, 120), (220, 140, 60)]

    for i in range(3):
        lx = 475 + i * lane_w
        w = lane_w if i < 2 else 290 - (2 * lane_w)
        lane_box = pygame.Rect(lx + 3, 208, w - 6, 59)
        if i == thief_dir:
            pygame.draw.rect(screen, lane_colors[i], lane_box, border_radius=6)
            draw_fitted_text(screen, lane_labels[i], lane_box, (20, 25, 30), bold=True)
        else:
            pygame.draw.rect(screen, (35, 42, 54), lane_box, border_radius=6)
            draw_fitted_text(screen, lane_labels[i], lane_box, TEXT_MUTED, bold=False)

    dist_label = font.render("Closing Distance to Thief:", True, TEXT_COLOR)
    screen.blit(dist_label, (475, 282))
    track_rect = pygame.Rect(475, 305, 290, 16)
    pygame.draw.rect(screen, (20, 25, 30), track_rect, border_radius=6)
    progress_ratio = max(0.0, min(1.0, (16 - dist) / 16.0))
    fill_w = int(290 * progress_ratio)
    pygame.draw.rect(screen, (80, 180, 230), pygame.Rect(475, 305, fill_w, 16), border_radius=6)
    pygame.draw.rect(screen, PANEL_BORDER, track_rect, width=1, border_radius=6)

    t_limit = max(0.1, player.get("chase_time_limit", 2.0))
    t_rem = max(0.0, player.get("chase_timer", 0.0))
    timer_w = int(290 * (t_rem / t_limit))
    pygame.draw.rect(screen, (220, 80, 80), pygame.Rect(475, 345, timer_w, 12), border_radius=5)

# ==========================================
# WALLMAKERS SHIFT 1: SOUNDING THE STONE (STORY + 60s ARCADE MINESWEEPER RUSH)
# ==========================================

SECTOR_NAMES = {
    "north": "North Wall (Behind the Post Office & Pub)",
    "west":  "West Wall (Behind the Stables)",
    "south": "South Wall (Grazing Field Perimeter)",
    "east":  "East Wall (Behind the Blacksmiths)",
    "arcade": "Arcade Masonry Blitz"
}


def _spawn_sounding_board(player):
    """Generates a fresh 4x4 acoustic grid with a randomized 3-stone flaw."""
    player["sounding_revealed"] = [[False] * 4 for _ in range(4)]
    player["sounding_chalk"] = [[False] * 4 for _ in range(4)]
    player["sounding_tool"] = "hammer"
    player["sounding_taps"] = 0
    player["sounding_recorded"] = False
    player["sounding_wiped"] = True

    flaw_shapes = [
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1)],
        [(1, 0), (0, 1), (1, 1)],
        [(0, 0), (0, 1), (1, 1)]
    ]
    shape = random.choice(flaw_shapes)
    max_dx = max(p[0] for p in shape)
    max_dy = max(p[1] for p in shape)
    ox = random.randint(0, 3 - max_dx)
    oy = random.randint(0, 3 - max_dy)
    flaw_coords = {(ox + dx, oy + dy) for dx, dy in shape}

    grid = [[0] * 4 for _ in range(4)]
    for y in range(4):
        for x in range(4):
            if (x, y) in flaw_coords:
                grid[y][x] = 2
            else:
                for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                    if (nx, ny) in flaw_coords:
                        grid[y][x] = 1
                        break
    player["sounding_grid"] = grid


def init_sounding_minigame(player, sector_key="arcade"):
    """Initializes a 4x4 stone inspection grid for Story Mode or 60s Arcade Minesweeper Rush."""
    player["sounding_sector"] = sector_key
    player["sounding_score"] = 0
    player["sounding_walls_cleared"] = 0
    player["sounding_time_left"] = 60.0
    _spawn_sounding_board(player)

    if player.get("arcade_mode"):
        log = (
            "--- ARCADE MASON'S MINESWEEPER RUSH (60.0 SECONDS) ---\n"
            "Sound the granite and chalk as many 3-stone hollow flaws as you can in 60 seconds!\n"
            "• Left-Click to tap with your Hammer (`!` = Flaw, `~` = Adjacent to Flaw, `.` = Solid).\n"
            "• Right-Click (or switch tool) to mark the 3 flawed stones with White Chalk, then click [Record Flaw in Ledger]!\n"
            "• Every accurate 3-stone outline awards **+100 pts** (+25 bonus pts if solved in <= 5 taps)!"
        )
        return player, log, "MINIGAME_SOUNDING"

    is_final_sector = (len(player.get("wall_sectors_inspected", [])) == 3)
    log = f"--- INSPECTING: {SECTOR_NAMES.get(sector_key, 'Wall').upper()} ---\n"
    if is_final_sector:
        log += "You approach the final stretch of masonry. Fresh stone dust litters the weeds at the base of the wall...\n"
    log += (
        "Left-Click stones to use your active tool (or Right-Click any stone to toggle Chalk).\n"
        "Find and outline all 3 flawed stones in 7 hammer taps or fewer, record them in your ledger, and wipe your chalk before leaving!"
    )
    return player, log, "MINIGAME_SOUNDING"


def update_sounding_timer(player, dt):
    """Ticks the 60-second clock during Arcade Mason's Minesweeper Rush."""
    if not player.get("arcade_mode"):
        return player, None, "MINIGAME_SOUNDING"

    player["sounding_time_left"] = player.get("sounding_time_left", 60.0) - dt
    if player["sounding_time_left"] <= 0:
        cleared = player.get("sounding_walls_cleared", 0)
        score = player.get("sounding_score", 0)
        return finish_arcade_session(
            player, "sounding", score,
            f"*** TIME UP! You pinpointed {cleared} hidden wall flaw(s) for {score} points! ***"
        )
    return player, None, "MINIGAME_SOUNDING"


def handle_sounding_event(event, player):
    """Handles mouse clicks on the 4x4 masonry grid."""
    grid_x, grid_y = 480, 182
    cell_size = 44

    if event.type == pygame.MOUSEBUTTONDOWN and not player.get("sounding_recorded"):
        mx, my = event.pos
        if grid_x <= mx < grid_x + 4 * cell_size and grid_y <= my < grid_y + 4 * cell_size:
            cx = (mx - grid_x) // cell_size
            cy = (my - grid_y) // cell_size

            action = "chalk" if event.button == 3 else player.get("sounding_tool", "hammer")

            if action == "chalk":
                player["sounding_chalk"][cy][cx] = not player["sounding_chalk"][cy][cx]
                player["sounding_wiped"] = not any(
                    player["sounding_chalk"][r][c] for r in range(4) for c in range(4)
                )
                return player, None, "MINIGAME_SOUNDING"

            elif action == "hammer":
                if player["sounding_revealed"][cy][cx]:
                    return player, "You already sounded that stone.", "MINIGAME_SOUNDING"

                player["sounding_revealed"][cy][cx] = True
                player["sounding_taps"] += 1
                val = player["sounding_grid"][cy][cx]
                is_final_sector = (not player.get("arcade_mode") and len(player.get("wall_sectors_inspected", [])) == 3)

                if val == 2:
                    if is_final_sector:
                        msg = f"Stone ({cx+1},{cy+1}): CRUNCH! A hollow cavity—and the snapped tip of an iron prybar is wedged in the seam!"
                    else:
                        msg = f"Stone ({cx+1},{cy+1}): THUD! A deep hollow echo. This stone is structurally compromised!"
                elif val == 1:
                    msg = f"Stone ({cx+1},{cy+1}): A muffled vibration (~). The stone is solid, but a flaw lies directly adjacent."
                else:
                    msg = f"Stone ({cx+1},{cy+1}): CLINK! A high, clear ring. Solid granite all around."

                if not player.get("arcade_mode") and player["sounding_taps"] in (8, 9):
                    player["shift_1_mistakes"] = player.get("shift_1_mistakes", 0) + 1
                    msg += f"\n*** CLANG! Your repeated hammering echoes down the street! (+1 Mistake, Total: {player['shift_1_mistakes']}) ***"

                return player, msg, "MINIGAME_SOUNDING"

    return player, None, "MINIGAME_SOUNDING"


def sounding_button_action(action, player):
    """Handles the control buttons beneath the Sounding UI."""
    if action == "toggle_tool":
        player["sounding_tool"] = "chalk" if player.get("sounding_tool") == "hammer" else "hammer"
        return player, f"Switched active left-click tool to: {player['sounding_tool'].title()}.", "MINIGAME_SOUNDING"

    if action == "wipe_chalk":
        player["sounding_chalk"] = [[False] * 4 for _ in range(4)]
        player["sounding_wiped"] = True
        return player, "You scrub the white mason's chalk clean off the stone face.", "MINIGAME_SOUNDING"

    if action == "record_ledger":
        flawed_set = {(x, y) for y in range(4) for x in range(4) if player["sounding_grid"][y][x] == 2}
        chalked_set = {(x, y) for y in range(4) for x in range(4) if player["sounding_chalk"][y][x]}

        # --- ARCADE MODE: INSTANT SCORING & NEXT WALL SPAWN ---
        if player.get("arcade_mode"):
            if chalked_set == flawed_set:
                taps = player.get("sounding_taps", 0)
                bonus = 25 if taps <= 5 else 0
                pts = 100 + bonus
                player["sounding_walls_cleared"] = player.get("sounding_walls_cleared", 0) + 1
                player["sounding_score"] = player.get("sounding_score", 0) + pts
                _spawn_sounding_board(player)
                t_rem = max(0.0, player.get("sounding_time_left", 0.0))
                b_str = " (incl. +25 Low-Tap Bonus!)" if bonus else ""
                return (
                    player,
                    f"*** WALL #{player['sounding_walls_cleared']} CLEARED! +{pts} PTS{b_str} (Total: {player['sounding_score']}p | {t_rem:.1f}s left)! Next wall! ***",
                    "MINIGAME_SOUNDING"
                )
            else:
                player["sounding_time_left"] = max(0.0, player.get("sounding_time_left", 60.0) - 5.0)
                _spawn_sounding_board(player)
                return (
                    player,
                    "*** WRONG CHALK OUTLINE (-5.0s Penalty)! Moving to next wall section... ***",
                    "MINIGAME_SOUNDING"
                )

        # --- STORY MODE ---
        player["sounding_recorded"] = True
        player["sounding_revealed"] = [[True] * 4 for _ in range(4)]

        if chalked_set == flawed_set:
            log = "*** LEDGER UPDATED: You traced the exact boundary of the flaw! Now wipe your chalk before leaving. ***"
        else:
            player["shift_1_mistakes"] = player.get("shift_1_mistakes", 0) + 1
            log = (
                "*** SLOPPY SURVEY: Your chalk outline didn't match the true 3-stone flaw! "
                f"(+1 Mistake, Total: {player['shift_1_mistakes']}) ***\n"
                "Remember to wipe your chalk off the wall before leaving the sector!"
            )
        return player, log, "MINIGAME_SOUNDING"

    if action == "finish_sector":
        sector = player["sounding_sector"]
        log = ""

        if not player.get("sounding_wiped", True):
            player["shift_1_mistakes"] = player.get("shift_1_mistakes", 0) + 1
            log += (
                "*** CARELESS EXIT: You walked away leaving white chalk marks on the masonry! "
                f"(+1 Mistake, Total: {player['shift_1_mistakes']}) ***\n"
            )

        if sector not in player["wall_sectors_inspected"]:
            player["wall_sectors_inspected"].append(sector)

        done_count = len(player["wall_sectors_inspected"])
        if done_count < 4:
            remaining = [s.title() for s in ["north", "west", "south", "east"] if s not in player["wall_sectors_inspected"]]
            log += f"Sector inspection complete ({done_count}/4). Remaining sectors: {', '.join(remaining)}."
        else:
            log += (
                "*** ALL 4 SECTORS INSPECTED! ***\n"
                "On this final stretch of wall, you uncovered a FAILED BREAK-IN—hollowed stones and a snapped prybar tip!\n"
                "Return to Wellspring at the Wallmakers' Offices immediately!"
            )
        return player, log, "MAIN"

    return player, None, "MINIGAME_SOUNDING"


def draw_sounding_ui(screen, player, font, font_bold):
    """Draws the 4x4 masonry inspection grid and acoustic legend."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    if player.get("arcade_mode"):
        t_left = max(0.0, player.get("sounding_time_left", 60.0))
        pts = player.get("sounding_score", 0)
        title_surf = font_bold.render(f"SOUNDING RUSH: {t_left:04.1f}s ({pts}p)", True, LOCATION_ACCENT)
        screen.blit(title_surf, (472, 148))
    else:
        sector_title = player.get("sounding_sector", "wall").upper()
        title_surf = font_bold.render(f"SOUNDING: {sector_title} WALL", True, LOCATION_ACCENT)
        screen.blit(title_surf, (475, 148))

    taps = player.get("sounding_taps", 0)
    tap_color = TEXT_COLOR if taps <= 7 else (220, 80, 80)
    tap_surf = font.render(f"Taps: {taps}", True, tap_color)
    screen.blit(tap_surf, (705, 148))

    grid_x, grid_y = 480, 182
    cell_size = 44

    for y in range(4):
        for x in range(4):
            rect = pygame.Rect(grid_x + x * cell_size, grid_y + y * cell_size, cell_size - 2, cell_size - 2)
            revealed = player["sounding_revealed"][y][x]
            val = player["sounding_grid"][y][x]

            if not revealed:
                color = (65, 72, 84)
                symbol = ""
            elif val == 2:
                color = (185, 65, 65)
                symbol = "!"
            elif val == 1:
                color = (165, 140, 70)
                symbol = "~"
            else:
                color = (70, 115, 85)
                symbol = "."

            pygame.draw.rect(screen, color, rect, border_radius=4)
            pygame.draw.rect(screen, (30, 35, 45), rect, width=1, border_radius=4)

            if symbol:
                sym_surf = font_bold.render(symbol, True, TEXT_COLOR)
                screen.blit(sym_surf, (rect.centerx - sym_surf.get_width() // 2, rect.centery - sym_surf.get_height() // 2))

            if player["sounding_chalk"][y][x]:
                pygame.draw.rect(screen, (245, 245, 255), rect.inflate(-4, -4), width=3, border_radius=3)

    lx = 665
    screen.blit(font_bold.render("Key:", True, TEXT_MUTED), (lx, 185))
    screen.blit(font.render("[!] Flaw", True, (220, 100, 100)), (lx, 210))
    screen.blit(font.render("[~] Near", True, (210, 185, 100)), (lx, 232))
    screen.blit(font.render("[.] Solid", True, (110, 175, 130)), (lx, 254))
    screen.blit(font.render("[ ] Chalk", True, (245, 245, 255)), (lx, 276))

    if player.get("arcade_mode"):
        cleared = player.get("sounding_walls_cleared", 0)
        screen.blit(font.render(f"Cleared: {cleared}", True, (110, 215, 140)), (lx, 315))
    else:
        mistakes = player.get("shift_1_mistakes", 0)
        m_surf = font.render(f"Mistakes: {mistakes}", True, (220, 80, 80) if mistakes > 0 else TEXT_MUTED)
        screen.blit(m_surf, (lx, 315))

# ==========================================
# WALLMAKERS SHIFT 2: PENTOMINO BREACH REPAIR
# ==========================================

def init_breach_minigame(player):
    """Initializes the 5x5 Load-Bearing Pentomino Breach puzzle."""
    player["breach_grid"] = [[0] * 5 for _ in range(5)]
    player["breach_selected"] = None
    player["breach_scrapes_left"] = 2

    # 5 distinct Pentominoes (V, N, U, P, Y) that tile the 5x5 breach from the bottom up:
    # Solved Layout Reference (y=0 top .. y=4 bottom):
    #   y=0:  4  4  3  3  5
    #   y=1:  4  4  3  5  5
    #   y=2:  1  4  3  3  5   <-- (2,2) is [C] covered by Piece 3 (U-Hollow Core)
    #   y=3:  1  2  2  2  5
    #   y=4:  1  1  1  2  2   <-- Bottom row supported by Granite Pieces 1 (V) & 2 (N)
    pieces = [
        {
            "id": 1, "name": "V-Granite", "granite": True, "hollow": False,
            "shape": [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
            "color": (95, 105, 120), "placed": False
        },
        {
            "id": 2, "name": "N-Granite", "granite": True, "hollow": False,
            "shape": [(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)],
            "color": (115, 125, 140), "placed": False
        },
        {
            "id": 3, "name": "U-Hollow", "granite": False, "hollow": True,
            "shape": [(0, 0), (1, 0), (0, 1), (0, 2), (1, 2)],
            "color": (195, 115, 70), "placed": False
        },
        {
            "id": 4, "name": "P-Arch", "granite": False, "hollow": False,
            "shape": [(0, 0), (1, 0), (0, 1), (1, 1), (1, 2)],
            "color": (165, 145, 105), "placed": False
        },
        {
            "id": 5, "name": "Y-Keystone", "granite": False, "hollow": False,
            "shape": [(1, 0), (0, 1), (1, 1), (1, 2), (1, 3)],
            "color": (210, 180, 110), "placed": False
        }
    ]

    # Rotate pieces so the player must orient them before laying courses
    for idx, p in enumerate(pieces):
        for _ in range((idx % 3) + 1):
            p["shape"] = rotate_shape(p["shape"])

    player["breach_pieces"] = pieces

    log = (
        "--- SHIFT 2: REPAIRING THE EAST WALL BREACH ---\n"
        "As you clear the shattered masonry, your fingers strike a lead cylinder wedged in the central cavity: "
        "you found a SMUGGLER'S CIPHER!\n\n"
        "MASONRY RULES:\n"
        "  • Build from the bottom up (every stone must touch the floor or rest on a placed stone).\n"
        "  • Only heavy Granite (V-Granite & N-Granite) can sit on the bottom row without cracking.\n"
        "  • Cover the central Cavity [C] with the copper U-Hollow stone!\n"
        "(Left-Click palette/grid to Pick Up/Place, Right-Click to Rotate)"
    )
    return player, log, "MINIGAME_BREACH"


def handle_breach_event(event, player):
    """Handles picking up, rotating, placing, and scraping Pentomino stones."""
    grid_x, grid_y = 472, 182
    cell_size = 38
    palette_x, palette_y = 680, 175

    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos

        # Right-Click rotates the currently held stone
        if event.button == 3 and player.get("breach_selected") is not None:
            p_idx = player["breach_selected"]
            player["breach_pieces"][p_idx]["shape"] = rotate_shape(player["breach_pieces"][p_idx]["shape"])
            return player, None, "MINIGAME_BREACH"

        # Left-Click to Pick Up / Place / Drop
        if event.button == 1:
            # 1. Clicked inside the 5x5 Breach Grid
            if grid_x <= mx < grid_x + 5 * cell_size and grid_y <= my < grid_y + 5 * cell_size:
                cx = (mx - grid_x) // cell_size
                cy = (my - grid_y) // cell_size

                if player.get("breach_selected") is not None:
                    p_idx = player["breach_selected"]
                    piece = player["breach_pieces"][p_idx]
                    anchor_x = min(px for px, py in piece["shape"] if py == 0)

                    # Verify all 5 squares fit inside the 5x5 grid and don't overlap
                    coords = []
                    for px, py in piece["shape"]:
                        nx, ny = cx + (px - anchor_x), cy + py
                        if nx < 0 or nx >= 5 or ny < 0 or ny >= 5 or player["breach_grid"][ny][nx] != 0:
                            return player, "That stone does not fit there.", "MINIGAME_BREACH"
                        coords.append((nx, ny))

                    # Place the stone into the grid
                    for nx, ny in coords:
                        player["breach_grid"][ny][nx] = piece["id"]
                    piece["placed"] = True
                    player["breach_selected"] = None

                    # --- MASONRY PHYSICS & MISTAKE CHECKS ---
                    warnings = []

                    # Check 1: Gravity / Support (must touch y==4 OR have a non-zero block at ny+1)
                    has_support = False
                    for nx, ny in coords:
                        if ny == 4 or (ny + 1 < 5 and player["breach_grid"][ny + 1][nx] not in (0, piece["id"])):
                            has_support = True
                            break
                    if not has_support:
                        player["shift_2_mistakes"] = player.get("shift_2_mistakes", 0) + 1
                        warnings.append(
                            f"*** UNSUPPORTED OVERHANG! {piece['name']} sags in the wet mortar! "
                            f"(+1 Mistake, Total: {player['shift_2_mistakes']}) ***"
                        )

                    # Check 2: Load-Bearing Foundation (Bottom row y==4 requires Granite)
                    touches_bottom = any(ny == 4 for _, ny in coords)
                    if touches_bottom and not piece["granite"]:
                        player["shift_2_mistakes"] = player.get("shift_2_mistakes", 0) + 1
                        warnings.append(
                            f"*** WEAK FOUNDATION! {piece['name']} cracks under the bottom-row load! "
                            f"(+1 Mistake, Total: {player['shift_2_mistakes']}) ***"
                        )

                    # Check 3: Central Cavity (2, 2) must be covered by the U-Hollow stone
                    if (2, 2) in coords and not piece["hollow"]:
                        player["shift_2_mistakes"] = player.get("shift_2_mistakes", 0) + 1
                        warnings.append(
                            f"*** BLOCKED CAVITY! You covered the central niche [C] with solid {piece['name']} instead of U-Hollow! "
                            f"(+1 Mistake, Total: {player['shift_2_mistakes']}) ***"
                        )

                    # Check Win Condition (All 5 stones placed)
                    if all(p["placed"] for p in player["breach_pieces"]):
                        player["active_wallmaker_task"] = "report_breach_repair"
                        msg = "\n".join(warnings) + ("\n" if warnings else "")
                        msg += (
                            "*** BREACH SEALED! ***\n"
                            "You wipe the excess mortar from the joints. To a passing guard, the East Wall looks solid—yet the "
                            "keystone locks a hidden chamber right inside the masonry.\n"
                            "Return to Wellspring at the Wallmakers' Offices!"
                        )
                        return player, msg, "MAIN"

                    log_msg = "\n".join(warnings) if warnings else f"You bed the {piece['name']} into the mortar."
                    return player, log_msg, "MINIGAME_BREACH"

                else:
                    # Pick up an already-placed stone from the grid (uses a Trowel Scrape)
                    cell_val = player["breach_grid"][cy][cx]
                    if cell_val != 0:
                        for y in range(5):
                            for x in range(5):
                                if player["breach_grid"][y][x] == cell_val:
                                    player["breach_grid"][y][x] = 0
                        for i, p in enumerate(player["breach_pieces"]):
                            if p["id"] == cell_val:
                                p["placed"] = False
                                player["breach_selected"] = i
                                break

                        if player["breach_scrapes_left"] > 0:
                            player["breach_scrapes_left"] -= 1
                            msg = f"You pry the stone loose and scrape off the wet mortar. (Free Scrapes left: {player['breach_scrapes_left']})"
                        else:
                            player["shift_2_mistakes"] = player.get("shift_2_mistakes", 0) + 1
                            msg = (
                                "*** SLOPPY MORTAR: Prying out another stone scatters fresh mortar dust across the weeds! "
                                f"(+1 Mistake, Total: {player['shift_2_mistakes']}) ***"
                            )
                        return player, msg, "MINIGAME_BREACH"

            # 2. Clicked in the Right-Hand Stone Palette
            elif palette_x - 10 <= mx <= palette_x + 95:
                for i, p in enumerate(player["breach_pieces"]):
                    if not p["placed"]:
                        by = palette_y + i * 42
                        if by - 5 <= my <= by + 36:
                            player["breach_selected"] = i
                            return player, f"Selected {p['name']} ({'Granite Base' if p['granite'] else 'Hollow Core' if p['hollow'] else 'Upper Course'}).", "MINIGAME_BREACH"

            # 3. Clicked outside the grid while holding a piece -> Deselect
            elif player.get("breach_selected") is not None:
                player["breach_selected"] = None

    return player, None, "MINIGAME_BREACH"


def breach_button_action(action, player):
    """Handles helper buttons below the Pentomino Breach overlay."""
    if action == "rotate":
        if player.get("breach_selected") is not None:
            p_idx = player["breach_selected"]
            player["breach_pieces"][p_idx]["shape"] = rotate_shape(player["breach_pieces"][p_idx]["shape"])
            return player, None, "MINIGAME_BREACH"
        return player, "Select a stone from the palette first to rotate it.", "MINIGAME_BREACH"

    if action == "inspect_niche":
        log = (
            "--- MASON'S ARCHITECTURAL NOTE ---\n"
            "• Bottom Row (Row 5): Place V-Granite on the bottom-left and N-Granite on the bottom-right.\n"
            "• Middle/Top Courses: Fit P-Arch on the upper-left, U-Hollow over the center [C], and Y-Keystone on the right!"
        )
        return player, log, "MINIGAME_BREACH"

    return player, None, "MINIGAME_BREACH"


def draw_breach_ui(screen, player, font, font_bold):
    """Draws the 5x5 Pentomino Breach grid, central [C] marker, palette, and snapped hover ghost."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    title_surf = font_bold.render("SEAL THE WALL BREACH", True, LOCATION_ACCENT)
    screen.blit(title_surf, (472, 148))

    mistakes = player.get("shift_2_mistakes", 0)
    m_color = (220, 80, 80) if mistakes > 0 else TEXT_MUTED
    screen.blit(font.render(f"Mistakes: {mistakes}", True, m_color), (680, 148))

    grid_x, grid_y = 472, 178
    cell_size = 38

    # Draw 5x5 Breach Grid
    for y in range(5):
        for x in range(5):
            rect = pygame.Rect(grid_x + x * cell_size, grid_y + y * cell_size, cell_size, cell_size)
            bg_col = (35, 30, 30) if y == 4 else (20, 25, 30)
            pygame.draw.rect(screen, bg_col, rect)
            pygame.draw.rect(screen, PANEL_BORDER, rect, 1)

            # Highlight bottom load-bearing row and central cavity (2, 2)
            val = player["breach_grid"][y][x]
            if val == 0:
                if x == 2 and y == 2:
                    c_surf = font_bold.render("[C]", True, (220, 130, 80))
                    screen.blit(c_surf, (rect.centerx - c_surf.get_width() // 2, rect.centery - c_surf.get_height() // 2))
                elif y == 4:
                    b_surf = font.render("BASE", True, (80, 85, 95))
                    screen.blit(b_surf, (rect.centerx - b_surf.get_width() // 2, rect.centery - b_surf.get_height() // 2))
            else:
                for p in player["breach_pieces"]:
                    if p["id"] == val:
                        pygame.draw.rect(screen, p["color"], rect.inflate(-2, -2), border_radius=3)
                        if x == 2 and y == 2 and p["hollow"]:
                            h_surf = font_bold.render("O", True, (255, 230, 180))
                            screen.blit(h_surf, (rect.centerx - h_surf.get_width() // 2, rect.centery - h_surf.get_height() // 2))
                        break

    # Draw Stone Palette on the right
    palette_x, palette_y = 682, 174
    p_cell = 8
    for i, p in enumerate(player["breach_pieces"]):
        if not p["placed"]:
            px, py = palette_x, palette_y + i * 41
            if player.get("breach_selected") == i:
                pygame.draw.rect(screen, LOCATION_ACCENT, (px - 4, py - 3, 88, 36), 1, border_radius=4)

            for bx, by in p["shape"]:
                r = pygame.Rect(px + bx * p_cell, py + by * p_cell, p_cell, p_cell)
                pygame.draw.rect(screen, p["color"], r)
                pygame.draw.rect(screen, (15, 20, 25), r, 1)

            lbl = font.render(p["name"][:6], True, TEXT_MUTED)
            screen.blit(lbl, (px + 36, py + 6))

    # Draw Snapped Ghost Preview on Grid (or at Cursor if outside grid)
    if player.get("breach_selected") is not None:
        mx, my = pygame.mouse.get_pos()
        p = player["breach_pieces"][player["breach_selected"]]
        if grid_x <= mx < grid_x + 5 * cell_size and grid_y <= my < grid_y + 5 * cell_size:
            cx = (mx - grid_x) // cell_size
            cy = (my - grid_y) // cell_size
            anchor_x = min(px for px, py in p["shape"] if py == 0)
            for bx, by in p["shape"]:
                nx, ny = cx + (bx - anchor_x), cy + by
                if 0 <= nx < 5 and 0 <= ny < 5:
                    r = pygame.Rect(grid_x + nx * cell_size, grid_y + ny * cell_size, cell_size, cell_size)
                    pygame.draw.rect(screen, p["color"], r.inflate(-4, -4), width=3, border_radius=3)
        else:
            for bx, by in p["shape"]:
                r = pygame.Rect(mx + bx * 24, my + by * 24, 24, 24)
                pygame.draw.rect(screen, p["color"], r)
                pygame.draw.rect(screen, (255, 255, 255), r, 1)

# ==========================================
# WALLMAKERS SHIFT 3: THE LOST DAMAGE REPORT
# ==========================================

SURVEYORS = ["Steadfast", "Plumbline", "Truelevel", "Hardstone"]
WALL_LOCS = ["Sluice Gate", "North Tower", "Market Wall", "West Bastion"]
DAMAGE_TYPES = ["Rusted Grate", "Loose Merlon", "Weeping Mortar", "Frost Subsidence"]

# True Solution Index Mapping:
# Row 0 (Steadfast): Sluice Gate (0), Rusted Grate (0)
# Row 1 (Plumbline): North Tower (1), Loose Merlon (1)
# Row 2 (Truelevel): Market Wall (2), Weeping Mortar (2)
# Row 3 (Hardstone): West Bastion (3), Frost Subsidence (3)
TRUE_LEDGER = [(0, 0), (1, 1), (2, 2), (3, 3)]


def init_deduction_minigame(player):
    """Initializes the 4x4x4 Surveyor Logic Grid in the Wallmakers' Offices."""
    # Start with a scrambled board so the player must deduce the pairings
    player["deduction_locs"] = [2, 3, 1, 0]
    player["deduction_dmgs"] = [3, 2, 0, 1]
    player["deduction_phase"] = "deduce"   # "deduce" -> "sabotage"
    player["deduction_swap_sel"] = None
    player["sabotaged_route"] = "through"  # Default if no swap is made

    log = (
        "--- SHIFT 3: THE LOST DAMAGE REPORT ---\n"
        "Four surveyors left their unlabelled chits scattered across the drafting table.\n"
        "1. Click [Inspect Cubbies] and [Read Field Notes] to gather the clues.\n"
        "2. Click any Location or Damage chit on the board to cycle it (Left-Click: Next, Right-Click: Previous).\n"
        "3. Once all 4 surveyors are matched to their true Location and Damage, click [Verify True Ledger]!"
    )
    return player, log, "MINIGAME_DEDUCTION"


def handle_deduction_event(event, player):
    """Handles clicking Location and Damage chits on the 4-row board."""
    if event.type != pygame.MOUSEBUTTONDOWN:
        return player, None, "MINIGAME_DEDUCTION"

    mx, my = event.pos
    phase = player.get("deduction_phase", "deduce")

    # Row geometry inside the 460..780 panel
    start_y = 198
    row_h = 38
    loc_x, loc_w = 548, 108
    dmg_x, dmg_w = 662, 110

    for row in range(4):
        ry = start_y + row * row_h
        if ry <= my <= ry + 32:
            step = -1 if event.button == 3 else 1

            # PHASE 1: Cycle Location or Damage Chits to solve the logic puzzle
            if phase == "deduce":
                if loc_x <= mx <= loc_x + loc_w:
                    player["deduction_locs"][row] = (player["deduction_locs"][row] + step) % 4
                    return player, None, "MINIGAME_DEDUCTION"
                elif dmg_x <= mx <= dmg_x + dmg_w:
                    player["deduction_dmgs"][row] = (player["deduction_dmgs"][row] + step) % 4
                    return player, None, "MINIGAME_DEDUCTION"

            # PHASE 2: Click two Damage Chits to swap them (Sabotage)
            elif phase == "sabotage":
                if dmg_x <= mx <= dmg_x + dmg_w:
                    sel = player.get("deduction_swap_sel")
                    if sel is None:
                        player["deduction_swap_sel"] = row
                        return player, f"Selected {WALL_LOCS[row]}'s '{DAMAGE_TYPES[player['deduction_dmgs'][row]]}' chit to swap...", "MINIGAME_DEDUCTION"
                    elif sel == row:
                        player["deduction_swap_sel"] = None
                        return player, "Deselected chit.", "MINIGAME_DEDUCTION"
                    else:
                        # Swap the two damage chits
                        d1, d2 = player["deduction_dmgs"][sel], player["deduction_dmgs"][row]
                        player["deduction_dmgs"][sel], player["deduction_dmgs"][row] = d2, d1
                        player["deduction_swap_sel"] = None
                        msg = (
                            f"Swapped Damage Chits between {WALL_LOCS[sel]} and {WALL_LOCS[row]}!\n"
                            f"  • {WALL_LOCS[sel]} now lists: {DAMAGE_TYPES[player['deduction_dmgs'][sel]]}\n"
                            f"  • {WALL_LOCS[row]} now lists: {DAMAGE_TYPES[player['deduction_dmgs'][row]]}"
                        )
                        return player, msg, "MINIGAME_DEDUCTION"

    return player, None, "MINIGAME_DEDUCTION"


def deduction_button_action(action, player):
    """Handles clue buttons, verification, and sabotage submission."""
    if action == "cubbies":
        log = (
            "--- CLUES: THE SURVEYORS' CUBBIES ---\n"
            "• STEADFAST's waders are soaked in river-culvert muck; he inspected the SLUICE GATE.\n"
            "• TRUELEVEL's coat reeks of fishmonger brine and rotten cabbage from the MARKET WALL.\n"
            "• HARDSTONE suffers from terrible vertigo and refuses to climb the high NORTH TOWER."
        )
        return player, log, "MINIGAME_DEDUCTION"

    if action == "notes":
        log = (
            "--- CLUES: TORN FIELD NOTES ---\n"
            "• 'Whoever climbed the NORTH TOWER found a LOOSE MERLON on the battlements (an ideal Over-Wall rope point).'\n"
            "• 'HARDSTONE logged severe FROST SUBSIDENCE cracking the lower foundation stones.'\n"
            "• 'The MARKET WALL has minor WEEPING MORTAR, while the RUSTED GRATE was found in the flooded culvert.'"
        )
        return player, log, "MINIGAME_DEDUCTION"

    if action == "verify":
        correct_rows = 0
        for r in range(4):
            if (player["deduction_locs"][r], player["deduction_dmgs"][r]) == TRUE_LEDGER[r]:
                correct_rows += 1

        if correct_rows == 4:
            player["deduction_phase"] = "sabotage"
            log = (
                "*** LEDGER RECONSTRUCTED! ***\n"
                "You have uncovered all the vulnerabilities:\n"
                "  • Sluice Gate has a RUSTED GRATE (Opens the 'Under the Wall' smuggling route).\n"
                "  • North Tower has a LOOSE MERLON (Opens the 'Over the Wall' smuggling route).\n\n"
                "--- OPTIONAL SABOTAGE (PHASE 2) ---\n"
                "If you submit this true ledger, repair crews will seal both the Rusted Grate and Loose Merlon!\n"
                "To keep ONE route open for Shift 5, click its Damage Chit and swap it with a routine flaw "
                "(Weeping Mortar or Frost Subsidence), then click [Submit Final Ledger]!"
            )
            return player, log, "MINIGAME_DEDUCTION"
        else:
            player["shift_3_mistakes"] = player.get("shift_3_mistakes", 0) + 1
            log = (
                f"*** INCORRECT DEDUCTION ({correct_rows}/4 rows accurate)! ***\n"
                "You scratch out the wrong entries, leaving messy ink smudges on the ledger. "
                f"(+1 Mistake, Total: {player['shift_3_mistakes']})\n"
                "Re-read the Cubbies and Field Notes carefully!"
            )
            return player, log, "MINIGAME_DEDUCTION"

    if action == "reset_sabotage":
        player["deduction_dmgs"] = [0, 1, 2, 3]
        player["deduction_swap_sel"] = None
        return player, "Reset Damage Chits back to the true 4x4x4 pairings.", "MINIGAME_DEDUCTION"

    if action == "submit_final":
        dmgs = player["deduction_dmgs"]
        warnings = []

        # Count how many rows differ from the true damage assignment [0, 1, 2, 3]
        changed_rows = [r for r in range(4) if dmgs[r] != r]

        if len(changed_rows) == 0:
            # No swap made: both Sluice Gate and North Tower get repaired; only Through-Wall (Shift 2 cavity) remains
            player["sabotaged_route"] = "through"
            result_note = "You left the ledger completely accurate. Crews will reinforce the Sluice Gate and North Tower, leaving your East Wall hollow stone as the primary route."

        elif len(changed_rows) > 2:
            # Swapped too many chits—looks completely scrambled!
            player["shift_3_mistakes"] = player.get("shift_3_mistakes", 0) + 1
            player["sabotaged_route"] = "through"
            warnings.append(
                f"*** OBVIOUS TAMPERING! You scrambled {len(changed_rows)} sectors on the board! "
                f"(+1 Mistake, Total: {player['shift_3_mistakes']}) ***"
            )
            result_note = "The suspiciously scrambled board will draw extra scrutiny."

        else:
            # Exactly 2 chits swapped: check if they swapped Sluice Gate (0) and North Tower (1) directly with each other!
            if set(changed_rows) == {0, 1}:
                player["shift_3_mistakes"] = player.get("shift_3_mistakes", 0) + 1
                player["sabotaged_route"] = "under"
                warnings.append(
                    "*** ABSURD CONTRADICTION! You reported a flooded 'Rusted Grate' on the roof of the North Watchtower! "
                    f"(+1 Mistake, Total: {player['shift_3_mistakes']}) ***"
                )
                result_note = "The Sluice Gate and North Tower reports are swapped, though a sharp clerk might notice the contradiction."
            elif 0 in changed_rows:
                player["sabotaged_route"] = "under"
                result_note = "Clever swap! You diverted the repair crew away from the SLUICE GATE, keeping the 'Under the Wall' route wide open!"
            elif 1 in changed_rows:
                player["sabotaged_route"] = "over"
                result_note = "Clever swap! You diverted the mason crew away from the NORTH TOWER, keeping the 'Over the Wall' route wide open!"
            else:
                player["sabotaged_route"] = "through"
                result_note = "You swapped the two routine sectors, leaving the main smuggling routes to be repaired except for your East Wall cavity."

        player["active_wallmaker_task"] = "report_damage_ledger"
        log = ("\n".join(warnings) + "\n" if warnings else "") + (
            f"*** DAMAGE LEDGER LOCKED IN! ***\n{result_note}\n"
            "Speak to Wellspring ('Return from Task') to hand in the ledger and collect your wages!"
        )
        return player, log, "MAIN"

    return player, None, "MINIGAME_DEDUCTION"


def draw_deduction_ui(screen, player, font, font_bold):
    """Draws the 4x4x4 Surveyor Deduction Board inside the 460..780 panel."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    phase = player.get("deduction_phase", "deduce")
    header = "PHASE 1: DEDUCE LEDGER" if phase == "deduce" else "PHASE 2: SWAP 2 DMG CHITS"
    screen.blit(font_bold.render(header, True, LOCATION_ACCENT), (470, 148))

    mistakes = player.get("shift_3_mistakes", 0)
    m_col = (220, 80, 80) if mistakes > 0 else TEXT_MUTED
    screen.blit(font.render(f"Mistakes: {mistakes}", True, m_col), (685, 148))

    screen.blit(font.render("Surveyor", True, TEXT_MUTED), (468, 174))
    screen.blit(font.render("Wall Sector", True, TEXT_MUTED), (552, 174))
    screen.blit(font.render("Damage Type", True, TEXT_MUTED), (666, 174))

    start_y = 198
    row_h = 38
    loc_x, loc_w = 548, 108
    dmg_x, dmg_w = 662, 110

    for r in range(4):
        ry = start_y + r * row_h

        s_surf = font_bold.render(SURVEYORS[r], True, TEXT_COLOR)
        screen.blit(s_surf, (468, ry + 7))

        loc_idx = player["deduction_locs"][r]
        loc_rect = pygame.Rect(loc_x, ry, loc_w, 32)
        loc_bg = (45, 60, 75) if phase == "deduce" else (30, 38, 46)
        pygame.draw.rect(screen, loc_bg, loc_rect, border_radius=4)
        pygame.draw.rect(screen, PANEL_BORDER, loc_rect, width=1, border_radius=4)
        draw_fitted_text(screen, WALL_LOCS[loc_idx], loc_rect, TEXT_COLOR if phase == "deduce" else TEXT_MUTED)

        dmg_idx = player["deduction_dmgs"][r]
        dmg_rect = pygame.Rect(dmg_x, ry, dmg_w, 32)
        is_selected = (phase == "sabotage" and player.get("deduction_swap_sel") == r)
        is_swapped = (phase == "sabotage" and dmg_idx != r)

        if is_selected:
            dmg_bg = (140, 100, 45)
        elif is_swapped:
            dmg_bg = (115, 55, 55)
        else:
            dmg_bg = (65, 50, 70)

        pygame.draw.rect(screen, dmg_bg, dmg_rect, border_radius=4)
        border_col = LOCATION_ACCENT if is_selected else PANEL_BORDER
        pygame.draw.rect(screen, border_col, dmg_rect, width=2 if is_selected else 1, border_radius=4)
        draw_fitted_text(screen, DAMAGE_TYPES[dmg_idx], dmg_rect, TEXT_COLOR)

    hint = "Click chits to cycle (L/R Click)" if phase == "deduce" else "Click two Damage Chits to swap them"
    screen.blit(font.render(hint, True, TEXT_MUTED), (470, 358))

# ==========================================
# WALLMAKERS SHIFT 4: SECRET STAIRS & PARAPET CACHE
# ==========================================

STAIR_LAYOUT = ["cant", "slit", "cant", "slit", "slit", "cant", "slit", "cant"]


def init_parapet_minigame(player):
    """Initializes Stage 1 (Secret Stairs Lantern Discipline) & Stage 2 (Sliding-Stone Cache)."""
    player["parapet_phase"] = "stairs"
    player["stair_step"] = 0
    player["lantern_open"] = True

    if player.get("arcade_mode"):
        player["stair_layout"] = [random.choice(["cant", "slit"]) for _ in range(8)]
        klotski_variants = [
            [
                {"id": 1, "name": "SILK",  "cells": [(0, 1), (1, 1)], "orient": "H", "color": (215, 175, 65)},
                {"id": 2, "name": "Pin-A", "cells": [(2, 0), (2, 1)], "orient": "V", "color": (100, 110, 125)},
                {"id": 3, "name": "Pin-B", "cells": [(3, 1), (3, 2)], "orient": "V", "color": (120, 130, 145)},
                {"id": 4, "name": "Bar-C", "cells": [(0, 2), (1, 2)], "orient": "H", "color": (90, 100, 115)},
                {"id": 5, "name": "Bar-D", "cells": [(1, 3), (2, 3)], "orient": "H", "color": (110, 120, 135)},
            ],
            [
                {"id": 1, "name": "SILK",  "cells": [(0, 1), (1, 1)], "orient": "H", "color": (215, 175, 65)},
                {"id": 2, "name": "Pin-A", "cells": [(2, 1), (2, 2)], "orient": "V", "color": (100, 110, 125)},
                {"id": 3, "name": "Pin-B", "cells": [(3, 0), (3, 1)], "orient": "V", "color": (120, 130, 145)},
                {"id": 4, "name": "Bar-C", "cells": [(1, 0), (2, 0)], "orient": "H", "color": (90, 100, 115)},
                {"id": 5, "name": "Bar-D", "cells": [(0, 3), (1, 3)], "orient": "H", "color": (110, 120, 135)},
            ],
            [
                {"id": 1, "name": "SILK",  "cells": [(0, 1), (1, 1)], "orient": "H", "color": (215, 175, 65)},
                {"id": 2, "name": "Pin-A", "cells": [(2, 0), (2, 1)], "orient": "V", "color": (100, 110, 125)},
                {"id": 3, "name": "Pin-B", "cells": [(3, 1), (3, 2)], "orient": "V", "color": (120, 130, 145)},
                {"id": 4, "name": "Bar-C", "cells": [(1, 2), (2, 2)], "orient": "H", "color": (90, 100, 115)},
                {"id": 5, "name": "Bar-D", "cells": [(0, 3), (1, 3)], "orient": "H", "color": (110, 120, 135)},
            ],
        ]
        chosen = copy.deepcopy(random.choice(klotski_variants))
        player["klotski_blocks"] = chosen
        player["klotski_initial"] = copy.deepcopy(chosen)
    else:
        player["stair_layout"] = list(STAIR_LAYOUT)
        default_blocks = [
            {"id": 1, "name": "SILK",  "cells": [(0, 1), (1, 1)], "orient": "H", "color": (215, 175, 65)},
            {"id": 2, "name": "Pin-A", "cells": [(2, 0), (2, 1)], "orient": "V", "color": (100, 110, 125)},
            {"id": 3, "name": "Pin-B", "cells": [(3, 1), (3, 2)], "orient": "V", "color": (120, 130, 145)},
            {"id": 4, "name": "Bar-C", "cells": [(0, 2), (1, 2)], "orient": "H", "color": (90, 100, 115)},
            {"id": 5, "name": "Bar-D", "cells": [(1, 3), (2, 3)], "orient": "H", "color": (110, 120, 135)},
        ]
        player["klotski_blocks"] = copy.deepcopy(default_blocks)
        player["klotski_initial"] = copy.deepcopy(default_blocks)

    player["klotski_selected"] = None
    player["klotski_slides"] = 0

    log = (
        "--- SHIFT 4 (STAGE 1): THE SECRET WALL STAIRS ---\n"
        "You unlock the hidden mason's postern behind the Tavern and step into the hollow stone shaft.\n"
        "LANTERN DISCIPLINE:\n"
        "  • Check the NEXT step above you before clicking [Climb Next Step >>]!\n"
        "  • If the next step is [SLIT] (Arrow Slit), CLOSE your lantern shutter or patrols outside will see the light!\n"
        "  • If the next step is [CANT] (Dark Rubble & Thieves' Cant), OPEN your shutter to read the chalk and avoid tripping!"
    )
    return player, log, "MINIGAME_PARAPET"


def handle_parapet_event(event, player):
    """Handles mouse clicks for the Stage 2 4x4 Sliding-Stone Cache puzzle."""
    if event.type != pygame.MOUSEBUTTONDOWN or player.get("parapet_phase") != "klotski":
        return player, None, "MINIGAME_PARAPET"

    grid_x, grid_y = 478, 182
    cell_size = 44
    mx, my = event.pos

    if grid_x <= mx < grid_x + 4 * cell_size and grid_y <= my < grid_y + 4 * cell_size:
        cx = (mx - grid_x) // cell_size
        cy = (my - grid_y) // cell_size

        blocks = player["klotski_blocks"]
        occupied = {}
        for idx, b in enumerate(blocks):
            for bx, by in b["cells"]:
                occupied[(bx, by)] = idx

        if (cx, cy) in occupied:
            sel_idx = occupied[(cx, cy)]
            player["klotski_selected"] = sel_idx
            return player, f"Selected {blocks[sel_idx]['name']}. Click an adjacent empty space in line with the block to slide it.", "MINIGAME_PARAPET"

        sel_idx = player.get("klotski_selected")
        if sel_idx is not None:
            b = blocks[sel_idx]
            cells = b["cells"]
            dx, dy = 0, 0

            if b["orient"] == "H":
                row_y = cells[0][1]
                min_x = min(c[0] for c in cells)
                max_x = max(c[0] for c in cells)
                if cy == row_y:
                    if cx == min_x - 1:
                        dx = -1
                    elif cx == max_x + 1:
                        dx = 1
            else:
                col_x = cells[0][0]
                min_y = min(c[1] for c in cells)
                max_y = max(c[1] for c in cells)
                if cx == col_x:
                    if cy == min_y - 1:
                        dy = -1
                    elif cy == max_y + 1:
                        dy = 1

            if dx != 0 or dy != 0:
                new_cells = [(x + dx, y + dy) for x, y in cells]
                if all(0 <= nx < 4 and 0 <= ny < 4 and ((nx, ny) not in occupied or occupied.get((nx, ny)) == sel_idx) for nx, ny in new_cells):
                    b["cells"] = new_cells
                    player["klotski_slides"] += 1
                    msg = f"Slid {b['name']} ({player['klotski_slides']}/10 quiet slides)."

                    if player["klotski_slides"] in (11, 13):
                        player["shift_4_mistakes"] = player.get("shift_4_mistakes", 0) + 1
                        msg += f"\n*** GRIND! The heavy stone pin scrapes loudly against the parapet! (+1 Mistake, Total: {player['shift_4_mistakes']}) ***"

                    if b["id"] == 1 and set(b["cells"]) == {(2, 1), (3, 1)}:
                        if player.get("arcade_mode"):
                            score = max(10, 150 - (player.get("klotski_slides", 5) * 10) - (player.get("shift_4_mistakes", 0) * 20))
                            return finish_arcade_session(player, "parapet", score, f"Arcade Practice: Cache extracted in {player['klotski_slides']} slides!")

                        if "contraband silk cache" not in player["inventory"]:
                            player["inventory"].append("contraband silk cache")
                        player["active_wallmaker_task"] = "report_parapet_walk"
                        msg += (
                            "\n\n*** CONTRABAND CACHE EXTRACTED! ***\n"
                            "The locking pins clear the recess, and you slide the oilskin Contraband Silk Cache cleanly into your pack without breaking its wax seal!\n"
                            "Return to Wellspring at the Wallmakers' Offices!"
                        )
                        return player, msg, "MAIN"

                    return player, msg, "MINIGAME_PARAPET"

            return player, "Stone pins can only slide lengthwise into an immediately adjacent empty slot.", "MINIGAME_PARAPET"

    return player, None, "MINIGAME_PARAPET"


def parapet_button_action(action, player):
    """Handles buttons for Stage 1 (Lantern Stairs) and Stage 2 (Klotski Cache)."""
    phase = player.get("parapet_phase", "stairs")
    layout = player.get("stair_layout", STAIR_LAYOUT)

    if phase == "stairs":
        if action == "toggle_lantern":
            player["lantern_open"] = not player.get("lantern_open", True)
            state_str = "OPEN (Bright Beam)" if player["lantern_open"] else "CLOSED (Darkened)"
            return player, f"You slide the brass lantern shutter: {state_str}.", "MINIGAME_PARAPET"

        if action == "climb_step":
            step_idx = player["stair_step"]
            step_type = layout[step_idx]
            is_open = player.get("lantern_open", True)
            player["stair_step"] += 1
            cur = player["stair_step"]

            msg = f"Step {cur}/8: "
            if step_type == "slit" and is_open:
                player["shift_4_mistakes"] = player.get("shift_4_mistakes", 0) + 1
                msg += (
                    "*** FLASH! You passed an open Arrow Slit with your lantern shutter OPEN! "
                    f"A beam of light cuts across the dark street below! (+1 Mistake, Total: {player['shift_4_mistakes']}) ***"
                )
            elif step_type == "cant" and not is_open:
                player["shift_4_mistakes"] = player.get("shift_4_mistakes", 0) + 1
                msg += (
                    "*** CLATTER! Pitch-black step! With your shutter closed, you kick a mason's chisel down the stone steps! "
                    f"(+1 Mistake, Total: {player['shift_4_mistakes']}) ***"
                )
            else:
                if step_type == "slit":
                    msg += "You slip past the open Arrow Slit in total darkness, unseen by the street patrol below."
                else:
                    msg += "Your lantern illuminates a chalk Thieves' Cant arrow pointing upward, guiding your footing."

            if cur >= 8:
                player["parapet_phase"] = "klotski"
                msg += (
                    "\n\n--- SHIFT 4 (STAGE 2): THE PARAPET DEAD-DROP ---\n"
                    "You emerge onto the windswept battlements! Lining up the Chipped Merlon with the Tavern Chimney below, "
                    "you find the hidden 4x4 masonry dead-drop.\n"
                    "Click the grey locking pins (Pin-A, Pin-B, Bar-C, Bar-D) and click an adjacent empty square to slide them "
                    "out of the way until the gold [SILK] parcel slides to the [EXIT] on the right!"
                )
            return player, msg, "MINIGAME_PARAPET"

    else:
        if action == "reset_klotski":
            player["klotski_blocks"] = copy.deepcopy(player.get("klotski_initial", player["klotski_blocks"]))
            player["klotski_selected"] = None
            return player, "You reset the locking pins back to their starting positions.", "MINIGAME_PARAPET"

        if action == "force_cache":
            if player.get("arcade_mode"):
                return finish_arcade_session(player, "parapet", 15, "Arcade Practice: Forced the cache with a crowbar (+1 Mistake).")
            player["shift_4_mistakes"] = player.get("shift_4_mistakes", 0) + 1
            if "contraband silk cache" not in player["inventory"]:
                player["inventory"].append("contraband silk cache")
            player["active_wallmaker_task"] = "report_parapet_walk"
            log = (
                "*** SEAL SNAPPED! ***\n"
                "You jam your crowbar into the recess and wrench the Contraband Silk Cache out by force—snapping "
                f"the Guild's delicate wax thread and gouging the stone! (+1 Mistake, Total: {player['shift_4_mistakes']})\n"
                "Return to Wellspring at the Wallmakers' Offices!"
            )
            return player, log, "MAIN"

    return player, None, "MINIGAME_PARAPET"


def draw_parapet_ui(screen, player, font, font_bold):
    """Draws Stage 1 (8-Step Secret Staircase) or Stage 2 (4x4 Sliding-Stone Cache)."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    mistakes = player.get("shift_4_mistakes", 0)
    m_col = (220, 80, 80) if mistakes > 0 else TEXT_MUTED
    screen.blit(font.render(f"Mistakes: {mistakes}", True, m_col), (682, 148))

    phase = player.get("parapet_phase", "stairs")
    layout = player.get("stair_layout", STAIR_LAYOUT)

    if phase == "stairs":
        screen.blit(font_bold.render("SECRET WALL STAIRS", True, LOCATION_ACCENT), (472, 148))
        cur_step = player.get("stair_step", 0)
        is_open = player.get("lantern_open", True)

        for i in range(8):
            ry = 348 - i * 22
            rx = 480 + i * 8
            step_rect = pygame.Rect(rx, ry, 145, 19)
            stype = layout[i]

            if i < cur_step:
                bg = (40, 55, 45)
            elif i == cur_step:
                bg = (165, 125, 50) if is_open else (55, 65, 85)
            else:
                bg = (25, 30, 38)

            pygame.draw.rect(screen, bg, step_rect, border_radius=3)
            pygame.draw.rect(screen, LOCATION_ACCENT if i == cur_step else PANEL_BORDER, step_rect, width=1, border_radius=3)

            tag = "[SLIT - SHUT!]" if stype == "slit" else "[CANT - OPEN!]"
            tag_col = (230, 110, 110) if stype == "slit" else (130, 200, 150)
            draw_fitted_text(screen, f"{i+1}. {tag}", step_rect, tag_col if i >= cur_step else TEXT_MUTED, align="left", max_lines=1)

        sx = 650
        screen.blit(font_bold.render(f"Step: {cur_step}/8", True, TEXT_COLOR), (sx, 190))
        l_col = (250, 210, 90) if is_open else (120, 135, 155)
        screen.blit(font_bold.render("LANTERN:", True, TEXT_MUTED), (sx, 225))
        screen.blit(font_bold.render("OPEN" if is_open else "SHUTTERED", True, l_col), (sx, 245))

        if cur_step < 8:
            nxt = layout[cur_step]
            screen.blit(font.render("Next Step:", True, TEXT_MUTED), (sx, 285))
            n_txt = "ARROW SLIT" if nxt == "slit" else "DARK RUBBLE"
            n_col = (230, 110, 110) if nxt == "slit" else (130, 200, 150)
            screen.blit(font_bold.render(n_txt, True, n_col), (sx, 305))

    else:
        screen.blit(font_bold.render("PARAPET CACHE PUZZLE", True, LOCATION_ACCENT), (472, 148))
        grid_x, grid_y = 478, 182
        cell_size = 44

        for y in range(4):
            for x in range(4):
                r = pygame.Rect(grid_x + x * cell_size, grid_y + y * cell_size, cell_size, cell_size)
                is_exit = (y == 1 and x in (2, 3))
                pygame.draw.rect(screen, (45, 42, 30) if is_exit else (20, 25, 30), r)
                pygame.draw.rect(screen, LOCATION_ACCENT if is_exit else PANEL_BORDER, r, 1)
                if is_exit:
                    ex_s = font.render("EXIT", True, (120, 105, 65))
                    screen.blit(ex_s, (r.centerx - ex_s.get_width() // 2, r.centery - ex_s.get_height() // 2))

        for idx, b in enumerate(player["klotski_blocks"]):
            xs = [c[0] for c in b["cells"]]
            ys = [c[1] for c in b["cells"]]
            bx = grid_x + min(xs) * cell_size + 3
            by = grid_y + min(ys) * cell_size + 3
            bw = (max(xs) - min(xs) + 1) * cell_size - 6
            bh = (max(ys) - min(ys) + 1) * cell_size - 6

            brect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(screen, b["color"], brect, border_radius=5)
            is_sel = (player.get("klotski_selected") == idx)
            pygame.draw.rect(screen, (255, 255, 255) if is_sel else (25, 30, 35), brect, width=2 if is_sel else 1, border_radius=5)
            draw_fitted_text(screen, b["name"], brect, (25, 25, 25) if b["id"] == 1 else TEXT_COLOR, bold=True)

        slides = player.get("klotski_slides", 0)
        s_col = TEXT_COLOR if slides <= 10 else (220, 80, 80)
        screen.blit(font_bold.render("Quiet Slides:", True, TEXT_MUTED), (662, 195))
        screen.blit(font_bold.render(f"{slides} / 10", True, s_col), (662, 218))
        screen.blit(font.render("Goal: Slide", True, TEXT_MUTED), (662, 260))
        screen.blit(font.render("SILK to EXIT", True, LOCATION_ACCENT), (662, 280))
        screen.blit(font.render("(Row 2 Right)", True, TEXT_MUTED), (662, 300))


# ==========================================
# WALLMAKERS SHIFT 5: CONTACT 'X' & THE SMUGGLING RUN
# ==========================================

MASON_CODE_SEQ = ["light", "heavy", "light", "heavy"]

TRANSFER_PROMPTS = {
    0: ("WINDOW OPEN: Wind masks the sound!", "advance"),
    1: ("SENTRY LOOKING: Torchlight sweeps the wall!", "freeze"),
    2: ("SNAG DETECTED: The parcel catches on stone!", "camouflage"),
}


def init_smuggle_minigame(player):
    """Initializes Stage 1 (Mason's Tap Code with 'X') at the Town Hall Milestone."""
    if player.get("arcade_mode"):
        player["mason_code_seq"] = [random.choice(["light", "heavy"]) for _ in range(4)]
        player["transfer_goal"] = 6
    else:
        player["mason_code_seq"] = list(MASON_CODE_SEQ)
        player["transfer_goal"] = 3

    player["smuggle_phase"] = "contact"
    player["tap_step"] = 0
    player["patrol_earshot"] = False
    player["smuggle_route"] = None
    player["transfer_step"] = 0
    player["transfer_hazard"] = 0

    seq = player["mason_code_seq"]
    rhythm_str = " -> ".join(f"[{i+1}. {'Light (.)' if b=='light' else 'Heavy (-)'}]" for i, b in enumerate(seq))
    log = (
        "--- SHIFT 5 (STAGE 1): CONTACTING 'X' AT THE MILESTONE ---\n"
        "You kneel beside the Town Hall milestone with your hammer and chisel. Across the cobbles, a hooded figure ('X') leans against a cobnut cart.\n"
        "MASON'S TAP CODE:\n"
        f"  • Tap the 4-beat sequence: {rhythm_str}\n"
        "  • WATCH THE PATROL GAUGE! If a Guard is in EARSHOT, click [Wipe Brow & Wait] until they pass!"
    )
    return player, log, "MINIGAME_SMUGGLE"


def smuggle_button_action(action, player):
    """Handles all 3 stages of Shift 5 and triggers the 5-Shift Tell Finale upon completion."""
    phase = player.get("smuggle_phase", "contact")
    seq = player.get("mason_code_seq", MASON_CODE_SEQ)
    goal = player.get("transfer_goal", 3)

    if phase == "contact":
        if action == "wait_patrol":
            if player.get("patrol_earshot"):
                player["patrol_earshot"] = False
                return player, "You wipe your brow and pretend to squint at the milestone until the guard's footsteps fade.", "MINIGAME_SMUGGLE"
            else:
                player["patrol_earshot"] = True
                return player, "You hesitate too long—a Town Watch sentry strolls into earshot!", "MINIGAME_SMUGGLE"

        if action in ("light", "heavy"):
            msg = ""
            if player.get("patrol_earshot"):
                player["shift_5_mistakes"] = player.get("shift_5_mistakes", 0) + 1
                msg += (
                    "*** SUSPICIOUS RHYTHM! You tapped code while a guard was in earshot! "
                    f"The sentry glares at you and 'X' tenses up! (+1 Mistake, Total: {player['shift_5_mistakes']}) ***\n"
                )

            expected = seq[player["tap_step"]]
            if action == expected:
                player["tap_step"] += 1
                beat_sym = "." if action == "light" else "-"
                msg += f"Beat {player['tap_step']}/4 [{beat_sym}]: 'X' subtly shifts a crate in acknowledgment."

                if player["tap_step"] >= 4:
                    player["smuggle_phase"] = "route"
                    prep_route = player.get("sabotaged_route", "through").upper()
                    msg += (
                        "\n\n--- SHIFT 5 (STAGE 2): SELECT SMUGGLING ROUTE ---\n"
                        "'X' brushes past you, whispering: \"Signal received. How are we moving the Silk Cache?\"\n"
                        f"(Hint: Based on your Shift 2 & 3 prep, your safest prepared route is: {prep_route} THE WALL)."
                    )
                    return player, msg, "MINIGAME_SMUGGLE"
                else:
                    player["patrol_earshot"] = (player["tap_step"] in (1, 3))
            else:
                player["shift_5_mistakes"] = player.get("shift_5_mistakes", 0) + 1
                player["patrol_earshot"] = True
                msg += (
                    f"*** WRONG BEAT! Expected a {expected.upper()} tap for Beat {player['tap_step']+1}/4! "
                    f"'X' frowns in confusion. (+1 Mistake, Total: {player['shift_5_mistakes']}) ***"
                )
            return player, msg, "MINIGAME_SMUGGLE"

    # ------------------------------------------------------------------
    # STAGE 2: ROUTE SELECTION (OVER / THROUGH / UNDER)
    # ------------------------------------------------------------------
    elif phase == "route":
        if action in ("over", "through", "under"):
            player["smuggle_route"] = action
            player["smuggle_phase"] = "transfer"
            player["transfer_step"] = 0
            player["transfer_hazard"] = 0  # First step starts with a clear window

            prep = player.get("sabotaged_route", "through")
            msg = f"--- SHIFT 5 (STAGE 3): EXECUTING '{action.upper()} THE WALL' TRANSFER ---\n"

            # Check if they picked Over or Under without having sabotaged that sector in Shift 3
            if action in ("over", "under") and prep != action:
                player["shift_5_mistakes"] = player.get("shift_5_mistakes", 0) + 1
                msg += (
                    f"*** UNPREPARED SECTOR! Because you didn't divert the crews away from the '{action.title()} the Wall' "
                    f"sector in Shift 3, fresh guards and masons are patrolling near the drop! (+1 Mistake, Total: {player['shift_5_mistakes']}) ***\n"
                )
            else:
                msg += f"Thanks to your earlier preparation, the '{action.title()} the Wall' approach is dark and unguarded!\n"

            msg += (
                "Complete 3 Transfer Steps to move the Contraband Silk Cache:\n"
                "  • Match your action to the Hazard Alert on the right-hand gauge!"
            )
            return player, msg, "MINIGAME_SMUGGLE"

        return player, None, "MINIGAME_SMUGGLE"

    # ------------------------------------------------------------------
    # STAGE 3: THE 3-STEP CONTRABAND TRANSFER
    # ------------------------------------------------------------------
    elif phase == "transfer":
        hazard = player.get("transfer_hazard", 0)
        _, required_act = TRANSFER_PROMPTS[hazard]

        if action == required_act:
            player["transfer_step"] += 1
            if player["transfer_step"] >= 3:
                return resolve_smuggle_finale(player)

            # Cycle to the next hazard state (0 -> 1 -> 2)
            player["transfer_hazard"] = player["transfer_step"] % 3
            next_desc, _ = TRANSFER_PROMPTS[player["transfer_hazard"]]
            msg = f"Transfer Progress: {player['transfer_step']}/3! Next condition: {next_desc}"
            return player, msg, "MINIGAME_SMUGGLE"
        else:
            player["shift_5_mistakes"] = player.get("shift_5_mistakes", 0) + 1
            msg = (
                f"*** CLUMSY TRANSFER! Wrong response to '{TRANSFER_PROMPTS[hazard][0]}'! "
                f"(+1 Mistake, Total: {player['shift_5_mistakes']}) ***"
            )
            return player, msg, "MINIGAME_SMUGGLE"

    return player, None, "MINIGAME_SMUGGLE"


def _roll_shift_tell(mistakes):
    """Returns True if a shift's Tell triggers based on mistake count."""
    if mistakes <= 0:
        return False
    chance = 0.25 if mistakes == 1 else 0.50 if mistakes == 2 else 0.85
    return random.random() < chance


def resolve_smuggle_finale(player):
    """Rolls all 5 independent Shift Tells and resolves the Loyal Smuggler or Double Agent Climax."""
    if player.get("arcade_mode"):
        score = max(10, 120 - (player.get("shift_5_mistakes", 0) * 25))
        return finish_arcade_session(player, "smuggle", score, "Arcade Practice: Completed the 3-Stage Smuggling Run!")

    if "contraband silk cache" in player["inventory"]:
        player["inventory"].remove("contraband silk cache")

    is_double_agent = player.get("wallmaker_double_agent", False)

    # Roll independently for each of the 5 shifts
    m1 = player.get("shift_1_mistakes", 0)
    m2 = player.get("shift_2_mistakes", 0)
    m3 = player.get("shift_3_mistakes", 0)
    m4 = player.get("shift_4_mistakes", 0)
    m5 = player.get("shift_5_mistakes", 0)

    t1 = _roll_shift_tell(m1)
    t2 = _roll_shift_tell(m2)
    t3 = _roll_shift_tell(m3)
    t4 = _roll_shift_tell(m4)
    t5 = _roll_shift_tell(m5)

    triggered_tells = []

    # ==================================================================
    # BRANCH A: DOUBLE AGENT FOR CAPTAIN WEALDHERE (THE STING!)
    # ==================================================================
    if is_double_agent:
        if t1:
            triggered_tells.append("• [Shift 1 Tell - The Narc's Notes]: Hopestill's lookouts saw your leftover chalk marks and noisy hammering during your perimeter circuit.")
        if t2:
            triggered_tells.append("• [Shift 2 Tell - The Mason's Mark]: Watching from the tavern roof, Hopestill sees the Guards march straight to your sloppy Pentomino keystone and knock it out on command.")
        if t3:
            triggered_tells.append("• [Shift 3 Tell - The Canary Trap]: Wellspring realizes the Watch ambush was waiting in the exact sector you clumsily altered on the 4x4x4 damage board.")
        if t4:
            triggered_tells.append("• [Shift 4 Tell - The Broken Seal]: As the net drops, 'X' spots your rough pry-marks and smudged Guard chalk on the Silk Cache and yells, \"The surveyor is a rat!\"")
        if t5:
            triggered_tells.append("• [Shift 5 Tell - The Nervous Informant]: Your mistimed hammer taps at the milestone tipped 'X' off that you were stalling for the Watch.")

        player["active_wallmaker_task"] = None
        player["owes_hopestill"] = False
        player["surveyor_report"] = None
        player["wall_surveyor_shifts"] += 1
        player = mark_shift_completed(player)
        player, _ = advance_time(300, player)

        log = (
            "=== DOUBLE AGENT CLIMAX: THE GUARD RAID ===\n"
            "As the Contraband Silk Cache clears the wall, shrill brass whistles pierce the fog!\n"
            "Captain Wealdhere and an armoured squad of the Town Watch burst from cover on both sides of the wall, pinning 'X' and the receiving crew in heavy irons!\n\n"
        )

        if not triggered_tells:
            player["silver"] += 60
            player["reputation"] += 5
            player["stealth"] += 1
            player["faction_guard"] = min(10, player.get("faction_guard", 0) + 5)
            player["wallmakers_reported"] = False
            if "intelligence officer" not in player["skills"]:
                player["skills"].append("intelligence officer")
            set_region_territory(player, "The New Road", "Guard")

            log += (
                "*** FLAWLESS UNDERCOVER STING (0 Tells Triggered)! ***\n"
                "From the shadows of the tavern roof, Hopestill curses Surveyor Steadfast—completely convinced the veteran leaked the ledger!\n"
                "Captain Wealdhere slips you a heavy 60-silver bounty in the dark while pretending to rough you up so your cover with the Wallmakers stays 100% intact!\n"
                "*** (+60 Silver, +5 Reputation, +1 Stealth, +5 Guard Faction, 'intelligence officer' Skill | The New Road is now GUARD TERRITORY!) ***"
            )
        else:
            player["silver"] += 25
            player["health"] = max(1, player["health"] - 3)
            player["faction_wallmakers"] = -10
            if len(triggered_tells) >= 2:
                player["reputation"] -= 1
            else:
                player["reputation"] += 1
            player["wallmakers_reported"] = True
            player["hopestill_angry"] = True
            player["current_job"] = None
            log += (
                "*** YOUR COVER IS BLOWN! HOPESTILL DISCOVERED YOUR BETRAYAL: ***\n"
                + "\n".join(triggered_tells) + "\n\n"
                "Up on the tavern ridge, Hopestill spots your betrayal and signals his lookouts! A crossbow bolt grazes your shoulder (-3 Health) and half the contraband is lost in the chaos before the Watch secures the street.\n"
                "Captain Wealdhere hands you a reduced 25-silver hazard payout, docking the rest for the botched sting—and the surviving Wallmakers have sworn a blood vendetta against you!\n"
                "*** (+25 Silver, -3 Health, +3 Guard Faction | Wallmakers Faction: -10, Fired from Guild!) ***"
            )
        return player, log, "MAIN"

    # ==================================================================
    # BRANCH B: LOYAL WALLMAKER SMUGGLER (MOVING THE SILK FOR HOPESTILL)
    # ==================================================================
    else:
        if t1:
            triggered_tells.append("• [Shift 1 Tell - The Chalk Trail]: A Watch sergeant followed your un-wiped mason's chalk and loud hammer scuffs along the wall.")
        if t2:
            triggered_tells.append("• [Shift 2 Tell - The Weeping Mortar]: Patrols noticed fresh mortar dust trickling from your sloppy Pentomino repair behind the Blacksmiths.")
        if t3:
            triggered_tells.append("• [Shift 3 Tell - The Paper Trail]: The Overseer spotted your smudged, contradictory 4x4x4 damage ledger and alerted Captain Wealdhere.")
        if t4:
            triggered_tells.append("• [Shift 4 Tell - Light in the Murder-Holes]: A sentry saw your lantern flash through the secret stair slits and heard stone pins grinding on the parapet.")
        if t5:
            triggered_tells.append("• [Shift 5 Tell - Caught Red-Handed]: A patrol heard your mistimed hammer taps at the milestone and tracked you to the wall.")

        player["active_wallmaker_task"] = "report_smuggle_finale"

        if not triggered_tells:
            player["smuggle_clean_success"] = True
            player["silver"] += 50
            player["stealth"] += 1
            player["faction_wallmakers"] = min(10, player["faction_wallmakers"] + 5)
            if "master wallmaker" not in player["skills"]:
                player["skills"].append("master wallmaker")
            set_region_territory(player, "The Old Path", "Wallmakers")
            set_region_territory(player, "Old Path Plains", "Wallmakers")

            log = (
                "=== HEIST CLIMAX: THE PERFECT SMUGGLING RUN ===\n"
                "*** ZERO TELLS TRIGGERED! ***\n"
                "Every stone, ledger swap, and lantern shutter pays off cleanly. 'X' slides the Contraband Silk Cache onto the waiting pack-mules beyond the wall without a single guard patrol wiser!\n"
                "'X' presses a heavy pouch of 50 silver into your gloved hand—your personal cut of the silk profits.\n\n"
                "*** FLAWLESS HEIST! (+50 Silver Bonus, +1 Stealth, +5 Wallmakers Faction, 'Master Wallmaker' Skill | The Old Path is now WALLMAKERS TERRITORY!) ***\n"
                "*** Return to Wellspring at the Wallmakers' Offices to collect your shift pay! ***"
            )
        else:
            player["smuggle_clean_success"] = False
            player["reputation"] -= 3
            player["health"] = max(1, player["health"] - 2)
            log = (
                "=== HEIST CLIMAX: AMBUSHED AT THE WALL! ===\n"
                "Just as 'X' reaches for the Silk Cache, Town Watch lanterns blaze through the fog! The Guards tracked your operation using your earlier mistakes:\n"
                + "\n".join(triggered_tells) + "\n\n"
                "'X' cuts the tether and flees into the heath with only half the silk, while you scramble back into the alleys of Murum with a grazing crossbow bolt across your coat (-2 Health)!\n"
                "*** HEIST COMPROMISED! (-3 Reputation, -2 Health) ***\n"
                "*** Return to Wellspring at the Wallmakers' Offices to report what happened! ***"
            )
        return player, log, "MAIN"


def draw_smuggle_ui(screen, player, font, font_bold):
    """Draws Stage 1 (Milestone Tap Code), Stage 2 (Route Picker), or Stage 3 (Transfer Gauge)."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    mistakes = player.get("shift_5_mistakes", 0)
    m_col = (220, 80, 80) if mistakes > 0 else TEXT_MUTED
    screen.blit(font.render(f"Mistakes: {mistakes}", True, m_col), (682, 148))

    phase = player.get("smuggle_phase", "contact")

    # --- STAGE 1 UI: MASON'S TAP CODE ---
    if phase == "contact":
        seq = player.get("mason_code_seq", MASON_CODE_SEQ)
        rhythm_syms = "   ".join("[ . ]" if b == "light" else "[ - ]" for b in seq)
        screen.blit(font_bold.render("CONTACT 'X' (MASON CODE)", True, LOCATION_ACCENT), (470, 148))
        screen.blit(font.render(f"Target Rhythm:  {rhythm_syms}", True, TEXT_MUTED), (475, 182))
        labels = [f"{i+1}. {'LIGHT' if b == 'light' else 'HEAVY'}" for i, b in enumerate(seq)]
        cur_beat = player.get("tap_step", 0)
        for i in range(4):
            bx = 472 + i * 74
            r = pygame.Rect(bx, 210, 68, 42)
            bg = (55, 120, 75) if i < cur_beat else (150, 115, 45) if i == cur_beat else (25, 30, 38)
            pygame.draw.rect(screen, bg, r, border_radius=5)
            pygame.draw.rect(screen, LOCATION_ACCENT if i == cur_beat else PANEL_BORDER, r, width=1, border_radius=5)
            t_surf = font_bold.render(labels[i], True, TEXT_COLOR)
            screen.blit(t_surf, (r.centerx - t_surf.get_width() // 2, r.centery - t_surf.get_height() // 2))

        # Patrol Earshot Indicator Bar
        earshot = player.get("patrol_earshot", False)
        p_rect = pygame.Rect(475, 278, 290, 56)
        p_bg = (145, 45, 45) if earshot else (40, 95, 60)
        pygame.draw.rect(screen, p_bg, p_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 200, 200) if earshot else PANEL_BORDER, p_rect, width=2, border_radius=6)

        p_txt = "PATROL IN EARSHOT! (WAIT!)" if earshot else "STREET CLEAR (SAFE TO TAP)"
        p_surf = font_bold.render(p_txt, True, TEXT_COLOR)
        screen.blit(p_surf, (p_rect.centerx - p_surf.get_width() // 2, p_rect.centery - p_surf.get_height() // 2))

    # --- STAGE 2 UI: ROUTE SELECTION ---
    elif phase == "route":
        screen.blit(font_bold.render("SELECT SMUGGLING ROUTE", True, LOCATION_ACCENT), (470, 148))
        prep = player.get("sabotaged_route", "through")

        routes = [
            ("over",    "OVER THE WALL",    "North Tower Rope Drop"),
            ("through", "THROUGH THE WALL", "East Breach Hollow Stone"),
            ("under",   "UNDER THE WALL",   "Sluice Gate Culvert"),
        ]
        for idx, (r_key, r_title, r_sub) in enumerate(routes):
            ry = 185 + idx * 58
            r_rect = pygame.Rect(475, ry, 290, 48)
            is_prep = (r_key == prep or r_key == "through")
            pygame.draw.rect(screen, (40, 65, 55) if is_prep else (45, 35, 40), r_rect, border_radius=5)
            pygame.draw.rect(screen, LOCATION_ACCENT if is_prep else PANEL_BORDER, r_rect, width=1, border_radius=5)

            screen.blit(font_bold.render(r_title, True, TEXT_COLOR), (488, ry + 6))
            tag = " [PREPARED]" if r_key == prep else ""
            screen.blit(font.render(r_sub + tag, True, (130, 210, 150) if is_prep else TEXT_MUTED), (488, ry + 25))

    # --- STAGE 3 UI: CONTRABAND TRANSFER GAUGE ---
    else:
        route_str = (player.get("smuggle_route") or "wall").upper()
        screen.blit(font_bold.render(f"TRANSFER: {route_str} THE WALL", True, LOCATION_ACCENT), (470, 148))

        # Progress Track (0/3 .. 3/3)
        step = player.get("transfer_step", 0)
        screen.blit(font.render(f"Contraband Transfer Progress: {step} / 3", True, TEXT_COLOR), (475, 185))
        for i in range(3):
            s_rect = pygame.Rect(475 + i * 98, 210, 90, 32)
            pygame.draw.rect(screen, (205, 165, 60) if i < step else (25, 30, 38), s_rect, border_radius=4)
            pygame.draw.rect(screen, PANEL_BORDER, s_rect, width=1, border_radius=4)

        # Current Hazard Prompt Box
        hazard = player.get("transfer_hazard", 0)
        h_desc, _ = TRANSFER_PROMPTS[hazard]
        h_colors = {0: (45, 105, 65), 1: (155, 55, 55), 2: (150, 110, 45)}
        h_rect = pygame.Rect(475, 265, 290, 75)
        pygame.draw.rect(screen, h_colors[hazard], h_rect, border_radius=6)
        pygame.draw.rect(screen, TEXT_COLOR, h_rect, width=2, border_radius=6)

        screen.blit(font_bold.render("CURRENT WALL CONDITION:", True, TEXT_MUTED), (488, 275))
        screen.blit(font_bold.render(h_desc[:32], True, TEXT_COLOR), (488, 302))

# ==========================================
# MARKET SHIFT 3 SIDE-QUEST: APOTHECARY'S RECIPE (STORY + 60s ARCADE POTION RUSH)
# ==========================================

RECIPE_INGREDIENTS = ["Willow Bark", "Valerian Root", "Moon-Water", "Brimstone Ash"]
RECIPE_TARGET_SEQ = [(0, 3), (1, 1), (2, 4), (3, 2)]


def _spawn_arcade_recipe(player):
    """Generates a randomized 4-step formula for Arcade Potion Rush."""
    ings = [0, 1, 2, 3]
    random.shuffle(ings)
    player["recipe_target_seq"] = [(ing, random.randint(1, 4)) for ing in ings]
    player["recipe_step"] = 0


def init_recipe_minigame(player):
    """Initializes the 4-Step Apothecary Compounding Mini-Game."""
    player["recipe_step"] = 0
    player["recipe_ing_idx"] = 0
    player["recipe_qty"] = 1
    player["recipe_mistakes"] = 0
    player["recipe_score"] = 0
    player["recipe_potions_brewed"] = 0
    player["recipe_time_left"] = 60.0

    if player.get("arcade_mode"):
        _spawn_arcade_recipe(player)
        log = (
            "--- ARCADE POTION RUSH (60.0 SECONDS) ---\n"
            "Brew as many randomized **Sovereign Draughts** as you can in 60 seconds!\n"
            "• Every completed 4-step potion awards **+100 points** and spawns a new randomized formula scroll!\n"
            "• Cycle the Reagent and Dram Quantity (1–4) and click [Add to Cauldron >>]!"
        )
    else:
        player["recipe_target_seq"] = list(RECIPE_TARGET_SEQ)
        log = (
            "--- APOTHECARY COMPOUNDING: SOVEREIGN FEVER-DRAUGHT ---\n"
            "Follow the formula scroll on the cauldron panel!\n"
            "  • Step 1: Add **3 drams** of **Willow Bark**\n"
            "  • Step 2: Add **1 dram** of **Valerian Root**\n"
            "  • Step 3: Add **4 drams** of **Moon-Water**\n"
            "  • Step 4: Add **2 drams** of **Brimstone Ash**\n"
            "Use the buttons on the right to cycle the Ingredient and Quantity (1-4 drams), then click [Add to Cauldron >>]!"
        )
    return player, log, "MINIGAME_RECIPE"


def update_recipe_timer(player, dt):
    if not player.get("arcade_mode"):
        return player, None, "MINIGAME_RECIPE"
    player["recipe_time_left"] = player.get("recipe_time_left", 60.0) - dt
    if player["recipe_time_left"] <= 0:
        brewed = player.get("recipe_potions_brewed", 0)
        partial = player.get("recipe_step", 0) * 20
        score = max(0, (brewed * 100) + partial - (player.get("recipe_mistakes", 0) * 25))
        return finish_arcade_session(
            player, "recipe", score,
            f"*** TIME UP! You brewed {brewed} full potion(s) for {score} points! ***"
        )
    return player, None, "MINIGAME_RECIPE"


def recipe_button_action(action, player):
    """Handles cycling ingredients, adjusting dram quantities, and dropping into the cauldron."""
    if action == "cycle_ing":
        player["recipe_ing_idx"] = (player.get("recipe_ing_idx", 0) + 1) % 4
        return player, f"Selected reagent: {RECIPE_INGREDIENTS[player['recipe_ing_idx']]}.", "MINIGAME_RECIPE"

    if action == "cycle_qty":
        player["recipe_qty"] = (player.get("recipe_qty", 1) % 4) + 1
        return player, f"Measured quantity: {player['recipe_qty']} dram(s).", "MINIGAME_RECIPE"

    if action == "add_cauldron":
        step = player.get("recipe_step", 0)
        seq = player.get("recipe_target_seq", RECIPE_TARGET_SEQ)
        chosen_pair = (player.get("recipe_ing_idx", 0), player.get("recipe_qty", 1))
        req_ing, req_qty = seq[step]

        if chosen_pair == (req_ing, req_qty):
            player["recipe_step"] = step + 1
            if player["recipe_step"] >= 4:
                if player.get("arcade_mode"):
                    player["recipe_potions_brewed"] = player.get("recipe_potions_brewed", 0) + 1
                    player["recipe_score"] = player["recipe_potions_brewed"] * 100
                    _spawn_arcade_recipe(player)
                    t_rem = max(0.0, player.get("recipe_time_left", 0.0))
                    return (
                        player,
                        f"*** POTION #{player['recipe_potions_brewed']} BREWED (+100 PTS | {t_rem:.1f}s left)! New formula scroll unrolled! ***",
                        "MINIGAME_RECIPE"
                    )

                player["market_sq3_done"] = True
                player["silver"] += 10
                log = (
                    "*** PERFECT COMPOUND! ***\n"
                    "The cauldron turns a luminous emerald green and settles into a fragrant steam!\n"
                    "The Apothecary bottles the Sovereign Fever-Draught with a wide grin. \"Flawless measurements! Not a dram out of place!\"\n"
                    "\"Take this 10 silver for saving my stall today—and I'll tell Godwin what a marvel you are!\"\n\n"
                    f"*** SIDE-QUEST COMPLETE! (+10 Silver, Total: {player['silver']}; +1 Bonus Charisma when you finish Shift 3 with Godwin!) ***"
                )
                return player, log, "MAIN"
            return player, f"Step {step+1}/4 added cleanly! The draught simmers steadily. Prepare Step {step+2}/4!", "MINIGAME_RECIPE"
        else:
            player["recipe_mistakes"] = player.get("recipe_mistakes", 0) + 1
            if player.get("arcade_mode"):
                player["recipe_time_left"] = max(0.0, player.get("recipe_time_left", 60.0) - 4.0)
                if player["recipe_mistakes"] >= 3:
                    score = player.get("recipe_potions_brewed", 0) * 100
                    return finish_arcade_session(player, "recipe", score, f"Arcade Cauldron Boiled Over! (Final Score: {score} pts)")
                return player, f"*** HISS! Wrong measure (-4.0s Penalty | Mistake {player['recipe_mistakes']}/3)! Expected {req_qty} dram(s) of {RECIPE_INGREDIENTS[req_ing]}! ***", "MINIGAME_RECIPE"

            if player["recipe_mistakes"] >= 2:
                player["market_sq3_failed"] = True
                log = (
                    "*** CAULDRON BOILED OVER! ***\n"
                    "Purple acrid smoke belches from the pot as the ruined mixture curdles into black sludge!\n"
                    "The Apothecary coughs and waves a towel. \"Stop, stop! The batch is ruined! Stick to your broom today, sweeper!\"\n\n"
                    "*** Side-Quest Failed! ***"
                )
                return player, log, "MAIN"
            log = (
                f"*** HISS! Wrong measure! Step {step+1} requires {req_qty} dram(s) of {RECIPE_INGREDIENTS[req_ing]}! "
                f"(Mistake {player['recipe_mistakes']}/2 — one more mistake ruins the batch!) ***"
            )
            return player, log, "MINIGAME_RECIPE"

    return player, None, "MINIGAME_RECIPE"


def draw_recipe_ui(screen, player, font, font_bold):
    """Draws the Apothecary's Formula Scroll and Cauldron Status."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    if player.get("arcade_mode"):
        t_left = max(0.0, player.get("recipe_time_left", 60.0))
        pts = player.get("recipe_potions_brewed", 0) * 100
        screen.blit(font_bold.render(f"POTION RUSH: {t_left:04.1f}s ({pts}p)", True, LOCATION_ACCENT), (470, 148))
    else:
        screen.blit(font_bold.render("APOTHECARY'S CAULDRON", True, LOCATION_ACCENT), (472, 148))

    mistakes = player.get("recipe_mistakes", 0)
    max_m = 3 if player.get("arcade_mode") else 2
    screen.blit(font.render(f"Err: {mistakes}/{max_m}", True, (220, 80, 80) if mistakes else TEXT_MUTED), (705, 148))

    seq = player.get("recipe_target_seq", RECIPE_TARGET_SEQ)
    cur_step = player.get("recipe_step", 0)
    for i, (ing_idx, qty) in enumerate(seq):
        ry = 176 + i * 32
        r_rect = pygame.Rect(472, ry, 296, 28)
        bg = (45, 95, 65) if i < cur_step else (130, 95, 40) if i == cur_step else (25, 30, 38)
        pygame.draw.rect(screen, bg, r_rect, border_radius=4)
        pygame.draw.rect(screen, LOCATION_ACCENT if i == cur_step else PANEL_BORDER, r_rect, width=1, border_radius=4)
        status_sym = "[DONE]" if i < cur_step else "[NEXT]" if i == cur_step else f"Step {i+1}"
        draw_fitted_text(screen, f"{status_sym}: {qty} dram(s) of {RECIPE_INGREDIENTS[ing_idx]}", r_rect, TEXT_COLOR, align="left", max_lines=1)

    sel_box = pygame.Rect(472, 310, 296, 66)
    pygame.draw.rect(screen, (20, 25, 30), sel_box, border_radius=6)
    pygame.draw.rect(screen, LOCATION_ACCENT, sel_box, width=1, border_radius=6)
    ing_name = RECIPE_INGREDIENTS[player.get("recipe_ing_idx", 0)]
    qty_val = player.get("recipe_qty", 1)
    screen.blit(font_bold.render(f"LADLE: {qty_val} dram(s) of {ing_name}", True, TEXT_COLOR), (484, 320))
    screen.blit(font.render("Match the [NEXT] step above and click Add!", True, TEXT_MUTED), (484, 344))


# ==========================================
# MARKET SHIFT 4 MAIN TASK: 4x4x4 FLY-TIPPING LOGIC PUZZLE (STORY + RANDOMIZED ARCADE)
# ==========================================

FLYTIP_MERCHANTS = ["Butcher", "Fishmonger", "Fruiterer", "Commissar"]
FLYTIP_LOCS = ["Archway", "Gutter", "Fountain", "Old Well"]
FLYTIP_WASTE = ["Rotten Offal", "Fish-Heads", "Mouldy Rinds", "Rancid Tallow"]

TRUE_FLYTIP = [(0, 0), (1, 1), (2, 2), (3, 3)]


def _generate_flytip_solution(player):
    """Generates a randomized 4x4x4 solution and matching clues for Arcade Mode."""
    if not player.get("arcade_mode"):
        player["flytip_solution"] = list(TRUE_FLYTIP)
    else:
        locs = [0, 1, 2, 3]
        wastes = [0, 1, 2, 3]
        random.shuffle(locs)
        random.shuffle(wastes)
        player["flytip_solution"] = list(zip(locs, wastes))

    # Scramble starting chits so they never start already solved
    sol = player["flytip_solution"]
    player["flytip_locs"] = [(sol[r][0] + r + 1) % 4 for r in range(4)]
    player["flytip_wastes"] = [(sol[r][1] + r + 2) % 4 for r in range(4)]


def init_flytip_minigame(player):
    """Initializes the 4x4x4 Fly-Tipping Sanitation Citation Board."""
    if player.get("arcade_mode") or "flytip_locs" not in player or player.get("active_market_task") != "solve_flytipping":
        player["flytip_mistakes"] = 0
        player["flytip_cases_solved"] = 0
        player["flytip_time_left"] = 75.0
        _generate_flytip_solution(player)

    if player.get("arcade_mode"):
        log = (
            "--- ARCADE SANITARY INSPECTOR (RANDOMIZED CASES — 75.0s) ---\n"
            "Every case in Arcade Mode has a **brand-new randomized culprit layout**!\n"
            "1. Click [Inspect Rubbish Heaps] and [Question Stall Alibis] to read the clues for this case.\n"
            "2. Cycle the Dumping Spot and Waste Type chits to match all 4 merchants and click [Issue Citations >>] (+100 pts per case)!"
        )
    else:
        log = (
            "--- SHIFT 4: THE FLY-TIPPING CITATION BOARD ---\n"
            "Four merchants dumped foul waste in four corners of the Market overnight.\n"
            "1. Click [Inspect Rubbish Heaps] and [Question Stall Alibis] to gather the clues.\n"
            "2. Click any Dumping Spot or Waste Type chit on the board to cycle it (L/R Click).\n"
            "3. Once all 4 merchants are matched to their true Dumping Spot and Waste Type, click [Issue Citations >>]!\n"
            "(Remember: You can click [< Pause & Return] to resolve the Butcher's stall brawl side-quest first!)"
        )
    return player, log, "MINIGAME_FLYTIP"


def update_flytip_timer(player, dt):
    if not player.get("arcade_mode"):
        return player, None, "MINIGAME_FLYTIP"
    player["flytip_time_left"] = player.get("flytip_time_left", 75.0) - dt
    if player["flytip_time_left"] <= 0:
        cases = player.get("flytip_cases_solved", 0)
        sol = player.get("flytip_solution", TRUE_FLYTIP)
        correct_now = sum(1 for r in range(4) if (player["flytip_locs"][r], player["flytip_wastes"][r]) == sol[r])
        score = max(0, (cases * 100) + (correct_now * 20) - (player.get("flytip_mistakes", 0) * 15))
        return finish_arcade_session(
            player, "flytip", score,
            f"*** TIME UP! You solved {cases} full fly-tipping case(s) for {score} points! ***"
        )
    return player, None, "MINIGAME_FLYTIP"


def handle_flytip_event(event, player):
    """Handles clicking Dumping Spot and Waste Type chits on the 4-row board."""
    if event.type != pygame.MOUSEBUTTONDOWN:
        return player, None, "MINIGAME_FLYTIP"

    mx, my = event.pos
    start_y = 198
    row_h = 38
    loc_x, loc_w = 548, 108
    wst_x, wst_w = 662, 110

    for row in range(4):
        ry = start_y + row * row_h
        if ry <= my <= ry + 32:
            step = -1 if event.button == 3 else 1
            if loc_x <= mx <= loc_x + loc_w:
                player["flytip_locs"][row] = (player["flytip_locs"][row] + step) % 4
                return player, None, "MINIGAME_FLYTIP"
            elif wst_x <= mx <= wst_x + wst_w:
                player["flytip_wastes"][row] = (player["flytip_wastes"][row] + step) % 4
                return player, None, "MINIGAME_FLYTIP"

    return player, None, "MINIGAME_FLYTIP"


def flytip_button_action(action, player):
    """Handles clue buttons and citation verification for Market Shift 4 & Randomized Arcade Mode."""
    sol = player.get("flytip_solution", TRUE_FLYTIP)

    if action == "heaps":
        # Dynamically generate heap clues from current solution `sol`!
        log = (
            "--- CLUES: INSPECTING THE RUBBISH HEAPS ---\n"
            f"• At the {FLYTIP_LOCS[sol[0][0]].upper()}, someone dumped a heap of {FLYTIP_WASTE[sol[0][1]].upper()}.\n"
            f"• Beside the {FLYTIP_LOCS[sol[2][0]].upper()}, you find piles of {FLYTIP_WASTE[sol[2][1]].upper()}.\n"
            f"• Near the {FLYTIP_LOCS[sol[1][0]].upper()}, the cobbles are covered in {FLYTIP_WASTE[sol[1][1]].upper()}."
        )
        return player, log, "MINIGAME_FLYTIP"

    if action == "alibis":
        # Dynamically generate merchant alibi clues from current solution `sol`!
        log = (
            "--- CLUES: MERCHANT STALL ALIBIS ---\n"
            f"• The BUTCHER's apprentice was spotted wheeling a barrow toward the {FLYTIP_LOCS[sol[0][0]].upper()} at dusk.\n"
            f"• The COMMISSAR was seen scrubbing {FLYTIP_WASTE[sol[3][1]].upper()} barrels right beside the {FLYTIP_LOCS[sol[3][0]].upper()}.\n"
            f"• The FRUITERER always dumps their crates by the {FLYTIP_LOCS[sol[2][0]].upper()} before locking up."
        )
        return player, log, "MINIGAME_FLYTIP"

    if action == "verify":
        correct = sum(
            1 for r in range(4)
            if (player["flytip_locs"][r], player["flytip_wastes"][r]) == sol[r]
        )
        if correct == 4:
            if player.get("arcade_mode"):
                player["flytip_cases_solved"] = player.get("flytip_cases_solved", 0) + 1
                _generate_flytip_solution(player)
                t_rem = max(0.0, player.get("flytip_time_left", 0.0))
                return (
                    player,
                    f"*** CASE #{player['flytip_cases_solved']} SOLVED (+100 PTS | {t_rem:.1f}s left)! New randomized case on the board—check the new clues! ***",
                    "MINIGAME_FLYTIP"
                )

            player["active_market_task"] = "report_market_shift_4"
            log = (
                "*** ALL 4 FLY-TIPPING CITATIONS VERIFIED! ***\n"
                "You have pinned every heap of illegal waste to the exact merchant responsible!\n"
                "Speak to Godwin ('Return from Task') to turn in the citations—or talk to the **Butcher** first if you haven't done the Shift 4 Side-Quest yet!"
            )
            return player, log, "MAIN"
        else:
            player["flytip_mistakes"] = player.get("flytip_mistakes", 0) + 1
            if player.get("arcade_mode"):
                player["flytip_time_left"] = max(0.0, player.get("flytip_time_left", 75.0) - 5.0)
            log = (
                f"*** INCORRECT CITATIONS ({correct}/4 rows accurate)! ***\n"
                "Check [Inspect Rubbish Heaps] and [Question Stall Alibis] again."
            )
            return player, log, "MINIGAME_FLYTIP"

    return player, None, "MINIGAME_FLYTIP"

def draw_flytip_ui(screen, player, font, font_bold):
    """Draws the 4x4x4 Market Sanitation Citation Board."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    if player.get("arcade_mode"):
        t_left = max(0.0, player.get("flytip_time_left", 75.0))
        pts = player.get("flytip_cases_solved", 0) * 100
        screen.blit(font_bold.render(f"CITATIONS: {t_left:04.1f}s ({pts}p)", True, LOCATION_ACCENT), (470, 148))
    else:
        screen.blit(font_bold.render("FLY-TIPPING CITATIONS", True, LOCATION_ACCENT), (470, 148))

    mistakes = player.get("flytip_mistakes", 0)
    screen.blit(font.render(f"Errors: {mistakes}", True, (220, 80, 80) if mistakes else TEXT_MUTED), (695, 148))

    screen.blit(font.render("Merchant", True, TEXT_MUTED), (468, 174))
    screen.blit(font.render("Dumping Spot", True, TEXT_MUTED), (552, 174))
    screen.blit(font.render("Waste Type", True, TEXT_MUTED), (666, 174))

    start_y = 198
    row_h = 38
    loc_x, loc_w = 548, 108
    wst_x, wst_w = 662, 110

    for r in range(4):
        ry = start_y + r * row_h
        screen.blit(font_bold.render(FLYTIP_MERCHANTS[r], True, TEXT_COLOR), (468, ry + 7))

        loc_idx = player["flytip_locs"][r]
        loc_rect = pygame.Rect(loc_x, ry, loc_w, 32)
        pygame.draw.rect(screen, (45, 60, 75), loc_rect, border_radius=4)
        pygame.draw.rect(screen, PANEL_BORDER, loc_rect, width=1, border_radius=4)
        draw_fitted_text(screen, FLYTIP_LOCS[loc_idx], loc_rect, TEXT_COLOR)

        wst_idx = player["flytip_wastes"][r]
        wst_rect = pygame.Rect(wst_x, ry, wst_w, 32)
        pygame.draw.rect(screen, (65, 50, 70), wst_rect, border_radius=4)
        pygame.draw.rect(screen, PANEL_BORDER, wst_rect, width=1, border_radius=4)
        draw_fitted_text(screen, FLYTIP_WASTE[wst_idx], wst_rect, TEXT_COLOR)

    screen.blit(font.render("Click chits to cycle (L/R Click)", True, TEXT_MUTED), (470, 358))


# ==========================================
# ARCADE PRACTICE PARLOUR & HIGH SCORES
# ==========================================

def update_high_score(player, game_name, score):
    current_best = player.setdefault("high_scores", {}).get(game_name, 0)
    if score > current_best:
        player["high_scores"][game_name] = score
        return True, score
    return False, current_best

def get_arcade_menu_text(player):
    hs = player.get("high_scores", {})
    claimed = len(player.get("arcade_prizes_claimed", []))
    return (
        f"--- THE HOUSE OF GAMES: MECHANICAL ARCADE ({claimed}/9 House Prizes Claimed) ---\n"
        f"• Blacksmith Forge Best: {hs.get('forge', 0)} pts   |   • Masonry Jigsaw Best: {hs.get('jigsaw', 0)} pts\n"
        f"• Market Thief Chase Best: {hs.get('chase', 0)} pts   |   • Fly-Tipping Board Best: {hs.get('flytip', 0)} pts\n"
        f"• Parapet Cache Best: {hs.get('parapet', 0)} pts   |   • Smuggler Run Best: {hs.get('smuggle', 0)} pts\n"
        f"• Apothecary Recipe Best: {hs.get('recipe', 0)} pts   |   • Sounding Rush Best: {hs.get('sounding', 0)} pts\n"
        f"• Sharpshooter Archery Best: {hs.get('archery', 0)} pts\n\n"
        "Beat the House Record on any cabinet to win +10 Casino Chips and +1 Reputation:"
    )

def start_arcade_game(player, game_key):
    """Launches any mini-game in Challenging Arcade Blitz Mode without touching story quests."""
    player["arcade_mode"] = True
    if game_key == "forge":
        player["forge_round"] = 0
        player["forge_mistakes"] = 0
        player["forge_score"] = 0
        player["forge_arcade_time_left"] = 60.0
        p, _, st = start_next_forge_round(player)
        return p, (
            "--- ARCADE 60-SECOND FORGE BLITZ ---\n"
            "Land as many clean strikes as you can in **60.0 seconds**!\n"
            "• Each strike awards **+10 pts**, and the reaction timer speeds up with every strike!\n"
            "• A mistake costs **-2.0 seconds** (and 4 mistakes shatters the blade!)."
        ), st
    elif game_key == "jigsaw":
        return init_jigsaw(player)
    elif game_key == "chase":
        p, _, st = init_chase(player, stage=1, bonus_paces=0)
        p["chase_distance"] = 20
        p["chase_time_limit"] = 1.65
        p["chase_timer"] = 1.65
        return p, (
            "--- ARCADE ENDURANCE PURSUIT (20 PACES) ---\n"
            "The Cutpurse has a **20-pace head start** and darts between lanes at top speed!\n"
            "React in the first half of the timer bar to close 2 paces at once!"
        ), st
    elif game_key == "flytip":
        return init_flytip_minigame(player)
    elif game_key == "parapet":
        return init_parapet_minigame(player)
    elif game_key == "smuggle":
        return init_smuggle_minigame(player)
    elif game_key == "recipe":
        return init_recipe_minigame(player)
    elif game_key == "sounding":
        return init_sounding_minigame(player, "arcade")
    elif game_key == "archery":
        return init_archery_minigame(player)
    player["arcade_mode"] = False
    return player, get_arcade_menu_text(player), "ARCADE_MENU"

def finish_arcade_session(player, game_key, score, summary_msg):
    """Safely concludes an Arcade practice run and awards 10-Chip House Record Prizes."""
    player["arcade_mode"] = False
    is_new, best = update_high_score(player, game_key, score)
    banner = f"*** NEW HIGH SCORE: {score} PTS! ***" if is_new else f"(Score: {score} pts | Personal Best: {best} pts)"
    prize_msg = check_arcade_champion_prize(player, game_key, score)
    log = f"{summary_msg}\n{banner}{prize_msg}\n\n{get_arcade_menu_text(player)}"
    return player, log, "ARCADE_MENU"

# =========================================================================
# 1. SHARED 52-CARD DECK, ANIMATION HELPERS & VECTOR CARD RENDERER
# =========================================================================
SUITS = ["S", "H", "D", "C"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

BAIZE_GREEN = (22, 84, 52)
BAIZE_DARK = (14, 58, 35)
BAIZE_LINE = (46, 122, 80)
RAIL_WOOD = (48, 26, 18)
BRASS_GOLD = (205, 165, 85)
CARD_IVORY = (246, 241, 228)
CARD_BACK_RED = (158, 42, 32)
SUIT_RED = (185, 35, 35)
SUIT_BLACK = (28, 28, 32)

SHOE_POS = (690, 140)  # Origin point where cards slide out from


def create_shuffled_deck():
    deck = [(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def schedule_card_anim(player, key, delay_ms=0):
    """Records a timestamp so a newly dealt card slides smoothly from the shoe."""
    if "card_spawn_ticks" not in player:
        player["card_spawn_ticks"] = {}
    player["card_spawn_ticks"][key] = pygame.time.get_ticks() + delay_ms


def get_animated_card_pos(player, key, target_x, target_y, duration_ms=260):
    """Returns interpolated (x, y) coordinates from the shoe to the target slot."""
    ticks = player.get("card_spawn_ticks", {})
    if key not in ticks:
        return target_x, target_y
    now = pygame.time.get_ticks()
    t0 = ticks[key]
    if now < t0:
        return SHOE_POS
    elapsed = now - t0
    if elapsed >= duration_ms:
        return target_x, target_y
    t = elapsed / float(duration_ms)
    ease = 1.0 - (1.0 - t) ** 3  # Cubic ease-out
    cur_x = int(SHOE_POS[0] + (target_x - SHOE_POS[0]) * ease)
    cur_y = int(SHOE_POS[1] + (target_y - SHOE_POS[1]) * ease)
    return cur_x, cur_y


def draw_suit_pip(surface, suit, cx, cy, size):
    color = SUIT_RED if suit in ("H", "D") else SUIT_BLACK
    if suit == "D":
        pts = [(cx, cy - size), (cx + int(size * 0.75), cy), (cx, cy + size), (cx - int(size * 0.75), cy)]
        pygame.draw.polygon(surface, color, pts)
    elif suit == "H":
        r = max(2, int(size * 0.45))
        pygame.draw.circle(surface, color, (cx - r + 1, cy - int(size * 0.25)), r)
        pygame.draw.circle(surface, color, (cx + r - 1, cy - int(size * 0.25)), r)
        pts = [(cx - int(size * 0.85), cy - int(size * 0.1)), (cx + int(size * 0.85), cy - int(size * 0.1)), (cx, cy + size)]
        pygame.draw.polygon(surface, color, pts)
    elif suit == "S":
        r = max(2, int(size * 0.42))
        pygame.draw.circle(surface, color, (cx - r + 1, cy + int(size * 0.15)), r)
        pygame.draw.circle(surface, color, (cx + r - 1, cy + int(size * 0.15)), r)
        pts = [(cx - int(size * 0.85), cy + int(size * 0.05)), (cx + int(size * 0.85), cy + int(size * 0.05)), (cx, cy - size)]
        pygame.draw.polygon(surface, color, pts)
        stem = [(cx, cy + int(size * 0.2)), (cx - int(size * 0.35), cy + size), (cx + int(size * 0.35), cy + size)]
        pygame.draw.polygon(surface, color, stem)
    elif suit == "C":
        r = max(2, int(size * 0.40))
        pygame.draw.circle(surface, color, (cx, cy - int(size * 0.35)), r)
        pygame.draw.circle(surface, color, (cx - int(size * 0.42), cy + int(size * 0.15)), r)
        pygame.draw.circle(surface, color, (cx + int(size * 0.42), cy + int(size * 0.15)), r)
        stem = [(cx, cy + int(size * 0.1)), (cx - int(size * 0.35), cy + size), (cx + int(size * 0.35), cy + size)]
        pygame.draw.polygon(surface, color, stem)


def draw_playing_card(surface, x, y, card, font, font_bold, hidden=False, width=76, height=110):
    pygame.draw.rect(surface, (10, 35, 20), (x + 4, y + 4, width, height), border_radius=7)
    card_rect = pygame.Rect(x, y, width, height)

    if hidden or card is None:
        pygame.draw.rect(surface, CARD_IVORY, card_rect, border_radius=7)
        inner = card_rect.inflate(-8, -8)
        pygame.draw.rect(surface, CARD_BACK_RED, inner, border_radius=5)
        pygame.draw.rect(surface, BRASS_GOLD, inner, width=1, border_radius=5)
        cx, cy = card_rect.center
        pygame.draw.polygon(surface, BRASS_GOLD, [(cx, cy - 16), (cx + 12, cy), (cx, cy + 16), (cx - 12, cy)], width=2)
        pygame.draw.rect(surface, SUIT_BLACK, card_rect, width=2, border_radius=7)
        return

    rank, suit = card
    pygame.draw.rect(surface, CARD_IVORY, card_rect, border_radius=7)
    pygame.draw.rect(surface, SUIT_BLACK, card_rect, width=2, border_radius=7)

    color = SUIT_RED if suit in ("H", "D") else SUIT_BLACK
    r_surf = font_bold.render(rank, True, color)
    surface.blit(r_surf, (x + 7, y + 6))
    draw_suit_pip(surface, suit, x + 14, y + 32, 6)

    surface.blit(r_surf, (x + width - r_surf.get_width() - 7, y + height - 24))
    draw_suit_pip(surface, suit, x + width - 14, y + height - 34, 6)

    cx, cy = card_rect.center
    if rank in ("J", "Q", "K"):
        inner_box = card_rect.inflate(-26, -36)
        pygame.draw.rect(surface, (232, 224, 205), inner_box, border_radius=4)
        pygame.draw.rect(surface, BRASS_GOLD, inner_box, width=1, border_radius=4)
        draw_suit_pip(surface, suit, cx, cy, 14)
    else:
        draw_suit_pip(surface, suit, cx, cy, 18)


def draw_card_shoe(surface, font):
    """Draws the mahogany dealing shoe in the top-right corner of the baize."""
    sx, sy = SHOE_POS
    pygame.draw.rect(surface, RAIL_WOOD, (sx - 8, sy - 8, 62, 86), border_radius=6)
    pygame.draw.rect(surface, BRASS_GOLD, (sx - 8, sy - 8, 62, 86), width=2, border_radius=6)
    pygame.draw.rect(surface, CARD_BACK_RED, (sx - 2, sy - 2, 50, 74), border_radius=4)
    lbl = font.render("SHOE", True, BRASS_GOLD)
    surface.blit(lbl, (sx + 23 - lbl.get_width() // 2, sy + 82))


def draw_chip_stack(surface, x, y, amount, font, label_prefix=""):
    num_chips = min(7, max(1, amount // 6)) if amount > 0 else 0
    for i in range(num_chips):
        cy = y - i * 5
        pygame.draw.ellipse(surface, (140, 25, 25), (x, cy, 32, 14))
        pygame.draw.ellipse(surface, CARD_IVORY, (x, cy, 32, 14), width=2)
        pygame.draw.ellipse(surface, BRASS_GOLD, (x + 6, cy + 3, 20, 8), width=1)
    txt = f"{label_prefix}{amount} Chips" if label_prefix else f"{amount} Chips"
    lbl = font.render(txt, True, CARD_IVORY)
    surface.blit(lbl, (x + 40, y - 2))


# =========================================================================
# 2. BLACKJACK (TWENTY-ONE) ENGINE WITH PACED DEALER ANIMATIONS
# =========================================================================
def calc_blackjack_score(hand):
    total, aces = 0, 0
    for rank, _ in hand:
        if rank in ("J", "Q", "K"):
            total += 10
        elif rank == "A":
            total += 11
            aces += 1
        else:
            total += int(rank)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def init_blackjack(player):
    player["bj_phase"] = "BETTING"  # "BETTING", "PLAYER_TURN", "DEALER_TURN", "ROUND_OVER"
    player["bj_stake"] = 5
    player["bj_deck"] = create_shuffled_deck()
    player["bj_player_hand"] = []
    player["bj_dealer_hand"] = []
    player["bj_dealer_revealed"] = False
    player["card_spawn_ticks"] = {}
    player["bj_banner"] = "The Croupier taps the shoe. \"Select your stake and deal the cards!\""
    return player, "You take a seat at the Twenty-One baize.", "CASINO_BLACKJACK"


def resolve_blackjack_action(action, player):
    chips = player.get("casino_chips", 0)
    stake = player.get("bj_stake", 5)

    if action.startswith("stake_"):
        new_stake = int(action.split("_")[1])
        player["bj_stake"] = new_stake
        player["bj_banner"] = f"Wager set to {new_stake} Chips. Click [Deal Hand] when ready."
        return player, None, "CASINO_BLACKJACK"

    if action == "deal":
        if chips < stake:
            player["bj_banner"] = f"\"You need at least {stake} Chips to deal! Visit the Cashier cage for more.\""
            return player, None, "CASINO_BLACKJACK"

        player["casino_chips"] -= stake
        deck = create_shuffled_deck()
        p_hand = [deck.pop(), deck.pop()]
        d_hand = [deck.pop(), deck.pop()]
        player["bj_deck"] = deck
        player["bj_player_hand"] = p_hand
        player["bj_dealer_hand"] = d_hand
        player["bj_dealer_revealed"] = False

        # Staggered sliding card animations from the shoe
        player["card_spawn_ticks"] = {}
        schedule_card_anim(player, "bj_p_0", 0)
        schedule_card_anim(player, "bj_d_0", 130)
        schedule_card_anim(player, "bj_p_1", 260)
        schedule_card_anim(player, "bj_d_1", 390)

        p_score = calc_blackjack_score(p_hand)
        d_score = calc_blackjack_score(d_hand)

        if p_score == 21:
            player["bj_phase"] = "ROUND_OVER"
            player["bj_dealer_revealed"] = True
            if d_score == 21:
                player["casino_chips"] += stake
                player["bj_banner"] = "Both you and the Dealer hit Natural 21! Push — your stake is returned."
            else:
                payout = stake + int(stake * 1.5)
                player["casino_chips"] += payout
                player["bj_banner"] = f"NATURAL TWENTY-ONE! You win a 3-to-2 payout (+{payout} Chips)!"
            return player, player["bj_banner"], "CASINO_BLACKJACK"

        player["bj_phase"] = "PLAYER_TURN"
        player["bj_banner"] = f"You hold {p_score}. Dealer shows {d_hand[0][0]}. Will you Hit, Stand, or Double Down?"
        return player, None, "CASINO_BLACKJACK"

    p_hand = player["bj_player_hand"]
    d_hand = player["bj_dealer_hand"]
    deck = player["bj_deck"]

    if action == "double":
        if chips < stake:
            player["bj_banner"] = "\"Not enough chips to Double Down!\""
            return player, None, "CASINO_BLACKJACK"
        player["casino_chips"] -= stake
        player["bj_stake"] = stake * 2
        stake = player["bj_stake"]
        p_hand.append(deck.pop())
        schedule_card_anim(player, f"bj_p_{len(p_hand)-1}", 0)
        p_score = calc_blackjack_score(p_hand)
        if p_score > 21:
            player["bj_phase"] = "ROUND_OVER"
            player["bj_dealer_revealed"] = True
            player["bj_banner"] = f"Double Down drew {p_hand[-1][0]} — BUST at {p_score}! House takes {stake} Chips."
            return player, player["bj_banner"], "CASINO_BLACKJACK"
        action = "stand"

    if action == "hit":
        p_hand.append(deck.pop())
        schedule_card_anim(player, f"bj_p_{len(p_hand)-1}", 0)
        p_score = calc_blackjack_score(p_hand)
        if p_score > 21:
            player["bj_phase"] = "ROUND_OVER"
            player["bj_dealer_revealed"] = True
            player["bj_banner"] = f"You drew {p_hand[-1][0]} and BUSTED with {p_score}! House wins {stake} Chips."
            return player, player["bj_banner"], "CASINO_BLACKJACK"
        elif p_score == 21:
            action = "stand"
        else:
            player["bj_banner"] = f"You drew {p_hand[-1][0]} (Total: {p_score}). Hit or Stand?"
            return player, None, "CASINO_BLACKJACK"

    if action == "stand":
        # Start paced dealer reveal & card-by-card drawing
        player["bj_phase"] = "DEALER_TURN"
        player["bj_dealer_revealed"] = False
        player["bj_next_step_tick"] = pygame.time.get_ticks() + 480
        player["bj_banner"] = f"You stand on {calc_blackjack_score(p_hand)}. Croupier Fortunesmile reaches for her hole card..."
        return player, None, "CASINO_BLACKJACK"

    return player, None, "CASINO_BLACKJACK"


def step_blackjack_dealer_turn(player):
    """Called automatically by the renderer timer to reveal and draw dealer cards one by one."""
    now = pygame.time.get_ticks()
    if now < player.get("bj_next_step_tick", 0):
        return

    d_hand = player["bj_dealer_hand"]
    p_hand = player["bj_player_hand"]
    deck = player["bj_deck"]
    stake = player.get("bj_stake", 5)

    if not player.get("bj_dealer_revealed"):
        player["bj_dealer_revealed"] = True
        d_score = calc_blackjack_score(d_hand)
        player["bj_banner"] = f"Dealer flips {d_hand[1][0]} (Dealer Total: {d_score})."
        player["bj_next_step_tick"] = now + 680
        return

    d_score = calc_blackjack_score(d_hand)
    if d_score < 17:
        card = deck.pop()
        d_hand.append(card)
        schedule_card_anim(player, f"bj_d_{len(d_hand)-1}", 0)
        new_score = calc_blackjack_score(d_hand)
        player["bj_banner"] = f"Dealer draws {card[0]} (Dealer Total: {new_score})..."
        player["bj_next_step_tick"] = now + 700
        return

    # Dealer is at 17+ or busted — resolve outcome
    p_score = calc_blackjack_score(p_hand)
    player["bj_phase"] = "ROUND_OVER"
    if d_score > 21:
        winnings = stake * 2
        player["casino_chips"] += winnings
        player["bj_banner"] = f"Dealer busts with {d_score}! YOU WIN {winnings} Chips!"
    elif p_score > d_score:
        winnings = stake * 2
        player["casino_chips"] += winnings
        player["bj_banner"] = f"You stand on {p_score} vs. Dealer's {d_score}. YOU WIN {winnings} Chips!"
    elif p_score == d_score:
        player["casino_chips"] += stake
        player["bj_banner"] = f"Both hold {p_score}. PUSH! Your {stake} Chips are returned."
    else:
        player["bj_banner"] = f"Dealer stands on {d_score} against your {p_score}. House takes {stake} Chips."


# =========================================================================
# 3. TEXAS HOLD'EM FREEZEOUT ENGINE (BUY-IN, BLINDS, SLIDER & WIPEOUT)
# =========================================================================
HAND_CATEGORY_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card"
}

POKER_MIN_BUYIN = 50
SMALL_BLIND = 2
BIG_BLIND = 4
SLIDER_RECT = pygame.Rect(245, 476, 260, 18)


def evaluate_5card_hand(cards):
    vals = sorted([RANK_VALUES[r] for r, _ in cards], reverse=True)
    suits = [s for _, s in cards]
    is_flush = len(set(suits)) == 1

    unique_vals = sorted(set(vals), reverse=True)
    is_straight = False
    straight_high = 0
    if len(unique_vals) == 5:
        if unique_vals[0] - unique_vals[4] == 4:
            is_straight = True
            straight_high = unique_vals[0]
        elif unique_vals == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    if is_straight and is_flush:
        return (8, [straight_high])

    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    groups = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    pattern = [g[1] for g in groups]
    ordered_vals = [g[0] for g in groups]

    if pattern == [4, 1]: return (7, ordered_vals)
    if pattern == [3, 2]: return (6, ordered_vals)
    if is_flush:          return (5, vals)
    if is_straight:       return (4, [straight_high])
    if pattern == [3, 1, 1]: return (3, ordered_vals)
    if pattern == [2, 2, 1]: return (2, ordered_vals)
    if pattern == [2, 1, 1, 1]: return (1, ordered_vals)
    return (0, vals)


def get_best_poker_hand(seven_cards):
    if len(seven_cards) < 5:
        return (0, [0]), "Incomplete"
    best_score = (-1, [])
    for combo in itertools.combinations(seven_cards, 5):
        score = evaluate_5card_hand(combo)
        if score > best_score:
            best_score = score
    return best_score, HAND_CATEGORY_NAMES[best_score[0]]


def get_poker_raise_bounds(player):
    """Calculates the minimum and maximum additional chips the player can raise."""
    to_call = player.get("poker_to_call", 0)
    avail_after_call = max(0, player.get("casino_chips", 0) - to_call)
    ever_remaining = max(0, player.get("poker_ever_stack", 0))
    max_raise = min(avail_after_call, ever_remaining)
    if max_raise <= 0:
        return 0, 0
    min_raise = min(BIG_BLIND, max_raise)
    return min_raise, max_raise


def clamp_poker_raise(player, val):
    min_r, max_r = get_poker_raise_bounds(player)
    if max_r <= 0:
        player["poker_raise_amt"] = 0
        player["poker_raise_str"] = "0"
    else:
        clamped = max(min_r, min(max_r, int(val)))
        player["poker_raise_amt"] = clamped
        player["poker_raise_str"] = str(clamped)


def handle_poker_input_event(event, player):
    """Handles mouse dragging on the Raise Slider and keyboard typing for exact raise amounts."""
    if player.get("poker_phase") not in ("PREFLOP", "FLOP", "TURN", "RIVER"):
        return
    if player.get("poker_subphase") != "PLAYER_TURN":
        return

    min_r, max_r = get_poker_raise_bounds(player)
    if max_r <= 0:
        return

    # Mouse click or drag on the brass slider track
    if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
        if event.type == pygame.MOUSEMOTION and not pygame.mouse.get_pressed()[0]:
            return
        mx, my = event.pos
        hit_rect = SLIDER_RECT.inflate(16, 14)
        if hit_rect.collidepoint(mx, my):
            ratio = (mx - SLIDER_RECT.x) / float(SLIDER_RECT.width)
            ratio = max(0.0, min(1.0, ratio))
            raw_val = round(min_r + ratio * (max_r - min_r))
            clamp_poker_raise(player, raw_val)

    # Keyboard typing (0-9 and Backspace)
    elif event.type == pygame.KEYDOWN:
        cur_str = player.get("poker_raise_str", str(player.get("poker_raise_amt", min_r)))
        if event.key == pygame.K_BACKSPACE:
            cur_str = cur_str[:-1]
            player["poker_raise_str"] = cur_str
            player["poker_raise_amt"] = max(min_r, min(max_r, int(cur_str))) if cur_str.isdigit() else min_r
        elif event.unicode and event.unicode.isdigit():
            new_str = (cur_str + event.unicode).lstrip("0") or "0"
            if len(new_str) <= 4:
                val = int(new_str)
                if val > max_r:
                    val = max_r
                    new_str = str(val)
                player["poker_raise_str"] = new_str
                player["poker_raise_amt"] = max(min_r, val)


def init_poker(player):
    chips = player.get("casino_chips", 0)
    if chips < POKER_MIN_BUYIN:
        return (
            player,
            f"Everpenitent taps his stack of ivory chips. \"Minimum buy-in at this table is {POKER_MIN_BUYIN} Chips, stranger. "
            "Visit Croupier Fortunesmile's cashier cage first.\"",
            "NPC_DIALOGUE"
        )

    player["poker_ever_stack"] = POKER_MIN_BUYIN
    player["poker_dealer"] = "ever"  # Will flip to "player" on Hand 1
    player["poker_raise_amt"] = BIG_BLIND
    player["poker_raise_str"] = str(BIG_BLIND)
    player["card_spawn_ticks"] = {}
    return resolve_poker_action("deal", player)


def advance_poker_street(player):
    """Deals the next community card(s) with smooth animations from the shoe."""
    phase = player["poker_phase"]
    deck = player["poker_deck"]
    player["poker_to_call"] = 0

    if phase == "PREFLOP":
        player["poker_phase"] = "FLOP"
        player["poker_community"] = [deck.pop(), deck.pop(), deck.pop()]
        schedule_card_anim(player, "pk_c_0", 0)
        schedule_card_anim(player, "pk_c_1", 140)
        schedule_card_anim(player, "pk_c_2", 280)
        street_msg = "The Flop slides onto the baize (3 cards)."
    elif phase == "FLOP":
        player["poker_phase"] = "TURN"
        player["poker_community"].append(deck.pop())
        schedule_card_anim(player, "pk_c_3", 0)
        street_msg = "The Turn card hits the baize."
    elif phase == "TURN":
        player["poker_phase"] = "RIVER"
        player["poker_community"].append(deck.pop())
        schedule_card_anim(player, "pk_c_4", 0)
        street_msg = "The River card is dealt. Final betting round!"
    elif phase == "RIVER":
        return resolve_poker_showdown(player)

    # If either player is All-In (0 chips remaining), automatically run out the remaining streets!
    if player.get("casino_chips", 0) == 0 or player.get("poker_ever_stack", 0) == 0:
        player["poker_subphase"] = "ALL_IN_RUNOUT"
        player["poker_next_step_tick"] = pygame.time.get_ticks() + 850
        player["poker_banner"] = street_msg + " (All-In — dealing next card...)"
    else:
        player["poker_subphase"] = "PLAYER_TURN"
        clamp_poker_raise(player, player.get("poker_raise_amt", BIG_BLIND))
        player["poker_banner"] = street_msg + " Check or Raise?"

    return player, None, "CASINO_POKER"


def resolve_poker_showdown(player):
    comm = player["poker_community"]
    p_score, p_name = get_best_poker_hand(player["poker_player_cards"] + comm)
    e_score, e_name = get_best_poker_hand(player["poker_ever_cards"] + comm)
    pot = player["poker_pot"]
    player["poker_pot"] = 0
    player["poker_subphase"] = "HAND_OVER"

    if p_score > e_score:
        player["casino_chips"] += pot
        outcome = f"SHOWDOWN: Your {p_name} beats Everpenitent's {e_name}! You scoop the {pot}-Chip pot!"
    elif p_score < e_score:
        player["poker_ever_stack"] += pot
        outcome = f"SHOWDOWN: Everpenitent's {e_name} beats your {p_name}. He rakes in {pot} Chips."
    else:
        half = pot // 2
        player["casino_chips"] += half
        player["poker_ever_stack"] += (pot - half)
        outcome = f"SPLIT POT! Both hold {p_name}. You each reclaim {half} Chips."

    # Check if either player has been completely wiped out!
    if player["poker_ever_stack"] <= 0:
        player["poker_ever_stack"] = 0
        player["poker_phase"] = "MATCH_WON"
        if "dtessera terra world map" not in player["inventory"] and not player.get("everpenitent_defeated"):
            player["everpenitent_defeated"] = True
            player["inventory"].append("dtessera terra world map")
            outcome += " Everpenitent is WIPED OUT! He curses and tosses the Grand Dtessera Terra World Map onto the baize!"
        else:
            outcome += " Everpenitent is completely WIPED OUT! You have conquered the high-stakes table!"
    elif player["casino_chips"] <= 0:
        player["casino_chips"] = 0
        player["poker_phase"] = "MATCH_LOST"
        outcome += " You are WIPED OUT of chips! Visit the Cashier cage before challenging Everpenitent again."
    else:
        player["poker_phase"] = "SHOWDOWN"

    player["poker_banner"] = outcome
    return player, outcome, "CASINO_POKER"


def resolve_poker_action(action, player):
    chips = player.get("casino_chips", 0)
    ever_stack = player.get("poker_ever_stack", POKER_MIN_BUYIN)

    # --- QUICK SLIDER BUTTONS (-5, +5, MAX) ---
    if action == "raise_minus":
        clamp_poker_raise(player, player.get("poker_raise_amt", BIG_BLIND) - 5)
        return player, None, "CASINO_POKER"
    if action == "raise_plus":
        clamp_poker_raise(player, player.get("poker_raise_amt", BIG_BLIND) + 5)
        return player, None, "CASINO_POKER"
    if action == "raise_max":
        _, max_r = get_poker_raise_bounds(player)
        clamp_poker_raise(player, max_r)
        return player, None, "CASINO_POKER"

    # --- DEAL NEXT HAND IN THE FREEZEOUT MATCH ---
    if action == "deal":
        if ever_stack <= 0:
            player["poker_ever_stack"] = POKER_MIN_BUYIN
            ever_stack = POKER_MIN_BUYIN
        if chips <= 0:
            player["poker_banner"] = "\"You're out of chips! Visit the Cashier cage to buy back in.\""
            player["poker_phase"] = "MATCH_LOST"
            return player, None, "CASINO_POKER"

        deck = create_shuffled_deck()
        player["poker_deck"] = deck
        player["poker_player_cards"] = [deck.pop(), deck.pop()]
        player["poker_ever_cards"] = [deck.pop(), deck.pop()]
        player["poker_community"] = []

        player["card_spawn_ticks"] = {}
        schedule_card_anim(player, "pk_p_0", 0)
        schedule_card_anim(player, "pk_e_0", 120)
        schedule_card_anim(player, "pk_p_1", 240)
        schedule_card_anim(player, "pk_e_1", 360)

        # Rotate Dealer Button & Post Blinds (Small Blind = 2, Big Blind = 4)
        dealer = "player" if player.get("poker_dealer") == "ever" else "ever"
        player["poker_dealer"] = dealer

        if dealer == "player":
            # Player posts Small Blind (2), Everpenitent posts Big Blind (4)
            p_blind = min(chips, SMALL_BLIND)
            e_blind = min(ever_stack, BIG_BLIND)
            player["casino_chips"] -= p_blind
            player["poker_ever_stack"] -= e_blind
            player["poker_pot"] = p_blind + e_blind
            player["poker_to_call"] = max(0, e_blind - p_blind)
            player["poker_banner"] = f"You are Dealer (SB: {p_blind}). Everpenitent posts BB ({e_blind}). Call {player['poker_to_call']} or Raise?"
        else:
            # Everpenitent posts Small Blind (2) and matches to Big Blind (4) so Player gets the option
            p_blind = min(chips, BIG_BLIND)
            e_blind = min(ever_stack, BIG_BLIND)
            player["casino_chips"] -= p_blind
            player["poker_ever_stack"] -= e_blind
            player["poker_pot"] = p_blind + e_blind
            player["poker_to_call"] = 0
            player["poker_banner"] = f"You post Big Blind ({p_blind}). Everpenitent calls {e_blind}. Check or Raise?"

        player["poker_phase"] = "PREFLOP"
        player["poker_subphase"] = "PLAYER_TURN"
        clamp_poker_raise(player, BIG_BLIND)
        return player, None, "CASINO_POKER"

    # --- PLAYER FOLDS ---
    if action == "fold":
        pot = player.get("poker_pot", 0)
        player["poker_ever_stack"] += pot
        player["poker_pot"] = 0
        player["poker_subphase"] = "HAND_OVER"
        if player["casino_chips"] <= 0:
            player["poker_phase"] = "MATCH_LOST"
            player["poker_banner"] = "You fold with 0 Chips left — Everpenitent wipes you out!"
        else:
            player["poker_phase"] = "SHOWDOWN"
            player["poker_banner"] = f"You fold. Everpenitent chuckles and adds the {pot}-Chip pot to his stack."
        return player, player["poker_banner"], "CASINO_POKER"

    to_call = player.get("poker_to_call", 0)

    # --- PLAYER CHECKS OR CALLS ---
    if action == "check_call":
        if to_call > 0:
            wager = min(chips, to_call)
            player["casino_chips"] -= wager
            player["poker_pot"] += wager
            player["poker_to_call"] = 0
            player["poker_banner"] = f"You call {wager} Chips. Dealing next street..."
        else:
            player["poker_banner"] = "You check. Everpenitent taps the table..."

        player["poker_subphase"] = "AI_THINKING"
        player["poker_pending_action"] = ("AFTER_CHECK_CALL", 0)
        player["poker_next_step_tick"] = pygame.time.get_ticks() + 500
        return player, None, "CASINO_POKER"

    # --- PLAYER RAISES (CUSTOM SLIDER / TYPED VALUE) ---
    if action == "raise_custom":
        min_r, max_r = get_poker_raise_bounds(player)
        if max_r <= 0:
            return resolve_poker_action("check_call", player)

        raise_amt = max(min_r, min(max_r, int(player.get("poker_raise_amt", min_r))))
        total_put_in = to_call + raise_amt
        player["casino_chips"] -= total_put_in
        player["poker_pot"] += total_put_in
        player["poker_to_call"] = 0

        player["poker_banner"] = f"You raise by {raise_amt} Chips! Everpenitent narrows his eyes and considers his stack..."
        player["poker_subphase"] = "AI_THINKING"
        player["poker_pending_action"] = ("AFTER_PLAYER_RAISE", raise_amt)
        player["poker_next_step_tick"] = pygame.time.get_ticks() + 600
        return player, None, "CASINO_POKER"

    return player, None, "CASINO_POKER"


def step_poker_animations(player):
    """Processes timed AI responses and street transitions so Poker never feels instant/jerky."""
    now = pygame.time.get_ticks()
    sub = player.get("poker_subphase", "PLAYER_TURN")
    if sub not in ("AI_THINKING", "DEALING_NEXT_STREET", "ALL_IN_RUNOUT"):
        return
    if now < player.get("poker_next_step_tick", 0):
        return

    if sub == "ALL_IN_RUNOUT":
        advance_poker_street(player)
        return

    if sub == "DEALING_NEXT_STREET":
        advance_poker_street(player)
        return

    # sub == "AI_THINKING"
    kind, raise_amt = player.get("poker_pending_action", ("AFTER_CHECK_CALL", 0))
    ever_stack = player.get("poker_ever_stack", 0)
    chips = player.get("casino_chips", 0)

    ever_cards = player["poker_ever_cards"] + player["poker_community"]
    ai_cat = get_best_poker_hand(ever_cards)[0][0] if len(ever_cards) >= 5 else (
        1 if ever_cards[0][0] == ever_cards[1][0] or RANK_VALUES[ever_cards[0][0]] >= 12 else 0
    )

    if kind == "AFTER_CHECK_CALL":
        # Everpenitent can bet out if he has a strong hand and stacks allow it
        if ai_cat >= 2 and ever_stack >= BIG_BLIND and chips >= BIG_BLIND and random.random() < 0.35:
            ai_bet = min(BIG_BLIND, ever_stack, chips)
            player["poker_ever_stack"] -= ai_bet
            player["poker_pot"] += ai_bet
            player["poker_to_call"] = ai_bet
            player["poker_subphase"] = "PLAYER_TURN"
            clamp_poker_raise(player, BIG_BLIND)
            player["poker_banner"] = f"Everpenitent bets {ai_bet} Chips! Call {ai_bet}, Raise, or Fold?"
            return
        advance_poker_street(player)
        return

    if kind == "AFTER_PLAYER_RAISE":
        # Everpenitent folds weak hands if raised heavily
        if ai_cat == 0 and raise_amt >= 8 and ever_stack > raise_amt and random.random() < 0.32:
            pot = player["poker_pot"]
            player["casino_chips"] += pot
            player["poker_pot"] = 0
            player["poker_phase"] = "SHOWDOWN"
            player["poker_subphase"] = "HAND_OVER"
            player["poker_banner"] = f"Everpenitent scowls at your {raise_amt}-Chip raise and folds! You scoop {pot} Chips!"
            return

        # Everpenitent counter-raises on strong hands
        if ai_cat >= 2 and ever_stack > raise_amt + BIG_BLIND and chips >= BIG_BLIND and random.random() < 0.30:
            re_raise = min(BIG_BLIND, ever_stack - raise_amt, chips)
            total_ai = raise_amt + re_raise
            player["poker_ever_stack"] -= total_ai
            player["poker_pot"] += total_ai
            player["poker_to_call"] = re_raise
            player["poker_subphase"] = "PLAYER_TURN"
            clamp_poker_raise(player, BIG_BLIND)
            player["poker_banner"] = f"Everpenitent calls your {raise_amt} and raises {re_raise} more! (Call {re_raise} or Fold)"
            return

        # Otherwise Everpenitent calls the raise, pauses briefly, and then the next street deals out
        call_amt = min(ever_stack, raise_amt)
        player["poker_ever_stack"] -= call_amt
        player["poker_pot"] += call_amt
        player["poker_banner"] = f"Everpenitent calls {call_amt} Chips (Pot: {player['poker_pot']}). Dealing next street..."
        player["poker_subphase"] = "DEALING_NEXT_STREET"
        player["poker_next_step_tick"] = now + 520


# =========================================================================
# 4. FULL-SCREEN BAIZE & CARD TABLE RENDERER (800 x 600)
# =========================================================================
def draw_casino_card_table(screen, player, font, font_bold, title_font, menu_state):
    if menu_state == "CASINO_ROULETTE":
        draw_roulette_table(screen, player, font, font_bold, title_font)
        return
    if menu_state == "CASINO_CRAPS":
        draw_craps_table(screen, player, font, font_bold, title_font)
        return
    # Step active animations first
    if menu_state == "CASINO_BLACKJACK" and player.get("bj_phase") == "DEALER_TURN":
        step_blackjack_dealer_turn(player)
    elif menu_state == "CASINO_POKER":
        step_poker_animations(player)

    # 1. Outer Mahogany Frame & Green Baize
    screen.fill(RAIL_WOOD)
    baize_rect = pygame.Rect(16, 16, 768, 568)
    pygame.draw.rect(screen, BAIZE_GREEN, baize_rect, border_radius=22)
    pygame.draw.rect(screen, BRASS_GOLD, baize_rect, width=3, border_radius=22)

    inner_ring = pygame.Rect(46, 70, 708, 435)
    pygame.draw.rect(screen, BAIZE_LINE, inner_ring, width=2, border_radius=60)

    # 2. Top Brass Header Bar
    header_rect = pygame.Rect(30, 26, 740, 38)
    pygame.draw.rect(screen, BAIZE_DARK, header_rect, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, header_rect, width=1, border_radius=8)

    game_title = "THE HOUSE OF GAMES — TWENTY-ONE" if menu_state == "CASINO_BLACKJACK" else "THE HOUSE OF GAMES — TEXAS HOLD'EM"
    t_surf = title_font.render(game_title, True, BRASS_GOLD)
    screen.blit(t_surf, (45, 33))

    wallet_str = f"Your Chips: {player.get('casino_chips', 0)}  |  Purse: {player.get('silver', 0)}s"
    w_surf = font_bold.render(wallet_str, True, CARD_IVORY)
    screen.blit(w_surf, (755 - w_surf.get_width(), 36))

    # Draw Card Shoe on Top-Right Baize
    draw_card_shoe(screen, font)

    # 3. Opponent Nameplate & Dialogue Banner
    opp_box = pygame.Rect(65, 76, 600, 50)
    pygame.draw.rect(screen, (18, 48, 30), opp_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, opp_box, width=1, border_radius=8)

    if menu_state == "CASINO_BLACKJACK":
        banner_txt = player.get("bj_banner", "")
        opp_label = "CROUPIER FORTUNESMILE (DEALER — STANDS ON 17)"
        d_hand = player.get("bj_dealer_hand", [])
        phase = player.get("bj_phase", "BETTING")
        revealed = player.get("bj_dealer_revealed", False)

        # Dealer Cards with smooth shoe slide
        start_x = 400 - (len(d_hand) * 86) // 2
        for idx, card in enumerate(d_hand):
            hide_card = (idx == 1 and not revealed and phase in ("PLAYER_TURN", "DEALER_TURN"))
            cx, cy = get_animated_card_pos(player, f"bj_d_{idx}", start_x + idx * 86, 142)
            draw_playing_card(screen, cx, cy, card, font, font_bold, hidden=hide_card)

        if d_hand:
            hide_second = (not revealed and phase in ("PLAYER_TURN", "DEALER_TURN"))
            d_val = calc_blackjack_score([d_hand[0]]) if hide_second else calc_blackjack_score(d_hand)
            suffix = "+" if hide_second else ""
            d_badge = font_bold.render(f"Dealer: {d_val}{suffix}", True, CARD_IVORY)
            screen.blit(d_badge, (65, 188))

        # Center Stake Circle
        pygame.draw.circle(screen, BAIZE_DARK, (400, 300), 40)
        pygame.draw.circle(screen, BRASS_GOLD, (400, 300), 40, width=2)
        draw_chip_stack(screen, 350, 294, player.get("bj_stake", 5), font_bold, "Stake: ")

        # Player Cards with smooth shoe slide
        p_hand = player.get("bj_player_hand", [])
        p_start_x = 400 - (len(p_hand) * 86) // 2
        for idx, card in enumerate(p_hand):
            cx, cy = get_animated_card_pos(player, f"bj_p_{idx}", p_start_x + idx * 86, 362)
            draw_playing_card(screen, cx, cy, card, font, font_bold)

        if p_hand:
            p_val = calc_blackjack_score(p_hand)
            p_badge = font_bold.render(f"Your Hand: {p_val}", True, BRASS_GOLD)
            screen.blit(p_badge, (65, 408))

    elif menu_state == "CASINO_POKER":
        banner_txt = player.get("poker_banner", "")
        ever_stack = player.get("poker_ever_stack", POKER_MIN_BUYIN)
        opp_label = f"EVERPENITENT — STACK: {ever_stack} CHIPS (BLINDS: {SMALL_BLIND}/{BIG_BLIND})"
        phase = player.get("poker_phase", "PREFLOP")

        # Everpenitent's Chip Stack & Dealer Button
        draw_chip_stack(screen, 50, 178, ever_stack, font_bold, "Everpenitent: ")
        if player.get("poker_dealer") == "ever":
            pygame.draw.circle(screen, BRASS_GOLD, (285, 180), 13)
            d_txt = font_bold.render("D", True, SUIT_BLACK)
            screen.blit(d_txt, (285 - d_txt.get_width() // 2, 172))

        # Everpenitent's 2 Hole Cards
        e_hand = player.get("poker_ever_cards", [])
        show_ever = phase in ("SHOWDOWN", "MATCH_WON", "MATCH_LOST") and player.get("poker_subphase") == "HAND_OVER"
        for idx, card in enumerate(e_hand):
            cx, cy = get_animated_card_pos(player, f"pk_e_{idx}", 320 + idx * 86, 134)
            draw_playing_card(screen, cx, cy, card, font, font_bold, hidden=(not show_ever), width=68, height=96)

        # 5 Community Cards Slots
        comm = player.get("poker_community", [])
        for slot in range(5):
            tx = 195 + slot * 84
            ty = 242
            pygame.draw.rect(screen, BAIZE_DARK, (tx, ty, 70, 100), border_radius=7)
            pygame.draw.rect(screen, BAIZE_LINE, (tx, ty, 70, 100), width=2, border_radius=7)
            if slot < len(comm):
                cx, cy = get_animated_card_pos(player, f"pk_c_{slot}", tx, ty)
                draw_playing_card(screen, cx, cy, comm[slot], font, font_bold, width=70, height=100)

        # Center Pot Display
        draw_chip_stack(screen, 50, 290, player.get("poker_pot", 0), font_bold, "Pot: ")

        # Player's Stack, Dealer Button & 2 Hole Cards
        draw_chip_stack(screen, 50, 395, player.get("casino_chips", 0), font_bold, "Your Stack: ")
        if player.get("poker_dealer") == "player":
            pygame.draw.circle(screen, BRASS_GOLD, (285, 405), 13)
            d_txt = font_bold.render("D", True, SUIT_BLACK)
            screen.blit(d_txt, (285 - d_txt.get_width() // 2, 397))

        p_hand = player.get("poker_player_cards", [])
        for idx, card in enumerate(p_hand):
            cx, cy = get_animated_card_pos(player, f"pk_p_{idx}", 320 + idx * 86, 355)
            draw_playing_card(screen, cx, cy, card, font, font_bold, width=72, height=102)

        if len(p_hand) + len(comm) >= 5:
            _, best_label = get_best_poker_hand(p_hand + comm)
            h_surf = font_bold.render(f"Best Hand: {best_label}", True, BRASS_GOLD)
            screen.blit(h_surf, (520, 395))

        # --- INTERACTIVE RAISE SLIDER & TYPING BOX ---
        min_r, max_r = get_poker_raise_bounds(player)
        if phase in ("PREFLOP", "FLOP", "TURN", "RIVER") and player.get("poker_subphase") == "PLAYER_TURN" and max_r > 0:
            cur_r = max(min_r, min(max_r, int(player.get("poker_raise_amt", min_r))))
            # Slider Bar Label
            s_lbl = font.render(f"Raise Slider ({min_r}–{max_r}):", True, CARD_IVORY)
            screen.blit(s_lbl, (82, 476))

            # Track & Fill
            pygame.draw.rect(screen, BAIZE_DARK, SLIDER_RECT, border_radius=9)
            pygame.draw.rect(screen, BRASS_GOLD, SLIDER_RECT, width=2, border_radius=9)
            ratio = (cur_r - min_r) / float(max(1, max_r - min_r))
            fill_w = int(SLIDER_RECT.width * ratio)
            if fill_w > 0:
                pygame.draw.rect(screen, (175, 50, 40), (SLIDER_RECT.x, SLIDER_RECT.y, fill_w, SLIDER_RECT.height), border_radius=9)
            knob_x = SLIDER_RECT.x + fill_w
            pygame.draw.circle(screen, CARD_IVORY, (knob_x, SLIDER_RECT.centery), 10)
            pygame.draw.circle(screen, BRASS_GOLD, (knob_x, SLIDER_RECT.centery), 10, width=2)

            # Typed Value Box (Type 0-9 / Backspace on keyboard)
            box_rect = pygame.Rect(520, 470, 210, 28)
            pygame.draw.rect(screen, (18, 42, 28), box_rect, border_radius=6)
            pygame.draw.rect(screen, BRASS_GOLD, box_rect, width=1, border_radius=6)
            typed_str = player.get("poker_raise_str", str(cur_r))
            t_lbl = font_bold.render(f"Type Raise: {typed_str} Chips", True, BRASS_GOLD)
            screen.blit(t_lbl, (530, 476))

    # Render Opponent Header & Dialogue Line inside Top Box
    draw_wrapped_banner(screen, opp_label, banner_txt, opp_box, BRASS_GOLD, CARD_IVORY)

    # 4. Bottom Mahogany Action Tray
    tray_rect = pygame.Rect(30, 512, 740, 58)
    pygame.draw.rect(screen, BAIZE_DARK, tray_rect, border_radius=10)
    pygame.draw.rect(screen, BRASS_GOLD, tray_rect, width=1, border_radius=10)

# =========================================================================
# 5. EUROPEAN ROULETTE — 3D PERSPECTIVE WHEEL & FULL BETTING BAIZE
# =========================================================================
WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
    5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26
]
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# Layout Constants for the Interactive Baize Grid (Right Side of Screen)
RL_ZERO_RECT = pygame.Rect(368, 155, 34, 156)   # 0 pocket on baize
RL_GRID_X = 402
RL_GRID_Y = 155
RL_CELL_W = 26
RL_CELL_H = 52  # 3 rows * 52 = 156px tall, 12 cols * 26 = 312px wide (ends at x=714)

# 3D Wheel Center & Perspective Tilt (Left Side of Screen)
WHEEL_CX = 192
WHEEL_CY = 282
WHEEL_TILT = 0.64  # Elliptical Y-compression giving a 3D 38-degree viewing angle


def proj_wheel_3d(r, theta, z=0.0):
    """Projects cylindrical wheel coordinates (r, theta, height_z) onto the 2D screen."""
    x = WHEEL_CX + r * math.cos(theta)
    y = WHEEL_CY + r * math.sin(theta) * WHEEL_TILT - z
    return int(x), int(y)


def init_roulette(player):
    player["rl_phase"] = "BETTING"  # "BETTING", "SPINNING"
    player["rl_chip_val"] = 1
    player["rl_bets"] = []          # List of dicts: {"label", "nums", "mult", "amount", "pos"}
    player["rl_last_bets"] = []
    player["rl_history"] = player.get("rl_history", [])
    player["rl_wheel_angle"] = 0.0
    player["rl_win_num"] = None
    player["rl_hover_bet"] = None
    player["rl_banner"] = (
        "The Croupier gestures to the baize. \"Place your bets!\""
    )
    return player, "You step up to the European Roulette table.", "CASINO_ROULETTE"


def get_grid_num(col, row):
    """Returns the Roulette table number at (col 0..11, row 0..2 from top to bottom)."""
    # Top row (row 0): 3, 6, 9..36 | Mid row (row 1): 2, 5, 8..35 | Bot row (row 2): 1, 4, 7..34
    return col * 3 + (3 - row)


def detect_roulette_bet_at_pos(mx, my):
    """
    Returns a bet descriptor dict {"label", "nums", "mult", "pos"} for the exact spot hovered/clicked,
    including Straight Up, Split, Street, Corner, Six-Line, Columns, Dozens, and Even-Money bets.
    """
    # 1. Zero (0)
    if RL_ZERO_RECT.collidepoint(mx, my):
        return {
            "label": "Straight Up 0 (35:1)",
            "nums": [0],
            "mult": 35,
            "pos": RL_ZERO_RECT.center
        }

    # 2. Inside Number Grid (1..36) + Splits, Streets, Corners, Six-Lines
    gx_end = RL_GRID_X + 12 * RL_CELL_W
    gy_end = RL_GRID_Y + 3 * RL_CELL_H
    if RL_GRID_X <= mx <= gx_end and RL_GRID_Y <= my <= gy_end + 6:
        rel_x = mx - RL_GRID_X
        rel_y = my - RL_GRID_Y
        col = min(11, max(0, int(rel_x // RL_CELL_W)))
        row = min(2, max(0, int(rel_y // RL_CELL_H)))

        rem_x = rel_x - col * RL_CELL_W
        rem_y = rel_y - row * RL_CELL_H
        edge_tol = 6

        near_left = (rem_x <= edge_tol and col > 0)
        near_right = (rem_x >= RL_CELL_W - edge_tol and col < 11)
        near_top = (rem_y <= edge_tol and row > 0)
        near_bot = (rem_y >= RL_CELL_H - edge_tol and row < 2)
        near_street_line = (abs(my - gy_end) <= 7)

        # Bottom Edge of Grid -> Street (3 nums) or Six-Line (6 nums)
        if near_street_line:
            if near_left or near_right:
                c1 = col - 1 if near_left else col
                c2 = c1 + 1
                nums = sorted([get_grid_num(c1, r) for r in range(3)] + [get_grid_num(c2, r) for r in range(3)])
                px = RL_GRID_X + (c1 + 1) * RL_CELL_W
                return {
                    "label": f"Six Line {nums[0]}-{nums[-1]} (5:1)",
                    "nums": nums,
                    "mult": 5,
                    "pos": (px, gy_end)
                }
            else:
                nums = sorted([get_grid_num(col, r) for r in range(3)])
                px = RL_GRID_X + col * RL_CELL_W + RL_CELL_W // 2
                return {
                    "label": f"Street {nums[0]}-{nums[2]} (11:1)",
                    "nums": nums,
                    "mult": 11,
                    "pos": (px, gy_end)
                }

        # 4-Way Interior Intersection -> Corner Bet (4 nums, 8:1)
        if (near_left or near_right) and (near_top or near_bot):
            c1 = col - 1 if near_left else col
            r1 = row - 1 if near_top else row
            nums = sorted([
                get_grid_num(c1, r1), get_grid_num(c1 + 1, r1),
                get_grid_num(c1, r1 + 1), get_grid_num(c1 + 1, r1 + 1)
            ])
            px = RL_GRID_X + (c1 + 1) * RL_CELL_W
            py = RL_GRID_Y + (r1 + 1) * RL_CELL_H
            return {
                "label": f"Corner {nums[0]},{nums[1]},{nums[2]},{nums[3]} (8:1)",
                "nums": nums,
                "mult": 8,
                "pos": (px, py)
            }

        # Horizontal Split between two columns (2 nums, 17:1)
        if near_left or near_right:
            c1 = col - 1 if near_left else col
            nums = sorted([get_grid_num(c1, row), get_grid_num(c1 + 1, row)])
            px = RL_GRID_X + (c1 + 1) * RL_CELL_W
            py = RL_GRID_Y + row * RL_CELL_H + RL_CELL_H // 2
            return {
                "label": f"Split {nums[0]}/{nums[1]} (17:1)",
                "nums": nums,
                "mult": 17,
                "pos": (px, py)
            }

        # Vertical Split between two rows (2 nums, 17:1)
        if near_top or near_bot:
            r1 = row - 1 if near_top else row
            nums = sorted([get_grid_num(col, r1), get_grid_num(col, r1 + 1)])
            px = RL_GRID_X + col * RL_CELL_W + RL_CELL_W // 2
            py = RL_GRID_Y + (r1 + 1) * RL_CELL_H
            return {
                "label": f"Split {nums[0]}/{nums[1]} (17:1)",
                "nums": nums,
                "mult": 17,
                "pos": (px, py)
            }

        # Center of Cell -> Straight Up (1 num, 35:1)
        n = get_grid_num(col, row)
        px = RL_GRID_X + col * RL_CELL_W + RL_CELL_W // 2
        py = RL_GRID_Y + row * RL_CELL_H + RL_CELL_H // 2
        return {
            "label": f"Straight Up {n} (35:1)",
            "nums": [n],
            "mult": 35,
            "pos": (px, py)
        }

    # 3. Right-Hand "2 to 1" Column Boxes (Pays 2:1)
    if gx_end <= mx <= gx_end + 42 and RL_GRID_Y <= my <= gy_end:
        row = min(2, max(0, int((my - RL_GRID_Y) // RL_CELL_H)))
        nums = [get_grid_num(c, row) for c in range(12)]
        cy = RL_GRID_Y + row * RL_CELL_H + RL_CELL_H // 2
        return {
            "label": f"Column {3 - row} (2:1)",
            "nums": nums,
            "mult": 2,
            "pos": (gx_end + 21, cy)
        }

    # 4. Dozen Boxes: 1st 12, 2nd 12, 3rd 12 (Pays 2:1)
    doz_y = gy_end + 8
    if RL_GRID_X <= mx <= gx_end and doz_y <= my <= doz_y + 38:
        d_idx = min(2, max(0, int((mx - RL_GRID_X) // (4 * RL_CELL_W))))
        nums = list(range(d_idx * 12 + 1, (d_idx + 1) * 12 + 1))
        labels = ["1st 12 (1-12)", "2nd 12 (13-24)", "3rd 12 (25-36)"]
        cx = RL_GRID_X + d_idx * 4 * RL_CELL_W + 2 * RL_CELL_W
        return {
            "label": f"{labels[d_idx]} (2:1)",
            "nums": nums,
            "mult": 2,
            "pos": (cx, doz_y + 19)
        }

    # 5. Even-Money Outside Boxes: 1-18, EVEN, RED, BLACK, ODD, 19-36 (Pays 1:1)

    even_y = doz_y + 42
    if RL_GRID_X <= mx <= gx_end and even_y <= my <= even_y + 40:
        b_idx = min(5, max(0, int((mx - RL_GRID_X) // (2 * RL_CELL_W))))
        cx = RL_GRID_X + b_idx * 2 * RL_CELL_W + RL_CELL_W
        cy = even_y + 20
        specs = [
            ("Low 1-18 (1:1)", list(range(1, 19))),
            ("EVEN (1:1)", [n for n in range(1, 37) if n % 2 == 0]),
            ("RED (1:1)", sorted(list(RED_NUMBERS))),
            ("BLACK (1:1)", [n for n in range(1, 37) if n not in RED_NUMBERS]),
            ("ODD (1:1)", [n for n in range(1, 37) if n % 2 == 1]),
            ("High 19-36 (1:1)", list(range(19, 37))),
        ]
        lbl, nums = specs[b_idx]
        return {"label": lbl, "nums": nums, "mult": 1, "pos": (cx, cy)}

    return None


def handle_roulette_event(event, player):
    """Handles mouse hover previews and chip placement clicks on the Roulette baize."""
    if player.get("rl_phase") != "BETTING":
        player["rl_hover_bet"] = None
        return

    if event.type == pygame.MOUSEMOTION:
        player["rl_hover_bet"] = detect_roulette_bet_at_pos(*event.pos)

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        bet_spot = detect_roulette_bet_at_pos(*event.pos)
        if not bet_spot:
            return
        chip_val = player.get("rl_chip_val", 1)
        chips = player.get("casino_chips", 0)
        if chips < chip_val:
            player["rl_banner"] = f"\"You need at least {chip_val} Chips in your stack to place that bet!\""
            return

        player["casino_chips"] -= chip_val
        # Merge onto existing chip stack if clicking the exact same spot
        for existing in player["rl_bets"]:
            if existing["pos"] == bet_spot["pos"]:
                existing["amount"] += chip_val
                player["rl_banner"] = f"Added {chip_val} Chips to {bet_spot['label']} (Total on spot: {existing['amount']})."
                return

        new_bet = dict(bet_spot)
        new_bet["amount"] = chip_val
        player["rl_bets"].append(new_bet)
        player["rl_banner"] = f"Placed {chip_val} Chips on {bet_spot['label']}."


def resolve_roulette_action(action, player):
    """Handles bottom rail button actions for Roulette."""
    if player.get("rl_phase") == "SPINNING":
        return player, None, "CASINO_ROULETTE"

    if action.startswith("chip_"):
        val = int(action.split("_")[1])
        player["rl_chip_val"] = val
        player["rl_banner"] = f"Selected {val}-Chip denomination. Click anywhere on the betting layout to place chips."
        return player, None, "CASINO_ROULETTE"

    if action == "clear":
        refund = sum(b["amount"] for b in player.get("rl_bets", []))
        player["casino_chips"] = player.get("casino_chips", 0) + refund
        player["rl_bets"] = []
        player["rl_banner"] = f"Cleared table and returned {refund} Chips to your stack."
        return player, None, "CASINO_ROULETTE"

    if action == "rebet":
        last_bets = player.get("rl_last_bets", [])
        if not last_bets:
            player["rl_banner"] = "\"No previous bet layout to repeat yet!\""
            return player, None, "CASINO_ROULETTE"
        needed = sum(b["amount"] for b in last_bets)
        refund = sum(b["amount"] for b in player.get("rl_bets", []))
        avail = player.get("casino_chips", 0) + refund
        if avail < needed:
            player["rl_banner"] = f"\"You need {needed} Chips to repeat your last bet layout!\""
            return player, None, "CASINO_ROULETTE"
        player["casino_chips"] = avail - needed
        player["rl_bets"] = [dict(b) for b in last_bets]
        player["rl_banner"] = f"Repeated previous layout ({needed} Chips total). Ready to spin!"
        return player, None, "CASINO_ROULETTE"

    if action == "spin":
        bets = player.get("rl_bets", [])
        if not bets:
            player["rl_banner"] = "\"Place at least one chip on the baize before spinning the wheel!\""
            return player, None, "CASINO_ROULETTE"

        # Save layout for Rebet and launch 3D spin physics
        player["rl_last_bets"] = [dict(b) for b in bets]
        player["rl_phase"] = "SPINNING"
        player["rl_hover_bet"] = None
        player["rl_spin_start_tick"] = pygame.time.get_ticks()
        player["rl_spin_duration"] = 5200  # 5.2 seconds of wheel spin + ball bounce

        win_idx = random.randrange(len(WHEEL_ORDER))
        player["rl_win_idx"] = win_idx
        player["rl_win_num"] = WHEEL_ORDER[win_idx]
        player["rl_start_wheel_angle"] = player.get("rl_wheel_angle", 0.0)
        player["rl_total_wheel_rot"] = 4.0 * math.pi + random.uniform(0.8, 2.4)
        # Random seed for realistic ball bobble/deflector rattle
        player["rl_bounce_seed"] = random.uniform(0.0, 6.28)
        player["rl_banner"] = "Croupier Fortunesmile launches the ivory ball: \"Rien ne va plus — no more bets!\""
        return player, None, "CASINO_ROULETTE"

    return player, None, "CASINO_ROULETTE"


def step_roulette_physics(player):
    """Updates wheel rotation, ball track deceleration, deflector hits, and pocket bounces."""
    if player.get("rl_phase") != "SPINNING":
        return

    now = pygame.time.get_ticks()
    elapsed = now - player.get("rl_spin_start_tick", now)
    dur = float(player.get("rl_spin_duration", 5200))
    t = min(1.0, max(0.0, elapsed / dur))

    # 1. Wheel spins clockwise and smoothly decelerates (cubic ease-out)
    wheel_ease = 1.0 - (1.0 - t) ** 3
    w_angle = player["rl_start_wheel_angle"] + player["rl_total_wheel_rot"] * wheel_ease
    player["rl_wheel_angle"] = w_angle

    # Target pocket angle on the wheel at current frame
    slice_angle = (2.0 * math.pi) / 37.0
    win_idx = player["rl_win_idx"]
    pocket_world_angle = w_angle + (win_idx + 0.5) * slice_angle

    # We also compute where the pocket will be at t = 0.82 (when the ball finishes bouncing)
    ease_82 = 1.0 - (1.0 - 0.82) ** 3
    w_angle_82 = player["rl_start_wheel_angle"] + player["rl_total_wheel_rot"] * ease_82
    target_angle_at_lock = w_angle_82 + (win_idx + 0.5) * slice_angle
    seed = player.get("rl_bounce_seed", 0.0)

    # 2. Ball Trajectory across 4 Physical Stages:
    if t < 0.36:
        # Stage A: High-speed counter-clockwise sprint on the upper mahogany ball track
        p = t / 0.36
        rem_turns = (1.0 - p) ** 1.7 * 16.5 + (1.0 - 0.36) * 6.0
        b_angle = target_angle_at_lock - rem_turns
        b_radius = 132.0
        b_z = 14.0
    elif t < 0.54:
        # Stage B: Ball drops off the track down the sloped apron & ricochets off a brass deflector!
        p = (t - 0.36) / 0.18
        rem_turns = (1.0 - p) * 3.8 + 1.4
        deflector_kick = math.sin(p * math.pi * 3.0 + seed) * 0.22
        b_angle = target_angle_at_lock - rem_turns + deflector_kick
        b_radius = 132.0 - p * 34.0 + abs(math.sin(p * math.pi * 2.0)) * 7.0
        b_z = 14.0 * (1.0 - p) + abs(math.sin(p * math.pi * 3.0)) * 9.0
        player["rl_banner"] = "The ivory ball drops off the rim and clatters against the brass deflectors..."
    elif t < 0.82:
        # Stage C: Ball bobbles and bounces randomly across the pocket frets before settling!
        p = (t - 0.54) / 0.28
        decay = (1.0 - p) ** 1.6
        # Multi-frequency angular & radial bounce across neighboring pockets
        ang_bobble = (
            math.sin(p * 22.0 + seed) * 0.45 * decay
            + math.cos(p * 35.0) * 0.20 * decay
            - (1.0 - p) ** 2 * 1.4
        )
        b_angle = pocket_world_angle + ang_bobble
        b_radius = 91.0 + math.sin(p * 28.0 + seed) * 11.0 * decay
        b_z = -4.0 + abs(math.sin(p * 19.0)) * 15.0 * decay
        player["rl_banner"] = "The ball bounces across the spinning pockets..."
    else:
        # Stage D: Ball is nestled inside the winning pocket and co-rotates as the wheel halts
        p = (t - 0.82) / 0.18
        tiny_settle = math.sin(p * 18.0) * 0.03 * (1.0 - p)
        b_angle = pocket_world_angle + tiny_settle
        b_radius = 90.0
        b_z = -5.0

    player["rl_ball_state"] = (b_radius, b_angle, b_z)

    # 3. When spin finishes (t >= 1.0), evaluate all bets & pay winnings!
    if t >= 1.0:
        player["rl_phase"] = "BETTING"
        win_num = player["rl_win_num"]
        history = player.get("rl_history", [])
        history.append(win_num)
        player["rl_history"] = history[-10:]  # Keep last 10 numbers

        total_wagered = sum(b["amount"] for b in player["rl_bets"])
        total_payout = 0
        winning_labels = []

        for b in player["rl_bets"]:
            if win_num in b["nums"]:
                # Payout returns original stake + (stake * odds_multiplier)
                win_amt = b["amount"] * (b["mult"] + 1)
                total_payout += win_amt
                winning_labels.append(b["label"].split(" (")[0])

        player["casino_chips"] = player.get("casino_chips", 0) + total_payout
        player["rl_bets"] = []

        col_name = "GREEN 0" if win_num == 0 else (f"RED {win_num}" if win_num in RED_NUMBERS else f"BLACK {win_num}")
        if total_payout > 0:
            net = total_payout - total_wagered
            hits = ", ".join(winning_labels[:2])
            player["rl_banner"] = f"Ball lands on {col_name}! Winning hit ({hits}) — Payout: {total_payout} Chips (+{net} net)!"
        else:
            player["rl_banner"] = f"Ball settles into {col_name}. House sweeps {total_wagered} Chips. Place bets or click [Rebet]!"


def draw_roulette_wheel_3d(screen, player, font, font_bold):
    """Renders the tilted 3D European Roulette wheel, brass turret, deflectors, and bouncing ball."""
    w_angle = player.get("rl_wheel_angle", 0.0)
    slice_ang = (2.0 * math.pi) / 37.0

    # 1. Outer 3D Mahogany Bowl Base (Stacked Ellipses for Cylindrical Depth)
    rx_outer, ry_outer = 152, int(152 * WHEEL_TILT)
    for depth in range(26, 0, -2):
        shade = max(18, 46 - depth)
        pygame.draw.ellipse(
            screen, (shade + 18, shade, shade - 6),
            (WHEEL_CX - rx_outer, WHEEL_CY - ry_outer + depth, rx_outer * 2, ry_outer * 2)
        )

    # Top Mahogany Rim & Brass Trim
    rim_rect = pygame.Rect(WHEEL_CX - rx_outer, WHEEL_CY - ry_outer, rx_outer * 2, ry_outer * 2)
    pygame.draw.ellipse(screen, (76, 38, 24), rim_rect)
    pygame.draw.ellipse(screen, BRASS_GOLD, rim_rect, width=3)

    # 2. Sunken Wooden Ball Track & Sloped Apron
    track_rx, track_ry = 136, int(136 * WHEEL_TILT)
    pygame.draw.ellipse(screen, (42, 22, 15), (WHEEL_CX - track_rx, WHEEL_CY - track_ry + 4, track_rx * 2, track_ry * 2))
    pygame.draw.ellipse(screen, (110, 78, 42), (WHEEL_CX - track_rx, WHEEL_CY - track_ry + 4, track_rx * 2, track_ry * 2), width=2)

    # 8 Brass Diamond Deflectors around the sloped apron
    for d_i in range(8):
        da = d_i * (math.pi / 4.0) + 0.2
        dx, dy = proj_wheel_3d(122, da, z=4)
        diamond = [(dx, dy - 4), (dx + 5, dy), (dx, dy + 4), (dx - 5, dy)]
        pygame.draw.polygon(screen, BRASS_GOLD, diamond)

    # 3. 37 Sloped Perspective Pockets (Outer Ring r=112 z=-2 -> Inner Ring r=64 z=-10)
    num_font = pygame.font.Font(None, 16)
    win_num = player.get("rl_win_num")
    is_spinning = (player.get("rl_phase") == "SPINNING")

    for i, num in enumerate(WHEEL_ORDER):
        a0 = w_angle + i * slice_ang
        a1 = a0 + slice_ang
        amid = (a0 + a1) * 0.5

        p_out0 = proj_wheel_3d(113, a0, z=-2)
        p_out1 = proj_wheel_3d(113, a1, z=-2)
        p_in1 = proj_wheel_3d(64, a1, z=-10)
        p_in0 = proj_wheel_3d(64, a0, z=-10)

        if num == 0:
            p_col = (24, 138, 62)
        elif num in RED_NUMBERS:
            p_col = (178, 32, 32)
        else:
            p_col = (26, 26, 30)

        pygame.draw.polygon(screen, p_col, [p_out0, p_out1, p_in1, p_in0])

        # Highlight winning pocket after spin completes
        if not is_spinning and win_num == num:
            pygame.draw.polygon(screen, BRASS_GOLD, [p_out0, p_out1, p_in1, p_in0], width=3)
        else:
            pygame.draw.line(screen, (175, 145, 75), p_out0, p_in0, 1)

        # Pocket Number Label
        tx, ty = proj_wheel_3d(98, amid, z=-5)
        n_surf = num_font.render(str(num), True, CARD_IVORY)
        screen.blit(n_surf, (tx - n_surf.get_width() // 2, ty - n_surf.get_height() // 2))

    # Inner Pocket Brass Ring
    in_rx, in_ry = 64, int(64 * WHEEL_TILT)
    pygame.draw.ellipse(screen, BRASS_GOLD, (WHEEL_CX - in_rx, WHEEL_CY - in_ry + 10, in_rx * 2, in_ry * 2), width=2)

    # 4. Central 3D Conical Dish & Raised Brass Turret Spindle
    pygame.draw.ellipse(screen, (58, 32, 20), (WHEEL_CX - in_rx + 2, WHEEL_CY - in_ry + 11, (in_rx - 2) * 2, (in_ry - 2) * 2))

    # Conical Turret Column rising to z = +26
    base_x, base_y = proj_wheel_3d(0, 0, z=-8)
    top_x, top_y = proj_wheel_3d(0, 0, z=24)
    pygame.draw.polygon(screen, (165, 128, 55), [(base_x - 20, base_y), (base_x + 20, base_y), (top_x + 8, top_y), (top_x - 8, top_y)])
    pygame.draw.ellipse(screen, BRASS_GOLD, (base_x - 22, base_y - 8, 44, 16))

    # 4 Rotating Turret Crossbars (Spokes)
    for s_i in range(4):
        sa = w_angle + s_i * (math.pi / 2.0)
        sx, sy = proj_wheel_3d(34, sa, z=16)
        pygame.draw.line(screen, BRASS_GOLD, (top_x, top_y + 4), (sx, sy), 3)
        pygame.draw.circle(screen, CARD_IVORY, (sx, sy), 4)

    # Finial Dome Cap
    pygame.draw.circle(screen, BRASS_GOLD, (top_x, top_y), 10)
    pygame.draw.circle(screen, (245, 225, 155), (top_x - 3, top_y - 3), 4)

    # 5. Draw the Ivory Roulette Ball (with drop shadow on the wheel)
    ball_state = player.get("rl_ball_state")
    if not ball_state and win_num is not None:
        w_idx = WHEEL_ORDER.index(win_num)
        ball_state = (90.0, w_angle + (w_idx + 0.5) * slice_ang, -5.0)

    if ball_state:
        br, bang, bz = ball_state
        sh_x, sh_y = proj_wheel_3d(br, bang, z=-6.0)
        bx, by = proj_wheel_3d(br, bang, z=bz)
        pygame.draw.circle(screen, (12, 18, 14), (sh_x + 2, sh_y + 3), 6)
        pygame.draw.circle(screen, (250, 248, 240), (bx, by), 6)
        pygame.draw.circle(screen, (255, 255, 255), (bx - 2, by - 2), 2)


def draw_roulette_table(screen, player, font, font_bold, title_font):
    """Renders the full-screen 800x600 European Roulette table."""
    step_roulette_physics(player)

    # 1. Outer Mahogany Frame & Green Baize
    screen.fill(RAIL_WOOD)
    baize_rect = pygame.Rect(16, 16, 768, 568)
    pygame.draw.rect(screen, BAIZE_GREEN, baize_rect, border_radius=22)
    pygame.draw.rect(screen, BRASS_GOLD, baize_rect, width=3, border_radius=22)

    # 2. Top Brass Header Bar
    header_rect = pygame.Rect(30, 26, 740, 38)
    pygame.draw.rect(screen, BAIZE_DARK, header_rect, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, header_rect, width=1, border_radius=8)

    t_surf = title_font.render("THE HOUSE OF GAMES — ROULETTE", True, BRASS_GOLD)
    screen.blit(t_surf, (45, 33))

    total_bet = sum(b["amount"] for b in player.get("rl_bets", []))
    wallet_str = f"Bet: {total_bet}  |  Chips: {player.get('casino_chips', 0)}  |  Purse: {player.get('silver', 0)}s"
    w_surf = font_bold.render(wallet_str, True, CARD_IVORY)
    screen.blit(w_surf, (755 - w_surf.get_width(), 36))

    # 3. Croupier Banner Box
    opp_box = pygame.Rect(30, 72, 740, 48)
    pygame.draw.rect(screen, (18, 48, 30), opp_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, opp_box, width=1, border_radius=8)
    lbl_surf = font_bold.render("CROUPIER FORTUNESMILE:", True, BRASS_GOLD)
    screen.blit(lbl_surf, (44, 77))
    msg_surf = font.render(player.get("rl_banner", ""), True, CARD_IVORY)
    screen.blit(msg_surf, (44, 97))

    # 4. Left Half: 3D Perspective Roulette Wheel & Recent Numbers History
    draw_roulette_wheel_3d(screen, player, font, font_bold)

    # Recent Winning Numbers Bead Bar below Wheel
    hist_box = pygame.Rect(34, 425, 315, 68)
    pygame.draw.rect(screen, BAIZE_DARK, hist_box, border_radius=8)
    pygame.draw.rect(screen, BAIZE_LINE, hist_box, width=1, border_radius=8)
    h_lbl = font_bold.render("Recent Numbers:", True, BRASS_GOLD)
    screen.blit(h_lbl, (44, 432))

    history = player.get("rl_history", [])
    if not history:
        none_s = font.render("No spins recorded yet.", True, (150, 175, 160))
        screen.blit(none_s, (44, 458))
    else:
        for idx, h_num in enumerate(reversed(history[-9:])):
            hx = 54 + idx * 32
            hy = 468
            h_col = (24, 138, 62) if h_num == 0 else ((180, 34, 34) if h_num in RED_NUMBERS else (28, 28, 34))
            pygame.draw.circle(screen, h_col, (hx, hy), 13)
            pygame.draw.circle(screen, BRASS_GOLD if idx == 0 else CARD_IVORY, (hx, hy), 13, width=2 if idx == 0 else 1)
            ns = font_bold.render(str(h_num), True, CARD_IVORY)
            screen.blit(ns, (hx - ns.get_width() // 2, hy - ns.get_height() // 2))

    # 5. Right Half: Full Interactive Betting Layout (0..36, Columns, Dozens, Even-Money)
    hover_bet = player.get("rl_hover_bet")
    hovered_nums = set(hover_bet["nums"]) if hover_bet else set()
    win_num = player.get("rl_win_num")
    show_win = (player.get("rl_phase") == "BETTING" and win_num is not None)

    # Zero (0) Cell
    z_col = (38, 165, 80) if 0 in hovered_nums else (22, 120, 52)
    pygame.draw.rect(screen, z_col, RL_ZERO_RECT, border_radius=5)
    pygame.draw.rect(screen, BRASS_GOLD if (show_win and win_num == 0) else CARD_IVORY, RL_ZERO_RECT, width=2, border_radius=5)
    z_txt = font_bold.render("0", True, CARD_IVORY)
    screen.blit(z_txt, z_txt.get_rect(center=RL_ZERO_RECT.center))

    # Numbers 1..36 Grid
    for col in range(12):
        for row in range(3):
            n = get_grid_num(col, row)
            cx = RL_GRID_X + col * RL_CELL_W
            cy = RL_GRID_Y + row * RL_CELL_H
            c_rect = pygame.Rect(cx, cy, RL_CELL_W, RL_CELL_H)

            if n in RED_NUMBERS:
                base_c = (215, 65, 55) if n in hovered_nums else (165, 32, 32)
            else:
                base_c = (65, 70, 82) if n in hovered_nums else (28, 30, 36)

            pygame.draw.rect(screen, base_c, c_rect)
            border_c = BRASS_GOLD if (n in hovered_nums or (show_win and win_num == n)) else CARD_IVORY
            border_w = 2 if (n in hovered_nums or (show_win and win_num == n)) else 1
            pygame.draw.rect(screen, border_c, c_rect, width=border_w)

            nt = font_bold.render(str(n), True, CARD_IVORY)
            screen.blit(nt, nt.get_rect(center=c_rect.center))

    # Right "2 to 1" Column Cells
    gx_end = RL_GRID_X + 12 * RL_CELL_W
    gy_end = RL_GRID_Y + 3 * RL_CELL_H
    for row in range(3):
        col_rect = pygame.Rect(gx_end, RL_GRID_Y + row * RL_CELL_H, 42, RL_CELL_H)
        pygame.draw.rect(screen, BAIZE_DARK, col_rect)
        pygame.draw.rect(screen, CARD_IVORY, col_rect, width=1)
        ct = font.render("2:1", True, BRASS_GOLD)
        screen.blit(ct, ct.get_rect(center=col_rect.center))

    # Dozen Boxes (1st 12, 2nd 12, 3rd 12)
    doz_y = gy_end + 8
    doz_labels = ["1st 12", "2nd 12", "3rd 12"]
    for d_i in range(3):
        d_rect = pygame.Rect(RL_GRID_X + d_i * 4 * RL_CELL_W, doz_y, 4 * RL_CELL_W, 38)
        pygame.draw.rect(screen, BAIZE_DARK, d_rect)
        pygame.draw.rect(screen, CARD_IVORY, d_rect, width=1)
        dt = font_bold.render(doz_labels[d_i], True, CARD_IVORY)
        screen.blit(dt, dt.get_rect(center=d_rect.center))

    # Even-Money Boxes (1-18, EVEN, RED, BLACK, ODD, 19-36)
    # Define a smaller font for the even-money boxes (e.g., size 18)
    even_font = pygame.font.Font(None, 20)
    
    even_y = doz_y + 42
    even_labels = ["1-18", "EVEN", "RED", "BLACK", "ODD", "19-36"]
    for e_i in range(6):
        e_rect = pygame.Rect(RL_GRID_X + e_i * 2 * RL_CELL_W, even_y, 2 * RL_CELL_W, 40)
        bg = (155, 30, 30) if e_i == 2 else ((26, 28, 34) if e_i == 3 else BAIZE_DARK)
        pygame.draw.rect(screen, bg, e_rect)
        pygame.draw.rect(screen, CARD_IVORY, e_rect, width=1)
        et = even_font.render(even_labels[e_i], True, CARD_IVORY)
        screen.blit(et, et.get_rect(center=e_rect.center))

    # 6. Draw Placed Chip Tokens on the Baize
    chip_font = pygame.font.Font(None, 16)
    for b in player.get("rl_bets", []):
        bx, by = b["pos"]
        pygame.draw.circle(screen, (10, 30, 18), (bx + 2, by + 2), 11)
        pygame.draw.circle(screen, (178, 34, 34), (bx, by), 11)
        pygame.draw.circle(screen, CARD_IVORY, (bx, by), 11, width=2)
        pygame.draw.circle(screen, BRASS_GOLD, (bx, by), 8, width=1)
        amt_s = chip_font.render(str(b["amount"]), True, CARD_IVORY)
        screen.blit(amt_s, amt_s.get_rect(center=(bx, by)))

    # Hover Preview Indicator & Info Strip under Betting Grid
    info_box = pygame.Rect(368, 452, 388, 41)
    pygame.draw.rect(screen, BAIZE_DARK, info_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, info_box, width=1, border_radius=8)
    if hover_bet:
        px, py = hover_bet["pos"]
        pygame.draw.circle(screen, BRASS_GOLD, (px, py), 9, width=2)
        h_str = f"Click to Bet ({player.get('rl_chip_val', 1)}): {hover_bet['label']}"
    else:
        h_str = f"Active Chip: {player.get('rl_chip_val', 1)}  |  Hover over options to bet"
    h_surf = font.render(h_str, True, BRASS_GOLD if hover_bet else CARD_IVORY)
    screen.blit(h_surf, (380, 464))

    # 7. Bottom Mahogany Action Tray
    tray_rect = pygame.Rect(30, 512, 740, 58)
    pygame.draw.rect(screen, BAIZE_DARK, tray_rect, border_radius=10)
    pygame.draw.rect(screen, BRASS_GOLD, tray_rect, width=1, border_radius=10)

# =========================================================================
# 6. FULL-SCREEN CRAPS — 3D SUNKEN TUB, BOUNCING DICE & FULL BETTING BAIZE
# =========================================================================

# Normalized (u0, v0, u1, v1) coordinates on the Craps Felt (0.0..1.0 across width and depth)
CRAPS_ZONES = [
    # --- Top Row: Place Bets (4, 5, SIX, 8, NINE, 10) ---
    {"id": "place_4",   "uv": (0.03, 0.04, 0.13, 0.25), "title": "4",    "sub": "9:5",  "label": "Place 4 (Pays 9:5)"},
    {"id": "place_5",   "uv": (0.135,0.04, 0.235,0.25), "title": "5",    "sub": "7:5",  "label": "Place 5 (Pays 7:5)"},
    {"id": "place_6",   "uv": (0.24, 0.04, 0.34, 0.25), "title": "SIX",  "sub": "7:6",  "label": "Place 6 (Pays 7:6)"},
    {"id": "place_8",   "uv": (0.345,0.04, 0.445,0.25), "title": "8",    "sub": "7:6",  "label": "Place 8 (Pays 7:6)"},
    {"id": "place_9",   "uv": (0.45, 0.04, 0.55, 0.25), "title": "NINE", "sub": "7:5",  "label": "Place 9 (Pays 7:5)"},
    {"id": "place_10",  "uv": (0.555,0.04, 0.655,0.25), "title": "10",   "sub": "9:5",  "label": "Place 10 (Pays 9:5)"},

    # --- Middle Left: THE FIELD (One-Roll Bet) ---
    {"id": "field",     "uv": (0.03, 0.28, 0.655,0.48), "title": "FIELD:  (2)•2x   3   4   9   10   11   (12)•2x", "sub": "ONE-ROLL BET", "label": "The Field (3,4,9,10,11 pay 1:1 | 2 & 12 pay 2:1)"},

    # --- Lower Left: Don't Pass Bar, Pass Line & Free Odds ---
    {"id": "dont_pass", "uv": (0.03, 0.51, 0.655,0.68), "title": "DON'T PASS BAR (12)", "sub": "1:1",  "label": "Don't Pass Bar (Wins on 2,3 | Pushes 12 | Loses 7,11)"},
    {"id": "pass_line", "uv": (0.03, 0.71, 0.485,0.92), "title": "PASS LINE",           "sub": "1:1",  "label": "Pass Line (Wins on 7,11 Come-Out | Hit Point to Win 1:1)"},
    {"id": "pass_odds", "uv": (0.495,0.71, 0.655,0.92), "title": "FREE ODDS",          "sub": "TRUE", "label": "Pass Line Free Odds (4/10 pay 2:1 | 5/9 pay 3:2 | 6/8 pay 6:5)"},

    # --- Right Column: Center Proposition & Hardways Box ---
    {"id": "any_7",      "uv": (0.68, 0.04, 0.97, 0.17), "title": "ANY SEVEN (4 TO 1)", "sub": "",     "label": "Any Seven — One Roll (Pays 4:1)"},
    {"id": "hard_4",     "uv": (0.68, 0.19, 0.822,0.34), "title": "HARD 4 (2-2)",       "sub": "7:1",  "label": "Hard 4 (2+2 before 7 or Easy 4 — Pays 7:1)"},
    {"id": "hard_10",    "uv": (0.828,0.19, 0.97, 0.34), "title": "HARD 10 (5-5)",      "sub": "7:1",  "label": "Hard 10 (5+5 before 7 or Easy 10 — Pays 7:1)"},
    {"id": "hard_6",     "uv": (0.68, 0.36, 0.822,0.51), "title": "HARD 6 (3-3)",       "sub": "9:1",  "label": "Hard 6 (3+3 before 7 or Easy 6 — Pays 9:1)"},
    {"id": "hard_8",     "uv": (0.828,0.36, 0.97, 0.51), "title": "HARD 8 (4-4)",       "sub": "9:1",  "label": "Hard 8 (4+4 before 7 or Easy 8 — Pays 9:1)"},
    {"id": "snake_2",    "uv": (0.68, 0.53, 0.822,0.68), "title": "SNAKE EYES (2)",     "sub": "30:1", "label": "Snake Eyes 1+1 — One Roll (Pays 30:1)"},
    {"id": "boxcars_12", "uv": (0.828,0.53, 0.97, 0.68), "title": "BOXCARS (12)",       "sub": "30:1", "label": "Boxcars 6+6 — One Roll (Pays 30:1)"},
    {"id": "ace_3",      "uv": (0.68, 0.71, 0.772,0.92), "title": "ACE-2",              "sub": "15:1", "label": "Ace-Deuce (3) — One Roll (Pays 15:1)"},
    {"id": "yo_11",      "uv": (0.778,0.71, 0.872,0.92), "title": "YO-11",              "sub": "15:1", "label": "Yo-Eleven (11) — One Roll (Pays 15:1)"},
    {"id": "any_craps",  "uv": (0.878,0.71, 0.97, 0.92), "title": "CRAPS",              "sub": "7:1",  "label": "Any Craps (2, 3, or 12) — One Roll (Pays 7:1)"},
]

# 3D Sunken Felt Trapezoid Geometry:
# Top edge (far wall): y = 176, x = 92 .. 708 (width = 616)
# Bottom edge (near rail): y = 446, x = 36 .. 764 (width = 728)
CRAPS_TOP_Y = 176.0
CRAPS_BOT_Y = 446.0


def project_craps_uv(u, v):
    """Projects normalized felt coordinates (u, v in 0..1) into 3D perspective screen coordinates (x, y)."""
    # Non-linear perspective foreshortening along depth v
    v_persp = (v ** 1.12)
    y = CRAPS_TOP_Y + v_persp * (CRAPS_BOT_Y - CRAPS_TOP_Y)
    left_x = 92.0 - v_persp * 56.0
    right_x = 708.0 + v_persp * 56.0
    x = left_x + u * (right_x - left_x)
    return int(x), int(y)


def unproject_craps_screen(mx, my):
    """Inverse perspective mapping from screen (mx, my) back to normalized felt coordinates (u, v)."""
    if my < CRAPS_TOP_Y or my > CRAPS_BOT_Y:
        return -1.0, -1.0
    v_persp = (my - CRAPS_TOP_Y) / (CRAPS_BOT_Y - CRAPS_TOP_Y)
    v = v_persp ** (1.0 / 1.12)
    left_x = 92.0 - v_persp * 56.0
    right_x = 708.0 + v_persp * 56.0
    u = (mx - left_x) / max(1.0, (right_x - left_x))
    return u, v


def get_craps_zone_quad(zone):
    """Returns the 4 perspective-projected polygon vertices [TL, TR, BR, BL] and center for a betting zone."""
    u0, v0, u1, v1 = zone["uv"]
    tl = project_craps_uv(u0, v0)
    tr = project_craps_uv(u1, v0)
    br = project_craps_uv(u1, v1)
    bl = project_craps_uv(u0, v1)
    cx, cy = project_craps_uv((u0 + u1) * 0.5, (v0 + v1) * 0.5)
    return [tl, tr, br, bl], (cx, cy)


def detect_craps_zone_at_pos(mx, my):
    u, v = unproject_craps_screen(mx, my)
    if not (0.0 <= u <= 1.0 and 0.0 <= v <= 1.0):
        return None
    for z in CRAPS_ZONES:
        u0, v0, u1, v1 = z["uv"]
        if u0 <= u <= u1 and v0 <= v <= v1:
            return z
    return None


def draw_craps_table(screen, player, font, font_bold, title_font):
    """Renders the full-screen 3D Perspective Craps Tub, Pyramid Backboard, Perspective Baize & Dice."""
    step_craps_physics(player)

    # 1. Outer Mahogany Tub Rail
    screen.fill(RAIL_WOOD)
    outer_rect = pygame.Rect(14, 14, 772, 572)
    pygame.draw.rect(screen, (36, 18, 12), outer_rect, border_radius=22)
    pygame.draw.rect(screen, BRASS_GOLD, outer_rect, width=3, border_radius=22)

    # 2. Top Brass Header Bar
    header_rect = pygame.Rect(30, 24, 740, 36)
    pygame.draw.rect(screen, (12, 42, 25), header_rect, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, header_rect, width=1, border_radius=8)

    t_surf = title_font.render("THE HOUSE OF GAMES — CRAPS (THE BONES)", True, BRASS_GOLD)
    screen.blit(t_surf, (45, 30))

    total_bet = sum(player.get("cr_bets", {}).values())
    wallet_str = f"On Baize: {total_bet}  |  Chips: {player.get('casino_chips', 0)}  |  Purse: {player.get('silver', 0)}s"
    w_surf = font_bold.render(wallet_str, True, CARD_IVORY)
    screen.blit(w_surf, (755 - w_surf.get_width(), 33))

    # 3. Stickman Call Banner
    opp_box = pygame.Rect(30, 66, 740, 44)
    pygame.draw.rect(screen, (18, 48, 30), opp_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, opp_box, width=1, border_radius=8)
    point = player.get("cr_point")
    puck_status = f"POINT IS ON ({point})" if point else "PUCK IS OFF (COME-OUT ROLL)"
    lbl_surf = font_bold.render(f"STICKMAN CALL  —  {puck_status}", True, BRASS_GOLD)
    screen.blit(lbl_surf, (44, 71))
    msg_surf = font.render(player.get("cr_banner", ""), True, CARD_IVORY)
    screen.blit(msg_surf, (44, 90))

    # 4. 3D Sunken Craps Tub (Perspective Rear Wall, Angled Side Walls & Padded Leather Rim)
    # Outer top rim of the sunken pit:
    rim_tl, rim_tr = (68, 118), (732, 118)
    rim_bl, rim_br = (18, 452), (782, 452)
    # Inner bottom floor corners (where walls meet the green baize):
    fl_tl, fl_tr = project_craps_uv(0.0, 0.0), project_craps_uv(1.0, 0.0)
    fl_bl, fl_br = project_craps_uv(0.0, 1.0), project_craps_uv(1.0, 1.0)

    # Draw 3D Sunken Cushion Walls (Top/Back Wall, Left Wall, Right Bounce Wall)
    pygame.draw.polygon(screen, (14, 58, 36), [rim_tl, rim_tr, fl_tr, fl_tl])  # Back Wall
    pygame.draw.polygon(screen, (19, 72, 45), [rim_tl, fl_tl, fl_bl, rim_bl])  # Left Wall (lit)
    pygame.draw.polygon(screen, (10, 44, 27), [rim_tr, rim_br, fl_br, fl_tr])  # Right Wall (shaded)

    # 3D Rubber Pyramid Deflector Cushion ("Alligator Teeth") along Back Wall
    num_back_teeth = 22
    for i in range(num_back_teeth):
        u_a = i / float(num_back_teeth)
        u_m = (i + 0.5) / float(num_back_teeth)
        u_b = (i + 1.0) / float(num_back_teeth)
        tx0 = int(rim_tl[0] + u_a * (rim_tr[0] - rim_tl[0]))
        txm = int(rim_tl[0] + u_m * (rim_tr[0] - rim_tl[0]))
        tx1 = int(rim_tl[0] + u_b * (rim_tr[0] - rim_tl[0]))
        bx0 = int(fl_tl[0] + u_a * (fl_tr[0] - fl_tl[0]))
        bxm = int(fl_tl[0] + u_m * (fl_tr[0] - fl_tl[0]))
        bx1 = int(fl_tl[0] + u_b * (fl_tr[0] - fl_tl[0]))
        mid_y = (rim_tl[1] + fl_tl[1]) // 2
        diamond = [(txm, rim_tl[1] + 8), (tx1, mid_y), (bxm, fl_tl[1] - 5), (bx0, mid_y)]
        pygame.draw.polygon(screen, (9, 38, 23), diamond)
        pygame.draw.polygon(screen, (32, 96, 60), diamond, width=1)

    # 3D Rubber Pyramid Diamonds along Right Bounce Wall
    num_side_teeth = 9
    for i in range(num_side_teeth):
        t0 = i / float(num_side_teeth)
        tm = (i + 0.5) / float(num_side_teeth)
        t1 = (i + 1.0) / float(num_side_teeth)
        rx_m = int(rim_tr[0] + tm * (rim_br[0] - rim_tr[0])) - 5
        ry_m = int(rim_tr[1] + tm * (rim_br[1] - rim_tr[1]))
        fx_0 = int(fl_tr[0] + t0 * (fl_br[0] - fl_tr[0])) + 3
        fy_0 = int(fl_tr[1] + t0 * (fl_br[1] - fl_tr[1]))
        fx_1 = int(fl_tr[0] + t1 * (fl_br[0] - fl_tr[0])) + 3
        fy_1 = int(fl_tr[1] + t1 * (fl_br[1] - fl_tr[1]))
        fx_m = (fx_0 + fx_1) // 2
        fy_m = (fy_0 + fy_1) // 2
        s_diamond = [(fx_0, fy_0), (rx_m, ry_m), (fx_1, fy_1), (fx_m, fy_m)]
        pygame.draw.polygon(screen, (8, 34, 20), s_diamond)
        pygame.draw.polygon(screen, (30, 88, 54), s_diamond, width=1)

    # Sunken Perspective Baize Floor
    felt_poly = [fl_tl, fl_tr, fl_br, fl_bl]
    pygame.draw.polygon(screen, BAIZE_GREEN, felt_poly)
    pygame.draw.polygon(screen, BRASS_GOLD, felt_poly, width=2)
    # Outer Mahogany Lip
    pygame.draw.polygon(screen, BRASS_GOLD, [rim_tl, rim_tr, rim_br, rim_bl], width=2)

    # 5. Draw All 20 Betting Zones as True 3D Perspective Quads!
    hover_zone = player.get("cr_hover_zone")
    hover_id = hover_zone["id"] if hover_zone else None
    small_f = pygame.font.Font(None, 16)
    med_f = pygame.font.Font(None, 19)

    for z in CRAPS_ZONES:
        zid = z["id"]
        quad, (cx, cy) = get_craps_zone_quad(z)
        is_hov = (zid == hover_id)

        if zid.startswith("place_"):
            bg = (36, 118, 72) if is_hov else (18, 72, 44)
        elif zid == "field":
            bg = (42, 118, 68) if is_hov else (20, 68, 40)
        elif zid in ("any_7", "hard_4", "hard_10", "hard_6", "hard_8", "snake_2", "boxcars_12", "ace_3", "yo_11", "any_craps"):
            bg = (102, 40, 34) if is_hov else (48, 24, 22)
        else:
            bg = (38, 112, 68) if is_hov else BAIZE_DARK

        pygame.draw.polygon(screen, bg, quad)
        border_c = BRASS_GOLD if is_hov else (215, 210, 192)
        pygame.draw.polygon(screen, border_c, quad, width=2 if is_hov else 1)

        t_col = BRASS_GOLD if ("FIELD" in z["title"] or "SEVEN" in z["title"] or zid.startswith("place_")) else CARD_IVORY
        ts = med_f.render(z["title"], True, t_col)
        if z["sub"]:
            screen.blit(ts, ts.get_rect(center=(cx, cy - 6)))
            ss = small_f.render(z["sub"], True, (210, 195, 155))
            screen.blit(ss, ss.get_rect(center=(cx, cy + 9)))
        else:
            screen.blit(ts, ts.get_rect(center=(cx, cy)))

    # 6. Draw the 3D Elliptical ON / OFF Point Puck
    if point is None:
        puck_x, puck_y = project_craps_uv(0.015, 0.12)
        pygame.draw.ellipse(screen, (8, 20, 12), (puck_x - 15, puck_y - 9, 30, 22))
        pygame.draw.ellipse(screen, SUIT_BLACK, (puck_x - 15, puck_y - 12, 30, 22))
        pygame.draw.ellipse(screen, BRASS_GOLD, (puck_x - 15, puck_y - 12, 30, 22), width=2)
        pt = small_f.render("OFF", True, CARD_IVORY)
        screen.blit(pt, pt.get_rect(center=(puck_x, puck_y - 1)))
    else:
        p_zone = next(z for z in CRAPS_ZONES if z["id"] == f"place_{point}")
        u0, v0, u1, v1 = p_zone["uv"]
        puck_x, puck_y = project_craps_uv(u1 - 0.02, v0 + 0.05)
        pygame.draw.ellipse(screen, (8, 20, 12), (puck_x - 13, puck_y - 7, 26, 18))
        pygame.draw.ellipse(screen, CARD_IVORY, (puck_x - 13, puck_y - 10, 26, 18))
        pygame.draw.ellipse(screen, SUIT_BLACK, (puck_x - 13, puck_y - 10, 26, 18), width=2)
        pt = small_f.render("ON", True, SUIT_BLACK)
        screen.blit(pt, pt.get_rect(center=(puck_x, puck_y - 1)))

    # 7. Draw 3D Perspective Chip Stacks on the Felt
    for z in CRAPS_ZONES:
        amt = player.get("cr_bets", {}).get(z["id"], 0)
        if amt > 0:
            u0, v0, u1, v1 = z["uv"]
            bx, by = project_craps_uv(u0 + 0.025, v1 - 0.04)
            num_discs = min(4, max(1, amt // 5 + 1))
            for d_i in range(num_discs):
                cy_d = by - d_i * 3
                pygame.draw.ellipse(screen, (10, 30, 18), (bx - 11, cy_d - 6, 22, 15))
                pygame.draw.ellipse(screen, (185, 36, 36), (bx - 12, cy_d - 8, 22, 15))
                pygame.draw.ellipse(screen, CARD_IVORY, (bx - 12, cy_d - 8, 22, 15), width=2)
            top_y = by - (num_discs - 1) * 3 - 1
            at = small_f.render(str(amt), True, CARD_IVORY)
            screen.blit(at, at.get_rect(center=(bx - 1, top_y)))

    # 8. Draw the Two 3D Ivory Dice (Animated during roll, or resting in the lower shooter alley)
    if player.get("cr_phase") == "ROLLING" and player.get("cr_anim_dice"):
        for (dx, dy, dz, fval, ang) in player["cr_anim_dice"]:
            draw_3d_die(screen, dx, dy, dz, fval, ang)
    else:
        d1, d2 = player.get("cr_dice", (3, 4))
        dx1, dy1 = project_craps_uv(0.54, 0.59)
        dx2, dy2 = project_craps_uv(0.61, 0.62)
        draw_3d_die(screen, dx1, dy1, 0.0, d1, 0.15)
        draw_3d_die(screen, dx2, dy2, 0.0, d2, -0.22)

    # 9. Bottom Info Strip & Recent Rolls Bead Bar
    info_box = pygame.Rect(30, 458, 740, 44)
    pygame.draw.rect(screen, BAIZE_DARK, info_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, info_box, width=1, border_radius=8)

    if hover_zone:
        h_str = f"Left-Click (+{player.get('cr_chip_val', 1)}) / Right-Click (Remove):  {hover_zone['label']}"
        h_col = BRASS_GOLD
    else:
        h_str = f"Active Chip: {player.get('cr_chip_val', 1)}  |  Hover any 3D box on the baize to see rules & payout odds"
        h_col = CARD_IVORY
    screen.blit(font.render(h_str, True, h_col), (44, 464))

    d1, d2 = player.get("cr_dice", (3, 4))
    hist = player.get("cr_history", [])
    hist_str = f"Last Roll: {d1}+{d2}={d1+d2}   |   Recent:  " + ("   ".join(f"[{a}+{b}={a+b}]" for a, b in reversed(hist[-5:])) if hist else "None yet")
    screen.blit(small_f.render(hist_str, True, (185, 205, 190)), (44, 484))

    # 10. Bottom Mahogany Action Tray
    tray_rect = pygame.Rect(30, 512, 740, 58)
    pygame.draw.rect(screen, BAIZE_DARK, tray_rect, border_radius=10)
    pygame.draw.rect(screen, BRASS_GOLD, tray_rect, width=1, border_radius=10)

def init_craps(player):
    player["cr_phase"] = "BETTING"      # "BETTING", "ROLLING"
    player["cr_point"] = None           # None = Come-Out Roll, or 4, 5, 6, 8, 9, 10
    player["cr_chip_val"] = 1
    player["cr_bets"] = {}              # Dict mapping zone_id -> chip amount
    player["cr_last_bets"] = {}
    player["cr_dice"] = (3, 4)
    player["cr_history"] = player.get("cr_history", [])
    player["cr_hover_zone"] = None
    player["cr_banner"] = (
        "Stickman Fortunesmile slides two ivory bones across the felt. "
        "\"Puck is OFF — Come-Out roll! Place your Pass Line, Field, or Proposition bets!\""
    )
    return player, "You step up to the sunken mahogany rail of the Craps pit.", "CASINO_CRAPS"

def handle_craps_event(event, player):
    """Handles mouse hover highlights and chip placement/removal on the Craps baize."""
    if player.get("cr_phase") is None:
        player["cr_phase"] = "BETTING"
    if player.get("cr_phase") != "BETTING":
        player["cr_hover_zone"] = None
        return

    if event.type == pygame.MOUSEMOTION:
        player["cr_hover_zone"] = detect_craps_zone_at_pos(*event.pos)

    elif event.type == pygame.MOUSEBUTTONDOWN:
        zone = detect_craps_zone_at_pos(*event.pos)
        if not zone:
            return
        zid = zone["id"]
        point = player.get("cr_point")
        bets = player.setdefault("cr_bets", {})

        # Right-click removes a bet (except locked Pass/Don't Pass once a Point is established)
        if event.button == 3:
            if zid in bets and bets[zid] > 0:
                if point is not None and zid in ("pass_line", "dont_pass"):
                    player["cr_banner"] = "\"Contract bets (Pass / Don't Pass) cannot be taken down while a Point is ON!\""
                    return
                refund = bets.pop(zid)
                player["casino_chips"] = player.get("casino_chips", 0) + refund
                player["cr_banner"] = f"Pulled back {refund} Chips from {zone['label'].split(' (')[0]}."
            return

        # Left-click places a chip
        if event.button == 1:
            if zid == "pass_odds" and (point is None or bets.get("pass_line", 0) <= 0):
                player["cr_banner"] = "\"You can only back Free Odds after a Point is established on your Pass Line bet!\""
                return

            chip_val = player.get("cr_chip_val", 1)
            chips = player.get("casino_chips", 0)
            if chips < chip_val:
                player["cr_banner"] = f"\"You Have {chips} Chips! Visit the Cashier Cage first to buy chips before betting!\""
                return

            player["casino_chips"] -= chip_val
            bets[zid] = bets.get(zid, 0) + chip_val
            player["cr_banner"] = f"Placed {chip_val} Chips on {zone['label']} (Spot Total: {bets[zid]})."


def resolve_craps_action(action, player):
    if player.get("cr_phase") == "ROLLING":
        return player, None, "CASINO_CRAPS"

    if action == "toggle_loaded":
        if "weighted ivory dice" not in player.get("inventory", []):
            player["cr_use_loaded"] = False
            player["cr_banner"] = "\"You don't have any weighted dice in your pockets!\""
            return player, None, "CASINO_CRAPS"
        player["cr_use_loaded"] = not player.get("cr_use_loaded", False)
        state_str = "PALMED (ACTIVE)" if player["cr_use_loaded"] else "HIDDEN (OFF)"
        player["cr_banner"] = f"You discreetly shift the Weighted Ivory Dice in your palm: [{state_str}]."
        return player, None, "CASINO_CRAPS"

    if action.startswith("chip_"):
        val = int(action.split("_")[1])
        player["cr_chip_val"] = val
        player["cr_banner"] = f"Selected {val}-Chip denomination. Left-click any box to bet (Right-click to pull down a bet)."
        return player, None, "CASINO_CRAPS"

    if action == "clear":
        point = player.get("cr_point")
        bets = player.get("cr_bets", {})
        refund = 0
        kept = {}
        for zid, amt in bets.items():
            # Keep contract bets on the line if a Point is currently ON
            if point is not None and zid in ("pass_line", "dont_pass"):
                kept[zid] = amt
            else:
                refund += amt
        player["casino_chips"] = player.get("casino_chips", 0) + refund
        player["cr_bets"] = kept
        player["cr_banner"] = f"Returned {refund} Chips to your stack." + (" (Pass/Don't Pass remain locked until Point resolves.)" if kept else "")
        return player, None, "CASINO_CRAPS"

    if action == "clear_all_leave":
        # Refunds every chip on the felt when walking away from the table
        bets = player.get("cr_bets", {})
        refund = sum(bets.values())
        player["casino_chips"] = player.get("casino_chips", 0) + refund
        player["cr_bets"] = {}
        return player, None, "MAIN"

    if action == "rebet":
        last_bets = player.get("cr_last_bets", {})
        if not last_bets:
            player["cr_banner"] = "\"No previous bet layout to repeat yet!\""
            return player, None, "CASINO_CRAPS"
        point = player.get("cr_point")
        # Filter out Free Odds if Puck is currently OFF
        target_bets = {k: v for k, v in last_bets.items() if not (k == "pass_odds" and point is None)}
        current_total = sum(player.get("cr_bets", {}).values())
        needed = sum(target_bets.values())
        avail = player.get("casino_chips", 0) + current_total
        if avail < needed:
            player["cr_banner"] = f"\"You need {needed} Chips to repeat your previous Craps layout!\""
            return player, None, "CASINO_CRAPS"
        player["casino_chips"] = avail - needed
        player["cr_bets"] = dict(target_bets)
        player["cr_banner"] = f"Repeated previous layout ({needed} Chips across the baize). Ready to shoot!"
        return player, None, "CASINO_CRAPS"

    if action == "roll":
        bets = player.get("cr_bets", {})
        if not bets:
            player["cr_banner"] = "\"Place at least one bet on the baize before throwing the bones!\""
            return player, None, "CASINO_CRAPS"

        player["cr_last_bets"] = dict(bets)
        player["cr_phase"] = "ROLLING"
        player["cr_hover_zone"] = None
        player["cr_roll_start_tick"] = pygame.time.get_ticks()
        player["cr_roll_duration"] = 1850  # 1.85s 3D throw + pyramid wall bounce + settle
        use_loaded = player.get("cr_use_loaded", False) and ("weighted ivory dice" in player.get("inventory", []))
        player["cr_caught_cheating"] = False

        if use_loaded:
            # Stealth check: 28% base chance to be caught, -6% per Stealth point (min 5%)
            catch_prob = max(0.05, 0.28 - player.get("stealth", 0) * 0.06)
            if random.random() < catch_prob:
                player["cr_caught_cheating"] = True
                d1, d2 = random.randint(1, 6), random.randint(1, 6)
            else:
                # 65% chance to roll a favourable outcome!
                point = player.get("cr_point")
                if random.random() < 0.65:
                    if point is None:
                        d1, d2 = random.choice([(3, 4), (4, 3), (5, 2), (2, 5), (5, 6), (6, 5)])
                    elif point in (4, 6, 8, 10) and random.random() < 0.60:
                        half = point // 2
                        d1, d2 = half, half  # Hits both the Point AND the Hardway!
                    else:
                        pairs = [(a, b) for a in range(1, 7) for b in range(1, 7) if a + b == point]
                        d1, d2 = random.choice(pairs)
                else:
                    d1, d2 = random.randint(1, 6), random.randint(1, 6)
        else:
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
        
        player["cr_target_dice"] = (d1, d2)
        player["cr_traj_seed"] = random.uniform(-1.0, 1.0)
        player["cr_banner"] = "Shooter shakes the ivory bones and hurls them down the tub toward the pyramid wall..."
        return player, None, "CASINO_CRAPS"

    return player, None, "CASINO_CRAPS"


def evaluate_craps_roll(player, d1, d2):
    """Evaluates all 20 Craps betting zones according to authentic casino rules."""
    total = d1 + d2
    is_hard = (d1 == d2)
    point = player.get("cr_point")
    bets = player.get("cr_bets", {})
    new_bets = dict(bets)

    winnings = 0
    net_profit = 0
    notes = []

    def win_bet(zid, profit, keep_on_felt=False):
        nonlocal winnings, net_profit
        stake = new_bets.get(zid, 0)
        if stake <= 0:
            return
        net_profit += profit
        if keep_on_felt:
            winnings += profit  # Original stake stays on the baize; profit goes straight to stack!
        else:
            winnings += stake + profit
            new_bets.pop(zid, None)

    def lose_bet(zid):
        new_bets.pop(zid, None)

    # 1. ONE-ROLL PROPOSITION BETS & THE FIELD (Always resolve on every roll)
    if "field" in new_bets:
        stake = new_bets["field"]
        if total in (2, 12):
            win_bet("field", stake * 2)
            notes.append(f"Field Double ({total}) +{stake*2}")
        elif total in (3, 4, 9, 10, 11):
            win_bet("field", stake)
            notes.append(f"Field +{stake}")
        else:
            lose_bet("field")

    one_roll_specs = [
        ("any_7",      total == 7,            4,  "Any 7"),
        ("any_craps",  total in (2, 3, 12),   7,  "Any Craps"),
        ("snake_2",    total == 2,            30, "Snake Eyes"),
        ("boxcars_12", total == 12,           30, "Boxcars"),
        ("ace_3",      total == 3,            15, "Ace-Deuce"),
        ("yo_11",      total == 11,           15, "Yo-11"),
    ]
    for zid, cond, mult, name in one_roll_specs:
        if zid in new_bets:
            if cond:
                p = new_bets[zid] * mult
                win_bet(zid, p)
                notes.append(f"{name} +{p}")
            else:
                lose_bet(zid)

    # 2. MULTI-ROLL HARDWAYS (4, 6, 8, 10)
    hard_specs = [
        ("hard_4",  4,  7),
        ("hard_10", 10, 7),
        ("hard_6",  6,  9),
        ("hard_8",  8,  9),
    ]
    for zid, target_tot, mult in hard_specs:
        if zid in new_bets:
            if total == target_tot and is_hard:
                p = new_bets[zid] * mult
                win_bet(zid, p, keep_on_felt=True)
                notes.append(f"Hard {target_tot} +{p}")
            elif total == 7 or (total == target_tot and not is_hard):
                lose_bet(zid)

    # 3. PLACE BETS (4, 5, 6, 8, 9, 10) — Working whenever a Point is ON!
    if point is not None:
        place_specs = [
            ("place_4",  4,  9, 5),
            ("place_5",  5,  7, 5),
            ("place_6",  6,  7, 6),
            ("place_8",  8,  7, 6),
            ("place_9",  9,  7, 5),
            ("place_10", 10, 9, 5),
        ]
        for zid, p_num, num_m, den_m in place_specs:
            if zid in new_bets:
                if total == p_num:
                    stake = new_bets[zid]
                    p = max(1, (stake * num_m) // den_m)
                    win_bet(zid, p, keep_on_felt=True)
                    notes.append(f"Place {p_num} +{p}")
                elif total == 7:
                    lose_bet(zid)

    # 4. PASS LINE, DON'T PASS & FREE ODDS (Come-Out vs. Point Phase)
    call_dict = {
        2: "Two Craps — Snake Eyes!",
        3: "Three Craps — Ace-Deuce!",
        12: "Twelve Craps — Boxcars!",
        11: "Yo-Eleven!"
    }
    stick_call = call_dict.get(total, f"{total} {' the Hard Way' if (is_hard and total in (4,6,8,10)) else ''}!")

    if point is None:
        # --- COME-OUT ROLL ---
        if total in (7, 11):
            stick_call = f"{total} — Front Line Winner!"
            if "pass_line" in new_bets:
                p = new_bets["pass_line"]
                win_bet("pass_line", p)
                notes.append(f"Pass Line +{p}")
            if "dont_pass" in new_bets:
                lose_bet("dont_pass")
        elif total in (2, 3, 12):
            if "pass_line" in new_bets:
                lose_bet("pass_line")
            if "dont_pass" in new_bets:
                if total == 12:
                    notes.append("Don't Pass Bar 12 (Push)")
                else:
                    p = new_bets["dont_pass"]
                    win_bet("dont_pass", p)
                    notes.append(f"Don't Pass +{p}")
        else:
            # Point is established (4, 5, 6, 8, 9, or 10)
            player["cr_point"] = total
            stick_call = f"Point is {total}! Puck moves to {total} (ON)."
    else:
        # --- POINT PHASE ROLL ---
        if total == point:
            stick_call = f"{total} — Shooter hits the Point! Puck turns OFF."
            if "pass_line" in new_bets:
                p = new_bets["pass_line"]
                win_bet("pass_line", p)
                notes.append(f"Pass Line +{p}")
            if "pass_odds" in new_bets:
                stake = new_bets["pass_odds"]
                if point in (4, 10):   odds_p = stake * 2
                elif point in (5, 9):  odds_p = max(1, (stake * 3) // 2)
                else:                  odds_p = max(1, (stake * 6) // 5)
                win_bet("pass_odds", odds_p)
                notes.append(f"Free Odds +{odds_p}")
            if "dont_pass" in new_bets:
                lose_bet("dont_pass")
            player["cr_point"] = None

        elif total == 7:
            stick_call = "SEVEN OUT — Line Away! Puck turns OFF."
            if "pass_line" in new_bets:
                lose_bet("pass_line")
            if "pass_odds" in new_bets:
                lose_bet("pass_odds")
            if "dont_pass" in new_bets:
                p = new_bets["dont_pass"]
                win_bet("dont_pass", p)
                notes.append(f"Don't Pass +{p}")
            player["cr_point"] = None

    player["casino_chips"] = player.get("casino_chips", 0) + winnings
    player["cr_bets"] = new_bets

    hist = player.get("cr_history", [])
    hist.append((d1, d2))
    player["cr_history"] = hist[-8:]

    if notes:
        hit_str = ", ".join(notes[:3])
        player["cr_banner"] = f"Rolled {d1}+{d2} = {stick_call}  |  WIN: {hit_str}!"
    else:
        player["cr_banner"] = f"Rolled {d1}+{d2} = {stick_call}"


def step_craps_physics(player):
    """Animates the two 3D dice flying from the shooter's corner, bouncing off the rear pyramid wall, and settling."""
    if player.get("cr_phase") != "ROLLING":
        return

    now = pygame.time.get_ticks()
    elapsed = now - player.get("cr_roll_start_tick", now)
    dur = float(player.get("cr_roll_duration", 1850))
    t = min(1.0, max(0.0, elapsed / dur))

    seed = player.get("cr_traj_seed", 0.0)
    # Stage 1 (t = 0.0 -> 0.44): High arc from bottom-left shooter rail (115, 420) to right pyramid wall (725, 250)
    if t < 0.44:
        p = t / 0.44
        x1 = 115 + p * 608
        y1 = 415 - p * 172 + int(seed * 18 * p)
        z1 = math.sin(p * math.pi) * 58.0

        x2 = 135 + p * 582
        y2 = 438 - p * 165 - int(seed * 16 * p)
        z2 = math.sin(p * math.pi) * 48.0
    else:
        # Stage 2 (t = 0.44 -> 1.0): Rebound off the diamond pyramid rubber backboard & bounce to rest
        p = (t - 0.44) / 0.56
        ease = 1.0 - (1.0 - p) ** 2.6
        decay = (1.0 - p) ** 1.5

        x1 = 723 - ease * 195 + math.sin(p * 14.0) * 10.0 * decay
        y1 = 243 + ease * 165 + int(seed * 14) + math.cos(p * 12.0) * 8.0 * decay
        z1 = abs(math.sin(p * math.pi * 3.2)) * 34.0 * decay

        x2 = 717 - ease * 135 - math.sin(p * 16.0) * 10.0 * decay
        y2 = 273 + ease * 142 - int(seed * 12) + math.sin(p * 11.0) * 8.0 * decay
        z2 = abs(math.sin(p * math.pi * 3.6 + 0.5)) * 28.0 * decay

    # Tumble displayed faces rapidly until t = 0.84, then lock onto the true roll
    if t < 0.84:
        tick_step = int(now // 65)
        f1 = ((tick_step + 1) % 6) + 1
        f2 = ((tick_step * 3 + 2) % 6) + 1
        spin_ang = t * 14.0
    else:
        f1, f2 = player["cr_target_dice"]
        player["cr_dice"] = (f1, f2)
        spin_ang = (1.0 - t) * 2.5

    player["cr_anim_dice"] = [
        (int(x1), int(y1), z1, f1, spin_ang),
        (int(x2), int(y2), z2, f2, -spin_ang * 0.8)
    ]

    if t >= 1.0:
        player["cr_phase"] = "BETTING"
        d1, d2 = player["cr_target_dice"]
        player["cr_dice"] = (d1, d2)
        if player.get("cr_caught_cheating"):
            player["cr_caught_cheating"] = False
            player["cr_use_loaded"] = False
            player["cr_bets"] = {}
            if "weighted ivory dice" in player.get("inventory", []):
                player["inventory"].remove("weighted ivory dice")
            player["cr_kick_to_combat"] = True
        else:
            evaluate_craps_roll(player, d1, d2)


def draw_3d_die(screen, cx, cy, z, face_val, angle=0.0):
    """Draws an isometric 3D ivory die with a ground shadow, shaded side walls, and pips."""
    # 1. Drop shadow on the green baize
    sh_y = int(cy + 6)
    pygame.draw.ellipse(screen, (8, 28, 16), (cx - 15, sh_y - 7, 30, 16))

    dy = int(cy - z)
    r = 15
    # 4 rotated top-face corners
    base_ang = angle + math.pi / 4.0
    top_pts = []
    for i in range(4):
        a = base_ang + i * (math.pi / 2.0)
        px = cx + int(r * math.cos(a))
        py = dy + int(r * math.sin(a) * 0.78)
        top_pts.append((px, py))

    # Extrude the bottom 3 corners downward by depth=10px to create 3D cube sides
    depth = 10
    # Find front-most vertex to split left/right visible side faces
    bot_pts = [(px, py + depth) for (px, py) in top_pts]
    pygame.draw.polygon(screen, (198, 190, 172), [top_pts[0], top_pts[1], bot_pts[1], bot_pts[0]])
    pygame.draw.polygon(screen, (168, 158, 140), [top_pts[1], top_pts[2], bot_pts[2], bot_pts[1]])
    pygame.draw.polygon(screen, (212, 204, 188), [top_pts[3], top_pts[0], bot_pts[0], bot_pts[3]])

    # Top Ivory Face
    pygame.draw.polygon(screen, CARD_IVORY, top_pts)
    pygame.draw.polygon(screen, SUIT_BLACK, top_pts, width=2)

    # Draw Pips on Top Face
    pip_offsets = {
        1: [(0, 0)],
        2: [(-5, -4), (5, 4)],
        3: [(-5, -4), (0, 0), (5, 4)],
        4: [(-5, -4), (5, -4), (-5, 4), (5, 4)],
        5: [(-5, -4), (5, -4), (0, 0), (-5, 4), (5, 4)],
        6: [(-5, -4), (5, -4), (-5, 0), (5, 0), (-5, 4), (5, 4)],
    }
    pip_col = SUIT_RED if face_val in (1, 4) else SUIT_BLACK
    for ox, oy in pip_offsets.get(face_val, [(0, 0)]):
        pygame.draw.circle(screen, pip_col, (cx + ox, dy + oy), 2)

# =========================================================================
# 7. FULL-SCREEN FIRST-PERSON LONGBOW ARCHERY (30 YDS -> 50 YDS -> 70 YDS)
# =========================================================================
ARCHERY_CENTER_X = 415
ARCHERY_CENTER_Y = 278

# Progressive Distance Stages for Standard Range (and cycling in Arcade Blitz):
# Stage 0: 30 Yards (Larger target, minimal drop, 0.38s flight)
# Stage 1: 50 Yards (Medium target, moderate drop, 0.55s flight)
# Stage 2: 70 Yards (True Longbow distance, smaller target, heavy drop + wind, 0.75s flight)
ARCHERY_STAGES = [
    {"yards": 30, "bull_r": 18, "inner_r": 42, "outer_r": 74, "drop_px": 5.0,  "wind_mult": 7.5,  "flight_s": 0.38},
    {"yards": 50, "bull_r": 14, "inner_r": 33, "outer_r": 58, "drop_px": 14.0, "wind_mult": 10.5, "flight_s": 0.55},
    {"yards": 70, "bull_r": 11, "inner_r": 26, "outer_r": 46, "drop_px": 24.0, "wind_mult": 13.5, "flight_s": 0.75},
]


def _get_archery_stage(player):
    idx = min(2, player.get("archery_bullseye_streak", 0))
    return ARCHERY_STAGES[idx]


def _roll_archery_wind(player):
    streak = player.get("archery_bullseye_streak", 0)
    if not player.get("arcade_mode") and streak == 0:
        player["archery_wind"] = random.choice([-1, 0, 1])
    elif streak == 1:
        player["archery_wind"] = random.choice([-2, -1, 1, 2])
    else:
        player["archery_wind"] = random.choice([-3, -2, -1, 1, 2, 3])


def init_archery_minigame(player):
    """Initializes the Full-Screen First-Person Longbow Range (30yd -> 50yd -> 70yd)."""
    player["archery_bullseye_streak"] = 0
    player["archery_score"] = 0
    player["archery_drawn"] = False
    player["archery_draw_time"] = 0.0
    player["archery_phase_t"] = random.uniform(0.0, 6.28)
    player["archery_user_x"] = float(ARCHERY_CENTER_X)
    player["archery_user_y"] = float(ARCHERY_CENTER_Y)
    player["archery_sight_x"] = float(ARCHERY_CENTER_X)
    player["archery_sight_y"] = float(ARCHERY_CENTER_Y)
    player["archery_shots"] = []          # List of (x, y, ring_tag, stage_yards)
    player["archery_last_flight"] = None  # (dest_x, dest_y, timer, max_timer)
    player["archery_time_left"] = 60.0
    _roll_archery_wind(player)

    str_stat = player.get("strength", 0)
    player["archery_banner"] = (
        f"Range: 30 Yards (Strength: {str_stat}). Click the target or press SPACE to draw your yew longbow! "
        "Land 3 Bullseyes in a row (30 yds -> 50 yds -> 70 yds) to earn the 'Archery' skill!"
    )
    return player, "You step up to the shooting stakes of the longbow range.", "MINIGAME_ARCHERY"


def _compute_archery_sway_params(player):
    """Returns (sway_amp_px, sway_speed, stamina_limit_sec) scaled by player['strength']."""
    s = max(0, player.get("strength", 0))
    sway_amp = max(7.0, 48.0 - (s * 4.1))
    sway_speed = max(1.15, 2.75 - (s * 0.15))
    stamina_limit = 2.5 + (s * 0.45)
    return sway_amp, sway_speed, stamina_limit


def update_archery_timer(player, dt):
    """Updates first-person bow sway, keyboard/mouse steering, parabolic arrow flight, and Arcade clock."""
    # 1. Tick parabolic arrow flight animation
    flight = player.get("archery_last_flight")
    if flight:
        fx, fy, ft, fmax = flight
        ft -= dt
        player["archery_last_flight"] = (fx, fy, ft, fmax) if ft > 0 else None

    # 2. Tick 60-second Arcade Blitz clock
    if player.get("arcade_mode"):
        player["archery_time_left"] = player.get("archery_time_left", 60.0) - dt
        if player["archery_time_left"] <= 0:
            score = player.get("archery_score", 0)
            return finish_arcade_session(
                player, "archery", score,
                f"*** TIME UP! You scored {score} points on the Sharpshooter Longbow range! ***"
            )

    # 3. Update First-Person Sight Box Sway & Arm Fatigue when Bow is Drawn
    if player.get("archery_drawn"):
        player["archery_draw_time"] = player.get("archery_draw_time", 0.0) + dt
        sway_amp, sway_speed, stamina_limit = _compute_archery_sway_params(player)
        player["archery_phase_t"] = player.get("archery_phase_t", 0.0) + dt * sway_speed

        keys = pygame.key.get_pressed()
        steer_speed = 110.0 * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player["archery_user_x"] -= steer_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player["archery_user_x"] += steer_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player["archery_user_y"] -= steer_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player["archery_user_y"] += steer_speed

        player["archery_user_x"] = max(180.0, min(680.0, player["archery_user_x"]))
        player["archery_user_y"] = max(145.0, min(450.0, player["archery_user_y"]))

        t = player["archery_phase_t"]
        draw_t = player["archery_draw_time"]
        fatigue_over = max(0.0, draw_t - stamina_limit)
        tremor_amp = min(28.0, fatigue_over * 8.0)

        sway_x = math.sin(t * 1.7) * sway_amp + (math.sin(t * 13.0) * tremor_amp if tremor_amp > 0 else 0.0)
        sway_y = math.cos(t * 2.3) * (sway_amp * 0.78) + (math.cos(t * 17.0) * tremor_amp if tremor_amp > 0 else 0.0)

        player["archery_sight_x"] = max(160.0, min(700.0, player["archery_user_x"] + sway_x))
        player["archery_sight_y"] = max(135.0, min(475.0, player["archery_user_y"] + sway_y))

        if fatigue_over > 4.5:
            player["archery_drawn"] = False
            player["archery_draw_time"] = 0.0
            player["archery_banner"] = "Your bow-arm trembles and gives out from exhaustion! Catch your breath and draw again."
            return player, None, "MINIGAME_ARCHERY"

    return player, None, "MINIGAME_ARCHERY"


def _loose_arrow(player):
    """Looses the arrow down the full-screen range with distance-based gravity drop and wind drift."""
    if not player.get("archery_drawn"):
        player["archery_banner"] = "Draw your longbow first before loosing an arrow!"
        return player, None, "MINIGAME_ARCHERY"

    player["archery_drawn"] = False
    player["archery_draw_time"] = 0.0

    stage = _get_archery_stage(player)
    wind = player.get("archery_wind", 0)
    wind_drift_px = wind * stage["wind_mult"]
    gravity_drop_px = stage["drop_px"]

    hit_x = player.get("archery_sight_x", float(ARCHERY_CENTER_X)) + wind_drift_px + random.uniform(-2.0, 2.0)
    hit_y = player.get("archery_sight_y", float(ARCHERY_CENTER_Y)) + gravity_drop_px + random.uniform(-2.0, 2.0)

    dist = math.hypot(hit_x - ARCHERY_CENTER_X, hit_y - ARCHERY_CENTER_Y)
    f_dur = stage["flight_s"]
    player["archery_last_flight"] = (hit_x, hit_y, f_dur, f_dur)

    if dist <= stage["bull_r"]:
        ring = "BULLSEYE"
        player["archery_bullseye_streak"] = player.get("archery_bullseye_streak", 0) + 1
        streak = player["archery_bullseye_streak"]
        pts = 50 + (25 * (streak - 1) if player.get("arcade_mode") else 0)
        player["archery_score"] = player.get("archery_score", 0) + pts
        next_yds = ARCHERY_STAGES[min(2, streak)]["yards"]
        msg = f"THWACK! {stage['yards']}-Yard GOLD BULLSEYE! (+{pts} pts | Streak: {streak}/3! Next target: {next_yds} Yards!)"
    elif dist <= stage["inner_r"]:
        ring = "INNER"
        player["archery_bullseye_streak"] = 0
        pts = 25
        player["archery_score"] = player.get("archery_score", 0) + pts
        msg = f"THUD! Inner Ring at {stage['yards']} Yards (+25 pts) — Streak resets to 0/3 (Back to 30 Yards)!"
    elif dist <= stage["outer_r"]:
        ring = "OUTER"
        player["archery_bullseye_streak"] = 0
        pts = 10
        player["archery_score"] = player.get("archery_score", 0) + pts
        msg = f"Grazed the Outer Straw Ring at {stage['yards']} Yards (+10 pts) — Streak resets to 0/3!"
    else:
        ring = "MISS"
        player["archery_bullseye_streak"] = 0
        msg = f"WHOOSH! Your shaft sails past the {stage['yards']}-Yard butt into the turf! (Streak reset to 0/3)"

    shots = player.setdefault("archery_shots", [])
    shots.append((int(hit_x), int(hit_y), ring, stage["yards"]))
    if len(shots) > 8:
        shots.pop(0)

    player["archery_banner"] = msg

    # Check if 3 Bullseyes in a Row (30yd -> 50yd -> 70yd) unlocked the 'archery' skill!
    if player["archery_bullseye_streak"] >= 3:
        newly_learned = False
        if "archery" not in player["skills"]:
            player["skills"].append("archery")
            newly_learned = True

        if not player.get("arcade_mode"):
            if newly_learned:
                player["reputation"] += 1
                win_log = (
                    f"{msg}\n\n"
                    "=========================================================\n"
                    "   30, 50 & 70 YARDS CONQUERED! SKILL UNLOCKED: ARCHERY! \n"
                    "=========================================================\n"
                    "Your third longbow shaft arcs across the 70-yard lawn and splits the centre peg of the gold!\n"
                    "*** You have mastered the 'Archery' skill! (+1 Reputation) ***"
                )
            else:
                win_log = f"{msg}\n\n*** THREE BULLSEYES IN A ROW (30, 50 & 70 Yards)! Masterful longbow shooting! ***"
            return player, win_log, "MAIN"
        else:
            if newly_learned:
                player["archery_banner"] = msg + " [UNLOCKED 'ARCHERY' SKILL!]"

    _roll_archery_wind(player)
    player["archery_user_x"] = float(ARCHERY_CENTER_X) + random.uniform(-18.0, 18.0)
    player["archery_user_y"] = float(ARCHERY_CENTER_Y) + random.uniform(-14.0, 14.0)
    return player, None, "MINIGAME_ARCHERY"


def archery_button_action(action, player):
    if action == "draw":
        player["archery_drawn"] = True
        player["archery_draw_time"] = 0.0
        player["archery_phase_t"] = random.uniform(0.0, 6.28)
        player["archery_user_x"] = float(ARCHERY_CENTER_X) + random.uniform(-16.0, 16.0)
        player["archery_user_y"] = float(ARCHERY_CENTER_Y) + random.uniform(-12.0, 12.0)
        stage = _get_archery_stage(player)
        wind = player.get("archery_wind", 0)
        w_str = "CALM (0 mph)" if wind == 0 else f"{abs(wind)} mph {'RIGHT >>' if wind > 0 else '<< LEFT'}"
        player["archery_banner"] = (
            f"Full Draw at {stage['yards']} Yards! (Wind: {w_str} | Hold slightly high for {stage['yards']}yd gravity drop!)"
        )
        return player, None, "MINIGAME_ARCHERY"

    if action == "loose":
        return _loose_arrow(player)

    if action == "relax":
        player["archery_drawn"] = False
        player["archery_draw_time"] = 0.0
        player["archery_banner"] = "You slowly ease the yew bowstring down and rest your arm."
        return player, None, "MINIGAME_ARCHERY"

    nudge_step = 12.0
    if action == "nudge_left":
        player["archery_user_x"] = max(180.0, player.get("archery_user_x", ARCHERY_CENTER_X) - nudge_step)
    elif action == "nudge_right":
        player["archery_user_x"] = min(680.0, player.get("archery_user_x", ARCHERY_CENTER_X) + nudge_step)
    elif action == "nudge_up":
        player["archery_user_y"] = max(145.0, player.get("archery_user_y", ARCHERY_CENTER_Y) - nudge_step)
    elif action == "nudge_down":
        player["archery_user_y"] = min(450.0, player.get("archery_user_y", ARCHERY_CENTER_Y) + nudge_step)

    return player, None, "MINIGAME_ARCHERY"


def handle_archery_event(event, player):
    """Handles mouse aiming across the full-screen 740x390 range canvas, click-to-loose, and SPACE."""
    field_rect = pygame.Rect(30, 116, 740, 390)

    if event.type == pygame.MOUSEMOTION and player.get("archery_drawn"):
        mx, my = event.pos
        if field_rect.collidepoint(mx, my):
            player["archery_user_x"] = player["archery_user_x"] * 0.55 + mx * 0.45
            player["archery_user_y"] = player["archery_user_y"] * 0.55 + my * 0.45
        return player, None, "MINIGAME_ARCHERY"

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if field_rect.collidepoint(event.pos):
            if not player.get("archery_drawn"):
                return archery_button_action("draw", player)
            else:
                return _loose_arrow(player)

    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
        if not player.get("archery_drawn"):
            return archery_button_action("draw", player)
        else:
            return _loose_arrow(player)

    return player, None, "MINIGAME_ARCHERY"


def draw_archery_ui(screen, player, font, font_bold, title_font=None):
    """Renders the Full-Screen 800x600 First-Person Longbow Range with 30/50/70 Yard Progression."""
    if title_font is None:
        title_font = pygame.font.Font(None, 28)

    stage = _get_archery_stage(player)
    yards = stage["yards"]
    streak = player.get("archery_bullseye_streak", 0)
    dots = " ".join("●" if i < streak else "○" for i in range(3))

    # 1. Outer Timber Frame
    screen.fill(RAIL_WOOD)
    outer_rect = pygame.Rect(14, 14, 772, 572)
    pygame.draw.rect(screen, (28, 36, 28), outer_rect, border_radius=20)
    pygame.draw.rect(screen, BRASS_GOLD, outer_rect, width=3, border_radius=20)

    # 2. Top Brass Header Bar
    header_rect = pygame.Rect(30, 24, 740, 36)
    pygame.draw.rect(screen, (18, 28, 22), header_rect, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, header_rect, width=1, border_radius=8)

    if player.get("arcade_mode"):
        t_left = max(0.0, player.get("archery_time_left", 60.0))
        title_str = f"SHARPSHOOTER LONGBOW BLITZ — {t_left:04.1f}s LEFT"
        right_str = f"Score: {player.get('archery_score', 0)} pts  |  Range: {yards} Yds  |  Streak: {dots}"
    else:
        title_str = f"THE ARCHERY BUTTS — {yards}-YARD LONGBOW RANGE"
        right_str = f"Bullseye Streak: {dots} ({streak}/3)  |  Strength: {player.get('strength', 0)}"

    screen.blit(title_font.render(title_str, True, BRASS_GOLD), (44, 30))
    r_surf = font_bold.render(right_str, True, CARD_IVORY)
    screen.blit(r_surf, (755 - r_surf.get_width(), 33))

    # 3. Auto-Wrapped Range Master Banner Box
    banner_box = pygame.Rect(30, 66, 740, 44)
    pygame.draw.rect(screen, (20, 36, 26), banner_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, banner_box, width=1, border_radius=8)
    wind = player.get("archery_wind", 0)
    w_hdr = "WIND: CALM (0 mph)" if wind == 0 else f"CROSSWIND: {abs(wind)} mph {'EAST (>>)' if wind > 0 else 'WEST (<<)'}"
    draw_wrapped_banner(
        screen,
        f"RANGE CONDITION — {w_hdr}  |  TARGET DISTANCE: {yards} YARDS",
        player.get("archery_banner", ""),
        banner_box,
        BRASS_GOLD,
        CARD_IVORY
    )

    # 4. Main First-Person Longbow Range Viewport (30..770 x 116..504)
    vp = pygame.Rect(30, 116, 740, 388)
    pygame.draw.rect(screen, (105, 138, 170), (32, 118, 736, 108))  # Sky

    # Distant Treeline & Stone Battlements along Horizon (y = 204..226)
    for tx in range(40, 760, 28):
        pygame.draw.circle(screen, (48, 78, 46), (tx, 212), 16)
    pygame.draw.rect(screen, (76, 78, 84), (240, 204, 350, 22))
    for mx in range(244, 586, 22):
        pygame.draw.rect(screen, (76, 78, 84), (mx, 196, 12, 8))

    # Deep Receding Grassy Shooting Field (y = 226..502)
    pygame.draw.rect(screen, (52, 98, 54), (32, 226, 736, 276))
    # Perspective Lane Lines converging toward the horizon
    lane_poly = [(140, 502), (345, 226), (485, 226), (690, 502)]
    pygame.draw.polygon(screen, (62, 110, 62), lane_poly)
    pygame.draw.line(screen, (82, 132, 78), (140, 502), (345, 226), 2)
    pygame.draw.line(screen, (82, 132, 78), (690, 502), (485, 226), 2)

    # Distance Yardage Markers painted across the turf (30 Yds, 50 Yds, 70 Yds)
    for y_line, y_lbl in [(415, "30 YDS"), (345, "50 YDS"), (285, "70 YDS")]:
        pygame.draw.line(screen, (90, 140, 86), (220, y_line), (610, y_line), 1)
        yl_s = pygame.font.Font(None, 17).render(y_lbl, True, (195, 215, 185))
        screen.blit(yl_s, (618, y_line - 6))

    # 5. Large Animated Wind Pole & Fluttering Pennant (Left Side of Field, x = 118)
    pole_x = 118
    pygame.draw.line(screen, (110, 78, 46), (pole_x, 162), (pole_x, 370), 5)
    pygame.draw.circle(screen, BRASS_GOLD, (pole_x, 160), 5)
    if wind == 0:
        flag_pts = [(pole_x, 166), (pole_x + 10, 195), (pole_x, 202)]
    else:
        dir_sign = 1 if wind > 0 else -1
        flag_len = 24 + abs(wind) * 16
        flutter = int(math.sin(pygame.time.get_ticks() * 0.014) * 5)
        flag_pts = [
            (pole_x, 166),
            (pole_x + dir_sign * flag_len, 176 + flutter),
            (pole_x, 190)
        ]
    pygame.draw.polygon(screen, (198, 45, 38), flag_pts)
    pygame.draw.polygon(screen, CARD_IVORY, flag_pts, width=1)

    # 6. Timber Tripod & Distance-Scaled Concentric Straw Target Butt at (415, 278)
    cx, cy = ARCHERY_CENTER_X, ARCHERY_CENTER_Y
    out_r = stage["outer_r"]
    in_r = stage["inner_r"]
    bull_r = stage["bull_r"]

    # Timber Stand Legs scaled to target size
    leg_w = int(out_r * 0.75)
    pygame.draw.line(screen, (105, 72, 42), (cx - leg_w // 2, cy - out_r // 2), (cx - leg_w, cy + out_r + 36), 6)
    pygame.draw.line(screen, (105, 72, 42), (cx + leg_w // 2, cy - out_r // 2), (cx + leg_w, cy + out_r + 36), 6)
    pygame.draw.line(screen, (85, 58, 34), (cx, cy - out_r // 2), (cx, cy + out_r + 30), 5)

    # Straw Boss & 5 Concentric Target Rings
    pygame.draw.circle(screen, (185, 155, 90), (cx, cy), out_r + 8)
    pygame.draw.circle(screen, (95, 75, 40), (cx, cy), out_r + 8, 2)
    pygame.draw.circle(screen, (242, 238, 228), (cx, cy), out_r)                 # White Outer
    pygame.draw.circle(screen, (35, 38, 44), (cx, cy), int(out_r * 0.78))        # Black Outer
    pygame.draw.circle(screen, (55, 125, 195), (cx, cy), in_r)                   # Blue Inner
    pygame.draw.circle(screen, (205, 50, 45), (cx, cy), int(in_r * 0.68))        # Red Inner
    pygame.draw.circle(screen, (245, 200, 50), (cx, cy), bull_r)                 # Gold Bullseye
    pygame.draw.circle(screen, (40, 30, 15), (cx, cy), bull_r, 1)
    pygame.draw.circle(screen, (40, 30, 15), (cx, cy), 2)

    # 7. Draw Arrows Stuck in Target from Current Distance
    for sx_h, sy_h, r_tag, s_yds in player.get("archery_shots", []):
        if s_yds == yards:
            pygame.draw.line(screen, (215, 195, 145), (sx_h, sy_h), (sx_h + 8, sy_h + 10), 2)
            fletch_col = (250, 215, 65) if r_tag == "BULLSEYE" else (225, 70, 65)
            pygame.draw.circle(screen, fletch_col, (sx_h + 8, sy_h + 10), 3)
            pygame.draw.circle(screen, (20, 20, 20), (sx_h, sy_h), 2)

    # 8. Parabolic In-Flight Arrow Animation
    flight = player.get("archery_last_flight")
    if flight:
        fx, fy, ft, fmax = flight
        p = 1.0 - (ft / max(0.1, fmax))
        cur_x = int(415 + (fx - 415) * p)
        arc_height = 35.0 + (yards - 30) * 0.9
        cur_y = int(490 + (fy - 490) * p - math.sin(p * math.pi) * arc_height)
        tail_x = int(cur_x - (fx - 415) * 0.06)
        tail_y = int(cur_y + 14 * (1.0 - p * 0.5))
        pygame.draw.line(screen, (235, 210, 145), (tail_x, tail_y), (cur_x, cur_y), 3)
        pygame.draw.circle(screen, (255, 235, 150), (cur_x, cur_y), max(2, int(6 * (1.0 - p * 0.65))))

    # 9. Full-Scale First-Person Yew Longbow, Drawn String, Nocked Shaft & Sight Box
    is_drawn = player.get("archery_drawn", False)
    sx = int(player.get("archery_sight_x", cx))
    sy = int(player.get("archery_sight_y", cy))

    flex = 26 if is_drawn else 0
    top_tip = (210 + flex, 132)
    grip_pt = (232, 320)
    bot_tip = (220 + flex, 496)
    bow_pts = [
        top_tip,
        (195 + flex // 2, 215),
        grip_pt,
        (202 + flex // 2, 415),
        bot_tip
    ]
    pygame.draw.lines(screen, (118, 72, 34), False, bow_pts, 11)
    pygame.draw.lines(screen, (165, 110, 58), False, bow_pts, 4)
    # Leather Riser Grip & Archer's Gauntleted Bow-Hand
    pygame.draw.circle(screen, (70, 42, 24), grip_pt, 10)
    pygame.draw.circle(screen, (215, 175, 140), (grip_pt[0] + 5, grip_pt[1] + 2), 9)

    if is_drawn:
        anchor = (415, 496)
        pygame.draw.line(screen, (230, 225, 210), top_tip, anchor, 2)
        pygame.draw.line(screen, (230, 225, 210), bot_tip, anchor, 2)

        ang = math.atan2(sy - anchor[1], sx - anchor[0])
        tip_x = int(anchor[0] + math.cos(ang) * 195)
        tip_y = int(anchor[1] + math.sin(ang) * 195)
        pygame.draw.line(screen, (212, 182, 126), anchor, (tip_x, tip_y), 5)
        pygame.draw.circle(screen, (190, 200, 215), (tip_x, tip_y), 5)

        _, _, stamina_limit = _compute_archery_sway_params(player)
        draw_t = player.get("archery_draw_time", 0.0)
        strain_ratio = min(1.0, draw_t / max(0.5, stamina_limit + 2.5))
        box_col = (110, 240, 135) if draw_t <= stamina_limit else (245, 85, 75)

        sight_rect = pygame.Rect(sx - 16, sy - 16, 32, 32)
        pygame.draw.rect(screen, box_col, sight_rect, width=2, border_radius=4)
        pygame.draw.line(screen, box_col, (sx - 22, sy), (sx - 8, sy), 2)
        pygame.draw.line(screen, box_col, (sx + 8, sy), (sx + 22, sy), 2)
        pygame.draw.line(screen, box_col, (sx, sy - 22), (sx, sy - 8), 2)
        pygame.draw.line(screen, box_col, (sx, sy + 8), (sx, sy + 22), 2)
        pygame.draw.circle(screen, (255, 240, 120), (sx, sy), 2)

        # Right-Side Arm Stamina / Stability Gauge
        gauge_bg = pygame.Rect(732, 155, 22, 280)
        pygame.draw.rect(screen, (20, 25, 32), gauge_bg, border_radius=6)
        fill_h = int(280 * (1.0 - strain_ratio))
        if fill_h > 0:
            pygame.draw.rect(screen, box_col, (732, 155 + (280 - fill_h), 22, fill_h), border_radius=6)
        pygame.draw.rect(screen, BRASS_GOLD, gauge_bg, width=1, border_radius=6)
        st_lbl = pygame.font.Font(None, 16).render("ARM", True, CARD_IVORY)
        screen.blit(st_lbl, (731, 442))
    else:
        pygame.draw.line(screen, (215, 210, 195), top_tip, bot_tip, 2)

    pygame.draw.rect(screen, BRASS_GOLD, vp, width=2, border_radius=8)

    # 10. Bottom Mahogany Action Tray
    tray_rect = pygame.Rect(30, 512, 740, 58)
    pygame.draw.rect(screen, (18, 28, 22), tray_rect, border_radius=10)
    pygame.draw.rect(screen, BRASS_GOLD, tray_rect, width=1, border_radius=10)

# =========================================================================
# CHAPTER 2: MISSION 1A — 5-EXCHANGE UNION FERVOUR & PROMISE TRACKER
# =========================================================================
# Demand indices matching chapter_2.UNION_DEMANDS:
# 0: "10% Rent Reduction"
# 1: "Abolish Mill-Wheel Tariffs"
# 2: "Halt Forest Clear-Cutting"
# 3: "8-Hour Decimal Workday"
# 4: "Worker Control of Granaries"

DELEGATE_PROFILES = {
    "steadfast": {
        "name": "Ploughman Steadfast (Murum Oats)",
        "difficulty": "EASY",
        "start_fervour": 28,
        "gain_promise": 22,
        "gain_solidarity": 13,
        "loss_bad": -12,
        "stages": [
            {
                "prompt": "1/5: \"Bailiff Seekgrace's rent-collectors take every spare sack of oats. How do we survive the winter if we strike?\"",
                "options": [
                    ("Swear you won't sign a treaty without a 10% Rent Reduction!", "promise", 0),
                    ("Pool our cellar stores into a shared Strike Granary so no family starves.", "solidarity", None),
                    ("Tell him his family will just have to tighten their belts.", "bad", None),
                ]
            },
            {
                "prompt": "2/5: \"We work from dawn bell to curfew in the wet furrows until our backs give out!\"",
                "options": [
                    ("Pledge to force Seekgrace into signing an 8-Hour Decimal Workday!", "promise", 3),
                    ("Organise rotating plough-shifts among the crew so older hands can rest.", "solidarity", None),
                    ("Remind him that harvest season is always exhausting.", "bad", None),
                ]
            },
            {
                "prompt": "3/5: \"What if the Bailiff locks the estate granaries and refuses to release seed-corn in the spring?\"",
                "options": [
                    ("Promise we'll seize full Worker Control of the Granaries in the charter!", "promise", 4),
                    ("Hide a tithe of seed-oats across twenty tenant barns tonight.", "solidarity", None),
                    ("Hope the Magistrate orders the Bailiff to be reasonable.", "bad", None),
                ]
            },
            {
                "prompt": "4/5: \"The Town Watch rode past our lane this morning with halberds on their shoulders, glaring at my boys!\"",
                "options": [
                    ("Stand fifty ploughmen shoulder-to-shoulder—patrols won't charge a disciplined wall!", "solidarity", None),
                    ("Promise the Union will pay off every farmer's rent arrears in cash!", "promise", 0),
                    ("Advise his boys to scatter and hide if the Watch approaches.", "bad", None),
                ]
            },
            {
                "prompt": "5/5: \"If we march back to the brazier, Noburu, how do we know the committee won't trade away our farm claims first?\"",
                "options": [
                    ("Elect your own ploughman to sit beside me inside the bargaining hall!", "solidarity", None),
                    ("Guarantee that both Rent Cuts and the 8-Hour Day are locked into our minimum pledge!", "promise", 3),
                    ("Ask him to trust the Murum leadership blindly.", "bad", None),
                ]
            },
        ]
    },
    "goodseed": {
        "name": "Orchardist Goodseed (Fluvius Pressers)",
        "difficulty": "MEDIUM",
        "start_fervour": 20,
        "gain_promise": 22,
        "gain_solidarity": 12,
        "loss_bad": -15,
        "stages": [
            {
                "prompt": "1/5: \"Bailiff Seekgrace just doubled the toll on every cider-press and waterwheel along the river!\"",
                "options": [
                    ("Vow to Abolish Mill-Wheel & Press Tariffs completely at Fluvius Hall!", "promise", 1),
                    ("Boycott the Bailiff's stamped casks and trade directly with the river-barges.", "solidarity", None),
                    ("Suggest she pass the tariff cost onto the townsfolk.", "bad", None),
                ]
            },
            {
                "prompt": "2/5: \"The Castellan's timber-crews are clear-cutting Lignum Forest, and displaced deer and boars are trampling our orchards!\"",
                "options": [
                    ("Promise our treaty will legally Halt Forest Clear-Cutting along the border!", "promise", 2),
                    ("Build woven wattle-fencing with the Communards to guide the herds around the trees.", "solidarity", None),
                    ("Tell her to slaughter every deer that crosses the ditch.", "bad", None),
                ]
            },
            {
                "prompt": "3/5: \"Kokeshi thugs showed me a saw at dusk and threatened to ring-bark my thirty-year-old apple trees!\"",
                "options": [
                    ("Rotate armed strikers from the picket line to stand night-watch in your orchard!", "solidarity", None),
                    ("Promise we'll take Worker Control of the Granaries and seizing Kokeshi warehouses!", "promise", 4),
                    ("Suggest paying the Kokeshi a small bribe to leave her trees alone.", "bad", None),
                ]
            },
            {
                "prompt": "4/5: \"My press-hands are demanding shorter hours too, even while barrels of must are waiting to be racked!\"",
                "options": [
                    ("Pledge an 8-Hour Decimal Workday with tariff relief to pay for a second shift!", "promise", 3),
                    ("Bring idle field-strikers over to help rack the casks in mutual aid.", "solidarity", None),
                    ("Tell her to dock her press-hands' pay if they leave early.", "bad", None),
                ]
            },
            {
                "prompt": "5/5: \"Why should skilled orchardists risk our presses for grain-tenants who don't own a single barrel?\"",
                "options": [
                    ("Because the Bailiff's ledger chains the furrow and the press alike—united we break him!", "solidarity", None),
                    ("Swear that Abolishing Mill-Wheel Tariffs is the #1 non-negotiable condition of peace!", "promise", 1),
                    ("Threaten to tip her cider into the river if she refuses.", "bad", None),
                ]
            },
        ]
    },
    "ironhand": {
        "name": "Carter Ironhand (Fluvius Teamsters)",
        "difficulty": "HARD",
        "start_fervour": 12,
        "gain_promise": 22,
        "gain_solidarity": 11,
        "loss_bad": -20,
        "stages": [
            {
                "prompt": "1/5: \"Ten years ago in Parvus, the magistrates starved our strike out while the committee talked! What makes this time different?\"",
                "options": [
                    ("Swear we won't unchain a single wagon until we win Worker Control of the Granaries!", "promise", 4),
                    ("This time the ploughmen, pressers, and teamsters hold the road together—no separate peace!", "solidarity", None),
                    ("Tell him the Parvus strike only failed because the carters were weak.", "bad", None),
                ]
            },
            {
                "prompt": "2/5: \"My drivers haul grain twelve decimal hours a day in the mud while Seekgrace docks us for worn axle-grease!\"",
                "options": [
                    ("Pledge an ironclad 8-Hour Decimal Workday for every driver and farmhand!", "promise", 3),
                    ("Set up a Union wheelwright station at the barricade to service every teamster rig.", "solidarity", None),
                    ("Tell him long hours are just the lot of a carter.", "bad", None),
                ]
            },
            {
                "prompt": "3/5: \"The Kokeshi are hiring drifters to drive scab grain-wagons straight through the Fluvius barricade tomorrow!\"",
                "options": [
                    ("Unspan your Percherons and lock the heavy timber-wains wheel-to-wheel across the defile!", "solidarity", None),
                    ("Promise a 10% Rent & Toll Reduction for every teamster who blocks the road!", "promise", 0),
                    ("Pull back and let the scab convoy pass peacefully.", "bad", None),
                ]
            },
            {
                "prompt": "4/5: \"And what about the timber-barons? They're stripping the eastern woods and ruining the old logging tracks!\"",
                "options": [
                    ("Pledge to Halt Forest Clear-Cutting in the official Fluvius treaty!", "promise", 2),
                    ("Coordinate with the woodland communes so only windfall timber is hauled.", "solidarity", None),
                    ("Say the forest can burn so long as the roads stay open.", "bad", None),
                ]
            },
            {
                "prompt": "5/5: \"Last word over this porter, Noburu: if you make big promises here and cave in to Seekgrace's pipe-smoke tomorrow, what then?\"",
                "options": [
                    ("Judge me by my deeds at the bargaining table—if I break my word, the Union answers to you!", "solidarity", None),
                    ("I swear on the Union banner: we'll take the Granaries AND the 8-Hour Day or walk out trying!", "promise", 4),
                    ("Remind him that politics always requires breaking a few campaign promises.", "bad", None),
                ]
            },
        ]
    }
}


def init_farm_debate(player, delegate_key="steadfast"):
    """Initializes the 5-Exchange Union Fervour Debate & Promise Tracker."""
    prof = DELEGATE_PROFILES.get(delegate_key, DELEGATE_PROFILES["steadfast"])
    player["debate_delegate_key"] = delegate_key
    player["debate_round"] = 1
    player["debate_phase"] = "BRIEFING"

    stat_boost = max(0, (player.get("charisma", 0) - 4) * 2) + (4 if "radical theory" in player.get("skills", []) else 0)
    player["debate_fervour"] = min(42, prof["start_fervour"] + stat_boost)
    player["debate_last_delta"] = 0
    player["debate_feedback_str"] = ""
    player.setdefault("union_promises_made", [])
    player.setdefault("promises_count", 0)

    shuffled_stages = []
    for st in prof["stages"]:
        opts_copy = list(st["options"])
        random.shuffle(opts_copy)
        shuffled_stages.append({"prompt": st["prompt"], "options": opts_copy})
    player["debate_stages"] = shuffled_stages

    log = (
        f"--- UNION CANVASSING: {prof['name'].upper()} (DIFFICULTY: {prof['difficulty']}) ---\n"
        f"• Starting Union Fervour: **{player['debate_fervour']}%** (Need **60%+** to rally; **100%** for Fire-Breathing Unionist!)\n"
        "• **STRATEGIC TRADEOFF:** Making sweeping **Promises** rockets Fervour upward (+22%), but locks those demands onto your plate when you face **Bailiff Seekgrace** in Mission 1b! "
        "Building **Principled Solidarity** raises Fervour more modestly, but leaves your hands freer at the negotiating table!\n"
        "Click [Begin 5-Point Persuasion >>] when ready!"
    )
    return player, log, "MINIGAME_DEBATE"


def debate_action(choice_idx, player):
    key = player.get("debate_delegate_key", "steadfast")
    prof = DELEGATE_PROFILES.get(key, DELEGATE_PROFILES["steadfast"])
    phase = player.get("debate_phase", "BRIEFING")

    if phase == "BRIEFING":
        player["debate_phase"] = "ACTIVE"
        st = player["debate_stages"][0]
        return player, f"{prof['name']} — {st['prompt']}", "MINIGAME_DEBATE"

    if phase == "RESULT":
        return conclude_farm_debate(player)

    rnd = player.get("debate_round", 1)
    stages = player.get("debate_stages", prof["stages"])
    cur_stage = stages[rnd - 1]
    chosen_text, kind, demand_idx = cur_stage["options"][choice_idx]

    # Charisma / Equusense / Radical Theory help Principled Solidarity land harder!
    skill_bonus = (
        (2 if player.get("charisma", 0) >= 6 else 0)
        + (2 if player.get("equusense", 0) >= 5 else 0)
        + (2 if "radical theory" in player.get("skills", []) else 0)
    )

    if kind == "promise":
        delta = prof["gain_promise"]
        promises = player.setdefault("union_promises_made", [])
        if demand_idx is not None and demand_idx not in promises:
            promises.append(demand_idx)
        player["promises_count"] = player.get("promises_count", 0) + 1
        player["debate_feedback_str"] = f"PROMISE PLEDGED! (+{delta}% Fervour | Bound for 1b!)"
        react = "The workers cheer your concrete pledge—and write your promise down in their strike notebook!"
    elif kind == "solidarity":
        delta = prof["gain_solidarity"] + skill_bonus
        player["debate_feedback_str"] = f"SOLIDARITY BUILT! (+{delta}% Fervour | No Debt)"
        react = "Your grounded plan for mutual aid steadies their resolve without over-promising at the table!"
    else:
        delta = prof["loss_bad"]
        player["debate_feedback_str"] = f"ALIENATED WORKERS! ({delta}% Fervour)"
        react = "They scowl and mutter angrily—that answer dampened their spirit!"

    player["debate_last_delta"] = delta
    player["debate_fervour"] = max(0, min(100, player.get("debate_fervour", 30) + delta))

    if rnd >= 5:
        player["debate_phase"] = "RESULT"
        ferv = player["debate_fervour"]
        status = "FIRE-BREATHING UNIONIST (100%)!" if ferv >= 100 else ("RALLIED TO THE STRIKE!" if ferv >= 60 else "UNCONVINCED (<60%)")
        p_cnt = len(player.get("union_promises_made", []))
        log = (
            f"You argued: \"{chosen_text}\"\n{react}\n\n"
            f"*** FINAL FERVOUR: {ferv}% — {status} (Binding Promises Made So Far: {p_cnt}/5 Demands) ***\n"
            "Click [Conclude Parley >>] to finish!"
        )
        return player, log, "MINIGAME_DEBATE"

    player["debate_round"] = rnd + 1
    next_st = stages[rnd]
    log = (
        f"You argued: \"{chosen_text}\"\n{react} (Fervour: **{player['debate_fervour']}%**)\n\n"
        f"{prof['name']} — {next_st['prompt']}"
    )
    return player, log, "MINIGAME_DEBATE"


def update_debate_timer(player, dt):
    return player, None, "MINIGAME_DEBATE"


def conclude_farm_debate(player):
    """Concludes the 5-Exchange Union Fervour Debate and updates Mission 1A progress."""
    key = player.get("debate_delegate_key", "steadfast")
    prof = DELEGATE_PROFILES.get(key, DELEGATE_PROFILES["steadfast"])
    ferv = player.get("debate_fervour", 0)
    player["active_ch2_mission"] = None

    if ferv < 60:
        log = (
            f"*** {prof['name'].upper()} REMAINS WAVERING (Fervour: {ferv}% < 60% Required) ***\n"
            f"{prof['name']} shakes their head. \"Your words aren't enough to risk our livelihoods yet, Noburu. "
            "Come back when you have stronger answers.\"\n"
            "(Speak to them again to retry the 5-point persuasion!)"
        )
        return player, log, "MAIN"

    rallied = player.setdefault("m1a_rallied", [])
    if key not in rallied:
        rallied.append(key)

    fire = player.setdefault("m1a_firebreathers", [])
    is_fire = (ferv >= 100)
    if is_fire and key not in fire:
        fire.append(key)

    fire_banner = (
        "\n*** 100% FERVOUR: FIRE-BREATHING UNIONIST! Their entire crew seizes red banners and swears an unbreakable oath! ***"
        if is_fire else
        f"\n*** DELEGATION RALLIED (Fervour: {ferv}%)! (Tip: You can speak to them again before reporting to Joyinsorrow if you want to push for 100%!) ***"
    )

    if key == "steadfast":
        next_hint = "Now travel south to the Western Cider Orchards in the Fluvius Farmlands to convince **Orchardist Goodseed**!"
    elif key == "goodseed":
        next_hint = "Now head into **Fluvius Town** and enter **The Barge & Anchor Taproom** on the South Quayside to find **Carter Ironhand** (bring 6 silver for 3 rounds of porter!)!"
    else:
        next_hint = "All 3 delegations have been rallied! Return to **Organiser Joyinsorrow** at the farm picket line to complete Mission 1a!"

    log = (
        f"*** {prof['name'].upper()} RALLIED ({len(rallied)}/3 Delegations)! ***{fire_banner}\n"
        f"• Next Step: {next_hint}"
    )
    return player, log, "MAIN"


def draw_debate_ui(screen, player, font, font_bold):
    """Draws the Union Fervour Thermometer/Gauge, Delegate Info, and Current Objection."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, PANEL_BG, minigame_bg, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, minigame_bg, width=2, border_radius=8)

    key = player.get("debate_delegate_key", "steadfast")
    prof = DELEGATE_PROFILES.get(key, DELEGATE_PROFILES["steadfast"])
    phase = player.get("debate_phase", "BRIEFING")
    ferv = player.get("debate_fervour", 30)
    rnd = player.get("debate_round", 1)

    # Header
    hdr = f"{prof['name'].split(' (')[0].upper()} ({rnd}/5)" if phase == "ACTIVE" else prof["name"].split(" (")[0].upper()
    screen.blit(font_bold.render(hdr, True, LOCATION_ACCENT), (472, 148))
    diff_col = (110, 210, 130) if prof["difficulty"] == "EASY" else (230, 180, 80) if prof["difficulty"] == "MEDIUM" else (230, 95, 95)
    screen.blit(font.render(prof["difficulty"], True, diff_col), (710, 148))

    # --- UNION FERVOUR GAUGE (0% .. 60% Threshold .. 100% Fire-Breathing) ---
    screen.blit(font.render(f"Union Fervour: {ferv}%", True, TEXT_COLOR), (472, 174))
    if ferv >= 100:
        tag_txt, tag_col = "FIRE-BREATHING!", (255, 215, 70)
    elif ferv >= 60:
        tag_txt, tag_col = "RALLIED (60%+)", (100, 220, 120)
    else:
        tag_txt, tag_col = "WAVERING (<60%)", (220, 100, 100)
    screen.blit(font_bold.render(tag_txt, True, tag_col), (615, 174))

    bar_rect = pygame.Rect(472, 196, 296, 22)
    pygame.draw.rect(screen, (20, 25, 32), bar_rect, border_radius=5)

    fill_w = int(296 * (ferv / 100.0))
    if fill_w > 0:
        f_col = (225, 65, 50) if ferv >= 100 else (75, 195, 110) if ferv >= 60 else (210, 145, 55)
        pygame.draw.rect(screen, f_col, (472, 196, fill_w, 22), border_radius=5)

    # 60% Rally Threshold Line
    thresh_x = 472 + int(296 * 0.60)
    pygame.draw.line(screen, (255, 255, 255), (thresh_x, 194), (thresh_x, 220), 2)
    pygame.draw.rect(screen, PANEL_BORDER, bar_rect, width=2, border_radius=5)

    # Feedback line
    fb = player.get("debate_feedback_str", "")
    if fb:
        fb_col = (100, 220, 120) if "+" in fb else (230, 95, 95)
        screen.blit(font_bold.render(fb, True, fb_col), (472, 224))

    # Grievance / Prompt Box
    grievance_box = pygame.Rect(472, 248, 296, 128)
    pygame.draw.rect(screen, (20, 25, 30), grievance_box, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, grievance_box, width=1, border_radius=8)

    if phase == "BRIEFING":
        msg = f"Raise {prof['name'].split(' (')[0]}'s Fervour to 60%+ across 5 exchanges (or 100% for the Fire-Breathing bonus)!"
    elif phase == "RESULT":
        msg = f"Final Fervour: {ferv}%. " + (
            "A fire-breathing champion of the strike!" if ferv >= 100 else
            "Convinced to rejoin the picket line!" if ferv >= 60 else
            "Still unconvinced. Try stronger arguments!"
        )
    else:
        stages = player.get("debate_stages", prof["stages"])
        msg = stages[rnd - 1]["prompt"]

    draw_fitted_text(screen, msg, grievance_box.inflate(-14, -14), (255, 255, 255), max_lines=4)

# ==========================================
# CHAPTER 2: MISSION 1B — THE 10-POINT PARLEY (POP-OUT WINDOW)
# ==========================================
BARGAIN_DEMANDS = [
    # UNION DEMANDS (Indices 0..4 match Mission 1A promise indices!)
    {"id": "u_rent",    "owner": "union",   "name": "Rent Reduction",          "max_val": 20,  "unit": "%",    "start": 0,   "target": 10,  "promise_idx": 0},
    {"id": "u_tariff",  "owner": "union",   "name": "Abolish Mill Tariffs",    "max_val": 100, "unit": "%",    "start": 0,   "target": 100, "promise_idx": 1},
    {"id": "u_forest",  "owner": "union",   "name": "Halt Clear-Cutting",      "max_val": 100, "unit": "%",    "start": 0,   "target": 100, "promise_idx": 2},
    {"id": "u_hours",   "owner": "union",   "name": "Decimal Workday",         "max_val": 12,  "unit": " Hrs", "start": 12,  "target": 8,   "promise_idx": 3},
    {"id": "u_grain",   "owner": "union",   "name": "Control of Granaries",    "max_val": 100, "unit": "%",    "start": 0,   "target": 100, "promise_idx": 4},

    # BAILIFF DEMANDS (Player wants 0 / target; Seekgrace starts at max_val)
    {"id": "b_names",    "owner": "bailiff", "name": "Surrender Ringleaders",   "max_val": 10,  "unit": " Men", "start": 10,  "target": 0,   "promise_idx": None},
    {"id": "b_bond",     "owner": "bailiff", "name": "Damages Bond",            "max_val": 50,  "unit": "s",    "start": 50,  "target": 0,   "promise_idx": None},
    {"id": "b_windfall", "owner": "bailiff", "name": "Ban Windfalling",         "max_val": 100, "unit": "%",    "start": 100, "target": 0,   "promise_idx": None},
    {"id": "b_dock",     "owner": "bailiff", "name": "Dock Striker Pay",        "max_val": 100, "unit": "%",    "start": 100, "target": 0,   "promise_idx": None},
    {"id": "b_private",  "owner": "bailiff", "name": "Guarantee Private Sales", "max_val": 100, "unit": "%",    "start": 100, "target": 0,   "promise_idx": None},
]

BARGAIN_SLIDER_RECT = pygame.Rect(200, 260, 400, 18)


def init_bargain_minigame(player):
    """Initializes the 10-Point Parley Pop-Out Window with Bailiff Seekgrace."""
    player["bargain_phase"] = "DOCKET"  # "DOCKET" or "SLIDER_PLAYER"
    player["bargain_demands"] = {
        d["id"]: (d["start"] if d["owner"] == "bailiff" else d["target"])
        for d in BARGAIN_DEMANDS
    }
    player["bargain_settled"] = {d["id"]: False for d in BARGAIN_DEMANDS}
    player["bargain_selected_id"] = None
    player["bargain_slider_val"] = 0

    # Calculate Leverage (0 to 100) from Charisma, Influence, 1A Delegations & Fluvius Intel
    leverage = (
        25
        + (player.get("charisma", 0) * 4)
        + (player.get("influence", 0) * 4)
        + (player.get("union_delegations", 0) * 6)
    )
    if player.get("intel_garrison_mutiny"):
        leverage += 20
    if player.get("intel_kokeshi_debt"):
        leverage += 20
    if player.get("bailiff_tells_learned"):
        leverage += len(player.get("bailiff_tells_learned", [])) * 6

    # Daily attrition penalty for every day past Day 1
    days_elapsed = max(0, (player.get("total_game_minutes", 375) // 1000))
    player["bargain_leverage"] = max(15, min(95, leverage - (days_elapsed * 2)))

    # Seekgrace's starting patience
    promises = player.get("promises_count", 0)
    player["bargain_patience"] = max(25, 100 - (promises * 3) - (days_elapsed * 2))

    player["bargain_feedback"] = (
        "Seekgrace slides the ten-point charter across the mahogany table. "
        "\"Click any clause above to table an offer or counter-offer. I sign nothing until all ten points are settled.\""
    )
    return player, player["bargain_feedback"], "MINIGAME_BARGAIN"


def bargain_action(action_type, val, player):
    """Handles clicks in the MINIGAME_BARGAIN pop-out modal."""
    phase = player.get("bargain_phase", "DOCKET")

    if phase == "DOCKET":
        if action_type == "select_demand":
            player["bargain_selected_id"] = val
            d_obj = next(d for d in BARGAIN_DEMANDS if d["id"] == val)
            player["bargain_slider_val"] = player["bargain_demands"][val]
            player["bargain_phase"] = "SLIDER_PLAYER"
            player["bargain_settled"][val] = False
            player["bargain_feedback"] = (
                f"Tabled '{d_obj['name']}'. Drag the slider (or use the - / + buttons) to set your proposal, then click [Submit Offer to Seekgrace]."
            )
            return player, None, "MINIGAME_BARGAIN"

        elif action_type == "leave_table":
            player["active_ch2_mission"] = None
            log = (
                "You step away from the bargaining table without a signed charter. "
                "The strike drags on—return to Bailiff Seekgrace when you are ready to resume negotiations."
            )
            return player, log, "MAIN"

        elif action_type == "conclude":
            if all(player["bargain_settled"].values()):
                return conclude_bargain_minigame(player)
            unsettled_cnt = sum(1 for v in player["bargain_settled"].values() if not v)
            player["bargain_feedback"] = (
                f"Seekgrace raps his knuckles on the parchment. \"There are still {unsettled_cnt} unsettled clauses on the docket, Delegate!\""
            )
            return player, None, "MINIGAME_BARGAIN"

    elif phase == "SLIDER_PLAYER":
        d_id = player.get("bargain_selected_id")
        d_obj = next(d for d in BARGAIN_DEMANDS if d["id"] == d_id)
        step = 1 if d_obj["max_val"] <= 20 else 5

        if action_type == "back_docket":
            player["bargain_phase"] = "DOCKET"
            return player, None, "MINIGAME_BARGAIN"

        elif action_type == "step_minus":
            min_v = 8 if d_id == "u_hours" else 0
            player["bargain_slider_val"] = max(min_v, player.get("bargain_slider_val", 0) - step)
            return player, None, "MINIGAME_BARGAIN"

        elif action_type == "step_plus":
            player["bargain_slider_val"] = min(d_obj["max_val"], player.get("bargain_slider_val", 0) + step)
            return player, None, "MINIGAME_BARGAIN"

        elif action_type == "submit_offer":
            offer_val = player["bargain_slider_val"]

            # Calculate how hard the player is pushing (0.0 = full concession to Bailiff, 1.0 = max Union demand)
            if d_obj["owner"] == "union":
                if d_id == "u_hours":
                    push_ratio = (12.0 - offer_val) / 4.0 if offer_val <= 12 else 0.0
                else:
                    push_ratio = offer_val / float(d_obj["max_val"])
            else:
                push_ratio = (d_obj["max_val"] - offer_val) / float(d_obj["max_val"])

            # --- 2d6 BOUNDED NEGOTIATION ROLL & TABLE TWISTS ---
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            dice_swing = (d1 + d2 - 7) * 4  # Swings leverage by -20 to +20!
            roll_tag = f"[Roll {d1}+{d2}={d1+d2}] "

            twist_msg = ""
            if d1 + d2 == 12:
                dice_swing += 10
                player["bargain_patience"] = min(100, player.get("bargain_patience", 50) + 5)
                twist_msg = " [WINDFALL: A clerk whispers that another grain-barge just cancelled its contract—Seekgrace blinks!] "
            elif d1 + d2 == 2:
                dice_swing -= 10
                twist_msg = " [FRICTION: Seekgrace's quill snaps in half, souring his temper!] "

            effective_leverage = player.get("bargain_leverage", 50) + dice_swing
            resistance = (push_ratio * 100.0) - effective_leverage

            if resistance <= 5:
                player["bargain_demands"][d_id] = offer_val
                player["bargain_settled"][d_id] = True
                player["bargain_feedback"] = (
                    f"{roll_tag}{twist_msg}Seekgrace dips his quill and initials the margin: \"Very well. '{d_obj['name']}' is settled at {offer_val}{d_obj['unit']}.\""
                )
                player["bargain_phase"] = "DOCKET"
            else:
                push_back_pct = min(0.85, max(0.20, resistance / 100.0))
                if d_obj["owner"] == "union":
                    if d_id == "u_hours":
                        ai_counter = min(12, max(8, int(round(offer_val + (12 - offer_val) * push_back_pct))))
                    else:
                        ai_counter = max(0, int(round(offer_val * (1.0 - push_back_pct))))
                else:
                    ai_counter = min(d_obj["max_val"], int(round(offer_val + (d_obj["max_val"] - offer_val) * push_back_pct)))

                prev_table_val = player["bargain_demands"][d_id]
                if (
                    (d_obj["owner"] == "union" and d_id != "u_hours" and offer_val <= prev_table_val)
                    or (d_id == "u_hours" and offer_val >= prev_table_val)
                    or (d_obj["owner"] == "bailiff" and offer_val >= prev_table_val)
                ):
                    player["bargain_demands"][d_id] = offer_val
                    player["bargain_settled"][d_id] = True
                    player["bargain_feedback"] = (
                        f"{roll_tag}Seekgrace nods curtly. \"A sensible compromise. '{d_obj['name']}' is settled at {offer_val}{d_obj['unit']}.\""
                    )
                    player["bargain_phase"] = "DOCKET"
                else:
                    player["bargain_demands"][d_id] = ai_counter
                    patience_loss = 6 if (d1 + d2 >= 8) else 10
                    player["bargain_patience"] = player.get("bargain_patience", 50) - patience_loss
                    if player["bargain_patience"] <= 0:
                        return fail_bargain_minigame(player)
                    player["bargain_feedback"] = (
                        f"{roll_tag}{twist_msg}\"Out of the question!\" Seekgrace counters '{d_obj['name']}' at {ai_counter}{d_obj['unit']}. "
                        "(Click the clause again to accept his counter-offer or test your luck!)"
                    )
                    player["bargain_phase"] = "DOCKET"

            return player, player["bargain_feedback"], "MINIGAME_BARGAIN"

    return player, None, "MINIGAME_BARGAIN"


def fail_bargain_minigame(player):
    player["active_ch2_mission"] = None
    log = (
        "*** NEGOTIATIONS COLLAPSED! ***\n"
        "Bailiff Seekgrace's thumb twists his iron signet ring until his knuckles turn white. He slams his brass ledger shut!\n"
        "\"Enough! We are wasting ink! Come back when the Union is ready to talk sense!\"\n"
        "(Talks have broken down for today. Speak to Bailiff Seekgrace to reconvene the parley!)"
    )
    return player, log, "MAIN"


def conclude_bargain_minigame(player):
    player["ch2_mission_step"] = 3
    player["active_ch2_mission"] = None

    promised = player.get("union_promises_made", [])
    broken = []
    for p_idx in promised:
        d_obj = BARGAIN_DEMANDS[p_idx]
        final_val = player["bargain_demands"][d_obj["id"]]
        if d_obj["id"] == "u_hours" and final_val > 8:
            broken.append(d_obj["name"])
        elif d_obj["id"] != "u_hours" and final_val < d_obj["target"]:
            broken.append(d_obj["name"])

    # Also tally concessions made to the Bailiff's demands
    bailiff_concessions = 0
    for d in BARGAIN_DEMANDS[5:]:
        val = player["bargain_demands"][d["id"]]
        if val > 0:
            bailiff_concessions += int((val / float(d["max_val"])) * 6)

    fire_cnt = len(player.get("m1a_firebreathers", []))
    fall_per_broken = 12 if fire_cnt >= 2 else 8

    betrayal_loss = len(broken) * fall_per_broken
    net_gain = max(5, 40 - betrayal_loss - bailiff_concessions)
    player["position_strength"] = max(0, player.get("position_strength", 0) + net_gain)

    if broken:
        modify_faction(player, "faction_union", -len(broken))
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        b_names = ", ".join(broken)
        betrayal_note = (
            f"\n\n*** BROKEN PROMISES BACKLASH! ***\n"
            f"Although the charter is signed, you compromised on **{b_names}** after promising the full demand to the strikers!\n"
            f"The higher you lifted their hopes, the harder they turn on you now (-{betrayal_loss}% Position Strength, -{len(broken)} Union Faction, +1 Exposure Tell)!"
        )
    else:
        modify_faction(player, "faction_union", 3)
        betrayal_note = "\n\n*** ALL PROMISES KEPT! The rank-and-file hail your unyielding diplomacy! (+3 Union Faction) ***"

    log = (
        f"*** TREATY SIGNED (Mission 1b Complete — +{net_gain}% Position Strength)! ***\n"
        "All ten points of the Fluvius Charter are initialled and sealed with Seekgrace's iron signet ring."
        f"{betrayal_note}\n\n"
        "*** Next (Mission 1c): Return to Organiser Joyinsorrow at the farm picket line to confront the Kokeshi scab convoy! ***"
    )
    return player, log, "MAIN"


def draw_bargain_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x470 Tate Britain Pop-Out Window for the 10-Point Parley."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    # Header & Physical Habit Description (No numeric spoilers!)
    title = font_bold.render("FLUVIUS COUNTING HOUSE — THE TEN-POINT PARLEY", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 54))

    patience = player.get("bargain_patience", 100)
    if patience >= 70:
        tell_prose = "Seekgrace packs his clay pipe with cheap shag and blows a ring of grey smoke."
    elif patience >= 40:
        tell_prose = "Seekgrace removes his brass spectacles and polishes the lenses with a linen cloth."
    else:
        tell_prose = "Seekgrace's jaw tightens as his thumb twists the heavy iron signet ring on his hand."

    tell_box = pygame.Rect(85, 82, 630, 28)
    pygame.draw.rect(screen, (230, 222, 205), tell_box, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, tell_box, width=1, border_radius=6)
    draw_fitted_text(screen, tell_prose, tell_box, CLOCK_BLACK, bold=True, max_lines=1)

    phase = player.get("bargain_phase", "DOCKET")
    promised = player.get("union_promises_made", [])
    settled_cnt = sum(1 for v in player.get("bargain_settled", {}).values() if v)

    if phase == "DOCKET":
        # Column Headers
        screen.blit(font_bold.render("UNION DEMANDS (Click to Table)", True, TATE_RED), (85, 118))
        screen.blit(font_bold.render("BAILIFF COUNTER-DEMANDS", True, TATE_RED), (415, 118))
        pygame.draw.line(screen, TATE_RED, (85, 138), (715, 138), 2)

        for i in range(5):
            # Left Column: Union Demand i | Right Column: Bailiff Demand i+5
            for col_idx, d in enumerate([BARGAIN_DEMANDS[i], BARGAIN_DEMANDS[i + 5]]):
                rx = 85 if col_idx == 0 else 415
                ry = 146 + i * 42
                row_rect = pygame.Rect(rx, ry, 295, 36)

                is_settled = player["bargain_settled"].get(d["id"], False)
                val = player["bargain_demands"].get(d["id"], d["start"])
                is_hover = row_rect.collidepoint(mouse_pos)
                is_promised = (d.get("promise_idx") in promised)

                if is_settled:
                    bg_col = (205, 232, 208) if not is_hover else (190, 222, 195)
                    border_col = (40, 120, 55)
                else:
                    bg_col = (224, 216, 198) if is_hover else (252, 248, 238)
                    border_col = TATE_RED if is_promised else CLOCK_BLACK

                pygame.draw.rect(screen, bg_col, row_rect, border_radius=6)
                pygame.draw.rect(screen, border_col, row_rect, width=2 if (is_hover or is_promised or is_settled) else 1, border_radius=6)

                prom_tag = " [PROMISED]" if is_promised else ""
                status_tag = " [SETTLED]" if is_settled else ""
                lbl = f"{d['name']}: {val}{d['unit']}{prom_tag}{status_tag}"
                draw_fitted_text(screen, lbl, row_rect.inflate(-8, -4), CLOCK_BLACK, bold=is_settled, align="left", max_lines=1)

        # Feedback / Parley Transcript Box
        fb_box = pygame.Rect(85, 362, 630, 62)
        pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
        pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
        fb_txt = f"[{settled_cnt}/10 Clauses Settled]  " + player.get("bargain_feedback", "")
        draw_fitted_text(screen, fb_txt, fb_box.inflate(-16, -10), (245, 240, 230), max_lines=2)

    elif phase == "SLIDER_PLAYER":
        d_id = player.get("bargain_selected_id")
        d_obj = next(d for d in BARGAIN_DEMANDS if d["id"] == d_id)
        val = player.get("bargain_slider_val", 0)
        cur_table = player["bargain_demands"].get(d_id, d_obj["start"])

        box = pygame.Rect(110, 130, 580, 285)
        pygame.draw.rect(screen, (236, 230, 214), box, border_radius=10)
        pygame.draw.rect(screen, CLOCK_BLACK, box, width=1, border_radius=10)

        hdr = f"CLAUSE ON THE TABLE: {d_obj['name'].upper()}"
        h_surf = font_bold.render(hdr, True, TATE_RED)
        screen.blit(h_surf, (400 - h_surf.get_width() // 2, 146))

        if d_obj["owner"] == "union":
            goal_str = f"Union Goal: {d_obj['target']}{d_obj['unit']}   |   Current Table Position: {cur_table}{d_obj['unit']}"
        else:
            goal_str = f"Union Goal: 0{d_obj['unit']} (Reject Bailiff Demand)   |   Seekgrace Demands: {cur_table}{d_obj['unit']}"
        g_surf = font.render(goal_str, True, CLOCK_BLACK)
        screen.blit(g_surf, (400 - g_surf.get_width() // 2, 178))

        # Proposed Value Readout
        prop_surf = pygame.font.Font(None, 36).render(f"Your Proposal: {val}{d_obj['unit']}", True, TATE_RED)
        screen.blit(prop_surf, (400 - prop_surf.get_width() // 2, 214))

        # Slider Track (BARGAIN_SLIDER_RECT = pygame.Rect(200, 260, 400, 18))
        pygame.draw.rect(screen, (40, 44, 52), BARGAIN_SLIDER_RECT, border_radius=9)
        pygame.draw.rect(screen, TATE_RED, BARGAIN_SLIDER_RECT, width=2, border_radius=9)

        min_v = 8 if d_id == "u_hours" else 0
        span = max(1, d_obj["max_val"] - min_v)
        pct = max(0.0, min(1.0, (val - min_v) / float(span)))
        fill_w = int(BARGAIN_SLIDER_RECT.width * pct)
        if fill_w > 0:
            pygame.draw.rect(screen, (168, 50, 35), (BARGAIN_SLIDER_RECT.x, BARGAIN_SLIDER_RECT.y, fill_w, BARGAIN_SLIDER_RECT.height), border_radius=9)

        hx = BARGAIN_SLIDER_RECT.x + fill_w
        hy = BARGAIN_SLIDER_RECT.centery
        pygame.draw.circle(screen, DIAL_CREAM, (hx, hy), 12)
        pygame.draw.circle(screen, TATE_RED, (hx, hy), 12, width=3)

        hint_s = font.render("Drag the slider knob with your mouse or click [ - ] / [ + ] below:", True, (90, 80, 70))
        screen.blit(hint_s, (400 - hint_s.get_width() // 2, 295))

# ==========================================
# CHAPTER 2: HALBERD DRILL MINIGAME (MISSION 2A)
# ==========================================
DRILL_COMMANDS = [
    "HIGH GUARD!",
    "THRUST!",
    "SWEEP!",
    "SHIELD WALL!"
]

def init_halberd_drill(player):
    """Initializes the Mission 2a Town Guard Drill in the BRIEFING state."""
    player["drill_phase"] = "BRIEFING"
    player["drill_round"] = 1
    player["drill_mistakes"] = 0
    player["drill_score"] = 0
    player["drill_stance_feedback"] = None
    
    player["drill_pendulum_pos"] = -1.0 
    player["drill_pendulum_dir"] = 1
    player["drill_passes"] = 0
    
    # Base speed 2.5, minus 0.1 per STR
    str_stat = player.get("strength", 0)
    player["drill_speed"] = max(2, 3.5 - (str_stat * 0.1))
    
    log = (
        "--- MISSION: PARADE GROUND DRILL ---\n" # MISSION 2A
        "Lieutenant Beornraed calls the squad to attention.\n"
        "\"Listen up, recruit! We drill as a single unit! When I call a stance, wait for the exact beat—do not step early, and do not step late!\"\n"
        "Click [Step Into Line & Begin Drill >>] to begin the cadence drill!"
    )
    return player, log, "MINIGAME_DRILL"

def start_next_drill_round(player):
    if player["drill_round"] > 8:
        return conclude_halberd_drill(player)
        
    command = random.choice(DRILL_COMMANDS)
    player["drill_current_command"] = command
    player["drill_correct_action"] = command
    
    player["drill_pendulum_pos"] = -1.0
    player["drill_pendulum_dir"] = 1
    player["drill_passes"] = 0
    
    player["drill_stance_feedback"] = None
    player["drill_feedback_timer"] = 0.0
    player["drill_phase"] = "SWEEPING"
    
    log = f"--- PARADE DRILL (Round {player['drill_round']}/8) ---\n"
    log += f"Sergeant: \"{command}\"\n"
    log += "Follow the count: 1... 2... Click on 3!"
    
    return player, log, "MINIGAME_DRILL"

def update_drill_timer(player, dt):
    phase = player.get("drill_phase")
    
    if phase == "FEEDBACK":
        player["drill_feedback_timer"] -= dt
        if player["drill_feedback_timer"] <= 0:
            if player["drill_mistakes"] >= 3:
                return fail_halberd_drill(player, "*** DISMISSED! You broke formation too many times! ***")
            player["drill_round"] += 1
            return start_next_drill_round(player)
        return player, None, "MINIGAME_DRILL"

    if phase == "SWEEPING":
        speed = player.get("drill_speed", 3.5)
        old_pos = player["drill_pendulum_pos"]
        
        # Move the pendulum
        player["drill_pendulum_pos"] += speed * dt * player["drill_pendulum_dir"]
        new_pos = player["drill_pendulum_pos"]
        
        # Check if the pendulum crossed the center (0.0) this frame
        if (old_pos < 0.0 and new_pos >= 0.0) or (old_pos > 0.0 and new_pos <= 0.0):
            player["drill_passes"] += 1
            
        # Bounce at the edges
        if new_pos >= 1.0:
            player["drill_pendulum_pos"] = 1.0
            player["drill_pendulum_dir"] = -1
        elif new_pos <= -1.0:
            player["drill_pendulum_pos"] = -1.0
            player["drill_pendulum_dir"] = 1

        # If it passes the center a 4th time, they missed the 3rd beat!
        if player["drill_passes"] >= 4:
            player["drill_mistakes"] = player.get("drill_mistakes", 0) + 1
            player["drill_stance_feedback"] = ("TOO SLOW!", "At Ease")
            player["drill_phase"] = "FEEDBACK"
            player["drill_feedback_timer"] = 0.8
            log_msg = f"*** HESITATION! You missed the 3-count! (Mistake {player['drill_mistakes']}/3) ***"
            return player, log_msg, "MINIGAME_DRILL"

    return player, None, "MINIGAME_DRILL"

def drill_action(action_type, player):
    if player.get("drill_phase") == "BRIEFING":
        if action_type == "start":
            return start_next_drill_round(player)
        return player, None, "MINIGAME_DRILL"
        
    if player.get("drill_phase") != "SWEEPING":
        return player, None, "MINIGAME_DRILL"
        
    correct_act = player["drill_correct_action"]
    pos = player["drill_pendulum_pos"]
    abs_pos = abs(pos)
    
    # 0.0 to 0.05 = PERFECT GREEN
    # 0.05 to 0.20 = AMBER
    # > 0.20 = RED
    
    current_pass = player.get("drill_passes", 0)
    
    # If they click before it crosses the center the first time, it's considered pass 1
    if current_pass == 0:
        current_pass = 1
        
    if action_type != correct_act:
        player["drill_mistakes"] += 1
        timing_str = "WRONG STANCE!"
        log_msg = f"*** CLUMSY! You took the wrong stance! (Mistake {player['drill_mistakes']}/3) ***"
    else:
        # Player MUST click on Pass 3 AND be inside the Green Zone (abs_pos <= 0.05)
        if current_pass == 3:
            if abs_pos <= 0.05:
                player["drill_score"] += 1
                timing_str = "PERFECT CADENCE!"
                log_msg = "*** CRISP MOVEMENT! Perfectly on the 3-count! ***"
            elif abs_pos <= 0.20: 
                timing_str = "RAGGED TIMING"
                log_msg = "You clicked on 3, but were slightly early/late to the center."
            else:
                player["drill_mistakes"] += 1
                timing_str = "OUT OF STEP!"
                log_msg = f"*** SLOPPY! You clicked on 3, but missed the green zone! (Mistake {player['drill_mistakes']}/3) ***"
        else: 
            player["drill_mistakes"] += 1
            timing_str = f"CLICKED ON COUNT {current_pass}!"
            log_msg = f"*** OUT OF STEP! You must wait for the 3rd pass! (Mistake {player['drill_mistakes']}/3) ***"

    player["drill_stance_feedback"] = (timing_str, action_type)
    player["drill_phase"] = "FEEDBACK"
    player["drill_feedback_timer"] = 0.8
    
    return player, log_msg, "MINIGAME_DRILL"

def fail_halberd_drill(player, extra_log):
    player["active_ch2_mission"] = None
    log = extra_log + "\n\n"
    log += "Lieutenant Beornraed shakes his head in disgust. \"Sloppy! Get off my parade ground!\"\n"
    log += "*** MISSION FAILED! You must retry the drill to advance! ***"
    return player, log, "MAIN"

def conclude_halberd_drill(player):
    """Calculates final Position Strength and rewards for completing the Mission 2A Halberd Drill."""
    player["ch2_mission_step"] = 2
    player["active_ch2_mission"] = None

    score = player.get("drill_score", 0)
    if score >= 8:
        perf_bonus = score * 2
        gain = 10 + perf_bonus
        log = (
            f"*** FLAWLESS DRILL! MISSION COMPLETE! (+{gain}% Position Strength, +25 Silver) ***\n"
            "You command all eight beats of the halberd-cadence without a single misstep! Mayor Givethanks pins a Corporal's epaulette to your collar.\n"
            "*** Next Mission: Speak to Lieutenant Beornraed to receive an urgent dispatch regarding a riot in Fluvius Town! ***"
        )
    else:
        perf_bonus = score
        gain = 10 + perf_bonus
        log = (
            f"*** MISSION COMPLETE! (+{gain}% Position Strength, +25 Silver) ***\n"
            "You complete the halberd-cadence drill on the parade ground. Mayor Givethanks salutes your unit in thanks.\n"
            "*** Next Mission: Speak to Lieutenant Beornraed to receive an urgent dispatch regarding a riot in Fluvius Town! ***"
        )

    player["position_strength"] = player.get("position_strength", 0) + gain
    player["silver"] += 25

    return player, log, "MAIN"


def draw_drill_silhouette(screen, cx, cy, stance, is_player, is_feedback):
    """Draws a single geometric soldier posing with a halberd and shield."""
    head_col = (190, 160, 120) if is_player else (100, 110, 120)
    torso_col = (50, 70, 110) if is_player else (80, 90, 100)
    
    pygame.draw.circle(screen, head_col, (cx, cy - 25), 10)
    
    if stance == "HIGH GUARD!":
        pygame.draw.rect(screen, torso_col, (cx - 10, cy - 10, 20, 35), border_radius=4)
        pygame.draw.line(screen, (200, 200, 200), (cx - 25, cy - 40), (cx + 25, cy - 40), 4)
        pygame.draw.polygon(screen, (220, 220, 220), [(cx + 15, cy - 40), (cx + 25, cy - 50), (cx + 25, cy - 30)])
        
    elif stance == "THRUST!":
        pygame.draw.polygon(screen, torso_col, [(cx - 5, cy - 15), (cx + 15, cy - 5), (cx + 5, cy + 25), (cx - 15, cy + 25)])
        pygame.draw.line(screen, (200, 200, 200), (cx - 20, cy), (cx + 35, cy), 4)
        pygame.draw.polygon(screen, (220, 220, 220), [(cx + 25, cy), (cx + 40, cy - 10), (cx + 40, cy + 10)])
        
    elif stance == "SWEEP!":
        pygame.draw.rect(screen, torso_col, (cx - 12, cy - 5, 24, 30), border_radius=4)
        pygame.draw.line(screen, (200, 200, 200), (cx - 25, cy + 15), (cx + 25, cy + 25), 4)
        pygame.draw.polygon(screen, (220, 220, 220), [(cx + 15, cy + 21), (cx + 30, cy + 15), (cx + 30, cy + 30)])
        
    elif stance == "SHIELD WALL!":
        pygame.draw.rect(screen, torso_col, (cx - 10, cy, 20, 25), border_radius=4)
        pygame.draw.line(screen, (200, 200, 200), (cx - 20, cy + 20), (cx + 25, cy - 25), 4)
        pygame.draw.polygon(screen, (220, 220, 220), [(cx + 15, cy - 15), (cx + 30, cy - 30), (cx + 25, cy - 10)])
        pygame.draw.rect(screen, (130, 80, 50), (cx - 15, cy - 15, 12, 35), border_radius=3)
        
    else:
        # At Ease
        pygame.draw.rect(screen, torso_col, (cx - 10, cy - 10, 20, 35), border_radius=4)
        pygame.draw.line(screen, (200, 200, 200), (cx + 12, cy - 30), (cx + 12, cy + 25), 4)


def draw_drill_ui(screen, player, font, font_bold):
    """Draws the Drill Briefing or the swinging timing gauge and animated silhouettes."""
    minigame_bg = pygame.Rect(460, 140, 320, 248)
    pygame.draw.rect(screen, (35, 42, 54), minigame_bg, border_radius=8)
    pygame.draw.rect(screen, (55, 65, 81), minigame_bg, width=2, border_radius=8)

    phase = player.get("drill_phase", "BRIEFING")
    
    if phase == "BRIEFING":
        title = font_bold.render("PARADE GROUND DRILL", True, (240, 180, 120))
        screen.blit(title, (475, 150))
        
        info = [
            "Wait for Beornraed's command.",
            "Watch the timing gauge and count:",
            "\"1... 2... Click on 3!\"",
            "Click the correct stance button",
            "ONLY when the black marker sweeps",
            "across the GREEN center zone on pass 3!",
        ]
        y = 180
        for line in info:
            screen.blit(font.render(line, True, (240, 240, 240)), (475, y))
            y += 22
            
    else:
        title = font_bold.render(f"DRILL ROUND {player.get('drill_round', 1)}/8", True, (240, 180, 120))
        screen.blit(title, (475, 148))
        
        mistakes = player.get("drill_mistakes", 0)
        m_surf = font.render(f"Mistakes: {mistakes}/3", True, (220, 80, 80) if mistakes > 0 else (160, 174, 192))
        screen.blit(m_surf, (670, 148))
        
        command_box = pygame.Rect(475, 172, 290, 36)
        pygame.draw.rect(screen, (20, 25, 30), command_box, border_radius=8)
        
        # --- DYNAMIC PASS COUNT ---
        pos = player.get("drill_pendulum_pos", 0.0)
        abs_pos = abs(pos)
        current_pass = player.get("drill_passes", 0)
        
        # If it hasn't crossed the center yet, we are anticipating pass 1
        display_pass = current_pass + 1 if current_pass < 3 else "LATE"
        
        # We pulse the number when the pendulum is within the amber/green zones
        # 1.0 - (0.35 / 0.35) = 0 (no pulse at edges of amber)
        # 1.0 - (0.0 / 0.35) = 1 (max pulse at dead center)
        pulse_factor = max(0.0, 1.0 - (abs_pos / 0.35))
        
    
        if display_pass == 1:
            count_col = (200, 80, 80)
            pulse = int(pulse_factor * 8)
            count_str = "0"
        elif display_pass == 2:
            count_col = (200, 80, 80)
            pulse = int(pulse_factor * 10)
            count_str = "1"
        elif display_pass == 3:
            count_col = (200, 80, 80)
            pulse = int(pulse_factor * 10)
            count_str = "2"
        else:
            count_col = (80, 200, 80)
            pulse = int(pulse_factor * 16) # Largest pulse on 3
            count_str = "3!"
            
        count_font = pygame.font.Font(None, 24 + pulse)
        count_surf = count_font.render(count_str, True, count_col)
        
        cmd_text = player.get("drill_current_command", "")
        cmd_surf = font_bold.render(cmd_text, True, (255, 255, 255))
        
        # Draw the Count centered to the left of the Command
        total_w = count_surf.get_width() + 10 + cmd_surf.get_width()
        start_x = command_box.centerx - (total_w // 2)
        
        # We offset the text vertically slightly so the center remains aligned despite the pulsing font size
        cy = command_box.centery - count_surf.get_height() // 2
        screen.blit(count_surf, (start_x, cy))
        screen.blit(cmd_surf, (start_x + count_surf.get_width() + 10, command_box.centery - cmd_surf.get_height() // 2))
        
        # --- TIMING GAUGE ---
        gauge_rect = pygame.Rect(475, 240, 290, 20)
        pygame.draw.rect(screen, (200, 80, 80), gauge_rect, border_radius=5) 
        
        amber_w = int(290 * 0.15) 
        amber_l = pygame.Rect(475 + int(290 * 0.35), 240, amber_w, 20)
        amber_r = pygame.Rect(475 + int(290 * 0.50), 240, amber_w, 20)
        pygame.draw.rect(screen, (200, 160, 80), amber_l)
        pygame.draw.rect(screen, (200, 160, 80), amber_r)
        
        green_w = int(290 * 0.05)
        green_rect = pygame.Rect(475 + int(290 * 0.475), 240, green_w, 20)
        pygame.draw.rect(screen, (80, 200, 80), green_rect)
        
        # Calculate pendulum position
        normalized_pos = (pos + 1.0) / 2.0
        line_x = 475 + int(290 * normalized_pos)
        pygame.draw.line(screen, (255, 255, 255), (line_x, 238), (line_x, 262), 4)

        # --- 4 SILHOUETTES ---
        sil_y = 310
        sil_w = 40
        sil_gap = 20
        start_x = 475 + (290 - (sil_w * 4 + sil_gap * 3)) // 2
        
        correct_act = player.get("drill_correct_action", "At Ease")
        feedback = player.get("drill_stance_feedback")
        
        for i in range(4):
            cx = start_x + i * (sil_w + sil_gap) + sil_w // 2
            is_player = (i == 3)
            
            if phase == "FEEDBACK":
                stance = feedback[1] if is_player else correct_act
            else:
                stance = "At Ease"
                
            draw_drill_silhouette(screen, cx, sil_y, stance, is_player, phase == "FEEDBACK")
            
            if is_player:
                screen.blit(font.render("YOU", True, (240, 180, 120)), (cx - 12, sil_y + 35))
                
        if phase == "FEEDBACK" and feedback:
            res_str = feedback[0]
            res_col = (80, 200, 80) if "PERFECT" in res_str else (200, 80, 80) if "WRONG" in res_str or "SLOPPY" in res_str or "SLOW" in res_str or "CLICKED" in res_str else (200, 160, 80)
            f_surf = font_bold.render(res_str, True, res_col)
            screen.blit(f_surf, (475, 265))

# -------------------------    
# ARCADE BENCHMARKS
# -------------------------

ARCADE_BENCHMARKS = {
    "forge": 250,      # 25+ strikes in 60s
    "jigsaw": 200,     # 2+ boards in 60s
    "chase": 100,      # Catching the thief cleanly
    "flytip": 200,     # 2+ randomized cases in 75s
    "parapet": 90,     # Extracting the silk cleanly
    "smuggle": 95,     # Completing the run cleanly
    "recipe": 200,     # 2+ randomized potions in 60s
    "sounding": 200,   # 2+ flawed walls pinpointed in 60s
    "archery": 250,    # 250+ points in 60s Sharpshooter Blitz
}

def check_arcade_champion_prize(player, cabinet_key, score):
    """Awards a one-time 10-Chip + 1 Reputation House Prize for beating a cabinet's benchmark."""
    claimed = player.setdefault("arcade_prizes_claimed", [])
    target = ARCADE_BENCHMARKS.get(cabinet_key, 1)
    if cabinet_key not in claimed and score >= target:
        claimed.append(cabinet_key)
        player["casino_chips"] = player.get("casino_chips", 0) + 10
        player["reputation"] = player.get("reputation", 0) + 1
        return (
            f"\n*** HOUSE RECORD BROKEN! Croupier Fortunesmile applauds and awards you "
            f"+10 Casino Chips and +1 Reputation! ({len(claimed)}/9 Cabinets Conquered) ***"
        )
    return ""
