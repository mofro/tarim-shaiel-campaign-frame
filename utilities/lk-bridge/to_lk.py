#!/usr/bin/env python3
"""
Vault Markdown → LegendKeeper import file.

Usage:
    # arbitrary files
    python utilities/lk-bridge/to_lk.py narrative/lore/liberation_aftermath.md \
        world/regions/tarim-basin.md --audience gm --lk -o roundtrip/test.json

    # directory scope (recursive; scope guards applied)
    python utilities/lk-bridge/to_lk.py narrative world --audience gm \
        -o roundtrip/full-export.json --lk

Audience modes (see README.md secrets mapping):
    gm     — full mirror: GM constructs become LK block-secret sections;
             page-level gm_secrets files become hidden resources (default)
    player — public-HTML parity: all GM content stripped; gm_secrets files
             excluded entirely

Scope guards (directory mode): Index.md / _category.md skipped; default-excluded
subtrees (world/abilities, world/classes — SRD reference data) need --include-all.
Never writes to any vault file. Warnings go to stderr and the manifest.
"""

import sys
import json
import argparse
from pathlib import Path

BRIDGE_DIR = Path(__file__).parent
VAULT = BRIDGE_DIR.parent.parent
sys.path.insert(0, str(BRIDGE_DIR))
sys.path.insert(0, str(BRIDGE_DIR.parent))

import lk_schema as lk
import md_to_pm
from shared.frontmatter import parse_frontmatter

SKIP_NAMES = {'Index.md', '_category.md'}
DEFAULT_EXCLUDE_SUBTREES = ('world/abilities', 'world/classes')
POS_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def collect_files(paths: list[str], include_all: bool) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = (VAULT / p) if not Path(p).is_absolute() else Path(p)
        if path.is_file():
            files.append(path)
            continue
        if not path.is_dir():
            print(f"WARNING: {p} not found — skipped", file=sys.stderr)
            continue
        for md in sorted(path.rglob('*.md')):
            rel = md.relative_to(VAULT).as_posix()
            if md.name in SKIP_NAMES:
                continue
            if not include_all and rel.startswith(DEFAULT_EXCLUDE_SUBTREES):
                continue
            files.append(md)
    # dedupe, keep order
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def is_gm_page(fm: dict, rel: str) -> bool:
    """Fails-closed, mirroring the HTML pipeline's narrow allowlist: only an
    explicit ``visibility: public`` is player-visible. Any other value —
    gm_secrets, internal, a typo like gm_only, or a missing field — is
    GM-side (hidden in gm mode, excluded in player mode)."""
    return fm.get('visibility') != 'public' or '/gm_secrets/' in f'/{rel}'


def pos_for(index: int) -> str:
    """Fractional-index style position: A, B, ..., Z, ZA, ZB, ..."""
    out = ''
    while True:
        out = POS_ALPHABET[index % 26] + out if not out else out
        prefix = index // 26
        if prefix == 0:
            return ('Z' * (len(out) - 1)) + out if len(out) > 1 else out
        index = index % 26
        return 'Z' * prefix + POS_ALPHABET[index]


def main() -> None:
    ap = argparse.ArgumentParser(description="Vault Markdown → LK import file")
    ap.add_argument('paths', nargs='+', help="Vault files and/or directories")
    ap.add_argument('--audience', choices=['gm', 'player'], default='gm')
    ap.add_argument('-o', '--output', required=True, help="Output .json path")
    ap.add_argument('--lk', action='store_true', help="Also write gzip .lk beside the .json")
    ap.add_argument('--include-all', action='store_true',
                    help="Include default-excluded subtrees (world/abilities, world/classes)")
    ap.add_argument('--hub-name', default=None,
                    help="Name for the auto-generated hub parent page")
    ap.add_argument('--manifest', default=str(BRIDGE_DIR / 'lk_manifest.json'),
                    help="Provisional-ID manifest output path")
    args = ap.parse_args()

    out_path = Path(args.output)
    if out_path.resolve().is_relative_to(VAULT) and not \
            out_path.resolve().is_relative_to(BRIDGE_DIR):
        # allow only bridge-internal output dirs inside the vault
        for content_root in ('world', 'narrative', 'mechanics', 'characters'):
            if out_path.resolve().is_relative_to(VAULT / content_root):
                sys.exit(f"REFUSED: output path {out_path} is inside vault content")

    files = collect_files(args.paths, args.include_all)
    if not files:
        sys.exit("No files collected.")

    gm_mode = args.audience == 'gm'

    # ── pass 1: read all files, build the link-resolution index ────────────
    entries = []          # (rel, fm, body, res_id, is_gm)
    by_stem = {}          # lowercase stem → (res_id, title)
    by_rel = {}           # vault-relative path (no ext) → (res_id, title)
    for f in files:
        try:
            rel = f.relative_to(VAULT).as_posix()
        except ValueError:
            rel = f.name          # file outside the vault (tests, ad-hoc input)
        raw = f.read_text(errors='ignore')
        fm, body = parse_frontmatter(raw)
        gm_page = is_gm_page(fm, rel)
        if gm_page and not gm_mode:
            continue                      # player export: excluded entirely
        title = str(fm.get('title') or f.stem)
        res_id = lk.short_id(rel)
        entries.append((rel, fm, body, res_id, gm_page))
        by_stem[f.stem.lower()] = (res_id, title)
        by_rel[rel[:-3].lower()] = (res_id, title)

    def resolve_link(target: str):
        t = target.strip().strip('/')
        if t.lower().endswith('.md'):
            t = t[:-3]
        return by_rel.get(t.lower()) or by_stem.get(t.rsplit('/', 1)[-1].lower())

    # ── pass 2: build directory-hierarchy resources ────────────────────────
    hub_name = args.hub_name or f"LK Bridge Import {lk.now_iso()[:10]}"
    hub_id = lk.short_id(f"hub:{hub_name}")
    resources = []
    dir_ids: dict[str, str] = {}
    warnings: list[str] = []
    old_schema: list[str] = []

    def dir_resource(rel_dir: str) -> str:
        """Get/create a folder resource chain for rel_dir; return its ID."""
        if not rel_dir or rel_dir == '.':
            return hub_id
        if rel_dir in dir_ids:
            return dir_ids[rel_dir]
        parent = dir_resource(str(Path(rel_dir).parent))
        rid = lk.short_id(f"dir:{rel_dir}")
        name = Path(rel_dir).name.replace('_', ' ').replace('-', ' ').title()
        hidden = 'gm_secrets' in Path(rel_dir).parts
        resources.append(lk.resource(
            rid, name, parent, [lk.doc(lk.short_id(f"dirdoc:{rel_dir}"),
                                       [lk.para(f"Section: {rel_dir}")])],
            tags=['section'], pos=pos_for(len(resources)),
            is_hidden=hidden, icon_glyph="fas fa-folder"))
        dir_ids[rel_dir] = rid
        return rid

    # ── pass 3: convert every file ──────────────────────────────────────────
    manifest_resources = {}
    for idx, (rel, fm, body, res_id, gm_page) in enumerate(entries):
        title = str(fm.get('title') or Path(rel).stem)
        if not fm.get('doc_type') and fm.get('type'):
            old_schema.append(rel)
        result = md_to_pm.convert(body, audience=args.audience,
                                  resolve_link=resolve_link, source=rel)
        warnings.extend(result.warnings)
        tags = []
        for key in ('domain', 'content_type'):
            v = fm.get(key)
            if isinstance(v, str) and v:
                tags.append(v)
        fmtags = fm.get('tags')
        if isinstance(fmtags, list):
            tags.extend(str(t) for t in fmtags[:6])
        if gm_page and 'gm-secret' not in tags:
            tags.append('gm-secret')
        parent = dir_resource(str(Path(rel).parent))
        resources.append(lk.resource(
            res_id, title, parent,
            [lk.doc(lk.short_id(f"doc:{rel}"), result.nodes or [lk.para()])],
            tags=tags, pos=pos_for(idx), is_hidden=gm_page))
        manifest_resources[rel] = {
            "provisionalId": res_id, "lkId": None, "lkName": title,
            "gm": gm_page,
        }

    # hub page with mentions to top-level sections
    top_mentions = []
    for rel_dir, rid in sorted(dir_ids.items()):
        if str(Path(rel_dir).parent) in ('.', ''):
            name = Path(rel_dir).name.title()
            top_mentions.append(lk.para("• ", lk.mention(rid, name)))
    hub_doc_nodes = [
        lk.heading(hub_name, 1),
        lk.para(f"Generated from vault by lk-bridge to_lk.py — audience: {args.audience}. "
                f"{len(entries)} pages."),
    ] + top_mentions
    resources.insert(0, lk.resource(
        hub_id, hub_name, "", [lk.doc(lk.short_id(f"hubdoc:{hub_name}"), hub_doc_nodes)],
        tags=['lk-bridge'], pos="A", icon_glyph="fas fa-compass"))

    export = lk.envelope(resources, export_id=lk.short_id(f"exp:{hub_name}"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    lk.write_export(export, out_path)
    if args.lk:
        lk.write_export(export, out_path.with_suffix('.lk'), as_lk=True)

    manifest = {
        "generation": {"exportId": export["exportId"], "capturedAt": export["exportedAt"],
                       "note": "lkId fields are filled by manifest.py from an LK re-export; "
                               "LK reassigns IDs on import."},
        "resources": manifest_resources,
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=1))

    print(f"Export written: {out_path}" + (f" (+ .lk)" if args.lk else ""))
    print(f"  resources: {len(resources)} ({len(entries)} pages, "
          f"{len(dir_ids)} sections, 1 hub)")
    print(f"  audience:  {args.audience}")
    if old_schema:
        print(f"  old-schema files tolerated: {len(old_schema)}")
    if warnings:
        print(f"  conversion warnings: {len(warnings)} (first 20 below)", file=sys.stderr)
        for w in warnings[:20]:
            print(f"    ⚠ {w}", file=sys.stderr)
    print(f"  manifest:  {args.manifest}")


if __name__ == '__main__':
    main()
