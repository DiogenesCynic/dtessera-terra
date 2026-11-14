"""
ch2_union.py
------------
Chapter 2 Track 1 (Regional Union Official) mechanics, Fluvius Town NPCs,
environmental search investigations, Mission 1C No-Weapons Barricade Fisticuffs,
Mission 1D Fluvius Tribunal Cross-Examination, and Mission 1E Murum Union House
Traitor Indictment.
"""

import random
import pygame
import game_data as db
from mechanics import modify_faction, advance_time, execute_ch2_mission
from ui_components import draw_fitted_text

# =========================================================================
# 1. FLUVIUS POST OFFICE & PACKET-BOAT WHARF (LINKING MURUM & FLUVIUS)
# =========================================================================
def get_keepfaith_options(player):
    opts = [
        "Ask about dispatches & news from Murum Town",
        "Inquire about the Fluvius Regional Chart (15s)"
    ]
    if not player.get("m1c_murum_circular_taken"):
        opts.append("Ask if any post arrived from Union House in Murum")
    if player.get("chapter_2_route") == "Stand for Union Official" and player.get("ch2_mission_step") == 5:
        opts.append("Inspect the evening pigeon-post & money-order ledger")
    opts.append("Leave")
    return opts


def resolve_keepfaith(choice, player):
    if choice == "Leave":
        return player, "Postmistress Keepfaith returns to sorting wax-sealed packets into her pigeonholes.", "MAIN"

    if choice == "Ask about dispatches & news from Murum Town":
        job_note = (
            f"\"Why, Postmaster Safehaven mentioned your name in his last packet from Murum!\" she says warmly. "
            if player.get("market_sweeper_shifts", 0) > 0 or player.get("mayors_house_shifts", 0) > 0 else ""
        )
        return player, (
            "Postmistress Keepfaith adjusts her half-moon spectacles and gestures to the **Murum Dispatch Board** on the wall.\n"
            f"{job_note}\"Oisín brings the mail-skiff down the River Fluvius from Murum every morning. "
            "Between the Castellan's toll-collectors on the New Road and the rockslides on the Old Path, the river packet is the only reliable link left between our towns.\""
        ), "NPC_DIALOGUE"

    if choice == "Inquire about the Fluvius Regional Chart (15s)":
        if "fluvius town map" in player["inventory"]:
            return player, "\"You already have a copy of the Fluvius surveyor's chart in your satchel, friend.\"", "NPC_DIALOGUE"
        if player["silver"] < 15:
            return player, "\"The surveyor's chart of Fluvius Town and the delta costs 15 silver, traveller.\"", "NPC_DIALOGUE"
        player["silver"] -= 15
        player["inventory"].append("fluvius town map")
        return player, (
            "Postmistress Keepfaith unrolls a crisp linen-backed chart of Fluvius Town and its surrounding farmlands and hands it across the counter.\n"
            f"*** You purchased the Fluvius Town Map (-15 Silver | Remaining: {player['silver']}s)! ***"
        ), "MAIN"

    if choice == "Ask if any post arrived from Union House in Murum":
        player["m1c_murum_circular_taken"] = True
        return player, (
            "Keepfaith reaches into the 'Murum Guilds' cubby and pulls out a bundle of handbills stamped with the red seal of Union House.\n"
            "\"Truthtale sent these down on Oisín's morning skiff. Someone has been spreading forged notices in the Caligo hills claiming the Murum Union folded. "
            "Take a copy—the truth ought to be read aloud.\""
        ), "NPC_DIALOGUE"

    if choice == "Inspect the evening pigeon-post & money-order ledger":
        player["m1e_post_ledger_clue"] = True
        return player, (
            "Keepfaith lowers her voice and opens the night-dispatch register.\n"
            "\"Last evening, just before curfew, someone slipped a packet into the northern box addressed to a Kokeshi factor—written in violet ink with a split brass nib. "
            "Whoever posted it paid the express fee using newly minted silver coins still dusted with yellow fuller's earth from the granary."
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_oisin_options(player):
    return [
        "Ask about the river passage from Murum",
        "Ask what he saw along the riverbanks today",
        "Leave"
    ]


def resolve_oisin(choice, player):
    if choice == "Leave":
        return player, "Oisín coils a hemp mooring-line on the gunwale of his mail-skiff.", "MAIN"

    if choice == "Ask about the river passage from Murum":
        return player, (
            "Oisín spits into the current and grins.\n"
            "\"Born on this water, I was. The road-wardens can block the highways all they like, "
            "but as long as the Fluvius flows, my skiff carries Murum's letters from the northern sluice right down to the delta.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask what he saw along the riverbanks today":
        return player, (
            "Oisín leans on his boat-hook, glancing toward the western canal.\n"
            "\"When I poled past the western irrigation pond an hour ago, the water was brimming right up to the top of the old timber sluice-gate above the sunken lane. "
            "And down by the eastern mill-bend, I saw old Tadhg hiding in the willow reeds—looked like he'd seen a ghost by the broken waterwheel.\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 2. MISSION 1C EXPLORATION NPCS (FEARGHAL & CORBAN)
# =========================================================================
def get_fearghal_options(player):
    opts = [
        "Ask about his bandaged wrist & the wagon crews",
        "Buy Fearghal a bowl of mutton broth (1s)",
        "Leave"
    ]
    return opts


def resolve_fearghal(choice, player):
    if choice == "Leave":
        return player, "Fearghal stares into the peat fire, nursing his sprained wrist.", "MAIN"

    if choice == "Ask about his bandaged wrist & the wagon crews":
        return player, (
            "Fearghal winces, adjusting the rough linen sling around his arm.\n"
            "\"Sprained it loading grain-sacks at the eastern wharf. Look, friend—I'm a Caligo stone-hauler, not a strikebreaker by choice. "
            "A Kokeshi crimp named Corban came up to our quarry camp and swore on a bible that the Murum Union had already signed a separate peace and gone back to work.\""
        ), "NPC_DIALOGUE"

    if choice == "Buy Fearghal a bowl of mutton broth (1s)":
        if player["silver"] < 1:
            return player, "You don't have a silver coin to spare.", "NPC_DIALOGUE"
        player["silver"] -= 1
        player["m1c_learned_scab_motive"] = True
        return player, (
            "You set a steaming trencher of barley-and-mutton broth before the drover. Fearghal eats gratefully and leans in close.\n"
            "\"Bless you. Here's the ugly truth of it: when my mates reached the Granary Wharf this morning and saw your red picket banners, half of them wanted to turn back.\"\n"
            "\"But Corban locked our twelve hill-mules inside the eastern wharf corral! He told the boys that if they don't drive those three wains through the sunken lane at midday, "
            "the Syndicate will slaughter their mules for debt. Show the boys proof that the Union hasn't folded—or get that corral gate unbarred—and not a single quarryman will lift a whip against you.\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_corban_options(player):
    opts = ["Observe the wagon-teams in the yard"]
    if player.get("m1c_started") and not player.get("m1c_scabs_persuaded"):
        opts.append("Speak to the Caligo quarry drivers by the wagons")
    opts.append("Leave")
    return opts


def resolve_corban(choice, player):
    if choice == "Leave":
        return player, "Corban slaps a heavy leather riding-crop against his boot and glares after you.", "MAIN"

    if choice == "Observe the wagon-teams in the yard":
        return player, (
            "Three iron-rimmed grain wains stand hitched in the mud. Six thick-necked Kokeshi bruisers lounge against the tailboards—notably carrying no blades or clubs, "
            "only heavy leather gauntlets—while a dozen gaunt Caligo quarrymen glance nervously toward the padlocked mule corral."
        ), "NPC_DIALOGUE"

    if choice == "Speak to the Caligo quarry drivers by the wagons":
        # Check if the player has gathered the pieces to persuade the drivers!
        has_motive = player.get("m1c_learned_scab_motive", False)
        has_circular = player.get("m1c_murum_circular_taken", False)
        has_corral_freed = player.get("m1c_mules_freed", False)

        if has_motive and (has_circular or has_corral_freed or player.get("charisma", 0) >= 8):
            player["m1c_scabs_persuaded"] = True
            return player, (
                "Stepping past Corban's scowling bruisers, you hold up the stamped Murum Union Circular and speak directly to the Caligo quarrymen about the lie told at their camp.\n"
                + ("When the drivers see that you've already unbarred the corral so their hill-mules are safe on the towpath, " if has_corral_freed else "")
                + "the lead quarryman spits at Corban's feet, drops his reins into the mire, and walks out of the yard with six of his fellows!\n"
                "Corban snarls in fury—the convoy has lost half its drivers before a wheel has even turned!"
            ), "MAIN"
        else:
            return player, (
                "The quarry drivers keep their eyes fixed on the mud.\n"
                "\"Easy for you to talk, friend,\" one mutters under his breath. \"They told us Murum already settled, and Corban has our mules under lock and key in that corral.\""
            ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 3. ENVIRONMENTAL SEARCH ACTIONS IN FLUVIUS (SLUICE-GATE, CORRAL & 1E CLUES)
# =========================================================================
def handle_fluvius_search(player):
    """
    Called when the player uses 'Search' outdoors in the Fluvius region.
    Uses 1d6 + Stat/Skill rolls so players experience windfalls and friction!
    """
    pos = (player["x"], player["y"])

    # 1. The Sunken Sluice-Gate Lane (10, 5): Damage/Flood the road!
    if pos == (10, 5) and not player.get("current_building"):
        if player.get("m1c_road_sabotaged"):
            return True, "The irrigation sluice is already wide open; thick red clay mire churns ankle-deep across the sunken lane."

        die = random.randint(1, 6)
        has_tool = any(t in player.get("inventory", []) for t in ["crowbar", "iron sword", "masonry drill", "grappling hook"])
        bonus = (player.get("strength", 0) // 2) + (3 if has_tool else 0) + (2 if "master wallmaker" in player.get("skills", []) else 0)
        tot = die + bonus

        if tot >= 5:
            player["m1c_road_sabotaged"] = True
            player, _ = advance_time(30, player)
            if die == 6:
                player["silver"] += 6
                extra = "\n*** WINDFALL (Rolled a Natural 6!): Wedged behind the sluice-chock, you also uncover an old oilskin toll-pouch containing 6 silver! (+6s) ***"
            elif die == 1:
                player["health"] = max(1, player.get("health", 10) - 1)
                extra = "\n*** FRICTION (Rolled a 1!): The rusted iron pin snaps violently as it gives way, gashing your knuckles (-1 Health)! ***"
            else:
                extra = ""
            return True, (
                f"[Sluice Roll: 1d6({die}) + {bonus} = {tot}] You wrench the rusted iron lynch-pin free and heave two boundary boulders into the ruts!\n"
                "Pond-water roars down the chute, turning the sunken lane into an axle-deep quagmire of red clay!" + extra
            )
        else:
            player["hunger"] = max(0, player.get("hunger", 100) - 8)
            return True, (
                f"[Sluice Roll: 1d6({die}) + {bonus} = {tot} < 5] You strain against the rusted sluice-pin until your shoulders ache (-8 Hunger), "
                "but the iron chock refuses to budge! Try again or bring a prying tool / higher Strength."
            )

    # 2. The Granary Wharf & Teamsters' Yard (12, 4): Unbar the Mule Corral (Step 3) OR Search Behind Weigh-Beam (Step 5)
    if pos == (12, 4) and not player.get("current_building"):
        if player.get("ch2_mission_step") == 5:
            player["m1e_wharf_inspected"] = True
            die = random.randint(1, 6)
            windfall = ""
            if die == 6 and not player.get("m1e_wharf_windfall"):
                player["m1e_wharf_windfall"] = True
                player["silver"] += 5
                windfall = " (Windfall: You also spot 5 silver coins dropped beside the scales! +5s)"
            return True, (
                "Searching the mud behind the brick granary weigh-beam, where yellow fuller's earth is swept from the floor, "
                "you kick up a discarded tin of **beeswax key-impression putty** and a crumpled bar-chit from **The Barge & Anchor Taproom** "
                f"stamped 'PAID IN FULL — 40 SILVER', signed by **Delegate Faintnot**!{windfall}"
            )

        if player.get("m1c_mules_freed"):
            return True, "The timber corral gate hangs unbarred, and the quarrymen's hill-mules are safely out on the towpath."

        die = random.randint(1, 6)
        bonus = (player.get("stealth", 0) // 2) + (3 if "muddy master key" in player.get("inventory", []) else 0)
        tot = die + bonus
        if tot >= 5:
            player["m1c_mules_freed"] = True
            player, _ = advance_time(20, player)
            friction = ""
            if die == 1:
                player["reputation"] = player.get("reputation", 0) - 1
                friction = "\n(Friction: A mule brays loudly as you unbar the gate—a wharf-clerk spots your cloak in the gloom! -1 Reputation)"
            return True, (
                f"[Stealth Roll: 1d6({die}) + {bonus} = {tot}] Slipping behind the brick granary wall, "
                "you draw the iron drop-bolt on the timber corral and lead the quarrymen's hill-mules safely out to the canal towpath!" + friction
            )
        else:
            player["health"] = max(1, player.get("health", 10) - 1)
            return True, (
                f"[Stealth Roll: 1d6({die}) + {bonus} = {tot} < 5] You step on a dry shingle beside the corral! "
                "One of Corban's bruisers hurls a stone that clips your shoulder (-1 Health), forcing you to duck back into the alley!"
            )

    # 3. The East-Bank Watermill (13, 7): Subtle observation of the shattered wheel
    if pos == (13, 7) and not player.get("current_building"):
        player["flyfornication_chisel_clue"] = True
        return True, (
            "You kneel beside the shattered waterwheel and run your fingers along the broken oak axle.\n"
            "Instead of jagged axe-splinters, three smooth, cylindrical bore-holes have been drilled into the load-bearing mortise with a hollow-core masonry bit—and beside the sluice lies a heel-print of yellow fuller's clay from the town granary."
        )

    # 4. Mission 1E Investigation at the Crossroads Picket Brazier (11, 6): Inspect the Looted Strike Chest
    if pos == (11, 6) and not player.get("current_building") and player.get("ch2_mission_step") == 5:
        player["m1e_chest_inspected"] = True
        return True, (
            "You kneel beside the iron-bound Strike Chest near the brazier.\n"
            "The heavy padlock has not been forced or scratched—instead, a thin smear of soft **beeswax** clings to the keyhole ward, "
            "showing someone pressed a wax mould of the Treasurer's key to cast a duplicate.\n"
            "Wedged inside the spine of the stolen grain-cache register, you also find the snapped tip of a **split brass pen-nib** stained with violet ink."
        )

    return False, ""

# =========================================================================
# 4. MISSION 1C STEP 2: THE NO-WEAPONS BARRICADE FISTICUFFS (POP-OUT BRAWL)
# =========================================================================

BRAWL_OPPONENTS = [
    {
        "name": "Kokeshi Lead Knuckle-Duster",
        "max_hp": 18,
        "max_poise": 12,
        "intro": "A scar-faced Kokeshi vanguard spits into his leather-wrapped palms and steps up to the overturned hay-wain."
    },
    {
        "name": "Corban's Wharf-Enforcer",
        "max_hp": 22,
        "max_poise": 14,
        "intro": "A barrel-chested wharf bruiser vaults over the wagon tongue, rolling his shoulders as he eyes the chain."
    },
    {
        "name": "Corban (Kokeshi Wagon-Boss)",
        "max_hp": 26,
        "max_poise": 16,
        "intro": "Wagon-Boss Corban himself leaps down into the ruts, tossing aside his riding cloak and raising his scarred fists!"
    },
]

TELEGRAPH_PROSE = {
    "HAYMAKER": (
        "shifts his back boot into the ruts and cocks his right fist far behind his ear for a skull-rattling haymaker!"
    ),
    "BULL_RUSH": (
        "lowers his head between his shoulders and lunges forward at your waist to bull-rush the hay-wain off the road!"
    ),
    "IRON_GUARD": (
        "plants his heels wide and crosses both thick, leather-gauntleted forearms tightly across his jaw and ribs!"
    ),
}


def _spawn_brawl_opponent(player, index):
    wave = player.get("brawl_wave_list", BRAWL_OPPONENTS)
    spec = wave[index]
    sab_penalty = 4 if player.get("m1c_road_sabotaged") else 0
    player["brawl_opp_idx"] = index
    player["brawl_opp_name"] = spec["name"]
    player["brawl_opp_hp"] = spec["max_hp"]
    player["brawl_opp_max_hp"] = spec["max_hp"]
    player["brawl_opp_poise"] = max(6, spec["max_poise"] - sab_penalty)
    player["brawl_opp_max_poise"] = spec["max_poise"]
    player["brawl_opp_staggered"] = False
    player["brawl_telegraph"] = random.choice(["HAYMAKER", "BULL_RUSH", "IRON_GUARD"])
    return spec["intro"]


def init_barricade_brawl(player):
    """Initializes the Mission 1C Standoff & No-Weapons Fisticuffs Pop-Out."""
    # 1. Immediate check: Did the player walk up to the barricade carrying a drawn weapon?
    weapon = player.get("equipped_weapon", "fists")
    if weapon != "fists":
        return trigger_watch_martial_law(player, weapon)

    crews = len(player.get("m1c_mustered_crews", []))
    sab = player.get("m1c_road_sabotaged", False)
    persuaded = player.get("m1c_scabs_persuaded", False)

    # If scabs were persuaded at the wharf, the middle bruiser is already gone (2 foes instead of 3)
    if persuaded:
        player["brawl_wave_list"] = [BRAWL_OPPONENTS[0], BRAWL_OPPONENTS[2]]
    else:
        player["brawl_wave_list"] = list(BRAWL_OPPONENTS)

    player["brawl_phase"] = "STANDOFF"  # "STANDOFF", "FIGHT", "VICTORY", "DEFEAT"
    player["brawl_momentum"] = 1 + (1 if "red-and-gold strike banner" in player.get("inventory", []) else 0)
    player["brawl_line_hold"] = min(100, 55 + (crews * 12) + (10 if sab else 0))

    road_desc = (
        "The lead grain-wain lurches out of the flooded sunken lane, its wheels clogged axle-deep in thick red clay mire!"
        if sab else
        "Three heavy grain-wains rattle briskly up the dry ruts toward the overturned hay-wains!"
    )
    crew_desc = (
        f"Behind you, {crews} mustered Union farm delegation(s) lock arms across the crossroads."
        if crews > 0 else
        "Your picket line is thin—only Joyinsorrow and a handful of strikers stand beside the brazier."
    )

    player["brawl_banner"] = (
        f"{road_desc} {crew_desc} "
        "On the ridge above, Watch Sergeant Beornraed's lancers sit in their saddles, watching for any flash of steel."
    )
    return player, player["brawl_banner"], "MINIGAME_BRAWL"


def trigger_watch_martial_law(player, weapon_name):
    """Triggered if the player enters the picket brawl with a weapon or draws steel mid-fight."""
    player["ch2_mission_step"] = 4
    player["active_ch2_mission"] = None
    player["court_claim"] = 1

    if weapon_name in player.get("inventory", []):
        player["inventory"].remove(weapon_name)
    player["equipped_weapon"] = "fists"

    player["health"] = max(1, player.get("health", 10) - 3)
    player["reputation"] = player.get("reputation", 0) - 4
    player["position_strength"] = max(0, player.get("position_strength", 0) - 25)
    player["exposure_tells"] = player.get("exposure_tells", 0) + 2
    modify_faction(player, "faction_union", -2)
    modify_faction(player, "faction_guard", -3)

    log = (
        "=== MARTIAL LAW INTERVENTION: COLD STEEL AT THE BARRICADE! ===\n"
        f"The moment {weapon_name.upper()} flashes in the daylight, shrill brass whistles echo from the ridge!\n"
        "\"WEAPONS ON THE HIGHWAY! CHARGE!\" Watch Sergeant Beornraed's mounted lancers thunder down the slope, "
        "clubbing strikers and teamsters alike with the butts of their halberds while the Kokeshi wagons roll straight through the shattered barricade!\n\n"
        f"Your {weapon_name} is confiscated by the Watch, you take a heavy blow across the shoulders (-3 Health), "
        "and the Union is branded an armed insurrection (-25% Position Strength, -4 Reputation, -2 Union Faction, +2 Exposure Tells)!\n\n"
        "*** In the aftermath of the rout, word arrives that Farmer Flyfornication has been arrested at the East-Bank Watermill and dragged before the Fluvius Tribunal. ***"
    )
    return player, log, "MAIN"


def brawl_action(action, player):
    """Handles all tactical choices in the MINIGAME_BRAWL pop-out window."""
    phase = player.get("brawl_phase", "STANDOFF")

    # ------------------------------------------------------------------
    # PHASE 1: PRE-CLASH STANDOFF (FINAL CHANCE TO TURN DRIVERS)
    # ------------------------------------------------------------------
    if phase == "STANDOFF":
        if action == "shout_truth":
            if player.get("m1c_scabs_persuaded"):
                player["brawl_banner"] = "The honest Caligo quarrymen have already walked off—only Corban's hardline bruisers remain!"
                return player, None, "MINIGAME_BRAWL"

            has_intel = player.get("m1c_learned_scab_motive") or player.get("m1c_murum_circular_taken")
            if has_intel or player.get("charisma", 0) >= 7:
                player["m1c_scabs_persuaded"] = True
                player["brawl_wave_list"] = [BRAWL_OPPONENTS[0], BRAWL_OPPONENTS[2]]
                player["brawl_line_hold"] = min(100, player.get("brawl_line_hold", 60) + 12)
                intro = _spawn_brawl_opponent(player, 0)
                player["brawl_phase"] = "FIGHT"
                player["brawl_banner"] = (
                    "Your voice rings across the ruts, exposing Corban's lie about the Murum strike! "
                    "Two Caligo drivers curse the Kokeshi crimp, drop their reins, and walk away! " + intro
                )
                return player, player["brawl_banner"], "MINIGAME_BRAWL"
            else:
                intro = _spawn_brawl_opponent(player, 0)
                player["brawl_phase"] = "FIGHT"
                player["brawl_banner"] = (
                    "You shout for the drivers to halt, but without proof of why they're being coerced, Corban's whip cracks and the bruisers charge! " + intro
                )
                return player, player["brawl_banner"], "MINIGAME_BRAWL"

        elif action == "lock_arms":
            intro = _spawn_brawl_opponent(player, 0)
            player["brawl_phase"] = "FIGHT"
            player["brawl_banner"] = f"You spit on your hands, step in front of the overturned hay-wain, and square your fists! {intro}"
            return player, player["brawl_banner"], "MINIGAME_BRAWL"

        elif action == "draw_weapon":
            w = next((i for i in player.get("inventory", []) if i in db.weapon_max_hit and i != "fists"), "iron blade")
            return trigger_watch_martial_law(player, w)

    # ------------------------------------------------------------------
    # PHASE 2: TACTICAL FISTICUFFS (JAB / BARGE / BRACE / DITCH-TOSS)
    # ------------------------------------------------------------------
    elif phase == "FIGHT":
        if action == "draw_weapon":
            w = next((i for i in player.get("inventory", []) if i in db.weapon_max_hit and i != "fists"), "iron blade")
            return trigger_watch_martial_law(player, w)

        tele = player.get("brawl_telegraph", "HAYMAKER")
        staggered = player.get("brawl_opp_staggered", False)
        str_bonus = max(0, player.get("strength", 0) // 3)
        crews = len(player.get("m1c_mustered_crews", []))
        mom = player.get("brawl_momentum", 0)
        opp_name = player.get("brawl_opp_name", "Bruiser")

        # Roll 2d6 for combat variance!
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        roll_sum = d1 + d2
        luck_mod = 2 if roll_sum >= 10 else (-1 if roll_sum <= 4 else 0)

        dmg_to_opp = 0
        poise_dmg = 0
        hp_loss = 0
        line_delta = 0
        notes = [f"[Roll {d1}+{d2}={roll_sum}]"]

        # 1. QUICK JAB COMBINATION
        if action == "jab":
            if tele == "BULL_RUSH" or staggered:
                dmg_to_opp = max(2, 5 + str_bonus + luck_mod)
                poise_dmg = max(2, 5 + luck_mod)
                player["brawl_momentum"] = min(5, mom + 1)
                player["brawl_opp_staggered"] = False
                notes.append(f"CRACK! Your one-two jab catches {opp_name} flush on the nose mid-rush (-{dmg_to_opp} HP, -{poise_dmg} Footing)!")
            elif tele == "IRON_GUARD":
                dmg_to_opp = max(1, 2 + luck_mod)
                poise_dmg = 1
                hp_loss = 1 if roll_sum < 9 else 0
                notes.append(f"Your jabs thud against {opp_name}'s crossed forearms" + (" and he clips your ear (-1 HP)!" if hp_loss else ", barely grazing him!"))
            else:
                dmg_to_opp = max(2, 4 + (str_bonus // 2) + luck_mod)
                poise_dmg = 2
                hp_loss = 1 if roll_sum >= 8 else 2
                line_delta = -6
                notes.append(f"You land a fast jab, but {opp_name} swings through with his haymaker (-{hp_loss} HP)!")

        # 2. HEAVY SHOULDER-BARGE & HOOK
        elif action == "barge":
            player["brawl_momentum"] = max(0, mom - 1)
            if tele == "IRON_GUARD" or staggered:
                dmg_to_opp = max(4, 8 + str_bonus + crews + luck_mod)
                poise_dmg = max(4, 6 + luck_mod)
                line_delta = 6
                player["brawl_opp_staggered"] = True
                notes.append(f"BOOM! You drive your shoulder through {opp_name}'s guard, rocking him backward (-{dmg_to_opp} HP, STAGGERED)!")
            elif tele == "BULL_RUSH":
                dmg_to_opp = max(3, 5 + str_bonus + luck_mod)
                poise_dmg = 4
                hp_loss = 0 if roll_sum >= 9 else 1
                notes.append(f"You collide head-on with {opp_name} in a bone-jarring clash of shoulders!")
            else:
                dmg_to_opp = max(2, 4 + luck_mod)
                poise_dmg = 2
                hp_loss = 2
                line_delta = -10
                notes.append(f"You lunge in heavy just as {opp_name} uncorks his haymaker—both of you trade brutal hooks (-2 HP)!")

        # 3. BRACE & COUNTER-PARRY
        elif action == "brace":
            if tele == "HAYMAKER":
                dmg_to_opp = max(3, 4 + str_bonus + luck_mod)
                poise_dmg = max(4, 7 + luck_mod)
                player["brawl_momentum"] = min(5, mom + 2)
                player["brawl_opp_staggered"] = True
                line_delta = 6
                notes.append(f"COUNTER! You duck inside {opp_name}'s wild haymaker and crack a hook into his ribs (+2 Momentum, STAGGERED)!")
            elif tele == "BULL_RUSH":
                dmg_to_opp = 1
                poise_dmg = 1
                hp_loss = 1
                line_delta = -10
                notes.append(f"You brace high and {opp_name} tackles low into your knees (-1 HP, -10% Line Hold)!")
            else:
                player["brawl_momentum"] = min(5, mom + 1)
                notes.append(f"Both you and {opp_name} circle each other with fists raised (+1 Momentum).")

        # 4. CONTESTED GRAPPLE & DITCH-TOSS ROLL!
        elif action == "ditch_toss":
            cur_poise = player.get("brawl_opp_poise", 10)
            player_grapple = roll_sum + (player.get("strength", 0) // 2) + (crews * 2) + (3 if staggered else 0) + (2 if player.get("m1c_road_sabotaged") else 0)
            enemy_resist = random.randint(1, 6) + cur_poise

            if player_grapple >= enemy_resist:
                dmg_to_opp = 999
                poise_dmg = 999
                line_delta = 8
                notes.append(
                    f"[Grapple {player_grapple} vs {enemy_resist}: SUCCESS!] With a mighty heave, you hurl {opp_name} headfirst into the flooded clay ditch!"
                )
            else:
                dmg_to_opp = 2
                poise_dmg = 3
                hp_loss = 1 if roll_sum >= 7 else 2
                line_delta = -6
                notes.append(
                    f"[Grapple {player_grapple} vs {enemy_resist}: SLIPPED!] {opp_name} braces his boot in the mud, wrenches free, and clubs your collarbone (-{hp_loss} HP, -3 Enemy Footing)!"
                )

        # --- 30% CHANCE OF UNPREDICTABLE CROSSROADS TWIST (WINDFALL OR FRICTION) ---
        if dmg_to_opp < 900 and random.random() < 0.30:
            twists = [
                ("WINDFALL: A runaway cider-cask rolls down the ruts and clips the bruiser's shins! (-3 Enemy Footing)", 0, 3, 0, 0),
                ("WINDFALL: Orchardist Goodseed's press-hands pelt the bruisers with rotten apples! (+8% Barricade Hold)", 0, 1, 0, 8),
                ("WINDFALL: As the bruiser stumbles, a 5-silver Kokeshi wage-pouch spills from his waistcoat into your hand! (+5s)", 0, 0, 0, 0),
                ("FRICTION: A sudden squall of cold rain turns the crossroads ruts slick as grease! (-6% Barricade Hold)", 0, 2, 0, -6),
                ("FRICTION: A frightened draught-mule kicks the overturned hay-wain, jarring your shoulder! (-1 HP)", 0, 0, 1, -4),
            ]
            t_txt, ex_dmg, ex_poise, ex_hp, ex_line = random.choice(twists)
            dmg_to_opp += ex_dmg
            poise_dmg += ex_poise
            hp_loss += ex_hp
            line_delta += ex_line
            if "+5s" in t_txt:
                player["silver"] += 5
            notes.append(f"[{t_txt}]")

        # Apply results
        player["brawl_opp_hp"] = max(0, player.get("brawl_opp_hp", 10) - dmg_to_opp)
        player["brawl_opp_poise"] = max(0, player.get("brawl_opp_poise", 10) - poise_dmg)
        if player["brawl_opp_poise"] == 0 and player["brawl_opp_hp"] > 0:
            player["brawl_opp_staggered"] = True

        if hp_loss > 0:
            player["health"] = max(0, player.get("health", 10) - hp_loss)
            if player["health"] <= 0:
                return player, "You collapse into the churned mud of the crossroads as darkness closes in...", "DEAD"

        player["brawl_line_hold"] = max(0, min(100, player.get("brawl_line_hold", 60) + line_delta))
        if player["brawl_line_hold"] <= 0:
            player["brawl_phase"] = "DEFEAT"
            player["brawl_banner"] = (
                "The Kokeshi bruisers heave the overturned hay-wain out of the ruts! The picket line buckles as the wagons force their way through!"
            )
            return player, player["brawl_banner"], "MINIGAME_BRAWL"

        if player["brawl_opp_hp"] <= 0:
            next_idx = player.get("brawl_opp_idx", 0) + 1
            wave = player.get("brawl_wave_list", BRAWL_OPPONENTS)
            if next_idx >= len(wave):
                player["brawl_phase"] = "VICTORY"
                player["brawl_banner"] = (
                    " ".join(notes) + " Bruised and mud-caked, Wagon-Boss Corban crawls out of the ditch and signals a retreat!"
                )
                return player, player["brawl_banner"], "MINIGAME_BRAWL"
            else:
                intro = _spawn_brawl_opponent(player, next_idx)
                player["brawl_banner"] = " ".join(notes) + f" Next up: {intro}"
                return player, player["brawl_banner"], "MINIGAME_BRAWL"

        choices = ["HAYMAKER", "BULL_RUSH", "IRON_GUARD"]
        if tele in choices and len(choices) > 1:
            choices.remove(tele)
        player["brawl_telegraph"] = random.choice(choices)
        player["brawl_banner"] = " ".join(notes)
        return player, None, "MINIGAME_BRAWL"

    # ------------------------------------------------------------------
    # PHASE 3: CONCLUDE BRAWL (VICTORY OR DEFEAT)
    # ------------------------------------------------------------------
    elif phase in ("VICTORY", "DEFEAT"):
        player["ch2_mission_step"] = 4
        player["active_ch2_mission"] = None
        player["court_claim"] = 1

        # Clear temporary muster locations
        db.npc_database["steadfast_ploughman"]["location"] = None
        db.npc_database["goodseed_orchardist"]["location"] = None

        if phase == "VICTORY":
            bonus = (
                20
                + (5 if player.get("m1c_road_sabotaged") else 0)
                + (5 if player.get("m1c_scabs_persuaded") else 0)
            )
            player["position_strength"] = player.get("position_strength", 0) + bonus
            player["reputation"] = player.get("reputation", 0) + 2
            player["strength"] = player.get("strength", 0) + 1
            modify_faction(player, "faction_union", 3)
            log = (
                f"=== BARRICADE HELD UNBROKEN (+{bonus}% Position Strength, +1 Strength, +2 Reputation, +3 Union Faction)! ===\n"
                "Without a single blade drawn, your fists and the locked arms of the Fluvius strikers send Corban's bruisers limping back to the wharves!\n"
                "Up on the ridge, Watch Sergeant Beornraed lowers his spyglass—denied any excuse to declare martial law—and wheels his lancers away.\n\n"
                "As the strikers cheer around the brazier, a breathless mill-boy splashes across the ford with urgent news:\n"
                "\"Organiser! Bailiff Seekgrace's men have clapped **Farmer Flyfornication** in irons for allegedly smashing the East-Bank waterwheel! "
                "Magistrate Fleepride has convened a tribunal at the Counting House in Fluvius Town—if no one uncovers the truth and defends him, he'll be transported in chains!\""
            )
            return player, log, "MAIN"
        else:
            player["position_strength"] = max(0, player.get("position_strength", 0) - 15)
            player["exposure_tells"] = player.get("exposure_tells", 0) + 1
            log = (
                "=== THE CONVOY BREAKS THROUGH (-15% Position Strength, +1 Exposure Tell) ===\n"
                "Battered and outnumbered, your picket line is shoved aside as the Kokeshi wagons churn through the crossroads toward the river barges.\n\n"
                "Worse still, word arrives that **Farmer Flyfornication** has been arrested for the sabotage of the East-Bank waterwheel and faces Magistrate Fleepride's Tribunal in Fluvius Town!"
            )
            return player, log, "MAIN"

    return player, None, "MINIGAME_BRAWL"


def draw_brawl_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for the Mission 1C Barricade Brawl."""
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

    title = font_bold.render("FLUVIUS CROSSROADS — THE BARRICADE STANDOFF", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    # Top Status Strip: Player HP | Momentum | Barricade Line Hold
    status_box = pygame.Rect(85, 80, 630, 34)
    pygame.draw.rect(screen, (232, 224, 206), status_box, border_radius=6)
    pygame.draw.rect(screen, CLOCK_BLACK, status_box, width=1, border_radius=6)

    hp_str = f"Your Stamina: {player.get('health', 10)}/{player.get('max_health', 10)} HP"
    mom_val = player.get("brawl_momentum", 0)
    mom_dots = "★" * mom_val + "☆" * (5 - mom_val)
    hold_val = player.get("brawl_line_hold", 60)

    screen.blit(font_bold.render(hp_str, True, CLOCK_BLACK), (98, 89))
    screen.blit(font_bold.render(f"Momentum: {mom_dots}", True, TATE_RED), (305, 89))
    screen.blit(font_bold.render(f"Barricade Hold: {hold_val}%", True, (40, 110, 55) if hold_val >= 50 else TATE_RED), (535, 89))

    phase = player.get("brawl_phase", "STANDOFF")

    if phase == "STANDOFF":
        scene_box = pygame.Rect(85, 126, 630, 185)
        pygame.draw.rect(screen, (250, 246, 236), scene_box, border_radius=8)
        pygame.draw.rect(screen, TATE_RED, scene_box, width=2, border_radius=8)

        crews = player.get("m1c_mustered_crews", [])
        crew_names = ", ".join(c.title() for c in crews) if crews else "None mustered"
        prep_lines = [
            "THE CONVOY RUMBLES UP TO THE OVERTURNED HAY-WAINS!",
            f"• Sunken Sluice-Gate Road: {'Flooded axle-deep in red clay mire (Bruisers Off-Balance!)' if player.get('m1c_road_sabotaged') else 'Dry and intact'}",
            f"• Caligo Quarry Drivers: {'Persuaded at the Wharf (Convoy reduced to 2 Bruisers!)' if player.get('m1c_scabs_persuaded') else 'Still driving the wains'}",
            f"• Allied Union Crews on the Line: {crew_names}",
            "• Watch Lancers on the Ridge: Watching closely — DRAWING WEAPONS WILL TRIGGER MARTIAL LAW!"
        ]
        y_c = 138
        for idx, line in enumerate(prep_lines):
            col = TATE_RED if idx in (0, 4) else CLOCK_BLACK
            f_use = font_bold if idx in (0, 4) else font
            screen.blit(f_use.render(line, True, col), (100, y_c))
            y_c += 32

    elif phase == "FIGHT":
        wave = player.get("brawl_wave_list", BRAWL_OPPONENTS)
        idx = player.get("brawl_opp_idx", 0)
        opp_name = player.get("brawl_opp_name", "Kokeshi Bruiser")
        opp_hp = player.get("brawl_opp_hp", 18)
        opp_max_hp = max(1, player.get("brawl_opp_max_hp", 18))
        opp_poise = player.get("brawl_opp_poise", 10)
        opp_max_poise = max(1, player.get("brawl_opp_max_poise", 12))
        staggered = player.get("brawl_opp_staggered", False)

        opp_box = pygame.Rect(85, 124, 630, 112)
        pygame.draw.rect(screen, (250, 246, 236), opp_box, border_radius=8)
        pygame.draw.rect(screen, TATE_RED, opp_box, width=2, border_radius=8)

        hdr = f"OPPONENT ({idx + 1}/{len(wave)}): {opp_name.upper()}"
        screen.blit(font_bold.render(hdr, True, TATE_RED), (100, 132))
        if staggered:
            screen.blit(font_bold.render("[OFF-BALANCE / STAGGERED — TOSS HIM IN THE DITCH!]", True, (40, 125, 55)), (390, 132))

        # Opponent Resolve (HP) Bar
        screen.blit(font.render(f"Bruiser Resolve: {opp_hp}/{opp_max_hp}", True, CLOCK_BLACK), (100, 160))
        hp_bar = pygame.Rect(275, 160, 415, 18)
        pygame.draw.rect(screen, (40, 35, 35), hp_bar, border_radius=5)
        hp_w = int(415 * (opp_hp / float(opp_max_hp)))
        if hp_w > 0:
            pygame.draw.rect(screen, (185, 45, 40), (275, 160, hp_w, 18), border_radius=5)
        pygame.draw.rect(screen, CLOCK_BLACK, hp_bar, width=1, border_radius=5)

        # Opponent Footing / Balance (Poise) Bar
        screen.blit(font.render(f"Footing in Mud: {opp_poise}/{opp_max_poise}", True, CLOCK_BLACK), (100, 192))
        p_bar = pygame.Rect(275, 192, 415, 18)
        pygame.draw.rect(screen, (40, 35, 35), p_bar, border_radius=5)
        p_w = int(415 * (opp_poise / float(opp_max_poise)))
        if p_w > 0:
            pygame.draw.rect(screen, (205, 155, 55), (275, 192, p_w, 18), border_radius=5)
        pygame.draw.rect(screen, CLOCK_BLACK, p_bar, width=1, border_radius=5)

        # Opponent Telegraph Box (Pure Prose — Player reads the move!)
        tele_box = pygame.Rect(85, 244, 630, 62)
        pygame.draw.rect(screen, (236, 226, 208), tele_box, border_radius=8)
        pygame.draw.rect(screen, CLOCK_BLACK, tele_box, width=2, border_radius=8)
        tele_key = player.get("brawl_telegraph", "HAYMAKER")
        tele_sentence = f"WATCH HIS MOVE: {opp_name} {TELEGRAPH_PROSE.get(tele_key, '')}"
        draw_fitted_text(screen, tele_sentence, tele_box.inflate(-16, -8), CLOCK_BLACK, bold=True, max_lines=2)

    else:
        # VICTORY or DEFEAT Banner Box
        out_box = pygame.Rect(85, 140, 630, 150)
        pygame.draw.rect(screen, (250, 246, 236), out_box, border_radius=8)
        pygame.draw.rect(screen, TATE_RED, out_box, width=2, border_radius=8)
        draw_fitted_text(screen, player.get("brawl_banner", ""), out_box.inflate(-20, -20), CLOCK_BLACK, bold=True, max_lines=3)

    # Bottom Narrative Exchange Box
    fb_box = pygame.Rect(85, 314, 630, 56)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("brawl_banner", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)

# =========================================================================
# 5. MISSION 1D: THE FLUVIUS TRIBUNAL CROSS-EXAMINATION (POP-OUT COURTROOM)
# =========================================================================
TRIBUNAL_WITNESSES = [
    {
        "name": "Witness 1: Mill-Warden Gavel",
        "initial_claim": (
            "\"Your Honour, at dawn I found the East-Bank waterwheel smashed to splinters! "
            "It is plain as day: Farmer Flyfornication wrecked his own wheel in a drunken rage to spite the Bailiff's mill-tariff!\""
        ),
        "pressed_claim": (
            "Under your questioning, Warden Gavel puffs out his chest: \"I didn't need to look twice at the timber! "
            "The oak axle was hacked apart with a heavy woodsman's felling-axe—the very sort Flyfornication keeps in his woodshed!\""
        ),
        "best_actions": ["forensics", "trade_demo"],
    },
    {
        "name": "Witness 2: Squint-Eyed Ned (Quayside Informant)",
        "initial_claim": (
            "\"I was walking the canal towpath at midnight, Your Honour, when I heard a crash by the mill-race! "
            "A lantern flashed on the sluice, and I saw the miller himself standing over the broken paddles!\""
        ),
        "pressed_claim": (
            "When pressed on what he saw across the dark water, Ned blurts out: \"The lantern light hit his face square on! "
            "I saw his smooth, clean-shaven jaw and chin as clear as I see you now, Magistrate!\""
        ),
        "best_actions": ["testimony"],
    },
    {
        "name": "Witness 3: Chief Clerk Pinchpenny",
        "initial_claim": (
            "\"The defence peddles fantasies, Your Honour! No outside party had the slightest reason to harm that grist-mill. "
            "Only a rebellious Union striker would sabotage an estate waterwheel!\""
        ),
        "pressed_claim": (
            "Pinchpenny adjusts his cuffs nervously: \"The Counting House has no private buyers for the East-Bank lease, "
            "and none of our staff were anywhere near the eastern mill-race last night!\""
        ),
        "best_actions": ["motive", "forensics"],
    },
]


def get_fleepride_union_options(player):
    opts = []
    if player.get("chapter_2_route") == "Stand for Union Official" and player.get("ch2_mission_step") == 4:
        if not player.get("m1d_intro_seen"):
            opts.append("Mission: Inquire about the Tribunal of Farmer Flyfornication")
        else:
            opts.append("Mission: Step to the Defence Lectern (Begin Tribunal Cross-Examination)")
    opts.extend(["Observe the Fluvius Tribunal", "Leave"])
    return opts


def resolve_fleepride_union(choice, player):
    if choice == "Leave":
        return player, "You step quietly out of the Fluvius Tribunal gallery.", "MAIN"

    if choice == "Observe the Fluvius Tribunal":
        return player, (
            "Magistrate Fleepride sits high upon the carved oak bench, her iron-grey hair pinned beneath a judicial cap as clerks stacks docket scrolls below."
        ), "NPC_DIALOGUE"

    if choice == "Mission: Inquire about the Tribunal of Farmer Flyfornication":
        player["m1d_intro_seen"] = True
        log = (
            "=== MISSION: THE FLUVIUS TRIBUNAL ===\n"
            "Inside the high-ceilinged courtroom above the Counting House, Farmer Flyfornication sits in the iron dock, his long red beard tangled and his wrists chained.\n"
            "Magistrate Fleepride peers down over her half-moon spectacles at you.\n"
            "\"So the Murum Union sends an advocate. Hear me well: Bailiff Seekgrace's prosecutor has called three witnesses to swear that this farmer took an axe to his own mill-wheel to obstruct the harvest.\"\n\n"
            "\"Once you step to the defence lectern and I strike my gavel, there will be no recess. "
            "Do not begin until you have personally examined the scene of the sabotage, sought out anyone who was along the riverbanks that night, and uncovered who truly stands to profit from this mill's forfeiture.\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Step to the Defence Lectern (Begin Tribunal Cross-Examination)":
        player, t_msg = execute_ch2_mission(player, "1d_court", time_cost=120, stamina_drain=10)
        player, log, next_state = init_tribunal_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    return player, "Magistrate Fleepride raps her gavel for silence.", "MAIN"


def init_tribunal_minigame(player):
    """Initializes the 3-Witness Courtroom Cross-Examination Pop-Out."""
    player["tribunal_phase"] = "ACTIVE"  # "ACTIVE" or "VERDICT"
    player["tribunal_witness_idx"] = 0
    player["tribunal_pressed"] = False
    player["tribunal_doubt"] = 30 + min(10, player.get("charisma", 0) + player.get("influence", 0))
    player["tribunal_feedback"] = (
        "Magistrate Fleepride strikes her gavel: \"The prosecution calls its first witness. "
        "Advocate, you may press the witness for specifics first, or present your rebuttal from the lectern!\""
    )
    return player, player["tribunal_feedback"], "MINIGAME_TRIBUNAL"


def tribunal_action(action, player):
    """Processes cross-examination actions in the MINIGAME_TRIBUNAL pop-out."""
    phase = player.get("tribunal_phase", "ACTIVE")
    if phase == "VERDICT":
        return conclude_tribunal_minigame(player)

    w_idx = player.get("tribunal_witness_idx", 0)
    w_data = TRIBUNAL_WITNESSES[w_idx]
    pressed = player.get("tribunal_pressed", False)

    # 1. PRESS WITNESS FOR SPECIFICS (Draws out their specific contradiction!)
    if action == "press":
        if pressed:
            player["tribunal_feedback"] = "You have already pinned the witness down on the details of their claim—now present your counter-evidence!"
            return player, None, "MINIGAME_TRIBUNAL"
        player["tribunal_pressed"] = True
        player["tribunal_doubt"] = min(100, player.get("tribunal_doubt", 30) + 5)
        player["tribunal_feedback"] = (
            "You lean across the oak rail and demand the witness swear to the exact particulars of their story! (+5% Judicial Doubt)"
        )
        return player, None, "MINIGAME_TRIBUNAL"

    # 2. EVALUATE REBUTTAL CHOICE AGAINST CURRENT WITNESS
    press_bonus = 8 if pressed else 0
    gain = 0
    msg = ""

    # --- WITNESS 1: MILL-WARDEN GAVEL (THE TOOL) ---
    if w_idx == 0:
        has_chisel = player.get("flyfornication_chisel_clue", False)
        has_trade = any(s in player.get("skills", []) for s in ["forge", "master blacksmith", "master wallmaker"]) or "masonry drill" in player.get("inventory", [])

        if action == "forensics" and has_chisel:
            gain = 22 + press_bonus
            msg = (
                "You lay a splintered section of the mill-axle on the Magistrate's bench, pointing out the three smooth, cylindrical bore-holes drilled through the mortise—and the smear of yellow granary clay on the sluice!"
            )
        elif action == "trade_demo" and has_trade:
            gain = 24 + press_bonus
            msg = (
                "Drawing on your own craft training, you demonstrate to Magistrate Fleepride how a hollow-core masonry bit bores clean cylinders through oak heartwood—proving no woodsman's axe ever touched that wheel!"
            )
        elif action in ("forensics", "trade_demo"):
            gain = -12
            msg = (
                "You try to argue about the broken timber, but because you never inspected the shattered waterwheel yourself (and lack masonry tools), Warden Gavel scoffs at your guesswork! (-12% Doubt)"
            )
        else:
            gain = -10
            msg = "Magistrate Fleepride frowns: \"That does not address the Warden's testimony regarding how the oak axle was severed, Advocate.\" (-10% Doubt)"

    # --- WITNESS 2: SQUINT-EYED NED (THE MIDNIGHT IDENTIFICATION) ---
    elif w_idx == 1:
        has_tadhg = "tadhg's witness statement" in player.get("inventory", [])
        if action == "testimony" and has_tadhg:
            gain = 25 + press_bonus
            msg = (
                "The gallery gasps as you read Tadhg's sworn statement that all three midnight saboteurs were completely clean-shaven—and then gesture to Farmer Flyfornication's waist-length fiery red beard in the dock!"
            )
        elif action == "testimony":
            gain = -12
            msg = (
                "You challenge Ned's eyesight, but without a sworn eyewitness who was actually on the river reeds that night, Ned sticks stubbornly to his story! (-12% Doubt)"
            )
        else:
            gain = -10
            msg = "Magistrate Fleepride taps her gavel: \"Address the witness's claim that he saw the accused's face by lantern-light, Advocate!\" (-10% Doubt)"

    # --- WITNESS 3: CHIEF CLERK PINCHPENNY (MOTIVE & CUI BONO) ---
    elif w_idx == 2:
        has_motive = (
            player.get("intel_kokeshi_debt", False)
            or ("spectacles" in player.get("bailiff_tells_learned", []))
            or player.get("m1e_post_ledger_clue", False)
        )
        has_chisel = player.get("flyfornication_chisel_clue", False)

        if action == "motive" and has_motive:
            gain = 25 + press_bonus
            msg = (
                "Pinchpenny turns ash-pale as you expose the Bailiff's overdue Kokeshi debts and the violet-ink kickbacks—proving the Syndicate framed Flyfornication to seize his mill-lease for the eastern granary wharf!"
            )
        elif action == "forensics" and has_chisel:
            gain = 18 + press_bonus
            msg = (
                "You point to the yellow fuller's earth found on the mill sluice-plank—matching the exact clay on the floor of the Bailiff's brick granary yard!"
            )
        else:
            gain = -12
            msg = (
                "You accuse the Counting House of a frame-up, but without proof of Seekgrace's Kokeshi debts or the granary clay trail, Pinchpenny dismisses it as slander! (-12% Doubt)"
            )

    # Roll 2d6 Rhetoric & Gallery Variance on every courtroom exchange!
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    court_swing = (d1 + d2 - 7) * 2
    gain += court_swing
    if d1 + d2 == 12:
        msg += " [WINDFALL (Rolled 12!): The townsfolk in the gallery erupt in applause, visibly swaying Magistrate Fleepride!]"
    elif d1 + d2 == 2:
        msg += " [FRICTION (Rolled 2!): Clerk Pinchpenny raises a procedural objection that blunts part of your point!]"
    msg = f"[Roll {d1}+{d2}] " + msg

    player["tribunal_doubt"] = max(0, min(100, player.get("tribunal_doubt", 30) + gain))

    # Advance to next witness or to final verdict
    if w_idx + 1 < len(TRIBUNAL_WITNESSES):
        player["tribunal_witness_idx"] = w_idx + 1
        player["tribunal_pressed"] = False
        player["tribunal_feedback"] = msg + f" (Next up: {TRIBUNAL_WITNESSES[w_idx + 1]['name']})"
    else:
        player["tribunal_phase"] = "VERDICT"
        doubt = player["tribunal_doubt"]
        verdict_tag = "FULL ACQUITTAL!" if doubt >= 70 else "CONVICTION UPHELD!"
        player["tribunal_feedback"] = f"{msg} — [Magistrate's Doubt: {doubt}% — {verdict_tag}] Click [Hear Final Verdict >>]!"

    return player, player["tribunal_feedback"], "MINIGAME_TRIBUNAL"


def conclude_tribunal_minigame(player):
    doubt = player.get("tribunal_doubt", 0)
    player["ch2_mission_step"] = 5
    player["active_ch2_mission"] = None

    if doubt >= 70:
        player["position_strength"] = player.get("position_strength", 0) + 25
        player["reputation"] = player.get("reputation", 0) + 2
        modify_faction(player, "faction_union", 3)
        log = (
            f"=== TRIBUNAL ACQUITTAL (Doubt Raised to {doubt}% — +25% Position Strength, +2 Reputation, +3 Union Faction)! ===\n"
            "Magistrate Fleepride slams her gavel down so hard the inkwells rattle!\n"
            "\"Perjury and fabrication! The charges against Farmer Flyfornication are hereby dismissed in full, his shackles struck off, "
            "and a formal inquiry opened into the Counting House's conduct!\"\n\n"
            "As Flyfornication embraces you outside the courtroom, Organiser Joyinsorrow intercepts you in the shadow of the staircase, their face pale:\n"
            "\"Noburu—while we were in court, someone unlocked the Union's emergency strike chest using a duplicate key, stole forty silver, and passed our secret grain-cache locations to the Kokeshi!\"\n"
            "\"Every leader on our committee is held beyond reproach here in the valley—which is why I am placing **you** in charge of the investigation. "
            "Search the region, question our people and the townsfolk, and when you know the truth, bring the evidence back to **Union House in Murum Town** so an unbiased council can judge the traitor!\""
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) - 15)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            f"=== TRIBUNAL CONVICTION (Doubt Only Reached {doubt}% < 70% Required — -15% Position Strength, +1 Exposure Tell) ===\n"
            "Magistrate Fleepride shakes her head coldly: \"The defence has failed to substantiate its allegations with hard proof. "
            "Farmer Flyfornication's mill-lease is hereby forfeited to the estate!\"\n\n"
            "As the guards lead Flyfornication away, Organiser Joyinsorrow pulls you aside with even darker news:\n"
            "\"Someone on our own Union committee leaked our defence strategy and stole forty silver from the strike chest! "
            "Investigate around Fluvius and the farmlands, and report to **Union House in Murum Town** for an unbiased tribunal once you can prove who betrayed us!\""
        )
    return player, log, "MAIN"


def draw_tribunal_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for the Mission 1D Courtroom Battle."""
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

    title = font_bold.render("FLUVIUS MAGISTRATE'S TRIBUNAL — DEFENCE OF FLYFORNICATION", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    # Judicial Doubt / Acquittal Gauge (Need 70%+ for Acquittal)
    doubt = player.get("tribunal_doubt", 30)
    screen.blit(font_bold.render(f"Magistrate's Doubt in Prosecution: {doubt}% (Need 70%+ to Acquit)", True, CLOCK_BLACK), (85, 78))

    bar_rect = pygame.Rect(85, 100, 630, 20)
    pygame.draw.rect(screen, (40, 36, 36), bar_rect, border_radius=5)
    fill_w = int(630 * (doubt / 100.0))
    if fill_w > 0:
        b_col = (45, 135, 65) if doubt >= 70 else (205, 145, 50)
        pygame.draw.rect(screen, b_col, (85, 100, fill_w, 20), border_radius=5)
    # 70% Threshold Marker
    tx = 85 + int(630 * 0.70)
    pygame.draw.line(screen, (255, 255, 255), (tx, 98), (tx, 122), 3)
    pygame.draw.rect(screen, CLOCK_BLACK, bar_rect, width=1, border_radius=5)

    w_idx = player.get("tribunal_witness_idx", 0)
    w_data = TRIBUNAL_WITNESSES[w_idx]
    pressed = player.get("tribunal_pressed", False)

    # Witness Stand Box
    w_box = pygame.Rect(85, 130, 630, 145)
    pygame.draw.rect(screen, (252, 248, 238), w_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, w_box, width=2, border_radius=8)

    w_hdr = f"ON THE STAND ({w_idx + 1}/3): {w_data['name'].upper()}" + (" [PRESSED UNDER OATH]" if pressed else "")
    screen.blit(font_bold.render(w_hdr, True, TATE_RED), (100, 138))

    claim_text = w_data["pressed_claim"] if pressed else w_data["initial_claim"]
    draw_fitted_text(screen, claim_text, pygame.Rect(100, 165, 600, 100), CLOCK_BLACK, bold=False, max_lines=4)

    # Courtroom Transcript / Ruling Box
    fb_box = pygame.Rect(85, 283, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("tribunal_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)

# =========================================================================
# 6. MISSION 1E: THE TRAITOR INVESTIGATION & MURUM UNION HOUSE TRIBUNAL
# =========================================================================
TRAITOR_SUSPECTS = [
    "Organiser Joyinsorrow",
    "Ploughman Steadfast",
    "Orchardist Goodseed",
    "Delegate Faintnot",
]

TRAITOR_METHODS = [
    "Pried Open with an Iron Crowbar",
    "Picked with a Bent Wire",
    "Duplicate Key Cast from a Beeswax Mould",
    "Smashed Open with a Boundary Stone",
]

TRAITOR_LEAKS = [
    "Flashed a Signal Lantern from the Mill",
    "Pigeon-Post Written with a Split Brass Nib",
    "Whispered to an Off-Duty Lancer",
    "Stuffed Inside a Cider Cask",
]

TRAITOR_MOTIVES = [
    "Hidden in the Southern Eel-Weirs",
    "Sent North to Castle Laydere",
    "Paid a 40-Silver Gambling Tab at the Quay",
    "Buried Beneath the Western Orchards",
]

# True Solution Indices: Faintnot (3), Beeswax Mould (2), Split Brass Nib (1), 40s Quay Tab (2)
TRUE_TRAITOR_INDICTMENT = (3, 2, 1, 2)

SUSPECT_TESTIMONIES = {
    0: (
        "ORGANISER JOYINSORROW: \"I never left the crossroads brazier except to attend Flyfornication's trial with you, Noburu. "
        "I carry one of the two keys to the strike chest around my neck—and it hasn't left my waistcoat.\""
    ),
    1: (
        "PLOUGHMAN STEADFAST: \"Me and my boys were ditching the oat-furrows until sundown. "
        "I barely know how to sign my own mark in chalk, let alone write dispatches in fancy violet ink!\""
    ),
    2: (
        "ORCHARDIST GOODSEED: \"I was Cooper-banding apple casks in the western orchard shed all evening. "
        "Check my hands—nothing on them but apple-must and pine resin.\""
    ),
    3: (
        "DELEGATE FAINTNOT: \"As Strike Treasurer, I guard the second key with my life! Last night before curfew I was... "
        "er... fasting and praying alone in the orchard chapels. I never went near the Post Office, the granary wharf, or the taproom!\""
    ),
}


def get_faintnot_options(player):
    opts = ["Ask about the Strike Committee's treasury"]
    if player.get("ch2_mission_step") == 5:
        opts.insert(0, "Question Faintnot about where he was when the chest was robbed")
        opts.insert(1, "Look closely at Faintnot's hands and coat cuffs")
    opts.append("Leave")
    return opts


def resolve_faintnot(choice, player):
    if choice == "Leave":
        return player, "Delegate Faintnot clutches his leather ledger-satchel tightly to his chest.", "MAIN"

    if choice == "Ask about the Strike Committee's treasury":
        return player, (
            "Delegate Faintnot—a prim, narrow-shouldered clerk with ink-stained fingers—adjusts his collar.\n"
            "\"Every penny of the agrarian strike fund is accounted for by double-entry bookkeeping, comrade. "
            "The farmhands revere the four of us on the committee like saints.\""
        ), "NPC_DIALOGUE"

    if choice == "Question Faintnot about where he was when the chest was robbed":
        player["m1e_questioned_faintnot"] = True
        return player, (
            "Faintnot's left eyelid twitches.\n"
            "\"Robbed? A tragedy! Why, while you were at the Tribunal, I was meditating in the western orchards far from town. "
            "Some outside cutpurse must have pried the lockbox open with a crowbar!\"\n"
            "\"And why are you questioning me, an elected pillar of Fluvius? Only the General Executive at **Union House in Murum Town** has the authority to judge a committee member!\""
        ), "NPC_DIALOGUE"

    if choice == "Look closely at Faintnot's hands and coat cuffs":
        player["m1e_inspected_faintnot"] = True
        return player, (
            "As Faintnot reaches up to adjust his cravat, you notice a crescent of soft **beeswax** wedged beneath his right thumbnail, "
            "a smudge of **violet ink** on his middle finger where a brass nib split, and dustings of **yellow fuller's earth** along the hem of his boots."
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def init_traitor_tribunal(player):
    """Initializes the Mission 1E Unbiased Traitor Tribunal Pop-Out at Union House in Murum."""
    player["traitor_phase"] = "DELIBERATE"  # "DELIBERATE" or "VERDICT"
    # Start with non-solution defaults so the player must actively set the indictment
    player["traitor_picks"] = [0, 0, 0, 0]
    player["traitor_focus_suspect"] = 0
    player["traitor_feedback"] = (
        "Union Representative Truthtale calls the Murum Executive Council to order: "
        "\"Review the four Fluvius delegates' statements above, then set all four particulars of your formal indictment below.\""
    )
    return player, player["traitor_feedback"], "MINIGAME_TRAITOR"


def traitor_action(action, player):
    """Handles clicks inside the MINIGAME_TRAITOR pop-out at Murum Union House."""
    phase = player.get("traitor_phase", "DELIBERATE")
    if phase == "VERDICT":
        return conclude_traitor_tribunal(player)

    if action.startswith(" testimony_"):
        idx = int(action.split("_")[1])
        player["traitor_focus_suspect"] = idx
        player["traitor_feedback"] = SUSPECT_TESTIMONIES[idx]
        return player, None, "MINIGAME_TRAITOR"

    if action == "cycle_suspect":
        player["traitor_picks"][0] = (player["traitor_picks"][0] + 1) % 4
        player["traitor_focus_suspect"] = player["traitor_picks"][0]
        player["traitor_feedback"] = SUSPECT_TESTIMONIES[player["traitor_picks"][0]]
        return player, None, "MINIGAME_TRAITOR"

    if action == "cycle_method":
        player["traitor_picks"][1] = (player["traitor_picks"][1] + 1) % 4
        return player, None, "MINIGAME_TRAITOR"

    if action == "cycle_leak":
        player["traitor_picks"][2] = (player["traitor_picks"][2] + 1) % 4
        return player, None, "MINIGAME_TRAITOR"

    if action == "cycle_motive":
        player["traitor_picks"][3] = (player["traitor_picks"][3] + 1) % 4
        return player, None, "MINIGAME_TRAITOR"

    if action == "leave_council":
        player["active_ch2_mission"] = None
        return player, (
            "You request a recess from Truthtale's council to gather more evidence in Fluvius before presenting your final indictment."
        ), "MAIN"

    if action == "submit_indictment":
        picks = tuple(player.get("traitor_picks", [0, 0, 0, 0]))
        matches = sum(1 for a, b in zip(picks, TRUE_TRAITOR_INDICTMENT) if a == b)
        player["traitor_matches"] = matches
        player["traitor_phase"] = "VERDICT"

        if picks == TRUE_TRAITOR_INDICTMENT:
            player["traitor_feedback"] = (
                "UNANIMOUS CONVICTION (4/4 Proofs Verified)! Faced with the beeswax mould, the split brass nib dispatch, "
                "and the 40-silver Barge & Anchor receipt, Delegate Faintnot breaks down and confesses before the Murum Council!"
            )
        elif picks[0] == 3 and matches >= 2:
            player["traitor_feedback"] = (
                f"PARTIAL INDICTMENT ({matches}/4 Accurate): You named Delegate Faintnot, but some of your forensic particulars were inaccurate. "
                "Faintnot is stripped of office, though he manages to burn half the Kokeshi ledger in the confusion!"
            )
        else:
            accused_name = TRAITOR_SUSPECTS[picks[0]]
            player["traitor_feedback"] = (
                f"INDICTMENT COLLAPSES ({matches}/4 Accurate)! Your case against {accused_name} falls apart under scrutiny—and while the council argues, "
                "the true informant slips out of Murum with the strike fund!"
            )
        return player, player["traitor_feedback"], "MINIGAME_TRAITOR"

    return player, None, "MINIGAME_TRAITOR"


def conclude_traitor_tribunal(player):
    picks = tuple(player.get("traitor_picks", [0, 0, 0, 0]))
    matches = player.get("traitor_matches", 0)
    player["ch2_mission_step"] = 6
    player["active_ch2_mission"] = None
    db.npc_database["faintnot"]["location"] = None

    if picks == TRUE_TRAITOR_INDICTMENT:
        player["position_strength"] = player.get("position_strength", 0) + 25
        player["reputation"] = player.get("reputation", 0) + 3
        player["influence"] = player.get("influence", 0) + 2
        modify_faction(player, "faction_union", 4)
        player.setdefault("ch3_world_bits", {})["track_1"] = 1
        log = (
            "=========================================================\n"
            "   MISSION COMPLETE: THE UNION STANDS UNBROKEN!       \n"
            "=========================================================\n"
            "In the neutral chamber of Murum Union House, your ironclad investigation leaves no room for doubt or factional division.\n"
            "Delegate Faintnot is expelled in disgrace, the stolen 40 silver and the grain-cache cipher are recovered intact, "
            "and the northern and southern chapters of the Workers' Union unite under your banner as the war of Chapter 3 dawns!\n\n"
            f"*** (+25% Position Strength, +3 Reputation, +2 Influence, +4 Union Faction | Final Position Strength: {player.get('position_strength', 0)}%) ***"
        )
    elif picks[0] == 3 and matches >= 2:
        player["position_strength"] = player.get("position_strength", 0) + 12
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        player.setdefault("ch3_world_bits", {})["track_1"] = 1
        log = (
            "=== MISSION COMPLETE: TRAITOR EXPELLED WITH DOUBTS ===\n"
            "You correctly unmasked Delegate Faintnot, though gaps in your forensic presentation allowed him to destroy part of the Kokeshi correspondence before being seized (+12% Position Strength, +1 Exposure Tell)."
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) - 20)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 2
        player.setdefault("ch3_world_bits", {})["track_1"] = 0
        log = (
            "=== MISSION FAILED: THE UNION FRACTURES ON THE EVE OF WAR! ===\n"
            "Your flawed accusation throws the Murum and Fluvius delegates into a bitter schism while Delegate Faintnot escapes with the strike fund (-20% Position Strength, +2 Exposure Tells)!"
        )

    return player, log, "CHAPTER_2_COMPLETE"


def draw_traitor_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for the Mission 1E Murum Union Tribunal."""
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

    title = font_bold.render("MURUM UNION HOUSE — GENERAL EXECUTIVE TRIBUNAL", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    sub = font.render("Unbiased Inquiry into the Stolen Fluvius Strike Fund & Kokeshi Leak", True, CLOCK_BLACK)
    screen.blit(sub, (400 - sub.get_width() // 2, 76))

    # Suspect Alibi / Testimony Box
    test_box = pygame.Rect(85, 100, 630, 88)
    pygame.draw.rect(screen, (252, 248, 238), test_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, test_box, width=2, border_radius=8)
    focus_idx = player.get("traitor_focus_suspect", 0)
    draw_fitted_text(screen, SUSPECT_TESTIMONIES.get(focus_idx, ""), test_box.inflate(-16, -10), CLOCK_BLACK, max_lines=3)

    # Current Indictment Readout Box
    picks = player.get("traitor_picks", [0, 0, 0, 0])
    ind_box = pygame.Rect(85, 196, 630, 108)
    pygame.draw.rect(screen, (236, 228, 212), ind_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, ind_box, width=1, border_radius=8)

    lines = [
        f"1. ACCUSED TRAITOR:  {TRAITOR_SUSPECTS[picks[0]]}",
        f"2. LOCKBOX METHOD:   {TRAITOR_METHODS[picks[1]]}",
        f"3. LEAK CHANNEL:     {TRAITOR_LEAKS[picks[2]]}",
        f"4. STOLEN 40 SILVER: {TRAITOR_MOTIVES[picks[3]]}",
    ]
    for i, ln in enumerate(lines):
        screen.blit(font_bold.render(ln, True, TATE_RED if i == 0 else CLOCK_BLACK), (100, 204 + i * 24))

    # Transcript / Verdict Banner
    fb_box = pygame.Rect(85, 310, 630, 52)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("traitor_feedback", ""), fb_box.inflate(-14, -6), (245, 240, 230), max_lines=2)

# =========================================================================
# MODULE REGISTRATION (HANDLERS)
# =========================================================================
HANDLERS = {
    "keepfaith": (get_keepfaith_options, resolve_keepfaith),
    "oisin":     (get_oisin_options, resolve_oisin),
    "fearghal":  (get_fearghal_options, resolve_fearghal),
    "corban":    (get_corban_options, resolve_corban),
    "faintnot":  (get_faintnot_options, resolve_faintnot),
}
