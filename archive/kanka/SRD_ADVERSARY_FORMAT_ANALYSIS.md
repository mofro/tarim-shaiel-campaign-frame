---
title: SRD Adversary Format Analysis - Kanka Sync Compatibility
date: 2026-01-28
tags: [daggerheart, srd, kanka-sync, compatibility]
---

# SRD Adversary Format vs Kanka Sync Requirements

## TL;DR: **NO - Requires Conversion**

The SRD adversaries are **NOT directly compatible** with the Phase 2 Kanka sync. They use a **prose markdown format** instead of **YAML code blocks**.

---

## Format Comparison

### SRD Format (Bear.md)
```markdown
# Bear

**_Tier 1 Bruiser._** _A large bear with thick fur and powerful claws._

- **Motives & Tactics:** Climb, defend territory, pummel, track
- **Difficulty:** 14 | **Thresholds:** 9/17 | **HP:** 7 | **Stress:** 2
- **ATK:** +1 | **Claws:** Melee | 1d8+3 phy
- **Experience:** Ambusher +3, Keen Senses +2

### FEATURES

**_Overwhelming Force - Passive:_** Description...
```

### Required Format (test-bear.md)
```markdown
# Bear

```daggerheart
name: Bear
tier: 1
type: Bruiser
desc: A large bear with thick fur and powerful claws
difficulty: 14
thresholds: 9/17
hp: 7
stress: 2
attack: +1
weapon: Claws
range: Melee
damage: 1d8+3 phy
motives: Climb, defend territory, pummel, track
xp: Ambusher +3, Keen Senses +2

features:
- name: Overwhelming Force
  type: Passive
  desc: Targets who mark HP are knocked back to Very Close range
```
\```

---

## Key Differences

| Aspect | SRD Format | Kanka Sync Format |
|--------|-----------|-------------------|
| **Structure** | Prose markdown with bold/italic | YAML code block |
| **Stat Block** | Inline bullets with pipes | Structured key-value pairs |
| **Features** | Markdown headers + bold | YAML array of dicts |
| **Parsing** | Requires regex/text parsing | Native YAML parsing |
| **Metadata** | Mixed in prose | Structured frontmatter |

---

## What Would Need to Change

### 1. Add Frontmatter
SRD files have **no frontmatter**. Need to add:
```yaml
---
kanka_type: creature
is_private: false
name: Bear
type: bruiser
---
```

### 2. Convert Stat Block
From: `**Difficulty:** 14 | **Thresholds:** 9/17`
To: 
```yaml
difficulty: 14
thresholds: 9/17
```

### 3. Convert Features
From: `**_Overwhelming Force - Passive:_** Description...`
To:
```yaml
features:
- name: Overwhelming Force
  type: Passive
  desc: Description...
```

### 4. Wrap in Code Block
Entire stat block needs to be wrapped in:
```
```daggerheart
...
```
\```

---

## Options for Using SRD Adversaries

### Option A: Manual Conversion (Recommended for Now)
**Best for:** Cherry-picking specific adversaries

1. Copy SRD adversary file
2. Add frontmatter manually
3. Convert stat block to YAML format
4. Wrap in ```daggerheart block
5. Sync to Kanka

**Pros:**
- Full control over what gets synced
- Can customize/adapt for Hero Heaven
- Clean, intentional additions

**Cons:**
- Manual work for each adversary
- Time-consuming for bulk imports

### Option B: Create Conversion Script
**Best for:** Bulk importing many adversaries

Create `srd-to-kanka-converter.py` that:
1. Reads SRD adversary markdown
2. Parses prose format with regex
3. Generates YAML daggerheart block
4. Adds frontmatter
5. Writes to `bestiary/` directory

**Pros:**
- Automated bulk conversion
- Consistent formatting
- Fast for large imports

**Cons:**
- Requires writing/testing conversion script
- May need manual cleanup for edge cases
- SRD format variations might break parser

### Option C: Update Kanka Sync to Parse Both Formats
**Best for:** Long-term flexibility

Enhance `extract_daggerheart_blocks()` to:
1. Check for YAML blocks first
2. If none found, parse prose format
3. Convert to internal dict structure
4. Process normally

**Pros:**
- Works with both formats
- No file conversion needed
- Most flexible

**Cons:**
- Complex parsing logic
- Harder to maintain
- Prose format has variations

---

## Recommendation

### Immediate: **Option A - Manual Conversion**
For now, manually convert adversaries you actually want to use:
1. Only convert what you need for your campaign
2. Customize them for Hero Heaven setting
3. Ensures quality over quantity

### Future: **Option B - Conversion Script**
If you want to bulk import SRD adversaries:
- Write a parser script
- Test on 5-10 adversaries
- Run bulk conversion
- Manual cleanup for edge cases

I can help build Option B if you want to import a lot of SRD adversaries!

---

## Example Conversion

### SRD Source
```markdown
# Bear

**_Tier 1 Bruiser._** _A large bear with thick fur and powerful claws._

- **Motives & Tactics:** Climb, defend territory, pummel, track
- **Difficulty:** 14 | **Thresholds:** 9/17 | **HP:** 7 | **Stress:** 2
- **ATK:** +1 | **Claws:** Melee | 1d8+3 phy
- **Experience:** Ambusher +3, Keen Senses +2
```

### Converted to Kanka-Ready
```markdown
---
kanka_type: creature
is_private: false
name: Bear
type: bruiser
tags: [tier-1, bruiser, srd-adversary]
---

# Bear

```daggerheart
name: Bear
tier: 1
type: Bruiser
desc: A large bear with thick fur and powerful claws
difficulty: 14
thresholds: 9/17
hp: 7
stress: 2
attack: +1
weapon: Claws
range: Melee
damage: 1d8+3 phy
motives: Climb, defend territory, pummel, track
xp: Ambusher +3, Keen Senses +2

features:
- name: Overwhelming Force
  type: Passive
  desc: Targets who mark HP from the Bear's standard attack are knocked back to Very Close range
- name: Bite
  type: Action
  desc: Mark a Stress to make an attack against a target within Melee range. On a success, deal 3d4+10 physical damage and the target is Restrained until they break free with a successful Strength Roll
- name: Momentum
  type: Reaction
  desc: When the Bear makes a successful attack against a PC, you gain a Fear
```
\```

## Narrative Notes

A massive brown bear protecting its territory in the mountain passes.
```

---

## Next Steps

**Do you want to:**
1. Manually convert a few key adversaries? (I can help!)
2. Build a bulk conversion script? (Will take ~30-45 min)
3. Leave SRD as reference-only and create custom adversaries?

Let me know what approach works best for your workflow!
