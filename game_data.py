import math

# Weapon Database
weapon_max_hit = {
    "fists": 2,
    "wooden club": 4,
    "iron dagger": 5,
    "iron sword": 8,
    "steel longsword": 10,
    "masterwork steel longsword": 15
}

# Shield Defense Database (Damage Reduction per enemy strike)
shield_defense = {
    "none": 0,
    "shield": 1,
    "heavy shield": 3
}

# Item Database
item_database = {
    "ancient castellan signet": {
        "price": 45,
        "weight": 0.2,
        "gift": True,
        "description": "A heavy gold signet ring recovered from the sunken lake strongbox, engraved with the ancient crest of the Castellans."
    },
    "ancient sapper's blueprint": {
        "price": 45, "weight": 0.3,
        "description": "An oiled vellum scroll detailing the hidden counter-mine tunnels and masonry weak-points along the Old Path and frontier keeps."
    },
    "ancient castellan signet": {
        "price": 45,
        "weight": 0.1,
        "description": (
            "A heavy gold-and-garnet signet ring recovered from the sunken "
            "belfry of Calluna Lake, bearing the crest of the First Castellan."
        ),
    },
    "apothecary's parcel": {
        "price": 0,
        "description": "A carefully wrapped medical parcel addressed to the Apothecary, containing rare Moon-Blight Extract.",
        "weight": 1.0
    },
    "apple": {
        "price": 3,
        "hunger_restore": 20,
        "shelf_life": 2000,
        "consume_desc": "You eat the crisp apple.",
        "horse_food": True,
        "description": "A fresh, crisp apple that will sate a small amount of hunger.",
        "weight": 0.5
    },
    "armadillo carapace polish": {
        "price": 10,
        "weight": 0.5,
        "gift": True,
        "description": "A tin of beeswax and pine resin used by Snail caravanners to oil the plates of their giant hairy armadillos."
    },
    "bandoka's cipher": {
        "price": 30,
        "weight": 0.2,
        "description": "A coded intelligence dispatch confiscated from Bandoka the Double Agent, bearing the private wax seal of rival conspirators."
    },
    "birthing tonic": {
        "price": 10,
        "description": "A soothing herbal concoction designed to ease the pains and panic of labor.",
        "weight": 0.5
    },
    "blacksmith's horse report": {
        "price": 0,
        "description": "A soot-stained response from Lovejoy detailing the new steel shoes forged for the Mayor's stallion.",
        "weight": 0.2
    },
    "bottle of ink": {
        "price": 6, "weight": 0.3,
        "description": "A stoneware inkpot of dark iron-gall and printer's lampblack ink."
    },
    "box of candied violets": {
        "price": 12,
        "weight": 0.5,
        "gift": True,
        "description": "A ribbon-tied confectionery box of sugar-dusted violets. A coveted gift among refined townsfolk."
    },
    "brass microscope": {
        "price": 45, "weight": 1.2, "usable": True,
        "description": "A compound brass field-microscope (20x magnification). Uncovers microscopic forensic evidence on surfaces and documents."
    },
    "bucket of hot water": {
        "price": 0,
        "description": "A wooden bucket sloshing with steaming hot water.",
        "weight": 8.0
    },
    "bucket of sand": {
        "price": 0,
        "description": "A heavy wooden bucket filled with dense, dry sand. Perfect for smothering fires.",
        "weight": 9.0
    },
    "bundle of halberds": {
        "price": 0,
        "description": "A dozen heavy polearms bound tightly with thick rope.",
        "weight": 12.0
    },
    "bundle of radical pamphlets": {
        "price": 0,
        "description": "An oilskin-wrapped bundle of banned anarchist treatises by P.J. Proudhon. Highly illegal in Murum.",
        "weight": 0.2
    },
    "butter": {
        "price": 10,
        "shelf_life": 2000,
        "description": "A block of rich, yellow butter wrapped in parchment.",
        "weight": 1.0
    },
    "caligo mountains map": {
        "price": 15,
        "description": "A topographical map of the Caligo Mountain Range and its hidden mountain lake.",
        "weight": 0.2
    },
    "career ledger": {
        "price": 10, "weight": 0.2,
        "description": "A leather-bound pocket dossier whose 10 lines record the exact stat, skill, and faction requirements for every Chapter 2 career path."
    },
    "carrot": {
        "price": 2,
        "hunger_restore": 15,
        "shelf_life": 2000,
        "consume_desc": "You eat the fresh carrot.",
        "horse_food": True,
        "description": "Fresh and locally grown Murum carrots, purple through to the core and bound to take the edge off your hunger.",
        "weight": 0.5
    },
    "carved yew wayfinder": {
        "price": 18,
        "weight": 0.2,
        "description": (
            "A notched yew sun-ring carved by the Wilderness Vanguardists. "
            "Prevents disorientation in Lignum Forest just like a Brass Compass."
        ),
    },
    "castle key mould": {
        "price": 0,
        "description": "A heavy clay mould bearing the negative impression of a complex castle key.",
        "weight": 2.0
    },
    "charcoal bitters": {
        "price": 12,
        "weight": 0.5,
        "cures_affliction": "food_poisoning",
        "consume_desc": "You drink the gritty willow-charcoal and gentian root mixture.",
        "description": "An apothecary's stomach purge that neutralises Food Poisoning and internal toxins, halting health loss."
    },
    "clean straw": {
        "price": 0,
        "description": "A fresh bundle of clean straw for bedding.",
        "weight": 4.0
    },
    "cobnuts": {
        "price": 1,
        "horse_food": True,
        "description": "A handful of fresh, earthy cobnuts. A favourite treat for horses.",
        "weight": 0.3
    }, 
    "codewheel": {
        "price": 25, "weight": 0.4,
        "description": "A concentric two-ring brass Alberti cipher disk for rotating and decoding shifted intelligence dispatches."
    },
    "compass": {
        "price": 0,
        "weight": 0.5,
        "description": "A heavy brass pocket compass taken from the New Road highwaymen. Its steady magnetic needle keeps you from losing your bearings beneath the dark canopy of Lignum Forest."
    },
    "contraband silk cache": {
        "price": 0,
        "description": "An oilskin-wrapped parcel of unstamped luxury silk, sealed with a hair-fine Wallmakers' wax thread.",
        "weight": 0.2
    },
    "copy of the key to ragmore castle": {
        "price": 0,
        "description": "A freshly forged, heavy iron key designed to unlock the gates of Ragmore Castle.",
        "weight": 0.5
    },
    "coryllus (haltered)": {
        "price": 0,
        "description": "Coryllus, the temperamental stallion, safely secured by a halter.",
        "weight": 0.0
    },
    "crate of horseshoes": {
        "price": 0,
        "description": "An incredibly heavy wooden crate packed with iron horseshoes.",
        "weight": 14.0
    },
    "crown of the first castellan": {
        "price": 75, "weight": 1.5,
        "description": "An ancient circlet of tarnished silver and jet recovered from the drowned crypt of Calluna, conferring undeniable feudal authority."
    },
    "crude brass scope": {
        "price": 25,
        "weight": 1.0,
        "scope_range": 2,
        "description": "A dented brass tube with pinched glass lenses. Allows you to peer up to 2 squares away."
    },
    "cucumber": {
        "price": 2,
        "hunger_restore": 15,
        "shelf_life": 2000,
        "consume_desc": "You eat the fresh cucumber.",
        "description": "It may only be a cucumber but the size of a baby's arm these will take the edge off of your hunger.",
        "weight": 0.5
    },
    "custom breastplate": {
        "price": 0,
        "description": "A massive, thick steel breastplate commissioned by the Armourer.",
        "weight": 10.0
    },
    "deck of cards": {
        "price": 8, "weight": 0.2,
        "description": "A 54-card pack (52 suited cards plus two distinct Jokers) used for tavern games and the Cryptonomicon 'Pontifex' keystream cipher."
    },
    "dtessera terra world map": {
        "price": 100,
        "description": "A grand, comprehensive map of the entire known world of Dtessera Terra.",
        "weight": 0.2
    },
    "empty flask": {
        "price": 10,
        "description": "A leather waterskin. It is currently empty.",
        "weight": 0.4
    },
    "fed and watered stallion": {
        "price": 0,
        "description": "The stallion is fully rested, fed, and watered.",
        "weight": 0.0
    },
    "fish jerky": {
        "price": 6,
        "hunger_restore": 50,
        "consume_desc": "You eat the hearty fish jerky.",
        "description": "A curious delicacy of Murum Town. The smell is strong but it will sate a significant amount of your hunger.",
        "weight": 0.8
    },
    "flu medicine": {
        "price": 15,
        "weight": 0.5,
        "cures_affliction": "damp_chill",
        "consume_desc": "You swallow the bitter, warming draught of elderberry and camphor.",
        "description": "A glass vial of foul-smelling tonic that cures the Brumaire Damp-Chill (Flu) and stops feverish health loss."
    },
    "fluvius town map": {
        "price": 10,
        "description": "A map showing Fluvius Town, the surrounding farmlands, and the local lake.",
        "weight": 0.2
    },
    "foaling manual": {
        "price": 0,
        "description": "A heavily stained and worn book on equine birth.",
        "weight": 1.5
    },
    "full water flask": {
        "price": 0,
        "thirst_restore": 50,
        "transforms_into": "half-full water flask",
        "consume_desc": "You drink half your flask.",
        "description": "A leather waterskin, sloshing with fresh water.",
        "weight": 2.0
    },
    "giant hairy armadillo": {
        "price": 120,
        "weight": 0.0,
        "description": "A massive, shaggy-plated giant hairy armadillo fitted with a high brass-rimmed snail-howdah. Slow to anger, impervious to thorns, and unstoppable across rough terrain."
    },
    "grappling hook": {
        "price": 25,
        "description": "An iron hook for grappling.",
        "equippable": True,
        "weight": 3.0
    },
    "guard uniform": {
        "price": 45, "weight": 4.0,
        "description": "A complete blue-and-brass Town Watch tabard and cloak that lets you walk past standard guard checkpoints."
    },
    "half-full water flask": {
        "price": 0,
        "thirst_restore": 50,
        "transforms_into": "empty flask",
        "consume_desc": "You finish off your flask.",
        "description": "A leather waterskin, carrying one more drink of water.",
        "weight": 1.2
    },
    "halter": {
        "price": 5,
        "description": "A sturdy leather and rope halter used to lead a horse.",
        "weight": 1.0
    },
    "heavy shield": {
        "price": 30,
        "description": "A thick, iron-banded wooden shield. Very sturdy.",
        "equippable": True,
        "weight": 8.0
    },
    "heavy winter blanket": {
        "price": 16, "weight": 2.0,
        "description": "A double-woven wool blanket large enough to wrap both yourself and your horse's loins when camping or riding in freezing weather."
    },
    "hidden secret ledger": {
        "price": 0,
        "description": "A pristine ledger hidden by Lightfoot, detailing the Wallmakers' massive unpaid debts and extortion.",
        "weight": 0.2
    },
    "horse": {
        "price": 50,
        "description": "A strong, fast steed that significantly cuts down travel time.",
        "weight": 0.0
    },
    "ice crampons": {
        "price": 20, "weight": 1.0,
        "description": "Forged iron heel-spikes that strap to your boots, preventing slips and stamina loss on icy roads and Caligo mountain crags."
    },
    "iron dagger": {
        "price": 15,
        "equippable": True,
        "description": "A compact, well-balanced iron utility knife forged by Lovejoy.",
        "weight": 2.0
    },
    "iron screw-spindle": {
        "price": 25, "weight": 3.0,
        "description": "A forged iron platen screw and devil's-tail lever for a printing press (Part 2/3)."
    },
    "iron sword": {
        "price": 30,
        "description": "A standard, dependable iron sword forged by Lovejoy.",
        "equippable": True,
        "weight": 5.0
    },
    "kokeshi doll": {
        "price": 35, "weight": 0.5,
        "description": "A lathe-turned wooden doll bearing the secret lathe-rings of the Kokeshi Syndicate—grants instant recognition in underworld dens."
    },
    "lead type-case": {
        "price": 20, "weight": 2.5,
        "description": "Acompartmentalised wooden drawer of cast lead-antimony letter-blocks and spacers (Part 3/3)."
    },
    "leather": {
        "price": 12,
        "description": "A thick, durable hide of leather. Useful for crafting.",
        "weight": 3.0
    },
    "lignum forest map": {
        "price": 15,
        "description": "A map charting the dense, sprawling Lignum Forest.",
        "weight": 0.2
    },
    "looking glass": {
        "price": 30, "weight": 0.5, "usable": True,
        "description": "A collapsible three-draw brass spyglass. Reveals distant or high-elevation hidden hotspots during investigations."
    },
    "market lockbox": {
        "price": 0,
        "description": "Godwin's heavy iron lockbox, filled with the week's merchant stall rents.",
        "weight": 0.2
    },
    "masonry drill": {
        "price": 0,
        "description": "A fully assembled, silent masonry drill. It feels heavy and highly illegal.",
        "weight": 10.0
    },
    "masterworkelliott monocular scope": {
        "price": 110,
        "weight": 1.0,
        "scope_range": 5,
        "description": "A crystal-clear optical scope of remarkable magnification. Allows you to peer up to 5 squares away."
    },
    "masterwork steel longsword": {
        "price": 150,
        "description": "A flawlessly tempered steel longsword forged by your own hands under Lovejoy's tutelage. A true masterpiece.",
        "equippable": True,
        "weight": 4.5
    },
    "mayor's birthday cake": {
        "price": 0,
        "description": "A beautifully baked sponge cake with thick icing.",
        "weight": 3.0
    },
    "mayor's dinner letter": {
        "price": 0,
        "description": "A quick note from the Mayor instructing Praisegod on what to prepare for the evening meal.",
        "weight": 0.2
    },
    "mayor's horse letter": {
        "price": 0,
        "description": "An official letter from the Mayor to Lovejoy regarding new shoes for their prized stallion.",
        "weight": 0.2
    },
    "mayor's incoming post": {
        "price": 0,
        "description": "A heavy, wax-sealed stack of incoming dispatches addressed to the Mayor.",
        "weight": 0.2
    },
    "mayor's outgoing letters": {
        "price": 0,
        "description": "A stack of official correspondence from the Mayor's residence to be deposited at the Post Office.",
        "weight": 0.2
    },
    "mayor's seal": {
        "price": 0,
        "description": "A heavy gold signet ring bearing the Mayor's crest.",
        "weight": 0.2
    },
    "mayor's shod stallion": {
        "price": 0,
        "description": "The stallion, now wearing freshly forged steel shoes.",
        "weight": 0.0
    },
    "mayor's stallion": {
        "price": 0,
        "description": "A massive, powerful stallion belonging to the Mayor.",
        "weight": 0.0
    },
    "meat ration": {
        "price": 6,
        "hunger_restore": 50,
        "consume_desc": "You eat the hearty meat ration.",
        "description": "A cured cut of meat that will sate a significant amount of hunger.",
        "weight": 1.0
    },
    "misdelivered town hall letter": {
        "price": 0,
        "weight": 0.2,
        "description": "A thick parchment envelope addressed to the Murum Town Hall Surveyor's Office, accidentally left sticking out of the Postbox by Fleetfoot. You can feel a folded map inside!"
    },
    "mouflin": {
        "price": 80,
        "weight": 0.0,
        "description": "A sure-footed Caligo mountain sheep with massive spiral horns. Can be ridden across steep Mountain crags without needing to climb!"
    },
    "muddy master key": {
        "price": 0,
        "description": "A heavy iron master key fished out of the market fountain drain. It unlocks every merchant lockbox in Murum Market.",
        "weight": 0.2
    },
    "murum town map": {
        "price": 10,
        "description": "A parchment map detailing Murum Town and its towering walls.",
        "weight": 0.2
    },
    "oak press-frame": {
        "price": 20, "weight": 4.0,
        "description": "The heavy mortised oak bed and tympan frame of a flatbed printing press (Part 1/3)."
    },
    "package of drill parts": {
        "price": 0,
        "description": "A heavy parcel containing highly specialized gears and diamond-tipped bits.",
        "weight": 7.0
    },
    "parvus town map": {
        "price": 10,
        "description": "A small map showing the coastal town of Parvus.",
        "weight": 0.2
    },
    "pear": {
        "price": 3,
        "hunger_restore": 20,
        "shelf_life": 2000,
        "consume_desc": "You eat the crisp pear.",
        "description": "A juicy conference pear that will sate a small amount of hunger.",
        "weight": 0.5
    },
    "pen and quill": {
        "price": 5, "weight": 0.1,
        "description": "A trimmed goose-quill and brass nib-holder for drafting dispatches and forgeries."
    },
    "portable printing press": {
        "price": 65, "weight": 8.0,
        "description": "A compact oak-and-iron flatbed screw press with a tray of movable lead type."
    },
    "poster": {
        "price": 0,
        "description": "A promotional flyer handed out by Fairlight outside the Murum Playhouse.",
        "weight": 0.2
    },
    "postie's route sheet": {
        "price": 0,
        "description": "A copy of the Post Office's daily delivery loop around Murum Town.",
        "weight": 0.2
    },
    "printed pamphlet": {
        "price": 5, "weight": 0.1,
        "description": "A freshly inked broadsheet printed on your flatbed press, ready to distribute in the streets."
    },
    "red-and-gold strike banner": {
        "price": 40,
        "weight": 1.0,
        "description": "A heavy silk banner embroidered with the clasped hands of the Agrarian Union. Awarded for turning all three wavering farm delegations into fire-breathing unionists."
    },
    "reference letter": {
        "price": 0,
        "description": "A formal letter of reference written by Headteacher Dr. Makepeace.",
        "weight": 0.2
    },
    "rope": {
        "price": 20,
        "description": "A thick rope, strong enough to climb.",
        "weight": 3.0
    },
    "sack of coal": {
        "price": 10,
        "description": "A heavy hessian sack filled with black forge coal to ward off the damp Brumaire chill.",
        "weight": 10.0
    },
    "sack of oats": {
        "price": 5,
        "description": "A heavy sack of premium oats, perfect for feeding working draught horses.",
        "weight": 5.0
    },
    "saddlebag": {
        "price": 25,
        "weight": 0.0,
        "carry_bonus": 15.0,
        "description": "Sturdy stitched leather packs that increase your carrying capacity by 15 lbs."
    },
    "sage's charter": {
        "price": 0,
        "weight": 0.2,
        "description": "A parchment scroll signed and sealed by Master Spotted Tail, Sage of the Caligo Mountains. Commands deep respect in diplomatic and faction disputes."
    },
    "sappers' master-key": {
        "price": 30, "weight": 0.5,
        "description": "A heavy brass skeleton key and valve-wrench stamped with the mark of the Parvus subterranean engineers."
    },
    "sheets of paper": {
        "price": 4, "weight": 0.2,
        "description": "A quire of rag-linen paper suitable for correspondence or flatbed printing."
    },
    "shield": {
        "price": 10,
        "description": "A standard wooden shield.",
        "equippable": True,
        "weight": 5.0
    },
    "silk ribbon": {
        "price": 8,
        "weight": 0.1,
        "gift": True,
        "description": "A bolt of crimson Fluvius silk ribbon. Popular as a thoughtful token of appreciation."
    },
    "silver pocket charm": {
        "price": 20,
        "weight": 0.2,
        "gift": True,
        "description": "A finely stamped silver token for good fortune. Makes an impressive gift."
    },
    "smudged receipt": {
        "price": 0,
        "description": "A payment receipt with ink smeared across the client's name.",
        "weight": 0.2
    },
    "skeleton key": {
        "price": 65, "weight": 0.1, "usable": True,
        "description": "A master-filed star-iron ward key. Silently unlocks any padlocked cache, grate, or door during a search without a roll."
    },
    "smugglers' cipher": {
        "price": 0,
        "description": "A flattened lead cylinder containing oiled vellum marked with mason's thieves' cant.",
        "weight": 0.2
    },
    "spiced cider": {
        "price": 5,
        "weight": 1.5,
        "thirst_restore": 60,
        "hunger_restore": 10,
        "consume_desc": "You drink the warming, cinnamon-spiced orchard cider.",
        "description": "A stoppered clay jug of pressed apple cider infused with cloves."
    },
    "spoiled food": {
        "price": 0,
        "weight": 0.5,
        "hunger_restore": 5,
        "causes_affliction": "food_poisoning",
        "consume_desc": "Stomach churning, you force down the rancid, mouldering food...",
        "description": "Rotting, foul-smelling produce. Eating this will almost certainly make you violently ill, though Shareall at the Vegetable Stall buys compost for 1s."
    },
    "spool of thread": {
        "price": 3, "weight": 0.1,
        "description": "Waxed linen cord and bone needles for knotting, netting, and mending winter garments."
    },
    "star-iron ingot": {
        "price": 60, "weight": 3.0,
        "description": "A dense, silvery-blue billet of meteoric mountain ore from the deep-delve mines of Caligo—prized above gold by master founders."
    },
    "steel longsword": {
        "price": 75,
        "description": "A beautifully balanced longsword made of gleaming steel.",
        "equippable": True,
        "weight": 5.0
    },
    "storm lantern": {
        "price": 18, "weight": 1.0,
        "description": "A brass whale-oil lantern with horn panes that cannot be blown out by Heavy Rain, Gales, or Blizzards."
    },
    "surveyor's spyglass": {
        "price": 55,
        "weight": 1.5,
        "scope_range": 3,
        "description": "A precision-ground telescopic lens used by Wall Surveyors. Allows you to peer up to 3 squares away."
    },
    "syndicate token": {
        "price": 0,
        "description": "A small wooden disc painted diagonally in red and black. The secret mark of the Free-Earth Syndicate.",
        "weight": 0.2
    },
    "tadhg's witness statement": {
        "price": 0,
        "weight": 0.1,
        "description": "A sworn statement from Tadhg the night eel-fisher, testifying that the three waterwheel saboteurs were clean-shaven Kokeshi agents—none had Farmer Flyfornication's long red beard."
    },
    "tent": {
        "price": 15,
        "description": "A sturdy canvas tent. Essential for sleeping safely in the wilderness.",
        "weight": 6.0
    },
    "topographic survey map": {
        "price": 35, "weight": 0.2, "usable": True,
        "description": "A Royal Cartographer's contour & hydrological chart of Dtessera Terra. Allows you to toggle the live Elevation & Flood-Stage Overlay [Press T or Use]."
    },
    "torch": {
        "price": 3, "weight": 0.5,
        "description": "A resin-soaked pine torch that illuminates the darkness for 300 decimal minutes (3 decimal hours) and wards off evening chill."
    },
    "torn ledger page": {
        "price": 0,
        "description": "A ripped page from the stable's accounting ledger.",
        "weight": 0.2
    },
    "vintage brumaire wine": {
        "price": 22,
        "weight": 2.5,
        "gift": True,
        "thirst_restore": 40,
        "consume_desc": "You uncork the rich vintage wine and drink deeply.",
        "description": "A dark glass bottle of cellared autumn wine. Prized by officials and guildmasters alike."
    },
    "wallmaker blueprint": {
        "price": 0,
        "description": "An intricate blueprint detailing a tool designed to bore silently into stone walls.",
        "weight": 0.2
    },
    "war manual": {
        "price": 15,
        "weight": 0.3,
        "description": (
            "A pocket-sized Tate-red linen booklet titled 'Articles of War & "
            "Campaign Standing Orders for Dtessera Terra'."
        ),
    },
    "warm winter coat": {
        "price": 28, "weight": 2.5,
        "description": "A thick sheepskin-lined wool greatcoat that insulates against freezing temperatures, snow, and hail."
    },
    "watered stallion": {
        "price": 0,
        "description": "The stallion is refreshed.",
        "weight": 0.0
    },
    "waxed jacket": {
        "price": 22, "weight": 1.5,
        "description": "A heavy linseed-oiledsailcloth coat that keeps you dry in Light, Heavy, and Torrential Rain."
    },
    "weighted ivory dice": {
        "price": 25,
        "weight": 1,
        "description": "A pair of shaved ivory bones weighted with quicksilver. Deadly at the Craps table—if the Pit Boss doesn't catch you."
    },
    "wheel of aged cheese": {
        "price": 8,
        "weight": 2.0,
        "hunger_restore": 60,
        "shelf_life": 4000,
        "consume_desc": "You cut a thick wedge of the sharp, crumbly aged cheese.",
        "description": "A rich wheel of aged Murum dairy cheese. Keeps well on long journeys."
    },
    "wooden club": {
        "price": 5,
        "description": "A heavy piece of carved wood. Better than using your fists.",
        "equippable": True,
        "weight": 4.0
    },
    "woodland drum": {
        "price": 20, "weight": 2.0,
        "description": "A resonant ash-wood frame drum; the animals of Lignum Forest love a rhythmic drum circle."
    },
    "wound salve": {
        "price": 14,
        "weight": 0.5,
        "cures_affliction": "wound_infection",
        "consume_desc": "You clean and dress your festering cuts with the stinging antiseptic salve.",
        "description": "A jar of boiled pine-pitch, alcohol, and yarrow that stops Wound Sepsis and blood poisoning."
    }
}

# Skills Database
skills_database = {
    "archery",
    "river navigation",
    "swim",
    "ride",
    "climb",
    "forge",
    "mayor's footman",
    "safe travel",
    "junior apprentice blacksmith",
    "apprentice blacksmith",
    "master blacksmith",
    "stable master",
    "radical theory",
    "market overseer",
    "master wallmaker",
    "intelligence officer",
    "union steward"
}

# Building Database
building_database = {
    "blacksmiths": {
        "location": (11, 14),
        "name": "The Blacksmiths",
        "description": "You enter the blacksmiths and are immediately pushed back by the intense heat of the furnace." +
        "\nYou can see the blacksmith punishing a piece of iron on the anvil." +
        "\nSix and a half feet tall, their sweat causing their long black hair to plaster across their glowing face." +
        "\nThey are wearing a full length heavy apron and wielding a heavy hammer." +
        "\nThey have a very intimidating presence."  
    },
    "apothecary": {
        "location": (10, 15),
        "name": "The Apothecary",
        "description": "You enter the apothecary and the bell above the door anounces your entry." +
        "\nYou see glass bottles on the shelves and herbs drying by hanging down from the rafters above." +
        "\nA person stands behind a wooden bench mixing different ingredients with a pestle and morter." +
        "\nThey look up as you enter."
    },
    "commissary": {
        "location": (10, 15),
        "name": "The Commissary",
        "description": "A dark narrow shop with little on the shelves or walls." +
        "\nA small person sits before a door that stands ajar. You can see boxes of stock in the back neatly stacked up on shelves." +
        "\nThe shopkeeper is quietly sewing and mending their eyes fixed on you as you walk toward them."
    },
    "armourer": {
        "location": (10, 15),
        "name": "The Armourer",
        "description": "The Armourer sits at the front of the shop polishing steel." +
        "\nTheir bench across the front door barring entry beyond the threshold." +
        "\nAll of their stock sits behind them and out of reach of anyone with sticky fingers."
    },
    "pawnbroker": {
        "location": (10, 15),
        "name": "Old Pennyweight's",
        "description": "A metal cage confronts you as you cross the threshold of the pawnbrokers." +
        "\nYou can see the wares through the mesh of the cage, the price labels unintelligible from the frequent re-pricing." +
        "\nOld Pennyweight sits staring at you with suspicion. His shop attacked too many times from people with a chip on their shoulder."
    },
    "house of games": {
        "location": (9, 13),
        "name": "The House of Games",
        "description": (
            "You step through heavy velvet curtains into The House of Games. Cigar smoke and the warm glow of oil chandeliers hang over green baize tables "
            "for Roulette, Blackjack, and Texas Hold'em.\n"
            "Along the panelled back wall stands a row of gleaming brass-and-mahogany Mechanical Arcade Cabinets where townsfolk compete for high scores."
        )
    },
    "dog and duck pub": {
        "location": (9, 16),
        "name": "The Dog and Duck Pub",
        "description": "The Dog and Duck Pub is as old on the inside as the walls suggest." +
        "\nA 16th-century stone fireplace draws you into its warm hearth and boasts of its ancient history." +
        "\nInscriptions and witch marks are scratched into the walls to ward off witches and protect against evil." +
        "\nA trade union banner takes up most of the wall opposite the bar." +
        "\nIt depicts a raised fist on a red background with a unfurled scroll that reads," +
        "\"Together Toward Socialism, Murum Town Branch\""
    },
    "guard house": {
        "location": (7, 14),
        "name": "Murum Guard House",
        "description": "The inside of the Guard House is much the same. Fresh hay has been scattered on the floor and an on duty guard sits at a well constructed home built desk."
    },
    "mayor's house": {
        "location": (9, 15),
        "name": "The Mayor's House",
        "parent": None,
        "description": "You are standing in the grand foyer of the Mayor's House. The floors are polished marble and the walls are adorned with expensive tapestries." +
        "\nThrough an arched doorway, you can hear the faint bustling of the kitchen and servants' quarters." +
        "\nThe Mayor's Butler stands at rigid attention near the grand staircase, maintaining strict decorum and ensuring no commoners track mud onto the rugs."  
    },
    "mayor's staff entrance": {
        "location": (9, 15),
        "name": "Mayor's House - Staff Entrance",
        "parent": None,
        "description": "The rear entrance to the Mayor's sprawling estate. The heat of the kitchen radiates from the open doorway, accompanied by the clatter of pots and pans." +
        "\nHouse Manager Praisegod oversees deliveries and household staff from a small standing desk near the pantry."
    },
    "post office": {
        "location": (8, 16),
        "name": "Murum Post Office",
        "description": "Postmaster Safehaven sits at an old wooden desk sorting through piles of sealed envelopes." +
        "\nEffortlessly and without error tossing them into small pigeon holes marking their destination." +
        "\nThe continual thwack of letters and missives being sorted fills the room."
    },
    "playhouse": {
        "location": (9, 14),
        "name": "Murum Playhouse",
        "description": "Inside Murum Playhouse you can see that the open yard in front of the stage is cobbled and provides standing room." +
        "\nFor a little more money attendees are allowed into the galleries where they can either stand or, for even more money, procure a stool." +
        "\nOne of the galleries is divided into small compartments to be used by the wealthy and aristocrats." +
        "\nThe playhouse is a timber building with a tile roof; although the patrons in the open yard remain uncovered and open to the elements."   
    },
    "school": {
        "location": (8, 14),
        "name": "The Headteacher's Office",
        "description": "A quiet, dusty office filled with towering bookshelves. Dr. Makepeace's heavy oak desk sits in the centre."
    },
    "stables": {
        "location": (7, 15),
        "name": "Murum Stables",
        "parent": None,
        "description": "Within the stables, it appears that you are alone among the many horses, most of whom pay you little to no attention. " +
        "However, there is one tall, strong horse toward the back of the stables that looks over at you and kicks their pen three times with their back leg. " +
        "Fifteen seconds later a young person enters. Long blonde hair, tangled and greasy fell over their shoulders. A pair of stained and well worn " +
        "dungarees marked them out as the stable manager. " +
        "At the far end of the stable, a heavy wooden door leads into the Tack Room. " +
        "Beside the horse stalls, a sturdy ladder ascends to the Hay Loft above."
    },
    "stable loft": {
        "location": (7, 15),
        "name": "The Stable Loft",
        "parent": "stables",
        "description": "A dusty, warm space above the stables filled with mounds of hay and straw. Dust motes dance in the light piercing through the roof slats."
    },
    "tack room": {
        "location": (7, 15),
        "name": "The Tack Room",
        "parent": "stables",
        "description": "The Head Hostler's personal workspace. It smells of polished leather, saddle soap, and stale ale. Bridles and saddles line the walls, and a cluttered desk sits in the corner."
    },
    "tavern": {
        "location": (10, 13), 
        "name": "Murum Tavern",
        "description": "Murum Tavern is a lively, rowdy pub filled with the smell of woodsmoke and stale ale." +
        "\nMany patrons stand around the bar talking loudly and animatedly, while others sit in the corners with conspiratorial glances around the bar." +
        "\nThe bartender looks at you curiously as they serve their customers."
    },
    "town hall": {
        "location": (10, 16),
        "name": "Murum Town Hall",
        "description": "Inside the Town Hall you observe that the ground floor is built with fine unblemished marble. " +
        "\nThe first floor is accessible via a large staircase of Tuscan style. But this is roped off and a sign reads, 'No Entrance to first floor.' " +
        "\nYou see an inscription explaining that the Municipality of Murum erected this building in the honor of the former mayor Alethea Workhard." +
        "\nFrom the main entrance you enter the lobby. On the left of the staircase, there is the bust of Alethea Workhard. You can see the Town Hall rooms arranged in rows." +
        "\nIn the lobby there are the portraits of all the previous Mayors. You can also see oil paintings of the Castellans of old. Front and centre of these is the present Castellan," +
        "\nLord Longsword. Beside this, somewhat innocuously, stands a noticeboard."
    },
    "union house": {
        "location": (11, 15),
        "name": "Union House",
        "description": "Inside Union House you start to understand the power of the union in Murum Town." +
        "\nThere are people moving with purpose all around you and you observe that the people here are not solely from the town itself." +
        "\nThere are farmers that work land outside of town, shepherds from the mountains, and herders from the grasslands." +
        "\nUnion House feels busy and cosmopolitan."
    },
    "wallmakers' offices": {
        "location": (10, 14),
        "name": "The Wallmakers' Office",
        "description": "Inside the Wallmakers' Offices you can begin to see how the guild operates." +
        "\nIt is a two-storey structure where the ground floor houses the main Wallmakers' administrative offices," +
        "\nalongside a public-facing enquiry area. Up the stairs ahead of you is off limits and is likely where" +
        "\nthe offices for senior members of staff are located, and perhaps some meetings rooms." +
        "\nThe Wallmakers are obviously well financed and all furnishings are plush and the building's upkeep is obviously well maintained."
    },
    "fluvius post office": {
        "location": (11, 3),
        "name": "Fluvius Post Office & Packet Wharf",
        "description": (
            "The smell of sealing wax, damp river-canvas, and pigeon-lofts fills the narrow timber office.\n"
            "Pigeonholes along the wall are stuffed with letters carried downstream from Murum Town by packet-skiff, "
            "and a wooden **Murum Dispatch Board** hangs beside the counter where locals read the latest news from the walled town."
        )
    },
    "barge and anchor": {
        "location": (11, 3),
        "name": "The Barge & Anchor Taproom",
        "description": (
            "Low-beamed rafters blackened by pipe-smoke hang over trestle tables scarred by boat-hooks.\n"
            "River-bargees, teamsters, and exhausted quarrymen from the Caligo foothills nurse tankards of dark quay porter by a peat fire."
        )
    },
    "counting house": {
        "location": (11, 4),
        "name": "Fluvius Counting House & Tribunal",
        "description": (
            "Polished oak panelling and tall brass-bound rent ledgers dominate the ground-floor counting room, "
            "while a wide staircase leads up to the gallery of the Fluvius Magistrate's Tribunal."
        )
    },
}



# --- BUILDING ALIASES ---
building_aliases = {
    "casino":               "house of games",
    "red wheel":            "house of games",
    "the red wheel":        "house of games",
    "the red wheel casino": "house of games",
    "arcade":               "house of games",
    "gaming house":         "house of games",
    "pub":                  "dog and duck pub",
    "dog and duck":         "dog and duck pub",
    "mayors house":         "mayor's house",
    "staff entrance":       "mayor's staff entrance",
    "kitchen":              "mayor's staff entrance",
    "staff":                "mayor's staff entrance",
    "servants entrance":    "mayor's staff entrance",
    "servants' entrance":   "mayor's staff entrance",
    "back door":            "mayor's staff entrance",
    "theatre":              "playhouse",
    "hall":                 "town hall",
    "headteacher's office": "school",
    "office":               "school",
    "hay loft":             "stable loft",
    "hayloft":              "stable loft",
    "loft":                 "stable loft",
    "stable loft":          "stable loft",
    "tack room":            "tack room",
    "tack":                 "tack room",
    "hostler's room":       "tack room",
    "murum tavern":         "tavern",
    "wallmakers":           "wallmakers' offices",
    "wallmakers offices":   "wallmakers' offices",
    "wall makers":          "wallmakers' offices",
    "wall makers offices":  "wallmakers' offices",
    "wall makers' offices": "wallmakers' offices",
    "wallmakers' office":   "wallmakers' offices",
    "wallmakers office":    "wallmakers' offices",
    "fluvius post office":  "fluvius post office",
    "packet wharf":         "fluvius post office",
    "barge and anchor":     "barge and anchor",
    "taproom":              "barge and anchor",
    "quay taproom":         "barge and anchor",
    "counting house":       "counting house",
    "tribunal":             "counting house",
    "tribunal hall":        "counting house",
}

# NPC Database
npc_database = {
    "absenceofsin": {
        "location": (12, 2),
        "proper_name": "Printer Absenceofsin (Fluvius Broadsheets)"
    },
    "aelfgifu": {
        "location": (7, 16),
        "proper_name": "Aelfgifu the Town Guard"
    },
    "aelfwine": {
        "location": (9, 3),
        "proper_name": "Constable Ælfwine (Fluvius Watch)"
    },
    "aethelstan": {
        "location": (3, 22),
        "proper_name": "Huntsman Æthelstan (Master of Hounds)"
    },
    "aldred_foundry": {
        "location": (18, 21),
        "proper_name": "Foundryman Aldred (Parvus Dry-Dock)"
    },
    "apothecary": {
        "location": "apothecary",
        "proper_name": "The Apothecary"
    },
    "armourer": {
        "location": "armourer",
        "proper_name": "The Armourer"
    },
    "bandoka": {
        "location": [(6, 17), (5, 17)],
        "proper_name": "Bandoka the Fellow Traveller"
    },
    "beornraed": {
        "location": (6, 21),
        "proper_name": "Lieutenant Beornraed (Watch Warden)"
    },
    "black_dog": {
        "location": (10, 22),
        "proper_name": "Black Dog (Outlaw Lieutenant)"
    },
    "black hills": {
        "location": (19, 19),
        "proper_name": "Black Hills (Vanguard Elder)"
    },
    "blacksmith": {
        "location": "blacksmiths",
        "proper_name": "Lovejoy the Blacksmith"
    },
    "bran_outrider": {
        "location": (7, 15),
        "proper_name": "Outrider Bran (Crooked Post-Rider)"
    },
    "breakchains": {
        "location": None,
        "proper_name": "Breakchains, Syndicate Organizer"
    },
    "buildhope": {
        "location": (18, 22),
        "proper_name": "Guildmaster Buildhope"
    },
    "butcher": {
        "location": (8, 15),
        "proper_name": "The Butcher"
    },
    "cenric": {
        "location": (6, 21),
        "proper_name": "Quartermaster Cenric (Frontier Watchpost)"
    },
    "ceolwulf": {
        "location": (5, 22),
        "proper_name": "Herdsman Ceolwulf (Ragmore Pastures)"
    },
    "chandler": {
        "location": (8, 15),
        "proper_name": "The Corn Chandler"
    },
    "corban": {
        "location": (12, 4),
        "proper_name": "Corban (Kokeshi Wagon-Boss)"
    },
    "coryllus": {
        "location": None,
        "proper_name": "Coryllus the Spooked Steed"
    },
    "commissar": {
        "location": "commissary",
        "proper_name": "The Commissary"
    },
    "croupier": {
        "location": "house of games",
        "proper_name": "Croupier Fortunesmile"
    },
    "dairy stall merchant": {
        "location": (8, 15),
        "proper_name": "The Dairy Stall Merchant"
    },
    "diarmuid": {
        "location": (11, 3),
        "proper_name": "Diarmuid the Quay Tap-Boy"
    },
    "diewell": {
        "location": (3, 12),
        "proper_name": "The Diewell (Syndicate Courier)"
    },
    "eadric": {
        "location": (16, 22),
        "proper_name": "Eadric (Crown Intelligencer)"
    },
    "crier_embracepenitence": {
        "location": (11, 4),
        "proper_name": "Town Crier Embracepenitence (Fluvius Broadsheets)"
    },
    "eoghan": {
        "location": [(11, 3), "barge and anchor"],
        "proper_name": "Eoghan the River-Fence"
    },
    "faintnot": {
        "location": [(11, 4), "barge and anchor"],
        "proper_name": "Delegate Faintnot (Strike Treasurer)"
    },
    "fairlight": {
        "location": (9, 14),
        "proper_name": "The Actor, Fairlight"
    },
    "fearghal": {
        "location": "barge and anchor",
        "proper_name": "Fearghal the Limping Drover"
    },
    "fearnot": {
        "location": "mayor's house",
        "proper_name": "Mayor's Butler Fearnot"
    },
    "fishmonger": {
        "location": (8, 15),
        "proper_name": "The Fishmonger"
    },
    "flyfornication": {
        "location": (13, 7),
        "proper_name": "Farmer Flyfornication"
    },
    "fleepride": {
        "location": "counting house",
        "proper_name": "Magistrate Fleepride (Fluvius Tribunal)"
    },
    "forest owls": {
        "location": [
            (9, 25), (11, 25), (13, 25), (15, 25), (17, 25),
            (19, 25), (16, 24), (20, 24), (9, 23), (12, 23),
            (8, 22), (13, 22), (7, 21), (14, 21), (11, 20)
        ],
        "proper_name": "A Parliament of Tawny Owls"
    },
    "forest squirrels": {
        "location": [
            (10, 25), (14, 25), (18, 25), (17, 24), (10, 23),
            (15, 23), (9, 22), (14, 22), (8, 21), (15, 21),
            (7, 20), (13, 20), (17, 20), (8, 19), (12, 19)
        ],
        "proper_name": "A Drey of Red Squirrels"
    },
    "forest deer": {
        "location": [
            (12, 25), (16, 25), (20, 25), (18, 24), (11, 23),
            (19, 23), (11, 22), (19, 22), (12, 21), (19, 21),
            (12, 20), (15, 20), (19, 20), (7, 19)
        ],
        "proper_name": "A Herd of Antlered Deer"
    },
    "forest armadillo": {
        "location": [
            (9, 19), (14, 19), (18, 19), (7, 18), (9, 18),
            (12, 18), (15, 18), (19, 18), (14, 17), (14, 15),
            (15, 13), (12, 12), (11, 10), (9, 8)
        ],
        "proper_name": "A Forest Giant Hairy Armadillo"
    },
    "fromabove": {
        "location": None,
        "proper_name": "Stable Worker Fromabove"
    },
    "fruiterer": {
        "location": (8, 15),
        "proper_name": "The Fruiterer"
    },
    "gilded_tongue": {
        "location": (11, 4),
        "proper_name": "Alderman Gilded-Tongue (Rival Candidate)"
    },
    "godric_reeve": {
        "location": (4, 15),
        "proper_name": "Manor Reeve Godric (Ragmore Tithe-Barn)"
    },
    "goodseed_orchardist": {
        "location": None,
        "proper_name": "Orchardist Goodseed (Fluvius Pressers' Delegate)"
    },
    "goodtidings": {
        "location": "tavern",
        "proper_name": "Bartender Goodtidings"
    },
    "grimwald": {
        "location": (11, 6),
        "proper_name": "Sergeant Grimwald (Field Quartermaster)"
    },
    "hateevil": {
        "location": (10, 4),
        "proper_name": "Laundress Hateevil"
    },
    "head hostler": {
        "location": None,
        "proper_name": "Head Hostler Lightfoot"
    },
    "holdfast": {
        "location": (17, 22),
        "proper_name": "Mayor Holdfast of Parvus"
    },
    "hopestill": {
        "location": "tavern",
        "proper_name": "Hopestill"
    },
    "hopewell": {
        "location": (10, 2),
        "proper_name": "Chandler Hopewell"
    },
    "horse": {
        "location": (7, 15),
        "proper_name": "Rosinante the Horse"
    },
    "horse groom": {
        "location": None,
        "proper_name": "Muchmerceye the Unionised Horse Groom"
    },
    "hrothgar": {
        "location": (4, 22),
        "proper_name": "Castellan Hrothgar of Ragmore"
    },
    "ironhand_carter": {
        "location": "barge and anchor",
        "proper_name": "Carter Ironhand (Fluvius Teamsters' Delegate)"
    },
    "joyinsorrow_union": {
        "location": [(8, 10), (11, 6)],
        "proper_name": "Organiser Joyinsorrow (Union Delegate)"
    },
    "keepfaith": {
        "location": "fluvius post office",
        "proper_name": "Postmistress Keepfaith"
    },
    "landlord": {
        "location": "dog and duck pub",
        "proper_name": "Landlord Fairweather"
    },
    "maeve_anchor": {
        "location": (17, 21),
        "proper_name": "Maeve (Keeper of The Salted Anchor)"
    },
    "mairead": {
        "location": (11, 1),
        "proper_name": "Mairéad the Barge-Wife"
    },
    "makepeace": {
        "location": "school",
        "proper_name": "Dr. Makepeace"
    },
    "market manager": {
        "location": (8, 15),
        "proper_name": "Godwin Williams the Market Manager"
    },
    "mayor": {
        "location": None,
        "proper_name": "Mayor Verity Givethanks"
    },
    "mayors house manager": {
        "location": "mayor's staff entrance",
        "proper_name": "Mayor's House Manager Praisegod"
    },
    "mayors maid": {
        "location": None,
        "proper_name": "Patience"
    },
    "mercenary": {
        "location": None,
        "proper_name": "Sindeny the Mercenary"
    },
    "mountain sage": {
        "location": (18, 5),
        "proper_name": "Master Spotted Tail (Sage of the Mountains)"
    },
    "odhran": {
        "location": (7, 15),
        "proper_name": "Coachman Odhrán (Mayor's Driver)"
    },
    "oisin": {
        "location": (11, 3),
        "proper_name": "Oisín the Packet-Boat Courier"
    },
    "osric": {
        "location": (9, 3),
        "proper_name": "Osric (Off-Duty Lancer)"
    },
    "oswin": {
        "location": (4, 22),
        "proper_name": "Cellarer Oswin (Ragmore Keep)"
    },
    "pawnbroker": {
        "location": "pawnbroker",
        "proper_name": "Old Pennyweight the Pawnbroker"
    },
    "pinchpenny": {
        "location": (10, 4),
        "proper_name": "Chief Clerk Pinchpenny"
    },
    "postie": {
        "location": None,
        "proper_name": "Fleetfoot the Postie"
    },
    "postmaster": {
        "location": "post office",
        "proper_name": "The Postmaster"
    },
    "rain in the face": {
        "location": (16, 15),
        "proper_name": "Rain in the Face (Communard Sage)"
    },
    "returning_officer": {
        "location": (12, 4),
        "proper_name": "Returning Officer Standfast (Fluvius Guildhall)"
    },
    "river trader": {
        "location": [(10, 20), (13, 13), (7, 7)],
        "proper_name": "Skipper Ceara (River Trader)"
    },
    "ronan_rigger": {
        "location": (16, 23),
        "proper_name": "Rigger Ronan (Parvus Rope-Walk)"
    },
    "scullery maid": {
        "location": "mayor's staff entrance",
        "proper_name": "Loveday the Scullery Maid"
    },
    "seekgrace": {
        "location": "counting house",
        "proper_name": "Bailiff Seekgrace"
    },
    "silktongue": {
        "location": [(9, 14), "playhouse"],
        "proper_name": "Silktongue (Troupe Costumer & Prompter)"
    },
    "sigeberht": {
        "location": (7, 16),
        "proper_name": "Sigeberht the Town Guard"
    },
    "skipper_omalley": {
        "location": (17, 23),
        "proper_name": "Skipper O'Malley (Coastal Packet-Boat)"
    },
    "snail envoy": {
        "location": (10, 22),
        "proper_name": "Walks in Dew, Snail Envoy (Atop Digs the Earth, a Giant Hairy Armadillo)"
    },
    "speaktruth": {
        "location": (17, 23),
        "proper_name": "Speaktruth (F.A.I. Agitator)"
    },
    "stable manager": {
        "location": "stables",
        "proper_name": "Squire Godspeed"
    },
    "steadfast_ploughman": {
        "location": None,
        "proper_name": "Ploughman Steadfast (Murum Oats Delegate)"
    },
    "tadhg": {
        "location": (12, 6),
        "proper_name": "Tadhg the Night Eel-Fisher"
    },
    "truthtale": {
        "location": None,
        "proper_name": "Truthtale"
    },
    "union clerk": {
        "location": "union house",
        "proper_name": "The Union Clerk"
    },
    "vegetable stall merchant": {
        "location": (8, 15),
        "proper_name": "Shareall the Vegetable Stall Owner"
    },
    "watchandpray": {
        "location": (10, 3),
        "proper_name": "Clockmaker Watchandpray"
    },
    "wealdhere": {
        "location": "guard house",
        "proper_name": "Captain Wealdhere"
    },
    "wellspring": {
        "location": "wallmakers' offices",
        "proper_name": "Wellspring, Guild Foreman"
    },
    "wulfgar": {
        "location": (9, 10),
        "proper_name": "Sergeant Wulfgar (Ragmore Lancers)"
    }
}

# NPC Aliases
npc_aliases = {
    "absenceofsin":                         "absenceofsin",
    "printer absenceofsin":                 "absenceofsin",
    "printer":                              "absenceofsin",
    "guard on the right":                   "aelfgifu",
    "right guard":                          "aelfgifu",
    "aelfgifu":                             "aelfgifu",
    "aelfwine":                             "aelfwine",
    "constable aelfwine":                   "aelfwine",
    "constable":                            "aelfwine",
    "aethelstan":                           "aethelstan",
    "huntsman aethelstan":                  "aethelstan",
    "huntsman":                             "aethelstan",
    "aldred":                               "aldred_foundry",
    "foundryman aldred":                    "aldred_foundry",
    "foundryman":                           "aldred_foundry",
    "apothecary":                           "apothecary",
    "armourer":                             "armourer",
    "bandoka":                              "bandoka",
    "traveller":                            "bandoka",
    "beornraed":                            "beornraed",
    "lieutenant beornraed":                 "beornraed",
    "black dog":                            "black_dog",
    "outlaw lieutenant":                    "black_dog",
    "vanguard elder":                       "black hills",
    "black hills":                          "black hills",
    "lovejoy":                              "blacksmith",
    "blacksmith":                           "blacksmith",
    "blacksmith lovejoy":                   "blacksmith",
    "bran":                                 "bran_outrider",
    "outrider bran":                        "bran_outrider",
    "outrider":                             "bran_outrider",
    "breakchains":                          "breakchains",
    "organizer":                            "breakchains",
    "buildhope":                            "buildhope",
    "guildmaster buildhope":                "buildhope",
    "butcher":                              "butcher",
    "tadg":                                 "odhran",
    "coachman tadg":                        "odhran",
    "coachman":                             "odhran",
    "cenric":                               "cenric",
    "quartermaster cenric":                 "cenric",
    "quartermaster":                        "cenric",
    "ceolwulf":                             "ceolwulf",
    "herdsman ceolwulf":                    "ceolwulf",
    "herdsman":                             "ceolwulf",
    "chandler":                             "chandler",
    "corn chandler":                        "chandler",
    "the corn chandler":                    "chandler",
    "grain merchant":                       "chandler",
    "grain stall":                          "chandler",
    "commissar":                            "commissar",
    "commissary":                           "commissar",
    "corban":                               "corban",
    "wagon-boss":                           "corban",
    "coryllus":                             "coryllus",
    "croupier":                             "croupier",
    "fortunesmile":                         "croupier",
    "croupier fortunesmile":                "croupier",
    "dairy":                                "dairy stall merchant",
    "dairy stall":                          "dairy stall merchant",
    "dairy merchant":                       "dairy stall merchant",
    "dairy stall merchant":                 "dairy stall merchant",
    "the dairy stall merchant":             "dairy stall merchant",
    "diarmuid":                             "diarmuid",
    "diewell":                              "diewell",
    "the diewell":                          "diewell",
    "eadric":                               "eadric",
    "crown intelligencer":                  "eadric",
    "embracepenitence":                     "embracepenitence",
    "town crier":                           "embracepenitence",
    "crier":                                "embracepenntence",
    "eoghan":                               "eoghan",
    "eoghan the river-fence":               "eoghan",
    "faintnot":                             "faintnot",
    "delegate faintnot":                    "faintnot",
    "treasurer":                            "faintnot",
    "the actor":                            "fairlight",
    "butler":                               "fearnot",
    "the butler":                           "fearnot",
    "mayors butler":                        "fearnot",
    "mayor's butler":                       "fearnot",
    "fearghal":                             "fearghal",
    "limping drover":                       "fearghal",
    "drover":                               "fearghal",
    "fleepride":                            "fleepride",
    "magistrate fleepride":                 "fleepride",
    "owls":                                 "forest owls",
    "forest owls":                          "forest owls",
    "parliament of tawny owls":             "forest owls",
    "squirrels":                            "forest squirrels",
    "forest squirrels":                     "forest squirrels",
    "drey of red squirrels":                "forest squirrels",
    "deer":                                 "forest deer",
    "forest deer":                          "forest deer",
    "herd of antlered deer":                "forest deer",
    "forest armadillo":                     "forest armadillo",
    "a forest giant hairy armadillo":       "forest armadillo",
    "armadillo":                            "forest armadillo",
    "fromabove":                            "fromabove",
    "stable worker fromabove":              "fromabove",
    "stable worker":                        "fromabove",
    "fairlight":                            "fairlight",
    "fishmonger":                           "fishmonger",
    "fishmongers":                          "fishmonger",
    "flyfornication":                       "flyfornication",
    "farmer flyfornication":                "flyfornication",
    "fruiterer":                            "fruiterer",
    "gilded_tongue":                        "gilded_tongue",
    "alderman gilded-tongue":               "gilded_tongue",
    "rival candidate":                      "gilded_tongue",
    "godric_reeve":                         "godric_reeve",
    "reeve godric":                         "godric_reeve",
    "manor reeve":                          "godric_reeve",
    "reeve":                                "godric_reeve",
    "goodseed":                             "goodseed_orchardist",
    "orchardist goodseed":                  "goodseed_orchardist",
    "bartender":                            "goodtidings",
    "barkeep":                              "goodtidings",
    "grimwald":                             "grimwald",
    "sergeant grimwald":                    "grimwald",
    "quartermaster":                        "grimwald",
    "field sergeant":                       "grimwald",
    "hateevil":                             "hateevil",
    "laundress hateevil":                   "hateevil",
    "lightfoot":                            "head hostler",
    "hostler":                              "head hostler",
    "head hostler":                         "head hostler",
    "holdfast":                             "holdfast",
    "mayor holdfast":                       "holdfast",
    "hopestill":                            "hopestill",   
    "hopewell":                             "hopewell",
    "chandler hopewell":                    "hopewell",
    "fluvius chandler":                     "hopewell",
    "rosinante":                            "horse",
    "horse":                                "horse",
    "groom":                                "horse groom",
    "horse groom":                          "horse groom",
    "union worker":                         "horse groom",
    "worker":                               "horse groom",
    "muchmerceye":                          "horse groom",
    "hrothgar":                             "hrothgar",
    "castellan hrothgar":                   "hrothgar",
    "castellan":                            "hrothgar",
    "ironhand":                             "ironhand_carter",
    "carter ironhand":                      "ironhand_carter",
    "joyinsorrow":                          "joyinsorrow_union",
    "organiser joyinsorrow":                "joyinsorrow_union",
    "keepfaith":                            "keepfaith",
    "postmistress":                         "keepfaith",
    "postmistress keepfaith":               "keepfaith",
    "fairweather":                          "landlord",
    "landlord fairweather":                 "landlord",
    "landlord":                             "landlord",
    "maeve":                                "maeve_anchor",
    "tavern-keeper maeve":                  "maeve_anchor",
    "mairead":                              "mairead",
    "barge-wife":                           "mairead",
    "headteacher":                          "makepeace",
    "dr":                                   "makepeace",
    "dr. makepeace":                        "makepeace",
    "godwin":                               "market manager",
    "godwin williams":                      "market manager",
    "godwin williams the market manager":   "market manager",
    "market manager":                       "market manager",
    "mayor":                                "mayor",
    "verity":                               "mayor",
    "verity givethanks":                    "mayor",
    "mayor verity givethanks":              "mayor",
    "mayor givethanks":                     "mayor",
    "praisegod":                            "mayors house manager",
    "house manager":                        "mayors house manager",
    "mayor's house manager":                "mayors house manager",
    "patience":                             "mayors maid",
    "mayors maid":                          "mayors maid",
    "mayor's maid":                         "mayors maid",
    "sindeny":                              "mercenary",
    "sindeny the mercenary":                "mercenary",
    "mercenary":                            "mercenary",
    "sage":                                 "mountain sage",
    "spotted tail":                         "mountain sage",
    "master spotted tail":                  "mountain sage",
    "mountain sage":                        "mountain sage",
    "oisin":                                "oisin",
    "packet courier":                       "oisin",
    "osric":                                "osric",
    "lancer osric":                         "osric",
    "oswin":                                "oswin",
    "cellarer oswin":                       "oswin",
    "cellarer":                             "oswin",
    "pawnbroker":                           "pawnbroker",
    "pennyweight":                          "pawnbroker",
    "old pennyweight":                      "pawnbroker",
    "pawn shop":                            "pawnbroker",
    "pinchpenny":                           "pinchpenny",
    "chief clerk":                          "pinchpenny",
    "clerk pinchpenny":                     "pinchpenny",
    "postie":                               "postie",
    "fleetfoot":                            "postie",
    "fleetfoot the postie":                 "postie",
    "postmaster":                           "postmaster",
    "post master":                          "postmaster",
    "postmaster safehaven":                 "postmaster",
    "post master safehaven":                "postmaster",
    "safehaven":                            "postmaster",
    "communard sage":                       "rain in the face",
    "rain in the face":                     "rain in the face",
    "standfast":                            "returning_officer",
    "returning officer":                    "returning_officer",
    "skipper":                              "river trader",
    "ceara":                                "river trader",
    "skipper ceara":                        "river trader",
    "river trader":                         "river trader",
    "ronan":                                "ronan_rigger",
    "rigger ronan":                         "ronan_rigger",
    "rigger":                               "ronan_rigger",
    "loveday":                              "scullery maid",
    "maid":                                 "scullery maid",
    "scullery maid":                        "scullery maid",
    "seekgrace":                            "seekgrace",
    "bailiff seekgrace":                    "seekgrace",
    "guard on the left":                    "sigeberht",
    "left guard":                           "sigeberht",
    "sigeberht":                            "sigeberht",
    "silktongue":                           "silktongue",
    "costumer":                             "silktongue",
    "prompter":                             "silktongue",
    "omalley":                              "skipper_omalley",
    "skipper omalley":                      "skipper_omalley",
    "skipper":                              "skipper_omalley",
    "snail":                                "snail envoy",
    "snail envoy":                          "snail envoy",
    "walks in dew":                         "snail envoy",
    "envoy walks in dew":                   "snail envoy",
    "speaktruth":                           "speaktruth",
    "squire":                               "stable manager",
    "godspeed":                             "stable manager",
    "squire godspeed":                      "stable manager",
    "steadfast":                            "steadfast_ploughman",
    "ploughman steadfast":                  "steadfast_ploughman",
    "tadhg":                                "tadhg",
    "eel-fisher":                           "tadhg",
    "truthtale":                            "truthtale",
    "clerk":                                "union clerk",
    "union clerk":                          "union clerk",
    "vegetable stall":                      "vegetable stall merchant",
    "veg stall":                            "vegetable stall merchant",
    "shareall":                             "vegetable stall merchant",
    "watchandpray":                         "watchandpray",
    "clockmaker":                           "watchandpray",
    "wealdhere":                            "wealdhere",
    "captain":                              "wealdhere",
    "captain wealdhere":                    "wealdhere",
    "wellspring":                           "wellspring",
    "foreman":                              "wellspring",
    "foreman wellspring":                   "wellspring",
    "wulfgar":                              "wulfgar",
    "sergeant wulfgar":                     "wulfgar",
    "lancer sergeant":                      "wulfgar"
}

# --- READABLES DATABASE ---
readables_database = {
    "noticeboard": {
        "location": "town hall",
        "text": "--- OFFICIAL MURUM NOTICEBOARD ---" +
        "\nWANTED: Work available in Stables, please enquire with Squire Godspeed at Murum Stables." +
        "\nWANTED: Blacksmith apprentice, good reputation required, enquiries with Blacksmith opposite Union House." +
        "\nWANTED: Market sweeper needed to maintain clean and tidy market, no timewasters. Enquire with Market Manager Godwin Williams." +
        "\nWANTED: Reputable House staff required for work in Mayor's House. Enquiries to be made to House Manager Praisegod at 1 Central Square, Murum. South west of Town hall."
    },
    "poster": {
        "location": "inventory",
        "text": "Looking for work?" +
        "\nGood pay for the right person." +
        "\nAsk for Hopestill at the Murum Tavern."
    },
    "reference letter": {
        "location": "inventory",
        "text": "The ink on this letter is smudged and unreadable."
    },
    "foaling manual": {
        "location": "inventory",
        "text": "--- FOALING EMERGENCIES ---\n1. Ensure you completely [COFFEE STAIN]... before touching the animal to prevent infection.\n2. Administer [COFFEE STAIN]... to soothe the mother's panic.\n3. If breached, gently reposition the [HEAVY SMEAR]... limbs so they face outward. Leave the hind legs alone.\n4. Pull in rhythm with her [COFFEE STAIN]... do not force against her."
    },
    "bronze plaque": {
        "location": "school",
        "text": "\"Dr. Makepeace, HEADTEACHER\""
    },
    "signpost": {
        "location": (8, 17),
        "text": "<- North: The New Road | South: Town Center ->"
    },
    "torn ledger page": {
        "location": "inventory",
        "text": "--- STABLE ACCOUNTS ---\nCLIENTS: The Mayor, The Guard, The Blacksmith, The Wallmakers.\nAMOUNTS: 15s, 25s, 30s, 45s.\nSTATUS: 3 Paid, 1 UNPAID."
    },
    "smudged receipt": {
        "location": "inventory",
        "text": "--- RECEIPT OF PAYMENT ---\nDATE: Monday\nAMOUNT: 30 Silver\nSTATUS: PAID IN FULL\nCLIENT: [HEAVILY SMUDGED]"
    },
    "hidden secret ledger": {
        "location": "inventory",
        "text": "--- TRUE STABLE ACCOUNTS ---\nWALLMAKERS GUILD: 850 Silver in arrears.\nNOTE: Wellspring threatened to burn the stables to the ground if I reported this to the Castellan."
    },
    "postie's route sheet": {
        "location": "inventory",
        "text": (
            "--- OFFICIAL POSTAL DELIVERY LOOP ---\n"
            "Postie Departure: 34 minutes ago from Post Office.\n"
            "Postie Speed: 14 minutes per stop.\n"
            "Your Speed: 10 minutes per grid move (North, South, East, or West).\n"
            "RULE: Take the shortest route directly to the stop where you and the Postie will arrive at the EXACT same minute!\n\n"
            "Stop 1 (A): Murum Stables\n"
            "Stop 2 (B): Murum Guard House\n"
            "Stop 3 (C): The School\n"
            "Stop 4 (D): Murum Playhouse\n"
            "Stop 5 (E): The Wallmakers' Office\n"
            "Stop 6 (F): The Blacksmiths\n"
            "Stop 7 (G): Union House\n"
            "Stop 8 (H): Murum Town Hall\n"
            "Stop 9 (I): The Dog and Duck Pub\n"
            "Stop 10 (J): Murum Post Office"
        )
    },
    "bundle of radical pamphlets": {
        "location": "inventory",
        "text": (
            "--- WHAT IS PROPERTY? (P.J. Proudhon) ---\n"
            "\"If I were asked to answer the following question: What is slavery? and I should answer in one word, It is murder! my meaning would be understood at once.\n"
            "Why, then, to this other question: What is property? may I not likewise answer, It is theft!\"\n\n"
            "[Handwritten in the margin in violet ink]:\n"
            "\"Truthtale and the Union House bureaucrats beg for crumbs from the Mayor's table, while Wealdhere's foreign mercenaries guard the gates. Only the Free-Earth Syndicate and direct action will break the Castellan's chains.\"\n\n"
            "[Physical Clue]: The corners of the parchment are stained with deep purple root-juice and smell of damp soil."
        )
    },
    "wallmaker blueprint": {
        "location": "inventory",
        "text": "--- HOLLOW-BORE MASONRY DRILL ---\n1. Order specialized diamond-tipped drill parts from Fluvius via the Post Office.\n2. Purchase thick Leather from the High Street Commissary.\n3. Fit the 5 components into the 5x5 assembly frame at the Blacksmiths."
    },
    "smugglers' cipher": {
        "location": "inventory",
        "text": (
            "Scrawled in charcoal upon the oiled vellum are three symbols:\n"
            "  1. A Shuttered Lantern (Keep the light hidden past the murder-holes)\n"
            "  2. A Chipped Merlon aligned with the Tavern Chimney\n"
            "  3. A note at the bottom: 'If the East Breach fails, hide the Silk Cache in the upper parapet dead-drop. "
            "X will tap the mason's rhythm at the milestone.'"
        )
    },
    "bandoka's cipher": {
        "location": "inventory",
        "text": (
            "--- CODED CIPHER CYLINDER (BANDOKA'S DOSSIER) ------\n"
            "A heavy brass letter-ring cylinder. Aligning the rotating sleeves to the keyword 'CALIGO' decodes the enclosed vellum strip:\n\n"
            "\"To Castellan Eormenhild at Castle Laydere:\n"
            " Murum dispatches verified. The Watch post at on the New Road is undermanned on the night shift. "
            " Strike the frontier road before the Union strike committee mobilizes.\n"
            " — B.\"\n\n"
            "*** This cipher confirms Bandoka was acting as a deep-cover saboteur for Castle Laydere! Take this to Captain Wealdhere at the Guard House or keep it for leverage. ***"
        )
    },
    "weathered signpost": {
        "location": (5, 17),
        "text": (
            "--- WEATHERED CROSSROADS SIGNPOST ---\n"
            "A moss-covered wooden fingerpost pointing down three diverging tracks:\n\n"
            "--> NORTH-EAST: 'Murum Town (1 League)'\n"
            "--> SOUTH: 'The Old Path to Fluvius Town (Beware Rockslides)'\n"
            "--> WEST: 'Caligo Mountains & River Ferry (Seek the Sage at the Summit)'\n\n"
            "You can see, scratched into the wood at the bottom of the signpost a barely legible message:\n"
            "'Brandy lands at the hidden shingle cove along the Old Path at midnight.'"
        )
    },
    "murum dispatch board": {
        "location": "fluvius post office",
        "text": (
            "--- MURUM PACKET-BOAT DISPATCHES & POSTAL GAZETTE ---\n"
            "• DISPATCH FROM MURUM POSTMASTER SAFEHAVEN: 'Regular river-packet service between Murum and Fluvius continues despite the unrest along the roads.'\n"
            "• UNION HOUSE CIRCULAR (Signed by Truthtale): 'To all southern hands: Do not believe the flyers distributed in the Caligo foothills! The Murum Workers' Union has NOT settled with the Kokeshi Syndicate, and our strike fund stands unbroken.'\n"
            "• GUARD HOUSE NOTICE: 'Watch Sergeant Beornraed's lancers have been deployed to observe the southern farm crossroads. Both strikers and drovers are warned that drawing lethal steel or cold iron on the highway will be treated as armed insurrection.'"
        )
    },
    "drover's chalk slate": {
        "location": (12, 4),
        "text": (
            "--- TEAMSTERS' YARD CHALK SLATE ---\n"
            "Scrawled in dusty white chalk beside the grain-scales:\n\n"
            "  'CONVOY ORDERS — THREE HEAVY GRAIN-WAINS'\n"
            "  'Route: Bypass the main crossroads until the last moment via the West Sunken Sluice-Lane.'\n"
            "  'Muster Time: High Noon (5:00) sharp.'\n"
            "  'Escort: Six Kokeshi Bruisers (unarmed—Watch lancers are watching the ridge).'\n"
            "  'Note: Keep the Caligo quarrymen's mules locked in the eastern corral until they deliver the sacks to the barges.'"
        )
    },
    "war manual": {
        "location": "inventory",
        "text": (
            "=== ARTICLES OF WAR & CAMPAIGN MANUAL ===\n"
            "1. THE 100-POINT HEGEMONY GOAL:\n"
            "   Victory belongs to the first faction to reach 100 Hegemony "
            "Points. Your score combines your locked Chapter I-II Legacy "
            "Foundation (10-35 Pts) with Live Territories (+4 Pts each), "
            "Sympathy (up to +20 Pts), and Agenda Milestones (+5 Pts per "
            "clash won, +15 Pts per Stronghold Siege).\n\n"
            "2. THE THREE DAILY PHASES:\n"
            "   • MORNING (Logistics & Dice Tray): Drag Command Dice into "
            "Muster, Supply Lines, Barricades, or Rations. Unslotted dice "
            "convert directly into Afternoon Movement Points (MP). Deploy "
            "Chapter II tools (Printing Press, Codewheel, Forge Steel) via "
            "the bottom ledger.\n"
            "   • AFTERNOON (The March): Generals and Captains move carved "
            "war-blocks across the map (Open/Road: 1 MP; Forest/Mountain: "
            "2 MP; Flooded Basins: Impassable). Privates toggle into First-"
            "Person Field Mode ('MAIN') to walk the map and complete their "
            "Captain's directive before dusk for +2 Tactical Tokens.\n"
            "   • EVENING (Tactical Clash & Sieges): Colliding armies roll "
            "dice pools equal to battalion strength + rank bonus. Trigger "
            "Faction Advantages (Ragmore '6' Snipe, Union Pair-Lock, "
            "Kokeshi/FAI 10s Sabotage, Laydere Tiebreaker) before pressing "
            "the assault.\n\n"
            "3. CHAIN OF COMMAND & SUBVERSION:\n"
            "   • GENERALS forge Known Treaties (+2 Standing) or Secret "
            "Pacts, or Betray Allies (+6 Pts, -10 Standing).\n"
            "   • CAPTAINS execute Sector Directives (+5% Confidence). If "
            "Confidence drops to 35% or below, Captains may Incite a Coup "
            "to become General or Defect to a rival faction.\n"
            "   • PRIVATES earn promotions through field directives or "
            "seize Captaincy during night skirmishes."
        ),
    },
    
}

# --- REGISTER ALL MAPS IN READABLES DATABASE ---
MAP_READABLES = {
    "murum town map": {
        "location": "inventory",
        "text": "A detailed street plan of the walled town of Murum and its civic buildings."
    },
    "dtessera terra world map": {
        "location": "inventory",
        "text": "A grand cartographic atlas of the entire known world of Dtessera Terra."
    },
    "parvus town map": {
        "location": "inventory",
        "text": "A coastal chart of Parvus Town, the northern New Road, and the northern forest edge."
    },
    "fluvius town map": {
        "location": "inventory",
        "text": "A surveyor's map of Fluvius Town, its farmlands, and the southern river delta."
    },
    "lignum forest map": {
        "location": "inventory",
        "text": "A forester's chart of the sprawling Lignum Forest and its central glade."
    },
    "caligo mountains map": {
        "location": "inventory",
        "text": "A high-altitude chart of the Caligo Mountain Range and the hidden Mountain Lake."
    }
}
readables_database.update(MAP_READABLES)

readable_aliases = {
    "reference":            "reference letter",
    "letter":               "reference letter",
    "board":                "noticeboard",
    "notices":              "noticeboard",
    "plaque":               "bronze plaque",
    "sign":                 "signpost",
    "flyer":                "poster",
    "paper":                "poster",
    "ledger":               "torn ledger page",
    "receipt":              "smudged receipt",
    "manual":               "foaling manual",
    "secret ledger":        "hidden secret ledger",
    "route":                "postie's route sheet",
    "route sheet":          "postie's route sheet",
    "blueprint":            "wallmaker blueprint",
    "pamphlets":            "bundle of radical pamphlets",
    "pamphlet":             "bundle of radical pamphlets",
    "contraband":           "bundle of radical pamphlets",
    "smugglers cipher":     "smugglers' cipher",
    "smuggler's cipher":    "smugglers' cipher",
    "map":                  "murum town map",
    "town map":             "murum town map",
    "world map":            "dtessera terra world map",
    "parvus map":           "parvus town map",
    "fluvius map":          "fluvius town map",
    "forest map":           "lignum forest map",
    "mountain map":         "caligo mountains map",
    "cipher":               "bandoka's cipher",
    "bandoka's cipher":     "bandoka's cipher",
    "cylinder":             "bandoka's cipher",
    "signpost":             "weathered signpost",
    "weathered signpost":   "weathered signpost",
    "dispatch board":       "murum dispatch board",
    "murum dispatch board": "murum dispatch board",
    "chalk slate":          "drover's chalk slate",
    "drover's chalk slate": "drover's chalk slate",
    "slate":                "drover's chalk slate",
    "war manual":           "war manual",
    "manual":               "war manual",
    "articles of war":      "war manual",
    "rule book":            "war manual",
}

storage_locations = {
    "tavern", "dog and duck pub", "stables", "tack room",
    "mayor's house", "mayor's staff entrance", "blacksmiths"
}
STORAGE_LOCATIONS = storage_locations


