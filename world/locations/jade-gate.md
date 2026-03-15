---
created: 2025-12-13
description: The western gateway to imperial China. A heavily fortified checkpoint
  where all merchants are inspected and taxed.
elevation: 1400
factions:
- Imperial Guard Post
fantasy_name: Jade Gate
historical_basis: Gansu Corridor - Western border of imperial Chinese territory
is_private: false
last_updated: 2025-12-13
location:
- 40.339
- 94.5855
mapmarker: fortress
name: Jade Gate
resources:
- garrison supplies
tags:
- player-visible
- campaign-arc-eastern-routes
- type-route-node
type: route-node
visibility: secret
---

```leaflet
id: location-jade-gate
coordinates: [[world/locations/jade-gate]]
defaultZoom: 10
minZoom: 6.5
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

# Jade Gate

The imperial Chinese border post. Here, merchants entering China are inspected, documented, and taxed. The gate marks the boundary between the Silk Road proper and imperial territory.

## Strategic Importance

- **Imperial Checkpoint** – All goods entering China are recorded
- **Garrison Post** – Armed guards enforce imperial law
- **Cultural Boundary** – Marks transition from Central Asian to Chinese influence

## Factions

- Imperial Guard Post
- Chinese bureaucracy
- Trade authorities

## Current Status

Busy hub of bureaucratic activity. Merchants learn here what goods are permitted and what prices they'll pay in taxes.