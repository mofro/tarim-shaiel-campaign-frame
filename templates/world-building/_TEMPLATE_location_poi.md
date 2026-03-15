---
# ── REQUIRED ──────────────────────────────────────────────────────────────────
name:                       # Canonical name (used in all wikilinks)
type: poi
created:
last_updated:

# ── HIERARCHY ─────────────────────────────────────────────────────────────────
# Set ONE of these depending on whether this POI is standalone or a sub-element.
# Both can be set if the POI is a sub-element that also warrants a map pin.
parent_region:              # [[../regions/region-name]] — set for standalone POIs
parent:                     # [[../locations/settlement-or-landmark]] — set for sub-elements

# ── MAP (OPTIONAL) ────────────────────────────────────────────────────────────
# Omit if this is a sub-element with no independent map presence.
# Include even for sub-elements if this specific POI warrants its own map pin.
location:                   # [lat, long] — optional
mapmarker:                  # sacred-site | marker-dungeon | city | etc. — optional
fantasy_name:               # If display name differs from canonical name

# ── IDENTITY ──────────────────────────────────────────────────────────────────
concept:                    # One phrase — what this POI essentially is (e.g. "A tavern that remembers everyone")
poi_type:                   # building | ruin | sacred-site | natural-feature | dungeon |
                            # cultural-practice | creature-habitat | route-node | cosmological | other
formerly:                   # What this was before its current state (ruins, transformed sites, etc.)
current_state:              # active | abandoned | ruined | sealed | contested | unknown

# ── CLASSIFICATION ────────────────────────────────────────────────────────────
visibility: public          # public | secret
danger_level:               # 1–5 — optional, omit for non-threatening sub-elements
narrative_weight:           # very-high | high | medium | low

# ── FACTIONS ──────────────────────────────────────────────────────────────────
factions_present: []        # Canonical wikilinks
factions_claiming: []       # Factions asserting control or ownership
factions_seeking: []        # Factions who want this but don't have it

# ── COSMOLOGICAL ──────────────────────────────────────────────────────────────
concepts_related: []        # Canonical concept wikilinks — e.g. [[../concepts/mythic-ecosystem]]

# ── STATUS ────────────────────────────────────────────────────────────────────
status:                     # canon | draft | tbd
is_private: false

tags:
  -                         # player-visible | gm-only | secret
  -                         # campaign-arc-[name]
  - type-poi
---

```leaflet
id: poi-[filename-slug]
coordinates: [[world/locations/[filename-slug]]]
defaultZoom: 10
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

<!-- Remove the leaflet block above if this POI has no map presence (sub-element only) -->

# [POI Name]

> [One sentence. What do you notice before you understand what this is?]

*Concept: [paste concept value here]*

---

## What It Is

[Current state — what can be observed, entered, or experienced. 2–4 sentences, player-facing. Write for the moment of arrival or discovery.]

---

## What It Was
*(Omit if this is a simple active feature with no history worth noting)*

[Historical identity — what this was before its current state. The source of its narrative weight.]

**Era of origin:** [Era 0–5, or earlier]
**Historical significance:** [Why it was built, named, or significant]

---

## Special Rules & Mechanics

*The behavioral contracts, magical properties, or mechanical facts of this POI. Include these whenever the POI has rules the players will interact with — even informally.*

- **[Rule or property name]:** [What it does or requires]
- **[Rule or property name]:** [What it does or requires]

---

## What's Here

**Accessible:** [What players find without special effort]

**Hidden or restricted:** [What requires a roll, key, relationship, or knowledge to access — mark DM-only if needed]

---

## Cosmological Significance
*(Omit if none)*

[Is there a Warren node here? Ecosystem damage? Binding magic residue? A pressure point?]

Related: [[../concepts/|]] [[../concepts/|]]

---

## Faction Presence
*(Omit if none)*

| faction | relationship to this POI |
|---------|-------------------------|
| [[../factions/\|]] | [aware / claiming / seeking / protecting / avoiding] |

---

## Connected Events
*(Omit if none)*

| event | connection |
|-------|-----------|
| [[../events/\|]] | [Built during / site of / affected by] |

---

## Environment
*(Only if this POI warrants its own encounter design — most sub-elements won't)*

→ [[../environments/|]]

---

## What Players Know

[Common knowledge or rumors — what locals, merchants, or scholars say.]

---

## DM Notes

**The real truth:** [What this place actually is beneath its surface appearance]

**Wizard's awareness:** [Does he know? Has he sent agents? Is it in his plan?]

**If players fully engage with this:** [What do they learn? What's irreversible?]

**Hook:** [One story hook specific to this POI]

---

## References
- Parent: [[../locations/|]] | Region: [[../regions/|]]
- [[../factions/Index|Factions Index]] | [[../events/Index|Events Index]] | [[../concepts/Index|Concepts Index]]
