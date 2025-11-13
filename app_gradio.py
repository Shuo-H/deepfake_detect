# app_gradio.py
"""
Contains all Gradio-related UI functions.
This script can be run independently to launch the web app.
"""
import argparse
import gradio as gr
from typing import Dict, Any

# Import the engine from our other file
from detector import AntiSpoofingDetector

def _format_result(result: Dict[str, Any]) -> str:
    """Format prediction result for Gradio display"""
    label = result.get('label', 'unknown')
    score = result.get('score', 0.0)
    all_scores = result.get('all_scores', {})
    
    bonafide_score = all_scores.get('bonafide', 0.0)
    spoof_score = all_scores.get('spoof', 0.0)
    
    is_spoof = label == 'spoof'
    confidence = score
    
    output = f"🔍 **Detection Result**\n\n"
    output += f"**Prediction**: {'🚨 SPOOF (Fake)' if is_spoof else '✅ BONAFIDE (Real)'}\n\n"
    output += f"**Confidence**: {confidence:.2%}\n\n"
    output += f"**Scores**:\n"
    output += f"    - Spoof: {spoof_score:.2%}\n"
    output += f"   - Bonafide: {bonafide_score:.2%}\n\n"
    
    if 'logits' in result:
        logits = result['logits']
        if logits and len(logits) > 0:
            output += f"**Logits**: {logits[0]}\n\n"
    
    if is_spoof:
        output += f"⚠️ **Warning**: This audio is likely a deepfake or spoofed audio.\n"
    else:
        output += f"✓ This audio appears to be genuine.\n"
    
    return output

def create_gradio_interface(model_name: str, server_name: str,
                             server_port: int, share: bool, detector):
    """Create and launch Gradio interface"""
    
    # Initialize detector
    try:
        detector = AntiSpoofingDetector(
            model_name=model_name, 
            device=device,
            trust_remote_code=trust_remote_code
        )
    except Exception as e:
        print(f"Failed to initialize detector: {e}")
        return
    
    title = "🎤 Audio Anti-Spoofing Detection"
    description = f"""
    Upload an audio file to detect if it's a **spoof (deepfake)** or **bonafide (real)** audio.
    **Model**: {model_name}
    """
    
    def predict_audio(audio):
        """Wrapper function for Gradio"""
        if audio is None:
            return "❌ Please upload an audio file"
        try:
            # 1. Get raw dict result from the engine
            result_dict = detector.predict(audio_path=None, audio_data=audio)
            # 2. Format the dict for UI display
            return _format_result(result_dict)
        except Exception as e:
            return f"❌ Error processing audio: {str(e)}"
    
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
    """Main function to launch Gradio from command line"""
    parser = argparse.ArgumentParser(description="Audio Anti-Spoofing Detection (Gradio UI)")
    parser.add_argument("--model_name", type=str, default="Speech-Arena-2025/DF_Arena_500M_V_1", help="Hugging Face model name")
    parser.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"], help="Device to use")
    parser.add_argument("--server_name", type=str, default="0.0.0.0", help="Gradio server host")
    parser.add_argument("--server_port", type=int, default=7860, help="Gradio server port")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link")
    parser.add_argument("--no_trust_remote_code", action="store_true", help="Do not trust remote code")
    
    args = parser.parse_args()
    
    create_gradio_interface(
        model_name=args.model_name,
        device=args.device,
        server_name=args.server_name,
        server_port=args.server_port,
        share=args.share,
        trust_remote_code=not args.no_trust_remote_code
    )

if __name__ == "__main__":
    main()