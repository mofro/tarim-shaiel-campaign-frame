"""
Central project configuration for Tarim-Shaiel generators.

Import ProjectConfig rather than re-computing paths or hardcoding project
identity strings in individual generator scripts.
"""
from dataclasses import dataclass, field
from pathlib import Path

_VAULT_ROOT = Path(__file__).parent.parent.parent  # shared/ → utilities/ → repo root


@dataclass(frozen=True)
class _ProjectConfig:
    project_name: str = "tarim-shaiel"
    display_name: str = "Tarim-Shaiel"
    vault_name: str = "HeroHeaven"          # Obsidian vault folder name
    logger_name: str = "tarim_shaiel_generators"
    vault_root: Path = field(default_factory=lambda: _VAULT_ROOT)


ProjectConfig = _ProjectConfig()
