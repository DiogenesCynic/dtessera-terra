"""
chapter_2.py
------------
Chapter 2 regional missions (Tracks 1 to 10), field representatives,
Bandoka's double-agent storyline, Master Spotted Tail's mountain trial,
and the 20 Wilderness Trials across Dtessera Terra.
"""

import random
import game_data as db
import encounters
import mini_games
import ch2_union
import ch2_guard
import ch2_castellan
import ch2_parvus
import ch2_election
import ch2_roguery
import meta_progression
import ch3_war_engine
import ch2_easter_eggs
from mechanics import (
    advance_time,
    modify_faction,
    infect_player,
    set_region_territory,
    consume_fresh_food_timestamp,
    get_inventory_weight,
    format_item_name,
    execute_ch2_mission,
)

# =========================================================================
# 1. BANDOKA, MASTER SPOTTED TAIL & THE 5 FACTION REPRESENTATIVES (DIALOGUE)
# =========================================================================
def get_bandoka_options(player):
    if player.get("bandoka_joined"):
        clues = player.get("bandoka_clues_spotted", [])
        opts = [
            "Ask Bandoka about their background",
            "Watch Bandoka's habits by the roadside",
        ]
        # Only unlock the confrontation once the player has spotted at least 2 clues!
        if len(clues) >= 2:
            opts.insert(0, "Question Bandoka's story about leaving Murum (Examine discrepancies...)")
        opts.extend(["Part ways for now", "Leave"])
        return opts
    return [
        "Accept Bandoka's offer to travel together",
        "Ask why they are leaving Murum",
        "Decline — I travel alone",
        "Leave"
    ]


def resolve_bandoka(choice, player):
    if choice in ["Leave", "Decline — I travel alone"]:
        return player, "Bandoka adjusts their heavy travel cloak with an easy smile. \"Suit yourself, friend. I'll be resting by the milestone if you change your mind.\"", "MAIN"

    if choice == "Ask why they are leaving Murum":
        log = (
            "Bandoka leans on a stout ash walking-staff and glances back at Murum's oak gates.\n"
            "\"Me? Just a humble wool-factor's clerk heading out to check on the regional warehouses. "
            "Though I was delayed at the Town Gate until 8:00 last night sorting out my customs papers!\""
        )
        player.setdefault("bandoka_clues_spotted", [])
        if "curfew_lie" not in player["bandoka_clues_spotted"]:
            player["bandoka_clues_spotted"].append("curfew_lie")
        return player, log, "NPC_DIALOGUE"

    if choice == "Accept Bandoka's offer to travel together":
        player["bandoka_joined"] = True
        db.npc_database["bandoka"]["location"] = (player["x"], player["y"])
        log = (
            "Bandoka claps you on the shoulder with genuine relief.\n"
            "\"Two pairs of eyes are better than one on these roads! Lead the way, Noburu—whenever we camp or hit a crossroads, we'll watch each other's backs.\"\n\n"
            "*** Bandoka the Fellow Traveller has joined your journey! (Use 'Action -> Talk' at any stop to question them.) ***"
        )
        return player, log, "MAIN"

    if choice == "Ask Bandoka about their background":
        log = (
            "\"Born and raised by the docks of Parvus,\" Bandoka says breezily, tightening their boot-straps.\n"
            "\"Never could stomach the sea, though—give me dry cobbles any day.\"\n"
            "You look down and see that their boots are caked in yellow mountain clay from the Caligo foothills rather than coastal sand"
        )
        player.setdefault("bandoka_clues_spotted", [])
        if "clay_boots" not in player["bandoka_clues_spotted"]:
            player["bandoka_clues_spotted"].append("clay_boots")
        return player, log, "NPC_DIALOGUE"

    if choice == "Watch Bandoka's habits by the roadside":
        log = (
            "While you pause to check your pack, you catch Bandoka sketching your route milestones in shorthand on a strip of oiled vellum—and their walking-staff is weighted with lead like a sapper's cosh!\n"
        )
        player.setdefault("bandoka_clues_spotted", [])
        if "cipher_sketch" not in player["bandoka_clues_spotted"]:
            player["bandoka_clues_spotted"].append("cipher_sketch")
        return player, log, "NPC_DIALOGUE"

    if choice.startswith("Question Bandoka's story") or choice.startswith("Confront Bandoka"):
        player["active_ch2_trial"] = "trial_9_bandoka"
        log = (
            "*** TRIAL: UNMASKING THE DOUBLE AGENT! ***\n\n"
            "You step directly into Bandoka's path, resting your hand on your weapon.\n"
            "Bandoka's genial smile freezes. \"What's the matter, Noburu? You're looking at me as if I'm a highwayman!\"\n"
            "How do you expose Bandoka's cover?"
        )
        return player, log, "CH2_TRIAL"

    if choice == "Part ways for now":
        player["bandoka_joined"] = False
        db.npc_database["bandoka"]["location"] = (player["x"], player["y"])
        return player, "Bandoka nods. \"I'll make camp here for a spell. Catch up with me if you need company!\"", "MAIN"

    return player, "Conversation ended.", "MAIN"


def get_mountain_sage_options(player):
    completed = player.get("ch2_trials_done", [])
    opts = []
    if "trial_12_sage" not in completed:
        opts.append("Seek the Wisdom of the Mountain Sage (Begin Trial)")
    else:
        opts.append("Share a cup of mountain herbal tea (+Full HP/Hunger/Thirst)")
    opts.append("Ask about the Castellans & the Gathering Storm")
    opts.append("Leave")
    return opts


def resolve_mountain_sage(choice, player):
    if choice == "Leave":
        return player, "Master Spotted Tail bows slightly and returns to gazing through the brass armillary sphere.", "MAIN"

    if choice == "Seek the Wisdom of the Mountain Sage (Begin Trial)":
        player["active_ch2_trial"] = "trial_12_sage_q1"
        player["sage_mistakes"] = 0
        log = (
            "*** TRIAL: THE SAGE OF THE CALIGO MOUNTAINS (QUESTION 1 OF 3) ***\n\n"
            "Master Spotted Tail pours two clay cups of steaming pine-needle tea and fixes you with calm, ancient eyes.\n"
            "\"Many climb these crags seeking charters, maps, or advantage in the coming storm between Ragmore and Laydere. First, let us see if you possess wisdom.\"\n\n"
            "\"QUESTION 1: In Murum, the magistrates measure every worker's sweat by the 1,000-minute Decimal Clock, locking the gates at 7:50. Tell me, traveller: who truly owns the hours of the day?\""
        )
        return player, log, "CH2_TRIAL"

    if choice.startswith("Share a cup of mountain herbal tea"):
        player["health"] = player["max_health"]
        player["hunger"] = 100
        player["thirst"] = 100
        return player, (
            "Master Spotted Tail pours you a steaming cup of fragrant alpine herb tea. Warmth floods your limbs and clears your mind.\n"
            "*** Your Health, Hunger, and Thirst are completely restored! ***"
        ), "MAIN"

    if choice == "Ask about the Castellans & the Gathering Storm":
        return player, (
            "\"Castellan Hrothgar at Castle Ragmore and Castellan Eormenhild at Castle Laydere are two blades forged from the same ruthless iron,\" Spotted Tail muses.\n"
            "\"Right now they keep a brittle peace—but once you take up your new post, their cold war will break into open fire. Guard your allies well.\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"

def get_joyinsorrow_union_options(player):
    opts = ["Ask about the Farm Picket Line"]
    if player.get("chapter_2_route") == "Stand for Union Official":
        step = player.get("ch2_mission_step", 1)
        if step == 1:
            if not player.get("m1a_started"):
                opts.insert(0, "Mission: Rally Wavering Farm Delegations to the Strike")
            else:
                rallied = len(player.get("m1a_rallied", []))
                opts.insert(0, f"Report on Wavering Delegations ({rallied}/3 Rallied)")
        elif step == 3:
            if not player.get("m1c_started"):
                opts.insert(0, "Mission: Hear Joyinsorrow's Urgent Report on the Scab Convoy")
            else:
                opts.insert(0, "Ask how our Picket Line preparations look")
                opts.insert(0, "Mission: Take Position at the Barricade (Confront the Convoy!)")
        elif step == 5:
            opts.insert(0, "Discuss the Stolen Strike Chest & Committee Alibis")
    else:
        opts.append("Offer Solidarity to the Strikers")
    opts.append("Leave")
    return opts


def resolve_joyinsorrow_union(choice, player):
    if choice == "Leave":
        return player, "\"Solidarity forever, comrade.\"", "MAIN"

    if choice == "Mission: Rally Wavering Farm Delegations to the Strike":
        player["m1a_started"] = True
        player["m1a_rallied"] = []
        player["m1a_firebreathers"] = []
        player["ironhand_drinks_bought"] = 0

        db.npc_database["steadfast_ploughman"]["location"] = (10, 10)
        db.npc_database["goodseed_orchardist"]["location"] = (10, 6)
        db.npc_database["ironhand_carter"]["location"] = (11, 3)

        log = (
            "=== MISSION: THE WAVERING STRIKE COMMITTEE ===\n"
            "Organiser Joyinsorrow pulls you aside by the glowing brazier, their voice low and urgent.\n"
            "\"Thank the earth you're here, Noburu. Our picket line looks fierce, but behind the scenes the strike is hanging by a thread.\"\n"
            "\"Bailiff Seekgrace has threatened winter evictions, and the Kokeshi Syndicate is paying off muscle to break us. "
            "Three of our crucial farm delegations have lost their nerve and abandoned the picket:\"\n\n"
            "  1. **Ploughman Steadfast** — Packing up his tools in the eastern Murum Farmlands south-east of the town wall. He's an honest man, just frightened for his family's larder.\n"
            "  2. **Orchardist Goodseed** — Hiding among the cider presses in the western Fluvius Orchards. Kokeshi thugs threatened to burn her trees.\n"
            "  3. **Carter Ironhand** — Leader of the heavy grain-teamsters. He's holed up drinking at the Quayside Taproom in Fluvius Town. He's the hardest nut to crack—and he won't listen to a dry throat, so you'll need to buy him a few rounds first!\n\n"
            "\"Travel to each of them, hear out their five grievances, and raise their **Union Fervour** until they swear to return! "
            "If you can turn all three into **100% Fire-Breathing Unionists**, our position before the Bailiff will be unstoppable!\""
        )
        return player, log, "MAIN"

    if choice.startswith("Report on Wavering Delegations"):
        rallied = player.get("m1a_rallied", [])
        if len(rallied) < 3:
            missing = []
            if "steadfast" not in rallied:
                missing.append("Ploughman Steadfast in the eastern Murum Farmlands")
            if "goodseed" not in rallied:
                missing.append("Orchardist Goodseed in the western Fluvius Orchards")
            if "ironhand" not in rallied:
                missing.append("Carter Ironhand at the Quayside Taproom in Fluvius Town")
            return player, (
                f"\"You've rallied {len(rallied)} of the 3 delegations so far, comrade! We need all three standing shoulder-to-shoulder before we face Bailiff Seekgrace.\"\n"
                "Still wavering:\n • " + "\n • ".join(missing)
            ), "MAIN"

        db.npc_database["steadfast_ploughman"]["location"] = None
        db.npc_database["goodseed_orchardist"]["location"] = None
        db.npc_database["ironhand_carter"]["location"] = None

        fire_cnt = len(player.get("m1a_firebreathers", []))
        player["ch2_mission_step"] = 2

        if fire_cnt >= 3:
            player["union_delegations"] = 3
            player["position_strength"] = player.get("position_strength", 0) + 35
            player["charisma"] = player.get("charisma", 0) + 2
            player["silver"] += 30
            modify_faction(player, "faction_union", 3)
            if "red-and-gold strike banner" not in player["inventory"]:
                player["inventory"].append("red-and-gold strike banner")
            log = (
                "=========================================================\n"
                "   MISSION TRIUMPH: THREE FIRE-BREATHING DELEGATIONS! \n"
                "=========================================================\n"
                "Steadfast, Goodseed, and Ironhand march back to the barricade at the head of their workers, singing the Union anthem at the top of their lungs!\n"
                "Organiser Joyinsorrow grips your shoulders in awe.\n"
                "\"You didn't just bring them back, Noburu—you set their hearts ablaze! Every farmhand from Murum to the delta is ready to lock the granaries!\"\n"
                "Joyinsorrow presents you with the **Red-and-Gold Strike Banner** and a **30-silver** campaign purse!\n\n"
                "*** SPECIAL REWARD UNLOCKED: +Red-and-Gold Strike Banner, +35% Position Strength, +2 Charisma, +3 Union Faction, +30 Silver! ***\n"
                "*** Next Mission: Travel to the Counting House in Fluvius Town to negotiate with Bailiff Seekgrace ***"
            )
        else:
            player["union_delegations"] = 2
            player["position_strength"] = player.get("position_strength", 0) + 24
            player["charisma"] = player.get("charisma", 0) + 1
            modify_faction(player, "faction_union", 2)
            log = (
                "*** MISSION COMPLETE! (+24% Position Strength, +1 Charisma, +2 Union Faction) ***\n"
                f"All three delegations have returned to the picket line ({fire_cnt}/3 at maximum Fire-Breathing Fervour)!\n"
                "Organiser Joyinsorrow salutes you warmly.\n"
                "*** Next Mission: Travel to the Counting House in Fluvius Town to negotiate with Bailiff Seekgrace ***"
            )
        return player, log, "MAIN"

    if choice in (
        "Mission: Hear Joyinsorrow's Urgent Report on the Scab Convoy",
        "Mission: Confront the Kokeshi Scab Convoy at the Barricade!",
    ):
        player["m1c_started"] = True
        player["m1c_mustered_crews"] = []
        db.npc_database["steadfast_ploughman"]["location"] = (10, 10)
        db.npc_database["goodseed_orchardist"]["location"] = (10, 6)
        db.npc_database["ironhand_carter"]["location"] = [(11, 3), "barge and anchor"]

        log = (
            "=== MISSION: THE GATHERING STORM AT THE CROSSROADS ===\n"
            "Organiser Joyinsorrow tosses an armful of dry brushwood onto the picket brazier, their face grim.\n"
            "\"Seekgrace may have signed our parchment, Noburu, but the Kokeshi Syndicate refuses to let the harvest sit locked in the barns. "
            "Our lookouts spotted heavy grain-wagons and hired muscle gathering down in Fluvius Town to smash through our picket line and haul the grain to the barges.\"\n\n"
            "\"Right now, we don't know **when** they plan to roll, **which road** they're taking, or **why** working drovers have agreed to drive for the Kokeshi. "
            "And with only a handful of us round this brazier, three heavy teams and six bruisers will trample us flat.\"\n\n"
            "\"Before you call the standoff here at the barricade, go into Fluvius and the surrounding lanes—find out what the convoy is planning, "
            "see if you can slow their wagons on the approach, call up our allied farm crews to swell our ranks, and remember: "
            "**Watch Sergeant Beornraed's lancers are watching from the ridge. If anyone draws a blade or weapon, the Watch will cut us down under martial law—fists and shoulders only!**\""
        )
        return player, log, "MAIN"

    if choice == "Ask how our Picket Line preparations look":
        crews = len(player.get("m1c_mustered_crews", []))
        sab = "Flooded & narrowed" if player.get("m1c_road_sabotaged") else "Clear and fast"
        scabs = "Half the drivers have walked off" if player.get("m1c_scabs_persuaded") else "All three wagon crews are still intact"
        return player, (
            "Joyinsorrow shades their eyes, surveying the crossroads:\n"
            f"• **Allied Crews Mustered at the Barricade:** {crews}/3 delegations on the line.\n"
            f"• **Approach Road Condition:** {sab}.\n"
            f"• **Scab Convoy Morale:** {scabs}.\n"
            "\"When you are completely satisfied with our preparations, give the word and we'll lock arms across the road!\""
        ), "NPC_DIALOGUE"

    if choice.startswith("Mission: Take Position at the Barricade"):
        player, t_msg = execute_ch2_mission(player, "1c_barricade", time_cost=90, stamina_drain=15)
        player, log, next_state = ch2_union.init_barricade_brawl(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice == "Discuss the Stolen Strike Chest & Committee Alibis":
        return player, (
            "Organiser Joyinsorrow glances around the crossroads with a heavy heart.\n"
            "\"Steadfast, Goodseed, Faintnot, and I have led these farmhands since the first day of the strike. "
            "In local circles, every one of us is held beyond reproach—if we accuse one of our own here in Fluvius without an ironclad case before a neutral bench, the picket line will tear itself apart.\"\n\n"
            "\"Search around the crossroads brazier here, check the wharves and establishments in Fluvius Town, and question everyone. "
            "Once you know **who** unlocked the chest, **how** they opened the padlock, **how** they sent the grain-cache list to the Kokeshi, and **where** the forty silver went, "
            "travel north to **Union House in Murum Town** and lay your indictment before **Representative Truthtale**!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the Farm Picket Line":
        return player, "\"Not a sack of oats passes until the farmhands get a fair charter!\"", "NPC_DIALOGUE"

    if choice == "Offer Solidarity to the Strikers":
        player["active_ch2_trial"] = "trial_2_picket"
        return player, "You step up to the picket line.", "CH2_TRIAL"

    return player, "Error.", "MAIN"

# -------------------------------------------------------------------------
# MISSION 1A: THE 3 WAVERING FARM DELEGATES (STEADFAST, GOODSEED, IRONHAND)
# -------------------------------------------------------------------------

def get_steadfast_ploughman_options(player):
    rallied = player.get("m1a_rallied", [])
    if "steadfast" in rallied:
        opts = ["Ask how the Murum Oats crew is holding up"]
        # --- NEW FOR MISSION 1C ---
        if player.get("m1c_started") and "steadfast" not in player.get("m1c_mustered_crews", []):
            opts.insert(0, "Call up Steadfast's Ploughmen to reinforce the Crossroads Barricade")
        opts.append("Leave")
        return opts

    return [
        "Rally Ploughman Steadfast back to the Strike (Difficulty: Easy)",
        "Ask why his crew left the picket line",
        "Leave"
    ]

def resolve_steadfast_ploughman(choice, player):
    if choice == "Leave":
        return player, "Ploughman Steadfast leans on his ash pitchfork, gazing worriedly at his oat-rows.", "MAIN"
    if choice == "Ask how the Murum Oats crew is holding up":
        return player, "\"Our pitchforks are sharp and the red ribbon is flying from the barn, comrade!\"", "MAIN"
    if choice == "Ask why his crew left the picket line":
        return player, (
            "Steadfast sighs, rubbing his calloused palms.\n"
            "\"I believe in the Union, Noburu—truly I do. But my cottage roof leaks, the Bailiff's clerk threatened to seize our seed-oats, "
            "and the men are terrified their children will go hungry before Seekgrace yields.\""
        ), "NPC_DIALOGUE"
    if choice.startswith("Call up Steadfast's Ploughmen"):
        player.setdefault("m1c_mustered_crews", []).append("steadfast")
        return player, "Ploughman Steadfast hefts his ash pitchfork. \"Right lads! The organiser calls! March to the crossroads!\" (Steadfast's crew joins the barricade line).", "MAIN"
    if choice.startswith("Rally Ploughman Steadfast"):
        player, t_msg = execute_ch2_mission(player, "1a_steadfast", time_cost=90, stamina_drain=10)
        import mini_games
        player, log, next_state = mini_games.init_farm_debate(player, delegate_key="steadfast")
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state
    return player, "Error.", "MAIN"


def get_goodseed_orchardist_options(player):
    rallied = player.get("m1a_rallied", [])
    if "goodseed" in rallied:
        opts = ["Check on the Fluvius Pressers"]
        # --- NEW FOR MISSION 1C ---
        if player.get("m1c_started") and "goodseed" not in player.get("m1c_mustered_crews", []):
            opts.insert(0, "Call up Goodseed's Cider-Pressers to reinforce the Crossroads Barricade")
        opts.append("Leave")
        return opts

    if "steadfast" not in rallied:
        return ["Ask about the Fluvius Orchards (Rally Steadfast first!)", "Leave"]

    return [
        "Rally Orchardist Goodseed back to the Strike (Difficulty: Medium)",
        "Ask about the Kokeshi threats",
        "Leave"
    ]

def resolve_goodseed_orchardist(choice, player):
    if choice == "Leave":
        return player, "Orchardist Goodseed checks the iron padlocks on her cider-press shed.", "MAIN"
    if choice == "Check on the Fluvius Pressers":
        return player, "\"Not a single barrel of cider leaves this orchard until the charter is signed!\"", "MAIN"
    if choice.startswith("Ask about the Fluvius Orchards"):
        return player, (
            "Goodseed glances north toward Murum.\n"
            "\"If Ploughman Steadfast's oat-harvesters in the eastern Murum Farmlands haven't even committed to the strike yet, "
            "my orchard hands won't stick their necks out alone! Convince Steadfast first.\""
        ), "NPC_DIALOGUE"
    if choice == "Ask about the Kokeshi threats":
        return player, (
            "Goodseed's jaw tightens.\n"
            "\"Two men with Kokeshi tattoos rode through my trees at dusk. They said if I don't press cider for the Bailiff's tables, "
            "they'll ring-bark my thirty-year-old apple trees! Speeches won't stop axes, Noburu.\""
        ), "NPC_DIALOGUE"
    if choice.startswith("Call up Goodseed's Cider-Pressers"):
        player.setdefault("m1c_mustered_crews", []).append("goodseed")
        return player, (
            "Orchardist Goodseed locks her cider sheds. \"Let the Kokeshi come. Our press-hands are marching to the barricade!\" "
            "(Goodseed's crew joins the line)."
        ), "MAIN"
    if choice.startswith("Rally Orchardist Goodseed"):
        player, t_msg = execute_ch2_mission(player, "1a_goodseed", time_cost=120, stamina_drain=12)
        player, log, next_state = mini_games.init_farm_debate(player, delegate_key="goodseed")
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state
    return player, "Error.", "MAIN"

def get_ironhand_carter_options(player):
    rallied = player.get("m1a_rallied", [])
    if "ironhand" in rallied:
        opts = ["Share a toast to the Teamsters' Union"]
        # --- NEW FOR MISSION 1C ---
        if player.get("m1c_started") and "ironhand" not in player.get("m1c_mustered_crews", []):
            opts.insert(0, "Call up Carter Ironhand's Teamsters to reinforce the Crossroads Barricade")
        opts.append("Leave")
        return opts

    if "goodseed" not in rallied:
        return ["Try to speak with Carter Ironhand (Rally Goodseed first!)", "Leave"]

    drinks = player.get("ironhand_drinks_bought", 0)
    opts = []
    if drinks < 3:
        opts.append(f"Buy Ironhand a Tankard of Dark Quay Porter (2s) [{drinks}/3 Drinks]")
        opts.append("Try to talk Union politics with him dry")
    else:
        opts.append("Rally Carter Ironhand back to the Strike! (Difficulty: Hard)")
    opts.append("Leave")
    return opts

def resolve_ironhand_carter(choice, player):
    if choice == "Leave":
        return player, "Carter Ironhand stares moodily into his pewter tankard at the back of the Fluvius taproom.", "MAIN"
    if choice == "Share a toast to the Teamsters' Union":
        return player, "Ironhand clinks his tankard against yours. \"Every wagon axle in Fluvius is locked down tight, comrade!\"", "MAIN"
    if choice.startswith("Try to speak with Carter Ironhand"):
        return player, (
            "Ironhand doesn't even look up from the scarred oak table.\n"
            "\"Don't waste my time, organiser. Until both Steadfast and Goodseed are back on the line, the Teamsters aren't parking a single wagon.\""
        ), "NPC_DIALOGUE"
    if choice == "Try to talk Union politics with him dry":
        return player, (
            "Ironhand barks a bitter laugh and taps his empty pewter mug.\n"
            "\"My throat's as dry as a lime-kiln after hauling grain all week, and you want to lecture me on solidarity without wetting my whistle? Buy a working man three pints of Dark Porter first!\""
        ), "NPC_DIALOGUE"
    if choice.startswith("Buy Ironhand a Tankard"):
        if player["silver"] < 2:
            return player, "\"Two silver for two pints of Dark Quay Porter, friend—and your purse is light!\"", "NPC_DIALOGUE"
        player["silver"] -= 2
        player["thirst"] = min(100, player["thirst"] + 30)
        player["ironhand_drinks_bought"] = player.get("ironhand_drinks_bought", 0) + 1
        d_cnt = player["ironhand_drinks_bought"]
        if d_cnt == 1:
            msg = (
                "You slide 2 silver across the wet bar and bring two foaming tankards of dark Fluvius porter to the booth.\n"
                "Ironhand drains half his pint in one pull and wipes his moustache. \"Hmph. Decent head on that ale. Still doesn't pay my teamsters' fines, though.\" (1/3 Drinks)"
            )
        elif d_cnt == 2:
            msg = (
                "You set a second round of dark porter on the table. The warmth of the ale loosens Ironhand's broad shoulders.\n"
                "\"You know why I walked out, Noburu? Ten years ago I led a dock strike in Parvus, and the magistrates starved us out while the politicians talked. I won't watch my drivers broken again.\" (2/3 Drinks)"
            )
        else:
            msg = (
                "By the third tankard of porter, Ironhand slams his mug down and leans across the booth, his eyes glinting with old fire.\n"
                "\"Alright, comrade—you've paid your dues at the bar and you drink like a teamster! Speak your piece. Convince me this strike can actually win!\" (3/3 Drinks — Ready to Debate!)"
            )
        return player, msg, "NPC_DIALOGUE"
    if choice.startswith("Call up Carter Ironhand's Teamsters"):
        player.setdefault("m1c_mustered_crews", []).append("ironhand")
        return player, "Carter Ironhand drains his pewter mug and slams it down. \"Teams, unchain the wains! We're rolling to the crossroads!\" (Teamsters join the line).", "MAIN"
    if choice.startswith("Rally Carter Ironhand"):
        player, t_msg = execute_ch2_mission(player, "1a_ironhand", time_cost=120, stamina_drain=15)
        import mini_games
        player, log, next_state = mini_games.init_farm_debate(player, delegate_key="ironhand")
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    return player, "Error.", "MAIN"

def get_black_hills_options(player):
    return ["Speak of the Forest's Defence", "Pledge to halt farmland encroachment", "Leave"]


def resolve_black_hills(choice, player):
    if choice == "Leave":
        return player, "The Black Hills watches you from beneath the ancient boughs.", "MAIN"
    if choice == "Speak of the Forest's Defence":
        return player, (
            "\"The townsfolk think Lignum Forest is an endless larder of timber and soil,\" the Black Hills rumbles.\n"
            "\"Those who walk with respect for the canopy have nothing to fear from the Vanguard—but we will break every axe and plough that crosses our border.\""
        ), "NPC_DIALOGUE"
    if choice == "Pledge to halt farmland encroachment":
        if not player.get("vanguard_oath_taken"):
            player["vanguard_oath_taken"] = True
            modify_faction(player, "faction_vanguardists", 3)
            return player, "You swear to defend the ancient treeline. The Vanguardist elders mark your cloak with green moss-sap! (+3 Vanguardists Faction)", "MAIN"
        return player, "\"Your oath is already known among the boughs, friend of the Vanguard.\"", "MAIN"
    return player, "Error.", "MAIN"


def get_rain_in_the_face_options(player):
    return ["Rest & Drink at the Glade Spring (+Full Thirst/Hunger)", "Ask for Foraging Wisdom", "Leave"]


def resolve_rain_in_the_face(choice, player):
    if choice == "Leave":
        return player, "\"Walk in peace beneath the leaves, comrade.\"", "MAIN"
    if choice.startswith("Rest & Drink"):
        player["hunger"] = 100
        player["thirst"] = 100
        modify_faction(player, "faction_communards", 1)
        return player, (
            "Rain in the Face shares sweet roasted cobnuts and clear spring water with you in the sun-dappled glade.\n"
            "*** Your Hunger and Thirst are fully restored! (+1 Communards Faction) ***"
        ), "MAIN"
    if choice == "Ask for Foraging Wisdom":
        player["foraging_lore_learned"] = True
        return player, (
            "Rain in the Face shows you the difference between wholesome woodland roots and toxic lookalikes:\n"
            "\"Remember: **Golden Chanterelles** smell of apricots and have forked ridges, while **Pale Death-Caps** have white gills and a volva cup at the base. "
            "And **Sweet Bilberries** grow low on green stems, whereas **Dark Nightshade** bears five-petalled purple stars!\"\n"
            "*** You learned Communard Foraging Lore! ***"
        ), "NPC_DIALOGUE"
    return player, "Error.", "MAIN"

# -------------------------------------------------------------------------
# TRIAL 14: SKIPPER CEARA & THE RIVER FLUVIUS TRADERS
# -------------------------------------------------------------------------
RIVER_QUAYS = {
    (10, 20): "Northern Landing (Near Lake Diluvium & Parvus)",
    (13, 13): "Mid-River Quay (Lignum Forest Edge)",
    (7, 7):   "Southern Quay (Near The Heath & Fluvius Town)",
}

def get_river_trader_options(player):
    cur_pos = (player["x"], player["y"])
    fare = 5 if (player.get("charisma", 0) >= 3 or "market overseer" in player.get("skills", [])) else 12
    opts = []
    for q_coord, q_name in RIVER_QUAYS.items():
        if q_coord != cur_pos:
            opts.append(f"Pay {fare}s Fare to {q_name.split(' (')[0]}")
            if player.get("strength", 0) >= 2:
                opts.append(f"Work the Oars to {q_name.split(' (')[0]} (Free — Str 2+)")
            if any(b in player["inventory"] for b in ["spiced cider", "vintage brumaire wine"]):
                opts.append(f"Barter Cider/Wine for Passage to {q_name.split(' (')[0]}")
    opts.append("Ask about River Navigation")
    opts.append("Leave")
    return opts


def resolve_river_trader(choice, player):
    if choice == "Leave":
        return player, "Skipper Ceara touches his oiled cap. \"Mind the current, traveller.\"", "MAIN"

    if choice == "Ask about River Navigation":
        trips = player.get("river_trips_taken", 0)
        return player, (
            "Skipper Ceara leans on his long ash setting-pole.\n"
            "\"The River Fluvius has treacherous eddies and hidden gravel-bars. Make **two voyages** with my crew and watch how we read the ripples, and I'll teach you the **'River Navigation'** skill myself!\"\n"
            f"(Voyages completed: {trips}/2)"
        ), "NPC_DIALOGUE"

    dest_map = {
        "Northern Landing": (10, 20),
        "Mid-River Quay":   (13, 13),
        "Southern Quay":    (7, 7),
    }
    target_coord = next((coord for label, coord in dest_map.items() if label in choice), None)
    if not target_coord:
        return player, "Error.", "MAIN"

    fare = 5 if (player.get("charisma", 0) >= 3 or "market overseer" in player.get("skills", [])) else 12

    if choice.startswith("Pay "):
        if player["silver"] < fare:
            return player, f"\"Passage costs {fare} silver, friend, and you only have {player['silver']}s!\"", "NPC_DIALOGUE"
        player["silver"] -= fare
        pay_msg = f"You count out {fare} silver coins to Skipper Ceara."
    elif choice.startswith("Work the Oars"):
        player["hunger"] = max(0, player["hunger"] - 12)
        player["strength"] += 1
        pay_msg = "You take up a heavy ash sweep-oar and pull alongside the crew, earning your passage with honest sweat! (+1 Strength, -12 Hunger)"
    elif choice.startswith("Barter "):
        bottle = "spiced cider" if "spiced cider" in player["inventory"] else "vintage brumaire wine"
        player["inventory"].remove(bottle)
        pay_msg = f"You hand over your {format_item_name(bottle)}. Skipper Ceara grins warmly and waves you aboard!"
    else:
        return player, "Error.", "MAIN"

    player["prev_x"], player["prev_y"] = player["x"], player["y"]
    player["x"], player["y"] = target_coord
    player, _ = advance_time(45, player)
    player["river_trips_taken"] = player.get("river_trips_taken", 0) + 1
    player.setdefault("ch2_trials_done", []).append("trial_14_river")

    skill_note = ""
    if player["river_trips_taken"] >= 2 and "river navigation" not in player["skills"]:
        player["skills"].append("river navigation")
        skill_note = "\n*** Skipper Ceara shows you how to read the currents and shoals! You learned the 'River Navigation' skill! ***"

    return player, (
        f"{pay_msg}\n"
        f"The flat-bottomed keelboat glides swiftly along the River Fluvius and docks at {RIVER_QUAYS[target_coord]}!{skill_note}"
    ), "MAIN"

# =========================================================================
# CHUNK 1A: MOSAIC CLUE NPCS & TRACK 1 (UNION OFFICIAL: 1a - 1e)
# =========================================================================
def get_diarmuid_options(player):
    opts = ["Ask about Bailiff Seekgrace's habits"]
    if player.get("ch2_mission_step") == 5:
        opts.insert(0, "Ask if anyone paid off a large tab at the taproom recently")
    opts.append("Leave")
    return opts

def resolve_diarmuid(choice, player):
    if choice == "Leave":
        return player, "Diarmuid goes back to rinsing tankards.", "MAIN"
    if choice == "Ask if anyone paid off a large tab at the taproom recently":
        player["m1e_diarmuid_tab_clue"] = True
        return player, (
            "Diarmuid polishes a pewter tankard and lowers his voice.\n"
            "\"Funny you should ask! Delegate Faintnot—the one who preaches temperance at every strike meeting—had a secret forty-silver dice and gin tab running in our back room. "
            "The Kokeshi debt-collectors were threatening to break his fingers, and then an hour ago he waltzed in with dusty yellow boots and paid the whole forty silver in crisp coin from an iron-inked pouch!\""
        ), "NPC_DIALOGUE"
    tells = player.setdefault("bailiff_tells_learned", [])
    if "pipe" not in tells:
        tells.append("pipe")
    return player, (
        "Diarmuid leans over the quay rail.\n"
        "\"Old Bailiff Seekgrace? Whenever he sends me for cheap two-penny shag and puffs his clay pipe, "
        "it means his rent-chest is empty and he's bluffing! Never yield when he's smoking that pipe.\""
    ), "MAIN"

def get_hateevil_options(player):
    return ["Ask about the Bailiff's laundry & cuffs", "Leave"]

def resolve_hateevil(choice, player):
    if choice == "Leave":
        return player, "Laundress Hateevil wrings out a linen shirt.", "MAIN"
    tells = player.setdefault("bailiff_tells_learned", [])
    if "spectacles" not in tells:
        tells.append("spectacles")
    return player, (
        "Laundress Hateevil scowls at a stack of collars.\n"
        "\"Seekgrace always gets violet ink on his left cuff when he's taking Kokeshi kickbacks. "
        "And mark my words: when he polishes his brass spectacles, he's calculating a concession—but if he twists his iron signet ring, one more demand will make him walk out!\""
    ), "MAIN"

def get_tadhg_options(player):
    return [
        "Ask about the fishing in the southern reeds",
        "Ask if he heard the commotion at the watermill",
        "Leave"
    ]


def resolve_tadhg(choice, player):
    if choice == "Leave":
        return player, "Tadhg checks his wicker eel-traps among the willow osiers.", "MAIN"

    if choice == "Ask about the fishing in the southern reeds":
        return player, (
            "Tadhg nods toward the dark, slow-moving channel.\n"
            "\"Silver eels run thick along the mud-banks after dusk. I'm out here in the reeds most nights long after the town curfew bell rings.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask if he heard the commotion at the watermill":
        if "tadhg's witness statement" not in player["inventory"]:
            player["inventory"].append("tadhg's witness statement")
        return player, (
            "Tadhg glances nervously over his shoulder toward the eastern mill-race.\n"
            "\"I was crouched in the bullrushes lifting my wicker traps at midnight when three men came down the bank from the direction of the brick granaries. "
            "They weren't swinging axes—they had iron prybars and a boring-brace.\"\n"
            "\"When the oak axle cracked, one of them unshuttered a dark-lantern to check their work. The light fell straight across all three of their faces—every last man of them had a chin as smooth as a peeled onion! "
            "How could any of them be Farmer Flyfornication, when that man's fiery red beard hangs down to his belt buckle?!\"\n"
            "Tadhg scrawls his mark onto a strip of parchment so his account can be read before the bench."
        ), "MAIN"

    return player, "Error.", "MAIN"


def get_flyfornication_options(player):
    return [
        "Speak with him about the charges against him",
        "Ask if anyone had threatened his mill",
        "Leave"
    ]


def resolve_flyfornication(choice, player):
    if choice == "Leave":
        return player, "Farmer Flyfornication strokes his waist-length red beard, his wrists chafed by the Bailiff's iron shackles.", "MAIN"

    if choice == "Speak with him about the charges against him":
        return player, (
            "Farmer Flyfornication—whose thick red beard reaches his leather belt—shakes his head in disbelief.\n"
            "\"I built that waterwheel with my own father's hands, comrade! Why on earth would I take an axe to my own livelihood in the dead of night? "
            "I was asleep in the mill-loft until the crash of the timber woke me—and before I could even light a candle, the Bailiff's wardens were battering down my door with warrants already written!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask if anyone had threatened his mill":
        return player, (
            "\"Three days ago, Clerk Pinchpenny came out from the Counting House with a factor wearing a Kokeshi lapel-pin,\" Flyfornication says grimly.\n"
            "\"They offered to buy out my mill-lease for a pittance so the Syndicate could route all river-grain through the eastern granary wharf. "
            "When I threw them off my land, Pinchpenny wiped the yellow granary clay off his boots and told me I wouldn't own a single paddle by week's end.\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


def get_fleepride_options(player):
    return ch2_union.get_fleepride_union_options(player)


def resolve_fleepride(choice, player):
    return ch2_union.resolve_fleepride_union(choice, player)

UNION_DEMANDS = [
    ("10% Rent Reduction", 15),
    ("Abolish Mill-Wheel Tariffs", 20),
    ("Halt Forest Clear-Cutting", 20),
    ("8-Hour Decimal Workday", 25),
    ("Worker Control of Granaries", 30),
]

def calc_bargaining_success(player):
    """
    Calculates negotiation success % using Charisma, Influence, 1a Delegations & Tells,
    minus the weight of active demands AND Seekgrace's resistance to extravagant 1a promises!
    """
    cha_bonus = player.get("charisma", 0) * 6
    inf_bonus = player.get("influence", 0) * 6
    del_bonus = player.get("union_delegations", 0) * 10
    sk_bonus = 10 if ("union steward" in player.get("skills", []) or "radical theory" in player.get("skills", [])) else 0
    tell_bonus = len(player.get("bailiff_tells_learned", [])) * 10

    # Every demand toggled ON weighs down the probability of Seekgrace signing
    weight = sum(w for idx, (_, w) in enumerate(UNION_DEMANDS) if idx in player.get("active_demands", []))
    # Over-promising in 1a puts Seekgrace on his guard!
    promise_resistance = player.get("promises_count", 0) * 3

    return max(5, min(95, 65 + cha_bonus + inf_bonus + del_bonus + sk_bonus + tell_bonus - weight - promise_resistance))

def get_seekgrace_options(player):
    step = player.get("ch2_mission_step", 1)
    if player.get("chapter_2_route") == "Stand for Union Official" and step == 2:
        opts = []
        if not player.get("m1b_ready_to_sign"):
            opts.append("Mission: Request an Audience with the Bailiff")
        else:
            opts.append("Mission: Take your seat at the Bargaining Table")
        opts.append("Leave")
        return opts
    return ["Ask about farm rents", "Leave"]


def resolve_seekgrace(choice, player):
    if choice == "Leave":
        return player, "Bailiff Seekgrace snaps his heavy ledger shut, ignoring you.", "MAIN"
        
    if choice == "Mission: Request an Audience with the Bailiff":
        player["m1b_ready_to_sign"] = True
        log = (
            "=== MISSION: THE FLUVIUS HALL PARLEY ===\n"
            "You step into the oak-panelled counting house overlooking the Fluvius canal. Bailiff Seekgrace—a gaunt, sharp-featured man in a high-collared woollen coat—sits flanked by two bored lancers and a towering brass-bound rent ledger. He doesn't even look up from his quill.\n\n"
            "*** WARNING: Seekgrace is a veteran magistrate's factor who will give nothing away for free. Once you sit down at his table, you must negotiate all 10 points of the treaty via offer and counter-offer. ***\n"
            "*** Do not begin the parley until you have explored Fluvius Town and are fully satisfied with the intelligence you have gathered! ***"
        )
        return player, log, "MAIN"
        
    if choice == "Mission: Take your seat at the Bargaining Table":
        player, t_msg = execute_ch2_mission(player, "1b_bargain", time_cost=60, stamina_drain=5)
        import mini_games
        player, log, next_state = mini_games.init_bargain_minigame(player)
        if t_msg: log += "\n\n" + t_msg
        return player, log, next_state

    return player, "\"Pay your tariffs or face the lancers.\"", "MAIN"

# --- M1B INTEL: OSRIC THE LANCER (9, 3) ---
def get_osric_options(player):
    opts = ["Ask about the Garrison's Morale"]
    if player.get("silver", 0) >= 3:
        opts.append("Buy Osric a Hot Meat Pie & Ale (3s)")
    opts.append("Leave")
    return opts
    
def resolve_osric(choice, player):
    if choice == "Leave":
        return player, "Osric leans over the canal bridge, watching the dark water.", "MAIN"
        
    if choice == "Ask about the Garrison's Morale":
        return player, (
            "Osric scoffs. \"Morale? I serve the Castellan, not the Bailiff. If Seekgrace wants us to crack farmhand skulls, he can pay us.\""
        ), "NPC_DIALOGUE"
        
    if choice.startswith("Buy Osric a Hot"):
        player["silver"] -= 3
        player["intel_garrison_mutiny"] = True
        return player, (
            "You slide 3 silver onto the bridge wall for a pie and a pint. Osric devours it hungrily.\n"
            "\"You didn't hear it from me, comrade,\" he chews, \"but Seekgrace's local lancers haven't seen a silver penny in two weeks. "
            "If he orders a charge on the barricades tonight, the men will flat-out refuse to march.\""
        ), "MAIN"
        
# --- M1B INTEL: CHIEF CLERK PINCHPENNY (10, 4) ---
def get_pinchpenny_options(player):
    time_of_day = player["total_game_minutes"] % 1000
    opts = []
    if 500 <= time_of_day <= 700:
        opts.append("Eavesdrop from the Laundry Steps")
    opts.extend(["Ask for an appointment with Seekgrace", "Leave"])
    return opts
    
def resolve_pinchpenny(choice, player):
    if choice == "Leave":
        return player, "Pinchpenny scurries away, clutching a stack of wax-sealed invoices.", "MAIN"

    if choice.startswith("Ask for an appointment"):
        return player, "\"The Bailiff sees no one until the grain barges sail! Good day!\"", "NPC_DIALOGUE"

    if choice.startswith("Eavesdrop"):
        if player.get("stealth", 0) >= 3:
            player["intel_kokeshi_debt"] = True
            player["stealth"] += 1
            return player, (
                "Hiding in the shadows of the laundry steps, you listen as Pinchpenny confers with a Kokeshi grain-broker on the balcony.\n"
                "\"Tell your masters we need three more days!\" Pinchpenny begs. \"If the Syndicate forecloses on the Bailiff's private debts now, he will be ruined!\" (+1 Stealth) ***"
            ), "MAIN"
        player["health"] -= 1
        return player, (
            "You try to creep closer to the balcony, but you kick a loose bucket! "
            "Pinchpenny shouts for the guards, who rough you up and throw you back into the street! (-1 Health)"
        ), "MAIN"

    return player, "Pinchpenny ignores you.", "MAIN"

# =========================================================================
# CHUNK 1B: TRACK 7 (PUBLIC OFFICE) & TRACK 8 (KOKESHI SYNDICATE)
# =========================================================================
def get_watchandpray_options(player):
    opts = ["Ask about the Fluvius Civic Clock Tower"]
    if not player.get("clock_shim_fixed") and ("forge" in player.get("skills", []) or "masonry drill" in player.get("inventory", [])):
        opts.insert(0, "Remove the copper shim from the clock escapement (Forge / Drill)")
    opts.append("Leave")
    return opts

def resolve_watchandpray(choice, player):
    if choice == "Leave":
        return player, "Clockmaker Watchandpray peers through his brass loupe.", "MAIN"
    if choice.startswith("Remove the copper shim"):
        player["clock_shim_fixed"] = True
        player["position_strength"] = player.get("position_strength", 0) + 15
        return player, (
            "You extract a Kokeshi copper shim wedged inside the pendulum escapement!\n"
            "Watchandpray gasps: \"Someone was trying to shift the Election Poll closing hour! Take this key to the clock-face—if you need to advance or retard the town bell on Election Day (7e/8e), the tower is yours!\""
        ), "MAIN"
    return player, "\"The town clock is running 20 decimal minutes fast! Someone tampered with the high gears, and my hands are too arthritic to pull the shim.\"", "NPC_DIALOGUE"


# =========================================================================
# CHUNK 2: TRACK 2 (GUARD), TRACK 3 (CASTELLAN), & TRACK 9 (HIGHWAY ROBBER)
# =========================================================================

# --- TRACK 2: TOWN GUARD (BEORNRAED) ---
def get_beornraed_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []

    if route == "Apply for Town Guard":
        if step == 1:
            opts.append("Mission: Drill in the Square for the Mayor's Parade")
        elif step == 2:
            if not player.get("m2b_started"):
                opts.append("Mission: Receive Urgent Dispatch on the Fluvius Street Riot")
            else:
                opts.append("Mission: Form the Watch Shield-Wall in Fluvius Square!")
        elif step == 3:
            if not player.get("m2c_started"):
                opts.append("Mission: Receive Orders for the Farm Strike Standoff")
            else:
                opts.append("Mission: Take Command of the Watch Cordon at the Crossroads!")
        elif step == 4:
            if not player.get("m2d_started"):
                opts.append("Mission: Receive Orders for the Mayor's Ragmore Convoy")
            else:
                opts.append("Mission: Order the Mayor's Carriage Out of Murum Gate (Begin Escort!)")
        elif step == 5:
            opts.append("Mission: Sound the Assembly Horn at the Frontier Watchpost!")

    opts.extend(["Ask about the Northern Road & Parvus", "Request Watch Patrol Support", "Leave"])
    return opts


def resolve_beornraed(choice, player):
    if choice == "Leave":
        return player, "\"Eyes sharp on the road, Watchman.\"", "MAIN"

    if choice == "Mission: Drill in the Square for the Mayor's Parade":
        player, t_msg = execute_ch2_mission(player, "2a_drill", time_cost=180, stamina_drain=25)
        player, log, next_state = mini_games.init_halberd_drill(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive Urgent Dispatch on the Fluvius Street Riot",
        "Mission: Quell the Street Riot",
    ):
        player["m2b_started"] = True
        log = (
            "=== MISSION: THE MASQUERADE RIOT IN FLUVIUS TOWN ===\n"
            "Lieutenant Beornraed unrolls a mud-splattered dispatch rider's scroll, his brow furrowed.\n"
            "\"Corporal, we have an emergency down in **Fluvius Town**. A mob of townsfolk and river-bargees has erupted in the Market Square outside the Counting House, tearing up cobbles and brandishing pitch-torches!\"\n\n"
            "\"Constable Ælfwine is holding the West Canal Bridge with a skeleton squad, but something about this uprising stinks. "
            "Why would honest chandlers and bargees suddenly riot in the middle of the afternoon?\"\n\n"
            "\"March south to **Fluvius Town** and speak with **Constable Ælfwine** at the western bridge. "
            "Before you order our shield-wall into the square, patrol the southern lanes, the clock-tower, and the river-booms—find out **who** incited the crowd, **what** they're trying to cover up, and **how** to douse those torches without butchering the townsfolk!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Form the Watch Shield-Wall in Fluvius Square!":
        player, t_msg = execute_ch2_mission(player, "2b_riot", time_cost=90, stamina_drain=15)
        player, log, next_state = ch2_guard.init_riot_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive Orders for the Farm Strike Standoff",
        "Mission: Manage Tensions at the Farm Strike",
    ):
        player["m2c_started"] = True
        db.npc_database["aelfwine"]["location"] = (11, 6)
        db.npc_database["wulfgar"]["location"] = (9, 10)
        log = (
            "=== MISSION: THE THIN BLUE LINE AT THE CROSSROADS ===\n"
            "Lieutenant Beornraed points a gauntleted finger at the regional map.\n"
            "\"Good work in Fluvius Square, Corporal—but the peace is hanging by a thread at the Fluvius Farm Crossroads. "
            "Organiser Joyinsorrow's strikers have chained hay-wains across the highway, and the Kokeshi Syndicate is marching a heavily escorted scab convoy up from the wharves to ram through.\"\n\n"
            "\"Our orders from Mayor Givethanks are strict: hold the thin blue line between them and prevent a bloodbath. "
            "But my scouts report three dangerous complications around the perimeter:\"\n"
            "  • Someone was seen hiding a bundle of lethal iron weapons near the Western Cider Orchards to spark a massacre.\n"
            "  • Sergeant Wulfgar and a troop of Castle Ragmore Lancers are massed along the Murum Farmland border, itching for an excuse to ride down the strikers.\n"
            "  • Outlaw highwaymen have been spotted lurking in the Sunken Sluice-Gate Lane west of the crossroads, waiting to rob the Bailiff's pay-wagon in the confusion.\n\n"
            "\"Patrol the surrounding farmlands, orchards, and lanes to neutralize those three threats first! "
            "When you are satisfied with your perimeter, speak to Constable Ælfwine at the crossroads (or return to me) to take command of the cordon!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Take Command of the Watch Cordon at the Crossroads!":
        player, t_msg = execute_ch2_mission(player, "2c_strike", time_cost=120, stamina_drain=15)
        player, log, next_state = ch2_guard.init_strike_cordon_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive Orders for the Mayor's Ragmore Convoy",
        "Mission: Escort Mayor Givethanks to Ragmore",
    ):
        player["m2d_started"] = True
        log = (
            "=== MISSION: THE DIPLOMATIC CONVOY UP THE NEW ROAD ===\n"
            "Lieutenant Beornraed buckles on his heavy breastplate.\n"
            "\"Mayor Givethanks has been summoned to Castle Ragmore for an emergency war-tax summit with Castellan Hrothgar. "
            "\"You are to command the Watch escort taking his state coach up the New Road.\"\n\n"
            "\"Be on your guard, Corporal: we have word that Black Dog's highwaymen are planning to ambush the coach along the road, "
            "\"and rumours of foul play surround the summit banquet itself.\n"
            "\"Before you order the coach out of the gate, Odhrán at the stables had concerns about the state coach,\n"
            "\"and Black Dog's gang favours the Muddy Hollow north of the Watchpost.\n"
            "\"It would be wise to check in with Quartermaster Cenric at the Frontier Watchpost regarding the summit provisions.\n"
            "\"See that the road and the summit provisions are secure before we roll!\n"
        )
        return player, log, "MAIN"

    if choice == "Mission: Order the Mayor's Carriage Out of Murum Gate (Begin Escort!)":
        player, t_msg = execute_ch2_mission(player, "2d_convoy", time_cost=120, stamina_drain=15)
        player, log, next_state = ch2_guard.init_convoy_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice.startswith("Mission: Sound the Assembly Horn") or choice.startswith("Mission 2e:") or choice.startswith("Mission: Rally the Watch") or choice.startswith("Mission: Defect"):
        player, t_msg = execute_ch2_mission(player, "2e_split", time_cost=90, stamina_drain=15)
        player, log, next_state = ch2_guard.init_watch_split_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if (
        choice.startswith("Mission: Rally the Watch")
        or choice.startswith("Mission: Defect and Join")
        or choice.startswith("Mission 2e:")
    ):
        player["ch2_mission_step"] = 6
        is_ragmore = "Ragmore" in choice
        player.setdefault("ch3_world_bits", {})["track_2"] = 1 if is_ragmore else 0
        pos = player.get("position_strength", 0) + (player.get("strength", 0) * 4)
        player["reputation"] += 2
        return player, (
            f"*** THE WATCH SPLITS (Mission Complete)! ***\n"
            f"You lock down the Frontier Watchpost and declare for Castle {'Ragmore' if is_ragmore else 'Laydere'}! Your troops ready their crossbows for Chapter 3!\n"
            f"*** Final Position Strength: {min(100, pos)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
        ), "CHAPTER_2_COMPLETE"

    if choice == "Ask about the Northern Road & Parvus":
        return player, "\"Watch out for deep wagon ruts and highwaymen in the tall grass.\"", "NPC_DIALOGUE"
    if choice == "Request Watch Patrol Support":
        if player.get("faction_guard", 0) >= 3:
            player["hunger"] = 100
            player["thirst"] = 100
            return player, "Beornraed shares hot garrison rations! (+Full Hunger/Thirst)", "MAIN"
        return player, "\"Garrison supplies are strictly for proven friends of the Guard.\"", "NPC_DIALOGUE"
    return player, "Error.", "MAIN"

# --- TRACK 3: CASTELLAN'S STAFF (HROTHGAR) ---
def get_hrothgar_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []

    # Preserve Track 7a Crossover from Chunk 1B
    if route == "Run for Public Office (50s)" and step == 1:
        if not player.get("m7a_briefed"):
            opts.append("Mission: Inquire about the Municipal War-Tax Summit")
        else:
            opts.append("Mission: Convene the Feudal War-Tax Summit with Lord Hrothgar!")

    if route == "Join Castellan's House Staff":
        if step == 1:
            if not player.get("m3a_started"):
                opts.append("Mission: Receive Orders on the Ragmore Plains Stampede")
            else:
                opts.append("Mission: Mount the Outriders & Clear Ragmore Plains!")
        elif step == 2:
            if not player.get("m3b_started"):
                opts.append("Mission: Receive Orders for the Royal Hunt in Lignum Forest")
            else:
                opts.append("Mission: Sound the Horns & Lead the Hunt into Lignum Forest!")
        elif step == 3:
            if not player.get("m3c_started"):
                opts.append("Mission: Receive Cavalry Orders for the Farm Strike Blockade")
            else:
                opts.append("Mission: Ride South with the Ragmore Lancers to the Crossroads!")
        elif step == 4:
            if not player.get("m3d_started"):
                opts.append("Mission: Receive Instructions for the Mayor's Summit Banquet")
            else:
                opts.append("Mission: Ring the Great Hall Gong & Host the Summit Banquet!")
        elif step == 5:
            if not player.get("m3e_started"):
                opts.append("Mission: Receive the Iron Signet to Muster the Feudal Levy")
            else:
                opts.append("Mission: Convene the War-Table & Muster the Feudal Host!")

    opts.extend(["Ask about the strained peace with Castle Laydere", "Leave"])
    return opts

def resolve_hrothgar(choice, player):
    if choice == "Leave":
        return player, "Castellan Hrothgar rests his mailed hand on his greatsword.", "MAIN"

    # Preserve Track 7a Resolution from Chunk 1B
    if choice == "Mission: Inquire about the Municipal War-Tax Summit":
        player["m7a_briefed"] = True
        return player, (
            "=== MISSION: THE FEUDAL WAR-TAX SUMMIT ===\n"
            "Castellan Hrothgar fixes you with a stern gaze from his high seat.\n"
            "\"So you seek the Tribune's chair in Fluvius? Then hear me well: before I endorse any candidate, I expect a pledge of war-taxes to supply my lancers against Castle Laydere.\"\n\n"
            "\"(Before convening the summit, search the chancery chests here in the Castle Ragmore bailey for the ancient Municipal Tax-Exemption Roll\n"
            "— or seek the Sage's Charter high in the Caligo Mountains — if you wish to negotiate Armed Neutrality from a position of strength!)\""
        ), "MAIN"

    if choice.startswith("Mission: Convene the Feudal War-Tax Summit"):
        return ch2_election.init_election_minigame(player, "7a")

    # Inside resolve_hrothgar(choice, player):
    if choice in (
        "Mission: Receive Orders on the Ragmore Plains Stampede",
        "Mission: Evict Wild Animals from Ragmore Plains",
    ):
        player["m3a_started"] = True
        log = (
            "=== MISSION: THE STAMPEDE ON RAGMORE PLAINS ===\n"
            "Castellan Hrothgar slams his mailed fist onto the oak table of the Great Hall.\n"
            "\"Steward! Scores of wild stags and razor-boars have burst out of Lignum Forest onto Ragmore Plains, "
            "stampeding my prize shorthorn cattle toward the western sea-cliffs!\"\n\n"
            "\"Before you take command of my outriders, ride out onto Ragmore Plains south of the keep and speak with Herdsman Ceolwulf. "
            "Find out why those woodland beasts fled the trees, search the eastern pasture hedge where they broke through, "
            "and see if the woodland folk in the glade know how to turn the stags without losing my cattle over the cliffs!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Mount the Outriders & Clear Ragmore Plains!":
        player, t_msg = execute_ch2_mission(player, "3a_herding", time_cost=120, stamina_drain=15)
        player, log, next_state = ch2_castellan.init_herding_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive Orders for the Royal Hunt in Lignum Forest",
        "Mission: Guide the Castellan's Hunt in Lignum Forest",
    ):
        player["m3b_started"] = True
        log = (
            "=== MISSION: THE ROYAL HUNT IN LIGNUM FOREST ===\n"
            "Castellan Hrothgar tests the edge of his heavy boar-spear.\n"
            "\"The barony must see that Castle Ragmore commands both plain and forest! Today we ride beneath the boughs of Lignum Forest to hunt the Great White Hart.\"\n\n"
            "\"Speak with Huntsman Æthelstan in the outer bailey before we set out. "
            "He claims the militant Vanguardist creatures have rigged the northern forest trails with deadfalls and snares. "
            "Scout the northern forest border yourself—and when you are ready to guide my stirrup, give the word!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Sound the Horns & Lead the Hunt into Lignum Forest!":
        player, t_msg = execute_ch2_mission(player, "3b_hunt", time_cost=150, stamina_drain=20)
        player, log, next_state = ch2_castellan.init_hunt_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive Cavalry Orders for the Farm Strike Blockade",
        "Mission: Dispatch Lancers to Quash the Farm Strike",
    ):
        player["m3c_started"] = True
        db.npc_database["wulfgar"]["location"] = (9, 10)
        log = (
            "=== MISSION: THE CAVALRY QUESTION AT THE CROSSROADS ===\n"
            "Castellan Hrothgar unrolls a petition sealed with Bailiff Seekgrace's signet.\n"
            "\"Down in the southern farmlands, striking peasants have barricaded the Fluvius Farm Crossroads, halting our grain-rents, while Kokeshi wagons clamor to pass. "
            "Sergeant Wulfgar and twenty of my heavy lancers are waiting on the Murum Farmland border for your command.\"\n\n"
            "\"Take heed, Steward: heavy destriers are worth their weight in silver. Do not lead my cavalry blindly into a narrow defile without scouting the Sunken Sluice-Gate Lane west of the crossroads first, "
            "and find out whether Bailiff Seekgrace and the Kokeshi are telling us the whole truth before you couch lances!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Ride South with the Ragmore Lancers to the Crossroads!":
        player, t_msg = execute_ch2_mission(player, "3c_lancers", time_cost=120, stamina_drain=15)
        player, log, next_state = ch2_castellan.init_lancers_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive Instructions for the Mayor's Summit Banquet",
        "Mission: Host the Summit with the Mayor",
    ):
        player["m3d_started"] = True
        log = (
            "=== MISSION: THE GRAND BANQUET & SUMMIT ===\n"
            "Castellan Hrothgar clasps his velvet mantle over his mail.\n"
            "\"Tonight we host Mayor Givethanks of Murum in the Great Hall to seal our financial alliance before war breaks out with Castle Laydere. "
            "As my Steward, the seating protocol, the wine, and the security of my keep rest on your shoulders.\"\n\n"
            "\"Speak with Cellarer Oswin here in the inner bailey before you ring the banquet gong. "
            "He has concerns about an unrecorded cask of wine landed at the Ragmore Lake jetty to the north, and about travelling performers lingering near the tapestries outside my map-room. "
            "Investigate both thoroughly before seating the guests!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Ring the Great Hall Gong & Host the Summit Banquet!":
        player, t_msg = execute_ch2_mission(player, "3d_summit", time_cost=120, stamina_drain=15)
        player, log, next_state = ch2_castellan.init_summit_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice in (
        "Mission: Receive the Iron Signet to Muster the Feudal Levy",
        "Mission: Muster the Feudal Levy for War!",
    ):
        player["m3e_started"] = True
        log = (
            "=== FINAL MISSION: MUSTERING THE FEUDAL LEVY FOR WAR ===\n"
            "Castellan Hrothgar presses his heavy iron signet ring into your palm, his eyes blazing.\n"
            "\"The beacons are lit! Castellan Eormenhild of Laydere is marching on the eastern river-fords! "
            "I am placing the mobilisation of the Grand Feudal Levy in your hands.\"\n\n"
            "\"Before you convene the War-Table to march:\"\n"
            "  • Search the Armoury Rack right here in the inner bailey to test the newly delivered lance-heads.\n"
            "  • Ride south into the **Ragmore Farmlands** to speak with Manor Reeve Godric at the Manor Tithe-Barn and search the baggage wains for any sabotage.\n"
            "\"Return to me when every lance and wagon is ready for war!\""
        )
        return player, log, "MAIN"

    if choice == "Mission: Convene the War-Table & Muster the Feudal Host!":
        player, t_msg = execute_ch2_mission(player, "3e_levy", time_cost=150, stamina_drain=20)
        player, log, next_state = ch2_castellan.init_levy_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice == "Ask about the strained peace with Castle Laydere":
        return player, "\"Castellan Eormenhild of Laydere has dammed our upper river and clear-cut the eastern woods. War is coming, traveller.\"", "NPC_DIALOGUE"
    return player, "Error.", "MAIN"

# --- MAYOR HOLDFAST OF PARVUS TOWN ---
def get_holdfast_options(player):
    route = player.get("chapter_2_route")
    step = player.get("ch2_mission_step", 1)
    opts = []
    if route == "Parvus: F.A.I.-C.N.T. Syndicate" and step == 5:
        opts.append("Mission: Strike at the Upper Parvus Promenade!")
    elif route == "Parvus: Crown Intelligencers" and step == 5:
        opts.append("Mission: Take Post on the Promenade to Foil the Assassin!")
    opts.extend(["Ask about Parvus Town", "Leave"])
    return opts

def resolve_holdfast(choice, player):
    if choice == "Leave":
        return player, "Mayor Holdfast turns back to the bustling festival crowd.", "MAIN"
    if choice == "Ask about Parvus Town":
        return player, (
            "Mayor Holdfast sweeps a hand across the bustling docks.\n"
            "\"Parvus is the maritime lifeblood of Dtessera Terra! Goods from across the sea flow through our harbour.\"\n"
            "\"But the radical syndicates, Kokeshi smugglers, and Crown agents wage a shadow war in my streets! I trust no one.\""
        ), "NPC_DIALOGUE"
    if choice == "Mission: Strike at the Upper Parvus Promenade!":
        return ch2_parvus.init_parvus_minigame(player, "4e")
    if choice == "Mission: Take Post on the Promenade to Foil the Assassin!":
        return ch2_parvus.init_parvus_minigame(player, "5e")
    return player, "Error.", "MAIN"


# In chapter_2.py, replace HANDLERS with:
HANDLERS = {
    "absenceofsin":         (ch2_election.get_absenceofsin_options, ch2_election.resolve_absenceofsin),
    "aelfwine":             (ch2_guard.get_aelfwine_options, ch2_guard.resolve_aelfwine),
    "aethelstan":           (ch2_castellan.get_aethelstan_options, ch2_castellan.resolve_aethelstan),
    "aldred_foundry":       (ch2_parvus.get_aldred_options, ch2_parvus.resolve_aldred),
    "bandoka":              (get_bandoka_options, resolve_bandoka),
    "beornraed":            (get_beornraed_options, resolve_beornraed),
    "black_dog":            (ch2_roguery.get_black_dog_roguery_options, ch2_roguery.resolve_black_dog_roguery),
    "black hills":          (get_black_hills_options, resolve_black_hills),
    "bran_outrider":        (ch2_roguery.get_bran_options, ch2_roguery.resolve_bran),
    "buildhope":            (ch2_parvus.get_buildhope_parvus_options, ch2_parvus.resolve_buildhope_parvus),
    "cenric":               (ch2_guard.get_cenric_options, ch2_guard.resolve_cenric),
    "ceolwulf":             (ch2_castellan.get_ceolwulf_options, ch2_castellan.resolve_ceolwulf),
    "corban":               (ch2_union.get_corban_options, ch2_union.resolve_corban),
    "diarmuid":             (get_diarmuid_options, resolve_diarmuid),
    "diewell":              (ch2_election.get_diewell_election_options, ch2_election.resolve_diewell_election),
    "eadric":               (ch2_parvus.get_eadric_parvus_options, ch2_parvus.resolve_eadric_parvus),
    "embracepenitence":     (meta_progression.get_embracepenitence_options, meta_progression.resolve_embracepenitence),
    "eoghan":               (ch2_election.get_eoghan_options, ch2_election.resolve_eoghan),
    "faintnot":             (ch2_union.get_faintnot_options, ch2_union.resolve_faintnot),
    "fairlight":            (ch2_roguery.get_fairlight_roguery_options, ch2_roguery.resolve_fairlight_roguery),
    "fearghal":             (ch2_union.get_fearghal_options, ch2_union.resolve_fearghal),
    "fleepride":            (get_fleepride_options, resolve_fleepride),
    "flyfornication":       (get_flyfornication_options, resolve_flyfornication),
    "gilded_tongue":        (ch2_election.get_gilded_tongue_options, ch2_election.resolve_gilded_tongue),
    "godric_reeve":         (ch2_castellan.get_godric_reeve_options, ch2_castellan.resolve_godric_reeve),
    "goodseed_orchardist":  (get_goodseed_orchardist_options, resolve_goodseed_orchardist),
    "hateevil":             (get_hateevil_options, resolve_hateevil),
    "holdfast":             (get_holdfast_options, resolve_holdfast),
    "hopewell":             (ch2_guard.get_hopewell_options, ch2_guard.resolve_hopewell),
    "hrothgar":             (get_hrothgar_options, resolve_hrothgar),
    "ironhand_carter":      (get_ironhand_carter_options, resolve_ironhand_carter),
    "joyinsorrow_union":    (get_joyinsorrow_union_options, resolve_joyinsorrow_union),
    "keepfaith":            (ch2_union.get_keepfaith_options, ch2_union.resolve_keepfaith),
    "maeve_anchor":         (ch2_parvus.get_maeve_options, ch2_parvus.resolve_maeve),
    "mairead":              (ch2_guard.get_mairead_options, ch2_guard.resolve_mairead),
    "mountain sage":        (get_mountain_sage_options, resolve_mountain_sage),
    "odhran":               (ch2_guard.get_odhran_options, ch2_guard.resolve_odhran),
    "oisin":                (ch2_union.get_oisin_options, ch2_union.resolve_oisin),
    "osric":                (get_osric_options, resolve_osric),
    "oswin":                (ch2_castellan.get_oswin_options, ch2_castellan.resolve_oswin),
    "pinchpenny":           (get_pinchpenny_options, resolve_pinchpenny),
    "rain in the face":     (get_rain_in_the_face_options, resolve_rain_in_the_face),
    "returning_officer":    (ch2_election.get_returning_officer_election_options, ch2_election.resolve_returning_officer_election),
    "river trader":         (get_river_trader_options, resolve_river_trader),
    "ronan_rigger":         (ch2_parvus.get_ronan_options, ch2_parvus.resolve_ronan),
    "seekgrace":            (get_seekgrace_options, resolve_seekgrace),
    "silktongue":           (ch2_roguery.get_silktongue_options, ch2_roguery.resolve_silktongue),
    "skipper_omalley":      (meta_progression.get_embracepenitence_options, meta_progression.resolve_embracepenitence),
    "speaktruth":           (ch2_parvus.get_speaktruth_parvus_options, ch2_parvus.resolve_speaktruth_parvus),
    "steadfast_ploughman":  (get_steadfast_ploughman_options, resolve_steadfast_ploughman),
    "tadhg":                (get_tadhg_options, resolve_tadhg),
    "watchandpray":         (get_watchandpray_options, resolve_watchandpray),
    "wulfgar":              (ch2_guard.get_wulfgar_options, ch2_guard.resolve_wulfgar),
    "grimwald":             (ch3_war_engine.get_grimwald_options, ch3_war_engine.resolve_grimwald),
}


# =========================================================================
# 3. CHAPTER 2 TRIALS ENGINE — BATCHES 1, 2 & 3 (TRIALS 1 TO 12)
# =========================================================================


def trigger_wilderness_forage(player, world_map):
    """
    Launches Trial 17 (Botanical Foraging Puzzle) ONLY when searching in true wilderness regions!
    """
    pos = (player["x"], player["y"])
    room = world_map.get(pos)
    if not room or player.get("current_building"):
        return False, None, "MAIN"

    wild_regions = {
        "The Forest", "Lignum Glade", "Diluvium Glade",
        "The Heath", "Plains", "Old Path Plains", " The Caligo Mountains", "The Caligo Mountains"
    }
    if room.region not in wild_regions:
        return False, None, "MAIN"

    player["active_ch2_trial"] = "trial_17_forage"
    player["forage_variant"] = random.choice(["mushrooms", "berries"])
    if player["forage_variant"] == "mushrooms":
        log = (
            "*** TRIAL: FORAGING IN THE WILDS (MUSHROOMS) ***\n\n"
            "Searching beneath the damp roots, you find two clusters of wild fungi growing side by side:\n"
            "• **Cluster A:** Trumpet-shaped golden caps with forked ridges underneath and a faint scent of apricots.\n"
            "• **Cluster B:** Smooth, pale-white caps with white gills and a cup-like sack around the base of the stem.\n"
        )
    else:
        log = (
            "*** TRIAL: FORAGING IN THE WILDS (BERRIES) ***\n\n"
            "Parting the bracken, you spot two different berry-bearing shrubs:\n"
            "• **Shrub A:** Low-growing green stems bearing dusty-blue berries with a sweet, tart aroma.\n"
            "• **Shrub B:** Tall branching stalks with five-petalled purple star-flowers and shiny black berries.\n"
            "Which do you harvest and eat?"
        )
    return True, log, "CH2_TRIAL"

def check_chapter_2_move_triggers(player, target_pos, target_room):
    """
    Checks if stepping onto `target_pos` triggers one of the Chapter 2 Trials.
    Returns (triggered_bool, log_msg, next_menu_state).
    """
    completed = player.setdefault("ch2_trials_done", [])
    region = target_room.region

    # --- BANDOKA ROADSIDE MILESTONE ENCOUNTER ---
    if target_pos in [(6, 17), (5, 17)] and not player.get("bandoka_met_roadside") and not player.get("bandoka_joined"):
        player["bandoka_met_roadside"] = True
        db.npc_database["bandoka"]["location"] = target_pos
        log = (
            "*** A TRAVELLER BY THE MILESTONE ***\n\n"
            "As you reach the milestone where the road leaves Murum's shadow, a figure leaning on a stout ash staff straightens up from a stone marker.\n"
            "He has an easy, weather-worn smile and a heavy travel cloak.\n"
            "\"Ho there, traveller!\" he calls out cheerfully. \"Roads are long and the highwaymen are restless today. "
            "Name's Bandoka—I'm heading north toward the frontier. Mind if I walk alongside you for a spell?\"\n\n"
            "*** Bandoka the Fellow Traveller is resting by the milestone! Use 'Action -> Talk' to speak with him. ***"
        )
        return True, log, "MAIN"

    # Keep Bandoka walking alongside the player on every outdoor tile!
    if player.get("bandoka_joined"):
        db.npc_database["bandoka"]["location"] = target_pos

    # --- TRIAL 9: BANDOKA'S DOUBLE AGENT CLIMAX AT DESTINATION APPROACHES ---
    if (
        player.get("bandoka_joined")
        and "trial_9_bandoka" not in completed
        and target_pos in [(15, 24), (16, 21), (10, 5), (5, 22), (16, 10)]
    ):
        player["active_ch2_trial"] = "trial_9_bandoka"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE DOUBLE AGENT'S TRAP! ***\n\n"
            "As the destination comes into view ahead, Bandoka suddenly steps in front of you on the narrow path, blocking your way.\n"
            "Their easygoing smile is gone, replaced by a cold, calculating stare.\n"
            "\"Far enough, Noburu. My employers paid handsomely to make sure your Murum dispatches—and your credentials—never reach their destination.\"\n\n"
            "How do you counter Bandoka's betrayal?"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 2: THE FARM PICKET LINE at (8, 10) or (11, 6) ---
    if target_pos in [(8, 10), (11, 6)] and f"picket_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_2_picket"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE FARM PICKET LINE! ***\n\n"
            "Three heavy hay-wains are chained wheel-to-wheel across the farm road, blocking all passage!\n"
            "Two dozen striking farmhands led by Organiser Joyinsorrow stand behind a glowing brazier, holding pitchforks and a red Union banner.\n"
            "\"Halt!\" Joyinsorrow calls out. \"This road is closed by order of the Agrarian Strike Committee until the grain-rents are lowered! State your business!\""
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 4: BROKEN TRAVELLING CART at (7, 22) or (6, 11) ---
    if target_pos in [(7, 22), (6, 11)] and f"broken_cart_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_4_cart_stage_1"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE BROKEN SUPPLY WAGON! ***\n\n"
            "As you round the bend, you see a heavy supply wagon lurch into a waterlogged rut. CRACK! The rear iron axle-pin shears clean in half!\n"
            "The driver is thrown into the mud as the two draught horses in the traces rear up in terror, threatening to kick the wagon to splinters!\n\n"
            "*** STEP 1 OF 3: First, you must calm or restrain the panicked horses before they wreck the rig! ***"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 5: BROKEN CART BLOCKING THE PATH at (2, 14) or (11, 24) ---
    if target_pos in [(2, 14), (11, 24)] and f"blocked_cart_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_5_blocked_cart"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE BLOCKED DEFILE! ***\n\n"
            "A merchant's heavily laden provision cart has snapped its left wheel right in the narrowest choke-point of the road!\n"
            "On one side rises a sheer rockface; on the other drops a deep, bramble-choked ditch. The frantic merchant waves for help as their draught horse panics in the traces.\n"
            "How do you get past the blockage?"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 6: RICKETY BRIDGE WITH 15-LB MAX WEIGHT LIMIT at (6, 9) or (12, 17) ---
    if target_pos in [(6, 9), (12, 17)] and f"bridge_reinforced_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_6_rickety_bridge"
        player["active_ch2_coord"] = list(target_pos)
        curr_w = get_inventory_weight(player)
        mount_warn = " [WARNING: YOU ARE MOUNTED!]" if player.get("riding_horse") else ""
        log = (
            "*** TRIAL: THE RICKETY ROPE-BRIDGE (MAX LOAD: 15.0 LBS)! ***\n\n"
            "Before you sways an ancient rope-and-plank suspension bridge high above the white-water rapids of the River Fluvius.\n"
            "Half the hempen stays are frayed, and a weathered sign warns:\n"
            "  'DANGER: ROTTED TIMBERS — MAXIMUM SAFE LOAD 15.0 LBS. NO MOUNTED HORSES.'\n\n"
            f"• Your Current Load (Pack + Equipped Gear): **{curr_w} lbs**{mount_warn}\n"
            "• A dry **Riverbank Cache Box** sits beside the bridge pier where you can temporarily stash heavy gear, cross light to winch and reinforce the bridge cables from the far bank, and then reclaim your items!"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 7: LOCKED GATE & ABANDONED GATEHOUSE at (6, 12) or (15, 4) ---
    if target_pos in [(6, 12), (15, 4)] and f"locked_gate_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_7_locked_gate"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE LOCKED PORTCULLIS GATE! ***\n\n"
            "A massive iron portcullis is lowered across the stone archway, completely sealing the road ahead!\n"
            "Beside the arch stands an abandoned stone gatehouse—its oak door hanging slightly ajar, with a dusty ledger desk, a mossy cistern stone, and a dark chimney flue visible inside.\n"
            "How do you open or bypass the portcullis?"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 8: SPREADING HEATH FIRE & DANGEROUS SMOKE at (5, 5) or (4, 4) ---
    if target_pos in [(5, 5), (4, 4)] and f"heath_fire_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_8_heath_fire"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE SPREADING HEATH FIRE! ***\n\n"
            "A wall of orange flame is racing through the bone-dry gorse and heather! A gusting south-west wind drives thick, choking black smoke directly across the trail.\n"
            "Nearby, a soot-stained Heath Shepherd is desperately trying to beat back the flames before they reach a penned flock of sheep!\n"
            "How do you deal with the fire and smoke?"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 10: RIVER BREAKS ITS BANKS & CAUSES FLOODING at (9, 5) or (12, 7) ---
    if target_pos in [(9, 5), (12, 7)] and f"river_flood_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_10_flood"
        player["active_ch2_coord"] = list(target_pos)
        log = (
            "*** TRIAL: THE RIVER BREAKS ITS BANKS! ***\n\n"
            "Swollen by autumn rain and mountain snowmelt, the River Fluvius has burst right through its earthen levee!\n"
            "A freezing, waist-deep torrent roars across the road, threatening to wash away the lower farmsteads and blocking your path.\n"
            "How do you deal with the floodwaters?"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 11: SUNKEN TREASURE IN THE LAKE at (4, 24), (9, 20), (8, 2), or (18, 3) ---
    if target_pos in [(4, 24), (9, 20), (8, 2), (18, 3)] and f"lake_treasure_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_11_lake_stage_1"
        player["active_ch2_coord"] = list(target_pos)
        player["lake_breath"] = 4 if "swim" in player.get("skills", []) else 3
        player["lake_rope_tied"] = False
        log = (
            f"*** TRIAL: THE SUNKEN TREASURE OF {target_room.name.upper()}! ***\n\n"
            "Peering down through twenty feet of cold, glass-clear water from the mooring ledge, you spot a heavy iron-bound strongbox wedged beneath drowned roots on the lakebed!\n"
            f"• Your Lung Capacity: **{player['lake_breath']} Breath** ({'Boosted by Swim skill!' if 'swim' in player.get('skills', []) else 'Standard'})\n\n"
            "*** STAGE 1 OF 3 (THE DESCENT): How do you dive down to the lakebed? ***"
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 12: SEEK ADVICE FROM THE SAGE OF THE MOUNTAINS at (18, 5) ---
    if target_pos == (18, 5) and "trial_12_sage" not in completed:
        player["active_ch2_trial"] = "trial_12_sage_q1"
        player["active_ch2_coord"] = list(target_pos)
        player["sage_mistakes"] = 0
        log = (
            "*** TRIAL: THE SAGE OF THE CALIGO MOUNTAINS (QUESTION 1 OF 3) ***\n\n"
            "At the summit of the cloud-swept pass, Master Spotted Tail welcomes you into the stone observatory and pours two clay cups of steaming pine-needle tea.\n"
            "\"Many climb these crags seeking charters, maps, or advantage in the coming storm between Ragmore and Laydere. First, let us see if you possess wisdom.\"\n\n"
            "\"QUESTION 1: In Murum, the magistrates measure every worker's sweat by the 1,000-minute Decimal Clock, locking the gates at 7:50. Tell me, traveller: who truly owns the hours of the day?\""
        )
        return True, log, "CH2_TRIAL"

    # --- TRIAL 13: MOUFLIN ENCOUNTER in the Caligo Mountains ---
    if (target_pos == (16, 5) or region == "The Caligo Mountains") and "trial_13_mouflin" not in completed:
        if target_pos == (16, 5) or random.randint(1, 3) == 1:
            player["active_ch2_trial"] = "trial_13_mouflin"
            player["active_ch2_coord"] = list(target_pos)
            return True, (
                "*** TRIAL: THE CALIGO MOUFLIN RAM! ***\n\n"
                "On a narrow slate ledge high above the gorge, a herd of wild Caligo Mouflin blocks the pass.\n"
                "Their massive Alpha Ram—crowned with sweeping spiral horns—lowers its head and stamps the rock!\n"
                "How do you handle the Alpha Mouflin?"
            ), "CH2_TRIAL"

    # --- TRIAL 15: SINGLE-TUPLE BRIAR-MAZE DUNGEON at (8, 20) Diluvium Glade ---
    if target_pos == (8, 20) and "trial_15_maze" not in completed:
        player["active_ch2_trial"] = "trial_15_maze"
        player["maze_room"] = 0
        player["active_ch2_coord"] = list(target_pos)
        return True, (
            "*** TRIAL: THE DILUVIUM BRIAR-LABYRINTH (ROOM 1 OF 4)! ***\n\n"
            "You step through the ancient standing stones into a sprawling, roofed labyrinth of twenty-foot blackthorn hedges!\n"
            "To reach the hidden heart of the glade, you must read the natural signs in each chamber:\n\n"
            "• **CHAMBER 1 (THE MOSSY FORK):** Three thorny tunnels branch ahead. Silvery lichen grows thick on the **Northern** arch; the **Eastern** tunnel smells of stagnant bog-gas; the **Western** tunnel is choked with spiderwebs."
        ), "CH2_TRIAL"

    # --- TRIAL 16: WILD ANIMAL ATTACK (Wolves & Razor-Boar) ---
    if region in ["Plains", "Old Path Plains", "The Heath", "Diluvium Glade"] and random.randint(1, 6) == 1:
        player["active_ch2_trial"] = "trial_16_wild_beast"
        beast_name = "Pack of Starved Heath Wolves" if "Heath" in region else "Charging Razor-Boar"
        player["active_beast_name"] = beast_name
        return True, (
            f"*** TRIAL: WILD ANIMAL ATTACK ({beast_name.upper()})! ***\n\n"
            f"A {beast_name} bursts from the scrub with fangs bared, lunging straight at you!\n"
            "How do you react?"
        ), "CH2_TRIAL"

    # --- TRIAL 18: BUILD A BRIDGE at (13, 16) or (16, 10) ---
    if target_pos in [(13, 16), (16, 10)] and f"built_bridge_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_18_bridge_s1"
        player["active_ch2_coord"] = list(target_pos)
        return True, (
            "*** TRIAL: THE WASHED-OUT GORGE (BUILD A BRIDGE — STEP 1 OF 3)! ***\n\n"
            "The stone bridge across the torrent has collapsed, leaving a 15-foot chasm between the piers!\n"
            "To span the gorge, you must first **get a guide-line across to the far pier**. How do you do it?"
        ), "CH2_TRIAL"

    # --- TRIAL 19: REPAIR A PATH (THE ROCKSLIDE PASS) at (4, 12) or (16, 4) ---
    if target_pos in [(4, 12), (16, 4)] and f"repaired_path_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_19_rockslide"
        player["active_ch2_coord"] = list(target_pos)
        return True, (
            "*** TRIAL: THE ROCKSLIDE PASS! ***\n\n"
            "A massive slide of loose shale and a wedged **Central Keystone Boulder** block the pass!\n"
            "Inspecting the rubble, you see three features:\n"
            "  1. The **Upper Loose Shale** teetering precariously at the top.\n"
            "  2. The **Central Keystone Boulder** locking the pile together.\n"
            "  3. The **Lower Drainage Culvert** choked with mud, making the whole slope slick and unstable.\n"
            "How do you clear the rockslide?"
        ), "CH2_TRIAL"

    # --- TRIAL 20: THE SMUGGLERS ENCOUNTER at (2, 11) or (15, 22) ---
    if target_pos in [(2, 11), (15, 22)] and f"smugglers_{target_pos}" not in completed:
        player["active_ch2_trial"] = "trial_20_smugglers"
        player["active_ch2_coord"] = list(target_pos)
        return True, (
            "*** TRIAL: THE SMUGGLERS' COVE! ***\n\n"
            "Through the mist, you stumble upon a crew of hooded smugglers hauling crates of unstamped Parvus brandy and silk up from a muffled boat!\n"
            "Their lookout spots you and reaches for a crossbar: \"Hold! Friend, tax-man, or buzzard—speak fast!\""
        ), "CH2_TRIAL"

    # --- CHAPTER 2 DESTINATION ARRIVAL CHECK ---
    route = player.get("chapter_2_route")
    if route and not player.get("chapter_2_arrived"):
        dest_regions = {
            "Stand for Union Official":                 ["Fluvius Town", "Fluvius Farm"],
            "Apply for Town Guard":                     ["Parvus Town"],
            "Join Castellan's House Staff":             ["Ragmore Castle", "Laydere Castle"],
            "Parvus: F.A.I.-C.N.T. Syndicate":          ["Parvus Town"],
            "Parvus: Crown Intelligencers":             ["Parvus Town"],
            "Parvus: Maritime & Artisans Guild (50s)":  ["Parvus Town"],
            "Run for Public Office (50s)":              ["Fluvius Town"],
            "Join Wallmaker Syndicate":                 ["Laydere Castle"],
            "Become a Highway Robber":                  ["Diluvium Glade"],
            "Join Fairlight's Acting Troupe":           ["Fluvius Town", "Parvus Town"],
        }
        if region in dest_regions.get(route, []):
            player["chapter_2_arrived"] = True
            player["silver"] += 50
            player["reputation"] += 3
            return True, (
                "=========================================================\n"
                f"   CHAPTER 2 DESTINATION REACHED: {target_room.name.upper()}!   \n"
                "=========================================================\n"
                f"After braving the trials of the wilderness, you have arrived safely to assume your new post: **{route}**!\n"
                "Your superiors and allies welcome you with a **50 Silver completion purse** and **+3 Reputation** as the gathering storm of Chapter 3 looms on the horizon!"
            ), "MAIN"

    # --- TRIAL 1: EVOLVED HIGHWAY ROBBERS (Road Ambush with Archery / Outlaw / Faction Options) ---
    if region in ["The New Road", "The Old Path"] and "safe travel" not in player.get("skills", []):
        roll = random.randint(1, 6)
        if (not player.get("riding_horse") and roll <= 2) or (player.get("riding_horse") and roll == 1):
            player["active_ch2_trial"] = "trial_1_robbers"
            log = (
                "*** TRIAL: HIGHWAY ROBBERS OF THE FRONTIER! ***\n\n"
                "Whistles echo from the roadside gorse as a band of heavily armed highwaymen step out to block the road, crossbows and notched blades raised!\n"
                "Their scarred captain steps forward: \"Your coin purse or your life, traveller! Nobody walks this road for free!\""
            )
            return True, log, "CH2_TRIAL"

    # --- TRIAL 3: POOR WEATHER (BRUMAIRE GALE & FREEZING SQUALL) ---
    if region in ["Plains", "Old Path Plains", "The Heath", "The Caligo Mountains", "Dtessera Coast"]:
        if random.randint(1, 7) == 1:
            player["active_ch2_trial"] = "trial_3_weather"
            log = (
                f"*** TRIAL: HARSH BRUMAIRE STORM ON {region.upper()}! ***\n\n"
                "Black clouds roll in violently from the Dtessera Sea! Within moments, a freezing gale of sleet and horizontal rain lashes across the exposed landscape, "
                "numbing your fingers and dropping visibility to almost nothing!\n"
                "How do you weather the squall?"
            )
            return True, log, "CH2_TRIAL"

    return False, None, "MAIN"


def get_trial_options(player):
    """Returns the button labels for the currently active Chapter 2 Trial without meta-stat spoilers."""
    trial = player.get("active_ch2_trial")
    skills = player.get("skills", [])
    inv = player.get("inventory", [])

    if trial == "trial_1_robbers":
        opts = []
        if "archery" in skills:
            opts.append("Loose a longbow shot into their leader!")
        if player.get("chapter_2_route") == "Become a Highway Robber" or player.get("reputation", 0) <= -2:
            opts.append("Claim Outlaw Authority & Demand *Their* Tribute!")
        if player.get("faction_wallmakers", 0) >= 4 or "smugglers' cipher" in inv:
            opts.append("Flash Wallmaker Syndicate Signet")
        opts.append("Draw weapon and fight them!")
        opts.append(f"Pay Road Toll (Purse: {player['silver']}s)")
        opts.append("Make a run for it!")
        return opts

    if trial == "trial_2_picket":
        return [
            "Show Union Solidarity & Quote Proudhon",
            "Donate 10 Silver to the Strike Fund (10s)",
            "Mediate or Perform for the Strikers",
            "Break through the barricade by force",
            "Slip through the hedgerows unseen",
            "Turn back to the previous crossroads"
        ]

    if trial == "trial_3_weather":
        opts = []
        if "tent" in inv:
            opts.append("Pitch your Canvas Tent and wait out the storm")
        if any(d in inv for d in ["spiced cider", "vintage brumaire wine"]):
            opts.append("Drink Spiced Cider / Wine to keep your blood warm")
        if player.get("equusense", 0) >= 2 or any("scope" in i or "spyglass" in i for i in inv):
            opts.append("Spot a leeward rock hollow to shelter in")
        opts.append("Wrap your cloak tight and trudge through the freezing gale")
        return opts

    if trial == "trial_4_cart_stage_1":
        return [
            "Soothe the panicked horses with a steady cadence",
            "Feed the team a Carrot, Apple, or Cobnuts to calm them",
            "Seize the bridles by sheer muscle",
            "Dive clear of the kicking hooves!"
        ]
    if trial == "trial_4_cart_stage_2":
        return [
            "Heave the wagon bed up with your bare shoulders",
            "Rig a timber lever fulcrum under the axle",
            "Rally passing travellers to help lift together"
        ]
    if trial == "trial_4_cart_stage_3":
        return [
            "Hammer a replacement iron pin into the hub",
            "Lash the axle housing tightly with Rope or Leather",
            "Pay a passing tinker 10 Silver for a spare iron linchpin (10s)",
            "Drag the limping wagon out of the rut"
        ]

    if trial == "trial_5_blocked_cart":
        return [
            "Heave & chock the broken wheel for the merchant",
            "Calm & lead the panicked horse out of the traces",
            "Scale the rockface above the bottleneck",
            "Rob the stranded merchant while their cart is pinned!",
            "Scramble through the thorny briar-ditch",
            "Turn back the way you came"
        ]

    if trial == "trial_6_rickety_bridge":
        curr_w = get_inventory_weight(player)
        cache = player.get("bridge_cache", [])
        opts = []
        if player.get("riding_horse"):
            opts.append("Dismount your horse before stepping onto the planks")
        if curr_w > 15.0:
            opts.append(f"Stash heavy gear in Riverbank Cache (Load: {curr_w} lbs)")
        if cache:
            opts.append(f"Retrieve cached gear from Riverbank Cache ({len(cache)} item(s))")
        if "rope" in inv or "forge" in skills or player.get("strength", 0) >= 3:
            opts.append("Reinforce bridge cables & timbers from here")
        opts.append(f"Cross the Rickety Bridge now (Load: {curr_w} lbs)")
        opts.append("Step back from the bridge")
        return opts

    if trial == "trial_7_locked_gate":
        opts = []
        if player.get("gate_key_found"):
            opts.append("Unlock the Iron Portcullis with the Heavy Gate-Key!")
        opts.append("Read the Gatekeeper's Logbook on the desk")
        opts.append("Search beneath the mossy cistern stone")
        opts.append("Reach up inside the dark chimney flue")
        if "climb" in skills or ("rope" in inv and "grappling hook" in inv):
            opts.append("Scale the archway & release the winch from inside")
        if "masonry drill" in inv or "forge" in skills:
            opts.append("Shatter the rusted lock-bolt")
        opts.append("Step back from the locked gate")
        return opts

    if trial == "trial_8_heath_fire":
        opts = [
            "Read the wind direction & skirt upwind along the ridge",
            "Dig a firebreak & douse the brush to save the Shepherd's flock!",
        ]
        if any(w in inv for w in ["full water flask", "half-full water flask"]):
            opts.append("Soak a cloth from your Water Flask to breathe through the smoke")
        opts.append("Sprint blindly through the choking black smoke")
        opts.append("Retreat back the way you came")
        return opts

    if trial == "trial_9_bandoka":
        clues = player.get("bandoka_clues_spotted", [])
        opts = []
        if "curfew_lie" in clues:
            opts.append("Expose Curfew Lie: 'Murum's gates lock at 7:50—not 8:00!'")
        if "clay_boots" in clues:
            opts.append("Expose Boot-Clay: 'Your boots carry yellow Caligo clay, not Parvus sand!'")
        if "lock_slip" in clues or "cipher_sketch" in clues:
            opts.append("Expose Sapper Training: 'I saw you work that military winch and cipher!'")
        if player.get("stealth", 0) >= 2 or "intelligence officer" in skills:
            opts.append("Slip falsified dispatches into Bandoka's pack")
        opts.append("Draw your weapon and fight Bandoka!")
        opts.append("Trust Bandoka and hand over your travel papers for inspection")
        return opts

    if trial == "trial_10_flood":
        opts = [
            "Haul sandbags & timber stakes to plug the levee breach!",
            "Cut a diversion sluice trench to drain the road",
        ]
        if "swim" in skills:
            opts.append("Swim across the surging floodwater")
        if player.get("riding_horse") or "giant hairy armadillo" in inv:
            opts.append("Ride your mount through the swirling current")
        opts.append("Wade chest-deep through the freezing flood")
        opts.append("Pull back to higher ground")
        return opts

    if trial == "trial_11_lake_stage_1":
        opts = []
        if "swim" in skills:
            opts.append("Dive smoothly with trained swimmer's strokes")
        if "rope" in inv:
            opts.append("Tie a Rope to the jetty as a guide-line & descend")
        opts.append("Kick down holding a heavy ballast stone to sink fast")
        opts.append("Step back from the water's edge")
        return opts

    if trial == "trial_11_lake_stage_2":
        return [
            "Pry the strongbox free with a blade or drill",
            "Wrench the drowned oak roots apart with raw muscle",
            "Hack frantically at the roots with bare hands"
        ]

    if trial == "trial_11_lake_stage_3":
        opts = []
        if player.get("lake_rope_tied"):
            opts.append("Haul yourself straight up your knotted Rope guide-line!")
        opts.append("Drop ballast & kick powerfully for the surface")
        opts.append("Thrash upward toward the light with the heavy chest")
        return opts

    if trial == "trial_12_sage_q1":
        return [
            "Those who forge, sweep, and tend the land with their own hands.",
            "No one—time belongs to the turning of the earth and seasons.",
            "Whoever holds the gold to buy another person's labour.",
            "Step back from the observatory"
        ]
    if trial == "trial_12_sage_q2":
        return [
            "By curbing the townsfolk's greed and sharing the glades in mutual aid.",
            "By honouring ancient boundaries so neither axe nor antler draws blood.",
            "By burning the woods down so the strongest faction rules the ashes."
        ]
    if trial == "trial_12_sage_q3":
        return [
            "Keeping the peace and feeding the people rather than hoarding territory.",
            "Standing accountable to the commons who built the walls.",
            "Crushing every rival until only one banner flies."
        ]

    if trial == "trial_13_mouflin":
        opts = []
        if any(f in inv for f in ["cobnuts", "carrot", "apple"]) and player.get("equusense", 0) >= 2:
            opts.append("Offer Cobnuts/Carrot & Tame the Alpha Mouflin!")
        if player.get("equusense", 0) >= 1:
            opts.append("Bow your head & mimic a peaceful herd posture")
        if "archery" in skills:
            opts.append("Loose a warning shaft into the cliff above its horns")
        if player.get("stealth", 0) >= 2 or "climb" in skills:
            opts.append("Scramble along the lower crag unseen")
        opts.append("Draw weapon and fight the Alpha Mouflin Ram!")
        opts.append("Back down the mountain trail")
        return opts

    if trial == "trial_15_maze":
        rm = player.get("maze_room", 0)
        if rm == 0:
            opts = [
                "Take the Northern Arch (Silvery Lichen)",
                "Take the Eastern Tunnel (Bog-Gas Smell)",
                "Take the Western Tunnel (Spiderwebs)",
            ]
        elif rm == 1:
            opts = [
                "Follow the sound of trickling spring-water (West)",
                "Follow the trail of snapped deadwood twigs (North)",
                "Follow the muddy boar-wallows (East)",
            ]
        elif rm == 2:
            opts = [
                "Duck beneath the arch where purple violets bloom (South-East)",
                "Push through the pale nightshade brambles (North)",
                "Crawl through the dry bone-littered hollow (West)",
            ]
        else:
            opts = [
                "Step between the twin standing stones toward the sunlit glade!",
                "Follow the circling crow-shadows back into the gloom",
            ]
        if "compass" in inv or player.get("foraging_lore_learned"):
            opts.append("Use your Compass & Woodland Lore to verify the true path")
        opts.append("Retreat out of the Briar-Labyrinth")
        return opts

    if trial == "trial_16_wild_beast":
        opts = []
        if "archery" in skills:
            opts.append("Loose a first-strike arrow as it charges!")
        if any(m in inv for m in ["meat ration", "fish jerky"]) or player.get("equusense", 0) >= 2:
            opts.append("Toss dried meat or calm the charging beast")
        opts.append("Stand your ground and fight in melee!")
        opts.append("Scramble up a boulder to evade the charge")
        return opts

    if trial == "trial_17_forage":
        if player.get("forage_variant") == "mushrooms":
            opts = [
                "Harvest Cluster A (Golden trumpet caps with forked ridges)",
                "Harvest Cluster B (Smooth pale-white caps with a base cup)",
            ]
        else:
            opts = [
                "Harvest Shrub A (Low green stems with dusty-blue berries)",
                "Harvest Shrub B (Tall stalks with purple star-flowers & black berries)",
            ]
        if player.get("foraging_lore_learned") or player.get("equusense", 0) >= 2:
            opts.append("Use Foraging Lore to identify the safe plant")
        opts.append("Leave the wild plants alone")
        return opts

    if trial == "trial_18_bridge_s1":
        opts = []
        if "archery" in skills:
            opts.append("Shoot a cord across to the far pier with your bow!")
        if "grappling hook" in inv or "rope" in inv:
            opts.append("Hurl a Grappling Hook / Weighted Rope across the gap")
        if "swim" in skills:
            opts.append("Swim across the gorge with a line between your teeth")
        opts.append("Climb down & wade the boulder-rapids with a line")
        opts.append("Step back from the gorge")
        return opts

    if trial == "trial_18_bridge_s2":
        return [
            "Fell & lever two straight pine trunks across the piers",
            "Use your Rope & pulley leverage to haul the fallen logs across",
            "Strain with bare hands to drag the heavy trunks into place"
        ]

    if trial == "trial_18_bridge_s3":
        return [
            "Spike & brace the cross-planks with iron",
            "Lash the cross-planks taut with hemp Rope or Leather",
            "Wedge split stones and notched branches to lock the deck"
        ]

    if trial == "trial_19_rockslide":
        return [
            "1st: Clear the Lower Culvert, then lever the Keystone from the side!",
            "Use Masonry Drill or Forge skill to split the Keystone cleanly",
            "Yell & pull on the Upper Loose Shale first",
            "Heave directly in front of the Central Keystone Boulder",
            "Step back from the rockslide"
        ]

    if trial == "trial_20_smugglers":
        return [
            "Tap the 4-beat Mason's Code: Light, Heavy, Light, Heavy",
            "Declare Watch / Crown Authority & seize the contraband!",
            "Raid their boat and take the cargo for yourself!",
            "Offer 10 Silver to trade quietly for a Regional Map & Cider (10s)",
            "Back away into the mist"
        ]

    return ["Continue"]

def resolve_trial_choice(choice, player):
    """Resolves the player's chosen action in the active Chapter 2 Trial."""
    trial = player.get("active_ch2_trial")
    completed = player.setdefault("ch2_trials_done", [])
    coord_list = player.get("active_ch2_coord", [player["x"], player["y"]])
    coord_tuple = tuple(coord_list)

    # ==================================================================
    # TRIAL 1 RESOLUTION: HIGHWAY ROBBERS
    # ==================================================================
    if trial == "trial_1_robbers":
        player["active_ch2_trial"] = None

        if choice.startswith("Loose a longbow shot"):
            player["silver"] += 15
            player["reputation"] += 1
            log = (
                "Before the bandit captain can finish his threat, you smoothly draw your bow and loose a shaft that pins his hat to an oak trunk an inch above his ear!\n"
                "\"Archers! Run for it!\" the terrified highwaymen bellow, dropping a pouch of 15 silver as they scatter into the brush!\n"
                f"*** TRIAL OVERCOME VIA ARCHERY! (+15 Silver, +1 Reputation | Total Silver: {player['silver']}s) ***"
            )
            return player, log, "MAIN"

        if choice.startswith("Claim Outlaw Authority"):
            player["silver"] += 20
            log = (
                "You step forward coldly, display your own wanted notice and blade, and inform the gang that this stretch of road now belongs to YOU.\n"
                "Intimidated by your ruthless reputation, their leader bows and hands over 20 silver in road tribute!\n"
                f"*** OUTLAW DOMINANCE! (+20 Silver Tribute | Total Silver: {player['silver']}s) ***"
            )
            return player, log, "MAIN"

        if choice.startswith("Flash Wallmaker Syndicate"):
            log = (
                "You flash the secret sign of the Wallmaker Syndicate. The bandit captain lowers his crossbow immediately.\n"
                "\"Didn't realize you were on Wellspring and Hopestill's payroll, friend. Safe travels along the road.\""
            )
            return player, log, "MAIN"

        if choice == "Draw weapon and fight them!":
            p, _, _ = encounters.trigger_robber_encounter(player)
            return p, "You draw your weapon and charge the highwaymen!", "COMBAT"

        if choice.startswith("Pay Road Toll"):
            return encounters.pay_robber_toll(player)

        if choice == "Make a run for it!":
            p, _, _ = encounters.trigger_robber_encounter(player)
            return encounters.flee_encounter(p)

    # ==================================================================
    # TRIAL 2 RESOLUTION: THE FARM PICKET LINE
    # ==================================================================
    if trial == "trial_2_picket":
        if choice == "Turn back to the previous crossroads":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You turn back from the farm barricade.", "MAIN"

        if choice.startswith("Show Union Solidarity"):
            if player.get("union_status") == "joined" or "radical theory" in player.get("skills", []) or player.get("faction_union", 0) >= 3:
                player["active_ch2_trial"] = None
                completed.append(f"picket_{coord_tuple}")
                modify_faction(player, "faction_union", 2)
                player["inventory"].append("carrot")
                set_region_territory(player, "Murum Farm" if coord_tuple == (8, 10) else "Fluvius Farm", "Union")
                log = (
                    "You raise your fist in salute, flash your Union credentials, and speak in solidarity with the agrarian strikers!\n"
                    "The farmhands erupt into cheers, unchain the hay-wains to let you pass, and press a fresh purple carrot into your hand for the road.\n"
                    "*** PICKET LINE PASSED! (+2 Union Faction, +1 Free Carrot | Farmland rallied to UNION TERRITORY!) ***"
                )
                return player, log, "MAIN"
            return player, "\"Words are cheap, stranger! You don't carry a Union card or know the theory!\" Joyinsorrow calls back. Try another approach.", "CH2_TRIAL"

        if choice.startswith("Donate 10 Silver"):
            if player["silver"] >= 10:
                player["silver"] -= 10
                player["active_ch2_trial"] = None
                completed.append(f"picket_{coord_tuple}")
                modify_faction(player, "faction_union", 1)
                player["reputation"] += 1
                log = (
                    "You toss 10 silver coins into the strikers' soup-kettle fund.\n"
                    "Organiser Joyinsorrow nods gratefully and signals the farmhands to roll the hay-wain aside for you.\n"
                    f"*** PICKET LINE PASSED! (+1 Union Faction, +1 Reputation | Remaining Silver: {player['silver']}s) ***"
                )
                return player, log, "MAIN"
            return player, "\"You don't have 10 silver in your purse!\"", "CH2_TRIAL"

        if choice.startswith("Mediate or Perform"):
            if player.get("charisma", 0) >= 2 or player.get("influence", 0) >= 2 or player.get("chapter_2_route") == "Join Fairlight's Acting Troupe":
                player["active_ch2_trial"] = None
                completed.append(f"picket_{coord_tuple}")
                player["reputation"] += 2
                player["charisma"] += 1
                log = (
                    "Climbing onto a hay-bale, you deliver a stirring address (and a biting satirical verse about the tax-bailiffs) that has the entire picket line roaring with applause!\n"
                    "They unchain the wains and wave you through with warm blessings.\n"
                    "*** PICKET LINE PASSED! (+2 Reputation, +1 Charisma) ***"
                )
                return player, log, "MAIN"
            return player, "Your voice falters against the jeering crowd (Requires Charisma 2+, Influence 2+, or Acting Troupe)!", "CH2_TRIAL"

        if choice.startswith("Break through the barricade"):
            if player.get("strength", 0) >= 3 or player.get("chapter_2_route") == "Apply for Town Guard":
                player["active_ch2_trial"] = None
                completed.append(f"picket_{coord_tuple}")
                modify_faction(player, "faction_guard", 2)
                modify_faction(player, "faction_union", -2)
                set_region_territory(player, "Murum Farm" if coord_tuple == (8, 10) else "Fluvius Farm", "Guard")
                log = (
                    "You shatter the iron padlock on the hay-wains with a single heavy blow and order the highway cleared in the name of the Watch!\n"
                    "The strikers fall back muttering curses as you force the road open.\n"
                    "*** BARRICADE CLEARED BY FORCE! (+2 Guard Faction, -2 Union Faction | Farmland under GUARD PATROL!) ***"
                )
                return player, log, "MAIN"
            return player, "The heavy iron chain holds fast against your shoulder (Requires Strength 3+ or Town Guard authority)!", "CH2_TRIAL"

        if choice.startswith("Slip through the hedgerows"):
            if player.get("stealth", 0) >= 2:
                player["active_ch2_trial"] = None
                completed.append(f"picket_{coord_tuple}")
                player["stealth"] += 1
                return player, "Using the thick hawthorn hedges as cover, you slip past the picket line unseen! (+1 Stealth)", "MAIN"
            player["health"] -= 1
            return player, f"You get tangled in the thorny hawthorn hedge and are spotted by the lookouts! (-1 Health | HP: {player['health']})", "CH2_TRIAL"

    # ==================================================================
    # TRIAL 3 RESOLUTION: POOR WEATHER (BRUMAIRE STORM)
    # ==================================================================
    if trial == "trial_3_weather":
        player["active_ch2_trial"] = None

        if choice.startswith("Pitch your Canvas Tent"):
            player, _ = advance_time(60, player)
            return player, (
                "You quickly peg down your sturdy canvas tent against the howling wind and wait inside until the freezing squall passes.\n"
                "*** You weathered the storm warm and dry! (+60 mins) ***"
            ), "MAIN"

        if choice.startswith("Drink Spiced Cider"):
            drink = "spiced cider" if "spiced cider" in player["inventory"] else "vintage brumaire wine"
            player["inventory"].remove(drink)
            player["thirst"] = min(100, player["thirst"] + 50)
            return player, (
                f"You uncork your {drink.title()} and take a long, warming draught! The spiced warmth carries you briskly through the sleet without a shiver.\n"
                "*** Storm weathered unharmed! (+50 Thirst) ***"
            ), "MAIN"

        if choice.startswith("Spot a leeward rock"):
            return player, (
                "Reading the lay of the land, you duck beneath an overhanging limestone shelf until the worst of the freezing rain sweeps past.\n"
                "*** Storm weathered safely! ***"
            ), "MAIN"

        player, _ = advance_time(50, player)
        player["hunger"] = max(0, player["hunger"] - 15)
        player["thirst"] = max(0, player["thirst"] - 10)
        log = (
            "You bow your head into the freezing sleet and slog forward through the ankle-deep mud.\n"
            "The brutal gale saps your strength (-15 Hunger, -10 Thirst, +50 mins)!"
        )
        if random.random() < 0.45:
            chill_msg = infect_player(player, "damp_chill")
            if chill_msg:
                log += f"\n{chill_msg}"
        return player, log, "MAIN"

    # ==================================================================
    # TRIAL 4 RESOLUTION: BROKEN TRAVELLING CART (3 STAGES)
    # ==================================================================
    if trial == "trial_4_cart_stage_1":
        player["active_ch2_trial"] = "trial_4_cart_stage_2"
        food = next((f for f in ["carrot", "apple", "cobnuts", "sack of oats"] if f in player["inventory"]), None)

        if choice.startswith("Soothe the panicked horses") and (player.get("equusense", 0) >= 1 or "ride" in player.get("skills", [])):
            msg = "Speaking in a low, steady horseman's cadence, you calm the rearing team before they can snap the traces!"
        elif choice.startswith("Feed the team") and food:
            player["inventory"].remove(food)
            consume_fresh_food_timestamp(player, food)
            msg = f"You hold out {food} to the lead horse; the team immediately settles down and munches happily!"
        elif choice.startswith("Seize the bridles") and player.get("strength", 0) >= 2:
            msg = "You haul down on both leather bridles with iron-forged muscle, forcing the team to a standstill!"
        else:
            player["health"] -= 1
            msg = f"A panicked hoof clips your shin as you scramble to tie the horses to a roadside tree! (-1 Health | HP: {player['health']})"

        log = (
            f"{msg}\n\n"
            "*** STEP 2 OF 3: THE SUNKEN AXLE ***\n"
            "With the horses steady, you inspect the wagon: the rear axle is sunk deep in the mud. How do you lift the heavy bed?"
        )
        return player, log, "CH2_TRIAL"

    if trial == "trial_4_cart_stage_2":
        player["active_ch2_trial"] = "trial_4_cart_stage_3"
        has_lever = any(i in player["inventory"] for i in ["wooden club", "rope"]) or "climb" in player.get("skills", [])

        if choice.startswith("Heave the wagon bed") and player.get("strength", 0) >= 3:
            msg = "Bracing your boots in the mud, you deadlift the rear corner of the wagon bed and prop it on a flat stone!"
        elif choice.startswith("Rig a timber lever") and has_lever:
            msg = "Using clever leverage and a stout fulcrum stone, you pry the heavy axle cleanly out of the mud without straining your back!"
        elif choice.startswith("Rally passing travellers") and (player.get("charisma", 0) >= 2 or player.get("bandoka_joined")):
            helper = "Bandoka and two passing drovers" if player.get("bandoka_joined") else "Three passing drovers"
            msg = f"At your call, {helper} put their shoulders to the tailboard and heave the axle up onto dry stone!"
        else:
            player["hunger"] = max(0, player["hunger"] - 15)
            msg = "It takes a gruelling half-hour of straining and digging in the mud to prop the axle up (-15 Hunger)!"

        log = (
            f"{msg}\n\n"
            "*** STEP 3 OF 3: THE SHEARED LINCHPIN ***\n"
            "The wheel is back on the hub, but the iron linchpin is sheared in two. How do you secure the wheel?"
        )
        return player, log, "CH2_TRIAL"

    if trial == "trial_4_cart_stage_3":
        player["active_ch2_trial"] = None
        completed.append(f"broken_cart_{coord_tuple}")
        has_metal = "forge" in player.get("skills", []) or any(w in player["inventory"] or player.get("equipped_weapon") == w for w in ["iron dagger", "iron sword", "steel longsword", "masterwork steel longsword"])
        has_binding = any(i in player["inventory"] for i in ["rope", "leather", "halter"])

        if choice.startswith("Hammer a replacement") and has_metal:
            player["strength"] += 1
            player["reputation"] += 1
            return player, (
                "Using the pommel of your blade, you cold-hammer a spare iron bolt through the axle-hub—stronger than the day it left the wheelwright's shop!\n"
                "*** CART REPAIRED! (+1 Strength, +1 Reputation) ***"
            ), "MAIN"

        if choice.startswith("Lash the axle housing") and has_binding:
            bind_item = next(i for i in ["rope", "leather", "halter"] if i in player["inventory"])
            player["inventory"].remove(bind_item)
            player["reputation"] += 1
            return player, (
                f"You bind the axle-hub tightly with your {bind_item.title()} using a taut miller's hitch. The wheel rolls true!\n"
                "*** CART REPAIRED! (+1 Reputation) ***"
            ), "MAIN"

        if choice.startswith("Pay a passing tinker") and player["silver"] >= 10:
            player["silver"] -= 10
            return player, (
                f"You buy a forged iron linchpin from a passing tinker for 10 silver and tap it into place.\n"
                f"*** CART REPAIRED! (Remaining Silver: {player['silver']}s) ***"
            ), "MAIN"

        player, _ = advance_time(120, player)
        player["hunger"] = max(0, player["hunger"] - 20)
        player["thirst"] = max(0, player["thirst"] - 20)
        return player, (
            "With no pin or binding, you are forced to wedge a green stick into the hub and limp slowly down the road, stopping every hundred yards to hammer it back in.\n"
            "*** Exhausting delay! (+120 mins, -20 Hunger, -20 Thirst) ***"
        ), "MAIN"

    # ==================================================================
    # TRIAL 5 RESOLUTION: BROKEN CART BLOCKING THE PATH
    # ==================================================================
    if trial == "trial_5_blocked_cart":
        if choice == "Turn back the way you came":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You step back from the blocked defile.", "MAIN"

        reward_map = "fluvius town map" if coord_tuple == (2, 14) else "parvus town map"

        if choice.startswith("Heave & chock"):
            if player.get("strength", 0) >= 2 or "rope" in player["inventory"]:
                player["active_ch2_trial"] = None
                completed.append(f"blocked_cart_{coord_tuple}")
                player["silver"] += 15
                player["reputation"] += 1
                map_note = ""
                if reward_map not in player["inventory"]:
                    player["inventory"].append(reward_map)
                    map_note = f" and hands you a spare **{format_item_name(reward_map)}**"
                log = (
                    "You put your shoulder under the splintered axle, heave the cart level, and chock the wheel with flat stones so it can be rolled clear of the defile!\n"
                    f"The grateful merchant presses **15 silver** into your palm{map_note}!\n"
                    f"*** DEFILE CLEARED! (+15 Silver, +1 Reputation | Total Silver: {player['silver']}s) ***"
                )
                return player, log, "MAIN"
            return player, "The overloaded cart is too heavy to budge without more muscle (Strength 2+) or a Rope to rig a pulley!", "CH2_TRIAL"

        if choice.startswith("Calm & lead"):
            if player.get("equusense", 0) >= 2 or "halter" in player["inventory"] or "ride" in player.get("skills", []):
                player["active_ch2_trial"] = None
                completed.append(f"blocked_cart_{coord_tuple}")
                player["silver"] += 15
                player["equusense"] = player.get("equusense", 0) + 1
                map_note = ""
                if reward_map not in player["inventory"]:
                    player["inventory"].append(reward_map)
                    map_note = f" and gifts you a **{format_item_name(reward_map)}**"
                log = (
                    "You stroke the trembling draught horse's neck and unbuckle the twisted traces, leading the beast safely out of the bottleneck so the cart can be pivoted aside.\n"
                    f"The merchant thanks you warmly, pays you **15 silver**{map_note}!\n"
                    f"*** DEFILE CLEARED! (+15 Silver, +1 Equusense | Total Silver: {player['silver']}s) ***"
                )
                return player, log, "MAIN"
            return player, "The panicked draught horse snaps at your sleeve (Requires Equusense 2+, Ride, or a Halter)!", "CH2_TRIAL"

        if choice.startswith("Scale the rockface"):
            if "climb" in player.get("skills", []):
                player["active_ch2_trial"] = None
                completed.append(f"blocked_cart_{coord_tuple}")
                player["stealth"] += 1
                return player, (
                    "Finding narrow fingerholds in the volcanic rock, you climb smoothly over the ledge above the stalled cart and drop down on the open road beyond!\n"
                    "*** DEFILE BYPASSED! (+1 Stealth) ***"
                ), "MAIN"
            return player, "The rockface is too sheer to scale without the 'climb' skill!", "CH2_TRIAL"

        if choice.startswith("Rob the stranded merchant"):
            player["active_ch2_trial"] = None
            completed.append(f"blocked_cart_{coord_tuple}")
            player["silver"] += 25
            player["reputation"] -= 2
            player["inventory"].append("meat ration")
            log = (
                "While the merchant is pinned beneath the tilted tailboard, you help yourself to their lock-pouch (25 silver) and a cured Meat Ration before tipping the cart into the ditch to clear your path!\n"
                f"*** OUTLAW PLUNDER! (+25 Silver, +Meat Ration, -2 Reputation | Total Silver: {player['silver']}s) ***"
            )
            return player, log, "MAIN"

        if choice.startswith("Scramble through the thorny"):
            player["active_ch2_trial"] = None
            completed.append(f"blocked_cart_{coord_tuple}")
            player["health"] -= 2
            player, _ = advance_time(30, player)
            return player, (
                "You force your way through the bramble-choked ditch beside the cart. Razor-sharp thorns tear at your arms and cloak, but you emerge on the far side!\n"
                f"*** (-2 Health, +30 mins | Current HP: {player['health']}/{player['max_health']}) ***"
            ), "MAIN"

    # ==================================================================
    # TRIAL 6 RESOLUTION: RICKETY BRIDGE (MAX WEIGHT 15 LBS)
    # ==================================================================
    if trial == "trial_6_rickety_bridge":
        cache = player.setdefault("bridge_cache", [])

        if choice == "Step back from the bridge":
            while cache:
                player["inventory"].append(cache.pop())
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You reclaim your gear and step back from the swaying rope-bridge.", "MAIN"

        if choice.startswith("Dismount your horse"):
            player["riding_horse"] = False
            return player, "You climb down from the saddle and lead your horse by the reins.", "CH2_TRIAL"

        if choice.startswith("Stash heavy gear"):
            stashed_now = []
            while get_inventory_weight(player) > 15.0:
                inv_items = [i for i in player["inventory"] if i != "horse"]
                if inv_items:
                    heaviest = max(inv_items, key=lambda x: db.item_database.get(x, {}).get("weight", 0.2))
                    player["inventory"].remove(heaviest)
                    cache.append(heaviest)
                    stashed_now.append(format_item_name(heaviest))
                elif player.get("equipped_shield", "none") != "none":
                    sh = player["equipped_shield"]
                    player["equipped_shield"] = "none"
                    cache.append(sh)
                    stashed_now.append(format_item_name(sh))
                elif player.get("equipped_weapon", "fists") != "fists":
                    wp = player["equipped_weapon"]
                    player["equipped_weapon"] = "fists"
                    cache.append(wp)
                    stashed_now.append(format_item_name(wp))
                else:
                    break
            new_w = get_inventory_weight(player)
            stashed_str = ", ".join(stashed_now) if stashed_now else "nothing"
            return player, (
                f"You place {stashed_str} into the dry Riverbank Cache Box.\n"
                f"*** Your carry load is now **{new_w} lbs** (Safe limit: <= 15.0 lbs)! You can now cross and winch the bridge tight! ***"
            ), "CH2_TRIAL"

        if choice.startswith("Retrieve cached gear"):
            while cache:
                player["inventory"].append(cache.pop())
            new_w = get_inventory_weight(player)
            return player, f"You retrieve all your stashed gear from the Riverbank Cache. (Current Load: {new_w} lbs)", "CH2_TRIAL"

        if choice.startswith("Reinforce bridge cables"):
            while cache:
                player["inventory"].append(cache.pop())
            if "rope" in player["inventory"]:
                player["inventory"].remove("rope")
            player["active_ch2_trial"] = None
            completed.append(f"bridge_reinforced_{coord_tuple}")
            player["reputation"] += 1
            return player, (
                "You lash fresh stays across the rotten main-cables and wedge oak struts beneath the sagging pier!\n"
                "The bridge is now rock-solid (Max Load raised to 50 lbs) and all your gear is safely back in your pack!\n"
                "*** BRIDGE REINFORCED! (+1 Reputation) ***"
            ), "MAIN"

        if choice.startswith("Cross the Rickety Bridge now"):
            curr_w = get_inventory_weight(player)
            if curr_w <= 15.0 and not player.get("riding_horse"):
                reclaimed_note = ""
                if cache:
                    while cache:
                        player["inventory"].append(cache.pop())
                    reclaimed_note = "\nOnce on the far bank, you crank the iron tension-winch to lock the bridge cables taut, then walk back across the steadied planks to collect your stashed gear from the Riverbank Cache!"
                player["active_ch2_trial"] = None
                completed.append(f"bridge_reinforced_{coord_tuple}")
                return player, (
                    f"Moving lightly ({curr_w} lbs <= 15.0 lbs), you step carefully across the creaking oak planks and reach the far bank of the River Fluvius!{reclaimed_note}\n"
                    "*** BRIDGE CROSSED & STABILIZED! ***"
                ), "MAIN"
            else:
                while cache:
                    player["inventory"].append(cache.pop())
                player["active_ch2_trial"] = None
                player["riding_horse"] = False
                player["health"] -= 3
                downstream = (5, 8) if coord_tuple == (6, 9) else (11, 18)
                player["x"], player["y"] = downstream
                lost_note = ""
                if "swim" not in player.get("skills", []):
                    droppable = [i for i in player["inventory"] if db.item_database.get(i, {}).get("price", 0) > 0]
                    if droppable:
                        lost_item = random.choice(droppable)
                        player["inventory"].remove(lost_item)
                        lost_note = f"\nIn the churning white-water, you lose your **{format_item_name(lost_item)}** to the current!"
                else:
                    lost_note = "\nThanks to your 'swim' skill, you keep a tight grip on all your gear as you kick to the bank!"
                return player, (
                    f"*** SNAP! ({curr_w} lbs > 15.0 lbs limit!) ***\n"
                    "The rotted cross-planks give way beneath your weight! You plunge into the icy rapids of the River Fluvius and are swept downstream before hauling yourself onto the muddy reeds!\n"
                    f"*** (-3 Health | Current HP: {player['health']}/{player['max_health']}){lost_note} ***"
                ), "MAIN"

    # ==================================================================
    # TRIAL 7 RESOLUTION: LOCKED GATE & ABANDONED GATEHOUSE
    # ==================================================================
    if trial == "trial_7_locked_gate":
        if choice == "Step back from the locked gate":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You step back from the locked iron portcullis.", "MAIN"

        if choice == "Read the Gatekeeper's Logbook on the desk":
            player["gate_logbook_read"] = True
            log = (
                "--- GATEKEEPER'S LOGBOOK (ENTRY 44) ---\n"
                "\"Robbers and syndicalists prowling the roads again. Before abandoning the post, I locked the iron portcullis and hid the **Heavy Gate-Key** in the damp hollow beneath the **mossy cistern stone**.\"\n"
                "\"WARNING TO RELIEF WATCHMEN: Do NOT reach up the **chimney flue**—a nest of venomous soot-adders has moved into the brickwork!\""
            )
            return player, log, "CH2_TRIAL"

        if choice == "Reach up inside the dark chimney flue":
            player["health"] -= 2
            return player, (
                "*** HISS! ***\n"
                "You thrust your hand up into the dark chimney flue and a nesting soot-adder sinks its fangs into your wrist!\n"
                f"*** (-2 Health | Current HP: {player['health']}/{player['max_health']}) — Maybe you should read the Gatekeeper's Logbook on the desk first! ***"
            ), "CH2_TRIAL"

        if choice == "Search beneath the mossy cistern stone":
            player["gate_key_found"] = True
            if not player.get("gate_cistern_looted"):
                player["gate_cistern_looted"] = True
                player["silver"] += 12
                coin_msg = " along with an oiled pouch containing **12 silver coins**"
            else:
                coin_msg = ""
            return player, (
                f"You heave aside the mossy cistern slab and pull out a heavy **Iron Portcullis Key**{coin_msg}!\n"
                "*** Click 'Unlock the Iron Portcullis with the Heavy Gate-Key!' to open the road! ***"
            ), "CH2_TRIAL"

        if choice in [
            "Unlock the Iron Portcullis with the Heavy Gate-Key!",
            "Scale the archway & release the winch from inside (Climb / Grappling Hook)",
            "Shatter the rusted lock-bolt (Masonry Drill / Forge)"
        ]:
            player["active_ch2_trial"] = None
            player["gate_key_found"] = False
            completed.append(f"locked_gate_{coord_tuple}")
            bandoka_clue = ""
            if player.get("bandoka_joined"):
                player.setdefault("bandoka_clues_spotted", [])
                if "lock_slip" not in player["bandoka_clues_spotted"]:
                    player["bandoka_clues_spotted"].append("lock_slip")
                bandoka_clue = (
                    "\n\n(Subtle Clue: As the portcullis rises, you notice Bandoka effortlessly resetting the military counter-weights on the Castellan's winch—a mechanism only trained Castle Laydere sappers and Crown agents know how to operate...)"
                )
            return player, (
                "With a deep, echoing groan of iron chains, the heavy portcullis rises into the stone archway! The road ahead is wide open."
                f"{bandoka_clue}\n*** PORTCULLIS GATE UNLOCKED! ***"
            ), "MAIN"

    # ==================================================================
    # TRIAL 8 RESOLUTION: SPREADING HEATH FIRE & DANGEROUS SMOKE
    # ==================================================================
    if trial == "trial_8_heath_fire":
        if choice == "Retreat back the way you came":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You retreat upwind from the crackling gorse fire.", "MAIN"

        if choice.startswith("Read the wind direction"):
            player["active_ch2_trial"] = None
            completed.append(f"heath_fire_{coord_tuple}")
            player, _ = advance_time(30, player)
            return player, (
                "Watching the slant of the heather and the drift of the embers, you chart a path along the windward granite ridge where the sea-breeze blows the choking smoke away from your lungs.\n"
                "*** HEATH FIRE BYPASSED SAFELY! (+30 mins) ***"
            ), "MAIN"

        if choice.startswith("Soak a cloth from your Water Flask"):
            if "full water flask" in player["inventory"]:
                player["inventory"].remove("full water flask")
                player["inventory"].append("half-full water flask")
            elif "half-full water flask" in player["inventory"]:
                player["inventory"].remove("half-full water flask")
                player["inventory"].append("empty flask")
            player["active_ch2_trial"] = None
            completed.append(f"heath_fire_{coord_tuple}")
            return player, (
                "You douse your kerchief from your water flask, bind it tightly across your nose and mouth, and push straight through the billowing smoke without inhaling a single lungful of ash!\n"
                "*** CROSSED THROUGH THE SMOKE UNHARMED! ***"
            ), "MAIN"

        if choice.startswith("Dig a firebreak"):
            if player.get("strength", 0) >= 2 or "bucket of sand" in player["inventory"]:
                if "bucket of sand" in player["inventory"]:
                    player["inventory"].remove("bucket of sand")
                player["active_ch2_trial"] = None
                completed.append(f"heath_fire_{coord_tuple}")
                player["silver"] += 20
                player["reputation"] += 2
                player["inventory"].append("wheel of aged cheese")
                return player, (
                    "Seizing a turf-spade beside the sheepfold, you hack a wide firebreak trench across the peat and smother the leading edge of the burning gorse before it can reach the penned flock!\n"
                    "The Heath Shepherd weeps with gratitude, pressing **20 silver** and a **Wheel of Aged Cheese** into your hands!\n"
                    f"*** HEATH FIRE EXTINGUISHED! (+20 Silver, +2 Reputation, +Wheel of Aged Cheese | Total Silver: {player['silver']}s) ***"
                ), "MAIN"
            return player, "Beating back the blazing gorse requires Strength 2+ or a Bucket of Sand!", "CH2_TRIAL"

        if choice.startswith("Sprint blindly through"):
            player["active_ch2_trial"] = None
            completed.append(f"heath_fire_{coord_tuple}")
            player["health"] -= 3
            player, _ = advance_time(50, player)
            return player, (
                "Coughing violently, you lower your head and sprint blindly through the searing black smoke! Flying embers scorch your cloak and the acrid fumes burn your lungs.\n"
                f"*** (-3 Health, +50 mins | Current HP: {player['health']}/{player['max_health']}) ***"
            ), "MAIN"

    # ==================================================================
    # TRIAL 9 RESOLUTION: UNMASKING BANDOKA THE DOUBLE AGENT
    # ==================================================================
    if trial == "trial_9_bandoka":
        player["active_ch2_trial"] = None
        completed.append("trial_9_bandoka")

        if choice.startswith("Expose ") or choice.startswith("Slip falsified dispatches"):
            player["bandoka_joined"] = False
            db.npc_database["bandoka"]["location"] = None
            player["silver"] += 30
            player["influence"] = player.get("influence", 0) + 2
            player["stealth"] = player.get("stealth", 0) + 1
            player["reputation"] += 2
            if "bandoka's cipher" not in player["inventory"]:
                player["inventory"].append("bandoka's cipher")

            if choice.startswith("Slip falsified dispatches"):
                method_desc = (
                    "With practiced sleight of hand, you swap your real credentials for a decoy packet filled with false troop movements.\n"
                    "When Bandoka reaches for their blade, you reveal that their courier pigeon is already carrying your trap straight to their masters!"
                )
            else:
                method_desc = (
                    "You coldly lay out every contradiction in Bandoka's story—the 7:50 curfew lock at Murum Gate, the yellow Caligo mountain clay on their boots, and their sapper's training.\n"
                    "Realizing their cover is completely blown and you are ready for their blade, Bandoka curses and backs away!"
                )

            log = (
                f"{method_desc}\n\n"
                "To buy their escape, Bandoka tosses you their **Coded Cipher Cylinder** and a heavy purse of **30 silver** before vaulting into the roadside brush!\n"
                f"*** DOUBLE AGENT UNMASKED! (+30 Silver, +Bandoka's Cipher, +2 Influence, +1 Stealth, +2 Reputation | Total Silver: {player['silver']}s) ***"
            )
            return player, log, "MAIN"

        if choice == "Draw your weapon and fight Bandoka!":
            return encounters.trigger_bandoka_combat(player)

        # Trusted Bandoka blindly -> Ambushed!
        loss = min(player["silver"], 15)
        player["silver"] -= loss
        player["health"] -= 2
        p, c_log, st = encounters.trigger_bandoka_combat(player)
        betray_intro = (
            f"You hand over your satchel—and Bandoka immediately slashes at your ribs (-2 Health, -{loss} Silver stolen) with a hidden stiletto!\n"
            "\"Too trusting for the frontier, Noburu!\"\n\n"
        )
        return p, betray_intro + c_log, st

    # ==================================================================
    # TRIAL 10 RESOLUTION: RIVER BREAKS ITS BANKS & CAUSES FLOODING
    # ==================================================================
    if trial == "trial_10_flood":
        if choice == "Pull back to higher ground":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You retreat to higher ground above the swirling floodwater.", "MAIN"

        if choice.startswith("Haul sandbags"):
            if player.get("strength", 0) >= 2 or "bucket of sand" in player["inventory"] or "rope" in player["inventory"]:
                if "bucket of sand" in player["inventory"]:
                    player["inventory"].remove("bucket of sand")
                player["active_ch2_trial"] = None
                completed.append(f"river_flood_{coord_tuple}")
                player["silver"] += 20
                player["reputation"] += 2
                modify_faction(player, "faction_union", 2)
                return player, (
                    "Working shoulder-to-shoulder with the Fluvius farmhands, you drive timber stakes into the gap and stack heavy sandbags until the levee holds!\n"
                    "The floodwaters recede from the road, and the grateful bailiff pays you **20 silver**!\n"
                    f"*** LEVEE REPAIRED! (+20 Silver, +2 Reputation, +2 Union Faction | Total Silver: {player['silver']}s) ***"
                ), "MAIN"
            return player, "Holding back the surging breach requires Strength 2+, Rope, or a Bucket of Sand!", "CH2_TRIAL"

        if choice.startswith("Cut a diversion sluice"):
            if "masonry drill" in player["inventory"] or "forge" in player.get("skills", []) or player.get("faction_wallmakers", 0) >= 3:
                player["active_ch2_trial"] = None
                completed.append(f"river_flood_{coord_tuple}")
                player["silver"] += 20
                modify_faction(player, "faction_wallmakers", 2)
                return player, (
                    "Using surveyor's engineering, you bore out the jammed stone culvert and cut a clean drainage sluice that channels the floodwater harmlessly back into the river channel!\n"
                    f"*** FLOOD DRAINED! (+20 Silver, +2 Wallmakers Faction | Total Silver: {player['silver']}s) ***"
                ), "MAIN"
            return player, "Cutting a stone diversion sluice requires a Masonry Drill, the Forge skill, or Wallmaker expertise!", "CH2_TRIAL"

        if choice.startswith("Swim across"):
            player["active_ch2_trial"] = None
            completed.append(f"river_flood_{coord_tuple}")
            return player, "Using strong, steady strokes, you swim across the flooded road section and haul yourself up onto dry cobbles beyond!", "MAIN"

        if choice.startswith("Ride your mount"):
            player["active_ch2_trial"] = None
            completed.append(f"river_flood_{coord_tuple}")
            return player, "Your sturdy mount powers through the swirling current without losing its footing, carrying you safely across the floodzone!", "MAIN"

        if choice.startswith("Wade chest-deep"):
            player["active_ch2_trial"] = None
            completed.append(f"river_flood_{coord_tuple}")
            player["health"] -= 2
            player, _ = advance_time(40, player)
            return player, (
                "You slog chest-deep through the freezing, debris-choked floodwater! The icy current batters your legs and chills you to the bone, but you reach the far bank.\n"
                f"*** (-2 Health, +40 mins | Current HP: {player['health']}/{player['max_health']}) ***"
            ), "MAIN"

    # ==================================================================
    # TRIAL 11 RESOLUTION: SUNKEN TREASURE IN THE LAKE (3 STAGES)
    # ==================================================================
    if trial == "trial_11_lake_stage_1":
        if choice.startswith("Step back from the water"):
            player["active_ch2_trial"] = None
            return player, "You step back onto the dry jetty, leaving the sunken strongbox beneath the waves for now.", "MAIN"

        if choice.startswith("Dive smoothly"):
            cost = 0
            msg = "With a swimmer's streamlined dolphin-kick, you glide twenty feet down to the lakebed without wasting a single breath!"
        elif choice.startswith("Tie a Rope"):
            cost = 1
            player["lake_rope_tied"] = True
            msg = "You knot your Rope around the jetty bollard and slide down the taut line to the lakebed!"
        else:
            cost = 1
            msg = "Clutching a heavy ballast stone to your chest, you sink rapidly to the silty bottom!"

        player["lake_breath"] = player.get("lake_breath", 3) - cost
        player["active_ch2_trial"] = "trial_11_lake_stage_2"
        return player, (
            f"{msg}\n"
            f"• Remaining Lung Capacity: **{player['lake_breath']} Breath**\n\n"
            "*** STAGE 2 OF 3 (THE SUBMERGED STRONGBOX): ***\n"
            "The iron-bound chest is tangled in thick, waterlogged oak roots on the bottom. How do you free it?"
        ), "CH2_TRIAL"

    if trial == "trial_11_lake_stage_2":
        has_tool = any(w in player["inventory"] or player.get("equipped_weapon") == w for w in ["iron dagger", "iron sword", "steel longsword", "masterwork steel longsword", "masonry drill"])
        if choice.startswith("Pry the strongbox") and has_tool:
            cost = 1
            msg = "You wedge your steel blade under the root-knot and slice the chest free in one clean stroke!"
        elif choice.startswith("Wrench the drowned") and player.get("strength", 0) >= 3:
            cost = 1
            msg = "Bracing your boots against the lakebed stones, you rip the rotten oak roots apart with raw muscle!"
        else:
            cost = 2
            msg = "Without a prying blade or high strength, you burn precious air wrenching at the stubborn roots with both hands!"

        player["lake_breath"] = player.get("lake_breath", 2) - cost
        if player["lake_breath"] <= 0:
            player["active_ch2_trial"] = None
            player["health"] -= 3
            return player, (
                f"{msg}\n\n"
                "*** OUT OF BREATH! ***\n"
                "Your lungs burn like fire! Forced to let go of the heavy chest, you kick frantically for the surface and drag yourself onto the bank, coughing up lake water!\n"
                f"*** (-3 Health | Current HP: {player['health']}/{player['max_health']}) — Catch your breath and try again when ready! ***"
            ), "MAIN"

        player["active_ch2_trial"] = "trial_11_lake_stage_3"
        return player, (
            f"{msg}\n"
            f"• Remaining Lung Capacity: **{player['lake_breath']} Breath**\n\n"
            "*** STAGE 3 OF 3 (THE ASCENT): ***\n"
            "You have the heavy strongbox in your arms, but your lungs are aching for air! How do you surface?"
        ), "CH2_TRIAL"

    if trial == "trial_11_lake_stage_3":
        if choice.startswith("Haul yourself straight up") and player.get("lake_rope_tied"):
            cost = 0
            msg = "Hand over hand along your knotted guide-rope, you haul yourself and the chest rapidly into the sunlight!"
        elif choice.startswith("Drop ballast") and ("swim" in player.get("skills", []) or player.get("strength", 0) >= 2):
            cost = 1
            msg = "Kicking off the bottom with powerful strokes, you shoot upward through the shimmering water!"
        else:
            cost = 2
            msg = "Weighted down by the iron chest, you thrash desperately toward the surface!"

        player["lake_breath"] = player.get("lake_breath", 1) - cost
        player["active_ch2_trial"] = None

        if player["lake_breath"] < 0:
            player["health"] -= 3
            return player, (
                f"{msg}\n\n"
                "*** NEAR-DROWNING! ***\n"
                "Just yards from the surface, your vision dims and the heavy chest slips from your numb fingers back into the deep as you gasp air at the bank!\n"
                f"*** (-3 Health | Current HP: {player['health']}/{player['max_health']}) ***"
            ), "MAIN"

        completed.append(f"lake_treasure_{coord_tuple}")
        player["silver"] += 35
        player["reputation"] += 2
        if "ancient castellan signet" not in player["inventory"]:
            player["inventory"].append("ancient castellan signet")
        bonus_map = "lignum forest map" if coord_tuple == (9, 20) else "caligo mountains map"
        map_str = ""
        if bonus_map not in player["inventory"]:
            player["inventory"].append(bonus_map)
            map_str = f", an oiled **{format_item_name(bonus_map)}**"
        return player, (
            f"{msg}\n\n"
            "*** SUNKEN TREASURE RECOVERED! ***\n"
            f"On the bank, you pry open the barnacle-crusted strongbox to find **35 silver coins**, an **Ancient Castellan Signet**{map_str}!\n"
            f"*** (+35 Silver, +Ancient Castellan Signet, +2 Reputation | Total Silver: {player['silver']}s) ***"
        ), "MAIN"

    # ==================================================================
    # TRIAL 12 RESOLUTION: THE SAGE OF THE MOUNTAINS (3 QUESTIONS)
    # ==================================================================
    if trial == "trial_12_sage_q1":
        if choice == "Step back from the observatory":
            player["active_ch2_trial"] = None
            return player, "You bow respectfully to Master Spotted Tail and step back onto the mountain ledge.", "MAIN"

        if "buy another person's labour" in choice:
            player["sage_mistakes"] = player.get("sage_mistakes", 0) + 1
            reply = "Master Spotted Tail frowns slightly. \"A merchant's answer. Gold can rent a person's hands, but never the truth of their hours.\""
        else:
            reply = "Master Spotted Tail nods slowly. \"Well spoken. Time belongs to the living who inhabit it, not the clock-face on the Guild wall.\""

        player["active_ch2_trial"] = "trial_12_sage_q2"
        log = (
            f"{reply}\n\n"
            "*** QUESTION 2 OF 3: THE GREAT SCHISM ***\n"
            "\"Below these peaks, the townsfolk clear-cut Lignum Forest for farmland, splitting the woodland creatures into militant Vanguardists and peaceful Communards. How can the forest and the plough endure together?\""
        )
        return player, log, "CH2_TRIAL"

    if trial == "trial_12_sage_q2":
        if "burning the woods down" in choice:
            player["sage_mistakes"] = player.get("sage_mistakes", 0) + 1
            reply = "Spotted Tail's eyes flash with warning. \"He who rules ashes rules a graveyard, traveller.\""
        else:
            reply = "Spotted Tail smiles warmly. \"Indeed. Only when the townsfolk restrain their appetite can the furrow and the forest breathe the same air.\""

        player["active_ch2_trial"] = "trial_12_sage_q3"
        log = (
            f"{reply}\n\n"
            "*** QUESTION 3 OF 3: THE TWO CASTELLANS ***\n"
            "\"Ceara at Castle Ragmore and Castellan Ironbough at Castle Laydere sharpen their lances while their subjects starve. What is the true measure of a leader?\""
        )
        return player, log, "CH2_TRIAL"

    if trial == "trial_12_sage_q3":
        if "Crushing every rival" in choice:
            player["sage_mistakes"] = player.get("sage_mistakes", 0) + 1

        mistakes = player.get("sage_mistakes", 0)
        player["active_ch2_trial"] = None

        if mistakes >= 2:
            return player, (
                "Master Spotted Tail sets down their tea cup and rises.\n"
                "\"Your heart is still clouded by the greed and tyranny of the lowland courts, traveller. Walk the mountains, reflect, and return when you seek wisdom rather than dominion.\"\n"
                "*** Trial Incomplete (2+ arrogant answers) — Speak to Master Spotted Tail to try again! ***"
            ), "MAIN"

        completed.append("trial_12_sage")
        player["health"] = player["max_health"]
        player["hunger"] = 100
        player["thirst"] = 100
        player["charisma"] += 2
        player["influence"] = player.get("influence", 0) + 2
        player["reputation"] += 2
        if "sage's charter" not in player["inventory"]:
            player["inventory"].append("sage's charter")
        if "caligo mountains map" not in player["inventory"]:
            player["inventory"].append("caligo mountains map")

        return player, (
            "Master Spotted Tail bows deeply and presses a wax-sealed parchment scroll and a topographical chart into your hands.\n"
            "\"You see clearly through the fog of Dtessera Terra, Noburu. Carry my **Sage's Charter** and this **Caligo Mountains Map**—when you stand before the factions and Castellans at the end of your journey, my seal will lend weight to your voice.\"\n"
            "*** SAGE'S TRIAL COMPLETED! (+Sage's Charter, +Caligo Mountains Map, +2 Charisma, +2 Influence, +2 Reputation, Full HP/Hunger/Thirst!) ***"
        ), "MAIN"

    # ==================================================================
    # TRIAL 13 RESOLUTION: MOUFLIN ENCOUNTER
    # ==================================================================
    if trial == "trial_13_mouflin":
        if choice == "Back down the mountain trail":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You back slowly down the narrow mountain ledge.", "MAIN"

        if choice.startswith("Offer Cobnuts/Carrot"):
            treat = next(f for f in ["cobnuts", "carrot", "apple"] if f in player["inventory"])
            player["inventory"].remove(treat)
            consume_fresh_food_timestamp(player, treat)
            player["active_ch2_trial"] = None
            completed.append("trial_13_mouflin")
            player["equusense"] = player.get("equusense", 0) + 1
            if "mouflin" not in player["inventory"]:
                player["inventory"].append("mouflin")
            return player, (
                f"You kneel on the slate ledge and offer the {treat}. The massive Alpha Mouflin steps forward, crunches the treat from your palm, and butts your shoulder affectionately!\n"
                "*** MOUFLIN TAMED! The Alpha Mouflin joins you as a mountain mount! (+1 Equusense | Use 'Action -> Mount / Dismount' to ride the Mouflin across Mountain crags without needing to climb!) ***"
            ), "MAIN"

        if choice.startswith("Bow your head") or choice.startswith("Loose a warning") or choice.startswith("Scramble along"):
            player["active_ch2_trial"] = None
            completed.append("trial_13_mouflin")
            player["reputation"] += 1
            return player, (
                "The Alpha Mouflin snorts and leads its herd up the high crags, leaving the mountain pass clear for you!\n"
                "*** MOUNTAIN PASS CLEARED! (+1 Reputation) ***"
            ), "MAIN"

        if choice.startswith("Draw weapon"):
            player["active_ch2_trial"] = None
            completed.append("trial_13_mouflin")
            player["active_enemy"] = {
                "id": "mouflin_ram",
                "name": "Alpha Mouflin Ram",
                "health": 18,
                "flee_damage": 3,
                "attack_min": 2,
                "attack_max": 6,
                "attack_verb": "The Alpha Mouflin Ram charges with its iron-hard spiral horns, battering you",
                "defeat_msg": "You drive off the Alpha Mouflin Ram and harvest a prime cut of mountain venison! (+Meat Ration)",
                "flee_msg": "You scramble down the scree as the ram butts your shield! (-{dmg} Health)"
            }
            player["inventory"].append("meat ration")
            return player, "The Alpha Mouflin lowers its spiral horns and charges!", "COMBAT"

    # ==================================================================
    # TRIAL 15 RESOLUTION: SINGLE-TUPLE BRIAR-MAZE DUNGEON AT (8, 20)
    # ==================================================================
    if trial == "trial_15_maze":
        if choice == "Retreat out of the Briar-Labyrinth":
            player["active_ch2_trial"] = None
            return player, "You retrace your steps out of the blackthorn archway.", "MAIN"

        rm = player.get("maze_room", 0)
        if choice.startswith("Use your Compass"):
            hints = [
                "Your Compass & Lore confirm: Lichen grows where fresh air flows—take the **Northern Arch**!",
                "Follow the sound of **trickling spring-water (West)** toward the glade!",
                "Violets only bloom in sweet woodland soil—duck beneath the **South-East arch**!",
                "Step between the **twin standing stones** into the sunlit glade!"
            ]
            return player, f"*** PATHFINDING INSIGHT: {hints[rm]} ***", "CH2_TRIAL"

        correct_picks = [
            "Take the Northern Arch",
            "Follow the sound of trickling spring-water",
            "Duck beneath the arch where purple violets bloom",
            "Step between the twin standing stones"
        ]
        if choice.startswith(correct_picks[rm]):
            if rm == 0:
                player["maze_room"] = 1
                return player, (
                    "You slip cleanly through the lichen-draped arch into **CHAMBER 2 (THE ECHOING HOLLOW)**!\n"
                    "• To the **West**, you hear the faint trickle of clear spring-water.\n"
                    "• To the **North**, snapped deadwood twigs litter a dark cul-de-sac.\n"
                    "• To the **East**, rank mud marks a wild boar wallow."
                ), "CH2_TRIAL"
            elif rm == 1:
                player["maze_room"] = 2
                return player, (
                    "Following the sound of running water, you enter **CHAMBER 3 (THE BRIAR CROWN)**!\n"
                    "• To the **South-East**, sweet purple violets bloom beneath a low thorn-arch.\n"
                    "• To the **North**, toxic pale nightshade chokes the path.\n"
                    "• To the **West**, animal bones litter a dry hollow."
                ), "CH2_TRIAL"
            elif rm == 2:
                player["maze_room"] = 3
                return player, (
                    "You duck beneath the violet arch and reach **CHAMBER 4 (THE INNER SANCTUM GATE)**!\n"
                    "• Ahead stand **twin moss-carved standing stones** opening into a sunlit sanctuary.\n"
                    "• To the side, circling crow-shadows wind back into the dark briars."
                ), "CH2_TRIAL"
            else:
                player["active_ch2_trial"] = None
                completed.append("trial_15_maze")
                player["silver"] += 25
                player["reputation"] += 2
                if "lignum forest map" not in player["inventory"]:
                    player["inventory"].append("lignum forest map")
                return player, (
                    "*** BRIAR-LABYRINTH CONQUERED! ***\n"
                    "You step between the twin standing stones into the hidden sanctuary of Diluvium Glade!\n"
                    "Resting inside a dry stone cairn at the centre of the glade, you discover a surveyor's **Lignum Forest Map** and **25 silver coins**!\n"
                    f"*** (+25 Silver, +Lignum Forest Map, +2 Reputation | Total Silver: {player['silver']}s) ***"
                ), "MAIN"
        else:
            player["health"] -= 1
            player["maze_room"] = 0
            player, _ = advance_time(25, player)
            return player, (
                "*** DEAD END OF THORNS! ***\n"
                "The tunnel twists into a wall of razor-sharp blackthorn that tears at your cloak (-1 Health, +25 mins) and loops you right back to **CHAMBER 1**!\n"
                f"(Current HP: {player['health']}/{player['max_health']})"
            ), "CH2_TRIAL"

    # ==================================================================
    # TRIAL 16 RESOLUTION: WILD ANIMAL ATTACK
    # ==================================================================
    if trial == "trial_16_wild_beast":
        player["active_ch2_trial"] = None
        b_name = player.get("active_beast_name", "Wild Beast")

        if choice.startswith("Loose a first-strike arrow"):
            player["inventory"].append("meat ration")
            player["inventory"].append("leather")
            return player, (
                f"Your longbow sings! The arrow strikes the lead {b_name} in mid-bound, sending the pack fleeing into the brush while leaving behind a prime hide and meat!\n"
                "*** WILD BEAST FELLED VIA ARCHERY! (+Meat Ration, +Leather) ***"
            ), "MAIN"

        if choice.startswith("Toss dried meat"):
            for m in ["meat ration", "fish jerky"]:
                if m in player["inventory"]:
                    player["inventory"].remove(m)
                    break
            player["equusense"] = player.get("equusense", 0) + 1
            modify_faction(player, "faction_communards", 1)
            return player, (
                f"You toss a piece of cured meat and hold a non-threatening posture. The {b_name} sniffs the offering, takes it, and melts peacefully back into the wilds!\n"
                "*** BEAST PACIFIED! (+1 Equusense, +1 Communards Faction) ***"
            ), "MAIN"

        if choice.startswith("Scramble up a boulder"):
            player["hunger"] = max(0, player["hunger"] - 15)
            player, _ = advance_time(30, player)
            return player, f"You haul yourself atop a high boulder until the {b_name} loses interest and wanders off. (-15 Hunger, +30 mins)", "MAIN"

        player["active_enemy"] = {
            "id": "wild_beast",
            "name": b_name,
            "health": 15,
            "flee_damage": 3,
            "attack_min": 2,
            "attack_max": 5,
            "attack_verb": f"The {b_name} lunges with snapping jaws and tusks, tearing at you",
            "defeat_msg": f"You slay the attacking {b_name} and butcher a fresh Meat Ration!",
            "flee_msg": f"You sprint away as the {b_name} nips at your heels! (-{{dmg}} Health)"
        }
        player["inventory"].append("meat ration")
        return player, f"You brace your feet and raise your weapon against the {b_name}!", "COMBAT"

    # ==================================================================
    # TRIAL 17 RESOLUTION: BOTANICAL FORAGING PUZZLE
    # ==================================================================
    if trial == "trial_17_forage":
        if choice == "Leave the wild plants alone":
            player["active_ch2_trial"] = None
            return player, "You decide not to risk eating unfamiliar wild plants.", "MAIN"

        if choice.startswith("Use Foraging Lore"):
            hint = (
                "Cluster A (**Golden Chanterelles**) is delicious and safe; Cluster B is the deadly **Death-Cap**!"
                if player.get("forage_variant") == "mushrooms"
                else "Shrub A (**Sweet Bilberries**) is wholesome; Shrub B is toxic **Deadly Nightshade**!"
            )
            return player, f"*** BOTANICAL INSIGHT: {hint} ***", "CH2_TRIAL"

        player["active_ch2_trial"] = None
        if choice.startswith("Harvest Cluster A") or choice.startswith("Harvest Shrub A"):
            player["hunger"] = min(100, player["hunger"] + 30)
            player["thirst"] = min(100, player["thirst"] + 15)
            player["inventory"].append("cobnuts")
            return player, (
                "You gather a generous handful of the wholesome wild forage! It is fresh and revitalizing, and you also pocket a handful of wild **Cobnuts**.\n"
                "*** SAFE FORAGE! (+30 Hunger, +15 Thirst, +Cobnuts) ***"
            ), "MAIN"
        else:
            player["hunger"] = min(100, player["hunger"] + 5)
            inf_msg = infect_player(player, "food_poisoning") or ""
            return player, (
                "The moment you swallow a mouthful, a bitter, burning numbness spreads across your tongue—you ate the toxic lookalike!\n"
                f"{inf_msg}"
            ), "MAIN"

    # ==================================================================
    # TRIAL 18 RESOLUTION: BUILD A BRIDGE (3 STEPS)
    # ==================================================================
    if trial == "trial_18_bridge_s1":
        if choice == "Step back from the gorge":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You step back from the washed-out gorge.", "MAIN"

        if choice.startswith("Climb down"):
            player["health"] -= 1
            msg = f"You scrape your knees (-1 Health | HP: {player['health']}) scrambling through the foaming boulders, but secure a guide-line to the far pier!"
        else:
            msg = "You send the guide-line cleanly across the chasm and anchor it fast to the stone pier!"

        player["active_ch2_trial"] = "trial_18_bridge_s2"
        return player, f"{msg}\n\n*** STEP 2 OF 3 (THE MAIN STRINGERS): How do you span the 15-foot gap with heavy pine trunks? ***", "CH2_TRIAL"

    if trial == "trial_18_bridge_s2":
        if choice.startswith("Strain with bare hands"):
            player["hunger"] = max(0, player["hunger"] - 15)
        player["active_ch2_trial"] = "trial_18_bridge_s3"
        return player, (
            "The two massive pine stringers boom into place across the stone abutments!\n\n"
            "*** STEP 3 OF 3 (THE DECKING): How do you lock the cross-planks so the bridge holds permanently? ***"
        ), "CH2_TRIAL"

    if trial == "trial_18_bridge_s3":
        player["active_ch2_trial"] = None
        completed.append(f"built_bridge_{coord_tuple}")
        player["strength"] += 1
        player["reputation"] += 2
        return player, (
            "You lock the cross-timbers tightly across the pine stringers! Your newly built timber bridge spans the gorge—opening a permanent dry shortcut across the River Fluvius!\n"
            "*** BRIDGE BUILT! (+1 Strength, +2 Reputation) ***"
        ), "MAIN"

    # ==================================================================
    # TRIAL 19 RESOLUTION: REPAIR A PATH (THE ROCKSLIDE PASS)
    # ==================================================================
    if trial == "trial_19_rockslide":
        if choice == "Step back from the rockslide":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You step back from the rockslide.", "MAIN"

        if choice.startswith("1st: Clear the Lower Culvert") or choice.startswith("Use Masonry Drill"):
            player["active_ch2_trial"] = None
            completed.append(f"repaired_path_{coord_tuple}")
            player["silver"] += 15
            player["strength"] += 1
            player["reputation"] += 1
            return player, (
                "By draining the mud-clogged culvert first and levering the Keystone Boulder from the side, the entire rockslide rumbles harmlessly down into the ravine!\n"
                "Glinting in the freshly exposed rock-seam, you also pocket **15 silver** worth of native silver ore!\n"
                f"*** PATH REPAIRED! (+15 Silver, +1 Strength, +1 Reputation | Silver: {player['silver']}s) ***"
            ), "MAIN"
        else:
            player["health"] -= 3
            return player, (
                "*** RUMBLE! SECONDARY ROCKFALL! ***\n"
                "Disturbing the unstable shale before draining the culvert triggers a cascade of heavy stones that batters your shoulders (-3 Health)!\n"
                f"(Current HP: {player['health']}/{player['max_health']} — Clear the Lower Culvert first!)"
            ), "CH2_TRIAL"

    # ==================================================================
    # TRIAL 20 RESOLUTION: THE SMUGGLERS ENCOUNTER
    # ==================================================================
    if trial == "trial_20_smugglers":
        if choice == "Back away into the mist":
            player["active_ch2_trial"] = None
            player["x"], player["y"] = player["prev_x"], player["prev_y"]
            return player, "You slip quietly back into the mist.", "MAIN"

        player["active_ch2_trial"] = None
        completed.append(f"smugglers_{coord_tuple}")

        if choice.startswith("Tap the 4-beat Mason's Code"):
            player["silver"] += 25
            modify_faction(player, "faction_wallmakers", 2)
            return player, (
                "The smugglers lower their weapons at the sound of the Guild rhythm!\n"
                "\"One of Hopestill's surveyors! Here is your **25-silver** cut of the landing, friend.\"\n"
                f"*** (+25 Silver, +2 Wallmakers Faction | Silver: {player['silver']}s) ***"
            ), "MAIN"

        if choice.startswith("Offer 10 Silver"):
            if player["silver"] >= 10:
                player["silver"] -= 10
                player["inventory"].append("spiced cider")
                m_item = "parvus town map" if coord_tuple == (15, 22) else "fluvius town map"
                if m_item not in player["inventory"]:
                    player["inventory"].append(m_item)
                return player, f"You trade 10 silver for a jug of **Spiced Cider** and a **{format_item_name(m_item)}**!", "MAIN"
            return player, "\"You don't have 10 silver!\"", "MAIN"

        # Fight the smugglers (Watch arrest or Outlaw raid)
        is_guard = choice.startswith("Declare Watch")
        if is_guard:
            modify_faction(player, "faction_guard", 2)
        else:
            player["reputation"] -= 2
        player["silver"] += 30
        player["inventory"].append("vintage brumaire wine")
        player["active_enemy"] = {
            "id": "smugglers_crew",
            "name": "Contraband Smugglers",
            "health": 18,
            "flee_damage": 3,
            "attack_min": 2,
            "attack_max": 6,
            "attack_verb": "The smugglers slash at you with cutlasses",
            "defeat_msg": "You rout the smugglers and seize **30 silver** and a bottle of **Vintage Brumaire Wine** from their crates!",
            "flee_msg": "You retreat up the bank under a hail of pistol-shot! (-{dmg} Health)"
        }
        return player, "You charge the smugglers' landing!", "COMBAT"

    player["active_ch2_trial"] = None
    return player, "You continue on your journey.", "MAIN"
