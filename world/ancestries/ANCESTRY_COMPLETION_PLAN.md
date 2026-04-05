---
title: Ancestry Completion Plan
project: TTRPG_Tarim_Shaiel
type: operational
visibility: gm_secrets
status: active
created: 2026-04-05
last_updated: 2026-04-05
github_issue: https://github.com/mofro/tarim-shaiel-campaign-frame/issues/105
supersedes:
  - https://github.com/mofro/tarim-shaiel-campaign-frame/issues/102
  - https://github.com/mofro/tarim-shaiel-campaign-frame/issues/103
---

# Ancestry Completion Plan

*Implementation guide for [#105](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/105). Read this at the start of any session picking up ancestry work.*

---

## What This Is

A two-session plan to get ancestry content into a clean, fully functional state that unblocks player character creation and Session 0. Does not cover future foundation docs for ancestries not yet in play.

**Blocker chain:**
```
Session 0
  └─ Player character creation
       └─ Players can read ancestry options
            ├─ peoples-of-tarim-shaiel.html must render all 18 ancestries correctly
            ├─ Tarim-Shaiel names must be applied in player-facing docs
            └─ No single points of failure (content backed by individual files)
```

---

## Key Files

| File | Role | Current Problem |
|---|---|---|
| `world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md` | Compiled player-facing view, 18 ancestries | `type: world_building` → invisible to pipeline |
| `utilities/ancestries/generate_ancestry_html.py` | Dedicated HTML generator for ancestry doc | Reads from PEOPLES_OF_TARIM_SHAIEL.md directly |
| `docs/peoples-of-tarim-shaiel.html` | Generated output | Stale: missing 4 ancestries, old names, pipeline not triggering |
| `simiah.md` … `fungril.md` | 6 full foundation docs | `type: world_building`, no `daggerheart_name:` |
| `drakona.md`, `galapa.md`, `faerie.md`, `ribbet.md` | 4 stubs | `type: world_building`, `visibility: gm_secrets` (wrong) |
| `orcs.md` | Full deep-dive, pre-#79 | Needs Tulpar/Tengirchi naming — deferred (complex) |
| `world/ancestries/ANCESTRY_NAMING_PLAN.md` | Agreed rename table + scope | 2 checkboxes undone; stub-file gap not noted |
| `world/content/CULTURAL_FRAMEWORK.md` | World doc with ancestry references | Old Daggerheart names in Racial & Cultural Positions section |

---

## Complete Rename Table

| Daggerheart | Tarim-Shaiel | Individual file | Done? |
|---|---|---|---|
| Simiah | Vanara | `simiah.md` | ✅ |
| Infernis | Div-Born | `infernis.md` | ✅ |
| Firbolg | Gavar | `firbolg.md` | ✅ |
| Clank | Tadbir | `clank.md` | ✅ |
| Faun | Pari-Kin | `faun.md` | ✅ |
| Fungril | Khavar | `fungril.md` | ✅ |
| Drakona | Naga-Kin | `drakona.md` (stub) | ✅ name |
| Dwarf | Kuhban | `dwarf.md` (to create) | ❌ |
| Goblin | Jivar | `goblin.md` (to create) | ❌ |
| Halfling | Rahban | `halfling.md` (to create) | ❌ |
| Katari | Vaghri | `katari.md` (to create) | ❌ |
| Giant | Kalan | `giant.md` (to create) | ❌ |
| Elf | Serenvar (trade) / Yulduzir (sacred) | `elf.md` (to create) | ❌ |
| Orc | Tulpar (trade/reclaimed) / Tengirchi (sacred) | `orcs.md` (exists, deferred) | ❌ deferred |
| Human | Human | `human.md` (to create) | — no rename |
| Galapa | Galapa | `galapa.md` (stub) | — no rename |
| Ribbet | Ribbet | `ribbet.md` (stub) | — no rename |
| Faerie | Faerie | `faerie.md` (stub) | — no rename |

**Layered names (from ANCESTRY_NAMING_PLAN.md):**
- **Elf:** trade name *Serenvar* (what everyone calls them); sacred self-name *Yulduzir* ("star-people", rarely shared). Player-facing canon = Serenvar.
- **Orc:** trade name *Tulpar* (reclaimed Imperial label; mythological weight of the winged steppe horse); sacred self-name *Tengirchi* ("people of the Sky-Father", passed mouth-to-ear through 80 years of enslavement, never written). Both names have deep design resonance — see ANCESTRY_NAMING_PLAN.md for full design notes.

---

## Session A — Implementation Steps

*Target: one session, ~1–1.5 hours. Completes the naming pass, eliminates single-point-of-failure risk, fixes pipeline type.*

### Step 1: Naming pass — `PEOPLES_OF_TARIM_SHAIEL.md`

Section header format (match existing style of `## VANARA (Simiah)`):
```
## ELF        → ## SERENVAR (Elf)
## DWARF      → ## KUHBAN (Dwarf)
## ORC        → ## ORC / TULPAR   ← special case; see design notes on Tulpar/Tengirchi
## KATARI     → ## VAGHRI (Katari)
## GOBLIN     → ## JIVAR (Goblin)
## HALFLING   → ## RAHBAN (Halfling)
## GIANT      → ## KALAN (Giant)
```
Also update any inline references to these names within each section's body text.

### Step 2: Naming pass — `world/content/CULTURAL_FRAMEWORK.md`

Search for: Dwarf, Goblin, Halfling, Katari, Giant, Elf, Orc (bare names in running text).
Replace with Tarim-Shaiel names. Keep Daggerheart name in parentheses where context is technical.

### Step 3: Update `ANCESTRY_NAMING_PLAN.md`

Mark the two undone checkboxes as done. Add a note under "Implementation Scope":
```
### Additional: Stub files created
Individual files created for all at-risk ancestries (human.md, elf.md, dwarf.md,
katari.md, goblin.md, halfling.md, giant.md) — descriptions pulled from
PEOPLES_OF_TARIM_SHAIEL.md, type: lore, status: stub.
```

### Step 4: Create stub files for at-risk ancestries

**For each file**, use this frontmatter template:
```yaml
---
title: [Tarim-Shaiel Name]
project: TTRPG_Tarim_Shaiel
type: lore
visibility: public
status: stub
daggerheart_name: [Daggerheart name]
created: 2026-04-05
last_updated: 2026-04-05
---
```

**Files to create:**
- `world/ancestries/human.md` — title: Human, daggerheart_name: Human
- `world/ancestries/elf.md` — title: Serenvar, daggerheart_name: Elf
- `world/ancestries/dwarf.md` — title: Kuhban, daggerheart_name: Dwarf
- `world/ancestries/katari.md` — title: Vaghri, daggerheart_name: Katari
- `world/ancestries/goblin.md` — title: Jivar, daggerheart_name: Goblin
- `world/ancestries/halfling.md` — title: Rahban, daggerheart_name: Halfling
- `world/ancestries/giant.md` — title: Kalan, daggerheart_name: Giant

**Content for each:** Pull the existing description + Ancestry Features from `PEOPLES_OF_TARIM_SHAIEL.md`. Add a footer:
```
---
*Foundation document — pending. Full lore to be developed when this ancestry enters play.*
*Description sourced from `PEOPLES_OF_TARIM_SHAIEL.md`.*
```

### Step 5: Fix `type` and `visibility` on all existing ancestry files

**`type: world_building` → `type: lore`** on:
- `PEOPLES_OF_TARIM_SHAIEL.md`
- `simiah.md`, `infernis.md`, `firbolg.md`, `clank.md`, `faun.md`, `fungril.md`
- `drakona.md`, `galapa.md`, `faerie.md`, `ribbet.md`
- `orcs.md`

**`visibility: gm_secrets` → `visibility: public`** on:
- `drakona.md`, `galapa.md`, `faerie.md`, `ribbet.md`
(These stubs were set to gm_secrets by mistake — `status: stub` conveys incompleteness without hiding them.)

### Step 6: Add `daggerheart_name:` frontmatter

Add to each foundation doc and stub where missing. The 7 new stub files already have it from Step 4.

Files needing it added:
- `simiah.md` → `daggerheart_name: Simiah`
- `infernis.md` → `daggerheart_name: Infernis`
- `firbolg.md` → `daggerheart_name: Firbolg`
- `clank.md` → `daggerheart_name: Clank`
- `faun.md` → `daggerheart_name: Faun`
- `fungril.md` → `daggerheart_name: Fungril`
- `drakona.md` → `daggerheart_name: Drakona`
- `galapa.md` → `daggerheart_name: Galapa`
- `faerie.md` → `daggerheart_name: Faerie`
- `ribbet.md` → `daggerheart_name: Ribbet`
- `orcs.md` → `daggerheart_name: Orc`

---

## Session B — Single Source of Truth

*Target: one session, ~1–1.5 hours. Eliminates content drift permanently.*

### Architecture (confirmed)

```
PEOPLES_OF_TARIM_SHAIEL.md     ← player-facing summary view
  2-3 para description
  Ancestry Features (transcluded from individual file)
  "Full lore: [[simiah]]" reference

simiah.md (etc.)               ← canonical full source
  Overview (= the 2-3 para description)    ← source of truth
  Historical Position
  Cultural Characteristics
  ...
  ## Ancestry Features         ← tagged ^ancestry-features
  (transcluded INTO PEOPLES_OF_TARIM_SHAIEL.md)
```

### Step B1: Add block IDs to Ancestry Features in 6 full foundation docs

In each of `simiah.md`, `infernis.md`, `firbolg.md`, `clank.md`, `faun.md`, `fungril.md`:
```markdown
## Ancestry Features
^ancestry-features

**Feature Name:** Description...
```

### Step B2: Replace inline Ancestry Features in `PEOPLES_OF_TARIM_SHAIEL.md`

Replace each `### Ancestry Features` block with:
```markdown
### Ancestry Features
![[simiah#^ancestry-features]]
```

For ancestries with stub-only individual files (Human, Serenvar, Kuhban etc.) — leave inline until those stubs are promoted to full foundation docs.

### Step B3: Test through generator

```bash
python utilities/ancestries/generate_ancestry_html.py
```

Check:
- All 18 ancestries render
- Ancestry Features resolve from transcluded source (not blank)
- Tarim-Shaiel names appear correctly throughout
- Images load (check `docs/images/` for missing files)

### Step B4: Wire into CI if needed

Check `netlify.toml` and `.github/workflows/generate-html.yml` for an explicit call to the ancestry generator. If missing, add:
```
python utilities/ancestries/generate_ancestry_html.py
```

---

## Out of Scope

- Full foundation docs for Human, Serenvar, Kuhban, Vaghri, Jivar, Rahban, Kalan, Galapa, Ribbet, Faerie — when those ancestries enter play
- GM-only naming pass (`HISTORICAL_TIMELINE.md`, `WIZARD_AND_LICH_CADRE.md`, `BACKLOG.md`) — not player-facing, deferred
- GM secrets files for each foundation doc (`world/ancestries/gm_secrets/`) — future
- `orcs.md` Tulpar/Tengirchi update — complex enough to need dedicated treatment

---

## Session End Checklist

After Session A:
- [ ] `PEOPLES_OF_TARIM_SHAIEL.md` has all 7 new section headers
- [ ] `CULTURAL_FRAMEWORK.md` updated
- [ ] `ANCESTRY_NAMING_PLAN.md` checkboxes marked done
- [ ] 7 new stub files committed
- [ ] All ancestry files have `type: lore`
- [ ] 4 stubs have `visibility: public`
- [ ] All files have `daggerheart_name:`
- [ ] Issue #105 Session A items checked off
- [ ] Commit + push

After Session B:
- [ ] Block IDs in 6 foundation docs
- [ ] Transclusion embeds in `PEOPLES_OF_TARIM_SHAIEL.md`
- [ ] Generator tested locally — all 18 render
- [ ] CI wired
- [ ] Issue #105 closed
- [ ] Commit + push
