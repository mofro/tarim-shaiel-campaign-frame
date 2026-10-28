---
title: Locations — AI Navigation
project: TTRPG_Tarim_Shaiel
type: navigation
visibility: internal
status: canon
created: 2026-05-04
last_updated: 2026-10-27
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
| Shared map style | `utilities/shared/map_style.py` | MapLibre styling emitted as JS by every map: route line (`ROUTE_COLOR`; `routes_layer_js(dim_hidden=True)` dims routes the players cannot see, `ROUTE_DIM_OPACITY`), region layers, six location tiers, hover-popup JS/CSS, `popup_description()` (200-char blurb, `player_safe=True` strips `{gm:}`, placeholders and session/awakening text), `check_tier_coverage()`, basemap peak constants (`BASEMAP_PEAK_LAYER`, `BASEMAP_HIDDEN_LAYERS`, `PLAYER_HIDDEN_LAYERS`) and `basemap_hide_js()` — see Basemap Peak Markers below |
| Route visibility | `utilities/shared/route_visibility.py` | `visible_routes(routes, all_locations)` and `visible_waystations(waystations, routes)`: the one rule for which routes reach player output. Used by the player map and the public locations build |
| Route travel time | `utilities/shared/travel_time.py` | Speed table (`SPEEDS`), path factors, terrain constants (Tobler, `MAX_SLOPE`, tile URL and limits), `segment_hours(km, mode, path, slope_factor)`, `format_duration()`, `tt_json()` for the Workshop JS |
| Terrain path worker | `utilities/world/terrain_path.js` | Least-cost walk over terrarium elevation tiles (A*, Tobler, slope limits, IndexedDB tile cache); embedded in the Workshop as `_TERRAIN_SRC` and run in a Web Worker |
| Journeys | `utilities/shared/journeys.py` | Saved-journey store (`world/data/tarim-shaiel-journeys.geojson`): validation, `create`/`replace`/`patch`/`delete`, `popup_info()`, `journey_is_public()`, `player_payload()` / `gm_payload()`. See Journeys below |

**Surfaces using `map_style.py`:** the Workshop (`generate_map_workshop.py`, GM badge on `gm_secrets` hovers), the player map (`_build_player_html`, hover on desktop / tap-to-open on touch, no GM text, `gm_secrets` features dropped by `_player_locations_geojson`) and `docs/world.html` (routes and regions only; tiers, popups and click-navigate remain local to `generate_locations_html.py`). Workshop and player icon matching differs from `categories.ICON_MAP` (used by `world.html`) — a known divergence, not yet reconciled.

## Basemap Peak Markers

The MapTiler style (`01a074c7-536a-71cb-b0d8-9e7fe4fd1100`, `MAPTILER_STYLE_ID` in `location_components.py`) draws real-world peaks and volcanoes with six `icon-image: "triangle"` layers. They are hidden in code (#325, PR #326), not in MapTiler Cloud, so the Workshop and player map can differ and the locations pages that share the style are untouched.

| Layer | Workshop | Player map |
|---|---|---|
| `Peak labels` | "Peak markers" checkbox in the Layers menu, shown by default; state in `sessionStorage` key `_wsPeaks` | Hidden, no control |
| `Peak labels (US)`, `Volcano labels`, `Volcano labels (US)`, `Volcano labels active`, `Volcano labels active (US)` | Hidden | Hidden |

- `basemap_hide_js(ids)` emits a `map.getLayer()`-guarded `setLayoutProperty(id,"visibility","none")` loop run in the `map.on("load")` handler, so a renamed layer is a silent no-op. Layer ids contain spaces and parentheses and must match the style exactly.
- Tests: `tests/test_basemap_markers.py` (7).
- **Limit:** the Workshop Topo overlay is raster `topo-v2` tiles with peak glyphs baked in at zoom 9+, so peaks show with Peak markers off. Harmless in the Workshop; it must be decided before #323 shares overlays with players (accept it, give the player overlay a `maxzoom`, or use another raster). #323's Player's-eye preview must also hide `Peak labels`.

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

**Frontmatter write-back.** Every Workshop save (Apply, Save Fields, Edit Coords, Add Point follow-ups) goes through `_set_frontmatter_fields` and `_set_location` in `utilities/devserver.py`. Both use `_replace_first`, which counts matches: it replaces the first copy of a key in place and drops any later copies, so saving an unchanged value is a no-op and a page that already has duplicate keys heals on its next save (#321). Never test "did the text change" to decide whether a key exists; an identical replacement leaves the text unchanged. Tests: `tests/test_devserver_frontmatter.py`.

## Route Visibility

A route reaches player output only when its own `visibility` is `public` **and** both end locations are not `gm_secrets`; anything else hides it.

- **Endpoints:** a route's first and last coordinate are matched to the nearest location within 1 km, searching all locations (hidden ones too, so a hidden end is found and hides the route).
- **Fails closed:** a missing route `visibility`, an endpoint with no location within 1 km, or a missing end location hides the route. An unmatched endpoint on an otherwise public route prints a warning to stderr.
- **Surfaces:** the player map, `docs/world.html` and every location mini-map in public builds. `--gm` builds and the Workshop keep every route; the Workshop dims the hidden ones and the route panel shows who sees each.
- **Waystations:** filtered by `properties.route_segment`; a missing `route_segment` drops the point. No waystations file exists today.
- **Revealing:** routes need no separate step beyond a route's own `visibility`. Reveal both end locations, then set the route to `public` in the Workshop route panel.

All 37 routes were set to `gm_secrets` on 2026-10-26, together with the locations.

## Journeys

A journey is a saved multi-stop trip planned on the Workshop **Travel Time** tab. It is a GeoJSON Feature (id `journey_<slug>`) in `world/data/tarim-shaiel-journeys.geojson`, a `MultiLineString` with one line per leg. The file is created on the first save.

- **Per-leg state:** each leg has a `mode` (a key of the speed table) and a `path` (`road` follows OSRM, `terrain` is a least-cost walk over elevation tiles, `straight` is a direct line). Fliers (bird, dragon) force `straight`. Time is computed from the leg's length, mode, path and, for terrain legs, the saved `slope_factor`, so a speed-table change updates every journey.
- **Terrain paths (#312):** the walk runs in a browser Web Worker (`utilities/world/terrain_path.js`, embedded in the Workshop page as text), so the page stays responsive. It reads AWS terrarium elevation tiles and keeps them in IndexedDB (`hh-terrain-tiles`), so a repeat leg needs no network. Steps are weighted by a relative Tobler hiking factor `exp(-3.5(|S+0.05|-0.05))` (1.0 on the flat), and a step steeper than the mode's limit is impassable (foot 0.60, mounted 0.35, cart 0.12 rise/run), so a cart routes around a climb a walker would take. `slope_factor` is the path's average speed against flat ground (clamped 0.05 to 2), is saved on the leg, and seeds the Workshop cache on load, so a saved journey reloads with no re-routing. Data credit: U.S. Geological Survey (SRTM, GMTED2010).
- **Terrain limits:** water is not a barrier (a river crossing costs nothing); existing roads are ignored; the result is only as fine as the elevation data (about 30 to 90 m); the 8-neighbour grid makes a flat leg up to about 8% longer than the straight line (86 km against 80 km). A leg is refused below zoom 6 (`toolarge`), and a failed tile fetch or an unreachable stop (`network`, `nopath`) falls back to a straight line with a notice. The slope limits and the 8 hour day are assumptions, edited in `utilities/shared/travel_time.py`.
- **Stops:** a stop that sits on a location carries its `slug` and follows it. Loading a journey snaps a stop to its location when the location has moved more than 50 m (`STALE_M`) and recomputes the legs on either side as unsaved changes. A free point has no slug.
- **Visibility:** new journeys are `gm_secrets`. A journey reaches player output only when its own `visibility` is `public` **and** every slug-stop exists and is not `gm_secrets` **and** the nearest location within 1 km of every stop is not `gm_secrets` (`journey_is_public`). Anything else hides it, so it fails closed like routes. Judged against the full location set, before the public filter.
- **Player payload:** only `{id, name}` plus geometry, with the popup text (`popup_info`: per-leg from, to, how, km, time, and a total) formatted once in Python. Popups open on hover in the Workshop and on tap in the player map and `world.html`; they are suppressed while the cursor is over a location marker.
- **Surfaces:** the Workshop (hidden journeys dimmed, `Saved journeys` layer toggle), the player map, `docs/world.html` and the location and region mini-maps (plain line, no popup there). `--gm` builds keep every journey.
- **Boot:** the Workshop embeds journeys at build time but refetches `GET /api/journeys` on load, so a journey saved since the last build still lists. The player map is static, so rebuild after making a journey public.
- **Endpoints:** `GET`/`POST /api/journeys`, `PUT`/`PATCH`/`DELETE /api/journeys/{id}` (see `lat.md/build-workflows.md`). `PUT` keeps id, visibility and `created`; `PATCH` changes only `name` and `visibility`.

## Coordinate Audit

`utilities/locations/coord_audit.py` (#314) lists locations whose coordinates or `elevation:` look wrong and lets the GM decide each one. It shows evidence and never edits a file until an annotated report is passed back in.

- **Evidence:** the terrain elevation at the location (AWS terrarium tiles, credit USGS) against the `elevation:` field, and the location of its real-world analog (Wikidata P625 from `real_world_name`, or an exact `wikidata:` id) against `location:`. MapTiler is never fetched from the script (its terms do not allow scripted bulk use).
- **Classes:** `coord-suspect` (analog 20 km or more away and the elevation field fits the analog better, or the analog is the only evidence), `elevation-suspect` (analog near, field off by more than 250 m), `resolution-suspect` (field off, but inside the 1 km relief range, so probably a sampling artefact; no elevation is suggested), `ambiguous` (evidence disagrees, or only the terrain is available). Thresholds are constants at the top of the script.
- **Ranking:** two tiers. Rows where the `elevation:` field contradicts the terrain at the stated position come first, because that is evidence from the location's own data. Rows where only an analog name match disagrees come after them, since a generic name matches many real places. Inside a tier the score is the multiple of the thresholds exceeded, weighted by class.
- **Report:** `world/data/coord-audit/audit-<timestamp>.md` and `.csv`, same rows, ranked, with a blank `decision` column. The directory and its tile and Wikidata caches are gitignored. A new run never overwrites an earlier report.
- **Decisions:** `move` writes the row's `suggest_lat`/`suggest_lon` (editable) to `location:`; `elevation` writes `suggest_elev` to `elevation:`; `intentional` stamps `coord_review: intentional` and `coord_reviewed: <date>` so the row is never listed again; `skip` or blank writes nothing. `move` and a near-analog `elevation` also store the analog's `wikidata:` id so later runs match it exactly.
- **Apply:** `coord_audit.py --apply <file> [--dry-run] [--confirm-canon]`. All rows are checked first and any error (unknown decision, stale row, canon file without `--confirm-canon`) stops the run with nothing written. Edits go through the devserver's `_set_location` and `_set_frontmatter_fields` (which bumps `last_updated`), the same path as the Workshop's coordinate edit. After a `move` it lists the routes that start or end within 1 km of the old position; run Regenerate on each, then rebuild.
- **Analog matching:** the first search hit with coordinates inside the map region (lon 45 to 125, lat 15 to 55) is used and flagged when another such hit is more than 100 km away. A missing `real_world_name`, or the value `redirect`, gives a terrain-only check for manual review. Many `real_world_name` values are generic (a balcony, old town), so confirm the analog shown on each row.
- **Limits:** the player map and `docs/world.html` never see audit data. `zz`- and `_`-prefixed files are skipped like the generators. A coarse zoom-10 sample screens every location; only rows whose field disagrees are re-sampled at zoom 12. About 200 tiles are fetched once and cached; `--max-tiles` stops a run that would fetch more than 600.

## GeoJSON Structure

- `world/data/tarim-shaiel-locations.geojson` — one Point per location (183 as of 2026-10-25); IDs: `location_{slug}`
- `world/data/tarim-shaiel-routes.geojson` — trade route linestrings; per-route properties `visibility` (all `gm_secrets`) and optional `mode`
- `world/data/tarim-shaiel-journeys.geojson` — saved travel journeys, one MultiLineString per journey; per-journey properties `name`, `visibility`, `stops`, `legs` (see Journeys above). Absent until the first save
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
- A Workshop rename writes `title:` only when the page has both `title:` and `name:`, so a rename can leave `name:` stale (pre-existing, not changed by #321)
