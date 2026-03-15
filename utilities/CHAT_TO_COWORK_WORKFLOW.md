---
title: Chat-to-Cowork Workflow Guide
date: 2026-01-29
type: workflow
tags: [workflow, cowork, chat, collaboration]
---

# Chat-to-Cowork Workflow Guide

## The Two-Phase Workflow

### Phase 1: Design & Decide (Chat)
**Where:** claude.ai chat (this interface)
**Who:** You + Claude collaborating
**What:** Discuss, design, decide, document

**Outputs:**
- Decision logs
- Design docs
- Handoff documents
- Context files

### Phase 2: Build & Execute (Cowork)
**Where:** Claude Desktop app → Cowork tab
**Who:** Cowork Claude autonomously executing
**What:** Read handoffs, build code, create files

**Outputs:**
- Working code
- Generated files
- Processed data
- Final deliverables

---

## When to Use Each

### Use Chat For:
✅ Brainstorming and ideation
✅ Making decisions (import vs custom, formats, etc.)
✅ Discussing approaches and trade-offs
✅ Creating documentation and plans
✅ Quick questions and clarifications
✅ Learning and understanding concepts
✅ Reviewing outputs from Cowork

### Use Cowork For:
✅ Building multi-file codebases
✅ Processing many files in batch
✅ Complex file organization tasks
✅ Creating large documents (reports, spreadsheets)
✅ Data extraction and synthesis
✅ Repetitive file operations
✅ Long-running autonomous tasks

### Use Both Together:
⭐ **Design in Chat → Build in Cowork → Review in Chat** ⭐

---

## Example Workflow: Equipment Converter

### Step 1: Design Phase (Chat)
```
You: "What about the SRD equipment? Should we import it?"

Claude: [Analyzes SRD format, creates comparison docs]

You: "Let's do Tier 1 basics only"

Claude: [Creates decision log, analysis, handoff doc]

Outputs created:
- SRD_REFERENCE_MATERIAL_ANALYSIS.md
- DECISION_CUSTOM_CONTENT_OVER_SRD_IMPORT.md
- EQUIPMENT_CONVERTER_HANDOFF.md
```

### Step 2: Build Phase (Cowork)
```
[Open Claude Desktop → Cowork tab]
[Grant access to HeroHeaven folder]

You: "Read utilities/handoffs/EQUIPMENT_CONVERTER_HANDOFF.md 
and build the converter as specified"

Cowork: [Reads handoff → Reads SRD files → Builds script → 
Creates output files → Reports completion]

Outputs created:
- utilities/scripts/srd-equipment-converter.py
- equipment/weapons/ (32 files)
- equipment/armor/ (4 files)
```

### Step 3: Review Phase (Chat)
```
You: "Ran the converter, got an error on Shortbow.md"

Claude: [Debugs, provides fix]

You: "Working now! Should I sync to Kanka?"

Claude: [Provides sync instructions, next steps]
```

---

## Handoff Document Checklist

When creating handoff docs in Chat, include:

**✅ COWORK TASK BRIEF section at top**
- Clear one-sentence goal
- All input file paths (full absolute paths)
- All output file paths (full absolute paths)
- Referenced docs for context
- Complexity estimate

**✅ Context section**
- Why this task exists
- What decisions led here
- Key constraints

**✅ Requirements section**
- Must Have (critical)
- Should Have (nice to have)
- Must NOT Do (anti-patterns)

**✅ Implementation Guide**
- Code structure
- Parsing logic
- Error handling
- Examples

**✅ Validation Checklist**
- How to verify success
- What to test
- Expected outcomes

---

## File Organization Strategy

### `/utilities/` Directory Structure

```
utilities/
├── handoffs/                    # Cowork task specs
│   ├── EQUIPMENT_CONVERTER_HANDOFF.md
│   ├── CUSTOM_ADVERSARY_HANDOFF.md
│   └── ...
├── scripts/                     # Executable code
│   ├── kanka-sync.py
│   ├── srd-equipment-converter.py
│   └── ...
├── COWORK_HANDOFF_TEMPLATE.md  # Template reference
├── DECISION_*.md                # Decision logs
├── PHASE_*.md                   # Implementation docs
└── *_ANALYSIS.md                # Analysis docs
```

**Naming Conventions:**
- Handoffs: `[TASK_NAME]_HANDOFF.md` in `/handoffs/`
- Decisions: `DECISION_[TOPIC].md` in `/utilities/`
- Analysis: `[TOPIC]_ANALYSIS.md` in `/utilities/`
- Guides: `[TOPIC]_GUIDE.md` in `/utilities/`

---

## Communication Patterns

### Chat → Cowork
**Via:** Handoff documents (markdown files)
**Content:** Task specs, requirements, examples, context
**Format:** Structured markdown with sections

### Cowork → Chat
**Via:** You manually report results
**Content:** "It worked!" or "Got an error: XYZ"
**Format:** Natural language

### No Direct Communication
❌ Cowork can't talk to Chat
❌ Chat can't see Cowork's work in progress
✅ Files on disk are the bridge

---

## Best Practices

### In Chat Sessions

**DO:**
- ✅ Create detailed handoff docs with full paths
- ✅ Use absolute paths (not relative)
- ✅ Include specific examples
- ✅ Reference other docs by exact filename
- ✅ Add validation checklists
- ✅ Organize docs logically

**DON'T:**
- ❌ Assume Cowork has chat context
- ❌ Use relative paths or shortcuts
- ❌ Leave requirements vague
- ❌ Skip examples
- ❌ Forget to specify output locations

### In Cowork Sessions

**DO:**
- ✅ Point to specific handoff docs
- ✅ Grant minimal folder access needed
- ✅ Review the plan before approving
- ✅ Monitor progress
- ✅ Return to Chat for debugging

**DON'T:**
- ❌ Give vague instructions
- ❌ Grant access to entire home folder
- ❌ Auto-approve without reading
- ❌ Leave it running unwatched on critical files
- ❌ Try to transfer complex context verbally

---

## Common Patterns

### Pattern 1: Code Generator
```
Chat: Design API, write handoff
Cowork: Build implementation
Chat: Review, iterate if needed
```

### Pattern 2: Batch Processor
```
Chat: Define transformation logic, write handoff
Cowork: Process all files
Chat: Verify results, handle edge cases
```

### Pattern 3: Document Creator
```
Chat: Define outline, provide data, write handoff
Cowork: Generate formatted documents
Chat: Review, request edits
```

### Pattern 4: File Organizer
```
Chat: Define organization rules, write handoff
Cowork: Sort/rename/move files
Chat: Verify structure
```

---

## Troubleshooting

### "Cowork didn't understand the task"
**Fix:** Handoff doc needs more specificity
- Add concrete examples
- List exact file paths
- Show expected input/output

### "Cowork did the wrong thing"
**Fix:** Requirements section needs Must NOT items
- Specify anti-patterns to avoid
- Add constraints explicitly
- Show counterexamples

### "Can't pass context to Cowork"
**Fix:** Create intermediate markdown files
- Save context as .md files
- Reference them in handoff
- Cowork reads them

### "File paths don't work"
**Fix:** Use absolute paths, verify locations
- Always use `/Users/mo/...` full paths
- No `~/` shortcuts
- No relative paths like `../../`

---

## Future Enhancements

Ideas for improving the workflow:

- **Handoff validation tool** - Check handoffs before running
- **Cowork templates** - Pre-built handoffs for common tasks
- **Results logger** - Automatic logging of Cowork outputs
- **Diff viewer** - Compare Chat suggestions vs Cowork outputs

---

## Summary

**The Golden Rule:**
```
Chat = Brain (design, decide, document)
Cowork = Hands (build, execute, deliver)
Files = Bridge (handoffs, context, outputs)
```

**The Workflow:**
```
1. Discuss in Chat → Create handoff docs
2. Run in Cowork → Build implementations
3. Review in Chat → Iterate if needed
```

**The Files:**
```
/utilities/handoffs/[TASK]_HANDOFF.md  ← Cowork reads this
/utilities/scripts/[output].py         ← Cowork creates this
/utilities/DECISION_*.md               ← Context for understanding
```

---

**Next:** Try this workflow with the equipment converter!
