#!/usr/bin/env python3
"""
Citation Network Extractor for PDF Files
Extracts citations from PDFs and creates nodes/edges tables for network analysis

Author: Generated for AIH Digital Humanities Course
Date: November 2025
"""

import PyPDF2
import re
import pandas as pd
import requests
from urllib.parse import quote
import json
from typing import Dict, List, Tuple, Set
import time


class CitationExtractor:
    """Extract and process citations from academic PDFs"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""
        self.citations = []
        self.nodes = pd.DataFrame()
        self.edges = pd.DataFrame()
        
    def extract_text_from_pdf(self) -> str:
        """Extract text content from PDF file"""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                self.text = text
                return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_references_section(self) -> str:
        """Extract the references/bibliography section from the text"""
        # Common patterns for references sections
        ref_patterns = [
            r"References\s*\n(.*?)(?:\n\n|\Z)",
            r"Bibliography\s*\n(.*?)(?:\n\n|\Z)",
            r"Works Cited\s*\n(.*?)(?:\n\n|\Z)",
            r"Literature Cited\s*\n(.*?)(?:\n\n|\Z)"
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        # Fallback: look for the last section that might be references
        lines = self.text.split('\n')
        for i, line in enumerate(lines):
            if re.match(r'^\s*(References|Bibliography|Works Cited)', line, re.IGNORECASE):
                return '\n'.join(lines[i+1:])
        
        return ""
    
    def parse_citations(self) -> List[Dict]:
        """Parse individual citations from the references section"""
        ref_text = self.extract_references_section()
        if not ref_text:
            print("Warning: No references section found")
            return []
        
        # Split citations (assuming each starts with author name or number)
        # This is a simplified parser - real citations are complex!
        citation_lines = []
        current_citation = ""
        
        for line in ref_text.split('\n'):
            line = line.strip()
            if not line:
                if current_citation:
                    citation_lines.append(current_citation.strip())
                    current_citation = ""
            elif re.match(r'^\d+\.', line) or re.match(r'^[A-Z][a-z]+,', line):
                # New citation starts
                if current_citation:
                    citation_lines.append(current_citation.strip())
                current_citation = line
            else:
                # Continuation of current citation
                current_citation += " " + line
        
        # Don't forget the last citation
        if current_citation:
            citation_lines.append(current_citation.strip())
        
        # Parse each citation into structured data
        citations = []
        for i, cite_text in enumerate(citation_lines):
            citation = self.parse_individual_citation(cite_text, i)
            if citation:
                citations.append(citation)
        
        self.citations = citations
        return citations
    
    def parse_individual_citation(self, cite_text: str, index: int) -> Dict:
        """Parse individual citation into structured fields"""
        # This is a simplified parser - real citation parsing is very complex
        citation = {
            'id': f"cite_{index}",
            'raw_text': cite_text,
            'authors': [],
            'title': '',
            'year': None,
            'journal': '',
            'volume': '',
            'pages': '',
            'doi': '',
            'type': 'unknown'
        }
        
        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', cite_text)
        if year_match:
            citation['year'] = int(year_match.group())
        
        # Extract DOI
        doi_match = re.search(r'doi:\s*([^\s]+)', cite_text, re.IGNORECASE)
        if doi_match:
            citation['doi'] = doi_match.group(1)
        
        # Extract authors (simplified - just first author)
        author_match = re.match(r'^([^.]+?),', cite_text)
        if author_match:
            citation['authors'] = [author_match.group(1).strip()]
        
        # Extract title (text in quotes or after author and before year)
        title_match = re.search(r'"([^"]+)"', cite_text)
        if title_match:
            citation['title'] = title_match.group(1)
        else:
            # Try to extract title between author and year
            if citation['year']:
                parts = cite_text.split(str(citation['year']))
                if len(parts) > 1:
                    # Title might be before year
                    title_part = parts[0]
                    # Remove author part
                    if citation['authors']:
                        title_part = title_part.replace(citation['authors'][0], '').strip(' .,')
                    citation['title'] = title_part[:100]  # Limit length
        
        return citation
    
    def extract_in_text_citations(self) -> List[Tuple[str, str]]:
        """Extract in-text citations and create citation relationships"""
        # Look for patterns like (Author, Year) or [1] or Author (Year)
        patterns = [
            r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?),?\s*(\d{4})\)',  # (Smith, 2020)
            r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?)\s+(\d{4})\)',    # (Smith 2020)
            r'\[(\d+)\]',  # [1]
            r'([A-Z][a-z]+(?:\s+et\s+al\.)?)\s+\((\d{4})\)'  # Smith (2020)
        ]
        
        relationships = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, self.text)
            for match in matches:
                if len(match.groups()) == 2:
                    author, year = match.groups()
                    # Find matching citation in references
                    for citation in self.citations:
                        if (citation['year'] == int(year) and 
                            citation['authors'] and 
                            author.lower() in citation['authors'][0].lower()):
                            relationships.append(("main_paper", citation['id']))
                            break
                elif len(match.groups()) == 1:
                    # Numbered citation
                    num = match.groups()[0]
                    try:
                        idx = int(num) - 1
                        if 0 <= idx < len(self.citations):
                            relationships.append(("main_paper", self.citations[idx]['id']))
                    except ValueError:
                        continue
        
        return relationships
    
    def create_nodes_table(self) -> pd.DataFrame:
        """Create nodes table for network analysis"""
        nodes_data = []
        
        # Add the main paper as a node
        nodes_data.append({
            'id': 'main_paper',
            'label': 'Excited Delirium (Main Paper)',
            'type': 'main',
            'year': None,
            'authors': '',
            'title': 'Excited Delirium Analysis',
            'citation_count': len(self.citations)
        })
        
        # Add each citation as a node
        for citation in self.citations:
            nodes_data.append({
                'id': citation['id'],
                'label': citation['title'][:50] + '...' if len(citation['title']) > 50 else citation['title'],
                'type': 'citation',
                'year': citation['year'],
                'authors': ', '.join(citation['authors']),
                'title': citation['title'],
                'citation_count': 1  # Could be enhanced with actual citation counts
            })
        
        self.nodes = pd.DataFrame(nodes_data)
        return self.nodes
    
    def create_edges_table(self) -> pd.DataFrame:
        """Create edges table for network analysis"""
        relationships = self.extract_in_text_citations()
        
        edges_data = []
        for source, target in relationships:
            edges_data.append({
                'source': source,
                'target': target,
                'weight': 1,
                'type': 'citation'
            })
        
        self.edges = pd.DataFrame(edges_data)
        return self.edges
    
    def save_to_csv(self, nodes_file: str = "citation_nodes.csv", 
                    edges_file: str = "citation_edges.csv"):
        """Save nodes and edges tables to CSV files"""
        if not self.nodes.empty:
            self.nodes.to_csv(nodes_file, index=False)
            print(f"Nodes saved to {nodes_file}")
        
        if not self.edges.empty:
            self.edges.to_csv(edges_file, index=False)
            print(f"Edges saved to {edges_file}")
    
    def generate_report(self) -> str:
        """Generate a summary report of the citation extraction"""
        report = f"""
Citation Network Extraction Report
==================================

PDF File: {self.pdf_path}
Total Citations Found: {len(self.citations)}
Total Nodes: {len(self.nodes)}
Total Edges: {len(self.edges)}

Citation Breakdown by Year:
"""
        if self.citations:
            year_counts = {}
            for citation in self.citations:
                year = citation.get('year', 'Unknown')
                year_counts[year] = year_counts.get(year, 0) + 1
            
            for year, count in sorted(year_counts.items()):
                report += f"  {year}: {count} citations\n"
        
        return report


def main():
    """Main function to run the citation extractor"""
    pdf_path = "/Users/proctorf/Documents/GitHub/AIH/Eleanor/excited_delirium.pdf"
    
    # Create extractor
    extractor = CitationExtractor(pdf_path)
    
    # Extract text
    print("Extracting text from PDF...")
    text = extractor.extract_text_from_pdf()
    if not text:
        print("Failed to extract text from PDF")
        return
    
    # Parse citations
    print("Parsing citations...")
    citations = extractor.parse_citations()
    print(f"Found {len(citations)} citations")
    
    # Create network tables
    print("Creating network tables...")
    nodes = extractor.create_nodes_table()
    edges = extractor.create_edges_table()
    
    # Save results
    extractor.save_to_csv()
    
    # Generate report
    print("\n" + extractor.generate_report())
    
    # Display sample data
    print("\nSample Nodes:")
    print(nodes.head())
    print("\nSample Edges:")
    print(edges.head())


if __name__ == "__main__":
    main()