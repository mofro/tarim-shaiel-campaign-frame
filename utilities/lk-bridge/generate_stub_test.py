#!/usr/bin/env python3
"""
Generate a minimal LK stub test JSON for round-trip ID verification.

Three resources:
  tstpar01  LK Bridge Test: Hub         (parent, mentions both children, has secret block)
  tstcld01  LK Bridge Test: Cold Scene  (child, tagged, back-mention to parent)
  tstcld02  LK Bridge Test: Approach    (child, has secret block)

After importing this into a fresh LK project and re-exporting, compare
the resource IDs in the export against these known IDs to determine
whether LK preserves IDs on import.

Usage:
    python generate_stub_test.py
    python generate_stub_test.py --output path/to/output.json
"""

import json
import gzip
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def doc(doc_id: str, content_nodes: list, name: str = "Main") -> dict:
    return {
        "id": doc_id,
        "pos": "Q",
        "createdAt": NOW,
        "updatedAt": NOW,
        "locatorId": f"document:{doc_id}",
        "name": name,
        "type": "page",
        "isHidden": False,
        "isFullWidth": False,
        "isFirst": True,
        "transforms": [],
        "sources": [],
        "presentation": None,
        "content": {
            "type": "doc",
            "content": content_nodes,
        },
    }


def resource(res_id: str, name: str, parent_id: str, docs: list,
             tags: list = None, pos: str = "Q") -> dict:
    return {
        "schemaVersion": 1,
        "aliases": [],
        "banner": {"enabled": False, "url": "", "yPosition": 50},
        "createdBy": "",
        "iconColor": "#FFFFFF",
        "iconGlyph": "fas fa-book",
        "iconShape": "pin-icon",
        "id": res_id,
        "isHidden": False,
        "isLocked": False,
        "name": name,
        "parentId": parent_id,
        "pos": pos,
        "properties": [],
        "showPropertyBar": False,
        "tags": tags or [],
        "documents": docs,
    }


def heading(text: str, level: int = 1) -> dict:
    return {"type": "heading", "attrs": {"level": level},
            "content": [{"type": "text", "text": text}]}


def para(*inline) -> dict:
    return {"type": "paragraph", "content": list(inline)}


def text(t: str) -> dict:
    return {"type": "text", "text": t}


def mention(res_id: str, name: str) -> dict:
    return {"type": "mention",
            "attrs": {"id": res_id, "text": name, "alias": "",
                      "accessLevel": "", "userType": ""}}


def secret_block(*inner_nodes) -> dict:
    return {
        "type": "bodiedExtension",
        "attrs": {
            "extensionType": "com.algorific.legendkeeper.extensions",
            "extensionKey": "block-secret",
            "parameters": {"extensionTitle": "Secret"},
            "layout": "default",
        },
        "content": list(inner_nodes),
    }


def build() -> dict:
    # ── Resource IDs ─────────────────────────────────────────────────────────
    PAR = "tstpar01"
    C1  = "tstcld01"
    C2  = "tstcld02"
    ROOT = ""           # top-level resources have empty parentId

    # ── Hub page ─────────────────────────────────────────────────────────────
    hub_doc = doc("tstdoc01", [
        heading("LK Bridge Test: Hub"),
        para(
            text("Test hub. Child pages: "),
            mention(C1, "LK Bridge Test: Cold Scene"),
            text(" and "),
            mention(C2, "LK Bridge Test: Approach"),
            text("."),
        ),
        secret_block(
            para(text(
                "GM secret in hub. "
                "If this survives import/export, block-secret blocks work."
            )),
        ),
    ])
    hub = resource(PAR, "LK Bridge Test: Hub", ROOT, [hub_doc],
                   tags=["test"], pos="A")

    # ── Cold Scene page ───────────────────────────────────────────────────────
    cold_doc = doc("tstdoc02", [
        heading("LK Bridge Test: Cold Scene"),
        para(
            text("Cold comes first. Child of "),
            mention(PAR, "LK Bridge Test: Hub"),
            text("."),
        ),
        para(text(
            "This page is clean — no secret block. "
            "Tests that plain content survives round-trip."
        )),
    ])
    cold = resource(C1, "LK Bridge Test: Cold Scene", PAR, [cold_doc],
                    tags=["scene", "test"], pos="B")

    # ── Approach page ─────────────────────────────────────────────────────────
    approach_doc = doc("tstdoc03", [
        heading("LK Bridge Test: Approach"),
        para(text("The approach. Child of "),
             mention(PAR, "LK Bridge Test: Hub"),
             text(".")),
        secret_block(
            para(text(
                "GM secret in Approach. "
                "Tests secret blocks in child pages."
            )),
        ),
    ])
    approach = resource(C2, "LK Bridge Test: Approach", PAR, [approach_doc],
                        tags=["scene", "test"], pos="C")

    # ── Export envelope ───────────────────────────────────────────────────────
    export = {
        "version": 1,
        "exportId": "tstexprt",       # recognisable stub export ID
        "exportedAt": NOW,
        "resources": [hub, cold, approach],
        "calendars": [],
        "resourceCount": 3,
        "hash": "",
    }

    payload = {k: v for k, v in export.items() if k != "hash"}
    export["hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return export


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a minimal LK stub test JSON for round-trip ID verification."
    )
    parser.add_argument("--output", "-o", default="lk-bridge-test.json",
                        help="Output file path (default: lk-bridge-test.json)")
    parser.add_argument("--lk", action="store_true",
                        help="Also write a gzip-compressed .lk alongside the JSON")
    args = parser.parse_args()

    export = build()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(export, indent=2, ensure_ascii=False))
    print(f"JSON written:  {out}")

    if args.lk:
        lk_out = out.with_suffix(".lk")
        lk_out.write_bytes(gzip.compress(
            json.dumps(export, separators=(",", ":"), ensure_ascii=False).encode()
        ))
        print(f".lk  written:  {lk_out}")

    print()
    print("Known IDs to verify after import + export:")
    print("  tstpar01  →  LK Bridge Test: Hub")
    print("  tstcld01  →  LK Bridge Test: Cold Scene")
    print("  tstcld02  →  LK Bridge Test: Approach")
    print()
    print("If the exported JSON contains these same IDs: pre-generation works.")
    print("If the IDs are different: use the exported name→ID map for stub-bootstrap.")


if __name__ == "__main__":
    main()
