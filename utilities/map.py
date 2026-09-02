#!/usr/bin/env python3
"""Map workflow dispatcher for Tarim-Shaiel.

Each command adds data then automatically rebuilds the GeoJSON and workshop.

Commands:
  location [opts]   Add a location stub + rebuild GeoJSON + refresh workshop
  route    [opts]   Add route segment(s) + refresh workshop
  rebuild           Rebuild GeoJSON + refresh workshop (no new data)
  snap     [opts]   OSRM-snap route geometries + refresh workshop
  list              List all locations and route segments

Run with no arguments for an interactive TUI menu.

Examples:
    python utilities/map.py location --name "Nur-Ata" --lat 40.56 --lon 65.69 --category route-node
    python utilities/map.py route balkh dehdadi aybak baghlan charikar kabul
    python utilities/map.py route kashgar stone-ledger-gate --spur
    python utilities/map.py rebuild
    python utilities/map.py snap
    python utilities/map.py list
"""

import json
import math
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent

LOCATIONS_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-locations.geojson"
ROUTES_PATH    = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"

# ── ANSI colours (graceful fallback when not a tty) ──────────────────────────

_USE_COLOR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def bold(t: str)    -> str: return _c("1", t)
def dim(t: str)     -> str: return _c("2", t)
def cyan(t: str)    -> str: return _c("36", t)
def yellow(t: str)  -> str: return _c("33", t)
def green(t: str)   -> str: return _c("32", t)
def red(t: str)     -> str: return _c("31", t)
def magenta(t: str) -> str: return _c("35", t)

# ── env ──────────────────────────────────────────────────────────────────────

def _load_dotenv() -> None:
    env_path = VAULT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

_load_dotenv()

# ── data helpers ─────────────────────────────────────────────────────────────

def _load_location_slugs() -> list[str]:
    if not LOCATIONS_PATH.exists():
        return []
    data = json.loads(LOCATIONS_PATH.read_text(encoding="utf-8"))
    return sorted(
        f["properties"].get("slug", "") for f in data.get("features", [])
        if f["properties"].get("slug")
    )

def _load_locations_data() -> list[dict]:
    if not LOCATIONS_PATH.exists():
        return []
    data = json.loads(LOCATIONS_PATH.read_text(encoding="utf-8"))
    rows = []
    for f in data.get("features", []):
        p = f["properties"]
        coords = f["geometry"]["coordinates"]
        rows.append({
            "slug":     p.get("slug", ""),
            "label":    p.get("label") or p.get("title") or "",
            "category": p.get("category") or p.get("mapmarker") or "",
            "region":   p.get("parent_region") or p.get("region") or "",
            "lon":      coords[0],
            "lat":      coords[1],
        })
    return sorted(rows, key=lambda r: (r["region"], r["slug"]))

def _load_routes_data() -> list[dict]:
    if not ROUTES_PATH.exists():
        return []
    data = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    rows = []
    for f in data.get("features", []):
        coords = f["geometry"]["coordinates"]
        km = _path_km(coords)
        rows.append({
            "id":    f.get("id", ""),
            "label": f["properties"].get("label", ""),
            "km":    km,
            "routed": len(coords) > 2,
        })
    return sorted(rows, key=lambda r: r["id"])

def _haversine(lon1, lat1, lon2, lat2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def _path_km(coords: list) -> float:
    total = 0.0
    for i in range(len(coords) - 1):
        total += _haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return total

# ── readline completion ───────────────────────────────────────────────────────

def _setup_completion(options: list[str]) -> None:
    try:
        import readline
        matches: list[str] = []

        def completer(text: str, state: int) -> str | None:
            nonlocal matches
            if state == 0:
                matches = [o for o in options if o.startswith(text)]
            return matches[state] if state < len(matches) else None

        readline.set_completer(completer)
        readline.set_completer_delims(" \t")
        # macOS ships libedit, not GNU readline
        if "libedit" in getattr(readline, "__doc__", ""):
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
    except ImportError:
        pass  # readline unavailable — silent degradation

def _clear_completion() -> None:
    try:
        import readline
        readline.set_completer(None)
    except ImportError:
        pass

# ── step runners ─────────────────────────────────────────────────────────────

def _run(label: str, cmd: list[str]) -> bool:
    print(f"\n{bold('──')} {cyan(label)} {bold('──')}")
    result = subprocess.run([sys.executable] + cmd, cwd=str(VAULT_ROOT))
    if result.returncode != 0:
        print(f"  {red('ERROR')}: step failed (exit {result.returncode})", file=sys.stderr)
    return result.returncode == 0

def step_add_location(extra_args: list[str]) -> bool:
    return _run("add location", ["utilities/world/add_location.py"] + extra_args)

def step_add_route(extra_args: list[str]) -> bool:
    return _run("add route", ["utilities/routes/add_route.py"] + extra_args)

def step_geojson() -> bool:
    return _run("rebuild GeoJSON", ["utilities/build.py", "geojson"])

def step_snap(extra_args: list[str] | None = None) -> bool:
    return _run("snap routes (OSRM)", ["utilities/routes/generate_routes.py"] + (extra_args or []))

def step_workshop() -> bool:
    return _run("refresh workshop", ["utilities/world/generate_map_workshop.py"])

# ── commands ─────────────────────────────────────────────────────────────────

def cmd_location(args: list[str]) -> int:
    if not step_add_location(args):
        return 1
    if not step_geojson():
        return 1
    step_workshop()
    print(f"\n{green('✓')} Location added and workshop refreshed.")
    return 0

def cmd_route(args: list[str]) -> int:
    if not step_add_route(args):
        return 1
    step_snap()   # best-effort; falls back to straight line if OSRM unreachable
    step_workshop()
    print(f"\n{green('✓')} Route added, snapped to roads, and workshop refreshed.")
    return 0

def cmd_rebuild(_args: list[str]) -> int:
    if not step_geojson():
        return 1
    step_workshop()
    print(f"\n{green('✓')} GeoJSON and workshop refreshed.")
    return 0

def cmd_snap(args: list[str]) -> int:
    if not step_snap(args):
        return 1
    step_workshop()
    print(f"\n{green('✓')} Routes snapped and workshop refreshed.")
    return 0

def cmd_list(_args: list[str]) -> int:
    _print_locations()
    print()
    _print_routes()
    return 0

# ── list display ─────────────────────────────────────────────────────────────

_CAT_COLOR = {
    "city": yellow, "capital": yellow, "town": yellow,
    "sacred-site": magenta, "mythic-landscape": magenta,
    "fortress": red, "ruins": dim,
    "route-node": cyan, "caravanserai": cyan,
    "landmark": green, "water-body": green,
}

def _print_locations() -> None:
    rows = _load_locations_data()
    if not rows:
        print("No location data found.")
        return

    sw = max(len(r["slug"])     for r in rows)
    cw = max(len(r["category"]) for r in rows)

    print(bold(f"LOCATIONS ({len(rows)})"))
    print(dim(f"  {'slug':<{sw}}  {'category':<{cw}}  {'lat':>9}  {'lon':>9}"))
    print(dim(f"  {'─'*sw}  {'─'*cw}  {'─'*9}  {'─'*9}"))

    for r in rows:
        col = _CAT_COLOR.get(r["category"], lambda t: t)
        # Pad raw strings first, then colorize — keeps column alignment intact
        slug_str = f"{r['slug']:<{sw}}"
        cat_str  = col(f"{r['category']:<{cw}}")
        print(f"  {slug_str}  {cat_str}  {r['lat']:>9.4f}  {r['lon']:>9.4f}")

def _print_routes() -> None:
    rows = _load_routes_data()
    if not rows:
        print("No route data found.")
        return

    iw = max(len(r["id"])    for r in rows)
    lw = max(len(r["label"]) for r in rows)

    print(bold(f"ROUTES ({len(rows)} segments)"))
    print(dim(f"  {'id':<{iw}}  {'label':<{lw}}  {'dist':>8}  {'days':>4}  geo"))
    print(dim(f"  {'─'*iw}  {'─'*lw}  {'─'*8}  {'─'*4}  {'─'*4}"))

    for r in rows:
        km       = r["km"]
        days     = math.ceil(km / 30) if km else 0
        approx   = not r["routed"]
        dist_str = f"{'~' if approx else ''}{km:.0f} km"
        days_str = f"{days}d"
        geo_str  = green("road") if r["routed"] else dim("line")
        # Pad before colorizing
        id_str    = f"{r['id']:<{iw}}"
        label_str = dim(f"{r['label']:<{lw}}")
        dist_col  = dim(f"{dist_str:>8}") if approx else f"{dist_str:>8}"
        print(f"  {id_str}  {label_str}  {dist_col}  {days_str:>4}  {geo_str}")

# ── TUI ──────────────────────────────────────────────────────────────────────

def _prompt(label: str, default: str = "") -> str:
    suffix = dim(f" [{default}]") if default else ""
    val = input(f"  {label}{suffix}: ").strip()
    return val or default

def _prompt_slug(label: str, slugs: list[str], default: str = "") -> str:
    _setup_completion(slugs)
    try:
        val = _prompt(label, default)
    finally:
        _clear_completion()
    return val

def _prompt_slugs(label: str, slugs: list[str]) -> str:
    """Prompt for space-separated slugs with tab completion on each token."""
    _setup_completion(slugs)
    try:
        val = _prompt(label)
    finally:
        _clear_completion()
    return val

CATEGORIES = [
    "caravanserai", "capital", "city", "town", "fortress", "sacred-site",
    "ruins", "route-node", "water-body", "landmark", "mythic-landscape",
]
REGIONS = ["central-asian-hubs", "tarim-basin", "steppe", "hindu-kush",
           "persian-corridor", "ferghana-valley", "sogdiana"]

def _tui_location() -> int:
    print(f"\n{bold('── Add Location ──')}")
    name = _prompt("Name (required)")
    if not name:
        print("  Cancelled.")
        return 0
    lat  = _prompt("Latitude  (required)")
    lon  = _prompt("Longitude (required)")
    print(f"  {dim('Tab to complete category.')}")
    cat  = _prompt_slug("Category (required)", CATEGORIES)
    fantasy = _prompt("Fantasy name")
    slugs = _load_location_slugs()
    print(f"  {dim('Tab to complete region slug.')}")
    region  = _prompt_slug("Region slug", slugs)
    vis     = _prompt_slug("Visibility", ["public", "gm_secrets"], "public")
    desc    = _prompt("Description", "PLACEHOLDER — location pending. Prose pass pending.")

    args = ["--name", name, "--lat", lat, "--lon", lon, "--category", cat,
            "--visibility", vis, "--description", desc]
    if fantasy:
        args += ["--fantasy-name", fantasy]
    if region:
        args += ["--region", region]
    return cmd_location(args)

def _tui_route() -> int:
    print(f"\n{bold('── Add Route ──')}")
    slugs = _load_location_slugs()
    print(f"  Enter slugs in order, space-separated.  {dim('Tab to complete each slug.')}")
    raw = _prompt_slugs("Slugs (required)", slugs)
    if not raw:
        print("  Cancelled.")
        return 0
    spur = _prompt("Spur route?", "N").lower().startswith("y")
    args = raw.split() + (["--spur"] if spur else [])
    return cmd_route(args)

def _tui_snap() -> int:
    print(f"\n{bold('── Snap Routes (OSRM) ──')}")
    seg = _prompt("Segment ID to snap (blank = all)")
    return cmd_snap(["--segment", seg] if seg else [])

_TUI_MENU = [
    ("List locations & routes",        lambda: cmd_list([])),
    ("Add location",                   _tui_location),
    ("Add route",                      _tui_route),
    ("Rebuild GeoJSON + workshop",     lambda: cmd_rebuild([])),
    ("Snap routes to roads (OSRM)",    _tui_snap),
    ("Quit",                           None),
]

def tui() -> int:
    print(f"\n{bold('Map Workshop — Tarim-Shaiel')}")
    print("═" * 32)
    while True:
        print()
        for i, (label, _) in enumerate(_TUI_MENU, 1):
            print(f"  {dim(str(i))}.  {label}")
        choice = input(f"\n{dim('Select')} [1-{len(_TUI_MENU)}]: ").strip()
        try:
            idx = int(choice) - 1
        except ValueError:
            print(f"  {dim('Enter a number 1–' + str(len(_TUI_MENU)))}.")
            continue
        if not 0 <= idx < len(_TUI_MENU):
            print(f"  {dim('Out of range.')} ")
            continue
        _, fn = _TUI_MENU[idx]
        if fn is None:
            print("Bye.")
            return 0
        fn()

# ── entry point ───────────────────────────────────────────────────────────────

COMMANDS = {
    "location": cmd_location,
    "route":    cmd_route,
    "rebuild":  cmd_rebuild,
    "snap":     cmd_snap,
    "list":     cmd_list,
}

def main() -> int:
    args = sys.argv[1:]
    if not args:
        return tui()
    cmd = args[0]
    if cmd in ("-h", "--help"):
        print(__doc__)
        return 0
    if cmd not in COMMANDS:
        print(f"ERROR: unknown command '{cmd}'. "
              f"Choose from: {', '.join(COMMANDS)}", file=sys.stderr)
        print("Run without arguments for the interactive menu.", file=sys.stderr)
        return 1
    return COMMANDS[cmd](args[1:])

if __name__ == "__main__":
    sys.exit(main())
