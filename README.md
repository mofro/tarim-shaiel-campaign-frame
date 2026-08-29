---
title: Tarim-Shaiel - Project Overview
project: TTRPG_Tarim_Shaiel
type: navigation
status: active
created: 2025-12-05
last_updated: 2026-05-10
---

# Tarim-Shaiel

**A Daggerheart campaign set in a post-imperial world** where heroes awaken to confront the remnants of a fallen empire, navigate emerging power dynamics, and discover their role in shaping the future.

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
| [.claude/README.md](.claude/README.md) | How the AI session is configured — hooks, morning report, skill descriptions |
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
.claude/            Claude Code session config — hooks, skills, morning report pattern
```

---

## Current status

Three of eleven Session 0 awakening scenarios are complete (Warrior, Seeker, Breaker). Cosmological architecture is fully locked. The HTML publishing pipeline is live. See [TODO.md](TODO.md) for the active critical path.

**AI authoring:** Two personas are active — *Lore Keeper* (consistency, documentation) and *Mythweaver* (cosmological and mythic work). See [CLAUDE.md](CLAUDE.md) for full persona protocols and hard constraints.

---

## Infrastructure

| Service | Identifier | Purpose |
|---|---|---|
| Netlify (public) | `tarim-shaiel-campaign` · `f0034da8` | Public player-facing site (`netlify.toml`) |
| Netlify (GM) | `tarim-shaiel-gm` · `ea2db802` | GM-only build (`netlify-gm.toml`); Netlify Identity |
| Netlify (public player) | `tarim-shaiel-public` · `71a7b6c3` | Custom domain (`tarim-shaiel.world`) |
| Supabase Realtime | `wmrxfhxkcbkjipvuyazw` | Session 2 live map sync (`docs/session2-map.html`) |
| MapTiler | env `MAPTILER_KEY`; style `topo-v2` | Location map tiles (local only; not injected in CI) |
| Mapbox | Studio style `mofro/cmjjblqtk000r01pc1m2fhq7c` | Account-owned map style (see `EXTERNAL_TOOLS.md`) |
| OSRM | `router.project-osrm.org` | Route snapping utility (build-time only; no key) |
| GitHub Actions | `.github/workflows/generate-html.yml` | Auto-commits regenerated `docs/` on push to main |

Full details, env vars, and notes in [`services.json`](services.json).
