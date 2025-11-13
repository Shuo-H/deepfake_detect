import yaml
import soundfile as sf
import os

AUDIO_EXTENSIONS = {
        ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma",
        ".opus", ".aiff", ".aif"
    }


def load_from_directory(config_path: str):
    config = yaml.safe_load(open(config_path, 'r'))
    directory = config.get("directory", "samples")
    for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                # Check the extension
                _, ext = os.path.splitext(filename)
                if ext.lower() in AUDIO_EXTENSIONS:
                    audio_path = os.path.join(dirpath, filename)
                    data, sr = sf.read(audio_path)
                    yield audio_path, data, sr

    
def load_from_gradio(config_path: str):
    pass