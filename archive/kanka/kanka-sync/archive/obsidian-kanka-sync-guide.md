# Obsidian → Kanka Sync Setup Guide

## Overview
This guide will help you set up an automated workflow to sync your Obsidian vault (Hero Heaven) to Kanka while maintaining Obsidian as your source of truth.

## Architecture

```
┌─────────────────┐
│  Obsidian Vault │  ← SOURCE OF TRUTH
│  (Hero Heaven)  │
└────────┬────────┘
         │
         │ Python Script (sync.py)
         │ - Reads markdown files
         │ - Parses frontmatter
         │ - Maps to Kanka entities
         │
         ↓
┌─────────────────┐
│   Kanka API     │
│  (via HTTPS)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Kanka Campaign  │  ← PLAYER-FACING
│ "Hero Heaven"   │     Published view
└─────────────────┘
```

---

## Phase 1: Kanka Setup (15 minutes)

### Step 1.1: Create Kanka Account
1. Go to https://kanka.io
2. Sign up (free tier is sufficient)
3. Create a new campaign: "Hero Heaven"

### Step 1.2: Generate API Token
1. Click your profile icon (top right)
2. Go to **Settings** → **API**
3. Click **Create New Token**
4. Give it a name: "Obsidian Sync"
5. **SAVE THE TOKEN** immediately (you won't see it again)
   - Format: `kanka_XXX...`
   - Store it somewhere safe temporarily

### Step 1.3: Get Your Campaign ID
1. Navigate to your "Hero Heaven" campaign
2. Look at the URL: `https://kanka.io/w/{CAMPAIGN_ID}/dashboard`
3. Note down the `{CAMPAIGN_ID}` number

### Step 1.4: Set Up Roles & Permissions
1. In campaign, click **World** → **Roles**
2. Default roles:
   - **Admin** (you) - sees everything
   - **Player** - configure what they can see
   - **Public** - external viewers
3. For "Player" role:
   - **Character** module: Allow "View", "Create", "Edit" (for own characters)
   - **Location** module: Allow "View" only
   - **Quest** module: Allow "View" only
   - Disable "Delete" on everything
4. Click **Save**

---

## Phase 2: Obsidian Vault Preparation (30 minutes)

### Step 2.1: Establish Frontmatter Schema
Add YAML frontmatter to your markdown files to map them to Kanka entity types.

**Example: Location file (`/World/Locations/Khel-Khor.md`)**
```yaml
---
kanka_type: location
kanka_id: null  # Will be populated after first sync
tags:
  - city
  - trade-hub
parent: null
is_private: false
---

# Khel-Khor

The great trade city at the crossroads of the Silk Road...

## History
[Your content here]

## Notable Features
[Your content here]
```

**Example: Character file (`/Characters/Archetypes/Breaker.md`)**
```yaml
---
kanka_type: character
kanka_id: null
archetype: breaker
tags:
  - hero
  - archetype
is_private: false
---

# The Breaker

Heroes who break bonds and shatter chains...
```

**Example: GM Notes (Private content)**
```yaml
---
kanka_type: note
kanka_id: null
tags:
  - gm-only
  - session-prep
is_private: true  # ← Won't show to players
---

# Session 3 Planning Notes

The heroes will discover...
```

### Step 2.2: Kanka Entity Type Mapping

Map your Obsidian file structure to Kanka entity types:

| Your Obsidian Structure | Kanka Entity Type | Module ID |
|-------------------------|-------------------|-----------|
| `/World/Locations/`     | `location`        | 3         |
| `/Characters/`          | `character`       | 1         |
| `/Mechanics/`           | `note`            | 13        |
| `/Session-Notes/`       | `journal`         | 8         |
| `/Lore/Artifacts/`      | `item`            | 5         |
| `/Quests/`              | `quest`           | 11        |

**Full Kanka Module List:**
- 1 = Character
- 2 = Family
- 3 = Location
- 4 = Organization
- 5 = Item
- 6 = Timeline
- 7 = Race
- 8 = Journal
- 9 = Ability
- 10 = Event
- 11 = Quest
- 12 = Calendar
- 13 = Note
- 14 = Map
- 20 = Creature

### Step 2.3: Create Sync Configuration
Create a config file in your vault root: `/Users/mo/Documents/Games/HeroHeaven/kanka-sync-config.yaml`

```yaml
kanka:
  api_token: "YOUR_TOKEN_HERE"  # Replace with actual token
  campaign_id: YOUR_CAMPAIGN_ID  # Replace with actual ID
  base_url: "https://api.kanka.io/1.0"

sync:
  vault_path: "/Users/mo/Documents/Games/HeroHeaven"
  
  # Directories to sync
  include_paths:
    - "World/Locations"
    - "World/Regions"
    - "Characters"
    - "Mechanics"
    - "Narrative/Awakening-Scenarios"
  
  # Directories to exclude
  exclude_paths:
    - ".obsidian"
    - "Transcripts"
    - "Templates"
  
  # Mapping: Obsidian path prefix → Kanka entity type
  entity_mapping:
    "World/Locations": "location"
    "World/Regions": "location"
    "Characters/Archetypes": "character"
    "Characters/NPCs": "character"
    "Mechanics": "note"
    "Narrative": "journal"
    "Session-Notes": "journal"
    "Quests": "quest"

logging:
  level: "INFO"
  file: "kanka-sync.log"
```

---

## Phase 3: Python Sync Script Setup (45 minutes)

### Step 3.1: Install Dependencies

```bash
cd /Users/mo/Documents/Games/HeroHeaven
python3 -m venv venv
source venv/bin/activate
pip install requests pyyaml python-frontmatter
```

### Step 3.2: Create Sync Script

I'll create the complete script for you in the next step.

### Step 3.3: Test Connection

```bash
python kanka-sync.py --test-connection
```

Expected output:
```
✓ Connected to Kanka API
✓ Campaign found: Hero Heaven (ID: 12345)
✓ Found 3 existing entities
```

---

## Phase 4: Initial Sync (30 minutes)

### Step 4.1: Dry Run
Test without making changes:

```bash
python kanka-sync.py --dry-run
```

Review output:
```
[DRY RUN] Would create: Characters/Archetypes/Breaker.md → Character
[DRY RUN] Would create: World/Locations/Khel-Khor.md → Location
[DRY RUN] Would skip: Templates/Character-Template.md (excluded)
...
Total: 23 files would be synced
```

### Step 4.2: Actual Sync
If dry run looks good:

```bash
python kanka-sync.py --sync
```

### Step 4.3: Verify in Kanka
1. Log into Kanka
2. Navigate to your campaign
3. Check that entities were created
4. Verify permissions (use "View As" feature)

---

## Phase 5: Ongoing Workflow

### Daily Workflow

1. **Author in Obsidian** (your normal process)
   - Create/edit markdown files
   - Use your existing tools/plugins
   - Maintain frontmatter

2. **Sync to Kanka** (when ready to publish)
   ```bash
   python kanka-sync.py --sync
   ```

3. **Review Player Changes** (weekly/as needed)
   ```bash
   python kanka-sync.py --pull-player-updates
   ```
   - Script will download player-edited characters
   - Creates `/Player-Updates/` folder with changes
   - You manually merge into your vault

### Automated Sync (Optional)

**macOS LaunchAgent** (runs every hour):

```bash
# Create launch agent
mkdir -p ~/Library/LaunchAgents

# I'll create the plist file for you
```

---

## Phase 6: Permission Testing (15 minutes)

### Step 6.1: Create Test Player Account
1. Create a second account (use different email/incognito)
2. Join campaign via invitation
3. Assign to "Player" role

### Step 6.2: Test Permissions
1. Login as player
2. Verify you can:
   - View public locations
   - View public NPCs
   - Create/edit a character assigned to you
3. Verify you CANNOT:
   - See GM-only notes (`is_private: true`)
   - Delete anything
   - Edit locations/NPCs

### Step 6.3: Use "View As" Feature
1. Login as GM
2. Go to **World** → **Members**
3. Click "View As" next to test player
4. Confirm experience matches expectations

---

## Conflict Resolution Strategy

### Scenario 1: You Edit in Obsidian, Player Edits in Kanka

**Sync Direction:** Obsidian → Kanka (overwrites by default)

**To preserve player edits:**
1. Before syncing, run: `python kanka-sync.py --pull-player-updates`
2. Review changes in `/Player-Updates/`
3. Manually merge into Obsidian
4. Then sync: `python kanka-sync.py --sync`

### Scenario 2: Concurrent Edits

**Prevention:**
- Player edits ONLY their assigned character
- You edit everything else
- Use Kanka's entity-level permissions to enforce

**If it happens:**
- Script detects `updated_at` mismatch
- Prompts you to choose: Keep Obsidian / Keep Kanka / Merge manually

---

## Troubleshooting

### "API Token Invalid"
- Regenerate token in Kanka
- Update `kanka-sync-config.yaml`
- Tokens expire after 364 days

### "Entity Not Found"
- Check `kanka_id` in frontmatter matches Kanka
- If deleted in Kanka, set `kanka_id: null` to recreate

### "Rate Limit Exceeded"
- Script automatically respects rate limits
- If syncing many files, add delays (built into script)

### "Frontmatter Parse Error"
- Validate YAML syntax
- Common issues: unquoted colons, incorrect indentation

---

## Next Steps

1. **Review this guide completely**
2. **Complete Phase 1 (Kanka Setup)**
3. **Ask me to generate the Python script** when ready
4. **Test with a small subset** of files first
5. **Iterate on frontmatter schema** as needed

---

## Questions to Answer Before Proceeding

1. **Do you want to sync ALL files or just specific directories?**
   - Recommendation: Start with just Locations + Characters

2. **How often do you want to sync?**
   - Manual (run command when ready)
   - Automated (hourly/daily via cron/LaunchAgent)

3. **What should happen to player-created content?**
   - Pull into special folder for manual merge
   - Auto-merge if no conflicts (risky)

4. **Do you want bi-directional sync or one-way?**
   - Recommendation: Start with one-way (Obsidian → Kanka)

Let me know when you're ready for the Python script!
