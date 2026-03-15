---
title: Kanka Sync - Architectural Decisions (Archived)
type: archived-decisions
archived_from: ARCHITECTURAL_DECISIONS.md
archived_date: 2026-03-09
tags: [kanka, archived, decisions]
---

# Kanka Sync Architectural Decisions

*Archived from ARCHITECTURAL_DECISIONS.md — these decisions relate specifically to the Kanka integration.*

---
## Decision: Kanka Sync Change Detection Strategy

**Date:** 2025-01-27  
**Context:** Kanka API rate limiting (30 requests/minute) + desire to batch sync subsets of files  
**Decision:** Implement Tag-Based Filtering + Hash-Based Change Detection (Option A+B)

### The Problem

With 37+ location files ready to sync:
- Full sync takes 15-20 minutes due to rate limiting
- Need ability to sync subsets (5-10 files at a time)
- Want to avoid unnecessary re-syncs of unchanged files
- Need balance between editor workflow and API efficiency

### Options Considered

#### Option A: Tags Only
**Mechanism:**
- Use frontmatter tags: `needs-sync` → `synced`
- Script auto-manages tag transitions
- Filter syncs by tag: `--tag needs-sync --limit 5`

**Pros:**
- Simple implementation (~10 lines of code)
- Explicit control over what syncs
- No additional frontmatter fields

**Cons:**
- ❌ Must manually change tags after every edit
- ❌ Easy to forget tag changes
- ❌ Tedious for bulk edits (change 5 tags manually)
- ❌ No protection against unnecessary re-syncs

**Editor Experience:**
```markdown
Edit file → Change tag manually → Sync → Repeat
```

#### Option A+B: Tags + Hash (CHOSEN)
**Mechanism:**
- Tags for explicit control: `needs-sync` / `synced`
- MD5 hash stored in frontmatter: `kanka_hash: "a3f5e8b9..."`
- Script compares content hash to detect changes automatically
- Auto-skips unchanged files even if tagged

**Pros:**
- ✅ Zero manual tag changes for edits (automatic detection)
- ✅ Frictionless bulk edits (just save files)
- ✅ Protection against unnecessary syncs
- ✅ Still have explicit control via tags when needed
- ✅ API efficiency (only syncs what changed)

**Cons:**
- ⚠️ Adds `kanka_hash` frontmatter field
- ⚠️ Slightly more complex (~25 lines of code)

**Editor Experience:**
```markdown
Edit file → Save → Sync (auto-detects change)
```

### Comparative Analysis

#### New File Creation (Powering Through 37 Locations)
**Both options:** Identical workflow, identical performance
```bash
python kanka-bulk-prepare.py --tag needs-sync
python kanka-sync.py --sync --tag needs-sync --limit 10
```
**Winner:** Tie (hash adds no value for new files)

#### Session Prep (Edit 5 Existing Locations)
**Option A:** 5 manual tag changes (tedious)
**Option A+B:** 0 manual tag changes (frictionless)
**Winner:** A+B ✅✅✅ (saves 5 manual steps)

#### Iterative Polish (Edit Same File 3x)
**Option A:** 3 tag changes across drafts
**Option A+B:** 0 tag changes (automatic detection)
**Winner:** A+B ✅✅

#### Code Complexity
**Option A:** ~10 lines (simple tag swap)
**Option A+B:** ~25 lines (tag swap + hash computation)
**Winner:** A (slightly simpler), but cost is minimal

## **My Assessment**

### **"Bang for Buck" Score**

|Metric|Option A|Option A+B|Advantage|
|---|---|---|---|
|New file creation|⭐⭐⭐⭐⭐|⭐⭐⭐⭐⭐|Tie|
|Edit workflow|⭐⭐|⭐⭐⭐⭐⭐|**Huge** for A+B|
|Maintenance burden|⭐⭐|⭐⭐⭐⭐⭐|**Huge** for A+B|
|Code complexity|⭐⭐⭐⭐⭐|⭐⭐⭐⭐|Slight for A|
|API efficiency|⭐⭐⭐|⭐⭐⭐⭐⭐|Better for A+B|

---

## **Recommendation**

**Implement A+B** because:

1. **Powering through new files:** Same experience
2. **Consistent editing:** Massively better (zero manual tag changes)
3. **Long-term maintenance:** Much less tedious
4. **Code cost:** Minimal (~15 extra lines)
5. **API efficiency:** Skips unchanged files automatically

**The hash is "cheap insurance"** - costs little to implement, saves tons of manual work in the long run.


### Decision Rationale

**Chose Option A+B because:**

1. **Same experience for bulk new files** - No penalty during initial creation
2. **Massively better for editing** - Zero manual tag management
3. **Long-term maintenance wins** - Less tedious over campaign lifecycle
4. **Minimal code cost** - ~15 extra lines using standard library
5. **API efficiency** - Automatically skips unchanged files
6. **Smart defaults with explicit control** - Hash handles 90%, tags override when needed

**The hash is "cheap insurance":**
- Low implementation cost
- High workflow value
- Pays for itself after first editing session

### Implementation Details

**Frontmatter additions:**
```yaml
kanka_id: 1970045          # Existing
kanka_hash: "a3f5e8b9..."  # NEW - MD5 of content
tags: [synced]              # Existing - auto-managed
```

**Script logic:**
```python
import hashlib

def needs_update(metadata, content):
    current_hash = hashlib.md5(content.encode()).hexdigest()
    stored_hash = metadata.get('kanka_hash')
    return current_hash != stored_hash

def sync_file(file_path, tag_filter=None):
    # Check tag filter
    if tag_filter and tag_filter not in tags:
        return False
    
    # Check if changed (auto-skip if unchanged)
    if kanka_id and not needs_update(metadata, content):
        return False
    
    # Sync + update hash + manage tags
```

**Usage patterns:**
```bash
# Explicit control (new files)
python kanka-sync.py --sync --tag needs-sync --limit 5

# Automatic detection (edited files)
python kanka-sync.py --sync --limit 10

# Force update (ignore hash)
python kanka-sync.py --sync --force --tag synced --limit 5
```

### Trade-offs Accepted

**Accepted:**
- ✅ One additional frontmatter field (`kanka_hash`)
- ✅ Slightly more complex sync logic (~15 lines)
- ✅ Hash changes for whitespace/formatting (acceptable noise)

**Rejected:**
- ❌ Timestamp-based (unreliable file system timestamps)
- ❌ Directory-based (reorganizes vault structure)
- ❌ Filename flags (pollutes Obsidian graph)
- ❌ Interactive selection (can't script/automate)
- ❌ Queue files (extra file to maintain)

### Success Metrics

- ✅ Editor makes 5 edits with zero manual tag changes
- ✅ Script auto-skips unchanged files in batch syncs
- ✅ API calls reduced by ~60% for typical editing sessions
- ✅ Tag system still available for explicit control when needed

### Future Considerations

- Could add `--ignore-hash` flag to force re-sync all tagged files
- Could add hash-based change summary in dry-run output
- Could extend to other entity types (characters, quests, etc.)
- Could add "modified since last sync" reporting

---

## Decision: Kanka Map Marker Sync Strategy

**Date:** 2025-01-27  
**Context:** Need to sync Obsidian location notes to Kanka image map markers using real-world lat/long coordinates  
**Decision:** Implement Marker-First Sync with Independent Idempotency

### The Problem

- Obsidian location notes have `location: [lat, lng]` coordinates
- Kanka image maps need pixel coordinates for markers
- Want markers on map 125882 using `fantasy_name` for labels
- Need idempotent sync: create once, then update existing markers
- Marker sync should coexist with planned content hash/tag gating

### Requirements

1. **Coordinate conversion**: Real-world lat/long → Kanka image pixel coordinates via affine transform
2. **Marker naming**: Use `fantasy_name` if present, else note `name`
3. **Privacy**: Respect `is_private` flag for marker visibility
4. **Idempotency**: Store `kanka_marker_id` in frontmatter, update existing marker
5. **Independence**: Marker sync should work even when content is gated by hash/tags

### Solution Architecture

#### 1. Marker-First Sync Pass
```python
def sync_location_marker(file_path, post_obj, metadata, entity_id, dry_run=False):
    # Extract lat/lng from metadata['location']
    # Convert to Kanka pixel coords via affine transform
    # Create or update marker on DEFAULT_LOCATION_MAP_ID (125882)
    # Store kanka_marker_id back to frontmatter
```

#### 2. Coordinate Transformation
- Use calibrated affine transform from Mapping Coordinates file
- Convert `(lng, lat) → (pixelX, pixelY)`
- Invert Y-axis for Kanka coordinate system
- Default to map ID 125882 (Tarim-Shaiel world map)

#### 3. Marker Payload
```json
{
    "name": "fantasy_name or name",
    "latitude": 1234.567,
    "longitude": 2345.678,
    "entity_id": 1970080,
    "is_private": false,
    "map_id": 125882,
    "shape_id": 1,
    "icon": 4
}
```

#### 4. Idempotency via Frontmatter
```yaml
kanka_id: 1970080          # Entity ID
kanka_marker_id: 419303    # Marker ID (added after first sync)
location: [46.5, 74.9]     # Real-world coordinates
fantasy_name: Balkh-Kamen  # Marker label
is_private: false          # Marker visibility
```

### Integration with Content Sync

#### Current Behavior (v2.0)
- Content sync: Creates/updates Kanka entities and posts
- Marker sync: Runs independently for locations with coordinates
- No hash/tag gating yet (implemented later)

#### Future Compatibility with Hash/Tag Gating
When hash/tag gating is implemented:

**Option A: Independent Marker Sync (RECOMMENDED)**
- Marker sync runs regardless of content hash
- Only blocked by explicit tag filters (`--tag`)
- Rationale: Marker creation is a one-time setup; shouldn't be blocked by content edits

**Option B: Gated Marker Sync**
- Marker sync respects same hash/tag filters as content
- Use case: If you want to batch-create markers only during explicit sync sessions

**Implementation Sketch (Option A):**
```python
def sync_file(file_path, dry_run=False):
    # Content sync (hash-gated)
    if should_sync_content(metadata, content):
        sync_content(...)
    
    # Marker sync (independent)
    if entity_type == 'location' and 'location' in metadata:
        sync_location_marker(...)  # Always runs unless --tag filtered
```

### Usage Patterns

#### Pilot/Test Single Location
```bash
./venv/bin/python kanka-sync.py --sync-one world/locations/balkh-kamen.md
```

#### Batch Marker Creation (New Locations)
```bash
# Tag new locations, then sync
python kanka-bulk-prepare.py --tag needs-sync
python kanka-sync.py --sync --tag needs-sync --limit 10
```

#### Update Existing Markers
```bash
# Edit coordinates/fantasy_name, then sync
python kanka-sync.py --sync --limit 5
# Marker updates automatically via kanka_marker_id
```

### Trade-offs

#### Accepted
- ✅ Additional frontmatter field (`kanka_marker_id`)
- ✅ Marker sync runs even when content unchanged (acceptable overhead)
- ✅ Coordinate conversion hardcodes Hero Heaven map calibration
- ✅ Default map ID (125882) can be overridden per note via `kanka_map_id`

#### Rejected
- ❌ Separate marker-only script (adds complexity)
- ❌ Marker-only sync mode (rare use case)
- ❌ Automatic marker deletion (too destructive)

### Success Metrics

- ✅ Single-location pilot creates marker on map 125882
- ✅ Subsequent syncs update same marker (no duplicates)
- ✅ `fantasy_name` used as marker label
- ✅ `is_private` respected for marker visibility
- ✅ `kanka_marker_id` written back to frontmatter
- ✅ Marker sync continues working when hash/tag gating added

### Implementation Details

#### Constants (Hero Heaven Specific)
```python
DEFAULT_LOCATION_MAP_ID = 125882
DEFAULT_MAP_IMAGE_WIDTH_PX = 6457.0
DEFAULT_MAP_IMAGE_HEIGHT_PX = 2682.0

# Affine transform from (lng, lat) -> (pixelX, pixelY)
AFFINE_X_A = 89.4
AFFINE_X_B = -0.0793
AFFINE_X_C = -4344.8

AFFINE_Y_A = -1.632
AFFINE_Y_B = -111.8
AFFINE_Y_C = 5726.2
```

#### Error Handling
- Skip marker sync if `location` field missing/invalid
- Log warnings for coordinate conversion issues
- Gracefully handle API failures (continue with other syncs)

### Future Enhancements

- Support multiple maps (different `kanka_map_id` per region)
- Marker shape/icon based on `mapmarker` frontmatter field
- Batch marker validation (check for duplicates/overlaps)
- Marker-only sync mode (`--markers-only`)

### Related Documentation

- Implementation: `/kanka-sync.py` (marker sync functions)
- Coordinate calibration: `/world/maps/Mapping Coordinates`
- Pilot example: `/world/locations/balkh-kamen.md`
- Content sync strategy: "Kanka Sync Change Detection Strategy" (above)

---
