---
title:
project:
parent_region:
domain:
doc_type:
content_type:
visibility:
status: deprecated
created:
  "{ date }":
cultural_notes:
description:
elevation:
factions_visible:
fantasy_name:
last_updated:
location: []
mapmarker:
name:
resources: []
tags: []
type:
---
```leaflet
id: location-<location>
coordinates: [[world/locations/<location>]]
defaultZoom: 10
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false
tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite

tileOverlay:
  - https://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png|Hillshade|on

geojson:
  - [[world/tarim-shaiel-regions.geojson]]|Regions
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations

```
# {{title}}

Brief description of the location (1-2 sentences).

## Geography

Physical characteristics, terrain, climate, notable features.

## Economy

Trade, resources, economic activity, markets.

## Key Features

Distinctive landmarks, architecture, cultural elements.

## Factions

Major groups, organizations, or power structures present.

## Resources

What this location produces, exports, or is known for.

## Cultural Notes

Customs, traditions, social structure, daily life.

## Historical Basis

Real-world inspiration and historical context (player-facing).

---

## Narrative Significance
<!-- GM SECTION - Creates separate admin-only post -->

Why this location matters to the campaign narrative.

## Hidden Secrets
<!-- GM SECTION - Creates separate admin-only post -->

Information players don't know yet.

## Plot Hooks
<!-- GM SECTION - Creates separate admin-only post -->

Potential adventures, mysteries, or complications.

## DM Notes
<!-- GM SECTION - Creates separate admin-only post -->

Mechanics, encounters, prep notes.

---

## Location Type Glossary

**Common Location Types:**
- `city` - Major urban center
- `town` - Mid-sized settlement
- `village` - Small rural community
- `route-node` - Waypoint/crossroads
- `sacred-site` - Religious/spiritual location
- `dungeon` - Adventure site
- `fortress` - Military installation
- `ruins` - Abandoned/destroyed site
- `wilderness` - Natural area
- `region` - Large geographic area

**Map Marker Types:**
- `city` - Urban settlement
- `route-node` - Travel waypoint
- `sacred-site` - Religious location
- `marker-dungeon` - Adventure site
- `marker-ruins` - Ancient ruins

See [[WORLD_CREATION_WORKFLOW#location-note-schema|LOCATION_NOTE_SCHEMA]] for complete field reference.
