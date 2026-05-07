#!/usr/bin/env python3
"""
Tarim-Shaiel Dashboard Generator
=================================
Reads Beads issues (.beads/issues.jsonl), DASHBOARD.md (health panel), and
CREATION_SESSIONS.md (session log) to generate docs/dashboard.html.

Usage:
    python generate_dashboard.py
    python generate_dashboard.py --out path/to/output.html
    python generate_dashboard.py --json   # also emit dashboard_data.json

Domain tagging convention (in Beads issue --notes field):
    domain: narrative    -> narrative
    domain: mechanics    -> mechanics
    domain: world        -> world
    domain: infra        -> infra
    domain: cosmology    -> cosmology

Domain percentages are driven by DASHBOARD.md domain_overrides (manually updated
when milestones complete). Beads issue close rate feeds incremental computation
when no override is set for a domain.
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
BEADS_JSONL_PATH = VAULT_ROOT / ".beads" / "issues.jsonl"
SESSIONS_PATH   = VAULT_ROOT / "CREATION_SESSIONS.md"
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
# Beads issue reader
# Reads .beads/issues.jsonl (one JSON object per line), extracts domain tag
# from the notes field using the convention: "domain: <name>"
# ---------------------------------------------------------------------------
_DOMAIN_NOTE_RE = re.compile(r"domain:\s*(\w+)", re.IGNORECASE)
_ALL_DOMAINS = ["narrative", "mechanics", "world", "infra", "cosmology"]

def parse_beads_issues(path: Optional[Path] = None) -> list[dict]:
    """Read .beads/issues.jsonl and return list of issue dicts. Returns [] if missing."""
    p = path or BEADS_JSONL_PATH
    if not p.exists():
        return []
    issues = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            issues.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return issues

def _issue_domain(issue: dict) -> str:
    """Extract domain tag from issue notes field. Returns 'general' if absent."""
    notes = issue.get("notes") or issue.get("note") or ""
    m = _DOMAIN_NOTE_RE.search(notes)
    if m:
        d = m.group(1).lower()
        return d if d in _ALL_DOMAINS else "general"
    # fall back to keyword detection on title
    return detect_domain(issue.get("title", ""), default="general")

# ---------------------------------------------------------------------------
# Domain completion percentages
# Primary: DASHBOARD.md domain_overrides (manually updated at milestones).
# Fallback: closed/(closed+open) ratio from Beads issues for that domain.
# ---------------------------------------------------------------------------
def compute_domain_pcts(beads_issues: list[dict], overrides: dict[str, int]) -> dict[str, int]:
    counts: dict[str, list[int]] = {d: [0, 0] for d in _ALL_DOMAINS}
    for issue in beads_issues:
        domain = _issue_domain(issue)
        if domain not in counts:
            continue
        status = (issue.get("status") or "open").lower()
        counts[domain][1] += 1  # total
        if status == "closed":
            counts[domain][0] += 1  # done

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
# Recent sessions — reads ### Session YYYY-MM-DD entries from CREATION_SESSIONS.md
# ---------------------------------------------------------------------------
SESSION_ENTRY_RE = re.compile(
    r"###\s+Session\s+(\d{4}-\d{2}-\d{2})(.*?)(?=\n###\s+Session\s+\d{4}|\n##\s|\Z)",
    re.DOTALL
)

def extract_recent_sessions(sessions_path: Optional[Path] = None) -> list[dict]:
    """Read CREATION_SESSIONS.md and return the 3 most recent session entries."""
    p = sessions_path or SESSIONS_PATH
    if not p.exists():
        return []
    search_text = p.read_text(encoding="utf-8")
    sessions = []
    for m in SESSION_ENTRY_RE.finditer(search_text):
        body = m.group(2)
        title_m = re.search(r"\*\*([^*\n]+)\*\*", body)
        title = title_m.group(1) if title_m else "Session Update"
        text_lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")]
        summary = text_lines[1] if len(text_lines) > 1 else (text_lines[0] if text_lines else "")
        summary = re.sub(r"\*+|`", "", summary)[:220]
        links = []
        for lm in re.finditer(r"`(/[^`]+\.md)`", body):
            lp = lm.group(1)
            links.append({"label": Path(lp).stem, "vault_path": lp})
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
# Beads section builder
# Maps Beads issue statuses to dashboard sections, groups issues by domain
# ---------------------------------------------------------------------------
_BD_STATUS_TO_SECTION = {
    "open":        "active",
    "in_progress": "active",
    "blocked":     "blocked",
    "deferred":    "upcoming",
    "closed":      "done",
}
SECTION_TITLES = {
    "active":   ("Active Work",                      "Open and in progress"),
    "blocked":  ("Blocked — Decisions Required", "Waiting on decisions or dependencies"),
    "upcoming": ("Deferred",                          "Scheduled for later"),
    "done":     ("Completed",                         "Closed issues"),
}
_DOMAIN_DISPLAY = {
    "narrative":  "Narrative & Session 0",
    "mechanics":  "Mechanics & Campaign Frame",
    "world":      "World-Building",
    "infra":      "Infrastructure",
    "cosmology":  "Cosmological Architecture",
    "general":    "General",
}

def parse_beads_sections(beads_issues: list[dict]) -> list[Section]:
    """Build dashboard sections from Beads issues, grouped by domain."""
    buckets: dict[str, dict[str, list[dict]]] = {s: {} for s in SECTION_TITLES}

    for issue in beads_issues:
        raw_status = (issue.get("status") or "open").lower()
        section_key = _BD_STATUS_TO_SECTION.get(raw_status, "active")
        if section_key not in buckets:
            continue
        domain = _issue_domain(issue)
        buckets[section_key].setdefault(domain, []).append(issue)

    sections: list[Section] = []
    order = ["active", "blocked", "upcoming", "done"]
    for section_key in order:
        domain_map = buckets[section_key]
        if not domain_map:
            continue
        title, subtitle = SECTION_TITLES[section_key]
        section = Section(status=section_key, title=title, subtitle=subtitle)
        for domain in _ALL_DOMAINS + ["general"]:
            issues_in_domain = domain_map.get(domain, [])
            if not issues_in_domain:
                continue
            group_title = _DOMAIN_DISPLAY.get(domain, domain.capitalize())
            group = TodoGroup(title=group_title, domain=domain)
            for issue in issues_in_domain:
                done    = (issue.get("status") or "").lower() == "closed"
                blocked = (issue.get("status") or "").lower() == "blocked"
                text    = issue.get("title") or "(untitled)"
                note    = (issue.get("description") or "").split("\n")[0][:180]
                note    = re.sub(r"\*+|`", "", note).strip()
                group.items.append(TodoItem(text=text, done=done, blocked=blocked, note=note))
            section.groups.append(group)
        if section.groups:
            sections.append(section)
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
    ap = argparse.ArgumentParser(description="Regenerate Tarim-Shaiel dashboard from Beads issues")
    ap.add_argument("--out",  default=str(OUTPUT_PATH))
    ap.add_argument("--json", action="store_true", help="Also write dashboard_data.json alongside HTML")
    ap.add_argument("--open", action="store_true", help="Open dashboard in browser after writing")
    args = ap.parse_args()

    out_path = Path(args.out)

    print("Reading Beads issues ...")
    beads_issues = parse_beads_issues()
    if not beads_issues:
        print(f"WARNING: No issues found in {BEADS_JSONL_PATH} — sections will be empty.")

    dashboard   = parse_dashboard_md()
    overrides   = dashboard["domain_overrides"]
    domain_pcts = compute_domain_pcts(beads_issues, overrides)
    readiness   = compute_readiness(domain_pcts)
    data = DashboardData(
        last_updated    = dashboard["last_updated"],
        generation_time = extract_generation_time(),
        readiness       = readiness,
        domain_pcts     = domain_pcts,
        critical_path   = dashboard["critical_path"],
        blockers        = dashboard["blockers"],
        recent_sessions = extract_recent_sessions(),
        sections        = parse_beads_sections(beads_issues),
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
        src = " (override)" if d in dashboard["domain_overrides"] else " (beads)"
        print(f"  {d:12s}: {pct}%{src}")
    print(f"  Issues    : {len(beads_issues)}")
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
    description = "Regenerate project dashboard from Beads issues + CREATION_SESSIONS.md"

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
