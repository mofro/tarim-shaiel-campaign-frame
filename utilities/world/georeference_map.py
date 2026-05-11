#!/usr/bin/env python3
"""
Georeferencing helper for the Tarim-Shaiel Wonderdraft map.

Usage:
    # After filling in GCPS pixel coordinates below:
    python georeference_map.py
    python georeference_map.py --image images/places/maps/reference_map.png
    python georeference_map.py --target images/places/maps/tarim-shaiel.wonderdraft_map.png

Workflow:
    1. Open reference_map.png in any image viewer.
    2. Record pixel (x, y) for each known city and fill them into GCPS below.
    3. Run the script — it prints bounds, a GDAL command, and a MapLibre snippet.
    4. Copy the bounds into HeroHeaven-w8t (Wonderdraft base layer task).
"""

import argparse
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ground Control Points
# Fill in pixel_x and pixel_y by opening reference_map.png and clicking each city.
# Leave as None for cities not visible on the map.
# ---------------------------------------------------------------------------

GCPS = [
    # (pixel_x, pixel_y, lat_deg, lng_deg)
    (None, None, 39.47, 75.99),   # Kashgar
    (None, None, 39.65, 66.97),   # Samarkand
    (None, None, 40.15, 94.67),   # Dunhuang
    (None, None, 34.27, 108.93),  # Chang'an (comment out if not visible)
]

DEFAULT_IMAGE = Path(__file__).parent.parent.parent / "images/places/maps/reference_map.png"


# ---------------------------------------------------------------------------
# Math (no numpy — ordinary least squares for y = a*x + b)
# ---------------------------------------------------------------------------

def _fit_linear(xs, ys):
    """Return (a, b) for y = a*x + b via OLS. Requires len >= 2."""
    n = len(xs)
    sx  = sum(xs)
    sy  = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    det = n * sxx - sx * sx
    if abs(det) < 1e-12:
        sys.exit("Error: GCP x-coordinates are collinear — add more spread.")
    a = (n * sxy - sx * sy) / det
    b = (sy - a * sx) / n
    return a, b


def _rmse(xs, ys, a, b):
    residuals = [y - (a * x + b) for x, y in zip(xs, ys)]
    return math.sqrt(sum(r * r for r in residuals) / len(residuals))


def compute_bounds(gcps, img_w, img_h):
    """
    Fit linear models: lng = a*px + b, lat = c*py + d.
    Evaluate at all four image corners and return (sw, ne) bounds.
    """
    pxs = [g[0] for g in gcps]
    pys = [g[1] for g in gcps]
    lats = [g[2] for g in gcps]
    lngs = [g[3] for g in gcps]

    a_lng, b_lng = _fit_linear(pxs, lngs)
    a_lat, b_lat = _fit_linear(pys, lats)

    # Evaluate at corners
    corner_lngs = [a_lng * px + b_lng for px in (0, img_w)]
    corner_lats = [a_lat * py + b_lat for py in (0, img_h)]

    sw = (min(corner_lats), min(corner_lngs))
    ne = (max(corner_lats), max(corner_lngs))

    rmse_lng = _rmse(pxs, lngs, a_lng, b_lng)
    rmse_lat = _rmse(pys, lats, a_lat, b_lat)

    return sw, ne, rmse_lat, rmse_lng


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def print_report(label, img_path, img_w, img_h, gcps):
    sw, ne, rmse_lat, rmse_lng = compute_bounds(gcps, img_w, img_h)
    sw_lat, sw_lng = sw
    ne_lat, ne_lng = ne

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {img_path}  ({img_w} × {img_h} px)")
    print(f"{'='*60}")

    if len(gcps) >= 3:
        print(f"\nResiduals (fit quality)")
        print(f"  lat RMSE : {rmse_lat:.4f}°")
        print(f"  lng RMSE : {rmse_lng:.4f}°")
        if rmse_lat > 1.0 or rmse_lng > 1.0:
            print("  ⚠ RMSE > 1° — check pixel coordinates or add more GCPs")
    else:
        print("\n(Only 2 GCPs — residuals not computable; add a third for confidence)")

    print(f"\nBounds")
    print(f"  SW  : [{sw_lat:.6f}, {sw_lng:.6f}]")
    print(f"  NE  : [{ne_lat:.6f}, {ne_lng:.6f}]")
    print(f"  JSON: [[{sw_lat:.6f}, {sw_lng:.6f}], [{ne_lat:.6f}, {ne_lng:.6f}]]")

    print(f"\nGDAL command")
    print(f"  gdal_translate -of GTiff \\")
    print(f"    -a_srs EPSG:4326 \\")
    print(f"    -a_ullr {sw_lng:.6f} {ne_lat:.6f} {ne_lng:.6f} {sw_lat:.6f} \\")
    print(f"    {img_path} output_georef.tif")

    print(f"\nMapLibre maxBounds snippet")
    print(f"  maxBounds: [[{sw_lng:.4f}, {sw_lat:.4f}], [{ne_lng:.4f}, {ne_lat:.4f}]],")

    print(f"\nMapTiler upload")
    print(f"  1. Upload the PNG to MapTiler Cloud → New Raster Tileset")
    print(f"  2. Set bounds: W={sw_lng:.4f} S={sw_lat:.4f} E={ne_lng:.4f} N={ne_lat:.4f}")
    print(f"  3. Coordinate system: WGS84 / EPSG:4326")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Compute lat/lng bounds from GCPs.")
    parser.add_argument(
        "--image",
        default=str(DEFAULT_IMAGE),
        help="Image the GCPs were measured on (default: reference_map.png)",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Optional second image to also compute bounds for (e.g. the Wonderdraft PNG)",
    )
    args = parser.parse_args()

    # Validate GCPs
    active = [(px, py, lat, lng) for px, py, lat, lng in GCPS if px is not None and py is not None]
    if not active:
        sys.exit(
            "Error: No pixel coordinates set.\n"
            "Open reference_map.png, record (x, y) for each city, "
            "and fill them into the GCPS list at the top of this script."
        )
    if len(active) < 2:
        sys.exit("Error: At least 2 GCPs with pixel coordinates are required.")

    # Read image dimensions via PIL
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Error: Pillow not installed. Run: pip install Pillow")

    def get_dims(path):
        p = Path(path)
        if not p.exists():
            sys.exit(f"Error: image not found: {path}")
        w, h = Image.open(p).size
        return w, h

    img_w, img_h = get_dims(args.image)
    print_report("GCP image (bounds for this image)", args.image, img_w, img_h, active)

    if args.target:
        t_w, t_h = get_dims(args.target)
        print_report("Target image (Wonderdraft map)", args.target, t_w, t_h, active)
        print(
            "\nNote: target bounds assume both images cover the same geographic extent.\n"
            "If the maps are cropped differently, measure GCPs directly on the target image."
        )


if __name__ == "__main__":
    main()
