import game_data as db
from mechanics import (
    get_inventory_weight,
    get_max_carry_weight,
    sell_item_helper,
    format_item_name
)
import mini_games

# -------------------------------------------------------------------------
# THE ARMOURER (HIGH STREET WEAPON & SHIELD SHOP)
# -------------------------------------------------------------------------
ARMOURER_STOCK = [
    ("iron dagger", 15, "2–5 Dmg"),
    ("iron sword", 30, "2–8 Dmg"),
    ("steel longsword", 75, "2–10 Dmg"),
    ("shield", 10, "Blocks 1 Dmg"),
    ("heavy shield", 30, "Blocks 3 Dmg"),
]

def get_armourer_options(player):
    if player.get("armourer_state") == "shopping":
        discount = max(0, player.get("charisma", 0) - 10)
        opts = []
        for item_key, base_cost, stat_tag in ARMOURER_STOCK:
            cost = max(1, base_cost - discount)
            opts.append(f"Buy {format_item_name(item_key)} ({cost}s | {stat_tag})")
        opts.append("< Back")
        return opts

    options = ["Browse Weapons & Shields"]
    if "custom breastplate" in player["inventory"]:
        options.append("Deliver Breastplate")
    options.append("Ask about Shields & Defence")
    options.append("Leave")
    return options


def resolve_armourer(choice, player):
    if choice == "Leave":
        player["armourer_state"] = None
        return player, "You step away from the armourer's bench.", "MAIN"

    if choice == "< Back":
        player["armourer_state"] = None
        return player, "\"Take your time! Good steel saves lives on the New Road.\"", "NPC_DIALOGUE"

    if choice == "Browse Weapons & Shields":
        player["armourer_state"] = "shopping"
        return player, "\"Every blade forged by Lovejoy, and shields banded in Murum iron! What do you need?\"", "NPC_DIALOGUE"

    if choice == "Ask about Shields & Defence":
        log = (
            "The Armourer raps their knuckles against an iron-banded shield.\n"
            "\"A weapon helps you strike harder, but a Shield keeps you standing!\"\n"
            "\"Use 'Action -> Equip' to strap a shield to your off-hand alongside your weapon.\"\n"
            "\"A standard Wooden Shield absorbs 1 point of damage from every blow in combat, while a Heavy Shield absorbs up to 3 points of damage per strike!\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice == "Deliver Breastplate":
        player["inventory"].remove("custom breastplate")
        player["silver"] += 5
        log = (
            "The Armourer inspects the gleaming steel breastplate with a wide grin.\n"
            "\"Magnificent! Lovejoy's hammer work is second to none.\"\n"
            "\"Here, take this for your trouble. A thirsty runner is a slow runner!\"\n"
            f"*** Breastplate delivered! You received a 5 silver tip! (Total: {player['silver']}) ***"
        )
        return player, log, "MAIN"

    if choice.startswith("Buy "):
        discount = max(0, player.get("charisma", 0) - 10)
        raw_name = choice[4:].split(" (")[0].lower()
        if raw_name in db.item_database:
            final_price = max(1, db.item_database[raw_name]["price"] - discount)
            item_w = db.item_database[raw_name].get("weight", 2.0)
            if get_inventory_weight(player) + item_w > get_max_carry_weight(player) + 15.0:
                return player, "\"You're already carrying too much weight to haul more armour! Lighten your pack first.\"", "NPC_DIALOGUE"
            if player["silver"] >= final_price:
                player["silver"] -= final_price
                player["inventory"].append(raw_name)
                return player, (
                    f"You hand over {final_price} silver and take the {format_item_name(raw_name)}.\n"
                    f"*** Bought {format_item_name(raw_name)}! Use 'Action -> Equip' to ready it for combat. (Remaining Silver: {player['silver']}s) ***"
                ), "NPC_DIALOGUE"
            return player, f"\"You need {final_price} silver for that, and you only have {player['silver']}s!\"", "NPC_DIALOGUE"

    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# THE APOTHECARY (HIGH STREET MEDICINE & REMEDY SHOP)
# -------------------------------------------------------------------------
APOTHECARY_STOCK = [
    ("flu medicine", 15, "Cures Damp-Chill"),
    ("charcoal bitters", 12, "Cures Food Poisoning"),
    ("wound salve", 14, "Cures Wound Sepsis"),
    ("empty flask", 10, "Holds 2 Drinks"),
    ("birthing tonic", 10, "Equine Labour Aid"),
]

def get_apothecary_options(player):
    if player.get("apothecary_state") == "shopping":
        discount = max(0, player.get("charisma", 0) - 10)
        opts = []
        for item_key, base_cost, stat_tag in APOTHECARY_STOCK:
            cost = max(1, base_cost - discount)
            opts.append(f"Buy {format_item_name(item_key)} ({cost}s | {stat_tag})")
        opts.append("< Back")
        return opts

    options = []
    if "apothecary's parcel" in player["inventory"]:
        options.append("Deliver Apothecary's Parcel")

    if (
        player.get("current_job") == "market"
        and player.get("market_sweeper_shifts") == 2
        and player.get("active_market_task") is not None
        and not player.get("market_sq3_done")
        and not player.get("market_sq3_failed")
    ):
        options.append("Help mix Fever-Draught (Side-Quest)")

    options.append("Browse Medicines and Remedies")
    options.append("Leave")
    return options


def resolve_apothecary(choice, player):
    if choice == "Leave":
        player["apothecary_state"] = None
        return player, "You step away from the apothecary's counter.", "MAIN"

    if choice == "< Back":
        player["apothecary_state"] = None
        return player, "\"Take your time! They are all good salves and cures, I assure you.\"", "NPC_DIALOGUE"

    if choice == "Deliver Apothecary's Parcel":
        player["inventory"].remove("apothecary's parcel")
        player["active_market_task"] = "report_market_shift_2"
        player["silver"] += 5
        log = (
            "The Apothecary snatches the parcel with trembling hands and immediately uncorks the vial of Moon-Blight Extract.\n"
            "\"Thank the heavens! You actually caught Fleetfoot on their rounds! You have saved a life today, my friend.\"\n"
            "\"Take this 5 silver tip for your swift feet, and let Godwin know the delivery is safe!\"\n\n"
            f"*** Parcel Delivered! You received a 5 silver tip! (Total: {player['silver']}) ***\n"
            "*** Return to Godwin Williams at the Food Market to complete your shift! ***"
        )
        return player, log, "MAIN"

    if choice == "Help mix Fever-Draught (Side-Quest)":
        player, mini_log, next_state = mini_games.init_recipe_minigame(player)
        intro = (
            "The Apothecary looks up from a bubbling copper cauldron, bags under their eyes.\n"
            "\"My apprentice is home in bed with the flu, and compounding a batch of **Sovereign Fever-Draught** requires two pairs of hands!\"\n"
            "\"I'll work the bellows and mortar—you measure out the four reagents in the exact order and exact dram quantities on the recipe scroll!\"\n\n"
        )
        return player, intro + mini_log, next_state

    if choice == "Browse Medicines and Remedies":
        player["apothecary_state"] = "shopping"
        return player, "\"Everything here for sale has been concocted by my hand and expertise. I vouch for each and every one of them! What do you need?\"", "NPC_DIALOGUE"

    if choice.startswith("Buy "):
        discount = max(0, player.get("charisma", 0) - 10)
        raw_name = choice[4:].split(" (")[0].lower()
        if raw_name in db.item_database:
            final_price = max(1, db.item_database[raw_name]["price"] - discount)
            item_w = db.item_database[raw_name].get("weight", 0.5)
            if get_inventory_weight(player) + item_w > get_max_carry_weight(player) + 15.0:
                return player, "\"You're already carrying too much weight! Lighten your pack first.\"", "NPC_DIALOGUE"
            if player["silver"] >= final_price:
                player["silver"] -= final_price
                player["inventory"].append(raw_name)
                return player, (
                    f"You hand over {final_price} silver and take the {format_item_name(raw_name)}.\n"
                    f"*** Bought {format_item_name(raw_name)}! (Remaining Silver: {player['silver']}s) ***"
                ), "NPC_DIALOGUE"
            return player, f"\"You need {final_price} silver for that, and you only have {player['silver']}s!\"", "NPC_DIALOGUE"

    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# THE COMMISSARY (HIGH STREET OUTFITTER & GENERAL PROVISIONER)
# -------------------------------------------------------------------------
COMMISSARY_STOCK = [
    ("tent", 15, "Wilderness Camp"),
    ("rope", 20, "Climbing Gear"),
    ("leather", 12, "Crafting Material"),
    ("empty flask", 10, "Holds 2 Drinks"),
    ("saddlebag", 25, "+15 lbs Max Carry"),
    ("silk ribbon", 8, "Gift (+1 Rep)"),
    ("silver pocket charm", 20, "Fine Gift (+2 Rep)"),
    ("vintage brumaire wine", 22, "Fine Gift / Drink"),
]

def get_commissar_options(player):
    if player.get("commissar_state") == "shopping":
        discount = max(0, player.get("charisma", 0) - 10)
        opts = []
        for item_key, base_cost, stat_tag in COMMISSARY_STOCK:
            cost = max(1, base_cost - discount)
            opts.append(f"Buy {format_item_name(item_key)} ({cost}s | {stat_tag})")
        opts.append("< Back")
        return opts

    return [
        "Browse Outfitting, Tents & Sundries",
        "Leave"
    ]


def resolve_commissar(choice, player):
    if choice == "Leave":
        player["commissar_state"] = None
        return player, "You step out of the quiet Commissary.", "MAIN"

    if choice == "< Back":
        player["commissar_state"] = None
        return player, "The shopkeeper sets down their needle and waits patiently.", "NPC_DIALOGUE"

    if choice == "Browse Outfitting, Tents & Sundries":
        player["commissar_state"] = "shopping"
        return player, "\"Canvas tents, strong hemp rope, stitched leather saddlebags, and fine gifts from the back room. What do you require?\"", "NPC_DIALOGUE"

    if choice.startswith("Buy "):
        discount = max(0, player.get("charisma", 0) - 10)
        raw_name = choice[4:].split(" (")[0].lower()
        if raw_name in db.item_database:
            final_price = max(1, db.item_database[raw_name]["price"] - discount)
            item_w = db.item_database[raw_name].get("weight", 1.0)
            if get_inventory_weight(player) + item_w > get_max_carry_weight(player) + 15.0:
                return player, "\"Your pack is already groaning under the weight! Stash or drop something first.\"", "NPC_DIALOGUE"
            if player["silver"] >= final_price:
                player["silver"] -= final_price
                player["inventory"].append(raw_name)
                return player, (
                    f"You pay {final_price} silver and pack away the {format_item_name(raw_name)}.\n"
                    f"*** Bought {format_item_name(raw_name)}! (Remaining Silver: {player['silver']}s) ***"
                ), "NPC_DIALOGUE"
            return player, f"\"That costs {final_price} silver, and you only have {player['silver']}s.\"", "NPC_DIALOGUE"

    return player, "Error", "MAIN"


# -------------------------------------------------------------------------
# OLD PENNYWEIGHT THE PAWNBROKER (BUY & SELL)
# -------------------------------------------------------------------------
PAWN_SHOP_STOCK = [
    "murum town map",
    "dtessera terra world map",
    "crude brass scope",
    "surveyor's spyglass",
    "masterworkelliott monocular scope",
    "grappling hook",
    "wooden club",
]

def get_pawnbroker_options(player):
    state = player.get("pawnbroker_state")
    discount = max(0, player.get("charisma", 0) - 10)

    if state == "buy":
        opts = []
        for item in PAWN_SHOP_STOCK:
            if item in db.item_database:
                price = max(1, db.item_database[item]["price"] - discount)
                opts.append(f"Buy {format_item_name(item)} ({price}s)")
        opts.append("< Back")
        return opts

    if state == "sell":
        opts = []
        for item in sorted(set(player["inventory"])):
            price = db.item_database.get(item, {}).get("price", 0)
            if price > 0 and item not in ["horse", "dtessera terra world map", "murum town map"]:
                sell_val = max(1, price // 3)
                cnt = player["inventory"].count(item)
                qty_str = f" [x{cnt}]" if cnt > 1 else ""
                opts.append(f"Sell {format_item_name(item)}{qty_str} (+{sell_val}s)")
        if not opts:
            opts.append("No Salable Goods in Pack")
        opts.append("< Back")
        return opts

    return [
        "Sell Surplus Gear (Pawn Items)",
        "Browse Curiosities, Scopes & Maps",
        "Ask about Scopes & Maps",
        "Leave"
    ]


def resolve_pawnbroker(choice, player):
    if choice == "Leave":
        player["pawnbroker_state"] = None
        return player, "Old Pennyweight adjusts his brass eyeglass. \"Everything has a price, friend. Come back when your pockets are heavy—or empty!\"", "MAIN"

    if choice in ["< Back", "No Salable Goods in Pack"]:
        player["pawnbroker_state"] = None
        return player, "Old Pennyweight taps his brass scales. \"What else can I do for you?\"", "NPC_DIALOGUE"

    if choice == "Sell Surplus Gear (Pawn Items)":
        player["pawnbroker_state"] = "sell"
        return player, "\"Let's see what you've dragged in. I pay half the market value in good silver coin on the spot.\"", "NPC_DIALOGUE"

    if choice == "Browse Curiosities, Scopes & Maps":
        player["pawnbroker_state"] = "buy"
        return player, "\"Unredeemed pledges, optical scopes from Parvus, and regional survey maps! Take your pick.\"", "NPC_DIALOGUE"

    if choice == "Ask about Scopes & Maps":
        log = (
            "Old Pennyweight polishes a brass lens with his sleeve.\n"
            "\"By the naked eye, you can only scout one square ahead when you switch your D-Pad to LOOK mode.\"\n"
            "\"Carry one of my optical scopes in your pack, and you can click the same compass direction repeatedly to peer 2, 3, or even 5 squares across the horizon!\""
        )
        return player, log, "NPC_DIALOGUE"

    if choice.startswith("Sell "):
        raw_name = choice[5:].split(" (+")[0].split(" [x")[0].lower()
        if raw_name in player["inventory"]:
            player, msg = sell_item_helper(player, raw_name)
            return player, msg, "NPC_DIALOGUE"
        return player, "\"You don't seem to have that item anymore.\"", "NPC_DIALOGUE"

    if choice.startswith("Buy "):
        discount = max(0, player.get("charisma", 0) - 10)
        raw_name = choice[4:].split(" (")[0].lower()
        if raw_name in db.item_database:
            final_price = max(1, db.item_database[raw_name]["price"] - discount)
            item_w = db.item_database[raw_name].get("weight", 0.2)
            if get_inventory_weight(player) + item_w > get_max_carry_weight(player) + 15.0:
                return player, "\"Your pack is already groaning at the seams! Sell or stash something first.\"", "NPC_DIALOGUE"
            if player["silver"] >= final_price:
                player["silver"] -= final_price
                player["inventory"].append(raw_name)
                return player, (
                    f"You pay {final_price} silver to Old Pennyweight and pack away the {format_item_name(raw_name)}.\n"
                    f"*** Bought {format_item_name(raw_name)}! (Remaining Silver: {player['silver']}s) ***"
                ), "NPC_DIALOGUE"
            return player, f"\"That costs {final_price} silver, and you only have {player['silver']}s.\"", "NPC_DIALOGUE"

    return player, "Error.", "MAIN"


# -------------------------------------------------------------------------
# MODULE REGISTRATION
# -------------------------------------------------------------------------
HANDLERS = {
    "armourer":   (get_armourer_options, resolve_armourer),
    "apothecary": (get_apothecary_options, resolve_apothecary),
    "commissar":  (get_commissar_options, resolve_commissar),
    "pawnbroker": (get_pawnbroker_options, resolve_pawnbroker),
}
