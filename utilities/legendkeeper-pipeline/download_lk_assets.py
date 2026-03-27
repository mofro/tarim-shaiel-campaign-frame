#!/usr/bin/env python3
"""
Download LegendKeeper asset images to docs/assets/ for local self-hosting.

LK asset URLs (assets.legendkeeper.com) return 403 for unauthenticated
requests. Run this script locally (with internet access) to download all
referenced images. generate_world_html.py will then use local relative paths
instead of the LK CDN URLs.

Usage:
    python download_lk_assets.py                   # scan all *.md, download all
    python download_lk_assets.py --dry-run         # list URLs without downloading
    python download_lk_assets.py --source FILE.md  # limit scan to one file
"""

import re
import sys
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print('Missing dependency: pip install requests')
    sys.exit(1)

LK_ASSET_RE = re.compile(r'https://assets\.legendkeeper\.com/([\w.\-]+)')
ASSETS_DIR   = Path('docs/assets')


def collect_urls(md_files: list[Path]) -> list[tuple[str, str]]:
    """Return sorted list of unique (filename, url) pairs from all md files."""
    seen: dict[str, str] = {}
    for p in md_files:
        text = p.read_text(encoding='utf-8')
        for m in LK_ASSET_RE.finditer(text):
            url      = m.group(0)
            filename = m.group(1)
            seen[filename] = url
    return sorted(seen.items())


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Download LegendKeeper CDN assets to docs/assets/'
    )
    parser.add_argument('--dry-run',  action='store_true', help='List URLs without downloading')
    parser.add_argument('--source',   metavar='FILE',      help='Limit scan to a single .md file')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    if args.source:
        md_files = [Path(args.source).resolve()]
    else:
        md_files = [
            f for f in repo_root.glob('**/*.md')
            if 'archive' not in f.parts and 'utilities' not in f.parts
        ]

    pairs = collect_urls(md_files)

    if not pairs:
        print('No assets.legendkeeper.com URLs found.')
        return

    if args.dry_run:
        print(f'Found {len(pairs)} unique LK asset URL(s):\n')
        for _, url in pairs:
            print(f'  {url}')
        return

    assets_abs = repo_root / ASSETS_DIR
    assets_abs.mkdir(parents=True, exist_ok=True)

    ok = skipped = failed = 0
    for filename, url in pairs:
        dest = assets_abs / filename
        if dest.exists():
            print(f'  ⚠  skip    {filename}')
            skipped += 1
            continue
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                print(f'  ✓  saved   {filename}  ({len(resp.content):,} bytes)')
                ok += 1
            else:
                print(f'  ✗  {resp.status_code}    {url}')
                failed += 1
        except Exception as exc:
            print(f'  ✗  error   {url}  ({exc})')
            failed += 1

    print(f'\n{ok} downloaded · {skipped} skipped · {failed} failed')
    if ok:
        print(f'Assets written to: {assets_abs}')
        print('Next: git add docs/assets/ && git commit, then re-run publish.py --html')


if __name__ == '__main__':
    main()
