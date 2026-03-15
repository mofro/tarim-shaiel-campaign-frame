---
title: Tarim-Shaiel Utilities
project: TTRPG_Tarim_Shaiel
type: utilities
created: 2025-12-07
---

# Tarim-Shaiel Utilities

This directory contains utility scripts and tools for the Tarim-Shaiel TTRPG project.

---

## mountain_range_generator.py

**Purpose:** Generates KML files with evenly-spaced mountain icons along ridge lines for fantasy mapping.

**Use Case:** Create Tolkien-style decorated mountain ranges on maps, where instead of a single point or line, you get a row of mountain icons distributed along the ridge crest.

### Quick Start

```bash
cd /Users/mo/Documents/Games/HeroHeaven/utilities
python3 mountain_range_generator.py
```

This generates `mountain_ranges.kml` in the current directory with the five major ranges (Tian Shan, Kunlun, Pamir, Turkestan, Zarafshan).

### Customization

Edit the `ranges` list in the `if __name__ == "__main__":` section to define your own ranges:

```python
ranges = [
    {
        'name': 'Your Range Name',
        'start_lat': 40.0,          # Starting latitude
        'start_lon': 70.0,          # Starting longitude
        'end_lat': 42.0,            # Ending latitude
        'end_lon': 75.0,            # Ending longitude
        'spacing_km': 60,           # Distance between icons (km)
        'style': 'mountain-peak'    # Style ID
    }
]
```

### Available Styles

- `mountain-peak` - Brown/tan mountains (standard)
- `high-peak` - White mountains (snow-capped, larger)
- `sacred-peak` - Gold mountains (special/magical)

### Programmatic Use

You can also import the functions:

```python
from mountain_range_generator import generate_ridge_placemarks, generate_kml

# Generate placemarks for a single range
placemarks = generate_ridge_placemarks(
    start_lat=40.0, start_lon=70.0,
    end_lat=42.0, end_lon=75.0,
    spacing_km=60,
    name_prefix="My Mountains",
    style="mountain-peak"
)

# Or generate a complete KML file
ranges = [...]  # Your range definitions
generate_kml(ranges, output_file="custom_mountains.kml")
```

### Icon Spacing

The default spacing of 60km is calibrated for Google Earth at the scale of Central Asia. At this scale, mountain icons appear to be ~55-60km wide, so 60km spacing creates a continuous decorated ridge without overlap.

Adjust `spacing_km` if working at different map scales:
- Larger scale (zoomed in): Use smaller spacing (30-40km)
- Smaller scale (zoomed out): Use larger spacing (80-100km)

### Output Location

Generated KML files can be imported directly into:
- Google Earth (File → Import)
- Google My Maps
- Most GIS tools
- Obsidian with Leaflet plugin

---

## Future Utilities

Additional utilities to be added:
- Trade route generator
- City placement validator (minimum distances)
- Region boundary generator
- Fantasy name generator
