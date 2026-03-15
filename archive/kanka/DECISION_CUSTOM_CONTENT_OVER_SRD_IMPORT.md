---
title: SRD Import Decision - Custom Content Over Bulk Conversion
date: 2026-01-28
type: decision-log
tags: [decision, srd, adversaries, world-building, daggerheart]
---

# Decision: Custom Content Over SRD Bulk Import

## Context

After successfully implementing Phase 2 Daggerheart parsing for Kanka sync, the question arose: Should we bulk-convert all 130+ SRD adversaries for import to Kanka?

## Decision: **NO - Create Custom Content As Needed**

### Rationale

**Against Bulk Import:**
- ❌ 130+ generic fantasy adversaries don't fit Tarim-Shaiel's Silk Road-inspired setting
- ❌ SRD creatures lack cultural/regional customization
- ❌ No R/H/K thematic integration in generic stat blocks
- ❌ Would clutter Kanka with unused content
- ❌ Requires busywork to customize afterward anyway

**For Custom Creation:**
- ✅ Build adversaries that fit the actual world (Silk Road setting)
- ✅ Design them for specific regions/cultures as needed
- ✅ Integrate R/H/K themes from the start
- ✅ Create content at campaign pace (quality over quantity)
- ✅ Use SRD as inspiration/reference, not wholesale import
- ✅ Environments need customization too - not just adversaries

### User Quote
> "That's also a LOT of 'stuff' I may not get to use (or would want to 'customize' anyway). I want adversaries that fit THIS world, AND environments as well... And I'll need time and help making those 'Daggerheart' compatible."

## Implications

### What This Means

1. **SRD stays reference-only** in Obsidian at `/references/daggerheart-srd/`
2. **Custom adversaries created as needed** for Tarim-Shaiel campaign
3. **Environments designed for actual locations** in the world
4. **Quality over quantity** - build what fits, when needed
5. **Collaborative approach** - user requests help designing Daggerheart-compatible content

### Converter Script Status

**Decision: NOT building bulk converter**
- Effort not worth it for content that won't be used
- Manual conversion available for specific SRD creatures that DO fit
- Can revisit if needs change

### Phase 2 Status

✅ **Phase 2 infrastructure is complete and ready**
- Daggerheart parsing works perfectly
- Can sync any properly formatted adversary
- Ready for custom content creation at user's pace

## Next Steps

### When User is Ready

Assistant is available to help:

1. **Design custom adversaries**
   - Silk Road-inspired creatures
   - Region-specific challenges
   - Culturally appropriate stat blocks
   - R/H/K thematic integration

2. **Create environment templates**
   - Daggerheart-compatible encounter design
   - Tied to specific Hero Heaven locations
   - Proper difficulty scaling

3. **Convert/adapt selected SRD content**
   - Cherry-pick specific creatures that fit
   - Customize for world setting
   - Manual conversion on case-by-case basis

4. **Build custom stat blocks**
   - Original adversaries
   - NPCs with Daggerheart stats
   - Faction-specific enemies

### Workflow

```
User identifies need → Collaborative design → Create in Obsidian → Sync to Kanka
```

**No rush** - content built organically as campaign develops

## Files Related to This Decision

- `utilities/SRD_ADVERSARY_FORMAT_ANALYSIS.md` - Format comparison and conversion options
- `utilities/PHASE_2_IMPLEMENTATION_COMPLETE.md` - Phase 2 completion status
- `templates/world-building/adversary_template.md` - Template for custom adversaries
- `bestiary/test-bear.md` - Example of properly formatted adversary

## Technical Notes

### SRD Format vs Kanka Sync Format

**SRD uses:** Prose markdown with bold/italic formatting
**Kanka sync requires:** YAML code blocks in `daggerheart` fences

This format mismatch reinforces the decision - even if we bulk-converted, the output would still need customization for Tarim-Shaiel's world.

## Conclusion

**Status:** DECIDED - Custom content creation approach
**Blocker Removed:** No need to spend time on bulk converter
**Path Forward:** Build world-appropriate content collaboratively as needed

User maintains full creative control over what enters the campaign world, ensuring all content fits the Hero Heaven setting and themes.

---

**Related Decisions:**
- [[utilities/DAGGERHEART_MIGRATION_PLAN|Daggerheart Migration Strategy]]
- [[utilities/PHASE_2_IMPLEMENTATION_COMPLETE|Phase 2 Completion]]

**Future Considerations:**
- May manually convert 5-10 specific SRD adversaries that fit well
- Environment design process to be developed
- R/H/K integration in stat blocks to be explored
