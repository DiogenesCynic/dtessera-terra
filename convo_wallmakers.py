import random
import game_data as db
from mechanics import (
    modify_faction, advance_time, handle_sleep_nap, handle_sleep_morning,
    get_time_string, calculate_max_hit, get_eligible_chapter_2_routes,
    can_start_shift, mark_shift_started, mark_shift_completed
)
import encounters
import mini_games

# -------------------------------------------------------------------------
# BARTENDER (GOODTIDINGS)
# -------------------------------------------------------------------------
def get_goodtidings_options(player):
    if player["active_mayor_task"] == "find_hopestill" and not player["hopestill_revealed"]:
        return ["Show Mayor's Seal"]
        
    if player.get("goodtidings_state") == "food":
        return ["Hot Stew (3s)", "Murky Ale (1s)", "Back"]
        
    return ["Rent Room (2s)", "Order Sustenance", "Ask about Hopestill", "Leave"]

def resolve_goodtidings(choice, player):
    if choice == "Leave": 
        return player, "\"Suit yourself.\"", "MAIN"
    if choice == "Back":
        player["goodtidings_state"] = None
        return player, "You step back from the bar.", "NPC_DIALOGUE"

    if choice == "Show Mayor's Seal":
        player["hopestill_revealed"] = True
        return player, "You quietly flash the Mayor's seal and ask where to find Hopestill.\n\"Put that away!\" she hisses, glancing around the room nervously.\n\"He is sitting right over there in the corner. Do what you need to do, but no bloodshed in my tavern.\"\n*** Hopestill has been revealed! ***", "MAIN"

    if choice == "Ask about Hopestill":
        if player["hopestill_revealed"]:
            return player, "\"They're sitting right over there in the corner,\" Goodtidings says, pointing.", "MAIN"
        if "poster" in player["inventory"]:
            player["hopestill_revealed"] = True
            return player, "Goodtidings stops wiping the bar. His eyes narrow. \"Who's asking?\"\nYou hand over the flyer from Fairlight.\nGoodtidings looks at the poster, then nods towards a dark corner of the tavern.\n\"Over there. Keep your voice down.\"\n*** Hopestill has been revealed! ***", "MAIN"
        return player, "Goodtidings stops wiping the bar. His eyes narrow. \"Who's asking?\"\n\"I don't know anyone by that name. Now buy something or get out.\"", "MAIN"

    if choice == "Rent Room (2s)":
        if not player["free_room_used"] and (player["market_sweeper_shifts"] > 0 or player["blacksmith_shifts_completed"] > 0 or player["stable_shifts"] > 0):
            player["free_room_used"] = True
            player, log_sleep = handle_sleep_morning(player)
            player["hunger"] = player["thirst"] = 100
            return player, "You mention to Goodtidings who sent you.\n\"Ah, fair enough. Any friend of theirs is welcome here. First night is on the house!\"\n\n" + log_sleep + "\n\n*** Time passes while you rest... ***\n*** You wake up to a hearty breakfast! (Hunger/Thirst restored) ***", "MAIN"
        elif player["silver"] >= 2:
            player["silver"] -= 2
            player, log_sleep = handle_sleep_morning(player)
            player["hunger"] = player["thirst"] = 100
            return player, "You hand over 2 silver. Goodtidings hands you a key and points to the stairs.\n\n" + log_sleep + "\n\n*** Time passes while you rest... ***\n*** You wake up to a hearty breakfast! (Hunger/Thirst restored) ***", "MAIN"
        return player, f"\"Rooms are 2 silver. You only have {player['silver']}. You can sleep in the dirt outside.\"", "MAIN"

    if choice == "Order Sustenance":
        player["goodtidings_state"] = "food"
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
            return player, "You buy a pint of murky ale and drink it down.\n*** Your thirst is fully satisfied! ***", "NPC_DIALOGUE"
        return player, "\"You don't have enough coin for a drink.\"", "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# HOPESTILL
# -------------------------------------------------------------------------
def get_hopestill_options(player):
    if "muddy master key" in player["inventory"] and not player.get("master_key_copied"):
        return ["Sell Wax Impression of Master Key (30s)", "Leave"]
    # Intercept: Mayor's Task
    if player["active_mayor_task"] == "find_hopestill" and "mayor's seal" in player["inventory"]:
        return ["Show Mayor's Seal"]
        
    # State 1: Angry
    if player.get("hopestill_angry"):
        return ["Defend yourself!"]
        
    # State 1.5: Collecting Debt
    if player.get("owes_hopestill") and player["current_building"] == "tavern":
        return ["Pay 7s & Report", "Refuse"]
        
    # State 2: Waiting at the Guild
    if player.get("wallmakers_quest_active"):
        return ["Speak to Wellspring"] if player["current_building"] == "wallmakers' offices" else ["Leave"]
        
    # State 3: Giving the Quest
    if player["reputation"] > 0:
        return ["Leave"]
    return ["Accept Job Offer", "Decline"]

def resolve_hopestill(choice, player):
    player["spoken_to_hopestill"] = True

    if choice in ["Leave", "Decline"]:
        if player["reputation"] > 0 and not player.get("wallmakers_quest_active"):
            return player, "\"Actually... you're a bit too 'respectable' for this gig. I need someone with less... visibility.\"\n\"Come back if your reputation takes a dive.\"", "MAIN"
        if choice == "Decline":
            return player, "\"Your loss. Plenty of other hungry mouths in Murum.\"", "MAIN"
        return player, "You step away.", "MAIN"

    if choice == "Sell Wax Impression of Master Key (30s)":
        player["master_key_copied"] = True
        player["silver"] += 30
        modify_faction(player, "faction_wallmakers", 2)
        player["stealth"] += 1
        player["reputation"] -= 2
        log = (
            "Hopestill's eyes light up with a greedy spark as you show him Godwin's Master Key.\n"
            "He pulls a block of warm beeswax from his coat, presses the iron teeth into it, and hands the original key back to you along with a heavy purse.\n"
            "\"Thirty silver, as promised. Return the original to Godwin—he'll never know why his lockboxes feel lighter next month.\"\n\n"
            "*** You sold a copy of the Master Key! (+30 Silver, +2 Wallmakers Faction, +1 Stealth, -2 Reputation) ***"
        )
        return player, log, "MAIN"
        
    if choice == "Show Mayor's Seal":
        player["active_mayor_task"] = "wallmakers_matinee"
        log = (
            "Hopestill eyes you suspiciously. You flash the Mayor's seal.\n"
            "\"The Mayor? They usually send their lackeys to the Guild, not a public tavern.\"\n"
            "\"Fine. Go to the Wallmakers' Offices. Tell Wellspring that Hopestill vouches for a meeting.\""
        )
        return player, log, "MAIN"

    if choice == "Defend yourself!":
        return encounters.trigger_hopestill_combat(player)

    if choice == "Refuse":
        return player, "Hopestill glares. \"Don't play games with me. Get the money.\"", "MAIN"
        
    if choice == "Pay 7s & Report":
        if player["silver"] >= 7:
            player["silver"] -= 7
            player["owes_hopestill"] = False
            
            report = player.get("surveyor_report")
            if report == "failed_break_in":
                if not player.get("wallmaker_double_agent"):
                    modify_faction(player, "faction_wallmakers", 1)
                log = (
                    "Hopestill's eyes narrow as you describe the hollow stones and the snapped prybar tip.\n"
                    "\"Some amateur crew tried to muscle in on our wall last night and botched it.\"\n"
                    "He leans in close. \"Listen carefully. Tomorrow, Wellspring will order you to brick up that breach.\"\n"
                    "\"Don't seal it solid. Leave a hidden cavity inside the masonry so we can use it for our own smuggling run.\""
                )
            elif report == "breach_rigged":
                if not player.get("wallmaker_double_agent"):
                    modify_faction(player, "faction_wallmakers", 1)
                log = (
                    "Hopestill grins darkly as you describe the U-Hollow core hidden behind the Y-Keystone—and his eyes light up when you mention the Smuggler's Cipher.\n"
                    "\"So the fools who snapped their prybar left their dead-drop cipher in the rubble! Keep that cipher safe in your pack.\"\n"
                    "\"Once we sort out the Guard's blind spots tomorrow (Shift 3), you'll use that cipher to claim the contraband they abandoned on the ramparts (Shift 4)!\""
                )
            elif report == "damage_ledger":
                if not player.get("wallmaker_double_agent"):
                    modify_faction(player, "faction_wallmakers", 1)
                route = player.get("sabotaged_route", "through")
                if route == "under":
                    route_msg = "\"You buried the Sluice Gate report? Ha! That Rusted Grate gives us an 'Under the Wall' tunnel right through the culvert!\""
                elif route == "over":
                    route_msg = "\"You hid the North Tower report? Brilliant! That Loose Merlon gives us an unguarded 'Over the Wall' rope drop!\""
                else:
                    route_msg = "\"Kept the ledger clean, eh? No matter—we still have the hollow stone cavity you built into the East Wall.\""

                log = (
                    f"You hand Hopestill his 7 silver and explain how you organized the surveyors' damage board.\n{route_msg}\n"
                    "He taps his nose. \"Tomorrow (Shift 4) is the big preparation. Wellspring will send you up the secret stairs inside the wall. "
                    "Use that Smuggler's Cipher from the breach to locate the abandoned contraband cache on the upper parapet!\""
                )
            elif report == "parapet_cache":
                if not player.get("wallmaker_double_agent"):
                    modify_faction(player, "faction_wallmakers", 2)
                log = (
                    "You slide 7 silver across the table and flash a corner of the Contraband Silk Cache tucked inside your coat.\n"
                    "Hopestill lets out a low, triumphant whistle.\n"
                    "\"Unstamped Parvus silk—worth a king's ransom! Hold onto that parcel until tomorrow.\"\n"
                    "\"On your final shift (Shift 5), Wellspring will send you to chisel the courtyard milestone. "
                    "Our outside contact, 'X', will be waiting nearby. Tap the mason's code on the stone to arrange the handoff—and move that silk through the wall!\""
                )
            elif report == "smuggle_complete":
                if player.get("smuggle_clean_success"):
                    player["faction_wallmakers"] = min(10, modify_faction(player, "faction_wallmakers", 3))
                    log = (
                        "Hopestill raises a tankard in salute as you toss his 7 silver onto the table.\n"
                        "\"The Parvus silk is already in our cellars, and Wealdhere's guards are still chasing shadows!\"\n"
                        "\"You are officially Inner Circle now, friend. Any time you want steady surveyor work on the walls, Wellspring's door is open.\""
                    )
                else:
                    log = (
                        "Hopestill scowls as you hand over his 7 silver and explain how the Watch ambushed the transfer.\n"
                        "\"We lost half the silk because you left a trail of sloppy mistakes across four days of work!\"\n"
                        "\"Be grateful 'X' didn't rat you out. Keep your head down if you want to keep working for the Guild.\""
                    )
            elif report == "schedule":
                log = "\"Good to know. We will need to observe before we act.\""
            elif report == "delivery":
                log = "\"Someone is working our turf. We'll teach them a lesson.\""
            elif report == "staffing":
                log = "\"This feels like an opportunity too good to miss.\""
            elif report == "rat":
                log = "\"Let us pause operations till this blows over.\""
            elif report == "damage":
                log = "\"This needs investigating further. Thanks for the heads up.\""
            else:
                log = "\"Keep your ears open next time. See Wellspring tomorrow.\""

            player["surveyor_report"] = None
            return player, f"You pay 7 silver and report your findings.\n{log}", "MAIN"

        return player, f"\"You only have {player['silver']} silver! Did you drink my cut?\"", "MAIN"
    
    if choice == "Speak to Wellspring":
        current_day = (player["total_game_minutes"] // 1000) + 1
        time_of_day = player["total_game_minutes"] % 1000
        
        if current_day == player["wallmakers_meeting_day"] and time_of_day < 500:
            log = (
                "Hopestill nods in approval. \"You're on time. Good.\"\n"
                "He waves over a stern-looking figure. \"This is Wellspring, the Guild Foreman.\"\n\n"
            )
            if player["reputation"] < 1:
                log += (
                    "Wellspring looks you up and down. \"We need someone to walk the wall, check for damage, and... listen to the guards. 20 silver a day.\"\n"
                    "Hopestill interjects, \"But 7 of that comes to me. After every shift, you report back to me at the Tavern with my cut and what you heard.\"\n\n"
                )
                if player["current_job"] is None:
                    player["current_job"] = "wall surveyor"
                    player["current_tenure"] = 0
                    player["wallmakers_quest_active"] = False
                    db.npc_database["hopestill"]["location"] = "tavern"
                    log += "\"You start immediately,\" Wellspring says.\n*** You are now employed as a Wall Surveyor! ***"
                else:
                    log += f"\"But I see you already work for the {player['current_job']}. Resign from that first, then speak to Wellspring to start your shifts.\""
            else:
                player["wallmakers_quest_active"] = False
                player["hopestill_angry"] = True
                db.npc_database["hopestill"]["location"] = "tavern"
                player["faction_wallmakers"] = max(-10, modify_faction(player, "faction_wallmakers", -5))
                log += (
                    "Wellspring scoffs. \"They're too well-known. We need discretion.\"\n"
                    "Hopestill scowls at you. \"You made me look like a fool bringing a celebrity here!\"\n"
                    f"*** Your relationship with the Wallmakers has dropped to {player['faction_wallmakers']}! ***"
                )
            return player, log, "MAIN"
            
        elif current_day < player["wallmakers_meeting_day"]:
            return player, "Hopestill looks surprised. \"You're early! The meeting with the Foreman isn't until tomorrow morning.\"\n\"Keep your head down until then.\"", "MAIN"
            
        else:
            player["wallmakers_quest_active"] = False
            player["hopestill_angry"] = True
            db.npc_database["hopestill"]["location"] = "tavern"
            player["faction_wallmakers"] = max(-10, modify_faction(player, "faction_wallmakers", -5))
            log = (
                "Hopestill scowls at you. \"You're late! The meeting was for this morning!\"\n"
                "\"You've made me look like a fool, and the Wallmakers won't forget this.\"\n"
                f"*** Your relationship with the Wallmakers has dropped to {player['faction_wallmakers']}! ***"
            )
            return player, log, "MAIN"

    if choice == "Accept Job Offer":
        current_day = (player["total_game_minutes"] // 1000) + 1
        player["wallmakers_quest_active"] = True
        player["wallmakers_meeting_day"] = current_day + 1
        db.npc_database["hopestill"]["location"] = "wallmakers' offices"
        return player, "\"Good. Meet me at the Wallmakers' Guild tomorrow morning. Don't be late.\"", "MAIN"

    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# WELLSPRING (WALLMAKERS GUILD FOREMAN)
# -------------------------------------------------------------------------
def get_wellspring_options(player):
    if player.get("wallmaker_state") == "shift_6_prompt":
        return ["Proceed with shift", "Hand in notice with immediate effect"]
    if player["active_mayor_task"] == "wallmakers_matinee":
        return ["Deliver Message", "Leave"]
    if player["active_mayor_task"] == "negotiate_coal":
        return ["Promise Mayor's Favor", "Pay for horses (40s)", "Threaten with Mayor's wrath", "Leave"]

    options = []
    if "mayor's incoming post" in player["inventory"] and not player.get("mayor_post_leaked_wall"):
        options.append("Let Wellspring Copy Wall Dispatch (+Wallmakers)")

    if player["current_job"] == "wall surveyor":
        if player.get("active_wallmaker_task"):
            options.append("Return from Task")
        else:
            options.append(f"Start Shift ({player['wall_surveyor_shifts']} Completed)")
            if player["wall_surveyor_shifts"] >= 6 and not player.get("owes_hopestill"):
                options.append("Hand in notice with immediate effect")

    options.append("Leave")
    return options


def resolve_wellspring(choice, player):
    if choice == "Leave":
        return player, "\"I have no business with you. Be on your way.\"", "MAIN"

    if choice == "Let Wellspring Copy Wall Dispatch (+Wallmakers)":
        player["mayor_post_leaked_wall"] = True
        modify_faction(player, "faction_wallmakers", 3)
        player["influence"] = player.get("influence", 0) + 1
        log = (
            "Wellspring carefully steams open the Mayor's incoming masonry-inspection dispatch, copies the figures, and reseals the wax flawlessly.\n"
            "\"A servant with a flexible conscience,\" Wellspring smiles. \"The Guild remembers its friends inside the manor.\"\n"
            "*** (+3 Wallmakers Faction, +1 Influence) ***"
        )
        return player, log, "MAIN"

    if choice == "Hand in notice with immediate effect":
        player["wallmaker_state"] = None
        player["current_job"] = None
        player["current_tenure"] = 0
        player["active_wallmaker_task"] = None
        player["chapter_2_unlocked"] = True
        log = (
            "Wellspring steeples his fingers and gives you a sly, knowing nod.\n"
            "\"You've learned every hollow and shadow of Murum's walls, Noburu. I won't keep you on a surveyor's tether.\"\n"
            "\"Go check the Noticeboard in the Town Hall—someone with your stealth and connections has bigger plays to make.\"\n\n"
            "*** You have handed in your notice! Visit the Noticeboard in the Town Hall to explore new opportunities! ***"
        )
        return player, log, "MAIN"

    if choice == "Proceed with shift":
        player["wallmaker_state"] = None
        player["wallmaker_shift_6_prompted"] = True
        choice = f"Start Shift ({player['wall_surveyor_shifts']} Completed)"

    if choice == "Deliver Message":
        player["active_mayor_task"] = "playhouse_meet"
        log = (
            "Wellspring narrows his eyes. \"Hopestill sent you? And with the Mayor's seal?\"\n"
            "\"I see. The Mayor wants to talk business away from prying eyes. Very well.\"\n"
            "\"Tell Praisegod we will meet the Mayor at the Playhouse during the matinee performance.\"\n"
            "\"My associate will find you there. Don't be late.\""
        )
        return player, log, "MAIN"

    # Coal Negotiation
    if choice in ["Promise Mayor's Favor", "Pay for horses (40s)", "Threaten with Mayor's wrath"]:
        if choice == "Promise Mayor's Favor":
            player["faction_wallmakers"] = min(10, modify_faction(player, "faction_wallmakers", 2))
            log = "\"A favor from the Mayor?\" Wellspring smiles greasily. \"We will hold you to that. The coal will be delivered.\"\n*** You leveraged the Mayor's name! (+2 Wallmakers Faction) ***"
        elif choice == "Pay for horses (40s)":
            if player["silver"] < 40:
                return player, f"\"You don't even have 40 silver! You only have {player['silver']}! Don't waste my time.\"", "MAIN"
            player["silver"] -= 40
            player["reputation"] += 2
            player["faction_wallmakers"] = min(10, modify_faction(player, "faction_wallmakers", 1))
            log = "You slam 40 silver onto the table to cover the shoeing dispute. Wellspring looks surprised, then scoops it up.\n\"Money talks. The coal is yours.\"\n*** You paid from your own pocket! (+2 Reputation, +1 Wallmakers Faction) ***"
        else:
            player["faction_wallmakers"] = max(-10, modify_faction(player, "faction_wallmakers", -5))
            player["reputation"] += 2
            log = "You lean in and promise that the Mayor will have the guard raid this office if the coal isn't released.\nWellspring pales. \"Fine! Take the coal. But we won't forget this insult!\"\n*** You made an enemy of the Wallmakers! (-5 Wallmakers Faction, +2 Reputation) ***"
            
        player["active_mayor_task"] = "return_with_coal"
        player["inventory"].append("sack of coal")
        return player, log, "MAIN"

    # --- STARTING A SHIFT ---
    if choice.startswith("Start Shift"):
        if player.get("owes_hopestill"):
            return player, "\"Hopestill sent word you haven't given him his 7-silver cut. Go to the Tavern first.\"", "MAIN"
        ok, msg = can_start_shift(player)
        if not ok:
            return player, msg, "MAIN"
        player = mark_shift_started(player)

        shifts = player["wall_surveyor_shifts"]

        # --- SHIFT 6 EVALUATION: NOTICEBOARD OR DISMISSAL (GAME OVER) ---
        if shifts == 5 and not player.get("wallmaker_shift_6_prompted"):
            eligible = get_eligible_chapter_2_routes(player)
            if not eligible:
                player["current_job"] = None
                player["current_tenure"] = 0
                log = (
                    "Wellspring closes his ledger with a sharp snap and eyes you coldly.\n"
                    "\"I am afraid that you have failed to reach the level that we expect of a wall surveyor in the time that you have been here. "
                    "We are going to have to let you go. I cannot see you acquiring any further work in Murum. "
                    "You will have to try your luck on the road. I wish you luck.\"\n\n"
                    "*** GAME OVER: You failed to qualify for any Chapter 2 path and have been dismissed from Murum! ***"
                )
                return player, log, "DEAD"

            player["wallmaker_state"] = "shift_6_prompt"
            player["chapter_2_unlocked"] = True
            log = (
                "Wellspring leans across his ledger desk and lowers his voice.\n"
                "\"You've survived five shifts on the walls, Noburu. With your new experience and skills, "
                "there may be new opportunities for you if you look at the Noticeboard in the Town Hall.\"\n"
                "\"Do you want to proceed with your shift today, or hand in your notice with immediate effect?\""
            )
            return player, log, "NPC_DIALOGUE"

        # SHIFT 1 (Index 0): CIRCUMNAVIGATE & INSPECT
        if shifts == 0:
            player["active_wallmaker_task"] = "inspect_perimeter"
            player["wall_sectors_inspected"] = []
            player["shift_1_mistakes"] = 0
            log = (
                "Wellspring hands you a Surveyor's Sounding Hammer, white Mason's Chalk, and an Inspection Ledger.\n"
                "\"Your first duty is to circumnavigate the internal perimeter of Murum Town and sound the masonry at all four cardinal sectors:\"\n"
                "  • North Wall: Outside the Post Office or Dog and Duck Pub\n"
                "  • West Wall: Outside Murum Stables\n"
                "  • South Wall: At the Grazing Field\n"
                "  • East Wall: Outside the Blacksmiths\n"
                "\"Use 'Action -> Gather / Search' at each wall sector to tap the stones, trace any flaws in chalk, record them, and wipe your chalk clean before moving on.\"\n\n"
                "*** SHIFT 1 STARTED: Inspect all 4 Wall Sectors! ***"
            )
            return player, log, "MAIN"

        # SHIFT 2 (shifts == 1): PENTOMINO BREACH REPAIR
        elif shifts == 1:
            player["active_wallmaker_task"] = "repair_breach"
            player["shift_2_mistakes"] = 0
            log = (
                "Wellspring hands you a heavy Masonry Trowel, a hod of wet mortar, and five cut stone blocks.\n"
                "\"Head to the East Wall behind the Blacksmiths and use 'Action -> Gather / Search' to patch that failed break-in before the Watch spots it.\"\n"
                "He lowers his voice. \"Remember what Hopestill told you: set the heavy Granite blocks on the bottom row, build from the bottom up, and place the Hollow U-Core over the central niche [C].\"\n\n"
                "*** SHIFT 2 STARTED: Repair the Breach at the East Wall behind the Blacksmiths! ***"
            )
            return player, log, "MAIN"
        
        # SHIFT 3 (shifts == 2): THE LOST DAMAGE REPORT (4x4x4 LOGIC PUZZLE)
        elif shifts == 2:
            player["active_wallmaker_task"] = "solve_damage_ledger"
            player["shift_3_mistakes"] = 0
            player, mini_log, next_state = mini_games.init_deduction_minigame(player)
            intro = (
                "Wellspring rubs his temples over a chaotic desk covered in wooden chits and ink-stained notes.\n"
                "\"The Overseer's regional damage report is in shambles! Four surveyors—Steadfast, Plumbline, Truelevel, and Hardstone—dropped off their findings without labelling the master board.\"\n"
                "\"Check their cubbies and field notes, deduce which surveyor inspected which Wall Sector and Damage Type, and lock the board in before the Watch demands our copy!\"\n\n"
            )
            return player, intro + mini_log, next_state

        elif shifts == 3:
            player["active_wallmaker_task"] = "walk_secret_stairs"
            player["shift_4_mistakes"] = 0
            log = (
                "Wellspring glances out the sash window, then presses a heavy Brass Postern Key and a Shuttered Mason's Lantern into your hand.\n"
                "\"Today you ascend the internal wall stairs and walk the upper ramparts. The secret postern door is built into the South-East Wall right outside the Murum Tavern.\"\n"
                "\"Use 'Action -> Gather / Search' outside the Tavern to enter the stairwell. Keep your lantern shuttered when passing arrow slits, and check the parapet merlons using that cipher you found!\"\n\n"
                "*** SHIFT 4 STARTED: Go outside the Murum Tavern and use 'Action -> Gather / Search'! ***"
            )
            return player, log, "MAIN"

        elif shifts == 4:
            player["active_wallmaker_task"] = "smuggle_silk"
            player["shift_5_mistakes"] = 0
            log = (
                "Wellspring locks the office door and hands you a Mason's Point Chisel.\n"
                "\"This is it—Shift 5. Take the Contraband Silk Cache to the weathered milestone outside Town Hall and use 'Action -> Gather / Search'.\"\n"
                "\"Our outside courier 'X' is waiting by the cobnut trees. Tap the 4-beat Mason's Code (Light, Heavy, Light, Heavy) when no guards are in earshot, choose your smuggling route, and move that silk across the wall!\"\n\n"
                "*** SHIFT 5 STARTED: Meet 'X' outside Town Hall using 'Action -> Gather / Search'! ***"
            )
            return player, log, "MAIN"

        # Fallback for later shifts
        player["silver"] += 20
        player, _ = advance_time(300, player)
        player = mark_shift_completed(player)
        player["wall_surveyor_shifts"] += 1
        player["current_tenure"] += 1
        player["owes_hopestill"] = True

        log = (
            "\"Take this clipboard. Walk the perimeter, note the structural damage, and keep your ears open.\"\n"
            "You spend the next three hours walking the high walls of Murum. It is quiet, stealthy work.\n"
            f"*** You earned 20 silver! (Total: {player['silver']}) ***\n"
        )
        
        base_chance = 0.25
        final_chance = base_chance * (1 + (player["stealth"] * 0.2))
        
        if random.random() < final_chance:
            report_roll = random.randint(1, 10)
            if report_roll <= 3:
                player["surveyor_report"] = "schedule"
                log += "\n*** You overheard the guards discussing a change in the patrol schedule! ***"
            elif report_roll == 4:
                player["surveyor_report"] = "delivery"
                log += "\n*** You overheard whispers of a black market goods delivery! ***"
            elif report_roll <= 7:
                player["surveyor_report"] = "staffing"
                log += "\n*** You noticed severe short staffing on the eastern watchtowers! ***"
            elif report_roll == 8:
                player["surveyor_report"] = "rat"
                log += "\n*** You heard the captain order a tightening of security due to a suspected rat! ***"
            else:
                player["surveyor_report"] = "damage"
                log += "\n*** You catalogued major structural damage that the guards are trying to hide! ***"
        else:
            player["surveyor_report"] = None
            log += "\nYour shift was quiet. You did not overhear anything of note today."

        if player["wall_surveyor_shifts"] >= 5:
            player["stealth"] += 1
            log += f"\n*** Walking the walls unseen has honed your skills! (+1 Stealth, Total: {player['stealth']}) ***"
            
        if random.randint(1, 10) == 1:
            player["reputation"] -= 1
            log += f"\n*** A guard catches you lingering and acting suspiciously! (-1 Reputation, Total: {player['reputation']}) ***"
            if player["reputation"] < 0:
                log += "\n*** You feel a chill run down your spine. The guard patrols will be watching for you. ***"
            
        if player["wall_surveyor_shifts"] == 10:
            modify_faction(player, "faction_wallmakers", 2)
            log += f"\n*** You are considered a reliable operative. (+2 Wallmakers Faction, Total: {player['faction_wallmakers']}) ***"
        elif player["wall_surveyor_shifts"] == 15:
            modify_faction(player, "faction_wallmakers", 3)
            log += f"\n*** You continue to climb the ranks of the Wallmakers. (+3 Wallmakers Faction, Total: {player['faction_wallmakers']}) ***"
        elif player["wall_surveyor_shifts"] == 25:
            modify_faction(player, "faction_wallmakers", 3)
            log += f"\n*** You are an inner circle member of the Wallmakers. (+3 Wallmakers Faction, Total: {player['faction_wallmakers']}) ***"
            
        return player, log, "MAIN"

    # --- RETURNING FROM SHIFT TASK ---
    if choice == "Return from Task":
        task = player.get("active_wallmaker_task")

        if task == "inspect_perimeter":
            done = player.get("wall_sectors_inspected", [])
            if len(done) < 4:
                missing = [s.title() for s in ["north", "west", "south", "east"] if s not in done]
                return player, f"\"You haven't finished your perimeter circuit! You still need to inspect: {', '.join(missing)}.\"", "MAIN"

            player["active_wallmaker_task"] = None
            player["silver"] += 20
            player["stealth"] += 1
            player, _ = advance_time(300, player)
            player = mark_shift_completed(player)
            player["wall_surveyor_shifts"] += 1
            player["current_tenure"] += 1
            player["owes_hopestill"] = True
            player["surveyor_report"] = "failed_break_in"
            player["reported_shift_1_to_guard"] = False

            log = (
                "You hand Wellspring your ledger and whisper about the hollow breach and snapped prybar tip on the final wall.\n"
                "Wellspring pales, quickly shutting the office door.\n"
                "\"Fools! Someone tried to break through the town wall last night without Guild sanction!\"\n"
                "\"If Captain Wealdhere's patrols discover that breach before we patch it, the Watch will lock down the whole perimeter.\"\n"
                "\"Take your 20 silver wage. Deliver Hopestill's 7-silver cut and your report at the Tavern posthaste.\"\n\n"
                f"*** SHIFT 1 COMPLETE! (+20 Silver, +1 Stealth, Total Silver: {player['silver']}, Total Stealth: {player['stealth']}) ***\n"
                "*** Report to Hopestill at the Tavern — or visit Captain Wealdhere at the Guard House first to become a Double Agent! ***"
            )
            return player, log, "MAIN"

        elif task == "repair_breach":
            return player, "\"You haven't sealed the breach yet! Go to the East Wall behind the Blacksmiths and use 'Action -> Gather / Search'.\"", "MAIN"

        elif task == "report_breach_repair":
            player["active_wallmaker_task"] = None
            player["silver"] += 20
            player["stealth"] += 1
            player, _ = advance_time(300, player)
            player = mark_shift_completed(player)
            player["wall_surveyor_shifts"] += 1
            player["current_tenure"] += 1
            player["owes_hopestill"] = True
            player["surveyor_report"] = "breach_rigged"
            player["reported_shift_2_to_guard"] = False

            log = (
                "You return your masonry tools to Wellspring and confirm the East Wall breach is sealed with the hollow core tucked inside.\n"
                "\"Clean work,\" Wellspring mutters, counting out 20 silver coins. \"Take Hopestill's 7-silver cut to the Tavern and tell him the stone is set.\"\n\n"
                f"*** SHIFT 2 COMPLETE! (+20 Silver, +1 Stealth, Total Silver: {player['silver']}, Total Stealth: {player['stealth']}) ***\n"
                "*** Report to Hopestill at the Tavern — or visit Captain Wealdhere at the Guard House first if you are working undercover! ***"
            )
            return player, log, "MAIN"

        elif task == "solve_damage_ledger":
            return mini_games.init_deduction_minigame(player)

        elif task == "report_damage_ledger":
            player["active_wallmaker_task"] = None
            player["silver"] += 20
            player["stealth"] += 1
            player, _ = advance_time(300, player)
            player = mark_shift_completed(player)
            player["wall_surveyor_shifts"] += 1
            player["current_tenure"] += 1
            player["owes_hopestill"] = True
            player["surveyor_report"] = "damage_ledger"
            player["reported_shift_3_to_guard"] = False

            log = (
                "Wellspring inspects the completed 4x4x4 ledger board and nods in relief.\n"
                "\"Order out of chaos. I'll dispatch the repair crews according to these exact chits.\"\n"
                "He counts out 20 silver into your palm. \"Take Hopestill's 7-silver cut to the Tavern and let him know which sectors are being left alone.\"\n\n"
                f"*** SHIFT 3 COMPLETE! (+20 Silver, +1 Stealth, Total Silver: {player['silver']}, Total Stealth: {player['stealth']}) ***\n"
                "*** Report to Hopestill at the Tavern — or visit Captain Wealdhere at the Guard House first if you are working undercover! ***"
            )
            return player, log, "MAIN"

        elif task == "walk_secret_stairs":
            return player, "\"You haven't walked the upper parapet yet! Go outside the Murum Tavern and use 'Action -> Gather / Search' to enter the secret stairs.\"", "MAIN"

        elif task == "report_parapet_walk":
            player["active_wallmaker_task"] = None
            player["silver"] += 20
            player, _ = advance_time(300, player)
            player = mark_shift_completed(player)
            player["wall_surveyor_shifts"] += 1
            player["current_tenure"] += 1
            player["owes_hopestill"] = True
            player["surveyor_report"] = "parapet_cache"
            player["reported_shift_4_to_guard"] = False
            if player.get("shift_4_mistakes", 0) == 0:
                player["stealth"] += 2
                skill_msg = "\n*** Sneaking through the secret wall stairs without error honed your instincts! (+2 Stealth) ***"
            else:
                player["stealth"] += 1
                skill_msg = "\n*** Sneaking through the secret wall stairs successfully honed your instincts! (+1 Stealth) ***"
            
            if "climb" not in player["skills"]:
                player["skills"].append("climb")
                skill_msg += "\n*** Navigating the secret stairs and high battlements has taught you the 'climb' skill! ***"

            log = (
                "You return the Brass Postern Key to Wellspring and report that the upper battlements are clear—while keeping the Contraband Silk Cache hidden in your pack.\n"
                "Wellspring gives you a knowing nod and counts out 20 silver.\n"
                "\"Hopestill is waiting at the Tavern for his 7 silver and word on what you pulled from the parapet dead-drop.\"\n\n"
                f"*** SHIFT 4 COMPLETE! (+20 Silver, Total Silver: {player['silver']}, Total Stealth: {player['stealth']}) ***{skill_msg}\n"
                "*** Report to Hopestill at the Tavern — or bring the Contraband Cache to Captain Wealdhere at the Guard House first so he can mark it for the sting! ***"
            )
            return player, log, "MAIN"

        elif task == "smuggle_silk":
            return player, "\"'X' is waiting by the milestone outside Town Hall! Go there and use 'Action -> Gather / Search' to make contact!\"", "MAIN"

        elif task == "report_smuggle_finale":
            player["active_wallmaker_task"] = None
            player["silver"] += 20
            player, _ = advance_time(300, player)
            player = mark_shift_completed(player)
            player["wall_surveyor_shifts"] += 1
            player["current_tenure"] += 1
            player["owes_hopestill"] = True
            player["surveyor_report"] = "smuggle_complete"

            if player.get("smuggle_clean_success"):
                player["stealth"] += 1
                log = (
                    "Wellspring beams as you step into the office. \"Word already reached me—the silk cleared the wall without a hitch!\"\n"
                    "He counts out your 20 silver shift pay. \"Pay Hopestill his final 7-silver cut at the Tavern. You've earned your place among the master Wallmakers of Murum!\"\n\n"
                    f"*** SHIFT 5 COMPLETE! (+20 Silver, +1 Stealth, Total Silver: {player['silver']}, Total Stealth: {player['stealth']}) ***"
                )
            else:
                log = (
                    "Wellspring winces at your torn coat. \"I heard the Watch whistles near the wall. At least you escaped before Wealdhere clapped you in irons.\"\n"
                    "He hands you your 20 silver wage. \"Go settle up with Hopestill at the Tavern.\"\n\n"
                    f"*** SHIFT 5 COMPLETE! (+20 Silver, Total: {player['silver']}) ***"
                )
            return player, log, "MAIN"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------------------------
HANDLERS = {
    "goodtidings": (get_goodtidings_options, resolve_goodtidings),
    "hopestill":   (get_hopestill_options, resolve_hopestill),
    "wellspring":  (get_wellspring_options, resolve_wellspring),
}
