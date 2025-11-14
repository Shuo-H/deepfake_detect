# model/base.py
import torch.nn as nn

class BaseDetector(nn.Module):
    def __init__(self):
        super().__init__()

    def detect(self, audio, sr) -> dict:
        """
        Process a single audio file and return {'label': 'real' or 'fake', 'score': float}
        Subclasses implement the logic.
        """
        raise NotImplementedError("Subclasses must implement detect()")