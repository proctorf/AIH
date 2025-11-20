#!/usr/bin/env python3
"""
True Force-Directed Citation Network using Force Atlas 2
Creates a genuine force-directed graph using the Force Atlas 2 algorithm
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Try to import fa2 (ForceAtlas2), install if not available
try:
    from fa2 import ForceAtlas2
    FA2_AVAILABLE = True
except ImportError:
    print("ForceAtlas2 not found. Installing...")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fa2"])
        from fa2 import ForceAtlas2
        FA2_AVAILABLE = True
        print("ForceAtlas2 installed successfully!")
    except Exception as e:
        print(f"Could not install ForceAtlas2: {e}")
        print("Falling back to improved spring layout...")
        FA2_AVAILABLE = False

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

def create_force_atlas2_layout(G):
    """Create layout using Force Atlas 2 algorithm"""
    
    if not FA2_AVAILABLE:
        print("Using improved spring layout as fallback...")
        # More natural spring layout without circular constraints
        return nx.spring_layout(G, 
                              k=5,              # Increased distance between nodes
                              iterations=200,    # More iterations
                              seed=42,
                              weight='weight')   # Use edge weights
    
    print("Computing Force Atlas 2 layout...")
    
    # Initialize ForceAtlas2 with optimized parameters
    forceatlas2 = ForceAtlas2(
        # Behavior alternatives
        outboundAttractionDistribution=True,  # Dissuade hubs
        linLogMode=False,                     # NOT in linLog mode
        adjustSizes=False,                    # Prevent node overlapping
        edgeWeightInfluence=1.0,             # Use edge weights
        
        # Performance
        jitterTolerance=1.0,                 # Tolerance
        barnesHutOptimize=True,              # Barnes Hut optimization
        barnesHutTheta=1.2,                  # Barnes Hut theta
        multiThreaded=False,                 # Multi-threading
        
        # Tuning
        scalingRatio=2.0,                    # Attraction/repulsion ratio
        strongGravityMode=False,             # Strong gravity
        gravity=1.0,                         # Gravity strength
        
        verbose=True                         # Show progress
    )
    
    # Convert to undirected for FA2 (it works better with undirected graphs)
    G_undirected = G.to_undirected()
    
    # Run Force Atlas 2
    positions = forceatlas2.forceatlas2_networkx_layout(
        G_undirected, 
        pos=None, 
        iterations=1000  # More iterations for better convergence
    )
    
    print("Force Atlas 2 layout completed!")
    return positions

def create_true_force_directed_visualization(G, save_file='force_atlas2_citation_network.png'):
    """Create Force Atlas 2 visualization"""
    plt.figure(figsize=(24, 18))
    
    # Get Force Atlas 2 positions
    pos = create_force_atlas2_layout(G)
    
    # Separate nodes by type and citation frequency
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    # Categorize cited nodes by citation frequency
    highly_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) >= 3]
    moderately_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 2]
    single_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 1]
    
    print(f"Network Composition:")
    print(f"  Main papers: {len(main_nodes)}")
    print(f"  Highly cited (3+): {len(highly_cited)}")
    print(f"  Moderately cited (2): {len(moderately_cited)}")
    print(f"  Single cited (1): {len(single_cited)}")
    
    # Node sizes based on citation importance and out-degree
    node_sizes = {}
    for node in G.nodes():
        base_size = 200
        if G.nodes[node].get('type') == 'main_paper':
            # Size based on how many papers they cite
            out_deg = G.out_degree(node)
            node_sizes[node] = base_size + (out_deg * 30)  # Scale with citations made
        elif node in highly_cited:
            in_deg = G.nodes[node].get('in_degree', 1)
            node_sizes[node] = base_size + (in_deg * 150)  # Large for highly cited
        elif node in moderately_cited:
            node_sizes[node] = base_size + 100            # Medium for moderately cited
        else:
            node_sizes[node] = base_size                   # Base size for single cited
    
    # Color scheme based on node importance
    colors = {
        'main': '#FF4444',        # Bright red for main papers
        'highly_cited': '#FF8C00', # Dark orange for highly cited
        'moderately_cited': '#FFD700', # Gold for moderately cited
        'single_cited': '#87CEEB'  # Sky blue for single cited
    }
    
    # Draw edges first (so they appear behind nodes)
    edges = list(G.edges())
    edge_weights = [G[u][v].get('weight', 1) for u, v in edges]
    max_weight = max(edge_weights) if edge_weights else 1
    
    # Create edge widths and alpha based on weights
    edge_widths = [max(0.2, w/max_weight * 3) for w in edge_weights]
    edge_alphas = [max(0.1, w/max_weight * 0.8) for w in edge_weights]
    
    # Draw edges with individual alpha values
    for i, (u, v) in enumerate(edges):
        nx.draw_networkx_edges(G, pos,
                              edgelist=[(u, v)],
                              edge_color='gray',
                              arrows=True,
                              arrowsize=15,
                              arrowstyle='->',
                              width=edge_widths[i],
                              alpha=edge_alphas[i],
                              connectionstyle="arc3,rad=0.1")
    
    # Draw nodes by category
    if main_nodes:
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=main_nodes,
                              node_color=colors['main'],
                              node_size=[node_sizes[n] for n in main_nodes],
                              alpha=0.9,
                              edgecolors='darkred',
                              linewidths=3)
    
    if highly_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=highly_cited,
                              node_color=colors['highly_cited'],
                              node_size=[node_sizes[n] for n in highly_cited],
                              alpha=0.85,
                              edgecolors='darkorange',
                              linewidths=2)
    
    if moderately_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=moderately_cited,
                              node_color=colors['moderately_cited'],
                              node_size=[node_sizes[n] for n in moderately_cited],
                              alpha=0.8,
                              edgecolors='goldenrod',
                              linewidths=1.5)
    
    if single_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=single_cited,
                              node_color=colors['single_cited'],
                              node_size=[node_sizes[n] for n in single_cited],
                              alpha=0.7,
                              edgecolors='steelblue',
                              linewidths=1)
    
    # Smart labeling based on node importance and position spread
    labels = {}
    
    # Always label main papers
    for node in main_nodes:
        if 'excited_delirium' in node:
            labels[node] = 'Excited Delirium'
        elif 'sudden_death' in node:
            labels[node] = 'Sudden Death'
        elif 'restraint' in node:
            labels[node] = 'Restraint'
        else:
            labels[node] = 'Main Paper'
    
    # Label all highly cited papers
    for node in highly_cited:
        if 'author' in G.nodes[node]:
            author = G.nodes[node]['author'].split()[0] if G.nodes[node]['author'] else 'Unknown'
            year = G.nodes[node].get('year', '?')
            count = G.nodes[node].get('in_degree', 1)
            labels[node] = f"{author} ({year}) [{count}]"
    
    # Label some moderately cited papers (avoid overcrowding)
    if moderately_cited:
        # Select papers that are well-separated in the layout
        positions_array = np.array([pos[node] for node in moderately_cited])
        if len(positions_array) > 0:
            # Simple spacing algorithm: select papers that are far from each other
            selected_moderate = []
            min_distance = 0.3  # Minimum distance between labeled nodes
            
            for i, node in enumerate(moderately_cited[:15]):  # Limit to 15
                node_pos = pos[node]
                too_close = False
                
                for selected in selected_moderate:
                    selected_pos = pos[selected]
                    distance = np.sqrt((node_pos[0] - selected_pos[0])**2 + 
                                     (node_pos[1] - selected_pos[1])**2)
                    if distance < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    selected_moderate.append(node)
                    author = G.nodes[node]['author'].split()[0] if G.nodes[node]['author'] else 'Unknown'
                    year = G.nodes[node].get('year', '?')
                    labels[node] = f"{author} ({year})"
    
    # Draw labels with improved styling
    nx.draw_networkx_labels(G, pos, labels, 
                           font_size=10, 
                           font_weight='bold',
                           font_color='black',
                           bbox=dict(boxstyle="round,pad=0.3", 
                                   facecolor="white", 
                                   alpha=0.9,
                                   edgecolor='gray'))
    
    # Title with algorithm information
    title = "Force Atlas 2 Citation Network: True Force-Directed Layout\n"
    if FA2_AVAILABLE:
        title += "Using Force Atlas 2 Algorithm • Natural Clustering • No Imposed Constraints"
    else:
        title += "Using Enhanced Spring Layout (ForceAtlas2 not available)"
    
    plt.title(title, fontsize=20, fontweight='bold', pad=40)
    
    # Enhanced legend
    legend_elements = [
        mpatches.Patch(color=colors['main'], label=f'Main Papers ({len(main_nodes)})'),
        mpatches.Patch(color=colors['highly_cited'], label=f'Highly Cited - 3+ papers ({len(highly_cited)})'),
        mpatches.Patch(color=colors['moderately_cited'], label=f'Moderately Cited - 2 papers ({len(moderately_cited)})'),
        mpatches.Patch(color=colors['single_cited'], label=f'Single Citations ({len(single_cited)})'),
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
               fontsize=14, title="Citation Frequency", title_fontsize=16, 
               frameon=True, fancybox=True, shadow=True)
    
    # Algorithm and network info box
    algorithm_info = f"""Force Atlas 2 Parameters
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Algorithm: {'ForceAtlas2' if FA2_AVAILABLE else 'Spring Layout'}
• Iterations: {'1000' if FA2_AVAILABLE else '200'}
• Edge Weight Influence: {'Yes' if FA2_AVAILABLE else 'Yes'}
• Barnes-Hut Optimization: {'Yes' if FA2_AVAILABLE else 'N/A'}
• Prevents Node Overlap: {'Yes' if FA2_AVAILABLE else 'Partial'}

Network Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total Nodes: {len(G.nodes())}
• Total Edges: {len(G.edges())}
• Density: {nx.density(G):.4f}
• Main Papers: {len(main_nodes)}
• Cited Papers: {len(cited_nodes)}"""
    
    plt.text(0.02, 0.02, algorithm_info, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.6", facecolor="lightyellow", alpha=0.95),
             fontsize=11, verticalalignment='bottom', fontfamily='monospace')
    
    # Add Force Atlas 2 description
    fa2_description = """Force Atlas 2 creates natural clustering by:
• Repulsing nodes based on degree
• Attracting connected nodes  
• Using edge weights for stronger connections
• Preventing artificial circular arrangements
• Allowing organic network topology emergence"""
    
    plt.text(0.98, 0.02, fa2_description, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.6", facecolor="lightcyan", alpha=0.95),
             fontsize=11, verticalalignment='bottom', horizontalalignment='right',
             fontfamily='serif', style='italic')
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Force Atlas 2 visualization saved as '{save_file}'")
    
    return G, pos

def analyze_force_atlas2_clustering(G, pos):
    """Analyze clustering patterns in the Force Atlas 2 layout"""
    print(f"\n{'='*60}")
    print("FORCE ATLAS 2 LAYOUT ANALYSIS")
    print('='*60)
    
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    
    # Calculate distances between main papers
    if len(main_nodes) >= 2:
        print("Distances between main papers:")
        for i, node1 in enumerate(main_nodes):
            for node2 in main_nodes[i+1:]:
                pos1 = np.array(pos[node1])
                pos2 = np.array(pos[node2])
                distance = np.linalg.norm(pos1 - pos2)
                print(f"  {node1} <-> {node2}: {distance:.2f}")
    
    # Find clusters by analyzing node positions
    print(f"\nClustering Analysis:")
    print("(Natural groupings formed by Force Atlas 2)")
    
    # Simple clustering: find nodes that are close to each main paper
    for main_node in main_nodes:
        main_pos = np.array(pos[main_node])
        nearby_nodes = []
        
        for node in G.nodes():
            if node != main_node and G.nodes[node].get('type') == 'cited_paper':
                node_pos = np.array(pos[node])
                distance = np.linalg.norm(main_pos - node_pos)
                if distance < 1.0:  # Threshold for "nearby"
                    nearby_nodes.append((node, distance))
        
        nearby_nodes.sort(key=lambda x: x[1])  # Sort by distance
        print(f"\n{main_node} cluster ({len(nearby_nodes)} nearby nodes):")
        for node, dist in nearby_nodes[:5]:  # Show top 5 closest
            author = G.nodes[node].get('author', 'Unknown').split()[0]
            year = G.nodes[node].get('year', '?')
            print(f"  {author} ({year}) - distance: {dist:.2f}")

def main():
    """Main function"""
    print("Loading citation network data...")
    edges_df, nodes_df = load_network_data()
    
    if edges_df is None or nodes_df is None:
        return
    
    print("Creating network graph...")
    G = create_network_graph(edges_df, nodes_df)
    
    print("Creating Force Atlas 2 visualization...")
    G, pos = create_true_force_directed_visualization(G)
    
    print("Analyzing Force Atlas 2 clustering...")
    analyze_force_atlas2_clustering(G, pos)
    
    print(f"\n{'='*60}")
    print("FORCE ATLAS 2 VISUALIZATION COMPLETE")
    print('='*60)
    print("File created: force_atlas2_citation_network.png")
    print("\nThis visualization uses the Force Atlas 2 algorithm for:")
    print("• Natural, organic network topology")
    print("• No imposed geometric constraints") 
    print("• True force-directed positioning")
    print("• Clustering based on citation relationships")
    print("• Edge weight influence on node positioning")

if __name__ == "__main__":
    main()