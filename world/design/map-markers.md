---
title: Map Marker Symbol System
project: TTRPG_Tarim_Shaiel
domain: world
doc_type: design_decision
content_type: reference
visibility: internal
status: canon
created: 2026-05-10
last_updated: 2026-05-10
tags: [map, markers, symbols, cartography, design]
---

# Map Marker Symbol System

Custom SVG symbols for the Tarim-Shaiel interactive map, derived from historical Islamic, Catalan, and Chinese cartographic traditions (12th–16th century). Each symbol is a geometric abstraction of a real convention — not invented iconography.

Live preview: `docs/icon-preview.html` (served at `/icon-preview.html` on the campaign site).

---

## Symbol Inventory

| Type | Symbol | Historical Source |
|---|---|---|
| `city` | Bullseye — outer ring + inner filled disc | Islamic KMMS "dot-in-ring"; walled city with citadel |
| `town` | Ring only — outer circle, hollow | KMMS wall-ring without citadel; lesser settlement |
| `route-node` | Diamond outline + centre dot | Catalan Atlas caravanserai enclosure; waypoint |
| `sacred-site` | Pointed arch / mihrab silhouette | Islamic mihrab arch; universal mosque/shrine marker |
| `fortress` | Crenellated rectangle — 3 merlons | Catalan Atlas castle; battlemented wall plan |
| `oasis` | 5-frond asterisk + centre circle | KMMS palm-tree glyph; top-down crown view |
| `landmark` | Twin-peak mountain silhouette | Universal cartographic convention; all traditions |
| `poi` | Solid disc (smaller than city) | Al-Idrisi small settlement disc |
| `dungeon` | Two concentric rings + dot, gap at top | Invented — labyrinth/descent rings; cave-entrance gap |

---

## SVG Paths (32×32 viewBox)

```
city:         <circle cx="16" cy="16" r="13" fill="none" stroke="…" stroke-width="2.5"/>
              <circle cx="16" cy="16" r="6" fill="…"/>

town:         <circle cx="16" cy="16" r="13" fill="none" stroke="…" stroke-width="2.5"/>

route-node:   <path d="M16 2 L30 16 L16 30 L2 16 Z" fill="none" stroke="…" stroke-width="2.5" stroke-linejoin="round"/>
              <circle cx="16" cy="16" r="4" fill="…"/>

sacred-site:  <path d="M7 29 L7 17 Q7 3 16 3 Q25 3 25 17 L25 29 Z" fill="…"/>

fortress:     <rect x="4" y="15" width="24" height="13" fill="…" rx="1"/>
              <rect x="4" y="8" width="6" height="8" fill="…" rx="1"/>
              <rect x="13" y="8" width="6" height="8" fill="…" rx="1"/>
              <rect x="22" y="8" width="6" height="8" fill="…" rx="1"/>

oasis:        <line x1="16" y1="16" x2="16" y2="3" stroke="…" stroke-width="4" stroke-linecap="round"/>
              <line x1="16" y1="16" x2="26.9" y2="9.5" stroke="…" stroke-width="4" stroke-linecap="round"/>
              <line x1="16" y1="16" x2="22.5" y2="23.5" stroke="…" stroke-width="4" stroke-linecap="round"/>
              <line x1="16" y1="16" x2="9.5" y2="23.5" stroke="…" stroke-width="4" stroke-linecap="round"/>
              <line x1="16" y1="16" x2="5.1" y2="9.5" stroke="…" stroke-width="4" stroke-linecap="round"/>
              <circle cx="16" cy="16" r="5" fill="…"/>

landmark:     <path d="M2 28 Q5 14 11 12 Q14 6 17 12 Q22 14 30 28 Z" fill="…"/>

poi:          <circle cx="16" cy="16" r="9" fill="…"/>

dungeon:      <path d="M 21.5 4.2 A 13 13 0 1 1 10.5 4.2" fill="none" stroke="…" stroke-width="2" stroke-linecap="round"/>
              <circle cx="16" cy="16" r="8" fill="none" stroke="…" stroke-width="2"/>
              <circle cx="16" cy="16" r="3.5" fill="…"/>
```

---

## Color System

MapLibre SDF sprites allow runtime recolouring — one sprite sheet, colour set by data expression in `map-style.json`.

Planned mapping (not yet implemented — see HeroHeaven-0jh):

| Colour | Hex | Use |
|---|---|---|
| Dark red | `#7a1f1f` | Default: cities, towns, route nodes, poi |
| Campaign gold | `#b8892a` | Sacred sites |
| Olive | `#5a4020` | Lesser markers (optional secondary tier) |
| Parchment | `#f5edd8` | All markers on dark map background |

---

## Reserved — Not Yet Implemented

`capital` — bullseye + 4 cardinal tick marks (Al-Idrisi prominence disc). SVG ready; add when a specific location warrants it.

---

## Sources

- Al-Idrisi, *Tabula Rogeriana* (1154)
- *Catalan Atlas* (1375)
- Islamic KMMS manuscript tradition (14th–15th c.)
- Zheng He-era Chinese cartography (early 15th c.)
- Ottoman/Timurid manuscript conventions (~1450s)
