#!/usr/bin/env python3
"""
Simple Citation Network Demo
Creates sample nodes and edges tables to demonstrate the concept
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

def create_sample_citation_network():
    """Create sample citation data to demonstrate network structure"""
    
    # Sample nodes (papers in the network)
    nodes_data = [
        {
            'id': 'main_paper',
            'label': 'Excited Delirium: A Medical Review',
            'type': 'main',
            'year': 2023,
            'authors': 'Johnson, M. et al.',
            'title': 'Excited Delirium: A Comprehensive Medical Review',
            'citation_count': 15
        },
        {
            'id': 'cite_1',
            'label': 'Forensic Pathology in Context',
            'type': 'citation',
            'year': 2020,
            'authors': 'Smith, J.',
            'title': 'Forensic Pathology in Context: Understanding Sudden Death',
            'citation_count': 45
        },
        {
            'id': 'cite_2',
            'label': 'Psychiatric Emergency Medicine',
            'type': 'citation',
            'year': 2019,
            'authors': 'Brown, K.',
            'title': 'Psychiatric Emergency Medicine: Current Practices',
            'citation_count': 32
        },
        {
            'id': 'cite_3',
            'label': 'Police Use of Force Studies',
            'type': 'citation',
            'year': 2021,
            'authors': 'Davis, L.',
            'title': 'Police Use of Force: A Statistical Analysis',
            'citation_count': 28
        },
        {
            'id': 'cite_4',
            'label': 'Drug-Induced Psychosis Research',
            'type': 'citation',
            'year': 2018,
            'authors': 'Wilson, R.',
            'title': 'Drug-Induced Psychosis: Clinical Manifestations',
            'citation_count': 55
        },
        {
            'id': 'cite_5',
            'label': 'Medical Ethics in Forensics',
            'type': 'citation',
            'year': 2022,
            'authors': 'Taylor, S.',
            'title': 'Medical Ethics in Forensic Investigations',
            'citation_count': 22
        }
    ]
    
    # Sample edges (citation relationships)
    edges_data = [
        {'source': 'main_paper', 'target': 'cite_1', 'weight': 3, 'type': 'citation'},
        {'source': 'main_paper', 'target': 'cite_2', 'weight': 2, 'type': 'citation'},
        {'source': 'main_paper', 'target': 'cite_3', 'weight': 1, 'type': 'citation'},
        {'source': 'main_paper', 'target': 'cite_4', 'weight': 4, 'type': 'citation'},
        {'source': 'main_paper', 'target': 'cite_5', 'weight': 1, 'type': 'citation'},
        {'source': 'cite_1', 'target': 'cite_4', 'weight': 1, 'type': 'citation'},
        {'source': 'cite_2', 'target': 'cite_4', 'weight': 2, 'type': 'citation'},
        {'source': 'cite_3', 'target': 'cite_1', 'weight': 1, 'type': 'citation'},
    ]
    
    return pd.DataFrame(nodes_data), pd.DataFrame(edges_data)

def visualize_network(nodes_df, edges_df, save_plot=True):
    """Create a network visualization"""
    
    # Create NetworkX graph
    G = nx.from_pandas_edgelist(edges_df, source='source', target='target', 
                               edge_attr='weight', create_using=nx.DiGraph())
    
    # Add node attributes
    for _, row in nodes_df.iterrows():
        if row['id'] in G.nodes():
            G.nodes[row['id']].update(row.to_dict())
    
    # Create visualization
    plt.figure(figsize=(14, 10))
    
    # Position nodes using spring layout
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Draw nodes with different colors for different types
    main_nodes = [node for node in G.nodes() if G.nodes[node].get('type') == 'main']
    citation_nodes = [node for node in G.nodes() if G.nodes[node].get('type') == 'citation']
    
    nx.draw_networkx_nodes(G, pos, nodelist=main_nodes, node_color='red', 
                          node_size=1000, alpha=0.8, label='Main Paper')
    nx.draw_networkx_nodes(G, pos, nodelist=citation_nodes, node_color='lightblue', 
                          node_size=500, alpha=0.8, label='Citations')
    
    # Draw edges with varying thickness based on weight
    edges = G.edges()
    weights = [G[u][v]['weight'] for u, v in edges]
    nx.draw_networkx_edges(G, pos, width=weights, alpha=0.6, 
                          edge_color='gray', arrows=True, arrowsize=20)
    
    # Add labels
    labels = {node: G.nodes[node].get('label', node)[:30] + '...' 
              if len(G.nodes[node].get('label', node)) > 30 
              else G.nodes[node].get('label', node) 
              for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
    
    plt.title("Citation Network: Excited Delirium Literature", fontsize=16, fontweight='bold')
    plt.legend()
    plt.axis('off')
    plt.tight_layout()
    
    if save_plot:
        plt.savefig('citation_network_visualization.png', dpi=300, bbox_inches='tight')
        print("Network visualization saved as 'citation_network_visualization.png'")
    
    plt.show()

def analyze_network(nodes_df, edges_df):
    """Perform basic network analysis"""
    
    G = nx.from_pandas_edgelist(edges_df, source='source', target='target', 
                               create_using=nx.DiGraph())
    
    print("Citation Network Analysis")
    print("=" * 40)
    print(f"Number of nodes (papers): {len(G.nodes())}")
    print(f"Number of edges (citations): {len(G.edges())}")
    print(f"Network density: {nx.density(G):.3f}")
    
    print("\nMost Cited Papers (by in-degree):")
    in_degrees = dict(G.in_degree())
    sorted_by_citations = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
    for node, degree in sorted_by_citations[:5]:
        title = nodes_df[nodes_df['id'] == node]['title'].iloc[0] if not nodes_df[nodes_df['id'] == node].empty else node
        print(f"  {title[:50]}... : {degree} citations")
    
    print("\nMost Citing Papers (by out-degree):")
    out_degrees = dict(G.out_degree())
    sorted_by_citing = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)
    for node, degree in sorted_by_citing[:5]:
        title = nodes_df[nodes_df['id'] == node]['title'].iloc[0] if not nodes_df[nodes_df['id'] == node].empty else node
        print(f"  {title[:50]}... : cites {degree} papers")

def main():
    """Run the citation network demo"""
    
    print("Creating sample citation network...")
    nodes_df, edges_df = create_sample_citation_network()
    
    # Save to CSV files
    nodes_df.to_csv('sample_citation_nodes.csv', index=False)
    edges_df.to_csv('sample_citation_edges.csv', index=False)
    print("Sample data saved to CSV files")
    
    # Display the data
    print("\nNodes Table:")
    print(nodes_df.to_string(index=False))
    
    print("\nEdges Table:")
    print(edges_df.to_string(index=False))
    
    # Analyze the network
    print("\n")
    analyze_network(nodes_df, edges_df)
    
    # Create visualization
    print("\nCreating network visualization...")
    visualize_network(nodes_df, edges_df)

if __name__ == "__main__":
    main()