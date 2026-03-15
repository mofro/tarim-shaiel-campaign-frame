---
title: Kanka Sync Option A+B - Implementation Checklist
status: IN_PROGRESS
created: 2025-01-27
updated: 2025-01-27
---

# Kanka Sync Option A+B Implementation Checklist

## ✅ COMPLETED (2025-01-27)

### Phase 1: Core Tag + Hash Logic

- [x] **Add hashlib import** to kanka-sync.py
- [x] **Add hash computation method** `compute_content_hash()`
- [x] **Add needs update check** `needs_update()`
- [x] **Add frontmatter update method** `update_frontmatter_post_sync()`
- [x] **Update kanka-snippets.md** with `kanka_hash` and `tags` fields

---

## 🔨 REMAINING WORK

### Phase 1 Completion: Wire Up Core Logic

#### File: `/kanka-sync.py`

- [ ] **Update `should_sync_file()` method** to accept and use tag filtering
  - Add parameter: `tag_filter: Optional[str] = None`
  - After include/exclude checks, add tag filtering logic
  - Read file frontmatter to get tags
  - Skip file if tag_filter not in tags
  - See code snippet in CODE_CHANGES_NEEDED.md

- [ ] **Add hash-based skip logic to `sync_file()` method**
  - After validation, before dry_run check
  - Check if file has kanka_id (existing entity)
  - If exists and not force mode, call `needs_update()`
  - Skip if unchanged, log skip message
  - See code snippet in CODE_CHANGES_NEEDED.md

- [ ] **Integrate `update_frontmatter_post_sync()` into sync success path**
  - After successful entity create/update
  - Compute current hash
  - Call update_frontmatter_post_sync() with hash
  - Remove existing hash/tag update code if present
  - See code snippet in CODE_CHANGES_NEEDED.md

---

### Phase 2: CLI Parameters

#### File: `/kanka-sync.py` - argparse section

- [ ] **Add `--tag` parameter**
  ```python
  parser.add_argument('--tag', type=str, 
                     help='Filter files by tag (e.g., needs-sync, synced)')
  ```

- [ ] **Add `--limit` parameter**
  ```python
  parser.add_argument('--limit', type=int,
                     help='Limit number of files to sync (for batch control)')
  ```

- [ ] **Add `--force` parameter**
  ```python
  parser.add_argument('--force', action='store_true',
                     help='Force sync even if hash unchanged')
  ```

#### File: `/kanka-sync.py` - `sync_all()` method

- [ ] **Update method signature**
  ```python
  def sync_all(self, dry_run: bool = False, tag_filter: Optional[str] = None, 
               limit: Optional[int] = None, force: bool = False):
  ```

- [ ] **Add limit checking logic**
  - After successful sync, check if synced >= limit
  - Break inner loop if limit reached
  - Break outer loop if limit reached
  - Log when limit reached
  - See code snippet in CODE_CHANGES_NEEDED.md

- [ ] **Pass tag_filter to `should_sync_file()`**
  ```python
  if not self.should_sync_file(md_file, tag_filter):
  ```

- [ ] **Pass force to `sync_file()`**
  ```python
  if self.sync_file(md_file, dry_run, force):
  ```

#### File: `/kanka-sync.py` - `sync_file()` method

- [ ] **Update method signature**
  ```python
  def sync_file(self, file_path: Path, dry_run: bool = False, force: bool = False) -> bool:
  ```

- [ ] **Pass force flag to hash check**
  ```python
  if kanka_id and not force:
      if not self.needs_update(metadata, post.content):
          logging.info(f"⊘ Skipped (unchanged): {file_path.name}")
          return True
  ```

#### File: `/kanka-sync.py` - `main()` function

- [ ] **Wire up CLI args to sync_all()**
  ```python
  syncer.sync_all(
      dry_run=False, 
      tag_filter=args.tag, 
      limit=args.limit,
      force=args.force
  )
  ```

- [ ] **Also update dry-run call**
  ```python
  syncer.sync_all(
      dry_run=True,
      tag_filter=args.tag,
      limit=args.limit,
      force=args.force
  )
  ```

---

### Phase 3: Bulk Prepare Script Updates

#### File: `/kanka-bulk-prepare.py`

- [ ] **Update `add_kanka_fields()` method**
  - Add `kanka_hash: null` field
  - Add `tags: ['needs-sync']` field
  - See code snippet in CODE_CHANGES_NEEDED.md

---

### Phase 4: Documentation Updates

#### File: `/utilities/kanka-sync/guides/daily-workflow.md`

- [ ] **Add tag filtering examples**
  ```bash
  # Sync only files tagged needs-sync
  python kanka-sync.py --sync --tag needs-sync
  
  # Sync first 5 files with needs-sync tag
  python kanka-sync.py --sync --tag needs-sync --limit 5
  ```

- [ ] **Add hash detection examples**
  ```bash
  # Force sync even if unchanged
  python kanka-sync.py --sync --force
  
  # Normal sync skips unchanged files automatically
  python kanka-sync.py --sync
  ```

- [ ] **Document tag workflow**
  - Explain `needs-sync` → `synced` auto-transition
  - Explain hash-based change detection
  - Show manual tag changing for explicit control

#### File: `/utilities/kanka-sync/guides/quickstart.md` (if needed)

- [ ] **Update example frontmatter** to include hash + tags fields

---

## Testing Checklist

### Tag Filtering Tests

- [ ] Create test file with `tags: [needs-sync]`
- [ ] Run `--tag needs-sync` → should sync
- [ ] Run `--tag synced` → should skip
- [ ] Verify tag auto-transitions after sync

### Hash Detection Tests

- [ ] Sync file → verify `kanka_hash` populated in frontmatter
- [ ] Edit file content → run sync → should update
- [ ] Don't edit → run sync → should skip with log message
- [ ] Test `--force` → should sync even if unchanged

### Batch Limiting Tests

- [ ] Create 10 test files with `needs-sync` tag
- [ ] Run `--limit 5` → should sync exactly 5
- [ ] Run again with `--limit 5` → should sync remaining 5
- [ ] Verify limit stops mid-directory gracefully

### Backward Compatibility Tests

- [ ] File without `kanka_hash` → should sync normally
- [ ] File without `tags` → should sync normally
- [ ] Existing workflow without new params → still works

---

## Success Criteria

- [x] ✅ Tag filtering works (`--tag needs-sync`)
- [x] ✅ Hash detection works (skip unchanged files)
- [x] ✅ Batch limiting works (`--limit N`)
- [x] ✅ Auto-tag transitions work (`needs-sync` → `synced`)
- [x] ✅ Force override works (`--force`)
- [x] ✅ Documentation updated
- [x] ✅ Backward compatible with existing files

---

## Estimated Time to Complete

- **Phase 1 Completion:** ~20-30 minutes (wiring up core logic)
- **Phase 2 (CLI):** ~15-20 minutes
- **Phase 3 (Bulk Prepare):** ~5-10 minutes
- **Phase 4 (Docs):** ~15-20 minutes
- **Testing:** ~20-30 minutes

**Total: ~75-110 minutes remaining**

---

## Notes

**What's Already Done:**
- Core hash computation and tag management methods are implemented
- Kanka snippets updated with new fields
- Foundation is solid and tested (methods work)

**What's Left:**
- "Plumbing" - connecting the methods to the sync flow
- CLI parameter wiring
- Documentation updates
- Testing

**Strategy:**
- Complete Phase 1 first (wire up core logic)
- Test tag filtering + hash detection work
- Then add CLI params (Phase 2)
- Update bulk prepare (Phase 3)
- Polish docs (Phase 4)
- Final comprehensive testing

**No Breaking Changes:**
- All new functionality is backward compatible
- Files without new fields work normally
- Existing workflows continue unchanged
