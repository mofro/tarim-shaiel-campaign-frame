---
title: Gijduvan
project: TTRPG_Tarim_Shaiel
parent_region: tarim-basin
domain: world
doc_type: canon
content_type: poi
visibility: public
status: draft
created: 2025-12-13
description: An isolated waypoint on the southern route through harsh desert.
elevation: 1000
factions_visible:
  - Desert Survivors
fantasy_name: Gijduvel
historical_basis: Tarim Basin - Remote southern route waypoint
last_updated: 2025-12-13
location:
  - 40.102498
  - 64.682693
map_min_zoom: 6
map_max_zoom: 7
mapmarker: route-node
name: Gijduvan
resources:
  - oasis goods
tags:
  - player-visible
  - campaign-arc-southern-harsh
  - type-route-node
type: route-node
---

```leaflet
id: location-gijduvel
coordinates: [[world/locations/gijduvel]]
defaultZoom: 10
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false
tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite

tileOverlay:
  - https://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png|Hillshade|on

geojson:
  - [[world/tarim-shaiel-regions.geojson]]|Regions
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations

```

# Gijduvel

An isolated oasis on the most dangerous section of the southern route. Only the hardiest merchants and most determined pilgrims stop here. The desert around it is unforgiving.

## Location

Remote and difficult to reach, even from other oases. Merchants passing through speak of eerie isolation.

## Resources

Water, minimal food supplies. Guides are rare.

## Character

A place of quiet desperation. Those here survive through resilience and adaptation to harsh desert life.
