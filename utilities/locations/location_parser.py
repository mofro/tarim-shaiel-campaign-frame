"""
Location source file parser.

Reads world/locations/*.md files and returns structured LocationData dicts.
Strips Obsidian leaflet blocks, extracts frontmatter, classifies location type.
"""

import re
from pathlib import Path
from typing import TypedDict, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

class LocationData(TypedDict):
    slug: str
    title: str
    fantasy_name: str
    description: str
    location_type: str       # city | route-node | oasis | dungeon | landmark | poi | sacred-site | fortress
    visibility: str          # public | secret | gm_secrets
    status: str
    parent_region: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    elevation: Optional[int]
    mapmarker: str
    factions_visible: list[str]
    resources: list[str]
    tags: list[str]
    gm_revealed: list[str]   # list of block IDs promoted to player-visible
    body: str                # raw markdown body (leaflet block stripped)
    source_path: Path


# ---------------------------------------------------------------------------
# Location type classification
# ---------------------------------------------------------------------------

_TYPE_FIELD_MAP: dict[str, str] = {
    "city": "city",
    "route-node": "route-node",
    "oasis": "oasis",
    "dungeon": "dungeon",
    "landmark": "landmark",
    "poi": "poi",
    "sacred-site": "sacred-site",
    "fortress": "fortress",
    "water-body": "landmark",
    "caravanserai": "route-node",
}

_CONTENT_TYPE_MAP: dict[str, str] = {
    "location": "city",
    "poi": "poi",
    "landmark": "landmark",
}

_TAG_TYPE_MAP: dict[str, str] = {
    "type-city": "city",
    "type-route-node": "route-node",
    "type-oasis": "oasis",
    "type-dungeon": "dungeon",
    "type-sacred-site": "sacred-site",
    "type-fortress": "fortress",
}


def _classify_type(fm: dict) -> str:
    """Determine location type from frontmatter fields in priority order."""
    # 1. explicit `type:` field
    raw = fm.get("type", "")
    if isinstance(raw, str):
        raw = raw.lower().replace("_", "-").strip()
        if raw in _TYPE_FIELD_MAP:
            return _TYPE_FIELD_MAP[raw]

    # 2. `mapmarker:` field
    marker = str(fm.get("mapmarker", "")).lower().strip()
    if marker in _TYPE_FIELD_MAP:
        return _TYPE_FIELD_MAP[marker]

    # 3. `content_type:` field
    ct = str(fm.get("content_type", "")).lower().strip()
    if ct in _CONTENT_TYPE_MAP:
        return _CONTENT_TYPE_MAP[ct]

    # 4. tags list
    tags = _str_list(fm.get("tags", []))
    for tag in tags:
        if tag in _TAG_TYPE_MAP:
            return _TAG_TYPE_MAP[tag]

    return "poi"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LEAFLET_BLOCK_RE = re.compile(
    r'```leaflet\n.*?```', re.DOTALL
)


def strip_leaflet_block(body: str) -> str:
    """Remove Obsidian ```leaflet ... ``` blocks from markdown body."""
    return _LEAFLET_BLOCK_RE.sub('', body).strip()


def _str_list(val) -> list[str]:
    """Normalise a frontmatter field to a list of strings."""
    if isinstance(val, list):
        return [str(v).strip() for v in val if v is not None]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _parse_fm(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text)."""
    m = re.match(r'^---\n(.*?\n)---\n', text, re.DOTALL)
    if not m:
        return {}, text

    fm_text = m.group(1)
    body = text[m.end():]

    if _YAML_AVAILABLE:
        try:
            fm = yaml.safe_load(fm_text) or {}
        except Exception:
            fm = {}
    else:
        fm = {}
        for line in fm_text.splitlines():
            kv = line.split(':', 1)
            if len(kv) == 2 and not line.startswith(' ') and not line.startswith('-'):
                k, v = kv[0].strip(), kv[1].strip()
                fm[k] = v.strip('"\'')

    return fm, body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_location(path: Path) -> Optional[LocationData]:
    """Parse a location .md file into a LocationData dict.

    Returns None if the file is a template, test fixture, or not a location doc.
    """
    name = path.name
    if name.startswith('_') or name.startswith('zz'):
        return None

    text = path.read_text(encoding='utf-8')
    fm, body = _parse_fm(text)

    if not fm:
        return None

    # Accept content_type in {location, poi, landmark} OR explicit `type:` field
    ct = str(fm.get('content_type', '')).lower()
    if ct not in ('location', 'poi', 'landmark', 'region'):
        # Some files use `type:` only
        if not fm.get('type') and not fm.get('mapmarker'):
            return None

    # Extract coordinates
    lat = lon = None
    loc = fm.get('location')
    if isinstance(loc, list) and len(loc) >= 2:
        try:
            lat, lon = float(loc[0]), float(loc[1])
        except (TypeError, ValueError):
            pass

    # Elevation
    elev = None
    try:
        elev = int(fm.get('elevation', 0) or 0)
    except (TypeError, ValueError):
        pass

    title = str(fm.get('title') or fm.get('name') or path.stem).strip()
    fantasy_name = str(fm.get('fantasy_name') or title).strip()
    slug = path.stem

    return LocationData(
        slug=slug,
        title=title,
        fantasy_name=fantasy_name,
        description=str(fm.get('description', '')).strip(),
        location_type=_classify_type(fm),
        visibility=str(fm.get('visibility', 'public')).strip(),
        status=str(fm.get('status', 'draft')).strip(),
        parent_region=fm.get('parent_region') or None,
        lat=lat,
        lon=lon,
        elevation=elev,
        mapmarker=str(fm.get('mapmarker', '')).strip(),
        factions_visible=_str_list(fm.get('factions_visible') or fm.get('factions', [])),
        resources=_str_list(fm.get('resources', [])),
        tags=_str_list(fm.get('tags', [])),
        gm_revealed=_str_list(fm.get('gm_revealed', [])),
        body=strip_leaflet_block(body),
        source_path=path,
    )


def load_all_locations(locations_dir: Path, public_only: bool = False) -> list[LocationData]:
    """Load and parse all location files from a directory.

    public_only: skip files with visibility != 'public'.
    """
    results: list[LocationData] = []
    for p in sorted(locations_dir.glob('*.md')):
        data = parse_location(p)
        if data is None:
            continue
        if public_only and data['visibility'] != 'public':
            continue
        results.append(data)
    return results
