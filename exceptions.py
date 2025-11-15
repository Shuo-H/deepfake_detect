"""
Custom exceptions for the deepfake detection framework.

This module defines custom exception classes for better error handling
and debugging.
"""


class DeepfakeDetectionError(Exception):
    """Base exception for all deepfake detection errors."""
    pass


class ModelError(DeepfakeDetectionError):
    """Base exception for model-related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when a requested model is not found."""
    pass


class ModelLoadError(ModelError):
    """Raised when model loading fails."""
    pass


class ModelInitializationError(ModelError):
    """Raised when model initialization fails."""
    pass


class ConfigError(DeepfakeDetectionError):
    """Base exception for configuration-related errors."""
    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file is not found."""
    pass


class AudioProcessingError(DeepfakeDetectionError):
    """Base exception for audio processing errors."""
    pass


class AudioLoadError(AudioProcessingError):
    """Raised when audio file loading fails."""
    pass


class AudioFormatError(AudioProcessingError):
    """Raised when audio format is unsupported or invalid."""
    pass


class AudioQualityError(AudioProcessingError):
    """Raised when audio quality is insufficient for detection."""
    pass


class DetectionError(DeepfakeDetectionError):
    """Base exception for detection-related errors."""
    pass


class DetectionTimeoutError(DetectionError):
    """Raised when detection times out."""
    pass


class DetectionFailedError(DetectionError):
    """Raised when detection fails."""
    pass

