---
title: Historical Events Index
project: TTRPG_Tarim_Shaiel
type: entity_index
entity_type: event
status: active
created: 2026-03-10
last_updated: 2026-03-10
---

# Historical Events Index

Master registry of named historical events — pivot points in the 1,000-year arc. These are the nodes that connect eras, factions, and concepts into a causal chain. Each is a linkable entity.

**Era reference:**
- Era 0 (~200–250 CE) — The Age of Chains
- Era 1 (~250–400 CE) — The Age of Blood and Ash
- Era 2 (~400–700 CE) — The Age of Many Voices
- Era 3 (~700–1000 CE) — The Age of Pacts and Suspicions
- Era 4 (~1000–1200 CE) — The Age of Whispers and Warnings
- Era 5 (~1200 CE+) — The Age of Reckoning (campaign present)

**Status key:** `canon` | `draft` | `proposed` | `tbd`

---

## The Causal Chain

| name                                                       | era     | approx_date   | type                   | cause                                                                                 | effect                                                                                      | key_actors                                              | narrative_weight | status               |
| ---------------------------------------------------------- | ------- | ------------- | ---------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------- | -------------------- |
| [[the-enslavement\|The Enslavement]]                       | Era 0   | ~150 CE       | magical / political    | human-empire expansion + binding magic                                                | orc-subjugation, empire-military-power                                                      | human-empire, orcs                                      | high             | canon                |
| [[the-liberation\|The Liberation]]                         | Era 0   | ~200–250 CE   | magical / military     | heroes break binding spells                                                           | orc-freedom, ecosystem-ripple-effects                                                       | the-heroes, the-wizard (failed to prevent)              | very-high        | canon                |
| [[the-military-victory\|The Military Victory]]             | Era 0   | ~250 CE       | military               | heroes + allied forces defeat empire                                                  | human-empire dissolved, regional fragmentation begins                                       | the-heroes, human-empire, orc-confederation-samarkand   | very-high        | canon                |
| [[the-sacrifice\|The Sacrifice]]                           | Era 0   | ~250 CE       | personal / narrative   | final push against empire                                                             | fallen-teammate dies; gaes-connection created; heroes' rallying point                       | fallen-teammate, the-heroes                             | very-high        | tbd — details needed |
| [[the-ascension\|The Ascension]]                           | Era 0   | ~250 CE       | cosmological           | heroes complete charge (partially)                                                    | heroes enter Celestial Peak; charge left incomplete; Wizard survives                        | the-heroes, celestial-peak                              | very-high        | canon                |
| [[the-scattering\|The Scattering / Orc Eruption]]          | Era 1   | ~250–320 CE   | social / military      | liberation without ecosystem repair; power vacuum                                     | 70 years of regional chaos; orc cultural reorganization begins                              | orc-confederation-samarkand, human-imperial-remnants    | high             | canon                |
| [[the-wizards-retreat\|The Wizard's Retreat]]              | Era 1   | ~250 CE       | strategic              | defeat of empire; heroes' ascension                                                   | Wizard begins 1,000-year plan; studies mythic ecosystem; assembles Lich-Legion slowly       | the-wizard                                              | very-high        | canon                |
| [[the-vanishing-of-khorashar\|The Vanishing of Khorashar]] | Era 3   | ~950 CE       | cosmological           | ecosystem stress / unknown cause                                                      | entire settlement disappears; dwarven archivists begin tracking anomalies                   | dwarven-mountain-confederations, mythic-ecosystem       | high             | draft                |
| [[scholars-purge]]                                         | Era 4   | ~1175 CE      | political / covert     | Wizard eliminating competition                                                        | researchers studying mythic ecosystem killed or disappeared; knowledge fragments suppressed | the-wizard, lich-cadre, human-mage-scholars             | high             | proposed             |
| [[the-expulsion\|The Expulsion / The Gaes]]                | Era 5   | ~1200 CE      | cosmological / magical | heroes' incomplete charge triggers ecosystem response; Wizard exploits gaes mechanism | heroes expelled from Celestial Peak; returned to mortal world; charged with completion      | the-heroes, fallen-teammate, celestial-peak, the-wizard | very-high        | canon                |
| [[the-lich-legion-assembly\|The Lich-Legion Assembly]]     | Era 4–5 | ~1000–1200 CE | military / necromantic | Wizard's 1,000-year plan reaching completion                                          | 100,000+ undead assembled; ecosystem under strain; campaign threat                          | the-wizard, lich-cadre                                  | very-high        | canon                |

---

## Anticipated / Possible Future Events

*Not yet occurred in campaign. Listed for structural completeness.*

| name | type | trigger | possible_outcomes | status |
|------|------|---------|------------------|--------|
| [[the-threshold-breach\|The Threshold Breach]] | cosmological / military | Wizard launches final assault on Hero Heaven | ecosystem collapse / heroes defend / threshold sealed | proposed |
| [[the-completion\|The Completion]] | narrative / cosmological | Heroes fulfill original charge | Wizard defeated; ecosystem stabilized; heroes re-earn ascension | tbd |

---

## Notes

- Individual event files live alongside this index in `/world/events/`
- `cause` and `effect` fields use canonical entity names from Factions and Concepts indexes
- Historical Timeline (full prose) → see [[../content/HISTORICAL_TIMELINE]]
- Story arc / speculative endgame → see [[../../narrative/STORY_ARC_SYNTHESIS]]
- Events that are `proposed` require Mo's approval before being treated as canon
