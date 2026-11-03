#!/usr/bin/env python3
"""
Tarim-Shaiel Session Notes HTML Generator
==========================================
Renders each narrative/sessions/<folder>/Session_<N>_Player_Summary.md as
docs/sessions/session-<N>.html using the HeroHeaven design system, and
generates a listing page at docs/sessions/index.html.

Selection is fail-closed.  A file is published only when ALL of these hold:
  - its name is Session_<N>_Player_Summary.md
  - frontmatter has `visibility: public`
  - frontmatter has `status: canon`
Anything else under narrative/sessions/ (GM material, drafts, scenario files)
is skipped.

The page title comes from the filename ("Session 1 — Player Summary"), not
from the `title:` frontmatter.

Usage (standalone):
    python utilities/sessions/generate_sessions_html.py

Via build.py:
    python utilities/build.py sessions
    python utilities/build.py sessions --standalone

PDFs are not produced here (Netlify and CI carry no PDF toolchain).  Build the
`--standalone` HTML and print it with headless Chrome:
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \\
        --disable-gpu --no-sandbox --no-pdf-header-footer \\
        --print-to-pdf=<out.pdf> file://<standalone.html>
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
from shared.html_render import render_body, AUDIO_EXTS
from shared.renderer import render_page

PLAYER_SUMMARY = re.compile(r"^Session_(\d+)_Player_Summary\.md$")

# Heading and rule lines the renderer reads per blank-line-separated block: a
# heading or `---` sitting directly against other lines is swallowed into that
# block, so each is isolated first.
_HEADING_LINE = re.compile(r"^(#{1,6}\s.*)$", re.MULTILINE)
_RULE_LINE    = re.compile(r"^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$", re.MULTILINE)
_NUMERIC_REF  = re.compile(r"&#(?:[xX]([0-9a-fA-F]{1,6})|([0-9]{1,7}));")
_AUDIO_EMBED  = re.compile(
    r"^!\[\[([^\]|]+?)(?:\|([^\]]*))?\]\][ \t]*$", re.MULTILINE
)


def _rel(p: Path) -> Path:
    """Path relative to the vault when inside it (--out may point elsewhere)."""
    try:
        return p.relative_to(VAULT_ROOT)
    except ValueError:
        return p


def player_summary_number(src: Path) -> int | None:
    """Session number from a Session_<N>_Player_Summary.md filename, else None."""
    m = PLAYER_SUMMARY.match(src.name)
    return int(m.group(1)) if m else None


def load_player_summary(src: Path) -> dict | None:
    """Parse one candidate file; return None unless it may be published.

    Returns {"number", "fm", "body"} for a public, canon Player Summary.
    """
    number = player_summary_number(src)
    if number is None:
        return None
    fm, body = parse_frontmatter(src.read_text(encoding="utf-8"))
    if str(fm.get("visibility", "")).strip().lower() != "public":
        return None
    if str(fm.get("status", "")).strip().lower() != "canon":
        return None
    return {"number": number, "fm": fm, "body": body}


def session_title(number: int) -> str:
    return f"Session {number} \u2014 Player Summary"


def _split_lead_title(body: str, number: int) -> tuple[str, str]:
    """Remove the leading "Session N" heading the page title already says.

    Returns (subtitle, body).  "###### Session 0: Prologue" yields "Prologue";
    a bare "# Session 1" yields "".  Only a heading at the very top of the body
    is touched.
    """
    m = re.match(
        rf"\s*#{{1,6}}[ \t]+\**[ \t]*Session[ \t]+{number}\b[ \t:\u2014\u2013-]*([^\n]*?)\**[ \t]*(?:\n|$)",
        body,
    )
    if not m:
        return "", body
    return m.group(1).strip(" *"), body[m.end():]


def _decode_numeric_refs(body: str) -> str:
    """Decode &#x68; / &#104; character references.

    Markdown allows them and the renderer escapes the '&', so left alone they
    print literally.  The Session 1 export carries them as 'Volkat&#x68;**'s**'.
    Text is HTML-escaped again by the renderer, so a decoded '<' stays inert.
    """
    def _char(m: re.Match) -> str:
        code = int(m.group(1), 16) if m.group(1) else int(m.group(2))
        return chr(code) if 0 < code <= 0x10FFFF else m.group(0)
    return _NUMERIC_REF.sub(_char, body)


def _audio_cue(m: re.Match) -> str:
    """Turn a standalone audio embed into a plain-text cue, else leave it."""
    target = m.group(1).strip()
    if Path(target).suffix.lower() not in AUDIO_EXTS:
        return m.group(0)
    label = (m.group(2) or "").split("|")[0].strip() or Path(target).stem.replace("_", " ")
    return f"*\u266a {label}*"


def prepare_body(body: str, number: int) -> tuple[str, str]:
    """Normalise a Player Summary body for render_body.

    Returns (subtitle, body).  Audio files are not published, so an embedded
    track becomes a text cue instead of a player that points at a missing file.
    """
    body = _decode_numeric_refs(body)
    body = _HEADING_LINE.sub(r"\n\1\n", body)
    body = _RULE_LINE.sub("\n---\n", body)
    subtitle, body = _split_lead_title(body, number)
    body = _AUDIO_EMBED.sub(_audio_cue, body)
    return subtitle, body


def generate_session_page(src: Path, out_dir: Path) -> dict | None:
    """Render one Player Summary → docs/sessions/session-<N>.html.

    Returns a metadata dict for the listing page, or None if the file may not
    be published (wrong name, not public, not canon).
    """
    loaded = load_player_summary(src)
    if loaded is None:
        return None

    number   = loaded["number"]
    slug     = f"session-{number}"
    title    = session_title(number)
    campaign = str(loaded["fm"].get("campaign", "Tarim-Shaiel"))

    subtitle, body = prepare_body(loaded["body"], number)
    body_html, _ = render_body(body, VAULT_ROOT, DOCS_DIR, gm_mode=False,
                              keep_h1=True, ordered_lists=True)

    out = out_dir / f"{slug}.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    html = render_page(
        "pages/session.html",
        title=title,
        subtitle=subtitle,
        campaign=campaign,
        eyebrow="Session Chronicle",
        back_href="/sessions/index.html",
        back_label="All Sessions",
        extra_css=["page-session"],
        generator_name="utilities/sessions/generate_sessions_html.py",
        body_html=body_html,
    )

    out.write_text(html, encoding="utf-8")
    print(f"  {_rel(out)}")
    return {
        "number": number, "slug": slug, "title": title,
        "subtitle": subtitle, "campaign": campaign,
    }


def generate_index_page(sessions: list[dict], out_dir: Path) -> None:
    """Render the sessions listing page at docs/sessions/index.html."""
    sessions_sorted = sorted(sessions, key=lambda s: s["number"], reverse=True)

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
    print(f"  {_rel(out)}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate session notes HTML pages from Player Summary files."
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
    for src in sorted(SESSIONS_SRC.glob("*/Session_*_Player_Summary.md")):
        result = generate_session_page(src, out_dir)
        if result:
            sessions.append(result)
        else:
            print(f"  skipped {_rel(src)} (not public + canon, or not a Player Summary)")

    if not sessions:
        print("sessions: no public, canon Session_N_Player_Summary.md files found — nothing generated.")
        return

    generate_index_page(sessions, out_dir)
    print(f"\nsessions: {len(sessions)} session(s) built.")


if __name__ == "__main__":
    main()


from shared.base_generator import make_generator
generator = make_generator(
    "sessions",
    "Render public Session_N_Player_Summary pages and listing index",
    main,
)
