"""
Visibility flag checker and read/set command (#394).

Every lore page carries `visibility:` in its frontmatter: public, gm_secrets or
internal. A missing or unrecognised value is reported here instead of being
guessed by each generator.

    python utilities/shared/visibility_check.py check [--strict]
    python utilities/shared/visibility_check.py show <file>
    python utilities/shared/visibility_check.py set <file> <public|gm_secrets|internal>

`check` warns and exits 0 unless --strict is given.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent

VALID = ("public", "gm_secrets", "internal")

# Directories whose Markdown is lore and must carry the flag.
SCAN_DIRS = ("world", "narrative", "characters", "mechanics", "templates")

# Never scanned: operational navigation files, generator-excluded stubs, archives.
SKIP_DIRS = {"archive", ".obsidian", ".meta", "node_modules"}

_FM_RE = re.compile(r"^---\n(.*?\n)---\n", re.DOTALL)

# Problem kinds
MISSING = "missing"
INVALID = "invalid"
NO_FRONTMATTER = "no-frontmatter"
BAD_YAML = "bad-yaml"


def _skipped(path: Path) -> bool:
    name = path.name
    if name == "_category.md" or name.startswith("zz"):
        return True
    return any(part in SKIP_DIRS for part in path.parts)


def lore_files(root: Path = VAULT_ROOT) -> list[Path]:
    files = []
    for d in SCAN_DIRS:
        base = root / d
        if base.is_dir():
            files.extend(p for p in sorted(base.rglob("*.md")) if not _skipped(p.relative_to(root)))
    return files


def read_visibility(text: str) -> tuple[str, object]:
    """Return (kind, value): kind is 'ok' or one of the problem kinds."""
    m = _FM_RE.match(text)
    if not m:
        return NO_FRONTMATTER, None
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return BAD_YAML, None
    if not isinstance(fm, dict):
        return BAD_YAML, None
    if "visibility" not in fm or fm["visibility"] in (None, ""):
        return MISSING, None
    value = fm["visibility"]
    if value not in VALID:
        return INVALID, value
    return "ok", value


def check(root: Path = VAULT_ROOT) -> list[tuple[Path, str, object]]:
    problems = []
    for p in lore_files(root):
        kind, value = read_visibility(p.read_text(encoding="utf-8"))
        if kind != "ok":
            problems.append((p.relative_to(root), kind, value))
    return problems


def set_visibility(text: str, value: str) -> str:
    """Return text with `visibility: value` set, touching only that line.

    Replaces an existing line in place; otherwise inserts after `title:` (or as the
    first frontmatter line). Raises ValueError for a bad value or no frontmatter.
    """
    if value not in VALID:
        raise ValueError(f"visibility must be one of {', '.join(VALID)}, not {value!r}")
    m = _FM_RE.match(text)
    if not m:
        raise ValueError("file has no frontmatter block")
    lines = m.group(1).split("\n")
    for i, ln in enumerate(lines):
        if re.match(r"visibility\s*:", ln):
            lines[i] = f"visibility: {value}"
            break
    else:
        at = 0
        for i, ln in enumerate(lines):
            if re.match(r"title\s*:", ln):
                at = i + 1
                break
        lines.insert(at, f"visibility: {value}")
    return "---\n" + "\n".join(lines) + "---\n" + text[m.end():]


def _resolve(arg: str) -> Path:
    p = Path(arg)
    return p if p.is_absolute() else (Path.cwd() / p)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="list lore files with a missing or invalid visibility")
    c.add_argument("--strict", action="store_true", help="exit 1 if any problem is found")
    s = sub.add_parser("show", help="print a file's visibility")
    s.add_argument("file")
    st = sub.add_parser("set", help="set a file's visibility")
    st.add_argument("file")
    st.add_argument("value", choices=VALID)
    args = ap.parse_args(argv)

    if args.cmd == "check":
        problems = check(VAULT_ROOT)
        for rel, kind, value in problems:
            detail = f" ({value!r})" if kind == INVALID else ""
            print(f"  WARN: {rel}: visibility {kind}{detail}", file=sys.stderr)
        total = len(lore_files(VAULT_ROOT))
        print(f"visibility: {total - len(problems)}/{total} lore files flagged, {len(problems)} to fix")
        return 1 if (problems and args.strict) else 0

    path = _resolve(args.file)
    if not path.is_file():
        print(f"ERROR: {args.file} not found", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    if args.cmd == "show":
        kind, value = read_visibility(text)
        print(value if kind == "ok" else f"({kind}{': ' + repr(value) if kind == INVALID else ''})")
        return 0 if kind == "ok" else 1
    try:
        new = set_visibility(text, args.value)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if new != text:
        path.write_text(new, encoding="utf-8")
    print(f"{args.file}: visibility: {args.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
