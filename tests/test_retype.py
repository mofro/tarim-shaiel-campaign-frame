"""
`map.py retype` (#336, PR 4): set `type:` on many pages from a sheet, changing
`type:` and `last_updated:` and nothing else, refusing the whole sheet on one bad row.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "utilities"))

from locations import retype  # noqa: E402

BODY = "\n# {t}\n\nProse that must never change.\n"


def page(title, type_, *, status="draft", extra=""):
    return (
        "---\n"
        f"title: {title}\n"
        f"status: {status}\n"
        "last_updated: 2026-01-01\n"
        "location:\n- 40.1\n- 65.2\n"
        f"mapmarker: {type_}\n"
        f"{extra}"
        f"type: {type_}\n"
        "tags:\n- placeholder\n"
        "---\n" + BODY.format(t=title)
    )


@pytest.fixture
def vault(tmp_path):
    d = tmp_path / "world" / "locations"
    d.mkdir(parents=True)
    (d / "achal.md").write_text(page("Achal", "caravanserai"), encoding="utf-8")
    (d / "baryn.md").write_text(page("Baryn", "route-node"), encoding="utf-8")
    (d / "chor.md").write_text(page("Chor", "town", status="canon"), encoding="utf-8")
    (d / "dara.md").write_text(page("Dara", "lake", extra="map_icon: none\n"), encoding="utf-8")
    return d


def sheet(tmp_path, *rows, header="slug,type,from"):
    f = tmp_path / "sheet.csv"
    f.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return f


def run(tmp_path, vault, *rows, dry_run=False, confirm_canon=False, header="slug,type,from"):
    lines = []
    code = retype.apply_sheet(sheet(tmp_path, *rows, header=header), vault,
                              dry_run=dry_run, confirm_canon=confirm_canon, out=lines.append)
    return code, "\n".join(lines)


def snapshot(vault):
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(vault.glob("*.md"))}


def changed_lines(before, after):
    b, a = before.splitlines(), after.splitlines()
    assert len(b) == len(a)
    return [(x, y) for x, y in zip(b, a) if x != y]


# -- what it writes --------------------------------------------------------------------

def test_it_changes_type_and_last_updated_and_nothing_else(tmp_path, vault):
    before = snapshot(vault)
    code, out = run(tmp_path, vault, "achal,village,caravanserai")
    assert code == 0 and "changed 1 file(s)" in out
    after = snapshot(vault)
    assert after["baryn.md"] == before["baryn.md"]
    diff = changed_lines(before["achal.md"], after["achal.md"])
    assert [x for x, _ in diff] == ["last_updated: 2026-01-01", "type: caravanserai"]
    assert "type: village" in after["achal.md"]
    assert after["achal.md"].endswith("Prose that must never change.\n")
    assert "mapmarker: caravanserai" in after["achal.md"]  # the inert older marker is not ours


def test_it_leaves_an_icon_override_alone(tmp_path, vault):
    code, _ = run(tmp_path, vault, "dara,village,lake")
    after = snapshot(vault)["dara.md"]
    assert code == 0 and "type: village" in after
    assert "map_icon: none" in after


def test_dry_run_prints_the_diff_and_writes_nothing(tmp_path, vault):
    before = snapshot(vault)
    code, out = run(tmp_path, vault, "achal,village,", "baryn,town,", dry_run=True)
    assert code == 0
    assert snapshot(vault) == before
    assert "-type: caravanserai" in out and "+type: village" in out
    assert "-type: route-node" in out and "+type: town" in out
    assert "would change 2 file(s)" in out
    assert "Rebuild next" not in out


def test_a_write_says_what_to_run_next(tmp_path, vault):
    _, out = run(tmp_path, vault, "achal,village,")
    assert "Rebuild next: venv/bin/python utilities/map.py rebuild" in out


def test_a_page_already_at_the_type_is_counted_not_touched(tmp_path, vault):
    before = snapshot(vault)
    code, out = run(tmp_path, vault, "baryn,route-node,")
    assert code == 0 and snapshot(vault) == before
    assert "changed 0 file(s); 1 already at that Type" in out


def test_a_blank_type_skips_the_row(tmp_path, vault):
    before = snapshot(vault)
    code, out = run(tmp_path, vault, "achal,,caravanserai", ",,")
    assert code == 0 and snapshot(vault) == before
    assert "1 row(s) skipped" in out


def test_extra_columns_are_ignored(tmp_path, vault):
    code, _ = run(tmp_path, vault, "achal,village,caravanserai,a note,5",
                  header="slug,type,from,note,rank")
    assert code == 0 and "type: village" in snapshot(vault)["achal.md"]


# -- what it refuses -------------------------------------------------------------------

def refused(tmp_path, vault, *rows, confirm_canon=False, header="slug,type,from"):
    before = snapshot(vault)
    code, out = run(tmp_path, vault, *rows, confirm_canon=confirm_canon, header=header)
    assert code == 2
    assert out.startswith("Nothing was written")
    assert snapshot(vault) == before
    return out


def test_one_bad_row_stops_the_whole_sheet(tmp_path, vault):
    out = refused(tmp_path, vault, "achal,village,", "baryn,not-a-type,")
    assert "baryn: “not-a-type” is not a Type" in out


def test_every_bad_row_is_named(tmp_path, vault):
    out = refused(tmp_path, vault, "nowhere,village,", "baryn,water,", "achal,town,")
    assert "nowhere: no such location file" in out
    assert "baryn: “water” is not a Type" in out


def test_a_type_that_is_only_tolerated_is_not_one_to_move_to(tmp_path, vault):
    for legacy in ("caravanserai", "water-body", "Oasis"):
        assert "is not a Type" in refused(tmp_path, vault, f"baryn,{legacy},")


def test_a_stale_row_is_refused(tmp_path, vault):
    out = refused(tmp_path, vault, "achal,village,town")
    assert "achal: stale row" in out and "“caravanserai”, not “town”" in out


def test_a_slug_twice_is_refused(tmp_path, vault):
    assert "baryn: appears more than once" in refused(tmp_path, vault, "baryn,town,", "baryn,city,")


def test_a_type_with_no_slug_is_refused(tmp_path, vault):
    assert "no slug" in refused(tmp_path, vault, ",village,")


def test_a_canon_page_needs_confirm_canon(tmp_path, vault):
    out = refused(tmp_path, vault, "chor,city,")
    assert "chor: canon file" in out
    code, _ = run(tmp_path, vault, "chor,city,", confirm_canon=True)
    assert code == 0 and "type: city" in snapshot(vault)["chor.md"]


def test_a_sheet_without_the_columns_is_refused(tmp_path, vault):
    out = refused(tmp_path, vault, "achal,village", header="slug,kind")
    assert "needs a `slug` and a `type` column (missing: type)" in out


def test_a_missing_sheet_is_refused(tmp_path, vault):
    lines = []
    code = retype.apply_sheet(tmp_path / "nope.csv", vault, dry_run=False, confirm_canon=False,
                              out=lines.append)
    assert code == 2 and "Nothing was written" in lines[0]


# -- the command -----------------------------------------------------------------------

def test_map_py_retype_runs_end_to_end(tmp_path, vault):
    def cmd(sheet_file, *flags):
        return [sys.executable, str(ROOT / "utilities" / "map.py"), "retype", str(sheet_file),
                "--locations-dir", str(vault), *flags]

    f = sheet(tmp_path, "achal,town,caravanserai")
    dry = subprocess.run(cmd(f, "--dry-run"), capture_output=True, text=True)
    assert dry.returncode == 0 and "would change 1 file(s)" in dry.stdout
    assert "type: caravanserai" in snapshot(vault)["achal.md"]
    real = subprocess.run(cmd(f), capture_output=True, text=True)
    assert real.returncode == 0 and re.search(r"changed 1 file\(s\)", real.stdout)
    assert "type: town" in snapshot(vault)["achal.md"]
    bad = subprocess.run(cmd(sheet(tmp_path, "achal,zzz,")), capture_output=True, text=True)
    assert bad.returncode == 2 and "“zzz” is not a Type" in bad.stdout
