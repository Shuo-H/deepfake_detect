"""
HuggingFace-based deepfake audio detector using DF_Arena models.

This module provides the DFArena detector class and its configuration.
"""
import torchaudio
import torch
import numpy as np
from typing import Dict, Any
from transformers import pipeline
from pydantic import Field, BaseModel, field_validator

from .base import BaseDetector
from . import DETECTOR_REGISTRY, DETECTOR_CONFIGS_REGISTER

@DETECTOR_CONFIGS_REGISTER.register()
class DFArenaConfig(BaseModel):
    """Configuration for DFArena deepfake detector model."""
    
    model_id: str = Field(
        'Speech-Arena-2025/DF_Arena_500M_V_1',
        description="Hugging Face model ID"
    )
    device: str = Field('cpu', description="Device to run the model on")
    resample_rate: int = Field(16000, description="Resample rate for audio")
    threshold: float = Field(0.5, description="Threshold for classification")
    
    @field_validator('model_id')
    def validate_model_id(cls, v: str) -> str:
        """Validate that the model_id is supported."""
        supported_models = [
            'Speech-Arena-2025/DF_Arena_100M_V_1',
            'Speech-Arena-2025/DF_Arena_500M_V_1',
            'Speech-Arena-2025/DF_Arena_1B_V_1'
        ]
        if v not in supported_models:
            raise ValueError(f"Unsupported model_id: {v}. Must be one of {supported_models}")
        return v
    
    @field_validator('device')
    def validate_device(cls, v: str) -> str:
        """Validate that the device is either 'cpu' or 'cuda'."""
        if v not in ['cpu', 'cuda']:
            raise ValueError("Device must be 'cpu' or 'cuda'")
        return v
    
    @field_validator('threshold')
    def validate_threshold(cls, v: float) -> float:
        """Validate that threshold is between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v

@DETECTOR_REGISTRY.register()
class DFArena(BaseDetector):
    """Deepfake audio detector using HuggingFace DF_Arena models."""
    
    def __init__(self, config: DFArenaConfig):
        """
        Initialize the DFArena detector.
        
        Args:
            config: Configuration object for the detector
        """
        super().__init__()
        self.config = config
        self.pipe = pipeline(
            "antispoofing",
            model=self.config.model_id,
            device=self.config.device,
            trust_remote_code=True
        )
        
    def _format_result(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the raw results from the pipeline.
        
        Args:
            results: Raw output from the antispoofing pipeline
            
        Returns:
            Formatted result dictionary with label, score, and all_scores
        """
        label = results.get('label', 'unknown')
        score = results.get('score', 0.0)
        all_scores = results.get('all_scores', {})
        
        # Extract bonafide and spoof scores
        bonafide_score = all_scores.get('bonafide', 0.0)
        spoof_score = all_scores.get('spoof', 0.0)
        
        return {
            'label': label,
            'is_spoof': label == 'spoof',
            'logits': results.get('logits', []),
            'score': score,
            'all_scores': {
                'bonafide': bonafide_score,
                'spoof': spoof_score
            }
        }
        
    def detect(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Detect deepfake in audio data.
        
        Args:
            audio: Audio data as numpy array. Shape: (num_samples,) or (num_channels, num_samples)
            sr: Sample rate of the audio data in Hz
            
        Returns:
            Detection result dictionary with keys:
                - 'label': 'spoof' or 'bonafide'
                - 'score': Confidence score for the prediction
                - 'all_scores': Dictionary with 'spoof' and 'bonafide' scores
                - 'logits': Raw logits from the model
                - 'is_spoof': Boolean indicating if audio is spoofed
        """
        # Resample if needed (requires torch tensors)
        if sr != self.config.resample_rate:
            # Convert to torch tensor for resampling
            if isinstance(audio, np.ndarray):
                audio_tensor = torch.from_numpy(audio).float()
            elif isinstance(audio, torch.Tensor):
                audio_tensor = audio.float()
            else:
                audio_tensor = torch.tensor(audio, dtype=torch.float32)
            
            # Create resampler
            resampler = torchaudio.transforms.Resample(
                orig_freq=sr,
                new_freq=self.config.resample_rate
            )
            
            # Add channel dimension if mono (single channel)
            if len(audio_tensor.shape) == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Resample
            audio_tensor = resampler(audio_tensor)
            
            # Remove channel dimension if single channel
            if audio_tensor.shape[0] == 1:
                audio_tensor = audio_tensor.squeeze(0)
            
            # Convert back to numpy for pipeline
            audio = audio_tensor.numpy()
            sr = self.config.resample_rate
        else:
            # No resampling needed - ensure numpy array
            if isinstance(audio, torch.Tensor):
                audio = audio.numpy()
            elif not isinstance(audio, np.ndarray):
                audio = np.array(audio, dtype=np.float32)
        
        # Run detection
        results = self.pipe(audio)
        return self._format_result(results)