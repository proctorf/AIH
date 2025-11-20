#!/usr/bin/env python3
"""
Citation Network Edges Creator
Creates a directed edges file connecting citations to the main citing article
Uses weight to measure citation frequency
"""

import pandas as pd
import re
from collections import Counter
from typing import Dict, List, Tuple

def parse_citations_file(file_path: str) -> List[str]:
    """Read and parse the extracted citations file"""
    citations = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by numbered citations (e.g., " 1. ", " 2. ", etc.)
    citation_pattern = r'\s+\d+\.\s+(.*?)(?=\n\s+\d+\.\s+|\Z)'
    matches = re.findall(citation_pattern, content, re.DOTALL)
    
    for match in matches:
        # Clean up the citation text
        clean_citation = ' '.join(match.split())
        if len(clean_citation) > 20:  # Filter out very short matches
            citations.append(clean_citation)
    
    return citations

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
    # Look for text after author and before journal/year
    # This is a simplified approach - titles often appear between periods
    
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

def create_edges_table(citations: List[str]) -> pd.DataFrame:
    """Create edges table from citations list"""
    
    main_paper_id = "excited_delirium_main"
    main_paper_title = "Excited Delirium (Main Article)"
    
    edges_data = []
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
            'source': main_paper_id,
            'target': citation_id,
            'source_title': main_paper_title,
            'target_title': title,
            'target_author': author,
            'target_year': year,
            'weight': 1,  # Will be updated below
            'edge_type': 'citation',
            'full_citation': citation
        }
        
        edges_data.append(edge_data)
    
    # Create DataFrame
    edges_df = pd.DataFrame(edges_data)
    
    # Update weights based on citation frequency
    for idx, row in edges_df.iterrows():
        edges_df.at[idx, 'weight'] = citation_counter[row['target']]
    
    # Remove duplicate edges (keeping the one with weight)
    edges_df = edges_df.drop_duplicates(subset=['source', 'target'], keep='first')
    
    # Sort by weight (most cited first)
    edges_df = edges_df.sort_values('weight', ascending=False)
    
    return edges_df

def create_nodes_table(edges_df: pd.DataFrame) -> pd.DataFrame:
    """Create nodes table from edges data"""
    
    nodes_data = []
    
    # Add main paper node
    main_node = {
        'id': 'excited_delirium_main',
        'label': 'Excited Delirium (Main)',
        'title': 'Excited Delirium: Main Article',
        'author': 'Takeuchi et al.',
        'year': 'Unknown',
        'type': 'main_paper',
        'in_degree': 0,  # Main paper doesn't cite others in this network
        'out_degree': len(edges_df),  # Number of citations it makes
        'citation_count': len(edges_df)
    }
    nodes_data.append(main_node)
    
    # Add citation nodes
    for _, row in edges_df.iterrows():
        node = {
            'id': row['target'],
            'label': f"{row['target_author']} ({row['target_year']})",
            'title': row['target_title'],
            'author': row['target_author'],
            'year': row['target_year'],
            'type': 'cited_paper',
            'in_degree': row['weight'],  # How many times it's cited
            'out_degree': 0,  # We don't have data on what these papers cite
            'citation_count': row['weight']
        }
        nodes_data.append(node)
    
    return pd.DataFrame(nodes_data)

def main():
    """Main function to create edges and nodes tables"""
    
    citations_file = "extracted_citations.txt"
    
    print("Reading citations from file...")
    citations = parse_citations_file(citations_file)
    print(f"Found {len(citations)} citations")
    
    print("\nCreating edges table...")
    edges_df = create_edges_table(citations)
    print(f"Created {len(edges_df)} edges")
    
    print("\nCreating nodes table...")
    nodes_df = create_nodes_table(edges_df)
    print(f"Created {len(nodes_df)} nodes")
    
    # Save to CSV files
    edges_filename = "citation_edges.csv"
    nodes_filename = "citation_nodes.csv"
    
    edges_df.to_csv(edges_filename, index=False)
    nodes_df.to_csv(nodes_filename, index=False)
    
    print(f"\nFiles saved:")
    print(f"- {edges_filename}")
    print(f"- {nodes_filename}")
    
    # Display summary statistics
    print(f"\nEdges Summary:")
    print(f"Total edges: {len(edges_df)}")
    print(f"Unique citations: {len(edges_df)}")
    print(f"Weight range: {edges_df['weight'].min()} - {edges_df['weight'].max()}")
    print(f"Most cited papers:")
    top_cited = edges_df.nlargest(5, 'weight')[['target_author', 'target_year', 'weight']]
    for _, row in top_cited.iterrows():
        print(f"  {row['target_author']} ({row['target_year']}): {row['weight']} citations")
    
    print(f"\nNodes Summary:")
    print(f"Total nodes: {len(nodes_df)}")
    main_papers = len(nodes_df[nodes_df['type'] == 'main_paper'])
    cited_papers = len(nodes_df[nodes_df['type'] == 'cited_paper'])
    print(f"Main papers: {main_papers}")
    print(f"Cited papers: {cited_papers}")
    
    # Display sample of edges table
    print(f"\nSample Edges Table:")
    print(edges_df[['source', 'target', 'target_author', 'target_year', 'weight']].head(10).to_string(index=False))

if __name__ == "__main__":
    main()