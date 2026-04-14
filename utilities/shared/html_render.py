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
    # Obsidian allows multiple pipes: ![[file|alias|width]] — take first segment only
    alias_part = (obs_m.group(2) or '').split('|')[0].strip()
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
        stripped = line.strip().replace('\u200b', '').replace('\u00a0', ' ').strip()
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

def render_md_table(para: str) -> str:
    """Render a markdown table paragraph block as an HTML <table>.

    Expects a multi-line block where the first line is the header row,
    the second line is the separator (|---|---| pattern), and subsequent
    lines are data rows.  Returns an empty string if the block is not a
    recognisable table.
    """
    lines = [l.strip() for l in para.splitlines() if l.strip()]
    # Need at least header + separator
    if len(lines) < 2:
        return ''
    if not (lines[0].startswith('|') and lines[1].startswith('|')):
        return ''
    # Second line must be a separator: |---|  |:---:| etc.
    if not re.match(r'^\|[\s\-:|]+\|', lines[1]):
        return ''

    def _parse_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip('|').split('|')]

    header_cells = _parse_cells(lines[0])
    # lines[1] is the separator — skip it
    data_lines = lines[2:]

    thead = (
        '<thead><tr>'
        + ''.join(f'<th>{inline_md(c)}</th>' for c in header_cells)
        + '</tr></thead>'
    )
    tbody_rows = [
        '<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in _parse_cells(l)) + '</tr>'
        for l in data_lines
        if l.startswith('|')
    ]
    tbody = '<tbody>' + ''.join(tbody_rows) + '</tbody>'

    return f'<div class="table-wrap"><table class="md-table">{thead}{tbody}</table></div>\n'


def _slug_anchor(text: str) -> str:
    """Convert a header string to a URL-safe anchor id."""
    return re.sub(r'[^\w\-]+', '-', text.lower()).strip('-')


def render_body(body: str, vault: 'Path', docs: 'Path') -> 'tuple[str, list[dict]]':
    """Render a full Markdown body to HTML with component support.

    Handles (in priority order):
      ![[file|caption]]  → lore-figure or audio-player (via render_wiki_embed)
      ![alt](path)       → lore-figure
      **Name:** text     → feature-box (accumulated into feature-grid)
      ## heading         → <h2 id=...>  (jump nav level 2)
      ### heading        → <h3 id=...>  (jump nav level 3)
      > text             → callout div
      - item / * item    → <ul>
      anything else      → <p>

    Strips: frontmatter, Obsidian %% comments, wikilinks (preserving ![[]] embeds),
    Obsidian callout markers.

    Returns: (html_string, jump_nav_items)
      jump_nav_items = [{'text': str, 'anchor': str, 'level': int}, ...]
    """
    if not body or not body.strip():
        return '', []

    # --- Preprocessing ---
    body = re.sub(r'^---\n.*?\n---\n', '', body, flags=re.DOTALL)   # frontmatter
    body = re.sub(r'%%.*?%%', '', body, flags=re.DOTALL)             # GM comments
    body = re.sub(r'(?<!!)\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', body)  # wikilinks w/ alias
    body = re.sub(r'(?<!!)\[\[([^\]]+)\]\]', r'\1', body)             # bare wikilinks
    body = re.sub(r'^>\s*\[!\w+\]\s*$', '', body, flags=re.MULTILINE) # callout markers
    body = body.replace('\u200b', '')                                   # Obsidian zero-width spaces
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = body.strip()

    if not body:
        return '', []

    html_parts: list[str] = []
    jump_nav_items: list[dict] = []
    paragraphs = [p.strip() for p in re.split(r'\n\n+', body) if p.strip()]
    feature_buffer: list[tuple[str, str]] = []

    def _flush_features() -> None:
        nonlocal feature_buffer
        if not feature_buffer:
            return
        html_parts.append('<div class="feature-grid">\n')
        for name, flavor in feature_buffer:
            html_parts.append(
                f'  <div class="feature-box">\n'
                f'    <div class="feature-name">{escape(name)}</div>\n'
                f'    <p>{inline_md(flavor)}</p>\n'
                f'  </div>\n'
            )
        html_parts.append('</div>\n')
        feature_buffer = []

    for para in paragraphs:
        # Wiki-embed: ![[file|caption|width]] → figure or audio
        wiki_html = render_wiki_embed(para)
        if wiki_html:
            _flush_features()
            html_parts.append(wiki_html)
            continue

        # Markdown image: ![alt](path)
        md_img = re.match(r'^!\[([^\]]*)\]\(([^\)]+)\)$', para)
        if md_img:
            alt = escape(md_img.group(1))
            src = escape(md_img.group(2))
            _flush_features()
            html_parts.append(
                f'    <figure class="lore-figure">\n'
                f'      <img src="{src}" alt="{alt}" />\n'
                f'      <figcaption>{alt}</figcaption>\n'
                f'    </figure>\n'
            )
            continue

        # Feature box: **Feature Name:** description text
        feat = re.match(r'^\*\*(.+?):\*\*\s*(.+)', para, re.DOTALL)
        if feat:
            feature_buffer.append((feat.group(1).strip(), feat.group(2).strip()))
            continue

        # Flush features before non-feature content
        _flush_features()

        # H2 header
        if para.startswith('## '):
            text = para[3:].strip()
            anchor = _slug_anchor(text)
            jump_nav_items.append({'text': text, 'anchor': anchor, 'level': 2})
            html_parts.append(f'<h2 id="{anchor}">{inline_md(text)}</h2>\n')
            continue

        # H3 header
        if para.startswith('### '):
            text = para[4:].strip()
            anchor = _slug_anchor(text)
            html_parts.append(f'<h3 id="{anchor}">{inline_md(text)}</h3>\n')
            continue

        # Horizontal rule
        if para in ('---', '***', '___'):
            html_parts.append('<div class="divider"></div>\n')
            continue

        # Markdown table
        tbl = render_md_table(para)
        if tbl:
            html_parts.append(tbl)
            continue

        # Callout
        if para.startswith('> ') or para == '>':
            inner = re.sub(r'^>\s*', '', para, flags=re.MULTILINE).strip()
            html_parts.append(f'<div class="callout">{inline_md(inner)}</div>\n')
            continue

        # Unordered list
        if any(re.match(r'^[-*]\s+', line.strip()) for line in para.splitlines()):
            prefix_lines: list[str] = []
            list_items: list[str] = []
            for line in para.splitlines():
                ls = line.strip()
                if re.match(r'^[-*]\s+', ls):
                    item_text = re.sub(r'^[-*]\s+', '', ls)
                    list_items.append(f'  <li>{inline_md(item_text)}</li>\n')
                elif ls and not list_items:
                    prefix_lines.append(ls)
            if prefix_lines:
                html_parts.append(f'<p>{inline_md(" ".join(prefix_lines))}</p>\n')
            if list_items:
                html_parts.append('<ul>\n' + ''.join(list_items) + '</ul>\n')
            continue

        # Regular paragraph
        html_parts.append(f'<p>{inline_md(para)}</p>\n')

    _flush_features()
    return ''.join(html_parts), jump_nav_items