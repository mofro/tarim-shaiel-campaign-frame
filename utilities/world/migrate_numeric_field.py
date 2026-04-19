#!/usr/bin/env python3
"""
ONE-SHOT MIGRATION SCRIPT — DELETE AFTER USE.

Adds a numeric frontmatter field (e.g. `tier: 3` or `level: 7`) to .md files
by extracting the value from a body pattern like `**_Tier 3_**` or `**_Level 7_**`.

Usage examples:
    # Add tier: to all classes and armor files
    python migrate_numeric_field.py --field tier --dir world/classes world/armor

    # Add level: to all abilities files
    python migrate_numeric_field.py --field level --dir world/abilities

    # Dry run
    python migrate_numeric_field.py --field tier --dir world/classes --dry-run
"""
import argparse
import re
from pathlib import Path


def migrate_dir(vault: Path, directory: Path, field: str, dry_run: bool) -> dict:
    files = sorted(f for f in directory.rglob('*.md') if f.name != '_category.md')
    counts = {'total': 0, 'migrated': 0, 'already_done': 0, 'not_found': 0}

    pattern = re.compile(r'\*\*_?' + re.escape(field.title()) + r'\s+(\d+)', re.IGNORECASE)

    for path in files:
        counts['total'] += 1
        text = path.read_text(encoding='utf-8')

        parts = text.split('---\n', 2)
        has_frontmatter = len(parts) == 3

        if has_frontmatter:
            fm_block = parts[1]
            if re.search(rf'^{re.escape(field)}:', fm_block, re.MULTILINE):
                counts['already_done'] += 1
                continue
            body = parts[2]
        else:
            fm_block = None
            body = text

        m = pattern.search(body)
        if not m:
            print(f'  WARNING (no {field.title()} found): {path.relative_to(vault)}')
            counts['not_found'] += 1
            continue

        value = int(m.group(1))
        if has_frontmatter:
            new_fm = fm_block.rstrip('\n') + f'\n{field}: {value}\n'
            new_text = f'---\n{new_fm}---\n{body}'
        else:
            new_text = f'---\n{field}: {value}\n---\n{body}'

        rel = path.relative_to(vault)
        if dry_run:
            print(f'  DRY-RUN: {rel}  →  {field}: {value}')
        else:
            path.write_text(new_text, encoding='utf-8')
        counts['migrated'] += 1

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description='ONE-SHOT: add a numeric field to .md frontmatter')
    parser.add_argument('--field', required=True, help='Frontmatter field name (e.g. tier, level)')
    parser.add_argument('--dir', nargs='+', required=True, help='Directories relative to vault root')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--vault', default=None)
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else Path(__file__).parent.parent.parent

    totals = {'total': 0, 'migrated': 0, 'already_done': 0, 'not_found': 0}
    for d in args.dir:
        directory = vault / d
        if not directory.exists():
            print(f'  SKIP (directory not found): {d}')
            continue
        print(f'\n[{d}]')
        counts = migrate_dir(vault, directory, args.field, args.dry_run)
        for k in totals:
            totals[k] += counts[k]

    print(f'\nTotal: {totals["total"]} files — '
          f'migrated={totals["migrated"]} already-done={totals["already_done"]} '
          f'not-found={totals["not_found"]}')


if __name__ == '__main__':
    main()
