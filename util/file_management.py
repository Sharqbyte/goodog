import os
import json
import shutil
import logging
from util.str_util import Utils
from util.extract_text import DataExtractorUtil
from util.configuration_util import ConfigUtil
from datetime import datetime

class FileManagement:

    def __init__(self, config_path):
        ConfigUtil.load_config(config_path)

    # Scan source folder for PDF files
    def scan_source_folder(self):
        logging.info(f"Scan source folder")
        # Load pdf files from scan folder
        for filename in os.listdir(ConfigUtil.get_posteingang_folder()):
            data_extractor = DataExtractorUtil(ConfigUtil.get_config(), r'--oem 3 --psm 6 -l deu+eng')

            if filename.endswith(".pdf"):
                pdf_path = os.path.join(ConfigUtil.get_posteingang_folder(), filename)
                recipient = None  # Initialize recipient variable
                supplier = None  # Initialize supplier variable
                invoice_number = None  # Initialize invoice_number variable
                date = None  # Initialize date variable
                invoice = None  # Initialize invoice variable
                reference = None  # Initialize reference variable

                try:
                    # Extract text from PDF
                    invoice, reference, date, invoice_number, supplier, recipient = data_extractor.extract_text(pdf_path)

                    # Rename and move file
                    self.rename_and_move_file(pdf_path, invoice, reference, date, invoice_number, supplier, recipient)
                except Exception as e:
                    # Anything goes wrong: Move file to unknown folder
                    logging.error(f"Error processing file {pdf_path}: {e}")
                    logging.debug("Exception details:", exc_info=True)
                    logging.debug(f"Empfänger: {recipient}")
                    logging.debug(f"Lieferant: {supplier}")
                    logging.debug(f"Rechnungsnummer: {invoice_number}")
                    logging.debug(f"Datum: {date}")
                    logging.debug(f"Rechnung / Schriftverkehr: {invoice}")
                    logging.debug(f"Referenz: {reference}")
                    unknown_path = os.path.join(ConfigUtil.get_unknown_folder(), filename)
                    shutil.move(pdf_path, unknown_path)
                    logging.info(f"Moved file to unknown folder: {unknown_path}")

    # Rename and move file to archive folder
    def rename_and_move_file(self, pdf_path, invoice, reference, date, invoice_number, supplier, recipient):
        original_filename = os.path.basename(pdf_path)
        archive_folder = None
        logging.debug(f"Date: {date}")

        parsed_date = Utils.parse_date(date) if date else None

        formatted_date = parsed_date.strftime('%y%m%d') if parsed_date else "Unknown"
        year = parsed_date.strftime('%Y') if parsed_date else None
        logging.debug(f"Year: {year}")
        overwrite_file = True

        if invoice:
            new_filename = f"{formatted_date}_{invoice_number or 'Unknown'}_{supplier or 'Unknown'}.pdf"
            if not date or not invoice_number:
                overwrite_file = False
                if recipient == "Medmind":
                    archive_folder = ConfigUtil.get_medmind_invoice_rename_folder()
                elif recipient == "Perspectify":
                    archive_folder = ConfigUtil.get_perspectify_invoice_rename_folder()
                elif recipient == "Immo":
                    archive_folder = ConfigUtil.get_immo_invoice_rename_folder()
                elif recipient == "Private":
                    archive_folder = ConfigUtil.get_private_invoice_rename_folder()
                else:
                    archive_folder = ConfigUtil.get_unknown_folder()
            else:
                if recipient == "Medmind":
                    archive_folder = ConfigUtil.get_medmind_invoice_folder()
                elif recipient == "Perspectify":
                    archive_folder = ConfigUtil.get_perspectify_invoice_folder()
                elif recipient == "Immo":
                    archive_folder = ConfigUtil.get_immo_invoice_folder()
                elif recipient == "Private":
                    archive_folder = ConfigUtil.get_private_invoice_folder()

                    # Add year as subfolder to correspondence path if year is available
                    if year:
                        archive_folder = os.path.join(archive_folder, str(year))
                        os.makedirs(archive_folder, exist_ok=True)
                else:
                    archive_folder = ConfigUtil.get_unknown_folder()
                    overwrite_file = False
        else:
            new_filename = f"{formatted_date}_{supplier or 'Unknown'}.pdf"
            if not date or not supplier:
                archive_folder = ConfigUtil.get_unknown_folder()
                overwrite_file = False
            else:
                if recipient == "Medmind":
                    archive_folder = ConfigUtil.get_medmind_correspondence_folder()
                elif recipient == "Perspectify":
                    archive_folder = ConfigUtil.get_perspectify_correspondence_folder()
                elif recipient == "Immo":
                    archive_folder = ConfigUtil.get_immo_correspondence_folder()
                elif recipient == "Private":
                    archive_folder = ConfigUtil.get_private_correspondence_folder()
                else:
                    archive_folder = ConfigUtil.get_unknown_folder()
                    overwrite_file = False

                # Add year as subfolder to correspondence path if year is available
                if year:
                    archive_folder = os.path.join(archive_folder, str(year))
                    os.makedirs(archive_folder, exist_ok=True)

        destination_path = os.path.join(archive_folder, new_filename)
        if os.path.exists(destination_path) and not overwrite_file:
            new_filename = Utils.add_timestamp_to_filename(new_filename)
            destination_path = os.path.join(archive_folder, new_filename)

        logging.debug(f"Empfänger: {recipient}")
        logging.debug(f"Lieferant: {supplier}")
        logging.debug(f"Rechnungsnummer: {invoice_number}")
        logging.debug(f"Datum: {date}")
        logging.debug(f"Rechnung / Schriftverkehr: {invoice}")
        logging.debug(f"Referenz: {reference}")
        logging.info(f"Moved file to archive: {archive_folder}/{new_filename}")

        shutil.move(pdf_path, destination_path)