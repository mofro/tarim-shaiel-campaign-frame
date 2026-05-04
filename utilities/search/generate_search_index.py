#!/usr/bin/env python3
"""
Tarim-Shaiel Search Index Generator
=====================================
Crawls all source .md files and writes docs/search-index.json for use
by the client-side Lunr.js search page.

Usage:
    python utilities/search/generate_search_index.py
    python utilities/search/generate_search_index.py --public
    python utilities/search/generate_search_index.py --gm
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
DOCS_DIR = VAULT_ROOT / "docs"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.frontmatter import parse_frontmatter

# Directories under vault root to crawl
SEARCH_ROOTS = ["world", "narrative", "characters", "mechanics"]

# Path segments that disqualify a file from indexing
SKIP_SEGMENTS = {"lat.md", ".meta", "transcripts", "archive", "gm_secrets"}

# Filename patterns that disqualify a file
SKIP_FILENAME_PREFIXES = ("_TEMPLATE_",)

# content_type / type values that get entity card treatment
ENTITY_TYPES = {
    "location", "landmark", "poi", "region",
    "faction", "ancestry", "npc", "character",
}

BODY_MAX_CHARS = 500

# Scan roots that the world generator knows about (mirrors SCAN_ROOTS in generate_all_world_html.py)
_WORLD_SCAN_ROOTS = {"world", "narrative"}


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _slug(text: str) -> str:
    """Mirror generate_all_world_html._slug(): lowercase, non-word chars → hyphens."""
    return re.sub(r'[^\w\-]+', '-', text.lower()).strip('-')


def _output_subfolder(path: Path) -> str:
    """Mirror generate_all_world_html._output_subfolder().

    Returns the docs-relative subdirectory for a source file by stripping
    the scan root from the source parent path.
    """
    for root_name in _WORLD_SCAN_ROOTS:
        root = VAULT_ROOT / root_name
        try:
            parts = path.parent.relative_to(root).parts
            return '/'.join(parts) if parts else path.parent.name
        except ValueError:
            continue
    # For paths outside world/narrative (e.g. characters/), strip top-level folder
    rel_parts = path.relative_to(VAULT_ROOT).parts
    return '/'.join(rel_parts[1:-1]) if len(rel_parts) > 2 else path.parent.name

def _strip_obsidian(text: str) -> str:
    """Convert Obsidian-flavoured Markdown to plain indexable text."""
    # Remove wiki embeds: ![[...]]
    text = re.sub(r'!\[\[[^\]]*\]\]', ' ', text)
    # Wiki links with alias: [[target|alias]] → alias
    text = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', text)
    # Wiki links without alias: [[target]] → target
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # Markdown headings → keep text
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Bold / italic
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # Inline code
    text = re.sub(r'`[^`]*`', ' ', text)
    # Fenced code blocks
    text = re.sub(r'```[\s\S]*?```', ' ', text)
    # HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Horizontal rules / YAML-like lines
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


_SUBFOLDER_OVERRIDES: dict[str, str] = {
    # world/regions/ → locations generator outputs to docs/locations/regions/
    "regions": "locations/regions",
}


def _compute_url(path: Path) -> str:
    """Compute the site-relative URL for a source .md file.

    Mirrors each generator's output path logic:
      - subfolder via _output_subfolder() (strips scan root from parent)
      - filename via _slug(stem) (lowercase, non-word → hyphens)
      - _SUBFOLDER_OVERRIDES remaps subfolders whose output path differs from
        the simple strip-scan-root rule (e.g. world/regions/ → locations/regions/)

    Examples:
      world/locations/kucha.md          → /locations/kucha.html
      world/regions/tarim-basin.md      → /locations/regions/tarim-basin.html
      world/ancestries/PEOPLES_OF_...md → /ancestries/peoples-of-....html
      narrative/lore/The Roads.md       → /lore/the-roads.html
    """
    subfolder = _output_subfolder(path)
    subfolder = _SUBFOLDER_OVERRIDES.get(subfolder, subfolder)
    slug = _slug(path.stem)
    if subfolder:
        return f"/{subfolder}/{slug}.html"
    return f"/{slug}.html"


def _make_id(path: Path) -> str:
    """Stable string ID derived from vault-relative path without extension."""
    rel = path.relative_to(VAULT_ROOT)
    return re.sub(r'\.md$', '', str(rel).replace("\\", "/"), flags=re.IGNORECASE)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _should_skip_path(path: Path) -> bool:
    """Return True if this path should be excluded from the index."""
    parts_set = set(path.parts)
    if parts_set & SKIP_SEGMENTS:
        return True
    if any(s in str(path) for s in SKIP_SEGMENTS):
        return True
    if any(path.name.startswith(p) for p in SKIP_FILENAME_PREFIXES):
        return True
    return False


def _discover_files(public_only: bool) -> list[Path]:
    """Return all indexable .md files respecting visibility rules."""
    found = []
    for root_name in SEARCH_ROOTS:
        root = VAULT_ROOT / root_name
        if not root.exists():
            continue
        for md in root.rglob("*.md"):
            if _should_skip_path(md):
                continue
            found.append(md)
    return found


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------

def _build_record(path: Path, public_only: bool) -> dict | None:
    """Parse a .md file and return an index record, or None to skip."""
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception:
        return None

    fm, body = parse_frontmatter(raw)

    # Status gate
    if str(fm.get("status", "")).lower() == "deprecated":
        return None

    # Visibility gate
    visibility = str(fm.get("visibility", "gm_secrets")).lower()
    if public_only and visibility != "public":
        return None

    title = fm.get("title") or path.stem
    if not title:
        return None

    content_type = str(fm.get("content_type") or fm.get("type") or "").lower()
    entity = content_type in ENTITY_TYPES

    # Summary / description (prefer explicit field, fall back to body snippet)
    summary = str(fm.get("summary") or fm.get("description") or "").strip()

    # Tags: normalise to list of strings
    raw_tags = fm.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    tags = [str(t) for t in raw_tags]

    region = str(fm.get("region") or "").strip()

    body_text = _strip_obsidian(body)
    body_snippet = body_text[:BODY_MAX_CHARS]

    return {
        "id": _make_id(path),
        "title": title,
        "url": _compute_url(path),
        "content_type": content_type,
        "entity": entity,
        "region": region,
        "summary": summary,
        "tags": tags,
        "body": body_snippet,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate search-index.json for the Tarim-Shaiel site."
    )
    parser.add_argument(
        "--public", action="store_true",
        help="Only index visibility:public documents (Netlify public build)"
    )
    parser.add_argument(
        "--gm", action="store_true",
        help="Index all documents including gm_secrets (default behaviour)"
    )
    args = parser.parse_args()

    # Honour TS_GM_MODE env var used by other generators
    public_only = args.public
    if not public_only and not args.gm:
        # Default: follow TS_GM_MODE; if not set → index everything (GM mode)
        public_only = False

    files = _discover_files(public_only)
    records = []
    skipped = 0

    for f in sorted(files):
        rec = _build_record(f, public_only)
        if rec is None:
            skipped += 1
            continue
        records.append(rec)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out = DOCS_DIR / "search-index.json"
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    mode = "public" if public_only else "gm"
    print(f"Search index written: {out}")
    print(f"  Mode:    {mode}")
    print(f"  Indexed: {len(records)} documents")
    print(f"  Skipped: {skipped} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Generator protocol (used by utilities/build.py)
# ---------------------------------------------------------------------------

class _Generator:
    name = "search-index"
    description = "Generate search-index.json from all source .md files"

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
