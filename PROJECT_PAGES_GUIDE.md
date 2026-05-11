# Cairo Transportation System - Page Guide

## Pages Overview

### 1. **Traffic** (`/traffic`)
**Purpose:** Optimize real-time traffic flow and signal timing

**Features:**
- **Route Planning** (left panel):
  - Find shortest route between 2 locations using Dijkstra, A*, or Greedy algorithms
  - Select time of day (Morning Peak, Afternoon, Evening Peak, Night) to account for traffic patterns
  - Optional: Specify roads to avoid
  - Map displays calculated route as red polyline
  - Shows distance, path details, and estimated travel time
  
- **Signal Optimization** (right panel):
  - Select multiple intersections (neighborhoods/facilities)
  - Click "Optimize Signals" to compute optimal green light timing
  - Backend uses proportional allocation based on traffic flow per direction
  - Results displayed as JSON with signal phase times for each intersection

- **Time-Varying Analysis**:
  - Shows how traffic volume changes throughout the day for a selected road
  - Chart with hourly patterns (Morning/Afternoon patterns)

**Test Cases:**
- Start: "Sheikh Zayed", End: "Giza", Algorithm: "A* Search", Time: "Morning Peak" → should draw route on map
- Check intersections 1, 3, F2 → Click "Optimize Signals" → shows signal_phases JSON

---

### 2. **Infrastructure** (`/infrastructure`)
**Purpose:** Design and optimize transportation infrastructure

**Features:**
- **Network Overview Map**: 
  - Shows all neighborhoods (green circles) and facilities (markers)
  - Pan/zoom the network
  
- **Design Actions**:
  - **Build MST Button**: Calculates Minimum Spanning Tree using Kruskal's algorithm
  - MST identifies the most cost-effective roads to connect all neighborhoods
  - Returns:
    - Number of roads in the MST
    - Cost analysis (estimated savings, existing vs new roads)
    - Edges with `from`, `to`, `weight`, and `type` (Existing/New)
  - Chart shows edges count and estimated savings
  
- **Use Case**: Plan infrastructure investments, identify critical roads, understand network connectivity

**Test Case:**
- Click "Build MST" → Chart updates showing number of roads and cost savings

---

### 3. **Transit** (`/transit`)
**Purpose:** Optimize public transit scheduling and bus route assignments

**Features:**
- **Transit Scheduling**:
  - **Optimize Bus Schedules Button**: Uses dynamic programming to assign buses to routes
  - Optimizes passenger capacity utilization across metro lines and bus routes
  - Returns:
    - Max passengers that can be served
    - Total hours of transit operation
    - List of bus assignments (bus_id → route_id mappings)
  
- **Demand Overview Chart**:
  - Shows mode split: 45% Metro, 30% Bus, 20% Private Cars, 5% Walking
  - Helps visualize public vs private transport usage
  
- **Use Case**: Plan fleet deployment, manage passenger flow, optimize resource allocation

**Test Case:**
- Click "Optimize Bus Schedules" → Shows passengers served (540000), total hours (18), assignments count

---

### 4. **Emergency** (`/emergency`)
**Purpose:** Plan optimal routes for emergency vehicles

**Features:**
- **Emergency Route Planner**:
  - Select Incident Location and Hospital
  - Uses A* search with priority weighting (critical/emergency faster than regular)
  - Draws fastest route from incident to nearest hospital
  - Uses preemption logic: critical emergencies clear all traffic signals
  
- **Route Display**:
  - Red polyline on map showing emergency vehicle path
  - Status displays: distance (km), estimated time (minutes), nodes explored
  
- **Use Case**: Dispatch emergency vehicles (ambulances, fire trucks), minimize response time

**Test Case:**
- Start: "Maadi", Hospital: "Qasr El Aini Hospital" → Click "Plan" → Route drawn on map with time/distance

---

### 5. **Compare** (`/comparison`)
**Purpose:** Benchmark different pathfinding algorithms

**Features:**
- **Comparison Controls**:
  - Input start/end nodes and hour of day
  - Compare 3 algorithms: Dijkstra, A*, Greedy
  
- **Metrics**:
  - Execution time (ms)
  - Path distance (km)
  - Path length (number of nodes)
  
- **Chart**: Bar chart showing time vs distance for each algorithm

**Current Issue - GREEDY RETURNS NULL:**
- When Greedy algorithm can't find a path from start to end (gets stuck), it returns incomplete path without total_distance
- Backend sanitizes this to `distance: null` for frontend safety
- Chart displays the null value but it's visually confusing

**Test Case:**
- Start: 1, End: 5 → Dijkstra: 16.3 km (good), A*: 14.6 km (better), Greedy: null (stuck)
- Start: 1, End: 3 → All three algorithms succeed

---

## Current Issues & Fixes Applied

### ✅ Find Route Button - FIXED
- **Issue**: Button did nothing
- **Cause**: `findRoute()` function was defined inline in traffic.html but not handling errors properly
- **Fix**: Already implemented in traffic.html

### ✅ Optimize Signals Button - FIXED  
- **Issue**: Button did nothing
- **Cause**: `loadIntersections()` and `optimizeSignals()` functions were missing from main.js
- **Fix**: Added to src/web/static/js/main.js with proper error handling

### ✅ Emergency Route Drawing - FIXED
- **Issue**: Route calculated but not drawn on map
- **Cause**: `planEmergency()` didn't render polyline
- **Fix**: Added polyline drawing logic to emergency.html

### ⚠️ Greedy in Compare - PARTIALLY WORKING
- **Issue**: Greedy shows `distance: null` when it can't find a path
- **Cause**: Greedy algorithm gets stuck on some routes; backend correctly sanitizes Infinity → null
- **Root Cause**: Greedy algorithm is incomplete/dead-end; not all nodes are reachable via greedy heuristic
- **Current Behavior**: Works fine on some start/end pairs, returns null on others
- **Recommendation**: This is algorithm behavior, not a bug. Greedy is simpler but less reliable than Dijkstra/A*

---

## API Test Cases (curl/Python)

### Find Route
```bash
curl -X POST http://127.0.0.1:5000/api/shortest-path \
  -H "Content-Type: application/json" \
  -d '{"start":"1","end":"3","algorithm":"astar","time_hour":8}'
```
Expected: Route with path nodes containing coordinates

### Optimize Signals
```bash
curl -X POST http://127.0.0.1:5000/api/optimize-signals \
  -H "Content-Type: application/json" \
  -d '{"intersections":["1","3"]}'
```
Expected: signal_phases object with timing for each intersection

### Emergency Route
```bash
curl -X POST http://127.0.0.1:5000/api/emergency-route \
  -H "Content-Type: application/json" \
  -d '{"start":"1","hospital":"F9","priority":3}'
```
Expected: Route with path, estimated_time, distance

### Compare Algorithms
```bash
curl -X POST http://127.0.0.1:5000/api/compare-algorithms \
  -H "Content-Type: application/json" \
  -d '{"start":"1","end":"5","time_hour":10}'
```
Expected: Results array with Dijkstra, A*, and Greedy entries (Greedy may have null distance)

### Build MST
```bash
curl -X POST http://127.0.0.1:5000/api/mst \
  -H "Content-Type: application/json" \
  -d '{"prioritize_critical":true}'
```
Expected: edges array with from/to/weight/type, cost_analysis with total_cost

### Optimize Transit
```bash
curl -X POST http://127.0.0.1:5000/api/optimize-transit \
  -H "Content-Type: application/json" \
  -d '{}'
```
Expected: max_passengers, total_hours, assignments array
