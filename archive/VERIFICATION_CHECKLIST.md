---
type: verification-checklist
purpose: Track test results and identify any issues before updating documentation
created: 2025-12-13
last_updated: 2025-12-13
---

# System Verification Checklist

## What We Have Set Up

✅ **Directory Structure**
- `/world/locations/` – Created (contains 3 test Location Notes)
- `/world/maps/` – Created (contains test Dataview & Leaflet notes)
- `/world/data/archives/` – Created (for storing session exports)

✅ **Test Location Notes Created** (with marker types)
- `samarkand.md` – Central Asian trade hub | `marker_type: city`
- `kashgar.md` – Trade crossroads city | `marker_type: city`
- `dunhuang.md` – Sacred Buddhist site | `marker_type: sacred-site`

✅ **Plugins Installed**
- Dataview
- Obsidian Leaflet
- Mapbox Location Image
- Data Files Editor

✅ **Test Verification Notes**
- `test_dataview.md` – Queries all 3 locations; should show table
- `test_leaflet.md` – Renders interactive map with OpenTopoMap tiles and marker type icons

✅ **Marker Types Defined**
- `city` (Blue building icon) – Trade hubs, major cities
- `sacred-site` (Gold temple icon) – Temples, monasteries, pilgrimage sites
- `caravanserai` (Orange tent icon) – Way stations, rest points
- `natural-feature` (Green mountain icon) – Mountains, deserts, landmarks
- `route-node` (Red map-pin icon) – Waypoints along routes
- `fortress` (Purple castle icon) – Military installations

✅ **Tile Customization**
- Default: OpenTopoMap (topographic with terrain contours)
- Per-map override capability implemented
- Other tile styles documented (Stamen Toner, USGS Topo, Mapnik)

---

## Verification Steps (Run These Now)

### Test 1: Dataview Functionality

**Action:** Open `/world/maps/test_dataview.md` in **Reading Mode** (Cmd+E)

**Expected Result:**
Table showing 3 locations (Dunhuang, Kashgar, Samarkand) with coordinates and descriptions.

**If NOT working:**
- [ ] Check: Dataview plugin enabled (Settings → Community plugins)
- [ ] Check: Restart Obsidian completely
- [ ] Check: Syntax in query

---

### Test 2: Leaflet + OpenTopoMap + Marker Types

**Action:** Open `/world/maps/test_leaflet.md` in **Reading Mode** (Cmd+E)

**Expected Result:**
- Interactive topographic map (OpenTopoMap tiles visible)
- Three markers with distinct icons:
  - **Samarkand** [39.65, 66.97] – Blue building (city type)
  - **Kashgar** [39.65, 75.99] – Blue building (city type)
  - **Dunhuang** [40.15, 94.67] – Gold temple (sacred-site type)
- Map can be zoomed/panned
- Clicking markers shows location names

**Verification checklist:**
- [ ] Topographic terrain contours visible (not flat street map)
- [ ] Marker icons differ by type (blue buildings vs. gold temple)
- [ ] Map is interactive (zoom, pan, click)
- [ ] Marker labels appear on click

**If NOT working:**
- [ ] Check: Obsidian Leaflet plugin enabled
- [ ] Check: Location coordinates valid WGS84 format
- [ ] Check: `marker_type` field present in Location Notes
- [ ] Check: Restart Obsidian completely
- [ ] Check: Browser console for errors (Advanced → Developer Tools → Console)

---

### Test 3: Tile Style Override (Per-Map)

**Action:** Create a test map with different tile style

Create `/world/maps/test_tile_override.md`:

```markdown
---
type: test-map-tiles
---

# Test: Stamen Toner Tiles

```leaflet
id: test-toner
markerFolder: world/locations
markerTag: test
tileServer: https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png
lat: 38
long: 80
defaultZoom: 5
height: 600px
```
```

**Expected Result:**
- Black and white map (Stamen Toner style)
- Same markers from test_leaflet.md
- Different visual appearance but same functionality

**If works:** ✅ Per-map tile override working

---

## Issues Encountered (Track Here)

### Dataview
- [ ] No issues
- [ ] (Describe any found here)

### Leaflet/Marker Icons
- [ ] No issues
- [ ] (Describe any found here)

### OpenTopoMap Tiles
- [ ] No issues
- [ ] (Describe any found here)

### Marker Type Configuration
- [ ] No issues
- [ ] (Describe any found here)

---

## Configuration Notes

### Plugin Settings (Obsidian Leaflet)

Current default tile server in plugin: OpenTopoMap

To verify/modify:
1. Settings → Community plugins → Installed plugins
2. Click "Obsidian Leaflet" settings icon
3. Look for "Tile Server" or map settings
4. Confirm default is OpenTopoMap

### Marker Type Definitions

Marker types are defined by `marker_type` field in Location Note frontmatter. No additional plugin configuration needed—Obsidian Leaflet reads the field and matches icons based on Font Awesome availability.

---

## Data Source Status

✅ **regions.json** – Valid and ready for bulk conversion
- 13+ location entries available
- All have valid WGS84 coordinates
- Can populate Location Notes as needed

---

## Next Steps (Once Both Tests Pass)

1. **Bulk convert** more locations from regions.json to Location Notes
2. **Test trade route rendering** (line features, not just points)
3. **Create session-specific maps** (filtered by tags)
4. **Test GeoJSON export** (manual conversion)
5. **Update main documentation** with tested patterns

---

## Documentation Created

- ✅ SETUP_AND_CONFIGURATION.md (system setup guide)
- ✅ LOCATION_NOTE_SCHEMA.md (Location Note structure)
- ✅ MARKER_TYPES_AND_TILES.md (marker/tile reference) ← NEW
- ✅ MAPPING_ARCHITECTURE.md (system overview)
- ✅ PUBLISHING_WORKFLOWS.md (export workflows)
- ✅ DATAVIEW_QUERIES.md (query examples)
- ✅ VERIFICATION_CHECKLIST.md (this file)

---

## Summary

**Ready to test:**
- ✅ Dataview queries
- ✅ Leaflet maps with OpenTopoMap tiles
- ✅ Marker types by category
- ✅ Per-map tile override
