"""
Network Visualization for Cairo Transportation System
Generates visualizations of the transportation network with algorithms results
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from ..core.data_loader import CairoTransportData


class NetworkPlotter:
    """
    Visualizes the Cairo transportation network
    Time Complexity: O(V + E) for graph plotting
    """

    def __init__(self, data: CairoTransportData, figure_size: Tuple = (15, 12)):
        self.data = data
        self.figure_size = figure_size
        self.G = nx.Graph()
        self._build_networkx_graph()

    def _build_networkx_graph(self):
        """Build NetworkX graph from transportation data"""
        # Add nodes
        for nid, neighborhood in self.data.neighborhoods.items():
            self.G.add_node(nid, pos=(neighborhood.x, neighborhood.y),
                           node_type='neighborhood', population=neighborhood.population)
        
        for fid, facility in self.data.facilities.items():
            self.G.add_node(fid, pos=(facility.x, facility.y),
                           node_type='facility', facility_type=facility.type.name)
        
        # Add edges
        for road in self.data.roads:
            self.G.add_edge(road.from_id, road.to_id,
                           weight=road.distance, capacity=road.capacity,
                           condition=road.condition)

    def plot_basic_network(self, title: str = "Cairo Transportation Network",
                          save_path: Optional[str] = None):
        """
        Plot basic network topology
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        # Get positions
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Draw edges
        nx.draw_networkx_edges(self.G, pos, ax=ax, width=1.5, alpha=0.6)
        
        # Draw neighborhood nodes
        neighborhoods = [n for n, d in self.G.nodes(data=True) 
                        if d.get('node_type') == 'neighborhood']
        nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhoods,
                              node_color='lightblue', node_size=500,
                              label='Neighborhoods', ax=ax)
        
        # Draw facility nodes
        facilities = [n for n, d in self.G.nodes(data=True) 
                     if d.get('node_type') == 'facility']
        nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                              node_color='red', node_size=400,
                              label='Facilities', ax=ax)
        
        # Draw labels
        labels = {}
        for node in self.G.nodes():
            if isinstance(node, int):
                labels[node] = str(node)
            else:
                labels[node] = node
        
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax

    def plot_mst_network(self, mst_edges: List[Tuple], title: str = "Minimum Spanning Tree",
                        save_path: Optional[str] = None):
        """
        Plot MST with highlighted edges
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Get MST edges
        mst_edge_list = [(e[0], e[1]) for e in mst_edges]
        
        # Draw all edges in light gray
        nx.draw_networkx_edges(self.G, pos, ax=ax, width=0.5, alpha=0.2, edge_color='gray')
        
        # Highlight MST edges
        mst_edges_subset = self.G.edge_subgraph(mst_edge_list)
        nx.draw_networkx_edges(mst_edges_subset, pos, ax=ax, width=3,
                              edge_color='green', alpha=0.8, label='MST Edges')
        
        # Draw nodes
        neighborhoods = [n for n, d in self.G.nodes(data=True) 
                        if d.get('node_type') == 'neighborhood']
        nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhoods,
                              node_color='lightblue', node_size=500, ax=ax)
        
        facilities = [n for n, d in self.G.nodes(data=True) 
                     if d.get('node_type') == 'facility']
        nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                              node_color='red', node_size=400, ax=ax)
        
        # Labels
        labels = {n: str(n) for n in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax

    def plot_shortest_path(self, path: List[Any], title: str = "Shortest Path Route",
                          save_path: Optional[str] = None):
        """
        Plot a specific shortest path route
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Draw all edges faintly
        nx.draw_networkx_edges(self.G, pos, ax=ax, width=0.5, alpha=0.1, edge_color='gray')
        
        # Highlight path
        path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        path_subgraph = self.G.edge_subgraph(path_edges)
        nx.draw_networkx_edges(path_subgraph, pos, ax=ax, width=3,
                              edge_color='blue', alpha=0.8)
        
        # Draw path nodes
        path_nodes = path[1:-1]  # Exclude start and end
        if path_nodes:
            nx.draw_networkx_nodes(self.G, pos, nodelist=path_nodes,
                                  node_color='yellow', node_size=400, ax=ax)
        
        # Draw start and end
        if path:
            nx.draw_networkx_nodes(self.G, pos, nodelist=[path[0]],
                                  node_color='green', node_size=600, ax=ax,
                                  label='Start')
            nx.draw_networkx_nodes(self.G, pos, nodelist=[path[-1]],
                                  node_color='red', node_size=600, ax=ax,
                                  label='End')
        
        # Draw other nodes
        other_nodes = [n for n in self.G.nodes() if n not in path]
        neighborhoods = [n for n in other_nodes if isinstance(n, int)]
        facilities = [n for n in other_nodes if isinstance(n, str)]
        
        nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhoods,
                              node_color='lightblue', node_size=300, ax=ax)
        nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                              node_color='lightcoral', node_size=250, ax=ax)
        
        # Labels
        labels = {n: str(n) for n in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend(loc='upper right')
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax

    def plot_traffic_congestion(self, congestion_data: Dict[Tuple, float],
                               title: str = "Traffic Congestion Map",
                               save_path: Optional[str] = None):
        """
        Plot traffic congestion levels on roads
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Create edge colors based on congestion
        edge_colors = []
        edge_widths = []
        
        for edge in self.G.edges():
            congestion = congestion_data.get(edge, 0)
            # Reverse lookup if not found
            if edge not in congestion_data:
                congestion = congestion_data.get((edge[1], edge[0]), 0)
            
            edge_colors.append(congestion)
            edge_widths.append(1 + congestion * 2)
        
        # Draw edges with color gradient
        edges = nx.draw_networkx_edges(self.G, pos, ax=ax, width=edge_widths,
                                       edge_color=edge_colors, edge_cmap=plt.cm.RdYlGn_r,
                                       edge_vmin=0, edge_vmax=1, alpha=0.8)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn_r, 
                                   norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Congestion Level', fontsize=12)
        
        # Draw nodes
        neighborhoods = [n for n, d in self.G.nodes(data=True) 
                        if d.get('node_type') == 'neighborhood']
        nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhoods,
                              node_color='lightblue', node_size=500, ax=ax)
        
        facilities = [n for n, d in self.G.nodes(data=True) 
                     if d.get('node_type') == 'facility']
        nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                              node_color='red', node_size=400, ax=ax)
        
        # Labels
        labels = {n: str(n) for n in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax

    def plot_population_density(self, title: str = "Population Distribution",
                               save_path: Optional[str] = None):
        """
        Plot nodes colored by population density
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Draw edges
        nx.draw_networkx_edges(self.G, pos, ax=ax, width=1, alpha=0.3)
        
        # Get population values
        populations = []
        neighborhood_nodes = []
        
        for node in self.G.nodes():
            if isinstance(node, int):  # Neighborhood
                pop = self.data.neighborhoods[node].population
                populations.append(pop)
                neighborhood_nodes.append(node)
        
        # Normalize populations for node sizes
        if populations:
            min_pop = min(populations)
            max_pop = max(populations)
            node_sizes = [300 + (p - min_pop) / (max_pop - min_pop) * 700 
                         for p in populations]
        else:
            node_sizes = [500] * len(neighborhood_nodes)
        
        # Draw neighborhood nodes with size based on population
        nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhood_nodes,
                              node_color=populations, node_size=node_sizes,
                              cmap=plt.cm.YlOrRd, ax=ax, alpha=0.8)
        
        # Draw facility nodes
        facilities = [n for n, d in self.G.nodes(data=True) 
                     if d.get('node_type') == 'facility']
        nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                              node_color='blue', node_size=400, ax=ax, alpha=0.8)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd,
                                   norm=plt.Normalize(vmin=min(populations) if populations else 0,
                                                     vmax=max(populations) if populations else 1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Population', fontsize=12)
        
        # Labels
        labels = {n: str(n) for n in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax

    def plot_road_condition(self, title: str = "Road Condition Map",
                           save_path: Optional[str] = None):
        """
        Plot roads colored by condition (1-10 scale)
        """
        fig, ax = plt.subplots(figsize=self.figure_size)
        
        pos = nx.get_node_attributes(self.G, 'pos')
        
        # Get edge conditions
        edge_conditions = []
        edge_list = []
        
        for u, v, data in self.G.edges(data=True):
            condition = data.get('condition', 5)
            edge_conditions.append(condition)
            edge_list.append((u, v))
        
        # Draw edges with color based on condition
        edges = nx.draw_networkx_edges(self.G, pos, ax=ax, width=2,
                                       edge_color=edge_conditions,
                                       edge_cmap=plt.cm.RdYlGn,
                                       edge_vmin=1, edge_vmax=10, alpha=0.8)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn,
                                   norm=plt.Normalize(vmin=1, vmax=10))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Road Condition (1=Poor, 10=Excellent)', fontsize=12)
        
        # Draw nodes
        neighborhoods = [n for n, d in self.G.nodes(data=True) 
                        if d.get('node_type') == 'neighborhood']
        nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhoods,
                              node_color='lightblue', node_size=500, ax=ax)
        
        facilities = [n for n, d in self.G.nodes(data=True) 
                     if d.get('node_type') == 'facility']
        nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                              node_color='red', node_size=400, ax=ax)
        
        # Labels
        labels = {n: str(n) for n in self.G.nodes()}
        nx.draw_networkx_labels(self.G, pos, labels, font_size=8, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, ax

    def plot_multi_algorithm_comparison(self, results: Dict[str, List],
                                       title: str = "Algorithm Comparison",
                                       save_path: Optional[str] = None):
        """
        Plot multiple algorithm results side by side
        """
        num_algos = len(results)
        fig, axes = plt.subplots(1, num_algos, figsize=(15 * num_algos / 4, 12))
        
        if num_algos == 1:
            axes = [axes]
        
        pos = nx.get_node_attributes(self.G, 'pos')
        
        for idx, (algo_name, path) in enumerate(results.items()):
            ax = axes[idx]
            
            # Draw all edges faintly
            nx.draw_networkx_edges(self.G, pos, ax=ax, width=0.5, alpha=0.1)
            
            # Highlight path
            path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
            path_subgraph = self.G.edge_subgraph(path_edges)
            nx.draw_networkx_edges(path_subgraph, pos, ax=ax, width=2,
                                  edge_color='blue', alpha=0.8)
            
            # Draw nodes
            neighborhoods = [n for n, d in self.G.nodes(data=True) 
                            if d.get('node_type') == 'neighborhood']
            nx.draw_networkx_nodes(self.G, pos, nodelist=neighborhoods,
                                  node_color='lightblue', node_size=300, ax=ax)
            
            facilities = [n for n, d in self.G.nodes(data=True) 
                         if d.get('node_type') == 'facility']
            nx.draw_networkx_nodes(self.G, pos, nodelist=facilities,
                                  node_color='red', node_size=250, ax=ax)
            
            # Start and end
            nx.draw_networkx_nodes(self.G, pos, nodelist=[path[0]],
                                  node_color='green', node_size=400, ax=ax)
            nx.draw_networkx_nodes(self.G, pos, nodelist=[path[-1]],
                                  node_color='red', node_size=400, ax=ax)
            
            # Labels
            labels = {n: str(n) for n in self.G.nodes()}
            nx.draw_networkx_labels(self.G, pos, labels, font_size=7, ax=ax)
            
            ax.set_title(algo_name, fontsize=12, fontweight='bold')
            ax.axis('off')
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def save_network_stats(self, output_path: str):
        """Save network statistics to file"""
        with open(output_path, 'w') as f:
            f.write("=== Cairo Transportation Network Statistics ===\n\n")
            
            f.write(f"Nodes: {self.G.number_of_nodes()}\n")
            f.write(f"  - Neighborhoods: {len([n for n in self.G.nodes() if isinstance(n, int)])}\n")
            f.write(f"  - Facilities: {len([n for n in self.G.nodes() if isinstance(n, str)])}\n")
            
            f.write(f"\nEdges: {self.G.number_of_edges()}\n")
            
            total_distance = sum([data['weight'] for u, v, data in self.G.edges(data=True)])
            f.write(f"Total Road Distance: {total_distance:.2f} km\n")
            
            total_capacity = sum([data['capacity'] for u, v, data in self.G.edges(data=True)])
            f.write(f"Total Network Capacity: {total_capacity:,} vehicles/hour\n")
            
            avg_condition = np.mean([data['condition'] for u, v, data in self.G.edges(data=True)])
            f.write(f"Average Road Condition: {avg_condition:.2f}/10\n")
