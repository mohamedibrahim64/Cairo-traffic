from typing import List, Dict, Tuple
import heapq
from collections import deque
from ..core.data_loader import CairoTransportData

class GreedyTrafficOptimizer:
    def __init__(self, data: CairoTransportData):
        self.data = data
        
    def optimize_traffic_signals(self, intersections: List, 
                                  time_window: int = 60) -> Dict:
        """
        Greedy approach for real-time traffic signal optimization
        Time Complexity: O(n * t) where n is intersections, t is time window
        Space Complexity: O(n)
        """
        signal_phases = {}
        
        for intersection in intersections:
            # Determine incoming traffic from all directions
            traffic_flows = self._get_intersection_traffic(intersection)
            
            # Greedy: allocate more green time to highest traffic direction
            total_flow = sum(traffic_flows.values())
            
            if total_flow == 0:
                # Equal distribution if no data
                phase_time = time_window / len(traffic_flows)
                signal_phases[intersection] = {
                    direction: phase_time 
                    for direction in traffic_flows
                }
            else:
                # Proportional to traffic flow (greedy)
                signal_phases[intersection] = {}
                for direction, flow in traffic_flows.items():
                    # Allocate time proportionally
                    green_time = (flow / total_flow) * time_window
                    
                    # Ensure minimum green time for safety
                    green_time = max(green_time, 5)  
                    green_time = min(green_time, time_window - 10)
                    
                    signal_phases[intersection][direction] = green_time
        
        return {
            "signal_phases": signal_phases,
            "total_green_time": sum(sum(p.values()) for p in signal_phases.values())
        }
    
    def emergency_vehicle_preemption(self, active_emergencies: List,
                                     current_signals: Dict,
                                     hour: int = 10) -> Dict:
        """
        Priority-based system for managing emergency vehicle preemption
        Greedy: Assign highest priority to most critical emergencies
        """
        # Define priority levels
        priority_levels = {
            "critical": 0,  # Highest priority
            "emergency": 1,
            "urgent": 2,
            "normal": 3
        }
        
        # Sort emergencies by priority (greedy selection)
        emergencies = deque(sorted(
            active_emergencies,
            key=lambda e: (priority_levels.get(e['type'], 3), e['response_time'])
        ))
        
        modified_signals = dict(current_signals)
        path_clear_times = {}
        
        processed_order = []

        while emergencies:
            emergency = emergencies.popleft()
            emergency_id = emergency.get('id') or f"emergency_{len(processed_order) + 1}"
            processed_order.append(emergency_id)
            vehicle_path = emergency['path']
            vehicle_type = emergency['type']
            
            # Greedy: clear entire path in advance
            for intersection in vehicle_path:
                if intersection in modified_signals:
                    # Override signals for emergency vehicle
                    phases = modified_signals[intersection]
                    
                    if vehicle_type == 'critical':
                        # Full preemption for critical emergencies
                        for direction in phases:
                            phases[direction] = 0
                        phases['emergency_pass'] = 60  # Full green
                    elif vehicle_type == 'emergency':
                        # Partial preemption
                        for direction in phases:
                            phases[direction] *= 0.3
                        phases['emergency_pass'] = 40
                    else:
                        # Priority adjustment
                        for direction in phases:
                            phases[direction] *= 0.7
                        phases['emergency_pass'] = 20
            
            path_clear_times[emergency_id] = len(vehicle_path) * 0.5
        
        return {
            "modified_signals": modified_signals,
            "clear_times": path_clear_times,
            "priority_order": processed_order
        }
    
    def greedy_route_recommendation(self, start, end, avoid_roads: List = None,
                                    hour: int = 10) -> Dict:
        """
        Greedy route recommendation avoiding congested areas.
        If Greedy gets stuck, fall back to a shortest-path tail so the UI still gets a complete route.
        """
        current = start
        path = [current]
        total_distance = 0
        avoid_set = set(avoid_roads or [])
        used_fallback = False
        
        while current != end:
            best_next = None
            best_score = float('inf')
            
            # Greedy: choose the next node that minimizes congestion
            for road in self.data.graph[current]:
                neighbor = road.to_id
                
                if neighbor in path:  # Avoid cycles
                    continue
                
                road_key = f"{current}-{neighbor}"
                if road_key in avoid_set:
                    continue
                
                # Score based on distance and traffic
                congestion = self._get_congestion(road_key, hour)
                score = road.distance * (1 + congestion / road.capacity)
                
                if score < best_score:
                    best_score = score
                    best_next = neighbor
            
            if best_next is None:
                break
            
            path.append(best_next)
            total_distance += self._get_distance(current, best_next)
            current = best_next
            
            # Prevent infinite loops
            if len(path) > len(self.data.graph) * 2:
                break

        # If Greedy stopped early, complete the route with a shortest-path fallback.
        if current != end:
            from .shortest_path import ShortestPath
            fallback_path, fallback_distance = ShortestPath(self.data).dijkstra(current, end, hour)
            if fallback_path:
                used_fallback = True
                path.extend(fallback_path[1:])
                total_distance += fallback_distance
                current = end
        
        return {
            "path": path,
            "total_distance": total_distance,
            "complete": current == end,
            "used_fallback": used_fallback,
            "congestion_score": self._calculate_path_congestion(path, hour)
        }
    
    def analyze_greedy_optimality(self, start, end, hour: int = 10) -> Dict:
        """
        Analyze cases where greedy provides optimal vs suboptimal solutions
        """
        from .shortest_path import ShortestPath
        sp = ShortestPath(self.data)
        
        # Get optimal path using Dijkstra
        optimal_path, optimal_dist = sp.dijkstra(start, end, hour)
        
        # Get greedy path
        greedy_result = self.greedy_route_recommendation(start, end, hour=hour)
        greedy_path = greedy_result['path']
        greedy_dist = greedy_result['total_distance']
        
        # Calculate optimality gap
        if optimal_dist > 0:
            optimality_gap = (greedy_dist - optimal_dist) / optimal_dist * 100
        else:
            optimality_gap = 0
        
        return {
            "optimal_path": optimal_path,
            "optimal_distance": optimal_dist,
            "greedy_path": greedy_path,
            "greedy_distance": greedy_dist,
            "optimality_gap_percent": optimality_gap,
            "is_optimal": optimality_gap < 1,  # Within 1% tolerance
            "analysis": "Greedy performs well in most cases but can be suboptimal "
                       "when traffic patterns change dynamically"
        }
    
    def _get_intersection_traffic(self, intersection) -> Dict[str, int]:
        """Get traffic flows for an intersection"""
        flows = {}
        for road in self.data.roads:
            if road.from_id == intersection or road.to_id == intersection:
                direction = f"{road.from_id}-{road.to_id}"
                # Find traffic data
                for pattern_key, pattern in self.data.traffic_patterns.items():
                    if pattern_key == direction:
                        flows[direction] = pattern.morning_peak
                        break
                else:
                    flows[direction] = 1000  # Default
        return flows
    
    def _get_congestion(self, road_key: str, hour: int) -> float:
        """Get congestion level for a road at given hour"""
        if road_key in self.data.traffic_patterns:
            return self.data.traffic_patterns[road_key].get_current_traffic(hour)
        return 500  # Default
    
    def _get_distance(self, from_node, to_node) -> float:
        """Get distance between two nodes"""
        for road in self.data.roads:
            if (road.from_id == from_node and road.to_id == to_node) or \
               (road.from_id == to_node and road.to_id == from_node):
                return road.distance
        return 0.0
    
    def _calculate_path_congestion(self, path: List, hour: int) -> float:
        """Calculate congestion score for a path"""
        if not path:
            return 0
        total_congestion = 0
        for i in range(len(path) - 1):
            road_key = f"{path[i]}-{path[i+1]}"
            total_congestion += self._get_congestion(road_key, hour)
        return total_congestion / len(path) if len(path) > 1 else 0