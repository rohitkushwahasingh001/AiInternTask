import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
        
        # If text is empty, try OCR on image
        if not page.get_text():
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            text += pytesseract.image_to_string(img)
    return text
