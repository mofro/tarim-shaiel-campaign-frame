---
created: 2025-12-13
description: An oasis in a depression, protected from harsh desert winds. Known for
  cultivation of grapes and wine production.
elevation: -154
factions:
- Oasis Settlers
fantasy_name: Turfan Depression
historical_basis: Tarim Basin - Oasis settlement in depression; known for agriculture
is_private: false
last_updated: 2025-12-13
location:
- 42.95
- 89.19
mapmarker: route-node
name: Turfan
resources:
- wine
- grapes
- grain
tags:
- player-visible
- campaign-arc-tarim-routes
- type-route-node
- oasis
type: route-node
---

```leaflet
id: location-turfan
coordinates: [[world/locations/turfan]]
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

# Turfan

A large verdant oasis nestled in a depression, offering refuge from the harsh Taklamakan Desert. The protected valley produces exceptional grapes and wine.

## Geography

- **Depression Site** – Natural bowl that protects from extreme desert winds
- **Water Sources** – Underground springs and irrigation
- **Agricultural Hub** – Produces grapes, melons, and grain

## Economy

Wine production is famous throughout the Silk Road. Merchants seek Turfan wine for its quality and the prestige of carrying it.

## Factions

- Oasis farmers and settlers
- Traders and caravanners
- Local government

## Waypoint Status

Critical stop on the Northern Route. Merchants refresh supplies and animals here before crossing harsh desert sections.