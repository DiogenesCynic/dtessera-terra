import random
import pygame
import game_data as db
import ch2_dungeons
import companions_engine
from mechanics import modify_faction, advance_time, execute_ch2_mission
from ui_components import draw_fitted_text


# =========================================================================
# 1. SHARED 2d6 HARBOUR VARIANCE, WINDFALLS & FRICTION
# =========================================================================
def roll_parvus_2d6_twist(player, track_kind="fai"):
    """
    Rolls 2d6 for Parvus missions (-10% to +10% swing) plus a 30% chance of a Coastal Windfall or Friction twist!
    Returns (swing_int, prefix_str, twist_str).
    """
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    swing = (d1 + d2 - 7) * 2
    prefix = f"[Roll {d1}+{d2}={d1+d2}] "
    twist_str = ""

    if random.random() < 0.30:
        if track_kind == "fai":
            twists = [
                ("WINDFALL: Sympathetic rope-spinners tip a barrel of Stockholm tar across the cobbles, slowing the Watch patrol! (+8% Progress)", 8),
                ("WINDFALL: A dockside sympathiser slips 8 silver into the strike-fund tin! (+8s)", 5),
                ("FRICTION: A sudden squall off the Dtessera Sea dampens your oilskin satchels! (-6% Progress)", -6),
            ]
        elif track_kind == "crown":
            twists = [
                ("WINDFALL: A customs cutter signals from the mole, confirming your suspect's barge registry! (+8% Progress)", 8),
                ("WINDFALL: You confiscate a smuggler's dead-drop pouch containing 10 silver! (+10s)", 6),
                ("FRICTION: Thick harbour sea-fog rolls across the quays, obscuring your tail on the suspect! (-6% Progress)", -6),
            ]
        else:
            twists = [
                ("WINDFALL: A merchant captain pays a 12-silver priority crane fee to the Guild chest! (+12s, +6% Progress)", 6),
                ("WINDFALL: High tide lifts the brigantines cleanly level with the stone mole! (+8% Progress)", 8),
                ("FRICTION: A snapped hemp hawser whips across the crane-deck in the gale! (-6% Progress)", -6),
            ]
        t_text, mod = random.choice(twists)
        swing += mod
        if "+8s" in t_text:
            player["silver"] += 8
        elif "+10s" in t_text:
            player["silver"] += 10
        elif "+12s" in t_text:
            player["silver"] += 12
        twist_str = f" [{t_text}]"

    return swing, prefix, twist_str


# =========================================================================
# 2. DISCOVERABLE PARVUS NPCS (RONAN, MAEVE, ALDRED)
# =========================================================================
def get_ronan_options(player):
    opts = ["Ask about the work at the Rope-Walk"]
    step = player.get("ch2_mission_step", 1)
    if step == 1:
        opts.insert(0, "Ask about the new dockside recruits & syndicalist passwords")
        opts.insert(1, "Ask why the Guild Gantry Crane on the harbour-front is jammed")
    elif step == 3:
        opts.insert(0, "Ask which ships arrived at the Bonded Slipway last night")
    if player.get("active_companion") != "padraig_brawler":
        opts.append("Hire Rigger Padraig as Road Escort (12s, 3 Days)")
    opts.append("Leave")
    return opts


def resolve_ronan(choice, player):
    if choice == "Leave":
        return player, "Rigger Ronan twists three tarred hemp strands into a stout hawser.", "MAIN"

    if choice == "Ask about the work at the Rope-Walk":
        return player, (
            "Rigger Ronan wipes Stockholm tar from his knuckles.\n"
            "\"Every cable and shroud in the Parvus fleet is spun in these sheds, comrade—though between the Crown spies and the Kokeshi crimps, a man has to watch his tongue.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the new dockside recruits & syndicalist passwords":
        player["parvus_ronan_recruits_clue"] = True
        return player, (
            "Ronan leans in close over the tar-boiler.\n"
            "\"Listen sharp: every true F.A.I. rigger in Parvus knows that our password comes from **Proudhon's first chapter**, and our hands are stained black up to the wrist with **Stockholm pine-tar**.\"\n"
            "\"There's a fellow named **Garrick** hanging round the sheds claiming to be a veteran cable-spinner—but his palms are as pink and uncalloused as a customs clerk's, and his boots have Crown guard-wax on the heels!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask why the Guild Gantry Crane on the harbour-front is jammed":
        player["parvus_crane_clue"] = True
        return player, (
            "Ronan snorts.\n"
            "\"The crane isn't broken by accident! A Kokeshi saboteur wedged a **cast-iron shim into the upper worm-gear** on the Harbour-Front mole, "
            "and the riggers walked out because the Guild factor docked their danger-pay. Pull that iron shim out of the crane gear and promise the riggers their fair danger-rate, and that crane will lift ten tons before noon!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask which ships arrived at the Bonded Slipway last night":
        player["parvus_ship_draft_clue"] = True
        return player, (
            "Ronan squints toward the harbour mole.\n"
            "\"Three brigantines berthed at dawn: the *Sea-Swallow*, the *Cormorant*, and the *Gilded Gull*. "
            "The *Cormorant*'s manifest claims she's carrying light cork and feathers—yet she's sitting two feet below her Plimsoll water-mark! "
            "Only heavy crates of Kokeshi muskets and lead shot make a hull ride that deep!\""
        ), "NPC_DIALOGUE"

    if choice == "Hire Rigger Padraig as Road Escort (12s, 3 Days)":
        return companions_engine.hire_temporary_companion(player, "padraig_brawler", 12, 3)

    return player, "Error.", "MAIN"


def get_maeve_options(player):
    opts = ["Buy a Tot of Spiced Navy Rum (2s)"]
    step = player.get("ch2_mission_step", 1)
    if step == 2:
        opts.insert(0, "Ask about the forged Watch Billeting flyers & counterfeit steel")
    elif step == 3:
        opts.insert(0, "Ask about the midnight meeting at the Kokeshi Bonded Warehouses")
    elif step == 5:
        opts.insert(0, "Ask about the rooftop approaches to the Upper Parvus Promenade")
    opts.append("Leave")
    return opts


def resolve_maeve(choice, player):
    if choice == "Leave":
        return player, "Maeve polishes a brass ship's bell behind the bar of The Salted Anchor.", "MAIN"

    if choice == "Buy a Tot of Spiced Navy Rum (2s)":
        if player["silver"] < 2:
            return player, "\"Two silver for navy rum, sailor!\"", "NPC_DIALOGUE"
        player["silver"] -= 2
        player["thirst"] = min(100, player.get("thirst", 100) + 25)
        return player, "You toss back a fiery tot of spiced navy rum (+25 Thirst).", "NPC_DIALOGUE"

    if choice == "Ask about the forged Watch Billeting flyers & counterfeit steel":
        player["parvus_maeve_step2_clue"] = True
        return player, (
            "Maeve leans across the rum-stained counter.\n"
            "\"Two secrets for the price of one, friend: first, the F.A.I. printers are stamping their forged Watch Billeting Orders using **blue gall-ink on un-watermarked rag paper**—whereas true Customs House warrants always bear the **Crown Anchor watermark** and red sealing-wax.\"\n\n"
            "\"Second, a Kokeshi fence named **Vane** was in my back booth an hour ago bragging that he swapped the Artisans' Guild's pure Swedish pig-iron at the **Dry-Dock Foundry** for brittle slag-iron, and hid the stolen Guild bullion inside the **quench-trough false bottom**!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the midnight meeting at the Kokeshi Bonded Warehouses":
        player["parvus_maeve_step3_clue"] = True
        return player, (
            "Maeve lowers her voice.\n"
            "\"Tonight at the **Kokeshi Bonded Warehouses** on the eastern quay, the Syndicate bosses are inspecting a cache of smuggled muskets in the upper loft—while an F.A.I. squad plans to slip in through the **sea-side slipway chute** at the exact same hour. "
            "Whoever controls the slipway grate and the warehouse main doors controls the whole trap!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the rooftop approaches to the Upper Parvus Promenade":
        player["parvus_maeve_step5_clue"] = True
        return player, (
            "Maeve glances up toward the cliffside tiers.\n"
            "\"During the Harbour Festival, Mayor Holdfast always steps out onto the **Promenade Balcony** when the bronze harbour-bell tolls the third stroke. "
            "The Crown guards watch the front stairs, but the **gilded astrolabe dome on the Guildhall roof** has a direct sightline right onto the balcony rail!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_aldred_options(player):
    opts = ["Ask about the Dry-Dock & Iron Foundry"]
    step = player.get("ch2_mission_step", 1)
    if step in (1, 2):
        opts.insert(0, "Ask about the quality of the hull-plates & foundry pig-iron")
    elif step == 5:
        opts.insert(0, "Ask what the shipwrights need in the Grand War-Fleet Contract")
    opts.append("Leave")
    return opts


def resolve_aldred(choice, player):
    if choice == "Leave":
        return player, "Foundryman Aldred stokes the roaring coke-furnace with a long iron rod.", "MAIN"

    if choice == "Ask about the Dry-Dock & Iron Foundry":
        return player, (
            "Aldred wipes sweat from his soot-blackened brow.\n"
            "\"We cast the cannon and roll the copper sheathing for every hull in Parvus—when the fences and politicians let us work in peace.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the quality of the hull-plates & foundry pig-iron":
        player["parvus_aldred_iron_clue"] = True
        return player, (
            "Aldred spits into the quenching trough.\n"
            "\"Someone substituted high-sulphur bog-slag for our Guild steel billets! When you strike the counterfeit plates with a hammer, they give a dull leaden *thud* and smell of **rotten brimstone**, "
            "whereas true Guild steel rings like a church bell. Search the **quenching trough** here in the yard and check the **Harbour-Front Gantry Crane** if you want to set things right!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask what the shipwrights need in the Grand War-Fleet Contract":
        player["parvus_aldred_fleet_clue"] = True
        return player, (
            "Aldred taps a rolled blueprint against his leather apron.\n"
            "\"If Guildmaster Buildhope wants the Maritime Guild to stay independent in the coming war, we must demand **Three Clauses** at the Admiralty table: "
            "**1) Guild Ownership of the Dry-Dock**, **2) Exemption from Feudal Impressment**, and **3) Armed Convoy Letters of Marque**!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 3. ENVIRONMENTAL SEARCH HOOKS IN PARVUS TOWN
# =========================================================================
def handle_parvus_search(player):
    """
    Called inside action_gather() when exploring Parvus Town.
    Returns (handled_bool, log_message).
    """
    pos = (player["x"], player["y"])
    if player.get("current_building"):
        return False, ""

    step = player.get("ch2_mission_step", 1)

    # 1. Parvus Harbour-Front & Gantry Crane (17, 23): Unjam Crane (Step 1) or Check Ship Drafts (Step 3)
    if pos == (17, 23):
        if step == 1 and not player.get("parvus_crane_shimmed"):
            die = random.randint(1, 6) + (player.get("strength", 0) // 2) + (3 if "forge" in player.get("skills", []) else 0)
            player["parvus_crane_shimmed"] = True
            player, _ = advance_time(20, player)
            extra = " (+6s Windfall found in the gear-housing!)" if die >= 8 else ""
            if die >= 8:
                player["silver"] += 6
            return True, (
                f"[Search Roll: {die}] Climbing the oak timber frame of the Guild Gantry Crane, you spot a jagged Kokeshi cast-iron shim wedged deep inside the brass worm-gear!\n"
                f"You prize the shim loose with a wrench and grease the drum—the great crane is ready to turn again!{extra}"
            )
        if step == 3 and not player.get("parvus_ships_inspected"):
            player["parvus_ships_inspected"] = True
            player, _ = advance_time(15, player)
            return True, (
                "Walking along the stone mole, you inspect the Plimsoll waterline marks on the three moored brigantines:\n"
                "The *Sea-Swallow* and *Gilded Gull* ride high and light, but the ***Cormorant***—whose manifest claims she carries only cork—sits two feet below her load-line, weighted down with secret Kokeshi musket crates!"
            )

    # 2. Harbourmaster's Customs House (16, 22): Inspect Seals & Watermarks (Step 2)
    if pos == (16, 22) and step == 2:
        if player.get("parvus_customs_searched"):
            return True, "You have already secured the Crown Anchor watermarked paper and inspected the brass seal-press at the Customs House."
        player["parvus_customs_searched"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Searching the waste-bins and drafting desks behind the Harbourmaster's Customs House, you recover a quire of **Crown Anchor Watermarked Paper**, "
            "a wax impression of the **Parvus Watch Billeting Seal**, and a blotted proof-sheet of the F.A.I.'s blue gall-ink flyers!"
        )

    # 3. Parvus Dry-Dock & Iron Foundry (18, 21): Search the Quenching Trough (Step 2)
    if pos == (18, 21) and step == 2:
        if player.get("parvus_foundry_searched"):
            return True, "You have already recovered the stolen Guild bullion and counterfeit slag-plates from the foundry quenching trough."
        player["parvus_foundry_searched"] = True
        player["silver"] += 15
        player, _ = advance_time(20, player)
        return True, (
            "Rolling up your sleeves beside the Dry-Dock quenching trough, you trip the false iron grate at the bottom and haul up an oilskin chest containing **15 silver** of stolen Guild bullion "
            "alongside the Kokeshi fence's ledger for the brittle slag-iron plates! (+15 Silver)"
        )

    # 4. Kokeshi Bonded Warehouses & Slipway (18, 23): Scout the Slipway Chute (Step 3)
    if pos == (18, 23) and step == 3:
        if player.get("parvus_warehouse_scouted"):
            return True, "You have already unbolted the sea-side slipway grate and mapped the upper musket loft of the Bonded Warehouse."
        player["parvus_warehouse_scouted"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Creeping down the slick stone slipway beside the Kokeshi Bonded Warehouses, you find the sea-side cargo chute and silently draw back its rusted iron bolt—giving you a secret back-door straight into the contraband musket loft!"
        )

    return False, ""


# =========================================================================
# 4. UNIFIED PARVUS POP-OUT MISSION SCENARIOS (TRACKS 4, 5 & 6)
# =========================================================================
PARVUS_SCENARIOS = {
    # ------------------------------------------------------------------
    # TRACK 4: F.A.I.-C.N.T. REVOLUTIONARY SYNDICATE (4A, 4B, 4C, 4E)
    # ------------------------------------------------------------------
    "4a": {
        "track": "fai",
        "header": "PARVUS ROPE-WALK — VETTING THE REVOLUTIONARY CELL",
        "prep_flag": "parvus_ronan_recruits_clue",
        "prep_label": "Rigger Ronan's Tar-Stained Hands & Password Intel",
        "stages": [
            {
                "title": "STAGE 1/3: THE SHIBBOLETH AT THE TAR-BOILERS",
                "desc": "Three dockside volunteers step into the Rope-Walk shed at dusk. How do you test their knowledge of revolutionary theory?",
                "opts": [
                    ("Challenge them to quote Proudhon's 'What Is Property?' (2d6)", 22),
                    ("Ask them to sing a traditional sailors' shanty (2d6)", 12),
                    ("Demand a 5-silver initiation fee from each man", -10),
                ],
            },
            {
                "title": "STAGE 2/3: UNMASKING THE CROWN INFORMER!",
                "desc": "You inspect the three recruits: **Conor** (tar-stained knuckles), **Padraig** (hemp-calloused palms), and **Garrick** (soft pink palms and waxed guard-boots).",
                "opts": [
                    ("Expose & Expel Garrick as a Crown Informer! (2d6)", 28),
                    ("Accept all three men into the cell without objection", -20),
                    ("Accuse Conor the rope-spinner of being a spy", -15),
                ],
            },
            {
                "title": "STAGE 3/3: SWEARING THE SYNDICALIST OATH",
                "desc": "With the informer driven off, how do you organise your new Parvus dockside cell?",
                "opts": [
                    ("Establish compartmentalised three-person dock rings (2d6)", 22),
                    ("Issue red-and-black tokens and assign night lookouts (2d6)", 18),
                    ("Write everyone's real names in a single paper ledger", -15),
                ],
            },
        ],
    },
    "4b": {
        "track": "fai",
        "header": "CUSTOMS HOUSE PRESS — FORGING THE BILLETING ORDERS",
        "prep_flag": "parvus_customs_searched",
        "prep_label": "Crown Anchor Watermarked Paper & Watch Seal Impression",
        "stages": [
            {
                "title": "STAGE 1/3: SELECTING THE PAPER STOCK",
                "desc": "At the underground flatbed press, you prepare to print faux Watch Billeting Warrants claiming the Guard will quarter soldiers in every dockworker's cottage.",
                "opts": [
                    ("Print on the stolen Crown Anchor Watermarked Paper! (2d6)", 25),
                    ("Print on heavy shipping-manifest vellum (2d6)", 14),
                    ("Print on cheap, un-watermarked blue rag-paper", -15),
                ],
            },
            {
                "title": "STAGE 2/3: STAMPING THE HARBOURMASTER'S SEAL",
                "desc": "Each warrant requires the official embossed seal of the Parvus Watch Billet to fool the street sergeants.",
                "opts": [
                    ("Cast a beeswax matrix from the Customs House Seal-Press! (2d6)", 25),
                    ("Carve a wooden block-stamp by hand (2d6)", 12),
                    ("Scrawl a forged signature without a wax seal", -15),
                ],
            },
            {
                "title": "STAGE 3/3: POSTING THE WARRANTS AT DAWN",
                "desc": "Before the morning bell, your cell fans out to nail the forged billeting orders across the port!",
                "opts": [
                    ("Pin them to the Rope-Walk, Dry-Dock & Salted Anchor! (2d6)", 22),
                    ("Slip them into the fishwives' market baskets (2d6)", 16),
                    ("Nail one directly to the Guard House door in broad daylight", -10),
                ],
            },
        ],
    },
    "4c": {
        "track": "fai",
        "header": "EASTERN QUAY — FRAMING THE KOKESHI WAREHOUSES",
        "prep_flag": "parvus_warehouse_scouted",
        "prep_label": "Unbolted Sea-Side Slipway Chute & Loft Layout",
        "stages": [
            {
                "title": "STAGE 1/3: BREACHING THE BONDED WAREHOUSE",
                "desc": "Your cell creeps along the eastern quay carrying a crate of stolen Crown muskets to plant inside the Kokeshi Syndicate's bonded warehouse.",
                "opts": [
                    ("Slip silently through the unbolted Sea-Side Slipway Chute! (2d6)", 25),
                    ("Scale the warehouse drainpipe with a grappling rope (2d6)", 15),
                    ("Pry the front iron double-doors in view of the street", -15),
                ],
            },
            {
                "title": "STAGE 2/3: PLANTING THE SEDITIOUS CONTRABAND",
                "desc": "Inside the dark upper loft, rows of Kokeshi silk and brandy crates stand beside the factor's desk.",
                "opts": [
                    ("Hide the muskets in the main crate & alter the Kokeshi manifest! (2d6)", 25),
                    ("Stack the muskets behind the brandy casks (2d6)", 15),
                    ("Dump the muskets on the stairs and run", -10),
                ],
            },
            {
                "title": "STAGE 3/3: TIPPING OFF THE CUSTOMS WATCH",
                "desc": "As you slip back out to the quay, how do you bring the Parvus Watch down on the Kokeshi bosses?",
                "opts": [
                    ("Ring the bronze Harbour-Bell & drop an anonymous manifest tip! (2d6)", 22),
                    ("Fire a musket shot into the air outside the warehouse (2d6)", 14),
                    ("Deliver the tip in person to the Watch sergeant", -12),
                ],
            },
        ],
    },
    "4e": {
        "track": "fai",
        "header": "UPPER PARVUS PROMENADE — THE HARBOUR FESTIVAL COUP",
        "prep_flag": "parvus_maeve_step5_clue",
        "prep_label": "Guildhall Astrolabe Sightline & Third Bell-Stroke Timing",
        "stages": [
            {
                "title": "STAGE 1/3: TAKING POSITION ABOVE THE PROMENADE",
                "desc": "Silk banners snap in the sea-wind as thousands pack the Upper Parvus Promenade for the Harbour Festival! Where do you take up your position?",
                "opts": [
                    ("Scale the gilded Astrolabe Dome atop the Guildhall roof! (2d6)", 25),
                    ("Blend into the dockworkers' delegation below the balcony (2d6)", 15),
                    ("Rush the front stone staircase past the Watch halberdiers", -18),
                ],
            },
            {
                "title": "STAGE 2/3: THE THIRD STROKE OF THE HARBOUR BELL",
                "desc": "Mayor Holdfast steps onto the limestone balcony rail as the bronze harbour-bell begins to toll!",
                "opts": [
                    ("Strike on the roar of the Third Bell-Stroke & raise the Red-and-Black Flag! (2d6)", 28),
                    ("Hurl a smoke-pot onto the dais to scatter the guards! (2d6)", 18),
                    ("Shout a warning slogan before striking", -15),
                ],
            },
            {
                "title": "STAGE 3/3: PROCLAIMING THE FREE COMMUNE OF PARVUS!",
                "desc": "As panic seizes the magistracy, your F.A.I. cells surge into the square!",
                "opts": [
                    ("Seize the Harbour Boom-Chains & proclaim the Revolutionary Commune! (2d6)", 22),
                    ("Distribute the bonded granary stores to the cheering crowd (2d6)", 18),
                    ("Linger on the balcony to loot the silver candelabra", -12),
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # TRACK 5: CROWN INTELLIGENCERS (5A, 5B, 5C, 5E)
    # ------------------------------------------------------------------
    "5a": {
        "track": "crown",
        "header": "PARVUS ROPE-WALK — INFILTRATING THE F.A.I. CELL",
        "prep_flag": "parvus_ronan_recruits_clue",
        "prep_label": "Stockholm Tar Disguise & Proudhon Password",
        "stages": [
            {
                "title": "STAGE 1/3: CRAFTING YOUR UNDERCOVER ALIBI",
                "desc": "To slip inside Speaktruth's revolutionary cell at the Rope-Walk, you must look and speak like a veteran coastal rigger.",
                "opts": [
                    ("Rub Stockholm pine-tar into your palms & wear a rigger's smock! (2d6)", 25),
                    ("Carry a coil of hemp cordage over your shoulder (2d6)", 15),
                    ("Walk in wearing your clean travel cloak and polished boots", -20),
                ],
            },
            {
                "title": "STAGE 2/3: THE CELL LEADER'S CHALLENGE",
                "desc": "Speaktruth narrows their eyes at you in the lantern-light: \"State the theoretical password and show your hands, newcomer!\"",
                "opts": [
                    ("Quote Proudhon's First Chapter & display your tar-blackened knuckles! (2d6)", 28),
                    ("Claim you escaped from the Fluvius farm picket line (2d6)", 16),
                    ("Fumble the password and try to bluff", -18),
                ],
            },
            {
                "title": "STAGE 3/3: COPYING THE CELL CIPHER-ROLL",
                "desc": "Accepted into the circle, you are handed the night-watch roster while the agitators debate.",
                "opts": [
                    ("Memorise the cell codenames & dead-drop hours in shorthand! (2d6)", 22),
                    ("Palming a spare copy of the roster into your boot (2d6)", 16),
                    ("Take notes openly on Crown stationery", -20),
                ],
            },
        ],
    },
    "5b": {
        "track": "crown",
        "header": "HARBOUR STEPS — EXPOSING THE FORGED BILLETING ORDERS",
        "prep_flag": "parvus_maeve_step2_clue",
        "prep_label": "Blue Gall-Ink & Missing Crown Watermark Forensics",
        "stages": [
            {
                "title": "STAGE 1/3: INTERCEPTING THE DAWN BILL-POSTERS",
                "desc": "Angry dockers are gathering around freshly pasted 'Watch Billeting Warrants' threatening to quarter troops in their homes!",
                "opts": [
                    ("Hold a flyer up to the sun to show it lacks the Crown Anchor Watermark! (2d6)", 26),
                    ("Point out the wet blue gall-ink smudging on the rag-paper! (2d6)", 22),
                    ("Tear the flyers down at sword-point without explaining", -18),
                ],
            },
            {
                "title": "STAGE 2/3: DISPLAYING THE TRUE HARBOURMASTER SEAL",
                "desc": "A dockside heckler shouts: \"How do we know the Harbourmaster didn't sign that warrant himself?!\"",
                "opts": [
                    ("Produce the genuine red-wax Customs Seal-Press to prove the forgery! (2d6)", 25),
                    ("Swear on your honour that the Watch is quartered in barracks (2d6)", 14),
                    ("Threaten to arrest anyone who reads the flyer", -15),
                ],
            },
            {
                "title": "STAGE 3/3: RAIDING THE ILLICIT FLATBED PRESS",
                "desc": "Tracking the wet blue ink-smudges down the alley behind the net-sheds, you corner the F.A.I.'s hidden printing press!",
                "opts": [
                    ("Seize the lead type-plates & turn the printer into a double-agent! (2d6)", 22),
                    ("Smash the printing press with an iron bar (2d6)", 16),
                    ("Let the printer escape with the plates", -12),
                ],
            },
        ],
    },
    "5c": {
        "track": "crown",
        "header": "BONDED WAREHOUSES — THE DOUBLE-SYNDICATE STING",
        "prep_flag": "parvus_maeve_step3_clue",
        "prep_label": "Midnight Loft Meeting & Sea-Side Slipway Chute Intel",
        "stages": [
            {
                "title": "STAGE 1/3: SETTING THE HARBOUR TRAP",
                "desc": "Midnight approaches at the Kokeshi Bonded Warehouses. Both Kokeshi bosses and F.A.I. saboteurs are converging on the building!",
                "opts": [
                    ("Wait until BOTH groups are inside, then bar the Slipway Chute & Main Doors! (2d6)", 28),
                    ("Deploy Watch crossbowmen along the stone mole roof (2d6)", 16),
                    ("Blow your whistle too early while the F.A.I. is still outside", -18),
                ],
            },
            {
                "title": "STAGE 2/3: SPRINGING THE CUSTOMS NET",
                "desc": "Inside the musket loft, Kokeshi smugglers and F.A.I. frames collide in the dark—just as your Watch lanterns flare!",
                "opts": [
                    ("Seize the Kokeshi arms-manifest AND the F.A.I. saboteur team in one sweep! (2d6)", 25),
                    ("Focus on arresting the Kokeshi warehouse factor (2d6)", 15),
                    ("Allow the two gangs to shoot it out and burn the evidence", -15),
                ],
            },
            {
                "title": "STAGE 3/3: INTERROGATING THE CAPTURED COURIER",
                "desc": "A captured saboteur trembles in irons on the slipway. You need to know where the F.A.I. has planted their main explosive charge!",
                "opts": [
                    ("Leverage your undercover cell knowledge to make him confess the Promenade Grate! (2d6)", 22),
                    ("Offer him a reduced sentence in exchange for the target (2d6)", 16),
                    ("Lock him in the brig without questioning him", -12),
                ],
            },
        ],
    },
    "5e": {
        "track": "crown",
        "header": "UPPER PARVUS PROMENADE — FOILING THE ASSASSINATION",
        "prep_flag": "parvus_maeve_step5_clue",
        "prep_label": "Guildhall Astrolabe Sightline & Third Bell-Stroke Timing",
        "stages": [
            {
                "title": "STAGE 1/3: SCANNING THE FESTIVAL CROWD & ROOFLINES",
                "desc": "Mayor Holdfast prepares to step onto the Upper Parvus Balcony. Where do you focus your counter-espionage sweep?",
                "opts": [
                    ("Train your spyglass on the Guildhall Astrolabe Dome & roof-ledges! (2d6)", 26),
                    ("Search the cloaks of the dignitaries on the balcony stairs (2d6)", 15),
                    ("Stand with your back to the crowd facing the Mayor", -18),
                ],
            },
            {
                "title": "STAGE 2/3: THE THIRD STROKE OF THE HARBOUR BELL!",
                "desc": "BONG! BONG! BONG! On the third stroke of the harbour-bell, a glint of steel flashes from the rooftop shadow above the balcony!",
                "opts": [
                    ("Shove Mayor Holdfast behind the stone pillar & intercept the assassin! (2d6)", 28),
                    ("Loose a snap-shot / throwing blade at the rooftop figure! (2d6)", 20),
                    ("Freeze in shock as the bolt whistles toward the dais", -25),
                ],
            },
            {
                "title": "STAGE 3/3: SECURING THE PORT FOR THE CROWN",
                "desc": "With the assassin pinned to the cobbles and Mayor Holdfast unharmed, the festival square looks to the balcony!",
                "opts": [
                    ("Have Mayor Holdfast proclaim Royal Order & reward the loyal Watch! (2d6)", 22),
                    ("Lock down the harbour boom-chains under Crown control (2d6)", 18),
                    ("Order the Watch to clear the festival square with clubs", -12),
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # TRACK 6: MARITIME & ARTISANS GUILD (6A, 6B, 6C, 6E)
    # ------------------------------------------------------------------
    "6a": {
        "track": "guild",
        "header": "HARBOUR-FRONT MOLE — THE GREAT GANTRY CRANE",
        "prep_flag": "parvus_crane_shimmed",
        "prep_label": "Kokeshi Iron Shim Removed from Worm-Gear",
        "stages": [
            {
                "title": "STAGE 1/3: DIAGNOSING THE JAMMED COUNTERWEIGHT",
                "desc": "Cargo is piling up along the Parvus mole while the great oak Gantry Crane sits frozen. How do you restore the mechanism?",
                "opts": [
                    ("Engage the cleaned worm-gear (Shim already removed!) & grease the drum! (2d6)", 26),
                    ("Use your Forge / Masonry skill to realign the bronze pinion (2d6)", 20),
                    ("Order six mules to haul the jammed chain by brute force", -15),
                ],
            },
            {
                "title": "STAGE 2/3: SETTLING WITH THE CRANE-RIGGERS",
                "desc": "Rigger Ronan and the crane-crew refuse to man the treadwheel unless their docked danger-pay is restored.",
                "opts": [
                    ("Restore full Guild danger-pay & sign a profit-sharing charter! (2d6)", 24),
                    ("Pay a 10-silver bonus out of your own purse to start the wheel (2d6)", 16),
                    ("Threaten to replace the riggers with untrained landsmen", -15),
                ],
            },
            {
                "title": "STAGE 3/3: THE FIRST TEN-TON LIFT",
                "desc": "The treadwheel turns and the massive iron hook hoists a ten-ton naval boiler off the deck of a waiting brigantine!",
                "opts": [
                    ("Guide the boom smoothly onto the Guild cradle to the cheers of the quay! (2d6)", 22),
                    ("Lock the pawl-brake and open the Guild Workshop doors (2d6)", 16),
                    ("Swing the heavy load too fast across the crowded dock", -12),
                ],
            },
        ],
    },
    "6b": {
        "track": "guild",
        "header": "PARVUS DRY-DOCK — THE COUNTERFEIT STEEL RING",
        "prep_flag": "parvus_foundry_searched",
        "prep_label": "Stolen Bullion & Slag-Iron Ledger Recovered from Trough",
        "stages": [
            {
                "title": "STAGE 1/3: METALLURGICAL AUDIT AT THE FOUNDRY",
                "desc": "Shipwrights complain that newly delivered hull-plates are cracking on the rivets. How do you test the suspect iron?",
                "opts": [
                    ("Strike the plates for the dull brimstone ring of high-sulphur bog-slag! (2d6)", 25),
                    ("Melt a sample in Foundryman Aldred's assay crucible (2d6)", 20),
                    ("Approve the plates without testing them", -20),
                ],
            },
            {
                "title": "STAGE 2/3: CONFRONTING THE KOKESHI FENCE",
                "desc": "Tracing the dross shipment to Fence Vane at The Salted Anchor, you corner him over his ledger!",
                "opts": [
                    ("Slam the Quenching-Trough Ledger on the table & reclaim the Guild bullion! (2d6)", 28),
                    ("Threaten him with a Guild embargo until he refunds 20 silver (2d6)", 18),
                    ("Accept a small kickback to overlook the bad steel", -20),
                ],
            },
            {
                "title": "STAGE 3/3: RE-CASTING THE WARSHIP SHEATHING",
                "desc": "Back at the Dry-Dock Foundry, how do you ensure the fleet's armour plates are forged to perfection?",
                "opts": [
                    ("Alloy the melt with pure Swedish/Star-Iron & oil-quench the plates! (2d6)", 22),
                    ("Double-rivet the sound reserve plates onto the flagship hull (2d6)", 16),
                    ("Patch the cracked plates with pitch and canvas", -15),
                ],
            },
        ],
    },
    "6c": {
        "track": "guild",
        "header": "HARBOUR CUSTOMS MOLE — THE CONTRABAND MANIFEST",
        "prep_flag": "parvus_ships_inspected",
        "prep_label": "Plimsoll Waterline Draft-Marks Audited",
        "stages": [
            {
                "title": "STAGE 1/3: READING THE PLIMSOLL DRAFT-MARKS",
                "desc": "Three merchant brigantines sit moored at the mole: the *Sea-Swallow*, the *Cormorant*, and the *Gilded Gull*. One is secretly ballasted with Kokeshi contraband arms!",
                "opts": [
                    ("Pinpoint the *Cormorant*—riding two feet deep despite a 'cork' manifest! (2d6)", 28),
                    ("Board the *Sea-Swallow* and search her spice hold", -12),
                    ("Board the *Gilded Gull* and search her timber deck", -12),
                ],
            },
            {
                "title": "STAGE 2/3: SOUNDING THE FALSE BULKHEAD",
                "desc": "Down in the *Cormorant*'s hold, bales of light cork fill the forward bay—yet the hull sits deep in the water.",
                "opts": [
                    ("Measure the keel-length & pry open the false aft bulkhead! (2d6)", 25),
                    ("Use a carpenter's auger to bore into the bilge-planks (2d6)", 16),
                    ("Give up and sign off on the cork manifest", -20),
                ],
            },
            {
                "title": "STAGE 3/3: IMPOUNDING THE ARMS CACHE FOR THE GUILD",
                "desc": "Behind the false bulkhead lie forty crates of naval muskets, swivel-guns, and Kokeshi silver!",
                "opts": [
                    ("Impound the swivel-guns to arm the Guild's own merchant cutters! (2d6)", 22),
                    ("Turn the manifest over to the Harbourmaster for a lawful bounty (2d6)", 18),
                    ("Leave the weapons on board unguarded", -15),
                ],
            },
        ],
    },
    "6e": {
        "track": "guild",
        "header": "MARITIME GUILDHALL — THE GRAND WAR-FLEET CONTRACT",
        "prep_flag": "parvus_aldred_fleet_clue",
        "prep_label": "The Three Shipwright Independence Clauses",
        "stages": [
            {
                "title": "STAGE 1/3: CLAUSE 1 — THE DRY-DOCK & FOUNDRIES",
                "desc": "Envoys from the Crown, the Castellans, and Mayor Holdfast sit around the Guildhall Admiralty Table, demanding warships for Chapter 3!",
                "opts": [
                    ("Demand Clause 1: Perpetual Guild Ownership of the Dry-Dock & Foundries! (2d6)", 25),
                    ("Lease the Dry-Dock to the highest bidder for cash (2d6)", 14),
                    ("Surrender the Dry-Dock to military requisition", -20),
                ],
            },
            {
                "title": "STAGE 2/3: CLAUSE 2 — PROTECTION OF GUILD CREWS",
                "desc": "The military commissioners demand the right to press-gang Parvus sailors and riggers into the feudal infantry!",
                "opts": [
                    ("Enforce Clause 2: Total Exemption from Feudal Impressment for Guildsmen! (2d6)", 26),
                    ("Agree to supply only volunteer transport crews (2d6)", 16),
                    ("Allow press-gangs into the Sailors' Quarter", -20),
                ],
            },
            {
                "title": "STAGE 3/3: CLAUSE 3 — LETTERS OF MARQUE & ARMED FLEET",
                "desc": "With the envoys desperate for your copper-sheathed ships and Star-Iron cannon, you lay down the final condition!",
                "opts": [
                    ("Secure Clause 3: Independent Armed Letters of Marque under the Guild Flag! (2d6)", 25),
                    ("Sign a lucrative toll-charter for all coastal supply convoys (2d6)", 18),
                    ("Place the Guild fleet under a royal admiral's command", -15),
                ],
            },
        ],
    },
}


def init_parvus_minigame(player, mission_code):
    """Initializes the unified 680x480 Pop-Out Window for any Track 4, 5, or 6 mission."""
    scen = PARVUS_SCENARIOS[mission_code]
    player["pv_code"] = mission_code
    player["pv_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["pv_stage"] = 0

    base_prog = 35 + (player.get("stealth", 0) * 2) + (player.get("charisma", 0) * 2) + (player.get("influence", 0) * 2)
    if player.get(scen["prep_flag"]):
        base_prog += 18
    if "star-iron ingot" in player.get("inventory", []) and scen["track"] == "guild":
        base_prog += 10
    if "crown of the first castellan" in player.get("inventory", []) and scen["track"] == "crown":
        base_prog += 10

    player["pv_progress"] = min(65, base_prog)
    player["pv_feedback"] = (
        f"Mission Underway: {scen['header']}. "
        "Complete all 3 stages and drive Mission Success to 75%+ (each choice rolls 2d6 + your preparation & coastal twists)!"
    )
    return player, player["pv_feedback"], "MINIGAME_PARVUS"


def parvus_action(choice_idx, player):
    """Processes a stage choice (0, 1, or 2) in MINIGAME_PARVUS with 2d6 rolls & windfalls."""
    code = player.get("pv_code", "4a")
    scen = PARVUS_SCENARIOS[code]

    if player.get("pv_phase") == "RESULT":
        return conclude_parvus_minigame(player)

    st_idx = player.get("pv_stage", 0)
    st_data = scen["stages"][st_idx]
    opt_label, base_delta = st_data["opts"][choice_idx]

    swing, prefix, twist_str = roll_parvus_2d6_twist(player, track_kind=scen["track"])
    prep_bonus = 6 if (choice_idx == 0 and player.get(scen["prep_flag"])) else 0

    # If the player picked the top prep option WITHOUT having done the field investigation, reduce its gain!
    if choice_idx == 0 and not player.get(scen["prep_flag"]) and base_delta >= 24:
        actual_delta = 10 + (swing // 2)
        note = f"You attempt '{opt_label.split(' (')[0]}', though without prior dockside recon you have to improvise on the spot!"
    else:
        actual_delta = base_delta + prep_bonus + (swing // 2)
        note = f"Executed: {opt_label.split(' (')[0]}!"

    player["pv_progress"] = max(0, min(100, player.get("pv_progress", 40) + actual_delta))
    full_msg = f"{prefix}{note} ({'+' if actual_delta >= 0 else ''}{actual_delta}%){twist_str}"

    if st_idx >= 2:
        player["pv_phase"] = "RESULT"
        tag = "MISSION TRIUMPH!" if player["pv_progress"] >= 75 else "PARTIAL EXECUTION!"
        player["pv_feedback"] = f"{full_msg} — [{tag} ({player['pv_progress']}%)] Click [Conclude Operation >>]!"
        return player, player["pv_feedback"], "MINIGAME_PARVUS"

    player["pv_stage"] = st_idx + 1
    player["pv_feedback"] = full_msg
    return player, None, "MINIGAME_PARVUS"


def conclude_parvus_minigame(player):
    code = player.get("pv_code", "4a")
    prog = player.get("pv_progress", 0)
    player["active_ch2_mission"] = None

    step_num = ord(code[1]) - ord('a') + 1  # 'a'->1 .. 'e'->5
    player["ch2_mission_step"] = step_num + 1

    success = (prog >= 75)
    gain = 22 if success else 8
    player["position_strength"] = min(100, player.get("position_strength", 0) + gain)
    if not success:
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1

    # Check if this was the Finale (4E, 5E, or 6E)!
    if code in ("4e", "5e", "6e"):
        track_num = code[0]
        win_finale = (prog >= 70 or player.get("position_strength", 0) >= 75)
        player.setdefault("ch3_world_bits", {})[f"track_{track_num}"] = 1 if win_finale else 0

        if code == "4e":
            modify_faction(player, "faction_union", 3 if win_finale else -1)
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: THE PARVUS REVOLUTIONARY COMMUNE! \n"
                "=========================================================\n"
                "On the third stroke of the harbour-bell, your strike from the rooftops topples the old magistracy! "
                "Red-and-black banners unfurl from the Gantry Crane to the Promenade as Parvus proclaims the Revolutionary Commune for Chapter 3!\n\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
                if win_finale else
                "=== MISSION FAILED: MARTIAL LAW IN PARVUS ===\n"
                "Crown Intelligencers intercept your strike on the balcony, and the port is locked down under royal martial law!"
            )
        elif code == "5e":
            player["reputation"] = player.get("reputation", 0) + (3 if win_finale else -1)
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: THE CROWN SHIELD OF PARVUS!       \n"
                "=========================================================\n"
                "Spotting the rooftop assassin on the third stroke of the harbour-bell, you foil the F.A.I. coup in full view of the festival crowd! "
                "Mayor Holdfast and Handler Eadric salute you as Parvus stands rock-solid for the Crown in Chapter 3!\n\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
                if win_finale else
                "=== MISSION FAILED: CHAOS ON THE PROMENADE ===\n"
                "You were a heartbeat too late to stop the rooftop strike, plunging Parvus Harbour into revolutionary turmoil!"
            )
        else:
            player["silver"] += 40 if win_finale else 10
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: THE INDEPENDENT GUILD ARMADA!     \n"
                "=========================================================\n"
                "With all three Shipwright Clauses locked into the Grand War-Fleet Contract, the Maritime & Artisans Guild commands its own armed merchant fleet and dry-docks (+40 Silver) as Chapter 3 begins!\n\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
                if win_finale else
                "=== MISSION FAILED: MILITARY REQUISITION ===\n"
                "Outmanoeuvred at the Admiralty table, the Guild's dry-docks are forcibly requisitioned for the feudal war effort!"
            )
        return player, log, "CHAPTER_2_COMPLETE"

    # Next-step hints for A, B, C (remembering Step 4 is the Under-Parvus Dungeon!)
    if step_num == 3:
        next_hint = (
            "*** NEXT (MISSION D — THE UNDER-PARVUS CATACOMBS DUNGEON!): ***\n"
            "Speak to your faction leader for your subterranean briefing, then head to the **Upper Parvus Promenade** and use **Action -> Search** at the **Iron Storm-Drain Grate** to descend into the **Under-Parvus Tidal Catacombs**!"
        )
    else:
        next_hint = "Return to your Parvus faction leader (and explore the Rope-Walk, Salted Anchor, Customs House, and Dry-Dock) for your next operation!"

    log = (
        f"=== MISSION {code.upper()} COMPLETE (+{gain}% Position Strength | Operation Score: {prog}%)! ===\n"
        f"{next_hint}"
    )
    return player, log, "MAIN"


def draw_parvus_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Tracks 4, 5, and 6."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    SEA_BLUE = (38, 98, 145)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    code = player.get("pv_code", "4a")
    scen = PARVUS_SCENARIOS[code]

    title = font_bold.render(scen["header"], True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    prog = player.get("pv_progress", 40)
    screen.blit(font_bold.render(f"Operation Success & Leverage: {prog}% (Target: 75%+)", True, SEA_BLUE), (85, 80))
    p_bar = pygame.Rect(425, 80, 290, 18)
    pygame.draw.rect(screen, (40, 35, 35), p_bar, border_radius=4)
    if prog > 0:
        col = (45, 135, 65) if prog >= 75 else SEA_BLUE
        pygame.draw.rect(screen, col, (425, 80, int(290 * (prog / 100.0)), 18), border_radius=4)
    tx = 425 + int(290 * 0.75)
    pygame.draw.line(screen, (255, 255, 255), (tx, 78), (tx, 100), 2)
    pygame.draw.rect(screen, CLOCK_BLACK, p_bar, width=1, border_radius=4)

    st_idx = min(2, player.get("pv_stage", 0))
    st_data = scen["stages"][st_idx]

    s_box = pygame.Rect(85, 112, 630, 140)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 120))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 146, 600, 70), CLOCK_BLACK, max_lines=3)

    has_prep = player.get(scen["prep_flag"], False)
    prep_txt = f"Harbour Reconnaissance: [{scen['prep_label']} SECURED!]" if has_prep else f"Harbour Reconnaissance: Unverified (Explore Parvus to uncover: {scen['prep_label']})"
    screen.blit(font.render(prep_txt[:78], True, (45, 125, 60) if has_prep else TATE_RED), (100, 226))

    fb_box = pygame.Rect(85, 262, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("pv_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 5. DIALOGUE HANDLERS FOR SPEAKTRUTH (4), EADRIC (5), AND BUILDHOPE (6)
# =========================================================================
def get_speaktruth_parvus_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []
    if route == "Parvus: F.A.I.-C.N.T. Syndicate":
        if step == 1:
            opts.append("Mission: Briefing on Dockside Cell Recruitment" if not player.get("m4a_briefed") else "Mission: Vet the Recruits at the Rope-Walk!")
        elif step == 2:
            opts.append("Mission: Briefing on the Watch Billeting Forgery" if not player.get("m4b_briefed") else "Mission: Run the Underground Flatbed Press!")
        elif step == 3:
            opts.append("Mission: Briefing on the Kokeshi Warehouse Frame-Up" if not player.get("m4c_briefed") else "Mission: Plant the Muskets in the Bonded Warehouse!")
        elif step == 4:
            opts.append("Mission: Descend into the Under-Parvus Catacombs (Route the Fuses!)")
        elif step == 5:
            opts.append("Mission: Briefing on the Harbour Festival Climax" if not player.get("m4e_briefed") else "Mission: Strike at the Upper Parvus Promenade!")
    opts.extend(["Ask about the Dock Strike", "Leave"])
    return opts


def resolve_speaktruth_parvus(choice, player):
    if choice == "Leave":
        return player, "Speaktruth pulls their salt-stained cap low and melts into the Rope-Walk shadows.", "MAIN"
    if choice == "Ask about the Dock Strike":
        return player, "\"The port is ready to rise, comrade—we only need to break the Watch and the Kokeshi bosses.\"", "NPC_DIALOGUE"

    if choice in ("Mission: Briefing on Dockside Cell Recruitment", "Mission: Canvas the Docks & Recruit a Cell"):
        player["m4a_briefed"] = True
        return player, (
            "=== MISSION: VETTING THE PARVUS CELL ===\n"
            "Speaktruth gestures toward the tar-boilers along the Rope-Walk.\n"
            "\"Three volunteers want into our Parvus cell, Noburu—but Crown Intelligencer Eadric has planted a rat among them.\"\n"
            "\"Speak with **Rigger Ronan** right here at the Rope-Walk first to learn how true syndicalist riggers spot a phony, then return to me to vet the recruits!\""
        ), "MAIN"
    if choice == "Mission: Vet the Recruits at the Rope-Walk!":
        return init_parvus_minigame(player, "4a")

    if choice in ("Mission: Briefing on the Watch Billeting Forgery", "Mission: Forge the Watch Billeting Orders"):
        player["m4b_briefed"] = True
        return player, (
            "=== MISSION: THE BILLETING WARRANT FORGERY ===\n"
            "\"To turn the whole town against the garrison, we're printing forged Watch Billeting Warrants,\" Speaktruth whispers.\n"
            "\"Before we ink the press, **search** around the **Harbourmaster's Customs House** and question **Maeve at The Salted Anchor** so our paper watermark and wax seal are indistinguishable from the real thing!\""
        ), "MAIN"
    if choice == "Mission: Run the Underground Flatbed Press!":
        return init_parvus_minigame(player, "4b")

    if choice in ("Mission: Briefing on the Kokeshi Warehouse Frame-Up", "Mission: Plant Contraband in the Kokeshi Warehouses"):
        player["m4c_briefed"] = True
        return player, (
            "=== MISSION: FRAMING THE KOKESHI BOSSES ===\n"
            "\"We've seized a crate of stolen muskets. If we plant them inside the **Kokeshi Bonded Warehouses** on the eastern quay and tip off the customs watch, the Guard will arrest the Kokeshi leadership for us!\"\n"
            "\"Go to the **Bonded Warehouses** and **search** the stone slipway for a secret entry chute before we move the crate!\""
        ), "MAIN"
    if choice == "Mission: Plant the Muskets in the Bonded Warehouse!":
        return init_parvus_minigame(player, "4c")

    if choice in ("Mission: Descend into the Under-Parvus Catacombs (Route the Fuses!)", "Mission: Route Fuses under Upper Parvus"):
        return ch2_dungeons.init_dungeon(player, "parvus_catacombs")

    if choice in ("Mission: Briefing on the Harbour Festival Climax", "Mission: Assassinate Mayor Holdfast at the Festival!"):
        player["m4e_briefed"] = True
        return player, (
            "=== FINAL MISSION: THE HARBOUR FESTIVAL COUP ===\n"
            "\"The slow-match fuses have shaken Upper Parvus, and today Mayor Holdfast addresses the Harbour Festival from the **Promenade Balcony**!\"\n"
            "\"Speak with **Maeve at The Salted Anchor** to learn the exact bell-stroke timing and rooftop sightline—then give the word to strike!\""
        ), "MAIN"
    if choice == "Mission: Strike at the Upper Parvus Promenade!":
        return init_parvus_minigame(player, "4e")

    return player, "Error.", "MAIN"


def get_eadric_parvus_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []
    if route == "Parvus: Crown Intelligencers":
        if step == 1:
            opts.append("Mission: Briefing on F.A.I. Cell Infiltration" if not player.get("m5a_briefed") else "Mission: Infiltrate the Rope-Walk Cell Meeting!")
        elif step == 2:
            opts.append("Mission: Briefing on the Forged Billeting Flyers" if not player.get("m5b_briefed") else "Mission: Expose the Forged Warrants on the Steps!")
        elif step == 3:
            opts.append("Mission: Briefing on the Bonded Warehouse Double-Sting" if not player.get("m5c_briefed") else "Mission: Spring the Double-Trap at the Warehouses!")
        elif step == 4:
            opts.append("Mission: Descend into the Under-Parvus Catacombs (Defuse the Bomb!)")
        elif step == 5:
            opts.append("Mission: Briefing on the Promenade Balcony Guard" if not player.get("m5e_briefed") else "Mission: Take Post on the Promenade to Foil the Assassin!")
    opts.extend(["Request Watch Intelligence", "Leave"])
    return opts


def resolve_eadric_parvus(choice, player):
    if choice == "Leave":
        return player, "Eadric locks his cipher-ledger inside the Customs House desk.", "MAIN"
    if choice == "Request Watch Intelligence":
        return player, "\"Every tavern and rope-shed in Parvus has ears, agent. Gather your facts before showing your hand.\"", "NPC_DIALOGUE"

    if choice in ("Mission: Briefing on F.A.I. Cell Infiltration", "Mission: Solidify Alibi & Infiltrate the F.A.I."):
        player["m5a_briefed"] = True
        return player, (
            "=== MISSION: INFILTRATING THE SYNDICATE ===\n"
            "Eadric hands you a weathered rigger's tally.\n"
            "\"Our last informer at the **Parvus Rope-Walk** went sloppy and got himself exposed. You are going in to take his place.\"\n"
            "\"Before you present yourself to Speaktruth, talk to **Rigger Ronan** at the Rope-Walk to learn what physical tells and book-passwords the F.A.I. uses to vet recruits!\""
        ), "MAIN"
    if choice == "Mission: Infiltrate the Rope-Walk Cell Meeting!":
        return init_parvus_minigame(player, "5a")

    if choice in ("Mission: Briefing on the Forged Billeting Flyers", "Mission: Intercept & Expose the Forged Orders"):
        player["m5b_briefed"] = True
        return player, (
            "=== MISSION: THE FORGED BILLETING WARRANTS ===\n"
            "\"The F.A.I. has plastered the harbour with forged warrants claiming the Watch is seizing workmen's cottages!\"\n"
            "\"**Search** our **Customs House** here for genuine watermarked stock and speak with **Maeve at The Salted Anchor** to learn how the forgeries were printed—then expose them before the docks riot!\""
        ), "MAIN"
    if choice == "Mission: Expose the Forged Warrants on the Steps!":
        return init_parvus_minigame(player, "5b")

    if choice in ("Mission: Briefing on the Bonded Warehouse Double-Sting", "Mission: Turn the Sting & Arrest Both Syndicates"):
        player["m5c_briefed"] = True
        return player, (
            "=== MISSION: THE DOUBLE-SYNDICATE STING ===\n"
            "\"Tonight, the F.A.I. intends to plant contraband inside the **Kokeshi Bonded Warehouses** while the Kokeshi bosses are inspecting their smuggled arms!\"\n"
            "\"Speak with **Maeve at The Salted Anchor** and **search** the **Bonded Warehouse slipway** so we can bar both exits and arrest BOTH syndicates in a single net!\""
        ), "MAIN"
    if choice == "Mission: Spring the Double-Trap at the Warehouses!":
        return init_parvus_minigame(player, "5c")

    if choice in ("Mission: Descend into the Under-Parvus Catacombs (Defuse the Bomb!)", "Mission: Defuse the Upper Parvus Bomb"):
        return ch2_dungeons.init_dungeon(player, "parvus_catacombs")

    if choice in ("Mission: Briefing on the Promenade Balcony Guard", "Mission: Foil Mayor Holdfast's Assassination!"):
        player["m5e_briefed"] = True
        return player, (
            "=== FINAL MISSION: GUARDING THE HARBOUR FESTIVAL ===\n"
            "\"Even with their cellar bomb defused, a lone F.A.I. marksman is targeting **Mayor Holdfast** on the **Upper Parvus Promenade Balcony** today!\"\n"
            "\"Question **Maeve at The Salted Anchor** about the rooftop sightlines and bell-stroke signal before taking your post!\""
        ), "MAIN"
    if choice == "Mission: Take Post on the Promenade to Foil the Assassin!":
        return init_parvus_minigame(player, "5e")

    return player, "Error.", "MAIN"


def get_buildhope_parvus_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []
    if route == "Parvus: Maritime & Artisans Guild (50s)":
        if step == 1:
            opts.append("Mission: Briefing on the Jammed Harbour Gantry Crane" if not player.get("m6a_briefed") else "Mission: Repair the Crane & Open the Guild Workshop!")
        elif step == 2:
            opts.append("Mission: Briefing on the Counterfeit Foundry Steel" if not player.get("m6b_briefed") else "Mission: Expose the Slag-Iron Fence & Re-Cast the Plates!")
        elif step == 3:
            opts.append("Mission: Briefing on the Smuggled Arms Brigantine" if not player.get("m6c_briefed") else "Mission: Audit the Brigantines & Seize the Arms Cache!")
        elif step == 4:
            opts.append("Mission: Descend into the Under-Parvus Catacombs (Seal the Guild Vaults!)")
        elif step == 5:
            opts.append("Mission: Briefing on the Grand War-Fleet Contract" if not player.get("m6e_briefed") else "Mission: Convene the Admiralty Table & Dictate the Contract!")
    opts.extend(["Talk Commerce", "Leave"])
    return opts


def resolve_buildhope_parvus(choice, player):
    if choice == "Leave":
        return player, "Guildmaster Buildhope adjusts his brass calipers over a ship's draught.", "MAIN"
    if choice == "Talk Commerce":
        return player, "\"Oak, bronze, and honest steel built Parvus—and the Guild will bow to neither syndicalist bombers nor feudal press-gangs.\"", "NPC_DIALOGUE"

    if choice in ("Mission: Briefing on the Jammed Harbour Gantry Crane", "Mission: Fix the Crane & Open the Guild Workshop"):
        player["m6a_briefed"] = True
        return player, (
            "=== MISSION: THE GREAT GANTRY CRANE ===\n"
            "Guildmaster Buildhope points through the casement toward the **Parvus Harbour-Front**.\n"
            "\"Our ten-ton Gantry Crane on the mole is jammed fast, and the crane-riggers have walked off!\"\n"
            "\"Go to the **Harbour-Front** and **search** the crane's worm-gear yourself, and speak with **Rigger Ronan** at the **Rope-Walk** to find out why the crew struck before you call the lift!\""
        ), "MAIN"
    if choice == "Mission: Repair the Crane & Open the Guild Workshop!":
        return init_parvus_minigame(player, "6a")

    if choice in ("Mission: Briefing on the Counterfeit Foundry Steel", "Mission: Expose the Counterfeit Steel Ring"):
        player["m6b_briefed"] = True
        return player, (
            "=== MISSION: THE COUNTERFEIT STEEL RING ===\n"
            "\"Someone has swapped our pure Guild steel at the **Parvus Dry-Dock & Iron Foundry** for brittle bog-slag and stolen our bullion!\"\n"
            "\"Speak with **Foundryman Aldred** and **search** the **quenching trough** at the Dry-Dock, and question **Maeve at The Salted Anchor** to unmask the Kokeshi fence!\""
        ), "MAIN"
    if choice == "Mission: Expose the Slag-Iron Fence & Re-Cast the Plates!":
        return init_parvus_minigame(player, "6b")

    if choice in ("Mission: Briefing on the Smuggled Arms Brigantine", "Mission: Deduce the Kokeshi Contraband Manifest"):
        player["m6c_briefed"] = True
        return player, (
            "=== MISSION: THE CONTRABAND SHIP MANIFEST ===\n"
            "\"One of the three brigantines moored at the **Harbour-Front** is secretly carrying Kokeshi swivel-guns and muskets under a false manifest.\"\n"
            "\"Walk the **Harbour-Front mole** and **search** the ships' Plimsoll waterline marks (or ask **Rigger Ronan**) before boarding the suspect vessel!\""
        ), "MAIN"
    if choice == "Mission: Audit the Brigantines & Seize the Arms Cache!":
        return init_parvus_minigame(player, "6c")

    if choice in ("Mission: Descend into the Under-Parvus Catacombs (Seal the Guild Vaults!)", "Mission: Fortify the Guild Vaults from the Bombing"):
        return ch2_dungeons.init_dungeon(player, "parvus_catacombs")

    if choice in ("Mission: Briefing on the Grand War-Fleet Contract", "Mission: Dictate the Grand War-Fleet Contract!"):
        player["m6e_briefed"] = True
        return player, (
            "=== FINAL MISSION: THE GRAND WAR-FLEET CONTRACT ===\n"
            "\"With our vaults intact and our ships armed, the Crown and the Castellans are begging for the Guild's war-fleet!\"\n"
            "\"Speak with **Foundryman Aldred** at the **Dry-Dock** to confirm the **Three Shipwright Independence Clauses** (and if you delved the **Caligo Silver Mine** for **Star-Iron**, bring it!), then take your seat at the Admiralty table!\""
        ), "MAIN"
    if choice == "Mission: Convene the Admiralty Table & Dictate the Contract!":
        return init_parvus_minigame(player, "6e")

    return player, "Error.", "MAIN"


# =========================================================================
# MODULE REGISTRATION (HANDLERS)
# =========================================================================
HANDLERS = {
    "speaktruth":     (get_speaktruth_parvus_options, resolve_speaktruth_parvus),
    "eadric":         (get_eadric_parvus_options, resolve_eadric_parvus),
    "buildhope":      (get_buildhope_parvus_options, resolve_buildhope_parvus),
    "ronan_rigger":   (get_ronan_options, resolve_ronan),
    "maeve_anchor":   (get_maeve_options, resolve_maeve),
    "aldred_foundry": (get_aldred_options, resolve_aldred),
}
