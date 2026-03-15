---
title: Kanka Sync — TODO Archive
project: TTRPG_Tarim_Shaiel
type: archived_todo
status: deferred
archived: 2026-03-10
note: Kanka sync work is paused indefinitely. Phase 1 is complete and the code is sound. Phases 2–5 are well-specified and can be picked up at any time. See /archive/kanka/ for all implementation docs.
---

# Kanka Sync — Archived TODO

> **Status:** Deferred — work paused, not abandoned. Phase 1 complete and verified.
> **Archived:** 2026-03-10
> **Reason:** Active development focus shifted away from Kanka integration. All code, plans, and references preserved here for future resumption.

---

## INCOMPLETE (Paused — Phases 2–5)

### Kanka Sync Implementation ⚡ 75% COMPLETE
**Estimated Time Remaining:** ~75-110 minutes (Phases 2-4)

**Remaining Work:**
- [ ] **Phase 2: Wire up to sync flow** (~35 min)
  - Update `should_sync_file()` to accept `tag_filter` parameter
  - Add hash check logic to `sync_file()` to skip unchanged files
  - Call `update_frontmatter_post_sync()` after successful sync
  - Update `sync_all()` to accept `tag_filter`, `limit`, and `force` parameters

- [ ] **Phase 3: CLI Parameters** (~13 min)
  - Add `--tag`, `--limit`, `--force` arguments to argparse
  - Wire up new arguments to `sync_all()` calls in `main()`

- [ ] **Phase 4: Bulk Prepare Script** (~3 min)
  - Add `kanka_hash: null` and `tags: [needs-sync]` to bulk prepare script

- [ ] **Phase 5: Testing** (~30 min)
  - Test tag filtering, hash detection, batch limiting, force override
  - Verify backward compatibility

**References (all in `/archive/kanka/`):**
- `kanka-sync/` — Script directory (kanka-sync.py)
- `IMPLEMENTATION_CHECKLIST.md` — Detailed phase-by-phase breakdown
- `PHASE_1_COMPLETION_SUMMARY.md` — What was done in Phase 1
- `PHASE_2_IMPLEMENTATION_PLAN.md` — Detailed Phase 2 spec
- `PHASE_2_COMPLETE_DEPLOYMENT_GUIDE.md` — Full deployment instructions

### World Content Pending Kanka Import
- [ ] **Integrate weapons with kanka-sync** — Import `/mechanics/weapons_silk_road.md` weapon list
  - Tag structure for filtering
  - Cross-reference with NPC equipment
  - Blocked until Phase 2–5 complete

---

## COMPLETED

### Phase 1: Core Logic ✅ DONE

**Session:** 2025-01-27

- [x] Added `hashlib` import to kanka-sync.py
- [x] Implemented `compute_content_hash()` method (MD5)
- [x] Implemented `needs_update()` method (hash comparison)
- [x] Implemented `update_frontmatter_post_sync()` method (tag management)
- [x] Updated kanka-snippets.md with `kanka_hash` and `tags` fields
- [x] Created `IMPLEMENTATION_CHECKLIST.md` and `CODE_CHANGES_NEEDED.md`
- [x] Hash computation methods implemented
- [x] Tag management methods implemented
- [x] Documentation updated (kanka-snippets.md)
- [x] Implementation checklists created

---

## QUICK REFERENCE (Archived)

- **Sync Script:** `kanka-sync/kanka-sync.py` (in archive)
- **Implementation Checklist:** `IMPLEMENTATION_CHECKLIST.md`
- **Code Changes:** `CODE_CHANGES_NEEDED.md` — copy-paste ready code for Phases 2–5
- **Config:** `kanka-sync-config.yaml` / `kanka-sync-config.yaml.example`
- **Templates:** `kanka-templates/`
- **Logs:** `logs/`
