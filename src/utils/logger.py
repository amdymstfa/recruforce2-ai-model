"""
Centralized logging configuration using loguru.
Provides structured logging for the AI service.
"""

import sys
from loguru import logger
from pathlib import Path
from src.core.config import settings


def setup_logger():
    """
    Configure loguru logger with file and console output.
    """
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File handler with rotation
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    logger.info(f"Logger initialized - Level: {settings.log_level}")
    return logger


# Initialize logger on import
log = setup_logger()


def get_logger():
    """Get configured logger instance."""
    return log