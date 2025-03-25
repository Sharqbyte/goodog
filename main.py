# This is a sample Python script.
import os
import json
import logging
from util.file_management import scan_source_folder

# Konfigurationsdatei laden
with open("config.json", "r") as f:
    config = json.load(f)

# Configure logging
logfile_path = os.path.join(config["log_folder"], 'file_operations.log')
logging.basicConfig(filename=logfile_path, level=logging.INFO, format='%(asctime)s - %(message)s')

# Process scan files
scan_source_folder()
