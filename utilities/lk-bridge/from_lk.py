#!/usr/bin/env python3
"""
LegendKeeper export → Schema C Markdown files.

Usage:
    python utilities/lk-bridge/from_lk.py roundtrip/lk-reexport.json \
        --out roundtrip/post-lk/

Safety: REFUSES to write inside vault content roots (world/, narrative/,
mechanics/, characters/, templates/) — output goes to a scratch directory and
is merged into the vault by a human, never by this tool.

Frontmatter: emits Schema C (never legacy ``type:``). When a manifest
(lk_manifest.json) maps the resource back to a vault path, the original path
and gm-flag are honored; otherwise defaults apply (domain: narrative,
doc_type: canon, content_type: lore, status: draft).
"""

import re
import sys
import json
import gzip
import argparse
from datetime import date
from pathlib import Path

BRIDGE_DIR = Path(__file__).parent
VAULT = BRIDGE_DIR.parent.parent
sys.path.insert(0, str(BRIDGE_DIR))

import pm_to_md

CONTENT_ROOTS = ('world', 'narrative', 'mechanics', 'characters', 'templates')
SKIP_TAGS = {'section', 'lk-bridge'}      # bridge-generated scaffolding resources


def load_export(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw)


def safe_out_dir(out: Path) -> Path:
    out = out.resolve()
    for root in CONTENT_ROOTS:
        content_root = (VAULT / root).resolve()
        if out == content_root or out.is_relative_to(content_root):
            sys.exit(f"REFUSED: --out {out} is inside vault content root {content_root}. "
                     f"Write to a scratch directory and merge manually.")
    return out


def slugify(name: str) -> str:
    slug = re.sub(r'[^\w\- ]+', '', name).strip().replace(' ', '_')
    return slug or 'untitled'


def main() -> None:
    ap = argparse.ArgumentParser(description="LK export → Schema C Markdown")
    ap.add_argument('export_file')
    ap.add_argument('--out', required=True, help="Scratch output directory")
    ap.add_argument('--manifest', default=str(BRIDGE_DIR / 'lk_manifest.json'))
    ap.add_argument('--include-scaffolding', action='store_true',
                    help="Also emit bridge-generated hub/section resources")
    args = ap.parse_args()

    out_dir = safe_out_dir(Path(args.out))
    export = load_export(Path(args.export_file))

    manifest = {}
    mpath = Path(args.manifest)
    if mpath.exists():
        try:
            manifest = json.loads(mpath.read_text())
        except Exception:
            pass
    # provisional-ID → vault rel path (from to_lk run); lkId → path (post-capture)
    id_to_vaultpath = {}
    for rel, entry in (manifest.get('resources') or {}).items():
        for key in ('provisionalId', 'lkId'):
            if entry.get(key):
                id_to_vaultpath[entry[key]] = rel

    id_to_name = {r['id']: r['name'] for r in export.get('resources', [])}
    today = date.today().isoformat()
    written, skipped = 0, 0

    for r in export.get('resources', []):
        tags = r.get('tags') or []
        if not args.include_scaffolding and (set(tags) & SKIP_TAGS):
            skipped += 1
            continue
        pages = [d for d in r.get('documents', [])
                 if d.get('type') == 'page' and (d.get('content') or {}).get('type')]
        if not pages:
            skipped += 1
            continue

        body = '\n\n'.join(
            pm_to_md.doc_to_markdown(d['content'], id_to_name) for d in pages).strip()

        gm = bool(r.get('isHidden')) or 'gm-secret' in tags
        vault_rel = id_to_vaultpath.get(r['id'])
        if vault_rel:
            rel_out = Path(vault_rel)
            entry = (manifest.get('resources') or {}).get(vault_rel, {})
            gm = gm or entry.get('gm', False)
        else:
            rel_out = Path(slugify(r['name']) + '.md')

        content_tags = [t for t in tags if t not in SKIP_TAGS and t != 'gm-secret']
        fm_lines = [
            '---',
            f'title: "{r["name"]}"',
            'project: TTRPG_Tarim_Shaiel',
            f'domain: {content_tags[0] if content_tags else "narrative"}',
            'doc_type: canon',
            f'content_type: {content_tags[1] if len(content_tags) > 1 else "lore"}',
            f'visibility: {"gm_secrets" if gm else "public"}',
            'status: draft',
            f'created: {today}',
            f'last_updated: {today}',
            f'tags: [{", ".join(content_tags[2:])}]',
            f'lk_id: {r["id"]}',
            '---',
            '',
        ]
        target = out_dir / rel_out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('\n'.join(fm_lines) + body + '\n')
        written += 1

    print(f"Wrote {written} file(s) to {out_dir} ({skipped} scaffolding/empty skipped)")


if __name__ == '__main__':
    main()
