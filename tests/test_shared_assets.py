"""
Integration tests for shared asset utilities.

Tests the complete workflow of finding, copying, and verifying assets
from vault to docs directory.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add utilities to path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from shared.assets import prepare_image, prepare_audio, prepare_audio_wiki, find_in_vault
from shared.errors import AssetNotFoundError, AssetCopyError


class TestAssetWorkflow:
    """Test complete asset preparation workflows."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary vault and docs directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault_root = temp_path / "vault"
            docs_dir = temp_path / "docs"
            
            vault_root.mkdir()
            docs_dir.mkdir()
            
            # Create test files in vault
            (vault_root / "images").mkdir()
            (vault_root / "audio").mkdir()
            
            test_image = vault_root / "images" / "test.png"
            test_image.write_bytes(b"fake_image_data")
            
            test_audio = vault_root / "audio" / "test.mp3"
            test_audio.write_bytes(b"fake_audio_data")
            
            yield vault_root, docs_dir
    
    def test_prepare_image_new_file(self, temp_dirs):
        """Test copying a new image from vault to docs."""
        vault_root, docs_dir = temp_dirs
        
        result = prepare_image("test.png", vault_root, docs_dir)
        
        assert result == "images/test.png"
        assert (docs_dir / "images" / "test.png").exists()
        assert (docs_dir / "images" / "test.png").read_bytes() == b"fake_image_data"
    
    def test_prepare_image_existing_file(self, temp_dirs):
        """Test handling when image already exists in docs."""
        vault_root, docs_dir = temp_dirs
        
        # Pre-create the file in docs
        (docs_dir / "images").mkdir()
        existing_file = docs_dir / "images" / "test.png"
        existing_file.write_bytes(b"existing_data")
        
        result = prepare_image("test.png", vault_root, docs_dir)
        
        assert result == "images/test.png"
        # Should not overwrite existing file
        assert existing_file.read_bytes() == b"existing_data"
    
    def test_prepare_image_not_found(self, temp_dirs):
        """Test handling when image is not found in vault."""
        vault_root, docs_dir = temp_dirs
        
        result = prepare_image("nonexistent.png", vault_root, docs_dir)
        
        assert result is None
        assert not (docs_dir / "images" / "nonexistent.png").exists()
    
    def test_prepare_audio_from_docs(self, temp_dirs):
        """Test audio file already in docs directory."""
        vault_root, docs_dir = temp_dirs
        
        # Create audio file directly in docs
        (docs_dir / "audio").mkdir()
        audio_file = docs_dir / "audio" / "test.mp3"
        audio_file.write_bytes(b"docs_audio_data")
        
        result = prepare_audio("test.mp3", vault_root, docs_dir)
        
        assert result == "audio/test.mp3"
    
    def test_prepare_audio_from_vault(self, temp_dirs):
        """Test copying audio file from vault to docs."""
        vault_root, docs_dir = temp_dirs
        
        result = prepare_audio("audio/test.mp3", vault_root, docs_dir)
        
        assert result == "audio/test.mp3"
        assert (docs_dir / "audio" / "test.mp3").exists()
    
    def test_prepare_audio_wiki_embed(self, temp_dirs):
        """Test preparing audio from wiki embed syntax."""
        vault_root, docs_dir = temp_dirs
        
        result = prepare_audio_wiki("test.mp3", vault_root, docs_dir)
        
        assert result == "audio/test.mp3"
        assert (docs_dir / "audio" / "test.mp3").exists()
    
    def test_find_in_vault(self, temp_dirs):
        """Test finding files in vault recursively."""
        vault_root, docs_dir = temp_dirs
        
        # Test finding existing file
        result = find_in_vault("test.png", vault_root)
        assert result == vault_root / "images" / "test.png"
        
        # Test finding non-existent file
        result = find_in_vault("nonexistent.jpg", vault_root)
        assert result is None
    
    def test_file_verification_corruption(self, temp_dirs):
        """Test handling of corrupted/invalid files."""
        vault_root, docs_dir = temp_dirs
        
        # Create a file that exists but becomes unreadable
        test_file = vault_root / "images" / "test.png"
        test_file.write_bytes(b"fake_image_data")
        
        # Mock the verify_file_integrity function to return False
        with patch('shared.assets.verify_file_integrity', return_value=False):
            result = prepare_image("test.png", vault_root, docs_dir)
            assert result is None


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories with permission issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            vault_root = temp_path / "vault"
            docs_dir = temp_path / "docs"
            
            vault_root.mkdir()
            docs_dir.mkdir()
            
            yield vault_root, docs_dir
    
    def test_copy_permission_error(self, temp_dirs):
        """Test handling of permission errors during copy."""
        vault_root, docs_dir = temp_dirs
        
        # Create source file
        test_image = vault_root / "test.png"
        test_image.write_bytes(b"fake_image_data")
        
        # Mock shutil.copy2 to raise PermissionError
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            result = prepare_image("test.png", vault_root, docs_dir)
            assert result is None
    
    def test_disk_space_error(self, temp_dirs):
        """Test handling of disk space errors."""
        vault_root, docs_dir = temp_dirs
        
        # Create source file
        test_image = vault_root / "test.png"
        test_image.write_bytes(b"fake_image_data")
        
        # Mock shutil.copy2 to raise OSError (disk full)
        with patch('shutil.copy2', side_effect=OSError("No space left on device")):
            result = prepare_image("test.png", vault_root, docs_dir)
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
