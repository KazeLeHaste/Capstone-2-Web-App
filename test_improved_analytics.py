#!/usr/bin/env python3
"""
Test script to regenerate analytics for a session with improved analytics engine
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from analytics_engine import TrafficAnalyticsEngine

def test_session_analytics():
    """Test analytics for recent session"""
    
    # Use the recent session
    session_id = "session_1756744496240_s0zuuojsk"
    session_path = Path("backend/sessions") / session_id
    
    if not session_path.exists():
        print(f"Session path {session_path} does not exist")
        return
    
    print(f"Testing analytics for session: {session_id}")
    print(f"Session path: {session_path}")
    
    # Initialize analytics engine
    engine = TrafficAnalyticsEngine()
    
    try:
        # Generate analytics
        result = engine.analyze_session(str(session_path))
        
        if 'error' not in result:
            print("\n=== ANALYTICS RESULT ===")
            print(f"Analysis successful!")
            
            kpis = result['kpis']
            print(f"\n=== BASIC VEHICLE STATS ===")
            print(f"Total Vehicles Loaded: {kpis['total_vehicles_loaded']}")
            print(f"Total Vehicles Completed: {kpis['total_vehicles_completed']}")
            print(f"Total Vehicles Running: {kpis['total_vehicles_running']}")
            print(f"Simulation Duration: {kpis.get('simulation_duration', 'N/A')}s")
            
            if kpis.get('notes'):
                print(f"\nNote: {kpis['notes']}")
            
            print(f"\n=== TIME METRICS ===")
            print(f"Avg Travel Time: {kpis['avg_travel_time']}s")
            print(f"Avg Waiting Time: {kpis['avg_waiting_time']}s")
            
            print(f"\n=== SPEED METRICS ===")
            print(f"Avg Speed: {kpis['avg_speed']} km/h")
            
            print(f"\n=== DISTANCE METRICS ===")
            print(f"Total Distance: {kpis['total_distance_traveled']}m")
            print(f"Avg Route Length: {kpis['avg_route_length']}m")
            
            print(f"\n=== RECOMMENDATIONS ===")
            recommendations = result.get('recommendations', [])
            for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                print(f"{i}. {rec.get('message', 'No message')}")
            
        else:
            print(f"Analytics failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error running analytics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_analytics()
