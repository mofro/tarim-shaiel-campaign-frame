#!/usr/bin/env python3
"""
Tarim-Shaïal local development server.

Replaces 'python -m http.server' for interactive authoring sessions.
Serves docs/ as the main site, the map workshop at /workshop, and
exposes write-back API endpoints for coordinate updates and rebuilds.

Usage:
    python utilities/devserver.py [--port PORT]
    Site:     http://localhost:8000/
    Workshop: http://localhost:8000/workshop

Endpoints:
    PUT  /api/locations/{slug}/coordinates  — update lat/lon in .md frontmatter
    POST /api/rebuild/locations             — run build.py locations
    POST /api/rebuild/workshop              — run build.py workshop
"""

import http.server
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent
DOCS_DIR = VAULT_ROOT / "docs"
WORKSHOP_PATH = VAULT_ROOT / "map-workshop.html"
LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
DEFAULT_PORT = 8000


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/") == "/workshop":
            self._serve_workshop()
        else:
            super().do_GET()

    def do_PUT(self):
        m = re.match(r"^/api/locations/([^/?]+)/coordinates(?:\?.*)?$", self.path)
        if m:
            self._put_coordinates(m.group(1))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/rebuild/locations":
            self._rebuild("locations")
        elif self.path == "/api/rebuild/workshop":
            self._rebuild("workshop")
        else:
            self.send_error(404)

    # ---- Handlers ----

    def _serve_workshop(self):
        if not WORKSHOP_PATH.exists():
            self.send_error(
                404,
                "Workshop not built — run: python utilities/build.py workshop",
            )
            return
        body = WORKSHOP_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _put_coordinates(self, slug: str):
        try:
            data = self._read_json()
            lat = float(data["lat"])
            lon = float(data["lon"])
        except (ValueError, KeyError, TypeError):
            return self.send_error(400, 'Body must be {"lat": number, "lon": number}')

        md_path = _find_slug(slug)
        if md_path is None:
            return self._json({"ok": False, "error": f"slug not found: {slug}"}, 404)

        text = md_path.read_text(encoding="utf-8")
        updated = _set_location(text, lat, lon)

        tmp = md_path.with_suffix(".tmp")
        try:
            tmp.write_text(updated, encoding="utf-8")
            os.replace(tmp, md_path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

        rel = str(md_path.relative_to(VAULT_ROOT))
        print(f"  Updated: {rel}  [{lat}, {lon}]")
        self._json({"ok": True, "file": rel, "lat": lat, "lon": lon})

    def _rebuild(self, target: str):
        cmd = [sys.executable, str(VAULT_ROOT / "utilities" / "build.py"), target]
        print(f"  Rebuilding: {target} ...")
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(VAULT_ROOT)
        )
        ok = result.returncode == 0
        print(f"  {'OK' if ok else 'FAILED'}: {target}")
        self._json(
            {
                "ok": ok,
                "returncode": result.returncode,
                "output": result.stdout + result.stderr,
            }
        )

    # ---- Helpers ----

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length))

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        pass  # Per-request noise suppressed; important events logged explicitly


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def _find_slug(slug: str) -> "Path | None":
    for p in LOCATIONS_DIR.rglob("*.md"):
        if p.stem == slug:
            return p
    return None


def _set_location(text: str, lat: float, lon: float) -> str:
    """Update or insert `location: [lat, lon]` block in YAML frontmatter."""
    m = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not m:
        return text  # no frontmatter — leave unchanged

    fm = m.group(1)
    body = text[m.end():]
    new = f"location:\n- {lat}\n- {lon}\n"

    # Block list format: location:\n- value\n- value\n
    fm2 = re.sub(
        r"^location:\s*\n(?:[ \t]*-[^\n]*\n)+",
        new,
        fm,
        flags=re.MULTILINE,
    )
    if fm2 == fm:
        # Inline format: location: [lat, lon]
        fm2 = re.sub(r"^location:[^\n]*\n", new, fm, flags=re.MULTILINE)
    if fm2 == fm:
        # Field absent — append at end of frontmatter block
        fm2 = fm + new

    return f"---\n{fm2}---\n{body}"


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def _stale_workshop_warning() -> None:
    if not WORKSHOP_PATH.exists():
        print("  WARNING: map-workshop.html not found.")
        print("           Run: python utilities/build.py workshop")
        return
    wt = WORKSHOP_PATH.stat().st_mtime
    stale = any(p.stat().st_mtime > wt for p in LOCATIONS_DIR.rglob("*.md"))
    if stale:
        print("  WARNING: map-workshop.html is older than one or more location .md files.")
        print("           Run: python utilities/build.py workshop  to refresh it.")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Tarim-Shaïal local dev server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    port = args.port

    print("Tarim-Shaïal Dev Server")
    print(f"  Vault root:  {VAULT_ROOT}")
    print(f"  Serving:     {DOCS_DIR}")
    print(f"  Site:        http://localhost:{port}/")
    print(f"  Workshop:    http://localhost:{port}/workshop")
    print()
    print("  Endpoints:")
    print(f"    PUT  http://localhost:{port}/api/locations/{{slug}}/coordinates")
    print(f"    POST http://localhost:{port}/api/rebuild/locations")
    print(f"    POST http://localhost:{port}/api/rebuild/workshop")
    print()
    _stale_workshop_warning()
    print()
    print("  Press Ctrl-C to stop.")
    print()

    server = http.server.HTTPServer(("localhost", port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
