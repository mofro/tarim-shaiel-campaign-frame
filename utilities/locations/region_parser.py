"""
Region source file parser.

Reads world/regions/*.md files and returns structured RegionData dicts keyed
by region slug. Used by the locations generator to build region index pages
and annotate location detail pages.
"""

import re
from pathlib import Path
from typing import TypedDict, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


class RegionBounds(TypedDict):
    sw: list[float]  # [lat, lon]
    ne: list[float]  # [lat, lon]


class RegionData(TypedDict):
    slug: str
    title: str
    geojson_id: Optional[str]
    bounds: Optional[RegionBounds]
    location_count: int        # declared in frontmatter; actual count added at runtime
    primary_ancestry: str
    faction_weight: str        # low | medium | high
    visibility: str
    status: str
    body: str                  # markdown prose


def _parse_fm(text: str) -> tuple[dict, str]:
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
            if len(kv) == 2 and not line.startswith(' '):
                k, v = kv[0].strip(), kv[1].strip()
                fm[k] = v.strip('"\'')

    return fm, body


def parse_region(path: Path) -> Optional[RegionData]:
    """Parse a region .md file into a RegionData dict."""
    if path.name.startswith('_') or path.name.startswith('KEY_'):
        return None

    text = path.read_text(encoding='utf-8')
    fm, body = _parse_fm(text)

    if not fm:
        return None

    ct = str(fm.get('content_type', '')).lower()
    if ct not in ('region',):
        return None

    geojson_id = fm.get('geojson_id')
    if geojson_id == 'null' or geojson_id is None:
        geojson_id = None

    bounds_raw = fm.get('bounds')
    bounds: Optional[RegionBounds] = None
    if isinstance(bounds_raw, dict):
        sw = bounds_raw.get('sw')
        ne = bounds_raw.get('ne')
        if sw and ne:
            bounds = RegionBounds(sw=list(sw), ne=list(ne))

    return RegionData(
        slug=path.stem,
        title=str(fm.get('title', path.stem)).strip(),
        geojson_id=geojson_id,
        bounds=bounds,
        location_count=int(fm.get('location_count', 0) or 0),
        primary_ancestry=str(fm.get('primary_ancestry', 'mixed')).strip(),
        faction_weight=str(fm.get('faction_weight', 'medium')).strip(),
        visibility=str(fm.get('visibility', 'public')).strip(),
        status=str(fm.get('status', 'draft')).strip(),
        body=body.strip(),
    )


def load_all_regions(regions_dir: Path) -> dict[str, RegionData]:
    """Load and parse all region files. Returns a slug→RegionData dict."""
    result: dict[str, RegionData] = {}
    for p in sorted(regions_dir.glob('*.md')):
        data = parse_region(p)
        if data is not None:
            result[data['slug']] = data
    return result
