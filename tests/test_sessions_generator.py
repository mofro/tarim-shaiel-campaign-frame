"""
Tests for the session notes generator (Session_N_Player_Summary.md -> HTML).

Covers the fail-closed selection rule, title and lead-heading handling, the
body clean-ups the Player Summaries need, and the renderer features added for
them (ordered lists, structured callouts, keep_h1).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from sessions import generate_sessions_html as gen
from shared.html_render import render_body


def _summary(folder: Path, number: int, visibility="public", status="canon", body="Body text.\n"):
    """Write a Session_<n>_Player_Summary.md under folder and return its path."""
    folder.mkdir(parents=True, exist_ok=True)
    src = folder / f"Session_{number}_Player_Summary.md"
    src.write_text(
        f"---\nvisibility: {visibility}\nstatus: {status}\ncampaign: Tarim-Shaiel\n---\n\n{body}",
        encoding="utf-8",
    )
    return src


def _render(body: str, **kw) -> str:
    html, _ = render_body(body, gen.VAULT_ROOT, gen.DOCS_DIR, gm_mode=False, **kw)
    return html


class TestSelection:
    """A file is published only when name, visibility and status all agree."""

    def test_public_canon_player_summary_is_loaded(self, tmp_path):
        src = _summary(tmp_path / "01_session1", 1)
        loaded = gen.load_player_summary(src)
        assert loaded is not None
        assert loaded["number"] == 1

    @pytest.mark.parametrize("visibility,status", [
        ("gm_secrets", "canon"),
        ("public", "draft"),
        ("internal", "review"),
    ])
    def test_wrong_visibility_or_status_is_refused(self, tmp_path, visibility, status):
        src = _summary(tmp_path / "02_session2", 2, visibility=visibility, status=status)
        assert gen.load_player_summary(src) is None

    def test_missing_frontmatter_fields_are_refused(self, tmp_path):
        src = tmp_path / "Session_3_Player_Summary.md"
        src.write_text("No frontmatter at all.\n", encoding="utf-8")
        assert gen.load_player_summary(src) is None

    @pytest.mark.parametrize("name", [
        "Session_2_Player_Summary_Full.md",
        "Session_2_GM_Notes.md",
        "session_2_player_summary.md",
        "index.md",
    ])
    def test_other_filenames_are_refused_even_when_public_and_canon(self, tmp_path, name):
        src = tmp_path / name
        src.write_text("---\nvisibility: public\nstatus: canon\n---\n\nBody\n", encoding="utf-8")
        assert gen.load_player_summary(src) is None

    def test_number_comes_from_the_filename(self):
        assert gen.player_summary_number(Path("Session_12_Player_Summary.md")) == 12
        assert gen.player_summary_number(Path("Session_x_Player_Summary.md")) is None

    def test_title_comes_from_the_number_not_frontmatter(self):
        assert gen.session_title(2) == "Session 2 — Player Summary"


class TestLeadTitle:
    def test_colon_form_yields_subtitle(self):
        sub, body = gen._split_lead_title("###### Session 0: Prologue\n\nText.\n", 0)
        assert sub == "Prologue"
        assert body.strip() == "Text."

    def test_bare_form_yields_empty_subtitle(self):
        sub, body = gen._split_lead_title("# Session 1\n\n## Chapter 1: Waking\n", 1)
        assert sub == ""
        assert "Chapter 1: Waking" in body

    def test_next_heading_is_not_swallowed_as_subtitle(self):
        """Regression: the first chapter heading was captured as the subtitle."""
        sub, body = gen._split_lead_title("# Session 3\n## Chapter 5: Smoke\n\nText\n", 3)
        assert sub == ""
        assert body.lstrip().startswith("## Chapter 5: Smoke")

    def test_other_session_number_is_left_alone(self):
        text = "# Session 2\n\nText\n"
        assert gen._split_lead_title(text, 1) == ("", text)

    def test_session_ten_is_not_read_as_session_one(self):
        text = "# Session 10\n\nText\n"
        assert gen._split_lead_title(text, 1) == ("", text)

    def test_only_the_leading_heading_is_touched(self):
        text = "Intro paragraph.\n\n# Session 1\n\nText\n"
        assert gen._split_lead_title(text, 1) == ("", text)


class TestPrepareBody:
    def test_numeric_references_are_decoded(self):
        _, body = gen.prepare_body("Volkat&#x68; and &#104;ere &#72;\n", 9)
        assert body.strip() == "Volkath and here H"

    def test_out_of_range_reference_is_left_alone(self):
        _, body = gen.prepare_body("bad &#x110000; ref\n", 9)
        assert "&#x110000;" in body

    def test_decoded_markup_is_still_escaped_by_the_renderer(self):
        _, body = gen.prepare_body("&#x3C;script&#x3E;alert(1)&#x3C;/script&#x3E;\n", 9)
        html = _render(body)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_audio_embed_becomes_text_cue(self):
        _, body = gen.prepare_body("![[Stone_Beneath.mp3|Stone Beneath Your Feet]]\n", 9)
        assert body.strip() == "*♪ Stone Beneath Your Feet*"

    def test_image_embed_is_not_treated_as_audio(self):
        _, body = gen.prepare_body("![[map.png]]\n", 9)
        assert body.strip() == "![[map.png]]"

    def test_rule_and_heading_are_isolated_by_blank_lines(self):
        _, body = gen.prepare_body("para one\n---\n## Heading\npara two\n", 9)
        html = _render(body)
        assert 'class="divider"' in html
        assert "<h2" in html and "Heading" in html
        assert "para two" in html


class TestRendererAdditions:
    def test_ordered_item_keeps_its_number(self):
        html = _render("7. **Volkath's Tale**\n", ordered_lists=True)
        assert '<ol start="7">' in html
        assert "<strong>Volkath" in html

    def test_consecutive_ordered_lines_share_one_list(self):
        html = _render("1. one\n2. two\n", ordered_lists=True)
        assert html.count("<ol") == 1
        assert html.count("<li>") == 2
        assert "start=" not in html

    def test_mixed_numbered_and_plain_lines_stay_a_paragraph(self):
        html = _render("1. one\nplain line\n", ordered_lists=True)
        assert "<ol" not in html
        assert "<p>" in html

    def test_numbered_paragraphs_are_untouched_unless_asked(self):
        """Regression: the ancestry pages' numbered questions must stay <p>."""
        html = _render("1. **Where are you from?** Text.\n\n2. **What changed?** Text.\n")
        assert "<ol" not in html
        assert html.count("<p>1. ") == 1 and html.count("<p>2. ") == 1

    def test_h1_is_stripped_by_default_and_kept_as_part_title_on_request(self):
        assert "part-title" not in _render("# ***Act 1***\n")
        html = _render("# ***Act 1***\n", keep_h1=True)
        assert '<h2 class="part-title" id="act-1">Act 1</h2>' in html

    def test_titled_callout_renders_title_text_and_bullets(self):
        html = _render("> [!info] NPC Reference\n> **Kira** (scout)\n> - Scarred\n> - Armed\n")
        assert 'class="callout callout-info"' in html
        assert '<div class="callout-title">NPC Reference</div>' in html
        assert "<ul>" in html and html.count("<li>") == 2

    def test_plain_quote_keeps_single_div_form(self):
        html = _render("> just a quote\n")
        assert html.strip() == '<div class="callout">just a quote</div>'


class TestEndToEnd:
    def test_builds_public_canon_and_skips_the_rest(self, tmp_path, monkeypatch, capsys):
        src_root = tmp_path / "sessions"
        _summary(src_root / "00_session0", 0, body=(
            "###### Session 0: Prologue\n\n# ***Act 1***\n\n## Waking\n\n"
            "![[track.mp3|Cue]]\n\nProse.\n"
        ))
        _summary(src_root / "01_session1", 1,
                 body="# Session 1\n\n## Chapter 1\n\n3. **Volkath's Tale**\n\nText\n")
        _summary(src_root / "02_session2", 2, status="draft")
        _summary(src_root / "03_session3", 3, visibility="gm_secrets")
        (src_root / "01_session1" / "Session_1_GM_Notes.md").write_text("secret", encoding="utf-8")

        out = tmp_path / "out"
        monkeypatch.setattr(gen, "SESSIONS_SRC", src_root)
        monkeypatch.setattr(sys, "argv", ["generate_sessions_html.py", "--out", str(out)])
        gen.main()

        assert (out / "00_session0" / "index.html").exists()
        assert (out / "01_session1" / "index.html").exists()
        assert not (out / "02_session2").exists()
        assert not (out / "03_session3").exists()

        page = (out / "00_session0" / "index.html").read_text(encoding="utf-8")
        assert "Session 0 — Player Summary" in page
        assert "Prologue" in page
        assert "<audio" not in page
        assert 'class="part-title"' in page

        beats = (out / "01_session1" / "index.html").read_text(encoding="utf-8")
        assert '<ol start="3">' in beats

        index = (out / "index.html").read_text(encoding="utf-8")
        assert "Session 1 — Player Summary" in index
        assert "Session 2" not in index and "Session 3" not in index
        assert index.index("Session 1") < index.index("Session 0")

        assert "skipped" in capsys.readouterr().out

    def test_nothing_publishable_writes_nothing(self, tmp_path, monkeypatch, capsys):
        src_root = tmp_path / "sessions"
        _summary(src_root / "00_session0", 0, status="draft")
        out = tmp_path / "out"
        monkeypatch.setattr(gen, "SESSIONS_SRC", src_root)
        monkeypatch.setattr(sys, "argv", ["generate_sessions_html.py", "--out", str(out)])
        gen.main()

        assert not out.exists()
        assert "nothing generated" in capsys.readouterr().out
