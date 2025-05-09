import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.data.loader import load_data
from src.visualization.terrain3d import display_3d_visualization

def main():
    st.set_page_config(
        page_title="3D Visualization",
        page_icon="🏔️",
        layout="wide"
    )
    
    st.title("3D Terrain Visualization")
    st.write("""
    This page provides a 3D terrain visualization of the Cairo transportation network.
    You can explore the terrain model with neighborhoods, facilities, and roads.
    """)
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("You need to log in to use the 3D visualization. Please go back to the main page and log in.")
        return
    
    # Load data
    data = load_data()
    neighborhoods = data['neighborhoods']
    facilities = data['facilities']
    existing_roads = data['existing_roads']
    
    # Create tabs for different visualization modes
    tab1, tab2 = st.tabs(["Base Network", "Analysis Results"])
    
    with tab1:
        st.subheader("Base Transportation Network")
        
        # Display the 3D visualization for the base network
        display_3d_visualization(neighborhoods, facilities, existing_roads)
    
    with tab2:
        st.subheader("3D Visualization of Analysis Results")
        
        # Get saved analyses from user profile
        username = st.session_state.username
        user_data = st.session_state.user_data
        
        if 'saved_analyses' not in user_data or not user_data['saved_analyses']:
            st.warning("You don't have any saved analyses. Run some analyses first and save them.")
        else:
            saved_analyses = user_data['saved_analyses']
            
            # Filter analyses that have path information
            route_analyses = []
            for name, analysis in saved_analyses.items():
                # MST, Dijkstra, and A* have path information
                if ("Infrastructure Network Design" in analysis['algorithm'] or 
                    "Traffic Flow" in analysis['algorithm'] or 
                    "Emergency Response" in analysis['algorithm']):
                    route_analyses.append(name)
            
            if not route_analyses:
                st.warning("No analysis results with path information found.")
            else:
                # Select analysis to visualize
                selected_analysis = st.selectbox("Select Analysis to Visualize", route_analyses)
                
                analysis_data = saved_analyses[selected_analysis]
                results = analysis_data['results']
                
                # Extract path information
                path_edges = None
                if "Infrastructure Network Design" in analysis_data['algorithm']:
                    if "selected_roads" in results:
                        path_edges = results["selected_roads"]
                elif "Traffic Flow" in analysis_data['algorithm'] or "Emergency Response" in analysis_data['algorithm']:
                    if "path_edges" in results:
                        path_edges = results["path_edges"]
                
                # Display the visualization with highlighted path
                if path_edges:
                    display_3d_visualization(neighborhoods, facilities, existing_roads, path_edges)
                else:
                    st.error("Could not extract path information from the selected analysis.")

if __name__ == "__main__":
    main()