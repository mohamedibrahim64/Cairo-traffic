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
astar = AStarSearch(data.graph, get_node_coordinates(data))

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
    
    try:
        start_str = str(start)
        end_str = str(end)
        start_id = int(start_str) if start_str.isdigit() else start
        end_id = int(end_str) if end_str.isdigit() else end
        
        if algorithm == 'dijkstra':
            path, distance = sp.dijkstra(start_id, end_id, time_hour)
        elif algorithm == 'astar':
            path, distance = sp.a_star_search(start_id, end_id, time_hour)
        elif algorithm == 'greedy':
            result = greedy.greedy_route_recommendation(start_id, end_id, hour=time_hour)
            path = result['path']
            distance = result['total_distance']
        else:
            path, distance = sp.dijkstra(start_id, end_id, time_hour)
        
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
                'osrm_geometry': osrm_geom
            })

        return jsonify({
            'success': True,
            'path': path_names,
            'segments': segments,
            'distance': distance,
            'algorithm': algorithm
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
    
    try:
        start_id = int(start) if str(start).isdigit() else start
        hospital_id = int(hospital) if str(hospital).isdigit() else hospital
        path, distance = sp.a_star_search(start_id, hospital_id)
        
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
        if osrm_geom:
            return jsonify({
                'success': bool(path),
                'path': path_coords,
                'segments': segments,
                'osrm_geometry': osrm_geom,
                'distance': distance,
                'estimated_time': (distance / 40) * 60 if distance != float('inf') else 0,
                'nodes_explored': len(path_coords)
            })

        return jsonify({
            'success': bool(path),
            'path': path_coords,
            'segments': segments,
            'distance': distance,
            'estimated_time': (distance / 40) * 60 if distance != float('inf') else 0,
            'nodes_explored': len(path_coords)
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
        buses = list(range(50))
        routes = [b.stops for b in data.bus_routes]
        demands = [b.daily_passengers for b in data.bus_routes]
        
        result = dp.optimize_bus_schedules(buses, routes, demands)
        
        return jsonify({
            'success': True,
            'max_passengers': result['max_passengers_served'],
            'assignments': result['bus_assignments'],
            'total_hours': result['total_hours_used']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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
        
        # A*
        start_time = __import__('time').time()
        path_a, dist_a = sp.a_star_search(start, end, time_hour)
        astar_time = __import__('time').time() - start_time
        
        # Greedy
        start_time = __import__('time').time()
        result_g = greedy.greedy_route_recommendation(start, end, hour=time_hour)
        greedy_time = __import__('time').time() - start_time
        
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
                'color': '#e74c3c'
            },
            {
                'name': 'Greedy',
                'distance': result_g.get('total_distance', float('inf')),
                'path_length': len(result_g.get('path', [])),
                'time': greedy_time * 1000,
                'color': '#f39c12'
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


def _get_osrm_geometry_for_path(path):
    """Request OSRM public server for a route geometry that follows roads for the given ordered node path.
    Returns a list of {'x': lon, 'y': lat} coordinates or None on failure."""
    if not path or len(path) < 2:
        return None

    coords_parts = []
    for node in path:
        c = get_node_coordinate(node)
        if not c:
            return None
        lon, lat = c[0], c[1]
        coords_parts.append(f"{lon},{lat}")

    coords_str = ";".join(coords_parts)
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None
        jr = resp.json()
        routes = jr.get('routes') or []
        if not routes:
            return None
        geom = routes[0].get('geometry', {}).get('coordinates', [])
        # OSRM gives [lon, lat] pairs
        converted = [{'x': c[0], 'y': c[1]} for c in geom]
        return converted
    except Exception:
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)