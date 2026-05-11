// ===== Cairo Smart Transportation API Handler =====

class CairoTransportAPI {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
    }
    
    // Get network data
    async getNetworkData() {
        try {
            const response = await fetch(`${this.baseURL}/network-data`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching network data:', error);
            throw error;
        }
    }
    
    // Calculate shortest path
    async getShortestPath(start, end, algorithm = 'dijkstra', timeHour = 10) {
        try {
            const response = await fetch(`${this.baseURL}/shortest-path`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start: start.toString(),
                    end: end.toString(),
                    algorithm,
                    time_hour: timeHour
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error calculating shortest path:', error);
            throw error;
        }
    }
    
    // Compute MST
    async computeMST(prioritizeCritical = true) {
        try {
            const response = await fetch(`${this.baseURL}/mst`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prioritize_critical: prioritizeCritical
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error computing MST:', error);
            throw error;
        }
    }
    
    // Get emergency route
    async getEmergencyRoute(start, hospital, priority = 2) {
        try {
            const response = await fetch(`${this.baseURL}/emergency-route`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start,
                    hospital,
                    priority
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error calculating emergency route:', error);
            throw error;
        }
    }
    
    // Optimize traffic signals
    async optimizeSignals(intersections) {
        try {
            const response = await fetch(`${this.baseURL}/optimize-signals`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    intersections
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error optimizing signals:', error);
            throw error;
        }
    }
    
    // Optimize transit schedules
    async optimizeTransit() {
        try {
            const response = await fetch(`${this.baseURL}/optimize-transit`, {
                method: 'POST'
            });
            return await response.json();
        } catch (error) {
            console.error('Error optimizing transit:', error);
            throw error;
        }
    }
    
    // Predict traffic with ML
    async predictTraffic(hour, dayType = 'weekday', roadId = '1-3') {
        try {
            const response = await fetch(`${this.baseURL}/predict-traffic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    hour,
                    day_type: dayType,
                    road_id: roadId
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error predicting traffic:', error);
            throw error;
        }
    }
    
    // Compare algorithms
    async compareAlgorithms(start, end, timeHour = 10) {
        try {
            const response = await fetch(`${this.baseURL}/compare-algorithms`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start,
                    end,
                    time_hour: timeHour
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error comparing algorithms:', error);
            throw error;
        }
    }
    
    // Get system statistics
    async getStatistics() {
        try {
            const response = await fetch(`${this.baseURL}/statistics`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching statistics:', error);
            throw error;
        }
    }
}

// Create global API instance
const api = new CairoTransportAPI();