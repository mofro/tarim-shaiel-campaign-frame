#!/usr/bin/env python3
"""
Mountain Range Icon Generator for KML
Creates evenly-spaced mountain placemarks along a ridge line

Usage:
    python mountain_range_generator.py
    
Or import and use the functions:
    from mountain_range_generator import generate_ridge_placemarks
"""

import math
from typing import List, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth in kilometers
    Uses Haversine formula
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def interpolate_point(start: Tuple[float, float], 
                     end: Tuple[float, float], 
                     fraction: float) -> Tuple[float, float]:
    """
    Interpolate a point along a great circle between start and end
    fraction: 0.0 = start, 1.0 = end
    
    For shorter distances (<1000km), linear interpolation is close enough
    """
    lat = start[0] + (end[0] - start[0]) * fraction
    lon = start[1] + (end[1] - start[1]) * fraction
    return (lat, lon)

def generate_ridge_placemarks(start_lat: float, start_lon: float,
                             end_lat: float, end_lon: float,
                             spacing_km: float = 60.0,
                             name_prefix: str = "Mountain",
                             style: str = "mountain-peak") -> List[dict]:
    """
    Generate evenly-spaced placemarks along a ridge line
    
    Args:
        start_lat, start_lon: Starting point (degrees)
        end_lat, end_lon: Ending point (degrees)
        spacing_km: Distance between icons (default 60km)
        name_prefix: Name for the placemarks (will add numbers)
        style: KML style reference
        
    Returns:
        List of placemark dictionaries with name, lat, lon, style
    """
    # Calculate total distance
    total_distance = haversine_distance(start_lat, start_lon, end_lat, end_lon)
    
    # Calculate number of placemarks needed
    num_placemarks = max(2, int(total_distance / spacing_km) + 1)
    
    placemarks = []
    for i in range(num_placemarks):
        fraction = i / (num_placemarks - 1) if num_placemarks > 1 else 0
        lat, lon = interpolate_point((start_lat, start_lon), 
                                     (end_lat, end_lon), 
                                     fraction)
        
        placemarks.append({
            'name': f"{name_prefix} {i+1}",
            'lat': lat,
            'lon': lon,
            'style': style
        })
    
    return placemarks

def generate_kml(ranges: List[dict], output_file: str = "mountain_ranges.kml"):
    """
    Generate KML file with mountain range placemarks
    
    Args:
        ranges: List of range definitions, each containing:
            - name: Range name
            - start_lat, start_lon: Start coordinates
            - end_lat, end_lon: End coordinates
            - spacing_km: Spacing between icons (optional, default 60)
            - style: Icon style (optional, default 'mountain-peak')
        output_file: Path to output KML file
    """
    # KML header - NOTE: Using proper <name> tags!
    kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Mountain Ranges</name>
    <description>Mountain range icons for fantasy mapping</description>
    
    <!-- Styles for different mountain types -->
    <Style id="mountain-peak">
      <IconStyle>
        <color>ff8B4513</color>
        <scale>1.0</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/mountains.png</href></Icon>
      </IconStyle>
    </Style>
    
    <Style id="high-peak">
      <IconStyle>
        <color>ffFFFFFF</color>
        <scale>1.2</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/mountains.png</href></Icon>
      </IconStyle>
    </Style>
    
    <Style id="sacred-peak">
      <IconStyle>
        <color>ffFFD700</color>
        <scale>1.1</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/mountains.png</href></Icon>
      </IconStyle>
    </Style>
'''
    
    # Generate placemarks for each range
    for range_def in ranges:
        name = range_def['name']
        spacing = range_def.get('spacing_km', 60.0)
        style = range_def.get('style', 'mountain-peak')
        
        # Add folder for this range - using <name> tag!
        kml_content += f'''
    <Folder>
      <name>{name}</name>
'''
        
        # Generate placemarks
        placemarks = generate_ridge_placemarks(
            range_def['start_lat'], range_def['start_lon'],
            range_def['end_lat'], range_def['end_lon'],
            spacing, name, style
        )
        
        for pm in placemarks:
            kml_content += f'''      <Placemark>
        <name>{pm['name']}</name>
        <styleUrl>#{pm['style']}</styleUrl>
        <Point>
          <coordinates>{pm['lon']},{pm['lat']},0</coordinates>
        </Point>
      </Placemark>
'''
        
        kml_content += '''    </Folder>
'''
    
    # KML footer
    kml_content += '''  </Document>
</kml>
'''
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(kml_content)
    
    print(f"Generated {output_file}")
    return output_file


if __name__ == "__main__":
    # Define major mountain ranges for Hero Heaven
    ranges = [
        {
            'name': 'Tian Shan Range',
            'start_lat': 42.0, 'start_lon': 69.0,  # Western end (near Tashkent)
            'end_lat': 42.5, 'end_lon': 95.0,      # Eastern end
            'spacing_km': 60,
            'style': 'mountain-peak'
        },
        {
            'name': 'Kunlun Range',
            'start_lat': 36.0, 'start_lon': 75.0,  # Western end
            'end_lat': 36.0, 'end_lon': 99.0,      # Eastern end
            'spacing_km': 60,
            'style': 'mountain-peak'
        },
        {
            'name': 'Pamir Range',
            'start_lat': 37.5, 'start_lon': 71.0,  # Western extent
            'end_lat': 39.0, 'end_lon': 75.0,      # Eastern extent
            'spacing_km': 60,
            'style': 'high-peak'
        },
        {
            'name': 'Turkestan Range',
            'start_lat': 39.5, 'start_lon': 68.5,
            'end_lat': 40.0, 'end_lon': 73.5,
            'spacing_km': 60,
            'style': 'mountain-peak'
        },
        {
            'name': 'Zarafshan Range',
            'start_lat': 39.2, 'start_lon': 68.5,
            'end_lat': 39.5, 'end_lon': 72.0,
            'spacing_km': 60,
            'style': 'mountain-peak'
        }
    ]
    
    # Generate the KML
    generate_kml(ranges, "mountain_ranges.kml")
    
    # Print summary
    print("\nMountain Range Summary:")
    print("=" * 70)
    for r in ranges:
        total_dist = haversine_distance(
            r['start_lat'], r['start_lon'],
            r['end_lat'], r['end_lon']
        )
        num_icons = max(2, int(total_dist / r.get('spacing_km', 60)) + 1)
        print(f"{r['name']:25s} - {total_dist:6.0f} km - {num_icons:3d} icons")
    print("=" * 70)
