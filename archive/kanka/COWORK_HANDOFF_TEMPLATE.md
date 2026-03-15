---
title: Cowork Handoff Template
date: 2026-01-29
type: workflow-guide
tags: [cowork, workflow, context-transfer]
---

# Cowork Handoff Template

## Purpose

This template ensures smooth context transfer from Chat sessions to Cowork sessions by structuring documentation for easy Cowork consumption.

---

## Template Structure

### 1. Task Brief (Top of Document)

```markdown
## COWORK TASK BRIEF

**Goal:** [One sentence description]
**Input Files:** [List of files to read]
**Output Files:** [List of files to create]
**Dependencies:** [Other docs to reference]
**Estimated Complexity:** [Low/Medium/High]
```

### 2. Context Section

```markdown
## Context

[Brief background - what led to this task]
[Key decisions made]
[Constraints or requirements]
```

### 3. Detailed Requirements

```markdown
## Requirements

### Must Have
- [ ] Requirement 1
- [ ] Requirement 2

### Should Have
- [ ] Optional feature 1

### Must NOT Do
- [ ] Anti-pattern to avoid
```

### 4. Implementation Guide

```markdown
## Implementation Guide

**Approach:** [High-level strategy]

**Steps:**
1. Step 1
2. Step 2
3. Step 3

**Code Structure:**
- File 1: Purpose
- File 2: Purpose

**Testing:**
- Test case 1
- Test case 2
```

### 5. File Locations

```markdown
## File Locations

**Input:**
- `/path/to/input1.md`
- `/path/to/input2.json`

**Output:**
- `/path/to/output1.py`
- `/path/to/output2.md`

**Reference:**
- `/path/to/reference_doc.md`
```

### 6. Examples

```markdown
## Examples

### Example Input
[Show what input looks like]

### Example Output
[Show what output should look like]
```

### 7. Validation Checklist

```markdown
## Validation Checklist

After completion, verify:
- [ ] All output files created
- [ ] Files in correct locations
- [ ] Format matches examples
- [ ] No errors in logs
```

---

## Example: Equipment Converter Task

```markdown
## COWORK TASK BRIEF

**Goal:** Build Python converter to transform SRD Tier 1 equipment to Kanka format
**Input Files:** 
- `/references/daggerheart-srd/weapons/*.md` (32 files)
- `/references/daggerheart-srd/armor/*.md` (4 files)
**Output Files:** 
- `/utilities/scripts/srd-equipment-converter.py`
- `/equipment/weapons/*.md` (32 files after running)
- `/equipment/armor/*.md` (4 files after running)
**Dependencies:** 
- `SRD_REFERENCE_MATERIAL_ANALYSIS.md` (format specs)
- `EQUIPMENT_CONVERTER_GUIDE.md` (usage instructions)
**Estimated Complexity:** Medium

## Context

Phase 2 Daggerheart integration is complete. We decided to import Tier 1 
basic equipment (weapons + armor) but NOT bulk import all SRD adversaries 
(see DECISION_CUSTOM_CONTENT_OVER_SRD_IMPORT.md). Equipment has simple 
format suitable for automated conversion.

## Requirements

### Must Have
- [ ] Parse all Tier 1 weapons (no Advanced/Improved/Legendary)
- [ ] Parse all Tier 1 armor (4 basic types)
- [ ] Generate Kanka frontmatter with attributes
- [ ] Create markdown body with stats section
- [ ] Output to /equipment/weapons/ and /equipment/armor/

### Should Have
- [ ] Progress logging during conversion
- [ ] Summary statistics at end
- [ ] Handle missing files gracefully

### Must NOT Do
- [ ] Import Advanced/Improved/Legendary variants
- [ ] Modify original SRD files
- [ ] Sync to Kanka (that's separate step)

## Implementation Guide

**Approach:** Regex parsing of consistent SRD format → YAML frontmatter generation

**Steps:**
1. Define lists of Tier 1 files to convert
2. Parse weapon format (Trait, Range, Damage, Burden)
3. Parse armor format (Thresholds, Score)
4. Generate frontmatter with kanka_type + attributes
5. Create markdown body
6. Write to output directories

**Code Structure:**
- `parse_weapon()`: Extract data from SRD weapon file
- `parse_armor()`: Extract data from SRD armor file
- `generate_weapon_markdown()`: Create Kanka-ready output
- `generate_armor_markdown()`: Create Kanka-ready output
- `convert_weapons()`: Loop through weapon list
- `convert_armor()`: Loop through armor list
- `main()`: Orchestrate conversion

**Testing:**
- Test on Longsword.md (weapon)
- Test on Leather Armor.md (armor)
- Verify frontmatter format
- Verify output locations
```

---

## Usage in Chat Sessions

When creating handoff documentation, Claude should:

1. **Add COWORK TASK BRIEF** to top of technical documentation
2. **List all relevant files** with full paths
3. **Be explicit about requirements** (must/should/must-not)
4. **Include examples** of expected input/output
5. **Reference other context docs** by name

---

## Usage in Cowork Sessions

User prompt example:

```
Read SRD_EQUIPMENT_CONVERTER_HANDOFF.md and build the converter 
as specified. Reference SRD_REFERENCE_MATERIAL_ANALYSIS.md for 
format details.
```

Cowork will:
1. Read the handoff doc
2. Read referenced docs
3. Parse requirements
4. Build implementation
5. Create outputs in specified locations
6. Report completion

---

## File Naming Convention

**Handoff docs should be named:**
- `[TASK_NAME]_HANDOFF.md`

**Examples:**
- `EQUIPMENT_CONVERTER_HANDOFF.md`
- `CUSTOM_ADVERSARY_CREATION_HANDOFF.md`
- `FACTION_STAT_BLOCKS_HANDOFF.md`

**Location:** `/utilities/handoffs/` directory

---

## Benefits

✅ **Clear context transfer** - Cowork knows exactly what to do
✅ **Reproducible** - Can re-run with same instructions
✅ **Reviewable** - User can read the handoff before running
✅ **Self-documenting** - Task brief explains why/what/how
✅ **Testable** - Validation checklist ensures completeness

---

## Next Steps

1. Create `/utilities/handoffs/` directory
2. Convert existing docs to handoff format when needed
3. Use template for new complex tasks
4. Iterate based on what works in practice

---

**Future Enhancement Ideas:**
- Add "Rollback Instructions" section
- Add "Known Issues" section
- Add "Performance Expectations" (time/resources)
- Include "Related Tasks" links
