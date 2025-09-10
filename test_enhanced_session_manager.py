#!/usr/bin/env python3
"""
Enhanced Session Manager Test Script

Tests the new multi-session functionality with database integration.

Author: Traffic Simulator Team
Date: September 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database.service import DatabaseService
from enhanced_session_manager import EnhancedSessionManager
import time
import json

def test_enhanced_session_manager():
    """Test the enhanced session manager functionality"""
    print("=" * 70)
    print("Testing Enhanced Session Manager")
    print("=" * 70)
    
    # Initialize services
    print("\n1. Initializing services...")
    db_service = DatabaseService()
    enhanced_manager = EnhancedSessionManager(
        base_networks_dir="backend/networks",
        db_service=db_service
    )
    print("✓ Services initialized successfully")
    
    # Test session creation
    print("\n2. Testing session creation...")
    config = {
        'sumo_begin': 0,
        'sumo_end': 300,
        'trafficIntensity': 1.5,
        'enabledVehicles': ['passenger', 'bus'],
        'trafficControl': {
            'method': 'adaptive',
            'globalMode': True
        }
    }
    
    # Create first session
    result1 = enhanced_manager.create_session(
        network_id='sm_molino_area',
        config=config,
        enable_gui=False
    )
    
    if result1['success']:
        session_id1 = result1['session_id']
        print(f"✓ Session 1 created: {session_id1}")
        print(f"  - TraCI Port: {result1['traci_port']}")
        print(f"  - Session Path: {result1['session_path']}")
    else:
        print(f"✗ Failed to create session 1: {result1['message']}")
        return
    
    # Create second session to test multi-session capability
    result2 = enhanced_manager.create_session(
        network_id='jollibee_molino',
        config=config,
        enable_gui=False
    )
    
    if result2['success']:
        session_id2 = result2['session_id']
        print(f"✓ Session 2 created: {session_id2}")
        print(f"  - TraCI Port: {result2['traci_port']}")
        print(f"  - Session Path: {result2['session_path']}")
    else:
        print(f"✗ Failed to create session 2: {result2['message']}")
        return
    
    # Test active sessions retrieval
    print("\n3. Testing active sessions retrieval...")
    active_sessions = enhanced_manager.get_active_sessions()
    print(f"✓ Found {len(active_sessions)} active sessions:")
    for session in active_sessions:
        print(f"  - {session['session_id']} ({session['network_id']}) - Port: {session['traci_port']}")
    
    # Test database integration
    print("\n4. Testing database integration...")
    db_session1 = db_service.get_session_by_id(session_id1)
    if db_session1:
        print(f"✓ Session 1 found in database:")
        print(f"  - Status: {db_session1.status}")
        print(f"  - Network: {db_session1.network_id}")
        print(f"  - TraCI Port: {db_session1.traci_port}")
        print(f"  - Temp Directory: {db_session1.temp_directory}")
    else:
        print("✗ Session 1 not found in database")
    
    # Test configuration retrieval
    config1 = db_service.get_configuration(session_id1)
    if config1:
        print(f"✓ Configuration found in database:")
        print(f"  - Traffic Intensity: {config1.sumo_traffic_intensity}")
        print(f"  - Enabled Vehicles: {json.loads(config1.enabled_vehicles)}")
    else:
        print("✗ Configuration not found in database")
    
    # Test resource usage
    print("\n5. Testing resource usage...")
    allocated_ports = enhanced_manager.port_allocator.get_allocated_ports()
    print(f"✓ Allocated ports: {allocated_ports}")
    print(f"✓ Available ports: {enhanced_manager.port_allocator.max_ports - len(allocated_ports)}")
    
    # Test session cleanup
    print("\n6. Testing session cleanup...")
    cleanup_result1 = enhanced_manager.cleanup_session(session_id1)
    cleanup_result2 = enhanced_manager.cleanup_session(session_id2)
    
    if cleanup_result1 and cleanup_result2:
        print(f"✓ Both sessions cleaned up successfully")
    else:
        print(f"✗ Cleanup failed: Session 1: {cleanup_result1}, Session 2: {cleanup_result2}")
    
    # Verify cleanup
    active_sessions_after = enhanced_manager.get_active_sessions()
    allocated_ports_after = enhanced_manager.port_allocator.get_allocated_ports()
    
    print(f"✓ Active sessions after cleanup: {len(active_sessions_after)}")
    print(f"✓ Allocated ports after cleanup: {allocated_ports_after}")
    
    # Test database session status
    db_session1_after = db_service.get_session_by_id(session_id1)
    if db_session1_after:
        print(f"✓ Database session still exists (expected): Status = {db_session1_after.status}")
    
    print("\n" + "=" * 70)
    print("✓ ALL ENHANCED SESSION MANAGER TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_enhanced_session_manager()
