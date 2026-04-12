#!/usr/bin/env python3
"""
Batch HTML Generator & Index Builder
======================================
Discovers all pipeline source files (type: timeline | myth | lore) in the
vault, generates HTML for each, then writes docs/index.html.

Called by both netlify.toml and GitHub Actions after the campaign-frame and
dashboard generators have run.

Usage:
    python generate_all_world_html.py
    python generate_all_world_html.py --vault /path/to/vault
    python generate_all_world_html.py --dry-run
    python generate_all_world_html.py --public   # Netlify/CI: only visibility: public docs

Visibility gating (--public, fails closed):
    Only documents with EXPLICIT 'visibility: public' in frontmatter are generated
    and listed in the index.  Missing, gm_secrets, or any other value → skipped.
    Documents without a visibility tag default to 'gm_secrets' in metadata (safe side).
"""

import re
import sys
import argparse
from pathlib import Path
from html import escape

# ── import sibling generator ──────────────────────────────────────────────────
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from generate_world_html import render_timeline_html, build_myth_html

sys.path.insert(0, str(HERE.parent))   # makes utilities/shared importable
from shared.assets import prepare_image
from shared.frontmatter import parse_frontmatter
from shared.html_render import render_wiki_embed, inline_md as shared_inline_md

# ── discovery config ──────────────────────────────────────────────────────────
PIPELINE_TYPES = {'timeline', 'myth', 'lore'}

# Directories to search (relative to vault root)
SCAN_ROOTS = ['world', 'narrative']

# Directory names that are never pipeline sources
SKIP_DIRS = {'archive', 'references', 'utilities', '.git', 'docs', 'templates'}

# File-name prefixes that are skipped (templates, test fixtures)
SKIP_PREFIXES = ('_',)

CATEGORY_DISPLAY_NAMES: dict[str, str] = {
    'world':      'World',
    'narrative':  'Narrative',
    'gm_secrets': 'GM Secrets',
}

CATEGORY_DESCRIPTIONS: dict[str, str] = {
    'world':      'Geography, history, factions, and peoples.',
    'narrative':  'Session write-ups, fiction, and campaign prose.',
    'gm_secrets': 'GM-only reference material.',
}


def _category_label(folder: str) -> str:
    return CATEGORY_DISPLAY_NAMES.get(folder, folder.replace('_', ' ').title())


# ── category config helpers ───────────────────────────────────────────────────

def _find_folder_path(vault: Path, folder: str) -> Path | None:
    """Return the filesystem path of a named folder under any SCAN_ROOT."""
    for root_name in SCAN_ROOTS:
        p = vault / root_name / folder
        if p.is_dir():
            return p
    p = vault / folder
    return p if p.is_dir() else None


def _read_category_config(vault: Path, folder: str) -> tuple[dict, str]:
    """Read optional _category.md config for a folder. Returns (frontmatter dict, body content)."""  
    folder_path = _find_folder_path(vault, folder)
    if folder_path is None:
        return {}, ''
    cfg_file = folder_path / '_category.md'
    if not cfg_file.exists():
        return {}, ''
    try:
        raw = cfg_file.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(raw)
        return fm, body
    except Exception:
        return {}, ''


def inline_md(text: str) -> str:
    """Convert inline markdown to HTML (after HTML-escaping)."""
    text = escape(text)
    text = re.sub(r'\*{3}(.+?)\*{3}', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text


def render_category_body(body: str, vault: Path, docs: Path) -> tuple[str, list[dict]]:
    """Render category body Markdown as HTML. Returns (html, jump_nav_items).
    
    Supports:
    - Images: ![[image.png|caption]] → <figure class="lore-figure">
    - Feature boxes: **Feature Name:** description → <div class="feature-box">
    - Headers: ## and ### with auto-generated anchors for jump nav
    - Lists, callouts, bold/italic
    
    Args:
        body: Markdown content
        vault: Vault root path for image resolution
        docs: Docs output path for image copying
        
    Returns:
        (html_string, [{text, anchor}]) where jump_nav_items are H2/H3 headers
    """
    if not body.strip():
        return '', []
    
    # Strip frontmatter if present
    body = re.sub(r'^---\n.*?\n---\n', '', body, flags=re.DOTALL)
    # Strip Obsidian comments
    body = re.sub(r'%%.*?%%', '', body, flags=re.DOTALL)
    # Strip wikilinks (but NOT image embeds which start with !)
    body = re.sub(r'(?<!!)\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', body)
    body = re.sub(r'(?<!!)\[\[([^\]]+)\]\]', r'\1', body)
    # Strip callout markers
    body = re.sub(r'^>\s*\[!\w+\]\s*$', '', body, flags=re.MULTILINE)
    # Normalize blank lines
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = body.strip()
    
    if not body:
        return '', []
    
    html_parts = []
    jump_nav_items = []
    paragraphs = [p.strip() for p in re.split(r'\n\n+', body) if p.strip()]
    
    feature_buffer = []  # Accumulate feature boxes
    
    def _slug(text: str) -> str:
        return re.sub(r'[^\w\-]+', '-', text.lower()).strip('-')
    
    def _flush_features():
        """Output accumulated feature boxes as a grid."""
        nonlocal feature_buffer
        if not feature_buffer:
            return
        html_parts.append('<div class=\"feature-grid\">\n')
        for name, flavor in feature_buffer:
            html_parts.append(f'  <div class=\"feature-box\">\n')
            html_parts.append(f'    <div class=\"feature-name\">{escape(name)}</div>\n')
            html_parts.append(f'    <p>{inline_md(flavor)}</p>\n')
            html_parts.append(f'  </div>\n')
        html_parts.append('</div>\n')
        feature_buffer = []
    
    for para in paragraphs:
        # Try wiki embed first (handles ![[file|caption|width]] automatically)
        wiki_html = render_wiki_embed(para)
        if wiki_html:
            _flush_features()  # Features can't span images
            html_parts.append(wiki_html)
            continue
        
        # Try standalone markdown image: ![alt](path)
        md_img_match = re.match(r'^!\[([^\]]*)\]\(([^\)]+)\)$', para)
        if md_img_match:
            alt = escape(md_img_match.group(1))
            src = escape(md_img_match.group(2))
            _flush_features()  # Features can't span images
            html_parts.append(f'    <figure class=\"lore-figure\">\n')
            html_parts.append(f'      <img src=\"{src}\" alt=\"{alt}\" />\n')
            html_parts.append(f'      <figcaption>{alt}</figcaption>\n')
            html_parts.append(f'    </figure>\n')
            continue
        
        # Feature boxes: **Feature Name:** description
        feat_match = re.match(r'^\*\*(.+?):\*\*\s*(.+)', para, re.DOTALL)
        if feat_match:
            feature_buffer.append((feat_match.group(1).strip(), feat_match.group(2).strip()))
            continue
        
        # Flush features if we hit non-feature content
        _flush_features()
        
        # Headers with jump nav anchors
        if para.startswith('## '):
            header_text = para[3:].strip()
            anchor = _slug(header_text)
            jump_nav_items.append({'text': header_text, 'anchor': anchor, 'level': 2})
            html_parts.append(f'<h2 id=\"{anchor}\">{inline_md(header_text)}</h2>\n')
        elif para.startswith('### '):
            header_text = para[4:].strip()
            anchor = _slug(header_text)
            jump_nav_items.append({'text': header_text, 'anchor': anchor, 'level': 3})
            html_parts.append(f'<h3 id=\"{anchor}\">{inline_md(header_text)}</h3>\n')
        # Callouts
        elif para.startswith('> ') or para.startswith('>'):
            inner = re.sub(r'^>\s*', '', para, flags=re.MULTILINE).strip()
            html_parts.append(f'<div class=\"callout\">{inline_md(inner)}</div>\n')
        # Lists (check if any line starts with - or *)
        elif any(re.match(r'^[-*]\s+', line.strip()) for line in para.splitlines()):
            list_items = []
            prefix_para = []
            for line in para.splitlines():
                line_stripped = line.strip()
                if re.match(r'^[-*]\s+', line_stripped):
                    item_text = re.sub(r'^[-*]\s+', '', line_stripped)
                    list_items.append(f'  <li>{inline_md(item_text)}</li>\n')
                elif line_stripped and not list_items:
                    # Text before the list starts (like "Consider:")
                    prefix_para.append(line_stripped)
            if prefix_para:
                html_parts.append(f'<p>{inline_md(" ".join(prefix_para))}</p>\n')
            if list_items:
                html_parts.append('<ul>\n' + ''.join(list_items) + '</ul>\n')
        # Regular paragraphs
        else:
            html_parts.append(f'<p>{inline_md(para)}</p>\n')
    
    # Flush any remaining features
    _flush_features()
    
    return ''.join(html_parts), jump_nav_items


def _extract_concept(body: str) -> str:
    m = re.search(r'(?ms)^##\s*Concept\s*$\n(.*?)(?:\n^##\s+|\Z)', body)
    if not m:
        return ''
    for line in m.group(1).splitlines():
        line = line.strip()
        if re.match(r'^[_*].+[_*]$', line):
            return re.sub(r'^[_*]+(.+?)[_*]+$', r'\1', line).strip()
    return ''


def _read_site_config(vault: Path) -> dict:
    cfg_file = vault / 'templates' / 'tarim-shaiel-campaign-frame-v2.md'
    if not cfg_file.exists():
        return {}
    raw = cfg_file.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(raw)
    if 'concept' not in fm:
        fm['concept'] = _extract_concept(body)
    return fm


def _hero_html(config: dict, vault: Path, docs: Path) -> str:
    banner = str(config.get('banner', '')).strip()
    image_style = ''
    if banner:
        if re.match(r'^(https?:|data:)', banner):
            url = banner
        else:
            url = prepare_image(banner, vault, docs)
            if not url:
                url = banner
        banner_x = config.get('banner-x') or config.get('banner_x') or '50'
        banner_y = config.get('banner-y') or config.get('banner_y') or '4'
        image_style = f' style="background-image: url({url}); background-position: center {escape(str(banner_y))}%;"'

    title = config.get('title', 'Tarim Shaiel')
    subtitle = config.get('subtitle', '')
    concept = config.get('concept', '')

    subtitle_html = f'      <div class="cover-subtitle">{escape(subtitle)}</div>\n' if subtitle else ''
    if concept and not subtitle:
        subtitle_html = f'      <div class="cover-subtitle">{escape(concept)}</div>\n'

    return (
        f'  <div class="cover">\n'
        f'    <div class="cover-image"{image_style}></div>\n'
        f'    <div class="cover-gradient"></div>\n'
        f'    <div class="cover-content">\n'
        f'      <div class="cover-title">{escape(title)}</div>\n'
        f'{subtitle_html}'
        f'    </div>\n'
        f'  </div>\n'
    )


def _category_section_html(folder: str, folder_docs: list[dict], vault: Path, public_only: bool) -> str:
    cfg, _ = _read_category_config(vault, folder)  # body not needed for inline preview
    label = cfg.get('title') or _category_label(folder)
    desc = cfg.get('description') or CATEGORY_DESCRIPTIONS.get(folder, '')
    count = len(folder_docs)
    has_gm = any(d['visibility'] == 'gm_secrets' for d in folder_docs)
    plural = 's' if count != 1 else ''
    meta = f'{count} document{plural}' + (' · includes GM content' if has_gm else '')
    sorted_docs = sorted(folder_docs, key=lambda d: d['title'].lower())
    inline_docs = sorted_docs[:6]
    remainder = max(0, count - len(inline_docs))

    items_html = ''
    for d in inline_docs:
        badge = ' <span class="gm-badge">GM</span>' if d['visibility'] == 'gm_secrets' else ''
        extra = ' gm-secrets' if d['visibility'] == 'gm_secrets' else ''
        items_html += (
            f'      <a class="inline-doc-item{extra}" href="{escape(d['filename'])}">{escape(d['title'])}{badge}</a>\n'
        )

    remainder_html = ''
    if remainder:
        remainder_html = f'      <div class="inline-doc-more">+ {remainder} more</div>\n'

    desc_html = f'    <div class="cat-section-desc">{escape(desc)}</div>\n' if desc else ''

    return (
        '    <div class="cat-section">\n'
        '      <div class="cat-section-header">\n'
        '        <div>\n'
        f'          <div class="cat-section-title">{escape(label)}</div>\n'
        f'          <div class="cat-section-meta">{escape(meta)}</div>\n'
        '        </div>\n'
        f'        <a class="see-all" href="category-{escape(folder)}.html">See all →</a>\n'
        '      </div>\n'
        f'{desc_html}'
        '      <div class="inline-doc-list">\n'
        f'{items_html}'
        f'{remainder_html}'
        '      </div>\n'
        '    </div>\n'
    )


# ── discovery ─────────────────────────────────────────────────────────────────

def _should_skip(path: Path, vault: Path) -> bool:
    rel_parts = path.relative_to(vault).parts
    if any(p in SKIP_DIRS for p in rel_parts):
        return True
    if path.name.startswith(SKIP_PREFIXES):
        return True
    return False


def discover_sources(vault: Path) -> dict[str, list[Path]]:
    """Return all .md files under SCAN_ROOTS bucketed by parent folder name."""
    buckets: dict[str, list[Path]] = {}
    for root_name in SCAN_ROOTS:
        root = vault / root_name
        if not root.exists():
            continue
        for md in sorted(root.rglob('*.md')):
            if _should_skip(md, vault):
                continue
            try:
                head = md.read_text(encoding='utf-8')[:600]
            except Exception:
                continue
            m = re.search(r'^type:\s*(\w+)', head, re.MULTILINE)
            if m and m.group(1).lower() in PIPELINE_TYPES:
                # TODO: section: frontmatter override — folder = fm.get('section') or src.parent.name
                folder = md.parent.name
                buckets.setdefault(folder, []).append(md)
    # Apply _category.md suppression
    suppressed = [f for f in list(buckets.keys())
                  if _read_category_config(vault, f)[0].get('published') is False]
    for folder in suppressed:
        print(f'  SUPPRESS  category "{folder}" (published: false in _category.md)')
        del buckets[folder]
    return buckets


def _slug(src: Path) -> str:
    s = re.sub(r'[^\w\-]', '-', src.stem.lower().replace(' ', '-'))
    return re.sub(r'-+', '-', s).strip('-')


# ── generation ────────────────────────────────────────────────────────────────

def generate_all(
    vault: Path, docs: Path,
    dry_run: bool = False,
    public_only: bool = False,
    grouped_sources: dict[str, list[Path]] | None = None,
) -> dict[str, list[dict]]:
    """Generate HTML for every discovered source. Returns docs grouped by folder.

    Args:
        public_only: When True, only generate docs explicitly tagged
                     visibility: public (fails closed — missing/other → skipped).
        grouped_sources: Pre-computed discover_sources() result. If None, calls
                         discover_sources() internally (preserves backward compat).
    """
    if grouped_sources is None:
        grouped_sources = discover_sources(vault)

    grouped: dict[str, list[dict]] = {}

    for folder, sources in grouped_sources.items():
        for src in sources:
            raw = src.read_text(encoding='utf-8')
            fm, body = parse_frontmatter(raw)
            doc_type = fm.get('type', '').lower()
            if doc_type not in PIPELINE_TYPES:
                continue

            # Visibility gate (fails closed): require explicit visibility: public.
            # Default is 'gm_secrets' — untagged docs are treated as GM-only.
            visibility = fm.get('visibility', 'gm_secrets')
            if public_only and visibility != 'public':
                rel = src.relative_to(vault)
                print(f'  SKIP     {rel}  (not visibility: public)')
                continue

            slug     = _slug(src)
            out_path = docs / f'{slug}.html'
            rel      = src.relative_to(vault)

            print(f'  {doc_type:8}  {rel}  →  docs/{slug}.html')

            if not dry_run:
                if doc_type == 'timeline':
                    html = render_timeline_html(fm, body)
                else:
                    html = build_myth_html(fm, body)
                docs.mkdir(parents=True, exist_ok=True)
                out_path.write_text(html, encoding='utf-8')

            grouped.setdefault(folder, []).append({
                'title':       fm.get('title') or slug.replace('-', ' ').title(),
                'type':        doc_type,
                'visibility':  visibility,   # 'gm_secrets' if untagged (safe default)
                'calendar':    fm.get('calendar', ''),
                'description': fm.get('description', ''),
                'filename':    f'{slug}.html',
            })

    return grouped


# ── index generator ───────────────────────────────────────────────────────────

_FAVICON = (
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='10' fill='%231a1208'/>"
    "<polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 "
    "81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 33.4,43.1 "
    "18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>"
)

_INDEX_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inconsolata:wght@400;500&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --ink: #1a1208; --parchment: #f5edd8; --parchment2: #ede0c4;
      --gold: #b8922c; --gold-light: #d4a843; --crimson: #7a1f1f;
      --steel: #3c4a5a; --rule: rgba(184,146,44,0.4); --shadow: rgba(26,18,8,0.15);
    }
    html { scroll-behavior: smooth; }
    body {
      background: #1a1208;
      background-image: url('images/paper-texture-top-view-2.jpg');
      font-family: 'EB Garamond', Georgia, serif;
      font-size: 17px; line-height: 1.72; color: var(--ink);
    }
    .page-wrap {
      max-width: 860px; margin: 0 auto;
      background: var(--parchment);
      box-shadow: 0 0 80px rgba(0,0,0,0.75);
      position: relative; overflow: hidden;
    }
    .page-wrap::before {
      content: '';
      position: absolute; inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
      pointer-events: none; z-index: 0; opacity: 0.45;
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
    .cover {
      position: relative; min-height: 280px;
      display: flex; flex-direction: column; justify-content: flex-end;
      overflow: hidden;
    }
    .cover-image {
      position: absolute; inset: 0;
      background-size: cover;
      background-position: center;
      z-index: 0;
    }
    .cover-gradient {
      position: absolute; inset: 0;
      background: linear-gradient(to bottom, rgba(26,18,8,0.08) 0%, rgba(26,18,8,0.55) 55%, rgba(26,18,8,0.92) 100%);
      z-index: 1;
    }
    .cover-content {
      position: relative; z-index: 2;
      padding: 2.5rem 3rem 3rem;
      color: var(--parchment);
    }
    .cover-title {
      font-family: 'Cinzel', serif;
      font-size: 2.8rem; font-weight: 700;
      letter-spacing: 0.06em; line-height: 1.1;
      color: #f5e6c0;
      text-shadow: 0 2px 12px rgba(0,0,0,0.7);
      margin-bottom: 0.15rem;
    }
    .cover-subtitle {
      font-family: 'Cinzel', serif;
      font-size: 1rem; font-weight: 400;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--gold-light);
    }
    .banner {
      background: var(--steel);
      color: var(--parchment);
      display: flex; align-items: center; justify-content: space-between;
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
    .content {
      position: relative; z-index: 1;
      padding: 0 3rem 3.5rem;
    }
    .content h2 {
      font-family: 'Cinzel', serif;
      font-size: 1.45rem; font-weight: 600;
      color: var(--crimson);
      letter-spacing: 0.04em;
      margin: 2.4rem 0 0.8rem;
      padding-bottom: 0.4rem;
      border-bottom: 2px solid var(--rule);
    }
    .content h2:first-child { margin-top: 2.8rem; }
    .content h3 {
      font-family: 'Cinzel', serif;
      font-size: 1.1rem; font-weight: 600;
      color: var(--steel);
      letter-spacing: 0.04em;
      margin: 1.8rem 0 0.6rem;
    }
    .content p {
      margin-bottom: 1em;
      line-height: 1.72;
    }
    .content p:last-child { margin-bottom: 0; }
    .content ul {
      margin: 0.8em 0;
      padding-left: 2em;
    }
    .content li {
      margin-bottom: 0.4em;
      line-height: 1.6;
    }
    .content .callout {
      background: var(--parchment2);
      border-left: 3px solid var(--gold);
      border-radius: 2px;
      padding: 0.9rem 1.1rem;
      margin: 1.1rem 0;
      font-size: 0.97rem;
    }
    .content .callout strong { color: var(--steel); }
    .jump-nav {
      display: flex; flex-wrap: wrap;
      gap: 0.3rem 1.1rem;
      padding: 1.1rem 0 1.4rem;
      border-bottom: 1px solid var(--rule);
      margin-bottom: 2.8rem;
      font-family: 'Cinzel', serif;
      font-size: 0.7rem;
      letter-spacing: 0.13em;
      text-transform: uppercase;
    }
    .jump-nav a {
      color: var(--gold);
      text-decoration: none;
      transition: color 0.15s;
    }
    .jump-nav a:hover { color: var(--gold-light); }
    .feature-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.9rem;
      margin-top: 1.3rem;
    }
    .feature-box {
      background: var(--parchment2);
      border: 1px solid var(--rule);
      border-radius: 2px;
      padding: 0.95rem 1.1rem 1rem;
      box-shadow: inset 0 1px 4px rgba(26,18,8,0.06);
    }
    .feature-name {
      font-family: 'Cinzel', serif;
      font-size: 0.76rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--steel);
      margin-bottom: 0.45rem;
    }
    .feature-box p {
      margin: 0;
      font-size: 0.97rem;
      line-height: 1.6;
    }
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
      border-radius: 1rem;
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
    .section-label {
      font-family: 'Inconsolata', monospace; font-size: 12px;
      letter-spacing: 0.2em; text-transform: uppercase;
      color: var(--gold); margin: 2.2rem 0 1.2rem;
    }
    .doc-card {
      border: 1px solid var(--rule); border-radius: 3px; padding: 24px 28px;
      margin-bottom: 16px; text-decoration: none; display: block;
      transition: border-color 0.2s, background 0.2s;
      background: var(--parchment); position: relative;
    }
    .doc-card:hover { border-color: var(--gold); background: var(--parchment2); }
    .doc-card-arrow {
      position: absolute; right: 24px; top: 50%; transform: translateY(-50%);
      color: var(--gold); font-size: 20px; opacity: 0.5;
      transition: opacity 0.2s, right 0.2s;
    }
    .doc-card:hover .doc-card-arrow { opacity: 1; right: 20px; }
    .doc-title {
      font-family: 'Cinzel', serif; font-size: 1.1rem; font-weight: 600;
      color: var(--crimson); margin-bottom: 5px;
    }
    .doc-meta {
      font-family: 'Inconsolata', monospace; font-size: 12px;
      color: rgba(26,18,8,0.45); letter-spacing: 0.1em;
      text-transform: uppercase; margin-bottom: 8px;
    }
    .doc-desc { font-size: 15px; color: rgba(26,18,8,0.65); font-style: italic; }
    .gm-badge {
      background: #7a1f1f; color: #f5edd8; font-size: 10px;
      letter-spacing: 0.15em; text-transform: uppercase;
      padding: 2px 7px; border-radius: 100px; margin-left: 8px;
      font-family: 'Inconsolata', monospace; vertical-align: middle;
    }
    .doc-card.gm-secrets {
      background: rgba(122,31,31,0.04);
      border-color: rgba(122,31,31,0.25);
    }
    .doc-card.gm-secrets:hover {
      background: rgba(122,31,31,0.08);
      border-color: var(--crimson);
    }
    .cat-section {
      margin-top: 2.8rem;
      padding: 28px 26px 22px;
      border: 1px solid var(--rule);
      border-radius: 4px;
      background: rgba(245,237,216,0.95);
    }
    .cat-section-header {
      display: flex; align-items: flex-start; justify-content: space-between;
      gap: 1rem; margin-bottom: 14px;
    }
    .cat-section-title {
      font-family: 'Cinzel', serif; font-size: 1.15rem; font-weight: 600;
      color: var(--ink); margin-bottom: 4px;
    }
    .cat-section-meta {
      font-family: 'Inconsolata', monospace; font-size: 11px;
      color: rgba(26,18,8,0.6); text-transform: uppercase; letter-spacing: 0.14em;
    }
    .cat-section-desc {
      font-size: 0.95rem; color: rgba(26,18,8,0.75); margin-bottom: 16px;
    }
    .see-all {
      font-family: 'Cinzel', serif; font-size: 0.95rem;
      color: var(--gold); text-decoration: none; white-space: nowrap;
    }
    .see-all:hover { text-decoration: underline; }
    .inline-doc-list {
      display: flex; flex-wrap: wrap; gap: 10px 12px;
    }
    .inline-doc-item {
      display: inline-flex; align-items: center;
      padding: 10px 14px; border-radius: 999px;
      background: rgba(26,18,8,0.08); color: var(--ink);
      text-decoration: none; font-size: 0.95rem;
      transition: background 0.2s, border-color 0.2s;
      border: 1px solid transparent;
    }
    .inline-doc-item:hover { background: rgba(26,18,8,0.12); }
    .inline-doc-item.gm-secrets {
      border-color: rgba(122,31,31,0.25);
      background: rgba(122,31,31,0.06);
    }
    .inline-doc-more {
      align-self: center; font-family: 'Inconsolata', monospace;
      font-size: 0.9rem; color: rgba(26,18,8,0.6);
      padding: 10px 14px; border-radius: 999px;
      background: rgba(26,18,8,0.04);
    }
    .footer {
      background: #1a1208;
      padding: 1.6rem 3rem;
      border-top: 1px solid rgba(184,146,44,0.3);
    }
    .footer-text {
      font-family: 'Inconsolata', monospace; font-size: 11px;
      color: rgba(245,237,216,0.3); letter-spacing: 0.1em;
    }
    @media (max-width: 640px) {
      .cover-title { font-size: 2.2rem; }
      .cover-content, .content { padding: 1.8rem 1.4rem; }
      .banner { padding: 0.5rem 1.4rem; }
      .banner-rule { margin: 0 1.4rem; }
      .footer { padding: 1.6rem 1.4rem; }
    }
"""


def _card_html(filename: str, title: str, meta: str, desc: str, gm: bool = False) -> str:
    gm_badge = '<span class="gm-badge">GM</span>' if gm else ''
    extra    = ' gm-secrets' if gm else ''
    return (
        f'    <a class="doc-card{extra}" href="{escape(filename)}">\n'
        f'      <div class="doc-title">{escape(title)}{gm_badge}</div>\n'
        f'      <div class="doc-meta">{escape(meta)}</div>\n'
        f'      <div class="doc-desc">{escape(desc)}</div>\n'
        f'      <div class="doc-card-arrow">&#8594;</div>\n'
        f'    </a>\n'
    )


def _meta_line(doc: dict) -> str:
    parts = [doc['type'].capitalize()]
    if doc['calendar']:
        parts.append(doc['calendar'])
    if doc['visibility'] == 'gm_secrets':
        parts.append('GM Only')
    return ' · '.join(parts)


def _auto_desc(doc: dict) -> str:
    if doc['description']:
        return doc['description']
    if doc['type'] == 'timeline':
        cal = doc['calendar']
        return f"World timeline{' · ' + cal if cal else ''}."
    if doc['type'] == 'myth':
        return 'Myth or fable from the world of Tarim-Shaiel.'
    return 'World lore document.'


# Core docs are always present — generated by separate scripts
_CORE_DOCS = [
    {
        'filename': 'the-roads.html',
        'title':    'The Roads',
        'meta':     'World Lore · Public',
        'desc':     "The roads were here before the empire. A lore piece on the world's ancient trade routes and the silence that has returned to them.",
    },
    {
        'filename': 'campaign-frame.html',
        'title':    'Campaign Frame',
        'meta':     'Player-Facing · v2.0 · Daggerheart',
        'desc':     'The pitch, themes, principles, and session zero questions. Everything your players need before character creation.',
    },
    {
        'filename': 'nianhao-the-divine-arc.html',
        'title':    'Campaign Timeline',
        'meta':     'Player-Facing · v2.0 · Daggerheart',
        'desc':     'The chronicle of the world timeline. Major Epochs and Events are documented here.',
    },
    {
        'filename': 'peoples-of-tarim-shaiel.html',
        'title':    'Peoples of Tarim-Shaiel',
        'meta':     'Player-Facing · Ancestry Guide · Daggerheart',
        'desc':     'Fourteen ancestries of the known world — lore descriptions and in-world feature summaries for character creation.',
    },
]


def generate_category_page(docs: Path, vault: Path, folder: str, folder_docs: list[dict]) -> int:
    """Write docs/category-{folder}.html. Returns count of docs rendered."""
    cfg, body = _read_category_config(vault, folder)
    label = cfg.get('title') or _category_label(folder)
    desc  = cfg.get('description') or CATEGORY_DESCRIPTIONS.get(folder, '')
    
    # Render body content as HTML with jump nav support
    body_html, jump_nav_items = render_category_body(body, vault, docs)
    
    # Generate jump nav if enabled in frontmatter
    jump_nav_html = ''
    if cfg.get('jump_nav') and jump_nav_items:
        nav_links = []
        for item in jump_nav_items:
            indent = '  ' if item['level'] == 3 else ''
            nav_links.append(f'{indent}<a href=\"#{item["anchor"]}\">{escape(item["text"])}</a>')
        jump_nav_html = '<div class=\"jump-nav\">\n  ' + '\n  '.join(nav_links) + '\n</div>\n'

    # Cover image (optional)
    cover_style = ''
    cover_file  = cfg.get('hero_image') or cfg.get('hero') or cfg.get('cover_image')
    if cover_file:
        url = prepare_image(cover_file, vault, docs)
        if url:
            cover_x = cfg.get('cover-x') or cfg.get('cover_x') or '50'
            cover_y = cfg.get('cover-y') or cfg.get('cover_y') or '4'
            cover_style = f' style="background-image: url({url}); background-position: center {escape(str(cover_y))}%;"'

    sorted_docs = sorted(folder_docs, key=lambda d: d['title'].lower())
    cards_html  = ''.join(
        _card_html(
            d['filename'], d['title'], _meta_line(d), _auto_desc(d),
            gm=(d['visibility'] == 'gm_secrets'),
        )
        for d in sorted_docs
    )
    count = len(sorted_docs)

    # Back navigation
    back_nav_html = (
        '<div class="back-nav">\n'
        '  <a href="index.html">← Campaign Documents</a>\n'
        '</div>\n'
    )

    # Cover section
    cover_html = (
        '<div class="cover">\n'
        f'  <div class="cover-image"{cover_style}></div>\n'
        '  <div class="cover-gradient"></div>\n'
        '  <div class="cover-content">\n'
        f'    <div class="cover-title">{escape(label)}</div>\n'
        f'    <div class="cover-subtitle">{escape(desc)}</div>\n'
        '  </div>\n'
        '</div>\n'
    )

    # Banner
    banner_left = cfg.get('banner_left') or 'Category Index'
    banner_right = cfg.get('banner_right') or f'{escape(label)} · Tarim-Shaiel'
    banner_html = (
        '<div class="banner">\n'
        f'<span>{escape(banner_left)}</span>\n'
        f'<span>{banner_right}</span>\n'
        '</div>\n'
        '<div class="banner-rule"></div>\n'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(label)} - Tarim-Shaiel</title>
  <!-- AUTO-GENERATED by utilities/world/generate_all_world_html.py - do not hand-edit -->
  <link rel="icon" href="{_FAVICON}">
  <style>{_INDEX_CSS}  </style>
</head>
<body>

<div class="page-wrap">

{back_nav_html}
{cover_html}
{banner_html}

  <div class="content">
{jump_nav_html}{body_html}
    <div class="section-label">{escape(label)} ({count})</div>
{cards_html}
  </div>

  <div class="footer">
    <div class="footer-text">AUTO-GENERATED - DO NOT HAND-EDIT - {count} DOCUMENTS - SOURCE: GITHUB MAIN BRANCH</div>
  </div>

</div>
</body>
</html>
"""
    (docs / f'category-{folder}.html').write_text(html, encoding='utf-8')
    return count


def generate_index(docs: Path, grouped_docs: dict[str, list[dict]], vault: Path | None = None, public_only: bool = False) -> None:
    """Write docs/index.html listing core docs with hero and category sections."""
    config = _read_site_config(vault) if vault else {}
    hero_html = _hero_html(config, vault, docs) if config else ''

    # Banner for index page
    banner_html = (
        '<div class="banner">\n'
        '<span>Campaign Documents</span>\n'
        '<span>Tarim-Shaiel · Daggerheart</span>\n'
        '</div>\n'
        '<div class="banner-rule"></div>\n'
    )

    core_html = ''.join(
        _card_html(d['filename'], d['title'], d['meta'], d['desc'])
        for d in _CORE_DOCS
    )

    categories_html = ''
    if grouped_docs:
        sorted_folders = sorted(grouped_docs.keys(), key=_category_label)
        categories_html = ''.join(
            _category_section_html(folder, grouped_docs[folder], vault, public_only)
            for folder in sorted_folders
        )

    total = len(_CORE_DOCS) + sum(len(v) for v in grouped_docs.values())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tarim Shaiel - Campaign Lore</title>
  <!-- AUTO-GENERATED by utilities/world/generate_all_world_html.py - do not hand-edit -->
  <link rel="icon" href="{_FAVICON}">
  <style>{_INDEX_CSS}  </style>
</head>
<body>

<div class="page-wrap">

{hero_html}
{banner_html}

  <div class="content">
    <div class="section-label">Core Documents</div>
{core_html}
{categories_html}
  </div>

  <div class="footer">
    <div class="footer-text">AUTO-GENERATED - DO NOT HAND-EDIT - {total} DOCUMENTS - SOURCE: GITHUB MAIN BRANCH</div>
  </div>

</div>
</body>
</html>
"""
    (docs / 'index.html').write_text(html, encoding='utf-8')


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Batch-generate HTML for all pipeline source files, then write docs/index.html.'
    )
    parser.add_argument('--vault',   help='Vault root (default: auto-detected from script location)')
    parser.add_argument('--dry-run', action='store_true', help='Print what would run, do not write files')
    parser.add_argument(
        '--public', action='store_true',
        help='Public-only mode: only generate/index docs with explicit visibility: public. '
             'Use for Netlify/CI deployments. Fails closed — missing or gm_secrets → skipped.',
    )
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else Path(__file__).parent.parent.parent
    docs  = vault / 'docs'

    print(f'Vault: {vault}')
    if args.public:
        print('Mode: PUBLIC (visibility: public only — fails closed)')
    else:
        print('Mode: LOCAL (all docs including gm_secrets)')
    print('Scanning for pipeline sources...')

    grouped_sources = discover_sources(vault)
    grouped_docs    = generate_all(vault, docs, grouped_sources=grouped_sources,
                                   dry_run=args.dry_run, public_only=args.public)
    total = sum(len(v) for v in grouped_docs.values())
    print(f'Generated {total} world document(s) across {len(grouped_docs)} categories.')

    if not args.dry_run:
        for folder, folder_docs in sorted(grouped_docs.items()):
            count = generate_category_page(docs, vault, folder, folder_docs)
            print(f'  Category: {folder} ({count} doc(s)) → docs/category-{folder}.html')
        generate_index(docs, grouped_docs, vault=vault, public_only=args.public)
        print(f'Index: docs/index.html ({len(_CORE_DOCS)} core + {len(grouped_docs)} categories)')


if __name__ == '__main__':
    main()


# ---------------------------------------------------------------------------
# Generator protocol wrapper (used by utilities/build.py)
# ---------------------------------------------------------------------------
class _Generator:
    name = "world-all"
    description = "Batch-generate HTML for all world docs and write index"

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
