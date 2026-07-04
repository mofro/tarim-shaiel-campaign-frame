# LK Bridge — Obsidian vault ↔ LegendKeeper

Bidirectional conversion between the Tarim-Shaiel vault (Schema C Markdown)
and LegendKeeper import/export JSON. Supersedes `utilities/legendkeeper-pipeline/`
for prose pages (that pipeline remains authoritative for timelines only).

Spec and findings log: [GH #213](https://github.com/mofro/tarim-shaiel-campaign-frame/issues/213).
Format provenance: [schemas/SOURCE.md](schemas/SOURCE.md).

## Status: interim (no LK API)

LK has no public API. Imports always create new resources (IDs are minted per
import; they are stable database keys thereafter — they survive rewrites and
renames, proven 2026-07-03). Until the API ships:

- **The LK project is a disposable build artifact** — like `docs/`. Resync =
  delete vault-managed resources in the LK UI → re-import → `manifest.py build`
  on the fresh re-export.
- Hand-edits inside LK are lost on resync unless captured first with
  `from_lk.py` and merged into the vault manually. **The vault is the single
  source of truth.**

## Tools

| Tool | Purpose |
|---|---|
| `to_lk.py` | Vault files/directories → LK import file (`.json` / `.lk`) |
| `from_lk.py` | LK export → Schema C Markdown (scratch dir only — refuses vault content roots) |
| `validate_lk.py` | Offline validation: envelope schema + LK-dialect content schema + semantic checks |
| `manifest.py` | Capture real LK resource IDs from a re-export into `lk_manifest.json` |
| `lk_schema.py` | LK JSON builders (library) |
| `md_to_pm.py` / `pm_to_md.py` | Markdown ↔ ProseMirror converters (library) |
| `generate_stub_test.py` | Minimal 3-resource stub for importer probing (legacy shape, uses `lk_schema`) |

```bash
# full narrative+world GM mirror
python utilities/lk-bridge/to_lk.py narrative world --audience gm --lk \
    -o utilities/lk-bridge/roundtrip/full-gm.json

# arbitrary files, player-safe
python utilities/lk-bridge/to_lk.py narrative/lore/The\ Roads.md \
    --audience player -o utilities/lk-bridge/roundtrip/roads.json

python utilities/lk-bridge/validate_lk.py utilities/lk-bridge/roundtrip/full-gm.json
python utilities/lk-bridge/from_lk.py <lk-reexport.json> --out utilities/lk-bridge/roundtrip/post-lk/
python utilities/lk-bridge/manifest.py build <lk-reexport.json>
```

## Secrets mapping (vault ↔ LK)

`--audience player` (public-HTML parity) vs `--audience gm` (full mirror,
default). The round-trip discriminator is `parameters.extensionTitle` on
LK's `block-secret` extension.

| Vault construct | player | gm (→ LK) | reverse (LK → vault) |
|---|---|---|---|
| `visibility: gm_secrets` file | excluded | resource `isHidden: true` + tag `gm-secret` | hidden/tagged → `visibility: gm_secrets` |
| Tier 1 `{gm:text}` | `██████` literal | `{gm:text}` literal passthrough | verbatim |
| Tier 2 `> [!gm-only id=x]` | stripped | `block-secret` title `GM` / `GM id=x` | title `GM*` → callout, id restored |
| Tier 3 `![[gm_secrets/f]]` | stripped | `block-secret` title `GM embed: <path>`, **marker only — never inlined** | title → `![[path]]`, inner content discarded |
| `%%…%%` | stripped | `block-secret` title `GM comment` | title → `%%…%%` |
| LK-authored secret (title `Secret` etc.) | — | — | `> [!gm-only]` |

Round-trip safety: Tier 3 is marker-only and Tier 1 is passthrough, so
vault→LK(gm)→vault reconstructs the exact syntax the HTML pipeline parses.
A stray unpaired `%%` in prose swallows text to the next `%%` — same behavior
as Obsidian itself.

## Scope rules (directory mode)

- Non-`.md` files: never picked up
- `Index.md` / `_category.md`: skipped (navigation + dataview)
- `world/abilities/`, `world/classes/`: default-excluded SRD reference data
  (`--include-all` to include)
- Old-schema (pre-Schema-C) files: tolerated; counted in the run summary

## Quirk verdicts (whole-vault census 2026-07-03, GH #213)

| Construct | Handling |
|---|---|
| ```` ```leaflet ```` (35 location files) | skip + warning — future: LK native `map` doc type |
| audio embeds | italic `♪ label` + warning (CDN upload is API-gated) |
| image embeds `![[x.png]]` | skip + warning (same) — external `![](url)` maps to media |
| ```` ```dataview ```` / ```` ```mermaid ```` | skip + warning |
| other fences (incl. ```` ```daggerheart ````) | code-marked paragraphs (LK block-code node unverified) |
| `[[x#heading]]` | mention to page, anchor dropped + warning |
| section/note transclusions (non-GM) | mention link, not inlined |
| `==highlight==` / `~~strike~~` | em / plain + warning (LK marks: strong·em·code·link only) |
| nested sub-lists | flatten to sibling items (known limitation) |

## Manual round-trip protocol

1. Generate + validate (see commands above); import the **small fixture export
   first**, then the full one, into a **scratch LK project**
2. In LK verify: no import hang; tree structure; mentions click through;
   secret blocks render collapsed; hidden resources arrive hidden (**open
   question — isHidden import preservation**)
3. Re-export from LK → save under `roundtrip/`; run `from_lk.py` on it and
   diff against sources; grep the re-export for `extensionTitle` values
   (**open question — custom title survival**)
4. `manifest.py build <re-export>` → captures real IDs
5. **Retarget probe**: `to_lk.py` a single new page containing a `mention`
   whose id is a real ID from the manifest; import into the same project;
   click the link (**open question — cross-import mention retargeting**)
6. Author a code block in LK, re-export, capture the node shape
   (**open question — block-level code node**)

Record all four verdicts in GH #213.
