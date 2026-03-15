---
type: test-map
purpose: Test GeoJSON overlay system with Thunderforest Pioneer base
created: 2025-12-14
last_updated: 2025-12-14
---

# Test: GeoJSON Overlay System (Native Plugin)

Testing integration of:
- **Base Map:** Thunderforest Pioneer (clean, topographic)
- **Overlay:** test-geojson.json (3 regions, 5 locations, 1 trade route)

Replace `YOUR_THUNDERFOREST_KEY` with your actual Thunderforest API key.

%%
 - https://maps.geoapify.com/v1/tile/carto/{z}/{x}/{y}.png?&apiKey=9628e752e43040a7aa8a1699a288cd13
%%

```leaflet
id: fantasy-map
bounds:
 - [0,0]
 - [52,152]
lat: 25
long: 74
defaultZoom: 4.5
minZoom: 4.5
maxZoom: 18
image: [[HH_test_map_export_colorful_w_labels.png]]
width: 1600px
height: 475px
zoomDelta: 0.5
  
geojson:

- [[world/tarim-shaiel-routes.geojson]]|Routes

```

```leaflet
id: hero-heaven
lat: 38
long: 80
defaultZoom: 4.5
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false
disableResetZoomControl: true
disableFilterControl: false

tileServer:

  - https://api.maptiler.com/tiles/hand-drawn-hillshade/{z}/{x}/{y}.webp?key=uZtsACZHTZGwWfZ3HGai


tileOverlay:

- https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png|Labels
- https://tile.thunderforest.com/pioneer/{z}/{x}/{y}.png?apikey=988025a356244971b4db7ddced28eedb | Pioneer
- https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite (No Labels)


  
geojson:

- [[world/tarim-shaiel-routes.geojson]]|Routes


```

---

## What We're Testing

1. **Base Map:** Thunderforest Pioneer (clean topographic base)
2. **Region Polygons:** 3 regions loaded from test-geojson.json
3. **Location Points:** 5 locations as GeoJSON features
4. **Trade Route:** Orange dashed line connecting locations

## Expected Behavior

- Pioneer tiles load (no OpenStreetMap labels)
- GeoJSON features render on map
- Click features to see popup with name and description
- Zoom and pan normally

## Configuration Notes

- `osmLayer: false` - Disables default OpenStreetMap (we only want Pioneer)
- `geojson: [[world/test-geojson.json]]` - Wikilink to GeoJSON file in vault
- File path is relative to vault root

## Next Steps

1. Verify Pioneer loads and GeoJSON displays
2. Test feature interactivity (click for popups)
3. Adjust GeoJSON styling in the JSON file itself
4. Expand to all 22 locations incrementally
5. Create regional GeoJSON files for cleaner data organization
