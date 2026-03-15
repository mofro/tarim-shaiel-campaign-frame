---
title: Phase 2 - Daggerheart Block Parsing Implementation
type: code-changes
created: 2025-01-28
tags: [phase-2, daggerheart, kanka-sync, implementation]
---

# Phase 2: Daggerheart Block Parsing Implementation

## Overview

This document tracks the implementation of daggerheart stat block parsing for Kanka sync.

**Goal:** Parse `daggerheart` code blocks and convert them to:
1. Kanka attributes (queryable fields)
2. HTML stat blocks (formatted display)
3. Features rendering (passive/active abilities)

---

## Changes Required

### 1. Stop Stripping Daggerheart Blocks

**File:** `utilities/scripts/kanka-sync.py`
**Line:** ~320 in `ContentRouter.split_markdown_content()`

**Current:**
```python
# Remove code blocks (except daggerheart blocks - those pass through for stat display)
cleaned = re.sub(r'```(?!daggerheart)[\w]*\n[\s\S]*?```', '', cleaned)
```

**Status:** ✅ Already implemented correctly (uses negative lookahead)

---

### 2. Add Daggerheart Parsing Functions

**Location:** After `ContentRouter` class, before `ObsidianKankaSync` class

**New Functions:**
```python
def extract_daggerheart_blocks(content: str) -> List[Dict]:
    """Find and parse daggerheart code blocks."""
    
def daggerheart_to_attributes(block: Dict) -> List[Dict]:
    """Convert daggerheart block to Kanka attributes."""
    
def render_statblock_html(block: Dict) -> str:
    """Render a nice HTML stat block for entity entry."""
    
def render_features_html(features: List[Dict]) -> str:
    """Render features as HTML list."""
```

---

### 3. Attribute Mappings

**Add to `ATTRIBUTE_MAPPINGS` dict (line ~95):**

```python
# Daggerheart adversary attributes
'dh_tier': ('Tier', 'number', False),
'dh_type': ('Adversary Type', 'text', False),
'dh_difficulty': ('Difficulty', 'number', False),
'dh_thresholds': ('Thresholds', 'text', False),
'dh_hp': ('HP', 'number', False),
'dh_stress': ('Stress', 'number', False),
'dh_attack': ('Attack Bonus', 'text', False),
'dh_weapon': ('Weapon', 'text', False),
'dh_range': ('Range', 'text', False),
'dh_damage': ('Damage', 'text', False),
'dh_motives': ('Motives', 'text', False),
'dh_xp': ('Experiences', 'text', False),
```

**Note:** Prefixed with `dh_` to avoid conflicts with frontmatter fields

---

### 4. Integration Points

#### A. In `ContentRouter.split_markdown_content()`

**Before splitting into sections:**
```python
# Extract daggerheart blocks BEFORE content splitting
dh_blocks = extract_daggerheart_blocks(markdown_body)
```

**After public/GM split:**
```python
# Render stat blocks as HTML and prepend to public content
for block in dh_blocks:
    stat_html = render_statblock_html(block)
    public_content = stat_html + "\n\n" + public_content
    
# Return blocks along with content
return public_content, gm_sections, dh_blocks
```

#### B. Update `split_markdown_content()` signature

**Change from:**
```python
def split_markdown_content(markdown_body: str) -> Tuple[str, Dict[str, str]]:
```

**To:**
```python
def split_markdown_content(markdown_body: str) -> Tuple[str, Dict[str, str], List[Dict]]:
```

#### C. In `ObsidianKankaSync.sync_file()`

**Update the content split call (line ~607):**
```python
# Split content
public_content, gm_sections, dh_blocks = self.router.split_markdown_content(post.content)
```

**After entity creation/update, add daggerheart attributes:**
```python
# Sync daggerheart stat block attributes
if dh_blocks:
    for block in dh_blocks:
        dh_attrs = daggerheart_to_attributes(block)
        for attr_data in dh_attrs:
            attr_name = attr_data['name']
            # Check if exists
            if attr_name in attr_lookup:
                self.api.update_attribute(entity_id, attr_lookup[attr_name]['id'], attr_data)
            else:
                self.api.create_attribute(entity_id, attr_data)
```

---

## Implementation Strategy

### Phase 2.1: Core Parsing (30 min)
1. Add extraction function
2. Test with test-bear.md
3. Verify blocks are found and parsed

### Phase 2.2: Attribute Mapping (20 min)
1. Add attribute mappings to dict
2. Implement `daggerheart_to_attributes()`
3. Test attribute creation in Kanka

### Phase 2.3: HTML Rendering (30 min)
1. Implement `render_statblock_html()`
2. Implement `render_features_html()`
3. Test display in Kanka entry

### Phase 2.4: Integration (30 min)
1. Update `split_markdown_content()` return signature
2. Update `sync_file()` to handle dh_blocks
3. Test end-to-end sync

### Phase 2.5: Testing (30 min)
1. Dry-run test with test-bear.md
2. Live sync test
3. Verify in Kanka UI
4. Test with multiple adversaries

**Total estimated time:** 2.5 hours

---

## Testing Plan

### Test File: `bestiary/test-bear.md`

**Expected Results:**
- ✅ Stat block appears as formatted HTML in Kanka entry
- ✅ Attributes created: Tier (1), Type (Bruiser), Difficulty (14), HP (7), Stress (2)
- ✅ Features rendered as HTML list in stat block
- ✅ Narrative sections still route correctly

### Verification Checklist:
- [ ] Dry run shows daggerheart blocks detected
- [ ] Dry run shows attribute count includes daggerheart fields
- [ ] Live sync creates entity successfully
- [ ] Kanka entry shows formatted stat block at top
- [ ] Kanka attributes tab shows daggerheart stats
- [ ] Kanka attributes are correct types (number vs text)
- [ ] Features display correctly in stat block
- [ ] No duplicate content in entry

---

## Rollback Plan

If issues occur:
1. **Parsing breaks sync:** Comment out daggerheart extraction, code blocks will just appear as-is
2. **Attributes conflict:** Remove dh_ prefix mappings from ATTRIBUTE_MAPPINGS
3. **HTML rendering issues:** Skip stat block rendering, just parse attributes
4. **Full rollback:** Restore from git

---

## Next Steps After Phase 2

**Phase 3 considerations:**
- Character attribute mappings (daggerheart_class, subclass, traits, etc.)
- R/H/K balance tracking in Kanka
- Charm tier progression attributes
- Session notes as posts

---

[[utilities/DAGGERHEART_MIGRATION_PLAN|← Migration Plan]] | [[utilities/kanka-sync/INDEX|Kanka Sync Docs →]]
