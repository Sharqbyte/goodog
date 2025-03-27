```python
import PyPDF2
import cv2
import json
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import re
from dateutil import parser
import logging

class DefaultExtractor:
    date_format_regexp = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\.\s*[A-Za-z]+\s*\d{4}|\d{1,2}\s*[A-Za-z]+\s*\d{4}|\d{4}-\d{1,2}-\d{1,2}|[A-Za-z]+\s*\d{1,2},\s*\d{4}|\d{2}-[A-Z]{3}-\d{4}|[A-Za-z]{3}\s[A-Za-z]{3}\s\d{1,2}\s\d{2}:\d{2}:\d{2}\sUTC\s\d{4})\b'

    def __init__(self, config_path="config.json"):
        self.config = self.load_supplier_config(config_path)

    def load_supplier_config(self, config_path):
        with open(config_path, "r") as f:
            return json.load(f)

    def extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e:
            logging.error(f"Error extracting text from {pdf_path}: {e}")

        # Extract data from text
        invoice, reference, date, invoice_number, supplier, recipient = self.extract_invoice_info(text)
        return invoice, reference, date, invoice_number, supplier, recipient

    def extract_invoice_info(self, text):
        invoice = False
        reference = None
        date = None
        invoice_number = None
        supplier = None
        recipient = None

        # Identify invoice or correspondence
        invoice = self.identify_invoice_or_correspondence(text)

        # Extract recipient
        recipient = self.extract_recipient(text)

        # Extract reference
        reference = self.extract_reference(text)

        # Extract invoice number
        invoice_number = self.extract_invoice_number(text)

        # Extract date
        date = self.extract_date(text)

        # Extract supplier
        supplier = self.extract_supplier(text)

        return invoice, reference, date, invoice_number, supplier, recipient

    def identify_invoice_or_correspondence(self, text):
        if re.search(r"Rechnung|Invoice|Billing", text, re.IGNORECASE):
            return True
        else:
            return False

    def extract_recipient(self, text):
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

    def extract_reference(self, text):
        return self.extract_reference_from_header(text)

    def extract_reference_from_header(self, header_text):
        reference_match = re.search(r'\b\d{6}\b', header_text)
        if reference_match:
            return reference_match.group(0)
        return None

    def extract_invoice_number(self, text):
        invoice_number_match = re.search(r"(Rechnungsnummer|Belegnummer|Invoice No|Order Number|Transaktionsnummer)\s*[:\s]*([\w\/-]+)", text, re.IGNORECASE)
        if invoice_number_match:
            invoice_number = invoice_number_match.group(2)
            invoice_number = re.sub(r'[^\w-]', '-', invoice_number)
            return invoice_number
        return None

    def extract_date(self, text):
        date_patterns = [
            re.compile(r'\s*Rechnungsdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Leistungsdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Belegdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Beleg-/Leistungsdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Datum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Bezahlt am\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*(Invoice date|Billing date)\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Date\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Time\s*:?\s*' + self.date_format_regexp, re.IGNORECASE)
        ]

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

    def extract_supplier(self, text):
        supplier_keywords = self.config.get("supplier_keywords", {})
        for keyword, supplier_name in supplier_keywords.items():
            if re.search(re.escape(keyword), text, re.IGNORECASE):
                return self.replace_umlauts(re.sub(r'[ \-]', '_', supplier_name))

        supplier_pattern = r"\b(?:[\w\s]+(?:{}))\b".format("|".join(companies_legal_forms))
        supplier_match = re.search(supplier_pattern, text, re.IGNORECASE)
        if supplier_match:
            potential_supplier = supplier_match.group(0)
            if potential_supplier not in excluded_companies:
                return self.replace_umlauts(re.sub(r'[ \-]', '_', potential_supplier))
        return None

    def replace_umlauts(self, supplier):
        supplier = supplier.replace("Ü", "Ue")
        supplier = supplier.replace("ü", "ue")
        supplier = supplier.replace("Ö", "Oe")
        supplier = supplier.replace("ö", "oe")
        supplier = supplier.replace("Ä", "Ae")
        supplier = supplier.replace("ä", "ae")
        return supplier