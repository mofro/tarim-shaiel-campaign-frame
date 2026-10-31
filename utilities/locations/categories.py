"""
Single source of truth for Tarim-Shaiel location Types.

TYPES is the one table. The parser, the Type dropdowns, the icon expressions, the
tier filters and the Display toggles all read it, so they cannot disagree about
what a Type is or how it is drawn (#336).

Where two surfaces disagree about a Type, the disagreement is a cell in this table,
not an exception in code, so fixing it edits one cell. The same goes for zoom: a tier
has one zoom, read by the Workshop, the player map, the world page, the GM layers and
the mini-maps, so moving a tier is one cell in TIER_ZOOM. `tests/fixtures/type_pins.json`
records what every Type draws on every surface; a change here regenerates it, and its
diff is the change's before-and-after pin list.

Columns
-------
slug       the value of a page's `type:`; the only column every row has
parses_as  what the location parser makes of that `type:` (or `mapmarker:`) value.
           None = the parser does not recognise it and falls through to the page's
           `content_type:`, then tags, then "poi"
tier       which tier draws it (TIER_ZOOM), on every surface; None = not drawn
map_icon   the icon the Workshop and player map draw; None = the default icon
page_icon  the icon the world page and the GM layers draw
mini_icon  the icon the mini-maps on location pages draw
toggle     the Display checkbox label; None = no checkbox, always drawn
listed     False = tolerated but not offered in any dropdown: a legacy spelling, an
           alias of another row, or a non-place (`icon: none`, no tier, never drawn)

Exports
-------
Type, TYPES        the row type and the table
TIER_ZOOM, TIERS   the tier ladder: each tier's zoom, and the names in layer (z) order
PAGE_ICON_SIZE     the world page's icon-size ramp for each tier
CATEGORIES         the listed slugs in dropdown order
VALID_CATEGORIES   frozenset of CATEGORIES, for membership checks and CLI validation
ICON_MAP           {slug: page_icon}, the world page's icon arms
DEFAULT_ICON       the icon a Type with no arm is drawn with
tier_members()     the slugs in one tier, in row order
tier_fade()        the zooms a tier's icon fades in over
icon_arms()        (slug, icon) pairs for one surface's icon match
"""

from typing import NamedTuple


class Type(NamedTuple):
    slug: str
    parses_as: str | None = None
    tier: str | None = None
    map_icon: str | None = None
    page_icon: str | None = None
    mini_icon: str | None = None
    toggle: str | None = None
    listed: bool = True


# The tier ladder. Each tier's icon starts fading in at this zoom and is fully drawn one
# zoom later; every surface reads it. Order is layer (z) order: later tiers sit above
# earlier ones. The Workshop and the world page cannot zoom out past 3, the mini-maps
# start at 5, so a tier below that is simply fully drawn from the first view.
TIER_ZOOM: dict[str, int] = {
    "capital": 2,
    "city": 3,
    "town": 4,
    "secondary": 5,
    "spiritual": 6,
    "routes": 6,
    "detail": 7,
}
TIERS = tuple(TIER_ZOOM)

# The world page's icon size for each tier: (zoom, size, zoom, size), a linear ramp --
# smaller at overview zooms to reduce crowding, growing as the viewer zooms in. The GM
# layers share it. (The Workshop and the mini-maps size their icons their own way.)
PAGE_ICON_SIZE: dict[str, tuple[int, float, int, float]] = {
    "capital":   (3, 0.5,  8, 0.85),
    "city":      (3, 0.5,  8, 0.85),
    "town":      (4, 0.45, 8, 0.78),
    "secondary": (5, 0.4,  8, 0.72),
    "spiritual": (5, 0.4,  8, 0.72),
    "routes":    (6, 0.35, 9, 0.66),
    "detail":    (7, 0.3, 10, 0.6),
}

# Row order is the order of the Type dropdowns and of the Display checkboxes. The
# unlisted rows come last and are the only rows with listed=False.
TYPES: tuple[Type, ...] = (
    #    slug             parses_as      tier         map_icon           page_icon          mini_icon          toggle
    # Cities
    Type("city",          "city",        "city",      "cat-city",        "cat-city",        "cat-city",        "Cities"),
    Type("capital",       "capital",     "capital",   "cat-capital",     "cat-capital",     "cat-capital",     "Capitals"),
    Type("bridge",        "bridge",      "city",      "cat-bridge",      "cat-bridge",      "cat-bridge",      "Bridges"),
    Type("landmark",      "landmark",    "city",      "cat-landmark",    "cat-landmark",    "cat-landmark",    "Landmarks"),
    Type("fortress",      "fortress",    "city",      "cat-fortress",    "cat-fortress",    "cat-fortress",    "Fortresses"),
    # Towns
    Type("town",          "town",        "town",      "cat-town",        "cat-town",        "cat-town",        "Towns"),
    # Sacred and mythic places
    Type("sacred-site",   "sacred-site", "spiritual", "cat-sacred-site", "cat-sacred-site", "cat-sacred-site", "Sacred Sites"),
    Type("mythic-landscape", "mythic-landscape", "spiritual", "cat-sacred-site", "cat-sacred-site", "cat-sacred-site", None),
    # Secondary locations
    Type("oasis",         "oasis",       "secondary", "cat-oasis",       "cat-oasis",       "cat-oasis",       "Oases"),
    Type("lake",          "lake",        "secondary", "cat-water",       "cat-water",       "cat-water",       "Lakes"),
    Type("sea",           "sea",         "secondary", "cat-water",       "cat-water",       "cat-water",       None),
    Type("river",         "river",       "secondary", "cat-water",       "cat-water",       "cat-water",       None),
    Type("reservoir",     "reservoir",   "secondary", "cat-water",       "cat-water",       "cat-water",       None),
    Type("spring",        "spring",      "secondary", "cat-water",       "cat-water",       "cat-water",       None),
    Type("well",          "well",        "secondary", "cat-water",       "cat-water",       "cat-water",       None),
    # Route network
    Type("route-node",    "route-node",  "routes",    "cat-route-node",  "cat-route-node",  "cat-route-node",  "Route Nodes"),
    Type("chokepoint",    "chokepoint",  "routes",    "cat-fortress",    "cat-fortress",    "cat-fortress",    None),
    Type("mountain-pass", "mountain-pass", "routes",  "cat-landmark",    "cat-landmark",    "cat-landmark",    None),
    # Detail layer
    Type("ruins",         "ruins",       "detail",    "cat-dungeon",     "cat-dungeon",     "cat-dungeon",     None),
    Type("poi",           "poi",         "detail",    None,              "cat-poi",         None,              "POIs"),
    Type("power-site",    "power-site",  "spiritual", "cat-sacred-site", "cat-sacred-site", "cat-sacred-site", None),
    Type("site",          "site",        "detail",    "cat-poi",         "cat-poi",         "cat-poi",         None),
    # Legacy spellings still on pages or in old tooling: tolerated, never offered.
    Type("water-body",    "lake",        "secondary", "cat-water",       "cat-water",       "cat-water",       None, listed=False),
    Type("caravanserai",  "route-node",  "routes",    "cat-route-node",  "cat-route-node",  "cat-route-node",  None, listed=False),
    Type("dungeon",       "dungeon",     None,        None,              None,              None,              None, listed=False),
    # Not places: `icon: none`. The parser keeps the page's Type; no tier draws it.
    Type("cosmological-realm", "cosmological-realm", None, None, None, None, None, listed=False),
    Type("mobile entity", "mobile entity", None,      None,              None,              None,              None, listed=False),
    Type("Oasis",         None,          None,        "cat-oasis",       None,              "cat-oasis",       None, listed=False),
)

CATEGORIES: list[str] = [t.slug for t in TYPES if t.listed]

VALID_CATEGORIES: frozenset[str] = frozenset(CATEGORIES)

DEFAULT_ICON = "cat-poi"


def tier_members(tier: str) -> list[str]:
    """Slugs whose `tier` is `tier`, in row order."""
    return [t.slug for t in TYPES if t.tier == tier]


def tier_fade(tier: str) -> tuple[int, int]:
    """(start, end) zooms of a tier's icon fade: from the tier's zoom to one zoom later."""
    zoom = TIER_ZOOM[tier]
    return zoom, zoom + 1


def page_icon_size_expr(tier: str) -> str:
    """The world page's icon-size expression for a tier (PAGE_ICON_SIZE)."""
    z0, s0, z1, s1 = PAGE_ICON_SIZE[tier]
    return f'["interpolate",["linear"],["zoom"],{z0},{s0},{z1},{s1}]'


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
