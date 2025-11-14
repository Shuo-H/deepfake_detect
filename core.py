# core.py
import os
import sys
import logging
from omegaconf import OmegaConf

from gradio_app import launch_gradio
from model import DETECTOR_REGISTRY, DETECTOR_CONFIGS_REGISTER
from loader import load_with_directory
from logger import setup_logging

def main():
    # Setup logging first
    setup_logging(log_filename="debug.log", log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting deepfake detection application")
    
    # Manually load main.yaml
    logger.info("Loading main configuration from config/main.yaml")
    cfg = OmegaConf.load("config/main.yaml")
    
    # Manually load model-specific YAML based on model_name
    model_yaml_path = f"config/{cfg.model_name}.yaml"
    if os.path.exists(model_yaml_path):
        logger.info(f"Loading model configuration from {model_yaml_path}")
        model_cfg = OmegaConf.load(model_yaml_path)
    else:
        logger.error(f"Model config not found: {model_yaml_path}")
        raise FileNotFoundError(f"Model config not found: {model_yaml_path}")

    logger.info(f"Initializing model: {model_cfg.model_class} with config: {model_cfg.config_class}")
    config_class = DETECTOR_CONFIGS_REGISTER.get(model_cfg.config_class)
    if config_class is None:
        logger.error(f"Config class not registered: {model_cfg.config_class}")
        raise ValueError(f"Config class not registered: {model_cfg.config_class}")
    valid_model_cfg = config_class(**model_cfg)
    
    # Build model
    logger.info("Building model...")
    model = DETECTOR_REGISTRY.get(model_cfg.model_class)(valid_model_cfg)
    logger.info("Model built successfully")

    # Handle load_type (as before)
    logger.info(f"Load type: {cfg.load_type}")
    if cfg.load_type == 'directory':
        directory = cfg.get('input_dir', 'samples/')
        logger.info(f"Processing audio files from directory: {directory}")
        processed_count = 0
        for audio_path, audio_data, sample_rate in load_with_directory(directory):
            logger.debug(f"Processing audio file: {audio_path} (sample rate: {sample_rate} Hz)")
            result = model.detect(audio_data, sample_rate)
            logger.info(f"Detection result for {audio_path}: {result}")
            processed_count += 1
        logger.info(f"Processed {processed_count} audio file(s)")
    elif cfg.load_type == 'gradio':
        logger.info("Launching Gradio interface...")
        launch_gradio(model)
    else:
        logger.error(f"Unknown load_type: {cfg.load_type}")
        raise ValueError(f"Unknown load_type: {cfg.load_type}")
    
    logger.info("Application finished")

if __name__ == "__main__":
    main()