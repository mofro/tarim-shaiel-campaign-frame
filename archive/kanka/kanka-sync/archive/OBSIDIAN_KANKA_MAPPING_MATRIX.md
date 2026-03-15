# Obsidian → Kanka Field Mapping Matrix
**Tarim-Shaiel Campaign**

---

## Executive Summary

This document provides:
1. **Field-by-field mapping** from your current Obsidian schema to Kanka API fields
2. **Strategic recommendations** for what to sync vs. what to keep Obsidian-only
3. **Attribute strategy** for custom data that doesn't fit standard Kanka fields
4. **Body content patterns** for consistent section mapping

---

## Part 1: Location Mapping Matrix

### **Frontmatter → Kanka API Direct Mappings**

| Your Obsidian Field | Maps To Kanka | Notes |
|---------------------|---------------|-------|
| `name` | `name` | ✅ Direct 1:1 |
| `type` | `type` | ✅ Direct 1:1 (e.g., "city", "route-node") |
| `is_private` | `is_private` | ✅ Direct 1:1 boolean |
| `kanka_id` | `id` (read-only) | ✅ Auto-populated after sync |
| `kanka_type` | `module` (via type_id) | ✅ Always "location" (type_id: 3) |
| `description` | `entry` (partial) | ⚠️ Use as opening paragraph in HTML entry |
| `tags` | `tags` (array of IDs) | ⚠️ Requires tag creation in Kanka first |

### **Frontmatter → Kanka Attributes (Custom Data)**

These fields don't have direct Kanka API equivalents, so store as **attributes**:

| Your Obsidian Field | Store As Attribute | Type | Example |
|---------------------|-------------------|------|---------|
| `elevation` | "Elevation" | number | 700 |
| `location` (coordinates) | "Coordinates" | text | "39.65, 66.97" |
| `mapmarker` | "Map Marker Type" | text | "city" |
| `fantasy_name` | Skip (use as subtitle) | — | Use in `entry` HTML |
| `historical_basis` | "Historical Basis" | text | "Tarim Basin - Oasis settlement" |
| `factions` | "Primary Factions" | text | "Sogdian Merchants Guild" |
| `resources` | "Resources" | text | "silk, spices, jade" |
| `created` | Skip | — | Kanka has `created_at` |
| `last_updated` | Skip | — | Kanka has `updated_at` |

**Why use attributes?**
- Kanka doesn't have built-in fields for elevation, coordinates, resources, etc.
- Attributes are flexible key-value pairs you can add to any entity
- They appear in a clean table on the entity page
- They're searchable and can be private

### **Body Content → Kanka Entry (HTML)**

Your location notes have consistent markdown sections. Map them to Kanka's `entry` field as HTML:

| Your Markdown Section | Include in Kanka? | Strategy |
|-----------------------|-------------------|----------|
| `# [Name]` | ✅ Yes | Opening `<h1>` |
| Opening paragraph | ✅ Yes | Use `description` field content |
| `## Geography` | ✅ Yes | Convert to `<h2>Geography</h2>` |
| `## Economy` | ✅ Yes | Convert to `<h2>Economy</h2>` |
| `## Factions` | ✅ Yes | Convert to `<h2>Factions</h2>` |
| `## Historical Basis` | ⚠️ Maybe | Public: Yes, GM-only: Use attribute |
| `## Waypoint Status` | ✅ Yes | Include if player-relevant |
| `## Key Features` | ✅ Yes | Convert to `<h2>Key Features</h2>` |
| Leaflet code blocks | ❌ No | Strip completely (already handled) |
| `## Narrative Significance` | ❌ No | **GM-only**, store as private post |
| `## Key Narrative Elements` | ❌ No | **GM-only**, store as private post |

**Recommended strategy for GM notes:**
- Strip GM sections from main `entry`
- Create a **private post** on the entity with GM content
- Posts support visibility levels: `admin`, `self`, `all`

---

## Part 2: Character Archetype Mapping

Your character archetypes are thematic, not stat-based. Here's how to represent them in Kanka:

### **Archetype → Kanka Character**

| Your Obsidian Field | Maps To Kanka | Notes |
|---------------------|---------------|-------|
| Archetype name | `name` | "The Breaker", "The Bridge", etc. |
| `type` | `type` | "Archetype" or "Hero Template" |
| Thematic description | `entry` (HTML) | Full archetype writeup |
| `is_private` | `is_private: false` | Archetypes are player-visible |

### **Character Fields → Kanka**

When players create actual characters using these archetypes:

| Player Character Field | Maps To Kanka | Notes |
|------------------------|---------------|-------|
| Character name | `name` | "Kaida the Breaker" |
| Archetype | `type` | "Breaker" (links thematic role) |
| Class (Daggerheart) | Attribute: "Class" | "Seraph", "Guardian", etc. |
| Level/Tier | Attribute: "Tier" | 1, 2, or 3 |
| Background story | `entry` | HTML biography |
| Current location | `location_id` | Foreign key to location entity |
| Families/Affiliations | `families` | Array of family entity IDs |

### **Charm System → Kanka Attributes**

Store mechanical details as attributes on character entities:

| Charm System Data | Store As | Type | Example |
|-------------------|----------|------|---------|
| Fatigue Points (FP) | "Fatigue Points (Current)" | number | 12 |
| Fatigue Points (Max) | "Fatigue Points (Max)" | number | 15 |
| Will Points | "Will Points" | number | 3 |
| Hope | "Hope" | number | 2 |
| Competency Areas | "Competencies" | text | "Combat, Diplomacy, Mysticism" |
| Active Charms | See Abilities | — | Link via entity_abilities |

**Charms as Abilities:**
- Each Charm becomes a Kanka **Ability** entity
- Link to character via `entity_abilities` relationship
- Ability fields: `name`, `type` (Tier 1/2/3), `charges`, `entry` (description)

---

## Part 3: Mechanics Notes Mapping

Your mechanics notes are **GM-only** reference material.

### **Mechanics → Kanka Notes**

| Your Obsidian Note | Maps To Kanka | Privacy |
|--------------------|---------------|---------|
| `CHARM_SYSTEM_ANALYSIS.md` | Note entity | `is_private: true` |
| `CELESTIAL_DICE_MECHANICS.md` | Note entity | `is_private: true` |
| `CHARACTER_CREATION_SEQUENCE.md` | Note entity | `is_private: true` |
| `TOOL_EVOLUTION_FRAMEWORK.md` | Note entity | `is_private: true` |

### **Note Mapping**

| Your Field | Maps To Kanka | Notes |
|------------|---------------|-------|
| Document title | `name` | "Charm System Analysis" |
| `type` | `type` | "Mechanics Reference" |
| Full markdown content | `entry` (HTML) | Convert headings, lists, tables |
| `is_private` | `is_private: true` | **Always true** for mechanics |

---

## Part 4: Regional Data Mapping

Regions can be represented as **Locations** with parent/child nesting.

### **Region → Kanka Location**

| Your Field | Maps To Kanka | Notes |
|------------|---------------|-------|
| `region` (name) | `name` | "Transoxiana" |
| `type` | `type` | "Region" or specific like "Trade Hub" |
| `coordinates` | Attribute: "Center Coords" | Store as text |
| `historicalBasis` | Attribute: "Historical Basis" | Text field |
| `magicalElements` | `entry` section | Include as `<h2>Magic</h2>` |
| `keyFactions` | Attribute: "Key Factions" | Or link via Relations |
| `campaignStatus` | Attribute: "Campaign Status" | "unexplored", "active", etc. |

### **Nested Locations**

Use `location_id` for parent/child:

```yaml
# Samarkand (child of Transoxiana region)
name: "Samarkand"
type: "city"
location_id: 12  # ID of Transoxiana region
```

This creates: **Transoxiana** > **Samarkand**

---

## Part 5: Strategic Recommendations

### **What to Sync**

✅ **Sync to Kanka:**
1. **Player-visible locations** (cities, landmarks, sacred sites)
2. **Character archetypes** (as templates/references)
3. **Player characters** (when created)
4. **Public lore** (history, geography, culture)
5. **Quests** (when introduced to players)

❌ **Keep Obsidian-Only:**
1. **GM notes** (narrative significance, plot hooks)
2. **Mechanics analysis** (unless you want Kanka as reference backup)
3. **Session prep** (use Obsidian's linking for this)
4. **Leaflet map code** (incompatible with Kanka)
5. **Templates** (these are authoring tools, not content)

⚠️ **Hybrid Approach:**
1. **Regions** - Sync basic info, keep detailed GM notes in Obsidian
2. **Factions** - Sync public face, keep secret motives in Obsidian
3. **NPCs** - Sync stats/appearance, keep plot connections in Obsidian

---

## Part 6: Attribute Strategy

### **Recommended Attribute Schema**

For **Location** entities, create these standard attributes:

| Attribute Name | Type | Use For |
|----------------|------|---------|
| Coordinates | text | "39.65, 66.97" |
| Elevation | number | 700 |
| Population | number | 50000 |
| Primary Export | text | "Silk, Spices" |
| Danger Level | number | 1-5 scale |
| Historical Basis | text | "Tarim Basin settlement" |
| Map Marker | text | "city" |
| Campaign Status | text | "visited", "rumored", etc. |

For **Character** entities:

| Attribute Name | Type | Use For |
|----------------|------|---------|
| Tier | number | 1, 2, or 3 |
| Archetype | text | "Breaker", "Seeker", etc. |
| Fatigue Points (Current) | number | 12 |
| Fatigue Points (Max) | number | 15 |
| Will Points | number | 3 |
| Hope | number | 2 |
| Competencies | text | "Combat, Mysticism" |
| Daggerheart Class | text | "Seraph", "Guardian" |

**Benefits of this approach:**
- Consistent structure across all entities
- Searchable in Kanka
- Can be made private individually
- Easy to template with Attribute Templates

---

## Part 7: Sync Script Enhancement Recommendations

### **Current Script Status**

Your `kanka-sync.py` currently handles:
- ✅ Basic entity creation (name, type, entry)
- ✅ Privacy flag (`is_private`)
- ✅ Content cleaning (Leaflet blocks, wiki links)
- ✅ Markdown → HTML conversion
- ✅ Fail-closed security (requires explicit fields)

### **Recommended Enhancements**

#### **1. Attribute Sync**

Add function to sync frontmatter → attributes:

```python
def sync_attributes(entity_id, frontmatter_data):
    """Sync specific frontmatter fields as Kanka attributes"""
    
    attribute_mappings = {
        'elevation': {'name': 'Elevation', 'type': 'number'},
        'resources': {'name': 'Resources', 'type': 'text'},
        'factions': {'name': 'Primary Factions', 'type': 'text'},
        'historical_basis': {'name': 'Historical Basis', 'type': 'text'},
        # ... etc
    }
    
    for field, config in attribute_mappings.items():
        if field in frontmatter_data:
            create_or_update_attribute(
                entity_id,
                name=config['name'],
                value=frontmatter_data[field],
                type=config['type']
            )
```

#### **2. GM Note Splitting**

Detect GM-only sections and create private posts:

```python
def split_gm_content(markdown_body):
    """
    Split markdown into:
    - public_content (for main entry)
    - gm_notes (for private post)
    """
    gm_sections = [
        '## Narrative Significance',
        '## Key Narrative Elements',
        '## DM Notes',
        '## Hidden Secrets'
    ]
    
    # ... parse and split logic
    return public_content, gm_notes
```

#### **3. Parent Location Lookup**

For nested locations, resolve names → IDs:

```python
def resolve_parent_location(parent_name, campaign_id):
    """Look up location ID by name for parent relationships"""
    # Search existing locations
    # Return location_id or None
```

#### **4. Tag Management**

Create/sync tags automatically:

```python
def ensure_tags_exist(tag_names, campaign_id):
    """
    Create tags in Kanka if they don't exist
    Return array of tag IDs
    """
    tag_ids = []
    for tag_name in tag_names:
        tag_id = get_or_create_tag(tag_name, campaign_id)
        tag_ids.append(tag_id)
    return tag_ids
```

---

## Part 8: Body Content Mapping Patterns

### **Consistent Section Headers**

Your location notes use these sections consistently. Here's how to map them:

#### **Public Sections (Include in Kanka Entry)**

```markdown
# [Name]                          → <h1>Name</h1>
[opening paragraph from description] → <p>...</p>

## Geography                      → <h2>Geography</h2>
## Economy                        → <h2>Economy</h2>
## Key Features                   → <h2>Key Features</h2>
## Factions Present               → <h2>Factions</h2>
## Resources                      → <h2>Resources</h2>
## Waypoint Status                → <h2>Waypoint Status</h2>
## Cultural Notes                 → <h2>Culture</h2>
```

#### **GM-Only Sections (Create as Private Post)**

```markdown
## Narrative Significance         → Private Post
## Key Narrative Elements          → Private Post
## DM Notes                        → Private Post
## Hidden Secrets                  → Private Post
## Plot Hooks                      → Private Post
```

#### **Skip Entirely**

```markdown
```leaflet                        → Strip (already done)
[internal wiki links]             → Convert to plain text
## Historical Basis                → Move to attribute
```

---

## Part 9: Example Complete Mapping

### **Before (Obsidian)**

```yaml
---
name: Samarkand
location: [39.65, 66.97]
type: city
mapmarker: city
elevation: 700
fantasy_name: Samarqandh
factions: ["Sogdian Merchants Guild"]
resources: ["textiles", "luxury goods", "paper"]
description: "A major hub on the Silk Road..."
is_private: false
kanka_type: location
kanka_id: null
tags:
  - player-visible
  - campaign-arc-desert
---

# Samarqandh

A jeweled city where trade routes converge.

## Geography
- Monumental architecture
- Blue-domed mosques

## Economy
Famous for textiles and paper production.

## Narrative Significance
This is where heroes will converge. Keep secret.
```

### **After Sync (Kanka)**

**Entity (Location):**
```json
{
  "name": "Samarkand",
  "type": "city",
  "entry": "<h1>Samarqandh</h1><p>A jeweled city...</p><h2>Geography</h2><ul><li>Monumental architecture</li></ul><h2>Economy</h2><p>Famous for textiles...</p>",
  "is_private": false,
  "tags": [5, 12]  // IDs for "player-visible", "campaign-arc-desert"
}
```

**Attributes:**
```json
[
  {"name": "Elevation", "value": "700", "type": "number"},
  {"name": "Coordinates", "value": "39.65, 66.97", "type": "text"},
  {"name": "Resources", "value": "textiles, luxury goods, paper", "type": "text"},
  {"name": "Primary Factions", "value": "Sogdian Merchants Guild", "type": "text"},
  {"name": "Map Marker", "value": "city", "type": "text"}
]
```

**Private Post:**
```json
{
  "name": "GM Notes",
  "entry": "<h2>Narrative Significance</h2><p>This is where heroes will converge...</p>",
  "visibility": "admin"
}
```

---

## Part 10: Implementation Roadmap

### **Phase 1: Core Mapping (Current)**
- ✅ Basic entity sync (name, type, entry)
- ✅ Privacy handling
- ✅ Content cleaning
- ✅ Markdown → HTML

### **Phase 2: Attribute Integration (Next)**
1. Add attribute mapping configuration
2. Sync elevation, coordinates, resources, factions
3. Test attribute creation/updates

### **Phase 3: GM Content Splitting**
1. Detect GM sections in markdown
2. Strip from main entry
3. Create as private posts

### **Phase 4: Relationship Handling**
1. Parent location lookup (name → ID)
2. Tag creation/lookup
3. Faction linking (if using Organization entities)

### **Phase 5: Advanced Features**
1. Character-specific fields (races, families)
2. Charm → Ability entity sync
3. Quest integration

---

## Part 11: Quick Reference Cards

### **Location Quick Ref**

```yaml
# SYNC THESE
name: → name
type: → type
description: → entry (opening)
is_private: → is_private

# AS ATTRIBUTES
elevation: → "Elevation"
location: → "Coordinates"
resources: → "Resources"
factions: → "Primary Factions"
historical_basis: → "Historical Basis"

# BODY SECTIONS
Geography, Economy, Key Features → entry HTML
Narrative Significance, DM Notes → private post

# SKIP
created, last_updated → Kanka auto-generates
Leaflet blocks → already stripped
```

### **Character Quick Ref**

```yaml
# SYNC THESE
name: → name
type: (archetype) → type
entry: (bio) → entry
is_private: → is_private

# AS ATTRIBUTES
tier: → "Tier"
fatigue_points: → "Fatigue Points"
will_points: → "Will Points"
hope: → "Hope"
competencies: → "Competencies"
class: → "Daggerheart Class"

# AS RELATIONSHIPS
current_location: → location_id
families: → families array
```

### **Mechanics Notes Quick Ref**

```yaml
# ALWAYS
is_private: true
kanka_type: note

# SYNC
title: → name
type: "Mechanics Reference"
content: → entry (HTML)
```

---

## Part 12: Testing Checklist

Before bulk sync, test these scenarios:

- [ ] Location with all optional fields
- [ ] Location with minimal fields
- [ ] Location with GM sections
- [ ] Character archetype
- [ ] Nested location (city in region)
- [ ] Entity with tags
- [ ] Private note
- [ ] Entity with attributes
- [ ] Entity with multiple factions

---

## Summary: What Goes Where

| Content Type | Sync to Kanka? | Storage Method |
|--------------|---------------|----------------|
| Player-visible locations | ✅ Yes | Entity + Attributes |
| GM location notes | ⚠️ Partial | Entity (public) + Private Post (secrets) |
| Character archetypes | ✅ Yes | Character entities |
| Mechanics rules | ⚠️ Optional | Note entities (private) |
| Session prep | ❌ No | Keep in Obsidian |
| Leaflet maps | ❌ No | Obsidian-only |
| World regions | ✅ Yes | Location entities (parents) |
| Custom coordinates | ✅ Yes | As attributes |
| Resources, factions | ✅ Yes | As attributes |

---

**Next Steps:**
1. Review this mapping
2. Decide which enhancements to prioritize
3. Update `kanka-sync.py` with attribute support
4. Test with 5-10 locations
5. Refine and bulk sync

**Questions to answer:**
- Do you want mechanics notes in Kanka as backup reference?
- Should regions be separate entities or just parent locations?
- How should you handle factions - as attributes or Organization entities?
