#!/usr/bin/env python3
"""
Generate LegendKeeper .lk file with PC character resources from DaggerForge + Obsidian data.
Mirrors the layout of the knkm2u6a "Character" template from Default Templates.

Usage:
    python3 utilities/lk_character_generator.py

Reads:
    - ~/Downloads/Tarim-Shaiel Library.lk  (existing export)
    - .obsidian/plugins/daggerforge/data.json
    - characters/PCs/*.md  (frontmatter: archetype, divine_tool, patron, player)

Writes:
    - ~/Downloads/Tarim-Shaiel Library (with PCs).lk
"""

import json
import gzip
import random
import string
import re
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
VAULT_ROOT  = Path(__file__).parent.parent
LK_INPUT    = Path.home() / "Downloads/Tarim-Shaiel Library.lk"
LK_OUTPUT   = Path.home() / "Downloads/Tarim-Shaiel Library (with PCs).lk"
DF_DATA     = VAULT_ROOT / ".obsidian/plugins/daggerforge/data.json"
PC_DIR      = VAULT_ROOT / "characters/PCs"
PARENT_ID   = "eexxn5m5"    # "Welcome" resource in the existing export
CREATED_BY  = "cml2gce5mkeo90876am5qn6na"

# LK CDN placeholder image (hooded silhouette, already on LK's CDN)
PLACEHOLDER_IMG = "https://assets.legendkeeper.com/256251b7-aacd-4dd9-88a7-78694a4e4e1e.png"

# PCs to skip — DaggerForge sheet is blank/empty
SKIP_NAMES = {"Ariel"}

PC_POSITIONS = list("abcdefghij")

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def gen_id(seed: str) -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(string.ascii_lowercase + string.digits) for _ in range(8))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse_first_num(s: str, default: int = 0) -> int:
    m = re.search(r"-?\d+", str(s))
    return int(m.group()) if m else default


# ---------------------------------------------------------------------------
# Prosemirror node constructors
# ---------------------------------------------------------------------------

def text_node(text: str, bold=False, italic=False) -> dict:
    node: dict = {"type": "text", "text": text}
    marks = []
    if bold:
        marks.append({"type": "strong", "attrs": {}})
    if italic:
        marks.append({"type": "em", "attrs": {}})
    if marks:
        node["marks"] = marks
    return node


def para(*nodes) -> dict:
    if not nodes:
        return {"type": "paragraph"}
    return {"type": "paragraph", "content": list(nodes)}


def heading(level: int, text: str) -> dict:
    return {"type": "heading", "attrs": {"level": level}, "content": [text_node(text)]}


def val_doc(text: str) -> dict:
    """A minimal doc-format value for KEY_VALUE rows."""
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "attrs": {"ychange": None, "textAlign": None},
                "content": [{"type": "text", "text": str(text)}],
            }
        ],
    }


def kv_row(row_id: str, pos: str, key: str, value: str = "") -> dict:
    """A KEY_VALUE row. value is optional — if blank, row is left empty (editable in LK)."""
    row: dict = {"id": row_id, "pos": pos, "key": key}
    if value:
        row["value"] = val_doc(value)
    return row


# ---------------------------------------------------------------------------
# Block builders matching the Character.json template structure
# ---------------------------------------------------------------------------

def block_image(node_id: str, url: str = PLACEHOLDER_IMG) -> dict:
    return {
        "type": "extension",
        "attrs": {
            "extensionType": "com.algorific.legendkeeper.extensions",
            "extensionKey": "block-image",
            "parameters": {
                "nodeId": node_id,
                "extensionTitle": "Image",
                "blockTitle": "Image",
                "isTitleHidden": True,
                "fixedWidth": True,
                "blockWidth": 280,
                "fill": True,
                "url": url,
                "displayAspectRatio": 1.3275862068965518,
                "naturalAspect": 1.3275862068965518,
                "fadeBottom": True,
            },
            "text": "Image",
            "layout": "default",
        },
    }


def block_meter(node_id: str, title: str, items: list, mode: str = "bar",
                hidden_title: bool = True) -> dict:
    return {
        "type": "extension",
        "attrs": {
            "extensionType": "com.algorific.legendkeeper.extensions",
            "extensionKey": "block-meter",
            "parameters": {
                "nodeId": node_id,
                "extensionTitle": title,
                "blockTitle": title,
                "isTitleHidden": hidden_title,
                "mode": mode,
                "items": items,
                "format": "a",
                "showText": True,
                "showIcon": True,
            },
            "text": title,
            "layout": "default",
        },
    }


def block_key_value(node_id: str, rows: list) -> dict:
    """Standalone block-key-value extension (rows pre-populated with values)."""
    return {
        "type": "extension",
        "attrs": {
            "extensionType": "com.algorific.legendkeeper.extensions",
            "extensionKey": "block-key-value",
            "parameters": {
                "nodeId": node_id,
                "extensionTitle": "Properties",
                "blockTitle": "Properties",
                "isTitleHidden": True,
                "rows": rows,
                "align": "left",
                "showIcons": True,
            },
            "text": "Properties",
            "layout": "default",
        },
    }


def block_text_field(node_id: str, content_blocks: list) -> dict:
    """bodiedExtension block-text-field."""
    return {
        "type": "bodiedExtension",
        "attrs": {
            "extensionType": "com.algorific.legendkeeper.extensions",
            "extensionKey": "block-text-field",
            "parameters": {
                "nodeId": node_id,
                "extensionTitle": "TEXT",
                "blockTitle": "TEXT",
                "isTitleHidden": True,
            },
            "text": "TEXT",
            "layout": "default",
        },
        "content": content_blocks,
    }


def infobox_kv(prop_id: str, pos: str, title: str, rows: list,
               bg_color: str = "#A855F7", hidden: bool = True) -> dict:
    """infoboxPm wrapping a KEY_VALUE property."""
    return {
        "type": "infoboxPm",
        "attrs": {
            "extensionType": "com.algorific.legendkeeper.extensions",
            "extensionKey": "block-infobox",
            "parameters": {},
            "layout": "default",
        },
        "content": [
            {
                "type": "infoboxPmRow",
                "attrs": {
                    "value": {
                        "type": "KEY_VALUE",
                        "title": title,
                        "data": {
                            "rows": rows,
                            "align": "left",
                            "showIcons": True,
                            "layout": "list",
                            "isTitleHidden": True,
                            "backgroundColor": bg_color,
                        },
                        "isTitleHidden": hidden,
                        "backgroundColor": bg_color,
                        "id": prop_id,
                        "pos": pos,
                    }
                },
            }
        ],
    }


def traits_table(tv: dict) -> dict:
    """Horizontal banded traits table matching the Character.json template."""
    trait_order = ["agility", "strength", "finesse", "instinct", "presence", "knowledge"]
    labels = ["AGILITY", "STRENGTH", "FINESSE", "INSTINCT", "PRESENCE", "KNOWLEDGE"]
    col_widths = [120, 120, None, None, None, 123]

    def header_cell(label: str, width) -> dict:
        attrs: dict = {"colspan": 1, "rowspan": 1}
        if width:
            attrs["colwidth"] = [width]
        return {
            "type": "tableHeader",
            "attrs": attrs,
            "content": [heading(6, label)],
        }

    def value_cell(value: str, width) -> dict:
        attrs: dict = {"colspan": 1, "rowspan": 1}
        if width:
            attrs["colwidth"] = [width]
        return {
            "type": "tableCell",
            "attrs": attrs,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [text_node(value or "0", bold=True)],
                }
            ],
        }

    header_row = {
        "type": "tableRow",
        "content": [header_cell(labels[i], col_widths[i]) for i in range(6)],
    }
    value_row = {
        "type": "tableRow",
        "content": [
            value_cell(
                tv.get(trait_order[i], {}).get("value", "0")
                if isinstance(tv.get(trait_order[i]), dict)
                else str(tv.get(trait_order[i], "0")),
                col_widths[i],
            )
            for i in range(6)
        ],
    }

    return {
        "type": "table",
        "attrs": {"isNumberColumnEnabled": False, "layout": "banded", "__autoSize": False},
        "content": [header_row, value_row],
    }


# ---------------------------------------------------------------------------
# Overview page builder — mirrors Character.json layout exactly
# ---------------------------------------------------------------------------

def build_overview(char: dict, obsidian: dict, seed: str) -> dict:
    name        = char.get("name", "Unknown")
    pronouns    = char.get("pronouns", "")
    heritage    = char.get("heritage", "")
    class_sub   = char.get("classSubclass", "")
    level       = char.get("level", "1")
    evasion     = char.get("evasion", "")
    armor_score = char.get("armorScore", "")
    major_thr   = char.get("majorThreshold", "")
    severe_thr  = char.get("severeThreshold", "")

    archetype   = obsidian.get("archetype", "")
    divine_tool = obsidian.get("divine_tool", "")
    patron      = obsidian.get("patron", "").strip('"')
    ancestry    = obsidian.get("ancestry", "").strip('"')
    player      = obsidian.get("player", "")

    # Parse class / subclass from various separator formats
    class_name, subclass_name = class_sub.strip(), ""
    for sep in [" / ", " - ", "/"]:
        if sep in class_sub:
            class_name, subclass_name = [x.strip() for x in class_sub.split(sep, 1)]
            break

    traits    = char.get("traits", {})
    ss        = char.get("sheetSettings", {})
    max_hp    = ss.get("maxHp", 6)
    max_str   = ss.get("maxStress", 6)
    max_hope  = ss.get("maxHope", 6)
    armor_int = parse_first_num(armor_score, 0)
    armor_max = max(armor_int, 6)

    pw = char.get("primaryWeapon") or {}
    sw = char.get("secondaryWeapon") or {}
    aa = char.get("activeArmor") or {}

    inventory   = char.get("inventory", "") or ""
    class_feat  = char.get("classFeature", "") or ""
    hope_feat   = char.get("hopeFeature", "") or ""

    # Experiences as bullet list
    exps = char.get("experiences") or []
    exp_items = []
    for e in exps:
        if isinstance(e, dict) and e.get("text"):
            mod = e.get("modifier", e.get("bonus", ""))
            label = e["text"] + (f"  ({mod})" if mod else "")
            exp_items.append({"type": "listItem", "content": [para(text_node(label))]})

    # Domain cards as bullet list
    domains = char.get("domainCards") or []
    domain_items = [
        {"type": "listItem", "content": [para(text_node(d["name"], bold=True))]}
        for d in domains if isinstance(d, dict) and d.get("name")
    ]

    # ---- node IDs ----
    img_id    = f"block-image-{gen_id(seed+'_img')}"
    meter_id  = f"block-meter-{gen_id(seed+'_meter')}"
    coin1_id  = f"meter-{gen_id(seed+'_coin1')}"
    coin2_id  = f"block-meter-{gen_id(seed+'_coin2')}"
    tf_id     = f"block-text-field-{gen_id(seed+'_tf')}"
    wprimary_id = f"block-key-value-{gen_id(seed+'_wp')}"
    wsec_id   = f"block-key-value-{gen_id(seed+'_ws')}"
    armor_bkv_id = f"block-key-value-{gen_id(seed+'_abkv')}"
    inv_tf_id = f"block-text-field-{gen_id(seed+'_itf')}"

    # ---- KEY_VALUE row IDs ----
    def row_ids(*suffixes):
        return [gen_id(seed + s) for s in suffixes]

    # Stats infobox rows (left column, below image)
    stat_ids = row_ids("_ev", "_mn", "_mj", "_sv")
    stat_rows = [
        kv_row(stat_ids[0], "0|aaaaaa:", "Evasion", str(evasion)),
        kv_row(stat_ids[1], "0|aaaaaa<", "Minor",   str(major_thr)),
        kv_row(stat_ids[2], "0|aaaaaa@", "Major",   ""),   # calculated in play
        kv_row(stat_ids[3], "0|aaaaaaE", "Severe",  str(severe_thr)),
    ]

    # Weapon KEY_VALUE rows — pre-filled with DaggerForge data
    def weapon_rows(w: dict, id_seed: str) -> list:
        ids = row_ids(id_seed+"_n", id_seed+"_tr", id_seed+"_dd", id_seed+"_ft")
        return [
            kv_row(ids[0], "0|aaaaaa:", "Name",          w.get("name", "")),
            kv_row(ids[1], "0|aaaaaa;", "Trait & Range",  w.get("traitRange", "")),
            kv_row(ids[2], "0|aaaaaa?", "Damage Dice",    w.get("damageDice", "")),
            kv_row(ids[3], "0|aaaaaaB", "Feature",        w.get("feature", "")),
        ]

    # Armor KEY_VALUE rows
    armor_ids = row_ids("_an", "_as", "_af")
    armor_rows = [
        kv_row(armor_ids[0], "0|aaaaaa:", "Name",       aa.get("name", "")),
        kv_row(armor_ids[1], "0|aaaaaa;", "Base Score",  aa.get("baseScore", "")),
        kv_row(armor_ids[2], "0|aaaaaa<", "Feature",     aa.get("feature", "")),
    ]

    # Inventory infobox rows
    inv_prop_id = gen_id(seed + "_invp")
    inv_rows_for_infobox = [
        {
            "type": "infoboxPmRow",
            "attrs": {
                "value": {
                    "type": "TEXT_FIELD",
                    "title": "TEXT",
                    "data": {
                        "fragment": {
                            "type": "doc",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "attrs": {"id": None, "visibility": None,
                                              "ychange": None, "textAlign": None},
                                    "content": [text_node(inventory)] if inventory else [],
                                }
                            ],
                        }
                    },
                    "isTitleHidden": True,
                    "id": inv_prop_id,
                    "pos": "S",
                }
            },
        }
    ]

    # Properties infobox at page top (class → subclass)
    top_prop_id   = gen_id(seed + "_tpid")
    top_prop_rows = [kv_row(gen_id(seed + "_tpr"), "R", class_name, subclass_name)]

    # ---- assemble document content ----
    blocks = [
        # Panel removed (template-only instructional note)
        # Blockquote for a tag-line / quote
        {
            "type": "blockquote",
            "content": [
                para(text_node(
                    f"{player}  ·  {ancestry or heritage}"
                    + (f"  ·  {pronouns}" if pronouns else ""),
                    italic=True,
                ))
            ],
        },

        # Properties infobox (class / subclass)
        infobox_kv(top_prop_id, "S", "PROPERTIES", top_prop_rows,
                   bg_color="#A855F7", hidden=True),

        # Horizontal traits table
        traits_table(traits),

        # Two-column: image+stats  |  meter+features
        {
            "type": "layoutSection",
            "content": [
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 50},
                    "content": [
                        block_image(img_id),
                        infobox_kv(
                            gen_id(seed + "_statib"), "R", "Properties",
                            stat_rows, bg_color="#A855F7", hidden=True,
                        ),
                    ],
                },
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 50},
                    "content": [
                        block_meter(
                            meter_id, "Progress Bar",
                            [
                                {"id": "bar-1",          "name": "HP",    "icon": "heart",           "current": max_hp,    "max": max_hp,   "color": "#EC4899"},
                                {"id": "bar-2",          "name": "Stress","icon": "bolt-lightning",  "current": 0,         "max": max_str,  "color": "#F59E0B"},
                                {"id": "bar-armor",      "name": "Armor", "icon": "shield",          "current": armor_int, "max": armor_max,"color": "none"},
                                {"id": "bar-hope",       "name": "Hope",  "icon": "fa-solid fa-circle","current": 0,        "max": max_hope, "color": "none"},
                            ],
                            hidden_title=True,
                        ),
                        block_text_field(
                            tf_id,
                            [
                                para(
                                    text_node("MAIN", bold=True),
                                    text_node(f": {class_feat}" if class_feat else ": —"),
                                ),
                                para(
                                    text_node("SECONDARY", bold=True),
                                    text_node(f": {hope_feat}" if hope_feat else ": —"),
                                ),
                            ],
                        ),
                    ],
                },
            ],
        },

        # Two-column: experiences+armor  |  weapons
        {
            "type": "layoutSection",
            "content": [
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 50},
                    "content": [
                        heading(2, "Experience (+2)"),
                        {"type": "bulletList", "content": exp_items}
                        if exp_items
                        else para(text_node("—")),

                        heading(2, "Active Armor (+2)"),
                        block_key_value(armor_bkv_id, armor_rows),
                    ],
                },
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 50},
                    "content": [
                        {
                            "type": "heading",
                            "attrs": {"level": 2},
                            "content": [
                                text_node("Active Weapons "),
                                {
                                    "type": "inlineExtension",
                                    "attrs": {
                                        "extensionType": "com.algorific.legendkeeper.extensions",
                                        "extensionKey": "inline-icon",
                                        "parameters": {"icon": "hand-back-fist"},
                                        "text": "Icon",
                                    },
                                },
                            ],
                        },
                        heading(3, "Primary"),
                        block_key_value(wprimary_id, weapon_rows(pw, "_wp")),
                        heading(3, "Secondary"),
                        block_key_value(wsec_id, weapon_rows(sw, "_ws")),
                    ],
                },
            ],
        },

        # Two-column: Class Feature  |  Gold coins
        {
            "type": "layoutSection",
            "content": [
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 50},
                    "content": [
                        heading(2, "Class Feature"),
                        para(text_node(class_feat) if class_feat else text_node("—")),
                        {"type": "paragraph"},
                    ],
                },
                {
                    "type": "layoutColumn",
                    "attrs": {"width": 50},
                    "content": [
                        {"type": "heading", "attrs": {"level": 2}, "content": []},
                        block_meter(coin1_id, "COIN",
                                    [{"id": "k1a9l3z7", "name": "Gold",   "icon": "circle",
                                      "current": 0, "max": 50, "color": "#F59E0B"}],
                                    mode="pool", hidden_title=False),
                        block_meter(coin2_id, "COIN",
                                    [
                                        {"id": "silv01", "name": "Silver", "icon": "fa-solid fa-circle",
                                         "current": 0, "max": 50, "color": "#D4D4D4"},
                                        {"id": "copp01", "name": "Copper", "icon": "fa-solid fa-circle",
                                         "current": 0, "max": 50, "color": "#78350F"},
                                    ],
                                    mode="pool", hidden_title=False),
                    ],
                },
            ],
        },

        # Inventory
        heading(2, "Inventory"),
        {
            "type": "infoboxPm",
            "attrs": {
                "extensionType": "com.algorific.legendkeeper.extensions",
                "extensionKey": "block-infobox",
                "parameters": {},
                "layout": "default",
            },
            "content": inv_rows_for_infobox,
        },

        # Arcane Identity (Tarim-Shaiel specific)
        heading(2, "Arcane Identity"),
        {
            "type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "banded", "__autoSize": False},
            "content": [
                r for r in [
                    _simple_table_row("Archetype:",   archetype)   if archetype   else None,
                    _simple_table_row("Divine Tool:", divine_tool) if divine_tool else None,
                    _simple_table_row("Patron:",      patron)      if patron      else None,
                    _simple_table_row("Level:",       level)       if level       else None,
                ]
                if r is not None
            ],
        },

        # Standard description sections (blank for players to fill)
        heading(2, "Description"),
        para(text_node("Physical description, mannerisms, distinguishing features.")),
        heading(2, "Traits and Motivations"),
        para(text_node("Personality, virtues, fears, motivations.")),
        heading(2, "Routine"),
        para(text_node("What does a typical day look like for this character?")),
        {"type": "paragraph", "content": [text_node(" ")]},

        # GM-only secrets block
        {
            "type": "bodiedExtension",
            "attrs": {
                "extensionType": "com.algorific.legendkeeper.extensions",
                "extensionKey": "block-secret",
                "parameters": {"extensionTitle": "Secret"},
                "layout": "default",
            },
            "content": [
                para(text_node("GM-only notes about this character. Hidden from players.")),
            ],
        },
        {"type": "paragraph"},
    ]

    return {"type": "doc", "content": blocks}


def _simple_table_row(label: str, value: str) -> dict:
    """Two-cell table row for the arcane identity block."""
    return {
        "type": "tableRow",
        "content": [
            {
                "type": "tableCell",
                "attrs": {"colspan": 1, "rowspan": 1, "colwidth": [130]},
                "content": [para(text_node(label, bold=True))],
            },
            {
                "type": "tableCell",
                "attrs": {"colspan": 1, "rowspan": 1},
                "content": [para(text_node(str(value)))],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Backstory page — GM-hidden
# ---------------------------------------------------------------------------

def build_backstory(char: dict, obsidian: dict) -> dict:
    archetype   = obsidian.get("archetype", "")
    divine_tool = obsidian.get("divine_tool", "")
    patron      = obsidian.get("patron", "").strip('"')

    ac    = char.get("ancestryCard") or {}
    cc    = char.get("communityCard") or {}
    notes = char.get("notes", "") or ""

    blocks: list = [
        heading(2, "GM Notes"),
        {"type": "table",
         "attrs": {"isNumberColumnEnabled": False, "layout": "banded", "__autoSize": False},
         "content": [
             r for r in [
                 _simple_table_row("Archetype:",   archetype)   if archetype   else None,
                 _simple_table_row("Divine Tool:", divine_tool) if divine_tool else None,
                 _simple_table_row("Patron:",      patron)      if patron      else None,
             ] if r is not None
         ]},
        {"type": "paragraph"},
    ]

    if ac.get("name"):
        blocks.append(heading(3, f"Ancestry — {ac['name']}"))
        if ac.get("description"):
            blocks.append(para(text_node(ac["description"])))
        for feat in (ac.get("features") or []):
            if isinstance(feat, dict) and feat.get("name"):
                blocks.append(para(text_node(feat["name"], bold=True)))
                if feat.get("description"):
                    blocks.append(para(text_node(feat["description"])))
        blocks.append({"type": "paragraph"})

    if cc.get("name"):
        blocks.append(heading(3, f"Community — {cc['name']}"))
        if cc.get("description"):
            blocks.append(para(text_node(cc["description"])))
        for feat in (cc.get("features") or []):
            if isinstance(feat, dict) and feat.get("name"):
                blocks.append(para(text_node(feat["name"], bold=True)))
                if feat.get("description"):
                    blocks.append(para(text_node(feat["description"])))
        blocks.append({"type": "paragraph"})

    if notes:
        blocks.append(heading(3, "Player Notes (DaggerForge)"))
        for line in notes.strip().splitlines():
            if line.strip():
                blocks.append(para(text_node(line)))

    return {"type": "doc", "content": blocks}


# ---------------------------------------------------------------------------
# Full resource constructor
# ---------------------------------------------------------------------------

def make_character_resource(char: dict, obsidian: dict, folder_id: str, pos: str) -> dict:
    name  = char.get("name", "Unknown")
    seed  = name.lower().replace(" ", "_")
    rid   = gen_id(seed + "_res")
    doc1  = gen_id(seed + "_doc1")
    doc2  = gen_id(seed + "_doc2")
    ts    = now_iso()

    def prop_id(suffix: str) -> str:
        return gen_id(seed + suffix)

    return {
        "schemaVersion": 1,
        "aliases": [],
        "banner": {"enabled": False, "url": "", "yPosition": 50},
        "createdBy": CREATED_BY,
        "documents": [
            {
                "id": doc1,
                "pos": "A",
                "createdAt": ts,
                "updatedAt": ts,
                "locatorId": f"document:{doc1}",
                "name": "Overview",
                "type": "page",
                "isHidden": False,
                "tableOfContents": False,
                "isFirst": True,
                "transforms": [],
                "sources": [],
                "content": build_overview(char, obsidian, seed),
            },
            {
                "id": doc2,
                "pos": "B",
                "createdAt": ts,
                "updatedAt": ts,
                "locatorId": f"document:{doc2}",
                "name": "Backstory",
                "type": "page",
                "isHidden": True,
                "tableOfContents": False,
                "isFirst": False,
                "transforms": [],
                "sources": [],
                "content": build_backstory(char, obsidian),
            },
        ],
        "iconColor": "#F59E0B",
        "iconGlyph": "fas fa-user",
        "iconShape": "pin-icon",
        "id": rid,
        "isHidden": False,
        "isLocked": False,
        "name": name,
        "parentId": folder_id,
        "pos": pos,
        "properties": [
            # Mirror the knkm2u6a template property IDs exactly for template linkage
            {"id": "ciclix8g",  "pos": "Q",  "title": "IMAGE",   "type": "IMAGE",
             "data": {"url": "", "displayHeight": 272, "scale": 1.0, "origin": [0.5, 0.5]}},
            {"id": "jaid6l8h",  "pos": "S",  "title": "VIBE",    "type": "SPOTIFY_SINGLE", "data": {"url": ""}},
            {"id": "a4njho9z",  "pos": "W",  "title": "SUMMARY", "type": "TEXT_FIELD",
             "data": {"fragment": {"type": "doc", "content": [{"type": "paragraph"}]}}},
            {"id": "vd7sykno",  "pos": "X",  "title": "FRIENDS", "type": "RESOURCE_LINK", "data": {"items": []}},
            {"id": "tqc10f9r",  "pos": "\\", "title": "ENEMIES", "type": "RESOURCE_LINK", "data": {"items": []}},
            {"id": "xv6t7kqk",  "pos": "`",  "title": "TAGS",    "type": "TAGS"},
            {"id": "rvcgpo27",  "pos": "c",  "title": "Token Pool", "type": "METER",
             "data": {"mode": "pool", "showIcon": False,
                      "items": [{"id": "osxsrqed", "name": "Currency", "icon": "circle",
                                 "current": 0, "max": 50, "color": "#3B82F6"}],
                      "format": "a"}},
        ],
        "showPropertyBar": False,  # matches knkm2u6a
        "tags": ["character"],
    }


def make_folder_resource(folder_id: str) -> dict:
    ts     = now_iso()
    doc_id = gen_id("pc_folder_doc1")
    return {
        "schemaVersion": 1,
        "aliases": [],
        "banner": {"enabled": False, "url": "", "yPosition": 50},
        "createdBy": CREATED_BY,
        "documents": [
            {
                "id": doc_id,
                "pos": "A",
                "createdAt": ts,
                "updatedAt": ts,
                "locatorId": f"document:{doc_id}",
                "name": "Overview",
                "type": "page",
                "isHidden": False,
                "tableOfContents": False,
                "isFirst": True,
                "transforms": [],
                "sources": [],
                "content": {
                    "type": "doc",
                    "content": [
                        heading(1, "Player Characters"),
                        para(text_node(
                            "The six heroes of Tarim-Shaiel — champions expelled from paradise "
                            "to discover their unfinished work."
                        )),
                    ],
                },
            }
        ],
        "iconColor": "#F59E0B",
        "iconGlyph": "fas fa-users",
        "iconShape": "pin-icon",
        "id": folder_id,
        "isHidden": False,
        "isLocked": False,
        "name": "Player Characters",
        "parentId": PARENT_ID,
        "pos": "g",
        "properties": [],
        "showPropertyBar": False,
        "tags": [],
    }


# ---------------------------------------------------------------------------
# Obsidian frontmatter reader
# ---------------------------------------------------------------------------

def read_obsidian_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm


def load_obsidian_pcs() -> dict:
    result = {}
    for path in PC_DIR.glob("*.md"):
        if "(player)" in path.name:
            continue
        fm   = read_obsidian_frontmatter(path)
        body = path.read_text(encoding="utf-8")
        m    = re.search(r"id:\s*(CHR_\S+)", body)
        if m:
            result[m.group(1)] = fm
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Reading {LK_INPUT} …")
    with gzip.open(LK_INPUT, "rt", encoding="utf-8") as f:
        lk_data = json.load(f)

    existing_ids = {r["id"] for r in lk_data.get("resources", [])}
    print(f"  {len(existing_ids)} existing resources")

    print("Reading DaggerForge data …")
    df_data  = json.load(open(DF_DATA))
    df_chars = {c["id"]: c for c in df_data.get("characters", [])}
    print(f"  {len(df_chars)} DaggerForge characters")

    print("Reading Obsidian PC files …")
    obsidian_by_df_id = load_obsidian_pcs()
    print(f"  {len(obsidian_by_df_id)} PC files with DaggerForge IDs")

    folder_id    = gen_id("pc_folder_res")
    new_resources = [make_folder_resource(folder_id)]

    pos_iter = iter(PC_POSITIONS)
    built    = []

    for df_id, char in df_chars.items():
        name = char.get("name", "?")
        if name in SKIP_NAMES:
            print(f"  Skipping {name} (no stats in DaggerForge)")
            continue

        obsidian = obsidian_by_df_id.get(df_id, {})
        if not obsidian:
            print(f"  WARNING: no Obsidian file for {name} ({df_id})")

        pos      = next(pos_iter, "z")
        resource = make_character_resource(char, obsidian, folder_id, pos)

        if resource["id"] in existing_ids:
            print(f"  WARNING: ID collision for {name} — skipping")
            continue

        new_resources.append(resource)
        built.append(name)
        print(f"  Built: {name}  (id={resource['id']})")

    lk_data["resources"]      = lk_data.get("resources", []) + new_resources
    lk_data["resourceCount"]  = len(lk_data["resources"])
    lk_data["exportedAt"]     = now_iso()

    print(f"\nWriting {LK_OUTPUT} …")
    json_bytes = json.dumps(lk_data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with gzip.open(LK_OUTPUT, "wb") as f:
        f.write(json_bytes)

    size_kb = LK_OUTPUT.stat().st_size // 1024
    print(f"  Done — {size_kb}KB  ({len(built)} PCs: {', '.join(built)})")
    print()
    print("Import instructions:")
    print("  1. LegendKeeper → your world → Settings → Import/Export → Import")
    print(f"  2. Upload: {LK_OUTPUT.name}")
    print("  3. 'Player Characters' folder appears in the sidebar under Welcome")
    print("  4. Drag portraits into each character's IMAGE property to replace the placeholder")


if __name__ == "__main__":
    main()
