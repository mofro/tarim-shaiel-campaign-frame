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
    PUT    /api/locations/{slug}/coordinates  — update lat/lon in .md frontmatter
    PATCH  /api/locations/{slug}/frontmatter  — patch name/fantasy_name/type/mapmarker/visibility
    POST   /api/locations/create              — create a new location stub
    POST   /api/routes/add                    — add route segment(s) to routes.geojson
    DELETE /api/routes/{route_id}             — delete one route by ID
    POST   /api/routes/delete-bulk            — delete multiple routes: {"ids": [...]}
    POST   /api/routes/{route_id}/regenerate  — re-snap one route to roads via OSRM
    POST   /api/rebuild/locations             — run build.py locations
    POST   /api/rebuild/workshop              — run build.py workshop
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
ROUTES_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
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

    def do_PATCH(self):
        m = re.match(r"^/api/locations/([^/?]+)/frontmatter(?:\?.*)?$", self.path)
        if m:
            self._patch_frontmatter(m.group(1))
        else:
            self.send_error(404)

    def do_DELETE(self):
        m = re.match(r"^/api/routes/([^/?]+)(?:\?.*)?$", self.path)
        if m:
            self._delete_route(m.group(1))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/locations/create":
            self._create_location()
        elif self.path == "/api/routes/add":
            self._add_route()
        elif self.path == "/api/routes/delete-bulk":
            self._delete_routes_bulk()
        elif re.match(r"^/api/routes/([^/?]+)/regenerate(?:\?.*)?$", self.path):
            m = re.match(r"^/api/routes/([^/?]+)/regenerate(?:\?.*)?$", self.path)
            self._regenerate_route(m.group(1))
        elif self.path == "/api/rebuild/locations":
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

    def _patch_frontmatter(self, slug: str):
        ALLOWED = {"name", "fantasy_name", "type", "mapmarker", "visibility"}
        try:
            data = self._read_json()
        except Exception:
            return self.send_error(400, "Invalid JSON body")

        fields = {k: v for k, v in data.items() if k in ALLOWED}
        if not fields:
            return self._json({"ok": False, "error": "no recognised fields"}, 400)

        md_path = _find_slug(slug)
        if md_path is None:
            return self._json({"ok": False, "error": f"slug not found: {slug}"}, 404)

        text = md_path.read_text(encoding="utf-8")
        updated = _set_frontmatter_fields(text, fields)

        tmp = md_path.with_suffix(".tmp")
        try:
            tmp.write_text(updated, encoding="utf-8")
            os.replace(tmp, md_path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

        rel = str(md_path.relative_to(VAULT_ROOT))
        print(f"  Patched: {rel}  {list(fields.keys())}")
        self._json({"ok": True, "file": rel, "fields": list(fields.keys())})

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

    def _create_location(self):
        try:
            data = self._read_json()
            name = str(data.get("name", "")).strip()
            lat  = float(data["lat"])
            lon  = float(data["lon"])
            cat  = str(data.get("category", "")).strip()
        except (ValueError, KeyError, TypeError):
            return self.send_error(400, 'Body must include name, lat, lon, category')
        if not name or not cat:
            return self._json({"ok": False, "error": "name and category are required"}, 400)

        cmd = [
            sys.executable, str(VAULT_ROOT / "utilities" / "map.py"), "location",
            "--name", name, "--lat", str(lat), "--lon", str(lon), "--category", cat,
        ]
        fantasy = str(data.get("fantasy_name", "")).strip()
        if fantasy:
            cmd += ["--fantasy-name", fantasy]
        region = str(data.get("region", "")).strip()
        if region:
            cmd += ["--region", region]
        vis = str(data.get("visibility", "public")).strip()
        if vis:
            cmd += ["--visibility", vis]
        desc = str(data.get("description", "")).strip()
        if desc:
            cmd += ["--description", desc]

        print(f"  Creating location: {name!r} ...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(VAULT_ROOT))
        ok = result.returncode == 0
        print(f"  {'OK' if ok else 'FAILED'}: create location {name!r}")
        self._json({
            "ok": ok,
            "returncode": result.returncode,
            "output": result.stdout + result.stderr,
        })

    def _add_route(self):
        try:
            data = self._read_json()
            slugs = [str(s) for s in data["slugs"]]
            spur  = bool(data.get("spur", False))
            name  = str(data.get("name", "")).strip()
            description = str(data.get("description", "")).strip()
            route_type = str(data.get("routeType", "")).strip()
        except (ValueError, KeyError, TypeError):
            return self.send_error(400, 'Body must include slugs array')
        if len(slugs) < 2:
            return self._json({"ok": False, "error": "at least 2 slugs required"}, 400)

        cmd = [sys.executable, str(VAULT_ROOT / "utilities" / "map.py"), "route"] + slugs
        if spur:
            cmd.append("--spur")
        if name:
            cmd += ["--name", name]
        if description:
            cmd += ["--description", description]
        if route_type:
            cmd += ["--route-type", route_type]

        print(f"  Adding route: {' → '.join(slugs)} ...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(VAULT_ROOT))
        ok = result.returncode == 0
        print(f"  {'OK' if ok else 'FAILED'}: add route")
        self._json({
            "ok": ok,
            "returncode": result.returncode,
            "output": result.stdout + result.stderr,
        })

    def _delete_route(self, route_id: str):
        if not ROUTES_PATH.exists():
            return self._json({"ok": False, "error": "routes.geojson not found"}, 404)
        gj = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
        features = gj.get("features", [])
        gj["features"] = [f for f in features if f.get("id") != route_id]
        if len(gj["features"]) == len(features):
            return self._json({"ok": False, "error": f"route not found: {route_id}"}, 404)
        tmp = ROUTES_PATH.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(gj, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, ROUTES_PATH)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"  Deleted route: {route_id}")
        self._json({"ok": True, "deleted": route_id})

    def _delete_routes_bulk(self):
        try:
            data = self._read_json()
            ids = [str(i) for i in data["ids"]]
        except (ValueError, KeyError, TypeError):
            return self.send_error(400, 'Body must be {"ids": [...]}')
        if not ids:
            return self._json({"ok": False, "error": "ids array is empty"}, 400)
        if not ROUTES_PATH.exists():
            return self._json({"ok": False, "error": "routes.geojson not found"}, 404)
        id_set = set(ids)
        gj = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
        features = gj.get("features", [])
        deleted = [f["id"] for f in features if f.get("id") in id_set]
        gj["features"] = [f for f in features if f.get("id") not in id_set]
        tmp = ROUTES_PATH.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(gj, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, ROUTES_PATH)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"  Deleted {len(deleted)} route(s): {', '.join(deleted)}")
        self._json({"ok": True, "deleted": deleted, "count": len(deleted)})

    def _regenerate_route(self, route_id: str):
        if not ROUTES_PATH.exists():
            return self._json({"ok": False, "error": "routes.geojson not found"}, 404)
        gj = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
        if not any(f.get("id") == route_id for f in gj.get("features", [])):
            return self._json({"ok": False, "error": f"route not found: {route_id}"}, 404)

        cmd = [
            sys.executable, str(VAULT_ROOT / "utilities" / "routes" / "generate_routes.py"),
            "--segment", route_id, "--force",
        ]
        print(f"  Regenerating route: {route_id} ...")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(VAULT_ROOT))
        ok = result.returncode == 0
        print(f"  {'OK' if ok else 'FAILED'}: regenerate route {route_id}")
        self._json({
            "ok": ok,
            "returncode": result.returncode,
            "output": result.stdout + result.stderr,
        })

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
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, PATCH, POST, DELETE, OPTIONS")
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


def _yaml_scalar(value) -> str:
    """Format a Python value as a safe YAML scalar string."""
    if value is None:
        return "~"
    if isinstance(value, bool):
        return "true" if value else "false"
    s = str(value)
    # Quote if the value contains YAML special characters or looks like a bool/null
    needs_quote = (
        not s
        or s.lower() in ("true", "false", "null", "~", "yes", "no", "on", "off")
        or any(c in s for c in ":#\n[]{}|>&*!,%@`'\"")
    )
    if needs_quote:
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s


def _set_frontmatter_fields(text: str, fields: dict) -> str:
    """Patch named scalar fields in YAML frontmatter.

    Handles name, fantasy_name, type, mapmarker, visibility.
    Uses regex line-replacement so block scalars elsewhere are untouched.
    """
    m = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not m:
        return text  # no frontmatter
    fm = m.group(1)
    body = text[m.end():]

    for key, value in fields.items():
        if key == "name":
            # The parser accepts title: or name:; update whichever is present
            scalar = _yaml_scalar(value)
            new_title = f"title: {scalar}\n"
            new_name  = f"name: {scalar}\n"
            fm2 = re.sub(r"^title:[^\n]*\n", new_title, fm, flags=re.MULTILINE)
            if fm2 != fm:
                fm = fm2
            else:
                fm2 = re.sub(r"^name:[^\n]*\n", new_name, fm, flags=re.MULTILINE)
                fm = fm2 if fm2 != fm else fm + new_title
        elif value is None:
            # Remove field entirely
            fm = re.sub(rf"^{re.escape(key)}:[^\n]*\n", "", fm, flags=re.MULTILINE)
        else:
            scalar = _yaml_scalar(value)
            new_line = f"{key}: {scalar}\n"
            fm2 = re.sub(rf"^{re.escape(key)}:[^\n]*\n", new_line, fm, flags=re.MULTILINE)
            fm = fm2 if fm2 != fm else fm + new_line

    # Bump last_updated
    today = __import__("datetime").date.today().isoformat()
    fm = re.sub(r"^last_updated:[^\n]*\n", f"last_updated: {today}\n", fm, flags=re.MULTILINE)

    return f"---\n{fm}---\n{body}"


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
    print(f"    PUT    http://localhost:{port}/api/locations/{{slug}}/coordinates")
    print(f"    POST   http://localhost:{port}/api/locations/create")
    print(f"    POST   http://localhost:{port}/api/routes/add")
    print(f"    DELETE http://localhost:{port}/api/routes/{{route_id}}")
    print(f"    POST   http://localhost:{port}/api/routes/delete-bulk")
    print(f"    POST   http://localhost:{port}/api/rebuild/locations")
    print(f"    POST   http://localhost:{port}/api/rebuild/workshop")
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
