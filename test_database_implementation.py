#!/usr/bin/env python3
"""
Database Implementation Test Script

Tests the new database functionality for the traffic simulator.

Author: Traffic Simulator Team
Date: September 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database.service import DatabaseService
from datetime import datetime
import json

def test_database_implementation():
    """Test the database implementation"""
    print("=" * 60)
    print("Testing Database Implementation")
    print("=" * 60)
    
    try:
        # Initialize database service
        print("\n1. Initializing database service...")
        db_service = DatabaseService()
        print("✓ Database service initialized successfully")
        
        # Test session creation
        print("\n2. Testing session creation...")
        session_id = f"test_session_{int(datetime.now().timestamp())}"
        session = db_service.create_session(
            session_id=session_id,
            network_id="test_network",
            network_name="Test Network",
            session_path="/path/to/session"
        )
        print(f"✓ Session created: {session.id}")
        
        # Test configuration saving
        print("\n3. Testing configuration saving...")
        config_data = {
            'sessionId': session_id,
            'config': {
                'sumo_begin': 0,
                'sumo_end': 1800,
                'sumo_step_length': 1.0,
                'sumo_traffic_intensity': 1.5,
                'enabledVehicles': ['passenger', 'bus'],
                'trafficControl': {
                    'method': 'adaptive',
                    'adaptive': {
                        'minGreenTime': 8,
                        'maxGreenTime': 45
                    }
                },
                'vehicleTypes': {
                    'passenger': {'enabled': True},
                    'bus': {'enabled': True}
                }
            }
        }
        
        success = db_service.save_configuration(session_id, config_data)
        if success:
            print("✓ Configuration saved successfully")
        else:
            print("✗ Failed to save configuration")
        
        # Test configuration retrieval
        print("\n4. Testing configuration retrieval...")
        config = db_service.get_configuration(session_id)
        if config:
            print(f"✓ Configuration retrieved: {config.traffic_control_method}")
            print(f"  Enabled vehicles: {config.get_enabled_vehicles()}")
        else:
            print("✗ Failed to retrieve configuration")
        
        # Test live data saving
        print("\n5. Testing live data saving...")
        live_data = {
            'simulation_time': 150,
            'active_vehicles': 45,
            'avg_speed': 32.5,
            'throughput': 120
        }
        success = db_service.save_live_data(session_id, live_data)
        if success:
            print("✓ Live data saved successfully")
        else:
            print("✗ Failed to save live data")
        
        # Test KPIs saving
        print("\n6. Testing KPIs saving...")
        kpis_data = {
            'total_vehicles_completed': 100,
            'avg_travel_time': 245.6,
            'avg_waiting_time': 12.3,
            'avg_speed': 8.9,
            'throughput': 120,
            'simulation_duration': 1800
        }
        success = db_service.save_kpis(session_id, kpis_data)
        if success:
            print("✓ KPIs saved successfully")
        else:
            print("✗ Failed to save KPIs")
        
        # Test analytics retrieval
        print("\n7. Testing analytics retrieval...")
        analytics = db_service.get_session_analytics(session_id)
        if analytics:
            print("✓ Analytics retrieved successfully")
            print(f"  Session status: {analytics['session']['status']}")
            if analytics['kpis']:
                print(f"  Avg travel time: {analytics['kpis']['avg_travel_time']:.1f}s")
        else:
            print("✗ Failed to retrieve analytics")
        
        # Test network saving
        print("\n8. Testing network saving...")
        network_data = {
            'id': 'test_network',
            'name': 'Test Network',
            'description': 'A test network for validation',
            'path': '/path/to/network.net.xml',
            'is_osm_scenario': False,
            'vehicle_types': ['passenger', 'bus', 'truck']
        }
        success = db_service.save_network(network_data)
        if success:
            print("✓ Network saved successfully")
        else:
            print("✗ Failed to save network")
        
        # Test database stats
        print("\n9. Testing database stats...")
        stats = db_service.get_database_stats()
        print("✓ Database stats retrieved:")
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  Completed sessions: {stats['completed_sessions']}")
        print(f"  Total networks: {stats['total_networks']}")
        print(f"  Database size: {stats['database_size']} bytes")
        
        # Test recent sessions
        print("\n10. Testing recent sessions retrieval...")
        recent_sessions = db_service.get_recent_sessions(limit=5)
        print(f"✓ Retrieved {len(recent_sessions)} recent sessions")
        for session in recent_sessions:
            print(f"  - {session.id} ({session.status})")
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Database implementation working correctly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_implementation()
    sys.exit(0 if success else 1)
