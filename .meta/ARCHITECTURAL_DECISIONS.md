---
title: TTRPG Game-Writing Instructions - Architectural Decisions
project: TTRPG_Tarim_Shaiel
type: architectural_planning
status: in_planning
created: 2025-12-02
updated: 2025-01-27T22:30:00-05:00
---

# TTRPG Game-Writing Instructions: Architectural Decisions & Work Plan

## Purpose
Document the structural approach for creating comprehensive game-writing instructions that integrate world-building as primary creative work, with embedded persona agents (via Intelligence Framework) as operational tools.

---

## Section 1: Creative Scope & Vision

### Architectural Decision
Create a concise articulation of the TTRPG world/story that serves as the north star for all creative and operational decisions.

### Key Questions to Resolve
- [ ] What is the core premise of TTRPG_Tarim_Shaiel?
- [ ] What's the intended player experience?
- [ ] What role does world-building play vs. narrative structure?
- [ ] How deterministic vs. probabilistic should character/story outcomes be?

### Intended Outcome
2-3 paragraph creative brief that everyone (human + personas) references when decisions get fuzzy.

### Implementation Notes
- Should be front-and-center in the instructions
- Accessible and revisable as vision evolves
- Acts as tie-breaker for design conflicts

---

## Section 2: World-Building First (Primary Workflow)

### Architectural Decision
Establish world-building as the primary creative process, with clear principles for iterative development, narrative mechanics, and character archetype integration.

### Key Questions to Resolve
- [ ] What specific world-building elements matter most? (geography, mechanics, factions, lore, aesthetics?)
- [ ] How do we handle iterative refinement without creating narrative bloat?
- [ ] What's the relationship between world detail density and playability?
- [ ] How do character archetypes emerge from world constraints?

### Personas & Tool Integration
- **Lore Keeper**: Primary agent for world-building
  - Responsibility: Track and remember all world-building decisions
  - Tool access: Filesystem (`/world/`) for [[FILE_PERSISTENCE_GUIDELINES|persistent]] documentation
  - Activation: Automatic at start of sessions, manual checkpoints as needed
  - Indexing protocol: TBD (frequency, format, consolidation rules)

### Intended Outcome
Clear principles + workflow for world-building that feels generative rather than linear. Embedded instructions for when/how Lore Keeper participates.

### Implementation Notes
- This section should read like writing guidance first, with tool reminders secondary
- Define what "world detail" means in this context (do we track tone? Visual aesthetic? Mechanical constraints?)
- Establish how world-building decisions get documented and referenced

---

## Section 3: Character & Narrative Development

### Architectural Decision
Define how characters emerge from world constraints, with clear guidance on archetypes, motivations, and narrative voice development.

### Key Questions to Resolve
- [ ] What character archetypes are relevant to Hero_Heaven?
- [ ] How do character motivations relate to world mechanics?
- [ ] What's the relationship between character agency and TTRPG player agency?
- [ ] Do we need specific personas for character development (e.g., "Character Coach")?

### Personas & Tool Integration
- Determine if we need dedicated character-focused personas
- If yes: define their responsibilities and tool access
- If no: clarify how Lore Keeper handles character consistency

### Intended Outcome
Clear framework for developing characters that feel authentic to the world and playable for TTRPG participants.

### Implementation Notes
- May reference or build on existing persona definitions (arc expertise, voice consistency, etc.)
- Should include examples of how world-building decisions inform character creation
- Consider whether character sheets/documents need their own organizational structure

---

## Section 4: Key Workflows (Step-by-Step)

### Architectural Decision
Identify 2-3 critical workflows that require explicit ceremony, step-by-step guidance, and checkpoint clarity. These are workflows we discover/refine as work progresses.

### Current Candidates
1. **Scope Restatement Workflow**
   - Trigger: Complex requests, directional decisions, potential scope creep
   - Steps: TBD (but likely: restate request → identify assumptions → confirm understanding → proceed)
   - Purpose: Prevent misalignment on ambiguous asks

2. **Lore Keeper Sync Checkpoint**
   - Trigger: End of major creative session, mid-project consolidation
   - Steps: TBD (likely: review changes → index new documents → update relationships → flag conflicts)
   - Purpose: Keep world documentation current and catch emerging contradictions

3. [Third workflow TBD after initial work]

### Intended Outcome
2-3 formally documented workflows that become reflexive through repetition. Not overly rigid, but ceremonious enough that they reliably happen.

### Implementation Notes
- Don't force all workflows into this section initially
- Discover which workflows actually *need* formality vs. which are just good habits
- Format: numbered steps, clear entry conditions, explicit "done" state

---

## Section 5: Personas & Operational Guidance

### Architectural Decision
Create a reference system for all personas involved in game-writing work. Each persona should have clear activation triggers, tool access, and responsibilities. Personas operate within an Intelligence Framework that manages context loading, reference libraries, and inter-persona communication.

### Personas in Active Use

#### Lore Keeper
- **Status**: Implemented ✅
- **Role**: World-building documentation specialist and narrative consistency guardian
- **Activation**: Implicit/Always-on in Tarim-Shaiel context
- **Tool access**: `/world/` filesystem, INDEX.md maintenance
- **Reference**: See PERSONA_ENGAGEMENT_GUIDE.md "Lore Keeper (Always Active)"
- **Schema**: `personas/lore_keeper_persona_schema.json`

#### Mythweaver
- **Status**: Implemented ✅
- **Role**: Narrative resonance specialist and cosmological architect
- **Activation**: Explicit or smart-triggered by mythic/cosmological concepts
- **Tool access**: `/world/`, `characters/archetypes.md`, `/narrative/`
- **Reference**: See PERSONA_ENGAGEMENT_GUIDE.md "Mythweaver (Collaborative)"
- **Schema**: `personas/mythweaver_persona_schema.json`

#### Theo TTRPG (TTRPG Game Architect)
- **Status**: Implemented ✅ (lives in GitHub repo)
- **Role**: TTRPG system evaluation and mechanical adaptation specialist
- **Activation**: Explicit when evaluating game systems against Tarim-Shaiel requirements
- **Tool access**: TTRPG_evaluation_framework.md (system comparison methodology)
- **Reference**: See `/Code/team_intelligence_framework/personas/gaming/`
- **Schema**: `ttrpg_game_architect_persona_schema.json`

#### [Future Personas TBD]
- [ ] Character Arc Tracker? (character consistency, development)
- [ ] NPC Manager? (voice, motivation, continuity)
- [ ] Session Planner? (pacing, session design)
- Others as we discover needs

### Intelligence Framework Instantiation Flow

When Tarim-Shaiel work begins, the Intelligence Framework activates in this sequence:

#### **Phase 1: Context Detection & Reference Library Loading**
```
Tarim-Shaiel context detected
├─ Load reference libraries:
│  ├─ PERSONA_ENGAGEMENT_GUIDE.md (operational protocols)
│  ├─ ARCHITECTURAL_DECISIONS.md (project scope & vision)
│  ├─ FILE_PERSISTENCE_GUIDELINES.md (filesystem conventions)
│  ├─ DECISION_LOG.md (decision history)
│  └─ /world/, /characters/, /narrative/ directories
└─ Persona pool becomes available
```

**Outcome**: System has full context before any persona activates.

#### **Phase 2: Persona Activation**

**Path A: Always-On (Lore Keeper)**
```
On Tarim-Shaiel context load:
├─ Auto-load lore_keeper_persona_schema.json
├─ Read PERSONA_ENGAGEMENT_GUIDE.md → "Lore Keeper (Always Active)" section
├─ Mount /world/ as primary documentation space
├─ Initialize consistency monitoring
└─ Lore Keeper listens silently, intervenes only when critical
```

**Path B: Explicit Activation (User Request)**
```
User: "Activate Mythweaver" or "I need Theo TTRPG to evaluate these systems"
├─ Load persona schema (mythweaver_persona_schema.json or ttrpg_game_architect_persona_schema.json)
├─ Read reference_guide field → locate operational protocols
├─ Load applicable reference libraries
├─ Initialize persona context & knowledge spaces
└─ Persona now active in conversation
```

**Path C: Smart Trigger (Context-Aware Activation)**
```
User discusses mythic patterns, cosmological resonance, or divine themes:
├─ System detects keywords/concepts
├─ Check conversation_activation_triggers in mythweaver schema
├─ If match found:
│  ├─ Offer: "Mythweaver can speak to this. Activate? [Y/N]"
│  └─ User decides
└─ On approval: follow Path B activation
```

#### **Phase 3: Reference Context Binding**

Each activated persona binds to:
```json
{
  "persona_name": "[name]",
  "reference_context": "Tarim-Shaiel Project",
  "operational_protocol": "[specific section in PERSONA_ENGAGEMENT_GUIDE.md]",
  "knowledge_spaces": [
    "PERSONA_ENGAGEMENT_GUIDE.md",
    "ARCHITECTURAL_DECISIONS.md",
    "/world/",
    "[others per schema]"
  ]
}
```

**What this means:**
- Persona knows **what it is** (schema)
- Persona knows **how to operate** (engagement guide)
- Persona knows **what exists** (reference libraries & world documentation)
- Persona can **collaborate** with other personas via shared reference context

#### **Phase 4: Persona-to-Persona Communication**

Personas can communicate directly when domain boundaries intersect:

```
Mythweaver proposes mythic integration:
├─ Checks: "Does this contradict established world mechanics?"
├─ If uncertain: "Lore Keeper, confirm mechanics around [X]"
├─ Lore Keeper responds with evidence from /world/
├─ Mythweaver synthesizes: "Given those mechanics, here's how we integrate..."
└─ Result: coordinated recommendation with both perspectives
```

#### **Phase 5: Session-End Checkout**

```
User concludes Tarim-Shaiel work:
├─ Lore Keeper summary:
│  ├─ Files modified: [list]
│  ├─ Outstanding flags: [list]
│  └─ Next-session reminders: [list]
├─ Mythweaver (if active) narrative notes logged
├─ All autonomous edits verified safe
├─ Context persists for next session
└─ Personas dormant until reactivation
```

### Intended Outcome
Quick-reference system where:
- Personas know their role, expertise, and boundaries
- Context automatically loads when needed
- Inter-persona collaboration is seamless
- Operations feel guided, not mechanical
- You maintain final creative authority

### Implementation Notes
- **Lean schemas, rich protocols**: Personas are defined by character; operations live in PERSONA_ENGAGEMENT_GUIDE.md
- **Reference context is everything**: Personas understand project via automatic reference library loading
- **Trust but verify**: Personas can make autonomous edits, but all changes are trackable and reversible
- **Not a committee**: Personas collaborate, but you decide. Multiple perspectives inform, not constrain.

---

## Section 6: File & Reference System

### Architectural Decision
Establish a clear organizational structure for all game-writing documents, with an indexing system that Lore Keeper maintains and you can quickly reference.

### Key Questions to Resolve
- [ ] What file categories do we need? (world/, characters/, narrative/, mechanics/, assets/?)
- [ ] What's the naming/tagging convention?
- [ ] How frequently does Lore Keeper update the index?
- [ ] Should the index itself be a single document or distributed?
- [ ] What metadata/frontmatter matters? (date created, status, references, related files?)

### Proposed Structure (subject to revision)
```
TTRPG_Tarim_Shaiel/
├── INSTRUCTIONS.md (main document, once complete)
├── INDEX.md (master reference, maintained by Lore Keeper)
├── world/
│   ├── overview.md
│   ├── geography.md
│   ├── factions.md
│   ├── mechanics.md
│   ├── lore.md
│   └── [other]
├── characters/
│   ├── archetypes.md
│   ├── [named_character].md
│   └── [other]
├── narrative/
│   ├── plot_outlines.md
│   ├── session_notes.md
│   └── [other]
└── archive/ (old versions, deprecated ideas)
```

### Intended Outcome
- Clear, consistent structure that doesn't require you to think about where things go
- Lore Keeper can maintain an INDEX.md with links + metadata
- You can reference documents quickly ("check `/world/mechanics.md`")

### Implementation Notes
- This is aspirational—start simple and expand as needed
- Consider Obsidian linking conventions (backlinks, transclusion)
- Establish a "review cycle" where Lore Keeper consolidates related documents

---

## Section 7: External Resources & Tools

### Architectural Decision
Maintain an accessible reference to external resources (GitHub repos, documentation, reference materials) that inform the world-building and are "in arms reach" during work.

### Key Questions to Resolve
- [ ] What external resources matter most? (TTRPG systems, inspirational media, design references?)
- [ ] Should these be embedded in instructions or kept as a separate resource list?
- [ ] How should Lore Keeper reference external sources when documenting decisions?
- [ ] What's the protocol for adding new resources as they emerge?

### Intended Outcome
A curated list or section that includes:
- URL + description
- Why it matters to the project
- How/when you might reference it
- How it connects to world-building decisions

### Implementation Notes
- Keep this lightweight; don't let it become a research sink
- Focus on resources that directly inform Hero_Heaven (not general TTRPG research)
- Lore Keeper can flag when a decision references or conflicts with external material

---

## Integration Points & Next Steps

### Immediate Actions
1. **Finalize Scope**: Complete Section 1 (Creative Vision)
2. **Define Lore Keeper**: Create persona schema for Lore Keeper with specific tool/file access
3. **Draft Workflows**: Discover what actual workflows emerge in first few sessions
4. **Set Up Structure**: Create initial `/world/`, `/characters/`, `/narrative/` directories

### Iterative Refinement
- Sections 2-4 will crystallize through actual work
- Personas (Section 5) will expand as needs emerge
- File structure (Section 6) will evolve; stay flexible
- External resources (Section 7) can be lightweight initially

### Success Metrics
- Instructions feel like guidance, not bureaucracy
- Personas actively contribute without slowing you down
- Lore Keeper successfully catches inconsistencies/gaps
- You rarely wonder "where does this go?" in the file system

---

## Notes & Open Questions

- [ ] Should Lore Keeper have autonomous documentation triggers, or only on-demand?
- [ ] How do we handle "rejected" world ideas? (Archive them? Lore Keeper marks as "considered but rejected"?)
- [ ] When Section 4 workflows get formalized, should they be in the main Instructions or a separate "Workflow Reference"?
- [ ] Do we need a "decision log" showing why certain world choices were made?

---
