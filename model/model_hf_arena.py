# model/model_df_arena.py
import torchaudio
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

    def detect(self, audio, sr) -> dict:
        # Load and preprocess audio (resample to 16kHz)
        if sr != self.config.resample_rate:
            audio = torchaudio.transforms.Resample(sr, self.config.resample_rate)(audio)
        audio = audio.mean(0) if audio.shape[0] > 1 else audio[0]  # To mono

        # Inference
        results = self.pipe(waveform.to(self.config.device))
        score = next(r['score'] for r in results if r['label'] == 'bonafide')  # Assuming 'bonafide' is real
        label = 'real' if score > self.config.threshold else 'fake'

        return {'label': label, 'score': score}