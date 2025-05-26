import json

def load_data():
    """
    Load data for the Cairo transportation network.
    This includes neighborhoods, facilities, roads, and traffic patterns.
    """
    # Define neighborhoods from the dataset
    neighborhoods = [
        {"id": 1, "name": "Maadi", "population": 250000, "type": "Residential", "x": 31.25, "y": 29.96},
        {"id": 2, "name": "Nasr City", "population": 500000, "type": "Mixed", "x": 31.34, "y": 30.06},
        {"id": 3, "name": "Downtown Cairo", "population": 100000, "type": "Business", "x": 31.24, "y": 30.04},
        {"id": 4, "name": "New Cairo", "population": 300000, "type": "Residential", "x": 31.47, "y": 30.03},
        {"id": 5, "name": "Heliopolis", "population": 200000, "type": "Mixed", "x": 31.32, "y": 30.09},
        {"id": 6, "name": "Zamalek", "population": 50000, "type": "Residential", "x": 31.22, "y": 30.06},
        {"id": 7, "name": "6th October City", "population": 400000, "type": "Mixed", "x": 30.98, "y": 29.93},
        {"id": 8, "name": "Giza", "population": 550000, "type": "Mixed", "x": 31.21, "y": 29.99},
        {"id": 9, "name": "Mohandessin", "population": 180000, "type": "Business", "x": 31.20, "y": 30.05},
        {"id": 10, "name": "Dokki", "population": 220000, "type": "Mixed", "x": 31.21, "y": 30.03},
        {"id": 11, "name": "Shubra", "population": 450000, "type": "Residential", "x": 31.24, "y": 30.11},
        {"id": 12, "name": "Helwan", "population": 350000, "type": "Industrial", "x": 31.33, "y": 29.85},
        {"id": 13, "name": "New Administrative Capital", "population": 50000, "type": "Government", "x": 31.80, "y": 30.02},
        {"id": 14, "name": "Al Rehab", "population": 120000, "type": "Residential", "x": 31.49, "y": 30.06},
        {"id": 15, "name": "Sheikh Zayed", "population": 150000, "type": "Residential", "x": 30.94, "y": 30.01}
    ]
    
    # Define facilities from the dataset
    facilities = [
        {"id": "F1", "name": "Cairo International Airport", "type": "Airport", "x": 31.41, "y": 30.11},
        {"id": "F2", "name": "Ramses Railway Station", "type": "Transit Hub", "x": 31.25, "y": 30.06},
        {"id": "F3", "name": "Cairo University", "type": "Education", "x": 31.21, "y": 30.03},
        {"id": "F4", "name": "Al-Azhar University", "type": "Education", "x": 31.26, "y": 30.05},
        {"id": "F5", "name": "Egyptian Museum", "type": "Tourism", "x": 31.23, "y": 30.05},
        {"id": "F6", "name": "Cairo International Stadium", "type": "Sports", "x": 31.30, "y": 30.07},
        {"id": "F7", "name": "Smart Village", "type": "Business", "x": 30.97, "y": 30.07},
        {"id": "F8", "name": "Cairo Festival City", "type": "Commercial", "x": 31.40, "y": 30.03},
        {"id": "F9", "name": "Qasr El Aini Hospital", "type": "Medical", "x": 31.23, "y": 30.03},
        {"id": "F10", "name": "Maadi Military Hospital", "type": "Medical", "x": 31.25, "y": 29.95}
    ]
    
    # Define existing roads from the dataset
    existing_roads = [
        {"from": 1, "to": 3, "distance": 8.5, "capacity": 3000, "condition": 7},
        {"from": 1, "to": 8, "distance": 6.2, "capacity": 2500, "condition": 6},
        {"from": 2, "to": 3, "distance": 5.9, "capacity": 2800, "condition": 8},
        {"from": 2, "to": 5, "distance": 4.0, "capacity": 3200, "condition": 9},
        {"from": 3, "to": 5, "distance": 6.1, "capacity": 3500, "condition": 7},
        {"from": 3, "to": 6, "distance": 3.2, "capacity": 2000, "condition": 8},
        {"from": 3, "to": 9, "distance": 4.5, "capacity": 2600, "condition": 6},
        {"from": 3, "to": 10, "distance": 3.8, "capacity": 2400, "condition": 7},
        {"from": 4, "to": 2, "distance": 15.2, "capacity": 3800, "condition": 9},
        {"from": 4, "to": 14, "distance": 5.3, "capacity": 3000, "condition": 10},
        {"from": 5, "to": 11, "distance": 7.9, "capacity": 3100, "condition": 7},
        {"from": 6, "to": 9, "distance": 2.2, "capacity": 1800, "condition": 8},
        {"from": 7, "to": 8, "distance": 24.5, "capacity": 3500, "condition": 8},
        {"from": 7, "to": 15, "distance": 9.8, "capacity": 3000, "condition": 9},
        {"from": 8, "to": 10, "distance": 3.3, "capacity": 2200, "condition": 7},
        {"from": 8, "to": 12, "distance": 14.8, "capacity": 2600, "condition": 5},
        {"from": 9, "to": 10, "distance": 2.1, "capacity": 1900, "condition": 7},
        {"from": 10, "to": 11, "distance": 8.7, "capacity": 2400, "condition": 6},
        {"from": 11, "to": "F2", "distance": 3.6, "capacity": 2200, "condition": 7},
        {"from": 12, "to": 1, "distance": 12.7, "capacity": 2800, "condition": 6},
        {"from": 13, "to": 4, "distance": 45.0, "capacity": 4000, "condition": 10},
        {"from": 14, "to": 13, "distance": 35.5, "capacity": 3800, "condition": 9},
        {"from": 15, "to": 7, "distance": 9.8, "capacity": 3000, "condition": 9},
        {"from": "F1", "to": 5, "distance": 7.5, "capacity": 3500, "condition": 9},
        {"from": "F1", "to": 2, "distance": 9.2, "capacity": 3200, "condition": 8},
        {"from": "F2", "to": 3, "distance": 2.5, "capacity": 2000, "condition": 7},
        {"from": "F7", "to": 15, "distance": 8.3, "capacity": 2800, "condition": 8},
        {"from": "F8", "to": 4, "distance": 6.1, "capacity": 3000, "condition": 9},
        {"from": "F9", "to": 3, "distance": 1.2, "capacity": 2000, "condition": 6},
        {"from": "F10", "to": 10, "distance": 1.5, "capacity": 2000, "condition": 7},
        {"from": "F9", "to": "F10", "distance": 2.1, "capacity": 1900, "condition": 7}
    ]
    
    # Define potential new roads from the dataset
    potential_roads = [
        {"from": 1, "to": 4, "distance": 22.8, "capacity": 4000, "cost": 450},
        {"from": 1, "to": 14, "distance": 25.3, "capacity": 3800, "cost": 500},
        {"from": 2, "to": 13, "distance": 48.2, "capacity": 4500, "cost": 950},
        {"from": 3, "to": 13, "distance": 56.7, "capacity": 4500, "cost": 1100},
        {"from": 5, "to": 4, "distance": 16.8, "capacity": 3500, "cost": 320},
        {"from": 6, "to": 8, "distance": 7.5, "capacity": 2500, "cost": 150},
        {"from": 7, "to": 13, "distance": 82.3, "capacity": 4000, "cost": 1600},
        {"from": 9, "to": 11, "distance": 6.9, "capacity": 2800, "cost": 140},
        {"from": 10, "to": "F7", "distance": 27.4, "capacity": 3200, "cost": 550},
        {"from": 11, "to": 13, "distance": 62.1, "capacity": 4200, "cost": 1250},
        {"from": 12, "to": 14, "distance": 30.5, "capacity": 3600, "cost": 610},
        {"from": 14, "to": 5, "distance": 18.2, "capacity": 3300, "cost": 360},
        {"from": 15, "to": 9, "distance": 22.7, "capacity": 3000, "cost": 450},
        {"from": "F1", "to": 13, "distance": 40.2, "capacity": 4000, "cost": 800},
        {"from": "F7", "to": 9, "distance": 26.8, "capacity": 3200, "cost": 540}
    ]
    
    # Define traffic flow patterns by time of day
    traffic_flows = {
        "1-3": {"morning_peak": 2800, "afternoon": 1500, "evening_peak": 2600, "night": 800},
        "1-8": {"morning_peak": 2200, "afternoon": 1200, "evening_peak": 2100, "night": 600},
        "2-3": {"morning_peak": 2700, "afternoon": 1400, "evening_peak": 2500, "night": 700},
        "2-5": {"morning_peak": 3000, "afternoon": 1600, "evening_peak": 2800, "night": 650},
        "3-5": {"morning_peak": 3200, "afternoon": 1700, "evening_peak": 3100, "night": 800},
        "3-6": {"morning_peak": 1800, "afternoon": 1400, "evening_peak": 1900, "night": 500},
        "3-9": {"morning_peak": 2400, "afternoon": 1300, "evening_peak": 2200, "night": 550},
        "3-10": {"morning_peak": 2300, "afternoon": 1200, "evening_peak": 2100, "night": 500},
        "4-2": {"morning_peak": 3600, "afternoon": 1800, "evening_peak": 3300, "night": 750},
        "4-14": {"morning_peak": 2800, "afternoon": 1600, "evening_peak": 2600, "night": 600},
        "5-11": {"morning_peak": 2900, "afternoon": 1500, "evening_peak": 2700, "night": 650},
        "6-9": {"morning_peak": 1700, "afternoon": 1300, "evening_peak": 1800, "night": 450},
        "7-8": {"morning_peak": 3200, "afternoon": 1700, "evening_peak": 3000, "night": 700},
        "7-15": {"morning_peak": 2800, "afternoon": 1500, "evening_peak": 2600, "night": 600},
        "8-10": {"morning_peak": 2000, "afternoon": 1100, "evening_peak": 1900, "night": 450},
        "8-12": {"morning_peak": 2400, "afternoon": 1300, "evening_peak": 2200, "night": 500},
        "9-10": {"morning_peak": 1800, "afternoon": 1200, "evening_peak": 1700, "night": 400},
        "10-11": {"morning_peak": 2200, "afternoon": 1300, "evening_peak": 2100, "night": 500},
        "11-F2": {"morning_peak": 2100, "afternoon": 1200, "evening_peak": 2000, "night": 450},
        "12-1": {"morning_peak": 2600, "afternoon": 1400, "evening_peak": 2400, "night": 550},
        "13-4": {"morning_peak": 3400, "afternoon": 1600, "evening_peak": 3100, "night": 600},
        "14-13": {"morning_peak": 2600, "afternoon": 1300, "evening_peak": 2400, "night": 500},
        "15-7": {"morning_peak": 2700, "afternoon": 1400, "evening_peak": 2500, "night": 550},
        "F1-5": {"morning_peak": 3300, "afternoon": 2000, "evening_peak": 3100, "night": 1200},
        "F1-2": {"morning_peak": 3000, "afternoon": 1800, "evening_peak": 2800, "night": 1000},
        "F2-3": {"morning_peak": 1800, "afternoon": 1200, "evening_peak": 1900, "night": 600},
        "F7-15": {"morning_peak": 2500, "afternoon": 1800, "evening_peak": 2700, "night": 800},
        "F8-4": {"morning_peak": 2800, "afternoon": 2000, "evening_peak": 2600, "night": 900}
    }
    
    # Define public transit data
    metro_lines = [
        {
            "id": "M1",
            "name": "Line 1 (Helwan - New El-Marg)",
            "daily_passengers": 1500000,
            "stations": ["Helwan", "Maadi", "Sadat", "Ramses", "Shubra"],
            "frequency_peak": 3,  # minutes
            "frequency_offpeak": 6
        },
        {
            "id": "M2",
            "name": "Line 2 (Shubra - Giza)",
            "daily_passengers": 1200000,
            "stations": ["Shubra", "Ramses", "Cairo University", "Giza"],
            "frequency_peak": 4,
            "frequency_offpeak": 7
        },
        {
            "id": "M3",
            "name": "Line 3 (Airport - Imbaba)",
            "daily_passengers": 900000,
            "stations": ["Airport", "Heliopolis", "Attaba", "Zamalek", "Imbaba"],
            "frequency_peak": 4,
            "frequency_offpeak": 8
        }
    ]
    
    bus_routes = [
        {
            "id": "B1",
            "route": "New Cairo - Downtown",
            "daily_passengers": 35000,
            "stops": ["New Cairo", "Nasr City", "Heliopolis", "Downtown"],
            "current_buses": 12
        },
        {
            "id": "B2",
            "route": "6th October - Dokki - Downtown",
            "daily_passengers": 42000,
            "stops": ["6th October", "Sheikh Zayed", "Mohandessin", "Dokki", "Downtown"],
            "current_buses": 15
        },
        {
            "id": "B3",
            "route": "Maadi - Zamalek - Mohandessin",
            "daily_passengers": 28000,
            "stops": ["Maadi", "Downtown", "Zamalek", "Mohandessin"],
            "current_buses": 10
        },
        {
            "id": "B4",
            "route": "Helwan - Maadi - Downtown",
            "daily_passengers": 32000,
            "stops": ["Helwan", "Maadi", "Downtown"],
            "current_buses": 11
        },
        {
            "id": "B5",
            "route": "Nasr City - Heliopolis - Shubra",
            "daily_passengers": 30000,
            "stops": ["Nasr City", "Heliopolis", "Shubra"],
            "current_buses": 10
        },
        {
            "id": "B6",
            "route": "New Cairo - Maadi - Giza",
            "daily_passengers": 25000,
            "stops": ["New Cairo", "Maadi", "Dokki", "Giza"],
            "current_buses": 9
        },
        {
            "id": "B7",
            "route": "Sheikh Zayed - Mohandessin",
            "daily_passengers": 18000,
            "stops": ["Sheikh Zayed", "6th October", "Mohandessin"],
            "current_buses": 7
        },
        {
            "id": "B8",
            "route": "Rehab - Heliopolis - Downtown",
            "daily_passengers": 22000,
            "stops": ["Rehab", "Nasr City", "Heliopolis", "Downtown"],
            "current_buses": 8
        },
        {
            "id": "B9",
            "route": "NAC - New Cairo - Nasr City",
            "daily_passengers": 15000,
            "stops": ["NAC", "Rehab", "New Cairo", "Nasr City"],
            "current_buses": 6
        },
        {
            "id": "B10",
            "route": "Giza - Dokki - Downtown - Ramses",
            "daily_passengers": 38000,
            "stops": ["Giza", "Dokki", "Downtown", "Ramses"],
            "current_buses": 14
        }
    ]
    
    # Bundle all data
    data = {
        "neighborhoods": neighborhoods,
        "facilities": facilities,
        "existing_roads": existing_roads,
        "potential_roads": potential_roads,
        "traffic_flows": traffic_flows,
        "metro_lines": metro_lines,
        "bus_routes": bus_routes
    }
    
    return data
