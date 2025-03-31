import logging
import re
from dateutil import parser
from pdf2image import convert_from_path
import cv2
import numpy as np
import pytesseract
from util.str_util import Utils
from util.suppliers.abstract_extractor import AbstractExtractor
from util.pdf_text_extractor import PDFTextExtractor

class DefaultExtractor(AbstractExtractor):

    def __init__(self, config, tesseract_config):
        self.config = config
        self.text = None
        self.date_format_regexp = r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\.\s*[A-Za-z]+\s*\d{4}|\d{1,2}\s*[A-Za-z]+\s*\d{4}|\d{4}-\d{1,2}-\d{1,2}|[A-Za-z]+\s*\d{1,2},\s*\d{4}|\d{2}-[A-Z]{3}-\d{4}|[A-Za-z]{3}\s[A-Za-z]{3}\s\d{1,2}\s\d{2}:\d{2}:\d{2}\sUTC\s\d{4})\b'
        self.pdf_text_extractor = PDFTextExtractor(tesseract_config)

    def set_tesseract_config(self, config):
        self.pdf_text_extractor.set_tesseract_config(config)

    def parse_pdf(self, config, pdf_path):
        # Extract data from text
        self.pdf_path = pdf_path
        self.config = config
        self.text = self.pdf_text_extractor.extract_text_from_pdf(pdf_path)
        invoice, reference, date, invoice_number, supplier, recipient = self.extract_invoice_info()
        return invoice, reference, date, invoice_number, supplier, recipient

    def extract_invoice_info(self):
        invoice = False
        reference = None
        date = None
        invoice_number = None
        supplier = None
        recipient = None

        # Identify invoice or correspondence
        invoice = self.is_invoice()

        # Extract recipient
        recipient = self.extract_recipient()

        # Extract reference
        reference = self.extract_reference()

        # Extract invoice number
        invoice_number = self.extract_invoice_number()

        # Extract date
        date = self.extract_date()

        # Extract supplier
        supplier = self.extract_supplier()

        return invoice, reference, date, invoice_number, supplier, recipient

    def is_invoice(self):
        if re.search(r"Rechnung|Invoice|Billing", self.text, re.IGNORECASE):
            return True
        else:
            return False

    def extract_recipient(self):
        if re.search(r"Medmind", self.text, re.IGNORECASE):
            return "Medmind"
        elif re.search(r"Distinctify", self.text, re.IGNORECASE):
            return "Medmind"
        elif re.search(r"IQAL", self.text, re.IGNORECASE):
            return "Medmind"
        elif re.search(r"Perspectify", self.text, re.IGNORECASE):
            return "Perspectify"
        elif re.search(r"ME Verwaltung|Eberl Bau", self.text, re.IGNORECASE):
            return "Immo"
        elif re.search(r"Martin Eberl|Martina Eberl", self.text, re.IGNORECASE):
            return "Private"
        else:
            return "Unknown"

    def extract_reference(self):
        reference_match = re.search(r'\b\d{6}\b', self.text)
        if reference_match:
            return reference_match.group(0)
        return None

    def extract_invoice_number(self):
        invoice_number_match = re.search(r"(Rechnungsnummer|Belegnummer|Invoice No|Order Number|Transaktionsnummer)\s*[:\s]*([\w\/-]+)", self.text, re.IGNORECASE)
        if invoice_number_match:
            invoice_number = invoice_number_match.group(2)
            invoice_number = re.sub(r'[^\w-]', '-', invoice_number)
            return invoice_number
        return None

    def extract_date(self):
        date_patterns = [
            re.compile(r'\s*Rechnungsdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Leistungsdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Belegdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Beleg-/Leistungsdatum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Datum\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Bezahlt am\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*(Invoice|Invoice number|Invoice date|Billing date)\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Date\s*:?\s*' + self.date_format_regexp, re.IGNORECASE),
            re.compile(r'\s*Time\s*:?\s*' + self.date_format_regexp, re.IGNORECASE)
        ]

        logging.debug(f"Searching for date in text: \n{self.text}")
        for pattern in date_patterns:
            date_match = pattern.search(self.text)
            if date_match:
                date = date_match.group(1)
                logging.debug(f"Date found: {date}")
                break
        else:
            try:
                date = str(parser.parse(self.text, fuzzy_with_tokens=True)[0].date())
                logging.debug(f"Date parsed: {date}")
            except:
                date = 'Unbekannt'
                logging.warning("Date not found")

        for pattern in date_patterns:
            date_match = pattern.search(self.text)
            if date_match:
                return date_match.group(1)
        try:
            return str(parser.parse(self.text, fuzzy_with_tokens=True)[0].date())
        except:
            return 'Unbekannt'

    def extract_supplier(self):
        supplier_keywords = self.config.get("supplier_keywords", {})
        for keyword, supplier_name in supplier_keywords.items():
            if re.search(re.escape(keyword), self.text, re.IGNORECASE):
                if isinstance(supplier_name, list):
                    supplier_name = supplier_name[0]  # Assuming the first element is the supplier name
                return Utils.replace_umlauts(re.sub(r'[ \-]', '_', supplier_name))

        supplier_pattern = r"\b(?:[\w\s]+(?:{}))\b".format("|".join(self.config.get("companies_legal_forms", [])))
        supplier_match = re.search(supplier_pattern, self.text, re.IGNORECASE)
        if supplier_match:
            potential_supplier = supplier_match.group(0)
            excluded_companies = self.config.get("excluded_companies", [])
            if potential_supplier not in excluded_companies:
                return Utils.replace_umlauts(re.sub(r'[ \-]', '_', potential_supplier))
        return None