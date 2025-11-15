# model/base.py
import torch.nn as nn
from typing import Dict, Any

class BaseDetector(nn.Module):
    def __init__(self):
        super().__init__()

    def detect(self, audio, sr) -> dict:
        """
        Process a single audio file and return {'label': 'real' or 'fake', 'score': float}
        Subclasses implement the logic.
        """
        raise NotImplementedError("Subclasses must implement detect()")
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """Format prediction result for display"""
        label = result.get('label', 'unknown')
        score = result.get('score', 0.0)
        all_scores = result.get('all_scores', {})
        
        # Get bonafide and spoof scores
        bonafide_score = all_scores.get('bonafide', 0.0)
        spoof_score = all_scores.get('spoof', 0.0)
        
        # Determine prediction
        is_spoof = label == 'spoof'
        confidence = score
        
        # Format output
        output = f"🔍 **Detection Result**\n\n"
        output += f"**Prediction**: {'🚨 SPOOF (Fake)' if is_spoof else '✅ BONAFIDE (Real)'}\n\n"
        output += f"**Confidence**: {confidence:.2%}\n\n"
        output += f"**Scores**:\n"
        output += f"  - Spoof: {spoof_score:.2%}\n"
        output += f"  - Bonafide: {bonafide_score:.2%}\n\n"
        
        if 'logits' in result:
            logits = result['logits']
            if logits and len(logits) > 0:
                output += f"**Logits**: {logits[0]}\n\n"
        
        # Add interpretation
        if is_spoof:
            output += f"⚠️ **Warning**: This audio is likely a deepfake or spoofed audio.\n"
        else:
            output += f"✓ This audio appears to be genuine.\n"
        
        return output