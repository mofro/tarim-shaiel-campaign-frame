---
title: Kanka Sync Documentation
type: documentation-index
category: utilities
tags: [kanka, sync, obsidian, automation]
created: 2025-01-27
---

# Kanka Sync Documentation

**Obsidian → Kanka campaign sync system with content splitting, attribute mapping, and GM post management.**

---

## 🚀 Getting Started

**New to Kanka Sync?** Start here:

1. **[Quickstart Guide](guides/quickstart.md)** - Get syncing in 10 minutes
2. **[Daily Workflow](guides/daily-workflow.md)** - Day-to-day usage patterns

---

## 📚 Documentation Sections

### **Setup** (One-Time)
- Installation & requirements
- API configuration  
- First sync

### **Guides** (How-To)
- [[guides/quickstart|Quickstart Guide]] - Fast setup
- [[guides/daily-workflow|Daily Workflow]] - Regular usage
- Bulk operations - Preparing many files at once

### **Templates** (Content Creation)
- [[utilities/templates/kanka-templates/INDEX|Templates & Snippets]] - Pre-made templates
- Location Template - Full location structure (see templates/INDEX)
- Kanka Snippets - Quick frontmatter (see templates/INDEX)
- Section Snippets - Modular sections (see templates/INDEX)

### **Reference** (Technical Details)
- [[reference/routing-rules|Content Routing Rules]] - How sections are routed
- [[reference/field-mappings|Field Mappings]] - Obsidian → Kanka mappings
- API rate limits - How rate limiting works

### **Troubleshooting** (Problem Solving)
- [[troubleshooting/common-issues|Common Issues & Solutions]] - Fix problems
- Testing checklist - Verify sync is working

---

## 🎯 Common Tasks

**I want to...**

| Task | Guide |
|------|-------|
| Set up sync for the first time | [Quickstart](guides/quickstart.md) |
| Create a new location | [Templates](utilities/templates/kanka-templates/INDEX.md) - See location template |
| Add Kanka fields to existing file | [Templates](utilities/templates/kanka-templates/INDEX.md) - See Kanka snippets |
| Sync a single file | [Daily Workflow](guides/daily-workflow.md) |
| Prepare 30+ files for sync | Bulk Operations |
| Understand what goes where | [Routing Rules](reference/routing-rules.md) |
| Fix sync errors | [Troubleshooting](troubleshooting/common-issues.md) |
| Check field mappings | [Field Mappings](reference/field-mappings.md) |

---

## 📁 File Locations

**Scripts:**
- `/HeroHeaven/kanka-sync.py` - Main sync script
- `/HeroHeaven/kanka-bulk-prepare.py` - Bulk frontmatter tool
- `/HeroHeaven/kanka-sync-config.yaml` - Your configuration

**Logs:**
- `/HeroHeaven/kanka-sync.log` - Sync activity log

**Documentation:**
- `/HeroHeaven/utilities/kanka-sync/` - This directory

---

## ⚡ Quick Reference

### **Key Concepts**

**Content Routing:**
- Public sections → Main entity entry (players see)
- GM sections → Separate admin-only posts
- Unknown sections → Default to GM (safe)

**Frontmatter Fields:**
- `kanka_type` - **REQUIRED** (location, character, note, etc.)
- `is_private` - Optional (defaults to false with warning)
- `kanka_id` - Auto-generated after first sync

**Attributes Created:**
- elevation, resources, factions, coordinates, etc.
- See [Field Mappings](reference/field-mappings.md) for complete list

---

## 🔧 Command Reference

```bash
# Test connection
python kanka-sync.py --test-connection

# Preview changes (no sync)
python kanka-sync.py --dry-run

# Sync files
python kanka-sync.py --sync

# Bulk prepare
python kanka-bulk-prepare.py --scan
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

---

## 📖 Version History

**v2.0 (Current)** - Enhanced sync
- Content splitting (public/GM)
- Attribute syncing
- Separate GM posts
- Smart rate limiting (30 req/min)

**v1.0** - Initial implementation
- Basic entity sync
- Markdown → HTML conversion
- Fail-closed security

---

## 🆘 Need Help?

1. Check [Troubleshooting](troubleshooting/common-issues.md) section
2. Review `kanka-sync.log` for errors
3. Verify configuration in `kanka-sync-config.yaml`

---

## 📝 Related Documentation

**Project Root Docs (To Be Archived):**
- `KANKA_SYNC_HOWTO.md` - Original setup guide
- `KANKA_SYNC_V2_GUIDE.md` - v2 features overview
- `KANKA_CONTENT_ROUTING_PLAN.md` - Detailed routing plan
- `TESTING_CHECKLIST.md` - Testing procedures

*These will be consolidated and archived once new structure is verified.*
