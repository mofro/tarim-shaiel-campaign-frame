---
title: Project Dashboard
project: TTRPG_Tarim_Shaiel
type: operational
visibility: internal
status: active
last_updated: 2026-05-01  # session 4

critical_path:
  - Resolve cosmological architecture
  - Complete Session 0 scenarios
  - Resolve Campaign Frame
  - Playtest

players:
  committed: 1
  total: 6
  archetypes:
    - {name: Warrior,    status: committed}
    - {name: Breaker,    status: pending}
    - {name: Bridge,     status: pending}
    - {name: Seeker,     status: pending}
    - {name: Sacrificer, status: pending}
    - {name: Visionary,  status: pending}
    - {name: Trickster,  status: pending}
    - {name: Crafter,    status: pending}
    - {name: Sentinel,   status: pending}
    - {name: Healer,     status: pending}

domain_overrides:
  # Uncomment + set a value to manually pin a domain's percentage.
  # Remove entry to let checkbox counts drive it.
  # world: 42
  # mechanics: 80

blockers:
  # - "⛔ Description of active blocker"
---

## Quick Summary

- [x] **Core complete:** Campaign narrative, world geography, fantasy naming, charm architecture, Orc cultural framework, Silk Road weapons, Cosmological architecture (all 8 decisions locked 2026-03-17), World entity infrastructure (factions/events/concepts indexes + all location templates 2026-03-10), Preliminary world diagrams (2026-03-13), HTML publishing pipeline + Netlify deployment (2026-03-15), Visibility gating + Obsidian Shell Commands integration (2026-03-17)
- 🔄 **Active work:** Session 0 scenarios (3/6 core done; expanded 4 have design framework only), STORY_ARC_SYNTHESIS.md needs update to reflect locked decisions, individual entity files to be created from indexes
- ✅ **Resolved (2026-04-05):** liberation_aftermath.md rewrite — v2.0 complete; Warren disturbance framing + 1,000-year timeline. [#106](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/106)
- ✅ **Completed (2026-04-11):** lat.md/ AI navigation layer — 6 dense, path-forward orientation files + CLAUDE.md Quick Navigation table. [#121](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/121)
- ✅ **Completed (2026-04-11):** CLAUDE.md audit + subagent context block — created lat.md/subagent-context.md; CLAUDE.md slimmed 258→174 lines; stale Wizard constraint corrected. [#128](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/128)
- ✅ **Completed (2026-04-22):** DASHBOARD.md schema + generator refactor — health panel separated from TODO.md; six regex extractors replaced with YAML readers; SECTION_DOMAIN_HEADERS expanded. [#166](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/166)
- 🆕 **Filed (2026-04-14):** Faction file stubs — 16 P1–P3 faction files to create from _category.md registry; 3 deferred pending #42, #43, Decision #11. [#144](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/144)
- 🗒️ **Backlog:** HTML generation pipeline refactor — consolidate shared utilities, eliminate _Generator boilerplate + CSS token drift across 6 scripts. [#138](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/138)
- 🗒️ **Backlog:** docs/ output hierarchy restructure — move per-document HTML into subdirectories; fixes ~500-file flat directory. [#168](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/168)
- ✅ **Completed (2026-05-01):** Faction stubs — 16 P1–P3 files created; 3 deferred pending #42, #43, Decision #11. [#144](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/144)
- ✅ **Completed (2026-05-01):** Phase 2d Jinja2 — dashboard generator migrated; `page-dashboard.css` + `pages/dashboard.html` created; `render_html()` f-string removed. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183)
- ✅ **Completed (2026-05-01):** Phase 3 Jinja2 — dark/light theme layer; `--bg`/`--fg`/`--surface` semantic vars in `tokens.css`; page CSS files use semantic vars; `[data-theme]` + `@media dark` overrides; floating `◑` toggle button on all pages. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183) (PR #195)
- ✅ **Completed (2026-05-01):** Phase 2c Jinja2 — world generators migrated; `base.html` extended with extra_head/page_gm_banner/back_nav/cover blocks; `pages/world.html` + `pages/world-timeline.html` created; `_html_wrapper()` removed. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183)
- ✅ **Completed (2026-05-01):** Phase 2b Jinja2 — campaign frame generator migrated; `base.html` extended with cover_extra + conditional base.css hooks. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183) (PR #189)
- ✅ **Completed (2026-04-30):** CSS extraction + Jinja2 template layer Phase 0–2a — tokens.css + linked CSS files (PR #187); renderer.py + base/ancestry/lore templates; ancestry + lore generators are now pure data-extraction. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183)
- ✅ **Completed (2026-04-22):** Account-based GM gatekeeping — `build.py all --gm`, Netlify Identity auth guard, three-tier markdown gating (Tier 1/2/3), `docs/login.html`, `GM_AUTHORING.md`. Remaining: manual Netlify second-site setup. [#176](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/176)
- 🗒️ **Backlog:** Nianhao D3 timeline phase 2 — content import, GM-tunable influence scores, cross-view interaction, mobile optimization. [#116](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/116)
- 🗒️ **Backlog:** Dashboard completion % from GitHub Issues — tie domain percentages to issue open/closed state. [#40](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/40)
- 🗒️ **Backlog:** Template frontmatter reconciliation — align templates/world-building/ files with CLAUDE.md spec
- 🗃️ **Charm system deferred (2026-03-13):** Archived to archive/charms/; Daggerheart base used for now
