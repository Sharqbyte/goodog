import re
from .base_supplier import BaseSupplier
import numpy as np

import logging
import cv2
import pytesseract
from pdf2image import convert_from_path
from util.str_util import Utils

class SupplierFinanzamtEbersberg(BaseSupplier):
    def extract_invoice_number(self, pdf_path, text):
        info_text = None
        tax_number_text = None
        filename_part = None

        tax_number = re.search(r"Steuernummer\s*[:\s]*([\d\/]+)", text, re.IGNORECASE)

        if tax_number.group(1):
            tax_number_text = Utils.replace_special_characters(tax_number.group(1))
            subject = re.search(r"Bescheid für\s*(\d{4})", text, re.IGNORECASE)
            if subject in subject.group(0):
                subject_text = Utils.replace_umlauts(subject.group(0))
                subject_text = Utils.replace_spaces(subject_text)
                filename_part = subject_text + "_" + tax_number_text
        else:
            filename_part = tax_number.group(1)

        return filename_part if filename_part else None

    def extract_date_old(self, pdf_path, text):
        # Split the text into lines and take the first 20 lines
        lines = text.split('\n')[:20]
        # Join the first 20 lines back into a single string
        first_20_lines = '\n'.join(lines)

        # Use regex to find the date in the format "DD.MM.YYYY"
        match = re.search(r'\b\d{2}\.\d{2}\.\d{4}\b', first_20_lines)
        if match:
            return match.group(0)
        return None

    def extract_date(self, pdf_path, text):
        date = Utils.find_latest_date(text)

        return str(date) if date else None

    def extract_date_from_pdf(pdf_path):
        # Convert PDF to image
        images = convert_from_path(pdf_path)
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

    def extract_reference(self, pdf_path, text):
        reference_match = re.search(r"\d{6}", text)
        return reference_match.group(1) if reference_match else None

    def extract_recipient(self, pdf_path, text):
        recipient = re.search(r"Finanzamt Ebersberg\s*[:\s]*([\w\/-]+)", text, re.IGNORECASE)
        if recipient.group(0) in text:
            return "Finanzamt_Ebersberg"
        return "Unknown"

    def extract_supplier(self, pdf_path, text):
        return "SupplierFinanzamtEbersberg"

    def parse_data(self, pdf_path):
        reference = None
        date = None
        invoice_number = None
        supplier = None
        recipient = None

        # Extract data from text
        text = self.extract_text_from_pdf(pdf_path)
        if text:
            # Extract data from text
            reference = self.extract_reference(pdf_path, text)
            date = self.extract_date(pdf_path, text)
            invoice_number = self.extract_invoice_number(pdf_path, text)
            supplier = self.extract_supplier(pdf_path, text)
            recipient = self.extract_recipient(pdf_path, text)
        return reference, date, invoice_number, supplier, recipient

    def parse_pdf(self, config, pdf_path):
        # Extract data from text
        data_extract = self.extract_data(pdf_path)
        self.config = config
        logging.debug(f"Start data extraction for Finanzamt Ebersberg document")
        print(f"Start data extraction for Finanzamt Ebersberg document")
        return data_extract