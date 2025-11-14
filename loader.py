"""
Audio file loading utilities.

This module provides functions to load audio files from various sources,
including directories and Gradio interfaces.
"""
import os
import logging
from typing import Generator, Tuple, Optional

import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)

# Supported audio file extensions
AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma",
    ".opus", ".aiff", ".aif"
}


def load_with_directory(directory: str) -> Generator[Tuple[str, np.ndarray, int], None, None]:
    """
    Load audio files from a directory specified in a YAML config file.
    
    Args:
        config_path: Path to YAML configuration file containing directory path
    
    Yields:
        Tuple of (audio_path, audio_data, sample_rate) for each audio file found
    
    Raises:
        FileNotFoundError: If config file or directory doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            # Check the extension
            _, ext = os.path.splitext(filename)
            if ext.lower() in AUDIO_EXTENSIONS:
                audio_path = os.path.join(dirpath, filename)
                try:
                    audio, sr = sf.read(audio_path)
                    logger.debug(f"Successfully loaded {audio_path} (shape: {audio.shape}, sample rate: {sr} Hz)")
                    yield audio_path, audio, sr
                except Exception as e:
                    # Log error but continue processing other files
                    logger.error(f"Error loading {audio_path}: {e}", exc_info=True)
                    continue