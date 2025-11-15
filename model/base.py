"""
Base detector class for deepfake audio detection.

This module provides the abstract base class that all detector implementations
must inherit from.
"""
import torch.nn as nn
import numpy as np
from typing import Dict, Any

class BaseDetector(nn.Module):
    """Base class for all deepfake audio detectors."""
    
    def __init__(self):
        """Initialize the base detector."""
        super().__init__()

    def detect(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Process a single audio file and return detection results.
        
        Args:
            audio: Audio data as numpy array
            sr: Sample rate of the audio in Hz
            
        Returns:
            Dictionary with detection results containing at least:
                - 'label': 'spoof' or 'bonafide'
                - 'score': Confidence score (float)
                
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement detect()")
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format prediction result for display in markdown.
        
        Args:
            result: Detection result dictionary from detect() method
            
        Returns:
            Formatted markdown string for display
        """
        label = result.get('label', 'unknown')
        score = result.get('score', 0.0)
        all_scores = result.get('all_scores', {})
        
        # Extract bonafide and spoof scores
        bonafide_score = all_scores.get('bonafide', 0.0)
        spoof_score = all_scores.get('spoof', 0.0)
        
        # Determine prediction
        is_spoof = label == 'spoof'
        confidence = score
        
        # Format output
        output = "🔍 **Detection Result**\n\n"
        output += f"**Prediction**: {'🚨 SPOOF (Fake)' if is_spoof else '✅ BONAFIDE (Real)'}\n\n"
        output += f"**Confidence**: {confidence:.2%}\n\n"
        output += "**Scores**:\n"
        output += f"  - Spoof: {spoof_score:.2%}\n"
        output += f"  - Bonafide: {bonafide_score:.2%}\n\n"
        
        # Add logits if available
        if 'logits' in result:
            logits = result['logits']
            if logits and len(logits) > 0:
                output += f"**Logits**: {logits[0]}\n\n"
        
        # Add interpretation
        if is_spoof:
            output += "⚠️ **Warning**: This audio is likely a deepfake or spoofed audio.\n"
        else:
            output += "✓ This audio appears to be genuine.\n"
        
        return output