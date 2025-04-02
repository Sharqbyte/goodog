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
from util.configuration_util import ConfigUtil
from fuzzywuzzy import fuzz

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
        self.text = self.pdf_text_extractor.extract_text_by_lang(pdf_path, self.pdf_text_extractor, self.text)
        invoice, reference, date, invoice_number, recipient = self.extract_invoice_info()
        return invoice, reference, date, invoice_number, recipient

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
        # supplier = self.extract_supplier()

        return invoice, reference, date, invoice_number, recipient

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
        date = None
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
                raw_date = date_match.group(1)
                logging.debug(f"Raw date found: {raw_date}")
                date = Utils.parse_date(raw_date)

        return date

    def extract_supplier(self):
        supplier_keywords = self.config.get("supplier_keywords", {})
        # Known suppliers match defined in config.json
        for keyword, supplier_name in supplier_keywords.items():
            if re.search(re.escape(keyword), self.text, re.IGNORECASE):
                if isinstance(supplier_name, list):
                    # supplier_name = supplier_name[0]  # Assuming the first element is the supplier name
                    supplier_name = ConfigUtil.get_supplier_class_name(keyword).lower()
                return Utils.replace_umlauts(re.sub(r'[ \-]', '_', supplier_name))

        # Identified suppliers by legal forms
        supplier_pattern = r"\b(?:[\w\s]+(?:{}))\b".format("|".join(ConfigUtil.get_companies_legal_forms()))
        supplier_match = re.search(supplier_pattern, self.text, re.IGNORECASE)

        if supplier_match:
            potential_supplier = supplier_match.group(0)
            excluded_companies = ConfigUtil.get_exclude_companies()
            if potential_supplier not in excluded_companies:
                return Utils.replace_umlauts(re.sub(r'[ \-]', '_', potential_supplier))

        return None