"""
Markdown and Obsidian text utilities.

Inline markdown conversion plus Obsidian-specific sanitizers.
Used by all generators that process Obsidian .md source files.
"""

import re
from html import escape as html_escape


def inline_md(text: str) -> str:
    """Convert inline markdown to HTML (bold, italic, bold-italic).

    HTML-escapes the input first so caller does not need to pre-escape.
    """
    text = html_escape(text)
    text = re.sub(r'\*{3}(.+?)\*{3}', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    return text


def extract_secret_blocks(text: str) -> tuple[str, list[str]]:
    """Remove %% ... %% blocks and return (cleaned_text, [secret_contents]).

    Collects non-empty block contents for callers that need them (e.g. LK export).
    """
    secrets: list[str] = []

    def _collect(m: re.Match) -> str:
        content = m.group(1).strip()
        if content:
            secrets.append(content)
        return ''

    cleaned = re.sub(r'%%(.+?)%%', _collect, text, flags=re.DOTALL)
    return cleaned, secrets


def strip_obsidian_comments(text: str) -> str:
    """Remove %% ... %% blocks (single-line and multi-line). Discards contents."""
    return re.sub(r'%%.*?%%', '', text, flags=re.DOTALL)


def strip_wikilinks(text: str) -> str:
    """Convert [[link|alias]] → alias, [[link]] → link."""
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    return text


def strip_obsidian_embeds(text: str) -> str:
    """Remove ![[embedded media]] references."""
    return re.sub(r'!\[\[[^\]]+\]\]', '', text)


def clean_body(text: str) -> str:
    """Strip wikilinks, embeds, callout markers, and normalize blank lines."""
    text = strip_wikilinks(text)
    text = strip_obsidian_embeds(text)
    # Strip Obsidian callout markers (> [!tip] etc.) but keep content
    text = re.sub(r'^>\s*\[!\w+\]\s*$', '', text, flags=re.MULTILINE)
    # Normalize excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
