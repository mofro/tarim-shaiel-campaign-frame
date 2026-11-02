"""
Tests for the Map Workshop type scale and text contrast (#333 step 1).

Scenarios (posted on #333):
  1. font sizes come from a 5-token rem scale, no raw px sizes in the sidebar CSS
  2. every text colour is at least 4.5:1 on the background it sits on
  4. the scale is a pure restyle: no new rules for layout properties are asserted
     here, so this file only guards sizes and colours

Backgrounds: a rule that declares its own solid background is measured against
it; every other rule is measured against #1a1410, the lightest background that
text sits on in the sidebar (stricter than the #120f08 panel).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw

SOURCE = Path(gmw.__file__).read_text(encoding="utf-8")
DEFAULT_BG = "#1a1410"
MIN_CONTRAST = 4.5


def _strip_player_css(src: str) -> str:
    """The player-map layer CSS shares this file but is not the Workshop sidebar."""
    return src.replace(gmw._PLAYER_LAYERS_CSS, "")


def _tokens(css: str) -> dict:
    root = re.search(r":root\s*\{([^}]*)\}", css)
    assert root, "expected a :root block defining the type and colour tokens"
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root.group(1)))


def _resolve(value: str, tokens: dict) -> str:
    value = value.strip()
    m = re.fullmatch(r"var\((--[\w-]+)\)", value)
    return tokens[m.group(1)].strip() if m else value


def _lum(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _rules(css: str):
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel = " ".join(m.group(1).split())
        if sel.startswith(":root"):
            continue
        yield sel, dict(
            (k.strip(), v.strip())
            for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+);?", m.group(2))
        )


HEX = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b")


def test_scale_tokens_are_five_rem_steps_about_1_2x_apart():
    t = _tokens(gmw._CSS)
    steps = [t[f"--fs-{i}"] for i in range(1, 6)]
    assert all(s.endswith("rem") for s in steps), steps
    rems = [float(s[:-3]) for s in steps]
    assert rems[0] >= 0.75, "floor is 12px for uppercase or tracked labels"
    assert rems[1] >= 0.8125, "floor is 13px for lowercase text"
    for lo, hi in zip(rems, rems[1:]):
        assert hi / lo >= 1.15, f"steps too close: {rems}"
    assert f"--fs-6" not in t, "scale is 4-5 tokens"


def test_sidebar_css_uses_tokens_not_raw_sizes():
    # Workshop sidebar scope: the _CSS block plus inline style="..." attributes.
    # The player map's own page CSS (follow button etc.) is a different surface.
    inline = " ".join(re.findall(r'style="([^"]*)"', _strip_player_css(SOURCE)))
    scope = re.sub(r"--fs-\d\s*:\s*[^;]+;", "", gmw._CSS) + " " + inline
    raw = re.findall(r"font-size\s*:\s*(?!\s|var\(--fs-\d\))[^;}\"']+", scope)
    assert not raw, f"raw font-size values remain: {sorted(set(raw))}"
    # the shorthand would bypass the scale
    assert not re.findall(r"font\s*:\s*\d", scope)


def test_every_text_colour_meets_4_5_to_1():
    tokens = _tokens(gmw._CSS)
    failures = []
    for sel, decls in _rules(_strip_player_css(gmw._CSS)):
        if "color" not in decls:
            continue
        fg = _resolve(decls["color"], tokens)
        if not HEX.fullmatch(fg):
            continue
        bg_raw = decls.get("background") or decls.get("background-color") or ""
        bg_first = _resolve(bg_raw.split()[0], tokens) if bg_raw.strip() else ""
        bg = bg_first if HEX.fullmatch(bg_first or "") else DEFAULT_BG
        ratio = _contrast(fg, bg)
        if ratio < MIN_CONTRAST:
            failures.append(f"{sel}: {fg} on {bg} = {ratio:.2f}")
    assert not failures, "text below 4.5:1:\n  " + "\n  ".join(failures)


def test_inline_style_text_colours_meet_4_5_to_1():
    tokens = _tokens(gmw._CSS)
    failures = []
    for style in re.findall(r'style="([^"]*)"', _strip_player_css(SOURCE)):
        m = re.search(r"(?<![-\w])color\s*:\s*(#[0-9a-fA-F]{3,6})", style)
        if not m:
            continue
        bg_m = re.search(r"background\s*:\s*(#[0-9a-fA-F]{3,6})", style)
        bg = bg_m.group(1) if bg_m else DEFAULT_BG
        ratio = _contrast(m.group(1), bg)
        if ratio < MIN_CONTRAST:
            failures.append(f"{style[:60]}: {m.group(1)} on {bg} = {ratio:.2f}")
    assert not failures, "inline text below 4.5:1:\n  " + "\n  ".join(failures)
