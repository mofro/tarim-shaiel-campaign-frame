# Kanka Sync v2.0 - Testing Checklist

## Pre-Flight Checks

### **1. Verify Enhanced Script**
```bash
cd /Users/mo/Documents/Games/HeroHeaven
ls -la kanka-sync.py
```

**Expected:** File exists, ~500+ lines (enhanced version)

---

### **2. Test API Connection**
```bash
source venv/bin/activate
python kanka-sync.py --test-connection
```

**Expected:**
```
✓ Connected to campaign: Hero Heaven
```

---

## Phase 1: Dry Run (No Changes)

### **3. Run Dry Run**
```bash
python kanka-sync.py --dry-run
```

**Expected Output:**
```
🔍 Dry run mode - no changes will be made

[DRY RUN] turfan.md → location (private=False, 5 attrs, 0 GM posts)
  turfan.md: Auto-generated name: 'Turfan'  [if name missing]

==================================================
Sync complete:
  ✓ 1 files synced
  ✗ 0 files failed
  ⊘ 36 files skipped
==================================================
```

**If you see "36 files skipped":** They're missing `kanka_type` field. Run bulk-prepare first.

---

### **4. Bulk Prepare Locations**
```bash
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

**Expected:**
```
📁 Directory: World/Locations
📊 Status: 1 ready, 36 need preparation

🔧 Will add:
   kanka_type: location
   kanka_id: null
   is_private: False

⚠️  Update 36 files? (yes/no): yes

✅ Complete: 36 updated, 0 failed
```

---

### **5. Dry Run Again (After Bulk Prepare)**
```bash
python kanka-sync.py --dry-run
```

**Expected Output:**
```
[DRY RUN] turfan.md → location (private=False, 5 attrs, 0 GM posts)
[DRY RUN] samarkand.md → location (private=False, 4 attrs, 2 GM posts)
[DRY RUN] kashkar.md → location (private=False, 3 attrs, 2 GM posts)
... (37 total)

Sync complete:
  ✓ 37 files synced
  ✗ 0 files failed
  ⊘ 0 files skipped
```

**Check the counts:**
- Number of attrs shows how many frontmatter fields map to attributes
- Number of GM posts shows GM sections detected

---

## Phase 2: Test Sync (1 File)

### **6. Manual Test: Sync Just Turfan**

Edit a test location to isolate it:

```bash
# Temporarily rename other files so only turfan syncs
cd World/Locations
mkdir temp_hold
mv *.md temp_hold/
mv temp_hold/turfan.md .

# Now sync
cd ../..
python kanka-sync.py --sync
```

**Expected:**
```
⚠️  Ready to sync files to Kanka
Features: Content splitting, attributes, GM posts

Continue? (yes/no): yes

✓ Created: turfan.md (ID: 1970045)

Sync complete:
  ✓ 1 files synced
```

---

### **7. Verify in Kanka UI**

**Go to Kanka → Locations → Turfan**

**Check Overview Tab:**
- [ ] Name: "Turfan"
- [ ] Type: "route-node"
- [ ] Entry has Geography, Economy sections
- [ ] Entry does NOT have any GM sections

**Check Attributes Tab:**
- [ ] Elevation: 700 (or -154 based on your data)
- [ ] Coordinates: "42.95, 89.19"
- [ ] Resources: "wine, grapes, grain"
- [ ] Primary Factions: "@Oasis_Settlers"
- [ ] Map Marker Type: "route-node"

**Check Posts Tab:**
- [ ] Should be empty (turfan.md has no GM sections)

**Test "View As Player":**
- [ ] World → Members
- [ ] Click "View As" next to a player role
- [ ] Navigate to Turfan
- [ ] Confirm you see the location

---

### **8. Test with GM Content**

Pick a file with GM sections (like kashkar.md):

```bash
# Move kashkar out of temp_hold
mv World/Locations/temp_hold/kashkar.md World/Locations/

# Sync
python kanka-sync.py --sync
```

**Expected:**
```
✓ Created: kashkar.md (ID: ...)
  └─ 2 GM posts synced
```

**Verify in Kanka → Kashkar:**

**Posts Tab should have:**
- [ ] "World-Building Context" (admin-only)
- [ ] "Narrative Significance" (admin-only)

**Click one post, check:**
- [ ] Visibility shows "admin"
- [ ] Content is properly formatted HTML

**Test "View As Player":**
- [ ] Posts tab should be empty for players
- [ ] Only Overview and Attributes visible

---

## Phase 3: Bulk Sync

### **9. Restore All Files**
```bash
cd World/Locations
mv temp_hold/*.md .
rmdir temp_hold
cd ../..
```

### **10. Final Dry Run**
```bash
python kanka-sync.py --dry-run
```

**Expected:** All 37 files ready

---

### **11. Full Sync**
```bash
python kanka-sync.py --sync
```

**Expected:**
```
✓ Updated: turfan.md
✓ Updated: kashkar.md  (2 GM posts already exist)
  └─ 2 GM posts synced
✓ Created: samarkand.md (ID: ...)
  └─ 2 GM posts synced
... (continues for all files)

Sync complete:
  ✓ 37 files synced
  ✗ 0 files failed
```

---

### **12. Verify Kanka**

**Check entity counts:**
- [ ] Go to Kanka → Locations
- [ ] Should see ~37 locations
- [ ] Spot-check 5 random ones for:
  - Proper name
  - Entry content (no Leaflet blocks)
  - Attributes populated
  - GM posts on relevant ones

**Check "View As Player":**
- [ ] Locations visible
- [ ] GM posts NOT visible
- [ ] Attributes visible (except private ones)

---

## Phase 4: Updates Test

### **13. Modify a File**

Edit `turfan.md`:
```yaml
elevation: 1000  # Changed from 700
```

Add a GM section:
```markdown
## Plot Hooks

Investigate strange vine growth.
```

### **14. Sync Again**
```bash
python kanka-sync.py --sync
```

**Expected:**
```
✓ Updated: turfan.md
  └─ 1 GM posts synced
```

**Verify in Kanka → Turfan:**
- [ ] Attribute "Elevation" now shows 1000
- [ ] Posts tab has new "Plot Hooks" post

---

## Common Issues

### **Issue: "Missing kanka_type field"**
**Fix:** Run bulk-prepare script

### **Issue: "Connection failed"**
**Fix:** Check `kanka-sync-config.yaml` has correct token and campaign_id

### **Issue: "Failed to create location"**
**Fix:** Check `kanka-sync.log` for details, likely API error

### **Issue: Sections in wrong place**
**Fix:** Check section headers match exactly (case-sensitive)

### **Issue: Attributes not appearing**
**Fix:** Check frontmatter field names match ATTRIBUTE_MAPPINGS

### **Issue: GM posts not created**
**Fix:** Check section headers match GM_SECTION_MARKERS exactly

---

## Success Criteria

✅ **All 37 location files synced**  
✅ **Attributes populated correctly**  
✅ **GM sections in separate posts**  
✅ **Posts are admin-only**  
✅ **"View As Player" shows correct content**  
✅ **Faction @mentions are clickable (if faction entities exist)**  
✅ **Updates work (modifying file updates Kanka)**  
✅ **No Leaflet blocks in Kanka**  
✅ **No duplicate entities created**  

---

## Next Steps After Success

1. ✅ Sync is working
2. Test with character archetypes (when created)
3. Test with mechanics notes (if you want them in Kanka)
4. Set up automated sync (optional - cron/LaunchAgent)
5. Invite players to Kanka campaign
6. Test permission system with real player accounts

---

**Ready to test!** Follow this checklist step-by-step.
