// ===== Cairo Smart Transportation Main JavaScript =====

// Utility Functions
class Utils {
    static formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    static getNodeColor(type) {
        const colors = {
            'Residential': '#2ecc71',
            'Business': '#3498db',
            'Mixed': '#f39c12',
            'Industrial': '#e74c3c',
            'Government': '#9b59b6'
        };
        return colors[type] || '#95a5a6';
    }
    
    static getFacilityIcon(type) {
        const icons = {
            'Airport': 'fa-plane',
            'Transit Hub': 'fa-train',
            'Education': 'fa-graduation-cap',
            'Medical': 'fa-hospital',
            'Tourism': 'fa-camera',
            'Sports': 'fa-futbol',
            'Business': 'fa-briefcase',
            'Commercial': 'fa-shopping-cart'
        };
        return icons[type] || 'fa-map-marker';
    }
    
    static showLoading(element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
    
    static hideLoading(element, content) {
        element.innerHTML = content;
    }
    
    static showAlert(message, type = 'success', duration = 3000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        
        if (duration) {
            setTimeout(() => {
                alertDiv.remove();
            }, duration);
        }
    }
}

// Map Manager
class MapManager {
    constructor(containerId, options = {}) {
        this.map = L.map(containerId, {
            center: options.center || [30.0444, 31.2357],
            zoom: options.zoom || 11,
            layers: [L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')]
        });
        this.layers = {};
        this.markers = [];
    }
    
    addNeighborhoodMarker(neighborhood) {
        const color = Utils.getNodeColor(neighborhood.type);
        const marker = L.circleMarker([neighborhood.y, neighborhood.x], {
            radius: 8,
            fillColor: color,
            color: color,
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7
        })
        .bindPopup(`
            <b>${neighborhood.name}</b><br>
            Population: ${neighborhood.population.toLocaleString()}<br>
            Type: ${neighborhood.type}
        `)
        .addTo(this.map);
        
        this.markers.push(marker);
        return marker;
    }
    
    addFacilityMarker(facility) {
        const icon = Utils.getFacilityIcon(facility.type);
        const marker = L.marker([facility.y, facility.x], {
            icon: L.divIcon({
                html: `<i class="fas ${icon}" style="color: red; font-size: 20px;"></i>`,
                className: 'facility-marker'
            })
        })
        .bindPopup(`
            <b>${facility.name}</b><br>
            Type: ${facility.type}
        `)
        .addTo(this.map);
        
        this.markers.push(marker);
        return marker;
    }
    
    addRoad(from, to, options = {}) {
        if (!from || !to) return null;
        
        const polyline = L.polyline(
            [[from.y, from.x], [to.y, to.x]],
            {
                color: options.color || '#95a5a6',
                weight: options.weight || 2,
                opacity: options.opacity || 0.6,
                dashArray: options.dashArray || null
            }
        )
        .bindPopup(options.popup || '')
        .addTo(this.map);
        
        return polyline;
    }
    
    addRoutePath(path, color = '#e74c3c', weight = 4) {
        const coordinates = path.map(node => [node.y, node.x]);
        return L.polyline(coordinates, {
            color: color,
            weight: weight,
            opacity: 0.8
        }).addTo(this.map);
    }
    
    fitToBounds(coordinates) {
        this.map.fitBounds(coordinates, { padding: [50, 50] });
    }
    
    clearLayer(layer) {
        if (layer) {
            this.map.removeLayer(layer);
        }
    }
    
    clearAllMarkers() {
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];
    }
}

// Chart Manager
class ChartManager {
    static createTrafficChart(canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const hours = Array.from({length: 24}, (_, i) => i);
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [
                    {
                        label: 'Morning Pattern',
                        data: hours.map(h => 800 + 800 * Math.sin(Math.PI * h / 12)),
                        borderColor: '#FF6B6B',
                        tension: 0.4,
                        fill: true,
                        backgroundColor: 'rgba(255, 107, 107, 0.1)'
                    },
                    {
                        label: 'Afternoon Pattern',
                        data: hours.map(h => 1000 + 600 * Math.sin(Math.PI * (h - 6) / 12)),
                        borderColor: '#4ECDC4',
                        tension: 0.4,
                        fill: true,
                        backgroundColor: 'rgba(78, 205, 196, 0.1)'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
    
    static createComparisonChart(canvasId, algorithmsData) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: algorithmsData.map(a => a.name),
                datasets: [
                    {
                        label: 'Execution Time (ms)',
                        data: algorithmsData.map(a => a.time),
                        backgroundColor: algorithmsData.map(a => a.color),
                        yAxisID: 'y-time'
                    },
                    {
                        label: 'Distance (km)',
                        data: algorithmsData.map(a => a.distance),
                        backgroundColor: 'rgba(149, 165, 166, 0.5)',
                        yAxisID: 'y-distance'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    'y-time': {
                        type: 'linear',
                        position: 'left',
                        title: { display: true, text: 'Time (ms)' }
                    },
                    'y-distance': {
                        type: 'linear',
                        position: 'right',
                        title: { display: true, text: 'Distance (km)' }
                    }
                }
            }
        });
    }
}

// Export utilities for global use
window.Utils = Utils;
window.MapManager = MapManager;
window.ChartManager = ChartManager;

// Populate intersection checkboxes (used by traffic.html)
async function loadIntersections() {
    try {
        // Use global api instance from api.js
        if (typeof api === 'undefined') {
            console.warn('API helper not found; falling back to /api/network-data');
            const resp = await fetch('/api/network-data');
            const data = await resp.json();
            renderIntersections(data);
            return;
        }

        const data = await api.getNetworkData();
        renderIntersections(data);
    } catch (err) {
        console.error('Failed to load intersections', err);
    }
}

function renderIntersections(data) {
    const container = document.getElementById('intersection-checkboxes');
    if (!container) return;
    container.innerHTML = '';

    // Combine neighborhoods and facilities as potential intersections
    const items = [];
    if (data.neighborhoods) items.push(...data.neighborhoods.map(n => ({id: n.id, name: n.name})));
    if (data.facilities) items.push(...data.facilities.map(f => ({id: f.id, name: f.name})));

    items.forEach(it => {
        const id = `intersection-${it.id}`;
        const wrapper = document.createElement('div');
        wrapper.className = 'form-check';
        wrapper.innerHTML = `
            <input class="form-check-input" type="checkbox" value="${it.id}" id="${id}">
            <label class="form-check-label" for="${id}">${it.name}</label>
        `;
        container.appendChild(wrapper);
    });
}

// Called when user clicks "Optimize Signals" button
async function optimizeSignals() {
    const btn = document.getElementById('optimize-signals-btn');
    const resultsDiv = document.getElementById('signal-results');
    if (!btn) return;

    // Gather selected intersections
    const checkboxes = Array.from(document.querySelectorAll('#intersection-checkboxes input[type=checkbox]:checked'));
    const intersections = checkboxes.map(cb => cb.value);

    if (intersections.length === 0) {
        Utils.showAlert('Please select at least one intersection to optimize', 'warning');
        return;
    }

    // Show loading state
    btn.disabled = true;
    const prevHtml = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Optimizing...';
    resultsDiv.style.display = 'none';

    try {
        let resp;
        if (typeof api !== 'undefined') {
            resp = await api.optimizeSignals(intersections);
        } else {
            const r = await fetch('/api/optimize-signals', {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({intersections})
            });
            resp = await r.json();
        }

        if (!resp || !resp.success) {
            Utils.showAlert('Signal optimization failed', 'danger');
            console.error('optimizeSignals response', resp);
            return;
        }

        // Render basic results
        resultsDiv.innerHTML = '';
        const phases = resp.signal_phases || resp.signalPhases || {};
        const pre = document.createElement('pre');
        pre.style.whiteSpace = 'pre-wrap';
        pre.textContent = JSON.stringify(phases, null, 2);
        resultsDiv.appendChild(pre);
        resultsDiv.style.display = 'block';
        Utils.showAlert('Signal optimization completed', 'success');
    } catch (err) {
        console.error('Error optimizing signals', err);
        Utils.showAlert('Error optimizing signals', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = prevHtml;
    }
}

// Export for global use (templates rely on these names)
window.loadIntersections = loadIntersections;
window.optimizeSignals = optimizeSignals;