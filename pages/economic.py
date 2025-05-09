import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# Add src to the path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.analysis.economic import display_economic_analysis

def main():
    st.set_page_config(
        page_title="Economic Analysis",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("Economic Analysis")
    st.write("""
    This page provides a comprehensive economic analysis tool for transportation infrastructure projects.
    You can assess the economic viability of different project types using benefit-cost analysis.
    """)
    
    # Check if user is authenticated
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("You need to log in to use the economic analysis tool. Please go back to the main page and log in.")
        return
    
    # Display economic analysis interface
    display_economic_analysis()
    
    st.markdown("""
    ### About Economic Analysis
    
    Economic analysis is crucial for transportation planning as it helps:
    
    - Justify infrastructure investments
    - Compare alternative project designs
    - Optimize resource allocation
    - Quantify benefits to society
    - Assess long-term financial sustainability
    
    The analysis uses standard methodologies from transportation economics, including:
    
    - Net Present Value (NPV): The difference between the present value of benefits and costs
    - Benefit-Cost Ratio (BCR): The ratio of benefits to costs (> 1.0 indicates economic viability)
    - Internal Rate of Return (IRR): The discount rate at which NPV equals zero
    - Payback Period: The time required to recover the initial investment
    """)

if __name__ == "__main__":
    main()