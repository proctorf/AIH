#!/usr/bin/env python3
"""
Simple Citation Network Visualizer
Creates a basic visualization of the citation network from the edges and nodes files
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

def load_network_data():
    """Load the edges and nodes CSV files"""
    try:
        edges_df = pd.read_csv('citation_edges.csv')
        nodes_df = pd.read_csv('citation_nodes.csv')
        return edges_df, nodes_df
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure you've run create_citation_edges.py first")
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
                'title': node['title']
            })
    
    return G

def visualize_network(G, save_file='citation_network.png'):
    """Create and save network visualization"""
    plt.figure(figsize=(16, 12))
    
    # Separate nodes by type
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    # Create layout - put main paper in center
    pos = {}
    
    # Center the main paper
    if main_nodes:
        pos[main_nodes[0]] = (0, 0)
    
    # Arrange cited papers in a circle around the main paper
    import numpy as np
    if cited_nodes:
        angles = np.linspace(0, 2*np.pi, len(cited_nodes), endpoint=False)
        radius = 3
        for i, node in enumerate(cited_nodes):
            pos[node] = (radius * np.cos(angles[i]), radius * np.sin(angles[i]))
    
    # Draw the network
    # Main paper (larger, red)
    if main_nodes:
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=main_nodes,
                              node_color='red',
                              node_size=2000,
                              alpha=0.9)
    
    # Cited papers (smaller, blue)
    if cited_nodes:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=cited_nodes,
                              node_color='lightblue',
                              node_size=300,
                              alpha=0.7)
    
    # Draw edges (arrows pointing from main to cited papers)
    nx.draw_networkx_edges(G, pos,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=20,
                          arrowstyle='->',
                          width=1,
                          alpha=0.6)
    
    # Add labels for main paper and some key citations
    labels = {}
    if main_nodes:
        labels[main_nodes[0]] = 'Excited\nDelirium\n(Main)'
    
    # Add labels for a few cited papers (to avoid clutter)
    for node in cited_nodes[:10]:  # Only first 10 to avoid overcrowding
        if 'author' in G.nodes[node] and 'year' in G.nodes[node]:
            author = G.nodes[node]['author'].split()[0] if G.nodes[node]['author'] else 'Unknown'
            year = G.nodes[node]['year']
            labels[node] = f"{author}\n({year})"
    
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
    
    plt.title("Citation Network: Excited Delirium Literature\n51 Citations", 
              fontsize=16, fontweight='bold', pad=20)
    
    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Main Article'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=10, label='Cited Articles'),
        Line2D([0], [0], color='gray', linewidth=2, label='Citation Link')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Network visualization saved as '{save_file}'")
    
    # Show basic statistics
    print(f"\nNetwork Statistics:")
    print(f"Total nodes: {len(G.nodes())}")
    print(f"Total edges: {len(G.edges())}")
    print(f"Network density: {nx.density(G):.4f}")
    
    return G

def analyze_citations_by_year(nodes_df):
    """Analyze citation patterns by publication year"""
    cited_papers = nodes_df[nodes_df['type'] == 'cited_paper'].copy()
    
    # Convert year to numeric, handle 'Unknown'
    cited_papers['year_num'] = pd.to_numeric(cited_papers['year'], errors='coerce')
    
    # Plot citations by year
    plt.figure(figsize=(12, 6))
    year_counts = cited_papers['year_num'].value_counts().sort_index()
    
    plt.bar(year_counts.index, year_counts.values, alpha=0.7, color='skyblue')
    plt.title('Citations by Publication Year', fontsize=14, fontweight='bold')
    plt.xlabel('Year')
    plt.ylabel('Number of Citations')
    plt.grid(axis='y', alpha=0.3)
    
    # Add trend line
    z = np.polyfit(year_counts.index, year_counts.values, 1)
    p = np.poly1d(z)
    plt.plot(year_counts.index, p(year_counts.index), "r--", alpha=0.8, linewidth=2)
    
    plt.tight_layout()
    plt.savefig('citations_by_year.png', dpi=300, bbox_inches='tight')
    print("Year analysis saved as 'citations_by_year.png'")

def main():
    """Main function"""
    print("Loading citation network data...")
    edges_df, nodes_df = load_network_data()
    
    if edges_df is None or nodes_df is None:
        return
    
    print("Creating network graph...")
    G = create_network_graph(edges_df, nodes_df)
    
    print("Creating visualization...")
    visualize_network(G)
    
    print("Analyzing citations by year...")
    analyze_citations_by_year(nodes_df)
    
    print("\nCitation Network Analysis Complete!")
    print("Files created:")
    print("- citation_network.png (network visualization)")
    print("- citations_by_year.png (temporal analysis)")

if __name__ == "__main__":
    # Install required packages if needed
    try:
        import numpy as np
        main()
    except ImportError:
        print("NumPy is required for this visualization.")
        print("Install it with: pip3 install numpy")
