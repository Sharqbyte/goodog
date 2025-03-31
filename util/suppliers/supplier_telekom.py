import re
from util.suppliers.DefaultExtractor import DefaultExtractor
from dateutil import parser

import cv2
from util.str_util import Utils

class SupplierTelekom(DefaultExtractor):
    def __init__(self, config, tessoract_config):
        super().__init__(config, tessoract_config)
        self.pdf_text_extractor.set_tesseract_config(r'--oem 3 --psm 3 -l deu')

    def parse_pdf(self, config, pdf_path):
        # Extract data from text
        self.pdf_path = pdf_path
        self.config = config
        self.text = self.pdf_text_extractor.extract_text_from_pdf(pdf_path)
        invoice, reference, date, invoice_number, supplier, recipient = super().extract_invoice_info()
        return invoice, reference, date, invoice_number, supplier, recipient

    def extract_date(self):
        # Split the text into lines
        lines = self.text.split('\n')

        # Iterate over each line to find lines containing "Datum "
        for line in lines:
            if "Datum " in line:
                for date_pattern in Utils.date_patterns:
                    match = re.search(date_pattern, line)
                    if match:
                        date_str = match.group(0)
                        try:
                            # Handle dates like "06.04 2022"
                            date_str = date_str.replace(' ', '.')
                            # Parse the date using dateutil.parser to handle various formats
                            date = parser.parse(date_str, dayfirst=True)
                            return str(date.date())
                        except ValueError:
                            continue

        # Return None if no valid date is found
        return None

    def extract_invoice_number(self):
        # Regex mit OCR-Toleranz für Label und Bindestrich-Formatierung
        pattern = r"""
            Re[c-n]{3}u?ngsnummer  # OCR-Fehler wie "Rechmungsnummer" abdecken
            [:\s\-]*                # Toleriert :, Leerzeichen, Bindestriche
            (\d{2}\s?-?\s?\d{4}\s?-?\s?\d{4}\s?-?\s?\d{4})  # Flexibles Trennzeichen
            (?=\s|$)               # Stopp bei Leerzeichen/Zeilenende
        """

        match = re.search(pattern, self.text, re.X | re.IGNORECASE)
        if match:
            raw_number = match.group(1)
            # OCR-Fehler bereinigen und vereinheitlichen
            cleaned = re.sub(r'[\sO]', lambda m: '-' if m.group() == ' ' else '0', raw_number)
            cleaned = re.sub(r'[^\d-]', '', cleaned)  # Nur Zahlen und Bindestriche behalten

            # Formatierung erzwingen (2-4-4-4)
            parts = re.split(r'-+', cleaned)
            if len(parts) == 4 and all(len(p) in (2,4) for p in parts):
                return '-'.join(parts)

            # Fallback für falsche Segmentierung
            digits = re.sub(r'\D', '', cleaned)
            if len(digits) == 14:
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}-{digits[10:14]}"

            # Fallback-Suche ohne Label-Kontext
            fallback = re.search(r"\b\d{2}(-\d{4}){3}\b", self.text)
            return fallback
        return None

    def preprocess_image(self, image):
        # Konvertierung zu Graustufen
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Skalierung mit optimierten Parametern
        #gray = cv2.resize(gray, None, fx=2, fy=2,
        #                  interpolation=cv2.INTER_LINEAR)  # Statt CUBIC
        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(resized, (5, 5), 0)
        equalized = cv2.equalizeHist(blurred)
        # gray = cv2.GaussianBlur(gray, (5, 5), 0)
        # gray = cv2.equalizeHist(gray)
        # _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # denoised = cv2.fastNlMeansDenoising(thresh, None, 30, 7, 21)

        thresh = cv2.adaptiveThreshold(equalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        denoised = cv2.fastNlMeansDenoising(thresh, None, 20, 7, 21)  # Parameter anpassen

        return denoised