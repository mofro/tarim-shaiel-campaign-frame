# Kanka Sync v2.0 - Enhanced Features Guide

## What's New in v2.0

### **1. Content Splitting (Public vs. GM)**
Markdown sections are automatically routed:
- **Public sections** → Main entity entry (players see)
- **GM sections** → Separate admin-only posts (GM only)

### **2. Attribute Syncing**
Frontmatter fields automatically create Kanka attributes:
- `elevation` → "Elevation" attribute
- `resources` → "Resources" attribute
- `factions` → "Primary Factions" (with @mentions)
- And more...

### **3. Faction @Mentions**
Factions are converted to clickable entity mentions:
```yaml
factions: ["Sogdian Merchants", "Local Traders"]
```
Becomes: `@Sogdian_Merchants, @Local_Traders` (clickable if entities exist)

### **4. Separate GM Posts**
Each GM section becomes its own post for progressive revelation:
- "Narrative Significance"
- "Hidden Secrets"
- "Plot Hooks"
- etc.

### **5. Relaxed Validation**
Only `kanka_type` required:
- `name` auto-generated from filename
- `is_private` defaults to False (with warning)

---

## Quick Start

### **1. Prepare Your Files**

```bash
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate

# Prepare locations
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

### **2. Test the Sync**

```bash
# Dry run (no changes)
python kanka-sync.py --dry-run
```

**Example Output:**
```
[DRY RUN] turfan.md → location (private=False, 5 attrs, 0 GM posts)
[DRY RUN] samarkand.md → location (private=False, 4 attrs, 2 GM posts)
```

### **3. Sync for Real**

```bash
python kanka-sync.py --sync
```

---

## Content Routing Rules

### **Public Sections (→ Entry HTML)**
These go in the main entity entry field:
- `## Geography`
- `## Economy`
- `## Key Features`
- `## Factions`
- `## Resources`
- `## Waypoint Status`
- `## Cultural Notes`
- `## Historical Basis`

### **GM Sections (→ Separate Posts)**
Each becomes an admin-only post:
- `## Narrative Significance` → Post: "Narrative Significance"
- `## Hidden Secrets` → Post: "Hidden Secrets"
- `## Plot Hooks` → Post: "Plot Hooks"
- `## DM Notes` → Post: "DM Notes"
- `## World-Building Context` → Post: "World-Building Context"

### **Unknown Sections (→ GM Default)**
Any section NOT in the lists above defaults to GM (safe).

---

## Attribute Mappings

### **Frontmatter → Kanka Attributes**

| Your Field | Kanka Attribute | Type | Private? |
|------------|-----------------|------|----------|
| `elevation` | "Elevation" | number | No |
| `location` | "Coordinates" | text | No |
| `mapmarker` | "Map Marker Type" | text | No |
| `resources` | "Resources" | text | No |
| `factions` | "Primary Factions" | text (with @mentions) | No |
| `population` | "Population" | number | No |
| `danger_level` | "Danger Level" | number | No |

**Note:** `historical_basis` frontmatter field is **ignored** (use body section instead).

---

## Example Workflow

### **Your Obsidian File:**

```yaml
---
name: Samarkand
type: city
is_private: false
kanka_type: location
kanka_id: null

elevation: 700
resources: ["silk", "paper"]
factions: ["Sogdian Merchants Guild"]
---

# Samarkand

A jeweled city.

## Geography
Monumental architecture.

## Economy
Famous for textiles.

## Hidden Secrets
The Wizard has an agent here.
```

### **After Sync → Kanka Result:**

**Entity (Location):**
- Name: "Samarkand"
- Type: "city"
- Entry: `<h1>Samarkand</h1><p>A jeweled city.</p><h2>Geography</h2>...`
- is_private: false

**Attributes:**
- Elevation: 700
- Coordinates: (if you had `location` field)
- Resources: silk, paper
- Primary Factions: @Sogdian_Merchants_Guild

**Posts:**
- "Hidden Secrets" (admin-only)
  - Content: `<h2>Hidden Secrets</h2><p>The Wizard has an agent here.</p>`

---

## Validation Rules

### **Required Field:**
- ✅ `kanka_type` - MUST be present

### **Optional Fields:**
- ⚠️ `name` - Auto-generated from filename if missing
- ⚠️ `is_private` - Defaults to `false` with loud warning if missing

### **Example Warnings:**

```
turfan.md: Auto-generated name: 'Turfan'
samarkand.md: ⚠️  PRIVACY WARNING: No 'is_private' field - defaulting to PUBLIC
```

---

## Privacy & Security

### **Fail-Safe Defaults:**
- Missing `is_private`? → Defaults to **public** with warning
- Unknown section? → Routes to **GM post** (conservative)

### **Progressive Revelation:**
GM posts start as admin-only. You can manually change visibility in Kanka UI:
1. Open entity in Kanka
2. Go to Posts tab
3. Edit "Hidden Secrets" post
4. Change visibility: `admin` → `all`
5. Save

Now players see that content!

---

## Troubleshooting

### **"Missing kanka_type field"**
Add to frontmatter:
```yaml
kanka_type: location
```

### **"Auto-generated name: [weird name]"**
Add explicit name:
```yaml
name: Proper Name
```

### **"PRIVACY WARNING"**
Add explicit privacy flag:
```yaml
is_private: false  # or true
```

### **Sections Not Appearing**
Check if section header matches exactly:
- ✅ `## Geography` (works)
- ❌ `## geography` (case-sensitive, goes to GM)
- ❌ `## Geo` (not in list, goes to GM)

### **Factions Not Linking**
Ensure faction entities exist in Kanka first, or they'll just be plain text.

---

## Advanced Usage

### **Add Custom Attributes**

Edit `kanka-sync.py`:

```python
ATTRIBUTE_MAPPINGS = {
    # ... existing ...
    'my_custom_field': ('My Custom Name', 'text', False),
}
```

### **Add Custom Sections**

Edit routing lists:

```python
PUBLIC_SECTION_MARKERS = [
    # ... existing ...
    '## My Custom Section',
]

GM_SECTION_MARKERS = {
    # ... existing ...
    '## My GM Section': 'My GM Post Name',
}
```

---

## Testing Checklist

Before bulk sync:

- [ ] Dry run shows expected entity types
- [ ] Dry run shows expected attribute counts
- [ ] Dry run shows expected GM post counts
- [ ] Test sync 1-2 files
- [ ] Verify in Kanka UI (Overview, Attributes, Posts tabs)
- [ ] Test "View As Player" to confirm GM content hidden
- [ ] Check faction @mentions are clickable
- [ ] Bulk sync remaining files

---

## Command Reference

```bash
# Test connection
python kanka-sync.py --test-connection

# Preview what would sync
python kanka-sync.py --dry-run

# Actually sync
python kanka-sync.py --sync

# Prepare files in bulk
python kanka-bulk-prepare.py --scan
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

---

## What Gets Synced

### ✅ **Synced:**
- Entity core fields (name, type, entry, is_private)
- Attributes (elevation, resources, factions, etc.)
- GM posts (separate, admin-only)
- Tags (if configured)

### ❌ **NOT Synced:**
- `created` / `last_updated` (Kanka auto-generates)
- `historical_basis` frontmatter (use body section instead)
- `mapmarker` (stored as attribute, not used by Kanka maps)
- Leaflet code blocks (stripped)
- Obsidian wiki links (converted to plain text)
- Templates (skipped by filename pattern)

---

## Support

- Logs: `kanka-sync.log`
- Config: `kanka-sync-config.yaml`
- Routing details: `KANKA_CONTENT_ROUTING_PLAN.md`
- Field mappings: `KANKA_FIELD_MAPPINGS.md`
- Full how-to: `KANKA_SYNC_HOWTO.md`

---

**Ready to sync!** 🚀
