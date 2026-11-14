import random
import game_data as db
import companions_engine
from mechanics import (
    modify_faction, advance_time, handle_sleep_nap, handle_sleep_morning,
    get_time_string, calculate_max_hit, get_eligible_chapter_2_routes,
    can_start_shift, mark_shift_started, mark_shift_completed,
    set_region_territory
)

# -------------------------------------------------------------------------
# DR. MAKEPEACE
# -------------------------------------------------------------------------
def get_makepeace_options(player):
    if player.get("makepeace_state") == "writing_reference":
        return ["Yes please", "No thank you"]

    if player["story_path"] is not None:
        opts = ["Ask for Advice"]
        if player.get("active_companion") not in ("sister_caelia", "sister_hilde"):
            opts.append("Hire Sister Caelia as Field Chirurgeon (15s, 3 Days)")
            if player.get("chapter_2_unlocked"):
                opts.append("Escort Sister Hilde to Fluvius Town (+18s on Arrival)")
        opts.append("Leave")
        return opts

    return ["Get a job in town", "Join the castle defence", "Explore Dtessera Terra", "Ask for Advice", "Leave"]

def resolve_makepeace(choice, player):
    # State 1: Writing the Reference Letter
    if player.get("makepeace_state") == "writing_reference":
        player["makepeace_state"] = None
        player["story_path"] = "Job"
        
        if choice == "Yes please":
            log = "Dr. Makepeace pulls out a fresh piece of parchment and begins to write.\n\n"
            roll = random.randint(1, 6)
            log += f"*** You rolled a {roll}! ***\n\n"
            
            if roll >= 5:
                log += "They write a glowing recommendation detailing your exceptional diligence, smiling as they hand it over, obviously filled with warm affection."
                player["reputation"] += 2 
                db.readables_database["reference letter"]["text"] = "To whom it may concern,\nNoburu is a former student of Escuela Moderna. I can attest to their exceptional diligence and outstanding character.\nI highly recommend them for any endeavor.\nSigned, Dr. Makepeace"
            elif roll in [3, 4]:
                log += "They write a standard, adequate letter confirming your attendance, which betrays their rather neutral feelings toward you despite your best efforts."
                player["reputation"] += 1  
                db.readables_database["reference letter"]["text"] = "To whom it may concern,\nNoburu is a former student of Escuela Moderna. They attended classes and fulfilled the basic requirements of our institution.\nSigned, Dr. Makepeace"
            else:
                log += "They sigh and explain that while you are personally liked you have failed to prove yourself valuable while at school, and hand you a letter that mentions your rather spotty disciplinary and academic record."
                db.readables_database["reference letter"]["text"] = "To whom it may concern,\nNoburu is a former student of Escuela Moderna. While personally liked, I must note their rather spotty disciplinary and academic record.\nSigned, Dr. Makepeace"
                
            player["inventory"].append("reference letter")
            log += "\n\n*** You received a Reference Letter! ***"
            return player, log, "MAIN"
            
        elif choice == "No thank you":
            player["reputation"] += 1
            return player, "\"Very well, Noburu. Let us hope your own merits carry you through.\"", "MAIN"

    # State 2: General Options
    if choice == "Leave":
        return player, "You step away from the desk.", "MAIN"

    if choice == "Hire Sister Caelia as Field Chirurgeon (15s, 3 Days)":
        return companions_engine.hire_temporary_companion(player, "sister_caelia", 15, 3)

    if choice == "Escort Sister Hilde to Fluvius Town (+18s on Arrival)":
        player["active_companion"] = "sister_hilde"
        player["companion_expiry_minute"] = None
        return player, (
            "Sister Hilde shoulders her herbalist's satchel and rowan staff.\n"
            "\"Bless you, Noburu! See me safely down the highway to **Fluvius Town Square**, "
            "and I will tend your wounds along the road and reward you upon arrival!\""
        ), "MAIN"

    if player["story_path"] is not None and choice == "Ask for Advice":
        log = (
            "Dr. Makepeace looks up from their paperwork.\n"
            f"\"Your path is already chosen Noburu. You must proceed with your goal: {player['story_path']}.\"\n"
            "\"Remember, you can always check your status or click Help if you need guidance.\""
        )
        return player, log, "MAIN"

    if choice == "Get a job in town":
        player["makepeace_state"] = "writing_reference"
        log = (
            "\"A sensible choice.\"\n"
            "\"In that case you will want to head to the noticeboards at the Town Hall to see what is on offer.\"\n"
            "\"I will write a reference for you if you would like?\""
        )
        return player, log, "NPC_DIALOGUE"
        
    elif choice == "Join the castle defence":
        player["story_path"] = "Defence"
        log = (
            "\"You will need to gain experience before being able to join the castle defence.\"\n"
            "\"They only recruit the best soldiers in Dtessera Terra.\"\n"
            "\"Build your reputation with the local guard first, but never relinquish your ambition.\""
        )
        return player, log, "MAIN"
        
    elif choice == "Explore Dtessera Terra":
        player["story_path"] = "Explore"
        log = (
            "\"There are many amazing creatures and adventures to be met across Dtessera Terra.\"\n"
            "\"I admire anyone brave and curious enough to embrace the challenges by exploring our world.\"\n"
            "\"However, you must go prepared. The dangers are too much for any person without doing so.\"\n"
            "\"Tread carefully, Noburu.\""
        )
        return player, log, "MAIN"
        
    elif choice == "Ask for Advice":
        log = (
            "Dr. Makepeace adjusts their spectacles and smiles gently.\n"
            "\"The world is vast, Noburu, and it is easy to become overwhelmed.\"\n"
            "\"Click the '?' Help button at any time to review the survival rules or save your progress.\"\n"
            "\"And keep a close eye on your condition! Use the Status and Inventory buttons to monitor your health, hunger, carry weight, and reputation.\"\n"
            "\"Knowledge is your greatest tool out there.\""
        )
        return player, log, "MAIN"

    return player, "Conversation ended.", "MAIN"


# -------------------------------------------------------------------------
# FAIRLIGHT (THE ACTOR)
# -------------------------------------------------------------------------
def get_fairlight_options(player):
    if player["active_mayor_task"] == "playhouse_meet":
        return [
            "Bribe for silence",
            "Deny everything",
            "Threaten him",
            "Permanently silence him",
            "Leak scandal to Union (+Union)",
            "Hand journalist's notes to Watch (+Guard)"
        ]
    options = ["Buy Ticket (5s)", "Interact"]
    if player.get("active_market_task") == "find_master_key":
        options.append("Ask about Godwin's Key")
    options.append("Leave")
    return options

def resolve_fairlight(choice, player):
    if choice == "Leave":
        return player, "\"A tragic choice!\"", "MAIN"

    if choice == "Ask about Godwin's Key":
        log = (
            "Fairlight places a hand over his heart dramatically.\n"
            "\"Ah, the Market Manager! He was here twenty minutes ago, waving his arms and ranting about my glorious playbills!\"\n"
            "\"I distinctly heard that heavy iron key jangling on his belt as he stormed off toward the Town Gate to pester the guards.\""
        )
        return player, log, "MAIN"
    
    # State 1: The Journalist Encounter (Shift 4 House Staff)
    if player["active_mayor_task"] == "playhouse_meet":
        log = ""
        if choice == "Bribe for silence":
            cost = random.randint(15, 40)
            log = f"The journalist smirks. \"It'll cost you {cost} silver.\"\n\n"
            if player["silver"] >= cost:
                player["silver"] -= cost
                player["reputation"] += 2
                player["influence"] = player.get("influence", 0) + 1
                log += f"You pay him the {cost} silver. He tips his hat and walks away.\n*** (+2 Reputation, +1 Influence) ***\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
            else:
                log += f"\"You only have {player['silver']} silver? That won't buy my silence!\"\nHe runs off to the printing press! (-3 Reputation, -3 Wallmakers Faction)\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["reputation"] -= 3
                modify_faction(player, "faction_wallmakers", -3)
            player["active_mayor_task"] = "report_playhouse"
            return player, log, "MAIN"
            
        elif choice == "Deny everything":
            log = "You flatly deny that anyone is in the box.\n\n"
            if random.choice([True, False]):
                log += "The journalist squints, shrugs, and walks away. \"Must have been seeing things.\"\n*** (+1 Influence) ***\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["influence"] = player.get("influence", 0) + 1
            else:
                log += "\"Do you think I'm an idiot? I know what I saw!\"\nHe storms off to publish the story! (-3 Reputation, -3 Wallmakers Faction)\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["reputation"] -= 3
                modify_faction(player, "faction_wallmakers", -3)
            player["active_mayor_task"] = "report_playhouse"
            return player, log, "MAIN"
            
        elif choice == "Threaten him":
            roll = random.randint(1, 3)
            if roll == 1:
                dmg = random.randint(2, 6)
                player["health"] -= dmg
                log = f"You grab his collar, but he pulls a small knife! A scuffle breaks out!\nHe slashes you across the arm (-{dmg} Health) and flees into the street!\nThe story hits the papers! (-3 Reputation, -3 Wallmakers Faction)\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["reputation"] -= 3
                modify_faction(player, "faction_wallmakers", -3)
            elif roll == 2:
                log = "You loom over him, threatening his life. He goes pale and drops his notepad.\n\"Alright, alright! I saw nothing!\" He runs away.\n*** Threat successful! (+1 Influence, +1 Wallmakers Faction) ***\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["influence"] = player.get("influence", 0) + 1
                modify_faction(player, "faction_wallmakers", 1)
            else:
                log = "You threaten him, but he laughs in your face and runs out the door to his publisher!\nThe scandal is printed! (-3 Reputation, -3 Wallmakers Faction)\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["reputation"] -= 3
                modify_faction(player, "faction_wallmakers", -3)
            player["active_mayor_task"] = "report_playhouse"
            return player, log, "MAIN"
            
        elif choice == "Permanently silence him":
            log = "You lure him into a dark alley beside the Playhouse...\n\n"
            if random.randint(1, 3) in [1, 2]:
                log += "You cleanly snap his neck and hide the body in a crate.\n*** The journalist is silenced! (+5 Wallmakers, +1 Stealth, -2 Reputation for murder rumors) ***\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                modify_faction(player, "faction_wallmakers", 5)
                player["stealth"] += 1
                player["reputation"] -= 2
            else:
                log += "As you strike, a passing guard spots you! The journalist screams and escapes!\n\"MURDERER!\" the guard yells. You are forced to flee the scene!\n*** Botched assassination! (-5 Reputation, -5 Wallmakers Faction) ***\n\nThe meeting finishes. The Wallmaker slips away. It is time to report back to Praisegod."
                player["reputation"] -= 5
                modify_faction(player, "faction_wallmakers", -5)
            player["active_mayor_task"] = "report_playhouse"
            return player, log, "MAIN"

        elif choice == "Leak scandal to Union (+Union)":
            modify_faction(player, "faction_union", 4)
            modify_faction(player, "faction_wallmakers", -2)
            player["charisma"] += 1
            player["active_mayor_task"] = "report_playhouse"
            log = (
                "You quietly steer the journalist away from the Mayor's box and instead slip him copies of the Wallmakers' wage-skimming contracts.\n"
                "\"Even better!\" the journalist grins, rushing off to print a pro-Union exposé!\n"
                "*** (+4 Union Faction, +1 Charisma, -2 Wallmakers Faction) ***\n\n"
                "The meeting finishes. It is time to report back to Praisegod."
            )
            return player, log, "MAIN"

        elif choice == "Hand journalist's notes to Watch (+Guard)":
            modify_faction(player, "faction_guard", 4)
            modify_faction(player, "faction_wallmakers", -2)
            player["reputation"] += 1
            player["active_mayor_task"] = "report_playhouse"
            log = (
                "You confiscate the journalist's notebook detailing the Wallmakers' secret meeting and pass the pages to a grateful Watch patrol outside while keeping the Mayor's name out of it!\n"
                "*** (+4 Guard Faction, +1 Reputation, -2 Wallmakers Faction) ***\n\n"
                "The meeting finishes. It is time to report back to Praisegod."
            )
            return player, log, "MAIN"

    # State 2: Standard Ticket Sales
    if choice == "Buy Ticket (5s)":
        if "playhouse ticket" in player["inventory"]:
            return player, "Fairlight laughs dramatically. \"You already hold the golden key to tonight's revelries, my friend!\"", "MAIN"
        elif player["silver"] >= 5:
            player["silver"] -= 5
            player["inventory"].append("playhouse ticket")
            return player, "You hand over the silver. Fairlight bows deeply and produces a finely printed ticket.", "MAIN"
        else:
            log = f"Fairlight sighs tragically. \"Alas, art requires patronage. You only have {player['silver']} silver.\""
            if "poster" not in player["inventory"]:
                log += "\n\"But fear not! Here, take a promotional poster!\""
                player["inventory"].append("poster")
            return player, log, "MAIN"

    if choice == "Interact":
        if player["reputation"] < 1 and "poster" not in player["inventory"]:
            log = (
                "\"A person such as yourself may find opportunity off the beaten track.\"\n"
                "\"Fear not! Here, take a promotional poster!\""
            )
            player["inventory"].append("poster")
        else:
            log = "Fairlight strikes a theatrical pose. \"All the world's a stage, my friend—and Murum is its grandest tragedy!\""
        return player, log, "MAIN"
            
    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# MAYOR'S BUTLER (FEARNOT)
# -------------------------------------------------------------------------
def get_butler_options(player):
    if player["current_job"] == "mayor's house":
        return ["Report for shift", "Leave"]
    return ["Apply for job", "Leave"]

def resolve_butler(choice, player):
    if choice == "Leave":
        return player, "\"Mind you do not drag mud across the threshold on your way out.\"", "MAIN"
        
    if player["current_job"] == "mayor's house":
        log = (
            "\"Impertinent wretch!\" the Butler hisses, glancing around as if scandalised.\n"
            "\"You are a servant of this household, yet you presume to present yourself in the grand foyer?!\"\n"
            "\"This entrance is reserved strictly for Their Worship and esteemed dignitaries.\"\n"
            "\"Take yourself around the back to the Staff Entrance immediately!\""
        )
    else:
        log = (
            "\"The utter insolence!\" the Butler scoffs, turning up their nose.\n"
            "\"You dare present your grimy self at the front doors of the Mayor's residence seeking domestic labour?!\"\n"
            "\"Common folk do not soil the foyer rugs. Go around back to the Staff Entrance.\"\n"
            "\"Praisegod deals with the help. Now out before I summon the watch!\""
        )
        
    return player, log, "MAIN"


# -------------------------------------------------------------------------
# MAYOR'S HOUSE MANAGER (PRAISEGOD)
# -------------------------------------------------------------------------
def get_mayors_house_manager_options(player):
    if player.get("mayor_staff_state") == "shift_6_prompt":
        return ["Proceed with shift", "Hand in notice with immediate effect"]
    if player["current_job"] == "mayor's house":
        if player["active_mayor_task"] is None:
            opts = [f"Start Shift ({player['mayors_house_shifts']} Completed)"]
            if player["mayors_house_shifts"] >= 6:
                opts.append("Hand in notice with immediate effect")
            opts.append("Leave")
            return opts
        else:
            return ["Return from Task", "Leave"]
    return ["Apply for Job", "Leave"]

def resolve_mayors_house_manager(choice, player):
    if choice == "Leave":
        return player, "You step away.", "MAIN"

    if choice == "Hand in notice with immediate effect":
        player["mayor_staff_state"] = None
        player["current_job"] = None
        player["current_tenure"] = 0
        player["active_mayor_task"] = None
        player["chapter_2_unlocked"] = True
        log = (
            "Praisegod adjusts their spectacles and gives a crisp, respectful bow.\n"
            "\"You have served Their Worship's household with distinction, Footman. I accept your notice with immediate effect.\"\n"
            "\"Take a look at the Noticeboard in the Town Hall—with your influence and references, doors across Dtessera Terra will be open to you.\"\n\n"
            "*** You have handed in your notice! Visit the Noticeboard in the Town Hall to explore new opportunities! ***"
        )
        return player, log, "MAIN"

    if choice == "Proceed with shift":
        player["mayor_staff_state"] = None
        player["mayor_shift_6_prompted"] = True
        choice = f"Start Shift ({player['mayors_house_shifts']} Completed)"
        
    # --- HIRING ---
    if choice == "Apply for Job":
        if player["current_job"] is not None and player["current_job"] != "mayor's house":
            return player, "Praisegod sneers. \"The Mayor requires exclusive service.\"", "MAIN"
            
        if "reference letter" not in player["inventory"]:
            return player, "\"Return when you have a formal letter of reference.\"", "MAIN"
            
        if player["reputation"] < 2:
            return player, f"\"Your standing in Murum is still too low. (Requires 2 Reputation, you have {player['reputation']})\"", "MAIN"
            
        player["current_job"] = "mayor's house"
        player["current_tenure"] = 0
        return player, "Praisegod reviews Dr. Makepeace's letter. \"Hmm. I suppose you will do. You are officially on the Mayor's staff.\"", "MAIN"

    # --- STARTING A SHIFT ---
    if choice.startswith("Start Shift"):
        ok, msg = can_start_shift(player)
        if not ok:
            return player, msg, "MAIN"
        player = mark_shift_started(player)
            
        player["mayor_task_deadline"] = player["total_game_minutes"] + 600
        shifts = player["mayors_house_shifts"]

        # --- SHIFT 6 EVALUATION: NOTICEBOARD OR DISMISSAL (GAME OVER) ---
        if shifts == 5 and not player.get("mayor_shift_6_prompted"):
            eligible = get_eligible_chapter_2_routes(player)
            if not eligible:
                player["current_job"] = None
                player["current_tenure"] = 0
                log = (
                    "Praisegod looks over your service record and sighs coldly.\n"
                    "\"I am afraid that you have failed to reach the level that we expect of a member of the Mayor's house staff in the time that you have been here. "
                    "We are going to have to let you go. I cannot see you acquiring any further work in Murum. "
                    "You will have to try your luck on the road. I wish you luck.\"\n\n"
                    "*** GAME OVER: You failed to qualify for any Chapter 2 path and have been dismissed from Murum! ***"
                )
                return player, log, "DEAD"

            player["mayor_staff_state"] = "shift_6_prompt"
            player["chapter_2_unlocked"] = True
            log = (
                "Praisegod pauses before handing you the day's duty roster.\n"
                "\"A moment, Footman. Now that you have risen to the top of the household staff and built real political influence, "
                "there may be new opportunities waiting for you if you look at the Noticeboard in the Town Hall.\"\n"
                "\"Would you like to proceed with your shift today, or hand in your notice with immediate effect?\""
            )
            return player, log, "NPC_DIALOGUE"
        
        if shifts == 0:
            log = (
                "\"Take these outgoing letters. Go to the Post Office, deposit them, and collect the incoming mail.\"\n"
                "*** SHIFT STARTED! You have 600 minutes to complete the task! ***"
            )
            player["inventory"].append("mayor's outgoing letters")
            player["active_mayor_task"] = "post_office"
        elif shifts == 1:
            log = (
                "\"The cook is baking a cake for the Mayor's birthday but we are out of butter.\"\n"
                "\"Take this 15 silver. Go to the Dairy Stall at the Food Market, buy Butter, and return immediately.\"\n"
                "*** SHIFT STARTED! You have 600 minutes to complete the tasks! ***"
            )
            player["silver"] += 15
            player["active_mayor_task"] = "buy_butter"
        elif shifts == 2:
            log = (
                "\"The Mayor's stallion requires new shoes.\"\n"
                "\"Collect the horse from the Stables and take it to the Blacksmith.\"\n"
                "\"The Mayor has paid for you to take a riding lesson while you wait.\"\n"
                "\"Afterward, water the horse at the Market fountain, graze it in the open field south east of the Escuela Moderna, and return it to the stables.\"\n"
                "*** SHIFT STARTED! You have 600 minutes to complete the tasks! ***"
            )
            player["active_mayor_task"] = "collect_horse"
        elif shifts == 3:
            log = (
                "\"The Mayor requires a delicate meeting. Not someone they like to do business with, but needs must.\"\n"
                "\"Take the Mayor's seal. Go to the Tavern and make contact with Hopestill.\"\n"
                "\"Use him to arrange a meeting with the Wallmakers.\"\n"
                "*** SHIFT STARTED! You have 600 minutes to complete the tasks! ***"
            )
            player["inventory"].append("mayor's seal")
            player["active_mayor_task"] = "find_hopestill"
        elif shifts == 4:
            log = (
                "\"I have heard troubling reports of disquiet amongst the unionised workforce.\"\n"
                "\"Go to Union House. Learn what they are planning and report back.\"\n"
                "*** SHIFT STARTED! You have 600 minutes to investigate! ***"
            )
            player["active_mayor_task"] = "investigate_union"
        else:
            log = (
                "\"Just standard duties today. Go polish the silver.\"\n"
                "*** SHIFT STARTED! You are working around the house for 6 hours. ***"
            )
            player["active_mayor_task"] = "standard_shift"
            
        return player, log, "MAIN"

    # --- RETURNING FROM A TASK ---
    if choice == "Return from Task":
        success = False
        log = ""
        task = player["active_mayor_task"]
        
        if task == "deliver_dinner_letter":
            if "mayor's dinner letter" in player["inventory"]:
                log = "Praisegod takes the letter. \"Excellent. I shall inform the kitchen immediately.\"\n\"Go polish the silver for the remainder of your shift.\""
                player["inventory"].remove("mayor's dinner letter")
                success = True
            else:
                log = "\"Why are you back here? Do you have the Mayor's dinner instructions? The clock is ticking!\""
                
        elif task == "buy_butter":
            if "butter" in player["inventory"]:
                player["inventory"].remove("butter")
                change_taken = 5 if player.get("stealth", 0) >= 1 else 10
                player["silver"] = max(0, player["silver"] - change_taken)
                skim_msg = " (You smoothly pocket 5 silver of the change!)" if change_taken == 5 else " Praisegod counts the 10 silver change back into their purse."

                log = (
                    f"\"Finally. I will take this to the kitchens.\" Praisegod snatches the butter.{skim_msg}\n"
                    "\"Now, the maid has fallen ill. Take this 20 silver. Go to the Apothecary and buy Flu Medicine.\""
                )
                player["silver"] += 20
                player["active_mayor_task"] = "buy_medicine"
            else:
                log = "\"Where is the butter? The cook is waiting!\""
                
        elif task == "buy_medicine":
            if "flu medicine" in player["inventory"]:
                player["inventory"].remove("flu medicine")
                change_taken = 5 if player.get("stealth", 0) >= 1 else 10
                player["silver"] = max(0, player["silver"] - change_taken)
                skim_msg = " (You deftly pocket 5 silver of the change!)" if change_taken == 5 else " Praisegod takes back the 10 silver change."

                log = (
                    f"\"Give that here. I'll see she takes it.\"{skim_msg}\n"
                    "\"The cake is now ready. The Mayor is having a birthday lunch with Goodcheer at the Dog and Duck Pub.\"\n"
                    "\"Take this cake to them at once!\""
                )
                player["inventory"].append("mayor's birthday cake")
                player["active_mayor_task"] = "deliver_cake"
                db.npc_database["mayor"]["location"] = "dog and duck pub"
            else:
                log = "\"Do you have the Flu Medicine? The maid is shivering!\""
                
        elif task == "report_to_praisegod":
            log = (
                "\"You delivered it? Good. The Mayor is pleased.\"\n"
                "\"However, this damp Brumaire chill has seeped into the estate and the cellar coal is nearly spent. Go to the Blacksmith and fetch a Sack of Coal.\"\n"
                "\"Tell Lovejoy to put it on the Mayor's tab.\""
            )
            player["active_mayor_task"] = "get_coal"
            
        elif task == "return_with_coal":
            if "sack of coal" in player["inventory"]:
                log = "\"Put that in the cellar. Excellent work today, you have earned your wage.\""
                player["inventory"].remove("sack of coal")
                success = True
            else:
                log = "\"Where is the coal? I am freezing!\""
                
        elif task == "report_to_praisegod_3":
            log = "\"The horse is safely returned? Good. Go polish the silver for the remainder of your shift.\""
            success = True
            
        elif task == "report_playhouse":
            log = "\"The meeting concluded successfully? Good. The Mayor is pleased.\"\n\"Go polish the silver for the remainder of your shift.\""
            if "mayor's seal" in player["inventory"]: player["inventory"].remove("mayor's seal")
            success = True
            
        elif task == "investigate_union":
            log = "\"You learned nothing from the official house? Then go dig deeper!\"\n\"Go to the Pub. Buy a drink. Listen to the rabble!\""
            
        elif task == "report_pub":
            log = (
                "\"Truthtale? I should have known they were behind this rabble-rousing.\"\n"
                "\"Take the Mayor's seal. Go back to Union House and arrange an official meeting.\"\n"
                "\"The Mayor and I will be touring the Market. Find us there once the meeting is set.\""
            )
            player["inventory"].append("mayor's seal")
            player["active_mayor_task"] = "arrange_meeting"
            
        elif task == "finish_shift_5":
            log = "\"A grueling day. The Mayor is resting. Take your pay.\""
            if "mayor's seal" in player["inventory"]: player["inventory"].remove("mayor's seal")
            success = True
            
        elif task == "standard_shift":
            log = "Praisegod inspects the silver and nods. \"Acceptable work today.\""
            success = True
            
        elif task == "post_office":
            log = "\"Why have you returned empty handed? Get to the Post Office!\""
        else:
            log = "\"You have not completed your task!\""

        # Shift Completion Payout
        if success:
            shift_start_time = player["mayor_task_deadline"] - 600
            time_spent = player["total_game_minutes"] - shift_start_time
            if time_spent < 600:
                player, _ = advance_time(600 - time_spent, player)

            shift_pay = 50 if player["mayors_house_shifts"] >= 5 else 30
            player["silver"] += shift_pay
            player["influence"] = player.get("influence", 0) + 1
            player = mark_shift_completed(player)
            player["mayors_house_shifts"] += 1
            player["current_tenure"] += 1
            player["active_mayor_task"] = None
            player["mayor_task_deadline"] = 0
            player["hunger"] = 100
            player["thirst"] = 100
            player["last_sustenance_tick"] = player["total_game_minutes"]
            db.npc_database["mayor"]["location"] = None

            log += f"\n\n*** Shift Completed! You earned {shift_pay} silver, +1 Influence (Total: {player['influence']}), and ate from the kitchen! (Total Silver: {player['silver']}) ***"

            if player["reputation"] > 0 and player["mayors_house_shifts"] == 5:
                for sk in ["mayor's footman", "safe travel"]:
                    if sk not in player["skills"]:
                        player["skills"].append(sk)
                player["reputation"] += 2
                log += "\n*** You are now the Mayor's Footman! (+2 Reputation, 'mayor's footman' & 'safe travel' skills) ***"
                
        return player, log, "MAIN"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# LANDLORD FAIRWEATHER (DOG AND DUCK PUB)
# -------------------------------------------------------------------------
def get_landlord_options(player):
    state = player.get("landlord_state")
    if state == "food": return ["Hot Stew (3s)", "Murky Ale (1s)", "Back"]
    if state == "union_join": return ["Join Union (2s)", "Refuse"]
    if state == "spy": return ["Side with management", "Remain neutral", "Side with workers"]
    
    options = ["Rent Room (2s)"]
    if player["union_status"] == "invited": options.append("Ask about the Union")
    elif player["union_status"] == "joined": options.append("Check in with Union")
    options.append("Order Sustenance")
    options.append("Leave")
    return options

def resolve_landlord(choice, player):
    state = player.get("landlord_state")
    
    if choice == "Leave": return player, "\"Mind how you go.\"", "MAIN"
    if choice == "Back":
        player["landlord_state"] = None
        return player, "You step back from the bar.", "NPC_DIALOGUE"

    if choice == "Rent Room (2s)":
        if not player["free_room_used"] and (player["market_sweeper_shifts"] > 0 or player["blacksmith_shifts_completed"] > 0 or player["stable_shifts"] > 0):
            player["free_room_used"] = True
            player, log_sleep = handle_sleep_morning(player)
            player["hunger"] = player["thirst"] = 100
            return player, "You mention who sent you.\n\"Ah, fair enough. Any friend of theirs is welcome here. First night is on the house!\"\n\n" + log_sleep + "\n\n*** Time passes while you rest... ***\n*** You wake up to a hearty breakfast! (Hunger/Thirst restored) ***", "MAIN"
        elif player["silver"] >= 2:
            player["silver"] -= 2
            player, log_sleep = handle_sleep_morning(player)
            player["hunger"] = player["thirst"] = 100
            return player, "You hand over 2 silver. The Landlord hands you a key and points to the stairs.\n\n" + log_sleep + "\n\n*** Time passes while you rest... ***\n*** You wake up to a hearty breakfast! (Hunger/Thirst restored) ***", "MAIN"
        return player, f"\"Rooms are 2 silver. You only have {player['silver']}. You can sleep in the dirt outside.\"", "MAIN"

    # --- UNION LOGIC ---
    if choice == "Ask about the Union":
        player["landlord_state"] = "union_join"
        log = (
            "The Landlord stops polishing and leans in close.\n"
            "\"The Workers Union, eh? It's 2 silver for your union card. It means you stand with your fellow workers.\"\n"
            "\"You won't get any fancy management promotions, but we protect our own. Are you in?\""
        )
        return player, log, "NPC_DIALOGUE"
        
    if choice == "Join Union (2s)":
        if player["silver"] >= 2:
            player["silver"] -= 2
            player["union_status"] = "joined"
            modify_faction(player, "faction_union", 5)
            player["landlord_state"] = None
            log = f"You slide 2 silver across the bar. The Landlord slips you a small, stamped card.\n*** You joined the Union! (+5 Union Faction, Total: {player['faction_union']}) ***"
            return player, log, "MAIN"
        return player, "\"You don't even have 2 silver! Come back when you can pay your dues.\"", "NPC_DIALOGUE"
        
    if choice == "Refuse":
        player["landlord_state"] = None
        return player, "\"Suit yourself. Don't come crying to us when the bosses squeeze you dry.\"", "MAIN"
        
    if choice == "Check in with Union":
        return player, "\"Welcome back, comrade. Keep your ear to the ground. We might have work for you soon.\"", "MAIN"

    # --- FOOD & SPYING ---
    if choice == "Order Sustenance":
        player["landlord_state"] = "food"
        return player, "\"What'll it be?\"", "NPC_DIALOGUE"

    if choice == "Hot Stew (3s)":
        if player["silver"] >= 3:
            player["silver"] -= 3
            player["hunger"] = 100
            player["last_sustenance_tick"] = player["total_game_minutes"]
            return player, "You buy a hearty stew and scarf it down.\n*** Your hunger is fully satisfied! ***", "NPC_DIALOGUE"
        return player, "\"You don't have enough coin for food.\"", "NPC_DIALOGUE"

    if choice == "Murky Ale (1s)":
        if player["silver"] >= 1:
            player["silver"] -= 1
            player["thirst"] = 100
            player["last_sustenance_tick"] = player["total_game_minutes"]
            log = "You buy a pint of murky ale and drink it down.\n*** Your thirst is fully satisfied! ***"
            
            # --- SHIFT 4: INEBRIATION CLUE ---
            if player.get("active_stable_task") == "investigate_ledger":
                player["beers_drank"] += 1
                if player["beers_drank"] == 1:
                    log += "\n\nMuchmerceye, the horse groom nearby, ignores you, sipping his ale quietly."
                elif player["beers_drank"] == 2:
                    log += "\n\nMuchmerceye looks a bit woozy. \"You drink a lot, don't you?\""
                elif player["beers_drank"] >= 3:
                    player["active_stable_task"] = "confront_fromabove"
                    log += (
                        "\n\nAs you finish your third ale, Muchmerceye leans over, heavily slurring.\n"
                        "\"Thass a shame 'bout the ledger... but Fromabove had no choice...\"\n"
                        "\"Wallmakers bought his debt... they use it as leverage. Make us do what they want...\"\n\n"
                        "*** CLUE UNCOVERED: Fromabove destroyed the ledger! Confront him at the stables! ***"
                    )
            
            # THE MAYOR'S SPY INTERCEPT
            elif player["active_mayor_task"] == "investigate_union":
                player["landlord_state"] = "spy"
                log += (
                    "\n\nYou sit in a dark corner with your ale and listen to a nearby table.\n"
                    "\"Truthtale says that it is unfair for us to be struggling so!\" one worker whispers.\n"
                    "\"They are right,\" another replies. \"How can some have so much and others so little?\"\n"
                    "\"Truthtale says we can demand more and they'll have to give it to us. The wealthy need us!\"\n\n"
                    "You slide your chair closer and try to join the conversation.\n"
                    "They glare at you. \"You are not union. We're not talking to you.\""
                )
                return player, log, "NPC_DIALOGUE"
                
            return player, log, "NPC_DIALOGUE"
        return player, "\"You don't have enough coin for a drink.\"", "NPC_DIALOGUE"

    if state == "spy":
        if choice in ["Side with management", "Disagree with them", "Remain neutral", "Enquire further", "Side with workers", "Sympathise"]:
            player["landlord_state"] = None
            player["active_mayor_task"] = "report_pub"
            if choice in ["Side with management", "Disagree with them"]:
                player["faction_union"] = max(-10, modify_faction(player, "faction_union", -1))
                player["influence"] = player.get("influence", 0) + 1
                log = "You tell them they should be grateful for their wages. They curse at you and leave.\n*** You angered the workers! (+1 Influence, -1 Union Faction) ***\n*** Report back to Praisegod! ***"
            elif choice in ["Side with workers", "Sympathise"]:
                player["faction_union"] = min(10, modify_faction(player, "faction_union", 3))
                player["charisma"] = player.get("charisma", 0) + 1
                log = "You tell them you understand their struggle. They nod appreciatively before departing.\n*** You built solidarity! (+1 Charisma, +3 Union Faction) ***\n*** Report back to Praisegod! ***"
            else:
                log = "You ask for more details, but they clam up and leave the pub.\n*** You have enough information! Report back to Praisegod! ***"
            return player, log, "MAIN"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# GUARDS (AELFGIFU & SIGEBERHT) & SNAIL ENVOY
# -------------------------------------------------------------------------
def get_guard_options(player):
    if player["reputation"] < 0:
        return ["Leave"]
    options = ["What lies beyond the gates?", "Is it dangerous?"]
    if player.get("active_market_task") in ["find_master_key", "search_fountain_key"]:
        options.append("Ask about Godwin's Key")
    options.append("Leave")
    return options

def resolve_sigeberht(choice, player):
    if player["reputation"] < 0:
        return player, "\"I know your face. You've been causing trouble in Murum. Keep moving before I drag you to the dungeons myself.\"", "MAIN"

    if choice == "Ask about Godwin's Key":
        player["active_market_task"] = "search_fountain_key"
        log = (
            "Sigeberht nods toward the town square.\n"
            "\"Godwin? Aye, he was here bending my ear about pickpockets. Looked exhausted and red in the face.\"\n"
            "\"When he walked back into the Market, I watched him lean right over the Water Fountain to splash cold water on his face. Heard a loud clink right before he dried off.\"\n\n"
            "*** CLUE UNCOVERED: Go to the Market and use 'Action -> Gather / Search' to check the fountain! ***"
        )
        return player, log, "MAIN"
        
    if choice == "What lies beyond the gates?":
        log = (
            "\"The New Road stretches north across the Ragmore Plains,\" Sigeberht says, gesturing out the gate.\n\""
            "If you follow the road far enough, you'll eventually reach Parvus Town on the coast. But it's a long journey.\"\n"
            "\"To the east lies the Lignum Forest. Don't go wandering in there without a working compass — the canopy blocks out the sun and spins your head right round!\""
        )
        return player, log, "MAIN"
    
    if choice == "Is it dangerous?":
        log = ("Sigeberht chuckles grimly. \"Dangerous? The wilderness is crawling with cutthroats, starved beasts, and worse.\"\n"
               "\"Highway Robbers stalk the New Road. They'll ambush you if you're traveling on foot."
               "And if you step off into the deep woods without knowing what you're doing, you won't come back.\"\n"
               "\"Make sure you have a good weapon, a sturdy tent, and a horse if you can afford one.\""
            )
        return player, log, "MAIN"
        
    return player, "\"A wise choice. The walls of Murum are the only truly safe place in Dtessera Terra.\"", "MAIN"

def resolve_aelfgifu(choice, player):
    if player["reputation"] < 0:
        return player, "\"Stay back. I have no patience for troublemakers today.\"", "MAIN"
        
    if choice == "What lies beyond the gates?":
        log = ("Aelfgifu looks at you with profound confusion. \"Are you feeling quite alright? You grew up here!\"\n"
               "\"Dtessera Terra is the world we live in. We are currently in the walled town of Murum. "
               "Far to the north is Parvus, and to the east is Fluvius.\"\n"
               "\"There are castles, lakes, forests... did you hit your head on a cobblestone?\""
            )
        return player, log, "MAIN"
    
    if choice == "Is it dangerous?":
        log = ("\"Since you seem to have forgotten the basics...\" Aelfgifu sighs.\n"
               "\"Pay attention to the time. It is a 1,000-minute decimal day, and a 10-day week. "
               "Most buildings lock their doors at 7:50, so don't get caught outside without a tent.\"\n"
               "\"And keep an eye on your hunger and thirst! The longer you walk, the more it drains. "
               "You will start dying of exhaustion or starvation if you don't eat, drink at the fountain, and sleep regularly.\""
            )
        return player, log, "MAIN"
        
    return player, "\"Keep your wits about you.\"", "MAIN"

def get_snail_envoy_options(player):
    opts = ["Ask about the Giant Hairy Armadillo", "Ask about the roads beyond Murum"]
    if "cobnuts" in player["inventory"]:
        opts.append("Feed cobnuts to the Giant Hairy Armadillo")
    opts.append("Leave")
    return opts

def resolve_snail_envoy(choice, player):
    if choice == "Leave":
        return player, "The giant hairy armadillo snuffles the cobblestones as you step back.", "MAIN"

    if choice == "Ask about the Giant Hairy Armadillo":
        log = (
            "Perched high in a lacquered brass saddle-cup, the Snail Envoy extends two ocular stalks toward you.\n"
            "\"A horse is swift on paved stone,\" the Snail rasps in a slow, resonant hum, \"but out on the Ragmore Plains "
            "and the roots of Lignum Forest, nothing matches a Giant Hairy Armadillo. Thick keratin plates against bandit arrows, "
            "claws that dig through rock, and a steady gait that never spills a drop of slime.\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Ask about the roads beyond Murum":
        log = (
            "\"The factions of Murum think their squabbles end at the Town Wall,\" Envoy Gastropoda muses.\n"
            "\"Out on the New Road and the Old Path, territories shift by the week. Never step off the road into a rival faction's "
            "turf without their mark—or a mount armoured like mine.\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Feed cobnuts to the Giant Hairy Armadillo":
        player["inventory"].remove("cobnuts")
        player["equusense"] = player.get("equusense", 0) + 1
        player["reputation"] += 1
        log = (
            "You offer the cobnuts. The giant hairy armadillo uncurls its long, sticky tongue, scoops them from your palm, "
            "and lets out a low, rumbling purr that vibrates through your boots!\n"
            "Envoy Gastropoda bows their shell in gratitude.\n"
            "*** (+1 Equusense, +1 Reputation) ***"
        )
        return player, log, "MAIN"

    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# CAPTAIN WEALDHERE
# -------------------------------------------------------------------------
def get_wealdhere_options(player):
    if player.get("wealdhere_state") == "contraband_interrogation":
        return [
            "Explain calmly that you found it while sweeping",
            "Denounce the anarchists passionately",
            "Stammer nervously"
        ]

    if player["reputation"] < 0:
        return ["Leave"]
    
    options = []
    if player["current_job"] == "wall surveyor" and player.get("surveyor_report") == "failed_break_in" and not player.get("reported_shift_1_to_guard"):
        options.append("Report Wallmaker Intel (Undercover)")
    elif player["current_job"] == "wall surveyor" and player.get("surveyor_report") == "breach_rigged" and not player.get("reported_shift_2_to_guard"):
        options.append("Report Breach Blueprint (Undercover)")
    elif player["current_job"] == "wall surveyor" and player.get("surveyor_report") == "damage_ledger" and not player.get("reported_shift_3_to_guard"):
        options.append("Report True Damage Ledger (Undercover)")
    elif player["current_job"] == "wall surveyor" and player.get("surveyor_report") == "parapet_cache" and not player.get("reported_shift_4_to_guard"):
        options.append("Let Wealdhere Mark Contraband (Undercover)")
    if player.get("active_market_task") == "hand_contraband_to_guard" and "bundle of radical pamphlets" in player["inventory"]:
        options.append("Hand in Radical Pamphlets")
    if "mayor's incoming post" in player["inventory"] and not player.get("mayor_post_leaked_guard"):
        options.append("Show Mayor's Customs Dispatch (+Guard)")
    if "bundle of halberds" in player["inventory"]:
        options.append("Deliver Halberds")
        
    options.append("Interact")
    options.append("Leave")
    return options

def resolve_wealdhere(choice, player):
    if choice == "Show Mayor's Customs Dispatch (+Guard)":
        player["mayor_post_leaked_guard"] = True
        modify_faction(player, "faction_guard", 3)
        player["influence"] = player.get("influence", 0) + 1
        log = (
            "Before handing the incoming dispatches to the Mayor, you let Captain Wealdhere discreetly inspect the customs seals.\n"
            "Wealdhere nods grimly. \"Good eye, Footman. The Watch remembers its friends inside the manor.\"\n"
            "*** (+3 Guard Faction, +1 Influence) ***"
        )
        return player, log, "MAIN"

    # --- SHIFT 3: WEALDHERE'S INTERROGATION ---
    if player.get("wealdhere_state") == "contraband_interrogation":
        player["wealdhere_state"] = None
        player["active_market_task"] = "report_market_shift_3"
        
        if choice in ["Explain calmly that you found it while sweeping", "Denounce the anarchists passionately"]:
            if player["charisma"] >= 2 or player["reputation"] >= 3:
                modify_faction(player, "faction_guard", 1)
                modify_faction(player, "faction_union", -2)
                log = (
                    "Wealdhere stares into your eyes for a long, tense moment, then tosses the pamphlets into the brazier.\n"
                    "\"Hmph. You have a clean record, citizen. Good work bringing this sedition to my attention.\"\n"
                    "\"Tell Godwin I'll have extra patrols watching the market stalls.\"\n\n"
                    "*** Interrogation Passed! (+1 Guard Faction, -2 Union Faction) ***\n"
                    "*** Return to Godwin at the Market to finish your shift! ***"
                )
                return player, log, "MAIN"
                
        player["reputation"] -= 2
        modify_faction(player, "faction_guard", -1)
        modify_faction(player, "faction_union", -2)
        log = (
            "Wealdhere's eyes narrow. \"You expect me to believe a humble sweeper just stumbled across hidden syndicalist literature?\"\n"
            "\"I think you lost your nerve and decided to turn it in before we caught you!\"\n"
            "They burn the pamphlets and write your name in their black ledger. \"I'm watching you, agitator. Now get out!\"\n\n"
            "*** The Watch suspects you of sedition! (-2 Reputation, -1 Guard Faction, -2 Union Faction) ***\n"
            "*** Return to Godwin at the Market to finish your shift! ***"
        )
        return player, log, "MAIN"

    if choice == "Leave":
        if player["reputation"] < 0:
            return player, "\"You've got a lot of nerve walking in here with your reputation,\" they growl, hand resting on their sword.\n\"Get out before I throw you in a cell to rot.\"", "MAIN"
        return player, "\"Then stop wasting my time.\"", "MAIN"
        
    if choice == "Hand in Radical Pamphlets":
        player["inventory"].remove("bundle of radical pamphlets")
        player["wealdhere_state"] = "contraband_interrogation"
        log = (
            "You hand the oilskin bundle to Captain Wealdhere. They unwrap it, read a single line of Proudhon, and slam their fist onto the desk.\n"
            "\"Anarchist filth! 'Property is Theft'?!\"\n"
            "Wealdhere stands up, looming over you suspiciously. \"And how do I know YOU aren't the courier who brought this sedition into Murum?! Speak quickly!\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Deliver Halberds":
        player["inventory"].remove("bundle of halberds")
        log = (
            "Captain Wealdhere gestures for a guard to take the heavy bundle.\n"
            "They look you up and down, sneering slightly.\n"
            "\"Lovejoy is sending errand runners now? Hmph. Tell that Blacksmith that the steel better be stronger than the person delivering it.\"\n"
            "*** Halberds delivered! ***"
        )
        return player, log, "MAIN"

    if choice == "Interact":
        if player.get("active_stable_task") == "find_coryllus":
            log = (
                "You ask if Wealdhere heard any commotion earlier.\n"
                "Wealdhere groans. \"Did I? Some clumsy new recruit dropped an entire rack of halberds down the armoury stairs.\"\n"
                "\"The clatter was deafening. Sounded like a dragon crashing into a forge. Why do you ask?\"\n"
                "\"And judging by those tracks leading North East I was not the only beast whose heart leapt out of their mouth.\"\n"
                "*** CLUE: Coryllus was spooked by a massive metallic clatter from the Guard House. ***"
            )
            return player, log, "MAIN"
        return player, "\"State your business, citizen. My guards have a town to protect.\"", "MAIN"
        
    if choice in [
        "Report Corruption",
        "Report Wallmaker Intel (Undercover)",
        "Report Breach Blueprint (Undercover)",
        "Report True Damage Ledger (Undercover)",
        "Let Wealdhere Mark Contraband (Undercover)"
    ]:
        if player.get("surveyor_report") == "failed_break_in":
            player["wallmaker_double_agent"] = True
            player["reported_shift_1_to_guard"] = True
            player["silver"] += 7
            player["reputation"] += 1
            modify_faction(player, "faction_guard", 2)
            log = (
                "You quietly show Captain Wealdhere your surveyor notes on the failed break-in and Wellspring's cover-up.\n"
                "Wealdhere's eyes gleam. Instead of sounding the alarm, they lower their voice.\n"
                "\"A prybar in the masonry—and Wellspring wants you to brick it up quietly tomorrow? Listen to me, citizen.\"\n"
                "\"Arresting one crooked foreman won't catch their smuggling ring. I want you to stay undercover as my Double Agent.\"\n"
                "Wealdhere slides 7 silver coins across the oak desk.\n"
                "\"Use the Watch's silver to pay Hopestill's extortion fee at the Tavern so they suspect nothing. Do every shift they ask, and we will bust the entire syndicate on smuggling night!\"\n\n"
                "*** DOUBLE AGENT RECRUITED! (+7 Silver for Hopestill, +1 Reputation, +2 Guard Faction) ***\n"
                "*** Now go to the Murum Tavern and pay Hopestill their 7s to keep your cover intact! ***"
            )
            return player, log, "MAIN"

        elif player.get("surveyor_report") == "breach_rigged":
            player["wallmaker_double_agent"] = True
            player["reported_shift_2_to_guard"] = True
            player["silver"] += 7
            player["reputation"] += 1
            modify_faction(player, "faction_guard", 2)
            log = (
                "You sketch the exact 5x5 Pentomino layout for Captain Wealdhere, pointing out the Y-Keystone that locks the U-Hollow smuggling cavity, and show them the Smuggler's Cipher.\n"
                "Wealdhere copies the cipher markings into their black ledger and slides 7 silver across the desk.\n"
                "\"A hollow stone right behind the forge... clever bastards. My sappers will know the exact keystone to knock out on raid night.\"\n"
                "\"Keep the cipher on you and pay Hopestill their 7 silver at the Tavern. We're tightening the noose!\"\n\n"
                "*** SHIFT 2 INTEL LOGGED! (+7 Silver for Hopestill, +1 Reputation, +2 Guard Faction) ***"
            )
            return player, log, "MAIN"

        elif player.get("surveyor_report") == "damage_ledger":
            player["wallmaker_double_agent"] = True
            player["reported_shift_3_to_guard"] = True
            player["silver"] += 7
            player["reputation"] += 1
            modify_faction(player, "faction_guard", 2)
            route = player.get("sabotaged_route", "through")
            log = (
                "You hand Captain Wealdhere a secret copy of the true 4x4x4 surveyor ledger and point out how the Guild's board was altered.\n"
                f"Wealdhere chuckles grimly. \"So Hopestill thinks the '{route.title()} the Wall' route is unguarded? Perfect. "
                "I will let the Guild believe the repair crew went to the wrong wall while my marksmen stake out all three approaches.\"\n"
                "They slide 7 silver coins across the desk.\n"
                "\"Pay Hopestill their cut at the Tavern. Tomorrow they'll send you after the contraband cache itself!\"\n\n"
                "*** SHIFT 3 INTEL LOGGED! (+7 Silver for Hopestill, +1 Reputation, +2 Guard Faction) ***"
            )
            return player, log, "MAIN"

        elif player.get("surveyor_report") == "parapet_cache":
            player["wallmaker_double_agent"] = True
            player["reported_shift_4_to_guard"] = True
            player["silver"] += 7
            player["reputation"] += 1
            modify_faction(player, "faction_guard", 2)
            log = (
                "You place the Contraband Silk Cache on Captain Wealdhere's desk.\n"
                "Careful not to disturb the Wallmakers' wax seal, Wealdhere dusts the underside of the oilskin with luminous alchemical chalk.\n"
                "\"Once their outside courier 'X' touches this parcel tomorrow, the chalk will glow under my guards' lanterns—undeniable proof of possession.\"\n"
                "They hand the parcel back along with 7 silver coins.\n"
                "\"Show Hopestill you have the goods and pay their cut. Tomorrow (Shift 5), when you meet 'X' for the transfer, my squad will spring the trap!\"\n\n"
                "*** CONTRABAND MARKED FOR THE STING! (+7 Silver for Hopestill, +1 Reputation, +2 Guard Faction) ***"
            )
            return player, log, "MAIN"

    return player, "Error.", "MAIN"

# -------------------------------------------------------------------------
# THE MAYOR (VERITY GIVETHANKS)
# -------------------------------------------------------------------------
def get_mayor_options(player):
    state = player.get("mayor_dialogue_state")
    if state == "union_choice":
        return ["Side with Mayor", "Side with Truthtale"]
    return ["Interact", "Leave"]

def resolve_mayor(choice, player):
    if choice == "Leave": 
        return player, "\"I am a very busy person. Speak to Praisegod if you need direction.\"", "MAIN"
        
    # --- UNION NEGOTIATION EVENT ---
    if choice == "Side with Mayor":
        player["reputation"] += 4
        player["charisma"] += 1
        player["influence"] = player.get("influence", 0) + 1
        player["faction_union"] = max(-10, modify_faction(player, "faction_union", -5))
        player["mayor_dialogue_state"] = None
        player["active_mayor_task"] = "finish_shift_5"
        db.npc_database["mayor"]["location"] = None
        log = (
            "You talk Truthtale down, forcing them to accept a standard wage increase.\n"
            "The Mayor is thrilled, but the Union feels betrayed.\n"
            "*** (+4 Reputation, +1 Charisma, +1 Influence, -5 Union Faction) ***\n\n"
            "\"Praisegod and I are returning to the estate,\" the Mayor sighs. \"Come collect your wages.\"\n"
            "*** The meeting is over. Return to the Mayor's House! ***"
        )
        return player, log, "MAIN"
        
    if choice == "Side with Truthtale":
        player["reputation"] -= 5
        modify_faction(player, "faction_union", 5)
        player["mayor_dialogue_state"] = None
        player["active_mayor_task"] = "finish_shift_5"
        db.npc_database["mayor"]["location"] = None
        set_region_territory(player, "Murum Farm", "Union")
        log = (
            "You stand with Truthtale. The Mayor storms out in a rage!\n"
            "The workers begin a massive strike, seizing the lower town and surrounding farmlands!\n"
            "*** (-5 Reputation, +5 Union Faction | Murum Farmland is now UNION TERRITORY!) ***\n\n"
            "\"Praisegod and I are returning to the estate,\" the Mayor sighs. \"Come collect your wages.\"\n"
            "*** The meeting is over. Return to the Mayor's House! ***"
        )
        return player, log, "MAIN"

    # --- STANDARD INTERACTS ---
    if choice == "Interact":
        task = player.get("active_mayor_task")
        
        if task == "inform_market":
            player["active_mayor_task"] = "attend_meeting"
            db.npc_database["mayor"]["location"] = "school"
            return player, "The Mayor is touring the market stalls with Praisegod.\n\"You secured the meeting with Truthtale? Excellent work.\"\n\"Praisegod and I will head to the School immediately. Meet us there.\"\n\n*** Go to the School for the negotiation! ***", "MAIN"
            
        elif task == "attend_meeting":
            if player["faction_union"] <= -3:
                player["reputation"] -= 3
                player["active_mayor_task"] = "finish_shift_5"
                db.npc_database["mayor"]["location"] = None
                log = (
                    "You stand in Dr. Makepeace's office. The Mayor sits on one side, Truthtale on the other.\n"
                    "Truthtale looks at you. They know your reputation among the workers.\n\n"
                    "\"We don't trust you, or your lackeys,\" Truthtale spits.\n"
                    "\"We demand a 200% wage increase and the immediate resignation of Praisegod!\"\n"
                    "The Mayor scoffs. \"Preposterous. This meeting is over.\"\n\n"
                    "The talks collapse. A strike is imminent.\n"
                    "*** Negotiation Failed! (-3 Reputation) ***\n\n"
                    "\"Praisegod and I are returning to the estate,\" the Mayor sighs. \"Come collect your wages.\"\n"
                    "*** The meeting is over. Return to the Mayor's House! ***"
                )
                return player, log, "MAIN"
            
            elif player["faction_union"] < 10:
                player["reputation"] += 3
                player["charisma"] += 1
                player["influence"] = player.get("influence", 0) + 1
                player["active_mayor_task"] = "finish_shift_5"
                db.npc_database["mayor"]["location"] = None
                log = (
                    "You stand in Dr. Makepeace's office. The Mayor sits on one side, Truthtale on the other.\n"
                    "Truthtale looks at you. They know your reputation among the workers.\n\n"
                    "\"We just want fair wages and safer hours,\" Truthtale says firmly.\n"
                    "You step in and mediate the discussion. After an hour, a compromise is reached.\n"
                    "The Mayor nods. \"Very well. It is done.\"\n\n"
                    "The strike is averted!\n"
                    "*** Negotiation Successful! (+3 Reputation, +1 Charisma, +1 Influence) ***\n\n"
                    "\"Praisegod and I are returning to the estate,\" the Mayor sighs. \"Come collect your wages.\"\n"
                    "*** The meeting is over. Return to the Mayor's House! ***"
                )
                return player, log, "MAIN"
            
            else:
                player["mayor_dialogue_state"] = "union_choice"
                log = (
                    "You stand in Dr. Makepeace's office. The Mayor sits on one side, Truthtale on the other.\n"
                    "Truthtale looks at you. They know your reputation among the workers.\n\n"
                    "Truthtale smiles at you. \"We have the people's support. We demand total control of the factories.\"\n"
                    "The Mayor turns red. \"Absolutely not! Whose side are you on?!\""
                )
                return player, log, "NPC_DIALOGUE"
                
        elif task == "find_mayor_1" and "mayor's incoming post" in player["inventory"]:
            player["inventory"].remove("mayor's incoming post")
            player["inventory"].append("mayor's horse letter")
            player["active_mayor_task"] = "blacksmith"
            db.npc_database["mayor"]["location"] = "school"
            log = (
                "The Mayor notices you holding the wax-sealed stack. \"Ah, the morning dispatches. Excellent.\"\n"
                "They tear one open, skim it, and sigh. \"Politics. Exhausting.\"\n"
                "They turn to you. \"You are my new staff? Good. Take this letter to Lovejoy at the Blacksmiths.\"\n"
                "\"It concerns the new shoes for my prized stallion. Bring me their response immediately.\"\n"
                "\"I must attend a meeting regarding school funding now. Meet me at the School when you have the response.\"\n\n"
                "*** The Mayor took the post and gave you a letter for the Blacksmith! ***"
            )
            return player, log, "MAIN"
            
        elif task == "find_mayor_2" and "blacksmith's horse report" in player["inventory"]:
            player["inventory"].remove("blacksmith's horse report")
            player["inventory"].append("mayor's dinner letter")
            player["active_mayor_task"] = "deliver_dinner_letter"
            db.npc_database["mayor"]["location"] = None
            log = (
                "The Mayor takes the report from you and reads it quickly. \"Splendid! Lovejoy always does fine work.\"\n"
                "They scribble a quick note on a scrap of parchment.\n"
                "\"Take this back to Praisegod at my house. It instructs them on what I wish to have for my evening meal.\"\n"
                "\"You have done well today. Dismissed.\"\n\n"
                "*** You received the dinner letter! Return to Praisegod to finish your shift! ***"
            )
            return player, log, "MAIN"
            
        elif task == "deliver_cake" and "mayor's birthday cake" in player["inventory"]:
            player["inventory"].remove("mayor's birthday cake")
            player["hunger"] = min(100, player["hunger"] + 30)
            player["active_mayor_task"] = "report_to_praisegod"
            db.npc_database["mayor"]["location"] = None
            log = (
                "The Mayor is sitting at a large table in the pub with Goodcheer, laughing loudly.\n"
                "They notice you. \"Ah! Praisegod sent you with the cake! Splendid!\"\n"
                "The Mayor cuts a massive slice for themselves, a slice for Goodcheer, and generously hands you a piece.\n"
                "\"Eat up, my friend! Today is a day for celebration!\"\n\n"
                "*** You ate a slice of the Mayor's cake! (+30 Hunger) ***\n\n"
                "\"Now, run back to Praisegod and tell them the delivery was a success.\""
            )
            return player, log, "MAIN"
            
        return player, "\"I am a very busy person. Speak to Praisegod if you need direction.\"", "MAIN"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# SIMPLE ONE-OFF NPCS (Union Clerk, Patience, Loveday)
# -------------------------------------------------------------------------
def get_union_clerk_options(player):
    opts = ["Interact"]
    if "mayor's incoming post" in player["inventory"] and not player.get("mayor_post_leaked_union"):
        opts.append("Whisper Mayor's Wage Memo (+Union)")
    opts.append("Leave")
    return opts

def get_simple_npc_options(player):
    return ["Interact", "Leave"]

def resolve_union_clerk(choice, player):
    if choice == "Leave": return player, "You step away.", "MAIN"

    if choice == "Whisper Mayor's Wage Memo (+Union)":
        player["mayor_post_leaked_union"] = True
        modify_faction(player, "faction_union", 3)
        player["influence"] = player.get("influence", 0) + 1
        log = (
            "You lean across the clerk's desk and quietly share the contents of the Mayor's incoming wage-freeze memorandum.\n"
            "The Union Clerk's eyes widen in gratitude. \"Truthtale will know of your solidarity inside the manor, comrade!\"\n"
            "*** (+3 Union Faction, +1 Influence) ***"
        )
        return player, log, "MAIN"
    
    task = player.get("active_mayor_task")
    if task == "investigate_union":
        return player, "\"You want to know about the workers' concerns?\" they scoff.\n\"If the Mayor actually cared, they would go through official channels. We aren't talking to anyone's spies. Out!\"", "MAIN"
        
    if task == "arrange_meeting" and "mayor's seal" in player["inventory"]:
        player["active_mayor_task"] = "inform_market"
        db.npc_database["mayor"]["location"] = (8, 15)
        log = (
            "The clerk scowls, but you slam the Mayor's heavy gold seal onto the desk.\n"
            "They pale slightly. \"An official parley? Very well.\"\n"
            "\"Truthtale will meet the Mayor at Escuela Moderna in one hour. Neutral ground.\"\n\n"
            "*** Meeting arranged! Find the Mayor and Praisegod at the Market! ***"
        )
        return player, log, "MAIN"
        
    return player, "\"Are you here to pay your dues? No? Then let me work.\"", "MAIN"

def resolve_mayors_maid(choice, player):
    if choice == "Leave": return player, "You step away.", "MAIN"
    if player.get("active_stable_task") == "find_coryllus":
        return player, "\"Keep away from me!\" she huffs. \"I've had enough near-death experiences for one morning!\"\n\"I was just walking down the main road when a massive, terrified horse nearly trampled me into the dirt!\"\n\"It tore off the road, heading straight for the Open Grazing Field. Animals are a menace!\"", "MAIN"
    return player, "\"Out of my way, please. The House Manager expects these vegetables immediately.\"", "MAIN"

def resolve_scullery_maid(choice, player):
    if choice == "Leave": return player, "You step away.", "MAIN"
    if player.get("active_stable_task") == "gather_supplies" and "bucket of hot water" not in player["inventory"]:
        player["inventory"].append("bucket of hot water")
        return player, "You quickly explain the foaling emergency at the stables.\n\"A foal? Oh, how sweet! Of course, here!\"\nShe quickly fills a wooden bucket from the boiling copper pot over the fire and hands it to you.\n\n*** You received a Bucket of Hot Water! ***", "MAIN"
    return player, "\"I have no time to chat! Praisegod will have my head if these pots aren't spotless!\"", "MAIN"

# -------------------------------------------------------------------------
# CROUPIER FORTUNESMILE (THE HOUSE OF GAMES & ARCADE)
# -------------------------------------------------------------------------
def get_croupier_options(player):
    state = player.get("croupier_state")
    chips = player.get("casino_chips", 0)

    if state == "cashier":
        opts = [
            "Buy 10 Casino Chips (10s)",
            "Buy 50 Casino Chips (50s)",
            f"Cash Out All Chips ({chips}s)",
        ]
        if player.get("casino_loan_owed", 0) > 0:
            opts.append("Repay House Marker (60 Silver or 60 Chips)")
        else:
            opts.append("Take 50-Chip House Loan (Repay 60s in 3 Days)")
        opts.append("< Back")
        return opts

    if state == "tables":
        return [
            "Play Twenty-One (Blackjack)",
            "Play Texas Hold'em vs. Everpenitent",
            "Play Roulette",
            "Play Craps (The Bones)",
            "< Back"
        ]

    if state == "rules_main":
        return [
            "Rules: Roulette (The Red Wheel)",
            "Rules: Craps (The Bones)",
            "Rules: Blackjack (Twenty-One)",
            "Rules: Texas Hold'em Poker",
            "Rules: Mechanical Arcade Cabinets",
            "< Back"
        ]

    if state == "rules_arcade":
        return [
            "How to play: Forge & Jigsaw",
            "How to play: Thief Chase & Fly-Tipping",
            "How to play: Parapet, Smuggle, Cauldron & Archery",
            "< Back to Rules"
        ]

    return [
        "Play Mechanical Arcade Cabinets",
        f"Casino Cashier (Chips: {chips} | Silver: {player['silver']}s)",
        "Visit Card & Roulette Tables",
        "Ask to Explain the Rules of the Games",
        "Leave"
    ]


def resolve_croupier(choice, player):
    if choice == "Leave":
        player["croupier_state"] = None
        return player, "Croupier Fortunesmile tips her velvet visor. \"Fortune favours the bold. Come back whenever you fancy a spin!\"", "MAIN"

    if choice == "Play Twenty-One (Blackjack)":
        player["croupier_state"] = None
        import mini_games
        return mini_games.init_blackjack(player)

    if choice == "Play Texas Hold'em vs. Everpenitent":
        player["croupier_state"] = None
        import mini_games
        return mini_games.init_poker(player)

    if choice == "Play Roulette":
        player["croupier_state"] = None
        import mini_games
        return mini_games.init_roulette(player)

    if choice == "Play Craps (The Bones)":
        player["croupier_state"] = None
        import mini_games
        return mini_games.init_craps(player)

    if choice == "< Back":
        player["croupier_state"] = None
        return player, "\"The wheel never stops turning. What is your pleasure?\"", "NPC_DIALOGUE"

    if choice == "< Back to Rules":
        player["croupier_state"] = "rules_main"
        return player, "\"Which game's rules would you like me to explain?\"", "NPC_DIALOGUE"

    if choice == "Play Mechanical Arcade Cabinets":
        player["croupier_state"] = None
        import mini_games
        return player, mini_games.get_arcade_menu_text(player), "ARCADE_MENU"

    # --- RULES EXPLANATIONS ---
    if choice == "Ask to Explain the Rules of the Games":
        player["croupier_state"] = "rules_main"
        log = (
            "Croupier Fortunesmile rests her hands on the polished mahogany rail and smiles warmly.\n"
            "\"Whether you prefer the spin of the ivory ball, the turn of a card, or testing your reflexes on our clockwork parlour machines, "
            "it pays to know the house rules before you wager. Which game shall I explain?\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Rules: Roulette (The Red Wheel)":
        log = (
            "--- HOUSE RULES: ROULETTE ---\n"
            "\"Our signature wheel has 37 numbered pockets: 1 through 36 coloured alternately in Red and Black, plus a single green Zero (0) for the House.\"\n"
            "• OUTSIDE BETS (Even Money, 1-to-1 payout): Bet on Red or Black, Odd or Even, or Low (1–18) vs. High (19–36).\n"
            "• DOZENS & COLUMNS (2-to-1 payout): Bet on a block of 12 numbers (1st 12, 2nd 12, or 3rd 12).\n"
            "• STRAIGHT UP (35-to-1 payout): Place your chips directly on a single number. If the ivory ball lands in your pocket, you win 35 times your stake!"
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Rules: Blackjack (Twenty-One)":
        log = (
            "--- HOUSE RULES: BLACKJACK (TWENTY-ONE) ---\n"
            "\"You play directly against the Dealer. The goal is to build a hand closer to 21 than the Dealer's without going over (Busting).\"\n"
            "• CARD VALUES: Number cards count at face value, Face Cards (J, Q, K) count as 10, and Aces count as either 1 or 11.\n"
            "• YOUR TURN: After receiving two cards, you may 'Hit' (draw another card), 'Stand' (hold your total), or 'Double Down' (double your wager for exactly one final card).\n"
            "• DEALER RULES: The House Dealer must Hit on 16 or less and Stand on 17 or more. An initial Ace + 10-value card is a natural Blackjack and pays 3-to-2!"
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Rules: Texas Hold'em Poker":
        log = (
            "--- HOUSE RULES: TEXAS HOLD'EM POKER ---\n"
            "\"Each player is dealt 2 private 'Hole Cards', and 5 'Community Cards' are dealt face-up in the centre across three stages: the Flop (3 cards), the Turn (1 card), and the River (1 card).\"\n"
            "• BETTING: On each street you may Check, Bet, Call, Raise, or Fold.\n"
            "• THE SHOWDOWN: You make the strongest 5-card poker hand using any combination of your 2 hole cards and the 5 community cards.\n"
            "• HAND RANKINGS (Highest to Lowest): Royal Flush, Straight Flush, Four of a Kind, Full House, Flush, Straight, Three of a Kind, Two Pair, One Pair, High Card."
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Rules: Craps (The Bones)":
        log = (
            "--- HOUSE RULES: CRAPS (THE BONES) ---\n"
            "\"When the Puck is OFF, the shooter makes a Come-Out Roll:\"\n"
            "• PASS LINE (1:1): Wins immediately on 7 or 11; loses on 2, 3, or 12. Any other number (4, 5, 6, 8, 9, 10) becomes the POINT (Puck turns ON). Roll the Point again before a 7 to win!\n"
            "• FREE ODDS & PLACE BETS: Once a Point is ON, you can back your Pass Line with True Free Odds or place bets directly on 4, 5, 6, 8, 9, or 10.\n"
            "• THE FIELD & PROPOSITIONS: Bet on single rolls (Field, Any 7, Snake Eyes 30:1, Boxcars 30:1, Yo-11 15:1) or multi-roll Hardways (pairs like 2-2, 3-3, 4-4, 5-5 before a 7 or easy total)!"
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Rules: Mechanical Arcade Cabinets":
        player["croupier_state"] = "rules_arcade"
        log = (
            "--- THE MECHANICAL ARCADE PARLOUR ---\n"
            "\"Along our back wall sit seven clockwork training cabinets modelled after the trades of Murum.\"\n"
            "\"Playing them here in the Arcade is purely for sport and High Scores—you won't risk a single coin or affect your job in town! Which cabinet's rules would you like to hear?\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "How to play: Forge & Jigsaw":
        log = (
            "--- ARCADE RULES: FORGE & JIGSAW ---\n"
            "• BLACKSMITH FORGE: Watch the thermometer for 20 strikes before the timer bar runs out! If the steel is COLD (orange), click 'Pump Bellows'. If PERFECT (red), click 'Add Coal'. If HOT (white), click 'Wait'.\n"
            "• MASONRY JIGSAW: Fit all 5 coloured pentomino pieces into the 5x5 square frame. Left-Click to pick up or place a piece, and Right-Click while holding a piece to rotate it 90 degrees!"
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "How to play: Thief Chase & Fly-Tipping":
        log = (
            "--- ARCADE RULES: THIEF CHASE & FLY-TIPPING ---\n"
            "• MARKET THIEF CHASE: Watch the 3-lane horizontal gauge (Dart Left, Straight, Shot Right). Click the matching lane before the red timer runs out! Reacting in the first half of the timer closes 2 paces instead of 1.\n"
            "• FLY-TIPPING CITATION BOARD: Read the Heap and Alibi clues, then Left/Right-Click the Dumping Spot and Waste Type chits on the 4-row board until all 4 merchants match their true crime!"
        )
        return player, log, "NPC_DIALOGUE"

    if choice in ["How to play: Parapet, Smuggle & Cauldron", "How to play: Parapet, Smuggle, Cauldron & Archery"]:
        log = (
            "--- ARCADE RULES: PARAPET, SMUGGLE, CAULDRON & ARCHERY ---\n"
            "• PARAPET CACHE: Close your lantern shutter before an Arrow Slit [SLIT] and open it before Dark Rubble [CANT]. Then slide the stone pins so the gold [SILK] block reaches the [EXIT]!\n"
            "• SMUGGLER RUN: Tap the 4-beat mason code only when no patrol is in earshot, pick a route, and match the 3 wall hazard prompts!\n"
            "• APOTHECARY CAULDRON: Cycle the Reagent and Dram quantity (1–4) to match each of the 4 steps on the formula scroll.\n"
            "• SHARPSHOOTER ARCHERY: Draw your bow (SPACE or Click), guide your swaying sight box against the wind (your Strength steadies your bow-arm!), and loose into the gold bullseye!"
        )
        return player, log, "NPC_DIALOGUE"

    # --- CASHIER & TABLES ---
    if choice.startswith("Casino Cashier"):
        player["croupier_state"] = "cashier"
        chips = player.get("casino_chips", 0)
        log = (
            "Croupier Fortunesmile gestures to the brass cashier's cage.\n"
            f"\"Each Red Wheel Chip is backed one-for-one in fine Murum silver (You hold: {chips} Chips).\"\n"
            "\"And between you and me—Highway Robbers on the New Road don't know what to do with ivory chips, so many travellers bank their silver here before leaving town!\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Buy 10 Casino Chips (10s)":
        if player["silver"] >= 10:
            player["silver"] -= 10
            player["casino_chips"] = player.get("casino_chips", 0) + 10
            return player, f"You slide 10 silver across the cage and receive a stack of 10 crimson ivory chips. (Chips: {player['casino_chips']} | Silver: {player['silver']}s)", "NPC_DIALOGUE"
        return player, "\"You need at least 10 silver for that stack.\"", "NPC_DIALOGUE"

    if choice == "Buy 50 Casino Chips (50s)":
        if player["silver"] >= 50:
            player["silver"] -= 50
            player["casino_chips"] = player.get("casino_chips", 0) + 50
            return player, f"You exchange 50 silver for a heavy cylinder of 50 crimson chips. (Chips: {player['casino_chips']} | Silver: {player['silver']}s)", "NPC_DIALOGUE"
        return player, "\"You need 50 silver for a full cylinder of chips.\"", "NPC_DIALOGUE"

    if choice.startswith("Cash Out All Chips"):
        chips = player.get("casino_chips", 0)
        if chips <= 0:
            return player, "\"You don't have any Casino Chips to cash out!\"", "NPC_DIALOGUE"
        player["silver"] += chips
        player["casino_chips"] = 0
        return player, f"Croupier Fortunesmile counts your ivory chips and slides {chips} gleaming silver coins back across the baize! (Silver: {player['silver']}s)", "NPC_DIALOGUE"

    if choice == "Visit Card & Roulette Tables":
        player["croupier_state"] = "tables"
        return player, "\"Our Roulette wheel, Blackjack shoe, and Texas Hold'em tables are being dressed for the evening high-rollers. Which table catches your eye?\"", "NPC_DIALOGUE"

    if choice in ["Roulette Table (Coming Soon)", "Blackjack Table (Coming Soon)", "Texas Hold'em Table (Coming Soon)"]:
        table_name = choice.split(" (")[0]
        log = (
            f"You step up to the green baize of the {table_name}.\n"
            "The pit boss polishes the brass trim and nods respectfully. \"The high-stakes table opens shortly—meanwhile, ask Fortunesmile if you'd like to learn the rules, or try the Mechanical Arcade Cabinets along the back wall!\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Take 50-Chip House Loan (Repay 60s in 3 Days)":
        if player.get("casino_loan_owed", 0) > 0:
            return player, "\"You already have an open marker with the House! Repay your 60s debt first.\"", "NPC_DIALOGUE"
        player["casino_chips"] = player.get("casino_chips", 0) + 50
        player["casino_loan_owed"] = 60
        player["casino_loan_due_min"] = player.get("total_game_minutes", 0) + 3000  # 3 Days (3,000 mins)
        log = (
            "Croupier Fortunesmile slides a heavy crimson cylinder of 50 Chips across the brass cage and has you thumb-sign a ledger.\n"
            "\"You have 3 days (3,000 minutes) to repay 60 Silver or 60 Chips. Do not make me send Ironjaw looking for you...\"\n"
            f"*** +50 Casino Chips! (60s Marker due in 3 days | Chips: {player['casino_chips']}) ***"
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Repay House Marker (60 Silver or 60 Chips)":
        owed = player.get("casino_loan_owed", 60)
        if player.get("casino_chips", 0) >= owed:
            player["casino_chips"] -= owed
            player["casino_loan_owed"] = 0
            player["casino_loan_due_min"] = None
            return player, f"You slide {owed} Chips across the cage. Fortunesmile stamps your marker PAID and tears it in half! (Remaining Chips: {player['casino_chips']})", "NPC_DIALOGUE"
        elif player.get("silver", 0) >= owed:
            player["silver"] -= owed
            player["casino_loan_owed"] = 0
            player["casino_loan_due_min"] = None
            return player, f"You count out {owed} Silver coins. Fortunesmile stamps your marker PAID and tears it in half! (Remaining Silver: {player['silver']}s)", "NPC_DIALOGUE"
        return player, f"\"Your marker is for {owed} Silver (or {owed} Chips). Come back when you have the full sum—before the 3 days expire!\"", "NPC_DIALOGUE"

    return player, "Error.", "MAIN"

# -------------------------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------------------------
HANDLERS = {
    "makepeace":            (get_makepeace_options, resolve_makepeace),
    "fairlight":            (get_fairlight_options, resolve_fairlight),
    "fearnot":              (get_butler_options, resolve_butler),
    "mayors house manager": (get_mayors_house_manager_options, resolve_mayors_house_manager),
    "landlord":             (get_landlord_options, resolve_landlord),
    "sigeberht":            (get_guard_options, resolve_sigeberht),
    "aelfgifu":             (get_guard_options, resolve_aelfgifu),
    "snail envoy":          (get_snail_envoy_options, resolve_snail_envoy),
    "wealdhere":            (get_wealdhere_options, resolve_wealdhere),
    "mayor":                (get_mayor_options, resolve_mayor),
    "union clerk":          (get_union_clerk_options, resolve_union_clerk),
    "mayors maid":          (get_simple_npc_options, resolve_mayors_maid),
    "scullery maid":        (get_simple_npc_options, resolve_scullery_maid),
    "croupier":             (get_croupier_options, resolve_croupier),
}
