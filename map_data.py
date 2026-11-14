# 1. The Blueprint
    # This tells Python what information every location must contain.
class Location:
    def __init__(self, name, description, objects, region, altitude=None):
        self.name = name
        self.description = description
        self.objects = objects
        self.region = region
        self.altitude = altitude  # Tier 0 (0m Water) to Tier 5 (450m High Peaks)

# 2. Building the Map
    # We use a dictionary to attach our Location boxes to your specific coordinates.
murum_town_locations = {
    (7, 16): Location("The Town Gate", "You stand outside Murum Town Gate, two twenty feet solid oak doors, reinforced with steel bands." +
                      "Two guards stand either side surveying the people and goods come into and out of town.",\
                      ["Iron Banded Oak Gates"], "Murum Town"),
    (7, 15): Location("The Stables", "You stand outside Murum Stables. Situated to the south of the town gate, and nestled against the wall that surrounds Murum, " +
                      "these large stables house and care for all the horses that enter Murum." +
                      "\nThe smell is strong and familiar, and the noise of the two dozen horses kicking and braying result in an envelopment of your senses." +
                      "\nThe rest of the town melts away.",\
                      ["Horse"], "Murum Town"),
    (7, 14): Location("The Guard House", "The Guard House is little more than a glorified shed. Situated in the south west of town the guards make do with their 'digs'," +
                      "\ntaking pride in keeping them clean and taking the time to maintain that which they have been given.  Two of them busily repaint the wooden planks" +
                      "\nthat provide their scant shelter as you approach.",\
                      ["Archery Butts"], "Murum Town"),
    (8, 16): Location("Post Office", "The Post office is a wooden building in the North West of town. It has a pitched wooden roof that is in dire need of renovating," +
                      "\nthe moss and cracks pepper its exterior and the door lilts in its frame. A nailed up sign above the door identifies the sad building as the post office." +
                      "\nYou can see people through the illuminated windows busying away and here their chatter spilling into the street.",\
                      ["Postbox"], "Murum Town"),
    (8, 15): Location("The Food Market", "A large open air market with many people bustling among the stalls.",\
                      ["Water Fountain"], "Murum Town"),
    (8, 14): Location("Escuela Moderna", "You see the school that has been your prison for the last 12 years. A boarding school and the only school in Murum Town." +
                      "\nIt houses all of the children of Murum, and these children are raised by the town.",\
                      [], "Murum Town"),
    (9, 13): Location("The House of Games",
                      "Tucked into the southern entertainment quarter beside the Playhouse stands The House of Games—Murum's famous gaming house and mechanical arcade."
                      "\nCrimson lanterns glow beneath its gilded sign, and the clatter of ivory roulette balls, shuffling cards, and clockwork parlour machines spills into the street.",
                      ["Gilded Roulette Sign"], "Murum Town"),
    (9, 16): Location("Dog and Duck Pub", "This beautiful pub at the north end of town is the oldest surviving building of Murum, parts of the building are over 1000 years old." +
                      "\n It is a splendidly rambling complex of two adjoining inns. The older, low-ceilinged timber-framed pub, and a newer whitewashed section housing a formal dining room." +
                      "\nOriginally the building was a Saxon hospice founded by the Murum Castallen, it was enlarged in stone after the Defenestration of the Old Order." +
                      "\nIt was then that it became a stronghold of unionism.",\
                      [], "Murum Town"),
    (9, 15): Location("Mayor's House", "The largest house in the town, it stands proudly but awkwardly in the centre of town." +
                      "\nThe path of the front garden leads directly to a grand entrance." +
                      "\nJust in your peripheral vision you espy a second entrance on the farside of the building, probably for staff and deliveries.",\
                      [], "Murum Town"),
    (9, 14): Location("Playhouse", "You have entered the suburb of sin, notorious for licentious behaviour, brothels and gaming houses." +
                      "\nThe most prominent building however is a polygonal wooden building with three galleries surrounding an open yard."
                      "\nFrom one side of the polygon extended a thrust stage." +
                      "\nIt is the Murum Playhouse. The local theatre is the heart of the entertainment for the townsfolk of Murum.",\
                      [], "Murum Town"),
    (8, 13): Location("Grazing Field", "A lush, open pasture of sweet green grass. Perfect for grazing.", ["Beautiful green grass", "Archery Butts"], "Murum Town"),
    (10, 16): Location("Town Hall", "You can see Murum Town hall ahead, a weathered building with doric columns framing its facade." +
                      "\nBuilt in the axis of the road it appears as a three storey bulding to the square and, because of the height difference, two storey to the rear road."
                      "\nThere are two long wards with five vertical window axes each and towers at the four corners of the building." +
                       "\nYou observe the weight of the cobnuts burden the boughs of the trees that surround this impressive building.",\
                      ["Cobnut Trees"], "Murum Town"),
    (10, 15): Location("High Street", "A bustling highstreet of shops for weary travellers and adventurers in need to gather their tools." +
                       "A dirt road cuts through the middle of a run of shops on either side, each advertising their wares.",\
                       [], "Murum Town"),
    (10, 14): Location("The Wallmakers' Offices", "Amongst the busy streets you can clearly see where the Wallmakers' Guild run their operation." +
                       "\nIt is a distinguished red brick building with a red-tiled roof and terracotta detailing, and features a prominent clock." +
                       "\n— a confident civic statement that carved its function in stone: the words \"Wallmakers' Offices\" are visible aobve the lintels of the beautiful sash windows that frame its entrance.",\
                      [], "Murum Town"),
    (10, 13): Location("Murum Tavern", "Tucked away in the south eastern corner of the Murum you can see the hanging sign of the Murum Tavern." +
                      "The building looks inviting but there exists too, a small voice speaking of great concern about the goings on of this seemingly friendly destination",\
                      [], "Murum Town"),
    (11, 15): Location("Union House", "Union house is a hodge podge of a building betraying is multiyear growth. A monstrosity that no architect would take responsibility for." +
                       "\nIt has a main building, wooden in construction and typical in design, two stories, a pitched wooden roof, double fronted windows, but tacked on with little thought" +
                       "\nis a brick built lean-to on the right, the pressure of which has caused the entire building to bow." +
                       "\nPerhaps to counterbalance this design floor, perhaps because of the growing size of the union power in the town of Murum," +
                       "\na second brick built extension has been added on the left, much larger than the first but more poorly constructed and judging by its appearance - " +
                       "\nperhaps never completely finsihed." +
                       "\nIn spite of this the place is incredibly active with serious faced people moving with intent in and out of the buildings.",\
                      [], "Murum Town"),
    (11, 14): Location("Blacksmiths", "You can see the Blacksmith shop before you, a glorified barn situated on the outskirts of town." +
                       "\nThe noise justifies this piece of town planning as the burning furnace and strikes of iron ring loud in the air." +
                       "\nBuckets of sand line the building, some hold hot pokers, others are in place waiting to be used to smother fire.",\
                      ["Bucket of sand"], "Murum Town")
}

ragmore_plains_locations = {
    (6,25): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (7,25): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (8,25): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (6,24): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (7,24): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (8, 24): Location(
        "Ragmore Plains — Eastern Forest Hedge",
        "Where the open cattle pastures of Ragmore Plains meet the dark eaves of Lignum Forest, a section of the boundary hedge has been trampled flat by fleeing stags and wild boars.\n"
        "A strange, acrid stench of rancid tallow and wolf-gall hangs on the breeze from a row of freshly whittled ash-stakes driven into the turf.",
        ["Trampled Hedge", "Reeking Ash-Stakes"],
        "Plains"
    ),
    (2,23): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the East you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (5,23): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the West you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (6,23): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (7,23): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (2,22): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the East you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (5,22): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the West you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (6,22): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (2,21): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the North East you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (3,21): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the North you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (4,21): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the North you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (5,21): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals. To the North West you can see Ragmore Castle", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (2,20): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (3,20): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (4,20): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (5,20): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (2,19): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (3,19): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (4,19): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (5,19): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (2,18): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (3,18): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (4,18): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains"),
    (5,18): Location("Ragmore Plains", "Grassland spreads out before you. You can see cattle grazing and herders tending to their animals.", ["Tall Grass", "Grazing Cattle"], "Plains")

}

old_path_plains_locations = {
    (3,8): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (3,9): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (3,10): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (3,11): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (4,8): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (4,9): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (4,10): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (4,11): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (5,9): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (5,10): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains"),
    (5,11): Location("Old Path Plains", "Wind-swept grassland rolling between the Old Path and the southern river bends.\n"
        "Wildflowers and tough meadow-grass ripple beneath the sea breeze.", ["Meadow Grass"], "Old Path Plains")

}

the_diluvium_glade_locations = {
    (8,20): Location("The Diluvium Glade", "A hushed, sun-dappled clearing hidden deep within the northern reaches of Lignum Forest.\n"
        "Ancient standing stones ring a carpet of soft emerald moss beside the entrance to a tangled briar-labyrinth.",
        ["Standing Stones", "Briar Archway"], "Diluvium Glade"),
    (10,22): Location("The Diluvium Glade", "A hushed, sun-dappled clearing hidden deep within the northern reaches of Lignum Forest.\n"
        "Ancient standing stones ring a carpet of soft emerald moss beside the entrance to a tangled briar-labyrinth.",
        ["Standing Stones", "Briar Archway"], "Diluvium Glade")

}

the_lignum_forest_glade_locations = {
    (15,15): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (15,16): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (16,14): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (16,15): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (16,16): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (16,17): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (17,14): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (17,15): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (17,16): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (17,17): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (18,15): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade"),
    (18,16): Location("The Lignum Forest Glade", "The peaceful heart of Lignum Forest, where the suffocating canopy opens to the sky.\n"
        "Clear springs bubble between the roots of giant oaks, and woodland creatures gather in quiet harmony.",
        ["Clear Spring", "Soft Moss"], "Lignum Glade")

}

ragmore_farm_locations = {
    (3,13): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (3,14): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (3,15): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (3,16): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (4,13): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (4,14): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (4, 15): Location(
        "Ragmore Farmland — Manor Tithe-Barn",
        "A sprawling stone tithe-barn stands at the heart of the Ragmore tenant holdings, surrounded by heavy baggage wains.\n"
        " Fresh wheel-ruts lead behind the threshing floor, and a pungent smell of tallow and pine-tar drifts from the grease-buckets beside the wagon hubs.",
        ["Tithe-Barn Doors", "Grease-Buckets"],
        "Ragmore Farm"
    ),
    (4,16): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (5,13): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (5,14): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (5,15): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm"),
    (5,16): Location("Ragmore Farmland", "Broad ploughed fields of barley and turnips supplying the granaries of Castle Ragmore to the north.\n"
        "Dry-stone walls divide the holdings, and woodsmoke rises from distant tenant cottages.",
        ["Ploughed Furrows", "Dry-Stone Wall"], "Ragmore Farm")

}

murum_farm_locations = {
    (7,10): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (7,11): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (8,10): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (8,11): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (9,10): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (9,11): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (10,10): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm"),
    (10,11): Location("Murum Farmland", "Fertile strip-farms just south of Murum's walls where purple carrots, oats, and cabbages are grown for the Food Market.\n"
        "Irrigation ditches carry water down from the hills toward the river.",
        ["Carrot Beds", "Irrigation Ditch"], "Murum Farm")

}

fluvius_farm_locations = {
    (10,5): Location("The Sunken Sluice-Gate Lane", "Where the Old Path dips down into the western Fluvius basin, the wagon track runs through a deep, narrow hollow between high clay banks.\n"
        "Above the western embankment sits an ancient timber-and-iron irrigation sluice holding back a brimming mill-pond; its rusted iron lynch-pin is wedged tight with a cracked oak chock, while loose boundary boulders teeter along the lip of the ditch.",
        ["Rusted Sluice-Gate", "Loose Boundary Boulders"], "Fluvius Farm"),
    (10,6): Location("Western Cider Orchards", "Rows of gnarled thirty-year-old apple trees stretch across the western river-terrace.\n"
        "Heavy oak cider-presses stand beneath a thatched open barn, the air thick with the sharp, sweet tang of crushed pomace.",
        ["Cider Presses", "Orchard Fence"], "Fluvius Farm"),
    (10,7): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (11,5): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (11,6): Location("Fluvius Farm Crossroads & Picket Brazier", "The main agricultural crossroads north of Fluvius Town, where the tracks from the Murum oat-fields, the western orchards, and the sunken lane converge.\n"
        "Striking farmhands have overturned a pair of hay-wains across the ruts and lit a roaring iron brazier.",
        ["Picket Brazier", "Overturned Hay-Wains"], "Fluvius Farm"),
    (11,7): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (12,5): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (12, 6): Location("Southern River Reeds & Eel-Weirs", "A quiet backwater of tall bullrushes and willow osiers along the bend of the River Fluvius.\n"
        "Wicker eel-traps are staked into the shallows, giving a clear view across the channel toward the eastern watermill.",
        ["Wicker Eel-Traps", "Willow Osiers"], "Fluvius Farm"),
    (12,7): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (13,5): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (13,6): Location("Fluvius Farmland", "Rich alluvial farmlands bordering the southern delta of the River Fluvius.\n"
        "Waterwheels creak along the embankments, feeding flooded orchards and grain paddocks.",
        ["Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (13, 7): Location("The East-Bank Watermill", "An old stone grist-mill straddling the eastern mill-race. Its great oak waterwheel hangs crookedly in its frame, several thick paddles shattered.\n"
        "Looking closely at the splintered oak axle, the wood isn't hacked by a blade—clean, cylindrical holes have been bored straight through the heartwood, and a faint smear of yellow mountain clay clings to the sluice-plank.",
        ["Shattered Waterwheel", "Splintered Oak Axle"], "Fluvius Farm"),
}

# Must create code to prevent player from entering until they have learnt how to swim
ragmore_lake_locations = {
    (2,24): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (2,25): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (3,24): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (3,25): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (4,24): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (4,25): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (5,24): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake"),
    (5,25): Location("Ragmore Lake", "The dark, mirror-still waters of Ragmore Lake lap against the northern foundations of Castle Ragmore.\n"
        "Cold mist clings to the surface, hiding submerged ruins beneath the depths.",
        ["Cold Water", "Submerged Stones"], "Ragmore Lake")

}

# Must create code to prevent player from entering until they have learnt how to swim
diluvium_lake_locations = {
    (9,20): Location("Lake Diluvium", "A secluded, crystal-clear woodland lake encircled by the ancient oaks of Lignum Forest.\n"
        "Beneath the lilies, the water drops into a deep, shadowed basin.",
        ["Water Lilies", "Clear Water"], "Diluvium Lake"),
    (9,21): Location("Lake Diluvium", "A secluded, crystal-clear woodland lake encircled by the ancient oaks of Lignum Forest.\n"
        "Beneath the lilies, the water drops into a deep, shadowed basin.",
        ["Water Lilies", "Clear Water"], "Diluvium Lake"),
    (10,21): Location("Lake Diluvium", "A secluded, crystal-clear woodland lake encircled by the ancient oaks of Lignum Forest.\n"
        "Beneath the lilies, the water drops into a deep, shadowed basin.",
        ["Water Lilies", "Clear Water"], "Diluvium Lake")

}

# Must create code to prevent player from entering until they have learnt how to swim
calluna_lake_locations = {
    (6,1): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (7, 1): Location(
        "Lake Calluna — The Sunken Mausoleum Shore",
        "Where the peat-stained waters of Lake Calluna lap against the southern heath, a half-submerged lintel of ancient black basalt juts from the reeds.\n"
        "Carved heraldic shields of the First Castellans flank a flight of mossy stone steps descending into a dark, subterranean crypt.",
        ["Submerged Basalt Lintel", "Crypt Steps"],
        "Calluna Lake"
    ),
    (8,1): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (9,1): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (10,1): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (7,2): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (8,2): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (9,2): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake"),
    (8,3): Location("Lake Calluna", "A broad, reed-ringed lake gleaming like pewter in the middle of the southern Heath.\n"
        "Peat-stained streams feed its quiet bays.",
        ["Peat Reeds", "Calm Water"], "Calluna Lake")

}

the_mountain_lake_locations = {
    (17,2): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (18,2): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (19,2): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (20,2): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (17,3): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (18,3): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (19,3): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (20,3): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (18,4): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (19,4): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (20,4): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (19,5): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (20,5): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake"),
    (20,6): Location("The Mountain Lake", "An icy, emerald-blue glacial tarn cradled high within the Caligo Mountain Range.\n"
        "Snowmelt cascades down the surrounding cliffs into the deep basin.",
        ["Glacial Water", "Quartz Pebbles"], "The Mountain Lake")
    
}

dtessera_sea_locations = {
    (1,1): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,2): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,3): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,4): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,5): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,6): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,7): Location("Dtessera Sea","The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,8): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (1,9): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (2,1): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (2,2): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (2,3): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (3,1): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (3,2): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea"),
    (4,1): Location("Dtessera Sea", "The grey, white-capped swells of the Dtessera Sea crash relentlessly against the western volcanic cliffs.\n"
        "Cold salt spray fills the air.",
        ["Salt Spray", "Floating Kelp"], "Dtessera Sea")

}

parvus_locations = {
    (16, 23): Location(
        "Parvus Rope-Walk & Tarred Net-Quays",
        "Long, salt-bleached timber sheds stretch along the western harbour where hemp-spinners and riggers twist heavy ships' cables.\n"
        "Red-and-black syndicalist flyers flutter from the tar-boilers beside a stack of coiled hawsers.",
        ["Tar-Boilers", "Coiled Hawsers"],
        "Parvus Town"
    ),
    (17, 23): Location(
        "Parvus Harbour-Front & Gantry Crane",
        "The deep-water heart of Parvus Town! Merchant brigantines and customs cutters jostle along the stone mole beneath a towering oak-and-iron **Guild Gantry Crane**.\n"
        "A bronze harbour-bell hangs beside the weigh-house.",
        ["Guild Gantry Crane", "Harbour Bell"],
        "Parvus Town"
    ),
    (18, 23): Location(
        "Kokeshi Bonded Warehouses & Slipway",
        "High, windowless brick customs-sheds dominate the eastern quay, their iron-reinforced double doors guarded by private watchmen.\n"
        "Fresh scrape-marks on the stone slipway show where heavy crates were hauled up from muffled barges after dark.",
        ["Bonded Warehouse Doors", "Stone Slipway"],
        "Parvus Town"
    ),
    (16, 22): Location(
        "Harbourmaster's Customs House & Watch Billet",
        "A stern building of grey ashlar overlooking the western steps, housing both the Parvus Watch billet and the Crown customs registry.\n"
        "Through the leaded casements, clerks stamp wax-sealed billeting warrants and shipping manifests.",
        ["Customs Noticeboard", "Brass Seal-Press"],
        "Parvus Town"
    ),
    (17, 22): Location(
        "Upper Parvus Promenade & Mayoral Balcony",
        "A colonnaded limestone square perched above the harbour tiers, where wealthy ship-owners stroll beneath silk festival banners.\n"
        "In the shadowed alley behind the grand balcony, a heavy **Iron Storm-Drain Grate** is set into the cobbles above the roaring tidal catacombs.",
        ["Mayoral Balcony", "Iron Storm-Drain Grate"],
        "Parvus Town"
    ),
    (18, 22): Location(
        "The Maritime & Artisans' Guildhall",
        "A grand timber-and-copper hall crowned with a gilded astrolabe weather-vane.\n"
        "Master shipwrights, compass-makers, and iron-founders confer on the steps above deep stone vaults that drop into the cliffside.",
        ["Guild Astrolabe", "Vault Fire-Shutters"],
        "Parvus Town"
    ),
    (17, 21): Location(
        "The Salted Anchor Tavern & Sailors' Quarter",
        "A labyrinth of steep, cobbled sailor-lanes smelling of spiced rum, fried sprats, and Stockholm tar.\n"
        "Whale-oil lamps swing outside **The Salted Anchor**, where deckhands, fences, and crimp-agents bargain in low voices.",
        ["Whale-Oil Lantern", "Rigger's Barrel"],
        "Parvus Town"
    ),
    (18, 21): Location(
        "Parvus Dry-Dock & Iron Foundry",
        "The smoky industrial yard of the port, where careened ship hulls are sheathed in copper and blast-furnaces pour pig-iron for naval cannon.\n"
        "Stacks of newly cast hull-plates cool beside the quenching troughs.",
        ["Quenching Trough", "Cast Iron Hull-Plates"],
        "Parvus Town"
    ),
}

fluvius_locations = {
    (9, 3): Location(
        "Fluvius West Canal Bridge",
        "A low-arched bridge of weathered grey ashlar spans the western canal where the river enters Fluvius Town.\n"
        "Iron mooring rings line the towpath, and a battered Watch guard-shelter stands beside the bridgehead.",
        ["Canal Bridge", "Mooring Rings"],
        "Fluvius Town"
    ),
    (10, 2): Location(
        "Fluvius Cobblers' & Chandlers' Row",
        "Narrow timber-framed shops lean over the southern cobblestones, their shutters hung with coiled hemp, tallow candles, and oiled river-boots.\n"
        "Barrels of rainwater and brass fire-buckets sit beneath the eaves.",
        ["Chandler's Sign", "Brass Fire-Buckets"],
        "Fluvius Town"
    ),
    (10, 3): Location(
        "The River Fluvius — Western Stone Bridge",
        "A broad three-arched stone bridge carries the town's main thoroughfare across the rushing current of the River Fluvius.\n"
        "From the parapet, you can look down at the laundry slabs to the north and the moored keelboats along the southern quayside.",
        ["Bridge Parapet", "Iron Lantern-Post"],
        "Fluvius Town"
    ),
    (10, 4): Location(
        "The Laundry Steps & Counting House Balcony",
        "Broad stone steps descend into the canal shallows where washerwomen beat linen against flat scrubbing-slabs.\n"
        "Directly overhead, the carved oak balcony of the Bailiff's Counting House juts out over the water, its leaded casements left ajar to catch the river breeze.",
        ["Scrubbing Slabs", "Overhanging Balcony"],
        "Fluvius Town"
    ),
    (11, 1): Location(
        "Southern Delta Timber-Booms & Net-Sheds",
        "At the southernmost tip of Fluvius Town, heavy chained pine logs float across the channel to catch driftwood before the river meets the delta.\n"
        "Tarred net-sheds and eel-smoking kilns line the shingle bank.",
        ["Chained Timber-Boom", "Smoking Kilns"],
        "Fluvius Town"
    ),
    (11, 2): Location(
        "The River Fluvius — Central Packet Reach",
        "The deep central channel of the River Fluvius cuts straight through the port, spanned by a timber draw-footbridge.\n"
        "Barges laden with grain-sacks and mountain slate jostle for space along the pilings.",
        ["Draw-Footbridge", "Barge Pilings"],
        "Fluvius Town"
    ),
    (11, 3): Location(
        "Fluvius South Quayside",
        "Timber wharves and tarred pilings jut into the main channel of the River Fluvius.\n"
        "On the cobbles opposite the moorings stand two busy establishments: the smoky lantern-lit doorway of **The Barge & Anchor Taproom**, and the blue-shuttered storefront of the **Fluvius Post Office & Packet-Boat Wharf**, where mail-skiffs from Murum tie up.",
        ["Mooring Bollards", "Murum Mail-Skiff"],
        "Fluvius Town"
    ),
    (11, 4): Location(
        "Fluvius Market & Counting House Square",
        "The civic heart of Fluvius Town. Towering over the cobblestones is the **Fluvius Counting House & Tribunal Hall**, its heavy double doors flanked by brass-plated tariff plaques.\n"
        "To the east of the square lies the **Teamsters' Wagon-Yard**, where heavy grain-wains are greased and marshalled before hauling cargo to the barges.",
        ["Tariff Plaques", "Wagon-Yard Gate"],
        "Fluvius Town"
    ),
    (12, 2): Location(
        "Fluvius Civic Clock-Tower & Guildhall Lane",
        "A tall, narrow tower of red brick and dressed stone rises above the eastern lane, its decimal clock-face ticking above the slate roofs.\n"
        "Behind the tower's buttresses lies a shadowed cul-de-sac cluttered with empty theatrical hampers and discarded crates.",
        ["Civic Clock-Tower", "Shadowed Cul-de-Sac"],
        "Fluvius Town"
    ),
    (12, 3): Location(
        "The River Fluvius — Cooperage & Sluice Ford",
        "Where the River Fluvius bends toward the eastern granaries, a stone weir and brass-handled hand-pump draw river water up into the street cisterns.\n"
        "Stacked oak barrel-staves from the town cooperage line the stone embankment.",
        ["Brass Canal-Pump", "Oak Barrel-Staves"],
        "Fluvius Town"
    ),
    (12, 4): Location(
        "The Granary Wharf & Teamsters' Yard",
        "A mud-churned yard behind the towering brick estate granaries. Heavy Percheron draught-teams and hill-mules are tethered inside a locked timber corral.\n"
        "Beside the weigh-beam hangs a dusty **Drover's Chalk Slate** listing the day's wagon movements.",
        ["Drover's Chalk Slate", "Mule Corral"],
        "Fluvius Town"
    ),
    (13, 3): Location(
        "Eastern Bargemen's Row & Salt-Cellars",
        "Low stone warehouses with iron-grated cellar doors store salt, pitch, and pickled herring along the eastern edge of Fluvius Town.\n"
        "Deep wheel-ruts lead from the cellar ramps toward the river slipway.",
        ["Salt-Cellar Doors", "Slipway Ruts"],
        "Fluvius Town"
    ),
    (13, 4): Location(
        "The River Fluvius — Eastern Watergate",
        "A fortified stone watergate arches over the River Fluvius where the current enters the town from the north-eastern woods.\n"
        "Heavy iron chains hang from the winches above the towpath.",
        ["Watergate Arch", "Towpath Winch"],
        "Fluvius Town"
    ),
}

castle_ragmore_locations = {
    (3,22): Location("Castle Ragmore", "The outer courtyard of Castle Ragmore, wherestraw archery butts stand along the curtain wall.", ["Archery Butts"], "Ragmore Castle"),
    (4, 22): Location(
        "Castle Ragmore — Inner Bailey & Great Hall",
        "The grim, towering keep of Castle Ragmore, seat of Castellan Hrothgar.\n"
        "Black-and-gold banners snap above the Great Hall steps, while beside the cellar arch stands a heavy oak **Armoury Rack** stacked with newly delivered ash lances and iron-bound supply chests.",
        ["Castellan's Banner", "Armoury Rack"],
        "Ragmore Castle"
    ),
    (3,23): Location("Castle Ragmore", "The grim, towering keep of Castle Ragmore, seat of Lord Longsword.\n"
        "Black-and-gold banners snap from the battlements above a heavily guarded barbican and inner bailey.",
        ["Castellan's Banner", "Armoury Rack"], "Ragmore Castle"),
    (4,23): Location("Castle Ragmore", "The grim, towering keep of Castle Ragmore, seat of Lord Longsword.\n"
        "Black-and-gold banners snap from the battlements above a heavily guarded barbican and inner bailey.",
        ["Castellan's Banner", "Armoury Rack"], "Ragmore Castle")
}

castle_laydere_locations = {
    (17,9): Location("Castle Laydere", "The training bailey of Castle Laydere, lined with weather-beaten straw archery butts.", ["Archery Butts"], "Laydere Castle"),
    (17,10): Location("Castle Laydere", "The red-stone fortress of Castle Laydere, commanding the eastern river-crossing at the foot of the Caligo Mountains.\n"
        "Soldiers drill in the courtyard while supply wagons rumble through the gatehouse.",
        ["Laydere Banner", "Supply Wagons"], "Laydere Castle"),
    (18,9): Location("Castle Laydere", "The red-stone fortress of Castle Laydere, commanding the eastern river-crossing at the foot of the Caligo Mountains.\n"
        "Soldiers drill in the courtyard while supply wagons rumble through the gatehouse.",
        ["Laydere Banner", "Supply Wagons"], "Laydere Castle"),
    (18,10): Location("Castle Laydere", "The red-stone fortress of Castle Laydere, commanding the eastern river-crossing at the foot of the Caligo Mountains.\n"
        "Soldiers drill in the courtyard while supply wagons rumble through the gatehouse.",
        ["Laydere Banner", "Supply Wagons"], "Laydere Castle")
}

the_old_path_locations = {
    (5,17): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (4,17): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (3,17): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,17): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,16): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,15): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,14): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,13): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,12): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,11): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,10): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (2,9): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (3,12): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (4,12): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (5,12): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (6,12): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (6,11): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (6,10): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (7,9): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (8,8): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (8,7): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (8,6): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path"),
    (9,5): Location("The Old Path", "An ancient, crumbling sunken track winding south-west between the volcanic sea-cliffs and the farmlands.\n"
        "Weathered boundary stones lean in the weeds, marking the old trade route toward the River Fluvius and Fluvius Town.",
        ["Weathered Cairn", "Overgrown Ruts"], "The Old Path")
}

the_new_road_locations = {
    (6,17): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (6,18): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (6,19): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (6,20): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (6,21): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (7,22): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (8,23): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (9,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (10,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (11,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (12,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (13,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (14,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road"),
    (15,24): Location("The New Road", "A wide, cobbled highway stretching north from Murum toward the coastal port of Parvus Town.\n"
        "Deep wagon ruts score the stones, and thick gorse and bracken line the roadside ditches—ideal cover for highwaymen.",
        ["Milestone", "Roadside Brush"], "The New Road")
}

the_heath_locations = {
    (6,8): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,7): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (6,7): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (3,6): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (4,6): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,6): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (6,6): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (2,5): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (3,5): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (4,5): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,5): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (6,5): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (7,5): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (2,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (3,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (4,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (6,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (7,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (8,4): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (3,3): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (4,3): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,3): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (6,3): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (7,3): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (4,2): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,2): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (6,2): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath"),
    (5,1): Location("The Heath", "A vast, desolate expanse of purple heather, prickly gorse, and treacherous peat-bogs.\n"
        "A salt-tangy wind howls inland from the Dtessera Sea, carrying the cries of curlews and the smell of dry brush.",
        ["Dry Gorse", "Heather Tussocks"], "The Heath")

}

the_river_fluvius_locations = {
    (2,6): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (2,7): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (2,8): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (3,7): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (4,7): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (5,8): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (6,9): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (7,8): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (7,7): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (7,6): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (8,5): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (9,4): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (10,3): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (11,2): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (12,3): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,4): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (14,5): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (14,6): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (14,7): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,8): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (12,9): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (12,10): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,11): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,12): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,13): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,14): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,15): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,16): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (12,17): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (11,18): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (10,19): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (10,20): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (11,21): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (12,22): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (13,23): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (14,23): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (15,22): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (16,21): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (16,20): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (16,19): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (17,18): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (18,17): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (19,16): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (19,15): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (18,14): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (17,13): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (17,12): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (17,11): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (16,10): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (16,9): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (17,8): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (18,7): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),
    (19,6): Location("The River Fluvius", "The wide, rushing waters of the River Fluvius surge between reed-choked banks and willow groves.\n"
        "The current runs deep and cold from the northern lakes down to the southern delta.",
        ["Reeds", "Riverbank Willows"], "The River Fluvius"),

}

the_caligo_mountains_locations = {
    (19,9): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (20,9): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (18,8): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (19,8): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (20,8): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (17,7): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (19,7): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (20,7): Location("The Caligo Mountain Range","Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (17,6): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (18,6): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (16,5): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (17,5): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (18,5): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (15,4): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (16,4): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (17,4): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (14,3): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (15,3): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (16,3): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (13,2): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (14,2): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (15, 2): Location(
        "The Caligo Mountain Range — Abandoned Silver Adit",
        "High on the southern slate crags of the Caligo range, a weathered timber mine-head is wedged into a fissure of quartz-veined rock.\n"
        "Rusted iron ore-cart rails disappear into the pitch-black mouth of the deep-delve silver mine.",
        ["Timber Mine-Adit", "Rusted Ore-Rails"],
        "The Caligo Mountains"
    ),
    (16,2): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (12,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (13,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (14,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (15,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (16,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (17,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (18,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (19,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains"),
    (20,1): Location("The Caligo Mountain Range", "Jagged peaks of grey slate and mist-shrouded crags tower above the eastern horizon.\n"
        "Narrow goat-tracks wind between sheer drops, where spiral-horned Mouflin watch from the high ledges.",
        ["Loose Scree", "Limestone Crag"], "The Caligo Mountains")

}

the_lignum_forest_locations = {
    (9,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (10,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (17,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,25): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,24): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (17,24): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,24): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,24): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,24): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (10,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,23): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (8, 22): Location(
        "The Forest — Northern Hunting Ride",
        "A mossy deer-track winds south from the Ragmore pastures beneath the boughs of Lignum Forest.\n"
        "Looking closely at the lower oak branches, you notice notches of pale green lichen and taut, mud-darkened vine-cords stretched ankle-high across the ferns.",
        ["Notched Oak Boughs", "Hidden Vine-Cord"],
        "The Forest"
    ),
    (9,22): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,22): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,22): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,22): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,22): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,22): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (7,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (8,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,21): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (7,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (17,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,20): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (7,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (8,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (17,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,19): Location("The Forest", "In the deepest, darkest heart of Lignum Forest, ancient oak roots arch over a sunken clearing.\n"
            "Broken survey stakes, rusted woodcutters' axes, and woven vine-nets hang from the boughs—this is the stronghold of the Vanguardist defenders fighting back against the townsfolk's encroaching farmlands.", ["Vine-Nets", "Broken Ploughshares"], "The Forest"),
    (20,19): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (7,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (8,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (10,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,18): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,17): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,17): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,17): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,17): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,17): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,16): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,16): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,15): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,15): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,14): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,14): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,14): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,14): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,13): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,13): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,13): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,13): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,13): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,13): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,12): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (18,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,11): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,10): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,10): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,10): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,10): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (19,10): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (20,10): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (8,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (10,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (13,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,9): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (10,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (11,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (12,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,8): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,7): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,7): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,7): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (9,6): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,6): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (16,6): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (15,5): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    (14,4): Location("The Forest", "Towering, ancient trees blot out the sky above you, plunging the forest floor into a shifting green twilight.\n"
            "Every gnarled trunk, moss-draped root, and fern-choked hollow looks eerily identical.", ["Ancient Trees"], "The Forest"),
    
}


cliff_edge_coordinates = [
    (1,25), (1,24), (1,23), (1,22), (1,21), (1,20), (1,19),
    (1,18), (1,17), (1,16), (1,15), (1,14), (1,13), (1,12),
    (1,11), (1,10)
]

wall_coordinates = [
    (6,13), (6,14), (6,15), (6,16), (7,17), (8,17), (9,17), 
    (10,17), (11,17), (11,16), (12,16), (12,15), (12,14), 
    (12,13), (11,13), (11,12), (10,12), (9,12), (8,12), (7,12), (7,13)
]

# --- MASTER WORLD MAP ---
world_map = {}
world_map.update(murum_town_locations)
world_map.update(parvus_locations)
world_map.update(castle_ragmore_locations)
world_map.update(ragmore_lake_locations)
world_map.update(ragmore_plains_locations)
world_map.update(castle_laydere_locations)
world_map.update(the_new_road_locations)
world_map.update(the_old_path_locations)
world_map.update(the_river_fluvius_locations)
world_map.update(fluvius_locations)
world_map.update(calluna_lake_locations)
world_map.update(diluvium_lake_locations)
world_map.update(dtessera_sea_locations)
world_map.update(the_mountain_lake_locations)
world_map.update(old_path_plains_locations)
world_map.update(the_diluvium_glade_locations)
world_map.update(the_lignum_forest_glade_locations)
world_map.update(ragmore_farm_locations)
world_map.update(murum_farm_locations)
world_map.update(fluvius_farm_locations)
world_map.update(the_caligo_mountains_locations)
world_map.update(the_lignum_forest_locations)
world_map.update(the_heath_locations)

# --- CHAPTER 2 LANDMARKS & TRIAL SITES ---
ch2_landmark_locations = {
    (6, 17): Location("The New Road — Outside Murum Gate",
        "Just north of Murum's oak gates, the cobbled New Road begins its long climb across the Ragmore Plains.\n"
        "Travellers tighten their packs and check their blades here before venturing into the wilds.",
        ["Roadside Milestone"], "The New Road"),
    (5, 17): Location("The Old Path — Western Turnoff",
        "A weathered signpost marks where the Old Path branches west from the New Road, skirting the farmlands toward the sea-cliffs.",
        ["Weathered Signpost"], "The Old Path"),
    (6, 21): Location("New Road — Frontier Watchpost",
        "A timber palisade and watchtower straddle the New Road where the track forks toward Castle Ragmore and Parvus Town.\n"
        "A brazier burns beside the toll-bar.",
        ["Watchpost Brazier", "Duty Roster"], "The New Road"),
    (7, 22): Location("The New Road — Muddy Hollow",
        "The highway dips through a waterlogged hollow where deep, jagged ruts have claimed many a wagon axle.",
        ["Deep Wagon Ruts"], "The New Road"),
    (8, 10): Location("Murum Farmland — Picket Crossroads",
        "At the main crossroads of the Murum Farmlands, striking farmhands have chained heavy hay-wains across the track.\n"
        "A red Union banner flutters from a pitchfork planted in the turf.",
        ["Chained Hay-Wains", "Strike Banner"], "Murum Farm"),
    (11, 6): Location("Fluvius Farmland — The Southern Barricade",
        "Outside the approaches to Fluvius Town, agrarian workers have formed a picket line across the farm road, demanding fair grain tariffs.",
        ["Farm Barricade", "Brazier"], "Fluvius Farm"),
    (12, 6): Location("Fluvius Farmland — Eel-Fisher's Weir",
        "Wicker eel-traps and willow nets are staked along the sluggish river-ditch beside the farmlands.\n"
        "From this bank, one has a clear view of the east-bank waterwheel across the channel.",
        ["Wicker Eel-Traps", "Reed Boat"], "Fluvius Farm"),
    (13, 7): Location("Fluvius Farmland — East-Bank Mill Holding",
        "A stone tenant cottage stands beside a shattered timber waterwheel on the eastern edge of the Fluvius Farmlands.\n"
        "Fresh splinters and raw chisel-gouges mark the broken paddles.",
        ["Shattered Waterwheel", "Orchard Rows"], "Fluvius Farm"),
    (6, 11): Location("The Old Path — Sunken Rut",
        "The Old Path narrows between high earth banks, its cobbles cracked and sunken from winter floods.",
        ["Cracked Cobbles"], "The Old Path"),
    (3, 12): Location("The Old Path — Ruined Waystation",
        "The ivy-choked shell of an old drovers' waystation stands beside the bend in the Old Path.\n"
        "Fresh chalk marks on the lintel suggest the Kokeshi couriers still use this ruin as a dead-drop.",
        ["Chalk-Marked Lintel", "Stone Trough"], "The Old Path"),
    (2, 14): Location("The Old Path — Cliffside Defile",
        "The Old Path squeezes through a narrow defile between sheer volcanic rock and a deep, bramble-choked ditch.",
        ["Overturned Merchant Cart", "Thorny Ditch"], "The Old Path"),
    (11, 24): Location("The New Road — Northern Bottleneck",
        "The northern highway narrows between two steep gravel embankments on the approach to Parvus.",
        ["Stalled Merchant Wain", "Gravel Bank"], "The New Road"),
    (6, 9): Location("The Old Path — Rickety Rope-Bridge",
        "A swaying suspension bridge of weathered hemp and rotted oak planks spans the churning gorge of the River Fluvius.\n"
        "A painted warning board creaks in the wind: 'MAX LOAD 15 LBS — NO MOUNTS'.",
        ["Warning Sign", "Riverbank Cache"], "The Old Path"),
    (12, 17): Location("Eastern River Crossing — Rickety Footbridge",
        "An ancient timber footbridge arches across the white-water rapids of the River Fluvius between the New Road and Lignum Forest.\n"
        "Several cross-planks are missing, and a carved post warns: 'MAX LOAD 15 LBS'.",
        ["Warning Post", "Riverbank Cache"], "The New Road"),
    (6, 12): Location("The Old Path — Castellan's Toll-Gate",
        "A weathered stone archway with a heavy iron portcullis bars the Old Path where it descends toward the southern plains.\n"
        "Beside the arch stands an abandoned stone gatehouse, its door hanging ajar.",
        ["Iron Portcullis", "Abandoned Gatehouse"], "The Old Path"),
    (15, 4): Location("Caligo Pass — The Mountain Gatehouse",
        "Set into a cleft of the Caligo Mountains stands an ancient fortified toll-gate, its iron portcullis rusted shut.",
        ["Rusted Portcullis", "Stone Watch-Cell"], "The Caligo Mountains"),
    (5, 5): Location("The Heath — Burning Gorse-Hollow",
        "Dry gorse bushes crackle with spreading wildfire across the peat-heath, sending billows of acrid black smoke rolling downwind!",
        ["Burning Gorse", "Shepherd's Fold"], "The Heath"),
    (4, 4): Location("The Heath — Smoke-Choked Ridge",
        "Cinders and thick grey smoke drift across the heather from a brushfire burning in the gorse-hollows.",
        ["Smouldering Heather"], "The Heath"),
    (9, 5): Location("The Old Path — Flooded Levee Bend",
        "Torrential runoff from the mountains has breached the earthen embankment of the River Fluvius!\n"
        "Churning, waist-deep floodwater pours across the road toward the lower farmlands.",
        ["Breached Levee", "Pile of Sandbags"], "The Old Path"),
    (12, 7): Location("Fluvius Farmland — Burst Riverbank",
        "The eastern levee has given way under the swollen River Fluvius, submerging the farm track in icy, swirling water.",
        ["Flooded Sluice", "Timber Stakes"], "Fluvius Farm"),
    (4, 24): Location("Ragmore Lake — Sunken Ruin Shallows",
        "A crumbling stone jetty juts into the cold, clear waters of Ragmore Lake.\n"
        "Twenty feet below the surface, the glint of an iron-bound chest is visible wedged among drowned pillars.",
        ["Diving Jetty", "Submerged Strongbox"], "Ragmore Lake"),
    (9, 20): Location("Lake Diluvium — Woodland Diving Cove",
        "A quiet cove on the edge of Lake Diluvium where an old cedar raft is moored.\n"
        "Through the crystal-clear water, you can see a sunken strongbox tangled in drowned oak roots.",
        ["Cedar Raft", "Sunken Strongbox"], "Diluvium Lake"),
    (8, 2): Location("Lake Calluna — Reed-Ringed Shallows",
        "A flat-bottomed punt rests in the reeds at the edge of Lake Calluna, directly above a submerged strongbox glinting on the lakebed.",
        ["Mooring Post", "Submerged Chest"], "The Heath"),
    (18, 3): Location("The Mountain Lake — Glacial Diving Ledge",
        "A flat quartz ledge overhangs the deep emerald basin of the Mountain Lake.\n"
        "Far below the icy surface, a brass-bound strongbox gleams between two boulders.",
        ["Quartz Ledge", "Glacial Depths"], "The Mountain Lake"),
    (18, 5): Location("Caligo Peak — The Cloud-Observatory",
        "High above the mist-line of the Caligo Mountains stands a weathered stone rotunda crowned with a brass armillary sphere.\n"
        "Incense smoke curls from the doorway where Master Spotted Tail, the Sage of the Mountains, contemplates the stars.",
        ["Brass Armillary Sphere", "Observatory Brazier"], "The Caligo Mountains"),
    (16, 5): Location("Caligo Pass — The Mouflin Ledge",
        "A narrow limestone ledge winds up into the Caligo Mountains.\n"
        "A herd of wild, spiral-horned Mouflin stands across the trail, led by a massive Alpha Ram!",
        ["Limestone Ledge", "Mountain Lichen"], "The Caligo Mountains"),
    (10, 20): Location("River Fluvius — Northern Trader Landing",
        "A timber landing stage juts into the River Fluvius where flat-bottomed keelboats moor between Parvus and the forest.",
        ["Mooring Bollard", "Trade Crates"], "Diluvium Glade"),
    (13, 13): Location("River Fluvius — Mid-River Ferry Quay",
        "A busy river-landing between Murum's eastern woods and the southern farmlands where Skipper Ceara's keelboat is tied up.",
        ["Keelboat Gangplank", "Coiled Hawser"], "The Forest"),
    (7, 7): Location("River Fluvius — Southern Heath Quay",
        "A stone jetty on the lower River Fluvius where river-traders load peat, wool, and grain bound for Fluvius Town.",
        ["Loading Crane", "Barge Bell"], "The Heath"),
    (13, 16): Location("River Fluvius — The Washed-Out Gorge",
        "The old stone bridge between Murum's eastern woods and the Lignum Glade has collapsed into the gorge!\n"
        "Sturdy pine trees grow along the bank beside the intact stone piers.",
        ["Collapsed Bridge Piers", "Tall Pine Trunks"], "The Forest"),
    (16, 10): Location("Laydere Approach — The Collapsed Span",
        "Just west of Castle Laydere, the river-gorge bridge has been swept away by floodwaters, leaving a 15-foot gap between the abutments.",
        ["Stone Abutments", "Felled Timber"], "The Forest"),
    (4, 12): Location("The Old Path — Rockslide Pass",
        "A massive rockslide of loose shale and a wedged keystone boulder completely buries the Old Path!\n"
        "Muddy water pools behind a clogged lower drainage culvert at the base of the slide.",
        ["Keystone Boulder", "Clogged Culvert", "Loose Shale"], "The Old Path"),
    (16, 4): Location("Caligo Foothills — Shale Rockslide",
        "Tons of fallen mountain slate and a precarious central boulder block the pass between Fluvius and the Caligo peaks.",
        ["Precarious Boulder", "Blocked Culvert"], "The Caligo Mountains"),
    (2, 11): Location("The Old Path — Sea-Smugglers' Cove",
        "A hidden shingle cove below the western cliffs where muffled oars and lantern-flashes signal a nocturnal smuggling landing.",
        ["Smugglers' Skiff", "Brandy Casks"], "The Old Path"),
    (15, 22): Location("River Fluvius — Smugglers' Reeds",
        "In a mist-shrouded backwater south of Parvus, hooded figures are unloading unstamped crates from a river-barge.",
        ["Muffled Barge", "Unstamped Crates"], "The New Road"),
}
world_map.update(ch2_landmark_locations)

for _coord in set(fluvius_locations) & set(the_river_fluvius_locations):
    _fl_loc = fluvius_locations[_coord]
    if _fl_loc.description != "X":
        world_map[_coord] = Location(
            _fl_loc.name if "River" in _fl_loc.name else f"The River Fluvius — {_fl_loc.name}",
            _fl_loc.description,
            _fl_loc.objects,
            "Fluvius Town"
        )
    else:
        world_map[_coord] = Location(
            "The River Fluvius",
            "The wide, rushing waters of the River Fluvius cut straight through the heart of Fluvius Town, spanned by bustling stone bridges and quaysides.",
            ["River Quay"],
            "Fluvius Town"
        )

for x, y in cliff_edge_coordinates:
    if (x, y) not in world_map:
        world_map[(x, y)] = Location(
            "The Cliff Edge",
            "You stand on the edge of the volcanic cliffs of Dtessera, looking out on an endless sea.",
            ["Volcanic Basalt"], "Dtessera Coast"
        )
            
for x, y in wall_coordinates:
    # This checks if a building already exists here before placing a wall
    if (x, y) not in world_map:
        world_map[(x, y)] = Location(
            "The Town Wall",
            "A towering stone wall ringing the town of Murum. The stone is cold and roughly hewn, moss grows freely in the gaps.",
            ["Ramparts", "Stones"], "Murum Town Wall"
        )

# =========================================================================
# 3. TOPOGRAPHIC ALTITUDE & HYDROLOGICAL DRAINAGE MAP (TIERS 0 TO 5)
# =========================================================================
ALTITUDE_TIER_METERS = {0: 0, 1: 5, 2: 20, 3: 60, 4: 180, 5: 450}
ALTITUDE_TIER_LABELS = {
    0: "Tier 0 — Water Level (0m)",
    1: "Tier 1 — Sunken Hollow / Flood-Basin (5m)",
    2: "Tier 2 — Lowland Floodplain (20m)",
    3: "Tier 3 — Upland Ridge / High Ground (60m)",
    4: "Tier 4 — Crag & Cliff Tableland (180m)",
    5: "Tier 5 — High Alpine Peak (450m)",
}

# Default base altitude tier by region
REGION_BASE_ALTITUDE = {
    "Dtessera Sea": 0,
    "The River Fluvius": 0,
    "Ragmore Lake": 0,
    "Diluvium Lake": 0,
    "Calluna Lake": 0,
    "The Mountain Lake": 5,       # High glacial tarn at 450m!
    "The Heath": 2,               # Lowland peat-heath (20m)
    "Old Path Plains": 2,         # Lowland coastal meadow (20m)
    "Fluvius Farm": 2,            # Alluvial delta floodplain (20m)
    "Fluvius Town": 2,            # Quayside & lower port (20m)
    "Parvus Town": 2,             # Harbour tiers (20m, Upper Parvus overridden to 3)
    "The Old Path": 2,            # Sunken coastal track (with Tier 1 hollows & Tier 3 cliff-ledges)
    "The New Road": 3,            # Built on a cambered upland causeway (60m, except Muddy Hollow!)
    "Murum Farm": 3,              # Hill-slope strip-farms above the flood-line (60m)
    "Ragmore Farm": 3,            # Upland barley holdings (60m)
    "Murum Town": 3,              # Walled hilltop town (60m)
    "Murum Town Wall": 4,         # High stone ramparts (180m)
    "Plains": 3,                  # Ragmore upland pastures (60m)
    "The Forest": 3,              # Lignum Forest canopy ridge (60m)
    "Lignum Glade": 3,
    "Diluvium Glade": 2,          # Sunken woodland basin around Lake Diluvium (20m)
    "Ragmore Castle": 4,          # Keep crag (180m)
    "Laydere Castle": 4,          # Red-stone mountain foot-fortress (180m)
    "Dtessera Coast": 4,          # Volcanic sea-cliffs (180m)
    "The Caligo Mountains": 5,    # Alpine slate peaks (450m, foothills overridden to 4)
}

# Specific Coordinate Overrides: Sunken Flood-Traps (Tier 1) vs. High-Ground Bypasses (Tier 3/4)
COORD_ALTITUDE_OVERRIDES = {
    # --- TIER 1: SUNKEN FLOOD-BASINS & HOLLOWS (First to flood when rains persist!) ---
    (10, 5): 1,  # The Sunken Sluice-Gate Lane (Fluvius Farm approach)
    (11, 5): 1,  # Lower Fluvius ditch south of the Crossroads
    (12, 5): 1,  # Lower delta marsh-paddock
    (12, 6): 1,  # Southern River Reeds & Eel-Weirs
    (12, 7): 1,  # Fluvius Farmland — Burst Riverbank
    (9, 5):  1,  # The Old Path — Flooded Levee Bend
    (8, 6):  1,  # The Old Path — Low River-Skirt
    (6, 11): 1,  # The Old Path — Sunken Rut
    (7, 22): 1,  # The New Road — Muddy Hollow (Flood-trap on the northern highway!)
    (5, 5):  1,  # The Heath — Burning/Peat Gorse-Hollow
    (6, 4):  1,  # The Heath — Low Peat-Bog

    # --- TIER 3: HIGH-GROUND BYPASS RIDGES & STONE BRIDGES (Stay dry during floods!) ---
    (10, 6): 3,  # Western Cider Orchards ("western river-terrace" — High-ground bypass around (10,5)!)
    (10, 7): 3,  # Upper Orchard Ridge (High-ground link to Murum Farmlands!)
    (11, 7): 3,  # North-Central Farm Ridge (High-ground approach to the Crossroads!)
    (9, 3):  3,  # Fluvius West Canal Bridge (Arched stone bridge above the flood!)
    (10, 3): 3,  # The River Fluvius — Western Stone Bridge (High three-arched bridge!)
    (11, 4): 3,  # Fluvius Market & Counting House Square (Built on the upper cobble rise)
    (12, 2): 3,  # Fluvius Civic Clock-Tower (High eastern lane)
    (6, 22): 3,  # Ragmore Plains Eastern Shoulder (High-ground bypass around (7,22) Muddy Hollow!)
    (5, 11): 3,  # Old Path Plains High Meadow (High-ground bypass around (6,11) Sunken Rut!)
    (4, 5):  3,  # The Heath — High Gorse-Ridge (Dry ridge path across the southern Heath!)
    (4, 4):  3,  # The Heath — Smoke-Choked Ridge
    (7, 5):  3,  # The Heath — Eastern Limestone Rise
    (2, 14): 3,  # The Old Path — Cliffside Defile (High above sea level)
    (2, 15): 3,
    (2, 16): 3,
    (17, 22): 3, # Upper Parvus Promenade & Mayoral Balcony (Cliff-top tier!)
    (18, 22): 3, # The Maritime & Artisans' Guildhall (Upper cliffside tier)

    # --- TIER 4: FOOTHILLS OF CALIGO (Transition zone before the 450m Alpine Peaks) ---
    (13, 2): 4, (14, 2): 4, (14, 3): 4, (15, 3): 4, (15, 4): 4, (16, 4): 4, (12, 1): 4, (13, 1): 4,
}

for _coord, _loc in world_map.items():
    if _loc.altitude is None:
        if _coord in COORD_ALTITUDE_OVERRIDES:
            _loc.altitude = COORD_ALTITUDE_OVERRIDES[_coord]
        else:
            _loc.altitude = REGION_BASE_ALTITUDE.get(_loc.region, 2)
    _loc.elevation_m = ALTITUDE_TIER_METERS.get(_loc.altitude, 20)
