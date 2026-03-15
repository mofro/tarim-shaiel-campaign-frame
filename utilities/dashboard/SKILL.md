# Skill: Tarim-Shaiel Dashboard Regeneration

## Purpose
Generate or update `templates/hero-heaven-todo-dashboard.html` from `TODO.md`.
**Do not hand-edit the HTML** — it is auto-generated. All content changes go to TODO.md.
Style tweaks go inside the `STYLE_OVERRIDES` block in the HTML (it survives regeneration).

---

## Canonical Locations
| Asset            | Path                                        |
| ---------------- | ------------------------------------------- |
| Generator script | `utilities/dashboard/generate_dashboard.py` |
| Input            | `TODO.md` (vault root)                      |
| Output           | `templates/hero-heaven-todo-dashboard.html` |
| This skill       | `utilities/dashboard/SKILL.md`              |

---

## How to Run (Mo)
```bash
cd /Users/mo/Documents/Games/HeroHeaven
python utilities/dashboard/generate_dashboard.py
```
Optional flags:
- `--todo path/to/TODO.md` — override input path
- `--out path/to/output.html` — override output path
- `--json` — also write `dashboard_data.json` for inspection

---

## How Claude Regenerates In-Session

When Mo asks to "regenerate the dashboard" or "update the dashboard from TODO":

### Step 1 — Copy generator and TODO to container
```
Filesystem:copy_file_user_to_claude
  /Users/mo/Documents/Games/HeroHeaven/utilities/dashboard/generate_dashboard.py

Filesystem:copy_file_user_to_claude
  /Users/mo/Documents/Games/HeroHeaven/TODO.md
```

### Step 2 — Run the generator
```
bash_tool: python /mnt/user-data/uploads/generate_dashboard.py \
  --todo /mnt/user-data/uploads/TODO.md \
  --out /home/claude/dashboard_out.html
```

### Step 3 — Write output back to vault
Read `/home/claude/dashboard_out.html` content and write to:
```
Filesystem:write_file
  /Users/mo/Documents/Games/HeroHeaven/templates/hero-heaven-todo-dashboard.html
```

### Step 4 — Report
Echo the script's stdout summary so Mo can verify computed percentages.

---

## What the Script Computes

### Domain percentages
- Walks H2-H4 headers, assigns current domain via keyword match
- Counts `- [x]` (done) and `- [ ]` (open) checkboxes per domain
- **Override:** if the `## PROGRESS TRACKING` section contains `**Domain: N%**` lines,
  those values replace the checkbox counts for that domain
- Domains: `narrative`, `mechanics`, `world`, `infra`, `cosmology`

### Campaign readiness
Weighted average: narrative×0.35 + mechanics×0.25 + world×0.25 + infra×0.15

### Blockers
Detected by regex from the BLOCKERS & DECISIONS section of TODO.md.
Currently watches for: Cosmological Architecture (P0), Classes vs. Archetypes,
liberation_aftermath 200yr error, Elven cosmology, GeoJSON field mapping.

### Recent sessions
Extracted from `## LATEST SESSION UPDATE` and `## PREVIOUS SESSION UPDATE` blocks.

### Critical path
Extracted from `**Critical Path:**` line in the Project Health section.

---

## Domain Keyword Mapping
The script assigns each TODO group a domain by scanning the group heading for keywords:

| Domain | Key keywords |
|---|---|
| cosmology | cosmolog, ecosystem, sleeping entity, entity, threshold |
| narrative | story, narrative, session 0, awakening, lore, liberation |
| mechanics | charm, campaign frame, archetype, daggerheart, r/h/k |
| world | world, ancestry, orc, location, myth, silk road, npc |
| infra | kanka, obsidian, geojson, sync, schema, automation |

Fallback: `world`.

---

## Style Overrides (Surviving Regeneration)
The generated HTML contains this comment block near the bottom of `<style>`:
```css
/* =====================================================
   STYLE_OVERRIDES
   Add your CSS overrides here. This block is preserved
   across regenerations if you document them in SKILL.md.
   ===================================================== */
```
Place CSS overrides here AND document them below so they survive regeneration.

### Current Active Overrides
*(Mo: document any CSS changes here so they survive regeneration)*

```css
/* none yet */
```

---

## Dashboard Sections (HTML structure)
| Section | data-status | Source heading in TODO.md |
|---|---|---|
| Active Work | active | `## HIGH PRIORITY` |
| Blocked | blocked | `## BLOCKERS & DECISIONS NEEDED` |
| Near-Term & Medium-Term | upcoming | `## NEAR-TERM` + `## MEDIUM-TERM` |
| Completed Assets | done | `## COMPLETED ASSETS` + `## SETTLED MECHANICS` |

---

## Known Limitations / Future Work
- [ ] `--preserve-overrides` flag to surgically preserve STYLE_OVERRIDES block content
- [ ] Decision-item rendering (amber cards for `#### Decision Required:` blocks)
- [ ] `--section` flag to regenerate only one section
- [ ] Watch mode (`--watch`) for automatic regeneration on TODO.md save
