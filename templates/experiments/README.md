---
title: Template Experiments Archive
type: archive
created: 2025-01-28
tags: [archive, experiments, templates]
---

# Template Experiments Archive

This folder contains experimental template variations that were explored during Phase 1 of the Daggerheart migration but not adopted for production use.

## Contents

### character_template_TEMPLATER.md
Interactive template using Templater plugin with dropdown prompts for class/subclass/ancestry/community selections.

**Why archived:** Dropdowns show ALL options without filtering for class-subclass dependencies. For one-off character creation, the added complexity wasn't worth the marginal time savings.

**Could be useful for:** Rapid NPC generation where relationships don't matter, or if SRD gets structured metadata.

### character_template_DATAVIEW.md
Template with embedded collapsible Dataview reference lists showing all available options.

**Why archived:** Same manual editing effort as static examples, but with visual clutter from reference sections.

**Could be useful for:** Learning the SRD options, or if you frequently forget what's available.

### DYNAMIC_TEMPLATE_OPTIONS_GUIDE.md
Comprehensive guide to using both experimental templates, including troubleshooting and extension patterns.

**Why archived:** Templates archived, so guide is no longer relevant for production workflow.

**Could be useful for:** Reference if you want to apply these patterns to other templates in the future.

## Production Templates

The active production templates are in their respective directories:
- `templates/character-creation/character_template.md` - Static examples (clean, simple)
- `templates/mechanics/charm_template.md` - Static examples
- `templates/world-building/adversary_template.md` - BeastVault-compatible
- `templates/world-building/environment_template.md` - Encounter design

## Future Considerations

These experimental approaches might become relevant if:
1. SRD files gain structured frontmatter with relationship metadata
2. Character creation volume increases significantly (e.g., running convention games)
3. You want to build an NPC generator tool
4. Templater gets better support for complex conditional logic

---

[[character_template|← Production Character Template]] | [[../../utilities/PHASE_1_COMPLETION_SUMMARY|Phase 1 Summary →]]
