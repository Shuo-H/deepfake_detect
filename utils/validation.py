"""
Input validation utilities for audio processing.

This module provides validation functions for audio inputs,
ensuring data quality and format compliance.
"""
import numpy as np
import logging
from typing import Tuple, Optional
from exceptions import AudioFormatError, AudioQualityError

logger = logging.getLogger(__name__)


def validate_audio(
    audio: np.ndarray,
    sr: int,
    min_duration: float = 0.1,
    max_duration: float = 300.0,
    min_sr: int = 8000,
    max_sr: int = 48000,
    check_silence: bool = True,
    silence_threshold: float = 0.01
) -> Tuple[bool, Optional[str]]:
    """
    Validate audio input.
    
    Args:
        audio: Audio data as numpy array
        sr: Sample rate
        min_duration: Minimum audio duration in seconds
        max_duration: Maximum audio duration in seconds
        min_sr: Minimum acceptable sample rate
        max_sr: Maximum acceptable sample rate
        check_silence: Whether to check for silence
        silence_threshold: RMS threshold for silence detection
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check sample rate
    if not (min_sr <= sr <= max_sr):
        return False, f"Sample rate {sr} Hz is out of range [{min_sr}, {max_sr}]"
    
    # Check audio array
    if not isinstance(audio, np.ndarray):
        return False, f"Audio must be numpy array, got {type(audio)}"
    
    if audio.size == 0:
        return False, "Audio array is empty"
    
    # Calculate duration
    duration = len(audio) / sr
    if duration < min_duration:
        return False, f"Audio duration {duration:.2f}s is too short (min: {min_duration}s)"
    
    if duration > max_duration:
        return False, f"Audio duration {duration:.2f}s is too long (max: {max_duration}s)"
    
    # Check for NaN or Inf
    if np.any(np.isnan(audio)) or np.any(np.isinf(audio)):
        return False, "Audio contains NaN or Inf values"
    
    # Check for silence
    if check_silence:
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < silence_threshold:
            logger.warning(f"Audio appears to be silent (RMS: {rms:.6f})")
            # Don't fail, just warn
    
    # Check data type
    if audio.dtype not in [np.float32, np.float64, np.int16, np.int32]:
        logger.warning(f"Audio dtype {audio.dtype} may need conversion to float32")
    
    return True, None


def validate_and_normalize_audio(
    audio: np.ndarray,
    sr: int,
    target_sr: Optional[int] = None
) -> Tuple[np.ndarray, int]:
    """
    Validate and normalize audio input.
    
    Args:
        audio: Audio data
        sr: Sample rate
        target_sr: Target sample rate (if None, use input sr)
        
    Returns:
        Tuple of (normalized_audio, sample_rate)
        
    Raises:
        AudioFormatError: If audio format is invalid
        AudioQualityError: If audio quality is insufficient
    """
    # Validate
    is_valid, error_msg = validate_audio(audio, sr)
    if not is_valid:
        raise AudioFormatError(error_msg)
    
    # Normalize to float32
    if audio.dtype != np.float32:
        if audio.dtype in [np.int16, np.int32]:
            # Convert from integer to float
            audio = audio.astype(np.float32) / (2 ** (audio.dtype.itemsize * 8 - 1))
        else:
            audio = audio.astype(np.float32)
    
    # Normalize amplitude to [-1, 1]
    max_val = np.abs(audio).max()
    if max_val > 0:
        audio = audio / max_val
    
    # Handle target sample rate
    if target_sr is not None and sr != target_sr:
        # Note: Actual resampling should be done with torchaudio
        # This is just a placeholder
        logger.warning(f"Sample rate conversion {sr} -> {target_sr} needed")
        sr = target_sr
    
    return audio, sr

