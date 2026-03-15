---
created: 2025-12-13
description: A waypoint at the base of mountain passes. Guides here help merchants
  navigate the treacherous western mountain crossing.
elevation: 1000
factions:
- Mountain Guides
fantasy_name: Maralbashi
historical_basis: Tarim Basin - Mountain gateway on northern route
is_private: false
last_updated: 2025-12-13
location:
- 39.77193
- 78.53602
mapmarker: route-node
name: Maralbashi
resources:
- mountain provisions
tags:
- player-visible
- campaign-arc-mountain-passages
- type-route-node
type: route-node
---

```leaflet
id: location-maralbashi
coordinates: [[world/locations/maralbashi]]
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

# Maralbashi

Where the desert gives way to mountains. A critical point where merchants acquire guides, fresh animals, and supplies for the mountain crossing ahead.

## Strategic Location

- Gateway to western mountain passes
- Guides and porters available
- Final resupply before high altitude sections

## Factions

- Mountain guides (essential service)
- Animal traders
- Local merchants

## Important

The mountain crossing is dangerous. Guides from Maralbashi are highly valued for their knowledge of safe routes.