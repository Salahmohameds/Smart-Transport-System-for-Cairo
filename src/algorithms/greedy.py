def run_greedy_algorithm(traffic_flows, intersection, time_period, optimization_priority, max_cycle_length):
    """
    Implements a greedy algorithm for traffic signal optimization.
    
    Args:
        traffic_flows: Dictionary containing traffic flow data
        intersection: Dictionary with intersection data
        time_period: Time period to optimize for
        optimization_priority: Optimization priority strategy
        max_cycle_length: Maximum cycle length in seconds
        
    Returns:
        signal_plan: Dictionary with optimized signal timing
        results: Dictionary with additional information
    """
    # Get the roads at this intersection
    roads = intersection["roads"]
    
    # Prepare traffic data at this intersection
    traffic_data = []
    
    for road_id in roads:
        # Check if traffic data exists for this road
        if road_id in traffic_flows:
            # Get traffic flow for the specified time period
            if time_period == "all_day":
                # Calculate average flow over all periods
                flow = sum(traffic_flows[road_id].values()) / len(traffic_flows[road_id])
            else:
                flow = traffic_flows[road_id].get(time_period, 0)
            
            # Add to traffic data
            traffic_data.append({
                "road": road_id,
                "flow": flow,
                "direction": "inbound"  # Assume inbound direction
            })
            
            # Also add outbound direction with estimated flow
            # Typically outbound is some percentage of inbound depending on the time of day
            if time_period == "morning_peak":
                outbound_ratio = 0.6  # Less outbound traffic in morning
            elif time_period == "evening_peak":
                outbound_ratio = 1.2  # More outbound traffic in evening
            else:
                outbound_ratio = 0.9  # Roughly balanced
            
            traffic_data.append({
                "road": road_id,
                "flow": flow * outbound_ratio,
                "direction": "outbound"
            })
    
    # Define the optimization approaches
    if optimization_priority == "Minimize Average Delay":
        # Allocate green time proportionally to traffic flow
        total_flow = sum(entry["flow"] for entry in traffic_data)
        
        # Calculate the minimum green time needed per road (seconds)
        min_green_time = 10  # Minimum reasonable green time
        
        # Calculate green times proportionally
        green_times = {}
        for road_id in roads:
            # Calculate total flow for this road (both directions)
            road_flow = sum(entry["flow"] for entry in traffic_data if entry["road"] == road_id)
            
            # Calculate proportional green time
            green_time = max(min_green_time, (road_flow / total_flow) * (max_cycle_length - len(roads) * min_green_time) + min_green_time)
            
            green_times[road_id] = green_time
    
    elif optimization_priority == "Prioritize High-Traffic Roads":
        # Sort roads by traffic volume and give more time to busier roads
        road_flows = {}
        for road_id in roads:
            road_flow = sum(entry["flow"] for entry in traffic_data if entry["road"] == road_id)
            road_flows[road_id] = road_flow
        
        # Sort roads by flow (highest first)
        sorted_roads = sorted(road_flows.items(), key=lambda x: x[1], reverse=True)
        
        # Allocate time with exponential weighting favoring busier roads
        total_weight = sum((flow ** 1.5) for _, flow in sorted_roads)
        
        # Calculate green times
        green_times = {}
        for road_id, flow in sorted_roads:
            weight = (flow ** 1.5) / total_weight
            green_time = max(10, weight * max_cycle_length)
            green_times[road_id] = green_time
    
    else:  # "Balance Wait Times"
        # Calculate green times to balance waiting times
        # This means roads with higher flow get more time, but not proportionally
        # Use square root of flow for more balanced allocation
        road_flows = {}
        for road_id in roads:
            road_flow = sum(entry["flow"] for entry in traffic_data if entry["road"] == road_id)
            road_flows[road_id] = road_flow
        
        # Calculate weights using square root
        road_weights = {road_id: (flow ** 0.5) for road_id, flow in road_flows.items()}
        total_weight = sum(road_weights.values())
        
        # Calculate green times
        green_times = {}
        for road_id, weight in road_weights.items():
            green_time = max(15, (weight / total_weight) * max_cycle_length)
            green_times[road_id] = green_time
    
    # Normalize green times to fit within max_cycle_length
    total_green = sum(green_times.values())
    scaling_factor = max_cycle_length / total_green
    
    for road_id in green_times:
        green_times[road_id] = green_times[road_id] * scaling_factor
    
    # Create signal plan
    signal_plan = {}
    red_times = {}
    
    for road_id in roads:
        green_time = int(green_times[road_id])
        red_time = int(max_cycle_length - green_time)
        
        signal_plan[road_id] = {
            "green_time": green_time,
            "red_time": red_time
        }
        
        red_times[road_id] = red_time
    
    # Calculate average wait time
    total_waiting = 0
    for entry in traffic_data:
        road_id = entry["road"]
        flow = entry["flow"]
        
        # Wait time is roughly half the red time on average
        wait_time = red_times[road_id] / 2
        
        # Total passenger waiting (flow * average wait)
        total_waiting += flow * wait_time
    
    avg_wait_time = total_waiting / sum(entry["flow"] for entry in traffic_data)
    
    # Calculate comparison against fixed timing (all roads get equal green time)
    fixed_green_time = max_cycle_length / len(roads)
    fixed_red_time = max_cycle_length - fixed_green_time
    
    fixed_waiting = 0
    for entry in traffic_data:
        flow = entry["flow"]
        fixed_waiting += flow * (fixed_red_time / 2)
    
    fixed_avg_wait = fixed_waiting / sum(entry["flow"] for entry in traffic_data)
    
    # Calculate improvement
    improvement_pct = (fixed_avg_wait - avg_wait_time) / fixed_avg_wait * 100
    
    # Prepare results
    results = {
        "total_cycle_length": max_cycle_length,
        "num_phases": len(roads),
        "avg_green_time": sum(signal_plan[road]["green_time"] for road in roads) / len(roads),
        "total_flow": sum(entry["flow"] for entry in traffic_data),
        "avg_wait_time": avg_wait_time,
        "improvement_pct": improvement_pct,
        "traffic_data": traffic_data
    }
    
    return signal_plan, results
