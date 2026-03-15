---
title: Daily Workflow Guide
type: guide
category: kanka-sync
tags: [kanka, workflow, daily-use]
parent: "[[utilities/kanka-sync/INDEX|Kanka Sync Documentation]]"
---

# Daily Workflow Guide

**How to use Kanka Sync in your regular TTRPG prep workflow.**

---

## The Typical Workflow

### **1. Author Content in Obsidian (Normal Process)**

Write your locations, NPCs, plot hooks as usual:

```markdown
---
name: New Location
type: village
# Don't add kanka fields yet - just work normally
---

# New Location

A quiet farming village.

## Geography
Rolling hills and fertile plains.

## Hidden Secrets
The well is actually a portal.
```

**Key:** Don't worry about Kanka fields while authoring. Just write.

---

### **2. Mark Files Ready for Players**

When content is ready for players to see, add `kanka_type`:

```yaml
---
name: New Location
type: village
kanka_type: location  # ← Add this when ready
is_private: false     # ← Add this (or let it default)
---
```

**This signals:** "This file is ready to sync."

---

### **3. Sync When Convenient**

```bash
cd /Users/mo/Documents/Games/HeroHeaven
source venv/bin/activate

# Quick preview
python kanka-sync.py --dry-run

# Sync
python kanka-sync.py --sync
```

**How often?**
- Before each session (ensure players have access)
- After major writing sessions
- Whenever you've marked 3+ files as ready

**Time:** 2-5 minutes for typical updates (3-5 files)

---

## Common Scenarios

### **Scenario 1: New Location for Tonight's Session**

**Morning:**
```markdown
---
name: Forgotten Temple
type: dungeon
# No kanka fields - still drafting
---

## Geography
Ancient ruins deep in forest.

## DM Notes
This is where they'll find the artifact.
```

**Afternoon (ready for players):**
```yaml
---
name: Forgotten Temple
type: dungeon
kanka_type: location  # ← Added
is_private: false
---
```

**1 Hour Before Session:**
```bash
python kanka-sync.py --sync
```

**Result:** Players can now see the temple in Kanka. Your DM Notes are in a private post.

---

### **Scenario 2: Updating Existing Location**

**During Prep:**
```markdown
## Plot Hooks
~~Investigate the well.~~
The well portal has been revealed! Now they must decide whether to enter.
```

**Sync:**
```bash
python kanka-sync.py --sync
```

**Result:** 
- Main entry updated
- "Plot Hooks" post updated
- Players see the change (if Plot Hooks was public)
- OR GMs see the change (if Plot Hooks is a GM section)

---

### **Scenario 3: Progressive Secret Revelation**

**Setup (before session):**
File has:
```markdown
## Hidden Secrets
The blacksmith is actually the BBEG's spy.
```

Syncs to: GM post "Hidden Secrets" (admin-only)

**During Session:**
Players discover the secret through investigation.

**After Session:**
1. Open entity in Kanka
2. Go to Posts tab
3. Edit "Hidden Secrets" post
4. Change visibility: `admin` → `all`
5. Save

**Result:** Players can now see that specific secret in Kanka.

**Next Session Prep:**
```markdown
## Hidden Secrets
~~The blacksmith is actually the BBEG's spy.~~  [Revealed Session 3]

The blacksmith's letter of instruction is hidden in the forge.
```

Sync → Updates the post with new secret.

---

### **Scenario 4: Bulk Preparation for Arc**

**You've written 10 new locations for the next story arc.**

**Mark them all:**
```bash
python kanka-bulk-prepare.py --prepare "World/Locations/Arc2" --type location --private false
```

**Preview:**
```bash
python kanka-sync.py --dry-run
```

**Sync (be patient ~5-8 minutes):**
```bash
python kanka-sync.py --sync
```

**Result:** All 10 locations now in Kanka, organized and ready.

---

## Quick Decisions

### **Should I Sync This File?**

**YES, sync if:**
- ✅ Players will encounter it soon (next 1-2 sessions)
- ✅ Players have already encountered it
- ✅ It's reference material players need (maps, rules, archetypes)
- ✅ It's world lore you want players to explore

**NO, don't sync if:**
- ❌ Still drafting/incomplete
- ❌ Contains only GM planning notes
- ❌ Major spoilers for future arcs
- ❌ Mechanical notes not relevant to players

---

### **Public or Private?**

**Set `is_private: true` if:**
- Entire entity is spoiler/secret
- Players don't know it exists
- Pure GM reference

**Set `is_private: false` if:**
- Players can/should know about it
- It's discoverable in-world
- Reference material

**Use GM sections for:**
- Partial secrets within public entities
- DM notes about public content
- Plot hooks and narrative significance

---

## Time Estimates

### **Quick Sync (1-3 Files)**
- Dry run: 5 seconds
- Sync: 30-90 seconds
- **Total: ~2 minutes**

### **Medium Sync (5-10 Files)**
- Dry run: 10 seconds  
- Sync: 3-5 minutes (rate limiting kicks in)
- **Total: ~5 minutes**

### **Large Sync (20+ Files)**
- Dry run: 20 seconds
- Sync: 10-15 minutes (multiple rate limit pauses)
- **Total: ~15 minutes**

**Tip:** Do large syncs during non-urgent prep time.

---

## Best Practices

### **1. Sync Early, Sync Often**

Don't wait until you have 50 files ready. Sync in batches of 5-10.

**Why:**
- Faster feedback loops
- Easier to catch errors
- Less intimidating

---

### **2. Use Dry Run Liberally**

```bash
python kanka-sync.py --dry-run
```

**Shows you:**
- What will sync
- How many attributes per file
- How many GM posts per file
- Any validation warnings

**No API calls, instant results.**

---

### **3. Check Logs After Sync**

```bash
tail -20 kanka-sync.log
```

**Look for:**
- ✓ Success messages
- ⏱ Rate limit pauses (normal)
- ❌ Errors (investigate)

---

### **4. Keep a "Ready to Sync" Tag**

In Obsidian, use a tag system:

```yaml
tags: [ready-for-kanka]
```

**Then search:**
```
tag:#ready-for-kanka
```

**Shows:** All files marked but not yet synced.

**After sync:** Remove tag or change to `synced-to-kanka`.

---

### **5. Verify in Kanka After Big Syncs**

After syncing 10+ files:
1. Open Kanka
2. Spot-check 3-5 entities
3. Use "View As Player" to verify privacy
4. Check one GM post for proper visibility

**Peace of mind:** Confirm everything routed correctly.

---

## Integration with Session Prep

### **Weekly Prep Cycle**

**Monday (Worldbuilding):**
- Author new content in Obsidian
- Don't worry about Kanka fields

**Wednesday (Polish):**
- Review drafted content
- Add `kanka_type` to files ready for players
- Run dry-run to preview

**Friday (Prep Day):**
- Final sync before session
- Verify in Kanka
- Add any last-minute GM posts

**Saturday (Session Day):**
- Players access Kanka during game
- You update notes in Obsidian
- Sync after session if needed

**Sunday (Review):**
- Reflect on session
- Update files with what players discovered
- Sync changes

---

## Keyboard Shortcuts (Optional)

**If using Obsidian Templater or QuickAdd:**

Create a template to add Kanka fields:

```markdown
<%*
const currentFile = tp.file.content;
const frontmatter = app.metadataCache.getFileCache(tp.file.find_tfile(tp.file.path())).frontmatter;

// Add kanka fields if missing
if (!frontmatter.kanka_type) {
  await app.fileManager.processFrontMatter(tp.file.find_tfile(tp.file.path()), fm => {
    fm.kanka_type = await tp.system.suggester(
      ["location", "character", "note", "quest"],
      ["location", "character", "note", "quest"]
    );
    fm.is_private = false;
    fm.kanka_id = null;
  });
}
%>
```

**Hotkey:** Ctrl+K → Adds Kanka fields to current file

---

## Troubleshooting During Daily Use

### **"File Not Syncing"**

**Check:**
1. Does file have `kanka_type`?
2. Is file in `include_paths` (config)?
3. Is file excluded by `exclude_paths`?

### **"Content in Wrong Place"**

**Check:**
- Section headers match exactly (case-sensitive)
- Review [[../reference/routing-rules|Routing Rules]]

### **"Sync Taking Forever"**

**Normal if:**
- Syncing 10+ files (rate limiting)
- See "⏱ Rate limit" messages in log

**Problem if:**
- No progress for 5+ minutes
- Errors in log
- Network issues

---

## Command Quick Reference

```bash
# Activate environment
source venv/bin/activate

# Preview what will sync
python kanka-sync.py --dry-run

# Sync files
python kanka-sync.py --sync

# Bulk prepare directory
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false

# Check logs
tail -f kanka-sync.log

# Test connection
python kanka-sync.py --test-connection
```

---

## Related Documentation

- [[quickstart|Quickstart Guide]] - Initial setup
- [[../reference/routing-rules|Routing Rules]] - How content splits
- [[../reference/field-mappings|Field Mappings]] - Frontmatter reference
- [[../INDEX|Documentation Index]] - All docs

---

[[INDEX|← Back to Documentation Index]]
