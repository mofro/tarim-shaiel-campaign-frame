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
import json
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
            return f'/assets/{m.group(1)}'
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
    # Negative lookbehind (?<!!) preserves image embeds (![[...]])
    text = re.sub(r'(?<!!)\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'(?<!!)\[\[([^\]]+)\]\]', r'\1', text)
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
            src   = _esc(f'/audio/{fname}')
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
            src = _esc(f'/images/{fname}')
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


def build_myth_html(fm: dict, body: str, folder: str | None = None) -> str:
    """Build a styled HTML page for a lore/myth document.

    Args:
        fm:     Parsed frontmatter dict.
        body:   Raw markdown body text.
        folder: Parent folder name (e.g. 'ancestries') used to generate
                back-navigation breadcrumb. Pass None to omit.
    """
    from shared.html_render import render_body as _render_body

    title = fm.get('title', 'Untitled')
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    tag_label = ', '.join(str(t) for t in tags) if tags else ''

    # --- Resolve cover image (lk_cover_image → banner → hero) ---
    raw_cover = fm.get('lk_cover_image', '') or fm.get('banner', '') or fm.get('hero', '')
    cover_image = ''
    if raw_cover:
        if raw_cover.startswith('http'):
            cover_image = raw_cover
        else:
            cover_image = prepare_image(Path(raw_cover).name, VAULT_ROOT, DOCS_DIR) or ''
    banner_x = fm.get('banner-x', 50)
    banner_y = fm.get('banner-y', 50)

    prepare_embeds(body)   # copy vault assets to docs/ before rendering

    # Strip only secrets and Obsidian artefacts — render_body handles wikilinks
    # with the correct !-preserving negative lookbehind
    body = strip_secret_blocks(body)
    body = re.sub(r'^>\s*\[!\w+\]\s*$', '', body, flags=re.MULTILINE)
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = body.strip()

    # Detect epigraph: first italic-only line before any ## heading
    epigraph_html = ''
    lines_before_h2 = []
    for line in body.splitlines():
        if re.match(r'^## ', line):
            break
        lines_before_h2.append(line.strip())
    non_empty_pre = [l for l in lines_before_h2 if l]
    if non_empty_pre and re.match(r'^[_*].+[_*]$', non_empty_pre[0]):
        epigraph_text = re.sub(r'^[_*](.+)[_*]$', r'\1', non_empty_pre[0])
        epigraph_html = f'<div class="epigraph">{inline_md(epigraph_text)}</div>\n'
        body = body.replace(non_empty_pre[0], '', 1).strip()

    # Render full body with component support (images, features, jump nav, headers)
    content_html, jump_nav_items = _render_body(body, VAULT_ROOT, DOCS_DIR)
    if epigraph_html:
        content_html = epigraph_html + content_html

    # --- Back navigation ---
    # If frontmatter has parent-class, link to parent page; otherwise link to category.
    back_nav_html = ''
    back_href = ''
    back_label = ''
    parent_class = str(fm.get('parent-page', '') or fm.get('parent-class', '')).strip()
    if parent_class:
        parent_slug = re.sub(r'[^\w\-]', '-', parent_class.lower().replace(' ', '-'))
        parent_slug = re.sub(r'-+', '-', parent_slug).strip('-')
        back_href  = f'{parent_slug}.html'
        back_label = parent_class.replace('-', ' ').replace('_', ' ').title()
    elif folder:
        cat_label  = folder.replace('-', ' ').replace('_', ' ').title()
        back_href  = f'../category-{escape(folder)}.html'
        back_label = cat_label
    if back_href:
        back_nav_html = (
            f'<div class="back-nav">'
            f'<a href="{back_href}">&larr; {escape(back_label)}</a>'
            f'</div>\n'
        )

    # --- Jump navigation (shown when 2+ sections exist, opt-out with jump_nav: false) ---
    jump_nav_html = ''
    if len(jump_nav_items) >= 2 and (fm.get('jump_nav', True) is not False):
        nav_items = []
        if back_href:
            nav_items.append(f'  <li style="list-style:none"><a href="{back_href}">&larr; {escape(back_label)}</a></li>')
            nav_items.append('  <li class="nav-divider"></li>')
        for item in jump_nav_items:
            nav_items.append(f'  <li><a href="#{item["anchor"]}">{escape(item["text"])}</a></li>')
        nav_items.append('  <li class="nav-divider"></li>')
        nav_items.append('  <li style="list-style:none"><a href="#">&#8593; Top</a></li>')
        jump_nav_html = '<div class="jump-nav">\n<ul>\n' + '\n'.join(nav_items) + '\n</ul>\n</div>\n'

    # --- Cover / header ---
    if cover_image:
        header_html = (
            f'<div class="cover">\n'
            f'  <div class="cover-image" style="background-image: url(\'{escape(cover_image)}\'); background-position: {banner_x}% {banner_y}%"></div>\n'
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

    # --- Banner (frontmatter-overridable) ---
    doc_type_label = str(fm.get('type', 'lore')).replace('_', ' ').title()
    banner_left  = fm.get('banner_left',  'Tarim-Shaiel')
    banner_right = fm.get('banner_right', doc_type_label)
    banner_html = (
        f'<div class="banner">'
        f'<span>{escape(str(banner_left))}</span>'
        f'<span>{escape(str(banner_right))}</span>'
        f'</div>\n'
        f'<div class="banner-rule"></div>\n'
    )

    return _html_wrapper(
        title=title,
        css=CSS_BASE + CSS_MYTH,
        back_nav_html=back_nav_html,
        header_html=header_html,
        banner_html=banner_html,
        content_html=content_html,
        jump_nav_html=jump_nav_html,
    )


# ---------------------------------------------------------------------------
# Timeline HTML builder  (list-view layout, LK-inspired)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Faction data for D3 power chart (used in render_timeline_html)
# ---------------------------------------------------------------------------

FACTION_DISPLAY_NAMES = {
    "former_empire":  "Former Empire",
    "human_east":     "Eastern City-States",
    "orc_nations":    "Orc Nations",
    "elf_enclaves":   "Elven Enclaves",
    "dwarf_clans":    "Dwarf Clans",
    "goblin_cities":  "Goblin Free Cities",
    "mediators":      "Mediator Alliance",
    "trade_league":   "Trade League",
    "wizard":         "The Wizard",
}

# Map CSS-lowercased color → (faction_id, display_name) for fallback grouping
COLOR_FACTION_FALLBACK = {
    "#22c55e": ("orc_nations",   "Orc Nations"),
    "#eab308": ("former_empire", "Former Empire"),
    "#8b5cf6": ("elf_enclaves",  "Elven Enclaves"),
    "#a16207": ("dwarf_clans",   "Dwarf Clans"),
    "#f97316": ("goblin_cities", "Goblin Free Cities"),
    "#f59e0b": ("mediators",     "Mediator Alliance"),
    "#0ea5e9": ("trade_league",  "Trade League"),
    "#dc2626": ("wizard",        "The Wizard"),
}

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




def group_declarations_by_faction(declaration_events: list) -> dict:
    """Group declaration events by their faction field (or color fallback).

    Returns {fid: {'name': str, 'color': str, 'periods': [{'start': float, 'end': float}]}}
    preserving insertion order.
    """
    groups: dict = {}
    order: list = []

    for ev in declaration_events:
        color_lower = ev.get('color', '').lower()
        faction_field = ev.get('faction', '').lower().strip()

        if faction_field:
            fid = faction_field
            fname = FACTION_DISPLAY_NAMES.get(fid, fid.replace('_', ' ').title())
            fcolor = ev['color']
        else:
            fallback = COLOR_FACTION_FALLBACK.get(color_lower)
            if fallback:
                fid, fname = fallback
            else:
                fid = color_lower.lstrip('#') or 'unknown'
                fname = 'Unknown'
            fcolor = ev['color']

        if fid not in groups:
            groups[fid] = {'name': fname, 'color': fcolor, 'periods': []}
            order.append(fid)

        start_yr = ev['start_min'] / MINUTES_PER_YEAR
        end_yr = ev['end_min'] / MINUTES_PER_YEAR if ev['end_min'] is not None else start_yr
        groups[fid]['periods'].append({'start': start_yr, 'end': end_yr})

    return {fid: groups[fid] for fid in order}


def derive_influence_data(faction_groups: dict, year_min: int, year_max: int, step: int = 25) -> list:
    """Generate binary influence scores (0 or 80) per faction at each year step.

    A faction is active (score=80) at year Y if any of its declaration periods
    contains Y. Produces a list of dicts suitable for D3 stack().
    """
    fids = list(faction_groups.keys())
    rows = []
    year = year_min
    while year <= year_max:
        row: dict = {'year': year}
        for fid in fids:
            active = any(
                p['start'] <= year <= p['end']
                for p in faction_groups[fid]['periods']
            )
            row[fid] = 80 if active else 0
        rows.append(row)
        year += step
    return rows


def render_power_chart_section(
    faction_groups: dict,
    influence_data: list,
    epoch_events: list,
    year_min: int,
    year_max: int,
) -> str:
    """Return HTML+script for the D3 stacked-area faction influence chart."""
    if not faction_groups or not influence_data:
        return ''

    factions_json = json.dumps([
        {'id': fid, 'name': data['name'], 'color': data['color']}
        for fid, data in faction_groups.items()
    ])

    influence_json = json.dumps(influence_data)

    eras = []
    for ev in epoch_events:
        if ev.get('end_min') is not None and ev.get('start_min') is not None:
            eras.append({
                'start': round(ev['start_min'] / MINUTES_PER_YEAR, 1),
                'end':   round(ev['end_min']   / MINUTES_PER_YEAR, 1),
                'label': re.sub(r'\s*[\(—–].*', '', ev['name']).strip(),
                'shade': ev['color'],
            })
    eras_json = json.dumps(eras)

    container_html = (
        '\n<div class="tl-d3-section" id="tl-power">\n'
        '  <div class="tl-d3-inner">\n'
        '    <h2 class="tl-d3-heading">Rise &amp; Fall of Powers</h2>\n'
        '    <p class="tl-d3-desc">Relative political and military dominance '
        'along the Tarim-Shaiel corridor. Click legend items to show or hide factions.</p>\n'
        '    <div class="tl-chart-controls">\n'
        '      <button class="tl-chart-btn active" data-view="stacked">Stacked</button>\n'
        '      <button class="tl-chart-btn" data-view="stream">Stream</button>\n'
        '      <button class="tl-chart-btn" data-view="expanded">Expanded</button>\n'
        '    </div>\n'
        '    <div id="tl-influence-chart" class="tl-chart-container"></div>\n'
        '    <div id="tl-influence-legend" class="tl-legend"></div>\n'
        '  </div>\n'
        '</div>\n'
    )

    script_html = (
        '<script>\n'
        '(function() {\n'
        'var TL_FACTIONS = ' + factions_json + ';\n'
        'var TL_INFLUENCE_DATA = ' + influence_json + ';\n'
        'var TL_ERAS = ' + eras_json + ';\n'
        'window._TL_ERAS = TL_ERAS;\n'
        """
var tlCurrentView = 'stacked';
var tlHiddenFactions = new Set();

function formatTLYear(y) {
    if (y < 0) return 'HJ ' + Math.abs(Math.round(y));
    return 'HB ' + Math.round(y);
}

function drawTLInfluenceChart() {
    var container = document.getElementById('tl-influence-chart');
    if (!container) return;
    container.innerHTML = '';

    var bounds = container.getBoundingClientRect();
    var margin = { top: 28, right: 20, bottom: 48, left: 44 };
    var width  = Math.max(bounds.width || 800, 400) - margin.left - margin.right;
    var height = 320 - margin.top - margin.bottom;

    var svg = d3.select(container)
        .append('svg')
        .attr('width',  width  + margin.left + margin.right)
        .attr('height', height + margin.top  + margin.bottom);

    var g = svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var visibleFactions = TL_FACTIONS.filter(function(f) { return !tlHiddenFactions.has(f.id); });
    var keys = visibleFactions.map(function(f) { return f.id; });

    var yearMin = TL_INFLUENCE_DATA[0].year;
    var yearMax = TL_INFLUENCE_DATA[TL_INFLUENCE_DATA.length - 1].year;
    var x = d3.scaleLinear().domain([yearMin, yearMax]).range([0, width]);

    var stack = d3.stack().keys(keys).order(d3.stackOrderNone);
    if (tlCurrentView === 'stream')    stack.offset(d3.stackOffsetSilhouette);
    else if (tlCurrentView === 'expanded') stack.offset(d3.stackOffsetExpand);
    else stack.offset(d3.stackOffsetNone);

    var series = stack(TL_INFLUENCE_DATA);

    var yMin = 0, yMax;
    if (tlCurrentView === 'expanded') {
        yMax = 1;
    } else if (tlCurrentView === 'stream') {
        var allVals = series.reduce(function(acc, s) {
            s.forEach(function(d) { acc.push(d[0], d[1]); }); return acc;
        }, []);
        yMax = d3.max(allVals); yMin = d3.min(allVals);
    } else {
        yMax = d3.max(series, function(s) { return d3.max(s, function(d) { return d[1]; }); });
    }

    var y = d3.scaleLinear().domain([yMin, yMax]).range([height, 0]);

    // Era bands
    TL_ERAS.forEach(function(era) {
        var ex = x(Math.max(era.start, yearMin));
        var ew = x(Math.min(era.end, yearMax)) - ex;
        if (ew <= 0) return;
        g.append('rect').attr('x', ex).attr('y', 0)
            .attr('width', ew).attr('height', height)
            .attr('fill', era.shade).attr('opacity', 0.06);
        if (ew > 70) {
            g.append('text').attr('x', ex + ew / 2).attr('y', 12)
                .attr('text-anchor', 'middle').attr('font-size', '11px')
                .attr('fill', '#b8922ccc')
                .text(era.label.substring(0, 22));
        }
    });

    // Grid
    g.append('g').attr('class', 'tl-grid')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x).ticks(8).tickSize(-height).tickFormat(''));

    // Areas
    var area = d3.area()
        .x(function(d) { return x(d.data.year); })
        .y0(function(d) { return y(d[0]); })
        .y1(function(d) { return y(d[1]); })
        .curve(d3.curveBasis);

    var paths = g.selectAll('.tl-area-layer').data(series).join('path')
        .attr('class', 'tl-area-layer')
        .attr('d', area)
        .attr('fill', function(d, i) { return visibleFactions[i].color; })
        .attr('fill-opacity', 0.75)
        .attr('stroke', function(d, i) { return visibleFactions[i].color; })
        .attr('stroke-width', 0.5).attr('stroke-opacity', 0.4);

    // X axis
    var xAxis = g.append('g').attr('class', 'tl-axis')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x).ticks(7)
            .tickFormat(function(d) { return formatTLYear(d); }));
    xAxis.selectAll('text').attr('font-size', '11px').attr('fill', '#d4a843')
        .attr('font-family', 'Cinzel, serif');
    xAxis.select('.domain').attr('stroke', '#b8922c66');
    xAxis.selectAll('.tick line').attr('stroke', '#b8922c55');

    // Y axis
    if (tlCurrentView !== 'stream') {
        var yAxis = g.append('g').attr('class', 'tl-axis')
            .call(d3.axisLeft(y).ticks(4)
                .tickFormat(tlCurrentView === 'expanded' ? d3.format('.0%') : d3.format('d')));
        yAxis.selectAll('text').attr('font-size', '11px').attr('fill', '#d4a843');
        yAxis.select('.domain').attr('stroke', '#b8922c66');
        yAxis.selectAll('.tick line').attr('stroke', '#b8922c55');
    }

    // Tooltip
    var tooltip = document.getElementById('tl-chart-tooltip');
    var hoverLine = g.append('line')
        .attr('stroke', '#b8922c99').attr('stroke-width', 1)
        .attr('stroke-dasharray', '4,3')
        .attr('y1', 0).attr('y2', height).style('opacity', 0);

    g.append('rect').attr('width', width).attr('height', height)
        .attr('fill', 'transparent')
        .on('mousemove', function(event) {
            var mx = d3.pointer(event)[0];
            var year = Math.round(x.invert(mx));
            var clamped = Math.max(yearMin, Math.min(yearMax, year));
            hoverLine.attr('x1', x(clamped)).attr('x2', x(clamped)).style('opacity', 1);

            var bisect = d3.bisector(function(d) { return d.year; }).left;
            var idx = bisect(TL_INFLUENCE_DATA, clamped);
            var d0 = TL_INFLUENCE_DATA[Math.max(0, idx - 1)];
            var d1 = TL_INFLUENCE_DATA[Math.min(TL_INFLUENCE_DATA.length - 1, idx)];
            var interp = {};
            if (d0 && d1 && d0.year !== d1.year) {
                var t = (clamped - d0.year) / (d1.year - d0.year);
                keys.forEach(function(k) { interp[k] = (d0[k]||0) + t * ((d1[k]||0) - (d0[k]||0)); });
            } else {
                var dd = d0 || d1;
                keys.forEach(function(k) { interp[k] = dd ? (dd[k]||0) : 0; });
            }

            var sorted = visibleFactions.map(function(f) {
                return { id: f.id, name: f.name, color: f.color, val: interp[f.id] || 0 };
            }).filter(function(f) { return f.val > 0.5; })
              .sort(function(a, b) { return b.val - a.val; });

            var rows = sorted.map(function(f) {
                return '<div class="tl-tt-row"><span class="tl-tt-swatch" style="background:' +
                    f.color + '"></span><span>' + f.name + '</span></div>';
            }).join('');

            if (tooltip) {
                tooltip.innerHTML = '<div class="tl-tt-body"><div class="tl-tt-year">' + formatTLYear(clamped) + '</div>' + rows + '</div>';
                tooltip.classList.add('visible');
                var rect = tooltip.getBoundingClientRect();
                var tx = event.clientX + 16, ty = event.clientY - 10;
                if (tx + rect.width > window.innerWidth - 20) tx = event.clientX - rect.width - 16;
                if (ty + rect.height > window.innerHeight - 20) ty = event.clientY - rect.height - 10;
                tooltip.style.left = tx + 'px'; tooltip.style.top = ty + 'px';
            }

            paths.attr('fill-opacity', function(d, i) {
                return (interp[visibleFactions[i].id] || 0) > 0.5 ? 0.9 : 0.25;
            });
        })
        .on('mouseleave', function() {
            hoverLine.style('opacity', 0);
            if (tooltip) tooltip.classList.remove('visible');
            paths.attr('fill-opacity', 0.75);
        });

    drawTLLegend();
}

function drawTLLegend() {
    var el = document.getElementById('tl-influence-legend');
    if (!el) return;
    el.innerHTML = '';
    TL_FACTIONS.forEach(function(f) {
        var item = document.createElement('div');
        item.className = 'tl-legend-item' + (tlHiddenFactions.has(f.id) ? ' dimmed' : '');
        item.innerHTML = '<span class="tl-legend-swatch" style="background:' + f.color +
            '"></span><span>' + f.name + '</span>';
        item.addEventListener('click', function() {
            if (tlHiddenFactions.has(f.id)) tlHiddenFactions.delete(f.id);
            else tlHiddenFactions.add(f.id);
            drawTLInfluenceChart();
        });
        el.appendChild(item);
    });
}

document.querySelectorAll('.tl-chart-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.tl-chart-btn').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        tlCurrentView = btn.dataset.view;
        drawTLInfluenceChart();
    });
});

drawTLInfluenceChart();
"""
        '})();\n'
        '</script>\n'
    )

    return container_html + script_html


def render_stem_timeline_section(
    events: list,
    epoch_events: list,
    year_min: int,
    year_max: int,
) -> str:
    """Return HTML+script for the D3 stem-and-dot event timeline."""
    if not events:
        return ''

    # Build events JSON — use start_yr as the representative year
    stem_events = []
    for ev in events:
        if ev.get('is_era'):
            continue
        yr = round(ev['start_min'] / MINUTES_PER_YEAR, 1)
        slug = re.sub(r'[^a-z0-9]+', '-', ev['name'].lower()).strip('-')
        stem_events.append({
            'year':      yr,
            'title':     ev['name'],
            'type':      ev.get('category', 'political'),
            'desc':      ev.get('desc', ''),
            'slug':      slug,
            'color':     ev.get('color', '#b8922c'),
            'icon':      ev.get('_iconChar', '◆'),
            'dateRange': ev.get('_dateRange', ''),
        })

    if not stem_events:
        return ''

    events_json = json.dumps(stem_events)
    eras_ref = 'window._TL_ERAS || []'

    container_html = (
        '\n<div class="tl-d3-section tl-d3-section-alt" id="tl-stem">\n'
        '  <div class="tl-d3-inner">\n'
        '    <h2 class="tl-d3-heading">Timeline of Key Events</h2>\n'
        '    <div class="tl-filter-bar">\n'
        '      <button class="tl-filter-btn active" data-filter="all">All Events</button>\n'
        '      <button class="tl-filter-btn" data-filter="political">Political</button>\n'
        '      <button class="tl-filter-btn" data-filter="military">Military</button>\n'
        '      <button class="tl-filter-btn" data-filter="trade">Trade &amp; Diplomacy</button>\n'
        '      <button class="tl-filter-btn" data-filter="cosmological">Cosmological</button>\n'
        '    </div>\n'
        '    <div id="tl-stem-chart" class="tl-chart-container tl-stem-container"></div>\n'
        '  </div>\n'
        '</div>\n'
    )

    script_html = (
        '<script>\n'
        '(function() {\n'
        'var TL_EVENTS = ' + events_json + ';\n'
        'var tlCurrentFilter = "all";\n'
        """
var TYPE_COLORS = {
    political:    '#6ba3d6',
    military:     '#e06858',
    trade:        '#82bc5a',
    cosmological: '#d04878',
};

function formatTLYear2(y) {
    if (y < 0) return 'HJ ' + Math.abs(Math.round(y));
    return 'HB ' + Math.round(y);
}

function tlWrapText(text, maxChars) {
    var words = text.split(' '), lines = [], current = '';
    words.forEach(function(w) {
        if ((current + ' ' + w).trim().length > maxChars && current) {
            lines.push(current.trim()); current = w;
        } else { current = (current + ' ' + w).trim(); }
    });
    if (current) lines.push(current.trim());
    return lines;
}

function drawTLStemTimeline(filter) {
    var container = document.getElementById('tl-stem-chart');
    if (!container) return;
    container.innerHTML = '';

    var TL_ERAS = window._TL_ERAS || [];
    var filtered = filter === 'all' ? TL_EVENTS : TL_EVENTS.filter(function(e) { return e.type === filter; });
    if (filtered.length === 0) {
        container.innerHTML = '<p style="color:#b8922c;text-align:center;padding:40px 0;font-family:Cinzel,serif;font-size:0.85rem">No events for this filter.</p>';
        return;
    }

    var allYears = TL_EVENTS.map(function(e) { return e.year; });
    var dataMin = d3.min(allYears), dataMax = d3.max(allYears);
    var xMin = Math.min(dataMin, -500), xMax = Math.max(dataMax, 1200);

    var bounds = container.getBoundingClientRect();
    var margin = { top: 20, right: 40, bottom: 64, left: 40 };
    var minW = Math.max(bounds.width || 800, 600);
    var neededW = Math.max(minW, filtered.length * 72 + margin.left + margin.right);
    var width  = neededW - margin.left - margin.right;
    var height = 460;

    var svg = d3.select(container).append('svg')
        .attr('width',  neededW)
        .attr('height', height + margin.top + margin.bottom)
        .style('min-width', neededW + 'px');

    var g = svg.append('g')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

    var x = d3.scaleLinear().domain([xMin, xMax]).range([0, width]);

    // Era bands
    TL_ERAS.forEach(function(era) {
        var ex = x(Math.max(era.start, xMin));
        var ew = x(Math.min(era.end, xMax)) - ex;
        if (ew <= 0) return;
        g.append('rect').attr('x', ex).attr('y', 0)
            .attr('width', ew).attr('height', height)
            .attr('fill', era.shade).attr('opacity', 0.04);
        if (ew > 80) {
            g.append('text').attr('x', ex + ew / 2).attr('y', height + 46)
                .attr('text-anchor', 'middle').attr('font-size', '10px')
                .attr('font-family', 'Cinzel, serif').attr('fill', '#b8922cbb')
                .text(era.label.substring(0, 18));
        }
    });

    // Central axis
    var axisY = height * 0.5;
    g.append('line').attr('x1', 0).attr('x2', width)
        .attr('y1', axisY).attr('y2', axisY)
        .attr('stroke', '#b8922c77').attr('stroke-width', 1.5);

    // Tick marks
    var span = xMax - xMin;
    var tickStep = span > 1500 ? 200 : 100;
    var firstTick = Math.ceil(xMin / tickStep) * tickStep;
    for (var yr = firstTick; yr <= xMax; yr += tickStep) {
        g.append('line').attr('x1', x(yr)).attr('x2', x(yr))
            .attr('y1', axisY - 5).attr('y2', axisY + 5)
            .attr('stroke', '#b8922c88').attr('stroke-width', 1);
        g.append('text').attr('x', x(yr)).attr('y', axisY + 20)
            .attr('text-anchor', 'middle').attr('font-size', '10px')
            .attr('fill', '#d4a843').text(formatTLYear2(yr));
    }

    // Position events
    var sorted = filtered.slice().sort(function(a, b) { return a.year - b.year; });
    var laneIdx = 0;
    var lanes = [1, 2, 3];
    var positioned = sorted.map(function(evt, i) {
        var above = i % 2 === 0;
        var lane  = lanes[laneIdx % lanes.length];
        laneIdx++;
        return { year: evt.year, title: evt.title, type: evt.type, desc: evt.desc, above: above, lane: lane };
    });

    var tooltip = document.getElementById('tl-chart-tooltip');

    positioned.forEach(function(evt) {
        var cx = x(evt.year);
        var baseStem  = height * 0.13;
        var stemLen   = baseStem + evt.lane * baseStem * 0.6;
        var ey        = evt.above ? axisY - stemLen : axisY + stemLen;
        var color     = TYPE_COLORS[evt.type] || '#5b7fa5';

        g.append('line').attr('x1', cx).attr('x2', cx)
            .attr('y1', axisY).attr('y2', ey)
            .attr('stroke', color).attr('stroke-width', 1)
            .attr('stroke-opacity', 0.55).attr('stroke-dasharray', '3,2');

        g.append('circle').attr('cx', cx).attr('cy', axisY).attr('r', 5)
            .attr('fill', color).attr('stroke', '#0e0b06').attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('mouseover', function(event) {
                d3.select(this).attr('r', 8);
                var tl = evt.type.charAt(0).toUpperCase() + evt.type.slice(1);
                if (tooltip) {
                    tooltip.innerHTML =
                        '<div class="tl-tt-header" style="background:' + evt.color + '22;border-bottom:1px solid ' + evt.color + '44;padding:8px 10px 6px;">' +
                            '<span class="tl-tt-icon" style="color:' + evt.color + ';">' + evt.icon + '</span>' +
                            '<span class="tl-tt-title">' + evt.title + '</span>' +
                        '</div>' +
                        '<div class="tl-tt-body">' +
                            '<div class="tl-tt-year">' + evt.dateRange + '</div>' +
                            '<span class="tl-tt-type tl-cat-' + evt.type + '">' + tl + '</span>' +
                            '<div class="tl-tt-hint">click to view card ↓</div>' +
                        '</div>';
                    tooltip.classList.add('visible');
                    var rect = tooltip.getBoundingClientRect();
                    var tx = event.clientX + 16, ty = event.clientY - 10;
                    if (tx + rect.width > window.innerWidth - 20) tx = event.clientX - rect.width - 16;
                    if (ty + rect.height > window.innerHeight - 20) ty = event.clientY - rect.height - 10;
                    tooltip.style.left = tx + 'px'; tooltip.style.top = ty + 'px';
                }
            })
            .on('mouseleave', function() {
                d3.select(this).attr('r', 5);
                if (tooltip) tooltip.classList.remove('visible');
            })
            .on('click', function() {
                if (tooltip) tooltip.classList.remove('visible');
                var card = document.getElementById('tl-card-' + evt.slug);
                if (card) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    card.classList.add('tl-card-highlight');
                    setTimeout(function() { card.classList.remove('tl-card-highlight'); }, 1800);
                }
            });

        g.append('circle').attr('cx', cx).attr('cy', ey).attr('r', 2.5)
            .attr('fill', color).attr('fill-opacity', 0.5);

        var lines = tlWrapText(evt.title, 13);
        var lh = 11, totalH = lines.length * lh;
        lines.forEach(function(line, li) {
            var ty = evt.above
                ? ey - 6 - totalH + (li + 1) * lh
                : ey + 9 + li * lh;
            g.append('text').attr('x', cx).attr('y', ty)
                .attr('text-anchor', 'middle').attr('font-size', '11px')
                .attr('fill', '#e8d5a0').text(line);
        });
    });
}

document.querySelectorAll('.tl-filter-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.tl-filter-btn').forEach(function(b) { b.classList.remove('active'); });
        btn.classList.add('active');
        tlCurrentFilter = btn.dataset.filter;
        drawTLStemTimeline(tlCurrentFilter);
    });
});

window.addEventListener('resize', function() {
    clearTimeout(window._tlResizeTimer);
    window._tlResizeTimer = setTimeout(function() {
        if (typeof drawTLInfluenceChart === 'function') drawTLInfluenceChart();
        drawTLStemTimeline(tlCurrentFilter);
    }, 200);
});

drawTLStemTimeline('all');
"""
        '})();\n'
        '</script>\n'
    )

    return container_html + script_html


def render_timeline_html(fm: dict, body: str, folder: str | None = None) -> str:
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

    # --- D3 chart data extraction ---
    # Identify special sections for D3 visualizations
    epoch_events_d3: list[dict] = []
    declaration_events_d3: list[dict] = []
    stem_events_d3: list[dict] = []

    for lane_name, events in sections:
        ll = lane_name.lower()
        if ll == 'epochs':
            epoch_events_d3 = events
        elif 'declaration' in ll:
            declaration_events_d3.extend(events)
        elif ll not in ('epochs',):
            # Collect all non-epoch events for the stem timeline
            for ev in events:
                if not ev.get('is_era'):
                    stem_events_d3.append(ev)

    # Enrich stem events with display fields (era_defs available here, not in render fn)
    for ev in stem_events_d3:
        start_yr = ev['start_min'] / MINUTES_PER_YEAR
        end_yr   = ev['end_min'] / MINUTES_PER_YEAR if ev['end_min'] is not None else None
        start_lbl = _era_date_label(start_yr, era_defs)
        if end_yr is not None and end_yr != start_yr:
            ev['_dateRange'] = f"{start_lbl} → {_era_date_label(end_yr, era_defs)}"
        else:
            ev['_dateRange'] = start_lbl
        ev['_iconChar'] = _icon_char(ev.get('icon', ''))

    faction_groups = group_declarations_by_faction(declaration_events_d3)
    d3_year_min, d3_year_max = -500, 1199
    influence_data = derive_influence_data(faction_groups, d3_year_min, d3_year_max, step=25)

    # --- end D3 data extraction ---

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
        category    = entry.get('category', '').lower().strip()
        entry_class = 'is-era' if is_era else ''
        cat_badge   = (
            f'<span class="tl-cat-badge tl-cat-{category}">{category.title()}</span>'
            if category and not is_era else ''
        )

        # Image area: background-image if provided, else empty (shows color tint)
        # _resolve_image_url upgrades LK CDN URLs to local paths when available
        image_url = _resolve_image_url(entry.get('image', ''))
        img_style = (
            f'background-image:url({escape(image_url)});'
            f'background-size:cover;background-position:center;'
            if image_url else ''
        )

        # Slug for cross-linking from D3 stem dots
        slug = re.sub(r'[^a-z0-9]+', '-', entry['name'].lower()).strip('-')
        card_id_attr = f' id="tl-card-{slug}"' if not is_era else ''

        rows_html += f"""<div class="tl-list-entry {entry_class}"{card_id_attr}>
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
      <span class="tl-card-badge">{escape(entry['lane'])}{cat_badge}</span>
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

    # Build D3 visualization sections
    d3_power_html  = render_power_chart_section(faction_groups, influence_data, epoch_events_d3, d3_year_min, d3_year_max)
    d3_stem_html   = render_stem_timeline_section(stem_events_d3, epoch_events_d3, d3_year_min, d3_year_max)

    # Tooltip element (shared by both D3 charts)
    tooltip_html = '<div id="tl-chart-tooltip" class="tl-chart-tooltip"></div>\n'

    content_html = (
        d3_power_html
        + d3_stem_html
        + tooltip_html
        + f'<div class="tl-list-wrap">\n{rows_html}\n</div>\n'
    )

    back_nav_html = ''
    if folder:
        cat_label = folder.replace('-', ' ').replace('_', ' ').title()
        back_href = f'../category-{escape(folder)}.html'
        back_nav_html = (
            f'<div class="back-nav">'
            f'<a href="{back_href}">&larr; {escape(cat_label)}</a>'
            f'</div>\n'
        )

    return _html_wrapper(
        title=title,
        css=CSS_BASE + CSS_TIMELINE,
        header_html=header_html,
        banner_html=banner_html,
        content_html=content_html,
        extra_head='<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>\n',
        back_nav_html=back_nav_html,
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
    extra_head: str = '',
    back_nav_html: str = '',
    jump_nav_html: str = '',
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)} &mdash; Tarim-Shaiel</title>
  <link rel="icon" href="{FAVICON}">
  <!-- AUTO-GENERATED by utilities/world/generate_world_html.py — do not hand-edit -->
  {extra_head}<style>{css}  </style>
</head>
<body>

{jump_nav_html}<div class="page-wrap">

{back_nav_html}{header_html}
{banner_html}

  <div class="content">
{content_html}
  </div>

  <div class="credits">Tarim-Shaiel &middot; Daggerheart Campaign &middot; 2026</div>

</div>

<script>
(function () {{
  var a = document.querySelector('.back-nav a');
  if (!a) return;
  a.addEventListener('click', function (e) {{
    e.preventDefault();
    if (history.length > 1 && document.referrer &&
        document.referrer.indexOf(location.hostname) !== -1) {{
      history.back();
    }} else {{
      location.replace(a.href);
    }}
  }});
}})();
</script>
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
