---
title: Locations — AI Navigation
project: TTRPG_Tarim_Shaiel
type: navigation
visibility: internal
status: canon
created: 2026-05-04
last_updated: 2026-10-26
---

> _Navigation layer — stop here if the summary answers your question. Do not read individual location files unless you need specific detail._

# Locations

## Generator Architecture

| Component | Path | Purpose |
|---|---|---|
| Main generator | `utilities/locations/generate_locations_html.py` | Full generation loop; CLI + build.py entry point |
| Location parser | `utilities/locations/location_parser.py` | Parses `world/locations/*.md` → `LocationData` dicts |
| Region parser | `utilities/locations/region_parser.py` | Parses `world/regions/*.md` → `RegionData` dicts |
| HTML components | `utilities/locations/location_components.py` | Mini-map, faction table, danger pips, stats row, xref stub |
| Normalization script | `utilities/world/normalize_locations.py` | One-time migration; adds `parent_region`, `visibility`, `status`, renames `factions→factions_visible` |
| Category source of truth | `utilities/locations/categories.py` | `CATEGORIES` (17 canonical types), `VALID_CATEGORIES`, `ICON_MAP`. The Workshop Add Point and Edit Coords dropdowns, `utilities/map.py` and `add_location.py` all import it — add a type here only |
| Shared map style | `utilities/shared/map_style.py` | MapLibre styling emitted as JS by every map: route line (`ROUTE_COLOR`), region layers, six location tiers, hover-popup JS/CSS, `popup_description()` (200-char blurb, `player_safe=True` strips `{gm:}`, placeholders and session/awakening text), `check_tier_coverage()` |

**Surfaces using `map_style.py`:** the Workshop (`generate_map_workshop.py`, GM badge on `gm_secrets` hovers), the player map (`_build_player_html`, hover on desktop / tap-to-open on touch, no GM text, `gm_secrets` features dropped by `_player_locations_geojson`) and `docs/world.html` (routes and regions only; tiers, popups and click-navigate remain local to `generate_locations_html.py`). Workshop and player icon matching differs from `categories.ICON_MAP` (used by `world.html`) — a known divergence, not yet reconciled.

## Output Paths

| Output | Description |
|---|---|
| `docs/world.html` | World home page — full Leaflet map + region cards + A-Z location index |
| `docs/locations/<slug>.html` | ~35 individual location detail pages |
| `docs/locations/regions/<slug>.html` | 7 regional index pages |

## Slug → Region Mapping

| Region slug | GeoJSON ID | Locations | Notes |
|---|---|---|---|
| `tarim-basin` | `region_tarim_basin` | ~20 | Core Silk Road oases |
| `eastern-gateway` | `region_eastern_gateway` | 4 | Gansu Corridor; Elven sacred sites |
| `central-asian-hubs` | `region_central_asia` | ~5 | Transoxiana/Sogdiana cities |
| `eastern-terminus` | _(no polygon)_ | 1 | Chang'an only |
| `mountain-passes` | _(no polygon)_ | 3 | Dwarven pass infrastructure |
| `transoxiana` | _(no polygon)_ | 0 | Stub; future development |
| `steppe-confederations` | _(no polygon)_ | 2+ | Nomadic; Alak-Mor, Balkh-Kamen |

## Type Classification (from location frontmatter)

Priority: `type:` field → `mapmarker:` → `content_type:` → tags (type-city etc.)

| Type slug | Display label | Default danger pips |
|---|---|---|
| city | City | 1 |
| route-node | Route Node | 2 |
| oasis | Oasis | 2 |
| sacred-site | Sacred Site | 3 |
| dungeon | Dungeon | 4 |
| landmark | Landmark | 3 |
| fortress | Fortress | 3 |
| poi | Point of Interest | 1 |

## GM Reveal Mechanic

**Syntax in location .md files:**
```markdown
> [!gm-only id=some-unique-id]
> This block is normally GM-only but can be promoted to player-visible.
```

**Promotion in frontmatter:**
```yaml
gm_revealed:
  - some-unique-id
```

At build time, any block whose `id=` value appears in `gm_revealed` is rendered as `.revealed-content.gm-callout--revealed` — promoted to the player DOM regardless of `gm_mode`. Blocks without a matching revealed ID are stripped in public builds.

## Map Reveal Workflow

Every location page is `visibility: gm_secrets` (flipped in one pass on 2026-10-26), so a public build shows no location markers, pages or search entries until you reveal them.

**Reveal tab (Workshop, devserver required).** Click a GM-only marker, or press **+** beside a name in the hidden list, to stage it (gold ring; green ring = already public). **Apply N reveals** confirms, then sets `visibility: public` on each staged location through `PATCH /api/locations/{slug}/frontmatter`, one at a time, and rebuilds the Workshop and the location pages. A failed PATCH leaves that row staged with its error. Staged earmarks live in the browser's `localStorage`, so they are per browser, and nothing is written until Apply. Locations with no coordinates cannot be staged there.

Revealing by hand is the same change: set `visibility: public` in the frontmatter.

Then commit + push → Netlify rebuilds → players see the marker.

`revealed: 2026-05-14` is an optional audit datestamp written by a Templater hook on save. No generator reads it and the Reveal tab does not write it; only `visibility` decides what is public. It is unrelated to `gm_revealed:` above, which promotes a single GM-only block.

The tracked `world/data/tarim-shaiel-locations.geojson` snapshot is not rewritten by Apply, so its `visibility` values lag behind the pages until `python utilities/build.py geojson --gm` is run.

## GeoJSON Structure

- `world/data/tarim-shaiel-locations.geojson` — one Point per location (183 as of 2026-10-25); IDs: `location_{slug}`
- `world/data/tarim-shaiel-routes.geojson` — trade route linestrings
- `world/data/tarim-shaiel-regions.geojson` — **removed in #299 (commit 2814443)**; recoverable from `2814443^`. Generators treat the missing file as "no regions layer", so no region polygons render anywhere. The GeoJSON IDs in the mapping table above are historical

Leaflet maps use ESRI satellite tile layer + Carto label overlay (no API key required).

## Build Commands

```bash
# Default (public-only, no GM content)
python utilities/build.py locations

# GM build
python utilities/build.py locations --gm

# Dry run
python utilities/locations/generate_locations_html.py --dry-run

# Full pipeline (locations runs before search-index to avoid broken links)
python utilities/build.py all
```

## Known Gaps

- `dun-kharan.md` — no coordinates (complex frontmatter; parent_region: null)
- `tarim-shaiel.md` — overview doc, not a specific location; parent_region: null
- No region has a GeoJSON polygon since #299 removed `tarim-shaiel-regions.geojson`; the region boundary layer is empty everywhere (the player map has no regions layer at all)
- `docs/locations/` cross-links not yet populated (xref-stub placeholder)
- `zzkashkar.md` — duplicate stub file; excluded by `zz` prefix filter
