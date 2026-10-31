"""
Single source of truth for Tarim-Shaiel location Types.

TYPES is the one table. The parser, the Type dropdowns, the icon expressions, the
tier filters and the Display toggles all read it, so they cannot disagree about
what a Type is or how it is drawn (#336).

Where two surfaces disagree about a Type, the disagreement is a cell in this table,
not an exception in code, so fixing it edits one cell. `tests/fixtures/type_pins.json`
records what every Type draws on every surface; a change here regenerates it, and its
diff is the change's before-and-after pin list.

Columns
-------
slug       the value of a page's `type:`; the only column every row has
parses_as  what the location parser makes of that `type:` (or `mapmarker:`) value.
           None = the parser does not recognise it and falls through to the page's
           `content_type:`, then tags, then "poi"
map_tier   which Workshop / player-map tier draws it (MAP_TIERS); None = not drawn
map_icon   the icon the Workshop and player map draw; None = the default icon
page_tier  which world-page / mini-map tier draws it (PAGE_TIERS); None = not drawn
page_icon  the icon the world page and the GM layers draw
mini_icon  the icon the mini-maps on location pages draw
toggle     the Display checkbox label; None = no checkbox, always drawn
listed     False = a legacy spelling that is tolerated and drawn as before but not
           offered in any dropdown

Exports
-------
Type, TYPES        the row type and the table
MAP_TIERS, PAGE_TIERS   the tier names a row may use, in layer (z) order
CATEGORIES         the listed slugs in dropdown order
VALID_CATEGORIES   frozenset of CATEGORIES, for membership checks and CLI validation
ICON_MAP           {slug: page_icon}, the world page's icon arms
DEFAULT_ICON       the icon a Type with no arm is drawn with
tier_members()     the slugs in one tier of one surface, in row order
icon_arms()        (slug, icon) pairs for one surface's icon match
"""

from typing import NamedTuple


class Type(NamedTuple):
    slug: str
    parses_as: str | None = None
    map_tier: str | None = None
    map_icon: str | None = None
    page_tier: str | None = None
    page_icon: str | None = None
    mini_icon: str | None = None
    toggle: str | None = None
    listed: bool = True


# Layer order is draw order: later tiers sit above earlier ones.
MAP_TIERS = ("major", "towns", "secondary", "spiritual", "routes", "detail")
PAGE_TIERS = ("major", "towns", "secondary", "routes", "detail")

# Row order is the order of the Type dropdowns and of the Display checkboxes. The
# legacy rows come last and are the only rows with listed=False.
TYPES: tuple[Type, ...] = (
    #    slug             parses_as      map_tier     map_icon           page_tier    page_icon          mini_icon          toggle
    # Major locations
    Type("city",          "city",        "major",     "cat-city",        "major",     "cat-city",        "cat-city",        "Cities"),
    Type("capital",       "capital",     "major",     "cat-capital",     "major",     "cat-capital",     "cat-capital",     "Capitals"),
    Type("bridge",        "bridge",      "major",     "cat-bridge",      "major",     "cat-bridge",      "cat-bridge",      "Bridges"),
    Type("landmark",      "landmark",    "major",     "cat-landmark",    "major",     "cat-landmark",    "cat-landmark",    "Landmarks"),
    Type("fortress",      "fortress",    "major",     "cat-fortress",    "major",     "cat-fortress",    "cat-fortress",    "Fortresses"),
    # Towns
    Type("town",          "town",        "towns",     "cat-town",        "towns",     "cat-town",        "cat-town",        "Towns"),
    # Secondary locations
    Type("sacred-site",   "sacred-site", "spiritual", "cat-sacred-site", "secondary", "cat-sacred-site", "cat-sacred-site", "Sacred Sites"),
    Type("mythic-landscape", "mythic-landscape", "spiritual", "cat-sacred-site", "secondary", "cat-sacred-site", "cat-sacred-site", None),
    Type("oasis",         "oasis",       "secondary", "cat-oasis",       "secondary", "cat-oasis",       "cat-oasis",       "Oases"),
    Type("lake",          "lake",        "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       "Lakes"),
    Type("sea",           "sea",         "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       None),
    Type("river",         "river",       "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       None),
    Type("reservoir",     "reservoir",   "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       None),
    Type("spring",        "spring",      "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       None),
    Type("well",          "well",        "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       None),
    Type("caravanserai",  "route-node",  "secondary", "cat-route-node",  "secondary", "cat-route-node",  "cat-route-node",  None),
    # Route network
    Type("route-node",    "route-node",  "routes",    "cat-route-node",  "routes",    "cat-route-node",  "cat-route-node",  "Route Nodes"),
    Type("chokepoint",    "chokepoint",  "routes",    "cat-fortress",    "routes",    "cat-fortress",    "cat-fortress",    None),
    Type("mountain-pass", "mountain-pass", "routes",  "cat-landmark",    "routes",    "cat-landmark",    "cat-landmark",    None),
    # Detail layer
    Type("ruins",         "ruins",       "detail",    "cat-dungeon",     "detail",    "cat-dungeon",     "cat-dungeon",     None),
    Type("poi",           "poi",         "detail",    None,              "detail",    "cat-poi",         None,              "POIs"),
    Type("power-site",    "power-site",  "spiritual", "cat-sacred-site", "detail",    "cat-sacred-site", "cat-sacred-site", None),
    Type("site",          "site",        "detail",    "cat-poi",         "detail",    "cat-poi",         "cat-poi",         None),
    # Legacy spellings still on pages or in old tooling: tolerated, never offered.
    Type("water-body",    "lake",        "secondary", "cat-water",       "secondary", "cat-water",       "cat-water",       None, listed=False),
    Type("dungeon",       "dungeon",     None,        None,              None,        None,              None,              None, listed=False),
    Type("Oasis",         None,          None,        "cat-oasis",       None,        None,              "cat-oasis",       None, listed=False),
)

CATEGORIES: list[str] = [t.slug for t in TYPES if t.listed]

VALID_CATEGORIES: frozenset[str] = frozenset(CATEGORIES)

DEFAULT_ICON = "cat-poi"


def tier_members(attr: str, tier: str) -> list[str]:
    """Slugs whose `attr` ("map_tier" or "page_tier") is `tier`, in row order."""
    return [t.slug for t in TYPES if getattr(t, attr) == tier]


def icon_arms(attr: str) -> list[tuple[str, str]]:
    """(slug, icon) for every row with an icon in `attr` ("map_icon", "page_icon" or
    "mini_icon"), in row order. A row with none is drawn with DEFAULT_ICON."""
    return [(t.slug, getattr(t, attr)) for t in TYPES if getattr(t, attr)]


# The world page's icon arms; the Workshop and the mini-maps read icon_arms() directly.
ICON_MAP: dict[str, str] = dict(icon_arms("page_icon"))


def build_icon_match_js(icon_size_expr: str = "1.3") -> str:
    """Build the MapLibre icon-image case/match expression as a JSON-fragment string.

    Priority:
      1. mapMarker frontmatter override — concat("cat-", mapMarker value)
      2. Category → icon via the table's page_icon column (ICON_MAP)
      3. Default: cat-poi

    icon_size_expr: a MapLibre expression string or bare number for icon-size.
    Pass a zoom-interpolate expression per layer tier for scaled sizing.

    Returns the full "icon-image": ... fragment plus icon-size / icon-allow-overlap /
    icon-anchor, ready to embed inside a MapLibre layout object literal.
    """
    pairs = "".join(f'"{cat}","{icon}",' for cat, icon in ICON_MAP.items())
    return (
        '"icon-image":["case",'
        '["!=",["get","mapMarker"],null],["concat","cat-",["get","mapMarker"]],'
        f'["match",["get","category"],{pairs}"{DEFAULT_ICON}"]],'
        f'"icon-size":{icon_size_expr},"icon-allow-overlap":true,"icon-anchor":"center"'
    )


def check_icon_coverage() -> list[str]:
    """Warnings where the table and the icons map_icons.py really registers disagree.

    An empty list means every icon a row names is registered, and every registered
    icon is used by some row on some surface.
    """
    from locations.map_icons import REGISTERED_ICONS

    columns = ("map_icon", "page_icon", "mini_icon")
    warnings: list[str] = []
    used = {getattr(t, c) for t in TYPES for c in columns if getattr(t, c)}
    for icon in sorted(REGISTERED_ICONS - used):
        warnings.append(f"Registered icon '{icon}' is not used by any Type")
    for t in TYPES:
        for c in columns:
            icon = getattr(t, c)
            if icon and icon not in REGISTERED_ICONS:
                warnings.append(f"Type '{t.slug}' has {c} '{icon}' which is not in map_icons.REGISTERED_ICONS")
    return warnings
