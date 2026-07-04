#!/usr/bin/env python3
"""
Obsidian Markdown → LK ProseMirror (ADF-dialect) converter.

Implements the vault↔LK mapping table (utilities/lk-bridge/README.md, GH #213),
including the GM-secrets mapping switched by ``audience``:

  audience="player": Tier 1 → ██████ literal; Tier 2 / Tier 3 / %%..%% stripped
  audience="gm":     Tier 1 → literal passthrough; Tier 2 → block-secret "GM [id=x]";
                     Tier 3 → block-secret "GM embed: <path>" (marker only);
                     %%..%% → block-secret "GM comment"

Quirk-audit verdicts (2026-07-03 census): leaflet/dataview/mermaid code fences
skip with a warning; daggerheart fences render as code-marked paragraphs;
unknown-target wikilinks degrade to plain text; image/audio embeds skip with a
warning (CDN upload is API-gated); ==highlight==/~~strike~~ degrade to em/plain.

Never writes any file — pure text → node-list transformation.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lk_schema as lk

# fences whose content cannot execute in LK → skip with warning
SKIP_FENCE_LANGS = {'leaflet', 'dataview', 'mermaid'}

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}


class ConversionResult:
    def __init__(self, nodes: list, warnings: list):
        self.nodes = nodes
        self.warnings = warnings


def convert(body: str, *, audience: str, resolve_link, source: str = "?") -> ConversionResult:
    """Convert a Markdown body to a list of ProseMirror block nodes.

    resolve_link(target: str) -> (res_id, name) | None
        Maps a wikilink target (path or stem, no alias/anchor) to an export-set
        resource. None → degrade to plain text.
    """
    warnings: list[str] = []

    def warn(msg: str) -> None:
        warnings.append(f"{source}: {msg}")

    blocks = _split_blocks(body, audience, warn)
    nodes: list[dict] = []
    for kind, payload in blocks:
        produced = _render_block(kind, payload, audience, resolve_link, warn)
        nodes.extend(produced)
    return ConversionResult(nodes, warnings)


# ── block splitting ──────────────────────────────────────────────────────────

def _split_blocks(body: str, audience: str, warn) -> list:
    """Tokenize into (kind, payload) blocks; GM constructs isolated here."""
    out = []
    # 1. %%...%% comments (multiline + inline) — pull out before anything else
    def _pct(m):
        content = m.group(1).strip()
        if content:
            out_marker = f"\x00PCT{len(_pct_store)}\x00"
            _pct_store.append(content)
            return out_marker
        return ''
    _pct_store: list[str] = []
    body = re.sub(r'%%(.*?)%%', _pct, body, flags=re.DOTALL)

    # 2. fenced code blocks
    fence_re = re.compile(r'^(```|~~~)([^\n`]*)\n(.*?)^\1\s*$\n?', re.M | re.S)
    segments: list[tuple[str, object]] = []
    pos = 0
    for m in fence_re.finditer(body):
        if m.start() > pos:
            segments.append(('md', body[pos:m.start()]))
        segments.append(('fence', (m.group(2).strip().lower(), m.group(3))))
        pos = m.end()
    segments.append(('md', body[pos:]))

    # 3. within md segments: line-group parsing
    for seg_kind, seg in segments:
        if seg_kind == 'fence':
            out.append(('fence', seg))
            continue
        lines = seg.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                i += 1
                continue
            if stripped.startswith('\x00PCT'):
                idx = int(stripped[4:-1])
                out.append(('pct', _pct_store[idx]))
                i += 1
                continue
            m = re.match(r'^#{1,6} ', stripped)
            if m:
                level = len(stripped) - len(stripped.lstrip('#'))
                out.append(('heading', (min(level, 6), stripped[level:].strip())))
                i += 1
                continue
            if re.match(r'^(---|\*\*\*|___)\s*$', stripped):
                out.append(('hrule', None))
                i += 1
                continue
            if stripped.startswith('>'):
                # gather the quote/callout run
                run = []
                while i < len(lines) and lines[i].strip().startswith('>'):
                    run.append(re.sub(r'^\s*>\s?', '', lines[i]))
                    i += 1
                head = run[0].strip() if run else ''
                cm = re.match(r'^\[!([\w-]+)[+-]?\]\s*(?:id=(\S+))?\s*(.*)$', head)
                if cm:
                    out.append(('callout', (cm.group(1).lower(), cm.group(2) or '',
                                            ([cm.group(3)] if cm.group(3) else []) + run[1:])))
                else:
                    out.append(('blockquote', run))
                continue
            if re.match(r'^\s*- \[[ xX/-]\] ', line):
                run = []
                while i < len(lines) and re.match(r'^\s*- \[[ xX/-]\] ', lines[i]):
                    mm = re.match(r'^\s*- \[([ xX/-])\] (.*)$', lines[i])
                    run.append((mm.group(1).lower() == 'x', mm.group(2)))
                    i += 1
                out.append(('tasklist', run))
                continue
            if re.match(r'^\s*[-*+] ', line):
                run = []
                while i < len(lines) and re.match(r'^\s*[-*+] ', lines[i]):
                    run.append(re.sub(r'^\s*[-*+] ', '', lines[i]))
                    i += 1
                out.append(('bullets', run))
                continue
            if re.match(r'^\s*\d+\. ', line):
                run = []
                while i < len(lines) and re.match(r'^\s*\d+\. ', lines[i]):
                    run.append(re.sub(r'^\s*\d+\. ', '', lines[i]))
                    i += 1
                out.append(('ordered', run))
                continue
            if stripped.startswith('|') and i + 1 < len(lines) \
                    and re.match(r'^\|[\s:|-]+\|\s*$', lines[i + 1].strip()):
                run = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    run.append(lines[i].strip())
                    i += 1
                out.append(('table', run))
                continue
            # standalone embed line?
            if re.fullmatch(r'!\[\[[^\]]+\]\]', stripped):
                out.append(('embed', stripped[3:-2]))
                i += 1
                continue
            # paragraph: gather until blank/structural line
            run = [line]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                ns = nxt.strip()
                if (not ns or ns.startswith(('>', '#', '|', '\x00PCT'))
                        or re.match(r'^\s*([-*+]|\d+\.) ', nxt)
                        or re.match(r'^(---|\*\*\*|___)\s*$', ns)
                        or re.fullmatch(r'!\[\[[^\]]+\]\]', ns)):
                    break
                run.append(nxt)
                i += 1
            out.append(('para', ' '.join(l.strip() for l in run)))
    return out


# ── block rendering ──────────────────────────────────────────────────────────

def _render_block(kind, payload, audience, resolve_link, warn) -> list:
    gm = audience == 'gm'

    if kind == 'heading':
        level, txt = payload
        return [lk.heading(_inline(txt, audience, resolve_link, warn), level)]

    if kind == 'hrule':
        return [lk.rule()]

    if kind == 'para':
        inline = _inline(payload, audience, resolve_link, warn)
        return [lk.para(*inline)] if inline else []

    if kind == 'blockquote':
        paras = [lk.para(*_inline(l, audience, resolve_link, warn))
                 for l in payload if l.strip()]
        return [lk.blockquote(*paras)] if paras else []

    if kind == 'callout':
        ctype, cid, body_lines = payload
        inner = _lines_to_blocks(body_lines, audience, resolve_link, warn)
        if ctype == 'gm-only':
            if not gm:
                return []                                   # player: stripped
            title = f"GM id={cid}" if cid else "GM"
            return [lk.secret_block(inner or [lk.para()], title)]
        panel_type = {'info': 'info', 'note': 'note', 'tip': 'success',
                      'success': 'success', 'important': 'warning',
                      'warning': 'warning', 'danger': 'warning',
                      'caution': 'warning'}.get(ctype, 'note')
        return [lk.panel(panel_type, *(inner or [lk.para()]))]

    if kind == 'pct':
        if not gm:
            return []                                       # player: stripped
        inner = _lines_to_blocks(payload.split('\n'), audience, resolve_link, warn)
        return [lk.secret_block(inner or [lk.para()], "GM comment")]

    if kind == 'tasklist':
        items = [(done, _inline(t, audience, resolve_link, warn))
                 for done, t in payload]
        return [lk.task_list(items)]

    if kind == 'bullets':
        return [lk.bullet_list([lk.para(*_inline(t, audience, resolve_link, warn))
                                for t in payload])]

    if kind == 'ordered':
        return [lk.ordered_list([lk.para(*_inline(t, audience, resolve_link, warn))
                                 for t in payload])]

    if kind == 'table':
        rows = []
        for li, line in enumerate(payload):
            if li == 1:
                continue                                    # separator row
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append([[lk.para(*_inline(c, audience, resolve_link, warn))]
                         if c else [lk.para()] for c in cells])
        return [lk.table(rows)] if rows else []

    if kind == 'fence':
        lang, code = payload
        lang = lang or '(none)'
        if lang in SKIP_FENCE_LANGS:
            warn(f"```{lang} block skipped (no LK equivalent this round)")
            return []
        # daggerheart stat blocks + generic fences → code-marked paragraphs
        # (LK block-code node unverified — see manual checklist, GH #213)
        code_paras = [lk.para(lk.text(l, [lk.mark('code')]))
                      for l in code.rstrip('\n').split('\n')]
        if lang == 'daggerheart':
            warn("```daggerheart stat block rendered as code-marked paragraphs")
        return code_paras

    if kind == 'embed':
        return _render_embed(payload, audience, resolve_link, warn)

    return []


def _render_embed(inner: str, audience: str, resolve_link, warn) -> list:
    gm = audience == 'gm'
    target = inner.split('|')[0].strip()
    label = inner.split('|')[1].strip() if '|' in inner else Path(target).stem
    ext = Path(target).suffix.lower()

    if target.startswith('gm_secrets/') or '/gm_secrets/' in target:
        if not gm:
            return []                                       # player: stripped
        # Tier 3: marker only — vault file remains the single source of truth
        path = target if target.endswith('.md') else target + '.md'
        marker = [lk.para(f"[GM content lives in vault file {path} — not inlined]")]
        resolved = resolve_link(target)
        if resolved:
            res_id, name = resolved
            marker.append(lk.para("See hidden page: ", lk.mention(res_id, name)))
        return [lk.secret_block(marker, f"GM embed: {path}")]

    if ext in IMG_EXTS:
        warn(f"image embed ![[{inner}]] skipped (vault→CDN upload is API-gated)")
        return []
    if ext in AUDIO_EXTS:
        warn(f"audio embed ![[{inner}]] rendered as label (CDN upload API-gated)")
        return [lk.para(lk.text(f"♪ {label}", [lk.mark('em')]))]
    if '#' in inner:
        base = target.split('#')[0]
        resolved = resolve_link(base)
        warn(f"section transclusion ![[{inner}]] rendered as link (not inlined)")
        if resolved:
            res_id, name = resolved
            return [lk.para("→ ", lk.mention(res_id, name, alias=label))]
        return [lk.para(lk.text(f"→ {label}", [lk.mark('em')]))]
    # whole-note transclusion of a public note → mention link
    resolved = resolve_link(target)
    warn(f"note transclusion ![[{inner}]] rendered as link (not inlined)")
    if resolved:
        res_id, name = resolved
        return [lk.para("→ ", lk.mention(res_id, name, alias=label))]
    return [lk.para(lk.text(f"→ {label}", [lk.mark('em')]))]


def _lines_to_blocks(lines: list, audience: str, resolve_link, warn) -> list:
    """Render a run of plain lines (callout / %% body) grouping list items."""
    blocks: list[dict] = []
    bullets: list[str] = []

    def flush():
        nonlocal bullets
        if bullets:
            blocks.append(lk.bullet_list(
                [lk.para(*_inline(b, audience, resolve_link, warn)) for b in bullets]))
            bullets = []

    for line in lines:
        s = line.strip()
        if not s:
            continue
        m = re.match(r'^[-*+] (.*)$', s)
        if m:
            bullets.append(m.group(1))
        else:
            flush()
            blocks.append(lk.para(*_inline(s, audience, resolve_link, warn)))
    flush()
    return blocks


# ── inline rendering ─────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(
    r'(?P<embed>!\[\[[^\]]+\]\])'
    r'|(?P<wikilink>\[\[[^\]]+\]\])'
    r'|(?P<mdlink>\[[^\]]*\]\([^)]+\))'
    r'|(?P<bolditalic>\*\*\*[^*]+\*\*\*)'
    r'|(?P<bold>\*\*[^*]+\*\*)'
    r'|(?P<italic_star>\*[^*\s][^*]*\*)'
    r'|(?P<italic_us>(?<![\w])_[^_]+_(?![\w]))'
    r'|(?P<code>`[^`]+`)'
    r'|(?P<strike>~~[^~]+~~)'
    r'|(?P<highlight>==[^=]+==)'
    r'|(?P<gm>\{gm:[^}]*\})'
    r'|(?P<br><br\s*/?>)'
)


def _inline(txt: str, audience: str, resolve_link, warn, marks=None) -> list:
    """Convert inline markdown to a list of inline nodes."""
    marks = marks or []
    nodes: list[dict] = []
    pos = 0
    for m in _TOKEN_RE.finditer(txt):
        if m.start() > pos:
            _push_text(nodes, txt[pos:m.start()], marks)
        g = m.lastgroup
        s = m.group(0)
        if g == 'gm':
            content = s[4:-1]
            if audience == 'gm':
                _push_text(nodes, s, marks)           # literal passthrough
            else:
                _push_text(nodes, '██████', marks)    # public-HTML parity
        elif g == 'wikilink':
            inner = s[2:-2]
            anchor = ''
            target = inner.split('|')[0].strip()
            alias = inner.split('|')[1].strip() if '|' in inner else ''
            if '#' in target:
                target, anchor = target.split('#', 1)
                target = target.strip()
            resolved = resolve_link(target) if target else None
            if resolved:
                res_id, name = resolved
                if anchor:
                    warn(f"[[{inner}]] heading anchor dropped (mention links whole page)")
                nodes.append(lk.mention(res_id, name, alias=alias))
            else:
                nodes.append(lk.text(alias or target or inner))
        elif g == 'embed':
            # inline embeds inside a paragraph: same policy as block embeds,
            # but flatten to inline (images/audio → label text)
            sub = _render_embed(s[3:-2], audience, resolve_link, warn)
            for blk in sub:
                nodes.extend(blk.get('content', []))
        elif g == 'mdlink':
            mm = re.match(r'\[([^\]]*)\]\(([^)]+)\)', s)
            label, href = mm.group(1), mm.group(2)
            if href.startswith(('http://', 'https://', 'mailto:')):
                nodes.append(lk.text(label or href, marks + [lk.link_mark(href)]))
            else:
                nodes.append(lk.text(label or href, marks))  # internal md link → text
        elif g == 'bolditalic':
            _push_text(nodes, s[3:-3], marks + [lk.mark('strong'), lk.mark('em')])
        elif g == 'bold':
            nodes.extend(_inline(s[2:-2], audience, resolve_link, warn,
                                 marks + [lk.mark('strong')]))
        elif g in ('italic_star', 'italic_us'):
            nodes.extend(_inline(s[1:-1], audience, resolve_link, warn,
                                 marks + [lk.mark('em')]))
        elif g == 'code':
            _push_text(nodes, s[1:-1], marks + [lk.mark('code')])
        elif g == 'strike':
            warn("~~strikethrough~~ degraded to plain text (no LK mark)")
            _push_text(nodes, s[2:-2], marks)
        elif g == 'highlight':
            warn("==highlight== degraded to emphasis (no LK mark)")
            _push_text(nodes, s[2:-2], marks + [lk.mark('em')])
        elif g == 'br':
            nodes.append(lk.hard_break())
        pos = m.end()
    if pos < len(txt):
        _push_text(nodes, txt[pos:], marks)
    return nodes


def _push_text(nodes: list, t: str, marks: list) -> None:
    if t:
        nodes.append(lk.text(t, list(marks) if marks else None))
