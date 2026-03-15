---
title: Setup & Configuration Guide
project: TTRPG_Tarim_Shaiel
type: operational_reference
status: in_development
created: 2025-12-13
last_updated: 2025-12-13
---

# Setup & Configuration: Tarim-Shaiel Mapping System

## Purpose
Document the minimum required setup to run the Tarim-Shaiel interactive mapping system. This guide is for initial installation and for replication across machines/vaults.

---

## System Requirements

### Software
- **Obsidian.md** (latest stable version)
- **Internet connection** (for tile server data, external documentation links)
- macOS, Windows, or Linux (tested on macOS)

**Note:** External tools (Python scripts for batch GeoJSON generation, text editors for manual GeoJSON editing) are optional and documented separately as needs emerge.

---

## Required Obsidian Plugins

Install these community plugins via Obsidian Settings → Community plugins → Browse.

### 1. **Dataview**
- **Purpose:** Query Location Notes; generate tables for Dataview dashboards and GeoJSON data exports
- **Repository:** https://github.com/blacksmithgu/obsidian-dataview
- **Installation:** Search "Dataview" in community plugins browser, install
- **Configuration:** No special setup required; works out-of-box
- **Status:** ✅ Installed in Tarim-Shaiel vault

### 2. **Obsidian Leaflet**
- **Purpose:** Render interactive maps in Obsidian notes using Leaflet.js
- **Repository:** https://github.com/javalent/obsidian-leaflet
- **Installation:** Search "Obsidian Leaflet" in community plugins browser, install
- **Configuration:** No required setup; optional settings in plugin preferences:
  - Tile server (default: Stamen Terrain; can switch to OpenStreetMap, others)
  - Dark mode toggle
  - See `/mnt/skills/user/obsidian-leaflet-mapping/SKILL.md` for advanced mapping patterns
- **Status:** ✅ Installed in Tarim-Shaiel vault
- **Documentation:** https://github.com/javalent/obsidian-leaflet/blob/main/README.md

### 3. **Mapbox Location Image** (Optional but Installed)
- **Purpose:** Embed static Mapbox images with location pins in notes
- **Repository:** https://obsidian-location.czichon.cloud/
- **Installation:** Already installed in Tarim-Shaiel vault
- **Configuration:** Requires Mapbox API token for full functionality (optional)
- **Documentation:** https://obsidian-location.czichon.cloud/docs/usage/settings
- **Status:** ✅ Installed; can be used for supplementary location visualization
- **Note:** Secondary to Leaflet; Leaflet is primary for interactive maps

### 4. **Data Files Editor** (Optional but Installed)
- **Purpose:** Edit JSON files directly within Obsidian with syntax highlighting
- **Installation:** Already installed in Tarim-Shaiel vault
- **Status:** ✅ Available for editing `regions.json` and GeoJSON files if needed

---

## Optional Plugins (Not Required)

The following are installed in your vault but not required for core mapping functionality:

- **Moulinette** – Content generation (not used for mapping)
- Others as discovered

---

## Directory Structure

Required directories for the mapping system:

```
/Users/mo/Documents/Games/HeroHeaven/
├── world/
│   ├── locations/           [CREATE THIS - Location Notes live here]
│   ├── maps/                [CREATE THIS - Leaflet map notes live here]
│   ├── data/                [EXISTS - GeoJSON, KML exports]
│   ├── images/              [EXISTS - map reference images]
│   └── [other world docs]   [EXISTING]
├── utilities/               [EXISTS - Python scripts (optional)]
└── [other project dirs]
```

**What to create:**
```bash
mkdir -p /Users/mo/Documents/Games/HeroHeaven/world/locations
mkdir -p /Users/mo/Documents/Games/HeroHeaven/world/maps
```

---

## Configuration Checklist

### Obsidian Vault Setup
- [ ] Dataview plugin installed and enabled
- [ ] Obsidian Leaflet plugin installed and enabled
- [ ] Mapbox Location plugin installed and enabled (optional)
- [ ] Data Files Editor installed and enabled (optional)
- [ ] Directories created: `/world/locations/`, `/world/maps/`

### Plugin Verification
- [ ] Open Obsidian Settings → Community plugins → Installed plugins
- [ ] Confirm all required plugins show as "Enabled"
- [ ] Restart Obsidian to ensure plugins load properly

### Initial Test (See "Verification" Section Below)
- [ ] Create a test Location Note
- [ ] Create a test Leaflet map
- [ ] Verify rendering

---

## Key Files & References

### Documentation (Read These First)
1. **MAPPING_ARCHITECTURE.md** – System overview & design
2. **LOCATION_NOTE_SCHEMA.md** – How to create Location Notes
3. **PUBLISHING_WORKFLOWS.md** – How to generate/export maps
4. **DATAVIEW_QUERIES.md** – How to query Location Notes

### Plugin Documentation
- **Obsidian Leaflet Guide:** https://github.com/javalent/obsidian-leaflet/blob/main/README.md
- **Leaflet Skill (in this project):** `/mnt/skills/user/obsidian-leaflet-mapping/SKILL.md`
- **Dataview Docs:** https://blacksmithgu.github.io/obsidian-dataview/
- **Mapbox Docs:** https://docs.mapbox.com/playground/static/
- **Mapbox Obsidian Plugin:** https://obsidian-location.czichon.cloud/docs/usage/settings

---

## Verification: Testing the Setup

### Test 1: Verify Dataview Works

1. Create a test note at `/world/locations/test_location.md`:

```markdown
---
name: Test City
location: [39.5, 66.5]
type: city
created: 2025-12-13
last_updated: 2025-12-13
tags:
  - test
---

# Test City

A location to verify the mapping system works.
```

2. Create a query note at `/world/test_dataview_query.md`:

```markdown
# Test Dataview Query

```dataview
TABLE name, location, type
FROM "world/locations"
SORT name
```
```

3. Open in Reading Mode (Cmd+E on macOS)
4. **Expected result:** Table shows the test location with name, coordinates, and type
5. **If it works:** ✅ Dataview is functioning
6. **If not:** Check Dataview plugin is enabled; restart Obsidian

### Test 2: Verify Leaflet Works

1. Create a test map note at `/world/maps/test_map.md`:

```markdown
---
type: leaflet-map
---

# Test Leaflet Map

```leaflet
id: test-map
markerFolder: world/locations
markerTag: test
lat: 39.5
long: 66.5
minZoom: 3
maxZoom: 12
defaultZoom: 6
height: 600px
```
```

2. Open in Reading Mode (Cmd+E on macOS)
3. **Expected result:** Interactive map appears with the test location marked
4. **If it works:** ✅ Leaflet is functioning
5. **If not:** 
   - Check plugin is enabled
   - Verify location coordinates are valid [lat, long] format
   - Restart Obsidian
   - Check browser console for errors (Advanced → Developer Tools)

### Test 3: Verify GeoJSON Conversion (Manual)

1. Query test locations using the Dataview table from Test 1
2. Copy the table data
3. Manually convert to GeoJSON or use https://geojson.io to test format
4. **Expected result:** Valid GeoJSON with Point features
5. **If it works:** ✅ Manual GeoJSON generation is possible

---

## External Tools (Future)

These are optional and documented only once you have actual experience with them:

- **Python 3** – For batch GeoJSON generation and KML transpilation scripts (see `/utilities/`)
- **Text editor (e.g., Windsurf)** – For editing large GeoJSON files outside Obsidian if needed

These are completely optional. The core system works without them.

---

## Troubleshooting

### Dataview queries not showing tables
- Ensure plugin is enabled: Settings → Community plugins → Dataview → toggle On
- Verify query syntax (check DATAVIEW_QUERIES.md for examples)
- Restart Obsidian
- Check for typos in `FROM "world/locations"` path

### Leaflet maps not rendering
- Verify plugin is enabled: Settings → Community plugins → Obsidian Leaflet → toggle On
- Check that Location Notes have valid `location: [lat, long]` in frontmatter
- Ensure GeoJSON files are valid (use https://geojson.io to validate)
- Coordinates should be WGS84 format (latitude between -90 and 90, longitude between -180 and 180)
- Restart Obsidian

### Markers appearing as "Untitled Folder" in KML
- This is a KML formatting issue (incorrect XML tags)
- Use KML generation scripts in `/utilities/` or verify export tool
- See PUBLISHING_WORKFLOWS.md for KML troubleshooting

### Plugin won't install or enable
- Restart Obsidian completely (quit and reopen)
- Check that you're using community plugins browser, not attempting manual installation
- Verify community plugins are enabled in Settings → Community plugins

### Obsidian Leaflet documentation
- **GitHub:** https://github.com/javalent/obsidian-leaflet
- **Skill guide:** `/mnt/skills/user/obsidian-leaflet-mapping/SKILL.md`

---

## Next Steps

Once setup is verified:

1. **Create initial Location Notes** in `/world/locations/` following LOCATION_NOTE_SCHEMA.md
2. **Test Dataview queries** using examples from DATAVIEW_QUERIES.md
3. **Create Leaflet map notes** in `/world/maps/` following patterns in PUBLISHING_WORKFLOWS.md
4. **Begin populating world data** by creating Location Notes for key cities, landmarks, routes, etc.

---

## Summary: What's Installed & Working

✅ **Obsidian Leaflet** – Interactive maps in notes  
✅ **Dataview** – Location Note queries & dashboards  
✅ **Mapbox Location** – Static location images (optional)  
✅ **Data Files Editor** – JSON editing (optional)  

✅ **Directories created** – `/world/locations/`, `/world/maps/`  

✅ **Documentation** – 4 core docs + skill guide available  

---

## Replication for Future Setups

To replicate this system on a new machine or vault:

1. Create `/world/locations/`, `/world/maps/`, `/world/data/` directories
2. Install Dataview plugin
3. Install Obsidian Leaflet plugin
4. Copy this documentation and LOCATION_NOTE_SCHEMA.md into the vault
5. Create a test Location Note and verify with Test 1 above
6. Create a test Leaflet map and verify with Test 2 above
7. You're ready to populate Location Notes

---

## Notes

- **Lore Keeper** monitors `/world/locations/` for new entries and maintains consistency
- **All Location Note data is persistent** (stored as markdown files in vault)
- **Map rendering is dynamic** (Dataview & Leaflet read current Location Notes each time you open a map)
- No external databases, APIs, or logins required (except optional Mapbox token)
