#!/usr/bin/env python3
"""
Tarim-Shaiel Class Primer HTML Generator
=========================================
Reads world/classes/class_primer.md and renders it as docs/class-primer.html.
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
DOCS_DIR    = VAULT_ROOT / "docs"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.frontmatter import parse_frontmatter
from shared.html_render import render_body
from shared.renderer import render_page

SOURCE = VAULT_ROOT / "world" / "classes" / "class_primer.md"
OUTPUT = DOCS_DIR / "class-primer.html"


def main(argv=None) -> int:
    if not SOURCE.exists():
        print(f"ERROR: source file not found: {SOURCE}", file=sys.stderr)
        return 1

    raw = SOURCE.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    title    = fm.get("title") or "Character Classes"
    date_str = str(fm.get("last_updated") or fm.get("created") or "")

    body_html, _ = render_body(body, VAULT_ROOT, DOCS_DIR)

    html = render_page(
        "pages/lore.html",
        title=title,
        eyebrow="Character Classes",
        cover_subtitle="Character Classes · Tarim-Shaiel",
        banner_left="Character Classes",
        banner_right="Class Primer · Tarim-Shaiel",
        cover_image_url=None,
        extra_css=["page-lore"],
        generator_name="utilities/class_primer/generate_class_primer.py",
        audio_url=None,
        audio_title=None,
        audio_mime=None,
        description="Daggerheart classes framed for the world of Tarim-Shaiel.",
        body_html=body_html,
        date_str=date_str,
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Class primer generated: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


from shared.base_generator import make_generator
generator = make_generator(
    "class-primer",
    "Class primer page (docs/class-primer.html)",
    main,
)
