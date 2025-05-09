import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Weather impact factors on traffic conditions
# Source: Based on published research on weather impacts on urban traffic
WEATHER_IMPACT_FACTORS = {
    # Speed reduction factors
    'speed_reduction': {
        'light_rain': 0.05,      # 5% reduction in speed
        'heavy_rain': 0.15,      # 15% reduction in speed
        'light_snow': 0.12,      # 12% reduction in speed
        'heavy_snow': 0.35,      # 35% reduction in speed
        'fog': 0.17,             # 17% reduction in speed
        'strong_winds': 0.08,    # 8% reduction in speed
        'normal': 0              # No reduction
    },
    
    # Capacity reduction factors (how much the road capacity is reduced)
    'capacity_reduction': {
        'light_rain': 0.08,      # 8% reduction in capacity
        'heavy_rain': 0.17,      # 17% reduction in capacity
        'light_snow': 0.15,      # 15% reduction in capacity
        'heavy_snow': 0.30,      # 30% reduction in capacity
        'fog': 0.12,             # 12% reduction in capacity
        'strong_winds': 0.09,    # 9% reduction in capacity
        'normal': 0              # No reduction
    },
    
    # Accident risk increase factors
    'accident_risk_increase': {
        'light_rain': 1.5,       # 1.5x normal accident risk
        'heavy_rain': 2.5,       # 2.5x normal accident risk
        'light_snow': 2.0,       # 2.0x normal accident risk
        'heavy_snow': 4.5,       # 4.5x normal accident risk
        'fog': 3.0,              # 3.0x normal accident risk
        'strong_winds': 1.7,     # 1.7x normal accident risk
        'normal': 1.0            # Normal accident risk
    }
}

# Sample seasonal weather patterns for Cairo (simplified)
CAIRO_WEATHER_PATTERNS = {
    'Winter': {
        'weather_types': ['normal', 'fog', 'light_rain', 'heavy_rain'],
        'probabilities': [0.70, 0.10, 0.15, 0.05],
        'temp_range': (10, 20),
        'months': [12, 1, 2]
    },
    'Spring': {
        'weather_types': ['normal', 'light_rain', 'strong_winds'],
        'probabilities': [0.80, 0.10, 0.10],
        'temp_range': (18, 30),
        'months': [3, 4, 5]
    },
    'Summer': {
        'weather_types': ['normal', 'strong_winds'],
        'probabilities': [0.95, 0.05],
        'temp_range': (25, 40),
        'months': [6, 7, 8]
    },
    'Autumn': {
        'weather_types': ['normal', 'fog', 'light_rain'],
        'probabilities': [0.85, 0.05, 0.10],
        'temp_range': (18, 28),
        'months': [9, 10, 11]
    }
}

def get_weather_for_date(date, season_override=None):
    """
    Get simulated weather for a specific date based on Cairo's seasonal patterns
    
    Args:
        date: Datetime object
        season_override: Override the season (for testing)
        
    Returns:
        Dictionary with weather data
    """
    # Determine season
    month = date.month
    
    if season_override:
        season = season_override
    else:
        if month in CAIRO_WEATHER_PATTERNS['Winter']['months']:
            season = 'Winter'
        elif month in CAIRO_WEATHER_PATTERNS['Spring']['months']:
            season = 'Spring'
        elif month in CAIRO_WEATHER_PATTERNS['Summer']['months']:
            season = 'Summer'
        else:
            season = 'Autumn'
    
    # Get weather pattern for this season
    pattern = CAIRO_WEATHER_PATTERNS[season]
    
    # Simulate weather type based on probabilities
    weather_type = np.random.choice(
        pattern['weather_types'],
        p=pattern['probabilities']
    )
    
    # Simulate temperature
    temp_min, temp_max = pattern['temp_range']
    temperature = round(np.random.uniform(temp_min, temp_max), 1)
    
    # Get impact factors
    speed_reduction = WEATHER_IMPACT_FACTORS['speed_reduction'][weather_type]
    capacity_reduction = WEATHER_IMPACT_FACTORS['capacity_reduction'][weather_type]
    accident_risk = WEATHER_IMPACT_FACTORS['accident_risk_increase'][weather_type]
    
    return {
        'date': date,
        'season': season,
        'weather_type': weather_type,
        'temperature': temperature,
        'speed_reduction': speed_reduction,
        'capacity_reduction': capacity_reduction,
        'accident_risk': accident_risk
    }

def simulate_weather_period(start_date, num_days=7, season_override=None):
    """
    Simulate weather for a period of days
    
    Args:
        start_date: Starting date as datetime object
        num_days: Number of days to simulate
        season_override: Override the season (for testing)
        
    Returns:
        List of weather data dictionaries
    """
    weather_period = []
    
    for i in range(num_days):
        date = start_date + timedelta(days=i)
        weather = get_weather_for_date(date, season_override)
        weather_period.append(weather)
    
    return weather_period

def calculate_weather_impact_on_route(route_data, weather_conditions):
    """
    Calculate the impact of weather on a route
    
    Args:
        route_data: Dictionary with route information (distance, normal_time)
        weather_conditions: Dictionary with weather conditions
        
    Returns:
        Dictionary with impact metrics
    """
    # Extract weather impact factors
    speed_reduction = weather_conditions['speed_reduction']
    capacity_reduction = weather_conditions['capacity_reduction']
    accident_risk = weather_conditions['accident_risk']
    
    # Calculate new travel time based on speed reduction
    normal_time = route_data['normal_time']  # in minutes
    weather_time = normal_time / (1 - speed_reduction)
    
    # Calculate delay
    delay = weather_time - normal_time
    
    # Calculate congestion impact based on capacity reduction
    congestion_factor = 1 / (1 - capacity_reduction) if capacity_reduction < 1 else float('inf')
    
    # During peak hours, congestion has more impact
    peak_hour_factor = 1.5
    peak_weather_time = normal_time * (1 + (congestion_factor - 1) * peak_hour_factor)
    peak_delay = peak_weather_time - normal_time
    
    return {
        'normal_time': normal_time,
        'weather_time': weather_time,
        'delay': delay,
        'delay_percentage': (delay / normal_time) * 100 if normal_time > 0 else 0,
        'peak_weather_time': peak_weather_time,
        'peak_delay': peak_delay,
        'peak_delay_percentage': (peak_delay / normal_time) * 100 if normal_time > 0 else 0,
        'accident_risk_factor': accident_risk
    }

def simulate_weather_impact_on_network(routes, weather_conditions):
    """
    Simulate the impact of weather on an entire road network
    
    Args:
        routes: Dictionary of routes with their normal conditions
        weather_conditions: Dictionary with weather conditions
        
    Returns:
        Dictionary with network-wide metrics
    """
    route_impacts = {}
    total_delay = 0
    total_normal_time = 0
    max_delay_percentage = 0
    most_affected_route = None
    
    for route_id, route_data in routes.items():
        impact = calculate_weather_impact_on_route(route_data, weather_conditions)
        route_impacts[route_id] = impact
        
        total_delay += impact['delay']
        total_normal_time += impact['normal_time']
        
        if impact['delay_percentage'] > max_delay_percentage:
            max_delay_percentage = impact['delay_percentage']
            most_affected_route = route_id
    
    network_delay_percentage = (total_delay / total_normal_time) * 100 if total_normal_time > 0 else 0
    
    return {
        'route_impacts': route_impacts,
        'total_delay': total_delay,
        'network_delay_percentage': network_delay_percentage,
        'most_affected_route': most_affected_route,
        'max_delay_percentage': max_delay_percentage
    }

def display_weather_simulation(routes=None):
    """
    Display weather simulation interface in Streamlit
    
    Args:
        routes: Dictionary of routes with their normal conditions (optional)
    """
    st.subheader("Weather Conditions Simulation")
    
    # If no routes provided, create a sample set
    if routes is None:
        st.write("No routes provided. Using sample routes for simulation.")
        routes = {
            'Downtown-Airport': {
                'name': 'Downtown Cairo to Airport',
                'distance': 20.5,
                'normal_time': 35.0
            },
            'Giza-Nasr City': {
                'name': 'Giza to Nasr City',
                'distance': 15.2,
                'normal_time': 45.0
            },
            'Heliopolis-Maadi': {
                'name': 'Heliopolis to Maadi',
                'distance': 18.7,
                'normal_time': 50.0
            },
            'October-Cairo': {
                'name': '6th October to Central Cairo',
                'distance': 28.3,
                'normal_time': 55.0
            }
        }
    
    # Date selection for weather simulation
    col1, col2 = st.columns(2)
    
    with col1:
        today = datetime.now()
        start_date = st.date_input("Simulation Start Date", today)
        start_datetime = datetime.combine(start_date, datetime.min.time())
    
    with col2:
        season_options = ["Automatic based on date", "Winter", "Spring", "Summer", "Autumn"]
        season_selection = st.selectbox("Season", season_options)
        
        season_override = None
        if season_selection != "Automatic based on date":
            season_override = season_selection
    
    # Simulate weather conditions
    weather_conditions = get_weather_for_date(start_datetime, season_override)
    
    # Display weather conditions
    st.subheader("Simulated Weather Conditions")
    
    # Weather type with emoji
    weather_emoji = {
        'normal': '☀️',
        'light_rain': '🌦️',
        'heavy_rain': '🌧️',
        'light_snow': '🌨️',
        'heavy_snow': '❄️',
        'fog': '🌫️',
        'strong_winds': '💨'
    }
    
    weather_description = {
        'normal': 'Clear Conditions',
        'light_rain': 'Light Rain',
        'heavy_rain': 'Heavy Rain',
        'light_snow': 'Light Snow',
        'heavy_snow': 'Heavy Snow',
        'fog': 'Foggy Conditions',
        'strong_winds': 'Strong Winds'
    }
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### {weather_emoji[weather_conditions['weather_type']]} {weather_description[weather_conditions['weather_type']]}")
        st.write(f"Season: {weather_conditions['season']}")
    
    with col2:
        st.metric("Temperature", f"{weather_conditions['temperature']}°C")
    
    with col3:
        st.metric("Accident Risk Factor", f"{weather_conditions['accident_risk']}x")
    
    # Display impact metrics
    st.subheader("Impact on Traffic Conditions")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Speed Reduction", f"{weather_conditions['speed_reduction']*100:.1f}%")
    
    with col2:
        st.metric("Capacity Reduction", f"{weather_conditions['capacity_reduction']*100:.1f}%")
    
    # Calculate impact on routes
    network_impact = simulate_weather_impact_on_network(routes, weather_conditions)
    
    # Display route-specific impacts
    st.subheader("Impact on Routes")
    
    route_data = []
    for route_id, route in routes.items():
        impact = network_impact['route_impacts'][route_id]
        route_data.append({
            'Route': route['name'],
            'Normal Time (min)': impact['normal_time'],
            'Weather Time (min)': round(impact['weather_time'], 1),
            'Delay (min)': round(impact['delay'], 1),
            'Delay (%)': round(impact['delay_percentage'], 1),
            'Peak Time (min)': round(impact['peak_weather_time'], 1),
            'Peak Delay (min)': round(impact['peak_delay'], 1)
        })
    
    route_df = pd.DataFrame(route_data)
    st.dataframe(route_df)
    
    # Visualize the delays
    fig = px.bar(
        route_df,
        x='Route',
        y=['Normal Time (min)', 'Delay (min)'],
        title="Impact of Weather on Travel Times",
        labels={'value': 'Time (minutes)', 'variable': 'Time Component'},
        barmode='stack'
    )
    st.plotly_chart(fig)
    
    # Peak vs Off-peak comparison
    peak_comparison = []
    for route_id, route in routes.items():
        impact = network_impact['route_impacts'][route_id]
        peak_comparison.append({
            'Route': route['name'],
            'Off-Peak Travel Time (min)': round(impact['weather_time'], 1),
            'Peak Travel Time (min)': round(impact['peak_weather_time'], 1)
        })
    
    peak_df = pd.DataFrame(peak_comparison)
    
    fig = px.bar(
        peak_df,
        x='Route',
        y=['Off-Peak Travel Time (min)', 'Peak Travel Time (min)'],
        title="Peak vs Off-Peak Travel Times in Current Weather",
        labels={'value': 'Time (minutes)', 'variable': 'Time Period'},
        barmode='group'
    )
    st.plotly_chart(fig)
    
    # Network-wide statistics
    st.subheader("Network-Wide Impact")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Network Delay", f"{network_impact['total_delay']:.1f} minutes")
        st.metric("Average Delay", f"{network_impact['network_delay_percentage']:.1f}%")
    
    with col2:
        most_affected = routes[network_impact['most_affected_route']]['name']
        st.metric("Most Affected Route", most_affected)
        st.metric("Maximum Delay", f"{network_impact['max_delay_percentage']:.1f}%")
    
    # Weather trend simulation
    st.subheader("Weather Trend Simulation")
    days_to_simulate = st.slider("Number of Days to Simulate", 3, 14, 7)
    
    if st.button("Simulate Weather Trend"):
        weather_period = simulate_weather_period(start_datetime, days_to_simulate, season_override)
        
        # Create dataframe for visualization
        weather_df = pd.DataFrame(weather_period)
        weather_df['date_str'] = weather_df['date'].dt.strftime('%Y-%m-%d')
        weather_df['weather_description'] = weather_df['weather_type'].map(weather_description)
        
        # Visualize weather trend
        fig = px.line(
            weather_df,
            x='date_str',
            y='temperature',
            title="Temperature Trend",
            labels={'date_str': 'Date', 'temperature': 'Temperature (°C)'},
            markers=True
        )
        st.plotly_chart(fig)
        
        # Visualize impact factors
        fig = px.line(
            weather_df,
            x='date_str',
            y=['speed_reduction', 'capacity_reduction', 'accident_risk'],
            title="Weather Impact Factors Over Time",
            labels={'date_str': 'Date', 'value': 'Impact Factor', 'variable': 'Factor Type'},
            markers=True
        )
        st.plotly_chart(fig)
        
        # Calculate and display the worst day for travel
        worst_day_index = weather_df['speed_reduction'].argmax()
        worst_day = weather_df.iloc[worst_day_index]
        
        st.warning(f"""
        **Worst Day for Travel: {worst_day['date_str']}**
        
        Weather: {worst_day['weather_description']}
        Temperature: {worst_day['temperature']}°C
        Speed Reduction: {worst_day['speed_reduction']*100:.1f}%
        Capacity Reduction: {worst_day['capacity_reduction']*100:.1f}%
        Accident Risk: {worst_day['accident_risk']}x normal
        """)
        
        # Recommendations
        st.subheader("Recommendations")
        
        if worst_day['weather_type'] in ['heavy_rain', 'heavy_snow', 'fog']:
            st.error("""
            ### High-Risk Weather Ahead
            
            - Consider postponing non-essential travel on the worst weather day
            - Implement emergency traffic management protocols
            - Increase public transport frequency on key routes
            - Activate road maintenance crews for rapid response
            """)
        elif worst_day['weather_type'] in ['light_rain', 'light_snow', 'strong_winds']:
            st.warning("""
            ### Moderate Weather Disruption Expected
            
            - Allow for extra travel time, especially during peak hours
            - Monitor traffic conditions and provide real-time updates
            - Ensure drainage systems are clear before rain events
            - Consider speed reductions on high-risk road segments
            """)
        else:
            st.success("""
            ### Minimal Weather Disruption Expected
            
            - Standard traffic management should be sufficient
            - Focus on regular maintenance activities
            - Monitor for any unexpected weather changes
            """)
    
    return weather_conditions