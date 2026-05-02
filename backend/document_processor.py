import os
import re
import math
import pdfplumber
import PyPDF2
import camelot
import tabula
from pdf2image import convert_from_path
import pytesseract
import pandas as pd
import numpy as np

try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class DocumentProcessor:
    def __init__(self):
        if HAS_PADDLE:
            try:
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
            except Exception:
                self.ocr = None
        else:
            self.ocr = None

    def validate_pdf(self, file_path):
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF")
        if os.path.getsize(file_path) > 50 * 1024 * 1024:
            raise ValueError("File size must not exceed 50MB")
        return True

    # ─────────────────── Text-Based Detection ─────────────────────────────────
    def is_text_based(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                if len(reader.pages) > 0:
                    text = reader.pages[0].extract_text()
                    if text and len(text.strip()) > 50:
                        return True
        except Exception:
            pass
        return False

    # ─────────────────── OpenCV Image Preprocessing for Low-Quality Scans ─────
    def preprocess_image_for_ocr(self, img):
        if not HAS_OPENCV:
            return np.array(img)

        img_array = np.array(img)

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Apply adaptive thresholding for better text contrast
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Median blur to reduce noise (especially for 72 DPI scans)
        denoised = cv2.medianBlur(thresh, 3)

        return denoised

    # ─────────────────── Cascading Extraction Pipeline ────────────────────────
    def extract_text_and_tables(self, file_path):
        is_text = self.is_text_based(file_path)
        raw_text = ""
        tables = []
        extraction_method = "none"

        if is_text:
            # ── Stage 1: pdfplumber (primary) ──
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            raw_text += text + "\n"
                extraction_method = "pdfplumber"
            except Exception:
                pass

            # Quality check: if pdfplumber extracted too little, cascade
            if len(raw_text.strip()) < 100:
                raw_text = ""
                try:
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text = page.extract_text()
                            if text:
                                raw_text += text + "\n"
                    extraction_method = "PyPDF2"
                except Exception:
                    pass

            # ── Table Extraction Cascade: Camelot → Tabula ──
            try:
                camelot_tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
                if not camelot_tables or len(camelot_tables) == 0:
                    camelot_tables = camelot.read_pdf(file_path, pages='all', flavor='stream')
                tables = [table.df for table in camelot_tables]
            except Exception:
                try:
                    tabula_tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
                    if tabula_tables:
                        tables = tabula_tables
                except Exception:
                    pass
        else:
            # ── Scanned PDF: OCR Pipeline with Image Preprocessing ──
            extraction_method = "ocr"
            try:
                images = convert_from_path(file_path, dpi=300)
                for img in images:
                    # Preprocess image using OpenCV (grayscale, threshold, denoise)
                    processed = self.preprocess_image_for_ocr(img)

                    # Try PaddleOCR first
                    if self.ocr:
                        try:
                            result = self.ocr.ocr(processed, cls=True)
                            if result and result[0]:
                                page_text = " ".join([line[1][0] for line in result[0]])
                                raw_text += page_text + "\n"
                                continue
                        except Exception:
                            pass

                    # Fallback to Tesseract
                    try:
                        page_text = pytesseract.image_to_string(processed)
                        raw_text += page_text + "\n"
                    except Exception:
                        pass

            except Exception:
                # Final fallback: force pdfplumber even on "scanned" PDF
                try:
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                raw_text += text + "\n"
                    extraction_method = "pdfplumber-forced"
                except Exception:
                    pass

        return raw_text, tables, extraction_method

    # ─────────────────── Company Detection ────────────────────────────────────
    def detect_company_info(self, raw_text):
        lines = raw_text.split('\n')[:50]
        company_name = None
        trading_symbol = None

        name_keywords = ["Limited", "Ltd", "Bank", "Corporation", "Inc", "Industries", "Infosys", "Wipro"]
        best_score = -1

        for i, line in enumerate(lines):
            score = 0
            for kw in name_keywords:
                if kw.lower() in line.lower():
                    score += 5
            if score > 0:
                score -= i * 0.1
                if score > best_score:
                    best_score = score
                    company_name = line.strip()

        # BSE/NSE symbol patterns
        # Strict matching: require colon or hyphen if it's just 'Symbol'
        symbol_pattern = re.compile(r'(?:NSE|BSE|Scrip Code|BSE Code|NSE Symbol)\s*[:\-]?\s*([A-Z0-9]{3,15})|Symbol\s*[:\-]\s*([A-Z0-9]{3,15})', re.IGNORECASE)
        match = symbol_pattern.search(raw_text)
        if match:
            extracted_sym = (match.group(1) or match.group(2)).upper().strip()
            # Ignore false positives
            if extracted_sym not in ['LIMITED', 'LTD', 'COMPANY', 'INC', 'AND', 'THE']:
                trading_symbol = extracted_sym

        # Fallback: Use Yahoo Finance Search API if company name was found but symbol was not
        if not trading_symbol and company_name:
            import requests
            import urllib.parse
            try:
                # Clean company name and URL encode it
                clean_name = re.sub(r'[^\w\s]', '', company_name).strip()
                encoded_query = urllib.parse.quote(clean_name)
                url = f"https://query2.finance.yahoo.com/v1/finance/search?q={encoded_query}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    quotes = res.json().get('quotes', [])
                    for q in quotes:
                        exch = q.get('exchange')
                        sym = q.get('symbol', '')
                        # Prefer Indian exchanges
                        if exch in ['NSE', 'BSE', 'NSI'] or sym.endswith('.NS') or sym.endswith('.BO'):
                            trading_symbol = sym.replace('.NS', '').replace('.BO', '')
                            break
                    # If still not found, just take the first match as a last resort
                    if not trading_symbol and quotes:
                        trading_symbol = quotes[0].get('symbol', '').replace('.NS', '').replace('.BO', '')
            except Exception as e:
                print(f"Yahoo Search fallback failed: {e}")

        print(f"--- Company Detection ---")
        print(f"Extracted Name: {company_name}")
        print(f"Detected Symbol: {trading_symbol}")
        print(f"-------------------------")

        return company_name, trading_symbol

    # ─────────────────── Indian Number Parser ─────────────────────────────────
    def parse_indian_number(self, text):
        text = text.lower().replace(',', '')
        match = re.search(r'([\d.]+)\s*(crore|cr|lakh|million|mn|billion|bn)?', text)
        if not match:
            return None

        val = float(match.group(1))
        unit = match.group(2)

        if unit in ['crore', 'cr']:
            return val * 10_000_000
        elif unit == 'lakh':
            return val * 100_000
        elif unit in ['million', 'mn']:
            return val * 1_000_000
        elif unit in ['billion', 'bn']:
            return val * 1_000_000_000
        return val

    # ─────────────────── Main Process ─────────────────────────────────────────
    def process(self, file_path):
        self.validate_pdf(file_path)
        raw_text, tables, extraction_method = self.extract_text_and_tables(file_path)
        company_name, symbol = self.detect_company_info(raw_text)

        return {
            "raw_text": raw_text,
            "tables": tables,
            "company_name": company_name,
            "trading_symbol": symbol,
            "extraction_method": extraction_method,
            "is_scanned": extraction_method == "ocr"
        }
