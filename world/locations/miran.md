---
created: 2025-12-13
description: A waypoint on the southern desert route. An ancient settlement with ruins
  of Buddhist temples.
elevation: 890
factions:
- Oasis Guardians
fantasy_name: Miran
historical_basis: Tarim Basin - Ancient oasis settlement on southern route
is_private: false
last_updated: 2025-12-13
location:
- 40.52
- 88.07
mapmarker: route-node
name: Miran
resources:
- oasis goods
- archaeological relics
tags:
- player-visible
- campaign-arc-southern-route
- type-route-node
type: route-node
---

```leaflet
id: location-miran
coordinates: [[world/locations/miran]]
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

# Miran

A rest stop on the treacherous southern route through the Taklamakan. Ancient ruins of Buddhist temples dot the area, attracting pilgrims and archaeologists.

## Site Features

- **Oasis Water** – Critical resupply point
- **Buddhist Ruins** – Ancient temples and religious structures
- **Archaeological Interest** – Treasures hidden in the sand

## Route Significance

Waypoint on the Southern Route. Merchants coming from Khotan use this before pressing toward the eastern sections.

## Current Status

Small settlement of guardians and caravanners. Ruins attract scholarly interest and occasionally bandits seeking treasure.