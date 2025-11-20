#!/usr/bin/env python3
"""
Force-Directed Citation Network Visualization
Creates an interactive and static force-directed graph of the complete citation network
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

def load_network_data():
    """Load the edges and nodes CSV files"""
    try:
        edges_df = pd.read_csv('citation_edges.csv')
        nodes_df = pd.read_csv('citation_nodes.csv')
        return edges_df, nodes_df
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None

def create_network_graph(edges_df, nodes_df):
    """Create NetworkX graph from the data"""
    # Create directed graph
    G = nx.from_pandas_edgelist(edges_df, 
                               source='source', 
                               target='target',
                               edge_attr=['weight'],
                               create_using=nx.DiGraph())
    
    # Add node attributes
    for _, node in nodes_df.iterrows():
        if node['id'] in G.nodes():
            G.nodes[node['id']].update({
                'label': node['label'],
                'type': node['type'],
                'author': node['author'],
                'year': node['year'],
                'title': node['title'],
                'in_degree': node['in_degree'],
                'citation_count': node['citation_count']
            })
    
    return G

def create_force_directed_visualization(G, save_file='force_directed_citation_network.png'):
    """Create force-directed layout visualization"""
    plt.figure(figsize=(20, 16))
    
    # Separate nodes by type and citation frequency
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    # Categorize cited nodes by how many times they're cited
    highly_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) >= 3]
    moderately_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 2]
    single_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 1]
    
    print(f"Network Composition:")
    print(f"  Main papers: {len(main_nodes)}")
    print(f"  Highly cited (3+): {len(highly_cited)}")
    print(f"  Moderately cited (2): {len(moderately_cited)}")
    print(f"  Single cited (1): {len(single_cited)}")
    
    # Use spring layout with custom parameters for force-directed positioning
    print("Computing force-directed layout...")
    pos = nx.spring_layout(G, 
                          k=3,           # Optimal distance between nodes
                          iterations=100, # More iterations for better layout
                          seed=42)       # Reproducible layout
    
    # Node sizes based on citation count and type
    node_sizes = {}
    for node in G.nodes():
        if G.nodes[node].get('type') == 'main_paper':
            node_sizes[node] = 3000  # Large for main papers
        elif node in highly_cited:
            node_sizes[node] = 800   # Large for highly cited
        elif node in moderately_cited:
            node_sizes[node] = 500   # Medium for moderately cited
        else:
            node_sizes[node] = 200   # Small for single cited
    
    # Draw nodes with different colors and sizes
    if main_nodes:
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=main_nodes,
                              node_color='red',
                              node_size=[node_sizes[n] for n in main_nodes],
                              alpha=0.9,
                              edgecolors='darkred',
                              linewidths=2)
    
    if highly_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=highly_cited,
                              node_color='orange',
                              node_size=[node_sizes[n] for n in highly_cited],
                              alpha=0.8,
                              edgecolors='darkorange',
                              linewidths=1.5)
    
    if moderately_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=moderately_cited,
                              node_color='gold',
                              node_size=[node_sizes[n] for n in moderately_cited],
                              alpha=0.7,
                              edgecolors='goldenrod',
                              linewidths=1)
    
    if single_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=single_cited,
                              node_color='lightblue',
                              node_size=[node_sizes[n] for n in single_cited],
                              alpha=0.6,
                              edgecolors='steelblue',
                              linewidths=0.5)
    
    # Draw edges with varying thickness and transparency
    edges = G.edges()
    weights = [G[u][v].get('weight', 1) for u, v in edges]
    max_weight = max(weights) if weights else 1
    
    # Different edge styles for different connection types
    edge_widths = [max(0.3, w/max_weight * 2) for w in weights]
    
    nx.draw_networkx_edges(G, pos,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=12,
                          arrowstyle='->',
                          width=edge_widths,
                          alpha=0.4,
                          connectionstyle="arc3,rad=0.05")  # Slight curve for better visibility
    
    # Add selective labels to avoid overcrowding
    labels = {}
    
    # Always label main papers
    for node in main_nodes:
        if 'excited_delirium' in node:
            labels[node] = 'Excited\nDelirium'
        elif 'sudden_death' in node:
            labels[node] = 'Sudden\nDeath'
        elif 'restraint' in node:
            labels[node] = 'Restraint'
        else:
            labels[node] = 'Main\nPaper'
    
    # Label highly cited papers
    for node in highly_cited:
        if 'author' in G.nodes[node]:
            author = G.nodes[node]['author'].split()[0] if G.nodes[node]['author'] else 'Unknown'
            year = G.nodes[node].get('year', 'Unknown')
            count = G.nodes[node].get('in_degree', 1)
            labels[node] = f"{author}\n({year})\n[{count}]"
    
    # Label some moderately cited papers (top 10 by year to show temporal spread)
    if moderately_cited:
        mod_cited_with_years = [(n, G.nodes[n].get('year', '0')) for n in moderately_cited]
        # Sort by year and take a sample
        mod_cited_sorted = sorted(mod_cited_with_years, key=lambda x: x[1])
        sample_size = min(10, len(mod_cited_sorted))
        for node, year in mod_cited_sorted[:sample_size]:
            if 'author' in G.nodes[node]:
                author = G.nodes[node]['author'].split()[0] if G.nodes[node]['author'] else 'Unknown'
                count = G.nodes[node].get('in_degree', 1)
                labels[node] = f"{author}\n({year})"
    
    # Draw labels with better positioning
    nx.draw_networkx_labels(G, pos, labels, 
                           font_size=8, 
                           font_weight='bold',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    
    plt.title("Force-Directed Citation Network: Complete Literature Map\n" + 
              f"3 Main Papers • {len(cited_nodes)} Cited Papers • {len(G.edges())} Citation Links", 
              fontsize=18, fontweight='bold', pad=30)
    
    # Create comprehensive legend
    legend_elements = [
        mpatches.Patch(color='red', label=f'Main Papers ({len(main_nodes)})'),
        mpatches.Patch(color='orange', label=f'Highly Cited - 3+ papers ({len(highly_cited)})'),
        mpatches.Patch(color='gold', label=f'Moderately Cited - 2 papers ({len(moderately_cited)})'),
        mpatches.Patch(color='lightblue', label=f'Single Citations ({len(single_cited)})'),
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
               fontsize=12, title="Node Types", title_fontsize=14)
    
    # Add comprehensive statistics box
    stats_text = f"""Network Statistics
━━━━━━━━━━━━━━━━━━━━━
Total Nodes: {len(G.nodes())}
Total Edges: {len(G.edges())}
Network Density: {nx.density(G):.4f}

Papers by Citation Count:
• 3+ citations: {len(highly_cited)}
• 2 citations: {len(moderately_cited)}  
• 1 citation: {len(single_cited)}

Main Papers:
• Excited Delirium
• Sudden Death  
• Restraint"""
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9),
             fontsize=11, verticalalignment='top', fontfamily='monospace')
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Force-directed visualization saved as '{save_file}'")
    
    return G

def analyze_network_properties(G, nodes_df):
    """Analyze key network properties"""
    print(f"\n{'='*60}")
    print("DETAILED NETWORK ANALYSIS")
    print('='*60)
    
    # Basic metrics
    print(f"Nodes: {len(G.nodes())}")
    print(f"Edges: {len(G.edges())}")
    print(f"Density: {nx.density(G):.4f}")
    print(f"Is Connected: {nx.is_weakly_connected(G)}")
    
    # Citation analysis
    cited_papers = nodes_df[nodes_df['type'] == 'cited_paper'].copy()
    citation_counts = cited_papers['in_degree'].value_counts().sort_index(ascending=False)
    
    print(f"\nCitation Distribution:")
    for count, freq in citation_counts.items():
        print(f"  {count} citations: {freq} papers")
    
    # Most cited papers
    top_cited = cited_papers.nlargest(10, 'in_degree')
    print(f"\nTop 10 Most Cited Papers:")
    for i, (_, paper) in enumerate(top_cited.iterrows(), 1):
        author = paper['author'].split()[0] if paper['author'] else 'Unknown'
        print(f"{i:2d}. {author} ({paper['year']}): {paper['in_degree']} citations")
        print(f"    {paper['title'][:70]}{'...' if len(paper['title']) > 70 else ''}")
    
    # Temporal analysis
    cited_papers['year_num'] = pd.to_numeric(cited_papers['year'], errors='coerce')
    year_range = cited_papers['year_num'].dropna()
    if len(year_range) > 0:
        print(f"\nTemporal Span:")
        print(f"  Earliest: {int(year_range.min())}")
        print(f"  Latest: {int(year_range.max())}")
        print(f"  Range: {int(year_range.max() - year_range.min())} years")
    
    return citation_counts, top_cited

def main():
    """Main function"""
    print("Loading complete citation network data...")
    edges_df, nodes_df = load_network_data()
    
    if edges_df is None or nodes_df is None:
        return
    
    print("Creating network graph...")
    G = create_network_graph(edges_df, nodes_df)
    
    print("Creating force-directed visualization...")
    G = create_force_directed_visualization(G)
    
    print("Analyzing network properties...")
    citation_counts, top_cited = analyze_network_properties(G, nodes_df)
    
    print(f"\n{'='*60}")
    print("VISUALIZATION COMPLETE")
    print('='*60)
    print("File created: force_directed_citation_network.png")
    print("This shows the complete literature network with force-directed positioning")
    print("revealing natural clustering and relationships between papers.")

if __name__ == "__main__":
    main()