import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple
from .models import *

class CairoTransportData:
    def __init__(self):
        self.neighborhoods: Dict[int, Neighborhood] = {}
        self.facilities: Dict[str, Facility] = {}
        self.roads: List[Road] = []
        self.potential_roads: List[Dict] = []
        self.traffic_patterns: Dict[str, TrafficPattern] = {}
        self.metro_lines: List[MetroLine] = []
        self.bus_routes: List[BusRoute] = []
        self.transport_demand: List[Tuple] = []
        self.graph = None
        
    def load_all_data(self):
        self._load_neighborhoods()
        self._load_facilities()
        self._load_roads()
        self._load_potential_roads()
        self._load_traffic_patterns()
        self._load_metro_lines()
        self._load_bus_routes()
        self._load_transport_demand()
        self._build_graph()

    def _load_potential_roads(self):
        self.potential_roads = [
            {"from_id": 1, "to_id": 2, "distance": 9.4, "construction_cost": 1200, "priority": 3},
            {"from_id": 2, "to_id": 4, "distance": 12.1, "construction_cost": 1500, "priority": 4},
            {"from_id": 3, "to_id": 8, "distance": 7.8, "construction_cost": 900, "priority": 5},
            {"from_id": 5, "to_id": 9, "distance": 5.7, "construction_cost": 850, "priority": 4},
            {"from_id": 6, "to_id": 11, "distance": 4.2, "construction_cost": 700, "priority": 3},
        ]

    def _load_traffic_patterns(self):
        self.traffic_patterns = {
            "1-3": TrafficPattern("1-3", 2800, 1800, 3200, 900),
            "2-5": TrafficPattern("2-5", 2600, 1700, 3000, 800),
            "3-5": TrafficPattern("3-5", 2400, 1600, 2900, 750),
            "3-9": TrafficPattern("3-9", 2200, 1500, 2600, 700),
            "8-10": TrafficPattern("8-10", 2100, 1400, 2500, 650),
            "F1-5": TrafficPattern("F1-5", 2500, 1900, 3000, 850),
        }

    def _load_metro_lines(self):
        self.metro_lines = [
            MetroLine("M1", "Line 1", ["Helwan", "Maadi", "Downtown Cairo", "Shubra"], 850000),
            MetroLine("M2", "Line 2", ["Giza", "Dokki", "Mohandessin", "Shubra"], 720000),
            MetroLine("M3", "Line 3", ["Cairo International Stadium", "Heliopolis", "Downtown Cairo"], 680000),
        ]

    def _load_bus_routes(self):
        self.bus_routes = [
            BusRoute("B1", ["Maadi", "Downtown Cairo", "Zamalek"], 18, 45000),
            BusRoute("B2", ["Nasr City", "Heliopolis", "Cairo International Airport"], 16, 52000),
            BusRoute("B3", ["Giza", "Dokki", "Mohandessin", "Downtown Cairo"], 20, 60000),
            BusRoute("B4", ["6th October City", "Sheikh Zayed", "Giza"], 12, 30000),
        ]

    def _load_transport_demand(self):
        self.transport_demand = [
            ("Maadi", "Downtown Cairo", 12000),
            ("Nasr City", "Heliopolis", 15000),
            ("Giza", "Downtown Cairo", 18000),
            ("6th October City", "Sheikh Zayed", 8000),
        ]
        
    def _load_neighborhoods(self):
        data = [
            (1, "Maadi", 250000, NodeType.RESIDENTIAL, 31.25, 29.96),
            (2, "Nasr City", 500000, NodeType.MIXED, 31.34, 30.06),
            (3, "Downtown Cairo", 100000, NodeType.BUSINESS, 31.24, 30.04),
            (4, "New Cairo", 300000, NodeType.RESIDENTIAL, 31.47, 30.03),
            (5, "Heliopolis", 200000, NodeType.MIXED, 31.32, 30.09),
            (6, "Zamalek", 50000, NodeType.RESIDENTIAL, 31.22, 30.06),
            (7, "6th October City", 400000, NodeType.MIXED, 30.98, 29.93),
            (8, "Giza", 550000, NodeType.MIXED, 31.21, 29.99),
            (9, "Mohandessin", 180000, NodeType.BUSINESS, 31.20, 30.05),
            (10, "Dokki", 220000, NodeType.MIXED, 31.21, 30.03),
            (11, "Shubra", 450000, NodeType.RESIDENTIAL, 31.24, 30.11),
            (12, "Helwan", 350000, NodeType.INDUSTRIAL, 31.33, 29.85),
            (13, "New Administrative Capital", 50000, NodeType.GOVERNMENT, 31.80, 30.02),
            (14, "Al Rehab", 120000, NodeType.RESIDENTIAL, 31.49, 30.06),
            (15, "Sheikh Zayed", 150000, NodeType.RESIDENTIAL, 30.94, 30.01)
        ]
        for n in data:
            self.neighborhoods[n[0]] = Neighborhood(*n)
            
    def _load_facilities(self):
        data = [
            ("F1", "Cairo International Airport", FacilityType.AIRPORT, 31.41, 30.11),
            ("F2", "Ramses Railway Station", FacilityType.TRANSIT_HUB, 31.25, 30.06),
            ("F3", "Cairo University", FacilityType.EDUCATION, 31.21, 30.03),
            ("F4", "Al-Azhar University", FacilityType.EDUCATION, 31.26, 30.05),
            ("F5", "Egyptian Museum", FacilityType.TOURISM, 31.23, 30.05),
            ("F6", "Cairo International Stadium", FacilityType.SPORTS, 31.30, 30.07),
            ("F7", "Smart Village", FacilityType.BUSINESS, 30.97, 30.07),
            ("F8", "Cairo Festival City", FacilityType.COMMERCIAL, 31.40, 30.03),
            ("F9", "Qasr El Aini Hospital", FacilityType.MEDICAL, 31.23, 30.03),
            ("F10", "Maadi Military Hospital", FacilityType.MEDICAL, 31.25, 29.95)
        ]
        for f in data:
            self.facilities[f[0]] = Facility(*f)
    
    def _load_roads(self):
        data = [
            (1, 3, 8.5, 3000, 7), (1, 8, 6.2, 2500, 6),
            (2, 3, 5.9, 2800, 8), (2, 5, 4.0, 3200, 9),
            (3, 5, 6.1, 3500, 7), (3, 6, 3.2, 2000, 8),
            (3, 9, 4.5, 2600, 6), (3, 10, 3.8, 2400, 7),
            (4, 2, 15.2, 3800, 9), (4, 14, 5.3, 3000, 10),
            (5, 11, 7.9, 3100, 7), (6, 9, 2.2, 1800, 8),
            (7, 8, 24.5, 3500, 8), (7, 15, 9.8, 3000, 9),
            (8, 10, 3.3, 2200, 7), (8, 12, 14.8, 2600, 5),
            (9, 10, 2.1, 1900, 7), (10, 11, 8.7, 2400, 6),
            (11, "F2", 3.6, 2200, 7), (12, 1, 12.7, 2800, 6),
            (13, 4, 45.0, 4000, 10), (14, 13, 35.5, 3800, 9),
            (15, 7, 9.8, 3000, 9), ("F1", 5, 7.5, 3500, 9),
            ("F1", 2, 9.2, 3200, 8), ("F2", 3, 2.5, 2000, 7),
            (3, "F9", 2.0, 2000, 9), (1, "F10", 4.5, 2200, 8),
            ("F7", 15, 8.3, 2800, 8), ("F8", 4, 6.1, 3000, 9)
        ]
        for r in data:
            self.roads.append(Road(r[0], r[1], r[2], r[3], r[4]))
    
    # Continue with other data loading methods...
    
    def _build_graph(self):
        """Build adjacency list representation of the transportation network"""
        self.graph = defaultdict(list)
        
        # Add road connections
        for road in self.roads:
            self.graph[road.from_id].append(road)
            # Add reverse direction for undirected graph
            reverse_road = Road(road.to_id, road.from_id, 
                               road.distance, road.capacity, road.condition)
            self.graph[road.to_id].append(reverse_road)