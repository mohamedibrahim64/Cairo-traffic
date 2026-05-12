import heapq
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import math
from itertools import count
from ..core.data_loader import CairoTransportData

class ShortestPath:
    def __init__(self, data: CairoTransportData):
        self.data = data
        self.memo_cache = {}
        
    def dijkstra(self, start: Any, end: Any, time_hour: int = 10,
                 avoid_roads: Optional[List[str]] = None) -> Tuple[List, float]:
        """
        Dijkstra's algorithm for shortest path
        Time Complexity: O((V + E) log V)
        Space Complexity: O(V)
        """
        # Check memo cache
        avoid_set = self._normalize_avoid_roads(avoid_roads)
        avoid_key = "|".join(sorted(avoid_set)) if avoid_set else "none"
        cache_key = f"dijkstra_{start}_{end}_{time_hour}_{avoid_key}"
        if cache_key in self.memo_cache:
            return self.memo_cache[cache_key]
        
        distances = defaultdict(lambda: float('inf'))
        distances[start] = 0
        previous = {}
        tie_breaker = count()
        pq = [(0, next(tie_breaker), start)]
        visited = set()
        
        while pq:
            current_dist, _, current = heapq.heappop(pq)
            
            if current == end:
                path = self._reconstruct_path(previous, start, end)
                self.memo_cache[cache_key] = (path, current_dist)
                return path, current_dist
            
            if current in visited:
                continue
            visited.add(current)
            
            # Process neighbors
            for road in self.data.graph[current]:
                neighbor = road.to_id
                if neighbor in visited:
                    continue

                if self._is_road_avoided(current, neighbor, avoid_set):
                    continue
                
                # Calculate edge weight considering traffic
                edge_weight = self._calculate_edge_weight(road, time_hour)
                new_dist = current_dist + edge_weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, next(tie_breaker), neighbor))
        
        return [], float('inf')
    
    def _calculate_edge_weight(self, road, time_hour: int) -> float:
        """Calculate edge weight considering traffic conditions"""
        base_weight = road.distance
        
        # Get traffic pattern for this road
        road_key = f"{road.from_id}-{road.to_id}"
        reverse_key = f"{road.to_id}-{road.from_id}"
        
        if road_key in self.data.traffic_patterns:
            pattern = self.data.traffic_patterns[road_key]
            traffic_volume = pattern.get_current_traffic(time_hour)
        elif reverse_key in self.data.traffic_patterns:
            pattern = self.data.traffic_patterns[reverse_key]
            traffic_volume = pattern.get_current_traffic(time_hour)
        else:
            traffic_volume = 1000  # Default
        
        # Adjust weight based on traffic congestion
        congestion_factor = traffic_volume / road.capacity
        if congestion_factor > 0.8:
            base_weight *= 1.5  # Heavy traffic penalty
        elif congestion_factor > 0.5:
            base_weight *= 1.2  # Moderate traffic
                
        return base_weight
    
    def a_star_search(self, start, end, time_hour: int = 10,
                      avoid_roads: Optional[List[str]] = None) -> Tuple[List, float]:
        """
        A* search algorithm for emergency vehicle routing
        Time Complexity: O((V + E) log V)
        Space Complexity: O(V)
        """
        def heuristic(node) -> float:
            """Heuristic function using straight-line distance"""
            if isinstance(node, int) and node in self.data.neighborhoods:
                node_coords = self.data.neighborhoods[node]
                end_coords = self._get_coordinates(end)
                return self._euclidean_distance(
                    node_coords.x, node_coords.y,
                    end_coords[0], end_coords[1]
                )
            elif isinstance(node, str):
                node_coords = self._get_coordinates(node)
                end_coords = self._get_coordinates(end)
                return self._euclidean_distance(
                    node_coords[0], node_coords[1],
                    end_coords[0], end_coords[1]
                )
            return 0
        
        tie_breaker = count()
        open_set = [(0, next(tie_breaker), start)]
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = heuristic(start)
        came_from = {}
        closed_set = set()
        avoid_set = self._normalize_avoid_roads(avoid_roads)
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            if current == end:
                path = self._reconstruct_path(came_from, start, end)
                return path, g_score[current]
            
            closed_set.add(current)
            
            for road in self.data.graph[current]:
                neighbor = road.to_id
                if neighbor in closed_set:
                    continue

                if self._is_road_avoided(current, neighbor, avoid_set):
                    continue
                
                # For emergency vehicles, prioritize shortest time using same
                # traffic-aware edge weight as Dijkstra so comparisons are consistent
                edge_weight = self._calculate_edge_weight(road, time_hour)
                tentative_g = g_score[current] + edge_weight
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = g_score[neighbor] + heuristic(neighbor)
                    
                    # Check if neighbor is medical facility - reduce priority
                    if isinstance(neighbor, str) and neighbor.startswith('F'):
                        facility = self.data.facilities.get(neighbor)
                        if facility and facility.type.value == "Medical":
                            f_score[neighbor] *= 0.8  # Prioritize medical facilities
                    
                    heapq.heappush(open_set, (f_score[neighbor], next(tie_breaker), neighbor))
        
        return [], float('inf')
    
    def time_varying_shortest_path(self, start, end, departure_time: int,
                                   avoid_roads: Optional[List[str]] = None) -> Dict:
        """
        Modified shortest path accounting for time-varying conditions
        """
        path_off_peak, dist_off = self.dijkstra(start, end, 10, avoid_roads)
        path_peak, dist_peak = self.dijkstra(start, end, 8, avoid_roads)
        
        # Calculate expected arrival times
        off_peak_congestion = self._calculate_path_congestion(path_off_peak, 10)
        peak_congestion = self._calculate_path_congestion(path_peak, 8)
        
        return {
            "off_peak_route": path_off_peak,
            "peak_route": path_peak,
            "off_peak_distance": dist_off,
            "peak_distance": dist_peak,
            "off_peak_congestion": off_peak_congestion,
            "peak_congestion": peak_congestion,
            "recommended_route": path_off_peak if off_peak_congestion < peak_congestion 
                                else path_peak
        }
    
    def _reconstruct_path(self, came_from: Dict, start, end) -> List:
        """Reconstruct path from start to end using came_from dictionary"""
        path = [end]
        current = end
        while current != start:
            current = came_from.get(current)
            if current is None:
                return []
            path.append(current)
        return path[::-1]
    
    def _get_coordinates(self, node) -> Tuple[float, float]:
        """Get coordinates for a node"""
        if isinstance(node, int) and node in self.data.neighborhoods:
            n = self.data.neighborhoods[node]
            return (n.x, n.y)
        elif isinstance(node, str) and node in self.data.facilities:
            f = self.data.facilities[node]
            return (f.x, f.y)
        return (0.0, 0.0)
    
    def _euclidean_distance(self, x1, y1, x2, y2) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def _calculate_path_congestion(self, path: List, time_hour: int) -> float:
        """Calculate average congestion along a path"""
        if not path:
            return 0
        total_congestion = 0
        for i in range(len(path) - 1):
            road_key = f"{path[i]}-{path[i+1]}"
            if road_key in self.data.traffic_patterns:
                pattern = self.data.traffic_patterns[road_key]
                traffic = pattern.get_current_traffic(time_hour)
                # Find road capacity
                for road in self.data.roads:
                    if f"{road.from_id}" == str(path[i]) and f"{road.to_id}" == str(path[i+1]):
                        total_congestion += traffic / road.capacity
                        break
        return total_congestion / len(path) if len(path) > 1 else 0

    def _normalize_avoid_roads(self, avoid_roads: Optional[List[str]]) -> set:
        """Normalize avoid road list into a set of canonical road keys."""
        if not avoid_roads:
            return set()
        normalized = set()
        for item in avoid_roads:
            if not item:
                continue
            if isinstance(item, str):
                key = item.strip()
                if '-' in key:
                    normalized.add(key)
        return normalized

    def _is_road_avoided(self, from_id: Any, to_id: Any, avoid_set: set) -> bool:
        if not avoid_set:
            return False
        key = f"{from_id}-{to_id}"
        reverse_key = f"{to_id}-{from_id}"
        return key in avoid_set or reverse_key in avoid_set