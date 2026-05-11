"""
Algorithm Comparison Visualizer
Compares performance of different algorithms on transportation optimization problems
"""
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime


class ComparisonVisualizer:
    """
    Visualizes comparisons between different algorithms
    """

    def __init__(self, figure_size: Tuple = (15, 10)):
        self.figure_size = figure_size
        self.comparison_results = {}

    def plot_shortest_path_comparison(self, results: Dict[str, Dict],
                                     title: str = "Shortest Path Algorithms Comparison",
                                     save_path: str = None):
        """
        Compare shortest path algorithms (Dijkstra's vs A* vs time-aware)
        
        results format: {
            'algorithm_name': {
                'distance': float,
                'time': float,
                'nodes_explored': int,
                'path_length': int
            }
        }
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figure_size)
        
        algorithms = list(results.keys())
        distances = [results[a]['distance'] for a in algorithms]
        times = [results[a]['time'] for a in algorithms]
        nodes_explored = [results[a]['nodes_explored'] for a in algorithms]
        path_lengths = [results[a]['path_length'] for a in algorithms]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(algorithms)))
        
        # Distance comparison
        ax = axes[0, 0]
        ax.bar(algorithms, distances, color=colors)
        ax.set_ylabel('Distance (km)', fontsize=11, fontweight='bold')
        ax.set_title('Total Distance', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(distances):
            ax.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Computation time comparison
        ax = axes[0, 1]
        ax.bar(algorithms, times, color=colors)
        ax.set_ylabel('Time (ms)', fontsize=11, fontweight='bold')
        ax.set_title('Computation Time', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(times):
            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Nodes explored comparison
        ax = axes[1, 0]
        ax.bar(algorithms, nodes_explored, color=colors)
        ax.set_ylabel('Nodes Explored', fontsize=11, fontweight='bold')
        ax.set_title('Search Space Complexity', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(nodes_explored):
            ax.text(i, v, str(int(v)), ha='center', va='bottom', fontweight='bold')
        
        # Efficiency score (distance/time)
        ax = axes[1, 1]
        efficiency = [d/t if t > 0 else 0 for d, t in zip(distances, times)]
        ax.bar(algorithms, efficiency, color=colors)
        ax.set_ylabel('Efficiency (km/ms)', fontsize=11, fontweight='bold')
        ax.set_title('Route Efficiency', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(efficiency):
            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def plot_mst_comparison(self, results: Dict[str, Dict],
                           title: str = "MST Algorithms Comparison",
                           save_path: str = None):
        """
        Compare MST algorithms (Kruskal's vs Prim's)
        
        results format: {
            'algorithm_name': {
                'total_cost': float,
                'edges_selected': int,
                'time': float,
                'cost_per_edge': float
            }
        }
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figure_size)
        
        algorithms = list(results.keys())
        total_costs = [results[a]['total_cost'] for a in algorithms]
        edges = [results[a]['edges_selected'] for a in algorithms]
        times = [results[a]['time'] for a in algorithms]
        cost_per_edge = [results[a]['cost_per_edge'] for a in algorithms]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(algorithms)))
        
        # Total cost comparison
        ax = axes[0, 0]
        ax.bar(algorithms, total_costs, color=colors)
        ax.set_ylabel('Total Cost (Million EGP)', fontsize=11, fontweight='bold')
        ax.set_title('Network Construction Cost', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(total_costs):
            ax.text(i, v, f'{v:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # Edges selected
        ax = axes[0, 1]
        ax.bar(algorithms, edges, color=colors)
        ax.set_ylabel('Number of Edges', fontsize=11, fontweight='bold')
        ax.set_title('Edges in MST', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(edges):
            ax.text(i, v, str(int(v)), ha='center', va='bottom', fontweight='bold')
        
        # Computation time
        ax = axes[1, 0]
        ax.bar(algorithms, times, color=colors)
        ax.set_ylabel('Time (ms)', fontsize=11, fontweight='bold')
        ax.set_title('Computation Time', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(times):
            ax.text(i, v, f'{v:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Cost efficiency
        ax = axes[1, 1]
        ax.bar(algorithms, cost_per_edge, color=colors)
        ax.set_ylabel('Cost per Edge', fontsize=11, fontweight='bold')
        ax.set_title('Cost Efficiency', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(cost_per_edge):
            ax.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def plot_traffic_simulation_comparison(self, scenarios: Dict[str, Dict],
                                          title: str = "Traffic Simulation Scenarios",
                                          save_path: str = None):
        """
        Compare traffic simulations across different scenarios
        
        scenarios format: {
            'scenario_name': {
                'avg_congestion': float,
                'peak_congestion': float,
                'bottlenecks': int,
                'avg_travel_time': float
            }
        }
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figure_size)
        
        scenarios_list = list(scenarios.keys())
        avg_congestion = [scenarios[s]['avg_congestion'] for s in scenarios_list]
        peak_congestion = [scenarios[s]['peak_congestion'] for s in scenarios_list]
        bottlenecks = [scenarios[s]['bottlenecks'] for s in scenarios_list]
        travel_times = [scenarios[s]['avg_travel_time'] for s in scenarios_list]
        
        colors = plt.cm.RdYlGn_r(np.linspace(0, 1, len(scenarios_list)))
        
        # Average congestion
        ax = axes[0, 0]
        ax.bar(scenarios_list, avg_congestion, color=colors)
        ax.set_ylabel('Average Congestion Level', fontsize=11, fontweight='bold')
        ax.set_title('Network Congestion', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(avg_congestion):
            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Peak congestion
        ax = axes[0, 1]
        ax.bar(scenarios_list, peak_congestion, color=colors)
        ax.set_ylabel('Peak Congestion Level', fontsize=11, fontweight='bold')
        ax.set_title('Peak Hour Congestion', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(peak_congestion):
            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
        
        # Bottleneck count
        ax = axes[1, 0]
        ax.bar(scenarios_list, bottlenecks, color=colors)
        ax.set_ylabel('Number of Bottlenecks', fontsize=11, fontweight='bold')
        ax.set_title('Traffic Bottlenecks', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(bottlenecks):
            ax.text(i, v, str(int(v)), ha='center', va='bottom', fontweight='bold')
        
        # Average travel time
        ax = axes[1, 1]
        ax.bar(scenarios_list, travel_times, color=colors)
        ax.set_ylabel('Average Travel Time (minutes)', fontsize=11, fontweight='bold')
        ax.set_title('Route Duration', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(travel_times):
            ax.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def plot_emergency_response_comparison(self, vehicles: Dict[str, Dict],
                                          title: str = "Emergency Response Performance",
                                          save_path: str = None):
        """
        Compare emergency response vehicle performance
        
        vehicles format: {
            'vehicle_id': {
                'avg_response_time': float,
                'calls_handled': int,
                'distance_traveled': float,
                'efficiency': float
            }
        }
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figure_size)
        
        vehicle_ids = list(vehicles.keys())
        response_times = [vehicles[v]['avg_response_time'] for v in vehicle_ids]
        calls = [vehicles[v]['calls_handled'] for v in vehicle_ids]
        distances = [vehicles[v]['distance_traveled'] for v in vehicle_ids]
        efficiency = [vehicles[v]['efficiency'] for v in vehicle_ids]
        
        colors = plt.cm.Spectral(np.linspace(0, 1, len(vehicle_ids)))
        
        # Response time
        ax = axes[0, 0]
        ax.barh(vehicle_ids, response_times, color=colors)
        ax.set_xlabel('Average Response Time (minutes)', fontsize=11, fontweight='bold')
        ax.set_title('Emergency Response Time', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        for i, v in enumerate(response_times):
            ax.text(v, i, f'{v:.1f}', va='center', ha='left', fontweight='bold')
        
        # Calls handled
        ax = axes[0, 1]
        ax.barh(vehicle_ids, calls, color=colors)
        ax.set_xlabel('Calls Handled', fontsize=11, fontweight='bold')
        ax.set_title('Workload Distribution', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        for i, v in enumerate(calls):
            ax.text(v, i, str(int(v)), va='center', ha='left', fontweight='bold')
        
        # Distance traveled
        ax = axes[1, 0]
        ax.barh(vehicle_ids, distances, color=colors)
        ax.set_xlabel('Distance Traveled (km)', fontsize=11, fontweight='bold')
        ax.set_title('Total Distance', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        for i, v in enumerate(distances):
            ax.text(v, i, f'{v:.1f}', va='center', ha='left', fontweight='bold')
        
        # Efficiency
        ax = axes[1, 1]
        ax.barh(vehicle_ids, efficiency, color=colors)
        ax.set_xlabel('Efficiency (calls/100km)', fontsize=11, fontweight='bold')
        ax.set_title('Response Efficiency', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        for i, v in enumerate(efficiency):
            ax.text(v, i, f'{v:.2f}', va='center', ha='left', fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def plot_dynamic_programming_comparison(self, schedules: Dict[str, Dict],
                                           title: str = "DP Solutions Comparison",
                                           save_path: str = None):
        """
        Compare dynamic programming solutions
        
        schedules format: {
            'solution_name': {
                'passengers_served': int,
                'cost': float,
                'utilization': float,
                'wait_time': float
            }
        }
        """
        fig, axes = plt.subplots(2, 2, figsize=self.figure_size)
        
        solutions = list(schedules.keys())
        passengers = [schedules[s]['passengers_served'] for s in solutions]
        costs = [schedules[s]['cost'] for s in solutions]
        utilization = [schedules[s]['utilization'] for s in solutions]
        wait_times = [schedules[s]['wait_time'] for s in solutions]
        
        colors = plt.cm.viridis(np.linspace(0, 1, len(solutions)))
        
        # Passengers served
        ax = axes[0, 0]
        ax.bar(solutions, passengers, color=colors)
        ax.set_ylabel('Passengers Served', fontsize=11, fontweight='bold')
        ax.set_title('Capacity Utilization', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(passengers):
            ax.text(i, v, str(int(v)), ha='center', va='bottom', fontweight='bold')
        
        # Cost
        ax = axes[0, 1]
        ax.bar(solutions, costs, color=colors)
        ax.set_ylabel('Operating Cost (EGP)', fontsize=11, fontweight='bold')
        ax.set_title('Operating Cost', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(costs):
            ax.text(i, v, f'{v:.0f}', ha='center', va='bottom', fontweight='bold')
        
        # Resource utilization
        ax = axes[1, 0]
        ax.bar(solutions, utilization, color=colors)
        ax.set_ylabel('Utilization Rate', fontsize=11, fontweight='bold')
        ax.set_title('Resource Utilization', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(utilization):
            ax.text(i, v, f'{v:.1%}', ha='center', va='bottom', fontweight='bold')
        
        # Average wait time
        ax = axes[1, 1]
        ax.bar(solutions, wait_times, color=colors)
        ax.set_ylabel('Average Wait Time (minutes)', fontsize=11, fontweight='bold')
        ax.set_title('Passenger Wait Time', fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        for i, v in enumerate(wait_times):
            ax.text(i, v, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def plot_complexity_analysis(self, algorithms: Dict[str, Dict],
                                title: str = "Algorithm Complexity Analysis",
                                save_path: str = None):
        """
        Plot time and space complexity comparison
        
        algorithms format: {
            'algorithm_name': {
                'time_complexity': str,
                'space_complexity': str,
                'avg_execution_time': float,
                'avg_space_used': float
            }
        }
        """
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        
        algo_names = list(algorithms.keys())
        exec_times = [algorithms[a]['avg_execution_time'] for a in algo_names]
        space_used = [algorithms[a]['avg_space_used'] for a in algo_names]
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(algo_names)))
        
        # Execution time
        ax = axes[0]
        bars = ax.bar(algo_names, exec_times, color=colors)
        ax.set_ylabel('Execution Time (ms)', fontsize=12, fontweight='bold')
        ax.set_title('Time Complexity (Practical)', fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Add complexity labels
        for i, (bar, algo) in enumerate(zip(bars, algo_names)):
            time_complexity = algorithms[algo]['time_complexity']
            ax.text(bar.get_x() + bar.get_width()/2, exec_times[i],
                   f'{exec_times[i]:.2f}ms\n({time_complexity})',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Space usage
        ax = axes[1]
        bars = ax.bar(algo_names, space_used, color=colors)
        ax.set_ylabel('Space Used (KB)', fontsize=12, fontweight='bold')
        ax.set_title('Space Complexity (Practical)', fontsize=13, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Add complexity labels
        for i, (bar, algo) in enumerate(zip(bars, algo_names)):
            space_complexity = algorithms[algo]['space_complexity']
            ax.text(bar.get_x() + bar.get_width()/2, space_used[i],
                   f'{space_used[i]:.1f}KB\n({space_complexity})',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig, axes

    def generate_comparison_report(self, report_path: str, 
                                  all_results: Dict[str, Any]):
        """Generate a comprehensive comparison report"""
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("CAIRO TRANSPORTATION SYSTEM - ALGORITHM COMPARISON REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Add summary of all results
            f.write("RESULTS SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(json.dumps(all_results, indent=2, default=str))
            f.write("\n\n")
            
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
