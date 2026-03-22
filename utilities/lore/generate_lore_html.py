#!/usr/bin/env python3
"""
Tarim-Shaiel Lore HTML Generator
==================================
Generic generator: reads any lore .md file → docs/<slug>.html

Outputs a player-facing HTML artifact in the same visual style as the
campaign-frame document (cover section, parchment design system, same fonts).

Usage:
    python generate_lore_html.py --source "narrative/lore/The Roads.md"
    python generate_lore_html.py --source path/to/lore.md --out docs/custom-name.html
"""

import re
import shutil
import argparse
from pathlib import Path
from html import escape

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
DOCS_DIR    = VAULT_ROOT / "docs"

COVER_IMAGE_URL = "https://images5.alphacoders.com/798/thumb-1920-798802.jpg"

AUDIO_EXTS = {'.mp3', '.ogg', '.wav', '.m4a', '.flac', '.aac'}
AUDIO_MIME  = {'.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav',
               '.m4a': 'audio/mp4',  '.flac': 'audio/flac', '.aac': 'audio/aac'}

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter as a dict and return the remaining body."""
    m = re.match(r'^---\n(.*?)\n---\n', text, re.DOTALL)
    if not m:
        return {}, text
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip()
    return fm, text[m.end():]


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
# Inline markdown conversion (shared with campaign frame generator)
# ---------------------------------------------------------------------------

def inline_md(text: str) -> str:
    """Convert inline markdown to HTML (after HTML-escaping the raw text)."""
    text = escape(text)
    text = re.sub(r'\*{3}(.+?)\*{3}', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text


# ---------------------------------------------------------------------------
# Content rendering
# ---------------------------------------------------------------------------

def render_prose(body: str) -> str:
    """Render the body as a sequence of <p> paragraphs and inline figures.

    Strips heading lines (### etc.) and renders each paragraph block.
    Handles the leading zero-width space that Obsidian sometimes inserts.
    Image lines (![caption](url)) on their own paragraph become <figure> blocks.
    """
    # Remove heading lines (###, ##, #)
    lines = [l for l in body.splitlines() if not re.match(r'^#{1,6}\s', l.strip())]
    body = '\n'.join(lines)

    # Remove zero-width spaces (Obsidian artefact)
    body = body.replace('\u200b', '')

    paras: list[str] = []
    current: list[str] = []

    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            paras.append(' '.join(current))
            current = []

    if current:
        paras.append(' '.join(current))

    html = ''
    for p in paras:
        if not p:
            continue
        # Detect Obsidian wiki-embed: ![[filename]] — image or audio
        obs_m = re.match(r'^!\[\[([^\]]+)\]\]$', p)
        if obs_m:
            fname = obs_m.group(1)
            ext = Path(fname).suffix.lower()
            if ext in AUDIO_EXTS:
                src   = escape(f'audio/{fname}')
                label = escape(Path(fname).stem.replace('-', ' ').replace('_', ' ').title())
                mime  = AUDIO_MIME.get(ext, 'audio/mpeg')
                html += (
                    f'    <div class="audio-player">\n'
                    f'      <div class="audio-player-label">{label}</div>\n'
                    f'      <audio controls preload="metadata">\n'
                    f'        <source src="{src}" type="{mime}" />\n'
                    f'      </audio>\n'
                    f'    </div>\n'
                )
            else:
                src = escape(f'images/{fname}')
                alt = escape(fname.rsplit('.', 1)[0])
                html += (
                    f'    <figure class="lore-figure">\n'
                    f'      <img src="{src}" alt="{alt}" />\n'
                    f'      <figcaption>{alt}</figcaption>\n'
                    f'    </figure>\n'
                )
        # Detect standalone image: ![caption](url)
        elif re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', p):
            img_m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', p)
            alt = escape(img_m.group(1))
            src = escape(img_m.group(2))
            html += (
                f'    <figure class="lore-figure">\n'
                f'      <img src="{src}" alt="{alt}" />\n'
                f'      <figcaption>{alt}</figcaption>\n'
                f'    </figure>\n'
            )
        else:
            html += f'    <p>{inline_md(p)}</p>\n'
    return html


# ---------------------------------------------------------------------------
# Audio helper
# ---------------------------------------------------------------------------

def prepare_audio(audio_field: str) -> str | None:
    """Resolve the audio frontmatter field to a docs-relative URL.

    Copies the source file into docs/audio/ if it exists.
    Returns the relative URL (e.g. 'audio/filename.mp3') or None.
    """
    if not audio_field:
        return None

    src = Path(audio_field)
    if not src.is_absolute():
        src = VAULT_ROOT / src

    if not src.exists():
        print(f'  [audio] Source not found, skipping player: {src}')
        return None

    dest_dir = DOCS_DIR / 'audio'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    print(f'  [audio] Copied to {dest}')
    return f'audio/{src.name}'


# ---------------------------------------------------------------------------
# Image helper
# ---------------------------------------------------------------------------

def find_image_in_vault(fname: str) -> Path | None:
    """Search vault recursively for an image file by name (Obsidian-style resolution)."""
    for candidate in VAULT_ROOT.rglob(fname):
        if candidate.is_file():
            return candidate
    return None


def prepare_image(fname: str) -> str | None:
    """Find an image by filename in the vault, copy to docs/images/, return relative URL."""
    src = find_image_in_vault(fname)
    if src is None:
        print(f'  [image] WARNING: {fname!r} not found in vault')
        return None

    dest_dir = DOCS_DIR / 'images'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname
    shutil.copy2(src, dest)
    print(f'  [image] Copied {src} → {dest}')
    return f'images/{fname}'


def prepare_audio_wiki(fname: str) -> str | None:
    """Find an audio file by filename in vault, copy to docs/audio/, return relative URL."""
    src = find_image_in_vault(fname)
    if src is None:
        print(f'  [audio] WARNING: {fname!r} not found in vault')
        return None

    dest_dir = DOCS_DIR / 'audio'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname
    shutil.copy2(src, dest)
    print(f'  [audio] Copied {src} → {dest}')
    return f'audio/{fname}'


# ---------------------------------------------------------------------------
# CSS (identical design system to campaign-frame)
# ---------------------------------------------------------------------------

CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --ink:        #1a1208;
      --parchment:  #f5edd8;
      --parchment2: #ede0c4;
      --gold:       #b8922c;
      --gold-light: #d4a843;
      --crimson:    #7a1f1f;
      --steel:      #3c4a5a;
      --rule:       rgba(184,146,44,0.4);
      --shadow:     rgba(26,18,8,0.15);
    }

    html { scroll-behavior: smooth; }

    body {
      background: #1a1208;
      font-family: 'EB Garamond', Georgia, serif;
      font-size: 18px;
      line-height: 1.85;
      color: var(--ink);
    }

    .page-wrap {
      max-width: 860px;
      margin: 0 auto;
      background: var(--parchment);
      box-shadow: 0 0 80px rgba(0,0,0,0.75);
      position: relative;
      overflow: hidden;
    }

    .page-wrap::before {
      content: '';
      position: absolute; inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 0;
      opacity: 0.45;
    }

    .cover {
      position: relative;
      min-height: 460px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      overflow: hidden;
    }

    .cover-image {
      position: absolute; inset: 0;
      background-image: url('%(cover_image_url)s');
      background-size: cover;
      background-position: center 4%;
      z-index: 0;
    }

    .cover-gradient {
      position: absolute; inset: 0;
      background: linear-gradient(to bottom, rgba(26,18,8,0.08) 0%, rgba(26,18,8,0.55) 55%, rgba(26,18,8,0.92) 100%);
      z-index: 1;
    }

    .cover-content {
      position: relative;
      z-index: 2;
      padding: 2.5rem 3rem 3rem;
      color: var(--parchment);
    }

    .cover-title {
      font-family: 'Cinzel', serif;
      font-size: 3.2rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      line-height: 1.1;
      color: #f5e6c0;
      text-shadow: 0 2px 12px rgba(0,0,0,0.7);
      margin-bottom: 0.15rem;
    }

    .cover-subtitle {
      font-family: 'Cinzel', serif;
      font-size: 1rem;
      font-weight: 400;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--gold-light);
    }

    .banner {
      background: var(--steel);
      color: var(--parchment);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 3rem;
      font-family: 'Cinzel', serif;
      font-size: 0.72rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }

    .banner-rule {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--gold), transparent);
      margin: 0 3rem;
    }

    .back-nav {
      background: #111008;
      padding: 0.5rem 3rem;
      border-bottom: 1px solid rgba(184,146,44,0.2);
    }

    .back-nav a {
      font-family: 'Cinzel', serif;
      font-size: 0.68rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: rgba(184,146,44,0.6);
      text-decoration: none;
      transition: color 0.2s;
    }

    .back-nav a:hover { color: var(--gold); }

    .content {
      position: relative;
      z-index: 1;
      padding: 3.2rem 3.8rem 3.6rem;
      max-width: 680px;
      margin: 0 auto;
    }

    p {
      margin-bottom: 1.3em;
      font-size: 1.08rem;
    }

    p:last-child { margin-bottom: 0; }

    .divider {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--gold), transparent);
      margin: 2.4rem 0;
    }

    /* ---- Inline image figure ---- */

    .lore-figure {
      float: right;
      margin: 0.4rem 0 1.6rem 2rem;
      max-width: 240px;
      clear: right;
    }

    .lore-figure img {
      width: 100%;
      display: block;
      border: 1px solid var(--rule);
      box-shadow: 4px 6px 18px var(--shadow);
    }

    .lore-figure figcaption {
      font-size: 0.8rem;
      font-style: italic;
      color: var(--steel);
      text-align: center;
      margin-top: 0.45rem;
      padding-top: 0.35rem;
      border-top: 1px solid var(--rule);
      line-height: 1.4;
    }

    @media (max-width: 640px) {
      .lore-figure {
        float: none;
        max-width: 100%;
        margin: 0 0 1.5rem 0;
      }
    }

    /* ---- Audio player ---- */

    .audio-player {
      margin: 2.4rem 0;
      padding: 1.1rem 1.4rem 1.2rem;
      background: var(--parchment2);
      border: 1px solid var(--rule);
      border-radius: 2px;
      box-shadow: inset 0 1px 4px rgba(26,18,8,0.06);
    }

    .audio-player-label {
      font-family: 'Cinzel', serif;
      font-size: 0.68rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--steel);
      margin-bottom: 0.65rem;
    }

    .audio-player audio {
      width: 100%;
      display: block;
    }

    .credits {
      background: var(--steel);
      color: rgba(245,237,216,0.55);
      padding: 2rem 3rem;
      font-size: 0.88rem;
      line-height: 1.6;
    }

    @media (max-width: 640px) {
      .cover-title { font-size: 2.2rem; }
      .cover-content, .content { padding: 1.8rem 1.4rem; }
      .banner { padding: 0.5rem 1.4rem; }
      .banner-rule { margin: 0 1.4rem; }
      .credits { padding: 1.6rem 1.4rem; }
    }
"""


# ---------------------------------------------------------------------------
# Full page assembly
# ---------------------------------------------------------------------------

def build_html(title: str, description: str, body: str, date_str: str,
               audio_url: str, audio_title: str | None = None) -> str:
    css = CSS.replace('%(cover_image_url)s', COVER_IMAGE_URL)
    prose_html = render_prose(body)
    title_esc = escape(title)
    desc_esc = escape(description) if description else ''

    desc_block = ''
    if desc_esc:
        desc_block = f'\n    <div class="divider"></div>\n    <p><em>{desc_esc}</em></p>\n    <div class="divider"></div>\n'

    audio_block = ''
    if audio_url:
        audio_title_esc = escape(audio_title) if audio_title else ''
        audio_url_esc = escape(audio_url)
        audio_block = (
            f'\n    <div class="audio-player">\n'
            f'      <div class="audio-player-label">{audio_title_esc}</div>\n'
            f'      <audio controls preload="metadata">\n'
            f'        <source src="{audio_url_esc}" type="audio/mpeg" />\n'
            f'      </audio>\n'
            f'    </div>\n'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title_esc} &mdash; Tarim-Shaiel</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='10' fill='%231a1208'/><polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 33.4,43.1 18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>">
  <!-- AUTO-GENERATED by utilities/lore/generate_lore_html.py — do not hand-edit -->
  <style>{css}  </style>
</head>
<body>

<div class="page-wrap">

  <!-- BACK NAV -->
  <div class="back-nav">
    <a href="index.html">&#8592; Campaign Documents</a>
  </div>

  <!-- COVER -->
  <div class="cover">
    <div class="cover-image"></div>
    <div class="cover-gradient"></div>
    <div class="cover-content">
      <div class="cover-title">{title_esc}</div>
      <div class="cover-subtitle">World Lore &middot; Tarim-Shaiel</div>
    </div>
  </div>

  <div class="banner">
    <span>World Lore</span>
    <span>{title_esc} &middot; Tarim-Shaiel</span>
  </div>
  <div class="banner-rule"></div>

  <!-- MAIN CONTENT -->
  <div class="content">
{desc_block}{audio_block}
{prose_html}
  </div><!-- /content -->

  <!-- FOOTER -->
  <div class="credits">
    Tarim-Shaiel &middot; World Lore &middot; {title_esc} &middot; {escape(date_str)}
  </div>

</div><!-- /page-wrap -->

</body>
</html>
"""


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
        help='Output HTML path (default: docs/<slug>.html derived from title)'
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
    date_str = fm.get('last_updated') or fm.get('created') or 'March 2026'
    audio_field = fm.get('audio', '')

    audio_url = prepare_audio(audio_field) if audio_field else None

    # Pre-copy assets referenced via Obsidian ![[filename]] syntax
    for ref in re.findall(r'!\[\[([^\]]+)\]\]', body):
        if Path(ref).suffix.lower() in AUDIO_EXTS:
            prepare_audio_wiki(ref)
        else:
            prepare_image(ref)

    if args.out:
        out = Path(args.out)
    else:
        slug = slugify(title)
        out = DOCS_DIR / f'{slug}.html'

    html = build_html(title, description, body, date_str, audio_url=audio_url)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')

    print(f'Lore page generated: {out}')
    print(f'  Source: {src}')
    print(f'  Title:  {title}')
    print(f'  Slug:   {slugify(title)}')


if __name__ == '__main__':
    main()
