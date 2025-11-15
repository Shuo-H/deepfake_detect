"""
Model adapters for normalizing input/output across different models.

This module provides adapters to handle differences between model interfaces,
ensuring consistent behavior across different detector implementations.
"""
import numpy as np
import torch
from typing import Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod

from .base import BaseDetector


class ModelAdapter(ABC):
    """
    Abstract adapter for normalizing model inputs and outputs.
    
    Different models may have different input/output formats.
    Adapters provide a unified interface.
    """
    
    @abstractmethod
    def normalize_input(
        self, 
        audio: np.ndarray, 
        sr: int,
        target_sr: int = 16000
    ) -> Tuple[np.ndarray, int]:
        """
        Normalize audio input to model requirements.
        
        Args:
            audio: Input audio data
            sr: Sample rate of input audio
            target_sr: Target sample rate
            
        Returns:
            Tuple of (normalized_audio, sample_rate)
        """
        pass
    
    @abstractmethod
    def normalize_output(
        self, 
        raw_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize model output to standard format.
        
        Args:
            raw_result: Raw output from model
            
        Returns:
            Standardized result dictionary
        """
        pass


class StandardAdapter(ModelAdapter):
    """
    Standard adapter for models with common input/output formats.
    """
    
    def normalize_input(
        self, 
        audio: np.ndarray, 
        sr: int,
        target_sr: int = 16000
    ) -> Tuple[np.ndarray, int]:
        """Normalize audio input."""
        # Ensure numpy array
        if isinstance(audio, torch.Tensor):
            audio = audio.numpy()
        elif not isinstance(audio, np.ndarray):
            audio = np.array(audio, dtype=np.float32)
        
        # Ensure float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize to [-1, 1] if needed
        if audio.max() > 1.0 or audio.min() < -1.0:
            audio = audio / (np.abs(audio).max() + 1e-8)
        
        # Resample if needed (simplified - actual resampling should use torchaudio)
        if sr != target_sr:
            # This is a placeholder - actual implementation should use proper resampling
            import warnings
            warnings.warn(f"Sample rate mismatch: {sr} != {target_sr}. "
                         f"Proper resampling should be implemented.")
        
        return audio, target_sr
    
    def normalize_output(
        self, 
        raw_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize model output to standard format."""
        # Ensure standard keys exist
        result = {
            'label': raw_result.get('label', 'unknown'),
            'score': float(raw_result.get('score', 0.0)),
            'all_scores': raw_result.get('all_scores', {}),
            'is_spoof': raw_result.get('is_spoof', False),
            'logits': raw_result.get('logits', []),
            'confidence': raw_result.get('score', 0.0)
        }
        
        # Ensure all_scores has both keys
        if 'bonafide' not in result['all_scores']:
            result['all_scores']['bonafide'] = 1.0 - result['score']
        if 'spoof' not in result['all_scores']:
            result['all_scores']['spoof'] = result['score']
        
        return result


class AdapterRegistry:
    """Registry for model adapters."""
    
    def __init__(self):
        self._adapters: Dict[str, ModelAdapter] = {}
        self._default_adapter = StandardAdapter()
    
    def register(self, model_name: str, adapter: ModelAdapter) -> None:
        """Register an adapter for a model."""
        self._adapters[model_name] = adapter
    
    def get(self, model_name: str) -> ModelAdapter:
        """Get adapter for a model, or default if not found."""
        return self._adapters.get(model_name, self._default_adapter)


# Global adapter registry
ADAPTER_REGISTRY = AdapterRegistry()

