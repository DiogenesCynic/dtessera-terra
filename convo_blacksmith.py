import game_data as db
from mechanics import (
    modify_faction, advance_time, handle_sleep_nap, handle_sleep_morning,
    get_time_string, calculate_max_hit, get_eligible_chapter_2_routes,
    can_start_shift, mark_shift_started, mark_shift_completed,
    get_inventory_weight, get_max_carry_weight
)
import encounters
import mini_games

# -------------------------------------------------------------------------
# BLACKSMITH (LOVEJOY)
# -------------------------------------------------------------------------
def get_blacksmith_options(player):
    options = []
    
    # Mayor Quest Intercepts
    if player["active_mayor_task"] == "blacksmith" and "mayor's horse letter" in player["inventory"]:
        return ["Give Mayor's Letter"]
    if player["active_mayor_task"] == "get_coal":
        return ["Ask for Mayor's Coal", "Leave"]
    if player["active_mayor_task"] == "blacksmith_horse" and "mayor's stallion" in player["inventory"]:
        return ["Drop off Stallion"]
    if player["active_mayor_task"] == "collect_shod_horse":
        return ["Collect Shod Stallion"]    
    if player.get("blacksmith_state") == "forge_instructions":
        return ["I understand. Begin Forging!"]
    if player.get("blacksmith_state") == "shift_6_prompt":
        return ["Proceed with shift", "Hand in notice with immediate effect"]
    if player.get("blacksmith_state") == "mercenary_confrontation":
        return ["Fight him!", "Challenge to a duel", "Talk him down", "Call the Guard"]

    # Job Options
    if player["current_job"] == "blacksmith":
        if player.get("active_blacksmith_task"):
            if player["active_blacksmith_task"] == "prepare_drill_parts" and "package of drill parts" in player["inventory"] and "leather" in player["inventory"]:
                options.append("Assemble Masonry Drill")
            else:
                options.append("Return from Task")
        else:
            options.append(f"Start Shift ({player['blacksmith_shifts_completed']} Completed)")
            if player["blacksmith_shifts_completed"] >= 6:
                options.append("Hand in notice with immediate effect")
    else:
        options.append("Apply for Apprenticeship")
        
    options.append("Shoe Horse (20s)")
    options.append("Leave")
    return options

def resolve_blacksmith(choice, player):
    if choice == "Leave":
        player["blacksmith_state"] = None
        return player, "\"Mind the heat on your way out.\"", "MAIN"
    if choice == "Back":
        player["blacksmith_state"] = None
        return player, "You step back from the wares.", "NPC_DIALOGUE"

    if choice == "Hand in notice with immediate effect":
        player["blacksmith_state"] = None
        player["current_job"] = None
        player["current_tenure"] = 0
        player["active_blacksmith_task"] = None
        player["chapter_2_unlocked"] = True
        log = (
            "Lovejoy sets down his hammer and nods slowly.\n"
            "\"You've mastered my anvil, Noburu. A smith of your strength and skill shouldn't be tied to another's bellows forever.\"\n"
            "\"Have a look at the Noticeboard in the Town Hall—there are wider horizons waiting for you.\"\n\n"
            "*** You have handed in your notice! Visit the Noticeboard in the Town Hall to explore new opportunities! ***"
        )
        return player, log, "MAIN"

    if choice == "Proceed with shift":
        player["blacksmith_state"] = None
        player["blacksmith_shift_6_prompted"] = True
        choice = f"Start Shift ({player['blacksmith_shifts_completed']} Completed)"

    if choice == "I understand. Begin Forging!":
        player["blacksmith_state"] = None
        player["active_blacksmith_task"] = "tame_furnace"

        player["forge_round"] = 1
        player["forge_mistakes"] = 0
        player["forge_time_limit"] = 5.0
        player["forge_timer"] = 5.0
        player["forge_heat_state"] = 1
        
        log = "*** The furnace roars to life! Watch the steel! ***"
        return player, log, "MINIGAME_FORGE"

    # --- SHIFT 4: CONFRONTATION CHOICES ---
    if player.get("blacksmith_state") == "mercenary_confrontation":
        if choice == "Fight him!":
            player["blacksmith_state"] = None
            return encounters.trigger_mercenary_brawl(player)

        elif choice == "Challenge to a duel":
            player["blacksmith_state"] = None
            player["active_blacksmith_task"] = "mercenary_duel"
            player["duel_day"] = (player["total_game_minutes"] // 1000) + 2 # Tomorrow
            player = mark_shift_completed(player)
            player, _ = advance_time(30, player)
            db.npc_database["mercenary"]["location"] = (8, 13) # The Grazing Field
            log = (
                "You step between them and challenge the mercenary to a formal duel.\n"
                "He sneers. \"Fine. Tomorrow morning. The Grazing Field. Don't be late.\"\n"
                "He storms out. Lovejoy looks at you. \"Foolish, but brave. Prepare yourself.\"\n\n"
                "*** QUEST: Meet the Mercenary at the Grazing Field between 3:75 and 4:75 tomorrow! ***"
            )
            return player, log, "MAIN"

        elif choice == "Talk him down":
            if player["charisma"] >= 2:
                player["blacksmith_state"] = None
                player["blacksmith_shifts_completed"] += 1
                player["current_tenure"] += 1
                player = mark_shift_completed(player)
                player["silver"] += 25
                player["strength"] += 1
                player, _ = advance_time(120, player)
                log = (
                    "You step forward, projecting unshakeable confidence. You loudly shame him for abusing his blade, pointing out his poor fighting form to the gathering crowd.\n"
                    "Embarrassed, he sheathes his weapon and leaves in a huff.\n"
                    "Lovejoy grunts. \"A silver tongue. Better than a broken jaw. Take your pay.\"\n"
                    "*** Shift Completed! (+25 Silver, +1 Strength) ***"
                )
                return player, log, "MAIN"
            else:
                log = (
                    "You try to reason with him, but you lack the presence (Charisma < 2).\n"
                    "He shoves you aside! You have no choice but to defend yourself!"
                )
                player["blacksmith_state"] = None
                player, combat_log, state = encounters.trigger_mercenary_brawl(player)
                return player, log + "\n\n" + combat_log, state

        elif choice == "Call the Guard":
            player["blacksmith_state"] = None
            player["blacksmith_shifts_completed"] += 1
            player = mark_shift_completed(player)
            fine = min(player["silver"], 15)
            player["silver"] = player["silver"] - fine + 10 # Docked pay + repair fine!
            player, _ = advance_time(120, player)
            log = (
                "You run out and flag down Sigeberht. The guard bursts in and arrests the mercenary after a brief scuffle that cracks a workbench.\n"
                "Lovejoy is safe, but he is furious that you brought the town watch into his shop.\n"
                f"\"I don't need the Castellan's lapdogs in my forge! I'm docking {fine} silver for the damaged bench and cutting your shift pay to 10 silver!\"\n"
                f"*** Shift Completed... poorly. (-{fine}s Repair Fine, +10s Pay) ***"
            )
            return player, log, "MAIN"

    if choice == "Give Mayor's Letter":
        player["inventory"].remove("mayor's horse letter")
        player["inventory"].append("blacksmith's horse report")
        player["active_mayor_task"] = "find_mayor_2"
        db.npc_database["mayor"]["location"] = "school"
        log = (
            "Before you can speak, Lovejoy notices the Mayor's seal on the letter in your hand.\n"
            "\"Ah, for the stallion. Let me see that.\"\n"
            "They wipe soot from their brow, read the note, and grunt.\n"
            "\"Tell Their Worship the shoes are forged from the finest steel. Coryllus will walk on air.\"\n"
            "They scrawl a messy response on the back of the parchment and hand it to you.\n"
            "*** You received the Blacksmith's report! You need to find the Mayor at the School. ***"
        )
        return player, log, "MAIN"

    if choice == "Ask for Mayor's Coal":
        player["active_mayor_task"] = "negotiate_coal"
        log = (
            "Lovejoy scowls and points at an empty coal bin.\n"
            "\"A sack of coal for the Mayor? I barely have enough to keep my own furnace lit!\"\n"
            "\"Wellspring at the Wallmakers' Offices impounded my latest coal shipment over an unpaid horse-shoeing dispute.\"\n"
            "\"Go to the Wallmakers' Offices and get Wellspring to release the coal!\""
        )
        return player, log, "MAIN"

    if choice == "Drop off Stallion":
        player["inventory"].remove("mayor's stallion")
        player["active_mayor_task"] = "riding_lesson"
        log = (
            "Lovejoy inspects the Mayor's stallion.\n"
            "\"Needs new shoes? Leave him here. It will take an hour or two.\"\n"
            "\"Go back to the Stables and take a riding lesson while you wait.\""
        )
        return player, log, "MAIN"

    if choice == "Collect Shod Stallion":
        player["inventory"].append("mayor's shod stallion")
        player["active_mayor_task"] = "water_horse"
        log = (
            "Lovejoy finishes hammering the last nail.\n"
            "\"There. Good as new. Take him to the market fountain for a drink, he's thirsty.\""
        )
        return player, log, "MAIN"

    if choice == "Shop for Gear":
        return player, "\"I don't sell retail over the anvil anymore! Go see the Armourer at Murum High Street—they handle all sales of my blades and shields.\"", "MAIN"

    if choice == "Shoe Horse (20s)":
        if player["silver"] >= 20:
            player["silver"] -= 20
            player["horse_shoe_durability"] = 50
            return player, "You hand over the silver and the Blacksmith leads your horse away to be shod.\n*** Your horse has been fitted with fresh steel shoes! (Durability restored) ***", "MAIN"
        return player, f"\"You do not have enough silver! You only have {player['silver']}.\"", "MAIN"

    if choice == "Apply for Apprenticeship":
        if player["current_job"] is not None and player["current_job"] != "blacksmith":
            return player, "'An apprenticeship requires total dedication. Quit your other work first.'", "MAIN"
        if "reference letter" not in player["inventory"]:
            return player, "\"Apprenticeship? I only take on folk with a proven, solid reputation in this town.\"\n\"Come back when you have a formal letter of reference.\"", "MAIN"
        if player["reputation"] < 2:
            return player, f"\"I see your letter, but your reputation is still lacking.\"\n\"Come back when you're well-regarded. (Requires 2 Reputation, you have {player['reputation']})\"", "MAIN"
            
        player["current_job"] = "blacksmith"
        player["current_tenure"] = 0
        player["active_blacksmith_task"] = None
        return player, "Lovejoy looks you up and down. \"Fine. You're my new apprentice. Don't slow me down.\"", "MAIN"

    if choice == "Assemble Masonry Drill":
        if "jigsaw_grid" not in player:
            return mini_games.init_jigsaw(player)
        return player, "You return to the blueprint.", "MINIGAME_JIGSAW"

    # --- STARTING A SHIFT ---
    if choice.startswith("Start Shift"):
        ok, msg = can_start_shift(player)
        if not ok:
            return player, msg, "MAIN"
        player = mark_shift_started(player)
        
        shifts = player["blacksmith_shifts_completed"]

        # --- SHIFT 6 EVALUATION: NOTICEBOARD OR DISMISSAL (GAME OVER) ---
        if shifts == 5 and not player.get("blacksmith_shift_6_prompted"):
            eligible = get_eligible_chapter_2_routes(player)
            if not eligible:
                player["current_job"] = None
                player["current_tenure"] = 0
                log = (
                    "Lovejoy sets down his hammer, crosses his arms, and glares at you.\n"
                    "\"I am afraid that you have failed to reach the level that we expect of a blacksmith's apprentice in the time that you have been here. "
                    "We are going to have to let you go. I cannot see you acquiring any further work in Murum. "
                    "You will have to try your luck on the road. I wish you luck.\"\n\n"
                    "*** GAME OVER: You failed to qualify for any Chapter 2 path and have been dismissed from Murum! ***"
                )
                return player, log, "DEAD"

            player["blacksmith_state"] = "shift_6_prompt"
            player["chapter_2_unlocked"] = True
            log = (
                "Lovejoy leans on his anvil and looks you in the eye.\n"
                "\"You're a Master Blacksmith now, Noburu. With your new experience and skills, "
                "there may be new opportunities for you if you look at the Noticeboard in the Town Hall.\"\n"
                "\"Do you want to proceed with your shift today, or hand in your notice with immediate effect?\""
            )
            return player, log, "NPC_DIALOGUE"
        
        if shifts == 0:
            player["active_blacksmith_task"] = "deliver_goods"
            player["blacksmith_task_deadline"] = player["total_game_minutes"] + 300
            player["inventory"].extend(["crate of horseshoes", "bundle of halberds", "custom breastplate"])
            log = (
                "Lovejoy points a heavy pair of tongs at a massive pile of goods.\n"
                "\"Before you touch a hammer, you need to prove you have the stamina.\"\n"
                "\"Take the Crate of Horseshoes to Squire Godspeed at the Stables.\"\n"
                "\"Take the Bundle of Halberds to Captain Wealdhere at the Guard House.\"\n"
                "\"And take the Custom Breastplate to the Armourer at the High Street.\"\n"
                "\"These items are incredibly heavy. Walking with them will slow you down and drain your stamina—and if you take longer than 300 minutes, I'm docking 10 silver for late delivery!\"\n"
                "\"Plan your route carefully!\"\n\n"
                "*** SHIFT STARTED! Deliver the heavy goods within 300 minutes! ***"
            )
            return player, log, "MAIN"

        elif shifts == 1:
            player["blacksmith_state"] = "forge_instructions"
            log = (
                "Lovejoy hands you a heavy forging hammer and tongs.\n"
                "\"Sweeping and deliveries are over. Today, you temper a blade.\"\n"
                "\"The heat of the furnace shifts rapidly. You must watch the steel!\"\n"
                "\"Now remember: high-carbon steel ingots cost 15 silver a bar. Ruin the temper, and it comes out of your pocket!\"\n"
                "\"If it goes dull orange (COLD), pump the bellows!\"\n"
                "\"If it hits cherry red (PERFECT), add coal to maintain it!\"\n"
                "\"If it goes blinding white (HOT), wait for it to cool!\"\n"
                "\"You have to strike perfectly 20 times. And be quick... the metal won't wait for you!\"\n\n"
                "\"Do you understand the instructions?\""
            )
            return player, log, "NPC_DIALOGUE"

        elif shifts == 2:
            player["active_blacksmith_task"] = "prepare_drill_parts"
            player["inventory"].append("wallmaker blueprint")
            log = (
                "Lovejoy slams a rolled-up parchment onto the anvil.\n"
                "\"Wellspring dropped this off. The Wallmakers want a 'Hollow-Bore Masonry Drill'.\"\n"
                "\"I bash steel, I don't fiddle with intricate merchant tools. You make it—and you front the silver for the parts and leather yourself.\"\n"
                "\"Go to the Post Office and order the specialized drill parts (10s). It'll take two days to arrive.\"\n"
                "\"In the meantime, go to the Commissary at the High Street and buy some thick Leather for the strap.\"\n"
                "\"Once you have both the Parts and the Leather, come back here and assemble it.\"\n\n"
                "*** SHIFT STARTED: Read the blueprint, order the parts, and buy the leather! ***"
            )
            return player, log, "MAIN"

        elif shifts == 3:
            player["blacksmith_state"] = "mercenary_confrontation"
            log = (
                "An arrogant freelance mercenary storms into the forge, furious that his new sword chipped during a fight.\n"
                "Lovejoy inspects it and coldly states, \"You struck a stone wall, you fool. Steel isn't magic.\"\n"
                "The mercenary draws his weapon and threatens Lovejoy. Lovejoy refuses to fight a paying customer and tells him to leave.\n"
                "The mercenary lunges at him!\n\n"
                "*** HOW DO YOU RESPOND? ***"
            )
            return player, log, "NPC_DIALOGUE"

        elif shifts == 4:
            player["active_blacksmith_task"] = "stables_fire_rescue"
            player["fire_extinguished"] = False
            
            db.npc_database["head hostler"]["location"] = "tack room"
            player["x"], player["y"] = 10, 14
            player["current_building"] = "wallmakers' offices"
            
            log = (
                "Lovejoy wipes his hands. \"The Wallmakers want a new contract after seeing your drill work. Come with me.\"\n"
                "You arrive at the Wallmakers' Offices. Wellspring immediately starts pouring wine and talking numbers.\n"
                "Lovejoy sighs. \"This will take a while. You, head over to the barn—the Stables.\"\n"
                "\"Head Hostler Lightfoot still owes us for horseshoes. Collect the coin from him in the tack room, then meet me back at the forge.\"\n\n"
                "*** SHIFT STARTED: Go to the Stables and find the Head Hostler! ***"
            )
            return player, log, "MAIN"
            
        elif shifts >= 5:
            shift_pay = 30 if shifts >= 25 else 25 if shifts >= 10 else 20 if shifts >= 5 else 15
            
            player["silver"] += shift_pay
            player["strength"] += 1
            player, _ = advance_time(300, player)
            player = mark_shift_completed(player)
            player["blacksmith_shifts_completed"] += 1
            player["current_tenure"] += 1
            
            log = (
                "\"Grab a hammer and start working the bellows. Keep the heat steady.\"\n"
                "You spend the next few hours sweating profusely over the anvil. It is exhausting work.\n"
                f"*** You earned {shift_pay} silver and 1 Strength! (Total silver: {player['silver']}, Total strength: {player['strength']}) ***"
            )
            
            if player["blacksmith_shifts_completed"] % 5 == 0:
                player["strength"] += 1
                log += f"\n\n*** The heavy labor has hardened your muscles! (+1 Strength, Total: {player['strength']}) ***"
                
            if player["reputation"] > 0:
                new_shifts = player["blacksmith_shifts_completed"]
                if new_shifts == 5:
                    player["skills"].append("junior apprentice blacksmith")
                    player["reputation"] += 1
                    log += "\n*** You are now a Junior Apprentice Blacksmith! (+1 Reputation) ***\n*** Your pay has increased to 20 silver per shift! ***"
                elif new_shifts == 10:
                    if "junior apprentice blacksmith" in player["skills"]: player["skills"].remove("junior apprentice blacksmith")
                    player["skills"].append("apprentice blacksmith")
                    player["reputation"] += 1
                    log += "\n*** You are now a full Apprentice Blacksmith! (+1 Reputation) ***\n*** Your pay has increased to 25 silver per shift! ***"
                elif new_shifts == 25:
                    if "apprentice blacksmith" in player["skills"]: player["skills"].remove("apprentice blacksmith")
                    player["skills"].extend(["master blacksmith", "forge"])
                    player["reputation"] += 2
                    log += "\n*** You have mastered the forge and become a Master Blacksmith! (+2 Reputation) ***\n*** You have learned the 'forge' skill! ***\n*** Your pay has increased to 30 silver per shift! ***"
                    
            return player, log, "MAIN"

    # --- RETURN FROM TASK LOGIC ---
    if choice == "Return from Task":
        task = player.get("active_blacksmith_task")
        
        if task == "deliver_goods":
            rem_items = [i for i in ["crate of horseshoes", "bundle of halberds", "custom breastplate"] if i in player["inventory"]]
            if rem_items:
                return player, f"\"You aren't done! You still have {len(rem_items)} deliveries to make!\"", "MAIN"
            
            player["active_blacksmith_task"] = None
            player["blacksmith_shifts_completed"] += 1
            player["current_tenure"] += 1
            player = mark_shift_completed(player)
            player["strength"] += 1

            deadline = player.get("blacksmith_task_deadline", 999999)
            if player["total_game_minutes"] > deadline:
                player["silver"] += 5
                late_note = "\n\"You took far too long! The clients complained, so I'm docking 10 silver from your shift pay!\" (+5 Silver instead of 15)"
            else:
                player["silver"] += 15
                late_note = ""

            player, _ = advance_time(120, player)
            
            log = (
                f"Lovejoy nods approvingly. \"You didn't collapse. Good.\"{late_note}\n"
                "\"Rest up. Next shift, I'll teach you how to manage the furnace.\"\n\n"
                f"*** Shift Completed! (+1 Strength, Total: {player['strength']} | Silver: {player['silver']}) ***\n\n"
                "The Blacksmith wipes their brow and gestures outside.\n"
                "\"If you haven't got a bed yet, head to the Dog and Duck Pub.\"\n"
                "\"A room is 2 silver. You'll need proper rest if you're going to survive the forge.\"\n"
                "\"Tell them that I sent you.\""
            )
            return player, log, "MAIN"
            
        if task == "report_forge_success":
            player["active_blacksmith_task"] = None
            player["blacksmith_shifts_completed"] += 1
            player["current_tenure"] += 1
            player = mark_shift_completed(player)
            player["silver"] += 20
            player, _ = advance_time(300, player)
            
            mistakes = player["forge_mistakes"]
            if mistakes == 0:
                player["reputation"] += 3
                player["strength"] += 2
                player["inventory"].append("masterwork steel longsword")
                log = (
                    "Lovejoy lifts the cooling blade with the tongs, inspecting the edge in the light of the fire.\n"
                    "His usual scowl vanishes, replaced by a look of sheer disbelief.\n"
                    "\"This... this is flawless. Not a single imperfection in the grain. I haven't seen a temper this clean in decades.\"\n"
                    "He turns to you, eyes wide. \"With skills like this, you could become the greatest blacksmith in all of Dtessera Terra... and the lands beyond.\"\n"
                    "He thrusts the hilt toward you. \"Take it. I am not worthy to sell a blade I did not forge.\"\n\n"
                    "*** PERFECT FORGE! Shift Completed (+3 Reputation, +2 Strength, 20 Silver) ***\n"
                    "*** You received the Masterwork Steel Longsword! ***"
                )
            else:
                player["reputation"] += 1
                player["strength"] += 1
                quality = "decent" if mistakes == 1 else "usable" if mistakes == 2 else "flawed but salvageable"
                log = (
                    f"Lovejoy inspects the blade. \"Hmm. It is {quality}. You made a few mistakes, but the steel will hold an edge.\"\n"
                    "\"You have potential, apprentice. Take your wages and rest.\"\n\n"
                    "*** Shift Completed! (+1 Reputation, +1 Strength, 20 Silver) ***"
                )
            return player, log, "MAIN"

        if task == "report_forge_fail":
            player["active_blacksmith_task"] = None
            player["blacksmith_shifts_completed"] += 1
            player = mark_shift_completed(player)
            player["reputation"] -= 1
            player, _ = advance_time(120, player)
            fine = min(player["silver"], 15)
            player["silver"] -= fine
            
            log = (
                "Lovejoy violently shoves you aside with his heavy leather apron.\n"
                "\"You completely ruined the temper! The steel is brittle and useless!\"\n"
                "\"Get out of my forge and don't come back today!\"\n"
                f"Lovejoy deducts {fine} silver from your purse to pay for the ruined steel ingot and wasted coal!\n\n"
                f"*** Shift Failed! (-1 Reputation, -{fine} Silver, No Pay) ***"
            )
            return player, log, "MAIN"

        if task == "prepare_drill_parts":
            return player, "\"Do you have the Package of Drill Parts from the Post Office and the Leather from the Commissary? I didn't think so. Keep gathering.\"", "MAIN"

        if task == "report_shift_3":
            player["active_blacksmith_task"] = None
            player["blacksmith_shifts_completed"] += 1
            player["current_tenure"] += 1
            player = mark_shift_completed(player)
            player["silver"] += 30
            player["strength"] += 1
            player, _ = advance_time(120, player)
            
            player["inventory"].remove("masonry drill")
            modify_faction(player, "faction_wallmakers", 2)
            
            log = (
                "Lovejoy inspects the heavy drill, turning the crank. It is completely silent.\n"
                "\"Hmph. Good work. Wellspring will be pleased.\"\n"
                "Wellspring arrives shortly after and snatches the tool. \"Excellent. We'll put this to good use on the... structural tests.\"\n"
                "Wellspring leaves behind a hefty pouch of coin.\n\n"
                "*** Shift Completed! You earned 30 silver! (+1 Strength, +2 Wallmakers Faction) ***"
            )
            return player, log, "MAIN"

        if task == "mercenary_duel":
            return player, "\"I have nothing for you until this matter is settled. Meet him at the Grazing Field tomorrow morning. Don't lose.\"", "MAIN"

        if task == "stables_fire_rescue":
            if not player.get("fire_extinguished"):
                return player, "\"What are you doing here?! The Stables are burning! Put it out!\"", "MAIN"
            if "hidden secret ledger" not in player["inventory"]:
                return player, "\"You put out the fire, but what about Lightfoot? Did he have the coin or a ledger?\"", "MAIN"
                
            player["active_blacksmith_task"] = None
            player["blacksmith_shifts_completed"] += 1
            player["current_tenure"] += 1
            player = mark_shift_completed(player)
            player["silver"] += 50
            player["reputation"] += 5
            player["strength"] += 2
            player["faction_wallmakers"] = max(-10, modify_faction(player, "faction_wallmakers", -5))
            
            player["inventory"].remove("hidden secret ledger")
            db.npc_database["head hostler"]["location"] = None
            
            if "master blacksmith" not in player["skills"]:
                player["skills"].extend(["master blacksmith", "forge"])
                
            player, _ = advance_time(120, player)
            
            log = (
                "You slam the secret ledger onto the anvil and tell Lovejoy about the Wallmakers' arson.\n"
                "Lovejoy's eyes narrow to dangerous slits as he reads the true accounts.\n"
                "\"They tried to burn Lightfoot alive to cover their extortions? And they thought I would supply them?\"\n"
                "He takes a heavy cleaver and cleanly chops the Wallmakers' new contract in half.\n"
                "\"You're no longer an apprentice, Noburu. You are a Master Blacksmith. This forge is yours as much as mine.\"\n\n"
                "*** Shift Completed! You mastered the Blacksmith career! (+5 Reputation, +2 Strength, -5 Wallmakers Faction, 50 Silver) ***"
            )
            return player, log, "MAIN"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# THE FURIOUS MERCENARY (GRAZING FIELD DUEL)
# -------------------------------------------------------------------------
def get_mercenary_options(player):
    return ["Start Duel", "Flee", "Leave"]

def resolve_mercenary(choice, player):
    if choice == "Leave":
        return player, "You step back. The mercenary glares at you, waiting.", "MAIN"
    if choice == "Flee":
        player["active_blacksmith_task"] = None
        db.npc_database["mercenary"]["location"] = None
        player["reputation"] -= 3
        player["blacksmith_shifts_completed"] += 1
        player = mark_shift_completed(player)
        return player, "You run away like a coward. The town will hear of this! (-3 Reputation)", "MAIN"
    
    if choice == "Start Duel":
        if "duel_day" not in player:
            return player, "\"You're in the wrong place, stranger. Get lost.\"", "MAIN"
        current_day = (player["total_game_minutes"] // 1000) + 1
        time_of_day = player["total_game_minutes"] % 1000
        
        if current_day < player["duel_day"] or (current_day == player["duel_day"] and time_of_day < 375):
            return player, "\"It's not time yet. Don't be eager to die.\"", "MAIN"
            
        elif current_day == player["duel_day"] and 375 <= time_of_day <= 475:
            return encounters.trigger_mercenary_duel(player)
            
        else:
            player["active_blacksmith_task"] = None
            db.npc_database["mercenary"]["location"] = None
            player["reputation"] -= 3
            player["blacksmith_shifts_completed"] += 1
            player = mark_shift_completed(player)
            return player, "\"You missed the time! You're a coward!\" he laughs, walking away. (-3 Reputation)", "MAIN"


# -------------------------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------------------------
HANDLERS = {
    "blacksmith": (get_blacksmith_options, resolve_blacksmith),
    "mercenary":  (get_mercenary_options, resolve_mercenary),
}
