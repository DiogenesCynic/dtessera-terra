"""
ch3_tutorial_book.py
--------------------
Provides the Chapter 3 Learning & Reference Suite:
1. The Complete 4-Tab War Rulebook ('CH3_RULEBOOK_MODAL') with an
   interactive 7-Faction Almanac and carved Meeple illustrations.
2. The 7-Faction Heavy-Handed Guided Tutorial ('CH3_TUTORIAL_SELECT' and
   live 10-step spotlight overlay) with safe campaign snapshotting.
"""

import copy
import pygame

import ch3_board_renderer
import ch3_combat_engine
import ch3_war_engine
import ui_renderer
from ui_components import draw_fitted_text

# --- SHARED PALETTE CONSTANTS ---
TATE_RED = (168, 50, 35)
DIAL_CREAM = (244, 239, 225)
CLOCK_BLACK = (28, 26, 24)
GOLD_ACCENT = (195, 148, 48)
GOLD_BRIGHT = (250, 215, 85)
OAK_DARK = (46, 33, 25)
OAK_MID = (66, 48, 36)
EQUIPPED_GREEN = (45, 125, 68)

_TUTORIAL_CAMPAIGN_BACKUP = None

RULEBOOK_TABS = [
    ("TAB_HEGEMONY", "I. 100-Pt Hegemony"),
    ("TAB_PHASES", "II. Daily Turn"),
    ("TAB_RANKS", "III. Ranks & Coups"),
    ("TAB_FACTIONS", "IV. 7 Factions"),
]

FACTION_ORDER = [
    "Union",
    "Kokeshi",
    "Laydere",
    "Ragmore",
    "FAI",
    "Communards",
    "Vanguardists",
]

FACTION_DOSSIERS = {
    "Union": {
        "capital": "Fluvius Town Guildhall",
        "leader": "Organiser Joyinsorrow & Representative Truthtale",
        "morning_tip": (
            "Slot matched pairs into Build Defences to erect wooden "
            "Barricades (+2 Hegemony Pts per ruled clearing), and deploy "
            "your Portable Printing Press for +4 Fairness Sympathy."
        ),
        "afternoon_tip": (
            "March in compact columns along the Fluvius and Murum farm "
            "corridors to link your barricaded towns."
        ),
        "evening_tip": (
            "• Barricade Lock: Any matching pair in your dice pool upgrades "
            "your lowest die to a 6.\n"
            "• Swarm Numbers: Having at least as many dice as the defender "
            "adds +1 bonus militia die (3-6)."
        ),
    },
    "Kokeshi": {
        "capital": "Murum Town Citadel",
        "leader": "The Diewell & Factor Hopestill",
        "morning_tip": (
            "Maintain high Silver reserves in your Syndicate treasury to "
            "fund daytime bribes and evening sabotage."
        ),
        "afternoon_tip": (
            "Use Wealth and road networks to outflank heavily armoured "
            "castellan columns without fighting fair."
        ),
        "evening_tip": (
            "• Underhand Sabotage (-10s): Shatters and removes the "
            "Defender's highest die before combat resolves.\n"
            "• Bribe Unit (-15s): Buys off an enemy battalion—sliding their "
            "highest die across the table into your attack pool!"
        ),
    },
    "Laydere": {
        "capital": "Castle Laydere Keep",
        "leader": "Castellan Eormenhild",
        "morning_tip": (
            "Muster disciplined heavy halberdiers and keep your supply "
            "lines locked with a 5 or 6 die."
        ),
        "afternoon_tip": (
            "• Military Expertise: Marching along The New Road costs only "
            "0.5 MP per clearing, letting your columns strike deep."
        ),
        "evening_tip": (
            "• Polearm Steel: Re-rolls all 1s and 2s in your attack pool "
            "into heavy 4-6 strikes.\n"
            "• Shield-Wall Discipline: Adds +2 to your lowest die AND "
            "automatically wins all tied battles!"
        ),
    },
    "Ragmore": {
        "capital": "Castle Ragmore Keep",
        "leader": "Castellan Hrothgar",
        "morning_tip": (
            "Build large dice pools to maximise the chance of rolling 6s "
            "for your longbowmen at dusk."
        ),
        "afternoon_tip": (
            "• Military Expertise: Marching along The New Road costs only "
            "0.5 MP per clearing. Seize high-altitude ridges."
        ),
        "evening_tip": (
            "• Longbow Volley: Spend a '6' from your pool to snipe and "
            "shatter the Defender's highest die.\n"
            "• Range Sighting: Re-rolls your lowest die into a 4-6 strike."
        ),
    },
    "FAI": {
        "capital": "Parvus Port Bastion",
        "leader": "Agitator Speaktruth",
        "morning_tip": (
            "Deploy Chapter 2 Codewheels and Printing Presses at dawn to "
            "accumulate Tactical Advantage Tokens."
        ),
        "afternoon_tip": (
            "Strike enemy supply corridors and coastal strongholds from "
            "Parvus Port."
        ),
        "evening_tip": (
            "• Guerrilla Strike: Adds +1 ambush die (4-6) and guarantees "
            "your battalions withdraw safely to Parvus if repelled.\n"
            "• Underhand Sap (-10s / Relic): Shatters the Defender's "
            "highest die."
        ),
    },
    "Communards": {
        "capital": "The Deep Glade Sanctuary",
        "leader": "Rain in the Face",
        "morning_tip": (
            "Cultivate Nature Sympathy so enemy conscripts willingly "
            "join your commune at dusk."
        ),
        "afternoon_tip": (
            "• Fog of War: Marching through Lignum Forest costs only "
            "1 MP (instead of 2 MP)."
        ),
        "evening_tip": (
            "• Peaceful Praxis (-4 Sympathy): Converts an enemy die "
            "across the table into your attack pool!\n"
            "• Canopy Mist: Woodland fog nullifies any enemy die of 5 or 6."
        ),
    },
    "Vanguardists": {
        "capital": "The Old Path Waystation",
        "leader": "The Black Hills & Black Dog",
        "morning_tip": (
            "Muster fast forest packs and hoard Chapter 2 Siege Relics "
            "to crack lowland fortifications."
        ),
        "afternoon_tip": (
            "• Fog of War: Move rapidly through Lignum Forest at 1 MP "
            "per clearing to ambush isolated garrisons."
        ),
        "evening_tip": (
            "• Pack Ambush: Adds +1 ambush die (4-6) and guarantees a "
            "safe woodland withdrawal if repelled.\n"
            "• Canopy Mist: Nullifies the Defender's highest die (5 or 6)."
        ),
    },
}


# =========================================================================
# 1. COMPLETE 4-TAB WAR RULEBOOK MODAL ('CH3_RULEBOOK_MODAL')
# =========================================================================
def draw_ch3_rulebook_modal(screen, player, font, small_font, mouse_pos):
    """
    Renders the full-screen 4-Tab Articles of War & Faction Compendium
    with zero text spillage and interactive Faction Sub-Tabs.
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((12, 10, 8, 220))
    screen.blit(overlay, (0, 0))

    book_rect = pygame.Rect(24, 20, 752, 560)
    pygame.draw.rect(screen, OAK_DARK, book_rect, border_radius=10)
    pygame.draw.rect(screen, GOLD_ACCENT, book_rect, 3, border_radius=10)
    page_rect = book_rect.inflate(-16, -16)
    pygame.draw.rect(screen, DIAL_CREAM, page_rect, border_radius=8)

    active_tab = player.get("ch3_rulebook_tab", "TAB_HEGEMONY")
    active_fac = player.get(
        "ch3_rulebook_fac", player.get("ch3_faction", "Union")
    )
    ui_rects = {}

    # 1. Top Navigation Tabs (y = 36..72)
    for idx, (t_key, t_lbl) in enumerate(RULEBOOK_TABS):
        tx = 40 + idx * 180
        t_rect = pygame.Rect(tx, 36, 174, 34)
        is_cur = t_key == active_tab
        pygame.draw.rect(
            screen,
            TATE_RED if is_cur else (78, 62, 50),
            t_rect,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if is_cur else CLOCK_BLACK,
            t_rect,
            2 if is_cur else 1,
            border_radius=6,
        )
        draw_fitted_text(
            screen, t_lbl, t_rect, DIAL_CREAM, bold=True, max_lines=1
        )
        ui_rects[t_key] = t_rect

    pygame.draw.line(screen, TATE_RED, (40, 76), (760, 76), 2)

    # 2. Render Active Tab Page Content
    if active_tab == "TAB_HEGEMONY":
        sections = [
            (
                "1. THE 100-POINT HEGEMONY GOAL",
                "Chapter 3 is an asymmetric tabletop war for Dtessera "
                "Terra. The first faction to reach 100 Hegemony Points "
                "wins the war and writes the island's constitutional "
                "epilogue.",
            ),
            (
                "2. PILLAR I — CHAPTER 1 & 2 LEGACY FOUNDATION (10–35 PTS)",
                "Your choices in Murum Town and the regional wilderness "
                "are permanently locked in as your starting foundation: "
                "the 10-bit World State Vector, your 5 attributes, your "
                "Chapter 2 Position Strength (minus Exposure Tells), and "
                "mastered assets (Printing Press, Forge, Intelligence).",
            ),
            (
                "3. PILLAR II — CONTROLLED CLEARINGS & BARRICADES (+4/+6 PTS)",
                "Every map clearing flying your banner awards +4 Hegemony "
                "Points (+6 Pts for Union Barricaded clearings). Losing a "
                "clearing reduces your live territory score.",
            ),
            (
                "4. PILLAR III — FACTION SYMPATHY & AGENDA MILESTONES",
                "Each faction champions a core Sympathy (Fairness, Wealth, "
                "Order, or Nature) worth up to +20 Hegemony Points. "
                "Winning an Evening Clash awards +5 Agenda Points, while "
                "conquering one of the 7 Major Strongholds in a 3-Stage "
                "Siege awards +15 Hegemony Points!",
            ),
        ]
        y_c = 86
        for hdr, body in sections:
            box = pygame.Rect(44, y_c, 712, 96)
            pygame.draw.rect(screen, (236, 228, 212), box, border_radius=6)
            pygame.draw.rect(screen, CLOCK_BLACK, box, 1, border_radius=6)
            draw_fitted_text(
                screen,
                hdr,
                pygame.Rect(56, y_c + 6, 688, 20),
                TATE_RED,
                bold=True,
                align="left",
                max_lines=1,
            )
            draw_fitted_text(
                screen,
                body,
                pygame.Rect(56, y_c + 28, 688, 62),
                CLOCK_BLACK,
                align="left",
                max_lines=3,
            )
            y_c += 104

    elif active_tab == "TAB_PHASES":
        sections = [
            (
                "PHASE 1: DAWN LOGISTICS & REVERSIBLE DICE SOCKETS",
                "Click 'Roll Dawn Dice' to cast your command pool into the "
                "velvet tray. Drag (or click) dice into the recessed wooden "
                "sockets on your Player Board to Muster Battalions, Secure "
                "Supply Lines, or Build Defences. Click any slotted die to "
                "pop it back into the tray! Every unslotted die converts "
                "into Afternoon Movement Points (MP).",
            ),
            (
                "PHASE 2: AFTERNOON TABLETOP MARCH & TERRAIN HAZARDS",
                "Use the right-hand Zoom & Tilt sliders to inspect the 3D "
                "board. Click your gold-ringed Meeples, then click a green "
                "adjacent clearing to march (Plains/Roads: 1 MP; Forest & "
                "Mountains: 2 MP). Waterlogged basins (+1 MP) and flooded "
                "hollows (Impassable at >=75% saturation) rewards high-"
                "ground detours. Marching with 0 MP risks a 1d6 Forced "
                "March!",
            ),
            (
                "PHASE 3: DUSK 5-STAGE BATTLE DIORAMA & SIEGES",
                "Marching into a rival garrison opens the Evening Battle "
                "Diorama. Click 'Roll Battle Dice' to cast both sides' 3D "
                "dice pools. Trigger your faction's bespoke advantages or "
                "Chapter 2 Siege Relics to watch procedural dice "
                "animations shift the Tug-of-War bar before clicking "
                "'Press Assault >>'.",
            ),
            (
                "STRONGHOLD 3-STAGE SIEGES (+15 HEGEMONY PTS)",
                "The 7 faction capitals are fortified Strongholds (+2 to +3 "
                "bonus Defender dice) fought across 3 stages: Outer Works "
                "-> Gatehouse Breach -> Inner Sanctum.",
            ),
        ]
        y_c = 86
        for hdr, body in sections:
            box = pygame.Rect(44, y_c, 712, 96)
            pygame.draw.rect(screen, (236, 228, 212), box, border_radius=6)
            pygame.draw.rect(screen, CLOCK_BLACK, box, 1, border_radius=6)
            draw_fitted_text(
                screen,
                hdr,
                pygame.Rect(56, y_c + 6, 688, 20),
                TATE_RED,
                bold=True,
                align="left",
                max_lines=1,
            )
            draw_fitted_text(
                screen,
                body,
                pygame.Rect(56, y_c + 28, 688, 62),
                CLOCK_BLACK,
                align="left",
                max_lines=3,
            )
            y_c += 104

    elif active_tab == "TAB_RANKS":
        sections = [
            (
                "SUPREME GENERAL (80%+ POSITION STRENGTH, <=1 TELL)",
                "Commands all faction armies across Dtessera Terra and "
                "adds +2 bonus dice in Evening Clashes. Click any rival "
                "Faction Badge on the Top Ribbon to Forge a Known Treaty "
                "(+2 Standing), Seal a Secret Pact, or Betray an Ally "
                "for an immediate +6 Hegemony Point surge (-10 Standing).",
            ),
            (
                "SECTOR CAPTAIN (50%+ POSITION STRENGTH, <=2 TELLS)",
                "Commands regional garrisons (+1 bonus combat die) and "
                "manages Unit Confidence. Can issue a once-per-dawn "
                "Battlefield Promotion (+1 '6' Command Die). If Unit "
                "Confidence drops to 35% or below, the Captain unlocks "
                "'Incite Coup!' (seizing Generalship) and 'Turncoat "
                "Defection' (handing their garrison to a rival faction!).",
            ),
            (
                "FRONTLINE PRIVATE (BOOTS IN THE MUD)",
                "Starts with a compact dice pool but can click 'RPG Field "
                "Mode' during the Afternoon Phase to step off the board "
                "into the 1st-person RPG view! Reaching your Captain's "
                "ordered landmark and Searching before Dusk awards +2 "
                "Tactical Advantage Tokens (+2 dice in tonight's clash) "
                "and opens the path to battlefield promotion.",
            ),
            (
                "CHAPTER 2 SPECIALIST WAR-TABLE TOOLS",
                "Carrying the Portable Printing Press (+4 Sympathy), "
                "Codewheel / Deck Cipher (Enemy Target Intercept +1 Token), "
                "or Master Blacksmith / Greek Fire (+1 '6' Die & Siege "
                "Breach) unlocks bonus Morning & Evening actions!",
            ),
        ]
        y_c = 86
        for hdr, body in sections:
            box = pygame.Rect(44, y_c, 712, 96)
            pygame.draw.rect(screen, (236, 228, 212), box, border_radius=6)
            pygame.draw.rect(screen, CLOCK_BLACK, box, 1, border_radius=6)
            draw_fitted_text(
                screen,
                hdr,
                pygame.Rect(56, y_c + 6, 688, 20),
                TATE_RED,
                bold=True,
                align="left",
                max_lines=1,
            )
            draw_fitted_text(
                screen,
                body,
                pygame.Rect(56, y_c + 28, 688, 62),
                CLOCK_BLACK,
                align="left",
                max_lines=3,
            )
            y_c += 104

    else:
        # TAB 4: THE 7 FACTIONS ALMANAC
        for idx, f_key in enumerate(FACTION_ORDER):
            f_spec = ch3_war_engine.DTESSERA_FACTIONS[f_key]
            fx = 44 + idx * 102
            f_rect = pygame.Rect(fx, 84, 98, 30)
            is_sel = f_key == active_fac
            pygame.draw.rect(
                screen, f_spec["color"], f_rect, border_radius=5
            )
            pygame.draw.rect(
                screen,
                GOLD_BRIGHT if is_sel else CLOCK_BLACK,
                f_rect,
                3 if is_sel else 1,
                border_radius=5,
            )
            draw_fitted_text(
                screen, f_key, f_rect, DIAL_CREAM, bold=True, max_lines=1
            )
            ui_rects[f"FAC_{f_key}"] = f_rect

        spec = ch3_war_engine.DTESSERA_FACTIONS[active_fac]
        dossier = FACTION_DOSSIERS[active_fac]

        # Left Meeple Showcase Card (x = 44..244, y = 122..446)
        left_card = pygame.Rect(44, 122, 200, 324)
        pygame.draw.rect(screen, OAK_MID, left_card, border_radius=8)
        pygame.draw.rect(
            screen, spec["color"], (44, 122, 200, 34), border_radius=8
        )
        pygame.draw.rect(screen, GOLD_ACCENT, left_card, 2, border_radius=8)

        draw_fitted_text(
            screen,
            spec["title"].upper(),
            pygame.Rect(50, 126, 188, 26),
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )

        # Draw Large Carved Wooden Meeple Preview
        ped_rect = pygame.Rect(94, 232, 100, 32)
        pygame.draw.ellipse(screen, DIAL_CREAM, ped_rect)
        pygame.draw.ellipse(screen, GOLD_BRIGHT, ped_rect, 2)
        ch3_board_renderer._draw_single_carved_meeple(
            screen, 144, 244, 2.2, active_fac
        )

        meta_txt = (
            f"Sympathy: {spec['sympathy_type']}\n"
            f"Stronghold:\n{dossier['capital']}\n\n"
            f"Commanders:\n{dossier['leader']}\n\n"
            f"Edges:\n• {spec['advantages'][0]}\n• {spec['advantages'][1]}"
        )
        draw_fitted_text(
            screen,
            meta_txt,
            pygame.Rect(54, 274, 180, 164),
            DIAL_CREAM,
            align="left",
            max_lines=10,
        )

        # Right Strategic Breakdown Cards (x = 254..756, y = 122..446)
        cards = [
            (
                "AGENDA MILESTONE & SYMPATHY ENGINE",
                f"{spec['agenda_desc']}. Building {spec['sympathy_type']} "
                "Sympathy increases both Morning muster yield and "
                "Hegemony score (up to +20 Pts).",
            ),
            ("MORNING PHASE STRATEGY", dossier["morning_tip"]),
            ("AFTERNOON MARCH & TERRAIN EDGE", dossier["afternoon_tip"]),
            ("EVENING BATTLE DIORAMA POWERS", dossier["evening_tip"]),
        ]
        cy = 122
        for c_hdr, c_body in cards:
            c_box = pygame.Rect(254, cy, 502, 76)
            pygame.draw.rect(
                screen, (236, 228, 212), c_box, border_radius=6
            )
            pygame.draw.rect(screen, CLOCK_BLACK, c_box, 1, border_radius=6)
            draw_fitted_text(
                screen,
                c_hdr,
                pygame.Rect(264, cy + 4, 482, 18),
                TATE_RED,
                bold=True,
                align="left",
                max_lines=1,
            )
            draw_fitted_text(
                screen,
                c_body,
                pygame.Rect(264, cy + 23, 482, 48),
                CLOCK_BLACK,
                align="left",
                max_lines=3,
            )
            cy += 82

        prac_btn = pygame.Rect(254, 454, 502, 36)
        pygame.draw.rect(screen, EQUIPPED_GREEN, prac_btn, border_radius=6)
        pygame.draw.rect(screen, GOLD_BRIGHT, prac_btn, 2, border_radius=6)
        draw_fitted_text(
            screen,
            f"Launch 1-Turn Guided Tutorial as {spec['title']} >>",
            prac_btn,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )
        ui_rects["LAUNCH_FAC_TUTORIAL"] = prac_btn

    # 3. Bottom Close Button (y = 508..548)
    close_btn = pygame.Rect(260, 508, 280, 40)
    pygame.draw.rect(screen, TATE_RED, close_btn, border_radius=6)
    pygame.draw.rect(screen, GOLD_BRIGHT, close_btn, 2, border_radius=6)
    draw_fitted_text(
        screen,
        "Close Rulebook & Return >>",
        close_btn,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )
    ui_rects["CLOSE_RULEBOOK"] = close_btn

    player["ch3_rulebook_rects"] = ui_rects
    return ui_rects


def handle_ch3_rulebook_event(event, player, world_map):
    """
    Handles clicks inside the 4-Tab War Rulebook Modal.
    Returns (handled_bool, next_menu_state_or_None).
    """
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False, None

    rects = player.get("ch3_rulebook_rects", {})
    pos = event.pos

    for t_key, _ in RULEBOOK_TABS:
        if rects.get(t_key) and rects[t_key].collidepoint(pos):
            player["ch3_rulebook_tab"] = t_key
            return True, None

    for f_key in FACTION_ORDER:
        r_f = rects.get(f"FAC_{f_key}")
        if r_f and r_f.collidepoint(pos):
            player["ch3_rulebook_fac"] = f_key
            return True, None

    if (
        rects.get("LAUNCH_FAC_TUTORIAL")
        and rects["LAUNCH_FAC_TUTORIAL"].collidepoint(pos)
    ):
        fac = player.get("ch3_rulebook_fac", "Union")
        rk = player.get("ch3_rank", "General")
        start_faction_tutorial(player, fac, rk, world_map)
        return True, "CH3_MORNING_PHASE"

    if (
        rects.get("CLOSE_RULEBOOK")
        and rects["CLOSE_RULEBOOK"].collidepoint(pos)
    ):
        prev = player.get("ch3_prev_modal_state", "CH3_MORNING_PHASE")
        return True, prev

    return False, None


# =========================================================================
# 2. 7-FACTION INTERACTIVE TUTORIAL SELECTOR & 10-STEP SANDBOX ENGINE
# =========================================================================
def draw_ch3_tutorial_select_modal(screen, player, font, small_font, mouse_pos):
    """
    Renders the Faction & Rank Selector Modal so the player can launch a
    sandboxed, heavy-handed 1-turn guided walkthrough for any faction.
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((12, 10, 8, 220))
    screen.blit(overlay, (0, 0))

    card = pygame.Rect(70, 48, 660, 504)
    pygame.draw.rect(screen, DIAL_CREAM, card, border_radius=10)
    pygame.draw.rect(screen, TATE_RED, card, 4, border_radius=10)
    pygame.draw.rect(
        screen, CLOCK_BLACK, card.inflate(-8, -8), 1, border_radius=8
    )

    draw_fitted_text(
        screen,
        "SELECT FACTION & RANK FOR 1-TURN GUIDED WALKTHROUGH",
        pygame.Rect(90, 64, 620, 26),
        TATE_RED,
        bold=True,
        max_lines=1,
    )
    draw_fitted_text(
        screen,
        "Your real campaign is safely snapshotted and will be restored "
        "untouched as soon as you finish or exit the practice turn.",
        pygame.Rect(90, 92, 620, 22),
        CLOCK_BLACK,
        max_lines=1,
    )

    sel_fac = player.get(
        "ch3_tut_pick_fac", player.get("ch3_faction", "Union")
    )
    sel_rk = player.get(
        "ch3_tut_pick_rank", player.get("ch3_rank", "General")
    )
    rects = {}

    # 1. Rank Selector Row (y = 124..164)
    for idx, rk in enumerate(("General", "Captain", "Private")):
        rx = 115 + idx * 195
        r_rect = pygame.Rect(rx, 124, 180, 38)
        is_r = rk == sel_rk
        pygame.draw.rect(
            screen,
            TATE_RED if is_r else (75, 62, 52),
            r_rect,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if is_r else CLOCK_BLACK,
            r_rect,
            2 if is_r else 1,
            border_radius=6,
        )
        draw_fitted_text(
            screen,
            f"Rank: {rk}",
            r_rect,
            DIAL_CREAM,
            bold=True,
            max_lines=1,
        )
        rects[f"RANK_{rk}"] = r_rect

    # 2. 7 Faction Cards (y = 176..428)
    for idx, f_key in enumerate(FACTION_ORDER):
        spec = ch3_war_engine.DTESSERA_FACTIONS[f_key]
        col = idx % 2
        row = idx // 2
        fx = 96 + col * 308
        fy = 176 + row * 62
        f_rect = pygame.Rect(fx, fy, 298, 54)
        is_f = f_key == sel_fac

        pygame.draw.rect(
            screen,
            spec["color"] if is_f else (228, 220, 204),
            f_rect,
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            GOLD_BRIGHT if is_f else CLOCK_BLACK,
            f_rect,
            3 if is_f else 1,
            border_radius=6,
        )
        txt_c = DIAL_CREAM if is_f else CLOCK_BLACK
        draw_fitted_text(
            screen,
            f"{spec['title']} ({spec['sympathy_type']})\n"
            f"Edges: {spec['advantages'][0]} & {spec['advantages'][1]}",
            f_rect.inflate(-12, -6),
            txt_c,
            bold=is_f,
            align="left",
            max_lines=2,
        )
        rects[f"FAC_{f_key}"] = f_rect

    # 3. Launch & Cancel Buttons (y = 480..526)
    start_btn = pygame.Rect(96, 480, 360, 44)
    back_btn = pygame.Rect(474, 480, 230, 44)

    pygame.draw.rect(screen, EQUIPPED_GREEN, start_btn, border_radius=6)
    pygame.draw.rect(screen, GOLD_BRIGHT, start_btn, 2, border_radius=6)
    draw_fitted_text(
        screen,
        f"Begin {sel_fac} ({sel_rk}) Walkthrough >>",
        start_btn,
        DIAL_CREAM,
        bold=True,
        max_lines=1,
    )

    pygame.draw.rect(screen, (95, 75, 65), back_btn, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, back_btn, 1, border_radius=6)
    draw_fitted_text(
        screen, "< Back to Tabletop", back_btn, DIAL_CREAM, bold=True, max_lines=1
    )

    rects["START_TUTORIAL"] = start_btn
    rects["CANCEL_TUTORIAL"] = back_btn
    player["ch3_tut_select_rects"] = rects
    return rects


def handle_ch3_tutorial_select_event(event, player, world_map):
    """Handles clicks in the 7-Faction Tutorial Selector modal."""
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False, None

    rects = player.get("ch3_tut_select_rects", {})
    pos = event.pos

    for rk in ("General", "Captain", "Private"):
        if rects.get(f"RANK_{rk}") and rects[f"RANK_{rk}"].collidepoint(pos):
            player["ch3_tut_pick_rank"] = rk
            return True, None

    for f_key in FACTION_ORDER:
        if (
            rects.get(f"FAC_{f_key}")
            and rects[f"FAC_{f_key}"].collidepoint(pos)
        ):
            player["ch3_tut_pick_fac"] = f_key
            return True, None

    if (
        rects.get("START_TUTORIAL")
        and rects["START_TUTORIAL"].collidepoint(pos)
    ):
        fac = player.get(
            "ch3_tut_pick_fac", player.get("ch3_faction", "Union")
        )
        rk = player.get(
            "ch3_tut_pick_rank", player.get("ch3_rank", "General")
        )
        start_faction_tutorial(player, fac, rk, world_map)
        return True, "CH3_MORNING_PHASE"

    if (
        rects.get("CANCEL_TUTORIAL")
        and rects["CANCEL_TUTORIAL"].collidepoint(pos)
    ):
        prev = player.get("ch3_prev_modal_state", "CH3_MORNING_PHASE")
        return True, prev

    return False, None


def start_faction_tutorial(player, faction_key, rank_key, world_map):
    """
    Snapshots the player's real campaign into memory and initialises a
    curated, deterministic 1-Turn Practice Board for `faction_key`.
    """
    global _TUTORIAL_CAMPAIGN_BACKUP
    if not player.get("ch3_tutorial_active"):
        _TUTORIAL_CAMPAIGN_BACKUP = copy.deepcopy(player)

    player["ch3_faction"] = faction_key
    player["ch3_rank"] = rank_key
    player["ch3_day"] = 1
    player["silver"] = max(50, player.get("silver", 50))
    player["ch3_world_bits"] = {f"track_{i}": 1 for i in range(1, 11)}
    for tool_item in ("portable printing press", "codewheel", "greek fire"):
        if tool_item not in player.get("inventory", []):
            player.setdefault("inventory", []).append(tool_item)

    ch3_war_engine.init_chapter_3_world_board(player, world_map)
    ui_renderer.init_ch3_morning_phase(player)

    # Curate a guaranteed pair of 4s and a 6 in the Dawn Dice Pool
    curated_vals = [6, 5, 4, 4, 3]
    player["ch3_morning_dice"] = [
        {
            "id": idx,
            "value": val,
            "rect": None,
            "slotted_in": None,
            "is_dragging": False,
        }
        for idx, val in enumerate(curated_vals)
    ]

    # Place the player's lead army at (10,10) and a rival garrison at (10,11)
    rival_fac = "Kokeshi" if faction_key != "Kokeshi" else "Laydere"
    player["ch3_armies"]["10,10"] = {"faction": faction_key, "count": 6}
    player["territories"]["10,10"] = faction_key
    player["ch3_armies"]["10,11"] = {"faction": rival_fac, "count": 3}
    player["territories"]["10,11"] = rival_fac
    player["ch3_factions"][faction_key]["capital"] = "10,10"

    ch3_board_renderer.centre_camera_on_player_forces(player)

    player["ch3_tutorial_active"] = True
    player["ch3_tutorial_step"] = 1
    player["ch3_tutorial_faction"] = faction_key
    return player


def end_faction_tutorial(player):
    """Restores the player's real campaign snapshot after exiting tutorial."""
    global _TUTORIAL_CAMPAIGN_BACKUP
    if _TUTORIAL_CAMPAIGN_BACKUP is not None:
        saved_copy = copy.deepcopy(_TUTORIAL_CAMPAIGN_BACKUP)
        player.clear()
        player.update(saved_copy)
        _TUTORIAL_CAMPAIGN_BACKUP = None
    player["ch3_tutorial_active"] = False
    player.pop("ch3_tutorial_step", None)
    return player


def _get_tutorial_step_spec(player):
    """
    Returns (spotlight_rect, card_rect, title_str, body_str, needs_next_btn)
    for the current step (1..10) of the heavy-handed guided walkthrough.
    """
    step = player.get("ch3_tutorial_step", 1)
    fac = player.get("ch3_faction", "Union")
    rk = player.get("ch3_rank", "General")
    spec = ch3_war_engine.DTESSERA_FACTIONS.get(
        fac, ch3_war_engine.DTESSERA_FACTIONS["Union"]
    )
    dossier = FACTION_DOSSIERS.get(fac, FACTION_DOSSIERS["Union"])

    if step == 1:
        return (
            pygame.Rect(260, 4, 452, 36),
            pygame.Rect(40, 62, 640, 130),
            f"STEP 1/10: THE 100-POINT HEGEMONY TRACK ({fac.upper()})",
            f"Welcome to your {fac} ({rk}) practice turn! Above you is the "
            "100-Point Hegemony Track. Your score combines your locked "
            f"Chapter 1-2 Legacy Foundation with controlled clearings (+4 "
            f"Pts each) and {spec['sympathy_type']} Sympathy. First banner "
            "to 100 Points wins the war!",
            True,
        )
    if step == 2:
        return (
            pygame.Rect(736, 44, 64, 376),
            pygame.Rect(40, 62, 640, 130),
            "STEP 2/10: THE 3D TILT & ZOOM CAMERA RAIL",
            "On the right rail are your Zoom (ZM), 3D Tilt (3D), and Pan "
            "(N/S/E/W/*) controls. Zooming in shows carved wooden Faction "
            "Meeples (your armies stand on glowing Ivory & Gold rings with "
            "a pennon flag); zooming out swaps them into Tactical Discs.",
            True,
        )
    if step == 3:
        return (
            pygame.Rect(540, 426, 252, 164),
            pygame.Rect(40, 260, 640, 128),
            "STEP 3/10: CASTING YOUR DAWN COMMAND DICE",
            "Nothing in Chapter 3 happens without your command. On the "
            "bottom-right sits your Velvet Dice Tray and Leather Dice Cup. "
            "--> ACTION REQUIRED: Click the red 'Roll Dawn Dice >>' button "
            "at the bottom-right corner now!",
            False,
        )
    if step == 4:
        return (
            pygame.Rect(204, 428, 332, 118),
            pygame.Rect(40, 260, 640, 128),
            "STEP 4/10: SLOTTING DICE INTO RECESSED WOODEN SOCKETS",
            f"{dossier['morning_tip']}\n"
            "--> ACTION REQUIRED: Drag (or click) one of your rolled 3D "
            "dice from the green Felt Tray into a recessed wooden socket "
            "in the centre of your Player Board!",
            False,
        )
    if step == 5:
        return (
            pygame.Rect(204, 428, 332, 118),
            pygame.Rect(40, 250, 640, 138),
            "STEP 5/10: 100% REVERSIBLE DICE PLACEMENT",
            "Notice how Zone A on the left updated your Muster Preview "
            "and Afternoon MP! What if you change your mind?\n"
            "--> ACTION REQUIRED: Click directly on the die you just "
            "placed inside the recessed socket to pop it right back out "
            "into the Felt Tray!",
            False,
        )
    if step == 6:
        return (
            pygame.Rect(540, 546, 252, 44),
            pygame.Rect(40, 250, 640, 138),
            "STEP 6/10: ALLOCATE & COMMIT MORNING ORDERS",
            "Every die you leave unslotted in the Felt Tray converts "
            "directly into Afternoon Movement Points (MP). Slot whichever "
            "dice you want (or use your Ch.2 tools at the bottom), then:\n"
            "--> ACTION REQUIRED: Click the green 'Commit & Start March >>' "
            "button at the bottom-right!",
            False,
        )
    if step == 7:
        return (
            pygame.Rect(206, 430, 326, 158),
            pygame.Rect(40, 62, 640, 134),
            "STEP 7/10: STEP-BY-STEP ENEMY AI & DIPLOMACY",
            "You are now in the Afternoon Phase! In the centre box, enemy "
            "AI movements are queued step-by-step so they never move "
            "behind your back. You can also click any top Faction Badge "
            "to target them with your Rank Command Deck.",
            True,
        )
    if step == 8:
        return (
            pygame.Rect(140, 80, 460, 280),
            pygame.Rect(40, 290, 640, 124),
            f"STEP 8/10: MARCH YOUR {fac.upper()} MEEPLES INTO CLASH!",
            f"{dossier['afternoon_tip']}\n"
            "--> ACTION REQUIRED: Click your gold-ringed Meeples in the "
            "centre of the board to select them, then click the adjacent "
            "RED-BORDERED enemy clearing ('CLASH!') to attack!",
            False,
        )
    if step == 9:
        return (
            pygame.Rect(60, 396, 680, 102),
            pygame.Rect(60, 284, 680, 106),
            f"STEP 9/10: ROLL BATTLE DICE & TRIGGER {fac.upper()} POWERS!",
            f"{dossier['evening_tip']}\n"
            "--> ACTION REQUIRED: Click 'Roll Battle Dice >>', then click "
            "one of your Faction Advantage buttons on the left to watch "
            "the procedural dice animation shift the Tug-of-War bar!",
            False,
        )
    return (
        pygame.Rect(398, 446, 336, 48),
        pygame.Rect(60, 284, 680, 106),
        "STEP 10/10: PRESS THE ASSAULT & CLAIM HEGEMONY!",
        "--> ACTION REQUIRED: Click 'Press Assault >>' (and then 'Next "
        "Dawn >>' once the defeated meeples topple) to claim +5 Hegemony "
        "Points and complete your guided walkthrough!",
        False,
    )


def draw_tutorial_spotlight_overlay(screen, player, small_font):
    """
    Renders the pulsing Gold Spotlight Frame and Sergeant Grimwald's
    Instructor Card during an active 10-step Faction Walkthrough.
    """
    if not player.get("ch3_tutorial_active"):
        return

    spot_rect, card_rect, title, body, has_next = _get_tutorial_step_spec(
        player
    )
    now = pygame.time.get_ticks()
    pulse = 3 if (now // 300) % 2 == 0 else 1

    # 1. Pulsing Gold Spotlight Frame around the target UI zone
    pygame.draw.rect(
        screen,
        GOLD_BRIGHT,
        spot_rect.inflate(pulse * 2, pulse * 2),
        4,
        border_radius=8,
    )
    pygame.draw.rect(
        screen, TATE_RED, spot_rect.inflate(8, 8), 2, border_radius=9
    )

    # 2. Instructor Parchment Card
    pygame.draw.rect(
        screen, (18, 14, 10), card_rect.move(4, 5), border_radius=8
    )
    pygame.draw.rect(screen, DIAL_CREAM, card_rect, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, card_rect, 3, border_radius=8)
    pygame.draw.rect(
        screen, GOLD_ACCENT, card_rect.inflate(-6, -6), 1, border_radius=6
    )

    draw_fitted_text(
        screen,
        title,
        pygame.Rect(card_rect.x + 14, card_rect.y + 8, card_rect.width - 150, 20),
        TATE_RED,
        bold=True,
        align="left",
        max_lines=1,
    )

    text_w = card_rect.width - (155 if has_next else 28)
    draw_fitted_text(
        screen,
        body,
        pygame.Rect(
            card_rect.x + 14, card_rect.y + 30, text_w, card_rect.height - 38
        ),
        CLOCK_BLACK,
        align="left",
        max_lines=5,
    )

    # Exit Tutorial Button (Top-Right of Instructor Card)
    exit_rect = pygame.Rect(card_rect.right - 128, card_rect.y + 7, 118, 22)
    pygame.draw.rect(screen, (85, 42, 38), exit_rect, border_radius=4)
    pygame.draw.rect(screen, GOLD_ACCENT, exit_rect, 1, border_radius=4)
    draw_fitted_text(
        screen, "Exit Tutorial [X]", exit_rect, DIAL_CREAM, bold=True, max_lines=1
    )
    player["ch3_tut_exit_rect"] = exit_rect

    # Next Step Button (if informational step)
    if has_next:
        next_rect = pygame.Rect(
            card_rect.right - 134, card_rect.bottom - 44, 124, 34
        )
        pygame.draw.rect(screen, EQUIPPED_GREEN, next_rect, border_radius=5)
        pygame.draw.rect(screen, GOLD_BRIGHT, next_rect, 2, border_radius=5)
        draw_fitted_text(
            screen, "Next Step >>", next_rect, DIAL_CREAM, bold=True, max_lines=1
        )
        player["ch3_tut_next_rect"] = next_rect
    else:
        player["ch3_tut_next_rect"] = None


def handle_tutorial_overlay_click(event, player):
    """
    Processes clicks on the Tutorial Instructor Card ('Next Step >>' or
    'Exit Tutorial [X]'). Returns (handled_bool, exited_tutorial_bool).
    """
    if not player.get("ch3_tutorial_active"):
        return False, False
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False, False

    pos = event.pos
    exit_r = player.get("ch3_tut_exit_rect")
    if exit_r and exit_r.collidepoint(pos):
        end_faction_tutorial(player)
        return True, True

    next_r = player.get("ch3_tut_next_rect")
    if next_r and next_r.collidepoint(pos):
        player["ch3_tutorial_step"] = min(
            10, player.get("ch3_tutorial_step", 1) + 1
        )
        return True, False

    return False, False
