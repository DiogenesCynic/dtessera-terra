import random
import pygame
import game_data as db
from mechanics import modify_faction, advance_time, execute_ch2_mission
from ui_components import draw_fitted_text


# =========================================================================
# 1. SHARED 2d6 ELECTION & SYNDICATE VARIANCE (WINDFALLS & FRICTION)
# =========================================================================
def roll_election_2d6_twist(player, track_kind="office"):
    """
    Rolls 2d6 for Public Office (Track 7) and Kokeshi Syndicate (Track 8) missions.
    Returns (swing_int, prefix_str, twist_str).
    """
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    swing = (d1 + d2 - 7) * 2
    prefix = f"[Roll {d1}+{d2}={d1+d2}] "
    twist_str = ""

    if random.random() < 0.30:
        if track_kind == "office":
            twists = [
                ("WINDFALL: The Fluvius Washerwomen's Guild marches into the square banging copper pots in support of your speech! (+8% Support)", 8),
                ("WINDFALL: An honest chandler donates 10 silver to your clean-elections ribbon fund! (+10s)", 6),
                ("FRICTION: A paid Kokeshi heckler hurls a rotten turnip at the hustings platform! (-6% Support)", -6),
            ]
        else:
            twists = [
                ("WINDFALL: A corrupt customs clerk looks the other way and slips you a 12-silver smuggling cut! (+12s, +6% Leverage)", 6),
                ("WINDFALL: Heavy river-mist blankets the Old Path milestones, hiding your courier marks from the Watch! (+8% Leverage)", 8),
                ("FRICTION: A stray Watch lantern-patrol forces you to duck into a wet ditch along the lane! (-6% Leverage)", -6),
            ]
        t_text, mod = random.choice(twists)
        swing += mod
        if "+10s" in t_text:
            player["silver"] += 10
        elif "+12s" in t_text:
            player["silver"] += 12
        twist_str = f" [{t_text}]"

    return swing, prefix, twist_str


# =========================================================================
# 2. DISCOVERABLE NPCS FOR TRACKS 7 & 8 (GILDED-TONGUE, ABSENCEOFSIN, EOGHAN)
# =========================================================================
def get_gilded_tongue_options(player):
    opts = ["Listen to Alderman Gilded-Tongue's campaign speech"]
    if player.get("chapter_2_route") in ("Run for Public Office (50s)", "Join Wallmaker Syndicate"):
        opts.insert(0, "Question his suspiciously lavish campaign banners")
    opts.append("Leave")
    return opts


def resolve_gilded_tongue(choice, player):
    if choice == "Leave":
        return player, "Alderman Gilded-Tongue adjusts his gold-trimmed waistcoat and waves to the crowd.", "MAIN"

    if choice == "Listen to Alderman Gilded-Tongue's campaign speech":
        return player, (
            "Standing atop a velvet-draped hustings box in Fluvius Square, Alderman Gilded-Tongue booms:\n"
            "\"Vote for stability, good burghers! Why trouble your heads with guild charters or farm strikes when my benefactors guarantee low duties for the great merchant houses?\""
        ), "NPC_DIALOGUE"

    if choice == "Question his suspiciously lavish campaign banners":
        player["el_gilded_clue"] = True
        return player, (
            "You step close to the Alderman's platform and notice that his silk banners are printed with violet Kokeshi ink—and his bodyguards wear the heavy leather gauntlets of Syndicate wharf-bruisers!\n"
            "Gilded-Tongue sweats beneath his powdered wig: \"A private donation from civic-minded wall-builders, I assure you!\" "
            "(Speaking with **Printer Absenceofsin** by the Civic Clock-Tower or **Search**ing the **Ruined Waystation** on the Old Path may reveal who holds his leash.)"
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_absenceofsin_options(player):
    opts = [
        "Use Absenceofsin's Flatbed Printing Press",
        "Ask about the Fluvius Election broadsheets",
    ]
    if player.get("ch2_mission_step") in (2, 3, 5):
        opts.insert(0, "Ask who has been buying up paper and ballot-wax in town")
    if "lead type-case" not in player.get("inventory", []) and "portable printing press" not in player.get("inventory", []):
        opts.insert(1, "Acquire a Spare Lead Type-Case for Your Own Press")
    opts.append("Leave")
    return opts


def resolve_absenceofsin(choice, player):
    if choice == "Leave":
        return player, "Printer Absenceofsin wipes black ink from his brass composing-stick.", "MAIN"

    if choice == "Ask about the Fluvius Election broadsheets":
        return player, (
            "\"Every candidate wants ten thousand handbills by sundown, and my apprentice's arms are ready to fall off at the press-lever!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask who has been buying up paper and ballot-wax in town":
        player["el_absenceofsin_clue"] = True
        return player, (
            "Printer Absenceofsin glances toward the shadowed cul-de-sac behind the Clock-Tower.\n"
            "\"Two things ought to concern any honest voter: first, the three voter blocs in Fluvius—the **River-Bargees**, the **Agrarian Tenants**, and the **Town Artisans**—all hate Bailiff Seekgrace's hidden river-tolls, "
            "so any candidate who pledges a **Unified River & Granary Charter** wins all three at once!\"\n\n"
            "\"Second, a hooded Kokeshi agent bought ten pounds of **crimson ballot-sealing wax** yesterday, stamped with the serial mark **'K-44'**! "
            "If you check the **ballot-table in the Counting House Square** during the funding drive, watch out for counterfeit coin and K-44 wax!\""
        ), "NPC_DIALOGUE"

    if choice == "Use Absenceofsin's Flatbed Printing Press":
        return printing_press_engine.init_typeset_minigame(player)

    if choice.startswith("Acquire a Spare Lead Type-Case"):
        if player.get("faction_union", 0) >= 4 or player.get("faction_wallmakers", 0) >= 4:
            player["inventory"].append("lead type-case")
            return player, (
                "Printer Absenceofsin slides a heavy wooden drawer of cast lead letter-blocks from beneath the counter.\n"
                "\"For a proven comrade of the cause, take this spare **Lead Type-Case** with my compliments! Fit it to an **Oak Press-Frame** and an **Iron Screw-Spindle**, and you can print anywhere on the road.\""
            ), "NPC_DIALOGUE"
        if player.get("silver", 0) >= 20:
            player["silver"] -= 20
            player["inventory"].append("lead type-case")
            return player, (
                "You pay 20 silver and receive a compartmentalised **Lead Type-Case** (Part 3/3 of the Portable Printing Press)!"
            ), "NPC_DIALOGUE"
        return player, "\"A full fount of cast lead-antimony type costs 20 silver, friend—unless you've earned the trust of the Union or the Syndicate.\"", "NPC_DIALOGUE"

def get_eoghan_options(player):
    opts = ["Ask about quiet river-cargo"]
    if player.get("ch2_mission_step") in (2, 4):
        opts.insert(0, "Ask who fence-moved the bullion from the robbed Kokeshi payroll coach")
    opts.append("Leave")
    return opts


def resolve_eoghan(choice, player):
    if choice == "Leave":
        return player, "Eoghan slides his pewter measure back under his oilskin coat.", "MAIN"

    if choice == "Ask about quiet river-cargo":
        return player, "\"Flotsam and jetsam, friend. The river brings all things to those who wait.\"", "NPC_DIALOGUE"

    if choice == "Ask who fence-moved the bullion from the robbed Kokeshi payroll coach":
        player["el_eoghan_clue"] = True
        return player, (
            "Eoghan's eyes dart toward the taproom door.\n"
            "\"Keep your voice down! That 'merchant coach' Black Dog's highwaymen knocked over on the **New Road Muddy Hollow** was carrying the Kokeshi Syndicate's black-iron seal and forty pounds of election silver!\"\n"
            "\"Black Dog's lieutenant ditched the smashed iron strongbox in the **Muddy Hollow bracken** on the New Road, and rode north toward the **Diluvium Glade briar-thickets** with the seal! "
            "**Search** the **Muddy Hollow on the New Road** first to recover the lock-plate and trail-spoor!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 3. ENVIRONMENTAL SEARCH HOOKS FOR TRACKS 7 & 8
# =========================================================================
def handle_election_search(player):
    """
    Called inside action_gather() for Public Office (Track 7) and Wallmaker Syndicate (Track 8).
    Returns (handled_bool, log_message).
    """
    pos = (player["x"], player["y"])
    if player.get("current_building"):
        return False, ""

    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)

    # 1. Castle Ragmore Inner Bailey (4, 22) on Step 1 of Public Office (7A): Find Royal Tax-Exemption Roll!
    if pos in ((3, 22), (4, 22)) and route == "Run for Public Office (50s)" and step == 1:
        if player.get("el_ragmore_charter_found"):
            return True, "You have already copied the Old-Order Municipal Tax-Exemption Roll from the Ragmore archive chest."
        player["el_ragmore_charter_found"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Searching the dusty chancery chests beside the Castle Ragmore bailey wall, you unroll an ancient parchment bearing the seal of the First Castellan:\n"
            "It proves that **Murum and Fluvius are legally exempt from feudal war-taxes whenever the towns maintain their own Watch and bridges**! "
            "With this precedent (or the Mountain Sage's Charter), you can compel Lord Hrothgar to respect Armed Neutrality!"
        )

    # 2. Fluvius Market & Counting House Square (11, 4) on Step 3 of Public Office (7C): Catch Marked Bribe-Coins!
    if pos == (11, 4) and route == "Run for Public Office (50s)" and step == 3:
        if player.get("el_marked_coins_found"):
            return True, "You have already purged the Kokeshi-marked silver coins from your campaign collection chest."
        player["el_marked_coins_found"] = True
        player["silver"] += 10
        player, _ = advance_time(15, player)
        return True, (
            "Inspecting your campaign subscription chest in Fluvius Square, you catch a Kokeshi clerk slipping twenty clip-edged silver coins stamped with violet dye into the slot—an attempt to frame your campaign for taking illicit syndicate money!\n"
            "You seize the clerk's genuine **10-silver** purse as a fine and publicly seal the tainted coins as evidence! (+10 Silver)"
        )

    # 3. The New Road — Muddy Hollow (7, 22) on Step 2 of Wallmaker Syndicate (8B): Recover Strongbox Lock & Trail!
    if pos == (7, 22) and route == "Join Wallmaker Syndicate" and step == 2:
        if player.get("el_hollow_strongbox_found"):
            return True, "You have already recovered the sheared Kokeshi strongbox lock and tracked the outlaw hoofprints from the Muddy Hollow."
        die = random.randint(1, 6) + (player.get("stealth", 0) // 2)
        player["el_hollow_strongbox_found"] = True
        player, _ = advance_time(20, player)
        extra = " (+8s Windfall found wedged in the lining!)" if die >= 7 else ""
        if die >= 7:
            player["silver"] += 8
        return True, (
            f"[Track Roll: {die}] Searching the gorse-choked ditch of the Muddy Hollow where the payroll coach was ambushed, "
            "you pull up the shattered oak lid of the Kokeshi strongbox!\n"
            "The boot-prints around it show that **one of the coach's own outriders** unbolted the box from the inside for Black Dog's gang, "
            f"leaving a trail of dropped silver and red-clay hoofprints leading straight to the **fence's cache**!{extra}"
        )

    # 4. The Old Path — Ruined Waystation (3, 12) on Step 4 (7D or 8D): Discover the Hollow Speaking-Tube!
    if pos == (3, 12) and step == 4 and route in ("Run for Public Office (50s)", "Join Wallmaker Syndicate"):
        if player.get("el_waystation_tube_found"):
            return True, "You have already rigged the acoustic speaking-tube and hidden wax-impression cylinder behind the Waystation hearth."
        player["el_waystation_tube_found"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Searching behind the ivy-choked hearth of the Ruined Waystation before the backroom meeting begins, "
            "you uncover a hollow mason's speaking-tube built into the chimney flue and a cache of **K-44 crimson ballot-wax**!\n"
            "Whether you sit at the table as Candidate or Syndicate Fixer, you now hold complete acoustic and physical leverage over the room!"
        )

    return False, ""


# =========================================================================
# 4. TRACKS 7 & 8 SCENARIOS (MINIGAME_ELECTION POP-OUT ENGINE)
# =========================================================================
ELECTION_SCENARIOS = {
    # ------------------------------------------------------------------
    # TRACK 7: PUBLIC OFFICE (7A, 7B, 7C, 7D, 7E)
    # ------------------------------------------------------------------
    "7a": {
        "track": "office",
        "header": "CASTLE RAGMORE GREAT HALL — THE FEUDAL WAR-TAX SUMMIT",
        "prep_flag": "el_ragmore_charter_found",
        "prep_label": "Old-Order Municipal Tax-Exemption Roll (or Sage's Charter)",
        "stages": [
            {
                "title": "ROUND 1/3: LORD HROTHGAR'S FEUDAL DEMAND",
                "desc": "Castellan Hrothgar demands that every candidate for the Fluvius & Murum Magistracy swear to levy a 20% war-tax on the towns to fund his lancers!",
                "opts": [
                    ("Cite the Old-Order Tax-Exemption Roll & Sage's Charter for Armed Neutrality! (2d6)", 26),
                    ("Offer to maintain the New Road bridges in lieu of cash taxes (2d6)", 16),
                    ("Bow humbly and promise to tax the townsfolk dry", -15),
                ],
            },
            {
                "title": "ROUND 2/3: THE BARONIAL KNIGHTS' CHALLENGE",
                "desc": "Hrothgar's Knight-Marshal sneers: \"And if Castle Laydere marches on the river-fords, how will a civilian tribune defend the valley?\"",
                "opts": [
                    ("Pledge a disciplined Municipal Watch & fortified town walls! (2d6)", 24),
                    ("Remind the knights that Castle Ragmore depends on town grain & iron (2d6)", 18),
                    ("Admit that the towns are helpless without feudal lords", -18),
                ],
            },
            {
                "title": "ROUND 3/3: SEALING THE CANDIDATE'S ACCORD",
                "desc": "Impressed by your spine, Castellan Hrothgar reaches for his signet to endorse a border compact.",
                "opts": [
                    ("Sign the Compact of Armed Municipal Neutrality (+Union & +Town Support)! (2d6)", 25),
                    ("Accept a 30-silver Gentry trade-subsidy with no feudal strings (2d6)", 20),
                    ("Sign a secret war-tax codicil behind the voters' backs", -15),
                ],
            },
        ],
    },
    "7b": {
        "track": "office",
        "header": "FLUVIUS MARKET SQUARE — THE THREE-BLOC HUSTINGS DEBATE",
        "prep_flag": "el_absenceofsin_clue",
        "prep_label": "Printer Absenceofsin's Three-Bloc Coalition & Tariff Brief",
        "stages": [
            {
                "title": "BLOC 1/3: THE RIVER-BARGEES & QUAYSIDE WORKMEN",
                "desc": "Alderman Gilded-Tongue promises the merchant houses free rein on the wharves. Mairéad and the bargees shout: \"What will you do about the canal tolls?!\"",
                "opts": [
                    ("Propose the Unified River & Granary Charter: Abolish Petty Canal Tolls! (2d6)", 26),
                    ("Promise to dredge the southern delta timber-booms (2d6)", 16),
                    ("Tell the bargees to pay Bailiff Seekgrace's rates", -20),
                ],
            },
            {
                "title": "BLOC 2/3: THE AGRARIAN TENANTS & ORCHARDISTS",
                "desc": "Orchardist Goodseed and the farmhands press forward: \"The Kokeshi and the timber-crews are squeezing our land from both sides!\"",
                "opts": [
                    ("Pledge Grain Price-Supports, Fair Mill-Rates & Forest Border Protection! (2d6)", 26),
                    ("Promise a municipal grain-reserve for lean winters (2d6)", 18),
                    ("Side with Alderman Gilded-Tongue's enclosure of the commons", -20),
                ],
            },
            {
                "title": "BLOC 3/3: THE TOWN ARTISANS & CHANDLERS",
                "desc": "Chandler Hopewell and Clockmaker Watchandpray call out: \"And how do we protect honest Fluvius tradesmen from Kokeshi protection rackets?\"",
                "opts": [
                    ("Expose Gilded-Tongue's violet-ink Kokeshi banners & vow a Clean Guild Court! (2d6)", 26),
                    ("Promise lower market-stall rents in Counting House Square (2d6)", 16),
                    ("Dodge the question with vague platitudes", -15),
                ],
            },
        ],
    },
    "7c": {
        "track": "office",
        "header": "COUNTING HOUSE SQUARE — CAMPAIGN TREASURY & AUDIT",
        "prep_flag": "el_marked_coins_found",
        "prep_label": "Purged Kokeshi Marked Bribe-Coins from Subscription Chest",
        "stages": [
            {
                "title": "STEP 1/3: LAUNCHING THE CLEAN SUBSCRIPTION DRIVE",
                "desc": "To print manifestos and hire poll-watchers across every ward, your campaign needs a clean war-chest.",
                "opts": [
                    ("Organise a Grass-Roots Union & Guild Penny-Subscription! (2d6)", 24),
                    ("Contribute 20 Silver of your own hard-earned coin to the chest (2d6)", 22),
                    ("Pass the hat among Bailiff Seekgrace's tax-farmers", -18),
                ],
            },
            {
                "title": "STEP 2/3: THE KOKESHI POISON-PILL AUDIT!",
                "desc": "Alderman Gilded-Tongue's clerk suddenly demands a public inspection of your campaign chest, claiming you took illicit Syndicate silver!",
                "opts": [
                    ("Display the purged Violet-Marked Coins & expose Gilded-Tongue's plant! (2d6)", 28),
                    ("Open your double-entry ledger for Printer Absenceofsin's public audit (2d6)", 18),
                    ("Refuse to open the chest and look guilty", -22),
                ],
            },
            {
                "title": "STEP 3/3: DEPLOYING THE ELECTION-EVE PRESS RUN",
                "desc": "With your campaign chest verified clean, Printer Absenceofsin inks the great broadsheet press!",
                "opts": [
                    ("Print 5,000 'People's Tribune' Charters & hire Watch poll-guards! (2d6)", 24),
                    ("Distribute free hot cider and manifestos at the West Bridge (2d6)", 16),
                    ("Pocket half the campaign funds for yourself", -20),
                ],
            },
        ],
    },
    "7d": {
        "track": "office",
        "header": "RUINED WAYSTATION — THE SMOKE-FILLED BACKROOM",
        "prep_flag": "el_waystation_tube_found",
        "prep_label": "Hidden Hearth Speaking-Tube & K-44 Ballot-Wax Evidence",
        "stages": [
            {
                "title": "EXCHANGE 1/3: THE DIEWELL'S FORTY-SILVER OFFER",
                "desc": "In the candle-lit ruin on the Old Path, The Diewell slides a heavy 40-silver pouch and a stick of crimson 'K-44' ballot-wax across the stone table.",
                "opts": [
                    ("Angle the discussion toward the Hearth Speaking-Tube so witnesses hear every word! (2d6)", 26),
                    ("Keep a poker face and ask how the Kokeshi plan to swap the urns (2d6)", 20),
                    ("Grab the 40 silver eagerly and kiss the Syndicate ring", -15),
                ],
            },
            {
                "title": "EXCHANGE 2/3: THE BLACKMAIL DOSSIER",
                "desc": "The Diewell taps a leather folder: \"Refuse us, candidate, and our printers will flood Fluvius with forged tales of your past in Murum.\"",
                "opts": [
                    ("Counter-bluff by producing their own 'K-44' Crimson Wax matrix from the hearth! (2d6)", 28),
                    ("Stare The Diewell down with unshakeable civic reputation (2d6)", 18),
                    ("Flinch and beg them to burn the dossier", -20),
                ],
            },
            {
                "title": "EXCHANGE 3/3: SEALING YOUR ELECTION-EVE STANCE",
                "desc": "The Diewell rises into the ivy shadows: \"Decide now, Tribune—are you our partner, or our enemy at the polls tomorrow?\"",
                "opts": [
                    ("Refuse the bribe & lock in the recorded K-44 Ballot-Rigging Proof! (2d6)", 26),
                    ("Feign neutrality until you reach Returning Officer Standfast's hall (2d6)", 16),
                    ("Accept the 40s dirty money & corrupt pact (+40s, +1 Exposure Tell)", -10),
                ],
            },
        ],
    },
    "7e": {
        "track": "office",
        "header": "FLUVIUS GUILDHALL — THE GRAND ELECTION & POLL COUNT",
        "prep_flag": "clock_shim_fixed",
        "prep_label": "Fluvius Civic Clock-Tower Key & K-44 Wax Proof",
        "stages": [
            {
                "title": "POLL STAGE 1/3: THE DECIMAL CLOCK-TOWER BELL!",
                "desc": "Kokeshi thugs are blocking the West Canal Bridge to delay working voters while trying to ring the fast town clock-bell twenty minutes early!",
                "opts": [
                    ("Use Watchandpray's Clock-Tower Key to chime the true hour & keep polls open! (2d6)", 28),
                    ("Send Union & Watch volunteers to escort bridge voters at a run (2d6)", 18),
                    ("Let the polls close early while workers are still outside", -22),
                ],
            },
            {
                "title": "POLL STAGE 2/3: INSPECTING THE OAK BALLOT URNS!",
                "desc": "Returning Officer Standfast prepares to break the seals on the three ward urns—Wait! Urn #3 has a fresh smudge of crimson wax!",
                "opts": [
                    ("Expose the 'K-44' Kokeshi Wax Seal & recover the true 3rd Ward Urn! (2d6)", 28),
                    ("Demand a public hand-recount in front of the whole square (2d6)", 20),
                    ("Allow the tampered urn to be counted unchallenged", -25),
                ],
            },
            {
                "title": "POLL STAGE 3/3: THE TRIBUNE'S VICTORY ADDRESS!",
                "desc": "The true tallies are read aloud from the balcony—your coalition of bargees, farmers, and artisans carries Fluvius by a landslide!",
                "opts": [
                    ("Proclaim the Independent People's Magistracy of Fluvius & Murum! (2d6)", 24),
                    ("Appoint Returning Officer Standfast to head an anti-corruption bench (2d6)", 18),
                    ("Give a quiet, hesitant speech", -5),
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # TRACK 8: WALLMAKER / KOKESHI SYNDICATE (8A, 8B, 8C, 8D, 8E)
    # ------------------------------------------------------------------
    "8a": {
        "track": "syndicate",
        "header": "THE OLD PATH — ESTABLISHING THE KOKESHI DEAD-DROPS",
        "prep_flag": "ancient_blueprint_bonus",
        "prep_label": "Old Path Sapper Catacombs Explored",
        "stages": [
            {
                "title": "STAGE 1/3: CHALKING THE CLIFFSIDE MILESTONES",
                "desc": "Moving along the mist-shrouded Old Path, you must mark the three hollow boundary cairns with the Kokeshi 4-beat mason's cipher.",
                "opts": [
                    ("Carve the cipher beneath the lichen using sapper's shorthand! (2d6)", 25),
                    ("Wait for the Watch patrol to pass before chalking the stone (2d6)", 18),
                    ("Scrawl large white chalk marks visible from the highway", -18),
                ],
            },
            {
                "title": "STAGE 2/3: THE SUBTERRANEAN RELAY VAULT",
                "desc": "At the Ruined Waystation, you link the surface dead-drop to the ancient sapper tunnels beneath the cellar flagstones.",
                "opts": [
                    ("Use the Sapper Catacombs tunnel-map to rig a hidden pulley drop! (2d6)", 26),
                    ("Oil the stone trough lock-box and set a trip-cord (2d6)", 18),
                    ("Leave the cipher packets in an unguarded saddlebag", -18),
                ],
            },
            {
                "title": "STAGE 3/3: THE BREATHLESS COURIER'S ALERT!",
                "desc": "A bloodied Kokeshi rider stumbles into the Waystation: \"Black Dog's outlaws just ambushed our disguised payroll coach at the Muddy Hollow!\"",
                "opts": [
                    ("Tend the courier's wound & extract the exact ambush description! (2d6)", 22),
                    ("Dispatch shadow-runners to watch the river-fences in Fluvius (2d6)", 18),
                    ("Blame the courier and send him away", -12),
                ],
            },
        ],
    },
    "8b": {
        "track": "syndicate",
        "header": "THE NEW ROAD & QUAYSIDE — THE PAYROLL MANHUNT",
        "prep_flag": "el_hollow_strongbox_found",
        "prep_label": "Muddy Hollow Strongbox Lock & Inside-Job Bootprints",
        "stages": [
            {
                "title": "STAGE 1/3: READING THE AMBUSH SCENE AT MUDDY HOLLOW",
                "desc": "Examining the splintered coach ruts on the New Road, how do you reconstruct how Black Dog's gang cracked the iron strongbox so fast?",
                "opts": [
                    ("Match the sheared lock-plate to the Inside-Outrider's bootprints! (2d6)", 26),
                    ("Follow the trail of spilled oats and red-clay hoofprints (2d6)", 18),
                    ("Wander blindly into the roadside gorse", -15),
                ],
            },
            {
                "title": "STAGE 2/3: CORNERING EOGHAN THE RIVER-FENCE",
                "desc": "Tracking the crooked outrider to the back room behind the Fluvius quayside, you catch him bargaining over the stolen Kokeshi payroll!",
                "opts": [
                    ("Slam the sheared Strongbox Lock on the table & tap the Mason's Code! (2d6)", 28),
                    ("Overpower the outrider's bodyguard in the narrow alley (2d6)", 20),
                    ("Offer to buy back the Syndicate's own stolen silver", -18),
                ],
            },
            {
                "title": "STAGE 3/3: RECLAIMING THE BLACK-IRON SEAL",
                "desc": "Terrified of the Diewell's wrath, the fence surrenders the heavy **Black-Iron Kokeshi Seal** and the remaining payroll pouch!",
                "opts": [
                    ("Recover the Seal + 25s Payroll & turn the fence into a permanent asset! (2d6)", 24),
                    ("Seize the Seal and leave a Kokeshi warning mark on the door (2d6)", 18),
                    ("Let the outrider keep half the silver", -12),
                ],
            },
        ],
    },
    "8c": {
        "track": "syndicate",
        "header": "FLUVIUS GRANARY WHARF — ARMING THE SCAB CONVOY",
        "prep_flag": "el_eoghan_clue",
        "prep_label": "Granary Wharf Teamster & Sunken Lane Reconnaissance",
        "stages": [
            {
                "title": "STAGE 1/3: MUSTERING CORBAN'S WAGON CREWS",
                "desc": "At the Granary Wharf, the Caligo quarry drivers are hesitating to drive the grain-wains against Joyinsorrow's Union picket line!",
                "opts": [
                    ("Flash the recovered Black-Iron Kokeshi Seal & double the lead drivers' hazard pay! (2d6)", 26),
                    ("Issue padded leather gauntlets and oak wheel-spokes to the escort (2d6)", 18),
                    ("Threaten the drivers without paying them a penny", -15),
                ],
            },
            {
                "title": "STAGE 2/3: COUNTERING THE SUNKEN LANE FLOOD-TRAP",
                "desc": "Your outriders report that Union strikers have opened the irrigation sluice in the Sunken Lane to bog down the heavy wagons!",
                "opts": [
                    ("Lay broad timber-planks across the mire & winch the wains up the bank! (2d6)", 26),
                    ("Divert the convoy along the eastern orchard terrace track (2d6)", 20),
                    ("Lash the mules straight into the axle-deep red clay", -20),
                ],
            },
            {
                "title": "STAGE 3/3: PRESSING THE CROSSROADS BARRICADE",
                "desc": "With Watch Sergeant Beornraed's lancers watching from the ridge, your convoy hits the Fluvius Farm Crossroads!",
                "opts": [
                    ("Keep blades sheathed & use disciplined wedge-barges to force a wagon-lane! (2d6)", 24),
                    ("Bribe the Bailiff's clerk to serve an emergency road-warrant (2d6)", 18),
                    ("Draw illegal daggers in front of the Watch lancers", -25),
                ],
            },
        ],
    },
    "8d": {
        "track": "syndicate",
        "header": "RUINED WAYSTATION — CORNERING THE CANDIDATE",
        "prep_flag": "el_waystation_tube_found",
        "prep_label": "Waystation Speaking-Tube & Gilded-Tongue Leverage",
        "stages": [
            {
                "title": "EXCHANGE 1/3: LAYING THE SILVER & THE LEAD ON THE TABLE",
                "desc": "Inside the Ruined Waystation, you sit opposite the Public Office candidate with 40 silver in one hand and a blackmail dossier in the other.",
                "opts": [
                    ("Present the candidate's hidden debt-chits & offer 40s for quiet compliance! (2d6)", 26),
                    ("Promise to deliver all three guild wards via K-44 ballot-wax (2d6)", 20),
                    ("Bluster crudely without showing concrete leverage", -15),
                ],
            },
            {
                "title": "EXCHANGE 2/3: DETECTING THE CANDIDATE'S WIRE-TRAP",
                "desc": "You notice the candidate glancing subtly toward the ivy-covered chimney hearth while trying to draw you into a confession!",
                "opts": [
                    ("Use your Waystation recon to plug the Hearth Speaking-Tube & flip the trap! (2d6)", 28),
                    ("Speak entirely in Wallmaker surveyor's cant so no witness can quote you (2d6)", 20),
                    ("Boast loudly about the Syndicate's ballot-stuffing plan", -22),
                ],
            },
            {
                "title": "EXCHANGE 3/3: LOCKING IN THE SYNDICATE COMPACT",
                "desc": "Outmanoeuvred in the shadows, the candidate signs the unwritten understanding and vacates the room.",
                "opts": [
                    ("Secure the duplicate Guildhall Vault key-impression & K-44 wax! (2d6)", 25),
                    ("Post Kokeshi lookouts around the Fluvius Clock-Tower (2d6)", 18),
                    ("Leave the blackmail papers behind on the table", -15),
                ],
            },
        ],
    },
    "8e": {
        "track": "syndicate",
        "header": "FLUVIUS GUILDHALL VAULT — THE BALLOT-URN HEIST",
        "prep_flag": "clock_shim_fixed",
        "prep_label": "Fluvius Civic Clock-Tower Key & Vault Key-Impression",
        "stages": [
            {
                "title": "HEIST STAGE 1/3: THE DECIMAL CLOCK-TOWER DIVERSION!",
                "desc": "Returning Officer Standfast guards the sealed oak ballot urns inside the Guildhall. You need a distraction to draw the Watch outside!",
                "opts": [
                    ("Use the Clock-Tower Key to strike the curfew chime early & clear the square! (2d6)", 28),
                    ("Light a smoky tar-barrel behind the Laundry Steps (2d6)", 18),
                    ("Try to pick the vault door while Standfast is looking right at you", -22),
                ],
            },
            {
                "title": "HEIST STAGE 2/3: SWAPPING THE WAX-SEALED URNS!",
                "desc": "Slipping into the shadowed Guildhall vault, you have sixty seconds to swap the three ward urns for the Kokeshi-stuffed urns!",
                "opts": [
                    ("Match the exact weight & stamp fresh crimson seals with the K-44 matrix! (2d6)", 28),
                    ("Use your Stealth & Master Wallmaker touch to slide the false stonework (2d6)", 22),
                    ("Crack the wax seal clumsily with a dagger", -22),
                ],
            },
            {
                "title": "HEIST STAGE 3/3: THE SHADOW COUP COMPLETE!",
                "desc": "Standfast returns to the vault, inspects the unbroken crimson seals with his loupe, and reads out a landslide victory for the Syndicate's slate!",
                "opts": [
                    ("Melt into the crowd & collect your 50-silver Syndicate bonus! (2d6)", 24),
                    ("Lock the true ballot tallies inside the Wallmaker blackmail safe (2d6)", 18),
                    ("Brag openly in the taproom about rigging the vote", -20),
                ],
            },
        ],
    },
}


def init_election_minigame(player, mission_code):
    """Initializes the unified 680x480 Pop-Out Window for any Track 7 or Track 8 mission."""
    # Check if the player delved the Old Path Sapper Catacombs for 8A bonus
    if "ancient sapper's blueprint" in player.get("inventory", []) or "old_path_catacombs" in player.get("dungeons_cleared", []):
        player["ancient_blueprint_bonus"] = True

    scen = ELECTION_SCENARIOS[mission_code]
    player["el_code"] = mission_code
    player["el_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["el_stage"] = 0

    base_prog = (
        35
        + (player.get("charisma", 0) * 2)
        + (player.get("influence", 0) * 2)
        + (player.get("stealth", 0) * 2)
    )
    if player.get(scen["prep_flag"]):
        base_prog += 18
    if "sage's charter" in player.get("inventory", []) and mission_code == "7a":
        base_prog += 15
    if "crown of the first castellan" in player.get("inventory", []):
        base_prog += 10

    player["el_progress"] = min(68, base_prog)
    player["el_feedback"] = (
        f"Operation Underway: {scen['header']}. "
        "Complete all 3 stages and push Leverage/Support to 75%+ (each choice rolls 2d6 + your preparation & twists)!"
    )
    return player, player["el_feedback"], "MINIGAME_ELECTION"


def election_action(choice_idx, player):
    """Processes a stage choice (0, 1, or 2) in MINIGAME_ELECTION with 2d6 rolls & twists."""
    code = player.get("el_code", "7a")
    scen = ELECTION_SCENARIOS[code]

    if player.get("el_phase") == "RESULT":
        return conclude_election_minigame(player)

    st_idx = player.get("el_stage", 0)
    st_data = scen["stages"][st_idx]
    opt_label, base_delta = st_data["opts"][choice_idx]

    swing, prefix, twist_str = roll_election_2d6_twist(player, track_kind=scen["track"])
    has_prep = player.get(scen["prep_flag"], False) or (code == "7a" and "sage's charter" in player.get("inventory", []))
    prep_bonus = 6 if (choice_idx == 0 and has_prep) else 0

    # Handle special 7C self-funding or 7D corrupt bribe choices
    if code == "7c" and st_idx == 0 and choice_idx == 1:
        if player.get("silver", 0) >= 20:
            player["silver"] -= 20
        else:
            base_delta = -10
    elif code == "7d" and st_idx == 2 and choice_idx == 2:
        player["silver"] += 40
        player["kokeshi_deal_accepted"] = True
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
    elif code == "7d" and st_idx == 2 and choice_idx == 0:
        player["kokeshi_bribe_recorded"] = True

    if choice_idx == 0 and not has_prep and base_delta >= 24:
        actual_delta = 12 + (swing // 2)
        note = f"You attempt '{opt_label.split(' (')[0]}', improvising on the fly without full field preparation!"
    else:
        actual_delta = base_delta + prep_bonus + (swing // 2)
        note = f"Executed: {opt_label.split(' (')[0]}!"

    player["el_progress"] = max(0, min(100, player.get("el_progress", 40) + actual_delta))
    full_msg = f"{prefix}{note} ({'+' if actual_delta >= 0 else ''}{actual_delta}%){twist_str}"

    if st_idx >= 2:
        player["el_phase"] = "RESULT"
        tag = "TRIUMPH!" if player["el_progress"] >= 75 else "CONTESTED OUTCOME!"
        player["el_feedback"] = f"{full_msg} — [{tag} ({player['el_progress']}%)] Click [Conclude Mission >>]!"
        return player, player["el_feedback"], "MINIGAME_ELECTION"

    player["el_stage"] = st_idx + 1
    player["el_feedback"] = full_msg
    return player, None, "MINIGAME_ELECTION"


def conclude_election_minigame(player):
    code = player.get("el_code", "7a")
    prog = player.get("el_progress", 0)
    player["active_ch2_mission"] = None

    step_num = ord(code[1]) - ord('a') + 1
    player["ch2_mission_step"] = step_num + 1

    success = (prog >= 75)
    gain = 22 if success else 10
    player["position_strength"] = min(100, player.get("position_strength", 0) + gain)
    if not success:
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1

    if code == "8b" and success:
        player["silver"] += 25

    # Check if this was the Grand Election / Heist Finale (7E or 8E)!
    if code == "7e":
        clean_win = (prog >= 70 and not player.get("kokeshi_deal_accepted"))
        player.setdefault("ch3_world_bits", {})["track_7"] = 1 if clean_win else 0
        if clean_win:
            player.setdefault("ch3_world_bits", {})["track_8"] = 0
            player["reputation"] = player.get("reputation", 0) + 3
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: LANDSLIDE FOR THE PEOPLE'S TRIBUNE! \n"
                "=========================================================\n"
                "You expose the Kokeshi 'K-44' wax ballot-rigging plot before the entire town and sweep all three wards of Fluvius as an independent People's Tribune!\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
            )
        else:
            log = (
                "=== MISSION COMPLETE: A COMPROMISED MAGISTRACY ===\n"
                "Between Kokeshi ballot-stuffing and backroom compromises, you take office bound to the shadow syndicate's strings as war breaks out!"
            )
        return player, log, "CHAPTER_2_COMPLETE"

    if code == "8e":
        heist_win = (prog >= 70)
        player.setdefault("ch3_world_bits", {})["track_8"] = 1 if heist_win else 0
        if heist_win:
            player.setdefault("ch3_world_bits", {})["track_7"] = 0
            player["silver"] += 50
            modify_faction(player, "faction_wallmakers", 3)
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: THE KOKESHI SHADOW COUP!         \n"
                "=========================================================\n"
                "Without a single guard wiser, your crimson-sealed ballot urns are certified by Returning Officer Standfast! "
                "The Wallmaker / Kokeshi Syndicate now secretly owns the civilian magistracy of Fluvius (+50 Silver)!\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
            )
        else:
            player["exposure_tells"] = player.get("exposure_tells", 0) + 2
            log = (
                "=== MISSION FAILED: BALLOT SWAP EXPOSED! ===\n"
                "A cracked wax seal alerts Returning Officer Standfast and the Watch! You escape across the slate roofs, but the Syndicate's election plot collapses!"
            )
        return player, log, "CHAPTER_2_COMPLETE"

    # Next-step hints without coordinate spoilers
    if code == "7a":
        nxt = "Travel south to **Fluvius Town** and speak with **Returning Officer Standfast** in the Counting House Square (and question **Printer Absenceofsin** by the Clock-Tower) for the **7B Hustings Debate**!"
    elif code == "7b":
        nxt = "**Search** the **Counting House Square** to audit your campaign subscription chest, then speak to **Returning Officer Standfast** for **7C Campaign Financing**!"
    elif code in ("7c", "8c"):
        nxt = "A hooded courier whispers that **The Diewell** awaits you at the **Ruined Waystation on the Old Path** (**Search** behind the Waystation hearth before beginning the **7D/8D Backroom Meeting**)!"
    elif code in ("7d", "8d"):
        nxt = "Visit **Clockmaker Watchandpray** at the **Fluvius Civic Clock-Tower** to inspect the tampered pendulum escapement, then speak to **Returning Officer Standfast** for the **Grand Election Finale**!"
    elif code == "8a":
        nxt = "Question **Eoghan the River-Fence** at the Barge & Anchor Taproom and **search** the **Muddy Hollow on the New Road** before speaking to **The Diewell** to launch the **8B Payroll Manhunt**!"
    elif code == "8b":
        nxt = "Travel to the **Granary Wharf in Fluvius Town** and speak to **The Diewell** (or Wagon-Boss Corban) to organise and arm the **8C Strikebreaker Convoy**!"
    else:
        nxt = "Continue your campaign!"

    log = (
        f"=== MISSION {code.upper()} COMPLETE (+{gain}% Position Strength | Score: {prog}%)! ===\n"
        f"• Next Step: {nxt}"
    )
    return player, log, "MAIN"


def draw_election_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Tracks 7 and 8."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    CIVIC_PURPLE = (95, 50, 130)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    code = player.get("el_code", "7a")
    scen = ELECTION_SCENARIOS[code]

    title = font_bold.render(scen["header"], True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    prog = player.get("el_progress", 40)
    lbl_str = "Public Support & Mandate:" if scen["track"] == "office" else "Syndicate Leverage & Control:"
    screen.blit(font_bold.render(f"{lbl_str} {prog}% (Target: 75%+)", True, CIVIC_PURPLE), (85, 80))

    p_bar = pygame.Rect(430, 80, 285, 18)
    pygame.draw.rect(screen, (40, 35, 35), p_bar, border_radius=4)
    if prog > 0:
        col = (45, 135, 65) if prog >= 75 else CIVIC_PURPLE
        pygame.draw.rect(screen, col, (430, 80, int(285 * (prog / 100.0)), 18), border_radius=4)
    tx = 430 + int(285 * 0.75)
    pygame.draw.line(screen, (255, 255, 255), (tx, 78), (tx, 100), 2)
    pygame.draw.rect(screen, CLOCK_BLACK, p_bar, width=1, border_radius=4)

    st_idx = min(2, player.get("el_stage", 0))
    st_data = scen["stages"][st_idx]

    s_box = pygame.Rect(85, 112, 630, 140)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 120))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 146, 600, 70), CLOCK_BLACK, max_lines=3)

    has_prep = player.get(scen["prep_flag"], False) or (code == "7a" and "sage's charter" in player.get("inventory", []))
    prep_txt = (
        f"Field Intelligence: [{scen['prep_label']} SECURED!]"
        if has_prep else
        f"Field Intelligence: Unverified (Explore to uncover: {scen['prep_label']})"
    )
    screen.blit(font.render(prep_txt[:78], True, (45, 125, 60) if has_prep else TATE_RED), (100, 226))

    fb_box = pygame.Rect(85, 262, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("el_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 5. UPGRADED DIALOGUE HANDLERS FOR RETURNING OFFICER (7) & THE DIEWELL (8)
# =========================================================================
def get_returning_officer_election_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []

    if route == "Run for Public Office (50s)":
        if step == 2:
            opts.append("Mission: Briefing on the Fluvius Hustings Debate" if not player.get("m7b_briefed") else "Mission: Step onto the Hustings Platform (Begin 7B Debate!)")
        elif step == 3:
            opts.append("Mission: Briefing on the Campaign Subscription Audit" if not player.get("m7c_briefed") else "Mission: Open the Subscription Chest & Audit Funds (7C)!")
        elif step == 5:
            opts.append("Mission: Open the Ballot Urns & Contest the Grand Election (7E)!")

    if route == "Join Wallmaker Syndicate" and step == 5:
        opts.append("Mission: Infiltrate the Guildhall Vault & Swap the Ballot Urns (8E)!")

    opts.extend(["Ask about the upcoming Regional Election", "Leave"])
    return opts


def resolve_returning_officer_election(choice, player):
    if choice == "Leave":
        return player, "Returning Officer Standfast guards the wax-sealed oak ballot urns.", "MAIN"

    if choice == "Ask about the upcoming Regional Election":
        return player, (
            "Returning Officer Standfast adjusts his spectacles.\n"
            "\"Three wards vote in the Fluvius Magistracy election: the **River-Bargees**, the **Agrarian Tenants**, and the **Town Artisans**. "
            "The polls close on the stroke of the **Civic Clock-Tower bell**!\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Briefing on the Fluvius Hustings Debate":
        player["m7b_briefed"] = True
        return player, (
            "=== MISSION: THE THREE-BLOC HUSTINGS DEBATE ===\n"
            "Returning Officer Standfast gestures toward the hustings platform in Counting House Square.\n"
            "\"Your rival, **Alderman Gilded-Tongue**, is already promising low duties to the merchant houses. "
            "Before you take the platform, speak with **Printer Absenceofsin** near the Civic Clock-Tower, **Mairéad** at the Southern Timber-Booms, and **Alderman Gilded-Tongue** himself to see who is funding his campaign!\""
        ), "MAIN"

    if choice.startswith("Mission: Step onto the Hustings Platform"):
        return init_election_minigame(player, "7b")

    if choice == "Mission: Briefing on the Campaign Subscription Audit":
        player["m7c_briefed"] = True
        return player, (
            "=== MISSION: CAMPAIGN FINANCING & THE BRIBE AUDIT ===\n"
            "\"Every candidate's subscription chest must pass a public audit before the election-eve broadsheets are printed,\" Standfast warns.\n"
            "\"**Search** around **Counting House Square** right here to inspect your collection box for any planted syndicate coins before we open the audit!\""
        ), "MAIN"

    if choice.startswith("Mission: Open the Subscription Chest"):
        return init_election_minigame(player, "7c")

    if choice.startswith("Mission: Open the Ballot Urns"):
        return init_election_minigame(player, "7e")

    if choice.startswith("Mission: Infiltrate the Guildhall Vault"):
        return init_election_minigame(player, "8e")

    return player, "Error.", "MAIN"


def get_diewell_election_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []

    if route == "Join Wallmaker Syndicate":
        if step == 1:
            opts.append("Mission: Briefing on the Old Path Dead-Drops & Sapper Tunnels" if not player.get("m8a_briefed") else "Mission: Chalk the Cipher & Link the Waystation Dead-Drops (8A)!")
        elif step == 2:
            opts.append("Mission: Briefing on the Robbed Kokeshi Payroll Coach" if not player.get("m8b_briefed") else "Mission: Track the Payroll Robbers & Shakedown the Fence (8B)!")
        elif step == 3:
            opts.append("Mission: Briefing on the Granary Wharf Scab Convoy" if not player.get("m8c_briefed") else "Mission: Marshal & Escort the Scab Convoy to the Crossroads (8C)!")
        elif step == 4:
            opts.append("Mission: Briefing on the Backroom Candidate Trap" if not player.get("m8d_briefed") else "Mission: Corner the Public Office Candidate in the Backroom (8D)!")

    if route == "Run for Public Office (50s)" and step == 4:
        opts.append("Mission: Briefing on the Backroom Syndicate Meeting" if not player.get("m7d_briefed") else "Mission: Enter the Smoke-Filled Backroom with The Diewell (7D)!")

    opts.extend([
        "Ask about the Old Path & Smuggling Routes",
        "Buy Black-Market Rope (15s)",
        "Buy Lockpick Crowbar (15s)",
        "Leave",
    ])
    return opts


def resolve_diewell_election(choice, player):
    if choice == "Leave":
        return player, "The Diewell melts back into the ivy shadows of the Ruined Waystation.", "MAIN"

    if choice == "Ask about the Old Path & Smuggling Routes":
        return player, (
            "\"Mind the rotted rope-bridge at the river crossing—it won't hold more than 15 lbs of gear unless reinforced. "
            "And if you **search** the flagstones right here in the Ruined Waystation, you'll find the steps down into the **Old Path Sapper Catacombs**.\""
        ), "NPC_DIALOGUE"

    if choice == "Buy Black-Market Rope (15s)":
        if player["silver"] >= 15:
            player["silver"] -= 15
            player["inventory"].append("rope")
            return player, f"You hand over 15 silver and receive a coil of strong hemp rope. (Silver: {player['silver']}s)", "NPC_DIALOGUE"
        return player, "\"Coin first, friend. 15 silver.\"", "NPC_DIALOGUE"

    if choice == "Buy Lockpick Crowbar (15s)":
        if player["silver"] >= 15:
            player["silver"] -= 15
            player["inventory"].append("iron dagger")
            return player, f"You pay 15 silver for a heavy prying-dagger. (Silver: {player['silver']}s)", "NPC_DIALOGUE"
        return player, "\"15 silver, no credit.\"", "NPC_DIALOGUE"

    if choice == "Mission: Briefing on the Old Path Dead-Drops & Sapper Tunnels":
        player["m8a_briefed"] = True
        return player, (
            "=== MISSION: THE OLD PATH DEAD-DROPS & SAPPER CATACOMBS ===\n"
            "The Diewell hands you a piece of yellow mason's chalk.\n"
            "\"Before we can move our election silver into Fluvius, we must secure the courier dead-drops along the Old Path and link them to the **Old Path Sapper Catacombs** directly beneath this Ruined Waystation.\"\n"
            "\"Use **Action -> Search** right here to delve the **Sapper Catacombs Dungeon** for the **Ancient Sapper's Blueprint** first—then speak to me to chalk the cipher route!\""
        ), "MAIN"
    if choice.startswith("Mission: Chalk the Cipher") or choice.startswith("Mission: Establish Old Path"):
        return init_election_minigame(player, "8a")

    if choice == "Mission: Briefing on the Robbed Kokeshi Payroll Coach":
        player["m8b_briefed"] = True
        return player, (
            "=== MISSION: THE STOLEN PAYROLL MANHUNT ===\n"
            "\"Black Dog's highwaymen ambushed our disguised payroll carriage on the **New Road Muddy Hollow** and stole our **Black-Iron Kokeshi Seal**!\"\n"
            "\"Travel to the **Muddy Hollow on the New Road** and **search** the ditch for the strongbox lock-plate, and question **Eoghan the River-Fence** at the Barge & Anchor Taproom in Fluvius before launching the manhunt!\""
        ), "MAIN"
    if choice.startswith("Mission: Track the Payroll Robbers") or choice.startswith("Mission: Track the Outlaw"):
        return init_election_minigame(player, "8b")

    if choice == "Mission: Briefing on the Granary Wharf Scab Convoy":
        player["m8c_briefed"] = True
        return player, (
            "=== MISSION: ARMING THE SCAB CONVOY ===\n"
            "\"The farm strike is choking our grain barges. Go to the **Granary Wharf in Fluvius Town** and check on **Wagon-Boss Corban** and the **Sunken Sluice-Gate Lane**—then give the word to march the strikebreaker convoy to the crossroads!\""
        ), "MAIN"
    if choice.startswith("Mission: Marshal & Escort") or choice.startswith("Mission: Organise & Arm"):
        return init_election_minigame(player, "8c")

    if choice in ("Mission: Briefing on the Backroom Candidate Trap", "Mission: Briefing on the Backroom Syndicate Meeting"):
        player["m8d_briefed"] = True
        player["m7d_briefed"] = True
        return player, (
            "=== MISSION: THE SMOKE-FILLED BACKROOM ===\n"
            "\"The backroom parley between the Public Office campaign and the Kokeshi Syndicate takes place right here in the Ruined Waystation.\"\n"
            "\"(Tip: If you haven't already, use **Action -> Search** to check behind the Waystation hearth for hidden acoustic tubes and K-44 ballot-wax before sitting down at the table!)\""
        ), "MAIN"
    if choice.startswith("Mission: Corner the Public Office"):
        return init_election_minigame(player, "8d")
    if choice.startswith("Mission: Enter the Smoke-Filled") or choice.startswith("Mission: Accept Kokeshi") or choice.startswith("Mission: Refuse the Bribe"):
        return init_election_minigame(player, "7d")

    return player, "Error.", "MAIN"


# =========================================================================
# MODULE REGISTRATION (HANDLERS)
# =========================================================================
HANDLERS = {
    "returning_officer":    (get_returning_officer_election_options, resolve_returning_officer_election),
    "diewell":              (get_diewell_election_options, resolve_diewell_election),
    "gilded_tongue":        (get_gilded_tongue_options, resolve_gilded_tongue),
    "absenceofsin":         (get_absenceofsin_options, resolve_absenceofsin),
    "eoghan":               (get_eoghan_options, resolve_eoghan),
}
