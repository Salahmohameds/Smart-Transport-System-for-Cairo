import networkx as nx
import math
from operator import itemgetter

def run_mst_algorithm(G, neighborhoods, facilities, existing_roads, potential_roads, 
                     prioritize_hospitals=True, prioritize_high_population=True):
    """
    Implements Kruskal's algorithm to find the minimum spanning tree for the transportation network.
    
    Args:
        G: The original network as a NetworkX graph
        neighborhoods: List of neighborhood data
        facilities: List of facility data
        existing_roads: List of existing road data
        potential_roads: List of potential new road data
        prioritize_hospitals: Whether to prioritize connections to hospitals
        prioritize_high_population: Whether to prioritize connections between high-population areas
        
    Returns:
        mst_graph: The MST as a NetworkX graph
        total_cost: The total cost of the MST solution
        results: Dictionary with additional information
    """
    # Create a new graph for MST calculation
    mst_graph = nx.Graph()
    
    # Add all nodes
    for node in neighborhoods:
        mst_graph.add_node(node['id'], 
                           name=node['name'], 
                           population=node['population'], 
                           type=node['type'], 
                           x=node['x'], 
                           y=node['y'])
        
    for node in facilities:
        mst_graph.add_node(node['id'], 
                           name=node['name'], 
                           type=node['type'], 
                           x=node['x'], 
                           y=node['y'])
    
    # Prepare edges for Kruskal's algorithm
    edges = []
    
    # Process existing roads
    for road in existing_roads:
        # Calculate a cost based on the inverse of road condition (worse condition = higher cost)
        maintenance_cost = (11 - road['condition']) * 10  # Scale from 10 to 100
        
        # Apply prioritization factors
        weight = road['distance'] * maintenance_cost
        
        # Prioritize high-population areas if enabled
        if prioritize_high_population:
            # Check if this road connects high-population areas
            source_id = road['from']
            target_id = road['to']
            
            source_pop = None
            target_pop = None
            
            # Get population data for neighborhoods
            for n in neighborhoods:
                if n['id'] == source_id:
                    source_pop = n['population']
                if n['id'] == target_id:
                    target_pop = n['population']
            
            # If both are neighborhoods with high population, reduce the weight
            if source_pop and target_pop and (source_pop >= 400000 or target_pop >= 400000):
                weight *= 0.7  # 30% discount for high-population areas
        
        # Prioritize hospital connections if enabled
        if prioritize_hospitals:
            # Check if this road connects to a hospital
            source_id = road['from']
            target_id = road['to']
            
            is_hospital_connection = False
            
            # Check if either end is a hospital (F9 or F10)
            if source_id == "F9" or source_id == "F10" or target_id == "F9" or target_id == "F10":
                is_hospital_connection = True
                
            # Also prioritize connections to the airport (F1)
            if source_id == "F1" or target_id == "F1":
                is_hospital_connection = True
            
            if is_hospital_connection:
                weight *= 0.6  # 40% discount for connections to hospitals/airport
        
        # Add the edge
        edges.append((
            road['from'], 
            road['to'], 
            {
                'weight': weight,
                'distance': road['distance'],
                'capacity': road['capacity'],
                'condition': road['condition'],
                'road_type': 'existing',
                'original_weight': weight,
                'cost': maintenance_cost
            }
        ))
    
    # Process potential new roads
    for road in potential_roads:
        # Use construction cost directly as the weight
        weight = road['cost']
        
        # Apply same prioritization factors
        # Prioritize high-population areas if enabled
        if prioritize_high_population:
            # Check if this road connects high-population areas
            source_id = road['from']
            target_id = road['to']
            
            source_pop = None
            target_pop = None
            
            # Get population data for neighborhoods
            for n in neighborhoods:
                if n['id'] == source_id:
                    source_pop = n['population']
                if n['id'] == target_id:
                    target_pop = n['population']
            
            # If both are neighborhoods with high population, reduce the weight
            if source_pop and target_pop and (source_pop >= 400000 or target_pop >= 400000):
                weight *= 0.8  # 20% discount for high-population areas
        
        # Prioritize hospital connections if enabled
        if prioritize_hospitals:
            # Check if this road connects to a hospital
            source_id = road['from']
            target_id = road['to']
            
            is_hospital_connection = False
            
            # Check if either end is a hospital (F9 or F10)
            if source_id == "F9" or source_id == "F10" or target_id == "F9" or target_id == "F10":
                is_hospital_connection = True
                
            # Also prioritize connections to the airport (F1)
            if source_id == "F1" or target_id == "F1":
                is_hospital_connection = True
            
            if is_hospital_connection:
                weight *= 0.7  # 30% discount for connections to hospitals/airport
        
        # Add the edge
        edges.append((
            road['from'], 
            road['to'], 
            {
                'weight': weight,
                'distance': road['distance'],
                'capacity': road['capacity'],
                'cost': road['cost'],  # Construction cost in millions EGP
                'road_type': 'potential',
                'original_weight': weight
            }
        ))
    
    # Sort edges by weight for Kruskal's algorithm
    edges.sort(key=lambda x: x[2]['weight'])
    
    # Implement Kruskal's algorithm
    # Initialize each node as a separate tree
    trees = {node: {node} for node in mst_graph.nodes()}
    
    # Track selected edges
    selected_roads = []
    existing_count = 0
    new_count = 0
    total_cost = 0
    
    # Kruskal's algorithm
    for u, v, data in edges:
        # If u and v are in different trees
        if trees[u] != trees[v]:
            # Add the edge to the MST
            mst_graph.add_edge(u, v, **data)
            selected_roads.append({
                'from': u,
                'to': v,
                'distance': data['distance'],
                'road_type': data['road_type'],
                'weight': data['weight']
            })
            
            # Track costs
            if data['road_type'] == 'existing':
                # Use maintenance cost
                existing_count += 1
                total_cost += data.get('cost', 0)
            else:
                # Use construction cost for new roads
                new_count += 1
                total_cost += data.get('cost', 0)
            
            # Merge trees
            union = trees[u].union(trees[v])
            for node in union:
                trees[node] = union
    
    # Check if all nodes are connected (should be in a single tree)
    all_connected = len(set(frozenset(tree) for tree in trees.values())) == 1
    
    # Count critical facilities that are connected
    critical_facilities = ["F1", "F9", "F10"]  # Airport and hospitals
    connected_critical = sum(1 for facility in critical_facilities if any(
        road['from'] == facility or road['to'] == facility for road in selected_roads
    ))
    
    # Prepare the results
    results = {
        "selected_roads": selected_roads,
        "existing_roads_count": existing_count,
        "new_roads_count": new_count,
        "all_connected": all_connected,
        "critical_facilities_connected": connected_critical,
        "total_critical_facilities": len(critical_facilities)
    }
    
    return mst_graph, total_cost, results
