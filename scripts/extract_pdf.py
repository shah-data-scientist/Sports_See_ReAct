"""
Extract text from the evaluation PDF.
"""
import os
import sys

try:
    import PyPDF2

    # Find the PDF file dynamically
    docs_dir = r"C:\Users\shahu\Documents\OneDrive\OPEN CLASSROOMS\PROJET 10\Sports_See\docs"
    pdf_files = [f for f in os.listdir(docs_dir) if f.endswith('.pdf') and 'valuez' in f.lower()]

    if not pdf_files:
        print(f"ERROR: No evaluation PDF found in {docs_dir}")
        sys.exit(1)

    pdf_filename = pdf_files[0]
    pdf_path = os.path.join(docs_dir, pdf_filename)

    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    print(f"Reading PDF: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes\n")

    with open(pdf_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        num_pages = len(pdf_reader.pages)
        print(f"Total pages: {num_pages}\n")

        full_text = []
        for i, page in enumerate(pdf_reader.pages, 1):
            print(f"Extracting page {i}/{num_pages}...")
            text = page.extract_text()
            full_text.append(f"\n{'='*80}\nPAGE {i}\n{'='*80}\n\n{text}")

        combined_text = "\n".join(full_text)
        print(f"\n\nTotal extracted text length: {len(combined_text)} characters\n")
        print(combined_text)

except ImportError:
    print("PyPDF2 not installed. Trying alternative...")
    try:
        import pdfplumber

        # Find the PDF file dynamically
        docs_dir = r"C:\Users\shahu\Documents\OneDrive\OPEN CLASSROOMS\PROJET 10\Sports_See\docs"
        pdf_files = [f for f in os.listdir(docs_dir) if f.endswith('.pdf') and 'valuez' in f.lower()]
        pdf_filename = pdf_files[0]
        pdf_path = os.path.join(docs_dir, pdf_filename)

        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}\n")

            full_text = []
            for i, page in enumerate(pdf.pages, 1):
                print(f"Extracting page {i}/{len(pdf.pages)}...")
                text = page.extract_text()
                full_text.append(f"\n{'='*80}\nPAGE {i}\n{'='*80}\n\n{text}")

            combined_text = "\n".join(full_text)
            print(f"\n\nTotal extracted text length: {len(combined_text)} characters\n")
            print(combined_text)

    except ImportError:
        print("Neither PyPDF2 nor pdfplumber is installed.")
        sys.exit(1)
