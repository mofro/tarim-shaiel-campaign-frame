#!/usr/bin/env python3
"""One-shot: add pipeline frontmatter to world/abilities/*.md files.

Extracts domain from body text pattern: _DomainName Ability._ or _DomainName Spell._
Adds type, project, visibility, status, domain, parent-page fields.
Preserves existing level: field.
"""
import re
from pathlib import Path

VAULT = Path(__file__).parent.parent.parent
ABILITIES_DIR = VAULT / 'world' / 'abilities'

DOMAIN_RE = re.compile(r'_([A-Z][a-z]+) (?:Ability|Spell)\._')
KNOWN_DOMAINS = {'Arcana', 'Blade', 'Bone', 'Codex', 'Grace', 'Midnight', 'Sage', 'Splendor', 'Valor'}


def parse_fm(text):
    if text.startswith('---\n'):
        end = text.index('\n---\n', 4)
        return text[4:end].strip(), text[end + 5:].strip()
    return '', text.strip()


def main():
    no_domain = []
    for path in sorted(ABILITIES_DIR.glob('*.md')):
        if path.name == '_category.md':
            continue
        text = path.read_text(encoding='utf-8')
        m = DOMAIN_RE.search(text)
        domain = m.group(1) if m and m.group(1) in KNOWN_DOMAINS else None

        existing_fm, body = parse_fm(text)

        # Preserve level: line from existing frontmatter
        level_line = ''
        for line in existing_fm.splitlines():
            if line.startswith('level:'):
                level_line = line
                break

        title = path.stem.replace('"', '\\"')
        fm_lines = [
            f'title: "{title}"',
            'project: TTRPG_Tarim_Shaiel',
            'type: lore',
            'visibility: gm_secrets',
            'status: canon',
            'created: 2026-04-20',
            'last_updated: 2026-04-20',
        ]
        if level_line:
            fm_lines.append(level_line)
        if domain:
            fm_lines.append(f'domain: {domain.lower()}')
            fm_lines.append(f'parent-page: {domain.lower()}')

        new_text = '---\n' + '\n'.join(fm_lines) + '\n---\n\n' + body + '\n'
        path.write_text(new_text, encoding='utf-8')

        status = domain if domain else 'NO-DOMAIN'
        print(f'  {status:<12} {path.name}')
        if not domain:
            no_domain.append(path.name)

    print(f'\nDone. {len(no_domain)} files with no domain detected:')
    for f in no_domain:
        print(f'  {f}')


if __name__ == '__main__':
    main()
