# Claude Code Session Configuration

This directory configures how Claude Code sessions behave in this project. It is not campaign content — it is the tooling layer that makes AI-assisted authoring sessions consistent, aware, and productive.

---

## What lives here

```
.claude/
  settings.json       Hooks (SessionStart, PreCompact, PreToolUse) + permissions
  skills/
    commit-hygiene/   Commit path discipline (content vs. infra vs. operational)
    morning-report/   Session-opening project briefing (see below)
  README.md           This file
```

---

## Hooks (`settings.json`)

Three hooks are active. Each fires at a specific point in the session lifecycle.

### `SessionStart`
Fires once when a session opens, before the first user message is processed.

**What it runs:**
1. `bd prime` — restores the Beads workflow context (commands, memories, session close protocol) into the session
2. A framework-aware data gather — runs `bd list`, `bd ready`, `bd stale`, and `git log` so the morning report data is pre-loaded into context before Claude responds

**Why:** Without `bd prime`, Claude Code has no knowledge of the Beads workflow after a session boundary. Without pre-gathering, the morning report would require Claude to run several commands reactively on first response, adding latency.

### `PreCompact`
Fires before the conversation is compacted (context window management).

**What it runs:** `bd prime`

**Why:** Compaction clears conversational context. Re-running `bd prime` restores the workflow context so Claude doesn't lose track of the Beads command set or session close protocol after compaction.

### `PreToolUse` (Bash matcher)
Fires before any Bash tool call that contains `git push`.

**What it runs:** `git fetch origin main && git rebase origin/main`

**Why:** Prevents push failures caused by diverged branches. Auto-rebases before every push so conflicts surface early, locally, rather than mid-push.

---

## The Morning Report Pattern

### What it is

When a session opens with no specific task — a greeting, an open opener, or "what should I work on" — Claude automatically generates a project state briefing before responding to anything else. This is the **morning report**.

It is not a chatbot nicety. It is a structured data pull that answers the real question behind most session-opening greetings: *where were we, and what's next?*

### What it reports

The morning report gathers from whatever tracking frameworks are present:

| Source | What it pulls |
|---|---|
| Beads (`bd`) | In-progress items, P0/P1 open issues, no-blocker ready items, stale issues |
| `DASHBOARD.md` | Critical path, blockers, player status |
| `CREATION_SESSIONS.md` | Last 2 session entries — recent context |
| git | Last 5 commits, uncommitted work |
| `TODO.md` | Open items (fallback if no other framework) |

### Report format

```
## Morning Report — YYYY-MM-DD

**Active**          [In-progress / claimed items]
**Priority Queue**  [P0 critical, P1 high]
**Ready to Work**   [No-blocker items, by priority]
**Needs Review**    [Stale, blocked, or potentially outdated items]

**Recommended Next**
> [Single action — one sentence. Issue ID + one-phrase rationale.]
```

### How it triggers

- Automatically: greeting messages, open openers ("what's up", "catch me up", "what's next")
- Explicitly: `/morning-report` at any point in a session
- Skipped: if the opening message names a concrete task

The trigger logic lives in `skills/morning-report/SKILL.md` (the skill description field). The instruction to obey it lives in `CLAUDE.md` under `## Morning Report`.

### The two-layer design

The morning report is implemented across two layers intentionally:

1. **The hook** (`settings.json` `SessionStart`) pre-gathers raw data at session open — this runs unconditionally and is fast
2. **The skill** (`skills/morning-report/SKILL.md`) + **the instruction** (`CLAUDE.md`) tell Claude what to *do* with that data when the first message is a greeting

Separating data-gather from formatting means the report is instant (data is already in context) and the format logic is auditable and editable without touching infrastructure.

---

## The `commit-hygiene` skill

Defines three work paths and the correct git workflow for each:
- **Content** (prose, lore, world-building) → commit directly to `main`
- **Infra** (generators, CI, pipeline scripts) → feature branch → PR → merge
- **Operational** (beads, session logs, dashboard) → isolated commit to `main`, never bundled with content or infra

See `skills/commit-hygiene/SKILL.md` for the full decision tree, grey zone file resolution, and commit message prefixes.

---

## Transferring the morning report to another project

The skill (`~/.claude/skills/morning-report/SKILL.md`) is installed globally and available in any Claude Code session. To enable the morning report in a different project:

**Step 1** — Add this block to that project's `CLAUDE.md`:

```markdown
## Morning Report

When the first user message in a session contains no specific task (greetings, open-ended openers, "what should I work on", etc.), run the morning-report skill before responding. Gather data using whatever tracking frameworks are present in this project — Beads (`bd`), `DASHBOARD.md`, `CREATION_SESSIONS.md`, git log, or `TODO.md`. Present a scannable briefing using the format defined in the skill.

Skip the report only if the user's opening message names a concrete task or question.
```

**Step 2 (optional but recommended)** — Add a `SessionStart` hook to that project's `.claude/settings.json` to pre-gather data. Adapt the command to whatever tracking system the project uses:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "command": "echo '=== SESSION STATE ===' && git log --oneline -5 2>/dev/null",
            "type": "command"
          }
        ],
        "matcher": ""
      }
    ]
  }
}
```

That is the complete transfer. No code to copy, no framework dependency — the skill handles detection automatically.
