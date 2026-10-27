#!/usr/bin/env python3
"""
Tarim-Shaïal local development server.

Replaces 'python -m http.server' for interactive authoring sessions.
Serves docs/ as the main site, the map workshop at /workshop, and
exposes write-back API endpoints for coordinate updates and rebuilds.

Usage (use the project venv — rebuild endpoints spawn build.py with this
interpreter, and build.py needs PyYAML):
    venv/bin/python utilities/devserver.py [--port PORT]
    Site:     http://localhost:8000/
    Workshop: http://localhost:8000/workshop

Endpoints:
    PUT    /api/locations/{slug}/coordinates  — update lat/lon in .md frontmatter
    PATCH  /api/locations/{slug}/frontmatter  — patch name/fantasy_name/type/mapmarker/visibility
    PATCH  /api/routes/{route_id}             — set one route's visibility (public|gm_secrets) or mode
    POST   /api/locations/create              — create a new location stub
    POST   /api/routes/add                    — add route segment(s) to routes.geojson
    DELETE /api/routes/{route_id}             — delete one route by ID
    POST   /api/routes/delete-bulk            — delete multiple routes: {"ids": [...]}
    POST   /api/routes/{route_id}/regenerate  — re-snap one route to roads via OSRM
    GET    /api/journeys                      — saved travel journeys + their popup text (localhost only)
    POST   /api/journeys                      — save a new journey (gm_secrets until made public)
    PUT    /api/journeys/{id}                 — overwrite a journey's name, stops and legs
    PATCH  /api/journeys/{id}                 — rename a journey or set its visibility
    DELETE /api/journeys/{id}                 — delete one journey
    POST   /api/rebuild/locations             — run build.py locations
    POST   /api/rebuild/workshop              — run build.py workshop
"""

import http.server
import json
import os
import re
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared.travel_time import SPEEDS
from shared import journeys as journeys_mod
VAULT_ROOT = SCRIPT_DIR.parent
DOCS_DIR = VAULT_ROOT / "docs"
WORKSHOP_PATH = VAULT_ROOT / "map-workshop.html"
PLAYER_PATH = VAULT_ROOT / "player-map.html"
LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
ROUTES_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
JOURNEYS_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-journeys.geojson"
DEFAULT_PORT = 8000

# Route properties the Workshop may change, and the values each accepts.
ROUTE_PATCH_VALUES = {
    "visibility": ("public", "gm_secrets"),
    "mode": tuple(SPEEDS),
}


def _patch_route_props(route_id: str, data: dict) -> "tuple[int, dict]":
    """Set whitelisted properties on one route; (HTTP status, JSON body).

    Rewrites routes.geojson with the same serialization the other route writers
    use, so a one-property change is a one-line git diff.
    """
    fields = {k: v for k, v in data.items() if k in ROUTE_PATCH_VALUES}
    if not fields:
        return 400, {"ok": False, "error": "no recognised fields"}
    for key, value in fields.items():
        if value not in ROUTE_PATCH_VALUES[key]:
            return 400, {"ok": False,
                         "error": f"{key} must be one of {', '.join(ROUTE_PATCH_VALUES[key])}"}
    if not ROUTES_PATH.exists():
        return 404, {"ok": False, "error": "routes.geojson not found"}
    gj = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    feat = next((f for f in gj.get("features", []) if f.get("id") == route_id), None)
    if feat is None:
        return 404, {"ok": False, "error": f"route not found: {route_id}"}
    feat.setdefault("properties", {}).update(fields)
    tmp = ROUTES_PATH.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(gj, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, ROUTES_PATH)
    finally:
        tmp.unlink(missing_ok=True)
    return 200, {"ok": True, "id": route_id, "fields": fields}


# Journey store calls: each returns (HTTP status, JSON body). The store owns
# validation and the atomic write; a rejected request never touches the file.

def _journey_body(feat: dict) -> dict:
    return {"ok": True, "journey": feat, "popup": journeys_mod.popup_info(feat)}


def _journey_list() -> "tuple[int, dict]":
    gj = journeys_mod.load(JOURNEYS_PATH)
    popups = {f["id"]: journeys_mod.popup_info(f) for f in gj.get("features", [])}
    return 200, {**gj, "popups": popups}


def _journey_create(data) -> "tuple[int, dict]":
    try:
        return 201, _journey_body(journeys_mod.create(JOURNEYS_PATH, data))
    except journeys_mod.JourneyError as e:
        return 400, {"ok": False, "error": str(e)}


def _journey_replace(jid: str, data) -> "tuple[int, dict]":
    try:
        feat = journeys_mod.replace(JOURNEYS_PATH, jid, data)
    except journeys_mod.JourneyError as e:
        return 400, {"ok": False, "error": str(e)}
    if feat is None:
        return 404, {"ok": False, "error": f"journey not found: {jid}"}
    return 200, _journey_body(feat)


def _journey_patch(jid: str, data) -> "tuple[int, dict]":
    try:
        feat = journeys_mod.patch(JOURNEYS_PATH, jid, data)
    except journeys_mod.JourneyError as e:
        return 400, {"ok": False, "error": str(e)}
    if feat is None:
        return 404, {"ok": False, "error": f"journey not found: {jid}"}
    return 200, _journey_body(feat)


def _journey_delete(jid: str) -> "tuple[int, dict]":
    if not journeys_mod.delete(JOURNEYS_PATH, jid):
        return 404, {"ok": False, "error": f"journey not found: {jid}"}
    return 200, {"ok": True, "deleted": jid}


# ---------------------------------------------------------------------------
# Shared state (GIL protects simple assignment; no heavy concurrency needed)
# ---------------------------------------------------------------------------

_map_center: "dict | None" = None  # {"lng": float, "lat": float, "zoom": float}
_lan_ip: str = "127.0.0.1"         # set at startup


def _detect_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


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

    def _is_local(self) -> bool:
        return self.client_address[0] in ("127.0.0.1", "::1")

    def do_GET(self):
        if self.path == "/api/health":
            self._json({
                "ok": True,
                "lan_ip": _lan_ip,
                "player_url": f"http://{_lan_ip}:{self.server.server_port}/player",
            })
        elif self.path.rstrip("/") == "/workshop":
            if not self._is_local():
                self.send_error(403, "Workshop is only accessible from localhost")
                return
            self._serve_workshop()
        elif self.path.rstrip("/") == "/player":
            self._serve_player()
        elif self.path == "/api/map-center":
            self._json(_map_center if _map_center else {"lng": None, "lat": None, "zoom": None})
        elif self.path.split("?")[0].rstrip("/") == "/api/journeys":
            if not self._is_local():
                self.send_error(403, "Journeys are only accessible from localhost")
                return
            self._respond(*_journey_list())
        elif self.path.startswith("/api/maptiler-proxy"):
            self._maptiler_proxy()
        else:
            super().do_GET()

    def do_PUT(self):
        if not self._is_local():
            self.send_error(403, "Write API only accessible from localhost")
            return
        m = re.match(r"^/api/locations/([^/?]+)/coordinates(?:\?.*)?$", self.path)
        if m:
            self._put_coordinates(m.group(1))
            return
        m = re.match(r"^/api/journeys/([^/?]+)(?:\?.*)?$", self.path)
        if m:
            self._journey_write(_journey_replace, urllib.parse.unquote(m.group(1)))
        else:
            self.send_error(404)

    def do_PATCH(self):
        if not self._is_local():
            self.send_error(403, "Write API only accessible from localhost")
            return
        m = re.match(r"^/api/locations/([^/?]+)/frontmatter(?:\?.*)?$", self.path)
        if m:
            self._patch_frontmatter(m.group(1))
            return
        m = re.match(r"^/api/routes/([^/?]+)(?:\?.*)?$", self.path)
        if m:
            self._patch_route(urllib.parse.unquote(m.group(1)))
            return
        m = re.match(r"^/api/journeys/([^/?]+)(?:\?.*)?$", self.path)
        if m:
            self._journey_write(_journey_patch, urllib.parse.unquote(m.group(1)))
        else:
            self.send_error(404)

    def do_DELETE(self):
        if not self._is_local():
            self.send_error(403, "Write API only accessible from localhost")
            return
        m = re.match(r"^/api/routes/([^/?]+)(?:\?.*)?$", self.path)
        if m:
            self._delete_route(m.group(1))
            return
        m = re.match(r"^/api/journeys/([^/?]+)(?:\?.*)?$", self.path)
        if m:
            self._respond(*_journey_delete(urllib.parse.unquote(m.group(1))))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/map-center":
            if not self._is_local():
                return self.send_error(403, "Only GM (localhost) can set map center")
            self._set_map_center()
            return
        if not self._is_local():
            self.send_error(403, "Write API only accessible from localhost")
            return
        if self.path == "/api/locations/create":
            self._create_location()
        elif self.path.split("?")[0].rstrip("/") == "/api/journeys":
            self._journey_write(_journey_create)
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

    def _serve_player(self):
        if not PLAYER_PATH.exists():
            self.send_error(
                404,
                "Player map not built — run: python utilities/world/generate_map_workshop.py",
            )
            return
        body = PLAYER_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _maptiler_proxy(self):
        """Proxy a MapTiler API request server-side to avoid key domain restrictions."""
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        target_url = qs.get("url", [None])[0]
        if not target_url:
            return self.send_error(400, "Missing ?url= parameter")
        # parse_qs decodes %20 → literal space; re-encode so urlopen accepts the URL
        target_url = urllib.parse.quote(target_url, safe=":/?=&#@,+")
        if not target_url.startswith("https://api.maptiler.com/"):
            return self.send_error(403, "Only maptiler.com URLs are proxied")
        try:
            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                    "Referer": "http://localhost:8000/",
                    "Origin": "http://localhost:8000",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()
                ct = resp.headers.get("Content-Type", "application/octet-stream")
        except urllib.error.HTTPError as exc:
            import sys
            short = target_url.split("?")[0].split("/tiles/")[-1] if "/tiles/" in target_url else target_url[-40:]
            print(f"[proxy] {exc.code} {short}", file=sys.stderr, flush=True)
            return self.send_error(502, f"Upstream error: {exc}")
        except Exception as exc:
            import sys
            print(f"[proxy] ERR {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
            return self.send_error(502, f"Upstream error: {exc}")
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _set_map_center(self):
        global _map_center
        try:
            data = self._read_json()
            lng = float(data["lng"])
            lat = float(data["lat"])
            zoom = float(data.get("zoom", 4))
        except (ValueError, KeyError, TypeError):
            return self.send_error(400, 'Body must be {"lng": number, "lat": number, "zoom": number}')
        _map_center = {"lng": lng, "lat": lat, "zoom": zoom}
        self._json({"ok": True})

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

    def _patch_route(self, route_id: str):
        try:
            data = self._read_json()
        except Exception:
            return self.send_error(400, "Invalid JSON body")
        status, body = _patch_route_props(route_id, data)
        if status == 200:
            print(f"  Patched route: {route_id}  {body['fields']}")
        self._json(body, status)

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

    def _journey_write(self, fn, *ids):
        try:
            data = self._read_json()
        except Exception:
            return self.send_error(400, "Invalid JSON body")
        status, body = fn(*ids, data)
        if status < 300:
            print(f"  Journey {fn.__name__[9:]}: {body['journey']['id']}")
        self._respond(status, body)

    # ---- Helpers ----

    def _respond(self, status: int, body: dict):
        self._json(body, status)

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


def _replace_first(fm: str, pattern: str, new: str) -> "tuple[str, bool]":
    """Replace the first match of `pattern` in `fm` with `new`; drop any later matches.

    Returns (frontmatter, matched). "Matched" is a count, not "the text changed":
    writing back an identical line must not read as "key absent", or the caller
    appends a duplicate. Dropping later matches heals a key that is already doubled.
    """
    hits = list(re.finditer(pattern, fm, flags=re.MULTILINE))
    if not hits:
        return fm, False
    out = fm[:hits[0].start()] + new
    pos = hits[0].end()
    for h in hits[1:]:
        out += fm[pos:h.start()]
        pos = h.end()
    return out + fm[pos:], True


def _set_location(text: str, lat: float, lon: float) -> str:
    """Update or insert `location: [lat, lon]` block in YAML frontmatter."""
    m = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not m:
        return text  # no frontmatter — leave unchanged

    fm = m.group(1)
    body = text[m.end():]
    new = f"location:\n- {lat}\n- {lon}\n"

    # Block list format: location:\n- value\n- value\n
    fm2, found = _replace_first(fm, r"^location:\s*\n(?:[ \t]*-[^\n]*\n)+", new)
    if not found:
        # Inline format: location: [lat, lon]
        fm2, found = _replace_first(fm, r"^location:[^\n]*\n", new)
    if not found:
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
            fm, found = _replace_first(fm, r"^title:[^\n]*\n", new_title)
            if not found:
                fm, found = _replace_first(fm, r"^name:[^\n]*\n", new_name)
            if not found:
                fm += new_title
        elif value is None:
            # Remove field entirely
            fm = re.sub(rf"^{re.escape(key)}:[^\n]*\n", "", fm, flags=re.MULTILINE)
        else:
            scalar = _yaml_scalar(value)
            new_line = f"{key}: {scalar}\n"
            fm, found = _replace_first(fm, rf"^{re.escape(key)}:[^\n]*\n", new_line)
            if not found:
                fm += new_line

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


def _require_pyyaml() -> None:
    try:
        import yaml  # noqa: F401
    except ImportError:
        sys.exit(
            f"ERROR: PyYAML is not installed for {sys.executable}\n"
            "  Write endpoints spawn build.py with this same interpreter, so every\n"
            "  rebuild would fail after the .md file had already been written.\n"
            "  Start the server with the project venv instead:\n"
            "    venv/bin/python utilities/devserver.py"
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Tarim-Shaïal local dev server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    port = args.port

    _require_pyyaml()

    global _lan_ip
    _lan_ip = _detect_lan_ip()

    print("Tarim-Shaïal Dev Server")
    print(f"  Vault root:  {VAULT_ROOT}")
    print(f"  Serving:     {DOCS_DIR}")
    print(f"  Site:        http://localhost:{port}/")
    print(f"  Workshop:    http://localhost:{port}/workshop  (localhost only)")
    print(f"  Player map:  http://{_lan_ip}:{port}/player  ← share this with players")
    print()
    print("  Endpoints (write APIs: localhost only):")
    print(f"    PUT    http://localhost:{port}/api/locations/{{slug}}/coordinates")
    print(f"    POST   http://localhost:{port}/api/locations/create")
    print(f"    POST   http://localhost:{port}/api/routes/add")
    print(f"    PATCH  http://localhost:{port}/api/routes/{{route_id}}")
    print(f"    DELETE http://localhost:{port}/api/routes/{{route_id}}")
    print(f"    POST   http://localhost:{port}/api/routes/delete-bulk")
    print(f"    POST   http://localhost:{port}/api/rebuild/locations")
    print(f"    POST   http://localhost:{port}/api/rebuild/workshop")
    print(f"    POST   http://localhost:{port}/api/map-center  (GM position sync)")
    print()
    _stale_workshop_warning()
    print()
    print("  Press Ctrl-C to stop.")
    print()

    server = http.server.ThreadingHTTPServer(("", port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
