---
title: Ancestry Naming Plan — Tarim-Shaiel
project: TTRPG_Tarim_Shaiel
type: world_building / implementation_plan
visibility: gm_only
status: approved_pending_implementation
created: 2026-04-03
last_updated: 2026-04-14
---

# Ancestry Naming Plan — Tarim-Shaiel

*This document records the agreed Tarim-Shaiel names for ancestries currently using generic Daggerheart labels, plus the implementation scope for applying those changes. All names were developed through cultural analysis of the four regional analogs (Central Asian/Turkic-Mongol, Persian/Zoroastrian, Tang Chinese, Indian Subcontinent).*

---

## Design Principles

- Names are **in-world demonyms** — what peoples are called in Tarim-Shaiel's lingua franca, and what they call themselves.
- Where a people has a **trade name** (common, widely used) and a **sacred self-name** (rarely shared with outsiders), both are recorded.
- Elves and Orcs receive **additional regional nicknames** reflecting how different ancestries perceive them, consistent with their outsized cultural footprint.
- The Daggerheart SRD names are **not replaced** in reference files — only in canon world documents.

---

## Master Name Table

### Single-Name Ancestries

| Daggerheart | Tarim-Shaiel Name | Linguistic Root | Meaning |
|---|---|---|---|
| Dwarf | *Kuhban* | Persian (*kuh* + *-ban*) | "Mountain-keepers / Mountain-guardians" |
| Goblin | *Jivar* | Persian/Arabic blend (*jinn* + *jivār*) | "In-between clever ones / neighborhood spirits" |
| Halfling | *Rahban* | Persian (*rah* + *-ban*) | "Road-keepers / Way-wardens" |
| Katari | *Vaghri* | Sanskrit/Prakrit (*vyāghra*) | "Tiger-folk" |
| Giant | *Kalan* | Turkic/Mongolian | "Great-kin" |

### Layered-Name Ancestries

#### ELVES

| Layer | Name | Notes |
|---|---|---|
| Trade name (common) | *Serenvar* | Persian: "those who have stillness." What everyone calls them. Player-facing canon. |
| Sacred self-name | *Yulduzir* | Turkic *yulduz* (star) + ancient Iranian nominal *-ir*. "Star-people." Ancient, self-given, rarely shared. Players may eventually hear this from Elven NPCs directly. |

**Elf Regional Nicknames**

| Who | Name | Register / Meaning |
|---|---|---|
| Orcs (*Tulpar*) | *Buz'han* | Turkic/Mongolian: "Ice-speakers." Cold, useful, baffling. Not quite insult, not quite compliment. |
| Goblins (*Jivar*) | *Purdah-folk* | Persian *purdah* (veil/curtain): "The behind-the-curtain people." Everything is about access; Elves keep the curtain drawn. |
| Dwarves (*Kuhban*) | *Takhtshin* | Persian: "Throne-dwellers." Elevated, untouchable, resentful admiration. |
| Humans (Tarim Basin) | *Serenvar* | They use the trade-word. Pragmatic. |
| Humans (Tang/Chang'an) | *Xianren* | Chinese: "Celestial immortals." A genuine honorific with real awe in it. |
| Naga-Kin | *Akashavar* | Sanskrit *ākāśa* (sky/ether) + *-var*: "Sky-dwellers." Places Elves within Naga cosmological framework. |

**Orc Regional Nicknames**

| Who | Name | Register / Meaning |
|---|---|---|
| Dwarves (*Kuhban*) | *Baatyr* | Turkic/Mongolian: "hero/warrior of the people." What the Kuhban call the Tulpar — pragmatic respect that acknowledges the martial history without flinching from it. |

#### ORCS

| Layer | Name | Notes |
|---|---|---|
| Trade name (common) | *Tulpar* | Originally an Imperial label — Turkic/Kazakh *tulpar* (the legendary winged horse of steppe myth). The Empire used it as a dehumanizing descriptor: "the horse-people / our war-beasts." The Orcs kept it. The mythological weight of the word (untameable, heroic, associated with impossible journeys) works against the slur — you cannot fully degrade a winged horse. Reclaimed in place, without changing a syllable. |
| Sacred self-name | *Tengirchi* | Turkic *Tengri* (sky/heaven, supreme steppe divinity) + *-chi* (one who belongs to). "People of the Sky-Father." Predates the Empire. Passed mouth-to-ear through 80 years of enslavement; never written down, precisely so it could not be taken. |

> **Design note — the two names tell the full arc:** *Tengirchi* is who they were before anyone tried to own them. *Tulpar* is what was thrown at them, which they caught and kept. Their proverb — *"You are what you carry"* — lands differently knowing their own name is something they chose to carry despite its origin.

> **Design note — sky resonance:** Both Orcs (*Tengirchi* = sky-father's people) and Elves (*Yulduzir* = star-people) reach toward the sky in their secret self-names. Two peoples who have almost never spoken directly about it. A GM thread for later.

#### GIANTS (including Cyclops)

| Layer | Name | Notes |
|---|---|---|
| World name | *Kalan* | Turkic/Mongolian: "Great-kin." Dignified, not reductive. |
| Cyclops internal nickname | *Tekgöz* | Turkic: "single-eye." Used affectionately within Giant communities; occasionally leaks into wider usage as an honorific. |

---

## Implementation Scope

### Documents requiring updates

| File | What changes |
|---|---|
| `world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md` | Section headers use trade name as primary with Daggerheart name in parentheses (e.g., `## SERENVAR (Elf)`). Inline references follow same pattern on first use per section. Ancestries: Dwarf → Kuhban, Goblin → Jivar, Halfling → Rahban, Katari → Vaghri, Giant → Kalan, Elf → Serenvar, Orc → Tulpar |
| `world/content/CULTURAL_FRAMEWORK.md` | Section headers and inline text for the same ancestries throughout the Racial & Cultural Positions section |

### Assets requiring renaming (optional / lower priority)

| Current path | Suggested rename |
|---|---|
| `audio/ambience/Elven/` | `audio/ambience/Serenvar/` |
| `audio/music/Elven/` | `audio/music/Serenvar/` |

### Documents confirmed clean (no changes needed)

- `TODO.md`
- `NEXT_SESSION_CONTEXT.md`
- `STORY_ARC_SYNTHESIS.md`
- `HISTORICAL_TIMELINE.md`
- `PLAYER_ARC_SYNTHESIS.md`
- `Session_0_Awakening_Design_Notes.md`
- `narrative/SILK_ROAD_MYTH_ANALYSIS.md`
- `narrative/gm_secrets/divine-players-naming.md`
- All mechanics files
- `references/daggerheart-srd/` (intentionally untouched — SRD reference only)

---

## Status

- [x] Names agreed
- [x] `narrative/gm_secrets/ANCESTRY_SECRET_NAMES.md` created
- [x] `world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md` updated
- [x] `world/content/CULTURAL_FRAMEWORK.md` updated
- [ ] Audio folder renames (optional — deferred, not blocking)
