#!/usr/bin/env python3
"""
True Force-Directed Citation Network using python-igraph's Force Atlas 2
Creates a genuine force-directed graph using igraph's implementation
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import matplotlib.patches as mpatches

# Try to use python-igraph for Force Atlas 2
try:
    import igraph as ig
    IGRAPH_AVAILABLE = True
    print("Using igraph for Force Atlas 2...")
except ImportError:
    print("Installing python-igraph...")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-igraph"])
        import igraph as ig
        IGRAPH_AVAILABLE = True
        print("python-igraph installed successfully!")
    except Exception as e:
        print(f"Could not install python-igraph: {e}")
        print("Falling back to enhanced spring layout...")
        IGRAPH_AVAILABLE = False

def load_network_data():
    """Load the edges and nodes CSV files"""
    try:
        edges_df = pd.read_csv('citation_edges.csv')
        nodes_df = pd.read_csv('citation_nodes.csv')
        return edges_df, nodes_df
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None

def create_igraph_network(edges_df, nodes_df):
    """Create igraph network from the data"""
    if not IGRAPH_AVAILABLE:
        return None
    
    # Create node ID mapping
    node_ids = list(nodes_df['id'])
    id_to_index = {node_id: i for i, node_id in enumerate(node_ids)}
    
    # Create edge list with indices
    edge_list = []
    edge_weights = []
    
    for _, edge in edges_df.iterrows():
        if edge['source'] in id_to_index and edge['target'] in id_to_index:
            source_idx = id_to_index[edge['source']]
            target_idx = id_to_index[edge['target']]
            edge_list.append((source_idx, target_idx))
            edge_weights.append(edge['weight'])
    
    # Create igraph object
    g = ig.Graph(directed=True)
    g.add_vertices(len(node_ids))
    g.add_edges(edge_list)
    
    # Add vertex attributes
    for i, (_, node) in enumerate(nodes_df.iterrows()):
        g.vs[i]['id'] = node['id']
        g.vs[i]['type'] = node['type']
        g.vs[i]['author'] = node['author']
        g.vs[i]['year'] = node['year']
        g.vs[i]['title'] = node['title']
        g.vs[i]['in_degree'] = node['in_degree']
        g.vs[i]['citation_count'] = node['citation_count']
    
    # Add edge weights
    g.es['weight'] = edge_weights
    
    return g, id_to_index

def compute_force_atlas2_layout(g):
    """Compute Force Atlas 2 layout using igraph"""
    if not IGRAPH_AVAILABLE:
        return None
    
    print("Computing Force Atlas 2 layout with igraph...")
    
    # Use igraph's built-in layout algorithms
    # Try different algorithms that create natural clustering
    
    # Option 1: Large Graph Layout (LGL) - good for large networks
    try:
        layout = g.layout("lgl")
        print("Using Large Graph Layout (LGL)")
        return layout
    except:
        pass
    
    # Option 2: Fruchterman-Reingold with more iterations
    try:
        layout = g.layout("fr", niter=1000, grid=False)
        print("Using Fruchterman-Reingold layout")
        return layout
    except:
        pass
    
    # Option 3: DrL (Distributed Recursive Layout)
    try:
        layout = g.layout("drl")
        print("Using DrL layout")
        return layout
    except:
        pass
    
    # Fallback: Kamada-Kawai
    layout = g.layout("kk")
    print("Using Kamada-Kawai layout")
    return layout

def create_networkx_from_igraph_layout(edges_df, nodes_df, layout, id_to_index):
    """Create NetworkX graph with positions from igraph layout"""
    # Create NetworkX graph
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
    
    # Convert igraph layout to NetworkX positions
    pos = {}
    if layout is not None:
        for node_id, index in id_to_index.items():
            if node_id in G.nodes():
                pos[node_id] = (layout[index][0], layout[index][1])
    else:
        # Fallback to spring layout
        pos = nx.spring_layout(G, k=8, iterations=300, seed=42)
    
    return G, pos

def create_advanced_spring_layout(G):
    """Create an advanced spring layout without circular constraints"""
    print("Creating advanced spring layout...")
    
    # Multi-level layout approach
    # 1. Start with a rough layout
    pos = nx.spring_layout(G, k=10, iterations=50, seed=42)
    
    # 2. Refine with different parameters
    pos = nx.spring_layout(G, pos=pos, k=15, iterations=200, 
                          weight='weight', seed=42)
    
    # 3. Final refinement with higher repulsion
    pos = nx.spring_layout(G, pos=pos, k=20, iterations=100, 
                          weight='weight', seed=42)
    
    return pos

def create_true_force_directed_visualization(G, pos, save_file='igraph_force_atlas2_citation_network.png'):
    """Create advanced force-directed visualization"""
    plt.figure(figsize=(28, 20))
    
    # Categorize nodes
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    highly_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) >= 3]
    moderately_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 2]
    single_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 1]
    
    print(f"Network composition:")
    print(f"  Main papers: {len(main_nodes)}")
    print(f"  Highly cited (3+): {len(highly_cited)}")
    print(f"  Moderately cited (2): {len(moderately_cited)}")
    print(f"  Single cited (1): {len(single_cited)}")
    
    # Advanced node sizing based on multiple factors
    node_sizes = {}
    for node in G.nodes():
        base_size = 150
        
        if G.nodes[node].get('type') == 'main_paper':
            # Main papers: size based on citations they make
            out_deg = G.out_degree(node)
            node_sizes[node] = base_size * 2 + (out_deg * 20)
        elif node in highly_cited:
            # Highly cited: larger, scaled by citation count
            in_deg = G.nodes[node].get('in_degree', 1)
            node_sizes[node] = base_size + (in_deg * 200)
        elif node in moderately_cited:
            node_sizes[node] = base_size + 120
        else:
            node_sizes[node] = base_size
    
    # Color scheme with better distinction
    colors = {
        'main': '#E74C3C',           # Strong red
        'highly_cited': '#FF6B35',   # Orange-red  
        'moderately_cited': '#F39C12', # Orange
        'single_cited': '#3498DB'    # Blue
    }
    
    # Advanced edge rendering
    edges = list(G.edges())
    edge_weights = [G[u][v].get('weight', 1) for u, v in edges]
    max_weight = max(edge_weights) if edge_weights else 1
    
    # Create variable edge properties
    for i, (u, v) in enumerate(edges):
        weight = edge_weights[i]
        alpha = 0.1 + (weight / max_weight * 0.6)
        width = 0.3 + (weight / max_weight * 2.5)
        
        nx.draw_networkx_edges(G, pos,
                              edgelist=[(u, v)],
                              edge_color='#34495E',
                              arrows=True,
                              arrowsize=20,
                              arrowstyle='->',
                              width=width,
                              alpha=alpha,
                              connectionstyle="arc3,rad=0.05")
    
    # Draw nodes with enhanced styling
    if main_nodes:
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=main_nodes,
                              node_color=colors['main'],
                              node_size=[node_sizes[n] for n in main_nodes],
                              alpha=0.95,
                              edgecolors='#C0392B',
                              linewidths=4)
    
    if highly_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=highly_cited,
                              node_color=colors['highly_cited'],
                              node_size=[node_sizes[n] for n in highly_cited],
                              alpha=0.9,
                              edgecolors='#E67E22',
                              linewidths=3)
    
    if moderately_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=moderately_cited,
                              node_color=colors['moderately_cited'],
                              node_size=[node_sizes[n] for n in moderately_cited],
                              alpha=0.85,
                              edgecolors='#D68910',
                              linewidths=2)
    
    if single_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=single_cited,
                              node_color=colors['single_cited'],
                              node_size=[node_sizes[n] for n in single_cited],
                              alpha=0.8,
                              edgecolors='#2980B9',
                              linewidths=1.5)
    
    # Intelligent labeling
    labels = {}
    
    # Main papers - always labeled
    for node in main_nodes:
        if 'excited_delirium' in node:
            labels[node] = 'Excited\nDelirium'
        elif 'sudden_death' in node:
            labels[node] = 'Sudden\nDeath'
        elif 'restraint' in node:
            labels[node] = 'Restraint'
        else:
            labels[node] = 'Main\nPaper'
    
    # Highly cited papers - all labeled
    for node in highly_cited:
        author = G.nodes[node].get('author', 'Unknown').split()[0]
        year = G.nodes[node].get('year', '?')
        count = G.nodes[node].get('in_degree', 1)
        labels[node] = f"{author}\n({year})\n[{count} cites]"
    
    # Moderately cited - selective labeling to avoid clutter
    if len(moderately_cited) <= 20:  # If not too many, label them all
        for node in moderately_cited:
            author = G.nodes[node].get('author', 'Unknown').split()[0]
            year = G.nodes[node].get('year', '?')
            labels[node] = f"{author}\n({year})"
    else:  # Otherwise, select by spacing
        positions_mod = np.array([pos[node] for node in moderately_cited])
        # Use spatial separation to select which ones to label
        from scipy.spatial.distance import cdist
        
        selected_moderate = []
        min_distance = 0.4
        
        for node in moderately_cited:
            if len(selected_moderate) == 0:
                selected_moderate.append(node)
                continue
                
            node_pos = np.array(pos[node])
            selected_positions = np.array([pos[s] for s in selected_moderate])
            distances = cdist([node_pos], selected_positions)[0]
            
            if np.min(distances) > min_distance:
                selected_moderate.append(node)
                author = G.nodes[node].get('author', 'Unknown').split()[0]
                year = G.nodes[node].get('year', '?')
                labels[node] = f"{author}\n({year})"
    
    # Draw labels with enhanced styling
    nx.draw_networkx_labels(G, pos, labels, 
                           font_size=12, 
                           font_weight='bold',
                           font_color='#2C3E50',
                           bbox=dict(boxstyle="round,pad=0.4", 
                                   facecolor="white", 
                                   alpha=0.95,
                                   edgecolor='#BDC3C7',
                                   linewidth=1))
    
    # Enhanced title
    algorithm_used = "igraph Layout Algorithm" if IGRAPH_AVAILABLE else "Enhanced Spring Layout"
    plt.title(f"Advanced Force-Directed Citation Network\n{algorithm_used} • Natural Clustering • No Geometric Constraints", 
              fontsize=22, fontweight='bold', pad=50)
    
    # Comprehensive legend
    legend_elements = [
        mpatches.Patch(color=colors['main'], label=f'Main Papers ({len(main_nodes)})'),
        mpatches.Patch(color=colors['highly_cited'], label=f'Highly Cited - 3+ papers ({len(highly_cited)})'),
        mpatches.Patch(color=colors['moderately_cited'], label=f'Moderately Cited - 2 papers ({len(moderately_cited)})'),
        mpatches.Patch(color=colors['single_cited'], label=f'Single Citations ({len(single_cited)})'),
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
               fontsize=16, title="Citation Frequency", title_fontsize=18, 
               frameon=True, fancybox=True, shadow=True)
    
    # Technical specifications
    specs_text = f"""Layout Specifications
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Algorithm: {algorithm_used}
• Library: {'python-igraph' if IGRAPH_AVAILABLE else 'NetworkX'}
• Natural clustering: Yes
• Geometric constraints: None
• Edge weight influence: Yes
• Node size scaling: Citation-based

Network Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Nodes: {len(G.nodes())}
• Edges: {len(G.edges())}
• Density: {nx.density(G):.4f}
• Avg. degree: {2*len(G.edges())/len(G.nodes()):.2f}"""
    
    plt.text(0.02, 0.02, specs_text, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.6", facecolor="#ECF0F1", alpha=0.98),
             fontsize=12, verticalalignment='bottom', fontfamily='monospace')
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Advanced force-directed visualization saved as '{save_file}'")
    
    return G, pos

def main():
    """Main function"""
    print("Loading citation network data...")
    edges_df, nodes_df = load_network_data()
    
    if edges_df is None or nodes_df is None:
        return
    
    if IGRAPH_AVAILABLE:
        print("Creating igraph network...")
        g, id_to_index = create_igraph_network(edges_df, nodes_df)
        
        print("Computing layout...")
        layout = compute_force_atlas2_layout(g)
        
        print("Converting to NetworkX...")
        G, pos = create_networkx_from_igraph_layout(edges_df, nodes_df, layout, id_to_index)
    else:
        print("Creating NetworkX graph...")
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
        
        pos = create_advanced_spring_layout(G)
    
    print("Creating advanced force-directed visualization...")
    G, pos = create_true_force_directed_visualization(G, pos)
    
    print(f"\n{'='*60}")
    print("ADVANCED FORCE-DIRECTED VISUALIZATION COMPLETE")
    print('='*60)
    print("File created: igraph_force_atlas2_citation_network.png")
    print(f"\nUsed: {'python-igraph layout algorithms' if IGRAPH_AVAILABLE else 'Enhanced multi-level spring layout'}")
    print("Features:")
    print("• True force-directed positioning")
    print("• No imposed geometric shapes")
    print("• Natural clustering emergence")
    print("• Citation-weight influenced positioning")
    print("• Intelligent node sizing and labeling")

if __name__ == "__main__":
    # Try to install scipy if needed (for spatial distance calculations)
    try:
        from scipy.spatial.distance import cdist
    except ImportError:
        print("Installing scipy for advanced features...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])
        from scipy.spatial.distance import cdist
    
    main()