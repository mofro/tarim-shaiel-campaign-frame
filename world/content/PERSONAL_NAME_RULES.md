---
title: Personal Name Rules by Region
project: TTRPG_Tarim_Shaiel
domain: world
doc_type: design_decision
content_type: reference
visibility: gm_secrets
status: draft
created: 2026-11-06
last_updated: 2026-11-06
tags: [naming, regions, "#384"]
---

# Personal Name Rules by Region

*Draft for GM review (#384). Visibility stays `gm_secrets` by GM decision. Nothing here is locked. Example names are illustrations of each pattern, not canon NPCs. Sacred self-names stay in `narrative/gm_secrets/ANCESTRY_SECRET_NAMES.md` and are not repeated here.*

## Intent

A name should tell a player three things at a glance: where this person is from, what people they belong to, and how the speaker regards them. Region sets the **sound and the shape** of a name. Ancestry **bends** it. The Persian register is the shared trade language, so any name can be heard in it, and most are spoken in it by strangers.

The rules feed the settlement passes (child C): each settlement takes its region's pool, applies its ancestry mix, and draws.

## Anatomy of a name

Every personal name is **given name + byname**. The byname type varies by region.

| Byname type | What it is | Where it dominates |
|---|---|---|
| Patronymic | "son/daughter of" a parent's given name | Steppe, Central Asian Hubs |
| Place byname | Origin town or oasis | Tarim Basin, Mountain Passes, Hubs |
| Trade byname | Craft, load carried, route worked | Eastern Gateway, Tarim Basin |
| Clan name | Kin group, passed on | Steppe, Tulpar anywhere |
| House name | Family line, fixed | Eastern Terminus |

Families that settle keep one fixed surname-like byname; travellers pick up new ones. A person may carry two bynames in one introduction: the formal one and the one used by friends.

## Ancestry modifiers (apply on top of any region)

| Ancestry | Modifier |
|---|---|
| Human | Takes the regional pattern unchanged. |
| Kuhban (Dwarf) | Regional given name, plus a byname built as a compound with a literal meaning (stone-reader, third-gate), in the Slavic-compound manner `CULTURAL_FRAMEWORK` sets for Dwarvish. |
| Serenvar (Elf) | Long, melodic, multi-syllable given names; tonal rendering. A trade name is used among other peoples; the older register is kept for sacred sites (see Elven Highlands). |
| Tulpar (Orc) | Guttural given name (K, GH, SH, glottal stops) plus clan name. Clan outranks ancestry: a person of any ancestry in a Tulpar clan takes the clan name. A carried-token byname is added with age ("You are what you carry"). |
| Vaghri (Katari) | Often a single name; a second is given only to those who earn one. No false modesty in the byname. |
| Jivar (Goblin) | Short given name; the byname is a market or ear-sign nickname others coined. |
| Rahban (Halfling) | Warm given name plus a hearth or home-road byname. |
| Kalan (Giant) | Turkic or Mongolian forms; nicknames from the body or deed (Cyclops: Tekgöz). |
| Naga-Kin | Family name carries the breath line, known to those who can read it. |
| Others (Vanara, Div-Born, Gavar, Tadbir, Pari-Kin, Khavar, Galapa, Ribbet, Faerie) | No rule by decision (2026-11-06): they take the regional pattern unchanged. |

## Region rules

### Eastern Terminus (imperial heartland, Chang'an side)

- **Register:** Chinese-derived, two-syllable given names, one-syllable house name placed first or last by speaker (formal: house first).
- **Byname type:** house name; courtesy names for scholars.
- **Examples (illustrative):** Lin Zhaohe, Du Meiyun, Han Qiubai, Wei Sanlang.
- **Notes:** Imperial offices appear as titles after the name. Foreigners are given a Chinese-sounding rendering by officials, which they keep or refuse.

### Eastern Gateway (includes Elven Highlands)

- **Register:** Chinese-derived given names softened by trade-town speech; frequent Persian loan names among merchants.
- **Byname type:** trade byname (Lamp-Seller, Gate-Warden) plus the family house name.
- **Examples:** Dong Yueshan, Fa Lienhua, Zhao the Gate-Warden, Mahan of the Lamps.
- **Elven Highlands (sub-region):** Serenvar take the Elven register above. Sacred sites and Elven officials are named in it; the Eastern Gateway Council uses the common form for dealings with outsiders.

### Tarim Basin

- **Register:** Persian given names with Uighur-Turkic and Tocharian-flavoured place forms.
- **Byname type:** oasis of origin (of Khotan, from Kucha) and trade byname.
- **Examples:** Farrokh of Khotan, Dilshad Kuchari, Bahar the Salt-Broker, Yarkan Beg.
- **Notes:** No one tribal pattern. A speaker who gives a place byname is signalling where their credit is good.

### Mountain Passes

- **Register:** Persian and Tibetan-flavoured, short given names, heavy use of titles.
- **Byname type:** place byname (the pass or valley), then the guild or toll-keeper title.
- **Examples:** Tashi of the Karakul, Gulnara Pamiri, Sher Dorje, Zarmin of the Third Pass.
- **Notes:** Kuhban concentration is highest here, so Dwarvish compound bynames are common and are the area's most recognisable naming feature.

### Central Asian Hubs (includes Transoxiana)

- **Register:** Persian is primary. Sogdian forms for the old merchant families, Turkic forms for newcomers.
- **Byname type:** patronymic (-zoda, -ugli, -zadeh) for families; place byname for traders.
- **Examples:** Anushirvan Rustamzoda, Gulbahor Bukharayi, Davlat ibn Murad, Shirin Khwarazmi.
- **Transoxiana (sub-region):** Inherits this pool unchanged. The river frontier adds only river-and-crossing bynames (of the Ford, Amu-man); no separate pool.
- **Dehdadi:** Draws from this pool, as a settlement of `central-asian-hubs`.

### Steppe Confederations

- **Register:** Turkic and Mongolian given names; guttural clan sounds near Tulpar clans.
- **Byname type:** clan name first, patronymic second; "son of" forms are used with strangers, clan with kin.
- **Examples:** Temirkhan of the Gokturk-Ash, Batu ibn Orkhan, Altan Oghul, Saran Tuvakh.
- **Notes:** The Tulpar clan rule applies here fully. Names announce allegiance before they announce the person.

## Quick draw guide (for child C settlement passes)

1. Read the settlement's `parent_region` (a missing value means the pass must assign one first).
2. Take the region's register and byname type.
3. Roll the settlement's ancestry mix; apply that ancestry's modifier.
4. Roughly one in four characters carries a second, informal byname.
5. For nested sub-regions, use the parent's pool; the sub-region adds only its listed byname flavour.
