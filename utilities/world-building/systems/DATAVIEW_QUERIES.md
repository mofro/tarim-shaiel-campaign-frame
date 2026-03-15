---
title: Dataview Queries - Location Note Dashboards & Utilities
project: TTRPG_Tarim_Shaiel
type: query_reference
status: in_development
created: 2025-12-08
last_updated: 2025-12-08
---

# Dataview Queries: Reference Dashboards & Data Utilities

## Overview
Dataview queries surface Location Note data in useful ways: dashboards for browsing, oversight queries for Lore Keeper maintenance, and data exports for publishing workflows.

All queries assume Location Notes live in `/world/locations/`.

---

## Reference Dashboards

These are reader-mode queries that provide quick overviews of the world.

### 1. All Locations Master Table

**Purpose:** Browse all locations with key details at a glance.

**Usage:** Create a note at `/world/maps/location_index.md` and embed:

```markdown
# Location Master Index

```dataview
TABLE name, type, location, factions, description
FROM "world/locations"
WHERE location AND type
SORT type, name
```

### Details by Type

All cities in the world:

```dataview
TABLE name, location, elevation, resources
FROM "world/locations"
WHERE type = "city"
SORT name
```

All natural features:

```dataview
TABLE name, location, terrain, climate
FROM "world/locations"
WHERE type = "natural-feature"
SORT name
```

All caravanserais and trade posts:

```dataview
TABLE name, location, parent_region
FROM "world/locations"
WHERE type = "caravanserai" OR type = "trade-post"
SORT name
```
```

---

### 2. Locations by Faction

**Purpose:** See which locations are affiliated with which factions.

**Usage:**

```markdown
# Locations by Faction

```dataview
TABLE name, type, location
FROM "world/locations"
WHERE contains(factions, "Sogdian Merchants Guild")
SORT name
```

Change the faction name to filter different groups.

Or, create a list of all factions:

```dataview
TABLE distinct(factions) as Factions
FROM "world/locations"
WHERE factions
```
```

---

### 3. Trade Routes Overview

**Purpose:** Map locations along named trade routes.

**Usage:**

```markdown
# Northern Silk Road Locations

```dataview
TABLE name, type, location, description
FROM "world/locations"
WHERE contains(tags, "trade-route-northern")
SORT location[1] DESC
```

This sorts locations by latitude (north to south), creating a visual "route".
```

---

### 4. Campaign Region Map

**Purpose:** Show only locations relevant to current campaign arc.

**Usage:**

```markdown
# Campaign Arc: The Desert Passage

Locations discovered during our journey through the southern dunes.

```dataview
TABLE name, type, description, danger_level
FROM "world/locations"
WHERE contains(tags, "campaign-arc-desert")
SORT name
```
```

---

### 5. Session-Specific Locations

**Purpose:** What locations matter THIS session?

**Usage:**

```markdown
# Session 3: The Oasis Negotiations

Locations the party will encounter or should know about.

```dataview
TABLE name, type, factions, conflicts
FROM "world/locations"
WHERE contains(tags, "session-3")
SORT name
```
```

---

## Maintenance & Oversight Queries

These are for Lore Keeper to monitor project health.

### 1. Incomplete Locations

**Purpose:** Find locations missing data (coordinates, descriptions, etc.).

**Usage:**

```markdown
# Locations Needing Work

```dataview
TABLE name, type, location, last_updated
FROM "world/locations"
WHERE contains(tags, "incomplete") OR location = null OR description = ""
SORT last_updated
```

This flags:
- Locations tagged `#incomplete`
- Locations with null coordinates
- Locations with empty descriptions
```

---

### 2. Recently Updated Locations

**Purpose:** What did the GM change recently?

**Usage:**

```markdown
# Recently Modified Locations

```dataview
TABLE name, type, last_updated, created
FROM "world/locations"
WHERE last_updated >= date("2025-12-01")
SORT last_updated DESC
```

Change the date to see updates from the past week, month, etc.
```

---

### 3. Locations Missing Visibility Tags

**Purpose:** Catch locations that haven't been classified as GM-only or player-visible.

**Usage:**

```markdown
# Locations Missing Visibility Tags

```dataview
TABLE name, type, tags
FROM "world/locations"
WHERE !contains(tags, "gm-only") AND !contains(tags, "player-visible") AND !contains(tags, "secret")
SORT name
```

These locations need tagging before publishing.
```

---

### 4. Workflow Status by Tag

**Purpose:** See which locations are ready for export.

**Usage:**

```markdown
# Publishing Status

**Ready for Player Export:**
```dataview
TABLE name, type
FROM "world/locations"
WHERE contains(tags, "ready-for-export")
SORT name
```

**Needs Narrative:**
```dataview
TABLE name, type, last_updated
FROM "world/locations"
WHERE contains(tags, "needs-narrative")
SORT last_updated
```

**Conflicts/Contested:**
```dataview
TABLE name, factions, conflicts
FROM "world/locations"
WHERE contains(tags, "conflict-zone")
SORT name
```
```

---

### 5. Data Audit: Coordinates Quality

**Purpose:** Verify all locations have valid coordinates.

**Usage:**

```markdown
# Coordinate Audit

**Locations with null coordinates:**
```dataview
TABLE name, type, created
FROM "world/locations"
WHERE location = null
SORT created DESC
```

**Locations with non-standard coordinate format:**
```dataview
TABLE name, location
FROM "world/locations"
WHERE length(string(location)) > 30 OR location = ""
SORT name
```

(This is a crude check; manually verify if anything appears.)
```

---

## Data Export Queries

These queries prepare data for publishing workflows.

### 1. Export: All Locations (GeoJSON-Ready)

**Purpose:** Generate table suitable for manual GeoJSON conversion.

**Usage:**

```markdown
# GeoJSON Export: All Locations

```dataview
TABLE 
  name,
  type,
  location,
  description,
  tags
FROM "world/locations"
WHERE location AND type
SORT name
```

**Note:** Use this table as a source for manual GeoJSON conversion (copy/paste) or feed into a Python script.
```

---

### 2. Export: Player-Visible Locations Only

**Purpose:** Generate player-safe GeoJSON.

**Usage:**

```markdown
# GeoJSON Export: Player Version

```dataview
TABLE 
  name,
  type,
  location,
  description
FROM "world/locations"
WHERE location AND type AND (contains(tags, "player-visible") OR !contains(tags, "gm-only"))
SORT name
```

This excludes `#gm-only` and `#secret` tagged locations.
```

---

### 3. Export: GM Full Dataset

**Purpose:** Generate complete GeoJSON for GM reference.

**Usage:**

```markdown
# GeoJSON Export: GM Full

```dataview
TABLE 
  name,
  type,
  location,
  description,
  factions,
  conflicts,
  tags
FROM "world/locations"
WHERE location AND type
SORT name
```

All locations, all details.
```

---

### 4. Export: By Region/Faction

**Purpose:** Generate partial GeoJSON for specific campaign area.

**Usage:**

```markdown
# GeoJSON Export: Transoxiana Region

```dataview
TABLE 
  name,
  type,
  location,
  description,
  factions
FROM "world/locations"
WHERE location AND type AND contains(parent_region, "Transoxiana")
SORT name
```

Change `parent_region` filter or use `factions` to narrow scope.
```

---

## Advanced Queries

### 1. Locations with No Faction Affiliation

**Purpose:** Find "neutral" or "independent" locations.

**Usage:**

```markdown
# Unaffiliated Locations

```dataview
TABLE name, type, description
FROM "world/locations"
WHERE (factions = null OR factions = []) AND type = "city"
SORT name
```

Good for finding places that are contested or truly neutral.
```

---

### 2. High Narrative Weight Locations

**Purpose:** Plot-critical locations that deserve extra attention.

**Usage:**

```markdown
# Plot-Critical Locations

```dataview
TABLE name, type, description, narrative_weight
FROM "world/locations"
WHERE narrative_weight = true
SORT name
```

These are locations the GM flagged as having special narrative importance.
```

---

### 3. Distance Between Two Locations

**Purpose:** Calculate rough travel time/distance (requires custom function).

**Usage:**

For a simple Haversine calculation in Dataview, use:

```markdown
# Distance Calculator

From Samarqandh to Bukhara:

**Latitude/Longitude:**
- Samarqandh: 39.65°N, 66.97°E
- Bukhara: 39.77°N, 64.41°E

**Rough Distance:** ~250 km (Haversine)
**Estimated Travel Time:** 10-15 days by caravan

(Use an external calculator like https://www.movable-type.co.uk/scripts/latlong.html for precision.)
```

Dataview doesn't natively support Haversine, so this is manual. For automation, use the Python utility script instead.
```

---

### 4. Conflict Zones by Severity

**Purpose:** Identify contested or dangerous regions.

**Usage:**

```markdown
# Conflict & Danger Summary

**High-Conflict Locations:**
```dataview
TABLE name, conflicts, danger_level
FROM "world/locations"
WHERE contains(tags, "conflict-zone") AND danger_level >= 3
SORT danger_level DESC
```

**Contested Territories (Multiple Factions):**
```dataview
TABLE name, factions
FROM "world/locations"
WHERE length(factions) > 1
SORT name
```
```

---

### 5. Locations Grouped by Type & Factions

**Purpose:** Cross-tabulate location types against faction control.

**Usage:**

```markdown
# Location Type by Faction Affiliation

**Sogdian-Controlled Cities:**
```dataview
TABLE name, type, resources
FROM "world/locations"
WHERE type = "city" AND contains(factions, "Sogdian Merchants Guild")
SORT name
```

**Contested Trade Posts:**
```dataview
TABLE name, factions, danger_level
FROM "world/locations"
WHERE type = "trade-post" AND length(factions) > 1
SORT name
```
```

---

## How to Use These Queries

1. **Create a note** in `/world/maps/` or `/world/` (e.g., `/world/maps/location_dashboard.md`)
2. **Paste a query** into the note
3. **Switch to reading mode** (Cmd+E on macOS, Ctrl+E on Windows)
4. **Dataview renders the table**
5. **Interact:** Sort by clicking headers, filter by clicking values (in some views)

---

## Customizing Queries

**Change the source directory:**
Replace `FROM "world/locations"` with any other folder.

**Add filter conditions:**
Chain `WHERE` clauses with `AND`/`OR`:
```
WHERE location AND type AND danger_level >= 3 AND contains(factions, "Sogdian")
```

**Sort by multiple fields:**
```
SORT type, name
```

**Show only certain fields:**
```
TABLE name, location, description
```

**Limit results:**
```
LIMIT 10
```

---

## Notes for Lore Keeper

- **Weekly:** Run "Incomplete Locations" query. Flag for GM.
- **Post-session:** Run "Recently Updated" query to see what changed.
- **Before export:** Run "Missing Visibility Tags" to catch unclassified locations.
- **Monthly:** Run "Coordinate Audit" to catch malformed data.

---

## Dataview Documentation

For more complex queries, see the official Dataview docs:
https://blacksmithgu.github.io/obsidian-dataview/

Common functions:
- `contains()` – substring/array membership
- `length()` – string/array length
- `sort()`, `reverse()` – sort arrays
- `date()` – parse dates
- `list()` – create lists from multiple fields
