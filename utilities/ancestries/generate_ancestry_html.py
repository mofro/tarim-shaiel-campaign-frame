#!/usr/bin/env python3
"""
Peoples of Tarim-Shaiel — Ancestry HTML Generator
==================================================
Reads world/ancestries/PEOPLES_OF_TARIM_SHAIEL.md and builds
docs/peoples-of-tarim-shaiel.html using the shared parchment design system.

Each ancestry entry mirrors the canonical Daggerheart format:
  - World name (Daggerheart system name in small type)
  - 3-paragraph lore description
  - Two named feature boxes with in-world flavor text

Feature flavor text lives in PEOPLES_OF_TARIM_SHAIEL.md under each
ancestry's "### Ancestry Features" subsection — parsed at runtime.

Usage:
    python utilities/ancestries/generate_ancestry_html.py
    python utilities/ancestries/generate_ancestry_html.py --out docs/custom.html
"""

import re
import sys
import argparse
from pathlib import Path
from html import escape

SCRIPT_DIR   = Path(__file__).parent
VAULT_ROOT   = SCRIPT_DIR.parent.parent
DOCS_DIR     = VAULT_ROOT / "docs"
SOURCE_PATH  = VAULT_ROOT / "world" / "ancestries" / "PEOPLES_OF_TARIM_SHAIEL.md"
ANCESTRY_DIR = VAULT_ROOT / "world" / "ancestries"
OUTPUT_PATH  = DOCS_DIR / "peoples-of-tarim-shaiel.html"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.page_shell import build_page
from shared.assets import prepare_image

COVER_IMAGE_URL = "https://images5.alphacoders.com/798/thumb-1920-798802.jpg"

# ---------------------------------------------------------------------------
# Ancestry metadata
# Maps heading key → world name + Daggerheart system name.
# Feature flavor text lives in PEOPLES_OF_TARIM_SHAIEL.md under each
# ancestry's "### Ancestry Features" subsection — parsed at runtime.
# ---------------------------------------------------------------------------

# Ancestry metadata is derived at runtime from PEOPLES_OF_TARIM_SHAIEL.md.
# Rendering order follows document order in that file.

# ---------------------------------------------------------------------------
# CSS (extends CSS_BASE from page_shell)
# ---------------------------------------------------------------------------

CSS_ANCESTRY = """\

    @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;500&display=swap');

    body {
      background: #1a1208;
      background-image: url('images/paper-texture-top-view-2.jpg');
      font-family: 'EB Garamond', Georgia, serif;
      font-size: 17px;
      line-height: 1.72;
      color: var(--ink);
    }

    .cover { min-height: 280px; }

    .content {
      position: relative;
      z-index: 1;
      padding: 0 3rem 3.5rem;
    }

    /* ---- Jump navigation ---- */

    .jump-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem 1.1rem;
      padding: 1.1rem 0 1.4rem;
      border-bottom: 1px solid var(--rule);
      margin-bottom: 2.8rem;
      font-family: 'Cinzel', serif;
      font-size: 0.7rem;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }

    .jump-nav a {
      color: var(--gold);
      text-decoration: none;
      transition: color 0.15s;
    }

    .jump-nav a:hover { color: var(--gold-light); }

    /* ---- Ancestry section ---- */

    .ancestry-section { scroll-margin-top: 1.5rem; }

    .ancestry-header { margin-bottom: 1.1rem; }

    .ancestry-name {
      display: block;
      font-family: 'Cinzel', serif;
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--crimson);
      letter-spacing: 0.04em;
      line-height: 1.15;
    }

    .ancestry-dh-name {
      font-family: 'Inconsolata', monospace;
      font-size: 0.76rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--steel);
      opacity: 0.75;
    }

    .ancestry-lore p {
      margin-bottom: 0.85rem;
      font-size: 1.02rem;
    }

    .ancestry-lore p:last-child { margin-bottom: 0; }

    /* ---- Feature boxes ---- */

    .feature-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.9rem;
      margin-top: 1.3rem;
    }

    .feature-box {
      background: var(--parchment2);
      border: 1px solid var(--rule);
      border-radius: 2px;
      padding: 0.95rem 1.1rem 1rem;
      box-shadow: inset 0 1px 4px rgba(26,18,8,0.06);
    }

    .feature-name {
      font-family: 'Cinzel', serif;
      font-size: 0.76rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--steel);
      margin-bottom: 0.45rem;
      padding-bottom: 0.35rem;
      border-bottom: 1px solid var(--rule);
    }

    .feature-box p {
      font-size: 0.95rem;
      line-height: 1.6;
      margin: 0;
    }

    /* ---- Ancestry image figure ---- */

    .lore-figure {
      float: right;
      margin: 0.4rem 0 1.6rem 2rem;
      max-width: 240px;
      clear: right;
    }

    .lore-figure img {
      width: 100%;
      display: block;
      border: 1px solid var(--rule);
      box-shadow: 4px 6px 18px var(--shadow);
    }

    .lore-figure figcaption {
      font-size: 0.8rem;
      font-style: italic;
      color: var(--steel);
      text-align: center;
      margin-top: 0.45rem;
      padding-top: 0.35rem;
      border-top: 1px solid var(--rule);
      line-height: 1.4;
    }

    @media (max-width: 640px) {
      .lore-figure { float: none; max-width: 100%; margin: 0 0 1.5rem 0; }
    }

    /* ---- Divider between ancestries ---- */

    .ancestry-divider {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--rule), transparent);
      margin: 2.4rem 0;
    }

    @media (max-width: 640px) {
      .content { padding: 0 1.4rem 2.5rem; }
      .feature-grid { grid-template-columns: 1fr; }
      .jump-nav { gap: 0.4rem 0.9rem; }
    }
"""

# ---------------------------------------------------------------------------
# Parse PEOPLES_OF_TARIM_SHAIEL.md
# ---------------------------------------------------------------------------

def parse_peoples_md(path: Path) -> dict[str, dict]:
    """Parse the source markdown into structured ancestry data.

    Returns:
        {HEADING_KEY: {"lore": str, "features": [{"name": str, "flavor": str}]}}

    HEADING_KEY is the uppercase name from the ## heading, e.g. 'VANARA'.
    lore is the prose paragraphs before ### Ancestry Features.
    features is a list of {name, flavor} dicts parsed from **Name:** blocks.
    """
    raw = path.read_text(encoding="utf-8")
    chunks = re.split(r'\n(?=## [A-Z])', raw)
    result = {}

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("## "):
            continue
        lines = chunk.splitlines()
        heading = lines[0]
        m = re.match(r"## ([A-Z][A-Z\-]*)(?:\s+\(([^)]+)\))?", heading)
        if not m:
            continue
        key        = m.group(1)
        world_name = key.title()               # "VANARA" → "Vanara", "DIV-BORN" → "Div-Born"
        dh_name    = m.group(2) or world_name  # "Simiah" if present, else same as world_name

        body = "\n".join(lines[1:]).strip()
        body = re.sub(r'\n---\s*$', '', body).strip()

        # Split lore from ### Ancestry Features subsection
        parts = re.split(r'\n### Ancestry Features\n', body, maxsplit=1)
        lore_text = parts[0].strip()

        features = []

        if len(parts) > 1:
            feat_block = parts[1].strip()
            # Format is **Feature Name:** flavor text (colon inside bold markers)
            for para in feat_block.split('\n\n'):
                fm = re.match(r'\*\*(.+?):\*\*\s*(.+)', para.strip(), re.DOTALL)
                if fm:
                    features.append({
                        "name":   fm.group(1).strip(),
                        "flavor": fm.group(2).strip(),
                    })

        result[key] = {
            "world_name": world_name,
            "dh_name":    dh_name,
            "lore":       lore_text,
            "features":   features,
            "image_url":  None,   # filled by main() via per-ancestry file lookup
        }

    return result


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def paragraphs_html(text: str) -> str:
    """Convert blank-line-separated plain text into <p> tags."""
    paras = re.split(r'\n{2,}', text.strip())
    parts = []
    for p in paras:
        p = p.strip()
        if p:
            parts.append(f"<p>{escape(p)}</p>")
    return "\n".join(parts)


def slug(name: str) -> str:
    return re.sub(r'\s+', '-', name.lower())


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

def build_jump_nav(order: list[str], parsed_map: dict) -> str:
    links = []
    for key in order:
        world_name = parsed_map[key]["world_name"]
        links.append(f'<a href="#{slug(world_name)}">{escape(world_name)}</a>')
    return (
        '\n    <div class="jump-nav">\n      '
        + "\n      ".join(links)
        + "\n    </div>\n"
    )


def build_ancestry_section(key: str, parsed: dict) -> str:
    world_name = parsed["world_name"]
    dh_name    = parsed["dh_name"]
    features   = parsed.get("features", [])
    lore_text  = parsed.get("lore", "")
    anchor     = slug(world_name)

    if not features:
        print(f"  WARNING: no ### Ancestry Features found for {key}")

    image_url  = parsed.get("image_url")
    lore_html  = paragraphs_html(lore_text)

    figure_html = ""
    if image_url:
        figure_html = (
            f'\n        <figure class="lore-figure">'
            f'\n          <img src="{escape(image_url)}" alt="">'
            f'\n          <figcaption>{escape(world_name)}</figcaption>'
            f'\n        </figure>'
        )

    feature_boxes = ""
    for feat in features:
        feature_boxes += (
            f'\n          <div class="feature-box">'
            f'\n            <div class="feature-name">{escape(feat["name"])}</div>'
            f'\n            <p>{escape(feat["flavor"])}</p>'
            f"\n          </div>"
        )

    return f"""\
    <div class="ancestry-section" id="{anchor}">
      <div class="ancestry-header">
        <span class="ancestry-name">{escape(world_name)}</span>
        <span class="ancestry-dh-name">{escape(dh_name)}</span>
      </div>
      <div class="ancestry-lore">{figure_html}
        {lore_html}
      </div>
      <div class="feature-grid">{feature_boxes}
      </div>
    </div>
"""


def build_content(parsed_map: dict[str, dict]) -> str:
    order = list(parsed_map.keys())
    parts = [build_jump_nav(order, parsed_map)]
    for i, key in enumerate(order):
        parts.append(build_ancestry_section(key, parsed_map[key]))
        if i < len(order) - 1:
            parts.append('    <div class="ancestry-divider"></div>\n')
    return "".join(parts)


# ---------------------------------------------------------------------------
# Per-ancestry image lookup
# ---------------------------------------------------------------------------

def find_ancestry_image(dh_name: str) -> str | None:
    """Scan world/ancestries/{dh_name.lower()}.md for an Obsidian ![[filename]] image link.

    Returns the bare filename (e.g. 'storyteller.png'), or None if no detail
    file exists or no image wiki-link is found. The generator calls this for each
    ancestry so images are sourced from per-ancestry canonical files, not from
    the consolidated PEOPLES_OF_TARIM_SHAIEL.md. This is compatible with the
    eventual Obsidian transclusion architecture (issue #79 Phase 2).
    """
    candidate = ANCESTRY_DIR / f"{dh_name.lower()}.md"
    if not candidate.exists():
        return None
    text = candidate.read_text(encoding="utf-8")
    m = re.search(
        r'!\[\[([^\]|]+?\.(png|jpg|jpeg|webp|gif|svg))(?:\|[^\]]*)?\]\]',
        text, re.IGNORECASE
    )
    if not m:
        return None
    return Path(m.group(1).strip()).name


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the Peoples of Tarim-Shaiel ancestry HTML page."
    )
    parser.add_argument(
        "--out", default=None,
        help="Output path (default: docs/peoples-of-tarim-shaiel.html)"
    )
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else OUTPUT_PATH

    parsed_map = parse_peoples_md(SOURCE_PATH)

    # Resolve images from per-ancestry detail files (world/ancestries/{dh_name}.md)
    for data in parsed_map.values():
        fname = find_ancestry_image(data["dh_name"])
        if fname:
            data["image_url"] = prepare_image(fname, VAULT_ROOT, DOCS_DIR)

    content_html = build_content(parsed_map)

    credits_html = (
        "    Tarim-Shaiel &middot; Ancestry Guide &middot; "
        "Peoples of Tarim-Shaiel &middot; 2026\n"
    )

    html = build_page(
        title="Peoples of Tarim-Shaiel",
        cover_subtitle=f"{len(parsed_map)} Ancestries of the Known World",
        banner_left="Ancestry Guide",
        banner_right="Peoples of Tarim-Shaiel · Daggerheart",
        content_html=content_html,
        credits_html=credits_html,
        cover_image_url=COVER_IMAGE_URL,
        css_extra=CSS_ANCESTRY,
        generator_name="utilities/ancestries/generate_ancestry_html.py",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path}")
    print(f"  Ancestries: {len(parsed_map)}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Generator protocol wrapper (used by utilities/build.py)
# ---------------------------------------------------------------------------
class _Generator:
    name = "ancestry"
    description = "Generate the Peoples of Tarim-Shaiel ancestry HTML page"

    def run(self, argv=None):
        import sys as _sys
        _saved = _sys.argv[1:]
        if argv is not None:
            _sys.argv[1:] = list(argv)
        try:
            result = main()
            return result if isinstance(result, int) else 0
        except SystemExit as e:
            return int(e.code) if isinstance(e.code, int) else 0
        finally:
            _sys.argv[1:] = _saved


generator = _Generator()
