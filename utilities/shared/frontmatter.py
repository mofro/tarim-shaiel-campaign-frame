"""
Frontmatter parsing utilities.

Canonical implementation: YAML (if available) with key:value regex fallback.
Used by all generators that read Obsidian .md source files.
"""

import re

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def doc_type_of(fm: dict) -> str:
    """Resolve a document's legacy type label across schema generations.

    Schema C (Decision 17, 2026-05-02) replaced the single ``type:`` field with
    ``domain:`` / ``doc_type:`` / ``content_type:``. Consumers that still route
    on the old label (LK pipeline: myth/lore/timeline) should call this instead
    of ``fm.get('type')``: it prefers ``content_type:``, then ``doc_type:``,
    then falls back to legacy ``type:``. Always returns a lowercase string.
    """
    for key in ('content_type', 'doc_type', 'type'):
        value = fm.get(key)
        if value:
            return str(value).strip().lower()
    return ''


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text).

    Tries YAML parsing first (if pyyaml is installed), falls back to a simple
    key: value regex parser that handles all values as strings.
    Returns ({}, text) if no frontmatter block is present.
    """
    m = re.match(r'^---\n(.*?\n)---\n', text, re.DOTALL)
    if not m:
        return {}, text

    fm_text = m.group(1)
    body = text[m.end():]

    fm = None

    if _YAML_AVAILABLE:
        try:
            fm = yaml.safe_load(fm_text) or {}
        except Exception:
            pass  # fall through to regex parser

    if fm is None:
        fm = {}
        for line in fm_text.splitlines():
            kv = line.split(':', 1)
            if len(kv) == 2:
                k, v = kv[0].strip(), kv[1].strip()
                fm[k] = v.strip('"\'')

    return fm, body
