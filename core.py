import argparse
import logging
import os
import sys  # <-- Import sys to specify console output

#
# import model 
from loader import load_from_directory, load_from_gradio
from logger import setup_logging

def main(args):

    setup_logging(log_filename="debug.log")
    # ----------------------------

    logging.info("--- Script execution started ---")
    
    # load detector
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
    
    # --- CHANGED: Fixed boolean argument ---
    # This creates a flag '--no-log'.
    # By default, 'debug' is True.
    # If the user runs with '--no-log', it sets 'debug' to False.
    parser.add_argument(
        '--no-log',
        dest='debug',             # Store the value in 'args.debug'
        action='store_false',     # If flag is present, store False
        help="Disables debug mode and enables file logging"
    )
    parser.set_defaults(debug=True) # Default value for 'debug' is True
    # ---------------------------------------

    main(parser.parse_args())