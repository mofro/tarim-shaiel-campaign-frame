#!/usr/bin/env python3
"""
Tarim-Shaiel Campaign Frame Generator
======================================
Parses templates/tarim-shaiel-campaign-frame-v2.md → docs/campaign-frame.html

Outputs player-facing content only (stops at GM-facing section marker).
Strips Obsidian-specific syntax (frontmatter, %% comments, [!callout] blocks).

Usage:
    python generate_campaign_frame.py
    python generate_campaign_frame.py --src path/to/frame.md
    python generate_campaign_frame.py --out path/to/output.html
"""

import re
import sys
import argparse
from pathlib import Path
from html import escape

# ---------------------------------------------------------------------------
# Paths (relative to this script: utilities/campaign_frame/)
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
SRC_PATH    = VAULT_ROOT / "templates" / "tarim-shaiel-campaign-frame-v2.md"
OUTPUT_PATH = VAULT_ROOT / "docs" / "campaign-frame.html"

# Make utilities/shared importable regardless of working directory
sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.frontmatter import parse_frontmatter
from shared.md_utils import inline_md, strip_obsidian_comments

COVER_IMAGE_URL = "https://images5.alphacoders.com/798/thumb-1920-798802.jpg"

# ---------------------------------------------------------------------------
# Preprocessing: strip Obsidian-specific syntax
# ---------------------------------------------------------------------------

def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter between opening --- delimiters."""
    m = re.match(r'^---\n.*?\n---\n', text, re.DOTALL)
    return text[m.end():] if m else text


def preprocess(text: str) -> str:
    text = strip_frontmatter(text)
    text = strip_obsidian_comments(text)
    # Clean up excessive blank lines left after stripping
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

def split_sections(text: str) -> dict[str, str]:
    """Split text into {section_title: body_content} at ## headings.
    Also captures the preamble (before first ##) as key ''.
    """
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
# Paragraph & block parsers
# ---------------------------------------------------------------------------

def parse_paragraphs(content: str) -> list[str]:
    """Split content into paragraphs at blank lines.
    Joins continued lines within a paragraph.
    Skips Obsidian callout syntax lines (> [!...]).
    """
    paras: list[str] = []
    current: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        # Skip horizontal rules
        if stripped == '---':
            if current:
                paras.append(' '.join(current))
                current = []
            continue
        # Skip callout type markers and their headers (already stripped by %% removal,
        # but Player/GM Principles callouts remain)
        if re.match(r'^>\s*\[!(tip|important)\]', stripped, re.IGNORECASE):
            if current:
                paras.append(' '.join(current))
                current = []
            continue
        if re.match(r'^>\s*#{1,4}\s+', stripped):
            # Callout title line — skip, handled by parse_principles
            if current:
                paras.append(' '.join(current))
                current = []
            continue

        if stripped:
            # Strip leading > for blockquotes — flag them specially
            current.append(stripped)
        elif current:
            paras.append(' '.join(current))
            current = []

    if current:
        paras.append(' '.join(current))

    return [p for p in paras if p]


def render_para(p: str) -> str:
    """Render a single paragraph, handling blockquotes → callout boxes."""
    p = p.strip()
    if p.startswith('> '):
        inner = re.sub(r'^>\s*', '', p).strip()
        return f'<div class="callout">{inline_md(inner)}</div>\n'
    elif p.startswith('>'):
        inner = p[1:].strip()
        return f'<div class="callout">{inline_md(inner)}</div>\n'
    else:
        return f'<p>{inline_md(p)}</p>\n'


def parse_principles(content: str) -> list[tuple[str, str]]:
    """Extract (title, body) pairs from Obsidian > [!tip/important] callout blocks.

    Format in source:
        > [!tip]
        > ### Title text.
        Body paragraph text follows on the next line.
    """
    principles: list[tuple[str, str]] = []
    lines = content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if re.match(r'^>\s*\[!(tip|important)\]', line, re.IGNORECASE):
            title = ''
            i += 1
            # Next line: > ### Title or > #### Title
            if i < len(lines):
                title_line = lines[i].strip()
                m = re.match(r'^>\s*#{1,4}\s+(.+)', title_line)
                if m:
                    title = m.group(1).rstrip('.')
                    i += 1

            # Collect body: non-empty, non-> lines up to next callout or blank-then-callout
            body_parts: list[str] = []
            while i < len(lines):
                bl = lines[i].strip()
                if not bl:
                    # Blank line — peek ahead; if next is a new callout, stop
                    if i + 1 < len(lines) and re.match(
                        r'^>\s*\[!(tip|important)\]', lines[i + 1].strip(), re.IGNORECASE
                    ):
                        i += 1
                        break
                    i += 1
                    if body_parts:
                        break
                elif bl.startswith('>'):
                    # Body text inside callout block — strip the > prefix and keep content
                    inner = re.sub(r'^>\s*', '', bl).strip()
                    if inner and not re.match(r'\[!(tip|important)\]', inner, re.IGNORECASE) \
                            and not re.match(r'#{1,4}\s', inner):
                        body_parts.append(inner)
                    i += 1
                else:
                    body_parts.append(bl)
                    i += 1

            if title:
                principles.append((title, ' '.join(body_parts)))
        else:
            i += 1

    return principles


def parse_themes(content: str) -> list[tuple[str, str]]:
    """Extract (title, body) from theme list items: - **Title.** Body."""
    themes: list[tuple[str, str]] = []
    for line in content.splitlines():
        m = re.match(r'^-\s+\*\*(.+?)\.\*\*\s+(.*)', line.strip())
        if m:
            themes.append((m.group(1), m.group(2).strip()))
    return themes


def parse_questions(content: str) -> dict[str, list[str]]:
    """Extract question groups: {'On your character': [...], 'On the campaign': [...]}"""
    groups: dict[str, list[str]] = {}
    current_group: str | None = None
    current_items: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        # Group header: **On your character:** or **On the campaign:**
        m = re.match(r'^\*\*(.+?):?\*\*\s*$', stripped)
        if m:
            if current_group and current_items:
                groups[current_group] = current_items
            current_group = m.group(1).rstrip(':')
            current_items = []
        elif current_group and stripped.startswith('- '):
            current_items.append(stripped[2:])

    if current_group and current_items:
        groups[current_group] = current_items

    return groups


def extract_content_advisories(content: str) -> str:
    """Extract the Lines & Veils content advisory list."""
    m = re.search(r'Content advisories?[:\s]+(.+?)(?:\.|$)', content)
    return m.group(1).strip() if m else ''


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def render_section(title: str, content_html: str, chapter_intro: str = '') -> str:
    intro = f'  <div class="chapter-intro">{escape(chapter_intro)}</div>\n' if chapter_intro else ''
    return (
        f'<div class="section">\n'
        f'  <div class="section-title">{escape(title)}</div>\n'
        f'{intro}'
        f'{content_html}'
        f'</div>\n'
    )


def render_pitch(content: str) -> str:
    paras = parse_paragraphs(content)
    html = ''.join(render_para(p) for p in paras)
    return render_section(
        'The Pitch',
        html,
        # chapter_intro='Read this to your players when pitching the campaign.',
    )


def render_tone(content: str) -> str:
    # Extract the tone tag line (contains · separators)
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and '·' in stripped:
            tags = escape(stripped)
            return (
                f'<div class="section">\n'
                f'  <div class="section-title">Tone &amp; Feel</div>\n'
                f'  <div class="tone-tags">{tags}</div>\n'
                f'</div>\n'
            )
    return ''


def render_themes(content: str) -> str:
    themes = parse_themes(content)
    left, right = themes[:3], themes[3:]

    def theme_block(title: str, body: str) -> str:
        return (
            f'    <div class="theme">\n'
            f'      <div class="theme-title">{escape(title)}.</div>\n'
            f'      <p>{inline_md(body)}</p>\n'
            f'    </div>\n'
        )

    two_col = (
        '  <div class="two-col">\n'
        '    <div>\n'
        + ''.join(theme_block(t, b) for t, b in left)
        + '    </div>\n'
        '    <div>\n'
        + ''.join(theme_block(t, b) for t, b in right)
        + '    </div>\n'
        '  </div>\n'
    )
    return render_section(
        'Themes',
        two_col,
        chapter_intro='These themes form the spine of the campaign.',
    )


def render_touchstones(content: str) -> str:
    # Filter out GM blockquote lines (> [GM: ...]) before parsing
    paras = [p for p in parse_paragraphs(content) if not p.strip().startswith('>')]
    # First non-empty para is the touchstone list (italic titles)
    # Second is the throughlines paragraph
    touchstone_line = paras[0] if paras else ''
    throughline = paras[1] if len(paras) > 1 else ''

    html = f'  <div class="touchstones">{inline_md(touchstone_line)}</div>\n'
    if throughline:
        html += f'  <div class="touchstones-body">{inline_md(throughline)}</div>\n'

    return render_section('Touchstones', html)


def render_overview(content: str) -> str:
    paras = parse_paragraphs(content)
    # Split roughly 3 left / 2 right (matching prototype)
    left, right = paras[:3], paras[3:]

    left_html = ''.join(f'      <p>{inline_md(p)}</p>\n' for p in left)
    right_html = ''.join(f'      <p>{inline_md(p)}</p>\n' for p in right)

    two_col = (
        '  <div class="two-col">\n'
        f'    <div>\n{left_html}    </div>\n'
        f'    <div>\n{right_html}    </div>\n'
        '  </div>\n'
    )
    return render_section(
        'Overview',
        two_col,
        chapter_intro='Player-facing. Sets the world without revealing the premise.',
    )


def render_heritage(content: str) -> str:
    paras = parse_paragraphs(content)
    html = ''
    for p in paras:
        stripped = p.strip()
        # Detect callout (blockquote)
        if stripped.startswith('>'):
            inner = re.sub(r'^>\s*', '', stripped)
            html += f'  <div class="callout">{inline_md(inner)}</div>\n'
        else:
            html += f'  <p>{inline_md(stripped)}</p>\n'

    return render_section('Heritage & Classes', html)


def render_principles_pair(player_content: str, gm_content: str) -> str:
    """Render Player Principles and GM Principles side by side."""

    def principle_block(title: str, body: str) -> str:
        return (
            f'      <div class="principle">\n'
            f'        <div class="principle-title">{inline_md(title)}.</div>\n'
            f'        <p>{inline_md(body)}</p>\n'
            f'      </div>\n'
        )

    player_items = parse_principles(player_content)
    gm_items = parse_principles(gm_content)

    player_html = ''.join(principle_block(t, b) for t, b in player_items)
    gm_html = ''.join(principle_block(t, b) for t, b in gm_items)

    return (
        '<div class="two-col">\n'
        '  <div>\n'
        '    <div class="section-title">Player Principles</div>\n'
        '    <div class="chapter-intro" style="margin-bottom:1.4rem;">'
        "Follow these principles to stay in the right relationship with the campaign&#8217;s themes."
        " They are not rules. They are the mindset that makes the campaign work."
        '</div>\n'
        f'{player_html}'
        '  </div>\n'
        '  <div>\n'
        '    <div class="section-title">GM Principles</div>\n'
        '    <div class="chapter-intro" style="margin-bottom:1.4rem;">'
        "Use these principles to run a campaign that earns its themes."
        '</div>\n'
        f'{gm_html}'
        '  </div>\n'
        '</div>\n'
    )


def render_session_zero(content: str) -> str:
    questions = parse_questions(content)
    advisories = extract_content_advisories(content)

    def question_col(group_name: str) -> str:
        items = questions.get(group_name, [])
        items_html = ''.join(f'          <li>{inline_md(q)}</li>\n' for q in items)
        return (
            f'    <div>\n'
            f'      <h4>{escape(group_name)}</h4>\n'
            f'      <ul>\n{items_html}      </ul>\n'
            f'    </div>\n'
        )

    left_col = question_col('On your character')

    right_items_html = ''
    campaign_items = questions.get('On the campaign', [])
    if campaign_items:
        right_items_html += '      <h4>On the campaign</h4>\n      <ul>\n'
        right_items_html += ''.join(f'        <li>{inline_md(q)}</li>\n' for q in campaign_items)
        right_items_html += '      </ul>\n'

    if advisories:
        right_items_html += (
            '      <div class="divider" style="margin:1.2rem 0;"></div>\n'
            '      <h4>Content Advisories</h4>\n'
            f'      <div class="advisories">{inline_md(advisories)}</div>\n'
        )

    two_col = (
        '  <div class="two-col session-questions">\n'
        f'{left_col}'
        f'    <div>\n{right_items_html}    </div>\n'
        '  </div>\n'
    )

    return render_section(
        'Session Zero',
        two_col,
        chapter_intro=(
            'Deliver these questions before character creation, not after.'
            " They invite the right character orientation without revealing the campaign's premise."
        ),
    )


# ---------------------------------------------------------------------------
# CSS (loaded from campaign_frame.css at runtime; inlined into HTML output)
# ---------------------------------------------------------------------------

CSS = (SCRIPT_DIR / "campaign_frame.css").read_text()


# ---------------------------------------------------------------------------
# At a Glance table parser
# ---------------------------------------------------------------------------

def render_at_a_glance(content: str) -> str:
    """Render the At a Glance markdown table as an HTML table."""
    rows_html = ''
    for line in content.splitlines():
        # Match table rows: | label | value |
        m = re.match(r'^\|\s*(.+?)\s*\|\s*(.+?)\s*\|', line)
        if m and not re.match(r'^\|[-| ]+\|', line):  # skip separator rows
            raw_label = re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(1).strip())
            label = escape(raw_label)
            value = inline_md(m.group(2).strip())
            rows_html += f'      <tr><td>{label}</td><td>{value}</td></tr>\n'

    if not rows_html:
        return ''
    return f'    <table class="at-a-glance">\n{rows_html}    </table>\n'


# ---------------------------------------------------------------------------
# Full page assembly
# ---------------------------------------------------------------------------

def build_html(sections: dict[str, str], version: str = 'v2.0') -> str:
    # Extract cover concept from Concept section
    concept = ''
    for line in sections.get('Concept', '').splitlines():
        stripped = line.strip().strip('*').strip()
        if stripped:
            concept = stripped
            break

    css = CSS.replace('%(cover_image_url)s', COVER_IMAGE_URL)

    # Build content blocks in document order
    content_blocks: list[str] = []

    # At a Glance table
    at_a_glance = render_at_a_glance(sections.get('At a Glance', ''))
    if at_a_glance:
        content_blocks.append(at_a_glance)

    # The Pitch
    if 'The Pitch' in sections:
        content_blocks.append(render_pitch(sections['The Pitch']))

    # Tone & Feel
    if 'Tone & Feel' in sections:
        content_blocks.append(render_tone(sections['Tone & Feel']))

    # Themes
    if 'Themes' in sections:
        content_blocks.append(render_themes(sections['Themes']))
        content_blocks.append('<div class="divider"></div>\n')

    # Touchstones
    if 'Touchstones' in sections:
        content_blocks.append(render_touchstones(sections['Touchstones']))
        content_blocks.append('<div class="divider"></div>\n')

    # Overview
    if 'Overview' in sections:
        content_blocks.append(render_overview(sections['Overview']))
        content_blocks.append('<div class="divider"></div>\n')

    # Heritage & Classes
    if 'Heritage & Classes' in sections:
        content_blocks.append(render_heritage(sections['Heritage & Classes']))
        content_blocks.append('<div class="divider"></div>\n')

    # Player + GM Principles (side by side)
    if 'Player Principles' in sections and 'GM Principles' in sections:
        content_blocks.append(
            render_principles_pair(sections['Player Principles'], sections['GM Principles'])
        )
        content_blocks.append('<div class="divider"></div>\n')

    # Session Zero Questions
    if 'Session Zero Questions' in sections:
        content_blocks.append(render_session_zero(sections['Session Zero Questions']))

    content_html = '\n'.join(content_blocks)
    concept_escaped = escape(concept)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tarim Shaiel &mdash; Campaign Frame</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='10' fill='%231a1208'/><polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 33.4,43.1 18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>">
  <!-- AUTO-GENERATED by utilities/campaign_frame/generate_campaign_frame.py — do not hand-edit -->
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
      <div class="cover-title">Tarim Shaiel</div>
      <div class="cover-subtitle">A Daggerheart Campaign</div>
      <div class="cover-concept"><em>{concept_escaped}</em></div>
    </div>
  </div>

  <div class="banner">
    <span>Player-Facing Document</span>
    <span>Campaign Frame &middot; {escape(version)}</span>
  </div>
  <div class="banner-rule"></div>

  <!-- MAIN CONTENT -->
  <div class="content">
{content_html}
  </div><!-- /content -->

  <!-- FOOTER / CREDITS -->
  <div class="credits">
    <div>Tarim Shaiel &middot; Campaign Frame {escape(version)} &middot; Daggerheart &middot; March 2026</div>
    <div class="dpcr-notice">
      This product includes material from the Daggerheart System Reference Document 1.0,
      &copy; Critical Role, LLC, under the terms of the Darrington Press Community Gaming License.
      More at <a href="https://www.daggerheart.com">daggerheart.com</a>.
    </div>
  </div>

</div><!-- /page-wrap -->

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description='Generate campaign frame HTML from Markdown source.')
    parser.add_argument('--src', default=str(SRC_PATH), help='Path to source .md file')
    parser.add_argument('--out', default=str(OUTPUT_PATH), help='Output HTML path')
    args = parser.parse_args()

    src = Path(args.src)
    out = Path(args.out)

    if not src.exists():
        raise FileNotFoundError(f'Source file not found: {src}')

    raw = src.read_text(encoding='utf-8')
    processed = preprocess(raw)
    sections = split_sections(processed)

    # Extract version from frontmatter of original (before stripping)
    version = 'v2.0'
    m = re.search(r'^version:\s*(.+)$', raw, re.MULTILINE)
    if m:
        ver_str = m.group(1).strip()
        if '.' not in ver_str:
            ver_str += '.0'
        version = f'v{ver_str}'

    html = build_html(sections, version=version)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')

    print(f'Campaign frame generated: {out}')
    print(f'  Source: {src}')
    print(f'  Sections found: {", ".join(k for k in sections if k)}')


if __name__ == '__main__':
    main()
