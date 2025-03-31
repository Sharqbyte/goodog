import logging
import os
import sys
from datetime import datetime
from util.file_management import FileManagement
from util.configuration_util import ConfigUtil
import logging.handlers

def setup_logging(log_dir: str) -> str:
    """Configure the logging system with rotation and error handling"""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"goodog_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # FileHandler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Console Handler for real-time feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return log_file

def main():
    try:
        config_path = 'config.json'
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        ConfigUtil.load_config(config_path)  # Ensure configuration is loaded first
        logging.debug(f"Configuration loaded: {ConfigUtil.get_config()}")

        log_path = setup_logging(ConfigUtil.get_log_folder())  # Use the correct folder for logs

        logging.info(f"Logfile: {log_path}")
        logging.info("Script start - Configuration loaded")

        file_manager = FileManagement(config_path)
        file_manager.scan_source_folder()

    except Exception as e:
        logging.exception("Critical error in main process:")
        logging.debug("Exception details:", exc_info=True)
        sys.exit(1)
    finally:
        logging.info("Script end\n" + "=" * 50)

if __name__ == "__main__":
    main()