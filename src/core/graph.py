"""
Graph data structure for Cairo transportation network
"""
from typing import Dict, List, Set, Tuple, Optional, Any, Iterator
import heapq
from collections import defaultdict, deque
import numpy as np

class Graph:
    """
    Weighted graph representation of Cairo's transportation network
    Supports both directed and undirected edges with multiple weight types
    """
    
    def __init__(self, directed: bool = False):
        self.directed = directed
        self.adjacency_list = defaultdict(list)
        self.nodes = set()
        self.edges = []
        self.node_attributes = {}
        self.edge_attributes = {}
        
    def add_node(self, node_id: Any, **attributes):
        """Add a node to the graph with optional attributes"""
        self.nodes.add(node_id)
        if attributes:
            if node_id not in self.node_attributes:
                self.node_attributes[node_id] = {}
            self.node_attributes[node_id].update(attributes)
    
    def add_edge(self, from_node: Any, to_node: Any, weight: float = 1.0, 
                 **attributes):
        """Add a weighted edge to the graph"""
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        
        edge_data = {'weight': weight, **attributes}
        self.adjacency_list[from_node].append((to_node, edge_data))
        self.edges.append((from_node, to_node, edge_data))
        
        if not self.directed:
            self.adjacency_list[to_node].append((from_node, edge_data.copy()))
    
    def remove_node(self, node_id: Any):
        """Remove a node and all its connected edges"""
        if node_id in self.nodes:
            self.nodes.remove(node_id)
            if node_id in self.adjacency_list:
                del self.adjacency_list[node_id]
            if node_id in self.node_attributes:
                del self.node_attributes[node_id]
            
            # Remove edges to this node
            self.edges = [(f, t, d) for f, t, d in self.edges 
                         if f != node_id and t != node_id]
            
            # Clean adjacency lists of other nodes
            for node in self.adjacency_list:
                self.adjacency_list[node] = [
                    (n, d) for n, d in self.adjacency_list[node] 
                    if n != node_id
                ]
    
    def get_neighbors(self, node_id: Any) -> List[Tuple[Any, Dict]]:
        """Get all neighbors of a node with edge data"""
        return self.adjacency_list.get(node_id, [])
    
    def get_edge_weight(self, from_node: Any, to_node: Any) -> Optional[float]:
        """Get the weight of an edge between two nodes"""
        for neighbor, edge_data in self.adjacency_list.get(from_node, []):
            if neighbor == to_node:
                return edge_data.get('weight', 1.0)
        return None
    
    def has_edge(self, from_node: Any, to_node: Any) -> bool:
        """Check if an edge exists between two nodes"""
        return any(n == to_node for n, _ in self.adjacency_list.get(from_node, []))
    
    @property
    def node_count(self) -> int:
        return len(self.nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    def get_node_coordinates(self, node_id: Any) -> Optional[Tuple[float, float]]:
        """Get coordinates of a node if available"""
        attrs = self.node_attributes.get(node_id, {})
        x = attrs.get('x', None)
        y = attrs.get('y', None)
        if x is not None and y is not None:
            return (x, y)
        return None
    
    def to_adjacency_matrix(self) -> np.ndarray:
        """Convert graph to adjacency matrix"""
        n = len(self.nodes)
        node_to_index = {node: i for i, node in enumerate(sorted(self.nodes))}
        matrix = np.full((n, n), np.inf)
        np.fill_diagonal(matrix, 0)
        
        for from_node, to_node, edge_data in self.edges:
            i, j = node_to_index[from_node], node_to_index[to_node]
            matrix[i][j] = edge_data.get('weight', 1.0)
            if not self.directed:
                matrix[j][i] = edge_data.get('weight', 1.0)
        
        return matrix
    
    def __str__(self) -> str:
        return f"Graph(nodes={len(self.nodes)}, edges={len(self.edges)}, directed={self.directed})"
    
    def __repr__(self) -> str:
        return self.__str__()


class TemporalGraph(Graph):
    """
    Extended graph that supports time-dependent edge weights
    Used for modeling time-varying traffic conditions
    """
    
    def __init__(self, directed: bool = False):
        super().__init__(directed)
        self.temporal_weights = defaultdict(dict)  # {edge: {time: weight}}
        
    def add_temporal_edge(self, from_node: Any, to_node: Any, 
                          time_weights: Dict[int, float], **attributes):
        """Add an edge with time-dependent weights"""
        edge_key = (from_node, to_node)
        self.temporal_weights[edge_key] = time_weights
        super().add_edge(from_node, to_node, 
                        weight=sum(time_weights.values())/len(time_weights),
                        **attributes)
    
    def get_weight_at_time(self, from_node: Any, to_node: Any, time: int) -> float:
        """Get edge weight at a specific time"""
        edge_key = (from_node, to_node)
        if edge_key in self.temporal_weights:
            return self.temporal_weights[edge_key].get(time, 1.0)
        return self.get_edge_weight(from_node, to_node) or 1.0


class FlowGraph(Graph):
    """
    Extended graph for flow network problems
    Supports capacity constraints
    """
    
    def __init__(self):
        super().__init__(directed=True)
        self.capacities = {}
        self.flow = defaultdict(float)
        
    def add_flow_edge(self, from_node: Any, to_node: Any, capacity: float, 
                      cost: float = 0):
        """Add an edge with capacity and cost"""
        super().add_edge(from_node, to_node, weight=cost)
        self.capacities[(from_node, to_node)] = capacity
        self.flow[(from_node, to_node)] = 0
        
        # Add reverse edge for residual graph
        super().add_edge(to_node, from_node, weight=-cost)
        self.capacities[(to_node, from_node)] = 0
        
    def get_residual_capacity(self, from_node: Any, to_node: Any) -> float:
        """Get remaining capacity on an edge"""
        if (from_node, to_node) in self.capacities:
            return self.capacities[(from_node, to_node)] - self.flow[(from_node, to_node)]
        return 0
    
    def push_flow(self, from_node: Any, to_node: Any, amount: float):
        """Push flow along an edge"""
        self.flow[(from_node, to_node)] += amount
        self.flow[(to_node, from_node)] -= amount
