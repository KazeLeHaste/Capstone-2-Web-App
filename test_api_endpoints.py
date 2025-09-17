#!/usr/bin/env python3
"""
Test the backend API endpoints with compressed networks
"""

from backend.app import app
import json

def test_api_endpoints():
    print("🧪 Testing backend API endpoints...")
    
    with app.test_client() as client:
        # Test networks endpoint
        response = client.get('/api/networks')
        data = response.get_json()
        
        print(f"API Response Status: {response.status_code}")
        print(f"Networks found: {data.get('count', 0)}")
        
        if data.get('networks'):
            network = data['networks'][0]
            print(f"Network ID: {network['id']}")
            print(f"Network Path: {network['path']}")
            print(f"Is compressed: {network['path'].endswith('.gz')}")
            print(f"OSM Scenario: {network['isOsmScenario']}")
            
            # Test session setup endpoint
            session_data = {
                'sessionId': 'api_test_session',
                'networkId': network['id'],
                'networkPath': network['path'],
                'config': {
                    'vehicles': 5,
                    'simulationTime': 120,
                    'enabledVehicles': ['passenger']
                }
            }
            
            response = client.post('/api/simulation/setup-network', 
                                 data=json.dumps(session_data),
                                 content_type='application/json')
            
            setup_data = response.get_json()
            print(f"\nSession setup status: {response.status_code}")
            print(f"Setup success: {setup_data.get('success', False)}")
            
            if setup_data.get('success'):
                print("✅ API endpoints working correctly with compressed networks!")
            else:
                print(f"❌ Session setup failed: {setup_data.get('error')}")
        else:
            print("❌ No networks found in API response")

if __name__ == "__main__":
    test_api_endpoints()