"""
Tests for the newspaper generator's flat output (/newspaper/<slug>.html).

Covers slug resolution (manifest `slug:` over folder name, invalid and duplicate
slugs fail the build), the flat output paths, the index card hrefs, and the
redirect that keeps the pre-flatten issue URL alive.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from newspaper import generate_newspaper_html as gen

REPO = Path(__file__).parent.parent


def _issue(src: Path, folder: str, slug: str | None = None):
    d = src / folder
    d.mkdir(parents=True)
    slug_line = f'slug: "{slug}"\n' if slug is not None else ""
    (d / "manifest.md").write_text(
        f'---\ntype: newspaper-manifest\n{slug_line}masthead:\n  title: "T {folder}"\n  issueNo: "No. 1"\n---\n',
        encoding="utf-8",
    )
    (d / "01-lead.md").write_text(
        "---\ntype: newspaper-story\nweight: lead\npage: 1\norder: 1\nheadline: \"Headline\"\n---\n\nBody.\n",
        encoding="utf-8",
    )


@pytest.fixture
def paths(tmp_path, monkeypatch):
    src, out = tmp_path / "src", tmp_path / "out"
    monkeypatch.setattr(gen, "NEWS_SRC", src)
    monkeypatch.setattr(gen, "NEWS_OUT", out)
    monkeypatch.setattr(gen, "_load_np_config", lambda: {"name": "The Herald"})
    return src, out


class TestSlug:
    def test_manifest_slug_wins_over_folder_name(self, tmp_path):
        d = tmp_path / "0002-long-folder"
        d.mkdir()
        assert gen._issue_slug(d, {"slug": "short-name"}) == "short-name"

    @pytest.mark.parametrize("fm", [{}, {"slug": ""}, {"slug": None}])
    def test_missing_slug_falls_back_to_folder_name(self, tmp_path, fm):
        d = tmp_path / "0003-fallback"
        d.mkdir()
        assert gen._issue_slug(d, fm) == "0003-fallback"

    @pytest.mark.parametrize("bad", ["Has Caps", "with/slash", "-lead", "trail-", "a--b", "x.html"])
    def test_invalid_slug_is_a_build_error(self, tmp_path, bad):
        d = tmp_path / "0004-bad"
        d.mkdir()
        with pytest.raises(ValueError):
            gen._issue_slug(d, {"slug": bad})


class TestFlatOutput:
    def test_issue_is_written_flat_not_in_a_folder(self, paths):
        src, out = paths
        _issue(src, "0002-folder-name", slug="the-slug")
        gen.generator.run()
        assert (out / "the-slug.html").is_file()
        assert not (out / "the-slug").exists()
        assert not (out / "0002-folder-name").exists()
        assert (out / "index.html").is_file()

    def test_index_cards_link_to_flat_files(self, paths):
        src, out = paths
        _issue(src, "0002-folder-name", slug="the-slug")
        gen.generator.run()
        index = (out / "index.html").read_text(encoding="utf-8")
        assert 'href="/newspaper/the-slug.html"' in index
        assert "/newspaper/the-slug/" not in index

    def test_issue_page_links_back_to_the_index(self, paths):
        src, out = paths
        _issue(src, "0002-folder-name", slug="the-slug")
        gen.generator.run()
        assert 'href="/newspaper/"' in (out / "the-slug.html").read_text(encoding="utf-8")

    def test_duplicate_slugs_fail_the_build(self, paths):
        src, _ = paths
        _issue(src, "0002-a", slug="same")
        _issue(src, "0003-b", slug="same")
        with pytest.raises(ValueError):
            gen.generator.run()

    def test_slug_index_is_refused(self, paths):
        src, _ = paths
        _issue(src, "0002-a", slug="index")
        with pytest.raises(ValueError):
            gen.generator.run()


class TestPublishedIssue:
    def test_published_issue_has_a_slug_and_its_old_url_redirects(self):
        manifest = (REPO / "narrative/newspaper/0002-session-0-convergence/manifest.md").read_text(encoding="utf-8")
        assert 'slug: "session-0-convergence"' in manifest
        toml = (REPO / "netlify.toml").read_text(encoding="utf-8")
        assert 'from   = "/newspaper/0002-session-0-convergence/"' in toml
        assert 'to     = "/newspaper/session-0-convergence.html"' in toml
