import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple
from .models import *

class CairoTransportData:
    def __init__(self):
        self.neighborhoods: Dict[int, Neighborhood] = {}
        self.facilities: Dict[str, Facility] = {}
        self.roads: List[Road] = []
        self.access_roads: List[Road] = []
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
        self._ensure_facility_access_roads()
        self._load_potential_roads()
        self._load_traffic_patterns()
        self._load_metro_lines()
        self._load_bus_routes()
        self._load_transport_demand()
        self._build_graph()

    def _load_potential_roads(self):
        # Data from Project_Provided_Data.pdf
        self.potential_roads = [
            {"from_id": 1, "to_id": 4, "distance": 22.8, "estimated_capacity": 4000, "construction_cost": 450},
            {"from_id": 1, "to_id": 14, "distance": 25.3, "estimated_capacity": 3800, "construction_cost": 500},
            {"from_id": 2, "to_id": 13, "distance": 48.2, "estimated_capacity": 4500, "construction_cost": 950},
            {"from_id": 3, "to_id": 13, "distance": 56.7, "estimated_capacity": 4500, "construction_cost": 1100},
            {"from_id": 5, "to_id": 4, "distance": 16.8, "estimated_capacity": 3500, "construction_cost": 320},
            {"from_id": 6, "to_id": 8, "distance": 7.5, "estimated_capacity": 2500, "construction_cost": 150},
            {"from_id": 7, "to_id": 13, "distance": 82.3, "estimated_capacity": 4000, "construction_cost": 1600},
            {"from_id": 9, "to_id": 11, "distance": 6.9, "estimated_capacity": 2800, "construction_cost": 140},
            {"from_id": 10, "to_id": "F7", "distance": 27.4, "estimated_capacity": 3200, "construction_cost": 550},
            {"from_id": 11, "to_id": 13, "distance": 62.1, "estimated_capacity": 4200, "construction_cost": 1250},
            {"from_id": 12, "to_id": 14, "distance": 30.5, "estimated_capacity": 3600, "construction_cost": 610},
            {"from_id": 14, "to_id": 5, "distance": 18.2, "estimated_capacity": 3300, "construction_cost": 360},
            {"from_id": 15, "to_id": 9, "distance": 22.7, "estimated_capacity": 3000, "construction_cost": 450},
            {"from_id": "F1", "to_id": 13, "distance": 40.2, "estimated_capacity": 4000, "construction_cost": 800},
            {"from_id": "F7", "to_id": 9, "distance": 26.8, "estimated_capacity": 3200, "construction_cost": 540},
        ]

    def _load_traffic_patterns(self):
        # Data from Project_Provided_Data.pdf
        self.traffic_patterns = {
            "1-3": TrafficPattern("1-3", 2800, 1500, 2600, 800),
            "1-8": TrafficPattern("1-8", 2200, 1200, 2100, 600),
            "2-3": TrafficPattern("2-3", 2700, 1400, 2500, 700),
            "2-5": TrafficPattern("2-5", 3000, 1600, 2800, 650),
            "3-5": TrafficPattern("3-5", 3200, 1700, 3100, 800),
            "3-6": TrafficPattern("3-6", 1800, 1400, 1900, 500),
            "3-9": TrafficPattern("3-9", 2400, 1300, 2200, 550),
            "3-10": TrafficPattern("3-10", 2300, 1200, 2100, 500),
            "4-2": TrafficPattern("4-2", 3600, 1800, 3300, 750),
            "4-14": TrafficPattern("4-14", 2800, 1600, 2600, 600),
            "5-11": TrafficPattern("5-11", 2900, 1500, 2700, 650),
            "6-9": TrafficPattern("6-9", 1700, 1300, 1800, 450),
            "7-8": TrafficPattern("7-8", 3200, 1700, 3000, 700),
            "7-15": TrafficPattern("7-15", 2800, 1500, 2600, 600),
            "8-10": TrafficPattern("8-10", 2000, 1100, 1900, 450),
            "8-12": TrafficPattern("8-12", 2400, 1300, 2200, 500),
            "9-10": TrafficPattern("9-10", 1800, 1200, 1700, 400),
            "10-11": TrafficPattern("10-11", 2200, 1300, 2100, 500),
            "11-F2": TrafficPattern("11-F2", 2100, 1200, 2000, 450),
            "12-1": TrafficPattern("12-1", 2600, 1400, 2400, 550),
            "13-4": TrafficPattern("13-4", 3800, 2000, 3500, 800),
            "14-13": TrafficPattern("14-13", 3600, 1900, 3300, 750),
            "15-7": TrafficPattern("15-7", 2800, 1500, 2600, 600),
            "F1-5": TrafficPattern("F1-5", 3300, 2200, 3100, 1200),
            "F1-2": TrafficPattern("F1-2", 3000, 2000, 2800, 1100),
            "F2-3": TrafficPattern("F2-3", 1900, 1600, 1800, 900),
            "F7-15": TrafficPattern("F7-15", 2600, 1500, 2400, 550),
            "F8-4": TrafficPattern("F8-4", 2800, 1600, 2600, 600),
        }

    def _load_metro_lines(self):
        self.metro_lines = [
            MetroLine("M1", "Line 1 (Helwan-New Marg)", [12, 1, 3, "F2", 11], 1500000),
            MetroLine("M2", "Line 2 (Shubra-Giza)", [11, "F2", 3, 10, 8], 1200000),
            MetroLine("M3", "Line 3 (Airport-Imbaba)", ["F1", 5, 2, 3, 9], 800000),
        ]

    def _load_bus_routes(self):
        self.bus_routes = [
            BusRoute("B1", [1, 3, 6, 9], 25, 35000),
            BusRoute("B2", [7, 15, 8, 10, 3], 30, 42000),
            BusRoute("B3", [2, 5, "F1"], 20, 28000),
            BusRoute("B4", [4, 14, 2, 3], 22, 31000),
            BusRoute("B5", [8, 12, 1], 18, 25000),
            BusRoute("B6", [11, 5, 2], 24, 33000),
            BusRoute("B7", [13, 4, 14], 15, 21000),
            BusRoute("B8", ["F7", 15, 7], 12, 17000),
            BusRoute("B9", [1, 8, 10, 9, 6], 28, 39000),
            BusRoute("B10", ["F8", 4, 2, 5], 20, 28000),
        ]

    def _load_transport_demand(self):
        self.transport_demand = [
            (3, 5, 15000),
            (1, 3, 12000),
            (2, 3, 18000),
            ("F2", 11, 25000),
            ("F1", 3, 20000),
            (7, 3, 14000),
            (4, 3, 16000),
            (8, 3, 22000),
            (3, 9, 13000),
            (5, 2, 17000),
            (11, 3, 24000),
            (12, 3, 11000),
            (1, 8, 9000),
            (7, "F7", 18000),
            (4, "F8", 12000),
            (13, 3, 8000),
            (14, 4, 7000),
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
                               road.distance, road.capacity, road.condition, road.source)
            self.graph[road.to_id].append(reverse_road)

    def _parse_node_id(self, value: str):
        """Convert node IDs to int when possible; keep facility IDs as strings."""
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value

    def _ensure_facility_access_roads(self):
        """Generate access roads for facilities without any road links."""
        connected = set()
        for road in self.roads:
            if isinstance(road.from_id, str) and road.from_id in self.facilities:
                connected.add(road.from_id)
            if isinstance(road.to_id, str) and road.to_id in self.facilities:
                connected.add(road.to_id)

        for fid, facility in self.facilities.items():
            if fid in connected:
                continue

            nearest_id = None
            nearest_dist = float('inf')
            for nid, neighborhood in self.neighborhoods.items():
                dx = facility.x - neighborhood.x
                dy = facility.y - neighborhood.y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_id = nid

            if nearest_id is not None:
                access = Road(fid, nearest_id, round(nearest_dist, 2), 2000, 7, source="generated")
                self.access_roads.append(access)
                self.roads.append(access)