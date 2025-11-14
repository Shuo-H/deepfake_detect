# gradio_app.py
import gradio as gr

def launch_gradio(model):
    """
    Launches Gradio app with the given model. Handles audio upload and detection.
    Model's detect() will validate audio internally.
    """
    def detect_audio(audio):
        if audio is None:
            return "No audio uploaded."
        try:
            result = model.detect(audio)  # audio is temp filepath; validation inside detect()
            return f"Label: {result['label']}, Score: {result['score']:.4f}"
        except ValueError as e:
            return f"Error: {str(e)}"  # Graceful error for invalid audio

    demo = gr.Interface(
        fn=detect_audio,
        inputs=gr.Audio(type="filepath", label="Upload Audio (WAV/MP3, 16kHz mono recommended)"),
        outputs="text",
        title="Deepfake Audio Detector",
        description="Upload an audio file for deepfake detection."
    )
    demo.launch(share=True)  # share=True for public link if needed