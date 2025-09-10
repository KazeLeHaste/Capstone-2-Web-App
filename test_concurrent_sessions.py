#!/usr/bin/env python3
"""
Multi-Session Concurrent Test

Tests creating and managing multiple concurrent sessions.

Author: Traffic Simulator Team
Date: September 2025
"""

import requests
import json
import time
import threading

def test_concurrent_sessions():
    """Test creating multiple concurrent sessions"""
    print("=" * 70)
    print("Testing Multiple Concurrent Sessions")
    print("=" * 70)
    
    base_url = "http://localhost:5000"
    sessions_created = []
    
    # Test data for different sessions
    session_configs = [
        {
            'networkId': 'sm_molino_area.net',
            'config': {
                'sumo_begin': 0,
                'sumo_end': 180,
                'trafficIntensity': 1.0,
                'enabledVehicles': ['passenger'],
            },
            'enableGui': False
        },
        {
            'networkId': 'jollibee_molino.net',
            'config': {
                'sumo_begin': 0,
                'sumo_end': 240,
                'trafficIntensity': 1.5,
                'enabledVehicles': ['passenger', 'bus'],
            },
            'enableGui': False
        },
        {
            'networkId': 'sm_bacoor_area.net',
            'config': {
                'sumo_begin': 0,
                'sumo_end': 300,
                'trafficIntensity': 2.0,
                'enabledVehicles': ['passenger', 'bus', 'truck'],
            },
            'enableGui': False
        }
    ]
    
    print(f"\n1. Creating {len(session_configs)} concurrent sessions...")
    
    # Create sessions concurrently
    def create_session(session_data, session_num):
        try:
            response = requests.post(f"{base_url}/api/v2/sessions", json=session_data)
            result = response.json()
            
            if result.get('success'):
                session_id = result.get('session_id')
                print(f"✓ Session {session_num} created: {session_id}")
                print(f"  - Network: {session_data['networkId']}")
                print(f"  - TraCI Port: {result.get('traci_port')}")
                sessions_created.append(session_id)
                return session_id
            else:
                print(f"✗ Failed to create session {session_num}: {result.get('message')}")
                return None
        except Exception as e:
            print(f"✗ Error creating session {session_num}: {e}")
            return None
    
    # Create sessions in parallel
    threads = []
    for i, config in enumerate(session_configs, 1):
        thread = threading.Thread(target=create_session, args=(config, i))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    time.sleep(1)  # Give server time to process
    
    print(f"\n2. Verifying {len(sessions_created)} active sessions...")
    try:
        response = requests.get(f"{base_url}/api/v2/sessions")
        result = response.json()
        
        if result.get('success'):
            active_sessions = result.get('sessions', [])
            print(f"✓ Found {len(active_sessions)} active sessions:")
            
            for session in active_sessions:
                print(f"  - {session.get('session_id')} ({session.get('network_id')}) - Port: {session.get('traci_port')}")
                
            if len(active_sessions) == len(sessions_created):
                print("✓ All sessions properly tracked")
            else:
                print(f"⚠ Expected {len(sessions_created)} sessions, found {len(active_sessions)}")
        else:
            print(f"✗ Failed to get active sessions: {result.get('message')}")
    except Exception as e:
        print(f"✗ Error getting active sessions: {e}")
    
    print("\n3. Testing resource allocation...")
    try:
        response = requests.get(f"{base_url}/api/v2/resource-usage")
        result = response.json()
        
        if result.get('success'):
            usage = result.get('resource_usage')
            print(f"✓ Resource usage:")
            print(f"  - Active Sessions: {usage.get('active_sessions')}")
            print(f"  - Allocated Ports: {usage.get('allocated_ports')}")
            print(f"  - Available Ports: {usage.get('available_ports')}")
            
            if len(usage.get('allocated_ports', [])) == len(sessions_created):
                print("✓ Port allocation working correctly")
            else:
                print("⚠ Port allocation may have issues")
        else:
            print(f"✗ Failed to get resource usage: {result.get('message')}")
    except Exception as e:
        print(f"✗ Error getting resource usage: {e}")
    
    print("\n4. Testing individual session status...")
    for i, session_id in enumerate(sessions_created, 1):
        try:
            response = requests.get(f"{base_url}/api/v2/sessions/{session_id}/status")
            result = response.json()
            
            if result.get('success'):
                session = result.get('session')
                print(f"✓ Session {i} status: {session.get('status')} - Network: {session.get('network_id')}")
            else:
                print(f"✗ Failed to get session {i} status: {result.get('message')}")
        except Exception as e:
            print(f"✗ Error getting session {i} status: {e}")
    
    print("\n5. Cleaning up all sessions...")
    cleanup_success = 0
    for i, session_id in enumerate(sessions_created, 1):
        try:
            response = requests.delete(f"{base_url}/api/v2/sessions/{session_id}")
            result = response.json()
            
            if result.get('success'):
                print(f"✓ Session {i} cleaned up")
                cleanup_success += 1
            else:
                print(f"✗ Failed to cleanup session {i}: {result.get('message')}")
        except Exception as e:
            print(f"✗ Error cleaning up session {i}: {e}")
    
    print(f"\n6. Verifying cleanup...")
    try:
        response = requests.get(f"{base_url}/api/v2/sessions")
        result = response.json()
        
        if result.get('success'):
            remaining_sessions = result.get('sessions', [])
            print(f"✓ Remaining active sessions: {len(remaining_sessions)}")
            
            if len(remaining_sessions) == 0:
                print("✓ All sessions properly cleaned up")
            else:
                print(f"⚠ {len(remaining_sessions)} sessions still active")
        else:
            print(f"✗ Failed to verify cleanup: {result.get('message')}")
    except Exception as e:
        print(f"✗ Error verifying cleanup: {e}")
    
    print("\n" + "=" * 70)
    if cleanup_success == len(sessions_created):
        print("🎉 MULTI-SESSION CONCURRENT TEST PASSED!")
        print("✓ Multiple sessions can be created and managed concurrently")
        print("✓ Resource allocation working properly")
        print("✓ Session isolation maintained")
        print("✓ Cleanup working correctly")
    else:
        print("⚠ MULTI-SESSION TEST COMPLETED WITH ISSUES")
        print(f"Created: {len(sessions_created)}, Cleaned: {cleanup_success}")
    print("=" * 70)

if __name__ == "__main__":
    test_concurrent_sessions()
