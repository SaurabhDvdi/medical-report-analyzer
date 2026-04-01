import os
import pytesseract
from PIL import Image
import pdf2image
import easyocr
from typing import Optional

class OCRService:
    def __init__(self):
        # Try to use EasyOCR first, fallback to Tesseract
        self.use_easyocr = True
        try:
            self.easyocr_reader = easyocr.Reader(['en'])
        except:
            self.use_easyocr = False
            print("EasyOCR not available, using Tesseract")
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from image or PDF file"""
        try:
            if file_path.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return f"Error extracting text: {str(e)}"
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(file_path)
            text_parts = []
            
            for image in images:
                if self.use_easyocr:
                    results = self.easyocr_reader.readtext(image)
                    text = " ".join([result[1] for result in results])
                else:
                    text = pytesseract.image_to_string(image)
                text_parts.append(text)
            
            return "\n".join(text_parts)
        except Exception as e:
            # Fallback to Tesseract if EasyOCR fails
            try:
                images = pdf2image.convert_from_path(file_path)
                text_parts = []
                for image in images:
                    text = pytesseract.image_to_string(image)
                    text_parts.append(text)
                return "\n".join(text_parts)
            except Exception as e2:
                return f"Error processing PDF: {str(e2)}"
    
    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image file"""
        try:
            image = Image.open(file_path)
            
            if self.use_easyocr:
                results = self.easyocr_reader.readtext(image)
                return " ".join([result[1] for result in results])
            else:
                return pytesseract.image_to_string(image)
        except Exception as e:
            return f"Error processing image: {str(e)}"

