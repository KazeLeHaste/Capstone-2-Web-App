"""
Quick test script to verify OSM Web Wizard launch functionality
"""
import sys
import requests
import time

def test_osm_launch():
    """Test launching OSM Web Wizard via API"""
    
    # Wait for app to be ready
    print("Waiting for app to start...")
    time.sleep(3)
    
    # Test the launch endpoint
    print("\nTesting OSM Web Wizard launch...")
    try:
        response = requests.post('http://localhost:5000/api/osm/launch-wizard', timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("\n✓ SUCCESS: OSM Web Wizard launched successfully!")
                print(f"  URL: {result.get('url')}")
                print(f"  Port: {result.get('port')}")
                if result.get('already_running'):
                    print("  (Already running)")
                else:
                    print(f"  Process ID: {result.get('process_id')}")
                return True
            else:
                print(f"\n✗ FAILED: {result.get('error')}")
                print(f"  Details: {result.get('details')}")
                return False
        else:
            print(f"\n✗ HTTP Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Connection Error: {e}")
        return False

if __name__ == '__main__':
    success = test_osm_launch()
    sys.exit(0 if success else 1)
