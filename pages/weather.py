import streamlit as st
import pandas as pd
import os
import sys
import datetime
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.data.loader import load_data
from src.analysis.weather import (
    get_weather_for_date,
    simulate_weather_period,
    calculate_weather_impact_on_route,
    simulate_weather_impact_on_network,
    display_weather_simulation
)
from src.utils.export import export_to_csv, export_to_json, export_plot_to_png, export_report_to_html

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
        
        with col1:
            st.metric("Temperature", f"{weather_data['temperature']}°C")
        
        with col2:
            st.metric("Weather", weather_data['condition'])
        
        with col3:
            st.metric("Wind Speed", f"{weather_data['wind_speed']} km/h")
        
        # Route selection for impact analysis
        st.subheader("Select Route to Analyze")
        
        # Origin selection
        origin_locations = [f"{n['id']} - {n['name']}" for n in neighborhoods]
        selected_origin = st.selectbox("Select Origin", origin_locations)
        origin_id = int(selected_origin.split(" - ")[0])
        
        # Destination selection
        dest_locations = [f"{n['id']} - {n['name']}" for n in neighborhoods] + [f"{f['id']} - {f['name']}" for f in facilities]
        selected_dest = st.selectbox("Select Destination", dest_locations)
        
        if selected_dest[0].isdigit():
            destination_id = int(selected_dest.split(" - ")[0])
        else:
            destination_id = selected_dest.split(" - ")[0]
        
        # Run analysis
        if st.button("Analyze Weather Impact"):
            # Route data would come from a path finding algorithm
            # For demo, create a sample route
            route_data = {
                "origin": origin_id,
                "destination": destination_id,
                "distance": 8.5,
                "normal_time": 25,
                "path": [origin_id, 5, 3, destination_id]
            }
            
            # Calculate impact
            impact = calculate_weather_impact_on_route(route_data, weather_data)
            
            # Display results
            st.subheader("Weather Impact Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                time_increase = impact['adjusted_time'] - route_data['normal_time']
                st.metric(
                    "Travel Time",
                    f"{impact['adjusted_time']:.1f} min",
                    f"{time_increase:+.1f} min",
                    delta_color="inverse"
                )
            
            with col2:
                st.metric(
                    "Visibility",
                    f"{impact['visibility']:.0f}%",
                    f"{impact['visibility'] - 100:+.0f}%", 
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    "Road Capacity",
                    f"{impact['capacity']:.0f}%",
                    f"{impact['capacity'] - 100:+.0f}%",
                    delta_color="inverse"
                )
            
            # Risk analysis
            st.subheader("Risk Assessment")
            
            risk_data = pd.DataFrame([
                {"Risk Factor": "Accident Risk", "Value": impact['accident_risk'] * 100},
                {"Risk Factor": "Traffic Congestion", "Value": impact['congestion_risk'] * 100},
                {"Risk Factor": "Infrastructure Stress", "Value": impact['infrastructure_risk'] * 100}
            ])
            
            fig = px.bar(
                risk_data,
                x="Risk Factor",
                y="Value",
                color="Value",
                color_continuous_scale=["green", "yellow", "red"],
                title="Weather Risk Factors (%)",
                labels={"Value": "Risk Level (%)"}
            )
            st.plotly_chart(fig)
            
            # Safety recommendations
            st.subheader("Safety Recommendations")
            
            recommendations = impact['recommendations']
            for rec in recommendations:
                st.info(rec)
            
            # Export section
            st.subheader("Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                weather_impact_df = pd.DataFrame([impact])
                st.markdown(export_to_csv(weather_impact_df, "weather_impact.csv"), unsafe_allow_html=True)
                st.markdown(export_to_json(impact, "weather_impact.json"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(export_plot_to_png(fig, "weather_risk_analysis.png"), unsafe_allow_html=True)
                st.markdown(export_report_to_html("Weather Impact Analysis", impact, "weather_report.html"), unsafe_allow_html=True)
    
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
            st.dataframe(weather_df)
            
            # Temperature chart
            fig_temp = px.line(
                weather_df,
                x="date",
                y="temperature",
                title="Temperature Forecast",
                labels={"temperature": "Temperature (°C)", "date": "Date"}
            )
            st.plotly_chart(fig_temp)
            
            # Condition chart
            condition_counts = weather_df['condition'].value_counts().reset_index()
            condition_counts.columns = ["Condition", "Count"]
            
            fig_cond = px.pie(
                condition_counts,
                values="Count",
                names="Condition",
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