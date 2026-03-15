---
title: Field Mappings Reference
type: reference
category: kanka-sync
tags: [kanka, frontmatter, attributes, fields]
parent: "[[utilities/kanka-sync/INDEX|Kanka Sync Documentation]]"
---

# Field Mappings Reference

**Complete mapping of Obsidian frontmatter fields to Kanka attributes and entity fields.**

---

## Core Entity Fields

These frontmatter fields map directly to Kanka entity core fields:

| Obsidian Field | Kanka Field | Type | Required? | Notes |
|----------------|-------------|------|-----------|-------|
| `name` | `name` | string | Yes* | Auto-generated from filename if missing |
| `kanka_type` | Entity type | string | **YES** | location, character, note, etc. |
| `type` | `type` | string | No | Location type, character archetype, etc. |
| `is_private` | `is_private` | boolean | No* | Defaults to `false` with warning |
| `kanka_id` | `id` | integer | No | Auto-generated after first sync |

*Required for sync, but can be auto-generated.

---

## Attribute Mappings

These frontmatter fields create Kanka attributes:

### **Location Attributes**

| Obsidian Field | Kanka Attribute Name | Type | Private? | Processing |
|----------------|---------------------|------|----------|------------|
| `elevation` | "Elevation" | number | No | Direct value |
| `location` (coords) | "Coordinates" | text | No | Array `[lat, lon]` → `"lat, lon"` |
| `mapmarker` | "Map Marker Type" | text | No | Direct value |
| `resources` | "Resources" | text | No | Array → comma-separated |
| `factions` | "Primary Factions" | text | No | Array → @mentions |
| `population` | "Population" | number | No | Direct value |
| `danger_level` | "Danger Level" | number | No | Direct value |

---

### **Faction @Mentions**

The `factions` field gets special processing:

**Input (frontmatter):**
```yaml
factions:
  - Sogdian Merchants Guild
  - Local Traders Coalition
```

**Output (Kanka attribute):**
```
Attribute: Primary Factions
Value: @Sogdian_Merchants_Guild, @Local_Traders_Coalition
```

**Result:** If these entities exist in Kanka, the @mentions become clickable links.

---

## Fields NOT Mapped

These frontmatter fields are **ignored** by the sync:

| Field | Reason |
|-------|--------|
| `created` | Kanka auto-generates `created_at` |
| `last_updated` | Kanka auto-generates `updated_at` |
| `historical_basis` | Use `## Historical Basis` section instead |
| `tags` | Not yet implemented (future feature) |
| `fantasy_name` | Not implemented (could be added) |

---

## Data Type Conversions

### **Arrays → Comma-Separated Strings**

**Input:**
```yaml
resources: ["silk", "jade", "wool"]
```

**Output:**
```
"silk, jade, wool"
```

### **Coordinates Array → String**

**Input:**
```yaml
location: [42.95, 89.19]
```

**Output:**
```
"42.95, 89.19"
```

### **Booleans → Kanka Booleans**

**Input:**
```yaml
is_private: true
```

**Output:**
```json
{"is_private": true}
```

---

## Character-Specific Fields

*Not yet implemented. Reserved for future expansion.*

Planned mappings:
- `archetype` → Entity type
- `class` → Attribute: "Daggerheart Class"
- `tier` → Attribute: "Tier"
- Charm system → Abilities (separate entities)

---

## Example: Complete Mapping

### **Obsidian File:**

```yaml
---
name: Kashkar
type: city
is_private: false
kanka_type: location
kanka_id: null

# Attributes
elevation: 1289
location: [39.47, 76.02]
mapmarker: city
resources: ["jade", "wool"]
factions: ["Jade Merchants", "Mountain Shepherds"]
population: 15000

# Ignored fields
created: 2025-01-15
last_updated: 2025-01-20
historical_basis: "Tarim Basin city-state"
---

# Kashkar

Gateway where jade flows from mountains to markets.

## Geography
High-altitude oasis city.
```

---

### **Kanka Result:**

**Entity (Location #1970071):**
```json
{
  "name": "Kashkar",
  "type": "city",
  "is_private": false,
  "entry": "<h1>Kashkar</h1><p>Gateway where jade flows...</p>..."
}
```

**Attributes:**
| Name | Value | Type | Private |
|------|-------|------|---------|
| Elevation | 1289 | number | false |
| Coordinates | "39.47, 76.02" | text | false |
| Map Marker Type | "city" | text | false |
| Resources | "jade, wool" | text | false |
| Primary Factions | "@Jade_Merchants, @Mountain_Shepherds" | text | false |
| Population | 15000 | number | false |

---

## Adding Custom Attributes

To add your own attribute mappings:

1. **Edit `kanka-sync.py`**
2. **Find `ATTRIBUTE_MAPPINGS` dictionary**
3. **Add your mapping:**

```python
ATTRIBUTE_MAPPINGS = {
    # ... existing mappings ...
    
    # Your custom field
    'custom_field': ('Custom Attribute Name', 'text', False),
    #               ↑ Kanka name       ↑ type  ↑ is_private
}
```

**Types available:**
- `'text'` - String values
- `'number'` - Numeric values
- `'checkbox'` - True/false (not commonly used)
- `'section'` - Header-only (visual separator)

---

## Attribute Character Limit

**WARNING:** Kanka attributes have a **191 character limit** on the `value` field.

**Safe:**
```yaml
elevation: 1289  # Numbers are always safe
resources: ["silk", "jade"]  # Short arrays are safe
```

**Risky:**
```yaml
# This might exceed 191 chars when joined
resources: ["silk", "jade", "precious metals", "rare earth minerals", ...]
```

**Solution:** Keep attribute values concise. Use body sections for long descriptions.

---

## Validation Rules

### **Required Field: `kanka_type`**

Files **must** have `kanka_type` to sync:

```yaml
kanka_type: location  # Required!
```

Valid values:
- `location`
- `character`
- `note`
- `quest`
- `organization`
- `item`
- And more... see Kanka entity types

### **Optional with Defaults: `is_private`**

```yaml
is_private: false  # Explicit (recommended)
# OR
# (omitted) → Defaults to false with warning
```

### **Optional with Auto-Generation: `name`**

```yaml
name: "Samarkand"  # Explicit (recommended)
# OR
# (omitted) → Generated from filename: "samarkand.md" → "Samarkand"
```

---

## Privacy Settings

### **Entity-Level Privacy**

```yaml
is_private: true  # Entire entity hidden from non-admins
```

**Effect:** Entity doesn't appear in player view at all.

### **Attribute-Level Privacy**

Currently all attributes created by script are **public** (`is_private: false`).

**To make an attribute private:**
1. Sync file normally (creates public attribute)
2. Go to Kanka → Entity → Attributes tab
3. Edit attribute → Check "Private"
4. Save

**Future enhancement:** Could add per-field privacy in script.

---

## Metadata Fields (Not Synced)

These fields are for **your** use in Obsidian only:

```yaml
# Organizational
tags: [player-visible, session-2]
category: locations
region: transoxiana

# Timestamps
created: 2025-01-15
last_updated: 2025-01-20

# Notes
notes: "WIP - needs more detail"
status: draft
```

**Script ignores these.** They help you organize in Obsidian but don't sync to Kanka.

---

## Future Enhancements

Potential future mappings:

```yaml
# Tag system
tags: ["player-visible", "session-2"]
→ Kanka tags (requires tag ID lookup)

# Parent relationships
parent_location: "Transoxiana"
→ location_id (requires entity lookup)

# Images
image: "samarkand.jpg"
→ Upload to Kanka entity_files

# Gallery
images: ["img1.jpg", "img2.jpg"]
→ Multiple entity_files
```

---

## Related Documentation

- [[routing-rules|Content Routing Rules]] - How body content is routed
- [[../guides/quickstart|Quickstart Guide]] - Get started syncing
- [[../INDEX|Documentation Index]] - All docs

---

[[INDEX|← Back to Documentation Index]]
