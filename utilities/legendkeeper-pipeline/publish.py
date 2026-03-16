#!/usr/bin/env python3
"""
LegendKeeper Pipeline Runner
==============================
Single entry point for all three publishing paths.

Usage:
    python publish.py --source path/to/doc.md --all
    python publish.py --source path/to/doc.md --html
    python publish.py --source path/to/doc.md --lk-md
    python publish.py --source path/to/doc.md --lk-json
    python publish.py --source path/to/doc.md --lk-json --lk-compressed

Options:
    --source        Source .md file (required)
    --output        Output directory (default: docs/ for HTML, alongside source for LK)
    --all           Run all generators (lk-md + lk-json + html)
    --html          Generate Campaign Frame-style HTML
    --lk-md         Generate LK-compatible Markdown
    --lk-json       Generate LK JSON (.json)
    --lk-compressed With --lk-json: output gzip-compressed .lk instead of .json
"""

import sys
import argparse
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run(script: Path, args: list[str]) -> bool:
    """Run a generator script with the given args. Returns True on success."""
    cmd = [sys.executable, str(script)] + args
    result = subprocess.run(cmd)
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run the LegendKeeper publishing pipeline for a source document.'
    )
    parser.add_argument('--source', '-s', required=True, help='Source .md file path')
    parser.add_argument('--output', '-o', help='Output directory (for HTML output)')
    parser.add_argument('--all', action='store_true', dest='all_outputs',
                        help='Run all generators')
    parser.add_argument('--html', action='store_true', help='Generate HTML')
    parser.add_argument('--lk-md', action='store_true', dest='lk_md',
                        help='Generate LK Markdown')
    parser.add_argument('--lk-json', action='store_true', dest='lk_json',
                        help='Generate LK JSON')
    parser.add_argument('--lk-compressed', action='store_true', dest='lk_compressed',
                        help='With --lk-json: output .lk (gzip) instead of .json')
    a = parser.parse_args()

    src = Path(a.source)
    if not src.exists():
        print(f'ERROR: Source file not found: {src}', file=sys.stderr)
        sys.exit(1)

    do_html    = a.all_outputs or a.html
    do_lk_md   = a.all_outputs or a.lk_md
    do_lk_json = a.all_outputs or a.lk_json

    if not any([do_html, do_lk_md, do_lk_json]):
        parser.print_help()
        print('\nERROR: specify at least one output flag (--all, --html, --lk-md, --lk-json)')
        sys.exit(1)

    results: list[tuple[str, bool]] = []

    if do_lk_md:
        script = SCRIPT_DIR / 'generate_lk_markdown.py'
        args = [str(src)]
        ok = run(script, args)
        results.append(('LK Markdown', ok))

    if do_lk_json:
        script = SCRIPT_DIR / 'generate_lk_json.py'
        args = [str(src)]
        if a.lk_compressed:
            args.append('--lk')
        ok = run(script, args)
        results.append(('LK JSON', ok))

    if do_html:
        script = SCRIPT_DIR / 'generate_world_html.py'
        args = [str(src)]
        if a.output:
            # If output is a directory, construct the output filename
            out_dir = Path(a.output)
            if out_dir.is_dir() or not out_dir.suffix:
                import re
                slug = re.sub(r'[^\w\-]', '-', src.stem.lower())
                slug = re.sub(r'-+', '-', slug).strip('-')
                out_file = out_dir / f'{slug}.html'
            else:
                out_file = out_dir
            args += ['--output', str(out_file)]
        ok = run(script, args)
        results.append(('HTML', ok))

    # Summary
    print()
    print('─' * 40)
    all_ok = all(ok for _, ok in results)
    for label, ok in results:
        status = '✓' if ok else '✗'
        print(f'  {status}  {label}')
    print('─' * 40)
    if all_ok:
        print(f'  Done. {len(results)} output(s) generated.')
    else:
        failed = [l for l, ok in results if not ok]
        print(f'  FAILED: {", ".join(failed)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
