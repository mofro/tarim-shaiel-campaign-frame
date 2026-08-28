"""
Single source of truth for Tarim-Shaiel location category slugs.

Exports
-------
CATEGORIES       — ordered list of all valid category slugs (display order mirrors map zoom tiers)
ICON_MAP         — maps each category slug to its registered MapLibre icon name
VALID_CATEGORIES — frozenset for O(1) membership checks and CLI validation
REGISTERED_ICONS — icon names declared in map_icons.py (for cross-validation)
"""

CATEGORIES: list[str] = [
    # Major locations — visible from zoom 3
    "city",
    "landmark",
    "fortress",
    # Towns — visible from zoom 4
    "town",
    # Secondary locations — visible from zoom 5
    "sacred-site",
    "oasis",
    "caravanserai",
    # Route network — visible from zoom 6
    "route-node",
    "chokepoint",
    "mountain-pass",
    # Detail layer — visible from zoom 7
    "ruins",
    "poi",
    "power-site",
    "site",
]

# Maps each category slug to its registered cat-* icon name.
# Alias categories (caravanserai, chokepoint, etc.) share an icon with their
# visual equivalent — that is intentional, not an error.
ICON_MAP: dict[str, str] = {
    "city":          "cat-city",
    "town":          "cat-town",
    "landmark":      "cat-landmark",
    "fortress":      "cat-fortress",
    "sacred-site":   "cat-sacred-site",
    "oasis":         "cat-oasis",
    "caravanserai":  "cat-route-node",
    "route-node":    "cat-route-node",
    "chokepoint":    "cat-fortress",
    "mountain-pass": "cat-landmark",
    "ruins":         "cat-dungeon",
    "poi":           "cat-poi",
    "power-site":    "cat-sacred-site",
    "site":          "cat-poi",
}

VALID_CATEGORIES: frozenset[str] = frozenset(CATEGORIES)

# Icon names registered via _mk() in map_icons.py.
# Keep in sync with that file — used by check_icon_coverage().
REGISTERED_ICONS: frozenset[str] = frozenset({
    "cat-city",
    "cat-town",
    "cat-route-node",
    "cat-sacred-site",
    "cat-fortress",
    "cat-oasis",
    "cat-landmark",
    "cat-poi",
    "cat-dungeon",
})

_DEFAULT_ICON = "cat-poi"


def build_icon_match_js() -> str:
    """Build the MapLibre icon-image case/match expression as a JSON-fragment string.

    Priority:
      1. mapMarker frontmatter override — concat("cat-", mapMarker value)
      2. Category → icon alias via ICON_MAP
      3. Default: cat-poi

    Returns the full "icon-image": ... fragment plus icon-size / icon-allow-overlap /
    icon-anchor, ready to embed inside a MapLibre layout object literal.
    """
    pairs = "".join(f'"{cat}","{icon}",' for cat, icon in ICON_MAP.items())
    return (
        '"icon-image":["case",'
        '["!=",["get","mapMarker"],null],["concat","cat-",["get","mapMarker"]],'
        f'["match",["get","category"],{pairs}"{_DEFAULT_ICON}"]],'
        '"icon-size":1.3,"icon-allow-overlap":true,"icon-anchor":"center"'
    )


def check_icon_coverage() -> list[str]:
    """Return a list of coverage warnings between ICON_MAP and REGISTERED_ICONS.

    An empty list means ICON_MAP and REGISTERED_ICONS are fully consistent.
    """
    warnings: list[str] = []
    used = set(ICON_MAP.values())
    for icon in REGISTERED_ICONS:
        if icon not in used:
            warnings.append(f"Registered icon '{icon}' is not referenced by any category in ICON_MAP")
    for cat, icon in ICON_MAP.items():
        if icon not in REGISTERED_ICONS:
            warnings.append(f"Category '{cat}' maps to '{icon}' which is not in REGISTERED_ICONS")
    return warnings
