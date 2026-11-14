"""
ch2_easter_eggs.py
------------------
Houses the 8 Simulation & Player-Experience Upgrades:
1. One-Time Lignum Forest Kidnapping & In-Place Vanguardist Skirmishes
   (with Carved Yew Wayfinder recovery).
2. Paying Murum Stabling Fees by Post from any Postbox.
3. Four High-Risk, High-Reward Wilderness Easter Eggs (with zero
   curiosity Exposure Tell penalty).
4. Shift 3 Mid-Week Career Appraisal & Shift 6 Probationary Grace Day.
"""

import random
import game_data as db
from mechanics import get_eligible_chapter_2_routes, modify_faction


# =========================================================================
# 1. ONE-TIME FOREST KIDNAPPING & IN-PLACE VANGUARDIST ENCOUNTERS
# =========================================================================
def has_forest_wayfinder(player):
    """
    Returns True if the player carries a Brass Compass or a Carved Yew
    Wayfinder (preventing Lignum Forest D-Pad scrambling).
    """
    inv = player.get("inventory", [])
    return "brass compass" in inv or "carved yew wayfinder" in inv


def resolve_vanguard_forest_intercept(player):
    """
    Handles Lignum Forest Vanguardist interceptions:
    - First time (`vanguard_kidnapped_once == False`): Kidnaps the player
      to the Deep Glade (5, 5) for the atmospheric introduction.
    - Subsequent times (`vanguard_kidnapped_once == True`): Triggers an
      IN-PLACE encounter at the player's current (x, y) coordinates and
      offers a chance to earn the 'carved yew wayfinder'.
    Returns (was_kidnapped_bool, narrative_log_str, next_menu_state).
    """
    if not player.get("vanguard_kidnapped_once", False):
        player["vanguard_kidnapped_once"] = True
        player["x"], player["y"] = 5, 5
        log = (
            "*** AMBUSHED IN THE MIST! (FIRST VANGUARDIST CAPTURE) ***\n"
            "Antler-helmed figures drop from the oak boughs! Before you "
            "can draw steel, a hessian hood is pulled over your eyes and "
            "you are marched deep into the heart of Lignum Glade.\n"
            "*(Note: Now that you know their trails, future Vanguardist "
            "patrols will confront you on the spot rather than dragging "
            "you back to the glade!)*"
        )
        return True, log, "MAIN"

    # Subsequent encounters happen IN PLACE at current (player['x'], player['y'])!
    inv = player.setdefault("inventory", [])
    roll = (
        random.randint(1, 6)
        + random.randint(1, 6)
        + max(
            player.get("strength", 0),
            player.get("stealth", 0),
            player.get("charisma", 0),
        )
    )

    if "drum" in inv or player.get("faction_vanguardists", 0) >= 2:
        if "carved yew wayfinder" not in inv and "brass compass" not in inv:
            inv.append("carved yew wayfinder")
            way_msg = (
                " Recognising you as a friend of the wilds, their scout "
                "presses a **Carved Yew Wayfinder** into your hand so "
                "the forest canopy will never confuse your steps again!"
            )
        else:
            way_msg = " They salute your passage and melt back into the ferns."
        return (
            False,
            "*** VANGUARDIST PATROL AT YOUR POSITION ***\n"
            "A pair of moss-cloaked Vanguardist outriders steps from the "
            f"thicket right beside you.{way_msg}",
            "MAIN",
        )

    if roll >= 9:
        if "carved yew wayfinder" not in inv and "brass compass" not in inv:
            inv.append("carved yew wayfinder")
            loot_str = (
                " You recover a **Carved Yew Wayfinder** (functions as a "
                "forest compass!) and **8 Silver** from their scout's pack!"
            )
        else:
            loot_str = " You recover **8 Silver** from their dropped satchel!"
        player["silver"] = player.get("silver", 0) + 8
        return (
            False,
            "*** VANGUARDIST SKIRMISH (HELD YOUR GROUND!) ***\n"
            "Vanguardist outriders lunge from the bracken to blindfold "
            "you again, but you anticipate their snare and drive them off "
            f"without losing a single step of ground!{loot_str}",
            "MAIN",
        )

    player["health"] = max(1, player.get("health", 10) - 2)
    return (
        False,
        "*** VANGUARDIST SKIRMISH (HELD YOUR POSITION!) ***\n"
        "A Vanguardist patrol clashes with you in the undergrowth! You "
        "take a glancing blow (-2 HP) fending off their nets, but you "
        "hold your ground at your current coordinates.",
        "MAIN",
    )


# =========================================================================
# 2. PAYING STABLE FEES BY POST (AT ANY POSTBOX)
# =========================================================================
def get_postbox_stabling_option(player):
    """
    If the player has a horse stabled at Murum Stables and owes fees
    (or wants to prepay), returns the postal remittance option string.
    """
    if not player.get("horse_stabled"):
        return None
    days_stabled = max(
        0, player.get("day", 1) - player.get("horse_stabled_day", 1)
    )
    debt = max(player.get("stabling_debt", 0), days_stabled * 2)
    cost = max(2, debt) + 1
    return (
        f"Post Stable-Fee Remittance to Squire Godspeed "
        f"({cost}s incl. 1s Stamp)"
    )


def resolve_postbox_stabling(player):
    """
    Pays Squire Godspeed's stabling tab remotely via postal money-order,
    preventing the >20s horse foreclosure while exploring Chapter 2.
    """
    days_stabled = max(
        0, player.get("day", 1) - player.get("horse_stabled_day", 1)
    )
    debt = max(player.get("stabling_debt", 0), days_stabled * 2)
    cost = max(2, debt) + 1

    if player.get("silver", 0) < cost:
        return (
            player,
            f"You need {cost} Silver ({max(2, debt)}s stabling fee + 1s "
            "postal stamp) to mail a money-order to Murum Stables.",
            "MAIN",
        )

    player["silver"] -= cost
    player["stabling_debt"] = 0
    player["horse_stabled_day"] = player.get("day", 1)
    return (
        player,
        "*** POSTAL REMITTANCE DISPATCHED TO MURUM STABLES! ***\n"
        f"You seal {max(2, debt)} Silver and a 1-silver brass post-stamp "
        "into an oilskin packet addressed to **Squire Godspeed** and drop "
        "it into the postbox slot.\n"
        "Your stabling tab is paid in full up to today—your mount is safe "
        "from foreclosure while you continue your journey!",
        "MAIN",
    )


# =========================================================================
# 3. HIGH-RISK, HIGH-REWARD WILDERNESS EASTER EGGS (ZERO EXPOSURE PENALTY)
# =========================================================================
def check_wilderness_easter_egg_search(player, world_map=None):
    """
    Checks if the player's Search action triggers one of the 4 High-Risk,
    High-Reward Easter Eggs across Dtessera Terra.
    Never adds an Exposure Tell!
    Returns (triggered_bool, narrative_log_str).
    """
    pos = (player.get("x", 0), player.get("y", 0))
    found = player.setdefault("easter_eggs_found", [])
    inv = player.setdefault("inventory", [])
    skills = player.get("skills", [])

    # EASTER EGG 1: THE SUNKEN BELL-TOWER OF CALLUNA LAKE — (7, 18) or (8, 18)
    if pos in ((7, 18), (8, 18)) and "sunken_belfry" not in found:
        if "swim" not in skills:
            return (
                True,
                "*** SUBMERGED SECRET: THE DROWNED BELFRY ***\n"
                "Peering through the dark ripples of the lake, you spot "
                "the bronze weathercock of a sunken medieval bell-tower "
                "glinting twenty feet below! You will need the **Swim** "
                "skill to dive down to it safely.",
            )
        found.append("sunken_belfry")
        roll = (
            random.randint(1, 6)
            + random.randint(1, 6)
            + player.get("strength", 0)
        )
        if roll >= 8:
            player["silver"] = player.get("silver", 0) + 30
            player["influence"] = player.get("influence", 0) + 2
            if "ancient castellan signet" not in inv:
                inv.append("ancient castellan signet")
            return (
                True,
                "*** HIGH-RISK DISCOVERY: THE SUNKEN BELL-TOWER! ***\n"
                "You take a deep breath and kick down through the icy "
                "waters into the submerged belfry! Prying open an oilskin "
                "reliquary wedged inside the great bell, you surface with "
                "the **Ancient Castellan Signet**, **30 Silver**, and "
                "**+2 Influence**!",
            )
        player["health"] = max(1, player.get("health", 10) - 3)
        player["silver"] = player.get("silver", 0) + 15
        return (
            True,
            "*** ICY DIVE AT THE SUNKEN BELL-TOWER! ***\n"
            "Your lungs burn in the freezing current (-3 HP) as you "
            "wrench a pouch of **15 Silver** from the drowned belfry "
            "before kicking desperately back to the surface!",
        )

    # EASTER EGG 2: THE POACHER'S HOLLOW OAK IN LIGNUM — (6, 7) or (7, 7)
    if pos in ((6, 7), (7, 7)) and "poachers_oak" not in found:
        found.append("poachers_oak")
        has_key = "skeleton key" in inv or player.get("stealth", 0) >= 5
        if has_key or (random.randint(1, 6) + player.get("stealth", 0) >= 7):
            if "obsidian vanguard dice" not in inv:
                inv.append("obsidian vanguard dice")
            player["weapon_poison_charges"] = (
                player.get("weapon_poison_charges", 0) + 3
            )
            player["silver"] = player.get("silver", 0) + 20
            return (
                True,
                "*** EASTER EGG: THE POACHER'S LIGHTNING-SPLIT OAK! ***\n"
                "Spotting a hair-thin brass tripwire inside the hollow "
                "trunk, you deftly unhook the cocked prod-bow and lift "
                "out a velvet-wrapped cache: **Obsidian Vanguard Dice**, "
                "**+3 Nightshade Blade-Poison Charges**, and **20 Silver**!",
            )
        player["health"] = max(1, player.get("health", 10) - 3)
        if "obsidian vanguard dice" not in inv:
            inv.append("obsidian vanguard dice")
        return (
            True,
            "*** TRIPWIRE SPRING-TRAP IN THE HOLLOW OAK! ***\n"
            "TWANG! A concealed poacher's crossbow grazes your shoulder "
            "(-3 HP) as you reach into the hollow oak—but behind the "
            "sprung mechanism you still claim a prized set of **Obsidian "
            "Vanguard Dice**!",
        )

    # EASTER EGG 3: THE CALIGO CIPHER MONOLITH — (15, 5) or (16, 5)
    if pos in ((15, 5), (16, 5)) and "caligo_monolith" not in found:
        found.append("caligo_monolith")
        for stat_k in (
            "strength",
            "charisma",
            "stealth",
            "influence",
            "equusense",
        ):
            player[stat_k] = player.get(stat_k, 0) + 1
        player["exposure_tells"] = max(0, player.get("exposure_tells", 0) - 1)
        return (
            True,
            "*** ANCIENT SECRET: THE FIRST SURVEYOR'S MONOLITH! ***\n"
            "Brushing mountain lichen from a basalt standing stone, you "
            "decipher an acrostic carved by the island's first cartographer: "
            "*'FOUR CORNERS MEASURED BY TEN DECIMAL BELLS.'*\n"
            "Rotating the bronze sundial ring to X unlocks a hidden vault "
            "containing antiguo treatises (**+1 to ALL 5 Attributes** and "
            "**-1 Exposure Tell cleared** running into Chapter 3)!",
        )

    # EASTER EGG 4: THE MIDNIGHT DRUM CIRCLE — (5, 6) or (6, 6)
    if pos in ((5, 6), (6, 6)) and "midnight_drum_circle" not in found:
        if "drum" in inv or player.get("current_time", 500) >= 750:
            found.append("midnight_drum_circle")
            player["afflictions"] = []
            player["health"] = player.get("max_health", 10)
            player["hunger"] = 100.0
            player["thirst"] = 100.0
            if "owl-feather charm" not in inv:
                inv.append("owl-feather charm")
            if "carved yew wayfinder" not in inv:
                inv.append("carved yew wayfinder")
            modify_faction(player, "faction_communards", 2)
            modify_faction(player, "faction_vanguardists", 2)
            return (
                True,
                "*** SECRET GATHERING: THE WOODLAND DRUM CIRCLE! ***\n"
                "As your rhythm echoes between the standing yews, lantern-"
                "eyes flicker in the mist. Communard healers and Vanguard "
                "scouts share roasted chestnuts and herbal draughts around "
                "a smokeless ember-pit—**curing all afflictions, restoring "
                "full HP/Food/Water**, and gifting you an **Owl-Feather "
                "Charm** and a **Carved Yew Wayfinder**!",
            )

    return False, ""


# =========================================================================
# 4. SHIFT 3 CAREER APPRAISAL & SHIFT 6 PROBATIONARY GRACE WINDOW
# =========================================================================
def build_shift_3_appraisal_note(player):
    """
    Returns a helpful, diegetic mid-week career appraisal after Shift 3
    so a blind player is never blindsided by Shift 6 Noticeboard gates.
    """
    if player.get("current_tenure") != 3 or player.get("shift_3_appraised"):
        return ""
    player["shift_3_appraised"] = True

    eligible = get_eligible_chapter_2_routes(player)
    if eligible:
        return (
            "\n\n=== MID-WEEK CAREER APPRAISAL (SHIFT 3 OF 5) ===\n"
            "Your supervisor nods approvingly at your ledger: \"Keep this "
            "up! You have already met the qualifications for **"
            f"{', '.join(eligible[:2])}** on the Town Hall Noticeboard "
            "when your five-shift apprenticeship concludes!\""
        )

    return (
        "\n\n=== MID-WEEK CAREER APPRAISAL (SHIFT 3 OF 5) ===\n"
        "Your supervisor taps the ledger thoughtfully: \"You have **two "
        "shifts left** before your five-shift trial ends. To qualify for "
        "a regional post on the **Town Hall Noticeboard** at Shift 6, "
        "make sure you specialise in at least one path:\n"
        "  • **Union / F.A.I.:** Raise Union standing (+3) or Charisma (4+).\n"
        "  • **Town Guard / Castellan:** Raise Strength (5+) or Guard/Equusense.\n"
        "  • **Public Office / Maritime Guild:** Save 50+ Silver & raise Rep.\n"
        "  • **Acting Troupe / Outlaw:** Raise Charisma/Influence (5+) or Stealth.\""
    )


def handle_shift_6_probationary_grace(player, boss_name="Your employer"):
    """
    Instead of an instant Zork-style Game Over on Shift 6 if the player
    missed every Noticeboard gate by a point, grants a one-time
    Probationary Bonus (+1 to their top stat & +15s) and re-checks!
    Returns (rescued_bool, rescue_log_str).
    """
    if player.get("shift_6_grace_used"):
        return False, ""
    player["shift_6_grace_used"] = True

    # Boost the player's highest attribute by +1 and grant 15s final wages
    stats = ["strength", "charisma", "stealth", "influence", "equusense"]
    best_stat = max(stats, key=lambda s: player.get(s, 0))
    player[best_stat] = player.get(best_stat, 0) + 1
    player["silver"] = player.get("silver", 0) + 15
    if player.get("reputation", 0) >= 0:
        player["reputation"] = player.get("reputation", 0) + 1

    eligible = get_eligible_chapter_2_routes(player)
    if eligible:
        player["chapter_2_unlocked"] = True
        log = (
            f"{boss_name} frowns over your apprentice tally, then sighs "
            "and signs a probationary endorsement letter (+1 "
            f"{best_stat.title()}, +15 Silver back-pay).\n"
            "\"You cut it closer than I like, apprentice, but with my "
            "letter of reference in hand, you now qualify for the **Town "
            f"Hall Noticeboard** ({', '.join(eligible[:2])})! Go make "
            "something of yourself!\""
        )
        return True, log

    # Guaranteed fallback qualification for 'Become a Highway Robber' / 'Stand for Union Official'
    player["charisma"] = max(4, player.get("charisma", 0))
    player["faction_union"] = max(3, player.get("faction_union", 0))
    player["chapter_2_unlocked"] = True
    log = (
        f"{boss_name} closes the ledger with a grim nod.\n"
        "\"The guild masters won't renew your indenture here in Murum, "
        "apprentice—but the **Fluvius Union** and the **road-crews** are "
        "desperate for hands who know how hard this town can be. Check "
        "the **Town Hall Noticeboard** before dusk; a regional track has "
        "opened for you!\""
    )
    return True, log
