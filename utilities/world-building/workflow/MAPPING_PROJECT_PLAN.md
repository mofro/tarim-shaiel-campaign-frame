---
title: Mapping Project Plan
project: TTRPG_Tarim_Shaiel
type: project_plan
status: in_progress
created: 2025-12-07
updated: 2025-12-07
---

# Tarim-Shaiel Mapping Project

## Goal
Create an interactive, Obsidian-native map system for Tarim-Shaiel's Silk Road-based world, using real geographic coordinates and KMZ/Leaflet visualization.

---

## Key Decisions Made (2025-12-07)

### Coordinate System: Real Earth Geography (Option B)
**Decision:** Use real lat/long coordinates from Earth geography as technical foundation
**Rationale:**
- Source geography markdown already contains real coordinates
- Coordinates work immediately with Google Maps, Leaflet, standard tools
- Can overlay fantasy names/styling on real geography
- Much easier than creating custom pixel-based coordinate system
- Players never see "Earth" - we control labels and presentation

**Alternative Considered:** Custom image-based map with fake coordinates (Option A)
**Why Rejected:** Requires creating world map image first, then manually mapping every location to pixel positions - significantly more upfront work

### File Structure
- `regions.json` - Single source of truth containing:
  - Region names with lat/long coordinates
  - Boundary paths (arrays of coordinate pairs)
  - Descriptions, lore, cultural/political details
  - Historical basis and magical elements
- KMZ files generated FROM regions.json
- Interactive maps built on same coordinate foundation

### Technology Stack
- **Leaflet.js** for interactive mapping (Obsidian plugin available)
- **KML/KMZ** for geographic data interchange
- **Markdown + frontmatter** for all lore/documentation (portability)
- **Obsidian** as primary authoring/presentation environment

---

## Implementation Phases

### Phase 1: Data Extraction & Structuring (30 min)
**Status:** Ready to begin
**Tasks:**
1. Parse source geography markdown to extract:
   - All location names with lat/long
   - Path definitions (coordinate sequences for boundaries/routes)
   - Substance/description information
   - Regional groupings
2. Build `regions.json` schema with:
   - name, coordinates, boundary, description
   - historicalBasis, magicalElements, culturalPolitics
   - Any other relevant metadata
3. Generate initial KMZ file(s) from regions.json

**Output:** 
- `/world/data/regions.json` (source of truth)
- `/world/data/hero_heaven.kmz` (generated file)

### Phase 2: Obsidian Integration (45 min)
**Status:** Pending Phase 1
**Tasks:**
1. Configure Obsidian Leaflet plugin
2. Determine base map approach (real geography or custom image)
3. Create initial interactive map view
4. Test coordinate mapping and region display

**Output:**
- Working interactive map in Obsidian
- Documentation of Leaflet configuration

### Phase 3: Lore Development (ongoing)
**Status:** Skeletal framework exists
**Tasks:**
1. Expand each region with:
   - Historical-fantasy merger storytelling
   - Cultural/political dynamics with magic
   - Logical consequences of magical elements
   - "What if" explorations grounded in history
2. Create Obsidian notes per region with standardized frontmatter
3. Link regions to peoples, factions, timeline

**Template Structure:**
```yaml
---
region: [Region Name]
type: [mountain-kingdom/trade-hub/etc]
historicalBasis: "[Real-world analogue]"
magicalElements: ["element1", "element2"]
keyFactions: ["faction1", "faction2"]
campaignStatus: [unexplored/visited/active]
coordinates: {lat: X, lon: Y}
---
```

**Output:**
- `/world/regions/[region-name].md` files
- Rich lore integrated with map system

### Phase 4: Campaign Management System (future)
**Status:** Planning
**Tasks:**
1. Design template architecture:
   - Region, NPC, location, session-note, story-artifact templates
2. Establish separation strategy:
   - `_dm/` - DM working knowledge
   - `narrative/` - Player-facing content
   - `canonical/` - True world state
3. Build frontmatter-driven linking and dataview queries
4. Create player presentation layer

**Output:**
- Comprehensive Obsidian-based campaign management
- Portable, markdown-centric workflow
- Clear DM/player knowledge separation

### Phase 5: Advanced Features (future)
**Potential additions:**
- Session tracking linked to map locations
- NPC relationship graphs
- Timeline visualization
- Player knowledge vs. DM knowledge filtering

---

## Open Questions

### Magic System Definition (CRITICAL)
- [ ] How does magic actually work? (mechanics, energy source, limitations)
- [ ] Who can use it? (bloodlines, training, artifacts, geography?)
- [ ] Environmental impact of magic?
- [ ] Political/military power implications?
- [ ] Economic effects?

### Knowledge Layers
- [ ] What is objective reality vs. common knowledge?
- [ ] What do scholars know vs. common people?
- [ ] How does player background affect knowledge?
- [ ] What are the "hidden truths" to be discovered?

### Historical-Fantasy Integration
- [ ] Which real events happened (with magical twists)?
- [ ] Which are completely replaced?
- [ ] What are the key divergence points?

### Geography Specifics
- [ ] Source geography markdown location?
- [ ] Naming conventions for regions?
- [ ] Level of geographic detail needed?
- [ ] How to handle region boundaries?

---

## Next Immediate Steps
1. Mo shares source geography markdown
2. Parse markdown → extract locations, coordinates, paths
3. Build regions.json schema
4. Generate initial KMZ file
5. Test in Google Maps / begin Leaflet setup

---

## References
- Real-world map sources in INDEX.md (UNESCO, UW Atlas, etc.)
- Historical timeline: `/world/historical_frame.md`
- Peoples structure: `/world/peoples_and_polities.md`
- Architecture: `/ARCHITECTURAL_DECISIONS.md`

**Maintained by:** Lore Keeper  
**Last Update:** 2025-12-07
