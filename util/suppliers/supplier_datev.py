import re
from util.suppliers.DefaultExtractor import DefaultExtractor
from dateutil import parser
import pytz

import cv2
from util.str_util import Utils

class SupplierDatev(DefaultExtractor):
    def __init__(self, config, tessoract_config):
        super().__init__(config, tessoract_config)
        self.pdf_text_extractor.set_tesseract_config(r'--oem 3 --psm 3 -l deu')

    def parse_pdf(self, config, pdf_path):
        # Extract data from text
        self.pdf_path = pdf_path
        self.config = config
        self.text = self.pdf_text_extractor.extract_text_from_pdf(pdf_path)
        invoice, reference, date, invoice_number, recipient = super().extract_invoice_info()
        return invoice, reference, date, invoice_number, recipient

    def extract_date(self):
        # Kombinierte Suche für beide Datumsformate
        date_patterns = [
        # Format "Rechnungsdatum: 31.03.2025"
        r'Rechnungsdatum:\s*(\d{2}\.\d{2}\.\d{4})',
        # Format "23.03.25" mit automatischer Jahrhundertergänzung
        r'\b(\d{2}\.\d{2}\.(\d{2}|\d{4}))\b'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, self.text)
            if match:
                date_str = match.group(1)
                try:
                    # Handle Kurzformat JJ zu JJJJ
                    if len(date_str.split('.')[-1]) == 2:
                        date_str = date_str[:-2] + '20' + date_str[-2:]
                        utc_time_str = parser.parse(date_str, dayfirst=True).date().isoformat()

                        # Parsen der UTC-Zeit
                        utc_time = parser.parse(utc_time_str)

                        # Umwandlung in deutsche Zeitzone (automatische Sommerzeit-Erkennung)
                        local_tz = pytz.timezone('Europe/Berlin')
                        local_time = utc_time.astimezone(local_tz)
                        return local_time.strftime('%d.%m.%Y')
                except:
                    continue
        return None

    def extract_invoice_number(self):
        # Direkte Extraktion des alphanumerischen Codes
        match = re.search(
            r'Rechnungsnummer:\s*([A-Z0-9]{10,15})',
            self.text,
            re.IGNORECASE
        )
        return match.group(2) if match else None

    def preprocess_image(self, image):
        # Optimierte Vorverarbeitung für Noodlesoft-Scans
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape)==3 else image

        # Skalierung mit Schärfung
        scaled = cv2.resize(gray, None, fx=1.5, fy=1.5,
                          interpolation=cv2.INTER_LINEAR_EXACT)

        # Adaptives Thresholding mit optimierten Parametern
        thresh = cv2.adaptiveThreshold(
            scaled, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 21, 10
        )

        # Selektives Denoising nur für kleine Artefakte
        return cv2.fastNlMeansDenoising(
            thresh,
            h=15,
            templateWindowSize=5,
            searchWindowSize=15
        )