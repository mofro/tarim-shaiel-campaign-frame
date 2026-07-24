# Newspaper Issue Workflow

Files in this directory are templates only. The generator skips `_`-prefixed directories.

---

## Creating a new issue

1. **Create a directory** under `narrative/newspaper/` with a slug like `0003-session-1-title/`
2. **Copy the template files** from this directory into it
3. **Edit `manifest.md`** — set the masthead (title, date, issue number)
4. **Edit or replace** the story files — each file is one story
5. **Run the build**: `uv run python utilities/build.py newspaper`
6. **Preview** at `http://localhost:8532/newspaper/<slug>/`

---

## Directory structure

```
narrative/newspaper/
  _template/                        ← this directory (skipped by generator)
  0001-session-0-warrior/           ← single-archetype prototype
  0002-session-0-convergence/       ← first full issue
  0003-session-N-title/             ← future issues
```

Each issue directory contains:
- `manifest.md` — masthead (title, date, issue number, tagline, edition)
- One `.md` file per story — any number, any order of filenames

---

## Page layout

The generator assembles stories into pages using the `page:` and `order:` frontmatter fields. Within a page, stories are sorted by `order:` and rendered into a **3-column grid**.

Each story weight occupies a fixed number of columns:

| Weight | Columns | Typical use |
|--------|---------|-------------|
| `lead` | 3 | Banner story — one per page, always first |
| `standard` | 2 | Main feature articles |
| `editorial` | 2 | Opinion, historical, or voice pieces |
| `brief` | 1 | Short news items |
| `sidebar` | 1 | Structured data (weather, omens, lists) |
| `reference` | 1 | NPC rosters, glossaries |

**Grid packing**: CSS auto-placement fills left-to-right. A `standard` (2-col) followed by a `brief` or `sidebar` (1-col) fills a full row. Plan your page around this — the `order:` field controls sequence, not explicit grid position.

**Typical page 1 layout:**
```
┌─────────────────────────────────┐
│ lead (3)                        │
├──────────────────┬──────────────┤
│ standard (2)     │ sidebar (1)  │
├──────────────────┼──────────────┤
│ standard (2)     │ brief (1)    │
└──────────────────┴──────────────┘
```

**Typical page 2 layout:**
```
┌──────────────────┬──────────────┐
│ standard (2)     │ reference (1)│
├──────────────────┼──────────────┤
│ standard (2)     │              │
├──────────────────┘              │
│ editorial (2)                   │
└─────────────────────────────────┘
```

---

## Masthead vs. config defaults

`manifest.md` overrides `storytell_config.json` newspaper defaults. If a field is omitted from the manifest, the config value is used. If `manifest.md` is absent entirely, all config defaults apply.

Fields in `storytell_config.json → newspaper`:
- `name` → masthead title and site nav link
- `tagline` → default tagline
- `edition` → default edition label
- `output_subdir` → where ttrpg_storyteller writes files

---

## Story file fields by weight

See the template files in this directory for full field listings. Quick reference:

**All story files require:**
```yaml
type: newspaper-story
weight: lead | standard | editorial | brief | sidebar | reference
order: 1          # sort position within the page
page: 1           # which sheet (1-indexed)
```

**Narrative body** (lead, standard, editorial): written as Markdown body below the frontmatter, split on blank lines into paragraphs.

**Brief body**: single paragraph in the Markdown body.

**Sidebar items**: structured list in frontmatter under `items:`.

**Reference entries**: structured list in frontmatter under `entries:`.

---

## ttrpg_storyteller integration (Track C — not yet built)

When `storytell.py --format newspaper` is implemented, each narrator writes its own story file into the issue directory. The generator assembles them at the next build. No file coordination between narrators.

Expected narrator → weight mapping:
- Julian (session summary) → `lead`
- Yūsra (fragment) → `standard` or `brief`
- Mythweaver (coda) → `editorial`
- Historian → `standard` or `brief`
- Weather/omens (from session context) → `sidebar`
- NPC roster (from beats) → `reference`
- Manifest generated once per session from config defaults
