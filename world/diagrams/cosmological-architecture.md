---
title: Cosmological Architecture Diagram
project: TTRPG_Tarim_Shaiel
type: diagram
diagram_type: cosmological-layers
status: draft
created: 2026-03-10
last_updated: 2026-03-10
source: narrative/STORY_ARC_SYNTHESIS.md, world/factions/Index.md, world/concepts/Index.md
---

# Cosmological Architecture

> Three layers of reality, the forces that inhabit each, and the mechanisms connecting them. Decisions still pending are marked ⚠️.

```mermaid
graph TD

    subgraph CELESTIAL["✨  CELESTIAL LAYER  —  Hero Heaven / Celestial Peak"]
        CC["⚠️ Celestial Court<br/>(issues charges; nature TBD)"]
        CP["Celestial Peak<br/>/ Hero Heaven<br/>(sanctuary + pressure regulator)"]
        HEROES["The Heroes<br/>(returned after 1,000 years;<br/>carry celestial memory)"]
        CC -->|"issues charge to"| HEROES
        CP -->|"reward"| HEROES
    end

    subgraph MORTAL["🌍  MORTAL WORLD  —  The Silk Road"]
        THRESHOLD["The Threshold<br/>(access point + pressure<br/>regulator in the ecosystem)"]
        GREAT_WALL["The Great Wall<br/>(cosmological infrastructure;<br/>Elven-maintained)"]
        ELV["Elven Highland Enclaves<br/>(cosmologically literate;<br/>withdrawn by design)"]
        ELV -->|"maintains"| GREAT_WALL
        ELV -.->|"understands / dreads"| THRESHOLD
    end

    subgraph WARRENS["🌀  WARREN LAYER  —  The Circulatory System"]
        WN["The Warrens & Holds<br/>(channels + containers;<br/>mythic ecosystem's<br/>circulatory system)"]
        NECRO["Necromantic Energy<br/>(anti-cycle force;<br/>inverts natural Warren flow)"]
        LICH["Lich Cadre + Lich-Legion<br/>(exploit the inversion;<br/>100,000+ undead = ecosystem strain)"]
        WIZ["The Wizard<br/>(commands the Cadre;<br/>targets the Threshold)"]
        WN -->|"natural flow<br/>inverted by"| NECRO
        NECRO -->|"exploited by"| LICH
        WIZ -->|"commands"| LICH
    end

    subgraph BENEATH["🔴  BENEATH EVERYTHING  —  Pre-Cosmic"]
        HB["The Held Breath<br/>(dormant liminal consciousnesses;<br/>not awake; not negotiable;<br/>horror is their weight)"]
        ELDER["⚠️ Elder Gods<br/>(speculative; may be<br/>the Held Breath's architects;<br/>may predate the ecosystem)"]
        HB -.->|"may be shaped<br/>or preceded by"| ELDER
    end

    %% ── CROSS-LAYER CONNECTIONS ──────────────────────────────────────

    HEROES -->|"seek / are drawn to"| THRESHOLD
    THRESHOLD <-->|"access point to"| CP

    THRESHOLD -->|"pressure regulator<br/>embedded in"| WN
    GREAT_WALL -.->|"structural element<br/>of the ecosystem?"| WN

    WIZ -->|"targets"| THRESHOLD
    LICH -->|"assault force<br/>against"| THRESHOLD

    WN -.->|"contains /<br/>suppresses"| HB

    %% ── MECHANISMS ───────────────────────────────────────────────────

    GAES["The Gaes<br/>(Wizard exploited<br/>Fallen Teammate's sacrifice;<br/>expulsion mechanism)"]
    BINDING["Binding Magic<br/>(Empire's enslaving tool;<br/>taps Warren channels parasitically)"]

    GAES -->|"expelled Heroes<br/>from"| CP
    GAES -->|"links Heroes<br/>to"| THRESHOLD
    BINDING -.->|"parasitic tap<br/>on"| WN

    %% ── STYLES ───────────────────────────────────────────────────────
    classDef celestial fill:#1a237e,color:#fff,stroke:#7986cb
    classDef mortal fill:#1b5e20,color:#fff,stroke:#81c784
    classDef warren fill:#4a148c,color:#fff,stroke:#ce93d8
    classDef beneath fill:#7c1d1d,color:#fff,stroke:#ef9a9a
    classDef mechanism fill:#4e342e,color:#fff,stroke:#a1887f,stroke-dasharray:4 2
    classDef pending fill:#455a64,color:#fff,stroke:#90a4ae,stroke-dasharray:6 3

    class CC,CP,HEROES celestial
    class THRESHOLD,GREAT_WALL,ELV mortal
    class WN,NECRO,LICH,WIZ warren
    class HB beneath
    class GAES,BINDING mechanism
    class ELDER,CC pending
```

---

## Layer Summary

| Layer | What Lives Here | Threat Direction |
|---|---|---|
| Celestial | Hero Heaven, Celestial Court, The Heroes | Threatened from below (Threshold breach = immediate break) |
| Mortal | Silk Road civilisations, Elven Highlands, The Threshold | Squeezed from both sides |
| Warrens | Magical infrastructure, necromantic inversion, Lich-Legion | Inverted from within; straining outward |
| Pre-cosmic | The Held Breath | Inert unless disturbed; irreversible if woken |

## Open Design Questions

- ⚠️ **Celestial Court** — governing body, impersonal accounting system, or distributed ecosystem will? See [[../../TODO]] → Divine & Cosmic Factions
- ⚠️ **Elder Gods** — same as the Elder Civilization? Architects of the ecosystem? Or something else entirely?
- ⚠️ **Warren Intelligences** — do the Warrens have agenda, or are they pure infrastructure? Decision affects Act 3

## Sources

- Full cosmological decisions → [[../../narrative/STORY_ARC_SYNTHESIS]]
- Concepts index → [[../concepts/Index]]
- Factions index (divine section) → [[../factions/Index]]
