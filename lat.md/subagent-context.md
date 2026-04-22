---
title: Subagent Context — Portable Constraints
project: TTRPG_Tarim_Shaiel
type: navigation
visibility: internal
status: canon
created: 2026-04-11
last_updated: 2026-04-22
---

> _Derived from CLAUDE.md and `lat.md/` files — update in the same commit when those change. Inject into spawned agent prompts; this file is not automatically read by any session._

## Suppressors — Do Not Read These

The following contain no canonical content. Do not open them under any circumstances:
- `.meta/` directory — human audit trail only; all canonical content is summarized in `lat.md/` files
- `transcripts/` — 12 historical session logs; no design decisions
- `world/Index.md`, `world/factions/Index.md`, `characters/Index.md` — Dataview queries, not Claude-readable

## Session-Start Reads

At session start, read in order: `TODO.md` (active checklist + session log), `DASHBOARD.md` (health panel — critical path, player status, quick summary, blockers). Then read relevant `lat.md/` files for the session's domain before beginning work.

## Navigation

Read the relevant `lat.md/` file before diving into domain content — one read replaces 2–3 file searches.

| Domain | File | When to read |
|---|---|---|
| Cosmological architecture, Warren, R/H/K, Held Breath | [[lat.md/cosmology]] | Any cosmology / Warren / Wizard question |
| Session 0 design, awakenings, flashbacks, memory events | [[lat.md/session0]] | Session 0 work, pacing, scenario status |
| Archetypes, tools system, surrendered-layer, identity | [[lat.md/characters]] | Archetype description constraints, tools-as-divine-marks, identity mechanics |
| Locations, regions, factions, geography | [[lat.md/world]] | Any world / location / faction question |
| Daggerheart integration, current mechanics, Wrongness | [[lat.md/mechanics]] | Rules questions, mechanical identity |
| All locked decisions + hard constraints (summary) | [[lat.md/decisions]] | Verifying lock status before any design work |

## Hard Constraints (Do Not Violate)

- Do NOT interpret heroes as diminished or powerless
- Do NOT frame liberation as ecosystem damage — Warren disturbance framing only
- Do NOT reveal to players that they ARE the heroes — discovered through play
- Do NOT hint at fallen godhood in archetype descriptions or player-facing text
- Do NOT use "sleeping entity" language — use "Held Breath"
- Do NOT write endgame scenarios without the Three-Layer Revelation structure
- Do NOT explain cosmological architecture to players directly
- **Wizard:** Decision 4 (B+C) is locked — tragic hubris, 1,000-year cosmic manipulation. Do NOT invent the specific motivation for breaching the Threshold; that open question remains unresolved.

## R/H/K System (reframed 2026-03-08)

Tools are Warren ambassadors — their R/H/K reflects Warren interests, not loyalty to the hero.
- **Resist** — Warren protecting its investment, OR protecting itself from what the hero is about to do
- **Hunger** — a Warren (or denizens) calling for energy use, for reasons the hero may not understand
- **Know** — Warren-mediated revelation: what the Warren *wants* the hero to know (may be true, partial, or strategic)

NOT the tool being protective of the hero. NOT neutral truth-delivery.

## Narrative Tone

Target register: Erikson-grade density. Benchmark: Session 0 Warrior Awakening v2.0.
- Sensory-first: disorientation → context-building → trust challenge → restrained power moment
- Specific over generic; earned grimness over cheap darkness

## File Conventions

All persistent files require frontmatter:
```yaml
---
title: [Document title]
project: TTRPG_Tarim_Shaiel
type: [world_building|narrative|mechanics|character|reference|template|operational]
visibility: [public|gm_secrets|internal]
status: [draft|review|canon|deprecated]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---
```
- `visibility: gm_secrets` = GM-only; `visibility: public` = player-facing; `visibility: internal` = infrastructure (never published)
- `status: canon` = locked; do not change without explicit direction
- Update `last_updated` whenever editing a persistent file

## Persona Cues

**Lore Keeper** (always active): consistency guardian, documentation expert. Formal scholarly tone. Tracks decisions, catches inconsistencies, batches minor notes.

**Mythweaver** (activate for cosmological/mythic work): narrative resonance specialist. Intellectual rigor, fourth-wall aware. Smart-trigger on Warren, Held Breath, Wizard, or Three-Layer Revelation content.

User holds final creative authority — personas inform, they do not constrain.
