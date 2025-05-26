import networkx as nx
import heapq
import math
from collections import deque

def run_dijkstra(G, origin, destination, time_period, traffic_flows):
    """
    Implements Dijkstra's algorithm for finding the shortest path with time-dependent weights.
    
    Args:
        G: NetworkX graph representing the road network
        origin: ID of the origin node
        destination: ID of the destination node
        time_period: Time period to consider (morning_peak, afternoon, evening_peak, night)
        traffic_flows: Dictionary containing traffic flow data
        
    Returns:
        path: List of nodes in the shortest path
        travel_time: Estimated travel time in minutes
        path_edges: List of edges in the path
        results: Dictionary with additional information
    """
    # Create a copy of the graph to modify weights
    temp_graph = G.copy()
    
    # Dictionary to map bidirectional road IDs
    road_id_map = {}
    for road_id in traffic_flows:
        nodes = road_id.split("-")
        road_id_map[(nodes[0], nodes[1])] = road_id
        road_id_map[(nodes[1], nodes[0])] = road_id  # Bidirectional
    
    # Update edge weights based on time period and traffic flows
    for u, v, data in temp_graph.edges(data=True):
        # Create a consistent key for the edge
        edge_key = (str(u), str(v))
        reversed_edge_key = (str(v), str(u))
        
        # Get original distance
        distance = data.get('distance', 1.0)
        
        # Find traffic flow data for this road if it exists
        traffic_factor = 1.0
        
        if edge_key in road_id_map:
            road_id = road_id_map[edge_key]
            if road_id in traffic_flows:
                # Calculate traffic factor based on flow vs capacity
                flow = traffic_flows[road_id].get(time_period, 0)
                capacity = data.get('capacity', 3000)
                
                # Volume-to-capacity ratio affects speed
                v_c_ratio = flow / capacity if capacity > 0 else 1.0
                
                # Use BPR function for travel time
                # t = t0 * (1 + 0.15 * (v/c)^4)
                traffic_factor = 1.0 + 0.15 * (v_c_ratio ** 4)
        
        elif reversed_edge_key in road_id_map:
            road_id = road_id_map[reversed_edge_key]
            if road_id in traffic_flows:
                # Calculate traffic factor based on flow vs capacity
                flow = traffic_flows[road_id].get(time_period, 0)
                capacity = data.get('capacity', 3000)
                
                # Volume-to-capacity ratio affects speed
                v_c_ratio = flow / capacity if capacity > 0 else 1.0
                
                # Use BPR function for travel time
                traffic_factor = 1.0 + 0.15 * (v_c_ratio ** 4)
        
        # Consider road condition for speed
        condition = data.get('condition', 5)
        condition_factor = 1.2 - (condition / 10)  # Better condition means faster travel
        
        # Update weight as travel time (distance / speed, where speed is affected by traffic and condition)
        # Assume base speed of 60 km/h for a road with condition 10 and no traffic
        time_weight = distance / (60 * (1 / traffic_factor) * (1 / condition_factor)) * 60  # Travel time in minutes
        
        # Update the edge weight
        temp_graph[u][v]['weight'] = time_weight
        temp_graph[u][v]['time'] = time_weight
        temp_graph[u][v]['traffic_factor'] = traffic_factor
    
    # Run Dijkstra's algorithm
    try:
        path = nx.shortest_path(temp_graph, source=origin, target=destination, weight='weight')
        travel_time = nx.shortest_path_length(temp_graph, source=origin, target=destination, weight='weight')
        
        # Get edges along the path
        path_edges = []
        total_distance = 0
        
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            
            # Get edge data
            edge_data = temp_graph[u][v]
            
            # Extract relevant information
            road_info = {
                "from": u,
                "to": v,
                "distance": edge_data.get('distance', 0),
                "time": edge_data.get('time', 0),
                "traffic_factor": edge_data.get('traffic_factor', 1.0),
                "road_type": edge_data.get('road_type', 'existing')
            }
            
            path_edges.append(road_info)
            total_distance += edge_data.get('distance', 0)
        
        # Calculate congestion level (1-10 scale)
        avg_traffic_factor = sum(edge['traffic_factor'] for edge in path_edges) / len(path_edges)
        congestion_level = min(10, int(avg_traffic_factor * 5))
        
        # Compare with other time periods (without recursion)
        time_comparison = {}
        for period in ["morning_peak", "afternoon", "evening_peak", "night"]:
            if period == time_period:
                # Already calculated for current period
                time_comparison[period] = travel_time
                continue
                
            # Create a temporary graph for this time period
            period_graph = G.copy()
            
            # Update edge weights for this period
            for u, v, data in period_graph.edges(data=True):
                # Create a consistent key for the edge
                edge_key = (str(u), str(v))
                reversed_edge_key = (str(v), str(u))
                
                # Get original distance
                distance = data.get('distance', 1.0)
                
                # Calculate traffic factor
                traffic_factor = 1.0
                if edge_key in road_id_map and road_id_map[edge_key] in traffic_flows:
                    flow = traffic_flows[road_id_map[edge_key]].get(period, 0)
                    capacity = data.get('capacity', 3000)
                    v_c_ratio = flow / capacity if capacity > 0 else 1.0
                    traffic_factor = 1.0 + 0.15 * (v_c_ratio ** 4)
                elif reversed_edge_key in road_id_map and road_id_map[reversed_edge_key] in traffic_flows:
                    flow = traffic_flows[road_id_map[reversed_edge_key]].get(period, 0)
                    capacity = data.get('capacity', 3000)
                    v_c_ratio = flow / capacity if capacity > 0 else 1.0
                    traffic_factor = 1.0 + 0.15 * (v_c_ratio ** 4)
                
                # Consider road condition
                condition = data.get('condition', 5)
                condition_factor = 1.2 - (condition / 10)
                
                # Update weight
                time_weight = distance / (60 * (1 / traffic_factor) * (1 / condition_factor)) * 60
                period_graph[u][v]['weight'] = time_weight
            
            # Calculate shortest path for this period
            try:
                period_time = nx.shortest_path_length(period_graph, source=origin, target=destination, weight='weight')
                time_comparison[period] = period_time
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                time_comparison[period] = float('inf')
        
        # Create route details for display
        route_details = []
        for i, edge in enumerate(path_edges):
            from_node = get_node_name(G, edge["from"])
            to_node = get_node_name(G, edge["to"])
            
            route_details.append({
                "Step": i + 1,
                "From": from_node,
                "To": to_node,
                "Distance (km)": f"{edge['distance']:.1f}",
                "Time (min)": f"{edge['time']:.1f}",
                "Traffic": "Heavy" if edge['traffic_factor'] > 1.3 else 
                           "Moderate" if edge['traffic_factor'] > 1.1 else "Light"
            })
        
        # Prepare results
        results = {
            "total_distance": total_distance,
            "congestion_level": congestion_level,
            "time_comparison": time_comparison,
            "route_details": route_details
        }
        
        return path, travel_time, path_edges, results
    
    except nx.NetworkXNoPath:
        return None, float('inf'), [], {"error": "No path found"}

def get_node_name(G, node_id):
    """Helper function to get node name from id"""
    if node_id in G.nodes:
        if 'name' in G.nodes[node_id]:
            return G.nodes[node_id]['name']
    return str(node_id)

def run_a_star(G, emergency_location, target_hospital, neighborhoods, facilities, min_road_condition=6):
    """
    Implements A* search algorithm for emergency response planning.
    
    Args:
        G: NetworkX graph representing the road network
        emergency_location: ID of the emergency location
        target_hospital: ID of the target hospital (or None for nearest)
        neighborhoods: List of neighborhood data
        facilities: List of facility data
        min_road_condition: Minimum acceptable road condition
        
    Returns:
        path: List of nodes in the shortest path
        travel_time: Estimated travel time in minutes
        path_edges: List of edges in the path
        results: Dictionary with additional information
    """
    # First, make sure the hospital IDs are valid
    hospital_ids = []
    for facility in facilities:
        if facility['type'] == 'Medical':
            hospital_ids.append(facility['id'])
    
    if not hospital_ids:
        hospital_ids = ["F9", "F10"]  # Fallback to default if no medical facilities found
    
    # Step 1: Check if the emergency location has any path to a hospital in the original graph
    original_graph = G.copy()
    has_any_path = False
    for hospital_id in hospital_ids:
        try:
            if nx.has_path(original_graph, source=emergency_location, target=hospital_id):
                has_any_path = True
                break
        except Exception as e:
            print(f"Path check error: {str(e)}")
            continue
    
    if not has_any_path:
        # Critical situation: No path exists even in the original graph
        return None, float('inf'), [], {"error": "No path exists to any hospital in the network"}
    
    # Step 2: Create a copy of the graph for emergency routing
    emergency_graph = G.copy()
    
    # Step 3: Apply road condition penalties instead of removing edges
    for u, v, data in emergency_graph.edges(data=True):
        condition = data.get('condition', 5)
        if condition < min_road_condition:
            # Apply a penalty based on road condition
                penalty_factor = 1 + ((min_road_condition - condition) / 5)
                if 'distance' in data:
                    emergency_graph[u][v]['distance'] *= penalty_factor
                # Also store the original distance for travel time calculation
                emergency_graph[u][v]['original_distance'] = data['distance']
    
    # If target hospital not specified, find nearest hospital
    target_hospital_id = target_hospital
    
    if not target_hospital_id:
        # Use standard Dijkstra to find nearest hospital
        distances = {}
        for hospital_id in hospital_ids:
            try:
                # Check if there's a path to this hospital
                path_length = nx.shortest_path_length(
                    emergency_graph, 
                    source=emergency_location, 
                    target=hospital_id, 
                    weight='distance'
                )
                distances[hospital_id] = path_length
            except nx.NetworkXNoPath:
                distances[hospital_id] = float('inf')
        
        # Find the closest hospital with a valid path
        if distances:
            min_distance = float('inf')
            for hosp_id, dist in distances.items():
                if dist < min_distance:
                    min_distance = dist
                    target_hospital_id = hosp_id
        else:
            return None, float('inf'), [], {"error": "No path to any hospital"}
    
    # Get hospital coordinates
    hospital_data = next((f for f in facilities if f['id'] == target_hospital_id), None)
    
    if not hospital_data:
        return None, float('inf'), [], {"error": "Hospital not found"}
    
    hospital_coords = (hospital_data['x'], hospital_data['y'])
    
    # Define heuristic function for A* (Euclidean distance)
    def heuristic(node):
        node_data = None
        
        # Find coordinates of the node
        for n in neighborhoods:
            if n['id'] == node:
                node_data = n
                break
        
        if not node_data:
            for f in facilities:
                if f['id'] == node:
                    node_data = f
                    break
        
        if node_data:
            # Calculate Euclidean distance
            node_coords = (node_data['x'], node_data['y'])
            return math.sqrt((node_coords[0] - hospital_coords[0])**2 + 
                             (node_coords[1] - hospital_coords[1])**2) * 10  # Scale to km approx
        
        return 0
    
    # Implement A* algorithm
    open_set = [(0, emergency_location)]  # Priority queue with (f_score, node)
    came_from = {}
    g_score = {node: float('inf') for node in emergency_graph.nodes()}
    g_score[emergency_location] = 0
    f_score = {node: float('inf') for node in emergency_graph.nodes()}
    f_score[emergency_location] = heuristic(emergency_location)
    
    while open_set:
        # Get node with lowest f_score
        current_f, current = heapq.heappop(open_set)
        
        if current == target_hospital_id:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            
            # Calculate travel time and get path edges
            path_edges = []
            total_distance = 0
            total_time = 0
            total_condition = 0
            
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i+1]
                
                # Get edge data
                edge_data = emergency_graph[u][v]
                
                # Use original distance for travel time calculation
                distance = edge_data.get('original_distance', edge_data.get('distance', 0))
                condition = edge_data.get('condition', 5)
                
                # Emergency vehicles can travel faster
                # Better road condition means higher speed
                speed_factor = 1.0 + (condition / 10) * 0.5  # Up to 50% speed boost for good roads
                
                # Emergency speed (km/h) - base 80 km/h adjusted for road condition
                emergency_speed = 80 * speed_factor
                
                # Time in minutes
                time = (distance / emergency_speed) * 60
                
                road_info = {
                    "from": u,
                    "to": v,
                    "distance": distance,
                    "time": time,
                    "condition": condition,
                    "road_type": edge_data.get('road_type', 'existing')
                }
                
                path_edges.append(road_info)
                total_distance += distance
                total_time += time
                total_condition += condition
            
            avg_road_condition = total_condition / len(path_edges) if path_edges else 0
            
            # Calculate standard routing time for comparison
            try:
                standard_time = nx.shortest_path_length(emergency_graph, source=emergency_location, target=target_hospital_id, weight='distance') / 60
            except nx.NetworkXNoPath:
                standard_time = float('inf')
            
            # Prepare results
            results = {
                "total_distance": total_distance,
                "avg_road_condition": avg_road_condition,
                "standard_time": standard_time,
                "hospital_id": target_hospital_id,
                "route_details": path_edges
            }
            
            return path, total_time, path_edges, results
        
        # Explore neighbors
        for neighbor in emergency_graph.neighbors(current):
            # Calculate edge cost considering both distance and road condition
            edge_data = emergency_graph[current][neighbor]
            distance = edge_data.get('distance', 0)
            condition = edge_data.get('condition', 5)
            
            # Calculate edge cost: distance * (1 + condition penalty)
            # Better condition = lower cost
            condition_penalty = (11 - condition) / 10  # 0 for condition 10, 1 for condition 1
            edge_cost = distance * (1 + condition_penalty)
            
            tentative_g_score = g_score[current] + edge_cost
            
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None, float('inf'), [], {"error": "No path found"}
