"""
Gradio web interface for deepfake audio detection.

This module provides a Gradio-based web UI for uploading and detecting
deepfake audio files.
"""
import gradio as gr
import numpy as np
from typing import Optional, Tuple


def launch_gradio(model,
                server_name: str = "0.0.0.0",
                server_port: int = 7860,
                share: bool = False):
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

    def detect_audio(audio: Optional[Tuple[int, np.ndarray]]):
        """
        Wrapper function for Gradio audio detection.
        
        Args:
            audio: Tuple of (sample_rate, audio_data) from Gradio, or None
        
        Returns:
            Formatted detection result string
        """
        if audio is None:
            return "❌ Please upload an audio file"
        
        # Gradio Audio component returns (sample_rate, audio_data)
        sample_rate, audio_data = audio
        
        # Run detection
        result = model.detect(audio_data, sample_rate)
        formatted_result = model.format_result(result)
        return formatted_result
    
    iface = gr.Interface(
        fn=detect_audio,
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
    
    iface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )
