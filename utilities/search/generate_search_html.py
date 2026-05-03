#!/usr/bin/env python3
"""
Tarim-Shaiel Search Page Generator
=====================================
Renders the static search UI shell at docs/search.html.
The page fetches search-index.json at runtime and performs all
searching client-side via Lunr.js.

Usage:
    python utilities/search/generate_search_html.py
    python utilities/search/generate_search_html.py --public
"""

import os
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
DOCS_DIR = VAULT_ROOT / "docs"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.renderer import render_page


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate docs/search.html search UI page."
    )
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--gm", action="store_true")
    parser.parse_args()

    gm_mode = os.environ.get("TS_GM_MODE") == "1"

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out = DOCS_DIR / "search.html"

    html = render_page(
        "pages/search.html",
        title="Search · Tarim-Shaiel",
        page_title="Search",
        extra_css=["page-search"],
        generator_name="utilities/search/generate_search_html.py",
        gm_mode=gm_mode,
    )

    out.write_text(html, encoding="utf-8")
    print(f"Search page generated: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Generator protocol (used by utilities/build.py)
# ---------------------------------------------------------------------------

class _Generator:
    name = "search"
    description = "Generate search.html Lunr.js search UI page"

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
