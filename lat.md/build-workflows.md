---
title: Build Workflows — Scenario Reference
project: TTRPG_Tarim_Shaiel
domain: utilities
doc_type: operational
content_type: reference
visibility: internal
status: canon
created: 2026-08-31
last_updated: 2026-09-02
tags: [build, pipeline, generators, workflow]
---

# Build Workflows — Scenario Reference

Quick lookup: what to run when. All commands run from the **vault root**.

---

## Scenario → Command

| I want to… | Run |
|---|---|
| New/edited location `.md` stubs → world map + detail pages | `python utilities/build.py locations` |
| New/edited location stubs → map workshop | `python utilities/build.py workshop` |
| Update routes for the workshop | edit `world/data/tarim-shaiel-routes.geojson`, then `python utilities/build.py workshop` |
| Update static location GeoJSON snapshot | `python utilities/build.py geojson` |
| Rebuild everything (all generators) | `python utilities/build.py all` |
| Public-facing rebuild only (no GM content) | `python utilities/build.py all --public` |
| GM-mode rebuild (auth-gated, all content) | `python utilities/build.py all --gm` |
| Netlify production build | runs `build.py all --public` automatically on push — no manual step |
| Interactive location/route editing (drag-to-update) | `python utilities/devserver.py` — site at `localhost:8000/`, workshop at `localhost:8000/workshop` |
| See all registered generators | `python utilities/build.py list` |

---

## Architecture Notes

### What each generator reads and writes

| Generator | Reads from | Writes to | Key dependency |
|---|---|---|---|
| `locations` | `world/locations/*.md` + `world/regions/*.md` + routes/regions/waystations GeoJSON | `docs/world.html` + `docs/locations/**` | MAPTILER_KEY (tiles load at runtime — no build failure if absent) |
| `workshop` | `world/locations/*.md` + `world/data/tarim-shaiel-routes.geojson` + `world/data/tarim-shaiel-regions.geojson` | `docs/map-workshop.html` | **MAPTILER_KEY required at build time** — key is baked into the HTML |
| `geojson` | `world/locations/*.md` | `world/data/tarim-shaiel-locations.geojson` | none |
| `world-all` | `narrative/world/**/*.md` + `narrative/lore/**/*.md` | `docs/world/**` | none |

### Critical distinction: `locations` vs. `workshop`

Both read location `.md` files, but they are **independent generators**:

- `locations` builds `docs/world.html` (the public-facing world map) and all location detail pages. Location data is built **in-memory** from `.md` files and inlined into the HTML at build time. It does **not** read `world/data/tarim-shaiel-locations.geojson`.
- `workshop` builds `map-workshop.html` in vault root (GM route-planning tool, gitignored). Also inlines location data in-memory from `.md` files. Routes come from `world/data/tarim-shaiel-routes.geojson`. **Excluded from `build.py all`** — invoke explicitly as `build.py workshop`.
- `geojson` generates `world/data/tarim-shaiel-locations.geojson` as a standalone snapshot — used by external tools, not by either HTML generator.

Running `build.py locations` does **not** update the workshop. Running `build.py workshop` does **not** update `world.html`. Run both explicitly, or use `build.py all` for the Netlify-publishable generators.

### MAPTILER_KEY

- Required **at build time** for `workshop` (baked into HTML). If absent, `build.py workshop` and `build.py all` skip the workshop with a warning.
- **Not** required at build time for `locations` — the key is already baked into previously generated HTML, and tile fetching happens at runtime in the browser.
- Store the key in a `.env` file at vault root (gitignored): `MAPTILER_KEY=your_key_here`

---

## Common Workflows

### "I added new location stubs"

```bash
python utilities/build.py locations    # updates world.html + location pages
python utilities/build.py workshop     # updates map workshop
```

Or just:

```bash
python utilities/build.py all          # rebuilds everything (workshop skipped if no key)
```

### "I edited routes in the GeoJSON"

```bash
python utilities/build.py workshop     # re-inlines the updated routes.geojson
```

### "I need to share a standalone location GeoJSON"

```bash
python utilities/build.py geojson      # writes world/data/tarim-shaiel-locations.geojson
```

### "Something looks wrong — full clean rebuild"

```bash
python utilities/build.py all
```

---

## Map Workshop — What It Is and How to Use It

The map workshop is a **local GM-only tool**. It is gitignored (contains the MapTiler API key baked in), never deployed to Netlify, and only accessible to whoever regenerates it on their local machine.

### What it is

A full-screen interactive map (`map-workshop.html` at vault root) with a left-panel sidebar. It shows all placed locations as pins, all routes as polylines, and region polygons when present. It is not a viewer — it is an **authoring and planning environment** for the GM.

Run it with the devserver for write-back capability (drag-to-update, in-browser rebuilds):

```bash
python utilities/devserver.py
```

Open at `http://localhost:8000/workshop`. Without the devserver, open `map-workshop.html` directly in a browser — read-only, no write-back.

---

### The Four Tabs

#### Add Point *(devserver required for one-click creation)*
For adding new location stubs with coordinates. Provides a form (title, category, fantasy name, description, lat/lon). Clicking the map drops a crosshair at that point and populates the coordinate fields. Click **Create Location** — the button POSTs to `POST /api/locations/create`, which runs `map.py location` end-to-end: writes the `.md` stub, rebuilds the GeoJSON snapshot, then triggers a workshop rebuild. Status shown inline; reload the workshop to see the new pin.

#### Plan Route *(devserver required for one-click adding)*
For building new routes between locations. Click location markers on the map to queue waypoints. The queue shows straight-line distance and travel time between each pair. Click **Add Route** — the button POSTs to `POST /api/routes/add`, which runs `map.py route` end-to-end: writes segments to `world/data/tarim-shaiel-routes.geojson`, snaps to roads via OSRM, rebuilds GeoJSON and workshop. Status shown inline; reload to see the new route.

Check "Spur route (branch)" before clicking Add Route to use the `route_spur_` id prefix.

#### Route Index
A table of all routes currently in `world/data/tarim-shaiel-routes.geojson`. Columns: route ID, label, distance (km), estimated travel time (at 30 km/day caravan pace). Straight-line (2-point) segments are flagged with `~`. Clicking a row flies the map to that route and highlights it.

#### Edit Coords *(devserver required)*
For updating the lat/lon of an existing location without editing YAML by hand. Click any pin on the map → the location loads in the Edit Coords panel. Drag the pin to its correct position, or type new coordinates directly. A badge on the tab shows how many unsaved edits are pending. "Save" sends a `PUT /api/locations/{slug}/coordinates` to the devserver, which writes the new coordinates into the `.md` file's frontmatter.

---

### Devserver Write-Back Endpoints

| Endpoint | Method | What it does |
|---|---|---|
| `/api/locations/{slug}/coordinates` | PUT | Writes new lat/lon into `world/locations/{slug}.md` frontmatter |
| `/api/locations/create` | POST | Creates a new location stub via `map.py location` (writes `.md`, rebuilds GeoJSON) |
| `/api/routes/add` | POST | Adds route segments via `map.py route` (writes GeoJSON, snaps to roads) |
| `/api/rebuild/locations` | POST | Runs `build.py locations` — regenerates `docs/world.html` |
| `/api/rebuild/workshop` | POST | Runs `build.py workshop` — regenerates `map-workshop.html` |

The workshop sidebar exposes these as buttons: **Create Location** (Add Point tab), **Add Route** (Plan Route tab), **Edit Coords** drag-and-confirm (Edit Coords tab), **Rebuild Locations** and **Rebuild Workshop** (Edit Coords tab). All show inline status and fall back gracefully when the devserver is not running.

---

### Authoring New Routes

Routes are LineString features in `world/data/tarim-shaiel-routes.geojson`. Three ways to add them:

**Via Plan Route tab → Add Route button** (recommended, devserver required):
Click waypoints on the map, click Add Route. The devserver runs `map.py route` which calls OSRM to snap to real road geometry and rebuilds everything. No terminal needed.

**Via terminal** (fallback when devserver is not running):
```bash
python utilities/map.py route slug-a slug-b slug-c   # snaps + rebuilds
```

**Hand-edit the GeoJSON** (for simple or approximate routes):
Add a feature directly to the file. A 2-point segment (start → end only) is flagged in the Route Index as `~` (straight-line estimate). Then: `python utilities/build.py workshop`.

---

### What the Workshop Is NOT

- Not the public-facing world map (`docs/world.html`) — that is built by `generate_locations_html.py` and served by Netlify
- Not accessible to players — it is gitignored and never pushed
- Not a replacement for editing `.md` files — it is a coordinate and route authoring aid

---

## Related Issues

- [#292](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/292) — This workflow doc + workshop registration
- [#293](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/293) — Route-from-points builder (workshop feature)
- [#294](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/294) — Drag-to-update coordinates + local devserver
