import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

def generate_terrain_model(neighborhoods, facilities, roads, dem_points=None):
    """
    Generate a terrain model with transportation infrastructure.
    
    Args:
        neighborhoods: List of neighborhood data points
        facilities: List of facility data points
        roads: List of road segments
        dem_points: Optional digital elevation model points (x, y, z)
        
    Returns:
        Plotly figure object with 3D terrain
    """
    # If no DEM provided, create a synthetic terrain
    if dem_points is None:
        # Find bounds of the data
        x_coords = [n['x'] for n in neighborhoods] + [f['x'] for f in facilities]
        y_coords = [n['y'] for n in neighborhoods] + [f['y'] for f in facilities]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Add some padding
        x_min -= 0.05
        x_max += 0.05
        y_min -= 0.05
        y_max += 0.05
        
        # Create a grid for the terrain
        grid_size = 100
        x_grid = np.linspace(x_min, x_max, grid_size)
        y_grid = np.linspace(y_min, y_max, grid_size)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        # Create synthetic terrain with random hills
        num_hills = 8
        zz = np.zeros_like(xx)
        
        for _ in range(num_hills):
            # Random hill center
            cx = np.random.uniform(x_min, x_max)
            cy = np.random.uniform(y_min, y_max)
            
            # Random hill properties
            radius = np.random.uniform(0.05, 0.2)
            height = np.random.uniform(10, 50)
            
            # Add hill to terrain
            dist = np.sqrt((xx - cx)**2 + (yy - cy)**2)
            zz += height * np.exp(-dist**2 / (2 * radius**2))
    else:
        # Use provided DEM points
        x_dem = [p[0] for p in dem_points]
        y_dem = [p[1] for p in dem_points]
        z_dem = [p[2] for p in dem_points]
        
        # Find bounds of the data
        x_coords = [n['x'] for n in neighborhoods] + [f['x'] for f in facilities]
        y_coords = [n['y'] for n in neighborhoods] + [f['y'] for f in facilities]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        # Create a grid for the terrain
        grid_size = 100
        x_grid = np.linspace(x_min, x_max, grid_size)
        y_grid = np.linspace(y_min, y_max, grid_size)
        xx, yy = np.meshgrid(x_grid, y_grid)
        
        # Interpolate elevation values
        points = np.column_stack((x_dem, y_dem))
        zz = griddata(points, z_dem, (xx, yy), method='linear')
        
        # Fill NaN values (if any)
        if np.isnan(zz).any():
            zz = np.nan_to_num(zz, nan=np.nanmean(zz))
    
    # Create 3D surface plot for terrain
    fig = go.Figure()
    
    # Add terrain surface
    fig.add_trace(go.Surface(
        z=zz,
        x=xx,
        y=yy,
        colorscale='Viridis',
        opacity=0.8,
        showscale=False,
        name='Terrain'
    ))
    
    # Add neighborhoods as markers
    neighborhood_x = [n['x'] for n in neighborhoods]
    neighborhood_y = [n['y'] for n in neighborhoods]
    neighborhood_z = []
    
    for i in range(len(neighborhoods)):
        # Find elevation at this point
        x_idx = np.abs(x_grid - neighborhood_x[i]).argmin()
        y_idx = np.abs(y_grid - neighborhood_y[i]).argmin()
        z = zz[y_idx, x_idx] + 5  # Add offset to ensure visibility
        neighborhood_z.append(z)
    
    neighborhood_text = [f"{n['name']}<br>Population: {n['population']:,}" for n in neighborhoods]
    
    fig.add_trace(go.Scatter3d(
        x=neighborhood_x,
        y=neighborhood_y,
        z=neighborhood_z,
        mode='markers',
        marker=dict(
            size=10,
            color='blue',
            symbol='circle'
        ),
        text=neighborhood_text,
        hoverinfo='text',
        name='Neighborhoods'
    ))
    
    # Add facilities as markers with different colors
    facility_x = [f['x'] for f in facilities]
    facility_y = [f['y'] for f in facilities]
    facility_z = []
    facility_colors = []
    
    for i in range(len(facilities)):
        # Find elevation at this point
        x_idx = np.abs(x_grid - facility_x[i]).argmin()
        y_idx = np.abs(y_grid - facility_y[i]).argmin()
        z = zz[y_idx, x_idx] + 5  # Add offset to ensure visibility
        facility_z.append(z)
        
        # Color based on facility type
        if facilities[i]['type'] == 'Medical':
            facility_colors.append('red')
        elif facilities[i]['type'] == 'Educational':
            facility_colors.append('green')
        elif facilities[i]['type'] == 'Transportation':
            facility_colors.append('orange')
        else:
            facility_colors.append('purple')
    
    facility_text = [f"{f['name']}<br>Type: {f['type']}" for f in facilities]
    
    fig.add_trace(go.Scatter3d(
        x=facility_x,
        y=facility_y,
        z=facility_z,
        mode='markers',
        marker=dict(
            size=8,
            color=facility_colors,
            symbol='diamond'
        ),
        text=facility_text,
        hoverinfo='text',
        name='Facilities'
    ))
    
    # Add roads as 3D lines
    for road in roads:
        # Get start and end nodes
        from_id = road['from']
        to_id = road['to']
        
        # Find coordinates for the nodes
        from_x, from_y, from_z = None, None, None
        to_x, to_y, to_z = None, None, None
        
        # Check if from_id is a neighborhood
        for n in neighborhoods:
            if n['id'] == from_id:
                from_x, from_y = n['x'], n['y']
                x_idx = np.abs(x_grid - from_x).argmin()
                y_idx = np.abs(y_grid - from_y).argmin()
                from_z = zz[y_idx, x_idx] + 2  # Add small offset
                break
        
        # Check if from_id is a facility
        if from_x is None:
            for f in facilities:
                if f['id'] == from_id:
                    from_x, from_y = f['x'], f['y']
                    x_idx = np.abs(x_grid - from_x).argmin()
                    y_idx = np.abs(y_grid - from_y).argmin()
                    from_z = zz[y_idx, x_idx] + 2  # Add small offset
                    break
        
        # Check if to_id is a neighborhood
        for n in neighborhoods:
            if n['id'] == to_id:
                to_x, to_y = n['x'], n['y']
                x_idx = np.abs(x_grid - to_x).argmin()
                y_idx = np.abs(y_grid - to_y).argmin()
                to_z = zz[y_idx, x_idx] + 2  # Add small offset
                break
        
        # Check if to_id is a facility
        if to_x is None:
            for f in facilities:
                if f['id'] == to_id:
                    to_x, to_y = f['x'], f['y']
                    x_idx = np.abs(x_grid - to_x).argmin()
                    y_idx = np.abs(y_grid - to_y).argmin()
                    to_z = zz[y_idx, x_idx] + 2  # Add small offset
                    break
        
        # If we found both endpoints, add the road
        if from_x is not None and to_x is not None:
            # Determine road color based on condition (if available)
            road_color = 'grey'
            if 'condition' in road:
                condition = road['condition']
                if condition >= 8:
                    road_color = 'green'
                elif condition >= 5:
                    road_color = 'orange'
                else:
                    road_color = 'red'
            
            # Add intermediate points to follow terrain
            num_points = 20
            x_points = np.linspace(from_x, to_x, num_points)
            y_points = np.linspace(from_y, to_y, num_points)
            z_points = []
            
            for i in range(num_points):
                x_idx = np.abs(x_grid - x_points[i]).argmin()
                y_idx = np.abs(y_grid - y_points[i]).argmin()
                z = zz[y_idx, x_idx] + 2  # Add small offset
                z_points.append(z)
            
            fig.add_trace(go.Scatter3d(
                x=x_points,
                y=y_points,
                z=z_points,
                mode='lines',
                line=dict(
                    color=road_color,
                    width=4 if 'road_type' in road and road['road_type'] == 'existing' else 2
                ),
                name=f"Road {from_id}-{to_id}"
            ))
    
    # Set layout
    fig.update_layout(
        title='3D Terrain Model of Cairo Transportation Network',
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Elevation (m)',
            aspectratio=dict(x=1, y=1, z=0.5)
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        height=700,
        legend=dict(
            x=0,
            y=1,
            bgcolor='rgba(255, 255, 255, 0.5)'
        )
    )
    
    return fig

def display_3d_visualization(neighborhoods, facilities, roads, path_edges=None, highlight_nodes=None):
    """
    Display 3D visualization in Streamlit
    
    Args:
        neighborhoods: List of neighborhood data
        facilities: List of facility data
        roads: List of road segments
        path_edges: Optional list of edges to highlight
        highlight_nodes: Optional list of nodes to highlight
    """
    st.subheader("3D Terrain Visualization")
    
    # Visualization options
    col1, col2 = st.columns(2)
    
    with col1:
        show_terrain = st.checkbox("Show Terrain", value=True)
        show_roads = st.checkbox("Show Roads", value=True)
    
    with col2:
        terrain_style = st.selectbox("Terrain Style", ["Standard", "Exaggerated", "Flat"])
        if path_edges:
            highlight_path = st.checkbox("Highlight Selected Path", value=True)
        else:
            highlight_path = False
    
    # Generate 3D terrain model
    fig = generate_terrain_model(neighborhoods, facilities, roads if show_roads else [])
    
    # Apply terrain style
    if terrain_style == "Exaggerated":
        fig.update_layout(scene=dict(aspectratio=dict(x=1, y=1, z=1.5)))
    elif terrain_style == "Flat":
        fig.update_layout(scene=dict(aspectratio=dict(x=1, y=1, z=0.2)))
    
    # Add highlighted path if requested
    if highlight_path and path_edges:
        # Add highlighted path as a separate line with a distinctive color
        for edge in path_edges:
            from_id = edge['from']
            to_id = edge['to']
            
            # Find coordinates for the nodes
            from_node = next((n for n in neighborhoods if n['id'] == from_id), None)
            if from_node is None:
                from_node = next((f for f in facilities if f['id'] == from_id), None)
                
            to_node = next((n for n in neighborhoods if n['id'] == to_id), None)
            if to_node is None:
                to_node = next((f for f in facilities if f['id'] == to_id), None)
                
            if from_node and to_node:
                fig.add_trace(go.Scatter3d(
                    x=[from_node['x'], to_node['x']],
                    y=[from_node['y'], to_node['y']],
                    z=[10, 10],  # Fixed height for visibility
                    mode='lines',
                    line=dict(
                        color='yellow',
                        width=8
                    ),
                    name='Highlighted Path'
                ))
    
    # Display the 3D model
    st.plotly_chart(fig, use_container_width=True)
    
    # Camera controls help
    with st.expander("3D Navigation Help"):
        st.write("""
        ### How to Navigate the 3D Model
        
        - **Rotate**: Click and drag to rotate the view
        - **Pan**: Shift + click and drag to pan the view
        - **Zoom**: Use the scroll wheel or pinch on touchpad
        - **Reset View**: Double-click to reset the view
        
        You can also use the camera controls in the top-right corner of the visualization.
        """)
    
    return fig