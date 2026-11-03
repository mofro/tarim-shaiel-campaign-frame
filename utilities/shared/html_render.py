"""
HTML rendering utilities for Obsidian prose bodies.

Converts sanitized Obsidian markdown body text into HTML fragments.
Handles wiki-embeds (![[...]]), standalone images (![]()), and paragraphs.

Depends on: shared.md_utils.inline_md
"""

import re
from pathlib import Path
from html import escape
from typing import Optional

from shared.md_utils import inline_md

AUDIO_EXTS = {'.mp3', '.ogg', '.wav', '.m4a', '.flac', '.aac'}
AUDIO_MIME  = {'.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav',
               '.m4a': 'audio/mp4',  '.flac': 'audio/flac', '.aac': 'audio/aac'}


def render_wiki_embed(
    p: str,
    vault: Optional[Path] = None,
    docs: Optional[Path] = None,
    gm_mode: bool = False,
) -> Optional[str]:
    """Render a single Obsidian wiki-embed paragraph (![[...]]) to HTML.

    Returns an audio player div for audio files, a figure for images, or a GM
    prose block for ![[gm_secrets/...]] embeds. Returns None if the paragraph
    is not a wiki-embed at all. Returns '' (empty string, not None) if it IS
    a recognized wiki-embed that intentionally resolves to nothing in this
    render mode — e.g. a Tier-3 ![[gm_secrets/...]] embed stripped from a
    public build. Callers must check `is not None`, not truthiness, or a
    correctly-stripped embed falls through and its raw ![[...]] syntax leaks
    into the page as a literal paragraph.

    Tier 3 logic:
      - path contains 'gm_secrets/': public → '' (stripped); GM → rendered block
      - .md or extensionless with gm_secrets/ prefix → prose transclusion
    """
    obs_m = re.match(r'^!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]$', p)
    if not obs_m:
        return None

    path_part  = obs_m.group(1).strip()
    alias_part = (obs_m.group(2) or '').split('|')[0].strip()
    fname = Path(path_part).name
    ext   = Path(fname).suffix.lower()

    # Tier 3: gm_secrets/ prose transclusion
    if 'gm_secrets/' in path_part.replace('\\', '/'):
        if not gm_mode or vault is None:
            return ''
        fname_md = fname if ext == '.md' else fname + '.md'
        matches  = list(vault.rglob(fname_md))
        if not matches:
            return f'<div class="gm-block"><em>⚠ GM embed not found: {escape(fname_md)}</em></div>\n'
        raw = matches[0].read_text(encoding='utf-8')
        # Strip frontmatter inline (avoid circular import with shared.frontmatter)
        raw_body = re.sub(r'^---\n.*?\n---\n', '', raw, flags=re.DOTALL).strip()
        body_html, _ = render_body(raw_body, vault, vault / 'docs', gm_mode=gm_mode)
        return f'<div class="gm-block">{body_html}</div>\n'

    if ext in AUDIO_EXTS:
        src   = escape(f'/audio/{fname}')
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
        if vault is not None and docs is not None:
            from shared.assets import prepare_image
            resolved = prepare_image(fname, vault, docs)
            src = escape(resolved or f'/images/{fname}')
        else:
            src = escape(f'/images/{fname}')
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
        if wiki_html is not None:
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


_CALLOUT_MARKER = re.compile(r'^\[!([\w-]+)\]\s*(.*)$')
_BULLET = re.compile(r'^[-*]\s+')
_ORDERED_ITEM = re.compile(r'^(\d+)[.)]\s+(.*)$')


def _render_ordered_list(para: str) -> str:
    """Render a paragraph whose every line is '1. text' as an <ol>.

    Returns '' when any line is not an ordered item, so the caller falls
    through to its other block types. The first number becomes the list's
    start, so a lone '7. **Title**' paragraph still reads as item 7.
    """
    items = [_ORDERED_ITEM.match(ln.strip()) for ln in para.splitlines() if ln.strip()]
    if not items or not all(items):
        return ''
    start = int(items[0].group(1))
    start_attr = f' start="{start}"' if start != 1 else ''
    lis = ''.join(f'  <li>{inline_md(m.group(2))}</li>\n' for m in items)
    return f'<ol{start_attr}>\n{lis}</ol>\n'


def _render_callout(para: str) -> str:
    """Render a '> ' blockquote paragraph as a callout div.

    A plain quote keeps the single-div form. A quote carrying an Obsidian
    '[!type] Title' marker or bullet lines renders structured: the title, one
    <p> per run of text lines, and a <ul> per run of bullets. Lines without a
    leading '>' (lazy continuation) belong to the quote, as in Obsidian.
    """
    inner_lines = []
    for ln in para.splitlines():
        ls = ln.strip()
        inner_lines.append(ls[1:].strip() if ls.startswith('>') else ls)

    marker = _CALLOUT_MARKER.match(inner_lines[0]) if inner_lines else None
    has_bullets = any(_BULLET.match(ln) for ln in inner_lines)
    if not marker and not has_bullets:
        inner = re.sub(r'^>\s*', '', para, flags=re.MULTILINE).strip()
        return f'<div class="callout">{inline_md(inner)}</div>\n'

    parts: list[str] = []
    text_buf: list[str] = []
    bullet_buf: list[str] = []

    def _flush() -> None:
        if text_buf:
            parts.append(f'<p>{inline_md(" ".join(text_buf))}</p>\n')
            text_buf.clear()
        if bullet_buf:
            parts.append('<ul>\n' + ''.join(f'  <li>{inline_md(b)}</li>\n' for b in bullet_buf) + '</ul>\n')
            bullet_buf.clear()

    cls = 'callout'
    if marker:
        cls += f' callout-{marker.group(1)}'
        if marker.group(2):
            parts.append(f'<div class="callout-title">{inline_md(marker.group(2))}</div>\n')
        inner_lines = inner_lines[1:]

    for ln in inner_lines:
        if not ln:
            _flush()
        elif _BULLET.match(ln):
            if text_buf:
                _flush()
            bullet_buf.append(_BULLET.sub('', ln))
        else:
            if bullet_buf:
                _flush()
            text_buf.append(ln)
    _flush()
    return f'<div class="{cls}">\n{"".join(parts)}</div>\n'


def render_body(
    body: str,
    vault: 'Path',
    docs: 'Path',
    gm_mode: bool = False,
    revealed_ids: 'set[str] | None' = None,
    keep_h1: bool = False,
    ordered_lists: bool = False,
) -> 'tuple[str, list[dict]]':
    """Render a full Markdown body to HTML with component support.

    Handles (in priority order):
      ![[gm_secrets/f]] → GM prose block (Tier 3) or stripped (public)
      ![[file|caption]] → lore-figure or audio-player (via render_wiki_embed)
      ![alt](path)      → lore-figure
      > [!gm-only]      → GM callout block (Tier 2) or stripped (public)
      **Name:** text    → feature-box (accumulated into feature-grid)
      # heading         → stripped (the page template owns the <h1>), or with
                          keep_h1=True an <h2 class="part-title"> for documents
                          that use H1 for parts inside the page
      ## heading        → <h2 id=...>  (jump nav level 2)
      ### heading       → <h3 id=...>  (jump nav level 3)
      > text            → callout div; '> [!type] Title' and bullet lines inside
                          the quote render as a titled, structured callout
      1. item           → <ol start=N>  (only with ordered_lists=True, and only
                          when every line of the paragraph is numbered; otherwise
                          the numbered lines stay a <p>, as ancestry pages expect)
      - item / * item   → <ul>
      anything else     → <p>

    Strips: frontmatter, Obsidian %% comments, wikilinks (preserving ![[]] embeds),
    Obsidian callout markers (except [!gm-only] which is handled by Tier 2).

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
        # Tier 2: GM-only callout block > [!gm-only] or > [!gm-only id=some-id]
        # The preprocessing regex (^>\s*\[!\w+\]\s*$) leaves [!gm-only] intact because
        # \w+ does not match across hyphens, so the marker survives to here.
        # Optional id= attribute enables build-time promotion via gm_revealed frontmatter.
        gm_marker = re.match(r'^>\s*\[!gm-only(?:\s+id=([^\]\s]+))?\]', para)
        if gm_marker:
            _flush_features()
            block_id = gm_marker.group(1)  # None if no id= attribute
            lines = para.splitlines()
            inner_lines = [re.sub(r'^>\s?', '', ln) for ln in lines[1:]]
            inner = '\n'.join(inner_lines).strip()
            # Revealed block: promoted to player-visible `.revealed-content` regardless of gm_mode
            if block_id and revealed_ids is not None and block_id in revealed_ids:
                html_parts.append(
                    f'<div class="revealed-content gm-callout--revealed">{inline_md(inner)}</div>\n'
                )
            elif gm_mode:
                css_cls = f'gm-callout gm-callout--id-{block_id}' if block_id else 'gm-callout'
                html_parts.append(f'<div class="{css_cls}">{inline_md(inner)}</div>\n')
            # public + unrevealed: strip entirely — GM content never reaches the DOM
            continue

        # Wiki-embed: ![[file|caption|width]] → figure, audio, or GM prose block
        wiki_html = render_wiki_embed(para, vault=vault, docs=docs, gm_mode=gm_mode)
        if wiki_html is not None:
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

        # Feature box: **Name:** text  OR  **_Name:_** text  (bold-italic name variant)
        feat = re.match(r'^\*\*_?(.+?):_?\*\*\s*(.+)', para, re.DOTALL)
        if feat:
            feature_buffer.append((feat.group(1).strip(), feat.group(2).strip()))
            continue

        # Flush features before non-feature content
        _flush_features()

        # H1 header — strip; page template owns the <h1> from frontmatter title
        if para.startswith('# ') and not para.startswith('## '):
            if keep_h1:
                # '# ***Act 1***' is emphasis on a heading; the heading style carries it
                text = re.sub(r'^(\*{1,3})(.+?)\1$', r'\2', para[2:].strip())
                anchor = _slug_anchor(text)
                jump_nav_items.append({'text': text, 'anchor': anchor, 'level': 1})
                html_parts.append(f'<h2 class="part-title" id="{anchor}">{inline_md(text)}</h2>\n')
            continue

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
            html_parts.append(_render_callout(para))
            continue

        # Ordered list
        ol = _render_ordered_list(para) if ordered_lists else ''
        if ol:
            html_parts.append(ol)
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