import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import networkx as nx
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import base64
import sys
import time
import random
import json

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))
from src.data.loader import load_data
from src.algorithms.mst import run_mst_algorithm
from src.algorithms.shortestpath import run_dijkstra, run_a_star
from src.algorithms.dp import run_transit_optimization
from src.algorithms.greedy import run_greedy_algorithm
from src.visualization.network import create_base_map, visualize_solution
from src.utils.export import export_to_csv, export_to_json, export_plot_to_png, export_map_to_html, export_report_to_html

# Page config
st.set_page_config(
    page_title="Cairo Transportation Network Optimization",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

def save_user_data():
    """Save user data to file"""
    try:
        # Use the current directory for user_data.json
        file_path = 'user_data.json'
        
        # Save the data with proper formatting
        with open(file_path, 'w') as f:
            json.dump(st.session_state.users, f, indent=4)
            
        return True
    except Exception as e:
        st.error(f"Error saving user data: {str(e)}")
        return False

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'users' not in st.session_state:
        # Initialize users with saved analyses from previous sessions
        try:
            # Use the current directory for user_data.json
            file_path = 'user_data.json'
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    st.session_state.users = json.load(f)
            else:
                # Sample users for demo purposes if no saved data exists
                st.session_state.users = {
                    "admin": {"password": "admin123", "saved_analyses": {}, "preferences": {}},
                    "planner": {"password": "cairo123", "saved_analyses": {}, "preferences": {}},
                    "guest": {"password": "guest", "saved_analyses": {}, "preferences": {}}
                }
                # Create the user_data.json file with initial data
                try:
                    with open(file_path, 'w') as f:
                        json.dump(st.session_state.users, f, indent=4)
                except Exception as e:
                    st.error(f"Error creating user data file: {str(e)}")
        except json.JSONDecodeError:
            # If the file is corrupted, reinitialize with demo users
            st.session_state.users = {
                "admin": {"password": "admin123", "saved_analyses": {}, "preferences": {}},
                "planner": {"password": "cairo123", "saved_analyses": {}, "preferences": {}},
                "guest": {"password": "guest", "saved_analyses": {}, "preferences": {}}
            }
            # Try to recreate the file
            try:
                with open(file_path, 'w') as f:
                    json.dump(st.session_state.users, f, indent=4)
            except Exception as e:
                st.error(f"Error recreating user data file: {str(e)}")
    if 'selected_algorithm' not in st.session_state:
        st.session_state.selected_algorithm = None
    if 'save_status' not in st.session_state:
        st.session_state.save_status = {'success': False, 'message': '', 'saved_name': None}
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

def login_page():
    """Display login form and handle authentication"""
    st.title("Smart City Transportation Network Optimization")
    
    st.markdown("""
    Welcome to the Greater Cairo Transportation Network Optimization System.
    Please log in to access the full features.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In")
            
            if submit:
                if username in st.session_state.users and st.session_state.users[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    # Load saved analyses from file
                    try:
                        with open('user_data.json', 'r') as f:
                            saved_data = json.load(f)
                            if username in saved_data and 'saved_analyses' in saved_data[username]:
                                st.session_state.users[username]['saved_analyses'] = saved_data[username]['saved_analyses']
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass
                    st.session_state.user_data = st.session_state.users[username]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("**Demo Accounts:**")
        st.markdown("- Username: admin, Password: admin123")
        st.markdown("- Username: planner, Password: cairo123")
        st.markdown("- Username: guest, Password: guest")
    
    with col2:
        st.image("generated-icon.png", width=150)

def save_analysis(analysis_name, algorithm, results):
    """Save current analysis to user data"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("You need to be logged in to save the analysis.")
        return False, None
    
    username = st.session_state.username
    
    # Add timestamp to analysis name to prevent overwriting
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if timestamp not in analysis_name:
        analysis_name = f"{analysis_name} ({timestamp})"
    
    # Ensure all necessary fields are included in the results
    if "Traffic Flow Optimization" in algorithm:
        # For Dijkstra's algorithm, ensure we have all required fields
        if 'route_details' in results:
            # Calculate metrics from route details
            total_distance = results.get('total_distance', 0)
            travel_time = sum(float(step['Time (min)'].replace('min', '').strip()) 
                            for step in results['route_details'] 
                            if 'Time (min)' in step)
            num_segments = len(results['route_details'])
            avg_speed = (total_distance / (travel_time / 60)) if travel_time > 0 else 0
            
            # Create path edges from route details
            path_edges = []
            for step in results['route_details']:
                # Extract node IDs from the step
                from_node = step['From'].split(' - ')[0]
                to_node = step['To'].split(' - ')[0]
                
                # Convert to integers if they are numeric
                try:
                    from_node = int(from_node)
                except ValueError:
                    pass
                try:
                    to_node = int(to_node)
                except ValueError:
                    pass
                
                # Create edge data
                edge_data = {
                    'from': from_node,
                    'to': to_node,
                    'distance': float(step['Distance (km)'].replace('km', '').strip()),
                    'time': float(step['Time (min)'].replace('min', '').strip()),
                    'traffic_factor': 1.3 if step['Traffic'] == 'Heavy' else 
                                    1.1 if step['Traffic'] == 'Moderate' else 1.0
                }
                path_edges.append(edge_data)
            
            # Update results with all necessary fields
            results.update({
                'travel_time': travel_time,
                'num_segments': num_segments,
                'avg_speed': avg_speed,
                'path_edges': path_edges  # Add path edges for visualization
            })
    elif "Emergency Response Planning" in algorithm:
        # For A* algorithm, convert route_details to path_edges if needed
        if 'route_details' in results and 'path_edges' not in results:
            # The route_details in emergency response already has the correct format
            results['path_edges'] = results['route_details']
        
        st.session_state.users[username]['saved_analyses'][analysis_name] = {
            "algorithm": algorithm,
        "timestamp": timestamp,
            "results": results
        }
        
        # Update session state
        st.session_state.user_data = st.session_state.users[username]
    
    # Save to file and check if successful
    if save_user_data():
        return True, analysis_name
    else:
        st.error("Failed to save analysis to file. Please try again.")
        return False, None
    return False, None

def save_analysis_callback():
    """Callback function for saving analysis"""
    if st.session_state.analysis_name and st.session_state.current_analysis:
        success, saved_name = save_analysis(
            st.session_state.analysis_name,
            st.session_state.current_analysis['algorithm'],
            st.session_state.current_analysis['results']
        )
        if success:
            st.session_state.save_status = {
                'success': True,
                'message': f"Analysis '{saved_name}' saved successfully!",
                'saved_name': saved_name
            }
            # Update user data
            if 'saved_analyses' not in st.session_state.users[st.session_state.username]:
                st.session_state.users[st.session_state.username]['saved_analyses'] = {}
            st.session_state.users[st.session_state.username]['saved_analyses'][saved_name] = st.session_state.current_analysis
            st.session_state.user_data = st.session_state.users[st.session_state.username]
            save_user_data()
        else:
            st.session_state.save_status = {
                'success': False,
                'message': "Failed to save analysis. Please make sure you're logged in.",
                'saved_name': None
            }

def display_save_analysis_section(algorithm, results, default_name=None):
    """Display a prominent save analysis section"""
    st.markdown("---")
    st.subheader("Save Analysis")
    
    # Store current analysis in session state
    st.session_state.current_analysis = {
        'algorithm': algorithm,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'results': results
    }
    
    # Create the save form
    with st.form(key="save_analysis_form", clear_on_submit=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(
                "Analysis Name",
                value=default_name or f"{algorithm} - {datetime.now().strftime('%Y-%m-%d')}",
                key="analysis_name"
            )
        with col2:
            st.form_submit_button(
                "💾 Save to Profile",
                use_container_width=True,
                on_click=save_analysis_callback
            )
    
    # Display save status
    if st.session_state.save_status['message']:
        if st.session_state.save_status['success']:
            st.success(st.session_state.save_status['message'])
        else:
            st.error(st.session_state.save_status['message'])

def create_data_description():
    st.markdown("""
    # Greater Cairo Transportation Network Optimization
    
    This application provides interactive tools for optimizing the transportation network of Greater Cairo. 
    You can analyze and visualize the following:
    
    - **Infrastructure Network Design** (Minimum Spanning Tree)
    - **Traffic Flow Optimization** (Dijkstra's algorithm)
    - **Emergency Response Planning** (A* Search)
    - **Public Transit Optimization** (Dynamic Programming)
    - **Traffic Signal Optimization** (Greedy algorithm)
    
    Select an algorithm from the sidebar to begin.
    """)
    
    with st.expander("Dataset Information"):
        st.markdown("""
        ### Dataset Details
        - 15 neighborhoods in Greater Cairo
        - 10 key facilities (airports, hospitals, etc.)
        - Existing road network with distances, capacities, and conditions
        - Potential new roads with construction costs
        - Time-dependent traffic flow data
        """)

def main():
    # Initialize session state
    init_session_state()
    
    # Initialize saved analyses in session state if not exists
    if 'saved_analyses' not in st.session_state:
        st.session_state.saved_analyses = {}
    
    # Display login page if not authenticated
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Load data
    data = load_data()
    neighborhoods = data['neighborhoods']
    facilities = data['facilities']
    existing_roads = data['existing_roads']
    potential_roads = data['potential_roads']
    traffic_flows = data['traffic_flows']
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add nodes
    for node in neighborhoods:
        G.add_node(node['id'], 
                  name=node['name'], 
                  population=node['population'], 
                  type=node['type'], 
                  x=node['x'], 
                  y=node['y'], 
                  node_type='neighborhood')
    
    for node in facilities:
        G.add_node(node['id'], 
                  name=node['name'], 
                  type=node['type'], 
                  x=node['x'], 
                  y=node['y'], 
                  node_type='facility')
    
    # Add existing road edges
    for road in existing_roads:
        G.add_edge(road['from'], road['to'], 
                  distance=road['distance'], 
                  capacity=road['capacity'], 
                  condition=road['condition'], 
                  road_type='existing')
    
    # Keep track of state
    if 'selected_algorithm' not in st.session_state:
        st.session_state.selected_algorithm = None
    
    # Sidebar
    st.sidebar.header("Cairo Transportation Network Optimization")
    
    # User info in sidebar
    st.sidebar.write(f"**Logged in as:** {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.saved_analyses = {}  # Clear saved analyses on logout
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Algorithm selection
    algorithm = st.sidebar.selectbox(
        "Select Algorithm",
        [
            "Overview",
            "Infrastructure Network Design (MST)",
            "Traffic Flow Optimization (Dijkstra)",
            "Emergency Response Planning (A*)",
            "Public Transit Optimization (DP)",
            "Traffic Signal Optimization (Greedy)"
        ]
    )
    
    st.session_state.selected_algorithm = algorithm
    
    # User's saved analyses
    st.sidebar.markdown("---")
    st.sidebar.subheader("Saved Analyses")
    
    # Combine session state saved analyses with user data saved analyses
    all_saved_analyses = {}
    if st.session_state.user_data and 'saved_analyses' in st.session_state.user_data:
        all_saved_analyses.update(st.session_state.user_data['saved_analyses'])
    all_saved_analyses.update(st.session_state.saved_analyses)
    
    if all_saved_analyses:
        analysis_names = list(all_saved_analyses.keys())
        selected_analysis = st.sidebar.selectbox("Select Analysis", analysis_names)
        
        if st.sidebar.button("Load Analysis"):
            analysis_data = all_saved_analyses[selected_analysis]
            st.sidebar.write(f"Loaded: {selected_analysis}")
            st.sidebar.write(f"Created: {analysis_data['timestamp']}")
            st.sidebar.write(f"Algorithm: {analysis_data['algorithm']}")
    else:
        st.sidebar.write("No saved analyses yet.")
    
    # Display sections based on selected algorithm
    if algorithm == "Overview":
        create_data_description()
        
        # Create base map with neighborhoods and facilities
        m = create_base_map(neighborhoods, facilities, existing_roads)
        st.subheader("Greater Cairo Transportation Network")
        folium_static(m, width=1000, height=600)
        
        # Show basic network statistics
        st.subheader("Network Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Neighborhoods", len(neighborhoods))
            st.metric("Total Population", sum(n['population'] for n in neighborhoods))
        
        with col2:
            st.metric("Facilities", len(facilities))
            st.metric("Existing Roads", len(existing_roads))
        
        with col3:
            st.metric("Potential New Roads", len(potential_roads))
            st.metric("Total Road Distance", f"{sum(r['distance'] for r in existing_roads):.1f} km")
    
    elif algorithm == "Infrastructure Network Design (MST)":
        st.title("Infrastructure Network Design")
        st.write("This tool helps identify the optimal road network that connects all neighborhoods and key facilities while minimizing total cost.")
        
        # Parameters
        with st.expander("Algorithm Parameters"):
            include_potential = st.checkbox("Include Potential New Roads", value=True)
            prioritize_hospitals = st.checkbox("Prioritize Hospital Connections", value=True)
            prioritize_high_population = st.checkbox("Prioritize High-Population Areas", value=True)
        
        # Run MST algorithm
        if st.button("Calculate Optimal Road Network"):
            with st.spinner("Running MST algorithm..."):
                mst_graph, total_cost, results = run_mst_algorithm(
                    G, 
                    neighborhoods, 
                    facilities, 
                    existing_roads, 
                    potential_roads if include_potential else [],
                    prioritize_hospitals,
                    prioritize_high_population
                )
                
                # Visualize the MST on the map
                mst_map = visualize_solution(neighborhoods, facilities, results["selected_roads"], 
                                             title="Minimum Spanning Tree Solution")
                st.subheader("Optimal Road Network")
                folium_static(mst_map, width=1000, height=600)
                
                # Show results
                st.subheader("Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Cost (million EGP)", f"{total_cost:.1f}")
                    st.metric("Number of Roads", len(results["selected_roads"]))
                    st.metric("New Roads Added", results["new_roads_count"])
                
                with col2:
                    st.metric("Existing Roads Used", results["existing_roads_count"])
                    st.metric("All Nodes Connected", "Yes" if results["all_connected"] else "No")
                    st.metric("Critical Facilities Connected", 
                              f"{results['critical_facilities_connected']}/{results['total_critical_facilities']}")
                
                # Display roads in the MST
                st.subheader("Roads in the Optimal Network")
                roads_df = pd.DataFrame(results["selected_roads"])
                st.dataframe(roads_df)
                
                # Export section
                st.subheader("Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Export Data")
                    st.markdown(export_to_csv(roads_df, "mst_roads.csv"), unsafe_allow_html=True)
                    st.markdown(export_to_json(results, "mst_results.json"), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### Export Map & Report")
                    st.markdown(export_map_to_html(mst_map, "mst_map.html"), unsafe_allow_html=True)
                    st.markdown(export_report_to_html("Infrastructure Network Design", results, "mst_report.html"), unsafe_allow_html=True)
                
                # Save analysis
                display_save_analysis_section(
                    "Infrastructure Network Design (MST)",
                    results,
                    f"MST Analysis - {datetime.now().strftime('%Y-%m-%d')}"
                )
    
    elif algorithm == "Traffic Flow Optimization (Dijkstra)":
        st.title("Traffic Flow Optimization")
        st.write("Find the fastest route between two points considering time-dependent traffic conditions.")
        
        # Time selection
        time_options = ["Morning Peak (7-9 AM)", "Afternoon (12-2 PM)", 
                         "Evening Peak (5-7 PM)", "Night (10 PM-5 AM)"]
        selected_time = st.selectbox("Select Time of Day", time_options)
        
        time_mapping = {
            "Morning Peak (7-9 AM)": "morning_peak",
            "Afternoon (12-2 PM)": "afternoon",
            "Evening Peak (5-7 PM)": "evening_peak",
            "Night (10 PM-5 AM)": "night"
        }
        
        time_period = time_mapping[selected_time]
        
        # Origin and destination selection
        col1, col2 = st.columns(2)
        
        with col1:
            origins = [f"{n['id']} - {n['name']}" for n in neighborhoods] + [f"{f['id']} - {f['name']}" for f in facilities]
            origin = st.selectbox("Select Origin", origins)
            origin_id = origin.split(" - ")[0]
            # Convert to integer if it's a neighborhood ID
            if origin_id.isdigit():
                origin_id = int(origin_id)
        
        with col2:
            destinations = [f"{n['id']} - {n['name']}" for n in neighborhoods] + [f"{f['id']} - {f['name']}" for f in facilities]
            destination = st.selectbox("Select Destination", destinations) 
            destination_id = destination.split(" - ")[0]
            # Convert to integer if it's a neighborhood ID
            if destination_id.isdigit():
                destination_id = int(destination_id)
        
        # Run algorithm
        if st.button("Find Optimal Route"):
            if origin_id == destination_id:
                st.error("Origin and destination must be different")
            else:
                with st.spinner("Calculating optimal route..."):
                    try:
                        # Run Dijkstra with time-dependent weights
                        path, travel_time, path_edges, results = run_dijkstra(
                            G, 
                            origin_id, 
                            destination_id, 
                            time_period,
                            traffic_flows
                        )
                        
                        if path:
                            # Visualize the path on the map
                            route_map = visualize_solution(neighborhoods, facilities, path_edges,
                                                          highlight_nodes=[origin_id, destination_id],
                                                          title=f"Optimal Route: {origin.split(' - ')[1]} to {destination.split(' - ')[1]}")
                            st.subheader("Optimal Route")
                            folium_static(route_map, width=1000, height=600)
                            
                            # Show results
                            st.subheader("Results")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.metric("Travel Time", f"{travel_time:.1f} minutes")
                                st.metric("Route Distance", f"{results['total_distance']:.1f} km")
                            
                            with col2:
                                st.metric("Road Segments", len(path_edges))
                                st.metric("Traffic Congestion", f"{results['congestion_level']}/10")
                            
                            # Compare with other time periods
                            st.subheader("Time Comparison")
                            comparison_data = results["time_comparison"]
                            
                            fig = px.bar(
                                x=list(time_mapping.keys()),
                                y=[comparison_data[tp] for tp in time_mapping.values()],
                                labels={"x": "Time of Day", "y": "Travel Time (minutes)"}
                            )
                            fig.update_layout(title="Travel Time Comparison by Time of Day")
                            st.plotly_chart(fig)
                            
                            # Show detailed route
                            st.subheader("Route Details")
                            route_details = results["route_details"]
                            st.table(route_details)
                            
                            # Export section
                            st.subheader("Export Results")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### Export Data")
                                route_df = pd.DataFrame(route_details)
                                st.markdown(export_to_csv(route_df, "route_details.csv"), unsafe_allow_html=True)
                                st.markdown(export_to_json(results, "route_results.json"), unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("### Export Map & Report")
                                st.markdown(export_map_to_html(route_map, "route_map.html"), unsafe_allow_html=True)
                                st.markdown(export_plot_to_png(fig, "time_comparison.png"), unsafe_allow_html=True)
                                st.markdown(export_report_to_html("Traffic Flow Optimization", results, "route_report.html"), unsafe_allow_html=True)
                            
                            # Save analysis
                            display_save_analysis_section(
                                "Traffic Flow Optimization (Dijkstra)",
                                results,
                                f"Route {origin.split(' - ')[1]} to {destination.split(' - ')[1]} - {datetime.now().strftime('%Y-%m-%d')}"
                            )
                        else:
                            st.error("No path found between selected points")
                    except Exception as e:
                        st.error(f"Error calculating route: {str(e)}")
    
    elif algorithm == "Emergency Response Planning (A*)":
        st.title("Emergency Response Planning")
        st.write("Find the fastest emergency route to the nearest hospital using A* algorithm.")
        
        # Emergency location selection
        emergency_locations = [f"{n['id']} - {n['name']}" for n in neighborhoods]
        emergency_location = st.selectbox("Select Emergency Location", emergency_locations)
        emergency_id = int(emergency_location.split(" - ")[0])
        
        # Hospital preference
        hospital_options = [f['id'] for f in facilities if f['type'] == 'Medical']
        specific_hospital = st.radio(
            "Hospital Selection",
            ["Nearest Hospital", "Specific Hospital"]
        )
        
        target_hospital = None
        if specific_hospital == "Specific Hospital":
            hospital_names = [f"{f['id']} - {f['name']}" for f in facilities if f['type'] == 'Medical']
            selected_hospital = st.selectbox("Select Hospital", hospital_names)
            target_hospital = selected_hospital.split(" - ")[0]
        
        # Run algorithm
        if st.button("Find Emergency Route"):
            try:
                with st.spinner("Calculating emergency route..."):
                    # Run A* algorithm - no minimum road condition
                    path, travel_time, path_edges, results = run_a_star(
                        G, 
                        emergency_id, 
                        target_hospital,
                        neighborhoods,
                        facilities,
                        1  # Use lowest possible condition to always find a path
                    )
                
                if path:
                    # Visualize the path on the map
                    hospital_id = results["hospital_id"]
                    hospital_name = next(f['name'] for f in facilities if f['id'] == hospital_id)
                    
                    route_map = visualize_solution(neighborhoods, facilities, path_edges,
                                                highlight_nodes=[emergency_id, hospital_id],
                                                title=f"Emergency Route to {hospital_name}")
                    st.subheader("Emergency Route")
                    folium_static(route_map, width=1000, height=600)
                    
                    # Show results
                    st.subheader("Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Estimated Travel Time", f"{travel_time:.1f} minutes")
                        st.metric("Route Distance", f"{results['total_distance']:.1f} km")
                    
                    with col2:
                        st.metric("Destination Hospital", hospital_name)
                        st.metric("Average Road Condition", f"{results['avg_road_condition']:.1f}/10")
                    
                    # Compare with standard routing
                    st.subheader("Comparison with Standard Routing")
                    comparison = pd.DataFrame([
                        {"Routing Method": "Emergency (A*)", "Travel Time (min)": travel_time},
                        {"Routing Method": "Standard (Dijkstra)", "Travel Time (min)": results["standard_time"]}
                    ])
                    
                    fig = px.bar(
                        comparison,
                        x="Routing Method",
                        y="Travel Time (min)",
                        color="Routing Method",
                        title="Emergency vs. Standard Routing Comparison"
                    )
                    st.plotly_chart(fig)
                    
                    # Show detailed route
                    st.subheader("Route Details")
                    route_details = results["route_details"]
                    st.table(route_details)
                    
                    # Export section
                    st.subheader("Export Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Export Data")
                        route_df = pd.DataFrame(route_details)
                        st.markdown(export_to_csv(route_df, "emergency_route_details.csv"), unsafe_allow_html=True)
                        st.markdown(export_to_json(results, "emergency_results.json"), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("### Export Map & Report")
                        st.markdown(export_map_to_html(route_map, "emergency_route_map.html"), unsafe_allow_html=True)
                        st.markdown(export_plot_to_png(fig, "emergency_comparison.png"), unsafe_allow_html=True)
                        st.markdown(export_report_to_html("Emergency Response Planning", results, "emergency_report.html"), unsafe_allow_html=True)
                    
                    # Save analysis
                    display_save_analysis_section(
                        "Emergency Response Planning (A*)",
                        results,
                        f"Emergency Route from {emergency_location.split(' - ')[1]} - {datetime.now().strftime('%Y-%m-%d')}"
                    )
                else:
                    st.error("No suitable emergency route found. Please try a different location or hospital.")
            except Exception as e:
                st.error(f"Error calculating emergency route: {str(e)}")
    
    elif algorithm == "Public Transit Optimization (DP)":
        st.title("Public Transit Optimization")
        st.write("Optimize bus allocation and schedules based on passenger demand.")
        
        # Parameters
        with st.expander("Transit Parameters"):
            total_buses = st.slider("Total Available Buses", 20, 100, 50)
            max_waiting_time = st.slider("Maximum Acceptable Waiting Time (min)", 5, 30, 15)
            optimize_transfers = st.checkbox("Optimize Metro-Bus Transfers", value=True)
        
        # Run algorithm
        if st.button("Optimize Transit Network"):
            with st.spinner("Running optimization algorithm..."):
                # Run DP algorithm
                optimized_schedule, results = run_transit_optimization(
                    total_buses,
                    max_waiting_time,
                    optimize_transfers
                )
                
                # Display results
                st.subheader("Optimized Bus Allocation")
                
                # Create transit network visualization on map
                transit_map = folium.Map(location=[30.05, 31.25], zoom_start=11)
                
                # Add neighborhoods and facilities
                for n in neighborhoods:
                    popup_text = f"<b>{n['name']}</b><br>Population: {n['population']:,}"
                    folium.CircleMarker(
                        location=[n['y'], n['x']],
                        radius=8,
                        color='blue',
                        fill=True,
                        fill_color='blue',
                        fill_opacity=0.7,
                        popup=popup_text
                    ).add_to(transit_map)
                
                # Add bus routes with line thickness based on buses allocated
                for route_data in results["bus_allocation"]:
                    route_id = route_data["route"]
                    buses = route_data["buses_allocated"]
                    line_width = max(2, min(8, buses / 2))  # Scale line width based on buses allocated
                    
                    # Get route coordinates from the route details in results
                    route_coords = []
                    route_stops = route_data.get("stops", [])  # Get stops from route data
                    
                    for stop_name in route_stops:
                        # Search in neighborhoods
                        stop = next((n for n in neighborhoods if n["name"] == stop_name), None)
                        if stop:
                            route_coords.append([stop["y"], stop["x"]])
                    else:
                            # Search in facilities
                            stop = next((f for f in facilities if f["name"] == stop_name), None)
                            if stop:
                                route_coords.append([stop["y"], stop["x"]])
                    
                    if len(route_coords) >= 2:  # Only draw if we have at least 2 points
                        folium.PolyLine(
                            locations=route_coords,
                            color='red',
                            weight=line_width,
                            opacity=0.8,
                            popup=f"Route: {route_data['route_name']}<br>Buses: {buses}<br>Daily Passengers: {route_data['daily_passengers']:,}"
                        ).add_to(transit_map)
                
                # Add transfer points if optimized
                if optimize_transfers:
                    for transfer in results["transfer_points"]:
                        # Find the station location
                        station_name = transfer["station"]
                        station = next((f for f in facilities if f["name"] == station_name and f["type"] == "Transit Hub"), None)
                        
                        if station:
                            folium.Marker(
                                location=[station["y"], station["x"]],
                                popup=f"Transfer Point: {transfer['station']}<br>Metro Lines: {transfer['metro_lines']}<br>Bus Routes: {transfer['bus_routes']}<br>Avg Waiting Time: {transfer['avg_waiting_after']:.1f} min",
                                icon=folium.Icon(color='purple', icon='exchange', prefix='fa')
                            ).add_to(transit_map)
                
                # Display the map
                st.subheader("Transit Network Map")
                folium_static(transit_map, width=1000, height=600)
                
                # Bus allocation chart
                st.subheader("Bus Allocation by Route")
                fig = px.bar(
                    results["bus_allocation"],
                    x="route",
                    y="buses_allocated",
                    color="daily_passengers",
                    labels={"buses_allocated": "Buses Allocated", "route": "Bus Route", "daily_passengers": "Daily Passengers"},
                    title="Bus Allocation by Route"
                )
                st.plotly_chart(fig)
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Buses Allocated", results["total_buses_allocated"])
                    st.metric("Routes Serviced", results["routes_serviced"])
                
                with col2:
                    st.metric("Avg Waiting Time (Peak)", f"{results['avg_peak_waiting_time']:.1f} min")
                    st.metric("Avg Waiting Time (Off-peak)", f"{results['avg_offpeak_waiting_time']:.1f} min")
                
                with col3:
                    st.metric("Daily Passengers Served", f"{results['total_daily_passengers']:,}")
                    st.metric("Transfer Improvement", f"{results['transfer_improvement']:.1f}%")
                
                # Waiting time by route
                st.subheader("Waiting Times by Route")
                fig = px.bar(
                    results["waiting_times"],
                    x="route",
                    y=["peak_waiting_time", "offpeak_waiting_time"],
                    barmode="group",
                    labels={
                        "value": "Waiting Time (min)",
                        "route": "Bus Route",
                        "variable": "Time Period"
                    },
                    title="Waiting Times by Route and Time Period"
                )
                st.plotly_chart(fig)
                
                # Transfer points optimization
                if optimize_transfers:
                    st.subheader("Metro-Bus Transfer Points")
                    st.table(results["transfer_points"])
                
                # Export section
                st.subheader("Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Export Data")
                    bus_allocation_df = pd.DataFrame(results["bus_allocation"])
                    waiting_times_df = pd.DataFrame(results["waiting_times"])
                    st.markdown(export_to_csv(bus_allocation_df, "bus_allocation.csv"), unsafe_allow_html=True)
                    st.markdown(export_to_csv(waiting_times_df, "waiting_times.csv"), unsafe_allow_html=True)
                    st.markdown(export_to_json(results, "transit_results.json"), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### Export Map & Visualizations")
                    st.markdown(export_map_to_html(transit_map, "transit_network_map.html"), unsafe_allow_html=True)
                    st.markdown(export_plot_to_png(fig, "waiting_times_chart.png"), unsafe_allow_html=True)
                    st.markdown(export_report_to_html("Public Transit Optimization", results, "transit_report.html"), unsafe_allow_html=True)
                
                # Save analysis
                display_save_analysis_section(
                    "Public Transit Optimization (DP)",
                    results,
                    f"Transit Optimization ({total_buses} buses) - {datetime.now().strftime('%Y-%m-%d')}"
                )
    
    elif algorithm == "Traffic Signal Optimization (Greedy)":
        st.title("Traffic Signal Optimization")
        st.write("Optimize traffic signal timings at intersections using a greedy algorithm.")
        
        # Parameters
        with st.expander("Algorithm Parameters"):
            time_period = st.selectbox(
                "Optimize for Time Period",
                ["Morning Peak (7-9 AM)", "Afternoon (12-2 PM)", "Evening Peak (5-7 PM)", "All Day"]
            )
            
            priority_options = [
                "Minimize Average Delay",
                "Prioritize High-Traffic Roads",
                "Balance Wait Times"
            ]
            optimization_priority = st.selectbox("Optimization Priority", priority_options)
            
            max_cycle_length = st.slider("Maximum Cycle Length (seconds)", 60, 180, 120)
        
        # Intersections with multiple roads
        intersections = [
            {"id": 1, "name": "Downtown Cairo Junction", "roads": ["1-3", "3-5", "3-6", "3-9"]},
            {"id": 2, "name": "Nasr City Hub", "roads": ["2-3", "2-5", "4-2"]},
            {"id": 3, "name": "Giza Square", "roads": ["1-8", "7-8", "8-10", "8-12"]},
            {"id": 4, "name": "Mohandessin Intersection", "roads": ["3-9", "6-9", "9-10"]},
            {"id": 5, "name": "Dokki Junction", "roads": ["3-10", "8-10", "9-10", "10-11"]}
        ]
        
        selected_intersection = st.selectbox(
            "Select Intersection to Optimize",
            [f"{i['id']} - {i['name']}" for i in intersections]
        )
        intersection_id = int(selected_intersection.split(" - ")[0])
        selected_intersection_data = next(i for i in intersections if i['id'] == intersection_id)
        
        # Run algorithm
        if st.button("Optimize Traffic Signals"):
            with st.spinner("Running greedy algorithm..."):
                # Run greedy algorithm
                time_mapping = {
                    "Morning Peak (7-9 AM)": "morning_peak",
                    "Afternoon (12-2 PM)": "afternoon",
                    "Evening Peak (5-7 PM)": "evening_peak",
                    "All Day": "all_day"
                }
                
                signal_plan, results = run_greedy_algorithm(
                    traffic_flows,
                    selected_intersection_data,
                    time_mapping[time_period],
                    optimization_priority,
                    max_cycle_length
                )
                
                # Display results
                st.subheader(f"Optimized Signal Timing for {selected_intersection_data['name']}")
                
                # Signal timing visualization
                fig = go.Figure()
                
                # Add signal phases as horizontal bars
                y_pos = 0
                for road, timing in signal_plan.items():
                    fig.add_trace(go.Bar(
                        x=[timing["green_time"]],
                        y=[road],
                        orientation='h',
                        name=f"{road} - Green",
                        marker_color='green',
                        text=f"{timing['green_time']}s",
                        textposition='inside'
                    ))
                    
                    # Add red time after green
                    fig.add_trace(go.Bar(
                        x=[timing["red_time"]],
                        y=[road],
                        orientation='h',
                        name=f"{road} - Red",
                        marker_color='red',
                        text=f"{timing['red_time']}s",
                        textposition='inside',
                        base=timing["green_time"]
                    ))
                    
                    y_pos += 1
                
                fig.update_layout(
                    title="Traffic Signal Timing Plan",
                    xaxis_title="Time (seconds)",
                    yaxis_title="Road",
                    barmode='stack',
                    height=400,
                    width=800
                )
                
                st.plotly_chart(fig)
                
                # Results metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Cycle Length", f"{results['total_cycle_length']} seconds")
                    st.metric("Number of Phases", results['num_phases'])
                
                with col2:
                    st.metric("Average Green Time", f"{results['avg_green_time']:.1f} seconds")
                    st.metric("Total Traffic Flow", f"{results['total_flow']} vehicles")
                
                with col3:
                    st.metric("Average Wait Time", f"{results['avg_wait_time']:.1f} seconds")
                    st.metric("Improvement vs. Fixed Timing", f"{results['improvement_pct']:.1f}%")
                
                # Traffic flow by direction
                st.subheader("Traffic Flow by Direction")
                traffic_data = results["traffic_data"]
                
                flow_fig = px.bar(
                    traffic_data,
                    x="road",
                    y="flow",
                    color="direction",
                    labels={"road": "Road", "flow": "Traffic Flow (vehicles per hour)"},
                    title="Directional Traffic Flow"
                )
                st.plotly_chart(flow_fig)
                
                # Export section
                st.subheader("Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Export Data")
                    # Convert signal plan to dataframe
                    signal_df = pd.DataFrame([
                        {"road": road, "green_time": data["green_time"], "red_time": data["red_time"]}
                        for road, data in signal_plan.items()
                    ])
                    traffic_df = pd.DataFrame(traffic_data)
                    st.markdown(export_to_csv(signal_df, "signal_timing.csv"), unsafe_allow_html=True)
                    st.markdown(export_to_csv(traffic_df, "traffic_flow.csv"), unsafe_allow_html=True)
                    st.markdown(export_to_json(results, "signal_results.json"), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### Export Visualizations")
                    st.markdown(export_plot_to_png(fig, "signal_timing_chart.png"), unsafe_allow_html=True)
                    st.markdown(export_plot_to_png(flow_fig, "traffic_flow_chart.png"), unsafe_allow_html=True)
                    st.markdown(export_report_to_html("Traffic Signal Optimization", results, "signal_report.html"), unsafe_allow_html=True)
                
                # Save analysis
                display_save_analysis_section(
                    "Traffic Signal Optimization (Greedy)",
                    results,
                    f"Signal Timing for {selected_intersection_data['name']} - {datetime.now().strftime('%Y-%m-%d')}"
                )

if __name__ == "__main__":
    main()
