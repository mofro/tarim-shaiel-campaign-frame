---
type: leaflet-map
purpose: Test satellite tiles to verify tileServer parameter works
created: 2025-12-13
---

# Test: Satellite Tiles

Testing ESRI World Imagery (satellite view) to see if tileServer parameter is actually being recognized.

```leaflet
id: test-satellite
markerFolder: world/locations
tileServer: https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite
lat: 38
long: 80
defaultZoom: 5
height: 600px
```

---

## What to Check

1. Open in Reading Mode (Cmd+E)
2. **Tile style:** Should show satellite/aerial imagery (earth photos from space)
3. **Comparison:** If this looks completely different from test_leaflet.md, then tileServer IS working
4. **If identical:** The parameter is being ignored by the plugin

