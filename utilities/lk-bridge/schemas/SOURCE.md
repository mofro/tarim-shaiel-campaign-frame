# Schema provenance

## `lk-envelope.schema.json` (hand-written)

Derived from real LK exports:
- `Welcome to Tarim Shaiel.json` (May 2026, 15 resources) — original baseline
- `Tarim-Shaiel Library.json` (2026-07-03, 50 resources, **post-rewrite**) — current reference

2026-07-03 baseline diff verdict: envelope schema identical across the rewrite;
additive changes only (`board`/`map` document types, optional `map` document
field). The `hash` field uses an unknown LK-internal algorithm — twelve
serialization variants failed to reproduce it — and LK does **not** verify it
on import (proven: an import with a "wrong" hash was accepted, May 2026,
re-confirmed against the rewrite's exports). Our exports carry a
self-consistency SHA-256 instead.

## `lk-dialect.schema.json` (hand-written — NOT vanilla ADF)

LegendKeeper's editor is the open-source Atlaskit editor (Atlassian's
ProseMirror distribution); its document model descends from ADF (Atlassian
Document Format). Evidence: 24/26 node types match ADF definitions, and link
marks carry `__confluenceMetadata` — an implementation-private field defined
in `@atlaskit/adf-schema`'s `link.js` (`OPTIONAL_ATTRS`). LK has never
documented this; it is artifact-proven.

**Why we don't validate against Atlassian's published ADF schema:** it rejects
14/14 real LK documents. Measured divergences (2026-07-03):

1. `strong`/`em` marks carry `"attrs": {}` (ADF forbids attrs on those marks)
2. GM sections use `bodiedExtension` with **empty** `extensionKey`/`extensionType`
   (ADF requires non-empty); real LK data contains `layout: "default "` with a
   trailing space (fails ADF's enum)
3. `mention.attrs.documentId` — LK addition, ADF forbids unknown attrs
4. `media` with empty `id`/`collection` plus `__external`/`url`/`__fileMimeType`
5. `blockquote` may contain `heading`; `panel` may contain `heading`
   (both disallowed by published ADF)

The dialect schema encodes the vocabulary LK actually emits, measured from the
reference exports above. Marks observed in real content: `strong`, `em`,
`code`, `link` only. Block-level code node: **unverified** (LK tutorial content
shows only the inline `code` mark) — manual checklist item, GH #213.

Vanilla ADF schema reference (not vendored — 74 KB, draft-04, rejected as
validator): `https://unpkg.com/@atlaskit/adf-schema@latest/dist/json-schema/v1/full.json`
