"""
Traffic Simulator for Cairo Transportation Network
Simulates realistic traffic flow patterns, congestion, and impact scenarios
"""
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta
import random
from ..core.data_loader import CairoTransportData
from ..algorithms.shortest_path import ShortestPath


class TrafficEvent:
    """Represents a traffic event (accident, closure, etc.)"""
    def __init__(self, event_id: str, road_id: Tuple, event_type: str,
                 severity: int, start_time: int, duration: int):
        self.event_id = event_id
        self.road_id = road_id  # (from_id, to_id)
        self.event_type = event_type  # 'accident', 'closure', 'construction'
        self.severity = severity  # 1-10
        self.start_time = start_time  # Hour
        self.duration = duration  # Hours
        self.active = True

    def is_active(self, current_hour: int) -> bool:
        """Check if event is active at given hour"""
        return self.active and self.start_time <= current_hour < self.start_time + self.duration


class RoadState:
    """Represents the state of a road at a given time"""
    def __init__(self, from_id, to_id, capacity: int, distance: float):
        self.from_id = from_id
        self.to_id = to_id
        self.capacity = capacity
        self.distance = distance
        self.current_traffic = 0
        self.congestion_level = 0.0  # 0-1
        self.avg_speed = 60  # km/h
        self.travel_time = distance / 60  # hours
        self.incidents = []

    def update_traffic(self, traffic_volume: int, base_capacity: int):
        """Update traffic state based on current volume"""
        self.current_traffic = traffic_volume
        self.congestion_level = min(1.0, traffic_volume / base_capacity)
        
        # Calculate speed based on congestion
        if self.congestion_level < 0.5:
            self.avg_speed = 60
        elif self.congestion_level < 0.8:
            self.avg_speed = 40
        else:
            self.avg_speed = 20
        
        # Calculate travel time
        self.travel_time = self.distance / self.avg_speed


class TrafficSimulator:
    """
    Main traffic simulation engine for Cairo transportation network
    Time Complexity: O(n * t) where n = roads, t = time steps
    Space Complexity: O(n + e) where n = nodes, e = events
    """

    def __init__(self, data: CairoTransportData):
        self.data = data
        self.road_states: Dict[Tuple, RoadState] = {}
        self.events: List[TrafficEvent] = []
        self.simulation_history: List[Dict] = []
        self.current_hour = 0
        self._initialize_road_states()

    def _initialize_road_states(self):
        """Initialize road state tracking"""
        for road in self.data.roads:
            key = (road.from_id, road.to_id)
            self.road_states[key] = RoadState(
                road.from_id, road.to_id, road.capacity, road.distance
            )
            # Also create reverse direction for undirected graph
            reverse_key = (road.to_id, road.from_id)
            self.road_states[reverse_key] = RoadState(
                road.to_id, road.from_id, road.capacity, road.distance
            )

    def get_traffic_for_hour(self, hour: int) -> Dict[Tuple, int]:
        """
        Get traffic volume for all roads at a given hour
        Uses traffic patterns data and applies realistic variation
        """
        traffic_volumes = {}
        
        for road in self.data.roads:
            road_key = f"{road.from_id}-{road.to_id}"
            reverse_key = f"{road.to_id}-{road.from_id}"
            
            # Get base traffic pattern
            if road_key in self.data.traffic_patterns:
                pattern = self.data.traffic_patterns[road_key]
                base_volume = pattern.get_current_traffic(hour)
            elif reverse_key in self.data.traffic_patterns:
                pattern = self.data.traffic_patterns[reverse_key]
                base_volume = pattern.get_current_traffic(hour)
            else:
                base_volume = 1500  # Default
            
            # Add random variation (±20%)
            variation = base_volume * random.uniform(-0.2, 0.2)
            volume = int(max(100, base_volume + variation))
            
            # Handle forward direction
            traffic_volumes[(road.from_id, road.to_id)] = volume
            # Reverse direction typically has similar volume
            traffic_volumes[(road.to_id, road.from_id)] = int(volume * 0.95)
        
        return traffic_volumes

    def apply_event(self, event: TrafficEvent):
        """Add a traffic event to the simulation"""
        self.events.append(event)

    def simulate_step(self, hour: int, apply_events: bool = True) -> Dict:
        """
        Simulate traffic for one hour
        Returns statistics for that hour
        """
        self.current_hour = hour
        
        # Get traffic volumes for this hour
        traffic_volumes = self.get_traffic_for_hour(hour)
        
        # Apply events (accidents, closures)
        if apply_events:
            traffic_volumes = self._apply_events(hour, traffic_volumes)
        
        # Update road states
        stats = {
            'hour': hour,
            'total_traffic': 0,
            'avg_congestion': 0.0,
            'roads_congested': 0,
            'bottlenecks': [],
            'road_details': {}
        }
        
        congestion_levels = []
        for road_key, volume in traffic_volumes.items():
            if road_key in self.road_states:
                road_state = self.road_states[road_key]
                road = self._find_road(road_key[0], road_key[1])
                if road:
                    road_state.update_traffic(volume, road.capacity)
                    stats['total_traffic'] += volume
                    congestion_levels.append(road_state.congestion_level)
                    
                    if road_state.congestion_level > 0.7:
                        stats['roads_congested'] += 1
                        stats['bottlenecks'].append({
                            'from': road_key[0],
                            'to': road_key[1],
                            'congestion': road_state.congestion_level,
                            'vehicles': volume,
                            'capacity': road.capacity
                        })
                    
                    stats['road_details'][road_key] = {
                        'traffic': volume,
                        'congestion': road_state.congestion_level,
                        'travel_time': road_state.travel_time,
                        'avg_speed': road_state.avg_speed
                    }
        
        if congestion_levels:
            stats['avg_congestion'] = np.mean(congestion_levels)
        
        self.simulation_history.append(stats)
        return stats

    def _apply_events(self, hour: int, traffic_volumes: Dict) -> Dict:
        """Apply traffic events to volumes"""
        modified_volumes = dict(traffic_volumes)
        
        for event in self.events:
            if event.is_active(hour):
                road_key = event.road_id
                
                if event.event_type == 'accident':
                    # Reduce capacity by severity
                    reduction = 0.3 + (event.severity / 10) * 0.4
                    modified_volumes[road_key] = int(modified_volumes.get(road_key, 0) * (1 + reduction))
                
                elif event.event_type == 'closure':
                    # Complete or partial closure
                    modified_volumes[road_key] = 0 if event.severity > 7 else int(modified_volumes.get(road_key, 0) * 0.2)
                
                elif event.event_type == 'construction':
                    # Moderate capacity reduction
                    modified_volumes[road_key] = int(modified_volumes.get(road_key, 0) * 1.15)
        
        return modified_volumes

    def simulate_period(self, start_hour: int, end_hour: int) -> Dict:
        """
        Simulate traffic for a period (e.g., full day 0-24)
        Time Complexity: O((end_hour - start_hour) * num_roads)
        """
        results = {
            'period': (start_hour, end_hour),
            'hourly_stats': [],
            'daily_summary': {}
        }
        
        total_congestion = 0
        total_events = 0
        peak_congestion = 0
        peak_hour = start_hour
        
        for hour in range(start_hour, end_hour):
            stats = self.simulate_step(hour)
            results['hourly_stats'].append(stats)
            total_congestion += stats['avg_congestion']
            total_events += len(stats['bottlenecks'])
            
            if stats['avg_congestion'] > peak_congestion:
                peak_congestion = stats['avg_congestion']
                peak_hour = hour
        
        duration = end_hour - start_hour
        results['daily_summary'] = {
            'avg_daily_congestion': total_congestion / duration,
            'peak_congestion_hour': peak_hour,
            'peak_congestion_level': peak_congestion,
            'total_bottleneck_hours': total_events,
            'avg_vehicles_per_hour': np.mean([
                s['total_traffic'] for s in results['hourly_stats']
            ])
        }
        
        return results

    def _find_road(self, from_id: Any, to_id: Any):
        """Find road object by its endpoints"""
        for road in self.data.roads:
            if road.from_id == from_id and road.to_id == to_id:
                return road
        return None

    def get_current_travel_time(self, from_id: Any, to_id: Any, hour: int = None) -> float:
        """Get estimated travel time for a road at given hour"""
        if hour is None:
            hour = self.current_hour
        
        key = (from_id, to_id)
        if key in self.road_states:
            # Update traffic for the hour if not already simulated
            if hour != self.current_hour:
                self.simulate_step(hour)
            return self.road_states[key].travel_time
        return 0.0

    def get_congestion_report(self, hour: int = None) -> Dict:
        """Get detailed congestion report for current or specified hour"""
        if hour is None:
            hour = self.current_hour
        
        # Find history for this hour
        hour_stats = next((s for s in self.simulation_history if s['hour'] == hour), None)
        
        if not hour_stats:
            hour_stats = self.simulate_step(hour)
        
        return {
            'hour': hour,
            'congestion_level': hour_stats['avg_congestion'],
            'bottlenecks': hour_stats['bottlenecks'],
            'roads_affected': hour_stats['roads_congested'],
            'total_vehicles': hour_stats['total_traffic']
        }

    def identify_optimal_routes(self, from_id: Any, to_id: Any, hour: int = None) -> Dict:
        """
        Identify optimal routes considering current traffic
        Returns multiple route options with congestion levels
        """
        if hour is None:
            hour = self.current_hour
        
        # This would use shortest_path algorithm with time-aware weights
        sp = ShortestPath(self.data)
        path, distance = sp.dijkstra(from_id, to_id, hour)
        
        # Calculate expected travel time with current congestion
        total_time = 0
        for i in range(len(path) - 1):
            total_time += self.get_current_travel_time(path[i], path[i+1], hour)
        
        return {
            'path': path,
            'distance': distance,
            'estimated_time': total_time,
            'congestion_factor': 1.0 + (total_time / (distance / 60) - 1)
        }

    def simulate_scenario(self, scenario_name: str, events: List[TrafficEvent]) -> Dict:
        """
        Simulate a specific scenario (e.g., accident on major road)
        Returns comparison of normal vs scenario traffic
        """
        # Clear previous events
        previous_events = self.events
        self.events = events
        
        # Simulate with events
        scenario_results = self.simulate_period(0, 24)
        
        # Simulate without events
        self.events = []
        normal_results = self.simulate_period(0, 24)
        
        # Restore previous events
        self.events = previous_events
        
        return {
            'scenario_name': scenario_name,
            'normal_conditions': normal_results['daily_summary'],
            'scenario_conditions': scenario_results['daily_summary'],
            'impact': {
                'congestion_increase': (
                    scenario_results['daily_summary']['avg_daily_congestion'] -
                    normal_results['daily_summary']['avg_daily_congestion']
                ),
                'additional_bottlenecks': (
                    scenario_results['daily_summary']['total_bottleneck_hours'] -
                    normal_results['daily_summary']['total_bottleneck_hours']
                )
            }
        }

    def export_simulation_data(self) -> Dict:
        """Export complete simulation data for analysis"""
        return {
            'simulation_history': self.simulation_history,
            'current_hour': self.current_hour,
            'road_states': {
                str(k): {
                    'traffic': v.current_traffic,
                    'congestion': v.congestion_level,
                    'speed': v.avg_speed,
                    'travel_time': v.travel_time
                }
                for k, v in self.road_states.items()
            },
            'events': [
                {
                    'id': e.event_id,
                    'type': e.event_type,
                    'severity': e.severity,
                    'road': str(e.road_id)
                }
                for e in self.events
            ]
        }
