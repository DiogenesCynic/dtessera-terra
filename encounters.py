"""
encounters.py
-------------
Combat encounter initializers, victory/flee callback hooks, universal 1v1 combat
resolution engine, highway robber compass interrogation, and Lignum Forest schism ambushes.
"""

import random
import game_data as db
import map_data
import companions_engine
import ch2_easter_eggs
from mechanics import (
    calculate_max_hit,
    advance_time,
    mark_shift_completed,
    infect_player,
    modify_faction,
    consume_fresh_food_timestamp,
)


# =========================================================================
# 1. ENCOUNTER INITIALIZERS (Starts the event)
# =========================================================================
# Every active_enemy dict is pure JSON-serializable data so F5/F9 saves work mid-combat.

def trigger_thief_combat(player):
    """Starts combat with the Cornered Cutpurse at the end of Market Shift 5."""
    player["active_enemy"] = {
        "id": "cornered_cutpurse",
        "name": "Cornered Cutpurse",
        "health": 18,
        "flee_damage": 4,
        "attack_min": 2,
        "attack_max": 6,
        "attack_verb": "The Cutpurse lunges with a narrow stiletto dagger, slashing you",
        "defeat_msg": (
            "You knock the dagger from the Cutpurse's hand and pin him to the cobblestones!\n"
            "You unstrap Godwin's Heavy Iron Lockbox from his back as the Town Watch arrives to haul him away.\n"
            "*** You recovered the Market Lockbox! Return to Godwin ('Return from Task') for your promotion! ***"
        ),
        "flee_msg": (
            "You back off as the Cutpurse slashes your arm (-{dmg} Health) and scrambles over the Town Wall with the lockbox!\n"
            "*** Shift Failed! Return to Godwin to report the loss... ***"
        ),
    }
    log = (
        "*** CORNERED AT THE WALL! ***\n\n"
        "Backed against the stone ramparts with nowhere left to run, the Cutpurse draws a gleaming stiletto dagger!"
    )
    return player, log, "COMBAT"


def trigger_wallmaker_brawl(player):
    """Starts combat with the Wallmaker Enforcer during the Market Shift 4 side-quest."""
    player["active_enemy"] = {
        "id": "wallmaker_enforcer",
        "name": "Wallmaker Enforcer",
        "health": 16,
        "flee_damage": 4,
        "attack_min": 2,
        "attack_max": 5,
        "attack_verb": "The Wallmaker Enforcer swings a brass-knuckled fist, hitting you",
        "defeat_msg": (
            "You knock the Wallmaker Enforcer flat onto the cobblestones!\n"
            "The Union worker cheers and clasps your shoulder before slipping away into the crowd.\n"
            "*** You won the brawl! (+3 Union Faction, -3 Wallmakers Faction) ***\n"
            "*** Speak to Godwin ('Return from Task') to collect your shift pay! ***"
        ),
        "flee_msg": (
            "You scramble out of the fray as a heavy punch clips your ear! (-{dmg} Health)\n"
            "The Town Watch storms in to break up the riot, trashing half the market stalls in the process!\n"
            "*** Shift Ruined! (-2 Reputation) ***"
        ),
    }
    log = (
        "*** MARKET BRAWL! ***\n\n"
        "You charge into the fray and tackle the Wallmaker Enforcer off the Union worker!\n"
        "He snarls, raising his brass-knuckled fists to fight you!"
    )
    return player, log, "COMBAT"


def trigger_union_brawl(player):
    """Starts combat with the Union Brawler during the Market Shift 4 side-quest."""
    player["active_enemy"] = {
        "id": "union_brawler",
        "name": "Union Brawler",
        "health": 16,
        "flee_damage": 4,
        "attack_min": 2,
        "attack_max": 5,
        "attack_verb": "The Union Brawler swings a heavy wooden crate-slat, hitting you",
        "defeat_msg": (
            "You wrestle the Union Brawler to the ground until he yields!\n"
            "The Wallmaker Enforcer dusts off his coat and nods coldly in approval before departing.\n"
            "*** You won the brawl! (+3 Wallmakers Faction, -3 Union Faction) ***\n"
            "*** Speak to Godwin ('Return from Task') to collect your shift pay! ***"
        ),
        "flee_msg": (
            "You scramble out of the fray as a swung crate-slat clips your shoulder! (-{dmg} Health)\n"
            "The Town Watch storms in to break up the riot, trashing half the market stalls in the process!\n"
            "*** Shift Ruined! (-2 Reputation) ***"
        ),
    }
    log = (
        "*** MARKET BRAWL! ***\n\n"
        "You charge into the fray and haul the Union Brawler away from the stalls!\n"
        "He turns on you in a blind fury, swinging a heavy wooden slat!"
    )
    return player, log, "COMBAT"


def trigger_mercenary_brawl(player):
    """Starts an unprepared unarmed brawl with Sindeny the Mercenary inside the forge."""
    if player["equipped_weapon"] != "fists":
        player["inventory"].append(player["equipped_weapon"])
        player["equipped_weapon"] = "fists"

    player["active_enemy"] = {
        "id": "mercenary_brawl",
        "name": "Furious Mercenary (Brawl)",
        "health": 25,
        "flee_damage": 5,
        "attack_min": 3,
        "attack_max": 8,
        "attack_verb": "Sindeny lunges with his heavy sword, striking you",
        "defeat_msg": (
            "You beat the mercenary bloody! He collapses on the forge floor.\n"
            "The town guard hears the commotion. Brawling in a shop severely damages your reputation! (-3 Reputation)\n"
            "But Lovejoy is incredibly proud. \"You protected my forge. Take this blade.\"\n"
            "*** Shift Completed! You received 25 Silver, +1 Strength, and a Steel Longsword! ***"
        ),
        "flee_msg": (
            "You turn and sprint away! The mercenary laughs at your cowardice and smashes Lovejoy's quench-trough on his way out.\n"
            "You take a brutal slash to the back (-{dmg} Health) and Lovejoy docks 20 silver for shop repairs!\n"
            "*** Shift Failed! (-3 Reputation, -20 Silver) ***"
        ),
    }
    log = (
        "*** SHOP BRAWL! ***\n\n"
        "Caught entirely off guard, you drop what you were doing to protect your master.\n"
        "You have no weapon equipped! The mercenary swings his chipped blade at you!"
    )
    return player, log, "COMBAT"


def trigger_mercenary_duel(player):
    """Starts the prepared morning duel with Sindeny the Mercenary at the Grazing Field."""
    player["active_enemy"] = {
        "id": "mercenary_duel",
        "name": "Furious Mercenary (Duel)",
        "health": 25,
        "flee_damage": 5,
        "attack_min": 3,
        "attack_max": 8,
        "attack_verb": "Sindeny lunges with his heavy sword, striking you",
        "defeat_msg": (
            "You best the mercenary in a fair duel! He yields, humiliated.\n"
            "The town respects your honor and strength. (+1 Reputation)\n"
            "Lovejoy meets you at the edge of the field. \"You did well. Take this blade.\"\n"
            "*** Duel Completed! You received 25 Silver, +1 Strength, and a Steel Longsword! ***"
        ),
        "flee_msg": (
            "You turn and sprint away! The mercenary laughs at your cowardice.\n"
            "You take a brutal slash to the back (-{dmg} Health). The town will hear of this shame!\n"
            "*** Shift Failed! (-3 Reputation) ***"
        ),
    }
    log = (
        "*** FORMAL DUEL! ***\n\n"
        "You face the mercenary on the open grass. The morning air is crisp.\n"
        "\"Let's see what you're made of!\" he yells, charging at you!"
    )
    return player, log, "COMBAT"


def trigger_hopestill_combat(player):
    """Starts combat with Hopestill at the Murum Tavern after a missed Wallmakers meeting."""
    player["hopestill_angry"] = False
    player["active_enemy"] = {
        "id": "hopestill",
        "name": "Hopestill",
        "health": 15,
        "flee_damage": 5,
        "attack_min": 2,
        "attack_max": 5,
        "attack_verb": "Hopestill slashes at you with his jagged blade, hitting you",
        "defeat_msg": "Hopestill crashes over a table and slumps to the tavern floor, unconscious!",
        "flee_msg": "You scramble backward and bolt out of the tavern! Hopestill's jagged blade slices your arm as you flee! (-{dmg} Health)",
    }
    log = (
        "Hopestill stands up, kicking his stool aside. He draws a jagged blade.\n"
        "\"You didn't show up. You made me look like a fool to the Wallmakers!\"\n"
        "\"I'm taking my finder's fee out of your hide!\""
    )
    return player, log, "COMBAT"


def trigger_robber_encounter(player):
    """Starts a Highway Robbers ambush along the New Road."""
    player["active_enemy"] = {
        "id": "robbers",
        "name": "Highway Robbers",
        "health": 10,
        "flee_damage": 2,
        "attack_min": 1,
        "attack_max": 4,
        "attack_verb": "The robbers swing their crude weapons, hitting you",
        "defeat_msg": "The robbers are overwhelmed by your ferocity and scatter into the woods!",
        "flee_msg": "You turn and sprint down the road as fast as you can. A thrown rock grazes your shoulder! (-{dmg} Health)",
    }
    log = (
        "*** AMBUSH! ***\n\n"
        "Three people step out from the tall grass, they look desperate and cling to their makeshift weapons with white knuckles. They have blocked your path.\n\n"
        "The leader of these highway robbers steps forward and speaks, 'There is a toll for travelling this road that all foolish enough to do so must pay.\n"
        "We care naught for your wellbeing. There will be no bargaining here.'"
    )
    return player, log, "MENU_ROBBER"


def trigger_thug_encounter(player):
    """Starts an ambush by Wallmaker Hired Thugs in town."""
    player["active_enemy"] = {
        "id": "thugs",
        "name": "Hired Thugs",
        "health": 15,
        "flee_damage": 3,
        "attack_min": 2,
        "attack_max": 6,
        "attack_verb": "The thugs bash you with their clubs, hitting you",
        "defeat_msg": "The thugs are beaten and flee into the labyrinth of town streets!",
        "flee_msg": "You turn and sprint down the street! A thrown brick catches you in the back! (-{dmg} Health)",
    }
    log = (
        "*** AMBUSH! ***\n\n"
        "Two heavy-set men step out from the shadows of an alleyway.\n"
        "\"Wellspring sends his regards, rat,\" one of them sneers, drawing a heavy iron club."
    )
    return player, log, "MENU_THUG"


def trigger_guard_encounter(player):
    """Starts a Town Guard arrest interception when player reputation is negative."""
    player["active_enemy"] = {
        "id": "guard",
        "name": "Murum Guard",
        "health": 20,
        "flee_damage": 0, # Calculated dynamically in _on_flee_guard
        "attack_min": 2,
        "attack_max": 6,
        "attack_verb": "The guard slashes you with their halberd, hitting you",
        "defeat_msg": "The guard collapses! You flee into the labyrinth of town streets before reinforcements arrive.",
        "flee_msg": "", # Handled in _on_flee_guard
    }
    log = (
        "*** HALT, THIEF! ***\n\n"
        "A heavily armored Murum Guard steps into your path, halberd lowered.\n"
        "\"By order of the Castellan, you are under arrest!\""
    )
    return player, log, "MENU_GUARD"


def trigger_territory_encounter(player, owner):
    """Triggered when a player trespasses off-road into a hostile faction's territory."""
    player["active_enemy"] = {
        "id": f"territory_{owner.lower()}",
        "name": f"{owner} Territory Outriders",
        "health": 16,
        "flee_damage": 3,
        "attack_min": 2,
        "attack_max": 6,
        "attack_verb": f"The {owner} outriders strike you",
        "defeat_msg": f"You fight off the {owner} patrol and force your way through the contested turf!",
        "flee_msg": f"You retreat from the {owner} patrol under a hail of blows! (-{{dmg}} Health)",
    }
    log = (
        f"*** TERRITORY INTERCEPTION ({owner.upper()} TURF)! ***\n\n"
        f"Armed {owner} outriders surround you off the main road!\n"
        f"\"Your kind isn't welcome on {owner} land!\""
    )
    return player, log, "MENU_THUG"


def trigger_casino_enforcer_combat(player, reason="cheating"):
    """Starts combat with Justwrath, the House of Games Pit Boss (for cheating or defaulted loan)."""
    if player.get("current_building") in ("casino", "the house of games", "house of games"):
        player["equipped_weapon"] = "fists"

    if reason == "cheating":
        intro = (
            "*** CAUGHT WITH SHAVED BONES! ***\n\n"
            "Stickman Fortunesmile slams his rattan stick down on your wrist! \"Weighted dice at my table?! Justwrath!\"\n"
            "Your weighted dice and table bets are swept away as a towering, scar-faced bruiser vaults the mahogany rail, cracking his brass-knuckled fists.\n"
            "Because the cloakroom holds all weapons inside The House of Games, you are completely UNARMED!"
        )
    else:
        intro = (
            "*** DEFAULTED HOUSE MARKER! ***\n\n"
            "A massive shadow falls across your path. Justwrath, the House of Games Pit Enforcer, steps forward holding your overdue 60-Silver marker.\n"
            "\"Three days are up, deadbeat. Fortunesmile says if you don't have the silver, I take it out of your ribs!\""
        )

    player["active_enemy"] = {
        "id": "casino_enforcer",
        "name": "Justwrath (House Pit Boss)",
        "health": 28,
        "flee_damage": 6,
        "attack_min": 4,
        "attack_max": 8,
        "attack_verb": "Justwrath swings a devastating haymaker with his heavy brass knuckles, smashing you",
        "defeat_msg": (
            "Against all odds, you drop the massive Pit Enforcer to one knee!\n"
            "Bloodied and wheezing, Justwrath waves you back. \"Enough! You fight like a cornered badger... Consider us square for today!\""
        ),
        "flee_msg": (
            "You duck a bone-crushing hook, take a glancing blow to the ribs (-{dmg} Health), and bolt out the doors into the winding streets of Murum!"
        ),
    }
    return player, intro, "COMBAT"


def trigger_bandoka_combat(player):
    """Launches combat against Bandoka when unmasked or when ambushing the player."""
    player["bandoka_joined"] = False
    db.npc_database["bandoka"]["location"] = None
    player["active_enemy"] = {
        "id": "bandoka_double_agent",
        "name": "Bandoka (Double Agent)",
        "health": 20,
        "flee_damage": 4,
        "attack_min": 2,
        "attack_max": 6,
        "attack_verb": "Bandoka lunges with a concealed stiletto and lead-weighted staff, striking you",
        "defeat_msg": (
            "You knock the stiletto from Bandoka's hand and pin the double agent to the ground!\n"
            "From their lining, you confiscate **Bandoka's Cipher** and a pouch of **30 silver** before they scramble away into the brush!\n"
            "*** DOUBLE AGENT DEFEATED! (+30 Silver, +Bandoka's Cipher, +2 Reputation) ***"
        ),
        "flee_msg": "You break away from Bandoka's ambush, taking a grazing slash across the shoulder (-{dmg} Health) as Bandoka vanishes into the mist!",
    }
    return (
        player,
        "*** DOUBLE AGENT SHOWDOWN! ***\nBandoka drops their traveller's disguise, drawing a concealed stiletto!",
        "COMBAT",
    )


# =========================================================================
# 2. OUTCOME HANDLERS (Victory & Flee Hooks)
# =========================================================================
def _on_defeat_casino_enforcer(player):
    if player.get("casino_loan_owed", 0) > 0:
        player["casino_loan_owed"] = 0
        player["casino_loan_due_min"] = None
    return player


def _on_flee_casino_enforcer(player):
    if player.get("casino_loan_owed", 0) > 0:
        player["casino_loan_due_min"] = player.get("total_game_minutes", 0) + 1000
    return player, None


def _on_defeat_bandoka(player):
    player["silver"] += 30
    player["reputation"] += 2
    if "bandoka's cipher" not in player["inventory"]:
        player["inventory"].append("bandoka's cipher")
    return player


def _on_defeat_mercenary_brawl(player):
    player["reputation"] -= 3
    player["silver"] += 25
    player["strength"] += 1
    player["inventory"].append("steel longsword")
    player["blacksmith_shifts_completed"] += 1
    player["current_tenure"] += 1
    player = mark_shift_completed(player)
    player, _ = advance_time(120, player)
    return player


def _on_defeat_mercenary_duel(player):
    player["reputation"] += 1
    player["silver"] += 25
    player["strength"] += 1
    player["inventory"].append("steel longsword")
    player["blacksmith_shifts_completed"] += 1
    player["current_tenure"] += 1
    player["active_blacksmith_task"] = None
    db.npc_database["mercenary"]["location"] = None
    player = mark_shift_completed(player)
    player, _ = advance_time(30, player)
    return player


def _on_flee_mercenary(player):
    player["reputation"] -= 3
    if player.get("active_enemy", {}).get("id") == "mercenary_brawl":
        player["silver"] = max(0, player["silver"] - 20)
    player["blacksmith_shifts_completed"] += 1
    player["active_blacksmith_task"] = None
    player = mark_shift_completed(player)
    player, _ = advance_time(30, player)
    db.npc_database["mercenary"]["location"] = None
    return player, None


def _on_flee_guard(player):
    dmg = random.randint(2, 6)
    player["health"] -= dmg
    modify_faction(player, "faction_guard", -2)
    player["reputation"] -= 1
    custom_log = (
        f"You turn and sprint down the winding streets! A crossbow bolt catches you in the shoulder! (-{dmg} Health)\n"
        "*** Fleeing arrest worsens your standing! (-2 Guard Faction, -1 Reputation) ***\n"
        f"Current Health: {player['health']}"
    )
    return player, custom_log


def _on_defeat_wallmaker_enforcer(player):
    modify_faction(player, "faction_union", 3)
    modify_faction(player, "faction_wallmakers", -3)
    player["active_market_task"] = "report_market_shift_4"
    return player


def _on_defeat_union_brawler(player):
    modify_faction(player, "faction_wallmakers", 3)
    modify_faction(player, "faction_union", -3)
    player["active_market_task"] = "report_market_shift_4"
    return player


def _on_flee_market_brawl(player):
    player["reputation"] -= 2
    player["market_sweeper_shifts"] += 1
    player["active_market_task"] = None
    player = mark_shift_completed(player)
    player, _ = advance_time(120, player)
    return player, None


def _on_defeat_cutpurse(player):
    if "market lockbox" not in player["inventory"]:
        player["inventory"].append("market lockbox")
    player["active_market_task"] = "report_market_shift_5_win"
    return player


def _on_flee_cutpurse(player):
    player["active_market_task"] = "report_market_shift_5_fail"
    return player, None


def _on_defeat_vanguard_animals(player):
    modify_faction(player, "faction_vanguardists", -2)
    return player


VICTORY_HANDLERS = {
    "mercenary_brawl": _on_defeat_mercenary_brawl,
    "mercenary_duel": _on_defeat_mercenary_duel,
    "wallmaker_enforcer": _on_defeat_wallmaker_enforcer,
    "union_brawler": _on_defeat_union_brawler,
    "cornered_cutpurse": _on_defeat_cutpurse,
    "casino_enforcer": _on_defeat_casino_enforcer,
    "bandoka_double_agent": _on_defeat_bandoka,
    "vanguard_animals": _on_defeat_vanguard_animals,
}

FLEE_HANDLERS = {
    "mercenary_brawl": _on_flee_mercenary,
    "mercenary_duel": _on_flee_mercenary,
    "guard": _on_flee_guard,
    "wallmaker_enforcer": _on_flee_market_brawl,
    "union_brawler": _on_flee_market_brawl,
    "cornered_cutpurse": _on_flee_cutpurse,
    "casino_enforcer": _on_flee_casino_enforcer,
}


# =========================================================================
# 3. ENCOUNTER RESOLUTIONS (UI Callbacks)
# =========================================================================
def pay_robber_toll(player):
    """Pays the highwaymen's toll (all silver if > 2s; otherwise triggers combat)."""
    if player["silver"] <= 2:
        log = (
            "You toss your coin purse at their feet.\n"
            f"The leader kicks the dirt. 'Only {player['silver']} silver?! You insult us. Boys, kill them!'"
        )
        return player, log, "COMBAT"

    player["silver"] = 0
    player["active_enemy"] = None
    log = (
        "You toss your coin purse at their feet. They laugh and disappear back into the wilderness.\n"
        "Your pockets are empty, but you are unharmed."
    )
    return player, log, "MAIN"


def bribe_guard(player):
    """Attempts to bribe an arresting Murum Guard for 15 silver."""
    if player["silver"] >= 15:
        player["silver"] -= 15
        player["active_enemy"] = None
        log = (
            "You discreetly hold up a heavy pouch of silver.\n"
            "The guard glances around, snatches the pouch, and steps aside.\n"
            "\"I didn't see anyone,\" they mutter.\n"
            f"*** You bribed the guard! (Remaining Silver: {player['silver']}) ***"
        )
        return player, log, "MAIN"

    dmg = random.randint(2, 5)
    player["health"] -= dmg
    modify_faction(player, "faction_guard", -2)
    player["reputation"] -= 1
    player["active_enemy"] = None
    log = (
        f"The guard scoffs. \"You only have {player['silver']} silver? You insult me!\"\n"
        "The guard swings their halberd at you!\n"
        f"You scramble away in a panic, taking a glancing blow to the ribs! (-{dmg} Health)\n"
        "*** Fleeing arrest worsens your standing! (-2 Guard Faction, -1 Reputation) ***\n"
        f"Current Health: {player['health']}"
    )
    return player, log, "MAIN"


def flee_encounter(player):
    """Flees from the current active enemy, applying parting damage reduced by shield defense."""
    enemy = player["active_enemy"]
    enemy_id = enemy.get("id", enemy["name"])

    if enemy_id in FLEE_HANDLERS:
        player, custom_log = FLEE_HANDLERS[enemy_id](player)
        if custom_log:
            player["active_enemy"] = None
            return player, custom_log, "MAIN"

    dmg = max(1, enemy.get("flee_damage", 2) - db.shield_defense.get(player.get("equipped_shield", "none"), 0))
    player["health"] -= dmg
    flee_template = enemy.get("flee_msg", "You flee the fight, taking a parting blow! (-{dmg} Health)")
    log = f"{flee_template.format(dmg=dmg)}\nCurrent Health: {player['health']}"

    player["active_enemy"] = None
    return player, log, "MAIN"


def start_combat(player):
    """Transitions from an encounter prompt into active combat."""
    if player["active_enemy"].get("id") == "guard":
        modify_faction(player, "faction_guard", -5)
        player["reputation"] -= 2
        log = (
            f"You raise your {player['equipped_weapon']}. The guard blows a whistle and charges!\n"
            "*** You assaulted a town guard! (-5 Guard Faction, -2 Reputation) ***\n\n"
            "Prepare to fight!"
        )
    else:
        log = f"You raise your {player['equipped_weapon']} and prepare to fight!"

    return player, log, "COMBAT"


# =========================================================================
# 4. UNIVERSAL COMBAT ENGINE
# =========================================================================
def combat_round(player):
    from mechanics import (
        calculate_max_hit,
        scale_enemy_for_progression,
        calculate_stat_based_hp_loss,
        recalculate_player_max_health,
    )
    recalculate_player_max_health(player)

    # Lazy-scale enemy on the first round of combat if not already scaled!
    if "escalation_tier" not in player["active_enemy"]:
        player["active_enemy"] = scale_enemy_for_progression(player["active_enemy"], player)

    enemy = player["active_enemy"]
    enemy_id = enemy.get("id", enemy["name"])
    wep = player.get("equipped_weapon", "fists")

    try:
        from crafting_engine import EXOTIC_GEAR_DATABASE
        base_max_hit = db.weapon_max_hit.get(wep) or EXOTIC_GEAR_DATABASE.get(wep, {}).get("damage", 2)
    except ImportError:
        base_max_hit = db.weapon_max_hit.get(wep, 2)

    min_hit, max_hit = calculate_max_hit(base_max_hit, player["strength"], player["health"], player["max_health"])

    # 1. Player attacks (+ Optional Nightshade Blade Poison & Companion Assist!)
    player_dmg = random.randint(min_hit, max_hit)
    poison_note = ""
    if player.get("weapon_poison_charges", 0) > 0:
        player["weapon_poison_charges"] -= 1
        player_dmg += 2
        poison_note = " (+2 Nightshade Poison!)"

    enemy["health"] -= player_dmg
    tier_tag = f" [Tier {enemy.get('escalation_tier', 0)}]" if enemy.get("escalation_tier", 0) > 0 else ""
    log = f"> You strike {enemy['name']}{tier_tag} with your {wep} for {player_dmg} damage!{poison_note}\n"

    # Companion Combat Assist
    comp_mit = 0
    try:
        import companions_engine
        c_dmg, c_heal, comp_mit, c_log = companions_engine.apply_companion_combat_assist(player)
        if c_dmg > 0 and enemy["health"] > 0:
            enemy["health"] -= c_dmg
            log += f"> {c_log}\n"
    except ImportError:
        pass

    # Check if enemy is defeated
    if enemy["health"] <= 0:
        if enemy_id == "robbers" and "compass" not in player["inventory"] and not player.get("robber_compass_obtained"):
            player["active_enemy"] = None
            loc_obj = map_data.world_map.get((player["x"], player["y"]))
            road_name = loc_obj.name if loc_obj else "The New Road"
            log += (
                f"\nThe highwaymen collapse in the dirt! Their leader clutches his bruised ribs, "
                f"pinned at your mercy on the side of {road_name}."
            )
            return player, log, "ROBBER_INTERROGATE"

        if enemy_id in VICTORY_HANDLERS:
            player = VICTORY_HANDLERS[enemy_id](player)

        defeat_msg = enemy.get("defeat_msg", f"You defeated {enemy['name']}!")
        if enemy_id not in VICTORY_HANDLERS and enemy_id not in ["robbers", "bandoka_double_agent"]:
            if any(k in enemy.get("name", "") for k in ("Beast", "Boar", "Wolf")):
                player["inventory"].append("meat ration")
                player["inventory"].append("leather")
                defeat_msg += "\n*** You harvested a Meat Ration and fresh Leather! ***"
            elif any(k in enemy.get("name", "") for k in ("Thugs", "Outriders")):
                coins = random.randint(8, 18) + (enemy.get("escalation_tier", 0) * 3)
                player["silver"] += coins
                player["reputation"] += 1
                defeat_msg += f"\n*** You looted {coins} Silver from their pockets and gained +1 Reputation! ***"

        log += f"\n{defeat_msg}"
        player["active_enemy"] = None
        return player, log, "MAIN"

    # 2. Enemy counterattacks (Mitigated by Player Stats, Armour, Shield & Companion!)
    raw_enemy_dmg = max(1, random.randint(enemy["attack_min"], enemy["attack_max"]) - comp_mit)
    enemy_dmg, mit_note = calculate_stat_based_hp_loss(raw_enemy_dmg, player, enemy.get("name", "Enemy"))

    player["health"] -= enemy_dmg
    attack_verb = enemy.get("attack_verb", f"{enemy['name']} strikes you")

    if enemy_dmg == 0:
        log += f"> {attack_verb} (Raw {raw_enemy_dmg}), but deals **0 damage**! {mit_note} (HP: {player['health']}/{player['max_health']})"
    else:
        log += f"> {attack_verb} for **{enemy_dmg} damage** (Raw {raw_enemy_dmg}){mit_note}! (HP: {player['health']}/{player['max_health']})"

    if enemy_dmg > 0 and player["health"] > 0 and enemy_id in ["cornered_cutpurse", "hopestill", "robbers"] and random.random() < 0.20:
        from mechanics import infect_player
        inf_msg = infect_player(player, "wound_infection")
        if inf_msg:
            log += f"\n{inf_msg}"

    if player["health"] <= 0:
        log += "\n\n*** You have been defeated... ***"

    return player, log, "COMBAT"


# =========================================================================
# 5. HIGHWAY ROBBER COMPASS INTERROGATION & FOREST SCHISM ENCOUNTERS
# =========================================================================
def resolve_robber_interrogation(choice, player):
    """Handles post-combat interrogation of the Highway Robber leader."""
    if choice == "demand_parvus":
        if "compass" not in player["inventory"]:
            player["inventory"].append("compass")
        player["robber_compass_obtained"] = True
        log = (
            "You press your weapon to the bandit leader's throat and demand he tell you the way to Parvus.\n\n"
            "He winces and rasps: \"You can follow the path along the New Road all the way round, sure... "
            "but if you are in a hurry, the quickest way is straight through Lignum Forest—but the canopy blocks "
            "the sky and spins your head right round! Step one foot in those trees without a needle and you'll "
            "walk in circles till your bones bleach!\"\n\n"
            "Trembling, he unhooks a heavy **Brass Compass** from his belt and presses it into your palm before scrambling into the brush.\n"
            "*** You obtained a Compass! Your D-Pad will now keep its labels and true bearings in Lignum Forest! ***"
        )
        return player, log, "MAIN"

    if choice == "loot_silver":
        player["silver"] += 12
        log = (
            "You empty the highwaymen's coin pouches before kicking them into the ditch.\n"
            "*** You looted 12 Silver! ***"
        )
        return player, log, "MAIN"

    player["reputation"] += 1
    log = (
        "You order the beaten highwaymen off the road. Word of your mercy and strength travels among passing merchants.\n"
        "*** Your Reputation increased by 1! ***"
    )
    return player, log, "MAIN"


FOREST_SPECIES_STATS = {
    "forest owls": {
        "name": "Vanguardist Tawny Owls",
        "health": 12,
        "flee_damage": 2,
        "attack_min": 2,
        "attack_max": 5,
        "attack_verb": "The Vanguardist Owls swoop silently from the dark boughs, raking you with razor talons",
    },
    "forest squirrels": {
        "name": "Vanguardist Red Squirrels",
        "health": 10,
        "flee_damage": 2,
        "attack_min": 1,
        "attack_max": 4,
        "attack_verb": "The Vanguardist Squirrels hurl sharpened flint-acorns and swarm your boots, biting you",
    },
    "forest deer": {
        "name": "Vanguardist Antlered Stag",
        "health": 16,
        "flee_damage": 3,
        "attack_min": 2,
        "attack_max": 6,
        "attack_verb": "The Vanguardist Stag lowers its sharpened crown of antlers and charges, goring you",
    },
    "forest armadillo": {
        "name": "Vanguardist Giant Hairy Armadillo",
        "health": 22,
        "flee_damage": 4,
        "attack_min": 3,
        "attack_max": 7,
        "attack_verb": "The Vanguardist Giant Hairy Armadillo curls its plated shoulders and slams into you with stone-crushing claws",
    },
}


def trigger_forest_animal_combat(player, npc_id):
    """Triggers combat with militant Vanguardist woodland animals in Lignum Forest."""
    spec = FOREST_SPECIES_STATS.get(npc_id, FOREST_SPECIES_STATS["forest deer"])
    player["active_enemy"] = {
        "id": "vanguard_animals",
        "name": spec["name"],
        "health": spec["health"],
        "flee_damage": spec["flee_damage"],
        "attack_min": spec["attack_min"],
        "attack_max": spec["attack_max"],
        "attack_verb": spec["attack_verb"],
        "defeat_msg": (
            f"You drive back the {spec['name']}! They retreat into the high boughs, hissing warnings against the townsfolk's axes.\n"
            "*** (-2 Vanguardists Faction) ***"
        ),
        "flee_msg": "You scramble back through the bracken as the forest defenders harry your heels! (-{dmg} Health)",
    }
    log = (
        "*** VANGUARDIST FOREST AMBUSH! ***\n\n"
        f"{spec['name']} block the trail! Unlike the peaceful Communards of the glades, this group joined the militant Vanguard in the Great Schism to fight the townsfolk turning their woods into farmland!\n"
        "\"No more axes! No more ploughs!\" they cry, lunging to drive you from the trees!"
    )
    return player, log, "COMBAT"


def trigger_vanguard_hideout_combat(player):
    """Triggers combat when breaking free at the Deep Forest Vanguardist Hideout."""
    player["active_enemy"] = {
        "id": "vanguard_animals",
        "name": "Vanguardist Hideout Sentries",
        "health": 20,
        "flee_damage": 4,
        "attack_min": 3,
        "attack_max": 7,
        "attack_verb": "The Vanguardist Stag and Giant Hairy Armadillo batter you with antlers and armoured plates",
        "defeat_msg": (
            "You slash through the last of the vine-nets and fight your way clear of the Vanguardist ring!\n"
            "*** You broke free in the Deep Forest Hideout! (-2 Vanguardists Faction) ***"
        ),
        "flee_msg": "You tear loose from the vine-nets and bolt blindly into the surrounding trees! (-{dmg} Health)",
    }
    log = (
        "*** BREAKING FREE AT THE HIDEOUT! ***\n\n"
        "You wrench your arms free of the vine-net and raise your weapon against the circle of Vanguardist defenders!"
    )
    return player, log, "COMBAT"


def resolve_forest_kidnap(choice, player):
    """Resolves the player's response after being kidnapped to the Deep Forest Hideout."""
    if choice == "sympathise":
        if (
            player.get("equusense", 0) >= 2
            or "radical theory" in player.get("skills", [])
            or player.get("charisma", 0) >= 3
            or player.get("faction_vanguardists", 0) >= 2
        ):
            modify_faction(player, "faction_vanguardists", 2)
            player.setdefault("territories", {})["19,19"] = "Vanguardists"
            log = (
                "Speaking with calm respect for the living woods, you denounce the townsfolk's insatiable appetite for felling ancient trees to make farmland.\n\n"
                "An elder Tawny Owl perches on a broken ploughshare and hoots softly. A Giant Hairy Armadillo slices your vine-bonds with a single claw.\n"
                "\"You speak like the Communards, yet you understand why the Vanguard must bare its teeth,\" the elders murmur. "
                "\"Go in peace, traveller—and tell the townsfolk the forest will not yield another acre.\"\n"
                "*** Released unharmed at the Deep Forest Hideout! (+2 Vanguardists Faction) ***"
            )
            return player, log, "MAIN"

        log = (
            "You try to claim you mean the trees no harm, but your words lack the animal-sense or radical conviction to convince them!\n"
            "\"Your boots smell of town cobbles and ploughed furrows!\" the Vanguardist sentries snarl!"
        )
        p, c_log, st = trigger_vanguard_hideout_combat(player)
        return p, log + "\n\n" + c_log, st

    if choice == "forfeit":
        food_keys = ("cobnuts", "carrot", "apple", "pear", "cucumber", "sack of oats", "meat ration")
        offered_food = next((f for f in food_keys if f in player.get("inventory", [])), None)
        if offered_food:
            player["inventory"].remove(offered_food)
            consume_fresh_food_timestamp(player, offered_food)
            modify_faction(player, "faction_vanguardists", 1)
            log = (
                f"You offer your {offered_food.title()} as reparations for the felled woodland edges.\n"
                "A drey of Red Squirrels unties the vine-net and carries the provisions into the hollow oak.\n"
                "\"The Vanguard accepts your tribute. Now find your own way out of the deep woods!\"\n"
                f"*** Surrendered {offered_food.title()} (+1 Vanguardists Faction) ***"
            )
            return player, log, "MAIN"
        if player.get("silver", 0) >= 10:
            player["silver"] -= 10
            modify_faction(player, "faction_vanguardists", 1)
            log = (
                "You hand over 10 silver coins so the forest defenders can buy back stolen grain and sabotage supplies.\n"
                "The owls slice your bonds and vanish into the canopy.\n"
                f"*** Paid 10 Silver Reparations (+1 Vanguardists Faction | Remaining Silver: {player['silver']}s) ***"
            )
            return player, log, "MAIN"

        log = "You have neither woodland food nor 10 silver to offer as reparations! The Vanguardist sentries close in!"
        p, c_log, st = trigger_vanguard_hideout_combat(player)
        return p, log + "\n\n" + c_log, st

    return trigger_vanguard_hideout_combat(player)
