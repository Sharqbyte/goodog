import re
from util.suppliers.DefaultExtractor import DefaultExtractor
from dateutil import parser
import logging
from fuzzywuzzy import fuzz
from pdf2image import convert_from_path
import numpy as np
import pytesseract

import cv2
from util.str_util import Utils

class SupplierSlack(DefaultExtractor):
    def __init__(self, config, tesseract_config: None):
        logger = logging.getLogger(__name__)
        super().__init__(config, tesseract_config)
        self.pdf_text_extractor.set_tesseract_config(r'--oem 3 --psm 3 -l deu')

    def parse_pdf(self, config, pdf_path):
        # Extract data from text
        self.pdf_path = pdf_path
        self.config = config

        self.text = self.pdf_text_extractor.extract_text_from_pdf(pdf_path)
        invoice, reference, date, invoice_number, supplier, recipient = super().extract_invoice_info()
        return invoice, reference, date, invoice_number, supplier, recipient

    def extract_date(self):
        date_pattern = r"""
            (?:Bezahlt\s+am|Datum|Datum:)  # Keywords (case-insensitive)
            \s*[:\s]* # Optional separators
            (                             # Capturing group for date formats
                \d{1,2}                     # 1 or 2 digits (day)
                (?:                         # Non-capturing group for OR options
                    \.?\s?\w+\s?\.?\d{4}    # 15. Februar 2025 OR 15 Februar 2025
                    |                       # OR
                    [./-]\d{1,2}[./-]\d{2,4}   # 15.02.2025 OR 15-02-25
                    |                       # OR
                    \s?\w+\s?\d{2,4}         # 15 Februar 25
                )
            )
        """
        pattern = re.compile(date_pattern, re.IGNORECASE | re.VERBOSE)
        month_to_number = {
            "Januar": "01", "January": "01",
            "Februar": "02", "February": "02",
            "März": "03", "March": "03",
            "April": "04", "April": "04",
            "Mai": "05", "May": "05",
            "Juni": "06", "June": "06",
            "Juli": "07", "July": "07",
            "August": "08", "August": "08",
            "September": "09", "September": "09",
            "Oktober": "10", "October": "10",
            "November": "11", "November": "11",
            "Dezember": "12", "December": "12"
        }

        date_match = pattern.search(self.text)
        if date_match:
            raw_date = date_match.group(1)
            logging.debug(f"Raw date found: {raw_date}")

            # Find the closest month match
            for month, number in month_to_number.items():
                if fuzz.partial_ratio(month, raw_date) > 80:
                    raw_date = re.sub(r'\b' + re.escape(month) + r'\b', number, raw_date)
                    break

            # Clean up the date string
            date_str = re.sub(r'(\d)\.?\s+', r'\1.', raw_date)  # Replace spaces after digits with periods
            date_str = re.sub(r'\s+', '.', date_str)  # Replace remaining spaces with periods
            date_str = re.sub(r'\.{2,}', '.', date_str)  # Remove double periods

            try:
                parsed_date = parser.parse(date_str, dayfirst=True)
                return parsed_date.strftime("%d.%m.%Y")
            except:
                logging.warning(f"Error parsing date: {date_str}")
        return None

    def extract_invoice_number(self):
        invoice_number_pattern = r"(Rechnungsnummer|Rechnungenummer)\s*[:\-\s]*\s*([A-Z0-9]+[\-]?\d+)"
        pattern = re.compile(invoice_number_pattern, re.IGNORECASE)
        for line in self.text.split('\n'):
            if fuzz.partial_ratio("Rechnungsnummer", line) > 80:
                invoice_number_match = pattern.search(line)
                if invoice_number_match:
                    invoice_number = invoice_number_match.group(2)
                    return invoice_number
        return None