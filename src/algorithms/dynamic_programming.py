from typing import List, Dict, Tuple
import numpy as np
from ..core.data_loader import CairoTransportData

class DynamicProgramming:
    def __init__(self, data: CairoTransportData):
        self.data = data
        self.memo = {}
        
    def optimize_bus_schedules(self, buses: List[int], routes: List[List[int]], 
                               demands: List[int], max_hours: int = 18) -> Dict:
        """
        DP solution for optimal bus scheduling
        Time Complexity: O(n * max_hours)
        Space Complexity: O(n * max_hours)
        """
        n = len(buses)
        # dp[i][h] = max passengers served using first i buses with h hours
        dp = [[0] * (max_hours + 1) for _ in range(n + 1)]
        # Keep track of assignments
        assignments = [[[] for _ in range(max_hours + 1)] for _ in range(n + 1)]
        
        for i in range(1, n + 1):
            for h in range(max_hours + 1):
                # Option 1: Don't use bus i
                dp[i][h] = dp[i-1][h]
                assignments[i][h] = assignments[i-1][h].copy()
                
                # Option 2: Assign to route if within time limits
                for route_idx, (route, demand) in enumerate(zip(routes, demands)):
                    route_time = self._calculate_route_time(route)
                    
                    if route_time <= h:
                        new_demand = dp[i-1][h - route_time] + demand
                        if new_demand > dp[i][h]:
                            dp[i][h] = new_demand
                            assignments[i][h] = assignments[i-1][h - route_time].copy()
                            assignments[i][h].append((i-1, route_idx))
        
        # Reconstruct optimal schedule
        optimal_assignments = assignments[n][max_hours]
        
        return {
            "max_passengers_served": dp[n][max_hours],
            "bus_assignments": optimal_assignments,
            "total_hours_used": sum(self._calculate_route_time(routes[a[1]]) 
                                   for a in optimal_assignments)
        }
    
    def resource_allocation_road_maintenance(self, roads: List, budget: int) -> Dict:
        """
        DP solution for road maintenance resource allocation
        Knapsack-like problem: maximize road condition improvement within budget
        Time Complexity: O(n * budget)
        Space Complexity: O(n * budget)
        """
        n = len(roads)
        # dp[i][b] = max condition improvement with first i roads and budget b
        dp = [[0] * (budget + 1) for _ in range(n + 1)]
        # Track selected roads
        selected = [[[] for _ in range(budget + 1)] for _ in range(n + 1)]
        
        for i in range(1, n + 1):
            road = roads[i-1]
            improvement = 10 - road['condition']  # Maximum improvement possible
            cost = road['maintenance_cost']
            
            for b in range(budget + 1):
                # Don't select this road
                dp[i][b] = dp[i-1][b]
                selected[i][b] = selected[i-1][b].copy()
                
                # Select this road if budget allows
                if cost <= b:
                    new_value = dp[i-1][b - cost] + improvement
                    if new_value > dp[i][b]:
                        dp[i][b] = new_value
                        selected[i][b] = selected[i-1][b - cost].copy()
                        selected[i][b].append(road['id'])
        
        return {
            "max_improvement": dp[n][budget],
            "selected_roads": selected[n][budget],
            "total_cost": sum(roads[s-1]['maintenance_cost'] 
                            for s in selected[n][budget] if isinstance(s, int))
        }
    
    def optimize_transport_integration(self, metro_lines: List, bus_routes: List,
                                      transfer_points: List) -> Dict:
        """
        DP for optimizing integration between metro and bus networks
        Time Complexity: O(n * m)
        Space Complexity: O(n * m)
        """
        m, b = len(metro_lines), len(bus_routes)
        
        # dp[i][j] = optimal passenger flow using first i metro lines and j bus routes
        dp = [[0] * (b + 1) for _ in range(m + 1)]
        coverage = [[set() for _ in range(b + 1)] for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, b + 1):
                # Without current bus route
                dp[i][j] = dp[i][j-1]
                coverage[i][j] = coverage[i][j-1].copy()
                
                # With current bus route
                transfer_efficiency = self._calculate_transfer_efficiency(
                    metro_lines[i-1], bus_routes[j-1], transfer_points
                )
                
                if transfer_efficiency > 0:
                    new_flow = dp[i-1][j-1] + transfer_efficiency
                    if new_flow > dp[i][j]:
                        dp[i][j] = new_flow
                        coverage[i][j] = coverage[i-1][j-1].copy()
                        coverage[i][j].add((i-1, j-1))
        
        return {
            "max_passenger_flow": dp[m][b],
            "optimal_pairs": list(coverage[m][b]),
            "integration_score": dp[m][b] / (m * b) if m * b > 0 else 0
        }
    
    def memoized_route_planning(self, start, end, time_constraint: float = None) -> Dict:
        """
        Memoized version of route planning for improved performance
        """
        memo_key = f"{start}_{end}_{time_constraint}"
        
        if memo_key in self.memo:
            return self.memo[memo_key]
        
        def dp_route(current, time_left, visited):
            if current == end:
                return [], 0
            
            if time_left <= 0:
                return None, float('inf')
            
            best_path = None
            best_cost = float('inf')
            
            visited.add(current)
            
            for road in self.data.graph[current]:
                neighbor = road.to_id
                if neighbor in visited:
                    continue
                
                travel_time = road.distance  # Simplified
                
                if travel_time > time_left:
                    continue
                
                sub_path, sub_cost = dp_route(neighbor, time_left - travel_time, 
                                             visited)
                
                if sub_path is not None:
                    total_cost = road.distance + sub_cost
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_path = [current] + sub_path
            
            visited.remove(current)
            return best_path, best_cost
        
        path, cost = dp_route(start, time_constraint or float('inf'), set())
        result = {"path": path, "cost": cost}
        self.memo[memo_key] = result
        return result
    
    def _calculate_route_time(self, route: List) -> int:
        """Calculate time needed for a route"""
        return max(1, int(round(len(route) * 0.5)))  # 30 minutes per stop approximation
    
    def _calculate_transfer_efficiency(self, metro_line, bus_route, 
                                       transfer_points) -> float:
        """Calculate efficiency of metro-bus transfer"""
        metro_stops = set(metro_line.stations)
        bus_stops = set(bus_route.stops)
        
        common_stops = metro_stops.intersection(bus_stops)
        transfer_score = len(common_stops) * 100
        
        # Add bonus for designated transfer points
        for tp in transfer_points:
            if tp in common_stops:
                transfer_score += 50
                
        return transfer_score