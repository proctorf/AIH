# Citation Network Analysis for Digital Humanities

This project automates the extraction of citation information from PDF academic papers to create citation networks for analysis.

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Citation Extractor**:
   ```bash
   python citation_network_extractor.py
   ```

3. **Output Files**:
   - `citation_nodes.csv`: Contains all the papers/citations as nodes
   - `citation_edges.csv`: Contains the citation relationships as edges

## What This Tool Does

### Automated Citation Extraction
- **PDF Text Extraction**: Extracts text from your PDF file
- **Reference Section Parsing**: Identifies and parses the bibliography/references section
- **In-Text Citation Matching**: Finds in-text citations and matches them to references
- **Structured Data Creation**: Converts citations into structured data with fields like:
  - Authors
  - Title
  - Year
  - Journal
  - DOI
  - Type

### Network Table Generation

#### Nodes Table (`citation_nodes.csv`)
Contains information about each paper in your network:
```csv
id,label,type,year,authors,title,citation_count
main_paper,Excited Delirium (Main Paper),main,2023,Smith et al,Analysis of Excited Delirium,25
cite_1,Forensic Pathology Review,citation,2020,Jones,Forensic Pathology in Context,1
cite_2,Medical Ethics Study,citation,2019,Brown,Ethics in Medical Practice,1
```

#### Edges Table (`citation_edges.csv`)
Contains the citation relationships:
```csv
source,target,weight,type
main_paper,cite_1,1,citation
main_paper,cite_2,1,citation
cite_1,cite_3,1,citation
```

## Next Steps for Citation Network Analysis

### 1. Network Visualization
```python
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# Load your data
nodes = pd.read_csv('citation_nodes.csv')
edges = pd.read_csv('citation_edges.csv')

# Create network
G = nx.from_pandas_edgelist(edges, source='source', target='target')

# Add node attributes
for _, row in nodes.iterrows():
    if row['id'] in G.nodes():
        G.nodes[row['id']]['year'] = row['year']
        G.nodes[row['id']]['title'] = row['title']

# Visualize
plt.figure(figsize=(12, 8))
nx.draw(G, with_labels=True, node_color='lightblue', 
        node_size=500, font_size=8, arrows=True)
plt.title("Citation Network")
plt.show()
```

### 2. Network Analysis Metrics
- **Centrality measures**: Which papers are most influential?
- **Clustering**: Are there research communities?
- **Temporal analysis**: How has the field evolved over time?

### 3. Advanced Features to Add
- **Cross-reference with external databases** (Google Scholar, PubMed)
- **Author disambiguation** 
- **Topic modeling** of citation content
- **Citation context analysis** (positive/negative citations)

## Limitations and Improvements

### Current Limitations
- PDF extraction can be imperfect with complex layouts
- Citation parsing is simplified (real citations are very complex)
- Limited to single PDF (could be extended to corpus)

### Possible Improvements
- Use more sophisticated PDF extraction (e.g., `pdfplumber`)
- Integrate with citation parsing libraries (e.g., `anystyle`, `cermine`)
- Add machine learning for better citation classification
- Connect to bibliographic APIs for metadata enrichment

## Integration with Digital Humanities Workflow

This tool fits perfectly into your DH curriculum:
- **Week 3-4**: Use Python to process text data (citations are text!)
- **Week 7**: Create network visualizations as a form of digital mapping
- **Week 9**: Apply network analysis to understand scholarly communities
- **Week 12**: Present citation networks as data storytelling

## Files in This Project
- `citation_network_extractor.py`: Main extraction script
- `requirements.txt`: Python dependencies
- `README.md`: This documentation
- `excited_delirium.pdf`: Source PDF (in Eleanor/ folder)
- `citation_nodes.csv`: Generated nodes table
- `citation_edges.csv`: Generated edges table