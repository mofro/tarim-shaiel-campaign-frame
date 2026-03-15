---
title: Narrative Directory Index
project: TTRPG_Tarim_Shaiel
type: directory_index
purpose: Dynamic navigation for narrative and story resources
created: 2025-01-21
updated: 2026-01-28
status: active
---

# Narrative Directory Index

## Core Narrative Structure

### 📖 Foundation Documents
```dataview
LIST 
FROM "narrative" 
WHERE file.name != "Index.md" AND 
      (contains(file.name, "CORE") OR 
       contains(file.name, "HERO") OR
       contains(file.name, "STRUCTURE"))
SORT file.name ASC
```

### 🎭 Session Resources
```dataview
LIST 
FROM "narrative" 
WHERE contains(file.name, "Session") OR
      contains(file.name, "Awakening")
SORT file.name ASC
```

### 🎪 Story Elements
```dataview
LIST 
FROM "narrative" 
WHERE file.name != "Index.md" AND
      !(contains(file.name, "CORE") OR 
        contains(file.name, "HERO") OR
        contains(file.name, "Session") OR
        contains(file.name, "Awakening"))
SORT file.name ASC
```

### 📊 Directory Stats
- **Total Files:** `= length(file.rows)`
- **Last Updated:** `= date(now)`
- **Purpose:** Campaign narrative, story structure, and session resources

---

## About This Directory

This directory contains the narrative foundation of Tarim-Shaiel:
- **Core Narrative** - Campaign foundation and hero identity
- **Session Structure** - Session 0 awakening scenarios and templates
- **Story Elements** - Shared memory events and narrative components
- **Audio Resources** - Music and atmospheric elements

## Key Documents

- **[[CORE_CAMPAIGN_NARRATIVE.md|Core Campaign Narrative]]** - Main story foundation
- **[[HERO_IDENTITY.md|Hero Identity]]** - Character and cosmological foundation
- **[[Sessions_Structure.md|Session Structure]]** - Campaign session framework

## Related Directories

- [[../characters|Character Frameworks]]
- [[../world|World-Building]]
- [[../mechanics|Game Systems]]

---

*This index updates automatically using Dataview queries.*

---

## Session 0: Awakening Scenarios

**Overview:** Individual hero awakening scenes, each 40-45 minutes, establishing archetype doubts and tool relationships.

### Completed Archetypes

- **[[Session_0_Warrior_Awakening]]** ✅ v2.0 Complete
  - *Restraint as strength; protection without dominance*
  - Refugee camp crisis, blade weapon
  - [[Session_0_Warrior_Awakening_VERSIONS|Version History]]

- **[[Session_0_Seeker_Awakening]]** ✅ v0.4 Complete
  - *Truth vs. comfort; instinct when certainty fails*
  - Desert wasteland, tome/compass/astrolabe
  - [[Session_0_Seeker_Awakening_VERSIONS|Version History]]

### In Progress

- **[[Session_0_Breaker_Awakening]]** 🚧 v0.2.1 In Progress
  - *Identity vs. survival; power vs. abandonment*
  - Collapsed inn, hammer (load-bearing)
  - Status: Segment 1/8 complete (Erikson-grade prose)
  - [[Session_0_Breaker_Awakening_VERSIONS|Version History]]

### Not Yet Started

- **Session_0_Bridge_Awakening** ⏳ Planned
  - *Prison cell; talk your way free when compromise seems impossible*
  - Tool: TBD (possibly rope, chain, or vocal instrument?)

- **Session_0_Sacrificer_Awakening** ⏳ Planned
  - *Give up something vital when loss seems unbearable*
  - Tool: TBD

- **Session_0_Visionary_Awakening** ⏳ Planned
  - *See the path forward when all futures look dark*
  - Tool: Tarot deck (noted in Breaker planning)

---

## Session 0: Supporting Materials

### Templates & Frameworks

- **[[Session_0_Secret_Snippets-Archetype_Templates]]** 📋 Reference
  - Secret snippet text for all six archetypes
  - Delivered during crisis moments
  - Establishes alignment memories

- **[[Sessions_Structure]]** 📋 Framework
  - Overall Session 0 architecture
  - Convergence mechanics
  - Multi-scene management guidance

- **[[Shared_Memory_Narrative_Template]]** 📋 Template
  - Format guide for crafting future scenes
  - Prose technique reference
  - Consistency standards

### Planning Documents

- **[[TEMP_Breaker_Planning_Notes]]** 📝 Working Notes
  - Breaker scenario development decisions
  - Tool selection rationale
  - Crisis architecture planning

---

## Core Campaign Narrative

### Primary Documents

- **[[CORE_CAMPAIGN_NARRATIVE]]** 📖 Master Document
  - Overarching campaign story
  - Thematic framework
  - World state and conflicts

- **[[story_skeleton]]** 🦴 Structure
  - Campaign arc outline
  - Key story beats
  - Narrative scaffolding

- **[[Shared_Memory_Events]]** 🧠 Memory Framework
  - Shared hero experiences
  - Heaven expulsion context
  - Fragmentary memory system

---

## Document Status Legend

- ✅ **Complete** - Publication ready, playtested/refined
- 🚧 **In Progress** - Active development, partial completion
- ⏳ **Planned** - Outlined but not yet started
- 📋 **Reference** - Supporting material, templates
- 📖 **Master** - Core campaign documentation
- 📝 **Working** - Temporary planning notes
- 🦴 **Structure** - Framework/outline documents
- 🧠 **Conceptual** - Thematic/theoretical foundations

---

## Version Control Notes

**Tracked Documents:**
- Warrior, Seeker, Breaker awakenings maintain detailed VERSION.md files
- Version history tracks prose refinements, structural changes, decision rationale

**Untracked Documents:**
- Reference materials and templates (stable, infrequently updated)
- Planning notes (ephemeral, conversation-specific)

---

## Quick Reference: Archetype Status

| Archetype | Status | Version | Segments Complete | Tool |
|-----------|--------|---------|-------------------|------|
| Warrior | ✅ Complete | v2.0 | 8/8 | Iron blade |
| Seeker | ✅ Complete | v0.4 | All paths | Tome/compass/astrolabe |
| Breaker | 🚧 In Progress | v0.2.1 | 1/8 | Hammer |
| Bridge | ⏳ Planned | - | 0/8 | TBD |
| Sacrificer | ⏳ Planned | - | 0/8 | TBD |
| Visionary | ⏳ Planned | - | 0/8 | Tarot deck |

---

## Related Project Files

**Outside narrative/ directory:**
- [[INDEX]] - Project root index
- [[TODO]] - Overall project task tracking
- [[DECISION_LOG]] - Major project decisions
- [[ARCHITECTURAL_DECISIONS]] - System design choices

**Mechanics Integration:**
- See `/mechanics` directory for charm systems, tools progression, celestial dice

**World Building:**
- See `/world` directory for geography, cultures, historical context

---

**Note:** This index should be updated when:
- Awakening scenarios reach new version milestones
- New documents are created
- Status changes (planned → in progress → complete)
- Major structural changes occur
