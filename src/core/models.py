from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import heapq
from collections import defaultdict

class NodeType(Enum):
    RESIDENTIAL = "Residential"
    BUSINESS = "Business"
    MIXED = "Mixed"
    INDUSTRIAL = "Industrial"
    GOVERNMENT = "Government"

class FacilityType(Enum):
    AIRPORT = "Airport"
    TRANSIT_HUB = "Transit Hub"
    EDUCATION = "Education"
    TOURISM = "Tourism"
    SPORTS = "Sports"
    BUSINESS = "Business"
    COMMERCIAL = "Commercial"
    MEDICAL = "Medical"

@dataclass
class Neighborhood:
    id: int
    name: str
    population: int
    type: NodeType
    x: float
    y: float

@dataclass
class Facility:
    id: str
    name: str
    type: FacilityType
    x: float
    y: float

@dataclass
class Road:
    from_id: str
    to_id: str
    distance: float
    capacity: int
    condition: int

@dataclass
class TrafficPattern:
    road_id: str
    morning_peak: int
    afternoon: int
    evening_peak: int
    night: int

    def get_current_traffic(self, hour: int) -> int:
        if 7 <= hour < 10:
            return self.morning_peak
        elif 10 <= hour < 16:
            return self.afternoon
        elif 16 <= hour < 20:
            return self.evening_peak
        else:
            return self.night

@dataclass
class MetroLine:
    id: str
    name: str
    stations: List[str]
    daily_passengers: int

@dataclass
class BusRoute:
    id: str
    stops: List[str]
    buses_assigned: int
    daily_passengers: int