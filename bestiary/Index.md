---
title: Bestiary Directory Index
project: TTRPG_Tarim_Shaiel
type: directory_index
purpose: Dynamic navigation for creature and adversary resources
created: 2026-01-28
---

# Bestiary Directory

## Quick Navigation

### 🐉 Creatures & Adversaries
```dataview
LIST 
FROM "bestiary" 
WHERE file.name != "Index.md"
SORT file.name ASC
```

### 📊 Directory Stats
- **Total Files:** `= length(file.rows)`
- **Last Updated:** `= date(now)`
- **Purpose:** Creature designs, adversary templates, and monster resources

---

## About This Directory

This directory contains resources for:
- **Creature designs** and stat blocks
- **Adversary templates** for encounters
- **Monster ecology** and behavior patterns
- **Bestiary organization** by campaign region

## Related Directories

- [[../mechanics/character-progression|Character Progression]]
- [[../world/locations|Creature Habitats]]
- [[../templates/world-building|World-Building Templates]]

---

*This index updates automatically using Dataview queries.*
