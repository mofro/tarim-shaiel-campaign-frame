---
title: World Creation Workflow
type: workflow-guide
category: world-building
tags: [workflow, world-building, content-creation]
created: 2025-01-27
status: active
---

# World Creation Workflow

**Comprehensive guide to creating and managing Tarim-Shaiel campaign content.**

---

## Overview

This document serves as the central hub for all world-building workflows, templates, and processes used in creating the Tarim-Shaiel campaign setting.

---

## Core Workflows

### **Location Creation**
- [[location-template|Location Template]] - Full location structure
- [[LOCATION_NOTE_SCHEMA|Location Schema]] - Field definitions and standards
- [[daily-workflow|Kanka Sync Workflow]] - Publishing to players

### **Maps & Geography**
- Leaflet integration *(documentation needed)*
- Geographic coordinate system *(documentation needed)*
- Map marker conventions *(documentation needed)*

### **Mythology & Lore**
- Heaven cosmology *(documentation needed)*
- Deity/hero pantheon *(documentation needed)*
- Charm system integration *(documentation needed)*

### **Events & Timeline**
- Historical events *(documentation needed)*
- Campaign timeline *(documentation needed)*
- Session tracking *(documentation needed)*

### **Factions & Organizations**
- Faction templates *(to be created)*
- Power structure documentation *(documentation needed)*
- Relationship mapping *(documentation needed)*

---

## Content Types & Templates

### **Locations**
**Primary Template:** [[location-template|location-template.md]]

**Workflow:**
1. Copy location template
2. Fill in frontmatter (name, type, coordinates, etc.)
3. Write body sections (Geography, Economy, etc.)
4. Add GM sections (Narrative Significance, Secrets, Hooks)
5. When ready for players: Add Kanka fields, sync

**Reference:** [[daily-workflow|Daily Workflow Guide]]

---

### **Characters**
**Template:** *(to be created)*

**Workflow:** *(to be defined)*

**Archetypes:**
- Breaker
- Bridge
- Seeker
- Sacrificer
- Warrior
- Visionary

**Reference:** [[../characters/|Characters Directory]]

---

### **Bestiary**
**Template:** *(to be created)*

**Workflow:** *(to be defined)*

**Reference:** [[../bestiary/|Bestiary Directory]]

---

### **Narrative Elements**
**Template:** *(to be created)*

**Workflow:** *(to be defined)*

**Reference:** [[../narrative/|Narrative Directory]]

---

### **Mechanics**
**Template:** *(to be created)*

**Workflow:** *(to be defined)*

**Daggerheart Integration:**
- Heritage system
- Charm mechanics
- Session frameworks

**Reference:** [[../mechanics/|Mechanics Directory]]

---

## Publishing Workflows

### **Kanka Sync (Player-Facing Content)**

**What Gets Synced:**
- ✅ Player-visible locations
- ✅ Character archetypes (templates)
- ✅ Public lore and history
- ✅ Quests (when introduced)

**What Stays Obsidian-Only:**
- ❌ Session prep notes
- ❌ Detailed GM planning
- ❌ Templates and authoring tools
- ❌ Spoilers for future arcs

**Process:**
1. Author content in Obsidian normally
2. Add `kanka_type` field when ready for players
3. Run sync script
4. Content appears in Kanka with proper routing (public/GM split)

**Full Guide:** [[utilities/kanka-sync/INDEX|Kanka Sync Documentation]]

---

### **Campaign Artifacts (Files for Players)**

**Process:** *(to be defined)*

**Types:**
- Handouts
- Maps (player versions)
- Character sheets
- Reference documents

---

## Standards & Conventions

### **Naming Conventions**

**Files:**
- Locations: `lowercase-with-hyphens.md` (e.g., `samarkand.md`)
- Characters: `lowercase-with-hyphens.md` (e.g., `hero-archetype-breaker.md`)
- Consistency across all content types

**Frontmatter:**
- `name` - Display name (Title Case)
- `type` - Entity subtype (lowercase)
- `tags` - Array format `[tag1, tag2]`

---

### **Coordinate System**

**Format:** `[latitude, longitude]`

**Reference System:** Real-world Silk Road coordinates transformed for fantasy setting

**Tools:**
- Google Earth for visualization
- Leaflet for interactive maps
- KML generation for geographic data

---

### **Section Structure**

**Public Sections (Player-Facing):**
Standard sections that appear in Kanka main entry:
- Geography
- Economy
- Key Features
- Factions
- Resources
- Cultural Notes
- Historical Basis

**GM Sections (Admin-Only):**
These become separate posts in Kanka:
- Narrative Significance
- Key Narrative Elements
- Hidden Secrets
- Plot Hooks
- DM Notes
- World-Building Context

**Reference:** [[routing-rules|Content Routing Rules]]

---

## Quick Start Guides

### **I Want To...**

| Task | Guide |
|------|-------|
| Create a new location | [[location-template\|Location Template]] |
| Sync content to Kanka | [[quickstart\|Kanka Quickstart]] |
| Understand location fields | [[LOCATION_NOTE_SCHEMA\|Location Schema]] |
| Add a map to a location | *(guide needed)* |
| Create a character archetype | *(guide needed)* |
| Define a faction | *(guide needed)* |
| Build a quest | *(guide needed)* |

---

## Tools & Utilities

### **Scripts**
- `kanka-sync.py` - Sync Obsidian → Kanka
- `kanka-bulk-prepare.py` - Bulk add Kanka frontmatter
- `mountain_range_generator.py` - Geographic data generation

### **Templates**
- Campaign Templates: `/utilities/templates/tarim-shaiel-templates/`
- Kanka Integration: `/utilities/templates/kanka-templates/`

### **Documentation**
- Kanka Sync: `/utilities/kanka-sync/`
- Location Schema: `LOCATION_NOTE_SCHEMA.md`

---

## Content Organization

### **Directory Structure**

```
/world/
├─ WORLD_CREATION_WORKFLOW.md    ← This file
├─ LOCATION_NOTE_SCHEMA.md       ← Location field reference
├─ Locations/                    ← All location files
├─ Regions/                      ← Regional overviews
└─ Maps/                         ← Map files and data
```

---

## Workflow Evolution

### **Completed Workflows**
- ✅ Location creation (template + schema)
- ✅ Kanka sync (automated publishing)
- ✅ Content routing (public/GM split)

### **In Progress**
- 🔄 Character creation workflow
- 🔄 Map integration workflow
- 🔄 Faction workflow

### **Planned**
- 📋 Quest workflow
- 📋 Bestiary workflow
- 📋 Event/timeline workflow
- 📋 Session prep workflow
- 📋 Mythology documentation workflow

---

## Best Practices

### **Content Creation**

1. **Start with templates** - Don't build from scratch
2. **Fill frontmatter first** - Establishes structure
3. **Write naturally** - Don't worry about Kanka while authoring
4. **Add GM sections** - Separate player/GM content from the start
5. **Sync when ready** - Add Kanka fields when content is player-facing

---

### **Version Control**

**When to commit:**
- ✅ After completing a location
- ✅ After major session prep
- ✅ Before bulk operations

**What to track:**
- ✅ All markdown content
- ✅ Configuration files
- ✅ Scripts and utilities
- ❌ Logs (`.gitignore`)
- ❌ Cache files

---

### **Documentation**

**When to update:**
- When creating new content types
- When establishing new conventions
- When workflows change
- When adding new tools

**Where to document:**
- Workflows → This file
- Schemas → Individual `*_SCHEMA.md` files
- Technical docs → `/utilities/` subdirectories
- Templates → `/utilities/templates/`

---

## Related Documentation

### **Core References**
- [[LOCATION_NOTE_SCHEMA|Location Note Schema]] - Field definitions
- [[utilities/kanka-sync/INDEX|Kanka Sync Documentation]] - Publishing workflow
- [[location-template|Location Template]] - Content creation

### **Campaign Design**
- [[HERO_IDENTITY|Hero Identity]] - Core themes
- [[ARCHITECTURAL_DECISIONS|Architectural Decisions]] - Design choices
- [[CULTURAL_FRAMEWORK]] - World structure

### **Session Management**
- [[narrative/story_skeleton|Story Skeleton]] - Campaign arc
- *(Session prep workflow - to be created)*
- *(Timeline - to be created)*

---

## Contributing

This workflow document evolves as the campaign develops. When you:
- Create a new content type → Add a section
- Establish a new convention → Document it
- Build a new workflow → Link to it
- Find a better way → Update the relevant section

**This is a living document.** Keep it current!

---

*Last updated: 2025-01-27*
