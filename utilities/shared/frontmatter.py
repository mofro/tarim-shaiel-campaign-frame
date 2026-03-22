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

    if _YAML_AVAILABLE:
        try:
            fm = yaml.safe_load(fm_text) or {}
        except Exception:
            fm = {}
    else:
        fm = {}
        for line in fm_text.splitlines():
            kv = line.split(':', 1)
            if len(kv) == 2:
                k, v = kv[0].strip(), kv[1].strip()
                fm[k] = v.strip('"\'')

    return fm, body
