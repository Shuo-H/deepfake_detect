"""
Logging configuration utilities.

This module provides functions to set up logging for the application,
configuring both file and console handlers.
"""
import logging
import sys
from typing import Optional


def setup_logging(
    log_filename: str = "debug.log",
    log_level: int = logging.INFO,
    console_level: Optional[int] = None,
    file_mode: str = "w"
) -> None:
    """
    Configure the root logger to log to both a file and the console.
    
    Args:
        log_filename: Path to the log file (default: "debug.log")
        log_level: Logging level for file handler (default: INFO)
        console_level: Logging level for console handler (default: same as log_level)
        file_mode: File mode for log file ('a' for append, 'w' for overwrite)
    
    Note:
        This function prevents duplicate handlers if called multiple times.
    """
    if console_level is None:
        console_level = log_level
    
    # Configure logging to a file
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=log_filename,
        filemode=file_mode,
        force=True  # Override any existing configuration
    )
    
    # Get the root logger
    logger = logging.getLogger()
    
    # Check if a console handler (StreamHandler) already exists
    # This prevents duplicate messages if the script is re-run in the same session
    has_console_handler = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in logger.handlers
    )
    
    if not has_console_handler:
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        
        # Create a formatter for the console (simpler format)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        
        # Add the handler to the root logger
        logger.addHandler(console_handler)