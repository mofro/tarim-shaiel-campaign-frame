---
created: 2025-12-13
description: A major waypoint where the southern and northern routes converge. A hub
  of trade and communication.
elevation: 1200
factions:
- Southern Route Merchants
fantasy_name: Yarkand
historical_basis: Tarim Basin - Convergence point of major trade routes
is_private: false
last_updated: 2025-12-13
location:
- 38.417
- 77.2411
mapmarker: route-node
name: Yarkand
resources:
- oasis goods
- fruits
- textiles
tags:
- player-visible
- campaign-arc-route-convergence
- type-route-node
type: route-node
---

```leaflet
id: location-yarkand
coordinates: [[world/locations/yarkand]]
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

# Yarkand

Where the northern and southern routes merge into one. A bustling hub where merchants from different paths exchange news, goods, and information.

## Route Significance

- **Convergence Point** – North and south routes meet here
- **Information Hub** – Latest trade news and road conditions
- **Market Center** – Merchants trade goods and services

## Factions

- Southern route merchants
- Northern route merchants
- Local authorities

## Strategic Importance

A crossroads where merchants traveling different routes meet and share knowledge. Critical intelligence flows through here.