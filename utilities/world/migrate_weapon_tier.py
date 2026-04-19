#!/usr/bin/env python3
"""
ONE-SHOT MIGRATION SCRIPT — DELETE AFTER USE.

Reads every weapon .md under world/weapons/ (recursively, skipping _category.md),
extracts the Tier value from the body line `**Tier N:**` and inserts
`tier: N` (integer) into the YAML frontmatter block.

Usage:
    python migrate_weapon_tier.py [--dry-run] [--vault /path/to/vault]
"""
import argparse
import re
from pathlib import Path


def migrate(vault: Path, dry_run: bool) -> None:
    weapons_root = vault / 'world' / 'weapons'
    files = sorted(f for f in weapons_root.rglob('*.md') if f.name != '_category.md')

    total = migrated = already_done = no_tier = 0

    for path in files:
        total += 1
        text = path.read_text(encoding='utf-8')

        parts = text.split('---\n', 2)
        if len(parts) < 3:
            print(f'  SKIP (no frontmatter): {path.relative_to(vault)}')
            no_tier += 1
            continue

        fm_block = parts[1]
        if re.search(r'^tier:', fm_block, re.MULTILINE):
            already_done += 1
            continue

        body = parts[2]
        m = re.search(r'\*\*Tier\s+(\d+)', body)
        if not m:
            print(f'  WARNING (no Tier found): {path.relative_to(vault)}')
            no_tier += 1
            continue

        tier_value = int(m.group(1))
        new_fm = fm_block.rstrip('\n') + f'\ntier: {tier_value}\n'
        new_text = f'---\n{new_fm}---\n{body}'

        rel = path.relative_to(vault)
        if dry_run:
            print(f'  DRY-RUN: {rel}  →  tier: {tier_value}')
        else:
            path.write_text(new_text, encoding='utf-8')
        migrated += 1

    print(f'\nDone. total={total} migrated={migrated} already-done={already_done} no-tier={no_tier}')


def main() -> None:
    parser = argparse.ArgumentParser(description='ONE-SHOT: add tier: to weapon frontmatter')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--vault', default=None)
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else Path(__file__).parent.parent.parent
    migrate(vault, args.dry_run)


if __name__ == '__main__':
    main()
