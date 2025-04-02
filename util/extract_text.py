import numpy as np
import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import re
import logging
import importlib
import cv2
from util.str_util import Utils
from util.configuration_util import ConfigUtil
from util.suppliers.DefaultExtractor import DefaultExtractor
from util.pdf_text_extractor import PDFTextExtractor

class DataExtractorUtil:

    def __init__(self, config, tessoract_config):
        self.config = config
        self.pdf_text_extractor = PDFTextExtractor(tessoract_config)
        self.companies_legal_forms = ConfigUtil.get_companies_legal_forms()
        self.excluded_companies = ConfigUtil.get_exclude_companies()

    def get_supplier_class(self, supplier_name):
        logging.debug(f"Supplier name: {supplier_name}")
        supplier_keywords = ConfigUtil.get_supplier_keywords()
        if supplier_name not in supplier_keywords:
            logging.warning(f"Supplier name '{supplier_name}' not found in supplier_keywords. Using DefaultExtractor.")
            return DefaultExtractor(self.config, ConfigUtil.get_supplier_tessoract_config(supplier_name))

        module_name = ConfigUtil.get_supplier_module_name(supplier_name)
        try:
            module = importlib.import_module(module_name)
            supplier_class = getattr(module, 'Supplier' + ConfigUtil.get_supplier_class_name(supplier_name))
            return supplier_class(self.config, ConfigUtil.get_supplier_tessoract_config(supplier_name))
        except ModuleNotFoundError:
            logging.error(f"No module named '{module_name}'")
            return DefaultExtractor(self.config, ConfigUtil.get_supplier_tessoract_config(supplier_name))

    def extract_text(self, pdf_path):
        # Extract text from PDF
        if self.config.get("text_extraction_method") == "PyPDF2":
            text = self.extract_text_from_pdf_PyPDF2(pdf_path)
        elif self.config.get("text_extraction_method") == "pdf2image":
            text = self.extract_text_from_pdf_pdf2image(pdf_path)
        else:
            text = self.extract_text_from_pdf_AI(pdf_path)

        # Identify supplier
        supplier = self.extract_supplier(pdf_path, text)

        # Get supplier class
        print(f"Supplier:  {supplier}")
        logging.info(f"Scan source folder")
        supplier_class = self.get_supplier_class(supplier)

        # Extract additional data using the supplier class
        invoice, reference, date, invoice_number, recipient = supplier_class.parse_pdf(self.config, pdf_path)

        logging.debug(f"Extracted text: {text}")
        print(f"PRINT : Extracted text: {text}")

        return supplier, invoice, reference, date, invoice_number, recipient

    def extract_text_from_pdf_PyPDF2(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e:
            logging.error(f"Error extracting text from {pdf_path}: {e}")
        return text

    def extract_text_from_pdf_pdf2image(self, pdf_path):
        # USe DefaultExtractor to extract text from PDF
        self.text = self.pdf_text_extractor.extract_text_from_pdf(pdf_path)
        return self.text

    # TBD defined
    def extract_text_from_pdf_AI(self, pdf_path):
        text = ""

        return text

    # Extract supplier from text using keywords and legal forms
    def extract_supplier(self, pdf_path, text):
        # First, search for the keys in supplier_keywords
        supplier_keywords = ConfigUtil.get_supplier_keywords()
        for supplier, keywords in supplier_keywords.items():
            for keyword in keywords:
                if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
                    return supplier

        self.pdf_text_extractor.extract_text_by_lang(pdf_path, self.pdf_text_extractor, text)

        # If no match is found, fall back to the original method
        supplier_pattern = r"\b(?:[\w\s]+(?:{}))\b".format("|".join(self.companies_legal_forms))
        supplier_match = re.search(supplier_pattern, text, re.IGNORECASE)
        if supplier_match:
            potential_supplier = supplier_match.group(0)
            if potential_supplier not in self.excluded_companies:
                return Utils.replace_umlauts(re.sub(r'[ \-]', '_', potential_supplier))
        return None