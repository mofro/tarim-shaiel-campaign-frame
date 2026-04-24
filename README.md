---
title: Tarim-Shaiel - Project Overview
project: TTRPG_Tarim_Shaiel
type: navigation
status: active
created: 2025-12-05
last_updated: 2026-04-24
---

# Tarim-Shaiel

**A Daggerheart campaign set in a post-imperial Silk Road world (~1450s CE).** Heroes are 1,000-year-old legendary champions who earned paradise, failed to recognize their unfinished work, and have been expelled to discover what they left undone. The Wizard is the primary antagonist; the true endgame threat is a set of liminal consciousnesses — the Held Breath — whose awakening the heroes must prevent.

---

## What is this repository?

A design and authoring workspace — Markdown files with YAML frontmatter, an Obsidian vault, a Python publishing pipeline, and two live Netlify sites. There is no build system in the software sense, no tests, no app to run.

**Live sites:**
- [Public site](https://tarim-shaiel.netlify.app) — player-facing content, visibility-gated at build time
- GM site — full content including `gm_secrets/` pages, protected by Netlify Identity (invite-only)

---

## Where to start

| File | Purpose |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Full project instructions, domain index, conventions — start here for AI sessions |
| [TODO.md](TODO.md) | Active task list, session log, source of truth for current state |
| [DASHBOARD.md](DASHBOARD.md) | Project health panel — critical path, player status, blockers |
| [GM_AUTHORING.md](GM_AUTHORING.md) | GM markdown conventions — inline redaction, callout blocks, file transclusion |

---

## Project structure

```
narrative/          Campaign story, Session 0 awakening scenarios, GM secrets
world/              Regions, locations, factions, events, ancestries, cosmology
mechanics/          Daggerheart integration, tool progression, R/H/K framework
templates/          Authoring templates for all domains
utilities/          Python publishing pipeline (generators, build.py, dashboard)
images/             Source images (ancestry portraits committed; others gitignored)
docs/               Generated HTML output (build artifact, gitignored except login.html)
lat.md/             AI navigation layer — read before diving into domain content
```

---

## Current status

Three of six core Session 0 awakening scenarios are complete (Warrior, Seeker, Breaker). Cosmological architecture is fully locked. The HTML publishing pipeline is live. See [TODO.md](TODO.md) for the active critical path.

**AI authoring:** Two personas are active — *Lore Keeper* (consistency, documentation) and *Mythweaver* (cosmological and mythic work). See [CLAUDE.md](CLAUDE.md) for full persona protocols and hard constraints.
