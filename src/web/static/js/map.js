// ===== Cairo Transportation Map Functions =====

class CairoMap {
    constructor() {
        this.map = null;
        this.neighborhoodMarkers = [];
        this.facilityMarkers = [];
        this.roadLines = [];
        this.routeLines = [];
    }
    
    init(containerId, options = {}) {
        this.map = L.map(containerId, {
            center: options.center || [30.0444, 31.2357],
            zoom: options.zoom || 11
        });
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        return this.map;
    }
    
    async loadNetworkData() {
        try {
            const data = await api.getNetworkData();
            this.renderNetwork(data);
            return data;
        } catch (error) {
            console.error('Error loading network data:', error);
        }
    }
    
    renderNetwork(data) {
        // Clear existing
        this.clearAll();
        
        // Add neighborhoods
        data.neighborhoods.forEach(n => {
            this.addNeighborhood(n);
        });
        
        // Add facilities
        data.facilities.forEach(f => {
            this.addFacility(f);
        });
        
        // Add roads
        data.roads.forEach(road => {
            const fromNode = this.findNode(data, road.from);
            const toNode = this.findNode(data, road.to);
            
            if (fromNode && toNode) {
                this.addRoad(fromNode, toNode, road);
            }
        });
    }
    
    findNode(data, nodeId) {
        const neighborhood = data.neighborhoods.find(n => n.id === nodeId);
        if (neighborhood) return neighborhood;
        
        const facility = data.facilities.find(f => f.id === nodeId);
        if (facility) return facility;
        
        return null;
    }
    
    addNeighborhood(neighborhood) {
        const color = Utils.getNodeColor(neighborhood.type);
        const marker = L.circleMarker([neighborhood.y, neighborhood.x], {
            radius: Math.max(6, Math.log(neighborhood.population) / 2),
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup(`
            <div class="map-popup">
                <h6>${neighborhood.name}</h6>
                <p><strong>Population:</strong> ${neighborhood.population.toLocaleString()}</p>
                <p><strong>Type:</strong> ${neighborhood.type}</p>
                <p><strong>Coordinates:</strong> ${neighborhood.x.toFixed(2)}, ${neighborhood.y.toFixed(2)}</p>
            </div>
        `).addTo(this.map);
        
        this.neighborhoodMarkers.push(marker);
        return marker;
    }
    
    addFacility(facility) {
        const icon = L.divIcon({
            html: `<div class="facility-icon facility-${facility.type.toLowerCase()}">
                    <i class="fas ${Utils.getFacilityIcon(facility.type)}"></i>
                   </div>`,
            className: 'custom-div-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        const marker = L.marker([facility.y, facility.x], { icon })
            .bindPopup(`
                <div class="map-popup">
                    <h6>${facility.name}</h6>
                    <p><strong>Type:</strong> ${facility.type}</p>
                </div>
            `)
            .addTo(this.map);
        
        this.facilityMarkers.push(marker);
        return marker;
    }
    
    addRoad(fromNode, toNode, roadData) {
        const line = L.polyline(
            [[fromNode.y, fromNode.x], [toNode.y, toNode.x]],
            {
                color: this.getRoadColor(roadData.condition),
                weight: Math.max(2, roadData.capacity / 1000),
                opacity: 0.7
            }
        ).bindPopup(`
            <div class="map-popup">
                <h6>Road ${roadData.from}-${roadData.to}</h6>
                <p><strong>Distance:</strong> ${roadData.distance} km</p>
                <p><strong>Capacity:</strong> ${roadData.capacity} vehicles/hour</p>
                <p><strong>Condition:</strong> ${roadData.condition}/10</p>
            </div>
        `).addTo(this.map);
        
        this.roadLines.push(line);
        return line;
    }
    
    addRoutePath(path, options = {}) {
        const coordinates = path.map(node => [node.y, node.x]);
        
        const line = L.polyline(coordinates, {
            color: options.color || '#e74c3c',
            weight: options.weight || 5,
            opacity: 0.8,
            dashArray: options.dashArray || null
        }).addTo(this.map);
        
        // Add start and end markers
        if (path.length > 0) {
            const start = path[0];
            const end = path[path.length - 1];
            
            L.marker([start.y, start.x], {
                icon: L.divIcon({
                    html: '<div class="route-marker start">S</div>',
                    className: 'route-marker-div',
                    iconSize: [30, 30]
                })
            }).addTo(this.map);
            
            L.marker([end.y, end.x], {
                icon: L.divIcon({
                    html: '<div class="route-marker end">E</div>',
                    className: 'route-marker-div',
                    iconSize: [30, 30]
                })
            }).addTo(this.map);
        }
        
        this.routeLines.push(line);
        
        // Fit map to show the route
        this.map.fitBounds(coordinates, { padding: [50, 50] });
        
        return line;
    }
    
    getRoadColor(condition) {
        if (condition >= 8) return '#2ecc71';
        if (condition >= 6) return '#f1c40f';
        if (condition >= 4) return '#e67e22';
        return '#e74c3c';
    }
    
    clearAll() {
        this.neighborhoodMarkers.forEach(m => this.map.removeLayer(m));
        this.facilityMarkers.forEach(m => this.map.removeLayer(m));
        this.roadLines.forEach(l => this.map.removeLayer(l));
        this.clearRoutes();
        
        this.neighborhoodMarkers = [];
        this.facilityMarkers = [];
        this.roadLines = [];
    }
    
    clearRoutes() {
        this.routeLines.forEach(l => this.map.removeLayer(l));
        this.routeLines = [];
    }
}

// Initialize global map
window.CairoMap = CairoMap;