import os
import json
import shutil
import logging
from dateutil import parser
import dateparser

import util.extract_text

pdf_path = None

# Konfigurationsdatei laden
with open("config.json", "r") as f:
    config = json.load(f)

scan_folder = config["scan_folder"]
medmind_invoice_folder = config["medmind_invoice_folder"]
perspectify_invoice_folder = config["perspectify_invoice_folder"]
immo_invoice_folder = config["immo_invoice_folder"]
private_invoice_folder = config["private_invoice_folder"]
medmind_correspondence_folder = config["medmind_correspondence_folder"]
perspectify_correspondence_folder = config["perspectify_correspondence_folder"]
immo_correspondence_folder = config["immo_correspondence_folder"]
private_correspondence_folder = config["private_correspondence_folder"]
unknown_folder = config["unknown_folder"]
companies_legal_forms = config["companies_legal_forms"]
excluded_companies = config["exclude_companies"]

def parse_date(date_str):
    try:
        return dateparser.parse(date_str)
    except Exception as e:
        logging.warning(f"Unable to parse date: {date_str} - {e}")
        return None

def rename_and_move_file(pdf_path, invoice, reference, date, invoice_number, supplier, recipient):
    original_filename = os.path.basename(pdf_path)
    archive_folder = None
    parsed_date = parse_date(date)
    year = parsed_date.strftime('%Y')

    formatted_date = parsed_date.strftime('%y%m%d')
    logging.debug(f"Date file name: {formatted_date}")

    if invoice:
        if reference:
            # new_filename = f"{formatted_date}_{reference}_{invoice_number}_{supplier}.pdf"
            new_filename = f"{formatted_date}_{invoice_number}_{supplier}.pdf"
        else:
            new_filename = f"{formatted_date}_{invoice_number}_{supplier}.pdf"

        if recipient == "Medmind":
            archive_folder = medmind_invoice_folder
        elif recipient == "Perspectify":
            archive_folder = perspectify_invoice_folder
        elif recipient == "Immo":
            archive_folder = immo_invoice_folder
        elif recipient == "Private":
            archive_folder = private_invoice_folder
        else:
            archive_folder = unknown_folder

    else:
        if reference:
            # new_filename = f"{formatted_date}_{reference}_{supplier}.pdf"
            new_filename = f"{formatted_date}_{supplier}.pdf"
        else:
            new_filename = f"{formatted_date}_{supplier}.pdf"

        if recipient == "Medmind":
            archive_folder = medmind_correspondence_folder
        elif recipient == "Perspectify":
            archive_folder = perspectify_correspondence_folder
        elif recipient == "Immo":
            archive_folder = immo_correspondence_folder
        elif recipient == "Private":
            archive_folder = private_correspondence_folder
        else:
            archive_folder = unknown_folder

        # Add year as subfolder to correspondence path
        correspondence_folder_with_year = os.path.join(archive_folder, str(year))
        os.makedirs(correspondence_folder_with_year, exist_ok=True)
        archive_folder = correspondence_folder_with_year

    if not date or date == "Unknown" or not supplier or supplier == "Unknown" or not invoice_number or invoice_number == "Unknown":
        archive_folder = unknown_folder

    logging.debug(f"Empfänger: {recipient}")
    logging.debug(f"Lieferant: {supplier}")
    logging.debug(f"Rechnungsnummer: {invoice_number}")
    logging.debug(f"Datum: {date}")
    logging.debug(f"Rechnung / Schriftverkehr: {invoice}")
    logging.debug(f"Referenz: {reference}")
    # shutil.copy(pdf_path, os.path.join(archive_folder, new_filename))
    logging.info(f"Moved file to archive: {archive_folder}/{new_filename}")
    shutil.move(pdf_path, os.path.join(archive_folder, new_filename))

def scan_source_folder():
    # Überwachung des Scan-Ordners (vereinfacht)
    for filename in os.listdir(scan_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(scan_folder, filename)

            # Extract text from PDF
            text = util.extract_text.extract_text_from_pdf(pdf_path)
            invoice, reference, date, invoice_number, supplier, recipient = util.extract_text.extract_invoice_info(text)

            # Rename and move file
            rename_and_move_file(pdf_path, invoice, reference, date, invoice_number, supplier, recipient)