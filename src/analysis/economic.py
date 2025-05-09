import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Economic constants for Cairo (approximations)
ECONOMIC_CONSTANTS = {
    # Road construction costs (million EGP per km)
    'construction_costs': {
        'local': 5.0,         # Local road
        'collector': 9.0,     # Collector road
        'arterial': 15.0,     # Arterial road
        'highway': 28.0       # Highway
    },
    
    # Maintenance costs (thousand EGP per km per year)
    'maintenance_costs': {
        'local': 150,         # Local road
        'collector': 250,     # Collector road
        'arterial': 400,      # Arterial road
        'highway': 600        # Highway
    },
    
    # Value of time (EGP per hour)
    'time_value': {
        'commuter': 50,       # Average commuter
        'business': 200,      # Business traveler
        'freight': 300        # Freight transport
    },
    
    # Vehicle operating costs (EGP per km)
    'operating_costs': {
        'car': 2.5,           # Car
        'bus': 8.0,           # Bus
        'truck': 12.0         # Truck
    },
    
    # Accident costs (thousand EGP per accident)
    'accident_costs': {
        'fatal': 5000,        # Fatal accident
        'injury': 500,        # Injury accident
        'property': 50        # Property damage only
    },
    
    # Emission costs (EGP per kg)
    'emission_costs': {
        'CO2': 0.25,          # Carbon dioxide
        'NOx': 80,            # Nitrogen oxides
        'PM': 150             # Particulate matter
    },
    
    # Discount rates
    'discount_rate': 0.10,    # 10% discount rate for public projects
    
    # Infrastructure lifespan (years)
    'lifespan': {
        'road': 25,           # Road infrastructure
        'bridge': 50,         # Bridges
        'tunnel': 75          # Tunnels
    }
}

def calculate_infrastructure_costs(project_data):
    """
    Calculate infrastructure costs for a road project
    
    Args:
        project_data: Dictionary with project information (road type, length, etc.)
        
    Returns:
        Dictionary with cost breakdown
    """
    road_type = project_data.get('road_type', 'arterial')
    length = project_data.get('length', 0)  # km
    
    # Construction cost
    construction_cost = ECONOMIC_CONSTANTS['construction_costs'][road_type] * length
    
    # Annual maintenance cost
    annual_maintenance = ECONOMIC_CONSTANTS['maintenance_costs'][road_type] * length / 1000  # Convert from thousand to million
    
    # Calculate present value of maintenance costs over lifespan
    lifespan = project_data.get('lifespan', ECONOMIC_CONSTANTS['lifespan']['road'])
    discount_rate = project_data.get('discount_rate', ECONOMIC_CONSTANTS['discount_rate'])
    
    # Present value calculation for recurring costs
    pvif = (1 - (1 / ((1 + discount_rate) ** lifespan))) / discount_rate
    maintenance_pv = annual_maintenance * pvif
    
    # Add other infrastructure elements if specified
    bridges_cost = 0
    if 'num_bridges' in project_data:
        bridge_cost_per_unit = project_data.get('bridge_cost', 50)  # million EGP per bridge
        bridges_cost = bridge_cost_per_unit * project_data['num_bridges']
    
    tunnels_cost = 0
    if 'tunnel_length' in project_data:
        tunnel_cost_per_km = project_data.get('tunnel_cost', 150)  # million EGP per km
        tunnels_cost = tunnel_cost_per_km * project_data['tunnel_length']
    
    # Add land acquisition costs if specified
    land_cost = 0
    if 'land_area' in project_data:
        land_cost_per_sqm = project_data.get('land_cost', 0.010)  # million EGP per square meter
        land_cost = land_cost_per_sqm * project_data['land_area']
    
    # Total project cost
    total_cost = construction_cost + maintenance_pv + bridges_cost + tunnels_cost + land_cost
    
    return {
        'construction_cost': construction_cost,
        'annual_maintenance': annual_maintenance,
        'maintenance_pv': maintenance_pv,
        'bridges_cost': bridges_cost,
        'tunnels_cost': tunnels_cost,
        'land_cost': land_cost,
        'total_cost': total_cost
    }

def calculate_user_benefits(traffic_data, project_data):
    """
    Calculate user benefits from the project
    
    Args:
        traffic_data: Dictionary with traffic information (daily traffic, etc.)
        project_data: Dictionary with project information
        
    Returns:
        Dictionary with benefits breakdown
    """
    # Extract parameters with defaults
    daily_traffic = traffic_data.get('daily_traffic', 20000)  # vehicles per day
    growth_rate = traffic_data.get('traffic_growth', 0.03)    # 3% annual growth
    time_saved = traffic_data.get('time_saved', 5)            # minutes saved per trip
    distance_saved = traffic_data.get('distance_saved', 2)    # km saved per trip
    vehicle_mix = traffic_data.get('vehicle_mix', {'car': 0.8, 'bus': 0.1, 'truck': 0.1})
    passenger_occupancy = traffic_data.get('passenger_occupancy', {'car': 1.5, 'bus': 40})
    
    lifespan = project_data.get('lifespan', ECONOMIC_CONSTANTS['lifespan']['road'])
    discount_rate = project_data.get('discount_rate', ECONOMIC_CONSTANTS['discount_rate'])
    
    # Annual benefits calculation
    annual_benefits = {
        'time_savings': 0,
        'operating_cost_savings': 0,
        'accident_reduction': 0,
        'emission_reduction': 0
    }
    
    # Time savings calculation
    daily_person_hours_saved = 0
    for vehicle_type, percentage in vehicle_mix.items():
        if vehicle_type in passenger_occupancy:
            # Cars and buses carry passengers
            vehicles = daily_traffic * percentage
            passengers = vehicles * passenger_occupancy.get(vehicle_type, 1)
            person_hours = passengers * (time_saved / 60)  # Convert minutes to hours
            
            # Apply value of time based on vehicle type
            time_value_category = 'business' if vehicle_type == 'truck' else 'commuter'
            time_value = ECONOMIC_CONSTANTS['time_value'][time_value_category]
            
            annual_benefits['time_savings'] += person_hours * time_value * 365
    
    # Operating cost savings
    for vehicle_type, percentage in vehicle_mix.items():
        vehicles = daily_traffic * percentage
        operating_cost = ECONOMIC_CONSTANTS['operating_costs'].get(vehicle_type, 2.5)
        annual_benefits['operating_cost_savings'] += vehicles * distance_saved * operating_cost * 365
    
    # Accident reduction (simplified)
    accidents_per_million_vkt = traffic_data.get('accident_rate', 0.5)  # Base accident rate
    accident_reduction_factor = traffic_data.get('accident_reduction', 0.2)  # 20% reduction
    
    vkt_before = daily_traffic * traffic_data.get('original_distance', distance_saved + 5) * 365 / 1000000
    vkt_after = daily_traffic * traffic_data.get('new_distance', 5) * 365 / 1000000
    
    accidents_before = vkt_before * accidents_per_million_vkt
    accidents_after = vkt_after * accidents_per_million_vkt * (1 - accident_reduction_factor)
    accidents_saved = accidents_before - accidents_after
    
    # Simplified accident cost calculation
    accident_cost = ECONOMIC_CONSTANTS['accident_costs']['property'] * 0.7 + \
                    ECONOMIC_CONSTANTS['accident_costs']['injury'] * 0.25 + \
                    ECONOMIC_CONSTANTS['accident_costs']['fatal'] * 0.05
    
    annual_benefits['accident_reduction'] = accidents_saved * accident_cost / 1000  # Convert to million
    
    # Emission reduction (simplified)
    emission_reduction = {
        'CO2': traffic_data.get('co2_reduction', 500),  # tonnes per year
        'NOx': traffic_data.get('nox_reduction', 2),    # tonnes per year
        'PM': traffic_data.get('pm_reduction', 0.5)     # tonnes per year
    }
    
    for emission_type, reduction in emission_reduction.items():
        annual_benefits['emission_reduction'] += reduction * 1000 * ECONOMIC_CONSTANTS['emission_costs'][emission_type] / 1000000  # Convert to million
    
    # Calculate present value of benefits over project lifespan
    # Use growing annuity formula for traffic growth
    pvif_growing = (1 - ((1 + growth_rate) / (1 + discount_rate)) ** lifespan) / (discount_rate - growth_rate)
    
    benefit_pv = {}
    for benefit_type, annual_value in annual_benefits.items():
        # Apply traffic growth to all benefits except emission reduction
        if benefit_type == 'emission_reduction':
            pvif = (1 - (1 / ((1 + discount_rate) ** lifespan))) / discount_rate
            benefit_pv[benefit_type] = annual_value * pvif
        else:
            benefit_pv[benefit_type] = annual_value * pvif_growing
    
    total_benefits = sum(benefit_pv.values())
    
    # Local economic benefits (jobs, business, etc.)
    local_economic_impact = project_data.get('local_economic_impact', 0.15)  # 15% of project cost
    local_benefits = local_economic_impact * project_data.get('total_cost', 0)
    
    return {
        'annual_benefits': annual_benefits,
        'benefit_pv': benefit_pv,
        'total_benefits': total_benefits,
        'local_benefits': local_benefits
    }

def perform_economic_analysis(project_data, traffic_data):
    """
    Perform complete economic analysis of a transportation project
    
    Args:
        project_data: Dictionary with project information
        traffic_data: Dictionary with traffic information
        
    Returns:
        Dictionary with analysis results
    """
    # Calculate costs
    cost_results = calculate_infrastructure_costs(project_data)
    
    # Update project data with total cost for benefit calculations
    project_data['total_cost'] = cost_results['total_cost']
    
    # Calculate benefits
    benefit_results = calculate_user_benefits(traffic_data, project_data)
    
    # Economic indicators
    net_present_value = benefit_results['total_benefits'] - cost_results['total_cost']
    bcr = benefit_results['total_benefits'] / cost_results['total_cost'] if cost_results['total_cost'] > 0 else 0
    
    # Simplified IRR calculation (approximate)
    # We use a simplification based on the benefit-cost ratio and discount rate
    if bcr > 1:
        irr = project_data.get('discount_rate', ECONOMIC_CONSTANTS['discount_rate']) * bcr
    else:
        irr = project_data.get('discount_rate', ECONOMIC_CONSTANTS['discount_rate']) * bcr * 0.8
    
    # Payback period (simplified)
    if benefit_results['total_benefits'] > 0:
        annual_equivalent_benefit = benefit_results['total_benefits'] / \
            ((1 - (1 / ((1 + project_data.get('discount_rate', ECONOMIC_CONSTANTS['discount_rate'])) ** 
                      project_data.get('lifespan', ECONOMIC_CONSTANTS['lifespan']['road'])))) / 
             project_data.get('discount_rate', ECONOMIC_CONSTANTS['discount_rate']))
        
        payback_period = cost_results['total_cost'] / annual_equivalent_benefit
    else:
        payback_period = float('inf')
    
    return {
        'costs': cost_results,
        'benefits': benefit_results,
        'npv': net_present_value,
        'bcr': bcr,
        'irr': irr,
        'payback_period': payback_period
    }

def display_economic_analysis():
    """Display economic analysis interface in Streamlit"""
    st.subheader("Economic Analysis of Transportation Projects")
    
    # Project type selection
    project_type = st.selectbox(
        "Project Type",
        ["New Road Construction", "Road Widening/Improvement", "Bridge/Interchange", "Complete Corridor"]
    )
    
    # Create tabs for input and results
    tab1, tab2 = st.tabs(["Project Inputs", "Results Dashboard"])
    
    with tab1:
        # Project information
        st.subheader("Project Information")
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("Project Name", "Cairo North-South Corridor")
            road_type = st.selectbox("Road Type", ["local", "collector", "arterial", "highway"])
            length = st.number_input("Road Length (km)", min_value=0.1, max_value=100.0, value=10.0, step=0.1)
        
        with col2:
            lifespan = st.number_input("Project Lifespan (years)", min_value=10, max_value=100, value=25)
            discount_rate = st.slider("Discount Rate (%)", min_value=5, max_value=15, value=10) / 100
        
        # Additional infrastructure elements
        st.subheader("Additional Infrastructure Elements")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            num_bridges = st.number_input("Number of Bridges", min_value=0, max_value=20, value=2)
            bridge_cost = st.number_input("Cost per Bridge (million EGP)", min_value=10.0, max_value=500.0, value=50.0)
        
        with col2:
            tunnel_length = st.number_input("Tunnel Length (km)", min_value=0.0, max_value=20.0, value=0.0)
            tunnel_cost = st.number_input("Tunnel Cost per km (million EGP)", min_value=50.0, max_value=300.0, value=150.0)
        
        with col3:
            land_area = st.number_input("Land Acquisition (thousand sqm)", min_value=0, max_value=1000, value=100)
            land_cost = st.number_input("Land Cost (thousand EGP per sqm)", min_value=1.0, max_value=50.0, value=10.0) / 1000
        
        # Traffic information
        st.subheader("Traffic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            daily_traffic = st.number_input("Daily Traffic (vehicles)", min_value=1000, max_value=200000, value=25000, step=1000)
            traffic_growth = st.slider("Annual Traffic Growth (%)", min_value=1, max_value=10, value=3) / 100
        
        with col2:
            time_saved = st.number_input("Time Saved per Trip (minutes)", min_value=1, max_value=60, value=8)
            distance_saved = st.number_input("Distance Saved per Trip (km)", min_value=0.0, max_value=20.0, value=3.0)
        
        # Vehicle mix
        st.subheader("Vehicle Mix")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            car_pct = st.slider("Cars (%)", min_value=0, max_value=100, value=75)
        
        with col2:
            bus_pct = st.slider("Buses (%)", min_value=0, max_value=100, value=15)
        
        with col3:
            truck_pct = st.slider("Trucks (%)", min_value=0, max_value=100, value=10)
        
        # Normalize percentages
        total_pct = car_pct + bus_pct + truck_pct
        vehicle_mix = {
            'car': car_pct / total_pct,
            'bus': bus_pct / total_pct,
            'truck': truck_pct / total_pct
        }
        
        # Safety and environmental benefits
        st.subheader("Safety and Environmental Benefits")
        col1, col2 = st.columns(2)
        
        with col1:
            accident_rate = st.number_input("Accident Rate (per million vkt)", min_value=0.1, max_value=5.0, value=0.8)
            accident_reduction = st.slider("Accident Reduction (%)", min_value=5, max_value=50, value=20) / 100
        
        with col2:
            co2_reduction = st.number_input("CO2 Reduction (tonnes/year)", min_value=0, max_value=5000, value=800)
            nox_reduction = st.number_input("NOx Reduction (tonnes/year)", min_value=0.0, max_value=50.0, value=3.5)
        
        # Run analysis button
        run_analysis = st.button("Run Economic Analysis")
    
    with tab2:
        if 'economic_results' not in st.session_state:
            st.info("Run the economic analysis from the Project Inputs tab to see results.")
        else:
            # Display results dashboard
            results = st.session_state.economic_results
            
            # Key financial indicators
            st.subheader("Economic Indicators")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                npv_delta = f"{results['npv']:.1f} vs threshold"
                st.metric("Net Present Value", f"{results['npv']:.1f} M EGP", delta=npv_delta, delta_color="normal" if results['npv'] > 0 else "inverse")
            
            with col2:
                bcr_delta = f"{results['bcr'] - 1:.2f} vs threshold"
                st.metric("Benefit-Cost Ratio", f"{results['bcr']:.2f}", delta=bcr_delta, delta_color="normal" if results['bcr'] > 1 else "inverse")
            
            with col3:
                irr_delta = f"{(results['irr'] - 0.1) * 100:.1f}% vs threshold"
                st.metric("Internal Rate of Return", f"{results['irr']*100:.1f}%", delta=irr_delta, delta_color="normal" if results['irr'] > 0.1 else "inverse")
            
            with col4:
                if results['payback_period'] > 100:
                    payback_text = "Never"
                    payback_delta = "Exceeds threshold"
                else:
                    payback_text = f"{results['payback_period']:.1f} years"
                    payback_delta = f"{15 - results['payback_period']:.1f} years vs threshold"
                st.metric("Payback Period", payback_text, delta=payback_delta, delta_color="normal" if results['payback_period'] < 15 else "inverse")
            
            # Costs breakdown
            st.subheader("Project Costs Breakdown")
            
            costs = results['costs']
            cost_items = {
                'Construction': costs['construction_cost'],
                'Maintenance (PV)': costs['maintenance_pv'],
                'Bridges': costs['bridges_cost'],
                'Tunnels': costs['tunnels_cost'],
                'Land Acquisition': costs['land_cost']
            }
            
            cost_df = pd.DataFrame({
                'Cost Component': list(cost_items.keys()),
                'Amount (Million EGP)': list(cost_items.values())
            })
            
            fig = px.pie(
                cost_df,
                values='Amount (Million EGP)',
                names='Cost Component',
                title="Cost Distribution",
                hole=0.4
            )
            st.plotly_chart(fig)
            
            # Benefits breakdown
            st.subheader("Project Benefits Breakdown")
            
            benefits = results['benefits']['benefit_pv']
            benefit_items = {
                'Time Savings': benefits['time_savings'],
                'Operating Cost Savings': benefits['operating_cost_savings'],
                'Accident Reduction': benefits['accident_reduction'],
                'Emission Reduction': benefits['emission_reduction']
            }
            
            benefit_df = pd.DataFrame({
                'Benefit Component': list(benefit_items.keys()),
                'Amount (Million EGP)': list(benefit_items.values())
            })
            
            fig = px.pie(
                benefit_df,
                values='Amount (Million EGP)',
                names='Benefit Component',
                title="Benefit Distribution",
                hole=0.4
            )
            st.plotly_chart(fig)
            
            # Costs vs Benefits chart
            st.subheader("Costs vs Benefits")
            
            comparison_data = pd.DataFrame([
                {'Category': 'Total Costs', 'Amount': costs['total_cost']},
                {'Category': 'Total Benefits', 'Amount': results['benefits']['total_benefits']}
            ])
            
            fig = px.bar(
                comparison_data,
                x='Category',
                y='Amount',
                title="Costs vs Benefits (Million EGP)",
                color='Category',
                labels={'Amount': 'Million EGP'}
            )
            st.plotly_chart(fig)
            
            # Analysis details as expandable section
            with st.expander("View Detailed Analysis Results"):
                st.write("### Cost Components (Million EGP)")
                st.dataframe(cost_df)
                
                st.write("### Benefit Components (Million EGP)")
                st.dataframe(benefit_df)
                
                st.write("### Annual Benefits (Million EGP)")
                annual_benefits_df = pd.DataFrame({
                    'Benefit Component': list(results['benefits']['annual_benefits'].keys()),
                    'Annual Amount (Million EGP)': list(results['benefits']['annual_benefits'].values())
                })
                st.dataframe(annual_benefits_df)
            
            # Project recommendation
            st.subheader("Project Recommendation")
            
            if results['bcr'] >= 1.5:
                st.success(f"""
                ### Highly Recommended
                
                The project shows strong economic returns with a BCR of {results['bcr']:.2f}. 
                It should be prioritized for implementation.
                
                **Key Strengths:**
                - Substantial time savings benefits
                - Positive environmental impacts
                - Reasonable payback period
                """)
            elif results['bcr'] >= 1.0:
                st.info(f"""
                ### Recommended
                
                The project is economically viable with a BCR of {results['bcr']:.2f}.
                It should proceed but with careful cost management.
                
                **Considerations:**
                - Moderate economic returns
                - Monitor costs during implementation
                - Consider phased implementation
                """)
            else:
                st.error(f"""
                ### Not Recommended
                
                The project does not demonstrate economic viability with a BCR of {results['bcr']:.2f}.
                Reconsideration or redesign is recommended.
                
                **Concerns:**
                - Costs exceed benefits
                - Long payback period
                - Consider alternative solutions
                """)
    
    # Run the analysis when button is clicked
    if run_analysis:
        # Prepare project data
        project_data = {
            'name': project_name,
            'road_type': road_type,
            'length': length,
            'lifespan': lifespan,
            'discount_rate': discount_rate,
            'num_bridges': num_bridges,
            'bridge_cost': bridge_cost,
            'tunnel_length': tunnel_length,
            'tunnel_cost': tunnel_cost,
            'land_area': land_area,
            'land_cost': land_cost
        }
        
        # Prepare traffic data
        traffic_data = {
            'daily_traffic': daily_traffic,
            'traffic_growth': traffic_growth,
            'time_saved': time_saved,
            'distance_saved': distance_saved,
            'vehicle_mix': vehicle_mix,
            'passenger_occupancy': {'car': 1.5, 'bus': 40},
            'accident_rate': accident_rate,
            'accident_reduction': accident_reduction,
            'co2_reduction': co2_reduction,
            'nox_reduction': nox_reduction,
            'pm_reduction': nox_reduction * 0.2  # Estimate PM based on NOx
        }
        
        # Run the analysis
        results = perform_economic_analysis(project_data, traffic_data)
        
        # Store results in session state
        st.session_state.economic_results = results
        
        # Switch to results tab
        st.rerun()
    
    return