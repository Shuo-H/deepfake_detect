# gradio_app.py
import logging
import gradio as gr

logger = logging.getLogger(__name__)

def launch_gradio(model):
    """
    Launches Gradio app with the given model. Handles audio upload and detection.
    Model's detect() will validate audio internally.
    """
    def detect_audio(audio):
        if audio is None:
            logger.warning("No audio uploaded")
            return "No audio uploaded."
        try:
            logger.info(f"Processing audio file: {audio}")
            result = model.detect(audio)  # audio is temp filepath; validation inside detect()
            logger.info(f"Detection result: {result}")
            return f"Label: {result['label']}, Score: {result['score']:.4f}"
        except ValueError as e:
            logger.error(f"Validation error during detection: {e}", exc_info=True)
            return f"Error: {str(e)}"  # Graceful error for invalid audio
        except Exception as e:
            logger.error(f"Unexpected error during detection: {e}", exc_info=True)
            return f"Error: {str(e)}"

    demo = gr.Interface(
        fn=detect_audio,
        inputs=gr.Audio(type="filepath", label="Upload Audio (WAV/MP3, 16kHz mono recommended)"),
        outputs="text",
        title="Deepfake Audio Detector",
        description="Upload an audio file for deepfake detection."
    )
    demo.launch(share=True)  # share=True for public link if needed