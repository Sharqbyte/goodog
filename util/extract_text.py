# This is a sample Python script.
import os
import cv2
import json
import numpy as np

import pytesseract
from pdf2image import convert_from_path
import re
from dateutil import parser
import logging

# Konfigurationsdatei laden
with open("config.json", "r") as f:
    config = json.load(f)

# Configure logging
logfile_path = os.path.join(config["log_folder"], 'file_operations.log')
logging.basicConfig(filename=logfile_path, level=logging.DEBUG, format='%(asctime)s - %(message)s')

companies_legal_forms = config["companies_legal_forms"]
excluded_companies = config["exclude_companies"]

# date_format_regexp = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\.\s*[A-Za-z]+\s*\d{4}|\d{1,2}\s*[A-Za-z]+\s*\d{4}|\d{4}-\d{1,2}-\d{1,2}|[A-Za-z]+\s*\d{1,2},\s*\d{4})\b'
# date_format_regexp = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\.\s*[A-Za-z]+\s*\d{4}|\d{1,2}\s*[A-Za-z]+\s*\d{4}|\d{4}-\d{1,2}-\d{1,2}|[A-Za-z]+\s*\d{1,2},\s*\d{4}|\d{2}-[A-Z]{3}-\d{4})\b'
date_format_regexp = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\.\s*[A-Za-z]+\s*\d{4}|\d{1,2}\s*[A-Za-z]+\s*\d{4}|\d{4}-\d{1,2}-\d{1,2}|[A-Za-z]+\s*\d{1,2},\s*\d{4}|\d{2}-[A-Z]{3}-\d{4}|[A-Za-z]{3}\s[A-Za-z]{3}\s\d{1,2}\s\d{2}:\d{2}:\d{2}\sUTC\s\d{4})\b'

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for image in images:
        # Convert PIL image to OpenCV format
        open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Convert the image to grayscale
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # Extract text using pytesseract
        text += pytesseract.image_to_string(thresh, lang='deu+eng')

    logging.debug(text)
    return text

def extract_text_from_pdf_header(pdf_path):
    # Convert PDF to images
    images = convert_from_path(pdf_path)

    # Assuming the reference is in the first third of the first image
    header_image = images[0].crop((0, 0, images[0].width, images[0].height // 3))  # Crop the first third

    # Extract text from the cropped image
    header_text = pytesseract.image_to_string(header_image, lang='deu')  # or 'eng' for English
    return header_text

def extract_reference_from_header(header_text):
    reference_match = re.search(r'\b\d{6}\b', header_text)
    if reference_match:
        return reference_match.group(0)
    return None

def extract_invoice_info(text):
    invoice = False
    reference = None
    date = None
    invoice_number = None
    supplier = None
    recipient = None

    # Identify invoice or correspondence
    invoice = identify_invoice_or_correspondence(text)

    # Empfänger extrahieren
    recipient = extract_recipient(text)

    # Exxtract reference
    reference = extract_reference(text)

    # Extract invoice number
    invoice_number = extract_invoice_number(text)

    # Extract date
    # date = extract_date_test(text)
    date = extract_date(text)

    # Extract supplier
    supplier = extract_supplier(text)

    return invoice, reference, date, invoice_number, supplier, recipient

#def extract_invoice_number(text):
    # invoice_number_match = re.search(r"Datum\s*:\s*([\w\/-]+)|Date\s*:\s*([\w\/-]+)", text, re.IGNORECASE)
#    invoice_number_match = None

#    if re.search(r"Rechnungsnummer\s*:\s*([\w\/-]+)|Invoice No\s*:\s*([\w\/-]+)|Transaktionsnummer\s*:\s*([\w\/-]+)", text, re.IGNORECASE):
#        invoice_number_match = re.search(r"Rechnungsnummer\s*:\s*([\w\/-]+)|Invoice No\s*:\s*([\w\/-]+)|Transaktionsnummer\s*:\s*([\w\/-]+)", text, re.IGNORECASE)
#    if invoice_number_match:
#        invoice_number = invoice_number_match.group(1)
        # Replace all spaces and special characters with underscores
#        invoice_number = re.sub(r'[^\w]', '-', invoice_number)
#        return invoice_number
#    return None

def extract_invoice_number(text):
    # Updated regex to match the invoice number format without including the pipe character
    invoice_number_match = re.search(r"(Rechnungsnummer|Invoice No|Order Number|Transaktionsnummer)\s*[:\s]*([\w\/-]+)", text, re.IGNORECASE)
    if invoice_number_match:
        invoice_number = invoice_number_match.group(2)
        # Replace all spaces and special characters with underscores
        invoice_number = re.sub(r'[^\w-]', '-', invoice_number)
        return invoice_number
    return None



def extract_date_test(text):
    # Define the pattern to match "Datum:" followed by a date
    date_pattern = re.compile(r'Datum\s*:\s*' + date_format_regexp, re.IGNORECASE)

    # Search for the date pattern in the text
    date_match = date_pattern.search(text)
    if date_match:
        return date_match.group(0)

    # If no date is found, return 'Unknown'
    return 'Unknown'

def extract_date(text):

    date_patterns = [
        re.compile(r'\s*Rechnungsdatum\s*:?\s*' + date_format_regexp, re.IGNORECASE),
        re.compile(r'\s*Datum\s*:?\s*' + date_format_regexp, re.IGNORECASE),
        re.compile(r'\s*Bezahlt am\s*:?\s*' + date_format_regexp, re.IGNORECASE),
        re.compile(r'\s*(Invoice date|Billing date)\s*:?\s*' + date_format_regexp, re.IGNORECASE),
        re.compile(r'\s*Date\s*:?\s*' + date_format_regexp, re.IGNORECASE),
        re.compile(r'\s*Time\s*:?\s*' + date_format_regexp, re.IGNORECASE)
    ]

    # Datum extrahieren
    logging.debug(f"Searching for date in text: \n{text}")
    for pattern in date_patterns:
        date_match = pattern.search(text)
        if date_match:
            date = date_match.group(1)
            logging.debug(f"Date found: {date}")
            break
    else:
        try:
            date = str(parser.parse(text, fuzzy_with_tokens=True)[0].date())
            logging.debug(f"Date parsed: {date}")
        except:
            date = 'Unbekannt'
            logging.warning("Date not found")

    for pattern in date_patterns:
        date_match = pattern.search(text)
        if date_match:
            return date_match.group(1)
    try:
        return str(parser.parse(text, fuzzy_with_tokens=True)[0].date())
    except:
        return 'Unbekannt'

def extract_recipient(text):
    if re.search(r"Medmind", text, re.IGNORECASE):
        return "Medmind"
    elif re.search(r"Distinctify", text, re.IGNORECASE):
        return "Medmind"
    elif re.search(r"Perspectify", text, re.IGNORECASE):
        return "Perspectify"
    elif re.search(r"ME Verwaltung|Eberl Bau", text, re.IGNORECASE):
        return "Immo"
    elif re.search(r"Martin Eberl|Martina Eberl", text, re.IGNORECASE):
        return "Private"
    else:
        return "Unknown"

def extract_supplier(text):
    supplier_keywords = config.get("supplier_keywords", {})
    for keyword, supplier_name in supplier_keywords.items():
        if re.search(re.escape(keyword), text, re.IGNORECASE):
            return replace_umlauts(re.sub(r'[ \-]', '_', supplier_name))

    supplier_pattern = r"\b(?:[\w\s]+(?:{}))\b".format("|".join(companies_legal_forms))
    supplier_match = re.search(supplier_pattern, text, re.IGNORECASE)
    if supplier_match:
        potential_supplier = supplier_match.group(0)
        if potential_supplier not in excluded_companies:
            return replace_umlauts(re.sub(r'[ \-]', '_', potential_supplier))
    return None

def replace_umlauts(supplier):
    supplier = supplier.replace("Ü", "Ue")
    supplier = supplier.replace("ü", "ue")
    supplier = supplier.replace("Ö", "Oe")
    supplier = supplier.replace("ö", "oe")
    supplier = supplier.replace("Ä", "Ae")
    supplier = supplier.replace("ä", "ae")
    return supplier

def extract_reference(text):
    reference = extract_reference_from_header(text)
    return reference

def identify_invoice_or_correspondence(text):
    if re.search(r"Rechnung|Invoice|Billing", text, re.IGNORECASE):
        return True
    else:
        return False