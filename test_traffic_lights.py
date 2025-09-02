#!/usr/bin/env python3
"""
Traffic Light Configuration Test Script

This script tests the traffic light configuration generation functionality
to ensure the implementation works correctly.

Usage:
    python test_traffic_lights.py

Author: Traffic Simulator Team
Date: September 2025
"""

import json
import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from simulation_manager import SimulationManager

def test_fixed_timer_config():
    """Test fixed timer traffic light configuration"""
    print("Testing Fixed Timer Traffic Light Configuration...")
    
    # Sample configuration for fixed timer
    config = {
        'trafficControl': {
            'method': 'fixed',
            'globalMode': True,
            'fixedTimer': {
                'greenPhase': 30,
                'yellowPhase': 3,
                'redPhase': 30,
                'allRedPhase': 2
            }
        }
    }
    
    # Create simulation manager
    sim_manager = SimulationManager()
    
    # Create a mock junction for testing
    import xml.etree.ElementTree as ET
    junction = ET.Element('junction', id='test_junction_1', type='traffic_light')
    
    # Test fixed timer generation
    tl_configs = sim_manager._generate_fixed_timer_tls([junction], config['trafficControl'])
    
    assert len(tl_configs) > 0, "Fixed timer configuration should generate traffic light logic"
    assert 'tlLogic id="test_junction_1" type="static"' in tl_configs[0], "Should generate static traffic light logic"
    assert f'duration="{config["trafficControl"]["fixedTimer"]["greenPhase"]}"' in tl_configs[0], "Should use configured green phase duration"
    
    print("✅ Fixed Timer configuration test passed!")
    return True

def test_adaptive_config():
    """Test adaptive traffic light configuration"""
    print("Testing Adaptive Traffic Light Configuration...")
    
    # Sample configuration for adaptive
    config = {
        'trafficControl': {
            'method': 'adaptive',
            'globalMode': True,
            'adaptive': {
                'minGreenTime': 5,
                'maxGreenTime': 60,
                'detectorSensitivity': 1.0,
                'jamThreshold': 30
            }
        }
    }
    
    # Create simulation manager
    sim_manager = SimulationManager()
    
    # Create a mock junction for testing
    import xml.etree.ElementTree as ET
    junction = ET.Element('junction', id='test_junction_2', type='traffic_light')
    
    # Test adaptive generation
    tl_configs = sim_manager._generate_adaptive_tls([junction], config['trafficControl'])
    
    assert len(tl_configs) > 0, "Adaptive configuration should generate traffic light logic and detectors"
    
    # Check for traffic light logic
    tl_logic_found = any('tlLogic id="test_junction_2" type="actuated"' in config_str for config_str in tl_configs)
    assert tl_logic_found, "Should generate actuated traffic light logic"
    
    # Check for detectors
    detector_found = any('laneAreaDetector' in config_str for config_str in tl_configs)
    assert detector_found, "Should generate lane area detectors"
    
    print("✅ Adaptive configuration test passed!")
    return True

def test_configuration_validation():
    """Test configuration validation and edge cases"""
    print("Testing Configuration Validation...")
    
    # Test with missing parameters
    minimal_config = {
        'trafficControl': {
            'method': 'fixed',
            'globalMode': True
        }
    }
    
    sim_manager = SimulationManager()
    
    # Should handle missing fixed timer configuration gracefully
    import xml.etree.ElementTree as ET
    junction = ET.Element('junction', id='test_junction_3', type='traffic_light')
    
    try:
        tl_configs = sim_manager._generate_fixed_timer_tls([junction], minimal_config['trafficControl'])
        print("✅ Configuration validation test passed!")
        return True
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False

def test_xml_generation():
    """Test XML generation and parsing"""
    print("Testing XML Generation...")
    
    config = {
        'trafficControl': {
            'method': 'fixed',
            'globalMode': True,
            'fixedTimer': {
                'greenPhase': 25,
                'yellowPhase': 4,
                'redPhase': 25,
                'allRedPhase': 3
            }
        }
    }
    
    sim_manager = SimulationManager()
    
    import xml.etree.ElementTree as ET
    junction = ET.Element('junction', id='test_xml_junction', type='traffic_light')
    
    tl_configs = sim_manager._generate_fixed_timer_tls([junction], config['trafficControl'])
    
    # Try to parse the generated XML
    try:
        for config_str in tl_configs:
            # Wrap in a root element for parsing
            test_xml = f"<root>{config_str}</root>"
            ET.fromstring(test_xml)
        
        print("✅ XML generation test passed!")
        return True
    except ET.ParseError as e:
        print(f"❌ XML generation test failed: Invalid XML generated - {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Traffic Light Configuration Tests\n")
    
    tests = [
        test_fixed_timer_config,
        test_adaptive_config,
        test_configuration_validation,
        test_xml_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Traffic light configuration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
