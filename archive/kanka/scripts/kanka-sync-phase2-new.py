#!/usr/bin/env python3
"""
Obsidian → Kanka Sync Script (Enhanced v2.1 - Phase 2: Daggerheart Support)
Syncs markdown files from Obsidian vault to Kanka campaign with advanced content routing

FEATURES:
- Content splitting: Public sections → entry, GM sections → separate posts
- Attribute syncing: elevation, resources, factions, etc.
- Faction @mentions for entity linking
- Fail-safe security: Only syncs files with explicit kanka_type
- PHASE 2: Daggerheart stat block parsing and rendering

Required frontmatter:
- kanka_type: (location, character, note, etc.) - REQUIRED
- is_private: (true/false) - Defaults to false with warning if missing
- kanka_id: (null for new, or existing ID for updates)

Usage:
    python kanka-sync.py --test-connection
    python kanka-sync.py --dry-run
    python kanka-sync.py --sync
"""

import os
import sys
import argparse
import logging
import time
import re
import markdown
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import requests
import frontmatter
from datetime import datetime

# Map marker defaults for HeroHeaven image map calibration
DEFAULT_LOCATION_MAP_ID = 125882
DEFAULT_MAP_IMAGE_WIDTH_PX = 6457.0
DEFAULT_MAP_IMAGE_HEIGHT_PX = 2682.0

# Affine transform from (lng, lat) -> (pixelX, pixelY)
AFFINE_X_A = 89.4
AFFINE_X_B = -0.0793
AFFINE_X_C = -4344.8

AFFINE_Y_A = -1.632
AFFINE_Y_B = -111.8
AFFINE_Y_C = 5726.2

# Module ID mapping for Kanka entity types
KANKA_MODULES = {
    'character': 1,
    'family': 2,
    'location': 3,
    'organization': 4,
    'item': 5,
    'timeline': 6,
    'race': 7,
    'journal': 8,
    'ability': 9,
    'event': 10,
    'quest': 11,
    'calendar': 12,
    'note': 13,
    'map': 14,
    'creature': 20
}

# Content routing configuration
PUBLIC_SECTION_MARKERS = [
    '## Geography',
    '## Economy',
    '## Key Features',
    '## Factions',
    '## Factions Present',
    '## Resources',
    '## Waypoint Status',
    '## Cultural Notes',
    '## Historical Basis',
    '## Historical Foundation',
]

GM_SECTION_MARKERS = {
    '## Narrative Significance': 'Narrative Significance',
    '## Key Narrative Elements': 'Key Narrative Elements',
    '## Hidden Secrets': 'Hidden Secrets',
    '## Plot Hooks': 'Plot Hooks',
    '## DM Notes': 'DM Notes',
    '## World-Building Context': 'World-Building Context',
}

# Attribute mappings: frontmatter field → (Kanka name, type, is_private)
ATTRIBUTE_MAPPINGS = {
    'elevation': ('Elevation', 'number', False),
    'location': ('Coordinates', 'text', False),
    'mapmarker': ('Map Marker Type', 'text', False),
    'resources': ('Resources', 'text', False),
    'factions': ('Primary Factions', 'text', False),
    'population': ('Population', 'number', False),
    'danger_level': ('Danger Level', 'number', False),
    # Daggerheart stat block attributes (parsed from code blocks)
    'dh_tier': ('Tier', 'number', False),
    'dh_type': ('Adversary Type', 'text', False),
    'dh_difficulty': ('Difficulty', 'number', False),
    'dh_thresholds': ('Thresholds', 'text', False),
    'dh_hp': ('HP', 'number', False),
    'dh_stress': ('Stress', 'number', False),
    'dh_attack': ('Attack Bonus', 'text', False),
    'dh_weapon': ('Weapon', 'text', False),
    'dh_range': ('Range', 'text', False),
    'dh_damage': ('Damage', 'text', False),
    'dh_motives': ('Motives', 'text', False),
    'dh_xp': ('Experiences', 'text', False),
}


def extract_daggerheart_blocks(content: str) -> List[Dict]:
    """
    Find and parse daggerheart code blocks.
    
    Returns:
        List of parsed stat block dictionaries
    """
    pattern = r'```daggerheart\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    blocks = []
    for match in matches:
        try:
            data = yaml.safe_load(match)
            if data and isinstance(data, dict):
                blocks.append(data)
        except yaml.YAMLError as e:
            logging.warning(f"Failed to parse daggerheart block: {e}")
            continue
    
    return blocks


def daggerheart_to_attributes(block: Dict) -> List[Dict]:
    """
    Convert daggerheart block to Kanka attributes.
    
    Args:
        block: Parsed daggerheart stat block
        
    Returns:
        List of attribute dicts ready for Kanka API
    """
    # Mapping from daggerheart fields to attribute data
    field_mappings = {
        'tier': ('Tier', 'number', False),
        'type': ('Adversary Type', 'text', False),
        'difficulty': ('Difficulty', 'number', False),
        'thresholds': ('Thresholds', 'text', False),
        'hp': ('HP', 'number', False),
        'stress': ('Stress', 'number', False),
        'attack': ('Attack Bonus', 'text', False),
        'weapon': ('Weapon', 'text', False),
        'range': ('Range', 'text', False),
        'damage': ('Damage', 'text', False),
        'motives': ('Motives', 'text', False),
        'xp': ('Experiences', 'text', False),
    }
    
    attributes = []
    for field, (kanka_name, attr_type, is_private) in field_mappings.items():
        if field not in block:
            continue
        
        value = block[field]
        
        # Handle arrays (like for multiple motives)
        if isinstance(value, list):
            value = ', '.join(str(v) for v in value)
        
        attributes.append({
            'name': kanka_name,
            'value': str(value),
            'type': attr_type,
            'is_private': is_private
        })
    
    return attributes


def render_features_html(features: List[Dict]) -> str:
    """
    Render features as HTML list.
    
    Args:
        features: List of feature dicts with 'name', 'type', 'desc'
        
    Returns:
        HTML string of formatted features
    """
    if not features:
        return ''
    
    html = '<h4>Features</h4><ul>'
    for f in features:
        feature_name = f.get('name', 'Feature')
        feature_type = f.get('type', 'Passive')
        feature_desc = f.get('desc', '')
        html += f'''
        <li>
          <strong>{feature_name}</strong> ({feature_type}): {feature_desc}
        </li>
        '''
    html += '</ul>'
    return html


def render_statblock_html(block: Dict) -> str:
    """
    Render a nice HTML stat block for entity entry.
    
    Args:
        block: Parsed daggerheart stat block
        
    Returns:
        HTML string of formatted stat block
    """
    name = block.get('name', 'Unknown')
    tier = block.get('tier', '?')
    adversary_type = block.get('type', 'Adversary')
    difficulty = block.get('difficulty', '?')
    thresholds = block.get('thresholds', '?')
    hp = block.get('hp', '?')
    stress = block.get('stress', '?')
    attack = block.get('attack', '+0')
    weapon = block.get('weapon', 'Attack')
    range_val = block.get('range', 'Melee')
    damage = block.get('damage', '1d6 phy')
    motives = block.get('motives', 'Unknown')
    xp = block.get('xp', '')
    
    html = f'''
    <div class="daggerheart-statblock" style="border: 2px solid #8b4513; padding: 15px; margin: 10px 0; background: #f5f5dc; border-radius: 5px;">
      <h3 style="margin-top: 0; color: #8b4513;">{name}</h3>
      <p><strong>Tier {tier} {adversary_type}</strong></p>
      <hr style="border-color: #8b4513;">
      <p>
        <strong>Difficulty:</strong> {difficulty} |
        <strong>Thresholds:</strong> {thresholds} |
        <strong>HP:</strong> {hp} |
        <strong>Stress:</strong> {stress}
      </p>
      <p>
        <strong>Attack:</strong> {attack} |
        <strong>{weapon}:</strong> {range_val} |
        <strong>Damage:</strong> {damage}
      </p>
      <p><strong>Motives:</strong> {motives}</p>
    '''
    
    if xp:
        html += f'<p><strong>Experiences:</strong> {xp}</p>'
    
    # Add features if present
    features = block.get('features', [])
    if features:
        html += render_features_html(features)
    
    html += '</div>'
    
    return html
