import logging
import sys

def setup_logging(log_filename="debug.log"):
    """
    Configures the root logger to log to both a file and the console.
    """
    # Configure logging to a file
    # This will capture all messages at INFO level and above
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=log_filename,
        filemode="w"  # 'a' for append, 'w' to overwrite
    )
    
    # --- Optional: Add console logging ---
    # Get the root logger
    logger = logging.getLogger()
    
    # Check if a console handler (StreamHandler) already exists
    # This prevents duplicate messages if the script is re-run in the same session
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO) # Log level for console
        
        # Create a formatter for the console (simpler format)
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        
        # Add the handler to the root logger
        logger.addHandler(console_handler)
    # -------------------------------------