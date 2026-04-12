---
title: Example Category with All Components
description: Demonstrates images, feature boxes, and jump navigation
published: true
jump_nav: true
banner_left: Example Category
banner_right: Full Feature Demo
---

## Overview

This is a demonstration of all three component types supported by category pages:

1. **Inline images** with captions using `![[filename.png|caption]]` syntax
2. **Feature boxes** using `**Feature Name:** description` markdown
3. **Jump navigation** auto-generated from H2 and H3 headers (when `jump_nav: true` in frontmatter)

## Inline Images

![[paper-texture-top-view-2.jpg|Ancient manuscript fragment]]

Images support **both Obsidian and standard Markdown syntax**:
- **Obsidian wikilinks**: `![[filename.png|caption]]` 
- **Markdown links**: `![alt text](path/to/image.png)`

They float to the right with a caption beneath, using the `lore-figure` component.

![Standard markdown image](paper-texture-top-view-2.jpg)

If no caption is provided, the filename (with underscores/hyphens converted to spaces) is used automatically.

### Image Positioning

Images flow naturally with the text, wrapping content around them. Multiple images in sequence will stack vertically on the right side.

## Feature Boxes

Feature boxes are created using the `**Feature Name:** description text` pattern. They accumulate and render as a 2-column grid:

**Versatility:** Feature boxes can contain any amount of text and support **bold**, *italic*, and _emphasis_ through inline markdown.

**Auto-Grid Layout:** When two or more features are defined consecutively, they automatically render as a responsive 2-column grid that collapses to single-column on mobile.

**Flexible Content:** Feature descriptions can be short or long. The grid layout adjusts to accommodate varying content lengths while maintaining visual balance.

**Visual Hierarchy:** Each feature has a prominent name in Cinzel font with the description below in EB Garamond, matching the overall design system.

## Jump Navigation

When `jump_nav: true` is set in the frontmatter, a navigation bar is auto-generated from all H2 and H3 headers in the document.

### Benefits

The jump nav provides:
- Quick access to sections in long documents
- Visual hierarchy (H3 headers are indented)
- Smooth scroll behavior
- Sticky positioning at the top of the content area

### Implementation

Headers automatically generate anchors using slugified versions of their text. The jump nav appears above the body content when enabled.

## Lists and Callouts

Standard markdown features also work:

Consider these examples:
- Unordered lists using `- ` or `* ` markers
- Support for mixed content (text before list items)
- Nested content within list items

> **Important Note:** Callouts use the `> ` markdown syntax and render with special styling to stand out from regular content.

## Combining Components

All three components can be used together in the same document:

![[paper-texture-top-view-2.jpg|Combined demo]]

**Component Synergy:** Images, features, and navigation work together to create rich, navigable content pages.

**Design Consistency:** All components use the same design language with parchment backgrounds, gold accents, and classic serif typography.

This creates a cohesive visual experience across all category pages.
