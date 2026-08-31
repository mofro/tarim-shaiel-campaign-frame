#!/usr/bin/env python3
"""
Tarim-Shaiel Build Dispatcher
==============================
Single entry point for the Tarim-Shaiel HTML publishing pipeline.

Usage:
    python utilities/build.py list
    python utilities/build.py all
    python utilities/build.py all --public
    python utilities/build.py campaign-frame
    python utilities/build.py ancestry lore
    python utilities/build.py lore --source narrative/lore/The Roads.md
    python utilities/build.py search-index search

Commands:
    list            Print all registered generators with their descriptions
    all             Run every generator in pipeline order
    <name> ...      Run one or more named generators

Options:
    --source PATH   Source file for generators that require one (lore, world)
    --public        Pass --public to world-all and search-index (omit GM-only content)
    --out PATH      Override output path for a single generator

Registered generators (in pipeline order):
    homepage        Site homepage
    dashboard       Project health dashboard from TODO.md
    campaign-frame  Campaign frame HTML
    lore            Styled lore HTML (requires --source or uses default)
    ancestry        Peoples of Tarim-Shaiel ancestry page
    search-index    Search index JSON (docs/search-index.json)
    search          Search UI page (docs/search.html)
    world           Single world/myth/timeline doc (requires --source)
    world-all       Batch all world docs + index
    geojson         Location GeoJSON (world/data/tarim-shaiel-locations.geojson)
    locations       Location detail pages, region indexes, and world home map
    workshop        Map workshop HTML (requires MAPTILER_KEY; skipped when absent)

The LegendKeeper pipeline (generate_lk_json, generate_lk_markdown) is
handled separately by utilities/legendkeeper-pipeline/publish.py.

Build pipeline:
    1. _copy_css()  — copies utilities/shared/css/*.css → docs/assets/css/
    2. _copy_js()   — copies utilities/shared/js/*.js  → docs/assets/js/
                      (downloads lunr.min.js on first run if not present)
    3. Run requested generators in order
"""

import os
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))

# ---------------------------------------------------------------------------
# Default source paths (mirrors netlify.toml build command)
# ---------------------------------------------------------------------------

LORE_DEFAULT_SOURCE = VAULT_ROOT / "narrative" / "lore" / "The Roads.md"

# ---------------------------------------------------------------------------
# Generator registry — import order = pipeline order
# ---------------------------------------------------------------------------

def _load_registry() -> dict:
    from homepage.generate_homepage import generator as homepage
    from dashboard.generate_dashboard import generator as dashboard
    from campaign_frame.generate_campaign_frame import generator as campaign_frame
    from lore.generate_lore_html import generator as lore
    from ancestries.generate_ancestry_html import generator as ancestry
    from class_primer.generate_class_primer import generator as class_primer
    from search.generate_search_index import generator as search_index
    from search.generate_search_html import generator as search
    from world.generate_world_html import generator as world
    from world.generate_all_world_html import generator as world_all
    from geojson.generate_geojson import generator as geojson
    from locations.generate_locations_html import generator as locations
    from sessions.generate_sessions_html import generator as sessions
    from newspaper.generate_newspaper_html import generator as newspaper
    from world.generate_map_workshop import generator as workshop

    return {
        g.name: g for g in [
            homepage, dashboard, campaign_frame, lore, ancestry, class_primer,
            search_index, search, world, world_all, geojson, locations, sessions,
            newspaper, workshop,
        ]
    }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_one(name: str, generator, args: argparse.Namespace) -> int:
    """Build the argv list for this generator and call generator.run()."""
    argv = []

    if name == "lore":
        source = args.source or str(LORE_DEFAULT_SOURCE)
        argv = ["--source", source]
        if args.out:
            argv += ["--out", args.out]

    elif name == "world":
        if not args.source:
            print(f"ERROR: 'world' generator requires --source <path>", file=sys.stderr)
            return 1
        argv = [args.source]
        if args.out:
            argv += ["--out", args.out]

    elif name in ("search-index", "search"):
        if args.public:
            argv = ["--public"]
        elif args.gm:
            argv = ["--gm"]

    elif name == "world-all":
        if args.public:
            argv = ["--public"]
        elif args.gm:
            argv = ["--gm"]
        if args.out:
            argv += ["--out", args.out]

    elif name == "geojson":
        if args.public:
            argv = ["--public"]
        elif args.gm:
            argv = ["--gm"]

    elif name == "locations":
        if args.public:
            argv = ["--public"]
        elif args.gm:
            argv = ["--gm"]

    elif name == "workshop":
        # The workshop generator hard-exits (rc=1) when MAPTILER_KEY is absent,
        # which would abort the whole 'all' pipeline. Pre-check here so 'all'
        # treats a missing key as a soft skip rather than a fatal failure.
        # By this point, location_components._load_dotenv() has already run
        # (it fires at import time), so os.environ reflects any .env file too.
        if not os.environ.get("MAPTILER_KEY", ""):
            print("  WARNING: MAPTILER_KEY not set — skipping workshop build", file=sys.stderr)
            return 0

    else:
        if args.out:
            argv += ["--out", args.out]

    rc = generator.run(argv)
    return rc if isinstance(rc, int) else 0


def _cmd_list(registry: dict) -> int:
    print("Registered generators (pipeline order):\n")
    for name, g in registry.items():
        print(f"  {name:<16} {g.description}")
    return 0


def _copy_assets() -> None:
    """Copy utilities/assets/*.json to docs/assets/ (e.g. map-style.json)."""
    import shutil
    src = SCRIPT_DIR / "assets"
    dst = VAULT_ROOT / "docs" / "assets"
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*.json"):
        shutil.copy2(f, dst / f.name)


def _copy_css() -> None:
    """Copy all *.css from utilities/shared/css/ to docs/assets/css/."""
    import shutil
    src = SCRIPT_DIR / "shared" / "css"
    dst = VAULT_ROOT / "docs" / "assets" / "css"
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*.css"):
        shutil.copy2(f, dst / f.name)


def _download_lunr(dest: Path) -> None:
    """Download lunr.min.js from CDN into utilities/shared/js/."""
    import urllib.request
    url = "https://cdn.jsdelivr.net/npm/lunr@2.3.9/lunr.min.js"
    print(f"  Downloading lunr.min.js from CDN → {dest.name}")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  lunr.min.js downloaded ({dest.stat().st_size} bytes)")
    except Exception as e:
        print(f"  WARNING: Could not download lunr.min.js: {e}", file=sys.stderr)
        print(f"  Search page will use CDN fallback. Vendor manually to remove CDN dependency.",
              file=sys.stderr)


def _copy_js() -> None:
    """Copy all *.js from utilities/shared/js/ to docs/assets/js/.

    Downloads lunr.min.js on first run if not already vendored.
    """
    import shutil
    src = SCRIPT_DIR / "shared" / "js"
    src.mkdir(parents=True, exist_ok=True)
    dst = VAULT_ROOT / "docs" / "assets" / "js"
    dst.mkdir(parents=True, exist_ok=True)

    lunr_src = src / "lunr.min.js"
    if not lunr_src.exists():
        _download_lunr(lunr_src)

    for f in src.glob("*.js"):
        shutil.copy2(f, dst / f.name)


def _cmd_run(names: list[str], registry: dict, args: argparse.Namespace) -> int:
    _copy_assets()
    _copy_css()
    _copy_js()
    if args.gm:
        os.environ['TS_GM_MODE'] = '1'
    if args.standalone:
        os.environ['TS_STANDALONE'] = '1'
    failed = []
    for name in names:
        if name not in registry:
            print(f"ERROR: unknown generator {name!r}. Run 'build.py list' to see options.",
                  file=sys.stderr)
            failed.append(name)
            continue
        print(f"\n{'─' * 60}")
        print(f"  Running: {name}")
        print(f"{'─' * 60}")
        rc = _run_one(name, registry[name], args)
        if rc != 0:
            print(f"  FAILED: {name} (exit {rc})", file=sys.stderr)
            failed.append(name)
    if failed:
        print(f"\nFailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="Tarim-Shaiel HTML publishing dispatcher.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "targets", nargs="*",
        help="Generator name(s) to run, or 'list' / 'all'"
    )
    parser.add_argument(
        "--source", "-s", default=None,
        help="Source .md file (for lore and world generators)"
    )
    parser.add_argument(
        "--out", "-o", default=None,
        help="Override output path (single-generator runs only)"
    )
    parser.add_argument(
        "--public", action="store_true",
        help="Pass --public to world-all (omit GM content)"
    )
    parser.add_argument(
        "--gm", action="store_true",
        help="GM mode: include all docs with GM markers + auth guard; sets TS_GM_MODE=1"
    )
    parser.add_argument(
        "--standalone", action="store_true",
        help=(
            "Inline all CSS into <style> blocks instead of linking external files. "
            "Produces portable HTML that works offline or as a printable document. "
            "Sets TS_STANDALONE=1. Does not affect Netlify output when omitted."
        ),
    )

    args = parser.parse_args()

    if not args.targets:
        parser.print_help()
        return 0

    registry = _load_registry()

    if args.targets == ["list"]:
        return _cmd_list(registry)

    if args.targets == ["all"]:
        # 'world' requires --source so is excluded from the full pipeline run;
        # invoke it explicitly: build.py world --source path/to/doc.md
        pipeline = [k for k in registry if k != "world"]
        return _cmd_run(pipeline, registry, args)

    return _cmd_run(args.targets, registry, args)


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# Generator protocol wrapper (so build.py itself is usable as a generator)
# ---------------------------------------------------------------------------
from shared.base_generator import make_generator
generator = make_generator(
    "build",
    "Tarim-Shaiel build dispatcher (run all or named generators)",
    main,
)
