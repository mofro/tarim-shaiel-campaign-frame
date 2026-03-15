---
title: World Directory Index
project: TTRPG_Tarim_Shaiel
type: directory_index
purpose: Dynamic navigation for world-building and setting resources
created: 2026-01-28
---

# World Directory

## Domain Structure

### 🗺️ World Creation Workflow
```dataview
LIST 
FROM "world/workflow" 
SORT file.name ASC
```

### ⚙️ Technical Systems
```dataview
LIST 
FROM "world/systems" 
SORT file.name ASC
```

### 📚 World-Building Content
```dataview
LIST 
FROM "world/content" 
SORT file.name ASC
```

### 📍 Locations (37)
```dataview
LIST 
FROM "world/locations" 
SORT file.name ASC
LIMIT 10
```
*...and 27 more locations*

### 🗂️ Data & Mapping
```dataview
LIST 
FROM "world/data" 
WHERE file.name != "Index.md"
SORT file.name ASC
```

### 🖼️ Visual Assets
```dataview
LIST 
FROM "world/images" 
WHERE file.name != "Index.md"
SORT file.name ASC
LIMIT 5
```
*...and visual resources*

### 📊 Directory Stats
- **Total Domains:** 8
- **Location Files:** 37
- **Last Updated:** `= date(now)`
- **Purpose:** Complete world-building and setting management

---

## About This Directory

This directory contains the complete world-building framework:
- **Workflow** - World creation processes and methodologies
- **Systems** - Technical infrastructure and mapping systems
- **Content** - World-building content and regional development
- **Locations** - Individual location files (37 cities, sites, etc.)
- **Data** - Geospatial data and mapping files
- **Images** - Maps and visual assets
- **Markers** - Map marker definitions
- **Mythology** - World mythology and cultural elements

## Related Directories

- [[../templates/world-building|World-Building Templates]]
- [[narrative-template|Narrative Foundation]]
- [[../characters|Character Elements]]

---

*This index updates automatically using Dataview queries.*
