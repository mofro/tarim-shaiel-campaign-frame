#!/usr/bin/env python3
"""
Tarim-Shaiel Dashboard Generator
=================================
Parses TODO.md (checkbox counts) and DASHBOARD.md (health panel) to generate docs/dashboard.html.

Usage:
    python generate_dashboard.py
    python generate_dashboard.py --todo path/to/TODO.md
    python generate_dashboard.py --out path/to/output.html
    python generate_dashboard.py --json   # also emit dashboard_data.json

Domain mapping (keyword -> domain key):
    cosmolog / ecosystem / entity      -> cosmology
    story / narrative / session / lore -> narrative
    charm / campaign frame / archetype -> mechanics
    world / ancestry / location / myth -> world
    kanka / obsidian / geojson / infra -> infra
"""

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import date, datetime, datetime
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Paths (relative to this script's location: utilities/dashboard/)
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent))
from shared.config import ProjectConfig

VAULT_ROOT      = ProjectConfig.vault_root
TODO_PATH       = VAULT_ROOT / "TODO.md"
DASHBOARD_PATH  = VAULT_ROOT / "DASHBOARD.md"
OUTPUT_PATH     = VAULT_ROOT / "docs" / "dashboard.html"

# ---------------------------------------------------------------------------
# Domain keyword detection
# ---------------------------------------------------------------------------
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "cosmology": [
        "cosmolog", "sleeping entity", "mythic ecosystem", "wizard's awareness",
        "stakeholder knowledge", "ecosystem", "threshold", "revelation structure",
        "cosmic", "entity",
    ],
    "narrative": [
        "story", "narrative", "session 0", "awakening", "seeker", "warrior",
        "breaker", "sacrificer", "visionary", "bridge", "shared memory",
        "secret snippet", "gm notes", "liberation_aftermath", "lore",
        "ghost communication", "unfinished charge", "manufactured doubt",
        "post-liberation", "merchant house", "player pitch",
    ],
    "mechanics": [
        "charm", "tool progression", "tool evolution", "campaign frame",
        "classes vs", "archetype", "daggerheart", "r/h/k", "resource",
        "conflict resolution", "character creation", "character advancement",
        "charm library", "charm tree",
    ],
    "world": [
        "world", "geographic", "ancestry", "orc", "goblin", "halfling",
        "dwarf", "elf", "elven", "location", "region", "faction", "trade route",
        "myth", "creature", "vetala", "jiangshi", "rakshasa", "silk road",
        "naming", "settlement", "npc", "culture",
    ],
    "infra": [
        "kanka", "obsidian", "infrastructure", "sync", "script", "leaflet",
        "template", "schema", "vault", "documentation", "geojson",
        "python script", "automation", "publish", "export", "dashboard",
    ],
}

def detect_domain(text: str, default: str = "general") -> str:
    """Return the best-matched domain for text, or `default` if nothing matches.
    Callers that need a fallback should pass an explicit default rather than
    relying on silent world-classification of unrelated content."""
    t = text.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return domain
    return default

def obsidian_link(vault_path: str, vault: str = ProjectConfig.vault_name) -> str:
    clean = vault_path.lstrip("/").replace(".md", "")
    return f"obsidian://open?vault={vault}&file={clean}"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class TodoItem:
    text: str
    done: bool
    blocked: bool = False
    note: str = ""
    effort: str = ""
    links: list[tuple[str, str]] = field(default_factory=list)

@dataclass
class TodoGroup:
    title: str
    domain: str
    items: list[TodoItem] = field(default_factory=list)

@dataclass
class Section:
    status: str   # active | blocked | upcoming | done
    title: str
    subtitle: str
    groups: list[TodoGroup] = field(default_factory=list)

@dataclass
class DashboardData:
    last_updated: str
    generation_time: str
    readiness: int
    domain_pcts: dict[str, int]
    critical_path: list[str]
    blockers: list[str]
    recent_sessions: list[dict]
    sections: list[Section]
    quick_summary: list[dict] = field(default_factory=list)
    player_status: dict = field(default_factory=dict)

# ---------------------------------------------------------------------------
# DASHBOARD.md reader
# Replaces six regex-based extractors. Reads YAML frontmatter + Quick Summary
# body from DASHBOARD.md. Falls back to sensible defaults if file is missing.
# ---------------------------------------------------------------------------
_SUMMARY_STATUS_MAP = [
    ("✅",  "done"),      # ✅
    ("\U0001f504", "active"), # 🔄
    ("⚠",  "blocked"),   # ⚠
    ("\U0001f195", "info"),   # 🆕
    ("\U0001f5c3", "info"),   # 🗃️
    ("\U0001f5d2", "info"),   # 🗒️
    ("- [x]",   "done"),
    ("- [ ]",   "pending"),
]

def parse_dashboard_md() -> dict:
    """Parse DASHBOARD.md and return structured health-panel data.

    Keys returned: last_updated, critical_path, players, domain_overrides,
    blockers, quick_summary.
    """
    if not DASHBOARD_PATH.exists():
        print(f"WARNING: {DASHBOARD_PATH} not found — health panel will use defaults. "
              "Create DASHBOARD.md to resolve this.")
        return {
            "last_updated":     date.today().strftime("%B %d, %Y"),
            "critical_path":    ["Complete Session 0 scenarios", "Resolve Campaign Frame", "Playtest"],
            "players":          {"summary": "", "archetypes": []},
            "domain_overrides": {},
            "blockers":         ["No active blockers detected"],
            "quick_summary":    [],
        }

    from shared.frontmatter import parse_frontmatter
    text = DASHBOARD_PATH.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # last_updated
    raw_date = fm.get("last_updated", "")
    try:
        parsed_date = datetime.strptime(str(raw_date), "%Y-%m-%d")
        last_updated = parsed_date.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        last_updated = date.today().strftime("%B %d, %Y")

    # critical_path
    critical_path = fm.get("critical_path") or []
    if isinstance(critical_path, str):
        critical_path = [s.strip() for s in re.split(r"→|->", critical_path) if s.strip()]

    # players
    players_fm = fm.get("players") or {}
    committed  = players_fm.get("committed", 0)
    total      = players_fm.get("total", 0)
    archetypes = [
        {"name": a["name"], "status": a.get("status", "pending"), "player": a.get("player", "")}
        for a in (players_fm.get("archetypes") or [])
        if isinstance(a, dict)
    ]
    player_status = {
        "summary":    f"{committed}/{total} committed" if (committed or total) else "",
        "archetypes": archetypes,
    }

    # domain_overrides
    overrides_fm    = fm.get("domain_overrides") or {}
    domain_overrides = {k: int(v) for k, v in overrides_fm.items() if v is not None}

    # blockers
    blockers_raw = fm.get("blockers") or []
    blockers     = [str(b) for b in blockers_raw if b] if blockers_raw else ["No active blockers detected"]

    # quick_summary — scan body for ## Quick Summary bullets
    quick_summary: list[dict] = []
    in_summary = False
    for line in body.splitlines():
        if re.match(r"^## Quick Summary", line, re.IGNORECASE):
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if in_summary:
            stripped = line.strip()
            if not stripped:
                continue
            if not stripped.startswith("-"):
                break
            item_text = stripped.lstrip("- ").strip()
            item_text = re.sub(r"^\[[xX ]\]\s*", "", item_text)
            item_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", item_text)
            item_text = re.sub(r"`[^`]+`", "", item_text).strip()
            status = "info"
            for marker, s in _SUMMARY_STATUS_MAP:
                if marker in stripped:
                    status = s
                    break
            display = item_text[:240] + ("…" if len(item_text) > 240 else "")
            quick_summary.append({"text": display, "status": status})

    return {
        "last_updated":     last_updated,
        "critical_path":    critical_path,
        "players":          player_status,
        "domain_overrides": domain_overrides,
        "blockers":         blockers,
        "quick_summary":    quick_summary,
    }

# ---------------------------------------------------------------------------
# Checkbox counter per domain
# Walks H2-H4 headers, assigns a current domain, counts [x] vs [ ]
# ---------------------------------------------------------------------------
SECTION_DOMAIN_HEADERS: dict[str, str] = {
    "cosmolog": "cosmology", "ecosystem": "cosmology",
    "story": "narrative", "narrative": "narrative", "session 0": "narrative",
    "awakening": "narrative", "lore": "narrative", "liberation": "narrative",
    "charm": "mechanics", "tool": "mechanics", "campaign frame": "mechanics",
    "mechanics": "mechanics", "archetype": "mechanics",
    "domains":    "mechanics", "abilities":  "mechanics", "classes":    "mechanics",
    "subclasses": "mechanics", "armor":      "mechanics",
    "world": "world", "geographic": "world", "ancestry": "world",
    "location": "world", "locations": "world", "orc": "world", "myth": "world",
    "silk road": "world", "npc": "world", "culture": "world",
    "faction": "world", "factions": "world", "events": "world",
    "regions": "world",
    "kanka": "infra", "obsidian": "infra", "infrastructure": "infra",
    "geojson": "infra", "documentation": "infra", "sync": "infra",
}

def compute_domain_pcts(todo_text: str, overrides: dict[str, int]) -> dict[str, int]:
    counts: dict[str, list[int]] = {d: [0, 0] for d in ["narrative", "mechanics", "world", "infra", "cosmology"]}
    current_domain: Optional[str] = None
    in_excluded_h2: bool = False

    # H2 sections that are pure journal/archive — never count their checkboxes
    # NOTE: "completed" is intentionally NOT excluded here — completed items
    # must count as done toward the domain percentages so the gauge reflects
    # actual overall progress, not just how much of the outstanding work is ticked.
    EXCLUDED_H2 = {"session log"}

    for line in todo_text.splitlines():
        if re.match(r"^#{2,4} ", line):
            h_text = re.sub(r"^#{2,4}\s+", "", line).lower()
            # H2 exclusion check: if we enter an archive section, kill domain and
            # keep it dead (including for any H3/H4 within) until another H2 is found
            if re.match(r"^## ", line):
                if any(excl in h_text for excl in EXCLUDED_H2):
                    current_domain = None
                    in_excluded_h2 = True
                    continue
                else:
                    in_excluded_h2 = False
            # Don't let H3/H4 inside excluded sections re-activate domain tracking
            if not in_excluded_h2:
                for kw, domain in SECTION_DOMAIN_HEADERS.items():
                    if kw in h_text:
                        current_domain = domain
                        break
        if current_domain:
            if re.search(r"- \[x\]", line, re.IGNORECASE):
                counts[current_domain][0] += 1
                counts[current_domain][1] += 1
            elif re.search(r"- \[ \]", line):
                counts[current_domain][1] += 1

    result: dict[str, int] = {}
    for domain, (done, total) in counts.items():
        if domain in overrides:
            result[domain] = overrides[domain]
        elif total > 0:
            result[domain] = round((done / total) * 100)
        else:
            result[domain] = 0
    return result

# ---------------------------------------------------------------------------
# Campaign readiness = weighted average of domain pcts
# ---------------------------------------------------------------------------
DOMAIN_WEIGHTS = {"narrative": 0.35, "mechanics": 0.25, "world": 0.25, "infra": 0.15}

def compute_readiness(domain_pcts: dict[str, int]) -> int:
    return round(sum(domain_pcts.get(d, 0) * w for d, w in DOMAIN_WEIGHTS.items()))

# ---------------------------------------------------------------------------
# Recent sessions — reads from ## SESSION LOG, ### Session YYYY-MM-DD entries
# ---------------------------------------------------------------------------
SESSION_LOG_RE = re.compile(
    r"^##\s+SESSION LOG\s*$.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL | re.IGNORECASE
)
SESSION_ENTRY_RE = re.compile(
    r"###\s+Session\s+(\d{4}-\d{2}-\d{2})(.*?)(?=\n###\s+Session\s+\d{4}|\n##\s|\Z)",
    re.DOTALL
)

def extract_recent_sessions(todo_text: str) -> list[dict]:
    sessions = []
    log_m = SESSION_LOG_RE.search(todo_text)
    search_text = log_m.group(0) if log_m else todo_text
    for m in SESSION_ENTRY_RE.finditer(search_text):
        body = m.group(2)
        title_m = re.search(r"\*\*([^*\n]+)\*\*", body)
        title = title_m.group(1) if title_m else "Session Update"
        text_lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
        summary = text_lines[1] if len(text_lines) > 1 else (text_lines[0] if text_lines else "")
        summary = re.sub(r"\*+|`", "", summary)[:220]
        links = []
        for lm in re.finditer(r"`(/[^`]+\.md)`", body):
            p = lm.group(1)
            links.append({"label": Path(p).stem, "vault_path": p})
        sessions.append({"date": m.group(1), "title": title, "summary": summary, "links": links[:3]})
        if len(sessions) >= 3:
            break
    return sessions

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
def extract_generation_time() -> str:
    return datetime.now().strftime("%B %d, %Y at %I:%M %p")


# ---------------------------------------------------------------------------
# TODO section parser
# Maps H2 headings to status categories, H3/H4 to groups, checkboxes to items
# ---------------------------------------------------------------------------
STATUS_MAP = {
    "ACTIVE": "active",
    "HIGH PRIORITY": "active",       # legacy compat
    "NEAR-TERM": "upcoming",
    "NEAR TERM": "upcoming",
    "MEDIUM-TERM": "upcoming",
    "MEDIUM TERM": "upcoming",
    "FUTURE": "upcoming",
    "BLOCKED": "blocked",
    "BLOCKERS": "blocked",           # legacy compat
    "DECISIONS NEEDED": "blocked",   # legacy compat
    "COMPLETED": "done",
    "COMPLETED ASSETS": "done",      # legacy compat
    "SETTLED MECHANICS": "done",     # legacy compat
    "SETTLED": "done",               # legacy compat
}
SECTION_TITLES = {
    "active":   ("Active Work",                  "In progress now"),
    "blocked":  ("Blocked \u2014 Decisions Required", "Decisions needed"),
    "upcoming": ("Near-Term & Medium-Term",       "This month / next 2\u20133 sessions"),
    "done":     ("Completed Assets",              "Locked & verified"),
}
SKIP_HEADINGS = {
    "PROGRESS TRACKING", "SESSION LOG", "QUICK REFERENCE",
    "WORKING PRINCIPLES", "BRAINSTORM", "PROJECT HEALTH",
    "RECENT ACCOMPLISHMENTS",  # legacy compat
    "LATEST SESSION",          # legacy compat
    "PREVIOUS SESSION",        # legacy compat
}

def parse_todo_sections(todo_text: str) -> list[Section]:
    sections: list[Section] = []
    active_section: Optional[Section] = None
    active_group:   Optional[TodoGroup] = None
    current_item:   Optional[TodoItem] = None

    def flush_item():
        nonlocal current_item
        if current_item is not None and active_group is not None:
            active_group.items.append(current_item)
            current_item = None

    def flush_group():
        nonlocal active_group
        flush_item()
        if active_group is not None and active_section is not None:
            if active_group.items:
                active_section.groups.append(active_group)
        active_group = None

    def flush_section():
        flush_group()
        if active_section is not None and active_section.groups:
            sections.append(active_section)

    for line in todo_text.splitlines():
        # H2 -> section
        if re.match(r"^## ", line):
            flush_section()
            active_section = None
            h = re.sub(r"^##\s+[^\w]*", "", line).upper().strip()
            if any(skip in h for skip in SKIP_HEADINGS):
                continue
            for key, status in STATUS_MAP.items():
                if key in h:
                    t, sub = SECTION_TITLES[status]
                    existing = next((s for s in sections if s.status == status), None)
                    if existing:
                        active_section = existing
                        sections.remove(existing)
                    else:
                        active_section = Section(status=status, title=t, subtitle=sub)
                    break

        # H3/H4 -> group
        elif re.match(r"^#{3,4} ", line) and active_section is not None:
            prev_domain = active_group.domain if active_group else None
            flush_group()
            raw = re.sub(r"^#{3,4}\s+", "", line)
            has_done_marker = bool(re.search(r"LOCKED|COMPLETE|DECIDED|WORKING", raw, re.IGNORECASE))
            # Strip non-ASCII (emoji) then cleanup status suffixes
            raw = re.sub(r"[^\x00-\x7F]", "", raw).strip()
            raw = re.sub(r"\s*(LOCKED|COMPLETE|DECIDED|WORKING|NEW|PARTIAL)\s*.*$", "", raw, flags=re.IGNORECASE).strip()
            # Use SECTION_DOMAIN_HEADERS (same as compute_domain_pcts) so display
            # domain matches the percentage domain. Fall back to parent group's domain
            # rather than defaulting to "world" — prevents false WORLD classification
            # for sub-headers like "GM-Facing Sections" or "Follow-up From DIVINE_PLAYERS.md".
            # If neither header nor parent matches, fall back to detect_domain with
            # "general" default (never silently classifies as world).
            h_lower = raw.lower()
            matched = next((dom for kw, dom in SECTION_DOMAIN_HEADERS.items() if kw in h_lower), None)
            domain = matched or prev_domain or detect_domain(raw, default="general")
            active_group = TodoGroup(title=raw, domain=domain)
            if active_section.status == "done" and has_done_marker:
                active_group.items.append(TodoItem(text=raw, done=True))

        # Checkbox item
        elif re.match(r"^\s*- \[[ xX]\]", line) and active_section is not None:
            if active_group is None:
                active_group = TodoGroup(title="General", domain=detect_domain(line, default="general"))
            flush_item()
            done = bool(re.match(r"^\s*- \[[xX]\]", line))
            text = re.sub(r"^\s*- \[[xX ]\]\s*", "", line)
            text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text).strip()
            blocked = (active_section.status == "blocked") and not done
            current_item = TodoItem(text=text, done=done, blocked=blocked)

        # Numbered list item (BLOCKERS section uses these)
        elif (re.match(r"^\d+\.\s+\*\*", line) and active_section is not None
              and active_section.status == "blocked"):
            if active_group is None:
                active_group = TodoGroup(title="Critical Blockers", domain="mechanics")
            flush_item()
            text = re.sub(r"^\d+\.\s+\*\*([^*]+)\*\*.*", r"\1", line).strip()
            current_item = TodoItem(text=text, done=False, blocked=True)

        # Sub-list continuation
        elif re.match(r"^\s{2,}- ", line) and current_item is not None:
            sub = line.strip().lstrip("- ").strip()
            if re.match(r"~\d", sub):
                current_item.effort = sub
            elif re.search(r"`/[^`]+`", sub) or "**File:**" in sub:
                pm = re.search(r"`(/[^`]+)`", sub)
                if pm:
                    current_item.links.append((Path(pm.group(1)).stem, pm.group(1)))
            else:
                sub_clean = re.sub(r"\*+|`", "", sub).strip()
                if sub_clean:
                    current_item.note = ((current_item.note + " ") if current_item.note else "") + sub_clean

    flush_section()

    order = ["active", "blocked", "upcoming", "done"]
    sections.sort(key=lambda s: order.index(s.status) if s.status in order else 99)
    return sections

# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------
SVG_FILE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>'
            '<polyline points="13 2 13 9 20 9"/></svg>')

DOMAIN_COLORS = {
    "narrative":  "#c2185b",
    "world":      "#388e3c",
    "mechanics":  "#3949ab",
    "infra":      "#7b1fa2",
    "cosmology":  "#0277bd",
    "general":    "#78909c",  # neutral blue-grey for unclassified items
}

def _obs_link(label: str, vault_path: str) -> str:
    href = obsidian_link(vault_path)
    return f'<a class="obs-link" href="{href}">{SVG_FILE}{label}</a>'

_MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')

def _md_links(text: str) -> str:
    """Convert markdown inline links [text](url) to HTML anchors."""
    return _MD_LINK_RE.sub(r'<a href="\2" target="_blank">\1</a>', text)

def _item_html(item: TodoItem) -> str:
    cb = "checked" if item.done else ("blocked" if item.blocked else "")
    tc = "todo-text done-text" if item.done else "todo-text"
    note = ""
    if item.note:
        warn = any(x in item.note for x in ("CRITICAL", "BLOCKED", "ERROR", "wrong"))
        note = f'<div class="todo-note{" warning" if warn else ""}">{_md_links(item.note)}</div>'
    links = "".join(_obs_link(l, p) for l, p in item.links)
    links = f'<div class="todo-links">{links}</div>' if links else ""
    effort = f'<div class="todo-effort">{item.effort}</div>' if item.effort else ""
    return (f'<div class="todo-item"><div class="todo-checkbox {cb}"></div>'
            f'<div class="todo-text-wrap"><div class="{tc}">{_md_links(item.text)}</div>'
            f'{note}{links}{effort}</div></div>')

def _group_html(g: TodoGroup) -> str:
    items = "".join(_item_html(i) for i in g.items)
    return (f'<div class="todo-group" data-domain="{g.domain}">'
            f'<div class="todo-group-header">'
            f'<span class="domain-badge domain-{g.domain}">{g.domain.upper()}</span>'
            f'<span class="todo-group-title">{g.title}</span></div>{items}</div>')

def _section_html(s: Section) -> str:
    groups = "".join(_group_html(g) for g in s.groups)
    return (f'<div class="section" data-status="{s.status}">'
            f'<div class="section-header" onclick="toggleSection(this)">'
            f'<div class="section-header-left">'
            f'<span class="section-status-badge badge-{s.status}">{s.status.title()}</span>'
            f'<span class="section-title">{s.title}</span></div>'
            f'<div style="display:flex;align-items:center;gap:12px;">'
            f'<span class="section-count">{s.subtitle}</span>'
            f'<span class="section-chevron">&#9662;</span></div></div>'
            f'<div class="section-body">{groups}</div></div>')

def _session_card(s: dict) -> str:
    links = "".join(_obs_link(l["label"], l["vault_path"]) for l in s.get("links", []))
    files = f'<div class="session-files">{links}</div>' if links else ""
    return (f'<div class="session-card">'
            f'<div class="session-date">{s["date"]}</div>'
            f'<div class="session-title">{s["title"]}</div>'
            f'<div class="session-summary">{s["summary"]}</div>'
            f'{files}</div>')

def _summary_panel_html(quick_summary: list[dict], player_status: dict) -> str:
    pip_class = {"done": "pip-done", "active": "pip-active", "blocked": "pip-blocked",
                 "info": "pip-info", "pending": "pip-pending"}
    items_html = ""
    for item in quick_summary:
        pc = pip_class.get(item["status"], "pip-info")
        items_html += (f'<div class="summary-item">'
                       f'<div class="summary-pip {pc}"></div>'
                       f'<div>{item["text"]}</div></div>')

    archetypes_html = ""
    for a in player_status.get("archetypes", []):
        cls = a.get("status", "unknown")
        player = a.get("player", "").strip()
        display = f'{a["name"]} - {player}' if player else a["name"]
        archetypes_html += f'<span class="archetype-chip {cls}">{display}</span>'
    chips = f'<div class="archetype-chips">{archetypes_html}</div>' if archetypes_html else ""
    count_display = player_status.get("summary", "")
    player_col = (f'<div class="summary-col">'
                  f'<div class="summary-heading">Player Status</div>'
                  f'<div class="player-count">{count_display}</div>'
                  f'{chips}</div>')
    summary_col = (f'<div class="summary-col">'
                   f'<div class="summary-heading">Quick Summary</div>'
                   f'{items_html}</div>')
    if not items_html and not count_display:
        return ""
    return f'<div class="summary-panel">{summary_col}{player_col}</div>'

def _gauge(label: str, domain: str, pct: int) -> str:
    return (f'<div class="domain-gauge-row">'
            f'<span class="domain-gauge-label">{label}</span>'
            f'<div class="domain-gauge-bar">'
            f'<div class="domain-gauge-fill gauge-{domain}" style="width:{pct}%"></div></div>'
            f'<span class="domain-gauge-pct">{pct}%</span></div>')

def render_html(data: DashboardData) -> str:
    import sys as _sys
    _sys.path.insert(0, str(SCRIPT_DIR.parent))
    from shared.renderer import render_page

    gauges_html = (
        _gauge("Narrative",      "narrative",  data.domain_pcts.get("narrative",  0)) +
        _gauge("World",          "world",      data.domain_pcts.get("world",      0)) +
        _gauge("Mechanics",      "mechanics",  data.domain_pcts.get("mechanics",  0)) +
        _gauge("Infrastructure", "infra",      data.domain_pcts.get("infra",      0)) +
        _gauge("Cosmology",      "cosmology",  data.domain_pcts.get("cosmology",  0))
    )
    crit_html = " &rarr; ".join(
        f"<strong>{s}</strong>" if i == 0 else s
        for i, s in enumerate(data.critical_path)
    )
    sections_html    = "\n".join(_section_html(s) for s in data.sections)
    sessions_html    = "\n".join(_session_card(s) for s in data.recent_sessions)
    has_blockers     = data.blockers != ["No active blockers detected"]
    blockers_class   = "blockers-callout" if has_blockers else "blockers-callout hidden"
    blockers_html    = "\n".join(f'<div class="blocker-chip">{b}</div>' for b in data.blockers)
    summary_panel_html = _summary_panel_html(data.quick_summary, data.player_status)

    return render_page(
        'pages/dashboard.html',
        generation_time   = data.generation_time,
        last_updated      = data.last_updated,
        readiness         = data.readiness,
        gauges_html       = gauges_html,
        crit_html         = crit_html,
        summary_panel_html = summary_panel_html,
        blockers_class    = blockers_class,
        blockers_html     = blockers_html,
        sessions_html     = sessions_html,
        sections_html     = sections_html,
        generator_name    = 'utilities/dashboard/generate_dashboard.py',
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Regenerate Hero Heaven dashboard from TODO.md")
    ap.add_argument("--todo", default=str(TODO_PATH))
    ap.add_argument("--out",  default=str(OUTPUT_PATH))
    ap.add_argument("--json", action="store_true", help="Also write dashboard_data.json alongside HTML")
    ap.add_argument("--open", action="store_true", help="Open dashboard in browser after writing")
    args = ap.parse_args()

    todo_path = Path(args.todo)
    out_path  = Path(args.out)

    if not todo_path.exists():
        print(f"ERROR: {todo_path} not found"); return 1

    print(f"Reading {todo_path.name} ...")
    txt = todo_path.read_text(encoding="utf-8")

    dashboard   = parse_dashboard_md()
    overrides   = dashboard["domain_overrides"]
    domain_pcts = compute_domain_pcts(txt, overrides)
    readiness   = compute_readiness(domain_pcts)
    data = DashboardData(
        last_updated    = dashboard["last_updated"],
        generation_time = extract_generation_time(),
        readiness       = readiness,
        domain_pcts     = domain_pcts,
        critical_path   = dashboard["critical_path"],
        blockers        = dashboard["blockers"],
        recent_sessions = extract_recent_sessions(txt),
        sections        = parse_todo_sections(txt),
        quick_summary   = dashboard["quick_summary"],
        player_status   = dashboard["players"],
    )

    if args.json:
        import dataclasses
        jp = out_path.with_suffix(".json")
        jp.write_text(json.dumps(dataclasses.asdict(data), indent=2), encoding="utf-8")
        print(f"JSON  -> {jp}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(data), encoding="utf-8")

    print(f"\nDashboard -> {out_path}")
    print(f"  Readiness : {readiness}%")
    for d, pct in domain_pcts.items():
        src = " (override)" if d in dashboard["domain_overrides"] else ""
        print(f"  {d:12s}: {pct}%{src}")
    print(f"  Sections  : {len(data.sections)}")
    print(f"  Blockers  : {len(data.blockers)}")

    if args.open:
        import webbrowser
        webbrowser.open(out_path.as_uri())
        print(f"  Opened in browser.")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# Generator protocol wrapper (used by utilities/build.py)
# ---------------------------------------------------------------------------
class _Generator:
    name = "dashboard"
    description = "Regenerate project dashboard from TODO.md"

    def run(self, argv=None):
        import sys as _sys
        _saved = _sys.argv[1:]
        if argv is not None:
            _sys.argv[1:] = list(argv)
        try:
            result = main()
            return result if isinstance(result, int) else 0
        except SystemExit as e:
            return int(e.code) if isinstance(e.code, int) else 0
        finally:
            _sys.argv[1:] = _saved


generator = _Generator()
