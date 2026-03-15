---
title: Coordinate Verification & Research
type: dataview-dashboard
purpose: Batch verify and update location coordinates
created: 2025-12-14
---

# Location Coordinate Verification Dashboard

Use this dashboard to verify and research accurate coordinates for all 22 locations. Edit the lat/long values directly and save to update Location Notes.

## All Locations with Current Coordinates

```dataview
TABLE name, location[0] as "Current Lat", location[1] as "Current Long", type
FROM "world/locations"
SORT name ASC
```

## By Type

### Cities
```dataview
TABLE name, location[0] as "Lat", location[1] as "Long"
FROM "world/locations"
WHERE type = "city"
SORT name ASC
```

### Route Nodes
```dataview
TABLE name, location[0] as "Lat", location[1] as "Long"
FROM "world/locations"
WHERE type = "route-node"
SORT name ASC
```

### Sacred Sites
```dataview
TABLE name, location[0] as "Lat", location[1] as "Long"
FROM "world/locations"
WHERE type = "sacred-site"
SORT name ASC
```

## Notes on Coordinate Updates

**Already Verified (by user):**
- Maralbashi: [39.77193, 78.53602]
- Kashgar: [39.4666, 75.99]
- Yarkand: [38.417, 77.2411]

**Coordinate Accuracy:**
- Previous coordinates were truncated to 2 decimals (~miles of error)
- Update to full precision (4-5 decimals) for accuracy
- Use mapcarta.com or equivalent sources for verification
- Decimal format: [latitude, longitude]

**How to Edit:**
1. Click on a location file from the table above
2. Edit the `location:` field in frontmatter to the new coordinates
3. Save the file
4. Dataview will auto-refresh the display
