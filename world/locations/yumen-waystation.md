---
created: 2025-12-13
description: Overflow staging post for caravans approaching the Jade Gate; paperwork,
  inspections, and remounts.
fantasy_name: Yumen Waystation (Outer)
is_private: false
last_updated: 2025-12-13
location:
- 40.42
- 94.78
mapmarker: route-node
name: Yumen Waystation (Outer)
tags:
- player-visible
- type-caravanserai
type: caravanserai
---

```leaflet
id: location-yumen-waystation
coordinates: [[world/locations/yumen-waystation]]
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

# Yumen Waystation (Outer)

A fortified overflow station that takes the pressure off the Jade Gate proper: stables, ledgers, inspectors, and caravan yards.