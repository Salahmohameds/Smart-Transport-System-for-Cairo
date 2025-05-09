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

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))
from src.data.loader import load_data
from src.algorithms.mst import run_mst_algorithm
from src.algorithms.shortestpath import run_dijkstra, run_a_star
from src.algorithms.dp import run_transit_optimization
from src.algorithms.greedy import run_greedy_algorithm
from src.visualization.network import create_base_map, visualize_solution

# Page config
st.set_page_config(
    page_title="Cairo Transportation Network Optimization",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        
        # Run algorithm
        if st.button("Find Optimal Route"):
            if origin_id == destination_id:
                st.error("Origin and destination must be different")
            else:
                with st.spinner("Calculating optimal route..."):
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
                    else:
                        st.error("No path found between selected points")
    
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
        
        # Road quality preference
        min_road_condition = st.slider("Minimum Road Condition", 1, 10, 6)
        
        # Run algorithm
        if st.button("Find Emergency Route"):
            with st.spinner("Calculating emergency route..."):
                # Run A* algorithm
                path, travel_time, path_edges, results = run_a_star(
                    G, 
                    emergency_id, 
                    target_hospital,
                    neighborhoods,
                    facilities,
                    min_road_condition
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
                else:
                    st.error("No suitable emergency route found. Try lowering the minimum road condition.")
    
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
                
                # Bus allocation chart
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
                
                fig = px.bar(
                    traffic_data,
                    x="road",
                    y="flow",
                    color="direction",
                    labels={"road": "Road", "flow": "Traffic Flow (vehicles per hour)"},
                    title="Directional Traffic Flow"
                )
                st.plotly_chart(fig)

if __name__ == "__main__":
    main()
