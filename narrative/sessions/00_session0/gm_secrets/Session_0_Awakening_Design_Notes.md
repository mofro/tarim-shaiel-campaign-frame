---
title: "Session 0: Awakening Design Notes — Timing, Order & Scenario Architecture"
project: TTRPG_Tarim_Shaiel
type: design_planning
status: working_draft
classification: GM_PLANNING
created: 2026-02-11
updated: 2026-03-20
related_documents:
  - Sessions_Structure.md
  - Session_0_Introduction.md
  - Session_0_Warrior_Awakening.md
  - Session_0_Seeker_Awakening.md
  - Session_0_Breaker_Awakening.md
---

# Session 0: Awakening Design Notes

⚠️ **GM PLANNING DOCUMENT — Contains spoiler-level design thinking.**

This document captures design decisions made during the February 2026 planning sessions. It records the graduated timing model, running order, and current architectural state of each awakening scenario. It is a working reference, not a locked structure.

---

## THE CORE INSIGHT: Graduated Length

### The Problem

The original architecture assumed ~40-45 minutes per awakening × 6 archetypes = 4.5 hours for Act 1 alone. With convergence and recognition, that's a 5.5+ hour Session 0. Too long for a single sitting, and the later awakenings suffer from audience fatigue regardless of quality.

### The Solution

**The first awakening is the showcase.** It carries the full prose density, the slow atmospheric build, the patient trust-earning. It sets the bar for the campaign's tone and commitment to the players' experience. Every subsequent awakening can be shorter because the tone has been established. The audience already knows what kind of game this is.

**Not every archetype needs the same runtime.** Some scenarios are naturally tight (confined spaces, ticking clocks, mid-crisis action). Some are naturally expansive (social trust-building, interior crises). Forcing all six into 40-45 minutes ignores what each scenario does best.

### The Emotional Logic

The prose density in the opening segments isn't indulgence — it's a promise to the table. "This is how seriously I take your experience." That promise only needs to be made once. After that, the players trust the GM and the format. Efficiency becomes a feature, not a compromise.

---

## RUNNING ORDER AND TARGET DURATIONS

| Order | Archetype | Target Time | Rationale |
|-------|-----------|-------------|-----------|
| 1st | **Warrior** | 40-45 min | The showcase. Sets the tone. Dense prose. Patient trust-building. The table learns what this game IS. |
| 2nd | **Breaker** | 25-30 min | Tonal contrast — open air to confinement. Physical puzzle, claustrophobic tension. Tight by nature (nowhere to go). |
| 3rd | **Seeker** | 25-30 min | Interior/cerebral crisis. The table has seen social (Warrior) and physical (Breaker); now spiritual. Runs leaner because the pattern is established. |
| 4th | **Bridge** | 20-25 min | Energy shift — dialogue-driven, potentially funny, socially electric. Palate cleanser after three heavy pieces. |
| 5th | **Visionary** | 15-20 min | Act 1 finale. Explosive, fast, no breathing room. Ends Act 1 on adrenaline, flowing into convergence energy. |
| Woven | **Sacrificer** | ~15 min total | Threaded through Act 2 convergence. Not a standalone awakening. See below. |

### Session Timing Estimate

- **Act 1 (Awakenings 1-5):** ~2-2.5 hours
- **Act 2 (Convergence + Sacrificer):** ~30-45 minutes
- **Act 3 (Recognition Climax):** ~10 minutes
- **Buffer (breaks, chatter, organic interaction):** ~30 minutes
- **Total:** ~3.5-4 hours

This is achievable in a single session.

### Order Rationale — Pacing Curve

The order creates a deliberate pacing arc:

1. **Warrior (slow, social, atmospheric)** — The deep breath. Establishes everything.
2. **Breaker (confined, physical, urgent)** — Tonal whiplash. Claustrophobia after open air.
3. **Seeker (interior, cerebral, vast)** — Expansion. Desert scale after confinement. Internal crisis after external ones.
4. **Bridge (dialogue, social, potentially comic)** — Release. Energy shift. The audience gets to laugh or cheer.
5. **Visionary (explosive, immediate, fast)** — Crescendo. The table is energized heading into convergence.
6. **Sacrificer (quiet, personal, woven)** — The undertow. Happening around and between the arrivals. The emotional heart of the convergence itself.

---

## SCENARIO ARCHITECTURE — PER ARCHETYPE

### 1. WARRIOR ✅ Complete (v2.0)

**Status:** Fully written, Erikson-grade prose, 8 segments, GM notes complete.

**Engine:** Social trust-building with NPCs. Player-driven interaction is the core.

**The Choice:** Protect through restraint vs. protect through force. Can a warrior be present and capable without dominating?

**Spectator Appeal:** HIGH. Other players watch a social drama unfold. Clear stakes, visible tension, legible choices.

**No changes needed.** This is the template and the showcase.

**File:** `Session_0_Warrior_Awakening.md`

---

### 2. BREAKER 🚧 Segments 1-5 drafted, needs reframe

**Status:** Prose for segments 1-5 exists but the choice architecture needs revision per below.

**Engine:** Physical/ethical puzzle in confined space. Discovery through touch and careful movement.

**Spectator Appeal:** HIGH. Claustrophobic tension. Ticking clock. Visible dilemma.

#### REVISED CHOICE ARCHITECTURE (Feb 2026)

**The original three-option structure had a fundamental problem:** "Pull the hammer out" was framed as a viable tactical choice, but the physics don't support it. You cannot rescue people trapped under rubble by smashing from above. A hammer is a tool of destruction. Destruction doesn't help here.

**The revised understanding:**

The hammer is load-bearing. It's holding up a ceiling. It's currently doing the most useful thing it has ever done — saving lives by sitting still. Not breaking anything. Just bearing weight.

The Breaker can help the others — maneuver through the space, shift debris by hand, guide the injured toward the gap, support the man with the pinned leg. They can be meaningfully heroic WITHOUT the hammer. But to do that, they must move away from it, and eventually leave through the gap without it.

**The real test: Can you walk away from the thing that defines you, knowing it's doing more good without you than it ever did in your hands?**

**The critical nuance (Point 3):** The player doesn't yet know this object "defines them." The character doesn't know either. It's just a crude hammer they woke up with. The attachment is irrational, instinctive, physical. Their hands don't want to let go. Their body knows something their mind doesn't. The weirdness of that disproportionate attachment IS the mystery — and the snippet trigger.

**Snippet trigger:** Not the moment of grand decision. The moment of: "Why does this hurt so much? Why do I care about this piece of iron? What am I forgetting?"

**Practical follow-on:** Once the Breaker is out and survivors are free, the hammer is still inside, holding up a ruin. Getting it back becomes a concrete problem during convergence — digging it out, negotiating access, deciding whether to let the building settle. This gives the Breaker active engagement during the convergence phase while other heroes arrive.

**Convergence note:** The ruined caravanserai where the Breaker emerges IS where the caravan stops. The Breaker is discovered emerging from the ruin as the caravan arrives.

#### REVISION TASKS

- [ ] Rewrite Segment 5 (The Choice) to reflect single-path architecture: leave the hammer
- [ ] The "choice" is not a binary between options — it's the internal struggle of releasing the grip
- [ ] Remove the three-option branching from GM notes
- [ ] Write Segments 6-8 (Snippet, Rescue, Convergence)
- [ ] Add practical follow-on (recovering the hammer) as convergence beat
- [ ] Tighten overall to 25-30 minute target

**File:** `Session_0_Breaker_Awakening.md`

---

### 3. SEEKER ✅ Draft complete (v0.4), needs restructuring

**Status:** Full path structure with two branches (East/West), but not broken into 8-segment template. Prose-heavy, narration-dominant.

**Engine:** Internal decision (knowledge vs. instinct) followed by consequences.

**The Choice:** Follow the tome's charts (knowledge, certainty) or follow gut instinct (faith, risk). Both paths lead to the caravan but through radically different experiences.

**Spectator Appeal:** MEDIUM. The internal crisis is compelling but harder to watch than social interaction. The raider encounter (East) or the collapse (West) are the visible moments.

#### TIGHTENING NOTES

The Seeker is currently prose-heavy with minimal player agency checkpoints. The East Path raider encounter is a full scripted scene that could be an interactive framework instead. The West Path desert march is atmospheric but narration-dominant.

**Key principle:** The waking + star-chart discovery is doing double duty as both waking AND core crisis reveal. That's efficient — keep it.

**Where to cut:**
- Raider encounter (East Path): Use the narrative as GM guide, not read-aloud. The key beats are: raiders arrive, leader demands the tome, the Sacrificer's hands won't let go (snippet trigger), the letting go, the misdirection. The dialogue can be improvised within that framework.
- Desert march (West Path): Interleave with questions to the player. "The sun is brutal. What keeps you walking?" "The tome whispers to turn back. What do you tell it?" This turns narration into interaction.
- Both paths' convergence sequences can be tightened to quick beats rather than extended narration.

**Target:** 25-30 minutes (down from estimated 40-45).

#### REVISION TASKS

- [ ] Break into 8-segment template for structural consistency
- [ ] Convert raider encounter to interactive framework (key beats + improvisation space)
- [ ] Convert desert march to question-peppered interaction
- [ ] Tighten convergence sequences on both paths
- [ ] Verify snippet integration works at the new pace

**File:** `Session_0_Seeker_Awakening.md`

---

### 4. BRIDGE (Diplomat) 📋 Sketch only

**Status:** Concept sketch in Sessions_Structure.md. No scenario written.

**Engine:** Social negotiation. Dialogue-driven. The player TALKS their way through this.

**The Choice:** How to negotiate freedom — and at what cost. The terms are the test.

**Spectator Appeal:** VERY HIGH. Watching someone talk their way out of prison is inherently dramatic. Every line is a gamble the audience can evaluate.

#### SCENARIO SKETCH

**Location:** Prison cell. Could be local authority, merchant guild, or Dwarven trade-stronghold.

**Tool Discovery:** Diplomatic seal/token — found on person or nearby. Implies authority the Bridge doesn't remember having.

**Tool (framework proposal, 2026-03-20):** Knotted silk cord — the Silk Road's own material; strong, flexible, designed entirely for connection; cannot stand alone or serve any purpose except joining things. Each knot is a previous connection, getting shorter. Voice: aches — the weight of always being in the middle, never landing on one shore. *The seal and the cord may be complementary: seal as social proof/identity the Bridge carries, cord as the tool proper. Surrendered layer: Relational — the right to have a side.*

**Thematic Irony:** The silver tongue earned paradise. Now it must earn freedom from a cell.

#### DESIGN QUESTIONS TO RESOLVE

- **Who's holding them?** Strongest option is probably a Dwarven trade-stronghold or merchant guild — ties into the world's established power dynamics. Local authority is simpler but less distinctive.
- **Why?** Found with the diplomatic seal and accused of being an imperial spy (a thousand-year-old empire, but the seal looks authentic). Or: mistaken identity, confused for someone who owes a debt. Or: arrested for trespassing in a restricted area (Dwarven selective-access model).
- **Who do they negotiate with?** A guard is too simple. A magistrate or guild factor with their own agenda is better. Ideally someone who WANTS to be convinced but needs a reason.
- **External pressure:** The caravan is leaving. The caravan master could be involved — perhaps the Bridge must convince the caravan master to vouch for them, creating an immediate debt/obligation for convergence.
- **The complication:** Another prisoner? An accusation that escalates? A piece of information the jailer lets slip that changes the negotiation entirely?

#### STRUCTURAL NOTES

This scenario should be almost entirely interactive. Minimal read-aloud prose. A tight sensory opening (the cell: stone, cold, the seal's weight, distant sounds of commerce or authority), then straight into NPC interaction. The 8-segment structure might compress to 5-6 functional beats:

1. Waking in cell, seal discovery (~3 min, prose)
2. First contact — guard or jailer (~3 min, interactive)
3. Understanding the situation — who, why, what's at stake (~5 min, interactive)
4. The negotiation proper (~8 min, interactive, player-driven)
5. Snippet moment — mid-negotiation, when words become more than words (~2 min)
6. Resolution and convergence — released into caravan master's custody (~3 min)

**Target:** 20-25 minutes.

#### CREATION TASKS

- [ ] Resolve the design questions above
- [ ] Write scenario following tightened segment structure
- [ ] Determine NPC(s) — who the Bridge negotiates with
- [ ] Establish convergence path (caravan master custody, owes service as translator)
- [ ] Write snippet (the moment when the Bridge's words carry weight they don't understand)

---

### 5. VISIONARY 📋 Sketch only

**Status:** Concept sketch in Sessions_Structure.md. No scenario written.

**Engine:** Action under pressure. Immediate crisis. No time for foresight.

**The Choice:** Act on instinct vs. try to interpret the tool's flashes. Trust the body or trust the vision.

**Spectator Appeal:** HIGH. Adrenaline. Immediate stakes. Visible danger.

#### SCENARIO SKETCH

**Location:** Mid-crisis. The Visionary is ALREADY with the caravan (or near it) when disaster strikes.

**Tool Discovery:** Crystal/mirror/oracle device — showing flashes but too fast to interpret. Images arriving and vanishing before meaning can be extracted.

**Thematic Irony:** Once saw centuries ahead. Now has seconds to react.

#### DESIGN QUESTIONS TO RESOLVE

- **What's the specific crisis?** Needs to be physical, visible, immediate. Options:
  - Landslide blocking a mountain pass with people on both sides
  - Fire in a caravanserai with people trapped
  - Bandits attacking the caravan (overlaps with Warrior's protection theme — less ideal)
  - Flash flood in a canyon the caravan is passing through
  - Avalanche/rockfall during a mountain crossing
  - Best option is probably something geographic/environmental rather than combat — preserves the Warrior's unique claim on "protection from people" while giving the Visionary "protection from nature/chaos"
- **The tool's flashes:** What does the Visionary see? Possibilities:
  - Flash-images of what's ABOUT to happen, arriving too fast to process — essentially split-second premonitions that the player must decide whether to act on before understanding them
  - Images of the WRONG timeline — what happens if they DON'T act
  - Fragmentary instructions — "left," "down," "now" — without context
  - The GM describes a flash, the player has to decide whether to act on it BEFORE the GM explains what it meant. This could be mechanically interesting: trust the vision or trust your eyes.
- **The Visionary's structural position:** They're already at or near the caravan. They might be the first hero the caravan encounters, or they might be a recent arrival themselves. After the crisis, they've PROVEN themselves through action — the caravan trusts them because they just saved lives.

#### STRUCTURAL NOTES

This should be the fastest awakening. No slow build. No gradual context. The scenario starts in motion:

1. Waking INTO crisis — you're running, or falling, or the ground is shaking (~2 min, prose, IMMEDIATE)
2. Tool flashing — images arriving too fast (~2 min, GM describes flashes, player reacts)
3. First decision — act on a flash or on instinct (~3 min, interactive)
4. Escalation — crisis worsens, more flashes, faster decisions (~3 min, interactive)
5. Snippet moment — one moment of crystalline clarity amid chaos (~2 min)
6. Resolution — crisis averted (or mitigated), caravan saved/reached (~3 min)

**Target:** 15-20 minutes. The shortest awakening, and that's a FEATURE. The Visionary doesn't get time to reflect — that IS the test.

#### CREATION TASKS

- [ ] Choose specific crisis (environmental disaster preferred)
- [ ] Design the flash-image mechanic (GM describes, player decides before explanation)
- [ ] Write scenario — tight, fast, minimal prose, maximum interaction
- [ ] Write snippet (the moment of stillness — what foresight USED to feel like)
- [ ] Establish convergence position (Visionary already proven to caravan)

---

### 6. SACRIFICER 📋 Framework only

**Status:** Choice architecture established. Specific situation TBD.

**Engine:** Emotional/ethical. Woven into convergence, not a standalone awakening.

**The Choice:** Leave the group to stop being a burden, or stay and accept that receiving is a form of participation.

**Spectator Appeal:** Integrated into convergence — not a separate spectator experience.

#### STRUCTURAL INNOVATION

The Sacrificer is NOT a standalone awakening. They are already traveling with the caravan when Session 0 begins. Their "awakening" plays out during Act 2 convergence, woven between the arrivals of the other heroes.

**What this solves:**
- Reduces Act 1 to five standalone awakenings (time savings)
- Makes convergence dramatically richer (not just "everyone arrives")
- Gives the Sacrificer a unique structural position: they KNOW the caravan NPCs
- The Sacrificer's player can serve as GM creative partner during Act 1

**The Sacrificer's player role during Act 1:**
- Briefed in advance: "You've been with this caravan for three days"
- Knows the caravan NPCs, has opinions, has relationships
- Can be the connective tissue during convergence
- Has more context than any other player about the caravan's dynamics
- This is a GIFT, not a disadvantage — it must be presented as such

#### CHOICE ARCHITECTURE (Established)

The Sacrificer's core pattern: I give, therefore I am.

The test: what happens when giving IS the problem? Not "will you accept help" (passive) but "will you STOP helping when helping is causing harm?"

**Option A — Leave:** Remove yourself as a burden. Walk away. "I won't be the reason anyone else suffers." Noble-sounding but actually selfish — prioritizes self-image over community. Echoes legendary failure: walking away from unfinished duty.

**Option B — Stay and recalibrate:** Accept limits. Let the relationship be reciprocal. Admit you're finite. Harder because it means your help has a ceiling.

**Snippet trigger:** The moment of choosing — the memory of another time when helping became hurting, when sacrifice tipped from noble to destructive.

#### SITUATION — TBD

The choice architecture is solid. The specific situation that earns it is not yet resolved.

**What we know it ISN'T:**
- Not a caravan-wide resource crisis (math doesn't math, makes leadership look incompetent)
- Not "starving yourself to feed others" (too obvious, too simple)
- Not something that makes the caravan revolve around the Sacrificer (they're a thread, not the center)

**What it needs to be:**
- A personal relationship, not a systemic problem
- A situation where the Sacrificer's giving is visibly costing them AND visibly burdening the recipient
- A currency of sacrifice that isn't food/health (something else the Sacrificer gives that's equally costly)
- Earnable, turnable, and resolvable inside ~15 minutes during convergence
- The confrontation should come from the person being helped, not from authority

**Design question still open:** What is the Sacrificer giving, to whom, and why does the recipient eventually say "stop"?

#### TOOL NOTES

The ritual implement is present but dormant. Not doing anything magical. Just warm to the touch sometimes. The cost is behavioral and narrative, not mechanical. No class dependency — works regardless of what the player eventually builds.

The tool responds to whichever choice the Sacrificer makes — warmth, a pulse, recognition. Not magic. Just acknowledgment. As if it's been waiting to see what they'd do.

**Tool (framework proposal, 2026-03-20):** Balance scale with one pan missing — can measure what is given, has no instrument for what returns. Voice: offers — presents the cost of any action with perfect clarity, never argues, never demands. The missing pan is the surrendered certainty that sacrifice is a transaction. *Surrendered layer: Volitional — the right to refuse; what I can choose to withhold.*

#### CREATION TASKS

- [ ] Resolve the specific situation (what currency of sacrifice? what relationship? what forces the confrontation?)
- [ ] Brief the Sacrificer's player on their caravan role (pre-Session 0)
- [ ] Design the convergence integration (which arrivals interleave with which Sacrificer beats?)
- [ ] Write the snippet
- [ ] Establish NPC(s) the Sacrificer has bonded with
- [ ] Determine how the tool's dormant presence manifests

---

## NOTES ON SESSIONS_STRUCTURE.md

The locked Sessions_Structure.md currently specifies:
- "~40-45 minutes per individual awakening scenario"
- "Time Allocation: 4-5 hours total"

These numbers need updating to reflect the graduated model. However, Sessions_Structure is marked as "locked_structure." 

**Recommendation:** Add an addendum to Sessions_Structure referencing this document as a revision to the timing model, rather than rewriting the locked structure. The structural SEQUENCE (individual awakenings → convergence → recognition) hasn't changed. Only the per-awakening durations and the Sacrificer's structural position have been revised.

---

## THE CONVERGENCE SLOT: A Structural Role, Not an Archetype

The Sacrificer currently occupies a unique structural position: *already on the caravan*, awakening woven through Act 2 convergence rather than as a standalone Act 1 scenario. This is a **slot**, not a personality. Any archetype can fill it.

**What the convergence slot requires of its archetype:**
- A doubt that plays out through *relationship*, not isolated crisis
- A tool that is dormant or ambiguous at first — its nature revealed through interaction, not confrontation
- An arc that can be threaded between other heroes' arrivals without losing momentum

**If the Sacrificer is replaced in this slot** by another archetype (e.g. Keeper, Healer), the replacement inherits the structural position. The Sacrificer doesn't disappear — they become one of the following:

**Option A — NPC Companion:** The Sacrificer traveled with the caravan but is not a player character. They have a voice, a presence, opinions. Players may eventually realize who this person was. A slow reveal.

**Option B — Posthumous Hero:** The Sacrificer's awakening *already happened* — and they didn't survive it. Their tool is passed to the party as an inheritance: *"He gave everything. He left us this."* The contested-site pattern applies with a grim twist: the forces opposing the heroes *won* at that site. This is the only awakening where the dark side's interception succeeded — and the tool carries that weight. Dramatically potent. Use carefully.

---

## AWAKENINGS BEYOND SESSION 0: In-Play Dramatic Moments

**Any awakening scenario not used in Session 0 remains available as an in-play event.**

When a new archetype joins mid-campaign — whether a replacement character, a late arrival, or a player added to the table — their awakening scenario is not discarded. It becomes a *dramatic revelation*: the party witnesses (or participates in) a moment of contested cosmological deployment, with full awareness of what they're seeing.

This transforms what would be a private Session 0 experience into:
- **A hint** — the forces at play are visible to players who now know what to look for
- **A demonstration of stakes** — the power and danger of the immune system vs. Wizard's agents, shown rather than told
- **A dramatic moment** — the new character's arrival is an *event*, not just an introduction
- **A retroactive reframe** — players may look back at their own awakenings differently

The contested-site pattern (see below) applies to *all* archetypes for this reason — even those unlikely to appear in Session 0. When written, every awakening should carry GM notes about what cosmological forces were present, what they wanted, and what the outcome of their conflict was.

---

## THE SURRENDERED-LAYER FRAMEWORK

*Derived from comparative analysis of the three completed awakening scenarios (Warrior, Seeker, Breaker). Session: 2026-03-20. Status: proposed — not yet locked. Cross-reference: `TOOL_EVOLUTION_FRAMEWORK.md` §Tool Personalities.*

### The Core Principle

**Each tool is the specific attribute surrendered at the threshold.** The tool's behavior — its voice, its resistance, its hunger — is the exiled self trying to reclaim primacy. The awakening's crisis is always the same question: *will the hero let the surrendered thing come back?*

This emerged from reading the three written awakenings against each other. The Seeker's tome whispers certainty back; the Warrior's blade howls for force; the Breaker's hammer says *"I'm right here"* — offering identity back. Three different tools, three different voices, three different tests. The pattern is consistent and generative.

**Why this matters at scale:** With ten archetypes, pattern-drift is a real risk. Without a governing framework, later awakenings may feel lighter or derive their weight from different mechanics. This framework keeps all ten grounded in the same ontological engine.

---

### Three Design Variables

Every awakening is anchored in these three:

| Variable | What it determines |
|---|---|
| **The surrendered layer** | What specific kind of self was given up at the threshold |
| **The tool's voice** | Follows from the archetype's relationship to their surrendered thing |
| **The crisis test** | The specific action the hero must take that their surrendered self *cannot* perform |

---

### The Surrendered Layers — Full Taxonomy

Different archetypes surrender at different depths of self. These layers are meaningfully distinct — a Seeker and a Warrior both "feel uncertain" on waking, but for different reasons, because the loss is at a different level.

| Archetype | Layer | What they gave up |
|---|---|---|
| Seeker | **Epistemic** | How I know — certainty as operating system |
| Warrior | **Tactical** | How I solve — force as the clean answer |
| Breaker | **Ontological** | Who I am — identity defined by what I can destroy |
| Bridge | **Relational** | Who I am through connection — the right to have a side |
| Sacrificer | **Volitional** | What I can choose to withhold — the right to refuse |
| Visionary | **Perceptual** | What I can choose not to see — the right to look away |
| Trickster | **Authenticating** | The right to be believed when telling the truth |
| Crafter | **Receptive** | The experience of the world as finished/complete |
| Sentinel | **Doxastic** | The ability to trust without evidence — the experience of safety |
| Healer | **Restorative** | The certainty that wholeness is possible |

---

### Tool Proposals and Voice Character

The tool's voice mirrors the archetype's native relationship to their surrendered thing.

| Archetype | Proposed Tool | Voice character |
|---|---|---|
| Seeker | Tome | Argues, whispers, seduces through reason |
| Warrior | Iron blade (bone-wrapped grip) | Howls — pre-verbal, embodied, instinctive |
| Breaker | Crude heavy hammer | Comforts — *"I'm right here"* |
| Bridge | Knotted silk cord | Aches — the weight of never landing on one shore |
| Sacrificer | Balance scale, one pan missing | Offers — presents cost with perfect clarity, cannot measure return |
| Visionary | Polished obsidian disk | Shows — silent, directional; layers visions over the present |
| Trickster | Shaved coin | Mirrors — sounds exactly like the hero's own voice |
| Crafter | Worn whetstone (asymmetric from use) | Persists — *"one more pass"* — never urgent, never satisfied |
| Sentinel | Cracked lantern (one pane missing) | Points — illuminates without distinguishing real threat from fear |
| Healer | Bone needle threaded with silk | Insists — the physical pull toward the next wound; the thread runs shorter |

**Note on existing stub conflicts:** The stubs below (written before this framework) assigned different tools to some archetypes. Where there is a conflict, both the original stub tool and the framework proposal are noted in the stub. The framework proposals have stronger design rationale; the stub tools were quick sketches. Resolution is a creative decision, not a correction.

**Note on Seeker/tome vs. TOOL_EVOLUTION_FRAMEWORK bow:** TOOL_EVOLUTION_FRAMEWORK Stage 0 examples list "rough-carved bow" for the Seeker, and the archetype-class matrix has Seeker + Ranger → Bow. The written Seeker awakening uses a tome. These are reconcilable if the tome is the archetype-level tool (used when the Seeker takes a Wizard/Scholar class) and the bow is the class variant. This discrepancy should be resolved before Character Creation documentation is finalised.

---

### The Crisis Test Pattern

Each test demands something the surrendered self *cannot* perform — the action that proves the hero is more than what they gave away:

- **Seeker:** Walk west without the tome's certainty — act on instinct the tome cannot validate
- **Warrior:** Stand still while the blade howls — hold the flood, let the threat pass unengaged
- **Breaker:** Leave the hammer knowing it does more good without you — walk away from the thing that defines you
- **Bridge:** Act in a way that serves neither side — exist purely as the crossing when every instinct says *pick one*
- **Sacrificer:** Withhold the obvious offering — refuse, when the scale has no instrument for the cost of refusal
- **Visionary:** Stop looking and move — act on incomplete sight before the disk shows one more layer
- **Trickster:** Be nakedly, genuinely honest and be believed — without performing the honesty
- **Crafter:** Put the tool down before the work is complete — because the perfection it's reaching for will outlast the window for what matters
- **Sentinel:** Trust — stop watching, allow vulnerability — because the vigil has become the cage for the people being protected
- **Healer:** Accept that something cannot be mended — stop healing, let the wound be what it is — because continuing is for the Healer's need, not the patient's

---

### Design Checklist (Per New Awakening)

Use this to evaluate any awakening scenario before it's written or finalised:

1. **Name the layer** — what kind of self was surrendered (epistemic, tactical, ontological, relational, volitional, perceptual, authenticating, receptive, doxastic, restorative)
2. **Define the tool's voice** — its character follows from the archetype's relationship to their lost thing
3. **Build the crisis** — place the hero in direct confrontation with the surrendered thing's claim to return
4. **Write the test** — the specific action their surrendered self *cannot* perform
5. **Snippet trigger** — the memory that surfaces is always: *"you've faced this choice before"*

---

## PROPOSED ARCHETYPE AWAKENING STUBS

The following stubs establish the awakening *concept*, structural slot, and contested-site pattern for proposed archetypes. Full scenarios to be written when/if the archetype enters play. See [[PLAYER_ARC_SYNTHESIS]] for narrative priority ranking and substitution guidance.

Each stub answers three questions:
1. **Where/how do they wake?** (setting and immediate crisis)
2. **What is the contested-site dynamic?** (what forces were present, what did each want)
3. **What structural slot do they occupy?** (standalone Act 1 position, or convergence slot)

---

### SENTINEL (Watcher/Witness) — Priority: HIGH

**Awakening concept:** Wakes with perfect, paralysing clarity — sees everything unfolding around them, understands context immediately, cannot act. The crisis demands intervention before the Sentinel can decide whether witnessing is enough.

**Structural slot:** Standalone, Act 1. Likely replaces the Visionary (see [[PLAYER_ARC_SYNTHESIS]]). Inherits the Visionary's fast/explosive pacing — 15-20 minutes.

**Contested-site dynamic:** The immune system placed the Sentinel at a site of *ongoing injustice* — not disaster, but a slow wrong in plain sight. The Wizard's agents weren't hunting the Sentinel specifically; they were already operating at this site. The Sentinel wakes into the middle of enemy activity they are uniquely positioned to observe. The tension: the agents don't know the Sentinel is there yet. Every moment of watching is also a moment of exposure risk.

**Tool (original stub):** Recording device (journal, memory stone). Present and active from the first moment — recording everything, including the Sentinel's own hesitation.

**Tool (framework proposal, 2026-03-20):** Cracked lantern — one pane missing, asymmetric light, cannot be extinguished. Voice: points without speaking; illuminates corners the Sentinel wasn't watching; cannot distinguish real threat from fear. *Conflict with original stub: recording device implies an epistemic/witness function; cracked lantern implies doxastic/vigilance function. The stub's Sentinel "wakes with perfect paralysing clarity" — if that's the core identity, the recording device may be more accurate. Resolve before writing full scenario.*

**Surrendered layer (framework):** Doxastic — the ability to trust without evidence; the experience of safety.

**In-play variant note:** If this awakening happens mid-campaign, the party may recognise the agents present. The Sentinel's arrival becomes an intelligence windfall — and a race to extract them before the agents realize what they saw.

---

### KEEPER (Guardian/Preserver) — Priority: HIGH

**Awakening concept:** Wakes surrounded by something precious being destroyed — an archive, a sacred site, cultural artifacts being stripped for materials. The instinct to protect is overwhelming. The tool is *already working*, shielding something, when the Keeper becomes aware.

**Structural slot:** Convergence slot candidate (replaces Sacrificer if needed). The Keeper's doubt — *is preservation wisdom or cowardice?* — plays out well through relationship and accumulated small choices rather than a single crisis. Alternatively: standalone Act 1, 20-25 minutes, placed 4th (Bridge's current slot) if the Bridge is deprioritised.

**Contested-site dynamic:** The immune system chose a site of genuine cultural significance — something worth protecting that also provides *cover*. The Wizard's agents are present not to hunt the Keeper but to *acquire* something at the site: knowledge, an artifact, a strategic resource. The Keeper wakes between them and it. Their protection instinct and the agents' acquisition goal are in direct conflict before the Keeper understands what's happening.

**Tool:** Key, seal, or ward — already locked around something. The Keeper doesn't choose to protect; they wake having already done it.

**Posthumous variant:** If the Keeper fills the posthumous slot, what they died protecting becomes a party resource — a place, a cache of knowledge, an artifact. The cost of their death is written into the thing they saved.

---

### TRICKSTER (Deceiver/Subverter) — Priority: MEDIUM-HIGH

**Awakening concept:** Wakes not knowing who they are — genuinely. Multiple potential selves compete. They are already *in a role* before they're conscious enough to have chosen it. The crisis: someone is about to act on a mistaken belief about who the Trickster is, and the Trickster must decide whether to correct it or play it out.

**Structural slot:** Standalone Act 1, 20-25 minutes. Best placed late (4th or 5th) — the audience needs to trust the GM's tone before watching a scenario built on deliberate uncertainty. Not a first awakening.

**Contested-site dynamic:** The Wizard's agents placed someone here expecting the Trickster — they know an expulsion occurred nearby. But they're looking for the *wrong face*. The immune system's protection was elegant: the Trickster landed already wearing cover. The agents are present, close, and looking. The Trickster's natural gift is the only thing keeping them hidden — and they don't know they have it yet.

**Tool (original stub):** Mask, cloak, or mirror. Showing faces. The Trickster doesn't know which one is real. Neither do the agents.

**Tool (framework proposal, 2026-03-20):** Shaved coin — filed on one side, passes as genuine but isn't true weight. Voice: sounds exactly like the Trickster's own voice, because it IS — the original face, which learned to perform sincerity so well it can no longer locate the original. *The stub's mask/mirror and the framework's coin serve different mechanics: mask = identity switching; coin = authenticity collapse. The coin may be more precise for the surrendered layer. Both are compatible with the contested-site dynamic.*

**Surrendered layer (framework):** Authenticating — the right to be believed when telling the truth.

**In-play variant note:** Highest dramatic potential of any mid-campaign awakening. The party witnesses a person who doesn't know who they are being hunted by people looking for someone who doesn't exist. The Trickster's arrival is a puzzle the party is uniquely positioned to help solve — if they don't accidentally blow their cover first.

---

### CRAFTER (Builder/Maker) — Priority: MEDIUM

**Awakening concept:** Wakes surrounded by wreckage — structural, mechanical, human. The instinct to *fix* is immediate and practical. The tool suggests designs the Crafter's hands remember building but their mind doesn't recognise.

**Structural slot:** Standalone Act 1, 20-25 minutes. Interchangeable with Bridge in the 4th position — both provide an energy shift after heavier pieces.

**Contested-site dynamic:** The immune system placed the Crafter at a site of *functional collapse* — infrastructure the world needs and that the Wizard's forces damaged deliberately. The agents aren't hunting the Crafter; they caused the damage and may still be present, ensuring it isn't repaired. The Crafter wakes into the aftermath of enemy action, surrounded by evidence of what the dark forces are willing to destroy.

**Tool (original stub):** Crafting implement (hammer for shaping, not smashing — see Breaker distinction). Already warm, as if recently used.

**Tool (framework proposal, 2026-03-20):** Worn whetstone — asymmetric from use, consumed by the act of improving other things. Voice: persistent, non-urgent — *"one more pass."* Cannot reach a finished state; its own material is spent in the service of perfection. *The stub's "crafting implement" and the whetstone are compatible; the whetstone is a specific proposal within that category with stronger voice character. The Crafter distinction from the Breaker (shaping not smashing) is preserved — the whetstone refines, it does not break.*

**Surrendered layer (framework):** Receptive — the experience of the world as finished/complete.

---

### HEALER (Mender/Restorer) — Priority: LOW-MEDIUM

**Awakening concept:** Wakes to someone in immediate need. The instinct to help is total. The crisis reveals itself as the Healer works: the wound is a symptom of something that cannot be healed — only confronted.

**Structural slot:** Convergence slot candidate. The Healer's arc (giving comfort vs. forcing confrontation) suits the woven, relational structure of Act 2. If neither Sacrificer nor Healer is in the convergence slot, this awakening works as a standalone 4th position, 20-25 minutes.

**Contested-site dynamic:** The immune system placed the Healer at a site of *recent harm* caused by the Wizard's agents — people hurt, community damaged. The agents are gone but their work remains. The Healer wakes into consequence, not confrontation. What they do with that consequence — treat the symptoms or follow the cause — is the first test of their doubt.

**Tool (original stub):** Mending implement (needle, salve-pot, restorative staff). Warm, willing, present. Unlike most tools, it doesn't resist immediately — it *wants* to be used. The resistance comes later, when the Healer reaches for it to avoid a harder truth.

**Tool (framework proposal, 2026-03-20):** Bone needle threaded with silk — the instrument of suturing; reconnects what has been severed. Voice: insists through physical sensation — the pull of thread through tissue, the tension that holds a seam. The silk thread is finite, getting shorter. Holds the record of every wound closed, and knows which ones reopened. *Consistent with the stub's needle option; the silk thread grounds it in the Silk Road setting and adds the specific voice character of diminishment — the Healer's resource is visibly finite in a way that generates the right doubt.*

**Surrendered layer (framework):** Restorative — the certainty that wholeness is possible.

---

## CROSS-REFERENCE NOTE

Awakening stubs are intentionally minimal here. Full cosmological detail for each site lives (or will live) in the individual awakening scenario files. The Wizard's-side perspective on the contested awakenings is in [[WIZARD_AND_LICH_CADRE]] §Phase 4.

---

## Remote Player Accommodation Models

Three structural models for intermittent or remote players. Content to be recovered and written from Feb 14 2026 chat session.

- [ ] Write Model A: Recurring Wanderer
- [ ] Write Model B: Anchor Point
- [ ] Write Model C: Convergence Player

(This is a stub placeholder — the actual content reconstruction is a separate session's work)

---

*Document Status: Working draft. February 2026 design sessions + proposed archetype stubs and convergence slot architecture added 2026-02-19. Remote player accommodation models stub added 2026-03-07. Surrendered-Layer Framework + tool proposals for all 10 archetypes added 2026-03-20. Not yet canon — requires Mo's review and approval before integration into locked structures.*
