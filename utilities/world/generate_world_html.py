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
    python generate_world_html.py source.md --public   # skip gm_secrets docs (fails closed)
    python generate_world_html.py source.md --open     # open in browser after generating
"""

import re
import argparse
from pathlib import Path
from html import escape

# ---------------------------------------------------------------------------
# Local asset resolution
# ---------------------------------------------------------------------------

_LK_ASSET_RE = re.compile(r'https://assets\.legendkeeper\.com/([\w.\-]+)')


def _resolve_image_url(url: str) -> str:
    """Return a local relative path if the asset exists in docs/assets/, else the original URL.

    Source .md files keep LK CDN URLs (preserves round-trip to LegendKeeper).
    When download_lk_assets.py has fetched the files locally, this transparently
    upgrades to a self-hosted relative path so the HTML works without LK auth.
    """
    if not url:
        return url
    m = _LK_ASSET_RE.match(url)
    if m:
        local = Path('docs/assets') / m.group(1)
        if local.exists():
            return f'assets/{m.group(1)}'
    return url

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
DOCS_DIR   = VAULT_ROOT / "docs"

import sys as _sys
_sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.assets import prepare_image, prepare_audio_wiki

# ---------------------------------------------------------------------------
# Shared CSS design system (loaded from .css files at runtime; inlined into HTML)
# world_base.css  — shared base (both myth/lore and timeline)
# world_myth.css  — myth/lore-specific additions
# world_timeline.css — timeline-specific additions
# ---------------------------------------------------------------------------

CSS_BASE = (SCRIPT_DIR / "world_base.css").read_text()
CSS_MYTH = (SCRIPT_DIR / "world_myth.css").read_text()
CSS_TIMELINE = (SCRIPT_DIR / "world_timeline.css").read_text()


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


_AUDIO_EXTS = {'.mp3', '.ogg', '.wav', '.m4a', '.flac', '.aac'}
_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}


def prepare_embeds(text: str) -> str:
    """Copy ![[image/audio]] vault assets to docs/ before rendering.

    Returns text unchanged — wiki-embed syntax is preserved so render_myth_para()
    can render it as <figure> or <audio>. Assets are copied here so they exist
    in docs/images/ or docs/audio/ when the HTML is served.
    """
    for m in re.finditer(r'!\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]', text):
        fname = Path(m.group(1).strip()).name
        ext   = Path(fname).suffix.lower()
        if ext in _IMAGE_EXTS:
            prepare_image(fname, VAULT_ROOT, DOCS_DIR)
        elif ext in _AUDIO_EXTS:
            prepare_audio_wiki(fname, VAULT_ROOT, DOCS_DIR)
    return text


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
    # Note: ![[embeds]] are NOT stripped here — prepare_embeds() has already
    # copied their assets; render_myth_para() renders them as figure/audio HTML.
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
    """Render a single paragraph line, handling blockquotes and wiki-embeds."""
    line = line.strip()
    # Wiki-embed: ![[image.png|alias]] or ![[audio.mp3]]
    m = re.match(r'^!\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]$', line)
    if m:
        path_part  = m.group(1).strip()
        alias_part = (m.group(2) or '').strip()
        fname = Path(path_part).name
        ext   = Path(fname).suffix.lower()
        if ext in _AUDIO_EXTS:
            from html import escape as _esc
            src   = _esc(f'audio/{fname}')
            label = _esc(alias_part or Path(fname).stem.replace('-', ' ').replace('_', ' ').title())
            return (
                f'<div class="audio-player">\n'
                f'  <div class="audio-player-label">{label}</div>\n'
                f'  <audio controls preload="metadata">'
                f'<source src="{src}" type="audio/mpeg" /></audio>\n'
                f'</div>\n'
            )
        else:
            from html import escape as _esc
            src = _esc(f'images/{fname}')
            alt = _esc(alias_part or fname.rsplit('.', 1)[0])
            return (
                f'<figure class="lore-figure">\n'
                f'  <img src="{src}" alt="{alt}" />\n'
                f'  <figcaption>{alt}</figcaption>\n'
                f'</figure>\n'
            )
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

    prepare_embeds(body)   # copy vault assets to docs/ before stripping/rendering
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
    """'The Held Breath' → 'HB', 'Împeratoriya Nû (New Empire)' → 'ÎN'."""
    # Strip parenthetical suffixes and em-dash clauses before abbreviating
    clean = re.sub(r'\s*\([^)]*\)', '', era_name)   # remove (...)
    clean = re.sub(r'\s*[—–].*$', '', clean)         # remove — clause
    clean = clean.strip()
    stops = {'the', 'a', 'an', 'of', 'in', 'at', 'by', 'for', 'and', 'or'}
    words = [w for w in clean.split()
             if w.lower() not in stops and w[:1].isalpha()]
    return ''.join(w[0].upper() for w in words[:3]) if words else era_name[:3].upper()


def _era_date_label(year: float, era_defs: list) -> str:
    """Format world-year as 'ERA YEAR', e.g. 'HB 188' or 'HJ 579'.

    Each era_def may have start_yr and/or end_yr (either can be None = open-ended).
    Backward eras (era['backward'] = True) display abs(year) instead of year.
    """
    for era in era_defs:
        s = era.get('start_yr')
        e = era.get('end_yr')
        if s is not None and year < s:
            continue
        if e is not None and year > e:
            continue
        abbrev = era['abbrev']
        if era.get('backward'):
            return f"{abbrev} {int(abs(year))}"
        return f"{abbrev} {int(year)}"
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

    # Parse ## sections → Calendar Eras (special, not a swimlane) + display lanes
    # A "## Calendar Eras" section defines the year-labeling system (like LK's
    # Time System eras: HJ/HB).  It is NOT rendered as an event lane.
    era_defs: list[dict] = []
    sections: list[tuple[str, list[dict]]] = []
    cur_name    = ''
    cur_events: list[dict] = []
    is_cal_era  = False

    for line in body.splitlines():
        if re.match(r'^## ', line):
            if cur_name:
                if is_cal_era:
                    for ev in cur_events:
                        abbrev   = ev.get('abbrev') or _era_abbrev(ev['name'])
                        s_raw    = ev.get('start', ev.get('date'))
                        e_raw    = ev.get('end')
                        backward = ev.get('backward', '').lower() in ('true', '1', 'yes')
                        era_defs.append({
                            'name':     ev['name'],
                            'abbrev':   abbrev,
                            'start_yr': float(s_raw) if s_raw else None,
                            'end_yr':   float(e_raw) if e_raw else None,
                            'backward': backward,
                        })
                else:
                    sections.append((cur_name, cur_events))
            cur_name   = re.sub(r'^##\s+', '', line).strip()
            is_cal_era = cur_name.lower() == 'calendar eras'
            cur_events = []
        elif line.strip().startswith('-') and cur_name:
            ev = parse_event_line_html(line)
            if ev:
                cur_events.append(ev)

    # Flush last section
    if cur_name:
        if is_cal_era:
            for ev in cur_events:
                abbrev   = ev.get('abbrev') or _era_abbrev(ev['name'])
                s_raw    = ev.get('start', ev.get('date'))
                e_raw    = ev.get('end')
                backward = ev.get('backward', '').lower() in ('true', '1', 'yes')
                era_defs.append({
                    'name':     ev['name'],
                    'abbrev':   abbrev,
                    'start_yr': float(s_raw) if s_raw else None,
                    'end_yr':   float(e_raw) if e_raw else None,
                    'backward': backward,
                })
        else:
            sections.append((cur_name, cur_events))

    if not sections:
        return build_myth_html(fm, body)

    # Fallback: no Calendar Eras section → derive from Eras swimlane (backward compat)
    if not era_defs:
        for lane_name, events in sections:
            if lane_name.lower() == 'eras':
                for ev in events:
                    era_defs.append({
                        'name':     ev['name'],
                        'abbrev':   _era_abbrev(ev['name']),
                        'start_yr': ev['start_min'] / MINUTES_PER_YEAR,
                        'end_yr':   (ev['end_min'] / MINUTES_PER_YEAR
                                     if ev['end_min'] is not None else None),
                        'backward': False,
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
        # _resolve_image_url upgrades LK CDN URLs to local paths when available
        image_url = _resolve_image_url(entry.get('image', ''))
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

PIPELINE_TYPES = {'timeline', 'myth', 'lore'}


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate Campaign Frame-style HTML from an Obsidian source file.'
    )
    parser.add_argument('source', help='Source .md file path')
    parser.add_argument(
        '--output', '-o',
        help='Output HTML path (default: docs/<source-stem>.html)',
    )
    parser.add_argument(
        '--public', action='store_true',
        help='Public-only mode: only generate docs explicitly tagged visibility: public. '
             'Anything else (gm_secrets, untagged, typo) is skipped. Fails closed.',
    )
    parser.add_argument(
        '--open', action='store_true',
        help='Open generated HTML in the default browser after writing.',
    )
    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise FileNotFoundError(f'Source file not found: {src}')

    raw = src.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(raw)
    doc_type = fm.get('type', '').lower()

    # Silent skip: not a pipeline source type — exit 0 without noise.
    # Allows Shell Commands file-save event to fire on any .md without errors.
    if doc_type not in PIPELINE_TYPES:
        import sys
        sys.exit(0)

    # Visibility gate (fails closed): only generate if explicitly visibility: public.
    # Missing tag, gm_secrets, or any other value → skip in public mode.
    if args.public and fm.get('visibility') != 'public':
        print(f'Skipped (not visibility: public): {src}')
        import sys
        sys.exit(0)

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
    print(f'  Type: {doc_type}')
    print(f'  Title: {fm.get("title", "(no title)")}')
    print(f'  Visibility: {fm.get("visibility", "(unset — treated as gm_secrets)")}')

    if args.open:
        import subprocess
        subprocess.run(['open', str(out_path)])


if __name__ == '__main__':
    main()


# ---------------------------------------------------------------------------
# Generator protocol wrapper (used by utilities/build.py)
# ---------------------------------------------------------------------------
class _Generator:
    name = "world"
    description = "Generate styled HTML for a single myth/lore/timeline doc"

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
