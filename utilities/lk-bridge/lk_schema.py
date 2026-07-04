#!/usr/bin/env python3
"""
LK export-format builders — the executable embodiment of the reverse-engineered
LegendKeeper JSON schema (GH #213).

Facts this module encodes (verified 2026-05 round-trip + 2026-07-03 baseline diff
against the post-rewrite export):

* Envelope: {version, exportId, exportedAt, resources, calendars, resourceCount,
  hash}. The hash LK writes uses an unknown algorithm, and LK does NOT verify
  the field on import — we emit a deterministic SHA-256 over the sorted payload
  purely as a self-consistency fingerprint.
* ``presentation`` must be ``{"documentType": "page"}`` — ``null`` hangs the
  LK importer.
* LK reassigns all resource IDs on import (mentions are remapped within one
  import); pre-assigned IDs here are provisional.
* Content is Atlassian-ADF-dialect ProseMirror. Marks may carry ``attrs: {}``;
  mentions carry a ``documentId`` attr; GM sections use ``bodiedExtension``
  with extensionKey ``block-secret``.
* ``.lk`` files are gzip-compressed JSON, byte-identical schema.
"""

import gzip
import json
import hashlib
import string
from datetime import datetime, timezone

LK_EXTENSION_TYPE = "com.algorific.legendkeeper.extensions"
_B36 = string.digits + string.ascii_lowercase


def now_iso() -> str:
    """LK-style UTC timestamp: millisecond precision, Z suffix."""
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def short_id(seed: str) -> str:
    """Deterministic 8-char base36 ID from a seed string (LK ID format).

    Deterministic so repeated exports of the same vault path produce the same
    provisional ID — LK reassigns on import anyway, but stable provisional IDs
    keep diffs quiet and internal mentions consistent.
    """
    digest = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], 'big')
    chars = []
    for _ in range(8):
        digest, rem = divmod(digest, 36)
        chars.append(_B36[rem])
    return ''.join(chars)


# ── inline nodes / marks ─────────────────────────────────────────────────────

def text(t: str, marks: list | None = None) -> dict:
    node = {"type": "text", "text": t}
    if marks:
        node["marks"] = marks
    return node


def mark(kind: str) -> dict:
    """strong | em | code — LK emits empty attrs on marks; mirror that."""
    return {"type": kind, "attrs": {}}


def link_mark(href: str) -> dict:
    return {"type": "link", "attrs": {"href": href, "__confluenceMetadata": None}}


def mention(res_id: str, name: str, alias: str = "") -> dict:
    """Internal page link. LK remaps ``id`` within one import.

    ``documentId`` is included for fidelity with LK's own output (2026-07-03
    baseline: LK adds it on round-trip).
    """
    return {"type": "mention",
            "attrs": {"id": res_id, "text": name, "alias": alias,
                      "accessLevel": "", "userType": "", "documentId": ""}}


def hard_break() -> dict:
    return {"type": "hardBreak"}


# ── block nodes ──────────────────────────────────────────────────────────────

def heading(inline: list | str, level: int = 1) -> dict:
    content = [text(inline)] if isinstance(inline, str) else inline
    return {"type": "heading", "attrs": {"level": level}, "content": content}


def para(*inline) -> dict:
    node = {"type": "paragraph"}
    flat = [text(i) if isinstance(i, str) else i for i in inline]
    if flat:
        node["content"] = flat
    return node


def rule() -> dict:
    return {"type": "rule"}


def blockquote(*blocks) -> dict:
    return {"type": "blockquote", "content": list(blocks)}


def bullet_list(items: list) -> dict:
    return {"type": "bulletList", "content": [list_item(i) for i in items]}


def ordered_list(items: list) -> dict:
    return {"type": "orderedList", "content": [list_item(i) for i in items]}


def list_item(blocks) -> dict:
    if isinstance(blocks, dict):
        blocks = [blocks]
    return {"type": "listItem", "content": blocks}


def task_list(items: list) -> dict:
    """items: list of (checked: bool, inline_nodes: list)."""
    return {"type": "taskList",
            "content": [{"type": "taskItem",
                         "attrs": {"state": "DONE" if done else "TODO"},
                         "content": inline}
                        for done, inline in items]}


def panel(panel_type: str, *blocks) -> dict:
    """LK callout. panelType: info | note | warning | success."""
    return {"type": "panel", "attrs": {"panelType": panel_type}, "content": list(blocks)}


def table(rows: list, header_row: bool = True) -> dict:
    """rows: list of list of cell-block-lists (each cell = list of block nodes)."""
    trows = []
    for i, row in enumerate(rows):
        cell_type = "tableHeader" if (header_row and i == 0) else "tableCell"
        cells = [{"type": cell_type, "attrs": {"colspan": 1, "rowspan": 1},
                  "content": cell} for cell in row]
        trows.append({"type": "tableRow", "content": cells})
    return {"type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default", "__autoSize": False},
            "content": trows}


def media_external(url: str) -> dict:
    """External-URL image (no CDN upload path without the API)."""
    return {"type": "mediaSingle", "attrs": {"layout": "center"},
            "content": [{"type": "media",
                         "attrs": {"id": "", "type": "file", "collection": "",
                                   "__external": True, "url": url}}]}


def secret_block(inner_blocks: list, title: str = "Secret") -> dict:
    """GM-only section — LK's single native secret mechanism.

    ``title`` doubles as the round-trip discriminator channel (see the
    secrets mapping table in README.md): "GM", "GM id=x", "GM comment",
    "GM embed: <path>".
    """
    return {"type": "bodiedExtension",
            "attrs": {"extensionType": LK_EXTENSION_TYPE,
                      "extensionKey": "block-secret",
                      "parameters": {"extensionTitle": title},
                      "layout": "default"},
            "content": inner_blocks}


# ── documents / resources / envelope ─────────────────────────────────────────

def doc(doc_id: str, content_nodes: list, name: str = "Main") -> dict:
    ts = now_iso()
    return {"id": doc_id, "pos": "Q", "createdAt": ts, "updatedAt": ts,
            "locatorId": f"document:{doc_id}", "name": name, "type": "page",
            "isHidden": False, "isFullWidth": False, "isFirst": True,
            "transforms": [], "sources": [],
            "presentation": {"documentType": "page"},   # null hangs the importer
            "content": {"type": "doc", "content": content_nodes}}


def resource(res_id: str, name: str, parent_id: str, docs: list, *,
             tags: list | None = None, pos: str = "Q",
             is_hidden: bool = False, icon_glyph: str = "fas fa-book") -> dict:
    return {"schemaVersion": 1, "aliases": [],
            "banner": {"enabled": False, "url": "", "yPosition": 50},
            "createdBy": "", "iconColor": "#FFFFFF", "iconGlyph": icon_glyph,
            "iconShape": "pin-icon", "id": res_id, "isHidden": is_hidden,
            "isLocked": False, "name": name, "parentId": parent_id, "pos": pos,
            "properties": [], "showPropertyBar": False, "tags": tags or [],
            "documents": docs}


def envelope(resources: list, export_id: str = "lkbridge") -> dict:
    """Assemble the export envelope with a self-consistency hash.

    The hash is OUR deterministic fingerprint (SHA-256, sorted compact JSON,
    hash field excluded) — NOT LK's algorithm, which is unknown. LK does not
    verify this field on import (proven 2026-05, re-confirmed 2026-07-03).
    """
    export = {"version": 1, "exportId": export_id, "exportedAt": now_iso(),
              "resources": resources, "calendars": [],
              "resourceCount": len(resources), "hash": ""}
    payload = {k: v for k, v in export.items() if k != "hash"}
    export["hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return export


def write_export(export: dict, out_path, as_lk: bool = False) -> None:
    """Write plain .json, or gzip .lk when as_lk is True."""
    data = json.dumps(export, separators=(",", ":"), ensure_ascii=False)
    if as_lk:
        out_path.write_bytes(gzip.compress(data.encode()))
    else:
        out_path.write_text(json.dumps(export, indent=2, ensure_ascii=False))
