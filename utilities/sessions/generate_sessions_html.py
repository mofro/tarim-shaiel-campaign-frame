#!/usr/bin/env python3
"""
Tarim-Shaiel Session Narrative HTML Generator
==============================================
Reads storyteller-produced narrative/sessions/<slug>/index.md files and
renders each as docs/sessions/<slug>/index.html using the HeroHeaven design
system.  Also generates a listing page at docs/sessions/index.html.

Only processes directories whose index.md has `type: narrative-session` in
its frontmatter — source/planning files (e.g. 00_session0/) are skipped.

Usage (standalone):
    python utilities/sessions/generate_sessions_html.py

Via build.py:
    python utilities/build.py sessions
    python utilities/build.py sessions --standalone
"""

import re
import sys
from pathlib import Path

SCRIPT_DIR   = Path(__file__).parent
VAULT_ROOT   = SCRIPT_DIR.parent.parent
DOCS_DIR     = VAULT_ROOT / "docs"
SESSIONS_SRC = VAULT_ROOT / "narrative" / "sessions"

sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.frontmatter import parse_frontmatter
from shared.html_render import render_body
from shared.renderer import render_page


def _display_title(fm: dict, slug: str) -> str:
    """Derive a display title from frontmatter session field or slug."""
    session = str(fm.get("session", ""))
    if session:
        # "2026-06-25 The Vault" → strip the leading date prefix
        parts = session.split(" ", 1)
        if len(parts) == 2 and re.match(r"\d{4}-\d{2}-\d{2}$", parts[0]):
            return parts[1]
        return session
    return slug.replace("-", " ").title()


def generate_session_page(src: Path, out_dir: Path) -> dict | None:
    """Render one session index.md → docs/sessions/<slug>/index.html.

    Returns a metadata dict for the listing page, or None if the file is not
    a narrative-session (wrong type in frontmatter or no frontmatter).
    """
    raw = src.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    if fm.get("type") != "narrative-session":
        return None

    slug     = src.parent.name
    title    = _display_title(fm, slug)
    date_str = str(fm.get("date", ""))
    campaign = str(fm.get("campaign", "Tarim-Shaiel"))

    body_html, _ = render_body(body, VAULT_ROOT, DOCS_DIR, gm_mode=False)

    out = out_dir / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    html = render_page(
        "pages/session.html",
        title=title,
        date_str=date_str,
        campaign=campaign,
        eyebrow="Session Chronicle",
        back_href="/sessions/index.html",
        back_label="All Sessions",
        extra_css=["page-session"],
        generator_name="utilities/sessions/generate_sessions_html.py",
        body_html=body_html,
    )

    out.write_text(html, encoding="utf-8")
    print(f"  {out.relative_to(VAULT_ROOT)}")
    return {"slug": slug, "title": title, "date": date_str, "campaign": campaign}


def generate_index_page(sessions: list[dict], out_dir: Path) -> None:
    """Render the sessions listing page at docs/sessions/index.html."""
    sessions_sorted = sorted(sessions, key=lambda s: s["date"], reverse=True)

    html = render_page(
        "pages/sessions-index.html",
        title="Session Chronicles",
        eyebrow="Tarim-Shaiel",
        extra_css=["page-session"],
        generator_name="utilities/sessions/generate_sessions_html.py",
        sessions=sessions_sorted,
    )

    out = out_dir / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  {out.relative_to(VAULT_ROOT)}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate session narrative HTML pages from storyteller output."
    )
    parser.add_argument(
        "--out", default=None,
        help="Output directory override (default: docs/sessions/)"
    )
    args = parser.parse_args()

    out_dir = Path(args.out) if args.out else DOCS_DIR / "sessions"

    if not SESSIONS_SRC.exists():
        print(f"No sessions source directory at {SESSIONS_SRC}", file=sys.stderr)
        return

    sessions: list[dict] = []
    for index_md in sorted(SESSIONS_SRC.glob("*/index.md")):
        result = generate_session_page(index_md, out_dir)
        if result:
            sessions.append(result)

    if not sessions:
        print("sessions: no narrative-session index.md files found — nothing generated.")
        return

    generate_index_page(sessions, out_dir)
    print(f"\nsessions: {len(sessions)} session(s) built.")


if __name__ == "__main__":
    main()


from shared.base_generator import make_generator
generator = make_generator(
    "sessions",
    "Render storyteller session narrative pages and listing index",
    main,
)
