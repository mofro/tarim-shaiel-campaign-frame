#!/usr/bin/env python3
"""
Retype: change the `type:` of many location pages from one sheet (#336).

A page's Type decides its pin (see categories.py), so sorting pins into the right
Type is a content job done in bulk. This writes `type:` and `last_updated:` and
nothing else; the page body and every other field are left as they are.

    venv/bin/python utilities/map.py retype <sheet.csv> --dry-run
    venv/bin/python utilities/map.py retype <sheet.csv> [--confirm-canon]

The sheet is a CSV with a header row and these columns (others are ignored, so an
annotated report can be passed back as it is):

    slug   the page's file name without `.md`
    type   the Type to write: one of the listed Types in categories.py (blank = skip)
    from   optional. The Type the page has now. A page that has moved on since the
           sheet was made is refused, so a stale sheet never overwrites newer work.

Nothing is written unless every row passes: a bad row stops the whole run and is
named. A page already at the new Type is left alone and counted.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(VAULT_ROOT / "utilities"))

from locations import location_parser  # noqa: E402
from locations.categories import CATEGORIES, VALID_CATEGORIES  # noqa: E402

DEFAULT_LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"


class RetypeError(Exception):
    pass


def read_sheet(path: Path) -> list[dict]:
    """Rows of the sheet as dicts keyed by column name."""
    text = Path(path).read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames or []
    missing = [c for c in ("slug", "type") if c not in fields]
    if missing:
        raise RetypeError(f"{path}: the header row needs a `slug` and a `type` column "
                          f"(missing: {', '.join(missing)})")
    return [dict(r) for r in reader]


def plan_changes(rows: list[dict], locations_dir: Path, *,
                 confirm_canon: bool) -> tuple[list[dict], int, int, list[str]]:
    """Validate every row; return (changes, skipped, unchanged, errors). Writes nothing."""
    import devserver  # the same frontmatter edit path as the Workshop's Save

    changes, errors = [], []
    skipped = unchanged = 0
    seen = set()
    for row in rows:
        slug = str(row.get("slug") or "").strip()
        new_type = str(row.get("type") or "").strip()
        if not slug and not new_type:
            continue
        if not new_type:
            skipped += 1
            continue
        try:
            if not slug:
                raise RetypeError(f"a row has type “{new_type}” but no slug")
            if new_type not in VALID_CATEGORIES:
                raise RetypeError(f"{slug}: “{new_type}” is not a Type "
                                  f"(use one of: {', '.join(CATEGORIES)})")
            if slug in seen:
                raise RetypeError(f"{slug}: appears more than once")
            seen.add(slug)
            path = Path(locations_dir) / f"{slug}.md"
            if not path.exists():
                raise RetypeError(f"{slug}: no such location file")
            old = path.read_text(encoding="utf-8")
            fm, _ = location_parser._parse_fm(old)
            if not fm:
                raise RetypeError(f"{slug}: the file has no frontmatter")
            current = str(fm.get("type") or "").strip()
            expected = str(row.get("from") or "").strip()
            if expected and expected != current:
                raise RetypeError(f"{slug}: stale row — the file's type is “{current}”, not "
                                  f"“{expected}”; make the sheet again")
            if str(fm.get("status", "")).strip().lower() == "canon" and not confirm_canon:
                raise RetypeError(f"{slug}: canon file — re-run with --confirm-canon to change it")
            if current == new_type:
                unchanged += 1
                continue
            new = devserver._set_frontmatter_fields(old, {"type": new_type})  # bumps last_updated
            changes.append({"slug": slug, "path": path, "old": old, "new": new,
                            "from": current, "to": new_type})
        except RetypeError as exc:
            errors.append(str(exc))
    return changes, skipped, unchanged, errors


def apply_sheet(sheet: Path, locations_dir: Path, *, dry_run: bool, confirm_canon: bool,
                out=print) -> int:
    """Print the diff per changed page and write it unless dry_run. 0 ok, 2 on any error."""
    from locations.coord_audit import diff_text, write_atomic  # shared with the coordinate audit

    try:
        rows = read_sheet(sheet)
    except (RetypeError, OSError) as exc:
        out(f"Nothing was written. {exc}")
        return 2
    changes, skipped, unchanged, errors = plan_changes(rows, locations_dir,
                                                       confirm_canon=confirm_canon)
    if errors:
        out("Nothing was written. Fix these rows and run again:")
        for e in errors:
            out(f"  - {e}")
        return 2
    base = Path(locations_dir).parent.parent
    for ch in changes:
        out(diff_text(ch, base).rstrip("\n"))
    if not dry_run:
        for ch in changes:
            write_atomic(ch["path"], ch["new"])
    verb = "would change" if dry_run else "changed"
    out(f"\n{verb} {len(changes)} file(s); {unchanged} already at that Type; "
        f"{skipped} row(s) skipped (blank type).")
    if changes and not dry_run:
        out("Rebuild next: venv/bin/python utilities/map.py rebuild")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="map.py retype", description=__doc__.split("\n\n")[0])
    ap.add_argument("sheet", metavar="SHEET", help="CSV with `slug` and `type` columns")
    ap.add_argument("--dry-run", action="store_true", help="print the diffs, write nothing")
    ap.add_argument("--confirm-canon", action="store_true",
                    help="allow changes to files marked status: canon")
    ap.add_argument("--locations-dir", default=str(DEFAULT_LOCATIONS_DIR))
    args = ap.parse_args(argv)
    return apply_sheet(Path(args.sheet), Path(args.locations_dir),
                       dry_run=args.dry_run, confirm_canon=args.confirm_canon)


if __name__ == "__main__":
    sys.exit(main())
