#!/usr/bin/env python3
"""
LegendKeeper JSON Generator
=============================
Converts an Obsidian source .md file → LegendKeeper JSON (importable .json or .lk).
With --push, syncs the timeline directly to LegendKeeper via the v3 REST API.

Currently supports: timeline (type: timeline)
Phase 2: prose pages (type: myth/lore) — requires ProseMirror schema.

LK JSON schema (from reverse-engineered export):
  { version, exportId, exportedAt, resources[], calendars[], resourceCount, hash }
  resource → { documents[], banner, … }
  document → { id, type:"time", calendarId, transforms[], content:{lanes[], events[]} }
  lane     → { id, name, pos, size }
  event    → { id, laneId, type:"event", pos, detail, start, end?, name,
               iconGlyph, color, imageUrl, imageFit, opacity, isSynced, data }

Timestamps: minutes since Unix epoch.
Conversion: year_number * 525960  (365.25 × 24 × 60)

Usage:
    python generate_lk_json.py source.md
    python generate_lk_json.py source.md --output timeline.json
    python generate_lk_json.py source.md --lk          # gzip-compressed .lk
    python generate_lk_json.py source.md --push        # sync to LK via API
"""

import os
import re
import sys
import json
import gzip
import hashlib
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Make utilities/shared importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.frontmatter import doc_type_of

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    raise ImportError(
        "PyYAML is required (pip install -r requirements.txt, or check "
        "you're using the project's intended Python interpreter) — "
        "frontmatter parsing silently degrades to a broken minimal parser "
        "without it, producing empty/incorrect build output."
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MINUTES_PER_YEAR = int(365.25 * 24 * 60)  # 525,960

# Pre-built calendar definition for "Menology of Epochs"
# Sourced from the user's LK export (Timeline_ Nianhao - The Divine Arc.json)
MENOLOGY_OF_EPOCHS: dict = {
    "id": "c1kuyu04",
    "name": "Menology of Epochs",
    "hasZeroYear": True,
    "maxMinutes": 1682164800,
    "months": [
        {"id": "jan", "name": "January",   "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
        {"id": "feb", "name": "February",  "isIntercalary": False, "length": 28, "interval": 1, "offset": 0},
        {"id": "mar", "name": "March",     "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
        {"id": "apr", "name": "April",     "isIntercalary": False, "length": 30, "interval": 1, "offset": 0},
        {"id": "may", "name": "May",       "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
        {"id": "jun", "name": "June",      "isIntercalary": False, "length": 30, "interval": 1, "offset": 0},
        {"id": "jul", "name": "July",      "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
        {"id": "aug", "name": "August",    "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
        {"id": "sep", "name": "September", "isIntercalary": False, "length": 30, "interval": 1, "offset": 0},
        {"id": "oct", "name": "October",   "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
        {"id": "nov", "name": "November",  "isIntercalary": False, "length": 30, "interval": 1, "offset": 0},
        {"id": "dec", "name": "December",  "isIntercalary": False, "length": 31, "interval": 1, "offset": 0},
    ],
    "leapDays": [
        {
            "id": "leap-day",
            "name": "Leap Day",
            "intercalary": False,
            "month": 1,
            "addsWeekDay": False,
            "day": 0,
            "weekDay": "",
            "interval": "400,!100,4",
            "offset": 0,
        }
    ],
    "weekdays": [
        {"id": "sun", "name": "Sunday"},
        {"id": "mon", "name": "Monday"},
        {"id": "tue", "name": "Tuesday"},
        {"id": "wed", "name": "Wednesday"},
        {"id": "thu", "name": "Thursday"},
        {"id": "fri", "name": "Friday"},
        {"id": "sat", "name": "Saturday"},
    ],
    "epochWeekday": 1,
    "weekResetsEachMonth": False,
    "hoursInDay": 24,
    "minutesInHour": 60,
    "negativeEra": {
        "id": "bc",
        "name": "The Slow Forgetting (Jibîrkirina Hêdî)",
        "abbr": "HJ",
        "hideAbbr": False,
        "startsAt": -1051552800,
        "resetMode": "none",
    },
    "positiveEras": [
        {
            "id": "lzrepnnp",
            "name": "The Held Breath (Tutulan Nefes)",
            "abbr": "HB",
            "hideAbbr": False,
            "startsAt": 0,
            "resetMode": "calendar",
        }
    ],
    "moons": [
        {
            "id": "8706b02f-74c1-496e-8577-1a60f88dee30",
            "name": "New Moon",
            "phase": 42524.0463,
            "shift": 15238,
            "color": "#FFFFFF",
        }
    ],
    "format": {
        "id": "custom-1771100402501",
        "year": "E YYYY",
        "month": "MMMM, E YYYY",
        "day": "DDDD, D^ MMMM, [the] SYYYY^ [Year of] EE",
        "time": "DDDD, D^ MMMM, EE SYYYY, HH:mm",
    },
    "halfClock": False,
}


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def short_id() -> str:
    """Generate an 8-char hex ID matching LK's format (e.g. 'r7fua06g')."""
    return uuid4().hex[:8]


def lane_pos(index: int) -> str:
    """Generate a simple lane position key."""
    # Simple lexicographic ordering: a0, b0, c0, …
    letters = 'abcdefghijklmnopqrstuvwxyz'
    return f'{letters[index % 26]}0'


def event_pos(lane_index: int, event_index: int) -> str:
    """Generate a simple event position key."""
    letters = 'abcdefghijklmnopqrstuvwxyz'
    return f'{letters[lane_index % 26]}{event_index}'


# LK exposes exactly three opacity levels in its UI.
# Any value outside these is non-standard; snap to the nearest valid level.
_LK_OPACITY_LEVELS = (0.25, 0.5, 1.0)

def snap_opacity(value: float) -> float:
    """Snap an arbitrary opacity float to the nearest LK-supported level (0.25 / 0.5 / 1.0)."""
    return min(_LK_OPACITY_LEVELS, key=lambda v: abs(v - value))


# ---------------------------------------------------------------------------
# Timestamp conversion
# ---------------------------------------------------------------------------

def year_to_minutes(year_str: str) -> int:
    """Convert a year string (e.g. '188', '-500', '1450') to LK epoch minutes."""
    try:
        year = float(year_str)
    except (ValueError, TypeError):
        return 0
    return int(year * MINUTES_PER_YEAR)


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
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


# ---------------------------------------------------------------------------
# Event line parser
# ---------------------------------------------------------------------------

# Lane names that represent background era/epoch spans — events in these lanes
# get layer:0 so they render behind other events in LK's timeline view.
BACKGROUND_LANE_NAMES: frozenset[str] = frozenset({'eras', 'era', 'epochs', 'epoch', 'ages', 'age'})

# Section names in the Markdown that map to calendar-level constructs (negativeEra /
# positiveEras) already embedded in MENOLOGY_OF_EPOCHS — they must NOT become lanes.
CALENDAR_ERA_SECTION_NAMES: frozenset[str] = frozenset({'calendar eras', 'calendar era'})


def parse_event_line(
    line: str,
    lane_id: str,
    lane_index: int,
    event_index: int,
    is_background_lane: bool = False,
) -> dict | None:
    """Parse one pipe-syntax event line → LK event object."""
    line = line.strip().lstrip('- ').strip()
    m = re.match(r'"([^"]+)"\s*(.*)', line)
    if not m:
        return None

    name = m.group(1).strip()
    props: dict = {}
    for part in m.group(2).split('|'):
        part = part.strip()
        if not part:
            continue
        if ':' in part:
            k, v = part.split(':', 1)
            props[k.strip().lower()] = v.strip().strip('"\'')

    # Resolve start/end from props
    start_str = props.get('start', props.get('date', ''))
    end_str = props.get('end', '')

    if not start_str:
        return None

    ev: dict = {
        'id': short_id(),
        'laneId': lane_id,
        'type': 'event',
        'pos': event_pos(lane_index, event_index),
        'detail': 1 if is_background_lane else 2,
        'start': year_to_minutes(start_str),
        'name': name,
        'iconGlyph': props.get('icon', 'circle'),
        'color': props.get('color', '#6B7280'),
        'imageUrl': props.get('image', ''),
        'imageFit': 'cover',
        'opacity': snap_opacity(float(props.get('opacity', '1'))),
        'isSynced': False,
        'data': {},
    }

    if end_str:
        ev['end'] = year_to_minutes(end_str)

    # Background lane events (Epochs, Eras, etc.) get layer:0 so they render
    # as visual bands behind all other events in LK's timeline view.
    if is_background_lane:
        ev['layer'] = 0

    return ev


# ---------------------------------------------------------------------------
# Timeline builder
# ---------------------------------------------------------------------------

def build_timeline_json(fm: dict, body: str) -> dict:
    """Build the full LK JSON export dict for a timeline document."""

    title = fm.get('title', 'Timeline')
    calendar_name = fm.get('calendar', 'Menology of Epochs')

    # Extract secret blocks
    secret_parts: list[str] = []

    def _collect_secret(m: re.Match) -> str:
        secret_parts.append(m.group(1).strip())
        return ''

    clean_body = re.sub(r'%%(.+?)%%', _collect_secret, body, flags=re.DOTALL)

    # Split into sections → lanes
    sections: dict[str, str] = {}
    current_name = ''
    current_lines: list[str] = []
    for line in clean_body.splitlines():
        if re.match(r'^## ', line):
            if current_name is not None:
                sections[current_name] = '\n'.join(current_lines)
            current_name = re.sub(r'^##\s+', '', line).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_name:
        sections[current_name] = '\n'.join(current_lines)

    # Build lanes and events
    lanes: list[dict] = []
    all_events: list[dict] = []
    public_lane_ids: list[str] = []

    for i, (section_name, section_content) in enumerate(sections.items()):
        if not section_name:
            continue
        # Calendar eras (negativeEra / positiveEras) are already encoded in the
        # MENOLOGY_OF_EPOCHS calendar constant — skip them as a lane entirely.
        if section_name.lower() in CALENDAR_ERA_SECTION_NAMES:
            continue
        is_background = section_name.lower() in BACKGROUND_LANE_NAMES
        lane_id = short_id()
        lane = {
            'id': lane_id,
            'name': section_name,
            'pos': lane_pos(len(lanes)),  # use current lane count for sequential, gap-free pos
            'size': 'sm',
        }
        lanes.append(lane)
        public_lane_ids.append(lane_id)

        event_index = 0
        for line in section_content.splitlines():
            if line.strip().startswith('-'):
                ev = parse_event_line(line, lane_id, i, event_index, is_background_lane=is_background)
                if ev:
                    all_events.append(ev)
                    event_index += 1

    # Build SECRET lane from %% blocks
    secret_lane_id: str | None = None
    if secret_parts:
        secret_lane_id = short_id()
        lane = {
            'id': secret_lane_id,
            'name': 'SECRET',
            'pos': lane_pos(len(lanes)),
            'size': 'sm',
        }
        lanes.append(lane)

        event_index = 0
        for secret_part in secret_parts:
            for line in secret_part.splitlines():
                if line.strip().startswith('-'):
                    ev = parse_event_line(line, secret_lane_id, len(lanes) - 1, event_index)
                    if ev:
                        ev['isHidden'] = True
                        all_events.append(ev)
                        event_index += 1

    # Calculate view range: clamp to calendar bounds so LK doesn't try to render
    # dates outside the defined calendar range (which can cause stalls).
    cal_min = MENOLOGY_OF_EPOCHS['negativeEra']['startsAt']
    cal_max = MENOLOGY_OF_EPOCHS['maxMinutes']
    starts = [e['start'] for e in all_events]
    ends = [e.get('end', e['start']) for e in all_events]
    all_times = starts + ends
    view_start = max(min(all_times) if all_times else 0, cal_min)
    view_end = min(max(all_times) if all_times else cal_max, cal_max)

    # Build transform filter (public lanes only — excludes SECRET)
    transforms: list[dict] = []
    if public_lane_ids:
        transforms.append({
            'type': 'filter',
            'filterType': 'id',
            'id': short_id(),
            'operator': 'in',
            'ids': public_lane_ids,
            'scope': 'lanes',
        })

    document_id = short_id()
    resource_id = short_id()
    # Use millisecond precision — JS Date.parse() does not accept Python's default
    # microsecond precision (6 decimal places) and returns NaN, causing LK to stall.
    now_iso = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    # Use Menology of Epochs calendar (or the default)
    calendar = MENOLOGY_OF_EPOCHS.copy()

    resource: dict = {
        'schemaVersion': 1,
        'aliases': [],
        'banner': {
            'enabled': False,
            'url': '',
            'yPosition': 50,
        },
        'createdBy': '',
        'documents': [
            {
                'id': document_id,
                'pos': 'Q',
                'createdAt': now_iso,
                'updatedAt': now_iso,
                'locatorId': f'document:{document_id}',
                'name': 'Main',
                'type': 'time',
                'isHidden': False,
                'isFirst': True,
                'calendarId': calendar['id'],
                'transforms': transforms,
                'sources': [],
                'presentation': {
                    'documentType': 'time',
                    'range': {
                        'start': view_start,
                        'end': view_end,
                        'detail': 3,
                    },
                },
                'content': {
                    'lanes': lanes,
                    'events': all_events,
                },
            }
        ],
        'iconColor': '#FFFFFF',
        'iconGlyph': 'calendar',
        'iconShape': 'pin-icon',
        'id': resource_id,
        'isHidden': False,
        'isLocked': False,
        'name': title if title.startswith('Timeline:') else f'Timeline: {title}',
        'parentId': '',
        'pos': 'Q',
        'properties': [],
        'showPropertyBar': False,
        'tags': [],
    }

    export: dict = {
        'version': 1,
        'exportId': short_id(),
        'exportedAt': now_iso,
        'resources': [resource],
        'calendars': [calendar],
        'resourceCount': 1,
        'hash': '',  # filled below
    }

    # Compute hash over content (excluding hash field)
    export_for_hash = {k: v for k, v in export.items() if k != 'hash'}
    content_bytes = json.dumps(export_for_hash, sort_keys=True, separators=(',', ':')).encode()
    export['hash'] = hashlib.sha256(content_bytes).hexdigest()

    return export


# ---------------------------------------------------------------------------
# Dotenv loader (mirrors location_components._load_dotenv)
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


# ---------------------------------------------------------------------------
# LegendKeeper API push
# ---------------------------------------------------------------------------

_LK_BASE = "https://www.legendkeeper.com"
_LK_API  = "/api/v3"


def _lk_request(
    api_key: str,
    project_id: str,
    method: str,
    path: str,
    body: dict | None = None,
) -> dict | list | None:
    url = f"{_LK_BASE}{_LK_API}/projects/{project_id}/{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; tarim-shaiel-pipeline/1.0)",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors='replace')
        raise RuntimeError(f"LK API {method} {path} → {e.code}: {body_text}") from e


def _lk_list_all(api_key: str, project_id: str, path: str) -> list:
    """Paginate through a LK list endpoint, returning all items."""
    results = []
    cursor = None
    while True:
        qs = f"limit=100{'&cursor=' + cursor if cursor else ''}"
        resp = _lk_request(api_key, project_id, "GET", f"{path}?{qs}")
        data = resp.get("data", []) if isinstance(resp, dict) else []
        results.extend(data)
        if not resp.get("hasMore"):
            break
        cursor = resp.get("nextCursor")
        if not cursor:
            break
    return results


def _find_time_doc_id(api_key: str, project_id: str, resource_id: str) -> str:
    """Return the ID of the first 'time' document in the resource."""
    docs = _lk_list_all(api_key, project_id, f"resources/{resource_id}/docs")
    time_docs = [d for d in docs if d.get("type") == "time"]
    if not time_docs:
        raise RuntimeError(f"No timeline document found in resource {resource_id}")
    return time_docs[0]["id"]


def push_to_legendkeeper(export: dict, fm: dict) -> None:
    """Sync the generated timeline to LegendKeeper via the v3 API.

    Strategy: upsert lanes and events by name. Events in LK that are no
    longer in the Markdown are deleted. isHidden is respected per event.
    """
    api_key = os.environ.get("LEGENDKEEPER_API_KEY", "")
    if not api_key:
        print("ERROR: LEGENDKEEPER_API_KEY not set — cannot push", file=sys.stderr)
        raise SystemExit(1)

    project_id = str(fm.get("lk_project_id", "")).strip()
    resource_id = str(fm.get("lk_resource_id", "")).strip()
    if not project_id or not resource_id:
        print(
            "ERROR: frontmatter missing lk_project_id or lk_resource_id\n"
            "  Add these to the timeline .md file to enable --push",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"  Connecting to LK project {project_id}, resource {resource_id}…")
    doc_id = _find_time_doc_id(api_key, project_id, resource_id)
    print(f"  Timeline document: {doc_id}")

    base = f"resources/{resource_id}/docs/{doc_id}"

    # --- Sync lanes -------------------------------------------------------
    existing_lanes_raw = _lk_request(api_key, project_id, "GET", f"{base}/lanes")
    existing_lanes: dict[str, str] = {
        l["name"]: l["id"]
        for l in (existing_lanes_raw.get("data", []) if existing_lanes_raw else [])
    }

    doc = export["resources"][0]["documents"][0]
    desired_lanes: list[dict] = doc["content"]["lanes"]
    lane_id_map: dict[str, str] = {}  # local short_id → LK lane id

    for i, lane in enumerate(desired_lanes):
        name = lane["name"]
        if name in existing_lanes:
            lk_lane_id = existing_lanes[name]
        else:
            resp = _lk_request(api_key, project_id, "POST", f"{base}/lanes", {
                "name": name,
                "rank": f"{chr(ord('a') + i)}0",
                "size": lane.get("size", "sm"),
            })
            lk_lane_id = resp["id"]
            print(f"    + lane  {name!r}")
        lane_id_map[lane["id"]] = lk_lane_id

    # --- Sync events ------------------------------------------------------
    existing_events_raw = _lk_list_all(api_key, project_id, f"{base}/events")
    existing_by_name: dict[str, dict] = {e["name"]: e for e in existing_events_raw}

    desired_events: list[dict] = doc["content"]["events"]
    desired_names: set[str] = {e["name"] for e in desired_events}

    created = updated = deleted = 0

    for ev in desired_events:
        lk_lane_id = lane_id_map.get(ev["laneId"], ev["laneId"])
        base_payload: dict = {
            "laneId": lk_lane_id,
            "name": ev["name"],
            "start": ev["start"],
            "color": ev.get("color", "#6B7280"),
            "iconGlyph": ev.get("iconGlyph", "circle"),
            "isHidden": ev.get("isHidden", False),
        }
        if "end" in ev:
            base_payload["end"] = ev["end"]

        if ev["name"] in existing_by_name:
            existing = existing_by_name[ev["name"]]
            # Only PATCH if something actually changed
            needs_update = (
                existing.get("start") != base_payload["start"]
                or existing.get("end") != base_payload.get("end")
                or existing.get("color") != base_payload["color"]
                or existing.get("iconGlyph") != base_payload["iconGlyph"]
                or existing.get("isHidden") != base_payload["isHidden"]
                or existing.get("laneId") != lk_lane_id
            )
            if needs_update:
                _lk_request(
                    api_key, project_id, "PATCH",
                    f"{base}/events/{existing['id']}", base_payload,
                )
                updated += 1
        else:
            _lk_request(api_key, project_id, "POST", f"{base}/events",
                        {"type": "event", **base_payload})
            created += 1

    # Delete events in LK that are no longer in the Markdown
    for name, ev in existing_by_name.items():
        if name not in desired_names:
            _lk_request(
                api_key, project_id, "DELETE", f"{base}/events/{ev['id']}"
            )
            deleted += 1

    print(f"  Events: {created} created, {updated} updated, {deleted} deleted")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate LegendKeeper JSON (.json or .lk) from Obsidian source.'
    )
    parser.add_argument('source', help='Source .md file path')
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: <source-stem>.json alongside source)',
    )
    parser.add_argument(
        '--lk', action='store_true',
        help='Output as gzip-compressed .lk file instead of plain .json',
    )
    parser.add_argument(
        '--push', action='store_true',
        help='Sync timeline to LegendKeeper via the v3 API (requires LEGENDKEEPER_API_KEY '
             'and lk_project_id / lk_resource_id in frontmatter)',
    )
    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise FileNotFoundError(f'Source file not found: {src}')

    raw = src.read_text(encoding='utf-8')
    fm, body = parse_frontmatter(raw)
    doc_type = doc_type_of(fm)  # Schema C aware (content_type → doc_type → legacy type)

    if doc_type == 'timeline':
        export = build_timeline_json(fm, body)
    else:
        print(f'ERROR: Document type "{doc_type}" not yet supported for JSON export.')
        print('  Supported types: timeline')
        print('  Prose pages (myth/lore) require Phase 2 ProseMirror implementation.')
        raise SystemExit(1)

    json_bytes = json.dumps(export, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    if args.lk:
        suffix = '.lk'
        out_path = Path(args.output) if args.output else src.with_suffix('.lk')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(out_path, 'wb') as f:
            f.write(json_bytes)
        fmt = 'gzip-compressed .lk'
    else:
        suffix = '.json'
        out_path = Path(args.output) if args.output else src.with_suffix('.json')
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(json_bytes)
        fmt = 'plain JSON'

    doc = export['resources'][0]['documents'][0]
    lanes = doc['content']['lanes']
    events = doc['content']['events']
    public_count = sum(1 for e in events if e['laneId'] in {l['id'] for l in lanes if l['name'] != 'SECRET'})
    secret_count = len(events) - public_count

    print(f'LK {fmt} written: {out_path}')
    print(f'  Lanes:  {len(lanes)} ({", ".join(l["name"] for l in lanes)})')
    print(f'  Events: {public_count} public + {secret_count} secret')
    print(f'  Hash:   {export["hash"][:16]}…')

    if args.push:
        print('Pushing to LegendKeeper…')
        push_to_legendkeeper(export, fm)
        print('Push complete.')


if __name__ == '__main__':
    main()
