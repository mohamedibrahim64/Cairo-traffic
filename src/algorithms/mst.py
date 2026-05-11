import heapq
from typing import List, Dict, Set, Tuple
from ..core.data_loader import CairoTransportData
from ..core.models import Road

class MinimumSpanningTree:
    def __init__(self, data: CairoTransportData):
        self.data = data
        self.mst_edges = []
        
    def kruskal_mst(self, prioritize_critical: bool = True) -> List[Tuple]:
        """
        Kruskal's algorithm for MST with priority for critical facilities
        Time Complexity: O(E log E)
        Space Complexity: O(V + E)
        """
        class DisjointSet:
            def __init__(self):
                self.parent = {}
                self.rank = {}
                
            def find(self, node):
                if node not in self.parent:
                    self.parent[node] = node
                    self.rank[node] = 0
                if self.parent[node] != node:
                    self.parent[node] = self.find(self.parent[node])
                return self.parent[node]
                
            def union(self, n1, n2):
                p1, p2 = self.find(n1), self.find(n2)
                if p1 == p2:
                    return False
                if self.rank[p1] < self.rank[p2]:
                    p1, p2 = p2, p1
                self.parent[p2] = p1
                if self.rank[p1] == self.rank[p2]:
                    self.rank[p1] += 1
                return True
        
        # Collect all edges with weights
        edges = []
        critical_facilities = {"F9", "F10", "F1", "F2"}
        
        # Add existing roads
        for road in self.data.roads:
            weight = road.distance
            # Prioritize critical facilities connections
            if prioritize_critical:
                if str(road.from_id) in critical_facilities or \
                   str(road.to_id) in critical_facilities:
                    weight *= 0.5  # Reduce weight for critical connections
                    
            edges.append((weight, road.from_id, road.to_id, "Existing", road))
        
        # Add potential new roads
        for new_road in self.data.potential_roads:
            weight = new_road['distance'] * (new_road['construction_cost'] / 1000)
            if prioritize_critical:
                if str(new_road['from_id']) in critical_facilities or \
                   str(new_road['to_id']) in critical_facilities:
                    weight *= 0.7
            edges.append((weight, new_road['from_id'], new_road['to_id'], 
                         "New", new_road))
        
        # Sort edges by weight
        edges.sort(key=lambda x: x[0])
        
        # Apply Kruskal's algorithm
        ds = DisjointSet()
        mst = []
        total_cost = 0
        
        # Collect all nodes
        all_nodes = set()
        for road in self.data.roads:
            all_nodes.add(road.from_id)
            all_nodes.add(road.to_id)
        for new_road in self.data.potential_roads:
            all_nodes.add(new_road['from_id'])
            all_nodes.add(new_road['to_id'])
        
        for weight, u, v, edge_type, edge_data in edges:
            if ds.union(str(u), str(v)):
                mst.append((u, v, weight, edge_type, edge_data))
                total_cost += weight
                if len(mst) == len(all_nodes) - 1:
                    break
        
        self.mst_edges = mst
        return mst
    
    def calculate_cost_effectiveness(self) -> Dict:
        """Calculate cost-effectiveness metrics for the MST"""
        existing_cost = sum(edge[4].distance * 100 for edge in self.mst_edges 
                          if edge[3] == "Existing")
        new_cost = sum(edge[4]['construction_cost'] for edge in self.mst_edges 
                      if edge[3] == "New")
        
        population_served = 0
        connected_nodes = set()
        for edge in self.mst_edges:
            if isinstance(edge[1], int) and edge[1] in self.data.neighborhoods:
                connected_nodes.add(edge[1])
            if isinstance(edge[2], int) and edge[2] in self.data.neighborhoods:
                connected_nodes.add(edge[2])
        
        for node in connected_nodes:
            population_served += self.data.neighborhoods[node].population
        total_cost = existing_cost + new_cost
        
        return {
            "total_cost": total_cost,
            "total_existing_cost_million": existing_cost,
            "total_new_cost_million": new_cost,
            "total_cost_million": total_cost,
            "population_served": population_served,
            "nodes_connected": len(connected_nodes),
            "edges_count": len(self.mst_edges)
        }
    
    def prim_mst(self, start_node=3) -> List[Tuple]:
        """
        Prim's algorithm for MST (alternative implementation)
        Time Complexity: O((V + E) log V)
        Space Complexity: O(V + E)
        """
        visited = set()
        mst = []
        pq = []
        
        # Initialize with start node
        visited.add(start_node)
        
        # Add all edges from start node
        for road in self.data.graph[start_node]:
            heapq.heappush(pq, (road.distance, start_node, road.to_id))
        
        while pq and len(visited) < len(self.data.neighborhoods):
            weight, u, v = heapq.heappop(pq)
            
            if v in visited:
                continue
                
            visited.add(v)
            mst.append((u, v, weight))
            
            # Add edges from newly visited node
            for road in self.data.graph[v]:
                if road.to_id not in visited:
                    heapq.heappush(pq, (road.distance, v, road.to_id))
        
        return mst