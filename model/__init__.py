# model/__init__.py
from mmengine import Registry

MODELS = Registry('models', scope='model')  # For models
CONFIGS = Registry('configs', scope='model')  # For model-specific configs

# Import all model modules to register them
from .model_zoo import *