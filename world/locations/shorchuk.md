---
created: 2025-12-13
description: A waypoint on the northern route where merchants rest before mountain
  passages.
elevation: 1050
factions:
- Route Keepers
fantasy_name: Shorchuk
historical_basis: Tarim Basin - Northern route waypoint
is_private: false
last_updated: 2025-12-13
location:
- 41.525095839817354
- 82.07693159580232
mapmarker: route-node
name: Shorchuk
resources:
- oasis goods
tags:
- player-visible
- campaign-arc-northern-route
- type-route-node
type: route-node
---

```leaflet
id: location-shorchuk
coordinates: [[world/locations/shorchuk]]
defaultZoom: 10
minZoom: 4.5
maxZoom: 18
height: 500px
osmLayer: false
tileServer:
  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}|Satellite (No Labels)

tileOverlay:
  - https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png|Labels

geojson:
  - [[world/tarim-shaiel-routes.geojson]]|Routes
  - [[world/tarim-shaiel-locations.geojson]]|Locations

```

# Shorchuk

A waypoint on the northern route approaching the western mountain passes. Merchants gather supplies and information here before the dangerous sections ahead.

## Location Significance

Between Kucha and Aksu on the northern corridor. A transition point between oasis commerce and mountain passage preparation.

## Resources

Water, local provisions, guide services.

## Character

A modest but organized waypoint with experienced handlers of mountain caravans.

# Location Section Snippets

**Modular snippets for location sections. Copy what you need.**

---

## Public Sections

### Geography
```markdown
## Geography

Physical characteristics, terrain, climate, notable features.
```

### Economy
```markdown
## Economy

Trade, resources, economic activity, markets.
```

### Key Features
```markdown
## Key Features

Distinctive landmarks, architecture, cultural elements.
```

### Factions
```markdown
## Factions

Major groups, organizations, or power structures present.
```

### Resources
```markdown
## Resources

What this location produces, exports, or is known for.
```

### Cultural Notes
```markdown
## Cultural Notes

Customs, traditions, social structure, daily life.
```

### Historical Basis
```markdown
## Historical Basis

**Real-world inspiration** – Historical context and cultural influences.
```

### Waypoint Status
```markdown
## Waypoint Status

Travel information, connections to other locations, journey details.
```

---

## GM Sections

### Narrative Significance
```markdown
## Narrative Significance

Why this location matters to the campaign narrative. How it connects to themes and arcs.
```

### Key Narrative Elements
```markdown
## Key Narrative Elements

Core story beats, dramatic moments, thematic connections.
```

### Hidden Secrets
```markdown
## Hidden Secrets

Information players don't know yet. Mysteries to be uncovered.
```

### Plot Hooks
```markdown
## Plot Hooks

Potential adventures, mysteries, or complications. Story threads to explore.
```

### DM Notes
```markdown
## DM Notes

Mechanics, encounters, prep notes. Session-specific information.
```

### World-Building Context
```markdown
## World-Building Context

Meta-narrative design notes. How this location serves the larger campaign.
```

---

## Usage

**Quick Add to File:**
1. Position cursor where you want section
2. Copy snippet above
3. Paste and fill in content

**Obsidian Hotkeys:**
Set up templates in Obsidian settings for even faster insertion.

---

See [[../reference/routing-rules|Routing Rules]] for how sections are processed.