"""
Standardized error handling for asset operations.

Provides consistent error reporting and logging across all generators.
"""

import sys
from pathlib import Path
from typing import Optional, Any
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AssetError(Exception):
    """Base exception for asset-related errors."""
    pass


class AssetNotFoundError(AssetError):
    """Raised when an asset cannot be found in expected locations."""
    pass


class AssetCopyError(AssetError):
    """Raised when asset copying fails."""
    pass


def log(level: LogLevel, message: str, context: Optional[dict] = None) -> None:
    """Standardized logging function that can be replaced with proper logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        message: Log message
        context: Optional context dictionary for additional info
    """
    prefix = f"  [{level.value}]"
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        message = f"{message} ({context_str})"
    
    print(f"{prefix} {message}")


def handle_asset_error(
    operation: str,
    asset_name: str,
    error: Exception,
    fail_silently: bool = False
) -> Optional[Any]:
    """Standardized error handling for asset operations.
    
    Args:
        operation: Description of the operation (e.g., "copy image", "find audio")
        asset_name: Name/path of the asset being processed
        error: The exception that occurred
        fail_silently: If True, returns None; if False, re-raises the exception
    
    Returns:
        None if fail_silently=True, otherwise re-raises the exception
    """
    log(LogLevel.ERROR, f"Failed to {operation}: {asset_name}", {"error": str(error)})
    
    if not fail_silently:
        raise error
    
    return None


def verify_file_integrity(file_path: Path, expected_size: Optional[int] = None) -> bool:
    """Verify that a file exists and has expected properties.
    
    Args:
        file_path: Path to the file to verify
        expected_size: Optional expected file size in bytes
    
    Returns:
        True if file passes verification, False otherwise
    """
    if not file_path.exists():
        log(LogLevel.ERROR, f"File does not exist: {file_path}")
        return False
    
    if not file_path.is_file():
        log(LogLevel.ERROR, f"Path is not a file: {file_path}")
        return False
    
    if expected_size is not None and file_path.stat().st_size != expected_size:
        log(LogLevel.WARNING, f"File size mismatch for {file_path}", {
            "expected": expected_size,
            "actual": file_path.stat().st_size
        })
        return False
    
    return True
