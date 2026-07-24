#!/usr/bin/env python3
"""
Tarim-Shaiel Newspaper Generator
==================================
Reads per-story .md files from narrative/newspaper/<issue-slug>/ directories
and assembles them into HTML pages per issue.

Story file frontmatter fields:
  type: newspaper-story   (required)
  weight: lead | standard | brief | sidebar | editorial | reference
  order: 1                (sort position within the issue)
  page: 1                 (optional; target page; default 1)
  kicker, headline, dek, byline  (narrative story metadata)
  kind, title, items      (sidebar fields)
  title, entries          (reference fields)

Narrative body (lead / standard / editorial / brief) comes from the Markdown
body of the file, split on blank lines into paragraphs.

Optional manifest.md per issue directory:
  type: newspaper-manifest
  masthead:
    title, tagline, edition, date, issueNo

Usage:
  python utilities/newspaper/generate_newspaper_html.py
  python utilities/build.py newspaper
"""

import copy
import json
import sys
from pathlib import Path

SCRIPT_DIR  = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
DOCS_DIR    = VAULT_ROOT / "docs"
NEWS_SRC    = VAULT_ROOT / "narrative" / "newspaper"
NEWS_OUT    = DOCS_DIR / "newspaper"
CONFIG_PATH = VAULT_ROOT / "storytell_config.json"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.frontmatter import parse_frontmatter
from shared.renderer import render_page

LEAD_WORD_BUDGET = 600  # words per lead body fragment

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_np_config() -> dict:
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return cfg.get("newspaper", {})
    return {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_words(text: str) -> int:
    return len(text.split())


def _split_body(body_text: str) -> list:
    """Split Markdown body on blank lines → list of paragraph strings."""
    return [p.strip() for p in body_text.split("\n\n") if p.strip()]


def _paginate_lead(paragraphs: list, budget: int = LEAD_WORD_BUDGET):
    """Split at word-budget paragraph boundary. Returns (first_half, remainder)."""
    total = 0
    for i, para in enumerate(paragraphs):
        total += _count_words(para)
        if total >= budget and i < len(paragraphs) - 1:
            return paragraphs[: i + 1], paragraphs[i + 1 :]
    return paragraphs, []

# ---------------------------------------------------------------------------
# Story parsing
# ---------------------------------------------------------------------------

def _build_story(fm: dict, body: str) -> dict:
    """Build a story dict from already-parsed frontmatter and Markdown body."""
    weight = fm.get("weight", "")
    story = {
        "weight":              weight,
        "order":               int(fm.get("order", 99)),
        "page":                int(fm.get("page", 1)),
        "kicker":              fm.get("kicker", ""),
        "headline":            fm.get("headline", ""),
        "title":               fm.get("title", fm.get("headline", "")),
        "dek":                 fm.get("dek", ""),
        "byline":              fm.get("byline", ""),
        "image":               bool(fm.get("image", False)),
        "continued_on_page":   None,
        "continued_from_page": None,
        # sidebar
        "kind":         fm.get("kind", ""),
        "sidebar_items": fm.get("items", []),
        # reference
        "entries": fm.get("entries", []),
    }

    if weight in ("lead", "standard", "editorial"):
        story["body"] = _split_body(body)
    elif weight == "brief":
        # brief is always one paragraph — prefer Markdown body, fallback to frontmatter
        story["body"] = body.strip() or str(fm.get("body", ""))
    else:
        story["body"] = []

    return story

# ---------------------------------------------------------------------------
# Issue assembly
# ---------------------------------------------------------------------------

def _assemble_issue(issue_dir: Path, np_config: dict) -> dict | None:
    stories: list[dict] = []
    manifest_fm: dict = {}

    for md in sorted(issue_dir.glob("*.md")):
        raw = md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(raw)
        doc_type = fm.get("type", "")

        if doc_type == "newspaper-manifest":
            manifest_fm = fm
        elif doc_type == "newspaper-story":
            stories.append(_build_story(fm, body))

    if not stories:
        return None

    # Masthead: config defaults → manifest overrides
    m = manifest_fm.get("masthead", {})
    masthead = {
        "title":    m.get("title",   np_config.get("name", "THE HERALD")),
        "tagline":  m.get("tagline", np_config.get("tagline", "")),
        "edition":  m.get("edition", np_config.get("edition", "")),
        "date":     m.get("date",    ""),
        "issue_no": m.get("issueNo", ""),
    }

    # Sort by (page, order)
    stories.sort(key=lambda s: (s["page"], s["order"]))

    # Auto-paginate lead stories that exceed word budget.
    # Continuation fragment gets placed on the NEXT page after its source.
    # (Inserted right after the source story so that further sorting keeps it adjacent.)
    paginated: list[dict] = []
    for story in stories:
        if story["weight"] == "lead" and not story.get("continued_from_page"):
            first, rest = _paginate_lead(story["body"])
            if rest:
                cont_page = story["page"] + 1
                story = copy.copy(story)
                story["body"] = first
                story["continued_on_page"] = cont_page

                cont = copy.copy(story)
                cont["body"] = rest
                cont["page"] = cont_page
                cont["order"] = 0          # continuations sort first on their page
                cont["continued_from_page"] = story["page"]
                cont["continued_on_page"] = None

                paginated.append(story)
                paginated.append(cont)
                continue
        paginated.append(story)

    # Group into ordered pages
    pages_dict: dict[int, list] = {}
    for s in paginated:
        pages_dict.setdefault(s["page"], []).append(s)

    pages = [
        {"stories": pages_dict[n]}
        for n in sorted(pages_dict)
    ]

    return {"masthead": masthead, "pages": pages}

# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class _Generator:
    name        = "newspaper"
    description = "Assemble per-story .md files into newspaper issue HTML"

    def run(self, argv=None):
        np_config = _load_np_config()
        NEWS_SRC.mkdir(parents=True, exist_ok=True)
        NEWS_OUT.mkdir(parents=True, exist_ok=True)

        issue_dirs = sorted(
            d for d in NEWS_SRC.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

        listing: list[dict] = []

        for issue_dir in issue_dirs:
            issue = _assemble_issue(issue_dir, np_config)
            if not issue:
                print(f"  [newspaper] skip {issue_dir.name} — no stories found")
                continue

            slug    = issue_dir.name
            out_dir = NEWS_OUT / slug
            out_dir.mkdir(parents=True, exist_ok=True)

            html = render_page(
                "pages/newspaper.html",
                title=issue["masthead"]["title"],
                issue=issue,
                use_base_css=True,
                page_class=" newspaper-page",
                extra_css=["newspaper-tokens", "page-newspaper"],
                generator_name="utilities/newspaper/generate_newspaper_html.py",
            )
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            print(f"  [newspaper] wrote {out_dir / 'index.html'}")

            # Extract lead headline for listing card
            lead_headline = ""
            for pg in issue["pages"]:
                for s in pg["stories"]:
                    if s["weight"] == "lead" and not s.get("continued_from_page"):
                        lead_headline = s.get("headline", "")
                        break
                if lead_headline:
                    break

            listing.append({
                "slug":         slug,
                "issue_no":     issue["masthead"]["issue_no"],
                "lead_headline": lead_headline,
                "date":         issue["masthead"]["date"],
            })

        # Listing page (newest first)
        newspaper_name = np_config.get("name", "The Herald")
        listing_html = render_page(
            "pages/newspaper-index.html",
            title=newspaper_name,
            newspaper_name=newspaper_name,
            issues=list(reversed(listing)),
            use_base_css=True,
            page_class=" newspaper-page",
            extra_css=["newspaper-tokens", "page-newspaper"],
            generator_name="utilities/newspaper/generate_newspaper_html.py",
        )
        (NEWS_OUT / "index.html").write_text(listing_html, encoding="utf-8")
        print(f"  [newspaper] wrote {NEWS_OUT / 'index.html'} ({len(listing)} issues)")

        return 0


generator = _Generator()

if __name__ == "__main__":
    sys.exit(generator.run())
