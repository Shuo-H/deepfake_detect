"""
Hugging Face Audio Anti-Spoofing Detection with Gradio Interface
Using Speech-Arena-2025/DF_Arena_500M_V_1 model
"""
import argparse
import os
import warnings
from typing import Optional, Dict, Any

import gradio as gr
import librosa
import numpy as np
from transformers import pipeline

warnings.filterwarnings("ignore", category=FutureWarning)

class AntiSpoofingDetector:
    """Audio Anti-Spoofing Detector using Hugging Face Transformers"""
    
    def __init__(self, model_name: str = "Speech-Arena-2025/DF_Arena_500M_V_1", 
                 device: str = "cuda", trust_remote_code: bool = True):
        """
        Initialize the anti-spoofing detector
        
        Args:
            model_name: Hugging Face model identifier
            device: Device to use ('cuda' or 'cpu')
            trust_remote_code: Whether to trust remote code
        """
        self.model_name = model_name
        self.device = device if device == "cuda" and self._check_cuda() else "cpu"
        self.trust_remote_code = trust_remote_code
        self.pipe = None
        self._load_model()
    
    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """Load the anti-spoofing model"""
        try:
            print(f"Loading model: {self.model_name}")
            print(f"Device: {self.device}")
            self.pipe = pipeline(
                "antispoofing",
                model=self.model_name,
                trust_remote_code=self.trust_remote_code,
                device=self.device
            )
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def predict(self, audio_path: Optional[str], audio_data: Optional[tuple] = None) -> str:
            """
            Predict if audio is spoof or bonafide
            ...
            """
            if self.pipe is None:
                return "❌ Error: Model not loaded"
            
            try:
                # Handle different input types
                if audio_data is not None:
                    # Gradio audio input: (sample_rate, audio_array)
                    sr, audio = audio_data
                    
                    # --- START: CORRECTED NORMALIZATION LOGIC ---
                    
                    # Check if audio is an integer type (e.g., int16)
                    if np.issubdtype(audio.dtype, np.integer):
                        # Normalize to float32 in [-1, 1]
                        max_val = np.iinfo(audio.dtype).max
                        audio = audio.astype(np.float32) / max_val
                    
                    # Check if audio is already a float type
                    elif np.issubdtype(audio.dtype, np.floating):
                        # Just ensure it's float32
                        audio = audio.astype(np.float32)
                    
                    else:
                        return f"❌ Error: Unsupported audio data type {audio.dtype}"
                    
                    # --- END: CORRECTED NORMALIZATION LOGIC ---
                    
                    # Resample to 16kHz if needed
                    if sr != 16000:
                        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                
                elif audio_path:
                    # File path input (librosa handles normalization by default)
                    audio, sr = librosa.load(audio_path, sr=16000)
                
                else:
                    return "❌ Error: No audio provided"
                
                # Ensure mono audio
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=0)
                
                # Run prediction
                result = self.pipe(audio)
                
                # Format result
                return self._format_result(result)
                
            except Exception as e:
                # The error message will now be more informative if something else fails
                return f"❌ Error processing audio: {str(e)}"
    
    def _format_result(self, result: Dict[str, Any]) -> str:
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

def create_gradio_interface(model_name: str = "Speech-Arena-2025/DF_Arena_500M_V_1",
                           device: str = "cuda",
                           server_name: str = "0.0.0.0",
                           server_port: int = 7860,
                           share: bool = False):
    """Create and launch Gradio interface"""
    
    # Initialize detector
    try:
        detector = AntiSpoofingDetector(model_name=model_name, device=device)
    except Exception as e:
        print(f"Failed to initialize detector: {e}")
        return
    
    # Create Gradio interface
    title = "🎤 Audio Anti-Spoofing Detection"
    description = """
    Upload an audio file to detect if it's a **spoof (deepfake)** or **bonafide (real)** audio.
    
    **Model**: Speech-Arena-2025/DF_Arena_500M_V_1
    
    **How it works**:
    - The model analyzes audio features to detect spoofing attacks
    - Returns confidence scores for both spoof and bonafide classes
    - Higher spoof score indicates a higher likelihood of deepfake/spoofing
    
    **Supported formats**: WAV, MP3, M4A, FLAC, OGG (will be resampled to 16kHz)
    """
    
    def predict_audio(audio):
        """Wrapper function for Gradio"""
        if audio is None:
            return "❌ Please upload an audio file"
        return detector.predict(audio_path=None, audio_data=audio)
    
    iface = gr.Interface(
        fn=predict_audio,
        inputs=gr.Audio(
            type="numpy",
            label="Upload Audio File",
            sources=["upload", "microphone"]
        ),
        outputs=gr.Markdown(label="Detection Result"),
        title=title,
        description=description,
        examples=None,
        theme=gr.themes.Soft(),
        allow_flagging="never"
    )
    
    print("🚀 Starting Gradio interface...")
    print(f"🌐 Server will be available at http://{server_name}:{server_port}")
    print(f"📦 Model: {model_name}")
    print(f"💻 Device: {detector.device}")
    
    iface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )

def main():
    parser = argparse.ArgumentParser(
        description="Audio Anti-Spoofing Detection with Hugging Face",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch Gradio interface:
  python hf_detection.py
  
  # Custom model:
  python hf_detection.py --model_name "your-model-name"
  
  # CPU mode:
  python hf_detection.py --device cpu
  
  # Custom port:
  python hf_detection.py --server_port 8080
        """
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="Speech-Arena-2025/DF_Arena_500M_V_1",
        help="Hugging Face model name (default: Speech-Arena-2025/DF_Arena_500M_V_1)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to use (default: cuda)"
    )
    parser.add_argument(
        "--server_name",
        type=str,
        default="0.0.0.0",
        help="Gradio server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--server_port",
        type=int,
        default=7860,
        help="Gradio server port (default: 7860)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public Gradio share link"
    )
    parser.add_argument(
        "--no_trust_remote_code",
        action="store_true",
        help="Do not trust remote code (default: trust_remote_code=True)"
    )
    
    args = parser.parse_args()
    
    create_gradio_interface(
        model_name=args.model_name,
        device=args.device,
        server_name=args.server_name,
        server_port=args.server_port,
        share=args.share
    )

if __name__ == "__main__":
    main()