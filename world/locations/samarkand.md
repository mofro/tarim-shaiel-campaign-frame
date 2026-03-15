---
created: 2025-12-13
description: A major hub on the Silk Road, known for its bazaars and monumental architecture.
elevation: 700
factions:
- Sogdian Merchants Guild
fantasy_name: Samarqandh
is_private: false
last_updated: 2025-12-13
location:
- 39.65
- 66.97
mapmarker: city
name: Samarkand
resources:
- textiles
- luxury goods
- paper
tags:
- player-visible
- campaign-arc-desert
- type-city
- test
type: city
---

```leaflet
id: location-samarkand
coordinates: [[world/locations/samarkand]]
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

# Samarqandh

A jeweled city where trade routes converge. Once ruled by distant empires, it has become a nexus of commerce and intrigue.

## Historical Basis

**Sogdania** – Originally Zoroastrian, converted to Islam. Survived Mongol conquest and was revived as a major Timurid cultural center. Known as "Stone Fort" in antiquity.

## Key Features

- **The Grand Bazaar** – Famous for textiles, luxury goods, and paper mills
- **Monumental Architecture** – Blue domes and ancient structures testament to past glory
- **Scholarly Hub** – Intellectual center of Central Asia

## Factions Present

- Sogdian Merchants Guild (primary traders)
- Local authorities

## Resources

- High-quality textiles
- Luxury items
- Paper production