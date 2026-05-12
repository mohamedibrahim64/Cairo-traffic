"""
Integration Validation Script
Validates that all components work together correctly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.data_loader import CairoTransportData
from src.core.graph import Graph
from src.algorithms.shortest_path import ShortestPath
from src.algorithms.astar import AStarSearch
from src.algorithms.mst import MinimumSpanningTree
from src.algorithms.dynamic_programming import DynamicProgramming
from src.algorithms.greedy import GreedyTrafficOptimizer
from src.simulation.traffic_simulator import TrafficSimulator, TrafficEvent
from src.simulation.emergency_response import EmergencyDispatchCenter, EmergencyCall, EmergencyType, EmergencySeverity
from src.visualization.network_plotter import NetworkPlotter
from src.visualization.comparison_visualizer import ComparisonVisualizer
import time


class IntegrationValidator:
    """Validates all system components"""
    
    def __init__(self):
        self.results = []
        self.data = None
        self.start_time = None
        self.total_time = None
    
    def log(self, component, status, message=""):
        """Log validation result"""
        result = {
            'component': component,
            'status': '✓ PASS' if status else '✗ FAIL',
            'message': message
        }
        self.results.append(result)
        print(f"{result['status']} {component}: {message}")

    def _road_exists(self, a, b):
        for road in self.data.roads:
            if (road.from_id == a and road.to_id == b) or \
               (road.from_id == b and road.to_id == a):
                return True
        return False

    def _path_uses_roads(self, path):
        if not path:
            return True
        for i in range(len(path) - 1):
            if not self._road_exists(path[i], path[i + 1]):
                return False
        return True
    
    def validate_all(self):
        """Run all validation checks"""
        self.start_time = time.time()
        
        print("\n" + "="*80)
        print("CAIRO TRANSPORTATION SYSTEM - INTEGRATION VALIDATION")
        print("="*80 + "\n")
        
        # Phase 1: Data Loading
        print("PHASE 1: Data Loading and Initialization")
        print("-"*80)
        self.validate_data_loading()
        
        # Phase 2: Core Algorithms
        print("\nPHASE 2: Core Algorithm Validation")
        print("-"*80)
        self.validate_shortest_path()
        self.validate_astar()
        self.validate_mst()
        self.validate_dp()
        self.validate_greedy()
        
        # Phase 3: Simulation Systems
        print("\nPHASE 3: Simulation Systems Validation")
        print("-"*80)
        self.validate_traffic_simulator()
        self.validate_emergency_dispatch()
        
        # Phase 4: Integration Tests
        print("\nPHASE 4: Integration Tests")
        print("-"*80)
        self.validate_integrated_workflow()
        
        # Phase 5: Visualization
        print("\nPHASE 5: Visualization Module Validation")
        print("-"*80)
        self.validate_visualization()
        
        self.total_time = time.time() - self.start_time
        self.print_summary()
    
    def validate_data_loading(self):
        """Validate data loading"""
        try:
            self.data = CairoTransportData()
            self.data.load_all_data()
            
            # Check neighborhoods
            assert len(self.data.neighborhoods) == 15, "Should have 15 neighborhoods"
            self.log("Data: Neighborhoods", True, f"Loaded {len(self.data.neighborhoods)} neighborhoods")
            
            # Check facilities
            assert len(self.data.facilities) == 10, "Should have 10 facilities"
            self.log("Data: Facilities", True, f"Loaded {len(self.data.facilities)} facilities")
            
            # Check roads
            assert len(self.data.roads) > 0, "Should have roads"
            self.log("Data: Roads", True, f"Loaded {len(self.data.roads)} roads")
            
            # Check graph
            assert self.data.graph is not None, "Graph should be built"
            self.log("Data: Graph Construction", True, f"Graph built with {len(self.data.graph)} nodes")
            
            # Check traffic patterns
            assert len(self.data.traffic_patterns) > 0, "Should have traffic patterns"
            self.log("Data: Traffic Patterns", True, f"Loaded {len(self.data.traffic_patterns)} patterns")

            # Check provided dataset sizes
            assert len(self.data.potential_roads) == 15, "Should have 15 potential roads"
            self.log("Data: Potential Roads", True, "Loaded 15 potential roads")
            assert len(self.data.traffic_patterns) == 28, "Should have 28 traffic patterns"
            self.log("Data: Traffic Patterns (Full)", True, "Loaded 28 patterns")
            assert len(self.data.metro_lines) == 3, "Should have 3 metro lines"
            self.log("Data: Metro Lines", True, "Loaded 3 metro lines")
            assert len(self.data.bus_routes) == 10, "Should have 10 bus routes"
            self.log("Data: Bus Routes", True, "Loaded 10 bus routes")
            assert len(self.data.transport_demand) == 17, "Should have 17 demand entries"
            self.log("Data: Transport Demand", True, "Loaded 17 demand entries")
            
        except Exception as e:
            self.log("Data Loading", False, str(e))
    
    def validate_shortest_path(self):
        """Validate shortest path algorithm"""
        try:
            sp = ShortestPath(self.data)
            
            # Test basic path finding
            path, distance = sp.dijkstra(1, 3, 10)
            assert isinstance(path, list), "Path should be list"
            assert isinstance(distance, (int, float)), "Distance should be numeric"
            assert self._path_uses_roads(path), "Dijkstra path should follow roads"
            self.log("Dijkstra: Basic Routing", True, f"Path found: {path}, Distance: {distance:.2f} km")
            
            # Test with different time
            path_peak, distance_peak = sp.dijkstra(1, 3, 17)
            assert distance_peak > 0, "Peak hour path should have positive distance"
            assert self._path_uses_roads(path_peak), "Peak-hour path should follow roads"
            self.log("Dijkstra: Time-Aware", True, f"Peak hour distance: {distance_peak:.2f} km")
            
            # Test memoization
            path_memo, distance_memo = sp.dijkstra(1, 3, 10)
            assert distance_memo == distance, "Memoized result should match"
            self.log("Dijkstra: Memoization", True, "Cache working correctly")
            
        except Exception as e:
            self.log("Dijkstra Algorithm", False, str(e))
    
    def validate_astar(self):
        """Validate A* algorithm"""
        try:
            coords = {}
            for nid, n in self.data.neighborhoods.items():
                coords[nid] = (n.x, n.y)
            for fid, f in self.data.facilities.items():
                coords[fid] = (f.x, f.y)
            
            astar = AStarSearch(self.data.graph, coords)
            
            # Test basic path finding
            result = astar.find_path(1, 3)
            assert result['success'], "Path should be found"
            assert len(result['path']) > 0, "Path should not be empty"
            assert self._path_uses_roads(result['path']), "A* path should follow roads"
            self.log("A*: Basic Emergency Routing", True, f"Found path: {result['path']}")
            
            # Test with priority
            result_priority = astar.find_path(1, 'F9', emergency_priority=3)
            assert result_priority['success'], "Priority routing should work"
            self.log("A*: Priority Routing", True, f"Emergency route computed")
            
            # Test node exploration efficiency
            assert result['nodes_explored'] > 0, "Should explore nodes"
            self.log("A*: Efficiency", True, f"Nodes explored: {result['nodes_explored']}")
            
        except Exception as e:
            self.log("A* Algorithm", False, str(e))
    
    def validate_mst(self):
        """Validate MST algorithm"""
        try:
            mst = MinimumSpanningTree(self.data)
            
            # Test MST generation
            mst_edges = mst.kruskal_mst()
            assert len(mst_edges) > 0, "MST should have edges"
            self.log("MST: Generation", True, f"Generated {len(mst_edges)} edges")
            
            # Test with critical facility prioritization
            mst_critical = mst.kruskal_mst(prioritize_critical=True)
            assert len(mst_critical) > 0, "MST with priority should have edges"
            self.log("MST: Critical Facility Prioritization", True, f"Priority MST has {len(mst_critical)} edges")
            
            # Test cost effectiveness
            metrics = mst.calculate_cost_effectiveness()
            assert 'total_cost' in metrics, "Metrics should include cost"
            self.log("MST: Cost Analysis", True, f"Total cost: {metrics['total_cost']:.0f} Million EGP")
            
        except Exception as e:
            self.log("MST Algorithm", False, str(e))
    
    def validate_dp(self):
        """Validate dynamic programming"""
        try:
            dp = DynamicProgramming(self.data)
            
            # Test bus scheduling
            buses = [1, 2, 3]
            routes = [[1, 2, 3], [3, 4, 5], [5, 6, 7]]
            demands = [100, 150, 200]
            
            result = dp.optimize_bus_schedules(buses, routes, demands)
            assert 'max_passengers_served' in result, "Should return passengers"
            self.log("DP: Bus Scheduling", True, f"Max passengers: {result['max_passengers_served']}")
            
            # Test resource allocation
            roads = [
                {'id': 1, 'condition': 5, 'maintenance_cost': 10},
                {'id': 2, 'condition': 6, 'maintenance_cost': 15},
            ]
            result_maint = dp.resource_allocation_road_maintenance(roads, budget=30)
            assert 'max_improvement' in result_maint, "Should return improvement"
            self.log("DP: Road Maintenance", True, f"Max improvement: {result_maint['max_improvement']}")
            
        except Exception as e:
            self.log("Dynamic Programming", False, str(e))
    
    def validate_greedy(self):
        """Validate greedy algorithms"""
        try:
            greedy = GreedyTrafficOptimizer(self.data)
            
            # Test signal optimization
            intersections = [1, 2, 3]
            result = greedy.optimize_traffic_signals(intersections)
            assert 'signal_phases' in result, "Should return signal phases"
            self.log("Greedy: Traffic Signal Optimization", True, f"Optimized {len(result['signal_phases'])} intersections")
            
            # Test emergency preemption
            emergencies = [{'type': 'critical', 'path': [1, 2, 3], 'response_time': 5}]
            signals = {1: {'N': 30, 'S': 30, 'E': 20, 'W': 20}}
            result_emerg = greedy.emergency_vehicle_preemption(emergencies, signals)
            assert result_emerg is not None, "Should handle emergency preemption"
            self.log("Greedy: Emergency Preemption", True, "Emergency signals adjusted")
            
        except Exception as e:
            self.log("Greedy Algorithm", False, str(e))
    
    def validate_traffic_simulator(self):
        """Validate traffic simulator"""
        try:
            simulator = TrafficSimulator(self.data)
            
            # Test single step
            stats = simulator.simulate_step(10)
            assert 'hour' in stats, "Should have hour"
            assert 'avg_congestion' in stats, "Should have congestion"
            self.log("Simulator: Single Step", True, f"Congestion at 10 AM: {stats['avg_congestion']:.2f}")
            
            # Test period
            results = simulator.simulate_period(0, 24)
            assert len(results['hourly_stats']) == 24, "Should simulate 24 hours"
            self.log("Simulator: 24-Hour Period", True, f"Peak congestion: {results['daily_summary']['peak_congestion_level']:.2f}")
            
            # Test events
            event = TrafficEvent('E1', (1, 3), 'accident', 5, 10, 2)
            simulator.apply_event(event)
            assert len(simulator.events) > 0, "Event should be added"
            self.log("Simulator: Traffic Events", True, "Accident event processed")
            
        except Exception as e:
            self.log("Traffic Simulator", False, str(e))
    
    def validate_emergency_dispatch(self):
        """Validate emergency dispatch"""
        try:
            dispatch = EmergencyDispatchCenter(self.data)
            
            # Check vehicles
            assert len(dispatch.vehicles) > 0, "Should have vehicles"
            self.log("Emergency: Vehicle Fleet", True, f"Deployed {len(dispatch.vehicles)} vehicles")
            
            # Create call
            call = EmergencyCall('E1', EmergencyType.MEDICAL, 1, EmergencySeverity.HIGH)
            dispatch.receive_call(call)
            assert len(dispatch.active_calls) > 0, "Call should be received"
            self.log("Emergency: Call Reception", True, "Emergency call received")
            
            # Get status
            status = dispatch.get_system_status()
            assert status['total_vehicles'] > 0, "Should have status"
            self.log("Emergency: System Status", True, f"Available: {status['available_vehicles']}/{status['total_vehicles']}")
            
            # Get metrics
            metrics = dispatch.get_performance_metrics()
            assert 'avg_response_time_minutes' in metrics, "Should have metrics"
            self.log("Emergency: Performance Metrics", True, f"Response time tracking enabled")
            
        except Exception as e:
            self.log("Emergency Dispatch", False, str(e))
    
    def validate_integrated_workflow(self):
        """Validate integrated workflow"""
        try:
            # Full workflow
            data = CairoTransportData()
            data.load_all_data()
            
            # Shortest path
            sp = ShortestPath(data)
            path, _ = sp.dijkstra(1, 3)
            assert len(path) > 0, "Shortest path should work"
            
            # MST
            mst = MinimumSpanningTree(data)
            mst_edges = mst.kruskal_mst()
            assert len(mst_edges) > 0, "MST should work"
            
            # Traffic sim
            sim = TrafficSimulator(data)
            stats = sim.simulate_step(10)
            assert 'hour' in stats, "Traffic sim should work"
            
            # Emergency
            dispatch = EmergencyDispatchCenter(data)
            call = EmergencyCall('E1', EmergencyType.MEDICAL, 1, EmergencySeverity.HIGH)
            dispatch.receive_call(call)
            assert len(dispatch.active_calls) > 0, "Emergency should work"
            
            self.log("Integration: Full Workflow", True, "All components working together")
            
        except Exception as e:
            self.log("Integration Workflow", False, str(e))
    
    def validate_visualization(self):
        """Validate visualization modules"""
        try:
            # Network plotter
            plotter = NetworkPlotter(self.data)
            assert plotter.G is not None, "NetworkX graph should be built"
            self.log("Visualization: Network Plotter", True, "Network graph initialized")
            
            # Comparison visualizer
            comparator = ComparisonVisualizer()
            assert comparator is not None, "Comparison visualizer initialized"
            self.log("Visualization: Comparison Visualizer", True, "Comparator initialized")
            
        except Exception as e:
            self.log("Visualization", False, str(e))
    
    def print_summary(self):
        """Print validation summary"""
        passed = sum(1 for r in self.results if '✓' in r['status'])
        failed = sum(1 for r in self.results if '✗' in r['status'])
        
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"\nTotal Checks: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        print(f"Total Time: {self.total_time:.2f} seconds")
        
        if failed == 0:
            print("\n✓ ALL VALIDATIONS PASSED - SYSTEM READY FOR PRODUCTION")
        else:
            print(f"\n✗ {failed} VALIDATION(S) FAILED - REVIEW ABOVE")
        
        print("\n" + "="*80)


def main():
    """Run integration validation"""
    validator = IntegrationValidator()
    validator.validate_all()


if __name__ == '__main__':
    main()
