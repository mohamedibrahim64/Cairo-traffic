"""
Flask Backend API for Cairo Smart Transportation System
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.graph import Graph, TemporalGraph
from src.core.data_loader import CairoTransportData
from src.algorithms.mst import MinimumSpanningTree
from src.algorithms.shortest_path import ShortestPath
from src.algorithms.astar import AStarSearch
from src.algorithms.dynamic_programming import DynamicProgramming
from src.algorithms.greedy import GreedyTrafficOptimizer
from src.ml.traffic_predictor import TrafficPredictor
from src.ml.traffic_predictor import generate_training_data
import requests

# Optional OSRM routing to draw road-following polylines in the UI
OSRM_BASE_URL = os.getenv('OSRM_BASE_URL', 'https://router.project-osrm.org').rstrip('/')
OSRM_PROFILE = os.getenv('OSRM_PROFILE', 'driving')
try:
    OSRM_TIMEOUT = float(os.getenv('OSRM_TIMEOUT', '5'))
except ValueError:
    OSRM_TIMEOUT = 5.0


def get_node_coordinates(data):
    """Get coordinates for all nodes"""
    coordinates = {}
    for nid, neighborhood in data.neighborhoods.items():
        coordinates[nid] = (neighborhood.x, neighborhood.y)
    for fid, facility in data.facilities.items():
        coordinates[fid] = (facility.x, facility.y)
    return coordinates

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
CORS(app)

# Initialize system
data = CairoTransportData()
data.load_all_data()

mst = MinimumSpanningTree(data)
sp = ShortestPath(data)
dp = DynamicProgramming(data)
greedy = GreedyTrafficOptimizer(data)
ml_predictor = TrafficPredictor()

def initialize_ml_predictor():
    """Train the traffic predictor on the bundled traffic patterns."""
    if ml_predictor.trained:
        return

    try:
        X, y = generate_training_data(data.traffic_patterns)
        if X and y:
            ml_predictor.train(X, y)
    except Exception:
        pass


initialize_ml_predictor()
astar = AStarSearch(data.graph, get_node_coordinates(data), data.traffic_patterns)

# ==================== Routes ====================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/infrastructure')
def infrastructure():
    """Infrastructure network page"""
    return render_template('infrastructure.html')

@app.route('/traffic')
def traffic():
    """Traffic flow optimization page"""
    return render_template('traffic.html')

@app.route('/emergency')
def emergency():
    """Emergency response page"""
    return render_template('emergency.html')

@app.route('/transit')
def transit():
    """Public transit page"""
    return render_template('transit.html')

@app.route('/ml-prediction')
def ml_prediction():
    """ML prediction page"""
    return render_template('ml_prediction.html')

@app.route('/comparison')
def comparison():
    """Algorithm comparison page"""
    return render_template('comparison.html')

# ==================== API Endpoints ====================

@app.route('/api/network-data')
def get_network_data():
    """Get complete network data"""
    neighborhoods = []
    for nid, n in data.neighborhoods.items():
        neighborhoods.append({
            'id': n.id,
            'name': n.name,
            'population': n.population,
            'type': n.type.value if hasattr(n.type, 'value') else str(n.type),
            'x': n.x,
            'y': n.y
        })
    
    facilities = []
    for fid, f in data.facilities.items():
        facilities.append({
            'id': f.id if hasattr(f, 'id') else fid,
            'name': f.name,
            'type': f.type.value if hasattr(f.type, 'value') else str(f.type),
            'x': f.x,
            'y': f.y
        })
    
    roads = []
    for road in data.roads:
        roads.append({
            'from': road.from_id,
            'to': road.to_id,
            'distance': road.distance,
            'capacity': road.capacity,
            'condition': road.condition
        })
    
    return jsonify({
        'neighborhoods': neighborhoods,
        'facilities': facilities,
        'roads': roads
    })

@app.route('/api/shortest-path', methods=['POST'])
def shortest_path():
    """Calculate shortest path"""
    req_data = request.json
    start = req_data['start']
    end = req_data['end']
    algorithm = req_data.get('algorithm', 'dijkstra')
    time_hour = req_data.get('time_hour', 10)
    avoid_roads = _normalize_avoid_roads(req_data.get('avoid_roads'))
    
    try:
        start_str = str(start)
        end_str = str(end)
        start_id = int(start_str) if start_str.isdigit() else start
        end_id = int(end_str) if end_str.isdigit() else end
        
        time_varying_result = None
        if algorithm == 'dijkstra':
            path, distance = sp.dijkstra(start_id, end_id, time_hour, avoid_roads)
        elif algorithm == 'astar':
            path, distance = sp.a_star_search(start_id, end_id, time_hour, avoid_roads)
        elif algorithm == 'time_varying':
            time_varying_result = sp.time_varying_shortest_path(start_id, end_id, time_hour, avoid_roads)
            path = time_varying_result.get('recommended_route', [])
            if path == time_varying_result.get('off_peak_route'):
                distance = time_varying_result.get('off_peak_distance')
            else:
                distance = time_varying_result.get('peak_distance')
        elif algorithm == 'greedy':
            result = greedy.greedy_route_recommendation(start_id, end_id, avoid_roads=avoid_roads, hour=time_hour)
            path = result['path']
            distance = result['total_distance']
        else:
            path, distance = sp.dijkstra(start_id, end_id, time_hour, avoid_roads)
        
        # Convert path to names + coordinates for the frontend map
        path_names = []
        for node in path:
            name = get_node_name(node)
            coords = get_node_coordinate(node)
            item = {
                'id': node,
                'name': name,
                'x': coords[0] if coords else None,
                'y': coords[1] if coords else None
            }
            path_names.append(item)

        # Build route segments (ordered list of road segments with coords)
        segments = []
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i+1]
            # Find matching road (either direction)
            matched = None
            for road in data.roads:
                if (road.from_id == a and road.to_id == b) or (road.from_id == b and road.to_id == a):
                    matched = road
                    break

            from_coords = get_node_coordinate(a) or (None, None)
            to_coords = get_node_coordinate(b) or (None, None)
            segments.append({
                'from': a,
                'to': b,
                'distance': matched.distance if matched else None,
                'coords': [
                    {'x': from_coords[0], 'y': from_coords[1]},
                    {'x': to_coords[0], 'y': to_coords[1]}
                ]
            })

        # Try to get OSRM geometry for the full path so the drawn route follows real roads
        osrm_geom = _get_osrm_geometry_for_path(path)
        if osrm_geom:
            # attach as separate geometry field the frontend can prefer
            return jsonify({
                'success': True,
                'path': path_names,
                'segments': segments,
                'distance': distance,
                'algorithm': algorithm,
                'osrm_geometry': osrm_geom,
                'time_varying': time_varying_result
            })

        return jsonify({
            'success': True,
            'path': path_names,
            'segments': segments,
            'distance': distance,
            'algorithm': algorithm,
            'time_varying': time_varying_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/compare-routes', methods=['POST'])
def compare_routes():
    """Calculate and compare routes for all three algorithms"""
    req_data = request.json
    start = req_data['start']
    end = req_data['end']
    time_hour = req_data.get('time_hour', 10)
    
    try:
        start_str = str(start)
        end_str = str(end)
        start_id = int(start_str) if start_str.isdigit() else start
        end_id = int(end_str) if end_str.isdigit() else end

        algorithms_data = []
        distances = {}

        for algo_name in ['dijkstra', 'astar', 'greedy']:
            try:
                if algo_name == 'dijkstra':
                    path, distance = sp.dijkstra(start_id, end_id, time_hour)
                elif algo_name == 'astar':
                    path, distance = sp.a_star_search(start_id, end_id, time_hour)
                else:
                    result = greedy.greedy_route_recommendation(start_id, end_id, hour=time_hour)
                    path = result['path']
                    distance = result['total_distance']

                path_names = []
                for node in path:
                    coords = get_node_coordinate(node)
                    path_names.append({
                        'id': node,
                        'name': get_node_name(node),
                        'x': coords[0] if coords else None,
                        'y': coords[1] if coords else None
                    })

                segments = []
                for i in range(len(path) - 1):
                    a = path[i]
                    b = path[i + 1]
                    matched = None
                    for road in data.roads:
                        if (road.from_id == a and road.to_id == b) or (road.from_id == b and road.to_id == a):
                            matched = road
                            break

                    from_coords = get_node_coordinate(a) or (None, None)
                    to_coords = get_node_coordinate(b) or (None, None)
                    segments.append({
                        'from': a,
                        'to': b,
                        'distance': matched.distance if matched else None,
                        'coords': [
                            {'x': from_coords[0], 'y': from_coords[1]},
                            {'x': to_coords[0], 'y': to_coords[1]}
                        ]
                    })

                osrm_geom = _get_osrm_geometry_for_path(path)

                algorithms_data.append({
                    'algorithm': algo_name,
                    'path': path_names,
                    'segments': segments,
                    'distance': distance,
                    'osrm_geometry': osrm_geom
                })
                distances[algo_name] = distance
            except Exception as algo_error:
                algorithms_data.append({
                    'algorithm': algo_name,
                    'error': str(algo_error)
                })

        valid_distances = {name: dist for name, dist in distances.items() if dist is not None and dist != float('inf')}
        best_algo = min(valid_distances, key=valid_distances.get) if valid_distances else None
        best_distance = valid_distances[best_algo] if best_algo else float('inf')
        optimal_algos = [name for name, dist in valid_distances.items() if dist == best_distance]

        if len(optimal_algos) > 1:
            analysis = {
                'summary': 'Dijkstra and A* found the same shortest path here.',
                'why_dijkstra': 'Dijkstra guarantees the optimal route by expanding nodes in increasing cost order.',
                'why_astar': 'A* is also optimal here because the heuristic is admissible, but it is usually faster because it guides search toward the destination.',
                'why_greedy': 'Greedy is faster to decide locally, but it does not guarantee the shortest full route.',
                'recommended': 'Use Dijkstra when you want a guaranteed shortest path and A* when you want the same optimal path with less search in larger graphs.'
            }
        else:
            analysis = {
                'summary': f'{best_algo.upper()} returned the shortest route.' if best_algo else 'No valid route found.',
                'why_dijkstra': 'Dijkstra is the safest baseline for shortest-path correctness.',
                'why_astar': 'A* can be better in search efficiency, but it still matches Dijkstra on optimality when the heuristic is admissible.',
                'why_greedy': 'Greedy is not guaranteed to be globally optimal.',
                'recommended': 'Dijkstra and A* are both correct shortest-path methods; A* is often faster, but Dijkstra is easier to justify academically.'
            }

        return jsonify({
            'success': True,
            'routes': algorithms_data,
            'best_algorithm': best_algo,
            'best_algorithms': optimal_algos,
            'best_distance': best_distance,
            'analysis': analysis,
            'optimal_algorithms': optimal_algos
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/mst', methods=['POST'])
def compute_mst():
    """Compute Minimum Spanning Tree"""
    req_data = request.json
    prioritize_critical = req_data.get('prioritize_critical', True)
    
    try:
        mst_edges = mst.kruskal_mst(prioritize_critical)
        cost_analysis = mst.calculate_cost_effectiveness()
        
        # Format edges for visualization
        edges = []
        for edge in mst_edges:
            from_name = get_node_name(edge[0])
            to_name = get_node_name(edge[1])
            
            from_coords = get_node_coordinate(edge[0])
            to_coords = get_node_coordinate(edge[1])
            
            edges.append({
                'from': {
                    'id': edge[0],
                    'name': from_name,
                    'x': from_coords[0] if from_coords else 0,
                    'y': from_coords[1] if from_coords else 0
                },
                'to': {
                    'id': edge[1],
                    'name': to_name,
                    'x': to_coords[0] if to_coords else 0,
                    'y': to_coords[1] if to_coords else 0
                },
                'weight': edge[2],
                'type': edge[3]
            })
        
        return jsonify({
            'success': True,
            'edges': edges,
            'cost_analysis': cost_analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/emergency-route', methods=['POST'])
def emergency_route():
    """Calculate emergency vehicle route"""
    req_data = request.json
    start = req_data['start']
    hospital = req_data['hospital']
    priority = req_data.get('priority', 2)
    time_hour = req_data.get('time_hour')
    road_closures = _normalize_avoid_roads(req_data.get('road_closures'))
    
    try:
        start_id = int(start) if str(start).isdigit() else start
        hospital_id = int(hospital) if str(hospital).isdigit() else hospital

        if time_hour is None:
            time_hour = __import__('datetime').datetime.now().hour

        result = astar.find_path(
            start_id,
            hospital_id,
            heuristic_type='euclidean',
            emergency_priority=int(priority),
            time_hour=int(time_hour),
            avoid_edges=road_closures
        )

        path = result.get('path', [])
        distance = result.get('distance', float('inf'))
        
        # Convert path to coordinates for visualization
        path_coords = []
        for node in path:
            coords = get_node_coordinate(node)
            if coords:
                path_coords.append({
                    'id': node,
                    'name': get_node_name(node),
                    'x': coords[0],
                    'y': coords[1]
                })

        # Build route segments for visualization
        segments = []
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i+1]
            matched = None
            for road in data.roads:
                if (road.from_id == a and road.to_id == b) or (road.from_id == b and road.to_id == a):
                    matched = road
                    break

            from_coords = get_node_coordinate(a) or (None, None)
            to_coords = get_node_coordinate(b) or (None, None)
            segments.append({
                'from': a,
                'to': b,
                'distance': matched.distance if matched else None,
                'coords': [
                    {'x': from_coords[0], 'y': from_coords[1]},
                    {'x': to_coords[0], 'y': to_coords[1]}
                ]
            })

        # Try OSRM geometry for the entire path
        osrm_geom = _get_osrm_geometry_for_path(path)
        preemption_plan = None
        if path:
            signals = {node: {'N': 30, 'S': 30, 'E': 20, 'W': 20} for node in path}
            severity_map = {3: 'critical', 2: 'emergency', 1: 'urgent'}
            preemption_plan = greedy.emergency_vehicle_preemption(
                [{'type': severity_map.get(int(priority), 'urgent'), 'path': path, 'response_time': 0}],
                signals
            )
        if osrm_geom:
            return jsonify({
                'success': bool(path),
                'path': path_coords,
                'segments': segments,
                'osrm_geometry': osrm_geom,
                'distance': distance,
                'estimated_time': (distance / 40) * 60 if distance != float('inf') else 0,
                'nodes_explored': len(path_coords),
                'preemption_plan': preemption_plan
            })

        return jsonify({
            'success': bool(path),
            'path': path_coords,
            'segments': segments,
            'distance': distance,
            'estimated_time': (distance / 40) * 60 if distance != float('inf') else 0,
            'nodes_explored': len(path_coords),
            'preemption_plan': preemption_plan
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/ml-status')
def ml_status():
    """Return the traffic predictor status for the web UI."""
    return jsonify({
        'trained': ml_predictor.trained,
        'models': list(ml_predictor.models.keys())
    })

@app.route('/api/optimize-signals', methods=['POST'])
def optimize_signals():
    """Optimize traffic signals"""
    req_data = request.json
    intersections = req_data.get('intersections', [3, 5, 10])
    
    try:
        result = greedy.optimize_traffic_signals(intersections)
        
        return jsonify({
            'success': True,
            'signal_phases': result['signal_phases']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/optimize-transit', methods=['POST'])
def optimize_transit():
    """Optimize public transit schedules"""
    try:
        total_buses = sum(b.buses_assigned for b in data.bus_routes)
        buses = list(range(total_buses))
        routes = [b.stops for b in data.bus_routes]
        demands = [b.daily_passengers for b in data.bus_routes]

        result = dp.optimize_bus_schedules(buses, routes, demands)
        transfer_points = _get_transfer_points()
        integration = dp.optimize_transport_integration(
            data.metro_lines, data.bus_routes, transfer_points
        )
        
        return jsonify({
            'success': True,
            'max_passengers': result['max_passengers_served'],
            'assignments': result['bus_assignments'],
            'total_hours': result['total_hours_used'],
            'integration': integration
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/transit-data')
def transit_data():
    """Return metro/bus routes with coordinates for visualization."""
    metro_lines = []
    for line in data.metro_lines:
        stops = []
        for stop in line.stations:
            coords = get_node_coordinate(stop)
            if coords:
                stops.append({'id': stop, 'x': coords[0], 'y': coords[1]})
        metro_lines.append({
            'id': line.id,
            'name': line.name,
            'stations': stops,
            'daily_passengers': line.daily_passengers
        })

    bus_routes = []
    for route in data.bus_routes:
        stops = []
        for stop in route.stops:
            coords = get_node_coordinate(stop)
            if coords:
                stops.append({'id': stop, 'x': coords[0], 'y': coords[1]})
        bus_routes.append({
            'id': route.id,
            'stops': stops,
            'buses_assigned': route.buses_assigned,
            'daily_passengers': route.daily_passengers
        })

    return jsonify({
        'success': True,
        'metro_lines': metro_lines,
        'bus_routes': bus_routes,
        'transport_demand': data.transport_demand
    })

@app.route('/api/predict-traffic', methods=['POST'])
def predict_traffic():
    """Predict traffic using ML model"""
    req_data = request.json
    hour = req_data.get('hour', 8)
    day_type = req_data.get('day_type', 'weekday')
    road_id = req_data.get('road_id', '1-3')
    
    try:
        conditions = {
            'hour': hour,
            'day_of_week': 1 if day_type == 'weekday' else 6,
            'is_weekend': day_type == 'weekend',
            'road_capacity': 3000,
            'road_condition': 7,
            'road_length': 10.0,
            'from_population': 300000,
            'to_population': 300000,
            'historical_avg': 2500,
            'traffic_lag_1h': 2000,
            'traffic_lag_2h': 1800,
            'traffic_lag_24h': 2200,
            'is_holiday': False
        }
        
        prediction = ml_predictor.predict(conditions)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'road_id': road_id,
            'hour': hour
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/compare-algorithms', methods=['POST'])
def compare_algorithms():
    """Compare different pathfinding algorithms"""
    req_data = request.json
    start = req_data.get('start', 1)
    end = req_data.get('end', 5)
    time_hour = req_data.get('time_hour', 10)

    start = int(start) if str(start).isdigit() else start
    end = int(end) if str(end).isdigit() else end
    
    results = []
    
    try:
        # Dijkstra
        start_time = __import__('time').time()
        path_d, dist_d = sp.dijkstra(start, end, time_hour)
        dijkstra_time = __import__('time').time() - start_time

        # A* (time-aware)
        start_time = __import__('time').time()
        astar_result = astar.find_path(
            start,
            end,
            heuristic_type='euclidean',
            emergency_priority=1,
            time_hour=time_hour
        )
        astar_time = __import__('time').time() - start_time
        path_a = astar_result.get('path', [])
        dist_a = astar_result.get('distance', float('inf'))

        # Greedy
        start_time = __import__('time').time()
        result_g = greedy.greedy_route_recommendation(start, end, hour=time_hour)
        greedy_time = __import__('time').time() - start_time

        # Time-varying Dijkstra
        start_time = __import__('time').time()
        tv = sp.time_varying_shortest_path(start, end, time_hour)
        tv_time = __import__('time').time() - start_time
        tv_path = tv.get('recommended_route', [])
        if tv_path == tv.get('off_peak_route'):
            tv_dist = tv.get('off_peak_distance')
        else:
            tv_dist = tv.get('peak_distance')

        results = [
            {
                'name': 'Dijkstra',
                'distance': dist_d,
                'path_length': len(path_d),
                'time': dijkstra_time * 1000,  # ms
                'color': '#3498db'
            },
            {
                'name': 'A* Search',
                'distance': dist_a,
                'path_length': len(path_a),
                'time': astar_time * 1000,
                'nodes_explored': astar_result.get('nodes_explored'),
                'color': '#e74c3c'
            },
            {
                'name': 'Greedy',
                'distance': result_g.get('total_distance', float('inf')),
                'path_length': len(result_g.get('path', [])),
                'time': greedy_time * 1000,
                'color': '#f39c12'
            },
            {
                'name': 'Time-Varying',
                'distance': tv_dist if tv_dist is not None else float('inf'),
                'path_length': len(tv_path),
                'time': tv_time * 1000,
                'color': '#2ecc71'
            }
        ]
        # Sanitize results for frontend (Chart.js can't plot Infinity)
        import math
        for r in results:
            if not isinstance(r.get('time'), (int, float)):
                r['time'] = 0.0
            d = r.get('distance')
            if d is None or (isinstance(d, float) and not math.isfinite(d)):
                r['distance'] = None

        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/statistics')
def get_statistics():
    """Get system statistics"""
    total_population = sum(n.population for n in data.neighborhoods.values())
    total_daily_transit = sum(m.daily_passengers for m in data.metro_lines)
    
    return jsonify({
        'neighborhoods': len(data.neighborhoods),
        'total_population': total_population,
        'roads': len(data.roads),
        'planned_roads': len(data.potential_roads),
        'facilities': len(data.facilities),
        'metro_lines': len(data.metro_lines),
        'bus_routes': len(data.bus_routes),
        'daily_transit_users': total_daily_transit,
        'traffic_patterns': len(data.traffic_patterns)
    })

# ==================== Helper Functions ====================

def get_node_name(node_id):
    """Get node name from ID"""
    if isinstance(node_id, int) and node_id in data.neighborhoods:
        return data.neighborhoods[node_id].name
    elif isinstance(node_id, str):
        for fid, facility in data.facilities.items():
            if fid == node_id:
                return facility.name
    return str(node_id)

def get_node_coordinate(node_id):
    """Get node coordinates"""
    if isinstance(node_id, int) and node_id in data.neighborhoods:
        n = data.neighborhoods[node_id]
        return (n.x, n.y)
    elif isinstance(node_id, str):
        for fid, facility in data.facilities.items():
            if fid == node_id:
                return (facility.x, facility.y)
    return None


def _normalize_avoid_roads(value):
    """Normalize avoid-road inputs into a list of road key strings."""
    if not value:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(',')]
    elif isinstance(value, list):
        parts = [str(p).strip() for p in value]
    else:
        return []

    cleaned = []
    for item in parts:
        if item and '-' in item:
            cleaned.append(item)
    return cleaned


def _get_transfer_points():
    """Compute shared transfer points between metro lines and bus routes."""
    metro_stops = set()
    for line in data.metro_lines:
        metro_stops.update(line.stations)

    bus_stops = set()
    for route in data.bus_routes:
        bus_stops.update(route.stops)

    return list(metro_stops.intersection(bus_stops))

def _fetch_osrm_geometry(coords):
    """Fetch a road-following geometry from OSRM for a list of (lon, lat) tuples."""
    if not OSRM_BASE_URL or len(coords) < 2:
        return None

    coords_str = ";".join([f"{lon},{lat}" for lon, lat in coords])
    url = f"{OSRM_BASE_URL}/route/v1/{OSRM_PROFILE}/{coords_str}?overview=full&geometries=geojson"

    try:
        resp = requests.get(url, timeout=OSRM_TIMEOUT)
        if resp.status_code != 200:
            return None
        jr = resp.json()
        routes = jr.get('routes') or []
        if not routes:
            return None
        geom = routes[0].get('geometry', {}).get('coordinates', [])
        if not geom:
            return None
        # OSRM returns [lon, lat] pairs
        return [{'x': c[0], 'y': c[1]} for c in geom]
    except Exception:
        return None


def _get_osrm_geometry_for_path(path):
    """Request OSRM for a route geometry that follows roads for the given ordered node path.
    Returns a list of {'x': lon, 'y': lat} coordinates or None on failure."""
    if not path or len(path) < 2:
        return None

    coords = []
    for node in path:
        c = get_node_coordinate(node)
        if not c:
            return None
        coords.append((c[0], c[1]))

    # Try a single OSRM request for the full route first.
    full_geom = _fetch_osrm_geometry(coords)
    if full_geom:
        return full_geom

    # Fallback: stitch per-segment geometries to reduce failure cases.
    stitched = []
    for i in range(len(coords) - 1):
        segment_geom = _fetch_osrm_geometry([coords[i], coords[i + 1]])
        if not segment_geom:
            return None
        if stitched:
            stitched.extend(segment_geom[1:])
        else:
            stitched.extend(segment_geom)

    return stitched or None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)