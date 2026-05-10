---
name: commit-hygiene
description: Enforce commit discipline across a project by classifying work into content, infra, or operational paths and applying the correct git workflow for each. Use this skill at the start of any session that will involve commits, when the user says they're about to do "content work", "infra work", "world-building", "pipeline changes", or similar. Also triggers on "commit hygiene", "what branch should I be on", "ready to commit", or any time staged files are about to be committed and their path membership is ambiguous. The skill should also trigger proactively at commit time if it detects files from different work types being bundled together.
---

# Commit Hygiene

Three kinds of work exist in any project. Each has a different git path, and mixing them is the source of most commit tangles. The goal of this skill is to make the right path obvious before work starts — not to untangle it afterward.

---

## Session Declaration

At the start of a session (or when this skill first triggers), establish which work type is in play. Ask if it isn't clear from context:

> "What kind of work are we doing — content, infra, or operational cleanup? Or a mix?"

Hold the declared type for the session. Use it to validate staging decisions at commit time.

If the user doesn't know yet, default to **observing** — classify work as it emerges, flag if types start mixing.

---

## The Three Paths

### Content Path
**What:** Prose, lore, world-building, character work, narrative, session materials, campaign documents.

**File signals:**
- `world/**`, `narrative/**`, `characters/**`, `mechanics/**` (non-script files)
- Any `.md` that is a creative or campaign document

**Git path:** Commit directly to `main`. No branch needed.

**Commit message prefix:** `narrative:`, `world:`, `characters:`, `mechanics:`

**Example:**
```
world: add Scholar's Remnant faction stub
narrative: complete Seeker Awakening segment 3–5
```

---

### Infra Path
**What:** Generator scripts, pipeline tooling, build scripts, CI/CD config, any Python or shell that produces output.

**File signals:**
- `utilities/**/*.py`
- `netlify.toml`, CI config files, `*.sh`
- Generator templates that feed into code (not narrative templates)

**Git path:** Feature branch → PR → merge to main. Branch named after the issue or feature (e.g., `HeroHeaven-73o`, `feature/search-refactor`).

**Commit message prefix:** `infra:`, `pipeline:`

**Rules:**
- Operational files (beads, logs) must not be included in the infra commit — they travel the operational path separately
- The PR should touch only infra files

**Example:**
```
infra: generator factory pattern — Stage 5 cleanup
pipeline: add --public flag to world-all generator
```

---

### Operational Path
**What:** Issue tracker state, session logs, project health panel, navigation indexes, project instructions.

**File signals:**
- `.beads/issues.jsonl`
- `CREATION_SESSIONS.md`, `DASHBOARD.md`
- `lat.md/**` (navigational summaries)
- `CLAUDE.md`, `README.md`
- `.meta/DECISION_LOG.md` (write-only; operational)

**Git path:** Commit directly to `main`. Always as a **separate commit** — never bundled with content or infra changes.

**Commit message prefix:** `chore:`

**Rules:**
- Operational commits must be isolated. A beads close and a narrative edit are two commits, not one.
- If infra work is on a feature branch, the beads close for that work goes to `main` independently — not on the branch.

**Example:**
```
chore: close HeroHeaven-73o in beads
chore: update CREATION_SESSIONS.md — session 2026-05-10
```

---

## Grey Zone Files

Some files don't obviously belong to one path. Resolve them as follows:

| File | Path | Reason |
|---|---|---|
| `CLAUDE.md` | Operational | Project instructions, not creative content |
| `lat.md/**` | Operational | Navigation infrastructure |
| `templates/_TEMPLATE_*.md` | Content | Narrative/world templates |
| `templates/*.md` used by generators | Infra | If edited to change generator output |
| `docs/**` (generated HTML) | Infra | Build artifacts; follow the generator that produced them |
| `README.md` | Operational | Project-level documentation |
| `.gitignore` | Infra | Build/repo configuration |

When genuinely ambiguous, ask. A wrong classification caught before commit costs nothing; caught after a force-push costs time.

---

## Mixed Sessions

When a session legitimately touches multiple work types (e.g., you fix a generator bug and also write a faction stub):

1. **Stage and commit each type separately.** Don't let `git add .` bundle them.
2. **Infra changes go to the feature branch first.** Merge to main before committing content changes on main — or commit content to main first, then branch for infra. Never mix on the same branch.
3. **Operational commits are always last** — after content and infra are resolved — so they reflect the true final state of the tracker.

---

## Commit-Time Sanity Check

Before any commit, run a mental check (or literally check `git diff --cached --name-only`):

1. Do all staged files belong to the same work path?
2. If on a feature branch, are operational files excluded?
3. Does the commit message prefix match the work type?

If any of these fail — stop, unstage the violating files, and commit them separately on the correct path.

---

## Commit Message Format

```
<prefix>: <what changed> [optional: why/context]
```

- One line for the summary; body optional for context
- Prefix must match the work type (see each path above)
- Be specific: `narrative: complete Seeker Awakening v1.0` not `narrative: updates`

---

## Quick Reference

| Work type | Branch? | Prefix | Can bundle with? |
|---|---|---|---|
| Content | No (main) | `narrative:` `world:` etc. | Other content only |
| Infra | Yes (feature) | `infra:` `pipeline:` | Other infra only |
| Operational | No (main) | `chore:` | Nothing — always isolated |
