import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Emission factors (g/km) for different vehicle types and speeds
# Source: Based on EMEP/EEA emission inventory guidebook 2019
EMISSION_FACTORS = {
    'CO2': {
        'car': {
            'low_speed': 180,      # g/km at low speeds (<40 km/h)
            'medium_speed': 150,   # g/km at medium speeds (40-70 km/h)
            'high_speed': 170      # g/km at high speeds (>70 km/h)
        },
        'bus': {
            'low_speed': 650,
            'medium_speed': 550,
            'high_speed': 600
        },
        'truck': {
            'low_speed': 800,
            'medium_speed': 700,
            'high_speed': 750
        }
    },
    'NOx': {
        'car': {
            'low_speed': 0.4,
            'medium_speed': 0.3,
            'high_speed': 0.35
        },
        'bus': {
            'low_speed': 6.0,
            'medium_speed': 5.0,
            'high_speed': 5.5
        },
        'truck': {
            'low_speed': 7.0,
            'medium_speed': 6.0,
            'high_speed': 6.5
        }
    },
    'PM': {
        'car': {
            'low_speed': 0.03,
            'medium_speed': 0.02,
            'high_speed': 0.025
        },
        'bus': {
            'low_speed': 0.2,
            'medium_speed': 0.15,
            'high_speed': 0.18
        },
        'truck': {
            'low_speed': 0.25,
            'medium_speed': 0.2,
            'high_speed': 0.22
        }
    }
}

def get_speed_category(speed):
    """Determine speed category based on speed in km/h"""
    if speed < 40:
        return 'low_speed'
    elif speed < 70:
        return 'medium_speed'
    else:
        return 'high_speed'

def calculate_emissions(distance, speed, vehicle_mix=None):
    """
    Calculate emissions for a given distance and speed
    
    Args:
        distance: Distance in km
        speed: Average speed in km/h
        vehicle_mix: Dictionary with vehicle type percentages (default: 80% cars, 10% buses, 10% trucks)
        
    Returns:
        Dictionary of emissions by type
    """
    if vehicle_mix is None:
        vehicle_mix = {'car': 0.8, 'bus': 0.1, 'truck': 0.1}
    
    speed_category = get_speed_category(speed)
    
    emissions = {
        'CO2': 0,
        'NOx': 0,
        'PM': 0
    }
    
    for vehicle_type, percentage in vehicle_mix.items():
        for emission_type in emissions.keys():
            emissions[emission_type] += (
                EMISSION_FACTORS[emission_type][vehicle_type][speed_category] * 
                distance * percentage
            )
    
    return emissions

def calculate_route_emissions(route_segments, vehicle_mix=None):
    """
    Calculate emissions for a route with multiple segments
    
    Args:
        route_segments: List of dictionaries with distance and speed for each segment
        vehicle_mix: Dictionary with vehicle type percentages
        
    Returns:
        Dictionary with total emissions and emissions by segment
    """
    total_emissions = {
        'CO2': 0,
        'NOx': 0,
        'PM': 0
    }
    
    segment_emissions = []
    
    for i, segment in enumerate(route_segments):
        distance = segment['distance']
        speed = segment.get('speed', 50)  # Default to 50 km/h if not provided
        
        emissions = calculate_emissions(distance, speed, vehicle_mix)
        
        # Add to total
        for emission_type in total_emissions.keys():
            total_emissions[emission_type] += emissions[emission_type]
        
        # Add segment data
        segment_data = {
            'segment': i + 1,
            'distance': distance,
            'speed': speed
        }
        segment_data.update(emissions)
        segment_emissions.append(segment_data)
    
    return {
        'total': total_emissions,
        'segments': segment_emissions
    }

def display_emission_analysis(route_segments, vehicle_mix=None):
    """
    Display environmental impact analysis in Streamlit
    
    Args:
        route_segments: List of dictionaries with distance and speed for each segment
        vehicle_mix: Dictionary with vehicle type percentages
    """
    if vehicle_mix is None:
        # Allow user to customize vehicle mix
        st.subheader("Vehicle Mix")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            car_pct = st.slider("Cars (%)", 0, 100, 80) / 100
        
        with col2:
            bus_pct = st.slider("Buses (%)", 0, 100, 10) / 100
        
        with col3:
            truck_pct = st.slider("Trucks (%)", 0, 100, 10) / 100
        
        # Normalize to ensure percentages add up to 1
        total = car_pct + bus_pct + truck_pct
        vehicle_mix = {
            'car': car_pct / total,
            'bus': bus_pct / total,
            'truck': truck_pct / total
        }
    
    # Calculate emissions
    emission_results = calculate_route_emissions(route_segments, vehicle_mix)
    
    # Display total emissions
    st.subheader("Total Emissions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CO₂ Emissions", f"{emission_results['total']['CO2']:.2f} g")
    
    with col2:
        st.metric("NOₓ Emissions", f"{emission_results['total']['NOx']:.2f} g")
    
    with col3:
        st.metric("Particulate Matter", f"{emission_results['total']['PM']:.2f} g")
    
    # Display segment emissions
    st.subheader("Emissions by Segment")
    segment_df = pd.DataFrame(emission_results['segments'])
    st.dataframe(segment_df)
    
    # Create emission charts
    st.subheader("Emission Distribution")
    
    # CO2 by segment
    fig = px.bar(
        segment_df,
        x="segment",
        y="CO2",
        title="CO₂ Emissions by Segment",
        labels={"segment": "Segment", "CO2": "CO₂ Emissions (g)"}
    )
    st.plotly_chart(fig)
    
    # NOx and PM by segment
    fig = px.bar(
        segment_df,
        x="segment",
        y=["NOx", "PM"],
        title="NOₓ and PM Emissions by Segment",
        labels={"segment": "Segment", "value": "Emissions (g)", "variable": "Pollutant"}
    )
    st.plotly_chart(fig)
    
    # Pie chart of emission composition
    labels = ["CO₂", "NOₓ", "PM"]
    values = [
        emission_results['total']['CO2'],
        emission_results['total']['NOx'],
        emission_results['total']['PM']
    ]
    
    # Create a derived scale to show all pollutants
    # (CO2 is much higher than others, so we need to scale)
    scaled_values = [values[0], values[1] * 100, values[2] * 1000]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=scaled_values,
        hole=.3,
        hovertemplate="<b>%{label}</b><br>%{text}<extra></extra>",
        text=[f"{v:.2f} g" for v in values]
    )])
    fig.update_layout(title_text="Emission Types (Scaled for Visualization)")
    st.plotly_chart(fig)
    
    # Display impact context
    st.subheader("Environmental Impact Context")
    co2_kg = emission_results['total']['CO2'] / 1000
    trees_equivalent = co2_kg * 0.05  # Approximate: 1 kg CO2 = 0.05 trees for one day
    
    st.info(f"""
    - The CO₂ emissions from this trip ({co2_kg:.2f} kg) are equivalent to the daily carbon sequestration of about {trees_equivalent:.1f} trees.
    - NOₓ emissions contribute to smog formation and respiratory issues.
    - Particulate matter (PM) can penetrate deep into lungs and cause health problems.
    """)
    
    # Mitigation suggestions
    st.subheader("Mitigation Strategies")
    st.success("""
    ### Ways to Reduce Environmental Impact:
    
    1. **Increase Public Transit Usage**: Shifting 10% of car traffic to buses could reduce CO₂ emissions by up to 8%.
    2. **Optimize Traffic Flow**: Reducing congestion and maintaining optimal speeds (40-60 km/h) minimizes emissions.
    3. **Green Infrastructure**: Plant trees along roadways to absorb pollutants and CO₂.
    4. **Electric Vehicles**: Transitioning to electric vehicles can reduce direct emissions significantly.
    5. **Improved Road Conditions**: Smoother roads reduce fuel consumption and emissions.
    """)
    
    return emission_results