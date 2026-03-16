#!/usr/bin/env python3
"""
World Document HTML Generator
================================
Converts an Obsidian source .md file → styled HTML using the Campaign Frame
design system (parchment / gold / crimson · EB Garamond + Cinzel).

Supports two document types:
  myth / lore  — prose page with cover image, epigraph, body, section cards
  timeline     — visual timeline with era bands and lane rows

Usage:
    python generate_world_html.py source.md
    python generate_world_html.py source.md --output docs/my-doc.html
"""

import re
import argparse
from pathlib import Path
from html import escape

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Shared CSS design system (matches Campaign Frame aesthetic)
# ---------------------------------------------------------------------------

CSS_BASE = """
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
      font-size: 17px;
      line-height: 1.72;
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

    .content {
      position: relative;
      z-index: 1;
      padding: 2.8rem 3rem;
    }

    .section-title {
      font-family: 'Cinzel', serif;
      font-size: 1.45rem;
      font-weight: 600;
      color: var(--crimson);
      letter-spacing: 0.04em;
      margin-bottom: 0.2rem;
      padding-bottom: 0.4rem;
      border-bottom: 2px solid var(--rule);
    }

    .section { margin-bottom: 2.8rem; }

    p { margin-bottom: 1em; }
    p:last-child { margin-bottom: 0; }

    .callout {
      background: var(--parchment2);
      border-left: 3px solid var(--gold);
      border-radius: 2px;
      padding: 0.9rem 1.1rem;
      margin: 1.1rem 0;
      font-size: 0.97rem;
    }

    .divider {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--gold), transparent);
      margin: 2rem 0;
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
    }

    .credits {
      background: var(--steel);
      color: rgba(245,237,216,0.55);
      padding: 1.4rem 3rem;
      font-size: 0.85rem;
      line-height: 1.6;
    }

    @media (max-width: 640px) {
      .content { padding: 1.8rem 1.4rem; }
      .banner  { padding: 0.5rem 1.4rem; }
    }
"""

CSS_MYTH = """
    /* --- Myth/Lore specific --- */
    .cover {
      position: relative;
      min-height: 380px;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      overflow: hidden;
    }

    .cover-image {
      position: absolute; inset: 0;
      background-size: cover;
      background-position: center 30%;
      z-index: 0;
    }

    .cover-gradient {
      position: absolute; inset: 0;
      background: linear-gradient(to bottom,
        rgba(26,18,8,0.05) 0%,
        rgba(26,18,8,0.5)  55%,
        rgba(26,18,8,0.92) 100%);
      z-index: 1;
    }

    .cover-content {
      position: relative;
      z-index: 2;
      padding: 2rem 3rem 2.5rem;
      color: var(--parchment);
    }

    .cover-title {
      font-family: 'Cinzel', serif;
      font-size: 2.8rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      line-height: 1.1;
      color: #f5e6c0;
      text-shadow: 0 2px 12px rgba(0,0,0,0.7);
      margin-bottom: 0.3rem;
    }

    .cover-tag {
      font-family: 'Cinzel', serif;
      font-size: 0.78rem;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--gold-light);
    }

    .no-cover-header {
      background: var(--steel);
      padding: 2.5rem 3rem 1.8rem;
      color: var(--parchment);
    }

    .epigraph {
      font-style: italic;
      font-size: 1.22rem;
      color: var(--steel);
      line-height: 1.65;
      margin-bottom: 2rem;
      padding-bottom: 1.4rem;
      border-bottom: 1px solid var(--rule);
    }

    .myth-body p {
      margin-bottom: 1.1em;
      font-size: 1.02rem;
      line-height: 1.78;
    }

    @media (max-width: 640px) {
      .cover-title { font-size: 2rem; }
      .cover-content { padding: 1.5rem 1.4rem 2rem; }
    }
"""

CSS_TIMELINE = """
    /* --- Timeline list view (LK-inspired vertical card layout) --- */

    /* Dark page for timeline */
    .page-wrap { background: #0d0a05; }
    .page-wrap::before { opacity: 0.1; }
    .content { padding: 0; }

    .tl-header {
      background: var(--steel);
      padding: 2rem 3rem 1.6rem;
      color: var(--parchment);
    }

    .tl-title {
      font-family: 'Cinzel', serif;
      font-size: 2.2rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      color: #f5e6c0;
      margin-bottom: 0.2rem;
    }

    .tl-calendar {
      font-family: 'Cinzel', serif;
      font-size: 0.75rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--gold-light);
    }

    .tl-list-wrap { padding: 0.5rem 0 2.5rem; }

    /* Each event row: date | connector | card */
    .tl-list-entry {
      display: grid;
      grid-template-columns: 160px 48px 1fr;
      min-height: 165px;
      position: relative;
    }

    .tl-list-entry.is-era {
      min-height: 80px;
      opacity: 0.65;
    }

    /* Left: date column */
    .tl-date-col {
      padding: 1.5rem 1rem 1.5rem 1.5rem;
      text-align: right;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    }

    .tl-date-main {
      font-family: 'Cinzel', serif;
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--parchment);
      line-height: 1.3;
    }

    .tl-date-end {
      font-family: 'Cinzel', serif;
      font-size: 0.7rem;
      color: rgba(245,237,216,0.42);
      margin-top: 0.15rem;
    }

    .tl-date-gap {
      font-family: 'EB Garamond', serif;
      font-size: 0.73rem;
      color: rgba(245,237,216,0.28);
      margin-top: 0.5rem;
      font-style: italic;
    }

    /* Center: continuous vertical line + diamond marker */
    .tl-connector-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
    }

    .tl-connector-line {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 1px;
      background: rgba(184,146,44,0.22);
    }

    .tl-diamond {
      position: relative;
      z-index: 2;
      width: 11px;
      height: 11px;
      border-radius: 2px;
      transform: rotate(45deg);
      margin-top: 1.6rem;
      flex-shrink: 0;
    }

    .tl-list-entry.is-era .tl-diamond {
      width: 7px;
      height: 7px;
      margin-top: 1.1rem;
    }

    /* Right: event card */
    .tl-card-col { padding: 0.75rem 1.5rem 0.75rem 0.5rem; }

    .tl-card {
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
      min-height: 135px;
    }

    .tl-list-entry.is-era .tl-card { min-height: 55px; }

    /* Lane badge pill — top-left of card */
    .tl-card-badge {
      position: absolute;
      top: 0.55rem;
      left: 0.55rem;
      background: rgba(26,18,8,0.65);
      color: rgba(245,237,216,0.85);
      font-family: 'Cinzel', serif;
      font-size: 0.58rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      padding: 0.2rem 0.55rem;
      border-radius: 100px;
      z-index: 2;
      white-space: nowrap;
    }

    /* Image area — empty by default, takes remaining height */
    .tl-card-image { flex: 1; min-height: 68px; }
    .tl-list-entry.is-era .tl-card-image { min-height: 8px; }

    /* Bottom info row: icon + name + date range */
    .tl-card-info {
      padding: 0.6rem 0.75rem;
      background: rgba(0,0,0,0.42);
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .tl-card-icon {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: rgba(255,255,255,0.1);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
      flex-shrink: 0;
    }

    .tl-card-name-wrap { flex: 1; min-width: 0; }

    .tl-card-name {
      font-family: 'Cinzel', serif;
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--parchment);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .tl-card-range {
      font-family: 'EB Garamond', serif;
      font-size: 0.73rem;
      color: rgba(245,237,216,0.38);
      margin-top: 0.05rem;
    }

    .credits { border-top: 1px solid rgba(184,146,44,0.15); }

    @media (max-width: 640px) {
      .tl-list-entry { grid-template-columns: 90px 36px 1fr; }
      .tl-date-col { padding: 1rem 0.5rem 1rem 0.75rem; }
      .tl-header { padding: 1.5rem 1.4rem 1.2rem; }
      .tl-card-col { padding: 0.5rem 0.75rem 0.5rem 0.25rem; }
    }
"""

FAVICON = (
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='10' fill='%231a1208'/>"
    "<polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 "
    "81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 33.4,43.1 "
    "18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>"
)


# ---------------------------------------------------------------------------
# Shared parsing utilities
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r'^---\n(.*?\n)---\n', text, re.DOTALL)
    if not m:
        return {}, text
    fm_text = m.group(1)
    body = text[m.end():]
    if _YAML_AVAILABLE:
        try:
            fm = yaml.safe_load(fm_text) or {}
        except Exception:
            fm = {}
    else:
        fm = {}
        for line in fm_text.splitlines():
            kv = line.split(':', 1)
            if len(kv) == 2:
                k, v = kv[0].strip(), kv[1].strip()
                fm[k] = v.strip('"\'')
    return fm, body


def strip_secret_blocks(text: str) -> str:
    """Remove all %% ... %% blocks (GM-only content)."""
    return re.sub(r'%%.*?%%', '', text, flags=re.DOTALL)


def strip_wikilinks(text: str) -> str:
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    return text


def strip_obsidian_embeds(text: str) -> str:
    return re.sub(r'!\[\[[^\]]+\]\]', '', text)


def inline_md(text: str) -> str:
    """Convert inline markdown to HTML (after HTML-escaping)."""
    text = escape(text)
    text = re.sub(r'\*{3}(.+?)\*{3}', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text


def preprocess_body(text: str) -> str:
    text = strip_secret_blocks(text)
    text = strip_wikilinks(text)
    text = strip_obsidian_embeds(text)
    text = re.sub(r'^>\s*\[!\w+\]\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_sections(text: str) -> dict[str, str]:
    """Split text at ## headings into {title: body}."""
    sections: dict[str, str] = {}
    current_title = ''
    current_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r'^## ', line):
            sections[current_title] = '\n'.join(current_lines).strip()
            current_title = re.sub(r'^##\s+', '', line).strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections[current_title] = '\n'.join(current_lines).strip()
    return sections


# ---------------------------------------------------------------------------
# Myth/Lore HTML builder
# ---------------------------------------------------------------------------

def render_myth_para(line: str) -> str:
    """Render a single paragraph line, handling blockquotes."""
    line = line.strip()
    if line.startswith('> ') or line.startswith('>'):
        inner = re.sub(r'^>\s*', '', line).strip()
        return f'<div class="callout">{inline_md(inner)}</div>\n'
    return f'<p>{inline_md(line)}</p>\n'


def render_myth_section(title: str, content: str) -> str:
    paras = [p.strip() for p in re.split(r'\n\n+', content) if p.strip()]
    body_html = ''.join(render_myth_para(p) for p in paras)
    return (
        f'<div class="section">\n'
        f'  <div class="section-title">{escape(title)}</div>\n'
        f'  {body_html}'
        f'</div>\n'
    )


def build_myth_html(fm: dict, body: str) -> str:
    title = fm.get('title', 'Untitled')
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    tag_label = ', '.join(str(t) for t in tags) if tags else ''
    cover_image = fm.get('lk_cover_image', '')

    body = preprocess_body(body)
    sections = split_sections(body)

    # Preamble (before first ##) — first italic line is epigraph
    preamble = sections.get('', '')
    preamble_lines = [l.strip() for l in preamble.splitlines() if l.strip()]

    epigraph = ''
    body_paras: list[str] = []
    for line in preamble_lines:
        # Detect epigraph: line that is fully italic (starts and ends with _ or *)
        if not epigraph and re.match(r'^[_*].+[_*]$', line):
            epigraph = re.sub(r'^[_*](.+)[_*]$', r'\1', line)
        else:
            body_paras.append(line)

    # Named sections (Moral, Cultural Significance, etc.)
    named_sections = [(k, v) for k, v in sections.items() if k]

    # Assemble cover / header
    if cover_image:
        header_html = (
            f'<div class="cover">\n'
            f'  <div class="cover-image" style="background-image: url(\'{escape(cover_image)}\')"></div>\n'
            f'  <div class="cover-gradient"></div>\n'
            f'  <div class="cover-content">\n'
            f'    <div class="cover-title">{escape(title)}</div>\n'
            + (f'    <div class="cover-tag">{escape(tag_label)}</div>\n' if tag_label else '')
            + f'  </div>\n</div>\n'
        )
    else:
        header_html = (
            f'<div class="no-cover-header">\n'
            f'  <div class="cover-title">{escape(title)}</div>\n'
            + (f'  <div class="cover-tag">{escape(tag_label)}</div>\n' if tag_label else '')
            + f'</div>\n'
        )

    # Banner
    doc_type_label = str(fm.get('type', 'lore')).capitalize()
    banner_html = (
        f'<div class="banner">'
        f'<span>Tarim-Shaiel</span>'
        f'<span>{escape(doc_type_label)}</span>'
        f'</div>\n'
        f'<div class="banner-rule"></div>\n'
    )

    # Content
    content_parts: list[str] = []

    if epigraph:
        content_parts.append(f'<div class="epigraph">{inline_md(epigraph)}</div>\n')

    if body_paras:
        paras_html = ''.join(render_myth_para(p) for p in body_paras)
        content_parts.append(f'<div class="myth-body">{paras_html}</div>\n')

    if named_sections:
        content_parts.append('<div class="divider"></div>\n')
        for sec_title, sec_body in named_sections:
            if sec_body.strip():
                content_parts.append(render_myth_section(sec_title, sec_body))

    content_html = '\n'.join(content_parts)

    return _html_wrapper(
        title=title,
        css=CSS_BASE + CSS_MYTH,
        header_html=header_html,
        banner_html=banner_html,
        content_html=content_html,
    )


# ---------------------------------------------------------------------------
# Timeline HTML builder  (list-view layout, LK-inspired)
# ---------------------------------------------------------------------------

MINUTES_PER_YEAR = int(365.25 * 24 * 60)


def year_to_minutes(year_str: str) -> int:
    try:
        return int(float(year_str) * MINUTES_PER_YEAR)
    except (ValueError, TypeError):
        return 0


def minutes_to_year(minutes: int) -> float:
    return minutes / MINUTES_PER_YEAR


def parse_event_line_html(line: str) -> dict | None:
    """Parse pipe-syntax event line → dict with name, start_min, end_min, color, icon, opacity."""
    line = line.strip().lstrip('- ').strip()
    m = re.match(r'"([^"]+)"\s*(.*)', line)
    if not m:
        return None
    ev: dict = {'name': m.group(1)}
    for part in m.group(2).split('|'):
        part = part.strip()
        if not part:
            continue
        if ':' in part:
            k, v = part.split(':', 1)
            ev[k.strip().lower()] = v.strip().strip('"\'')
    ev['start_min'] = year_to_minutes(ev.get('start', ev.get('date', '0')))
    ev['end_min']   = year_to_minutes(ev['end']) if 'end' in ev else None
    ev['color']     = ev.get('color', '#6B7280')
    ev['opacity']   = float(ev.get('opacity', '1.0'))
    ev['icon']      = ev.get('icon', '')
    return ev


# Icon name → Unicode symbol mapping
_ICON_MAP = {
    'flag':             '⚐',
    'swords':           '⚔',
    'sword':            '⚔',
    'scroll':           '📜',
    'fire':             '✦',
    'flame':            '✦',
    'city':             '◉',
    'wind':             '〜',
    'hourglass':        '⧗',
    'star':             '★',
    'hat-wizard':       '✧',
    'arrows-to-circle': '↺',
    'crown':            '♛',
    'heart':            '♥',
    'skull':            '☠',
    'shield':           '⛊',
    'anchor':           '⚓',
    'leaf':             '❧',
    'sun':              '☀',
    'moon':             '☽',
    'lightning':        '⚡',
    'book':             '📖',
    'key':              '🗝',
    'eye':              '◉',
    'axe':              '⚒',
    'tower':            '⌂',
    'map':              '⊞',
    'compass':          '⊕',
}


def _icon_char(name: str) -> str:
    return _ICON_MAP.get((name or '').lower().strip(), '◆')


def _era_abbrev(era_name: str) -> str:
    """'The Held Breath' → 'HB', 'The Slow Forgetting' → 'SF'."""
    stops = {'the', 'a', 'an', 'of', 'in', 'at', 'by', 'for', 'and', 'or'}
    words = [w for w in era_name.split() if w.lower() not in stops]
    return ''.join(w[0].upper() for w in words[:3]) if words else era_name[:3].upper()


def _era_date_label(year: float, era_defs: list) -> str:
    """Format world-year as 'ERA YEAR', e.g. 'HB 188' or 'SF -500'."""
    for era in era_defs:
        s, e = era['start_yr'], era['end_yr']
        if (e is None and year >= s) or (e is not None and s <= year <= e):
            return f"{era['abbrev']} {int(year)}"
    return str(int(year))


def _gap_label(years: float) -> str:
    y = int(years + 0.5)
    if y <= 0:
        return ''
    return f'{y:,} year{"s" if y != 1 else ""} later'


def render_timeline_html(fm: dict, body: str) -> str:
    title    = fm.get('title', 'Timeline')
    calendar = fm.get('calendar', '')

    body = strip_secret_blocks(body)
    body = strip_wikilinks(body)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()

    # Parse ## sections → lanes
    sections: list[tuple[str, list[dict]]] = []
    cur_name   = ''
    cur_events: list[dict] = []

    for line in body.splitlines():
        if re.match(r'^## ', line):
            if cur_name:
                sections.append((cur_name, cur_events))
            cur_name   = re.sub(r'^##\s+', '', line).strip()
            cur_events = []
        elif line.strip().startswith('-') and cur_name:
            ev = parse_event_line_html(line)
            if ev:
                cur_events.append(ev)
    if cur_name:
        sections.append((cur_name, cur_events))

    if not sections:
        return build_myth_html(fm, body)

    # Build era defs from the Eras lane for date labelling
    era_defs: list[dict] = []
    for lane_name, events in sections:
        if lane_name.lower() == 'eras':
            for ev in events:
                era_defs.append({
                    'name':     ev['name'],
                    'abbrev':   _era_abbrev(ev['name']),
                    'start_yr': ev['start_min'] / MINUTES_PER_YEAR,
                    'end_yr':   (ev['end_min'] / MINUTES_PER_YEAR
                                 if ev['end_min'] is not None else None),
                    'color':    ev['color'],
                })

    # Flatten all events, tag with lane + is_era, sort by start
    all_entries: list[dict] = []
    for lane_name, events in sections:
        is_era_lane = lane_name.lower() == 'eras'
        for ev in events:
            entry          = dict(ev)
            entry['lane']  = lane_name
            entry['is_era'] = is_era_lane
            all_entries.append(entry)
    all_entries.sort(key=lambda e: e['start_min'])

    # Build HTML rows
    rows_html = ''
    prev_yr: float | None = None

    for entry in all_entries:
        start_yr = entry['start_min'] / MINUTES_PER_YEAR
        end_yr   = (entry['end_min'] / MINUTES_PER_YEAR
                    if entry['end_min'] is not None else None)
        color    = entry['color']
        opacity  = entry['opacity']
        is_era   = entry['is_era']
        icon     = _icon_char(entry['icon'])

        # Gap label since previous event
        gap_html = ''
        if prev_yr is not None:
            lbl = _gap_label(start_yr - prev_yr)
            if lbl:
                gap_html = f'<div class="tl-date-gap">{escape(lbl)}</div>'
        prev_yr = start_yr

        # Left-column date
        date_label = _era_date_label(start_yr, era_defs)
        date_html  = f'<div class="tl-date-main">{escape(date_label)}</div>'
        if end_yr is not None and not is_era:
            date_html += (
                f'<div class="tl-date-end">'
                f'→ {escape(_era_date_label(end_yr, era_defs))}'
                f'</div>'
            )

        # Card footer date range
        if end_yr is not None:
            end_label  = _era_date_label(end_yr, era_defs)
            duration   = int(abs(end_yr - start_yr))
            range_text = f"{date_label} → {end_label} ({duration:,} years)"
        else:
            range_text = date_label

        # Card background: subtle color tint over near-black
        card_bg     = f"linear-gradient(160deg, {color}35 0%, rgba(14,11,6,0.93) 100%)"
        entry_class = 'is-era' if is_era else ''

        # Image area: background-image if provided, else empty (shows color tint)
        image_url = entry.get('image', '')
        img_style = (
            f'background-image:url({escape(image_url)});'
            f'background-size:cover;background-position:center;'
            if image_url else ''
        )

        rows_html += f"""<div class="tl-list-entry {entry_class}">
  <div class="tl-date-col">
    {date_html}
    {gap_html}
  </div>
  <div class="tl-connector-col">
    <div class="tl-connector-line"></div>
    <div class="tl-diamond" style="background:{color};opacity:{opacity:.2f};"></div>
  </div>
  <div class="tl-card-col">
    <div class="tl-card" style="background:{card_bg};">
      <span class="tl-card-badge">{escape(entry['lane'])}</span>
      <div class="tl-card-image" style="{img_style}"></div>
      <div class="tl-card-info">
        <div class="tl-card-icon">{icon}</div>
        <div class="tl-card-name-wrap">
          <div class="tl-card-name">{escape(entry['name'])}</div>
          <div class="tl-card-range">{escape(range_text)}</div>
        </div>
      </div>
    </div>
  </div>
</div>
"""

    header_html = (
        f'<div class="tl-header">\n'
        f'  <div class="tl-title">{escape(title)}</div>\n'
        + (f'  <div class="tl-calendar">{escape(calendar)}</div>\n' if calendar else '')
        + f'</div>\n'
    )

    banner_html = (
        '<div class="banner"><span>Tarim-Shaiel</span><span>Timeline</span></div>\n'
        '<div class="banner-rule"></div>\n'
    )

    content_html = f'<div class="tl-list-wrap">\n{rows_html}\n</div>\n'

    return _html_wrapper(
        title=title,
        css=CSS_BASE + CSS_TIMELINE,
        header_html=header_html,
        banner_html=banner_html,
        content_html=content_html,
    )


# ---------------------------------------------------------------------------
# HTML wrapper
# ---------------------------------------------------------------------------

def _html_wrapper(
    title: str,
    css: str,
    header_html: str,
    banner_html: str,
    content_html: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)} &mdash; Tarim-Shaiel</title>
  <link rel="icon" href="{FAVICON}">
  <!-- AUTO-GENERATED by utilities/legendkeeper-pipeline/generate_world_html.py — do not hand-edit -->
  <style>{css}  </style>
</head>
<body>

<div class="page-wrap">

{header_html}
{banner_html}

  <div class="content">
{content_html}
  </div>

  <div class="credits">Tarim-Shaiel &middot; Daggerheart Campaign &middot; 2026</div>

</div>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate Campaign Frame-style HTML from an Obsidian source file.'
    )
    parser.add_argument('source', help='Source .md file path')
    parser.add_argument(
        '--output', '-o',
        help='Output HTML path (default: docs/<source-stem>.html)',
    )
    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise FileNotFoundError(f'Source file not found: {src}')

    raw = src.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(raw)
    doc_type = fm.get('type', '').lower()

    if doc_type == 'timeline':
        html = render_timeline_html(fm, body)
    else:
        html = build_myth_html(fm, body)

    # Default output: docs/<stem>.html relative to vault root
    if args.output:
        out_path = Path(args.output)
    else:
        vault_root = Path(__file__).parent.parent.parent
        slug = re.sub(r'[^\w\-]', '-', src.stem.lower().replace(' ', '-'))
        slug = re.sub(r'-+', '-', slug).strip('-')
        out_path = vault_root / 'docs' / f'{slug}.html'

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    print(f'HTML written: {out_path}')
    print(f'  Type: {doc_type or "page (default)"}')
    print(f'  Title: {fm.get("title", "(no title)")}')


if __name__ == '__main__':
    main()
