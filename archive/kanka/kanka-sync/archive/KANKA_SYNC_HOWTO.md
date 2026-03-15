# Kanka Sync How-To Guide
*Complete guide for syncing your Hero Heaven Obsidian vault to Kanka*

---

## Table of Contents
1. [Quick Reference](#quick-reference)
2. [Initial Setup (One-Time)](#initial-setup-one-time)
3. [Daily Workflow](#daily-workflow)
4. [Bulk Preparation Tool](#bulk-preparation-tool)
5. [Troubleshooting](#troubleshooting)

---

## Quick Reference

### **Most Common Commands**

```bash
# Navigate to vault and activate Python environment
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate

# Scan vault to see what needs preparation
python kanka-bulk-prepare.py --scan

# Prepare files for a specific directory
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false

# Test sync (no changes made)
python kanka-sync.py --dry-run

# Actually sync to Kanka
python kanka-sync.py --sync

# Deactivate when done
deactivate
```

### **File Requirements**

Every file MUST have these frontmatter fields to sync:

```yaml
---
kanka_type: location  # or character, note, journal, quest, item, etc.
kanka_id: null        # Auto-populated after first sync
is_private: false     # true = GM-only, false = players can see
---
```

**Security Model:** Files WITHOUT these fields are **ignored** (fail-closed security).

---

## Initial Setup (One-Time)

### **1. Kanka Account Setup**

**A. Create Campaign**
1. Go to https://kanka.io and sign up
2. Create campaign: "Hero Heaven"
3. Note your campaign ID from URL: `https://kanka.io/w/{CAMPAIGN_ID}/dashboard`

**B. Generate API Token**
1. Profile icon → Settings → API
2. "Create New Token" → Name: "Obsidian Sync"
3. **SAVE THE TOKEN** (format: `kanka_XXX...`)

**C. Configure Permissions**
1. Campaign → World → Roles
2. Edit "Player" role:
   - Characters: View, Create, Edit (own only)
   - Locations: View only
   - Quests: View only
   - Notes: No access
3. Save

---

### **2. Python Environment Setup**

```bash
# Navigate to vault
cd /Users/mo/Documents/Games/HeroHeaven

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test installation
python kanka-sync.py --test-connection
```

**Expected Output:**
```
✓ Connected to Kanka API
✓ Campaign found: Hero Heaven (ID: 12345)
```

---

### **3. Configuration**

Edit `kanka-sync-config.yaml`:

```yaml
kanka:
  api_token: "YOUR_KANKA_TOKEN_HERE"
  campaign_id: YOUR_CAMPAIGN_ID_NUMBER
  base_url: "https://api.kanka.io/1.0"

sync:
  vault_path: "/Users/mo/Documents/Games/HeroHeaven"
  include_paths:
    - "World/Locations"
    - "World/Regions"
    - "Characters"
    - "Mechanics"
  exclude_paths:
    - ".obsidian"
    - "Transcripts"
```

---

## Daily Workflow

### **Workflow Overview**

```
1. Author/Edit in Obsidian (normal workflow)
   ↓
2. Add Kanka frontmatter to files ready for players
   ↓
3. Run sync script
   ↓
4. Kanka auto-updates (players see changes)
```

---

### **Step-by-Step Process**

#### **Step 1: Normal Editing in Obsidian**

Just work normally! Create and edit markdown files as usual.

---

#### **Step 2: Mark Files for Kanka**

When a file is ready for players, add frontmatter:

**Manual Method:**
```yaml
---
kanka_type: location
kanka_id: null
is_private: false
---

# Your Content Here
```

**Bulk Method:** See [Bulk Preparation Tool](#bulk-preparation-tool) section below.

---

#### **Step 3: Sync to Kanka**

```bash
# Activate environment
source venv/bin/activate

# Preview what will change (recommended first)
python kanka-sync.py --dry-run

# If preview looks good, sync
python kanka-sync.py --sync

# Check log for any issues
tail kanka-sync.log

# Deactivate when done
deactivate
```

---

#### **Step 4: Verify in Kanka**

1. Log into Kanka
2. Check entities were created/updated
3. Use "View As Player" to test permissions

---

## Bulk Preparation Tool

The bulk preparation tool helps you add Kanka frontmatter to multiple files at once.

### **Overview Scan**

See what needs preparation across your entire vault:

```bash
source venv/bin/activate
python kanka-bulk-prepare.py --scan
```

**Output:**
```
🔍 Scanning vault for Kanka-readiness...

✅ World/Locations              →   1 ready,  36 need prep
⚠️  World/Regions               →   0 ready,   5 need prep
⚠️  Mechanics                   →   0 ready,  24 need prep
⚠️  Characters/Archetypes       →   0 ready,   6 need prep
⚠️  Characters/NPCs             →   0 ready,   0 need prep

==================================================
📊 TOTAL: 1 ready, 71 need preparation
==================================================

💡 To prepare files, use:
   python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

---

### **Preparing Directories**

#### **Player-Visible Locations**

```bash
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

**What happens:**
1. Script shows you which files will be updated
2. Shows what frontmatter will be added
3. Asks for confirmation (`yes/no`)
4. Updates all files in that directory

---

#### **GM-Only Mechanics**

```bash
python kanka-bulk-prepare.py --prepare "Mechanics" --type note --private true
```

This adds `is_private: true` so players won't see these files.

---

#### **Dry Run Mode**

Test without making changes:

```bash
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false --dry-run
```

Preview shows what WOULD happen without actually modifying files.

---

### **Preparation Examples**

#### **Example 1: Prepare All Locations**

```bash
source venv/bin/activate

# Preview first
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false --dry-run

# If good, do it for real
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false

# Output:
# 📁 Directory: World/Locations
# 📊 Status: 1 ready, 36 need preparation
# 
# 🔧 Will add:
#    kanka_type: location
#    kanka_id: null
#    is_private: false
# 
# 📝 Files to update (36):
#    1. changji-pool.md
#    2. dalanzadgad.md
#    3. dunhuang.md
#    ... and 33 more
# 
# ⚠️  Update 36 files? (yes/no): yes
# 
# 🔄 Processing...
#   ✓ Updated changji-pool.md
#   ✓ Updated dalanzadgad.md
#   ...
# 
# ==================================================
# ✅ Complete: 36 updated, 0 failed
# ==================================================
```

---

#### **Example 2: Prepare Character Archetypes**

```bash
python kanka-bulk-prepare.py --prepare "Characters/Archetypes" --type character --private false
```

---

#### **Example 3: Prepare GM Notes**

```bash
python kanka-bulk-prepare.py --prepare "Mechanics" --type note --private true
```

---

### **Bulk Tool Options**

| Option | Description | Example |
|--------|-------------|---------|
| `--scan` | Scan vault and show status | `--scan` |
| `--prepare` | Prepare directory | `--prepare "World/Locations"` |
| `--type` | Kanka entity type | `--type location` |
| `--private` | Privacy setting | `--private false` |
| `--dry-run` | Preview without changes | `--dry-run` |

---

### **Entity Types Reference**

| Obsidian Content | Kanka Type | Private? |
|------------------|------------|----------|
| Locations, Cities, Regions | `location` | Usually `false` |
| Player Characters | `character` | Usually `false` |
| NPCs | `character` | Usually `false` |
| Game Mechanics, Rules | `note` | Usually `true` |
| Session Notes | `journal` | Usually `true` |
| Quests, Adventures | `quest` | Usually `false` |
| Items, Artifacts | `item` | Usually `false` |
| Events, History | `event` | Usually `false` |

---

## Troubleshooting

### **"No module named 'frontmatter'"**

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

### **"API Token Invalid"**

**Cause:** Token expired or incorrect

**Solution:**
1. Generate new token in Kanka (Settings → API)
2. Update `kanka-sync-config.yaml`
3. Test: `python kanka-sync.py --test-connection`

---

### **Files Not Syncing**

**Check:**
1. Does file have `kanka_type` field?
2. Does file have `is_private` field?
3. Is file in an `include_paths` directory?
4. Run with dry-run to see what's detected:
   ```bash
   python kanka-sync.py --dry-run
   ```

---

### **Leaflet Code Blocks Appear in Kanka**

**Expected:** Script automatically strips these during sync.

**If still appearing:**
1. Check `kanka-sync.py` has content cleaning enabled
2. Update the entity manually in Kanka once
3. Re-run sync

---

### **Rate Limit Errors**

**Solution:** Script has built-in delays. If still seeing errors, sync in smaller batches:

```bash
# Prepare and sync just one directory at a time
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
python kanka-sync.py --sync

# Wait 5 minutes, then next batch
python kanka-bulk-prepare.py --prepare "Characters/NPCs" --type character --private false
python kanka-sync.py --sync
```

---

### **YAML Parse Errors**

**Common Issues:**

```yaml
# ❌ BAD - missing quotes
description: The city's main gate

# ✅ GOOD - quoted
description: "The city's main gate"

# ❌ BAD - wrong indentation
tags:
- city
- trade

# ✅ GOOD - consistent indentation
tags:
  - city
  - trade
```

---

## Advanced Usage

### **Selective Sync**

Sync only specific files:

```bash
# Edit kanka-sync.py to add file filtering
# Or manually set kanka_type: null to skip files
```

---

### **Automated Sync (Optional)**

Create a LaunchAgent to auto-sync every hour:

```bash
# Create plist file
nano ~/Library/LaunchAgents/com.herohaven.kankasync.plist

# Add schedule
# Load with: launchctl load ~/Library/LaunchAgents/com.herohaven.kankasync.plist
```

---

### **Backup Before Bulk Operations**

```bash
# Backup your vault before major bulk operations
cp -r /Users/mo/Documents/Games/HeroHeaven ~/Desktop/HeroHeaven-Backup-$(date +%Y%m%d)
```

---

## Workflow Checklist

### **Daily Authoring**
- [ ] Write/edit in Obsidian normally
- [ ] Add frontmatter to files ready for players
- [ ] Run sync when ready to publish

### **Weekly Maintenance**
- [ ] Check Kanka for player-created content
- [ ] Review sync logs for errors
- [ ] Update tokens if needed (yearly)

### **Before Sessions**
- [ ] Sync new session content
- [ ] Verify permissions with "View As Player"
- [ ] Test any new features

---

## Quick Tips

1. **Start Small:** Prepare 5-10 files first, test sync, then bulk prepare rest
2. **Use Dry Run:** Always run `--dry-run` before real sync
3. **Check Logs:** `tail kanka-sync.log` shows what happened
4. **Incremental:** Prepare directories one at a time
5. **Test Permissions:** Use Kanka's "View As" feature frequently

---

## Summary Commands

```bash
# Full workflow
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate

# 1. See what needs work
python kanka-bulk-prepare.py --scan

# 2. Prepare a directory
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false

# 3. Preview sync
python kanka-sync.py --dry-run

# 4. Execute sync
python kanka-sync.py --sync

# 5. Clean up
deactivate
```

---

**That's it! You now have complete control over syncing your Obsidian vault to Kanka.**

Questions? Check the logs: `kanka-sync.log`
