import os
import dateparser
import re
import logging
from dateutil import parser
from datetime import datetime
from fuzzywuzzy import fuzz

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
    def parse_date_old(date_str):
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

    @staticmethod
    def parse_date(raw_date):
        # Month DE/EN
        month_to_number = {
            "Januar": "01", "January": "01",
            "Februar": "02", "February": "02",
            "März": "03", "March": "03",
            "April": "04", "April": "04",
            "Mai": "05", "May": "05",
            "Juni": "06", "June": "06",
            "Juli": "07", "July": "07",
            "August": "08", "August": "08",
            "September": "09", "September": "09",
            "Oktober": "10", "October": "10",
            "November": "11", "November": "11",
            "Dezember": "12", "December": "12"
        }

        # Date formats
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
                return datetime.strptime(raw_date, date_format)
            except ValueError:
                continue

        for month, number in month_to_number.items():
            # Find the closest month match
            if fuzz.partial_ratio(month, raw_date) > 80:
                raw_date = re.sub(r'\b' + re.escape(month) + r'\b', number, raw_date)
                break

        date_str = re.sub(r'(\d)\.?\s+', r'\1.', raw_date)
        date_str = re.sub(r'\s+', '.', date_str)
        date_str = re.sub(r'\.{2,}', '.', date_str)

        try:
            parsed_date = parser.parse(date_str, dayfirst=True)
            return parsed_date.strftime("%d.%m.%Y")
        except:
            logging.warning(f"Error parsing date: {date_str}")

        return None