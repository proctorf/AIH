#!/usr/bin/env python3
"""
Updated Citation Network Visualizer
Handles multiple main papers and updated network structure
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

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
                'in_degree': node['in_degree']
            })
    
    return G

def visualize_updated_network(G, save_file='updated_citation_network.png'):
    """Create and save updated network visualization"""
    plt.figure(figsize=(18, 14))
    
    # Separate nodes by type
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    # Get nodes cited by both papers (in_degree >= 2)
    highly_cited_nodes = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) >= 2]
    regular_cited_nodes = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) < 2]
    
    print(f"Main papers: {len(main_nodes)}")
    print(f"Highly cited papers (cited by multiple sources): {len(highly_cited_nodes)}")
    print(f"Regular cited papers: {len(regular_cited_nodes)}")
    
    # Create layout
    pos = {}
    
    # Position main papers
    if len(main_nodes) == 2:
        pos[main_nodes[0]] = (-2, 0)  # Left
        pos[main_nodes[1]] = (2, 0)   # Right
    elif len(main_nodes) == 1:
        pos[main_nodes[0]] = (0, 0)
    
    # Position highly cited papers (closer to center)
    if highly_cited_nodes:
        angles_high = np.linspace(0, 2*np.pi, len(highly_cited_nodes), endpoint=False)
        radius_high = 2.5
        for i, node in enumerate(highly_cited_nodes):
            pos[node] = (radius_high * np.cos(angles_high[i]), radius_high * np.sin(angles_high[i]))
    
    # Position regular cited papers (outer circle)
    if regular_cited_nodes:
        angles_reg = np.linspace(0, 2*np.pi, len(regular_cited_nodes), endpoint=False)
        radius_reg = 4.5
        for i, node in enumerate(regular_cited_nodes):
            pos[node] = (radius_reg * np.cos(angles_reg[i]), radius_reg * np.sin(angles_reg[i]))
    
    # Draw the network
    # Main papers (larger, red)
    if main_nodes:
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=main_nodes,
                              node_color='red',
                              node_size=2500,
                              alpha=0.9)
    
    # Highly cited papers (medium, orange)
    if highly_cited_nodes:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=highly_cited_nodes,
                              node_color='orange',
                              node_size=600,
                              alpha=0.8)
    
    # Regular cited papers (smaller, light blue)
    if regular_cited_nodes:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=regular_cited_nodes,
                              node_color='lightblue',
                              node_size=300,
                              alpha=0.7)
    
    # Draw edges with varying thickness based on weight
    edges = G.edges()
    weights = [G[u][v].get('weight', 1) for u, v in edges]
    max_weight = max(weights) if weights else 1
    
    nx.draw_networkx_edges(G, pos,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=15,
                          arrowstyle='->',
                          width=[w/max_weight * 2 for w in weights],
                          alpha=0.6)
    
    # Add labels
    labels = {}
    
    # Label main papers
    for node in main_nodes:
        if 'excited_delirium' in node:
            labels[node] = 'Excited\nDelirium'
        elif 'sudden_death' in node:
            labels[node] = 'Sudden\nDeath'
        else:
            labels[node] = 'Main\nPaper'
    
    # Label highly cited papers
    for node in highly_cited_nodes:
        if 'author' in G.nodes[node] and 'year' in G.nodes[node]:
            author = G.nodes[node]['author'].split()[0] if G.nodes[node]['author'] else 'Unknown'
            year = G.nodes[node]['year']
            count = G.nodes[node].get('in_degree', 1)
            labels[node] = f"{author}\n({year})\n[{count}]"
    
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold')
    
    plt.title("Updated Citation Network: Excited Delirium + Sudden Death Literature\n" + 
              f"{len(G.nodes())} nodes, {len(G.edges())} edges", 
              fontsize=16, fontweight='bold', pad=20)
    
    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Main Articles (2)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=12, label=f'Highly Cited ({len(highly_cited_nodes)})'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', markersize=8, label=f'Other Citations ({len(regular_cited_nodes)})'),
        Line2D([0], [0], color='gray', linewidth=2, label='Citation Links')
    ]
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    # Add text box with statistics
    stats_text = f"""Network Statistics:
• Total Nodes: {len(G.nodes())}
• Total Edges: {len(G.edges())}
• Main Papers: {len(main_nodes)}
• Cited Papers: {len(cited_nodes)}
• Overlapping Citations: {len(highly_cited_nodes)}
• Network Density: {nx.density(G):.4f}"""
    
    plt.text(0.02, 0.02, stats_text, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
             fontsize=10, verticalalignment='bottom')
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Updated network visualization saved as '{save_file}'")
    
    return G

def analyze_overlapping_citations(nodes_df):
    """Analyze citations that appear in multiple papers"""
    cited_papers = nodes_df[nodes_df['type'] == 'cited_paper'].copy()
    overlapping = cited_papers[cited_papers['in_degree'] >= 2].copy()
    
    if len(overlapping) > 0:
        print(f"\n=== OVERLAPPING CITATIONS ANALYSIS ===")
        print(f"Found {len(overlapping)} citations cited by multiple papers:")
        
        # Sort by citation count
        overlapping = overlapping.sort_values('in_degree', ascending=False)
        
        for _, citation in overlapping.iterrows():
            print(f"• {citation['author']} ({citation['year']}): cited {citation['in_degree']} times")
            print(f"  Title: {citation['title'][:60]}{'...' if len(citation['title']) > 60 else ''}")
            print()
        
        return overlapping
    else:
        print("No overlapping citations found.")
        return pd.DataFrame()

def main():
    """Main function"""
    print("Loading updated citation network data...")
    edges_df, nodes_df = load_network_data()
    
    if edges_df is None or nodes_df is None:
        return
    
    print("Creating network graph...")
    G = create_network_graph(edges_df, nodes_df)
    
    print("Creating updated visualization...")
    visualize_updated_network(G)
    
    print("Analyzing overlapping citations...")
    overlapping = analyze_overlapping_citations(nodes_df)
    
    print(f"\n=== NETWORK SUMMARY ===")
    main_papers = len(nodes_df[nodes_df['type'] == 'main_paper'])
    cited_papers = len(nodes_df[nodes_df['type'] == 'cited_paper'])
    total_citations = edges_df['weight'].sum()
    
    print(f"Main papers: {main_papers}")
    print(f"Unique cited papers: {cited_papers}")
    print(f"Total citation relationships: {len(edges_df)}")
    print(f"Overlapping citations: {len(overlapping)}")
    
    print("\nFiles created:")
    print("- updated_citation_network.png")

if __name__ == "__main__":
    main()