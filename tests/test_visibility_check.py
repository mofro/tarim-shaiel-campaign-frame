"""
Tests for the visibility flag checker and set command (#394): a lore page with no
`visibility:` or an unrecognised value is reported, and `set` changes that one line.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "shared"))

import visibility_check as vc

PAGE = "---\ntitle: Achal\nvisibility: gm_secrets\nlast_updated: 2026-10-26\n---\n\nProse.\n"


def _put(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# -- read_visibility -----------------------------------------------------------------

@pytest.mark.parametrize("value", vc.VALID)
def test_each_valid_value_reads_ok(value):
    assert vc.read_visibility(f"---\ntitle: X\nvisibility: {value}\n---\nbody\n") == ("ok", value)


def test_a_missing_key_is_missing():
    assert vc.read_visibility("---\ntitle: X\n---\nbody\n") == (vc.MISSING, None)


def test_a_blank_value_is_missing():
    assert vc.read_visibility("---\ntitle: X\nvisibility:\n---\nbody\n")[0] == vc.MISSING


def test_an_unknown_value_is_invalid_and_carries_the_value():
    assert vc.read_visibility("---\ntitle: X\nvisibility: gm_only\n---\n") == (vc.INVALID, "gm_only")


def test_no_frontmatter_block():
    assert vc.read_visibility("# Just a heading\n") == (vc.NO_FRONTMATTER, None)


def test_broken_yaml():
    assert vc.read_visibility("---\ntitle: [unclosed\n---\n")[0] == vc.BAD_YAML


# -- set_visibility ------------------------------------------------------------------

def test_set_replaces_the_existing_line_and_nothing_else():
    after = vc.set_visibility(PAGE, "public")
    assert after == PAGE.replace("visibility: gm_secrets", "visibility: public")


def test_set_inserts_after_title_when_missing():
    page = "---\ntitle: X\ntags: []\n---\n\nBody\n"
    assert vc.set_visibility(page, "internal") == "---\ntitle: X\nvisibility: internal\ntags: []\n---\n\nBody\n"


def test_set_inserts_first_when_there_is_no_title():
    assert vc.set_visibility("---\ntags: []\n---\nB\n", "public").startswith("---\nvisibility: public\ntags: []\n")


def test_set_leaves_the_body_untouched():
    assert vc.set_visibility(PAGE, "public").endswith("\nProse.\n")


def test_set_rejects_a_bad_value_and_a_page_with_no_frontmatter():
    with pytest.raises(ValueError):
        vc.set_visibility(PAGE, "secret")
    with pytest.raises(ValueError):
        vc.set_visibility("# no frontmatter\n", "public")


def test_set_is_idempotent():
    once = vc.set_visibility(PAGE, "public")
    assert vc.set_visibility(once, "public") == once


# -- check over a tree ---------------------------------------------------------------

def test_check_reports_only_flawed_lore_files(tmp_path):
    _put(tmp_path, "world/locations/a.md", PAGE)
    _put(tmp_path, "world/locations/b.md", "---\ntitle: B\n---\n")
    _put(tmp_path, "narrative/lore/c.md", "---\nvisibility: nope\n---\n")
    _put(tmp_path, "mechanics/d.md", "no frontmatter\n")
    got = {(str(rel), kind) for rel, kind, _ in vc.check(tmp_path)}
    assert got == {("world/locations/b.md", vc.MISSING),
                   ("narrative/lore/c.md", vc.INVALID),
                   ("mechanics/d.md", vc.NO_FRONTMATTER)}


def test_check_skips_category_files_zz_stubs_archives_and_other_dirs(tmp_path):
    bare = "---\ntitle: X\n---\n"
    _put(tmp_path, "world/locations/_category.md", bare)
    _put(tmp_path, "world/locations/zzkashkar.md", bare)
    _put(tmp_path, "world/archive/old.md", bare)
    _put(tmp_path, "world/data/coord-audit/audit-1.md", bare)
    _put(tmp_path, "docs/page.md", bare)
    _put(tmp_path, "transcripts/t.md", bare)
    assert vc.check(tmp_path) == []


def test_templates_are_scanned(tmp_path):
    _put(tmp_path, "templates/_TEMPLATE_x.md", "---\ntitle: T\n---\n")
    assert [k for _, k, _ in vc.check(tmp_path)] == [vc.MISSING]


# -- command line --------------------------------------------------------------------

def test_set_command_writes_only_the_flag_line(tmp_path, capsys):
    p = _put(tmp_path, "x.md", PAGE)
    assert vc.main(["set", str(p), "public"]) == 0
    assert p.read_text() == PAGE.replace("gm_secrets", "public")


def test_set_command_refuses_a_bad_value(tmp_path):
    p = _put(tmp_path, "x.md", PAGE)
    with pytest.raises(SystemExit):
        vc.main(["set", str(p), "secret"])
    assert p.read_text() == PAGE


def test_set_command_on_a_file_without_frontmatter_changes_nothing(tmp_path):
    p = _put(tmp_path, "x.md", "# plain\n")
    assert vc.main(["set", str(p), "public"]) == 2
    assert p.read_text() == "# plain\n"


def test_show_command_prints_the_value_or_the_problem(tmp_path, capsys):
    ok = _put(tmp_path, "ok.md", PAGE)
    bare = _put(tmp_path, "bare.md", "---\ntitle: X\n---\n")
    assert vc.main(["show", str(ok)]) == 0
    assert capsys.readouterr().out.strip() == "gm_secrets"
    assert vc.main(["show", str(bare)]) == 1
    assert capsys.readouterr().out.strip() == "(missing)"


def test_check_command_warns_by_default_and_fails_only_when_strict(monkeypatch, tmp_path, capsys):
    _put(tmp_path, "world/b.md", "---\ntitle: B\n---\n")
    monkeypatch.setattr(vc, "VAULT_ROOT", tmp_path)
    assert vc.main(["check"]) == 0
    assert vc.main(["check", "--strict"]) == 1
    assert "b.md" in capsys.readouterr().err


# -- the two callers that used to default to public ----------------------------------

def test_normalize_locations_adds_gm_secrets_not_public():
    sys.path.insert(0, str(ROOT / "utilities" / "world"))
    import normalize_locations as nl
    out, changes = nl._normalize_fm("title: Achal\n", Path("achal.md"), True)
    assert "visibility: gm_secrets" in out
    assert "visibility: public" not in out
    assert any("gm_secrets" in c for c in changes)


def test_normalize_locations_leaves_an_existing_flag_alone():
    sys.path.insert(0, str(ROOT / "utilities" / "world"))
    import normalize_locations as nl
    out, _ = nl._normalize_fm("title: Achal\nvisibility: public\n", Path("achal.md"), True)
    assert out.count("visibility:") == 1 and "visibility: public" in out


def test_build_warns_about_unflagged_lore_without_failing(monkeypatch, capsys):
    sys.path.insert(0, str(ROOT / "utilities"))
    import build
    from shared import visibility_check as built_vc
    monkeypatch.setattr(built_vc, "check", lambda root: [(Path("world/x.md"), vc.MISSING, None)])
    build._warn_visibility()
    assert "1 lore file(s) lack a valid visibility" in capsys.readouterr().err
