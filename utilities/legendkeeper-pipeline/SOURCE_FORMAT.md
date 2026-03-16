---
title: LegendKeeper Pipeline — Source Format Specification
project: TTRPG_Tarim_Shaiel
type: operational
visibility: public
status: active
created: 2026-03-16
last_updated: 2026-03-16
---

# LegendKeeper Pipeline — Source Format Specification

This document defines the canonical Obsidian Markdown source format for documents
that are published through the dual-path pipeline:

```
Source MD (Obsidian vault)
  ├─→ generate_lk_markdown.py  →  LK-compatible .md  (LK Markdown import)
  ├─→ generate_lk_json.py      →  .json / .lk file   (LK direct import)
  └─→ generate_world_html.py   →  styled .html        (Campaign Frame aesthetic)
```

---

## Supported Document Types

| `type:` value | Description | LK document type |
|---------------|-------------|-----------------|
| `myth`        | Prose lore/fable | page |
| `lore`        | World lore entry | page |
| `timeline`    | Calendar-based event doc | time |

---

## Standard Frontmatter (Required for all)

```yaml
---
title: Document Title
project: TTRPG_Tarim_Shaiel
type: myth              # myth | lore | timeline
tags: [myth]            # LK tag(s), list or string
visibility: public      # public | gm_secrets
status: draft           # draft | review | canon | deprecated
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---
```

### Myth/Lore — Additional Optional Fields

```yaml
lk_cover_image: https://url-to-image.jpg    # LK banner image; used in HTML cover
```

### Timeline — Additional Required Fields

```yaml
calendar: Menology of Epochs    # Calendar name (used in HTML subtitle)
```

---

## Myth / Lore Document Format

```markdown
---
title: The Roads: A Fable
project: TTRPG_Tarim_Shaiel
type: myth
tags: [myth]
visibility: public
status: draft
created: 2026-03-16
last_updated: 2026-03-16
lk_cover_image: https://assets.legendkeeper.com/abc123.png
---

_Italic epigraph — the opening line, shown large and centered._

Prose content with **bold** and *italic* formatting. Paragraphs are
separated by blank lines.

Multiple paragraphs are supported. [[Wikilinks]] are stripped to plain
text in all output formats.

## Moral

The moral or lesson conveyed by this myth.

## Cultural Significance

The myth's significance to the culture that tells it.

%%
## Secret

GM-only content. This entire block is:
- Stripped from HTML output
- Converted to a LK Secret section in LK Markdown output
- Excluded from public LK JSON (Phase 2)
%%
```

### Rules for Myth/Lore

- **First italic line** (`_text_`) → rendered as large epigraph in HTML
- **`## Section` headers** → rendered as titled section cards in HTML; preserved in LK output
- **`%%...%%` blocks** → stripped from HTML; converted to LK Secret section in LK Markdown
- **`[[wikilinks]]`** → stripped to plain text in all outputs
- **Blockquotes** (`> text`) → rendered as callout boxes in HTML

---

## Timeline Document Format

### Event Syntax

Each event is a list item using pipe-separated key-value pairs:

```
- "Event Name" | start: YEAR [| end: YEAR] [| color: "#hex"] [| icon: glyph] [| opacity: 0.8]
```

For point-in-time events, use `date:` as shorthand for `start:` (no `end:`):
```
- "Event Name" | date: YEAR | color: "#EAB308" | icon: flag
```

### Full Example

```markdown
---
title: "Nianhao: The Divine Arc"
project: TTRPG_Tarim_Shaiel
type: timeline
tags: [timeline, history]
visibility: gm_secrets
status: draft
created: 2026-03-16
last_updated: 2026-03-16
calendar: Menology of Epochs
---

## Eras

- "The Slow Forgetting"       | start: -2000 | end: 0    | color: "#4B5563" | icon: hourglass | opacity: 0.35
- "The Held Breath"           | start: 1     | end: 3200 | color: "#0079CC" | icon: wind      | opacity: 0.25

## Declarations (Nianhao)

- "First Nianhao Declared"    | date: 188  | color: "#EAB308" | icon: flag
- "Second Nianhao Declared"   | date: 350  | color: "#EAB308" | icon: flag

## Historical Events

- "Empire Rises"              | start: 250 | end: 400 | color: "#7a1f1f" | icon: swords | image: https://assets.legendkeeper.com/abc.jpg
- "The Great Trade Opens"     | date: 412  | color: "#22C55E"  | icon: scroll

%%
## Secret

- "The Heroes Are Expelled"   | date: 1450 | color: "#7C3AED" | icon: star
- "The Wizard Ascends"        | date: 1448 | color: "#DC2626"  | icon: hat-wizard
%%
```

### Event Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `"Name"` | Yes | Event name (quoted, first item) | `"Empire Falls"` |
| `start:` | Yes* | Start year (world calendar year) | `start: 188` |
| `date:` | Yes* | Alias for `start:` (point event) | `date: 450` |
| `end:` | No | End year (omit for point events) | `end: 600` |
| `color:` | No | Hex color code | `color: "#EAB308"` |
| `icon:` | No | Icon glyph name (Font Awesome) | `icon: swords` |
| `image:` | No | Direct image URL — shown as cropped thumbnail in HTML card | `image: https://assets.legendkeeper.com/abc.jpg` |
| `opacity:` | No | Visual opacity 0–1 (default 1.0) | `opacity: 0.4` |

*One of `start:` or `date:` is required.

### Year Numbers

Years are relative to the campaign calendar epoch (year 0 = calendar start):
- Positive years: after the epoch (e.g., `188` = year 188 HB in Menology of Epochs)
- Negative years: before the epoch (e.g., `-500` = 500 years before year 0)

**LK timestamp conversion:** `minutes = year * 525960` (365.25 × 24 × 60)

### Section → Lane Mapping

Each `## Section` becomes a **lane** in the LK timeline. Common lanes:

| Section Name | Suggested Use |
|-------------|---------------|
| `Eras` | Background epoch bands (low opacity) |
| `Declarations (Nianhao)` | Faction era declarations |
| `Historical Events` | Primary timeline events |
| `%%Secret%%` block | GM-only events (SECRET lane) |

### Common Icon Glyphs (Font Awesome names)

`flag` · `swords` · `star` · `scroll` · `house-flag` · `people-group` · `city`
`hat-wizard` · `hand-sparkles` · `seedling` · `droplet-slash` · `hourglass`
`wind` · `arrows-to-circle` · `arrows-maximize` · `crown` · `fire`

---

## Secret Content Handling

| Content | LK Markdown | LK JSON | HTML |
|---------|-------------|---------|------|
| `%%...%%` blocks | Converted to LK Secret section | SECRET lane (timeline); stripped (myth, Phase 2) | Stripped entirely |
| `visibility: gm_secrets` | No effect on content | No effect on content | File generated anyway; label added |

---

## Output Files

Given source file `narrative/myths/the-roads-a-fable.md`:

| Generator | Output | Location |
|-----------|--------|----------|
| `generate_lk_markdown.py` | `the-roads-a-fable-lk.md` | Alongside source (or `--output`) |
| `generate_lk_json.py` | `the-roads-a-fable.json` | Alongside source (or `--output`) |
| `generate_world_html.py` | `the-roads-a-fable.html` | `docs/` (or `--output`) |

---

## Pipeline Runner

```bash
# Generate all outputs
python utilities/legendkeeper-pipeline/publish.py \
  --source narrative/myths/the-roads-a-fable.md \
  --output docs/ \
  --all

# Generate only HTML
python utilities/legendkeeper-pipeline/publish.py \
  --source narrative/myths/the-roads-a-fable.md \
  --html

# Generate LK JSON for a timeline
python utilities/legendkeeper-pipeline/publish.py \
  --source world/timelines/nianhao.md \
  --lk-json
```
