---
# ── REQUIRED ──────────────────────────────────────────────────────────────────
name:                       # Canonical region name (used in all wikilinks)
type: region
created:
last_updated:

# ── IDENTITY ──────────────────────────────────────────────────────────────────
region_analog:              # Real-world geographic/cultural reference (internal use only)
era_established:            # Era when this region took its current political form

# ── CONTENTS ──────────────────────────────────────────────────────────────────
# Use canonical filenames — these drive Dataview and the relationship graph
contains_landmarks: []      # e.g. [[../locations/jade-gate]]
contains_settlements: []    # e.g. [[../locations/kashkar]], [[../locations/khotan]]
contains_poi: []            # Standalone POIs within this region (not sub-elements of anything)

# ── FACTIONS ──────────────────────────────────────────────────────────────────
# Canonical wikilinks only — local flavor goes in the Faction Presence section below
factions_dominant: []       # Faction(s) with primary power here
factions_present: []        # Other factions operating in this region
factions_hidden: []         # Factions with non-obvious influence

# ── NARRATIVE ─────────────────────────────────────────────────────────────────
narrative_weight:           # very-high | high | medium | low
campaign_arcs: []

# ── STATUS ────────────────────────────────────────────────────────────────────
status:                     # canon | draft | tbd
visibility: public          # public | secret

tags:
  -                         # player-visible | gm-only
  -                         # campaign-arc-[name]
  - type-region
---

# [Region Name]

> [One sentence: what does it feel like to travel through this region? Not what it contains — what it *is*.]

---

## Distinctions

*The named qualities that define this region's character. These cascade to every location within it — a GM running any settlement or landmark here should feel these as the backdrop.*

### [Quality Name — e.g. "Water as Currency"]
[2–3 sentences describing this quality — political, cultural, atmospheric, or physical.]

**You might encounter:**
- [Sensory or situational detail]
- [Sensory or situational detail]
- [Sensory or situational detail]

### [Quality Name — e.g. "The Open Secret"]
[2–3 sentences.]

**You might encounter:**
- [Detail]
- [Detail]
- [Detail]

### [Quality Name]
[2–3 sentences.]

**You might encounter:**
- [Detail]
- [Detail]
- [Detail]

---

## GM Principles

*Named tonal directives for running this region consistently. Every scene here should honor at least one of these.*

**[Principle Name — e.g. "Power Through Infrastructure, Not Force"]**
[1–2 sentences explaining what this means in practice and how to express it at the table.]

**[Principle Name]**
[1–2 sentences.]

**[Principle Name]**
[1–2 sentences.]

---

## Political Reality

**Visible governance:** [[../factions/|]]
**Hidden power:** [[../factions/|]]
**Nature of that relationship:** [Tense? Cooperative? Exploitative? Does anyone else know?]

**Regional tensions:**
- [Faction vs. faction or resource pressure]
- [Historical grievance or structural vulnerability]
- [External threat or opportunity]

---

## Faction Presence

*How each faction operates specifically in this region. Wikilink to canonical file; notes here are regional context only.*

| faction | regional role | primary leverage | key tension |
|---------|--------------|-----------------|-------------|
| [[../factions/\|]] | | | |
| [[../factions/\|]] | | | |

---

## Geography & Scale

[Physical character — terrain, climate, travel scale. What makes this feel distinct from neighboring regions?]

**Borders:** [Neighboring regions or natural features]
**Key routes:** [Named trade or travel routes]
**Water & resources:** [Rivers, oases, irrigation — what sustains life here]

---

## Contained Locations

*Set `parent_region` in individual files and Dataview will auto-populate. Manual list until then.*

**Landmarks:** [[../locations/|]]

**Settlements:** [[../locations/|]]

**Standalone POIs:** [[../locations/|]]

---

## Historical Context

**Era 0 (~200 CE):** [Role under the Empire]
**Era 1–2 (250–700 CE):** [How the Scattering reshaped this region]
**Era 3–4 (700–1200 CE):** [Stabilization or continued transformation]
**Campaign Present:** [Current state — who's winning, what's fragile]

---

## Campaign Relevance

[What would players find here that they couldn't find anywhere else? What does this region contribute to the main arc?]

**Wizard's presence:** [Agents, knowledge, or interest in this region]
**Ecosystem status:** [[../concepts/mythic-ecosystem|Mythic Ecosystem]] — [Intact / stressed / showing cracks]

---

## DM Notes

**Hidden truths:**
- [Something players won't learn until mid-campaign]
- [A faction relationship that isn't what it seems]

**If players fully investigate this region:** [What do they learn? What changes?]

**Adventure hooks:**
1. [Hook from faction tension]
2. [Hook from geography or resources]
3. [Hook tied to Wizard's plan or ecosystem]

---

## References
- [[../factions/Index|Factions Index]] | [[../events/Index|Events Index]] | [[../concepts/Index|Concepts Index]]
- [[../content/REGIONAL_FACTIONS_AND_POWER_DYNAMICS|Regional Factions & Power Dynamics]]
- [[../content/HISTORICAL_TIMELINE|Historical Timeline]]
