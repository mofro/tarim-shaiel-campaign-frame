---
type: reference
purpose: Quick reference for marker types and how they work
created: 2025-12-13
last_updated: 2025-12-13
status: verified_working
---

# Marker Types & Configuration Guide

## How Markers Work (The Real Flow)

1. **Define marker types in plugin settings** (one-time setup)
2. **Add `mapmarker: [type]` to Location Notes** (frontmatter field)
3. **Maps load locations and apply styling automatically** (plugin reads `mapmarker` and matches to settings)

---

## Configured Marker Types

These are the marker types currently defined in Obsidian Leaflet plugin settings. Use the exact name (case-sensitive) in Location Notes.

| Marker Name | Icon | Color | Use For | Example |
|------------|------|-------|---------|---------|
| `city` | fa-building | Blue | Major trade hubs, permanent settlements | Samarkand, Kashgar, Bukhara |
| `sacred-site` | fa-gopuram | Gold | Temples, monasteries, pilgrimage destinations | Dunhuang, Kucha, Buddhist sites |
| `marker-caravanserai` | fa-campground | Orange | Way stations, rest points, caravanserais | Caravanserai of Five Silks |
| `marker-natural-feature` | fa-mountain | Green | Mountains, deserts, water features, landmarks | Tian Shan, Taklamakan Desert |
| `marker-route-node` | fa-map-pin | Red | Way points along trade routes, minor settlements | Jade Gate, Miran, Turfan |
| `marker-fortress` | fa-chess-rook | Purple | Military installations, defensive structures, citadels | Mountain fortress, defensive outpost |
| `marker-dungeon` | fa-dungeon | Dark Brown | Dungeons, caves, underground locations | Lost Vault, underground complex |

---

## How to Use in Location Notes

### Add the `mapmarker` Field

In the frontmatter of any Location Note, add:

```yaml
---
name: Samarkand
location: [39.65, 66.97]
type: city
mapmarker: city              # ← This field controls the marker icon
created: 2025-12-13
last_updated: 2025-12-13
tags:
  - player-visible
---
```

**Important:** The value must match EXACTLY (case-sensitive) what's in plugin settings.

### Without `mapmarker`

If you omit the field, the location still appears on maps but uses the default tan marker:

```yaml
---
name: Unknown Place
location: [40, 70]
type: location
# No mapmarker field = default tan marker
---
```

---

## Adding New Marker Types

To add more marker types in the future:

1. **Open Obsidian Settings** → Community plugins → Obsidian Leaflet
2. **Scroll to "Additional Map Markers"**
3. **Click "Add marker"** and fill in:
   - **Marker Name:** Name to use in Location Notes (case-sensitive)
   - **Icon Name:** Font Awesome Free icon (e.g., `fa-chess-rook`)
   - **Marker Color:** Color name or hex code
   - Leave other fields blank
4. **Save and restart Obsidian**
5. **Use in Location Notes:** Add the marker name to `mapmarker` field

---

## Available Font Awesome Free Icons

For marker icons, use Font Awesome Free icons only:
- `fa-building` – Buildings, cities
- `fa-gopuram` – Temples, shrines
- `fa-dungeon` – Dungeons, caves
- `fa-mountain` – Mountains, natural features
- `fa-map-pin` – Generic location pin
- `fa-chess-rook` – Fortresses, defensive structures
- `fa-campground` – Caravanserai, way stations
- `fa-water` – Water sources, oases
- `fa-house` – Settlements, villages

Check Font Awesome Free at: https://fontawesome.com/icons (toggle to "Free" filter)

---

## Map Code Block (No Changes Needed)

Once Location Notes have `mapmarker` fields, maps automatically apply the styling:

```leaflet
id: my-map
markerFolder: world/locations
lat: 38
long: 80
defaultZoom: 5
height: 600px
```

That's it. The plugin:
1. Loads all notes in `/world/locations/`
2. Reads each note's `mapmarker` field
3. Applies the matching icon/color from plugin settings
4. Renders on map

---

## Tile Style Customization

To use a different tile server for a specific map:

```leaflet
id: my-map
markerFolder: world/locations
tileServer: https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png
lat: 38
long: 80
defaultZoom: 5
height: 600px
```

**Other tile options:**
- OpenTopoMap: `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png` (topographic)
- Stamen Toner: `https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png` (minimal, B&W)
- Standard OSM: `https://tile.openstreetmap.org/{z}/{x}/{y}.png` (default street map)

---

## Example: Creating a New Location with Marker

```markdown
---
name: The Lost Vault
location: [38.5, 70.3]
type: dungeon
mapmarker: marker-dungeon      # Uses the dark brown dungeon icon
created: 2025-12-13
last_updated: 2025-12-13
danger_level: 4
narrative_weight: true
description: "Underground complex rumored to contain treasures from the fallen age."
tags:
  - gm-only
  - narrative-important
---

# The Lost Vault

A dangerous underground location...
```

Open the map → marker appears with dark brown dungeon icon.

---

## Quick Reference: Adding a Location

1. Create file: `/world/locations/my_location.md`
2. Add frontmatter:
   ```yaml
   ---
   name: Location Name
   location: [lat, long]
   type: city
   mapmarker: city             # Pick from configured types
   created: 2025-12-13
   last_updated: 2025-12-13
   tags:
     - player-visible
   ---
   ```
3. Save
4. Maps automatically pick it up (if using `markerFolder: world/locations`)

---

## Troubleshooting

**Markers appear with default tan icon instead of custom icon:**
- Check: Does Location Note have `mapmarker: [type]`?
- Check: Is the value exactly (case-sensitive) what's in plugin settings?
- Check: Have you restarted Obsidian?

**Marker type not recognized in plugin settings:**
- The marker type must exist in Obsidian Leaflet settings
- Go to Settings → Community plugins → Obsidian Leaflet → Additional Map Markers
- Verify the "Marker Name" matches exactly

**Can't find icon I want:**
- Use Font Awesome Free only (check https://fontawesome.com/icons with "Free" filter)
- Pro icons won't work in this plugin version

---

## Summary

- **Simple workflow:** `mapmarker` field in Location Notes → plugin applies icon from settings → maps show styled markers
- **No fancy syntax** – just a field value that matches plugin settings
- **Expandable** – add new marker types in plugin settings as needed
- **Reliable** – markers appear automatically when you create Location Notes with the field
