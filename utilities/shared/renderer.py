"""Jinja2 environment and rendering helpers for Tarim-Shaiel generators."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

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
    """
    env = get_env()
    context.setdefault('favicon_svg', _FAVICON_SVG)
    context.setdefault('gm_guard_script', _GM_GUARD_SCRIPT)
    context.setdefault('gm_mode', False)
    context.setdefault('extra_css', [])
    context.setdefault('use_base_css', True)
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)
