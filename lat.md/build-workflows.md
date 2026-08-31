---
title: Build Workflows — Scenario Reference
project: TTRPG_Tarim_Shaiel
domain: utilities
doc_type: operational
content_type: reference
visibility: internal
status: canon
created: 2026-08-31
last_updated: 2026-08-31
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
| Interactive location/route editing (drag-to-update) | `python utilities/devserver.py` *(not yet built — see GitHub #294)* |
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
- `workshop` builds `docs/map-workshop.html` (the GM route-planning tool). Also inlines location data in-memory from `.md` files. Routes come from `world/data/tarim-shaiel-routes.geojson`.
- `geojson` generates `world/data/tarim-shaiel-locations.geojson` as a standalone snapshot — used by external tools, not by either HTML generator.

Running `build.py locations` does **not** update the workshop. Running `build.py workshop` does **not** update `world.html`. Run both, or use `build.py all`.

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

## Related Issues

- [#292](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/292) — This workflow doc + workshop registration
- [#293](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/293) — Route-from-points builder (workshop feature)
- [#294](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/294) — Drag-to-update coordinates + local devserver
