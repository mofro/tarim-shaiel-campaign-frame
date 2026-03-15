---
# ── REQUIRED ──────────────────────────────────────────────────────────────────
name:                       # Canonical name (used in all wikilinks)
type: landmark
created:
last_updated:

# ── IDENTITY ──────────────────────────────────────────────────────────────────
landmark_type:              # geographic | structural | mystical | natural | ruins | route
parent_region:              # [[../regions/region-name]] — region this landmark belongs to

# ── MAP (OPTIONAL) ────────────────────────────────────────────────────────────
# Only needed if this landmark warrants its own map pin (vs. being implied by region)
location:                   # [lat, long] — optional
mapmarker:                  # optional — sacred-site | marker-dungeon | city | etc.

# ── CONTENTS ──────────────────────────────────────────────────────────────────
# POI files that are sub-elements of this landmark — transcluded in body below
contains_poi: []            # e.g. [[../locations/duskwatch-outpost]], [[../locations/the-high-falls]]

# ── FACTIONS ──────────────────────────────────────────────────────────────────
factions_present: []        # Canonical wikilinks — local flavor in Faction Presence section
factions_claiming: []       # Factions asserting control or ownership
factions_seeking: []        # Factions who want this but don't have it

# ── NARRATIVE ─────────────────────────────────────────────────────────────────
description:                # One-sentence player-facing summary
narrative_weight:           # very-high | high | medium | low
campaign_arcs: []

# ── STATUS ────────────────────────────────────────────────────────────────────
status:                     # canon | draft | tbd
visibility: public          # public | secret
danger_level:               # 1–5 (1 = safe, 5 = existential)

tags:
  -                         # player-visible | gm-only | secret
  -                         # campaign-arc-[name]
  - type-landmark
---

```leaflet
id: landmark-[filename-slug]
coordinates: [[world/locations/[filename-slug]]]
defaultZoom: 8
minZoom: 4.5
maxZoom: 18
height: 400px
osmLayer: false
tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite (No Labels)
tileOverlay:
  - https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png|Labels
geojson:
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations
```

# [Landmark Name]

> [One sentence: what do you feel before you understand what this place is? Not description — sensation.]

---

## Distinctions

*Smaller in scale than regional Distinctions — these are the qualities specific to this landmark that a GM should hold while running any scene within it.*

### [Quality Name — e.g. "The Paths That Know You"]
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

## What It Is

[Scale, physical character, how you move through it. A landmark is traversed, not just visited. How long to cross? What's the dominant feature? What's the relationship between its parts?]

**Scale:** [Approximate size, travel time]
**Terrain:** [What you're moving through]
**Access:** [How do you enter? Are there routes, barriers, permissions needed?]

---

## Denizens

[Who or what inhabits this landmark? Not factions — creatures, communities, custodians, spirits. The Titan's Steps has Mountain Crabs and Spire Keepers. The Open Vale has the Stones. What lives here that belongs to the landmark itself?]

- **[Denizen name]:** [What they are, how they relate to the landmark, what they want]
- **[Denizen name]:**

---

## Faction Presence

*How each faction operates specifically within this landmark — local flavor only. Wikilink to canonical file.*

| faction | local role | what they want here | tension |
|---------|-----------|-------------------|---------|
| [[../factions/\|]] | | | |

---

## Notable Features & Sub-Elements

*Each sub-element is its own POI file, transcluded here for a cohesive read.*

![[poi-filename]]

![[poi-filename]]

![[poi-filename]]

---

## Environment

*Link to the associated Environment file for encounter/scene design mechanics.*

→ [[../environments/[filename]|[Environment Name]]]

*If this landmark contains multiple distinct environments (e.g., the approach vs. the interior), list each.*

---

## Connected Events

| event | connection |
|-------|-----------|
| [[../events/\|]] | [Built during / site of / affected by] |

---

## Connected Concepts

| concept | relevance |
|---------|-----------|
| [[../concepts/\|]] | |

---

## What Players Know

[Common knowledge — what merchants, scholars, or locals say about this place.]

**Rumors:**
- [Rumor that may or may not be true]
- [Rumor]

---

## DM Notes

**The real truth:** [What this landmark actually is beneath its reputation]

**Wizard's awareness:** [Does he know? Has he sent agents? Is it in his plan?]

**Ecosystem status:** [Is the Mythic Ecosystem intact here? Is this a pressure point?]

**If players fully explore this:**
[What do they learn? What's irreversible?]

**Adventure hooks:**
1. [Hook from the landmark's nature]
2. [Hook from its denizens or faction tension]
3. [Hook tied to campaign arc]

---

## References
- Parent region: [[../regions/|]]
- [[../factions/Index|Factions Index]] | [[../events/Index|Events Index]] | [[../concepts/Index|Concepts Index]]
