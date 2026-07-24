"""Jinja2 environment and rendering helpers for Tarim-Shaiel generators."""

import json
import os
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

_CSS_DIR = Path(__file__).parent / "css"

# One version per build run -- forces browsers to fetch fresh CSS instead of
# holding onto these unversioned filenames indefinitely across reloads.
_ASSET_VERSION = str(int(time.time()))


def _inline_css(*stems: str) -> str:
    """Read and concatenate CSS files from utilities/shared/css/ for standalone output."""
    parts = []
    for stem in stems:
        path = _CSS_DIR / f"{stem}.css"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

def _load_newspaper_name() -> str:
    config_path = Path(__file__).parent.parent.parent / "storytell_config.json"
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        return cfg.get("newspaper", {}).get("name", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""

_NEWSPAPER_NAME = _load_newspaper_name()

_FAVICON_SVG = (
    "data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect width='100' height='100' rx='10' fill='%231a1208'/>"
    "<polygon points='50,6 56.9,33.4 81.1,18.9 66.6,43.1 94,50 66.6,56.9 "
    "81.1,81.1 56.9,66.6 50,94 43.1,66.6 18.9,81.1 33.4,56.9 6,50 "
    "33.4,43.1 18.9,18.9 43.1,33.4' fill='%23b8922c'/></svg>"
)

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


def get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(['html']),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_page(template_name: str, **context) -> str:
    """Render a Jinja2 page template with the given context.

    Injects shared constants (favicon, gm_guard_script) into every context.
    When TS_STANDALONE=1, also injects pre-computed inline_css_html so the
    template can emit a <style> block instead of <link> tags.
    """
    env = get_env()
    context.setdefault('favicon_svg', _FAVICON_SVG)
    context.setdefault('gm_guard_script', _GM_GUARD_SCRIPT)
    context.setdefault('gm_mode', False)
    context.setdefault('extra_css', [])
    context.setdefault('use_base_css', True)
    context.setdefault('asset_version', _ASSET_VERSION)
    context.setdefault('newspaper_name', _NEWSPAPER_NAME)

    _standalone = os.environ.get('TS_STANDALONE') == '1'
    context.setdefault('standalone', _standalone)
    if _standalone and 'inline_css_html' not in context:
        stems = ['tokens']
        if context.get('use_base_css', True):
            stems += ['base', 'comp-nav', 'comp-sidebar', 'comp-card']
        stems += list(context.get('extra_css', []))
        if context.get('gm_mode', False):
            stems.append('gm')
        context['inline_css_html'] = f'<style>\n{_inline_css(*stems)}\n</style>'

    tmpl = env.get_template(template_name)
    return tmpl.render(**context)
