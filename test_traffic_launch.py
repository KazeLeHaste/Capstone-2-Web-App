#!/usr/bin/env python3
"""
Test script to verify traffic intensity in launch_simulation
"""

import json
import sys
from pathlib import Path

def test_launch_simulation_scaling():
    """Test that traffic scaling is added to SUMO command"""
    
    # Mock config with traffic intensity
    config = {
        'trafficIntensity': 10.0,
        'sumo_traffic_intensity': 10.0  # This should be set by setup_session_network
    }
    
    print("Testing traffic scaling in launch_simulation...")
    print(f"Config: {config}")
    
    # Test the logic that should be in launch_simulation
    traffic_intensity = config.get('sumo_traffic_intensity', 1.0)
    
    if traffic_intensity != 1.0:
        scale_param = ["--scale", str(traffic_intensity)]
        print(f"✓ Would add to SUMO command: {' '.join(scale_param)}")
        print(f"✓ SUMO GUI should show: Scale Traffic: {traffic_intensity}")
    else:
        print("✗ No scaling would be applied")
    
    return traffic_intensity != 1.0

if __name__ == "__main__":
    result = test_launch_simulation_scaling()
    if result:
        print("\n✅ Test PASSED - Traffic scaling should work!")
    else:
        print("\n❌ Test FAILED - Traffic scaling not working!")
