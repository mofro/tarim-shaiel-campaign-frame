---
title: Dynamic Template Options Guide
type: documentation
created: 2025-01-28
tags: [templater, dataview, templates, how-to]
---

# Dynamic Template Options Guide

You now have **three** character template options. Choose based on your workflow preferences.

---

## Option 1: Templater (Interactive Dropdowns)

**File:** `templates/character-creation/character_template_TEMPLATER.md`

### How It Works
When you insert this template, Templater will:
1. Scan your SRD directories for available files
2. Present interactive dropdown menus for each choice
3. Auto-fill the frontmatter and wikilinks with your selections
4. Prompt for character name and player name

### Usage
1. Create a new note in your desired location
2. Use Templater command: `Templater: Insert Template`
3. Select `character_template_TEMPLATER`
4. Answer the prompts:
   - Select Daggerheart Class
   - Select Subclass
   - Select Ancestry
   - Select Community
   - Select Tarim-Shaiel Archetype
   - Enter Character Name
   - Enter Player Name (or leave blank for NPC)

### Advantages
- ✅ Fastest workflow - all selections in one go
- ✅ No typos - selections are guaranteed valid
- ✅ Auto-populates frontmatter AND wikilinks
- ✅ Can prompt for additional info (character name, player, etc.)
- ✅ Dynamic - automatically includes new files added to SRD

### Disadvantages
- ❌ Requires Templater plugin
- ❌ Once inserted, can't re-run the dropdowns (must edit manually)
- ❌ Need to know your choices upfront

---

## Option 2: Dataview (Collapsible Reference Lists)

**File:** `templates/character-creation/character_template_DATAVIEW.md`

### How It Works
The template includes collapsible callouts with Dataview queries that show:
- All available classes (clickable links)
- All available subclasses (clickable links)
- All available ancestries (clickable links)
- All available communities (clickable links)
- All available archetypes (clickable links)

Click any link to navigate to the full SRD entry, then manually update the wikilink.

### Usage
1. Create a new note
2. Insert template (standard Obsidian template or Templater)
3. Expand the `> [!info]- Available Options` callout
4. Browse the lists to find what you want
5. Click to preview/read the full entry
6. Manually edit the wikilinks below to match your choice

### Advantages
- ✅ Persistent - reference lists stay in the document
- ✅ Browse before deciding - see all options without committing
- ✅ Click to read - easy navigation to full SRD entries
- ✅ Dynamic - automatically updates if SRD files change
- ✅ No extra setup - just uses standard template insertion

### Disadvantages
- ❌ Manual editing required - must type/paste the link yourself
- ❌ Reference sections add visual clutter (though collapsible)
- ❌ Requires Dataview plugin

---

## Option 3: Static Examples (Current Default)

**File:** `templates/character-creation/character_template.md`

### How It Works
Template has working example links pre-filled (Ranger/Beastbound/Human/Wanderborne). You edit them directly.

### Usage
1. Insert template
2. Edit the wikilinks to match your desired choices

### Advantages
- ✅ Simplest - no plugins required (beyond standard templates)
- ✅ Clean - no extra UI elements
- ✅ Fast if you know what you want

### Disadvantages
- ❌ Must know file names exactly (or use autocomplete)
- ❌ Typos possible
- ❌ Need to reference SRD separately

---

## Recommendations by Use Case

### For Quick Character Creation (You Know What You Want)
**Use Templater version** - fastest workflow, zero typos

### For Exploratory/Learning (Browsing Options)
**Use Dataview version** - see everything, click to read, then decide

### For Minimal Setup (No Extra Plugins)
**Use Static version** - simple and clean

---

## Implementation Notes

### Templater Script Details
The Templater version uses:
- `app.vault.getMarkdownFiles()` to scan directories
- `.filter()` to find files in specific paths
- `tp.system.suggester()` to present dropdown menus
- `tp.system.prompt()` for text input

### Dataview Query Pattern
```dataview
TABLE WITHOUT ID file.link as "DisplayName"
FROM "path/to/directory"
SORT file.name ASC
```

This creates a single-column table of clickable links, sorted alphabetically.

### Callout Syntax
```markdown
> [!info]- Collapsible Title
> Content here is hidden until clicked
```

The `-` after `[!info]` makes it collapsed by default.

---

## Adding Dynamic Lists to Other Templates

You can apply these patterns to ANY template:

### For Adversary Template (BeastVault)
Add a reference section for adversary types from your bestiary:

```markdown
> [!info]- Available Adversaries
> ```dataview
> TABLE WITHOUT ID file.link as "Adversary", type as "Type"
> FROM "bestiary"
> WHERE file.name != "Index"
> SORT file.name ASC
> ```
```

### For Charm Template
Add domain and archetype selectors:

**Templater version:**
```markdown
<%*
const domainFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith("references/daggerheart-srd/domains/"));
const domainList = domainFiles.map(f => f.basename).sort();
const chosenDomain = await tp.system.suggester(domainList, domainList, false, "Select Domain");
-%>
**Domain:** [[references/daggerheart-srd/domains/<% chosenDomain %>|<% chosenDomain %>]]
```

**Dataview version:**
```markdown
> [!info]- Available Domains
> ```dataview
> TABLE WITHOUT ID file.link as "Domain"
> FROM "references/daggerheart-srd/domains"
> SORT file.name ASC
> ```
```

---

## Testing Your Setup

### Test Templater Version
1. Create new note: `test-character-templater.md`
2. Insert template: `character_template_TEMPLATER`
3. Select: Wizard, School of Knowledge, Elf, Loreborne, Seeker
4. Enter name: "Test Character"
5. Verify frontmatter and links are correct
6. Delete test note

### Test Dataview Version
1. Create new note: `test-character-dataview.md`
2. Insert template: `character_template_DATAVIEW`
3. Expand the `Available Options` callout
4. Verify lists render correctly
5. Click one link to test navigation
6. Delete test note

---

## Troubleshooting

### Templater dropdowns are empty
**Cause:** Template can't find files in the specified directories
**Fix:** Check that paths match your vault structure exactly

### Dataview shows "No results"
**Cause:** Query path doesn't match actual directory
**Fix:** Verify the `FROM "path"` matches your folder structure

### Templater won't run
**Cause:** Templater plugin not enabled, or template not in templates folder
**Fix:** 
- Settings → Community Plugins → Enable Templater
- Settings → Templater → Template folder location
- Move template to designated templates folder

### Dataview shows raw code
**Cause:** Dataview plugin not enabled
**Fix:** Settings → Community Plugins → Enable Dataview

---

[[utilities/DAGGERHEART_MIGRATION_PLAN|← Migration Plan]] | [[character_template|Static Template]] | [[templates/character-creation/character_template_TEMPLATER|Templater Template]] | [[templates/character-creation/character_template_DATAVIEW|Dataview Template]]
