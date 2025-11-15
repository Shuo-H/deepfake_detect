"""
Main entry point for the deepfake detection application.

This module handles configuration loading, model initialization, audio file loading,
and orchestrates the detection workflow.
"""
import os
import logging
from omegaconf import OmegaConf, DictConfig

import soundfile as sf
import numpy as np

from gradio_app import launch_gradio
from model import DETECTOR_REGISTRY, DETECTOR_CONFIGS_REGISTER
from logger import setup_logging

logger = logging.getLogger(__name__)

# Supported audio file extensions
AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma",
    ".opus", ".aiff", ".aif"
}

def load_config(config_path: str) -> DictConfig:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        OmegaConf DictConfig object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    return OmegaConf.load(config_path)


def initialize_model(model_cfg: DictConfig):
    """
    Initialize the detector model from configuration.
    
    Args:
        model_cfg: Model configuration dictionary
        
    Returns:
        Initialized detector model instance
        
    Raises:
        ValueError: If config or model class is not registered
    """
    config_class_name = model_cfg.get('config_class')
    model_class_name = model_cfg.get('model_class')
    
    if not config_class_name:
        raise ValueError("config_class not specified in model configuration")
    if not model_class_name:
        raise ValueError("model_class not specified in model configuration")
    
    # Get and validate config class
    config_class = DETECTOR_CONFIGS_REGISTER.get(config_class_name)
    if config_class is None:
        raise ValueError(f"Config class '{config_class_name}' not registered. "
                        f"Available: {list(DETECTOR_CONFIGS_REGISTER._obj_map.keys())}")
    
    # Create validated config instance
    valid_model_cfg = config_class(**model_cfg)
    
    # Get and validate model class
    model_class = DETECTOR_REGISTRY.get(model_class_name)
    if model_class is None:
        raise ValueError(f"Model class '{model_class_name}' not registered. "
                        f"Available: {list(DETECTOR_REGISTRY._obj_map.keys())}")
    
    # Build model
    model = model_class(valid_model_cfg)
    return model


def process_directory(model, directory: str, logger: logging.Logger) -> int:
    """
    Load and process all audio files in a directory recursively.
    
    Args:
        model: Initialized detector model
        directory: Path to directory containing audio files
        logger: Logger instance
    
    Returns:
        Number of files processed successfully
    
    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If path is not a directory
    """
    # Validate directory
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not os.path.isdir(directory):
        raise ValueError(f"Path is not a directory: {directory}")
    
    logger.info(f"Processing audio files from directory: {directory}")
    processed_count = 0
    
    # Walk through directory and process audio files
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            # Check if file has supported audio extension
            _, ext = os.path.splitext(filename)
            if ext.lower() not in AUDIO_EXTENSIONS:
                continue
            
            audio_path = os.path.join(dirpath, filename)
            
            # Load audio file
            try:
                audio_data, sample_rate = sf.read(audio_path)
                logger.debug(f"Successfully loaded {audio_path} (shape: {audio_data.shape}, sample rate: {sample_rate} Hz)")
            except Exception as e:
                logger.error(f"Error loading {audio_path}: {e}", exc_info=True)
                continue
            
            # Process audio with model
            try:
                result = model.detect(audio_data, sample_rate)
                logger.info(f"Detection result for {audio_path}: {result}")
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing {audio_path}: {e}", exc_info=True)
                continue
    
    logger.info(f"Processed {processed_count} audio file(s)")
    return processed_count


def main():
    """Main entry point for the deepfake detection application."""
    # Setup logging first
    log_file = setup_logging(log_dir="logs", log_level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting deepfake detection application")
    
    try:
        # Load main configuration
        logger.info("Loading main configuration from config/main.yaml")
        cfg = load_config("config/main.yaml")
        
        # Load model-specific configuration
        model_name = cfg.get('model_name')
        if not model_name:
            raise ValueError("model_name not specified in main configuration")
        
        model_yaml_path = f"config/{model_name}.yaml"
        logger.info(f"Loading model configuration from {model_yaml_path}")
        model_cfg = load_config(model_yaml_path)
        
        # Initialize model
        logger.info(f"Initializing model: {model_cfg.get('model_class')} "
                   f"with config: {model_cfg.get('config_class')}")
        model = initialize_model(model_cfg)
        logger.info("Model built successfully")
        
        # Handle different load types
        load_type = cfg.get('load_type')
        logger.info(f"Load type: {load_type}")
        
        if load_type == 'directory':
            directory = cfg.get('input_dir', 'samples/')
            process_directory(model, directory, logger)
            
        elif load_type == 'gradio':
            logger.info("Launching Gradio interface...")
            server_name = cfg.get('server_name', '0.0.0.0')
            server_port = cfg.get('server_port', 7860)
            share = cfg.get('share', False)
            launch_gradio(model, server_name, server_port, share)
            
        else:
            raise ValueError(f"Unknown load_type: {load_type}. Must be 'directory' or 'gradio'")
        
        logger.info("Application finished")
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()