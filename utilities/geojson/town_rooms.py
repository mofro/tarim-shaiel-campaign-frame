"""
Suggested rooms per building type for the town inspector (#406).

FTG's export has no interiors, so these are the GM's starting points, not data: a plain
room list per kind of building, shown labelled as a suggestion. Types not listed are
taken to be a craft workshop, which is what most of the unlisted ones are.
"""

KINDS = {
    "home": ["Main room with the hearth", "Sleeping room", "Store cupboard or cellar", "Yard"],
    "rich home": ["Hall", "Kitchen", "Parlour", "Master bedroom", "Children's rooms",
                  "Servants' quarters", "Strongroom", "Courtyard"],
    "workshop": ["Shopfront", "Work floor", "Raw-material store", "Finished-goods rack",
                 "Living rooms above"],
    "shop": ["Sales floor", "Counter", "Back store", "Living rooms above"],
    "warehouse": ["Loading bay", "Main floor", "Tally office", "Loft", "Watchman's corner"],
    "drinking house": ["Taproom", "Kitchen", "Cellar", "Back room", "Keeper's rooms above"],
    "inn": ["Common room", "Kitchen", "Cellar", "Guest rooms", "Stable and yard", "Keeper's rooms"],
    "caravanserai": ["Gate and porter's lodge", "Courtyard", "Animal stalls", "Sleeping alcoves",
                     "Storerooms", "Well or cistern", "Keeper's room"],
    "barracks": ["Barrack hall", "Armoury", "Mess", "Officers' room", "Stores", "Drill yard"],
    "temple": ["Prayer hall", "Washing court", "Cleric's cells", "Store", "Garden or courtyard"],
    "school": ["Teaching room", "Teacher's room", "Store", "Yard"],
    "vice house": ["Front room", "Private rooms", "Kitchen", "Cellar", "Keeper's office"],
    "bathhouse": ["Changing room", "Hot room", "Cold plunge", "Steam room", "Furnace room", "Attendants' room"],
    "office": ["Waiting room", "Clerks' room", "Principal's office", "Archive", "Strongroom"],
}

KIND_OF = {}
for _kind, _types in {
    "home": ["middle class home", "lower class home", "house share", "abandoned squat"],
    "rich home": ["upper class home"],
    "warehouse": ["general warehouse", "specific warehouse", "log shop", "stone shop", "stock"],
    "drinking house": ["tavern", "upper class tavern", "quiet bar", "raucous dive", "bar", "brewery",
                       "distillery", "winemaker"],
    "inn": ["small inn", "medium inn", "large inn", "inn"],
    "caravanserai": ["caravanserai"],
    "barracks": ["barracks", "mercenary company", "armory"],
    "temple": ["temple"],
    "school": ["school"],
    "vice house": ["brothel", "gambling den", "casino", "gang hangout", "secret society"],
    "bathhouse": ["bathhouse"],
    "office": ["bank", "notary", "feudal office", "keep", "community hall", "scribe", "money lender"],
    "shop": ["general store", "fiber shop", "butcher", "grain shop", "greengrocer", "fish merchant",
             "game trader", "herbalist", "medicine shop", "apothecary", "used clothes dealer",
             "pastry shop", "cheesemonger", "outfitter", "bookshop", "jewellery shop", "clothes shop",
             "wax shop", "farmers market", "market square", "art dealer", "ore trader", "woodmonger",
             "mercer", "baker", "perfumer"],
}.items():
    for _t in _types:
        KIND_OF[_t] = _kind


def rooms(building_type) -> dict | None:
    """{"kind": label, "rooms": [...]} for a building type, or None when there is no type."""
    if not building_type:
        return None
    kind = KIND_OF.get(building_type, "workshop")
    return {"kind": kind, "rooms": list(KINDS[kind])}
