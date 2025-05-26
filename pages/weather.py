import streamlit as st
import pandas as pd
import os
import sys
import datetime
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import networkx as nx

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.data.loader import load_data
from src.analysis.weather import (
    get_weather_for_date,
    simulate_weather_period,
    calculate_weather_impact_on_route,
    simulate_weather_impact_on_network,
    display_weather_simulation,
    WEATHER_IMPACT_FACTORS
)
from src.utils.export import export_to_csv, export_to_json, export_plot_to_png, export_report_to_html

def find_route_between_points(origin_id, destination_id, existing_roads, neighborhoods, facilities):
    """
    Find a route between two points using the existing road network
    
    Args:
        origin_id: ID of the origin point
        destination_id: ID of the destination point
        existing_roads: List of existing roads
        neighborhoods: List of neighborhoods
        facilities: List of facilities
        
    Returns:
        Dictionary with route information or None if no route found
    """
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add all nodes (neighborhoods and facilities)
    for n in neighborhoods:
        G.add_node(n['id'], name=n['name'], type='neighborhood')
    for f in facilities:
        G.add_node(f['id'], name=f['name'], type='facility')
    
    # Add all edges (roads)
    for road in existing_roads:
        # Add edge in both directions since roads are bidirectional
        G.add_edge(road['from'], road['to'], 
                  distance=road['distance'],
                  condition=road['condition'])
        G.add_edge(road['to'], road['from'],
                  distance=road['distance'],
                  condition=road['condition'])
    
    try:
        # Try to find the shortest path
        path = nx.shortest_path(G, origin_id, destination_id, weight='distance')
        
        # Calculate total distance and time
        total_distance = 0
        for i in range(len(path) - 1):
            edge_data = G.get_edge_data(path[i], path[i + 1])
            total_distance += edge_data['distance']
        
        # Get origin and destination names
        origin_name = next((n['name'] for n in neighborhoods if n['id'] == origin_id),
                          next((f['name'] for f in facilities if f['id'] == origin_id), None))
        dest_name = next((n['name'] for n in neighborhoods if n['id'] == destination_id),
                        next((f['name'] for f in facilities if f['id'] == destination_id), None))
        
        # Calculate normal time (assuming average speed of 30 km/h)
        normal_time = total_distance * 2  # 2 minutes per km
        
        return {
            'name': f"{origin_name} to {dest_name}",
            'distance': total_distance,
            'normal_time': normal_time,
            'origin': origin_id,
            'destination': destination_id,
            'path': path
        }
    except nx.NetworkXNoPath:
        return None

def main():
    st.set_page_config(
        page_title="Weather Impact Analysis",
        page_icon="🌦️",
        layout="wide"
    )
    
    st.title("Weather Impact Analysis")
    st.write("""
    This page allows you to simulate weather conditions and analyze their impact on the transportation network.
    See how different weather conditions affect travel times, road capacities, and safety across Cairo.
    """)
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("You need to log in to use the weather simulation tool. Please go back to the main page and log in.")
        return
    
    # Load data
    data = load_data()
    neighborhoods = data['neighborhoods']
    facilities = data['facilities']
    existing_roads = data['existing_roads']
    
    # Create a dictionary of routes with their normal conditions
    routes = {}
    for road in existing_roads:
        # Get origin and destination names
        origin = next((n['name'] for n in neighborhoods if n['id'] == road['from']), 
                     next((f['name'] for f in facilities if f['id'] == road['from']), None))
        dest = next((n['name'] for n in neighborhoods if n['id'] == road['to']), 
                   next((f['name'] for f in facilities if f['id'] == road['to']), None))
        
        if origin and dest:
            route_id = f"{road['from']}-{road['to']}"
            routes[route_id] = {
                'name': f"{origin} to {dest}",
                'distance': road['distance'],
                'normal_time': road['distance'] * 2,  # Assuming average speed of 30 km/h
                'origin': road['from'],
                'destination': road['to']
            }
    
    # Create tabs for different analysis modes
    tab1, tab2 = st.tabs(["Single Day Analysis", "Multi-Day Simulation"])
    
    with tab1:
        st.subheader("Single Day Weather Impact")
        
        # Date selection
        today = datetime.now()
        selected_date = st.date_input(
            "Select Date", 
            value=today,
            min_value=today,
            max_value=today + timedelta(days=365)
        )
        
        # Weather override
        with st.expander("Override Weather Conditions"):
            use_override = st.checkbox("Override Predicted Weather", value=False)
            
            if use_override:
                weather_condition = st.selectbox(
                    "Weather Condition",
                    ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Dust Storm", "Extreme Heat"]
                )
                temperature = st.slider("Temperature (°C)", 10, 45, 25)
                wind_speed = st.slider("Wind Speed (km/h)", 0, 60, 10)
                precipitation = st.slider("Precipitation (mm)", 0, 100, 0)
                
                weather_data = {
                    "date": selected_date,
                    "condition": weather_condition,
                    "temperature": temperature,
                    "wind_speed": wind_speed,
                    "precipitation": precipitation
                }
            else:
                # Get simulated weather for the date
                weather_data = get_weather_for_date(selected_date)
        
        # Display current/predicted weather
        st.subheader("Weather Conditions")
        col1, col2, col3 = st.columns(3)
        
        # Weather type descriptions and emojis
        weather_descriptions = {
            'normal': '☀️ Clear',
            'light_rain': '🌦️ Light Rain',
            'heavy_rain': '🌧️ Heavy Rain',
            'light_snow': '🌨️ Light Snow',
            'heavy_snow': '❄️ Heavy Snow',
            'fog': '🌫️ Foggy',
            'strong_winds': '💨 Strong Winds'
        }
        
        with col1:
            st.metric("Temperature", f"{weather_data['temperature']}°C")
        
        with col2:
            weather_type = weather_data['weather_type']
            st.metric("Weather", weather_descriptions.get(weather_type, weather_type))
        
        with col3:
            # Calculate wind speed based on weather type
            wind_speed = 0
            if weather_type == 'strong_winds':
                wind_speed = 45  # km/h
            elif weather_type in ['heavy_rain', 'heavy_snow']:
                wind_speed = 25  # km/h
            elif weather_type in ['light_rain', 'light_snow']:
                wind_speed = 15  # km/h
            elif weather_type == 'fog':
                wind_speed = 5  # km/h
            st.metric("Wind Speed", f"{wind_speed} km/h")
        
        # Route selection for impact analysis
        st.subheader("Select Route to Analyze")
        
        # Origin selection
        origin_locations = [f"{n['id']} - {n['name']}" for n in neighborhoods] + [f"{f['id']} - {f['name']}" for f in facilities]
        selected_origin = st.selectbox("Select Origin", origin_locations)
        origin_id = int(selected_origin.split(" - ")[0])
        
        # Destination selection
        dest_locations = [f"{n['id']} - {n['name']}" for n in neighborhoods] + [f"{f['id']} - {f['name']}" for f in facilities]
        selected_dest = st.selectbox("Select Destination", dest_locations)
        destination_id = int(selected_dest.split(" - ")[0])
        
        # Check if origin and destination are the same
        if origin_id == destination_id:
            st.warning("Please select different origin and destination points for route analysis.")
            return
        
        # Find route between points
        route_data = find_route_between_points(origin_id, destination_id, existing_roads, neighborhoods, facilities)
        
        if route_data:
            # Get weather conditions
            weather_conditions = {
                'date': datetime.combine(selected_date, datetime.min.time()),
                'weather_type': weather_data['weather_type'],
                'temperature': weather_data['temperature'],
                'speed_reduction': WEATHER_IMPACT_FACTORS['speed_reduction'][weather_data['weather_type']],
                'capacity_reduction': WEATHER_IMPACT_FACTORS['capacity_reduction'][weather_data['weather_type']],
                'accident_risk': WEATHER_IMPACT_FACTORS['accident_risk_increase'][weather_data['weather_type']]
            }
            
            # Calculate impact
            impact = calculate_weather_impact_on_route(route_data, weather_conditions)
            
            # Display route information
            st.subheader("Route Information")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Distance", f"{route_data['distance']:.1f} km")
                st.metric("Normal Travel Time", f"{route_data['normal_time']:.1f} min")
            with col2:
                st.metric("Number of Segments", len(route_data['path']) - 1)
                # Calculate average speed only if normal_time is not zero
                avg_speed = route_data['distance'] / (route_data['normal_time'] / 60) if route_data['normal_time'] > 0 else 0
                st.metric("Average Speed", f"{avg_speed:.1f} km/h")
            
            # Display weather impact results
            st.subheader("Weather Impact Results")
            
            # Calculate time increase using weather_time instead of adjusted_time
            time_increase = impact['weather_time'] - route_data['normal_time']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Travel Time",
                    f"{impact['weather_time']:.1f} min",
                    f"+{time_increase:.1f} min"
                )
                st.metric(
                    "Peak Hour Time",
                    f"{impact['peak_weather_time']:.1f} min",
                    f"+{impact['peak_delay']:.1f} min"
                )
            
            with col2:
                st.metric(
                    "Visibility",
                    f"{impact['visibility']:.1f}%"
                )
                st.metric(
                    "Road Capacity",
                    f"{impact['capacity']:.1f}%"
                )
            
            with col3:
                st.metric(
                    "Accident Risk",
                    f"{impact['accident_risk']:.1f}x"
                )
                st.metric(
                    "Congestion Risk",
                    f"{impact['congestion_risk']:.1f}%"
                )
            
            # Display recommendations
            st.subheader("Recommendations")
            for recommendation in impact['recommendations']:
                st.write(recommendation)
            
            # Visualize impact
            st.subheader("Impact Visualization")
            
            # Create impact factors chart
            impact_factors = pd.DataFrame({
                'Factor': ['Speed Reduction', 'Capacity Reduction', 'Accident Risk'],
                'Value': [
                    weather_conditions['speed_reduction'] * 100,
                    weather_conditions['capacity_reduction'] * 100,
                    (weather_conditions['accident_risk'] - 1) * 100
                ]
            })
            
            fig = px.bar(
                impact_factors,
                x='Factor',
                y='Value',
                title="Weather Impact Factors",
                labels={'Value': 'Impact (%)', 'Factor': 'Impact Factor'}
            )
            st.plotly_chart(fig)
            
            # Create time comparison chart
            time_comparison = pd.DataFrame({
                'Time Type': ['Normal', 'Weather Impact', 'Peak Hour'],
                'Duration (min)': [
                    route_data['normal_time'],
                    impact['weather_time'],
                    impact['peak_weather_time']
                ]
            })
            
            fig = px.bar(
                time_comparison,
                x='Time Type',
                y='Duration (min)',
                title="Travel Time Comparison",
                color='Time Type',
                color_discrete_sequence=['green', 'orange', 'red']
            )
            st.plotly_chart(fig)
        else:
            st.error("No route found between selected points. Please try different locations.")
    
    with tab2:
        st.subheader("Multi-Day Weather Simulation")
        
        # Simulation parameters
        start_date = st.date_input(
            "Start Date",
            value=today,
            min_value=today,
            max_value=today + timedelta(days=365)
        )
        
        days = st.slider("Number of Days", 3, 30, 7)
        
        # Season override for testing
        with st.expander("Advanced Settings"):
            use_season_override = st.checkbox("Override Season (for testing)", value=False)
            
            season_override = None
            if use_season_override:
                season_override = st.selectbox(
                    "Season to Simulate",
                    ["Winter", "Spring", "Summer", "Fall"]
                )
        
        if st.button("Run Simulation"):
            # Run multi-day simulation
            weather_forecast = simulate_weather_period(start_date, days, season_override)
            
            # Sample route data (would come from actual routes)
            routes = {
                "Downtown-Airport": {
                    "distance": 18.5,
                    "normal_time": 45,
                    "importance": "high"
                },
                "Nasr City-Giza": {
                    "distance": 12.3,
                    "normal_time": 35,
                    "importance": "medium"
                },
                "Maadi-Heliopolis": {
                    "distance": 15.8,
                    "normal_time": 40,
                    "importance": "medium"
                },
                "El Marg-Dokki": {
                    "distance": 20.1,
                    "normal_time": 55,
                    "importance": "low"
                }
            }
            
            # Simulate network impact
            network_impact = simulate_weather_impact_on_network(routes, weather_forecast)
            
            # Display forecast
            st.subheader("Weather Forecast")
            weather_df = pd.DataFrame(weather_forecast)

            # Add weather descriptions
            weather_df['weather_description'] = weather_df['weather_type'].map(weather_descriptions)
            weather_df['date_str'] = weather_df['date'].dt.strftime('%Y-%m-%d')

            # Display the forecast with descriptions
            display_df = weather_df[['date_str', 'weather_description', 'temperature', 'speed_reduction', 'capacity_reduction', 'accident_risk']]
            display_df.columns = ['Date', 'Weather', 'Temperature (°C)', 'Speed Reduction (%)', 'Capacity Reduction (%)', 'Accident Risk Factor']
            st.dataframe(display_df)
            
            # Temperature chart
            fig_temp = px.line(
                weather_df,
                x="date_str",
                y="temperature",
                title="Temperature Forecast",
                labels={"temperature": "Temperature (°C)", "date_str": "Date"}
            )
            st.plotly_chart(fig_temp)
            
            # Weather conditions distribution
            weather_counts = weather_df['weather_type'].value_counts().reset_index()
            weather_counts.columns = ["Weather Type", "Count"]
            weather_counts['Weather Description'] = weather_counts['Weather Type'].map(weather_descriptions)
            
            fig_cond = px.pie(
                weather_counts,
                values="Count",
                names="Weather Description",
                title="Weather Conditions Distribution"
            )
            st.plotly_chart(fig_cond)
            
            # Network impact
            st.subheader("Network Impact")
            
            # Daily delay chart
            fig_delay = px.line(
                network_impact["daily_metrics"],
                x="date",
                y="avg_delay",
                title="Average Daily Delay",
                labels={"avg_delay": "Average Delay (min)", "date": "Date"}
            )
            st.plotly_chart(fig_delay)
            
            # Network metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Average Delay",
                    f"{network_impact['overall_metrics']['avg_delay']:.1f} min"
                )
            
            with col2:
                st.metric(
                    "Peak Delay",
                    f"{network_impact['overall_metrics']['peak_delay']:.1f} min"
                )
            
            with col3:
                st.metric(
                    "Reliability Index",
                    f"{network_impact['overall_metrics']['reliability_index']:.0f}%"
                )
            
            # Critical days
            st.subheader("Critical Weather Days")
            critical_days = network_impact["critical_days"]
            if critical_days:
                st.table(critical_days)
            else:
                st.info("No critical weather days detected in the forecast period.")
            
            # Export section
            st.subheader("Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(export_to_csv(weather_df, "weather_forecast.csv"), unsafe_allow_html=True)
                daily_metrics_df = pd.DataFrame(network_impact["daily_metrics"])
                st.markdown(export_to_csv(daily_metrics_df, "daily_weather_impact.csv"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(export_plot_to_png(fig_temp, "temperature_forecast.png"), unsafe_allow_html=True)
                st.markdown(export_plot_to_png(fig_delay, "delay_forecast.png"), unsafe_allow_html=True)
                st.markdown(export_report_to_html("Weather Simulation", network_impact, "weather_simulation_report.html"), unsafe_allow_html=True)

if __name__ == "__main__":
    main()