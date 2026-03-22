"""
Shared HTML page shell and CSS base for Tarim-Shaiel generators.

Provides:
  CSS_BASE    — shared design-system CSS (custom properties, cover, banner,
                back-nav, credits, responsive rules)
  build_page  — full HTML page with cover / banner / content / credits scaffold

Each generator supplies:
  - css_extra      : type-specific CSS (body background, content padding,
                     section-specific rules)
  - cover_image_url: URL for the cover background image
  - cover_subtitle : subtitle text rendered below the title in the cover
  - banner_left    : left-side banner label (e.g. "World Lore")
  - banner_right   : right-side banner text (e.g. "The Roads · Tarim-Shaiel")
  - content_html   : the rendered body HTML inserted into .content
  - credits_html   : HTML inserted into the .credits footer
  - generator_name : appears in the <!-- AUTO-GENERATED --> comment
"""

from html import escape as html_escape

FAVICON_SVG = (
    "data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='10' fill='%231a1208'/>"
    "<polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 "
    "81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 "
    "33.4,43.1 18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>"
)

# ---------------------------------------------------------------------------
# Shared CSS base
# ---------------------------------------------------------------------------

CSS_BASE = """\
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --ink:        #1a1208;
      --parchment:  #f5edd8;
      --parchment2: #ede0c4;
      --gold:       #b8922c;
      --gold-light: #d4a843;
      --crimson:    #7a1f1f;
      --steel:      #3c4a5a;
      --rule:       rgba(184,146,44,0.4);
      --shadow:     rgba(26,18,8,0.15);
    }

    html { scroll-behavior: smooth; }

    .page-wrap {
      max-width: 860px;
      margin: 0 auto;
      background: var(--parchment);
      box-shadow: 0 0 80px rgba(0,0,0,0.75);
      position: relative;
      overflow: hidden;
    }

    .page-wrap::before {
      content: '';
      position: absolute; inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 0;
      opacity: 0.45;
    }

    .cover {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      overflow: hidden;
    }

    .cover-image {
      position: absolute; inset: 0;
      background-size: cover;
      background-position: center 4%;
      z-index: 0;
    }

    .cover-gradient {
      position: absolute; inset: 0;
      background: linear-gradient(to bottom, rgba(26,18,8,0.08) 0%, rgba(26,18,8,0.55) 55%, rgba(26,18,8,0.92) 100%);
      z-index: 1;
    }

    .cover-content {
      position: relative;
      z-index: 2;
      padding: 2.5rem 3rem 3rem;
      color: var(--parchment);
    }

    .cover-title {
      font-family: 'Cinzel', serif;
      font-size: 3.2rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      line-height: 1.1;
      color: #f5e6c0;
      text-shadow: 0 2px 12px rgba(0,0,0,0.7);
      margin-bottom: 0.15rem;
    }

    .cover-subtitle {
      font-family: 'Cinzel', serif;
      font-size: 1rem;
      font-weight: 400;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--gold-light);
    }

    .banner {
      background: var(--steel);
      color: var(--parchment);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 3rem;
      font-family: 'Cinzel', serif;
      font-size: 0.72rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }

    .banner-rule {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--gold), transparent);
      margin: 0 3rem;
    }

    .back-nav {
      background: #111008;
      padding: 0.5rem 3rem;
      border-bottom: 1px solid rgba(184,146,44,0.2);
    }

    .back-nav a {
      font-family: 'Cinzel', serif;
      font-size: 0.68rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: rgba(184,146,44,0.6);
      text-decoration: none;
      transition: color 0.2s;
    }

    .back-nav a:hover { color: var(--gold); }

    .divider {
      height: 1px;
      background: linear-gradient(to right, transparent, var(--gold), transparent);
      margin: 2rem 0;
    }

    .credits {
      background: var(--steel);
      color: rgba(245,237,216,0.55);
      padding: 2rem 3rem;
      font-size: 0.88rem;
      line-height: 1.6;
    }

    @media (max-width: 640px) {
      .cover-title { font-size: 2.2rem; }
      .cover-content, .content { padding: 1.8rem 1.4rem; }
      .banner { padding: 0.5rem 1.4rem; }
      .banner-rule { margin: 0 1.4rem; }
      .credits { padding: 1.6rem 1.4rem; }
    }
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
    css_extra: str = '',
    generator_name: str = 'utilities',
) -> str:
    """Assemble a complete HTML page using the shared Tarim-Shaiel design system.

    Parameters
    ----------
    title          : Document title (used in <title>, cover, banner)
    cover_subtitle : Subtitle line below the title in the cover block
    banner_left    : Left label in the steel banner strip
    banner_right   : Right label in the steel banner strip
    content_html   : Pre-rendered HTML inserted into .content
    credits_html   : HTML inserted into .credits footer
    cover_image_url: URL for .cover-image background
    css_extra      : Additional CSS appended after CSS_BASE (generator-specific rules)
    generator_name : Appears in the AUTO-GENERATED comment
    """
    title_esc = html_escape(title)
    subtitle_esc = html_escape(cover_subtitle)
    banner_left_esc = html_escape(banner_left)
    banner_right_esc = html_escape(banner_right)
    cover_url_esc = html_escape(cover_image_url, quote=True)

    css = CSS_BASE + css_extra

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title_esc} &mdash; Tarim-Shaiel</title>
  <link rel="icon" href="{FAVICON_SVG}">
  <!-- AUTO-GENERATED by {generator_name} — do not hand-edit -->
  <style>{css}  </style>
</head>
<body>

<div class="page-wrap">

  <!-- BACK NAV -->
  <div class="back-nav">
    <a href="index.html">&#8592; Campaign Documents</a>
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
