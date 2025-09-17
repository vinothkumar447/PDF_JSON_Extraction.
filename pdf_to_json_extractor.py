import argparse
import json
import os
import re
from io import BytesIO
import webbrowser

# --- Imports ---
try:
    import pdfplumber
except ImportError:
    raise ImportError("Missing dependency: pdfplumber (install with `pip install pdfplumber`)")

try:
    import camelot
    HAS_CAMELOT = True
except Exception:
    HAS_CAMELOT = False

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except Exception:
    HAS_OCR = False


# --- Utility Functions ---
def is_heading(text: str) -> bool:
    """Heuristic to identify headings or section titles."""
    if not text:
        return False
    txt = text.strip()
    if len(txt) <= 60 and sum(c.isupper() for c in txt) > len(txt) * 0.5:
        return True
    if 1 <= len(txt.split()) <= 6 and txt[0].isupper() and txt.endswith(':'):
        return True
    if re.match(r'^(introduction|summary|conclusion|background|methodology|results|discussion|references)[:\s]?', txt, re.I):
        return True
    return False

def clean_text(s: str) -> str:
    """Remove extra spaces/newlines."""
    return re.sub(r"\s+", " ", s or "").strip()


# --- Extraction Functions ---
def extract_text_blocks(page):
    """Extract textual blocks from page."""
    blocks = []
    try:
        text = page.extract_text()
        if text:
            raw_blocks = re.split(r'\n\s*\n', text)
            blocks = [b for b in raw_blocks if b.strip()]
    except Exception:
        pass
    return blocks

def organize_sections(blocks):
    """Organize paragraphs into nested sections and sub-sections."""
    sections = []
    current_section = None
    current_sub = None

    for b in blocks:
        text = clean_text(b)
        if not text:
            continue
        first_line = text.split('\n')[0]

        if is_heading(first_line):
            # Decide if section or sub-section
            if current_section is None or len(first_line.split()) <= 3:
                # New section
                current_section = {
                    "section": first_line.rstrip(':'),
                    "sub_sections": []
                }
                sections.append(current_section)
                current_sub = None
            else:
                # New sub-section
                current_sub = {
                    "sub_section": first_line.rstrip(':'),
                    "paragraphs": []
                }
                if current_section is None:
                    # Create dummy section
                    current_section = {"section": "General", "sub_sections": [current_sub]}
                    sections.append(current_section)
                else:
                    current_section["sub_sections"].append(current_sub)
            # Add remaining text as paragraph
            rest = '\n'.join(text.split('\n')[1:]).strip()
            if rest:
                if current_sub:
                    current_sub["paragraphs"].append(rest)
                else:
                    # If no sub-section, create default
                    default_sub = {"sub_section": None, "paragraphs": [rest]}
                    current_section["sub_sections"].append(default_sub)
        else:
            # Regular paragraph
            if current_sub:
                current_sub["paragraphs"].append(text)
            elif current_section:
                default_sub = {"sub_section": None, "paragraphs": [text]}
                current_section["sub_sections"].append(default_sub)
            else:
                # No section yet
                default_section = {
                    "section": "General",
                    "sub_sections": [{"sub_section": None, "paragraphs": [text]}]
                }
                sections.append(default_section)
                current_section = default_section
    return sections

def extract_tables(pdf_path, page_number, page):
    """Extract tables using Camelot (preferred) or pdfplumber fallback."""
    tables = []
    if HAS_CAMELOT:
        try:
            tables = [t.df.values.tolist() for t in camelot.read_pdf(pdf_path, pages=str(page_number))]
        except Exception:
            pass
    if not tables:
        try:
            tables = [[[(cell or "") for cell in row] for row in tbl] for tbl in page.extract_tables()]
        except Exception:
            pass
    return [{'type': 'table', 'section': None, 'description': None, 'table_data': t} for t in tables]

def extract_images(pdf_path, page_number, page):
    """Extract images, apply OCR, classify chart vs image."""
    results = []
    if HAS_FITZ and HAS_OCR:
        try:
            doc = fitz.open(pdf_path)
            page_fitz = doc[page_number - 1]
            for img in page_fitz.get_images(full=True):
                base_img = doc.extract_image(img[0])
                try:
                    im = Image.open(BytesIO(base_img["image"]))
                    text = clean_text(pytesseract.image_to_string(im))
                    table_data = [] if re.search(r'\d', text) else None
                    results.append({
                        'type': 'chart' if table_data is not None else 'image',
                        'section': None,
                        'description': text or None,
                        'table_data': table_data
                    })
                except Exception:
                    continue
        except Exception:
            pass
    elif HAS_OCR:
        try:
            for img in page.images:
                try:
                    bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                    im = page.crop(bbox).to_image(resolution=150).original
                    text = clean_text(pytesseract.image_to_string(im))
                    table_data = [] if re.search(r'\d', text) else None
                    results.append({
                        'type': 'chart' if table_data is not None else 'image',
                        'section': None,
                        'description': text or None,
                        'table_data': table_data
                    })
                except Exception:
                    continue
        except Exception:
            pass
    return results

# --- Main Processing ---
def build_json(pdf_path: str) -> dict:
    """Process PDF and build structured JSON with nested sections/sub-sections."""
    result = {'pages': []}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_content = []

            # Extract text blocks
            blocks = extract_text_blocks(page)
            page_content.extend(organize_sections(blocks))

            # Extract tables and images
            page_content.extend(extract_tables(pdf_path, i, page))
            page_content.extend(extract_images(pdf_path, i, page))

            result['pages'].append({'page_number': i, 'content': page_content})
    return result

def main():
    parser = argparse.ArgumentParser(description="Extract structured JSON from a PDF")
    parser.add_argument(
        "-i", "--input",
        default=r"C:\Users\vinuv\Downloads\[Fund Factsheet - May]360ONE-MF-May 2025.pdf.pdf",
        help="Input PDF file path"
    )
    parser.add_argument(
        "-o", "--output",
        default="output.json",
        help="Output JSON file path"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"❌ Input file not found: {args.input}")
        return

    print(f"Processing: {args.input}")
    data = build_json(args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"JSON saved to: {args.output}")

    # Auto-open JSON in browser
    abs_path = os.path.abspath(args.output)
    webbrowser.open(f'file://{abs_path}')

if __name__ == "__main__":
    main()
