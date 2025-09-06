"""Logging configuration for Deep Research system."""

import sys
from loguru import logger
from src.utils.config import config

# Remove default logger
logger.remove()

# Console logger with rich formatting
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.log_level,
    colorize=True,
    enqueue=True
)

# File logger for debugging
if config.debug:
    logger.add(
        "logs/deep_research_{time}.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True
    )

# Export configured logger
__all__ = ["logger"]