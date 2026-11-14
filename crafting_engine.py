# =========================================================================
# EXOTIC WEAPONS, DEFENCE ITEMS & FORGING RECIPES DATABASE
# =========================================================================
EXOTIC_GEAR_DATABASE = {
    # Weapons
    "macuahuitl": {"price": 45, "weight": 3.5, "slot": "weapon", "damage": 8, "description": "A broad wooden club edged with razor-sharp obsidian blades; inflicts severe bleeding."},
    "greek fire flask": {"price": 55, "weight": 2.0, "slot": "consumable", "damage": 15, "description": "An alchemical siphon-pot of volatile naphtha that bursts into inextinguishable fire."},
    "urumi": {"price": 60, "weight": 2.0, "slot": "weapon", "damage": 7, "description": "A flexible steel whip-blade that coils around enemy parries and shields."},
    "kpinga": {"price": 35, "weight": 1.5, "slot": "weapon", "damage": 6, "description": "A multi-bladed throwing iron designed for spinning, multi-target lethality."},
    "chakram": {"price": 40, "weight": 1.0, "slot": "weapon", "damage": 6, "description": "A razor-edged steel throwing ring that slices through unarmored targets."},
    "crossbow": {"price": 50, "weight": 5.0, "slot": "weapon", "damage": 10, "description": "A heavy mechanical arbalest that punches straight through iron plate armor."},
    "knuckle duster": {"price": 15, "weight": 0.8, "slot": "weapon", "damage": 5, "description": "Reinforced bronze finger-guards for silent, brutal street fisticuffs."},

    # Defence & Armour
    "gambeson": {"price": 25, "weight": 4.0, "slot": "torso", "defense": 3, "description": "Quilted linen-and-wool padded jacket offering reliable blunt and slashing protection."},
    "leather jerkin": {"price": 20, "weight": 3.0, "slot": "torso", "defense": 2, "description": "Boiled leather chest protection favoured by scouts and outriders."},
    "helmet": {"price": 30, "weight": 3.5, "slot": "head", "defense": 3, "description": "A steel nasal helm that deflects glancing blows and head-strikes."},
    "horse armour": {"price": 90, "weight": 25.0, "slot": "horse", "defense": 6, "description": "Reinforced leather and segmented iron barding that shields your warhorse from harm."},
    "dragon shaffron": {"price": 150, "weight": 8.0, "slot": "horse", "defense": 10, "description": "A legendary Caligo star-iron horse head-plate that strikes terror into enemy mounts."},
}

# Forging recipes (Material 1, Material 2 -> Result Item)
FORGING_RECIPES = {
    ("iron ingot", "obsidian shard"): "macuahuitl",
    ("iron ingot", "iron ingot"): "crossbow",
    ("steel longsword", "leather straps"): "gambeson",
    ("iron ingot", "leather"): "leather jerkin",
    ("iron ingot", "iron ingot"): "helmet",
    ("iron ingot", "steel longsword"): "knuckle duster",
    ("star-iron ingot", "iron ingot"): "dragon shaffron",
}
