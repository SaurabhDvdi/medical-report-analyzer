import os
import pytesseract
from PIL import Image
import pdf2image
import easyocr
import numpy as np


class OCRService:
    def __init__(self):
        self.use_easyocr = True
        try:
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except:
            self.use_easyocr = False
            print("EasyOCR not available, using Tesseract")

    # -----------------------------
    # PUBLIC METHOD
    # -----------------------------
    def extract_text(self, file_path: str):
        """
        Returns: List[str] → structured lines
        """
        try:
            if file_path.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return []

    # -----------------------------
    # PDF HANDLING
    # -----------------------------
    def _extract_from_pdf(self, file_path: str):
        try:
            images = pdf2image.convert_from_path(file_path, dpi=300)
            all_lines = []

            for image in images:
                lines = self._process_image(image)
                all_lines.extend(lines)

            return all_lines

        except Exception as e:
            print(f"PDF OCR Error: {str(e)}")
            return []

    # -----------------------------
    # IMAGE HANDLING
    # -----------------------------
    def _extract_from_image(self, file_path: str):
        try:
            image = Image.open(file_path)
            return self._process_image(image)
        except Exception as e:
            print(f"Image OCR Error: {str(e)}")
            return []

    # -----------------------------
    # CORE PROCESSOR
    # -----------------------------
    def _process_image(self, image):
        if self.use_easyocr:
            return self._easyocr_lines(image)
        else:
            return self._tesseract_lines(image)

    # -----------------------------
    # EASYOCR (STRUCTURED OUTPUT)
    # -----------------------------
    def _easyocr_lines(self, image):
        results = self.easyocr_reader.readtext(np.array(image))

        # Filter low-confidence noise
        results = [r for r in results if r[2] > 0.4]

        # Sort by vertical position (top to bottom)
        results.sort(key=lambda x: min([pt[1] for pt in x[0]]))

        lines = []
        current_line = []
        current_y = None

        threshold = 15  # vertical grouping tolerance

        for bbox, text, conf in results:
            y = min([pt[1] for pt in bbox])

            if current_y is None:
                current_y = y

            # Same line grouping
            if abs(y - current_y) < threshold:
                current_line.append((bbox, text))
            else:
                # finalize previous line
                lines.append(self._merge_line(current_line))
                current_line = [(bbox, text)]
                current_y = y

        # last line
        if current_line:
            lines.append(self._merge_line(current_line))

        return self._clean_lines(lines)

    # -----------------------------
    # TESSERACT FALLBACK
    # -----------------------------
    def _tesseract_lines(self, image):
        text = pytesseract.image_to_string(image)
        lines = text.split("\n")
        return self._clean_lines(lines)

    # -----------------------------
    # MERGE WORDS INTO LINE
    # -----------------------------
    def _merge_line(self, line_items):
        # sort by X (left → right)
        line_items.sort(key=lambda x: min([pt[0] for pt in x[0]]))
        return " ".join([item[1] for item in line_items])

    # -----------------------------
    # CLEANING
    # -----------------------------
    def _clean_lines(self, lines):
        cleaned = []
        for line in lines:
            line = line.strip()

            # remove garbage lines
            if len(line) < 2:
                continue

            # remove OCR artifacts
            line = line.replace("|", "").replace(":", " : ")

            cleaned.append(line)

        return cleaned