"""
ch2_guard.py
------------
Chapter 2 Track 2 (Frontier Watch / Town Guard) mechanics for Fluvius Town:
- Mission 2B exploration NPCs (Constable Aelfwine, Chandler Hopewell, Mairead)
- Environmental search hooks (Clock-Tower theatrical hamper, Cooperage canal-pump,
  Eastern Salt-Cellar Kokeshi diversion)
- Mission 2B Non-Lethal Riot Control Shield-Wall Pop-Out (`MINIGAME_RIOT`)
"""

import pygame
import random
import game_data as db
from mechanics import modify_faction, advance_time, execute_ch2_mission
from ui_components import draw_fitted_text

def roll_guard_2d6_twist(player, context="riot"):
    """
    Rolls 2d6 for Guard tactical variance (-10% to +10% swing) plus a 30% chance of a Windfall or Friction twist!
    Returns (swing_int, prefix_str, twist_str).
    """
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    swing = (d1 + d2 - 7) * 2
    prefix = f"[Roll {d1}+{d2}={d1+d2}] "
    twist_str = ""

    if random.random() < 0.30:
        if context == "riot":
            twists = [
                ("WINDFALL: A guild alderman on an upper balcony cheers your discipline and tosses down a 10-silver purse! (+10s)", 4),
                ("WINDFALL: A sudden gust of river-rain dampens the rioters' pitch-torches! (-8% Crowd Fury)", 8),
                ("FRICTION: A barrel of tallow-grease spills across the cobbles, making footing treacherous! (-6% Discipline)", -6),
            ]
        else:
            twists = [
                ("WINDFALL: One of Corban's scab wagons drops a linchpin in the mud, slowing the Kokeshi push! (-8% Aggression)", 8),
                ("WINDFALL: A passing drover shares a skin of cider with your thirsty halberdiers! (+10 Thirst, +5% Integrity)", 5),
                ("FRICTION: A sudden Brumaire wind-squall blows acrid brazier smoke straight into your cordon! (-6% Integrity)", -6),
            ]
        t_text, mod = random.choice(twists)
        swing += mod
        if "+10s" in t_text:
            player["silver"] += 10
        if "+10 Thirst" in t_text:
            player["thirst"] = min(100, player.get("thirst", 100) + 10)
        twist_str = f" [{t_text}]"

    return swing, prefix, twist_str

# =========================================================================
# 1. MISSION 2B EXPLORATION NPCS IN FLUVIUS TOWN (AELFWINE, HOPEWELL, MAIREAD)
# =========================================================================
def get_aelfwine_options(player):
    opts = ["Ask about the situation in Fluvius Town"]
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)

    if route == "Apply for Town Guard":
        if step == 2:
            opts.insert(0, "Ask what sparked the riot in the square")
            if player.get("m2b_started"):
                opts.insert(0, "Mission: Form the Watch Shield-Wall & Advance into the Square!")
        elif step == 3 and player.get("m2c_started"):
            opts.insert(0, "Ask for a scout report on the Crossroads perimeter")
            opts.insert(0, "Mission: Take Command of the Watch Cordon at the Crossroads!")
    opts.append("Leave")
    return opts


def resolve_aelfwine(choice, player):
    """Resolves player conversation with Constable Aelfwine."""
    if choice == "Leave":
        return player, "Constable Ælfwine tightens the strap on his dented buckler and watches the bridge.", "MAIN"

    if choice == "Ask about the situation in Fluvius Town":
        return player, (
            "Constable Ælfwine dabs a split lip with the back of his sleeve.\n"
            "\"The square outside the Counting House is a powder-keg, Corporal. Bargemen and cobblers have torn up cobblestones and lit pitch-torches.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask what sparked the riot in the square":
        player["m2b_aelfwine_questioned"] = True
        return player, (
            "Ælfwine lowers his voice, leaning on his ash staff.\n"
            "\"That's the queerest part, Corporal. An hour ago, three fellows dressed in the black-and-gold livery of Castle Ragmore strode into the square, "
            "announced a tenfold 'breathing tax', and tipped over an old widow's apple-cart!\"\n\n"
            "\"When I tried to check their warrants, the lead bailiff declaimed a speech in rhyming pentameter—and I swear on my mother's grave, "
            "when the wind caught his cloak, he smelled of stage-greasepaint and lavender water! Before I could grab him, they vanished toward the southern lanes.\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Form the Watch Shield-Wall & Advance into the Square!":
        player, t_msg = execute_ch2_mission(player, "2b_riot", time_cost=90, stamina_drain=15)
        player, log, next_state = init_riot_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice == "Ask for a scout report on the Crossroads perimeter":
        cache = "Confiscated" if player.get("m2c_weapons_confiscated") else "Unchecked (Rumours of planted blades near the orchards)"
        lancers = "Stood down" if player.get("m2c_lancers_stood_down") else "Restless on the northern farm ridge"
        outlaws = "Flank guarded" if player.get("m2c_outlaw_ambush_foiled") else "Unchecked tracks in the western sunken lane"
        return player, (
            "Constable Ælfwine salutes beside the overturned hay-wains:\n"
            f"• **Rumoured Provocateur Weapons:** {cache}.\n"
            f"• **Castellan Lancer Detachment:** {lancers}.\n"
            f"• **Western Sunken Lane Flank:** {outlaws}.\n"
            "\"Give the word when you are ready to form the thin blue line between the strikers and the convoy, Corporal!\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Take Command of the Watch Cordon at the Crossroads!":
        player, t_msg = execute_ch2_mission(player, "2c_strike", time_cost=120, stamina_drain=15)
        player, log, next_state = init_strike_cordon_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    return player, "Error.", "MAIN"


def get_hopewell_options(player):
    """Returns dialogue options for Chandler Hopewell on Chandlers' Row."""
    opts = ["Ask about his chandlery wares"]
    if player.get("ch2_mission_step") == 2:
        opts.insert(0, "Ask if he saw the 'Castellan bailiffs' pass this way")
    opts.append("Leave")
    return opts


def resolve_hopewell(choice, player):
    """Resolves player conversation with Chandler Hopewell."""
    if choice == "Leave":
        return player, "Chandler Hopewell bars his shop shutters against the noise from the square.", "MAIN"

    if choice == "Ask about his chandlery wares":
        return player, (
            "\"Tallow dips, hemp cordage, and tarred canvas—though I daren't open the counter while the cobbles are flying in the square!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask if he saw the 'Castellan bailiffs' pass this way":
        player["m2b_hopewell_questioned"] = True
        return player, (
            "Chandler Hopewell peers through a crack in his shutters.\n"
            "\"Saw them? I nearly tripped over them! Ten minutes after the shouting started in the square, three men in Castellan tabards came sprinting down my lane—laughing their heads off!\"\n"
            "\"One of them peeled off his false horsehair moustache right under my sign and ducked into the shadowed cul-de-sac behind the **Civic Clock-Tower** to the east. "
            "If those were real noble bailiffs, I'm the King of Dtessera!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_mairead_options(player):
    """Returns dialogue options for Mairead the Barge-Wife at the Southern Delta Timber-Booms."""
    opts = ["Ask about the timber-booms on the delta"]
    if player.get("ch2_mission_step") == 2:
        opts.insert(0, "Ask why the river-bargees joined the riot")
    opts.append("Leave")
    return opts


def resolve_mairead(choice, player):
    """Resolves player conversation with Mairead the Barge-Wife."""
    if choice == "Leave":
        return player, "Mairéad turns back to tending the smouldering alder-chips in her eel-kiln.", "MAIN"

    if choice == "Ask about the timber-booms on the delta":
        return player, (
            "\"These chained pine booms keep the spring logs from stove-in our hulls,\" Mairéad says, wiping soot from her hands."
        ), "NPC_DIALOGUE"

    if choice == "Ask why the river-bargees joined the riot":
        player["m2b_mairead_questioned"] = True
        return player, (
            "Mairéad snorts, pointing her iron poker toward the north-eastern bends of the river.\n"
            "\"My husband and the bargees were played for fools, Watchman. While those painted 'bailiffs' got the whole town screaming outside the Counting House, "
            "I saw four Kokeshi wagons slip down to the **Eastern Salt-Cellars** completely unsearched by the customs watch!\"\n\n"
            "\"And if you want to cool the hotheads in the square without cracking skulls, take a look at the **Cooperage & Sluice Ford** on the river just south of the granaries—the cooper's brass canal-pump feeds the street hydrants right beside the square!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 2. ENVIRONMENTAL SEARCH HOOKS FOR MISSION 2B IN FLUVIUS TOWN
# =========================================================================
def handle_guard_fluvius_search(player):
    """
    Called inside action_gather() when exploring Fluvius Town.
    Returns (handled_bool, log_message).
    """
    pos = (player["x"], player["y"])
    if player.get("current_building"):
        return False, ""

    # 1. Civic Clock-Tower Cul-de-Sac (12, 2): Discover the Theatrical Costumes!
    if pos == (12, 2) and player.get("ch2_mission_step") == 2:
        if player.get("m2b_costumes_found"):
            return True, "You have already collected the discarded theatrical tabards and greasepaint from the hamper behind the Clock-Tower."
        player["m2b_costumes_found"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Searching the shadowed cul-de-sac behind the Civic Clock-Tower, you pry open a wicker theatrical hamper stamped 'MURUM PLAYHOUSE — FAIRLIGHT'S TROUPE'.\n"
            "Inside lie three papier-mâché Castellan crests, Tin-Foil Bailiff Chains, a jar of stage greasepaint, and three horsehair moustaches still sticky with spirit-gum!\n"
            "You bundle the fake livery under your arm—irrefutable proof that the riot was staged by actors!"
        )

    # 2. The Cooperage & Sluice Ford (12, 3): Prime the Brass Canal-Pump!
    if pos == (12, 3) and player.get("ch2_mission_step") == 2:
        if player.get("m2b_pump_primed"):
            return True, "The brass canal-pump at the weir is already primed and pressurized, feeding river water up to the Market Square sluice-cock."
        player["m2b_pump_primed"] = True
        player, _ = advance_time(15, player)
        return True, (
            "You step onto the stone weir beside the cooperage and unpin the heavy iron flywheel on the brass canal-pump.\n"
            "Hauling down on the lever until the leather bellows hiss with river-pressure, you open the valve feeding the upper Market Square cisterns!"
        )

    # 3. Eastern Bargemen's Row & Salt-Cellars (13, 3): Intercept the Kokeshi Diversion Cargo!
    if pos == (13, 3) and player.get("ch2_mission_step") == 2:
        if player.get("m2b_smugglers_caught"):
            return True, "The iron-grated salt-cellar is padlocked under Watch seal, and the Kokeshi contraband casks are impounded."
        player["m2b_smugglers_caught"] = True
        player["silver"] += 20
        player, _ = advance_time(20, player)
        return True, (
            "Creeping down the cellar ramp along Eastern Bargemen's Row, you catch two Kokeshi carters rolling unstamped casks into a barge while the town Watch is distracted by the riot!\n"
            "At the sight of your Watch badge, the carters bolt up the towpath, abandoning a **20-silver** bribe-pouch and their manifest—confirming they paid Fairlight's Troupe to stage the riot as a decoy! (+20 Silver)"
        )

    # 4. Mission 2C Search in the Western Cider Orchards (10, 6): Confiscate Planted Provocateur Blades!
    if pos == (10, 6) and player.get("ch2_mission_step") == 3:
        if player.get("m2c_weapons_confiscated"):
            return True, "You have already confiscated the oilskin bundle of planted Kokeshi cleavers and coshes from beneath the orchard hay."
        player["m2c_weapons_confiscated"] = True
        player, _ = advance_time(20, player)
        return True, (
            "Searching beneath a pile of loose hay-bales where the orchard fence meets the crossroads track, "
            "your boot strikes a heavy oilskin roll.\n"
            "Unwrapping it, you find half a dozen notched meat-cleavers and leaded iron coshes stamped with Union initials in fresh paint—planted here by Kokeshi agents so a provocateur could draw steel during the standoff and trick the Watch into slaughtering the strikers!\n"
            "You lock the entire bundle into your Watch evidence sack."
        )

    # 5. Mission 2C Search in the Sunken Sluice-Gate Lane (10, 5): Spot & Foil Black Dog's Outlaw Ambush (Linked to 9C)!
    if pos == (10, 5) and player.get("ch2_mission_step") == 3:
        if player.get("m2c_outlaw_ambush_foiled"):
            return True, "Two Watch halberdiers are posted atop the clay embankment, keeping the sunken lane secure against highwaymen."
        player["m2c_outlaw_ambush_foiled"] = True
        player, _ = advance_time(20, player)
        return True, (
            "Examining the gorse atop the high clay bank of the Sunken Lane, you spot four lathered horses tethered in the brush and freshly notched crossbow bolts aimed toward the rear of the Kokeshi pay-wagon!\n"
            "It is an outlaw ambush laid by Black Dog's highwaymen to rob the payroll while the Watch is busy at the barricade!\n"
            "You blow a low signal-note on your Watch whistle and post two halberdiers on the ridge—sending the outlaws scurrying back into the heath empty-handed!"
        )

    # 6. Mission 2D Search outside Murum Stables (7, 15): Inspect the Mayor's State Coach!
    if pos == (7, 15) and player.get("ch2_mission_step") == 4:
        if player.get("m2d_coach_repaired"):
            return True, "The Mayor's state coach has already been reinforced with a forged iron trace-link, and the decoy chest is rigged on the roof."
        roll = random.randint(1, 6) + max(player.get("stealth", 0), player.get("equusense", 0)) + (3 if "forge" in player.get("skills", []) else 0)
        player["m2d_coach_repaired"] = True
        player, _ = advance_time(20, player)
        if roll >= 6:
            player["silver"] += 8
            return True, (
                "Inspecting the undercarriage of the Mayor's state coach, you spot a white silk ribbon tied under the lantern-bracket—a highwayman's target mark—and discover that the left iron trace-chain has been filed halfway through!\n"
                "You cold-rivet a spare iron link over the sabotaged chain, move the real tribute chest under the footman's box, and even find **8 silver coins** dropped in the straw by the saboteur! (+8 Silver Windfall)"
            )
        else:
            player["health"] = max(1, player.get("health", 10) - 1)
            return True, (
                "You spot a filed iron link on the Mayor's trace-chain and a white silk signal ribbon under the lamp! "
                "As you wrench the sabotaged link free to replace it, the iron pin snaps and pinches your palm (-1 Health)—but the coach's traces are now secure!"
            )

    # 7. Mission 2D Search at the New Road Muddy Hollow (7, 22): Scout the Outlaw Kill-Zone!
    if pos == (7, 22) and player.get("ch2_mission_step") == 4:
        if player.get("m2d_hollow_scouted"):
            return True, "The sawn pine trunk above the Muddy Hollow has already had its haul-ropes severed, and your ambush markers are set."
        roll = random.randint(1, 6) + max(player.get("stealth", 0), player.get("strength", 0))
        player["m2d_hollow_scouted"] = True
        player, _ = advance_time(25, player)
        if roll >= 6:
            return True, (
                "Creeping up the gorse-choked bank above the Muddy Hollow, you discover a massive pine tree sawn three-quarters through and rigged with hemp haul-ropes by Black Dog's highwaymen!\n"
                "Moving like a shadow, you slice the tension-ropes with your blade so the trap cannot be sprung across the Mayor's horses!"
            )
        else:
            player["hunger"] = max(0, player.get("hunger", 100) - 10)
            return True, (
                "Scrambling through the wet brambles above the Muddy Hollow (-10 Hunger), you find a sawn pine trunk rigged with outlaw haul-ropes and cut the lines before the ambushers notice you!"
            )

    return False, ""


# =========================================================================
# 3. MISSION 2B POP-OUT MINIGAME: QUELLING THE FLUVIUS RIOT (MINIGAME_RIOT)
# =========================================================================
RIOT_WAVES = [
    {
        "title": "SURGE 1: COBBLESTONE VOLLEY FROM THE STEPS!",
        "desc": (
            "A score of angry dockers and apprentices wrench loose cobblestones from the gutter and hurl a hail of stones toward your front rank!"
        ),
        "best": "lock_shields",
    },
    {
        "title": "SURGE 2: THE RINGLEADER ON THE CIDER-BARREL!",
        "desc": (
            "A masked agitator leaps atop an overturned barrel, waving a forged tax-scroll and screaming that the Watch is here to seize every workman's tools!"
        ),
        "best": "expose_hoax",
    },
    {
        "title": "SURGE 3: PITCH-TORCHES AT THE COUNTING HOUSE DOORS!",
        "desc": (
            "A knot of hotheads with blazing pitch-torches surges toward the dry oak doors of the Counting House to set the archive ablaze!"
        ),
        "best": "flood_sluice",
    },
    {
        "title": "SURGE 4: THE FINAL PRESS IN THE SQUARE!",
        "desc": (
            "Hemmed in between the stalls, the wavering crowd presses chest-to-shield against your halberdiers, waiting to see if the Watch will draw blood or hold firm!"
        ),
        "best": "measured_advance",
    },
]


def init_riot_minigame(player):
    """Initializes the Mission 2B Non-Lethal Riot Control Pop-Out Window."""
    player["riot_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["riot_wave_idx"] = 0
    player["riot_fury"] = 85
    player["riot_discipline"] = 80 + min(20, player.get("strength", 0) * 2)

    if player.get("m2b_costumes_found"):
        player["riot_fury"] -= 15
    if player.get("m2b_pump_primed"):
        player["riot_discipline"] = min(100, player["riot_discipline"] + 10)

    player["riot_feedback"] = (
        "You form your Watch squad shoulder-to-shoulder across the mouth of Fluvius Square! "
        "Read each surge of the crowd and choose the right tactical command to bring Crowd Fury down to 0% without breaking Watch Discipline!"
    )
    return player, player["riot_feedback"], "MINIGAME_RIOT"


def riot_action(action, player):
    """Processes tactical shield-wall commands inside MINIGAME_RIOT."""
    if player.get("riot_phase") == "RESULT":
        return conclude_riot_minigame(player)

    w_idx = player.get("riot_wave_idx", 0)
    fury_delta = 0
    disc_delta = 0
    msg = ""

    # 1. LOCK OVERLAPPING SHIELDS & DRUM-BEAT (Best vs Cobblestone Volley)
    if action == "lock_shields":
        if w_idx == 0:
            fury_delta = -25
            disc_delta = 5
            msg = (
                "CLANG-THUD! Your Watchmen lock overlapping ash shields at a forty-five-degree slant! "
                "The hail of cobblestones bounces harmlessly off the rim as your steady drum-beat cows the throwers!"
            )
        else:
            fury_delta = -10
            disc_delta = -5
            msg = "Your squad turtles behind their shields, holding their ground, though the agitators keep shouting unchallenged."

    # 2. EXPOSE FAIRLIGHT'S THEATRICAL MASQUERADE (Best vs Agitator on Barrel)
    elif action == "expose_hoax":
        if player.get("m2b_costumes_found") or (player.get("m2b_aelfwine_questioned") and player.get("m2b_hopewell_questioned")):
            fury_delta = -35 if w_idx == 1 else -20
            disc_delta = 10
            msg = (
                "You hold up the hamper of papier-mâché Castellan crests, stage greasepaint, and false horsehair moustaches before the square!\n"
                "\"Citizens of Fluvius! Those weren't tax-bailiffs—you were duped by Fairlight's playhouse actors to cover a Kokeshi smuggling run!\" "
                "A roar of embarrassed laughter and outrage at the Syndicate ripples through the crowd, deflating the riot!"
            )
        else:
            fury_delta = 5
            disc_delta = -12
            msg = (
                "You shout that the tax-bailiffs were impostors, but because you didn't find their discarded costumes behind the Clock-Tower, "
                "the crowd jeers at your empty words! (-12% Discipline)"
            )

    # 3. OPEN THE COOPERAGE CANAL-SLUICE HYDRANT (Best vs Pitch-Torches)
    elif action == "flood_sluice":
        if player.get("m2b_pump_primed"):
            fury_delta = -35 if w_idx == 2 else -20
            disc_delta = 10
            msg = (
                "WHOOSH! You kick open the pressurized brass hydrant valve! A freezing jet of River Fluvius water arcs across the steps, "
                "dousing every blazing pitch-torch in seconds and cooling the rioters' heels without a single bruise!"
            )
        else:
            fury_delta = -5
            disc_delta = -15
            msg = (
                "You wrench the street hydrant valve, but only a dry cough of air comes out—you never primed the brass canal-pump down at the Cooperage Ford! "
                "Your men have to beat out the flames with their cloaks! (-15% Discipline)"
            )

    # 4. MEASURED ADVANCE WITH FLAT OF HALBERD-STAVES (Best vs Final Press)
    elif action == "measured_advance":
        str_bonus = 5 if player.get("strength", 0) >= 5 else 0
        if w_idx == 3:
            fury_delta = -25 - str_bonus
            disc_delta = 5
            msg = (
                "In the crisp 3-count cadence you drilled on the Murum parade ground, your Watchmen step forward as one, "
                "using the horizontal ash shafts of their halberds to gently but irresistibly part the crowd back down the side-lanes!"
            )
        elif w_idx == 0:
            fury_delta = -10
            disc_delta = -15
            player["health"] = max(1, player.get("health", 10) - 1)
            msg = "Advancing into a hail of flying cobblestones without locking shields first leaves your line battered (-1 HP, -15% Discipline)!"
        else:
            fury_delta = -15
            disc_delta = -5
            msg = "Your squad pushes forward with horizontal staves, driving the front rank back a few paces."

    # 5. ORDER LETHAL PIKE-CHARGE (Drops Fury fast, but destroys Watch Discipline & Reputation!)
    elif action == "lethal_charge":
        fury_delta = -45
        disc_delta = -45
        player["reputation"] = player.get("reputation", 0) - 3
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        msg = (
            "You order the points of the halberds lowered! The crowd scatters in terror before the steel, "
            "but blood stains the Fluvius cobbles—turning the townsfolk bitterly against the Watch (-45% Discipline, -3 Reputation, +1 Exposure Tell)!"
        )

    swing, prefix, twist_str = roll_guard_2d6_twist(player, context="riot")
    fury_delta -= swing
    disc_delta += (swing // 2)
    msg = prefix + msg + twist_str

    player["riot_fury"] = max(0, min(100, player.get("riot_fury", 85) + fury_delta))
    player["riot_discipline"] = max(0, min(100, player.get("riot_discipline", 80) + disc_delta))

    if player["riot_fury"] <= 0 or player["riot_discipline"] <= 0 or w_idx + 1 >= len(RIOT_WAVES):
        player["riot_phase"] = "RESULT"
        status = (
            "SQUARE SECURED WITHOUT BLOODSHED!"
            if (player["riot_discipline"] > 0 and player["riot_fury"] <= 25)
            else "MESSY SUPPRESSION!"
        )
        player["riot_feedback"] = f"{msg} — [{status}] Click [Conclude Riot Deployment >>]!"
        return player, player["riot_feedback"], "MINIGAME_RIOT"

    player["riot_wave_idx"] = w_idx + 1
    player["riot_feedback"] = msg
    return player, None, "MINIGAME_RIOT"


def conclude_riot_minigame(player):
    """Calculates final Mission 2B rewards and advances the Guard track to Step 3."""
    player["ch2_mission_step"] = 3
    player["active_ch2_mission"] = None

    fury = player.get("riot_fury", 0)
    disc = player.get("riot_discipline", 0)
    smug_bonus = 5 if player.get("m2b_smugglers_caught") else 0

    if disc >= 50 and fury <= 25:
        gain = 20 + smug_bonus + (5 if player.get("m2b_costumes_found") else 0)
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["reputation"] = player.get("reputation", 0) + 2
        modify_faction(player, "faction_guard", 2)
        log = (
            f"=== MISSION COMPLETE: ORDER RESTORED (+{gain}% Position Strength, +2 Reputation, +2 Guard Faction)! ===\n"
            "By unmasking Fairlight's theatrical decoy and cooling the square with disciplined shield-work, you disperse the Fluvius mob without a single citizen slain!\n"
            + ("Better still, your seizure of the Kokeshi contraband at the Eastern Salt-Cellars earns a commendation from the customs bench!\n\n" if smug_bonus else "\n")
            + "*** Next Mission: Report to Lieutenant Beornraed to deploy to the Farmland Crossroads, where tensions between the Union strikers and the Kokeshi scab convoy are about to boil over! ***"
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 5)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: BATTERED SHIELD-LINE (+5% Position Strength, +1 Exposure Tell) ===\n"
            "The square is cleared at last, though bruised Watchmen, scorched shutters, and bitter muttering among the townsfolk leave Lieutenant Beornraed grim-faced.\n\n"
            "*** Next Mission: Report to Lieutenant Beornraed to deploy to the Farmland Crossroads! ***"
        )

    return player, log, "MAIN"


def draw_riot_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for the Mission 2B Riot Shield-Wall."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    WATCH_BLUE = (45, 85, 155)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("FLUVIUS MARKET SQUARE — WATCH SHIELD-WALL DEPLOYMENT", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    fury = player.get("riot_fury", 85)
    disc = player.get("riot_discipline", 80)

    screen.blit(font_bold.render(f"Crowd Fury: {fury}% (Drive down to <= 25%)", True, TATE_RED), (85, 78))
    f_bar = pygame.Rect(380, 78, 335, 16)
    pygame.draw.rect(screen, (40, 35, 35), f_bar, border_radius=4)
    if fury > 0:
        pygame.draw.rect(screen, TATE_RED, (380, 78, int(335 * (fury / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, f_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Watch Discipline & Order: {disc}%", True, WATCH_BLUE), (85, 100))
    d_bar = pygame.Rect(380, 100, 335, 16)
    pygame.draw.rect(screen, (40, 35, 35), d_bar, border_radius=4)
    if disc > 0:
        pygame.draw.rect(screen, WATCH_BLUE, (380, 100, int(335 * (disc / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, d_bar, width=1, border_radius=4)

    w_idx = min(len(RIOT_WAVES) - 1, player.get("riot_wave_idx", 0))
    wave = RIOT_WAVES[w_idx]

    w_box = pygame.Rect(85, 126, 630, 130)
    pygame.draw.rect(screen, (252, 248, 238), w_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, w_box, width=2, border_radius=8)

    screen.blit(font_bold.render(f"{wave['title']} (Wave {w_idx + 1}/4)", True, TATE_RED), (100, 134))
    draw_fitted_text(screen, wave["desc"], pygame.Rect(100, 160, 600, 60), CLOCK_BLACK, bold=False, max_lines=3)

    intel_tags = []
    if player.get("m2b_costumes_found"):
        intel_tags.append("[Playhouse Disguises Found]")
    if player.get("m2b_pump_primed"):
        intel_tags.append("[Canal Sluice-Pump Primed]")
    if player.get("m2b_smugglers_caught"):
        intel_tags.append("[Salt-Cellar Smugglers Caught]")
    intel_str = "Field Intel Prepared: " + (", ".join(intel_tags) if intel_tags else "None gathered yet")
    screen.blit(font.render(intel_str, True, (45, 115, 60) if intel_tags else (120, 90, 70)), (100, 230))

    fb_box = pygame.Rect(85, 264, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("riot_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)

# =========================================================================
# 4. MISSION 2C NPC: SERGEANT WULFGAR OF THE RAGMORE LANCERS (9, 10)
# =========================================================================
def get_wulfgar_options(player):
    opts = ["Ask why Ragmore cavalry are massed on the farm border"]
    if player.get("ch2_mission_step") == 3 and not player.get("m2c_lancers_stood_down"):
        opts.insert(0, "Order Wulfgar to stand down under Municipal Watch jurisdiction")
        if player.get("intel_garrison_mutiny") or player.get("m1c_murum_circular_taken"):
            opts.insert(0, "Warn Wulfgar that Seekgrace's rent-chest is empty & his bounty is a bluff")
    opts.append("Leave")
    return opts


def resolve_wulfgar(choice, player):
    if choice == "Leave":
        return player, "Sergeant Wulfgar rests his mailed gauntlet on his saddle-pommel, eyeing the distant picket brazier.", "MAIN"

    if choice == "Ask why Ragmore cavalry are massed on the farm border":
        return player, (
            "Sergeant Wulfgar—a scar-cheeked cavalryman in Castle Ragmore's black-and-gold surcoat—spits into the carrot-rows.\n"
            "\"Lord Hrothgar wants the grain-roads open, and Bailiff Seekgrace promised my lancers five silver a head if the pitchfork-mob riots. "
            "The moment a single stone or blade flies at that crossroads, Corporal, my horsemen are riding through both the strikers and your Watchmen!\""
        ), "NPC_DIALOGUE"

    if choice.startswith("Warn Wulfgar"):
        player["m2c_lancers_stood_down"] = True
        return player, (
            "You step up to Wulfgar's stirrup and quietly inform him that Bailiff Seekgrace hasn't paid his own local lancers in two fortnights and is drowning in Kokeshi debt.\n"
            "Wulfgar's eyes narrow. \"So the skinflint factor thought he'd use Castle Ragmore's horses for free muscle, did he? "
            "Curse him! Wheel the troop around, lads—we're not dulling our lances for an empty purse!\"\n"
            "The Ragmore cavalry trots away northward, removing the threat of a cavalry charge on your flank!"
        ), "MAIN"

    if choice.startswith("Order Wulfgar to stand down"):
        if player.get("influence", 0) >= 4 or player.get("charisma", 0) >= 5 or player.get("strength", 0) >= 6:
            player["m2c_lancers_stood_down"] = True
            return player, (
                "Citing the Municipal Charter of Murum and Fluvius, you stand firm before Wulfgar's warhorse and warn him that any feudal incursion across the farm boundary will be reported to Mayor Givethanks as a breach of the peace.\n"
                "Grumbling under his breath, Sergeant Wulfgar salutes grudgingly and pulls his lancers back beyond the boundary ditch!"
            ), "MAIN"
        return player, (
            "Wulfgar laughs in your face. \"Takes more than a tin corporal's badge to order Castle Ragmore's horsemen off the field!\" "
            "(Try uncovering proof that the Bailiff's bounty purse is empty, or build higher Influence/Charisma!)"
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 5. MISSION 2C POP-OUT: THE THIN BLUE LINE AT THE STRIKE (MINIGAME_STRIKE_CORDON)
# =========================================================================
CORDON_BEATS = [
    {
        "title": "STANDOFF BEAT 1/4: THE SCAB CONVOY HITS THE BARRICADE!",
        "desc": (
            "Wagon-Boss Corban's three heavy grain-wains grind to a halt inches from the chained hay-wains! "
            "On your left, Organiser Joyinsorrow's farmhands raise ash pitchforks; on your right, Corban's bruisers roll up their sleeves to ram the line!"
        ),
    },
    {
        "title": "STANDOFF BEAT 2/4: THE STAGE-WAGON & THE PLANTED BLADE!",
        "desc": (
            "Fairlight's painted stage-wagon rolls up to the ditch performing a biting satire that sets the crowd roaring—while in the press of bodies, "
            "a hooded Kokeshi provocateur reaches under the orchard hay to pull a notched cleaver and stab a teamster!"
        ),
    },
    {
        "title": "STANDOFF BEAT 3/4: PERIL ON THE FLANKS!",
        "desc": (
            "As tempers flare at the brazier, hoofbeats thunder along the northern ridge where Sergeant Wulfgar's lancers eye the fray, "
            "while dark figures creep up the western sunken lane toward the Bailiff's pay-wagon!"
        ),
    },
    {
        "title": "STANDOFF BEAT 4/4: THE FINAL RULING OF THE ROAD!",
        "desc": (
            "Both the strikers and the Kokeshi teamsters are exhausted, their eyes fixed on your Watch halberdiers. "
            "How do you resolve the passage of the grain wagons before nightfall?"
        ),
    },
]


def init_strike_cordon_minigame(player):
    """Initializes the Mission 2C Thin Blue Line Standoff Pop-Out at the Farm Crossroads."""
    player["cordon_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["cordon_beat"] = 0
    player["cordon_union_tension"] = 55
    player["cordon_kokeshi_tension"] = 55
    player["cordon_integrity"] = 85

    player["cordon_feedback"] = (
        "Your Watch halberdiers form a double cordon between the overturned hay-wains and the Kokeshi grain-wagons! "
        "Keep both Union Tension and Kokeshi Aggression below 100% while preserving your Cordon Integrity!"
    )
    return player, player["cordon_feedback"], "MINIGAME_STRIKE_CORDON"


def strike_cordon_action(action, player):
    """Processes the player's Watch commands across the 4 Standoff Beats in MINIGAME_STRIKE_CORDON."""
    if player.get("cordon_phase") == "RESULT":
        return conclude_strike_cordon_minigame(player)

    beat = player.get("cordon_beat", 0)
    u_ten = player.get("cordon_union_tension", 55)
    k_ten = player.get("cordon_kokeshi_tension", 55)
    integ = player.get("cordon_integrity", 85)
    msg = ""

    # ------------------------------------------------------------------
    # BEAT 1: THE CONVOY HITS THE BARRICADE
    # ------------------------------------------------------------------
    if beat == 0:
        if action == "double_cordon":
            u_ten -= 10
            k_ten -= 10
            integ += 5
            msg = (
                "You plant your halberd butt in the centre of the ruts and order your Watchmen to face outward in two ranks—unspanned horses and ten paces of neutral ground enforced on both sides!"
            )
        elif action == "check_permits":
            k_ten -= 20
            u_ten -= 5
            msg = (
                "You demand Wagon-Boss Corban's customs bills and axle-weight tallies, legally halting the lead wain for an official Watch inspection while tempers cool!"
            )
        elif action == "push_strikers":
            u_ten += 25
            k_ten -= 20
            integ -= 10
            modify_faction(player, "faction_union", -1)
            msg = (
                "You order your men to shove the farmhands back from the hay-wains! Corban grins, but the strikers roar in fury and press against your shields (+25% Union Tension)!"
            )
        else:
            k_ten += 25
            u_ten -= 20
            integ -= 10
            msg = (
                "You lock wheels on Corban's lead wagon! The strikers cheer, but the Kokeshi bruisers surge forward with shoulder-barges (+25% Kokeshi Aggression)!"
            )

    # ------------------------------------------------------------------
    # BEAT 2: THE STAGE-WAGON & THE PLANTED BLADE
    # ------------------------------------------------------------------
    elif beat == 1:
        if action == "disarm_provocateur":
            if player.get("m2c_weapons_confiscated") or player.get("stealth", 0) >= 4:
                u_ten -= 20
                k_ten -= 20
                integ += 10
                msg = (
                    "Because you already confiscated the planted Kokeshi cleavers from the orchard hay, the provocateur grabs nothing but empty straw! "
                    "You haul him out by his collar and expose the Kokeshi frame-up to both sides!"
                )
            else:
                u_ten += 15
                k_ten += 15
                integ -= 25
                player["health"] = max(1, player.get("health", 10) - 2)
                msg = (
                    "A planted meat-cleaver flashes in the crowd! You dive in to knock the blade aside (-2 HP), "
                    "barely stopping a murder, though blood is drawn and the cordon shudders (-25% Cordon Integrity)!"
                )
        elif action == "let_fairlight_play":
            u_ten -= 15
            k_ten -= 5
            if not player.get("m2c_weapons_confiscated"):
                integ -= 15
                msg = (
                    "Fairlight's biting satire has the farmhands and drovers laughing, easing Union Tension—though in the distraction a scuffle breaks out by the orchard fence (-15% Integrity)!"
                )
            else:
                msg = (
                    "With the hidden blades already safely in your evidence bag, Fairlight's theatrical comedy turns the tense crossroads into a laughing crowd, draining the anger from both sides!"
                )
        else:
            u_ten += 15
            k_ten += 10
            integ -= 10
            msg = "You order the stage-wagon cleared by force, uniting both strikers and drovers in loud jeers against the Watch!"

    # ------------------------------------------------------------------
    # BEAT 3: PERIL ON THE FLANKS (LANCERS & OUTLAWS)
    # ------------------------------------------------------------------
    elif beat == 2:
        lancers_ok = player.get("m2c_lancers_stood_down", False)
        outlaws_ok = player.get("m2c_outlaw_ambush_foiled", False)

        if action == "secure_flanks":
            if lancers_ok and outlaws_ok:
                u_ten -= 15
                k_ten -= 15
                integ += 10
                msg = (
                    "Your pre-standoff patrols pay off handsomely! Wulfgar's lancers have already ridden off, and your halberdiers on the Sunken Lane bank rout Black Dog's outlaws before they can touch the pay-wagon!"
                )
            elif lancers_ok or outlaws_ok:
                integ -= 10
                msg = (
                    "One flank holds firm thanks to your earlier scouting, though your reserves have to scramble to repel a sudden raid on the opposite side (-10% Integrity)!"
                )
            else:
                u_ten += 20
                k_ten += 20
                integ -= 30
                msg = (
                    "CHAOS ON BOTH FLANKS! Because you didn't scout the perimeter first, Black Dog's highwaymen hit the pay-wagon in the Sunken Lane while Wulfgar's lancers charge the edge of the field (-30% Integrity)!"
                )
        elif action == "shield_square":
            integ -= 5 if (lancers_ok and outlaws_ok) else 20
            u_ten -= 5
            k_ten -= 5
            msg = "You pull your Watchmen into a tight hollow square around the crossroads brazier to weather the flank commotion."
        else:
            u_ten += 15
            k_ten += 15
            integ -= 20
            msg = "Splitting your cordon blindly in the middle of the standoff leaves the centre gap dangerously thin!"

    # ------------------------------------------------------------------
    # BEAT 4: THE FINAL RULING OF THE ROAD
    # ------------------------------------------------------------------
    elif beat == 3:
        if action == "escort_truce":
            u_ten -= 20
            k_ten -= 20
            modify_faction(player, "faction_guard", 2)
            modify_faction(player, "faction_union", 1)
            msg = (
                "Under Watch arbitration, the Caligo quarrymen's mules are returned unharmed, the unstamped Kokeshi wagons are impounded pending Magistrate Fleepride's audit, "
                "and the strikers peacefully unchain one lane for lawful town provisions!"
            )
        elif action == "clear_for_convoy":
            u_ten += 30
            k_ten -= 30
            modify_faction(player, "faction_union", -2)
            msg = "You force the hay-wains aside at halberd-point and wave the Kokeshi wagons through over the bitter curses of the strikers!"
        else:
            k_ten += 30
            u_ten -= 30
            modify_faction(player, "faction_union", 2)
            modify_faction(player, "faction_wallmakers", -2)
            msg = "You declare the Kokeshi convoy unlawful and order Corban's bruisers marched back to Fluvius in irons while the strikers cheer!"

    swing, prefix, twist_str = roll_guard_2d6_twist(player, context="cordon")
    u_ten -= (swing // 2)
    k_ten -= (swing // 2)
    integ += (swing // 2)
    msg = prefix + msg + twist_str

    player["cordon_union_tension"] = max(0, min(100, u_ten))
    player["cordon_kokeshi_tension"] = max(0, min(100, k_ten))
    player["cordon_integrity"] = max(0, min(100, integ))

    # Check for early collapse or completion of Beat 4
    if player["cordon_integrity"] <= 0 or player["cordon_union_tension"] >= 100 or player["cordon_kokeshi_tension"] >= 100 or beat >= 3:
        player["cordon_phase"] = "RESULT"
        if player["cordon_integrity"] > 25 and player["cordon_union_tension"] < 90 and player["cordon_kokeshi_tension"] < 90:
            tag = "PEACE PRESERVED AT THE CROSSROADS!"
        else:
            tag = "CROSSROADS ERUPTS INTO A MELEE!"
        player["cordon_feedback"] = f"{msg} — [{tag}] Click [Conclude Crossroads Deployment >>]!"
        return player, player["cordon_feedback"], "MINIGAME_STRIKE_CORDON"

    player["cordon_beat"] = beat + 1
    player["cordon_feedback"] = msg
    return player, None, "MINIGAME_STRIKE_CORDON"


def conclude_strike_cordon_minigame(player):
    player["ch2_mission_step"] = 4
    player["active_ch2_mission"] = None

    # Clean up temporary NPCs
    db.npc_database["wulfgar"]["location"] = None
    db.npc_database["aelfwine"]["location"] = (9, 3)

    integ = player.get("cordon_integrity", 0)
    u_ten = player.get("cordon_union_tension", 0)
    k_ten = player.get("cordon_kokeshi_tension", 0)

    prep_cnt = sum([
        1 if player.get("m2c_weapons_confiscated") else 0,
        1 if player.get("m2c_lancers_stood_down") else 0,
        1 if player.get("m2c_outlaw_ambush_foiled") else 0,
    ])

    if integ > 25 and u_ten < 90 and k_ten < 90:
        gain = 20 + (prep_cnt * 4)
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["reputation"] = player.get("reputation", 0) + 2
        modify_faction(player, "faction_guard", 2)
        log = (
            f"=== MISSION COMPLETE: THE THIN BLUE LINE HOLDS (+{gain}% Position Strength, +2 Reputation, +2 Guard Faction)! ===\n"
            "Through steady nerve and thorough perimeter scouting, your Watch detachment prevents a bloodbath at the Fluvius Crossroads, "
            "foiling both the planted Kokeshi blades and the flanking raids!\n\n"
            "*** Next Mission: Report to Lieutenant Beornraed—Mayor Givethanks requires an armed Watch escort up the New Road to Castle Ragmore for an emergency summit with Castellan Hrothgar! ***"
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 5)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: BLOODY SKIRMISH AT THE CROSSROADS (+5% Position Strength, +1 Exposure Tell) ===\n"
            "The cordon buckled under the pressure of the standoff, leaving overturned wagons and wounded men across the ruts before order could be restored.\n\n"
            "*** Next Mission: Report to Lieutenant Beornraed to escort Mayor Givethanks' carriage up the New Road to Castle Ragmore! ***"
        )

    return player, log, "MAIN"


def draw_strike_cordon_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 2C (The Thin Blue Line)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    WATCH_BLUE = (45, 85, 155)
    AMBER_GOLD = (195, 130, 35)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("FLUVIUS FARM CROSSROADS — THE THIN BLUE LINE", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    # Three Compact Gauges: Union Tension | Kokeshi Aggression | Watch Cordon Integrity
    u_ten = player.get("cordon_union_tension", 55)
    k_ten = player.get("cordon_kokeshi_tension", 55)
    integ = player.get("cordon_integrity", 85)

    gauges = [
        ("Union Striker Fury:", f"{u_ten}%", u_ten, TATE_RED, 74),
        ("Kokeshi Convoy Aggression:", f"{k_ten}%", k_ten, AMBER_GOLD, 94),
        ("Watch Cordon Integrity:", f"{integ}%", integ, WATCH_BLUE, 114),
    ]
    for lbl, val_s, pct, col, gy in gauges:
        screen.blit(font_bold.render(f"{lbl} {val_s}", True, col), (85, gy))
        bar = pygame.Rect(380, gy + 2, 335, 14)
        pygame.draw.rect(screen, (40, 35, 35), bar, border_radius=4)
        if pct > 0:
            pygame.draw.rect(screen, col, (380, gy + 2, int(335 * (pct / 100.0)), 14), border_radius=4)
        pygame.draw.rect(screen, CLOCK_BLACK, bar, width=1, border_radius=4)

    # Current Standoff Beat Box
    beat_idx = min(3, player.get("cordon_beat", 0))
    b_data = CORDON_BEATS[beat_idx]

    b_box = pygame.Rect(85, 136, 630, 122)
    pygame.draw.rect(screen, (252, 248, 238), b_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, b_box, width=2, border_radius=8)

    screen.blit(font_bold.render(b_data["title"], True, TATE_RED), (100, 144))
    draw_fitted_text(screen, b_data["desc"], pygame.Rect(100, 168, 600, 58), CLOCK_BLACK, bold=False, max_lines=3)

    # Perimeter Scouting Status Strip
    prep_tags = []
    if player.get("m2c_weapons_confiscated"):
        prep_tags.append("[Orchard Blades Confiscated]")
    if player.get("m2c_lancers_stood_down"):
        prep_tags.append("[Ragmore Lancers Stood Down]")
    if player.get("m2c_outlaw_ambush_foiled"):
        prep_tags.append("[Sunken Lane Outlaws Foiled]")
    prep_str = "Perimeter Security: " + (", ".join(prep_tags) if prep_tags else "Unscouted (High risk of ambushes & planted weapons!)")
    screen.blit(font.render(prep_str, True, (45, 115, 60) if prep_tags else TATE_RED), (100, 234))

    # Transcript / Outcome Box
    fb_box = pygame.Rect(85, 266, 630, 58)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("cordon_feedback", ""), fb_box.inflate(-14, -6), (245, 240, 230), max_lines=2)

# =========================================================================
# 6. MISSION 2D & 2E NPCS: COACHMAN  (7, 15) & QUARTERMASTER CENRIC (6, 21)
# =========================================================================
def get_odhran_options(player):
    opts = ["Ask about the Mayor's carriage team"]
    if player.get("ch2_mission_step") == 4:
        opts.insert(0, "Ask if anyone lingered near the state coach last night")
    opts.append("Leave")
    return opts


def resolve_odhran(choice, player):
    if choice == "Leave":
        return player, "Coachman Odhran checks the leather harnesses on the Mayor's greys.", "MAIN"

    if choice == "Ask about the Mayor's carriage team":
        return player, (
            "Coachman Odhran pats the neck of the lead grey gelding.\n"
            "\"Fastest pair in Murum, Watchman—so long as the trace-chains hold through the deep ruts on the New Road.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask if anyone lingered near the state coach last night":
        player["m2d_odhran_questioned"] = True
        return player, (
            "Odhran lowers his curry-comb and glances toward the Town Gate.\n"
            "\"Just before dawn, I heard a metallic rasping under the coach-wheels outside the stables.\n"
            "\"A fellow in a muddy highwayman's cloak bolted over the fence before I could loose the dogs!\n"
            "\"You'd best inspect the coach undercarriage here outside the stables before we roll — and keep a sharp eye on the **Muddy Hollow north of the Frontier Watchpost;\n"
            "\"that's where Black Dog's gang always fells timber across the road!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_cenric_options(player):
    opts = ["Ask about traffic at the Frontier Watchpost"]
    step = player.get("ch2_mission_step", 1)
    if step == 4:
        opts.insert(0, "Inspect the banquet wine crate delivered for the Ragmore Summit")
    elif step == 5:
        opts.insert(0, "Ask why half the Frontier Watchpost is murmuring of mutiny")
        if player.get("m2e_started"):
            opts.insert(0, "Mission: Sound the Assembly Horn & Convene the Watch Council!")
    opts.append("Leave")
    return opts


def resolve_cenric(choice, player):
    if choice == "Leave":
        return player, "Quartermaster Cenric tallies crossbow bolts beside the Watchpost brazier.", "MAIN"

    if choice == "Ask about traffic at the Frontier Watchpost":
        return player, (
            "\"Outlaws in the gorse, Ragmore lancers on the plains, and Laydere scouts in the woods,\" Cenric mutters. "
            "\"We sit right on the anvil between two hammers.\""
        ), "NPC_DIALOGUE"

    if choice == "Inspect the banquet wine crate delivered for the Ragmore Summit":
        if player.get("m2d_poison_found"):
            return player, "\"That poisoned flagon is already locked in the guardroom chest, Corporal.\"", "NPC_DIALOGUE"
        player["m2d_poison_found"] = True
        return player, (
            "Quartermaster Cenric pries open the straw-packed crate left by a 'vintner's boy' for Mayor Givethanks to present to Castellan Hrothgar.\n"
            "Uncorking the lead flagon, a sharp whiff of **bitter almonds** rises from the dark vintage—and the wax seal on the bottom bears the red-stone mark of **Castle Laydere**!\n"
            "\"God's teeth!\" Cenric gasps. \"A Laydere poisoner meant for the Mayor to unknowingly poison Lord Hrothgar at the summit table! We'll swap this flagon for wholesome Murum cider at once!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask why half the Frontier Watchpost is murmuring of mutiny":
        player["m2e_cenric_questioned"] = True
        return player, (
            "Quartermaster Cenric leans over the palisade rail, speaking barely above a whisper.\n"
            "\"War has broken out between **Castle Ragmore** and **Castle Laydere**, Corporal. An envoy from Castellan Eormenhild of Laydere rode up in the night offering the Watch double pay and municipal self-rule if we open the frontier to her army.\"\n\n"
            "\"Meanwhile, **Sergeant Wulfgar's** old-guard loyalists want us to swear feudal fealty to **Castellan Hrothgar**, and **Constable Ælfwine's** rank-and-file down by the gate just want to know which side won't starve Murum! "
            "Speak to the men if you must—then sound the assembly horn here to unite the garrison and declare our banner!\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Sound the Assembly Horn & Convene the Watch Council!":
        player, t_msg = execute_ch2_mission(player, "2e_split", time_cost=90, stamina_drain=15)
        player, log, next_state = init_watch_split_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    return player, "Error.", "MAIN"


# =========================================================================
# 7. MISSION 2D POP-OUT: ESCORTING THE MAYOR'S CONVOY (MINIGAME_CONVOY)
#    (Includes 2d6 Contested Rolls + Random Road Windfalls & Complications!)
# =========================================================================
CONVOY_STAGES = [
    {
        "title": "STAGE 1/3: THE LOWER HIGHWAY & THE DEEP RUTS",
        "desc": (
            "Mayor Givethanks' iron-banded coach rumbles north from Murum Gate onto the cobbled New Road! "
            "Ahead, the road dips into waterlogged ruts while whistles echo faintly from the roadside gorse."
        ),
    },
    {
        "title": "STAGE 2/3: BLACK DOG'S AMBUSH AT THE MUDDY HOLLOW!",
        "desc": (
            "At the narrowest bend of the Muddy Hollow, Black Dog's highwaymen rise from the bracken with crossbows levelled, "
            "straining on haul-ropes to drop a sawn pine tree across the Mayor's horses!"
        ),
    },
    {
        "title": "STAGE 3/3: THE RAGMORE BARBICAN & THE SUMMIT BANQUET!",
        "desc": (
            "The coach clatters through the barbican of Castle Ragmore! Inside the Great Hall, Castellan Hrothgar raises the ceremonial goblet "
            "as a nervous server pours the summit wine!"
        ),
    },
]

ROAD_TWISTS = [
    ("WINDFALL", "A passing timber-carter warns you of a fresh rut ahead and lends a spare trace-strap! (+10% Coach Integrity)", 10, 0),
    ("WINDFALL", "A sudden sea-fog rolls in from the coast,spoiling the highwaymen's crossbow aim! (+12% Tactical Advantage)", 0, 12),
    ("WINDFALL", "Your lead outrider spots an abandoned outlaw saddlebag in the ditch containing 10 silver! (+10s Windfall)", 0, 5),
    ("FRICTION", "A sudden Brumaire hail-squall lashes the road, spooking the carriage greys! (-10% Coach Integrity)", -10, 0),
    ("FRICTION", "A stray outlaw caltrop punctures a lead horse's frog before your farrier pulls it free! (-8% Tactical Advantage)", -5, -8),
]


def init_convoy_minigame(player):
    """Initializes the Mission 2D Diplomatic Escort Pop-Out Window."""
    player["convoy_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["convoy_stage"] = 0
    player["convoy_integrity"] = 85 + (10 if player.get("m2d_coach_repaired") else 0)
    player["convoy_integrity"] = min(100, player["convoy_integrity"])
    player["convoy_advantage"] = 40 + (15 if player.get("m2d_hollow_scouted") else 0) + (10 if player.get("m2d_poison_found") else 0)
    player["convoy_last_roll_str"] = "Roll: Ready"
    player["convoy_twist_str"] = ""

    player["convoy_feedback"] = (
        "The oak gates of Murum swing wide! Guide Mayor Givethanks' carriage through 3 stages to Castle Ragmore. "
        "Each command rolls 2d6 + your Watch stats/preparation—and watch out for unpredictable road twists!"
    )
    return player, player["convoy_feedback"], "MINIGAME_CONVOY"


def convoy_action(action, player):
    """Processes 2d6 contested rolls and random road twists across the 3 stages of Mission 2D."""
    if player.get("convoy_phase") == "RESULT":
        return conclude_convoy_minigame(player)

    stage = player.get("convoy_stage", 0)
    integ = player.get("convoy_integrity", 85)
    adv = player.get("convoy_advantage", 40)

    # 1. Roll 2d6 + Stat/Prep Bonus!
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    base_roll = d1 + d2
    stat_mod = max(player.get("strength", 0), player.get("stealth", 0), player.get("equusense", 0)) // 3
    prep_mod = (
        (2 if player.get("m2d_coach_repaired") and stage == 0 else 0)
        + (3 if player.get("m2d_hollow_scouted") and stage == 1 else 0)
        + (3 if player.get("m2d_poison_found") and stage == 2 else 0)
    )
    total_roll = base_roll + stat_mod + prep_mod
    player["convoy_last_roll_str"] = f"Dice Roll: [{d1}]+[{d2}] + {stat_mod + prep_mod} Bonus = {total_roll}"

    msg = ""

    # ------------------------------------------------------------------
    # STAGE 1: THE LOWER HIGHWAY & SABOTAGED TRACES
    # ------------------------------------------------------------------
    if stage == 0:
        if action == "steady_screen":
            if not player.get("m2d_coach_repaired") and base_roll <= 6:
                integ -= 25
                msg = f"[{total_roll}] SNAP! Because you never inspected the coach at the stables, the sabotaged left trace-chain shears in the ruts (-25% Coach Integrity)!"
            elif total_roll >= 9:
                adv += 15
                integ += 5
                msg = f"[{total_roll}] Your halberd screen marches in lockstep; the reinforced trace-chain holds fast through the deep ruts (+15% Advantage)!"
            else:
                adv += 5
                integ -= 5
                msg = f"[{total_roll}] The carriage jolts heavily through the mire, splashing your vanguard, but holds the road."

        elif action == "outrider_sweep":
            if total_roll >= 8:
                adv += 25
                msg = f"[{total_roll}] Your flanking outriders flush two of Black Dog's whistle-lookouts from the gorse before they can signal the hollow (+25% Advantage)!"
            else:
                integ -= 12
                msg = f"[{total_roll}] Your outriders get bogged down in the wet bracken, leaving the coach briefly exposed to sling-stones (-12% Integrity)!"

    # ------------------------------------------------------------------
    # STAGE 2: BLACK DOG'S AMBUSH AT THE MUDDY HOLLOW (LINKED TO 9D)
    # ------------------------------------------------------------------
    elif stage == 1:
        if action == "counter_ambush":
            if player.get("m2d_hollow_scouted") or total_roll >= 10:
                adv += 30
                player["silver"] += 15
                msg = (
                    f"[{total_roll}] DECISIVE OUTFLANK! With the pine-tree haul-ropes already severed, your Watchmen storm the high bank from behind, "
                    "routing Black Dog's highwaymen and seizing a **15-silver** outlaw bounty pouch! (+30% Advantage, +15s)"
                )
            elif total_roll >= 7:
                adv += 10
                integ -= 15
                msg = f"[{total_roll}] The sawn pine crashes onto the road, but your squad charges into the gorse and drives the highwaymen back in fierce hand-to-hand fighting (-15% Integrity)!"
            else:
                integ -= 30
                player["health"] = max(1, player.get("health", 10) - 2)
                msg = f"[{total_roll}] AMBUSHED! The pine tree crashes down in front of the greys and crossbow bolts rake the coach (-30% Integrity, -2 HP)!"

        elif action == "shield_tortoise":
            if total_roll >= 8:
                integ -= 5
                adv += 15
                msg = f"[{total_roll}] Your Watchmen lock shields over the coach windows as Coachman Odhran lashes the team around the fallen timber (+15% Advantage)!"
            else:
                integ -= 20
                msg = f"[{total_roll}] Heavy crossbow quarrels splinter the coach panels as you haul the tree clear under fire (-20% Integrity)!"

    # ------------------------------------------------------------------
    # STAGE 3: THE RAGMORE SUMMIT & THE POISONED TOAST (LINKED TO 3D)
    # ------------------------------------------------------------------
    elif stage == 2:
        if action == "foil_poison":
            if player.get("m2d_poison_found") or total_roll >= 9:
                adv += 25
                integ += 10
                msg = (
                    f"[{total_roll}] You step forward beside Lord Hrothgar's high table and expose the Laydere poison plot—presenting the safe flagon you swapped at the Watchpost! "
                    "Both Hrothgar and Mayor Givethanks salute your vigilance!"
                )
            else:
                integ -= 25
                adv -= 15
                msg = (
                    f"[{total_roll}] You knock the goblet from the table on a hunch, spilling wine across Hrothgar's furs—without the Watchpost proof, the Castellan is furious at the breach of protocol (-25% Integrity)!"
                )
        elif action == "stand_guard":
            if player.get("m2d_poison_found"):
                adv += 20
                msg = f"[{total_roll}] Because you already swapped the poisoned flagon at the Watchpost, the banquet toast proceeds in warm harmony (+20% Advantage)!"
            else:
                integ -= 35
                msg = (
                    f"[{total_roll}] DISASTER AT THE HIGH TABLE! Because you never checked the wine crate at the Watchpost, Castellan Hrothgar's taster collapses foaming at the mouth! "
                    "Swords are drawn across the hall (-35% Integrity)!"
                )

    # 2. Roll a 40% Chance for an Unpredictable Road Twist (Windfall or Friction) on Stages 0 and 1!
    twist_note = ""
    if stage < 2 and random.random() < 0.45:
        kind, t_text, d_int, d_adv = random.choice(ROAD_TWISTS)
        integ += d_int
        adv += d_adv
        if "10 silver" in t_text:
            player["silver"] += 10
        player["convoy_twist_str"] = f"[{kind}]: {t_text}"
        twist_note = f" | {t_text}"
    else:
        player["convoy_twist_str"] = ""

    player["convoy_integrity"] = max(0, min(100, integ))
    player["convoy_advantage"] = max(0, min(100, adv))

    if player["convoy_integrity"] <= 0 or stage >= 2:
        player["convoy_phase"] = "RESULT"
        status = "CONVOY MISSION ACCOMPLISHED!" if player["convoy_integrity"] >= 40 else "CONVOY BATTERED!"
        player["convoy_feedback"] = f"{msg}{twist_note} — [{status}] Click [Conclude Ragmore Escort >>]!"
        return player, player["convoy_feedback"], "MINIGAME_CONVOY"

    player["convoy_stage"] = stage + 1
    player["convoy_feedback"] = msg + twist_note
    return player, None, "MINIGAME_CONVOY"


def conclude_convoy_minigame(player):
    player["ch2_mission_step"] = 5
    player["active_ch2_mission"] = None
    player["m2e_started"] = True

    # Position NPCs at/near the Frontier Watchpost for the Mission 2E Finale!
    db.npc_database["beornraed"]["location"] = (6, 21)
    db.npc_database["cenric"]["location"] = (6, 21)
    db.npc_database["aelfwine"]["location"] = (7, 16)
    db.npc_database["wulfgar"]["location"] = (5, 21)

    integ = player.get("convoy_integrity", 0)
    adv = player.get("convoy_advantage", 0)

    if integ >= 40 and adv >= 60:
        gain = 22 + (5 if player.get("m2d_poison_found") else 0)
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["stealth"] = player.get("stealth", 0) + 1
        player["reputation"] = player.get("reputation", 0) + 2
        log = (
            f"=== MISSION COMPLETE: TRIUMPH ON THE NEW ROAD (+{gain}% Position Strength, +1 Stealth, +2 Reputation)! ===\n"
            "You outflanked Black Dog's highwaymen at the Muddy Hollow, delivered the Mayor's tribute chest intact, and saved the Ragmore summit from assassination!\n\n"
            "=== FINAL MISSION: THE WATCH SPLITS ON THE EVE OF WAR ===\n"
            "As you ride back down to the **Frontier Watchpost**, war-horns echo from both **Castle Ragmore** and **Castle Laydere**!\n"
            "The Town Watch is threatening to tear itself in two between Loyalist and Rebel camps. "
            "Speak to **Quartermaster Cenric** and **Lieutenant Beornraed** at the **Frontier Watchpost** (and check on **Constable Ælfwine** at Murum Gate or **Sergeant Wulfgar** on the plains) before sounding the horn to unite the garrison and declare your banner!"
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 8)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: A COSTLY ESCORT (+8% Position Strength, +1 Exposure Tell) ===\n"
            "Mayor Givethanks reaches Castle Ragmore alive, though the splintered coach and summit chaos leave the Watch's prestige shaken.\n\n"
            "=== FINAL MISSION: THE WATCH SPLITS ===\n"
            "Travel to the **Frontier Watchpost** on the New Road and speak to **Quartermaster Cenric** or **Lieutenant Beornraed** to face the final mutiny crisis!"
        )

    return player, log, "MAIN"


def draw_convoy_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 2D (Convoy Escort)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    WATCH_BLUE = (45, 85, 155)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("THE NEW ROAD — MAYORAL CONVOY ESCORT TO CASTLE RAGMORE", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    integ = player.get("convoy_integrity", 85)
    adv = player.get("convoy_advantage", 40)

    screen.blit(font_bold.render(f"Coach & Team Integrity: {integ}%", True, TATE_RED), (85, 76))
    i_bar = pygame.Rect(370, 76, 345, 15)
    pygame.draw.rect(screen, (40, 35, 35), i_bar, border_radius=4)
    if integ > 0:
        pygame.draw.rect(screen, TATE_RED, (370, 76, int(345 * (integ / 100.0)), 15), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, i_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Outflank & Tactical Advantage: {adv}%", True, WATCH_BLUE), (85, 96))
    a_bar = pygame.Rect(370, 96, 345, 15)
    pygame.draw.rect(screen, (40, 35, 35), a_bar, border_radius=4)
    if adv > 0:
        pygame.draw.rect(screen, WATCH_BLUE, (370, 96, int(345 * (adv / 100.0)), 15), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, a_bar, width=1, border_radius=4)

    # Dice Roll & Road Twist Banner
    roll_s = player.get("convoy_last_roll_str", "")
    twist_s = player.get("convoy_twist_str", "")
    screen.blit(font_bold.render(roll_s, True, CLOCK_BLACK), (85, 118))
    if twist_s:
        t_col = (40, 120, 55) if "WINDFALL" in twist_s else TATE_RED
        screen.blit(font_bold.render(twist_s[:48], True, t_col), (350, 118))

    st_idx = min(2, player.get("convoy_stage", 0))
    st_data = CONVOY_STAGES[st_idx]

    s_box = pygame.Rect(85, 140, 630, 125)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 148))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 172, 600, 58), CLOCK_BLACK, bold=False, max_lines=3)

    prep_tags = []
    if player.get("m2d_coach_repaired"):
        prep_tags.append("[Trace-Chain Reinforced]")
    if player.get("m2d_hollow_scouted"):
        prep_tags.append("[Hollow Tree-Trap Cut]")
    if player.get("m2d_poison_found"):
        prep_tags.append("[Poisoned Wine Swapped]")
    p_str = "Convoy Pre-Checks: " + (", ".join(prep_tags) if prep_tags else "None (Rolling without preparation bonuses!)")
    screen.blit(font.render(p_str, True, (40, 115, 55) if prep_tags else TATE_RED), (100, 240))

    fb_box = pygame.Rect(85, 272, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("convoy_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 8. MISSION 2E POP-OUT: THE WATCH SPLITS (MINIGAME_WATCH_SPLIT)
# =========================================================================
def init_watch_split_minigame(player):
    """Initializes the Mission 2E Garrison Unity & Allegiance Pop-Out at the Frontier Watchpost."""
    player["split_phase"] = "UNITY"  # "UNITY" -> "ALLEGIANCE"
    base_unity = 40 + (player.get("charisma", 0) * 3) + (player.get("influence", 0) * 3)
    if player.get("m2b_smugglers_caught"):
        base_unity += 10
    if player.get("m2c_weapons_confiscated"):
        base_unity += 10
    if player.get("m2d_poison_found"):
        base_unity += 10
    player["split_unity"] = min(90, base_unity)
    player["split_addressed"] = []
    player["split_last_roll"] = "Roll: Ready"
    player["split_feedback"] = (
        "Torchlight glints off a hundred halberds around the Frontier Watchpost! "
        "Before declaring for Castle Ragmore or Castle Laydere, rally the 3 Watch factions to 70%+ Garrison Unity so the Watch marches as one!"
    )
    return player, player["split_feedback"], "MINIGAME_WATCH_SPLIT"


def watch_split_action(action, player):
    """Handles 2d6 persuasion rolls to unite the Watch factions, then locks in Ragmore vs Laydere."""
    phase = player.get("split_phase", "UNITY")

    if phase == "UNITY":
        addressed = player.setdefault("split_addressed", [])
        if action in addressed:
            player["split_feedback"] = "You have already addressed that contingent of the Watch!"
            return player, None, "MINIGAME_WATCH_SPLIT"

        if action == "proceed_banner":
            player["split_phase"] = "ALLEGIANCE"
            player["split_feedback"] = (
                f"With Garrison Unity at {player['split_unity']}%, the drums fall silent. "
                "Which banner will you raise above the Frontier Watchpost for Chapter 3?"
            )
            return player, None, "MINIGAME_WATCH_SPLIT"

        addressed.append(action)
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        bonus = (player.get("charisma", 0) + player.get("strength", 0) + player.get("influence", 0)) // 4
        tot = d1 + d2 + bonus
        player["split_last_roll"] = f"Unity Roll: [{d1}]+[{d2}] + {bonus} = {tot}"

        gain = 18 if tot >= 9 else (10 if tot >= 6 else -5)
        player["split_unity"] = max(10, min(100, player.get("split_unity", 50) + gain))

        if action == "rally_rank":
            msg = (
                f"[{tot}] You remind Constable Ælfwine's rank-and-file how you held the shield-wall in Fluvius without slaughtering the townsfolk! "
                f"({'The Watchmen bang their shields in unanimous loyalty!' if gain > 0 else 'A few exhausted Watchmen mutter doubtfully.'})"
            )
        elif action == "rally_quartermaster":
            msg = (
                f"[{tot}] You open the seized Kokeshi & outlaw bounty chest to guarantee every Watchman's family rations through the winter campaign! "
                f"({'Quartermaster Cenric pledges the armoury keys to your command!' if gain > 0 else 'Cenric worries the silver will run dry.'})"
            )
        else:
            msg = (
                f"[{tot}] You step before the veteran halberdiers and swear that whoever the Watch marches with, you will lead from the front rank! "
                f"({'Lieutenant Beornraed salutes your iron resolve!' if gain > 0 else 'Some old-guard veterans hesitate.'})"
            )

        if len(addressed) >= 3:
            player["split_phase"] = "ALLEGIANCE"
            msg += f" — [All 3 Contingents Addressed | Final Garrison Unity: {player['split_unity']}%! Now declare your allegiance!]"

        player["split_feedback"] = msg
        return player, None, "MINIGAME_WATCH_SPLIT"

    # PHASE 2: DECLARE ALLEGIANCE (RAGMORE LOYALIST VS. LAYDERE REBEL)
    elif phase == "ALLEGIANCE":
        is_ragmore = (action == "declare_ragmore")
        player["ch2_mission_step"] = 6
        player["active_ch2_mission"] = None
        player.setdefault("ch3_world_bits", {})["track_2"] = 1 if is_ragmore else 0

        unity = player.get("split_unity", 50)
        if unity >= 70:
            player["position_strength"] = min(100, player.get("position_strength", 0) + 25 + (player.get("strength", 0) * 2))
            player["reputation"] = player.get("reputation", 0) + 3
            unity_banner = (
                "With 100% of the garrison united behind you, not a single Watchman deserts the palisade!"
            )
        else:
            player["position_strength"] = max(0, player.get("position_strength", 0) + 5)
            player["exposure_tells"] = player.get("exposure_tells", 0) + 2
            unity_banner = (
                "Because Garrison Unity was below 70%, a bitter faction of dissenters deserts into the night (+2 Exposure Tells)!"
            )

        castle_name = "Castle Ragmore (Loyalist)" if is_ragmore else "Castle Laydere (Rebel)"
        log = (
            "=========================================================\n"
            f"   MISSION COMPLETE: THE WATCH DECLARES FOR {castle_name.upper()}!   \n"
            "=========================================================\n"
            f"You lock down the Frontier Watchpost toll-bar, run up the banner of **{castle_name}**, and order the crossbowmen to the palisade!\n"
            f"{unity_banner}\n\n"
            f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
        )
        return player, log, "CHAPTER_2_COMPLETE"

    return player, None, "MINIGAME_WATCH_SPLIT"


def draw_watch_split_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for the Mission 2E Finale."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    WATCH_BLUE = (45, 85, 155)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("FRONTIER WATCHPOST — THE EVE OF WAR GARRISON COUNCIL", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 52))

    unity = player.get("split_unity", 50)
    screen.blit(font_bold.render(f"Garrison Unity: {unity}% (Need 70%+ to prevent desertions!)", True, WATCH_BLUE), (85, 80))
    u_bar = pygame.Rect(85, 102, 630, 20)
    pygame.draw.rect(screen, (40, 35, 35), u_bar, border_radius=5)
    if unity > 0:
        pygame.draw.rect(screen, (45, 135, 65) if unity >= 70 else WATCH_BLUE, (85, 102, int(630 * (unity / 100.0)), 20), border_radius=5)
    tx = 85 + int(630 * 0.70)
    pygame.draw.line(screen, (255, 255, 255), (tx, 100), (tx, 124), 3)
    pygame.draw.rect(screen, CLOCK_BLACK, u_bar, width=1, border_radius=5)

    screen.blit(font_bold.render(player.get("split_last_roll", ""), True, TATE_RED), (85, 130))

    c_box = pygame.Rect(85, 154, 630, 118)
    pygame.draw.rect(screen, (252, 248, 238), c_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, c_box, width=2, border_radius=8)

    if player.get("split_phase") == "UNITY":
        desc = (
            "Three contingents of the Watch stand around the brazier awaiting your word:\n"
            "• Constable Ælfwine's Municipal Rank-and-File (Concerned for Murum's citizens)\n"
            "• Quartermaster Cenric's Frontier Garrison (Tempered by Laydere's offer of self-rule & pay)\n"
            "• Lieutenant Beornraed's Veteran Halberdiers (Bound by oath and martial honour)"
        )
    else:
        desc = (
            "THE HORN SOUNDS ACROSS THE NORTHERN FRONTIER!\n"
            "Will you lock shields with Lord Hrothgar of Castle Ragmore (Loyalist), "
            "or swing the Frontier Watchpost open for Castellan Eormenhild of Castle Laydere (Rebel)?"
        )
    draw_fitted_text(screen, desc, c_box.inflate(-16, -12), CLOCK_BLACK, max_lines=4)

    fb_box = pygame.Rect(85, 280, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("split_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)

# =========================================================================
# MODULE REGISTRATION (HANDLERS)
# =========================================================================
HANDLERS = {
    "aelfwine": (get_aelfwine_options, resolve_aelfwine),
    "hopewell": (get_hopewell_options, resolve_hopewell),
    "mairead":  (get_mairead_options, resolve_mairead),
    "wulfgar":  (get_wulfgar_options, resolve_wulfgar),
    "odhran":   (get_odhran_options, resolve_odhran),
    "cenric":   (get_cenric_options, resolve_cenric),
}
