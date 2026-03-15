---
title: Equipment Converter - Cowork Handoff
date: 2026-01-29
type: cowork-handoff
tags: [cowork, equipment, converter, daggerheart]
---

## COWORK TASK BRIEF

**Goal:** Build Python converter to transform SRD Tier 1 equipment to Kanka-ready format
**Input Files:** 
- `/Users/mo/Documents/Games/HeroHeaven/references/daggerheart-srd/weapons/*.md` (~32 Tier 1 weapons)
- `/Users/mo/Documents/Games/HeroHeaven/references/daggerheart-srd/armor/*.md` (4 Tier 1 armor)
**Output Files:** 
- `/Users/mo/Documents/Games/HeroHeaven/utilities/scripts/srd-equipment-converter.py`
- `/Users/mo/Documents/Games/HeroHeaven/equipment/weapons/*.md` (created when script runs)
- `/Users/mo/Documents/Games/HeroHeaven/equipment/armor/*.md` (created when script runs)
**Dependencies:** 
- `/Users/mo/Documents/Games/HeroHeaven/utilities/SRD_REFERENCE_MATERIAL_ANALYSIS.md`
- `/Users/mo/Documents/Games/HeroHeaven/utilities/EQUIPMENT_CONVERTER_GUIDE.md`
**Estimated Complexity:** Medium (2-3 hours manual, 20-30 min Cowork)

---

## Context

### Background
- Phase 2 Daggerheart integration complete (stat block parsing works)
- Decided to import Tier 1 basic equipment but NOT bulk import adversaries
- Equipment has simple, consistent format suitable for automated conversion
- See `DECISION_CUSTOM_CONTENT_OVER_SRD_IMPORT.md` for rationale

### Why This Task
- ~36 equipment files (32 weapons + 4 armor) worth importing
- Simple format makes conversion tractable
- Players need quick reference to Tier 1 equipment during sessions
- Kanka attributes enable filtering/searching by stats

### Key Decisions
- Only Tier 1 basic equipment (excludes Advanced/Improved/Legendary)
- Weapons: Battleaxe, Longsword, Shortbow, etc. (standard starter weapons)
- Armor: Leather, Gambeson, Chainmail, Full Plate (4 basic types)
- Format uses frontmatter attributes for queryability in Kanka

---

## Requirements

### Must Have
- [ ] Parse Tier 1 weapons excluding Advanced/Improved/Legendary variants
- [ ] Parse Tier 1 armor (4 basic types only)
- [ ] Generate proper YAML frontmatter with kanka_type: item
- [ ] Extract all stat fields (trait, range, damage, burden for weapons)
- [ ] Extract all stat fields (thresholds, score for armor)
- [ ] Create attributes in frontmatter (weapon_trait, weapon_damage, etc.)
- [ ] Add tags: [tier-1, weapon/armor, daggerheart-srd]
- [ ] Output to `/equipment/weapons/` and `/equipment/armor/` directories
- [ ] Progress logging showing which files converted
- [ ] Summary stats at end (X weapons, Y armor converted)

### Should Have
- [ ] Handle missing files gracefully (log warning, continue)
- [ ] Validate parsed data before writing output
- [ ] Add source comment: "Standard equipment from Daggerheart SRD"
- [ ] Print helpful next-steps message after completion

### Must NOT Do
- [ ] Import Advanced/Improved/Legendary equipment variants
- [ ] Modify original SRD source files
- [ ] Sync to Kanka (that's a separate manual step)
- [ ] Create files outside `/equipment/` directory
- [ ] Overwrite existing custom equipment files

---

## Implementation Guide

### Approach
Regex parsing of consistent SRD markdown format → YAML frontmatter generation → Kanka-ready markdown output

### File Lists to Convert

**Tier 1 Weapons (~32 files):**
```python
TIER_1_WEAPONS = [
    "Battleaxe.md", "Broadsword.md", "Crossbow.md", "Cutlass.md", "Dagger.md",
    "Dualstaff.md", "Greatstaff.md", "Greatsword.md", "Halberd.md",
    "Hand Crossbow.md", "Longbow.md", "Longsword.md", "Mace.md",
    "Quarterstaff.md", "Rapier.md", "Round Shield.md", "Scepter.md",
    "Shortbow.md", "Shortstaff.md", "Shortsword.md", "Small Dagger.md",
    "Spear.md", "Tower Shield.md", "Wand.md", "Warhammer.md", "Whip.md",
    "Arcane Gauntlets.md", "Glowing Rings.md", "Grappler.md",
    "Hallowed Axe.md", "Hand Runes.md", "Returning Blade.md"
]
```

**Tier 1 Armor (4 files):**
```python
TIER_1_ARMOR = [
    "Leather Armor.md",
    "Gambeson Armor.md",
    "Chainmail Armor.md",
    "Full Plate Armor.md"
]
```

### SRD Format Examples

**Weapon Format:**
```markdown
# Longsword

**_Tier 1_** _Primary_ _Physical_ _Weapon_

- **Trait:** Agility
- **Range:** Melee
- **Damage:** d10+3 phy
- **Burden:** Two-Handed
```

**Armor Format:**
```markdown
# Leather Armor

**_Tier 1_** _Armor_

- **Base Thresholds:** 6 / 13
- **Base Score:** 3
```

### Output Format

**Weapon Output:**
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

**Armor Output:**
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

### Code Structure

**Functions needed:**
1. `parse_weapon(filepath)` → Dict with extracted data
2. `parse_armor(filepath)` → Dict with extracted data
3. `generate_weapon_markdown(data)` → str (full markdown)
4. `generate_armor_markdown(data)` → str (full markdown)
5. `convert_weapons()` → int (count converted)
6. `convert_armor()` → int (count converted)
7. `main()` → orchestration

**Parsing Logic:**
- Extract name from `# Name` line
- Extract tier from `**_Tier X_**` using regex
- Extract type (Primary/Secondary, Physical/Magical) from second line
- Parse bullet points for stats using `**Field:**` pattern
- Handle missing/optional fields gracefully

**Error Handling:**
- Try/except around file reads
- Log warnings for parsing failures
- Continue processing on errors (don't crash)
- Report summary at end

---

## File Locations

### Input Paths
```
/Users/mo/Documents/Games/HeroHeaven/references/daggerheart-srd/weapons/
/Users/mo/Documents/Games/HeroHeaven/references/daggerheart-srd/armor/
```

### Output Paths
```
/Users/mo/Documents/Games/HeroHeaven/utilities/scripts/srd-equipment-converter.py
/Users/mo/Documents/Games/HeroHeaven/equipment/weapons/ (created by script)
/Users/mo/Documents/Games/HeroHeaven/equipment/armor/ (created by script)
```

### Reference Docs
```
/Users/mo/Documents/Games/HeroHeaven/utilities/SRD_REFERENCE_MATERIAL_ANALYSIS.md
/Users/mo/Documents/Games/HeroHeaven/utilities/EQUIPMENT_CONVERTER_GUIDE.md
```

---

## Testing

### Test Cases
1. **Longsword.md** - Standard two-handed weapon
2. **Dagger.md** - One-handed weapon with Finesse trait
3. **Shortbow.md** - Ranged weapon with Far range
4. **Leather Armor.md** - Light armor
5. **Full Plate Armor.md** - Heavy armor

### Validation
After running converter, verify:
- [ ] Script executes without errors
- [ ] All expected files created in `/equipment/` subdirectories
- [ ] Frontmatter valid YAML (no syntax errors)
- [ ] All stat fields present in output
- [ ] Tags properly formatted as arrays
- [ ] Markdown body renders correctly
- [ ] Summary shows correct counts

---

## Validation Checklist

After completion, verify:
- [ ] Script created at `/utilities/scripts/srd-equipment-converter.py`
- [ ] Script is executable (`chmod +x`)
- [ ] Can run: `python srd-equipment-converter.py`
- [ ] Creates `/equipment/weapons/` directory
- [ ] Creates `/equipment/armor/` directory
- [ ] 32 weapon files created
- [ ] 4 armor files created
- [ ] No errors in console output
- [ ] Summary stats printed
- [ ] Files sync-ready for kanka-sync.py

---

## Next Steps After Conversion

1. **Test Run:**
```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities/scripts
python srd-equipment-converter.py
```

2. **Review Output:**
```bash
ls -la ../../equipment/weapons/ | wc -l  # Should show 32
ls -la ../../equipment/armor/ | wc -l    # Should show 4
```

3. **Sync to Kanka:**
```bash
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate
cd utilities/scripts
python kanka-sync.py --dry-run  # Preview
python kanka-sync.py --sync     # Execute
```

---

## Known Constraints

- SRD files are read-only (don't modify originals)
- Some weapons may have missing fields (handle gracefully)
- Output must be compatible with kanka-sync.py Phase 2
- User has venv at project root for Python dependencies

---

## Success Criteria

✅ Script successfully parses all Tier 1 weapons and armor
✅ All output files have valid frontmatter
✅ All stat fields extracted correctly
✅ Files ready to sync to Kanka without modification
✅ Clear progress logging during execution
✅ Helpful summary at completion
