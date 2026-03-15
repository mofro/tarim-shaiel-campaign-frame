---
created: 2025-12-13
description: A waypoint on the southern route between eastern and western Taklamakan
  sections.
elevation: 900
factions:
- Oasis Settlers
fantasy_name: Cherchen
historical_basis: Tarim Basin - Oasis waypoint on southern corridor
is_private: false
last_updated: 2025-12-13
location:
- 38.14
- 85.55
mapmarker: route-node
name: Cherchen
resources:
- oasis goods
tags:
- player-visible
- campaign-arc-southern-route
- type-route-node
type: route-node
---

```leaflet
id: location-cherchen
coordinates: [[world/locations/cherchen]]
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

# Cherchen

A small but essential oasis on the southern route. Merchants stop here to refresh supplies before crossing harsh desert sections.

## Route Function

- Waypoint between major oases
- Resupply point for southbound merchants
- Protection from desert exposure

## Resources

Water, local grain, and oasis fruits.

## Current State

A modest but reliable way station. Guides and local merchants provide services to passing caravans.