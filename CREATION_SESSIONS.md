---
title: Creation Session Log
project: TTRPG_Tarim_Shaiel
domain: utilities
doc_type: operational
visibility: internal
status: active
created: 2026-05-06
last_updated: 2026-11-03
---

# Creation Session Log

_Authoring and design work sessions. Newest first. Trim to last 10 sessions; older entries go to archive._
_Append new sessions here at session close. Do NOT append to TODO.md — that file is now archived._

---

### Session 2026-11-03 (Session chronicles)
- Session notes published to the site (#358, `HeroHeaven-gft`; #361): PR #360 (`c54827d`) generator, PR #362 (`ec252e6`) nav + homepage
  - `sessions` generator publishes `Session_N_Player_Summary.md` (fail-closed: filename + `visibility: public` + `status: canon`) to `docs/sessions/index.html` and flat `session-N.html` pages; Sessions 0-3 content committed (`a48665b`)
  - "Sessions" link after World in the header nav and mobile drawer; "Session Chronicles" card in the homepage Core Documents grid (`utilities/homepage/featured-docs.md`)
  - PDFs are local only (headless Chrome), not committed; `.gitignore` untouched
  - Open: `/newspaper/<issue>/index.html` has the same nested, vault-folder-named layout; flattening is a separate issue, not yet filed
  - 32 failing tests on `main` are pre-existing (#359, `HeroHeaven-x9f`)

### Session 2026-11-02 (Workshop shell)
- Map Workshop UX pass (#333, `HeroHeaven-fs8.1`): step 2 shipped as PR #348 (`b2036e0`), GH #347 / `HeroHeaven-fs8.1.1`
  - One width model (384px sidebar, 340px panel content, no per-panel caps), drag/arrow-key resize with double-click reset, hide/show with `\`, collapsible sections with persisted state
  - Review feedback folded in: Route Index is label + distance + travel + eye icon (open/held/closed), Layers and zoom stay on the map when the sidebar is hidden, Terrain explainer is an "i" popup
  - `tests/test_workshop_shell.py` added; Journeys in the Route Index deferred to the Routes consolidation (step 8)
  - Steps 3-10 remain open on #333; steps 5, 6 and 7 are the GM's calls and need a written case first

### Session 2026-11-02 (Workshop type scale)
- Map Workshop UX pass (#333, `HeroHeaven-fs8.1`): step 1 shipped as PR #346 (`b81da74`)
  - 5-token rem type scale and 4.5:1 text contrast in the Workshop sidebar; tabs now a 3-column grid (sidebar 464px to 383px)
  - `tests/test_workshop_type_scale.py` guards sizes and colours; decision logged in `.meta/DECISION_LOG.md`
  - Steps 2-10 remain open on #333 and `fs8.1`; step 2 (collapsible shell) is next, not yet claimed

### Session 2026-11-02
- Session 2 close-out and Session 3 documents brought in line with Session 3 having been played. No Beads or GitHub issue (GM: PR and commit notes suffice).
  - Gap fixes, `a32d39e`: Ariel, Sahir and Veyra got Session 2 Key Moments and resolved GM Notes; `characters/NPCs/Calberri Davis.md` (a tracked 0-byte file) is now a GM-only page for the Jade Illusionist avatar, linked from his Aliases list.
  - Session 3 treated as played, `524230d`: status callouts on `Session_3_Prep.md` and `Session_3_Encounter_Sheet.md` (they are pre-session docs, not direction for future work), Prep §12 items marked superseded by play, answered, or carried forward, and the "still carries this as TBD" line removed from `Session_2_GM_Record.md`. The GM wrote "Session 5"; read as Session 3 because the recording is `03_session3/Session_3.mp3`.
  - Deleted the untracked Session 2 `.html`/`.pdf` exports; kept the Session 3 Prep ones.
  - `.gitignore` rule `narrative/sessions/**/*.mp3` because `Session_3.mp3` is 139 MB (GitHub's limit is 100 MB). Scoped to `narrative/sessions` so the 21 tracked mp3s elsewhere are untouched. [PR #345](https://github.com/mofro/tarim-shaiel-campaign-frame/pull/345), awaiting the GM's merge.
- Next: merge #345. Open: the untracked 192 MB `Tarim-Shaiel: Session 3.m4a` (the mp3 rule does not cover it), no record yet of what Session 3 produced, and `characters/NPCs/Elder Road Merchant.md` is another 0-byte Jade Illusionist alias page

---

### Session 2026-10-30/11-01
- [HeroHeaven-fs8.4 / #336] Map: one Types table decides the pin. Closed 2026-11-01, GitHub and Beads together. Four PRs, all merged: #337 (Workshop Save sends only the fields the GM changed), #338 (one `TYPES` table feeds the parser, dropdowns, icons, tiers and toggles; PR 2 of 4), #339 (Types decide the pin, one zoom ladder, village and mythic-landscape; PR 3), #342 (`map_icon:` override, Type-only creation, `map.py retype`; PR 4)
  - Incident that started it, 2026-10-30: Workshop Save removed 11 `mapmarker:` and 6 `fantasy_name:` lines. The six `fantasy_name:` lines were restored in `f53d7a7`; #337 stops Save from writing fields the GM did not change
  - Content sort, 2026-10-31: 12 pages retyped (`ab8baa9`), 3 `map_marker: false` pages moved to `map_icon: none` (`7be1b1b`). 498 tests passed after PR 4
  - The GM declined every other change after seeing the sorted list (five of the 20 rows were public pages whose pin could differ). Left on purpose: the remaining `type:` / `mapmarker:` disagreements, the unlisted alias Types, pages with a blank Type, and `afrasiyan-plateau` (no `type:`, `mapmarker: ruin`). Working decision, not locked; any page can be retyped later in the Workshop or with `retype`
  - Process: decisions that turn on reasoned intent get a written case (intent, options with pros and cons, reversal cost, a suggestion), not a sheet to fill. Saved in project `CLAUDE.md` (`a714667`), global `~/.claude/CLAUDE.md` and `bdg remember`. Workshop live verification rules (block writes first, own tab only) are in project `CLAUDE.md` (`3ce37d9`, `36955f3`)
  - Recorded in DECISION_LOG and `lat.md/locations.md`: `11eb47f`, `cfaffc1`, `b41aa69`, `e3fdb9a`, `39425a1`
- [HeroHeaven-yuh / #343] Map: `utilities/geojson/generate_geojson.py` still styles the standalone snapshot from the legacy `mapmarker:` field; 25 of 207 pages lack it and new pages will too. Filed with checklist, open questions (does anything read the snapshot; where colour and symbol should come from) and reference files. Not started; touches `utilities/`, so it needs a review before closing
- Filed, not started: [HeroHeaven-v8l / #340] stale test fixes and `pytest.ini`; [HeroHeaven-mm8 / #341] build-version endpoint so pages stop reloading on every build
- Next: nothing is in flight. Open: #340, #341, #343, the GM's calls on the six #334 audit rows, #315 real-touch tap-to-open

---

### Session 2026-10-29
- [HeroHeaven-fs8.1 / #333] Map: Workshop UX pass filed as one umbrella issue (selection-driven Edit state, search by name / lat,lon / geocoder, one rebuild control, collapsible hideable resizable shell, routes consolidated, navigation that can grow, type scale). Spec-only; no code changed. Open questions are on the issue (geocoder, explicit tool modes, route edit popup, navigation shape, Reveal as batch action, rebuild automatic vs manual)
  - Findings verified in `generate_map_workshop.py`: pin-click meaning is multiplexed on `_activeTab`; `#panel-route-index` has no width cap; rebuild buttons exist only in Edit Coords while other flows rebuild automatically; 66 of 72 font-size declarations are 12px or smaller and 34 text colours are under 4.5:1
  - Type rule saved to `~/.claude/CLAUDE.md` ("Generated UI Type"): a 4-5 token scale, each step at least about 1.2x the last, floor 12px for uppercase or tracked labels and 13px for lowercase, secondary text drops size or weight before contrast, 4.5:1 minimum, rem units. A flat 14px minimum was rejected because it erases size-to-importance hierarchy
- [HeroHeaven-fs8.2 / #334, HeroHeaven-fs8.3 / #335] Map: coordinate audit scoped down. GM decision (working, not locked): decide only the six rows whose Wikidata analog is within 100 km (oyyaylak, mangnai, kagan, mazar-tag, baghlan, alak-mor); the other 21 rows and the Workshop Audit layer are deferred to #335 (P4). The 21 are left blank, not marked `intentional`
  - The latest report `audit-2026-10-26T183207` has 27 rows, not 30 (30 was the two earlier runs). Bands: 6 under 100 km, 5 at 100-1000 km, 14 over 1000 km, 2 DEM-only. Most far rows look like same-name collisions, so a blind `move` would teleport pins; `intentional` already means "pin right, analog wrong"
  - Not decided yet: the six `decision` values. The GM annotates a copy of the CSV, then `coord_audit.py --apply <file> --dry-run`
- Stale notes corrected: Topo baked-label handling resolved by #331/#332 (`lat.md/locations.md`), and the 2026-10-28 "Next" line below
- Next: GM decides the six rows on #334

---

### Session 2026-10-28
- [HeroHeaven-tic / #329] Map: player layer order matches the Workshop, layers panel tidied, type markers beside each toggle. PR #330 merged (squash `f56891e`); #329 and tic closed by hand, local branch deleted (head `5e3fbf7` == PR head; remote branch already gone)
  - Root cause: the player load handler added locations first, so routes and journeys drew over the pins. It now adds routes, journeys, locations (Workshop order). Panel is a borderless two-column grid of 44px rows with no vertical gap (bordered chips were tried and dropped as extra whitespace). `_dispIcons()` paints each type's registered map icon beside its label on both maps
  - Verified in Chrome: live layer order, 13 targets all 44px, no overflow at 591 px (the window would not go below it, so 375 px itself was not checked). The marker icons were checked by the user on both maps (Chrome disconnected before I could); 119 tests in `tests/test_display_layers.py`
  - Also this session: Karaulbazar caravanserai to city from the Workshop (`1fa2d43`, stale tag dropped `b8c5609`); map-pipeline Commit Paths row for route/waystation data is now `main directly` (`80619e3`, `09aeeec`). Open: that row's Prefix is still `infra:`
- [HeroHeaven-3kz / #323] Map: display layers for the player and Workshop maps. PR #328 merged (squash `e03fe47`); #323 closed by the merge (its "Closes" keyword), 3kz closed by hand, local branch deleted (head `fc86ddd` == PR head; the remote branch was already gone)
  - GM-owned Topo/Satellite overlays reach players only through the devserver relay (`POST`/`GET /api/map-overlays`; POST is localhost-only, validated whole, opacity clamped 0..1), gated per overlay by a "Share with players" box (default off). The player map polls every 2000 ms whether or not Follow GM is on and shows no error badge. Player-owned: Routes, Journeys and the 11 type toggles in `localStorage` `ts_player_display`, top-left, 44 px targets. The Workshop gains a Routes toggle and a Player's-eye preview; shared code is `map_style.display_controls_js`, with `_dispApply` the single `setFilter` owner
  - 116 tests in `tests/test_display_layers.py` (142 with `test_player_start_view.py`). Chrome-verified on the player map: relay on / clamp / 400 / off, toggle + persistence across reload, 375 px. The Workshop map could not be rendered (MapTiler 403 on ports 8010 and 8001, cause not established), so Workshop behaviour is node-harness only. Mutation spot-check was partial: 24 mutants, 22 killed, one real gap fixed, one equivalent; the full 70 was dropped as disproportionate
  - Behaviour changes: the shared filter excludes only toggled-off categories (the Workshop used to hide the 7 non-toggleable ones); Workshop storage key `_wsIt` → `_wsDisp`
  - Not decided at merge: the Topo raster bakes in real-world labels, borders and peaks from z8, so a shared Topo shows them under our markers (label-free raster / Topo Workshop-only / accept). Left unfixed: the Workshop overlay-error key mismatch (`_wstopo-overlayOn` written, `_wsTopoOn` read)
  - Real data: 0 of 35 routes are public, so the player Routes toggle has nothing to show yet
  - Process: added "Size verification to the change" to project `CLAUDE.md` Working Conventions after the mutation pass drew a correction
  - Pre-existing on main, not touched: the 5 `tests/test_shared_assets.py` failures and the `tests/test_lore_generator.py` ImportError
- Next (superseded 2026-10-29): the Topo baked-label handling was settled by #331/#332 (label-free custom style), and the Share boxes and Player's-eye preview have since had their browser pass

---

### Session 2026-10-27
- [HeroHeaven-lfj / #325] Map: peak markers on the Workshop only. PR #326 merged (squash `3d35295`); #325 and lfj closed together, branch deleted (local head `24e5699` == PR head)
  - Only `Peak labels` is wanted: Workshop "Peak markers" checkbox in the Layers menu (shown by default, `sessionStorage` key `_wsPeaks`), hidden on the player map with no control. The other five triangle layers (`Peak labels (US)` and the four volcano layers) are hidden on both maps
  - Done in code (`map_style.basemap_hide_js`), not in MapTiler Cloud, so the locations pages that share the style are unchanged. 7 tests in `tests/test_basemap_markers.py`; Chrome-verified on the Workshop and `/player`. No deployed copy to retest: both HTML files are gitignored local builds
  - Verified limit: the Workshop Topo overlay is raster with peak glyphs baked in at zoom 9+, so peaks still show with Peak markers off. Carried to #323 / HeroHeaven-3kz (on hold); decide before overlay sharing ships
  - Pre-existing on main, not touched: 5 failures in `tests/test_shared_assets.py` and an ImportError collecting `tests/test_lore_generator.py`
  - Assumed, not confirmed by the GM: the Workshop shows peaks by default; the locations pages are left alone
- [HeroHeaven-di4 / #324] Map: player map no longer opens at zoom 4 and then eases to the GM. PR #327 merged (squash `503a863`); #324 and di4 closed together, branch deleted (local head `5b41805` == PR head; the remote branch was already auto-deleted)
  - The map is built once, after the start view is chosen: GM position (`GET /api/map-center`, 800 ms timeout) → validated `localStorage` `ts_player_view` → the old 70/40 z4 default. `_lastCenter` is seeded from the GM start so the first poll does not re-ease. The view is written on a debounced `moveend` and on `pagehide` / `visibilitychange` (hidden), not `beforeunload`; all storage access is try/catch
  - 26 tests in `tests/test_player_start_view.py` (real emitted script run in node `vm`, plus devserver GET/POST); 16/16 hand-written mutants killed. Chrome-verified: before-state reproduced, GM start with no 4→7 step, stored view, `pagehide` write, blocked storage (throwing `localStorage` getter), phone width (375 px iframe)
  - Known gap, left alone (outside the spec): the Workshop POSTs its position only on `moveend`, so `/api/map-center` is null after a devserver restart until the GM first moves the map; a player refresh then uses the stored view. A one-time publish on Workshop load would close it
  - Pre-existing on main, not touched: same 5 `tests/test_shared_assets.py` failures and the `tests/test_lore_generator.py` ImportError
- Next: #323 / HeroHeaven-3kz was held until the GM said go, then shipped on 2026-10-28 (see Session 2026-10-28)

---

### Session 2026-10-26
- [HeroHeaven-5uw / #308] Map plan Phase A — shared map style, `poi` type, hover popups. Pipeline PR #313 merged (`f41679c`); #308 and 5uw closed together, branch deleted. Real-touch check split out as #315 / HeroHeaven-p5h
  - New `utilities/shared/map_style.py`: one definition of the route line, region layers, six location tiers and hover popups, used by the Workshop, the player map and `world.html` (routes + regions only)
  - Player popups use `popup_description(player_safe=True)` (fail-closed on session/awakening text); `gm_secrets` locations are dropped from the embedded player GeoJSON
  - `locations.categories.CATEGORIES` is now the only category list (Workshop Add Point + Edit Coords, `map.py`). Found and fixed: Edit Coords lacked 6 of 17 categories, so Save Fields silently re-typed those locations
  - Verified in Chrome: Add Point `poi` end to end (test file and regenerated GeoJSON removed), hover on Workshop and `/player`, route colour on all three surfaces, no console errors. Not verified: real touch tap-to-open
- Verification pass behind Phases A–E, recorded on #308/#309/#312: browser DEM decode matches PIL, Web Worker A* matches Node (851 km / 175 h), MapTiler Cloud Terms read in full (direct fetch §6.1, no server cache §7.2, client cache §5.7). Mounted and cart speed constants are still assumptions
- `shorchuk.md` frontmatter closed (`828768c`)
- `kashkar.md` merged into `kashgar.md` and deleted (`5ab5fd0`); faction `controls` slugs repointed; narrative-significance prose sits in a gm-only callout (hard constraint). GM answered the naming: canonical name and fantasy name are both Kashgar; `zzkashkar.md` is excluded by its `zz` prefix and left alone
- `jade-gate` set to `gm_secrets` (`743bdcc`, `revealed: 2026-05-13` kept); locations GeoJSON regenerated with `--gm` (`94f110f`), which also added `shorchuk`
- Coordinate audit specced in #314 / HeroHeaven-d95: per-item GM decision (move pin, fix elevation, mark intentional, skip), no global rule; AWS Terrain Tiles + Wikidata P625 instead of MapTiler for scripts. A throwaway DEM spike had sent browser-style Referer/Origin headers to MapTiler; it was discarded, never committed
- Beads "auto-export: git add failed": `~/.gitignore_global` ignores `.beads/issues.jsonl` while `export.git-add` was true. Set `export.git-add: false` in `.beads/config.yaml`; re-run of `bdg update` printed no warning
- `lat.md/locations.md`, `build-workflows.md`, `world.md`: documented the shared module and single category source; corrected stale references to the regions GeoJSON removed in #299
- Process feedback (GM): settled questions were asked again and the close-out was posed as a question. Saved to the `close-out-behavior-user-feedback-2026-10-25` bd memory and a `CLAUDE.md` working-convention bullet
- Map plan Phases B–F, built as a stacked PR chain (each on its own branch; merge in order and retarget the next to `main`)
  - B1: every location set to `gm_secrets` in one scripted pass (pushed, `00cf25b`); `revealed:` stays a datestamp that no code reads. B2 Reveal tab, PR #316 (#309 / HeroHeaven-u4v)
  - C: GM-only routes, route travel time and the route PATCH endpoint, PR #317 (#310 / HeroHeaven-15e)
  - D: per-leg travel state, persisted journeys, Travel Time tab, `/api/journeys`, PR #318 (#311 / HeroHeaven-6sm)
  - E: terrain-following paths for journey legs (DEM A* in a Web Worker), PR #319 (#312 / HeroHeaven-2py)
  - F: `utilities/locations/coord_audit.py` (#314 / HeroHeaven-d95). Report is a ranked Markdown + CSV list with a blank `decision` column; `--apply` writes only decided rows. First real run: 184 checked, 30 listed, 154 consistent. Endere ranked 17th behind generic-name Wikidata matches until rows were sorted by evidence tier (field contradicts terrain, then analog only). New location fields `coord_review`, `coord_reviewed`, `wikidata`; Pillow added to `requirements.txt`
  - Landed in order, each retargeted to `main` after the one below it was squash-merged: #316 (B2), #317 `b3c79fc`, #318 `5e10824`, #319 `ab2add2`, #320 `6e3b6f5`. After each squash the next PR conflicted (the branch still held the unsquashed history); fixed by merging `main` in with each file 3-way merged against the true common base, never a rebase. #308–#312 and #314 and their Beads issues closed with their merges; stack branches deleted
  - Open items: #315 / HeroHeaven-p5h (real-touch tap-to-open, needs a phone). Not built: a Workshop Audit layer for Phase F
- Frontmatter duplication (#321 / HeroHeaven-4um): saving an unchanged value from the Workshop appended another copy of the key (`title:`, `type:`, `visibility:` and the `location:` list). `_set_frontmatter_fields` and `_set_location` in `utilities/devserver.py` read "text unchanged after `re.sub`" as "key absent". Now `_replace_first` matches by count, replaces the first hit and drops later duplicates, so doubled pages heal on their next save. 13 tests in `tests/test_devserver_frontmatter.py`. Six damaged pages (`achatagh`, `aqyar`, `ember-wash`, `qarabulaq`, `qarachi`, `qizil`) had exact duplicate lines removed; devserver restarted to load the fix
  - The fix rode into `main` inside #320 (cherry-picked as `a508ccb` so the working checkout had it). #322 (same change on its own branch) was left with an empty diff against `main`; the GM merged it as is (`6d8e6a6`, no tree change) and #321 closed with it
  - Known and left alone: a Workshop rename updates `title:` only when both `title:` and `name:` exist, so it can leave `name:` stale

---

### Session 2026-10-25
- Map Workshop `ImportError: PyYAML is required` on Add Location — fixed and documented
  - Cause: `utilities/devserver.py` was launched with Homebrew `python`, which has no PyYAML; the rebuild endpoints spawn `build.py` with the server's own interpreter
  - Added a fail-fast PyYAML guard to the devserver (shipped in pipeline PR #306, `c1b1ae5`); CLAUDE.md and `lat.md/build-workflows.md` now say to run it from `venv/bin/python` (`7a33598`)
- Locations: kept `stashed-carts.md` and deleted the duplicate `stashed-carts-s3.md`; added `dire-wolf-pass.md` and `foothill-crossroads.md` route nodes; regenerated `tarim-shaiel-locations.geojson` (183 features) — `9ae212e`
- Reconciled the outstanding working tree into an ordered commit chain on main (plumbing commits, so the feature branch and working tree were never touched; nothing overwritten)
  - World Orc → Tulpar `3e1fac4`; narrative / characters / frame template `6518a40`; Session 2 record + Session 3 prep + Session 3 encounter sheet `ac80a3b`; DIVINE_PLAYERS `344ae98`; `lat.md/world.md` `fd24cac`
  - The Orc → Tulpar rename is a **partial pass**: word-level text only. Wikilink slugs and filenames (e.g. `orc-steppe-confederations`) are unchanged so no links break
- Pipeline PR #306 squash-merged to main (`c1b1ae5`): map workshop search, travel time, player share map, devserver PyYAML guard; `*.qta` added to `.gitignore`
- Beads: closed HeroHeaven-hya (Session 3 encounter sheet). The automatic `bd repo sync` left it in progress in beads-global (high-water-mark gotcha), so it was closed there directly and pushed to DoltHub; `bdg sync-down` found nothing to reconcile across the 14 registered projects
- PR #305 (2026-10-20 session close and EXTERNAL_TOOLS stale-ID fixes; its LK `isHidden` change was already on main) conflicted on this log with the chore commit `3112426`. Merged `origin/main` into its branch (`cfc9397`), kept both entries in order and trimmed to 10 (the `2026-05-10 (2)` entry went to the local archive), then squash-merged to main (`16d37e5`)
- Pipeline PR #307 squash-merged (`d60163e`): the four workshop hint strings in `generate_map_workshop.py` (Add Location, Add Route and Edit Location panels, plus the "Devserver not running" banner) now say `venv/bin/python utilities/devserver.py`
- Saved two zsh gotchas to the global CLAUDE.md and `bd remember`: never name a shell variable `path` (zsh ties it to `PATH`), and brace a variable before a colon (`${VAR}:refs/...`)
- Deliberately left alone: `5208caa` (`.gitignore` +8 and the Session 0 awakening file) remains only on `feature/workshop-search-nav`; not pursued
