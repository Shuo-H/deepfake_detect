# model/base.py

from abc import ABC, abstractmethod
import numpy as np

class BaseModel(ABC):
    """
    """
    
    @abstractmethod
    def predict(self, audio: np.ndarray, sr: int) -> dict:
        """
        """
        pass