import random
import pygame
import game_data as db
from mechanics import modify_faction, advance_time, execute_ch2_mission
from ui_components import draw_fitted_text


# =========================================================================
# 1. SHARED 2d6 OUTLAW & TROUPE VARIANCE (WINDFALLS & FRICTION)
# =========================================================================
def roll_roguery_2d6_twist(player, track_kind="outlaw"):
    """
    Rolls 2d6 for Highway Robber (Track 9) and Acting Troupe (Track 10) missions.
    Returns (swing_int, prefix_str, twist_str).
    """
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    swing = (d1 + d2 - 7) * 2
    prefix = f"[Roll {d1}+{d2}={d1+d2}] "
    twist_str = ""

    if random.random() < 0.30:
        if track_kind == "outlaw":
            twists = [
                ("WINDFALL: Inside a fat merchant's boot-lining, you discover an unrecorded pouch of 12 silver! (+12s, +6% Audacity)", 6),
                ("WINDFALL: A thick bank of bracken-mist rolls across the highway, masking your horses' tracks! (+8% Audacity)", 8),
                ("FRICTION: A nervous coach-guard fires a wild blunderbuss blast through the roof! (-6% Audacity)", -6),
            ]
        else:
            twists = [
                ("WINDFALL: A wealthy guild-widow in the front row weeps with laughter and tosses a 10-silver bouquet onto the boards! (+10s, +8% Applause)", 8),
                ("WINDFALL: The street acoustics carry your punchline clear across the canal! (+8% Applause)", 8),
                ("FRICTION: A sudden gust of wind rips a painted canvas backdrop off its frame! (-6% Applause)", -6),
            ]
        t_text, mod = random.choice(twists)
        swing += mod
        if "+12s" in t_text:
            player["silver"] += 12
        elif "+10s" in t_text:
            player["silver"] += 10
        twist_str = f" [{t_text}]"

    return swing, prefix, twist_str


# =========================================================================
# 2. DISCOVERABLE NPCS FOR TRACKS 9 & 10 (OUTRIDER BRAN & SILKTONGUE)
# =========================================================================
def get_bran_options(player):
    opts = ["Ask about the coaches leaving Murum"]
    step = player.get("ch2_mission_step", 1)
    if step == 1:
        opts.insert(0, "Ask for the timetable & weak-point of the Bullion Coach")
    elif step == 4:
        opts.insert(0, "Ask where the real tribute chest is hidden on the Mayor's Coach")
    opts.append("Leave")
    return opts


def resolve_bran(choice, player):
    if choice == "Leave":
        return player, "Outrider Bran spits straw from his teeth and Tightens a saddle-girth.", "MAIN"

    if choice == "Ask about the coaches leaving Murum":
        return player, (
            "Bran grins crookedly beneath his slouched hat.\n"
            "\"Every heavy axle that rolls out of Murum Gate passes under my eye, friend—and for a share of the take, a wise highwayman never robs the wrong box.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask for the timetable & weak-point of the Bullion Coach":
        player["rg_bran_coach_clue"] = True
        return player, (
            "Bran leans against the stable post and whispers:\n"
            "\"That 'wool-merchant's carriage' heading north up **the New Road** today is actually carrying a **Kokeshi Syndicate payroll chest**!\"\n"
            "\"I filed halfway through its left iron trace-chain myself and tied a **white silk ribbon** under the lamp. "
            "If you **search** the **Muddy Hollow on the New Road** north of the Frontier Watchpost to rig a sawn pine-tree across the ruts, the team will snap its traces on the spot!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask where the real tribute chest is hidden on the Mayor's Coach":
        player["rg_bran_mayor_clue"] = True
        return player, (
            "Bran chuckles softly.\n"
            "\"Watch Lieutenant Beornraed thinks he's clever—he strapped a lead-weighted **decoy chest** to the roof-rack of Mayor Givethanks' coach! "
            "Don't waste a second on the roof: the real municipal tribute silver is bolted inside the **false footman's boot under the driver's bench**!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_silktongue_options(player):
    opts = ["Ask about Fairlight's repertoire"]
    step = player.get("ch2_mission_step", 1)
    if step == 1:
        opts.insert(0, "Ask what the three secret envoys backstage are offering")
    elif step == 2:
        opts.insert(0, "Ask where the quick-change hampers are hidden in Fluvius Town")
    elif step == 4:
        opts.insert(0, "Ask how to slip behind the Great Hall tapestries at Castle Ragmore")
    opts.append("Leave")
    return opts


def resolve_silktongue(choice, player):
    if choice == "Leave":
        return player, "Silktongue dusts a papier-mâché crown with a feather duster.", "MAIN"

    if choice == "Ask about Fairlight's repertoire":
        return player, (
            "\"Tragedy for the lords, satire for the commons, and pickpocketing for the intermission!\" Silktongue beams."
        ), "NPC_DIALOGUE"

    if choice == "Ask what the three secret envoys backstage are offering":
        player["rg_silk_envoys_clue"] = True
        return player, (
            "Silktongue peers through the stage-curtain peephole.\n"
            "\"Three faction envoys are waiting in our dressing-rooms right now—one from **Castellan Hrothgar**, one from the **Union**, and one from the **Kokeshi Syndicate**.\"\n"
            "\"Here is the trick: none of them knows the other two are in the building! If you promise the Castellan's man a *heroic chivalric prologue*, the Union organiser a *biting comic interlude*, and the Kokeshi factor a *subtle street diversion*, you can pocket all three purses without a single contradiction!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask where the quick-change hampers are hidden in Fluvius Town":
        player["rg_silk_riot_clue"] = True
        return player, (
            "\"I sent our wicker costume hamper ahead to the **Shadowed Cul-de-Sac behind the Fluvius Civic Clock-Tower**,\" Silktongue whispers.\n"
            "\"Go to **Fluvius Town** and **search** behind the Clock-Tower to lay out our reversible beggar-cloaks before we start the masquerade in the square—that way, the moment Constable Ælfwine's Watchmen charge, we duck into the alley, peel off the false Castellan moustaches, and stroll out as innocent townsfolk!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask how to slip behind the Great Hall tapestries at Castle Ragmore":
        player["rg_silk_ragmore_clue"] = True
        return player, (
            "Silktongue holds up a small brass vial of theatrical spirit-gum.\n"
            "\"Before Fairlight begins the Command Performance at **Castle Ragmore**, walk into the **Inner Bailey** and **search** behind the Great Hall tapestries to grease the latch of Lord Hrothgar's map-room with this spirit-gum! "
            "Then, during the second-act drumroll, you can slip backstage and copy his war-dispatches without a sound!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 3. ENVIRONMENTAL SEARCH HOOKS FOR TRACKS 9 & 10
# =========================================================================
def handle_roguery_search(player):
    """
    Called inside action_gather() for Highway Robber (Track 9) and Acting Troupe (Track 10).
    Returns (handled_bool, log_message).
    """
    pos = (player["x"], player["y"])
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)

    # --- TRACK 9 (HIGHWAY ROBBER) SEARCH DISCOVERIES ---
    if route == "Become a Highway Robber" and not player.get("current_building"):
        # 9A: Search the Muddy Hollow on the New Road (7, 22) to rig the timber ambush!
        if pos == (7, 22) and step == 1:
            if player.get("rg_9a_tree_rigged"):
                return True, "The sawn pine-trunk above the Muddy Hollow is already rigged with your hemp trip-hawser."
            player["rg_9a_tree_rigged"] = True
            player, _ = advance_time(20, player)
            return True, (
                "Climbing the gorse bank above the **Muddy Hollow**, you saw three-quarters through a leaning pine trunk and run a taut hemp haul-rope back into the bracken—ready to drop the tree right in front of the bullion coach's horses!"
            )

        # 9B: Search the Diluvium Glade (8, 20) or (10, 22) to rig blackthorn snares for the Kokeshi hit-squad!
        if pos in ((8, 20), (10, 22)) and step == 2:
            if player.get("rg_9b_briars_rigged"):
                return True, "Your blackthorn whip-snares and bog-pit covers are already set across the Diluvium Glade approaches."
            player["rg_9b_briars_rigged"] = True
            player, _ = advance_time(20, player)
            return True, (
                "Working among the standing stones and blackthorn arches of **The Diluvium Glade**, you bend three iron-hard thorn-boughs across the false bog paths—turning the labyrinth into a deadly kill-zone for the pursuing Kokeshi hit-squad!"
            )

        # 9C: Search the Sunken Sluice-Gate Lane (10, 5) to spot the Bailiff's Pay-Wagon!
        if pos == (10, 5) and step == 3:
            if player.get("rg_9c_wagon_scouted"):
                return True, "You have alreadycharted the blind-spot behind the Sunken Lane embankment where the Bailiff's pay-wagon is halted."
            player["rg_9c_wagon_scouted"] = True
            player, _ = advance_time(15, player)
            return True, (
                "Peering down from the high clay lip of the **Sunken Sluice-Gate Lane**, you spot Bailiff Seekgrace's iron-bound pay-wagon stuck at the rear of the Kokeshi column while the guards are all staring ahead at the crossroads picket brazier!"
            )

        # 9E: Search the Washed-Out Gorge (13, 16) or Collapsed Span (16, 10) to rig the War-Train bottleneck!
        if pos in ((13, 16), (16, 10)) and step == 5:
            if player.get("rg_9e_gorge_rigged"):
                return True, "The gorge-bridge abutments are already packed with blasting-wedges to halt the military munitions train."
            player["rg_9e_gorge_rigged"] = True
            player, _ = advance_time(25, player)
            return True, (
                "Clambering beneath the timber stringers of the river-gorge crossing, you wedge iron splitting-chocks and tarred slow-match cord against the central trestle—allowing you to drop the span the instant the lead munitions wagon crosses!"
            )

    # --- TRACK 10 (ACTING TROUPE) SEARCH DISCOVERIES ---
    if route == "Join Fairlight's Acting Troupe":
        # 10B: Search the Fluvius Clock-Tower Cul-de-Sac (12, 2) to stage quick-change hampers!
        if pos == (12, 2) and step == 2 and not player.get("current_building"):
            if player.get("rg_10b_hampers_staged"):
                return True, "Your quick-change hampers and reversible cloaks are already staged in the shadowed cul-de-sac behind the Clock-Tower."
            player["rg_10b_hampers_staged"] = True
            player, _ = advance_time(15, player)
            return True, (
                "Slipping into the shadowed cul-de-sac behind the **Fluvius Civic Clock-Tower**, you unlatch the troupe's wicker hamper, lay out reversible town-cloaks, and prop the back alley gate for an instant quick-change escape!"
            )

        # 10D: Search Castle Ragmore Inner Bailey (4, 22) to grease the map-room latch!
        if pos in ((3, 22), (4, 22)) and step == 4 and not player.get("current_building"):
            if player.get("rg_10d_latch_greased"):
                return True, "The brass latch behind the Great Hall tapestries is already greased with spirit-gum and wedged with a folded playbill."
            player["rg_10d_latch_greased"] = True
            player, _ = advance_time(15, player)
            return True, (
                "While helping unload the stage-props in **Castle Ragmore's Inner Bailey**, you slip behind the Great Hall arras, coat the brass latch of Lord Hrothgar's war-map study in silent spirit-gum, and take a wax impression of the coat-room chest!"
            )

        # 10E: Search Fluvius Counting House Square (11, 4) or Parvus Promenade (17, 22) to rig stage-chains!
        if pos in ((11, 4), (17, 22)) and step == 5 and not player.get("current_building"):
            if player.get("rg_10e_doors_rigged"):
                return True, "Heavy oak bracing-timbers and acoustic megaphones are already rigged around the grand stage."
            player["rg_10e_doors_rigged"] = True
            player, _ = advance_time(15, player)
            return True, (
                "Inspecting the grand festival stage before the premiere, you rig heavy oak drop-bars across the side-galleries and position brass speaking-trumpets along the footlights—ensuring the Watch cannot storm the stage before your final act!"
            )

    return False, ""


# =========================================================================
# 4. TRACKS 9 & 10 SCENARIOS (MINIGAME_ROGUERY POP-OUT ENGINE)
# =========================================================================
ROGUERY_SCENARIOS = {
    # ------------------------------------------------------------------
    # TRACK 9: HIGHWAY ROBBER (9A, 9B, 9C, 9D, 9E)
    # ------------------------------------------------------------------
    "9a": {
        "track": "outlaw",
        "header": "NEW ROAD MUDDY HOLLOW — THE BULLION COACH HOLD-UP",
        "prep_flag": "rg_9a_tree_rigged",
        "prep_label": "Sawn Pine-Tree Trap & Filed Left Trace-Chain Intel",
        "stages": [
            {
                "title": "STAGE 1/3: SPRINGING THE TIMBER TRAP!",
                "desc": "The disguised bullion coach—marked with Outrider Bran's white silk ribbon—rumbles down into the Muddy Hollow! How do you halt the team?",
                "opts": [
                    ("Haul the hemp cable to drop the sawn pine-tree right across the ruts! (2d6)", 26),
                    ("Loose a longbow shaft through the coachman's tall hat (2d6)", 20),
                    ("Leap into the road waving a club in front of the galloping horses", -18),
                ],
            },
            {
                "title": "STAGE 2/3: SILENCING THE ESCORT",
                "desc": "As the horses rear and the filed left trace-chain snaps clean in two, two armed guards scramble for their blunderbusses!",
                "opts": [
                    ("Vault from the high bank & disarm the guards before they can prime powder! (2d6)", 26),
                    ("Roar Black Dog's outlaw war-cry from both sides of the gorse (2d6)", 18),
                    ("Trade open pistol shots in the middle of the highway", -15),
                ],
            },
            {
                "title": "STAGE 3/3: CRACKING THE IRON STRONGBOX",
                "desc": "Inside the coach floor sits a heavy iron-bound strongbox stamped with a strange black-iron seal!",
                "opts": [
                    ("Use the crooked outrider's inside bolt-key to pop the lid & take 50s! (2d6)", 25),
                    ("Smash the padlock with a heavy iron prybar (2d6)", 18),
                    ("Try to carry the 200-lb iron box on your back", -15),
                ],
            },
        ],
    },
    "9b": {
        "track": "outlaw",
        "header": "DILUVIUM BRIAR-MAZE — HUNTING THE KOKESHI HIT-SQUAD",
        "prep_flag": "rg_9b_briars_rigged",
        "prep_label": "Blackthorn Whip-Snares & Briar-Labyrinth Paths Mapped",
        "stages": [
            {
                "title": "CHAMBER 1/3: BAITING THE LABYRINTH ARCHWAY",
                "desc": "Black Dog warns you: that stolen chest belonged to the **Kokeshi Syndicate**, and six of their elite assassins have tracked you to the Diluvium Glade!",
                "opts": [
                    ("Drop a trail of copper coins to lure them into the Bog-Gas East Tunnel! (2d6)", 26),
                    ("Hide in the silvery-lichen Northern Arch with crossbows cocked (2d6)", 20),
                    ("Stand out in the open glade and wait for all six assassins", -20),
                ],
            },
            {
                "title": "CHAMBER 2/3: THE BLACKTHORN WHIP-SNARES!",
                "desc": "Coughing from the bog-fumes, the Kokeshi squad stumbles deeper into the twenty-foot blackthorn hedges!",
                "opts": [
                    ("Cut the trip-cord on your rigged Blackthorn Whip-Snares! (2d6)", 28),
                    ("Pick off their lantern-bearer from the violet-arch shadows (2d6)", 20),
                    ("Crash noisily through the deadwood twigs", -18),
                ],
            },
            {
                "title": "CHAMBER 3/3: SENDING A MESSAGE TO THE DIEWELL",
                "desc": "With the Kokeshi hit-squad tangled and disarmed in the thorns, their captain glares up at your blade.",
                "opts": [
                    ("Strip their weapons & send one man back to tell The Diewell the roads are yours! (2d6)", 24),
                    ("Ransom their Kokeshi signet rings for an extra 20 silver (2d6)", 20),
                    ("Let them keep their blades and walk free", -18),
                ],
            },
        ],
    },
    "9c": {
        "track": "outlaw",
        "header": "SUNKEN SLUICE-GATE LANE — THE STRIKE PAY-WAGON HEIST",
        "prep_flag": "rg_9c_wagon_scouted",
        "prep_label": "Sunken Lane Blind-Spot & Pay-Wagon Rear Guard Mapped",
        "stages": [
            {
                "title": "STAGE 1/3: THE SMOKE AT THE CROSSROADS",
                "desc": "Ahead at the Fluvius Crossroads, Union strikers, Kokeshi bruisers, and the Town Watch are locked in a deafening standoff—leaving the Bailiff's pay-wagon trailing in the Sunken Lane!",
                "opts": [
                    ("Drop silently from the high clay embankment onto the rear tailboard! (2d6)", 26),
                    ("Toss a peat-smoke bundle under the mules' noses to mask your approach (2d6)", 20),
                    ("Gallop straight past Watch Sergeant Beornraed's lancers", -22),
                ],
            },
            {
                "title": "STAGE 2/3: UNCHAINING THE BAILIFF'S WAGE-CHEST",
                "desc": "The Bailiff's pay-clerk spins around on the wagon bench, reaching for a brass alarm-bell!",
                "opts": [
                    ("Gag the clerk with his own ledger-sack & unpin the iron wage-chest! (2d6)", 26),
                    ("Cut the trace-leather and ride off on the lead pay-mule (2d6)", 18),
                    ("Let the clerk ring the brass bell and fight the whole guard squad", -20),
                ],
            },
            {
                "title": "STAGE 3/3: VANISHING INTO THE WESTERN HEATH",
                "desc": "With 40 silver in strikebreaker wages slung across your saddle, whistles finally sound from the ridge!",
                "opts": [
                    ("Spur your mount up the dry irrigation berm into the Heath mist! (2d6)", 24),
                    ("Scatter a handful of copper pennies in the mud to stall the pursuers (2d6)", 18),
                    ("Ride down into the axle-deep red clay mire", -18),
                ],
            },
        ],
    },
    "9d": {
        "track": "outlaw",
        "header": "RAGMORE HIGHWAY — THE MAYORAL CONVOY HIJACK",
        "prep_flag": "rg_bran_mayor_clue",
        "prep_label": "Outrider Bran's False Footman's Boot Intel (Bypassing Roof Decoy)",
        "stages": [
            {
                "title": "STAGE 1/3: DIVERTING THE WATCH VANGUARD",
                "desc": "Mayor Givethanks' armored state coach rolls up the New Road toward Castle Ragmore, flanked by Watch halberdiers!",
                "opts": [
                    ("Light brushwood decoy-fires on the east bank to draw the Watch screen away! (2d6)", 25),
                    ("Loose warning shafts from the gorse to split the outriders (2d6)", 18),
                    ("Charge directly into a wall of levelled Watch halberds", -22),
                ],
            },
            {
                "title": "STAGE 2/3: THE DECOY CHEST VS. THE FOOTMAN'S BOOT!",
                "desc": "Swinging alongside the lurching carriage, you see an iron-bound chest strapped to the roof—and a locked oak boot beneath the driver's bench!",
                "opts": [
                    ("Ignore the lead roof-decoy & pry open the Footman's Boot for the real tribute! (2d6)", 28),
                    ("Cut the leather straps on both boxes and test their weight (2d6)", 16),
                    ("Steal the lead-filled roof decoy chest and flee", -25),
                ],
            },
            {
                "title": "STAGE 3/3: THE HIGHWAYMAN'S BOW",
                "desc": "Mayor Givethanks peers terrified through the coach window as you hoist the municipal tribute bags onto your saddle!",
                "opts": [
                    ("Doff your hat gallantly to the Mayor & vault into the forest eaves! (2d6)", 24),
                    ("Take the Mayor's gold chain of office as a souvenir (2d6)", 18),
                    ("Linger on the highway while Ragmore lancers ride down from the keep", -18),
                ],
            },
        ],
    },
    "9e": {
        "track": "outlaw",
        "header": "RIVER GORGE CROSSING — THE GREAT WAR-TRAIN HEIST",
        "prep_flag": "rg_9e_gorge_rigged",
        "prep_label": "Gorge-Bridge Trestle Chocks & Sapper Blueprint Rigged",
        "stages": [
            {
                "title": "HEIST STAGE 1/3: THE BOTTLENECK AT THE GORGE!",
                "desc": "On the eve of war, the grand military munitions and war-chest train rumbles onto the narrow river-gorge span! Black Dog's entire outlaw host awaits your signal!",
                "opts": [
                    ("Knock out the rigged trestle-chocks to trap the payroll & powder wains! (2d6)", 28),
                    ("Fell two tall pine trunks behind the rear escort column (2d6)", 20),
                    ("Attack on the open plains before the train reaches the bridge", -20),
                ],
            },
            {
                "title": "HEIST STAGE 2/3: SEIZING THE CASTELLAN'S MUNITIONS!",
                "desc": "Caught on the bottlenecked span, the elite men-at-arms form a ring around the brass culverin-cannon and the iron war-chest!",
                "opts": [
                    ("Turn the lead swivel-gun on the escort & force their surrender! (2d6)", 28),
                    ("Lead Black Dog's boarding party across the wagon roofs! (2d6)", 22),
                    ("Let the escort pitch the war-chest into the river gorge", -22),
                ],
            },
            {
                "title": "HEIST STAGE 3/3: PROCLAIMING THE OUTLAW FREE-STATE!",
                "desc": "With fifty barrels of gunpowder, a hundred muskets, and the war-treasury in your hands, every highwayman from the Heath to Diluvium hails you as King of the Roads!",
                "opts": [
                    ("Fortify the Diluvium & Old Path passes as the Outlaw Free-State! (2d6)", 25),
                    ("Share out a 50-silver war-dividend to every rider in the gang! (2d6)", 20),
                    ("Squabble over the loot while the army regroups", -18),
                ],
            },
        ],
    },

    # ------------------------------------------------------------------
    # TRACK 10: FAIRLIGHT'S ACTING TROUPE (10A, 10B, 10C, 10D, 10E)
    # ------------------------------------------------------------------
    "10a": {
        "track": "troupe",
        "header": "MURUM PLAYHOUSE BACKSTAGE — THE PATRONAGE AUCTION",
        "prep_flag": "rg_silk_envoys_clue",
        "prep_label": "Silktongue's Three-Envoy Dressing-Room Schedule",
        "stages": [
            {
                "title": "ACT 1/3: ENVOYS IN THREE DRESSING ROOMS",
                "desc": "Backstage at the Murum Playhouse, envoys from the Castellan, the Union, and the Kokeshi Syndicate have each arrived in secret to buy your troupe's regional tour!",
                "opts": [
                    ("Keep them in separate rooms & promise each their own tailored act! (2d6)", 26),
                    ("Charm the Castellan and Union envoys with wine and verse (2d6)", 18),
                    ("Invite all three rival envoys into the same room at once", -22),
                ],
            },
            {
                "title": "ACT 2/3: BIDDING UP THE PATRONAGE PURSES",
                "desc": "Each envoy slides a leather purse across the dressing-table, asking if your play will champion *their* cause exclusively.",
                "opts": [
                    ("Play their anxieties off each other to extract all three purses (+40s)! (2d6)", 28),
                    ("Accept standard patronage fees from two of the factions (2d6)", 18),
                    ("Insult the patrons and refuse their silver", -18),
                ],
            },
            {
                "title": "ACT 3/3: PACKING THE PAINTED STAGE-WAGON",
                "desc": "With 40 silver jingling in the troupe's strongbox, Fairlight orders the stage-wagon loaded for Fluvius!",
                "opts": [
                    ("Pack reversible bailiff livery, satirical masks & double-bottom trunks! (2d6)", 24),
                    ("Hire two extra jugglers and a brass trumpeter for the road (2d6)", 18),
                    ("Leave half the costumes behind in Murum", -12),
                ],
            },
        ],
    },
    "10b": {
        "track": "troupe",
        "header": "FLUVIUS MARKET SQUARE — THE MASQUERADE RIOT",
        "prep_flag": "rg_10b_hampers_staged",
        "prep_label": "Quick-Change Hampers Staged Behind Civic Clock-Tower",
        "stages": [
            {
                "title": "SCENE 1/3: THE ARROGANT 'BAILIFFS' ENTER!",
                "desc": "Dressed in papier-mâché Castellan crests and horsehair moustaches, you and Fairlight stride into Fluvius Square to incite a diversionary riot!",
                "opts": [
                    ("Declaim a pompous 'Tenfold Breathing-Tax' in booming blank verse! (2d6)", 26),
                    ("Dramatically tip over a prop apple-cart (after slipping the widow 2s)! (2d6)", 22),
                    ("Mumble your lines so the crowd barely notices you", -18),
                ],
            },
            {
                "title": "SCENE 2/3: WHIPPING UP THE CROWD!",
                "desc": "Bargemen and cobblers roar in outrage, wrenching up cobblestones as Constable Ælfwine's Watch squad rushes toward the square!",
                "opts": [
                    ("Gesture dramatically toward the Counting House so the mob surrounds the Watch! (2d6)", 25),
                    ("Toss theatrical smoke-marbles into the gutter for chaos (2d6)", 18),
                    ("Stay still until Constable Ælfwine grabs your collar", -22),
                ],
            },
            {
                "title": "SCENE 3/3: THE CLOCK-TOWER QUICK-CHANGE!",
                "desc": "With the entire Town Watch pinned down in the square (allowing the Kokeshi cargo to slip past), you sprint into the Clock-Tower cul-de-sac!",
                "opts": [
                    ("Peel off the false moustaches at your staged hamper & stroll out in peasant smocks! (2d6)", 28),
                    ("Climb onto the slate roof above the square to watch the show (2d6)", 18),
                    ("Run through the streets still wearing the fake bailiff tabards", -20),
                ],
            },
        ],
    },
    "10c": {
        "track": "troupe",
        "header": "FLUVIUS FARM CROSSROADS — THE BARRICADE SATIRE",
        "prep_flag": "m1c_learned_scab_motive",
        "prep_label": "Bailiff Seekgrace's Pipe-Bluff & Corban's Mule-Debt Gossip",
        "stages": [
            {
                "title": "VERSE 1/3: ROLLING UP TO THE PICKET BRAZIER",
                "desc": "At the Fluvius Farm Crossroads, strikers and Kokeshi scabs are seconds from bloodshed when Fairlight drops the painted stage-wagon tailgate right between them!",
                "opts": [
                    ("Strike up a thunderous drum-fanfare & step out in oversized caricature masks! (2d6)", 25),
                    ("Juggle blazing brands from the picket brazier to freeze both lines (2d6)", 20),
                    ("Hide inside the wagon while stones fly", -18),
                ],
            },
            {
                "title": "VERSE 2/3: THE BALLAD OF THE EMPTY RENT-CHEST!",
                "desc": "Both strikers and Caligo quarry drivers lower their fists to watch as you lampoon Bailiff Seekgrace and Wagon-Boss Corban!",
                "opts": [
                    ("Perform 'Old Seekgrace's Empty Pipe & Corban's Stolen Mules'—shaming the scabs! (2d6)", 28),
                    ("Imitate Sergeant Beornraed's stiff halberd-drill to make the Watch laugh (2d6)", 22),
                    ("Forget your verses and insult the farmhands", -20),
                ],
            },
            {
                "title": "VERSE 3/3: THE CURTAIN CALL AT THE BARRICADE",
                "desc": "Roaring with laughter and stung with shame, half the strikebreakers toss down their whips and join the applause!",
                "opts": [
                    ("Take a sweeping bow as the strikers hail the Troupe as heroes of the commons! (2d6)", 24),
                    ("Pass the velvet hat among the laughing Watch lancers (+15s) (2d6)", 20),
                    ("Pack up hastily without taking a bow", -10),
                ],
            },
        ],
    },
    "10d": {
        "track": "troupe",
        "header": "CASTLE RAGMORE GREAT HALL — COMMAND PERFORMANCE ESPIONAGE",
        "prep_flag": "rg_10d_latch_greased",
        "prep_label": "Spirit-Gummed Map-Room Latch & Coat-Room Key Impression",
        "stages": [
            {
                "title": "ACT 1/3: HOLDING THE HIGH TABLE SPELLBOUND",
                "desc": "In the torchlit Great Hall of Castle Ragmore, Lord Hrothgar, Mayor Givethanks, and the baronial knights lean forward as the masque begins!",
                "opts": [
                    ("Deliver a booming chivalric soliloquy that fixes every eye on the stage! (2d6)", 25),
                    ("Cue the lute-players and fire-eaters for a dazzling spectacle (2d6)", 20),
                    ("Stumble over your opening lines", -18),
                ],
            },
            {
                "title": "ACT 2/3: BEHIND THE GREAT HALL TAPESTRIES!",
                "desc": "While Fairlight commands the spotlight during the grand battle-pantomime, you slip behind the velvet arras toward Hrothgar's study and the lords' cloak-room!",
                "opts": [
                    ("Slide open the Spirit-Gummed Latch & copy the war-plans and election blackmail! (2d6)", 28),
                    ("Rifle the magistrates' velvet cloaks for signet-letters and coin (+20s) (2d6)", 22),
                    ("Knock over a suit of decorative plate-armour in the corridor", -22),
                ],
            },
            {
                "title": "ACT 3/3: REJOINING THE GRAND FINALE",
                "desc": "With the stolen war-ciphers tucked safely inside your doublet lining, Fairlight gives your cue for the final verse!",
                "opts": [
                    ("Step smoothly through the curtain on cue & take a standing ovation from Hrothgar! (2d6)", 25),
                    ("Present Lord Hrothgar with a flattering dedicatory scroll (2d6)", 18),
                    ("Arrive late on stage out of breath", -15),
                ],
            },
        ],
    },
    "10e": {
        "track": "troupe",
        "header": "THE GRAND STAGE — THE ELECTION-EVE REVOLUTIONARY PREMIERE",
        "prep_flag": "rg_10e_doors_rigged",
        "prep_label": "Barred Gallery Doors & Brass Footlight Speaking-Trumpets",
        "stages": [
            {
                "title": "PREMIERE ACT 1/3: PACKING THE AMPHITHEATRE!",
                "desc": "Thousands of townsfolk, farmhands, sailors, and off-duty Watchmen pack the square for Fairlight's Election-Eve Premiere: *The Masque of the Broken Crown*!",
                "opts": [
                    ("Project through the Brass Speaking-Trumpets so every street hears the prologue! (2d6)", 26),
                    ("Shower crimson-and-gold playbills from the upper gallery (2d6)", 20),
                    ("Start the play with a dry, academic lecture", -15),
                ],
            },
            {
                "title": "PREMIERE ACT 2/3: DEFYING THE MARTIAL-LAW CENSORS!",
                "desc": "Outraged by your play's exposure of feudal warmongering and Kokeshi corruption, bailiffs hammer on the side-doors demanding the curtain be dropped!",
                "opts": [
                    ("Drop the rigged Oak Barricade-Bars & weave the bailiffs' banging into the script! (2d6)", 28),
                    ("Have the audience link arms twelve-deep around the stage steps (2d6)", 22),
                    ("Cut the third act short out of fear", -25),
                ],
            },
            {
                "title": "PREMIERE ACT 3/3: THE CATHARSIS OF THE COMMONS!",
                "desc": "As you unveil the stolen war-maps and blackmail ledgers on stage as 'props', the entire town rises to its feet in an earth-shaking roar!",
                "opts": [
                    ("Lead the crowd in the Oath of Popular Sovereignty—refusing feudal conscription! (2d6)", 28),
                    ("Ring the civic bells and crown the People's Assembly on stage! (2d6)", 22),
                    ("Slip out the back door before the applause ends", -10),
                ],
            },
        ],
    },
}


def init_roguery_minigame(player, mission_code):
    """Initializes the unified 680x480 Pop-Out Window for any Track 9 or Track 10 mission."""
    if "ancient sapper's blueprint" in player.get("inventory", []):
        player["rg_9e_gorge_rigged"] = True
    if player.get("bailiff_tells_learned"):
        player["m1c_learned_scab_motive"] = True

    scen = ROGUERY_SCENARIOS[mission_code]
    player["rg_code"] = mission_code
    player["rg_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["rg_stage"] = 0

    base_prog = (
        35
        + (player.get("stealth", 0) * 2)
        + (player.get("charisma", 0) * 2)
        + (player.get("strength", 0) * 2)
    )
    if player.get(scen["prep_flag"]):
        base_prog += 18

    player["rg_progress"] = min(68, base_prog)
    player["rg_feedback"] = (
        f"Operation Underway: {scen['header']}. "
        "Complete all 3 stages and drive Audacity/Applause to 75%+ (each choice rolls 2d6 + your preparation & twists)!"
    )
    return player, player["rg_feedback"], "MINIGAME_ROGUERY"


def roguery_action(choice_idx, player):
    """Processes a stage choice (0, 1, or 2) in MINIGAME_ROGUERY with 2d6 rolls & twists."""
    code = player.get("rg_code", "9a")
    scen = ROGUERY_SCENARIOS[code]

    if player.get("rg_phase") == "RESULT":
        return conclude_roguery_minigame(player)

    st_idx = player.get("rg_stage", 0)
    st_data = scen["stages"][st_idx]
    opt_label, base_delta = st_data["opts"][choice_idx]

    swing, prefix, twist_str = roll_roguery_2d6_twist(player, track_kind=scen["track"])
    has_prep = player.get(scen["prep_flag"], False)
    prep_bonus = 6 if (choice_idx == 0 and has_prep) else 0

    if choice_idx == 0 and not has_prep and base_delta >= 25:
        actual_delta = 12 + (swing // 2)
        note = f"You improvise '{opt_label.split(' (')[0]}' on the fly without having pre-rigged the site!"
    else:
        actual_delta = base_delta + prep_bonus + (swing // 2)
        note = f"Executed: {opt_label.split(' (')[0]}!"

    player["rg_progress"] = max(0, min(100, player.get("rg_progress", 40) + actual_delta))
    full_msg = f"{prefix}{note} ({'+' if actual_delta >= 0 else ''}{actual_delta}%){twist_str}"

    if st_idx >= 2:
        player["rg_phase"] = "RESULT"
        tag = "MASTERSTROKE!" if player["rg_progress"] >= 75 else "SCRAPED THROUGH!"
        player["rg_feedback"] = f"{full_msg} — [{tag} ({player['rg_progress']}%)] Click [Conclude Mission >>]!"
        return player, player["rg_feedback"], "MINIGAME_ROGUERY"

    player["rg_stage"] = st_idx + 1
    player["rg_feedback"] = full_msg
    return player, None, "MINIGAME_ROGUERY"


def conclude_roguery_minigame(player):
    code = player.get("rg_code", "9a")
    prog = player.get("rg_progress", 0)
    player["active_ch2_mission"] = None

    letter = code[-1]
    step_num = ord(letter) - ord('a') + 1
    player["ch2_mission_step"] = step_num + 1

    success = (prog >= 75)
    gain = 22 if success else 10
    player["position_strength"] = min(100, player.get("position_strength", 0) + gain)
    if not success:
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1

    # Award heist/patronage silver payouts matching the original design
    if code == "9a":
        player["silver"] += 50 if success else 25
    elif code == "9c":
        player["silver"] += 40 if success else 15
    elif code == "9d":
        player["silver"] += 35 if success else 15
        player["stealth"] = player.get("stealth", 0) + 1
    elif code == "10a":
        player["silver"] += 40 if success else 20
    elif code == "10c":
        modify_faction(player, "faction_union", 1)
    elif code == "10d":
        player["stealth"] = player.get("stealth", 0) + 1
        player["silver"] += 20 if success else 5

    # Check if this was the Finale (9E or 10E)!
    if code == "9e":
        win_heist = (prog >= 70)
        player.setdefault("ch3_world_bits", {})["track_9"] = 1 if win_heist else 0
        if win_heist:
            player["silver"] += 50
            player["reputation"] = player.get("reputation", 0) - 3
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: THE OUTLAW FREE-STATE!           \n"
                "=========================================================\n"
                "You hijack the military munitions train at the river-gorge! Armed with culverins, muskets, and a massive war-chest (+50 Silver), "
                "Black Dog's Outlaw Free-State commands the frontier highways as Chapter 3 begins!\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
            )
        else:
            player["exposure_tells"] = player.get("exposure_tells", 0) + 2
            log = (
                "=== MISSION FAILED: OUTLAWS CRUSHED BY MARTIAL LAW! ===\n"
                "The heavy escort breaks through your gorge trap and scatters the highway gangs into the hills!"
            )
        return player, log, "CHAPTER_2_COMPLETE"

    if code == "10e":
        win_play = (prog >= 70)
        player.setdefault("ch3_world_bits", {})["track_10"] = 1 if win_play else 0
        if win_play:
            player["reputation"] = player.get("reputation", 0) + 4
            log = (
                "=========================================================\n"
                "   MISSION COMPLETE: STANDING OVATION OF THE PEOPLE! \n"
                "=========================================================\n"
                "Your election-eve premiere ignites the spirit of Dtessera Terra! The townsfolk refuse feudal conscription and rally to popular sovereignty as the curtain rises on Chapter 3!\n"
                f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
            )
        else:
            player["exposure_tells"] = player.get("exposure_tells", 0) + 2
            log = (
                "=== MISSION FAILED: CLOSED BY THE CENSORS! ===\n"
                "Before the final act, bailiffs storm the stage and shut down the performance under martial law!"
            )
        return player, log, "CHAPTER_2_COMPLETE"

    # Next-step hints without coordinate tuples
    hints = {
        "9a": "Black Dog discovers the stolen chest bears the **Kokeshi Syndicate seal**—and a Kokeshi hit-squad is hunting you! **Search** the **Diluvium Glade** to rig blackthorn snares before speaking to Black Dog for **9B**!",
        "9b": "Ride south to the **Sunken Sluice-Gate Lane** west of the Fluvius Crossroads and **search** the embankment to spot the Bailiff's pay-wagon before launching **9C**!",
        "9c": "Question **Outrider Bran** outside **Murum Stables** to learn where the real tribute silver is hidden on the Mayor's coach before ambushing the convoy in **9D**!",
        "9d": "**Search** the **Washed-Out Gorge / Collapsed Span** (or bring the **Ancient Sapper's Blueprint**) to rig the bridge before launching **9E: The Great War-Train Heist**!",
        "10a": "Travel to **Fluvius Town** and **search** the **Shadowed Cul-de-Sac behind the Civic Clock-Tower** to stage your quick-change hampers before speaking to Fairlight for **10B: The Masquerade Riot**!",
        "10b": "Gather gossip on Bailiff Seekgrace's empty pipe and Corban's mules in **Fluvius Town**, then join Fairlight at the **Farm Picket Crossroads** for **10C: The Barricade Satire**!",
        "10c": "Travel north to **Castle Ragmore**, speak with **Silktongue**, and **search** the **Inner Bailey** tapestries before performing **10D: The Command Performance**!",
        "10d": "**Search** the grand stage in **Fluvius Counting House Square** (or **Upper Parvus Promenade**) to bar the gallery doors against censors before launching **10E: The Grand Premiere**!",
    }
    log = (
        f"=== MISSION {code.upper()} COMPLETE (+{gain}% Position Strength | Score: {prog}%)! ===\n"
        f"• Next Step: {hints.get(code, 'Speak to your leader for the next act!')}"
    )
    return player, log, "MAIN"


def draw_roguery_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Tracks 9 and 10."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    ROGUE_CRIMSON = (145, 40, 65)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    code = player.get("rg_code", "9a")
    scen = ROGUERY_SCENARIOS[code]

    title = font_bold.render(scen["header"], True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    prog = player.get("rg_progress", 40)
    lbl_str = "Outlaw Audacity & Plunder:" if scen["track"] == "outlaw" else "Audience Rapture & Intrigue:"
    screen.blit(font_bold.render(f"{lbl_str} {prog}% (Target: 75%+)", True, ROGUE_CRIMSON), (85, 80))

    p_bar = pygame.Rect(430, 80, 285, 18)
    pygame.draw.rect(screen, (40, 35, 35), p_bar, border_radius=4)
    if prog > 0:
        col = (45, 135, 65) if prog >= 75 else ROGUE_CRIMSON
        pygame.draw.rect(screen, col, (430, 80, int(285 * (prog / 100.0)), 18), border_radius=4)
    tx = 430 + int(285 * 0.75)
    pygame.draw.line(screen, (255, 255, 255), (tx, 78), (tx, 100), 2)
    pygame.draw.rect(screen, CLOCK_BLACK, p_bar, width=1, border_radius=4)

    st_idx = min(2, player.get("rg_stage", 0))
    st_data = scen["stages"][st_idx]

    s_box = pygame.Rect(85, 112, 630, 140)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 120))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 146, 600, 70), CLOCK_BLACK, max_lines=3)

    has_prep = player.get(scen["prep_flag"], False)
    prep_txt = (
        f"Preparation & Stagecraft: [{scen['prep_label']} READY!]"
        if has_prep else
        f"Preparation & Stagecraft: Unprepared (Explore to set up: {scen['prep_label']})"
    )
    screen.blit(font.render(prep_txt[:78], True, (45, 125, 60) if has_prep else TATE_RED), (100, 226))

    fb_box = pygame.Rect(85, 262, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("rg_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 5. UPGRADED DIALOGUE HANDLERS FOR BLACK DOG (9) & FAIRLIGHT (10)
# =========================================================================
def get_black_dog_roguery_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []

    if route == "Become a Highway Robber":
        if step == 1:
            opts.append("Mission: Briefing on the Bullion Coach Ambush" if not player.get("m9a_briefed") else "Mission: Spring the Muddy Hollow Bullion Heist (9A)!")
        elif step == 2:
            opts.append("Mission: Briefing on the Kokeshi Manhunt" if not player.get("m9b_briefed") else "Mission: Lure the Kokeshi Squad into the Briar-Maze (9B)!")
        elif step == 3:
            opts.append("Mission: Briefing on the Strike Pay-Wagon Raid" if not player.get("m9c_briefed") else "Mission: Hijack the Bailiff's Pay-Wagon in the Sunken Lane (9C)!")
        elif step == 4:
            opts.append("Mission: Briefing on the Mayor's Diplomatic Convoy" if not player.get("m9d_briefed") else "Mission: Ambush the Mayor's Convoy on the New Road (9D)!")
        elif step == 5:
            opts.append("Mission: Briefing on the Great War-Train Heist" if not player.get("m9e_briefed") else "Mission: Strike the Munitions War-Train at the Gorge (9E)!")

    opts.extend(["Ask about Outlaw Activity", "Leave"])
    return opts


def resolve_black_dog_roguery(choice, player):
    if choice == "Leave":
        return player, "Black Dog checks the flint on his horse-pistol and melts into the gorse.", "MAIN"
    if choice == "Ask about Outlaw Activity":
        return player, "\"The roads belong to whoever has the steel and the cunning to take them, friend.\"", "NPC_DIALOGUE"

    if choice == "Mission: Briefing on the Bullion Coach Ambush":
        player["m9a_briefed"] = True
        return player, (
            "=== MISSION: THE BULLION COACH HOLD-UP ===\n"
            "Black Dog grins wolfishly beneath his tricorn hat.\n"
            "\"A heavily guarded bullion coach is rolling north out of Murum today. Before we strike, speak with our inside man **Outrider Bran** outside **Murum Stables**, "
            "and **search** the **Muddy Hollow on the New Road** north of the Frontier Watchpost to rig a sawn pine-tree across the ruts!\""
        ), "MAIN"
    if choice.startswith("Mission: Spring the Muddy Hollow"):
        return init_roguery_minigame(player, "9a")

    if choice == "Mission: Briefing on the Kokeshi Manhunt":
        player["m9b_briefed"] = True
        return player, (
            "=== MISSION: THE BRIAR-MAZE COUNTER-AMBUSH ===\n"
            "Black Dog taps the black-iron seal on the stolen strongbox.\n"
            "\"Hell's bells—we just robbed the **Kokeshi Syndicate's** election payroll! The Diewell has sent a six-man hit-squad to skin us alive.\"\n"
            "\"**Search** around the standing stones here in **The Diluvium Glade** to rig blackthorn whip-snares across the bog-paths, then give the word to lure them in!\""
        ), "MAIN"
    if choice.startswith("Mission: Lure the Kokeshi"):
        return init_roguery_minigame(player, "9b")

    if choice == "Mission: Briefing on the Strike Pay-Wagon Raid":
        player["m9c_briefed"] = True
        return player, (
            "=== MISSION: THE CROSSROADS PAY-WAGON HEIST ===\n"
            "\"Down at the **Fluvius Farm Crossroads**, the Union strikers, the Kokeshi scabs, and the Town Watch are all nose-to-nose!\"\n"
            "\"Ride south and **search** the **Sunken Sluice-Gate Lane** just west of the crossroads to spot Bailiff Seekgrace's trailing pay-wagon before we snatch the chest!\""
        ), "MAIN"
    if choice.startswith("Mission: Hijack the Bailiff"):
        return init_roguery_minigame(player, "9c")

    if choice == "Mission: Briefing on the Mayor's Diplomatic Convoy":
        player["m9d_briefed"] = True
        return player, (
            "=== MISSION: THE MAYORAL CONVOY HIJACK ===\n"
            "\"Mayor Givethanks is hauling a chest of municipal tribute silver up **the New Road** to Castle Ragmore—but Lieutenant Beornraed has rigged a decoy chest!\"\n"
            "\"Question **Outrider Bran** outside **Murum Stables** to find out where the real tribute silver is hidden on the state coach before we ride out!\""
        ), "MAIN"
    if choice.startswith("Mission: Ambush the Mayor"):
        return init_roguery_minigame(player, "9d")

    if choice == "Mission: Briefing on the Great War-Train Heist":
        player["m9e_briefed"] = True
        return player, (
            "=== FINAL MISSION: THE GREAT WAR-TRAIN HEIST ===\n"
            "\"War has broken out between Ragmore and Laydere, and a massive military munitions and bullion train is marching toward the river-gorge!\"\n"
            "\"**Search** the **Washed-Out Gorge / Collapsed Span** (or bring the **Ancient Sapper's Blueprint** from the Old Path Catacombs) to rig the bridge trestles, then sound the horn for the greatest heist in history!\""
        ), "MAIN"
    if choice.startswith("Mission: Strike the Munitions"):
        return init_roguery_minigame(player, "9e")

    return player, "Error.", "MAIN"


def get_fairlight_roguery_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []

    if route == "Join Fairlight's Acting Troupe":
        if step == 1:
            opts.append("Mission: Briefing on the Backstage Patronage Envoys" if not player.get("m10a_briefed") else "Mission: Host the Backstage Patronage Auction (10A)!")
        elif step == 2:
            opts.append("Mission: Briefing on the Fluvius Masquerade Riot" if not player.get("m10b_briefed") else "Mission: Stage the Masquerade Riot in Fluvius Square (10B)!")
        elif step == 3:
            opts.append("Mission: Briefing on the Farm Barricade Satire" if not player.get("m10c_briefed") else "Mission: Perform the Barricade Satire at the Crossroads (10C)!")
        elif step == 4:
            opts.append("Mission: Briefing on the Castle Ragmore Command Performance" if not player.get("m10d_briefed") else "Mission: Perform the Masque & Rifle the Map-Room (10D)!")
        elif step == 5:
            opts.append("Mission: Briefing on the Election-Eve Grand Premiere" if not player.get("m10e_briefed") else "Mission: Raise the Curtain on the Grand Premiere (10E)!")

    opts.extend(["Buy Ticket (5s)", "Interact", "Leave"])
    return opts


def resolve_fairlight_roguery(choice, player):
    if choice == "Leave":
        return player, "\"A tragic exit! Until the next act, darling!\"", "MAIN"

    if choice == "Buy Ticket (5s)":
        if player["silver"] >= 5:
            player["silver"] -= 5
            player["inventory"].append("playhouse ticket")
            return player, "You hand over 5 silver. Fairlight bows deeply and produces a finely printed playhouse ticket.", "MAIN"
        return player, "Fairlight sighs tragically. \"Alas, art requires patronage. You lack the silver.\"", "MAIN"

    if choice == "Interact":
        return player, "Fairlight strikes a sweeping theatrical pose, adjusting their feathered mantle.", "NPC_DIALOGUE"

    if choice == "Mission: Briefing on the Backstage Patronage Envoys":
        player["m10a_briefed"] = True
        return player, (
            "=== MISSION: THE BACKSTAGE PATRONAGE AUCTION ===\n"
            "Fairlight leans on a gilded prop-sceptre, eyes twinkling.\n"
            "\"Darling, everyone wants to write our script! Envoys from the Castellan, the Union, and the Kokeshi Syndicate are waiting backstage right now.\"\n"
            "\"Speak with our costumer **Silktongue** here at the Playhouse first to learn how to keep all three envoys in separate dressing-rooms and pocket all three purses!\""
        ), "MAIN"
    if choice.startswith("Mission: Host the Backstage"):
        return init_roguery_minigame(player, "10a")

    if choice == "Mission: Briefing on the Fluvius Masquerade Riot":
        player["m10b_briefed"] = True
        return player, (
            "=== MISSION: THE MASQUERADE RIOT IN FLUVIUS ===\n"
            "\"To fulfill our Kokeshi patron's diversion—and expose the arrogance of the nobility—we shall dress as Castellan tax-bailiffs in **Fluvius Market Square**!\"\n"
            "\"Before we go on stage in the square, **search** the **Shadowed Cul-de-Sac behind the Fluvius Civic Clock-Tower** to stage our quick-change hampers so the Watch doesn't catch us in costume!\""
        ), "MAIN"
    if choice.startswith("Mission: Stage the Masquerade"):
        return init_roguery_minigame(player, "10b")

    if choice == "Mission: Briefing on the Farm Barricade Satire":
        player["m10c_briefed"] = True
        return player, (
            "=== MISSION: THE BARRICADE SATIRE ===\n"
            "\"Now for our Union patron's act! At the **Fluvius Farm Crossroads**, strikers and Kokeshi strikebreakers are about to crack skulls.\"\n"
            "\"Gather the local gossip in Fluvius (ask **Diarmuid** about Seekgrace's pipe or **Fearghal** at the Barge & Anchor about Corban's mules), then roll our stage-wagon up to the crossroads to shame the strikebreakers with biting comedy!\""
        ), "MAIN"
    if choice.startswith("Mission: Perform the Barricade"):
        return init_roguery_minigame(player, "10c")

    if choice == "Mission: Briefing on the Castle Ragmore Command Performance":
        player["m10d_briefed"] = True
        return player, (
            "=== MISSION: ESPIONAGE AT THE COMMAND PERFORMANCE ===\n"
            "\"Castellan Hrothgar has summoned us to perform at his diplomatic summit banquet at **Castle Ragmore**!\"\n"
            "\"Before the curtain rises, **search** the **Inner Bailey** at Castle Ragmore (or ask **Silktongue**) to grease the latch behind the Great Hall tapestries—so you can slip into Hrothgar's study during the second act!\""
        ), "MAIN"
    if choice.startswith("Mission: Perform the Masque"):
        return init_roguery_minigame(player, "10d")

    if choice == "Mission: Briefing on the Election-Eve Grand Premiere":
        player["m10e_briefed"] = True
        return player, (
            "=== FINAL MISSION: THE ELECTION-EVE GRAND PREMIERE ===\n"
            "\"Tonight we perform our masterwork—weaving every secret we stole from the lords, bailiffs, and syndicates into a three-act revelation for the people!\"\n"
            "\"**Search** the grand stage in **Fluvius Counting House Square** (or **Upper Parvus Promenade**) to rig oak drop-bars against the martial-law censors, then raise the curtain!\""
        ), "MAIN"
    if choice.startswith("Mission: Raise the Curtain"):
        return init_roguery_minigame(player, "10e")

    return player, "Error.", "MAIN"


# =========================================================================
# MODULE REGISTRATION (HANDLERS)
# =========================================================================
HANDLERS = {
    "black_dog":     (get_black_dog_roguery_options, resolve_black_dog_roguery),
    "fairlight":     (get_fairlight_roguery_options, resolve_fairlight_roguery),
    "bran_outrider": (get_bran_options, resolve_bran),
    "silktongue":    (get_silktongue_options, resolve_silktongue),
}
