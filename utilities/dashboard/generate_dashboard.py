#!/usr/bin/env python3
"""
Hero Heaven Dashboard Generator
================================
Parses TODO.md and generates hero-heaven-todo-dashboard.html

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
import json
import argparse
from pathlib import Path
from datetime import date
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Paths (relative to this script's location: utilities/dashboard/)
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent
TODO_PATH   = VAULT_ROOT / "TODO.md"
OUTPUT_PATH = VAULT_ROOT / "docs" / "dashboard.html"
# Legacy path kept for reference: VAULT_ROOT / "templates" / "hero-heaven-todo-dashboard.html"

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

def obsidian_link(vault_path: str, vault: str = "HeroHeaven") -> str:
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
    readiness: int
    domain_pcts: dict[str, int]
    critical_path: list[str]
    blockers: list[str]
    recent_sessions: list[dict]
    sections: list[Section]
    quick_summary: list[dict] = field(default_factory=list)
    player_status: dict = field(default_factory=dict)

# ---------------------------------------------------------------------------
# Progress Tracking override parser
# Reads manually-curated percentages from the Progress Tracking section and
# uses them to override checkbox-computed values for that domain.
# ---------------------------------------------------------------------------
PROGRESS_RE = re.compile(r"\*\*([^*]+):\*\*\s*(\d+)%", re.IGNORECASE)
LABEL_TO_DOMAIN = {
    "story": "narrative", "narrative": "narrative",
    "world": "world", "world-building": "world",
    "game mechanics": "mechanics", "mechanics": "mechanics",
    "infrastructure": "infra", "infra": "infra",
    "cosmolog": "cosmology",
}

def extract_manual_overrides(todo_text: str) -> dict[str, int]:
    overrides: dict[str, int] = {}
    in_progress = False
    for line in todo_text.splitlines():
        if re.search(r"##.*PROGRESS TRACKING", line, re.IGNORECASE):
            in_progress = True
        elif in_progress and line.startswith("## "):
            break
        if in_progress:
            for m in PROGRESS_RE.finditer(line):
                label = m.group(1).strip().lower()
                pct   = int(m.group(2))
                for key, domain in LABEL_TO_DOMAIN.items():
                    if key in label:
                        overrides[domain] = pct
                        break
    return overrides

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
    "world": "world", "geographic": "world", "ancestry": "world",
    "location": "world", "orc": "world", "myth": "world", "silk road": "world",
    "npc": "world", "culture": "world",
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
# Blocker extraction
# ---------------------------------------------------------------------------
BLOCKER_PATTERNS = [
    (r"Campaign Frame.*?Archetypes|Classes vs",     "\u26d4 Campaign Frame: Classes vs. Archetypes decision required"),
    (r"liberation_aftermath.*?200|200.year.*?liberation", "\u26a0\ufe0f liberation_aftermath.md — wrong 200yr timeline throughout"),
]

def extract_blockers(todo_text: str) -> list[str]:
    found = []
    for pattern, label in BLOCKER_PATTERNS:
        if re.search(pattern, todo_text, re.IGNORECASE):
            found.append(label)
    return found or ["No active blockers detected"]

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
def extract_last_updated(todo_text: str) -> str:
    m = re.search(r"last_updated:\s*(\d{4}-\d{2}-\d{2})", todo_text)
    if m:
        return m.group(1)
    m = re.search(r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", todo_text)
    return m.group(1) if m else str(date.today())

def extract_critical_path(todo_text: str) -> list[str]:
    m = re.search(r"\*\*Critical Path:\*\*\s*(.+?)(?:\n|$)", todo_text)
    if m:
        return [s.strip() for s in re.split(r"\u2192|->", m.group(1)) if s.strip()]
    return [
        "Cosmological architecture decisions",
        "Complete Session 0 scenarios",
        "Resolve Campaign Frame",
        "Build Charm library",
        "Playtest",
    ]

# ---------------------------------------------------------------------------
# Quick Summary extractor — parses **Quick Summary:** bullets from PROJECT HEALTH
# ---------------------------------------------------------------------------
QUICK_SUMMARY_STATUS_MAP = [
    ("\u2705",  "done"),     # ✅
    ("\U0001f504", "active"),  # 🔄
    ("\u26a0",  "blocked"),  # ⚠ (also ⚠️)
    ("\U0001f195", "info"),  # 🆕
    ("\U0001f5c3", "info"),  # 🗃️
    ("- [x]",   "done"),
    ("- [ ]",   "pending"),
]

def extract_quick_summary(todo_text: str) -> list[dict]:
    items: list[dict] = []
    in_health = False
    in_summary = False
    for line in todo_text.splitlines():
        if re.match(r"^## PROJECT HEALTH", line, re.IGNORECASE):
            in_health = True
            continue
        if in_health and line.startswith("## "):
            break
        if in_health and "**Quick Summary:**" in line:
            in_summary = True
            continue
        if in_summary:
            stripped = line.strip()
            if not stripped:
                continue
            # Stop when we hit a non-list line that isn't blank (e.g. **Players:**)
            if not stripped.startswith("-"):
                break
            text = stripped.lstrip("- ").strip()
            # Strip checkbox markers
            text = re.sub(r"^\[[xX ]\]\s*", "", text)
            # Clean markdown bold
            text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
            # Strip backtick code spans and trailing link references
            text = re.sub(r"`[^`]+`", "", text).strip()
            status = "info"
            for marker, s in QUICK_SUMMARY_STATUS_MAP:
                if marker in stripped:
                    status = s
                    break
            # Truncate long lines for display
            display = text[:240] + ("…" if len(text) > 240 else "")
            items.append({"text": display, "status": status})
    return items

# ---------------------------------------------------------------------------
# Player Status extractor — parses **Players:** line from PROJECT HEALTH
# ---------------------------------------------------------------------------
def extract_player_status(todo_text: str) -> dict:
    m = re.search(r"\*\*Players:\*\*\s*(.+?)(?:\n|$)", todo_text)
    if not m:
        return {"summary": "", "archetypes": []}
    raw = m.group(1).strip()

    # Count: "1/6 committed"
    count_m = re.search(r"(\d+)/(\d+)\s+\w+", raw)
    summary = f"{count_m.group(1)}/{count_m.group(2)} committed" if count_m else ""

    # Archetype list — after the em-dash: "Warrior ✅ | Breaker / Bridge / Seeker / Sacrificer / Visionary ⏳"
    archetypes: list[dict] = []
    after_dash = re.search(r"[—\-]\s*(.+)$", raw)
    if after_dash:
        segment = after_dash.group(1)
        for part in re.split(r"\s*/\s*|\s*\|\s*", segment):
            part = part.strip()
            if not part:
                continue
            if "\u2705" in part:   # ✅
                archetypes.append({"name": part.replace("\u2705", "").strip(), "status": "committed"})
            elif "\u23f3" in part: # ⏳
                archetypes.append({"name": part.replace("\u23f3", "").strip(), "status": "pending"})
            else:
                archetypes.append({"name": part.strip(), "status": "pending"})
    return {"summary": summary, "archetypes": archetypes}

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
        archetypes_html += f'<span class="archetype-chip {cls}">{a["name"]}</span>'
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
    gauge_css = "\n".join(
        f"    .domain-gauge-fill.gauge-{d} {{ background: {c}; }}"
        for d, c in DOMAIN_COLORS.items()
    )
    gauges = (_gauge("Narrative",      "narrative",  data.domain_pcts.get("narrative",  0)) +
              _gauge("World",          "world",      data.domain_pcts.get("world",      0)) +
              _gauge("Mechanics",      "mechanics",  data.domain_pcts.get("mechanics",  0)) +
              _gauge("Infrastructure", "infra",      data.domain_pcts.get("infra",      0)) +
              _gauge("Cosmology",      "cosmology",  data.domain_pcts.get("cosmology",  0)))

    crit = " &rarr; ".join(
        f"<strong>{s}</strong>" if i == 0 else s
        for i, s in enumerate(data.critical_path)
    )
    sections_html = "\n".join(_section_html(s) for s in data.sections)
    sessions_html = "\n".join(_session_card(s) for s in data.recent_sessions)
    blockers_html = "\n".join(f'<div class="blocker-chip">{b}</div>' for b in data.blockers)
    summary_panel = _summary_panel_html(data.quick_summary, data.player_status)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tarim Shaiel &mdash; Project Dashboard</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='10' fill='%231a1208'/><polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 33.4,43.1 18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>">
  <!-- AUTO-GENERATED by utilities/dashboard/generate_dashboard.py &mdash; do not hand-edit -->
  <!-- Style tweaks: add CSS inside STYLE_OVERRIDES block below; document in SKILL.md -->
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inconsolata:wght@400;500&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --ink:#1a1208; --parchment:#f5edd8; --parchment2:#ede0c4;
      --parchment3:#e4d5b0; --gold:#b8922c; --gold-light:#d4a843;
      --crimson:#7a1f1f; --steel:#3c4a5a; --forest:#2a4a2a;
      --rule:rgba(184,146,44,0.35); --shadow:rgba(26,18,8,0.12);
    }}
    html {{ scroll-behavior:smooth; }}
    body {{ background:#111008; background-image: url('images/paper-texture-top-view-2.jpg'); font-family:'EB Garamond',Georgia,serif; font-size:17px; line-height:1.7; color:var(--ink); min-height:100vh; }}
    .page-wrap {{ max-width:1100px; margin:0 auto; background:var(--parchment); box-shadow:0 0 100px rgba(0,0,0,0.8); }}
    .header {{ background:linear-gradient(170deg,#0d0a04 0%,#1a1208 50%,#2a1f0e 100%); padding:48px 60px 40px; position:relative; overflow:hidden; border-bottom:2px solid var(--gold); }}
    .header::after {{ content:''; position:absolute; inset:0; background:radial-gradient(ellipse at 60% 50%,rgba(184,146,44,0.08) 0%,transparent 70%); pointer-events:none; }}
    .header-inner {{ display:flex; align-items:flex-start; justify-content:space-between; gap:40px; position:relative; z-index:1; }}
    .header-eyebrow {{ font-family:'Inconsolata',monospace; font-size:13px; letter-spacing:0.25em; text-transform:uppercase; color:var(--gold); opacity:0.75; margin-bottom:8px; }}
    .header-title {{ font-family:'Cinzel',serif; font-size:32px; font-weight:700; color:var(--gold-light); letter-spacing:0.04em; line-height:1.2; text-shadow:0 2px 20px rgba(184,146,44,0.3); }}
    .header-subtitle {{ font-size:16px; color:rgba(245,237,216,0.6); font-style:italic; margin-top:6px; }}
    .header-meta {{ text-align:right; flex-shrink:0; }}
    .last-updated {{ font-family:'Inconsolata',monospace; font-size:13px; color:rgba(245,237,216,0.45); letter-spacing:0.1em; }}
    .health-panel {{ background:var(--parchment2); border-bottom:1px solid var(--rule); padding:28px 60px; display:grid; grid-template-columns:1fr 1fr 1fr; }}
    .health-cell {{ padding:0 30px; border-right:1px solid var(--rule); }}
    .health-cell:first-child {{ padding-left:0; }}
    .health-cell:last-child {{ border-right:none; }}
    .health-label {{ font-family:'Inconsolata',monospace; font-size:13px; letter-spacing:0.2em; text-transform:uppercase; color:var(--gold); margin-bottom:6px; }}
    .health-value {{ font-family:'Cinzel',serif; font-size:24px; font-weight:600; color:var(--ink); }}
    .health-note {{ font-size:14px; font-style:italic; color:rgba(26,18,8,0.55); margin-top:3px; }}
    .progress-bar-wrap {{ margin-top:1px; height:6px; background:rgba(26,18,8,0.12); border-radius:3px; overflow:hidden; }}
    .progress-bar-fill {{ height:100%; background:linear-gradient(90deg,var(--gold) 0%,var(--gold-light) 100%); border-radius:3px; }}
    .domain-gauges {{ display:flex; flex-direction:column; gap:5px; margin-top:8px; }}
    .domain-gauge-row {{ display:flex; align-items:center; gap:8px; }}
    .domain-gauge-label {{ width:90px; font-family:'Inconsolata',monospace; font-size:12px; color:rgba(26,18,8,0.7); }}
    .domain-gauge-bar {{ flex:1; height:4px; background:rgba(26,18,8,0.1); border-radius:2px; overflow:hidden; }}
    .domain-gauge-fill {{ height:100%; background:var(--gold); border-radius:2px; }}
{gauge_css}
    .domain-gauge-pct {{ width:32px; text-align:right; font-family:'Inconsolata',monospace; font-size:12px; color:rgba(26,18,8,0.7); }}
    .critical-path {{ margin-top:8px; font-size:14px; color:rgba(26,18,8,0.7); font-style:italic; }}
    .critical-path strong {{ color:var(--crimson); font-style:normal; font-weight:600; }}
    .blockers-callout {{ background:#2a1208; border-top:1px solid #5a2a10; border-bottom:1px solid #5a2a10; padding:20px 60px; display:flex; gap:16px; flex-wrap:wrap; align-items:flex-start; }}
    .blocker-eyebrow {{ font-family:'Inconsolata',monospace; font-size:12px; letter-spacing:0.2em; text-transform:uppercase; color:#d4843b; margin-bottom:10px; flex-basis:100%; }}
    .blocker-chip {{ background:rgba(122,31,31,0.25); border:1px solid rgba(122,31,31,0.5); border-radius:3px; padding:6px 12px; font-size:14px; color:#f5c9a0; font-family:'Inconsolata',monospace; }}
    .sessions-panel {{ background:var(--parchment3); border-bottom:1px solid var(--rule); padding:24px 60px; }}
    .sessions-heading {{ font-family:'Inconsolata',monospace; font-size:15px; letter-spacing:0.2em; text-transform:uppercase; color:var(--gold); margin-bottom:14px; }}
    .sessions-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
    .session-card {{ background:var(--parchment); border:1px solid var(--rule); border-radius:3px; padding:14px 16px; }}
    .session-date {{ font-family:'Inconsolata',monospace; font-size:12px; color:var(--gold); margin-bottom:4px; }}
    .session-title {{ font-family:'Cinzel',serif; font-size:14px; font-weight:600; color:var(--ink); margin-bottom:6px; }}
    .session-summary {{ font-size:14px; color:rgba(26,18,8,0.7); font-style:italic; line-height:1.5; }}
    .session-files {{ margin-top:8px; display:flex; flex-wrap:wrap; gap:4px; }}
    .obs-link {{ display:inline-flex; align-items:center; gap:4px; font-family:'Inconsolata',monospace; font-size:12px; color:var(--steel); background:rgba(60,74,90,0.08); border:1px solid rgba(60,74,90,0.2); border-radius:2px; padding:2px 7px; text-decoration:none; transition:background 0.2s,color 0.2s; }}
    .obs-link:hover {{ background:rgba(60,74,90,0.18); color:var(--ink); }}
    .obs-link svg {{ width:10px; height:10px; flex-shrink:0; }}
    .filter-bar {{ padding:16px 60px; background:var(--parchment2); border-bottom:1px solid var(--rule); display:flex; gap:24px; flex-wrap:wrap; align-items:center; }}
    .filter-group {{ display:flex; gap:6px; align-items:center; flex-wrap: wrap;  }}
    .filter-label {{ font-family:'Inconsolata',monospace; font-size:15px; letter-spacing:0.15em; text-transform:uppercase; color:rgba(26,18,8,0.5); margin-right:4px; }}
    .filter-btn {{ font-family:'Inconsolata',monospace; font-size:13px; padding:4px 10px; border:1px solid var(--rule); border-radius:2px; background:var(--parchment); color:rgba(26,18,8,0.6); cursor:pointer; transition:all 0.15s; }}
    .filter-btn:hover {{ border-color:var(--gold); color:var(--ink); }}
    .filter-btn.active {{ background:var(--ink); color:var(--parchment); border-color:var(--ink); }}
    .main {{ padding:40px 60px; }}
    .section {{ margin-bottom:32px; border:1px solid var(--rule); border-radius:3px; overflow:hidden; }}
    .section.hidden {{ display:none; }}
    .section-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 20px; cursor:pointer; user-select:none; border-bottom:1px solid var(--rule); transition:background 0.15s; }}
    .section-header:hover {{ background:rgba(184,146,44,0.05); }}
    .section-header-left {{ display:flex; align-items:center; gap:12px; }}
    .section-status-badge {{ font-family:'Inconsolata',monospace; font-size:13px; padding:3px 8px; border-radius:2px; letter-spacing:0.08em; font-weight:500; }}
    .badge-active   {{ background:#e8f5e9; color:#2e7d32; border:1px solid #a5d6a7; }}
    .badge-blocked  {{ background:#fbe9e7; color:#c62828; border:1px solid #ef9a9a; }}
    .badge-upcoming {{ background:#fff8e1; color:#f57f17; border:1px solid #ffe082; }}
    .badge-done     {{ background:#f3e5f5; color:#6a1b9a; border:1px solid #ce93d8; }}
    .section-title {{ font-family:'Cinzel',serif; font-size:17px; font-weight:600; color:var(--ink); }}
    .section-count {{ font-family:'Inconsolata',monospace; font-size:13px; color:rgba(26,18,8,0.45); }}
    .section-chevron {{ color:rgba(26,18,8,0.4); transition:transform 0.2s; font-size:15px; }}
    .section.collapsed .section-chevron {{ transform:rotate(-90deg); }}
    .section.collapsed .section-body {{ display:none; }}
    .todo-group {{ border-bottom:1px solid rgba(184,146,44,0.15); }}
    .todo-group:last-child {{ border-bottom:none; }}
    .todo-group-header {{ padding:10px 20px 8px; display:flex; align-items:center; gap:10px; background:rgba(184,146,44,0.04); border-bottom:1px solid rgba(184,146,44,0.1); }}
    .domain-badge {{ font-family:'Inconsolata',monospace; font-size:13px; padding:2px 7px; border-radius:2px; letter-spacing:0.1em; text-transform:uppercase; }}
    .domain-narrative {{ background:#fce4ec; color:#880e4f; border:1px solid #f48fb1; }}
    .domain-mechanics {{ background:#e8eaf6; color:#283593; border:1px solid #9fa8da; }}
    .domain-world     {{ background:#e8f5e9; color:#1b5e20; border:1px solid #a5d6a7; }}
    .domain-infra     {{ background:#f3e5f5; color:#4a148c; border:1px solid #ce93d8; }}
    .domain-cosmology {{ background:#e1f5fe; color:#01579b; border:1px solid #81d4fa; }}
    .domain-general   {{ background:#eceff1; color:#37474f; border:1px solid #b0bec5; }}
    .todo-group-title {{ font-family:'Cinzel',serif; font-size:14px; font-weight:600; color:var(--ink); }}
    .todo-item {{ padding:10px 20px 10px 32px; display:flex; gap:12px; align-items:flex-start; border-bottom:1px solid rgba(184,146,44,0.08); transition:background 0.15s; }}
    .todo-item:last-child {{ border-bottom:none; }}
    .todo-item:hover {{ background:rgba(184,146,44,0.04); }}
    .todo-checkbox {{ width:16px; height:16px; border:1.5px solid var(--rule); border-radius:2px; flex-shrink:0; margin-top:3px; position:relative; background:var(--parchment); }}
    .todo-checkbox.checked {{ background:var(--forest); border-color:var(--forest); }}
    .todo-checkbox.checked::after {{ content:'\u2713'; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:white; font-size:11px; }}
    .todo-checkbox.blocked {{ background:var(--crimson); border-color:var(--crimson); }}
    .todo-checkbox.blocked::after {{ content:'\u2298'; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:white; font-size:9px; }}
    .todo-text-wrap {{ flex:1; min-width:0; }}
    .todo-text {{ font-size:15.5px; color:var(--ink); line-height:1.5; }}
    .todo-text.done-text {{ color:rgba(26,18,8,0.4); text-decoration:line-through; }}
    .todo-note {{ font-size:13.5px; font-style:italic; color:rgba(26,18,8,0.5); margin-top:2px; line-height:1.4; }}
    .todo-note.warning {{ color:#9a3010; }}
    .todo-links {{ display:flex; gap:5px; flex-wrap:wrap; margin-top:5px; }}
    .todo-effort {{ font-family:'Inconsolata',monospace; font-size:12px; color:rgba(26,18,8,0.4); margin-top:3px; }}
    .footer {{ background:#1a1208; padding:24px 60px; display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(184,146,44,0.3); }}
    .footer-text {{ font-family:'Inconsolata',monospace; font-size:13px; color:rgba(245,237,216,0.3); letter-spacing:0.1em; }}
    .footer a {{ display: flex; align-items: center; justify-content: center; }}
    .footer img {{ width: 24px; cursor: auto; }}
    .footer-copyright {{ position:relative; margin-top: 0.15rem; }}
    .collapse-all-btn {{ font-family:'Inconsolata',monospace; font-size:13px; padding:6px 14px; border:1px solid rgba(184,146,44,0.3); border-radius:2px; background:transparent; color:rgba(245,237,216,0.5); cursor:pointer; transition:all 0.15s; }}
    .collapse-all-btn:hover {{ border-color:var(--gold); color:var(--gold-light); }}

    
    @media (max-width: 700px) {{
      .header {{ padding: 28px 20px 24px; }}
      .header-inner {{ flex-direction: column; gap: 16px; }}
      .header-meta {{ text-align: left; }}
      .health-panel {{ grid-template-columns: 1fr; padding: 20px 20px; gap: 0; }}
      .health-cell {{ padding: 14px 0; border-right: none; border-bottom: 1px solid var(--rule); }}
      .health-cell:last-child {{ border-bottom: none; padding-bottom: 0; }}
      .sessions-panel {{ padding: 20px 20px; }}
      .sessions-grid {{ grid-template-columns: 1fr; }}
      .blockers-callout {{ padding: 16px 20px; }}
      .filter-bar {{ padding: 12px 20px; }}
      .main {{ padding: 24px 20px; }}
      .footer {{ padding: 20px 20px; flex-direction: column; gap: 12px; align-items: flex-start; }}
    }}
    /* --- Summary + Player Status panel --- */
    .summary-panel {{ background:var(--parchment2); border-bottom:1px solid var(--rule); padding:22px 60px; display:grid; grid-template-columns:1fr 1fr; gap:0; }}
    .summary-col {{ padding:0 30px 0 0; border-right:1px solid var(--rule); }}
    .summary-col:last-child {{ padding:0 0 0 30px; border-right:none; }}
    .summary-heading {{ font-family:'Inconsolata',monospace; font-size:13px; letter-spacing:0.2em; text-transform:uppercase; color:var(--gold); margin-bottom:10px; }}
    .summary-item {{ display:flex; align-items:flex-start; gap:8px; font-size:13.5px; color:rgba(26,18,8,0.75); line-height:1.45; margin-bottom:6px; }}
    .summary-pip {{ flex-shrink:0; width:10px; height:10px; border-radius:50%; margin-top:4px; }}
    .pip-done    {{ background:#2e7d32; }}
    .pip-active  {{ background:#f57f17; }}
    .pip-blocked {{ background:#c62828; }}
    .pip-info    {{ background:#0277bd; }}
    .pip-pending {{ background:rgba(26,18,8,0.2); }}
    .player-count {{ font-family:'Cinzel',serif; font-size:20px; font-weight:600; color:var(--ink); margin-bottom:10px; }}
    .archetype-chips {{ display:flex; flex-wrap:wrap; gap:6px; }}
    .archetype-chip {{ font-family:'Inconsolata',monospace; font-size:13px; padding:4px 10px; border-radius:2px; border:1px solid; }}
    .archetype-chip.committed {{ background:#e8f5e9; color:#1b5e20; border-color:#a5d6a7; }}
    .archetype-chip.pending   {{ background:rgba(26,18,8,0.05); color:rgba(26,18,8,0.45); border-color:rgba(26,18,8,0.15); }}
    .archetype-chip.unknown   {{ background:#fff8e1; color:#f57f17; border-color:#ffe082; }}
    @media (max-width:700px) {{
      .summary-panel {{ grid-template-columns:1fr; padding:16px 20px; }}
      .summary-col {{ padding:0 0 16px 0; border-right:none; border-bottom:1px solid var(--rule); }}
      .summary-col:last-child {{ padding:16px 0 0 0; border-bottom:none; }}
    }}
    /* =====================================================
       STYLE_OVERRIDES
       Add your CSS overrides here. Document in SKILL.md.
       ===================================================== */
  </style>
</head>
<body>
<div class="page-wrap">

  <header class="header">
    <div class="header-inner">
      <div>
        <div class="header-eyebrow">Tarim-Shaiel Campaign &middot; Daggerheart System</div>
        <div class="header-title">TODO & Project Dashboard</div>
        <div class="header-subtitle">State of the world as of {data.last_updated}</div>
      </div>
      <div class="header-meta">
        <div class="last-updated">TODO.md last updated: {data.last_updated}</div>
        <div class="last-updated" style="margin-top:4px">Dun-Kharan caravan departs at dawn</div>
      </div>
    </div>
  </header>

  <div class="health-panel">
    <div class="health-cell">
      <div class="health-label">Campaign Readiness</div>
      <div class="health-value">{data.readiness}%</div>
      <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{data.readiness}%"></div></div>
      <div class="health-note">Weighted average of domain progress</div>
    </div>
    <div class="health-cell">
      <div class="health-label">Domain Progress</div>
      <div class="domain-gauges">{gauges}</div>
    </div>
    <div class="health-cell">
      <div class="health-label">Critical Path</div>
      <div class="critical-path">{crit}</div>
    </div>
  </div>

  {summary_panel}

  <div class="blockers-callout">
    <div class="blocker-eyebrow">&#9888; Open Blockers &amp; Upstream Dependencies</div>
    {blockers_html}
  </div>

  <div class="sessions-panel">
    <div class="sessions-heading">Recent Sessions</div>
    <div class="sessions-grid">{sessions_html}</div>
  </div>

  <div class="filter-bar">
    <div class="filter-group">
      <span class="filter-label">Status</span>
      <button class="filter-btn active" data-filter-status="all">All</button>
      <button class="filter-btn" data-filter-status="active">Active</button>
      <button class="filter-btn" data-filter-status="blocked">Blocked</button>
      <button class="filter-btn" data-filter-status="upcoming">Upcoming</button>
      <button class="filter-btn" data-filter-status="done">Done</button>
    </div>
    <div class="filter-group">
      <span class="filter-label">Domain</span>
      <button class="filter-btn active" data-filter-domain="all">All</button>
      <button class="filter-btn" data-filter-domain="narrative">Narrative</button>
      <button class="filter-btn" data-filter-domain="mechanics">Mechanics</button>
      <button class="filter-btn" data-filter-domain="world">World</button>
      <button class="filter-btn" data-filter-domain="infra">Infra</button>
      <button class="filter-btn" data-filter-domain="cosmology">Cosmology</button>
    </div>
    <div class="filter-group" style="margin-left:auto">
      <button class="filter-btn" id="toggle-done-btn" onclick="toggleDone()">Show Completed</button>
    </div>
  </div>

  <div class="main">{sections_html}</div>

  <footer class="footer">
    <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener noreferrer"><div class="footer-copyright"><img src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"/><img src="https://mirrors.creativecommons.org/presskit/icons/by.svg"/><img src="https://mirrors.creativecommons.org/presskit/icons/sa.svg"/></div></a><div class="footer-text"> MAURICE GASTON 2025 &middot; TTRPG PROJECT &middot; TARIM-SHAIEL &middot; DUN-KHARAN</div>
    <button class="collapse-all-btn" onclick="collapseAll()">Collapse All</button>
  </footer>

</div>
<script>
  function toggleSection(h) {{ h.closest('.section').classList.toggle('collapsed'); }}
  function collapseAll() {{ document.querySelectorAll('.section').forEach(s => s.classList.add('collapsed')); }}
  let activeStatus = 'all', activeDomain = 'all', hideDone = true;
  function toggleDone() {{
    hideDone = !hideDone;
    const btn = document.getElementById('toggle-done-btn');
    btn.textContent = hideDone ? 'Show Completed' : 'Hide Completed';
    btn.classList.toggle('active', !hideDone);
    applyFilters();
  }}
  document.querySelectorAll('[data-filter-status]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('[data-filter-status]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active'); activeStatus = btn.dataset.filterStatus; applyFilters();
    }});
  }});
  document.querySelectorAll('[data-filter-domain]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('[data-filter-domain]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active'); activeDomain = btn.dataset.filterDomain; applyFilters();
    }});
  }});
  function applyFilters() {{
    // Section-level: status filter
    document.querySelectorAll('.section').forEach(s => {{
      s.classList.toggle('hidden', activeStatus !== 'all' && s.dataset.status !== activeStatus);
    }});
    // Item-level: hide checked items when hideDone
    document.querySelectorAll('.todo-item').forEach(item => {{
      const checked = item.querySelector('.todo-checkbox.checked') !== null;
      item.style.display = (hideDone && checked) ? 'none' : '';
    }});
    // Group-level: domain filter + hide groups where all items are invisible
    document.querySelectorAll('.todo-group').forEach(g => {{
      const domainOk = activeDomain === 'all' || g.dataset.domain === activeDomain;
      const hasVisible = Array.from(g.querySelectorAll('.todo-item')).some(i => i.style.display !== 'none');
      g.style.display = (domainOk && hasVisible) ? '' : 'none';
    }});
    // Hide sections where all groups are hidden
    document.querySelectorAll('.section:not(.hidden)').forEach(s => {{
      const any = Array.from(s.querySelectorAll('.todo-group')).some(g => g.style.display !== 'none');
      if (!any) s.classList.add('hidden');
    }});
  }}
  applyFilters();
</script>
</body>
</html>"""

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

    overrides   = extract_manual_overrides(txt)
    domain_pcts = compute_domain_pcts(txt, overrides)
    readiness   = compute_readiness(domain_pcts)
    data = DashboardData(
        last_updated    = extract_last_updated(txt),
        readiness       = readiness,
        domain_pcts     = domain_pcts,
        critical_path   = extract_critical_path(txt),
        blockers        = extract_blockers(txt),
        recent_sessions = extract_recent_sessions(txt),
        sections        = parse_todo_sections(txt),
        quick_summary   = extract_quick_summary(txt),
        player_status   = extract_player_status(txt),
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
        src = " (override)" if d in overrides else ""
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
