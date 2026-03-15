---
created: 2025-12-13
description: Ancient oasis ruins on the southern route. Archaeological treasures hidden
  in the sands await discovery.
elevation: 1200
factions:
- Desert Guardians
fantasy_name: Niya
historical_basis: Tarim Basin - Ancient oasis settlement with archaeological significance
is_private: false
last_updated: 2025-12-13
location:
- 37.07
- 81.18
mapmarker: route-node
name: Niya
resources:
- oasis supplies
tags:
- player-visible
- campaign-arc-southern-mysteries
- type-route-node
type: route-node
---

```leaflet
id: location-niya
coordinates: [[world/locations/niya]]
defaultZoom: 10
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false
tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite (No Labels)

tileOverlay:
  - https://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png|Hillshade|on
  - https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png|Labels

geojson:
  - [[world/tarim-shaiel-regions.geojson]]|Regions
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations

```

# Niya

An ancient settlement slowly being reclaimed by the desert. The ruins hold secrets from ages past—manuscripts, artifacts, and mysteries for those brave enough to seek them.

## Archaeological Significance

- **Ancient Ruins** – Buildings from pre-Islamic era
- **Buried Treasures** – Manuscripts and artifacts in the sand
- **Lost Knowledge** – Scholars seek ancient texts here

## Route Function

A waypoint on the southern desert route, though increasingly isolated as desert encroaches.

## Dangers

- Sandstorms
- Bandits seeking treasure
- Structural collapse in ruins

## Opportunities

For adventurers and scholars, Niya offers potential discovery of lost knowledge from fallen civilizations.