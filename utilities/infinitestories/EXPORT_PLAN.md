---
title: Infinite Stories Export Utility — Design Plan
project: TTRPG_Tarim_Shaiel
type: operational
visibility: public
status: draft
created: 2026-03-21
last_updated: 2026-03-21
---

# Infinite Stories Export Utility — Design Plan

Export Tarim-Shaiel campaign content to Infinite Stories card format for upload
via the IS API (see `Infinite Stories API.md`).

---

## Planned Script

`utilities/infinitestories/generate_is_export.py`

### CLI

```
python generate_is_export.py \
  [--root PATH]                    # campaign root (default: auto-detected)
  [--output PATH]                  # default: docs/infinitestories-export.jsonl
  [--format json|jsonl|csv]        # default: jsonl
  [--public]                       # only export visibility: public records
  [--types char,loc,lore,story]    # filter IS types (default: all)
  [--status draft,canon]           # filter by status (default: all)
```

### Source directories

| Directory | IS card type |
|---|---|
| `world/locations/*.md` | `location` |
| `characters/**/*.md` | `character` |
| `narrative/lore/*.md` | `lore` |
| `world/factions/Index.md` | `lore` |
| `world/mythology/**/*.md` | `lore` |
| `narrative/sessions/**/*.md` | `story` |
| `narrative/*.md` (narrative/framework types) | `story` |

Skip: `_TEMPLATE_*`, `archive/`, `references/`, `utilities/`, `docs/`.

---

## Type Detection Logic

| Condition | IS type |
|---|---|
| File in `/world/locations/` | `location` |
| Frontmatter `type: character` or has `is_private` field | `character` |
| Frontmatter `type` in `[lore, world_building, entity_index]` | `lore` |
| Frontmatter `type` in `[narrative, narrative_framework, session_introduction, gm_secrets]` | `story` |
| No match | skip (logged) |

---

## Field Mappings

### location
- `id` → `uuid5(NAMESPACE_URL, relative_file_path)` (stable across re-exports)
- `title` → frontmatter `name` or `title`
- `public` → `visibility == "public"` AND no `gm_secrets/` in path
- `created_at` / `updated_at` → frontmatter `created` / `last_updated` (ISO-8601 normalised)
- `tags` → frontmatter `tags`
- `metadata` → `{region, mapmarker, elevation, factions, resources, historical_basis, fantasy_name}`
- `content.name` → frontmatter `name`
- `content.description` → frontmatter `description`
- `content.coordinates` → frontmatter `location: [lat, lng]` → `{lat, lng}`

### character
- `title` → frontmatter `name` or `title`
- `public` → NOT `is_private` AND no `gm_secrets/` in path
- `metadata` → `{affiliation, origin, tier, type}`
- `content.name` → frontmatter `name` or `title`
- `content.description` → frontmatter `description` or first prose paragraph from body
- `content.traits` → frontmatter `traits` or `[]`
- `content.backstory` → full Markdown body

### lore
- `title` → frontmatter `title`
- `public` → `visibility == "public"` AND no `gm_secrets/` in path
- `content.topic` → frontmatter `title`
- `content.summary` → first non-empty paragraph from body
- `content.entries` → `[{title, text}]` — one per `## ` section in body

### story
- `title` → frontmatter `title`
- `public` → `visibility == "public"` AND `audience != "gm_reference"` AND no `gm_secrets/` in path
- `content.synopsis` → first paragraph of body
- `content.body` → full Markdown body

---

## Implementation Notes

- **Frontmatter parsing:** regex `r'^---\n(.*?\n)---\n'` (re.DOTALL) + `yaml.safe_load()` — matches pattern in `utilities/legendkeeper-pipeline/generate_lk_json.py`
- **Visibility gating (dual-layer):** frontmatter field AND filesystem path check
- **Output formats:** JSONL (default, stream-friendly), JSON array, CSV (with serialised `content` column)
- **Libraries:** `pathlib`, `yaml`, `json`, `uuid`, `re`, `argparse`, `csv`, `datetime` (stdlib + pyyaml)
- **Error handling:** skip files with missing required fields; report counts at end

---

## Verification Plan

1. `python generate_is_export.py --root . --format jsonl` → output created, counts printed
2. `python generate_is_export.py --public` → only `visibility: public` records
3. `python generate_is_export.py --format json` → valid JSON (`python -m json.tool`)
4. `python generate_is_export.py --types location` → only location cards
5. Spot-check 2–3 location records: coordinates, tags, `public` flag correct
6. Spot-check 1 lore record: `entries` array built from Markdown `##` sections

---

## Future Phases (Not in Scope Here)

- **Phase 2 — Portal-style player view:** HTML page showing only `public: true` cards
- **Phase 3 — Session notes converter:** transcript → structured IS cards
