---
type: test-map
purpose: Test marker styling via marker field in Location Notes
created: 2025-12-13
last_updated: 2025-12-13
---

# Test: Marker Styling via Location Note Fields

Testing if the `marker` field in Location Notes connects to plugin-configured marker types.

```leaflet
id: test-map
markerFolder: world/locations
lat: 38
long: 80
defaultZoom: 5
height: 600px
```

---

## What We're Testing

- Samarkand has `marker: City` in frontmatter
- Plugin is configured with "City" marker (blue building icon)
- Does the plugin connect these?

**Expected:** Samarkand should render with blue building icon
**Current:** Markers appear tan/default

Open in Reading Mode and check.
