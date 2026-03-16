---
title: Project TODO & Status
project: TTRPG_Tarim_Shaiel
type: project_management
status: active
created: 2025-12-14
last_updated: 2026-03-17
banner: images/places/248420.jpg
banner-x: 51
banner-y: 37
---

# TODO & Project Status


## PROJECT HEALTH

**Last Updated:** 2026-03-17
**Critical Path:** Resolve cosmological architecture → Complete Session 0 scenarios → Resolve Campaign Frame → Playtest

**Quick Summary:**
- [x] **Core complete:** Campaign narrative, world geography, fantasy naming, charm architecture, **Orc cultural framework**, **Silk Road weapons**, **Cosmological architecture (7 of 8 decisions locked 2026-03-08)**, **World entity infrastructure (factions/events/concepts indexes + all location templates 2026-03-10)**, **Preliminary world diagrams (2026-03-13)**, **HTML publishing pipeline + Netlify deployment (2026-03-15)**, **Visibility gating + Obsidian Shell Commands integration (2026-03-17)**
- 🔄 **Active work:** Session 0 scenarios (3/6 done), STORY_ARC_SYNTHESIS.md needs update to reflect locked decisions, individual entity files to be created from indexes
- ⚠️ **Blockers:** liberation_aftermath.md rewrite (Warren disturbance framing — see DECISION_LOG 2026-03-08), Wizard's motivation/awareness (deferred), charm reference cleanup (7 active docs still reference old system)
- 🆕 **Infrastructure complete (2026-03-15–17):** LegendKeeper dual-path pipeline, HTML generator (timeline + myth), Calendar Era labels (HJ/HB), batch runner + auto-generated index, Netlify deploy, GitHub Actions, visibility gating (fails-closed `--public`), Obsidian Shell Commands setup
- 🔒 **PR #1 open** on `claude/upbeat-bartik` — 8 commits, pending merge to main
- 🐛 **Dashboard fix (2026-03-13):** SESSION LOG + COMPLETED sections now excluded from domain counting; world 58%→34%, readiness 51%→45% (inflation corrected, not regression)
- 🗃️ **Charm system removed (2026-03-13):** Archived to `archive/charms/`; Vestiges/Memory Fragments/The Wrongness carry mechanical identity; 7-doc reference cleanup still pending

---


## PUBLISHING INFRASTRUCTURE ✅ COMPLETE (2026-03-15–17)
_Pipeline from Obsidian vault → styled HTML → Netlify public site. All components live._

### HTML Pipeline & Netlify Deployment ✅
- [x] `utilities/legendkeeper-pipeline/generate_world_html.py` — Obsidian MD → styled HTML (Campaign Frame aesthetic); supports `type: timeline` and `type: myth|lore`
- [x] `utilities/legendkeeper-pipeline/generate_all_world_html.py` — batch runner; discovers all pipeline sources; writes `docs/index.html`; `--public` flag (fails-closed visibility gating)
- [x] `utilities/legendkeeper-pipeline/SOURCE_FORMAT.md` — canonical source format spec (frontmatter, event syntax, Calendar Eras, secret patterns)
- [x] `netlify.toml` — Netlify build command; runs all three generators with `--public`
- [x] `.github/workflows/generate-html.yml` — GitHub Actions; triggers on push to main; regenerates docs/; commits back with `[skip ci]`
- [x] `docs/index.html` — auto-generated index listing core docs + world docs
- [x] Calendar Eras section (`## Calendar Eras`) — date labels use LK Time System era definitions (HJ/HB), not swimlane auto-abbreviations
- [x] Image support — timeline event cards can include `image:` URL field
- [x] LK reverse converter (`from_lk_json.py`) + canonical Nianhao timeline source

### Visibility Gating ✅ (fails-closed)
- [x] `--public` flag on both generators: **only `visibility: public` passes**; missing, `gm_secrets`, or any other value → skipped
- [x] Netlify and GitHub Actions both run with `--public` — GM-only documents never appear in public deploy
- [x] Local runs (no flag) generate everything including `gm_secrets` docs for full GM preview
- [x] Default visibility changed from `'public'` to `'gm_secrets'` — untagged docs fail closed
- [x] Stale `docs/nianhao-the-divine-arc.html` removed from repo (was committed before gating existed)
- [x] `--open` flag: opens generated HTML in browser after writing
- [x] Silent-skip for non-pipeline files (exit 0) — Shell Commands on-save event fires without noise

### Obsidian Shell Commands Integration ✅ (setup doc written, plugin config manual)
- [x] `utilities/shell-commands-config.md` — setup reference for 3 Shell Commands plugin commands
- [ ] **Install Shell Commands plugin** in Obsidian (Settings → Community Plugins → "Shell Commands")
- [ ] **Configure Command 1: "Regenerate HTML Preview"** — on-save event (`world/` + `narrative/` folder filter); opens browser
- [ ] **Configure Command 2: "Full Pipeline (Local)"** — palette + hotkey (`Cmd+Shift+B`); runs all generators; opens `docs/index.html`
- [ ] **Configure Command 3: "Open Local Preview"** — palette convenience command

### Sub-document Secret Patterns ✅ (documented, not yet in use)
- [x] **Pattern A (`%%...%%`):** inline secrets stripped from all HTML output (already working)
- [x] **Pattern B (`-gm` companion file):** `<stem>-gm.md` with `visibility: gm_secrets`; enables Obsidian transclusion via block IDs; excluded from public deploy automatically
- [ ] **Apply patterns** as myth/lore documents are authored — no retroactive file changes needed

### Outstanding Pipeline Work
- [ ] **Charm reference cleanup** — 7 active docs still mention Charm system; surgical removal needed (Priority 1 from 2026-03-13)
- [ ] **Merge PR #1** (`claude/upbeat-bartik` → `main`) — 8 commits, all pipeline + visibility work
- [ ] **Connect Netlify site** — netlify.toml is in repo; site needs to be linked at netlify.com (one-time setup)

---


## ACTIVE
_Critical path items — must be completed for campaign launch_

### 0. Cosmological Architecture Decisions ✅ 7/8 COMPLETE
**Session:** 2026-03-08
**Reference:** `/narrative/STORY_ARC_SYNTHESIS.md` ⚠️ needs update to reflect locked decisions

**Remaining:** Wizard's motivation/awareness (Decision 4) — deferred by design, requires dedicated narrative session.

#### Critical Decisions (Must resolve before anything below becomes canon)

- [x] **Define the Mythic Ecosystem** — Confirmed: multi-dimensional biome. Warrens as distinct dimensional spaces. Power draws power. Affinities not interchangeable. Threshold = porous container. See DECISION_LOG.md 2026-03-08.
- [x] **Define the Sleeping Entity** — Confirmed: multiple liminal consciousnesses at celestial scale, held in suspension by cosmological equilibrium ("Held Breath"). Not a singular geological force. See DECISION_LOG.md 2026-03-08.
- [x] **Decide the Entity's Nature** — Confirmed: dormant liminal consciousnesses, not purely mindless, not negotiable (not awake enough). Horror is their weight. Threat is awakening, not containment breach. See DECISION_LOG.md 2026-03-08.
- [ ] **Decide the Wizard's Awareness** — Option A: tragic ignorance (doesn't know about entity), Option B: tragic hubris (knows, thinks he can manage it), Option C: cosmic manipulation (entity subtly influenced his 1,000-year obsession). Options are combinable (B+C recommended).
- [x] **Decide: Do Heroes' Charms Strain the Ecosystem?** — Confirmed: yes, scaled by tier, expressed as beacon not immediate cost. R/H/K reframed as Warren allegiance. Tools = endgame cosmological interface. See DECISION_LOG.md 2026-03-08.
- [x] **Define the Liberation's Ecosystem Side Effects** — Confirmed: NOT ecosystem damage. Liberation = massive beacon event → Warren ripples → drew attention of entities with agendas. Incomplete charge = reckon with what was woken/whose plans were crossed. Player doubt drama intact. See DECISION_LOG.md 2026-03-08.
- [x] **Define Threshold as Ecosystem Node** — Confirmed: Hero Heaven adjacent to (not a) Warren. Threshold = concentrated ecosystem wiring. Breach = immediate, unmistakable consequences (not slow accumulation). See DECISION_LOG.md 2026-03-08.
- [x] **Define Three-Layer Revelation Structure** — Confirmed: Layer 1 (stop Wizard) → Layer 2 (breach causes immediate cosmological break) → Layer 3 (reckon with liberation disturbance + Held Breath). Tools are the endgame interface. See DECISION_LOG.md 2026-03-08.

#### Stakeholder Knowledge Distribution (Must resolve for mid-campaign planning)

- [ ] **Map High Elf awareness** — They understand the ecosystem, withdrew because of cosmological fear, possess preventive (not restorative) knowledge. This answers the Elven cosmology question: not "celestial refugees" but "cosmologically literate beings who retreated from a fault line."
- [ ] **Map Dwarven archivist awareness** — Chronicle of Ages contains empirical evidence of ecosystem degradation (disappearance patterns, magical anomaly data). They have data but need theory.
- [ ] **Map Orcish shamanic degradation** — Ancestor communication becoming unreliable as ecosystem symptom. Ancient epic songs contain literal descriptions of the entity. Liberation side effects woven into their traditions.
- [ ] **Map human scholar suppression** — Scholar's Purge (~1175 CE) was Wizard eliminating researchers. Surviving scholars are scattered, hunted, hold practical fragments.
- [ ] **Map Goblin/Halfling observational network** — Trade disruptions, dead zones, charm failures = best continent-wide empirical dataset of ecosystem degradation. They don't know what their data means.
- [ ] **Design the information synthesis puzzle** — Heroes as the only beings who can assemble distributed knowledge from all cultures. This is a core campaign mechanic, not just plot.

#### Items This Unblocks (Existing TODOs That Get Answered)

| **Existing TODO/Blocker** | **How Cosmological Architecture Resolves It** |
|---|---|
| Elven cosmology decision | High Elf withdrawal = cosmological retreat from the Held Breath fault line (not celestial refugees) ✅ |
| liberation_aftermath.md rewrite | Rewrite: Warren disturbance + interested parties framing (NOT ecosystem damage) — timeline fix still needed ✅ |
| Wizard's exact goal (WIZARD_AND_LICH_CADRE.md TBD) | Deferred — requires dedicated narrative session 🔄 |
| Ghost communication mechanics | Ghost as ecosystem/Warren agent; gaes = cosmic immune response ✅ |
| Explicit unfinished charge definition | "Reckon with what was woken and whose plans were crossed" — not ecosystem repair ✅ |
| Endgame scenarios (HERO_HEAVEN_THRESHOLD.md) | Three-layer revelation structure locked; Threshold breach = immediate consequences ✅ |
| What makes Hero Heaven valuable to Wizard | Adjacent to Warren infrastructure; Threshold = concentrated ecosystem wiring ✅ |
| Consequences of Wizard succeeding | Threshold breach = immediate, unmistakable cosmological break + Held Breath stirs ✅ |

---

### 2. Campaign Frame Integration 🔄 IN PROGRESS
**File:** `templates/tarim-shaiel-campaign-frame-v2.md`
**Blocker resolved:** Class/archetype mapping — v2 sidesteps prescriptive mapping via "approach" framing; all Daggerheart classes available; character creation guide deferred to Session Zero.

#### Player-Facing Sections — COMPLETE
- [x] Concept / At a Glance
- [x] The Pitch
- [x] Tone & Feel / Themes / Touchstones
- [x] Overview (player-facing, ~1 page)
- [x] Heritage & Classes ("approach" framing; all classes open)
- [x] Player Principles (5 written)
- [x] GM Principles (6 written)
- [x] Session Zero Questions (7 questions + Lines & Veils)

#### GM-Facing Sections — STUBS ONLY (writing required)
- [ ] **Distinctions** (~1-2 sessions) — draw from existing locked material:
  - How the Warrens, Holds, and unreliable magic actually work (cosmological architecture)
  - The Heroic Age, the thousand-year gap, and what the characters actually are
  - The empire and its successor factions — the full picture (not player-facing)
  - The antagonist, the Lich-Legion, the Celestial Peak, the Fallen Companion, the Gaes
- [ ] **Inciting Incident** (~1 session) — creative writing task, no direct source exists yet:
  - The specific awakening circumstances: location, first witness, opening situation
  - Three-element structure: situation / objective / hooks keyed to character approaches
  - Must preserve secrets while making the opening scene executable
- [ ] **Custom Mechanics: Vestiges / Memory Fragments / The Wrongness** (~1 session) — translate locked decisions into campaign frame voice:
  - Vestiges = Tools; R-H-K (Resist/Hunger/Know) behavioral framework
  - Memory Fragments = Know behavior as a subsystem; how fragments surface and what they cost
  - The Wrongness = ecosystem strain / beacon effect / Warren inversion as players experience it
- [ ] **Campaign Map** (~1 session) — player-facing version of existing geographic framework:
  - Eight regions named and placed; post-imperial political shape
  - Space left for table co-creation contributions

**Estimated remaining effort:** 4-5 sessions

### 3. Session 0 Completion 🔄 IN PROGRESS
**Status:** 3 of 6 awakening scenarios complete

**Remaining Work:**
- [ ] **Breaker Awakening Scenario** (~1 session)
  - Finish segment structure
  - Erikson-inspired prose
  - Tool interaction (offering/sacrifice mechanics)

- [ ] **Sacrificer Awakening Scenario** (~1 session)
  - 8-segment structure
  - Erikson-inspired prose
  - Tool interaction (offering/sacrifice mechanics)
  - Secret snippet trigger moment

- [ ] **Visionary Awakening Scenario** (~1 session)
  - 8-segment structure
  - Tarot deck as mystical tool
  - Foresight/path-showing mechanics
  - Secret snippet trigger moment

- [ ] **Bridge Awakening Scenario** (~1 session)
  - 8-segment structure
  - Unity/influence mechanics
  - Voice/conviction tool
  - Secret snippet trigger moment

- [ ] **Sentinel awakening** — NEW (~1 session) — stub in `Session_0_Awakening_Design_Notes.md`
- [ ] **Keeper awakening** — NEW (~1 session) — stub in `Session_0_Awakening_Design_Notes.md`
- [ ] **Trickster awakening** — NEW (~1 session) — stub in `Session_0_Awakening_Design_Notes.md`
- [ ] **Crafter awakening** — NEW (~1 session) — stub in `Session_0_Awakening_Design_Notes.md`
- [ ] **Healer awakening** — NEW (~1 session) — stub in `Session_0_Awakening_Design_Notes.md`

- [ ] **Populate Shared_Memory_Events.md** (~1-2 sessions)
  - 5 thematic events (framework defined)
  - Event 1: The Warrior's Choice (method of engagement)
  - Event 2: The Question of Sight (knowledge vs. trust vs. truth)
  - Event 3: The Weight of Choice (action vs. consequence)
  - Event 4: Aspirations Undone (victory's unintended consequences)
  - Event 5: The Wizard's Shadow (false certainty about threat)
  - Each event: 400-600 word sensory scene + canonical truths revealed

- [ ] **Write Actual Secret Snippets** (~1 session)
  - 6 archetype-specific snippets
  - Sensory + emotional register (not explanatory)
  - Tied to awakening scenario trigger moments
  - Creates player-to-character investment

- [ ] **Create Session_0_GM_NOTES.md** (~1-2 sessions)
  - Detailed execution guide
  - Atmospheric details, NPC quick-refs, pacing cues
  - Scenario-specific GM guidance for all six awakenings
  - Convergence orchestration techniques

- [ ] **Finalize PLAYER_PITCH_AND_PRINCIPLES.md** (~1 session)
  - Both versions: transparent (GM reference) + less-transparent (player-facing)
  - All six archetype descriptions
  - Player principles (4-6 guidelines)

**Total Estimated:** 7-10 sessions

---


## BLOCKED

### Critical Blockers

1. ~~**Campaign Frame: Class/archetype mapping**~~ ✅ RESOLVED 2026-03-13
   - v2 document uses "approach" framing; all Daggerheart classes open; no prescriptive mapping needed

2. **GeoJSON Field Mapping** 🟡
   - **Question:** Which Location Note fields transfer to GeoJSON descriptions?
   - **Impact:** Blocks GeoJSON automation, Python script creation
   - **Decisions Needed:**
     - Which fields: `resources`, `factions`, `elevation`, `narrative_weight`?
     - Description building strategy (combine how?)
     - Wikilink format: `[Full details: [[location-name]]]`?
     - Marker mapping: Location Note `type` → `marker-symbol` auto-mapping?
     - Single source of truth: manual trigger or auto-regenerate?
     - Version control: git, Obsidian versioning, or both?
     - Validation checks: coordinates present, no duplicates, valid JSON?
   - **Required Before:** Can build Python script and generate overlays

### Secondary Decisions

3. - [/] **Ancestries for Silk Road Setting** 🟡
   - **Question:** Which Daggerheart ancestries fit? Custom ancestries needed?
   - **Confirmed Fit:** Humans, Orcs, Dwarves, Elves, Halflings, Goblins
   - **Decision Needed:** Use standard as-is, reflavor with Silk Road context, or create custom?
   - **Required Before:** Heritage & Classes section of Campaign Frame

4. - [/] **Campaign Frame Complexity Rating** 🟡
   - **Question:** Rating 3 or 4 on Daggerheart complexity scale?
   - **Factors:** Charm system + tool progression + R/H/K framework + archetype mechanics
   - **Recommendation:** 3-4 (significant custom mechanics, streamlined presentation)
   - **Required Before:** Campaign Frame header

5. - [x] **Cartography System Ownership** 🟢
   - **Question:** Formal Cartographer persona or lightweight workflow docs?
   - **Impact:** Minimal — affects who "owns" GeoJSON generation and map updates
   - **Options:** New persona, Lore Keeper extension, or user-triggered scripts
   - **Can Defer:** Not blocking immediate work

---


## NEAR-TERM

### Divine & Cosmic Factions ⚠️ DESIGN DECISIONS REQUIRED

*Two decisions gating mid-campaign design — not blocking Session 0 but must be resolved before Act 2 content.*

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

### Charm Reference Audit ⏳ DEFERRED — next session
**Decision (2026-03-13):** Charm system removed from active scope. Vestiges/Memory Fragments/The Wrongness (Tools + R-H-K) carry the campaign's mechanical identity. Charm infrastructure archived to `archive/charms/`.

**Remaining:** Light reference cleanup in 7 active docs — no rewrites, mostly removing passing mentions or updating to Vestiges language where needed:
- [ ] `mechanics/character-progression/TOOL_EVOLUTION_FRAMEWORK.md` (12 mentions)
- [ ] `mechanics/character-progression/CELESTIAL_DICE_MECHANICS.md` (8 mentions)
- [ ] `narrative/HERO_IDENTITY.md` (8 mentions)
- [ ] `narrative/STORY_ARC_SYNTHESIS.md` (6 mentions)
- [ ] `mechanics/character-creation/CHARACTER_CREATION_SEQUENCE.md` (3 mentions)
- [ ] `templates/tarim-shaiel-templates/character_template.md` (3 mentions)
- [ ] `.meta/NEXT_SESSION_CONTEXT.md` (1 mention — trivial)

**Estimated Effort:** 1 session

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

- [ ] **Design weapon-specific Charms** (~2-3 sessions)
  - Synergize with R/H/K system
  - Weapon mastery Charm trees
  - Mythic weapon awakening mechanics
  - Integration with Tool progression

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

#### Silk Road Mythology & Locations (From Brainstorm)
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
  - Lock field mapping decisions (see GeoJSON System Architecture below)
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
  - Starting Charms selection
  - How fall shapes motivation and goals

- [ ] **Document character advancement system**
  - How do heroes regain/restore aspects of reward?
  - Experience triggers (narrative vs. mechanical)
  - Charm learning and recovery
  - Tool progression triggers
  - Consequence system for trust and unity choices
  - Session-based advancement pacing

---


## FUTURE

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

### Charm System Explorations

- [ ] **Charm card format evaluation**
  - Exploratory phase — decide on Daggerheart card tool viability before committing
  - Evaluate available tools (see editorial note in Campaign Frame section)
  - Determine if native card formatting is worth implementation overhead
  - Reference: `/mechanics/character-progression/charms/CHARM_SYSTEM_ANALYSIS.md` § Future Considerations

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
  - What is the overall interaction with the mundane
  - What impacts to characters?

- [ ] **Detailed magical system paradigms** for magical powers/archetypes
  - How does the magic system express itself in the lore
  - Does it drive PLOT?

- [ ] **Possible alternate calendar descriptions**
  - Is it simple Gregorian, or something more "alternative earth" appropriate
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

These are open questions and concepts to develop when inspiration strikes:

### Prehistoric Civilizations & Pre-Imperial Constructs

*Highly speculative — the cosmological architecture implies this territory exists, but no design decisions have been made. Captured here so it isn't lost.*

- [ ] **Who built the Warrens?** — The infrastructure predates the Empire; something created it
- [ ] **Who built the Great Wall?** — Elves maintain it but may not have built it; its original purpose may differ from its current function
- [ ] **Where did Binding Magic come from?** — The Human Empire weaponized it; someone understood it first
- [ ] **What are the Elder Gods?** — Mentioned in brainstorm; relationship to Warrens, Held Breath, and Celestial Court entirely unknown; may be the Held Breath's original architects, or the beings who created the Mythic Ecosystem, or something else entirely
- [ ] **Were there pre-Imperial civilizations at meaningful scale?** — What did the world look like before the Human Empire consolidated power?
- [ ] **Is "prehistoric" the right frame, or is this cosmological rather than historical?** — The Elder Civilization may not be *older* so much as *other* — operating at a different ontological layer

*These questions may never need full answers — mysteries can serve the campaign better than explanations. But they should be *intentional* mysteries, not overlooked gaps.*

### Ancestry Structures & Drives
- [ ] What are Goblins' main drives? Halflings? Elves? Dwarves?
- [ ] How do we create similar depth to Orcs for other ancestries?
- [ ] Social hierarchies, economic roles, cultural identities for each

### Real-World Analogs & Stereotype Reversals
- [ ] Orcs = Sogdian merchants (cosmopolitan traders)
- [ ] Goblins = Venetian/Genoese republics?
- [ ] Halflings = Armenian/Jewish diaspora traders?
- [ ] Dwarves = Byzantine scholars? Islamic Golden Age?
- [ ] Elves = ??? (depends on cosmology decision)
- [ ] Which real Silk Road peoples are "missing" that ancestries could represent?

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
- [ ] **Potential paradigm shift from traditional high elf tropes:**
- Are Elves refugees from a celestial realm? Exiled? Fleeing catastrophe?
- Is "diminishing" an involuntary return to their origin?
- Is their long lifespan a curse/exile sentence, not a blessing?
- How does this integrate with Elder Gods, Warrens, and Hero Heaven?
- Do Elves recognize Hero Heaven? Fear it? "You went where we cannot return"?
- **Decision Required Before:** Elven cultural documentation, magic system details, campaign cosmology

### Silk Road Mythology & Key Locations
- [ ] **Real sites to map to fantasy versions:**
- Religious: Jerusalem, Mecca, Varanasi, Bodh Gaya, Mount Kailash, Lhasa
- Legendary: Shambhala, Kunlun Mountains, Taklamakan Desert
- Cities: Samarkand, Bukhara, Kashgar, Dunhuang
- Natural: Tian Shan, Pamir Mountains, Ganges, Yellow River
- **Options:** Direct analogs? Mythological inversions? Ancestry homelands? Campaign locations?
- **Where is Hero Heaven threshold?** Which Lich strongholds where?

**See `/narrative/BRAINSTORM_2026-02-13.md` for full exploration of these concepts.**

---


## COMPLETED

**— Assets —**
_Last verified: 2026-02-13_

### Story & Narrative Foundation

#### Core Campaign Structure — LOCKED
- [x] **File:** `/narrative/CORE_CAMPAIGN_NARRATIVE.md` 
- **Status:** Complete and locked \[EDITORIAL NOTE] **REVIEW - NOT 'COMPLETE' (e.g., `story_skeleton.md` is... outdated)**
- **Contents:**
  - [x] Hero Heaven cosmology (earned reward, premature expulsion)\[EDITORIAL NOTE] - Is it (e.g., magic system, god hierarchy)?
  - [x] Six archetype-specific self-doubt frameworks (Breaker, Bridge, Seeker, Sacrificer, Warrior, Visionary)
  - [x] Tool mechanics (Resist/Hunger/Know framework)
  - [x] Campaign arc structure (3 acts)
  - [x] The Wizard's catalyst role (not final boss)
  - [x] Ghost of fallen companion (ambiguous guide)
  - [x] Core campaign questions and themes

#### Session 0 Architecture — LOCKED
- **Files:**
  - [x] `/narrative/sessions/00_session0/Sessions_Structure.md`
  - [x] `/narrative/sessions/00_session0/gm_secrets/Session_0_Secret_Snippets-Archetype_Templates.md`
  - [x] `/narrative/Shared_Memory_Events.md`
  - [x] `/narrative/Shared_Memory_Narrative_Template.md`
  - [x] `/narrative/PLAYER_ARC_SYNTHESIS.md`
  - [x] `/narrative/sessions/00_session0/gm_secrets/Session_0_Awakening_Design_Notes.md`
- **Status:** Structure locked, ready for content population
- **Contents:**
  - [x] 8-segment awakening structure (4.5-5 hours verified executable)
  - [x] Hybrid parallel + sequential pacing (Bridge+Seeker, Warrior+Sacrificer parallel; Breaker sequential)
  - [x] Secret snippet architecture (god-tier moments during individual awakenings)
  - [x] Four-axis flashback trigger system
  - [x] Event-centric shared memory design (5 thematic events framework)
  - [x] Player pitch (less-transparent version preserving mystery)
  - [x] Six archetype descriptions (no past-leakage)

#### Awakening Scenarios PARTIAL (3 of 6 complete)
- **Completed:**
  - [x] `/narrative/sessions/00_session0/Session_0_Warrior_Awakening.md` + versions/
  - [x] `/narrative/sessions/00_session0/Session_0_Seeker_Awakening.md` + versions/
  - [x] `/narrative/sessions/00_session0/Session_0_Breaker_Awakening.md` + versions/
- **Status:** High-quality prose, Erikson-inspired atmospheric writing, ~8-segment structure

### World-Building EXPANDED (2026-02-13)

#### Weapons & Equipment — NEW
- [x] **File:** `/mechanics/weapons_silk_road.md`
- **Status:** Complete reference created 2026-02-13
- **Contents:**
  - 50+ weapons from Jerusalem to Changzhou
  - Daggerheart mechanics (SRD-compliant damage/tags)
  - Enhancement potential flags (16 Mythic Candidates)
  - NPC archetype pairings (10+ combat/cultural roles)
  - Ancestry weapon affinities (all 12+ ancestries)
  - Tier scaling guidance (Tier 1-4)
  - Cultural notes and regional availability

#### Ancestry Documentation ORC COMPLETE, OTHERS PENDING
- [x] **File:** `/world/ancestries/orcs.md`
- **Status:** Comprehensive cultural overview created 2026-02-13
- **Contents:**
  - Corrected 1,000-year timeline (40 generations post-liberation)
  - Historical context (5 Eras from captivity to present)
  - Cultural characteristics (clan diversity, cosmopolitan adaptation)
  - **The Trading Centuries** (~3,000 words on economic transformation)
  - **Diplomatic Academies** (~1,500 words on negotiation mastery)
  - **Found Family Philosophy** (~1,200 words on kinship expansion)
  - Social hierarchy including **Bondkeeper** role (trade/diplomatic leader)
  - Orc Merchant Leagues (4 regional leagues detailed)
  - Religious/spiritual practices (no unified religion, ancestor veneration)
  - Economic roles (5 primary industries)
  - Relations with other ancestries
  - Modern challenges (identity beyond liberation, wealth vs. memory, etc.)
  - NPC seeds and PC hooks
- [x] **Supporting Files:**
  - `/world/ancestries/ORCS_REVISION_SUMMARY.md` (change log)

### World Entity Infrastructure — COMPLETE (2026-03-10)

#### Entity Index Files — CREATED
- [x] **File:** `/world/factions/Index.md`
  - 12 present-day factions + 1 historical (Human Empire) + 2 individuals-as-factions (The Wizard, Fallen Teammate)
  - Columns: name | type | region | visible_control | hidden_control | rivals | controls | narrative_weight | status
  - Canonical wikilink names established — all future files should reference these

- [x] **File:** `/world/events/Index.md`
  - 11 historical events in causal chain order (Era 0–5) + 2 anticipated future events
  - Columns: name | era | approx_date | type | cause | effect | key_actors | narrative_weight | status

- [x] **File:** `/world/concepts/Index.md`
  - 13 world concepts across 3 layers: cosmological / magical mechanisms / named forces
  - Includes both canon and `proposed` items (from STORY_ARC_SYNTHESIS, pending canonization)

#### Entity Templates — CREATED
- [x] **File:** `templates/world-building/_TEMPLATE_faction.md` — Faction individual file template
- [x] **File:** `templates/world-building/_TEMPLATE_event.md` — Historical event individual file template
- [x] **File:** `templates/world-building/_TEMPLATE_concept.md` — Concept/force individual file template

#### Location Hierarchy Templates — REBUILT/CREATED
- [x] **File:** `templates/world-building/_TEMPLATE_region.md` — **REBUILT** (full rewrite)
  - Distinctions section (3 named qualities + "You might encounter" bullets)
  - GM Principles section (named tonal directives)
  - Faction fields: factions_dominant / factions_present / factions_hidden as canonical wikilinks
  - contains_landmarks / contains_settlements / contains_poi inventory fields
  - Era-by-era Historical Context + Campaign Relevance + Ecosystem status

- [x] **File:** `templates/world-building/_TEMPLATE_landmark.md` — **NEW**
  - Traversable container entity (between Region and Settlement/POI in hierarchy)
  - Own Distinctions section (landmark-scale atmospheric qualities)
  - Denizens section (what inhabits the landmark itself, distinct from factions)
  - contains_poi + transclusion slots for sub-elements

- [x] **File:** `templates/world-building/_TEMPLATE_environment.md` — **NEW** (Daggerheart-faithful)
  - Mechanical encounter layer: env_type / tier (1–4) / difficulty (8–18) / impulses
  - Features: Passive / Action / Reaction / Spend Fear structure
  - Embedded GM questions on every feature
  - Skill Challenges + Group Action Option sections

- [x] **File:** `templates/world-building/_TEMPLATE_location_settlement.md` — **UPDATED**
  - known_for one-liner (replaces Distinctions at settlement level)
  - factions_visible / factions_hidden / factions_present as canonical wikilinks
  - Rules/Norms/Customs section
  - contains_poi + transclusion slots (`![[poi-filename]]`) for sub-elements
  - environment_file link

- [x] **File:** `templates/world-building/_TEMPLATE_location_poi.md` — **REBUILT** (unified template)
  - Single template handles both standalone POIs (with coordinates) and sub-element POIs (without)
  - parent: field for sub-elements of Settlements or Landmarks
  - parent_region: field for standalone POIs
  - location: [lat, long] optional — present when POI warrants its own map pin
  - concept: one-liner replaces Distinctions at POI level
  - Leaflet block present with removal comment for sub-elements

**Design decisions locked this session:**
- Full entity hierarchy: Region → Landmark / Settlement → POI (sub-element or standalone) → Environment
- Distinctions belong at Region level (broad) and Landmark level (local-scale) only
- Settlements use known_for; POIs use concept — no full Distinctions at these levels
- All POI files use one template; sub-elements are transcluded into parents via `![[filename]]`
- region_tier removed as redundant (tier is an encounter-design tool, belongs at Environment level)

---

### World-Building GEOGRAPHIC FOUNDATION COMPLETE

#### Geographic Framework — LOCKED
- **Files:**
  - `/world/content/WORLD_REGIONS_AND_LOCATIONS.md`
  - `/world/content/FANTASY_NAMING_GUIDE.md`
  - `/world/content/REGIONAL_FACTIONS_AND_POWER_DYNAMICS.md`
  - `/world/data/regions.json`
- **Status:** Complete and locked
- **Contents:**
  - [x] 6 major regions defined (Skamarketh, Tarim Basin, Eastern Gateway, Mountain Passes, Steppe, Elven Highlands)
  - [x] 37 locations with coordinates (22 created as individual notes, 15 more in regions.json)
  - [x] Complete fantasy naming system with linguistic formulas per faction
  - [x] Ancient geographic features named (Taklamehr, Sky-Pass/Tian-Khor, Kunlain, Am-Darkath, Syrghar, Yuraneil)
  - [x] Regional faction controllers and power dynamics
  - [x] Cultural/political framework (Empire → Chaos → Stabilization → Present eras)
- **Remaining:**
  - [x] Timeline (History)
  - [x] Major events
#### Location Infrastructure — WORKING
- [x] **Location:** `/world/locations/` (37 markdown files)
- [x] **Status:** Infrastructure complete, content population ongoing
- [x] **Features:**
  - [x] Obsidian Leaflet integration working
  - [x] 7 marker types configured (city, ruins, pass, waystation, oasis, sacred-site, mystery)
  - [x] OpenTopoMap tiles verified
  - [x] Schema documented in LOCATION_NOTE_SCHEMA.md

### Game Mechanics ARCHITECTURE LOCKED

#### Charm System — DECIDED
- [x] **File:** `/mechanics/character-progression/charms/CHARM_SYSTEM_ANALYSIS.md`
- [x] **Decision:** Option C - Exalted-Lite (Hope + Fatigue Points hybrid)
- [x] **Status:** Architecture locked, ready for implementation
- [x] **Details:**
  - [x] 3-tier progression (Foundation/Specialization/Mastery)
  - [x] Hybrid resources: FP (tactical, from Health) + Hope (strategic, from duality dice)
  - [x] Conversion formulas: 1-3m → 2 FP OR 1 Hope (Tier 1); 4-6m → 3 FP OR 1 Hope + 1 Will (Tier 2); 7-10m → 2-3 Hope (Tier 3)
  - [x] Complete 194-charm Exalted reference document created
  - [x] Charm template created (`CHARM_TEMPLATE.md`)
  - [x] Charm accessibility matrix created

#### Tool Progression — LOCKED
- [x] **File:** `/mechanics/character-progression/TOOL_EVOLUTION_FRAMEWORK.md`
- [x] **Status:** 4-stage progression defined
- [x] **Stages:**
  - [x] 1. Crude tools: Standard Daggerheart rolls
  - [x] 2. Blessed tools: Narrative advantage only
  - [x] 3. Awakened tools: 2d12 Hope (keep highest) — celestial dice
  - [x] 4. Legendary tools: Additional effects TBD
- [x] **Integration:** Works with Resist/Hunger/Know framework

#### Daggerheart Integration — TEMPLATES CREATED
- [x] **Location:** `/templates/`
- [x] **Status:** Domain-aligned templates complete
- [x] **Contents:**
  - [x] Character sheet templates
  - [x] Session tracking templates
  - [x] Archetype-to-domain mapping
  - [x] Adversary templates
  - [x] Environment templates

**— Mechanics —**
_These are LOCKED decisions — see DECISION_LOG.md for rationale_  
_Last verified: 2026-02-05_

### Resource Management
- [x] **Hybrid System:** Hope (strategic) + Fatigue Points (tactical)
  - [x] FP derived from Health stat, recovers with rest
  - [x] Hope gained from duality dice + narrative choices + tier bonuses
  - [x] Will as rare high-stakes resource

### Charm Activation
- [x] **Model:** Exalted-Lite with Daggerheart foundation
- [x] **Costs:** 2-3 FP OR 1-3 Hope (tier-dependent)
- [x] **Types:** Simple, Supplemental, Reflexive
- [x] **Simplification:** No combat keyword complexity from Exalted

### Tool Mechanics
- [x] **Framework:** Resist/Hunger/Know (narrative-based, guideline-focused)
  - [x] Resist: Tool refuses certain actions (protective or restrictive?)
  - [x] Hunger: Tool calls for use/restoration (genuine or manipulation?)
  - [x] Know: Tool reveals fragmentary memories (truth or interpretation?)
- [x] **Progression:** 4-stage celestial dice advantage system
- [x] **Integration:** Works with Charm system and duality dice

### Conflict Resolution
- [x] **Foundation:** Daggerheart's duality dice (Hope/Fear d12s)
- [x] **Hope Generation:** Feeds Charm system
- [x] **Fear Complication:** Affects tool usage (specific mechanics TBD)

### Character Identity
- [x] **Archetypes:** 6 options (Breaker, Bridge, Seeker, Sacrificer, Warrior, Visionary)
- [x] **Domain Alignment:** Maps to Daggerheart domains
- [x] **Starting State:** Crude tools + tier 1 foundation Charms

---

### Preliminary World Diagrams — COMPLETE (2026-03-13)

- [x] **File:** `/world/diagrams/faction-web.md`
  - Mermaid `graph LR` — faction relationship web
  - Nodes colour-coded by narrative weight (very-high / high / medium-high / medium)
  - Edge types: rivals `<-->`, hidden control `-.->`, active opposition `-->`
  - Elven Highland Enclaves with three dotted "whispers in eastern courts" lines
- [x] **File:** `/world/diagrams/cosmological-architecture.md`
  - Mermaid `graph TD` — four-layer cosmological stack (Celestial → Mortal → Warrens → Pre-Cosmic)
  - Floating mechanism nodes (Gaes, Binding Magic) bridging layers
  - Pending design decisions shown in grey dashed style
  - Causal chain: Lich-Legion strain → Warren inversion → Threshold targeting → Held Breath stirs
- [x] **File:** `/world/diagrams/historical-causal-chain.md`
  - Mermaid `flowchart TD` — era-coloured nodes, Era 0–5 + Campaign Present + 2 anticipated futures
  - Long dotted line: The Sacrifice (Era 1) → The Expulsion (Era 5), 1,000 years dormant
- [x] **Fix:** All three diagrams updated: `\n` → `<br/>` in node/edge labels for Obsidian Mermaid compatibility

---


## SESSION LOG

### Session 2026-03-13 (continued II)
**Charm System Removal**

- [x] Decision: Charm system removed from active scope — Vestiges/Memory Fragments/The Wrongness (Tools + R-H-K) carry the campaign; Charms never reached players and generated no excitement
- [x] 15 dedicated Charm files archived to `archive/charms/`: full `charms/` directory, `charm-analysis/`, 3× SPELLS_VS_CHARMS analyses, 4 Charm templates
- [x] Charm Library Implementation replaced in TODO with scoped "Charm Reference Audit" task (7 active docs, 1 session, deferred)
- [x] Dashboard re-run post-removal

### Session 2026-03-13 (continued)
**Campaign Frame Audit & Blocker Resolution**

**Campaign Frame v2 audit against TODO:**
- [x] Confirmed `templates/tarim-shaiel-campaign-frame-v2.md` exists and is substantially complete
- [x] 8 of 12 TODO items confirmed done: Pitch, Tone/Feel, Themes, Touchstones, Overview, Heritage & Classes, Player Principles, GM Principles, Session Zero Questions
- [x] 4 GM-facing stubs remain: Distinctions, Inciting Incident, Custom Mechanics (Vestiges/Memory Fragments/The Wrongness), Campaign Map
- [x] Custom Mechanics terminology reconciled: Vestiges = Tools, Memory Fragments = Know/R-H-K subsystem, The Wrongness = ecosystem strain as players experience it

**Blocker resolved:**
- [x] Class/archetype mapping blocker cleared — v2 "approach" framing sidesteps prescriptive mapping; all Daggerheart classes open; removed from BLOCKED section and Quick Summary

**Dashboard script fix:**
- [x] `generate_dashboard.py`: SESSION LOG + COMPLETED hardcoded as excluded H2 sections — eliminates domain leakage from archive content
- [x] World: 58% → 34% (inflation corrected), Readiness: 51% → 45% → 48% (post campaign frame audit)
- [x] Blockers: 4 → 3 (Campaign Frame blocker cleared)

### Session 2026-03-13
**Preliminary World Diagrams & Mermaid Rendering Fix**

**Diagrams Created:**
- [x] `/world/diagrams/faction-web.md` — faction relationship web (narrative-weight colour-coded, rival/hidden-control/opposition edges)
- [x] `/world/diagrams/cosmological-architecture.md` — four-layer cosmological stack with floating mechanism nodes and pending-decision styling
- [x] `/world/diagrams/historical-causal-chain.md` — era-coloured causal chain from Era 0 to Campaign Present + 2 anticipated futures

**Rendering Fix:**
- [x] All three diagram files: replaced literal `\n` escape sequences in node/edge labels with `<br/>` for Obsidian Mermaid compatibility

**Housekeeping:**
- [x] TODO.md updated: session log, completed section, PROJECT HEALTH quick summary, `last_updated` frontmatter
- [x] Dashboard re-run (see below)
- [x] Dashboard script bug fixed: SESSION LOG + COMPLETED sections hardcoded as excluded from domain counting
- [x] Dashboard re-run post-fix: world 58%→34%, readiness 51%→45% (inflation corrected)

### Session 2026-03-10
**World Entity Infrastructure & Location Template System**

**Entity Indexes Created:**
- [x] `/world/factions/Index.md` — Master registry: 12 present-day + 1 historical + 2 individuals-as-factions; canonical wikilink names established
- [x] `/world/events/Index.md` — 11 historical events in causal chain (Era 0–5) + 2 anticipated future events
- [x] `/world/concepts/Index.md` — 13 concepts across cosmological / magical mechanisms / named forces layers

**Entity Templates Created:**
- [x] `templates/world-building/_TEMPLATE_faction.md`
- [x] `templates/world-building/_TEMPLATE_event.md`
- [x] `templates/world-building/_TEMPLATE_concept.md`

**Location Hierarchy Templates (full rewrite/new):**
- [x] `_TEMPLATE_region.md` — rebuilt with Distinctions, GM Principles, canonical faction wikilinks, era history
- [x] `_TEMPLATE_landmark.md` — new; traversable container with own Distinctions + Denizens sections
- [x] `_TEMPLATE_environment.md` — new; Daggerheart-faithful encounter layer (Passive/Action/Reaction/Fear-spend features + GM questions)
- [x] `_TEMPLATE_location_settlement.md` — updated with known_for, canonical faction fields, transclusion slots
- [x] `_TEMPLATE_location_poi.md` — rebuilt as unified template (standalone + sub-element in one)

**Architecture Decisions Locked:**
- Entity hierarchy: Region → Landmark / Settlement → POI → Environment
- Distinctions: Region (broad) + Landmark (local-scale) only; Settlement = known_for; POI = concept
- POI = universal sub-element format for both Landmarks and Settlements; transclusion via `![[filename]]`
- region_tier removed (redundant with Environment-level tier)
- All POI files include optional `location: [lat, long]` for map-pin presence regardless of parent status

**⚠️ Follow-up work flagged:**
- Create 12 individual faction files using `_TEMPLATE_faction.md`
- Create 11 individual event files using `_TEMPLATE_event.md`
- Create 13 individual concept files using `_TEMPLATE_concept.md`
- Create 6 region files using `_TEMPLATE_region.md` (Skamarketh, Tarim Basin, Eastern Gateway, Mountain Passes, The Steppe, Elven Highlands)
- Canonicalize existing 22 location files: replace free-text faction names with wikilinks from `/world/factions/Index.md`

### Session 2026-03-17
**Visibility Gating + Obsidian Shell Commands Integration**

- [x] Added `--public` flag (fails-closed) to `generate_world_html.py`: only `visibility: public` generates in public mode; missing/gm_secrets/typo → skipped
- [x] Added `--public` flag (fails-closed) to `generate_all_world_html.py`: same allowlist logic; default visibility changed from `'public'` to `'gm_secrets'`
- [x] Added `--open` flag to `generate_world_html.py`: opens browser after generation (Shell Commands integration)
- [x] Added silent-skip for non-pipeline file types (exit 0 without output)
- [x] Wired `--public` into `netlify.toml` and `.github/workflows/generate-html.yml`
- [x] Deleted stale `docs/nianhao-the-divine-arc.html` from repo (previously committed without gating)
- [x] Created `utilities/shell-commands-config.md`: setup reference for 3 Shell Commands plugin commands (on-save preview, full pipeline hotkey, open preview)
- [x] Updated `SOURCE_FORMAT.md`: fails-closed note, visibility gating table, Pattern A (`%%...%%`) and Pattern B (`-gm` companion file) documented with rules and tradeoffs
- [x] Committed as `471ecc9` + `c444901`, pushed to `origin/claude/upbeat-bartik` (PR #1, commit 7 & 8)

**Infrastructure design decisions locked this session:**
- Visibility gating = allowlist design (explicit `public` required, not denylist of `gm_secrets`)
- Sub-document secrets = two patterns: `%%...%%` inline (stripped everywhere) and `-gm` companion file (separate `gm_secrets` doc for transcludable GM notes)
- Shell Commands integration = no `--public` flag ever; local always generates everything

### Session 2026-03-15/16
**HTML Publishing Pipeline + Netlify Deployment**

- [x] Created `utilities/legendkeeper-pipeline/generate_world_html.py` — Obsidian MD → styled HTML; Campaign Frame design system (parchment/gold/crimson); `type: timeline` (list-view with era bands + lane rows) and `type: myth|lore` (cover, epigraph, prose body, section cards)
- [x] Added image support to timeline event cards (`image:` field)
- [x] Created `from_lk_json.py` — reverse converter from LK JSON export back to source MD format
- [x] Created canonical `world/timelines/nianhao-the-divine-arc.md` (57 events, 4 lanes, Calendar Eras)
- [x] Fixed era label bug: Calendar Eras section (`## Calendar Eras`) uses LK Time System era definitions (HJ/HB), not swimlane auto-abbreviations; supports backward eras and open-ended date ranges
- [x] Created `utilities/legendkeeper-pipeline/generate_all_world_html.py` — batch runner; auto-discovers pipeline sources; writes `docs/index.html` with Core + World sections
- [x] Updated `netlify.toml` — build command runs all three generators
- [x] Updated `.github/workflows/generate-html.yml` — path triggers for `world/**/*.md` + `narrative/**/*.md`; `pip install pyyaml` step; world HTML generation step
- [x] Deleted stale `docs/nianhao.html` (test artifact)
- [x] Updated `utilities/legendkeeper-pipeline/SOURCE_FORMAT.md` — Calendar Eras section documented
- [x] Committed as 5 commits (`06bfad8` through `23dae0e`), pushed to `origin/claude/upbeat-bartik`
- [x] PR #1 created: `claude/upbeat-bartik` → `main` on `github.com/mofro/tarim-shaiel-campaign-frame`

**⚠️ Follow-up work flagged:**
- Netlify site needs to be connected at netlify.com (one-time setup; `netlify.toml` is ready)
- Shell Commands plugin setup in Obsidian (see `utilities/shell-commands-config.md`)
- Merge PR #1 to get pipeline changes into `main`

### Session 2026-03-08
**Cosmological Architecture — 7 of 8 Critical Decisions Locked**

- [x] **Decision 1: Mythic Ecosystem** — Multi-dimensional biome. Warrens as distinct dimensional spaces. Power draws power. Affinities not interchangeable. Threshold = porous container.
- [x] **Decision 2: The Sleeping Entity** — Multiple liminal consciousnesses at celestial scale, held in suspension by cosmological equilibrium. Canonical term: "Held Breath." Not a singular geological force.
- [x] **Decision 3: Entity's Nature** — Dormant liminal consciousnesses. Not purely mindless, not negotiable. Horror is their weight. Threat is awakening, not containment breach.
- [ ] **Decision 4: Wizard's Awareness** — DEFERRED. Requires dedicated narrative session re: Wizard's motivation.
- [x] **Decision 5: Charms & Ecosystem** — Yes, scaled by tier, expressed as beacon. R/H/K reframed as Warren allegiance. Tools = endgame cosmological interface. Awakening narratives audited — no conflicts.
- [x] **Decision 6: Liberation's Side Effects** — REVISED from original. Not ecosystem damage. Liberation = massive beacon event → Warren ripples → drew attention of entities with agendas. Incomplete charge = reckon with what was woken.
- [x] **Decision 7: Threshold as Ecosystem Node** — Hero Heaven adjacent to (not a) Warren. Threshold = concentrated ecosystem wiring. Breach = immediate, unmistakable consequences.
- [x] **Decision 8: Three-Layer Revelation Structure** — Layer 1 (stop Wizard) → Layer 2 (breach causes immediate cosmological break) → Layer 3 (reckon with liberation disturbance + Held Breath). Locked.

**Also this session:**
- Removed "Charm Library" from critical path (moved to later phase, remains in NEAR-TERM)
- Fixed Cosmology domain gauge missing from dashboard (bug in generate_dashboard.py)
- Updated last_updated date to 2026-03-08

**⚠️ Follow-up work flagged:**
- `STORY_ARC_SYNTHESIS.md` — update [PROPOSED] sections to reflect locked decisions; replace "Sleeping Entity" framing with "Held Breath" / liminal consciousnesses
- `liberation_aftermath.md` — rewrite with Warren disturbance framing + timeline fix (200 → 1,000 years)
- `HERO_HEAVEN_THRESHOLD.md` — extend with Threshold-as-ecosystem-wiring framing
- `TOOL_EVOLUTION_FRAMEWORK.md` — add GM note: why does the Warren keep its heroes alive?

### Session 2026-03-05
**Silk Road Myth Analysis — Regional Source Material**

**New File Created:**
- `/narrative/SILK_ROAD_MYTH_ANALYSIS.md` — Research scaffolding (NOT yet canon)
  - Part I: Cosmological Frameworks — 6 regional cosmologies analyzed as simultaneous interpretations of the Mythic Ecosystem (Tengrist three-worlds, Zoroastrian dualism, Pangu/cosmic corpse, Svarga-as-accounting, Hundun paradox, Uçmag/cosmological memory)
  - Part II: Heroic Myth Resonances — 8 champion/cautionary legends mapped to HH structural themes (Alpamysh, Manas, Rostam/Sohrab, Kaveh, Zahhak, Arjuna, Vikramaditya/Vetala, Tang Taizong's descent)
  - Part III: Creatures & Dangers — 7 regionally-sourced adversary types with encounter design notes (Albast, Div, Jiangshi, Rakshasa, Vetala, Nagas, steppe omen-animals)
  - Next Steps section with Immediate/Near-Term/Long-Term action items

**Key Insight from Analysis:** The four regional cosmologies (Tengrist, Zoroastrian, Pangu, Svarga) are not competing explanations — they can be designed as *simultaneous cultural interpretations of the same Mythic Ecosystem reality.* This resolves a long-standing question: different NPC cultures don't need a unified cosmology, they need cosmologies that are *each partially correct* about the same underlying structure.

**Highest-Value Items Flagged:**
- Tengrist three-worlds as structural map for Üst/Orta/Alt = Hero Heaven/Mortal World/Warrens
- Svarga-as-hotel as most uncomfortable reframing of heroes' expulsion (not punishment, just accounting)
- Pangu/cosmic corpse as deepest layer — the world is built on a sacrifice; sacred sites are literally bones
- Uçmag + cosmological memory: *being forgotten has cosmological weight* — heroes' 1,000-year absence may have degraded their anchor in the living world
- Jiangshi / Orcish funerary rites intersection (dying far from home → Orc diaspora history)
- Vetala as ideal recurring NPC type — ancient, tests heroes through riddles, neither hostile nor friendly

---


### Session 2026-03-04
**Story Arc Synthesis & Cosmological Deep Layer:**
- [x] Created `/narrative/STORY_ARC_SYNTHESIS.md` (speculative draft, ~8,000 words)
  - Read and synthesized ALL major canonical documents (CORE_CAMPAIGN_NARRATIVE, HISTORICAL_TIMELINE, CULTURAL_AND_POLITICAL_FRAMEWORK, HERO_IDENTITY, HERO_HEAVEN_THRESHOLD, WIZARD_AND_LICH_CADRE, SPELLS_VS_CHARMS_ANALYSIS_v7, MYTHOLOGICAL_MAPPING_FRAMEWORK, Sessions_Structure, Shared_Memory_Events, MALAZAN_HOLDS_&_WARRENS_SYSTEM)
  - Proposed mythic ecosystem concept (Warrens/Holds/Hero Heaven as containment infrastructure)
  - Proposed sleeping entity as deeper-than-Wizard cosmic threat
  - Mapped all stakeholder awareness levels (High Elves, Mortal Elves, Dwarven archivists, Orcish shamans, human scholars, Goblin/Halfling networks, the Wizard, the heroes)
  - Drafted rough 3-act story arc with nested revelation structure
  - Identified 10 critical design questions (8 upstream, 2 mid-priority)
  - Proposed specific answers to multiple long-standing TBD items
- [x] Updated `TODO.md` with new Priority 0: Cosmological Architecture Decisions
  - 14 new tracked items (8 critical decisions + 6 stakeholder mappings)
  - Mapped how cosmological decisions unblock 8+ existing stalled TODOs
  - Updated critical path: cosmological architecture now upstream of Campaign Frame
- ⚠️ Key realization: Elven cosmology decision, liberation rewrite, Wizard's goal, ghost mechanics, unfinished charge, and endgame design are all sub-problems of a single cosmological architecture that hadn't been defined

### Session 2026-02-13
**Silk Road Weapons & Orc Culture Expansion:**
- [x] Created `/mechanics/weapons_silk_road.md` (comprehensive Silk Road arsenal)
  - 50+ weapons from Jerusalem to Changzhou
  - Mapped to Daggerheart mechanics (SRD-compliant)
  - Enhancement potential flags (Mythic Candidates vs Standard)
  - NPC archetype pairings (combat + cultural roles)
  - Ancestry weapon affinities for all ancestries
  - Scaling guidance for Tiers 2-4
- [x] Created `/world/ancestries/orcs.md` (complete cultural overview)
  - Fixed timeline: 200 years → 1,000 years (40 generations)
  - Added "The Trading Centuries" section (~3,000 words on economic mastery)
  - Added "Diplomatic Academies" section (~1,500 words on negotiation training)
  - Added "Found Family" section (~1,200 words on kinship philosophy)
  - Created **Bondkeeper** social role (economic/diplomatic equivalent of Bladespeaker)
  - Orc Merchant Leagues detailed (4 major regional leagues)
  - Elevated Orc status from marginal survivors → established economic powerhouses
- [x] Created `/world/ancestries/ORCS_REVISION_SUMMARY.md` (change log)
- [x] Created `/narrative/BRAINSTORM_2026-02-13.md` (simmering ideas repository)
  - Ancestry structures/drives for other peoples
  - Real-world analog mappings
  - Empire-era roles (who profited from Orc slavery?)
  - Magic & Elven history questions
  - Elven cosmology: "Celestial refugees" concept
  - Silk Road mythology & key location mapping
- ⚠️ Identified `/narrative/lore/liberation_aftermath.md` needs rewrite (wrong 200-year timeline)

### Session 2026-02-11
**Project Reorganization:**
- [x] Root = PROJECT infrastructure only (no world content)
- [x] INDEX.md → README.md with project overview
- [x] QUICK-START.md completely rewritten (current workflows)
- [x] Sessions organized: `/narrative/sessions/00_session0/` with subdirectories
- [x] Consistent `gm_secrets/` folders across all domains
- [x] Templates moved from `/world/` to `/templates/`
- [x] Operational docs moved to `/utilities/world-building/`
- [x] Metadata conventions documented
- [x] ALL_CAPS naming convention confirmed as meaningful

### Session 2026-02-05
- [x] Created comprehensive TODO refresh with verified file states
- [x] Reorganized into Health Dashboard + status sections
- [x] Audited completed work against actual filesystem
- [x] Identified accurate completion percentages

### Session 2025-01-08
**Session 0 Architecture Locked:**
- [x] Hybrid parallel + sequential pacing structure
- [x] Secret snippet architecture designed
- [x] Four-axis flashback trigger system
- [x] Event-centric shared memory framework (5 thematic events)
- [x] Player pitch (less-transparent version)
- [x] Six archetype descriptions (no past-leakage)

### Session 2025-12-24
**Fantasy Naming & Factions Locked:**
- [x] FANTASY_NAMING_GUIDE.md (complete linguistic system)
- [x] All 6 regions with fantasy names
- [x] Ancient geographic features named
- [x] REGIONAL_FACTIONS_AND_POWER_DYNAMICS.md
- [x] Updated /world/data/regions.json with complete metadata
- [x] Elven enclave mappings to real-world power places

### Session 2025-12-14
**Campaign Foundation & World Framework:**
- [x] CORE_CAMPAIGN_NARRATIVE.md created and locked
- [x] WORLD_REGIONS_AND_LOCATIONS.md
- [x] CULTURAL_FRAMEWORK.md
- [x] Mapping system verified (OpenTopoMap, 7 marker types)
- [x] 22 Location Notes with proper metadata

---


## QUICK REFERENCE

### Core Documents
- **Campaign Narrative:** [CORE_CAMPAIGN_NARRATIVE.md](/narrative/CORE_CAMPAIGN_NARRATIVE.md) ⭐ START HERE
- **Decision Log:** [DECISION_LOG.md](/DECISION_LOG.md)
- **Project Overview:** [README.md](../README.md)

### World Documentation
- **Regions & Locations:** [WORLD_REGIONS_AND_LOCATIONS.md](/world/content/WORLD_REGIONS_AND_LOCATIONS.md)
- **Fantasy Naming:** [FANTASY_NAMING_GUIDE.md](/world/content/FANTASY_NAMING_GUIDE.md)
- **Factions & Politics:** [REGIONAL_FACTIONS_AND_POWER_DYNAMICS.md](/world/content/REGIONAL_FACTIONS_AND_POWER_DYNAMICS.md)
- **Cultural Framework:** [CULTURAL_FRAMEWORK.md](/world/content/CULTURAL_FRAMEWORK.md)
- **Location Schema:** [LOCATION_NOTE_SCHEMA.md](/utilities/world-building/systems/LOCATION_NOTE_SCHEMA.md)

### Mechanics Documentation
- **Charm System:** [CHARM_SYSTEM_ANALYSIS.md](/mechanics/character-progression/charms/CHARM_SYSTEM_ANALYSIS.md)
- **Tool Evolution:** [TOOL_EVOLUTION_FRAMEWORK.md](/mechanics/character-progression/TOOL_EVOLUTION_FRAMEWORK.md)
- **Celestial Dice:** [CELESTIAL_DICE_MECHANICS.md](/mechanics/character-progression/CELESTIAL_DICE_MECHANICS.md)
- **Charm Reference:** [COMPLETE_CHARM_REFERENCE.md](/mechanics/character-progression/charms/COMPLETE_CHARM_REFERENCE.md)

### Session 0 Materials
- **Session Structure:** [Sessions_Structure.md](/narrative/sessions/00_session0/Sessions_Structure.md)
- **Warrior Awakening:** [Session_0_Warrior_Awakening.md](/narrative/sessions/00_session0/Session_0_Warrior_Awakening.md)
- **Seeker Awakening:** [Session_0_Seeker_Awakening.md](/narrative/sessions/00_session0/Session_0_Seeker_Awakening.md)
- **Breaker Awakening:** [Session_0_Breaker_Awakening.md](/narrative/sessions/00_session0/Session_0_Breaker_Awakening.md)
- **Secret Snippets Template:** [Session_0_Secret_Snippets-Archetype_Templates.md](/narrative/sessions/00_session0/gm_secrets/Session_0_Secret_Snippets-Archetype_Templates.md)
- **Shared Memory Events:** [Shared_Memory_Events.md](/narrative/Shared_Memory_Events.md)

### Maps & Data
- **All Locations:** `/world/locations/` (37 markdown files)
- **Source Data:** [regions.json](/world/data/regions.json)
- **Test Maps:** [test_leaflet.md](/world/maps/test_leaflet.md)

### Transcripts
- **Recent Sessions:** `/transcripts/` (12+ conversation records)

---


## WORKING PRINCIPLES

### Documentation Philosophy
1. **Single Source of Truth:** Each piece of information lives in exactly one canonical location
2. **Cross-Reference, Don't Duplicate:** Use links and references rather than copying content
3. **Verify Before Update:** Always check filesystem state before claiming completion
4. **Date Your Changes:** Include verification dates to track staleness

### Development Priorities
1. **Foundation Before Detail:** Lock architecture before populating content
2. **Playable Before Perfect:** Get to functional state, then polish
3. **Test Integration Early:** Verify systems work together before going deep
4. **Document Decisions:** Capture rationale, not just outcomes

### Session Flow
1. **Review Status:** Check TODO.md at session start
2. **Pick Priority:** Choose from ACTIVE or NEAR-TERM sections
3. **Update As You Go:** Mark items complete when verified in filesystem
4. **Capture New Work:** Add new tasks to appropriate priority tier

---

_This TODO reflects actual filesystem state verified 2026-02-05. All completion claims have been cross-checked against existing files. Progress metrics are based on verified deliverables, not estimates._
