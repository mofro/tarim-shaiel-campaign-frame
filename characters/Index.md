---
title: Characters Directory Index
project: TTRPG_Tarim_Shaiel
type: directory_index
purpose: Dynamic navigation for character development resources
created: 2026-01-28
---

# Characters Directory

## Quick Navigation

### 📋 Character Framework
```dataview
LIST 
FROM "characters" 
WHERE file.name != "Index.md"
SORT file.name ASC
```

### 📊 Directory Stats
- **Total Files:** `= length(file.rows)`
- **Last Updated:** `= date(now)`
- **Purpose:** Character development and archetype frameworks

---

## About This Directory

This directory contains character development resources including:
- **Archetype frameworks** for player character concepts
- **Character creation templates** and guidelines
- **Development methodologies** for Tarim-Shaiel characters

## Related Directories

- [[../mechanics/character-creation|Character Creation Mechanics]]
- [[narrative-template|Narrative Foundation]]
- [[../world/locations|Character Locations]]

---

*This index updates automatically using Dataview queries.*
