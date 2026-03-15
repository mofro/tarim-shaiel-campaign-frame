---
title: TTRPG Tarim-Shaiel - Interactive Mapping Architecture
project: TTRPG_Tarim_Shaiel
type: mapping_system
status: in_development
created: 2025-12-08
last_updated: 2025-12-08
---

# Interactive Mapping Architecture: Overview & System Design

## Purpose
Define the complete system for managing world geography, locations, and routes as **persistent, queryable data** that flows through multiple presentation layers (Obsidian Leaflet maps, KML exports for Google Earth, Dataview queries for reference).

---

## Core Principle: Single Source, Multiple Outputs

All geographic and location data originates from **Location Notes** (Obsidian markdown files with standardized frontmatter). From these notes, we generate:
- **Leaflet maps** (interactive, tagged for GM/player visibility)
- **GeoJSON** (for computational use, transpilation)
- **KML/KMZ** (for Google Earth export)
- **Dataview pages** (queryable reference dashboards)

No duplication. No manual sync. The notes are the source of truth.

---

## System Components

### 1. Location Notes (`/world/locations/`)
Individual markdown files for each map entity: cities, landmarks, natural features, settlement routes, etc.

**Minimal schema (5 fields):**
- `name` – canonical name (may differ from fantasy name via property)
- `location` – [latitude, longitude]
- `type` – entity category (city, landmark, natural-feature, route-node, settlement, etc.)
- `created` – YYYY-MM-DD (set once)
- `last_updated` – YYYY-MM-DD (auto-updated or manual)

**Additional properties** (emergent, optional):
- `description` – narrative/historical context
- `faction` – affiliation(s)
- `narrative_weight` – boolean flag for plot-driven importance
- `elevation` – altitude data
- `resources` – trade goods, materials
- Tags: `#gm-only`, `#player-visible`, `#session-X`, etc.

See `LOCATION_NOTE_SCHEMA.md` for full spec and examples.

### 2. Data Layer (`/world/data/`)
Structured exports and intermediates:
- `regions.json` – geographic master index (auto-generated from Location Notes via Dataview)
- `geojson_master.geojson` – full GeoJSON feature collection (used by Leaflet, can be transpiled to KML)
- `geojson_player.geojson` – filtered GeoJSON (player-visible only)
- `geojson_gm.geojson` – unfiltered GeoJSON (GM reference)

### 3. Map Notes (`/world/maps/`)
Obsidian notes that instantiate Leaflet maps by referencing Location Note data.

**Variants:**
- `master_world_map.md` – GM reference, all locations, all details
- `session_[N]_map.md` – tagged to show only session-relevant locations
- `faction_territories_map.md` – faction-tagged features
- `trade_routes_map.md` – route-tagged features

Each map note is a simple Leaflet code block that loads filtered GeoJSON or uses `markerTag` + `markerFolder` to pull from Location Notes directly.

### 4. Reference Documentation (`/world/`)
Human-readable narrative files (history, descriptions, social context):
- `geography_silk_road_reference.md` – original research notes
- `peoples_and_polities.md` – faction descriptions and politics
- `merchant_networks_guilds.md` – NPC factions, trading structures
- `historical_conflicts_disputes.md` – context for emergent conflicts

These inform *why* locations exist and matter, but don't contain coordinate data. They're cross-linked from Location Notes via wikilinks.

---

## Data Flow: From Notes to Maps

```
Location Notes (source)
    ↓
Dataview Query (filter by tag/type/date)
    ↓
GeoJSON generation (script or manual export)
    ↓
Leaflet Map Notes (load GeoJSON)
    ├→ Player Map (filtered GeoJSON)
    ├→ GM Map (full GeoJSON)
    └→ Session-specific Maps (tagged subsets)

Parallel export:
GeoJSON → KML/KMZ (transpilation)
    ↓
Google Earth (player-facing, curated export)
```

---

## Tag Semantics

Tags control visibility and filtering. Conventions:

**Visibility:**
- `#gm-only` – never shown to players
- `#player-visible` – safe for player maps
- `#secret` – hidden until explicitly revealed

**Session/Campaign:**
- `#session-1`, `#session-2`, etc. – location-specific to session
- `#campaign-arc-desert` – tied to campaign region/arc
- `#epilogue` – post-game locations

**Content:**
- `#faction-[name]` – faction affiliation
- `#trade-route-[name]` – part of named route
- `#natural-feature`, `#settlement`, `#landmark`, etc. – type flags for filtering

**Metadata:**
- `#needs-narrative` – location needs description write-up
- `#incomplete` – coordinates/data missing
- `#conflict-zone` – historically or narratively contested

---

## Workflow: Authoring Locations

1. **GM creates** Location Note in `/world/locations/` with minimal 5-field frontmatter
2. **GM tags** the note (visibility + content tags)
3. **Lore Keeper** monitors `/world/locations/` for new notes
4. **Lore Keeper** generates updated GeoJSON exports (manual or via script)
5. **Map notes** automatically reflect new locations (if using Dataview queries or markerFolder)
6. **Publishing workflow** generates player/GM exports on demand (post-session or manually)

---

## Publishing Workflows

See `PUBLISHING_WORKFLOWS.md` for step-by-step processes:
- Generating GeoJSON from Location Notes
- Creating/updating Leaflet map notes
- Exporting to KML/KMZ for Google Earth
- Filtering by tag for player visibility

---

## Tools & Technologies

- **Obsidian Leaflet Plugin** – renders Leaflet maps inside notes
- **Dataview** – queries Location Notes, generates GeoJSON-ready data
- **Python script** (optional) – batch GeoJSON generation, KML transpilation
- **Location Note Schema** – standardized frontmatter for consistency

---

## Success Metrics

- ✅ Adding a new location requires only creating one markdown file
- ✅ GM can generate player/GM maps without manual duplication
- ✅ Maps stay in sync with Location Notes (no stale data)
- ✅ Publishing a filtered export (for Google Earth) takes <5 minutes
- ✅ Dataview queries surface incomplete or stale locations
- ✅ Cross-linking between Location Notes and narrative docs feels natural

---

## Next Steps

1. Finalize `LOCATION_NOTE_SCHEMA.md` (what fields, examples, templates)
2. Create initial Location Notes (sample cities, routes, natural features)
3. Test Dataview query generation (`DATAVIEW_QUERIES.md`)
4. Set up publishing scripts (`PUBLISHING_WORKFLOWS.md`)
5. Create first Leaflet map notes and verify rendering

---

## Notes & Open Questions

- [ ] Should Location Notes live in `/world/locations/` or `/world/map-locations/`? (consistency with Obsidian structure)
- [ ] Do we want Lore Keeper to auto-generate GeoJSON weekly, or on-demand?
- [ ] Should KML export be a manual process (export → Google Earth) or a scheduled task?
- [ ] For very large GeoJSON files, should we split by region/faction to reduce file bloat?
