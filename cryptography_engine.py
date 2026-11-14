import random
import pygame
import printing_press_engine
import game_data as db
from mechanics import modify_faction, advance_time
from ui_components import draw_fitted_text


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# =========================================================================
# 1. CONCENTRIC BRASS CODEWHEEL (MINIGAME_CODEWHEEL)
# =========================================================================
CODEWHEEL_MESSAGES = [
    {
        "id": "bandoka",
        "title": "BANDOKA'S BRASS CIPHER CYLINDER",
        "plaintext": "WATCH POST AT SIX TWENTY ONE IS UNDERMANNED STRIKE BEFORE DAWN",
        "target_shift": 7,  # Shift 7 ('H' aligns with 'A')
        "reward_flag": "bandoka_cipher_decoded",
        "reward_silver": 20,
        "reward_text": (
            "=== BANDOKA'S CIPHER DECODED (+20 Silver Value, +1 Stealth)! ===\n"
            "\"WATCH POST AT THE NORTHERN FRONTIER FORK IS UNDERMANNED — STRIKE BEFORE DAWN.\"\n"
            "This proves Bandoka was transmitting Frontier Watchpost patrol schedules to Castle Laydere! "
            "You can present this to Captain Wealdhere or Lieutenant Beornraed—or use it yourself!"
        ),
    },
    {
        "id": "parvus_customs",
        "title": "INTERCEPTED PARVUS HARBOUR CIPHER",
        "plaintext": "KOKESHI MUSKETS HIDDEN BEHIND FALSE BULKHEAD ON BRIG CORMORANT",
        "target_shift": 14,
        "reward_flag": "parvus_ships_inspected",
        "reward_silver": 25,
        "reward_text": (
            "=== HARBOUR CIPHER DECODED (+25 Silver)! ===\n"
            "\"KOKESHI MUSKETS HIDDEN BEHIND FALSE BULKHEAD ON BRIG CORMORANT.\"\n"
            "You now have ironclad cryptographic proof of the contraband arms cache!"
        ),
    },
]


def _caesar_shift_text(text, shift):
    out = []
    for ch in text.upper():
        if ch in ALPHABET:
            idx = (ALPHABET.index(ch) + shift) % 26
            out.append(ALPHABET[idx])
        else:
            out.append(ch)
    return "".join(out)


def init_codewheel_minigame(player, msg_index=None):
    """Initializes the Concentric Brass Codewheel Pop-Out Window."""
    if msg_index is None:
        msg_index = 0 if not player.get("bandoka_cipher_decoded") else 1
    spec = CODEWHEEL_MESSAGES[msg_index % len(CODEWHEEL_MESSAGES)]

    player["cw_index"] = msg_index % len(CODEWHEEL_MESSAGES)
    player["cw_current_shift"] = random.choice([i for i in range(1, 26) if i != spec["target_shift"]])
    player["cw_solved"] = False
    player["cw_feedback"] = (
        "Rotate the inner brass letter-ring Left or Right until the scrambled ciphertext aligns into readable English, then click [Lock In Decoded Message]!"
    )
    return player, player["cw_feedback"], "MINIGAME_CODEWHEEL"


def codewheel_action(action, player):
    spec = CODEWHEEL_MESSAGES[player.get("cw_index", 0)]
    if action == "close":
        return player, "You slip the brass codewheel back into your coat.", "MAIN"

    if action == "left":
        player["cw_current_shift"] = (player.get("cw_current_shift", 0) - 1) % 26
    elif action == "right":
        player["cw_current_shift"] = (player.get("cw_current_shift", 0) + 1) % 26
    elif action == "submit":
        if player.get("cw_current_shift", 0) == spec["target_shift"]:
            player["cw_solved"] = True
            if not player.get(spec["reward_flag"]):
                player[spec["reward_flag"]] = True
                player["silver"] += spec["reward_silver"]
                player["stealth"] = player.get("stealth", 0) + 1
            return player, spec["reward_text"], "MAIN"
        else:
            player["cw_feedback"] = "The aligned letters are still gibberish! Keep rotating the inner brass ring until English words appear."
    return player, None, "MINIGAME_CODEWHEEL"


def draw_codewheel_ui(screen, player, font, font_bold, mouse_pos):
    """Renders the 680x480 Concentric Brass Codewheel Pop-Out Window."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    BRASS_GOLD = (185, 140, 45)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    spec = CODEWHEEL_MESSAGES[player.get("cw_index", 0)]
    cur_shift = player.get("cw_current_shift", 0)
    target_shift = spec["target_shift"]

    # Ciphertext is encoded with -target_shift so shifting by +cur_shift decodes it when cur_shift == target_shift!
    raw_cipher = _caesar_shift_text(spec["plaintext"], -target_shift)
    live_preview = _caesar_shift_text(raw_cipher, cur_shift)

    title = font_bold.render(f"ALBERTI BRASS CODEWHEEL — {spec['title']}", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    # Draw the Outer & Inner Brass Ring Alignment Strip
    ring_box = pygame.Rect(85, 84, 630, 74)
    pygame.draw.rect(screen, (42, 38, 30), ring_box, border_radius=8)
    pygame.draw.rect(screen, BRASS_GOLD, ring_box, width=3, border_radius=8)

    mono = pygame.font.Font(None, 22)
    outer_str = "OUTER RING:  " + " ".join(ALPHABET)
    inner_alpha = [ALPHABET[(i + cur_shift) % 26] for i in range(26)]
    inner_str = "INNER RING:  " + " ".join(inner_alpha)

    screen.blit(mono.render(outer_str, True, DIAL_CREAM), (102, 96))
    screen.blit(mono.render(inner_str, True, (255, 215, 90)), (102, 126))

    # Intercepted vs Live Decoded Slate
    msg_box = pygame.Rect(85, 170, 630, 118)
    pygame.draw.rect(screen, (252, 248, 238), msg_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, msg_box, width=2, border_radius=8)

    screen.blit(font_bold.render(f"Intercepted Ciphertext (Current Ring Offset: +{cur_shift}/26):", True, TATE_RED), (100, 178))
    draw_fitted_text(screen, raw_cipher, pygame.Rect(100, 200, 600, 28), (110, 105, 100), max_lines=1)

    screen.blit(font_bold.render("Live Inner-Ring Readout:", True, (35, 120, 55) if cur_shift == target_shift else CLOCK_BLACK), (100, 230))
    draw_fitted_text(screen, live_preview, pygame.Rect(100, 252, 600, 32), (35, 120, 55) if cur_shift == target_shift else CLOCK_BLACK, bold=True, max_lines=2)

    fb_box = pygame.Rect(85, 298, 630, 52)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    draw_fitted_text(screen, player.get("cw_feedback", ""), fb_box.inflate(-14, -6), DIAL_CREAM, max_lines=2)


# =========================================================================
# 2. CRYPTONOMICON "PONTIFEX" (SOLITAIRE) DECK-OF-CARDS CIPHER
# =========================================================================
def init_pontifex_minigame(player):
    """
    Initializes Neal Stephenson's Cryptonomicon 'Solitaire / Pontifex' 54-card cipher!
    Uses a 10-card mini-packet visualization (cards 1..8 + Joker A + Joker B) so the player
    can physically see the 4 Solitaire steps execute on screen!
    """
    # Packet: values 1..8, 9 = Joker A ('JA'), 10 = Joker B ('JB')
    player["pf_deck"] = [3, 9, 6, 1, 10, 4, 8, 2, 5, 7]
    player["pf_step"] = 0  # 0: Move JA, 1: Move JB, 2: Triple Cut, 3: Count Cut, 4: Extract Keystream
    player["pf_ciphertext"] = "W V L H J"   # Plaintext: S P I E S
    player["pf_feedback"] = (
        "CRYPTONOMICON 'PONTIFEX' CARD CIPHER: Execute the 4 Solitaire Deck Operations in sequence "
        "(1. Move Joker A -> 2. Move Joker B -> 3. Triple Cut -> 4. Count Cut) to generate the keystream and decrypt the spy dispatch!"
    )
    return player, player["pf_feedback"], "MINIGAME_PONTIFEX"


def pontifex_action(action, player):
    if action == "close":
        return player, "You square the deck of cards and slip it back into your pocket.", "MAIN"

    deck = list(player.get("pf_deck", [3, 9, 6, 1, 10, 4, 8, 2, 5, 7]))
    step = player.get("pf_step", 0)

    if action == "step_ja" and step == 0:
        idx = deck.index(9)
        swap_idx = (idx + 1) % len(deck)
        deck[idx], deck[swap_idx] = deck[swap_idx], deck[idx]
        player["pf_deck"] = deck
        player["pf_step"] = 1
        player["pf_feedback"] = "Step 1 Complete: Moved **Joker A (JA)** down 1 position! Next: Click [2. Move Joker B Down 2 Cards]."

    elif action == "step_jb" and step == 1:
        for _ in range(2):
            idx = deck.index(10)
            swap_idx = (idx + 1) % len(deck)
            deck[idx], deck[swap_idx] = deck[swap_idx], deck[idx]
        player["pf_deck"] = deck
        player["pf_step"] = 2
        player["pf_feedback"] = "Step 2 Complete: Moved **Joker B (JB)** down 2 positions! Next: Click [3. Perform Triple Cut Around Jokers]."

    elif action == "step_triple" and step == 2:
        ia, ib = deck.index(9), deck.index(10)
        top_j, bot_j = min(ia, ib), max(ia, ib)
        above = deck[:top_j]
        middle = deck[top_j:bot_j + 1]
        below = deck[bot_j + 1:]
        player["pf_deck"] = below + middle + above
        player["pf_step"] = 3
        player["pf_feedback"] = "Step 3 Complete: **Triple Cut** swapped the packets outside the two Jokers! Next: Click [4. Perform Bottom-Card Count Cut]."

    elif action == "step_count" and step == 3:
        bot_val = min(8, deck[-1])
        cut_n = bot_val % (len(deck) - 1)
        player["pf_deck"] = deck[cut_n:-1] + deck[:cut_n] + [deck[-1]]
        player["pf_step"] = 4
        player["pf_feedback"] = (
            "Step 4 Complete: **Count Cut** complete! Keystream generated: [4, 6, 3, 3, 17] -> "
            "Ciphertext 'W V L H J' minus Keystream = **'S P I E S — PAYROLL AT OLD PATH WAYSTATION'**! Click [Claim Decoded Dispatch >>]!"
        )

    elif action == "claim" and step >= 4:
        if not player.get("pontifex_solved"):
            player["pontifex_solved"] = True
            player["silver"] += 25
            player["stealth"] = player.get("stealth", 0) + 1
            player["el_waystation_tube_found"] = True
        return player, (
            "=== PONTIFEX DECK CIPHER SOLVED (+25 Silver, +1 Stealth)! ===\n"
            "Using the *Cryptonomicon* Solitaire algorithm, your deck of cards decodes the dead-drop without leaving a single written key behind!"
        ), "MAIN"
    else:
        player["pf_feedback"] = f"Follow the exact Solitaire sequence! You are currently on Step {step + 1}."

    return player, None, "MINIGAME_PONTIFEX"


def draw_pontifex_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the 680x480 Cryptonomicon Pontifex Playing-Card Cipher Window."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("CRYPTONOMICON 'PONTIFEX' (SOLITAIRE) DECK CIPHER", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    # Draw the 10 Playing Cards in a Row
    deck = player.get("pf_deck", [3, 9, 6, 1, 10, 4, 8, 2, 5, 7])
    for i, c_val in enumerate(deck):
        cx = 85 + i * 63
        c_rect = pygame.Rect(cx, 92, 56, 82)
        is_joker = c_val in (9, 10)
        bg = (255, 238, 195) if is_joker else (252, 250, 245)
        bd = TATE_RED if is_joker else CLOCK_BLACK
        pygame.draw.rect(screen, bg, c_rect, border_radius=6)
        pygame.draw.rect(screen, bd, c_rect, width=2, border_radius=6)

        lbl = "J-A" if c_val == 9 else ("J-B" if c_val == 10 else f"{c_val}♠")
        c_surf = font_bold.render(lbl, True, TATE_RED if is_joker else CLOCK_BLACK)
        screen.blit(c_surf, c_surf.get_rect(center=c_rect.center))

    step = player.get("pf_step", 0)
    plain = "S P I E S  (DECODED!)" if step >= 4 else "? ? ? ? ?"
    info_box = pygame.Rect(85, 188, 630, 82)
    pygame.draw.rect(screen, (252, 248, 238), info_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, info_box, width=2, border_radius=8)

    screen.blit(font_bold.render(f"Intercepted Cipher:  W  V  L  H  J   --->   Output:  {plain}", True, CLOCK_BLACK), (105, 202))
    screen.blit(font.render(f"Solitaire Algorithm Progress: Step {min(4, step)}/4 Completed", True, TATE_RED), (105, 234))

    fb_box = pygame.Rect(85, 280, 630, 56)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    draw_fitted_text(screen, player.get("pf_feedback", ""), fb_box.inflate(-14, -6), DIAL_CREAM, max_lines=2)


# =========================================================================
# 3. GCHQ PUZZLE BOOK CHALLENGES & REGIONAL POSTBOXES (MINIGAME_GCHQ)
# =========================================================================
GCHQ_PUZZLES = [
    {
        "title": "GCHQ PUZZLE #1: THE POLYBIUS PRISON KNOCK-CODE",
        "prompt": (
            "Found inside the Murum Postbox: A 5x5 Polybius Grid (A-Z, I/J shared) where Row 1 = A B C D E, Row 2 = F G H I K, Row 3 = L M N O P, Row 4 = Q R S T U, Row 5 = V W X Y Z.\n"
            "Decode the tapped coordinates:  (2,1) - (3,3) - (3,4) - (3,1) - (1,4)"
        ),
        "options": [
            ("F - N - O - L - D  ('FNOLD')", False),
            ("F - L - O - O - D  ('FLOOD' — Warn the Sluice-Gate!)", True),
            ("G - M - P - M - E  ('GMPME')", False),
        ],
        "correct_note": "Note: (2,1)=F, (3,1)=L, (3,4)=O, (3,4)=O, (1,4)=D -> 'FLOOD'!",
    },
    {
        "title": "GCHQ PUZZLE #2: THE FIRST-LETTER STEGANOGRAPHY DISPATCH",
        "prompt": (
            "Found inside the Fluvius Postbox: An innocent-looking letter from a 'wine merchant':\n"
            "\"**C**asks **O**f **R**ich **B**rumaire **A**le **N**earby — **B**ring **R**opes **I**mmediately **B**efore **E**vening.\"\n"
            "What hidden warning is concealed by the acrostic (initial letters)?"
        ),
        "options": [
            ("CORBAN BRIBE (Wagon-Boss Corban is bribing the gate!)", True),
            ("CASTLE LAYDERE ATTACKS AT DAWN", False),
            ("BUY WINE AT THE BARGE AND ANCHOR", False),
        ],
        "correct_note": "Taking the first letter of each word spells C-O-R-B-A-N  B-R-I-B-E!",
    },
    {
        "title": "GCHQ PUZZLE #3: THE REPUBLICAN DECIMAL SEQUENCE",
        "prompt": (
            "Found inside the Parvus Postbox: A GCHQ lateral-thinking letter sequence:\n"
            "What are the next two letters in this sequence?\n"
            "   V  —  B  —  F  —  N  —  P  —  V  —  G  —  ?  —  ?"
        ),
        "options": [
            ("F — P  (Floréal, Prairial — the months of the Republican Calendar!)", True),
            ("H — I  (Alphabetical skip)", False),
            ("M — T  (Messidor, Thermidor)", False),
        ],
        "correct_note": "Each letter is the initial of the 12 Republican Calendar months (Vendémiaire, Brumaire, Frimaire, Nivôse, Pluviôse, Ventôse, Germinal -> Floréal, Prairial)!",
    },
]


def init_gchq_puzzle(player, p_idx=None):
    if p_idx is None:
        solved = player.get("gchq_solved_list", [])
        remaining = [i for i in range(len(GCHQ_PUZZLES)) if i not in solved]
        p_idx = remaining[0] if remaining else random.randint(0, len(GCHQ_PUZZLES) - 1)

    player["gchq_idx"] = p_idx
    player["gchq_feedback"] = "Examine the intercepted postbox dispatch carefully and select the correct cryptanalytic deduction:"
    return player, player["gchq_feedback"], "MINIGAME_GCHQ"


def gchq_action(opt_idx, player):
    if opt_idx == -1:
        return player, "You close the postbox dispatch.", "MAIN"

    idx = player.get("gchq_idx", 0)
    puz = GCHQ_PUZZLES[idx]
    label, is_correct = puz["options"][opt_idx]

    if is_correct:
        solved = player.setdefault("gchq_solved_list", [])
        if idx not in solved:
            solved.append(idx)
            player["silver"] += 20
            player["influence"] = player.get("influence", 0) + 1
            return player, (
                f"=== GCHQ CRYPTOGRAM SOLVED (+20 Silver, +1 Influence)! ===\n"
                f"{puz['correct_note']}"
            ), "MAIN"
        return player, f"Correct! {puz['correct_note']}", "MAIN"
    else:
        player["gchq_feedback"] = f"'{label}' does not match the cipher pattern—look closely at the initial letters or coordinates!"
        return player, None, "MINIGAME_GCHQ"


def draw_gchq_ui(screen, player, font, font_bold, mouse_pos):
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    puz = GCHQ_PUZZLES[player.get("gchq_idx", 0)]
    title = font_bold.render(puz["title"], True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 54))

    p_box = pygame.Rect(85, 88, 630, 155)
    pygame.draw.rect(screen, (252, 248, 238), p_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, p_box, width=2, border_radius=8)
    draw_fitted_text(screen, puz["prompt"], p_box.inflate(-18, -14), CLOCK_BLACK, max_lines=5)

    fb_box = pygame.Rect(85, 256, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    draw_fitted_text(screen, player.get("gchq_feedback", ""), fb_box.inflate(-14, -8), DIAL_CREAM, max_lines=2)


# =========================================================================
# 4. NON-FIGHTING ITEMS: PRINTING PRESS, KNOTTING & FOREST DRUM CIRCLE
# =========================================================================
def use_non_fighting_item(item_name, player, world_map):
    """
    Handles Use -> [Codewheel, Bandoka's Cipher, Deck of Cards, Portable Printing Press,
    Spool of Thread, Woodland Drum, Guard Uniform, Kokeshi Doll].
    Returns (handled_bool, next_state, log_message).
    """
    inv = player.get("inventory", [])
    pos = (player.get("x", 8), player.get("y", 14))
    room = world_map.get(pos) if world_map else None
    reg = room.region if room else ""

    # 1. Brass Codewheel or Bandoka's Cipher
    if item_name in ("codewheel", "bandoka's cipher"):
        _, log, st = init_codewheel_minigame(player)
        return True, st, log

    # 2. Deck of Cards (Cryptonomicon Pontifex Cipher)
    if item_name == "deck of cards":
        _, log, st = init_pontifex_minigame(player)
        return True, st, log

    # 3. Portable Printing Press (Assemble from 3 parts, or open the 1886 Typesetting Bench)
    if item_name in ("oak press-frame", "iron screw-spindle", "lead type-case"):
        _, msg = printing_press_engine.try_assemble_printing_press(player)
        return True, "MAIN", msg

    if item_name == "portable printing press":
        _, msg, st = printing_press_engine.init_typeset_minigame(player)
        if "sheets of paper" not in inv or "bottle of ink" not in inv:
            msg += (
                "\n\n*** Note: You can arrange the lead type-blocks now, but you will need "
                "both **Sheets of Paper** and a **Bottle of Ink** in your pack to ink and pull the lever! ***"
            )
        return True, st, msg
    # 4. Knotting (Spool of Thread + Rope -> Warm Clothes / Climbing Harness)
    if item_name == "spool of thread":
        player, _ = advance_time(20, player)
        if "warm winter coat" not in inv:
            inv.append("warm winter coat")
            inv.remove("spool of thread")
            return True, "MAIN", (
                "=== KNOTTING & TAILORING COMPLETE! ===\n"
                "Using double-hitch sailor's knotting with your **Spool of Thread** and woollen lining, you stitch and quilt a **Warm Winter Coat** to protect against freezing temperatures!"
            )
        else:
            player["health"] = min(player.get("max_health", 10), player.get("health", 10) + 2)
            return True, "MAIN", "You mend the seams of your travel gear and knot a spare cordage sling (+2 Health)."

    # 5. The Woodland Drum (Forest Animals Love a Drum Circle!)
    if item_name == "woodland drum":
        player, _ = advance_time(25, player)
        if "Forest" in reg or "Glade" in reg:
            modify_faction(player, "faction_communards", 2)
            modify_faction(player, "faction_vanguardists", 1)
            player["health"] = player.get("max_health", 10)
            player["foraging_lore_learned"] = True
            if "cobnuts" not in inv:
                inv.append("cobnuts")
            return True, "MAIN", (
                "=== THE LIGNUM FOREST DRUM CIRCLE (+2 Communards, +1 Vanguardists, Full Health, +Cobnuts)! ===\n"
                "As you tap a warm, steady heartbeat on your **Woodland Drum**, the canopy rustles! "
                "Red squirrels, badgers, and antlered stags step peacefully into the clearing, swaying to the rhythm and leaving a pile of sweet **Cobnuts** at your feet!"
            )
        else:
            player["charisma"] = player.get("charisma", 0) + (1 if not player.get("drum_practiced") else 0)
            player["drum_practiced"] = True
            return True, "MAIN", (
                "You beat a lively cadence on your **Woodland Drum**! (Tip: Try playing a drum circle beneath the trees of **Lignum Forest**—the forest animals love a drum circle!)"
            )

    # 6. Guard Uniform & Kokeshi Doll
    if item_name == "guard uniform":
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        player["disguised_as_guard"] = True
        return True, "MAIN", (
            "You pull on the **Guard Uniform** tabard and buckle the brass Watch baldric across your chest. "
            "Standard Watch patrols and gate sentries now salute you as one of their own!"
        )

    if item_name == "kokeshi doll":
        player["kokeshi_recognized"] = True
        modify_faction(player, "faction_wallmakers", 2)
        return True, "MAIN", (
            "Displaying the secret lathe-rings on the **Kokeshi Doll** (+2 Wallmaker Syndicate standing) marks you as an initiated operative of the shadow syndicate!"
        )

    return False, "MAIN", ""
