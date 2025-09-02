import requests
import json

try:
    response = requests.get('http://localhost:5000/api/networks/available')
    networks = response.json()
    
    print(f"Found {len(networks)} networks:")
    for network in networks:
        print(f"- {network['name']} ({network['id']})")
        if 'osm' in network.get('type', ''):
            print(f"  Type: OSM imported scenario")
        print(f"  Edges: {network.get('network_info', {}).get('edges', 'N/A')}")
        
except Exception as e:
    print(f"Error: {e}")
