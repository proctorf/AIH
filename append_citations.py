#!/usr/bin/env python3
"""
Append Citations from Additional PDF
Extracts citations from sudden_death.pdf and appends to existing network files
"""

import PyPDF2
import re
import pandas as pd
from collections import Counter
from typing import Dict, List, Tuple
import os

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

def extract_citation_id(citation: str) -> str:
    """Extract a unique identifier from a citation"""
    # Try to extract first author's last name and year
    
    # Pattern 1: "LastName [FirstInitial], ... Year"
    pattern1 = r'^([A-Z][a-z]+)\s+[A-Z]{1,3}[,.].*?(\d{4})'
    match1 = re.search(pattern1, citation)
    
    if match1:
        author = match1.group(1)
        year = match1.group(2)
        return f"{author}_{year}"
    
    # Pattern 2: "LastName, FirstName... Year"
    pattern2 = r'^([A-Z][a-z]+),.*?(\d{4})'
    match2 = re.search(pattern2, citation)
    
    if match2:
        author = match2.group(1)
        year = match2.group(2)
        return f"{author}_{year}"
    
    # Fallback: use first word and any year found
    words = citation.split()
    first_word = words[0] if words else "Unknown"
    year_match = re.search(r'\d{4}', citation)
    year = year_match.group() if year_match else "Unknown"
    
    return f"{first_word}_{year}"

def extract_author_names(citation: str) -> str:
    """Extract primary author name from citation"""
    # Try to get the first author's full name
    
    # Pattern: "LastName FirstInitials"
    pattern1 = r'^([A-Z][a-z]+\s+[A-Z]{1,3})'
    match1 = re.search(pattern1, citation)
    
    if match1:
        return match1.group(1).strip()
    
    # Pattern: "LastName, FirstName"
    pattern2 = r'^([A-Z][a-z]+),\s*([A-Z][a-z]*)'
    match2 = re.search(pattern2, citation)
    
    if match2:
        return f"{match2.group(1)}, {match2.group(2)}"
    
    # Fallback: first word
    words = citation.split()
    return words[0] if words else "Unknown"

def extract_year(citation: str) -> str:
    """Extract publication year from citation"""
    year_match = re.search(r'\b(19|20)\d{2}\b', citation)
    return year_match.group() if year_match else "Unknown"

def extract_title(citation: str) -> str:
    """Extract article title from citation"""
    # Remove author part (everything before first period or comma-space-year)
    after_author = re.sub(r'^[^.]*?\.\s*', '', citation)
    
    # Try to find title (usually ends with period before journal name)
    title_match = re.search(r'^([^.]+)', after_author)
    
    if title_match:
        title = title_match.group(1).strip()
        # Remove year if it appears at the start of title
        title = re.sub(r'^\d{4}[a-z]?\.\s*', '', title)
        return title[:100] + "..." if len(title) > 100 else title
    
    return "Title not parsed"

def load_existing_network_files():
    """Load existing nodes and edges files"""
    nodes_df = pd.DataFrame()
    edges_df = pd.DataFrame()
    
    if os.path.exists('citation_nodes.csv'):
        nodes_df = pd.read_csv('citation_nodes.csv')
        print(f"Loaded existing nodes file with {len(nodes_df)} entries")
    
    if os.path.exists('citation_edges.csv'):
        edges_df = pd.read_csv('citation_edges.csv')
        print(f"Loaded existing edges file with {len(edges_df)} entries")
    
    return nodes_df, edges_df

def create_new_edges_and_nodes(citations: List[str], source_paper_id: str, source_paper_title: str):
    """Create new edges and nodes from citations"""
    
    new_edges_data = []
    new_nodes_data = []
    citation_counter = Counter()
    
    # Process each citation
    for citation in citations:
        citation_id = extract_citation_id(citation)
        author = extract_author_names(citation)
        year = extract_year(citation)
        title = extract_title(citation)
        
        # Count occurrences of this citation
        citation_counter[citation_id] += 1
        
        # Create edge data
        edge_data = {
            'source': source_paper_id,
            'target': citation_id,
            'source_title': source_paper_title,
            'target_title': title,
            'target_author': author,
            'target_year': year,
            'weight': 1,  # Will be updated below
            'edge_type': 'citation',
            'full_citation': citation
        }
        
        new_edges_data.append(edge_data)
    
    # Create DataFrame for new edges
    new_edges_df = pd.DataFrame(new_edges_data)
    
    # Update weights based on citation frequency
    for idx, row in new_edges_df.iterrows():
        new_edges_df.at[idx, 'weight'] = citation_counter[row['target']]
    
    # Remove duplicate edges (keeping the one with weight)
    new_edges_df = new_edges_df.drop_duplicates(subset=['source', 'target'], keep='first')
    
    # Create new source paper node
    source_node = {
        'id': source_paper_id,
        'label': source_paper_title,
        'title': source_paper_title,
        'author': 'Unknown',  # Would need to extract from PDF
        'year': 'Unknown',
        'type': 'main_paper',
        'in_degree': 0,
        'out_degree': len(new_edges_df),
        'citation_count': len(new_edges_df)
    }
    new_nodes_data.append(source_node)
    
    # Create citation nodes
    for _, row in new_edges_df.iterrows():
        node = {
            'id': row['target'],
            'label': f"{row['target_author']} ({row['target_year']})",
            'title': row['target_title'],
            'author': row['target_author'],
            'year': row['target_year'],
            'type': 'cited_paper',
            'in_degree': row['weight'],
            'out_degree': 0,
            'citation_count': row['weight']
        }
        new_nodes_data.append(node)
    
    new_nodes_df = pd.DataFrame(new_nodes_data)
    
    return new_edges_df, new_nodes_df

def merge_network_data(existing_nodes_df, existing_edges_df, new_nodes_df, new_edges_df):
    """Merge new data with existing network data"""
    
    # Merge edges - simply append since they come from different source papers
    if len(existing_edges_df) > 0:
        merged_edges_df = pd.concat([existing_edges_df, new_edges_df], ignore_index=True)
    else:
        merged_edges_df = new_edges_df.copy()
    
    # Merge nodes - need to handle duplicates for cited papers
    if len(existing_nodes_df) > 0:
        # Find overlapping citation nodes
        existing_citation_ids = set(existing_nodes_df[existing_nodes_df['type'] == 'cited_paper']['id'])
        new_citation_ids = set(new_nodes_df[new_nodes_df['type'] == 'cited_paper']['id'])
        overlapping_ids = existing_citation_ids.intersection(new_citation_ids)
        
        print(f"Found {len(overlapping_ids)} overlapping citations:")
        for cit_id in overlapping_ids:
            print(f"  - {cit_id}")
        
        # For overlapping citations, update the in_degree (they're cited by both papers now)
        merged_nodes_df = existing_nodes_df.copy()
        
        for _, new_node in new_nodes_df.iterrows():
            if new_node['type'] == 'main_paper':
                # Add new main paper
                merged_nodes_df = pd.concat([merged_nodes_df, new_node.to_frame().T], ignore_index=True)
            elif new_node['id'] in overlapping_ids:
                # Update existing citation node
                idx = merged_nodes_df[merged_nodes_df['id'] == new_node['id']].index[0]
                merged_nodes_df.at[idx, 'in_degree'] += new_node['in_degree']
                merged_nodes_df.at[idx, 'citation_count'] += new_node['citation_count']
            else:
                # Add new citation node
                merged_nodes_df = pd.concat([merged_nodes_df, new_node.to_frame().T], ignore_index=True)
    else:
        merged_nodes_df = new_nodes_df.copy()
    
    return merged_nodes_df, merged_edges_df

def main():
    """Main function to extract citations and append to existing network"""
    
    pdf_path = "/Users/proctorf/Documents/GitHub/AIH/Eleanor/restraint.pdf"
    source_paper_id = "restraint_main"
    source_paper_title = "Restraint (Main Article)"
    
    print(f"Extracting citations from {pdf_path}...")
    
    # Extract text and citations
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("Could not extract text from PDF")
        return
    
    print(f"Extracted {len(text)} characters of text")
    
    references_section = find_references_section(text)
    print(f"Found references section with {len(references_section)} characters")
    
    citations = extract_citations(references_section)
    print(f"Found {len(citations)} new citations")
    
    # Load existing network data
    print("\nLoading existing network data...")
    existing_nodes_df, existing_edges_df = load_existing_network_files()
    
    # Create new network data
    print("Creating new edges and nodes...")
    new_edges_df, new_nodes_df = create_new_edges_and_nodes(citations, source_paper_id, source_paper_title)
    
    # Merge with existing data
    print("Merging with existing network data...")
    merged_nodes_df, merged_edges_df = merge_network_data(existing_nodes_df, existing_edges_df, 
                                                         new_nodes_df, new_edges_df)
    
    # Save updated files
    merged_edges_df.to_csv('citation_edges.csv', index=False)
    merged_nodes_df.to_csv('citation_nodes.csv', index=False)
    
    # Also save the new citations separately for reference
    with open("restraint_citations.txt", "w", encoding="utf-8") as f:
        f.write("Citations extracted from restraint.pdf\n")
        f.write("=" * 50 + "\n\n")
        for i, citation in enumerate(citations, 1):
            f.write(f"{i:2d}. {citation}\n\n")
    
    # Print summary
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"New citations extracted: {len(citations)}")
    print(f"Total edges after merge: {len(merged_edges_df)}")
    print(f"Total nodes after merge: {len(merged_nodes_df)}")
    
    # Count main papers and cited papers
    main_papers = len(merged_nodes_df[merged_nodes_df['type'] == 'main_paper'])
    cited_papers = len(merged_nodes_df[merged_nodes_df['type'] == 'cited_paper'])
    print(f"Main papers: {main_papers}")
    print(f"Cited papers: {cited_papers}")
    
    print(f"\nFiles updated:")
    print(f"- citation_edges.csv")
    print(f"- citation_nodes.csv")
    print(f"- restraint_citations.txt (new citations only)")

if __name__ == "__main__":
    main()