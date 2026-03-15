---
type: test-query
purpose: Verify Dataview plugin works with Location Notes
created: 2025-12-13
---

# Test: Dataview Location Query

Below should show a table of all Location Notes in `/world/locations/`.

```dataview
TABLE name, type, location, description
FROM "world/locations"
WHERE location AND type
SORT name ASC
```

---

**Expected result:** 3 locations (Dunhuang, Kashgar, Samarkand) with their coordinates and types displayed.

**If this works:** ✅ Dataview is functioning correctly
