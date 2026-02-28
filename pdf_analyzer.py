"""
PDF Template Analyzer
Reads the Idea Submission PDF to understand its structure
"""

import PyPDF2
import sys

def analyze_pdf(pdf_path):
    """Analyze the PDF structure and extract text"""
    print(f"Analyzing PDF: {pdf_path}\n")
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            print(f"Total pages: {num_pages}\n")
            print("=" * 60)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                print(f"\n--- Page {page_num + 1} ---")
                print(text)
                print("=" * 60)
                
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    pdf_path = "Docs/Idea Submission _ AWS AI for Bharat Hackathon.pdf"
    analyze_pdf(pdf_path)
