---
title: GM Content Authoring Guide
project: TTRPG_Tarim_Shaiel
type: operational
visibility: internal
status: canon
created: 2026-04-22
last_updated: 2026-04-22
---

# GM Content Authoring Guide

Reference for all four content-gating levels in the Tarim-Shaiel publishing pipeline. All gating is **build-time** — nothing is hidden client-side. Players who visit the public site can never see GM content, even via DevTools.

---

## Gating Level Summary

| Level | Syntax | Scope | Public output | GM output |
|---|---|---|---|---|
| Page-level | `visibility: gm_secrets` frontmatter | Entire file | File never generated | Full page with crimson top border + "GM EYES ONLY" banner |
| Tier 1 | `{gm:text}` | Single word/phrase inline | `██████` redaction bar | Crimson underline span |
| Tier 2 | `> [!gm-only]` callout block | Paragraph(s) in a public doc | Stripped entirely | Crimson left-border callout |
| Tier 3 | `![[gm_secrets/filename]]` | Arbitrary-length content from a separate file | Stripped entirely | Rendered with crimson left border, "↓ GM CONTENT" label |

---

## Page-Level Gating

Set `visibility: gm_secrets` in the file's frontmatter. The entire file is excluded from `--public` builds. No other changes needed.

For mixed-visibility files (public doc with embedded GM notes), use Tier 1–3 instead.

### Revealing a location to players (map + site)

When players discover a `gm_secrets` location, run the **tp-reveal-location** Templater template on the file:

1. Open the location file in Obsidian
2. `Cmd+P` → **Templater: Open Insert Template Modal** → **tp-reveal-location**
3. Frontmatter updates automatically: `visibility: public`, `revealed: YYYY-MM-DD`, `last_updated: YYYY-MM-DD`
4. Commit + push → Netlify rebuilds → marker appears on player map

The template is at `templates/tarim-shaiel-templates/tp-reveal-location.md`.

**What changes on reveal:**
- `visibility: gm_secrets` → `visibility: public` (makes it visible in public builds)
- `revealed: YYYY-MM-DD` added (audit trail — when players found it)
- Map marker: was dimmed on GM map, now full opacity on both maps
- Location detail page: now generated in public build

**Important:** After running the template, you must also regenerate the GeoJSON for the Obsidian vault maps to update:
```bash
python utilities/build.py geojson
```
The Netlify HTML build reads frontmatter directly — no GeoJSON regeneration needed for the deployed site.

---

## Tier 1 — Inline Redaction: `{gm:text}`

For a single word, name, number, or short phrase that must stay hidden in a sentence.

**Syntax:**
```
The Wizard's true name is {gm:Sylaveth Vorn}, bound to the Sixth Warren.
The chest contains {gm:1,200 gp and a +2 dagger named Ashwhisper}.
```

**Public output:** `<span class="gm-redacted">██████</span>` — a black-on-black bar.  
Players see a thematic redaction signal that information exists but is withheld.

**GM output:** `<span class="gm-inline">Sylaveth Vorn</span>` — crimson underline.

**Obsidian:** Renders as literal `{gm:...}` text — readable in vault, doesn't break other syntax.

**When to use:** A name, a number, a single suppressed fact. Any longer GM note → Tier 2 or 3.

---

## Tier 2 — Block Callout: `> [!gm-only]`

For paragraph-length GM notes (hidden motivations, trap details, spoiler annotations) embedded within a public document.

**Syntax:**
```markdown
The ruin was abandoned before the empire fell.

> [!gm-only]
> That's the official story. Players will learn the tower was sealed after
> a containment failure — the Held Breath "Dust of the Closed Eye" nearly
> awakened here in 1209 CE.
>
> They can find the truth in the sealed lower chamber (Perception DC 16).

The locals avoid it entirely.
```

**Public output:** The entire callout block is stripped. No trace in the DOM.

**GM output:** Crimson left-border callout with "GM ONLY" label above the content.

**Multi-paragraph:** Use `>` alone on blank lines to continue the callout. If you leave a truly blank line (no `>`), the block is split into two paragraphs — use `>` on every line including blanks.

**Supports:** Multiple paragraphs, lists, inline markdown, Tier 1 `{gm:...}` markers within the block.

**Does not support:** Nested headings inside the callout. Use Tier 3 for content with headers or tables.

**Obsidian:** Renders as a styled callout in vault preview. Clearly visible during authoring.

**When to use:** A GM annotation, hidden NPC motivation, encounter note. Anything up to a few paragraphs that lives inside a public document.

---

## Tier 3 — File Transclusion: `![[gm_secrets/filename]]`

For arbitrary-length GM content: full scene descriptions, encounter tables, stat blocks, anything with headers, tables, or multiple sections.

**Syntax:**
```markdown
## The Black Palace — Ground Floor

The ground floor is accessible via the collapsed east wall.

![[gm_secrets/black_palace_ground_floor_gm_notes]]

The inner sanctum is locked with a puzzle lock (DC 18 Investigation).
```

**Public output:** The embed line is stripped entirely.

**GM output:** The referenced `.md` file is located via vault search, its body rendered, and wrapped in a `<div class="gm-block">` with "↓ GM CONTENT" label and crimson border.

**Path convention:** Always use `gm_secrets/` as a prefix in the `![[...]]` reference so the pipeline can detect it without a file lookup. The filename stem without extension is sufficient:
- `![[gm_secrets/filename]]` → resolves `filename.md` anywhere in the vault

**File creation workflow:**
1. Create the file in the appropriate `gm_secrets/` subdirectory (e.g. `world/locations/gm_secrets/black_palace_gm.md`)
2. Add `visibility: gm_secrets` to its frontmatter
3. Reference it from the public parent doc with `![[gm_secrets/black_palace_gm]]`

**Supports:** Full markdown — headings, tables, lists, audio embeds, Tier 1 `{gm:...}` and Tier 2 `> [!gm-only]` within the transcluded file.

**Obsidian:** Renders as a full embedded document (native wikilink transclusion).

**When to use:** A full scene description, stat block, encounter table, or any section with headers — anything too large or structured for a Tier 2 callout.

---

## Decision Guide: Which Tier?

| Scenario | Use |
|---|---|
| A name, a number, a single fact | Tier 1 `{gm:...}` |
| A GM note, hidden motivation, spoiler annotation (up to a few paragraphs) | Tier 2 `> [!gm-only]` |
| A full scene, encounter table, stat block, anything with headers | Tier 3 `![[gm_secrets/...]]` |
| An entire file is GM-only | Page-level `visibility: gm_secrets` frontmatter |

---

## Build Behavior Reference

| Build command | Tier 1 | Tier 2 | Tier 3 | Page-level gm_secrets |
|---|---|---|---|---|
| `build.py all --public` | `██████` bars | Stripped | Stripped | File skipped |
| `build.py all` (local) | `██████` bars | Stripped | Stripped | Rendered (no auth) |
| `build.py all --gm` | Crimson spans | Crimson callouts | GM blocks | Rendered, crimson banner |

**Note:** The local run (`build.py all` with no flag) generates `gm_secrets` pages for GM preview, but does NOT inject the Netlify Identity auth guard. Use `--gm` for the deployed GM site.

---

## Netlify Setup (manual, one-time)

The GM deploy uses a second Netlify site pointing at this repo with `netlify-gm.toml` as the build config:

1. In Netlify UI: Add new site → same GitHub repo
2. Override build settings: build command `python utilities/build.py all --gm`, publish dir `docs`
3. Site settings → Identity → Enable → set registration to **Invite only**
4. Identity → Invite users → your email → follow invite link to set a password
5. Keep the GM site URL private (Netlify subdomain URLs are not enumerable)

After login, the JWT persists in `localStorage` (default 60-day expiry) — no re-login on each visit.
