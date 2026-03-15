---
type: test-map
purpose: Test GeoJSON overlay system with Thunderforest Pioneer base and test-geojson.json
created: 2025-12-14
last_updated: 2025-12-14
---

# Test: GeoJSON Overlay System

Testing integration of:
- **Base Map:** Thunderforest Pioneer (clean, topographic)
- **Overlay:** test-geojson.json (3 regions, 5 locations, 1 trade route)

## Setup

Replace `YOUR_THUNDERFOREST_KEY` below with your actual API key.

```leaflet
id: test-geojson-map
lat: 38
long: 80
defaultZoom: 5
height: 800px
```

<script>
// Wait for the map to initialize
setTimeout(function() {
  var mapDiv = document.querySelector('[data-id="test-geojson-map"]');
  if (!mapDiv || !window.L) return;
  
  // Access the Leaflet map instance (if the plugin exposes it)
  // Note: This approach may vary depending on Obsidian Leaflet plugin implementation
  
  // Add Thunderforest Pioneer tile layer
  var pioneerlayer = L.tileLayer(
    'https://tile.thunderforest.com/pioneer/{z}/{x}/{y}.png?apikey=988025a356244971b4db7ddced28eedb',
    {
      attribution: '© Thunderforest, © OpenStreetMap',
      maxZoom: 18
    }
  );
  
  // Load and add GeoJSON
  fetch('/Users/mo/Documents/Games/HeroHeaven/world/tarim-shaiel-locations.geojson')
    .then(response => response.json())
    .then(geojsonData => {
      L.geoJSON(geojsonData, {
        style: function(feature) {
          if (feature.properties.type === 'region') {
            return {
              color: '#1f77b4',
              weight: 2,
              opacity: 0.3,
              fillOpacity: 0.1
            };
          } else if (feature.properties.type === 'trade-route') {
            return {
              color: '#ff7f0e',
              weight: 3,
              opacity: 0.7,
              dashArray: '5, 5'
            };
          }
        },
        pointToLayer: function(feature, latlng) {
          var markerColor = '#2ca02c';
          if (feature.properties.marker_type === 'city') {
            markerColor = '#d62728';
          } else if (feature.properties.marker_type === 'sacred-site') {
            markerColor = '#9467bd';
          } else if (feature.properties.marker_type === 'route-node') {
            markerColor = '#ff7f0e';
          }
          
          return L.circleMarker(latlng, {
            radius: 6,
            fillColor: markerColor,
            color: '#000',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
          });
        },
        onEachFeature: function(feature, layer) {
          var popup = '<strong>' + feature.properties.name + '</strong><br>';
          if (feature.properties.description) {
            popup += feature.properties.description;
          }
          layer.bindPopup(popup);
        }
      }).addTo(map);
    })
    .catch(err => console.error('Error loading GeoJSON:', err));
}, 500);
</script>

---

## What We're Testing

1. **Base Map:** Thunderforest Pioneer (clean topographic base)
2. **Region Polygons:** 3 regions with semi-transparent blue fills and borders
3. **Location Points:** 5 locations as color-coded circle markers
   - Red = City
   - Purple = Sacred Site
   - Orange = Route Node
4. **Trade Route:** Orange dashed line connecting locations

## Expected Behavior

- Pioneer tiles load (no labels)
- Region boundaries visible as semi-transparent blue polygons
- Location markers appear as colored circles
- Trade route visible as dashed orange line
- Click on any feature to see popup with name and description

## Known Limitations (Iteration 1)

- GeoJSON path is absolute (may need adjustment for Obsidian environment)
- Styling is basic (iterate on colors/sizes later)
- No legend yet (can add later)
- Region polygons are estimated (will refine with real data)

## Next Steps

1. Verify map loads and GeoJSON displays
2. Test interactivity (popups on click)
3. Adjust styling and colors
4. Refine region polygon boundaries
5. Add all 22 locations incrementally
