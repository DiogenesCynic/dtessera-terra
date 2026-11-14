"""
companions_engine.py
--------------------
Unified travelling companions database, recruitment helper, pack-mule carry bonuses,
combat assist rolls, and escort destination payouts.
"""

import random
import game_data as db

COMPANION_PROFILES = {
    "bandoka": {
        "name": "Bandoka (Wayfarer & Pack-Mule)",
        "weapon": "Twin Caligo Hunting Knives",
        "min_dmg": 2,
        "max_dmg": 4,
        "heal_per_turn": 0,
        "dmg_reduction": 1,
        "carry_bonus": 15.0,
        "combat_bark": "Bandoka darts in from the flank, slashing with twin hunting knives",
        "desc": "Fights beside you (2-4 DMG/turn, -1 incoming DMG) and adds +15 lbs carry capacity.",
    },
    "sister_hilde": {
        "name": "Sister Hilde (Mendicant Herbalist)",
        "weapon": "Rowan Staff & Chirurgeon's Satchel",
        "min_dmg": 1,
        "max_dmg": 2,
        "heal_per_turn": 1,
        "dmg_reduction": 0,
        "carry_bonus": 5.0,
        "combat_bark": "Sister Hilde wards off a blow with her staff and dresses your cuts with yarrow salve",
        "desc": "Supports in combat (1-2 DMG/turn, heals +1 HP/turn) and adds +5 lbs carry capacity.",
    },
    "sister_caelia": {
        "name": "Sister Caelia (Field Chirurgeon)",
        "weapon": "Lead-Shot Sling & Herb Satchel",
        "min_dmg": 1,
        "max_dmg": 3,
        "heal_per_turn": 1,
        "dmg_reduction": 0,
        "carry_bonus": 5.0,
        "combat_bark": "Sister Caelia looses a lead sling-stone and staunches your bleeding",
        "desc": "Supports with sling-stones (1-3 DMG/turn) and dresses your wounds (+1 HP/turn).",
    },
    "drover_tadgh": {
        "name": "Drover Tadgh (Caligo Muleteer)",
        "weapon": "Lead-Weighted Drover's Bullwhip",
        "min_dmg": 2,
        "max_dmg": 4,
        "heal_per_turn": 0,
        "dmg_reduction": 0,
        "carry_bonus": 20.0,
        "combat_bark": "Drover Tadgh cracks his braided bullwhip across the enemy's weapon-arm",
        "desc": "Cracks his bullwhip (2-4 DMG/turn) and his mule-train adds +20 lbs carry capacity.",
    },
    "bryn_wolfhound": {
        "name": "Houndmaster Bryn & Wolfhound",
        "weapon": "Hunting Spear & Wolfhound Fangs",
        "min_dmg": 2,
        "max_dmg": 4,
        "heal_per_turn": 0,
        "dmg_reduction": 1,
        "carry_bonus": 10.0,
        "combat_bark": "Houndmaster Bryn lunges with his boar-spear as his wolfhoundharries the enemy's heels",
        "desc": "Pins road bandits and beasts (2-4 DMG/turn, -1 incoming DMG, +10 lbs carry bonus).",
    },
    "padraig_brawler": {
        "name": "Rigger Padraig (Dockside Brawler)",
        "weapon": "Oak Belaying-Pin & Tarred Grapnel",
        "min_dmg": 3,
        "max_dmg": 5,
        "heal_per_turn": 0,
        "dmg_reduction": 1,
        "carry_bonus": 10.0,
        "combat_bark": "Rigger Padraig swings his heavy oak belaying-pin into the fray",
        "desc": "Heavy blunt brawler (3-5 DMG/turn, -1 incoming DMG, +10 lbs carry bonus).",
    },
    "corporal_wulfgar": {
        "name": "Corporal Wulfgar (Watch Pikeman)",
        "weapon": "Ten-Foot Ash Boarding Pike",
        "min_dmg": 3,
        "max_dmg": 5,
        "heal_per_turn": 0,
        "dmg_reduction": 1,
        "carry_bonus": 5.0,
        "combat_bark": "Corporal Wulfgar lunges forward with his ash pike, driving the attacker back",
        "desc": "Veteran pikeman (3-5 DMG/turn, -1 incoming DMG, +5 lbs carry bonus).",
    },
}


def get_active_companion_key(player):
    """Returns the key of the player's currently active road companion (or None)."""
    if (
        player.get("bandoka_joined")
        or player.get("traveling_with_bandoka")
        or player.get("bandoka_following")
    ) and not player.get("bandoka_exposed"):
        return "bandoka"

    comp = player.get("active_companion")
    if comp in COMPANION_PROFILES:
        expiry = player.get("companion_expiry_minute")
        if expiry is not None and player.get("total_game_minutes", 0) > expiry:
            player["active_companion"] = None
            player["companion_days_left"] = 0
            player["companion_expiry_minute"] = None
            return None
        return comp
    return None


def get_companion_info(player):
    """Returns the profile dictionary of the active companion, or None."""
    k = get_active_companion_key(player)
    return COMPANION_PROFILES.get(k) if k else None


def get_companion_carry_bonus(player):
    """Returns extra carry weight (lbs) provided by the active companion."""
    info = get_companion_info(player)
    return info["carry_bonus"] if info else 0.0


def hire_temporary_companion(player, comp_key, cost_silver=12, duration_days=3):
    """Recruits a temporary travelling companion for `duration_days` days (1,000 mins/day)."""
    if comp_key not in COMPANION_PROFILES:
        return player, "Unknown companion.", "MAIN"
    spec = COMPANION_PROFILES[comp_key]
    if player.get("active_companion") == comp_key:
        return player, f"{spec['name']} is already travelling with you!", "NPC_DIALOGUE"
    if player.get("silver", 0) < cost_silver:
        return (
            player,
            f"\"You need {cost_silver} silver to cover {spec['name']}'s road rations and hazard pay.\"",
            "NPC_DIALOGUE",
        )

    player["silver"] -= cost_silver
    player["active_companion"] = comp_key
    player["companion_days_left"] = duration_days
    player["companion_expiry_minute"] = player.get("total_game_minutes", 0) + (duration_days * 1000)
    log = (
        f"=== TRAVELLING COMPANION RECRUITED: {spec['name'].upper()} ({duration_days} Days) ===\n"
        f"{spec['desc']} (Remaining Silver: {player['silver']}s)"
    )
    return player, log, "MAIN"


def apply_companion_combat_assist(player):
    """
    Called automatically during every combat round in `encounters.py` and `ch2_dungeons.py`.
    Returns (bonus_enemy_dmg, player_heal, dmg_mitigation, log_string).
    """
    info = get_companion_info(player)
    if not info:
        return 0, 0, 0, ""

    dmg = random.randint(info["min_dmg"], info["max_dmg"])
    heal = info["heal_per_turn"]
    mit = info["dmg_reduction"]

    if heal > 0:
        player["health"] = min(player.get("max_health", 10), player.get("health", 10) + heal)

    parts = [f"> [Companion] {info['combat_bark']} (-{dmg} Enemy HP"]
    if heal > 0:
        parts.append(f", +{heal} Your HP")
    if mit > 0:
        parts.append(f", -{mit} Incoming Dmg")
    parts.append(")!")
    return dmg, heal, mit, "".join(parts)


def check_companion_destination_arrival(player):
    """Checks if an escort companion has reached their destination town and pays out rewards."""
    pos = (player.get("x", 8), player.get("y", 14))
    comp = player.get("active_companion")

    if comp == "sister_hilde" and pos in ((11, 4), (11, 3)):
        player["active_companion"] = None
        player["companion_expiry_minute"] = None
        player["silver"] += 18
        player["reputation"] = player.get("reputation", 0) + 1
        if "wound salve" not in player["inventory"]:
            player["inventory"].append("wound salve")
        return (
            "=== ESCORT COMPLETE: SISTER HILDE ARRIVES IN FLUVIUS (+18 Silver, +1 Reputation, +Wound Salve)! ===\n"
            "Sister Hilde blesses you at the Fluvius square: \"Thank you for seeing me safely down the highway, friend! Take this silver and my purest wound salve.\""
        )

    if comp == "drover_tadgh" and pos in ((17, 21), (17, 23)):
        player["active_companion"] = None
        player["companion_expiry_minute"] = None
        player["silver"] += 25
        player["equusense"] = player.get("equusense", 0) + 1
        return (
            "=== ESCORT COMPLETE: DROVER TADGH REACHES PARVUS PORT (+25 Silver, +1 Equusense)! ===\n"
            "Tadgh slaps your shoulder as his mule-train pulls onto the Parvus quays: \"Never seen finer road-work! Here is your 25-silver share—and a few tricks of the drover's trade!\""
        )

    return None

def get_companion_campfire_banter(player):
    """
    Returns atmospheric campfire banter (and a one-time +1 skill/stat tip!) when
    camping in the wilderness with Bandoka or a travelling companion.
    """
    c_key = get_active_companion_key(player)
    if not c_key:
        return ""

    if c_key == "bandoka":
        if not player.get("bandoka_camp_tip"):
            player["bandoka_camp_tip"] = True
            player["stealth"] = player.get("stealth", 0) + 1
            return (
                "\n\n[Campfire Banter — Bandoka (+1 Stealth)]: Across the crackling embers, Bandoka whets his twin Caligo hunting knives "
                "and shows you how mountain scouts muffle their boot-heels in dry bracken. "
                "As he reaches into his satchel for salt-pork, you catch a glint of a **heavy brass cipher cylinder** tucked beneath his cloak..."
            )
        return (
            "\n\n[Campfire — Bandoka]: Bandoka hobbles his pack-mule beside your tent and keeps first watch by the fire, "
            "his eyes scanning the dark horizon toward Castle Laydere."
        )

    if c_key == "sister_hilde":
        player["health"] = player.get("max_health", 10)
        return (
            "\n\n[Campfire — Sister Hilde (Full Health Restored)]: Sister Hilde brews a steaming pot of yarrow-and-mint tea over the camp-ember, "
            "cleaning your road-cuts and driving the night-chill from your bones."
        )

    if c_key == "drover_tadgh":
        if player.get("riding_horse") or "horse" in player.get("inventory", []):
            player["horse_hunger"] = 100
            player["horse_thirst"] = 100
        return (
            "\n\n[Campfire — Drover Tadgh (Mount Fed & Watered)]: Tadgh rubs down the animals with dry straw and shares a bag of roasted Caligo oats around the fire."
        )

    if c_key == "corporal_wulfgar":
        return (
            "\n\n[Campfire — Corporal Wulfgar]: Wulfgar plants his ten-foot ash pike beside the tent flap: "
            "\"Sleep easy, friend. No highwayman gets past a frontier pikeman on night watch.\""
        )

    return ""
