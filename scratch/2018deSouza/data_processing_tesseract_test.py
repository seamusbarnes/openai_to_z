from pdf2image import convert_from_path
from pytesseract import image_to_string
from PIL import Image
import os

# Optional: Set path to tesseract executable if needed (Windows example)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path, dpi=300, page_nums=None):
    print(f"Converting pages {page_nums} of PDF to images...")
    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=min(page_nums),
        last_page=max(page_nums)
    )
    print(f"Converted {len(images)} pages to images.")

    all_text = []

    for i, image in enumerate(images):
        actual_page = page_nums[i]
        print(f"Processing OCR on page {actual_page}...")
        text = image_to_string(image, config='--psm 6')
        all_text.append((actual_page, text))
        print(f"Finished OCR for page {actual_page}.")

    print("Finished processing all pages.")
    return all_text

if __name__ == "__main__":
    pdf_path = '2018deSouza_supplementarry_information.pdf'  # Replace with your actual PDF path
    pages_to_extract = [8, 9, 10]
    extracted = extract_text_from_pdf(pdf_path, page_nums=pages_to_extract)

    for page_num, text in extracted:
        print(f"--- Page {page_num} ---")
        print(text)