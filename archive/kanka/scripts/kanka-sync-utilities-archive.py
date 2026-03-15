#!/usr/bin/env python3
"""
Obsidian → Kanka Sync Script (Enhanced v2.0)
Syncs markdown files from Obsidian vault to Kanka campaign with advanced content routing

FEATURES:
- Content splitting: Public sections → entry, GM sections → separate posts
- Attribute syncing: elevation, resources, factions, etc.
- Faction @mentions for entity linking
- Fail-safe security: Only syncs files with explicit kanka_type

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
}


class KankaAPI:
    """Wrapper for Kanka API interactions"""
    
    def __init__(self, api_token: str, campaign_id: int, base_url: str = "https://api.kanka.io/1.0"):
        self.api_token = api_token
        self.campaign_id = campaign_id
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def _rate_limit_wait(self):
        """Respect Kanka's rate limits"""
        time.sleep(0.5)
        
    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            response = self.session.get(f"{self.base_url}/campaigns/{self.campaign_id}")
            response.raise_for_status()
            campaign = response.json()
            return True, f"Connected to campaign: {campaign['data']['name']}"
        except Exception as e:
            return False, f"Connection failed: {e}"
    
    def get_entity(self, entity_type: str, entity_id: int) -> Optional[Dict]:
        """Get entity with entity_id for posts/attributes"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/{entity_type}s/{entity_id}"
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to get {entity_type} {entity_id}: {e}")
            return None
    
    def create_entity(self, entity_type: str, data: Dict) -> Optional[Dict]:
        """Create new entity"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/{entity_type}s"
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to create {entity_type}: {e}")
            return None
    
    def update_entity(self, entity_type: str, entity_id: int, data: Dict) -> Optional[Dict]:
        """Update existing entity"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/{entity_type}s/{entity_id}"
            response = self.session.patch(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to update {entity_type} {entity_id}: {e}")
            return None
    
    def get_entity_posts(self, entity_id: int) -> List[Dict]:
        """Get all posts for an entity"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/entities/{entity_id}/posts"
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to get posts for entity {entity_id}: {e}")
            return []
    
    def create_post(self, entity_id: int, data: Dict) -> Optional[Dict]:
        """Create post on entity"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/entities/{entity_id}/posts"
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to create post: {e}")
            return None
    
    def update_post(self, entity_id: int, post_id: int, data: Dict) -> Optional[Dict]:
        """Update existing post"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/entities/{entity_id}/posts/{post_id}"
            response = self.session.patch(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to update post {post_id}: {e}")
            return None
    
    def get_entity_attributes(self, entity_id: int) -> List[Dict]:
        """Get all attributes for an entity"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/entities/{entity_id}/attributes"
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to get attributes for entity {entity_id}: {e}")
            return []
    
    def create_attribute(self, entity_id: int, data: Dict) -> Optional[Dict]:
        """Create attribute on entity"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/entities/{entity_id}/attributes"
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to create attribute: {e}")
            return None
    
    def update_attribute(self, entity_id: int, attr_id: int, data: Dict) -> Optional[Dict]:
        """Update existing attribute"""
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/entities/{entity_id}/attributes/{attr_id}"
            response = self.session.patch(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to update attribute {attr_id}: {e}")
            return None

    def create_map_marker(self, map_id: int, data: Dict) -> Optional[Dict]:
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/maps/{map_id}/map_markers"
            response = self.session.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to create map marker on map {map_id}: {e}")
            return None

    def update_map_marker(self, map_id: int, marker_id: int, data: Dict) -> Optional[Dict]:
        try:
            self._rate_limit_wait()
            endpoint = f"{self.base_url}/campaigns/{self.campaign_id}/maps/{map_id}/map_markers/{marker_id}"
            response = self.session.patch(endpoint, json=data)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logging.error(f"Failed to update map marker {marker_id} on map {map_id}: {e}")
            return None


class ContentRouter:
    """Handles markdown content splitting and routing"""
    
    @staticmethod
    def classify_section(header_line: str) -> str:
        """Classify section as public, gm, or unknown"""
        header = header_line.strip()
        
        # Check public markers
        if any(header.startswith(marker) for marker in PUBLIC_SECTION_MARKERS):
            return 'public'
        
        # Check GM markers
        if any(header.startswith(marker) for marker in GM_SECTION_MARKERS.keys()):
            return 'gm'
        
        # Unknown sections default to GM (conservative/safe)
        return 'gm'
    
    @staticmethod
    def split_markdown_content(markdown_body: str) -> Tuple[str, Dict[str, str]]:
        """
        Split markdown into public content and GM sections.
        
        Returns:
            (public_content, gm_sections_dict)
            where gm_sections_dict = {section_name: content}
        """
        # First, strip code blocks and comments
        cleaned = markdown_body
        
        # Remove code blocks
        cleaned = re.sub(r'```[\w]*\n[\s\S]*?```', '', cleaned)
        
        # Remove Obsidian comments
        cleaned = re.sub(r'%%.*?%%', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
        
        # Remove image embeds
        cleaned = re.sub(r'!\[\[.*?\]\]', '', cleaned)
        
        lines = cleaned.split('\n')
        public_lines = []
        gm_sections = {}
        
        current_destination = 'public'
        current_gm_section_name = None
        current_gm_lines = []
        
        for line in lines:
            # Check if this is a header
            if line.startswith('## '):
                section_type = ContentRouter.classify_section(line)
                
                # If we were collecting GM content, save it
                if current_destination == 'gm' and current_gm_section_name:
                    gm_sections[current_gm_section_name] = '\n'.join(current_gm_lines)
                    current_gm_lines = []
                
                if section_type == 'gm':
                    current_destination = 'gm'
                    # Find the post name for this section
                    current_gm_section_name = None
                    for marker, post_name in GM_SECTION_MARKERS.items():
                        if line.strip().startswith(marker):
                            current_gm_section_name = post_name
                            break
                    current_gm_lines = [line]  # Include the header
                    
                elif section_type == 'public':
                    current_destination = 'public'
                    current_gm_section_name = None
                    public_lines.append(line)
                    
                else:  # unknown defaults to GM
                    current_destination = 'gm'
                    current_gm_section_name = 'DM Notes'  # Default GM post name
                    current_gm_lines = [line]
            else:
                # Add line to appropriate destination
                if current_destination == 'gm':
                    current_gm_lines.append(line)
                else:
                    public_lines.append(line)
        
        # Save any remaining GM content
        if current_destination == 'gm' and current_gm_section_name and current_gm_lines:
            gm_sections[current_gm_section_name] = '\n'.join(current_gm_lines)
        
        public_content = '\n'.join(public_lines).strip()
        
        return public_content, gm_sections
    
    @staticmethod
    def clean_obsidian_syntax(content: str) -> str:
        """Remove Obsidian-specific syntax"""
        # Convert wiki links to plain text
        content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)
        
        # Clean up multiple blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    @staticmethod
    def markdown_to_html(content: str) -> str:
        """Convert Markdown to HTML for Kanka"""
        content = ContentRouter.clean_obsidian_syntax(content)
        md = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
        return md.convert(content)


class ObsidianKankaSync:
    """Main sync orchestrator with enhanced routing"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.api = KankaAPI(
            api_token=self.config['kanka']['api_token'],
            campaign_id=self.config['kanka']['campaign_id'],
            base_url=self.config['kanka']['base_url']
        )
        
        self.vault_path = Path(self.config['sync']['vault_path'])
        self.router = ContentRouter()
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'kanka-sync.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def compute_content_hash(self, content: str) -> str:
        """Compute MD5 hash of markdown content for change detection"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def needs_update(self, metadata: Dict, content: str) -> bool:
        """Check if file needs sync based on hash comparison"""
        current_hash = self.compute_content_hash(content)
        stored_hash = metadata.get('kanka_hash')
        
        # If no stored hash, always needs update (new file or pre-hash)
        if stored_hash is None:
            return True
        
        # Compare hashes
        return current_hash != stored_hash
    
    def update_frontmatter_post_sync(self, file_path: Path, post_obj, kanka_id: int, new_hash: str):
        """Update frontmatter after successful sync: hash, tags, kanka_id"""
        
        # Update kanka_id (for new entities)
        if post_obj.get('kanka_id') is None:
            post_obj['kanka_id'] = kanka_id
        
        # Update hash
        post_obj['kanka_hash'] = new_hash
        
        # Update tags: needs-sync → synced
        tags = post_obj.get('tags', [])
        if 'needs-sync' in tags:
            tags.remove('needs-sync')
        if 'synced' not in tags:
            tags.append('synced')
        post_obj['tags'] = tags
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post_obj))
    
    def validate_required_fields(self, metadata: Dict, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Validate required fields.
        
        REQUIRED: kanka_type
        OPTIONAL: name (auto-generated from filename), is_private (defaults to False with warning)
        """
        warnings = []
        
        # MUST have kanka_type
        if 'kanka_type' not in metadata:
            return False, ["Missing required field 'kanka_type'"]
        
        # Auto-generate name from filename if missing
        if 'name' not in metadata:
            metadata['name'] = filepath.stem.replace('-', ' ').title()
            warnings.append(f"Auto-generated name: '{metadata['name']}'")
        
        # Check is_private (warn if missing, default to False)
        if 'is_private' not in metadata:
            metadata['is_private'] = False
            warnings.append(
                "⚠️  PRIVACY WARNING: No 'is_private' field - defaulting to PUBLIC (False)"
            )
        
        return True, warnings
    
    def should_sync_file(self, file_path: Path) -> bool:
        """Determine if file should be synced"""
        rel_path = file_path.relative_to(self.vault_path)
        
        # Check exclusions
        for exclude in self.config['sync']['exclude_paths']:
            if str(rel_path).startswith(exclude):
                return False
        
        # Check inclusions
        for include in self.config['sync']['include_paths']:
            if str(rel_path).startswith(include):
                return True
        
        return False
    
    def convert_factions_to_mentions(self, factions: List[str]) -> str:
        """Convert faction list to @mention syntax"""
        mentions = []
        for faction in factions:
            mention_name = faction.replace(' ', '_')
            mentions.append(f"@{mention_name}")
        return ', '.join(mentions)
    
    def sync_attributes(self, entity_id: int, metadata: Dict, dry_run: bool = False):
        """Sync frontmatter fields as Kanka attributes"""
        if dry_run:
            return
        
        # Get existing attributes
        existing_attrs = self.api.get_entity_attributes(entity_id)
        attr_lookup = {attr['name']: attr for attr in existing_attrs}
        
        for obs_field, (kanka_name, attr_type, is_private) in ATTRIBUTE_MAPPINGS.items():
            if obs_field not in metadata:
                continue
            
            value = metadata[obs_field]
            
            # Convert arrays to comma-separated strings
            if isinstance(value, list):
                if obs_field == 'factions':
                    value = self.convert_factions_to_mentions(value)
                elif obs_field == 'location':  # Coordinates
                    value = f"{value[0]}, {value[1]}"
                else:
                    value = ', '.join(str(v) for v in value)
            
            attr_data = {
                'name': kanka_name,
                'value': str(value),
                'type': attr_type,
                'is_private': is_private
            }
            
            if kanka_name in attr_lookup:
                # Update existing
                self.api.update_attribute(entity_id, attr_lookup[kanka_name]['id'], attr_data)
            else:
                # Create new
                self.api.create_attribute(entity_id, attr_data)
    
    def sync_gm_posts(self, entity_id: int, gm_sections: Dict[str, str], dry_run: bool = False):
        """Create/update separate posts for each GM section"""
        if dry_run or not gm_sections:
            return
        
        # Get existing posts
        existing_posts = self.api.get_entity_posts(entity_id)
        post_lookup = {post['name']: post for post in existing_posts}
        
        for section_name, content in gm_sections.items():
            if not content.strip():
                continue
            
            html_content = self.router.markdown_to_html(content)
            
            post_data = {
                'name': section_name,
                'entry': html_content,
                'visibility': 'admin'  # GM-only
            }
            
            if section_name in post_lookup:
                # Update existing post
                self.api.update_post(entity_id, post_lookup[section_name]['id'], post_data)
            else:
                # Create new post
                self.api.create_post(entity_id, post_data)

    def compute_kanka_map_coords(self, lat: float, lng: float) -> Tuple[float, float, float, float]:
        pixel_x = (AFFINE_X_A * lng) + (AFFINE_X_B * lat) + AFFINE_X_C
        pixel_y = (AFFINE_Y_A * lng) + (AFFINE_Y_B * lat) + AFFINE_Y_C

        kanka_lat = DEFAULT_MAP_IMAGE_HEIGHT_PX - pixel_y
        kanka_lng = pixel_x

        return pixel_x, pixel_y, kanka_lat, kanka_lng

    def sync_location_marker(self, file_path: Path, post_obj, metadata: Dict, entity_id: int, dry_run: bool = False) -> bool:
        if 'location' not in metadata:
            return True

        coords = metadata.get('location')
        if not isinstance(coords, list) or len(coords) < 2:
            logging.warning(f"{file_path.name}: invalid 'location' field; expected [lat, lng]")
            return False

        lat = float(coords[0])
        lng = float(coords[1])

        _, _, kanka_lat, kanka_lng = self.compute_kanka_map_coords(lat, lng)
        map_id = int(metadata.get('kanka_map_id') or DEFAULT_LOCATION_MAP_ID)

        marker_name = metadata.get('fantasy_name') or metadata.get('name')
        marker_id = metadata.get('kanka_marker_id')

        marker_payload = {
            'name': marker_name,
            'latitude': float(f"{kanka_lat:.3f}"),
            'longitude': float(f"{kanka_lng:.3f}"),
            'entity_id': entity_id,
            'is_private': bool(metadata.get('is_private', False)),
            'map_id': map_id,
            'shape_id': 1,
            'icon': 4
        }

        if dry_run:
            logging.info(
                f"[DRY RUN] {file_path.name} marker → map {map_id} "
                f"(marker_id={marker_id}, name='{marker_name}', lat={marker_payload['latitude']}, lng={marker_payload['longitude']}, private={marker_payload['is_private']})"
            )
            return True

        if marker_id:
            result = self.api.update_map_marker(map_id, int(marker_id), marker_payload)
            if not result:
                return False
            logging.info(f"  └─ Marker updated: {file_path.name} (marker_id={marker_id})")
            return True

        result = self.api.create_map_marker(map_id, marker_payload)
        if not result:
            return False

        new_marker_id = result.get('id')
        if not new_marker_id:
            logging.error(f"Marker created but no id returned for {file_path.name}")
            return False

        post_obj['kanka_marker_id'] = int(new_marker_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post_obj))

        logging.info(f"  └─ Marker created: {file_path.name} (marker_id={new_marker_id})")
        return True
    
    def sync_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Sync single file with enhanced routing"""
        try:
            # Parse file
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
            
            metadata = dict(post.metadata)
            
            # Validate
            is_valid, messages = self.validate_required_fields(metadata, file_path)
            
            if not is_valid:
                logging.warning(f"Skipping {file_path.name}: {', '.join(messages)}")
                return False
            
            # Show warnings
            for msg in messages:
                logging.info(f"  {file_path.name}: {msg}")
            
            entity_type = metadata['kanka_type']
            
            if entity_type not in KANKA_MODULES:
                logging.error(f"Invalid entity type '{entity_type}' for {file_path.name}")
                return False
            
            # Split content
            public_content, gm_sections = self.router.split_markdown_content(post.content)
            
            # Convert public content to HTML
            entry_html = self.router.markdown_to_html(public_content)
            
            # Build payload
            payload = {
                'name': metadata['name'],
                'entry': entry_html,
                'is_private': metadata['is_private'],
                'type': metadata.get('type', '')
            }
            
            if dry_run:
                gm_count = len(gm_sections)
                attr_count = sum(1 for k in ATTRIBUTE_MAPPINGS.keys() if k in metadata)
                logging.info(
                    f"[DRY RUN] {file_path.name} → {entity_type} "
                    f"(private={metadata['is_private']}, {attr_count} attrs, {gm_count} GM posts)"
                )
                # Continue through marker preview logic (no API calls)
                kanka_id = metadata.get('kanka_id')
                if entity_type == 'location' and kanka_id:
                    try:
                        entity = self.api.get_entity(entity_type, int(kanka_id))
                        if entity and 'entity_id' in entity:
                            entity_id = entity['entity_id']
                            if not self.sync_location_marker(file_path, post, metadata, entity_id, dry_run=True):
                                return False
                    except Exception as e:
                        logging.error(f"[DRY RUN] Failed to preview marker for {file_path.name}: {e}")
                return True
            
            # Create or update entity
            kanka_id = metadata.get('kanka_id')
            
            if kanka_id:
                result = self.api.update_entity(entity_type, kanka_id, payload)
                if result:
                    logging.info(f"✓ Updated: {file_path.name}")
                else:
                    return False
            else:
                result = self.api.create_entity(entity_type, payload)
                if result:
                    kanka_id = result['id']
                    # Update frontmatter
                    post['kanka_id'] = kanka_id
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(frontmatter.dumps(post))
                    logging.info(f"✓ Created: {file_path.name} (ID: {kanka_id})")
                else:
                    return False
            
            # Get entity_id for attributes and posts
            entity = self.api.get_entity(entity_type, kanka_id)
            if not entity:
                logging.error(f"Failed to get entity_id for {file_path.name}")
                return False
            
            entity_id = entity['entity_id']
            
            # Sync attributes
            self.sync_attributes(entity_id, metadata, dry_run)
            
            # Sync GM posts
            if gm_sections:
                self.sync_gm_posts(entity_id, gm_sections, dry_run)
                logging.info(f"  └─ {len(gm_sections)} GM posts synced")

            # Sync map marker for locations with coordinates
            if entity_type == 'location':
                if not self.sync_location_marker(file_path, post, metadata, entity_id, dry_run=dry_run):
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to sync {file_path}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def sync_all(self, dry_run: bool = False):
        """Sync all eligible files"""
        synced = 0
        failed = 0
        skipped = 0
        
        for include_path in self.config['sync']['include_paths']:
            search_path = self.vault_path / include_path
            
            if not search_path.exists():
                logging.warning(f"Path does not exist: {search_path}")
                continue
            
            for md_file in search_path.rglob('*.md'):
                # Skip templates
                if '_TEMPLATE' in md_file.name or md_file.name.startswith('_'):
                    continue
                
                if not self.should_sync_file(md_file):
                    skipped += 1
                    continue
                
                if self.sync_file(md_file, dry_run):
                    synced += 1
                else:
                    failed += 1
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Sync complete:")
        logging.info(f"  ✓ {synced} files synced")
        logging.info(f"  ✗ {failed} files failed")
        logging.info(f"  ⊘ {skipped} files skipped")
        logging.info(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Obsidian → Kanka Sync (Enhanced)')
    parser.add_argument('--config', default='kanka-sync-config.yaml', help='Config file')
    parser.add_argument('--test-connection', action='store_true', help='Test API')
    parser.add_argument('--dry-run', action='store_true', help='Preview without syncing')
    parser.add_argument('--sync', action='store_true', help='Perform sync')
    parser.add_argument('--sync-one', type=str, help='Sync a single file (relative to vault path)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)
    
    syncer = ObsidianKankaSync(args.config)
    
    if args.test_connection:
        success, message = syncer.api.test_connection()
        print(f"{'✓' if success else '❌'} {message}")
        sys.exit(0 if success else 1)
    
    elif args.dry_run:
        print("🔍 Dry run mode - no changes will be made\n")
        if args.sync_one:
            file_path = syncer.vault_path / args.sync_one
            syncer.sync_file(file_path, dry_run=True)
        else:
            syncer.sync_all(dry_run=True)
    
    elif args.sync:
        print("\n⚠️  Ready to sync files to Kanka")
        print("Features: Content splitting, attributes, GM posts\n")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            if args.sync_one:
                file_path = syncer.vault_path / args.sync_one
                syncer.sync_file(file_path, dry_run=False)
            else:
                syncer.sync_all(dry_run=False)
        else:
            print("Cancelled")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
