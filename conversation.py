"""
conversation.py
---------------
Master dialogue switchboard for Dtessera Terra.
Aggregates NPC dialogue handlers across all Chapter 1 and Chapter 2 modules
and routes forest animal encounters and merchant stalls.
"""

import math
import encounters
from mechanics import modify_faction, consume_fresh_food_timestamp

import convo_market
import convo_high_street
import convo_blacksmith
import convo_stables
import convo_wallmakers
import convo_mayor_town
import chapter_2
import ch2_union
import ch2_guard
import ch2_roguery

FOREST_ANIMAL_TYPES = {
    "forest owls",
    "forest squirrels",
    "forest deer",
    "forest armadillo",
}

# -------------------------------------------------------------------------
# MASTER UI SWITCHBOARD (AGGREGATED DISPATCH TABLE)
# -------------------------------------------------------------------------
NPC_HANDLERS = {}
for module in (
    convo_market,
    convo_high_street,
    convo_blacksmith,
    convo_stables,
    convo_wallmakers,
    convo_mayor_town,
    chapter_2,
    ch2_union,
    ch2_guard,
):
    NPC_HANDLERS.update(module.HANDLERS)


def _get_combined_fairlight_options(player):
    """
    Combines Chapter 1 (Mayor's House Shift 4 & Market Shift 1) and
    Chapter 2 (Track 10 Acting Troupe) options for Fairlight so neither overwrites the other.
    """
    if player.get("active_mayor_task") == "playhouse_meet":
        return convo_mayor_town.get_fairlight_options(player)

    opts = []
    if player.get("chapter_2_route") == "Join Fairlight's Acting Troupe":
        ch2_opts = ch2_roguery.get_fairlight_roguery_options(player)
        opts.extend(o for o in ch2_opts if o.startswith("Mission"))

    for base_opt in convo_mayor_town.get_fairlight_options(player):
        if base_opt not in opts:
            opts.append(base_opt)
    return opts


def _resolve_combined_fairlight(choice, player):
    """Routes Fairlight choices to Chapter 2 for Mission 10a-10e, or Chapter 1 otherwise."""
    if choice.startswith("Mission"):
        return ch2_roguery.resolve_fairlight_roguery(choice, player)
    return convo_mayor_town.resolve_fairlight(choice, player)


NPC_HANDLERS["fairlight"] = (_get_combined_fairlight_options, _resolve_combined_fairlight)


# -------------------------------------------------------------------------
# LIGNUM FOREST ANIMAL ENCOUNTERS (THE GREAT SCHISM)
# -------------------------------------------------------------------------
def get_forest_animal_options(npc_name, player):
    """Returns dialogue options for Vanguardist or Communard woodland animals."""
    pos_key = f"{player['x']},{player['y']}"
    allegiance = player.get("forest_tile_allegiance", {}).get(pos_key, "communard")

    if allegiance == "vanguardist":
        return [
            "Pledge solidarity with the Vanguard (+Vanguardists)",
            "Urge them to make peace with the Communards (+Communards)",
            "Draw weapon and fight them",
            "Leave",
        ]

    opts = [
        "Ask about the Great Schism of the Forest",
        "Ask for bearings out of the woods",
    ]
    if any(f in player.get("inventory", []) for f in ("cobnuts", "carrot", "apple", "pear")):
        opts.append("Share food in Mutual Aid (+Communards, +Equusense)")
    opts.append("Leave")
    return opts


def resolve_forest_animal(npc_name, choice, player):
    """Resolves player interaction with woodland animals in Lignum Forest."""
    species_label = npc_name.replace("forest ", "").title()
    pos_key = f"{player['x']},{player['y']}"

    if choice == "Leave":
        return player, f"You bow respectfully to the {species_label} and step back beneath the boughs.", "MAIN"

    if choice == "Draw weapon and fight them":
        return encounters.trigger_forest_animal_combat(player, npc_name)

    if choice == "Pledge solidarity with the Vanguard (+Vanguardists)":
        modify_faction(player, "faction_vanguardists", 2)
        modify_faction(player, "faction_communards", -1)
        player.setdefault("territories", {})[pos_key] = "Vanguardists"
        log = (
            f"The Vanguardist {species_label} salute your oath.\n"
            "\"Every week the townsfolk of Murum, Parvus, and Fluvius clear another league of ancient trees to feed their insatiable appetite for farmland!\"\n"
            "\"The Communards think we can share the remaining glades in peace, but if we do not fight back, there will be no forest left to share!\"\n"
            "*** (+2 Vanguardists Faction, -1 Communards Faction | Tile marked as Vanguardists Territory!) ***"
        )
        return player, log, "MAIN"

    if choice == "Urge them to make peace with the Communards (+Communards)":
        modify_faction(player, "faction_communards", 2)
        modify_faction(player, "faction_vanguardists", -1)
        player.setdefault("territories", {})[pos_key] = "Communards"
        log = (
            "You speak passionately of mutual aid and warn that endless bloodshed will only bring the Castellan's soldiers into the woods.\n"
            f"The {species_label} lower their guard, pondering your words.\n"
            "*** (+2 Communards Faction, -1 Vanguardists Faction | Tile marked as Communards Territory!) ***"
        )
        return player, log, "MAIN"

    if choice == "Ask about the Great Schism of the Forest":
        player.setdefault("territories", {})[pos_key] = "Communards"
        log = (
            f"The Communard {species_label} gather around you peacefully.\n"
            "\"When the townsfolk's axes and ploughs began devouring the borders of Lignum Forest to turn our home into farmland, the council of animals broke in two.\"\n"
            "\"Half became the **Vanguardists**—militant defenders who ambush travellers and drag intruders to their hideout in the deepest part of the forest.\"\n"
            "\"We are the **Communards**. We chose to live in peaceful woodland communes, sharing what the canopy provides with all who walk gently.\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Ask for bearings out of the woods":
        x, y = player["x"], player["y"]

        def _dir_and_leagues(tx, ty):
            dx, dy = tx - x, ty - y
            dist = max(1, int(round(math.hypot(dx, dy) / 2.0)))
            ns = "North" if dy > 1 else ("South" if dy < -1 else "")
            ew = "East" if dx > 1 else ("West" if dx < -1 else "")
            card = f"{ns}-{ew}" if (ns and ew) else (ns or ew or "nearby")
            unit = "league" if dist == 1 else "leagues"
            return f"about {dist} {unit} {card}"

        parvus_dir = _dir_and_leagues(17, 22)
        glade_dir = _dir_and_leagues(16, 15)
        road_dir = _dir_and_leagues(7, y)
        log = (
            f"The Communard {species_label} lift their heads to scent the breeze filtering through the boughs:\n"
            f"\"If you seek the coastal gates of **Parvus Town**, press **{parvus_dir}** through the canopy.\"\n"
            f"\"The peaceful **Lignum Forest Glade** lies **{glade_dir}** from this hollow, while the cobbles of **The New Road** run **{road_dir}** toward the western treeline.\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice.startswith("Share food in Mutual Aid"):
        food = next((f for f in ("cobnuts", "carrot", "apple", "pear") if f in player["inventory"]), None)
        if food:
            player["inventory"].remove(food)
            consume_fresh_food_timestamp(player, food)
            modify_faction(player, "faction_communards", 2)
            player["equusense"] = player.get("equusense", 0) + 1
            player["hunger"] = min(100, player["hunger"] + 25)
            player["thirst"] = min(100, player["thirst"] + 25)
            player.setdefault("territories", {})[pos_key] = "Communards"
            log = (
                f"You share your {food} with the Communard {species_label}.\n"
                "In the spirit of woodland mutual aid, they lead you to a clear spring and offer sweet wild roots in return!\n"
                "*** (+2 Communards Faction, +1 Equusense, +25 Hunger, +25 Thirst | Tile marked as Communards Territory!) ***"
            )
            return player, log, "MAIN"

    return player, "Conversation ended.", "MAIN"


# -------------------------------------------------------------------------
# PUBLIC ENTRY POINTS FOR MAIN ENGINE
# -------------------------------------------------------------------------
def get_npc_dialogue_options(npc_name, player):
    """Returns a list of string labels for the UI buttons when speaking to `npc_name`."""
    if npc_name in FOREST_ANIMAL_TYPES:
        return get_forest_animal_options(npc_name, player)
    if npc_name in convo_market.MERCHANT_TYPES:
        return convo_market.get_merchant_options(npc_name, player)

    base_opts = NPC_HANDLERS[npc_name][0](player) if npc_name in NPC_HANDLERS else ["Leave"]

    # Mission 1E Hook: Allow convening the Unbiased Traitor Tribunal at Murum Union House
    if (
        npc_name in ("union clerk", "truthtale", "union rep")
        and player.get("chapter_2_route") == "Stand for Union Official"
        and player.get("ch2_mission_step") == 5
    ):
        tribunal_opt = "Mission: Convene Unbiased Tribunal to Unmask the Fluvius Traitor"
        if tribunal_opt not in base_opts:
            return [tribunal_opt] + base_opts

    return base_opts


def handle_npc_choice(npc_name, choice_label, player):
    """Executes the chosen dialogue option and returns (player_dict, log_string, new_menu_state)."""
    if (
        npc_name in ("union clerk", "truthtale", "union rep")
        and choice_label == "Mission: Convene Unbiased Tribunal to Unmask the Fluvius Traitor"
    ):
        return ch2_union.init_traitor_tribunal(player)

    if npc_name in FOREST_ANIMAL_TYPES:
        return resolve_forest_animal(npc_name, choice_label, player)
    if npc_name in convo_market.MERCHANT_TYPES:
        return convo_market.resolve_merchant(npc_name, choice_label, player)
    if npc_name in NPC_HANDLERS:
        res = NPC_HANDLERS[npc_name][1](choice_label, player)
        if res is not None:
            return res

    return player, "Conversation ended.", "MAIN"
