#!/usr/bin/env python3
"""
Pure Physics-Based Force-Directed Citation Network
No geometric constraints - pure force simulation
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import random

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
    G = nx.from_pandas_edgelist(edges_df, 
                               source='source', 
                               target='target',
                               edge_attr=['weight'],
                               create_using=nx.DiGraph())
    
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

class PhysicsSimulator:
    """Pure physics-based force simulation"""
    
    def __init__(self, G, width=20, height=20):
        self.G = G
        self.width = width
        self.height = height
        self.nodes = list(G.nodes())
        self.n_nodes = len(self.nodes)
        
        # Initialize random positions (no constraints)
        self.positions = {}
        for node in self.nodes:
            self.positions[node] = np.array([
                random.uniform(-width/2, width/2),
                random.uniform(-height/2, height/2)
            ])
        
        # Initialize velocities
        self.velocities = {node: np.array([0.0, 0.0]) for node in self.nodes}
        
        # Physics parameters
        self.spring_strength = 0.01  # Attraction force
        self.repulsion_strength = 100  # Repulsion force
        self.damping = 0.9  # Velocity damping
        self.dt = 0.1  # Time step
        self.min_distance = 0.1  # Minimum distance to prevent division by zero
        
        # Node masses based on importance
        self.masses = {}
        for node in self.nodes:
            if G.nodes[node].get('type') == 'main_paper':
                self.masses[node] = 10.0  # Heavy main papers
            elif G.nodes[node].get('in_degree', 1) >= 3:
                self.masses[node] = 5.0   # Heavy highly cited papers
            elif G.nodes[node].get('in_degree', 1) >= 2:
                self.masses[node] = 2.0   # Medium moderately cited
            else:
                self.masses[node] = 1.0   # Light single cited
    
    def calculate_repulsion_force(self, node1, node2):
        """Calculate repulsion force between two nodes"""
        pos1 = self.positions[node1]
        pos2 = self.positions[node2]
        
        diff = pos1 - pos2
        distance = np.linalg.norm(diff)
        
        if distance < self.min_distance:
            distance = self.min_distance
            
        # Coulomb-like repulsion: F = k * m1 * m2 / r^2
        force_magnitude = (self.repulsion_strength * 
                          self.masses[node1] * self.masses[node2] / 
                          (distance ** 2))
        
        # Force direction (normalize)
        force_direction = diff / distance if distance > 0 else np.array([1, 0])
        
        return force_magnitude * force_direction
    
    def calculate_spring_force(self, node1, node2, target_length=2.0):
        """Calculate spring force between connected nodes"""
        pos1 = self.positions[node1]
        pos2 = self.positions[node2]
        
        diff = pos2 - pos1
        distance = np.linalg.norm(diff)
        
        if distance == 0:
            return np.array([0.0, 0.0])
        
        # Get edge weight if it exists
        weight = 1.0
        if self.G.has_edge(node1, node2):
            weight = self.G[node1][node2].get('weight', 1.0)
        elif self.G.has_edge(node2, node1):
            weight = self.G[node2][node1].get('weight', 1.0)
        
        # Hooke's law: F = -k * (distance - natural_length)
        force_magnitude = (self.spring_strength * weight * 
                          (distance - target_length))
        
        # Force direction
        force_direction = diff / distance
        
        return force_magnitude * force_direction
    
    def step(self):
        """Single simulation step"""
        forces = {node: np.array([0.0, 0.0]) for node in self.nodes}
        
        # Calculate repulsion forces (all pairs)
        for i, node1 in enumerate(self.nodes):
            for j, node2 in enumerate(self.nodes[i+1:], i+1):
                repulsion = self.calculate_repulsion_force(node1, node2)
                forces[node1] += repulsion
                forces[node2] -= repulsion  # Newton's 3rd law
        
        # Calculate spring forces (connected pairs only)
        for edge in self.G.edges():
            node1, node2 = edge
            spring_force = self.calculate_spring_force(node1, node2)
            forces[node1] += spring_force
            forces[node2] -= spring_force
        
        # Update velocities and positions
        max_velocity = 5.0  # Cap maximum velocity
        
        for node in self.nodes:
            # F = ma, so a = F/m
            acceleration = forces[node] / self.masses[node]
            
            # Update velocity
            self.velocities[node] += acceleration * self.dt
            
            # Apply damping
            self.velocities[node] *= self.damping
            
            # Cap velocity
            vel_magnitude = np.linalg.norm(self.velocities[node])
            if vel_magnitude > max_velocity:
                self.velocities[node] = (self.velocities[node] / vel_magnitude) * max_velocity
            
            # Update position
            self.positions[node] += self.velocities[node] * self.dt
        
        # Calculate total kinetic energy (for convergence check)
        total_energy = sum(0.5 * self.masses[node] * np.linalg.norm(self.velocities[node])**2 
                          for node in self.nodes)
        
        return total_energy
    
    def simulate(self, max_steps=2000, energy_threshold=0.1, verbose=True):
        """Run the physics simulation until convergence"""
        if verbose:
            print(f"Starting physics simulation...")
            print(f"Nodes: {self.n_nodes}, Max steps: {max_steps}")
        
        energy_history = []
        
        for step in range(max_steps):
            energy = self.step()
            energy_history.append(energy)
            
            if verbose and step % 200 == 0:
                print(f"Step {step}, Energy: {energy:.4f}")
            
            # Check for convergence
            if energy < energy_threshold:
                if verbose:
                    print(f"Converged at step {step} with energy {energy:.4f}")
                break
            
            # Check for energy plateau (another convergence criterion)
            if len(energy_history) > 100:
                recent_energies = energy_history[-50:]
                if max(recent_energies) - min(recent_energies) < 0.01:
                    if verbose:
                        print(f"Converged by energy plateau at step {step}")
                    break
        
        return self.positions, energy_history

def create_pure_force_directed_visualization(G, positions, save_file='pure_force_directed_citation_network.png'):
    """Create visualization with pure force-directed positions"""
    plt.figure(figsize=(24, 18))
    
    # Categorize nodes
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    highly_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) >= 3]
    moderately_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 2]
    single_cited = [n for n in cited_nodes if G.nodes[n].get('in_degree', 1) == 1]
    
    print(f"\nNetwork composition:")
    print(f"  Main papers: {len(main_nodes)}")
    print(f"  Highly cited (3+): {len(highly_cited)}")
    print(f"  Moderately cited (2): {len(moderately_cited)}")
    print(f"  Single cited (1): {len(single_cited)}")
    
    # Convert positions to format expected by NetworkX
    pos = {node: positions[node] for node in G.nodes()}
    
    # Node sizes based on physics simulation masses
    node_sizes = {}
    for node in G.nodes():
        base_size = 100
        
        if G.nodes[node].get('type') == 'main_paper':
            out_deg = G.out_degree(node)
            node_sizes[node] = base_size * 3 + (out_deg * 15)
        elif node in highly_cited:
            in_deg = G.nodes[node].get('in_degree', 1)
            node_sizes[node] = base_size * 2 + (in_deg * 100)
        elif node in moderately_cited:
            node_sizes[node] = base_size * 1.5 + 50
        else:
            node_sizes[node] = base_size
    
    # Color scheme
    colors = {
        'main': '#E53E3E',           # Red
        'highly_cited': '#FF7A00',   # Orange  
        'moderately_cited': '#F6AD55', # Light orange
        'single_cited': '#4299E1'    # Blue
    }
    
    # Draw edges with physics-based weights
    edges = list(G.edges())
    for u, v in edges:
        weight = G[u][v].get('weight', 1)
        alpha = 0.1 + (weight * 0.4)
        width = 0.5 + (weight * 1.5)
        
        nx.draw_networkx_edges(G, pos,
                              edgelist=[(u, v)],
                              edge_color='#718096',
                              arrows=True,
                              arrowsize=15,
                              arrowstyle='->',
                              width=width,
                              alpha=alpha)
    
    # Draw nodes
    if main_nodes:
        nx.draw_networkx_nodes(G, pos, 
                              nodelist=main_nodes,
                              node_color=colors['main'],
                              node_size=[node_sizes[n] for n in main_nodes],
                              alpha=0.95,
                              edgecolors='#C53030',
                              linewidths=4)
    
    if highly_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=highly_cited,
                              node_color=colors['highly_cited'],
                              node_size=[node_sizes[n] for n in highly_cited],
                              alpha=0.9,
                              edgecolors='#DD6B20',
                              linewidths=3)
    
    if moderately_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=moderately_cited,
                              node_color=colors['moderately_cited'],
                              node_size=[node_sizes[n] for n in moderately_cited],
                              alpha=0.85,
                              edgecolors='#ED8936',
                              linewidths=2)
    
    if single_cited:
        nx.draw_networkx_nodes(G, pos,
                              nodelist=single_cited,
                              node_color=colors['single_cited'],
                              node_size=[node_sizes[n] for n in single_cited],
                              alpha=0.8,
                              edgecolors='#3182CE',
                              linewidths=1.5)
    
    # Smart labeling
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
        author = G.nodes[node].get('author', 'Unknown').split()[0]
        year = G.nodes[node].get('year', '?')
        count = G.nodes[node].get('in_degree', 1)
        labels[node] = f"{author}\n({year})\n[{count}]"
    
    # Selectively label moderately cited (avoid overlap)
    moderately_positions = np.array([pos[node] for node in moderately_cited])
    if len(moderately_cited) <= 10:  # If few enough, label all
        for node in moderately_cited:
            author = G.nodes[node].get('author', 'Unknown').split()[0]
            year = G.nodes[node].get('year', '?')
            labels[node] = f"{author}\n({year})"
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, labels, 
                           font_size=10, 
                           font_weight='bold',
                           font_color='#2D3748',
                           bbox=dict(boxstyle="round,pad=0.3", 
                                   facecolor="white", 
                                   alpha=0.9,
                                   edgecolor='#CBD5E0'))
    
    plt.title("Pure Physics-Based Citation Network\nNo Geometric Constraints • Natural Emergence • Force Simulation", 
              fontsize=20, fontweight='bold', pad=40)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=colors['main'], label=f'Main Papers ({len(main_nodes)})'),
        mpatches.Patch(color=colors['highly_cited'], label=f'Highly Cited - 3+ ({len(highly_cited)})'),
        mpatches.Patch(color=colors['moderately_cited'], label=f'Moderately Cited - 2 ({len(moderately_cited)})'),
        mpatches.Patch(color=colors['single_cited'], label=f'Single Citations ({len(single_cited)})'),
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1),
               fontsize=14, title="Node Types", title_fontsize=16)
    
    # Physics simulation info
    physics_info = f"""Physics Simulation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Pure force-based positioning
• No geometric constraints  
• Repulsion: Coulomb-like (1/r²)
• Attraction: Spring forces
• Mass-based node weighting
• Velocity damping
• Natural convergence

Network Properties
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Nodes: {len(G.nodes())}
• Edges: {len(G.edges())}
• Natural clustering emerged
• No imposed circular layout"""
    
    plt.text(0.02, 0.02, physics_info, transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#F7FAFC", alpha=0.95),
             fontsize=11, verticalalignment='bottom', fontfamily='monospace')
    
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Pure force-directed visualization saved as '{save_file}'")
    
    return pos

def analyze_natural_clusters(G, positions):
    """Analyze natural clusters that emerged from physics simulation"""
    print(f"\n{'='*60}")
    print("NATURAL CLUSTERING ANALYSIS")
    print('='*60)
    
    main_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'main_paper']
    cited_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'cited_paper']
    
    # Calculate center of mass for different node types
    if main_nodes:
        main_positions = np.array([positions[node] for node in main_nodes])
        main_center = np.mean(main_positions, axis=0)
        print(f"Main papers center of mass: ({main_center[0]:.2f}, {main_center[1]:.2f})")
    
    # Find natural clusters by analyzing distances
    print(f"\nNatural cluster formation:")
    for main_node in main_nodes:
        main_pos = positions[main_node]
        
        # Find all cited papers and their distances
        distances = []
        for cited_node in cited_nodes:
            cited_pos = positions[cited_node]
            distance = np.linalg.norm(np.array(main_pos) - np.array(cited_pos))
            distances.append((cited_node, distance))
        
        # Sort by distance and show closest
        distances.sort(key=lambda x: x[1])
        print(f"\n{main_node} - closest cited papers:")
        for node, dist in distances[:5]:
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
    
    print("Initializing physics simulation...")
    simulator = PhysicsSimulator(G, width=30, height=30)
    
    print("Running pure physics simulation...")
    positions, energy_history = simulator.simulate(max_steps=3000, verbose=True)
    
    print("Creating pure force-directed visualization...")
    pos = create_pure_force_directed_visualization(G, positions)
    
    print("Analyzing natural clusters...")
    analyze_natural_clusters(G, positions)
    
    print(f"\n{'='*60}")
    print("PURE PHYSICS SIMULATION COMPLETE")
    print('='*60)
    print("File created: pure_force_directed_citation_network.png")
    print("\nThis visualization uses:")
    print("• Pure physics-based forces (no constraints)")
    print("• Coulomb repulsion between all nodes")
    print("• Spring attraction between connected nodes") 
    print("• Mass-based weighting system")
    print("• Natural convergence to stable configuration")
    print("• Completely emergent clustering patterns")

if __name__ == "__main__":
    main()