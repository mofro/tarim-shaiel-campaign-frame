---
title: Archived Kanka Sync Documentation
type: archive
category: kanka-sync
created: 2025-01-27
---

# Archived Documentation

**These files have been superseded by the new documentation structure.**

---

## Why Archived?

These documents were the original Kanka sync documentation created during initial development. They've been consolidated and reorganized into a more discoverable structure.

**New documentation location:** `[[../INDEX|Kanka Sync Documentation Index]]`

---

## Archived Files

| File | Replaced By | Notes |
|------|-------------|-------|
| `KANKA_SYNC_HOWTO.md` | [[../guides/quickstart\|Quickstart Guide]] | Original setup guide |
| `KANKA_SYNC_V2_GUIDE.md` | [[../guides/quickstart\|Quickstart Guide]] | v2 features overview |
| `KANKA_CONTENT_ROUTING_PLAN.md` | [[../reference/routing-rules\|Routing Rules]] | Detailed routing plan |
| `KANKA_FIELD_MAPPINGS.md` | [[../reference/field-mappings\|Field Mappings]] | API field reference |
| `OBSIDIAN_KANKA_MAPPING_MATRIX.md` | [[../reference/field-mappings\|Field Mappings]] | Mapping strategy |
| `TESTING_CHECKLIST.md` | [[../troubleshooting/common-issues\|Troubleshooting]] | Testing procedures |
| `obsidian-kanka-sync-guide.md` | [[../guides/quickstart\|Quickstart Guide]] | Early setup guide |

---

## What Changed?

### **Before (Root Directory Sprawl):**
```
/HeroHeaven/
├─ KANKA_SYNC_HOWTO.md
├─ KANKA_SYNC_V2_GUIDE.md
├─ KANKA_CONTENT_ROUTING_PLAN.md
├─ KANKA_FIELD_MAPPINGS.md
├─ OBSIDIAN_KANKA_MAPPING_MATRIX.md
├─ TESTING_CHECKLIST.md
├─ obsidian-kanka-sync-guide.md
└─ ... (hard to find what you need)
```

### **After (Organized Structure):**
```
/utilities/kanka-sync/
├─ INDEX.md                    ← Single entry point
├─ guides/
│  ├─ quickstart.md
│  └─ daily-workflow.md
├─ reference/
│  ├─ field-mappings.md
│  └─ routing-rules.md
└─ troubleshooting/
   └─ common-issues.md
```

---

## Benefits of New Structure

✅ **Single entry point** - INDEX.md as navigation hub  
✅ **Task-based organization** - Guides, reference, troubleshooting  
✅ **Reduced redundancy** - Consolidated overlapping content  
✅ **Better discoverability** - Clear hierarchy and cross-links  
✅ **Obsidian-friendly** - Wiki links, frontmatter, graph view  

---

## Using Archived Files

**These files are kept for:**
- Historical reference
- Detailed technical context
- Comparison with new docs

**If you need information:**
1. Check [[../INDEX|new documentation]] first
2. Use these files only if information is missing
3. Consider updating new docs with missing info

---

## When to Delete?

These files can be safely deleted after:
- ✅ New documentation is verified working
- ✅ No information loss confirmed
- ✅ Team is familiar with new structure
- ✅ 1-2 weeks of usage with new docs

**Recommendation:** Keep for 2-4 weeks, then delete if unused.

---

[[../INDEX|← Back to Documentation Index]]
