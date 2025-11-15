# model/model_df_arena.py
import torchaudio
import torch
from transformers import pipeline
from pydantic import Field, BaseModel, field_validator

from .base import BaseDetector
from . import DETECTOR_REGISTRY, DETECTOR_CONFIGS_REGISTER

@DETECTOR_CONFIGS_REGISTER.register()
class DFArenaConfig(BaseModel):  # Model-specific config        
    model_id: str = Field('Speech-Arena-2025/DF_Arena_500M_V_1', description="Hugging Face model ID")
    device: str = Field('cpu', description="Device to run the model on")
    resample_rate: int = Field(16000, description="Resample rate for audio")
    threshold: float = Field(0.5, description="Threshold for classification")
    
    @field_validator('model_id')
    def validate_model_id(cls, v):
        if v not in ['Speech-Arena-2025/DF_Arena_100M_V_1', 'Speech-Arena-2025/DF_Arena_500M_V_1', 'Speech-Arena-2025/DF_Arena_1B_V_1']:
            raise ValueError("Unsupported model_id")
        return v
    
    @field_validator('device')
    def validate_device(cls, v):
        if v not in ['cpu', 'cuda']:
            raise ValueError("Device must be 'cpu' or 'cuda'")
        return v
    @field_validator('threshold')
    def validate_threshold(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v

@DETECTOR_REGISTRY.register()
class DFArena(BaseDetector):
    def __init__(self, config: DFArenaConfig):
        super().__init__()
        self.config = config
        self.pipe = pipeline("antispoofing", model=self.config.model_id, device=self.config.device, trust_remote_code=True)
        
    def _format_result(self, results: dict) -> dict:
        '''Format the raw results from the pipeline.
        
        Args:
            results (dict): Raw output from the antispoofing pipeline.
        '''
        label = results.get('label', 'unknown')
        score = results.get('score', 0.0)
        all_scores = results.get('all_scores', {})
        
        # Get bonafide and spoof scores
        bonafide_score = all_scores.get('bonafide', 0.0)
        spoof_score = all_scores.get('spoof', 0.0)
        
        # Determine prediction
        confidence = score
        return {
            'label': label,
            'is_spoof': label == 'spoof',
            'logits': results.get('logits', []),
            'score': confidence,
            'all_scores': {
                'bonafide': bonafide_score,
                'spoof': spoof_score
            }
        }
        
        
    def detect(self, audio, sr) -> dict:
        '''Detect deepfake in audio data.
        
        Args:
            audio (np.ndarray): Audio data. shape (num_samples,) or (num_channels, num_samples)
            sr (int): Sample rate of the audio data.
            
        Returns:
            results: {'label': 'spoof', 'logits': [[1.5515458583831787, -1.2254822254180908]], 'score': 0.9414217472076416, 'all_scores': {'spoof': 0.9414217472076416, 'bonafide': 0.05857823044061661}}
            dict: Detection result with keys 'label' and 'score'.
        '''
        # mono
        # resample if needed
        if sr != self.config.resample_rate:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=self.config.resample_rate)
            if len(audio.shape) == 1:
                audio = audio.unsqueeze(0)  # add channel dim
            audio = resampler(audio)
            audio = audio.squeeze(0)  # remove channel dim if single channel
            sr = self.config.resample_rate
        import pdb ; pdb.set_trace()
        results = self.pipe(audio)
        return self._format_result(results)