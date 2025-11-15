"""
Model Factory for creating and managing detector models.

This module provides a factory pattern for model creation with caching,
version management, and lifecycle control.
"""
import logging
from typing import Dict, Any, Optional
from omegaconf import DictConfig
from functools import lru_cache

from .base import BaseDetector
from . import DETECTOR_REGISTRY, DETECTOR_CONFIGS_REGISTER

# Import initialize_model - using absolute import
# Note: This assumes core.py is in the parent directory
# In a proper package structure, this would be: from ..core import initialize_model
try:
    from core import initialize_model
except ImportError:
    # Fallback for when running as module
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core import initialize_model

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    Factory for creating and managing detector models.
    
    Features:
    - Model instance caching
    - Model metadata management
    - Lifecycle management (load/unload/warmup)
    - Version tracking
    """
    
    def __init__(self):
        """Initialize the model factory."""
        self._cache: Dict[str, BaseDetector] = {}
        self._model_metadata: Dict[str, Dict[str, Any]] = {}
        self._model_configs: Dict[str, DictConfig] = {}
    
    def create(
        self, 
        model_name: str, 
        config: DictConfig,
        use_cache: bool = True,
        warmup: bool = True
    ) -> BaseDetector:
        """
        Create a model instance.
        
        Args:
            model_name: Name identifier for the model
            config: Model configuration
            use_cache: Whether to use cached instance if available
            warmup: Whether to warmup the model after creation
            
        Returns:
            Initialized detector model instance
            
        Raises:
            ValueError: If model creation fails
        """
        # Check cache first
        if use_cache and model_name in self._cache:
            logger.info(f"Using cached model instance: {model_name}")
            return self._cache[model_name]
        
        # Create new model instance
        logger.info(f"Creating new model instance: {model_name}")
        try:
            model = initialize_model(config)
            
            # Store in cache
            if use_cache:
                self._cache[model_name] = model
                self._model_configs[model_name] = config
            
            # Warmup if requested
            if warmup:
                self.warmup_model(model)
            
            # Store metadata
            self._model_metadata[model_name] = {
                'model_class': config.get('model_class'),
                'config_class': config.get('config_class'),
                'created_at': self._get_timestamp(),
                'warmup_done': warmup
            }
            
            logger.info(f"Model {model_name} created successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create model {model_name}: {e}", exc_info=True)
            raise ValueError(f"Model creation failed: {e}") from e
    
    def get_model(self, model_name: str) -> Optional[BaseDetector]:
        """
        Get a cached model instance.
        
        Args:
            model_name: Name identifier for the model
            
        Returns:
            Cached model instance or None if not found
        """
        return self._cache.get(model_name)
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name identifier for the model
            
        Returns:
            True if model was unloaded, False if not found
        """
        if model_name in self._cache:
            # Cleanup if model has cleanup method
            model = self._cache[model_name]
            if hasattr(model, 'cleanup'):
                model.cleanup()
            
            del self._cache[model_name]
            self._model_metadata.pop(model_name, None)
            self._model_configs.pop(model_name, None)
            logger.info(f"Model {model_name} unloaded")
            return True
        return False
    
    def reload_model(self, model_name: str, config: DictConfig) -> BaseDetector:
        """
        Reload a model with new configuration.
        
        Args:
            model_name: Name identifier for the model
            config: New model configuration
            
        Returns:
            Reloaded model instance
        """
        # Unload existing
        self.unload_model(model_name)
        
        # Create new
        return self.create(model_name, config, use_cache=True, warmup=True)
    
    def warmup_model(self, model: BaseDetector) -> None:
        """
        Warmup a model with dummy input.
        
        Args:
            model: Model instance to warmup
        """
        import numpy as np
        logger.info("Warming up model...")
        try:
            # Create dummy audio (1 second at 16kHz)
            dummy_audio = np.random.randn(16000).astype(np.float32)
            dummy_sr = 16000
            
            # Run dummy inference
            _ = model.detect(dummy_audio, dummy_sr)
            logger.info("Model warmup completed")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get metadata for a model.
        
        Args:
            model_name: Name identifier for the model
            
        Returns:
            Dictionary with model metadata
        """
        if model_name not in self._model_metadata:
            raise ValueError(f"Model {model_name} not found")
        
        info = self._model_metadata[model_name].copy()
        info['is_loaded'] = model_name in self._cache
        if model_name in self._model_configs:
            config = self._model_configs[model_name]
            info['config'] = {
                'model_id': config.get('model_id'),
                'device': config.get('device'),
                'resample_rate': config.get('resample_rate')
            }
        return info
    
    def list_models(self) -> list[str]:
        """
        List all loaded model names.
        
        Returns:
            List of model names
        """
        return list(self._cache.keys())
    
    def clear_cache(self) -> None:
        """Clear all cached models."""
        for model_name in list(self._cache.keys()):
            self.unload_model(model_name)
        logger.info("Model cache cleared")
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()


# Global factory instance
_factory_instance: Optional[ModelFactory] = None


def get_factory() -> ModelFactory:
    """
    Get the global model factory instance (singleton).
    
    Returns:
        Global ModelFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ModelFactory()
    return _factory_instance

