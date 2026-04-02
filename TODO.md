---
title: Project TODO & Status
project: TTRPG_Tarim_Shaiel
type: project_management
status: active
created: 2025-12-14
last_updated: 2026-03-31
backlog: BACKLOG.md
banner: images/places/248420.jpg
banner-x: 51
banner-y: 37
---

# TODO & Project Status


## PROJECT HEALTH

**Last Updated:** 2026-03-20
**Critical Path:** Resolve cosmological architecture → Complete Session 0 scenarios → Resolve Campaign Frame → Playtest

**Quick Summary:**
- [x] **Core complete:** Campaign narrative, world geography, fantasy naming, charm architecture, **Orc cultural framework**, **Silk Road weapons**, **Cosmological architecture (all 8 decisions locked 2026-03-17)**, **World entity infrastructure (factions/events/concepts indexes + all location templates 2026-03-10)**, **Preliminary world diagrams (2026-03-13)**, **HTML publishing pipeline + Netlify deployment (2026-03-15)**, **Visibility gating + Obsidian Shell Commands integration (2026-03-17)**
- 🔄 **Active work:** Session 0 scenarios (3/6 core done; expanded 4 have design framework only), STORY_ARC_SYNTHESIS.md needs update to reflect locked decisions, individual entity files to be created from indexes
- ⚠️ **Blockers:** liberation_aftermath.md rewrite (Warren disturbance framing — see DECISION_LOG 2026-03-08)
- 🗒️ **Backlog added (2026-03-26):** Dashboard completion % from GitHub Issues — explore tying domain/section completion percentages to GitHub issue open/closed state (in addition to TODO.md checkbox counts). Requires GitHub API call during dashboard generation. Low priority; investigate after hook infrastructure ([#40](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/40)) is live.
- 🗒️ **Backlog added (2026-03-21):** Template frontmatter reconciliation — `templates/world-building/` files use non-canonical fields (`type: concept`, `classification:` instead of `visibility:`, etc.); needs pass to align with CLAUDE.md spec
- 🆕 **Infrastructure complete (2026-03-15–17):** LegendKeeper dual-path pipeline, HTML generator (timeline + myth), Calendar Era labels (HJ/HB), batch runner + auto-generated index, Netlify deploy, GitHub Actions, visibility gating (fails-closed `--public`), Obsidian Shell Commands setup, **LK ↔ Markdown round-trip complete (`.lk` import/export + reverse converter, 2026-03-17)**
- 🗃️ **Charm system deferred (2026-03-13):** Archived to `archive/charms/`; Daggerheart base used for now; Charm reference audit + remaining cleanup moved to `BACKLOG.md`

**Players:** 1/6 committed — Warrior ✅ | Breaker / Bridge / Seeker / Sacrificer / Visionary / Trickster / Crafter / Sentinel / Healer ⏳

---


## SESSION LOG
_What happened this session. Newest first. Trim to last 3 sessions; older entries go to archive._

### 2026-03-26
- Explored Claude Code hooks vs. GitHub webhooks; designed `workflow_dispatch` trigger pattern via Claude Code `Stop`/`SessionStart` hooks
- Created GitHub Issue [#40](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/40): infra hooks plan (SessionStart sync + Stop pipeline trigger with commit-ahead guard)
- Migrated 23 ACTIVE/BLOCKED TODO items to GitHub Issues ([#41](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/41)–[#63](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/63))
- Established TODO→Issues workflow convention; documented in `CLAUDE.md` Working Conventions + `WORKING PRINCIPLES` pointer in TODO.md
- Fixed dashboard generator: inline markdown links `[text](url)` now render as HTML anchors (`_md_links()` helper)
- **Follow-up:** Merge `claude/github-hooks-investigation-DjJhb` → `main`; implement hooks locally per [#40](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/40)

### 2026-03-22
- Real-world historical parallels exploration via TimeMaps (1453 CE analog mapping across Middle East, Iran, Turkey, South Asia, China, Arabia, Steppe Peoples)
- Created `world/historical-parallels.md` — new doc type: design substrate (lower-case, `doc_type: substrate`); analog map, open questions, inspiration inventory, crawl status
- Established transitional workflow: substrate → named anchor → stub file → TODO checkbox → eventual canon promotion
- Created event stubs: `world/events/scholars-purge.md` (1173 HB, Byzantine dispersal model), `world/events/silent-flowering.md` (398–698 HB, Ming withdrawal model)
- DECISION_LOG entry 11: Cosmic Conscription — open question flagged; gates Celestial Court + Wizard motivation decisions
- BACKLOG: frontmatter schema redesign (3 competing schemas identified; proposed `domain`/`doc_type`/`content_type` split; single `visibility` field)
- BACKLOG: Real-World Analogs section updated — Elves/Ming and Orcs/Mamluks analogs added
- **Follow-up:** Reconcile Scholar's Purge description (see line below); link stubs from `world/events/Index.md`

### 2026-03-21
- Designed mid-campaign Convergence Point architecture (six points, Sessions 3-26): world-dynamic pressure systems that escalate stakes without plot-on-rails
- Filed to `narrative/gm_secrets/MID_CAMPAIGN_CONVERGENCE_ARCHITECTURE.md` (canon) + `DECISION_LOG.md` entry
- Shared Memory Event distribution locked: Events 1-2 at CP1, Events 3-4 at CP3, Event 5 at CP5
- The Wrongness three-tier escalation defined (obstacle → moral complication → weight made concrete)
- Tool stage transition timing locked to convergence points
- **Follow-up flagged:** Populate `narrative/Shared_Memory_Events.md` (currently template stubs) using CP distribution; update `narrative/STORY_ARC_SYNTHESIS.md` pre-lock framing

### 2026-03-20
- Developed Surrendered-Layer Framework via comparative analysis of Warrior, Breaker, and Seeker awakenings: each tool = the specific attribute surrendered at the threshold; the tool's voice is the exiled self trying to reclaim primacy
- Codified full 10-archetype taxonomy: surrendered layer, tool proposal, voice character, and crisis test for all archetypes (6 core + 4 expanded)
- Filed to `gm_secrets/Session_0_Awakening_Design_Notes.md` (new §THE SURRENDERED-LAYER FRAMEWORK), `TOOL_EVOLUTION_FRAMEWORK.md` (filled deferred Tool Personalities section), and `mechanics/design-decisions/DECISION_LOG.md`
- **Two open design questions flagged before framework locks:** (1) Seeker tome/bow discrepancy between TOOL_EVOLUTION_FRAMEWORK Stage 0 examples and written awakening; (2) Sentinel tool conflict — existing stub has "recording device" (epistemic/witness function), framework proposes "cracked lantern" (doxastic/vigilance function) — different design logic, requires creative decision

### 2026-03-19
- Created `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md` (canon) — 9 mortal stakeholders, full synthesis puzzle table, synthesis dependencies; supersedes Part 2 of STORY_ARC_SYNTHESIS.md for stakeholder awareness
- Created `narrative/gm_secrets/DIVINE_PLAYERS.md` (canon) — seven divine players with full entries and alignment map; resolves Celestial Court and Elder Gods pending nodes in cosmological-architecture diagram; supersedes speculative entries in world/factions/Index.md
- Marked all 6 Stakeholder Knowledge Distribution items complete
- Follow-up flagged: update factions/Index.md + cosmological-architecture.md diagram

### 2026-03-18
- Reviewed TODO and memory files at session start (DECISION_LOG, NEXT_SESSION_CONTEXT)
- Identified NEXT_SESSION_CONTEXT.md as stale and largely redundant with TODO + DECISION_LOG
- Decided to consolidate: SESSION LOG + Player Status added to TODO.md as first-class citizens
- Deprecated NEXT_SESSION_CONTEXT.md → archived
- Session-end checklist established: mark completed items → update SESSION LOG → update Player Status → commit + push to main

### 2026-03-17
- Locked Decision 4: Wizard's awareness (B+C — tragic hubris seeded by cosmic manipulation)
- Completed publishing infrastructure: visibility gating (fails-closed), Obsidian Shell Commands integration
- LK ↔ Markdown round-trip complete (`.lk` import/export + reverse converter)

### 2026-03-13
- Charm system archived to `archive/charms/`; mechanical identity now carried by Vestiges/Memory Fragments/The Wrongness
- Campaign Frame v2 blocker resolved: "approach" framing sidesteps prescriptive class mapping

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
- [x] Self-host LK asset images — `download_lk_assets.py` fetches CDN assets to `docs/assets/`; generator rewrites URLs to local relative paths when available; HTML portable without LK auth ([#70](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/70))

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
- _Plugin config steps tracked in ACTIVE §4_

### Sub-document Secret Patterns ✅ (documented, not yet in use)
- [x] **Pattern A (`%%...%%`):** inline secrets stripped from all HTML output (already working)
- [x] **Pattern B (`-gm` companion file):** `<stem>-gm.md` with `visibility: gm_secrets`; enables Obsidian transclusion via block IDs; excluded from public deploy automatically
- [ ] **Apply patterns** as myth/lore documents are authored — no retroactive file changes needed

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
- [x] **Decide the Wizard's Awareness** — LOCKED 2026-03-17. B+C: knows about the ecosystem risks (tragic hubris), AND the entity's 1,000-year subtle influence seeded his overconfidence. He is overconfident and unaware of the true risk — convinced he is the one person who understands the situation well enough to act. He is wrong in the specific way that matters.
- [x] **Decide: Do Heroes' Charms Strain the Ecosystem?** — Confirmed: yes, scaled by tier, expressed as beacon not immediate cost. R/H/K reframed as Warren allegiance. Tools = endgame cosmological interface. See DECISION_LOG.md 2026-03-08.
- [x] **Define the Liberation's Ecosystem Side Effects** — Confirmed: NOT ecosystem damage. Liberation = massive beacon event → Warren ripples → drew attention of entities with agendas. Incomplete charge = reckon with what was woken/whose plans were crossed. Player doubt drama intact. See DECISION_LOG.md 2026-03-08.
- [x] **Define Threshold as Ecosystem Node** — Confirmed: Hero Heaven adjacent to (not a) Warren. Threshold = concentrated ecosystem wiring. Breach = immediate, unmistakable consequences (not slow accumulation). See DECISION_LOG.md 2026-03-08.
- [x] **Define Three-Layer Revelation Structure** — Confirmed: Layer 1 (stop Wizard) → Layer 2 (breach causes immediate cosmological break) → Layer 3 (reckon with liberation disturbance + Held Breath). Tools are the endgame interface. See DECISION_LOG.md 2026-03-08.

#### Stakeholder Knowledge Distribution (Must resolve for mid-campaign planning)

- [x] **Map High Elf awareness** — They understand the ecosystem, withdrew because of cosmological fear, possess preventive (not restorative) knowledge. This answers the Elven cosmology question: not "celestial refugees" but "cosmologically literate beings who retreated from a fault line." → `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md`
- [x] **Map Dwarven archivist awareness** — Chronicle of Ages contains empirical evidence of ecosystem degradation (disappearance patterns, magical anomaly data). They have data but need theory. → `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md`
- [x] **Map Orcish shamanic degradation** — Ancestor communication becoming unreliable as ecosystem symptom. Ancient epic songs contain literal descriptions of the entity. Liberation side effects woven into their traditions. → `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md`
- [x] **Map human scholar suppression** — Scholar's Purge (~1175 CE) was Wizard eliminating researchers. Surviving scholars are scattered, hunted, hold practical fragments. → `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md`
  - ⚠️ **Reconcile model (2026-03-22):** "Wizard eliminating researchers" implies annihilation. `world/events/scholars-purge.md` now adopts Byzantine dispersal model (knowledge scattered, not destroyed). Decide: did the Wizard orchestrate dispersal deliberately, or was scattering an unintended side effect? Resolve before stub is promoted to canon.
- [x] **Map Goblin/Halfling observational network** — Trade disruptions, dead zones, charm failures = best continent-wide empirical dataset of ecosystem degradation. They don't know what their data means. → `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md`
- [x] **Design the information synthesis puzzle** — Heroes as the only beings who can assemble distributed knowledge from all cultures. This is a core campaign mechanic, not just plot. → Section 1 of `narrative/gm_secrets/STAKEHOLDER_KNOWLEDGE_DISTRIBUTION.md`

#### Follow-up From DIVINE_PLAYERS.md (2026-03-19)

- [ ] **Update `world/factions/Index.md`** ([#41](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/41)) — supersede the speculative "Divine & Cosmic Powers" entries with the seven canonical divine players from `narrative/gm_secrets/DIVINE_PLAYERS.md`
- [ ] **Update `world/diagrams/cosmological-architecture.md`** ([#41](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/41)) — resolve two ⚠️ pending nodes (Celestial Court nature + Elder Gods) using the locked divine player entries
- [ ] **Create individual entity files for all seven divine players** ([#41](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/41)) — templates now in `templates/world-building/`. Suggested split: **Adversary template** (`_TEMPLATE_divine_adversary.md`) → The Weighmaster, The Shattered King, The Jade Illusionist, The Conquering Heaven; **Environment template** (`_TEMPLATE_divine_environment.md`) → The Sky-Father, The Chaos Weaver, The Memory-Keeper. All files are `visibility: gm_secrets`; file in `narrative/gm_secrets/divine-players/` (create directory).

#### Event Stubs — From 2026-03-22 Session

- [ ] **Flesh out `world/events/scholars-purge.md`** ([#42](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/42)) — resolve open questions (who enacted it; annihilation vs. dispersal; Wizard's role); link from `world/events/Index.md`; gates `scholars-remnant` faction file
- [ ] **Flesh out `world/events/silent-flowering.md`** ([#43](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/43)) — resolve open questions (the Zheng He moment; the Japan-equivalent faction; what "The Whispered Warning" 1048 HB saw); link from `world/events/Index.md`; gates `elven-highland-enclaves` faction file
- [ ] **Flesh out `world/events/night-of-falling-stars.md`** ([#44](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/44)) — resolve open questions (what the Elf Watchers saw; Whispered Warning content; Wizard's relationship — his Long Preparation begins 698 HB, *before* 1048 HB; clarify causal direction); link from `world/events/Index.md`
- [x] **Link all three stubs from `world/events/Index.md`** ([#42](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/42), [#43](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/43), [#44](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/44)) — scholars-purge, silent-flowering, night-of-falling-stars; done 2026-04-01

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
- [ ] **Distinctions** ([#45](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/45)) (~1-2 sessions) — draw from existing locked material:
  - How the Warrens, Holds, and unreliable magic actually work (cosmological architecture)
  - The Heroic Age, the thousand-year gap, and what the characters actually are
  - The empire and its successor factions — the full picture (not player-facing)
  - The antagonist, the Lich-Legion, the Celestial Peak, the Fallen Companion, the Gaes
- [ ] **Inciting Incident** ([#46](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/46)) (~1 session) — creative writing task, no direct source exists yet:
  - The specific awakening circumstances: location, first witness, opening situation
  - Three-element structure: situation / objective / hooks keyed to character approaches
  - Must preserve secrets while making the opening scene executable
- [ ] **Custom Mechanics: Vestiges / Memory Fragments / The Wrongness** ([#47](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/47)) (~1 session) — translate locked decisions into campaign frame voice:
  - Vestiges = Tools; R-H-K (Resist/Hunger/Know) behavioral framework
  - Memory Fragments = Know behavior as a subsystem; how fragments surface and what they cost
  - The Wrongness = ecosystem strain / beacon effect / Warren inversion as players experience it
- [ ] **Campaign Map** ([#48](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/48)) (~1 session) — player-facing version of existing geographic framework:
  - Eight regions named and placed; post-imperial political shape
  - Space left for table co-creation contributions

**Estimated remaining effort:** 4-5 sessions

### 3. Session 0 Completion 🔄 IN PROGRESS
**Status:** 3 of 6 core awakening scenarios complete. 4 expanded archetypes have design framework (surrendered layer + tool proposal + crisis test) but no prose.
**Design anchor:** Surrendered-Layer Framework filed 2026-03-20 — all new awakenings use this as the design checklist. See `gm_secrets/Session_0_Awakening_Design_Notes.md` §THE SURRENDERED-LAYER FRAMEWORK.

**Open design questions (resolve before writing):**
- [ ] **Seeker tome/bow discrepancy** ([#49](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/49)) — TOOL_EVOLUTION_FRAMEWORK Stage 0 lists bow; written awakening uses tome. Reconcile before Character Creation doc is finalized.
- [ ] **Sentinel tool** ([#50](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/50)) — existing stub: recording device (epistemic/witness); framework proposal: cracked lantern (doxastic/vigilance). Different design logic. Creative decision required.

**Core Six — Remaining Work:**
- [ ] **Breaker Awakening Scenario** ([#51](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/51)) (~1 session)
  - Rewrite Segment 5 per revised single-path architecture (leave the hammer — see Design Notes)
  - Write Segments 6-8 (Snippet, Rescue, Convergence)
  - Tool: crude hammer — surrendered layer: ontological (identity through destruction); voice: comforts, *"I'm right here"*

- [ ] **Sacrificer Awakening Scenario** ([#52](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/52)) (~1 session)
  - 8-segment structure (woven into Act 2 convergence, not standalone)
  - Resolve open situation question: what currency of sacrifice? what relationship? what forces the confrontation?
  - Tool: balance scale with one pan missing — surrendered layer: volitional (right to refuse); voice: offers cost with perfect clarity
  - Secret snippet trigger moment

- [ ] **Visionary Awakening Scenario** ([#53](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/53)) (~1 session)
  - 8-segment structure (fast/explosive — 15-20 min target)
  - ⚠️ Tool conflict: existing notes say "tarot deck"; framework proposes obsidian disk (polished, divination mirror). Resolve before writing.
  - Surrendered layer: perceptual (right to look away); voice: shows — silent, directional, layers visions over present
  - Secret snippet trigger moment

- [ ] **Bridge Awakening Scenario** ([#54](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/54)) (~1 session)
  - 8-segment structure (dialogue-driven, 20-25 min target)
  - ⚠️ Tool conflict: existing notes say "voice/conviction tool"; framework proposes knotted silk cord. Resolve before writing. (May be complementary: seal = social proof, cord = tool proper.)
  - Surrendered layer: relational (right to have a side); voice: aches — weight of never landing
  - Secret snippet trigger moment

**Expanded Four — Design Framework Only (write when archetype enters play):**
- [ ] **Trickster awakening** — framework: shaved coin / authenticating layer / mirrors hero's own voice
- [ ] **Crafter awakening** — framework: worn whetstone / receptive layer / *"one more pass"*
- [ ] **Sentinel awakening** — framework: TBD (see open question above) / doxastic layer / vigilance-without-trust
- [ ] **Healer awakening** — framework: bone needle + silk thread / restorative layer / insists toward next wound
- [ ] *(Keeper awakening — not in expanded player list but stub exists in Design Notes)*

- [ ] **Populate Shared_Memory_Events.md** ([#55](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/55)) (~1-2 sessions)
  - 5 thematic events (framework defined)
  - Event 1: The Warrior's Choice (method of engagement)
  - Event 2: The Question of Sight (knowledge vs. trust vs. truth)
  - Event 3: The Weight of Choice (action vs. consequence)
  - Event 4: Aspirations Undone (victory's unintended consequences)
  - Event 5: The Wizard's Shadow (false certainty about threat)
  - Each event: 400-600 word sensory scene + canonical truths revealed

- [ ] **Write Actual Secret Snippets** ([#56](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/56)) (~1 session for core 6; expanded 4 deferred)
  - 6 core archetype snippets (priority); 4 expanded snippets when scenarios are written
  - Sensory + emotional register (not explanatory)
  - Tied to awakening scenario trigger moments — each snippet surfaces: *"you've faced this choice before"*
  - Creates player-to-character investment

- [ ] **Create Session_0_GM_NOTES.md** ([#57](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/57)) (~1-2 sessions)
  - Detailed execution guide
  - Atmospheric details, NPC quick-refs, pacing cues
  - Scenario-specific GM guidance for all six awakenings
  - Convergence orchestration techniques

- [ ] **Finalize PLAYER_PITCH_AND_PRINCIPLES.md** ([#58](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/58)) (~1 session)
  - Both versions: transparent (GM reference) + less-transparent (player-facing)
  - 6 core archetype descriptions (priority) + 4 expanded (Trickster, Crafter, Sentinel, Healer) when ready
  - Player principles (4-6 guidelines)
  - ⚠️ All descriptions must be present-tense psychological framing only — no hints of fallen godhood or past power

**Total Estimated:** 7-10 sessions

---

### 5. Cyclical Year Calendar 🆕 NOT STARTED ([#59](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/59))
**Domain:** `world/`
**Description:** A setting-appropriate cyclical calendar for years fashioned after the Chinese year-cycle tradition, synthesized with the competing mystical and religious traditions of Tarim-Shaiel (Islamic, Buddhist, Taoist, Silk Road animist). Should feel native to the setting, not imported.

- [ ] **Determine cycle structure** — 12-year animal cycle? 60-year stem-branch cycle? Hybrid? Decide what maps cleanly to the setting's cosmological logic (Warrens, celestial forces, Held Breath periodicity)
- [ ] **Name the cycle units** — names drawn from in-world traditions, not real-world direct translations; cross-reference the major competing religious/mystical traditions for resonance
- [ ] **Map to HJ/HB era system** — integrate with existing Calendar Eras so cycle year labels can appear alongside era dates in timelines and in-world documents
- [ ] **File to `world/calendar-cycles.md`** (new file, `visibility: public`); add reference in `world/` index

**Estimated effort:** ~1 session

---

### 6. Warren Index 🆕 NOT STARTED ([#60](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/60))
**Domain:** `world/cosmology/` + `narrative/gm_secrets/`
**Description:** A comprehensive list of Warrens — both **power Warrens** (housing major cosmic forces and celestial figures) and **affinity Warrens** (abstract, elemental, or conceptual). Some are inhabited by gods or divine players; others are pure dimensional realms with no governing intelligence.

- [ ] **Define Warren taxonomy** — power vs. affinity; inhabited vs. uninhabited; accessible vs. sealed
- [ ] **Map divine players to Warrens** — assign each of the seven canonical divine players (from `narrative/gm_secrets/DIVINE_PLAYERS.md`) to their home Warren or sphere of influence
- [ ] **Design abstract/conceptual Warrens** — death, memory, transformation, hunger, silence, etc. — at minimum those with mechanical/narrative relevance to the heroes' tools and the Held Breath
- [ ] **Flag Warrens with tool resonance** — which Warrens connect to specific hero archetypes or tool evolution stages (endgame cosmological interface)
- [ ] **File public scaffold to `world/cosmology/warrens.md`** (new file, `visibility: public`); GM detail layer at `narrative/gm_secrets/warrens-gm.md`; link from `world/diagrams/cosmological-architecture.md`

**Estimated effort:** ~1-2 sessions

---

### 7. Python Toolset Refactor 🆕 NOT STARTED ([#?](https://github.com/mofro/tarim-shaiel-campaign-frame/issues))
**Domain:** `utilities/`
**Description:** Evolve the ~29-script publishing toolset (~8,000 lines) into a coordinated,
modular infrastructure. 5-stage incremental refactor — each stage independently deployable
without breaking existing Netlify, GitHub Actions, or Obsidian Shell Commands invocations.

- [ ] **Stage 1:** `utilities/shared/config.py` — shared `ProjectConfig` dataclass (vault_root, docs_dir, environment); rename internal logger from `"hero_heaven_generators"` → `"tarim_shaiel_generators"` in `logging_config.py`; adopt in `generate_campaign_frame.py` + `generate_dashboard.py`
- [ ] **Stage 2:** Extract embedded CSS — `utilities/campaign_frame/campaign_frame.css` (~765 lines from `generate_campaign_frame.py` lines 447–795) and `utilities/legendkeeper-pipeline/world.css`; generators read CSS at runtime, HTML output unchanged
- [ ] **Stage 3:** `utilities/shared/base_generator.py` — lightweight `Generator` protocol (`name`, `description`, `run(config, args) -> int`); add thin wrapper class at bottom of each existing generator (no rewrites)
- [ ] **Stage 4:** `utilities/build.py` — unified CLI dispatcher covering all 8 generators; extends `legendkeeper-pipeline/publish.py` pattern to the entire toolset (`build.py campaign-frame`, `build.py all`, `build.py list`)
- [ ] **Stage 5 (after #79):** Fix `generate_ancestry_html.py` — replace hardcoded `ANCESTRY_DATA` dict with `parse_ancestry_file()` reading from `world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md`

**Estimated effort:** 3–4 sessions (stages 1–4); stage 5 deferred to ancestry reskin pass

---

### 4. Publishing Infrastructure Setup ✅ COMPLETE
_Manual one-time setup steps for Obsidian Shell Commands integration + Netlify._

- [x] **Install Shell Commands plugin** in Obsidian (Settings → Community Plugins → "Shell Commands")
- [x] **Configure Command 1: "Regenerate HTML Preview"** — on-save event (`world/` + `narrative/` folder filter); opens browser; reference: `utilities/shell-commands-config.md`
- [x] **Configure Command 2: "Full Pipeline (Local)"** — palette + hotkey (`Cmd+Shift+B`); runs all generators; opens `docs/index.html`
- [x] **Configure Command 3: "Open Local Preview"** — palette convenience command
- [x] **Connect Netlify site** — `netlify.toml` is in repo; site needs to be linked at netlify.com (one-time setup)

---


## BLOCKED

### Critical Blockers

1. ~~**Campaign Frame: Class/archetype mapping**~~ ✅ RESOLVED 2026-03-13
   - v2 document uses "approach" framing; all Daggerheart classes open; no prescriptive mapping needed

### Secondary Decisions

2. - [x] **Ancestries for Tarim-Shaiel** ([#61](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/61)) 🟢
   - **Decision (2026-04-01):** All 18 canonical Daggerheart 1.0 ancestries reviewed and suitability-ranked. Approach: Tarim-Shaiel-specific in-world descriptions for all 18; 6 priority ancestries receive full foundation documents. Several ancestries renamed (Simiah→Vanara, Infernis→Div-Born, Firbolg→Gavar, Clank→Tadbir, Faun→Pari-Kin, Fungril→Khavar, Drakona→Naga-Kin). See Decision 14 in `.meta/DECISION_LOG.md`.
   - **Execution tracked in:** [#79](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/79)

2a. - [ ] **Ancestry Reskin Series: Descriptions + Foundation Documents** ([#79](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/79)) 🟡
   - Phase 1: Create `world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md` — all 18 in-world descriptions compiled (player-facing artifact)
   - Phase 2: Foundation documents for 6 priority ancestries (Vanara, Div-Born, Gavar, Tadbir, Pari-Kin, Khavar) following `world/ancestries/orcs.md` structure at 1/3 depth
   - **Required Before:** Heritage & Classes section of Campaign Frame

3. - [x] **Campaign Frame Complexity Rating** ([#62](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/62)) 🟢
   - **Decision:** Rating **3** — charm system removed; remaining mechanics (Vestiges/Memory Fragments/The Wrongness/R/H/K) are narrative-first, not mechanical crunch. DECISION_LOG #13 (2026-03-31).
   - **Updated:** `templates/tarim-shaiel-campaign-frame-v2.md` header → ●●●○○

4. - [x] **Cartography System Ownership** 🟢
   - **Question:** Formal Cartographer persona or lightweight workflow docs?
   - **Impact:** Minimal — affects who "owns" GeoJSON generation and map updates
   - **Options:** New persona, Lore Keeper extension, or user-triggered scripts
   - **Can Defer:** Not blocking immediate work

5. - [/] **GeoJSON Field Mapping** ([#63](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/63)) 🟡
   - **Question:** Which Location Note fields transfer to GeoJSON descriptions?
   - **Decisions Needed:**
     - Which fields: `resources`, `factions`, `elevation`, `narrative_weight`?
     - Description building strategy (combine how?)
     - Wikilink format: `[Full details: [[location-name]]]`?
     - Marker mapping: Location Note `type` → `marker-symbol` auto-mapping?
     - Single source of truth: manual trigger or auto-regenerate?
     - Validation checks: coordinates present, no duplicates, valid JSON?
   - **Required Before:** Building GeoJSON automation script (low priority, not on critical path)

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
- [x] **Archetypes:** 6 core (Breaker, Bridge, Seeker, Sacrificer, Warrior, Visionary) + 4 expanded optional (Trickster, Crafter, Sentinel, Healer) — Surrendered-Layer Framework covers all 10 (2026-03-20)
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

### Session 2026-03-17 (continued) — LK Round-Trip Pipeline
**LegendKeeper ↔ Markdown Round-Trip — Debugging + Completion**

- [x] Diagnosed `.lk` import failures: `parentId: null` (must be string), pretty-printed JSON (must be compact), microsecond timestamps (JS Date only parses milliseconds), out-of-calendar presentation range
- [x] Snapped opacity to LK's three valid levels (1, 0.5, 0.25) — `0.3` was non-standard
- [x] Updated `from_lk_json.py`: accepts `.lk` (gzip) input directly via magic-byte detection — no manual decompression needed
- [x] Fixed Python 3.9 compatibility: `Path | None` → `Optional[Path]` in `from_lk_json.py`
- [x] Documented Shell Commands for LK pipeline: Command 4 (Generate LK Export via `publish.py`), Command 5 (Import from LK → archives `.md`, runs `from_lk_json.py`, outputs to same folder)
- [x] Resolved Shell Commands path escaping: `{{file_path:relative}}` (no quotes) instead of `{{file_path:absolute}}` with `!` prefix

**Round-trip is now complete:** Markdown → `.lk` (import to LK) and `.lk` → Markdown (pull from LK) both functional.

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
- [x] **Decision 4: Wizard's Awareness** — LOCKED 2026-03-17. B+C. See DECISION_LOG.
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

### GitHub Issues
- **TODO → GitHub Issues:** Qualifying planned items (ACTIVE/BLOCKED, with implementation context) get a GitHub Issue at authoring time. See `CLAUDE.md` Working Conventions for full criteria and workflow.

### Session Flow
1. **Review Status:** Check TODO.md at session start
2. **Pick Priority:** Choose from ACTIVE or NEAR-TERM sections
3. **Update As You Go:** Mark items complete when verified in filesystem
4. **Capture New Work:** Add new tasks to appropriate priority tier

---

_This TODO reflects actual filesystem state verified 2026-02-05. All completion claims have been cross-checked against existing files. Progress metrics are based on verified deliverables, not estimates._
