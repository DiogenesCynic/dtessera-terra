import pygame
import game_data as db
from mechanics import get_eligible_chapter_2_routes
from ui_components import draw_fitted_text


# =========================================================================
# 1. THE 10 UNLOCKABLE CHAPTER 2 TRACK REQUIREMENTS TABLE
# =========================================================================
TRACK_REQ_TABLE = [
    {
        "id": 1,
        "route_key": "Stand for Union Official",
        "name": "1. Regional Union Official",
        "reqs": "Joined Union | Union Faction >= 4 | Skill: Union Steward OR Radical Theory (or Cha >= 5 / Equ >= 5)",
        "hint_to_unlock": "Speak with Truthtale at Union House or work at the Stables/Market.",
    },
    {
        "id": 2,
        "route_key": "Apply for Town Guard",
        "name": "2. Corporal of the Town Guard",
        "reqs": "Rep >= 3 | Guard Faction >= 5 OR (Str >= 6 + Sword) OR (Ride + Equ >= 5) [Double-Agent: Rep >= 5, Guard >= 8, Stl >= 5]",
        "hint_to_unlock": "Speak with Captain Wealdhere at the Murum Guard House.",
    },
    {
        "id": 3,
        "route_key": "Join Castellan's House Staff",
        "name": "3. Castellan's House Staff (Ragmore)",
        "reqs": "Rep >= 5 | Wallmakers <= 2 | (Skill: Mayor's Footman + Inf >= 5) OR (Skill: Stable Master + Equ >= 5)",
        "hint_to_unlock": "Work at the Mayor's House or Murum Stables.",
    },
    {
        "id": 4,
        "route_key": "Parvus: F.A.I.-C.N.T. Syndicate",
        "name": "4. Parvus: F.A.I.-C.N.T. Syndicate",
        "reqs": "Syndicate Token / Anarchist Cell / Radical Theory | Cha >= 5 | Union Faction >= 3 (or Radical Theory)",
        "hint_to_unlock": "Attend a backroom meeting at Union House or study Radical Theory.",
    },
    {
        "id": 5,
        "route_key": "Parvus: Crown Intelligencers",
        "name": "5. Parvus: Crown Intelligencers",
        "reqs": "Skill: Intelligence Officer OR King's Intelligencer | Guard Faction >= 8 | Stealth >= 6",
        "hint_to_unlock": "Earn promotions in the Murum Guard under Captain Wealdhere.",
    },
    {
        "id": 6,
        "route_key": "Parvus: Maritime & Artisans Guild (50s)",
        "name": "6. Parvus: Maritime & Artisans Guild",
        "reqs": "Rep >= 5 | Silver >= 95s (50s Bond) | (Skill: Master Blacksmith + Str >= 6) OR (Market Overseer + Cha >= 5)",
        "hint_to_unlock": "Master the Blacksmith Forge or the Murum Market stalls.",
    },
    {
        "id": 7,
        "route_key": "Run for Public Office (50s)",
        "name": "7. Run for Public Office (Tribune)",
        "reqs": "Rep >= 6 | Silver >= 50s Deposit | Item: Reference Letter | Inf >= 6 OR Cha >= 6 (or Rep >= 7 + Inf/Cha >= 5)",
        "hint_to_unlock": "Speak with Dr. Makepeace at the Hospital or the Mayor's House.",
    },
    {
        "id": 8,
        "route_key": "Join Wallmaker Syndicate",
        "name": "8. The Wallmaker / Kokeshi Syndicate",
        "reqs": "Wallmaker Faction >= 6 | Stealth >= 6 | Not Reported to Guard | Skill: Master Wallmaker OR Climb",
        "hint_to_unlock": "Work on the Murum Town Wall with Hopestill and Wellspring.",
    },
    {
        "id": 9,
        "route_key": "Become a Highway Robber",
        "name": "9. Highway Robber (Black Dog's Gang)",
        "reqs": "Reputation <= -1 | Has Sword | Has Tent OR Horse | Strength >= 6 OR Stealth >= 6",
        "hint_to_unlock": "Visit the Tavern or let your Reputation slip into infamy.",
    },
    {
        "id": 10,
        "route_key": "Join Fairlight's Acting Troupe",
        "name": "10. Fairlight's Acting Troupe",
        "reqs": "Rep >= 2 | Item: Playhouse Ticket OR Poster | Charisma >= 5 (or Influence >= 5 + Cha >= 1)",
        "hint_to_unlock": "Speak with Fairlight at the Murum Playhouse.",
    },
]


def check_auto_unlock_ledger_lines(player):
    """Automatically unlocks lines in the Career Ledger based on the player's discoveries and skills."""
    unlocked = set(player.setdefault("unlocked_ledger_lines", [1, 2]))  # Lines 1 & 2 start unlocked as examples
    skills = player.get("skills", [])
    inv = player.get("inventory", [])

    if "mayor's footman" in skills or "stable master" in skills or player.get("mayors_house_shifts", 0) > 0:
        unlocked.add(3)
    if "radical theory" in skills or "syndicate token" in inv or player.get("anarchist_cell_joined"):
        unlocked.add(4)
    if "intelligence officer" in skills or player.get("faction_guard", 0) >= 4:
        unlocked.add(5)
    if "master blacksmith" in skills or "market overseer" in skills or "forge" in skills:
        unlocked.add(6)
    if "reference letter" in inv or player.get("reputation", 0) >= 4:
        unlocked.add(7)
    if player.get("faction_wallmakers", 0) >= 2 or "master wallmaker" in skills:
        unlocked.add(8)
    if player.get("reputation", 0) < 0 or "iron sword" in inv:
        unlocked.add(9)
    if "playhouse ticket" in inv or "poster" in inv:
        unlocked.add(10)

    player["unlocked_ledger_lines"] = sorted(list(unlocked))
    return player["unlocked_ledger_lines"]


def unlock_next_ledger_line_with_research(player):
    """Allows the player to spend 5 Silver (or 20 minutes of research) inside the Ledger UI to unseal the next locked line!"""
    unlocked = check_auto_unlock_ledger_lines(player)
    for row in TRACK_REQ_TABLE:
        if row["id"] not in unlocked:
            if player.get("silver", 0) < 5:
                return player, "Clerk's Inquiry Fee: You need 5 Silver to pay a courier for the unsealed dossier on that track!"
            player["silver"] -= 5
            unlocked.append(row["id"])
            player["unlocked_ledger_lines"] = sorted(unlocked)
            return player, f"For 5 Silver, a clerk unseals Line #{row['id']}: **{row['name']}**!"
    return player, "All 10 Career Track lines in your ledger are already unsealed!"


def draw_track_requirements_table_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the 680x480 Tate Britain Pop-Out Table showing the 10 Chapter 2 Track Minimum Requirements."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)

    panel = pygame.Rect(40, 30, 720, 500)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    unlocked = check_auto_unlock_ledger_lines(player)
    eligible_routes = set(get_eligible_chapter_2_routes(player))

    title = font_bold.render(
        f"SURVEYOR'S CAREER LEDGER — TRACK REQUIREMENTS ({len(unlocked)}/10 UNSEALED)",
        True, TATE_RED
    )
    screen.blit(title, (400 - title.get_width() // 2, 42))

    row_font = pygame.font.Font(None, 17)
    bold_row = pygame.font.Font(None, 18)

    y_cursor = 72
    for row in TRACK_REQ_TABLE:
        r_rect = pygame.Rect(58, y_cursor, 684, 36)
        is_open = (row["id"] in unlocked)
        is_elig = (row["route_key"] in eligible_routes)

        bg_col = (230, 246, 232) if (is_open and is_elig) else ((252, 248, 238) if is_open else (218, 214, 206))
        border_col = (45, 135, 65) if (is_open and is_elig) else (TATE_RED if is_open else (130, 130, 130))

        pygame.draw.rect(screen, bg_col, r_rect, border_radius=5)
        pygame.draw.rect(screen, border_col, r_rect, width=1, border_radius=5)

        if is_open:
            status_str = "[ELIGIBLE]" if is_elig else "[NOT YET MET]"
            st_col = (35, 125, 55) if is_elig else TATE_RED
            screen.blit(bold_row.render(f"{row['name']}  {status_str}", True, st_col), (68, y_cursor + 4))
            screen.blit(row_font.render(f"Min Reqs: {row['reqs']}", True, CLOCK_BLACK), (68, y_cursor + 20))
        else:
            screen.blit(bold_row.render(f"Track #{row['id']}: [SEALED DOSSIER — ???]", True, (90, 90, 90)), (68, y_cursor + 4))
            screen.blit(row_font.render(f"How to Unseal: {row['hint_to_unlock']} (Or click 'Unseal Next Line (5s)' below)", True, (110, 100, 95)), (68, y_cursor + 20))

        y_cursor += 39


# =========================================================================
# 2. CROSS-TRACK WORLD NEWS CRIERS (REACTIVE REALM DISPATCHES)
# =========================================================================
CROSS_TRACK_DISPATCHES = {
    1: (
        "=== REALM DISPATCHES: THE GATHERING STORM ===\n"
        "• **Fluvius Farmlands:** Union delegates are canvassing the tenant orchards while Watch recruits drill with halberds in Murum!\n"
        "• **Ragmore Plains:** Wild forest stags have stampeded across Castellan Hrothgar's pastures as envoys arrive for the war-tax summit.\n"
        "• **Parvus Harbour:** The great Guild Gantry Crane has jammed on the mole while F.A.I. agitators and Crown spies shadow each other along the Rope-Walk!\n"
        "• **The Highways & Stage:** Mystery chalk ciphers have appeared on the Old Path milestones, Black Dog's outlaws are eyeing a bullion coach on the New Road, and Fairlight's Troupe has three rival patrons bidding backstage!"
    ),
    2: (
        "=== REALM DISPATCHES: SPARKS IN THE TINDER ===\n"
        "• **Fluvius Town:** While Union delegates parley with Bailiff Seekgrace, costumed 'bailiffs' from Fairlight's Troupe sparked a cobblestone riot in Market Square right in front of the Town Watch and the Election Hustings!\n"
        "• **Lignum Forest & Diluvium:** Castellan Hrothgar's royal hunting party was ringed by Vanguardist antlers in the deep glade, while Kokeshi manhunters vanished into the Diluvium briar-maze chasing Black Dog's gang!\n"
        "• **Parvus Port:** Forged Watch billeting warrants have been pasted across the net-sheds, and the Artisans' Guild uncovered a ring of brittle counterfeit slag-iron at the Dry-Dock!"
    ),
    3: (
        "=== REALM DISPATCHES: THE GREAT CROSSROADS COLLISION ===\n"
        "• **Fluvius Farm Crossroads:** Six factions just collided at the Farm Picket Crossroads! Union strikers flooded the Sunken Lane, Wagon-Boss Corban's Kokeshi scabs tried to ram the hay-wains, Town Watch halberdiers formed a cordon, Ragmore Lancers appeared on the ridge, Fairlight performed a biting satire from a tailgate, and highwaymen snatched the Bailiff's pay-chest in the smoke!\n"
        "• **Fluvius Square:** Election auditors caught a clerk trying to slip violet-dyed Syndicate coins into the campaign subscription chest!\n"
        "• **Parvus Quays:** Lanterns flared at midnight inside the Kokeshi Bonded Warehouses as customs cutters impounded a brigantine weighted down with secret swivel-guns!"
    ),
    4: (
        "=== REALM DISPATCHES: THE NIGHT OF LONG KNIVES & CATACOMBS ===\n"
        "• **Castle Ragmore & The New Road:** Mayor Givethanks' state coach ran an outlaw gauntlet up the New Road to Lord Hrothgar's Summit Banquet—where a Castle Laydere poison plot and a backstage map-heist occurred during the masque!\n"
        "• **Fluvius & The Old Path:** Magistrate Fleepride's Emergency Tribunal convened over the shattered watermill axle, while a secret backroom parley took place by candlelight at the Ruined Waystation!\n"
        "• **Under-Parvus Catacombs:** Muffled tremors shook Upper Parvus as F.A.I. sappers, Crown agents, and Guild engineers clashed in the flooded tidal vaults beneath the Promenade!"
    ),
    5: (
        "=== REALM DISPATCHES: THE EVE OF WAR ===\n"
        "• **Murum & Frontier Watchpost:** Union House has locked its doors to unmask a syndicate mole, the Frontier Watchpost is choosing between Ragmore and Laydere, Hrothgar is mustering the Grand Feudal Levy, and Black Dog is preparing to hijack the military munitions train at the river-gorge!\n"
        "• **Fluvius Guildhall:** The oak ballot urns are sealed inside the Guildhall as the Civic Clock-Tower prepares to toll the close of polls and Fairlight raises the curtain on a revolutionary premiere!\n"
        "• **Parvus Promenade:** Thousands pack the Harbour Festival before Mayor Holdfast's balcony while the Maritime Guild dictates the Grand War-Fleet Contract!"
    ),
}


def get_embracepenitence_options(player):
    return [
        "Hear the Latest Dispatches Across Dtessera Terra",
        "Inspect Your Surveyor's Career Ledger",
        "Leave",
    ]


def resolve_embracepenitence(choice, player):
    if choice == "Leave":
        return player, "The crier rings his brass hand-bell and calls the hour.", "MAIN"

    if choice == "Inspect Your Surveyor's Career Ledger":
        return player, "You open your Surveyor's Career Ledger to review the 10 Chapter 2 tracks.", "MINIGAME_TRACK_TABLE"

    if choice == "Hear the Latest Dispatches Across Dtessera Terra":
        step = min(5, max(1, player.get("ch2_mission_step", 1)))
        return player, CROSS_TRACK_DISPATCHES[step], "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 3. CHAPTER 2 COMPLETION HERALDRY CARD (CHAPTER_2_COMPLETE)
# =========================================================================
TRACK_WORLD_BIT_NAMES = [
    ("track_1", "1. Agrarian & Union Solidarity"),
    ("track_2", "2. Frontier Watch Allegiance"),
    ("track_3", "3. Castle Ragmore Feudal Host"),
    ("track_4", "4. Parvus Revolutionary Commune"),
    ("track_5", "5. Crown Harbour Security"),
    ("track_6", "6. Independent Guild Armada"),
    ("track_7", "7. People's Tribune Magistracy"),
    ("track_8", "8. Kokeshi Shadow Syndicate"),
    ("track_9", "9. Outlaw Free-State of the Roads"),
    ("track_10", "10. Popular Theatrical Awakening"),
]


def draw_chapter_2_completion_card(screen, player, font, font_bold, mouse_pos):
    """
    Renders the ornate Full-Screen Tate Britain Chapter 2 Completion Card when any
    Track 1–10 Mission E finishes!
    """
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((12, 14, 20, 225))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    GOLD_ACCENT = (195, 145, 40)

    card = pygame.Rect(50, 30, 700, 500)
    pygame.draw.rect(screen, DIAL_CREAM, card, border_radius=14)
    pygame.draw.rect(screen, TATE_RED, card, width=5, border_radius=14)
    pygame.draw.rect(screen, GOLD_ACCENT, card.inflate(-10, -10), width=2, border_radius=10)

    # Header Banner
    hdr = font_bold.render("CHAPTER II COMPLETE — THE EVE OF WAR IN DTESSERA TERRA", True, TATE_RED)
    screen.blit(hdr, (400 - hdr.get_width() // 2, 48))

    route = player.get("chapter_2_route", "Independent Adventurer")
    pos_str = min(100, player.get("position_strength", 0))
    tells = player.get("exposure_tells", 0)
    dungeons = len(player.get("dungeons_cleared", []))

    sub = font_bold.render(
        f"Career Track: {route}  |  Position Strength: {pos_str}%  |  Exposure Tells: {tells}  |  Dungeons: {dungeons}/4",
        True, CLOCK_BLACK
    )
    screen.blit(sub, (400 - sub.get_width() // 2, 76))

    # Summary Narrative Box
    sum_box = pygame.Rect(80, 104, 640, 96)
    pygame.draw.rect(screen, (252, 248, 238), sum_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, sum_box, width=2, border_radius=8)

    rank_title = "GRAND ARCHITECT OF THE REALM" if pos_str >= 80 else ("SEASONED OPERATIVE" if pos_str >= 55 else "SURVIVOR OF THE STORM")
    summary_text = (
        f"Standing Rank: {rank_title}.\n"
        "Across the towns of Murum, Fluvius, and Parvus, the ten great currents of Chapter 2 have reached their climax. "
        "Below is the state of the realm your actions have forged for Chapter 3:"
    )
    draw_fitted_text(screen, summary_text, sum_box.inflate(-16, -12), CLOCK_BLACK, max_lines=3)

    # 10-Track World-State Heraldry Grid (2 columns x 5 rows)
    bits = player.get("ch3_world_bits", {})
    small_b = pygame.font.Font(None, 18)

    for idx, (b_key, b_label) in enumerate(TRACK_WORLD_BIT_NAMES):
        col = idx // 5
        row = idx % 5
        bx = 80 + col * 325
        by = 212 + row * 40
        b_rect = pygame.Rect(bx, by, 315, 34)

        val = bits.get(b_key, None)
        if val == 1:
            bg = (225, 245, 228)
            bd = (45, 135, 65)
            tag = "ASCENDANT [1]"
            t_col = (30, 110, 45)
        elif val == 0:
            bg = (248, 228, 225)
            bd = TATE_RED
            tag = "FOILED / OPPOSED [0]"
            t_col = TATE_RED
        else:
            bg = (238, 234, 224)
            bd = (140, 135, 125)
            tag = "UNCONTESTED [-]"
            t_col = (95, 95, 95)

        pygame.draw.rect(screen, bg, b_rect, border_radius=6)
        pygame.draw.rect(screen, bd, b_rect, width=2, border_radius=6)
        screen.blit(small_b.render(f"{b_label}: {tag}", True, t_col), (bx + 10, by + 9))


HANDLERS = {
    "embracepenitence":     (get_embracepenitence_options, resolve_embracepenitence),
    "skipper_omalley":      (get_embracepenitence_options, resolve_embracepenitence),
}
