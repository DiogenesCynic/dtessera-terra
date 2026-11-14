import random
import game_data as db
from mechanics import (
    modify_faction, advance_time, handle_sleep_nap, handle_sleep_morning,
    get_time_string, calculate_max_hit, get_eligible_chapter_2_routes,
    can_start_shift, mark_shift_started, mark_shift_completed,
    get_stabling_debt
)

# -------------------------------------------------------------------------
# STABLE MANAGER (SQUIRE GODSPEED)
# -------------------------------------------------------------------------
def get_stable_manager_options(player):
    options = []
    
    # --- SHIFT 5 FIRE RESCUE ---
    if player.get("active_blacksmith_task") == "stables_fire_rescue":
        if not player.get("fire_extinguished") and "bucket of sand" in player["inventory"]:
            options.append("Throw Sand on Fire")

    # --- MAYOR'S QUESTS ---
    if player["active_mayor_task"] == "collect_horse":
        options.append("Collect Mayor's Stallion")
    if player["active_mayor_task"] == "riding_lesson":
        options.append("Take Riding Lesson")
    if player["active_mayor_task"] == "return_horse_to_stables" and "fed and watered stallion" in player["inventory"]:
        options.append("Return Mayor's Stallion")

    # --- STABLE STATES ---
    state = player.get("stable_state")
    if state == "buy_horse": return ["Buy horse for 50 silver.", "Challenge price and offer 25 silver.", "Back"]
    if state == "quiz_1": return ["Wipe hands on straw", "Wash hands in hot water", "Check foal's position", "Give tonic"]
    if state == "quiz_2": return ["Yell loudly", "Force straw", "Administer Tonic", "Reposition foal"]
    if state == "quiz_3": return ["Push foal back", "Pull hind legs", "Reposition forelegs", "Pull forelegs"]
    if state == "quiz_4": return ["Pull continuously", "Pull in rhythm", "Pull on inhale", "Do not pull"]
    if state == "solve_puzzle": return ["The Wallmakers", "The Guard", "The Blacksmith", "The Mayor"]
    if state == "shift_4_decision": return ["Report Fromabove (Loyal to Boss)", "Cover for Fromabove (Loyal to Union)"]
    if state == "stall_allocation": return ["Pair Coryllus & Destrier", "Pair Coryllus & Draught Horse", "Conclude they cannot fit"]
    if state == "who_goes_outside": return ["Send Coryllus outside", "Send Destrier outside", "Send Union outside"]
    if state == "shift_6_prompt":
        return ["Proceed with shift", "Hand in notice with immediate effect"]

    # --- JOB AND GENERAL OPTIONS ---
    if player["current_job"] == "stables":
        if player["active_stable_task"] is None:
            options.append(f"Start Shift ({player['stable_shifts']} Completed)")
            if player["stable_shifts"] >= 6:
                options.append("Hand in notice with immediate effect")
        else:
            options.append("Return from Task")
    else:
        options.append("Apply for Job")
        
    if "crate of horseshoes" in player["inventory"]: options.append("Deliver Horseshoes")

    if "horse" in player["inventory"]:
        options.append("Stable Horse (2s/day tab)")
    elif player.get("horse_stabled"):
        debt = get_stabling_debt(player)
        options.append(f"Collect Stabled Horse (Pay {debt}s)")
    
    options.append("Buy a Horse")
    options.append("Riding Lesson (10s)")
    options.append("Leave")
    
    return options

def resolve_stable_manager(choice, player):
    state = player.get("stable_state")
    
    if choice == "Leave":
        return player, "\"Suit yourself. Close the door on your way out.\"", "MAIN"

    if choice == "Back":
        player["stable_state"] = None
        return player, "\"Well, come back when you have the coin.\"", "NPC_DIALOGUE"

    if choice == "Hand in notice with immediate effect":
        player["stable_state"] = None
        player["current_job"] = None
        player["current_tenure"] = 0
        player["active_stable_task"] = None
        player["chapter_2_unlocked"] = True
        log = (
            "Squire Godspeed shakes your hand firmly.\n"
            "\"You've got a rare gift with horses, Noburu. I hate to lose you, but I won't hold you back.\"\n"
            "\"Check the Noticeboard in the Town Hall — there's bound to be call for someone with your experience across Dtessera Terra.\"\n\n"
            "*** You have handed in your notice! Visit the Noticeboard in the Town Hall to explore new opportunities! ***"
        )
        return player, log, "MAIN"

    if choice == "Proceed with shift":
        player["stable_state"] = None
        player["stable_shift_6_prompted"] = True
        choice = f"Start Shift ({player['stable_shifts']} Completed)"

    if choice == "Throw Sand on Fire":
        player["inventory"].remove("bucket of sand")
        player["fire_extinguished"] = True
        log = (
            "You hurl the heavy bucket of sand onto the raging grease fire in the stalls!\n"
            "The flames are smothered instantly, plunging the barn into a smoky, ruined silence.\n"
            "Squire Godspeed weeps with relief. \"You saved us... and the horses!\"\n"
            "\"Take whatever you found to Lovejoy immediately!\"\n\n"
            "*** The fire is out! Return to the Blacksmith! ***"
        )
        return player, log, "MAIN"
    
    if choice == "Collect Mayor's Stallion":
        player["inventory"].append("mayor's stallion")
        player["active_mayor_task"] = "blacksmith_horse"
        log = "Squire Godspeed nods. \"Praisegod sent you? Very well, here is the Mayor's stallion.\"\n\"Take him straight to Lovejoy at the Blacksmiths. Do not dawdle.\""
        return player, log, "MAIN"
        
    if choice == "Deliver Horseshoes":
        player["inventory"].remove("crate of horseshoes")
        log = (
            "Squire Godspeed takes the heavy crate, nearly buckling under its weight.\n"
            "\"Finally! I ordered these a week ago. Lovejoy spends too much time filling orders for those corrupt Wallmakers and leaves the rest of us waiting.\"\n"
            "\"Tell your master to sort out his priorities.\"\n"
            "*** Horseshoes delivered! ***"
        )
        return player, log, "MAIN"

    if choice == "Take Riding Lesson":
        player["total_game_minutes"] += 60
        player["riding_lessons_completed"] += 1
        log = "\"Lovejoy sent you back? And the Mayor has already paid for your lesson? Excellent.\"\n\"Step into the yard. Let's see how you handle a saddle.\"\n*** You spend an hour learning to ride! ***"
        
        if player["riding_lessons_completed"] >= 5 and "ride" not in player["skills"]:
            player["skills"].append("ride")
            log += "\n*** Congratulations! You have mastered the 'ride' skill! ***"
        elif player["riding_lessons_completed"] < 5:
            log += f"\n*** You completed a riding lesson! ({player['riding_lessons_completed']}/5 completed) ***"
            
        player["active_mayor_task"] = "collect_shod_horse"
        return player, log, "MAIN"
        
    if choice == "Return Mayor's Stallion":
        player["inventory"].remove("fed and watered stallion")
        player["active_mayor_task"] = "report_to_praisegod_3"
        return player, "\"Ah, he looks well rested and fed. Good job. I'll put him in his stall.\"", "MAIN"

    if choice == "Riding Lesson (10s)":
        if "ride" in player["skills"]:
            return player, "'I already taught you everything I know! You are a natural rider.'", "MAIN"
        current_day = (player["total_game_minutes"] // 1000) + 1
        if player["last_riding_lesson_day"] == current_day:
            return player, "\"You've already had a lesson today. Both horse and rider need time to rest. Come back tomorrow.\"", "MAIN"
        if player["silver"] >= 10:
            player["silver"] -= 10
            player, _ = advance_time(100, player)
            player["riding_lessons_completed"] += 1
            player["last_riding_lesson_day"] = current_day
            log = (
                "You pay the 10 silver fee. Squire Godspeed takes you out back and spends an hour\n"
                "teaching you the fundamentals of commanding a steed.\n"
                f"*** You completed a riding lesson! ({player['riding_lessons_completed']}/5 completed) ***"
            )
            if player["riding_lessons_completed"] >= 5:
                player["skills"].append("ride")
                log += "\n*** Congratulations! You have mastered the 'ride' skill! ***"
            return player, log, "MAIN"
        return player, f"\"My time isn't free. A lesson costs 10 silver, and you only have {player['silver']}.\"", "MAIN"

    if choice == "Stable Horse (2s/day tab)":
        if "horse" in player["inventory"]:
            player["inventory"].remove("horse")
            player["riding_horse"] = False
            player["horse_stabled"] = True
            player["horse_stabled_day"] = (player["total_game_minutes"] // 1000) + 1
            player["horse_hunger"] = 100
            player["horse_thirst"] = 100
            log = (
                "Squire Godspeed leads your horse into a fresh stall and hangs its bridle on the peg.\n"
                "\"Two silver a day for hay, water, and stabling, paid when you collect the beast.\"\n"
                "\"Don't let your tab run past 20 silver—if you abandon it here for more than ten days without paying, I'll sell the horse to recoup my feed bill!\"\n\n"
                "*** Your horse is stabled! (Tab: 2s/day | Foreclosure limit: >20s) ***"
            )
            return player, log, "MAIN"
        return player, "\"You don't have a horse with you to stable.\"", "MAIN"

    if choice.startswith("Collect Stabled Horse"):
        if not player.get("horse_stabled"):
            return player, "\"You don't have a horse stabled here.\"", "MAIN"
        debt = get_stabling_debt(player)
        if player["silver"] < debt:
            return player, (
                f"\"Your stabling tab stands at {debt} silver (2s per day), and you only have {player['silver']} silver!\"\n"
                "\"Come back with the coin before your tab passes 20 silver, or I'll sell the beast on the open market!\""
            ), "MAIN"
        player["silver"] -= debt
        player["horse_stabled"] = False
        player["horse_stabled_day"] = 0
        player["horse_hunger"] = 100
        player["horse_thirst"] = 100
        player["inventory"].append("horse")
        log = (
            f"You settle your {debt}-silver stabling tab with Squire Godspeed and lead your well-rested horse out of the stall.\n"
            f"*** Horse Collected! (-{debt} Silver | Remaining: {player['silver']}s | Horse Hunger/Thirst: 100/100) ***"
        )
        return player, log, "MAIN"

    if choice == "Buy a Horse":
        if "horse" in player["inventory"] or player.get("horse_stabled"):
            return player, "\"I already sold you a horse! One is plenty for a lone adventurer.\"", "MAIN"
        player["stable_state"] = "buy_horse"
        if player.get("horse_sold_for_debt"):
            log = (
                "Squire Godspeed smirks coldly and gestures toward a familiar stall.\n"
                "\"Aye, I have ONE horse for sale—the very beast you abandoned here until your stabling tab passed 20 silver!\"\n"
                "\"If you want to buy your old mount back, it'll cost you the full 50 silver.\""
            )
        else:
            log = (
                "\"I only have one horse available for purchase at the moment.\"\n"
                "\"Its owner has not paid the stable fees and I am tired of spending my own money on its hay.\"\n"
                "\"You can have it for 50 silver.\""
            )
        return player, log, "NPC_DIALOGUE"

    if choice == "Buy horse for 50 silver.":
        if player["silver"] >= 50:
            player["silver"] -= 50
            player["inventory"].append("horse")
            player["stable_state"] = None
            player["horse_sold_for_debt"] = False
            log = f"You hand over the heavy pouch of silver. Squire Godspeed leads a sturdy, fast steed out to you.\n*** You bought a horse! (Remaining Silver: {player['silver']}) ***"
            return player, log, "MAIN"
        return player, f"\"You don't have 50 silver! You only have {player['silver']}. Don't waste my time.\"", "NPC_DIALOGUE"
        
    if choice == "Challenge price and offer 25 silver.":
        roll = random.randint(1, 6)
        log = f"You look him in the eye and say, 'I'll give you 25 silver for it.'\n\n*** You rolled a {roll}! ***\n\n"
        
        final_price = 50
        if roll <= 2:
            log += "Squire Godspeed chuckles. \"You drive a hard bargain. Fine, 25 silver it is.\"\n"
            final_price = 25
        elif roll <= 4:
            log += "Squire Godspeed shakes his head firmly. \"50 silver. Take it or leave it.\"\n"
            final_price = 50
        else:
            log += "Squire Godspeed scowls. \"Are you insulting my animals? The price just went up to 75 silver!\"\n"
            final_price = 75
            
        if player["silver"] >= final_price:
            player["silver"] -= final_price
            player["inventory"].append("horse")
            player["horse_sold_for_debt"] = False
            log += f"\nYou hand over {final_price} silver. Squire Godspeed leads the steed out to you.\n*** You bought a horse! (Remaining Silver: {player['silver']}) ***"
        else:
            log += f"\n\"And you don't even have {final_price} silver! Get out of here until you have the coin.\""
            
        player["stable_state"] = None
        return player, log, "MAIN"

    if choice == "Apply for Job":
        if player["current_job"] is not None and player["current_job"] != "stables":
            return player, "'You already have a job elsewhere! I need someone fully dedicated, not a moonlighter.'", "MAIN"
        if player["reputation"] >= 1:
            player["current_job"] = "stables"
            player["current_tenure"] = 0
            return player, "'Alright, you're hired. Welcome to the stables. Speak to me again when you are ready to start a shift.'", "MAIN"
        return player, "Squire Godspeed eyes you up and down suspiciously.\n'Come back when you've made a better name for yourself. (Requires 1 Reputation)'", "MAIN"

    # --- STARTING A SHIFT ---
    if choice.startswith("Start Shift"):
        ok, msg = can_start_shift(player)
        if not ok:
            return player, msg, "MAIN"
        player = mark_shift_started(player)
            
        shifts = player["stable_shifts"]

        # --- SHIFT 6 EVALUATION: NOTICEBOARD OR DISMISSAL (GAME OVER) ---
        if shifts == 5 and not player.get("stable_shift_6_prompted"):
            eligible = get_eligible_chapter_2_routes(player)
            if not eligible:
                player["current_job"] = None
                player["current_tenure"] = 0
                log = (
                    "Squire Godspeed looks over his ledger and shakes his head heavily.\n"
                    "\"I am afraid that you have failed to reach the level that we expect of a stable hand in the time that you have been here. "
                    "We are going to have to let you go. I cannot see you acquiring any further work in Murum. "
                    "You will have to try your luck on the road. I wish you luck.\"\n\n"
                    "*** GAME OVER: You failed to qualify for any Chapter 2 path and have been dismissed from Murum! ***"
                )
                return player, log, "DEAD"

            player["stable_state"] = "shift_6_prompt"
            player["chapter_2_unlocked"] = True
            log = (
                "Squire Godspeed lowers his clipboard and looks at you with respect.\n"
                "\"Listen, Noburu. With the experience and horse-sense you've gained here, there may be new opportunities for you "
                "if you look at the Noticeboard in the Town Hall.\"\n"
                "\"Do you want to proceed with your shift today, or hand in your notice with immediate effect?\""
            )
            return player, log, "NPC_DIALOGUE"
        
        if shifts == 0:
            player["inventory"].append("halter")
            player["active_stable_task"] = "find_coryllus"
            player["coryllus_spooked_by_lunge"] = False
            db.npc_database["coryllus"]["location"] = (8, 13)
            db.npc_database["mayors maid"]["location"] = (8, 15)
            log = (
                "Squire Godspeed looks frantic. \"Thank the heavens you are here. We have a crisis.\"\n"
                "\"Coryllus, the Mayor's highly temperamental prized stallion, has bolted!\"\n"
                "\"If the Mayor finds out, we will both be ruined. Take this halter. You must find him quietly.\"\n"
                "\"He is terrified of loud noises, so you can't just walk up to him. However, he goes weak at the knees for fresh cobnuts.\"\n"
                "\"I believe there is a tree that drops them outside the Town Hall. Ask around town to see where he ran!\"\n"
                "\"Start by travelling South, that is the direction Coryllus bolted in.\"\n\n"
                "*** SHIFT STARTED! Locate Coryllus! ***"
            )
            return player, log, "MAIN"
            
        elif shifts == 1:
            player["silver"] += 10
            player["active_stable_task"] = "buy_tonic"
            log = (
                "Squire Godspeed wipes his brow. \"Our prized mare is close to her time.\"\n"
                "\"Take this 10 silver, run to the Apothecary at the High Street, and buy Birthing Tonic.\"\n"
                "\"Hurry back. We don't have much time.\"\n\n"
                "*** SHIFT STARTED! Go to the Apothecary at the High Street! ***"
            )
            return player, log, "MAIN"

        elif shifts == 2:
            player["active_stable_task"] = "find_lightfoot_loft"
            db.npc_database["head hostler"]["location"] = "stable loft"
            log = (
                "Squire Godspeed looks stressed, staring at a ruined book.\n"
                "\"We have a problem. Someone hasn't paid their stabling fees, but my ledger has disappeared.\"\n"
                "\"I don't know who owes me money, but I do know that the Wallmakers paid their bill on Wednesday.\"\n"
                "\"Why don't you talk to Head Hostler Lightfoot? I think he is upstairs in the Stable Loft.\"\n\n"
                "*** SHIFT STARTED! Speak to Head Hostler Lightfoot in the loft! ***"
            )
            return player, log, "MAIN"

        elif shifts == 3:
            player["active_stable_task"] = "investigate_ledger"
            db.npc_database["fromabove"]["location"] = "stables"
            db.npc_database["head hostler"]["location"] = "stable loft"
            db.npc_database["horse groom"]["location"] = "dog and duck pub"
            
            log = (
                "Squire Godspeed glares at you as you approach.\n"
                "\"I found the ledger. Someone threw it into the water trough intentionally to hide their tracks.\"\n"
                "\"There are four of us working here, including you. You're the newest, so you're my prime suspect.\"\n"
                "\"Prove your innocence, or you're fired. Start asking around.\"\n\n"
                "*** SHIFT STARTED! Speak to the stable workers and see if they know anything. ***"
            )
            return player, log, "MAIN"

        elif shifts == 4:
            player["active_stable_task"] = "stall_allocation"
            player["stable_state"] = "stall_allocation"
            db.npc_database["truthtale"]["location"] = "stables"
            
            log = (
                "Squire Godspeed is arguing furiously with Truthtale.\n"
                "\"We demand four indoor stalls!\" Truthtale yells. \"Stabling is in our union contract!\"\n\n"
                "Godspeed turns to you, desperate. \"We only have three large double-stalls inside.\"\n"
                "\"That means we have to fit 6 horses into 3 stalls: The Mayor's Coryllus, the Guard's Destrier, and these 4 Union Draught horses.\"\n"
                "\"Coryllus hates Draught horses, and the Destrier is too aggressive to be near Coryllus.\"\n"
                "\"Help me figure out this allocation! Who do we pair together?!\""
            )
            return player, log, "NPC_DIALOGUE"

        else:
            shift_pay = 35 if "stable master" in player.get("skills", []) else 20
            player["silver"] += shift_pay
            player["equusense"] = player.get("equusense", 0) + 1
            player["stable_shifts"] += 1
            player["current_tenure"] += 1
            player = mark_shift_completed(player)
            player, _ = advance_time(300, player)
            log = (
                "You spend the day grooming the mounts, mucking out the stalls, and exercising the horses in the yard.\n"
                f"*** Shift Completed! You earned {shift_pay} silver and +1 Equusense (Total: {player['equusense']})! ***"
            )
            return player, log, "MAIN"

    # --- RETURN FROM TASK LOGIC ---
    if choice == "Return from Task":
        task = player.get("active_stable_task")
        
        if task == "find_coryllus":
            return player, "\"Have you found Coryllus yet?! Keep your voice down. Ask the guards or the Mayor's staff if they saw anything!\"", "MAIN"
            
        if task == "return_coryllus" and "coryllus (haltered)" in player["inventory"]:
            player["inventory"].remove("coryllus (haltered)")
            player["active_stable_task"] = None
            player["silver"] += 20
            player["stable_shifts"] += 1
            player["current_tenure"] += 1
            player["equusense"] = player.get("equusense", 0) + 1
            player = mark_shift_completed(player)
            player, _ = advance_time(120, player)
            db.npc_database["mayors maid"]["location"] = None

            rep_note = ""
            if player.pop("coryllus_spooked_by_lunge", False):
                player["reputation"] -= 2
                rep_note = "\n\"Though the Mayor's grooms saw you lunging at Coryllus in the pasture and word of your clumsy handling has spread!\" (-2 Reputation)"
            else:
                player["reputation"] += 1
                rep_note = " (+1 Reputation)"
            
            log = (
                "Squire Godspeed nearly faints with relief as you lead Coryllus into the yard.\n"
                f"\"You found him! And you brought him back in one piece.\"{rep_note}\n\n"
                f"*** Shift Completed! You earned 20 silver and developed your Equusense! (Total silver: {player['silver']}, Equusense: {player['equusense']}) ***"
            )
            if player["union_status"] is None:
                log += (
                    "\n\nAs you are cleaning up the stall, a grime-covered horse groom leans over the door.\n"
                    "\"You handled that well. But Godspeed expects too much of us for a pittance. Are you in the Union?\"\n"
                    "\"Go to the Dog and Duck Pub and ask the Landlord about signing up. We look after our own.\"\n"
                    "\"Tell him the stable hands sent you, and your first night's bed is on the house.\""
                )
                player["union_status"] = "invited"
            return player, log, "MAIN"
            
        if task == "buy_tonic":
            if "birthing tonic" in player["inventory"]:
                player["active_stable_task"] = "gather_supplies"
                log = (
                    "\"Good, you have the tonic!\" Godspeed says, taking a frantic breath.\n"
                    "\"Head Hostler Lightfoot is off drinking at the tavern again, the useless sod. I need you to gather the rest of the supplies while I prep the stall.\"\n"
                    "\"Go upstairs to the Stable Loft and gather Clean Straw.\"\n"
                    "\"Go to the Mayor's Staff Entrance and ask the Scullery Maid for a Bucket of Hot Water.\"\n"
                    "\"And enter the Tack Room and search Lightfoot's desk for the Foaling Manual!\"\n\n"
                    "*** TASK UPDATED: Gather Straw, Hot Water, and the Foaling Manual! ***"
                )
                return player, log, "MAIN"
            return player, "\"Where is the Birthing Tonic? The Apothecary is at the High Street! Hurry!\"", "MAIN"
            
        if task == "gather_supplies":
            has_straw = "clean straw" in player["inventory"]
            has_water = "bucket of hot water" in player["inventory"]
            has_manual = "foaling manual" in player["inventory"]
            
            if has_straw and has_water and has_manual:
                player["stable_mistakes"] = 0
                player["stable_state"] = "quiz_1"
                log = (
                    "You rush back to the main stable with your arms full of supplies.\n"
                    "\"She's early! And the foal is breeched!\" Godspeed yells, running past you toward the door.\n"
                    "\"I have to fetch the vet! Stay with her! Read the manual and use the supplies!\"\n"
                    "He disappears into the street. You are entirely on your own.\n\n"
                    "*** EMERGENCY: FOALING CRISIS ***\n"
                    "You quickly flip open the Foaling Manual. A massive coffee stain obscures the keywords!\n\n"
                    f"{db.readables_database['foaling manual']['text']}\n\n"
                    "The mare thrashes, covered in sweat and stable muck. Before touching her, you must:"
                )
                return player, log, "NPC_DIALOGUE"
            return player, "\"You don't have everything! I need Clean Straw from the loft, Hot Water from the Mayor's Scullery Maid, and the Foaling Manual from the Tack Room!\"", "MAIN"

        if task in ["find_lightfoot_loft", "search_tack_room"]:
            return player, "\"Have you found out who owes us money yet? Check the loft or search the tack room!\"", "MAIN"
            
        if task == "report_manager_1":
            if "smudged receipt" in player["inventory"]:
                player["active_stable_task"] = "find_union_worker"
                db.npc_database["horse groom"]["location"] = "dog and duck pub"
                log = (
                    "Godspeed inspects the torn ledger and the receipt.\n"
                    "\"A receipt for 30 silver that was paid? That is good progress.\"\n"
                    "\"I have been racking my brain and I have remembered that the Blacksmith's bill was 15 silver.\"\n"
                    "\"Perhaps if you speak to our unionised stable worker... I believe you will find them at the Dog and Duck Pub on their break.\"\n\n"
                    "*** TASK UPDATED: Find the stable worker at the Dog and Duck Pub! ***"
                )
                return player, log, "MAIN"
            return player, "\"Where are the ledger pages? Keep searching the tack room!\"", "MAIN"

        if task == "find_union_worker":
            return player, "\"Go to the Dog and Duck Pub and ask the stable worker if they remember anything!\"", "MAIN"

        if task == "solve_puzzle":
            player["stable_state"] = "solve_puzzle"
            log = (
                "\"You spoke to the worker? Excellent. Let's put all the pieces together.\"\n"
                "\"Based on what you've learned, who is the client with the unpaid bill?\""
            )
            return player, log, "NPC_DIALOGUE"
            
        if task == "investigate_ledger":
            return player, "\"Found anything yet? Your job is on the line.\"", "MAIN"
            
        if task == "confront_fromabove":
            return player, "\"Stop wasting time! Go talk to Fromabove and see what he knows!\"", "MAIN"

        if task == "report_to_godspeed_4":
            player["stable_state"] = "shift_4_decision"
            log = (
                "Squire Godspeed crosses his arms.\n"
                "\"Well? Who destroyed my ledger? Give me a name or pack your bags.\"\n\n"
                "You look over and see Fromabove sweeping the yard, his hands shaking."
            )
            return player, log, "NPC_DIALOGUE"

        if task in ["stall_allocation", "who_goes_outside"]:
            player["stable_state"] = task
            return player, "\"We have a standoff! Help me solve this stall allocation!\"", "NPC_DIALOGUE"

        if task == "setup_grazing_field":
            return player, "\"Have you set up the camp in the Grazing Field yet? Buy a 'Tent' from the Commissar and a 'Sack of Oats' from the Chandler!\"", "MAIN"

        if task == "report_manager_5":
            player["silver"] += 40
            player["strength"] += 1
            player["equusense"] = player.get("equusense", 0) + 1
            player["stable_shifts"] += 1
            player["current_tenure"] += 1
            player["active_stable_task"] = None
            player["stable_state"] = None
            
            db.npc_database["truthtale"]["location"] = None
            player = mark_shift_completed(player)
            player, _ = advance_time(120, player)

            # --- BRANCH A: Dedicated Union Member (> 5 Union Faction) ---
            if player.get("union_status") == "joined" and player.get("faction_union", 0) > 5:
                player["reputation"] += 3
                player["faction_union"] = min(10, modify_faction(player, "faction_union", 5))
                player["steward_nomination_eligible"] = True
                db.npc_database["horse groom"]["location"] = "dog and duck pub"
                
                log = (
                    "Truthtale inspects the Grazing Field and nods approvingly.\n"
                    "\"A private tent and premium oats? Acceptable. The Union is satisfied.\"\n\n"
                    "Squire Godspeed reluctantly hands over your 40 silver fee.\n\n"
                    "As you step out into the yard, the unionised horse groom catches your eye and pulls you aside:\n"
                    "\"Word travels fast, comrade. The Union Functional Council has been hearing good things about you.\"\n"
                    "\"They want to have a chat with you at the Dog and Duck Pub. Head over there when you're ready.\"\n\n"
                    "*** Great Success! (+3 Reputation, +1 Strength, +1 Equusense, +5 Union Faction, 40 Silver) ***\n"
                    "*** STORY BRANCH: Speak to the Horse Groom at the Dog and Duck Pub! ***"
                )
                return player, log, "MAIN"

            # --- BRANCH B: Non-Union Player (Company Loyalist) ---
            elif player.get("union_status") != "joined":
                player["reputation"] += 4
                if "stable master" not in player.get("skills", []):
                    player.setdefault("skills", []).append("stable master")
                
                log = (
                    "Squire Godspeed wipes tears of joy from his eyes.\n"
                    "\"You solved an impossible crisis with pure diplomacy, and you stood firm with management!\"\n"
                    "\"You've proven yourself indispensable. I am promoting you to Stable Master!\"\n"
                    "\"You'll receive an official pay rise to 35 silver for any future shifts here.\"\n\n"
                    "*** Great Success! (+4 Reputation, +1 Strength, +1 Equusense, 40 Silver Bonus) ***\n"
                    "*** PROMOTED: You are now Stable Master! (+15s base pay on future shifts) ***"
                )
                return player, log, "MAIN"

            # --- BRANCH C: Status Quo (Union member with low faction) ---
            else:
                player["reputation"] += 2
                player["faction_union"] = min(10, modify_faction(player, "faction_union", 2))
                log = (
                    "Truthtale and Godspeed grudgingly settle the horses.\n"
                    "\"A tenuous peace,\" Godspeed sighs, handing over your 40 silver wage.\n"
                    "\"Things are still tense between the bosses and the floor, but at least nobody lost their head today.\"\n\n"
                    "*** Shift Completed! (+2 Reputation, +1 Strength, +1 Equusense, +2 Union Faction, 40 Silver) ***\n"
                    "*** Things remain unchanged at the stables. ***"
                )
                return player, log, "MAIN"

        if task == "standard_stable_shift":
            shift_pay = 35 if "stable master" in player.get("skills", []) else 20
            player["silver"] += shift_pay
            player["stable_shifts"] += 1
            player["current_tenure"] += 1
            player["active_stable_task"] = None
            player = mark_shift_completed(player)
            player, _ = advance_time(120, player)
            
            title = "Stable Master" if "stable master" in player.get("skills", []) else "stable hand"
            log = (
                f"Squire Godspeed inspects the clean stalls and well-brushed horses.\n"
                f"\"Fine work as always, {title}. Here is your wage.\"\n\n"
                f"*** Shift Completed! You earned {shift_pay} silver! (Total: {player['silver']}) ***"
            )
            return player, log, "MAIN"

    # --- THE FOALING QUIZ ---
    if state == "quiz_1":
        if choice != "Wash hands in hot water": player["stable_mistakes"] += 1
        player["stable_state"] = "quiz_2"
        log = "Correct! You quickly sanitize your hands in the steaming bucket.\n\n" if choice == "Wash hands in hot water" else "Wrong! You touch the mare with dirty hands, risking severe infection!\n\n"
        log += "You are sterile, but the mare is panicked and kicking wildly. You must:"
        return player, log, "NPC_DIALOGUE"
        
    if state == "quiz_2":
        if choice != "Administer Tonic": player["stable_mistakes"] += 1
        player["stable_state"] = "quiz_3"
        log = "Correct! You pour the tonic into her mouth. Her eyes soften and she stops kicking.\n\n" if choice == "Administer Tonic" else "Wrong! Your action fails to calm her, and she nearly kicks you in the ribs!\n\n"
        log += "The mare is calmer. You inspect the foal. It is stuck! The manual says 'adjust the [SMEAR] limbs. Leave the hind legs alone.'\nWhat do you do?"
        return player, log, "NPC_DIALOGUE"
        
    if state == "quiz_3":
        if choice != "Reposition forelegs": player["stable_mistakes"] += 1
        player["stable_state"] = "quiz_4"
        log = "Correct! You gently align the forelegs so they face outward.\n\n" if choice == "Reposition forelegs" else "Wrong! You mishandle the limbs, causing the mare extreme distress!\n\n"
        log += "The foal is aligned, but the mare is exhausted. You need to pull, but when?"
        return player, log, "NPC_DIALOGUE"
        
    if state == "quiz_4":
        if choice != "Pull in rhythm": player["stable_mistakes"] += 1

        player["stable_state"] = None
        for item in ["birthing tonic", "clean straw", "bucket of hot water"]:
            if item in player["inventory"]: player["inventory"].remove(item)
            
        player["stable_shifts"] += 1
        player["current_tenure"] += 1
        player["active_stable_task"] = None
        player = mark_shift_completed(player)
        player, _ = advance_time(120, player)
        
        log = "Correct! You pull smoothly as her muscles contract, aiding the birth.\n\n...\n\n" if choice == "Pull in rhythm" else "Wrong! You pull against her natural rhythm, causing unnecessary strain and pain!\n\n...\n\n"

        if player["stable_mistakes"] >= 2:
            rep_loss = player["stable_mistakes"] * 2
            player["reputation"] -= rep_loss
            log += (
                "Squire Godspeed returns with the vet, but it is too late. The foal did not survive your mishandling.\n"
                "Godspeed is devastated, and the mare's aristocratic owner publicly denounces your incompetence!\n"
                f"*** Tragic Outcome! (-{rep_loss} Reputation, No Pay) ***"
            )
            
        elif player["stable_mistakes"] == 0:
            player["reputation"] += 2
            player["silver"] += 30
            player["equusense"] = player.get("equusense", 0) + 2
            log += (
                "Squire Godspeed bursts through the doors with the vet, just in time to see the healthy foal take its first breath!\n"
                "You lay the newborn down on the Clean Straw you gathered.\n"
                "The foal glows with the presence of new life. It was a perfect delivery.\n"
                "\"By the gods... you did it!\" Godspeed laughs, clapping you on the back. \"You're a natural!\"\n"
                f"*** Great Success! (+2 Reputation, 30 Silver Bonus, +2 Equusense | Total Silver: {player['silver']}, Equusense: {player['equusense']}) ***"
            )
        else:
            rep_loss = player["stable_mistakes"] * 2
            player["reputation"] -= rep_loss
            player["silver"] += 30
            player["equusense"] = player.get("equusense", 0) + 1
            log += (
                "Squire Godspeed bursts through the doors with the vet, just in time to see the healthy foal take its first breath!\n"
                "You lay the newborn down on the Clean Straw you gathered.\n"
                "\"By the gods... you did it!\" Godspeed sighs, though the mare's wealthy owner complains loudly about the bruising.\n"
                f"*** A Success, but a near miss! (-{rep_loss} Reputation, 30 Silver Bonus, +1 Equusense | Total Silver: {player['silver']}, Equusense: {player['equusense']}) ***"
            )
            
        return player, log, "MAIN"

    # --- SHIFT 3 PUZZLE RESOLUTION ---
    if state == "solve_puzzle":
        if choice == "The Mayor":
            player["reputation"] += 2
            player["charisma"] += 1
            player["silver"] += 25
            player["stable_shifts"] += 1
            player["current_tenure"] += 1
            player["equusense"] = player.get("equusense", 0) + 1
            player["active_stable_task"] = None
            player["stable_state"] = None
            
            for item in ["torn ledger page", "smudged receipt"]:
                if item in player["inventory"]:
                    player["inventory"].remove(item)
                    
            db.npc_database["head hostler"]["location"] = None
            db.npc_database["horse groom"]["location"] = None
            
            player = mark_shift_completed(player)
            player, _ = advance_time(120, player)
            
            log = (
                "\"The Mayor! Of course! Their bill was for 45 silver, and they haven't sent their clerk with the coin yet.\"\n"
                "\"Brilliant deductive work! You saved the stables a heavy loss.\"\n"
                f"*** Great Success! (+2 Reputation, +1 Charisma, 25 Silver, +1 Equusense | Total Reputation: {player['reputation']}, Total Silver: {player['silver']}, Equusense: {player['equusense']}) ***"
            )
            return player, log, "MAIN"
        else:
            return player, "\"That doesn't make sense! Check your clues again! (Use 'Read' to inspect your documents).\"", "NPC_DIALOGUE"

    # --- SHIFT 4 CONSEQUENCE RESOLUTION ---
    if state == "shift_4_decision":
        player["stable_shifts"] += 1
        player["current_tenure"] += 1
        player["active_stable_task"] = None
        player["stable_state"] = None
        player["beers_drank"] = 0
        
        db.npc_database["fromabove"]["location"] = None
        db.npc_database["head hostler"]["location"] = None
        db.npc_database["horse groom"]["location"] = None
        
        player = mark_shift_completed(player)
        player, _ = advance_time(120, player)
        
        if choice == "Report Fromabove (Loyal to Boss)":
            player["silver"] += 30
            player["reputation"] += 2
            player["equusense"] = player.get("equusense", 0) + 1
            log = (
                "You tell Godspeed everything. He marches over to Fromabove and fires him on the spot.\n"
                "\"I knew it was an inside job,\" Godspeed says. \"Thank you for your honesty. Here is your wage.\"\n\n"
            )
            if player["union_status"] == "joined":
                modify_faction(player, "faction_union", -8)
                log += "*** You betrayed a Union brother! (-8 Union Faction, +2 Reputation, +1 Equusense, 30 Silver) ***"
            else:
                modify_faction(player, "faction_union", -2)
                log += "*** The workers sneer at you for snitching. (-2 Union Faction, +2 Reputation, +1 Equusense, 30 Silver) ***"
            return player, log, "MAIN"
            
        elif choice == "Cover for Fromabove (Loyal to Union)":
            player["silver"] += 10
            player["reputation"] -= 2
            player["equusense"] = player.get("equusense", 0) + 1
            log = (
                "You lie, claiming a stray dog dragged it into the trough while you were all busy.\n"
                "Godspeed scowls as the wealthy horse owners complain about the chaotic bookkeeping. \"A dog? Fine. But I'm docking everyone's pay to cover the losses.\"\n\n"
            )
            if player["union_status"] == "joined":
                modify_faction(player, "faction_union", 5)
                log += "*** You protected a brother! True solidarity! (+5 Union Faction, -2 Reputation, +1 Equusense, 10 Silver) ***"
            else:
                modify_faction(player, "faction_union", 3)
                log += "*** You earned unexpected respect from the workers. (+3 Union Faction, -2 Reputation, +1 Equusense, 10 Silver) ***"
            return player, log, "MAIN"

    # --- SHIFT 5 PUZZLE RESOLUTION ---
    if state == "stall_allocation":
        if choice == "Conclude they cannot fit":
            player["stable_state"] = "who_goes_outside"
            player["active_stable_task"] = "who_goes_outside"
            log = (
                "You do the math. If Coryllus can't be with the Draughts, and can't be with the Destrier, he must be alone.\n"
                "That leaves 5 horses for 2 stalls. Maximum capacity is 4.\n\n"
                "Godspeed gasps. \"By the gods, you're right. It is mathematically impossible. We are short one stall.\"\n"
                "\"Someone has to sleep outside in the Grazing Field. But who?!\""
            )
            return player, log, "NPC_DIALOGUE"
        elif choice == "Pair Coryllus & Destrier":
            return player, "\"Are you mad?!\" Godspeed cries. \"They are both aggressive alphas! They will kick the stable to splinters!\"", "NPC_DIALOGUE"
        elif choice == "Pair Coryllus & Draught Horse":
            return player, "\"I just told you, Coryllus hates Draught horses! He will bite them! Try again!\"", "NPC_DIALOGUE"
            
    if state == "who_goes_outside":
        if choice == "Send Union outside":
            player["stable_state"] = None
            player["active_stable_task"] = "setup_grazing_field"
            log = (
                "\"Put the Union horses outside?\" Godspeed pales.\n"
                "\"Truthtale will call a strike unless we make the Grazing Field as comfortable as a royal suite.\"\n"
                "\"Go to the High Street! Buy a 'Tent' from the Commissary to keep the rain off, and go to the Market to buy a 'Sack of Oats' from the Chandler for them to eat.\"\n"
                "\"Once you have both, go to the Grazing Field and select 'Action -> Gather / Search' to set up the camp!\""
            )
            return player, log, "MAIN"
        elif choice == "Send Coryllus outside":
            return player, "\"The Mayor will have my head on a spike if their prized horse is left in the rain! Choose again!\"", "NPC_DIALOGUE"
        elif choice == "Send Destrier outside":
            return player, "\"Captain Wealdhere will arrest us both if their warhorse catches a chill! Choose again!\"", "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# CORYLLUS (THE HORSE)
# -------------------------------------------------------------------------
def get_coryllus_options(player):
    options = ["Approach with halter", "Whistle loudly"]
    if "cobnuts" in player["inventory"]:
        options.append("Offer cobnuts")
    options.append("Back away")
    return options

def resolve_coryllus(choice, player):
    if choice == "Back away":
        return player, "You slowly back away, leaving him cornered.", "MAIN"
        
    if choice == "Approach with halter":
        player["health"] -= 1
        player["coryllus_spooked_by_lunge"] = True
        return player, f"You lunge forward with the halter. Coryllus rears up on his hind legs, kicking wildly!\nHe evades you completely. You need a way to calm him down first.\n*** You took a glancing blow! (-1 Health, Current: {player['health']}) ***", "MAIN"
        
    if choice == "Whistle loudly":
        player["coryllus_spooked_by_lunge"] = True
        return player, "You whistle loudly. Coryllus's eyes widen in terror—loud noises are what spooked him in the first place!\nHe bucks and refuses to let you near.", "MAIN"
        
    if choice == "Offer cobnuts":
        player["inventory"].remove("cobnuts")
        if "halter" in player["inventory"]: player["inventory"].remove("halter")
        player["inventory"].append("coryllus (haltered)")
        player["active_stable_task"] = "return_coryllus"
        
        db.npc_database["coryllus"]["location"] = None
        
        log = (
            "You hold out the handful of fresh cobnuts. Coryllus freezes, his ears flicking forward.\n"
            "The smell of his favorite treat overrides his panic. He steps forward and begins crunching happily.\n"
            "While he is distracted, you smoothly slip the halter over his head and secure it.\n\n"
            "*** You captured Coryllus! Return him to the Stable Manager. ***"
        )
        return player, log, "MAIN"


# -------------------------------------------------------------------------
# HEAD HOSTLER (LIGHTFOOT)
# -------------------------------------------------------------------------
def get_head_hostler_options(player):
    task = player.get("active_stable_task")
    b_task = player.get("active_blacksmith_task")
    
    options = []
    if b_task == "stables_fire_rescue" and not player.get("fire_extinguished"):
        options.append("Drag him out of the smoke!")
        
    if task == "find_lightfoot_loft":
        options.append("Ask about unpaid bill")
    if task == "investigate_ledger":
        options.append("Ask about destroyed ledger")
        
    options.append("Leave")
    return options

def resolve_head_hostler(choice, player):
    if choice == "Leave":
        return player, "\"I'm on my break. Leave me be.\"", "MAIN"

    if choice == "Drag him out of the smoke!":
        db.npc_database["head hostler"]["location"] = None
        log = (
            "You haul Lightfoot up by his collar and drag him out into the fresh air. He coughs up black smoke, barely conscious.\n"
            "\"The Wallmakers...\" he gasps. \"Arson... trying to destroy the true accounts...\"\n"
            "\"Under the floorboards in the tack room! Grab the hidden secret ledger!\"\n"
            "\"And use the buckets of sand from outside the barn to kill the fire!\"\n\n"
            "*** QUEST: Use 'Gather / Search' in the Tack Room to get the ledger, and outside the Stables to get Sand! ***"
        )
        return player, log, "MAIN"

    if choice == "Ask about unpaid bill":
        player["active_stable_task"] = "search_tack_room"
        log = (
            "Head Hostler Lightfoot is resting on a bale of hay, nursing a mild hangover.\n"
            "\"An unpaid bill? I do not know who hasn't paid their bill...\"\n"
            "\"But I do know the regular fee we charge the Guard is 25 silver, and I saw them pay it myself.\"\n"
            "\"Why don't you search the Tack Room downstairs and see if there is more information there?\""
        )
        return player, log, "MAIN"

    if choice == "Ask about destroyed ledger":
        log = (
            "Head Hostler Lightfoot glances away nervously and crosses his arms.\n"
            "\"I didn't see anything happen to the ledger. We don't spy on our own here.\""
        )
        return player, log, "MAIN"

    return player, "\"I'm on my break. Leave me be.\"", "MAIN"


# -------------------------------------------------------------------------
# UNIONISED HORSE GROOM (MUCHMERCEYE)
# -------------------------------------------------------------------------
def get_horse_groom_options(player):
    task = player.get("active_stable_task")
    state = player.get("groom_dialogue_state")

    if state == "steward_offer":
        return ["Accept Nomination (Run for Steward)", "Decline Nomination"]
    if player.get("steward_nomination_eligible") and player.get("current_building") == "dog and duck pub":
        return ["Meet with Union Council", "Leave"]
    if task == "find_union_worker":
        return ["Ask about unpaid bill", "Leave"]
    if task == "investigate_ledger":
        return ["Ask about destroyed ledger", "Leave"]
        
    return ["Leave"]

def resolve_horse_groom(choice, player):
    if choice == "Leave":
        return player, "\"Solidarity, comrade. Enjoy your drink.\"", "MAIN"

    if choice == "Ask about unpaid bill":
        player["active_stable_task"] = "solve_puzzle"
        log = (
            "The unionised stable worker is nursing a murky ale at the pub.\n"
            "\"The missing bill? I don't know who hasn't paid...\"\n"
            "\"But I saw the ledger before it got ruined. I do know that the unpaid bill was for exactly 45 silver.\""
        )
        return player, log, "MAIN"

    if choice == "Ask about destroyed ledger":
        log = (
            "The stable worker scowls and takes a long drag from his tankard.\n"
            "\"Keep your nose out of it. Things happen. Buy a drink or leave me be.\""
        )
        return player, log, "MAIN"

    if choice == "Meet with Union Council":
        player["groom_dialogue_state"] = "steward_offer"
        log = (
            "The groom leads you to a private booth in the back of the Dog and Duck.\n"
            "Two senior delegates from the Functional Council sit with pints of dark ale.\n\n"
            "\"You stood your ground at the stables, comrade,\" one of them says quietly.\n"
            "\"The workers see that you have a head for negotiations and courage under pressure.\"\n"
            "\"The district election is coming up. We want you to stand as our candidate for Shop Steward.\"\n"
            "\"It means responsibility, and it puts a target on your back with the town magistrates. Will you run?\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Accept Nomination (Run for Steward)":
        player["groom_dialogue_state"] = None
        player["steward_nomination_eligible"] = False
        player["running_for_steward"] = True
        player["faction_union"] = min(10, modify_faction(player, "faction_union", 6))
        player["reputation"] += 2
        if "union steward" not in player["skills"]:
            player["skills"].append("union steward")
        log = (
            "You nod firmly and shake hands across the table.\n\n"
            "The delegates raise their mugs. \"To Noburu! May the floor speak through you!\"\n"
            "\"Keep your ear to the ground. We will begin canvassing support across the workshops.\"\n\n"
            "*** You are officially a Union Steward candidate! (+6 Union Faction, +2 Reputation, 'union steward' Skill!) ***"
        )
        return player, log, "MAIN"

    if choice == "Decline Nomination":
        player["groom_dialogue_state"] = None
        player["steward_nomination_eligible"] = False
        log = (
            "You shake your head. \"I prefer to keep a low profile.\"\n\n"
            "The delegates exchange disappointed glances, but the groom pats your arm.\n"
            "\"Fair enough, comrade. Not everyone is cut out for the political frontline. Solidarity all the same.\""
        )
        return player, log, "MAIN"

    return player, "\"Solidarity, comrade. Enjoy your drink.\"", "MAIN"


# -------------------------------------------------------------------------
# HORSE (ROSINANTE)
# -------------------------------------------------------------------------
def get_horse_options(player):
    return ["Pet the horse", "Leave"]

def resolve_horse(choice, player):
    if choice == "Leave":
        return player, "You step away from the horse.", "MAIN"

    if choice == "Pet the horse":
        current_day = (player["total_game_minutes"] // 1000) + 1
        fed_today = (player.get("rosinante_last_fed_day") == current_day)
        
        log = "The horse nuzzles your hand with its nose. It seems friendly."
        if not fed_today:
            log += "\nIt looks hungry."
        else:
            log += "\nIt crunches contentedly on the remnants of its snack."
        return player, log, "MAIN"

    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# STABLE WORKER (FROMABOVE)
# -------------------------------------------------------------------------
def get_fromabove_options(player):
    if player.get("active_stable_task") == "confront_fromabove":
        return ["Confront about the ledger", "Leave"]
    if player.get("active_stable_task") == "investigate_ledger":
        return ["Ask about destroyed ledger", "Leave"]
    return ["Talk", "Leave"]

def resolve_fromabove(choice, player):
    if choice == "Leave":
        return player, "You step away.", "MAIN"
        
    if choice in ["Talk", "Ask about destroyed ledger"]:
        return player, "\"I'm mucking out the stalls. Leave me be, I don't know anything about any ledger.\"", "MAIN"
        
    if choice == "Confront about the ledger":
        player["active_stable_task"] = "report_to_godspeed_4"
        log = (
            "You tell Fromabove that you know the Wallmakers bought his debt to leverage him into destroying the ledger.\n\n"
            "Fromabove drops his pitchfork, looking terrified. \"Keep your voice down!\"\n"
            "\"They bought my father's debts. They told me if I didn't ruin Godspeed's accounts so they could deny their fees, they'd break my legs!\"\n"
            "\"Please, you can't tell the Squire! He'll sack me, and without this wage, the Wallmakers will kill me!\"\n\n"
            "*** You have the truth. Return to Squire Godspeed to make your choice. ***"
        )
        return player, log, "MAIN"
        
    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# TRUTHTALE (UNION BOSS)
# -------------------------------------------------------------------------
def get_truthtale_options(player):
    return ["Talk", "Leave"]

def resolve_truthtale(choice, player):
    if choice == "Leave": return player, "You step away.", "MAIN"
    
    if player.get("active_stable_task") in ["stall_allocation", "who_goes_outside", "setup_grazing_field"]:
        return player, "\"We demand respect! Find us space, or Murum grinds to a halt today!\"", "MAIN"
    return player, "\"Solidarity.\"", "MAIN"

# -------------------------------------------------------------------------
# BREAKCHAINS (FREE-EARTH SYNDICATE / FAI-CNT DELEGATE)
# -------------------------------------------------------------------------
def get_breakchains_options(player):
    if not player.get("anarchist_cell_joined"):
        return ["Present Syndicate Token & Join the Affinity Group", "Leave"]
    return ["Discuss Chapter Two Plans", "Leave"]

def resolve_breakchains(choice, player):
    if choice == "Leave":
        return player, "\"Walk softly, comrade. The Castellan's eyes are everywhere.\"", "MAIN"

    if choice == "Present Syndicate Token & Join the Affinity Group":
        player["anarchist_cell_joined"] = True
        modify_faction(player, "faction_union", 5)
        player["charisma"] += 1
        log = (
            "A circle of hooded workers sits among the hay bales by the light of a single shaded lantern.\n"
            "Shareall nods as you step forward and hold up the Red-and-Black token.\n"
            "Breakchains, a tall woman with calloused hands and fierce eyes, grips your forearm warmly.\n"
            "\"Welcome to the Free-Earth Syndicate, comrade. While Truthtale's moderates beg the Mayor for pennies, we are organizing across the farms, the forests, and Fluvius.\"\n"
            "\"Finish your work here in Murum. Build your strength and allies. When the time comes to leave these walls, the Syndicate will call upon you.\"\n\n"
            "*** NEW PATH UNLOCKED: You are now a sworn member of the Anarcho-Syndicalist Affinity Group! (+5 Union Faction, +1 Charisma) ***"
        )
        return player, log, "MAIN"

    if choice == "Discuss Chapter Two Plans":
        return player, "\"Keep your cover in Murum for now, comrade. Once your business in town is concluded, our couriers on the roads will guide you to the wider struggle.\"", "MAIN"

    return player, "Error.", "MAIN"

# -------------------------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------------------------
HANDLERS = {
    "stable manager": (get_stable_manager_options, resolve_stable_manager),
    "coryllus":       (get_coryllus_options, resolve_coryllus),
    "head hostler":   (get_head_hostler_options, resolve_head_hostler),
    "horse groom":    (get_horse_groom_options, resolve_horse_groom),
    "horse":          (get_horse_options, resolve_horse),
    "fromabove":      (get_fromabove_options, resolve_fromabove),
    "truthtale":      (get_truthtale_options, resolve_truthtale),
    "breakchains":    (get_breakchains_options, resolve_breakchains),
}
