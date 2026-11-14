import hashlib
import os
import pygame
import game_data as db
from mechanics import modify_faction, advance_time
from ui_components import draw_fitted_text


# =========================================================================
# 1. EXTERNAL / HASHED PROHIBITED WORD FILTER (ZERO OFFENSIVE WORDS IN CODE!)
# =========================================================================
# Optional SHA-256 16-char prefixes of prohibited words (unreadable in source code).
# You can also drop a standard open-source 'prohibited_words.txt' (e.g. LDNOOBW) in the game folder
# or `pip install better_profanity` and this function will automatically use it!
PROHIBITED_SHA256_PREFIXES = {
    "04d6329713640152", "17a0690574264663", "2c26b46b68ffc68f",
    "4e07408562bedb8b", "6b86b273ff34fce1", "d4735e3a265e16ee",
}

# In-world extreme taboo phrases that also incite an immediate riot/lynching
IN_WORLD_DEATH_PHRASES = {
    "KILL ALL", "STARVE THE POOR", "POISON THE WELL", "DEATH TO ALL",
}


def is_pamphlet_prohibited(text_str):
    """
    Checks if the player's typeset pamphlet contains prohibited words WITHOUT storing
    offensive strings in the codebase:
      1. Checks `better_profanity` if installed (`pip install better_profanity`).
      2. Checks an optional external `prohibited_words.txt` file if present.
      3. Checks one-way SHA-256 hashes of each word + in-world taboo phrases.
    """
    clean_upper = text_str.upper().strip()
    if not clean_upper:
        return False

    # 1. Check in-world death phrases
    for phrase in IN_WORLD_DEATH_PHRASES:
        if phrase in clean_upper:
            return True

    # 2. Check open-source `better_profanity` library if installed
    try:
        from better_profanity import profanity
        if profanity.contains_profanity(clean_upper):
            return True
    except ImportError:
        pass

    # 3. Check external `prohibited_words.txt` if the developer placed one in the directory
    ext_set = set()
    if os.path.exists("prohibited_words.txt"):
        try:
            with open("prohibited_words.txt", "r", encoding="utf-8") as f:
                ext_set = {line.strip().lower() for line in f if line.strip()}
        except OSError:
            pass

    # 4. Check word-by-word against external list and SHA-256 hashes
    words = [w.strip(".,!?;:-'\"") for w in clean_upper.lower().split()]
    for w in words:
        if not w:
            continue
        if w in ext_set:
            return True
        h_prefix = hashlib.sha256(w.encode("utf-8")).hexdigest()[:16]
        if h_prefix in PROHIBITED_SHA256_PREFIXES:
            return True

    return False


# =========================================================================
# 2. ASSEMBLING THE PORTABLE PRINTING PRESS FROM 3 PARTS
# =========================================================================
def try_assemble_printing_press(player):
    """
    Allows the player to build a functioning 'portable printing press' once they collect:
      1. 'oak press-frame'
      2. 'iron screw-spindle'
      3. 'lead type-case'
    """
    inv = player.get("inventory", [])
    needed = ["oak press-frame", "iron screw-spindle", "lead type-case"]
    missing = [item for item in needed if item not in inv]

    if missing:
        return False, (
            "To build a functioning **Portable Printing Press**, you still need: "
            + ", ".join(f"**{m.title()}**" for m in missing) + "."
        )

    for item in needed:
        inv.remove(item)
    inv.append("portable printing press")
    player, _ = advance_time(45, player)
    player["press_built"] = True
    return True, (
        "=== FUNCTIONING PRINTING PRESS ASSEMBLED (45m)! ===\n"
        "You mortise the **Oak Press-Frame**, thread the **Iron Screw-Spindle** into the cross-beam, "
        "and lay out the **Lead Type-Case** on the bench! You now own a **Portable Printing Press**—use it anytime to typeset and print your own pamphlets!"
    )


# =========================================================================
# 3. DRAG-AND-DROP TYPESETTING & PRESS ENGINE (MINIGAME_TYPESET)
# =========================================================================
TYPE_CASE_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?- ")
COMPOSING_SLOTS = 28  # 2 rows of 14 lead letter-blocks


def init_typeset_minigame(player):
    """Initializes the interactive Drag-and-Drop Lead Typesetting Pop-Out Window."""
    if "typeset_slots" not in player or len(player["typeset_slots"]) != COMPOSING_SLOTS:
        player["typeset_slots"] = [" "] * COMPOSING_SLOTS
    player["typeset_cursor"] = 0
    player["typeset_dragging_char"] = None
    player["typeset_inked"] = False
    player["typeset_printed_text"] = player.get("last_printed_pamphlet", "")

    # Side-mission prompt based on active track
    route = player.get("chapter_2_route", "")
    if route == "Stand for Union Official":
        hint = "Union Side-Mission: Typeset a slogan containing 'STRIKE', 'UNION', or 'FAIR WAGE' to rally the workers!"
    elif route == "Parvus: F.A.I.-C.N.T. Syndicate":
        hint = "F.A.I. Side-Mission: Typeset a revolutionary tract containing 'COMMUNE', 'LIBERTY', or 'GENERAL STRIKE'!"
    elif route == "Join Wallmaker Syndicate":
        hint = "Syndicate Side-Mission: Typeset a subversive decoy handbill containing 'BILLET', 'TAX', or 'KOKESHI'!"
    else:
        hint = "Drag lead letter-blocks from the Type-Case into the Brass Composing Stick (or type with your keyboard)!"

    player["typeset_feedback"] = (
        f"FLATBED COMPOSING BENCH: {hint} "
        "Right-click a slot to clear it. Then click [1. Ink Forme], [2. Pull Press Lever], and [3. Distribute Pamphlets]!"
    )
    return player, player["typeset_feedback"], "MINIGAME_TYPESET"


def _get_type_case_rects():
    """Returns a list of (char, pygame.Rect) for the 40 compartments in the upper wooden type-case."""
    rects = []
    # 4 rows of 10 compartments inside (85, 86, 630, 148)
    start_x, start_y = 92, 92
    cell_w, cell_h = 61, 34
    for idx, ch in enumerate(TYPE_CASE_CHARS):
        r = idx // 10
        c = idx % 10
        rect = pygame.Rect(start_x + c * cell_w, start_y + r * cell_h, cell_w - 4, cell_h - 4)
        rects.append((ch, rect))
    return rects


def _get_composing_slot_rects():
    """Returns a list of (slot_idx, pygame.Rect) for the 28 slots (2 rows of 14) in the Brass Composing Stick."""
    rects = []
    start_x, start_y = 92, 262
    slot_w, slot_h = 44, 38
    for idx in range(COMPOSING_SLOTS):
        r = idx // 14
        c = idx % 14
        rect = pygame.Rect(start_x + c * slot_w, start_y + r * (slot_h + 6), slot_w - 4, slot_h)
        rects.append((idx, rect))
    return rects


def handle_typeset_event(event, player):
    """
    Handles mouse drag-and-drop of lead letter-blocks AND direct keyboard typing
    when menu_state == 'MINIGAME_TYPESET'.
    """
    slots = player.setdefault("typeset_slots", [" "] * COMPOSING_SLOTS)

    if event.type == pygame.MOUSEBUTTONDOWN:
        mx, my = event.pos
        if event.button == 1:
            # Check if picking up a lead letter-block from the Wooden Type-Case
            for ch, r in _get_type_case_rects():
                if r.collidepoint(mx, my):
                    player["typeset_dragging_char"] = ch
                    return
            # Or clicking a Composing Stick slot to move the active cursor there
            for s_idx, r in _get_composing_slot_rects():
                if r.collidepoint(mx, my):
                    player["typeset_cursor"] = s_idx
                    return
        elif event.button == 3:
            # Right-click a Composing Stick slot to remove that letter-block!
            for s_idx, r in _get_composing_slot_rects():
                if r.collidepoint(mx, my):
                    slots[s_idx] = " "
                    player["typeset_cursor"] = s_idx
                    player["typeset_inked"] = False
                    return

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        drag_ch = player.get("typeset_dragging_char")
        if drag_ch is not None:
            mx, my = event.pos
            placed = False
            for s_idx, r in _get_composing_slot_rects():
                if r.collidepoint(mx, my):
                    slots[s_idx] = drag_ch
                    player["typeset_cursor"] = min(COMPOSING_SLOTS - 1, s_idx + 1)
                    player["typeset_inked"] = False
                    placed = True
                    break
            # If simple click on a type-case letter without dragging to a specific slot, insert at cursor!
            if not placed:
                for ch, r in _get_type_case_rects():
                    if r.collidepoint(mx, my) and ch == drag_ch:
                        cur = player.get("typeset_cursor", 0)
                        slots[cur] = drag_ch
                        player["typeset_cursor"] = (cur + 1) % COMPOSING_SLOTS
                        player["typeset_inked"] = False
                        break
            player["typeset_dragging_char"] = None

    elif event.type == pygame.KEYDOWN:
        cur = player.get("typeset_cursor", 0)
        if event.key == pygame.K_BACKSPACE:
            prev = max(0, cur - 1) if slots[cur] == " " else cur
            slots[prev] = " "
            player["typeset_cursor"] = prev
            player["typeset_inked"] = False
        elif event.key == pygame.K_LEFT:
            player["typeset_cursor"] = max(0, cur - 1)
        elif event.key == pygame.K_RIGHT:
            player["typeset_cursor"] = min(COMPOSING_SLOTS - 1, cur + 1)
        else:
            ch = event.unicode.upper()
            if ch in TYPE_CASE_CHARS:
                slots[cur] = ch
                player["typeset_cursor"] = min(COMPOSING_SLOTS - 1, cur + 1)
                player["typeset_inked"] = False


def typeset_button_action(action, player):
    """Handles the bottom action buttons in MINIGAME_TYPESET."""
    slots = player.setdefault("typeset_slots", [" "] * COMPOSING_SLOTS)
    composed_str = "".join(slots).strip()

    if action == "close":
        return player, "You cover the lead type-case and step back from the press.", "MAIN"

    if action == "clear":
        player["typeset_slots"] = [" "] * COMPOSING_SLOTS
        player["typeset_cursor"] = 0
        player["typeset_inked"] = False
        player["typeset_feedback"] = "You redistribute all lead letter-blocks back into the wooden type-case."
        return player, None, "MINIGAME_TYPESET"

    if action == "ink":
        if not composed_str:
            player["typeset_feedback"] = "Your brass composing stick is empty! Drag letter-blocks into the slots before inking."
            return player, None, "MINIGAME_TYPESET"
        inv = player.get("inventory", [])
        if "bottle of ink" not in inv:
            player["typeset_feedback"] = "Wait: You have no **Bottle of Ink** in your inventory! Buy ink from a shop or apothecary first."
            return player, None, "MINIGAME_TYPESET"
        player["typeset_inked"] = True
        player["typeset_feedback"] = f"You roll glossy lampblack ink across the lead type-blocks: \"{composed_str}\". Now click [2. Pull Press Lever]!"
        return player, None, "MINIGAME_TYPESET"

    if action == "pull_lever":
        if not composed_str:
            player["typeset_feedback"] = "Arrange lead letter-blocks in the composing stick first!"
            return player, None, "MINIGAME_TYPESET"
        if not player.get("typeset_inked"):
            player["typeset_feedback"] = "You must click [1. Ink Forme] to coat the lead type-blocks before pulling the press lever!"
            return player, None, "MINIGAME_TYPESET"
        inv = player.get("inventory", [])
        if "sheets of paper" not in inv:
            player["typeset_feedback"] = "You need **Sheets of Paper** in your inventory to print a pamphlet run!"
            return player, None, "MINIGAME_TYPESET"

        inv.remove("sheets of paper")
        if "printed pamphlet" not in inv:
            inv.append("printed pamphlet")
        player["last_printed_pamphlet"] = composed_str
        player["typeset_printed_text"] = composed_str
        player["typeset_inked"] = False
        player, _ = advance_time(20, player)
        player["typeset_feedback"] = (
            f"CRUNCH-THUMP! You pull the devil's-tail lever and peel a crisp broadsheet off the tympan: "
            f"\"{composed_str}\"! Click [3. Distribute Pamphlets in Street >>] to hand them out!"
        )
        return player, None, "MINIGAME_TYPESET"

    if action == "distribute":
        pamphlet = player.get("typeset_printed_text", "").strip()
        if not pamphlet:
            player["typeset_feedback"] = "Print a pamphlet first by Inking the Forme and Pulling the Press Lever!"
            return player, None, "MINIGAME_TYPESET"

        # 1. CENSORSHIP & PROHIBITED WORD CHECK -> INSTANT DEATH BY ANGRY MOB!
        if is_pamphlet_prohibited(pamphlet):
            return player, (
                "=================================================================\n"
                "   LYNCHED BY AN OUTRAGED MOB! (PROHIBITED PAMPHLET PRINTED!)    \n"
                "=================================================================\n"
                f"The moment you hand out your broadsheet reading **\"{pamphlet}\"**, a horrified gasp ripples through the street!\n"
                "Within seconds, enraged townsfolk, barge-crews, and guild apprentices storm your press with cobblestones and iron bars, "
                "smashing the oak frame to splinters and striking you down in the gutter!"
            ), "DEAD"

        # 2. CHECK FACTION SIDE-MISSION KEYWORDS (UNION, F.A.I., WALLMAKER SYNDICATE)
        up = pamphlet.upper()
        route = player.get("chapter_2_route", "")
        bonus_log = ""

        if any(w in up for w in ("STRIKE", "UNION", "WAGE", "SOLIDARITY", "WORKERS")) and not player.get("pamphlet_union_done"):
            player["pamphlet_union_done"] = True
            modify_faction(player, "faction_union", 2)
            player["position_strength"] = min(100, player.get("position_strength", 0) + 12)
            player["silver"] += 20
            bonus_log = (
                "\n\n*** UNION PAMPHLETEER SIDE-MISSION COMPLETE (+2 Union Faction, +12% Position Strength, +20s Strike Donation)! ***\n"
                "Cheering farmhands and dockers pass your broadsheet from hand to hand around the picket braziers!"
            )
        elif any(w in up for w in ("COMMUNE", "LIBERTY", "FREE", "ANARCHY", "REVOLT")) and not player.get("pamphlet_fai_done"):
            player["pamphlet_fai_done"] = True
            modify_faction(player, "faction_union", 2)
            player["position_strength"] = min(100, player.get("position_strength", 0) + 12)
            player["stealth"] = player.get("stealth", 0) + 1
            player["exposure_tells"] = max(0, player.get("exposure_tells", 0) - 1)
            bonus_log = (
                "\n\n*** F.A.I.-C.N.T. AGITPROP SIDE-MISSION COMPLETE (+12% Position Strength, +1 Stealth, +2 Union)! ***\n"
                "Your revolutionary broadsheet ignites the rope-walks and quaysides!"
            )
        elif any(w in up for w in ("BILLET", "TAX", "KOKESHI", "WALL", "MARSHAL")) and not player.get("pamphlet_syndicate_done"):
            player["pamphlet_syndicate_done"] = True
            modify_faction(player, "faction_wallmakers", 2)
            player["position_strength"] = min(100, player.get("position_strength", 0) + 12)
            player["silver"] += 25
            bonus_log = (
                "\n\n*** SYNDICATE DISINFORMATION SIDE-MISSION COMPLETE (+2 Wallmakers, +12% Position Strength, +25s Stipend)! ***\n"
                "Your cleverly worded broadsheet sows confusion among the Watch while advancing the Syndicate's shadow agenda!"
            )
        if not player.get("pamphlet_general_done"):
            player["pamphlet_general_done"] = True
            player["reputation"] = player.get("reputation", 0) + 1
            player["influence"] = player.get("influence", 0) + 1
            player["exposure_tells"] = max(0, player.get("exposure_tells", 0) - 1)
            player["position_strength"] = min(100, player.get("position_strength", 0) + 8)
            bonus_log += (
                "\n*** FLATBED PRINTING PRESS OPERATED (+1 Reputation, +1 Influence, +8% Position Strength)! ***"
            )

        return player, (
            f"=== PAMPHLETS DISTRIBUTED ACROSS TOWN! ===\n"
            f"Headline Printed: **\"{pamphlet}\"**\n"
            f"Passersby gather on the street corners reading your freshly inked broadsheet aloud!{bonus_log}"
        ), "MAIN"

    return player, None, "MINIGAME_TYPESET"


def draw_typeset_ui(screen, player, font, font_bold, mouse_pos):
    """Renders the 680x480 Drag-and-Drop Press Window styled after 1886 Anarchist Broadside Newspapers."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 195))
    screen.blit(overlay, (0, 0))

    NEWS_BG = (248, 245, 238)
    INK_BLACK = (20, 20, 22)
    TATE_RED = (168, 50, 35)
    BRASS_GOLD = (185, 140, 45)
    LEAD_GREY = (62, 66, 74)

    panel = pygame.Rect(60, 25, 680, 525)
    pygame.draw.rect(screen, NEWS_BG, panel, border_radius=10)
    pygame.draw.rect(screen, INK_BLACK, panel, width=3, border_radius=10)

    # 1. Authentic 1886 Masthead Header
    mast_font = pygame.font.Font(None, 42)
    sub_font = pygame.font.Font(None, 18)
    
    # Title
    title_surf = mast_font.render("DTESSERA TRIBUNE", True, INK_BLACK)
    screen.blit(title_surf, (400 - title_surf.get_width() // 2, 34))

    # Subtitle
    sub_surf = sub_font.render("A JOURNAL OF RADICAL SOVEREIGNTY & WORKERS' RIGHTS", True, INK_BLACK)
    screen.blit(sub_surf, (400 - sub_surf.get_width() // 2, 70))

    # Thin Double Rules
    pygame.draw.line(screen, INK_BLACK, (85, 88), (715, 88), 2)
    pygame.draw.line(screen, INK_BLACK, (85, 91), (715, 91), 1)

    # Vol / Date Row
    meta_surf = pygame.font.Font(None, 15).render("VOL. II. — No. 4.        OCTOBER, 1886.        MONTHLY; ONE COPPER SOU.", True, (70, 70, 75))
    screen.blit(meta_surf, (400 - meta_surf.get_width() // 2, 95))
    pygame.draw.line(screen, INK_BLACK, (85, 110), (715, 95), 1)

    # 2. Upper Wooden California Job Case (Lead Type Blocks)
    case_box = pygame.Rect(85, 114, 630, 136)
    pygame.draw.rect(screen, (85, 58, 34), case_box, border_radius=6)
    pygame.draw.rect(screen, INK_BLACK, case_box, width=1, border_radius=6)

    block_font = pygame.font.Font(None, 20)
    for ch, r in _get_type_case_rects():
        is_hover = r.collidepoint(mouse_pos)
        # Shift rect down to align with masthead y=114
        r_shifted = r.move(0, 26)
        pygame.draw.rect(screen, (82, 88, 98) if is_hover else LEAD_GREY, r_shifted, border_radius=3)
        pygame.draw.rect(screen, BRASS_GOLD if is_hover else (35, 38, 42), r_shifted, width=1, border_radius=3)
        disp = "SPC" if ch == " " else ch
        s = block_font.render(disp, True, (240, 240, 240))
        screen.blit(s, s.get_rect(center=r_shifted.center))

    # 3. Middle Brass Composing Stick (28 Slots)
    stick_box = pygame.Rect(85, 258, 630, 102)
    pygame.draw.rect(screen, (45, 42, 35), stick_box, border_radius=6)
    pygame.draw.rect(screen, BRASS_GOLD, stick_box, width=2, border_radius=6)

    slots = player.get("typeset_slots", [" "] * COMPOSING_SLOTS)
    cur_idx = player.get("typeset_cursor", 0)
    inked = player.get("typeset_inked", False)
    ink_label = "[TYPE INKED]" if inked else "[DRY TYPE]"

    screen.blit(pygame.font.Font(None, 15).render(f"COMPOSING STICK (28 Slots)  {ink_label}", True, (255, 215, 115)), (95, 263))

    for s_idx, r in _get_composing_slot_rects():
        ch = slots[s_idx]
        is_cur = (s_idx == cur_idx)
        r_shifted = r.move(0, 16)
        bg = (22, 22, 25) if (inked and ch != " ") else ((75, 80, 90) if ch != " " else (32, 30, 26))
        bd = (255, 215, 80) if is_cur else (BRASS_GOLD if ch != " " else (85, 80, 70))
        pygame.draw.rect(screen, bg, r_shifted, border_radius=3)
        pygame.draw.rect(screen, bd, r_shifted, width=2 if is_cur else 1, border_radius=3)
        if ch != " ":
            s = block_font.render(ch, True, (250, 248, 240))
            screen.blit(s, s.get_rect(center=r_shifted.center))

    # 4. Status & Feedback Box
    fb_box = pygame.Rect(85, 372, 630, 52)
    pygame.draw.rect(screen, (235, 230, 220), fb_box, border_radius=6)
    pygame.draw.rect(screen, INK_BLACK, fb_box, width=1, border_radius=6)
    draw_fitted_text(screen, player.get("typeset_feedback", ""), fb_box.inflate(-12, -6), INK_BLACK, max_lines=2)

    # Floating Dragging Letter Block
    drag_ch = player.get("typeset_dragging_char")
    if drag_ch is not None:
        d_rect = pygame.Rect(mouse_pos[0] - 22, mouse_pos[1] - 18, 44, 36)
        pygame.draw.rect(screen, (95, 102, 115), d_rect, border_radius=4)
        pygame.draw.rect(screen, (255, 220, 90), d_rect, width=2, border_radius=4)
        lbl = "SPC" if drag_ch == " " else drag_ch
        s = font_bold.render(lbl, True, (255, 255, 255))
        screen.blit(s, s.get_rect(center=d_rect.center))
        
