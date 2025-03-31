class BaseSupplier:
    def __init__(self, config):
        self.config = config
    def is_invoice(self):
        raise NotImplementedError

    def extract_invoice_number(self):
        raise NotImplementedError

    def extract_date(self):
        raise NotImplementedError

    def extract_reference(self):
        raise NotImplementedError

    def extract_recipient(self):
        raise NotImplementedError

    def extract_supplier(self):
        raise NotImplementedError

    def extract_data(self):
        raise NotImplementedError

    def parse_pdf(self, config, pdf_path):
        raise NotImplementedError