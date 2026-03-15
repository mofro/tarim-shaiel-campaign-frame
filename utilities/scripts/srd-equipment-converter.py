#!/usr/bin/env python3
"""
SRD Equipment Converter - Tier 1 Weapons & Armor
Converts Daggerheart SRD equipment to Kanka-ready format

Usage:
    python srd-equipment-converter.py
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional

# Paths - relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRD_WEAPONS_DIR = PROJECT_ROOT / "references/daggerheart-srd/weapons"
SRD_ARMOR_DIR = PROJECT_ROOT / "references/daggerheart-srd/armor"
OUTPUT_DIR = PROJECT_ROOT / "equipment"

# Tier 1 basic weapons (excluding Advanced/Improved/Legendary variants)
TIER_1_WEAPONS = [
    "Battleaxe.md", "Broadsword.md", "Crossbow.md", "Cutlass.md", "Dagger.md",
    "Dualstaff.md", "Greatstaff.md", "Greatsword.md", "Halberd.md",
    "Hand Crossbow.md", "Longbow.md", "Longsword.md", "Mace.md",
    "Quarterstaff.md", "Rapier.md", "Round Shield.md", "Scepter.md",
    "Shortbow.md", "Shortstaff.md", "Shortsword.md", "Small Dagger.md",
    "Spear.md", "Tower Shield.md", "Wand.md", "Warhammer.md", "Whip.md",
    "Arcane Gauntlets.md", "Glowing Rings.md", "Grappler.md",
    "Hallowed Axe.md", "Hand Runes.md", "Returning Blade.md"
]

# Tier 1 basic armor
TIER_1_ARMOR = [
    "Leather Armor.md",
    "Gambeson Armor.md",
    "Chainmail Armor.md",
    "Full Plate Armor.md"
]


def parse_weapon(filepath: Path) -> Optional[Dict]:
    """Parse a weapon markdown file"""
    try:
        content = filepath.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        
        # Extract name from first line (# Name)
        name = lines[0].replace('# ', '').strip()
        
        # Extract tier and type from second line
        # **_Tier 1_** _Primary_ _Physical_ _Weapon_
        tier_line = lines[2] if len(lines) > 2 else ""
        tier_match = re.search(r'Tier (\d+)', tier_line)
        tier = tier_match.group(1) if tier_match else "1"
        
        # Determine weapon type
        weapon_type = "Primary"
        if "Secondary" in tier_line:
            weapon_type = "Secondary"
        
        # Determine damage type
        damage_type = "Physical"
        if "Magical" in tier_line or "Magic" in tier_line:
            damage_type = "Magical"
        
        # Parse attributes
        data = {
            'name': name,
            'tier': tier,
            'weapon_type': weapon_type,
            'damage_type': damage_type,
            'trait': None,
            'range': None,
            'damage': None,
            'burden': None
        }
        
        # Extract bullet point attributes
        for line in lines:
            if '**Trait:**' in line:
                data['trait'] = line.split('**Trait:**')[1].strip()
            elif '**Range:**' in line:
                data['range'] = line.split('**Range:**')[1].strip()
            elif '**Damage:**' in line:
                data['damage'] = line.split('**Damage:**')[1].strip()
            elif '**Burden:**' in line:
                data['burden'] = line.split('**Burden:**')[1].strip()
        
        return data
        
    except Exception as e:
        print(f"Error parsing weapon {filepath.name}: {e}")
        return None


def parse_armor(filepath: Path) -> Optional[Dict]:
    """Parse an armor markdown file"""
    try:
        content = filepath.read_text(encoding='utf-8')
        lines = content.strip().split('\n')
        
        # Extract name from first line
        name = lines[0].replace('# ', '').strip()
        
        # Extract tier
        tier_line = lines[2] if len(lines) > 2 else ""
        tier_match = re.search(r'Tier (\d+)', tier_line)
        tier = tier_match.group(1) if tier_match else "1"
        
        data = {
            'name': name,
            'tier': tier,
            'base_thresholds': None,
            'base_score': None
        }
        
        # Extract attributes
        for line in lines:
            if '**Base Thresholds:**' in line:
                data['base_thresholds'] = line.split('**Base Thresholds:**')[1].strip()
            elif '**Base Score:**' in line:
                data['base_score'] = line.split('**Base Score:**')[1].strip()
        
        return data
        
    except Exception as e:
        print(f"Error parsing armor {filepath.name}: {e}")
        return None


def generate_weapon_markdown(data: Dict) -> str:
    """Generate Kanka-ready markdown for weapon"""
    
    # Build frontmatter
    frontmatter = f"""---
kanka_type: item
is_private: false
name: {data['name']}
type: weapon
tags: [tier-{data['tier']}, weapon, daggerheart-srd]
weapon_tier: {data['tier']}
weapon_type: {data['weapon_type']}
weapon_damage_type: {data['damage_type']}"""
    
    if data['trait']:
        frontmatter += f"\nweapon_trait: {data['trait']}"
    if data['range']:
        frontmatter += f"\nweapon_range: {data['range']}"
    if data['damage']:
        frontmatter += f"\nweapon_damage: {data['damage']}"
    if data['burden']:
        frontmatter += f"\nweapon_burden: {data['burden']}"
    
    frontmatter += "\n---\n\n"
    
    # Build body
    body = f"# {data['name']}\n\n"
    body += f"**Tier {data['tier']} {data['weapon_type']} {data['damage_type']} Weapon**\n\n"
    
    if data['trait'] or data['range'] or data['damage'] or data['burden']:
        body += "## Stats\n\n"
        if data['trait']:
            body += f"- **Trait:** {data['trait']}\n"
        if data['range']:
            body += f"- **Range:** {data['range']}\n"
        if data['damage']:
            body += f"- **Damage:** {data['damage']}\n"
        if data['burden']:
            body += f"- **Burden:** {data['burden']}\n"
    
    body += "\n*Standard equipment from the Daggerheart SRD.*\n"
    
    return frontmatter + body


def generate_armor_markdown(data: Dict) -> str:
    """Generate Kanka-ready markdown for armor"""
    
    # Build frontmatter
    frontmatter = f"""---
kanka_type: item
is_private: false
name: {data['name']}
type: armor
tags: [tier-{data['tier']}, armor, daggerheart-srd]
armor_tier: {data['tier']}"""
    
    if data['base_thresholds']:
        frontmatter += f"\narmor_thresholds: {data['base_thresholds']}"
    if data['base_score']:
        frontmatter += f"\narmor_score: {data['base_score']}"
    
    frontmatter += "\n---\n\n"
    
    # Build body
    body = f"# {data['name']}\n\n"
    body += f"**Tier {data['tier']} Armor**\n\n"
    
    if data['base_thresholds'] or data['base_score']:
        body += "## Stats\n\n"
        if data['base_thresholds']:
            body += f"- **Base Thresholds:** {data['base_thresholds']}\n"
        if data['base_score']:
            body += f"- **Base Score:** {data['base_score']}\n"
    
    body += "\n*Standard equipment from the Daggerheart SRD.*\n"
    
    return frontmatter + body


def convert_weapons():
    """Convert Tier 1 weapons"""
    print("\n=== Converting Tier 1 Weapons ===\n")
    
    weapons_output = OUTPUT_DIR / "weapons"
    weapons_output.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    skipped = 0
    
    for weapon_file in TIER_1_WEAPONS:
        source = SRD_WEAPONS_DIR / weapon_file
        
        if not source.exists():
            print(f"⚠️  {weapon_file} not found - skipping")
            skipped += 1
            continue
        
        data = parse_weapon(source)
        if not data:
            print(f"✗ Failed to parse {weapon_file}")
            skipped += 1
            continue
        
        # Generate output
        output_content = generate_weapon_markdown(data)
        output_path = weapons_output / weapon_file
        output_path.write_text(output_content, encoding='utf-8')
        
        print(f"✓ {data['name']}")
        converted += 1
    
    print(f"\n{converted} weapons converted, {skipped} skipped")
    return converted


def convert_armor():
    """Convert Tier 1 armor"""
    print("\n=== Converting Tier 1 Armor ===\n")
    
    armor_output = OUTPUT_DIR / "armor"
    armor_output.mkdir(parents=True, exist_ok=True)
    
    converted = 0
    skipped = 0
    
    for armor_file in TIER_1_ARMOR:
        source = SRD_ARMOR_DIR / armor_file
        
        if not source.exists():
            print(f"⚠️  {armor_file} not found - skipping")
            skipped += 1
            continue
        
        data = parse_armor(source)
        if not data:
            print(f"✗ Failed to parse {armor_file}")
            skipped += 1
            continue
        
        # Generate output
        output_content = generate_armor_markdown(data)
        output_path = armor_output / armor_file
        output_path.write_text(output_content, encoding='utf-8')
        
        print(f"✓ {data['name']}")
        converted += 1
    
    print(f"\n{converted} armor pieces converted, {skipped} skipped")
    return converted


def main():
    print("="*60)
    print("SRD Equipment Converter - Tier 1 Weapons & Armor")
    print("="*60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert equipment
    weapon_count = convert_weapons()
    armor_count = convert_armor()
    
    # Summary
    print("\n" + "="*60)
    print("Conversion Complete!")
    print("="*60)
    print(f"Total: {weapon_count + armor_count} items converted")
    print(f"  - {weapon_count} weapons")
    print(f"  - {armor_count} armor pieces")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Review converted files in equipment/ directory")
    print("2. Activate venv: source venv/bin/activate")
    print("3. Sync to Kanka:")
    print("   cd utilities/scripts")
    print("   python kanka-sync.py --sync")
    print("="*60)


if __name__ == '__main__':
    main()
