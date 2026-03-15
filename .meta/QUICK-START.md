---
title: Quick Start Guide
project: TTRPG_Tarim_Shaiel
type: onboarding
status: active
created: 2025-12-05
last_updated: 2026-02-11
---

# Tarim-Shaiel: Quick Start Guide

## Getting Oriented

**Tarim-Shaiel** is a comprehensive TTRPG campaign workspace built on Daggerheart, organized into clear domains:

- **📖 /narrative/** - Campaign story, session content, awakening scenarios
- **🌍 /world/** - Setting, locations, cultures, history, maps
- **⚙️ /mechanics/** - Game systems, charms, character progression
- **👥 /characters/** - Archetypes, character frameworks
- **📋 /templates/** - Reusable templates for content creation
- **📚 /references/** - Daggerheart SRD and reference materials
- **🛠️ /utilities/** - Scripts, tools, operational resources

**Start here:** [[README.md|Project Overview]] for full navigation

---

## Quick Workflows

### As Game Master

**Preparing Session 0:**
1. Review [[narrative/CORE_CAMPAIGN_NARRATIVE.md|Core Campaign Narrative]]
2. Choose archetype awakening scenarios in `/narrative/sessions/00_session0/`
3. Check [[narrative/gm_secrets/|GM secrets]] for hidden plot elements
4. Review [[world/content/CULTURAL_FRAMEWORK.md|Cultural Framework]] for world context

**Creating Locations:**
1. Use templates in `/templates/world-building/`
2. Add to `/world/locations/`
3. Mark visibility: `public` or `gm_secrets` in frontmatter

**Managing Mechanics:**
1. Review [[mechanics/character-progression/|Character Progression]] for charm systems
2. Check [[mechanics/design-decisions/|Design Decisions]] for mechanical rationale

### As Content Creator

**Adding World Content:**
1. Check `/templates/` for relevant template
2. Create file in appropriate domain (`/world/`, `/narrative/`, etc.)
3. Add frontmatter with visibility metadata:
   ```yaml
   ---
   visibility: public
   status: draft
   ---
   ```
4. Link from domain index

**Publishing to Players:**
- Public content: Store in domain root (e.g., `/narrative/`, `/world/`)
- GM-only content: Store in `/[domain]/gm_secrets/`

---

## Project Structure Principles

### Root Directory = PROJECT Infrastructure
Files at root are about *how the project works*, not campaign content:
- [[ARCHITECTURAL_DECISIONS.md|Architectural Decisions]] - Project structure
- [[DECISION_LOG.md|Decision Log]] - Design rationale
- [[FILE_PERSISTENCE_GUIDELINES.md|File Persistence Guidelines]]
- [[TODO.md|Project Tasks]]
- [[SETUP_AND_CONFIGURATION.md|Setup & Configuration]]

### Domain Organization
- Each domain (`/narrative/`, `/world/`, etc.) has its own `Index.md` or `README.md`
- Content organized by domain first, then by type
- Consistent `/gm_secrets/` folders for classified content

### Metadata Conventions
```yaml
---
visibility: public | gm_secrets
status: draft | review | canon
session_type: awakening | convergence | adventure
archetype: warrior | seeker | breaker | all
---
```

See [[FILE_PERSISTENCE_GUIDELINES.md|File Persistence Guidelines]] for details

---

## Common Tasks

### Finding Content
- **By domain**: Check domain index (`/narrative/README.md`, `/world/Index.md`, etc.)
- **By topic**: Use Obsidian search or grep
- **Reference materials**: Check `/references/daggerheart-srd/`

### Creating Session Content
1. Start with `/narrative/sessions/`
2. Use session templates from `/templates/`
3. Separate player content from `/gm_secrets/`
4. Link audio assets from `/narrative/audio/`

### Working with Maps
1. Map data in `/world/maps/` and `/world/data/`
2. Map images in `/world/images/`
3. Use Obsidian Leaflet plugin for interactive maps
4. Check `/world/workflow/` for map creation processes

---

## Technical Setup

### Prerequisites
- Obsidian vault with Tarim-Shaiel content
- Python 3.8+ (for utilities)
- Git (optional, for version control)

Full guide: [[SETUP_AND_CONFIGURATION.md|Setup & Configuration]]

---

## Getting Help

**Project questions**: Check [[ARCHITECTURAL_DECISIONS.md|Architectural Decisions]]
**Content creation**: See `/templates/` for examples
**Game mechanics**: Review `/mechanics/` and [[references/daggerheart|Daggerheart SRD]]
**Workflow questions**: Check domain-specific README files

---

## Next Steps

Choose your path:

**🎲 Running Session 0**
→ [[narrative/sessions/00_session0/|Session 0 Content]]

**🌍 Building the World**
→ [[world/Index.md|World Hub]]

**⚙️ Understanding Mechanics**
→ [[mechanics/Index.md|Mechanics Hub]]

**📋 Creating Content**
→ [[templates/Index.md|Templates Hub]]
