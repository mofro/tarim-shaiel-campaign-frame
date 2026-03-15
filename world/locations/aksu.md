---
created: 2025-12-13
description: A waypoint on the northern route. An oasis providing critical supplies
  for westbound merchants.
elevation: 1141
factions:
- Merchants & Caravanners
fantasy_name: Aksu
historical_basis: Tarim Basin - Oasis waypoint on northern corridor
is_private: false
last_updated: 2025-12-13
location:
- 41.17
- 80.26
mapmarker: caravanserai
name: Aksu
resources:
- oasis goods
- fruits
tags:
- player-visible
- campaign-arc-northern-route
- type-route-node
type: route-node
---

```leaflet
id: location-aksu
coordinates: [[world/locations/aksu]]
defaultZoom: 10
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false

tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite (No Labels)

tileOverlay:
  - https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png|Labels

geojson:
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations
```

# Aksu

A vital rest stop on the Northern Route. Merchants rely on this oasis for water, food, and fresh animals before the difficult mountain crossing ahead.

## Resources

- Fresh water and spring
- Local fruits and grain
- Caravanserai facilities

## Route Significance

Gateway toward the western high passes. Westbound merchants prepare here for the challenging sections through mountain territory.

## Factions

- Oasis settlers
- Merchants and caravan operators
- Local guides

## Current State

Busy waypoint with established rest facilities and animal markets.