#!/usr/bin/env python3
"""
LK JSON → Source Markdown Converter
=====================================
Converts a LegendKeeper JSON export (timeline) back to the canonical
Obsidian source format understood by the publishing pipeline.

Usage:
    python from_lk_json.py Timeline_Export.json
    python from_lk_json.py Timeline_Export.json --output world/timelines/foo.md
    python from_lk_json.py Timeline_Export.json --include-search-images
"""

import re
import sys
import json
import gzip
import argparse
from datetime import date
from pathlib import Path

MPYR = 365.25 * 24 * 60  # minutes per year


def mins_to_year(minutes: float) -> int:
    # LK stores dates as late-December of each year (~year + 0.99).
    # int() truncates toward zero, recovering the intended year number.
    return int(minutes / MPYR)


def is_direct_image(url: str) -> bool:
    """True for hosted images; False for vecteezy/search pages."""
    if not url:
        return False
    search_hosts = ('vecteezy.com', 'google.com/search', 'bing.com/images',
                    'pinterest.com', 'unsplash.com/s/')
    return not any(h in url for h in search_hosts)


def fmt_event(ev: dict, lanes_by_id: dict, include_search_images: bool = False) -> str:
    name       = ev['name']
    start_yr   = mins_to_year(ev['start'])
    end_yr     = mins_to_year(ev['end']) if ev.get('end') else None
    color      = ev.get('color', '#6B7280')
    icon       = ev.get('iconGlyph', '') or ''
    opacity    = ev.get('opacity', 1.0)
    image_url  = ev.get('imageUrl', '') or ''

    parts = [f'"{name}"']

    if end_yr is not None:
        parts.append(f'start: {start_yr}')
        parts.append(f'end: {end_yr}')
    else:
        parts.append(f'date: {start_yr}')

    if color:
        parts.append(f'color: "{color}"')
    if icon:
        parts.append(f'icon: {icon}')

    use_image = image_url and (include_search_images or is_direct_image(image_url))
    if use_image:
        parts.append(f'image: {image_url}')

    if opacity != 1.0:
        parts.append(f'opacity: {opacity:.2f}')

    return '- ' + ' | '.join(parts)


def convert(json_path: Path, output_path: Path | None,
            include_search_images: bool) -> str:
    raw = json_path.read_bytes()
    if raw[:2] == b'\x1f\x8b':          # gzip magic bytes — .lk files
        raw = gzip.decompress(raw)
    data = json.loads(raw)

    # Extract metadata
    calendars   = data.get('calendars', [])
    cal_name    = calendars[0].get('name', '') if calendars else ''
    resource    = data['resources'][0]
    res_name    = resource.get('name', '')      # "Timeline: Nianhao - The Divine Arc"
    doc         = resource['documents'][0]
    # Strip "Timeline: " prefix if present; fall back to doc name
    doc_title   = re.sub(r'^Timeline:\s*', '', res_name).strip() or doc.get('name', '')

    content     = doc['content']
    lanes_raw   = content['lanes']
    events      = content['events']

    # Preserve JSON lane order (pos is an opaque fractional-index string)
    lanes_by_id = {l['id']: l for l in lanes_raw}

    # Group events by lane, sorted by start within each lane
    from collections import defaultdict
    by_lane: dict[str, list] = defaultdict(list)
    for ev in events:
        by_lane[ev['laneId']].append(ev)
    for lid in by_lane:
        by_lane[lid].sort(key=lambda e: e['start'])

    # Identify the SECRET lane
    secret_lane_ids = {l['id'] for l in lanes_raw if 'secret' in l['name'].lower()}

    # Build frontmatter
    today = date.today().isoformat()
    slug_title = doc_title if doc_title else 'Timeline'

    fm_lines = [
        '---',
        f'title: "{slug_title}"',
        'project: TTRPG_Tarim_Shaiel',
        'type: timeline',
        'tags: [timeline, history]',
        'visibility: gm_secrets',
        'status: draft',
        f'created: {today}',
        f'last_updated: {today}',
    ]
    if cal_name:
        fm_lines.append(f'calendar: {cal_name}')
    fm_lines.append('---')
    fm_lines.append('')

    # Build body sections
    public_sections: list[str] = []
    secret_sections: list[str] = []

    for lane in lanes_raw:
        lid     = lane['id']
        lname   = lane['name']
        evs     = by_lane.get(lid, [])
        if not evs:
            continue

        lines = [f'## {lname}', '']
        for ev in evs:
            lines.append(fmt_event(ev, lanes_by_id, include_search_images))
        lines.append('')

        section_text = '\n'.join(lines)
        if lid in secret_lane_ids:
            secret_sections.append(section_text)
        else:
            public_sections.append(section_text)

    body_parts = public_sections[:]
    if secret_sections:
        body_parts.append('%%')
        body_parts.extend(secret_sections)
        body_parts.append('%%')
        body_parts.append('')

    output = '\n'.join(fm_lines) + '\n' + '\n'.join(body_parts)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert a LegendKeeper JSON export to pipeline source Markdown.'
    )
    parser.add_argument('lk_file', help='LK export file (.json or gzip-compressed .lk)')
    parser.add_argument('--output', '-o', help='Output .md path (default: alongside JSON)')
    parser.add_argument('--include-search-images', action='store_true',
                        help='Include vecteezy/search-page imageUrls (default: skip them)')
    args = parser.parse_args()

    json_path = Path(args.lk_file)
    if not json_path.exists():
        print(f'ERROR: {json_path} not found', file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_path = Path(args.output)
    else:
        stem = re.sub(r'[^\w\-]', '-', json_path.stem.lower())
        stem = re.sub(r'-+', '-', stem).strip('-')
        out_path = json_path.with_name(stem + '-source.md')

    md = convert(json_path, out_path, args.include_search_images)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding='utf-8')
    print(f'Source MD written: {out_path}')
    print(f'  Events: {md.count(chr(10)+"- ")} lines starting with "- "')


if __name__ == '__main__':
    main()
