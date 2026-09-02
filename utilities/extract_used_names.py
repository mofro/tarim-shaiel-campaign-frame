#!/usr/bin/env python3
"""
Extract all committed character names from the Tarim-Shaiel vault.
Outputs utilities/used-names.json for import into the name generator artifact.

Usage:
    python3 utilities/extract_used_names.py

Reads:
    characters/PCs/*.md     — title: frontmatter field
    characters/NPCs/**/*.md — title: frontmatter, falls back to filename stem

Writes:
    utilities/used-names.json
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone

VAULT_ROOT  = Path(__file__).parent.parent
CHAR_DIR    = VAULT_ROOT / "characters"
OUTPUT_FILE = Path(__file__).parent / "used-names.json"

# Stems to skip — operational/template files, not real characters
SKIP_STEMS = {
    "untitled",
    "index",
    "archetypes",
    "character sheet prompts",
}


def read_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def collect_names() -> list[str]:
    seen:  set[str]  = set()
    names: list[str] = []

    for md in sorted(CHAR_DIR.rglob("*.md")):
        stem = md.stem

        # Skip operational files
        if stem.lower() in SKIP_STEMS:
            continue

        # Skip "(player)" duplicates — same character as the plain file
        if "(player)" in stem.lower():
            continue

        fm    = read_frontmatter(md)
        title = fm.get("title", "").strip()
        name  = title if title else stem

        # Skip empty results
        if not name or name.lower() in SKIP_STEMS:
            continue

        if name not in seen:
            seen.add(name)
            names.append(name)

    return sorted(names)


def main() -> None:
    names = collect_names()
    payload = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vault":     VAULT_ROOT.name,
        "count":     len(names),
        "names":     names,
    }
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✦ Extracted {len(names)} names → {OUTPUT_FILE.relative_to(VAULT_ROOT)}")
    for n in names:
        print(f"  {n}")


if __name__ == "__main__":
    main()
