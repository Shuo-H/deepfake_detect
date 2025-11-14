# model/__init__.py
import importlib
import pkgutil

from ..model.registry import Registry


DETECTOR_REGISTRY = Registry("BACKBONE")
DETECTOR_REGISTRY.__doc__ = "Registry for different deepfake detector"

DETECTOR_CONFIGS_REGISTER = Registry("DETECTOR_CONFIGS")
DETECTOR_CONFIGS_REGISTER.__doc__ = "Registry for different deepfake detector configs"

# Import all model modules to register them
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    if not is_pkg:
        importlib.import_module(f"{__name__}.{module_name}")