---
title: Project Dashboard
project: TTRPG_Tarim_Shaiel
type: operational
visibility: internal
status: active
last_updated: 2026-07-15

critical_path:
  - Resolve cosmological architecture
  - Complete Session 0 scenarios
  - Resolve Campaign Frame
  - Playtest

players:
  committed: 4
  total: 10
  archetypes:
    - {name: Warrior,    status: committed,  player: "Lisa",  character: "Human / Warrior class"}
    - {name: Sentinel,   status: committed,  player: "Arno",  character: "Pari-Kin / Druid class"}
    - {name: Seeker,     status: committed,  player: "Erik",  character: "Tadbir / Sorcerer"}
    - {name: Visionary,  status: committed,  player: "Marc",  character: "Human / Seraph class"}
    - {name: Breaker,    status: pending,    player: ""}
    - {name: Bridge,     status: pending,    player: ""}
    - {name: Sacrificer, status: pending,    player: ""}
    - {name: Trickster,  status: pending,    player: ""}
    - {name: Crafter,    status: pending,    player: ""}
    - {name: Healer,     status: pending,    player: ""}
    - {name: Keeper,     status: pending,    player: ""}
  deciding_players:
    - {player: "Dave",  class_pref: "Warlock",  archetype: "undecided"}
    - {player: "Bruce", class_pref: "Guardian", archetype: "undecided"}

domain_overrides:
  # Manually pinned at 2026-05-06 when task tracking migrated from TODO.md to Beads.
  # Update these when significant bodies of work complete — bd issue close rate drives
  # incremental progress; major milestones (scenario complete, section shipped) warrant
  # bumping the value manually.
  narrative: 50
  mechanics: 95
  world: 97
  infra: 96
  cosmology: 71

blockers:
  # - "⛔ Description of active blocker"
---

## Quick Summary

- 🔄 **In review (2026-07-04):** LK Bridge — vault↔LegendKeeper converter (`utilities/lk-bridge/`), validator, 24 tests; all four round-trip questions verified live (secrets survive, hidden pages preserved, additive sync works). [PR #273](https://github.com/mofro/tarim-shaiel-campaign-frame/pull/273); HeroHeaven-x1i stays open pending LK API. Pre-existing bugs filed: HeroHeaven-zqo (tests broken on main), HeroHeaven-bl5 (geojson build).
- [x] **Core complete:** Campaign narrative, world geography, fantasy naming, charm architecture, Orc cultural framework, Silk Road weapons, Cosmological architecture (all 8 decisions locked 2026-03-17), World entity infrastructure (factions/events/concepts indexes + all location templates 2026-03-10), Preliminary world diagrams (2026-03-13), HTML publishing pipeline + Netlify deployment (2026-03-15), Visibility gating + Obsidian Shell Commands integration (2026-03-17)
- 🔄 **Active work:** Session 0 scenarios (3/11 complete: Warrior, Seeker, Breaker; 7 have design framework only; Keeper surrendered layer pending Decision 15), STORY_ARC_SYNTHESIS.md needs update to reflect locked decisions, individual entity files to be created from indexes
- ✅ **Resolved (2026-04-05):** liberation_aftermath.md rewrite — v2.0 complete; Warren disturbance framing + 1,000-year timeline. [#106](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/106)
- ✅ **Completed (2026-04-11):** lat.md/ AI navigation layer — 6 dense, path-forward orientation files + CLAUDE.md Quick Navigation table. [#121](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/121)
- ✅ **Completed (2026-04-11):** CLAUDE.md audit + subagent context block — created lat.md/subagent-context.md; CLAUDE.md slimmed 258→174 lines; stale Wizard constraint corrected. [#128](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/128)
- ✅ **Completed (2026-04-22):** DASHBOARD.md schema + generator refactor — health panel separated from TODO.md; six regex extractors replaced with YAML readers; SECTION_DOMAIN_HEADERS expanded. [#166](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/166)
- 🆕 **Filed (2026-04-14):** Faction file stubs — 16 P1–P3 faction files to create from _category.md registry; 3 deferred pending #42, #43, Decision #11. [#144](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/144)
- ✅ **Closed (2026-05-01, superseded):** HTML generation pipeline refactor — subsumed by #183 Jinja2 migration; CSS unified, generators migrated; Stage 5 deferred to #198. [#138](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/138)
- ✅ **Completed (2026-04-21):** docs/ output hierarchy restructure — per-document HTML moved into subdirectories; root-relative asset paths; ~500-file flat directory resolved. [#168](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/168)
- ✅ **Completed (2026-05-01):** Faction stubs — 16 P1–P3 files created; 3 deferred pending #42, #43, Decision #11. [#144](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/144)
- ✅ **Completed (2026-05-01):** Phase 2d Jinja2 — dashboard generator migrated; `page-dashboard.css` + `pages/dashboard.html` created; `render_html()` f-string removed. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183)
- ✅ **Completed (2026-05-01):** Phase 3 Jinja2 — dark/light theme layer; `--bg`/`--fg`/`--surface` semantic vars in `tokens.css`; page CSS files use semantic vars; `[data-theme]` + `@media dark` overrides; floating `◑` toggle button on all pages. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183) (PR #195)
- ✅ **Completed (2026-05-01):** Phase 2c Jinja2 — world generators migrated; `base.html` extended with extra_head/page_gm_banner/back_nav/cover blocks; `pages/world.html` + `pages/world-timeline.html` created; `_html_wrapper()` removed. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183)
- ✅ **Completed (2026-05-01):** Phase 2b Jinja2 — campaign frame generator migrated; `base.html` extended with cover_extra + conditional base.css hooks. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183) (PR #189)
- ✅ **Completed (2026-04-30):** CSS extraction + Jinja2 template layer Phase 0–2a — tokens.css + linked CSS files (PR #187); renderer.py + base/ancestry/lore templates; ancestry + lore generators are now pure data-extraction. [#183](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/183)
- ✅ **Completed (2026-04-22):** Account-based GM gatekeeping — `build.py all --gm`, Netlify Identity auth guard, three-tier markdown gating (Tier 1/2/3), `docs/login.html`, `GM_AUTHORING.md`. Remaining: manual Netlify second-site setup. [#176](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/176)
- 🗒️ **Backlog:** Dark mode visual review — contrast/readability audit; badge pastels, crimson headings, page-card/body separation, hardcoded rgba values across all page CSS. [#197](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/197)
- 🗒️ **Backlog:** `html_render.py` structured-dict refactor — return component dicts instead of HTML strings; Jinja2 macro renders prose; eliminates last ~140 lines of Python HTML assembly. [#198](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/198)
- 🗒️ **Backlog:** Nianhao D3 timeline phase 2 — content import, GM-tunable influence scores, cross-view interaction, mobile optimization. [#116](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/116)
- ✅ **Completed (2026-04-24):** Claude Code hooks — `SessionStart` rebase sync + `Stop` workflow_dispatch pipeline trigger; `.claude/settings.local.json` + `hooks/stop.sh` created locally. [#40](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/40)
- ✅ **Completed (2026-05-02):** Schema C vault migration — all 5 phases; Decision 17 locked; 300+ files migrated from type: to domain/doc_type/content_type; is_private: removed; classification: removed. [#77](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/77)
- ✅ **Completed (2026-05-27):** Daggerheart class primer — 13 classes (9 SRD + 4 playtest), per-class Tarim-Shaiel framing, images, pipeline; classes page public. [HeroHeaven-5cf](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/262)
- ✅ **Completed (2026-06-06):** Class survey — 4 responses collected: Lisa/Warrior ✓, Arno/Sentinel ✓, Erik deciding Seeker vs Breaker, Marc TBD, Bruce queued as new player. [HeroHeaven-uma]
- ✅ **Resolved (2026-07-15):** Player archetypes confirmed: Lisa/Warrior, Arno/Sentinel, Erik/Seeker, Marc/Visionary — 4 committed. Bruce/Breaker + Dave deciding. Scenarios: Warrior, Seeker, Sentinel, Visionary complete; Breaker mostly complete.
- 🗃️ **Charm system deferred (2026-03-13):** Archived to archive/charms/; Daggerheart base used for now
