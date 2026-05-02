---
title: World — AI Navigation
project: TTRPG_Tarim_Shaiel
type: navigation
visibility: internal
status: canon
created: 2026-04-11
last_updated: 2026-05-02
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
- Faction index: [[world/factions/_category]] — 16 stub files created (P1–P3); 3 deferred: elven-highland-enclaves (#43), scholars-remnant (#42), celestial-court (Decision #11)
- Individual faction files: [[world/factions/lich-cadre.md]] · [[world/factions/the-wizard.md]] · [[world/factions/chain-breakers-order.md]] · [[world/factions/orc-confederation-samarkand.md]] · [[world/factions/eastern-gateway-council.md]] · [[world/factions/merchant-guilds.md]] · [[world/factions/eastern-imperial-dominion.md]] · [[world/factions/dwarven-mountain-confederations.md]] · [[world/factions/dwarven-tarim-authority.md]] · [[world/factions/human-tarim-councils.md]] · [[world/factions/human-imperial-remnants.md]] · [[world/factions/orc-steppe-confederations.md]] · [[world/factions/goblin-free-cities.md]] · [[world/factions/peoples-of-the-nine-roads.md]] · [[world/factions/gnome-guilds.md]] · [[world/factions/jade-coast-realms.md]]
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

## Weapons (`world/weapons/`)

192 weapon files across 7 subdirectories. All generated from SRD via `utilities/scripts/srd-equipment-converter.py`, reskinned for Silk Road setting.

| Directory | Files | Contents |
|---|---|---|
| `world/weapons/` | 44 | Base/Tier 1 weapons — standard Silk Road arsenal |
| `world/weapons/advanced-weapons/` | 32 | Advanced tier versions of base set |
| `world/weapons/improved-weapons/` | 32 | Improved tier versions of base set |
| `world/weapons/legendary-weapons/` | 32 | Legendary tier versions of base set |
| `world/weapons/magical-weapons/` | 38 | Named magical weapons (unique items, campaign-specific) |
| `world/weapons/powder-weapons/` | 3 | Powder weapons: Black Powder Revolver, Blunderbuss, Hand Cannon |
| `world/weapons/special-weapons/` | 11 | Named special weapons (Bravesword, Urok Broadsword, etc.) |

Frontmatter: `type: lore` (pre-Schema C — Phase 4 migration pending). Extension fields: `range:`, `tier:`, `banner_left:`, `banner_right:`, `published:`. `_category.md` files are operational navigation — out of Schema C scope (Decision 17).

Generator note: `srd-equipment-converter.py` still outputs `is_private: false` in new stubs — Phase 4 will fix the template.

## Only if the summary above doesn't answer it
- [[world/content/WORLD_REGIONS_AND_LOCATIONS.md]] — canonical regional framework (6 regions)

## Avoid
- `world/Index.md` — Dataview queries only; not Claude-readable
- `world/factions/Index.md` — Dataview queries only; not Claude-readable
