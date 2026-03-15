# Obsidian → Kanka Content Routing Plan
**Tarim-Shaiel Campaign - Comprehensive Sorting Strategy**

---

## Executive Summary

This document defines **exactly** how content flows from your Obsidian markdown files into Kanka's entity architecture. Every field, every section, every piece of data has a destination.

---

## Part 1: The Kanka Entity Container Model

Think of each Kanka entity as a **filing system** with specific compartments:

```
┌─────────────────────────────────────────────────┐
│  ENTITY: Samarkand (Location)                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  📋 CORE IDENTITY (API: /locations/{id})        │
│  ├─ name: "Samarkand"                          │
│  ├─ type: "city"                               │
│  ├─ entry: <HTML for Overview tab>            │
│  └─ is_private: false                          │
│                                                 │
│  📊 STRUCTURED DOMAINS (Dedicated APIs)         │
│  ├─ Attributes (/entities/{id}/attributes)    │
│  │  ├─ Elevation: 700                          │
│  │  ├─ Population: 50000                       │
│  │  └─ Resources: "silk, jade"                 │
│  │                                              │
│  ├─ Relations (/entities/{id}/relations)      │
│  │  └─ Allied with Bukhara (+5)                │
│  │                                              │
│  ├─ Files (/entities/{id}/entity_files)       │
│  │  └─ city-map.png                            │
│  │                                              │
│  └─ Map (/maps/{id}/map_points)               │
│     └─ Coordinates, markers                    │
│                                                 │
│  📝 FREEFORM POSTS (/entities/{id}/posts)      │
│  ├─ "GM Notes" (admin-only)                   │
│  │  └─ Narrative Significance                  │
│  │  └─ Hidden Secrets                          │
│  │                                              │
│  └─ "Session 3 Events" (public)               │
│     └─ What happened during gameplay           │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Part 2: Your Obsidian File Structure (Current State)

### **Frontmatter Fields You Use**

```yaml
---
# Required for sync
name: string
kanka_type: location | character | note | etc.
is_private: boolean
kanka_id: number | null

# Metadata
created: YYYY-MM-DD
last_updated: YYYY-MM-DD

# Location-specific
type: city | route-node | sacred-site | etc.
location: [lat, lon]  # Coordinates array
mapmarker: city | sacred-site | marker-dungeon

# Descriptive
description: string
fantasy_name: string
historical_basis: string

# Structured data
elevation: number
resources: array of strings
factions: array of strings

# Tagging
tags: array of strings
---
```

### **Body Sections You Use Consistently**

**Public Sections (Player-Facing):**
- `# [Name]` - Main heading
- Opening paragraph (usually from `description`)
- `## Geography`
- `## Economy`
- `## Key Features`
- `## Factions` or `## Factions Present`
- `## Resources`
- `## Waypoint Status`
- `## Cultural Notes`
- `## Historical Basis`

**GM Sections (Admin-Only):**
- `## Narrative Significance`
- `## Key Narrative Elements`
- `## World-Building Context`
- `## DM Notes`
- `## Hidden Secrets`
- `## Plot Hooks`

**Special/Ignore:**
- ` ```leaflet` code blocks
- Wiki links `[[other-page]]`
- Obsidian comments `%% note %%`

---

## Part 3: Content Routing Matrix

### **ROUTING TABLE: Frontmatter → Kanka**

| Obsidian Field | Kanka Destination | API Endpoint | Type | Notes |
|----------------|------------------|--------------|------|-------|
| `name` | Core: `name` | `/locations/{id}` | string | Direct 1:1 |
| `type` | Core: `type` | `/locations/{id}` | string | Direct 1:1 |
| `is_private` | Core: `is_private` | `/locations/{id}` | boolean | Direct 1:1 |
| `kanka_id` | Core: `id` (read) | `/locations/{id}` | number | Track for updates |
| `kanka_type` | Core: `module` | Via type_id | enum | "location" = 3 |
| `description` | Core: `entry` (partial) | `/locations/{id}` | string | Opening paragraph |
| `fantasy_name` | Core: `entry` (subtitle) | `/locations/{id}` | string | Use in HTML as subtitle |
| **`elevation`** | **Attribute** | `/entities/{id}/attributes` | number | Name: "Elevation" |
| **`location`** | **Attribute** | `/entities/{id}/attributes` | text | Name: "Coordinates" |
| **`mapmarker`** | **Attribute** | `/entities/{id}/attributes` | text | Name: "Map Marker Type" |
| **`historical_basis`** | **Attribute** | `/entities/{id}/attributes` | text | Name: "Historical Basis" |
| **`resources`** | **Attribute** | `/entities/{id}/attributes` | text | Name: "Resources" (join array) |
| **`factions`** | **Attribute** | `/entities/{id}/attributes` | text | Name: "Primary Factions" (join array) |
| `created` | Skip | — | — | Kanka has `created_at` |
| `last_updated` | Skip | — | — | Kanka has `updated_at` |
| `tags` | Core: `tags` | `/locations/{id}` | array | Requires tag ID lookup |

---

### **ROUTING TABLE: Body Sections → Kanka**

| Markdown Section | Kanka Destination | Method | Visibility |
|------------------|------------------|--------|------------|
| `# [Name]` | Core: `entry` | Convert to `<h1>` | Public |
| Opening paragraph | Core: `entry` | Use `description` field | Public |
| `## Geography` | Core: `entry` | Convert to `<h2>` | Public |
| `## Economy` | Core: `entry` | Convert to `<h2>` | Public |
| `## Key Features` | Core: `entry` | Convert to `<h2>` | Public |
| `## Factions` | Core: `entry` | Convert to `<h2>` | Public |
| `## Resources` | Core: `entry` | Convert to `<h2>` | Public |
| `## Waypoint Status` | Core: `entry` | Convert to `<h2>` | Public |
| `## Cultural Notes` | Core: `entry` | Convert to `<h2>` | Public |
| `## Historical Basis` | ⚠️ **Decision Needed** | Attribute OR entry? | Public or Private? |
| **`## Narrative Significance`** | **Post** | Create admin post | **Admin-only** |
| **`## Key Narrative Elements`** | **Post** | Create admin post | **Admin-only** |
| **`## World-Building Context`** | **Post** | Create admin post | **Admin-only** |
| **`## DM Notes`** | **Post** | Create admin post | **Admin-only** |
| **`## Hidden Secrets`** | **Post** | Create admin post | **Admin-only** |
| **`## Plot Hooks`** | **Post** | Create admin post | **Admin-only** |
| ` ```leaflet` blocks | **Strip** | Remove entirely | — |
| `[[wiki-links]]` | **Convert** | Extract text only | — |
| `%% comments %%` | **Strip** | Remove entirely | — |

---

## Part 4: Content Processing Pipeline

### **Step-by-Step Flow**

```
┌─────────────────────────────────────────────┐
│ 1. READ OBSIDIAN FILE                       │
│    ├─ Parse frontmatter (YAML)             │
│    └─ Parse body (Markdown)                │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 2. VALIDATE REQUIRED FIELDS                 │
│    ├─ Check: name, kanka_type, is_private  │
│    └─ FAIL if missing → Skip file          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 3. SPLIT BODY CONTENT                       │
│    ├─ Public sections → public_content     │
│    ├─ GM sections → gm_content             │
│    └─ Strip Leaflet/comments               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 4. BUILD CORE ENTITY DATA                   │
│    ├─ name, type, is_private               │
│    ├─ entry = HTML(public_content)         │
│    └─ tags = resolve_tag_ids()             │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 5. CREATE OR UPDATE ENTITY                  │
│    ├─ If kanka_id exists → UPDATE          │
│    ├─ Else → CREATE                        │
│    └─ Save entity_id for next steps        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 6. SYNC ATTRIBUTES                          │
│    ├─ elevation → Attribute                │
│    ├─ resources → Attribute                │
│    ├─ factions → Attribute                 │
│    ├─ location coords → Attribute          │
│    └─ Create/update each                   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 7. SYNC GM CONTENT (if exists)              │
│    ├─ Check if gm_content is not empty    │
│    ├─ Find existing "GM Notes" post        │
│    ├─ If exists → UPDATE                   │
│    └─ Else → CREATE new post               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│ 8. UPDATE FRONTMATTER                        │
│    ├─ Write kanka_id back to file          │
│    └─ Save file                            │
└─────────────────────────────────────────────┘
```

---

## Part 5: Detailed Content Splitting Logic

### **Public vs. GM Section Detection**

```python
# Configuration
PUBLIC_SECTION_MARKERS = [
    '## Geography',
    '## Economy',
    '## Key Features',
    '## Factions',
    '## Factions Present',
    '## Resources',
    '## Waypoint Status',
    '## Cultural Notes',
    '## Historical Foundation',
    '## Historical Basis'
]

GM_SECTION_MARKERS = [
    '## Narrative Significance',
    '## Key Narrative Elements',
    '## World-Building Context',
    '## DM Notes',
    '## Hidden Secrets',
    '## Plot Hooks',
    '## Secret Information'
]

STRIP_PATTERNS = [
    r'```leaflet.*?```',  # Leaflet code blocks
    r'%%.*?%%',           # Obsidian comments
    r'<!--.*?-->',        # HTML comments
]

def classify_section(header_line):
    """
    Determine if a markdown header is public, gm, or unknown.
    Returns: 'public' | 'gm' | 'unknown'
    """
    header = header_line.strip()
    
    # Check GM markers first (higher priority)
    if any(header.startswith(marker) for marker in GM_SECTION_MARKERS):
        return 'gm'
    
    # Check public markers
    if any(header.startswith(marker) for marker in PUBLIC_SECTION_MARKERS):
        return 'public'
    
    # Unknown header (default to public for safety)
    return 'unknown'


def split_markdown_content(markdown_body):
    """
    Split markdown into public and GM sections.
    
    Returns:
        public_content: str - Public markdown
        gm_content: str - GM-only markdown
    """
    # First, strip code blocks and comments
    cleaned = markdown_body
    for pattern in STRIP_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
    
    lines = cleaned.split('\n')
    public_lines = []
    gm_lines = []
    current_destination = 'public'  # Default
    
    for line in lines:
        # Check if this is a header
        if line.startswith('## '):
            section_type = classify_section(line)
            
            if section_type == 'gm':
                current_destination = 'gm'
            elif section_type == 'public':
                current_destination = 'public'
            # 'unknown' preserves current destination
        
        # Route the line
        if current_destination == 'gm':
            gm_lines.append(line)
        else:
            public_lines.append(line)
    
    public_content = '\n'.join(public_lines).strip()
    gm_content = '\n'.join(gm_lines).strip()
    
    return public_content, gm_content
```

---

### **Example Split**

**Input Markdown:**
```markdown
# Samarkand

A jeweled city.

## Geography
Mountains and valleys.

## Economy
Famous for silk.

## Narrative Significance
Secret convergence point.

## Hidden Secrets
The Wizard has an agent here.

## Factions
Sogdian Merchants Guild.
```

**After Split:**

**`public_content`:**
```markdown
# Samarkand

A jeweled city.

## Geography
Mountains and valleys.

## Economy
Famous for silk.

## Factions
Sogdian Merchants Guild.
```

**`gm_content`:**
```markdown
## Narrative Significance
Secret convergence point.

## Hidden Secrets
The Wizard has an agent here.
```

---

## Part 6: Attribute Mapping Strategy

### **Which Frontmatter Fields Become Attributes**

```python
ATTRIBUTE_MAPPINGS = {
    # Obsidian field: (Kanka name, type)
    'elevation': ('Elevation', 'number'),
    'location': ('Coordinates', 'text'),  # Join array as "lat, lon"
    'mapmarker': ('Map Marker Type', 'text'),
    'historical_basis': ('Historical Basis', 'text'),
    'resources': ('Resources', 'text'),  # Join array
    'factions': ('Primary Factions', 'text'),  # Join array
    'population': ('Population', 'number'),  # If you add this
    'danger_level': ('Danger Level', 'number'),  # If you add this
}

def sync_attributes(entity_id, frontmatter):
    """
    Create/update Kanka attributes from frontmatter fields.
    """
    for obs_field, (kanka_name, attr_type) in ATTRIBUTE_MAPPINGS.items():
        if obs_field not in frontmatter:
            continue  # Skip if not present
        
        value = frontmatter[obs_field]
        
        # Convert arrays to comma-separated strings
        if isinstance(value, list):
            value = ', '.join(str(v) for v in value)
        
        # Convert coordinates array to string
        if obs_field == 'location' and isinstance(value, list):
            value = f"{value[0]}, {value[1]}"
        
        # Create or update the attribute
        existing_attr = find_attribute_by_name(entity_id, kanka_name)
        
        if existing_attr:
            update_attribute(entity_id, existing_attr['id'], {
                'value': str(value),
                'type': attr_type
            })
        else:
            create_attribute(entity_id, {
                'name': kanka_name,
                'value': str(value),
                'type': attr_type,
                'is_private': False
            })
```

---

## Part 7: Entry Field Construction

### **Building the HTML Entry**

```python
def build_entry_html(frontmatter, public_content):
    """
    Construct the HTML for the entity's main entry field.
    
    Strategy:
    1. Start with fantasy_name (if different from name) as subtitle
    2. Add description as opening paragraph
    3. Convert remaining public_content to HTML
    """
    html_parts = []
    
    # Main heading
    name = frontmatter['name']
    fantasy_name = frontmatter.get('fantasy_name', name)
    
    if fantasy_name != name:
        html_parts.append(f'<h1>{fantasy_name}</h1>')
        html_parts.append(f'<p class="subtitle"><em>{name}</em></p>')
    else:
        html_parts.append(f'<h1>{name}</h1>')
    
    # Description as opening paragraph
    if 'description' in frontmatter:
        desc = frontmatter['description']
        html_parts.append(f'<p class="description">{desc}</p>')
    
    # Convert remaining markdown to HTML
    # (This strips the main heading since we already added it)
    body_html = markdown_to_html(public_content, strip_first_h1=True)
    html_parts.append(body_html)
    
    return '\n'.join(html_parts)
```

---

## Part 8: GM Post Management

### **Creating/Updating GM Notes Posts**

```python
def sync_gm_post(entity_id, gm_content):
    """
    Create or update the "GM Notes" post on an entity.
    
    Returns:
        post_id if successful, None otherwise
    """
    if not gm_content or not gm_content.strip():
        return None  # No GM content to sync
    
    # Check if "GM Notes" post already exists
    existing_posts = get_entity_posts(entity_id)
    gm_post = None
    
    for post in existing_posts:
        if post['name'] == 'GM Notes':
            gm_post = post
            break
    
    # Convert GM markdown to HTML
    gm_html = markdown_to_html(gm_content)
    
    post_data = {
        'name': 'GM Notes',
        'entry': gm_html,
        'visibility': 'admin'  # Admin-only
    }
    
    if gm_post:
        # Update existing post
        response = update_post(entity_id, gm_post['id'], post_data)
        return gm_post['id']
    else:
        # Create new post
        response = create_post(entity_id, post_data)
        return response['data']['id']
```

---

## Part 9: Tag Resolution

### **Handling Obsidian Tags → Kanka Tags**

```python
def resolve_tags(tag_names, campaign_id):
    """
    Convert Obsidian tag names to Kanka tag IDs.
    Creates tags if they don't exist.
    
    Args:
        tag_names: List of tag strings (e.g., ["player-visible", "city"])
        campaign_id: Kanka campaign ID
    
    Returns:
        List of tag IDs
    """
    tag_ids = []
    
    # Get all existing tags in campaign
    existing_tags = get_campaign_tags(campaign_id)
    tag_lookup = {tag['name']: tag['id'] for tag in existing_tags}
    
    for tag_name in tag_names:
        if tag_name in tag_lookup:
            # Tag exists, use its ID
            tag_ids.append(tag_lookup[tag_name])
        else:
            # Tag doesn't exist, create it
            new_tag = create_tag(campaign_id, {'name': tag_name})
            tag_ids.append(new_tag['data']['id'])
            tag_lookup[tag_name] = new_tag['data']['id']
    
    return tag_ids
```

---

## Part 10: Complete Sync Function

### **Putting It All Together**

```python
def sync_location_file(filepath, campaign_id):
    """
    Complete sync pipeline for a single location file.
    """
    # 1. Parse file
    with open(filepath, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)
    
    metadata = post.metadata
    body = post.content
    
    # 2. Validate required fields
    required = ['name', 'kanka_type', 'is_private']
    if not all(field in metadata for field in required):
        print(f"❌ {filepath.name}: Missing required fields")
        return False
    
    # 3. Split content
    public_content, gm_content = split_markdown_content(body)
    
    # 4. Build core entity data
    entity_data = {
        'name': metadata['name'],
        'type': metadata.get('type', 'location'),
        'entry': build_entry_html(metadata, public_content),
        'is_private': metadata['is_private']
    }
    
    # Resolve tags
    if 'tags' in metadata:
        entity_data['tags'] = resolve_tags(metadata['tags'], campaign_id)
    
    # 5. Create or update entity
    if metadata.get('kanka_id'):
        # Update existing
        entity = update_location(metadata['kanka_id'], entity_data)
        print(f"✓ Updated: {metadata['name']}")
    else:
        # Create new
        entity = create_location(campaign_id, entity_data)
        # Save ID back to frontmatter
        metadata['kanka_id'] = entity['data']['id']
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        print(f"✓ Created: {metadata['name']} (ID: {entity['data']['id']})")
    
    entity_id = entity['data']['entity_id']
    
    # 6. Sync attributes
    sync_attributes(entity_id, metadata)
    
    # 7. Sync GM post (if content exists)
    if gm_content:
        sync_gm_post(entity_id, gm_content)
        print(f"  └─ GM Notes synced")
    
    return True
```

---

## Part 11: Edge Cases & Decisions

### **Decision Points for You**

#### **A. Historical Basis Section**

Currently goes in both `## Historical Basis` section AND `historical_basis` frontmatter.

**Options:**
1. **Attribute only** - Remove section, keep frontmatter → attribute
2. **Entry only** - Keep section, ignore frontmatter
3. **Both** - Keep redundancy (attribute for data, section for prose)

**Recommendation:** **Option 3** - Attribute for searchability, section for narrative context.

---

#### **B. Factions Handling**

**Options:**
1. **Text Attribute** - `"Sogdian Merchants Guild, Local Traders"`
2. **Separate Organizations** - Create Organization entities, link via Relations
3. **Both** - Attribute for simple list, Relations for detailed factions

**Recommendation:** Start with **Option 1** (text attribute), upgrade to Organizations if factions become central.

---

#### **C. Unknown Section Headers**

What if you add a new section like `## Trade Routes`?

**Options:**
1. **Default to public** (safe, player-facing)
2. **Default to private** (safe, GM-only)
3. **Skip/warn** (conservative, requires explicit config)

**Recommendation:** **Option 1** - Default to public, add to GM markers if sensitive.

---

#### **D. Multiple GM Posts vs. Single Post**

**Options:**
1. **One "GM Notes" post** - All GM sections combined
2. **Multiple posts** - "Narrative Significance", "Hidden Secrets", "Plot Hooks" as separate posts

**Recommendation:** **Option 1** - Simpler, fewer API calls, easier to manage.

---

## Part 12: Testing Strategy

### **Test Cases to Verify**

Before bulk sync, test these scenarios:

#### **Test 1: Minimal Location**
```yaml
---
name: Test City
type: city
is_private: false
kanka_type: location
kanka_id: null
---

# Test City

A simple test location.
```

**Expected:**
- Entity created with name, type
- Entry has `<h1>` and paragraph
- No attributes
- No posts

---

#### **Test 2: Full Location with Attributes**
```yaml
---
name: Rich City
type: city
is_private: false
kanka_type: location
elevation: 1200
resources: ["gold", "iron"]
factions: ["Miners Guild"]
---

# Rich City

A wealthy mining town.

## Economy
Rich in minerals.
```

**Expected:**
- Entity created
- 3 attributes: Elevation, Resources, Primary Factions
- Entry has Economy section

---

#### **Test 3: Location with GM Content**
```yaml
---
name: Secret City
type: city
is_private: false
kanka_type: location
---

# Secret City

Public description.

## Geography
Mountains.

## Narrative Significance
This is where the BBEG hides.
```

**Expected:**
- Entity created with public content only
- Post created: "GM Notes" with Narrative Significance
- Post visibility: admin

---

#### **Test 4: Private Location**
```yaml
---
name: Hidden Vault
type: dungeon
is_private: true
kanka_type: location
---

# Hidden Vault

Secret location players don't know about.
```

**Expected:**
- Entity created with `is_private: true`
- Not visible to non-admins in Kanka

---

#### **Test 5: Update Existing**

Modify `Test City` frontmatter to add `elevation: 500`, run sync again.

**Expected:**
- Entity updated (not duplicated)
- New attribute created: Elevation
- kanka_id unchanged in frontmatter

---

## Part 13: Implementation Checklist

### **Phase 1: Core Pipeline**
- [ ] Parse frontmatter and body
- [ ] Validate required fields
- [ ] Strip Leaflet blocks, comments
- [ ] Build entity data
- [ ] Create/update entity
- [ ] Write kanka_id back to file

### **Phase 2: Content Splitting**
- [ ] Implement `classify_section()`
- [ ] Implement `split_markdown_content()`
- [ ] Test with sample files
- [ ] Verify public/GM separation

### **Phase 3: Attributes**
- [ ] Define `ATTRIBUTE_MAPPINGS`
- [ ] Implement `sync_attributes()`
- [ ] Handle array → string conversion
- [ ] Test attribute creation/updates

### **Phase 4: GM Posts**
- [ ] Implement `sync_gm_post()`
- [ ] Check for existing "GM Notes" post
- [ ] Create if missing, update if exists
- [ ] Verify admin-only visibility

### **Phase 5: Tags**
- [ ] Implement `resolve_tags()`
- [ ] Create missing tags
- [ ] Cache tag lookup
- [ ] Test tag assignment

### **Phase 6: Entry HTML**
- [ ] Implement `build_entry_html()`
- [ ] Handle fantasy_name subtitle
- [ ] Insert description paragraph
- [ ] Convert markdown → HTML
- [ ] Strip first H1 (already in heading)

### **Phase 7: Testing**
- [ ] Run Test Cases 1-5
- [ ] Verify in Kanka UI
- [ ] Check "View As Player"
- [ ] Confirm GM posts invisible

### **Phase 8: Bulk Sync**
- [ ] Dry run on 5 locations
- [ ] Review results
- [ ] Sync all 36 locations
- [ ] Verify no duplicates

---

## Part 14: Configuration File

### **kanka-sync-routing.yaml**

```yaml
# Content routing configuration

public_sections:
  - "## Geography"
  - "## Economy"
  - "## Key Features"
  - "## Factions"
  - "## Factions Present"
  - "## Resources"
  - "## Waypoint Status"
  - "## Cultural Notes"
  - "## Historical Foundation"
  - "## Historical Basis"

gm_sections:
  - "## Narrative Significance"
  - "## Key Narrative Elements"
  - "## World-Building Context"
  - "## DM Notes"
  - "## Hidden Secrets"
  - "## Plot Hooks"
  - "## Secret Information"

attribute_mappings:
  elevation:
    name: "Elevation"
    type: "number"
  location:
    name: "Coordinates"
    type: "text"
  mapmarker:
    name: "Map Marker Type"
    type: "text"
  historical_basis:
    name: "Historical Basis"
    type: "text"
  resources:
    name: "Resources"
    type: "text"
  factions:
    name: "Primary Factions"
    type: "text"

strip_patterns:
  - "```leaflet.*?```"
  - "%%.*?%%"
  - "<!--.*?-->"

defaults:
  unknown_section_destination: "public"  # public | gm | skip
  gm_post_name: "GM Notes"
  gm_post_visibility: "admin"
```

---

## Part 15: Quick Reference

### **One-Page Cheat Sheet**

```
OBSIDIAN FILE → KANKA ROUTING

┌─ FRONTMATTER ─────────────────────────────────────┐
│ name, type, is_private    → Core fields           │
│ elevation, resources      → Attributes             │
│ tags                      → Tag IDs (resolve)      │
│ created, last_updated     → Skip                   │
└───────────────────────────────────────────────────┘

┌─ BODY SECTIONS ───────────────────────────────────┐
│ ## Geography, Economy     → entry (public HTML)    │
│ ## Narrative Significance → Post (admin-only)     │
│ ```leaflet blocks         → Strip                  │
└───────────────────────────────────────────────────┘

┌─ KANKA STRUCTURE ─────────────────────────────────┐
│ Entity                                             │
│ ├─ Core: name, type, entry, is_private           │
│ ├─ Attributes: Elevation, Resources, etc.        │
│ ├─ Tags: [5, 12, 18]                             │
│ └─ Posts: ["GM Notes" (admin)]                   │
└───────────────────────────────────────────────────┘
```

---

## Summary

**This routing plan defines:**
1. ✅ **Where** every field and section goes
2. ✅ **How** content is split (public vs. GM)
3. ✅ **Why** each decision was made
4. ✅ **What** to test before bulk sync

**Next Steps:**
1. Review this plan - do the routing decisions make sense?
2. Confirm edge case handling (Historical Basis, unknown sections)
3. I'll code the enhanced sync script with this logic

**Questions to resolve:**
- Historical Basis: Attribute + section, or pick one?
- Unknown sections: Default to public, GM, or skip?
- Multiple GM posts, or one combined post?

Once you approve this routing plan, I'll implement it in code!
