---
created: 2025-12-13
description: A canyon pinch-point where the road compresses into a single file—ideal
  for tolls, patrols, and ambushes.
fantasy_name: The Wind-Cut Narrows
is_private: false
last_updated: 2025-12-13
location:
- 40.33
- 94.55
mapmarker: route-node
name: The Wind-Cut Narrows
tags:
- player-visible
- type-chokepoint
type: chokepoint
---

```leaflet
id: location-wind-cut-narrows
coordinates: [[world/locations/wind-cut-narrows]]
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
    
markerFolder: world/locations

```

# The Wind-Cut Narrows

A narrow, wind-carved passage where caravans are forced into a tight column and every guard tower matters.