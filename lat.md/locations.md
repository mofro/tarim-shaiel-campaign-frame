---
title: Locations — AI Navigation
project: TTRPG_Tarim_Shaiel
type: navigation
visibility: internal
status: canon
created: 2026-05-04
last_updated: 2026-05-14
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

Features start as `visibility: gm_secrets` — dimmed on the GM map, invisible on the player map. When players discover a location, the GM promotes it to player-visible via `world/data/player-revealed.json`.

**Three-state model:**

| State | GM map | Player map |
|---|---|---|
| `visibility: public` | full opacity | full opacity |
| `visibility: gm_secrets` (unrevealed) | dimmed (40%), "GM only" badge | hidden |
| `visibility: gm_secrets` + ID in `player-revealed.json` | full opacity | full opacity |

**GM workflow:**
1. After session: identify which features players discovered
2. Open `world/data/player-revealed.json`
3. Add the feature's GeoJSON ID to the `"revealed"` array
4. Commit + push → Netlify rebuilds → players see the new marker

**Feature ID format:**
```
location_<slug>    e.g.  location_jade-gate
region_<id>        e.g.  region_tarim_basin
route_<id>
```

**Current gm_secrets features** (candidates for reveal):
- `location_jade-gate` — Jade Gate (fortress, eastern-gateway)

**Future upgrade:** When file-editing becomes friction, replace with a GM-build UI button ("Reveal to players") that downloads an updated JSON. Filed as a future enhancement.

## GeoJSON Structure

- `world/data/tarim-shaiel-locations.geojson` — 32 features; IDs: `location_{slug}`
- `world/data/tarim-shaiel-routes.geojson` — trade route linestrings
- `world/data/tarim-shaiel-regions.geojson` — 3 polygon features; IDs: `region_tarim_basin`, `region_eastern_gateway`, `region_central_asia`

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
- 4 of 7 regions have no GeoJSON polygon — region boundary layer shows only 3 polygons
- `docs/locations/` cross-links not yet populated (xref-stub placeholder)
- `zzkashkar.md` — duplicate stub file; excluded by `zz` prefix filter
