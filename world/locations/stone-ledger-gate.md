---
created: 2025-12-13
description: A controlled high pass where weights, measures, and cargo manifests are
  certified before crossing.
fantasy_name: The Stone Ledger Gate
is_private: false
last_updated: 2025-12-13
location:
- 40.4
- 75.2
mapmarker: route-node
name: The Stone Ledger Gate
tags:
- player-visible
- type-mountain-pass
type: mountain-pass
---

```leaflet
id: location-stone-ledger-gate
coordinates: [[world/locations/stone-ledger-gate]]
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

# The Stone Ledger Gate

A pass controlled by officials who care as much about ledgers as they do about swords. Cargo is weighed, stamped, and recorded before the climb.