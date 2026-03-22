"""
HTML rendering utilities for Obsidian prose bodies.

Converts sanitized Obsidian markdown body text into HTML fragments.
Handles wiki-embeds (![[...]]), standalone images (![]()), and paragraphs.

Depends on: shared.md_utils.inline_md
"""

import re
from pathlib import Path
from html import escape

from shared.md_utils import inline_md

AUDIO_EXTS = {'.mp3', '.ogg', '.wav', '.m4a', '.flac', '.aac'}
AUDIO_MIME  = {'.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav',
               '.m4a': 'audio/mp4',  '.flac': 'audio/flac', '.aac': 'audio/aac'}


def render_wiki_embed(p: str) -> str:
    """Render a single Obsidian wiki-embed paragraph (![[...]]) to HTML.

    Returns an audio player div for audio files, or a figure block for images.
    Returns an empty string if `p` is not a wiki-embed pattern.
    """
    obs_m = re.match(r'^!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]$', p)
    if not obs_m:
        return ''

    path_part  = obs_m.group(1).strip()
    alias_part = (obs_m.group(2) or '').strip()
    fname = Path(path_part).name
    ext   = Path(fname).suffix.lower()

    if ext in AUDIO_EXTS:
        src   = escape(f'audio/{fname}')
        label = escape(alias_part if alias_part else
                       Path(fname).stem.replace('-', ' ').replace('_', ' ').title())
        mime  = AUDIO_MIME.get(ext, 'audio/mpeg')
        return (
            f'    <div class="audio-player">\n'
            f'      <div class="audio-player-label">{label}</div>\n'
            f'      <audio controls preload="metadata">\n'
            f'        <source src="{src}" type="{mime}" />\n'
            f'      </audio>\n'
            f'    </div>\n'
        )
    else:
        src = escape(f'images/{fname}')
        alt = escape(alias_part if alias_part else fname.rsplit('.', 1)[0])
        return (
            f'    <figure class="lore-figure">\n'
            f'      <img src="{src}" alt="{alt}" />\n'
            f'      <figcaption>{alt}</figcaption>\n'
            f'    </figure>\n'
        )


def render_prose(body: str) -> str:
    """Render the body as a sequence of HTML blocks.

    Strips heading lines, splits on blank lines into paragraphs, then for each:
      - ![[...]]   → audio player or figure (via render_wiki_embed)
      - ![alt](url) → figure block
      - anything else → <p> with inline markdown converted

    Also strips Obsidian zero-width spaces.
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

        # Obsidian wiki-embed
        wiki_html = render_wiki_embed(p)
        if wiki_html:
            html += wiki_html
            continue

        # Standalone markdown image: ![caption](url)
        img_m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', p)
        if img_m:
            alt = escape(img_m.group(1))
            src = escape(img_m.group(2))
            html += (
                f'    <figure class="lore-figure">\n'
                f'      <img src="{src}" alt="{alt}" />\n'
                f'      <figcaption>{alt}</figcaption>\n'
                f'    </figure>\n'
            )
            continue

        html += f'    <p>{inline_md(p)}</p>\n'

    return html
