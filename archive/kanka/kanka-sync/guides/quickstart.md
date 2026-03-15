---
title: Kanka Sync Quickstart Guide
type: guide
category: kanka-sync
tags: [kanka, setup, quickstart]
parent: "[[utilities/kanka-sync/INDEX|Kanka Sync Documentation]]"
---

# Kanka Sync Quickstart Guide

**Get your Obsidian vault syncing to Kanka in 10 minutes.**

---

## Prerequisites

- ✅ Python 3.8+ installed
- ✅ Kanka account with API access
- ✅ Campaign created in Kanka

---

## Step 1: Install Dependencies

```bash
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate  # Or create: python3 -m venv venv

pip install -r requirements.txt
```

**Required packages:**
- requests
- python-frontmatter
- markdown
- pyyaml

---

## Step 2: Configure API Access

1. **Get your Kanka API token:**
   - Go to https://kanka.io/en-US/settings/api
   - Create new token
   - Copy token (keep it secret!)

2. **Get your Campaign ID:**
   - Open your campaign in Kanka
   - URL shows: `https://kanka.io/en-US/campaign/12345`
   - Campaign ID = `12345`

3. **Create config file:**

```bash
cp kanka-sync-config.yaml.example kanka-sync-config.yaml
```

Edit `kanka-sync-config.yaml`:

```yaml
kanka:
  api_token: "YOUR_TOKEN_HERE"
  campaign_id: 12345
  base_url: "https://api.kanka.io/1.0"

sync:
  vault_path: "/Users/mo/Documents/Games/HeroHeaven"
  include_paths:
    - "World/Locations"
    # Add more as needed
  exclude_paths:
    - "Templates"
```

---

## Step 3: Test Connection

```bash
python kanka-sync.py --test-connection
```

**Expected:**
```
✓ Connected to campaign: Hero Heaven
```

---

## Step 4: Prepare Your First File

**Option A: Manual (Single File)**

Edit any location file, add to frontmatter:

```yaml
---
name: Turfan
kanka_type: location
is_private: false
kanka_id: null
# ... rest of your frontmatter
---
```

**Option B: Bulk Prepare (Many Files)**

```bash
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

This adds `kanka_type`, `is_private`, and `kanka_id` to all files in the directory.

---

## Step 5: Dry Run (Preview)

```bash
python kanka-sync.py --dry-run
```

**Output shows:**
- Which files will sync
- Entity types
- Attribute counts
- GM post counts

**Example:**
```
[DRY RUN] turfan.md → location (private=False, 5 attrs, 0 GM posts)
```

---

## Step 6: Sync!

```bash
python kanka-sync.py --sync
```

**What happens:**
1. Creates/updates Kanka entities
2. Syncs attributes (elevation, resources, etc.)
3. Creates GM posts (if you have GM sections)
4. Updates frontmatter with `kanka_id`

**Rate limiting:** Script automatically pauses every 30 requests. Be patient!

**First sync (37 files): ~15-20 minutes**

---

## Step 7: Verify in Kanka

1. Go to your Kanka campaign
2. Navigate to Locations
3. Open a synced location

**Check:**
- ✅ Overview tab has public content
- ✅ Attributes tab shows elevation, resources, etc.
- ✅ Posts tab has GM posts (if applicable)
- ✅ "View As Player" hides GM content

---

## What Gets Synced?

### **From Frontmatter → Kanka Attributes**

| Your Field | Kanka Attribute |
|------------|-----------------|
| `elevation` | "Elevation" |
| `resources` | "Resources" |
| `factions` | "Primary Factions" (with @mentions) |
| `location` (coords) | "Coordinates" |

See [[reference/field-mappings|Field Mappings]] for complete list.

---

### **From Body → Kanka Entry/Posts**

**Public Sections (→ Main Entry):**
- ## Geography
- ## Economy
- ## Historical Basis
- ## Factions
- etc.

**GM Sections (→ Separate Posts):**
- ## Narrative Significance
- ## Hidden Secrets
- ## Plot Hooks
- ## DM Notes

See [[reference/routing-rules|Routing Rules]] for complete list.

---

## Daily Workflow

```bash
# 1. Author normally in Obsidian
# 2. Add kanka_type to files ready for players
# 3. Sync when ready

source venv/bin/activate
python kanka-sync.py --sync
```

**Typical update sync: 2-5 minutes**

---

## Troubleshooting

### "Missing kanka_type field"
**Fix:** Add `kanka_type: location` to frontmatter

### "Connection failed"
**Fix:** Check token and campaign_id in config

### "Rate limit reached"
**Normal!** Script automatically pauses and resumes.

### Sections in wrong place
**Fix:** Check section headers match exactly (case-sensitive)

**More help:** See [[../troubleshooting/common-issues|Troubleshooting]]

---

## Next Steps

- Read [[daily-workflow|Daily Workflow]] for regular usage patterns
- Review [[../reference/routing-rules|Routing Rules]] to understand content splitting
- Check [[../reference/field-mappings|Field Mappings]] for all available attributes

---

## Quick Command Reference

```bash
# Test connection
python kanka-sync.py --test-connection

# Scan for Kanka-ready files
python kanka-bulk-prepare.py --scan

# Prepare files
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false

# Preview sync
python kanka-sync.py --dry-run

# Execute sync
python kanka-sync.py --sync

# Check logs
tail -f kanka-sync.log
```

---

**You're all set! Happy syncing!** 🚀

[[INDEX|← Back to Documentation Index]]
