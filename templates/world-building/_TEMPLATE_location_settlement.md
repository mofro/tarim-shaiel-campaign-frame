---
# ── REQUIRED ──────────────────────────────────────────────────────────────────
name:                       # Canonical fantasy name (used in all wikilinks)
location: [lat, long]       # WGS84 array format — MUST be array, not string
type: city                  # city | town | village | waystation | caravanserai | fortress | port
created:
last_updated:

# ── HIERARCHY ─────────────────────────────────────────────────────────────────
parent_region:              # [[../regions/region-name]] — REQUIRED
parent_landmark:            # [[../locations/landmark-name]] — only if nested within a Landmark

# ── MAP DISPLAY ───────────────────────────────────────────────────────────────
mapmarker: city             # city | sacred-site | marker-dungeon (must match Leaflet plugin settings)
fantasy_name:               # If the canonical name differs from what appears on the map label

# ── IDENTITY ──────────────────────────────────────────────────────────────────
known_for:                  # One phrase — what every traveler knows about this place
settlement_type:            # city | town | village | waystation | caravanserai | fortress | port

# ── POLITICAL ─────────────────────────────────────────────────────────────────
# Canonical wikilinks from world/factions/Index.md — NOT free text
factions_visible:           # Faction governing openly
  -
factions_hidden:            # Faction with actual leverage
  -
factions_present:           # Other factions operating here
  -

# ── GEOGRAPHY & TRADE ─────────────────────────────────────────────────────────
elevation:                  # meters
resources: []               # Primary trade goods or local resources
connected_routes: []        # Named trade routes passing through

# ── NARRATIVE ─────────────────────────────────────────────────────────────────
description:                # One-sentence player-facing summary
narrative_weight:           # very-high | high | medium | low
campaign_arcs: []

# ── CONTENTS ──────────────────────────────────────────────────────────────────
# POI files that are sub-elements of this settlement — transcluded in body below
contains_poi: []            # e.g. [[../locations/clover's-tavern]], [[../locations/the-sunless-farms]]
environment_file:           # [[../environments/settlement-name-social]] — link to Environment file

# ── STATUS ────────────────────────────────────────────────────────────────────
visibility: public          # public | secret
status:                     # canon | draft | tbd
is_private: false

tags:
  - player-visible          # player-visible | gm-only | secret
  -                         # campaign-arc-[name]
  - type-city               # type-[value matching settlement_type above]
---

```leaflet
id: location-[filename-slug]
coordinates: [[world/locations/[filename-slug]]]
defaultZoom: 10
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false
tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite (No Labels)
tileOverlay:
  - https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png|Labels
geojson:
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations
```

# [Settlement Name]

> [One evocative sentence. What does a traveler notice first — before they understand what they've arrived at?]

*Known for: [paste known_for value here for inline reader convenience]*

---

## Overview

[2–3 sentences: what this place is, why it exists where it does, and what defines it in the current era. Reader should know what kind of story happens here.]

---

## Political Reality

**Who governs (visibly):** [[../factions/|]]
**Who actually controls:** [[../factions/|]]
**Nature of that relationship:** [Tense? Cooperative? An open secret? Does the visible authority know?]

**Current tensions:**
- [Faction friction]
- [Resource or economic pressure]
- [Connection to regional politics]

---

## Faction Presence

*How each faction manifests specifically here — local flavor only. Canonical file holds the full picture.*

| faction | local role | local leverage | local tension |
|---------|-----------|---------------|--------------|
| [[../factions/\|]] | | | |
| [[../factions/\|]] | | | |

---

## Character & Culture

[What is daily life like? What do people value? 3–5 sentences, player-facing. Tone, not mechanics.]

**Population:** [Approximate — "a few thousand", "tens of thousands"]
**Primary inhabitants:** [Species mix]
**Cultural notes:** [Distinctive customs, architecture, language blend, local idioms]

---

## Rules, Norms & Customs

*The behavioral contracts of this settlement — what every visitor learns, often the hard way.*

- **[Custom name]:** [What it is and what happens if you violate it]
- **[Custom name]:** [What it is]
- **[Custom name]:** [What it is]

---

## Trade & Resources

**Primary exports:** [What this settlement produces or trades in]
**Primary imports:** [What it depends on from outside]
**Strategic value:** [Why this location matters on the map]

---

## Notable Features & Sub-Elements

*Each sub-element is its own POI file. Transcluded here for a cohesive read of the settlement.*

![[poi-filename]]

![[poi-filename]]

![[poi-filename]]

---

## Environment

*Link to the associated Environment file for encounter/scene design mechanics.*

→ [[../environments/|]]

---

## Connected Events

| event | how this settlement relates |
|-------|----------------------------|
| [[../events/\|]] | |

---

## Connected Concepts

| concept | relevance |
|---------|-----------|
| [[../concepts/\|]] | |

---

## What Players Know

[Common knowledge — what any reasonably well-traveled person would know or have heard about this place.]

**Rumors:**
- [Rumor — may or may not be true]
- [Rumor]

---

## DM Notes

**Hidden truths:**
- [Something not obvious on arrival]
- [A secret the settlement is keeping]

**Wizard's influence:** [Agents? Awareness? Strategic relevance to his plan?]

**Ecosystem status:** [Intact / stressed / a pressure point for the Mythic Ecosystem?]

**Adventure hooks:**
1. [Hook from faction tension]
2. [Hook from trade or resources]
3. [Hook tied to campaign arc]

---

## References
- Parent region: [[../regions/|]] | Parent landmark (if any): [[../locations/|]]
- [[../factions/Index|Factions Index]] | [[../events/Index|Events Index]] | [[../concepts/Index|Concepts Index]]
- Regional context: [[../content/REGIONAL_FACTIONS_AND_POWER_DYNAMICS|Regional Factions]]
