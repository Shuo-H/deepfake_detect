"""
Logging configuration utilities.

This module provides functions to set up logging for the application,
configuring both file and console handlers.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    console_level: Optional[int] = None,
    file_mode: str = "w"
) -> str:
    """
    Configure the root logger to log to both a file and the console.
    Creates a log file with timestamp in the specified directory.
    
    Args:
        log_dir: Directory to store log files (default: "logs")
        log_level: Logging level for file handler (default: INFO)
        console_level: Logging level for console handler (default: same as log_level)
        file_mode: File mode for log file ('a' for append, 'w' for overwrite)
    
    Returns:
        Path to the created log file
    
    Note:
        This function prevents duplicate handlers if called multiple times.
    """
    if console_level is None:
        console_level = log_level
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate timestamp-based log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"{timestamp}.log")
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename, mode=file_mode, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return log_filename