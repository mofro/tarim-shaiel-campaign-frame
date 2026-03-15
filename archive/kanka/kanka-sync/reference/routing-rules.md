---
title: Content Routing Rules
type: reference
category: kanka-sync
tags: [kanka, routing, content-splitting]
parent: "[[utilities/kanka-sync/INDEX|Kanka Sync Documentation]]"
---

# Content Routing Rules

**How your Obsidian content is routed to Kanka entities, attributes, and posts.**

---

## Overview

The sync script analyzes your markdown files and routes content based on:
1. **Frontmatter fields** → Kanka attributes
2. **Section headers** → Entry (public) or Posts (GM)
3. **Unknown content** → Defaults to GM (safe)

---

## Section Routing

### **Public Sections → Main Entry**

These sections go in the main entity `entry` field (players can see):

```markdown
## Geography
## Economy
## Key Features
## Factions
## Factions Present
## Resources
## Waypoint Status
## Cultural Notes
## Historical Basis
## Historical Foundation
```

**Result:** Converted to HTML and placed in entity's Overview tab.

---

### **GM Sections → Separate Posts**

These sections become individual admin-only posts:

| Markdown Section | Post Name | Visibility |
|------------------|-----------|------------|
| `## Narrative Significance` | "Narrative Significance" | admin-only |
| `## Key Narrative Elements` | "Key Narrative Elements" | admin-only |
| `## Hidden Secrets` | "Hidden Secrets" | admin-only |
| `## Plot Hooks` | "Plot Hooks" | admin-only |
| `## DM Notes` | "DM Notes" | admin-only |
| `## World-Building Context` | "World-Building Context" | admin-only |

**Result:** Each becomes a separate post on the entity, visible only to GMs.

---

### **Unknown Sections → Default to GM**

Any section header NOT in the lists above defaults to GM (conservative/safe).

**Example:**
```markdown
## Trade Routes
Connects to Bukhara.
```

**Result:** Goes into "DM Notes" post (hidden from players).

**To make it public:** Add `"## Trade Routes"` to `PUBLIC_SECTION_MARKERS` in script.

---

## Content Processing

### **What Gets Stripped**

**Removed entirely:**
- ` ```leaflet` code blocks
- ` ```dataview` queries
- `%% Obsidian comments %%`
- `<!-- HTML comments -->`
- `![[image embeds]]`

**Converted:**
- `[[wiki links]]` → Plain text ("wiki links")
- Markdown → HTML

---

## Frontmatter Routing

See [[field-mappings|Field Mappings]] for complete details.

### **Quick Reference**

| Frontmatter Field | Destination |
|-------------------|-------------|
| `name` | Entity name |
| `type` | Entity type |
| `is_private` | Entity privacy |
| `elevation` | Attribute: "Elevation" |
| `resources` | Attribute: "Resources" |
| `factions` | Attribute: "Primary Factions" (with @mentions) |
| `location` (coords) | Attribute: "Coordinates" |
| `historical_basis` | **IGNORED** (use body section instead) |

---

## Example: Full Routing

### **Your Obsidian File:**

```yaml
---
name: Samarkand
type: city
is_private: false
kanka_type: location
elevation: 700
resources: ["silk", "paper"]
factions: ["Sogdian Merchants Guild"]
---

# Samarkand

A jeweled city where East meets West.

## Geography
Monumental architecture surrounded by mountains.

## Economy
Famous for textile production.

## Historical Basis
**Sogdania** – Originally Zoroastrian, converted to Islam.

## Hidden Secrets
The Wizard has an agent in the merchant quarter.

## Plot Hooks
Investigate the corrupted jade supply chain.
```

---

### **After Sync → Kanka Result:**

**Entity (Location #1970046):**
- Name: "Samarkand"
- Type: "city"
- is_private: false
- Entry (HTML):
  ```html
  <h1>Samarkand</h1>
  <p>A jeweled city where East meets West.</p>
  <h2>Geography</h2>
  <p>Monumental architecture surrounded by mountains.</p>
  <h2>Economy</h2>
  <p>Famous for textile production.</p>
  <h2>Historical Basis</h2>
  <p><strong>Sogdania</strong> – Originally Zoroastrian, converted to Islam.</p>
  ```

**Attributes:**
- Elevation: 700 (number)
- Resources: "silk, paper" (text)
- Primary Factions: "@Sogdian_Merchants_Guild" (text, clickable if entity exists)

**Posts:**
1. **"Hidden Secrets"** (visibility: admin)
   ```html
   <h2>Hidden Secrets</h2>
   <p>The Wizard has an agent in the merchant quarter.</p>
   ```

2. **"Plot Hooks"** (visibility: admin)
   ```html
   <h2>Plot Hooks</h2>
   <p>Investigate the corrupted jade supply chain.</p>
   ```

---

## Player View vs. GM View

### **Player Sees:**
- Overview tab: Public content only
- Attributes tab: All attributes (unless marked private)
- Posts tab: Empty (no GM posts visible)

### **GM Sees:**
- Overview tab: Same as players
- Attributes tab: All attributes including private ones
- Posts tab: All GM posts ("Hidden Secrets", "Plot Hooks", etc.)

**Test this:** Use Kanka's "View As Player" feature.

---

## Progressive Revelation

Because each GM section is a separate post, you can reveal secrets progressively:

1. Create entity with GM posts (all admin-only)
2. During play, players discover a secret
3. In Kanka UI: Edit "Hidden Secrets" post
4. Change visibility: `admin` → `all`
5. Save

**Now players see that specific post!**

---

## Customizing Routing

### **Add a Public Section**

Edit `kanka-sync.py`:

```python
PUBLIC_SECTION_MARKERS = [
    '## Geography',
    '## Economy',
    # ... existing ...
    '## My Custom Section',  # ← Add this
]
```

### **Add a GM Section**

```python
GM_SECTION_MARKERS = {
    '## Narrative Significance': 'Narrative Significance',
    # ... existing ...
    '## My Secret Section': 'My Secret Notes',  # ← Add this
}
```

---

## Decision Tree

```
Markdown Section Header
│
├─ Is it in PUBLIC_SECTION_MARKERS?
│  └─ Yes → Route to main entry (public)
│
├─ Is it in GM_SECTION_MARKERS?
│  └─ Yes → Create separate post (admin-only)
│
└─ Unknown section
   └─ Default to GM post "DM Notes" (safe)
```

---

## Best Practices

### **For Public Content:**
- Use standard section headers (Geography, Economy, etc.)
- Write for player audience
- Avoid spoilers

### **For GM Content:**
- Use dedicated GM sections
- One section per type of secret/note
- Enables progressive revelation

### **For Unknown Sections:**
- They default to GM (safe)
- Add to PUBLIC_SECTION_MARKERS if player-facing
- Leave as GM if uncertain

---

## Related Documentation

- [[field-mappings|Field Mappings]] - Complete frontmatter → attribute mappings
- [[../guides/quickstart|Quickstart Guide]] - Get started syncing
- [[../INDEX|Documentation Index]] - All docs

---

[[INDEX|← Back to Documentation Index]]
