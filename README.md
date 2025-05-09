# Smart City Transportation Network Optimization System

## Project Overview
This project is a comprehensive transportation network optimization system for Greater Cairo, built using Python and Streamlit. It provides an interactive platform for urban planners, traffic engineers, and city officials to analyze and optimize various aspects of the city's transportation network using different algorithms.

## Features

### 1. Infrastructure Network Design (Minimum Spanning Tree)
- **Algorithm**: Uses Kruskal's algorithm to find the minimum spanning tree of the transportation network
- **Purpose**: Identifies the optimal road network that connects all neighborhoods and key facilities while minimizing total construction and maintenance costs
- **Parameters**:
  - Option to include potential new roads in the analysis
  - Prioritization for hospital connections
  - Prioritization for high-population neighborhoods
- **Output**:
  - Interactive map visualization of the optimal road network
  - Statistics on total cost, number of roads, new roads added, etc.

### 2. Traffic Flow Optimization (Dijkstra's Algorithm)
- **Algorithm**: Implements Dijkstra's algorithm with time-dependent edge weights
- **Purpose**: Finds the fastest route between any two points considering real-time traffic conditions
- **Parameters**:
  - Time of day (morning peak, afternoon, evening peak, night)
  - Origin and destination points
- **Output**:
  - Interactive map visualization of the optimal route
  - Travel time and distance statistics
  - Comparison of travel times across different times of day
  - Detailed step-by-step route information

### 3. Emergency Response Planning (A* Search)
- **Algorithm**: Implements A* search algorithm with a Euclidean distance heuristic
- **Purpose**: Optimizes routes for emergency vehicles to hospitals considering road conditions
- **Parameters**:
  - Emergency location
  - Target hospital (or option to find nearest)
  - Minimum acceptable road condition
- **Output**:
  - Interactive map visualization of the emergency route
  - Travel time estimations
  - Comparison with standard routing
  - Road condition analysis

### 4. Public Transit Optimization (Dynamic Programming)
- **Algorithm**: Dynamic programming approach for optimizing bus allocations
- **Purpose**: Optimizes the allocation of buses across different routes to minimize passenger waiting times
- **Parameters**:
  - Total available buses
  - Maximum acceptable waiting time
  - Option to optimize metro-bus transfers
- **Output**:
  - Transit network map visualization showing routes and allocations
  - Bus allocation charts and metrics
  - Waiting time analysis by route
  - Transfer point optimization results

### 5. Traffic Signal Optimization (Greedy Algorithm)
- **Algorithm**: Greedy algorithm for signal timing
- **Purpose**: Optimizes traffic signal timings at intersections to minimize delays
- **Parameters**:
  - Intersection selection
  - Time period to optimize for
  - Optimization priority (minimize delay, prioritize high-traffic roads, balance wait times)
  - Maximum cycle length
- **Output**:
  - Visual representation of signal timing plan
  - Performance metrics (cycle length, wait times, improvement vs. fixed timing)
  - Traffic flow analysis by direction

## Technical Details

### Data Components
1. **Neighborhoods**: 15 neighborhoods in Greater Cairo with population data
2. **Facilities**: 10 key facilities including hospitals, transportation hubs, and educational institutions
3. **Road Network**:
   - Existing roads with distances, capacities, and condition ratings
   - Potential new roads with construction costs
4. **Traffic Flows**: Time-dependent traffic flow data for different times of day

### Implementation
- **Backend**: Python with NetworkX for graph algorithms
- **Frontend**: Streamlit for interactive web interface
- **Visualization**: Folium for map visualizations, Plotly for charts and diagrams

### Algorithms
1. **Minimum Spanning Tree (Kruskal's Algorithm)**:
   - Time Complexity: O(E log E) where E is the number of edges
   - Space Complexity: O(V + E) where V is the number of vertices
   - Customized with priority weighting for critical connections

2. **Dijkstra's Algorithm**:
   - Time Complexity: O((V + E) log V)
   - Implemented with time-dependent edge weights to account for traffic flow variations

3. **A* Search Algorithm**:
   - Time Complexity: O(E)
   - Uses Euclidean distance heuristic for better performance
   - Customized to consider road conditions for emergency routing

4. **Dynamic Programming for Transit Optimization**:
   - Optimizes bus allocations across routes based on passenger demand
   - Handles transfer coordination between metro and bus systems

5. **Greedy Algorithm for Traffic Signal Timing**:
   - Optimizes green time allocations with multiple priority options
   - Models intersection flow to balance throughput and waiting times

## Installation and Setup

### Prerequisites
- Python 3.8+
- Required Python packages: streamlit, pandas, folium, streamlit-folium, networkx, matplotlib, plotly

### Installation
1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application
```
streamlit run app.py
```

## Project Structure
- `app.py`: Main Streamlit application
- `src/data/loader.py`: Data loading functions for Cairo transportation network
- `src/algorithms/mst.py`: Minimum Spanning Tree implementation
- `src/algorithms/shortestpath.py`: Implementation of Dijkstra and A* algorithms
- `src/algorithms/dp.py`: Dynamic Programming for public transit optimization
- `src/algorithms/greedy.py`: Greedy algorithm for traffic signal optimization
- `src/visualization/network.py`: Network visualization utilities

## Future Enhancements
1. **Real-time Data Integration**: Connect to real-time traffic data sources
2. **Machine Learning for Traffic Prediction**: Implement ML models to predict traffic flows
3. **Multi-objective Optimization**: Extend algorithms to handle multiple objectives (e.g., minimize both travel time and emissions)
4. **Public Transportation Schedule Optimization**: Add detailed scheduling functionality for public transit
5. **Pedestrian and Cycling Infrastructure**: Add analysis for non-vehicular transportation modes
6. **Demographic Analysis**: Include demographic data for more nuanced transportation planning

## Acknowledgements
- This project utilizes data from publicly available sources about Cairo's transportation network
- Algorithms implemented with inspiration from transportation research literature