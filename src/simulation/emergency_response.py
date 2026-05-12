"""
Emergency Response System for Cairo Transportation Network
Handles emergency vehicle routing and response optimization using A* search
"""
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import heapq
from datetime import datetime
from enum import Enum
from ..core.data_loader import CairoTransportData
from ..algorithms.astar import AStarSearch
from ..algorithms.shortest_path import ShortestPath
from ..algorithms.greedy import GreedyTrafficOptimizer


class EmergencyType(Enum):
    """Types of emergency responses"""
    MEDICAL = 1  # Ambulance to hospital
    FIRE = 2  # Fire truck to incident
    POLICE = 3  # Police response
    HAZMAT = 4  # Hazardous materials


class EmergencySeverity(Enum):
    """Severity levels for emergency calls"""
    LOW = 1  # Non-urgent
    MEDIUM = 2  # Urgent
    HIGH = 3  # Critical
    CRITICAL = 4  # Life-threatening


class EmergencyVehicle:
    """Represents an emergency vehicle in the system"""
    
    def __init__(self, vehicle_id: str, vehicle_type: EmergencyType,
                 current_location: Any, capacity: int = 1):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.current_location = current_location
        self.capacity = capacity
        self.is_active = False
        self.current_call: Optional['EmergencyCall'] = None
        self.route = []
        self.total_response_time = 0
        self.calls_handled = 0
        self.status = "available"  # available, en_route, at_scene, returning

    def dispatch_to(self, call: 'EmergencyCall', route: List[Any], eta: float):
        """Dispatch vehicle to emergency call"""
        self.current_call = call
        self.route = route
        self.is_active = True
        self.status = "en_route"
        call.assigned_vehicle = self
        call.eta = eta
        call.dispatched_time = datetime.now()

    def mark_arrived(self):
        """Mark vehicle as arrived at scene"""
        self.status = "at_scene"
        if self.current_call:
            self.current_call.arrival_time = datetime.now()

    def mark_completed(self):
        """Mark call as completed"""
        self.status = "available"
        if self.current_call:
            self.current_call.completion_time = datetime.now()
            self.current_call.status = "completed"
            self.current_call.response_time = (
                self.current_call.completion_time - self.current_call.call_time
            ).total_seconds()
            self.total_response_time += self.current_call.response_time
            self.calls_handled += 1
        self.current_call = None
        self.route = []


class EmergencyCall:
    """Represents an emergency call in the system"""
    
    def __init__(self, call_id: str, call_type: EmergencyType,
                 location: Any, severity: EmergencySeverity,
                 description: str = ""):
        self.call_id = call_id
        self.call_type = call_type
        self.location = location
        self.severity = severity
        self.description = description
        self.call_time = datetime.now()
        self.dispatched_time = None
        self.arrival_time = None
        self.completion_time = None
        self.assigned_vehicle: Optional[EmergencyVehicle] = None
        self.eta = None
        self.response_time = None
        self.status = "pending"  # pending, dispatched, arrived, completed

    def get_priority(self) -> int:
        """Get priority score (higher = more urgent)"""
        # Priority based on severity and type
        severity_score = self.severity.value * 100
        type_bonus = {
            EmergencyType.MEDICAL: 40,
            EmergencyType.FIRE: 30,
            EmergencyType.HAZMAT: 50,
            EmergencyType.POLICE: 20
        }.get(self.call_type, 10)
        return severity_score + type_bonus

    def time_waiting(self) -> float:
        """Get time call has been waiting in minutes"""
        elapsed = datetime.now() - self.call_time
        return elapsed.total_seconds() / 60


class EmergencyDispatchCenter:
    """
    Central emergency dispatch system
    Time Complexity: O(n * m) where n = calls, m = vehicles
    Space Complexity: O(n + m + e) where e = events
    """

    def __init__(self, data: CairoTransportData):
        self.data = data
        self.vehicles: Dict[str, EmergencyVehicle] = {}
        self.active_calls: List[EmergencyCall] = deque()
        self.completed_calls: List[EmergencyCall] = []
        self.astar = AStarSearch(data.graph, self._get_coordinates(), data.traffic_patterns)
        self.sp = ShortestPath(data)
        self.greedy = GreedyTrafficOptimizer(data)
        self.dispatch_history: List[Dict] = []
        self._initialize_vehicles()

    def _get_coordinates(self) -> Dict[Any, Tuple[float, float]]:
        """Get coordinates for all nodes"""
        coords = {}
        for nid, n in self.data.neighborhoods.items():
            coords[nid] = (n.x, n.y)
        for fid, f in self.data.facilities.items():
            coords[fid] = (f.x, f.y)
        return coords

    def _initialize_vehicles(self):
        """Initialize emergency vehicles for each facility"""
        # Ambulances at hospitals
        hospitals = {k: v for k, v in self.data.facilities.items() 
                    if 'Hospital' in v.name}
        ambulance_id = 1
        for hospital_id, hospital in hospitals.items():
            for i in range(2):  # 2 ambulances per hospital
                v = EmergencyVehicle(
                    f"AMBUL_{ambulance_id}",
                    EmergencyType.MEDICAL,
                    hospital_id,
                    capacity=2
                )
                self.vehicles[v.vehicle_id] = v
                ambulance_id += 1

        # Fire trucks at strategic locations
        fire_locations = [8, 2, 12]  # Giza, Nasr City, Helwan
        fire_id = 1
        for location in fire_locations:
            if location in self.data.neighborhoods:
                v = EmergencyVehicle(
                    f"FIRE_{fire_id}",
                    EmergencyType.FIRE,
                    location,
                    capacity=5
                )
                self.vehicles[v.vehicle_id] = v
                fire_id += 1

        # Police units at major areas
        police_locations = [2, 3, 8]  # Nasr City, Downtown, Giza
        police_id = 1
        for location in police_locations:
            if location in self.data.neighborhoods:
                v = EmergencyVehicle(
                    f"POLICE_{police_id}",
                    EmergencyType.POLICE,
                    location,
                    capacity=3
                )
                self.vehicles[v.vehicle_id] = v
                police_id += 1

    def receive_call(self, call: EmergencyCall):
        """Receive an emergency call"""
        self.active_calls.append(call)
        # Immediately dispatch if matching vehicle available
        self.process_dispatch_queue()

    def process_dispatch_queue(self):
        """Process pending calls and dispatch vehicles"""
        # Sort by priority (time-weighted priority)
        calls_list = list(self.active_calls)
        calls_list.sort(
            key=lambda c: (c.get_priority(), -c.time_waiting()),
            reverse=True
        )
        
        for call in calls_list:
            if call.status == "pending":
                best_vehicle = self._find_best_vehicle(call)
                if best_vehicle:
                    self._dispatch_vehicle(best_vehicle, call)

    def _find_best_vehicle(self, call: EmergencyCall) -> Optional[EmergencyVehicle]:
        """Find the best available vehicle for a call"""
        available = [v for v in self.vehicles.values() 
                    if v.status == "available" and v.vehicle_type == call.call_type]
        
        if not available:
            return None
        
        # Find closest vehicle by distance
        best_vehicle = None
        min_distance = float('inf')
        
        for vehicle in available:
            # Calculate distance (simplified - use straight line)
            v_coords = self._get_coordinates().get(vehicle.current_location, (0, 0))
            c_coords = self._get_coordinates().get(call.location, (0, 0))
            
            distance = ((v_coords[0] - c_coords[0])**2 + 
                       (v_coords[1] - c_coords[1])**2)**0.5
            
            if distance < min_distance:
                min_distance = distance
                best_vehicle = vehicle
        
        return best_vehicle

    def _dispatch_vehicle(self, vehicle: EmergencyVehicle, call: EmergencyCall):
        """Dispatch a vehicle to an emergency call"""
        # Find optimal route using A*
        current_hour = datetime.now().hour
        route_data = self.astar.find_path(
            vehicle.current_location,
            call.location,
            heuristic_type='euclidean',
            emergency_priority=call.severity.value,
            time_hour=current_hour
        )
        
        route = route_data['path']
        distance = route_data['distance']
        
        # Estimate travel time (simplified: use 60 km/h average for emergency)
        eta = distance / 60  # in hours
        
        # Generate a basic signal preemption plan for the route
        preemption_plan = None
        if route:
            signals = {node: {'N': 30, 'S': 30, 'E': 20, 'W': 20} for node in route}
            severity_map = {
                EmergencySeverity.CRITICAL: 'critical',
                EmergencySeverity.HIGH: 'emergency',
                EmergencySeverity.MEDIUM: 'urgent',
                EmergencySeverity.LOW: 'normal'
            }
            preemption_plan = self.greedy.emergency_vehicle_preemption(
                [{'type': severity_map.get(call.severity, 'urgent'), 'path': route, 'response_time': 0}],
                signals
            )

        # Dispatch vehicle
        vehicle.dispatch_to(call, route, eta)
        call.status = "dispatched"
        
        # Log dispatch
        self.dispatch_history.append({
            'timestamp': datetime.now(),
            'vehicle': vehicle.vehicle_id,
            'call': call.call_id,
            'route': route,
            'eta': eta,
            'distance': distance,
            'preemption_plan': preemption_plan,
            'time_hour': current_hour
        })

    def vehicle_arrived(self, vehicle_id: str):
        """Mark vehicle as arrived at scene"""
        if vehicle_id in self.vehicles:
            vehicle = self.vehicles[vehicle_id]
            vehicle.mark_arrived()

    def vehicle_completed_call(self, vehicle_id: str):
        """Mark call as completed"""
        if vehicle_id in self.vehicles:
            vehicle = self.vehicles[vehicle_id]
            vehicle.mark_completed()
            
            # Move call to completed
            if vehicle.current_call:
                self.active_calls.remove(vehicle.current_call)
                self.completed_calls.append(vehicle.current_call)

    def get_system_status(self) -> Dict:
        """Get current status of emergency system"""
        available_count = len([v for v in self.vehicles.values() 
                              if v.status == "available"])
        active_count = len(list(self.active_calls))
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_vehicles': len(self.vehicles),
            'available_vehicles': available_count,
            'active_calls': active_count,
            'pending_calls': len([c for c in self.active_calls 
                                 if c.status == "pending"]),
            'calls_completed': len(self.completed_calls),
            'vehicle_status': {
                v.vehicle_id: {
                    'status': v.status,
                    'location': v.current_location,
                    'calls_handled': v.calls_handled,
                    'current_call': v.current_call.call_id if v.current_call else None
                }
                for v in self.vehicles.values()
            }
        }

    def get_performance_metrics(self) -> Dict:
        """Get performance metrics for emergency response"""
        if not self.completed_calls:
            return {
                'avg_response_time_minutes': 0,
                'avg_distance_km': 0,
                'calls_completed': 0
            }
        
        response_times = [c.response_time for c in self.completed_calls 
                         if c.response_time is not None]
        distances = []
        
        for entry in self.dispatch_history:
            if any(c.call_id == entry['call'] and c in self.completed_calls 
                   for c in self.completed_calls):
                distances.append(entry['distance'])
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        avg_distance = sum(distances) / len(distances) if distances else 0
        
        return {
            'avg_response_time_minutes': avg_response / 60,
            'avg_distance_km': avg_distance,
            'calls_completed': len(self.completed_calls),
            'vehicles_utilized': len(set(d['vehicle'] for d in self.dispatch_history)),
            'emergency_types_handled': list(set(
                c.call_type.name for c in self.completed_calls
            ))
        }

    def simulate_emergency_scenario(self, scenario: Dict) -> Dict:
        """
        Simulate emergency response for a scenario
        
        Args:
            scenario: {
                'name': str,
                'calls': List[EmergencyCall],
                'simulation_time': int (hours)
            }
        """
        results = {
            'scenario': scenario['name'],
            'calls_received': 0,
            'calls_completed': 0,
            'avg_response_time': 0,
            'incident_log': []
        }
        
        # Reset system
        self.active_calls = deque()
        self.completed_calls = []
        self.dispatch_history = []
        for v in self.vehicles.values():
            v.status = "available"
            v.current_call = None
        
        # Simulate receiving calls
        for call in scenario.get('calls', []):
            self.receive_call(call)
            results['calls_received'] += 1
            
            # Simulate dispatch and completion
            self.process_dispatch_queue()
            
            # Simulate arrival (instant for now)
            for vehicle in self.vehicles.values():
                if vehicle.current_call == call:
                    vehicle.mark_arrived()
                    vehicle.mark_completed()
        
        # Calculate metrics
        results['calls_completed'] = len(self.completed_calls)
        metrics = self.get_performance_metrics()
        results['avg_response_time'] = metrics['avg_response_time_minutes']
        
        return results

    def export_call_log(self) -> List[Dict]:
        """Export complete call log"""
        log = []
        for call in self.completed_calls:
            log.append({
                'call_id': call.call_id,
                'type': call.call_type.name,
                'severity': call.severity.name,
                'location': str(call.location),
                'call_time': call.call_time.isoformat(),
                'dispatch_time': call.dispatched_time.isoformat() if call.dispatched_time else None,
                'arrival_time': call.arrival_time.isoformat() if call.arrival_time else None,
                'response_time_seconds': call.response_time,
                'assigned_vehicle': call.assigned_vehicle.vehicle_id if call.assigned_vehicle else None
            })
        return log
