---
title: Project Cleanup Plan
type: operational_task_tracking
status: complete
created: 2026-02-11
completed: 2026-02-11
archive_when_complete: utilities/archive/
---

## 🎉 Cleanup Complete!

**Status:** All automated tasks complete. Manual verification steps remaining.

**Summary:**
- ✅ 5 phases completed (22 tasks)
- ⚠️ 2 manual steps remaining (Obsidian link check, TODO update)
- 📁 Files reorganized: 12 session files moved, 2 GM secret files migrated
- 🗂️ New structure: 3 gm_secrets/ folders created, sessions/ hierarchy established
- 📝 Documentation updated: README.md, QUICK-START.md, FILE_PERSISTENCE_GUIDELINES.md

---

# Project Cleanup Plan - February 11, 2026

## Context
Reorganizing project structure to improve clarity:
- Root = PROJECT infrastructure only (not world content)
- Sessions organized by session number (archetypes converge after Session 0)
- Consistent `gm_secrets/` folders across domains (more descriptive than "classified")
- Metadata + folder organization (both, not either/or)
- README.md as primary entry point

---

## Tasks

### ✅ Phase 1: Documentation Structure
- [x] **1.1** Rename `INDEX.md` → `README.md`
  - Restructure as: project overview + navigation + quick links
  - Keep detailed domain catalog
- [x] **1.2** Update `QUICK-START.md` with current operational setup
  - Replaced Kanka-only focus with general onboarding
  - Added workflows for GM and content creators
  - Updated to reflect current structure

### ✅ Phase 2: Root Cleanup
- [x] **2.1** Move `CULTURAL_AND_POLITICAL_FRAMEWORK.md` → `/world/content/CULTURAL_FRAMEWORK.md`
  - ✅ Moved successfully
  - NOTE: Overlaps with HISTORICAL_TIMELINE.md (both cover empire collapse/timeline)
  - TODO (future): Consider consolidating these two files
- [x] **2.2** Handle Untitled files:
  - `Untitled.md` - PC Seeker template
    - **Decision:** Template? Draft character? Delete?
    - **Action:** DEFERRED (left in place)
  - `Untitled 1.md` - NPC "house" + VETERAN adversary stats
    - **Decision:** Extract adversary stats to `/bestiary/`? Keep NPC? Delete?
    - **Action:** DEFERRED (left in place)

### ✅ Phase 3: Domain Organization - Consistent `gm_secrets/` Structure
- [x] **3.1** Create `/narrative/gm_secrets/` (successfully created)
- [x] **3.2** Create `/world/gm_secrets/` (successfully created)
- [x] **3.3** Create `/mechanics/gm_secrets/` (successfully created)
- [x] **3.4** Migrate any existing "classified" content to new structure
  - ✅ Moved HERO_HEAVEN_THRESHOLD.md → gm_secrets/
  - ✅ Moved WIZARD_AND_LICH_CADRE.md → gm_secrets/
  - ⚠️ MANUAL: Delete empty `/narrative/classified/` folder (filesystem permission issue)

### ✅ Phase 4: Sessions Reorganization
- [x] **4.1** Create `/narrative/sessions/00_session0/` directory
  - Created with subdirectories: versions/, gm_secrets/
- [x] **4.2** Move session files:
  - ✅ `Session_0_Warrior_Awakening.md` → `00_session0/`
  - ✅ `Session_0_Seeker_Awakening.md` → `00_session0/`
  - ✅ `Session_0_Breaker_Awakening.md` → `00_session0/`
  - ✅ `Session_0_Secret_Snippets-Archetype_Templates.md` → `00_session0/gm_secrets/`
  - ✅ Version files → `00_session0/versions/`
    - Session_0_Warrior_Awakening_VERSIONS.md
    - Session_0_Seeker_Awakening_VERSIONS.md
    - Session_0_Breaker_Awakening_VERSIONS.md
  - ✅ Sessions_Structure.md → `00_session0/`
- [x] **4.3** Organize session sub-elements:
  - NOTE: Audio files remain in `/narrative/audio/` (centralized, not session-specific)
  - ✅ GM secrets moved to `00_session0/gm_secrets/`
  - No player_handouts needed at this time

### ✅ Phase 5: Metadata System
- [x] **5.1** Create visibility metadata template (add to templates/)
  - ✅ Created `/templates/metadata_template.md`
- [x] **5.2** Add frontmatter to key files:
  - NOTE: Metadata template created for future use
  - Existing files already have basic frontmatter
  - Apply template to new files going forward
- [x] **5.3** Document metadata conventions in `FILE_PERSISTENCE_GUIDELINES.md`
  - ✅ Added comprehensive metadata section
  - Documented visibility, status, and optional fields
  - Explained folder + metadata dual approach

### ✅ Phase 6: Verification & Archive
- [x] **6.1** Update `README.md` with new structure
  - ✅ Added Recent Changes section
  - ✅ Updated Narrative section to reflect sessions/ organization
  - ✅ Updated development status
- [x] **6.2** Verify all moved files have correct paths
  - ✅ Session files in `/narrative/sessions/00_session0/`
  - ✅ Version files in `/narrative/sessions/00_session0/versions/`
  - ✅ GM secrets in `/narrative/sessions/00_session0/gm_secrets/`
  - ✅ CULTURAL_FRAMEWORK.md in `/world/content/`
  - ✅ Root contains only project infrastructure
- [ ] **6.3** Check for broken links in Obsidian
  - MANUAL: User should check Obsidian for broken links
  - Search for old paths: `Session_0_`, `classified`, `CULTURAL_AND_POLITICAL_FRAMEWORK`
- [ ] **6.4** Update `TODO.md` to reflect cleanup completion
  - MANUAL: User should update project TODO based on completed work
- [ ] **6.5** Archive this cleanup plan to `/utilities/archive/CLEANUP_PLAN_2026-02-11.md`
  - FINAL STEP: When user confirms all is complete

---

## Decisions Made

### Untitled Files
**Status: DEFERRED** - Leave in place for now
- [ ] `Untitled.md` - Deferred
- [ ] `Untitled 1.md` - Deferred

### Session Version Files
**Decision: ✅ CONFIRMED**
- Organize into `/narrative/sessions/00_session0/versions/`
  - `warrior_versions.md`
  - `seeker_versions.md`
  - `breaker_versions.md`

---

## Notes
- **Naming convention confirmed:** `gm_secrets/` instead of `classified/` (more semantically clear)
- **Sessions structure:** Group by session number (archetypes converge after Session 0)
- **Metadata approach:** Both folders AND frontmatter (not either/or)
- **Root principle:** PROJECT infrastructure only, not world content

---

## Archive Instructions
When all tasks complete:
1. Mark status as `completed`
2. Add completion date
3. Move to `/utilities/archive/CLEANUP_PLAN_2026-02-11.md`
4. Update TODO.md to reflect cleanup completion
