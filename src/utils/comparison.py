import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def compare_mst_scenarios(scenarios):
    """
    Compare multiple MST infrastructure scenarios
    
    Args:
        scenarios: Dictionary with scenario names as keys and results as values
    """
    if len(scenarios) < 2:
        st.warning("Need at least 2 scenarios to compare.")
        return
    
    # Extract key metrics for comparison
    comparison_data = []
    
    for name, results in scenarios.items():
        comparison_data.append({
            "Scenario": name,
            "Total Cost (million EGP)": results["total_cost"],
            "Number of Roads": len(results["selected_roads"]),
            "New Roads Added": results["new_roads_count"],
            "Existing Roads Used": results["existing_roads_count"]
        })
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(comparison_data)
    
    # Display comparison table
    st.subheader("Scenario Comparison")
    st.dataframe(comparison_df)
    
    # Create bar charts for key metrics
    metrics_to_plot = ["Total Cost (million EGP)", "Number of Roads", "New Roads Added", "Existing Roads Used"]
    
    for metric in metrics_to_plot:
        fig = px.bar(
            comparison_df,
            x="Scenario",
            y=metric,
            title=f"Comparison of {metric}",
            color="Scenario"
        )
        st.plotly_chart(fig)
    
    return comparison_df

def compare_routes(scenarios):
    """
    Compare multiple routing scenarios (Dijkstra or A*)
    
    Args:
        scenarios: Dictionary with scenario names as keys and results as values
    """
    if len(scenarios) < 2:
        st.warning("Need at least 2 scenarios to compare.")
        return
    
    # Extract key metrics for comparison
    comparison_data = []
    
    for name, results in scenarios.items():
        # Calculate travel time from route details if not directly available
        if 'travel_time' not in results:
            if 'route_details' in results:
                # For emergency routes, sum up the time from route details
                travel_time = sum(segment['time'] for segment in results['route_details'])
            else:
                travel_time = 0
        else:
            travel_time = results['travel_time']
        
        # Calculate number of segments
        if 'num_segments' not in results:
            if 'route_details' in results:
                num_segments = len(results['route_details'])
            else:
                num_segments = 0
        else:
            num_segments = results['num_segments']
        
        # Calculate average speed
        if 'avg_speed' not in results:
            if results['total_distance'] > 0 and travel_time > 0:
                avg_speed = (results['total_distance'] / (travel_time / 60))  # Convert to km/h
            else:
                avg_speed = 0
        else:
            avg_speed = results['avg_speed']
        
        comparison_data.append({
            "Scenario": name,
            "Travel Time (min)": round(travel_time, 1),
            "Distance (km)": round(results['total_distance'], 1),
            "Road Segments": num_segments,
            "Avg Speed (km/h)": round(avg_speed, 1)
        })
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(comparison_data)
    
    # Display comparison table
    st.subheader("Route Comparison")
    st.dataframe(comparison_df)
    
    # Create bar charts for key metrics
    metrics_to_plot = ["Travel Time (min)", "Distance (km)", "Road Segments", "Avg Speed (km/h)"]
    
    for metric in metrics_to_plot:
        fig = px.bar(
            comparison_df,
            x="Scenario",
            y=metric,
            title=f"Comparison of {metric}",
            color="Scenario"
        )
        st.plotly_chart(fig)
    
    return comparison_df

def compare_transit_scenarios(scenarios):
    """
    Compare multiple transit optimization scenarios
    
    Args:
        scenarios: Dictionary with scenario names as keys and results as values
    """
    if len(scenarios) < 2:
        st.warning("Need at least 2 scenarios to compare.")
        return
    
    # Extract key metrics for comparison
    comparison_data = []
    
    for name, results in scenarios.items():
        comparison_data.append({
            "Scenario": name,
            "Total Buses": results["total_buses_allocated"],
            "Routes Serviced": results["routes_serviced"],
            "Avg Peak Waiting Time (min)": results["avg_peak_waiting_time"],
            "Avg Off-peak Waiting Time (min)": results["avg_offpeak_waiting_time"],
            "Daily Passengers Served": results["total_daily_passengers"],
            "Transfer Improvement (%)": results["transfer_improvement"]
        })
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(comparison_data)
    
    # Display comparison table
    st.subheader("Transit Optimization Comparison")
    st.dataframe(comparison_df)
    
    # Create bar charts for key metrics
    metrics_to_plot = [
        "Total Buses", "Routes Serviced", "Avg Peak Waiting Time (min)", 
        "Avg Off-peak Waiting Time (min)", "Transfer Improvement (%)"
    ]
    
    for metric in metrics_to_plot:
        fig = px.bar(
            comparison_df,
            x="Scenario",
            y=metric,
            title=f"Comparison of {metric}",
            color="Scenario"
        )
        st.plotly_chart(fig)
    
    # Compare bus allocation across routes
    st.subheader("Bus Allocation Comparison by Route")
    
    # Prepare data for route comparison
    route_data = []
    
    # For each scenario, extract bus allocation by route
    for name, results in scenarios.items():
        for route in results["bus_allocation"]:
            route_data.append({
                "Scenario": name,
                "Route": route["route"],
                "Buses Allocated": route["buses_allocated"],
                "Daily Passengers": route["daily_passengers"]
            })
    
    route_df = pd.DataFrame(route_data)
    
    # Create comparison chart
    fig = px.bar(
        route_df,
        x="Route",
        y="Buses Allocated",
        color="Scenario",
        barmode="group",
        title="Bus Allocation by Route and Scenario"
    )
    st.plotly_chart(fig)
    
    return comparison_df

def compare_signal_timings(scenarios):
    """
    Compare multiple traffic signal optimization scenarios
    
    Args:
        scenarios: Dictionary with scenario names as keys and results as values
    """
    if len(scenarios) < 2:
        st.warning("Need at least 2 scenarios to compare.")
        return
    
    # Extract key metrics for comparison
    comparison_data = []
    
    for name, results in scenarios.items():
        comparison_data.append({
            "Scenario": name,
            "Total Cycle Length (s)": results["total_cycle_length"],
            "Number of Phases": results["num_phases"],
            "Avg Green Time (s)": results["avg_green_time"],
            "Avg Wait Time (s)": results["avg_wait_time"],
            "Improvement vs Fixed (%)": results["improvement_pct"]
        })
    
    # Create comparison dataframe
    comparison_df = pd.DataFrame(comparison_data)
    
    # Display comparison table
    st.subheader("Signal Timing Comparison")
    st.dataframe(comparison_df)
    
    # Create bar charts for key metrics
    metrics_to_plot = [
        "Total Cycle Length (s)", "Number of Phases", 
        "Avg Green Time (s)", "Avg Wait Time (s)", "Improvement vs Fixed (%)"
    ]
    
    for metric in metrics_to_plot:
        fig = px.bar(
            comparison_df,
            x="Scenario",
            y=metric,
            title=f"Comparison of {metric}",
            color="Scenario"
        )
        st.plotly_chart(fig)
    
    return comparison_df