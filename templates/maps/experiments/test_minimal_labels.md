---
type: leaflet-map
purpose: Test minimal-label topographic tile server for fantasy map base
created: 2025-12-13
---

# Test: Stamen Toner Terrain (Minimal Labels)

Testing Stamen Toner Terrain—topographic with minimal place name labels.

```leaflet
id: test-minimal-labels
markerFolder: world/locations
lat: 38
long: 80
defaultZoom: 5
height: 600px
```

---

## Evaluation

Does this look good as a base? 
- Topographic terrain visible?
- Fewer place labels cluttering the map?
- Cleaner for overlaying fantasy names?

If yes → We'll use this as the default tile server and build GeoJSON overlays on top.

