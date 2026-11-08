"""
Daggerheart Difficulty and fight stats for town people (#409).

GM-only and generated: nothing here is written to the vault or to the derived files. The town
inspector calls `stats(person)` for each person and shows the result as a starting point the
GM adjusts at the table. The job title picks an adversary role, the ancestry picks the tier,
and the person's best relevant ability and place in the life nudge Difficulty and attack.

Every number lives in the tables below, so a ruling changes in one place.
"""

try:
    from geojson import settlement_profiles as sp
except ImportError:  # run with utilities/geojson itself on the path, as the tests do
    import settlement_profiles as sp

# Tier 1 rows: (Difficulty, HP, Stress, Major threshold, Severe threshold, attack bonus).
# A Minion has 1 HP and no thresholds: any damage that reaches it takes it out.
ROLES = {
    "Minion": (9, 1, 1, None, None, 0),
    "Social": (10, 3, 3, 4, 8, 0),
    "Standard": (12, 5, 3, 6, 11, 2),
    "Bruiser": (13, 7, 3, 8, 14, 3),
    "Leader": (14, 7, 5, 8, 15, 3),
}
ROLE_ORDER = list(ROLES)

# What moving up a tier adds: Difficulty, HP, Stress, both thresholds, attack.
TIER_STEP = {"difficulty": 3, "hp": 2, "stress": 1, "major": 5, "severe": 10, "attack": 1}

# Ancestries that start above Tier 1 (the GM's call: see the issue's open question).
TIER_OF_ANCESTRY = {"Div-Born": 2, "Tadbir": 2}

ABILITIES = {"Minion": ("constitution",), "Social": ("intelligence", "wisdom", "charisma"),
             "Standard": ("strength", "dexterity"), "Bruiser": ("strength", "constitution"),
             "Leader": ("strength", "intelligence", "charisma")}
STRONG, WEAK = 14, 6  # best ability at or above / at or below these moves Difficulty by one
BRUISER_STRENGTH = 14  # a Standard fighter this strong is a Bruiser

# Place in the life, as a share of the ancestry's lifespan.
CHILD_BELOW, ELDER_ABOVE = 0.15, 0.8
AGE_NUDGE = {"child": -2, "prime": 0, "elder": -1}
DIFFICULTY_FLOOR, DIFFICULTY_CEIL_NUDGE = 5, 1

# job title -> (role, weapon, damage die, tier). Apprentices take their master's row.
FIST = ("Fists", "1d4")
KNIFE = ("Knife", "1d6")
SPEAR = ("Spear", "1d8+1")
HAMMER = ("Smith's hammer", "1d8")
CLEAVER = ("Cleaver", "1d8")
STAFF = ("Staff", "1d6")
TOOL = ("Tool in hand", "1d4")
JOBS = {
    # No trade, or service work
    "": ("Minion", FIST, 1), "Labourer": ("Minion", TOOL, 1), "Stay at home parent": ("Minion", FIST, 1),
    "Shop assistant": ("Minion", FIST, 1), "Prostitute": ("Minion", KNIFE, 1),
    "Bartender": ("Minion", FIST, 1), "Server": ("Minion", FIST, 1), "Chamber maid": ("Minion", FIST, 1),
    "Servant": ("Minion", FIST, 1), "Stable-hand": ("Minion", TOOL, 1), "Porter": ("Minion", FIST, 1),
    "Messenger": ("Minion", KNIFE, 1), "Bath-tender": ("Minion", FIST, 1), "Launderer": ("Minion", FIST, 1),
    "Receptionist": ("Minion", FIST, 1), "Farmer": ("Minion", ("Sickle", "1d6"), 1),
    "Nanny": ("Minion", FIST, 1), "Cook": ("Minion", ("Cleaver", "1d8"), 1), "Stock": ("Minion", FIST, 1), "Undertaker": ("Minion", ("Spade", "1d6"), 1),
    # Armed
    "Guard": ("Standard", SPEAR, 1), "Settlement guardsman": ("Standard", SPEAR, 1),
    "Gang member": ("Bruiser", KNIFE, 1), "Gang boss": ("Leader", KNIFE, 1),
    "Caravanserai Warden": ("Leader", ("Short sword", "1d8+1"), 1),
    # Heavy trades
    "Blacksmith": ("Minion", HAMMER, 1), "Butcher": ("Minion", CLEAVER, 1),
    "Stone-cutter": ("Minion", HAMMER, 1), "Mason": ("Minion", HAMMER, 1),
    "Carpenter": ("Minion", ("Hatchet", "1d6"), 1), "Builder": ("Minion", HAMMER, 1),
    "Nail-smith": ("Minion", HAMMER, 1), "Locksmith": ("Minion", TOOL, 1),
    # Trade, face to face
    "Merchant": ("Social", KNIFE, 1), "Tavern Owner": ("Social", ("Cudgel", "1d6"), 1),
    "Bathhouse Owner": ("Social", FIST, 1), "Dealer": ("Social", KNIFE, 1), "Banker": ("Social", FIST, 1),
    "Money lender": ("Social", KNIFE, 1), "Notary": ("Social", FIST, 1), "Scribe": ("Social", FIST, 1),
    "Teacher": ("Social", STAFF, 1), "Head Teacher": ("Social", STAFF, 1), "Cleric": ("Social", STAFF, 1),
    "Priest": ("Social", STAFF, 2), "Advisor": ("Social", FIST, 2), "Seer": ("Social", STAFF, 2),
    "Doctor": ("Social", KNIFE, 1), "Alchemist": ("Social", KNIFE, 1), "Herbalist": ("Social", KNIFE, 1),
    "Apothecary": ("Social", KNIFE, 1), "Artificer": ("Social", TOOL, 1), "Architect": ("Social", STAFF, 1),
    "Cartographer": ("Social", FIST, 1), "Outfitter": ("Social", KNIFE, 1), "Bard": ("Social", KNIFE, 1),
    "Singer": ("Social", FIST, 1), "Harper": ("Social", FIST, 1), "Fiddler": ("Social", FIST, 1),
    "Illustrator": ("Social", FIST, 1), "Painter": ("Social", FIST, 1), "Tattoo artist": ("Social", KNIFE, 1),
    "Barber": ("Social", ("Razor", "1d4"), 1), "Jeweler": ("Social", KNIFE, 1),
    "Silversmith": ("Social", KNIFE, 1), "Engraver": ("Social", KNIFE, 1), "Perfumer": ("Social", FIST, 1),
    "Distiller": ("Social", FIST, 1), "Winemaker": ("Social", FIST, 1), "Brewer": ("Social", FIST, 1),
    # Other crafts: tools, not weapons
    "Tanner": ("Minion", KNIFE, 1), "Weaver": ("Minion", TOOL, 1), "Tailor": ("Minion", TOOL, 1),
    "Cobbler": ("Minion", TOOL, 1), "Shoemaker": ("Minion", TOOL, 1), "Furrier": ("Minion", KNIFE, 1),
    "Carder": ("Minion", TOOL, 1), "Roofer": ("Minion", TOOL, 1), "Thatcher": ("Minion", TOOL, 1),
    "House Painter": ("Minion", TOOL, 1), "Plasterer": ("Minion", TOOL, 1),
    "Leather armourer": ("Minion", KNIFE, 1), "Miller": ("Minion", TOOL, 1), "Cheesemaker": ("Minion", TOOL, 1),
    "Basket-maker": ("Minion", TOOL, 1), "Potter": ("Minion", TOOL, 1), "Lanternmaker": ("Minion", TOOL, 1),
    "Glassblower": ("Minion", TOOL, 1), "Purse maker": ("Minion", KNIFE, 1), "Wickerworker": ("Minion", TOOL, 1),
    "Glovemaker": ("Minion", TOOL, 1), "Chandler": ("Minion", TOOL, 1), "Baker": ("Minion", TOOL, 1),
    "Ropemaker": ("Minion", TOOL, 1), "Soap-maker": ("Minion", TOOL, 1), "Saddle maker": ("Minion", KNIFE, 1),
    "Parchment maker": ("Minion", KNIFE, 1), "Cabinet-maker": ("Minion", TOOL, 1),
    "Ink Maker": ("Minion", TOOL, 1), "Bookbinder": ("Minion", KNIFE, 1), "Paper maker": ("Minion", TOOL, 1),
    "Belt maker": ("Minion", KNIFE, 1), "Pewterer": ("Minion", HAMMER, 1), "Sculptor": ("Minion", HAMMER, 1),
}
APPRENTICE = "'s apprentice"
DEFAULT_JOB = ("Minion", FIST, 1)


def job_row(title) -> tuple[tuple, bool]:
    """(row, is_apprentice) for a job title; unknown titles fall back to an unarmed Minion."""
    title = title or ""
    apprentice = title.endswith(APPRENTICE)
    if apprentice:
        title = title[:-len(APPRENTICE)]
    return JOBS.get(title, DEFAULT_JOB), apprentice


def life_stage(age, race) -> str:
    """child, prime or elder, by the person's age against the ancestry's lifespan."""
    if age is None or race == "Tadbir":
        return "prime"
    share = age / sp.LIFESPAN.get(race, 100)
    return "child" if share < CHILD_BELOW else "elder" if share > ELDER_ABOVE else "prime"


def stats(person) -> dict:
    """Difficulty and fight stats for one person record (a town inspector `people` entry)."""
    (role, (weapon, die), tier), apprentice = job_row(person.get("job"))
    tier = max(tier, TIER_OF_ANCESTRY.get(person.get("race"), 1))
    ab = person.get("stats") or {}
    if role == "Standard" and ab.get("strength", 0) >= BRUISER_STRENGTH:
        role = "Bruiser"
    best = max((ab.get(k, 10) for k in ABILITIES[role]), default=10)
    by_ability = 1 if best >= STRONG else -1 if best <= WEAK else 0
    stage = life_stage(person.get("age"), person.get("race"))
    nudge = min(DIFFICULTY_CEIL_NUDGE, by_ability + AGE_NUDGE[stage] - (1 if apprentice else 0))
    difficulty, hp, stress, major, severe, attack = ROLES[role]
    up = tier - 1
    difficulty = max(DIFFICULTY_FLOOR, difficulty + up * TIER_STEP["difficulty"] + nudge)
    if role != "Minion":
        hp += up * TIER_STEP["hp"] - (1 if stage != "prime" else 0)
        major += up * TIER_STEP["major"]
        severe += up * TIER_STEP["severe"]
    stress += up * TIER_STEP["stress"]
    attack += up * TIER_STEP["attack"] + (0 if stage == "child" else by_ability)
    return {"role": role, "tier": tier, "difficulty": difficulty, "hp": hp, "stress": stress,
            "thresholds": [major, severe] if major is not None else None, "attack": attack,
            "weapon": weapon, "damage": die, "stage": stage}
