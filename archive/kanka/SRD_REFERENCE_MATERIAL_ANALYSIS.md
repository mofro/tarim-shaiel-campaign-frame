---
title: SRD Reference Material - Import Analysis
date: 2026-01-28
type: analysis
tags: [srd, reference, kanka, equipment, rules]
---

# SRD Reference Material Import Analysis

## TL;DR: **Different Needs Than Adversaries**

The "mundane" SRD content (weapons, armor, domains, classes, etc.) serves a **different purpose** than adversaries and has **different import needs**.

---

## Category Breakdown

### 1. **Rules/Reference Material** (Keep in Obsidian Only)

**Categories:**
- Classes (12 files) - Ranger, Guardian, Bard, etc.
- Subclasses (36 files) - Beastbound, Warden of Midnight, etc.
- Ancestries (9 files) - Drakona, Dwarf, Elf, etc.
- Communities (9 files) - Rural, Urban, etc.
- Domains (11 files) - Arcana, Blade, Bone, Codex, etc.
- Beastforms (for Ranger Beastbound)

**Format:** Rich markdown with tables, links, lore
**Use Case:** Player reference during character creation

**Recommendation: STAY IN OBSIDIAN**
- ✅ Players can reference during character creation
- ✅ Already formatted and linked properly
- ✅ No need in Kanka (not campaign-specific)
- ❌ Kanka would just duplicate reference material

---

### 2. **Equipment** (Consider Selective Import)

#### Weapons (~220 files)

**Format:**
```markdown
# Longsword
**_Tier 1_** _Primary_ _Physical_ _Weapon_
- **Trait:** Agility
- **Range:** Melee
- **Damage:** d10+3 phy
- **Burden:** Two-Handed
```

**Simple, structured data!**

**Options:**

**A) Import Basic Weapons to Kanka** ⭐ RECOMMENDED
- Import Tier 1 basic weapons (~30 files)
- Players can reference in Kanka during play
- GM can quickly look up weapon stats

**B) Keep ALL in Obsidian Only**
- Reference-only, no import
- Players use Obsidian or SRD site

**C) Selective Import**
- Only import weapons actually used by PCs/NPCs
- Add as needed to Kanka

#### Armor (~35 files)

**Format:**
```markdown
# Leather Armor
**_Tier 1_** _Armor_
- **Base Thresholds:** 6 / 13
- **Base Score:** 3
```

**Even simpler!**

**Recommendation: Import Basic Armor Sets**
- Tier 1 basics (Leather, Chainmail, Full Plate, Gambeson) = 4 files
- Quick reference in Kanka
- Easy to convert

#### Items/Consumables

**Similar simple format**

**Recommendation: Import As Needed**
- Add to Kanka when PCs acquire them
- No need to pre-populate

---

### 3. **Environments** (Complex - Needs Customization)

**SRD has:** Generic fantasy environments
**You need:** Silk Road-specific environments tied to Hero Heaven locations

**Format:** Similar to adversaries (prose, complex)

**Recommendation: CUSTOM CREATION**
- Use SRD as reference/inspiration
- Create Hero Heaven-specific environments
- Tie to actual locations in your world
- Same reasoning as adversaries decision

---

## Import Difficulty Assessment

| Category | Files | Format Complexity | Import Worth It? | Recommendation |
|----------|-------|-------------------|------------------|----------------|
| **Classes** | 12 | Complex, rich | ❌ | Keep in Obsidian |
| **Subclasses** | 36 | Complex, rich | ❌ | Keep in Obsidian |
| **Ancestries** | 9 | Complex, rich | ❌ | Keep in Obsidian |
| **Communities** | 9 | Complex, rich | ❌ | Keep in Obsidian |
| **Domains** | 11 | Tables, links | ❌ | Keep in Obsidian |
| **Beastforms** | ? | Complex | ❌ | Keep in Obsidian |
| **Tier 1 Weapons** | ~30 | **SIMPLE** | ✅ | **Import to Kanka** |
| **Tier 1 Armor** | ~4 | **SIMPLE** | ✅ | **Import to Kanka** |
| **Advanced Weapons** | ~190 | Simple | ⚠️ | Optional |
| **Advanced Armor** | ~30 | Simple | ⚠️ | Optional |
| **Items/Consumables** | ? | Simple | ⚠️ | Add as acquired |
| **Adversaries** | 130 | Complex | ❌ | Custom only |
| **Environments** | ? | Complex | ❌ | Custom only |

---

## Proposed Approach

### Phase 1: Basic Equipment Import ⭐

**Import to Kanka:**
1. **Tier 1 Basic Weapons** (~30 files)
   - Longsword, Shortsword, Dagger, Battleaxe, etc.
   - The "standard" weapons PCs start with

2. **Tier 1 Basic Armor** (~4 files)
   - Leather, Chainmail, Full Plate, Gambeson
   - The core armor types

**Why:** 
- Simple format (easy conversion)
- Actually useful in-game
- Small set (~34 files total)
- Quick reference during sessions

**Effort:** Low - could write converter in ~20 min

### Phase 2: On-Demand Equipment

**As campaign progresses:**
- Add advanced/legendary weapons when PCs acquire them
- Add consumables/items as needed
- Add faction-specific equipment

### Phase 3: Reference Material

**Keep in Obsidian:**
- All classes, subclasses, ancestries, communities, domains
- Players reference during character creation
- No Kanka import needed

---

## Equipment Import Format

### Current SRD Format
```markdown
# Longsword
**_Tier 1_** _Primary_ _Physical_ _Weapon_
- **Trait:** Agility
- **Range:** Melee
- **Damage:** d10+3 phy
- **Burden:** Two-Handed
```

### Kanka Format Option 1: Item Entity
```yaml
---
kanka_type: item
is_private: false
name: Longsword
type: weapon
tags: [tier-1, weapon, melee, two-handed]
---

# Longsword

**Tier 1 Primary Physical Weapon**

- **Trait:** Agility
- **Range:** Melee
- **Damage:** d10+3 phy
- **Burden:** Two-Handed
```

### Kanka Format Option 2: Attributes Only
```yaml
---
kanka_type: item
is_private: false
name: Longsword
weapon_tier: 1
weapon_type: Primary Physical Weapon
weapon_trait: Agility
weapon_range: Melee
weapon_damage: d10+3 phy
weapon_burden: Two-Handed
---

# Longsword

Standard two-handed blade used by warriors across the realms.
```

**Recommendation:** Option 2 (attributes) for queryability

---

## Converter Feasibility

### Easy to Convert (20-30 min work)
- ✅ Tier 1 weapons (simple format, few variations)
- ✅ Tier 1 armor (even simpler)

### Medium Difficulty (45-60 min)
- ⚠️ All weapons (many variations, special properties)
- ⚠️ All armor (legendary versions have features)

### Hard (not worth it)
- ❌ Classes/subclasses (rich content, tables, better as reference)
- ❌ Domains (tables with links, better as reference)

---

## Decision Points

### Question 1: Import Basic Equipment?

**YES - Import Tier 1 basics (~34 files)**
- Useful in-session reference
- Simple format (easy conversion)
- Small focused set

**NO - Keep all equipment in Obsidian**
- Reference-only approach
- Players use SRD or Obsidian

### Question 2: How Much Equipment?

**Option A: Tier 1 Only** ⭐ RECOMMENDED
- ~30 weapons, 4 armor
- Covers 90% of early game
- Clean, focused

**Option B: All Equipment**
- 220 weapons, 35 armor
- Comprehensive but overwhelming
- Likely won't use most

**Option C: None**
- Pure reference approach
- Add items individually as acquired

---

## Recommendation

### DO Import:
1. **Tier 1 Basic Weapons** (~30 files) - converter script
2. **Tier 1 Basic Armor** (~4 files) - manual or script

### KEEP in Obsidian Only:
- Classes, Subclasses, Ancestries, Communities, Domains, Beastforms
- All reference/rules material

### CREATE Custom:
- Adversaries (as previously decided)
- Environments (Hero Heaven-specific)

### ADD On-Demand:
- Advanced weapons as PCs acquire
- Legendary items as discovered
- Consumables as needed

---

## Next Steps

**If you want basic equipment in Kanka:**

I can build a simple converter for Tier 1 weapons + armor (~34 files total):
- Reads SRD weapon/armor files
- Generates Kanka-ready item files with attributes
- Outputs to `/equipment/` directory
- Ready to sync

**Time:** ~20-30 minutes to build, 2 minutes to run

**Alternative:** Manually add equipment as PCs acquire it during play

---

## What do you want to do?

1. **Import Tier 1 basics** (I build converter)?
2. **Keep all equipment as reference** (Obsidian-only)?
3. **Something else?**

Let me know! 🎲
