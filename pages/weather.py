import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.analysis.weather import display_weather_simulation

def main():
    st.set_page_config(
        page_title="Weather Impact Simulation",
        page_icon="🌦️",
        layout="wide"
    )
    
    st.title("Weather Impact Simulation")
    st.write("""
    This page allows you to simulate the impact of various weather conditions on the transportation network.
    You can analyze both saved routes and sample routes.
    """)
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("You need to log in to use weather simulation. Please go back to the main page and log in.")
        return
    
    tab1, tab2 = st.tabs(["Analyze Saved Routes", "Sample Network"])
    
    with tab1:
        st.subheader("Analyze Weather Impact on Saved Routes")
        
        # Get saved analyses from user profile
        username = st.session_state.username
        user_data = st.session_state.user_data
        
        if 'saved_analyses' not in user_data or not user_data['saved_analyses']:
            st.warning("You don't have any saved analyses. Run some route analyses first and save them.")
        else:
            saved_analyses = user_data['saved_analyses']
            route_analyses = []
            
            # Find traffic flow and emergency route analyses
            for name, analysis in saved_analyses.items():
                if "Traffic Flow" in analysis['algorithm'] or "Emergency Response" in analysis['algorithm']:
                    route_analyses.append(name)
            
            if not route_analyses:
                st.warning("No traffic route analyses found. Please run Traffic Flow or Emergency Response analyses first.")
            else:
                # Allow selecting multiple routes
                selected_analyses = st.multiselect(
                    "Select Routes to Analyze", 
                    route_analyses,
                    default=route_analyses[:1] if route_analyses else []
                )
                
                if not selected_analyses:
                    st.info("Please select at least one route to analyze.")
                else:
                    # Prepare routes dictionary for the simulation
                    routes = {}
                    
                    for analysis_name in selected_analyses:
                        analysis_data = saved_analyses[analysis_name]
                        results = analysis_data['results']
                        
                        # Extract key route information
                        if 'total_distance' in results and 'travel_time' in results:
                            route_id = analysis_name.replace(" ", "-")
                            routes[route_id] = {
                                'name': analysis_name,
                                'distance': results['total_distance'],
                                'normal_time': results['travel_time']
                            }
                    
                    if routes:
                        # Run the weather simulation with the selected routes
                        display_weather_simulation(routes)
                    else:
                        st.error("Could not extract route information from the selected analyses.")
    
    with tab2:
        st.subheader("Sample Network Weather Impact")
        st.write("This simulation uses sample routes in Cairo to demonstrate weather impacts.")
        
        # Run the weather simulation with default sample routes
        display_weather_simulation()

if __name__ == "__main__":
    main()