"""
Shared HTML page shell for Tarim-Shaiel generators.

Provides:
  build_page  — full HTML page with cover / banner / content / credits scaffold

Each generator supplies:
  - extra_css      : tuple of CSS file stems to link (e.g. ('page-ancestry',))
  - cover_image_url: URL for the cover background image
  - cover_subtitle : subtitle text rendered below the title in the cover
  - banner_left    : left-side banner label (e.g. "World Lore")
  - banner_right   : right-side banner text (e.g. "The Roads · Tarim-Shaiel")
  - content_html   : the rendered body HTML inserted into .content
  - credits_html   : HTML inserted into the .credits footer
  - generator_name : appears in the <!-- AUTO-GENERATED --> comment

CSS is served as linked external files from /assets/css/:
  tokens.css   — design-system custom properties (Decision 16 token map)
  base.css     — shared layout, typography, cover, banner, responsive rules
  <stem>.css   — per-page-type rules (supplied via extra_css parameter)
  gm.css       — GM-mode banners (linked only when TS_GM_MODE=1)
"""

import os
from html import escape as html_escape
from pathlib import Path

_CSS_DIR = Path(__file__).parent / "css"


def _read_css(*stems: str) -> str:
    """Read and concatenate CSS files from utilities/shared/css/."""
    parts = []
    for stem in stems:
        path = _CSS_DIR / f"{stem}.css"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _css_version(stem: str) -> str:
    """File mtime as a cache-busting query param -- browsers otherwise hold
    onto these unversioned filenames indefinitely across normal reloads."""
    path = _CSS_DIR / f"{stem}.css"
    try:
        return str(int(path.stat().st_mtime))
    except OSError:
        return "0"

FAVICON_SVG = (
    "data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='10' fill='%231a1208'/>"
    "<polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 "
    "81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 "
    "33.4,43.1 18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>"
)

# ---------------------------------------------------------------------------
# Auth guard script (injected into GM-build pages via TS_GM_MODE env var)
# ---------------------------------------------------------------------------

_GM_GUARD_SCRIPT = """\
<script src="https://cdn.jsdelivr.net/npm/netlify-identity-widget@1/build/netlify-identity-widget.js"></script>
<script>
(function () {
  netlifyIdentity.init();
  netlifyIdentity.on('init', function (user) {
    if (!user) { window.location.replace('login.html' + window.location.hash); }
  });
})();
</script>
"""

# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------

def build_page(
    title: str,
    cover_subtitle: str,
    banner_left: str,
    banner_right: str,
    content_html: str,
    credits_html: str,
    cover_image_url: str,
    extra_css: tuple = (),
    generator_name: str = 'utilities',
    jump_nav_html: str = '',
) -> str:
    """Assemble a complete HTML page using the shared Tarim-Shaiel design system.

    CSS is served as linked external files from /assets/css/ (copied at build
    time by build.py's _copy_css() step).

    Parameters
    ----------
    title          : Document title (used in <title>, cover, banner)
    cover_subtitle : Subtitle line below the title in the cover block
    banner_left    : Left label in the steel banner strip
    banner_right   : Right label in the steel banner strip
    content_html   : Pre-rendered HTML inserted into .content
    credits_html   : HTML inserted into .credits footer
    cover_image_url: URL for .cover-image background
    extra_css      : Tuple of CSS file stems to link after base.css
                     (e.g. ('page-ancestry',) → /assets/css/page-ancestry.css)
    generator_name : Appears in the AUTO-GENERATED comment
    """
    title_esc = html_escape(title)
    subtitle_esc = html_escape(cover_subtitle)
    banner_left_esc = html_escape(banner_left)
    banner_right_esc = html_escape(banner_right)
    cover_url_esc = html_escape(cover_image_url, quote=True)

    _gm = os.environ.get('TS_GM_MODE') == '1'
    _standalone = os.environ.get('TS_STANDALONE') == '1'
    guard_html   = _GM_GUARD_SCRIPT if _gm else ''
    gm_banner_html = '<div class="gm-mode-top-banner">GM VIEW — PRIVILEGED ARCHIVE</div>\n' if _gm else ''

    if _standalone:
        css_stems = ['tokens', 'base', *extra_css]
        if _gm:
            css_stems.append('gm')
        css_section = f'  <style>\n{_read_css(*css_stems)}\n  </style>\n'
    else:
        extra_link_tags = ''.join(
            f'  <link rel="stylesheet" href="/assets/css/{stem}.css?v={_css_version(stem)}">\n'
            for stem in extra_css
        )
        gm_link_tag = (
            f'  <link rel="stylesheet" href="/assets/css/gm.css?v={_css_version("gm")}">\n'
            if _gm else ''
        )
        css_section = (
            f'  <link rel="stylesheet" href="/assets/css/tokens.css?v={_css_version("tokens")}">\n'
            f'  <link rel="stylesheet" href="/assets/css/base.css?v={_css_version("base")}">\n'
            f'{extra_link_tags}{gm_link_tag}'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title_esc} &mdash; Tarim-Shaiel</title>
  <link rel="icon" href="{FAVICON_SVG}">
  <!-- AUTO-GENERATED by {generator_name} — do not hand-edit -->
  <script>(function(){{var t=localStorage.getItem('ts-theme');if(t)document.documentElement.setAttribute('data-theme',t);}})()</script>
{css_section}</head>
<body>

{guard_html}{jump_nav_html}<div class="page-wrap">
{gm_banner_html}

  <!-- BACK NAV -->
  <div class="back-nav">
    <a href="index.html">&#8592; Home</a>
  </div>

  <!-- COVER -->
  <div class="cover">
    <div class="cover-image" style="background-image: url('{cover_url_esc}');"></div>
    <div class="cover-gradient"></div>
    <div class="cover-content">
      <div class="cover-title">{title_esc}</div>
      <div class="cover-subtitle">{subtitle_esc}</div>
    </div>
  </div>

  <div class="banner">
    <span>{banner_left_esc}</span>
    <span>{banner_right_esc}</span>
  </div>
  <div class="banner-rule"></div>

  <!-- MAIN CONTENT -->
  <div class="content">
{content_html}  </div><!-- /content -->

  <!-- FOOTER -->
  <div class="credits">
{credits_html}  </div>

</div><!-- /page-wrap -->

</body>
</html>
"""
