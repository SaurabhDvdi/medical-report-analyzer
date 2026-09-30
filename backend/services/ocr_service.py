import os
import sys
import time
import psutil
import pytesseract
from PIL import Image
import pdf2image
import numpy as np
import tempfile
import threading
from logging_config import get_logger

if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    for p in sys.path:
        for candidate in ["sklearn/.libs", "numpy.libs", "pandas.libs"]:
            target = os.path.join(p, *candidate.split("/"))
            if os.path.isdir(target):
                try:
                    os.add_dll_directory(target)
                except Exception:
                    pass

logger = get_logger(__name__)

# Thread-safe Lazy Singleton for EasyOCR Reader
_easyocr_reader_instance = None
_easyocr_init_failed = False
_reader_lock = threading.Lock()


def get_current_ram_mb() -> float:
    try:
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def _get_easyocr_reader():
    global _easyocr_reader_instance, _easyocr_init_failed
    if _easyocr_init_failed:
        return None

    if _easyocr_reader_instance is None:
        with _reader_lock:
            if _easyocr_reader_instance is None and not _easyocr_init_failed:
                try:
                    init_start = time.perf_counter()
                    ram_before = get_current_ram_mb()
                    import easyocr
                    _easyocr_reader_instance = easyocr.Reader(['en'], gpu=False)
                    init_end = time.perf_counter()
                    ram_after = get_current_ram_mb()
                    logger.info(
                        f"[PROFILE_OCR_INIT] EasyOCR reader initialized in {(init_end - init_start)*1000:.2f}ms | "
                        f"RAM before={ram_before:.2f}MB, after={ram_after:.2f}MB, delta={ram_after - ram_before:.2f}MB"
                    )
                except Exception as e:
                    _easyocr_init_failed = True
                    logger.warning(f"EasyOCR initialization failed: {str(e)}. Fallback to Tesseract.")
                    return None

    return _easyocr_reader_instance


class OCRService:
    ROW_Y_TOLERANCE: float = 4.0

    def __init__(self, row_y_tolerance: float = 4.0):
        self.row_y_tolerance = row_y_tolerance

    def extract_direct_text(self, file_path: str) -> list:
        """
        Extract usable direct embedded text from PDF without invoking OCR.
        Reconstructs table rows using word coordinates (y_mid grouping within row_y_tolerance).
        Returns list of lines if usable embedded text is present (>= 3 lines), else [].
        """
        if not file_path.lower().endswith('.pdf'):
            return []

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            all_lines = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                words = page.get_text("words")
                if words:
                    # Sort words primarily by vertical midpoint, secondarily by x0
                    words_sorted = sorted(words, key=lambda w: ((w[1] + w[3]) / 2.0, w[0]))
                    curr_row = []
                    curr_y = None
                    for w in words_sorted:
                        y_mid = (w[1] + w[3]) / 2.0
                        if curr_y is None or abs(y_mid - curr_y) <= self.row_y_tolerance:
                            curr_row.append(w)
                            if curr_y is None:
                                curr_y = y_mid
                        else:
                            curr_row.sort(key=lambda item: item[0])
                            row_text = " ".join(item[4] for item in curr_row).strip()
                            if len(row_text) > 1:
                                all_lines.append(row_text)
                            curr_row = [w]
                            curr_y = y_mid
                    if curr_row:
                        curr_row.sort(key=lambda item: item[0])
                        row_text = " ".join(item[4] for item in curr_row).strip()
                        if len(row_text) > 1:
                            all_lines.append(row_text)
                else:
                    text = page.get_text()
                    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
                    if lines:
                        all_lines.extend(lines)
            doc.close()

            if len(all_lines) >= 3:
                return self._clean_lines(all_lines)
            return []
        except Exception as e:
            logger.warning(f"Direct text extraction error: {e}, trying pypdf fallback...")
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                pypdf_lines = []
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        pypdf_lines.extend([l.strip() for l in txt.split('\n') if len(l.strip()) > 1])
                if len(pypdf_lines) >= 3:
                    return self._clean_lines(pypdf_lines)
            except Exception as pypdf_err:
                logger.warning(f"pypdf fallback failed: {pypdf_err}")
            return []

    def extract_raw_direct_text(self, file_path: str) -> str:
        """
        Extract verbatim raw text stream from PDF without modification for display purposes.
        """
        if not file_path.lower().endswith('.pdf'):
            return ""
        try:
            import fitz
            doc = fitz.open(file_path)
            raw_parts = [page.get_text() for page in doc]
            doc.close()
            return "\n".join(raw_parts).strip()
        except Exception as e:
            logger.warning(f"Raw direct text extraction error: {e}, trying pypdf fallback...")
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                parts = [p.extract_text() or "" for p in reader.pages]
                return "\n".join(parts).strip()
            except Exception:
                return ""

    def extract_first_page_text(self, file_path: str) -> tuple:
        """
        Extract text from the first page of a document for early medical classification.
        Returns (lines: list, is_scanned: bool).
        """
        import gc
        if not file_path.lower().endswith('.pdf'):
            # Image file
            return self._extract_from_image(file_path), True

        try:
            import fitz
            doc = fitz.open(file_path)
            if len(doc) == 0:
                doc.close()
                return [], False

            page = doc[0]
            text = page.get_text()
            direct_lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]

            if len(direct_lines) >= 3:
                doc.close()
                return self._clean_lines(direct_lines), False

            # First page is scanned - render and OCR page 0 only
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()

            ocr_lines = self._process_image(img)
            del pix, img
            gc.collect()
            return ocr_lines, True
        except Exception as e:
            logger.warning(f"First-page extraction error: {e}, trying pypdf fallback...")
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                if len(reader.pages) > 0:
                    txt = reader.pages[0].extract_text()
                    if txt:
                        lines = [l.strip() for l in txt.split('\n') if len(l.strip()) > 1]
                        if len(lines) >= 3:
                            return self._clean_lines(lines), False
            except Exception:
                pass
            return [], True

    def extract_remaining_pages_text(self, file_path: str, start_page: int = 1) -> list:
        """
        Progressive OCR: Extract text from remaining pages (page 1 onwards)
        only after first-page medical validation succeeds.
        """
        import gc
        if not file_path.lower().endswith('.pdf'):
            return []

        all_lines = []
        try:
            import fitz
            doc = fitz.open(file_path)
            total_pages = len(doc)
            if start_page >= total_pages:
                doc.close()
                return []

            for page_num in range(start_page, total_pages):
                page = doc[page_num]
                text = page.get_text()
                direct_lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]

                if len(direct_lines) >= 3:
                    all_lines.extend(direct_lines)
                else:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_lines = self._process_image(img)
                    all_lines.extend(ocr_lines)
                    del pix, img
                    gc.collect()

            doc.close()
            return self._clean_lines(all_lines)
        except Exception as e:
            logger.warning(f"Remaining pages extraction error: {e}")
            return self._clean_lines(all_lines)

    def extract_text(self, file_path: str):
        # Returns list of text lines from PDF or image
        try:
            if file_path.lower().endswith('.pdf'):
                return self._extract_from_pdf(file_path)
            else:
                return self._extract_from_image(file_path)
        except Exception as e:
            logger.exception(f"OCR Error: {str(e)}")
            return []

    def _extract_from_pdf(self, file_path: str):
        """
        Primary Strategy: Fast PyMuPDF direct text extraction.
        If the PDF contains digital text (>= 3 usable lines), return immediately (0ms DPI rendering, 0 EasyOCR).
        Fallback Strategy: If PyMuPDF text is missing or scanned, perform image-based OCR via PyMuPDF.
        """
        import gc
        all_lines = []
        ram_start = get_current_ram_mb()

        # 1. Primary Path: PyMuPDF (fitz) Direct Text Extraction
        try:
            t0 = time.perf_counter()
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            pages_needing_ocr = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                page_lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 1]
                
                if len(page_lines) >= 3:
                    all_lines.extend(page_lines)
                else:
                    pages_needing_ocr.append(page_num)

            # If all or most pages yielded direct text, return immediately!
            if len(all_lines) >= 3 and len(pages_needing_ocr) == 0:
                doc.close()
                t1 = time.perf_counter()
                logger.info(
                    f"[PROFILE_DIRECT_TEXT] PyMuPDF extracted {len(all_lines)} direct text lines in {(t1 - t0)*1000:.2f}ms. "
                    f"RAM start={ram_start:.2f}MB"
                )
                return self._clean_lines(all_lines)

            # 2. Fallback Path for Scanned Pages: Perform page-level OCR rendering using PyMuPDF pixmaps
            if pages_needing_ocr:
                for page_num in pages_needing_ocr:
                    r0 = time.perf_counter()
                    page = doc[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    r1 = time.perf_counter()
                    
                    ocr_lines = self._process_image(img)
                    all_lines.extend(ocr_lines)
                    del pix, img  # Prompt RAM release
                    gc.collect()
                    
                    logger.info(f"[PROFILE_PAGE_RENDER] Page {page_num} rendered in {(r1 - r0)*1000:.2f}ms")
            
            doc.close()
            if len(all_lines) >= 2:
                ram_end = get_current_ram_mb()
                logger.info(
                    f"[PROFILE_SCANNED_PDF] PyMuPDF + Page OCR extracted {len(all_lines)} lines. "
                    f"RAM start={ram_start:.2f}MB, end={ram_end:.2f}MB"
                )
                return self._clean_lines(all_lines)

        except ImportError:
            logger.warning("PyMuPDF not installed, falling back to pdf2image OCR...")
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {str(e)}, trying pdf2image OCR fallback...")

        # 3. Last Fallback: pdf2image with Poppler (for scanned PDFs if PyMuPDF failed)
        try:
            poppler_env = os.getenv("POPPLER_PATH")
            poppler_path = poppler_env if poppler_env and os.path.isdir(poppler_env) else None

            with tempfile.TemporaryDirectory() as output_dir:
                images = pdf2image.convert_from_path(
                    file_path, 
                    dpi=300, 
                    poppler_path=poppler_path,
                    output_folder=output_dir,
                    paths_only=True
                )

                for img_path in images:
                    with Image.open(img_path) as image:
                        lines = self._process_image(image)
                        all_lines.extend(lines)
            
            logger.info(f"pdf2image extracted {len(all_lines)} lines from PDF")
            return self._clean_lines(all_lines)
        except Exception as e:
            logger.exception(f"All PDF extraction paths failed: {str(e)}")
            return self._clean_lines(all_lines)

    def _extract_from_image(self, file_path: str):
        try:
            with Image.open(file_path) as image:
                return self._process_image(image)
        except Exception as e:
            logger.exception(f"Image OCR Error: {str(e)}")
            return []

    # -----------------------------
    # CORE PROCESSOR
    # -----------------------------
    def _process_image(self, image):
        reader = _get_easyocr_reader()
        if reader is not None:
            return self._easyocr_lines(image, reader)
        else:
            return self._tesseract_lines(image)

    def _easyocr_lines(self, image, reader):
        ram_before = get_current_ram_mb()
        inf_start = time.perf_counter()
        results = reader.readtext(np.array(image))
        inf_end = time.perf_counter()
        ram_after = get_current_ram_mb()

        grp_start = time.perf_counter()
        # Filter low-confidence detections and sort by vertical position
        results = [r for r in results if r[2] > 0.4]
        results.sort(key=lambda x: min([pt[1] for pt in x[0]]))

        lines = []
        current_line = []
        current_y = None
        threshold = 15  # pixels; group text on same line

        for bbox, text, conf in results:
            y = min([pt[1] for pt in bbox])

            if current_y is None:
                current_y = y

            if abs(y - current_y) < threshold:
                current_line.append((bbox, text))
            else:
                lines.append(self._merge_line(current_line))
                current_line = [(bbox, text)]
                current_y = y

        if current_line:
            lines.append(self._merge_line(current_line))
        grp_end = time.perf_counter()

        cleaned_lines = self._clean_lines(lines)

        logger.info(
            f"[PROFILE_EASYOCR] Inference: {(inf_end - inf_start)*1000:.2f}ms | "
            f"Grouping: {(grp_end - grp_start)*1000:.2f}ms | "
            f"Detections: {len(results)} | Lines: {len(cleaned_lines)} | "
            f"RAM before: {ram_before:.2f}MB, after: {ram_after:.2f}MB"
        )
        del results, lines, current_line
        import gc
        gc.collect()

        return cleaned_lines

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