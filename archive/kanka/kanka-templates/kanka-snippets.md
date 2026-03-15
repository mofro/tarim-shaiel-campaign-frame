# Kanka Sync Frontmatter Snippets

**Quick snippets to add Kanka fields to existing files.**

> **Note:** These snippets include fields for tag-based sync filtering and hash-based change detection (Option A+B from ARCHITECTURAL_DECISIONS.md).

---

## Location Snippet

```yaml
kanka_type: location
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## Character Snippet

```yaml
kanka_type: character
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## Note Snippet

```yaml
kanka_type: note
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## Quest Snippet

```yaml
kanka_type: quest
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## Organization Snippet

```yaml
kanka_type: organization
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## Item Snippet

```yaml
kanka_type: item
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## Field Explanations

**Core Sync Fields:**
- `kanka_type` - Entity type in Kanka (location, character, note, etc.) - **REQUIRED**
- `is_private` - Player visibility: `false` = public, `true` = GM-only - Defaults to `false`
- `kanka_id` - Kanka entity ID (auto-populated on first sync, leave as `null`)

**Change Detection Fields (Option A+B):**
- `kanka_hash` - MD5 hash of content for change detection (auto-managed by script)
- `tags` - Sync workflow tags for filtering and batch control

---

## Tag Workflow

**Tag States:**
- `needs-sync` - File is ready to sync or has been modified
- `synced` - File is synced and unchanged (auto-set by script)

**Tag Transitions (Automatic):**
```
[New file with needs-sync] → Sync → [synced]
[Edit file] → Manual change tag to needs-sync → Sync → [synced]
```

**Hash-based auto-detection:**
```
[Edit file] → Just save → Sync detects change via hash → [synced]
```

---

## Usage

**Option 1: Copy/Paste**
1. Copy the snippet above
2. Open your markdown file
3. Add to frontmatter

**Option 2: Obsidian Templater**
```javascript
---
<% tp.system.suggester(
  ["location", "character", "note", "quest", "organization", "item"],
  ["location", "character", "note", "quest", "organization", "item"]
) %>
kanka_type: <% tp.system.clipboard() %>
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]
---
```

**Option 3: Bulk Prepare Script**
```bash
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

---

## Private Entity Snippet

For GM-only entities:

```yaml
kanka_type: location  # or character, note, etc.
is_private: true  # ← Hidden from players entirely
kanka_id: null
kanka_hash: null
tags: [needs-sync]
```

---

## With Optional Attributes

**Location with common attributes:**
```yaml
kanka_type: location
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]

# Optional location attributes
elevation: 
resources: []
factions: []
location: []  # [lat, lon]
```

**Character with common attributes:**
```yaml
kanka_type: character
is_private: false
kanka_id: null
kanka_hash: null
tags: [needs-sync]

# Optional character attributes (future implementation)
archetype: 
class: 
tier: 
```

---

## Future: Decomposed Template Structure

These snippets will eventually be decomposed into modular components following the pattern established in `tarim-shaiel-templates/`:

**Planned structure:**
```
/kanka-templates/
├─ kanka-core-fields.md       ← kanka_type, is_private, kanka_id
├─ kanka-sync-fields.md       ← kanka_hash, tags
├─ kanka-location-full.md     ← All location fields combined
├─ kanka-character-full.md    ← All character fields combined
└─ attributes/
   ├─ location-coords.md      ← location: []
   ├─ location-elevation.md   ← elevation:
   └─ character-archetype.md  ← archetype:
```

**Benefits of decomposition:**
- Mix-and-match individual fields
- Cleaner separation of concerns
- Easier to maintain and extend
- Consistent with campaign template pattern

---

See [[../../../utilities/kanka-sync/guides/quickstart|Quickstart Guide]] for setup instructions.
