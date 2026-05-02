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

from shared.renderer import render_page

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
    {
        "tag": "World Index",
        "title": "World Documents",
        "sub": "Locations, factions, myths, and timelines.",
        "href": "/world-index.html",
    },
]

WORLD_CATEGORIES = [
    {"tag": "Mechanics", "title": "Abilities", "sub": "Active and passive abilities across all classes.", "href": "/category-abilities.html"},
    {"tag": "Character Creation", "title": "Classes", "sub": "Character archetypes and their advancement paths.", "href": "/category-classes.html"},
    {"tag": "Character Creation", "title": "Domains", "sub": "Domain cards and domain-specific rules.", "href": "/category-domains.html"},
    {"tag": "World", "title": "Factions", "sub": "Powers, guilds, and political bodies of Tarim-Shaiel.", "href": "/category-factions.html"},
    {"tag": "World", "title": "World Index", "sub": "All world documents: lore, myths, timelines, and more.", "href": "/world-index.html"},
    {"tag": "Game Master", "title": "Dashboard", "sub": "Project health, TODO tracker, and session log.", "href": "/dashboard.html"},
]

ANCESTRY_NAMES = [
    "Div-Born", "Gavar", "Human", "Jivar", "Kalan", "Khavar",
    "Kuhban", "Pari-Kin", "Rahban", "Serenvar", "Tadbir",
    "Tulpar", "Vaghri", "Vanara",
]


def _ancestry_anchor(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "")


def main(argv=None) -> int:
    out = DOCS_DIR / "index.html"

    ancestry_links = [
        {"name": a, "anchor": _ancestry_anchor(a)}
        for a in ANCESTRY_NAMES
    ]

    html = render_page(
        "pages/homepage.html",
        title="Tarim-Shaiel",
        cover_subtitle="A Daggerheart Campaign",
        eyebrow="Campaign Hub",
        extra_css=["page-index"],
        generator_name="utilities/homepage/generate_homepage.py",
        featured_docs=FEATURED_DOCS,
        world_categories=WORLD_CATEGORIES,
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
