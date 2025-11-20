#!/usr/bin/env python3
"""
Simple Citation Extractor
Extracts citations from the excited_delirium.pdf file only
"""

import PyPDF2
import re
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text content from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def find_references_section(text: str) -> str:
    """Find and extract the references/bibliography section"""
    # Common patterns for references sections
    ref_patterns = [
        r"(?i)references\s*\n(.*?)(?=\n\s*\n|\Z)",
        r"(?i)bibliography\s*\n(.*?)(?=\n\s*\n|\Z)",
        r"(?i)works cited\s*\n(.*?)(?=\n\s*\n|\Z)",
        r"(?i)literature cited\s*\n(.*?)(?=\n\s*\n|\Z)"
    ]
    
    for pattern in ref_patterns:
        match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
        if match:
            return match.group(1)
    
    # If no explicit references section found, look for citation patterns throughout
    return text

def extract_citations(text: str) -> List[str]:
    """Extract individual citations from text"""
    citations = []
    
    # Split by common citation separators
    # Look for patterns like numbered citations or author-year patterns
    
    # Pattern 1: Numbered citations (1. Author, Title...)
    numbered_pattern = r'^\s*\d+\.\s+(.+?)(?=\n\s*\d+\.\s+|\Z)'
    numbered_matches = re.findall(numbered_pattern, text, re.MULTILINE | re.DOTALL)
    if numbered_matches:
        citations.extend(numbered_matches)
    
    # Pattern 2: Author-year citations in parentheses throughout text
    inline_pattern = r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s+\d{4}[a-z]?)\)'
    inline_matches = re.findall(inline_pattern, text)
    if inline_matches:
        citations.extend(inline_matches)
    
    # Pattern 3: Full citations (Author. Year. Title. Journal.)
    full_citation_pattern = r'([A-Z][a-zA-Z\s,]+\.\s+\d{4}[a-z]?\.\s+.+?\.(?:\s+[A-Z][a-zA-Z\s]+\.)?)'
    full_matches = re.findall(full_citation_pattern, text)
    if full_matches:
        citations.extend(full_matches)
    
    # Clean up citations
    cleaned_citations = []
    for citation in citations:
        # Remove excessive whitespace and newlines
        clean_citation = ' '.join(citation.split())
        if len(clean_citation) > 10:  # Filter out very short matches
            cleaned_citations.append(clean_citation)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_citations = []
    for citation in cleaned_citations:
        if citation not in seen:
            seen.add(citation)
            unique_citations.append(citation)
    
    return unique_citations

def main():
    pdf_path = "/Users/proctorf/Documents/GitHub/AIH/Eleanor/excited_delirium.pdf"
    
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print("Could not extract text from PDF")
        return
    
    print(f"Extracted {len(text)} characters of text")
    print("\nLooking for references section...")
    
    references_section = find_references_section(text)
    print(f"Found references section with {len(references_section)} characters")
    
    print("\nExtracting citations...")
    citations = extract_citations(references_section)
    
    print(f"\nFound {len(citations)} citations:\n")
    print("=" * 80)
    
    for i, citation in enumerate(citations, 1):
        print(f"{i:2d}. {citation}")
        print("-" * 80)
    
    # Save citations to a text file
    with open("extracted_citations.txt", "w", encoding="utf-8") as f:
        f.write("Citations extracted from excited_delirium.pdf\n")
        f.write("=" * 50 + "\n\n")
        for i, citation in enumerate(citations, 1):
            f.write(f"{i:2d}. {citation}\n\n")
    
    print(f"\nCitations saved to 'extracted_citations.txt'")

if __name__ == "__main__":
    main()