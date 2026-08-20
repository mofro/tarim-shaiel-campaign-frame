# Map Pipeline Skill

Use this skill when the user asks to:
- Add a location to the world map
- Add a route or road segment
- Snap routes to roads
- Place waystation candidates
- Rebuild the world map or location pages
- Find coordinates for a new location

---

## Critical: Coordinate Format

`location:` frontmatter is **lat-first**: `[lat, lon]`
GeoJSON coordinates are **lon-first**: `[lon, lat]`

The generators handle the flip automatically. Always write location files lat-first.

To convert DMS (degrees/minutes/seconds) to decimal:
`DD = degrees + minutes/60 + seconds/3600`
Positive = N/E, negative = S/W. Confirm sign before creating a file — wrong hemisphere is a silent data error.

---

## Adding a Location

1. Create `world/locations/<slug>.md` (slug = URL-safe lowercase name, hyphens for spaces)
2. Required frontmatter fields:
   ```yaml
   title: Display Name
   project: TTRPG_Tarim_Shaiel
   domain: world
   doc_type: canon
   content_type: location
   visibility: public
   status: draft
   created: YYYY-MM-DD
   last_updated: YYYY-MM-DD
   fantasy_name: Display Name
   name: Display Name
   location:
   - <lat>
   - <lon>
   mapmarker: <town|caravanserai|fortress|poi|hamlet|village|city|landmark>
   tags: []
   ```
3. Run: `python3 utilities/locations/generate_locations_html.py`
4. Commit to **main** as `world: add <name> location stub`

---

## Adding a Route Segment

Endpoints must already have location files in `world/locations/`.

```bash
# Interactive (no args in a TTY — prompts for everything)
python3 utilities/routes/add_route.py

# Scripted: two endpoints → one segment
python3 utilities/routes/add_route.py <slug-a> <slug-b>

# Multi-hop: N slugs → N-1 consecutive segments
python3 utilities/routes/add_route.py karmana nur-ata rabati-malik

# Flags
--spur            # use route_spur_ prefix instead of route_seg_
--description ""  # segment description
--color "#hex"    # stroke color (default: #8B7355)
--dry-run         # preview without writing
--force           # overwrite existing segment ID
```

Segment IDs are `route_seg_<slug-a>_<slug-b>` or `route_spur_<slug-a>_<slug-b>`.

After creating, snap to roads:
```bash
python3 utilities/routes/generate_routes.py --segment route_seg_<a>_<b>
```

Then place waystation candidates:
```bash
python3 utilities/routes/place_waystations.py --segment route_seg_<a>_<b>
```

Route/waystation data files are **infra path** (feature branch → PR).

---

## Generator Commands

```bash
# World map + all location pages
python3 utilities/locations/generate_locations_html.py

# Route geometry (OSRM foot profile)
python3 utilities/routes/generate_routes.py [--segment <id>]

# Waystation candidates (Overpass API)
python3 utilities/routes/place_waystations.py [--segment <id>] [--interval 30] [--radius 15] [--deviation 4]

# Full site rebuild (what Netlify runs)
python3 utilities/build.py
```

---

## Finding Coordinates (GM Mode)

```bash
python3 -m http.server 8000 --directory docs
```
Open `http://localhost:8000/world.html?gm=1` — coordinate picker is top-left. Click map to read lat/lon.

---

## Commit Paths

| Work | Branch | Prefix |
|---|---|---|
| New location `.md` file | main directly | `world:` |
| Location GeoJSON edits | main directly | `world:` |
| Generator scripts (`utilities/`) | feature branch → PR | `infra:` or `pipeline:` |
| Route/waystation GeoJSON data | feature branch with scripts | `infra:` |
