---
title: Project Backlog
project: TTRPG_Tarim_Shaiel
type: project_management
status: active
created: 2026-03-17
last_updated: 2026-03-17
---

# Backlog — Deferred & Future Work

Parked work that is not on the critical path for Session 0 or campaign launch. Promote items to `TODO.md → ACTIVE` when they become session priorities.

---

## NEAR-TERM
_Pre-Act 2 design work — not blocking Session 0 but must be resolved before mid-campaign content_

### Divine & Cosmic Factions ⚠️ DESIGN DECISIONS REQUIRED

*Two decisions gating mid-campaign design.*

- [ ] **Decision: What IS the Celestial Court?** (~1 session)
  - The heroes were *sent*, *rewarded*, and *expelled* by something. What is that something?
  - **Option A:** A governing body of divine beings with individual identities and agendas
  - **Option B:** An impersonal cosmic accounting system (Svarga-as-hotel framing from SILK_ROAD_MYTH_ANALYSIS — uncomfortable, mechanistic, nobody's "in charge")
  - **Option C:** The Mythic Ecosystem expressing itself as distributed will — no single authority, just emergent order
  - **Option D:** Something the heroes once understood and have now forgotten — the answer is in their celestial memory
  - **Impact:** Determines whether heroes have a divine patron, a cosmic employer, or a system they were part of and are now locked out of; shapes endgame options
  - Reference: `/world/factions/Index.md` → "Divine & Cosmic Powers" section for full context

- [ ] **Decision: Do the Warrens have intelligence/agenda?** (~30 min — yes/no with implications)
  - R/H/K reframing (tools express Warren allegiance) implies *something* is on the other end
  - **If yes:** Campaign's third act deepens; Warrens become a faction with goals of their own
  - **If no:** Warrens remain infrastructure; allegiance is to a *principle*, not an entity
  - **Hybrid:** Warrens don't think, but something *rides* them — the Held Breath entities may be using the Warren structure as nervous system
  - **Impact:** Gates Warren Intelligence faction file; affects endgame scenarios

- [ ] **Build Divine Factions files** (~1-2 sessions, after decisions above)
  - `celestial-court` — after Celestial Court decision
  - `ancestor-spirits` — can build now; Orc shamanic tradition is established
  - `held-breath` — after Warren Intelligence decision (affects how it's framed)
  - `warren-intelligences` — after Warren Intelligence decision
  - `elder-gods` — speculative placeholder only until prehistory decisions made
  - Reference: `/world/factions/Index.md` → Divine & Cosmic Powers section

**Estimated Effort:** 1-2 sessions for decisions; 1-2 sessions for files

---

### Charm Reference Audit ⏳ DEFERRED
**Decision (2026-03-13):** Charm system removed from active scope. Charm mechanics layer deferred — Daggerheart base system is used for now. No semantic renaming until Vestige/Memory Fragment mechanics are actually designed.

**Cleanup completed (2026-03-17):**
- [x] `templates/tarim-shaiel-templates/character_template.md` — removed `charm_tier` frontmatter field and "Active Charms" section (dead references to unbuilt mechanic)
- [x] `mechanics/character-creation/CHARACTER_CREATION_SEQUENCE.md` — removed "Prepare Charm reveals" checklist items; updated stale Next Steps note

**Deferred — no semantic rename until mechanics are designed:**
- [ ] `mechanics/character-progression/TOOL_EVOLUTION_FRAMEWORK.md` — Charm mechanics layer; leave as-is (aspirational, not active)
- [ ] `mechanics/character-progression/CELESTIAL_DICE_MECHANICS.md` — Charm tier progression; leave as-is (aspirational)
- [ ] `narrative/HERO_IDENTITY.md` — conceptual references; revisit when Vestige design is underway
- [ ] `narrative/STORY_ARC_SYNTHESIS.md` — conceptual references; revisit when Vestige design is underway
- [ ] `.meta/NEXT_SESSION_CONTEXT.md` — 1 trivial mention; low priority

**Also deferred (Charm mechanics layer):**
- [ ] **Design weapon-specific Charms** — deferred with Charm layer; revisit as weapon-specific abilities when active
- [ ] **Charm card format evaluation** — deferred; reference: `archive/charms/CHARM_SYSTEM_ANALYSIS.md` § Future Considerations

**Estimated Effort:** 1 session (when Vestige/ability design begins)

---

### World-Building Expansion

#### Orc Culture (Continued Development)
- [ ] **Detail specific Orc clans** (~1-2 sessions)
  - Create 5-8 named clans with full profiles
  - Clan histories, territories, specializations
  - Current leaders and internal politics
  - Relationships with other clans
  - Reference: `/world/ancestries/orcs.md` for foundation

- [ ] **Create Orc NPC stat blocks** (~1 session)
  - **Vessa Goldweave** (Master Bondkeeper, Golden Chain League)
  - **Thrakmar Ironshaper** (Bladespeaker weapon-master)
  - **Kera Chainkeeper** (Elderly Remembrancer)
  - **Dag the Blade-Seller** (Independent merchant)
  - Full Daggerheart mechanics + roleplay notes

- [ ] **Develop "Breaker's Chain" memorial weapon** (~30 min)
  - Daggerheart stat block
  - Ceremonial vs. combat stats
  - Spiritual significance mechanics
  - Other memorial weapons (mining picks, tools)

- [ ] **Map Orc settlement patterns** (~1 session)
  - Major Orc cities/territories on Silk Road map
  - Merchant League headquarters locations
  - Diplomatic academy locations
  - Settlement by clan/region

- [ ] **Create Orc-specific downtime moves** (~30 min)
  - Weapon-training (martial academies)
  - Diplomatic training (negotiation practice)
  - Clan networking (building trade relationships)
  - Remembrance rituals (cultural reinforcement)

- [ ] **Design Orc martial/diplomatic academy encounters** (~1 session)
  - "The Hundred Stances School" (martial)
  - "The House of Broken Chains" (diplomatic)
  - Location details, NPCs, services, costs
  - Quest hooks and training opportunities

#### Weapons & Equipment
- [ ] **Create legendary weapon variants** (~1-2 sessions)
  - Named versions for 16 Mythic Candidates
  - Unique features/histories
  - Tier 3-4 scaled versions
  - Integration with Tarim-Shaiel lore
  - Reference: `/mechanics/weapons_silk_road.md` for candidates

- [ ] **Develop cultural weapon availability charts** (~1 session)
  - Which weapons common in which regions
  - Merchant availability by city
  - Rarity/cost by location
  - Cultural significance notes

- [ ] **Create weapon-wielding NPC examples** (~1 session)
  - Combat archetypes using different weapons
  - Cultural role examples (Steppe Nomad, Temple Warrior, etc.)
  - Quick-reference stat blocks

#### Other Ancestries (From Brainstorm)
- [ ] **Develop Goblin cultural structure** (~2-3 sessions)
  - Main drives and identity (pragmatism? independence?)
  - Social hierarchy and roles
  - "Goblins deliver" reputation mechanics
  - Free Cities governance
  - Empire-era role (profiteers? collaborators?)
  - Real-world analog (Venetian merchants? Hanseatic League?)
  - Reference: `/narrative/BRAINSTORM_2026-02-13.md`

- [ ] **Develop Halfling cultural structure** (~2-3 sessions)
  - Main drives (mediation? comfort? wanderlust?)
  - Scattered community organization (or lack thereof)
  - Neutral mediator mechanics
  - Empire-era role
  - Real-world analog (Armenian traders? Jewish diaspora?)

- [ ] **Develop Dwarf cultural structure** (~2-3 sessions)
  - Beyond "Chronicle of Ages" - what defines them?
  - Social hierarchy and roles
  - Mountain isolation culture
  - Empire-era role (weapons suppliers? profiteers?)
  - Economic niche beyond craftsmanship

- [ ] **MAJOR DECISION: Elven cosmology** (~2-4 sessions)
  - **Critical Choice:** "Celestial refugees" vs. traditional high elves?
  - If refugees: What did they flee? Why diminishing? Forced return?
  - Integration with Elder Gods, Warrens, Hero Heaven
  - Impact on magic system and campaign
  - This decision cascades through entire setting
  - Reference: `/narrative/BRAINSTORM_2026-02-13.md` for full concept

- [ ] **Develop remaining ancestry structures** (~1-2 sessions each)
  - Drakona (dragon heritage cultural implications)
  - Fauns (pastoral origins → modern identity)
  - Firbolg (gentle giant drives)
  - Giants (scale/perspective culture)
  - Katari (feline/pride structures)
  - Infernis (demon-folk stigma vs reality)

#### Silk Road Mythology & Locations
- [x] **Initial myth research complete** — See `/narrative/SILK_ROAD_MYTH_ANALYSIS.md`
  - Cosmological frameworks: 6 regional systems analyzed
  - Heroic resonances: 8 legend structures mapped to HH themes
  - Creatures catalog: 7 adversary types with encounter design notes
- [ ] **Cross-reference cosmologies with STORY_ARC_SYNTHESIS.md** (~1 session)
  - Goal: each major world region has a *different but compatible* interpretation of the Mythic Ecosystem
  - Candidates mapped; needs formal integration decision
- [ ] **Decide: which cosmological framework do High Elves hold?** (~1 session, unlocks Elven cosmology blocker)
  - Leading candidate: Pangu/Hundun family (world built on sacrifice; afraid to destabilize it)
  - Connects to their cosmological withdrawal per STORY_ARC_SYNTHESIS
- [ ] **Create `WORLD_MYTHOLOGY_FRAMEWORK.md`** (~2-3 sessions)
  - In-world document: which myths exist as oral tradition vs. theology vs. suppressed heresy
  - This is the canon output of SILK_ROAD_MYTH_ANALYSIS research
- [ ] **Assign creatures to regions** (~1 session)
  - Albast → Steppe; Div → Persian-analog; Jiangshi → Eastern Gateway; Rakshasa/Vetala → Subcontinent; Nagas → underground/crossroads
  - Add to WORLD_REGIONS_AND_LOCATIONS.md
- [ ] **Design one Vetala NPC** (~1 session)
  - Recurring figure; tester archetype; inhabits a significant corpse
  - Useful before Session 0 for mystery seeding
- [ ] **Review Jiangshi ↔ Orcish funerary rites** (~30 min)
  - Diaspora/dying-far-from-home intersection
  - Add to `/world/ancestries/orcs.md` if resonant
- [ ] **Identify 3 heroic myths for active NPC oral tradition** (~1 session)
  - Alpamysh (Steppe bards), Rostam/Sohrab (Persian merchant scholars), Arjuna at Kurukshetra (subcontinent philosophers)
  - Add to NPC design notes when created
- [ ] **Create mythology/location master list** (~2-3 sessions)
  - Real Silk Road sites → fantasy versions
  - Religious/spiritual sites (Jerusalem, Mecca, Varanasi, etc.)
  - Legendary locations (Shambhala, Kunlun Mountains, etc.)
  - Natural wonders (Tian Shan, Pamir, rivers)
  - Decision: Direct analogs, inversions, or ancestry homelands?
  - Map to campaign locations (Lich strongholds, Hero Heaven threshold, etc.)
  - Reference: `/narrative/BRAINSTORM_2026-02-13.md` for full site list
- [ ] **Develop regional myth cycles** (~1-2 sessions per region, long-term)
  - One per major region: 3-5 connected stories defining how that region understands heroism, death, cosmic order
  - These become oral tradition NPCs cite, bards perform, temples preach
- [ ] **Map creatures to Daggerheart adversary stat blocks** (~2-3 sessions, long-term)
  - Albast (Social/Stealth), Div (Elite/incomprehensible), Jiangshi (Minion/tragic), Rakshasa (Major NPC adversary), Vetala (NPC/tester)

- [ ] **Update all 37 Location Notes with fantasy names**
  - Use FANTASY_NAMING_GUIDE.md as reference
  - Cross-reference regions.json for proper names
  - Add `fantasy_name`, `era_named`, `cultural_influence`, `historical_names` fields
  - Update schema in LOCATION_NOTE_SCHEMA.md

- [ ] **Create GeoJSON overlays** (after fantasy name updates complete)
  - `regions.geojson` — Fantasy region polygons + labels
  - `features.geojson` — Mountains, deserts, rivers + fantasy names
  - `routes.geojson` — Northern Route (Tian-Khor), Southern Route (Kunlain)
  - Lock field mapping decisions (see GeoJSON System Architecture in TODO.md → BLOCKED)
  - Build Python script (Option A recommended) to auto-generate from Location Notes

- [ ] **Refine Elven dynamics documentation**
  - Highland enclave locations and characteristics
  - Great Wall maintenance — who/what/why
  - Elven-adjacent intermediaries (humans, goblins)
  - Celestial mythology basis (Chinese + Asian cosmology)
  - "Islands to the East" mystery
  - Dwarven secrecy about Far North kingdoms (Arctic region)

- [ ] **Create detailed regional descriptions**
  - Regional history, current politics, cultural dynamics
  - Key power players and factions per region
  - Tensions and conflicts
  - Trade patterns and dependencies

### Documentation & Infrastructure

- [ ] **Frontmatter schema redesign for DataView compatibility** (~1 session) ⚠️ ARCHITECTURAL
  - **Problem:** At least 3 competing frontmatter schemas in active use; visibility handled 4 different ways (`visibility:` field, `is_private:` boolean, `classification:` field, `[player-visible]` tag); `type:` conflates domain + doc_type + content_type into one overloaded field
  - **Goal:** Single agreed schema that enables Obsidian DataView queries across all files
  - **Proposed schema:** Split `type` into `domain:` + `doc_type:` + `content_type:`; consolidate all visibility signals into single `visibility:` field; standardize `tags:` for cross-cutting concerns (analog-X, region-X, archetype-X, campaign-arc-X)
  - **Proof-of-concept:** `world/historical-parallels.md` uses proposed schema — validate it first
  - **Scope:** Retrofit across all active (non-archive) files with frontmatter; update `metadata_template.md` and `CLAUDE.md` schema definition
  - **DataView experiments already exist:** `templates/maps/experiments/test_dataview.md`, `templates/experiments/character_template_DATAVIEW.md`
  - **Related:** Glossary fragmentation (visibility-as-file vs. visibility-as-tag is the same problem); `world/locations/` files already use a richer schema worth examining as a base
  - Reference: 2026-03-22 session discussion on schema fragmentation

- [ ] **Fix `/narrative/lore/liberation_aftermath.md`** (~2-3 sessions)
  - **CRITICAL:** Currently has wrong 200-year timeline throughout
  - Needs complete rewrite to align with 1,000-year timeline
  - Reference `/world/content/HISTORICAL_TIMELINE.md` Era 1-4
  - Expand with Orc economic rise (Era 2-3 "Trading Centuries")
  - Add "From Warriors to Traders" development arc
  - Show how Orcs became indispensable to Silk Road economy
  - Cross-reference with `/world/ancestries/orcs.md`

- [x] **Create Factions index** — `/world/factions/Index.md` ✅ 2026-03-10
  - 12 present-day factions + 1 historical + 2 individuals-as-factions catalogued
  - Canonical wikilink names established for all factions
  - Template created: `templates/world-building/_TEMPLATE_faction.md`
- [ ] **Create individual faction files** (~2-3 sessions) — use `_TEMPLATE_faction.md`
  - See `/world/factions/Index.md` → "Faction File Build Order" for prioritized list
  - **Priority 1 (very-high weight):** `elven-highland-enclaves`, `lich-cadre`, `the-wizard`, `chain-breakers-order`, `scholars-remnant`, `celestial-court`
  - **Priority 2 (high weight):** `orc-confederation-samarkand`, `eastern-gateway-council`, `merchant-guilds`, `eastern-imperial-dominion`
  - **Priority 3 (medium weight):** remaining present-day factions
  - Reference: `/world/factions/Index.md` for canonical names + relationship data

- [ ] **Define the Original Human Empire** (~1 session) — high priority historical faction
  - Assign fantasy name (use FANTASY_NAMING_GUIDE.md)
  - Determine ruling structure: dynasty? priestly caste? military aristocracy?
  - Establish origin of binding magic knowledge — did the Wizard predate the Empire, rise within it, or create it?
  - Define the empire's cosmological relationship — did they *know* what they were tapping with binding magic, or was it pragmatic exploitation without understanding?
  - Build individual file using `_TEMPLATE_faction.md`
  - Reference: `/world/content/HISTORICAL_TIMELINE.md` Era 0 for source material
- [ ] **Expand factions with narrative depth** (~2-3 sessions, after individual files created)
  - Merchant guilds (per region, names, specializations)
  - Orc confederations (post-stabilization structures, leaders, territories)
  - Dwarven merchant-states (Venetian-style tolls, monopolies)
  - Human city authorities (remnant imperial vs. new power)
  - Religious organizations and influence

- [x] **Create Events index** — `/world/events/Index.md` ✅ 2026-03-10
  - 11 historical events in causal chain (Era 0–5) + 2 anticipated future events
  - Template created: `templates/world-building/_TEMPLATE_event.md`
- [ ] **Create individual event files** (~1 session) — use `_TEMPLATE_event.md`
  - 11 events: The Enslavement, Liberation, Military Victory, Sacrifice, Ascension, Scattering, Wizard's Retreat, Vanishing of Khorashar, Scholar's Purge, The Expulsion/Gaes, Lich-Legion Assembly
  - Reference: `/world/events/Index.md` for canonical names + causal chain data

- [x] **Create Concepts index** — `/world/concepts/Index.md` ✅ 2026-03-10
  - 13 concepts across cosmological / magical mechanisms / named forces layers
  - Template created: `templates/world-building/_TEMPLATE_concept.md`
- [ ] **Create individual concept files** (~1 session) — use `_TEMPLATE_concept.md`
  - 13 concepts: Mythic Ecosystem, Sleeping Entity/Held Breath, Warrens & Holds, Celestial Peak, The Threshold, Binding Magic, The Gaes, Necromantic Energy, The Great Wall, Celestial Dice, The Lich-Legion, The Heroes, The Liberation Charge
  - Reference: `/world/concepts/Index.md` for canonical names

- [ ] **Create region files** (~1-2 sessions) — use `_TEMPLATE_region.md`
  - 6 regions: Skamarketh (Samarkand-analog), Tarim Basin, Eastern Gateway, Mountain Passes, The Steppe, Elven Highlands
  - Populate Distinctions, GM Principles, faction presence, historical context per region

- [ ] **Canonicalize existing location files with wikilinks** (~1 session)
  - 22 existing `/world/locations/` files use free-text faction names
  - Update `factions:` fields to canonical wikilinks from `/world/factions/Index.md`
  - Add `parent_region:` links once region files are created

- [ ] **Create Trade Routes documentation** (TRADE_ROUTES.md)
  - Northern Route (Tian-Khor Route): waypoints, dangers, seasonal considerations
  - Southern Route (Kunlain Route): waypoints, dangers, seasonal considerations
  - Caravan types, travel times, typical goods

- [ ] **Create session-specific maps**
  - Player-facing map (filter to `player-visible` locations only)
  - GM-only map (all locations including `gm-only` and `secret`)
  - Episode-specific maps (filter by tags like `campaign-arc-desert`)

---

## MEDIUM-TERM
_After campaign begins — informed by actual play_

### Campaign Mechanics & Narrative Detail

- [ ] **Define ghost communication mechanics**
  - How: Dreams, whispers, visions, fragmented messages
  - Knowledge: What does ghost know/understand vs. what's unclear
  - State: Trapped, guided by others, or genuinely free
  - Interpretation: How heroes misunderstand ambiguous communication
  - Mechanical expression: When/how ghost intervenes

- [ ] **Explicit unfinished charge definition**
  - What specifically were heroes supposed to do about the Wizard?
  - When/how was charge conveyed to them at Celestial Peak?
  - Why didn't they recognize it as ongoing duty?
  - What are consequences of failing to complete charge?
  - How does completing charge relate to returning to Hero Heaven?

- [ ] **Manufactured doubt system design**
  - Create 8-12 specific NPCs who plant different doubts
  - Design contradictory information encounters per region
  - Build "suspicious witness" moments (frame potential traitors)
  - Create ambiguous evidence players must interpret
  - Tie doubt to archetype vulnerabilities

- [ ] **Develop post-liberation Orcish politics**
  - Confederation structures (names, leaders, territories)
  - Internal conflicts (traditionalists vs. integrationists)
  - External relations (with humans, dwarves, elves)
  - Player interaction opportunities (quests, negotiations, trade)

- [ ] **Create merchant house networks**
  - 6-8 major trading houses with names, specializations, allegiances
  - House hierarchies and succession politics
  - Rivalries and alliances between houses
  - Political influence and dependencies on regional powers
  - Player economic gameplay opportunities

### Character Development Systems

- [ ] **Expand character archetype documentation**
  - How each archetype relates to expulsion narrative
  - Mechanical benefits and drawbacks per archetype
  - Character creation walkthrough for exiled heroes
  - Example character concepts per archetype

- [ ] **Create player-facing character creation guide**
  - Step-by-step creation process (once Campaign Frame locked)
  - Archetype selection with psychological patterns
  - Relationship to Celestial Peak and lost reward
  - Tool assignment and initial state
  - How fall shapes motivation and goals

- [ ] **Document character advancement system**
  - How do heroes regain/restore aspects of reward?
  - Experience triggers (narrative vs. mechanical)
  - Tool progression triggers
  - Consequence system for trust and unity choices
  - Session-based advancement pacing

---

## FUTURE
_Aspirational — not needed for launch_

### Advanced Mapping

- [ ] **Create custom fantasy map image** (commission or DIY)
  - Replace real-world topographic base with fantasy aesthetic
  - Retain geographic accuracy underneath
  - Toggle between fantasy and topographic versions

- [ ] **Implement image map mode**
  - Upload custom map image to Obsidian
  - Set bounds to match coordinates
  - Layer Location Note markers over image

- [ ] **Add marker zoom breakpoints**
  - Major cities visible at zoom 3+
  - Minor waypoints visible at zoom 6+
  - Prevent map clutter at low zoom levels

- [ ] **Route visualization overlays**
  - GeoJSON LineString features for trade routes
  - Color-coded by season or danger level
  - Interactive route information (hover/click)

- [ ] **Test GeoJSON export to Google Earth** (KML format)
- [ ] **Create publishing workflow** for session-specific exports

### World-Building Depth

- [ ] **Timeline strengthening**
  - Deepen historical narrative across all eras
  - Add more granular event sequences
  - Enrich cause-and-effect chains between eras

- [ ] **Example events fleshing**
  - Expand Shared_Memory_Events.md with additional sensory detail
  - Add variant interpretations per archetype perspective
  - Deepen emotional resonance of canonical moments

- [ ] **Comparative cultural history**
  - Weave parallel development narratives (Orcish liberation ↔ human recovery ↔ Dwarven isolation)
  - Show how different ancestries experienced the same historical moments differently
  - Build depth through cultural contrast and intersection

- [ ] **Detailed mythical pantheons**
  - What do the mythical pantheons look like?
  - Do they drive PLOT?
  - What is the overall interaction with the mundane?
  - What impacts to characters?

- [ ] **Detailed magical system paradigms** for magical powers/archetypes
  - How does the magic system express itself in the lore?
  - Does it drive PLOT?

- [ ] **Possible alternate calendar descriptions**
  - Is it simple Gregorian, or something more "alternative earth" appropriate?
  - Regional naming conventions
  - Significant seasonal or religious/mystical events

- [ ] **NPC network development**
  - Major NPCs by region (names, motivations, secrets)
  - Interconnections and conflicts
  - Hidden agendas and faction allegiances
  - Relationship maps

- [ ] **Encounter tables by region/location type**
  - Random travel encounters (by terrain, season, route)
  - Social encounters in cities (by district, faction)
  - Combat encounters (by threat level, environment)

- [ ] **Historical conflicts documentation**
  - Pre-Empire era conflicts and alliances
  - Empire era oppression and resistance movements
  - Chaos period raiding patterns and atrocities
  - Stabilization era peace-building efforts

- [ ] **Economic simulation design**
  - Trade flow maps (what goods move where and why)
  - Price fluctuations by region and season
  - Supply/demand dynamics
  - Impact of politics on trade (tolls, embargoes, monopolies)

### System Development

- [ ] **TTRPG encounter resolution mechanics** (detail conflict structure)
- [ ] **Session structure templates** (Episodes 1-N pacing and format)
- [ ] **House rules documentation** (table-specific rulings)
- [ ] **Character death/resurrection mechanics** (fallen hero context)

### Team Intelligence Framework

- [ ] **Cartographer persona** (if needed for specialized geospatial work)
- [ ] **Mythweaver-Lore Keeper collaboration patterns** documentation
- [ ] **Context detection system** for persona activation
- [ ] **Update persona schema** across all domains

---

## BRAINSTORM
_Captured 2026-02-13 in `/narrative/BRAINSTORM_2026-02-13.md`_

Open questions to develop when inspiration strikes. These may never need full answers — intentional mysteries can serve the campaign better than explanations.

### Prehistoric Civilizations & Pre-Imperial Constructs

*Highly speculative — the cosmological architecture implies this territory exists, but no design decisions have been made.*

- [ ] **Who built the Warrens?** — The infrastructure predates the Empire; something created it
- [ ] **Who built the Great Wall?** — Elves maintain it but may not have built it; its original purpose may differ from its current function
- [ ] **Where did Binding Magic come from?** — The Human Empire weaponized it; someone understood it first
- [ ] **What are the Elder Gods?** — Relationship to Warrens, Held Breath, and Celestial Court entirely unknown; may be the Held Breath's original architects, the beings who created the Mythic Ecosystem, or something else entirely
- [ ] **Were there pre-Imperial civilizations at meaningful scale?**
- [ ] **Is "prehistoric" the right frame, or is this cosmological rather than historical?** — The Elder Civilization may not be *older* so much as *other* — operating at a different ontological layer

### Ancestry Structures & Drives
- [ ] What are Goblins' main drives? Halflings? Elves? Dwarves?
- [ ] How do we create similar depth to Orcs for other ancestries?
- [ ] Social hierarchies, economic roles, cultural identities for each

### Real-World Analogs & Stereotype Reversals
- **Reference doc:** `world/historical-parallels.md` (created 2026-03-22) — full analog map against 1453 CE; use as substrate when building any of the below
- [ ] Orcs = Sogdian merchants (cosmopolitan traders) ✅ done; **also** Mamluks (slave-warrior ruling class, sacred site guardians) — see historical-parallels.md
- [ ] Goblins = Venetian/Genoese republics?
- [ ] Halflings = Armenian/Jewish diaspora traders?
- [ ] Dwarves = Byzantine scholars? Islamic Golden Age?
- [ ] Elves = Ming dynasty (deliberate withdrawal after expansionist moment; Great Wall as policy not tragedy) — see historical-parallels.md; `elven-highland-enclaves` confirmed canon faction
- [ ] Which real Silk Road peoples are "missing" that ancestries could represent?
- [ ] Arab dispersed-network model (influence without territory; Sufi mysticism substrate) — no faction assigned yet; candidate for mystic/merchant network

### Empire-Era Roles
- [ ] Which ancestries profited from Orc enslavement?
- [ ] Did Dwarves sell the chains? Goblins profit as middlemen?
- [ ] Were Elves complicit, opposed, or indifferent?
- [ ] How do ancestries reckon with this history 1,000 years later?

### Magic & Elven History
- [ ] How does magic work mechanically in this world?
- [ ] Who could do magic in the Empire era?
- [ ] Has magic changed over 1,000 years?
- [ ] Do Elves understand magic differently than other ancestries?

### Elven Cosmology: "Celestial Refugees" Concept ⚠️ MAJOR DECISION
- [ ] Are Elves refugees from a celestial realm? Exiled? Fleeing catastrophe?
- [ ] Is "diminishing" an involuntary return to their origin?
- [ ] Is their long lifespan a curse/exile sentence, not a blessing?
- [ ] How does this integrate with Elder Gods, Warrens, and Hero Heaven?
- [ ] Do Elves recognize Hero Heaven? Fear it? "You went where we cannot return"?
- **Decision Required Before:** Elven cultural documentation, magic system details, campaign cosmology

### Silk Road Mythology & Key Locations
- [ ] **Real sites to map to fantasy versions:**
  - Religious: Jerusalem, Mecca, Varanasi, Bodh Gaya, Mount Kailash, Lhasa
  - Legendary: Shambhala, Kunlun Mountains, Taklamakan Desert
  - Cities: Samarkand, Bukhara, Kashgar, Dunhuang
  - Natural: Tian Shan, Pamir Mountains, Ganges, Yellow River
  - Options: Direct analogs? Mythological inversions? Ancestry homelands? Campaign locations?
  - Where is Hero Heaven threshold? Which Lich strongholds where?

**See `/narrative/BRAINSTORM_2026-02-13.md` for full exploration of these concepts.**
