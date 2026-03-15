---
title: Geography - Locations & Coordinates
project: TTRPG_Tarim_Shaiel
type: world_building
status: in_progress
created: 2025-12-07
updated: 2025-12-07
data_source: regions.json
---

# Tarim-Shaiel Geography

## Overview
This document catalogs all significant locations in the Tarim-Shaiel world, grounded in real Silk Road geography with fantasy overlays. All locations use real Earth coordinates (lat/long) as technical foundation.

**Data Management:**
- **Source of Truth:** `/world/data/regions.json`
- **This Document:** Human-readable reference with narrative context
- **Generated Artifacts:** KMZ files for mapping tools

---

## Major Regions

### [To be populated from source geography markdown]

Template for each region:
- **Name:** [Fantasy name] ([Real-world analogue])
- **Coordinates:** [lat, long]
- **Type:** [mountain-kingdom / trade-hub / steppe-confederation / etc.]
- **Historical Basis:** [Real geographic/cultural reference]
- **Current Status:** [Political situation, ~1450s present day]
- **Key Features:**
  - Geographic characteristics
  - Major settlements
  - Strategic importance
  - Cultural/religious significance
- **Magical Elements:** [How magic affects this region]
- **Lore Hooks:** [Adventure/campaign possibilities]

---

## Data Structure Notes

### Coordinates Format
All coordinates stored as:
```json
{
  "lat": decimal_degrees,
  "lon": decimal_degrees
}
```

### Boundary Paths
Region boundaries defined as arrays of coordinate pairs:
```json
{
  "boundary": [
    [lat1, lon1],
    [lat2, lon2],
    [lat3, lon3]
  ]
}
```

### Region Types
Standardized categories for filtering/visualization:
- `mountain-kingdom` - Highland territories (Dwarven strongholds, isolated kingdoms)
- `steppe-confederation` - Nomadic/semi-nomadic regions (Orc territories)
- `trade-hub` - Oasis cities, merchant centers
- `forest-enclave` - Elf territories, dense vegetation zones
- `river-valley` - Agricultural centers, human settlements
- `coastal-port` - Maritime trade hubs
- `desert-crossing` - Caravan routes, minimal settlement
- `sacred-site` - Religious/magical significance

---

## Regional Breakdown

### Eastern Territories
**[China analogue - to be detailed]**

### Central Asian Oases
**[Tarim Basin / Samarkand region - to be detailed]**

### Mountain Kingdoms
**[Hindu Kush / Pamir analogue - to be detailed]**

### Southern Trade Ports
**[Arabian Sea / Indian Ocean - to be detailed]**

### Western Reaches
**[Persia / Levant analogue - to be detailed]**

### Northern Steppes
**[Mongol heartland analogue - to be detailed]**

---

## Next Steps
1. Parse source geography markdown
2. Extract all locations with coordinates
3. Populate this document with narrative context
4. Build regions.json with complete data
5. Generate KMZ file for mapping

---

**Maintained by:** Lore Keeper  
**Data Source:** Awaiting source geography markdown from Mo  
**Last Update:** 2025-12-07 (structure created, awaiting data)
