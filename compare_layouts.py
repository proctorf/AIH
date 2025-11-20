#!/usr/bin/env python3
"""
Compare Layout Methods: Constrained vs Unconstrained
Shows the difference between circular-constrained and pure physics layouts
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

def load_network_data():
    """Load the edges and nodes CSV files"""
    edges_df = pd.read_csv('citation_edges.csv')
    nodes_df = pd.read_csv('citation_nodes.csv')
    return edges_df, nodes_df

def create_network_graph(edges_df, nodes_df):
    """Create NetworkX graph from the data"""
    G = nx.from_pandas_edgelist(edges_df, 
                               source='source', 
                               target='target',
                               edge_attr=['weight'],
                               create_using=nx.DiGraph())
    
    for _, node in nodes_df.iterrows():
        if node['id'] in G.nodes():
            G.nodes[node['id']].update({
                'type': node['type'],
                'in_degree': node['in_degree'],
            })
    
    return G

def analyze_layout_properties(positions, title):
    """Analyze the properties of a layout"""
    print(f"\n{title} Layout Analysis:")
    print("-" * 40)
    
    # Convert positions to array for analysis
    pos_array = np.array(list(positions.values()))
    
    # Calculate spread and distribution
    x_coords = pos_array[:, 0]
    y_coords = pos_array[:, 1]
    
    print(f"X-coordinate range: {x_coords.min():.2f} to {x_coords.max():.2f}")
    print(f"Y-coordinate range: {y_coords.min():.2f} to {y_coords.max():.2f}")
    print(f"X-coordinate std dev: {x_coords.std():.2f}")
    print(f"Y-coordinate std dev: {y_coords.std():.2f}")
    
    # Calculate distances from center
    center = np.array([x_coords.mean(), y_coords.mean()])
    distances = [np.linalg.norm(pos - center) for pos in pos_array]
    
    print(f"Average distance from center: {np.mean(distances):.2f}")
    print(f"Distance std dev: {np.std(distances):.2f}")
    
    # Check for circular pattern (uniform distances suggest circularity)
    distance_uniformity = np.std(distances) / np.mean(distances)
    print(f"Distance uniformity ratio: {distance_uniformity:.3f}")
    print(f"  (Lower = more circular, Higher = more organic)")

def create_layout_comparison(G, save_file='layout_comparison.png'):
    """Create side-by-side comparison of layout methods"""
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # Categorize nodes for consistent coloring
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    highly_cited = [n for n in G.nodes() if G.nodes[n].get('in_degree', 1) >= 3]
    moderately_cited = [n for n in G.nodes() if G.nodes[n].get('in_degree', 1) == 2]
    single_cited = [n for n in G.nodes() if G.nodes[n].get('in_degree', 1) == 1]
    
    colors = {
        'main': '#E53E3E',
        'highly_cited': '#FF7A00',
        'moderately_cited': '#F6AD55',
        'single_cited': '#4299E1'
    }
    
    # Layout 1: Spring layout with circular tendency
    ax = axes[0, 0]
    plt.sca(ax)
    pos1 = nx.spring_layout(G, k=1, iterations=50, seed=42)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos1, nodelist=main_nodes, node_color=colors['main'], 
                          node_size=300, alpha=0.9, ax=ax)
    nx.draw_networkx_nodes(G, pos1, nodelist=highly_cited, node_color=colors['highly_cited'], 
                          node_size=200, alpha=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos1, nodelist=moderately_cited, node_color=colors['moderately_cited'], 
                          node_size=150, alpha=0.7, ax=ax)
    nx.draw_networkx_nodes(G, pos1, nodelist=single_cited, node_color=colors['single_cited'], 
                          node_size=100, alpha=0.6, ax=ax)
    
    nx.draw_networkx_edges(G, pos1, alpha=0.3, ax=ax, arrows=False, width=0.5)
    
    ax.set_title("Spring Layout (k=1, 50 iterations)\nTends toward circular arrangement", 
                fontsize=12, fontweight='bold')
    ax.set_aspect('equal')
    
    analyze_layout_properties(pos1, "Spring Layout (Constrained)")
    
    # Layout 2: Improved spring layout
    ax = axes[0, 1]
    plt.sca(ax)
    pos2 = nx.spring_layout(G, k=5, iterations=200, seed=42)
    
    nx.draw_networkx_nodes(G, pos2, nodelist=main_nodes, node_color=colors['main'], 
                          node_size=300, alpha=0.9, ax=ax)
    nx.draw_networkx_nodes(G, pos2, nodelist=highly_cited, node_color=colors['highly_cited'], 
                          node_size=200, alpha=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos2, nodelist=moderately_cited, node_color=colors['moderately_cited'], 
                          node_size=150, alpha=0.7, ax=ax)
    nx.draw_networkx_nodes(G, pos2, nodelist=single_cited, node_color=colors['single_cited'], 
                          node_size=100, alpha=0.6, ax=ax)
    
    nx.draw_networkx_edges(G, pos2, alpha=0.3, ax=ax, arrows=False, width=0.5)
    
    ax.set_title("Enhanced Spring Layout (k=5, 200 iterations)\nLess circular but still constrained", 
                fontsize=12, fontweight='bold')
    ax.set_aspect('equal')
    
    analyze_layout_properties(pos2, "Enhanced Spring Layout")
    
    # Layout 3: Random layout (for comparison)
    ax = axes[1, 0]
    plt.sca(ax)
    pos3 = {}
    np.random.seed(42)
    for node in G.nodes():
        pos3[node] = np.random.uniform(-1, 1, 2)
    
    nx.draw_networkx_nodes(G, pos3, nodelist=main_nodes, node_color=colors['main'], 
                          node_size=300, alpha=0.9, ax=ax)
    nx.draw_networkx_nodes(G, pos3, nodelist=highly_cited, node_color=colors['highly_cited'], 
                          node_size=200, alpha=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos3, nodelist=moderately_cited, node_color=colors['moderately_cited'], 
                          node_size=150, alpha=0.7, ax=ax)
    nx.draw_networkx_nodes(G, pos3, nodelist=single_cited, node_color=colors['single_cited'], 
                          node_size=100, alpha=0.6, ax=ax)
    
    nx.draw_networkx_edges(G, pos3, alpha=0.3, ax=ax, arrows=False, width=0.5)
    
    ax.set_title("Random Layout\nNo constraints, no forces", 
                fontsize=12, fontweight='bold')
    ax.set_aspect('equal')
    
    analyze_layout_properties(pos3, "Random Layout")
    
    # Layout 4: Pure physics simulation (simplified)
    ax = axes[1, 1]
    plt.sca(ax)
    
    # Simulate a few steps of pure physics for demonstration
    nodes = list(G.nodes())
    
    # Initialize random positions
    pos4 = {}
    np.random.seed(42)
    for node in nodes:
        pos4[node] = np.random.uniform(-5, 5, 2)
    
    # Simple physics simulation
    for iteration in range(100):
        forces = {node: np.array([0.0, 0.0]) for node in nodes}
        
        # Repulsion between all pairs
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                diff = pos4[node1] - pos4[node2]
                distance = np.linalg.norm(diff)
                if distance > 0:
                    force = (diff / distance) * (10.0 / (distance ** 2))
                    forces[node1] += force
                    forces[node2] -= force
        
        # Attraction for connected nodes
        for edge in G.edges():
            node1, node2 = edge
            diff = pos4[node2] - pos4[node1]
            distance = np.linalg.norm(diff)
            if distance > 0:
                force = diff * 0.01
                forces[node1] += force
                forces[node2] -= force
        
        # Update positions
        for node in nodes:
            pos4[node] += forces[node] * 0.1
    
    nx.draw_networkx_nodes(G, pos4, nodelist=main_nodes, node_color=colors['main'], 
                          node_size=300, alpha=0.9, ax=ax)
    nx.draw_networkx_nodes(G, pos4, nodelist=highly_cited, node_color=colors['highly_cited'], 
                          node_size=200, alpha=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos4, nodelist=moderately_cited, node_color=colors['moderately_cited'], 
                          node_size=150, alpha=0.7, ax=ax)
    nx.draw_networkx_nodes(G, pos4, nodelist=single_cited, node_color=colors['single_cited'], 
                          node_size=100, alpha=0.6, ax=ax)
    
    nx.draw_networkx_edges(G, pos4, alpha=0.3, ax=ax, arrows=False, width=0.5)
    
    ax.set_title("Pure Physics Simulation\nNo geometric constraints, natural forces", 
                fontsize=12, fontweight='bold')
    ax.set_aspect('equal')
    
    analyze_layout_properties(pos4, "Pure Physics Layout")
    
    # Remove axis ticks for cleaner look
    for ax in axes.flat:
        ax.set_xticks([])
        ax.set_yticks([])
    
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Layout comparison saved as '{save_file}'")

def main():
    """Main function"""
    print("Loading citation network data...")
    edges_df, nodes_df = load_network_data()
    
    print("Creating network graph...")
    G = create_network_graph(edges_df, nodes_df)
    
    print("Creating layout comparison...")
    create_layout_comparison(G)
    
    print(f"\n{'='*60}")
    print("LAYOUT COMPARISON ANALYSIS")
    print('='*60)
    print("This comparison shows how different layout algorithms")
    print("impose different constraints on node positioning:")
    print("")
    print("1. Spring Layout (constrained): Circular tendency")
    print("2. Enhanced Spring: Less circular but still geometric")  
    print("3. Random Layout: No forces, purely random")
    print("4. Pure Physics: Natural force-based positioning")
    print("")
    print("The pure physics approach allows truly organic")
    print("clustering patterns to emerge without geometric bias.")

if __name__ == "__main__":
    main()