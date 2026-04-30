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
# CSS is now linked externally via page_shell.build_page(extra_css=('page-ancestry',))
# Source: utilities/shared/css/page-ancestry.css
# ---------------------------------------------------------------------------

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
            "visibility": "public",  # overwritten by main() from per-ancestry file
            "image_url":  None,      # overwritten by main() from per-ancestry file
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
    items = [
        '  <li style="list-style:none"><a href="index.html">&larr; Campaign Documents</a></li>',
        '  <li class="nav-divider"></li>',
    ]
    for key in order:
        world_name = parsed_map[key]["world_name"]
        dh_name    = parsed_map[key]["dh_name"]
        label = escape(world_name)
        if dh_name.lower() != world_name.lower():
            label += f' <span class="nav-dh-name">({escape(dh_name)})</span>'
        items.append(f'  <li><a href="#{slug(world_name)}">{label}</a></li>')
    items.append('  <li class="nav-divider"></li>')
    items.append('  <li style="list-style:none"><a href="#">&#8593; Top</a></li>')
    return '<div class="jump-nav">\n<ul>\n' + '\n'.join(items) + '\n</ul>\n</div>\n'


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
      <div class="ancestry-entry">
        <div class="ancestry-header">
          <span class="ancestry-name">{escape(world_name)}</span>
          <span class="ancestry-dh-name">{escape(dh_name)}</span>
        </div>
        <div class="ancestry-lore">{figure_html}
          {lore_html}
        </div>
      </div>
      <div class="feature-grid">{feature_boxes}
      </div>
    </div>
"""


def build_content(parsed_map: dict[str, dict]) -> tuple[str, str]:
    # Honour visibility: only public ancestries appear in the published HTML
    order = sorted(
        [k for k, v in parsed_map.items() if v.get("visibility", "public") == "public"],
        key=lambda k: parsed_map[k]["world_name"].lower(),
    )
    jump_nav = build_jump_nav(order, parsed_map)
    parts = []
    for i, key in enumerate(order):
        parts.append(build_ancestry_section(key, parsed_map[key]))
        if i < len(order) - 1:
            parts.append('    <div class="ancestry-divider"></div>\n')
    return jump_nav, "".join(parts)


# ---------------------------------------------------------------------------
# Per-ancestry metadata lookup
# ---------------------------------------------------------------------------

def read_ancestry_metadata(dh_name: str) -> dict:
    """Read visibility and image from world/ancestries/{dh_name.lower()}.md.

    Returns a dict with keys:
      visibility  — 'public' (default) or 'gm_secrets'
      image_fname — bare image filename from first ![[...]] link, or None

    Both fields are sourced from the per-ancestry canonical file so that
    PEOPLES_OF_TARIM_SHAIEL.md carries no metadata of its own — consistent
    with the eventual Obsidian transclusion architecture (issue #79 Phase 2).
    """
    candidate = ANCESTRY_DIR / f"{dh_name.lower()}.md"
    if not candidate.exists():
        return {"visibility": "public", "image_fname": None}

    text = candidate.read_text(encoding="utf-8")

    # Read HTML inclusion gate from YAML frontmatter.
    # `published: true` takes precedence — it separates "source file is GM-only"
    # from "ancestry appears in the player-facing HTML".
    # Falls back to `visibility: public` for backward compatibility.
    visibility = "public"
    fm_match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if fm_match:
        fm_body = fm_match.group(1)
        pub = re.search(r'^published:\s*(\S+)', fm_body, re.MULTILINE | re.IGNORECASE)
        if pub:
            visibility = "public" if pub.group(1).lower() in ("true", "yes", "1") else "gm_secrets"
        else:
            vis = re.search(r'^visibility:\s*(\S+)', fm_body, re.MULTILINE | re.IGNORECASE)
            if vis:
                visibility = vis.group(1).lower()

    # Find first image wiki-link in body
    image_fname = None
    img = re.search(
        r'!\[\[([^\]|]+?\.(png|jpg|jpeg|webp|gif|svg))(?:\|[^\]]*)?\]\]',
        text, re.IGNORECASE
    )
    if img:
        image_fname = Path(img.group(1).strip()).name

    return {"visibility": visibility, "image_fname": image_fname}


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

    # Read visibility and image from per-ancestry canonical files
    for data in parsed_map.values():
        meta = read_ancestry_metadata(data["dh_name"])
        data["visibility"] = meta["visibility"]
        if meta["image_fname"]:
            data["image_url"] = prepare_image(meta["image_fname"], VAULT_ROOT, DOCS_DIR)

    jump_nav_html, content_html = build_content(parsed_map)

    credits_html = (
        "    Tarim-Shaiel &middot; Ancestry Guide &middot; "
        "Peoples of Tarim-Shaiel &middot; 2026\n"
    )

    html = build_page(
        title="Peoples of Tarim-Shaiel",
        cover_subtitle="Ancestries of the Known World",
        banner_left="Ancestry Guide",
        banner_right="Peoples of Tarim-Shaiel · Daggerheart",
        content_html=content_html,
        credits_html=credits_html,
        cover_image_url=COVER_IMAGE_URL,
        extra_css=('page-ancestry',),
        generator_name="utilities/ancestries/generate_ancestry_html.py",
        jump_nav_html=jump_nav_html,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    published = sum(1 for v in parsed_map.values() if v.get("visibility", "public") == "public")
    skipped   = len(parsed_map) - published
    print(f"Generated: {out_path}")
    print(f"  Ancestries: {published} published" + (f", {skipped} skipped (gm_secrets)" if skipped else ""))


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
