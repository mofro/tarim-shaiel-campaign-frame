# Tier 1 Equipment Converter - Usage Guide

## Quick Start

### 1. Download and Install

Download the `srd-equipment-converter.py` file from the chat above and save it to your utilities/scripts directory:

```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities/scripts
# Move downloaded file here
chmod +x srd-equipment-converter.py
```

### 2. Run the Converter

```bash
# Activate venv first
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate

# Run converter
cd utilities/scripts
python srd-equipment-converter.py
```

### 3. Review Output

The converter creates files in `/equipment/`:
- `/equipment/weapons/` - ~32 Tier 1 weapons
- `/equipment/armor/` - 4 Tier 1 armor pieces

### 4. Sync to Kanka

```bash
# Sync all equipment
python kanka-sync.py --sync

# Or sync individually
python kanka-sync.py --sync --sync-one equipment/weapons/Longsword.md
```

---

## What Gets Converted

### Tier 1 Weapons (~32 files)
Basic weapons that Tier 1 characters use:
- **Melee:** Longsword, Shortsword, Dagger, Battleaxe, Mace, Warhammer, etc.
- **Ranged:** Longbow, Shortbow, Crossbow, Hand Crossbow
- **Two-Handed:** Greatsword, Greatstaff, Halberd, Dualstaff
- **Shields:** Round Shield, Tower Shield
- **Magic:** Wand, Scepter, Arcane Gauntlets, Glowing Rings, etc.

### Tier 1 Armor (4 files)
The four basic armor types:
- **Leather Armor** (Light) - Thresholds: 6/13, Score: 3
- **Gambeson Armor** (Light) - Thresholds: 7/14, Score: 3
- **Chainmail Armor** (Medium) - Thresholds: 8/15, Score: 4
- **Full Plate Armor** (Heavy) - Thresholds: 9/16, Score: 5

---

## Output Format

### Weapon Example

**Input (SRD format):**
```markdown
# Longsword

**_Tier 1_** _Primary_ _Physical_ _Weapon_

- **Trait:** Agility
- **Range:** Melee
- **Damage:** d10+3 phy
- **Burden:** Two-Handed
```

**Output (Kanka-ready):**
```markdown
---
kanka_type: item
is_private: false
name: Longsword
type: weapon
tags: [tier-1, weapon, daggerheart-srd]
weapon_tier: 1
weapon_type: Primary
weapon_damage_type: Physical
weapon_trait: Agility
weapon_range: Melee
weapon_damage: d10+3 phy
weapon_burden: Two-Handed
---

# Longsword

**Tier 1 Primary Physical Weapon**

## Stats

- **Trait:** Agility
- **Range:** Melee
- **Damage:** d10+3 phy
- **Burden:** Two-Handed

*Standard equipment from the Daggerheart SRD.*
```

### Armor Example

**Input:**
```markdown
# Leather Armor

**_Tier 1_** _Armor_

- **Base Thresholds:** 6 / 13
- **Base Score:** 3
```

**Output:**
```markdown
---
kanka_type: item
is_private: false
name: Leather Armor
type: armor
tags: [tier-1, armor, daggerheart-srd]
armor_tier: 1
armor_thresholds: 6 / 13
armor_score: 3
---

# Leather Armor

**Tier 1 Armor**

## Stats

- **Base Thresholds:** 6 / 13
- **Base Score:** 3

*Standard equipment from the Daggerheart SRD.*
```

---

## Benefits

### In Kanka
Once synced, you'll have:
- ✅ All Tier 1 equipment as queryable items
- ✅ Searchable by tags (weapon, armor, tier-1)
- ✅ Filterable attributes (damage, range, trait, etc.)
- ✅ Quick reference during sessions
- ✅ Can link to PC/NPC character sheets

### Attributes Created
**Weapons:**
- `weapon_tier` - Queryable tier level
- `weapon_type` - Primary/Secondary
- `weapon_damage_type` - Physical/Magical
- `weapon_trait` - Agility/Strength/Finesse/etc.
- `weapon_range` - Melee/Close/Far/Very Far
- `weapon_damage` - Dice notation
- `weapon_burden` - One-Handed/Two-Handed

**Armor:**
- `armor_tier` - Queryable tier level
- `armor_thresholds` - Defense values
- `armor_score` - Armor score

---

## Customization

After conversion, you can:
- Add Hero Heaven-specific lore to items
- Adjust stats for your world
- Add custom tags (e.g., `silk-road`, `faction-specific`)
- Link items to NPCs/locations/factions

---

## Troubleshooting

### Converter fails to find SRD files
Make sure the SRD is at:
```
/Users/mo/Documents/Games/HeroHeaven/references/daggerheart-srd/
```

### Can't sync to Kanka
1. Check you're in venv: `source ../../venv/bin/activate`
2. Check config: `kanka-sync-config-test.yaml` exists
3. Test connection: `python kanka-sync.py --test-connection`

### Want to re-run conversion
Just delete the `/equipment/` directory and run again:
```bash
rm -rf ../../equipment
python srd-equipment-converter.py
```

---

## Next Steps

After conversion and sync:
1. Check Kanka Items section for all equipment
2. Test filtering by tags
3. Link weapons to PC character sheets
4. Add custom items as campaign progresses

---

**Questions?** Let me know if you need any adjustments!
