#!/usr/bin/env python3
"""One-shot: add pipeline frontmatter to world/domains/*.md files
and fix broken ability links from references/daggerheart-srd/abilities/
to world/abilities/ with URL-decoded filenames.
"""
import re
from pathlib import Path
from urllib.parse import unquote

VAULT = Path(__file__).parent.parent.parent
DOMAINS_DIR = VAULT / 'world' / 'domains'

# Verify actual ability filenames for safe link replacement
ABILITIES_DIR = VAULT / 'world' / 'abilities'
ABILITY_FILES = {p.name for p in ABILITIES_DIR.glob('*.md')}


def fix_ability_link(m):
    link_text = m.group(1)
    raw_path = m.group(2)
    if 'daggerheart-srd/abilities/' not in raw_path:
        return m.group(0)
    # Extract filename, URL-decode, replace path prefix
    filename = unquote(raw_path.rsplit('/', 1)[-1])
    # Verify file exists; warn if not
    if filename not in ABILITY_FILES:
        print(f'    WARN: ability file not found: {filename!r}')
    return f'[{link_text}](world/abilities/{filename})'


LINK_RE = re.compile(r'\[([^\]]+)\]\((references/daggerheart-srd/abilities/[^)]+)\)')

DOMAINS = ['Arcana', 'Blade', 'Bone', 'Codex', 'Grace', 'Midnight', 'Sage', 'Splendor', 'Valor']


def main():
    for domain_name in DOMAINS:
        path = DOMAINS_DIR / f'{domain_name}.md'
        if not path.exists():
            print(f'  MISSING: {path}')
            continue

        text = path.read_text(encoding='utf-8')

        # Strip existing frontmatter if any
        if text.startswith('---\n'):
            end = text.index('\n---\n', 4)
            body = text[end + 5:].strip()
        else:
            body = text.strip()

        # Fix ability links
        body_fixed = LINK_RE.sub(fix_ability_link, body)

        fm = (
            f'---\n'
            f'title: {domain_name}\n'
            f'project: TTRPG_Tarim_Shaiel\n'
            f'type: lore\n'
            f'visibility: gm_secrets\n'
            f'status: canon\n'
            f'created: 2026-04-20\n'
            f'last_updated: 2026-04-20\n'
            f'---\n\n'
        )
        path.write_text(fm + body_fixed + '\n', encoding='utf-8')
        fixed = len(LINK_RE.findall(body))
        print(f'  OK  {domain_name}.md  ({fixed} links fixed)')


if __name__ == '__main__':
    main()
