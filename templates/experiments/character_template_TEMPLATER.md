<%*
// Get all available options from SRD directories
const classFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith("references/daggerheart-srd/classes/"));
const classList = classFiles.map(f => f.basename).sort();

const subclassFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith("references/daggerheart-srd/subclasses/"));
const subclassList = subclassFiles.map(f => f.basename).sort();

const ancestryFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith("references/daggerheart-srd/ancestries/"));
const ancestryList = ancestryFiles.map(f => f.basename).sort();

const communityFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith("references/daggerheart-srd/communities/"));
const communityList = communityFiles.map(f => f.basename).sort();

const archetypeFiles = app.vault.getMarkdownFiles().filter(f => f.path.startsWith("mechanics/archetypes/") && f.basename !== "INDEX");
const archetypeList = archetypeFiles.map(f => f.basename).sort();

// Prompt user for selections
const chosenClass = await tp.system.suggester(classList, classList, false, "Select Daggerheart Class");
const chosenSubclass = await tp.system.suggester(subclassList, subclassList, false, "Select Subclass");
const chosenAncestry = await tp.system.suggester(ancestryList, ancestryList, false, "Select Ancestry");
const chosenCommunity = await tp.system.suggester(communityList, communityList, false, "Select Community");
const chosenArchetype = await tp.system.suggester(archetypeList, archetypeList, false, "Select Tarim-Shaiel Archetype");

const characterName = await tp.system.prompt("Character Name");
const playerName = await tp.system.prompt("Player Name (leave empty for NPC)", "", false);
-%>
---
name: "<% characterName %>"
kanka_type: character
type: "<% playerName ? 'pc' : 'npc' %>"
is_private: false
tags: [<% playerName ? 'pc' : 'npc' %>]
player: "<% playerName %>"
status: active

# Daggerheart Standard
daggerheart_class: "<% chosenClass %>"
subclass: "<% chosenSubclass %>"
ancestry: "<% chosenAncestry %>"
community: "<% chosenCommunity %>"
level: 1
evasion: 10
armor_score: 0
major_thresholds: "7/14"
minor_thresholds: "3/6"
hope: 2
max_hope: 5

# Traits
agility: 0
strength: 0
finesse: 0
instinct: 0
presence: 0
knowledge: 0

# Tarim-Shaiel Extensions
hero_heaven_archetype: "<% chosenArchetype %>"
charm_tier: 1
r_h_k_resist: 0
r_h_k_hunger: 0
r_h_k_know: 0
---

# <% characterName %>

## Character Concept

[Brief character description, personality, defining traits]

## Daggerheart Foundation

**Class:** [[references/daggerheart-srd/classes/<% chosenClass %>|<% chosenClass %>]]
**Subclass:** [[references/daggerheart-srd/subclasses/<% chosenSubclass %>|<% chosenSubclass %>]]
**Ancestry:** [[references/daggerheart-srd/ancestries/<% chosenAncestry %>|<% chosenAncestry %>]]
**Community:** [[references/daggerheart-srd/communities/<% chosenCommunity %>|<% chosenCommunity %>]]

### Traits

| Agility | Strength | Finesse | Instinct | Presence | Knowledge |
|:-------:|:--------:|:-------:|:--------:|:--------:|:---------:|
| +0 | +0 | +0 | +0 | +0 | +0 |

### Defenses

| Evasion | Armor | Major Thresholds | Minor Thresholds |
|:-------:|:-----:|:----------------:|:----------------:|
| 10 | 0 | 7/14 | 3/6 |

## Tarim-Shaiel Archetype

**Archetype:** [[mechanics/archetypes/<% chosenArchetype %>|<% chosenArchetype %>]]

### R/H/K Progression

| Resist | Hunger | Know |
|:------:|:------:|:----:|
| 0 | 0 | 0 |

### Active Charms

[List of unlocked charms with links to charm entries]

## Background

### Origin Story
[Character's history before the campaign]

### Current Motivation
[What drives them now]

### Unresolved Tension
[Internal or external conflict to explore]

## Relationships

[Connections to other PCs, NPCs, factions]

## Equipment

### Signature Tool
[Primary weapon or item, potentially a sentient weapon]

### Inventory
[Other significant possessions, gold, consumables]

## Session Notes

### Key Moments
[Memorable events from play]

### Growth
[Character development, lessons learned]

## GM Notes

[Private notes about this character's arc, secrets, connections]
