---
title: Faction Relationship Web
project: TTRPG_Tarim_Shaiel
type: diagram
diagram_type: faction-web
status: draft
created: 2026-03-10
last_updated: 2026-03-10
source: world/factions/Index.md
---

# Faction Relationship Web

> **Legend:**
> `⚔ rivals` — bidirectional tension / competition
> `-.->` — hidden or covert influence (dotted = secret)
> `-->` — active opposition / pursuit
> Node colour = narrative weight: 🔴 very-high · 🔵 high · 🟢 medium-high · 🟠 medium

```mermaid
graph LR
    %% ── Very-High Weight ──────────────────────────────────────────────
    ELV["🔴 Elven Highland<br/>Enclaves"]
    LICH["🔴 Lich Cadre"]
    WIZ["🔴 The Wizard"]
    FT["🔴 Fallen Teammate<br/>(ghost / gaes)"]

    %% ── High Weight ───────────────────────────────────────────────────
    ORC_CONF["🔵 Orc Confederation<br/>(Samarkand)"]
    EGC["🔵 Eastern Gateway<br/>Council"]
    MERCH["🔵 Merchant Guilds<br/>(Multiethnic)"]
    EID["🔵 Eastern Imperial<br/>Dominion"]
    CHAIN["🔵 Chain-Breakers<br/>Order"]
    SCHOL["🔵 Scholar's Remnant"]

    %% ── Medium-High ───────────────────────────────────────────────────
    DWF_TAR["🟢 Dwarven Tarim<br/>Authority"]
    JCR["🟢 Jade Coast Realms"]

    %% ── Medium ────────────────────────────────────────────────────────
    HUMAN_REM["🟠 Human Imperial<br/>Remnants"]
    DWF_MTN["🟠 Dwarven Mountain<br/>Confederations"]
    HUM_TAR["🟠 Human Tarim<br/>Councils"]
    ORC_STL["🟠 Orc Steppe<br/>Confederations"]
    FREE["🟠 The Free Cities"]
    NINE["🟠 Peoples of the<br/>Nine Roads"]
    GNOME["🟠 Gnome Guilds"]

    %% ── RIVALS (open tensions) ────────────────────────────────────────
    ORC_CONF <-->|"⚔ rivals"| HUMAN_REM
    ORC_CONF <-->|"⚔ rivals"| ORC_STL
    DWF_MTN <-->|"⚔ rivals"| ORC_CONF
    DWF_MTN <-->|"⚔ rivals"| MERCH
    FREE <-->|"⚔ rivals"| NINE
    EID <-->|"⚔ rivals"| JCR

    %% ── HIDDEN CONTROL (covert influence) ────────────────────────────
    ELV -.->|"hidden broker"| EGC
    ELV -.->|"whispers in<br/>eastern courts"| EID
    ELV -.->|"whispers in<br/>eastern courts"| JCR
    DWF_TAR -.->|"open secret"| HUM_TAR
    WIZ -.->|"commands"| LICH

    %% ── ACTIVE OPPOSITION ─────────────────────────────────────────────
    CHAIN -->|"opposes"| WIZ
    CHAIN -->|"opposes"| HUMAN_REM
    WIZ -->|"hunts"| SCHOL
    WIZ -->|"hunts"| CHAIN
    LICH -->|"hunts"| SCHOL

    %% ── GAES / COSMOLOGICAL LINKS ─────────────────────────────────────
    FT -.->|"binds via gaes"| WIZ

    %% ── STYLES ────────────────────────────────────────────────────────
    classDef veryHigh fill:#7c1d1d,color:#fff,stroke:#c62828,stroke-width:2px
    classDef high fill:#1a237e,color:#fff,stroke:#283593,stroke-width:2px
    classDef medHigh fill:#1b5e20,color:#fff,stroke:#2e7d32,stroke-width:2px
    classDef medium fill:#bf360c,color:#fff,stroke:#e64a19,stroke-width:1px

    class ELV,LICH,WIZ,FT veryHigh
    class ORC_CONF,EGC,MERCH,EID,CHAIN,SCHOL high
    class DWF_TAR,JCR medHigh
    class HUMAN_REM,DWF_MTN,HUM_TAR,ORC_STL,FREE,NINE,GNOME medium
```

---

## Notes

- Pan-regional factions (Merchant Guilds, Free Cities, Peoples of the Nine Roads, Gnome Guilds) are not shown in regional groups — they operate across all nodes
- Steppe clan sub-factions (8 named clans) are folded under `Orc Steppe Confederations` until individually named
- Subcontinent factions (Lotus Thrones, Eternal Courts, Houses of the Monsoon, Clans of the Roof) omitted — `color` status, not yet in play
- Divine/Cosmic factions (Celestial Court, Held Breath, etc.) → see [[cosmological-architecture]]
- Source data: [[../factions/Index]]
