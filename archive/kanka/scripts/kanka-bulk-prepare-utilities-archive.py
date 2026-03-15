#!/usr/bin/env python3
"""
Bulk Kanka Frontmatter Preparation Script

Scans your Obsidian vault for files missing Kanka frontmatter and helps you
add the required fields (kanka_type, kanka_id, is_private) in batches.

Usage:
    python kanka-bulk-prepare.py --scan
    python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false
    python kanka-bulk-prepare.py --prepare "Mechanics" --type note --private true
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import yaml
import frontmatter

class BulkPreparer:
    """Helper for bulk adding Kanka frontmatter"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
    
    def scan_directory(self, directory: str) -> Tuple[List[Path], List[Path]]:
        """Scan a directory and categorize files by Kanka-readiness"""
        search_path = self.vault_path / directory
        
        if not search_path.exists():
            print(f"❌ Directory not found: {search_path}")
            return [], []
        
        ready = []
        not_ready = []
        
        for md_file in search_path.rglob('*.md'):
            # Skip templates
            if '_TEMPLATE' in md_file.name or md_file.name.startswith('_'):
                continue
            
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)
                
                metadata = dict(post.metadata)
                
                # Check if Kanka-ready
                has_kanka_type = 'kanka_type' in metadata
                has_is_private = 'is_private' in metadata
                
                if has_kanka_type and has_is_private:
                    ready.append(md_file)
                else:
                    not_ready.append(md_file)
            except Exception as e:
                print(f"⚠️  Error reading {md_file.name}: {e}")
                continue
        
        return ready, not_ready
    
    def add_kanka_fields(self, file_path: Path, kanka_type: str, is_private: bool, dry_run: bool = False):
        """Add Kanka frontmatter fields to a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            # Add Kanka fields
            post['kanka_type'] = kanka_type
            post['kanka_id'] = None
            post['is_private'] = is_private
            
            if dry_run:
                print(f"  [DRY RUN] Would add to {file_path.name}")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(post))
                print(f"  ✓ Updated {file_path.name}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to update {file_path.name}: {e}")
            return False
    
    def prepare_batch(self, directory: str, kanka_type: str, is_private: bool, dry_run: bool = False):
        """Prepare a batch of files"""
        ready, not_ready = self.scan_directory(directory)
        
        if not not_ready:
            print(f"\n✅ All files in {directory} are already Kanka-ready!")
            return
        
        print(f"\n📁 Directory: {directory}")
        print(f"📊 Status: {len(ready)} ready, {len(not_ready)} need preparation")
        print(f"\n🔧 Will add:")
        print(f"   kanka_type: {kanka_type}")
        print(f"   kanka_id: null")
        print(f"   is_private: {is_private}")
        
        if dry_run:
            print(f"\n[DRY RUN MODE - No files will be modified]")
        
        print(f"\n📝 Files to update ({len(not_ready)}):")
        for i, file_path in enumerate(not_ready[:10], 1):
            print(f"   {i}. {file_path.name}")
        
        if len(not_ready) > 10:
            print(f"   ... and {len(not_ready) - 10} more")
        
        if not dry_run:
            confirm = input(f"\n⚠️  Update {len(not_ready)} files? (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Cancelled")
                return
        
        # Process files
        success = 0
        failed = 0
        
        print(f"\n🔄 Processing...")
        for file_path in not_ready:
            if self.add_kanka_fields(file_path, kanka_type, is_private, dry_run):
                success += 1
            else:
                failed += 1
        
        print(f"\n{'='*50}")
        print(f"✅ Complete: {success} updated, {failed} failed")
        print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description='Bulk prepare files for Kanka sync')
    parser.add_argument('--vault', default='/Users/mo/Documents/Games/HeroHeaven', 
                       help='Path to Obsidian vault')
    
    # Commands
    parser.add_argument('--scan', action='store_true', 
                       help='Scan all directories and show status')
    parser.add_argument('--prepare', type=str, 
                       help='Prepare files in directory (e.g., "World/Locations")')
    
    # Options for --prepare
    parser.add_argument('--type', type=str, default='location',
                       help='Kanka entity type (default: location)')
    parser.add_argument('--private', type=str, choices=['true', 'false'], default='false',
                       help='Set is_private field (default: false)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without modifying files')
    
    args = parser.parse_args()
    
    preparer = BulkPreparer(args.vault)
    
    if args.scan:
        print("🔍 Scanning vault for Kanka-readiness...\n")
        
        directories = [
            ('World/Locations', 'location'),
            ('World/Regions', 'location'),
            ('Mechanics', 'note'),
            ('Characters/Archetypes', 'character'),
            ('Characters/NPCs', 'character'),
        ]
        
        total_ready = 0
        total_not_ready = 0
        
        for directory, entity_type in directories:
            ready, not_ready = preparer.scan_directory(directory)
            total_ready += len(ready)
            total_not_ready += len(not_ready)
            
            if ready or not_ready:
                status = "✅" if not not_ready else "⚠️"
                print(f"{status} {directory:30} → {len(ready):3} ready, {len(not_ready):3} need prep")
        
        print(f"\n{'='*50}")
        print(f"📊 TOTAL: {total_ready} ready, {total_not_ready} need preparation")
        print(f"{'='*50}\n")
        
        if total_not_ready > 0:
            print("💡 To prepare files, use:")
            print('   python kanka-bulk-prepare.py --prepare "World/Locations" --type location --private false')
    
    elif args.prepare:
        is_private = args.private == 'true'
        preparer.prepare_batch(args.prepare, args.type, is_private, args.dry_run)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
