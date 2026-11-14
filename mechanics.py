"""
mechanics.py
------------
Core game mechanics, survival rules, timekeeping, inventory/weight
management, animal care helpers, Chapter 2 route eligibility, and
Chapter 3 state evaluation.
"""

import copy
import json
import math
import os
import random
import pass_and_play

import ch3_combat_engine
import ch3_war_engine
import companions_engine
import game_data as db
from map_data import world_map
import weather_engine


def record_campaign_victory(player, profile_name="default"):
    """
    Appends a Victory Stamp to the player's persistent meta-profile.
    Triggered during the 100-Point Epilogue.
    """
    filename = f"profile_{profile_name.lower()}_meta.json"
    meta_data = {
        "profile_name": profile_name,
        "total_campaigns_won": 0,
        "victory_grid": [],
    }

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as file_obj:
                meta_data = json.load(file_obj)
        except (OSError, ValueError):
            pass

    difficulty = ch3_war_engine.calculate_campaign_difficulty(player)
    my_fac = player.get("ch3_faction", "Union")
    legacy_pts = (
        player.get("ch3_factions", {}).get(my_fac, {}).get("legacy_pts", 0)
    )

    stamp = {
        "victory_id": meta_data["total_campaigns_won"] + 1,
        "faction": player.get(
            "ch3_campaign_winner", player.get("ch3_winner", my_fac)
        ),
        "starting_rank": player.get(
            "ch3_start_rank", player.get("ch3_rank", "Private")
        ),
        "campaign_days_taken": player.get(
            "ch3_campaign_days", player.get("ch3_day", 1)
        ),
        "starting_legacy_points": legacy_pts,
        "difficulty_score": difficulty,
        "world_state_vector": player.get("ch3_world_bits", {}),
    }

    meta_data["victory_grid"].append(stamp)
    meta_data["victory_grid"] = sorted(
        meta_data["victory_grid"], key=lambda item: item["difficulty_score"]
    )
    meta_data["total_campaigns_won"] = len(meta_data["victory_grid"])

    try:
        with open(filename, "w", encoding="utf-8") as file_obj:
            json.dump(meta_data, file_obj, indent=2)
    except OSError:
        pass


def wipe_profile_data(profile_name="default"):
    """Completely erases the Victory Grid for the specified profile."""
    filename = f"profile_{profile_name.lower()}_meta.json"
    blank_data = {
        "profile_name": profile_name,
        "total_campaigns_won": 0,
        "victory_grid": [],
    }
    try:
        with open(filename, "w", encoding="utf-8") as file_obj:
            json.dump(blank_data, file_obj, indent=2)
        return True
    except OSError:
        return False


def format_item_name(item_key):
    """Formats item keys cleanly into Title Case without capitalizing 's after apostrophes."""
    return " ".join(w.capitalize() for w in str(item_key).split())

def execute_ch2_mission(player, mission_id, time_cost=120, stamina_drain=15):
    """
    Applies the time and stamina cost of a Chapter 2 mission and records
    `active_ch2_mission` for any subsequent interactive minigame.
    """
    player, t_log = advance_time(time_cost, player)
    player["hunger"] = max(0, player["hunger"] - stamina_drain)
    player["thirst"] = max(0, player["thirst"] - stamina_drain)
    player["active_ch2_mission"] = mission_id
    return player, t_log if t_log else ""


# =========================================================================
# 1. AFFLICTIONS, SPOILAGE & STABLING ENGINE
# =========================================================================
AFFLICTION_INFO = {
    "food_poisoning": {
        "name": "Food Poisoning",
        "cure_item": "charcoal bitters",
        "symptom": "Your stomach cramps violently from rancid food (-1 Health, natural healing halted! Cure with Charcoal Bitters)."
    },
    "damp_chill": {
        "name": "Brumaire Damp-Chill (Flu)",
        "cure_item": "flu medicine",
        "symptom": "A feverish Brumaire chill racks your lungs (-1 Health, natural healing halted! Cure with Flu Medicine)."
    },
    "wound_infection": {
        "name": "Wound Sepsis",
        "cure_item": "wound salve",
        "symptom": "Red streaks of infection burn around a dirty blade wound (-1 Health, natural healing halted! Cure with Wound Salve)."
    }
}


def infect_player(player, affliction_key):
    """Applies an illness/poison affliction if the player doesn't already have it."""
    affs = player.setdefault("afflictions", [])
    if affliction_key not in affs and affliction_key in AFFLICTION_INFO:
        affs.append(affliction_key)
        info = AFFLICTION_INFO[affliction_key]
        return (
            f"*** AFFLICTION CONTRACTED: {info['name'].upper()}! "
            f"(Buy {format_item_name(info['cure_item'])} from the Apothecary to stop health loss!) ***"
        )
    return None


def cure_player(player, affliction_key):
    """Removes an affliction using a non-magical remedy (stops health loss without adding HP)."""
    affs = player.get("afflictions", [])
    if affliction_key in affs:
        affs.remove(affliction_key)
        info = AFFLICTION_INFO[affliction_key]
        return (
            f"*** CURED: Your {info['name']} subsides! ***\n"
            "*** Your body is no longer losing health. Eat well and rest to recover your strength naturally. ***"
        )
    return "You take the remedy as a precaution, though you did not have that illness."


def record_food_acquisition(player, item_name):
    """Records the acquisition minute of perishable food items so they spoil over time."""
    shelf_life = db.item_database.get(item_name, {}).get("shelf_life")
    if shelf_life:
        tracker = player.setdefault("fresh_food_timestamps", {})
        tracker.setdefault(item_name, []).append(player["total_game_minutes"])


def consume_fresh_food_timestamp(player, item_name):
    """Pops the oldest timestamp when a perishable item is eaten, sold, dropped, or fed to a horse."""
    tracker = player.get("fresh_food_timestamps", {})
    if item_name in tracker and tracker[item_name]:
        tracker[item_name].pop(0)
        if not tracker[item_name]:
            tracker.pop(item_name, None)


def process_food_spoilage(player):
    """Checks all perishable items in player['inventory'] and converts expired ones into 'spoiled food'."""
    now = player["total_game_minutes"]
    tracker = player.setdefault("fresh_food_timestamps", {})
    spoiled_notices = []

    inv_counts = {}
    for item in player.get("inventory", []):
        if db.item_database.get(item, {}).get("shelf_life"):
            inv_counts[item] = inv_counts.get(item, 0) + 1

    for item, qty in list(inv_counts.items()):
        shelf_life = db.item_database[item]["shelf_life"]
        stamps = tracker.setdefault(item, [])
        while len(stamps) < qty:
            stamps.append(now)
        while len(stamps) > qty:
            stamps.pop(0)

        remaining_stamps = []
        spoiled_cnt = 0
        for acq_min in stamps:
            if now - acq_min >= shelf_life:
                spoiled_cnt += 1
            else:
                remaining_stamps.append(acq_min)

        if spoiled_cnt > 0:
            tracker[item] = remaining_stamps
            for _ in range(spoiled_cnt):
                if item in player["inventory"]:
                    player["inventory"].remove(item)
                    player["inventory"].append("spoiled food")
            qty_str = f"{spoiled_cnt}x " if spoiled_cnt > 1 else ""
            spoiled_notices.append(
                f"*** SPOILED: Your {qty_str}{format_item_name(item)} has gone rancid and turned into Spoiled Food! ***"
            )

    return "\n".join(spoiled_notices) if spoiled_notices else None


def get_stabling_debt(player):
    """Calculates stabling debt at 2 silver per day (minimum 2s on collection)."""
    if not player.get("horse_stabled"):
        return 0
    current_day = (player["total_game_minutes"] // 1000) + 1
    stabled_day = player.get("horse_stabled_day", current_day)
    days_elapsed = max(1, (current_day - stabled_day) + 1)
    return days_elapsed * 2


def check_stabling_foreclosure(player):
    """If stabling debt exceeds 20 silver, Squire Godspeed sells the horse to cover his hay bill."""
    if not player.get("horse_stabled"):
        return None
    debt = get_stabling_debt(player)
    if debt > 20:
        player["horse_stabled"] = False
        player["horse_stabled_day"] = 0
        player["horse_sold_for_debt"] = True
        return (
            "*** STABLE FORECLOSURE NOTICE! ***\n"
            f"Your unpaid stabling tab at Murum Stables exceeded 20 silver ({debt}s owed)!\n"
            "Tired of paying for hay out of his own pocket, Squire Godspeed has put your horse up for sale to recoup the debt!"
        )
    return None


# =========================================================================
# 2. WEIGHT, STORAGE & BANKING HELPERS
# =========================================================================
def get_inventory_weight(player):
    """Calculates total carried weight in lbs, excluding horse barding when the player has a mount."""
    has_mount = ("horse" in player.get("inventory", [])) or player.get("riding_horse", False)
    mount_worn_items = {"horse armour", "dragon shaffron", "heavy winter blanket"} if has_mount else set()

    total = 0.0
    for item in player.get("inventory", []):
        if item == "horse" or item in mount_worn_items:
            continue
        w = db.item_database.get(item, {}).get("weight", 0.2)
        total += w
    return round(total, 1)


def get_max_carry_weight(player):
    """Calculates normal carry threshold based on Strength, Saddlebags, Pack Mounts, and Companions."""
    base = 20.0 + (player.get("strength", 0) * 3.0)
    if "saddlebag" in player.get("inventory", []):
        base += 15.0
    if "horse" in player.get("inventory", []) or "giant hairy armadillo" in player.get("inventory", []):
        base += 15.0
    base += companions_engine.get_companion_carry_bonus(player)
    return round(base, 1)


def can_use_storage(player):
    """Returns True if the player is inside a building with a personal footlocker."""
    storage_set = getattr(db, "STORAGE_LOCATIONS", getattr(db, "storage_locations", set()))
    return player.get("current_building") in storage_set


def stash_item_helper(player, item):
    if not can_use_storage(player):
        return player, "You can only store gear in a safe chest at the Tavern, Pub, Stables, Blacksmith, or Mayor's Quarters."
    if item in player["inventory"]:
        player["inventory"].remove(item)
        player.setdefault("storage", []).append(item)
        curr_w = get_inventory_weight(player)
        max_w = get_max_carry_weight(player)
        return player, f"You store the {format_item_name(item)} safely in your footlocker. (Carry Weight: {curr_w}/{max_w} lbs)"
    return player, "You don't have that item in your pack."


def retrieve_item_helper(player, item):
    storage = player.get("storage", [])
    if item in storage:
        storage.remove(item)
        player["inventory"].append(item)
        curr_w = get_inventory_weight(player)
        max_w = get_max_carry_weight(player)
        return player, f"You retrieve the {format_item_name(item)} from your footlocker. (Carry Weight: {curr_w}/{max_w} lbs)"
    return player, "That item is not in your footlocker."


def deposit_silver_helper(player, amount):
    if not can_use_storage(player):
        return player, "You must be at an inn or workplace footlocker to lock away silver."
    amt = min(player["silver"], amount)
    if amt <= 0:
        return player, "You do not have any silver to deposit."
    player["silver"] -= amt
    player["banked_silver"] = player.get("banked_silver", 0) + amt
    return player, f"You lock {amt} silver safely in your footlocker. (Purse: {player['silver']}s | Stashed: {player['banked_silver']}s)"


def withdraw_silver_helper(player, amount):
    if not can_use_storage(player):
        return player, "You must be at an inn or workplace footlocker to retrieve your stashed silver."
    banked = player.get("banked_silver", 0)
    amt = min(banked, amount)
    if amt <= 0:
        return player, "You have no silver stashed in your footlocker."
    player["banked_silver"] -= amt
    player["silver"] += amt
    return player, f"You withdraw {amt} silver from your footlocker. (Purse: {player['silver']}s | Stashed: {player['banked_silver']}s)"


def sell_item_helper(player, item):
    base_price = db.item_database.get(item, {}).get("price", 0)
    if base_price <= 0:
        return player, f"Old Pennyweight shakes his head. \"I can't put a price on the {format_item_name(item)}, friend.\""
    sell_price = max(1, base_price // 3)
    player["inventory"].remove(item)
    consume_fresh_food_timestamp(player, item)
    player["silver"] += sell_price
    curr_w = get_inventory_weight(player)
    max_w = get_max_carry_weight(player)
    return player, (
        f"Old Pennyweight weighs the {format_item_name(item)} on his brass scales and counts out {sell_price} silver.\n"
        f"*** (+{sell_price} Silver | Total: {player['silver']}s | Carry Weight: {curr_w}/{max_w} lbs) ***"
    )


# =========================================================================
# 3. DISTANCE LOOKING (OPTICAL SCOPE SUPPORT) & COMBAT MATH
# =========================================================================
def get_player_look_range(player):
    """
    Returns (max_range, scope_name).
    Default naked-eye range is 1 square; optical scopes in inventory extend range.
    """
    max_range = 1
    best_scope = None

    for item in player.get("inventory", []):
        item_info = db.item_database.get(item, {})
        item_range = item_info.get("scope_range", 0)

        if item_range == 0 and ("scope" in item.lower() or "spyglass" in item.lower()):
            if any(k in item.lower() for k in ("master", "fine", "high")):
                item_range = 4
            elif any(k in item.lower() for k in ("crude", "battered", "old")):
                item_range = 2
            else:
                item_range = 3

        if item_range > max_range:
            max_range = item_range
            best_scope = item

    return max_range, best_scope


def calculate_max_hit(base_damage, strength, current_health, max_health):
    """
    Returns (min_hit, max_hit).
    Higher strength raises both the maximum hit and the minimum damage floor.
    """
    raw_max_damage = base_damage * (1 + (strength * 0.2))
    raw_min_damage = (raw_max_damage * 0.2) + (strength * 0.5)

    wounded_modifier = 0.5 if current_health <= (max_health * 0.25) else 1.0

    final_max = max(2, math.floor(raw_max_damage * wounded_modifier))
    final_min = max(1, math.floor(raw_min_damage * wounded_modifier))

    if final_min >= final_max:
        final_min = final_max - 1

    return final_min, final_max

# =========================================================================
# PROGRESSION ENEMY SCALING & STAT-BASED HP / DAMAGE MITIGATION
# =========================================================================
def recalculate_player_max_health(player):
    """
    Dynamically updates player['max_health'] based on Strength, overall veteran
    stat growth, and any permanent dungeon/relic health bonuses.
    """
    str_stat = player.get("strength", 0)
    total_stats = (
        str_stat
        + player.get("stealth", 0)
        + player.get("charisma", 0)
        + player.get("influence", 0)
        + player.get("equusense", 0)
    )
    relic_hp = player.get("bonus_max_hp", 0)  # e.g. +1 from Caligo Mine

    new_max = 10 + (str_stat // 3) + (total_stats // 12) + relic_hp
    old_max = player.get("max_health", 10)
    if new_max > old_max:
        diff = new_max - old_max
        player["max_health"] = new_max
        player["health"] = min(new_max, player.get("health", 10) + diff)
    else:
        player["max_health"] = max(old_max, new_max)
    return player["max_health"]


def scale_enemy_for_progression(enemy_dict, player):
    """
    Scales a copy of `enemy_dict` so enemies grow stronger as days pass,
    as Chapter 2 advances (Steps A->E), and when travelling with a Companion!
    """
    import copy
    e = copy.deepcopy(enemy_dict)

    days_passed = player.get("total_game_minutes", 0) // 1000
    ch2_step = player.get("ch2_mission_step", 0) if player.get("chapter_2_route") else 0
    dungeons_done = len(player.get("dungeons_cleared", []))

    # Escalation Tier (0 in early Ch.1 -> 2 at Ch.2 start -> 5 at Ch.2 climax)
    tier = min(6, (days_passed // 3) + ch2_step + (dungeons_done // 2))

    base_hp = e.get("health", 12)
    base_min = e.get("attack_min", 1)
    base_max = e.get("attack_max", 4)

    # +18% HP per Escalation Tier, +1 min/max attack every 2 tiers
    scaled_hp = int(round(base_hp * (1.0 + 0.18 * tier)))
    scaled_min = base_min + (tier // 3)
    scaled_max = base_max + (tier // 2)

    # If the player has an active Road Companion, enemy parties bring reinforcements!
    try:
        import companions_engine
        if companions_engine.get_active_companion_key(player):
            scaled_hp = int(round(scaled_hp * 1.35)) + 3
            scaled_max += 1
    except ImportError:
        pass

    e["health"] = scaled_hp
    e["max_health"] = scaled_hp
    e["attack_min"] = scaled_min
    e["attack_max"] = max(scaled_min + 1, scaled_max)
    e["escalation_tier"] = tier
    return e


def calculate_stat_based_hp_loss(raw_enemy_dmg, player, enemy_name="Enemy"):
    """
    Calculates final HP loss from an enemy attack using ALL of the player's stats
    (Stealth Evasion, Equusense Mounted Mobility, Charisma/Influence Hesitation,
    Strength Toughness, and Worn Armour/Shield/Horse Barding!).
    Returns (final_hp_loss, mitigation_log_note).
    """
    recalculate_player_max_health(player)
    inv = player.get("inventory", [])
    stl = player.get("stealth", 0)
    str_s = player.get("strength", 0)
    cha = player.get("charisma", 0)
    inf = player.get("influence", 0)
    equ = player.get("equusense", 0)
    mounted = bool(player.get("riding_horse"))

    notes = []
    dmg = raw_enemy_dmg

    # 1. STEALTH & MOUNTED EQUUSENSE: Full Dodge or Glancing Blow Roll!
    dodge_chance = min(0.35, stl * 0.035 + (equ * 0.025 if mounted else 0.0))
    glance_chance = min(0.50, stl * 0.05 + (equ * 0.03 if mounted else 0.0))

    roll = random.random()
    if roll < dodge_chance:
        if mounted and equ > stl:
            return 0, f"Your **Equusense ({equ})** wheels your mount cleanly out of reach (**DODGED — 0 HP lost**!)"
        return 0, f"Your **Stealth ({stl})** footwork slips completely past the strike (**DODGED — 0 HP lost**!)"
    elif roll < (dodge_chance + glance_chance):
        dmg = max(1, (dmg + 1) // 2)
        notes.append(f"Stealth/Agility Glancing Blow (-{raw_enemy_dmg - dmg})")

    # 2. CHARISMA & INFLUENCE: Daunting Presence (vs. Human Attackers)
    is_beast = any(b in enemy_name.lower() for b in ("wolf", "boar", "stag", "hound", "beast"))
    social_mit = (cha + inf) // 6 if not is_beast else 0
    if social_mit > 0 and dmg > 1:
        actual_soc = min(dmg - 1, social_mit)
        dmg -= actual_soc
        notes.append(f"Presence CHA/INF (-{actual_soc})")

    # 3. MOUNTED EQUUSENSE & HORSE ARMOUR BARDING
    if mounted and dmg > 1:
        mount_mit = (equ // 5) + (2 if "dragon shaffron" in inv else (1 if "horse armour" in inv else 0))
        if mount_mit > 0:
            actual_m = min(dmg - 1, mount_mit)
            dmg -= actual_m
            notes.append(f"Mount & Barding (-{actual_m})")

    # 4. STRENGTH TOUGHNESS, SHIELD & WORN BODY ARMOUR (Helmet / Gambeson / Jerkin)
    eq_shield = player.get("equipped_shield", "none")
    shield_def = db.shield_defense.get(eq_shield, 0)
    armour_def = (
        (1 if "helmet" in inv else 0)
        + (2 if "gambeson" in inv else (1 if "leather jerkin" in inv else (1 if "guard uniform" in inv else 0)))
    )
    toughness_def = str_s // 5
    total_phys_block = shield_def + armour_def + toughness_def

    if total_phys_block > 0 and dmg > 0:
        # Can reduce weak blows to 0 if heavily armored, or minimum 1 on heavy hits
        min_floor = 0 if (raw_enemy_dmg <= total_phys_block and random.random() < 0.5) else 1
        new_dmg = max(min_floor, dmg - total_phys_block)
        if dmg - new_dmg > 0:
            notes.append(f"Armour/Shield/STR (-{dmg - new_dmg})")
        dmg = new_dmg

    note_str = f" [{' | '.join(notes)}]" if notes else ""
    return max(0, dmg), note_str

# =========================================================================
# ADVANCE TIME, DECIMAL CLOCK & SLEEP
# =========================================================================
def advance_time(minutes, player, world_map=None):
    """Advances the game clock by `minutes` and processes hunger/thirst drain."""
    log_msgs = []
    player["total_game_minutes"] += minutes

    drain = minutes / 25.0
    raw_hunger = player["hunger"] - drain
    raw_thirst = player["thirst"] - drain

    starve_dmg = 0
    if raw_hunger < 0:
        deficit = abs(min(0, player["hunger"]) - raw_hunger) if player["hunger"] <= 0 else abs(raw_hunger)
        starve_dmg += max(1, int(deficit // 4))
    if raw_thirst < 0:
        deficit = abs(min(0, player["thirst"]) - raw_thirst) if player["thirst"] <= 0 else abs(raw_thirst)
        starve_dmg += max(1, int(deficit // 4))

    player["hunger"] = max(0, round(raw_hunger, 1))
    player["thirst"] = max(0, round(raw_thirst, 1))

    if starve_dmg > 0:
        player["health"] = max(1, player["health"] - starve_dmg)
        log_msgs.append(
            f"*** Starvation and thirst take their toll! (-{starve_dmg} Health, Current: {player['health']}/{player['max_health']}) ***"
        )

    if player["riding_horse"]:
        horse_drain = minutes / 12.5
        player["horse_hunger"] -= horse_drain
        player["horse_thirst"] -= horse_drain

        if player["horse_hunger"] <= 0 or player["horse_thirst"] <= 0:
            log_msgs.append(
                "*** Your horse is too hungry and thirsty to carry you! It stubbornly refuses to move. ***\n"
                "*** You are forced to dismount. You must 'water' and 'graze' it to ride again. ***"
            )
            player["riding_horse"] = False
            player["horse_hunger"] = max(0, player["horse_hunger"])
            player["horse_thirst"] = max(0, player["horse_thirst"])

    weather_alerts = weather_engine.update_weather_on_time_advance(player, minutes)
    if weather_alerts:
        log_msgs.extend(weather_alerts)
        
    log_msg = "\n".join(log_msgs) if log_msgs else None
    pass_and_play.record_time_advanced(player, minutes)
    return player, log_msg


def get_time_string(total_mins):
    """Formats total game minutes into the French Republican Decimal Calendar & Clock."""
    day_names = ["Primidi", "Duodi", "Tridi", "Quartidi", "Quintidi", "Sextidi", "Septidi", "Octidi", "Nonidi", "Décadi"]
    month_names = [
        "Vendémiaire", "Brumaire", "Frimaire", "Nivôse", "Pluviôse", "Ventôse",
        "Germinal", "Floréal", "Prairial", "Messidor", "Thermidor", "Fructidor"
    ]
    sansculottides_days = [
        "Fête de la Vertu", "Fête du Génie", "Fête du Travail",
        "Fête de l'Opinion", "Fête des Récompenses"
    ]

    hour = (total_mins % 1000) // 100
    minute = total_mins % 100
    total_days = (total_mins // 1000) + 34
    year = (total_days // 365) + 1
    day_of_year = total_days % 365

    if day_of_year < 360:
        month_index = day_of_year // 30
        day_of_month = (day_of_year % 30) + 1
        day_name = day_names[day_of_year % 10]
        month_name = month_names[month_index]
        date_str = f"{day_name} {day_of_month} {month_name}"
    else:
        sans_day_index = day_of_year - 360
        date_str = f"{sansculottides_days[sans_day_index]}"

    return f"{date_str}, Year {year} - {hour}:{minute:02d}"


def handle_sleep_nap(player):
    """Sleeps for 2 decimal hours (200 minutes), restoring half of missing health."""
    sleep_duration = 200
    missing_hp = player["max_health"] - player["health"]
    healed = max(1, missing_hp // 2) if missing_hp > 0 else 0

    player["health"] = min(player["max_health"], player["health"] + healed)
    player, _ = advance_time(sleep_duration, player)
    player["last_sleep_minute"] = player["total_game_minutes"]
    if player.get("current_building"):
        return player, f"You stretch out for a two-hour nap, recovering your strength (+{healed} HP)."
    return player, (
        "You crawl beneath the canvas of your tent, pull your cloak over your shoulders, and sleep for two decimal hours "
        f"while the wind rustles the brush outside (+{healed} HP)."
    )


def handle_sleep_morning(player, target_wake_time=300):
    """
    Allows the player to sleep until a chosen decimal morning hour:
      - 200 (2:00 Early Dawn — Bakeries, Stables & Docks open)
      - 250 (2:50 Sunrise — Early trail departure)
      - 300 (3:00 Morning Bell — Town Hall, Post Office & Shops open)
      - 375 (3:75 Late Morning Lie-In)
    """
    day_start = (player["total_game_minutes"] // 1000) * 1000
    target_morning = day_start + target_wake_time
    if player["total_game_minutes"] >= target_morning:
        target_morning += 1000

    sleep_duration = target_morning - player["total_game_minutes"]
    hr_str = f"{target_wake_time // 100}:{target_wake_time % 100:02d}"

    # Recovery scales fairly with how long you actually slept (400+ mins = full heal; short 150m catnap = partial heal)
    full_rest = (sleep_duration >= 300)

    if player.get("current_job") == "mayor's house" or player.get("current_building") in ["mayor's house", "mayor's staff entrance"]:
        player["total_game_minutes"] += sleep_duration
        player["health"] = player["max_health"] if full_rest else min(player["max_health"], player["health"] + 4)
        player["hunger"] = 100
        player["thirst"] = 100
        wake_msg = f"You sleep soundly in the servants' quarters and wake at **{hr_str}** to a hot kitchen breakfast."
    elif player.get("current_building"):
        player, _ = advance_time(sleep_duration, player)
        if player["hunger"] > 0 and player["thirst"] > 0:
            player["health"] = player["max_health"] if full_rest else min(player["max_health"], player["health"] + 4)
        else:
            player["health"] = min(player["max_health"], player["health"] + 2)
        wake_msg = f"You sleep soundly in a warm bed and wake at **{hr_str}** feeling rested."
    else:
        player, _ = advance_time(sleep_duration, player)
        if player["hunger"] > 0 and player["thirst"] > 0:
            player["health"] = player["max_health"] if full_rest else min(player["max_health"], player["health"] + 3)
        else:
            player["health"] = min(player["max_health"], player["health"] + 2)
        wake_msg = (
            f"Wrapped in your cloak inside your canvas tent, you sleep until **{hr_str}**.\n"
            "You shake the morning dew from the guy-ropes, pack up your tent, and step out onto the trail."
        )

    player["last_sleep_minute"] = player["total_game_minutes"]
    player["last_heal_minute"] = player["total_game_minutes"]
    player["last_sustenance_tick"] = player["total_game_minutes"]
    return player, wake_msg


# =========================================================================
# NUANCED BUILDING OPENING & CLOSING HOURS (10-HOUR DECIMAL CLOCK: 0..1000)
# =========================================================================
BUILDING_SCHEDULES = {
    # 1. Open 24 Hours (0:00 - 10:00) — Emergency, Watch & Lodging
    "guard house":            (0, 1000, "The Guard House watch-desk is manned around the clock."),
    "hospital":               (0, 1000, "The Hospital infirmary lamps burn day and night."),
    "tavern":                 (200, 1000, "The Tavern opens at 2:00 and locks its shutters at midnight (0:00)."),
    "dog and duck pub":       (250, 1000, "The Dog and Duck Pub opens at 2:50 and serves until midnight (0:00)."),
    "barge and anchor":       (200, 1000, "The Barge & Anchor opens for dawn bargees at 2:00 and closes at midnight (0:00)."),
    "salted anchor":          (200, 1000, "The Salted Anchor serves sailors from 2:00 until midnight (0:00)."),

    # 2. Early-Bird Trades (Open at 2:00 Dawn!)
    "bakery":                 (200, 700, "The Bakery ovens fire at 2:00 dawn and close at 7:00 once the loaves sell out."),
    "stables":                (200, 850, "The Stables open at 2:00 dawn for early riders and lock the stalls at 8:50."),
    "market":                 (225, 725, "The Market stalls open at 2:25 and pack up their awnings at 7:25."),
    "blacksmith":             (225, 800, "The Blacksmith fires the forge at 2:25 and quenches the anvil at 8:00."),

    # 3. Civic, Guild & Commercial Offices
    "post office":            (250, 775, "The Post Office counter is open from 2:50 until the evening mail coach at 7:75."),
    "fluvius post office":    (250, 775, "The Fluvius Post Office counter is open from 2:50 until 7:75."),
    "town hall":              (300, 750, "The Town Hall chancery clerks work from 3:00 until 7:50."),
    "union house":            (250, 900, "Union House is open to workers from 2:50 until 9:00 in the evening."),
    "mayor's house":          (325, 800, "The Mayor's front reception receives callers between 3:25 and 8:00."),
    "mayor's staff entrance": (150, 950, "The Servants' Entrance is unbolted from 1:50 until 9:50 (or all hours for resident staff)."),

    # 4. Afternoon & Evening Entertainment / Nightlife
    "playhouse":              (350, 925, "The Playhouse box-office and stage are open from 3:50 until 9:25."),
    "the red wheel casino":   (400, 1000, "The Red Wheel Casino opens its velvet doors at 4:00 afternoon and runs until midnight (0:00)."),
}


def check_building_open(building_id, total_mins, player=None):
    """
    Checks if a building is currently open based on nuanced decimal hours (0..999).
    Allows resident staff, Union members, or Skeleton Key holders special access!
    Returns (is_open_bool, message_str).
    """
    b_low = building_id.lower().strip()
    time_of_day = total_mins % 1000
    hr_str = f"{time_of_day // 100}:{time_of_day % 100:02d}"

    # Resident staff can always enter the Mayor's Staff Entrance, and lodging guests can enter Inns
    if player:
        if b_low in ("mayor's house", "mayor's staff entrance") and player.get("current_job") == "mayor's house":
            return True, ""
        if b_low == "union house" and player.get("union_status") == "joined" and time_of_day >= 200:
            return True, ""

    open_t, close_t, sched_note = BUILDING_SCHEDULES.get(
        b_low,
        (250, 800, f"The {building_id.title()} is open between 2:50 and 8:00.")
    )

    if open_t <= time_of_day < close_t:
        return True, ""

    open_str = f"{open_t // 100}:{open_t % 100:02d}"
    close_str = "0:00 (Midnight)" if close_t == 1000 else f"{close_t // 100}:{close_t % 100:02d}"
    return False, (
        f"The doors of the **{building_id.title()}** are currently locked (Current Time: **{hr_str}**).\n"
        f"• **Hours:** Open **{open_str} – {close_str}**. ({sched_note})"
    )

def modify_faction(player, faction_key, delta):
    """Safely adjusts a faction score and clamps it strictly between -10 and 10."""
    if faction_key not in player:
        player[faction_key] = 0
    player[faction_key] = max(-10, min(10, player[faction_key] + delta))
    return player[faction_key]


# =========================================================================
# 5. SHIFT TIMING HELPERS
# =========================================================================
def can_start_shift(player):
    """Checks if the player can start a shift right now (within working hours 3:75-7:50, once per day)."""
    current_day = (player["total_game_minutes"] // 1000) + 1
    time_of_day = player["total_game_minutes"] % 1000

    if time_of_day < 375 or time_of_day >= 750:
        return False, "\"It's outside working hours! Come back in the morning after 3:75.\""
    if player.get("last_job_day") == current_day:
        return False, "\"You've already worked a shift today. Get some rest and come back tomorrow.\""
    return True, ""


def mark_shift_started(player):
    """Records the day the shift started so finishing after midnight doesn't block the next day."""
    player["shift_start_day"] = (player["total_game_minutes"] // 1000) + 1
    return player


def mark_shift_completed(player):
    """Stamps last_job_day using the day the shift started rather than post-midnight time."""
    current_day = (player["total_game_minutes"] // 1000) + 1
    player["last_job_day"] = player.get("shift_start_day") or current_day
    player["shift_start_day"] = None
    return player


# =========================================================================
# 6. DYNAMIC TERRITORY & FRONTIER ACCESS ENGINE
# =========================================================================
FACTION_STAT_KEYS = {
    "Guard":        "faction_guard",
    "Union":        "faction_union",
    "Wallmakers":   "faction_wallmakers",
    "Vanguardists": "faction_vanguardists",
    "Communards":   "faction_communards",
}


def set_region_territory(player, region_keyword, controlling_faction):
    """
    Dynamically assigns all coordinates matching `region_keyword` in `world_map`
    to `controlling_faction` ('Guard', 'Union', 'Wallmakers', etc., or None).
    """
    territories = player.setdefault("territories", {})
    for (x, y), loc in world_map.items():
        if region_keyword.lower() in loc.region.lower() or region_keyword.lower() in loc.name.lower():
            key = f"{x},{y}"
            if controlling_faction is None:
                territories.pop(key, None)
            else:
                territories[key] = controlling_faction


def get_tile_territory(player, x, y):
    """Returns the faction currently controlling (x, y), or None if unclaimed."""
    return player.get("territories", {}).get(f"{x},{y}", None)


def check_territory_and_terrain_access(player, target_x, target_y, target_room):
    """
    Checks if the player can enter (target_x, target_y) based on:
      1. Terrain skills ('river navigation', 'swim').
      2. Dynamic Faction Territory ownership & 'safe travel' rules.
    Returns (allowed: bool, event_type: str or None, message: str).
    """
    region = target_room.region
    skills = player.get("skills", [])

    if "River Fluvius" in region:
        if "river navigation" not in skills and "boat" not in player.get("inventory", []):
            return (
                False,
                "BLOCKED_RIVER",
                "The currents of the River Fluvius run deep and swift.\n"
                "*** You need a river craft or the 'River Navigation' skill to travel along the river! ***"
            )

    if any(k in region for k in ["Lake", "Sea"]):
        if "swim" not in skills and "boat" not in player.get("inventory", []):
            return (
                False,
                "BLOCKED_WATER",
                f"The waters of {target_room.name} are deep and freezing.\n"
                "*** You cannot enter deep water without learning the 'Swim' skill! ***"
            )

    owner = get_tile_territory(player, target_x, target_y)
    if not owner:
        return True, None, ""

    is_road_or_path = any(k in region for k in ["Road", "Path"])
    faction_key = FACTION_STAT_KEYS.get(owner, "reputation")
    standing = player.get(faction_key, 0)
    route = player.get("chapter_2_route", "")

    guard_routes = ["Apply for Town Guard", "Parvus: Crown Intelligencers", "Join Castellan's House Staff"]
    union_routes = ["Stand for Union Official", "Parvus: F.A.I.-C.N.T. Syndicate", "Join Fairlight's Acting Troupe"]
    wall_routes = ["Join Wallmaker Syndicate", "Run for Public Office (50s)", "Parvus: Maritime & Artisans Guild (50s)"]

    rival_hostile = False

    if owner == "Guard":
        if route in guard_routes:
            standing = max(0, standing)
        elif player.get("faction_wallmakers", 0) >= 5 or player.get("reputation", 0) <= -2:
            rival_hostile = True
    elif owner == "Wallmakers":
        if route in wall_routes:
            standing = max(0, standing)
        elif player.get("faction_guard", 0) >= 5 or player.get("wallmakers_reported", False):
            rival_hostile = True
    elif owner == "Union":
        if route in union_routes:
            standing = max(0, standing)
        elif player.get("faction_union", 0) < 0:
            rival_hostile = True
    elif owner == "Vanguardists":
        if player.get("faction_vanguardists", 0) < 0 or player.get("faction_communards", 0) >= 5:
            rival_hostile = True
    elif owner == "Communards":
        if player.get("faction_communards", 0) < 0 or player.get("faction_vanguardists", 0) >= 5:
            rival_hostile = True

    if is_road_or_path and "safe travel" in skills and standing >= 0 and not rival_hostile:
        return (
            True,
            "SAFE_ROAD",
            f"[{owner} Territory] Your safe-conduct pass allows you through the {owner} checkpoint on {region}."
        )

    if standing < 0 or rival_hostile:
        return (
            True,
            f"HOSTILE_TERRITORY_{owner.upper()}",
            f"*** WARNING: You have stepped into {owner}-controlled territory ({region})! ***\n"
            f"Defenders loyal to the {owner} spot you trespassing on their turf!"
        )

    return True, "FRIENDLY_TERRITORY", f"[Controlled by {owner} Faction]"


# =========================================================================
# 7. BALANCED CHAPTER 2 ELIGIBILITY & PICK-UP POINTS ENGINE
# =========================================================================
def get_eligible_chapter_2_routes(player):
    """
    Evaluates the player's stats, skills, factions, reputation, and inventory
    against all 10 Chapter 2 starting points.
    """
    routes = []
    skills = player.get("skills", [])
    inv = player.get("inventory", [])
    rep = player.get("reputation", 0)
    silver = player.get("silver", 0)

    str_stat = player.get("strength", 0)
    cha_stat = player.get("charisma", 0)
    stl_stat = player.get("stealth", 0)
    inf_stat = player.get("influence", 0)
    equ_stat = player.get("equusense", 0)

    fac_union = player.get("faction_union", 0)
    fac_guard = player.get("faction_guard", 0)
    fac_wall = player.get("faction_wallmakers", 0)

    total_wealth = silver + player.get("banked_silver", 0) + (40 if ("horse" in inv or player.get("riding_horse")) else 0)

    has_sword = any(
        w in inv for w in ["iron dagger", "iron sword", "steel longsword", "masterwork steel longsword"]
    ) or (
        player.get("equipped_weapon") in ["iron dagger", "iron sword", "steel longsword", "masterwork steel longsword"]
    )
    has_camp_gear = (
        ("tent" in inv)
        or ("horse" in inv)
        or player.get("riding_horse", False)
        or player.get("horse_stabled", False)
    )

    has_outlaw_weapon = has_sword or any(w in inv for w in ["iron dagger", "knuckle duster", "crossbow", "macuahuitl"])

    # 1. Stand for Election as Union Official
    if (
        player.get("union_status") == "joined"
        and fac_union >= 4
        and ("union steward" in skills or "radical theory" in skills or cha_stat >= 5 or equ_stat >= 5)
    ):
        routes.append("Stand for Union Official")

    # 2. Apply for and Join the Guard
    blown_agent = player.get("wallmakers_reported", False) and "intelligence officer" not in skills
    if blown_agent:
        if rep >= 5 and fac_guard >= 8 and stl_stat >= 5:
            routes.append("Apply for Town Guard")
    else:
        if rep >= 3 and (
            fac_guard >= 5
            or (str_stat >= 6 and has_sword)
            or ("ride" in skills and equ_stat >= 5)
        ):
            routes.append("Apply for Town Guard")

    # 3. Visit Castellan and Join Castle House Staff
    if (
        rep >= 5
        and fac_wall <= 2
        and (
            ("mayor's footman" in skills and inf_stat >= 5)
            or ("stable master" in skills and equ_stat >= 5)
        )
    ):
        routes.append("Join Castellan's House Staff")

    # 4A. Sent to Parvus: F.A.I.-C.N.T. Revolutionary Syndicate
    if (
        ("syndicate token" in inv or player.get("anarchist_cell_joined") or "radical theory" in skills)
        and fac_union >= 3
        and cha_stat >= 5
    ):
        routes.append("Parvus: F.A.I.-C.N.T. Syndicate")

    # 4B. Sent to Parvus: Crown Intelligencers (Coastal Customs)
    if (
        ("intelligence officer" in skills or "king's intelligencer" in skills or fac_guard >= 7)
        and fac_guard >= 7
        and (stl_stat >= 5 or inf_stat >= 5)
    ):
        routes.append("Parvus: Crown Intelligencers")

    # 4C. Sent to Parvus: Maritime & Artisans Guild
    if (
        rep >= 5
        and silver >= 50
        and total_wealth >= 85
        and (
            ("master blacksmith" in skills and str_stat >= 5)
            or ("market overseer" in skills and cha_stat >= 5)
            or ("forge" in skills and str_stat >= 6)
        )
    ):
        routes.append("Parvus: Maritime & Artisans Guild (50s)")

    # 5. Run for Public Office
    if (
        rep >= 6
        and silver >= 50
        and "reference letter" in inv
        and (inf_stat >= 5 or cha_stat >= 5)
    ):
        routes.append("Run for Public Office (50s)")

    # 6. Join the Criminal Organisation Behind the Wallmakers
    if (
        fac_wall >= 6
        and stl_stat >= 6
        and not player.get("wallmakers_reported")
        and ("master wallmaker" in skills or "climb" in skills)
    ):
        routes.append("Join Wallmaker Syndicate")

    # 7. Become a Highway Robber
    if (
        rep <= 0
        and has_outlaw_weapon
        and has_camp_gear
        and (str_stat >= 5 or stl_stat >= 5)
    ):
        routes.append("Become a Highway Robber")

    # 8. Become a Member of Fairlight's Acting Troupe
    if (
        rep >= 1
        and (cha_stat >= 5 or inf_stat >= 5)
        and ("playhouse ticket" in inv or "poster" in inv)
    ):
        routes.append("Join Fairlight's Acting Troupe")
    routes = pass_and_play.filter_unclaimed_ch2_routes(player, routes)
    return routes


def resolve_chapter_2_route(choice, player):
    """
    Executes the chosen Chapter 2 starting point, updates territories and route gear,
    and keeps the player at the Town Hall Noticeboard with natural geographic directions.
    """
    if choice == "< Step Back":
        return player, "You step back from the Town Hall Noticeboard.", "MAIN"

    player["chapter_2_route"] = choice

    if choice == "Stand for Union Official":
        set_region_territory(player, "Murum Farm", "Union")
        set_region_territory(player, "Fluvius Farm", "Union")
        log = (
            "=== CHAPTER 2: REGIONAL UNION OFFICIAL ===\n"
            "You sign your name to the Union candidacy register! Word spreads rapidly to Union House and the surrounding farmlands.\n"
            "*** Murum Farm and Fluvius Farm have rallied to UNION TERRITORY! ***\n"
            "*** OBJECTIVE: Travel south of Murum Town to the Picket Crossroads in the Murum Farmlands and speak to Organiser Joyinsorrow to begin your campaign! ***"
        )
    elif choice == "Apply for Town Guard":
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        set_region_territory(player, "The New Road", "Guard")
        log = (
            "=== CHAPTER 2: THE FRONTIER WATCH ===\n"
            "Your enlistment into the Frontier Watch is stamped and sealed!\n"
            "*** The New Road is now patrolled as GUARD TERRITORY! (+Safe Travel) ***\n"
            "*** OBJECTIVE: Follow the New Road north of Murum Gate to the Frontier Watchpost and report to Lieutenant Beornraed! ***"
        )
    elif choice == "Join Castellan's House Staff":
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        log = (
            "=== CHAPTER 2: THE CASTELLAN'S HOUSEHOLD ===\n"
            "You claim the wax-sealed commission for Lord Longsword's household at Castle Ragmore!\n"
            "*** (+Safe Travel) ***\n"
            "*** OBJECTIVE: Travel north-west across the Ragmore Plains to Castle Ragmore and report to Castellan Hrothgar! ***"
        )
    elif choice == "Parvus: F.A.I.-C.N.T. Syndicate":
        log = (
            "=== CHAPTER 2: F.A.I.-C.N.T. SYNDICATE ===\n"
            "Your Syndicate credentials are prepared.\n"
            "*** OBJECTIVE: Travel north along the New Road (or through Lignum Forest) to the Parvus Town docks and make contact with Speaktruth! ***"
        )
    elif choice == "Parvus: Crown Intelligencers":
        player["silver"] += 50
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        log = (
            "=== CHAPTER 2: CROWN INTELLIGENCERS ===\n"
            "You receive a 50-silver cipher pouch from the Watch.\n"
            "*** (+Safe Travel, +50 Silver) ***\n"
            "*** OBJECTIVE: Travel north to Parvus Town and report to Crown Intelligencer Eadric on the western quays! ***"
        )
    elif choice == "Parvus: Maritime & Artisans Guild (50s)":
        player["silver"] -= 50
        log = (
            "=== CHAPTER 2: MARITIME & ARTISANS GUILD ===\n"
            "You pay the 50-silver charter bond.\n"
            "*** (-50 Silver) ***\n"
            "*** OBJECTIVE: Travel north to the eastern guild-wharves of Parvus Town and speak to Guildmaster Buildhope! ***"
        )
    elif choice == "Run for Public Office (50s)":
        player["silver"] -= 50
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        log = (
            "=== CHAPTER 2: REGIONAL ENVOY OF MURUM ===\n"
            "You lodge your 50-silver aldermanic deposit and receive diplomatic credentials!\n"
            "*** (+Safe Travel, -50 Silver) ***\n"
            "*** OBJECTIVE: Travel north-west across the plains to Castle Ragmore to secure Castellan Hrothgar's endorsement! ***"
        )
    elif choice == "Join Wallmaker Syndicate":
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        set_region_territory(player, "The Old Path", "Wallmakers")
        log = (
            "=== CHAPTER 2: INNER CIRCLE OF THE SYNDICATE ===\n"
            "You claim the hidden Guild marker on the noticeboard. Hopestill's couriers now recognize you along the Old Path.\n"
            "*** (+Safe Travel | The Old Path is now WALLMAKERS TERRITORY!) ***\n"
            "*** OBJECTIVE: Travel south-west down the Old Path to the Ruined Waystation and meet The Diewell! ***"
        )
    elif choice == "Become a Highway Robber":
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        log = (
            "=== CHAPTER 2: OUTLAW OF THE NEW ROAD ===\n"
            "You tear your own wanted notice off the Town Hall board and pocket it with a grin.\n"
            "*** (+Safe Travel) ***\n"
            "*** OBJECTIVE: Travel north-east to the outlaw camp at Diluvium Glade and speak with Black Dog! ***"
        )
    elif choice == "Join Fairlight's Acting Troupe":
        if "safe travel" not in player["skills"]:
            player["skills"].append("safe travel")
        log = (
            "=== CHAPTER 2: FAIRLIGHT'S GRAND THEATRICAL TOUR ===\n"
            "You sign Fairlight's touring contract!\n"
            "*** (+Safe Travel) ***\n"
            "*** OBJECTIVE: Meet Fairlight outside the Murum Playhouse to begin your regional tour! ***"
        )
    else:
        return player, "Unknown noticeboard posting.", "MAIN"

    player["ch2_mission_step"] = 1
    player["position_strength"] = 0
    player["exposure_tells"] = 0
    player["ch3_world_bits"] = {}

    return player, log, "MAIN"


# =========================================================================
# 8. WALL CLIMBING (UP / DOWN) & RAMPART WALKING ENGINE
# =========================================================================
def resolve_wall_walk(player, world_map_ref, target_pos):
    """
    Called when walking from one 'The Town Wall' tile to another adjacent 'The Town Wall' tile.
    Rolls 1d6 + Strength (+2 if 'climb' skill). On <= 3, the player slips and falls off the wall.
    """
    roll = random.randint(1, 6)
    str_stat = player.get("strength", 0)
    climb_bonus = 2 if "climb" in player.get("skills", []) else 0
    total = roll + str_stat + climb_bonus
    b_str = f" + {climb_bonus} Climb" if climb_bonus else ""

    if total >= 4:
        log = (
            f"*** RAMPART BALANCE CHECK: Rolled {roll} + {str_stat} Str{b_str} = {total} (Need 4+) ***\n"
            "You edge carefully along the narrow, moss-slicked stone ramparts."
        )
        return player, target_pos, log

    dmg = random.randint(2, 4)
    player["health"] -= dmg

    tx, ty = target_pos
    ground_neighbors = []
    for gx, gy in [(tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)]:
        if (gx, gy) in world_map_ref and world_map_ref[(gx, gy)].name not in ["The Town Wall", "Mountain"]:
            ground_neighbors.append((gx, gy))

    if not ground_neighbors:
        cx, cy = player["x"], player["y"]
        for gx, gy in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
            if (gx, gy) in world_map_ref and world_map_ref[(gx, gy)].name not in ["The Town Wall", "Mountain"]:
                ground_neighbors.append((gx, gy))

    landing_pos = random.choice(ground_neighbors) if ground_neighbors else (player["prev_x"], player["prev_y"])
    land_name = world_map_ref[landing_pos].name if landing_pos in world_map_ref else "the ground below"

    log = (
        f"*** RAMPART BALANCE FAILED! (Rolled {roll} + {str_stat} Str{b_str} = {total} < 4) ***\n"
        f"Your boot slips on wet moss! You lose your footing and plummet off the wall into {land_name}!\n"
        f"*** You took {dmg} fall damage! (Health: {player['health']}/{player['max_health']}) ***"
    )
    return player, landing_pos, log


def resolve_wall_climb(player, world_map_ref, target_name, dx, dy, mode="up"):
    """
    Handles both Climbing UP onto a Wall/Mountain and Climbing DOWN to an adjacent ground tile.
    Uses a 1d6 + Strength (+2 for 'climb' skill or rope) check.
    """
    skills = player.get("skills", [])
    inv = player.get("inventory", [])
    str_stat = player.get("strength", 0)
    has_gear = ("rope" in inv and "grappling hook" in inv)

    if mode == "up":
        if target_name == "The Town Wall" and "climb" not in skills and not has_gear:
            return (
                player,
                False,
                "A towering stone wall blocks your path. It is far too high to scale without the 'climb' skill or a Rope and Grappling Hook."
            )

        roll = random.randint(1, 6)
        bonus = 2 if "climb" in skills else (1 if has_gear else 0)
        total = roll + str_stat + bonus
        b_str = f" + {bonus} Skill/Gear" if bonus else ""

        if total < 3:
            player["health"] -= 1
            log = (
                f"*** CLIMB UP FAILED! (Rolled {roll} + {str_stat} Str{b_str} = {total} < 3) ***\n"
                f"Your grip slips on the cold stone halfway up {target_name}! You slide back down, scraping your hands (-1 Health | HP: {player['health']}/{player['max_health']})."
            )
            return player, False, log

        method = (
            "Using the handholds you memorized" if "climb" in skills
            else "Swinging your grappling hook" if has_gear
            else "Scrambling up the rock face"
        )
        log = (
            f"*** CLIMB UP SUCCESS: Rolled {roll} + {str_stat} Str{b_str} = {total} (Need 3+) ***\n"
            f"{method}, you haul yourself up onto {target_name}."
        )
    else:
        roll = random.randint(1, 6)
        bonus = 2 if ("climb" in skills or "rope" in inv) else 0
        total = roll + str_stat + bonus
        b_str = f" + {bonus} Skill/Rope" if bonus else ""

        if total >= 3:
            log = (
                f"*** CLIMB DOWN SUCCESS: Rolled {roll} + {str_stat} Str{b_str} = {total} (Need 3+) ***\n"
                f"You carefully lower yourself down from the ramparts into {target_name}."
            )
        else:
            player["health"] -= 2
            log = (
                f"*** ROUGH DESCENT! (Rolled {roll} + {str_stat} Str{b_str} = {total} < 3) ***\n"
                f"Your hand slips near the bottom and you drop hard onto the cobbles of {target_name}! (-2 Health | HP: {player['health']}/{player['max_health']})"
            )

    player["prev_x"], player["prev_y"] = player["x"], player["y"]
    player["x"] += dx
    player["y"] += dy

    if player.get("riding_horse"):
        player["riding_horse"] = False
        log += "\nYou are forced to dismount your horse to make the climb."

    return player, True, log


# =========================================================================
# 9. ANIMAL CARE, ITEM, STEAL & TELEMETRY HELPERS
# =========================================================================
def get_available_horses(player):
    """Returns a list of distinct horse labels currently available for Animal Care."""
    horses = []
    loc = player["current_building"] if player["current_building"] else (player["x"], player["y"])

    if (
        db.npc_database.get("horse", {}).get("location") == loc
        and "horse" not in player["inventory"]
        and not player.get("horse_stabled")
    ):
        horses.append("tethered horse")
    if "horse" in player["inventory"]:
        horses.append("your horse")
    if any(h in player["inventory"] for h in ["mayor's stallion", "mayor's shod stallion", "watered stallion", "fed and watered stallion"]):
        horses.append("mayor's stallion")
    return horses


def mount_dismount_helper(player, world_map_ref, animal="horse"):
    if animal in ["your horse", "horse"]:
        animal = "horse"
    is_riding = player.get("riding_horse", False) if animal == "horse" else player.get(f"riding_{animal}", False)

    if is_riding:
        if animal == "horse":
            player["riding_horse"] = False
        else:
            player[f"riding_{animal}"] = False
        return player, f"You climb down from the {animal}. You are now travelling on foot."

    if animal in player["inventory"]:
        if "ride" in player["skills"]:
            if player["current_building"]:
                return player, f"You cannot ride a {animal} indoors!"
            if "Town" in world_map_ref[(player["x"], player["y"])].region:
                return player, f"You cannot ride your {animal} here. The streets are too crowded."
            if animal == "horse":
                player["riding_horse"] = True
            else:
                player[f"riding_{animal}"] = True
            return player, f"You swing up into the saddle. You are now riding the {animal}."
        return player, f"You try to mount the {animal}, but without the 'ride' skill, it immediately bucks you off."
    if player.get("horse_stabled") and animal == "horse":
        return player, "Your horse is currently stabled at Murum Stables! Collect it from the stables first."
    return player, f"You do not own a {animal}."


def stable_horse_helper(player):
    at_stables = (player["current_building"] in ["stables", "tack room", "stable loft"]) or (player["x"] == 7 and player["y"] == 15)
    if not at_stables:
        return player, "You must be at Murum Stables to stable or collect your horse."

    if "horse" in player["inventory"]:
        player["inventory"].remove("horse")
        player["riding_horse"] = False
        player["horse_stabled"] = True
        player["horse_stabled_day"] = (player["total_game_minutes"] // 1000) + 1
        player["horse_hunger"] = 100
        player["horse_thirst"] = 100
        return player, (
            "You lead your horse into a warm stall at Murum Stables.\n"
            "*** Horse Stabled! (Tab: 2 silver/day, payable on collection. Warning: If your unpaid tab exceeds 20s, Squire Godspeed will sell your horse!) ***"
        )
    if player.get("horse_stabled"):
        debt = get_stabling_debt(player)
        if player["silver"] < debt:
            return player, (
                f"Your stabling tab is currently {debt} silver (2s/day), and you only have {player['silver']}s!\n"
                "Pay your tab before it exceeds 20 silver, or Squire Godspeed will sell your horse!"
            )
        player["silver"] -= debt
        player["horse_stabled"] = False
        player["horse_stabled_day"] = 0
        player["horse_hunger"] = 100
        player["horse_thirst"] = 100
        player["inventory"].append("horse")
        return player, (
            f"You pay your {debt}-silver stabling tab and retrieve your well-rested horse.\n"
            f"*** Your horse is back with you! (-{debt}s | Remaining Silver: {player['silver']}s) ***"
        )
    return player, "You do not have a horse to stable or collect."


def feed_animal_helper(player, animal):
    animal = animal.lower()
    food_item = next((f for f in ["apple", "carrot", "cobnuts"] if f in player["inventory"]), None)
    if not food_item:
        return player, "You don't have any apples, carrots, or cobnuts to feed the horse."

    if animal in ["tethered horse", "rosinante"]:
        player["inventory"].remove(food_item)
        consume_fresh_food_timestamp(player, food_item)
        current_day = (player["total_game_minutes"] // 1000) + 1
        if player["rosinante_last_fed_day"] == current_day:
            return player, f"You hold out a {food_item} to the tethered horse. It appreciates the extra snack, but seems full for today."
        player["rosinante_feed_count"] += 1
        player["rosinante_last_fed_day"] = current_day
        if player["rosinante_feed_count"] >= 3:
            player["inventory"].append("horse")
            db.npc_database["horse"]["location"] = None
            return player, (
                f"You hold out a {food_item}. The horse crunches it happily!\n\n"
                "*** The horse lets out a joyful whinny and breaks its tether! ***\n"
                "*** Rosinante has chosen you as its companion! You now own a horse! ***"
            )
        return player, f"You hold out a {food_item}. The horse crunches it happily and nudges your shoulder affectionately."

    if animal == "mayor's stallion":
        if player["active_mayor_task"] == "graze_horse" and "watered stallion" in player["inventory"]:
            player["inventory"].remove(food_item)
            consume_fresh_food_timestamp(player, food_item)
            player["inventory"].remove("watered stallion")
            player["inventory"].append("fed and watered stallion")
            player["active_mayor_task"] = "return_horse_to_stables"
            return player, f"You feed a {food_item} to the Mayor's stallion.\n*** The Mayor's horse is fed! Return it to the Stable Manager. ***"
        return player, "The Mayor's stallion needs to be shod and watered before being fed!"

    if animal in ["your horse", "horse"]:
        player["inventory"].remove(food_item)
        consume_fresh_food_timestamp(player, food_item)
        player["horse_hunger"] = min(100, player["horse_hunger"] + 50)
        return player, f"You feed a {food_item} to your horse. It crunches happily!\n*** Your horse's hunger is satisfied! (Hunger: {round(player['horse_hunger'])}/100) ***"

    return player, "Nothing happens."


def water_animal_helper(player, animal):
    animal = animal.lower()
    if animal == "tethered horse":
        return player, "The tethered horse already has a water trough right beside its post."

    at_fountain = (player["x"] == 8 and player["y"] == 15 and not player["current_building"])
    has_flask = ("full water flask" in player["inventory"] or "half-full water flask" in player["inventory"])
    if not at_fountain and not has_flask:
        return player, "You are not near the Market fountain, and you don't have any water in a flask!"

    if not at_fountain:
        flask_used = "full water flask" if "full water flask" in player["inventory"] else "half-full water flask"
        flask_result = "half-full water flask" if flask_used == "full water flask" else "empty flask"
        player["inventory"].remove(flask_used)
        player["inventory"].append(flask_result)
        prefix = "You pour water from your flask into your cupped hands."
    else:
        prefix = "You lead the horse to the market fountain."

    if animal == "mayor's stallion":
        if player["active_mayor_task"] == "water_horse" and "mayor's shod stallion" in player["inventory"]:
            player["inventory"].remove("mayor's shod stallion")
            player["inventory"].append("watered stallion")
            player["active_mayor_task"] = "graze_horse"
            return player, f"{prefix} The Mayor's stallion drinks deeply.\n*** The Mayor's horse is watered! Now it needs to graze or be fed. ***"
        return player, "The Mayor's stallion does not need water right now."

    if animal in ["your horse", "horse"]:
        restore = 100 if at_fountain else 50
        player["horse_thirst"] = min(100, player["horse_thirst"] + restore)
        return player, f"{prefix} Your horse drinks deeply.\n*** Your horse's thirst is now {round(player['horse_thirst'])}/100! ***"

    return player, "Nothing happens."


def graze_animal_helper(player, animal):
    animal = animal.lower()
    if animal == "tethered horse":
        return player, "You cannot lead the tethered horse away to graze."

    in_town = (7 <= player["x"] <= 11 and 13 <= player["y"] <= 16)
    if player["current_building"] is None and (not in_town or (player["x"] == 8 and player["y"] == 13)):
        player, t_log = advance_time(30, player)
        logs = [t_log] if t_log else []
        if animal == "mayor's stallion":
            if player["active_mayor_task"] == "graze_horse" and "watered stallion" in player["inventory"]:
                player["inventory"].remove("watered stallion")
                player["inventory"].append("fed and watered stallion")
                player["active_mayor_task"] = "return_horse_to_stables"
                logs.append("You let the Mayor's stallion graze in the lush grass.\n*** The Mayor's horse is fed! Return it to the Stable Manager. ***")
            else:
                logs.append("The Mayor's stallion does not need to graze right now.")
        elif animal in ["your horse", "horse"]:
            player["horse_hunger"] = 100
            logs.append("You let your horse graze in the lush grass.\n*** Your horse is fully fed! (Hunger: 100/100) ***")
        return player, "\n".join(logs)

    return player, "The paved streets of the town have no grass! Leave the town walls or go to the Grazing Field."


def equip_item_helper(player, item_key):
    if item_key in db.shield_defense or item_key == "unequip_shield":
        if player.get("equipped_shield", "none") != "none":
            player["inventory"].append(player["equipped_shield"])
        if item_key == "unequip_shield":
            player["equipped_shield"] = "none"
            return player, "*** You unequipped your shield. ***"
        player["equipped_shield"] = item_key
        if item_key in player["inventory"]:
            player["inventory"].remove(item_key)
        block_val = db.shield_defense[item_key]
        return player, f"*** You strapped on the {format_item_name(item_key)}! (Blocks up to {block_val} damage per hit) ***"

    if player["equipped_weapon"] != "fists":
        player["inventory"].append(player["equipped_weapon"])
    player["equipped_weapon"] = item_key
    if item_key != "fists" and item_key in player["inventory"]:
        player["inventory"].remove(item_key)
    return player, f"*** You equipped the {format_item_name(item_key)}! ***"


def consume_item_helper(player, item):
    item_info = db.item_database.get(item, {})
    if item not in player["inventory"]:
        return player, ""
    player["inventory"].remove(item)
    consume_fresh_food_timestamp(player, item)
    if "transforms_into" in item_info:
        player["inventory"].append(item_info["transforms_into"])

    logs = [item_info.get("consume_desc", f"You consume the {format_item_name(item)}.")]
    if "hunger_restore" in item_info:
        restore = item_info["hunger_restore"]
        player["hunger"] = min(100, player["hunger"] + restore)
        logs.append(f"*** You restored {restore} Hunger! (Current: {round(player['hunger'])}/100) ***")
    if "thirst_restore" in item_info:
        restore = item_info["thirst_restore"]
        player["thirst"] = min(100, player["thirst"] + restore)
        player["last_sustenance_tick"] = player["total_game_minutes"]
        logs.append(f"*** You restored {restore} Thirst! (Current: {round(player['thirst'])}/100) ***")
    if "causes_affliction" in item_info:
        inf_msg = infect_player(player, item_info["causes_affliction"])
        if inf_msg:
            logs.append(inf_msg)
    if "cures_affliction" in item_info:
        cure_msg = cure_player(player, item_info["cures_affliction"])
        if cure_msg:
            logs.append(cure_msg)
    return player, "\n".join(logs)


def drop_item_helper(player, item):
    if item not in player["inventory"]:
        return player, ""
    if db.item_database.get(item, {}).get("price", 0) == 0 and item not in ["spoiled food", "cobnuts", "clean straw", "bucket of sand", "bucket of hot water"]:
        return player, f"You shouldn't throw away the {format_item_name(item)}—it looks important!"
    player["inventory"].remove(item)
    consume_fresh_food_timestamp(player, item)
    curr_w = get_inventory_weight(player)
    max_w = get_max_carry_weight(player)
    return player, f"You set down and discard the {format_item_name(item)}. (Carry Weight: {curr_w}/{max_w} lbs)"


def give_gift_helper(player, npc_key, gift_item):
    if gift_item not in player["inventory"]:
        return player, ""
    current_day = (player["total_game_minutes"] // 1000) + 1
    gifted_today = player.setdefault("gifted_npcs_day", {})
    if gifted_today.get(npc_key) == current_day:
        return player, f"You have already given a gift to {db.npc_database[npc_key]['proper_name']} today."

    player["inventory"].remove(gift_item)
    gifted_today[npc_key] = current_day
    npc_name = db.npc_database[npc_key]["proper_name"]
    rep_gain = 2 if db.item_database.get(gift_item, {}).get("price", 0) >= 18 else 1
    player["reputation"] += rep_gain

    faction_msg = ""
    if npc_key in ["wealdhere", "sigeberht", "aelfgifu"]:
        player["faction_guard"] = min(10, player["faction_guard"] + 2)
        faction_msg = ", +2 Guard Faction"
    elif npc_key in ["union clerk", "truthtale", "horse groom", "landlord"]:
        player["faction_union"] = min(10, player["faction_union"] + 2)
        faction_msg = ", +2 Union Faction"
    elif npc_key in ["wellspring", "hopestill"]:
        player["faction_wallmakers"] = min(10, player["faction_wallmakers"] + 2)
        faction_msg = ", +2 Wallmakers Faction"

    return player, (
        f"You present the {format_item_name(gift_item)} to {npc_name}.\n"
        f"They accept your thoughtful gift with genuine appreciation!\n"
        f"*** (+{rep_gain} Reputation{faction_msg}) ***"
    )


def drink_helper(player, source):
    if source in db.item_database and "thirst_restore" in db.item_database[source]:
        return consume_item_helper(player, source)
    if source in ["fountain", "well", "river", "lake"]:
        player["thirst"] = 100
        player["last_sustenance_tick"] = player["total_game_minutes"]
        return player, f"You cup your hands and drink deeply from the {source}.\n*** Your thirst is fully satisfied! ***"
    if source == "sea":
        player["health"] -= 2
        player["thirst"] = max(0, player["thirst"] - 10)
        return player, "You gulp down the seawater. It is aggressively salty and makes you violently ill!\n*** You drank salt water! (-2 Health, increased thirst) ***"
    return player, ""


def fill_flask_helper(player, source):
    if source == "sea":
        return player, "You probably shouldn't fill your flask with salt water."
    if "empty flask" in player["inventory"]:
        player["inventory"].remove("empty flask")
        player["inventory"].append("full water flask")
        return player, f"You fill your empty flask to the brim at the {source}."
    if "half-full water flask" in player["inventory"]:
        player["inventory"].remove("half-full water flask")
        player["inventory"].append("full water flask")
        return player, f"You top off your water flask at the {source}."
    return player, "You don't have a flask to fill."


def steal_subject_helper(player, world_map_ref, target):
    pos = (player["x"], player["y"])
    room = world_map_ref[pos]
    if target in room.objects:
        room.objects.remove(target)
    player["inventory"].append(target.lower())
    if target.lower() == "horse":
        db.npc_database["horse"]["location"] = None

    logs = [f"You check your surroundings, quietly grab the {target}, and make off with it."]
    catch_chance = max(0.05, 0.80 - (player["stealth"] * 0.10))
    if random.random() < catch_chance:
        player["reputation"] -= 2
        msg = f"*** You were spotted! You lost 2 Reputation! (Current Reputation: {player['reputation']}) ***"
        if player["reputation"] < 0:
            msg += "\n*** You feel a chill run down your spine. The guards will be watching for you. ***"
        logs.append(msg)
    else:
        logs.append("*** Your high stealth allowed you to steal the item completely unseen! ***")
    return player, "\n".join(logs)


def steal_letter_map_helper(player):
    if "misdelivered town hall letter" not in player["inventory"]:
        return player, ""
    player["inventory"].remove("misdelivered town hall letter")
    player["inventory"].append("murum town map")
    log = (
        "You glance around, break the official wax seal on the Misdelivered Letter, and slip the **Murum Town Map** into your coat before tossing the torn envelope into a gutter!\n"
        "*** You obtained the Murum Town Map! (Press 'M' or click 'View Map' to inspect it!) ***"
    )
    catch_chance = max(0.05, 0.75 - (player["stealth"] * 0.10))
    if random.random() < catch_chance:
        player["reputation"] -= 2
        log += f"\n*** A passerby saw you tearing open official municipal post! (-2 Reputation | Current: {player['reputation']}) ***"
    else:
        log += "\n*** Your stealth allowed you to pocket the map without a soul noticing! ***"
    return player, log


def build_playtest_report(player, outcome_title):
    """Writes a human-readable playtest_report.txt file for beta testers to share."""
    days = (player["total_game_minutes"] // 1000) + 1
    skills_str = ", ".join(player.get("skills", [])) or "None"
    inv_str = ", ".join(player.get("inventory", [])) or "Empty"
    hs_str = ", ".join(f"{k}: {v}" for k, v in player.get("high_scores", {}).items())
    job_raw = player.get("current_job")
    job_str = " ".join(w.capitalize() for w in job_raw.split()) if job_raw else "Unemployed"

    report = (
        "=========================================================\n"
        "       DTESSERA TERRA - CHAPTER 1 PLAYTEST REPORT        \n"
        "=========================================================\n"
        f"Outcome / Route : {outcome_title}\n"
        f"Days Elapsed    : {days} (Total Minutes: {player['total_game_minutes']})\n"
        f"Primary Job     : {job_str}\n"
        f"Shifts Worked   : Blacksmith={player['blacksmith_shifts_completed']}, "
        f"Market={player['market_sweeper_shifts']}, Stables={player['stable_shifts']}, "
        f"Mayor={player['mayors_house_shifts']}, Wallmakers={player['wall_surveyor_shifts']}\n"
        "---------------------------------------------------------\n"
        f"Silver          : {player['silver']}s\n"
        f"Reputation      : {player['reputation']}\n"
        f"Health          : {player['health']}/{player['max_health']} "
        f"(Hunger: {player['hunger']:.0f}, Thirst: {player['thirst']:.0f})\n"
        f"Attributes      : Strength={player['strength']}, Charisma={player['charisma']}, "
        f"Stealth={player['stealth']}, Influence={player.get('influence', 0)}, Equusense={player.get('equusense', 0)}\n"
        f"Factions        : Guard={player['faction_guard']}, Union={player['faction_union']}, "
        f"Wallmakers={player['faction_wallmakers']}, Vanguardists={player.get('faction_vanguardists', 0)}, "
        f"Communards={player.get('faction_communards', 0)}\n"
        f"Skills Learned  : {skills_str}\n"
        f"Final Inventory : {inv_str}\n"
        f"Mini-Game Bests : {hs_str}\n"
        "=========================================================\n"
    )
    try:
        with open("playtest_report.txt", "a", encoding="utf-8") as f:
            f.write(report + "\n")
    except Exception:
        pass
    return report


# =========================================================================
# 10. CHAPTER 3: THE 1,024-STATE WORLD EVALUATOR & WAR ENGINE BRIDGES
# =========================================================================
CH3_VICTORY_GOAL = ch3_war_engine.CH3_VICTORY_GOAL
DTESSERA_FACTIONS = ch3_war_engine.DTESSERA_FACTIONS


ROUTE_TO_CH3_FACTION = {
    "Stand for Union Official": "Union",
    "Apply for Town Guard": "Ragmore",
    "Join Castellan's House Staff": "Ragmore",
    "Parvus: F.A.I.-C.N.T. Syndicate": "FAI",
    "Parvus: Crown Intelligencers": "Ragmore",
    "Parvus: Maritime & Artisans Guild (50s)": "Union",
    "Run for Public Office (50s)": "Union",
    "Join Wallmaker Syndicate": "Kokeshi",
    "Become a Highway Robber": "Vanguardists",
    "Join Fairlight's Acting Troupe": "Communards",
}


def evaluate_chapter_3_state(player):
    """
    Reads the 10 binary track outcomes and calculates the Chapter 3
    starting faction, rank, and world summary.
    """
    bits = player.setdefault("ch3_world_bits", {})

    if "track_1" not in bits:
        bits["track_1"] = 1 if player.get("faction_union", 0) >= 2 else 0
    if "track_2" not in bits:
        bits["track_2"] = 1 if player.get("faction_guard", 0) >= 3 else 0
    if "track_3" not in bits:
        bits["track_3"] = 1 if player.get("influence", 0) >= 4 else 0
    if "track_4" not in bits:
        bits["track_4"] = 1 if player.get("faction_union", 0) >= 5 else 0
    if "track_5" not in bits:
        bits["track_5"] = (
            1
            if (bits.get("track_4") == 0 and player.get("faction_guard", 0) >= 4)
            else 0
        )
    if "track_6" not in bits:
        bits["track_6"] = 1 if player.get("silver", 0) >= 150 else 0
    if "track_7" not in bits:
        bits["track_7"] = 1 if player.get("reputation", 0) >= 5 else 0
    if "track_8" not in bits:
        bits["track_8"] = 1 if player.get("faction_wallmakers", 0) >= 5 else 0
    if "track_9" not in bits:
        bits["track_9"] = 1 if player.get("reputation", 0) <= -3 else 0
    if "track_10" not in bits:
        bits["track_10"] = 1 if player.get("charisma", 0) >= 6 else 0

    # Automatically map the player's Chapter 2 route & choices to their Chapter 3 faction
    route = player.get("chapter_2_route", "")
    if not player.get("ch3_faction"):
        fac = ROUTE_TO_CH3_FACTION.get(route, "Union")
        if route == "Apply for Town Guard" and bits.get("track_2") == 0:
            fac = "Laydere"
        elif (
            route == "Become a Highway Robber"
            and player.get("faction_communards", 0)
            > player.get("faction_vanguardists", 0)
        ):
            fac = "Communards"
        player["ch3_faction"] = fac

    pos = player.get("position_strength", 0)
    tells = player.get("exposure_tells", 0)

    if pos >= 80 and tells <= 1:
        rank = "General"
    elif pos >= 50 and tells <= 2:
        rank = "Captain"
    else:
        rank = "Private"

    player["ch3_start_rank"] = rank
    union_str = (
        "Unified and controlling the farmlands"
        if bits["track_1"]
        else "Splintered and fighting itself"
    )
    watch_str = (
        "Fortified at Ragmore"
        if bits["track_2"]
        else "Defected to Castle Laydere"
    )
    army_str = (
        "Fully mobilised"
        if bits["track_3"]
        else "Mutinous and under-supplied"
    )
    parvus_str = (
        "F.A.I. Commune"
        if bits["track_4"]
        else ("Crown Secured" if bits["track_5"] else "In Chaos")
    )
    fleet_str = (
        "Independent and heavily armed"
        if bits["track_6"]
        else "Requisitioned by the Castellan"
    )
    civic_str = (
        "Independent Tribune elected"
        if bits["track_7"]
        else ("Shadow Syndicate rules" if bits["track_8"] else "Corrupt oligarchy")
    )
    road_str = (
        "Ruled by Outlaws" if bits["track_9"] else "Cleared by martial law"
    )
    pop_str = (
        "Rallied to sovereignty" if bits["track_10"] else "Suppressed in fear"
    )

    my_fac = player.get("ch3_faction", "Union")
    summary = (
        f"--- CHAPTER 3: THE EVE OF WAR ({my_fac.upper()} — {rank.upper()}) ---\n"
        f"• The Union: {union_str}.\n"
        f"• The Watch: {watch_str}.\n"
        f"• Ragmore Army: {army_str}.\n"
        f"• Parvus Port: {parvus_str}.\n"
        f"• The Guild Fleet: {fleet_str}.\n"
        f"• Civic Government: {civic_str}.\n"
        f"• The Highways: {road_str}.\n"
        f"• The Populace: {pop_str}.\n"
    )
    return rank, summary


def init_ch3_morning_phase(player):
    """
    Initialises the Chapter 3 Morning Phase state, generating the dice
    pool with penalties based on Chapter 2 survival stats.
    """
    rank = player.get("ch3_rank", "Private").lower()
    my_fac = player.get("ch3_faction", "Union")
    sympathy = (
        player.get("ch3_factions", {})
        .get(my_fac, {})
        .get("sympathy", player.get("faction_sympathy_score", 10))
    )

    if rank == "general":
        pool_size = (
            (player.get("influence", 0) // 2)
            + (sympathy // 4)
            + random.randint(1, 6)
        )
    elif rank == "captain":
        stat = max(player.get("strength", 0), player.get("charisma", 0))
        pool_size = (stat // 2) + random.randint(1, 6)
    else:
        stat = max(player.get("strength", 0), player.get("stealth", 0))
        pool_size = (stat // 2) + random.randint(1, 3)

    afflictions = player.get("afflictions", [])
    if any(
        a in afflictions
        for a in ("food_poisoning", "wound_infection", "damp_chill")
    ):
        pool_size -= 1
    if player.get("hunger", 100) <= 0:
        pool_size -= 2

    pool_size = max(2, min(12, pool_size))

    dice = []
    for idx in range(int(pool_size)):
        val = random.randint(1, 6)
        if afflictions and val > 4:
            val = 4
        dice.append({
            "id": idx,
            "value": val,
            "rect": None,
            "slotted_in": None,
            "is_dragging": False,
        })

    if rank == "general":
        slots = {
            "muster_troops": {
                "name": "Muster Reinforcements (Any)",
                "rect": None,
                "req": None,
                "dice_objs": [],
            },
            "supply_lines": {
                "name": "Secure Supply Lines (Needs 5-6)",
                "rect": None,
                "req": [5, 6],
                "dice_objs": [],
            },
        }
    elif rank == "captain":
        slots = {
            "distribute_rations": {
                "name": "Distribute Rations (Any)",
                "rect": None,
                "req": None,
                "dice_objs": [],
            },
            "build_barricades": {
                "name": "Build Defences (Pairs)",
                "rect": None,
                "req": "pair",
                "dice_objs": [],
            },
        }
    else:
        slots = {
            "execute_order": {
                "name": "Execute Captain's Order (Any)",
                "rect": None,
                "req": None,
                "dice_objs": [],
            },
            "scrounge": {
                "name": "Scrounge for Rations (Needs 6)",
                "rect": None,
                "req": [6],
                "dice_objs": [],
            },
        }

    player["ch3_morning_dice"] = dice
    player["ch3_morning_slots"] = slots
    player["ch3_phase_status"] = "allocating"
    player["ch3_tools_used_today"] = []
    player["ch3_dice_anim_until"] = int(random.uniform(700, 900))
    return player


def resolve_ch3_combat(
    player, attacker_army, defender_army, terrain_region, has_barricades
):
    """
    Resolves a Chapter 3 tactical engagement using dice pools and
    faction advantages. Returns (attacker_won, combat_log).
    """
    att_faction = attacker_army.get("faction", "Unknown")
    def_faction = defender_army.get("faction", "Unknown")

    att_dice_count = max(1, attacker_army.get("count", 1))
    def_dice_count = max(1, defender_army.get("count", 1))

    if "town" in terrain_region or "mountain" in terrain_region:
        def_dice_count += 2

    combat_log = f"*** ENGAGEMENT IN THE {terrain_region.upper()}! ***\n"
    combat_log += (
        f"{att_faction} ({att_dice_count} troops) vs "
        f"{def_faction} ({def_dice_count} garrison)\n"
    )

    if att_faction == "Ragmore" and "road" in terrain_region:
        volley = random.randint(1, 6)
        def_dice_count = max(1, def_dice_count - (volley // 2))
        combat_log += (
            "Ragmore Archers loose a devastating volley! "
            f"(Defender loses {volley // 2} dice)\n"
        )

    att_rolls = [random.randint(1, 6) for _ in range(att_dice_count)]
    def_rolls = [random.randint(1, 6) for _ in range(def_dice_count)]

    if att_faction == "Union":
        if attacker_army.get("count", 1) > defender_army.get("count", 1):
            att_rolls.append(random.randint(1, 6))
            combat_log += "Union overwhelms with sheer numbers! (+1 Die)\n"
        if has_barricades and att_rolls:
            min_idx = att_rolls.index(min(att_rolls))
            att_rolls[min_idx] = 6
            combat_log += (
                "Union barricades hold firm! (Lowest die becomes a 6)\n"
            )

    if att_faction == "Laydere":
        att_rolls = [random.randint(2, 6) if r == 1 else r for r in att_rolls]
        combat_log += "Laydere polearms strike true! (Re-rolled 1s)\n"

    if player.get("ch3_sabotage_active") or (
        att_faction in ("Kokeshi", "FAI")
        and player.get("silver", 0) >= 10
        and not player.get("ch3_evening_resolve_rect")
    ):
        if not player.get("ch3_sabotage_active"):
            player["silver"] -= 10
        if def_rolls:
            def_rolls.remove(max(def_rolls))
            combat_log += (
                "Syndicate sabotage! (Defender highest die discarded)\n"
            )

    att_total = sum(att_rolls)
    def_total = sum(def_rolls)

    combat_log += f"\n{att_faction} Roll: {att_total} {att_rolls}\n"
    combat_log += f"{def_faction} Roll: {def_total} {def_rolls}\n"

    attacker_won = att_total > def_total
    if att_total == def_total and att_faction == "Laydere":
        attacker_won = True
        combat_log += "Laydere discipline breaks the deadlock!\n"

    if attacker_won:
        combat_log += f"\n*** VICTORY! {att_faction} seizes the territory! ***"
    else:
        combat_log += f"\n*** DEFEAT! {def_faction} repels the assault! ***"

    player["ch3_att_rolls"] = att_rolls
    player["ch3_def_rolls"] = def_rolls
    return attacker_won, combat_log


def init_chapter_3_world_board(player, world_map_ref=None):
    """Delegates Day 1 board setup to ch3_war_engine."""
    w_map = world_map_ref if world_map_ref is not None else world_map
    return ch3_war_engine.init_chapter_3_world_board(player, w_map)


def calculate_ch1_ch2_legacy_points(player, faction_key):
    """Delegates Legacy Foundation calculation to ch3_war_engine."""
    return ch3_war_engine.calculate_ch1_ch2_legacy_points(player, faction_key)


def recalculate_ch3_total_points(player):
    """Delegates 100-Point Hegemony calculation to ch3_war_engine."""
    return ch3_war_engine.recalculate_ch3_total_points(player)


def execute_rank_political_action(player, action_key, target_faction=None):
    """Delegates Rank Command Deck actions to ch3_war_engine."""
    return ch3_war_engine.execute_rank_political_action(
        player, action_key, target_faction
    )


def assign_daily_orders(player, world_map_ref=None):
    """Delegates daily order generation to ch3_war_engine."""
    w_map = world_map_ref if world_map_ref is not None else world_map
    return ch3_war_engine.assign_daily_orders(player, w_map)


def start_private_afternoon_march(player, world_map_ref=None):
    """Delegates the Private's Afternoon RPG toggle to ch3_war_engine."""
    w_map = world_map_ref if world_map_ref is not None else world_map
    return ch3_war_engine.start_private_afternoon_march(player, w_map)


def check_private_afternoon_progress(
    player, world_map_ref=None, action_taken="move"
):
    """Delegates the Private's field progress check to ch3_war_engine."""
    w_map = world_map_ref if world_map_ref is not None else world_map
    return ch3_war_engine.check_private_afternoon_progress(
        player, w_map, action_taken
    )


def calculate_ch3_movement_cost(
    player, army_faction, target_pos, world_map_ref=None
):
    """Delegates Afternoon movement & weather cost math to ch3_war_engine."""
    w_map = world_map_ref if world_map_ref is not None else world_map
    return ch3_war_engine.calculate_ch3_movement_cost(
        player, army_faction, target_pos, w_map
    )


def init_ch3_evening_clash(
    player, attacker_info, defender_info, tile_pos, world_map_ref=None
):
    """Delegates Evening Clash / Siege setup to ch3_combat_engine."""
    w_map = world_map_ref if world_map_ref is not None else world_map
    return ch3_combat_engine.init_ch3_evening_clash(
        player, attacker_info, defender_info, tile_pos, w_map
    )


def execute_ch3_combat_action(player, action_type):
    """Delegates Evening Clash button actions to ch3_combat_engine."""
    return ch3_combat_engine.execute_ch3_combat_action(player, action_type)
