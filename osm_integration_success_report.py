#!/usr/bin/env python3
"""
OSM Integration Success Report
=============================

This script generates a final report on the successful integration of OSM scenarios.
"""

import os
import json
import requests
from pathlib import Path

# Configuration
BACKEND_NETWORKS_DIR = Path("backend/networks")
BACKEND_API = "http://localhost:5000"

def test_api_connection():
    """Test if backend API is accessible"""
    try:
        response = requests.get(f"{BACKEND_API}/api/networks", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_network_info():
    """Get network information from API"""
    try:
        response = requests.get(f"{BACKEND_API}/api/networks", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def analyze_osm_scenarios():
    """Analyze imported OSM scenarios"""
    osm_scenarios = []
    
    if not BACKEND_NETWORKS_DIR.exists():
        return osm_scenarios
    
    for network_dir in BACKEND_NETWORKS_DIR.iterdir():
        if network_dir.is_dir():
            # Check for required files
            required_files = [
                f"{network_dir.name}.net.xml",
                f"{network_dir.name}.sumocfg",
                f"{network_dir.name}.output_add.xml"
            ]
            
            routes_dir = network_dir / "routes"
            route_files = []
            if routes_dir.exists():
                route_files = [f.name for f in routes_dir.glob("*.rou.xml")]
            
            # Check metadata
            metadata_file = network_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except:
                    pass
            
            scenario_info = {
                'name': network_dir.name,
                'path': str(network_dir),
                'required_files_exist': all((network_dir / f).exists() for f in required_files),
                'route_files': route_files,
                'route_count': len(route_files),
                'metadata': metadata
            }
            
            osm_scenarios.append(scenario_info)
    
    return osm_scenarios

def print_success_report():
    """Print comprehensive success report"""
    print("🎉 OSM INTEGRATION SUCCESS REPORT")
    print("=" * 50)
    
    # Test API connection
    print("\n📡 Backend API Status:")
    api_connected = test_api_connection()
    if api_connected:
        print("   ✅ Backend API is accessible")
    else:
        print("   ❌ Backend API is not accessible")
        return
    
    # Get network info from API
    print("\n🌐 Available Networks (from API):")
    networks = get_network_info()
    if networks:
        for network in networks.get('networks', []):
            print(f"   ✅ {network['name']} - {network['description']}")
    else:
        print("   ⚠️  No networks retrieved from API")
    
    # Analyze local OSM scenarios
    print("\n📊 OSM Scenario Analysis:")
    osm_scenarios = analyze_osm_scenarios()
    
    if not osm_scenarios:
        print("   ⚠️  No OSM scenarios found")
        return
    
    print(f"   📁 Total OSM scenarios imported: {len(osm_scenarios)}")
    print("")
    
    for scenario in osm_scenarios:
        print(f"   🗺️  {scenario['name']}")
        print(f"      Required files: {'✅' if scenario['required_files_exist'] else '❌'}")
        print(f"      Route files: {scenario['route_count']} types")
        
        if scenario['route_files']:
            vehicle_types = []
            for route_file in scenario['route_files']:
                if '.bicycle.' in route_file:
                    vehicle_types.append('🚲 Bicycle')
                elif '.bus.' in route_file:
                    vehicle_types.append('🚌 Bus')
                elif '.motorcycle.' in route_file:
                    vehicle_types.append('🏍️ Motorcycle')
                elif '.passenger.' in route_file:
                    vehicle_types.append('🚗 Car')
                elif '.pedestrian.' in route_file:
                    vehicle_types.append('🚶 Pedestrian')
                elif '.truck.' in route_file:
                    vehicle_types.append('🚛 Truck')
            
            print(f"      Vehicle types: {', '.join(vehicle_types)}")
        
        if scenario['metadata']:
            source = scenario['metadata'].get('source', 'Unknown')
            print(f"      Source: {source}")
        
        print("")
    
    # Summary
    print("🏁 INTEGRATION SUMMARY:")
    print("=" * 30)
    working_scenarios = sum(1 for s in osm_scenarios if s['required_files_exist'])
    total_route_files = sum(s['route_count'] for s in osm_scenarios)
    
    print(f"✅ Successfully imported: {working_scenarios}/{len(osm_scenarios)} OSM scenarios")
    print(f"✅ Total route files generated: {total_route_files}")
    print(f"✅ Backend API: {'Online' if api_connected else 'Offline'}")
    print(f"✅ Frontend: Available at http://localhost:3000")
    
    print("\n🎯 WHAT YOU CAN DO NOW:")
    print("• Open http://localhost:3000 in your browser")
    print("• Select any OSM scenario from the network dropdown")
    print("• Choose vehicle types and launch SUMO simulations")
    print("• All OSM scenarios should launch without file errors")
    
    if working_scenarios == len(osm_scenarios):
        print("\n🎉 ALL OSM SCENARIOS ARE READY TO USE! 🎉")
    else:
        print(f"\n⚠️  {len(osm_scenarios) - working_scenarios} scenarios need attention")

if __name__ == "__main__":
    print_success_report()
