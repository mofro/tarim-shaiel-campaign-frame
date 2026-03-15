# Kanka API Field Mappings Reference

Comprehensive field mappings for all Kanka entity types based on API v1.0 documentation.

---

## Common Fields (All Entities)

These fields are available on **every entity type**:

```yaml
# Required
name: "Entity Name"

# Common Optional Fields
entry: "HTML description/content"
type: "Custom type string" # e.g., "City", "Legendary Warrior"
image: "URL or file path"
is_private: false  # true = admin only, false = visible per role permissions
tags: [1, 2, 3]  # Array of tag IDs

# Auto-generated (read-only)
id: 123
entity_id: 456
campaign_id: 1
created_at: "2025-01-26T00:00:00.000000Z"
updated_at: "2025-01-26T00:00:00.000000Z"
created_by: 1
updated_by: 1

# Optional
tooltip: "Custom tooltip text"
header_image: "URL for header background"
is_template: false
is_attributes_private: false
```

---

## Entity-Specific Fields

### **Locations** (type_id: 3)

```yaml
name: "City Name"
entry: "<p>Description...</p>"
type: "City" # or "Region", "Kingdom", etc.
location_id: 4  # Parent location ID (for nested locations)
is_private: false
tags: []

# Specific to locations
parent_location_id: null  # Alternative to location_id
map_id: null  # Associated map
```

**Available in UI (not all in API):**
- Name
- Type
- Parent Location (nesting)

---

### **Characters** (type_id: 1)

```yaml
name: "Character Name"
entry: "<p>Biography...</p>"
type: "Warrior" # Character class/role
title: "The Breaker"
age: "32" # Can be text or number
sex: "Female" # Gender
pronouns: "she/her"
is_dead: false

# Relationships (foreign keys)
location_id: 2  # Current location
family_id: null  # Primary family
race_id: null  # Primary race
families: [1, 2]  # Multiple families (array)
races: [3, 4]  # Multiple races (array)

# Standard fields
is_private: false
tags: []
```

**Character-Specific Fields:**
- Name, Title, Type
- Age, Gender/Sex, Pronouns
- Location (where they are)
- Family (primary family)
- Families (multiple families)
- Race (primary race)
- Races (multiple races)
- Dead status (is_dead)
- Physical appearance (separate UI section)
- Personality traits (separate UI section)

---

### **Items** (type_id: 5)

```yaml
name: "Sword of Cebolla"
entry: "<p>A legendary blade...</p>"
type: "Weapon"
price: "5000 gold"
size: "Medium"
weight: "5 lbs"

# Relationships
character_id: 12  # Creator/owner
location_id: 5  # Current location

# Standard fields
is_private: false
tags: []
```

**Item Fields:**
- Name, Type
- Price, Size, Weight
- Character (creator/owner)
- Location (where it is)

---

### **Notes** (type_id: 13)

```yaml
name: "GM Notes - Session 3"
entry: "<p>Secret planning...</p>"
type: "Session Prep"
is_private: true  # Typically GM-only
tags: []
```

**Note Fields:**
- Name, Type
- Entry (content)
- Privacy

---

### **Journals** (type_id: 8)

```yaml
name: "Session 3 Recap"
entry: "<p>What happened...</p>"
type: "Session Log"
date: "2025-01-26"  # Date string
calendar_date: "Year 1, Month 3, Day 15"  # Calendar-formatted date

# Relationships
location_id: 8  # Where events occurred
calendar_id: 2  # Associated calendar

# Standard fields
is_private: false
tags: []
```

**Journal Fields:**
- Name, Type
- Date
- Calendar Date
- Location
- Recurring Periodicity (for recurring entries)

---

### **Quests** (type_id: 11)

```yaml
name: "Defeat the Orc Wizard"
entry: "<p>Quest description...</p>"
type: "Main Quest"
date: "2025-01-26"
calendar_date: "Year 1, Month 3, Day 15"
is_completed: false

# Relationships (via sub-endpoints)
characters: [1, 2, 3]  # Quest participants
locations: [5, 6]  # Quest locations
items: [12]  # Quest items
organizations: [4]  # Quest organizations

# Standard fields
is_private: false
tags: []
```

**Quest Fields:**
- Name, Type
- Date, Calendar Date
- Completion status
- Quest Elements (characters, locations, items, orgs)

---

### **Events** (type_id: 10)

```yaml
name: "The Great Battle"
entry: "<p>Event description...</p>"
type: "Battle"
date: "2025-01-26"
location_id: 8

# Standard fields
is_private: false
tags: []
```

**Event Fields:**
- Name, Type
- Date
- Location

---

### **Organizations** (type_id: 4)

```yaml
name: "The Silk Road Merchants"
entry: "<p>Organization description...</p>"
type: "Trade Guild"
location_id: 3  # Headquarters

# Standard fields
is_private: false
tags: []
```

**Organization Fields:**
- Name, Type
- Location (headquarters)
- Members (via organization_members endpoint)

---

### **Families** (type_id: 2)

```yaml
name: "House Stark"
entry: "<p>Family history...</p>"
type: "Noble House"
location_id: 5  # Ancestral home
family_id: null  # Parent family (for nested families)

# Standard fields
is_private: false
tags: []
```

**Family Fields:**
- Name, Type
- Location
- Parent Family (nesting)

---

### **Races** (type_id: 7)

```yaml
name: "Orc"
entry: "<p>Racial description...</p>"
type: "Humanoid"
race_id: null  # Parent race (for subraces)

# Standard fields
is_private: false
tags: []
```

**Race Fields:**
- Name, Type
- Parent Race (for subraces)

---

### **Abilities** (type_id: 9)

```yaml
name: "Fireball"
entry: "<p>Spell description...</p>"
type: "Evocation"
charges: "3/day"
ability_id: null  # Parent ability (for sub-abilities)

# Standard fields
is_private: false
tags: []
```

**Ability Fields:**
- Name, Type
- Charges
- Parent Ability (for nesting)

---

### **Timelines** (type_id: 6)

```yaml
name: "Age of Heroes"
entry: "<p>Timeline description...</p>"
type: "Historical Era"
timeline_id: null  # Parent timeline

# Standard fields
is_private: false
tags: []
```

**Timeline Fields:**
- Name, Type
- Parent Timeline (nesting)

---

### **Calendars** (type_id: 12)

```yaml
name: "Gregorian Calendar"
entry: "<p>Calendar description...</p>"
type: "Solar"
suffix: "CE"  # Calendar suffix (e.g., "AD", "CE")

# Standard fields
is_private: false
tags: []
```

**Calendar Fields:**
- Name, Type
- Suffix

---

### **Maps** (type_id: 14)

```yaml
name: "World Map"
entry: "<p>Map description...</p>"
type: "Regional"
map_id: null  # Parent map (for nested maps)
grid: 50  # Grid size
height: 2000
width: 3000

# Standard fields
is_private: false
tags: []
```

**Map Fields:**
- Name, Type
- Parent Map (nesting)
- Grid, Height, Width
- Map image
- Markers (via map_points endpoint)

---

### **Creatures** (type_id: 20)

```yaml
name: "Dragon"
entry: "<p>Creature description...</p>"
type: "Beast"
creature_id: null  # Parent creature

# Standard fields
is_private: false
tags: []
```

**Creature Fields:**
- Name, Type
- Parent Creature (nesting)

---

## Related Sub-Entities

These are attached to main entities via sub-endpoints:

### **Attributes**

Attributes are key-value pairs attached to any entity:

```yaml
name: "HP"
value: "100"
type: "text"  # text, checkbox, number, section
is_private: false
default_order: 1
api_key: "hp"  # Optional unique identifier
```

**Attribute Types:**
- `text` - Basic text (up to 191 chars)
- `checkbox` - Boolean checkbox
- `number` - Numeric value
- `section` - Section header (no value)
- `attribute` - Reference to another attribute

**Access:** `GET /campaigns/{id}/entities/{entity_id}/attributes`

---

### **Posts**

Posts are like comments/entries attached to entities:

```yaml
name: "Session Notes"
entry: "<p>What happened...</p>"
visibility: "all"  # all, admin, self, members
is_private: false
```

**Access:** `GET /campaigns/{id}/entities/{entity_id}/posts`

---

### **Entity Relations**

Relationships between entities:

```yaml
target_id: 123  # Related entity ID
relation: "ally"  # Relationship type
attitude: 5  # -10 to 10 scale
is_private: false
```

**Access:** `GET /campaigns/{id}/relations`

---

### **Entity Files**

File attachments on entities:

```yaml
name: "Character Portrait"
path: "https://..."
size: 44420  # bytes
type: "image/jpeg"
visibility: "all"
```

**Access:** `GET /campaigns/{id}/entities/{entity_id}/entity_files`

---

## Foreign Field References

When creating entities, you can reference other entities by:

1. **ID** (most direct):
   ```yaml
   location_id: 5
   ```

2. **Name search** (UI only):
   - Type at least 3 characters
   - Prefix with `=` for exact match: `=Alex_Mercer`
   - Use `_` for spaces: `Alex_Mercer_The_Wise`

3. **Create on-the-fly** (UI only):
   - Type `@New_Entity_Name`
   - If not found, Kanka suggests creating it

---

## Privacy & Permissions

### **Entity-Level Privacy**

```yaml
is_private: true  # Only admin role sees this
```

### **Attribute-Level Privacy**

```yaml
attributes:
  - name: "Secret Weakness"
    value: "Fire"
    is_private: true  # Only admin sees this attribute
```

### **Post Visibility Levels**

```yaml
visibility: "all"      # Everyone can see
visibility: "admin"    # Admin role only
visibility: "self"     # Creator only
visibility: "members"  # Campaign members only
```

---

## Module IDs Reference

```
1  = Character
2  = Family
3  = Location
4  = Organization
5  = Item
6  = Timeline
7  = Race
8  = Journal
9  = Ability
10 = Event
11 = Quest
12 = Calendar
13 = Note
14 = Map
20 = Creature
```

---

## Mentions & References

### **Entity Mentions (in entry fields)**

```markdown
@Character_Name        # Basic mention
@=Exact_Name          # Exact match
@New_Entity_Name      # Create if not found
```

### **Advanced Mentions**

```markdown
[entity:123]                    # By ID
[entity:123|Custom Text]        # With custom text
[entity:123|field:location]     # Show specific field
[entity:123|field:entry]        # Embed entry
[entity:123|anchor:post-69]     # Link to specific post
```

### **Attribute References**

```markdown
{HP}                   # Reference attribute by name
{attribute:123}        # Reference by ID
```

---

## API Response Structure

### **List Response**

```json
{
  "data": [
    { /* entity 1 */ },
    { /* entity 2 */ }
  ],
  "links": {
    "first": "...",
    "last": "...",
    "prev": null,
    "next": "..."
  },
  "meta": {
    "current_page": 1,
    "from": 1,
    "last_page": 3,
    "path": "...",
    "per_page": 15,
    "to": 15,
    "total": 42
  }
}
```

### **Single Entity Response**

```json
{
  "data": {
    "id": 123,
    "name": "Entity Name",
    /* ... other fields ... */
  }
}
```

---

## Tips for Obsidian → Kanka Sync

### **Frontmatter Mapping Strategy**

```yaml
---
# Kanka sync fields
kanka_type: location
kanka_id: 123  # Populated after sync
is_private: false

# Your custom Obsidian fields (ignored by sync)
region: tarim-basin
culture: uyghur
population: 50000
tags:
  - city
  - trade-hub
---
```

### **Nested Entities**

For parent/child relationships:

```yaml
# Child location
kanka_type: location
parent_location: "Tarim Basin"  # Map to location_id during sync
```

### **Multi-Value Fields**

```yaml
# Character with multiple families
kanka_type: character
families: ["House Stark", "House Lannister"]  # Map to family IDs
```

### **Custom Attributes**

Store structured data as attributes:

```yaml
kanka_attributes:
  - name: "Population"
    value: "50000"
    type: "number"
  - name: "Wealth Level"
    value: "Rich"
    type: "text"
  - name: "Has Temple"
    value: true
    type: "checkbox"
```

---

## Next Steps

1. **Match your Obsidian frontmatter** to these field structures
2. **Update `kanka-sync.py`** to map custom fields to Kanka fields
3. **Use attributes** for data that doesn't fit standard fields
4. **Test with one entity** before bulk syncing

---

**Reference:** https://app.kanka.io/api-docs/1.0/
