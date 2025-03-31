import re
from util.suppliers.DefaultExtractor import DefaultExtractor
from util.pdf_text_extractor import PDFTextExtractor
import numpy as np
from datetime import datetime

import logging
import cv2
import pytesseract
from pdf2image import convert_from_path
from util.str_util import Utils

class SupplierFinanzkasse(DefaultExtractor):
    def __init__(self, config, tessoract_config):
        super().__init__(config, tessoract_config)
        self.pdf_text_extractor.set_tesseract_config(tessoract_config)

    def parse_pdf(self, config, pdf_path):
        self.config = config
        self.pdf_path = pdf_path
        self.text = self.pdf_text_extractor.extract_text_from_pdf(pdf_path)
        # Extract data from text
        data_extract = self.extract_data()
        self.config = config
        logging.debug(f"Start data extraction for Finanzamt Ebersberg document")
        print(f"Start data extraction for Finanzamt Ebersberg document")
        return data_extract

    def is_invoice(self):
        if re.search(r"Rechnung|Invoice|Billing", self.text, re.IGNORECASE):
            return True
        else:
            return False

    def extract_invoice_number(self):
        info_text = None
        tax_number_text = None
        filename_part = None

        tax_number = re.search(r"Steuernummer\s*[:\s]*([\d\/]+)", self.text, re.IGNORECASE)
        subject = re.search(r"Bescheid [Ff]ür\s*(\d{4})", self.text, re.IGNORECASE)

        if tax_number and tax_number.group(1):
            tax_number_text = Utils.replace_special_characters(tax_number.group(1))

        if subject and subject.group(0) in self.text:
            subject_text = Utils.replace_umlauts(subject.group(0))
            subject_text = Utils.replace_spaces(subject_text)
            if tax_number_text:
                filename_part = subject_text + "_" + tax_number_text
            else:
                filename_part = subject_text

        return filename_part if filename_part else None

    def extract_date_old(self):
        # Split the text into lines and take the first 20 lines
        lines = self.text.split('\n')[:20]
        # Join the first 20 lines back into a single string
        first_20_lines = '\n'.join(lines)

        # Use regex to find the date in the format "DD.MM.YYYY"
        match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', first_20_lines)
        if match:
            return match.group(0)
        return None

    def extract_date(self):
        date = Utils.find_latest_date(self.text)

        return str(date) if date else None

    def find_first_date(self):
        # Define a regex pattern to match dates in the format "DD.MM.YYYY"
        date_pattern = r'\b\d{2}\.\d{2}\.\d{4}\b'

        # Split the text into lines
        lines = self.text.split('\n')

        # Iterate over each line to find the first date
        for line in lines:
            match = re.search(date_pattern, line)
            if match:
                date_str = match.group(0)
                try:
                    # Validate and parse the date to ensure it's in the correct format
                    date = datetime.strptime(date_str, '%d.%m.%Y')
                    return str(date)
                except ValueError:
                    continue

        # Return None if no valid date is found
        return None

    def extract_date_from_pdf(self):
        # Convert PDF to image
        images = convert_from_path(self.pdf_path)
        if not images:
            return None

        # Convert the first page to OpenCV format
        image = cv2.cvtColor(np.array(images[0]), cv2.COLOR_RGB2BGR)

        # Define the region of interest (ROI) for the top right corner
        height, width, _ = image.shape
        roi = image[0:int(height * 0.1), int(width * 0.7):width]

        # Convert ROI to grayscale
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Use pytesseract to extract text
        text = pytesseract.image_to_string(gray, config='--psm 6')

        # Use regex to find the date in the format "DD.MM.YYYY"
        match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', text)
        if match:
            return match.group(0)
        return None

    def extract_reference(self):
        reference_match = re.search(r"\d{6}", self.text)
        if reference_match:
            return reference_match.group(0)
        return None

    def extract_recipient(self):
        if re.search(r"Medmind", self.text, re.IGNORECASE):
            return "Medmind"
        elif re.search(r"Distinctify", self.text, re.IGNORECASE):
            return "Medmind"
        elif re.search(r"Perspectify", self.text, re.IGNORECASE):
            return "Perspectify"
        elif re.search(r"ME Verwaltung|Eberl Bau", self.text, re.IGNORECASE):
            return "Immo"
        elif re.search(r"Martin Eberl|Martina Eberl", self.text, re.IGNORECASE):
            return "Private"
        else:
            return "Unknown"

    def extract_supplier(self):
        return "Finanzamt_Ebersberg"

    def extract_data(self):
        invoice = False
        reference = None
        date = None
        invoice_number = None
        supplier = None
        recipient = None

        if self.text:
            # Extract data from text
            invoice = self.is_invoice()
            reference = self.extract_reference()
            date = self.find_first_date()
            invoice_number = self.extract_invoice_number()
            supplier = self.extract_supplier()
            recipient = self.extract_recipient()

        logging.info(f"Extracted data: reference={reference}, date={date}, invoice_number={invoice_number}, supplier={supplier}, recipient={recipient}")
        return invoice, reference, date, invoice_number, supplier, recipient