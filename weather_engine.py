import math
import random
import pygame
from ui_components import draw_fitted_text
import game_data as db
from map_data import world_map


# =========================================================================
# 1. WEATHER DEGREES, INTENSITIES & SEASONAL TABLES
# =========================================================================
WEATHER_TYPES = {
    # --- SUNSHINE & CLEAR ---
    "blistering_sun": {
        "name": "Blistering Heatwave",
        "category": "SUN",
        "intensity": 3,
        "sat_delta": -10,
        "snow_delta": -15,
        "thirst_mult": 1.6,
        "visibility": 1.0,
        "tint": (255, 210, 110, 28),
        "desc": "A brassy, scorching sun beats down from a cloudless sky, baking the earth and parching your throat.",
    },
    "bright_sun": {
        "name": "Bright Sunshine",
        "category": "SUN",
        "intensity": 2,
        "sat_delta": -7,
        "snow_delta": -10,
        "thirst_mult": 1.15,
        "visibility": 1.0,
        "tint": (255, 240, 180, 15),
        "desc": "Warm, golden sunlight spills across the landscape.",
    },
    "dappled_sun": {
        "name": "Crisp & Clear",
        "category": "SUN",
        "intensity": 1,
        "sat_delta": -5,
        "snow_delta": -4,
        "thirst_mult": 1.0,
        "visibility": 1.0,
        "tint": None,
        "desc": "High,scattered clouds drift across a clear sky.",
    },

    # --- MIST & OVERCAST ---
    "overcast": {
        "name": "Grey Overcast",
        "category": "CLOUD",
        "intensity": 1,
        "sat_delta": -3,
        "snow_delta": -1,
        "thirst_mult": 1.0,
        "visibility": 0.9,
        "tint": (130, 138, 148, 25),
        "desc": "A low ceiling of slate-grey cloud hangs over the horizon.",
    },
    "thick_fog": {
        "name": "Thick Brumaire Fog",
        "category": "FOG",
        "intensity": 2,
        "sat_delta": -1,
        "snow_delta": 0,
        "thirst_mult": 0.95,
        "visibility": 0.55,
        "tint": (185, 195, 200, 55),
        "desc": "Clammy white fog curls over the hollows and river-reeds, muffling distant sounds.",
    },

    # --- RAIN DEGREES & THUNDERSTORMS ---
    "light_rain": {
        "name": "Light Drizzle & Showers",
        "category": "RAIN",
        "intensity": 1,
        "sat_delta": 3,
        "snow_delta": -5,
        "thirst_mult": 0.9,
        "visibility": 0.85,
        "tint": (90, 115, 145, 35),
        "desc": "A steady, fine drizzle stipples the puddles and dampens your cloak.",
    },
    "heavy_rain": {
        "name": "Heavy Driving Rain",
        "category": "RAIN",
        "intensity": 2,
        "sat_delta": 7,
        "snow_delta": -8,
        "thirst_mult": 0.85,
        "visibility": 0.70,
        "tint": (60, 85, 120, 55),
        "desc": "Sheets of cold, driving rain slant across the country, churning dirt tracks into mud.",
    },
    "torrential_rain": {
        "name": "Torrential Downpour",
        "category": "RAIN",
        "intensity": 3,
        "sat_delta": 13,
        "snow_delta": -12,
        "thirst_mult": 0.8,
        "visibility": 0.50,
        "tint": (40, 62, 95, 75),
        "desc": "A blinding deluge hammers the earth, overflowing ditches and swelling every stream!",
    },
    "thunder_lightning": {
        "name": "Thunder & Lightning Storm",
        "category": "STORM",
        "intensity": 4,
        "sat_delta": 15,
        "snow_delta": -10,
        "thirst_mult": 0.85,
        "visibility": 0.45,
        "tint": (35, 40, 75, 85),
        "desc": "Forked lightning splits the blackened sky followed by ear-splitting claps of thunder and lashing rain!",
    },

    # --- HAIL & SNOW DEGREES ---
    "hail_storm": {
        "name": "Bitter Hailstorm",
        "category": "HAIL",
        "intensity": 3,
        "sat_delta": 5,
        "snow_delta": 5,
        "thirst_mult": 1.0,
        "visibility": 0.55,
        "tint": (140, 165, 185, 60),
        "desc": "Hard pellets of ice rattle painfully against roofs, shields, and exposed skin!",
    },
    "light_snow": {
        "name": "Light Snow Flurries",
        "category": "SNOW",
        "intensity": 1,
        "sat_delta": 1,
        "snow_delta": 5,
        "thirst_mult": 1.0,
        "visibility": 0.80,
        "tint": (215, 225, 240, 35),
        "desc": "Soft white snowflakes drift down on a freezing wind, dusting the ruts and roofs.",
    },
    "heavy_snow": {
        "name": "Heavy Snowfall",
        "category": "SNOW",
        "intensity": 2,
        "sat_delta": 2,
        "snow_delta": 12,
        "thirst_mult": 1.1,
        "visibility": 0.60,
        "tint": (225, 235, 250, 55),
        "desc": "Thick, swirling snow buries boundary stones and piles deep drifts across the roads!",
    },
    "blizzard": {
        "name": "Howling Whiteout Blizzard",
        "category": "SNOW",
        "intensity": 4,
        "sat_delta": 3,
        "snow_delta": 22,
        "thirst_mult": 1.25,
        "visibility": 0.35,
        "tint": (235, 242, 255, 80),
        "desc": "A ferocious, sub-zero gale drives blinding walls of snow sideways across the frozen land!",
    },
}


# Republican Calendar Month Profiles (0 = Vendémiaire .. 11 = Fructidor)
# Each entry defines: (base_temp_c, dawn_decimal_hr, dusk_decimal_hr, weighted_weather_table)
MONTH_PROFILES = {
    0: (  # Vendémiaire (Sep/Oct — Early Autumn)
        13, 2.5, 7.5,
        [("dappled_sun", 28), ("bright_sun", 18), ("overcast", 22), ("thick_fog", 12), ("light_rain", 12), ("heavy_rain", 6), ("thunder_lightning", 2)],
    ),
    1: (  # Brumaire (Oct/Nov — Month of Fog & Autumn Rains)
        7, 2.9, 7.1,
        [("thick_fog", 26), ("overcast", 20), ("light_rain", 20), ("heavy_rain", 16), ("torrential_rain", 7), ("dappled_sun", 8), ("hail_storm", 3)],
    ),
    2: (  # Frimaire (Nov/Dec — Month of Frost & Sleet)
        2, 3.2, 6.8,
        [("overcast", 22), ("thick_fog", 15), ("light_snow", 18), ("heavy_rain", 14), ("hail_storm", 10), ("heavy_snow", 8), ("dappled_sun", 10), ("blizzard", 3)],
    ),
    3: (  # Nivôse (Dec/Jan — Deep Winter Snow)
        -3, 3.4, 6.6,
        [("light_snow", 25), ("heavy_snow", 22), ("blizzard", 12), ("hail_storm", 10), ("overcast", 18), ("dappled_sun", 13)],
    ),
    4: (  # Pluviôse (Jan/Feb — Winter Rain, Sleet & Ice)
        1, 3.2, 6.8,
        [("heavy_rain", 22), ("torrential_rain", 12), ("light_snow", 18), ("heavy_snow", 14), ("hail_storm", 12), ("overcast", 14), ("dappled_sun", 8)],
    ),
    5: (  # Ventôse (Feb/Mar — Windy Late Winter)
        6, 2.8, 7.2,
        [("overcast", 24), ("light_rain", 20), ("heavy_rain", 15), ("dappled_sun", 20), ("hail_storm", 8), ("light_snow", 8), ("bright_sun", 5)],
    ),
    6: (  # Germinal (Mar/Apr — Spring Buds & Showers)
        11, 2.4, 7.6,
        [("dappled_sun", 26), ("bright_sun", 20), ("light_rain", 22), ("heavy_rain", 12), ("overcast", 14), ("thunder_lightning", 6)],
    ),
    7: (  # Floréal (Apr/May — Flowering Late Spring)
        16, 2.1, 8.2,
        [("bright_sun", 32), ("dappled_sun", 28), ("light_rain", 18), ("overcast", 12), ("heavy_rain", 6), ("thunder_lightning", 4)],
    ),
    8: (  # Prairial (May/Jun — Early Summer Meadows)
        20, 1.9, 8.6,
        [("bright_sun", 40), ("dappled_sun", 26), ("blistering_sun", 10), ("light_rain", 12), ("thunder_lightning", 7), ("overcast", 5)],
    ),
    9: (  # Messidor (Jun/Jul — High Summer Harvest)
        24, 1.8, 8.8,
        [("bright_sun", 42), ("blistering_sun", 24), ("dappled_sun", 18), ("thunder_lightning", 8), ("torrential_rain", 4), ("light_rain", 4)],
    ),
    10: (  # Thermidor (Jul/Aug — Dog Days of Heat)
        26, 2.0, 8.5,
        [("blistering_sun", 32), ("bright_sun", 38), ("dappled_sun", 14), ("thunder_lightning", 10), ("torrential_rain", 6)],
    ),
    11: (  # Fructidor (Aug/Sep — Late Summer Fruit & Equinoctial Squalls)
        19, 2.3, 7.9,
        [("bright_sun", 34), ("dappled_sun", 24), ("light_rain", 14), ("heavy_rain", 10), ("thunder_lightning", 10), ("blistering_sun", 8)],
    ),
}


# =========================================================================
# 2. CALENDAR, DAYLIGHT & TEMPERATURE CALCULATORS
# =========================================================================
def get_calendar_metrics(total_mins):
    """Returns (month_index 0..11, day_of_month 1..30, decimal_hour_float 0.0..10.0)."""
    total_days = (total_mins // 1000) + 34
    day_of_year = total_days % 365
    month_idx = min(11, day_of_year // 30)
    day_of_month = (day_of_year % 30) + 1
    dec_hour = (total_mins % 1000) / 100.0
    return month_idx, day_of_month, dec_hour


def get_daylight_state(player):
    """
    Calculates whether it is DAY, TWILIGHT (Dawn/Dusk), or NIGHT based on the Northern Hemisphere month!
    Also checks if the player has an active Torch or Storm Lantern.
    Returns dict with keys: phase, dawn_hr, dusk_hr, is_dark, has_light, light_source_name.
    """
    m_idx, _, dec_hr = get_calendar_metrics(player.get("total_game_minutes", 0))
    _, dawn_hr, dusk_hr, _ = MONTH_PROFILES[m_idx]

    if dawn_hr <= dec_hr <= dusk_hr:
        phase = "DAY"
    elif (dawn_hr - 0.5) <= dec_hr < dawn_hr or dusk_hr < dec_hr <= (dusk_hr + 0.5):
        phase = "TWILIGHT"
    else:
        phase = "NIGHT"

    inv = player.get("inventory", [])
    torch_mins = player.get("torch_minutes_left", 0)
    has_lantern = "storm lantern" in inv
    has_lit_torch = torch_mins > 0

    has_light = (phase != "NIGHT") or has_lantern or has_lit_torch
    if has_lantern:
        light_name = "Storm Lantern"
    elif has_lit_torch:
        light_name = f"Lit Torch ({int(torch_mins)}m)"
    else:
        light_name = "None"

    return {
        "phase": phase,
        "dawn_hr": dawn_hr,
        "dusk_hr": dusk_hr,
        "is_dark": (phase == "NIGHT" and not has_light),
        "has_light": has_light,
        "light_source": light_name,
    }


def ensure_weather_initialized(player):
    """Initializes persistent weather state on the player dict if not yet present."""
    if "weather_current" not in player:
        player["weather_current"] = "thick_fog"
        player["weather_temp_c"] = 8
        player["ground_saturation"] = 35  # 0..100% (65%+ = Muddy Quagmire, 85%+ = River Flooding!)
        player["snowpack_level"] = 0      # 0..100% (50%+ = Icy/Snowbound Passes!)
        player["last_weather_roll_chunk"] = player.get("total_game_minutes", 0) // 250
        player["torch_minutes_left"] = 0


def update_weather_on_time_advance(player, minutes_elapsed, world_map=None):
    """
    Called automatically inside advance_time() in mechanics.py!
    Updates weather every 250 decimal minutes (2.5 decimal hours), tracks cumulative
    ground saturation & snowpack, and drains lit torches.
    Returns a list of atmospheric log alerts if weather shifts or hazards trigger.
    """
    ensure_weather_initialized(player)
    alerts = []

    # 1. Burn down active torch if lit
    if player.get("torch_minutes_left", 0) > 0:
        w_cur = player.get("weather_current", "overcast")
        # Heavy rain or blizzards snuff out open pine torches unless under a roof!
        if w_cur in ("torrential_rain", "thunder_lightning", "blizzard") and not player.get("current_building"):
            player["torch_minutes_left"] = 0
            alerts.append("*** The howling storm snuffs out your open pine torch! (A brass Storm Lantern won't blow out!) ***")
        else:
            player["torch_minutes_left"] = max(0, player["torch_minutes_left"] - minutes_elapsed)
            if player["torch_minutes_left"] == 0:
                alerts.append("*** Your pine torch sputters and burns out into darkness! ***")

    # 2. Check if 250-minute weather window has ticked over
    cur_chunk = player.get("total_game_minutes", 0) // 250
    last_chunk = player.get("last_weather_roll_chunk", cur_chunk)

    if cur_chunk > last_chunk:
        chunks_passed = min(8, cur_chunk - last_chunk)
        player["last_weather_roll_chunk"] = cur_chunk

        m_idx, _, dec_hr = get_calendar_metrics(player.get("total_game_minutes", 0))
        base_temp, dawn_hr, dusk_hr, table = MONTH_PROFILES[m_idx]

        # Regional altitude modifier (Caligo Mountains are -6°C colder!)
        pos = (player.get("x", 8), player.get("y", 14))
        reg = ""
        if world_map and pos in world_map:
            reg = world_map[pos].region

        alt_mod = -6 if "Caligo" in reg or "Mountain" in reg else (2 if "Parvus" in reg else 0)
        night_mod = -4 if (dec_hr < dawn_hr or dec_hr > dusk_hr) else 2

        for _ in range(chunks_passed):
            # 45% chance weather persists (creating multi-day rain streaks or heatwaves!), 55% chance to roll seasonal table
            if random.random() < 0.55 or player["weather_current"] not in WEATHER_TYPES:
                keys = [k for k, _ in table]
                weights = [w for _, w in table]
                chosen = random.choices(keys, weights=weights, k=1)[0]
            else:
                chosen = player["weather_current"]

            temp_c = base_temp + alt_mod + night_mod + random.randint(-3, 3)

            # If temperature is <= 0°C, rain automatically freezes into Snow or Hail!
            if temp_c <= 0 and chosen in ("light_rain", "heavy_rain", "torrential_rain"):
                chosen = "light_snow" if chosen == "light_rain" else ("heavy_snow" if chosen == "heavy_rain" else "blizzard")
            # Conversely, if temperature is > 4°C, snow melts into rain!
            elif temp_c > 4 and chosen in ("light_snow", "heavy_snow", "blizzard"):
                chosen = "light_rain" if chosen == "light_snow" else "heavy_rain"

            player["weather_current"] = chosen
            player["weather_temp_c"] = temp_c

            w_spec = WEATHER_TYPES[chosen]
            old_sat = player.get("ground_saturation", 35)
            old_snow = player.get("snowpack_level", 0)

            player["ground_saturation"] = max(0, min(100, old_sat + w_spec["sat_delta"]))
            player["snowpack_level"] = max(0, min(100, old_snow + w_spec["snow_delta"]))

        w_spec = WEATHER_TYPES[player["weather_current"]]
        alerts.append(f"[Weather Shift: {w_spec['name']} ({player['weather_temp_c']}°C) — {w_spec['desc']}]")

        # Warn if cumulative rain has triggered Flooding or Quagmires!
        sat = player["ground_saturation"]
        snow = player["snowpack_level"]
        if sat >= 85:
            alerts.append("*** FLOOD WARNING: Weeks of relentless rain have pushed Ground Saturation to 85%+! The River Fluvius is in flood and low sunken paths are submerged! ***")
        elif sat >= 65:
            alerts.append("*** QUAGMIRE WARNING: Heavy rains have waterlogged the country (Saturation 65%+). Unpaved tracks and farmlands are axle-deep in mud! ***")
        if snow >= 60:
            alerts.append("*** SNOWBOUND & ICY: Deep snowdrifts and black ice cover the passes (Snowpack 60%+). Wear Ice Crampons and Warm Winter Clothes! ***")

    # 3. Apply Exposure / Gear Checks when outdoors
    if not player.get("current_building") and minutes_elapsed >= 15:
        w_spec = WEATHER_TYPES.get(player.get("weather_current", "overcast"), WEATHER_TYPES["overcast"])
        temp_c = player.get("weather_temp_c", 10)
        inv = player.get("inventory", [])

        # Rain Exposure Check (Heavy/Torrential Rain without a Waxed Jacket)
        if w_spec["category"] in ("RAIN", "STORM") and w_spec["intensity"] >= 2:
            if "waxed jacket" not in inv:
                player["hunger"] = max(0, round(player.get("hunger", 100) - 1.5, 1))
                if w_spec["intensity"] >= 3 and temp_c <= 8 and random.random() < 0.25:
                    player["health"] = max(1, player["health"] - 1)
                    alerts.append("*** Soaked to the bone in the freezing downpour without a Waxed Jacket! (-1 Health) ***")

        # Freezing Cold / Snow / Hail Check (Temp <= 0°C or Hail without Warm Winter Coat / Blanket)
        if temp_c <= 0 or w_spec["category"] in ("SNOW", "HAIL"):
            has_warmth = ("warm winter coat" in inv) or ("heavy winter blanket" in inv)
            if not has_warmth and random.random() < 0.35:
                player["health"] = max(1, player["health"] - 1)
                alerts.append(f"*** Bitter {temp_c}°C frost bites through your thin clothes! Equip a Warm Winter Coat or Heavy Winter Blanket! (-1 Health) ***")
            # Horse chill check if riding without Heavy Winter Blanket or Horse Armour
            if player.get("riding_horse") and "heavy winter blanket" not in inv and "horse armour" not in inv:
                player["horse_hunger"] = max(0, player.get("horse_hunger", 100) - 2.0)

        # Heatwave Thirst Drain
        if w_spec["thirst_mult"] > 1.2:
            extra_thirst = round((minutes_elapsed / 25.0) * (w_spec["thirst_mult"] - 1.0), 1)
            player["thirst"] = max(0, round(player.get("thirst", 100) - extra_thirst, 1))

    return alerts


# =========================================================================
# 3. MOVEMENT, FLOODING, ICE & SWIMMING OBSTACLE ENGINE
# =========================================================================
LAKE_REGIONS = {"Ragmore Lake", "Diluvium Lake", "Calluna Lake", "The Mountain Lake"}
RIVER_SEA_REGIONS = {"The River Fluvius", "Dtessera Sea"}

def get_tile_altitude_and_temp(player, pos, world_map):
    """
    Returns (altitude_tier 0..5, elevation_m, local_temp_c) for any coordinate on the map.
    Applies the Northern Hemisphere adiabatic lapse rate (-1°C at 60m, -3°C at 180m, -6°C at 450m).
    """
    room = world_map.get(pos) if world_map else None
    alt = getattr(room, "altitude", 2) if room else 2
    elev_m = {0: 0, 1: 5, 2: 20, 3: 60, 4: 180, 5: 450}.get(alt, 20)

    lapse_table = {0: 0, 1: 0, 2: 0, 3: -1, 4: -3, 5: -6}
    base_sea_temp = player.get("weather_temp_c", 10)
    local_temp = base_sea_temp + lapse_table.get(alt, 0)
    return alt, elev_m, local_temp


def find_adjacent_high_ground_hint(curr_pos, world_map, min_alt=2):
    """
    Scans the 4 cardinal neighbors of the player's current position to see which directions
    offer higher ground (altitude >= min_alt) to circumvent a flooded hollow!
    """
    cx, cy = curr_pos
    dirs = [("North", (cx, cy + 1)), ("South", (cx, cy - 1)), ("East", (cx + 1, cy)), ("West", (cx - 1, cy))]
    high_options = []
    for d_name, n_pos in dirs:
        n_room = world_map.get(n_pos)
        if n_room and getattr(n_room, "altitude", 2) >= min_alt and n_room.region not in ("Dtessera Sea", "The River Fluvius"):
            high_options.append(f"**{d_name}** ({n_room.name}, {getattr(n_room, 'elevation_m', 60)}m)")
    if high_options:
        return "Higher ground available to circumvent the flood: " + ", ".join(high_options) + "."
    return "Seek higher upland ridges (60m+) to bypass the flooded basin."


def check_movement_weather_and_swim(player, target_x, target_y, world_map):
    """
    Altitude-driven hydrological & weather movement engine!
    Compares the target tile's Altitude Tier (0..5) against Ground Saturation and Snowpack.
    """
    ensure_weather_initialized(player)
    dest_room = world_map.get((target_x, target_y))
    if not dest_room:
        return True, None, 0, ""

    reg = dest_room.region
    r_name = dest_room.name
    alt, elev_m, local_temp_c = get_tile_altitude_and_temp(player, (target_x, target_y), world_map)

    inv = player.get("inventory", [])
    skills = player.get("skills", [])
    sat = player.get("ground_saturation", 35)
    snow = player.get("snowpack_level", 0)
    w_key = player.get("weather_current", "overcast")

    notes = []
    extra_mins = 0

    # ------------------------------------------------------------------
    # A. TIER 0 WATER BODIES: LAKES (SAFE IF TRAINED) VS. RIVERS (DANGEROUS!)
    # ------------------------------------------------------------------
    is_lake = (reg in LAKE_REGIONS) or ("Lake" in r_name)
    is_dangerous_water = (reg in RIVER_SEA_REGIONS)

    if is_lake:
        if "swim" not in skills:
            return False, None, 0, (
                f"You halt at the shore of **{r_name}** ({elev_m}m). You must learn the **Swim** skill before entering deep lakes!"
            )
        if player.get("riding_horse"):
            return False, None, 0, "Your horse refuses to swim out into the deep lake! Dismount first."
        extra_mins += 10
        if local_temp_c <= 4 and "heavy winter blanket" not in inv:
            player["health"] = max(1, player["health"] - 1)
            notes.append(f"You swim across **{r_name}**, though the {local_temp_c}°C glacial water chills you (-1 Health)!")
        else:
            notes.append(f"You swim smoothly across the calm waters of **{r_name}**.")

    elif is_dangerous_water:
        if "swim" not in skills and "rope" not in inv:
            return False, None, 0, (
                f"The rushing current of **{r_name}** is too dangerous to ford without the **Swim** skill, a **Rope**, or a **Tier 3 Stone Bridge**!"
            )
        flood_penalty = 3 if sat >= 75 else (1 if sat >= 55 else 0)
        target_dc = 8 + flood_penalty
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        swim_roll = d1 + d2 + (player.get("strength", 0) // 2) + (2 if "swim" in skills else 0) + (2 if "rope" in inv else 0)

        if swim_roll >= target_dc:
            extra_mins += 20
            notes.append(
                f"[River Ford Roll: {d1}+{d2}+Bonus = {swim_roll} vs DC {target_dc}: SUCCESS!] "
                f"Bracing against the current of **{r_name}**, you fight your way across!"
            )
        else:
            dmg = 2 if sat >= 75 else 1
            player["health"] = max(1, player["health"] - dmg)
            swept_y = max(1, target_y - 1)
            swept_pos = (target_x, swept_y) if (target_x, swept_y) in world_map else (target_x, target_y)
            swept_name = world_map[swept_pos].name if swept_pos in world_map else "the lower riverbank"
            return True, swept_pos, 30, (
                f"*** SWEPT DOWNSTREAM BY THE CURRENT! [Roll {swim_roll} < DC {target_dc}] ***\n"
                f"The swollen current of **{r_name}** sweeps you off your feet (-{dmg} Health) and carries you downstream to **{swept_name}**!"
            )

    # ------------------------------------------------------------------
    # B. ALTITUDE-DRIVEN FLOODING & HIGH-GROUND CIRCUMVENTION
    # ------------------------------------------------------------------
    # 1. TIER 1 (5m Sunken Hollows & Basins): Quagmire at 55%+, Submerged Flood at 75%+!
    if alt == 1:
        if sat >= 75:
            high_hint = find_adjacent_high_ground_hint((player["x"], player["y"]), world_map, min_alt=2)
            if player.get("riding_horse"):
                return False, None, 0, (
                    f"*** TIER 1 BASIN FLOODED ({r_name} — {elev_m}m ASL | Saturation {sat}%)! ***\n"
                    f"Runoff from the surrounding hills has submerged this low hollow under four feet of water! Your horse cannot pass.\n"
                    f"• **Navigator's Tip:** {high_hint}"
                )
            if "swim" not in skills and "rope" not in inv and player.get("strength", 0) < 5:
                return False, None, 0, (
                    f"*** IMPASSABLE FLOODED HOLLOW ({r_name} — {elev_m}m ASL | Saturation {sat}%)! ***\n"
                    f"This 5m sunken basin is flooded waist-deep! You need **Swim**, a **Rope**, or **5+ Strength** to wade through—or detour via higher ground!\n"
                    f"• **Navigator's Tip:** {high_hint}"
                )
            extra_mins += 25
            notes.append(
                f"[Flooded Tier 1 Hollow ({elev_m}m ASL, {sat}% Sat): +25m] You wade chest-deep through the submerged basin of **{r_name}**!"
            )
        elif sat >= 55:
            extra_mins += 15
            notes.append(
                f"[Waterlogged Tier 1 Hollow ({elev_m}m ASL): +15m] Runoff pools in this low 5m depression, turning the track into ankle-deep mire."
            )

    # 2. TIER 2 (20m Lowland Floodplain): Firm until 70%+, Quagmire at 70%+, Floods at 90%+ Deluge!
    elif alt == 2 and reg not in ("Fluvius Town", "Parvus Town"):
        if sat >= 90:
            high_hint = find_adjacent_high_ground_hint((player["x"], player["y"]), world_map, min_alt=3)
            if player.get("riding_horse") and player.get("equusense", 0) < 5:
                return False, None, 0, (
                    f"*** CATASTROPHIC FLOODPLAIN INUNDATION ({r_name} — {elev_m}m ASL | Saturation {sat}%)! ***\n"
                    f"The 20m floodplain is completely underwater! Take the **Tier 3 High Ground (60m+)** to circumvent the flood!\n"
                    f"• **Navigator's Tip:** {high_hint}"
                )
            extra_mins += 20
            notes.append(f"[Inundated 20m Floodplain ({sat}% Sat): +20m] Sheet-water covers the lowland fields! ({high_hint})")
        elif sat >= 70:
            extra_mins += 10
            notes.append(f"[Muddy 20m Floodplain ({sat}% Sat): +10m] The lowland soil is heavy and sodden. (Tier 3 ridges at 60m remain dry!)")

    # 3. TIER 3 (60m Upland Ridges, Orchards & Stone Bridges): Positive feedback when bypassing floods!
    elif alt == 3 and sat >= 70:
        notes.append(f"[High Ground Advantage ({elev_m}m ASL)]: Taking the elevated {r_name} keeps your boots and hooves high and dry above the flooded hollows!")

    # ------------------------------------------------------------------
    # C. ALTITUDE LAPSE RATE: ALPINE SNOWLINE & BLACK ICE ON TIERS 4 & 5
    # ------------------------------------------------------------------
    if (alt >= 4 and local_temp_c <= 0) or (snow >= 50 and alt >= 3):
        if "ice crampons" not in inv and "climb" not in skills:
            if random.random() < (0.45 if alt == 5 else 0.25):
                player["health"] = max(1, player["health"] - 1)
                extra_mins += 20
                notes.append(
                    f"*** ALPINE BLACK ICE ({elev_m}m ASL, {local_temp_c}°C)! *** "
                    f"At this high elevation, frozen rime coats the rock and you slip hard (-1 Health, +20m)! (Equip **Ice Crampons** for Tier 4–5 ascents!)"
                )
        else:
            notes.append(f"[High Altitude ({elev_m}m ASL, {local_temp_c}°C)]: Your **Ice Crampons** hold firm on the icy crag.")

    # ------------------------------------------------------------------
    # D. NIGHT-TIME DARKNESS CHECK
    # ------------------------------------------------------------------
    light_info = get_daylight_state(player)
    if light_info["is_dark"] and reg not in ("Murum Town", "Fluvius Town", "Parvus Town"):
        extra_mins += 15
        if player.get("stealth", 0) < 5 and random.random() < 0.30:
            player["health"] = max(1, player["health"] - 1)
            notes.append(
                "*** PITCH DARKNESS! *** Moving through the unlit wilds at night without a **Lit Torch** or **Storm Lantern**, you stumble in the dark (-1 Health, +15m)!"
            )
        else:
            notes.append("[Night Travel (Unlit): +15m] You pick your way slowly through the darkness.")

    return True, None, extra_mins, "\n".join(notes)


# =========================================================================
# 4. SCREEN OVERLAY & HUD WEATHER BANNER RENDERER
# =========================================================================
def draw_weather_and_darkness_overlay(screen, player, font, font_bold, mouse_pos=None):
    """
    Renders ONLY the compact, clickable Top-Bar Weather & Altitude Status Pill
    (No grey 420x420 box over the background!).
    """
    ensure_weather_initialized(player)
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()

    w_key = player.get("weather_current", "overcast")
    w_spec = WEATHER_TYPES.get(w_key, WEATHER_TYPES["overcast"])
    sat = player.get("ground_saturation", 35)
    light_info = get_daylight_state(player)

    from map_data import world_map
    pos = (player.get("x", 8), player.get("y", 14))
    alt, elev_m, local_temp_c = get_tile_altitude_and_temp(player, pos, world_map)

    if sat >= 75 and alt <= 1:
        ground_tag = "FLOODED HOLLOW!"
    elif sat >= 70 and alt == 2:
        ground_tag = "Muddy Plain"
    elif alt >= 4 and local_temp_c <= 0:
        ground_tag = "Icy Crag"
    else:
        ground_tag = f"Wetness {sat}%"

    bar_txt = (
        f"Alt: {elev_m}m (T{alt}) | {w_spec['name']} ({local_temp_c}°C) | {ground_tag} | "
        f"{light_info['phase']} | Light: {light_info['light_source']}  [Forecast]"
    )
    txt_col = (168, 50, 35) if ((sat >= 75 and alt <= 1) or light_info["is_dark"] or local_temp_c <= 0) else (45, 55, 70)

    is_hover = WEATHER_PILL_RECT.collidepoint(mouse_pos)
    pill_bg = (236, 228, 210) if is_hover else (244, 239, 225)
    pygame.draw.rect(screen, pill_bg, WEATHER_PILL_RECT, border_radius=5)
    pygame.draw.rect(screen, (168, 50, 35), WEATHER_PILL_RECT, width=2, border_radius=5)
    pygame.draw.rect(screen, (28, 28, 28), WEATHER_PILL_RECT.inflate(-2, -2), width=1, border_radius=4)

    from ui_components import draw_fitted_text
    draw_fitted_text(screen, bar_txt, WEATHER_PILL_RECT.inflate(-12, -2), txt_col, bold=is_hover, max_lines=1)


def draw_weather_report_modal(screen, player, world_map, font, font_bold, mouse_pos):
    """
    Renders the 700x500 Tate Britain Meteorological & Hydrological Almanac Pop-Out
    with every text block strictly fitted inside its box using draw_fitted_text!
    """
    from ui_components import draw_fitted_text
    ensure_weather_initialized(player)

    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    SEA_BLUE = (38, 98, 145)

    panel = pygame.Rect(50, 30, 700, 500)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    draw_fitted_text(
        screen, "ROYAL METEOROLOGICAL & HYDROLOGICAL ALMANAC",
        pygame.Rect(75, 40, 650, 24), TATE_RED, bold=True, max_lines=1
    )

    pos = (player.get("x", 8), player.get("y", 14))
    room = world_map.get(pos) if world_map else None
    reg_name = room.region if room else "Dtessera Terra"
    alt, elev_m, local_temp_c = get_tile_altitude_and_temp(player, pos, world_map)
    w_key = player.get("weather_current", "overcast")
    w_spec = WEATHER_TYPES.get(w_key, WEATHER_TYPES["overcast"])
    light_info = get_daylight_state(player)
    sat = player.get("ground_saturation", 35)
    snow = player.get("snowpack_level", 0)

    # 1. Current Conditions & Daylight Box
    cur_box = pygame.Rect(75, 70, 650, 90)
    pygame.draw.rect(screen, (252, 248, 238), cur_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, cur_box, width=2, border_radius=8)

    line1 = f"Location: {reg_name} — Altitude Tier {alt} ({elev_m}m ASL)  |  Local Temp: {local_temp_c}°C"
    line2 = f"Sky: {w_spec['name']}  |  Daylight: {light_info['phase']} (Dawn {light_info['dawn_hr']:.2f}h – Dusk {light_info['dusk_hr']:.2f}h)"
    draw_fitted_text(screen, line1, pygame.Rect(88, 76, 624, 22), CLOCK_BLACK, bold=True, max_lines=1)
    draw_fitted_text(screen, line2, pygame.Rect(88, 98, 624, 22), SEA_BLUE, bold=True, max_lines=1)
    draw_fitted_text(screen, w_spec["desc"], pygame.Rect(88, 120, 624, 34), (80, 75, 70), max_lines=2)

    # 2. Hydrological Ground Saturation & Alpine Snowpack Bars
    hyd_box = pygame.Rect(75, 166, 650, 78)
    pygame.draw.rect(screen, (252, 248, 238), hyd_box, border_radius=8)
    pygame.draw.rect(screen, CLOCK_BLACK, hyd_box, width=1, border_radius=8)

    sat_status = (
        "TIER 1 & 2 FLOODING!" if sat >= 90 else
        ("TIER 1 HOLLOWS FLOODED (Seek 20m-60m High Ground!)" if sat >= 75 else
         ("LOWLAND MIRE (55%+)" if sat >= 55 else "Firm & Passable"))
    )
    draw_fitted_text(
        screen, f"Ground Saturation: {sat}% — {sat_status}",
        pygame.Rect(88, 172, 624, 20), TATE_RED if sat >= 75 else CLOCK_BLACK, bold=True, max_lines=1
    )
    s_bar = pygame.Rect(90, 194, 615, 12)
    pygame.draw.rect(screen, (40, 38, 35), s_bar, border_radius=4)
    if sat > 0:
        s_col = (35, 95, 195) if sat >= 75 else ((165, 110, 45) if sat >= 55 else (55, 135, 70))
        pygame.draw.rect(screen, s_col, (90, 194, int(615 * (sat / 100.0)), 12), border_radius=4)
    pygame.draw.line(screen, (255, 220, 90), (90 + int(615 * 0.55), 192), (90 + int(615 * 0.55), 208), 2)
    pygame.draw.line(screen, TATE_RED, (90 + int(615 * 0.75), 192), (90 + int(615 * 0.75), 208), 2)

    snow_status = "SNOWBOUND & ICY CRAGS (Equip Ice Crampons!)" if (snow >= 50 or local_temp_c <= 0) else "Clear of Snowdrifts"
    draw_fitted_text(
        screen, f"Alpine Snowpack & Ice Glaze: {snow}% — {snow_status}",
        pygame.Rect(88, 214, 624, 22), CLOCK_BLACK, max_lines=1
    )

    # 3. 24-Hour (4-Window) Barometric Forecast Cards
    draw_fitted_text(
        screen, "BAROMETRIC FORECAST — NEXT 4 WINDOWS & 3-DAY OUTLOOK:",
        pygame.Rect(75, 250, 650, 20), TATE_RED, bold=True, max_lines=1
    )
    short_range, day_summaries = generate_barometric_forecast(player, world_map)

    for i, fc in enumerate(short_range):
        cx = 75 + i * 165
        c_rect = pygame.Rect(cx, 272, 155, 88)
        pygame.draw.rect(screen, (34, 38, 46), c_rect, border_radius=6)
        pygame.draw.rect(screen, (185, 140, 45), c_rect, width=1, border_radius=6)

        draw_fitted_text(screen, fc["window"], pygame.Rect(cx + 6, 276, 143, 18), (255, 215, 100), bold=True, max_lines=1)
        draw_fitted_text(screen, fc["name"], pygame.Rect(cx + 6, 296, 143, 22), DIAL_CREAM, max_lines=1)
        draw_fitted_text(
            screen, f"Temp: {fc['temp_c']}°C | Sat: {fc['pred_sat']}%",
            pygame.Rect(cx + 6, 322, 143, 30), (165, 215, 250) if fc["temp_c"] <= 2 else DIAL_CREAM, max_lines=2
        )

    # 4. 3-Day Almanac Strip + Gear Readiness Check (Strictly fitted!)
    alm_box = pygame.Rect(75, 368, 650, 90)
    pygame.draw.rect(screen, (252, 248, 238), alm_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, alm_box, width=1, border_radius=8)

    d_strs = [f"{d_lbl}: {s['name']} ({s['temp_c']}°C, Sat {s['pred_sat']}%)" for d_lbl, s in day_summaries]
    draw_fitted_text(screen, "3-Day Almanac: " + "  |  ".join(d_strs), pygame.Rect(85, 373, 630, 50), CLOCK_BLACK, max_lines=3, align="left")

    inv = player.get("inventory", [])
    gear_tags = [
        f"Rain Coat: {'YES' if 'waxed jacket' in inv else 'NO'}",
        f"Winter Coat: {'YES' if ('warm winter coat' in inv or 'heavy winter blanket' in inv) else 'NO'}",
        f"Crampons: {'YES' if 'ice crampons' in inv else 'NO'}",
        f"Light: {light_info['light_source']}",
        f"Topo Map: {'YES' if 'topographic survey map' in inv else 'NO'}",
    ]
    draw_fitted_text(screen, "Gear Readiness: " + " | ".join(gear_tags), pygame.Rect(85, 420, 630, 30), (35, 120, 55), bold=True, max_lines=2, align="left")


def toggle_topo_map(player):
    """Toggles the Topographic & Flood-Stage overlay if the player owns the Topographic Survey Map."""
    if "topographic survey map" not in player.get("inventory", []):
        player["topo_overlay_active"] = False
        return (
            "You only carry a plain map! To view live **Elevation Contours (`0m–450m`) & Flood Stages**, "
            "you must acquire a **Topographic Survey Map** (available from the Town Hall Clerk, Parvus Guildhall, or Fluvius Bookshop)."
        )
    player["topo_overlay_active"] = not player.get("topo_overlay_active", False)
    state_str = "ENABLED" if player["topo_overlay_active"] else "HIDDEN"
    return f"Topographic & Flood-Stage Survey Map Overlay: **{state_str}**."

def draw_topographic_contour_overlay(screen, player, world_map, map_rect=pygame.Rect(20, 160, 420, 420)):
    """
    When player['topo_overlay_active'] is True, renders a live Topographic & Flood-Stage
    surveyor's grid centered on the player's current position (7x7 visible tile window).
    """
    if not player.get("topo_overlay_active", False) or player.get("current_building") or "topographic survey map" not in player.get("inventory", []):
        return

    ensure_weather_initialized(player)
    sat = player.get("ground_saturation", 35)
    snow = player.get("snowpack_level", 0)
    px, py = player.get("x", 8), player.get("y", 14)

    # Semi-transparent parchment surveyor's backdrop over the map viewport
    backdrop = pygame.Surface((map_rect.width, map_rect.height), pygame.SRCALPHA)
    backdrop.fill((244, 239, 225, 225))
    screen.blit(backdrop, map_rect.topleft)

    cell_w = map_rect.width // 7   # 60px per tile
    cell_h = map_rect.height // 7  # 60px per tile
    small_font = pygame.font.Font(None, 16)
    bold_font = pygame.font.Font(None, 18)

    for gx in range(-3, 4):
        for gy in range(-3, 4):
            tx = px + gx
            ty = py - gy  # Screen Y grows downward, world Y grows northward
            c_rect = pygame.Rect(
                map_rect.left + (gx + 3) * cell_w + 2,
                map_rect.top + (gy + 3) * cell_h + 2,
                cell_w - 4,
                cell_h - 4,
            )

            room = world_map.get((tx, ty))
            if not room:
                pygame.draw.rect(screen, (35, 38, 45), c_rect, border_radius=4)
                continue

            alt, elev_m, local_temp_c = get_tile_altitude_and_temp(player, (tx, ty), world_map)
            base_col = TOPO_TIER_COLORS.get(alt, (110, 145, 85))
            status_tag = f"{elev_m}m"
            border_col = (60, 60, 60)
            border_w = 1

            # Highlight Live Flood, Mire, Ice, and High-Ground Bypass States!
            if alt == 0:
                status_tag = "WATER" if sat < 75 else "SWOLLEN"
            elif (alt == 1 and sat >= 75) or (alt == 2 and sat >= 90 and room.region not in ("Fluvius Town", "Parvus Town")):
                base_col = (35, 95, 195)
                status_tag = "FLOOD!"
                border_col = (168, 50, 35)
                border_w = 2
            elif (alt == 1 and sat >= 55) or (alt == 2 and sat >= 70 and room.region not in ("Fluvius Town", "Parvus Town")):
                base_col = (155, 105, 45)
                status_tag = f"MIRE {elev_m}m"
            elif alt >= 4 and (local_temp_c <= 0 or snow >= 50):
                base_col = (175, 215, 240)
                status_tag = f"ICE {local_temp_c}°C"
                border_col = (45, 95, 155)
                border_w = 2
            elif alt == 3 and sat >= 65:
                base_col = (40, 155, 75)
                status_tag = f"DRY {elev_m}m"
                border_col = (25, 95, 45)
                border_w = 2

            pygame.draw.rect(screen, base_col, c_rect, border_radius=5)
            pygame.draw.rect(screen, border_col, c_rect, width=border_w, border_radius=5)

            # Highlight Player Center Tile
            if gx == 0 and gy == 0:
                pygame.draw.rect(screen, (255, 235, 80), c_rect, width=3, border_radius=5)

            # Draw Tier & Status Text inside cell
            t_lbl = bold_font.render(f"T{alt}", True, (250, 248, 240) if alt < 5 else (28, 28, 28))
            s_lbl = small_font.render(status_tag, True, (255, 245, 220) if alt < 5 else (28, 28, 28))
            screen.blit(t_lbl, (c_rect.centerx - t_lbl.get_width() // 2, c_rect.top + 8))
            screen.blit(s_lbl, (c_rect.centerx - s_lbl.get_width() // 2, c_rect.bottom - 18))

    # Legend strip at bottom of map_rect
    leg_rect = pygame.Rect(map_rect.left + 6, map_rect.bottom - 24, map_rect.width - 12, 20)
    pygame.draw.rect(screen, (28, 28, 28), leg_rect, border_radius=4)
    leg_txt = small_font.render(
        "TOPO SURVEY [Press T]: T0=0m | T1=5m Hollow | T2=20m Plain | T3=60m High Bypass | T4=180m | T5=450m",
        True, (244, 239, 225)
    )
    screen.blit(leg_txt, (leg_rect.centerx - leg_txt.get_width() // 2, leg_rect.top + 3))

# =========================================================================
# 6. CLICKABLE WEATHER PILL & 3-DAY BAROMETRIC FORECAST POP-OUT
# =========================================================================
WEATHER_PILL_RECT = pygame.Rect(40, 3, 720, 20) # Change size of weather pill display on main screen


def _predict_chunk_weather(chunk_id, prev_weather_key, prev_sat, prev_snow, alt_mod=0):
    """
    Deterministically predicts the weather, temperature, saturation, and snowpack
    for a future 250-minute chunk using a seeded RNG (so forecasts are accurate!).
    """
    rng = random.Random(chunk_id * 7919 + 104729)
    total_mins = chunk_id * 250
    m_idx, day_of_m, dec_hr = get_calendar_metrics(total_mins)
    base_temp, dawn_hr, dusk_hr, table = MONTH_PROFILES[m_idx]

    if rng.random() < 0.55 or prev_weather_key not in WEATHER_TYPES:
        keys = [k for k, _ in table]
        weights = [w for _, w in table]
        chosen = rng.choices(keys, weights=weights, k=1)[0]
    else:
        chosen = prev_weather_key

    night_mod = -4 if (dec_hr < dawn_hr or dec_hr > dusk_hr) else 2
    temp_c = base_temp + alt_mod + night_mod + rng.randint(-3, 3)

    if temp_c <= 0 and chosen in ("light_rain", "heavy_rain", "torrential_rain"):
        chosen = "light_snow" if chosen == "light_rain" else ("heavy_snow" if chosen == "heavy_rain" else "blizzard")
    elif temp_c > 4 and chosen in ("light_snow", "heavy_snow", "blizzard"):
        chosen = "light_rain" if chosen == "light_snow" else "heavy_rain"

    w_spec = WEATHER_TYPES[chosen]
    next_sat = max(0, min(100, prev_sat + w_spec["sat_delta"]))
    next_snow = max(0, min(100, prev_snow + w_spec["snow_delta"]))
    return chosen, temp_c, next_sat, next_snow, m_idx, day_of_m, dec_hr


def generate_barometric_forecast(player, world_map=None):
    """
    Generates a 4-Window Short-Range Outlook (next 1000 decimal minutes / 1 full day)
    plus a 3-Day Almanac Outlook based on the player's current region and calendar date.
    """
    ensure_weather_initialized(player)
    cur_chunk = player.get("total_game_minutes", 0) // 250
    pos = (player.get("x", 8), player.get("y", 14))
    alt, elev_m, _ = get_tile_altitude_and_temp(player, pos, world_map)
    lapse_mod = {0: 0, 1: 0, 2: 0, 3: -1, 4: -3, 5: -6}.get(alt, 0)

    w_k = player.get("weather_current", "overcast")
    sat = player.get("ground_saturation", 35)
    snow = player.get("snowpack_level", 0)

    short_range = []
    for step in range(1, 5):
        c_id = cur_chunk + step
        w_k, t_c, sat, snow, m_i, d_m, d_hr = _predict_chunk_weather(c_id, w_k, sat, snow, alt_mod=lapse_mod)
        hr_label = f"{int(d_hr)}:00" if d_hr == int(d_hr) else f"{int(d_hr)}:50"
        short_range.append({
            "window": f"+{step * 2.5:.1f}h ({hr_label})",
            "weather_key": w_k,
            "name": WEATHER_TYPES[w_k]["name"],
            "temp_c": t_c,
            "pred_sat": sat,
            "pred_snow": snow,
        })

    # Continue projecting 8 more chunks (2 more days) for the 3-Day Almanac summary
    day_summaries = []
    for d_idx in range(1, 4):
        if d_idx == 1:
            sample = short_range[-1]
        else:
            for _ in range(4):
                c_id += 1
                w_k, t_c, sat, snow, m_i, d_m, d_hr = _predict_chunk_weather(c_id, w_k, sat, snow, alt_mod=lapse_mod)
            sample = {
                "name": WEATHER_TYPES[w_k]["name"],
                "temp_c": t_c,
                "pred_sat": sat,
                "pred_snow": snow,
            }
        day_summaries.append((f"Day +{d_idx}", sample))

    return short_range, day_summaries

