from abc import ABC, abstractmethod

class AbstractExtractor(ABC):
    @abstractmethod
    def parse_pdf(self, pdf_path, config):
        pass

    @abstractmethod
    def is_invoice(self):
        pass

    @abstractmethod
    def extract_recipient(self):
        pass

    @abstractmethod
    def extract_reference(self):
        pass

    @abstractmethod
    def extract_invoice_number(self):
        pass

    @abstractmethod
    def extract_date(self):
        pass

    @abstractmethod
    def extract_supplier(self):
        pass