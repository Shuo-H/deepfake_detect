import os
import importlib
from .base import BaseModel


MODELS = {}

def register(model_name: str):
    """
    """
    def decorator(model_class):
        if not issubclass(model_class, BaseModel):
            raise TypeError(f"{model_class.__name__} must inherit from BaseModel")
            
        MODELS[model_name] = model_class
        return model_class
    return decorator


# 2. core.py model by name
def get_model(model_name: str) -> BaseModel:
    """
    """
    if model_name not in MODELS:
        raise ValueError(f"Model '{model_name}' is not registered.")
    
    # return an instance of the model
    return MODELS[model_name]()


# 3. auto-import all model modules in the current package
# will run while importing model package

# Get the directory of the current file
package_dir = os.path.dirname(__file__)

# Iterate over all Python files in the directory
for filename in os.listdir(package_dir):
    if filename.endswith(".py") and filename not in ("__init__.py", "base.py"):
        # Import the module to register the model
        module_name = f".{filename[:-3]}"
        importlib.import_module(module_name, package=__name__)