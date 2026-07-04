#!/usr/bin/env python3
"""
LK ProseMirror (ADF-dialect) → Obsidian Markdown converter.

Inverse of md_to_pm.py — reconstructs the exact vault syntax the HTML pipeline
parses (Tier 2 callout regex html_render.py:261, Tier 1 {gm:} md_utils.py:35,
Tier 3 embed html_render.py:46, %% comments):

  block-secret "GM" / "GM id=x"      → > [!gm-only] / > [!gm-only id=x]
  block-secret "GM comment"          → %% ... %%
  block-secret "GM embed: <path>"    → ![[<path minus .md>]]  (content discarded
                                        — marker-only by construction)
  block-secret other titles          → > [!gm-only]  (LK-authored secrets)
  panel                              → > [!info/note/tip/important]
  mention                            → [[name]] / [[name|alias]]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

PANEL_TO_CALLOUT = {'info': 'info', 'note': 'note', 'success': 'tip',
                    'warning': 'important', 'error': 'warning'}


def doc_to_markdown(content: dict, id_to_name: dict) -> str:
    """Convert a ProseMirror doc node to Markdown text."""
    if not content or content.get('type') != 'doc':
        return ''
    lines: list[str] = []
    for node in content.get('content', []):
        block = _block(node, id_to_name)
        if block is not None:
            lines.append(block)
    return '\n\n'.join(l for l in lines if l is not None).strip() + '\n'


def _block(node: dict, ids: dict, depth: int = 0) -> str | None:
    t = node.get('type')
    if t == 'heading':
        level = (node.get('attrs') or {}).get('level', 1)
        return '#' * level + ' ' + _inline(node.get('content', []), ids)
    if t == 'paragraph':
        return _inline(node.get('content', []), ids)
    if t == 'rule':
        return '---'
    if t == 'blockquote':
        inner = [_block(c, ids) for c in node.get('content', [])]
        return '\n'.join('> ' + l for blk in inner if blk
                         for l in blk.split('\n'))
    if t == 'bulletList':
        out = []
        for item in node.get('content', []):
            body = [_block(c, ids) for c in item.get('content', [])]
            first, *rest = [b for b in body if b] or ['']
            out.append('- ' + first)
            out.extend('  ' + r for r in rest)
        return '\n'.join(out)
    if t == 'orderedList':
        out = []
        for i, item in enumerate(node.get('content', []), 1):
            body = [_block(c, ids) for c in item.get('content', [])]
            first, *rest = [b for b in body if b] or ['']
            out.append(f'{i}. ' + first)
            out.extend('   ' + r for r in rest)
        return '\n'.join(out)
    if t == 'taskList':
        out = []
        for item in node.get('content', []):
            state = (item.get('attrs') or {}).get('state') == 'DONE'
            txt = _inline_deep(item.get('content', []), ids)
            out.append(f"- [{'x' if state else ' '}] {txt}")
        return '\n'.join(out)
    if t == 'panel':
        ptype = (node.get('attrs') or {}).get('panelType', 'note')
        callout = PANEL_TO_CALLOUT.get(ptype, 'note')
        inner = [_block(c, ids) for c in node.get('content', [])]
        body = '\n'.join(l for blk in inner if blk for l in blk.split('\n'))
        return f'> [!{callout}]\n' + '\n'.join('> ' + l for l in body.split('\n'))
    if t == 'table':
        return _table(node, ids)
    if t == 'bodiedExtension':
        return _secret(node, ids)
    if t == 'mediaSingle':
        for media in node.get('content', []):
            url = (media.get('attrs') or {}).get('url', '')
            if url:
                return f'![embedded image]({url})'
        return None
    if t in ('layoutSection',):
        inner = []
        for col in node.get('content', []):
            for c in col.get('content', []):
                blk = _block(c, ids)
                if blk:
                    inner.append(blk)
        return '\n\n'.join(inner)
    if t in ('extension', 'inlineExtension', 'event', 'arrow', 'bookmark', 'draw',
             'element', 'external', 'frame', 'free', 'geo', 'group', 'image', 'note'):
        return None                       # board/map/timeline internals — out of scope
    # unknown block: flatten any inline content
    if node.get('content'):
        return _inline_deep(node.get('content', []), ids)
    return None


def _secret(node: dict, ids: dict) -> str | None:
    attrs = node.get('attrs') or {}
    if attrs.get('extensionKey') not in ('block-secret', ''):
        return None
    title = str((attrs.get('parameters') or {}).get('extensionTitle', '') or '')
    inner_blocks = [_block(c, ids) for c in node.get('content', [])]
    body = '\n'.join(b for b in inner_blocks if b)

    if title.startswith('GM embed: '):
        path = title[len('GM embed: '):].strip()
        if path.endswith('.md'):
            path = path[:-3]
        return f'![[{path}]]'             # content discarded — marker-only
    if title == 'GM comment':
        return f'%%\n{body}\n%%'
    # "GM", "GM id=x", LK default "Secret", or anything else → Tier 2 callout
    cid = ''
    if title.startswith('GM id='):
        cid = title[len('GM id='):].strip()
    header = f'> [!gm-only id={cid}]' if cid else '> [!gm-only]'
    quoted = '\n'.join('> ' + l for l in body.split('\n')) if body else '>'
    return f'{header}\n{quoted}'


def _table(node: dict, ids: dict) -> str:
    rows = []
    header = False
    for row in node.get('content', []):
        cells = []
        for cell in row.get('content', []):
            if cell.get('type') == 'tableHeader':
                header = True
            cells.append(_inline_deep(cell.get('content', []), ids).replace('|', '\\|'))
        rows.append(cells)
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    for r in rows:
        r.extend([''] * (width - len(r)))
    lines = ['| ' + ' | '.join(rows[0]) + ' |',
             '|' + '---|' * width]
    for r in rows[1:]:
        lines.append('| ' + ' | '.join(r) + ' |')
    if not header and len(rows) == 1:
        lines = ['| ' + ' | '.join(rows[0]) + ' |', '|' + '---|' * width]
    return '\n'.join(lines)


def _inline_deep(nodes: list, ids: dict) -> str:
    """Flatten nested block content (e.g. a table cell's paragraphs) to one line."""
    parts = []
    for n in nodes:
        t = n.get('type')
        if t == 'paragraph':
            parts.append(_inline(n.get('content', []), ids))
        elif t in ('text', 'mention', 'hardBreak', 'emoji', 'date', 'status'):
            parts.append(_inline([n], ids))
        else:
            blk = _block(n, ids)
            if blk:
                parts.append(blk.replace('\n', ' '))
    return ' '.join(p for p in parts if p)


def _inline(nodes: list, ids: dict) -> str:
    out = []
    for n in nodes:
        t = n.get('type')
        if t == 'text':
            out.append(_marked(n))
        elif t == 'mention':
            attrs = n.get('attrs') or {}
            name = ids.get(attrs.get('id', ''), attrs.get('text', ''))
            alias = attrs.get('alias', '')
            out.append(f'[[{name}|{alias}]]' if alias and alias != name else f'[[{name}]]')
        elif t == 'hardBreak':
            out.append('<br>')
        elif t in ('emoji', 'date', 'status', 'inlineExtension'):
            txt = (n.get('attrs') or {}).get('text', '')
            if txt:
                out.append(txt)
        elif n.get('content'):
            out.append(_inline(n['content'], ids))
    return ''.join(out)


def _marked(n: dict) -> str:
    txt = n.get('text', '')
    kinds = {m.get('type') for m in n.get('marks', [])}
    href = next((m.get('attrs', {}).get('href') for m in n.get('marks', [])
                 if m.get('type') == 'link'), None)
    if 'code' in kinds:
        txt = f'`{txt}`'
    if 'strong' in kinds and 'em' in kinds:
        txt = f'***{txt}***'
    elif 'strong' in kinds:
        txt = f'**{txt}**'
    elif 'em' in kinds:
        txt = f'*{txt}*'
    if href:
        txt = f'[{txt}]({href})'
    return txt
