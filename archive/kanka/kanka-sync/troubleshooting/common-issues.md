---
title: Troubleshooting & Common Issues
type: troubleshooting
category: kanka-sync
tags: [kanka, troubleshooting, errors, faq]
parent: "[[utilities/kanka-sync/INDEX|Kanka Sync Documentation]]"
---

# Troubleshooting & Common Issues

**Solutions to common problems when syncing Obsidian to Kanka.**

---

## Quick Diagnostics

### **Run These First**

```bash
# 1. Test API connection
python kanka-sync.py --test-connection

# 2. Check what would sync
python kanka-sync.py --dry-run

# 3. Review recent logs
tail -30 kanka-sync.log
```

---

## Connection Issues

### **"Connection failed" / "401 Unauthorized"**

**Cause:** Invalid API token or wrong campaign ID

**Fix:**
1. Check `kanka-sync-config.yaml`
2. Verify API token at https://kanka.io/en-US/settings/api
3. Verify campaign ID in URL: `https://kanka.io/en-US/campaign/12345`
4. Ensure no extra spaces in token

**Test:**
```bash
python kanka-sync.py --test-connection
```

---

### **"Network timeout" / "Connection refused"**

**Cause:** Network issues or Kanka API down

**Fix:**
1. Check internet connection
2. Try accessing https://kanka.io in browser
3. Check Kanka status: https://status.kanka.io
4. Wait and retry

---

## File Not Syncing

### **"Skipping [file]: No kanka_type field"**

**Cause:** File missing required `kanka_type` field

**Fix:**
Add to frontmatter:
```yaml
kanka_type: location  # or character, note, etc.
```

**Bulk fix:**
```bash
python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
```

---

### **"Skipping [file]: Missing is_private field"**

**Note:** This is a **warning**, not an error. File will sync with default `is_private: false`.

**To suppress warning:**
Add explicit privacy flag:
```yaml
is_private: false  # or true
```

---

### **File Has kanka_type But Still Not Syncing**

**Check:**

1. **Is file in include_paths?**
   
   Check `kanka-sync-config.yaml`:
   ```yaml
   include_paths:
     - "World/Locations"  # Your file must be under this path
   ```

2. **Is file excluded?**
   
   Check `exclude_paths`:
   ```yaml
   exclude_paths:
     - "Templates"  # Files here won't sync
   ```

3. **Is filename a template?**
   
   Files starting with `_` or containing `_TEMPLATE` are skipped:
   - `_location_template.md` ❌
   - `LOCATION_TEMPLATE.md` ❌
   - `samarkand.md` ✅

---

## Content Routing Issues

### **Section Appearing in Wrong Place**

**Problem:** `## Geography` section going to GM posts instead of main entry

**Cause:** Section header doesn't match exactly (case-sensitive)

**Fix:**
```markdown
# ❌ Wrong
## geography
## GEOGRAPHY
## Geography:

# ✅ Correct
## Geography
```

**Check your section headers against:**
- [[../reference/routing-rules|Routing Rules]]

---

### **GM Content Visible to Players**

**Problem:** Secret information showing up in player view

**Causes & Fixes:**

1. **Section not in GM_SECTION_MARKERS**
   
   Unknown sections default to GM, but verify:
   ```markdown
   ## My Secret Section  # ← Is this in GM_SECTION_MARKERS?
   ```
   
   **If not:** Add to script or use standard GM sections

2. **Post visibility manually changed**
   
   Check in Kanka:
   - Entity → Posts tab
   - Edit post
   - Verify visibility: `admin` (not `all`)

3. **Entity is public but should be private**
   
   ```yaml
   is_private: true  # Hide entire entity
   ```

**Always test:** Use "View As Player" in Kanka to verify

---

### **Public Content Not Visible**

**Problem:** Geography section not showing in entity entry

**Causes:**

1. **Section header typo**
   ```markdown
   ## Geograpy  # ❌ Typo
   ## Geography  # ✅ Correct
   ```

2. **Content was stripped**
   
   Check if your content contains:
   - ` ```leaflet` blocks (these are removed)
   - Only Obsidian comments `%% ... %%` (removed)
   - Only wiki links `[[...]]` (converted to plain text)

3. **Content went to GM by mistake**
   
   Check Posts tab in Kanka - is it there?

---

## Attribute Issues

### **Attributes Not Created**

**Problem:** Frontmatter fields not becoming Kanka attributes

**Check:**

1. **Is field in ATTRIBUTE_MAPPINGS?**
   
   Only these fields create attributes:
   - `elevation`
   - `location` (coordinates)
   - `mapmarker`
   - `resources`
   - `factions`
   - `population`
   - `danger_level`
   
   See [[../reference/field-mappings|Field Mappings]]

2. **Is field spelled correctly?**
   ```yaml
   elevation: 700      # ✅ Correct
   elevaton: 700       # ❌ Typo - ignored
   ```

3. **Did sync actually run?**
   Check logs for attribute creation messages

---

### **Attribute Values Wrong**

**Problem:** Resources showing as `['silk', 'jade']` instead of `silk, jade`

**Cause:** Old version of script (before array conversion was added)

**Fix:**
1. Update to latest `kanka-sync.py`
2. Re-sync the file:
   ```bash
   python kanka-sync.py --sync
   ```

---

### **Faction Links Not Working**

**Problem:** `@Sogdian_Merchants_Guild` appears as plain text, not a link

**Cause:** The faction entity doesn't exist in Kanka yet

**Fix:**
1. Create the faction entity in Kanka
2. Name it exactly: "Sogdian Merchants Guild"
3. The @mention will auto-link

**Alternative:** Create entities first, then sync locations

---

## Rate Limiting

### **"Rate limit reached, waiting X seconds"**

**This is NORMAL!** Not an error.

**What's happening:**
- Kanka limits: 30 requests/minute
- Script automatically pauses
- Resumes when safe

**Expected behavior:**
```
✓ Created: file1.md
✓ Created: file2.md
...
⏱  Rate limit reached, waiting 45.3s...
✓ Created: file30.md
```

**No action needed** - let it run.

---

### **"429 Too Many Requests" Error**

**Cause:** Rate limit hit (shouldn't happen with updated script)

**Fix:**
1. Stop the script
2. Wait 60 seconds
3. Re-run sync
4. If persists: Report issue (script's rate limiter may be broken)

---

### **Sync Taking Too Long**

**Expected times:**
- 37 files: 15-20 minutes
- 10 files: 5-8 minutes
- 3 files: 2-3 minutes

**If much slower:**
1. Check network speed
2. Check Kanka API status
3. Review logs for repeated errors/retries

---

## Data Issues

### **Frontmatter Getting Corrupted**

**Problem:** After sync, frontmatter shows weird formatting

**Cause:** python-frontmatter library reformats YAML

**Prevention:**
1. Use consistent YAML style
2. Avoid complex nested structures
3. Back up files before first sync

**Fix:**
If corrupted:
1. Restore from backup
2. Manually fix YAML formatting
3. Re-sync

---

### **kanka_id Not Being Written**

**Problem:** After successful create, `kanka_id` still null

**Causes:**

1. **File write permission issue**
   ```bash
   ls -la path/to/file.md
   # Check if writable
   ```

2. **File open in another program**
   Close file in editors during sync

3. **Script error during write**
   Check logs for write errors

**Fix:**
Manually add the ID from logs:
```
✓ Created: samarkand.md (ID: 1970046)
```

```yaml
kanka_id: 1970046  # Add manually
```

---

## Script Errors

### **"ModuleNotFoundError: No module named 'frontmatter'"**

**Cause:** Missing dependencies

**Fix:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

### **"FileNotFoundError: kanka-sync-config.yaml"**

**Cause:** Config file missing or wrong directory

**Fix:**
```bash
# Check you're in correct directory
pwd
# Should show: /Users/mo/Documents/Games/HeroHeaven

# Check config exists
ls kanka-sync-config.yaml

# Create if missing
cp kanka-sync-config.yaml.example kanka-sync-config.yaml
```

---

### **Python Version Issues**

**Error:** `SyntaxError: invalid syntax` or `f-string` errors

**Cause:** Python version too old

**Fix:**
```bash
python3 --version
# Need 3.8 or higher

# Use correct Python
python3 kanka-sync.py --test-connection
```

---

## Kanka UI Issues

### **Can't Find Synced Entity**

**Check:**

1. **Correct entity type?**
   - Locations → Locations tab
   - Characters → Characters tab
   - etc.

2. **Is entity private?**
   Check your frontmatter:
   ```yaml
   is_private: true  # You won't see it in player view
   ```
   
   Switch to GM view

3. **Search by name**
   Use Kanka's search: exact name from frontmatter

---

### **"View As Player" Not Working**

**Setup:**
1. Go to World → Members
2. Create a test player role
3. Click "View As" next to player role

**If still not working:**
- Clear browser cache
- Try incognito/private window
- Check Kanka permissions for role

---

### **Posts Tab Empty (Expected Posts)**

**Check:**

1. **Does file have GM sections?**
   ```markdown
   ## Narrative Significance  # ← GM section
   ```

2. **Did sync actually create posts?**
   Check logs:
   ```
   ✓ Created: file.md
     └─ 2 GM posts synced  # ← Should see this
   ```

3. **Are you in GM view?**
   Posts are admin-only - player view won't show them

---

## Validation Errors

### **"Invalid entity type 'X'"**

**Cause:** Typo in `kanka_type`

**Valid types:**
- location
- character
- note
- quest
- organization
- item
- timeline
- journal
- ability
- event
- calendar
- creature

**Fix:**
```yaml
kanka_type: location  # Must be exact, lowercase
```

---

## Getting More Help

### **Enable Debug Logging**

Edit `kanka-sync-config.yaml`:

```yaml
logging:
  level: DEBUG  # Changed from INFO
  file: "kanka-sync.log"
```

Re-run sync - logs will be much more verbose.

---

### **Collect Diagnostic Info**

```bash
# 1. Test connection
python kanka-sync.py --test-connection > diagnostics.txt

# 2. Dry run output
python kanka-sync.py --dry-run >> diagnostics.txt

# 3. Recent logs
tail -50 kanka-sync.log >> diagnostics.txt

# 4. Config (remove API token first!)
cat kanka-sync-config.yaml >> diagnostics.txt
```

---

### **Check Script Version**

```bash
head -20 kanka-sync.py | grep "v2.0"
```

Should show: `Obsidian → Kanka Sync Script (Enhanced v2.0)`

If not: Update to latest version.

---

## Known Limitations

### **Cannot Do (By Design)**

❌ **Sync images/files** - Only text content  
❌ **Sync relationships** - No entity linking yet  
❌ **Sync tags** - Not implemented  
❌ **Bidirectional sync** - Kanka → Obsidian not supported  
❌ **Selective attribute sync** - All or nothing per file  

### **Planned Features**

🔜 Tag syncing  
🔜 Parent location relationships  
🔜 Image upload support  
🔜 Bidirectional sync  

---

## Related Documentation

- [[../guides/quickstart|Quickstart Guide]] - Setup instructions
- [[../guides/daily-workflow|Daily Workflow]] - Usage patterns
- [[../reference/routing-rules|Routing Rules]] - Content routing
- [[../reference/field-mappings|Field Mappings]] - Frontmatter reference
- [[../INDEX|Documentation Index]] - All docs

---

[[INDEX|← Back to Documentation Index]]
