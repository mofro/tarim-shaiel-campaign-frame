---
title: World Directory Cleanup - Addendum
type: operational_task_tracking
status: complete
created: 2026-02-11
parent_plan: CLEANUP_PLAN_2026-02-11.md
archive_with_parent: true
---

# World Directory Cleanup - Addendum

## Context
Follow-up cleanup of `/world/` directory based on organizational principles established in main cleanup plan.

---

## Issues Identified

### 1. Template Misplaced
- `_TEMPLATE_region.md` was in `/world/regions/` (world content location)
- Templates should be in `/templates/` directory

### 2. Test/Experimental Files in Production Location
- 6 `test_*.md` files in `/world/maps/` cluttering production map directory
- Experimental files should be in `/templates/experiments/`

### 3. Operational Docs Mixed with World Content
- `/world/workflow/` - Process guides (MAPPING_PROJECT_PLAN, PUBLISHING_WORKFLOWS, WORLD_CREATION_WORKFLOW)
- `/world/systems/` - Technical docs (DATAVIEW_QUERIES, LOCATION_NOTE_SCHEMA, MAPPING_ARCHITECTURE, etc.)
- These describe HOW to build the world, not world content itself
- Should be in `/utilities/` with other project infrastructure

### 4. Naming Convention Confirmed
- **ALL_CAPS** in `/world/content/` = High-level canonical frameworks
  - HISTORICAL_TIMELINE.md, CULTURAL_FRAMEWORK.md, WORLD_REGIONS_AND_LOCATIONS.md
- **lowercase** = Detailed/specific content
  - geography_silk_road_reference.md, merchant_networks_guilds.md
- Pattern is consistent and meaningful - **no changes needed**

---

## Tasks Completed

### ✅ Phase 7: World Directory Reorganization
- [x] **7.1** Move test files to experiments
  - ✅ Created `/templates/maps/experiments/`
  - ✅ Moved 6 test files:
    - test_dataview.md
    - test_geojson_native.md
    - test_geojson_overlay.md
    - test_leaflet.md
    - test_minimal_labels.md
    - test_topo_override.md

- [x] **7.2** Move region template to templates directory
  - ✅ Moved `_TEMPLATE_region.md` → `/templates/world-building/`

- [x] **7.3** Move operational docs to utilities
  - ✅ Created `/utilities/world-building/`
  - ✅ Moved `/world/workflow/` → `/utilities/world-building/workflow/`
    - MAPPING_PROJECT_PLAN.md
    - PUBLISHING_WORKFLOWS.md
    - WORLD_CREATION_WORKFLOW.md
  - ✅ Moved `/world/systems/` → `/utilities/world-building/systems/`
    - DATAVIEW_QUERIES.md
    - LOCATION_COORDINATE_DASHBOARD.md
    - LOCATION_NOTE_SCHEMA.md
    - MAPPING_ARCHITECTURE.md
    - MARKER_TYPES_AND_TILES.md

- [x] **7.4** Verify naming conventions
  - ✅ Confirmed ALL_CAPS = high-level frameworks
  - ✅ Confirmed lowercase = detailed/specific content
  - ✅ No changes needed - pattern is consistent

---

## Results

### `/world/` Directory is Now Clean
**Contains only world content:**
- `/world/content/` - World-building content (cultures, history, geography)
- `/world/locations/` - Individual location files
- `/world/regions/` - Regional groupings
- `/world/maps/` - Production maps (tests removed)
- `/world/data/` - Geospatial data
- `/world/images/` - Map images and visual assets
- `/world/markers/` - Map markers
- `/world/mythology/` - Mythological content
- `/world/gm_secrets/` - GM-only world content

### Templates Properly Organized
- `/templates/world-building/_TEMPLATE_region.md` - Region template
- `/templates/maps/experiments/` - Map experimentation files

### Utilities Contains Infrastructure
- `/utilities/world-building/workflow/` - World creation processes
- `/utilities/world-building/systems/` - Technical mapping infrastructure

---

## Impact

**Clarity Improved:**
- `/world/` contains ONLY world content (not tooling/process docs)
- Templates centralized in `/templates/`
- Infrastructure/tooling centralized in `/utilities/`

**Consistency Maintained:**
- ALL_CAPS naming convention confirmed as meaningful
- Folder organization aligns with established principles
- No exceptions or special cases

---

## Archive Instructions
When main cleanup plan is archived:
1. Archive this addendum alongside it
2. Update `/world/Index.md` to reflect new structure (no workflow/ or systems/ folders)
3. Update `/utilities/` navigation to include world-building subdirectory
