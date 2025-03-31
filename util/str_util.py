import os
import dateparser
import re
import logging
from dateutil import parser
from datetime import datetime

class Utils:
    # Define a logger for the Utils class
    logger = logging.getLogger(__name__)

    # Define static date patterns
    date_patterns = [
        r'\b\d{2}[.\s]?\d{2}[.\s]?\d{4}\b',  # DD.MM.YYYY, DD MM.YYYY, DD MM YYYY
        r'\b\d{2}/\d{2}/\d{4}\b',            # DD/MM/YYYY
        r'\b\d{4}-\d{2}-\d{2}\b',            # YYYY-MM-DD
        r'\b\d{1,2} \w+ \d{4}\b',            # D Month YYYY
        r'\b\w+ \d{1,2}, \d{4}\b',           # Month D, YYYY
        r'\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\b'  # YYYY-MM-DD HH:MM:SS
    ]

    def __init__(self):
        pass

    @staticmethod
    def add_timestamp_to_filename(filename):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        return f"{name}_{timestamp}{ext}"

    @staticmethod
    def replace_umlauts(text):
        umlaut_map = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
            'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue'
        }
        for key, value in umlaut_map.items():
            text = text.replace(key, value)
        return text

    @staticmethod
    def replace_special_characters(text):
        # Replace all special characters with "-"
        return re.sub(r'[^\w\s]', '-', text)

    @staticmethod
    def replace_spaces(text):
        # Replace all spaces with "_"
        return text.replace(' ', '_')

    @staticmethod
    def parse_date(date_str):
        date_formats = [
            '%d.%m.%Y',
            '%d. %B %Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d %B %Y',
            '%B %d, %Y',
            '%Y-%m-%d %H:%M:%S'
        ]
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        return None

    @staticmethod
    def find_latest_date(text):

        dates = []

        # Search for all dates in the text
        for pattern in Utils.date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Parse the date and add to the list
                    parsed_date = parser.parse(match, dayfirst=True)
                    dates.append(parsed_date)
                except ValueError:
                    continue

        # Find the latest date
        if dates:
            latest_date = max(dates)
            return latest_date.date()
        return None