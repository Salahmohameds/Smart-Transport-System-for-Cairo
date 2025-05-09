import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.utils.comparison import (
    compare_mst_scenarios, 
    compare_routes, 
    compare_transit_scenarios, 
    compare_signal_timings
)

def main():
    st.set_page_config(
        page_title="Comparison Mode",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("Scenario Comparison Mode")
    st.write("""
    This page allows you to compare different optimization scenarios. 
    You can compare saved scenarios or load from JSON files.
    """)
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("You need to log in to use the comparison mode. Please go back to the main page and log in.")
        return
    
    # Get saved analyses from user profile
    username = st.session_state.username
    user_data = st.session_state.user_data
    
    if 'saved_analyses' not in user_data or not user_data['saved_analyses']:
        st.warning("You don't have any saved analyses. Run some analyses first and save them.")
        return
    
    saved_analyses = user_data['saved_analyses']
    
    # Group analyses by algorithm type
    algorithm_groups = {}
    for name, analysis in saved_analyses.items():
        algorithm = analysis['algorithm']
        if algorithm not in algorithm_groups:
            algorithm_groups[algorithm] = []
        algorithm_groups[algorithm].append(name)
    
    # Select algorithm type to compare
    algorithm_options = list(algorithm_groups.keys())
    
    # Add an empty first element to force user to make a selection
    algorithm_options = ["Select Algorithm Type"] + algorithm_options
    selected_algorithm = st.selectbox("Select Algorithm Type to Compare", algorithm_options)
    
    if selected_algorithm == "Select Algorithm Type":
        st.info("Please select an algorithm type to proceed.")
        return
    
    # Select analyses to compare
    st.subheader(f"Compare {selected_algorithm} Scenarios")
    analysis_options = algorithm_groups[selected_algorithm]
    
    # Allow selecting multiple analyses
    selected_analyses = st.multiselect(
        "Select Scenarios to Compare", 
        analysis_options,
        default=analysis_options[:2] if len(analysis_options) >= 2 else analysis_options
    )
    
    if len(selected_analyses) < 2:
        st.warning("Please select at least 2 scenarios to compare.")
        return
    
    # Create a dictionary of scenarios to compare
    scenarios = {}
    for name in selected_analyses:
        analysis_data = saved_analyses[name]
        scenarios[name] = analysis_data['results']
    
    # Perform comparison based on algorithm type
    if "Infrastructure Network Design" in selected_algorithm:
        comparison_df = compare_mst_scenarios(scenarios)
    elif "Traffic Flow" in selected_algorithm or "Emergency Response" in selected_algorithm:
        comparison_df = compare_routes(scenarios)
    elif "Public Transit" in selected_algorithm:
        comparison_df = compare_transit_scenarios(scenarios)
    elif "Traffic Signal" in selected_algorithm:
        comparison_df = compare_signal_timings(scenarios)
    else:
        st.error("Comparison for this algorithm type is not yet implemented.")
        return
    
    # Export comparison
    if comparison_df is not None:
        st.subheader("Export Comparison")
        
        # Create CSV download link
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            label="Download Comparison as CSV",
            data=csv,
            file_name=f"comparison_{selected_algorithm}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Create JSON download link
        scenarios_json = json.dumps(scenarios, indent=4, default=str)
        st.download_button(
            label="Download Comparison as JSON",
            data=scenarios_json,
            file_name=f"comparison_{selected_algorithm}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()