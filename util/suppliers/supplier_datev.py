import re
from .base_supplier import BaseSupplier

class SupplierMicrosoft(BaseSupplier):
    def extract_invoice_number(self, text):
        match = re.search(r"Invoice No\s*[:\s]*([\w\/-]+)", text, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_date(self, text):
        match = re.search(r"Date\s*[:\s]*([\d\/-]+)", text, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_reference(self, text):
        match = re.search(r"Reference\s*[:\s]*([\w\/-]+)", text, re.IGNORECASE)
        return match.group(1) if match else None

    def extract_recipient(self, text):
        if "Medmind" in text:
            return "Medmind"
        return "Unknown"

    def extract_supplier(self, text):
        return "SupplierA"

    def parse_pdf(self, pdf_path):
        # Implement PDF parsing logic specific to SupplierA
        pass