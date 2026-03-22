#!/usr/bin/env python3
"""
LegendKeeper Markdown Generator
================================
Converts an Obsidian source .md file → LK-compatible Markdown for LK Markdown import.

Handles two document types:
  myth / lore  — prose pages with optional epigraph, sections, secret block
  timeline     — event list rendered as a markdown table (for human reference)

Usage:
    python generate_lk_markdown.py source.md
    python generate_lk_markdown.py source.md --output path/to/output.md
"""

import re
import sys
import argparse
from pathlib import Path

# Make utilities/shared importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.frontmatter import parse_frontmatter
from shared.md_utils import (
    extract_secret_blocks,
    strip_wikilinks,
    strip_obsidian_embeds,
    clean_body,
)


# ---------------------------------------------------------------------------
# Timeline event parsing
# ---------------------------------------------------------------------------

def parse_event_line(line: str) -> dict | None:
    """Parse a pipe-syntax event line: - "Name" | key: val | key: val …"""
    line = line.strip().lstrip('- ').strip()
    m = re.match(r'"([^"]+)"\s*(.*)', line)
    if not m:
        return None
    ev = {'name': m.group(1)}
    for part in m.group(2).split('|'):
        part = part.strip()
        if not part:
            continue
        if ':' in part:
            k, v = part.split(':', 1)
            ev[k.strip().lower()] = v.strip().strip('"')
    return ev


def parse_timeline_sections(body: str) -> dict[str, list[dict]]:
    """Return {section_name: [events]} from timeline body (after secret removal)."""
    sections: dict[str, list[dict]] = {}
    current: str = ''
    for line in body.splitlines():
        if re.match(r'^## ', line):
            current = re.sub(r'^##\s+', '', line).strip()
            sections[current] = []
        elif current and line.strip().startswith('-'):
            ev = parse_event_line(line)
            if ev:
                sections[current].append(ev)
    return sections


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_myth_md(fm: dict, body: str) -> str:
    """Generate LK Markdown for a myth/lore/prose page."""
    body, secrets = extract_secret_blocks(body)
    body = clean_body(body)

    # Build LK frontmatter — only `tags` is used by LK Markdown import
    tags = fm.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in re.split(r'[,\s]+', tags) if t.strip()]
    # Format as YAML list
    if len(tags) == 1:
        lk_fm = f'---\ntags: {tags[0]}\n---'
    elif tags:
        tag_lines = '\n'.join(f'  - {t}' for t in tags)
        lk_fm = f'---\ntags:\n{tag_lines}\n---'
    else:
        lk_fm = ''

    parts: list[str] = []
    if lk_fm:
        parts.append(lk_fm)
    parts.append(body)

    # Append secret blocks as LK Secret sections
    for secret_content in secrets:
        secret_clean = clean_body(secret_content)
        # Strip any ## heading at the start of the secret block (e.g. "## Secret")
        secret_clean = re.sub(r'^#+\s+.+\n', '', secret_clean).strip()
        if secret_clean:
            parts.append(f'\nSecret\n\n{secret_clean}')

    return '\n\n'.join(p.strip() for p in parts if p.strip())


def generate_timeline_md(fm: dict, body: str) -> str:
    """Generate LK Markdown for a timeline (as a human-readable reference table)."""
    body, secrets = extract_secret_blocks(body)
    sections = parse_timeline_sections(body)

    title = fm.get('title', 'Timeline')
    calendar = fm.get('calendar', '')

    lines: list[str] = [f'# {title}']
    if calendar:
        lines.append(f'\n*Calendar: {calendar}*')

    for section_name, events in sections.items():
        if not events:
            continue
        lines.append(f'\n## {section_name}\n')
        lines.append('| Event | Start | End | Color | Icon |')
        lines.append('|-------|-------|-----|-------|------|')
        for ev in events:
            start = ev.get('start', ev.get('date', ''))
            end = ev.get('end', '')
            color = ev.get('color', '')
            icon = ev.get('icon', '')
            lines.append(f'| {ev["name"]} | {start} | {end} | {color} | {icon} |')

    # Secret events as LK Secret section
    if secrets:
        secret_events: list[dict] = []
        for secret_part in secrets:
            for line in secret_part.splitlines():
                if line.strip().startswith('-'):
                    ev = parse_event_line(line)
                    if ev:
                        secret_events.append(ev)

        if secret_events:
            lines.append('\nSecret\n')
            lines.append('| Event | Date | Color | Icon |')
            lines.append('|-------|------|-------|------|')
            for ev in secret_events:
                date = ev.get('start', ev.get('date', ''))
                color = ev.get('color', '')
                icon = ev.get('icon', '')
                lines.append(f'| {ev["name"]} | {date} | {color} | {icon} |')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate LK-compatible Markdown from an Obsidian source file.'
    )
    parser.add_argument('source', help='Source .md file path')
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: <source-stem>-lk.md alongside source)',
    )
    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise FileNotFoundError(f'Source file not found: {src}')

    raw = src.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(raw)
    doc_type = fm.get('type', '').lower()

    if doc_type in ('myth', 'fable', 'lore', 'page'):
        result = generate_myth_md(fm, body)
    elif doc_type == 'timeline':
        result = generate_timeline_md(fm, body)
    else:
        # Default: treat as prose page
        result = generate_myth_md(fm, body)

    out_path = Path(args.output) if args.output else src.with_name(src.stem + '-lk.md')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding='utf-8')
    print(f'LK Markdown written: {out_path}')
    print(f'  Type: {doc_type or "page (default)"}')


if __name__ == '__main__':
    main()
