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

SCRIPT_DIR   = Path(__file__).parent
VAULT_ROOT   = SCRIPT_DIR.parent.parent
DOCS_DIR     = VAULT_ROOT / "docs"
SOURCE_PATH  = VAULT_ROOT / "world" / "ancestries" / "PEOPLES_OF_TARIM_SHAIEL.md"
ANCESTRY_DIR = VAULT_ROOT / "world" / "ancestries"
OUTPUT_PATH  = DOCS_DIR / "peoples-of-tarim-shaiel.html"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.assets import prepare_image
from shared.renderer import render_page

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
# CSS is now linked externally via render_page(extra_css=['page-ancestry'])
# Source: utilities/shared/css/page-ancestry.css
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Parse PEOPLES_OF_TARIM_SHAIEL.md
# ---------------------------------------------------------------------------

def parse_peoples_md(path: Path) -> dict[str, dict]:
    """Parse the source markdown into structured ancestry data.

    Returns:
        {HEADING_KEY: {"lore": str, "lore_paras": list[str],
                       "features": [{"name": str, "flavor": str}]}}

    HEADING_KEY is the uppercase name from the ## heading, e.g. 'VANARA'.
    lore is the prose text before ### Ancestry Features (kept for compat).
    lore_paras is lore split into a list of paragraph strings.
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
            "lore_paras": [p.strip() for p in lore_text.split('\n\n') if p.strip()],
            "features":   features,
            "visibility": "public",  # overwritten by main() from per-ancestry file
            "image_url":  None,      # overwritten by main() from per-ancestry file
        }

    return result


def slug(name: str) -> str:
    return re.sub(r'\s+', '-', name.lower())


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

    ancestries = sorted(
        [
            {
                "world_name": v["world_name"],
                "dh_name":    v["dh_name"],
                "anchor":     slug(v["world_name"]),
                "lore_paras": v["lore_paras"],
                "features":   v["features"],
                "image_url":  v.get("image_url"),
            }
            for v in parsed_map.values()
            if v.get("visibility", "public") == "public"
        ],
        key=lambda a: a["world_name"].lower(),
    )

    for a in ancestries:
        if not a["features"]:
            print(f"  WARNING: no ### Ancestry Features found for {a['world_name']}")

    jump_nav_items = [
        {"anchor": a["anchor"], "text": a["world_name"]}
        for a in ancestries
    ]

    html = render_page(
        "pages/ancestry.html",
        title="Peoples of Tarim-Shaiel",
        cover_subtitle="Ancestries of the Known World",
        eyebrow="Ancestry Guide",
        back_href="index.html",
        back_label="Campaign Documents",
        sidebar_heading="Peoples",
        jump_nav_items=jump_nav_items,
        cover_image_url=COVER_IMAGE_URL,
        extra_css=["page-ancestry"],
        generator_name="utilities/ancestries/generate_ancestry_html.py",
        ancestries=ancestries,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    skipped = len(parsed_map) - len(ancestries)
    print(f"Generated: {out_path}")
    print(f"  Ancestries: {len(ancestries)} published" + (f", {skipped} skipped (gm_secrets)" if skipped else ""))


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
