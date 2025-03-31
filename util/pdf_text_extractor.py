# util/pdf_text_extractor.py
import numpy as np
import pytesseract
from pdf2image import convert_from_path
import cv2
import os

class PDFTextExtractor:
    def __init__(self, tesseract_config):
        self.set_tesseract_config(tesseract_config)
        # Set the TESSDATA_PREFIX environment variable
        os.environ['TESSDATA_PREFIX'] = '/usr/local/share/tessdata/'

    def set_tesseract_config(self, config):
        self.tesseract_config = config

    def preprocess_image(self, image):
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        # Resize the image to improve OCR accuracy
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        # Increase contrast
        gray = cv2.equalizeHist(gray)
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # Remove noise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 30, 7, 21)
        return denoised

    def extract_text_from_image(self, image):
        # Convert PIL image to OpenCV format
        open_cv_image = np.array(image)

        # Preprocess the image
        preprocessed_image = self.preprocess_image(open_cv_image)
        # return pytesseract.image_to_string(preprocessed_image, config=self.tesseract_config)
        return pytesseract.image_to_string(preprocessed_image, config=self.tesseract_config)

    def extract_text_from_pdf(self, pdf_path):
        images = convert_from_path(pdf_path)
        text = ""

        for image in images:
            # Convert PIL image to OpenCV format
            # open_cv_image = np.array(image)
            # Extract text from image
            text += self.extract_text_from_image(image)
        return text