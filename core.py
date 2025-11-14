# core.py
import os
import sys
from omegaconf import OmegaConf

from gradio_app import launch_gradio
from model import DETECTOR_REGISTRY, DETECTOR_CONFIGS_REGISTER
from loader import load_with_directory

def main():
    # Manually load main.yaml
    cfg = OmegaConf.load("config/main.yaml")
    # Manually load model-specific YAML based on model_name
    model_yaml_path = f"config/{cfg.model_name}.yaml"
    if os.path.exists(model_yaml_path):
        model_cfg = OmegaConf.load(model_yaml_path)
    else:
        raise FileNotFoundError(f"Model config not found: {model_yaml_path}")

    config_class = DETECTOR_CONFIGS_REGISTER.get(model_cfg.config_class)
    if config_class is None:
            raise ValueError(f"Config class not registered: {model_cfg.config_class}")
    import pdb; ipdb.set_trace()
    valid_model_cfg = config_class(model_cfg)
    
    # Build model
    model = DETECTOR_REGISTRY.build({'type': model_cfg.model_class, 'config': valid_model_cfg})

    # Handle load_type (as before)
    if cfg.load_type == 'directory':
        directory = cfg.get('input_dir', 'samples/')
        for audio_path, audio_data, sample_rate in load_with_directory(directory):
            result = model.detect(audio_data, sample_rate)
    elif cfg.load_type == 'gradio':
        launch_gradio(model)

    else:
        raise ValueError(f"Unknown load_type: {cfg.load_type}")

if __name__ == "__main__":
    main()