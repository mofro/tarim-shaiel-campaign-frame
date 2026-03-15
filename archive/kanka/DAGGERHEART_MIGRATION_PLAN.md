---
title: Daggerheart Campaign Management Migration Plan
type: planning
status: draft
created: 2025-01-28
tags: [daggerheart, beastvault, kanka, migration]
---

# Daggerheart Campaign Management Migration Plan

**Goal:** Integrate Daggerheart SRD, BeastVault plugin, and update templates while maintaining Kanka sync compatibility.

---

## Overview

| Phase | Focus | Risk Level |
|-------|-------|------------|
| **Phase 1** | SRD clone + plugin swap + template fixes | Low |
| **Phase 2** | Kanka sync enhancement for `daggerheart` blocks | Medium |
| **Phase 3** | Character template implementation | Low |

---

# Phase 1: Foundation

## 1.1 Clone Daggerheart SRD

**Location:** `references/daggerheart-srd/`

```bash
cd /path/to/HeroHeaven
git clone https://github.com/seansbox/daggerheart-srd.git references/daggerheart-srd
```

**What you get:**
- `abilities/` - Class abilities
- `adversaries/` - 130+ adversary stat blocks
- `ancestries/` - Character ancestry options
- `armor/` - Armor items by tier
- `beastforms/` - Druid beastform options
- `classes/` - 9 core classes (Bard, Druid, Guardian, etc.)
- `communities/` - Community backgrounds
- `consumables/` - Potions, scrolls, etc.
- `domains/` - 9 domains + domain cards
- `environments/` - Environment stat blocks
- `items/` - General items
- `subclasses/` - Subclass options per class
- `weapons/` - Weapons by tier

**Post-clone:** Add to `.gitignore` if you don't want to track it:
```
references/daggerheart-srd/
```

---

## 1.2 Plugin Swap: obsidian-5e-statblocks → BeastVault

### Remove obsidian-5e-statblocks

1. Obsidian → Settings → Community Plugins
2. Disable "Fantasy Statblocks" (obsidian-5e-statblocks)
3. Uninstall

### Install BeastVault

1. Community Plugins → Browse → Search "BeastVault"
2. Install + Enable
3. Configure:
   - **Library folder:** `bestiary/` (your existing folder)
   - **Enable Fantasy Statblocks compatibility:** OFF (clean start)

### Optional: Daggerheart Tracker

If you want encounter tracking with action economy:
1. Install "Daggerheart Tracker" plugin
2. It reads from BeastVault's library

---

## 1.3 Configure BeastVault Library

BeastVault scans a designated folder for `daggerheart` code blocks.

**Option A:** Use your existing `bestiary/` folder
- Put your custom adversaries here
- BeastVault finds them automatically

**Option B:** Point BeastVault at SRD adversaries
- Set library to `references/daggerheart-srd/adversaries/`
- Gives you all 130+ SRD adversaries in search
- But: SRD uses markdown format, not BeastVault YAML format

**Recommended:** Use `bestiary/` for your custom content in BeastVault format. Reference SRD as read-only markdown.

---

## 1.4 Fix Template Frontmatter Structure

Your current templates have content INSIDE the frontmatter block. This breaks YAML parsing.

### Current (broken):
```yaml
---
# Charm Template for Hero Heaven

## Metadata
title:
archetype: [Warrior, Breaker, Bridge, Seeker, Sacrificer, Visionary]
---
```

### Corrected:
```yaml
---
title: ""
archetype: ""
daggerheart_domain: ""
tier: 1
---

# Charm Template for Hero Heaven

## Metadata
...
```

**Files to fix:**
- `templates/mechanics/charm_template.md`
- `templates/character-creation/character_template.md`
- `templates/world-building/adversary_template.md`
- `templates/world-building/environment_template.md`

---

## 1.5 New Adversary Template (BeastVault-Compatible)

**Location:** `templates/world-building/adversary_template.md`

~~~markdown
---
name: ""
kanka_type: creature
type: ""
is_private: false
kanka_id: null
tags: [adversary]
---

# {{name}}

## Stat Block

```daggerheart
name: {{name}}
tier: 1
type: Bruiser
difficulty: 10
thresholds: 7/14
hp: 5
stress: 2
attack: +0
weapon: Claws
range: Melee
damage: 1d6+2 phy
motives: Defend territory, hunt prey
xp: Keen Senses +2
features:
  - name: Feature Name
    type: Passive
    desc: Description of what this feature does.
```

## Narrative Notes

[Physical description, behavior, habitat, story hooks]

## GM Notes

[Tactical considerations, encounter design notes]
~~~

**Why this structure:**
- Frontmatter: Kanka sync reads `kanka_type: creature` and basic metadata
- Code block: BeastVault renders and tracks HP/stress
- Sections: Kanka routes to entry (public) or posts (GM-only)

---

## 1.6 New Environment Template (BeastVault-Compatible)

**Location:** `templates/world-building/environment_template.md`

~~~markdown
---
name: ""
kanka_type: location
type: environment
is_private: false
kanka_id: null
tags: [environment, encounter]
---

# {{name}}

## Stat Block

```daggerheart
name: {{name}}
tier: 1
difficulty: 8
impulses:
  - On a 1-5: Environmental hazard triggers
  - On a 6-10: Reinforcements arrive
  - On an 11+: The environment shifts dramatically
tone: Oppressive, claustrophobic
adversaries:
  - 2x Minion
  - 1x Standard
```

## Description

[Sensory details, atmosphere, tactical features]

## Hidden Secrets

[What players might discover with investigation]
~~~

---

## 1.7 Linking Conventions

Your Tarim-Shaiel archetypes work ALONGSIDE Daggerheart classes. Establish clear linking:

### In Character Files:
```yaml
---
name: "Kira Sandwalker"
daggerheart_class: "[[references/daggerheart-srd/classes/Ranger|Ranger]]"
hero_heaven_archetype: "[[mechanics/archetypes/Seeker|Seeker]]"
subclass: "[[references/daggerheart-srd/subclasses/Ranger - Beastbound|Beastbound]]"
---
```

### In Archetype Files:
```markdown
# Seeker Archetype

The Seeker pursues hidden knowledge...

## Compatible Classes

Seekers often emerge from these Daggerheart classes:
- [[references/daggerheart-srd/classes/Wizard|Wizard]] - Arcane researchers
- [[references/daggerheart-srd/classes/Ranger|Ranger]] - Wilderness explorers
- [[references/daggerheart-srd/classes/Bard|Bard]] - Lore collectors
```

---

# Phase 2: Kanka Sync Enhancement

## 2.1 Remove `daggerheart` from Stripped Blocks

**File:** `utilities/kanka-sync/kanka-sync.py` (or wherever your script lives)

**Find:**
```python
STRIPPED_BLOCKS = ['leaflet', 'dataview', 'daggerheart']
```

**Change to:**
```python
STRIPPED_BLOCKS = ['leaflet', 'dataview']
# Note: daggerheart blocks now pass through for parsing
```

**Immediate result:** `daggerheart` code blocks appear as `<pre><code>` in Kanka entity entries. Readable but not parsed into attributes.

---

## 2.2 Parse `daggerheart` Blocks to Attributes (Optional Enhancement)

If you want adversary stats as queryable Kanka attributes, add parsing logic.

### Conceptual Implementation:

```python
import yaml
import re

def extract_daggerheart_blocks(content):
    """Find and parse daggerheart code blocks."""
    pattern = r'```daggerheart\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)

    blocks = []
    for match in matches:
        try:
            data = yaml.safe_load(match)
            blocks.append(data)
        except yaml.YAMLError:
            continue
    return blocks

def daggerheart_to_attributes(block):
    """Convert daggerheart block to Kanka attributes."""
    mappings = {
        'tier': ('Tier', 'number', False),
        'type': ('Adversary Type', 'text', False),
        'difficulty': ('Difficulty', 'number', False),
        'thresholds': ('Thresholds', 'text', False),
        'hp': ('HP', 'number', False),
        'stress': ('Stress', 'number', False),
        'attack': ('Attack Bonus', 'text', False),
        'weapon': ('Weapon', 'text', False),
        'range': ('Range', 'text', False),
        'damage': ('Damage', 'text', False),
        'motives': ('Motives', 'text', False),
        'xp': ('Experiences', 'text', False),
    }

    attributes = []
    for field, (kanka_name, attr_type, is_private) in mappings.items():
        if field in block:
            value = block[field]
            # Handle arrays
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            attributes.append({
                'name': kanka_name,
                'value': str(value),
                'type': attr_type,
                'is_private': is_private
            })

    return attributes

def render_statblock_html(block):
    """Render a nice HTML stat block for entity entry."""
    html = f'''
    <div class="daggerheart-statblock">
      <h3>{block.get('name', 'Unknown')}</h3>
      <p><strong>Tier {block.get('tier', '?')} {block.get('type', 'Adversary')}</strong></p>
      <p>
        <strong>Difficulty:</strong> {block.get('difficulty', '?')} |
        <strong>Thresholds:</strong> {block.get('thresholds', '?')} |
        <strong>HP:</strong> {block.get('hp', '?')} |
        <strong>Stress:</strong> {block.get('stress', '?')}
      </p>
      <p>
        <strong>Attack:</strong> {block.get('attack', '+0')} |
        <strong>{block.get('weapon', 'Attack')}:</strong> {block.get('range', 'Melee')} |
        {block.get('damage', '1d6 phy')}
      </p>
      <p><strong>Motives:</strong> {block.get('motives', 'Unknown')}</p>
    </div>
    '''
    return html
```

### Integration Points:

1. **In entity processing:** Call `extract_daggerheart_blocks(content)` before stripping
2. **For attributes:** Call `daggerheart_to_attributes(block)` and add to entity attributes
3. **For entry HTML:** Call `render_statblock_html(block)` and include in entity entry
4. **Strip from Kanka output:** After parsing, remove the raw YAML block from the content *being sent to Kanka* (your Obsidian source file is never modified)

### Features Handling:

Features are complex (array of objects). Options:
- **Simple:** Render as HTML in entry, don't create attributes
- **Advanced:** Create as Kanka Abilities (separate entity type, linked to creature)

```python
def render_features_html(features):
    """Render features as HTML list."""
    if not features:
        return ''

    html = '<h4>Features</h4><ul>'
    for f in features:
        html += f'''
        <li>
          <strong>{f.get('name', 'Feature')}</strong>
          ({f.get('type', 'Passive')}):
          {f.get('desc', '')}
        </li>
        '''
    html += '</ul>'
    return html
```

---

## 2.3 Kanka Entity Type Mapping

Add to your `kanka_type` routing:

| Obsidian Content | `kanka_type` | Kanka Entity |
|------------------|--------------|--------------|
| Player character | `character` | Character |
| Named NPC | `character` | Character |
| Adversary/Monster | `creature` | Creature |
| Race/Ancestry | `race` | Race |
| Environment | `location` | Location (with type: "environment") |

---

# Phase 3: Character Templates

## 3.1 Character Template (PC/NPC)

**Location:** `templates/character-creation/character_template.md`

```yaml
---
# Kanka Sync
name: ""
kanka_type: character
type: ""
is_private: false
kanka_id: null

# Daggerheart Standard
daggerheart_class: ""
subclass: ""
ancestry: ""
community: ""
level: 1
evasion: 10
armor_score: 0
major_thresholds: "7/14"
minor_thresholds: "3/6"
hope: 2
max_hope: 5

# Traits
agility: 0
strength: 0
finesse: 0
instinct: 0
presence: 0
knowledge: 0

# Tarim-Shaiel Extensions
hero_heaven_archetype: ""
charm_tier: 1
active_charms: []
r_h_k_balance:
  resist: 0
  hunger: 0
  know: 0

# Campaign
player: ""
status: active
---

# {{name}}

## Character Concept

[Brief character description]

## Daggerheart Class

**Class:** {{daggerheart_class}}
**Subclass:** {{subclass}}
**Ancestry:** {{ancestry}}
**Community:** {{community}}

## Tarim-Shaiel Archetype

**Archetype:** {{hero_heaven_archetype}}

### Active Charms

[List of unlocked charms]

### R/H/K Progression

| Resist | Hunger | Know |
|--------|--------|------|
| {{r_h_k_balance.resist}} | {{r_h_k_balance.hunger}} | {{r_h_k_balance.know}} |

## Inventory

[Equipment, gold, items]

## Notes

[Background, relationships, goals]
```

## 3.2 Kanka Character Attribute Mappings

Add to `ATTRIBUTE_MAPPINGS` in your sync script:

```python
# Character attributes
'daggerheart_class': ('Daggerheart Class', 'text', False),
'subclass': ('Subclass', 'text', False),
'ancestry': ('Ancestry', 'text', False),
'community': ('Community', 'text', False),
'level': ('Level', 'number', False),
'evasion': ('Evasion', 'number', False),
'armor_score': ('Armor Score', 'number', False),
'hope': ('Hope', 'number', False),
'max_hope': ('Max Hope', 'number', False),

# Traits
'agility': ('Agility', 'number', False),
'strength': ('Strength', 'number', False),
'finesse': ('Finesse', 'number', False),
'instinct': ('Instinct', 'number', False),
'presence': ('Presence', 'number', False),
'knowledge': ('Knowledge', 'number', False),

# Hero Heaven
'hero_heaven_archetype': ('Tarim-Shaiel Archetype', 'text', False),
'charm_tier': ('Charm Tier', 'number', False),
```

---

# Implementation Checklist

## Phase 1 Tasks

- [ ] Clone SRD to `references/daggerheart-srd/`
- [ ] Uninstall obsidian-5e-statblocks
- [ ] Install BeastVault
- [ ] Configure BeastVault library folder → `bestiary/`
- [ ] (Optional) Install Daggerheart Tracker
- [ ] Fix frontmatter structure in existing templates
- [ ] Create new adversary template (BeastVault-compatible)
- [ ] Create new environment template (BeastVault-compatible)
- [ ] Test: Create sample adversary, verify BeastVault renders it
- [ ] Test: Verify SRD files are accessible via Obsidian search

## Phase 2 Tasks

- [ ] Remove `'daggerheart'` from `STRIPPED_BLOCKS`
- [ ] Test: Sync adversary, verify code block appears in Kanka
- [ ] (Optional) Implement `extract_daggerheart_blocks()` parser
- [ ] (Optional) Implement `daggerheart_to_attributes()` mapper
- [ ] (Optional) Implement `render_statblock_html()` formatter
- [ ] Test: Sync adversary, verify attributes appear in Kanka

## Phase 3 Tasks

- [ ] Create character template with dual class/archetype structure
- [ ] Add character attribute mappings to sync script
- [ ] Test: Sync character, verify attributes in Kanka
- [ ] Document R/H/K progression display in Kanka

---

# Rollback Plan

If something breaks:

1. **BeastVault issues:** Reinstall obsidian-5e-statblocks, it's still in plugin cache
2. **SRD conflicts:** Delete `references/daggerheart-srd/` folder
3. **Kanka sync breaks:** Revert `STRIPPED_BLOCKS` change, restore from git
4. **Template issues:** Templates are still drafts, revert file changes

---

# References

- [seansbox/daggerheart-srd](https://github.com/seansbox/daggerheart-srd)
- [BeastVault Plugin](https://github.com/ly0va/beastvault)
- [Daggerheart Tracker](https://github.com/Batres3/daggerheart-tracker)
- [Kanka Creatures Documentation](https://docs.kanka.io/en/latest/entities/creatures.html)
- [Kanka Attributes Documentation](https://docs.kanka.io/en/latest/features/attributes.html)

---

[[utilities/kanka-sync/INDEX|← Kanka Sync Docs]] | [[INDEX|← Vault Index]]
