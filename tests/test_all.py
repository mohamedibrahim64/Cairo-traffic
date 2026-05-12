"""
Comprehensive Test Suite for Cairo Transportation System
Tests all major algorithms and components
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.data_loader import CairoTransportData
from src.core.graph import Graph
from src.algorithms.shortest_path import ShortestPath
from src.algorithms.mst import MinimumSpanningTree
from src.algorithms.astar import AStarSearch
from src.algorithms.greedy import GreedyTrafficOptimizer
from src.algorithms.dynamic_programming import DynamicProgramming
from src.simulation.traffic_simulator import TrafficSimulator, TrafficEvent
from src.simulation.emergency_response import EmergencyDispatchCenter, EmergencyCall, EmergencyType, EmergencySeverity


class TestGraphStructure(unittest.TestCase):
    """Test graph data structure"""

    def setUp(self):
        self.graph = Graph(directed=False)

    def test_add_node(self):
        """Test adding nodes to graph"""
        self.graph.add_node(1, x=31.25, y=29.96)
        self.assertEqual(1 in self.graph.nodes, True)

    def test_add_edge(self):
        """Test adding edges to graph"""
        self.graph.add_node(1)
        self.graph.add_node(2)
        self.graph.add_edge(1, 2, weight=5.0)
        self.assertTrue(self.graph.has_edge(1, 2))

    def test_get_neighbors(self):
        """Test getting node neighbors"""
        self.graph.add_node(1)
        self.graph.add_node(2)
        self.graph.add_node(3)
        self.graph.add_edge(1, 2)
        self.graph.add_edge(1, 3)
        
        neighbors = self.graph.get_neighbors(1)
        self.assertEqual(len(neighbors), 2)

    def test_node_count(self):
        """Test node counting"""
        self.graph.add_node(1)
        self.graph.add_node(2)
        self.graph.add_node(3)
        self.assertEqual(self.graph.node_count, 3)

    def test_edge_weight(self):
        """Test edge weight retrieval"""
        self.graph.add_node(1)
        self.graph.add_node(2)
        self.graph.add_edge(1, 2, weight=7.5)
        
        weight = self.graph.get_edge_weight(1, 2)
        self.assertEqual(weight, 7.5)


class TestDataLoader(unittest.TestCase):
    """Test data loading"""

    def setUp(self):
        self.data = CairoTransportData()

    def test_load_neighborhoods(self):
        """Test neighborhood data loading"""
        self.data._load_neighborhoods()
        self.assertGreater(len(self.data.neighborhoods), 0)
        self.assertIn(1, self.data.neighborhoods)

    def test_load_facilities(self):
        """Test facility data loading"""
        self.data._load_facilities()
        self.assertGreater(len(self.data.facilities), 0)
        self.assertIn('F1', self.data.facilities)

    def test_load_roads(self):
        """Test road data loading"""
        self.data._load_roads()
        self.assertGreater(len(self.data.roads), 0)
        
        # Check first road
        first_road = self.data.roads[0]
        self.assertEqual(first_road.from_id, 1)
        self.assertEqual(first_road.to_id, 3)

    def test_load_all_data(self):
        """Test loading all data"""
        self.data.load_all_data()
        
        self.assertGreater(len(self.data.neighborhoods), 0)
        self.assertGreater(len(self.data.facilities), 0)
        self.assertGreater(len(self.data.roads), 0)
        self.assertIsNotNone(self.data.graph)

    def test_pdf_dataset_counts(self):
        """Validate dataset sizes against the provided PDFs"""
        self.data.load_all_data()
        self.assertGreaterEqual(len(self.data.roads), 28)
        self.assertEqual(len(self.data.potential_roads), 15)
        self.assertEqual(len(self.data.traffic_patterns), 28)
        self.assertEqual(len(self.data.metro_lines), 3)
        self.assertEqual(len(self.data.bus_routes), 10)
        self.assertEqual(len(self.data.transport_demand), 17)


class TestShortestPathAlgorithm(unittest.TestCase):
    """Test shortest path algorithms"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        self.sp = ShortestPath(self.data)

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

    def test_dijkstra_exists(self):
        """Test that Dijkstra's algorithm runs"""
        # Test with simple start and end
        path, distance = self.sp.dijkstra(1, 3, time_hour=10)
        
        self.assertIsInstance(path, list)
        self.assertIsInstance(distance, (int, float))

    def test_dijkstra_valid_path(self):
        """Test that Dijkstra returns valid path"""
        path, distance = self.sp.dijkstra(1, 3)
        
        if path:  # Path might be empty if unreachable
            self.assertEqual(path[0], 1)
            self.assertEqual(path[-1], 3)

    def test_dijkstra_uses_roads(self):
        """Dijkstra path should follow defined roads"""
        path, _ = self.sp.dijkstra(1, 3)
        self.assertTrue(self._path_uses_roads(path))

    def test_dijkstra_avoid_roads(self):
        """Dijkstra should avoid blocked roads when provided"""
        path, _ = self.sp.dijkstra(1, 3, avoid_roads=["1-3"])
        self.assertTrue(path)
        for i in range(len(path) - 1):
            self.assertNotEqual(f"{path[i]}-{path[i+1]}", "1-3")

    def test_dijkstra_zero_distance_same_node(self):
        """Test Dijkstra with same start and end"""
        path, distance = self.sp.dijkstra(1, 1)
        
        # Could be empty or [1] depending on implementation
        self.assertIsInstance(path, list)

    def test_astar_exists(self):
        """Test that A* algorithm runs"""
        path, distance = self.sp.a_star_search(1, 3)
        
        self.assertIsInstance(path, list)
        self.assertIsInstance(distance, (int, float))

    def test_astar_uses_roads(self):
        """A* path should follow defined roads"""
        path, _ = self.sp.a_star_search(1, 3)
        self.assertTrue(self._path_uses_roads(path))

    def test_time_varying_shortest_path(self):
        """Time-varying routing should return a recommended route"""
        result = self.sp.time_varying_shortest_path(1, 3, 10)
        self.assertIn('recommended_route', result)
        self.assertTrue(self._path_uses_roads(result.get('recommended_route', [])))


class TestMinimumSpanningTree(unittest.TestCase):
    """Test MST algorithms"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        self.mst = MinimumSpanningTree(self.data)

    def test_kruskal_mst_exists(self):
        """Test that Kruskal's algorithm runs"""
        mst = self.mst.kruskal_mst()
        
        self.assertIsInstance(mst, list)
        self.assertGreater(len(mst), 0)

    def test_kruskal_mst_edges(self):
        """Test that MST produces valid edges"""
        mst = self.mst.kruskal_mst()
        
        for edge in mst:
            # Each edge should have at least 4 elements
            # (from, to, weight, type, data)
            self.assertGreaterEqual(len(edge), 3)

    def test_mst_cost_effectiveness(self):
        """Test cost effectiveness calculation"""
        self.mst.kruskal_mst()
        metrics = self.mst.calculate_cost_effectiveness()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_cost', metrics)


class TestAStarSearch(unittest.TestCase):
    """Test A* search"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        
        # Get coordinates
        coords = {}
        for nid, n in self.data.neighborhoods.items():
            coords[nid] = (n.x, n.y)
        for fid, f in self.data.facilities.items():
            coords[fid] = (f.x, f.y)
        
        self.astar = AStarSearch(self.data.graph, coords)

    def _graph_has_edge(self, a, b):
        if a not in self.data.graph:
            return False
        for road in self.data.graph[a]:
            if road.to_id == b:
                return True
        return False

    def _path_uses_graph_edges(self, path):
        if not path:
            return True
        for i in range(len(path) - 1):
            if not self._graph_has_edge(path[i], path[i + 1]):
                return False
        return True

    def test_astar_find_path(self):
        """Test A* path finding"""
        result = self.astar.find_path(1, 3)
        
        self.assertIsInstance(result, dict)
        self.assertIn('path', result)
        self.assertIn('distance', result)
        self.assertIn('success', result)

    def test_astar_path_edges_valid(self):
        """A* path should follow graph edges"""
        result = self.astar.find_path(1, 3)
        self.assertTrue(self._path_uses_graph_edges(result.get('path', [])))


class TestGreedyAlgorithm(unittest.TestCase):
    """Test greedy algorithms"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        self.greedy = GreedyTrafficOptimizer(self.data)

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

    def test_traffic_signal_optimization(self):
        """Test traffic signal optimization"""
        intersections = [1, 2, 3]
        result = self.greedy.optimize_traffic_signals(intersections)
        
        self.assertIsInstance(result, dict)
        self.assertIn('signal_phases', result)

    def test_emergency_preemption(self):
        """Test emergency vehicle preemption"""
        active_emergencies = [
            {'type': 'critical', 'path': [1, 2, 3], 'response_time': 5}
        ]
        current_signals = {1: {'N': 30, 'S': 30, 'E': 20, 'W': 20}}
        
        result = self.greedy.emergency_vehicle_preemption(
            active_emergencies, current_signals
        )
        
        self.assertIsInstance(result, dict)

    def test_greedy_route_uses_roads(self):
        """Greedy route should follow defined roads (with fallback if needed)"""
        result = self.greedy.greedy_route_recommendation(1, 3)
        self.assertTrue(self._path_uses_roads(result.get('path', [])))


class TestDynamicProgramming(unittest.TestCase):
    """Test dynamic programming solutions"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        self.dp = DynamicProgramming(self.data)

    def test_bus_schedule_optimization(self):
        """Test bus schedule optimization"""
        buses = [1, 2, 3]
        routes = [[1, 2, 3], [3, 4, 5], [5, 6, 7]]
        demands = [100, 150, 200]
        
        result = self.dp.optimize_bus_schedules(buses, routes, demands)
        
        self.assertIsInstance(result, dict)
        self.assertIn('max_passengers_served', result)


class TestTrafficSimulator(unittest.TestCase):
    """Test traffic simulator"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        self.simulator = TrafficSimulator(self.data)

    def test_simulate_step(self):
        """Test single hour simulation"""
        stats = self.simulator.simulate_step(10)
        
        self.assertIsInstance(stats, dict)
        self.assertIn('hour', stats)
        self.assertIn('total_traffic', stats)
        self.assertIn('avg_congestion', stats)

    def test_simulate_period(self):
        """Test period simulation"""
        results = self.simulator.simulate_period(0, 24)
        
        self.assertIsInstance(results, dict)
        self.assertIn('hourly_stats', results)
        self.assertEqual(len(results['hourly_stats']), 24)

    def test_apply_traffic_event(self):
        """Test traffic event application"""
        event = TrafficEvent('E1', (1, 3), 'accident', 5, 10, 2)
        self.simulator.apply_event(event)
        
        self.assertEqual(len(self.simulator.events), 1)

    def test_congestion_report(self):
        """Test congestion report generation"""
        self.simulator.simulate_step(10)
        report = self.simulator.get_congestion_report(10)
        
        self.assertIsInstance(report, dict)
        self.assertIn('congestion_level', report)
        self.assertIn('bottlenecks', report)


class TestEmergencyResponse(unittest.TestCase):
    """Test emergency response system"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()
        self.dispatch = EmergencyDispatchCenter(self.data)

    def test_dispatch_center_initialization(self):
        """Test dispatch center initialization"""
        self.assertGreater(len(self.dispatch.vehicles), 0)

    def test_receive_emergency_call(self):
        """Test receiving emergency call"""
        call = EmergencyCall(
            'C1', EmergencyType.MEDICAL, 1,
            EmergencySeverity.HIGH, "Heart attack"
        )
        
        self.dispatch.receive_call(call)
        
        self.assertGreater(len(self.dispatch.active_calls), 0)

    def test_system_status(self):
        """Test getting system status"""
        status = self.dispatch.get_system_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('total_vehicles', status)
        self.assertIn('available_vehicles', status)

    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        metrics = self.dispatch.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('avg_response_time_minutes', metrics)
        self.assertIn('avg_distance_km', metrics)


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def setUp(self):
        self.data = CairoTransportData()
        self.data.load_all_data()

    def test_full_workflow(self):
        """Test complete workflow"""
        # Load data
        self.assertIsNotNone(self.data.graph)
        
        # Run shortest path
        sp = ShortestPath(self.data)
        path, distance = sp.dijkstra(1, 3)
        self.assertIsInstance(path, list)
        
        # Run MST
        mst = MinimumSpanningTree(self.data)
        mst_result = mst.kruskal_mst()
        self.assertGreater(len(mst_result), 0)
        
        # Run simulation
        sim = TrafficSimulator(self.data)
        stats = sim.simulate_step(10)
        self.assertIn('hour', stats)

    def test_emergency_dispatch_workflow(self):
        """Test emergency dispatch workflow"""
        dispatch = EmergencyDispatchCenter(self.data)
        
        # Create emergency call
        call = EmergencyCall(
            'E1', EmergencyType.MEDICAL, 1,
            EmergencySeverity.CRITICAL, "Emergency"
        )
        
        # Receive call
        dispatch.receive_call(call)
        
        # Check status
        status = dispatch.get_system_status()
        self.assertGreater(status['active_calls'], 0)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGraphStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestShortestPathAlgorithm))
    suite.addTests(loader.loadTestsFromTestCase(TestMinimumSpanningTree))
    suite.addTests(loader.loadTestsFromTestCase(TestAStarSearch))
    suite.addTests(loader.loadTestsFromTestCase(TestGreedyAlgorithm))
    suite.addTests(loader.loadTestsFromTestCase(TestDynamicProgramming))
    suite.addTests(loader.loadTestsFromTestCase(TestTrafficSimulator))
    suite.addTests(loader.loadTestsFromTestCase(TestEmergencyResponse))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_tests()
    exit(0 if result.wasSuccessful() else 1)
