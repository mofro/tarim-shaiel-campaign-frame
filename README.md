---
title: Tarim-Shaiel - Project Overview
project: TTRPG_Tarim_Shaiel
type: navigation
status: active
created: 2025-12-05
last_updated: 2026-02-11
---

# Tarim-Shaiel: TTRPG Campaign Project

**A Daggerheart campaign set in a post-imperial world** where heroes awaken to confront the remnants of a fallen empire, navigate emerging power dynamics, and discover their role in shaping the future.

## What is This Project?

This is a comprehensive TTRPG campaign development workspace for **Tarim-Shaiel**, combining:
- **World-building**: 8 regions, 37 locations, complete cultural and political frameworks
- **Game mechanics**: Custom charm system integrated with Daggerheart rules
- **Narrative design**: Session 0 awakening scenarios for three core archetypes (Warrior, Seeker, Breaker)
- **Operational tools**: Templates, workflows, and AI persona integration for game mastering

📖 **New here?** Start with [[QUICK-START.md|Quick Start Guide]]
🏗️ **Understanding the structure?** See [[ARCHITECTURAL_DECISIONS.md|Architectural Decisions]]

---

## Project Navigation

## Domain-Aligned Structure

### 🏛️ Core Architecture
- **[[ARCHITECTURAL_DECISIONS.md|Architectural Decisions]]** - Project structure, workflow guidance, persona definitions
- **[[DECISION_LOG.md|Decision Log]]** - Design decisions with rationale (started 2025-12-07)
- **[[TODO.md|Project Tasks]]** - Current development priorities and status
- **[[FILE_PERSISTENCE_GUIDELINES.md|File Persistence Guidelines]]** - What to keep vs context-only

### ⚙️ Game Mechanics
- **[[mechanics/Index|Mechanics Hub]]** - Complete game systems (5 domains)
  - **Character Creation** - Session 0 and character development
  - **Character Progression** - Charms, tools, advancement systems
  - **Magic Systems** - Spells vs charms analysis
  - **Charm Analysis** - Detailed charm system research
  - **Design Decisions** - Mechanical design rationale

### 🌍 World-Building
- **[[world/Index|World Hub]]** - Complete setting (8 domains, 37 locations)
  - **Workflow** - World creation processes
  - **Systems** - Technical infrastructure and mapping
  - **Content** - World-building content and regions
  - **Locations** - Individual location files (cities, sites)
  - **Data** - Geospatial data and mapping files
  - **Images** - Maps and visual assets

### 📖 Narrative Foundation
- **[[narrative/README|Narrative Hub]]** - Campaign story and structure
  - **Core Narrative** - Campaign foundation and hero identity
  - **Sessions** - Organized by session number (Session 0 in `/narrative/sessions/00_session0/`)
  - **Story Elements** - Shared memory events and components
  - **GM Secrets** - Classified plot elements and future reveals

### 👥 Character Elements
- **[[characters/Index|Character Hub]]** - Character development frameworks
  - **Archetypes** - Six modes of heroism and thematic tensions

### 📋 Templates Library
- **[[templates/Index|Templates Hub]]** - Unified template system (6 categories)
  - **Character Creation** - Character and session templates
  - **Mechanics** - Charm, domain, and mechanical templates
  - **World-Building** - Location, environment, and adversary templates
  - **Kanka Integration** - Kanka sync templates and snippets
  - **Tarim Shaiel** - Campaign-specific location templates

### 📚 Reference Materials
- **[[references/daggerheart|Daggerheart Library]]** - System reference PDFs (7 files)
- **[[transcripts/Index|Transcripts Hub]]** - Session development history (12 files)

### 🎵 Assets & Utilities
- **[[Music|Music Collection]]** - Atmospheric and thematic audio (20 files)
- **[[utilities|Utilities]]** - Scripts, tools, and operational resources

---

## 🎯 Quick Navigation

- **⚙️ [[mechanics/Index|Mechanics]]** - Game Systems (character progression, charms, magic)
- **🌍 [[world/Index|World-Building]]** - Setting Development (37 locations, mapping systems)  
- **📖 [[narrative/README|Narrative]]** - Story Foundation (campaign structure, sessions)
- **👥 [[characters/Index|Characters]]** - Character Development (archetypes, frameworks)
- **📋 [[templates/Index|Templates]]** - Content Creation (unified template library)
- **📚 [[references/daggerheart|References]]** - System Resources (Daggerheart PDFs, transcripts)

---

## Development Status

### ✅ Completed (January 2026)
- **Domain-aligned organization** - All directories properly structured
- **Dynamic index system** - Self-updating navigation for all domains
- **Template unification** - Single source of truth for all templates
- **Reference library** - Organized PDF and transcript collections
- **World creation workflow** - Complete mapping and location systems

### 🔄 Active Development (February 2026)
- **Session 0 scenarios** - Warrior, Seeker, Breaker awakening sequences
- **Charm system implementation** - Mechanical integration with Daggerheart
- **Location content development** - 37 sites with full details
- **Kanka sync integration** - Publishing workflow for players
- **Project cleanup** - Domain organization, consistent gm_secrets/ structure

---

---

## Recent Changes (February 11, 2026)

**Project Reorganization:**
- ✅ Root directory = PROJECT infrastructure only (no world content)
- ✅ `INDEX.md` → `README.md` with project overview
- ✅ `CULTURAL_FRAMEWORK.md` moved to `/world/content/`
- ✅ Sessions organized: `/narrative/sessions/00_session0/` with subdirectories
- ✅ Consistent `gm_secrets/` folders across domains (replaces "classified")
- ✅ Metadata conventions documented in `FILE_PERSISTENCE_GUIDELINES.md`

*This README reflects the current domain-aligned structure as of February 2026. Each domain has its own dynamic index for detailed navigation.*
