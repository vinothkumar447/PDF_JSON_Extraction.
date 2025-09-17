# PDF Parsing and Structured JSON Extraction Assignment

## Assignment Objective

The goal of this assignment is to build a Python program that parses a PDF file and extracts its content into a **well-structured JSON format**.  
The extracted JSON preserves the hierarchical organization of the document, including sections, sub-sections, paragraphs, tables, and charts/images.

## Features

- Extracts textual content with **section/sub-section detection**.  
- Extracts **tables** using Camelot (preferred) or pdfplumber fallback.  
- Extracts **images and charts**, with OCR (via pytesseract) to identify textual content inside images.  
- Produces a **clean, hierarchical JSON output** that follows page-level organization.  

## JSON Structure

The JSON output has the following structure:

```json
{
  "pages": [
    {
      "page_number": 1,
      "content": [
        {
          "type": "paragraph",
          "section": "Introduction",
          "sub_section": "Background",
          "text": "This is an example paragraph extracted from the PDF..."
        },
        {
          "type": "table",
          "section": "Financial Data",
          "description": null,
          "table_data": [
            ["Year", "Revenue", "Profit"],
            ["2022", "$10M", "$2M"],
            ["2023", "$12M", "$3M"]
          ]
        },
        {
          "type": "chart",
          "section": "Performance Overview",
          "description": "Bar chart showing yearly growth...",
          "table_data": []
        }
      ]
    }
  ]
}
```

## Dependencies

Install required Python packages using pip (preferably in a virtual environment):

```
pdfplumber==0.7.6
camelot-py[cv]==0.10.1
pytesseract==0.3.10
Pillow==9.5.0
PyMuPDF==1.22.5
```

## Setup

1. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
```

2. Activate the virtual environment:

- **Windows:**  
```bash
venv\Scripts\activate
```

- **macOS/Linux:**  
```bash
source venv/bin/activate
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

4. Install **Tesseract OCR** (required for image text extraction):

- **Windows:** [Download Installer](https://github.com/UB-Mannheim/tesseract/wiki)  
- **Ubuntu:**  
```bash
sudo apt install tesseract-ocr
```  
- **macOS:**  
```bash
brew install tesseract
```

## Usage

Run the Python script with the input PDF and output JSON paths:

```bash
python pdf_to_json_extractor.py -i "input.pdf" -o "output.json"
```

- **Default input PDF:** `"input.pdf"`  
- **Default output JSON:** `"output.json"`  

The script will:  
1. Parse the PDF page by page.  
2. Detect headings for sections/sub-sections.  
3. Extract paragraphs, tables, and charts/images.  
4. Build structured JSON.

## Output

- Preserves **page-level hierarchy**.  
- Includes **sections & sub-sections**, paragraphs, tables, and charts/images.

Example:

```json
{
  "pages": [
    {
      "page_number": 1,
      "content": [
        {
          "section": "Introduction",
          "sub_section": "Background",
          "paragraphs": ["This is an example paragraph extracted from the PDF."]
        },
        {
          "type": "table",
          "section": null,
          "description": null,
          "table_data": [["Year", "Revenue"], ["2022", "$10M"]]
        }
      ]
    }
  ]
}
```

## Notes & Limitations

- Section/sub-section detection is **heuristic-based** (font case, length, keywords).  
- Table extraction works best with **well-structured tables**.  
- OCR works for images with readable text; charts with only graphics may not extract numerical data.  
- Multi-column PDFs may require preprocessing for best results.  

## Deliverables

1. **Python script:** `pdf_to_json_extractor.py`  
2. **Output JSON:** `output.json`  
