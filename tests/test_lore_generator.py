"""
Integration tests for the lore HTML generator.

Tests the complete workflow from markdown source to HTML output,
including asset processing and frontmatter parsing.
"""

import pytest
import tempfile
from pathlib import Path
import sys
from unittest.mock import patch

# Add utilities to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from lore.generate_lore_html import main, build_html, slugify
from shared.frontmatter import parse_frontmatter
from shared.errors import LogLevel


class TestLoreGeneratorWorkflow:
    """Test complete lore generation workflow."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project structure
            vault_root = temp_path / "vault"
            docs_dir = temp_path / "docs"
            utilities_dir = temp_path / "utilities"
            
            vault_root.mkdir()
            docs_dir.mkdir()
            utilities_dir.mkdir()
            
            # Create test markdown file with frontmatter and assets
            lore_file = vault_root / "lore" / "test_story.md"
            lore_file.parent.mkdir()
            
            content = """---
title: The Test Story
description: A story for testing
last_updated: 2026-03-22
audio: audio/test_audio.mp3
audio_title: Test Narration
---

This is a test story with an image.

![[test_image.png]]

And some audio content.

More text here.
"""
            lore_file.write_text(content)
            
            # Create test assets
            (vault_root / "images").mkdir()
            test_image = vault_root / "images" / "test_image.png"
            test_image.write_bytes(b"fake_image_data")
            
            (vault_root / "audio").mkdir()
            test_audio = vault_root / "audio" / "test_audio.mp3"
            test_audio.write_bytes(b"fake_audio_data")
            
            yield {
                "vault_root": vault_root,
                "docs_dir": docs_dir,
                "lore_file": lore_file,
                "test_image": test_image,
                "test_audio": test_audio
            }
    
    def test_slugify_function(self):
        """Test slug generation for various inputs."""
        assert slugify("The Test Story") == "the-test-story"
        assert slugify("A Story with Spaces") == "a-story-with-spaces"
        assert slugify("Special---Chars!!!") == "special-chars"
        assert slugify("Multiple   spaces") == "multiple-spaces"
        assert slugify("  Leading and trailing  ") == "leading-and-trailing"
    
    def test_frontmatter_parsing(self):
        """Test frontmatter parsing with YAML and fallback."""
        yaml_content = """---
title: Test Title
description: Test Description
last_updated: 2026-03-22
---
Body content here."""
        
        fm, body = parse_frontmatter(yaml_content)
        assert fm["title"] == "Test Title"
        assert fm["description"] == "Test Description"
        assert body == "Body content here."
        
        # Test without YAML
        simple_content = """---
title: Simple Title
---
Simple body."""
        
        fm, body = parse_frontmatter(simple_content)
        assert fm["title"] == "Simple Title"
        assert body == "Simple body."
    
    def test_build_html_function(self):
        """Test HTML building with various content types."""
        html = build_html(
            title="Test Title",
            description="Test Description",
            body="This is test content.",
            date_str="March 2026",
            audio_url="audio/test.mp3",
            audio_title="Test Audio"
        )
        
        assert "<title>Test Title &mdash; Tarim-Shaiel</title>" in html
        assert "Test Description" in html
        assert "This is test content." in html
        assert "audio/test.mp3" in html
        assert "Test Audio" in html
    
    def test_complete_generation_workflow(self, temp_project):
        """Test the complete generation workflow with real files."""
        project = temp_project
        
        # Mock sys.argv for the main function
        with patch.object(sys, 'argv', [
            'generate_lore_html.py',
            '--source', str(project["lore_file"].relative_to(project["vault_root"])),
            '--out', str(project["docs_dir"] / "test_output.html")
        ]):
            # Patch the paths in the module
            import lore.generate_lore_html as gen_module
            gen_module.VAULT_ROOT = project["vault_root"]
            gen_module.DOCS_DIR = project["docs_dir"]
            
            # Run the generator
            main()
        
        # Check output file exists
        output_file = project["docs_dir"] / "test_output.html"
        assert output_file.exists()
        
        # Check HTML content
        html_content = output_file.read_text()
        assert "The Test Story" in html_content
        assert "A story for testing" in html_content
        assert "audio/test_audio.mp3" in html_content
        assert "images/test_image.png" in html_content
        
        # Check assets were copied
        assert (project["docs_dir"] / "audio" / "test_audio.mp3").exists()
        assert (project["docs_dir"] / "images" / "test_image.png").exists()
    
    def test_missing_asset_handling(self, temp_project):
        """Test handling of missing assets."""
        project = temp_project
        
        # Create content with missing asset
        content = """---
title: Missing Asset Test
---
Content with missing asset:

![[missing_image.png]]

End content."""
        
        lore_file = project["vault_root"] / "lore" / "missing_asset.md"
        lore_file.write_text(content)
        
        with patch.object(sys, 'argv', [
            'generate_lore_html.py',
            '--source', str(lore_file.relative_to(project["vault_root"])),
            '--out', str(project["docs_dir"] / "missing_asset.html")
        ]):
            import lore.generate_lore_html as gen_module
            gen_module.VAULT_ROOT = project["vault_root"]
            gen_module.DOCS_DIR = project["docs_dir"]
            
            main()
        
        # Should still generate HTML, but without the missing asset
        output_file = project["docs_dir"] / "missing_asset.html"
        assert output_file.exists()
        
        html_content = output_file.read_text()
        assert "Missing Asset Test" in html_content
        assert "Content with missing asset:" in html_content
        # Missing image should still be referenced in HTML (with warning logged)
        # This is the current behavior - assets are rendered regardless of existence
        assert "images/missing_image.png" in html_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
