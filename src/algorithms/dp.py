def run_transit_optimization(total_buses, max_waiting_time, optimize_transfers):
    """
    Implements a dynamic programming solution for public transit optimization.
    
    Args:
        total_buses: Total number of buses available
        max_waiting_time: Maximum acceptable waiting time in minutes
        optimize_transfers: Whether to optimize metro-bus transfers
        
    Returns:
        optimized_schedule: Dictionary with optimized bus allocations
        results: Dictionary with additional information
    """
    # Define bus routes with demand data
    bus_routes = [
        {
            "id": "B1",
            "route": "New Cairo - Downtown Cairo",
            "daily_passengers": 35000,
            "stops": ["New Cairo", "Nasr City", "Heliopolis", "Downtown Cairo"],
            "current_buses": 12
        },
        {
            "id": "B2",
            "route": "6th October City - Dokki - Downtown Cairo",
            "daily_passengers": 42000,
            "stops": ["6th October City", "Sheikh Zayed", "Mohandessin", "Dokki", "Downtown Cairo"],
            "current_buses": 15
        },
        {
            "id": "B3",
            "route": "Maadi - Zamalek - Mohandessin",
            "daily_passengers": 28000,
            "stops": ["Maadi", "Downtown Cairo", "Zamalek", "Mohandessin"],
            "current_buses": 10
        },
        {
            "id": "B4",
            "route": "Helwan - Maadi - Downtown Cairo",
            "daily_passengers": 32000,
            "stops": ["Helwan", "Maadi", "Downtown Cairo"],
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
            "stops": ["Sheikh Zayed", "6th October City", "Mohandessin"],
            "current_buses": 7
        },
        {
            "id": "B8",
            "route": "Al Rehab - Heliopolis - Downtown Cairo",
            "daily_passengers": 22000,
            "stops": ["Al Rehab", "Nasr City", "Heliopolis", "Downtown Cairo"],
            "current_buses": 8
        },
        {
            "id": "B9",
            "route": "New Administrative Capital - New Cairo - Nasr City",
            "daily_passengers": 15000,
            "stops": ["New Administrative Capital", "Al Rehab", "New Cairo", "Nasr City"],
            "current_buses": 6
        },
        {
            "id": "B10",
            "route": "Giza - Dokki - Downtown Cairo - Ramses Railway Station",
            "daily_passengers": 38000,
            "stops": ["Giza", "Dokki", "Downtown Cairo", "Ramses Railway Station"],
            "current_buses": 14
        }
    ]
    
    # Define metro lines
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
    
    # Define transfer points between metro and bus
    transfer_points = [
        {"station": "Ramses", "metro_lines": ["M1", "M2"], "bus_routes": ["B10"]},
        {"station": "Sadat", "metro_lines": ["M1"], "bus_routes": ["B2", "B3", "B4"]},
        {"station": "Helwan", "metro_lines": ["M1"], "bus_routes": ["B4"]},
        {"station": "Maadi", "metro_lines": ["M1"], "bus_routes": ["B3", "B4", "B6"]},
        {"station": "Heliopolis", "metro_lines": ["M3"], "bus_routes": ["B1", "B5", "B8"]},
        {"station": "Giza", "metro_lines": ["M2"], "bus_routes": ["B6", "B10"]},
        {"station": "Shubra", "metro_lines": ["M1", "M2"], "bus_routes": ["B5"]},
        {"station": "Zamalek", "metro_lines": ["M3"], "bus_routes": ["B3"]},
    ]
    
    # Calculate the average operational time per day (assume 18 hours of operation)
    operational_minutes = 18 * 60
    
    # Estimate the average round-trip time for each route based on stops
    for route in bus_routes:
        # Approximate round-trip time based on number of stops
        # Assume each stop adds about 15 minutes for travel + 2 minutes for boarding/alighting
        num_stops = len(route["stops"])
        route["round_trip_time"] = num_stops * 17
    
    # Calculate maximum number of trips per bus per day
    for route in bus_routes:
        route["max_trips_per_bus"] = operational_minutes / route["round_trip_time"]
    
    # Calculate current headway (waiting time between buses)
    for route in bus_routes:
        route["current_headway_peak"] = (operational_minutes / 6) / route["current_buses"]  # Peak hours (6 hours)
        route["current_headway_offpeak"] = (operational_minutes / 12) / route["current_buses"]  # Off-peak (12 hours)
    
    # Calculate hourly passenger demand (peak and off-peak)
    peak_ratio = 0.7  # Assume 70% of daily passengers travel during peak hours
    peak_hours = 6
    offpeak_hours = 12
    
    for route in bus_routes:
        route["peak_hourly_demand"] = (route["daily_passengers"] * peak_ratio) / peak_hours
        route["offpeak_hourly_demand"] = (route["daily_passengers"] * (1 - peak_ratio)) / offpeak_hours
    
    # Dynamic Programming approach to allocate buses
    # We want to minimize waiting time based on passenger demand
    
    # First, calculate the "value" of adding a bus to each route
    # Value is the reduction in passenger waiting time (in passenger-minutes)
    route_values = []
    
    for route in bus_routes:
        # Calculate current waiting time in passenger-minutes
        current_peak_wait = route["current_headway_peak"] / 2 * route["peak_hourly_demand"] * peak_hours
        current_offpeak_wait = route["current_headway_offpeak"] / 2 * route["offpeak_hourly_demand"] * offpeak_hours
        current_total_wait = current_peak_wait + current_offpeak_wait
        
        # Calculate waiting time if one bus is added
        new_peak_wait = (operational_minutes / 6) / (route["current_buses"] + 1) / 2 * route["peak_hourly_demand"] * peak_hours
        new_offpeak_wait = (operational_minutes / 12) / (route["current_buses"] + 1) / 2 * route["offpeak_hourly_demand"] * offpeak_hours
        new_total_wait = new_peak_wait + new_offpeak_wait
        
        # Value is the reduction in waiting time
        value = current_total_wait - new_total_wait
        
        route_values.append({
            "route_id": route["id"],
            "value": value,
            "current_buses": route["current_buses"],
            "daily_passengers": route["daily_passengers"]
        })
    
    # Sort routes by value (highest first)
    route_values.sort(key=lambda x: x["value"], reverse=True)
    
    # Initialize allocation with current buses
    allocation = {route["id"]: route["current_buses"] for route in bus_routes}
    
    # Allocate additional buses greedily by value until total_buses is reached
    current_total = sum(allocation.values())
    extra_buses = total_buses - current_total
    
    # If we have extra buses to allocate
    if extra_buses > 0:
        # Keep allocating buses until we run out
        while extra_buses > 0:
            # Recalculate values after each allocation
            route_values = []
            
            for route in bus_routes:
                # Calculate current waiting time with current allocation
                current_buses = allocation[route["id"]]
                current_peak_wait = (operational_minutes / 6) / current_buses / 2 * route["peak_hourly_demand"] * peak_hours
                current_offpeak_wait = (operational_minutes / 12) / current_buses / 2 * route["offpeak_hourly_demand"] * offpeak_hours
                current_total_wait = current_peak_wait + current_offpeak_wait
                
                # Calculate waiting time if one bus is added
                new_peak_wait = (operational_minutes / 6) / (current_buses + 1) / 2 * route["peak_hourly_demand"] * peak_hours
                new_offpeak_wait = (operational_minutes / 12) / (current_buses + 1) / 2 * route["offpeak_hourly_demand"] * offpeak_hours
                new_total_wait = new_peak_wait + new_offpeak_wait
                
                # Value is the reduction in waiting time
                value = current_total_wait - new_total_wait
                
                route_values.append({
                    "route_id": route["id"],
                    "value": value,
                    "current_buses": current_buses,
                    "daily_passengers": route["daily_passengers"]
                })
            
            # Sort routes by value (highest first)
            route_values.sort(key=lambda x: x["value"], reverse=True)
            
            # Allocate a bus to the route with highest value
            allocation[route_values[0]["route_id"]] += 1
            extra_buses -= 1
    
    # If we need to reduce buses
    elif extra_buses < 0:
        # Keep removing buses until we meet the target
        while extra_buses < 0:
            # Recalculate values for removing a bus
            route_values = []
            
            for route in bus_routes:
                # Only consider routes with more than 1 bus
                current_buses = allocation[route["id"]]
                if current_buses <= 1:
                    # Can't remove the last bus
                    route_values.append({
                        "route_id": route["id"],
                        "value": float('inf'),  # Infinite cost to remove the last bus
                        "current_buses": current_buses,
                        "daily_passengers": route["daily_passengers"]
                    })
                    continue
                
                # Calculate current waiting time with current allocation
                current_peak_wait = (operational_minutes / 6) / current_buses / 2 * route["peak_hourly_demand"] * peak_hours
                current_offpeak_wait = (operational_minutes / 12) / current_buses / 2 * route["offpeak_hourly_demand"] * offpeak_hours
                current_total_wait = current_peak_wait + current_offpeak_wait
                
                # Calculate waiting time if one bus is removed
                new_peak_wait = (operational_minutes / 6) / (current_buses - 1) / 2 * route["peak_hourly_demand"] * peak_hours
                new_offpeak_wait = (operational_minutes / 12) / (current_buses - 1) / 2 * route["offpeak_hourly_demand"] * offpeak_hours
                new_total_wait = new_peak_wait + new_offpeak_wait
                
                # Cost is the increase in waiting time
                cost = new_total_wait - current_total_wait
                
                route_values.append({
                    "route_id": route["id"],
                    "value": cost,  # This is actually the cost of removing
                    "current_buses": current_buses,
                    "daily_passengers": route["daily_passengers"]
                })
            
            # Sort routes by value (lowest first - we want to remove from routes with lowest cost)
            route_values.sort(key=lambda x: x["value"])
            
            # Remove a bus from the route with lowest cost
            allocation[route_values[0]["route_id"]] -= 1
            extra_buses += 1
    
    # Calculate waiting times with new allocation
    waiting_times = []
    total_peak_waiting = 0
    total_offpeak_waiting = 0
    total_daily_passengers = 0
    
    for route in bus_routes:
        # Get allocated buses
        buses = allocation[route["id"]]
        
        # Calculate new headways
        peak_headway = (operational_minutes / 6) / buses
        offpeak_headway = (operational_minutes / 12) / buses
        
        # Average waiting time is half the headway
        peak_waiting = peak_headway / 2
        offpeak_waiting = offpeak_headway / 2
        
        # Cap waiting time to max_waiting_time
        peak_waiting = min(peak_waiting, max_waiting_time)
        offpeak_waiting = min(offpeak_waiting, max_waiting_time)
        
        waiting_times.append({
            "route": route["id"],
            "peak_waiting_time": peak_waiting,
            "offpeak_waiting_time": offpeak_waiting,
            "daily_passengers": route["daily_passengers"]
        })
        
        # Weighted by passengers
        total_peak_waiting += peak_waiting * route["peak_hourly_demand"] * peak_hours
        total_offpeak_waiting += offpeak_waiting * route["offpeak_hourly_demand"] * offpeak_hours
        total_daily_passengers += route["daily_passengers"]
    
    # Calculate average waiting times
    avg_peak_waiting = total_peak_waiting / sum(route["peak_hourly_demand"] * peak_hours for route in bus_routes)
    avg_offpeak_waiting = total_offpeak_waiting / sum(route["offpeak_hourly_demand"] * offpeak_hours for route in bus_routes)
    
    # Optimize metro-bus transfers if requested
    transfer_improvement = 0
    optimized_transfers = []
    
    if optimize_transfers:
        # For each transfer point
        for tp in transfer_points:
            # Get all connecting metro lines and bus routes
            metro_ids = tp["metro_lines"]
            bus_ids = tp["bus_routes"]
            
            # Get frequency data
            metro_frequencies = []
            for m_id in metro_ids:
                for metro in metro_lines:
                    if metro["id"] == m_id:
                        metro_frequencies.append({
                            "id": m_id,
                            "peak": metro["frequency_peak"],
                            "offpeak": metro["frequency_offpeak"]
                        })
            
            bus_headways = []
            for b_id in bus_ids:
                buses = allocation[b_id]
                peak_headway = (operational_minutes / 6) / buses
                offpeak_headway = (operational_minutes / 12) / buses
                
                bus_headways.append({
                    "id": b_id,
                    "peak": peak_headway,
                    "offpeak": offpeak_headway
                })
            
            # Calculate average waiting time with and without coordination
            # Without coordination: average waiting time is half the headway
            without_coord_peak = sum(b["peak"] / 2 for b in bus_headways) / len(bus_headways)
            without_coord_offpeak = sum(b["offpeak"] / 2 for b in bus_headways) / len(bus_headways)
            
            # With coordination: buses arrive shortly after metros
            # Assume a 2-minute buffer for transfers
            with_coord_peak = 2 + sum(m["peak"] / 4 for m in metro_frequencies) / len(metro_frequencies)
            with_coord_offpeak = 2 + sum(m["offpeak"] / 4 for m in metro_frequencies) / len(metro_frequencies)
            
            # Calculate improvement
            peak_improvement = (without_coord_peak - with_coord_peak) / without_coord_peak * 100
            offpeak_improvement = (without_coord_offpeak - with_coord_offpeak) / without_coord_offpeak * 100
            
            # Weight by number of connecting lines/routes
            weight = len(metro_ids) * len(bus_ids)
            transfer_improvement += (peak_improvement + offpeak_improvement) / 2 * weight
            
            optimized_transfers.append({
                "station": tp["station"],
                "metro_lines": ", ".join(metro_ids),
                "bus_routes": ", ".join(bus_ids),
                "avg_waiting_before": (without_coord_peak + without_coord_offpeak) / 2,
                "avg_waiting_after": (with_coord_peak + with_coord_offpeak) / 2,
                "improvement": (peak_improvement + offpeak_improvement) / 2
            })
        
        # Normalize transfer improvement (prevent division by zero)
        total_weights = sum(len(tp["metro_lines"]) * len(tp["bus_routes"]) for tp in transfer_points)
        if total_weights > 0:
            transfer_improvement = transfer_improvement / total_weights
        else:
            transfer_improvement = 0
    
    # Format results
    optimized_schedule = {"bus_allocation": allocation}
    
    results = {
        "bus_allocation": [
            {
                "route": route["id"],
                "route_name": route["route"],
                "daily_passengers": route["daily_passengers"],
                "buses_allocated": allocation[route["id"]],
                "stops": route["stops"]  # Include stops in the results
            } for route in bus_routes
        ],
        "waiting_times": waiting_times,
        "total_buses_allocated": sum(allocation.values()),
        "routes_serviced": len(bus_routes),
        "avg_peak_waiting_time": avg_peak_waiting,
        "avg_offpeak_waiting_time": avg_offpeak_waiting,
        "total_daily_passengers": total_daily_passengers,
        "transfer_improvement": transfer_improvement,
        "transfer_points": optimized_transfers if optimize_transfers else []
    }
    
    return optimized_schedule, results
