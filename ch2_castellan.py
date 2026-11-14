import random
import pygame
import game_data as db
import companions_engine
from mechanics import modify_faction, advance_time, execute_ch2_mission
from ui_components import draw_fitted_text


# =========================================================================
# SHARED 2d6 VARIANCE, WINDFALL & FRICTION HELPER FOR TRACK 3
# =========================================================================
def roll_castellan_2d6_twist(player, context="herding"):
    """
    Rolls 2d6 for Castellan staff missions (-10% to +10% swing) plus a 30% chance of a Windfall or Friction twist!
    Returns (swing_int, prefix_str, twist_str).
    """
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    swing = (d1 + d2 - 7) * 2
    prefix = f"[Roll {d1}+{d2}={d1+d2}] "
    twist_str = ""

    if random.random() < 0.30:
        if context == "herding":
            twists = [
                ("WINDFALL: Your outriders corner a prize brindle bull that had strayed into the gorse—Lord Hrothgar's bailiff awards a 10s bounty! (+10s)", 6),
                ("WINDFALL: A steady sea-breeze blows from the west, carrying your horn-calls clearly across the meadow! (+8% Herd Control)", 8),
                ("FRICTION: A flock of startled sea-gulls rises screaming from the western cliffs, spooking the lead heifers! (-6% Herd Control)", -6),
            ]
        elif context == "hunt":
            twists = [
                ("WINDFALL: A friendly Communard squirrel drops a pinecone onto a hidden tripwire right in front of your horse's hooves! (+8% Trail Mastery)", 8),
                ("WINDFALL: You spot a shed royal antler in the moss worth 8 silver at the castlehorn-carver's! (+8s)", 5),
                ("FRICTION: A sudden bank of cold Diluvium lake-mist rolls through the trees, dulling the hounds' scent! (-6% Trail Mastery)", -6),
            ]
        elif context == "summit":
            twists = [
                ("WINDFALL: Mayor Givethanks is delighted by the roasted Ragmore venison and pledges an extra 15s to the castle coffers! (+15s, +8% Harmony)", 8),
                ("WINDFALL: A loyal scullion tips you off that one of the minstrels is carrying a wax-key impression! (+6% Vigilance)", 6),
                ("FRICTION: A drunken baronial banneret spills gravy across the Murum alderman's velvet cloak! (-6% Harmony)", -6),
            ]
        elif context == "levy":
            twists = [
                ("WINDFALL: A retired Ragmore veteran rides into the bailey with three spare warhorses and a chest of sound mail! (+8% Readiness)", 8),
                ("WINDFALL: Auditing the toll-chests uncovers 12 silver in uncollected road-dues! (+12s)", 6),
                ("FRICTION: Autumn rain soaks the lower hay-ricks before the tarpaulins can belashed down! (-6% Readiness)", -6),
            ]
        else:
            twists = [
                ("WINDFALL: One of Corban's Kokeshi drivers panics at the sight of Ragmore's black-and-gold pennants and surrenders his manifest! (+8% Command)", 8),
                ("WINDFALL: A loyal tenant farmer brings a bucket of well-water and oats out to your lancers' mounts! (+6% Command)", 6),
                ("FRICTION: A nervous young destrier throws a shoe on the cobbles, slowing your second troop! (-6% Command)", -6),
            ]

        t_text, mod = random.choice(twists)
        swing += mod
        if "+10s" in t_text:
            player["silver"] += 10
        elif "+8s" in t_text:
            player["silver"] += 8
        elif "+15s" in t_text:
            player["silver"] += 15
        elif "+12s" in t_text:
            player["silver"] += 12
        twist_str = f" [{t_text}]"

    return swing, prefix, twist_str


# =========================================================================
# 1. TRACK 3 EXPLORATION NPCS: HERDSMAN CEOLWULF (5, 22) & HUNTSMAN AETHELSTAN (3, 22)
# =========================================================================
def get_ceolwulf_options(player):
    opts = ["Ask about the Castellan's cattle herds"]
    if player.get("chapter_2_route") == "Join Castellan's House Staff" and player.get("ch2_mission_step") == 1:
        opts.insert(0, "Ask why the forest boars and stags are stampeding onto the plains")
        if player.get("m3a_started"):
            opts.insert(0, "Mission: Mount the Outriders & Drive the Stampede from the Plains!")
    if player.get("active_companion") != "bryn_wolfhound":
        opts.append("Hire Houndmaster Bryn & Wolfhound as Escort (12s, 3 Days)")
    opts.append("Leave")
    return opts

def resolve_ceolwulf(choice, player):
    if choice == "Leave":
        return player, "Herdsman Ceolwulf leans on his long ash droving-goad, scanning the trampled turf.", "MAIN"

    if choice == "Ask about the Castellan's cattle herds":
        return player, (
            "Herdsman Ceolwulf shakes his weathered head.\n"
            "\"Three hundred head of black Ragmore shorthorns graze between here and the western sea-cliffs—or they did, before the woodland beasts burst through the eastern hedge!\""
        ), "NPC_DIALOGUE"

    if choice == "Ask why the forest boars and stags are stampeding onto the plains":
        player["m3a_ceolwulf_questioned"] = True
        return player, (
            "Ceolwulf points his goad toward the **eastern pasture boundary where the plains meet Lignum Forest**.\n"
            "\"That's what makes no sense, Steward. Woodland stags shun open pasture in daylight—yet yesterday a score of antlered harts and razor-boars crashed straight through our eastern hedge with foam on their flanks, "
            "driving our cattle dangerously close to the western volcanic cliffs!\"\n\n"
            "\"When I rode over toward the **eastern hedge-gap** to mend the fence, the wind carried a foul reek of burnt tallow and predator musk. "
            "And if you mean to guide those stags back into the trees without slaughtering them, the peaceful **Communard folk in the Lignum Forest Glade** know the old deer-calls better than any mortal huntsman.\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Mount the Outriders & Drive the Stampede from the Plains!":
        player, t_msg = execute_ch2_mission(player, "3a_herding", time_cost=120, stamina_drain=15)
        player, log, next_state = init_herding_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    if choice == "Hire Houndmaster Bryn & Wolfhound as Escort (12s, 3 Days)":
        return companions_engine.hire_temporary_companion(player, "bryn_wolfhound", 12, 3)

    return player, "Error.", "MAIN"


def get_aethelstan_options(player):
    opts = ["Ask about the Castle Ragmore hounds & stables"]
    if player.get("chapter_2_route") == "Join Castellan's House Staff" and player.get("ch2_mission_step") == 2:
        opts.insert(0, "Ask about the hazards of hunting in Lignum Forest")
        if player.get("m3b_started"):
            opts.insert(0, "Mission: Sound the Hunting Horns & Lead Lord Hrothgar into the Forest!")
    opts.append("Leave")
    return opts


def resolve_aethelstan(choice, player):
    if choice == "Leave":
        return player, "Huntsman Æthelstan couples two grey stag-hounds on a braided leather leash.", "MAIN"

    if choice == "Ask about the Castle Ragmore hounds & stables":
        return player, (
            "\"Finest pack in the northern barony,\" Æthelstan says proudly. \"Though they have little love for the dark boughs of Lignum Forest.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the hazards of hunting in Lignum Forest":
        player["m3b_aethelstan_questioned"] = True
        return player, (
            "Huntsman Æthelstan lowers his voice so the men-at-arms by the gate won't overhear.\n"
            "\"Lord Hrothgar insists on hunting the Great White Hart to show the realm he fears nothing—but the militant **Vanguardist** beasts of Lignum Forest hate our timber-axes.\"\n\n"
            "\"My whipper-in rode down the **Northern Hunting Ride just inside the forest border** at dawn and barely escaped with his neck—the Vanguardists have rigged deadfall logs and vine-snares across the game trails, marking their traps with notches of pale lichen! "
            "Scout that northern forest border yourself before we ride, and if you have any standing with **The Black Hills** in the deep woods, a word of parley may save Lord Hrothgar from an ambush!\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Sound the Hunting Horns & Lead Lord Hrothgar into the Forest!":
        player, t_msg = execute_ch2_mission(player, "3b_hunt", time_cost=150, stamina_drain=20)
        player, log, next_state = init_hunt_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    return player, "Error.", "MAIN"


# =========================================================================
# 2. ENVIRONMENTAL SEARCH HOOKS FOR TRACK 3 (RAGMORE PLAINS, FOREST & FARMS)
# =========================================================================
def handle_castellan_search(player):
    """
    Called inside action_gather() when exploring on the Castellan's House Staff route (or in Ragmore regions).
    Uses 1d6 + Stat/Skill rolls for windfalls and friction!
    """
    pos = (player["x"], player["y"])
    if player.get("current_building"):
        return False, ""

    # 1. Mission 3A Search at the Eastern Forest Hedge on Ragmore Plains (8, 24): Pull Up Wolf-Gall Stakes!
    if pos == (8, 24) and player.get("ch2_mission_step") == 1:
        if player.get("m3a_stakes_removed"):
            return True, "You have already pulled up the reeking Castle Laydere wolf-gall stakes along the eastern hedge-gap."
        die = random.randint(1, 6)
        bonus = max(player.get("equusense", 0), player.get("stealth", 0)) // 2
        player["m3a_stakes_removed"] = True
        player, _ = advance_time(20, player)
        extra = ""
        if die == 6:
            player["silver"] += 6
            extra = "\n*** WINDFALL (Rolled 6!): Beneath the last stake, you find a silver Laydere scout-badge worth 6 silver! (+6s) ***"
        elif die == 1:
            player["health"] = max(1, player.get("health", 10) - 1)
            extra = "\n*** FRICTION (Rolled 1!): A panicked boar bursts from the bracken and grazes your boot (-1 Health) as you uproot the stakes! ***"
        return True, (
            f"[Search Roll: 1d6({die})+{bonus}] Inspecting the trampled hedge-gap, you pull up a dozen ash-wood stakes smeared with rancid wolf-gall and stamped with the red-stone mark of **Castle Laydere**!\n"
            "Castellan Eormenhild's scouts planted these along the treeline so the scent of predators would drive the wild herds onto Hrothgar's pastures and prevent them from returning to the woods!"
            + extra
        )

    # 2. Mission 3B Search at the Northern Hunting Ride in Lignum Forest (8, 22): Disarm Vanguardist Snares!
    if pos == (8, 22) and player.get("ch2_mission_step") == 2:
        if player.get("m3b_traps_mapped"):
            return True, "You have already studied the pale-lichen trap markers and cut the front vine-snares along the hunting ride."
        die = random.randint(1, 6)
        bonus = max(player.get("stealth", 0), player.get("equusense", 0)) // 2
        player["m3b_traps_mapped"] = True
        player, _ = advance_time(20, player)
        extra = ""
        if die == 1:
            player["health"] = max(1, player.get("health", 10) - 1)
            extra = "\n(Friction: A taut briar-whip snaps back across your forearm as you sever it! -1 Health)"
        return True, (
            f"[Search Roll: 1d6({die})+{bonus}] Kneeling in the ferns along the Northern Hunting Ride, you trace the ankle-high vine-cord up to a heavy oak deadfall log balanced in the canopy!\n"
            "Better still, you decipher the Vanguardists' warning system: **three slashes of pale lichen on the north bark** always mark a trapped trail, while **unmarked moss** indicates a safe deer-run!"
            + extra
        )

    # 3. Mission 3C Search at the Sunken Sluice-Gate Lane (10, 5): Scout the Cavalry Mud-Trap!
    if pos == (10, 5) and player.get("chapter_2_route") == "Join Castellan's House Staff" and player.get("ch2_mission_step") == 3:
        if player.get("m3c_mudtrap_scouted"):
            return True, "You have already scouted the Sunken Sluice-Gate Lane and noted a firm bypass across the upper oat-ridge for your heavy cavalry."
        player["m3c_mudtrap_scouted"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Examining the narrow Sunken Sluice-Gate Lane from the saddle, you see that the irrigation pond above the bank is rigged to flood the hollow into axle-deep red clay mire!\n"
            "If you charge Castle Ragmore's armoured destriers down this sunken lane, half the horses will snap their cannon-bones in the mud. "
            "You chart a firm, dry cavalry approach along the **eastern oat-furrow ridge** instead!"
        )

    # 4. Mission 3D Search at Ragmore Lake Jetty (4, 24): Uncover the Smuggled Poison Vial & Laydere Seal!
    if pos == (4, 24) and player.get("ch2_mission_step") == 4:
        if player.get("m3d_lake_vial_found"):
            return True, "You have already recovered the empty bitter-almond phial and the Castle Laydere wax seal from the jetty reeds."
        die = random.randint(1, 6)
        player["m3d_lake_vial_found"] = True
        player, _ = advance_time(15, player)
        extra = " (+6s Windfall found in the reeds!)" if die == 6 else ""
        if die == 6:
            player["silver"] += 6
        return True, (
            f"[Search Roll: 1d6({die})] Searching the damp reeds beneath the Ragmore Lake jetty—where the unrecorded wine cask was landed at dusk—"
            "your boot strikes a discarded glass phial reeking of **bitter almonds**, lying beside a chipped **red-stone wax seal of Castle Laydere**!\n"
            f"The poison was poured into the **Dark Brumaire Vintage** flagon right here on the jetty!{extra}"
        )

    # 5. Mission 3D Search in Castle Ragmore Inner Bailey (4, 22): Spot the Loosened Tapestry Latch (Countering 10D)!
    if pos == (4, 22) and player.get("ch2_mission_step") == 4:
        if player.get("m3d_tapestry_checked"):
            return True, "You have already wedged the iron drop-bar across the map-room postern behind the Great Hall tapestries."
        player["m3d_tapestry_checked"] = True
        player, _ = advance_time(15, player)
        return True, (
            "Inspecting the gallery behind the Great Hall tapestries before the guests arrive, you notice that the brass latch to Lord Hrothgar's private map-room has been greased with theatrical spirit-gum and propped ajar with a folded playbill!\n"
            "One of Fairlight's backstage spies plans to rifle through Hrothgar's war-plans during the second course! You quietly drop the heavy iron security bar across the inner door."
        )

    # 6. Mission 3E Search in Castle Ragmore Inner Bailey (4, 22): Audit the Armoury Lances!
    if pos == (4, 22) and player.get("ch2_mission_step") == 5:
        if player.get("m3e_armoury_fixed"):
            return True, "The brittle Kokeshi lance-heads have already been culled and replaced with sound, tempered Ragmore steel."
        die = random.randint(1, 6) + (3 if "forge" in player.get("skills", []) else 0) + (player.get("strength", 0) // 2)
        player["m3e_armoury_fixed"] = True
        player, _ = advance_time(25, player)
        if die >= 5:
            return True, (
                f"[Armoury Roll: {die}] Testing the newly delivered ash lances on the Armoury Rack, you strike a spearhead against the anvil—and it snaps like dry clay! "
                "A Kokeshi contractor supplied cast-iron dross instead of tempered steel! "
                "You break open the keep's reserve vaults and re-arm the entire vanguard with sound, oil-quenched Ragmore steel!"
            )
        else:
            player["health"] = max(1, player.get("health", 10) - 1)
            return True, (
                "Testing a lance-head against the stone block, the brittle Kokeshi iron shatters and a shard nicked your forearm (-1 Health)—"
                "alerting you in time to swap the faulty batch for reserve steel before the levy marches!"
            )

    # 7. Mission 3E Search at the Ragmore Manor Tithe-Barn (4, 15): Uncover Grit-Sabotaged Axle-Grease!
    if pos == (4, 15) and player.get("ch2_mission_step") == 5:
        if player.get("m3e_wagons_fixed"):
            return True, "The grit-sabotaged grease buckets have been dumped, and the baggage wains are lubricated with clean tallow."
        player["m3e_wagons_fixed"] = True
        player, _ = advance_time(20, player)
        return True, (
            "Dipping your fingers into the grease-buckets beside the baggage wains at the Tithe-Barn, you feel coarse quartz sand mixed into the tallow!\n"
            "Someone paid a teamster to pack the wheel-hubs with grinding grit so Hrothgar's supply train would seize up five miles from the keep! "
            "You scrub the hubs clean and repack every axle with pure mutton-tallow."
        )

    return False, ""


# =========================================================================
# 3. MISSION 3A POP-OUT: THE STAMPEDE ON RAGMORE PLAINS (MINIGAME_HERDING)
# =========================================================================
HERDING_BEATS = [
    {
        "title": "PASTURE BEAT 1/4: THE CLIFF-EDGE PANIC!",
        "desc": (
            "Two score of wild ten-point stags and bristling razor-boars come thundering across the western pasture, "
            "driving Lord Hrothgar's prize shorthorn cattle straight toward the sheer volcanic drop of the Dtessera Sea-Cliffs!"
        ),
    },
    {
        "title": "PASTURE BEAT 2/4: THE CHARGING SOUNDERS IN THE GORSE!",
        "desc": (
            "Turned back from the cliff-edge, a sounder of massive forest razor-boars wheels around in the tall grass, "
            "lowering their tusks to gore your lead outriders' horses!"
        ),
    },
    {
        "title": "PASTURE BEAT 3/4: THE EASTERN HEDGE BOTTLENECK!",
        "desc": (
            "Your outriders have pressed the mixed herds back toward the trampled gap in the eastern forest hedge—but the stags rear up and balk, "
            "terrified by the scent clinging to the boundary line!"
        ),
    },
    {
        "title": "PASTURE BEAT 4/4: SEALING THE PASTURE MARCH!",
        "desc": (
            "The last of the woodland stags and boars bound across the ditch toward the eaves of Lignum Forest. "
            "How do you secure the eastern boundary so the herds remain at peace?"
        ),
    },
]


def init_herding_minigame(player):
    """Initializes the Mission 3A Spatial Pasture Herding Pop-Out Window."""
    player["herd_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["herd_beat"] = 0
    base_ctrl = 40 + (player.get("equusense", 0) * 3) + (10 if "ride" in player.get("skills", []) else 0)
    if player.get("m3a_stakes_removed"):
        base_ctrl += 15
    if player.get("foraging_lore_learned") or player.get("faction_communards", 0) >= 2:
        base_ctrl += 10
    player["herd_control"] = min(85, base_ctrl)
    player["herd_calm"] = 80
    player["herd_feedback"] = (
        "You swing into the saddle at the head of Hrothgar's outriders! "
        "Raise Herd Control to 75%+ across 4 beats while keeping Pasture Calm above 25% so no cattle are lost over the cliffs!"
    )
    return player, player["herd_feedback"], "MINIGAME_HERDING"


def herding_action(action, player):
    """Processes 2d6 horsemanship rolls and pasture maneuvers in MINIGAME_HERDING."""
    if player.get("herd_phase") == "RESULT":
        return conclude_herding_minigame(player)

    beat = player.get("herd_beat", 0)
    ctrl = player.get("herd_control", 45)
    calm = player.get("herd_calm", 80)

    swing, prefix, twist_str = roll_castellan_2d6_twist(player, context="herding")
    eq_bonus = (player.get("equusense", 0) // 2) + (3 if "ride" in player.get("skills", []) else 0)
    msg = ""

    # BEAT 1: THE CLIFF-EDGE PANIC
    if beat == 0:
        if action == "flank_cliff":
            ctrl += 15 + eq_bonus + (swing // 2)
            calm += 5
            msg = "Galloping hard along the basalt cliff-rim, you form a mounted crescent between the sea-drop and the panicked shorthorns, wheeling the herd safely inland!"
        elif action == "horn_cadence":
            if player.get("foraging_lore_learned") or player.get("faction_communards", 0) >= 1 or player.get("equusense", 0) >= 4:
                ctrl += 20 + (swing // 2)
                calm += 10
                msg = "You wind the low, melodic Communard deer-call on your horn! The wild stags recognise the woodland cadence and immediately slow their frantic gallop!"
            else:
                ctrl -= 5
                calm -= 15
                msg = "Your harsh horn-blast echoes off the sea-cliffs and startles the calves even worse (-15% Pasture Calm)!"
        else:
            ctrl += 10
            calm -= 25
            modify_faction(player, "faction_communards", -1)
            msg = "Your men loose crossbow bolts into the lead stags—turning the herd back from the cliff, but sending a wave of bloody panic across the pasture (-25% Calm)!"

    # BEAT 2: THE CHARGING SOUNDERS IN THE GORSE
    elif beat == 1:
        if action == "part_lanes":
            ctrl += 15 + eq_bonus + (swing // 2)
            msg = "With practiced horsemanship, you part your riders into wide parallel lanes, letting the charging razor-boars thunder harmlessly down the chute toward the trees!"
        elif action == "toss_cobnuts":
            if any(f in player.get("inventory", []) for f in ["cobnuts", "apple", "carrot", "sack of oats"]):
                ctrl += 22
                calm += 10
                msg = "Scattering sweet forage across the turf downwind, you draw the rooting boars away from the horses' legs without a single tusk-wound!"
            else:
                ctrl -= 5
                calm -= 10
                msg = "You have no woodland forage in your saddlebags to distract the sounder!"
        else:
            ctrl += 12
            calm -= 20
            player["health"] = max(1, player.get("health", 10) - 1)
            msg = "You meet the razor-boars with levelled boar-spears—driving them off, though a slashed stirrup-leather grazes your leg (-1 HP, -20% Calm)!"

    # BEAT 3: THE EASTERN HEDGE BOTTLENECK
    elif beat == 2:
        if action == "clear_scent":
            if player.get("m3a_stakes_removed"):
                ctrl += 25 + (swing // 2)
                calm += 10
                msg = (
                    "Because you already uprooted Castle Laydere's wolf-gall stakes from the hedge-gap, the air smells sweet and clear—the stags bound straight back into Lignum Forest!"
                )
            else:
                ctrl -= 10
                calm -= 20
                msg = (
                    "The stags rear in terror at the reek of wolf-gall clinging to the eastern hedge—because you didn't search the boundary fence beforehand, the herd stampedes sideways through your line (-20% Calm)!"
                )
        elif action == "windward_drive":
            ctrl += 12 + eq_bonus + (swing // 2)
            calm -= 5
            msg = "Riding upwind of the herd, you crack your stock-whips in unison and press the balking stags through a higher gap in the dry-stone wall!"
        else:
            ctrl += 5
            calm -= 20
            msg = "Forcing the terrified stags against the foul wind causes several beasts to crash into the thorny hedge (-20% Calm)!"

    # BEAT 4: SEALING THE PASTURE MARCH
    else:
        if action == "expose_laydere":
            if player.get("m3a_stakes_removed"):
                ctrl += 15
                calm += 10
                msg = (
                    "You present the wolf-gall stakes bearing Castle Laydere's red-stone mark to Herdsman Ceolwulf and Lord Hrothgar's bailiff—proving the stampede was an act of Laydere sabotage!"
                )
            else:
                ctrl += 5
                msg = "You blame Castle Laydere for the stampede, though without the physical stakes from the eastern hedge, the bailiff remains skeptical."
        elif action == "wattled_gate":
            ctrl += 15 + (swing // 2)
            calm += 5
            modify_faction(player, "faction_communards", 1)
            msg = "Working alongside Ceolwulf's drovers, you weave a sturdy wattle-hurdle across the cattle pasture while leaving a peaceful deer-stile open along the stream (+1 Communards)!"
        else:
            ctrl += 10
            calm -= 10
            modify_faction(player, "faction_vanguardists", -1)
            msg = "You stake iron caltrops and wolf-traps along the treeline—securing the cattle, but infuriating the woodland creatures (-1 Vanguardists)!"

    player["herd_control"] = max(0, min(100, ctrl))
    player["herd_calm"] = max(0, min(100, calm))
    full_msg = prefix + msg + twist_str

    if player["herd_calm"] <= 0 or beat >= 3:
        player["herd_phase"] = "RESULT"
        tag = "PASTURES SECURED IN TRIUMPH!" if (player["herd_control"] >= 70 and player["herd_calm"] >= 25) else "ROUGH DROVING!"
        player["herd_feedback"] = f"{full_msg} — [{tag}] Click [Report to Castellan Hrothgar >>]!"
        return player, player["herd_feedback"], "MINIGAME_HERDING"

    player["herd_beat"] = beat + 1
    player["herd_feedback"] = full_msg
    return player, None, "MINIGAME_HERDING"


def conclude_herding_minigame(player):
    player["ch2_mission_step"] = 2
    player["active_ch2_mission"] = None

    ctrl = player.get("herd_control", 0)
    calm = player.get("herd_calm", 0)
    stakes_bonus = 5 if player.get("m3a_stakes_removed") else 0

    if ctrl >= 70 and calm >= 25:
        gain = 20 + stakes_bonus
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["equusense"] = player.get("equusense", 0) + 1
        player["silver"] += 30
        log = (
            f"=== MISSION COMPLETE: THE PLAINS SECURED (+{gain}% Position Strength, +1 Equusense, +30 Silver)! ===\n"
            "Without losing a single heifer over the sea-cliffs, you guide the woodland herds safely back beneath the boughs of Lignum Forest"
            + (" and lay the Castle Laydere wolf-gall stakes before Lord Hrothgar's war-council!\n\n" if stakes_bonus else "!\n\n")
            + "Castellan Hrothgar tosses you a **30-silver** purse from the high steps of the keep.\n"
            "\"Well ridden, Steward! Now let us see how you handle the deep canopy—tomorrow I ride into **Lignum Forest** to hunt the Great White Hart. "
            "Speak with **Huntsman Æthelstan** in the outer bailey and scout the northern forest trails before we sound the horns!\""
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 8)
        player["silver"] += 15
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: A BRUISING STAMPEDE (+8% Position Strength, +15 Silver, +1 Exposure Tell) ===\n"
            "The pastures are cleared at last, though several prize shorthorns were lost in the gorse and Lord Hrothgar scowls at the tally.\n\n"
            "*** Next Mission: Speak to Castellan Hrothgar or Huntsman Æthelstan at Castle Ragmore to prepare for the Royal Hunt in Lignum Forest! ***"
        )
    return player, log, "MAIN"


def draw_herding_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 3A (Pasture Herding)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    FOREST_GREEN = (45, 125, 60)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("RAGMORE PLAINS — THE GREAT PASTURE STAMPEDE", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    ctrl = player.get("herd_control", 45)
    calm = player.get("herd_calm", 80)

    screen.blit(font_bold.render(f"Herd Control: {ctrl}% (Target: 70%+)", True, FOREST_GREEN), (85, 78))
    c_bar = pygame.Rect(380, 78, 335, 16)
    pygame.draw.rect(screen, (40, 35, 35), c_bar, border_radius=4)
    if ctrl > 0:
        pygame.draw.rect(screen, FOREST_GREEN, (380, 78, int(335 * (ctrl / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, c_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Pasture Calm & Safety: {calm}%", True, TATE_RED), (85, 100))
    s_bar = pygame.Rect(380, 100, 335, 16)
    pygame.draw.rect(screen, (40, 35, 35), s_bar, border_radius=4)
    if calm > 0:
        pygame.draw.rect(screen, TATE_RED, (380, 100, int(335 * (calm / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, s_bar, width=1, border_radius=4)

    b_idx = min(3, player.get("herd_beat", 0))
    b_data = HERDING_BEATS[b_idx]

    b_box = pygame.Rect(85, 126, 630, 130)
    pygame.draw.rect(screen, (252, 248, 238), b_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, b_box, width=2, border_radius=8)

    screen.blit(font_bold.render(b_data["title"], True, TATE_RED), (100, 134))
    draw_fitted_text(screen, b_data["desc"], pygame.Rect(100, 158, 600, 62), CLOCK_BLACK, max_lines=3)

    tags = []
    if player.get("m3a_stakes_removed"):
        tags.append("[Laydere Wolf-Gall Stakes Uprooted]")
    if player.get("m3a_ceolwulf_questioned"):
        tags.append("[Ceolwulf's Pasture Briefing]")
    if player.get("foraging_lore_learned") or player.get("faction_communards", 0) >= 1:
        tags.append("[Communard Deer-Cadence Known]")
    t_str = "Field Preparation: " + (", ".join(tags) if tags else "None gathered yet")
    screen.blit(font.render(t_str, True, FOREST_GREEN if tags else TATE_RED), (100, 230))

    fb_box = pygame.Rect(85, 264, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("herd_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 4. MISSION 3B POP-OUT: THE CASTELLAN'S HUNT IN LIGNUM FOREST (MINIGAME_HUNT)
# =========================================================================
HUNT_STAGES = [
    {
        "title": "CANOPY STAGE 1/3: THE FORK OF THE PALE LICHEN",
        "desc": (
            "The baying stag-hounds plunge beneath the green twilight of Lignum Forest! Ahead, the trail splits around a hollow oak: "
            "the left path has **three slashes of pale-green lichen** carved into the north bark; the right path is carpeted in **unmarked emerald moss**."
        ),
    },
    {
        "title": "CANOPY STAGE 2/3: THE SILENT CANOPY & THE BRIAR GORGE",
        "desc": (
            "Lord Hrothgar spurs his warhorse hard after a flash of white antlers! Suddenly, the wood-pigeons in the canopy overhead fall dead silent, "
            "and you smell fresh resin where a massive deadfall pine hangs above the sunken gorge!"
        ),
    },
    {
        "title": "CANOPY STAGE 3/3: RINGED BY ANTLERS IN THE DEEP GLADE!",
        "desc": (
            "Emerging into a sun-dappled clearing, you find the Great White Hart standing beside **The Black Hills** and two dozen militant **Vanguardist** defenders! "
            "Hrothgar reaches for his boar-spear as a hundred eyes watch from the boughs!"
        ),
    },
]


def init_hunt_minigame(player):
    """Initializes the Mission 3B Lignum Forest Hunt & Vanguardist Parley Pop-Out."""
    player["hunt_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["hunt_stage"] = 0
    base_track = 40 + (player.get("equusense", 0) * 3) + (10 if "compass" in player.get("inventory", []) else 0)
    if player.get("m3b_traps_mapped"):
        base_track += 20
    player["hunt_mastery"] = min(85, base_track)
    player["hunt_safety"] = 85
    player["hunt_feedback"] = (
        "The hunting horns echo beneath the ancient oaks! "
        "Read the natural signs of Lignum Forest to steer Lord Hrothgar clear of Vanguardist traps and resolve the confrontation in the glade!"
    )
    return player, player["hunt_feedback"], "MINIGAME_HUNT"


def hunt_action(action, player):
    """Processes 2d6 tracking rolls and the Vanguardist truce in MINIGAME_HUNT."""
    if player.get("hunt_phase") == "RESULT":
        return conclude_hunt_minigame(player)

    stage = player.get("hunt_stage", 0)
    mast = player.get("hunt_mastery", 45)
    safe = player.get("hunt_safety", 85)

    swing, prefix, twist_str = roll_castellan_2d6_twist(player, context="hunt")
    msg = ""

    # STAGE 1: THE FORK OF THE PALE LICHEN
    if stage == 0:
        if action == "take_moss":
            mast += 20 + (swing // 2)
            safe += 5
            msg = (
                "Reading the woodland signs, you steer Lord Hrothgar down the unmarked mossy deer-run—completely bypassing the vine-snare pit rigged along the lichen-slashed trail!"
            )
        elif action == "take_lichen":
            if player.get("m3b_traps_mapped"):
                mast += 10
                msg = "Recognizing the three lichen slashes at the last second, you shout for Hrothgar to leap the tripwire!"
            else:
                mast -= 10
                safe -= 25
                player["health"] = max(1, player.get("health", 10) - 1)
                msg = "SNAP! The three lichen slashes were a Vanguardist trap-marker! A whipped sapling lashes across the party (-25% Safety, -1 HP)!"
        else:
            mast += 12 + (swing // 2)
            safe -= 5
            msg = "Flipping open your Brass Compass, you cut an off-trail bearing across the roots to keep pace with the hounds."

    # STAGE 2: THE SILENT CANOPY & THE BRIAR GORGE
    elif stage == 1:
        if action == "halt_deadfall":
            mast += 22 + (swing // 2)
            safe += 10
            msg = (
                "Seizing Hrothgar's bridle-rein, you rear his destrier to a halt! A heartbeat later, a two-ton deadfall oak crashes harmlessly into the gorge ten paces ahead! "
                "Lord Hrothgar stares in stunned gratitude at your woodcraft!"
            )
        elif action == "loose_warning_arrow":
            if "archery" in player.get("skills", []):
                mast += 25
                safe += 10
                msg = "With a master archer's eye, you loose a shaft upward that severs the counterweight vine—dropping the deadfall log safely before the horses reach the gorge!"
            else:
                mast -= 5
                safe -= 20
                msg = "Without the Archery skill, your shot misses the counterweight vine and the falling branches graze the rear hounds (-20% Safety)!"
        else:
            mast -= 10
            safe -= 30
            player["health"] = max(1, player.get("health", 10) - 2)
            msg = "Charging blindly into the silent gorge triggers the Vanguardist deadfall! Crashing boughs batter the hunting party (-30% Safety, -2 HP)!"

    # STAGE 3: RINGED BY ANTLERS IN THE DEEP GLADE
    else:
        if action == "parley_truce":
            if player.get("vanguard_oath_taken") or player.get("faction_vanguardists", 0) >= 2 or player.get("faction_communards", 0) >= 2 or mast >= 65:
                mast += 25
                safe += 10
                modify_faction(player, "faction_vanguardists", 2)
                modify_faction(player, "faction_communards", 1)
                msg = (
                    "Stepping dismounted between Hrothgar's spear and The Black Hills, you negotiate the **Charter of the Ancient Boughs**: "
                    "Castle Ragmore swears to halt clear-cutting along the northern border, and in return the Vanguardists pledge never to raid Ragmore's flank during the war with Laydere!"
                )
            else:
                mast += 5
                safe -= 15
                msg = "You call for a truce, and though The Black Hills lets your party depart unharmed, your lack of prior woodland standing leaves the border tense (-15% Safety)."
        elif action == "expose_laydere_poachers":
            if player.get("m3a_stakes_removed"):
                mast += 25
                modify_faction(player, "faction_vanguardists", 2)
                msg = (
                    "You cast the wolf-gall stakes bearing **Castle Laydere's** red-stone seal onto the moss before The Black Hills—proving it was Castellan Eormenhild's agents who poisoned the eastern glades! "
                    "The Vanguardists turn their wrath against Castle Laydere!"
                )
            else:
                mast -= 5
                safe -= 15
                msg = "You claim Castle Laydere is to blame, but without the wolf-gall stakes from the eastern hedge, The Black Hills snorts in disbelief (-15% Safety)!"
        else:
            mast += 5
            safe -= 30
            modify_faction(player, "faction_vanguardists", -3)
            msg = "You form a boar-spear ring and fight your way out of the glade—bringing Hrothgar back alive, but turning the entire forest into sworn enemies (-30% Safety, -3 Vanguardists)!"

    player["hunt_mastery"] = max(0, min(100, mast))
    player["hunt_safety"] = max(0, min(100, safe))
    full_msg = prefix + msg + twist_str

    if player["hunt_safety"] <= 0 or stage >= 2:
        player["hunt_phase"] = "RESULT"
        tag = "WOODLAND TRUCE & SAFE RETURN!" if (player["hunt_mastery"] >= 70 and player["hunt_safety"] >= 35) else "BATTERED RETURN FROM THE WOODS!"
        player["hunt_feedback"] = f"{full_msg} — [{tag}] Click [Return to Castle Ragmore >>]!"
        return player, player["hunt_feedback"], "MINIGAME_HUNT"

    player["hunt_stage"] = stage + 1
    player["hunt_feedback"] = full_msg
    return player, None, "MINIGAME_HUNT"


def conclude_hunt_minigame(player):
    player["ch2_mission_step"] = 3
    player["active_ch2_mission"] = None

    mast = player.get("hunt_mastery", 0)
    safe = player.get("hunt_safety", 0)

    if mast >= 70 and safe >= 35:
        gain = 22 + (4 if player.get("m3b_traps_mapped") else 0)
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["equusense"] = player.get("equusense", 0) + 1
        player["reputation"] = player.get("reputation", 0) + 2
        log = (
            f"=== MISSION COMPLETE: THE CHARTER OF THE BOUGHS (+{gain}% Position Strength, +1 Equusense, +2 Reputation)! ===\n"
            "You guided Castellan Hrothgar past every deadfall in Lignum Forest and secured a historic border truce with the Vanguardist defenders, protecting Ragmore's eastern flank!\n\n"
            "*** Next Mission: Speak to Castellan Hrothgar in Castle Ragmore—he orders you to ride south with the Castle Lancers to deal with the Farm Strike blockade at the Fluvius Crossroads! ***"
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 8)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: A TORN CLOAK IN THE WOODS (+8% Position Strength, +1 Exposure Tell) ===\n"
            "Lord Hrothgar returns to Castle Ragmore nursing bruises from the forest snares, his mood thunderous.\n\n"
            "*** Next Mission: Speak to Castellan Hrothgar to receive your cavalry orders for the Farm Strike! ***"
        )
    return player, log, "MAIN"


def draw_hunt_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 3B (The Royal Hunt)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    FOREST_GREEN = (45, 125, 60)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("LIGNUM FOREST — THE CASTELLAN'S ROYAL HUNT", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    mast = player.get("hunt_mastery", 45)
    safe = player.get("hunt_safety", 85)

    screen.blit(font_bold.render(f"Trail Mastery & Diplomacy: {mast}% (Target: 70%+)", True, FOREST_GREEN), (85, 78))
    m_bar = pygame.Rect(390, 78, 325, 16)
    pygame.draw.rect(screen, (40, 35, 35), m_bar, border_radius=4)
    if mast > 0:
        pygame.draw.rect(screen, FOREST_GREEN, (390, 78, int(325 * (mast / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, m_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Party & Mount Safety: {safe}%", True, TATE_RED), (85, 100))
    s_bar = pygame.Rect(390, 100, 325, 16)
    pygame.draw.rect(screen, (40, 35, 35), s_bar, border_radius=4)
    if safe > 0:
        pygame.draw.rect(screen, TATE_RED, (390, 100, int(325 * (safe / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, s_bar, width=1, border_radius=4)

    st_idx = min(2, player.get("hunt_stage", 0))
    st_data = HUNT_STAGES[st_idx]

    s_box = pygame.Rect(85, 126, 630, 130)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 134))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 158, 600, 62), CLOCK_BLACK, max_lines=3)

    tags = []
    if player.get("m3b_traps_mapped"):
        tags.append("[Lichen Trap-Markers Deciphered]")
    if "compass" in player.get("inventory", []):
        tags.append("[Brass Compass]")
    if player.get("m3a_stakes_removed"):
        tags.append("[Laydere Wolf-Gall Evidence]")
    t_str = "Woodcraft Preparation: " + (", ".join(tags) if tags else "None gathered yet")
    screen.blit(font.render(t_str, True, FOREST_GREEN if tags else TATE_RED), (100, 230))

    fb_box = pygame.Rect(85, 264, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("hunt_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 5. MISSION 3C POP-OUT: LANCERS AT THE FARM STRIKE (MINIGAME_LANCERS)
# =========================================================================
LANCER_PHASES = [
    {
        "title": "CAVALRY PHASE 1/3: CHOOSING THE APPROACH VECTOR!",
        "desc": (
            "Riding south at the head of Sergeant Wulfgar's heavy Ragmore Lancers, you reach the rise above the Fluvius Farm Crossroads. "
            "Two routes lead down to the barricade: the narrow **Western Sunken Sluice-Gate Lane**, or the open **Eastern Oat-Furrow Ridge**."
        ),
    },
    {
        "title": "CAVALRY PHASE 2/3: THE STANDOFF AT THE HAY-WAINS!",
        "desc": (
            "Your pennants snap in the wind as you draw rein before the crossroads! Organiser Joyinsorrow's strikers lock arms behind the hay-wains, "
            "while Wagon-Boss Corban demands that you trample the peasants so his Kokeshi wagons can pass without paying feudal river-tolls!"
        ),
    },
    {
        "title": "CAVALRY PHASE 3/3: THE CASTELLAN'S SETTLEMENT!",
        "desc": (
            "With the entire valley watching your stirrup, how do you secure Castle Ragmore's grain-tribute and resolve the blockade?"
        ),
    },
]


def init_lancers_minigame(player):
    """Initializes the Mission 3C Cavalry Deployment Pop-Out at the Farm Strike."""
    player["lancer_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["lancer_step"] = 0
    base_cmd = 45 + (player.get("influence", 0) * 3) + (player.get("equusense", 0) * 2)
    if player.get("m3c_mudtrap_scouted"):
        base_cmd += 15
    player["lancer_command"] = min(85, base_cmd)
    player["lancer_mounts"] = 90
    player["lancer_feedback"] = (
        "Twenty armored Ragmore Lancers await your trumpet-call! "
        "Maintain Mount & Troop Readiness while raising Feudal Command to 70%+!"
    )
    return player, player["lancer_feedback"], "MINIGAME_LANCERS"


def lancers_action(action, player):
    """Processes 2d6 cavalry maneuvers and feudal arbitration in MINIGAME_LANCERS."""
    if player.get("lancer_phase") == "RESULT":
        return conclude_lancers_minigame(player)

    step = player.get("lancer_step", 0)
    cmd = player.get("lancer_command", 50)
    mounts = player.get("lancer_mounts", 90)

    swing, prefix, twist_str = roll_castellan_2d6_twist(player, context="lancers")
    msg = ""

    # PHASE 1: CHOOSING THE APPROACH VECTOR
    if step == 0:
        if action == "eastern_ridge":
            cmd += 20 + (swing // 2)
            mounts += 5
            msg = (
                "Wheeling the squadron across the firm turf of the Eastern Oat-Furrow Ridge, you bring your heavy warhorses down on the flank of the crossroads in pristine formation—completely bypassing the flooded Sunken Lane mud-trap!"
            )
        elif action == "sunken_lane":
            if player.get("m3c_mudtrap_scouted"):
                cmd += 5
                mounts -= 10
                msg = "Knowing the sluice is rigged, you pick your way single-file along the high bank, though the slick clay still tires the horses (-10% Mounts)."
            else:
                cmd -= 15
                mounts -= 35
                player["health"] = max(1, player.get("health", 10) - 2)
                msg = (
                    "TRAP SPRUNG! Because you didn't scout the Sunken Sluice-Gate Lane first, the strikers pull the sluice-pin as your cavalry enters the hollow! "
                    "Your armoured destriers flounder belly-deep in red clay mire (-35% Mount Readiness, -2 HP)!"
                )
        else:
            cmd += 10 + (swing // 2)
            msg = "You halt on the crest and send dismounted scouts ahead to sound the ditches before advancing."

    # PHASE 2: THE STANDOFF AT THE HAY-WAINS
    elif step == 1:
        if action == "audit_kokeshi":
            cmd += 22 + (swing // 2)
            modify_faction(player, "faction_union", 1)
            msg = (
                "Instead of charging the pitchforks, you ride straight up to Wagon-Boss Corban's lead wain and demand his feudal toll-charter! "
                "When your lancers uncover unstamped Kokeshi contraband sacks hidden beneath the grain, Corban's bruisers pale and back down!"
            )
        elif action == "couch_lances":
            cmd += 12 + (swing // 2)
            mounts -= 15
            modify_faction(player, "faction_union", -3)
            player["reputation"] = player.get("reputation", 0) - 2
            msg = (
                "You order lances lowered and drive the warhorses straight through the overturned hay-wains! "
                "The blockade shatters in splinters, though pitchforks bloody two destriers and the valley curses Hrothgar's tyranny (-15% Mounts, -3 Union, -2 Rep)!"
            )
        else:
            cmd += 15 + (swing // 2)
            msg = "You array your lancers in a glittering line across the crossroads and summon both Joyinsorrow and Corban to your stirrup."

    # PHASE 3: THE CASTELLAN'S SETTLEMENT
    else:
        if action == "eminent_domain":
            cmd += 20 + (swing // 2)
            player["silver"] += 25
            modify_faction(player, "faction_union", 1)
            msg = (
                "Invoking Castellan Hrothgar's feudal eminent domain, you confiscate Corban's smuggling wagons for the Castle Ragmore granaries (+25s toll-fines) "
                "while granting the Fluvius farmhands a royal safe-conduct against Bailiff Seekgrace's evictions! Both the grain and the peasantry are won!"
            )
        elif action == "iron_levy":
            cmd += 15
            mounts -= 10
            modify_faction(player, "faction_union", -2)
            msg = "You requisition half the harvest at lance-point and escort the Kokeshi wagons through the sullen, conquered crossroads."
        else:
            cmd -= 10
            msg = "You withdraw the cavalry without securing the grain-wagons, leaving the crossroads unresolved."

    player["lancer_command"] = max(0, min(100, cmd))
    player["lancer_mounts"] = max(0, min(100, mounts))
    full_msg = prefix + msg + twist_str

    if player["lancer_mounts"] <= 0 or step >= 2:
        player["lancer_phase"] = "RESULT"
        tag = "GRAIN TRIBUTE SECURED!" if (player["lancer_command"] >= 70 and player["lancer_mounts"] >= 35) else "COSTLY CAVALRY SORTIE!"
        player["lancer_feedback"] = f"{full_msg} — [{tag}] Click [Return to Castle Ragmore >>]!"
        return player, player["lancer_feedback"], "MINIGAME_LANCERS"

    player["lancer_step"] = step + 1
    player["lancer_feedback"] = full_msg
    return player, None, "MINIGAME_LANCERS"


def conclude_lancers_minigame(player):
    player["ch2_mission_step"] = 4
    player["active_ch2_mission"] = None

    cmd = player.get("lancer_command", 0)
    mounts = player.get("lancer_mounts", 0)

    if cmd >= 70 and mounts >= 35:
        gain = 22 + (4 if player.get("m3c_mudtrap_scouted") else 0)
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["influence"] = player.get("influence", 0) + 1
        log = (
            f"=== MISSION COMPLETE: FEUDAL AUTHORITY UPHELD (+{gain}% Position Strength, +1 Influence)! ===\n"
            "Your heavy lancers return to Castle Ragmore with full grain-wains and unblooded horses, having outmanoeuvred both the Sunken Lane mud-trap and the Kokeshi smugglers!\n\n"
            "*** Next Mission: Speak to Castellan Hrothgar in Castle Ragmore to prepare the Great Hall for the diplomatic summit banquet with Mayor Givethanks! ***"
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 8)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: MUDDY LANCES (+8% Position Strength, +1 Exposure Tell) ===\n"
            "The grain wagons reach Castle Ragmore, though lame warhorses and bitter unrest across the southern farmlands tarnish the expedition.\n\n"
            "*** Next Mission: Speak to Castellan Hrothgar to host the diplomatic summit banquet with Mayor Givethanks! ***"
        )
    return player, log, "MAIN"


def draw_lancers_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 3C (Cavalry Deployment)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    GOLD_ACCENT = (185, 130, 35)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("FLUVIUS CROSSROADS — RAGMORE HEAVY CAVALRY DEPLOYMENT", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    cmd = player.get("lancer_command", 50)
    mounts = player.get("lancer_mounts", 90)

    screen.blit(font_bold.render(f"Feudal Command & Authority: {cmd}% (Target: 70%+)", True, GOLD_ACCENT), (85, 78))
    c_bar = pygame.Rect(410, 78, 305, 16)
    pygame.draw.rect(screen, (40, 35, 35), c_bar, border_radius=4)
    if cmd > 0:
        pygame.draw.rect(screen, GOLD_ACCENT, (410, 78, int(305 * (cmd / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, c_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Warhorse & Squadron Readiness: {mounts}%", True, TATE_RED), (85, 100))
    m_bar = pygame.Rect(410, 100, 305, 16)
    pygame.draw.rect(screen, (40, 35, 35), m_bar, border_radius=4)
    if mounts > 0:
        pygame.draw.rect(screen, TATE_RED, (410, 100, int(305 * (mounts / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, m_bar, width=1, border_radius=4)

    st_idx = min(2, player.get("lancer_step", 0))
    st_data = LANCER_PHASES[st_idx]

    s_box = pygame.Rect(85, 126, 630, 130)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 134))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 158, 600, 62), CLOCK_BLACK, max_lines=3)

    tags = []
    if player.get("m3c_mudtrap_scouted"):
        tags.append("[Sunken Lane Mud-Trap Scouted]")
    if player.get("intel_kokeshi_debt"):
        tags.append("[Seekgrace's Kokeshi Debt Known]")
    t_str = "Cavalry Reconnaissance: " + (", ".join(tags) if tags else "Unscouted (Beware of sunken road traps!)")
    screen.blit(font.render(t_str, True, (45, 125, 60) if tags else TATE_RED), (100, 230))

    fb_box = pygame.Rect(85, 264, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("lancer_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)

# =========================================================================
# 6. MISSION 3D & 3E NPCS: CELLARER OSWIN (4, 22) & REEVE GODRIC (4, 15)
# =========================================================================
def get_oswin_options(player):
    opts = ["Ask about the Great Hall wine cellars"]
    if player.get("chapter_2_route") == "Join Castellan's House Staff" and player.get("ch2_mission_step") == 4:
        opts.insert(0, "Ask about the wine & entertainers for tonight's Summit Banquet")
        if player.get("m3d_started"):
            opts.insert(0, "Mission: Ring the Great Hall Gong & Begin the Summit Banquet!")
    opts.append("Leave")
    return opts


def resolve_oswin(choice, player):
    if choice == "Leave":
        return player, "Cellarer Oswin polishes a silver flagon with a linen apron.", "MAIN"

    if choice == "Ask about the Great Hall wine cellars":
        return player, (
            "\"Three hundred casks of cider, malmsey, and vintage sack rest beneath these flagstones, Steward.\""
        ), "NPC_DIALOGUE"

    if choice == "Ask about the wine & entertainers for tonight's Summit Banquet":
        player["m3d_oswin_questioned"] = True
        return player, (
            "Cellarer Oswin wipes his brow, looking troubled.\n"
            "\"Two things are irregular tonight, Steward. First, a cask of Dark Brumaire Vintage was delivered at dusk—not up the New Road with the Mayor's escort, "
            "but rowed across Ragmore Lake to the northern jetty by a fellow with yellow mountain clay on his boots!\"\n\n"
            "\"Second, the travelling players hired to entertain the hall kept lingering near the tapestries outside Lord Hrothgar's map-room here in the inner bailey. "
            "If I were you, Steward, I would take a close look around the inner bailey gallery here and down by the **Ragmore Lake jetty** to the north before we ring the banquet gong.\""
        ), "NPC_DIALOGUE"

    if choice == "Mission: Ring the Great Hall Gong & Begin the Summit Banquet!":
        player, t_msg = execute_ch2_mission(player, "3d_summit", time_cost=120, stamina_drain=15)
        player, log, next_state = init_summit_minigame(player)
        if t_msg:
            log += "\n\n" + t_msg
        return player, log, next_state

    return player, "Error.", "MAIN"


def get_godric_reeve_options(player):
    opts = ["Ask about the Ragmore tenant harvest"]
    if player.get("chapter_2_route") == "Join Castellan's House Staff" and player.get("ch2_mission_step") == 5:
        opts.insert(0, "Audit the Tithe-Barn grain & baggage wains for the war-levy")
    opts.append("Leave")
    return opts


def resolve_godric_reeve(choice, player):
    if choice == "Leave":
        return player, "Manor Reeve Godric tallies barley sacks on a notched hazel tally-stick.", "MAIN"

    if choice == "Ask about the Ragmore tenant harvest":
        return player, (
            "\"The barley is in the sheaves, Steward, though the tenants are fearful of the coming war with Castle Laydere.\""
        ), "NPC_DIALOGUE"

    if choice == "Audit the Tithe-Barn grain & baggage wains for the war-levy":
        player["m3e_reeve_audited"] = True
        return player, (
            "Manor Reeve Godric lowers his tally-stick and points toward the heavy baggage wains outside the barn.\n"
            "\"Thank heavens you rode down from the keep, Steward! Two of the lesser gentry tried to hold back forty sacks of oats until they saw Lord Hrothgar's signet on your finger\n"
            "\"- I've loaded those sacks onto the wagons now.\"\n\n"
            "\"Before you return to the keep, take a look at the grease-buckets and wagon hubs outside this barn,\n"
            "\"and the Armoury Rack in the Castle Inner Bailey — a peddler from the eastern hills was skulking around both yesterday!\""
        ), "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# =========================================================================
# 7. MISSION 3D POP-OUT: THE GRAND BANQUET & SUMMIT (MINIGAME_SUMMIT)
# =========================================================================
SUMMIT_COURSES = [
    {
        "title": "COURSE 1/3: HIGH-TABLE PROTOCOL & SEATING!",
        "desc": (
            "Trumpets sound as Mayor Givethanks of Murum and his aldermen enter the torchlit Great Hall! "
            "Prickly Ragmore knights jostle for the seats of honour beside Lord Hrothgar. How do you seat the high table?"
        ),
    },
    {
        "title": "COURSE 2/3: THE MINSTRELS' GALLERY & THE MAP-ROOM!",
        "desc": (
            "As the roasted venison is carved and the players strike up a lively masque in the gallery, "
            "you spot a cloaked performer slipping behind the Great Hall tapestries toward Lord Hrothgar's private war-map chamber!"
        ),
    },
    {
        "title": "COURSE 3/3: THE CEREMONIAL ALLIANCE TOAST!",
        "desc": (
            "Castellan Hrothgar rises to seal Murum's financial alliance with a ceremonial toast! Three silver flagons stand on the sideboard: "
            "**Dark Brumaire Vintage**, **Spiced Fluvius Cider**, and **Amber Cellar Malmsey**. A nervous server reaches for the Dark Brumaire Vintage!"
        ),
    },
]


def init_summit_minigame(player):
    """Initializes the Mission 3D Diplomatic Banquet & Counter-Espionage Pop-Out."""
    player["summit_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["summit_course"] = 0
    base_harm = 45 + (player.get("influence", 0) * 3) + (player.get("charisma", 0) * 2)
    if player.get("mayors_house_shifts", 0) > 0 or "mayors footman" in player.get("skills", []):
        base_harm += 15  # Chapter 1 Mayor's Footman background shines here!
    player["summit_harmony"] = min(85, base_harm)
    player["summit_vigilance"] = 50 + (15 if player.get("m3d_lake_vial_found") else 0) + (15 if player.get("m3d_tapestry_checked") else 0)
    player["summit_vigilance"] = min(95, player["summit_vigilance"])
    player["summit_feedback"] = (
        "The Great Hall blazes with a hundred beeswax candles! "
        "Guide the banquet through all 3 courses—raise Diplomatic Harmony to 70%+ and foil the plotters in the hall!"
    )
    return player, player["summit_feedback"], "MINIGAME_SUMMIT"


def summit_action(action, player):
    """Processes 2d6 protocol, counter-espionage, and poison-interception rolls in MINIGAME_SUMMIT."""
    if player.get("summit_phase") == "RESULT":
        return conclude_summit_minigame(player)

    course = player.get("summit_course", 0)
    harm = player.get("summit_harmony", 50)
    vig = player.get("summit_vigilance", 50)

    swing, prefix, twist_str = roll_castellan_2d6_twist(player, context="summit")
    msg = ""

    # COURSE 1: HIGH-TABLE PROTOCOL & SEATING
    if course == 0:
        if action == "equal_dais":
            harm += 20 + (swing // 2)
            msg = (
                "Drawing on impeccable statecraft, you seat Mayor Givethanks at Hrothgar's right hand on an equal velvet cushion while placing the Knight-Marshal opposite to toast Murum's guilds! Both townsmen and knights beam with pride!"
            )
        elif action == "flatter_mayor":
            harm += 12 + (swing // 2)
            vig -= 5
            msg = "You shower the Murum delegation with the finest dishes—pleasing Mayor Givethanks, though Hrothgar's knights mutter into their beards."
        else:
            harm -= 15
            msg = "Seating the Murum delegation below the salt infuriates Mayor Givethanks, who threatens to withhold the municipal war-loan (-15% Harmony)!"

    # COURSE 2: THE MINSTRELS' GALLERY & THE MAP-ROOM (COUNTERING 10D)
    elif course == 1:
        if action == "trap_spy":
            if player.get("m3d_tapestry_checked") or player.get("stealth", 0) >= 4:
                harm += 15
                vig += 20
                player["silver"] += 15
                msg = (
                    "Because you already barred the inner map-room door, the theatrical spy rattles the handle in vain! "
                    "You step silently behind the tapestry and seize their satchel of **15 silver** and forged keys without disturbing a single guest at the table! (+15s)"
                )
            else:
                harm -= 10
                vig -= 15
                msg = (
                    "You lunge behind the tapestry, but because the map-room latch was left unbarred, the spy slips out the casement window after knocking over a candelabrum (-10% Harmony, -15% Vigilance)!"
                )
        elif action == "double_sentries":
            harm += 5 + (swing // 2)
            vig += 10
            msg = "You quietly motion two halberdiers to stand before the tapestry arch, forcing the curious performer to retreat back to the gallery stage."
        else:
            harm -= 20
            vig -= 20
            msg = "While you ignore the gallery, the backstage spy slips into Hrothgar's study and makes off with copies of the eastern river-ford maps (-20% Harmony, -20% Vigilance)!"

    # COURSE 3: THE CEREMONIAL ALLIANCE TOAST (THE LAYDERE POISONER)
    else:
        if action == "serve_cider_expose":
            if player.get("m3d_lake_vial_found") or player.get("m3d_oswin_questioned") or vig >= 75:
                harm += 25 + (swing // 2)
                vig += 20
                msg = (
                    "You stay the server's hand, pour the wholesome **Spiced Fluvius Cider** for the toast, and force the server to smell the **Dark Brumaire Vintage**—exposing the bitter-almond poison and the **Castle Laydere wax seal** found at the lake jetty!\n"
                    "Lord Hrothgar roars with approval and Mayor Givethanks signs the full Murum War-Loan on the spot!"
                )
            else:
                harm += 10
                msg = "By fortunate instinct, you serve the Spiced Cider instead of the Dark Brumaire Vintage, averting tragedy at the high table!"
        elif action == "pour_brumaire":
            harm -= 45
            vig -= 40
            player["health"] = max(1, player.get("health", 10) - 2)
            msg = (
                "CATASTROPHE! You allow the **Dark Brumaire Vintage** to be poured! Lord Hrothgar's cup-bearer takes the first sip and collapses clutching his throat as the smell of bitter almonds fills the hall! "
                "The summit dissolves into chaos (-45% Harmony)!"
            )
        else:
            harm -= 15
            msg = "You smash the goblet on the flagstones without presenting the jetty evidence—saving Hrothgar, but terrifying Mayor Givethanks (-15% Harmony)!"

    player["summit_harmony"] = max(0, min(100, harm))
    player["summit_vigilance"] = max(0, min(100, vig))
    full_msg = prefix + msg + twist_str

    if course >= 2:
        player["summit_phase"] = "RESULT"
        tag = "ALLIANCE SEALED & POISONER FOILED!" if player["summit_harmony"] >= 70 else "CHAOTIC SUMMIT BANQUET!"
        player["summit_feedback"] = f"{full_msg} — [{tag}] Click [Conclude Summit Banquet >>]!"
        return player, player["summit_feedback"], "MINIGAME_SUMMIT"

    player["summit_course"] = course + 1
    player["summit_feedback"] = full_msg
    return player, None, "MINIGAME_SUMMIT"


def conclude_summit_minigame(player):
    player["ch2_mission_step"] = 5
    player["active_ch2_mission"] = None

    harm = player.get("summit_harmony", 0)
    if harm >= 70:
        gain = 22 + (4 if player.get("m3d_lake_vial_found") else 0) + (4 if player.get("m3d_tapestry_checked") else 0)
        player["position_strength"] = player.get("position_strength", 0) + gain
        player["influence"] = player.get("influence", 0) + 2
        player["reputation"] = player.get("reputation", 0) + 2
        log = (
            f"=== MISSION COMPLETE: TRIUMPH IN THE GREAT HALL (+{gain}% Position Strength, +2 Influence, +2 Reputation)! ===\n"
            "You orchestrated a flawless state banquet, foiled both the backstage map-thief and the Castle Laydere poisoner, and sealed Murum's financial alliance with Castle Ragmore!\n\n"
            "*** Final Mission: War with Castle Laydere has begun! Speak to Castellan Hrothgar to muster the Feudal Levy (and inspect the Castle Armoury and the Ragmore Manor Tithe-Barn first)! ***"
        )
    else:
        player["position_strength"] = max(0, player.get("position_strength", 0) + 5)
        player["exposure_tells"] = player.get("exposure_tells", 0) + 1
        log = (
            "=== MISSION COMPLETE: A SHAKEN SUMMIT (+5% Position Strength, +1 Exposure Tell) ===\n"
            "Mayor Givethanks departs at dawn with only a partial war-pledge after the commotion in the Great Hall.\n\n"
            "*** Final Mission: Speak to Castellan Hrothgar to muster the Feudal Levy for war! ***"
        )
    return player, log, "MAIN"


def draw_summit_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 3D (The Grand Banquet)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    GOLD_ACCENT = (185, 130, 35)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("CASTLE RAGMORE GREAT HALL — THE DIPLOMATIC SUMMIT BANQUET", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    harm = player.get("summit_harmony", 50)
    vig = player.get("summit_vigilance", 50)

    screen.blit(font_bold.render(f"Diplomatic Harmony & Alliance: {harm}% (Target: 70%+)", True, GOLD_ACCENT), (85, 78))
    h_bar = pygame.Rect(425, 78, 290, 16)
    pygame.draw.rect(screen, (40, 35, 35), h_bar, border_radius=4)
    if harm > 0:
        pygame.draw.rect(screen, GOLD_ACCENT, (425, 78, int(290 * (harm / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, h_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Counter-Espionage Vigilance: {vig}%", True, TATE_RED), (85, 100))
    v_bar = pygame.Rect(425, 100, 290, 16)
    pygame.draw.rect(screen, (40, 35, 35), v_bar, border_radius=4)
    if vig > 0:
        pygame.draw.rect(screen, TATE_RED, (425, 100, int(290 * (vig / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, v_bar, width=1, border_radius=4)

    c_idx = min(2, player.get("summit_course", 0))
    c_data = SUMMIT_COURSES[c_idx]

    c_box = pygame.Rect(85, 126, 630, 130)
    pygame.draw.rect(screen, (252, 248, 238), c_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, c_box, width=2, border_radius=8)

    screen.blit(font_bold.render(c_data["title"], True, TATE_RED), (100, 134))
    draw_fitted_text(screen, c_data["desc"], pygame.Rect(100, 158, 600, 62), CLOCK_BLACK, max_lines=3)

    tags = []
    if player.get("m3d_lake_vial_found"):
        tags.append("[Lake Jetty Poison & Laydere Seal Found]")
    if player.get("m3d_tapestry_checked"):
        tags.append("[Map-Room Tapestry Barred]")
    if player.get("m3d_oswin_questioned"):
        tags.append("[Cellarer Oswin's Wine Report]")
    t_str = "Household Security: " + (", ".join(tags) if tags else "Unchecked (High risk of poison & espionage!)")
    screen.blit(font.render(t_str, True, (45, 125, 60) if tags else TATE_RED), (100, 230))

    fb_box = pygame.Rect(85, 264, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("summit_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)


# =========================================================================
# 8. MISSION 3E POP-OUT: MUSTERING THE FEUDAL LEVY (MINIGAME_LEVY)
# =========================================================================
LEVY_DECREES = [
    {
        "title": "MUSTER DECREE 1/3: THE ARMOURY & VANGUARD STEEL!",
        "desc": (
            "Three hundred feudal retainers and men-at-arms muster in the inner bailey demanding lances, mail-shirts, and crossbows! "
            "How do you equip the vanguard host?"
        ),
    },
    {
        "title": "MUSTER DECREE 2/3: THE BAGGAGE TRAIN & COMMISSARY GRAIN!",
        "desc": (
            "An army marches on its stomach. The heavy supply wains from the Ragmore Manor Tithe-Barn are waiting to be hitched for the march toward the eastern river-crossings."
        ),
    },
    {
        "title": "MUSTER DECREE 3/3: THE BARONIAL KNIGHTS & CAVALRY MOUNTS!",
        "desc": (
            "The lesser gentry of Ragmore Plains grumble about risking their prized destriers in the opening clash against Castle Laydere. "
            "How do you marshal the mounted chivalry for Lord Hrothgar?"
        ),
    },
]


def init_levy_minigame(player):
    """Initializes the Mission 3E Grand Feudal Levy Mobilisation Pop-Out."""
    player["levy_phase"] = "ACTIVE"  # "ACTIVE" or "RESULT"
    player["levy_step"] = 0
    base_ready = 40 + (player.get("influence", 0) * 3) + (player.get("equusense", 0) * 2)
    if player.get("m3e_armoury_fixed"):
        base_ready += 12
    if player.get("m3e_wagons_fixed"):
        base_ready += 12
    if player.get("m3e_reeve_audited"):
        base_ready += 8
    player["levy_readiness"] = min(88, base_ready)
    player["levy_morale"] = 75
    player["levy_feedback"] = (
        "War-banners snap from every tower of Castle Ragmore! "
        "Issue 3 Mobilisation Decrees to raise Total Levy Readiness to 75%+ before marching to war!"
    )
    return player, player["levy_feedback"], "MINIGAME_LEVY"


def levy_action(action, player):
    """Processes 2d6 logistics and feudal mobilisation rolls in MINIGAME_LEVY."""
    if player.get("levy_phase") == "RESULT":
        return conclude_levy_minigame(player)

    step = player.get("levy_step", 0)
    ready = player.get("levy_readiness", 45)
    morale = player.get("levy_morale", 75)

    swing, prefix, twist_str = roll_castellan_2d6_twist(player, context="levy")
    msg = ""

    # DECREE 1: THE ARMOURY & VANGUARD STEEL
    if step == 0:
        if action == "issue_reserve_steel":
            if player.get("m3e_armoury_fixed") or "forge" in player.get("skills", []):
                ready += 20 + (swing // 2)
                morale += 10
                msg = (
                    "Having already culled the brittle Kokeshi lance-heads from the Armoury Rack, you issue oil-tempered Ragmore steel to every halberdier and lancer! The men cheer the ring of true iron!"
                )
            else:
                ready -= 10
                morale -= 20
                msg = (
                    "CRACK! Because you never inspected the Armoury Rack in the inner bailey, half the newly issued lance-heads snap during the muster inspection (-10% Readiness, -20% Morale)!"
                )
        elif action == "buy_guild_arms":
            if player.get("silver", 0) >= 25:
                player["silver"] -= 25
                ready += 18 + (swing // 2)
                morale += 5
                msg = "You spend 25 silver from your own purse to purchase spare steel longbows and mail-coifs from the guild armourers (-25s, +18% Readiness)!"
            else:
                ready -= 5
                msg = "You lack the 25 silver required to purchase emergency guild weapons!"
        else:
            ready += 5
            morale -= 15
            msg = "You send the rear ranks out with un-checked spears and padded jacks (-15% Morale)."

    # DECREE 2: THE BAGGAGE TRAIN & COMMISSARY GRAIN
    elif step == 1:
        if action == "roll_tithe_wagons":
            if player.get("m3e_wagons_fixed") and player.get("m3e_reeve_audited"):
                ready += 22 + (swing // 2)
                morale += 10
                msg = (
                    "With Reeve Godric's full barley tithe loaded and the grit-sabotaged axle-grease scrubbed from every hub, the Ragmore supply train rolls through the barbican without a single squeaking wheel!"
                )
            elif player.get("m3e_wagons_fixed") or player.get("m3e_reeve_audited"):
                ready += 12 + (swing // 2)
                msg = "Your partial inspection at the Tithe-Barn keeps the main supply wagons moving, though a rear axle runs hot on the road."
            else:
                ready -= 15
                morale -= 15
                msg = (
                    "SCREECH! Because you never inspected the grease-buckets at the Manor Tithe-Barn, quartz grit seizes three baggage-wain axles right in the castle gateway (-15% Readiness, -15% Morale)!"
                )
        elif action == "fair_commissary":
            ready += 14 + (swing // 2)
            morale += 10
            msg = "You guarantee silver promissory notes for every tenant bushel requisitioned, keeping the Ragmore peasantry loyal to the keep!"
        else:
            ready += 8
            morale -= 20
            msg = "Forcibly seizing the tenants' seed-barley fills the wagons but leaves the countryside muttering of rebellion (-20% Morale)!"

    # DECREE 3: THE BARONIAL KNIGHTS & CAVALRY MOUNTS
    else:
        if action == "sage_or_charter":
            if "sage's charter" in player.get("inventory", []) or "ancient castellan signet" in player.get("inventory", []) or player.get("influence", 0) >= 6:
                ready += 22 + (swing // 2)
                morale += 15
                msg = (
                    "Holding aloft the ancient seal of the realm and invoking your hard-won authority, you bind every knight and squire of Ragmore Plains under an unbreakable oath of chivalry!"
                )
            else:
                ready += 12 + (swing // 2)
                msg = "You appeal to the knights' feudal honour, bringing most of the mounted gentry into line."
        elif action == "lead_vanguard":
            ready += 18 + (player.get("equusense", 0) // 2) + (swing // 2)
            morale += 10
            msg = "Vaulting onto your own destrier, you challenge any hesitant banneret to ride abreast of your stirrup in the first charge—shaming every knight into the saddle!"
        else:
            ready += 5
            morale -= 15
            msg = "Threatening the gentry with forfeiture brings out their horses, but leaves the officers bickering (-15% Morale)."

    player["levy_readiness"] = max(0, min(100, ready))
    player["levy_morale"] = max(0, min(100, morale))
    full_msg = prefix + msg + twist_str

    if step >= 2:
        player["levy_phase"] = "RESULT"
        tag = "GRAND HOST MOBILISED AT FULL STRENGTH!" if player["levy_readiness"] >= 70 else "FRACTURED FEUDAL LEVY!"
        player["levy_feedback"] = f"{full_msg} — [{tag}] Click [March to War (Enter Chapter 3) >>]!"
        return player, player["levy_feedback"], "MINIGAME_LEVY"

    player["levy_step"] = step + 1
    player["levy_feedback"] = full_msg
    return player, None, "MINIGAME_LEVY"


def conclude_levy_minigame(player):
    player["ch2_mission_step"] = 6
    player["active_ch2_mission"] = None

    ready = player.get("levy_readiness", 0)
    morale = player.get("levy_morale", 0)

    if ready >= 70 and morale >= 40:
        player.setdefault("ch3_world_bits", {})["track_3"] = 1
        player["position_strength"] = min(100, player.get("position_strength", 0) + 25)
        player["reputation"] = player.get("reputation", 0) + 4
        log = (
            "=========================================================\n"
            "   MISSION COMPLETE: THE GRAND ARMY OF RAGMORE!       \n"
            "=========================================================\n"
            "By your logistical mastery and sharp eye for sabotage, Castle Ragmore's feudal host marches out of the barbican with sound steel, clean axles, and unshakeable morale!\n"
            "Lord Hrothgar salutes you with his drawn greatsword as the war of Chapter 3 begins!\n\n"
            f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
        )
    else:
        player.setdefault("ch3_world_bits", {})["track_3"] = 0
        player["exposure_tells"] = player.get("exposure_tells", 0) + 2
        log = (
            "=== MISSION COMPLETE: A FRACTURED LEVY ===\n"
            "Bogged down by snapped lance-heads, gritty wagon axles, and bickering gentry, Castle Ragmore marches to war with an under-equipped and mutinous host (+2 Exposure Tells)!\n\n"
            f"*** Final Position Strength: {player.get('position_strength', 0)}% | Exposure Tells: {player.get('exposure_tells', 0)} ***"
        )
    return player, log, "CHAPTER_2_COMPLETE"


def draw_levy_ui(screen, player, font, font_bold, mouse_pos):
    """Draws the centered 680x480 Tate Britain Pop-Out Window for Mission 3E (The Feudal Levy)."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)
    GOLD_ACCENT = (185, 130, 35)

    panel = pygame.Rect(60, 40, 680, 480)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    title = font_bold.render("CASTLE RAGMORE WAR-TABLE — MUSTERING THE FEUDAL LEVY", True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 50))

    ready = player.get("levy_readiness", 45)
    morale = player.get("levy_morale", 75)

    screen.blit(font_bold.render(f"Total Levy Readiness: {ready}% (Target: 70%+)", True, (45, 125, 60) if ready >= 70 else GOLD_ACCENT), (85, 78))
    r_bar = pygame.Rect(395, 78, 320, 16)
    pygame.draw.rect(screen, (40, 35, 35), r_bar, border_radius=4)
    if ready > 0:
        pygame.draw.rect(screen, (45, 125, 60) if ready >= 70 else GOLD_ACCENT, (395, 78, int(320 * (ready / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, r_bar, width=1, border_radius=4)

    screen.blit(font_bold.render(f"Baronial & Peasant Morale: {morale}%", True, TATE_RED), (85, 100))
    m_bar = pygame.Rect(395, 100, 320, 16)
    pygame.draw.rect(screen, (40, 35, 35), m_bar, border_radius=4)
    if morale > 0:
        pygame.draw.rect(screen, TATE_RED, (395, 100, int(320 * (morale / 100.0)), 16), border_radius=4)
    pygame.draw.rect(screen, CLOCK_BLACK, m_bar, width=1, border_radius=4)

    st_idx = min(2, player.get("levy_step", 0))
    st_data = LEVY_DECREES[st_idx]

    s_box = pygame.Rect(85, 126, 630, 130)
    pygame.draw.rect(screen, (252, 248, 238), s_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, s_box, width=2, border_radius=8)

    screen.blit(font_bold.render(st_data["title"], True, TATE_RED), (100, 134))
    draw_fitted_text(screen, st_data["desc"], pygame.Rect(100, 158, 600, 62), CLOCK_BLACK, max_lines=3)

    tags = []
    if player.get("m3e_armoury_fixed"):
        tags.append("[Armoury Lances Tempered]")
    if player.get("m3e_wagons_fixed"):
        tags.append("[Tithe-Barn Axles Cleaned]")
    if player.get("m3e_reeve_audited"):
        tags.append("[Reeve Godric's Grain Tally]")
    t_str = "Quartermaster Audits: " + (", ".join(tags) if tags else "Unchecked (Sabotage risk in Armoury & Tithe-Barn!)")
    screen.blit(font.render(t_str, True, (45, 125, 60) if tags else TATE_RED), (100, 230))

    fb_box = pygame.Rect(85, 264, 630, 62)
    pygame.draw.rect(screen, (30, 34, 42), fb_box, border_radius=8)
    pygame.draw.rect(screen, TATE_RED, fb_box, width=2, border_radius=8)
    draw_fitted_text(screen, player.get("levy_feedback", ""), fb_box.inflate(-14, -8), (245, 240, 230), max_lines=2)

# =========================================================================
# MODULE REGISTRATION (HANDLERS)
# =========================================================================
HANDLERS = {
    "ceolwulf":     (get_ceolwulf_options, resolve_ceolwulf),
    "aethelstan":   (get_aethelstan_options, resolve_aethelstan),
    "oswin":        (get_oswin_options, resolve_oswin),
    "godric_reeve": (get_godric_reeve_options, resolve_godric_reeve),
}
