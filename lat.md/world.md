---
title: World — AI Navigation
project: TTRPG_Tarim_Shaiel
type: navigation
visibility: internal
status: canon
created: 2026-04-11
last_updated: 2026-04-11
---

> _Navigation layer — stop here if the summary answers your question. Do not read index files with Dataview queries or `transcripts/` — neither contains canonical content. Do not read files listed under "Do not read" below._

# World

## Setting
- Post-imperial Silk Road, ~1450s CE equivalent
- Empire has collapsed; liberation of enslaved peoples (~1250s) triggered chaos period (~70 years), now stabilized
- Heroes travel **westward** on a merchant caravan; something calls them east
- Warren disturbance from liberation 1,000 years prior is the underlying cosmological context

## 6 Regions (+ Steppe)
| Region | Locations | Character |
|---|---|---|
| Eastern Terminus (Chang'an) | 1 | Imperial heartland; faded prestige |
| Central Asian Hubs (Transoxiana) | 5 | Garrison cities → cosmopolitan trade hubs; Orc influence growing |
| Eastern Gateway (Gansu Corridor) | 2 | Elven sacred sites; imperial checkpoints fading |
| Tarim Basin Oases | 11 | True heart of Silk Road; booming cosmopolitan; mixed factions |
| Mountain Passes (Dwarven) | 3 | Independent gatekeepers; always maintained own names/autonomy |
| Steppe Confederations (Orcish) | 0 | Nomadic; locations to be added as campaign develops |

## 37 Location Files (`world/locations/`)
Primary cities: [[world/locations/chang-an.md]] · [[world/locations/samarkand.md]] · [[world/locations/bukhara.md]] · [[world/locations/tashkent.md]] · [[world/locations/kashkar.md]] · [[world/locations/khotan.md]] · [[world/locations/turfan.md]]

Sacred sites: [[world/locations/dunhuang.md]] · [[world/locations/kucha.md]]

Route nodes: [[world/locations/aksu.md]] · [[world/locations/yarkand.md]] · [[world/locations/maralbashi.md]] · [[world/locations/shorchuk.md]] · [[world/locations/jade-gate.md]] · [[world/locations/merv.md]] · [[world/locations/balkh.md]] · [[world/locations/miran.md]] · [[world/locations/cherchen.md]] · [[world/locations/charklik.md]] · [[world/locations/endere.md]] · [[world/locations/niya.md]]

Additional (dungeons/landmarks/waypoints): [[world/locations/alak-mor.md]] · [[world/locations/anvil-sunder-switchbacks.md]] · [[world/locations/balkh-kamen.md]] · [[world/locations/black-timber-post.md]] · [[world/locations/buried-lens.md]] · [[world/locations/caravan-crypt.md]] · [[world/locations/dun-kharan.md]] · [[world/locations/isyk-zhel.md]] · [[world/locations/miran-temple-district.md]] · [[world/locations/niya-outer-fields.md]] · [[world/locations/salt-reed-oasis.md]] · [[world/locations/stone-ledger-gate.md]] · [[world/locations/wind-cut-narrows.md]] · [[world/locations/yumen-waystation.md]]

## Faction Landscape
- Visible factions in location frontmatter: `factions_visible:`
- Hidden factions: `factions_hidden:` (GM layer only)
- Faction index: [[world/factions/_category]] — individual faction files TBD
- Active political players overview: [[world/content/CAMPAIGN_PRESENT_FACTIONS.md]]

## Geospatial Data
- [[world/data/tarim-shaiel-locations.geojson]] — all location coordinates + properties
- [[world/data/tarim-shaiel-routes.geojson]] — trade route definitions
- [[world/data/tarim-shaiel-regions.geojson]] — regional boundaries
- Leaflet maps embedded in each location file; zoom 4.5–18

## Cultural Frameworks
- 18 ancestries (player-facing): [[world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md]]
- Cultural systems: [[world/content/CULTURAL_FRAMEWORK.md]]
- Peoples & ancestries: [[world/content/PEOPLES_AND_CULTURES.md]]
- Historical timeline: [[world/content/HISTORICAL_TIMELINE.md]]
- Real-world analog substrate (1453 CE): [[world/historical-parallels.md]]

## Only if the summary above doesn't answer it
- [[world/content/WORLD_REGIONS_AND_LOCATIONS.md]] — canonical regional framework (6 regions)

## Avoid
- `world/Index.md` — Dataview queries only; not Claude-readable
- `world/factions/Index.md` — Dataview queries only; not Claude-readable
