#!/usr/bin/env python3
"""
Homepage generator — produces docs/index.html
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
UTILITIES_DIR = SCRIPT_DIR.parent
VAULT_ROOT = UTILITIES_DIR.parent
DOCS_DIR = VAULT_ROOT / "docs"

sys.path.insert(0, str(UTILITIES_DIR))
sys.path.insert(0, str(UTILITIES_DIR / "world"))

from shared.renderer import render_page
from shared.frontmatter import parse_frontmatter

FEATURED_DOCS = [
    {
        "tag": "Player-Facing · v2.0",
        "title": "Campaign Frame",
        "sub": "Themes, principles, and Session Zero questions.",
        "href": "/campaign-frame.html",
    },
    {
        "tag": "Ancestry Guide · 14 Peoples",
        "title": "Peoples of Tarim-Shaiel",
        "sub": "Lore descriptions and features for character creation.",
        "href": "/peoples-of-tarim-shaiel.html",
    },
    {
        "tag": "World Lore",
        "title": "The Roads",
        "sub": "History, factions, and the shape of the known world.",
        "href": "/lore/the-roads.html",
    },
]

# Categories suppressed from the homepage (subcategories, GM-only, or low-value index noise)
SUPPRESS_FROM_HOME = {
    "advanced-weapons", "improved-weapons", "legendary-weapons",
    "magical-weapons", "powder-weapons", "special-weapons",
    "gm_secrets", "narrative", "events", "timelines",
}

ANCESTRY_NAMES = [
    "Div-Born", "Gavar", "Human", "Jivar", "Kalan", "Khavar",
    "Kuhban", "Pari-Kin", "Rahban", "Serenvar", "Tadbir",
    "Tulpar", "Vaghri", "Vanara",
]


def _ancestry_anchor(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "")


def _build_world_categories(gm_mode: bool = False) -> list[dict]:
    """Dynamically build category cards from _category.md files in the vault."""
    from generate_all_world_html import _read_category_config, _category_label, discover_sources

    buckets = discover_sources(VAULT_ROOT, gm_mode=gm_mode)
    categories = []
    for folder in sorted(buckets):
        if folder in SUPPRESS_FROM_HOME:
            continue
        cfg, _ = _read_category_config(VAULT_ROOT, folder)
        if cfg.get("published") is False:
            continue
        title = cfg.get("title") or _category_label(folder)
        desc = cfg.get("description") or ""
        tag = cfg.get("tag") or cfg.get("banner_left") or "World"
        count = len(buckets[folder])
        categories.append({
            "tag": f"{tag} · {count} docs",
            "title": title,
            "sub": desc,
            "href": f"/category-{folder}.html",
        })
    return categories


def main(argv=None) -> int:
    import os
    gm_mode = os.environ.get('TS_GM_MODE') == '1'
    out = DOCS_DIR / "index.html"

    ancestry_links = [
        {"name": a, "anchor": _ancestry_anchor(a)}
        for a in ANCESTRY_NAMES
    ]

    world_categories = _build_world_categories(gm_mode=gm_mode)

    html = render_page(
        "pages/homepage.html",
        title="Tarim-Shaiel",
        cover_subtitle="A Daggerheart Campaign",
        eyebrow="Campaign Hub",
        extra_css=["page-index"],
        generator_name="utilities/homepage/generate_homepage.py",
        featured_docs=FEATURED_DOCS,
        world_categories=world_categories,
        ancestry_links=ancestry_links,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Generated: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


class _Generator:
    name = "homepage"
    description = "Campaign homepage / index (docs/index.html)"

    def run(self, argv=None) -> int:
        return main(argv)


generator = _Generator()
