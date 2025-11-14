import argparse
import logging
import os
import sys  # <-- Import sys to specify console output

#
# import model 
from loader import load_from_directory, load_from_gradio
from logger import setup_logging

def main(args):

    if args.debug:
        setup_logging(log_filename="debug.log")  # Log to console only

    logging.info("--- Script execution started ---")
    logging.info(f"Loading model: {args.model_name}")
    # detector = model.get_model(args.model_name)
    
    if args.load_type == "directory":
        logging.info("Loading from directory...")

        for audio_path, data, sr in load_from_directory("config/loader.yaml"):
            print(data.shape)
            raise SystemError


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Anti-Spoofing Detection (Gradio UI)")
    parser.add_argument(
        "--model_name",
        type=str,
        default="Speech-Arena-2025/DF_Arena_500M_V_1",
        # help="Hugging Face model name (default: Speech-Arena-2025/DF_Arena_500M_V_1)"
    )
    parser.add_argument(
        "--load_type",
        type=str,
        default="directory",
        choices=["directory", "gradio"],
        help="Loading method (default: directory)"
    )
    
    parser.add_argument(
        '--debug',
        type=bool,
        default=True
    )

    main(parser.parse_args())