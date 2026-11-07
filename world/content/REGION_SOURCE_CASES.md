---
title: Region Source Cases (#384)
project: TTRPG_Tarim_Shaiel
domain: world
doc_type: design_decision
content_type: reference
visibility: gm_secrets
status: draft
created: 2026-11-07
last_updated: 2026-11-07
tags: [regions, naming, faith, parent_region, "#384"]
---

# Region Source Cases (#384)

*Written after `world/regions/` was read in full (it was not, the first time). The two drafts, `PERSONAL_NAME_RULES.md` and `REGIONAL_FAITH_LIST.md`, were revised for the mechanical gaps on 2026-11-07. The items below turn on what the work is for, so each is a case, not a change. Nothing here is applied unless marked.*

## What was already applied (mechanical)

- Name rules: a *Period strata* section from `KEY_POLITICAL_REGION_EXPLORATION.md` (Tangut, Khitan, Khwarazmian/Ghurid/Seljuk, Mongol/Chagatai/Golden Horde, Timurid, Song/Jin); the Dwarven Tarim Authority in the Tarim Basin entry; Mountain Passes rewritten around its primary ancestry (Kuhban), with the named pass-works; the Eastern Imperial Dominion in the Eastern Terminus entry.
- Faith list: no Islam-analog faith (your decision, 2026-11-07); the Lamp relabelled as a Persianate devotional tradition mapped onto the existing Court; the Authority added to Tarim Basin (Forge-Record 4%); Mountain Passes rebalanced around a Kuhban majority (Forge-Record 25%, Mountain Bride and Wind 25%). Shares still sum to 100 in every region (checked).
- The Mountain Passes shares are a judgment I made, not a reading of the file. It is one table to revert.

## Case 1. Where "Islam" survives in the region documents

**Intent behind the current state.** The region files were written with real-world analogs close to the surface. `central-asian-hubs.md` says scholars "translated Greek texts into Arabic, where paper reached the Islamic world" and names an "Islamic Scholarly Network" with "a complex relationship with older Zoroastrian traditions". The exploration note calls Baghdad "the spiritual heart of the Islamic world". Your decision means those lines name a creed the world does not have.

| Option | Pros | Cost to reverse |
|---|---|---|
| A. Leave the region documents; treat the words as analog scaffolding | Nothing to edit; nothing lost | None. But a player-visible page (these are not `gm_secrets`) says "Islamic" |
| B. Rename in-world, keep the substance (a scholarly network that carries the translation tradition, in tension with the Fire) | The page agrees with the cosmology; the tension with the Fire keeps its hook | A rename pass over two or three sentences; revert is a revert |
| C. Reword the sentences without naming a network | Smallest edit | Loses the faction hook the sentence carries |

**Suggested: B.** The faction is a useful hook and needs only an in-world name. The name is yours.[EDITORIAL] The user agrees

## Case 2. The Lamp's prophet role

**Intent behind the current state.** You said the prophet and deity analogs apply and the specific tenets do not. The Lamp now addresses the Court through its Persian faces and carries no scripture. The real tradition it flavours has a prophet figure, and nothing in the Court is one.

| Option | Pros | Cost to reverse |
|---|---|---|
| A. Leave the role empty | Honest to the Court as written; no figure promoted | None |
| B. Nominate an existing figure (a Court face, or a legendary non-hero) | Gives lodges a human origin story | Adds a claim about who stands where; the Hard Constraints (heroes are not religious figures; Decision 4) limit the choice |
| C. Leave it empty now, decide when a scene needs it | No cost today | None |

**Suggested: C.** The list does not need it; a scene that does will show which figure fits.[EDITORIAL] The user agrees

## Case 3. Strata as sound palettes, or as in-world history

**Intent behind the current state.** `KEY_POLITICAL_REGION_EXPLORATION.md` is a real-world map of Silk Road powers, 1100 to 1400 CE, with no frontmatter and no cross-references. Tarim-Shaiel sits after its own collapse. I used it as sound palettes only, with the palette-to-region assignments labelled as my inference from the cities the note lists.

| Option | Pros | Cost to reverse |
|---|---|---|
| A. Palettes only (as applied) | Adds texture to names without a historical claim | Delete the section |
| B. In-world successor states, each with a name | Gives each region a past | A new body of lore; touches Decision-level material; not mechanical |
| C. Drop the strata | Simplest | Names lose the older/younger layering |

**Suggested: A**, for now.[EDITORIAL] The user agrees, as long as B. Is noted for later design passes

## Case 4. The exploration note itself, and the unflagged lore pages

`KEY_POLITICAL_REGION_EXPLORATION.md` is one of 30 lore pages with no valid `visibility` (27 with no frontmatter, 3 with broken YAML). It reads as a pasted chat reply about a Google Earth layer. Setting a restrictive visibility is a safe commit; moving it toward `public` is yours.

| Option                                                  | Pros                                                        | Cost to reverse              |
| ------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------- |
| A. Add frontmatter, `gm_secrets`, `doc_type: substrate` | It becomes a referenced source (the name rules now cite it) | One commit                   |
| B. Move it to `archive/`                                | Marks it as historical                                      | A move                       |
| C. Leave it                                             | None                                                        | It stays on the warning list |

**Suggested: A**, since the name rules now cite it.[EDITORIAL] The user agrees. "substrate" is new, yes? Perhaps that is just bloat? I understand the intent... Is it actually "Lore"? Or another type?

## Case 5. `parent_region` for the 159 locations that lack it

Tested against the seven regions' `bounds` (`world/regions/*.md`), using each location's coordinates:

| Result | Count | What it means |
|---|---|---|
| Inside Tarim Basin only | 71 | Resolved |
| Inside Central Asian Hubs only | 4 | Resolved |
| Inside Mountain Passes only | 1 | Resolved |
| Inside Hubs **and** Transoxiana | 30 | Harmless for names (Transoxiana inherits the Hubs pool). It matters only for the faith pre-eminent: Anahita over Rashnu-e-Rah |
| Inside Passes **and** Tarim Basin | 37 | A real tie. They are mostly Basin oases (Yengisar, Kargilik, Guma, Aqyar) in a generous Passes box |
| Inside Steppe **and** Tarim Basin | 6 | A real tie |
| Inside none | 10 | Beijing, Chengdu, Kabul, Charikar, Islamabad, Puli-Khumri, Ruy-e-Do-Aab, He-An, Mati Temple, East China Sea. Real-world anchors outside every box; Mati Temple is 0.5 degrees under Eastern Gateway's southern edge |

No location has an `elevation` value, so elevation cannot break the Passes/Basin tie. None of the 159 falls in the Eastern Terminus or Eastern Gateway boxes.[EDITORIAL] Is it worth an elevation check against real named analogs for the locations FIRST, and then redo this pass? Or not...?

| Option | Pros | Cost to reverse |
|---|---|---|
| A. Basin as the default for the 37, Passes only where the page names a pass, mountain or Dwarven keepers; Steppe for the 6 only where the page says clan or yurt; anything the rule cannot place comes to you | Few decisions reach you; uses what the pages say | A written field per location; reverting means clearing a field. *Unverified:* I have not run the page-text rule |
| B. Nearest region centre | Fully mechanical | The Basin centre is far from the Passes, so it would misfile mountain places |
| C. You assign the contested 53 | Your word on each | Slow, and it is the sheet-to-fill pattern you declined on #336 |
| D. Leave them unassigned; the settlement pass assigns by ancestry mix | No edit now | Child C needs the field, so the work moves rather than disappears |

**Suggested: A**, with you seeing only the places the rule cannot classify. The 10 outside need a separate call: extend the boxes (Kabul-side, Mati Temple) or leave them outside the seven regions.[EDITORIAL] The user agrees

## Case 6. Your 11:04 edit to the faith list

The Still Mirror heading now reads "(Shizuka no Kagami; Yulduzir)". *Yulduzir* is the Elves' sacred self-name (`narrative/gm_secrets/ANCESTRY_SECRET_NAMES.md`). The same file's ground rules say sacred self-names are not used. The file is `gm_secrets`, so nothing leaks. Both cannot stand.

| Option | Pros | Cost to reverse |
|---|---|---|
| A. Keep your edit; relax the rule to "not used in player-facing text" | Your change stands | One sentence |
| B. Revert the heading to Serenvar and keep the rule | Rule stays clean | One word |

**Suggested: A**, since the edit is yours and the file is GM-only. I have kept the edit and left the rule as it was.[EDITORIAL] The user agrees

## Outcomes (2026-11-07)

| Case | Outcome |
|---|---|
| 1 | B done. The "Islamic Scholarly Network" is now the Anjoman-e Varaq (the Society of the Leaf), applied in `central-asian-hubs.md`. |
| 2 | C agreed. The Lamp's prophet role stays empty. |
| 3 | A agreed. **B (in-world successor states) is noted for later design passes**, not dropped. |
| 4 | A agreed. Open question from the GM: is `doc_type: substrate` the right type? It is in the Schema C list (`canon\|draft\|substrate\|template\|...`), so it is not new, but it was not yet used for lore sources. Alternatives within the schema: `draft` or `canon`. Awaiting the GM's call. |
| 5 | A agreed. The GM asked for an elevation check against real named analogs first, then a redo of the pass. Elevation pass done (parent_region elevations set); the six mid-band places are assigned (Refugee Rill and Egizyer: Basin; Shorkol, Qarajol, Singing Straights, Saparbay: Mountain Passes). Held: 30 Hubs/Transoxiana ties, 10 outside every box, Stone Ledger Gate (3510 m) and Anvil Sunder Switchbacks (4317 m) assigned to tarim-basin. |
| 6 | A agreed. The rule now reads "not used in player-facing text". |
