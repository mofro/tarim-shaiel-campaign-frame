---
title: Phase 2 Implementation Complete - READY TO DEPLOY
type: implementation-status
created: 2025-01-28
tags: [phase-2, daggerheart, complete, deployment]
---

# Phase 2 Implementation - DEPLOYMENT INSTRUCTIONS

## ✅ STATUS: COMPLETE - Ready for Testing

Phase 2 Daggerheart parsing has been fully implemented and is ready to deploy!

---

## What Was Implemented

### 1. Daggerheart Parsing Functions
- ✅ `extract_daggerheart_blocks()` - Finds and parses `daggerheart` code blocks
- ✅ `daggerheart_to_attributes()` - Converts stat blocks to Kanka attributes
- ✅ `render_statblock_html()` - Creates beautiful HTML stat blocks
- ✅ `render_features_html()` - Renders features as formatted lists

### 2. Updated ContentRouter
- ✅ `split_markdown_content()` now returns 3 values: (public_content, gm_sections, **dh_blocks**)
- ✅ Stat blocks are rendered as HTML and prepended to public content
- ✅ Daggerheart code blocks pass through (not stripped)

### 3. Attribute Mappings
- ✅ Added 12 daggerheart attribute mappings to `ATTRIBUTE_MAPPINGS` dict
- ✅ Prefixed with `dh_` to avoid conflicts with frontmatter

### 4. Enhanced sync_file()
- ✅ Extracts daggerheart blocks during content processing
- ✅ Converts blocks to attributes
- ✅ Syncs daggerheart attributes along with frontmatter attributes
- ✅ Logs daggerheart attribute count in output

### 5. Updated sync_attributes()
- ✅ Now accepts optional `dh_attrs` parameter
- ✅ Skips `dh_` prefixed fields in frontmatter (handled by blocks)
- ✅ Syncs both frontmatter and daggerheart attributes

---

## How to Deploy

### BACKUP FIRST (Important!)
```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities/scripts
cp kanka-sync.py kanka-sync.py.backup-pre-phase2
```

### Replace Script
The new Phase 2 enhanced script has been created on Claude's computer. You have two options:

**Option A: Manual Copy (Safest)**
1. Open this file in your terminal: `/mnt/user-data/uploads/kanka-sync.py` (this is your original backup)
2. The new script needs to be copied from Claude's system to your Mac

**Option B: Use the created script**
I've created the complete Phase 2 script at `/home/claude/kanka-sync-phase2.py`

You'll need to manually copy the enhanced script to your Mac at:
`/Users/mo/Documents/Games/HeroHeaven/utilities/scripts/kanka-sync.py`

**Since I can't directly write to your Mac's filesystem, here's what you need to do:**

1. I'll provide the complete script content in the next message
2. You copy it and paste it into your `kanka-sync.py` file
3. Or ask me to try a different approach to get it onto your filesystem

---

## Testing Plan

Once deployed, run these tests:

### Test 1: Dry Run with test-bear.md
```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities/scripts
python kanka-sync.py --dry-run --sync-one bestiary/test-bear.md
```

**Expected output:**
```
[DRY RUN] test-bear.md → creature (private=False, 0 attrs, 12 DH attrs, 0 GM posts)
```

### Test 2: Live Sync test-bear
```bash
python kanka-sync.py --sync --sync-one bestiary/test-bear.md
```

**Expected results:**
- ✅ Creature updated in Kanka
- ✅ HTML stat block appears at top of entry
- ✅ 12 attributes created: Tier, Adversary Type, Difficulty, Thresholds, HP, Stress, Attack Bonus, Weapon, Range, Damage, Motives, Experiences
- ✅ Features rendered in stat block HTML

### Test 3: Verify in Kanka UI
1. Open Kanka → Creatures → Test Bear
2. **Entry tab:** Should see formatted brown stat block at top
3. **Attributes tab:** Should see all 12 daggerheart attributes
4. **Check values:** Tier=1, HP=7, Difficulty=14, etc.

---

## What Changed in the Code

### Key Differences from v2.0:

**Line 95-117:** Added daggerheart attribute mappings
**Line 120-141:** New `extract_daggerheart_blocks()` function
**Line 143-187:** New `daggerheart_to_attributes()` function
**Line 190-214:** New `render_features_html()` function
**Line 217-268:** New `render_statblock_html()` function
**Line 485 (was 327):** `split_markdown_content()` signature changed - returns 3 values now
**Line 490:** Extracts daggerheart blocks BEFORE processing
**Line 535-539:** Renders stat blocks as HTML and prepends to public content
**Line 541:** Returns dh_blocks as third value
**Line 653-659:** `sync_attributes()` accepts `dh_attrs` parameter
**Line 666-668:** Skips `dh_` prefixed frontmatter fields
**Line 696-705:** Syncs daggerheart attributes
**Line 852:** `split_markdown_content()` call updated for 3 return values
**Line 855-858:** Converts daggerheart blocks to attributes
**Line 874:** Dry run shows DH attr count
**Line 922:** Passes `dh_attrs` to `sync_attributes()`
**Line 929-931:** Logs daggerheart attribute sync

---

## Rollback Procedure

If something breaks:

```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities/scripts
cp kanka-sync.py kanka-sync.py.broken
cp kanka-sync.py.backup-pre-phase2 kanka-sync.py
```

---

## Next Steps After Successful Testing

1. Update `utilities/PHASE_2_IMPLEMENTATION_PLAN.md` with test results
2. Create adversary files using the new template
3. Sync them to Kanka
4. Enjoy queryable stat blocks in Kanka!

Then move on to Phase 3 (if desired):
- Character attribute mappings
- R/H/K balance tracking
- Charm tier progression

---

[[utilities/DAGGERHEART_MIGRATION_PLAN|← Migration Plan]] | [[utilities/PHASE_2_IMPLEMENTATION_PLAN|Implementation Plan →]]
