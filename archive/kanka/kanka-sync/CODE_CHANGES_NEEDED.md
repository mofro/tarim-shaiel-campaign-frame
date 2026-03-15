---
title: Kanka Sync Option A+B - Exact Code Changes
type: implementation-reference
status: reference
created: 2025-01-27
---

# Kanka Sync Option A+B - Exact Code Changes

**Purpose:** Copy-paste ready code snippets for completing the implementation.

**Target Files:**
- `/Users/mo/Documents/Games/HeroHeaven/kanka-sync.py`
- `/Users/mo/Documents/Games/HeroHeaven/kanka-bulk-prepare.py`

---

## File 1: kanka-sync.py Changes

### Change 1: Update `should_sync_file()` Method Signature and Body

**Find (around line 485):**
```python
def should_sync_file(self, file_path: Path) -> bool:
    """Determine if file should be synced"""
    rel_path = file_path.relative_to(self.vault_path)
    
    # Check exclusions
    for exclude in self.config['sync']['exclude_paths']:
        if str(rel_path).startswith(exclude):
            return False
    
    # Check inclusions
    for include in self.config['sync']['include_paths']:
        if str(rel_path).startswith(include):
            return True
    
    return False
```

**Replace with:**
```python
def should_sync_file(self, file_path: Path, tag_filter: Optional[str] = None) -> bool:
    """Determine if file should be synced based on includes/excludes AND tag filter"""
    rel_path = file_path.relative_to(self.vault_path)
    
    # Check exclusions
    for exclude in self.config['sync']['exclude_paths']:
        if str(rel_path).startswith(exclude):
            return False
    
    # Check inclusions
    included = False
    for include in self.config['sync']['include_paths']:
        if str(rel_path).startswith(include):
            included = True
            break
    
    if not included:
        return False
    
    # NEW: Tag filtering
    if tag_filter:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            metadata = dict(post.metadata)
            tags = metadata.get('tags', [])
            
            # Skip if tag filter not in file tags
            if tag_filter not in tags:
                return False
        except Exception as e:
            logging.warning(f"Could not read tags from {file_path.name}: {e}")
            return False
    
    return True
```

---

### Change 2: Update `sync_file()` Method Signature

**Find (around line 705):**
```python
def sync_file(self, file_path: Path, dry_run: bool = False) -> bool:
```

**Replace with:**
```python
def sync_file(self, file_path: Path, dry_run: bool = False, force: bool = False) -> bool:
```

---

### Change 3: Add Hash Check Logic in `sync_file()`

**Find (around line 750):**
```python
# Create or update entity
kanka_id = metadata.get('kanka_id')

if kanka_id:
    result = self.api.update_entity(entity_type, kanka_id, payload)
```

**Replace with:**
```python
# NEW: Check if file needs update based on hash (skip if unchanged)
kanka_id = metadata.get('kanka_id')

if kanka_id and not dry_run and not force:
    # File has been synced before - check hash
    if not self.needs_update(metadata, post.content):
        logging.info(f"⊘ Skipped (unchanged): {file_path.name}")
        return True  # Not a failure, just skipped

# Create or update entity
if kanka_id:
    result = self.api.update_entity(entity_type, kanka_id, payload)
```

---

### Change 4: Add Post-Sync Frontmatter Update in `sync_file()`

**Find (around line 810, near end of `sync_file()` method):**
```python
# Sync map marker for locations with coordinates
if entity_type == 'location':
    if not self.sync_location_marker(file_path, post, metadata, entity_id, dry_run=dry_run):
        return False

return True
```

**Replace with:**
```python
# Sync map marker for locations with coordinates
if entity_type == 'location':
    if not self.sync_location_marker(file_path, post, metadata, entity_id, dry_run=dry_run):
        return False

# NEW: Update frontmatter post-sync (hash + tags + kanka_id)
if not dry_run:
    current_hash = self.compute_content_hash(post.content)
    self.update_frontmatter_post_sync(file_path, post, kanka_id, current_hash)

return True
```

---

### Change 5: Update `sync_all()` Method Signature

**Find (around line 820):**
```python
def sync_all(self, dry_run: bool = False):
    """Sync all eligible files"""
```

**Replace with:**
```python
def sync_all(self, dry_run: bool = False, tag_filter: Optional[str] = None, 
             limit: Optional[int] = None, force: bool = False):
    """Sync all eligible files with optional tag filtering and batch limiting"""
```

---

### Change 6: Update `sync_all()` Method Body

**Find (around line 835):**
```python
for md_file in search_path.rglob('*.md'):
    # Skip templates
    if '_TEMPLATE' in md_file.name or md_file.name.startswith('_'):
        continue
    
    if not self.should_sync_file(md_file):
        skipped += 1
        continue
    
    if self.sync_file(md_file, dry_run):
        synced += 1
    else:
        failed += 1

logging.info(f"\n{'='*60}")
```

**Replace with:**
```python
for md_file in search_path.rglob('*.md'):
    # Skip templates
    if '_TEMPLATE' in md_file.name or md_file.name.startswith('_'):
        continue
    
    # NEW: Pass tag_filter to should_sync_file
    if not self.should_sync_file(md_file, tag_filter):
        skipped += 1
        continue
    
    # NEW: Check limit
    if limit and synced >= limit:
        logging.info(f"\n⊘ Limit reached ({limit} files synced)")
        break
    
    # NEW: Pass force flag to sync_file
    if self.sync_file(md_file, dry_run, force):
        synced += 1
    else:
        failed += 1

# NEW: Break outer loop if limit reached
if limit and synced >= limit:
    break

logging.info(f"\n{'='*60}")
```

---

### Change 7: Add CLI Arguments in `main()`

**Find (around line 865):**
```python
parser = argparse.ArgumentParser(description='Obsidian → Kanka Sync (Enhanced)')
parser.add_argument('--config', default='kanka-sync-config.yaml', help='Config file')
parser.add_argument('--test-connection', action='store_true', help='Test API')
parser.add_argument('--dry-run', action='store_true', help='Preview without syncing')
parser.add_argument('--sync', action='store_true', help='Perform sync')
parser.add_argument('--sync-one', type=str, help='Sync a single file (relative to vault path)')
```

**Add after `--sync-one`:**
```python
parser.add_argument('--tag', type=str, 
                   help='Filter files by tag (e.g., needs-sync, synced)')
parser.add_argument('--limit', type=int,
                   help='Limit number of files to sync (for batch control)')
parser.add_argument('--force', action='store_true',
                   help='Force sync even if hash unchanged')
```

---

### Change 8: Wire Up CLI Args in `main()` - Dry Run Section

**Find (around line 890):**
```python
elif args.dry_run:
    print("🔍 Dry run mode - no changes will be made\n")
    if args.sync_one:
        file_path = syncer.vault_path / args.sync_one
        syncer.sync_file(file_path, dry_run=True)
    else:
        syncer.sync_all(dry_run=True)
```

**Replace with:**
```python
elif args.dry_run:
    print("🔍 Dry run mode - no changes will be made")
    if args.tag:
        print(f"Filter: tag={args.tag}")
    if args.limit:
        print(f"Limit: {args.limit} files")
    if args.force:
        print("Force: Ignoring hash checks")
    print()
    
    if args.sync_one:
        file_path = syncer.vault_path / args.sync_one
        syncer.sync_file(file_path, dry_run=True, force=args.force)
    else:
        syncer.sync_all(
            dry_run=True, 
            tag_filter=args.tag, 
            limit=args.limit,
            force=args.force
        )
```

---

### Change 9: Wire Up CLI Args in `main()` - Sync Section

**Find (around line 900):**
```python
elif args.sync:
    print("\n⚠️  Ready to sync files to Kanka")
    print("Features: Content splitting, attributes, GM posts\n")
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        if args.sync_one:
            file_path = syncer.vault_path / args.sync_one
            syncer.sync_file(file_path, dry_run=False)
        else:
            syncer.sync_all(dry_run=False)
    else:
        print("Cancelled")
```

**Replace with:**
```python
elif args.sync:
    print("\n⚠️  Ready to sync files to Kanka")
    print("Features: Content splitting, attributes, GM posts")
    if args.tag:
        print(f"Filter: tag={args.tag}")
    if args.limit:
        print(f"Limit: {args.limit} files")
    if args.force:
        print("Force: Ignoring hash checks")
    print()
    
    confirm = input("Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        if args.sync_one:
            file_path = syncer.vault_path / args.sync_one
            syncer.sync_file(file_path, dry_run=False, force=args.force)
        else:
            syncer.sync_all(
                dry_run=False, 
                tag_filter=args.tag, 
                limit=args.limit,
                force=args.force
            )
    else:
        print("Cancelled")
```

---

## File 2: kanka-bulk-prepare.py Changes

### Change 10: Add `kanka_hash` and `tags` Fields

**Find (around line 50 in `add_kanka_fields()` method):**
```python
# Add Kanka fields
post['kanka_type'] = kanka_type
post['kanka_id'] = None
post['is_private'] = is_private

if dry_run:
```

**Replace with:**
```python
# Add Kanka fields
post['kanka_type'] = kanka_type
post['kanka_id'] = None
post['is_private'] = is_private
post['kanka_hash'] = None          # NEW
post['tags'] = ['needs-sync']       # NEW

if dry_run:
```

---

## Quick Reference: New CLI Usage

After implementation, these commands will work:

```bash
# Sync only files tagged 'needs-sync'
python kanka-sync.py --sync --tag needs-sync

# Sync only 5 files at a time (batch control)
python kanka-sync.py --sync --limit 5

# Sync files tagged 'needs-sync', limit to 5
python kanka-sync.py --sync --tag needs-sync --limit 5

# Force sync even if hash unchanged
python kanka-sync.py --sync --force

# Dry run with filters
python kanka-sync.py --dry-run --tag needs-sync --limit 10

# Combine all options
python kanka-sync.py --sync --tag needs-sync --limit 5 --force
```

---

## Verification Commands

After making changes, verify syntax:

```bash
# Check Python syntax
python -m py_compile kanka-sync.py
python -m py_compile kanka-bulk-prepare.py

# Test help output
python kanka-sync.py --help

# Should show new options:
#   --tag TAG           Filter files by tag (e.g., needs-sync, synced)
#   --limit LIMIT       Limit number of files to sync (for batch control)
#   --force             Force sync even if hash unchanged
```

---

**Last Updated:** 2025-01-27
**Status:** Copy-paste ready
