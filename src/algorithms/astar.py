"""
A* Search Algorithm for Emergency Vehicle Routing
"""
import heapq
import math
from typing import Dict, List, Tuple, Set, Optional, Any, Callable
from collections import defaultdict
from itertools import count
import time

class AStarSearch:
    """
    A* search algorithm optimized for emergency vehicle routing
    Includes multiple heuristics and real-time traffic adaptation
    """
    
    def __init__(self, graph, node_coordinates: Dict[Any, Tuple[float, float]],
                 traffic_patterns: Optional[Dict[str, Any]] = None):
        self.graph = graph
        self.coordinates = node_coordinates
        self.memoized_heuristics = {}
        self.traffic_patterns = traffic_patterns or {}
        
    def find_path(self, start: Any, goal: Any, 
                  heuristic_type: str = 'euclidean',
                  time_constraint: Optional[float] = None,
                  avoid_nodes: Optional[Set[Any]] = None,
                  emergency_priority: int = 1,
                  time_hour: Optional[int] = None,
                  avoid_edges: Optional[Set[str]] = None) -> Dict:
        """
        Find optimal path using A* search
        
        Args:
            start: Starting node
            goal: Target node
            heuristic_type: 'euclidean', 'manhattan', 'chebyshev', or 'traffic_aware'
            time_constraint: Maximum allowed time for the path
            avoid_nodes: Set of nodes to avoid
            emergency_priority: Priority level (1=normal, 2=urgent, 3=critical)
            
        Returns:
            Dictionary with path, distance, time, and nodes explored
        """
        if avoid_nodes is None:
            avoid_nodes = set()
            
        # Initialize
        tie = count()
        open_set = []
        heapq.heappush(open_set, (0, next(tie), start))
        
        came_from = {}
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self._heuristic(start, goal, heuristic_type)
        
        closed_set = set()
        exploration_count = 0
        start_time = time.time()
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            exploration_count += 1
            
            if current == goal:
                path = self._reconstruct_path(came_from, start, goal)
                total_distance = g_score[goal]
                elapsed_time = time.time() - start_time
                
                return {
                    'path': path,
                    'distance': total_distance,
                    'nodes_explored': exploration_count,
                    'computation_time': elapsed_time,
                    'success': True
                }
            
            if current in closed_set:
                continue
                
            closed_set.add(current)
            
            # Explore neighbors
            for neighbor, edge_data in self._get_neighbors(current):
                if neighbor in closed_set or neighbor in avoid_nodes:
                    continue

                if self._is_edge_avoided(current, neighbor, avoid_edges):
                    continue
                
                # Calculate edge weight considering emergency priority
                edge_weight = self._calculate_edge_weight(
                    current, neighbor, edge_data, emergency_priority, time_hour
                )
                
                # Check time constraint
                tentative_g = g_score[current] + edge_weight
                if time_constraint and tentative_g > time_constraint:
                    continue
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + \
                        self._heuristic(neighbor, goal, heuristic_type)
                    
                    # Emergency bonus: reduce f_score for medical facilities
                    if self._is_medical_facility(neighbor):
                        f_score[neighbor] *= 0.8  # 20% priority boost
                    
                    heapq.heappush(open_set, (f_score[neighbor], next(tie), neighbor))
        
        # No path found
        return {
            'path': [],
            'distance': float('inf'),
            'nodes_explored': exploration_count,
            'computation_time': time.time() - start_time,
            'success': False
        }
    
    def emergency_route(self, start: Any, hospital: Any,
                        traffic_data: Optional[Dict] = None,
                        road_closures: Optional[Set[str]] = None,
                        time_hour: Optional[int] = None) -> Dict:
        """
        Specialized emergency routing with traffic awareness
        
        Args:
            start: Emergency vehicle location
            hospital: Target hospital
            traffic_data: Real-time traffic conditions
            road_closures: Set of closed roads (node1, node2)
        """
        avoid_nodes = set()
        if road_closures:
            for closure in road_closures:
                avoid_nodes.add(closure[0])
                avoid_nodes.add(closure[1])
        
        # Use traffic-aware heuristic if traffic data available
        heuristic_type = 'traffic_aware' if traffic_data else 'euclidean'
        
        result = self.find_path(
            start, hospital,
            heuristic_type=heuristic_type,
            emergency_priority=3,
            time_hour=time_hour,
            avoid_edges=road_closures
        )
        
        # Calculate estimated response time
        if result['success']:
            avg_speed = 60  # km/h for emergency vehicles
            if traffic_data:
                # Adjust speed based on traffic
                congestion = self._calculate_path_congestion(
                    result['path'], traffic_data
                )
                avg_speed *= max(0.5, 1 - congestion)
            
            result['estimated_time_minutes'] = (result['distance'] / avg_speed) * 60
        
        return result
    
    def multi_goal_search(self, start: Any, goals: List[Any],
                         heuristic_type: str = 'euclidean') -> Dict:
        """
        Find the closest goal and path to it
        Useful for finding nearest hospital
        """
        best_result = None
        best_distance = float('inf')
        
        for goal in goals:
            result = self.find_path(start, goal, heuristic_type)
            if result['success'] and result['distance'] < best_distance:
                best_result = result
                best_distance = result['distance']
                best_result['selected_goal'] = goal
        
        return best_result or {'success': False, 'path': []}
    
    def bidirectional_astar(self, start: Any, goal: Any,
                           heuristic_type: str = 'euclidean') -> Dict:
        """
        Bidirectional A* for more efficient path finding
        Searches from both start and goal simultaneously
        """
        # Forward search from start
        tie = count()
        forward_open = [(0, next(tie), start)]
        backward_open = [(0, next(tie), goal)]
        
        forward_g = defaultdict(lambda: float('inf'))
        backward_g = defaultdict(lambda: float('inf'))
        forward_g[start] = 0
        backward_g[goal] = 0
        
        forward_parent = {}
        backward_parent = {}
        
        forward_closed = set()
        backward_closed = set()
        
        best_path = None
        best_distance = float('inf')
        exploration_count = 0
        start_time = time.time()
        
        while forward_open and backward_open:
            # Forward step
            if forward_open:
                _, _, current_f = heapq.heappop(forward_open)
                exploration_count += 1
                
                if current_f in backward_closed:
                    # Paths meet
                    path = self._combine_paths(
                        forward_parent, backward_parent,
                        start, goal, current_f
                    )
                    return {
                        'path': path,
                        'distance': forward_g[current_f] + backward_g[current_f],
                        'nodes_explored': exploration_count,
                        'computation_time': time.time() - start_time,
                        'success': True
                    }
                
                if current_f not in forward_closed:
                    forward_closed.add(current_f)
                    
                    for neighbor, edge_data in self._get_neighbors(current_f):
                        if neighbor not in forward_closed:
                            tentative_g = forward_g[current_f] + edge_data.get('weight', 1)
                            if tentative_g < forward_g[neighbor]:
                                forward_parent[neighbor] = current_f
                                forward_g[neighbor] = tentative_g
                                f = tentative_g + self._heuristic(neighbor, goal, heuristic_type)
                                heapq.heappush(forward_open, (f, next(tie), neighbor))
            
            # Backward step
            if backward_open:
                _, _, current_b = heapq.heappop(backward_open)
                exploration_count += 1
                
                if current_b in forward_closed:
                    # Paths meet
                    path = self._combine_paths(
                        forward_parent, backward_parent,
                        start, goal, current_b
                    )
                    return {
                        'path': path,
                        'distance': forward_g[current_b] + backward_g[current_b],
                        'nodes_explored': exploration_count,
                        'computation_time': time.time() - start_time,
                        'success': True
                    }
                
                if current_b not in backward_closed:
                    backward_closed.add(current_b)
                    
                    for neighbor, edge_data in self._get_neighbors(current_b):
                        if neighbor not in backward_closed:
                            tentative_g = backward_g[current_b] + edge_data.get('weight', 1)
                            if tentative_g < backward_g[neighbor]:
                                backward_parent[neighbor] = current_b
                                backward_g[neighbor] = tentative_g
                                f = tentative_g + self._heuristic(neighbor, start, heuristic_type)
                                heapq.heappush(backward_open, (f, next(tie), neighbor))
        
        return {'success': False, 'path': []}
    
    def animate_search(self, start: Any, goal: Any,
                      heuristic_type: str = 'euclidean') -> List[Dict]:
        """
        Generate step-by-step animation data for visualization
        """
        frames = []
        
        tie = count()
        open_set = [(0, next(tie), start)]
        came_from = {}
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self._heuristic(start, goal, heuristic_type)
        closed_set = set()
        
        iteration = 0
        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            # Record frame
            frames.append({
                'iteration': iteration,
                'current': current,
                'open_set': [n for _, _, n in open_set],
                'closed_set': list(closed_set),
                'frontier': self._get_frontier(g_score, closed_set)
            })
            
            if current == goal:
                break
            
            if current in closed_set:
                continue
            closed_set.add(current)
            
            for neighbor, edge_data in self._get_neighbors(current):
                if neighbor in closed_set:
                    continue
                
                tentative_g = g_score[current] + edge_data.get('weight', 1)
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + \
                        self._heuristic(neighbor, goal, heuristic_type)
                    heapq.heappush(open_set, (f_score[neighbor], next(tie), neighbor))
            
            iteration += 1
        
        return frames
    
    def _heuristic(self, node: Any, goal: Any, heuristic_type: str) -> float:
        """Calculate heuristic value between node and goal"""
        # Check memo cache
        cache_key = (node, goal, heuristic_type)
        if cache_key in self.memoized_heuristics:
            return self.memoized_heuristics[cache_key]
        
        if node == goal:
            return 0
        
        # Get coordinates
        node_coords = self.coordinates.get(node)
        goal_coords = self.coordinates.get(goal)
        
        if not node_coords or not goal_coords:
            return 0
        
        x1, y1 = node_coords
        x2, y2 = goal_coords
        
        # Calculate based on heuristic type
        if heuristic_type == 'euclidean':
            h = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        elif heuristic_type == 'manhattan':
            h = abs(x2 - x1) + abs(y2 - y1)
        elif heuristic_type == 'chebyshev':
            h = max(abs(x2 - x1), abs(y2 - y1))
        elif heuristic_type == 'traffic_aware':
            # Add traffic penalty to heuristic
            base = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            traffic_penalty = self._estimate_traffic(node, goal)
            h = base * (1 + traffic_penalty)
        else:
            h = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Cache the result
        self.memoized_heuristics[cache_key] = h
        return h
    
    def _calculate_edge_weight(self, from_node: Any, to_node: Any, edge_data: Dict,
                               priority: int, time_hour: Optional[int]) -> float:
        """Calculate edge weight considering emergency priority and traffic patterns."""
        base_weight = edge_data.get('weight', 1.0)
        capacity = edge_data.get('capacity')

        if time_hour is not None and self.traffic_patterns and capacity:
            road_key = f"{from_node}-{to_node}"
            reverse_key = f"{to_node}-{from_node}"
            pattern = self.traffic_patterns.get(road_key) or self.traffic_patterns.get(reverse_key)
            if pattern:
                traffic_volume = pattern.get_current_traffic(time_hour)
                congestion_factor = traffic_volume / capacity
                if congestion_factor > 0.8:
                    base_weight *= 1.5
                elif congestion_factor > 0.5:
                    base_weight *= 1.2

        if priority >= 3:  # Critical emergency
            return base_weight * 0.5
        if priority >= 2:  # Urgent
            return base_weight * 0.75
        return base_weight

    def _get_neighbors(self, node: Any) -> List[Tuple[Any, Dict[str, Any]]]:
        """Normalize neighbors for both custom graph objects and dict adjacency lists."""
        neighbors: List[Tuple[Any, Dict[str, Any]]] = []

        if hasattr(self.graph, 'get_neighbors'):
            raw_neighbors = self.graph.get_neighbors(node)
        else:
            raw_neighbors = self.graph.get(node, []) if hasattr(self.graph, 'get') else []

        for item in raw_neighbors:
            if isinstance(item, tuple) and len(item) >= 2:
                neighbor = item[0]
                edge_data = item[1] if isinstance(item[1], dict) else {'weight': float(item[1])}
                neighbors.append((neighbor, edge_data))
                continue

            if hasattr(item, 'to_id'):
                distance = float(getattr(item, 'distance', 1.0))
                neighbors.append((
                    item.to_id,
                    {
                        'weight': distance,
                        'distance': distance,
                        'capacity': int(getattr(item, 'capacity', 0) or 0),
                        'traffic_factor': float(getattr(item, 'traffic_factor', 1.0))
                    }
                ))

        return neighbors
    
    def _is_medical_facility(self, node: Any) -> bool:
        """Check if a node is a medical facility"""
        # This would need to be customized based on your node naming
        return str(node).startswith('F') and any(
            medical in str(node).lower() 
            for medical in ['hospital', 'medical', 'clinic']
        )

    def _is_edge_avoided(self, from_node: Any, to_node: Any, avoid_edges: Optional[Set[str]]) -> bool:
        if not avoid_edges:
            return False
        key = f"{from_node}-{to_node}"
        reverse_key = f"{to_node}-{from_node}"
        return key in avoid_edges or reverse_key in avoid_edges
    
    def _calculate_path_congestion(self, path: List, traffic_data: Dict) -> float:
        """Calculate average congestion along a path"""
        if not path or len(path) < 2:
            return 0
        
        total_congestion = 0
        for i in range(len(path) - 1):
            edge_key = (path[i], path[i+1])
            total_congestion += traffic_data.get(edge_key, 0)
        
        return total_congestion / (len(path) - 1)
    
    def _estimate_traffic(self, node1: Any, node2: Any) -> float:
        """Estimate traffic between two nodes based on their locations"""
        # Simplified traffic estimation
        # In real implementation, this would use historical data
        coords1 = self.coordinates.get(node1)
        coords2 = self.coordinates.get(node2)
        
        if not coords1 or not coords2:
            return 0
        
        # Higher traffic in central areas (arbitrary implementation)
        center_x, center_y = 31.24, 30.04  # Downtown Cairo
        dist_to_center1 = math.sqrt((coords1[0]-center_x)**2 + (coords1[1]-center_y)**2)
        dist_to_center2 = math.sqrt((coords2[0]-center_x)**2 + (coords2[1]-center_y)**2)
        
        # More central = more traffic
        avg_dist = (dist_to_center1 + dist_to_center2) / 2
        traffic_factor = max(0, 1 - avg_dist / 0.5)
        
        return traffic_factor * 0.5
    
    def _reconstruct_path(self, came_from: Dict, start: Any, goal: Any) -> List:
        """Reconstruct path from came_from dictionary"""
        path = [goal]
        current = goal
        while current != start:
            current = came_from[current]
            path.append(current)
        return path[::-1]
    
    def _combine_paths(self, forward_parent: Dict, backward_parent: Dict,
                      start: Any, goal: Any, meeting_point: Any) -> List:
        """Combine forward and backward paths for bidirectional A*"""
        # Forward path from start to meeting point
        forward_path = [meeting_point]
        current = meeting_point
        while current != start:
            current = forward_parent[current]
            forward_path.append(current)
        forward_path = forward_path[::-1]
        
        # Backward path from meeting point to goal
        backward_path = []
        current = meeting_point
        while current != goal:
            current = backward_parent[current]
            backward_path.append(current)
        
        return forward_path + backward_path
    
    def _get_frontier(self, g_scores: Dict, closed_set: Set) -> List:
        """Get frontier nodes (discovered but not explored)"""
        frontier = []
        for node, score in g_scores.items():
            if node not in closed_set and score < float('inf'):
                frontier.append(node)
        return frontier
