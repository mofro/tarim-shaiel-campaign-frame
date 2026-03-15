---
title: Publishing Workflows - From Location Notes to Map Exports
project: TTRPG_Tarim_Shaiel
type: workflow_documentation
status: in_development
created: 2025-12-08
last_updated: 2025-12-08
---

# Publishing Workflows: Generating & Exporting Maps

## Overview
Publishing workflows move Location Notes through multiple transformations to produce GM/player-facing maps, GeoJSON exports, and KML files for Google Earth. This document outlines **step-by-step processes**, **decision points**, and **verification steps**.

---

## Workflow 1: Generate Master GeoJSON from Location Notes

### Purpose
Create a canonical GeoJSON file from all Location Notes in `/world/locations/`. This is the intermediate format that feeds into Leaflet maps, KML exports, and reference queries.

### Prerequisites
- Location Notes exist in `/world/locations/`
- Dataview plugin is installed and working
- Optional: Python script for batch conversion (see below)

### Process A: Manual Export (Obsidian Dataview)

**Step 1: Create a Dataview Query**
Create a note at `/world/data/generate_geojson.md` with the following Dataview query:

```markdown
---
type: utility-query
purpose: Generate GeoJSON from Location Notes
---

# GeoJSON Generation Query

```dataview
TABLE name, location, type, description
FROM "world/locations"
WHERE location AND type
SORT name ASC
```
```

This outputs all locations with coordinates and types. Copy this table.

**Step 2: Transform to GeoJSON**
Manually convert the Dataview output to GeoJSON format:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Samarqandh",
        "type": "city",
        "description": "...",
        "tags": ["player-visible", "faction-sogdian"]
      },
      "geometry": {
        "type": "Point",
        "coordinates": [66.97, 39.65]
      }
    }
    // ... more features
  ]
}
```

**Step 3: Save & Verify**
Save as `/world/data/geojson_master.geojson`

Verify with a GeoJSON linter (https://geojson.io) to ensure valid syntax.

---

### Process B: Python Script (Batch Generation)

For larger datasets, use a Python script to automate conversion.

**Script location:** `/world/utilities/geojson_generator.py`

**Usage:**
```bash
python3 geojson_generator.py --input "/Users/mo/Documents/Games/HeroHeaven/world/locations" --output "/Users/mo/Documents/Games/HeroHeaven/world/data/geojson_master.geojson"
```

**Script (template):**
```python
#!/usr/bin/env python3
"""
Generate GeoJSON from Location Notes frontmatter.
Reads all .md files in a directory, extracts location data, outputs GeoJSON.
"""

import os
import json
import re
from pathlib import Path
import frontmatter

def extract_location_data(file_path):
    """Extract name, location, type, tags from a Location Note."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            
        name = post.metadata.get('name')
        location = post.metadata.get('location')
        loc_type = post.metadata.get('type')
        tags = post.metadata.get('tags', [])
        description = post.metadata.get('description', '')
        
        if not (name and location and loc_type):
            return None
        
        # Ensure location is [lat, long]
        if not isinstance(location, list) or len(location) != 2:
            return None
        
        return {
            'name': name,
            'location': location,
            'type': loc_type,
            'tags': tags,
            'description': description
        }
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def build_geojson(locations_dir):
    """Build a GeoJSON FeatureCollection from location files."""
    features = []
    
    for filename in os.listdir(locations_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(locations_dir, filename)
            data = extract_location_data(file_path)
            
            if data:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": data['name'],
                        "type": data['type'],
                        "description": data['description'],
                        "tags": data['tags']
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [data['location'][1], data['location'][0]]  # [lon, lat]
                    }
                }
                features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to locations directory')
    parser.add_argument('--output', required=True, help='Path to output GeoJSON file')
    args = parser.parse_args()
    
    geojson = build_geojson(args.input)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(geojson['features'])} features to {args.output}")
```

---

## Workflow 2: Generate Filtered GeoJSON (Player vs. GM)

### Purpose
Create separate GeoJSON files for player and GM visibility, filtering by tags.

### Process

**Step 1: Create Player GeoJSON**
Filter out `#gm-only` and `#secret` tags. Keep only `#player-visible`.

Using Dataview:
```markdown
```dataview
TABLE name, location, type
FROM "world/locations"
WHERE location AND type AND contains(tags, "player-visible")
SORT name ASC
```
```

Then convert to GeoJSON format (same as Workflow 1, but filtered).

**Step 2: Create GM GeoJSON**
Keep all locations. No filtering.

Use the master GeoJSON from Workflow 1, or create a query that includes all tags.

**Step 3: Save**
- Player export: `/world/data/geojson_player.geojson`
- GM export: `/world/data/geojson_gm.geojson`

**Step 4: Verify**
Spot-check both files. Ensure player version has fewer features than GM version.

---

## Workflow 3: Create Leaflet Map Notes

### Purpose
Create readable Obsidian notes that instantiate interactive maps using the Obsidian Leaflet plugin.

### Process

**Step 1: Create a GM Reference Map**

Create `/world/maps/gm_master_world_map.md`:

```markdown
---
type: leaflet-map
purpose: GM reference - all locations, all details
created: 2025-12-08
last_updated: 2025-12-08
---

# GM Master World Map

All locations visible to GM. Use this for session prep and reference.

```leaflet
id: gm-master-map
geojson: [[geojson_gm.geojson]]
lat: 40
long: 70
minZoom: 3
maxZoom: 12
defaultZoom: 6
height: 600px
```

### Notes
- This loads the full GeoJSON file with all locations
- Use for GM prep and planning
- Do not share with players
```

**Step 2: Create a Player Map**

Create `/world/maps/player_world_map.md`:

```markdown
---
type: leaflet-map
purpose: Player reference - visible locations only
created: 2025-12-08
last_updated: 2025-12-08
---

# World Map (Player Version)

Locations you've discovered or heard of during your journey.

```leaflet
id: player-map
geojson: [[geojson_player.geojson]]
lat: 40
long: 70
minZoom: 3
maxZoom: 12
defaultZoom: 6
height: 600px
```

### How to Use
Click on any marker to see what you know about that location.
```

**Step 3: Create Session-Specific Maps (Optional)**

For Session 1, create `/world/maps/session_1_map.md`:

```markdown
---
type: leaflet-map
purpose: Session 1 - relevant locations only
---

# Session 1: The Oasis at Dawn

Your journey begins here. Relevant locations are marked.

```leaflet
id: session-1-map
markerTag: session-1
markerFolder: world/locations
lat: 39.5
long: 66.5
minZoom: 4
maxZoom: 12
defaultZoom: 7
height: 600px
```

This uses `markerTag: session-1` to load only Location Notes tagged with `#session-1`.
```

**Step 4: Verify**
- Open each map note in Obsidian reading mode
- Confirm markers render correctly
- Spot-check that player map has fewer markers than GM map

---

## Workflow 4: Export to KML for Google Earth

### Purpose
Generate KML/KMZ files from GeoJSON for Google Earth distribution to players.

### Process A: Online Converter

**Step 1: Use a GeoJSON-to-KML Converter**
- Go to https://geojson.io
- Load your `geojson_player.geojson` file
- Menu → Save → KML

**Step 2: Save as KML**
Save as `/world/data/tarim_shaiel_world_player.kml`

**Step 3: Create KMZ (Compressed)**
- KML files are text; KMZ is a ZIP archive
- Right-click the KML → Compress (on macOS: Cmd+Click)
- Rename `.zip` to `.kmz`

**Step 4: Share with Players**
Distribute the `.kmz` file. Players open it in Google Earth.

---

### Process B: Python Script (Advanced)

For batch KML generation with custom styling:

**Script location:** `/world/utilities/geojson_to_kml.py`

**Usage:**
```bash
python3 geojson_to_kml.py --input "geojson_player.geojson" --output "tarim_shaiel_world.kml" --name "Tarim-Shaiel"
```

**Script (template):**
```python
#!/usr/bin/env python3
"""
Convert GeoJSON to KML with styling.
"""

import json
import argparse
from lxml import etree

def geojson_to_kml(geojson_path, output_path, name="Map"):
    """Convert GeoJSON to KML."""
    
    with open(geojson_path, 'r') as f:
        geojson = json.load(f)
    
    # Create KML root
    kml = etree.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = etree.SubElement(kml, 'Document')
    name_elem = etree.SubElement(document, 'name')
    name_elem.text = name
    
    # Add placemarks
    for feature in geojson['features']:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        placemark = etree.SubElement(document, 'Placemark')
        pm_name = etree.SubElement(placemark, 'name')
        pm_name.text = props.get('name', 'Unnamed')
        
        description = etree.SubElement(placemark, 'description')
        description.text = props.get('description', '')
        
        point = etree.SubElement(placemark, 'Point')
        coordinate = etree.SubElement(point, 'coordinates')
        coordinate.text = f"{coords[0]},{coords[1]},0"
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(etree.tostring(kml, xml_declaration=True, encoding='UTF-8', pretty_print=True))
    
    print(f"Generated KML with {len(geojson['features'])} placemarks to {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--name', default='Tarim-Shaiel Map')
    args = parser.parse_args()
    
    geojson_to_kml(args.input, args.output, args.name)
```

---

## Workflow 5: Scheduled Post-Session Publishing

### Purpose
After each session, update player-facing exports and archives.

### Process

**Step 1: Refresh GeoJSON**
Run Workflow 1 or 1B (regenerate from Location Notes)

**Step 2: Filter & Export**
Run Workflow 2 (create player/GM versions)

**Step 3: Generate KML**
Run Workflow 4 (create `.kmz` for Google Earth)

**Step 4: Archive**
Move previous exports to `/world/data/archives/session_[N]/`

**Step 5: Notify Players**
Share the new `.kmz` file and/or send them the player Leaflet map note link.

---

## Checklist: Publishing a Session Map

- [ ] All Location Notes for the session are created and tagged `#session-X`
- [ ] Coordinates verified (WGS84, not null)
- [ ] Visibility tags applied (`#gm-only`, `#player-visible`, `#secret`)
- [ ] GeoJSON regenerated from Location Notes
- [ ] Player GeoJSON filtered (no `#gm-only`, no `#secret`)
- [ ] Leaflet map notes created and rendering correctly
- [ ] KML/KMZ exported and tested in Google Earth
- [ ] Previous session data archived
- [ ] Players notified of new map availability

---

## Notes for Lore Keeper

- Monitor `/world/locations/` weekly for new entries
- Regenerate GeoJSON monthly or post-session
- Audit player export for accidental secret data
- Archive old exports in `/world/data/archives/`
- Flag any locations with null coordinates

---

## Tools Required

- **Obsidian Leaflet Plugin** (for in-vault maps)
- **Dataview Plugin** (for querying Location Notes)
- **Python 3** (for batch scripts, optional)
- **geojson.io** (for testing/conversion, online)
- **Google Earth** (for KML verification, free)

---

## Troubleshooting

**Leaflet maps not rendering?**
- Verify GeoJSON is valid (use geojson.io)
- Check that file path in `geojson:` parameter is correct
- Ensure Leaflet plugin is installed and enabled

**KML markers appearing as "Untitled Folder"?**
- Verify KML uses proper `<name>` tags (not malformed XML)
- Test with a Python script to ensure tag structure

**GeoJSON features appearing in wrong location?**
- Check coordinate order: GeoJSON uses [longitude, latitude], not [latitude, longitude]
- Swap if needed in conversion script

**Player map showing secret locations?**
- Verify `#gm-only` and `#secret` tags are present in Location Notes
- Re-filter GeoJSON when new tags are added
