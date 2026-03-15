---
# ── REQUIRED ──────────────────────────────────────────────────────────────────
name:                       # Canonical name — e.g. "The Village of Hush (Social)"
type: environment
created:
last_updated:

# ── MECHANICAL IDENTITY ───────────────────────────────────────────────────────
env_type:                   # Exploration | Traversal | Social | Wilderness | Combat
tier:                       # 1 | 2 | 3 | 4
difficulty:                 # Target number for action rolls in this environment (8–18)

# ── PARENT ────────────────────────────────────────────────────────────────────
# The location this environment represents mechanically
parent:                     # [[../locations/settlement-or-landmark-or-poi]]
parent_type:                # settlement | landmark | poi | region

# ── ENCOUNTER DESIGN ──────────────────────────────────────────────────────────
# What this environment "wants" to do — drives GM behavior
impulses:
  -                         # e.g. "Display Hospitality, Provide Respite from Danger"
  -
  -

# Adversaries appropriate to this environment — use Bestiary names where possible
potential_adversaries: []

# ── STATUS ────────────────────────────────────────────────────────────────────
status:                     # canon | draft | tbd
classification: public      # public | gm-only

tags:
  -                         # player-visible | gm-only
  -                         # campaign-arc-[name]
  - type-environment
  -                         # env-exploration | env-traversal | env-social | env-wilderness | env-combat
---

# [Environment Name]

**Type:** [Exploration / Traversal / Social / Wilderness / Combat]
**Tier:** [1–4] | **Difficulty:** [8–18]

**Description:** [1–2 sentences — what is this place, mechanically? What kind of challenge does it present?]

**Impulses:** [What does this environment want to do? 2–3 drives that shape how the GM uses it.]

**Potential Adversaries:** [Named adversaries or types that fit this environment]

---

## Features

*Each feature is a tool the GM can deploy. Passive features are always true. Actions are triggered by circumstances or GM choice. Reactions fire in response to player actions. Fear spends create escalation.*

*Each feature includes an italic GM question — a prompt to customize the feature for your specific session.*

---

### [Feature Name] — Passive

[What is always true about this environment? What constraint, advantage, or condition applies at all times?]

*[GM question: How does this manifest visually? What clue tells players this feature is in play?]*

---

### [Feature Name] — Passive

[A second persistent condition — environmental, social, or mechanical.]

*[GM question: What variation on this makes it surprising the second time players encounter it?]*

---

### [Feature Name] — Action

[What can the GM trigger mid-scene? A complication, a new actor, a shift in conditions. This costs nothing — it's a natural consequence of being here.]

*[GM question: What specific circumstance in this location makes this action feel inevitable rather than arbitrary?]*

---

### [Feature Name] — Action

[A second triggerable complication.]

*[GM question: How does this action change what the players want to do next?]*

---

### [Feature Name] — Reaction: [Trigger Condition]

[What happens when players do a specific thing — fail a roll, succeed with Fear, push too hard? This fires automatically when its trigger occurs.]

*[GM question: How do you telegraph that this reaction is coming before it fires?]*

---

### [Spend Fear]: [Effect Name]

[What does the GM get when they spend a Fear token here? This should escalate the scene meaningfully — not just add damage, but change the situation.]

*[GM question: What does this look like from the players' perspective? How does the environment itself seem to respond?]*

---

### [Spend Fear]: [Effect Name]

[A second Fear spend — usually higher stakes than the first.]

*[GM question: Does this Fear spend change what's possible in this scene, or just who has leverage?]*

---

## Skill Challenges

*Optional — use when the environment calls for structured non-combat resolution.*

**[Challenge Name] — Progress Countdown ([X])**
[What are players trying to accomplish? What approaches work (which Traits/Skills are applicable)?]

*Complications:* [What obstacles interrupt progress?]
*[GM question: What does partial progress look like? What changes after each step?]*

---

## Group Action Option

*Use when you want to abstract a large encounter and keep momentum.*

[Describe the group action — what is everyone contributing to? What's the main roll?]

**On a Success with Fear:** [Each PC marks X and something changes]
**On a Failure:** [Each PC marks X and the situation worsens]

*[GM question: What does a creative individual contribution look like for each archetype?]*

---

## References
- Parent location: [[../locations/|]]
- Parent region: [[../regions/|]]
- Related factions: [[../factions/|]]
- Campaign arc: [[../../narrative/|]]
