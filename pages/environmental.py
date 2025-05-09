import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.analysis.environmental import display_emission_analysis

def main():
    st.set_page_config(
        page_title="Environmental Impact Analysis",
        page_icon="🌿",
        layout="wide"
    )
    
    st.title("Environmental Impact Analysis")
    st.write("""
    This page allows you to analyze the environmental impact of transportation routes and scenarios. 
    You can either load an existing route analysis or create a custom scenario.
    """)
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("You need to log in to use environmental analysis. Please go back to the main page and log in.")
        return
    
    tab1, tab2 = st.tabs(["Analyze Saved Route", "Custom Scenario"])
    
    with tab1:
        st.subheader("Analyze Environmental Impact of Saved Route")
        
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
                selected_analysis = st.selectbox("Select Route Analysis", route_analyses)
                
                analysis_data = saved_analyses[selected_analysis]
                results = analysis_data['results']
                
                # Check if route details are available
                if 'route_details' not in results:
                    st.error("Route details not found in the selected analysis.")
                else:
                    route_details = results['route_details']
                    st.write(f"Analyzing route with {len(route_details)} segments and total distance of {results['total_distance']:.2f} km.")
                    
                    # Convert route details to the format needed for emission analysis
                    route_segments = []
                    for segment in route_details:
                        # Extract distance from the segment data
                        if 'Distance (km)' in segment:
                            distance_str = segment['Distance (km)']
                            # Handle potential string format
                            if isinstance(distance_str, str):
                                distance = float(distance_str.replace('km', '').strip())
                            else:
                                distance = float(distance_str)
                        else:
                            # Fall back to total distance divided by segments if segment distance not available
                            distance = results['total_distance'] / len(route_details)
                        
                        # Extract or estimate speed
                        if 'Time (min)' in segment:
                            time_str = segment['Time (min)']
                            if isinstance(time_str, str):
                                time_min = float(time_str.replace('min', '').strip())
                            else:
                                time_min = float(time_str)
                            
                            # Calculate speed in km/h
                            if time_min > 0:
                                speed = distance / (time_min / 60)
                            else:
                                speed = 50  # Default
                        else:
                            speed = 50  # Default speed if not available
                        
                        route_segments.append({
                            'distance': distance,
                            'speed': speed
                        })
                    
                    # Display the environmental analysis
                    display_emission_analysis(route_segments)
    
    with tab2:
        st.subheader("Create Custom Environmental Scenario")
        
        st.write("Enter route segments for analysis:")
        
        # Initialize route segments
        if 'env_route_segments' not in st.session_state:
            st.session_state.env_route_segments = [
                {'distance': 5.0, 'speed': 50},
                {'distance': 3.0, 'speed': 30},
                {'distance': 7.0, 'speed': 70}
            ]
        
        # Display and edit segments
        num_segments = st.number_input("Number of Segments", min_value=1, max_value=10, value=len(st.session_state.env_route_segments))
        
        # Adjust the number of segments
        if num_segments > len(st.session_state.env_route_segments):
            # Add segments
            for _ in range(num_segments - len(st.session_state.env_route_segments)):
                st.session_state.env_route_segments.append({'distance': 5.0, 'speed': 50})
        elif num_segments < len(st.session_state.env_route_segments):
            # Remove segments
            st.session_state.env_route_segments = st.session_state.env_route_segments[:num_segments]
        
        # Display segment inputs
        segments = []
        for i, segment in enumerate(st.session_state.env_route_segments):
            st.write(f"#### Segment {i+1}")
            col1, col2 = st.columns(2)
            
            with col1:
                distance = st.number_input(f"Distance (km)", min_value=0.1, max_value=100.0, value=float(segment['distance']), key=f"dist_{i}")
            
            with col2:
                speed = st.number_input(f"Speed (km/h)", min_value=5, max_value=130, value=int(segment['speed']), key=f"speed_{i}")
            
            segments.append({'distance': distance, 'speed': speed})
        
        # Update session state
        st.session_state.env_route_segments = segments
        
        if st.button("Analyze Environmental Impact"):
            # Display the environmental analysis for custom scenario
            display_emission_analysis(st.session_state.env_route_segments)

if __name__ == "__main__":
    main()