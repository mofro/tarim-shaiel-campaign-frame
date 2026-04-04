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

SCRIPT_DIR  = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
DOCS_DIR    = VAULT_ROOT / "docs"
SOURCE_PATH = VAULT_ROOT / "world" / "ancestries" / "PEOPLES_OF_TARIM_SHAIEL.md"
OUTPUT_PATH = DOCS_DIR / "peoples-of-tarim-shaiel.html"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.page_shell import build_page

COVER_IMAGE_URL = "https://images5.alphacoders.com/798/thumb-1920-798802.jpg"

# ---------------------------------------------------------------------------
# Ancestry metadata
# Maps heading key → world name + Daggerheart system name.
# Feature flavor text lives in PEOPLES_OF_TARIM_SHAIEL.md under each
# ancestry's "### Ancestry Features" subsection — parsed at runtime.
# ---------------------------------------------------------------------------

ANCESTRY_DATA = {
    "VANARA":    {"world_name": "Vanara",   "dh_name": "Simiah"},
    "DIV-BORN":  {"world_name": "Div-Born", "dh_name": "Infernis"},
    "GAVAR":     {"world_name": "Gavar",    "dh_name": "Firbolg"},
    "TADBIR":    {"world_name": "Tadbir",   "dh_name": "Clank"},
    "PARI-KIN":  {"world_name": "Pari-Kin", "dh_name": "Faun"},
    "KHAVAR":    {"world_name": "Khavar",   "dh_name": "Fungril"},
    "HUMAN":     {"world_name": "Human",    "dh_name": "Human"},
    "ELF":       {"world_name": "Elf",      "dh_name": "Elf"},
    "DWARF":     {"world_name": "Dwarf",    "dh_name": "Dwarf"},
    "ORC":       {"world_name": "Orc",      "dh_name": "Orc"},
    "KATARI":    {"world_name": "Katari",   "dh_name": "Katari"},
    "GOBLIN":    {"world_name": "Goblin",   "dh_name": "Goblin"},
    "HALFLING":  {"world_name": "Halfling", "dh_name": "Halfling"},
    "GIANT":     {"world_name": "Giant",    "dh_name": "Giant"},
}

# Rendering order
ANCESTRY_ORDER = [
    "VANARA", "DIV-BORN", "GAVAR", "TADBIR", "PARI-KIN", "KHAVAR",
    "HUMAN", "ELF", "DWARF", "ORC", "KATARI", "GOBLIN", "HALFLING", "GIANT",
]

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
        m = re.match(r"## ([A-Z][A-Z\-]*)", heading)
        if not m:
            continue
        key = m.group(1)

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

        result[key] = {"lore": lore_text, "features": features}

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

def build_jump_nav(order: list[str]) -> str:
    links = []
    for key in order:
        world_name = ANCESTRY_DATA[key]["world_name"]
        links.append(f'<a href="#{slug(world_name)}">{escape(world_name)}</a>')
    return (
        '\n    <div class="jump-nav">\n      '
        + "\n      ".join(links)
        + "\n    </div>\n"
    )


def build_ancestry_section(key: str, parsed: dict) -> str:
    data      = ANCESTRY_DATA[key]
    world_name = data["world_name"]
    dh_name    = data["dh_name"]
    features   = parsed.get("features", [])
    lore_text  = parsed.get("lore", "")
    anchor     = slug(world_name)

    if not features:
        print(f"  WARNING: no ### Ancestry Features found for {key}")

    lore_html = paragraphs_html(lore_text)

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
      <div class="ancestry-lore">
        {lore_html}
      </div>
      <div class="feature-grid">{feature_boxes}
      </div>
    </div>
"""


def build_content(parsed_map: dict[str, dict]) -> str:
    parts = [build_jump_nav(ANCESTRY_ORDER)]
    for i, key in enumerate(ANCESTRY_ORDER):
        parsed = parsed_map.get(key, {"lore": "", "features": []})
        parts.append(build_ancestry_section(key, parsed))
        if i < len(ANCESTRY_ORDER) - 1:
            parts.append('    <div class="ancestry-divider"></div>\n')
    return "".join(parts)


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

    # Warn if any requested ancestry is missing from the source file
    for key in ANCESTRY_ORDER:
        if key not in parsed_map:
            print(f"WARNING: '{key}' not found in {SOURCE_PATH.name}")

    content_html = build_content(parsed_map)

    credits_html = (
        "    Tarim-Shaiel &middot; Ancestry Guide &middot; "
        "Peoples of Tarim-Shaiel &middot; 2026\n"
    )

    html = build_page(
        title="Peoples of Tarim-Shaiel",
        cover_subtitle="Fourteen Ancestries of the Known World",
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
    print(f"  Ancestries: {len(ANCESTRY_ORDER)}")


if __name__ == "__main__":
    main()
