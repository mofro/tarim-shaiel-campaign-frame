# Phase 2 Testing Workflow

## Step 1: Activate Virtual Environment

```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities/scripts
source venv/bin/activate
```

## Step 2: Verify Phase 2 Script is in Place

```bash
# Check if you have the Phase 2 script
head -5 kanka-sync.py
# Should show "Enhanced v2.1 - Phase 2: Daggerheart Support"
```

If it doesn't show Phase 2, you need to:
1. Download the `kanka-sync-phase2.py` file I provided above
2. Backup your current script: `cp kanka-sync.py kanka-sync.py.backup-pre-phase2`
3. Replace it: `mv ~/Downloads/kanka-sync-phase2.py kanka-sync.py`

## Step 3: Dry Run Test

```bash
python kanka-sync.py --dry-run --sync-one bestiary/test-bear.md
```

**Expected output:**
```
🔍 Dry run mode - no changes will be made

[DRY RUN] test-bear.md → creature (private=False, 0 attrs, 12 DH attrs, 0 GM posts)
```

## Step 4: Live Sync Test

```bash
python kanka-sync.py --sync --sync-one bestiary/test-bear.md
```

Type `yes` when prompted.

**Expected output:**
```
✓ Updated: test-bear.md
  └─ 12 Daggerheart attributes synced
```

## Step 5: Verify in Kanka

Open https://kanka.io and check Test Bear creature:
- **Entry tab**: Brown HTML stat block at top showing all stats
- **Attributes tab**: 12 attributes (Tier, HP, Difficulty, etc.)

## Troubleshooting

If you get import errors:
```bash
pip install --break-system-packages pyyaml markdown requests python-frontmatter
```

If the script isn't Phase 2 yet, download it from the chat above!
