---
title: Georeferencing the Fantasy World Map
project: TTRPG_Tarim_Shaiel
domain: world
doc_type: operational
content_type: reference
visibility: internal
status: canon
created: 2026-07-22
last_updated: 2026-07-22
tags: []
---

# Georeferencing the Fantasy World Map

How the Tarim-Shaiel Wonderdraft map gets tied to real lat/long, so that every location's frontmatter `location: [lat, lon]` places correctly on the live site's base map. Written after a full scoping pass on `HeroHeaven-1yu` / GitHub #275 — read that issue for the "why," this doc is the "how."

## The problem this solves

The production art (`images/places/maps/tarim-shaiel.wonderdraft_map.png`, 6880x2880 -- a native Wonderdraft "Export Map" output, not a screenshot) has no coordinate system of its own. To place a location marker on it from a real lat/long, we need a **pixel <-> real-world coordinate transform**. That transform comes from Ground Control Points (GCPs): pairs of (pixel on the art) <-> (known real lat/long).

A prior attempt (`utilities/world/georeference_map.py`) built this from 5 hardcoded GCPs fit with a simple two-axis linear regression, measured against a reference image (`reference_map.png`) that turned out to have a **different aspect ratio** than the production PNG (6547x2682 vs 6880x2880) -- meaning its GCP pixel coordinates were never valid against the actual art. That script is superseded by the process below.

## The core problem: the art has no cities on it

The Wonderdraft PNG shows terrain, mountain glyphs, and a handful of labeled water bodies -- no settlement markers. "Click where the artist drew Tashkent" isn't a measurement; there's nothing there to click.

**The fix**: a Google Maps satellite screenshot with the TARIM-SHAIEL title/compass/fantasy labels composited on top (kept locally as e.g. `~/Desktop/Untitled.png`, never committed to git -- see Hygiene below) was confirmed to be **exactly 6880x2880 -- pixel-identical dimensions to the production PNG** (verified via `sips`, 0.00% difference), and spot-checked via precise same-coordinate crops at multiple regions to have real (not coincidental) positional correspondence. It has actual city labels (Tashkent, Almaty, Bishkek, etc.) because it's a real satellite view.

So there are three images in play:
1. **The click source** -- the Google Maps overlay screenshot. Has real cities to click. Shares the production PNG's exact pixel grid.
2. **The reference layer** -- clean real-geography data (Natural Earth), used to capture each GCP's *real* lat/long automatically.
3. **The production art** -- the actual clean Wonderdraft PNG. Never touched during GCP-clicking; receives the final computed transform.

## Setup (already done as of 2026-07-22)

- QGIS installed: `/Applications/QGIS-final-4_2_0.app` (via `brew install --cask qgis`)
- Natural Earth reference data downloaded and clipped to the Silk Road region (lon 45-130, lat 20-55), sitting in `utilities/world/natural_earth/clipped/`:
  - `ne_10m_coastline_clipped.shp` (281 features)
  - `ne_10m_lakes_clipped.shp` (243 features)
  - `ne_10m_rivers_lake_centerlines_clipped.shp` (250 features)
  - `ne_10m_populated_places_clipped.shp` (487 features, `SCALERANK <= 6` filter to keep it to reasonably major places)
  - Source: naturalearthdata.com, public domain, no auth required, 10m resolution
  - These load directly into QGIS as vector layers -- no pre-rendered reference image needed.

## The GCP workflow

1. Open QGIS. `Layer > Add Layer > Add Vector Layer`, load the four clipped shapefiles above. This is your georeferenced backdrop -- QGIS knows its real coordinates already.
2. `Layer > Georeferencer`. Click **"Open raster"** and load the click-source image (the Google Maps overlay, not the production PNG).
3. For each anchor point (see candidate list below):
   - Click **"Add GCP Point"**, then click that point on the click-source image in the Georeferencer window.
   - Click **"From map canvas"** (pencil icon) -- this switches focus to the main QGIS window. Click the *same real-world location* on the Natural Earth backdrop. QGIS captures the real lat/long automatically -- no manual coordinate typing.
   - There's a checkbox to auto-hide the Georeferencer window during this step, to ease the back-and-forth.
4. Repeat for ~8-12 points, spread across the whole map rather than clustered (extrapolation toward un-anchored edges is exactly what caused the original bug).
5. QGIS can generate a report showing RMS error / residuals after the transform runs. Watch for outliers -- a point with much higher residual than the rest is worth re-clicking or dropping.
6. Decide the transform order based on the residual pattern: a straight **linear** fit if residuals are small and evenly distributed; a **thin-plate-spline (TPS)** warp if the hand-painted map has real local distortion the linear model can't absorb (residuals cluster or grow in one direction). Threshold: if linear residuals exceed roughly 20km of real-world error, use TPS instead.
7. Export the georeferenced result as a GeoTIFF.

## Candidate GCP anchor points

Real coordinates already confirmed (no need to look these up again):

**Cities and fantasy-name crosswalk** (`world/data/regions.json`): Samarkand (Skamarketh), Bukhara (Bukhgrath), Balkh (Khalkresh), Merv (Merk-Shahr), Tashkent (Taskhren), Urgench (Urgkesh), Dunhuang (Dun-Shaiel), Chang'an/Xi'an (Chang-Shai), Kashgar (Kashkar), Khotan (Khotaneth), Kucha (Ku-Thane), Yarkand (Yar-Khan), Turfan (Tur-Shai), Niya (Niya-Khan)

**Mountain ranges** (visible on the art as glyph clusters, same crosswalk): Hindu Kush / Kush-Kamen (36.0, 70.0), Pamir Mountains / Pamir-Zhel (37.0, 72.0), Karakoram Range / Karak-Mor (35.0, 78.0)

**Water body**: Lake Balkhash / Balkh-Kamen (46.5, 74.9) -- confirmed via `world/locations/balkh-kamen.md`

**New stub locations** (`world/locations/{slug}.md`, `visibility: gm_secrets`, `fantasy_name: TBD`), added specifically as well-spread anchors:
- Almaty (43.2220, 76.8512), Bishkek (42.8746, 74.5698), Dushanbe (38.5598, 68.7870), Ashgabat (37.9601, 58.3261) -- fill out the Central Asian core
- Beijing (39.9042, 116.4074), Chengdu (30.5728, 104.0668) -- distant anchors specifically chosen to ground the fit at the map's far eastern and southern edges rather than clustering near the center

## After georeferencing: applying the transform to the production art

The click-source image and the production PNG share an identical, verified pixel grid (same dimensions, spot-checked alignment). So: run the same georeferencing transform QGIS computed against the click-source, but apply it to `tarim-shaiel.wonderdraft_map.png` instead for the actual output GeoTIFF. The click-source image itself is discarded after this step -- it never ships.

```bash
# Illustrative -- exact GCP list comes from the QGIS session above
gdal_translate -of GTiff -a_srs EPSG:4326 \
  -gcp <px1> <py1> <lon1> <lat1> \
  -gcp <px2> <py2> <lon2> <lat2> \
  ... \
  images/places/maps/tarim-shaiel.wonderdraft_map.png \
  images/places/maps/tarim-shaiel_georef.tif

# Linear:
gdalwarp -r bilinear -t_srs EPSG:4326 tarim-shaiel_georef.tif tarim-shaiel_warped.tif
# or, if TPS was chosen:
gdalwarp -tps -r bilinear -t_srs EPSG:4326 tarim-shaiel_georef.tif tarim-shaiel_warped.tif
```

## Raster tile generation

```bash
gdal2tiles.py -p mercator -z 5-8 tarim-shaiel_warped.tif docs/tiles/
```

Zoom range **5-8**, not wider -- verified against actual usage: every one of 44 location files uses `map_min_zoom: 6` / `map_max_zoom: 8` with zero variance, and the world map itself is fixed at zoom 5. The source PNG's native resolution (~975 m/px) sits almost exactly at z7 -- z9/z10 would be genuine upscale blur, not real detail. If deeper zoom is ever wanted, re-export from Wonderdraft at a higher resolution multiplier (4x instead of the current 2x) rather than generating more tile levels from the same source pixels.

Commit the resulting tile pyramid to `docs/tiles/` as a static, git-tracked asset -- it only needs regenerating when the base map itself changes, not on every content build.

## MapLibre integration

Replace the MapTiler style URL (see `MAPTILER_STYLE_URL` in `utilities/locations/location_components.py`) with a local style JSON using a `raster` source pointing at `docs/tiles/{z}/{x}/{y}.png`, with `bounds` set from the georeferencing output. Existing GeoJSON overlay layers (locations, routes, regions) are unaffected -- they're added via separate `map.addLayer` calls after the base style loads, independent of the base map's own source.

## Maintenance: if the Wonderdraft map is ever repainted

Only the GCP-and-tiling steps need redoing -- re-click GCPs on the new export (same anchor list above, ~15-30 min), re-run the `gdal_translate`/`gdalwarp`/`gdal2tiles.py` commands, replace the tile files, update the bounds in the style JSON. Everything else in this doc (the Natural Earth reference data, the anchor list, this runbook itself) stays valid. Treat (production image + its tile pyramid) as one versioned unit -- if the canvas changes, don't mix an old tile pyramid with new art or vice versa.

## Hygiene

The click-source Google Maps screenshot is never committed to this repo (it's a screenshot of Google's satellite imagery; this repo is public). It lives locally only, used solely for the GCP-clicking session above, then discarded.
