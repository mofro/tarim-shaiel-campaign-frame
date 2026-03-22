"""
Asset resolution utilities for Obsidian-sourced HTML generators.

Handles finding image and audio files in the vault or docs/ directory
and copying them to the appropriate docs/ subdirectory for web serving.

All functions accept explicit `vault_root` and `docs_dir` Path parameters
so this module is not hardcoded to any particular project layout.
"""

import shutil
from pathlib import Path


def find_in_vault(fname: str, vault_root: Path) -> Path | None:
    """Search vault recursively for a file by name (Obsidian-style resolution).

    Returns the first match, or None if not found.
    """
    for candidate in vault_root.rglob(fname):
        if candidate.is_file():
            return candidate
    return None


def prepare_image(fname: str, vault_root: Path, docs_dir: Path) -> str | None:
    """Find an image by filename in the vault, copy to docs/images/, return relative URL."""
    src = find_in_vault(fname, vault_root)
    if src is None:
        print(f'  [image] WARNING: {fname!r} not found in vault')
        return None

    dest_dir = docs_dir / 'images'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname
    shutil.copy2(src, dest)
    print(f'  [image] Copied {src} → {dest}')
    return f'images/{fname}'


def prepare_audio(audio_field: str, vault_root: Path, docs_dir: Path) -> str | None:
    """Resolve an audio frontmatter field to a docs-relative URL.

    Resolution order:
      1. Search docs/ by filename (manually-placed files too large for the vault)
      2. Try vault-relative path and copy to docs/audio/
      3. Fail silently — no audio block rendered
    """
    if not audio_field:
        return None

    fname = Path(audio_field).name

    # 1. Search docs/ for an existing file with this name
    for candidate in docs_dir.rglob(fname):
        if candidate.is_file():
            rel = candidate.relative_to(docs_dir)
            print(f'  [audio] Found in docs/: {candidate}')
            return str(rel).replace('\\', '/')

    # 2. Try vault-relative path → copy to docs/audio/
    src = Path(audio_field)
    if not src.is_absolute():
        src = vault_root / src
    if src.exists():
        dest_dir = docs_dir / 'audio'
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / fname
        shutil.copy2(src, dest)
        print(f'  [audio] Copied to {dest}')
        return f'audio/{fname}'

    # 3. Fail silently
    print(f'  [audio] Not found, skipping player: {audio_field}')
    return None


def prepare_audio_wiki(fname: str, vault_root: Path, docs_dir: Path) -> str | None:
    """Resolve an inline ![[audio]] wiki-embed, ensuring the file is at docs/audio/.

    Resolution order:
      1. Search docs/ by filename — if not already at docs/audio/, copy it there
      2. Search vault by filename and copy to docs/audio/
      3. Fail silently
    """
    dest_dir = docs_dir / 'audio'
    dest = dest_dir / fname

    # 1. Search docs/ by filename
    for candidate in docs_dir.rglob(fname):
        if candidate.is_file():
            if candidate != dest:
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, dest)
                print(f'  [audio] Copied {candidate} → {dest}')
            else:
                print(f'  [audio] Already at {dest}')
            return f'audio/{fname}'

    # 2. Search vault by filename
    src = find_in_vault(fname, vault_root)
    if src is not None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f'  [audio] Copied {src} → {dest}')
        return f'audio/{fname}'

    # 3. Fail silently
    print(f'  [audio] WARNING: {fname!r} not found in docs/ or vault')
    return None
