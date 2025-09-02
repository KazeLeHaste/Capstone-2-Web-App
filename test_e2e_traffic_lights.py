#!/usr/bin/env python3
"""
End-to-End Traffic Light Test

This script creates a complete simulation session with traffic light configuration
and verifies that the files are generated correctly.

Usage:
    python test_e2e_traffic_lights.py

Author: Traffic Simulator Team
Date: September 2025
"""

import json
import sys
import os
import tempfile
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from simulation_manager import SimulationManager

def create_test_network():
    """Create a simple test network with traffic lights"""
    network_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">

    <location netOffset="0.00,0.00" convBoundary="0.00,0.00,200.00,200.00" origBoundary="0.00,0.00,200.00,200.00" projParameter="!"/>

    <edge id="n1_to_center" from="n1" to="center" priority="7" numLanes="2" speed="13.89">
        <lane id="n1_to_center_0" index="0" speed="13.89" length="100.00" shape="100.00,200.00 100.00,100.00"/>
        <lane id="n1_to_center_1" index="1" speed="13.89" length="100.00" shape="96.80,200.00 96.80,100.00"/>
    </edge>

    <edge id="center_to_n2" from="center" to="n2" priority="7" numLanes="2" speed="13.89">
        <lane id="center_to_n2_0" index="0" speed="13.89" length="100.00" shape="100.00,96.80 100.00,0.00"/>
        <lane id="center_to_n2_1" index="1" speed="13.89" length="100.00" shape="103.20,96.80 103.20,0.00"/>
    </edge>

    <edge id="n3_to_center" from="n3" to="center" priority="7" numLanes="2" speed="13.89">
        <lane id="n3_to_center_0" index="0" speed="13.89" length="100.00" shape="0.00,100.00 96.80,100.00"/>
        <lane id="n3_to_center_1" index="1" speed="13.89" length="100.00" shape="0.00,103.20 96.80,103.20"/>
    </edge>

    <edge id="center_to_n4" from="center" to="n4" priority="7" numLanes="2" speed="13.89">
        <lane id="center_to_n4_0" index="0" speed="13.89" length="100.00" shape="103.20,100.00 200.00,100.00"/>
        <lane id="center_to_n4_1" index="1" speed="13.89" length="100.00" shape="103.20,103.20 200.00,103.20"/>
    </edge>

    <junction id="center" type="traffic_light" x="100.00" y="100.00" incLanes="n1_to_center_0 n1_to_center_1 n3_to_center_0 n3_to_center_1" intLanes=":center_0_0 :center_1_0 :center_2_0 :center_3_0" shape="95.20,100.00 104.80,100.00 104.80,104.80 95.20,104.80">
        <request index="0" response="0000" foes="1000" cont="0"/>
        <request index="1" response="0000" foes="0100" cont="0"/>
        <request index="2" response="0000" foes="0010" cont="0"/>
        <request index="3" response="0000" foes="0001" cont="0"/>
    </junction>

    <junction id="n1" type="priority" x="100.00" y="200.00" incLanes="" intLanes="" shape="98.40,200.00 101.60,200.00"/>
    <junction id="n2" type="priority" x="100.00" y="0.00" incLanes="center_to_n2_0 center_to_n2_1" intLanes="" shape="98.40,0.00 104.80,0.00"/>
    <junction id="n3" type="priority" x="0.00" y="100.00" incLanes="" intLanes="" shape="0.00,101.60 0.00,98.40"/>
    <junction id="n4" type="priority" x="200.00" y="100.00" incLanes="center_to_n4_0 center_to_n4_1" intLanes="" shape="200.00,98.40 200.00,104.80"/>

    <connection from="n1_to_center" to="center_to_n2" fromLane="0" toLane="0" via=":center_0_0" dir="s" state="O"/>
    <connection from="n1_to_center" to="center_to_n4" fromLane="1" toLane="1" via=":center_1_0" dir="l" state="O"/>
    <connection from="n3_to_center" to="center_to_n4" fromLane="0" toLane="0" via=":center_2_0" dir="s" state="O"/>
    <connection from="n3_to_center" to="center_to_n2" fromLane="1" toLane="1" via=":center_3_0" dir="l" state="O"/>

</net>'''
    return network_xml

def test_fixed_timer_simulation():
    """Test complete simulation setup with fixed timer traffic lights"""
    print("🔧 Testing Fixed Timer Traffic Light Simulation Setup...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test network
        network_file = temp_path / "test_network.net.xml"
        with open(network_file, 'w') as f:
            f.write(create_test_network())
        
        # Create simulation manager
        sim_manager = SimulationManager(base_networks_dir=temp_path, websocket_handler=None)
        
        # Configuration with fixed timer traffic lights
        config = {
            'sessionId': 'test_session_fixed',
            'timestamp': '2025-09-03T12:00:00Z',
            'config': {
                'sumo_begin': 0,
                'sumo_end': 300,
                'sumo_step_length': 1.0,
                'sumo_time_to_teleport': 300,
                'sumo_traffic_intensity': 1.0,
                'enabledVehicles': ['passenger'],
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
        }
        
        # Save configuration
        result = sim_manager.save_session_config('test_session_fixed', config)
        assert result['success'], f"Failed to save configuration: {result.get('message')}"
        
        # Setup network in session
        setup_result = sim_manager.setup_session_network(
            'test_session_fixed',
            'test_network',
            str(network_file),
            config['config']
        )
        assert setup_result['success'], f"Failed to setup network: {setup_result.get('message')}"
        
        # Check that additional file was created and contains traffic light logic
        session_dir = sim_manager.sessions_dir / 'test_session_fixed'
        additional_file = session_dir / 'test_network.add.xml'
        
        assert additional_file.exists(), "Additional file should be created"
        
        # Parse and verify traffic light logic
        with open(additional_file, 'r') as f:
            content = f.read()
        
        assert 'tlLogic id="center" type="static"' in content, "Should contain static traffic light logic"
        assert 'duration="30"' in content, "Should contain configured green phase duration"
        assert 'duration="3"' in content, "Should contain configured yellow phase duration"
        
        print("✅ Fixed Timer simulation setup test passed!")
        return True

def test_adaptive_simulation():
    """Test complete simulation setup with adaptive traffic lights"""
    print("🔧 Testing Adaptive Traffic Light Simulation Setup...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test network
        network_file = temp_path / "test_network.net.xml"
        with open(network_file, 'w') as f:
            f.write(create_test_network())
        
        # Create simulation manager
        sim_manager = SimulationManager(base_networks_dir=temp_path, websocket_handler=None)
        
        # Configuration with adaptive traffic lights
        config = {
            'sessionId': 'test_session_adaptive',
            'timestamp': '2025-09-03T12:00:00Z',
            'config': {
                'sumo_begin': 0,
                'sumo_end': 300,
                'sumo_step_length': 1.0,
                'sumo_time_to_teleport': 300,
                'sumo_traffic_intensity': 1.0,
                'enabledVehicles': ['passenger'],
                'trafficControl': {
                    'method': 'adaptive',
                    'globalMode': True,
                    'adaptive': {
                        'minGreenTime': 10,
                        'maxGreenTime': 60,
                        'detectorSensitivity': 1.5,
                        'jamThreshold': 25
                    }
                }
            }
        }
        
        # Save configuration
        result = sim_manager.save_session_config('test_session_adaptive', config)
        assert result['success'], f"Failed to save configuration: {result.get('message')}"
        
        # Setup network in session
        setup_result = sim_manager.setup_session_network(
            'test_session_adaptive',
            'test_network',
            str(network_file),
            config['config']
        )
        assert setup_result['success'], f"Failed to setup network: {setup_result.get('message')}"
        
        # Check that additional file was created and contains traffic light logic and detectors
        session_dir = sim_manager.sessions_dir / 'test_session_adaptive'
        additional_file = session_dir / 'test_network.add.xml'
        
        assert additional_file.exists(), "Additional file should be created"
        
        # Parse and verify adaptive traffic light logic and detectors
        with open(additional_file, 'r') as f:
            content = f.read()
        
        assert 'tlLogic id="center" type="actuated"' in content, "Should contain actuated traffic light logic"
        assert 'minDur="10"' in content, "Should contain configured minimum green duration"
        assert 'maxDur="60"' in content, "Should contain configured maximum green duration"
        assert 'laneAreaDetector' in content, "Should contain lane area detectors"
        assert 'detector-gap' in content, "Should contain detector parameters"
        
        print("✅ Adaptive simulation setup test passed!")
        return True

def test_xml_validity():
    """Test that generated XML files are valid and parseable"""
    print("🔧 Testing XML Validity...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test network
        network_file = temp_path / "test_network.net.xml"
        with open(network_file, 'w') as f:
            f.write(create_test_network())
        
        # Create simulation manager
        sim_manager = SimulationManager(base_networks_dir=temp_path, websocket_handler=None)
        
        # Test both configurations
        configs = [
            {
                'trafficControl': {
                    'method': 'fixed',
                    'globalMode': True,
                    'fixedTimer': {'greenPhase': 25, 'yellowPhase': 4, 'redPhase': 25, 'allRedPhase': 3}
                }
            },
            {
                'trafficControl': {
                    'method': 'adaptive',
                    'globalMode': True,
                    'adaptive': {'minGreenTime': 8, 'maxGreenTime': 45, 'detectorSensitivity': 1.2, 'jamThreshold': 20}
                }
            }
        ]
        
        for i, config in enumerate(configs):
            session_id = f'xml_test_{i}'
            full_config = {
                'sessionId': session_id,
                'timestamp': '2025-09-03T12:00:00Z',
                'config': {
                    'sumo_begin': 0,
                    'sumo_end': 300,
                    'sumo_step_length': 1.0,
                    'sumo_time_to_teleport': 300,
                    'sumo_traffic_intensity': 1.0,
                    'enabledVehicles': ['passenger'],
                    **config
                }
            }
            
            # Save and setup
            sim_manager.save_session_config(session_id, full_config)
            setup_result = sim_manager.setup_session_network(session_id, 'test_network', str(network_file), full_config['config'])
            
            assert setup_result['success'], f"Failed to setup network for config {i}: {setup_result.get('message')}"
            
            # Validate XML
            session_dir = sim_manager.sessions_dir / session_id
            additional_file = session_dir / 'test_network.add.xml'
            
            try:
                tree = ET.parse(additional_file)
                root = tree.getroot()
                assert root.tag == 'additional', "Root element should be 'additional'"
                print(f"✅ XML validation passed for configuration {i} ({config['trafficControl']['method']})")
            except ET.ParseError as e:
                assert False, f"Generated XML is not valid for config {i}: {e}"
        
        print("✅ XML validity test passed!")
        return True

def main():
    """Run all end-to-end tests"""
    print("🧪 Running End-to-End Traffic Light Tests\n")
    
    tests = [
        test_fixed_timer_simulation,
        test_adaptive_simulation,
        test_xml_validity
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
        print("🎉 All end-to-end tests passed! Traffic light implementation is fully functional.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
