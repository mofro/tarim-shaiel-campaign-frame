#!/usr/bin/env python3
"""
Tarim-Shaiel Lore HTML Generator
==================================
Generic generator: reads any lore .md file → docs/<folder>/<slug>.html

Outputs a player-facing HTML artifact in the same visual style as the
campaign-frame document (cover section, parchment design system, same fonts).

Usage:
    python generate_lore_html.py --source "narrative/lore/The Roads.md"
    python generate_lore_html.py --source path/to/lore.md --out docs/custom-name.html
"""

import re
import sys
import argparse
from pathlib import Path
from html import escape

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
DOCS_DIR    = VAULT_ROOT / "docs"

# Make utilities/shared importable regardless of working directory
sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.frontmatter import parse_frontmatter
from shared.assets import prepare_image, prepare_audio, prepare_audio_wiki
from shared.html_render import render_prose, AUDIO_EXTS
from shared.page_shell import build_page

COVER_IMAGE_URL = "https://images5.alphacoders.com/798/thumb-1920-798802.jpg"

# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def slugify(title: str) -> str:
    """Convert a title to a URL-safe slug."""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


# ---------------------------------------------------------------------------
# CSS is now linked externally via page_shell.build_page(extra_css=('page-lore',))
# Source: utilities/shared/css/page-lore.css
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Full page assembly
# ---------------------------------------------------------------------------

def build_html(title: str, description: str, body: str, date_str: str,
               audio_url: str, audio_title: str | None = None) -> str:
    prose_html = render_prose(body)
    title_esc = escape(title)
    desc_esc = escape(description) if description else ''

    content_html = ''
    if audio_url:
        audio_title_esc = escape(audio_title) if audio_title else ''
        audio_url_esc = escape(audio_url)
        content_html += (
            f'\n    <div class="audio-player">\n'
            f'      <div class="audio-player-label">{audio_title_esc}</div>\n'
            f'      <audio controls preload="metadata">\n'
            f'        <source src="{audio_url_esc}" type="audio/mpeg" />\n'
            f'      </audio>\n'
            f'    </div>\n'
        )

    if desc_esc:
        content_html += f'\n    <div class="divider"></div>\n    <p><em>{desc_esc}</em></p>\n    <div class="divider"></div>\n'

    content_html += prose_html

    credits_html = (
        f'    Tarim-Shaiel &middot; World Lore &middot; '
        f'{title_esc} &middot; {escape(date_str)}\n'
    )

    return build_page(
        title=title,
        cover_subtitle='World Lore · Tarim-Shaiel',
        banner_left='World Lore',
        banner_right=f'{title} · Tarim-Shaiel',
        content_html=content_html,
        credits_html=credits_html,
        cover_image_url=COVER_IMAGE_URL,
        extra_css=('page-lore',),
        generator_name='utilities/lore/generate_lore_html.py',
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate a styled lore HTML page from a Markdown source file.'
    )
    parser.add_argument(
        '--source', required=True,
        help='Path to source .md file (relative to vault root or absolute)'
    )
    parser.add_argument(
        '--out', default=None,
        help='Output HTML path (default: docs/<source-folder>/<slug>.html derived from source path)'
    )
    args = parser.parse_args()

    src = Path(args.source)
    if not src.is_absolute():
        src = VAULT_ROOT / src

    if not src.exists():
        raise FileNotFoundError(f'Source file not found: {src}')

    raw = src.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(raw)

    title = fm.get('title') or src.stem
    description = fm.get('description', '')
    date_str = str(fm.get('last_updated') or fm.get('created') or 'March 2026')
    audio_field = fm.get('audio', '')
    audio_title = fm.get('audio_title', 'Opening Narration')

    audio_url = prepare_audio(audio_field, VAULT_ROOT, DOCS_DIR) if audio_field else None

    # Pre-copy assets referenced via Obsidian ![[...]] syntax
    for m in re.finditer(r'!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', body):
        fname = Path(m.group(1).strip()).name
        if Path(fname).suffix.lower() in AUDIO_EXTS:
            prepare_audio_wiki(fname, VAULT_ROOT, DOCS_DIR)
        else:
            prepare_image(fname, VAULT_ROOT, DOCS_DIR)

    if args.out:
        out = Path(args.out)
    else:
        slug = slugify(title)
        folder = src.parent.name
        out = DOCS_DIR / folder / f'{slug}.html'

    html = build_html(title, description, body, date_str, audio_url=audio_url, audio_title=audio_title)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')

    print(f'Lore page generated: {out}')
    print(f'  Source: {src}')
    print(f'  Title:  {title}')
    print(f'  Slug:   {slugify(title)}')


if __name__ == '__main__':
    main()


# ---------------------------------------------------------------------------
# Generator protocol wrapper (used by utilities/build.py)
# ---------------------------------------------------------------------------
class _Generator:
    name = "lore"
    description = "Generate styled lore HTML from a Markdown source file"

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
