---
created: 2025-12-13
description: A waypoint on the southern route between desert sections.
elevation: 800
factions:
- Oasis Keepers
fantasy_name: Charklik
historical_basis: Tarim Basin - Oasis waypoint
is_private: false
last_updated: 2025-12-13
location:
- 39
- 88.15
mapmarker: route-node
name: Charklik
resources:
- oasis supplies
tags:
- player-visible
- campaign-arc-southern-route
- type-route-node
type: route-node
---

```leaflet
id: location-charklik
coordinates: [[world/locations/charklik]]
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

# Charklik

A small but vital oasis on the southern desert route. Merchants rely on the fresh water and supplies here to cross between harsh desert sections.

## Route Function

Waypoint providing relief and resupply for southbound merchants.

## Resources

Water, local grain, simple food supplies.

## Character

A quiet, functional way station where merchants and guides prepare for the next desert crossing.