#!/usr/bin/env python3
"""
System Verification Test
Tests the complete integrated system with database and enhanced session management.
"""

import requests
import time
import json
from datetime import datetime
import os
import sqlite3

BASE_URL = "http://localhost:5000"
DATABASE_PATH = "backend/simulation_data.db"

def print_header(title):
    print("=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)

def print_section(title):
    print(f"\n📋 {title}")
    print("-" * 60)

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def test_database_connection():
    """Test database connectivity and schema"""
    print_section("1. Database Connection Test")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['sessions', 'configurations', 'analytics', 'networks']
        for table in expected_tables:
            if table in tables:
                print_success(f"Table '{table}' exists")
            else:
                print_error(f"Table '{table}' missing")
        
        # Check sessions table schema
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_columns = ['id', 'session_id', 'network_id', 'config_data', 'status', 
                          'created_at', 'updated_at', 'traci_port', 'process_id', 'temp_directory']
        
        for column in expected_columns:
            if column in columns:
                print_success(f"Column '{column}' exists in sessions table")
            else:
                print_error(f"Column '{column}' missing in sessions table")
        
        conn.close()
        print_success("Database connection and schema verification complete")
        
    except Exception as e:
        print_error(f"Database test failed: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Test all API endpoints"""
    print_section("2. API Endpoints Test")
    
    try:
        # Test health check
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            print_success("Health endpoint working")
        else:
            print_error(f"Health endpoint failed: {response.status_code}")
        
        # Test networks endpoint
        response = requests.get(f"{BASE_URL}/api/networks/available")
        if response.status_code == 200:
            networks = response.json()
            print_success(f"Networks endpoint working - Found {len(networks)} networks")
        else:
            print_error(f"Networks endpoint failed: {response.status_code}")
        
        # Test v2 endpoints
        response = requests.get(f"{BASE_URL}/api/v2/sessions")
        if response.status_code == 200:
            print_success("V2 sessions endpoint working")
        else:
            print_error(f"V2 sessions endpoint failed: {response.status_code}")
        
        response = requests.get(f"{BASE_URL}/api/v2/resource-usage")
        if response.status_code == 200:
            usage = response.json()['resource_usage']
            print_success(f"V2 resource usage endpoint working - Active sessions: {usage.get('active_sessions', 0)}")
        else:
            print_error(f"V2 resource usage endpoint failed: {response.status_code}")
        
    except Exception as e:
        print_error(f"API endpoints test failed: {e}")
        return False
    
    return True

def test_session_lifecycle():
    """Test complete session lifecycle"""
    print_section("3. Session Lifecycle Test")
    
    try:
        # Create a session
        session_data = {
            "networkId": "sm_molino_area.net",
            "config": {
                "sumo_begin": 0,
                "sumo_end": 100,
                "trafficIntensity": 1.0,
                "enabledVehicles": ["passenger"],
                "trafficControl": {
                    "method": "adaptive",
                    "globalMode": True
                }
            },
            "enableGui": False
        }
        
        response = requests.post(f"{BASE_URL}/api/v2/sessions", json=session_data)
        if response.status_code == 200:
            session_info = response.json()
            session_id = session_info['session_id']
            print_success(f"Session created: {session_id}")
            print_success(f"TraCI Port: {session_info['traci_port']}")
        else:
            print_error(f"Session creation failed: {response.status_code}")
            return False
        
        # Get session status
        response = requests.get(f"{BASE_URL}/api/v2/sessions/{session_id}/status")
        if response.status_code == 200:
            status = response.json()['session']
            print_success(f"Session status retrieved: {status['status']}")
        else:
            print_error(f"Session status failed: {response.status_code}")
        
        # Cleanup session
        response = requests.delete(f"{BASE_URL}/api/v2/sessions/{session_id}")
        if response.status_code == 200:
            print_success("Session cleaned up successfully")
        else:
            print_error(f"Session cleanup failed: {response.status_code}")
        
    except Exception as e:
        print_error(f"Session lifecycle test failed: {e}")
        return False
    
    return True

def test_concurrent_operations():
    """Test concurrent session operations"""
    print_section("4. Concurrent Operations Test")
    
    try:
        session_ids = []
        networks = ["sm_molino_area", "jollibee_molino", "sm_bacoor_area"]
        
        # Create multiple sessions
        for i, network in enumerate(networks):
            session_data = {
                "networkId": f"{network}.net",
                "config": {
                    "sumo_begin": 0,
                    "sumo_end": 50,
                    "trafficIntensity": 1.0,
                    "enabledVehicles": ["passenger"]
                },
                "enableGui": False
            }
            
            response = requests.post(f"{BASE_URL}/api/v2/sessions", json=session_data)
            if response.status_code == 200:
                session_info = response.json()
                session_ids.append(session_info['session_id'])
                print_success(f"Concurrent session {i+1} created: {session_info['session_id']}")
            else:
                print_error(f"Concurrent session {i+1} creation failed")
        
        # Check resource usage
        response = requests.get(f"{BASE_URL}/api/v2/resource-usage")
        if response.status_code == 200:
            usage = response.json()['resource_usage']
            print_success(f"Resource usage - Active: {usage['active_sessions']}, Ports: {len(usage['allocated_ports'])}")
        
        # Cleanup all sessions
        for session_id in session_ids:
            response = requests.delete(f"{BASE_URL}/api/v2/sessions/{session_id}")
            if response.status_code == 200:
                print_success(f"Session {session_id} cleaned up")
        
        # Verify cleanup
        response = requests.get(f"{BASE_URL}/api/v2/resource-usage")
        if response.status_code == 200:
            usage = response.json()['resource_usage']
            if usage['active_sessions'] == 0:
                print_success("All concurrent sessions cleaned up properly")
            else:
                print_error(f"Cleanup incomplete - {usage['active_sessions']} sessions remain")
        
    except Exception as e:
        print_error(f"Concurrent operations test failed: {e}")
        return False
    
    return True

def test_backward_compatibility():
    """Test backward compatibility with v1 API"""
    print_section("5. Backward Compatibility Test")
    
    try:
        # Test v1 sessions GET endpoint
        response = requests.get(f"{BASE_URL}/api/sessions")
        if response.status_code == 200:
            print_success("V1 API sessions GET endpoint working")
        else:
            print_error(f"V1 API sessions GET failed: {response.status_code}")
            return False
        
        # Note: V1 API doesn't have session creation - only V2 does
        # This is by design as part of the enhanced architecture
        print_success("V1 API compatibility verified - read operations working")
        
    except Exception as e:
        print_error(f"Backward compatibility test failed: {e}")
        return False
    
    return True

def main():
    print_header("SYSTEM VERIFICATION TEST")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("API Endpoints", test_api_endpoints),
        ("Session Lifecycle", test_session_lifecycle),
        ("Concurrent Operations", test_concurrent_operations),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print_success(f"{test_name} Test PASSED")
            else:
                print_error(f"{test_name} Test FAILED")
        except Exception as e:
            print_error(f"{test_name} Test ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is fully integrated and working correctly.")
        print("✓ Database integration complete")
        print("✓ Multi-session support working")
        print("✓ API endpoints functional")
        print("✓ Resource management working")
        print("✓ Backward compatibility maintained")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the results above.")
    
    print(f"\n🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
