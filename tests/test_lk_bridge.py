"""LK bridge test suite — lk_schema builders, md↔pm converters, round-trip.

Fixtures live in tests/fixtures/lk_bridge/. The offline round-trip test is the
executable form of the manual protocol's step 2 (GH #213).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
BRIDGE = REPO / 'utilities' / 'lk-bridge'
FIXTURES = Path(__file__).parent / 'fixtures' / 'lk_bridge'
sys.path.insert(0, str(BRIDGE))
sys.path.insert(0, str(REPO / 'utilities'))

import lk_schema as lk           # noqa: E402
import md_to_pm                  # noqa: E402
import pm_to_md                  # noqa: E402
from shared.frontmatter import parse_frontmatter, doc_type_of   # noqa: E402

FIXTURE_MD = FIXTURES / 'gm_constructs_fixture.md'


def _no_resolve(_target):
    return None


def _convert(body, audience):
    return md_to_pm.convert(body, audience=audience, resolve_link=_no_resolve,
                            source='test')


# ── lk_schema ────────────────────────────────────────────────────────────────

class TestLkSchema:
    def test_short_id_format_and_determinism(self):
        a, b = lk.short_id('narrative/foo.md'), lk.short_id('narrative/foo.md')
        assert a == b and len(a) == 8 and a.isalnum() and a == a.lower()
        assert lk.short_id('other') != a

    def test_envelope_self_consistency_hash(self):
        import hashlib
        env = lk.envelope([lk.resource('abcd1234', 'X', '', [lk.doc('d1', [lk.para('hi')])])])
        payload = {k: v for k, v in env.items() if k != 'hash'}
        expect = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert env['hash'] == expect
        assert env['resourceCount'] == 1

    def test_doc_presentation_never_null(self):
        d = lk.doc('d1', [])
        assert d['presentation'] == {'documentType': 'page'}

    def test_mention_carries_document_id(self):
        m = lk.mention('abcd1234', 'Page')
        assert m['attrs']['documentId'] == ''   # LK round-trip fidelity

    def test_write_lk_gzip_roundtrip(self, tmp_path):
        import gzip
        env = lk.envelope([])
        out = tmp_path / 'x.lk'
        lk.write_export(env, out, as_lk=True)
        assert json.loads(gzip.decompress(out.read_bytes())) == env


# ── frontmatter shim ─────────────────────────────────────────────────────────

class TestDocTypeOf:
    def test_schema_c_precedence(self):
        assert doc_type_of({'content_type': 'Timeline', 'type': 'lore'}) == 'timeline'

    def test_doc_type_fallback(self):
        assert doc_type_of({'doc_type': 'canon'}) == 'canon'

    def test_legacy_fallback(self):
        assert doc_type_of({'type': 'myth'}) == 'myth'

    def test_empty(self):
        assert doc_type_of({}) == ''


# ── md → pm: GM constructs by audience ───────────────────────────────────────

class TestGmMapping:
    @pytest.fixture(scope='class')
    def fixture_body(self):
        _, body = parse_frontmatter(FIXTURE_MD.read_text())
        return body

    def _secrets(self, nodes):
        found = []
        def walk(n):
            if isinstance(n, dict):
                if n.get('type') == 'bodiedExtension':
                    found.append(n)
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(nodes)
        return found

    def test_gm_mode_secret_blocks_and_titles(self, fixture_body):
        res = _convert(fixture_body, 'gm')
        titles = [s['attrs']['parameters']['extensionTitle']
                  for s in self._secrets(res.nodes)]
        assert 'GM' in titles                                   # Tier 2 no id
        assert 'GM id=fixture-1' in titles                      # Tier 2 with id
        assert any(t.startswith('GM embed: gm_secrets/') for t in titles)  # Tier 3
        assert 'GM comment' in titles                           # %% block

    def test_gm_mode_tier1_passthrough(self, fixture_body):
        res = _convert(fixture_body, 'gm')
        text = json.dumps(res.nodes)
        assert '{gm:Sylaveth Vorn}' in text
        assert '██████' not in text

    def test_player_mode_purity(self, fixture_body):
        res = _convert(fixture_body, 'player')
        text = json.dumps(res.nodes, ensure_ascii=False)
        assert 'Sylaveth' not in text
        assert 'block-secret' not in text
        assert 'gm_secrets' not in text
        assert 'containment failure' not in text                # Tier 2 stripped
        assert 'invisible to players' not in text               # %% stripped
        assert '██████' in text                                 # Tier 1 redaction bar

    def test_tier3_marker_only_never_inlines(self, fixture_body):
        res = _convert(fixture_body, 'gm')
        embeds = [s for s in self._secrets(res.nodes)
                  if s['attrs']['parameters']['extensionTitle'].startswith('GM embed')]
        assert embeds
        assert 'lives in vault file' in json.dumps(embeds[0]['content'])


# ── md → pm: general constructs ──────────────────────────────────────────────

class TestMdToPm:
    def test_heading_and_para(self):
        res = _convert('# Title\n\nBody text.', 'gm')
        assert res.nodes[0]['type'] == 'heading'
        assert res.nodes[1]['type'] == 'paragraph'

    def test_table(self):
        res = _convert('| A | B |\n|---|---|\n| 1 | 2 |', 'gm')
        tables = [n for n in res.nodes if n['type'] == 'table']
        assert len(tables) == 1
        assert tables[0]['content'][0]['content'][0]['type'] == 'tableHeader'

    def test_tasklist(self):
        res = _convert('- [ ] open\n- [x] done', 'gm')
        tl = res.nodes[0]
        assert tl['type'] == 'taskList'
        states = [i['attrs']['state'] for i in tl['content']]
        assert states == ['TODO', 'DONE']

    def test_skip_fences_warn(self):
        res = _convert('```leaflet\nid: map\n```', 'gm')
        assert res.nodes == []
        assert any('leaflet' in w for w in res.warnings)

    def test_callout_maps_to_panel(self):
        res = _convert('> [!tip]\n> Useful.', 'gm')
        assert res.nodes[0]['type'] == 'panel'
        assert res.nodes[0]['attrs']['panelType'] == 'success'

    def test_wikilink_resolution(self):
        def resolver(target):
            return ('abcd1234', 'Target Page') if target == 'target' else None
        res = md_to_pm.convert('See [[target|the page]] and [[missing]].',
                               audience='gm', resolve_link=resolver, source='t')
        para = res.nodes[0]['content']
        mentions = [n for n in para if n['type'] == 'mention']
        assert len(mentions) == 1
        assert mentions[0]['attrs']['alias'] == 'the page'
        assert any(n.get('text') == 'missing' for n in para)    # degraded


# ── pm → md and full offline round-trip ─────────────────────────────────────

class TestRoundTrip:
    def test_pm_to_md_reconstructs_gm_syntax(self):
        nodes = [
            lk.secret_block([lk.para('hidden fact')], 'GM id=x1'),
            lk.secret_block([lk.para('aside')], 'GM comment'),
            lk.secret_block([lk.para('marker')], 'GM embed: gm_secrets/deed.md'),
        ]
        md = pm_to_md.doc_to_markdown({'type': 'doc', 'content': nodes}, {})
        assert '> [!gm-only id=x1]' in md
        assert '%%\naside\n%%' in md
        assert '![[gm_secrets/deed]]' in md
        assert 'marker' not in md                # Tier 3 content discarded

    def test_fixture_survives_md_pm_md(self):
        _, body = parse_frontmatter(FIXTURE_MD.read_text())
        res = _convert(body, 'gm')
        md = pm_to_md.doc_to_markdown({'type': 'doc', 'content': res.nodes}, {})
        # the constructs the HTML pipeline parses must reconstruct exactly
        assert '{gm:Sylaveth Vorn}' in md
        assert '> [!gm-only id=fixture-1]' in md
        assert '![[gm_secrets/heroes_original_deed]]' in md
        assert '%%' in md
        assert '- [ ] open task' in md
        assert '- [x] done task' in md

    def test_cli_roundtrip_on_real_file(self, tmp_path):
        """to_lk → from_lk on the flagship real file; verify Tier 2 count survives."""
        src = REPO / 'narrative' / 'lore' / 'liberation_aftermath.md'
        if not src.exists():
            pytest.skip('vault content file not present')
        out_json = tmp_path / 'rt.json'
        r1 = subprocess.run(
            [sys.executable, str(BRIDGE / 'to_lk.py'), str(src),
             '--audience', 'gm', '-o', str(out_json),
             '--manifest', str(tmp_path / 'manifest.json')],
            capture_output=True, text=True)
        assert r1.returncode == 0, r1.stderr
        r2 = subprocess.run(
            [sys.executable, str(BRIDGE / 'from_lk.py'), str(out_json),
             '--out', str(tmp_path / 'back'),
             '--manifest', str(tmp_path / 'manifest.json')],
            capture_output=True, text=True)
        assert r2.returncode == 0, r2.stderr
        back = next((tmp_path / 'back').rglob('liberation_aftermath.md'))
        src_count = src.read_text().count('[!gm-only')
        assert back.read_text().count('[!gm-only') == src_count

    def test_from_lk_refuses_vault_content_out(self, tmp_path):
        r = subprocess.run(
            [sys.executable, str(BRIDGE / 'from_lk.py'), 'x.json',
             '--out', str(REPO / 'world' / 'nope')],
            capture_output=True, text=True)
        assert r.returncode != 0
        assert 'REFUSED' in (r.stdout + r.stderr)


# ── player-export purity at the CLI level ────────────────────────────────────

class TestPlayerExportCli:
    def test_player_export_excludes_gm_pages(self, tmp_path):
        fixture_gm = tmp_path / 'gm_secrets'
        fixture_gm.mkdir()
        (fixture_gm / 'secret_page.md').write_text(
            '---\ntitle: Secret\nvisibility: gm_secrets\n---\n# Hidden\n')
        pub = tmp_path / 'public_page.md'
        pub.write_text('---\ntitle: Pub\nvisibility: public\n---\n# Open {gm:X}\n')
        out = tmp_path / 'player.json'
        r = subprocess.run(
            [sys.executable, str(BRIDGE / 'to_lk.py'),
             str(pub), str(fixture_gm / 'secret_page.md'),
             '--audience', 'player', '-o', str(out),
             '--manifest', str(tmp_path / 'm.json')],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        data = json.loads(out.read_text())
        text = json.dumps(data, ensure_ascii=False)
        names = [res['name'] for res in data['resources']]
        assert 'Secret' not in names
        assert '{gm:' not in text
        assert '██████' in text
