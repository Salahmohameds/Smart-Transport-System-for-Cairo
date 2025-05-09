import folium
from folium import plugins
import branca.colormap as cm
import math

def create_base_map(neighborhoods, facilities, existing_roads):
    """
    Creates a base map with all neighborhoods and facilities.
    
    Args:
        neighborhoods: List of neighborhood data
        facilities: List of facility data
        existing_roads: List of existing road data
        
    Returns:
        folium.Map: A map object with neighborhoods and facilities
    """
    # Calculate center of the map
    all_x = [n['x'] for n in neighborhoods] + [f['x'] for f in facilities]
    all_y = [n['y'] for n in neighborhoods] + [f['y'] for f in facilities]
    
    center_x = sum(all_x) / len(all_x)
    center_y = sum(all_y) / len(all_y)
    
    # Create a map centered on Cairo
    m = folium.Map(location=[center_y, center_x], zoom_start=11, tiles='cartodbpositron')
    
    # Add neighborhood markers
    for node in neighborhoods:
        # Define marker color based on neighborhood type
        color_map = {
            'Residential': 'blue',
            'Business': 'red',
            'Mixed': 'purple',
            'Industrial': 'gray',
            'Government': 'green'
        }
        
        color = color_map.get(node['type'], 'blue')
        
        # Create a circle marker for each neighborhood
        # Size based on population
        radius = math.sqrt(node['population'] / 10000) * 3
        
        folium.CircleMarker(
            location=[node['y'], node['x']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2,
            popup=f"<b>{node['name']}</b><br>ID: {node['id']}<br>Population: {node['population']:,}<br>Type: {node['type']}"
        ).add_to(m)
        
        # Add text label
        folium.map.Marker(
            [node['y'], node['x']],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, 0),
                html=f'<div style="font-size: 10pt; color: black; font-weight: bold; background-color: white; border-radius: 3px; padding: 2px;">{node["id"]}</div>'
            )
        ).add_to(m)
    
    # Add facility markers
    for node in facilities:
        # Define marker icon based on facility type
        icon_map = {
            'Airport': 'plane',
            'Transit Hub': 'train',
            'Education': 'graduation-cap',
            'Tourism': 'camera',
            'Sports': 'futbol-o',
            'Business': 'building',
            'Commercial': 'shopping-cart',
            'Medical': 'hospital-o'
        }
        
        icon = icon_map.get(node['type'], 'info-circle')
        
        folium.Marker(
            location=[node['y'], node['x']],
            icon=folium.Icon(icon=icon, prefix='fa', color='cadetblue'),
            popup=f"<b>{node['name']}</b><br>ID: {node['id']}<br>Type: {node['type']}"
        ).add_to(m)
    
    # Add existing roads
    for road in existing_roads:
        # Find coordinates for source and target nodes
        source_coords = None
        target_coords = None
        
        # Search in neighborhoods
        for node in neighborhoods:
            if node['id'] == road['from']:
                source_coords = [node['y'], node['x']]
            if node['id'] == road['to']:
                target_coords = [node['y'], node['x']]
        
        # Search in facilities
        for node in facilities:
            if node['id'] == road['from']:
                source_coords = [node['y'], node['x']]
            if node['id'] == road['to']:
                target_coords = [node['y'], node['x']]
        
        if source_coords and target_coords:
            # Create a line with color based on road condition
            condition = road['condition']
            
            # Color scheme: red (poor) to green (excellent)
            if condition <= 3:
                color = 'red'
            elif condition <= 5:
                color = 'orange'
            elif condition <= 7:
                color = 'blue'
            else:
                color = 'green'
            
            # Line weight based on capacity
            weight = 2 + (road['capacity'] / 1000)
            
            # Create the line
            folium.PolyLine(
                locations=[source_coords, target_coords],
                color=color,
                weight=weight,
                opacity=0.7,
                popup=f"Road {road['from']} - {road['to']}<br>Distance: {road['distance']} km<br>Capacity: {road['capacity']} vehicles<br>Condition: {road['condition']}/10"
            ).add_to(m)
    
    # Add legend for neighborhoods
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border-radius: 5px;">
        <h4 style="margin-top: 0;">Legend</h4>
        <div><span style="background-color: blue; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></span> Residential</div>
        <div><span style="background-color: red; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></span> Business</div>
        <div><span style="background-color: purple; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></span> Mixed</div>
        <div><span style="background-color: gray; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></span> Industrial</div>
        <div><span style="background-color: green; width: 15px; height: 15px; display: inline-block; border-radius: 50%;"></span> Government</div>
        <br>
        <div><span style="background-color: green; width: 15px; height: 3px; display: inline-block;"></span> Excellent Road</div>
        <div><span style="background-color: blue; width: 15px; height: 3px; display: inline-block;"></span> Good Road</div>
        <div><span style="background-color: orange; width: 15px; height: 3px; display: inline-block;"></span> Fair Road</div>
        <div><span style="background-color: red; width: 15px; height: 3px; display: inline-block;"></span> Poor Road</div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add Fullscreen control
    plugins.Fullscreen().add_to(m)
    
    return m

def visualize_solution(neighborhoods, facilities, path_edges, highlight_nodes=None, title=None):
    """
    Visualize a solution on the map.
    
    Args:
        neighborhoods: List of neighborhood data
        facilities: List of facility data
        path_edges: List of edges to highlight
        highlight_nodes: List of nodes to highlight
        title: Title for the map
        
    Returns:
        folium.Map: A map object with the solution visualized
    """
    # Create a base map
    m = create_base_map(neighborhoods, facilities, [])
    
    # Add title if provided
    if title:
        title_html = f'''
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000; background-color: white; padding: 10px; border-radius: 5px; font-size: 18px; font-weight: bold;">
            {title}
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
    
    # Map node IDs to coordinates
    node_coords = {}
    for node in neighborhoods:
        node_coords[node['id']] = [node['y'], node['x']]
    
    for node in facilities:
        node_coords[node['id']] = [node['y'], node['x']]
    
    # Draw the path edges
    for edge in path_edges:
        source_id = edge['from']
        target_id = edge['to']
        
        if source_id in node_coords and target_id in node_coords:
            source_coords = node_coords[source_id]
            target_coords = node_coords[target_id]
            
            # Determine color and style based on edge type
            if edge.get('road_type') == 'potential':
                # New road
                color = 'red'
                dash_array = '5, 5'
                weight = 4
            elif 'traffic_factor' in edge:
                # Traffic-weighted edge
                traffic = edge['traffic_factor']
                if traffic > 1.3:
                    color = 'red'  # Heavy traffic
                elif traffic > 1.1:
                    color = 'orange'  # Moderate traffic
                else:
                    color = 'green'  # Light traffic
                dash_array = None
                weight = 5
            elif 'condition' in edge:
                # Condition-weighted edge (for emergency routes)
                condition = edge['condition']
                if condition >= 8:
                    color = 'green'  # Excellent condition
                elif condition >= 6:
                    color = 'blue'  # Good condition
                else:
                    color = 'orange'  # Fair condition
                dash_array = None
                weight = 5
            else:
                # Default style
                color = 'blue'
                dash_array = None
                weight = 5
            
            # Create popup content
            popup_content = f"Road: {source_id} - {target_id}<br>Distance: {edge.get('distance', 0):.1f} km"
            
            if 'time' in edge:
                popup_content += f"<br>Travel Time: {edge['time']:.1f} min"
            if 'traffic_factor' in edge:
                popup_content += f"<br>Traffic Factor: {edge['traffic_factor']:.2f}"
            if 'condition' in edge:
                popup_content += f"<br>Road Condition: {edge['condition']}/10"
            if 'cost' in edge:
                popup_content += f"<br>Construction Cost: {edge['cost']} million EGP"
            
            # Draw the line
            folium.PolyLine(
                locations=[source_coords, target_coords],
                color=color,
                weight=weight,
                opacity=0.8,
                popup=popup_content,
                dash_array=dash_array
            ).add_to(m)
    
    # Highlight specific nodes if requested
    if highlight_nodes:
        for node_id in highlight_nodes:
            if node_id in node_coords:
                folium.CircleMarker(
                    location=node_coords[node_id],
                    radius=12,
                    color='red',
                    fill=True,
                    fill_color='red',
                    fill_opacity=0.7,
                    weight=3
                ).add_to(m)
    
    return m
