---
title: Location Note Schema - Frontmatter Specification
project: TTRPG_Tarim_Shaiel
type: schema_reference
status: verified_working
created: 2025-12-13
last_updated: 2025-12-13
---

# Location Note Schema: Minimal Specification & Examples

## Overview
Location Notes are markdown files stored in `/world/locations/` that represent any mappable entity: cities, landmarks, natural features, route nodes, settlements, dungeons, etc. The schema is **minimal by design**—only 5 required fields—with optional properties added as needed.

---

## Core Fields (Required)

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `name` | string | Canonical name of the location | "Samarkand" or "The Naryn River" |
| `location` | [lat, long] | WGS84 coordinates (MUST be array format) | [39.65, 66.97] |
| `type` | string | Entity category | city, landmark, natural-feature, route-node, settlement, sacred-site, dungeon |
| `created` | YYYY-MM-DD | When this location was documented | 2025-12-13 |
| `last_updated` | YYYY-MM-DD | When last modified | 2025-12-13 |

**Critical Note on `location`:** Must be array format `[lat, long]`, NOT a string. This is required for the Leaflet plugin to recognize it.

---

## Marker Styling (Optional but Recommended)

### The `mapmarker` Field

Add this field to control how the location appears on maps:

```yaml
mapmarker: city              # Must match a marker type defined in plugin settings
```

**Configured marker types:**

| Type | Icon | Color | Use For |
|------|------|-------|---------|
| `city` | `fa-building` | Blue | Trade hubs, major cities |
| `sacred-site` | `fa-gopuram` | Gold | Temples, monasteries, pilgrimage sites |
| `marker-dungeon` | `fa-dungeon` | Dark Brown | Dungeons, caves, underground locations |

**Important:** The value must match EXACTLY (case-sensitive) what's defined in Obsidian Leaflet plugin settings.

**If `mapmarker` is omitted:** Location renders with default tan marker.

## Optional Properties (Add as Needed)

These are additional frontmatter fields you might add depending on the location type and narrative needs. **Don't fill them out upfront.** Add them when the location requires that detail.

### Visibility (Optional)

```yaml
visibility: public  # public | secret
```

If `visibility` is omitted, treat it as `public`.

### Descriptive

```yaml
description: "Brief narrative context about what this place is"
history: "Historical background or lore that explains its existence"
fantasy_name: "If different from canonical/real-world name"
```

### Geographic

```yaml
elevation: 2500  # meters
climate: "temperate highland steppe"
terrain: "mountain pass"
water_features: ["river", "springs"]
```

### Narrative & Gameplay

```yaml
narrative_weight: true  # flag for plot-driven importance
factions: ["Sogdian Merchants", "Khwarazmian Guard"]  # affiliation(s)
conflicts: ["trade-route-dispute", "resource-scarcity"]  # context tags
resources: ["silk", "spices", "jade"]  # trade goods or materials
danger_level: 3  # 1-5 scale for encounter difficulty (if applicable)
```

### Cross-Reference

```yaml
connected_routes: 
  - Northern Silk Road
  - Eastern Tributary
settlement_type: "merchant-city"  # further categorization
parent_region: "Transoxiana"  # geographic region it belongs to
```

---

## Tags (Obsidian Tag Syntax)

Tags are added in the note body or in frontmatter tags field. They help organize and filter locations.

### Visibility Tags
Prefer the `visibility` frontmatter field (`public`/`secret`) as the canonical flag.

```yaml
tags:
  - player-visible   # Safe for player exports
  - gm-only          # Never shown to players
  - secret           # Hidden until explicitly revealed
```

### Session/Campaign Tags

```yaml
tags:
- session-1        # Relevant to Session 1 events
- campaign-arc-desert
- test             # For testing/verification
```

### Content Tags (optional organization)

```yaml
tags:
  - faction-sogdian-merchants
  - trade-route-northern
```

### Workflow Tags

```yaml
tags:
  - needs-narrative    # Location needs description
  - incomplete         # Missing data (coords, details)
  - narrative-important
```

---

## Examples

### Example 1: Major City

```markdown
---
name: Samarkand
location: [39.65, 66.97]
type: city
mapmarker: city
created: 2025-12-13
last_updated: 2025-12-13
elevation: 700
fantasy_name: Samarqandh
factions:
  - Sogdian Merchants Guild
resources:
  - textiles
  - luxury goods
  - paper
description: "A major hub on the Silk Road, known for its bazaars and monumental architecture."
tags:
  - player-visible
  - campaign-arc-desert
  - type-city
---

## Samarqandh

A jeweled city where trade routes converge...
```

### Example 2: Sacred Site

```markdown
---
name: Dunhuang
location: [40.15, 94.67]
type: sacred-site
mapmarker: sacred-site
created: 2025-12-13
last_updated: 2025-12-13
narrative_weight: true
description: "Gateway to China; home to the Mogao Caves with thousands of Buddhist artworks."
tags:
  - player-visible
  - campaign-arc-eastern-journey
---

# Dunhuang

A sacred pilgrimage site...
```

### Example 3: Dungeon

```markdown
---
name: The Lost Vault
location: [38.5, 70.3]
type: dungeon
visibility: secret
mapmarker: marker-dungeon
created: 2025-12-13
last_updated: 2025-12-13
danger_level: 4
narrative_weight: true
description: "Underground complex rumored to contain treasures from the fallen age."
tags:
  - gm-only
  - narrative-important
  - plot-hook
---

# The Lost Vault

A dangerous underground location...
```

---

## Template for Quick Authoring

Copy this template when creating a new Location Note:

```markdown
---
name: 
location: [lat, long]
type: 
mapmarker:                    # Optional: city, sacred-site, marker-dungeon, etc.
created: 2025-12-13
last_updated: 2025-12-13
tags:
  - 
---

# [NAME]

## Overview
[Brief description]

## Details
[Add as needed]

## Connections
[Links to related locations, factions, routes]
```

---

## Guidelines

1. **Start minimal.** Fill only the 5 required fields + `mapmarker`. Add optional properties only when you have meaningful data to include.

2. **Coordinates are sacred.** Double-check WGS84 formatting. Swapped lat/long or wrong format breaks maps.
   - ✅ Correct: `location: [39.65, 66.97]`
   - ❌ Wrong: `location: "39.65, 66.97"` (string, not array)

3. **Marker types must match plugin settings.** The `mapmarker` value is case-sensitive and must exist in Obsidian Leaflet plugin settings.
   - ✅ Correct: `mapmarker: city`
   - ❌ Wrong: `mapmarker: City` (if plugin has lowercase "city")

4. **Tags are optional but useful.** Use tags to communicate status (`incomplete`, `needs-narrative`) and intent (`player-visible`, `gm-only`). These drive Dataview queries and publishing filters.

5. **Description over bullet points.** The markdown body is for narrative context, history, and cross-linking. Structured data lives in frontmatter; prose lives in the note.

6. **Link liberally.** Use wikilinks to [[other locations]], [[factions]], [[NPCs]]. This creates your knowledge graph.

7. **Update `last_updated` when substantive changes occur.** This helps Lore Keeper identify stale or recently-modified entries.

---

## Notes for Lore Keeper

- Monitor `/world/locations/` for new notes daily (or per session)
- Flag `#incomplete` and `#needs-narrative` entries in sync reports
- Verify coordinates are valid WGS84 (not swapped, not out-of-bounds, must be array format)
- Ensure `#gm-only` and `#secret` tags are respected in any exported data
- Ensure `mapmarker` values match plugin-configured marker types
- Regenerate GeoJSON exports after new locations are added

---

## Obsidian Templater Setup (Optional)

To auto-populate `created` and `last_updated`, create a template:

```
---
name: 
location: [lat, long]
type: 
mapmarker:
created: <% tp.date.now("YYYY-MM-DD") %>
last_updated: <% tp.date.now("YYYY-MM-DD") %>
tags:
  - 
---
```

Then set up an automation to update `last_updated` on each save (various community plugins support this).

---

## How Markers Work

**Behind the scenes:**
1. You create a Location Note with `location: [lat, long]` and `mapmarker: city`
2. You define marker types in Obsidian Leaflet plugin settings (icon, color, name)
3. Maps use `markerFolder: world/locations` to load all notes in that folder
4. The plugin reads each note's `mapmarker` field and applies the matching icon/color from plugin settings
5. Result: Your locations appear on maps with styled markers

**If a location has no `mapmarker` field:** It still appears, but uses the default tan marker.

**If `mapmarker` references a non-existent marker type:** It still appears with default marker (no error).
