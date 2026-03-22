"""
Logging configuration for Netlify deployment environment.

Provides appropriate logging setup for both development and production
environments, with consideration for Netlify's build and runtime constraints.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from enum import Enum


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    NETLIFY_BUILD = "netlify_build"


def detect_environment() -> Environment:
    """Detect the current environment based on environment variables."""
    if os.getenv("NETLIFY") == "true" or os.getenv("CONTEXT") in ["production", "deploy-preview"]:
        return Environment.NETLIFY_BUILD
    elif os.getenv("NODE_ENV") == "production":
        return Environment.PRODUCTION
    else:
        return Environment.DEVELOPMENT


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    environment: Optional[Environment] = None
) -> logging.Logger:
    """Setup logging configuration appropriate for the environment.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        environment: Environment override (auto-detected if not provided)
    
    Returns:
        Configured logger instance
    """
    if environment is None:
        environment = detect_environment()
    
    # Determine log level
    if level is None:
        if environment == Environment.DEVELOPMENT:
            level = "DEBUG"
        else:
            level = "INFO"
    
    # Create logger
    logger = logging.getLogger("hero_heaven_generators")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if environment == Environment.DEVELOPMENT:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        # Production/Netlify: simpler format for logs
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for development or if log_file specified
    if log_file or environment == Environment.DEVELOPMENT:
        if log_file is None:
            log_file = Path("logs") / "generator.log"
            log_file.parent.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "hero_heaven_generators") -> logging.Logger:
    """Get a logger instance with the current configuration."""
    return logging.getLogger(name)


# Netlify-specific logging considerations
class NetlifyLogger:
    """Logger optimized for Netlify build environment."""
    
    def __init__(self):
        self.env = detect_environment()
        self.logger = setup_logging(environment=self.env)
    
    def log_build_step(self, step: str, details: Optional[dict] = None):
        """Log a build step with Netlify-friendly formatting."""
        message = f"🔧 {step}"
        if details:
            details_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({details_str})"
        
        self.logger.info(message)
    
    def log_asset_operation(self, operation: str, asset: str, status: str, details: Optional[dict] = None):
        """Log asset operations with consistent formatting."""
        emoji = {"copied": "📁", "found": "🔍", "error": "❌", "skipped": "⏭️"}.get(status.lower(), "📋")
        message = f"{emoji} {operation}: {asset} [{status}]"
        if details:
            details_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({details_str})"
        
        if status.lower() == "error":
            self.logger.error(message)
        elif status.lower() == "skipped":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def log_generation_summary(self, source_file: str, output_file: str, assets_processed: int):
        """Log generation summary for Netlify build output."""
        self.logger.info(f"📄 Generated: {source_file} → {output_file}")
        self.logger.info(f"🎯 Assets processed: {assets_processed}")


# Singleton instance for easy import
netlify_logger = NetlifyLogger()


# Backward compatibility with existing print-based logging
def log_with_fallback(level: str, message: str, context: Optional[dict] = None):
    """Log using proper logging, fallback to print if logging fails."""
    try:
        logger = get_logger()
        log_method = getattr(logger, level.lower())
        
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} ({context_str})"
        
        log_method(message)
    except Exception:
        # Fallback to print-based logging
        prefix = f"  [{level.upper()}]"
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} ({context_str})"
        print(f"{prefix} {message}")
