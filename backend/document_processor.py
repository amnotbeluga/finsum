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

try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False

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

    def extract_text_and_tables(self, file_path):
        is_text = self.is_text_based(file_path)
        raw_text = ""
        tables = []
        
        if is_text:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        raw_text += text + "\n"
            
            try:
                camelot_tables = camelot.read_pdf(file_path, pages='all', flavor='lattice')
                if not camelot_tables:
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
            # Scanned PDF — try OCR, fallback to pdfplumber force-extract
            try:
                images = convert_from_path(file_path)
                for img in images:
                    if self.ocr:
                        try:
                            import numpy as np
                            img_array = np.array(img)
                            result = self.ocr.ocr(img_array, cls=True)
                            if result and result[0]:
                                page_text = " ".join([line[1][0] for line in result[0]])
                                raw_text += page_text + "\n"
                                continue
                        except Exception:
                            pass
                    try:
                        page_text = pytesseract.image_to_string(img)
                        raw_text += page_text + "\n"
                    except Exception:
                        pass
            except Exception:
                # If pdf2image/poppler also fails, force pdfplumber extraction
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            raw_text += text + "\n"
                    
        return raw_text, tables

    def detect_company_info(self, raw_text):
        lines = raw_text.split('\n')[:50]  # First page/50 lines
        company_name = None
        trading_symbol = None
        
        name_keywords = ["Limited", "Ltd", "Bank", "Corporation", "Inc"]
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
                    
        # BSE/NSE symbol patterns (e.g., NSE: RELIANCE, BSE: 500325)
        symbol_pattern = re.compile(r'(?:NSE|BSE)\s*:\s*([A-Z0-9]+)')
        match = symbol_pattern.search(raw_text)
        if match:
            trading_symbol = match.group(1)
            
        return company_name, trading_symbol

    def parse_indian_number(self, text):
        # Parses formats like 1.5 Crore, 50 Lakh, 2 Million
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
            return val * 1,000_000
        elif unit in ['billion', 'bn']:
            return val * 1_000_000_000
        return val

    def process(self, file_path):
        self.validate_pdf(file_path)
        raw_text, tables = self.extract_text_and_tables(file_path)
        company_name, symbol = self.detect_company_info(raw_text)
        
        return {
            "raw_text": raw_text,
            "tables": tables,
            "company_name": company_name,
            "trading_symbol": symbol
        }
