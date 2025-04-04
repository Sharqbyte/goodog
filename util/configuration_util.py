import json

class ConfigUtil:
    """
    A utility class for managing configuration settings.
    """

    _config = None

    @classmethod
    def load_config(cls, file_path: str):
        """
        Load configuration from a JSON file if it hasn't been loaded already.
        """
        if cls._config is None:
            try:
                with open(file_path, 'r') as file:
                    cls._config = json.load(file)
            except Exception as e:
                print(f"Error loading configuration: {e}")

    @classmethod
    def get_config(cls):
        """
        Get the loaded configuration.
        """
        if cls._config is None:
            raise ValueError("Configuration not loaded. Call load_config() first.")
        return cls._config

    @classmethod
    def get_posteingang_folder(cls):
        return cls.get_config().get("application_path", {}).get("posteingang_folder", "")

    @classmethod
    def get_medmind_invoice_folder(cls):
        return cls.get_config().get("application_path", {}).get("medmind_invoice_folder", "")

    @classmethod
    def get_perspectify_invoice_folder(cls):
        return cls.get_config().get("application_path", {}).get("perspectify_invoice_folder", "")

    @classmethod
    def get_immo_invoice_folder(cls):
        return cls.get_config().get("application_path", {}).get("immo_invoice_folder", "")

    @classmethod
    def get_private_invoice_folder(cls):
        return cls.get_config().get("application_path", {}).get("private_invoice_folder", "")

    @classmethod
    def get_medmind_correspondence_folder(cls):
        return cls.get_config().get("application_path", {}).get("medmind_correspondence_folder", "")

    @classmethod
    def get_perspectify_correspondence_folder(cls):
        return cls.get_config().get("application_path", {}).get("perspectify_correspondence_folder", "")

    @classmethod
    def get_immo_correspondence_folder(cls):
        return cls.get_config().get("application_path", {}).get("immo_correspondence_folder", "")

    @classmethod
    def get_private_correspondence_folder(cls):
        return cls.get_config().get("application_path", {}).get("private_correspondence_folder", "")

    @classmethod
    def get_unknown_folder(cls):
        return cls.get_config().get("application_path", {}).get("unknown_folder", "")

    @classmethod
    def get_log_folder(cls):
        return cls.get_config().get("application_path", {}).get("log_folder", "")

    @classmethod
    def get_medmind_invoice_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("medmind_invoice_rename_folder", "")

    @classmethod
    def get_perspectify_invoice_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("perspectify_invoice_rename_folder", "")

    @classmethod
    def get_immo_invoice_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("immo_invoice_rename_folder", "")

    @classmethod
    def get_private_invoice_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("private_invoice_rename_folder", "")

    @classmethod
    def get_medmind_correspondence_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("medmind_correspondence_rename_folder", "")

    @classmethod
    def get_perspectify_correspondence_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("perspectify_correspondence_rename_folder", "")

    @classmethod
    def get_immo_correspondence_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("immo_correspondence_rename_folder", "")

    @classmethod
    def get_private_correspondence_rename_folder(cls):
        return cls.get_config().get("application_path", {}).get("private_correspondence_rename_folder", "")

    @classmethod
    def get_supplier_keywords (cls):
        """
        Load supplier keywords from the configuration.
        """
        return cls.get_config().get("supplier_keywords", {})

    @classmethod
    def get_supplier_keyword(cls, keyword: str):
        """
        Get supplier keyword from the configuration.
        """
        supplier_keywords = cls.get_supplier_keywords()
        for supplier, keywords in supplier_keywords.items():
            if keyword in keywords:
                return supplier
        return None

    @classmethod
    def get_supplier_name(cls, supplier_keyword: str):
        supplier_keywords = cls.get_config().get("supplier_keywords", {})
        for keywords in supplier_keywords.values():
            if supplier_keyword in keywords:
                return keywords[1]
        return None

    @classmethod
    def get_supplier_module_name(cls, keyword: str):
        supplier_keywords = cls.get_config().get("supplier_keywords", {})
        for supplier, keywords in supplier_keywords.items():
            if keyword in keywords and len(keywords) > 1:
                return "util.suppliers.supplier_" + keywords[1].lower()
        return None

    @classmethod
    def get_supplier_class_name(cls, keyword: str):
        supplier_keywords = cls.get_config().get("supplier_keywords", {})
        for supplier, keywords in supplier_keywords.items():
            if keyword in keywords and len(keywords) > 1:
                return keywords[1]
        return None

    @classmethod
    def get_supplier_tessoract_config(cls, keyword: str):
        supplier_keywords = cls.get_config().get("supplier_keywords", {})
        for supplier, keywords in supplier_keywords.items():
            if keyword in keywords and len(keywords) > 1:
                return keywords[2]
        return None

    @classmethod
    def get_supplier_classname(cls, supplier_key: str):
        """
        Get the supplier class name from the supplier keywords.
        """
        supplier_keywords = cls.get_config().get("supplier_keywords", {})
        if supplier_key in supplier_keywords and len(supplier_keywords[supplier_key]) > 1:
            return supplier_keywords[supplier_key][1]
        return None

    @classmethod
    def get_companies_legal_forms(cls):
        """
        Get companies legal forms from the configuration.
        """
        return cls.get_config().get("companies_legal_forms", [])

    @classmethod
    def get_exclude_companies(cls):
        """
        Load exclude companies from the configuration.
        """
        return cls.get_config().get("exclude_companies", [])

    @classmethod
    def get_application_paths(cls):
        """
        Get application paths from the configuration.
        """
        paths = []
        for key, value in cls.get_config().items():
            if "folder" in key:
                paths.append(value)
        return paths

    @classmethod
    def get_text_extraction_method(cls):
        """
        Get text extraction method from the configuration.
        """
        return cls.get_config().get("text_extraction_method", "")

    @classmethod
    def get_tesseract_config(cls):
        """
        Get Tesseract configuration from the configuration.
        """
        return cls.get_config().get("tesseract_config", "")