---
name: legendkeeper-timeline-builder
description: Build rich, multi-layered timelines for LegendKeeper using the nianhao (overlapping regional eras) pattern. Use this skill whenever the user mentions LegendKeeper timelines, wants to create timeline JSON, needs to add historical events, wants to implement faction-specific eras, or asks about timeline color coding. Also trigger when user uploads timeline data files (.json, .md with dates) or asks to convert historical data into LegendKeeper format, even if they don't explicitly say "timeline."
---

# LegendKeeper Timeline Builder

## Overview

This skill creates rich, historically-layered timelines for LegendKeeper using the **nianhao pattern** — a Chinese-inspired system where different factions have overlapping regional era names for the same time periods.

## Core Concept: The Nianhao Pattern

**Challenge:** LegendKeeper's calendar eras are global — you can't have faction-specific eras where Orcs call year 850 "Year 1 of Copper Peace" while Dwarves call it "Year 130 of Mountain Accord."

**Solution:** Use long-span events to REPRESENT faction-specific time periods:
- **Lane 1:** Era declarations (50-150 year spans, low opacity 0.3, flag icons)
- **Lane 2:** Historical events (actual events, full opacity 1.0, varied icons)

Events visually sit "within" their faction's era containers, showing overlapping regional time systems.

## Workflow Decision Tree

```
User request
├─ Create new timeline → Gather Input → Generate Timeline
├─ Add events to existing → Read JSON → Add Events → Save
├─ Apply nianhao pattern → Read JSON → Generate Eras → Restructure
├─ Fix/validate timeline → Read JSON → Validate → Fix Issues
└─ Convert data to timeline → Parse Data → Generate Timeline
```

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
