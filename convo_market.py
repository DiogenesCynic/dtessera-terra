import game_data as db
from mechanics import (
    modify_faction,
    advance_time,
    handle_sleep_nap,
    handle_sleep_morning,
    get_time_string,
    calculate_max_hit,
    get_eligible_chapter_2_routes,
    can_start_shift,
    mark_shift_started,
    mark_shift_completed,
    get_inventory_weight,
    get_max_carry_weight,
    record_food_acquisition,
    sell_item_helper,
    format_item_name
)
import encounters
import mini_games

MERCHANT_TYPES = {
    "fruiterer", "butcher", "fishmonger",
    "vegetable stall merchant", "dairy stall merchant", "chandler"
}

# -------------------------------------------------------------------------
# MARKET MANAGER (GODWIN WILLIAMS)
# -------------------------------------------------------------------------
def get_market_manager_options(player):
    if player.get("market_state") == "shift_6_prompt":
        return ["Proceed with shift", "Hand in notice with immediate effect"]

    if player.get("market_state") == "market_brawl":
        return [
            "Throw dirty sweep-water over both of them!",
            "Step between them and talk them down",
            "Tackle the Wallmaker Enforcer (Side with Union)",
            "Tackle the Union Brawler (Side with Wallmakers)",
            "Duck behind the stalls and wait for the Guard"
        ]

    if player.get("market_state") == "chase_stage_1":
        return [
            "Bellow 'MAKE WAY!'",
            "Barge through the shoppers",
            "Dart along the stall awnings",
            "Scramble blindly through the crowd"
        ]
    if player.get("market_state") == "chase_stage_2":
        return [
            "Pole-vault over the cabbages using your heavy broom!",
            "Vault the overturned cart cleanly",
            "Shove the heavy cabbage cart out of the way"
        ]
    if player.get("market_state") == "chase_stage_3":
        opts = [
            "Hurl your broom like a javelin into his legs!",
            "Draw your weapon and fight him for the lockbox!",
            "Cut a 50/50 deal: take 40s and let him over the wall"
        ]
        if player.get("anarchist_cell_joined"):
            opts.append("Seize the lockbox for the Free-Earth Syndicate!")
        return opts

    if player["current_job"] == "market":
        if player.get("active_market_task") is None:
            opts = [f"Start Shift ({player['market_sweeper_shifts']} Completed)"]
            if player["market_sweeper_shifts"] >= 6:
                opts.append("Hand in notice with immediate effect")
            opts.append("Leave")
            return opts
        opts = []
        if player.get("active_market_task") == "solve_flytipping":
            opts.append("Open Fly-Tipping Citation Board")
        opts.extend(["Return from Task", "Leave"])
        return opts

    return ["Apply for Job", "Leave"]


def resolve_market_manager(choice, player):
    if choice == "Leave":
        return player, "\"Then out of the way, please!\"", "MAIN"

    if choice == "Apply for Job":
        if player["current_job"] is not None and player["current_job"] != "market":
            return player, "\"You're already employed elsewhere! Quit your other job first if you want to sweep my market.\"", "MAIN"
        player["current_job"] = "market"
        player["current_tenure"] = 0
        player["active_market_task"] = None
        return player, "Godwin Williams hands you a stiff broom. \"Don't lean on it! Come back during working hours to start your first shift.\"", "MAIN"

    if choice == "Open Fly-Tipping Citation Board":
        return mini_games.init_flytip_minigame(player)

    if choice == "Hand in notice with immediate effect":
        player["market_state"] = None
        player["current_job"] = None
        player["current_tenure"] = 0
        player["active_market_task"] = None
        player["chapter_2_unlocked"] = True
        log = (
            "Godwin Williams clasps your hand warmly with both of his.\n"
            "\"You saved this market more times than I can count, Overseer. I won't keep you tied to the stalls!\"\n"
            "\"Go inspect the Noticeboard in the Town Hall—with your silver tongue and experience, big opportunities await you!\"\n\n"
            "*** You have handed in your notice! Visit the Noticeboard in the Town Hall to explore new opportunities! ***"
        )
        return player, log, "MAIN"

    if choice == "Proceed with shift":
        player["market_state"] = None
        player["market_shift_6_prompted"] = True
        choice = f"Start Shift ({player['market_sweeper_shifts']} Completed)"

    # --- SHIFT 3: GODWIN'S CONFRONTATION ---
    if player.get("market_state") == "contraband_confrontation":
        player["market_state"] = None
        if choice == "Show Godwin the radical pamphlets":
            player["active_market_task"] = "hand_contraband_to_guard"
            log = (
                "Godwin's spectacles nearly fall off his nose as he reads the title page.\n"
                "\"'Property is Theft'?! Anarchist sedition in MY market?! Put that away before someone sees it!\"\n"
                "\"I want nothing to do with this! March straight to the Guard House and hand that filth over to Captain Wealdhere immediately!\"\n"
                "\"Come back to me only after the Watch has disposed of it!\"\n\n"
                "*** TASK UPDATED: Take the Bundle of Radical Pamphlets to Captain Wealdhere at the Guard House! ***"
            )
            return player, log, "MAIN"
        else:
            player["active_market_task"] = "contraband_hidden"
            log = (
                "You smoothly slide the oilskin bundle inside your coat and hold up a crumpled piece of twine.\n"
                "Godwin squints, satisfied. \"Hmph. Well, finish sweeping behind the stalls and let me know when you're done.\"\n\n"
                "*** You kept the Bundle of Radical Pamphlets! ***\n"
                "*** Use 'Action -> Read' to inspect the pamphlets for clues to their owner, or 'Return from Task' to Godwin to finish your shift and keep them for yourself! ***"
            )
            return player, log, "MAIN"

    # --- SHIFT 4 SIDE-QUEST: THE BUTCHER'S MARKET BRAWL RESOLUTION ---
    if player.get("market_state") == "market_brawl":
        player["market_state"] = None

        if choice == "Throw dirty sweep-water over both of them!":
            player["market_sq4_done"] = True
            player["silver"] += 5
            player["reputation"] += 1
            log = (
                "You hoist your heavy wooden wash-bucket—brimming with icy gutter-sludge, cabbage leaves, and horse muck—and hurl it squarely over both men!\n"
                "They freeze, gasping and sputtering in horrified disbelief as the foul water drips from their chins.\n"
                "The entire market square erupts into laughter! Humiliated and soaked to the bone, both brawlers slink away in opposite directions.\n\n"
                "The Butcher wipes a tear of laughter from his eye and tosses you 5 silver. \"Brilliant! You saved my chopping block! When you finish Godwin's fly-tipping board, I'll make sure he knows what you did!\"\n\n"
                "*** SIDE-QUEST COMPLETE! (+5 Silver, +1 Reputation; +1 Bonus Charisma upon completing Shift 4!) ***"
            )
            return player, log, "MAIN"

        elif choice == "Step between them and talk them down":
            if player["charisma"] >= 2:
                player["market_sq4_done"] = True
                player["silver"] += 10
                player["reputation"] += 2
                log = (
                    "You plant your broom handle firmly between them and project your voice across the square.\n"
                    "\"Enough! If you smash these stalls, the Watch shuts the market down and every working family in Murum goes hungry tonight!\"\n"
                    "The crowd murmurs in agreement. Shamed by your commanding presence, the Enforcer and the Union worker lower their fists and back away.\n\n"
                    "The Butcher claps you on the shoulder in awe and hands you 10 silver. \"A natural leader! Finish Godwin's fly-tipping citations and I'll sing your praises!\"\n\n"
                    "*** SIDE-QUEST COMPLETE! (+10 Silver, +2 Reputation; +1 Bonus Charisma upon completing Shift 4!) ***"
                )
                return player, log, "MAIN"
            else:
                log = (
                    "You try to step between them and call for calm, but your voice is drowned out by the shouting!\n"
                    "The Wallmaker Enforcer shoves you hard into a pile of crates and turns his brass knuckles on you!"
                )
                player["brawl_prior_task"] = player.get("active_market_task", "solve_flytipping")
                player, combat_log, next_state = encounters.trigger_wallmaker_brawl(player)
                return player, log + "\n\n" + combat_log, next_state

        elif choice == "Tackle the Wallmaker Enforcer (Side with Union)":
            player["brawl_prior_task"] = player.get("active_market_task", "solve_flytipping")
            return encounters.trigger_wallmaker_brawl(player)

        elif choice == "Tackle the Union Brawler (Side with Wallmakers)":
            player["brawl_prior_task"] = player.get("active_market_task", "solve_flytipping")
            return encounters.trigger_union_brawl(player)

        elif choice == "Duck behind the stalls and wait for the Guard":
            player["market_sq4_done"] = False
            player["reputation"] -= 1
            log = (
                "You dive behind the Fishmonger's barrel as the two men smash through the Butcher's stall, sending meat cleavers and ribs flying everywhere!\n"
                "Five minutes later, Captain Wealdhere's guards storm in with truncheons swinging.\n"
                "The Butcher glares at you amidst the wreckage. \"You just hid there while they wrecked my stall?! Don't expect a good word from me!\"\n\n"
                "*** Side-Quest Failed! (-1 Reputation) ***"
            )
            return player, log, "MAIN"

    # --- SHIFT 5: THE 3-STAGE THIEF CHASE ---
    if player.get("market_state") == "chase_stage_1":
        player["market_state"] = None
        bonus = 0
        if choice == "Bellow 'MAKE WAY!'" and player["charisma"] >= 1:
            bonus = 2
            intro = "Your booming voice parts the crowd of shoppers like the sea! (+2 Pace Advantage!)\n"
        elif choice == "Barge through the shoppers" and player["strength"] >= 1:
            bonus = 2
            intro = "You shoulder through the crowded aisle at full sprint! (+2 Pace Advantage!)\n"
        elif choice == "Dart along the stall awnings" and (player["stealth"] >= 1 or "climb" in player["skills"]):
            bonus = 2
            intro = "You bound effortlessly across the canvas stall awnings above the crowd! (+2 Pace Advantage!)\n"
        else:
            intro = "You stumble through the dense crowd of shoppers and set off after the Cutpurse!\n"

        player, _, next_state = mini_games.init_chase(player, stage=1, bonus_paces=bonus)
        return player, intro + "*** SPRINT 1: Match the Cutpurse's lane moves on the horizontal gauge! ***", next_state

    if player.get("market_state") == "chase_stage_2":
        player["market_state"] = None
        bonus = 0
        if choice == "Pole-vault over the cabbages using your heavy broom!":
            bonus = 2
            intro = "You plant the tip of your heavy broom handle into the cobbles and pole-vault cleanly over the rolling cabbages! (+2 Pace Advantage!)\n"
        elif choice == "Vault the overturned cart cleanly" and ("climb" in player["skills"] or player["strength"] >= 2):
            bonus = 2
            intro = "You leap onto the axle of the overturned cart and vault straight over the wreckage! (+2 Pace Advantage!)\n"
        else:
            intro = "You heave the heavy cart aside, losing a moment before sprinting back after him!\n"

        player, _, next_state = mini_games.init_chase(player, stage=2, bonus_paces=bonus)
        return player, intro + "*** SPRINT 2: Keep closing the distance! ***", next_state

    if player.get("market_state") == "chase_stage_3":
        player["market_state"] = None
        if choice == "Hurl your broom like a javelin into his legs!":
            if "market lockbox" not in player["inventory"]:
                player["inventory"].append("market lockbox")
            player["active_market_task"] = "report_market_shift_5_win"
            log = (
                "You level your heavy market broom like a spear and hurl it end-over-end between the Cutpurse's ankles!\n"
                "He flips headfirst into a stack of empty wicker baskets, knocking himself out cold as Godwin's Heavy Iron Lockbox clatters to your feet!\n\n"
                "*** You recovered the Market Lockbox! Return to Godwin and show him your success!! ***"
            )
            return player, log, "MAIN"

        elif choice == "Draw your weapon and fight him for the lockbox!":
            return encounters.trigger_thief_combat(player)

        elif choice == "Cut a 50/50 deal: take 40s and let him over the wall":
            player["silver"] += 40
            modify_faction(player, "faction_wallmakers", 2)
            player["active_market_task"] = "report_market_shift_5_fail"
            log = (
                "The Cutpurse grins, pries open the lockbox with a crowbar, and tosses you a heavy 40-silver share before scrambling up the rope and over the Town Wall!\n\n"
                f"*** You pocketed 40 silver of stolen stall rents! (+40 Silver, +2 Wallmakers Faction, Total Silver: {player['silver']}) ***\n"
                "*** Return to Godwin ('Return from Task') and pretend the thief got away... ***"
            )
            return player, log, "MAIN"

        elif choice == "Seize the lockbox for the Free-Earth Syndicate!":
            player["silver"] += 25
            modify_faction(player, "faction_union", 4)
            player["active_market_task"] = "report_market_shift_5_fail"
            log = (
                "You trip the Cutpurse, snatch the lockbox, and pass the week's stall rents through a drain-grate to Breakchains' waiting couriers—keeping 25 silver to fund your own travels!\n\n"
                f"*** Expropriation Complete! (+25 Silver, +3 Union Faction, Total Silver: {player['silver']}) ***\n"
                "*** Return to Godwin ('Return from Task') and claim the thief escaped over the wall! ***"
            )
            return player, log, "MAIN"

    # --- STARTING A SHIFT ---
    if choice.startswith("Start Shift"):
        ok, msg = can_start_shift(player)
        if not ok:
            return player, msg, "MAIN"
        player = mark_shift_started(player)

        shifts = player["market_sweeper_shifts"]

        # --- SHIFT 6 EVALUATION: NOTICEBOARD OR DISMISSAL (GAME OVER) ---
        if shifts == 5 and not player.get("market_shift_6_prompted"):
            eligible = get_eligible_chapter_2_routes(player)
            if not eligible:
                player["current_job"] = None
                player["current_tenure"] = 0
                log = (
                    "Godwin Williams flips through his clipboard and frowns deeply.\n"
                    "\"I am afraid that you have failed to reach the level that we expect of a market sweeper in the time that you have been here. "
                    "We are going to have to let you go. I cannot see you acquiring any further work in Murum. "
                    "You will have to try your luck on the road. I wish you luck.\"\n\n"
                    "*** GAME OVER: You failed to qualify for any Chapter 2 path and have been dismissed from Murum! ***"
                )
                return player, log, "DEAD"

            player["market_state"] = "shift_6_prompt"
            player["chapter_2_unlocked"] = True
            log = (
                "Godwin lowers his clipboard and smiles warmly at you.\n"
                "\"Noburu, you've risen to Market Overseer and won the respect of every stallholder here. "
                "With your new experience and skills, there may be new opportunities for you if you look at the Noticeboard in the Town Hall.\"\n"
                "\"Would you like to proceed with your shift today, or hand in your notice with immediate effect?\""
            )
            return player, log, "NPC_DIALOGUE"

        # --- SHIFT 1: THE MISPLACED MASTER KEY ---
        if shifts == 0:
            player["active_market_task"] = "find_master_key"
            log = (
                "Godwin Williams pats his pockets frantically, his face pale.\n"
                "\"Forget the broom for a moment! I've lost my Master Key! It locks every merchant's strongbox in the square!\"\n"
                "\"Retrace my morning steps and ask around. I started at the Post Office, walked down to the Playhouse to tell off Fairlight, and then spoke to the guards at the Town Gate before coming back here.\"\n"
                "\"Find out where I dropped it, search the spot, and bring that key back to me!\"\n\n"
                "*** SHIFT STARTED! Retrace Godwin's route: Post Office -> Playhouse -> Town Gate! ***"
            )
            return player, log, "MAIN"

        # --- SHIFT 2: THE MOVING POSTIE ---
        elif shifts == 1:
            player["active_market_task"] = "find_postie_post_office"
            log = (
                "Godwin Williams waves you over frantically.\n"
                "\"Leave the broom! The Apothecary is in a state of panic—they are waiting on an urgent delivery of Moon-Blight Extract, and their patient is fading fast!\"\n"
                "\"Sprint to the Post Office immediately and see if you can intercept the parcel!\"\n"
                "\"Once you have it, run it straight to the Apothecary on the High Street, then report back to me!\"\n\n"
                "*** URGENT ERRAND: You break into a flat sprint through Murum's streets (10 minutes per street instead of 15, though the pace drains your stamina and hastens exhaustion). Head to the Post Office and speak to the Postmaster! ***"
            )
            return player, log, "MAIN"

        # --- SHIFT 3: THE CONTRABAND ---
        elif shifts == 2:
            player["active_market_task"] = "sweep_contraband"
            player["market_sq3_done"] = False
            player["market_sq3_failed"] = False
            log = (
                "Godwin hands you a stiff-bristled broom.\n"
                "\"The back-alleys behind the produce and butcher stalls are a disgrace today. Crates everywhere.\"\n"
                "\"Give the market square a thorough sweep and clear out anything wedged behind the stalls.\"\n"
                "(Tip: The **Apothecary**'s apprentice is off sick today—speak to the Apothecary during your shift if you want to help compound a recipe for bonus Charisma!)\n\n"
                "*** SHIFT 3 STARTED! Use 'Action -> Gather / Search' here in the Market to sweep behind the stalls! ***"
            )
            return player, log, "MAIN"

        # --- SHIFT 4: 4x4x4 FLY-TIPPING LOGIC PUZZLE ---
        elif shifts == 3:
            player["active_market_task"] = "solve_flytipping"
            player["market_sq4_done"] = False
            player["market_sq4_attempted"] = False
            player["flytip_mistakes"] = 0
            player, mini_log, next_state = mini_games.init_flytip_minigame(player)
            intro = (
                "Godwin Williams is livid, waving a stack of sanitation citations.\n"
                "\"Four of my own stallholders—the **Butcher**, the **Fishmonger**, the **Fruiterer**, and the **Commissar**—have been fly-tipping their foul trade waste around the square overnight!\"\n"
                "\"Match each merchant to their dumping spot and waste type on the Citation Board so I can fine the culprits!\"\n"
                "(Tip: Before you turn in your completed report to Godwin, speak to the **Butcher** in the Market if you want to deal with a disturbance at his stall for bonus Charisma!)\n\n"
            )
            return player, intro + mini_log, next_state

        # --- SHIFT 5: STOP THIEF! ---
        elif shifts == 4:
            player["market_state"] = "chase_stage_1"
            log = (
                "You arrive at Godwin's counting table just as a hooded Cutpurse snatches the **Heavy Iron Lockbox**—filled with the entire week's merchant stall rents—and bolts into the crowded square!\n"
                "\"STOP THIEF!\" Godwin screams, clutching his chest. \"If I lose those rents, the Mayor will ruin me! Catch him, Noburu!\"\n\n"
                "*** STAGE 1: THE CROWDED SQUARE! The thief is 12 paces ahead and diving into a crowd of shoppers! How do you pursue?! ***"
            )
            return player, log, "NPC_DIALOGUE"

        # --- REPEATABLE SHIFTS (Shifts 5+) ---
        if "market overseer" in player["skills"] or shifts >= 25: shift_pay = 35
        elif shifts >= 10: shift_pay = 20
        elif shifts >= 5: shift_pay = 15
        else: shift_pay = 10

        player["silver"] += shift_pay
        player["charisma"] += 1
        player, _ = advance_time(300, player)
        player = mark_shift_completed(player)
        player["market_sweeper_shifts"] += 1
        player["current_tenure"] += 1

        log = (
            "\"Here's your broom. Get to work.\"\n\n"
            "You spend the next three hours sweeping the cobblestones of the market.\n"
            "While working, you make friendly conversation with the various stall owners, getting on their good side.\n"
            f"*** You earned {shift_pay} silver and +1 Charisma (Total: {player['charisma']})! ***"
        )

        if player["market_sweeper_shifts"] == 5 and "market overseer" not in player["skills"]:
            player["reputation"] += 1
            log += "\n*** The merchants appreciate your hard work! (+1 Reputation) ***\n*** Your pay has increased to 15 silver per shift! ***"
        elif player["market_sweeper_shifts"] == 10 and "market overseer" not in player["skills"]:
            player["reputation"] += 1
            log += "\n*** You are a trusted staple of the market! (+1 Reputation) ***\n*** Your pay has increased to 20 silver per shift! ***"
        elif player["market_sweeper_shifts"] == 25:
            player["reputation"] += 2
            log += "\n*** Godwin considers you his right hand! (+2 Reputation) ***"

        return player, log, "MAIN"

    if choice == "Return from Task":
        task = player.get("active_market_task")

        if task == "sweep_contraband":
            return player, "\"You haven't swept behind the stalls yet! Use 'Action -> Gather / Search' right here in the Market.\"", "MAIN"

        if task == "hand_contraband_to_guard":
            return player, "\"Why are you bringing sedition back to me?! Take those pamphlets to Captain Wealdhere at the Guard House!\"", "MAIN"

        if task == "solve_flytipping":
            return player, "\"You haven't finished matching the fly-tipping culprits on the Citation Board yet! Select 'Open Fly-Tipping Citation Board' to finish it.\"", "MAIN"

        # --- SHIFT 1 TURN-IN ---
        if task in ["find_master_key", "search_fountain_key"]:
            if "muddy master key" in player["inventory"]:
                player["inventory"].remove("muddy master key")
                player["active_market_task"] = None
                player = mark_shift_completed(player)
                player["market_sweeper_shifts"] += 1
                player["current_tenure"] += 1
                player["silver"] += 15
                player["reputation"] += 1

                cha_gain = 1
                sq_msg = ""
                if player.get("market_sq1_done"):
                    cha_gain += 1
                    sq_msg = "\n\"And the Fruiterer told me you fetched fresh cobnuts from the Town Hall trees for their stall! That's how you win the merchants' hearts!\" (+1 Bonus Charisma!)"

                player["charisma"] += cha_gain
                player, _ = advance_time(180, player)

                log = (
                    "You hand the Muddy Master Key over to Godwin. He clutches it to his chest with a massive sigh of relief.\n"
                    f"\"In the fountain drain?! I must have dropped it when I washed my face! You have saved the market from chaos today.\"{sq_msg}\n"
                    f"*** Shift Completed! You earned 15 silver, +{cha_gain} Charisma (Total: {player['charisma']}), and +1 Reputation! (Total Silver: {player['silver']}) ***\n\n"
                    "Godwin points down the street. \"You look like you need a place to sleep. Try the Dog and Duck Pub.\"\n"
                    "\"The Landlord rents rooms for 2 silver a night. Don't sleep in the streets. Tell them that I sent you.\""
                )
                return player, log, "MAIN"
            return player, "\"Have you found my Master Key yet?! Retrace my route: Post Office, Playhouse, and the Town Gate!\"", "MAIN"

        # --- SHIFT 2 TURN-IN ---
        if task in ["find_postie_post_office", "intercept_postie", "deliver_to_apothecary"]:
            return player, "\"Have you tracked down the Postie and delivered that parcel to the Apothecary yet?! Check the Post Office!\"", "MAIN"

        if task in ["report_market_shift_2", "report_postie_success"]:
            player["active_market_task"] = None
            player = mark_shift_completed(player)
            player["market_sweeper_shifts"] += 1
            player["current_tenure"] += 1
            player["silver"] += 20
            player["charisma"] += 1
            player["reputation"] += 1
            player, _ = advance_time(120, player)

            if "postie's route sheet" in player["inventory"]:
                player["inventory"].remove("postie's route sheet")
            db.npc_database["postie"]["location"] = None

            log = (
                "Godwin beams with pride. \"The Apothecary told me how you calculated Fleetfoot's exact position and intercepted them on the dot!\"\n"
                "\"Sharp maths and sharper feet. Here is your 20 silver wage!\"\n\n"
                f"*** Shift Completed! (+1 Reputation, 20 Silver, +1 Charisma, Total: {player['silver']}) ***"
            )
            return player, log, "MAIN"

        # --- SHIFT 3 TURN-IN ---
        if task in ["contraband_hidden", "report_market_shift_3"]:
            player["active_market_task"] = None
            player = mark_shift_completed(player)
            player["market_sweeper_shifts"] += 1
            player["current_tenure"] += 1
            player["silver"] += 15

            cha_gain = 1
            sq_msg = ""
            if player.get("market_sq3_done"):
                cha_gain += 1
                sq_msg = "\n\"The Apothecary also mentioned you stepped in for their sick apprentice and compounded a flawless Fever-Draught! The whole square is talking about your helpfulness!\" (+1 Bonus Charisma!)"

            player["charisma"] += cha_gain
            player, _ = advance_time(180, player)

            log = (
                f"Godwin inspects the swept cobblestones and nods approvingly.\n\"Clean work today. Here is your 15 silver wage.\"{sq_msg}\n\n"
                f"*** Shift Completed! You earned 15 silver and +{cha_gain} Charisma! (Total silver: {player['silver']}, Total charisma: {player['charisma']}) ***"
            )
            if "bundle of radical pamphlets" in player["inventory"]:
                log += (
                    "\n\n*** WARNING: You still have the banned anarchist pamphlets hidden in your coat! ***\n"
                    "*** Studying them ('Read') grants insight, but carrying contraband past the Town Watch is dangerous... ***"
                )
            return player, log, "MAIN"

        # --- SHIFT 4 TURN-IN ---
        if task == "report_market_shift_4":
            if player.pop("brawl_prior_task", None) == "solve_flytipping":
                player["market_sq4_done"] = True
                player["active_market_task"] = "solve_flytipping"
                log = (
                    "The Butcher cheers as the defeated brawler limps away! \"You saved my stall, friend!\"\n"
                    "\"Now finish matching those fly-tipping culprits on Godwin's Citation Board so you can clock out!\"\n\n"
                    "*** SIDE-QUEST COMPLETE! Select 'Open Fly-Tipping Citation Board' on Godwin to finish your main shift task! ***"
                )
                return player, log, "MAIN"

            player["active_market_task"] = None
            player = mark_shift_completed(player)
            player["market_sweeper_shifts"] += 1
            player["current_tenure"] += 1
            player["silver"] += 20
            player["reputation"] += 1

            cha_gain = 1
            sq_msg = ""
            if player.get("market_sq4_done"):
                cha_gain += 1
                sq_msg = "\n\"And the Butcher told me how you broke up that vicious brawl in front of his meat block before the Watch could shut us down! Magnificent leadership!\" (+1 Bonus Charisma!)"

            player["charisma"] += cha_gain
            player, _ = advance_time(180, player)

            log = (
                "Godwin reviews your completed Sanitation Citation Board with grim satisfaction.\n"
                f"\"Every single fly-tipper pinned down to the letter! Wait until I slap them with these fines!\"{sq_msg}\n"
                "\"Here is your 20 silver wage!\"\n\n"
                f"*** Shift Completed! (+1 Reputation, +{cha_gain} Charisma, 20 Silver, Total Silver: {player['silver']}, Total Charisma: {player['charisma']}) ***"
            )
            return player, log, "MAIN"

        # --- SHIFT 5 TURN-IN ---
        if task == "report_market_shift_5_win":
            if "market lockbox" in player["inventory"]:
                player["inventory"].remove("market lockbox")
            player["active_market_task"] = None
            player = mark_shift_completed(player)
            player["market_sweeper_shifts"] += 1
            player["current_tenure"] += 1
            player["silver"] += 35
            player["charisma"] += 1
            player["reputation"] += 3
            if "market overseer" not in player["skills"]:
                player["skills"].append("market overseer")
            player, _ = advance_time(180, player)

            log = (
                "You slam the Heavy Iron Lockbox back onto Godwin's counting table. Every merchant in the square erupts into applause!\n"
                "Godwin's hands tremble as he checks the intact seal. \"You chased down a cutpurse through the alleys and saved the market's treasury!\"\n"
                "\"Turn in your broom, Noburu. Effective immediately, I am promoting you to **Market Overseer**!\"\n"
                "\"Here is a 35 silver reward, and your base pay for all future shifts here is permanently raised to 35 silver!\"\n\n"
                f"*** CAREER MASTERED: You are now Market Overseer! (+3 Reputation, +1 Charisma, 35 Silver, Total: {player['silver']}) ***"
            )
            return player, log, "MAIN"

        if task == "report_market_shift_5_fail":
            player["active_market_task"] = None
            player = mark_shift_completed(player)
            player["market_sweeper_shifts"] += 1
            player["current_tenure"] += 1
            player["reputation"] -= 2
            player, _ = advance_time(180, player)

            log = (
                "You return to the square empty-handed and tell Godwin that the thief scaled the Town Wall and escaped.\n"
                "Godwin slumps into his chair, pale as a ghost. \"Gone... the entire week's rent, gone. I'll have to pay the Mayor out of my own savings.\"\n"
                "\"Go home, sweeper. I can't bear to look at you today.\"\n\n"
                "*** Shift Failed! (-2 Reputation, No Shift Wage) ***"
            )
            return player, log, "MAIN"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# MERCHANTS (Dynamic + Side-Quests on Shifts 1, 3, and 4)
# -------------------------------------------------------------------------
def get_merchant_options(merchant_type, player):
    discount = max(0, player["charisma"] - 10)

    goods_map = {
        "fruiterer": ["apple", "pear", "spiced cider", "box of candied violets"],
        "butcher": ["meat ration"],
        "fishmonger": ["fish jerky"],
        "vegetable stall merchant": ["carrot", "cucumber"],
        "dairy stall merchant": ["butter", "wheel of aged cheese"],
        "chandler": ["sack of oats"],
    }

    goods = goods_map.get(merchant_type, [])
    if not goods:
        return ["Leave"]

    options = []

    if (
        merchant_type == "fruiterer"
        and player.get("current_job") == "market"
        and player.get("market_sweeper_shifts") == 0
        and player.get("active_market_task") in ["find_master_key", "search_fountain_key"]
        and not player.get("market_sq1_done")
    ):
        if not player.get("market_sq1_started"):
            options.append("Ask if they need a hand (Side-Quest)")
        elif "cobnuts" in player["inventory"]:
            options.append("Deliver Cobnuts to Fruiterer")

    if (
        merchant_type == "apothecary"
        and player.get("current_job") == "market"
        and player.get("market_sweeper_shifts") == 2
        and player.get("active_market_task") is not None
        and not player.get("market_sq3_done")
        and not player.get("market_sq3_failed")
    ):
        options.append("Help mix Fever-Draught (Side-Quest)")

    if (
        merchant_type == "butcher"
        and player.get("current_job") == "market"
        and player.get("market_sweeper_shifts") == 3
        and player.get("active_market_task") in ["solve_flytipping", "report_market_shift_4"]
        and not player.get("market_sq4_attempted")
    ):
        options.append("Ask about Fly-Tipping / Stall Trouble")

    if "bundle of radical pamphlets" in player["inventory"]:
        if merchant_type == "fruiterer":
            options.append("Ask about violet ink & purple stains")
        elif merchant_type == "vegetable stall merchant":
            options.append("Discreetly return Radical Pamphlets")

    if merchant_type == "vegetable stall merchant" and player.get("syndicate_invited"):
        options.append("Take Comrade's Ration (Free Carrot)")

    if merchant_type == "vegetable stall merchant" and "spoiled food" in player["inventory"]:
        spoiled_cnt = player["inventory"].count("spoiled food")
        options.append(f"Trade Spoiled Food for Compost (+{spoiled_cnt}s)")

    for item in goods:
        base_price = db.item_database[item]["price"]
        final_price = max(1, base_price - discount)
        options.append(f"Buy {item.title()} ({final_price}s)")

    options.append("Leave")
    return options


def resolve_merchant(merchant_type, choice, player):
    if choice == "Leave":
        return player, "\"Have a good day! Let me know if you change your mind.\"", "MAIN"

    if merchant_type == "fruiterer" and choice == "Ask if they need a hand (Side-Quest)":
        player["market_sq1_started"] = True
        if "cobnuts" in player["inventory"]:
            log = (
                "The Fruiterer wipes their hands on their apron.\n"
                "\"Actually, yes! My customers are clamouring for fresh **Cobnuts**, and I can't leave my stall to gather them from beneath the trees outside the **Town Hall**.\"\n"
                "\"Wait—you already have a handful in your pack! Hand them over whenever you're ready!\""
            )
        else:
            log = (
                "The Fruiterer wipes their hands on their apron.\n"
                "\"Actually, yes! My customers are clamouring for fresh **Cobnuts**, and I can't leave my stall to gather them.\"\n"
                "\"Since you're walking around town looking for Godwin's key, could you head to the **Town Hall**, use 'Action -> Gather / Search' beneath the cobnut trees, and bring a handful back to me before you finish your shift?\""
            )
        return player, log, "MAIN"

    if merchant_type == "fruiterer" and choice == "Deliver Cobnuts to Fruiterer":
        if "cobnuts" in player["inventory"]:
            player["inventory"].remove("cobnuts")
            player["market_sq1_done"] = True
            player["silver"] += 5
            log = (
                "You pour the fresh cobnuts into the Fruiterer's wicker display basket. Their face lights up!\n"
                "\"Fresh from the Town Hall trees! You're a lifesaver, Noburu. Take this 5 silver for your trouble—and I'll make sure Godwin hears how helpful you've been today!\"\n\n"
                f"*** SIDE-QUEST COMPLETE! (+5 Silver, Total: {player['silver']}; +1 Bonus Charisma when you finish Shift 1 with Godwin!) ***"
            )
            return player, log, "MAIN"
        return player, "\"You don't have any cobnuts! Check beneath the trees outside the Town Hall.\"", "MAIN"

    if merchant_type == "butcher" and choice == "Ask about Fly-Tipping / Stall Trouble":
        player["market_sq4_attempted"] = True
        player["market_state"] = "market_brawl"
        log = (
            "Before the Butcher can answer your question about the fly-tipped offal, angry shouting erupts right beside his stall!\n"
            "A burly **Wallmaker Enforcer** and a furious **Union Brawler** are nose-to-nose over Guild debt collections.\n"
            "\"Parasite!\" the Union worker roars, throwing a wild punch. They crash straight into the Butcher's chopping block, sending cleavers clattering toward you!\n"
            "The Butcher yells in panic: \"Sweeper! Stop them before they smash my stall and draw the Watch!\"\n\n"
            "*** SIDE-QUEST CRISIS: How do you handle the brawlers?! ***"
        )
        return player, log, "INTERCEPT_MARKET_BRAWL"

    if merchant_type == "fruiterer" and choice == "Ask about violet ink & purple stains":
        log = (
            "The Fruiterer glances over at the neighbouring stall.\n"
            "\"Violet ink and purple stains? Well, Shareall over at the Vegetable Stall is always scribbling notes between customers with a violet nib.\"\n"
            "\"And anyone peeling Murum carrots all morning ends up with fingers stained purple to the bone!\""
        )
        return player, log, "MAIN"

    if merchant_type == "vegetable stall merchant" and choice == "Discreetly return Radical Pamphlets":
        player["inventory"].remove("bundle of radical pamphlets")
        if "syndicate token" not in player["inventory"]:
            player["inventory"].append("syndicate token")
        player["syndicate_invited"] = True
        modify_faction(player, "faction_union", 3)
        if player.get("active_market_task") == "contraband_hidden":
            player["active_market_task"] = "report_market_shift_3"

        log = (
            "You lean across the crate of purple Murum carrots and quietly slide the oilskin bundle beneath a burlap sack.\n"
            "Shareall freezes. Their purple-stained fingers close over the pamphlets as they check that no guards are watching.\n"
            "\"You hid these from Godwin... and you didn't run to Wealdhere's Anglo-Saxon watchdogs,\" Shareall whispers fiercely.\n"
            "\"The bureaucrats at Union House want to bargain with the Mayor. We want to abolish the Castellan's chains altogether.\"\n"
            "Shareall presses a diagonally painted Red-and-Black Wooden Token into your palm.\n"
            "\"Our affinity group—the Free-Earth Syndicate—meets in the **Stable Loft** after hours, between **7:50 and 9:50**. Bring this token. Breakchains will want to meet you.\"\n\n"
            "*** You obtained the Syndicate Token! (+3 Union Faction) ***\n"
            "*** Shareall will now give you free carrots whenever you visit! ***\n"
            "*** NEW PATH UNLOCKED: Visit the Stable Loft between 7:50 and 9:50 to attend the secret Syndicate meeting, and report back to Godwin to finish your shift! ***"
        )
        return player, log, "MAIN"

    if merchant_type == "vegetable stall merchant" and choice == "Take Comrade's Ration (Free Carrot)":
        if player["inventory"].count("carrot") >= 3:
            return player, "Shareall smiles warmly. \"You already have plenty of carrots in your pack, comrade. Save some for the others!\"", "MAIN"
        player["inventory"].append("carrot")
        record_food_acquisition(player, "carrot")
        return player, "Shareall slips a fresh purple carrot into your hand with a quiet nod. \"Solidarity, comrade. Mutual aid in action.\"\n*** You received a Free Carrot! ***", "MAIN"

    if merchant_type == "vegetable stall merchant" and choice.startswith("Trade Spoiled Food for Compost"):
        spoiled_cnt = player["inventory"].count("spoiled food")
        if spoiled_cnt > 0:
            player["inventory"] = [i for i in player["inventory"] if i != "spoiled food"]
            player["silver"] += spoiled_cnt
            return player, (
                f"Shareall tips your spoiled produce into a rich compost barrel behind the stall and hands you {spoiled_cnt} silver.\n"
                f"\"Nothing goes to waste on the commune's soil, friend. This will feed next season's carrots!\"\n"
                f"*** (+{spoiled_cnt} Silver | Total: {player['silver']}s) ***"
            ), "MAIN"
        
    discount = max(0, player["charisma"] - 10)
    item_name = choice[4:].split(" (")[0].lower()
    item_w = db.item_database.get(item_name, {}).get("weight", 0.2)

    if item_name in db.item_database:
        final_price = max(1, db.item_database[item_name]["price"] - discount)

        if get_inventory_weight(player) + item_w > get_max_carry_weight(player) + 15.0:
            return player, "\"You can barely stand under the weight of your pack already! Drop or use something first.\"", "MAIN"

        if player["silver"] >= final_price:
            player["silver"] -= final_price
            player["inventory"].append(item_name)
            record_food_acquisition(player, item_name)
            log = f"You hand over the silver and safely pack away the {item_name}.\n*** You bought a {item_name}! (Remaining Silver: {player['silver']}) ***"
            return player, log, "MAIN"
        return player, f"\"I'm sorry, friend, but you don't have enough coin. You only have {player['silver']}.\"", "MAIN"

    return player, "Item not found.", "MAIN"

# -------------------------------------------------------------------------
# POSTMASTER SAFEHAVEN
# -------------------------------------------------------------------------
def get_postmaster_options(player):
    options = []
    b_task = player.get("active_blacksmith_task")
    m_task = player.get("active_market_task")

    if b_task == "prepare_drill_parts" and "package of drill parts" not in player["inventory"]:
        if player.get("parts_order_day") is None:
            options.append("Order Drill Parts (10s)")
        else:
            options.append("Collect Drill Parts")

    if m_task == "find_postie_post_office":
        options.append("Ask about Apothecary's Parcel")
    elif m_task == "intercept_postie":
        options.append("Restart Postie Chase Timer")

    if m_task == "find_master_key":
        options.append("Ask about Godwin's Key")

    if "misdelivered town hall letter" in player["inventory"]:
        options.append("Mention Letter Found in Postbox")

    options.extend(["Interact", "Leave"])
    return options

def resolve_postmaster(choice, player):
    if choice == "Leave":
        return player, "You step away.", "MAIN"

    if choice == "Ask about Godwin's Key":
        log = (
            "Postmaster Safehaven peers over his spectacles.\n"
            "\"Godwin's master key? He definitely had it here. He unclipped his coin purse from the same heavy iron ring to pay for his stamps.\"\n"
            "\"He was muttering about the theatre posters cluttering the stalls and marched straight South toward the Playhouse.\""
        )
        return player, log, "MAIN"

    if choice in ["Ask about Apothecary's Parcel", "Restart Postie Chase Timer"]:
        if "postie's route sheet" not in player["inventory"]:
            player["inventory"].append("postie's route sheet")
        player["active_market_task"] = "intercept_postie"
        player["postie_start_time"] = player["total_game_minutes"]
        db.npc_database["postie"]["location"] = None

        log = (
            "Postmaster Safehaven checks the station clock and hands you a copy of the Postie's Route Sheet.\n"
            "\"The Apothecary's parcel? You missed Fleetfoot the Postie by **34 minutes**! They are already out on their delivery loop:\"\n"
            "\"1: Stables -> 2: Guard House -> 3: School -> 4: Playhouse -> 5: Wallmakers -> 6: Blacksmiths -> 7: Union House -> 8: Town Hall -> 9: Dog and Duck Pub -> 10: Post Office.\"\n\n"
            "\"Fleetfoot takes **14 minutes** to travel between each stop on their route.\"\n"
            "\"At a hard sprint, you cover each street in **10 minutes** (North, South, East, or West)—save your breath and don't take detours. Work out where Fleetfoot will be and take the **shortest route** from here so you arrive at that stop at the **exact same minute** as Fleetfoot!\"\n\n"
            "*** CHASE STARTED (t = 0m)! Use 'Read -> Postie's Route Sheet' if you need to check the stops, and take the shortest route to intercept Fleetfoot! ***"
        )
        return player, log, "MAIN"

    if choice == "Order Drill Parts (10s)":
        if player["silver"] >= 10:
            player["silver"] -= 10
            player["parts_order_day"] = (player["total_game_minutes"] // 1000) + 1
            return player, "\"Specialist parts? Highly unusual. It will take two full days to arrive from Fluvius. I will send the order out immediately.\"", "MAIN"
        return player, "\"You do not have 10 silver for the postage fee.\"", "MAIN"

    if choice == "Collect Drill Parts":
        current_day = (player["total_game_minutes"] // 1000) + 1
        if current_day >= player["parts_order_day"] + 2:
            player["inventory"].append("package of drill parts")
            return player, "\"Ah, yes. A heavy package arrived for you this morning on the Fluvius cart. Here it is.\"\n\n*** You received the Package of Drill Parts! ***", "MAIN"
        return player, "\"They aren't here yet. I told you, specialist mail takes two full days to arrive! Check back later.\"", "MAIN"

    if player.get("active_mayor_task") == "post_office" and "mayor's outgoing letters" in player["inventory"]:
        player["inventory"].remove("mayor's outgoing letters")
        player["inventory"].append("mayor's incoming post")
        player["active_mayor_task"] = "find_mayor_1"
        db.npc_database["mayor"]["location"] = "guard house"
        log = (
            "\"Ah, you must be the new staff from the Mayor's residence.\"\n"
            "Safehaven takes the outgoing letters and hands you a heavy, wax-sealed stack in return.\n"
            "\"These are the Mayor's incoming dispatches. You'll need to deliver them directly to them.\"\n"
            "\"They are not at home, though. Today is inspection day. You will find them at the Guard House watching the parade.\"\n\n"
            "*** You swapped the mail! Find the Mayor at the Guard House! ***"
        )
        return player, log, "MAIN"

    if choice == "Mention Letter Found in Postbox":
        return player, (
            "Postmaster Safehaven gasps. \"Fleetfoot left the Town Hall Surveyor's envelope sticking out of the postbox?!\"\n"
            "\"Please, run it over to the **Town Hall** and drop it off (use 'Gather / Search' inside the Town Hall lobby)—they'll reward you handsomely for your honesty!\""
        ), "MAIN"

    return player, "\"Unless you have a parcel to send, please step aside. The mail waits for no one.\"", "MAIN"


# -------------------------------------------------------------------------
# FLEETFOOT THE POSTIE
# -------------------------------------------------------------------------
def get_postie_options(player):
    if player.get("active_market_task") == "intercept_postie":
        return ["Collect Apothecary's Parcel", "Leave"]
    return ["Leave"]

def resolve_postie(choice, player):
    if choice == "Leave":
        return player, "\"No time to chat—the mail waits for no one!\"", "MAIN"

    if choice == "Collect Apothecary's Parcel":
        player["inventory"].append("apothecary's parcel")
        player["active_market_task"] = "deliver_to_apothecary"
        db.npc_database["postie"]["location"] = None
        log = (
            "Fleetfoot the Postie nearly drops their mailbag as you intercept them outside the Blacksmiths.\n"
            "\"By the clock, you timed that to the exact minute! 50 minutes on the dot—any earlier or later and we'd have missed each other in the crowd.\"\n"
            "\"Looking for the Apothecary's Moon-Blight Extract? Here it is. Run it back to the High Street before it's too late!\"\n\n"
            "*** You received the Apothecary's Parcel! Deliver it to the Apothecary in the High Street! ***"
        )
        return player, log, "MAIN"

    return player, "Error.", "MAIN"

# -------------------------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------------------------
HANDLERS = {
    "market manager": (get_market_manager_options, resolve_market_manager),
    "postmaster":     (get_postmaster_options, resolve_postmaster),
    "postie":         (get_postie_options, resolve_postie),
}
