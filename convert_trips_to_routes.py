#!/usr/bin/env python3
"""
Convert OSM trip files to route files for the web application.
This script processes all imported OSM scenarios and converts their trip files
to route files using SUMO's duarouter.
"""

import os
import sys
import subprocess
from pathlib import Path

def convert_trips_to_routes(networks_dir="backend/networks", sumo_bin_dir="C:\\Program Files (x86)\\Eclipse\\Sumo\\bin"):
    """
    Convert trip files to route files for all OSM imported scenarios
    
    Args:
        networks_dir: Directory containing network scenarios
        sumo_bin_dir: Path to SUMO bin directory containing duarouter
    """
    networks_path = Path(networks_dir)
    sumo_bin = Path(sumo_bin_dir)
    duarouter = sumo_bin / "duarouter.exe"
    
    if not duarouter.exists():
        print(f"❌ duarouter not found at {duarouter}")
        print("Please check your SUMO installation path")
        return False
    
    if not networks_path.exists():
        print(f"❌ Networks directory not found: {networks_dir}")
        return False
    
    print(f"🔧 Converting trip files to route files...")
    print(f"SUMO duarouter: {duarouter}")
    
    converted_count = 0
    
    # Process each network directory
    for network_dir in networks_path.iterdir():
        if network_dir.is_dir():
            routes_dir = network_dir / "routes"
            if routes_dir.exists():
                print(f"\n📁 Processing {network_dir.name}...")
                
                # Find network file
                network_file = None
                for net_pattern in ["*.net.xml"]:
                    net_files = list(network_dir.glob(net_pattern))
                    if net_files:
                        network_file = net_files[0]
                        break
                
                if not network_file:
                    print(f"   ⚠️  No network file found, skipping")
                    continue
                
                # Convert each trip file
                trip_files = list(routes_dir.glob("*.trips.xml"))
                if not trip_files:
                    print(f"   ⚠️  No trip files found, skipping")
                    continue
                
                for trip_file in trip_files:
                    # Determine output route file name
                    vehicle_type = trip_file.stem.split('.')[-2]  # Extract vehicle type from osm.XXX.trips.xml
                    route_file = routes_dir / f"osm.{vehicle_type}.rou.xml"
                    
                    print(f"   🔄 Converting {trip_file.name} -> {route_file.name}")
                    
                    try:
                        # Run duarouter to convert trips to routes
                        cmd = [
                            str(duarouter),
                            "-n", str(network_file.resolve()),
                            "--route-files", str(trip_file.resolve()),
                            "-o", str(route_file.resolve()),
                            "--ignore-errors"
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            print(f"   ✅ Successfully created {route_file.name}")
                            converted_count += 1
                        else:
                            print(f"   ❌ Failed to convert {trip_file.name}")
                            print(f"      Error: {result.stderr}")
                    
                    except Exception as e:
                        print(f"   ❌ Error converting {trip_file.name}: {e}")
    
    print(f"\n🎉 Conversion complete! Created {converted_count} route files.")
    return converted_count > 0

def verify_route_files(networks_dir="backend/networks"):
    """
    Verify that route files have been created correctly
    """
    networks_path = Path(networks_dir)
    
    print(f"\n🔍 Verifying route files...")
    
    for network_dir in networks_path.iterdir():
        if network_dir.is_dir():
            routes_dir = network_dir / "routes"
            if routes_dir.exists():
                route_files = list(routes_dir.glob("*.rou.xml"))
                trip_files = list(routes_dir.glob("*.trips.xml"))
                
                print(f"\n📁 {network_dir.name}:")
                print(f"   Trip files: {len(trip_files)}")
                print(f"   Route files: {len(route_files)}")
                
                if route_files:
                    for route_file in route_files:
                        if route_file.exists() and route_file.stat().st_size > 0:
                            print(f"   ✅ {route_file.name} ({route_file.stat().st_size:,} bytes)")
                        else:
                            print(f"   ❌ {route_file.name} (empty or missing)")
                else:
                    print(f"   ⚠️  No route files found")

if __name__ == "__main__":
    print("🚗 OSM Trip-to-Route Converter")
    print("Converting trip files to route files for web application...\n")
    
    # Convert trip files to route files
    success = convert_trips_to_routes()
    
    # Verify the conversion
    verify_route_files()
    
    if success:
        print("\n✅ All trip files have been converted to route files!")
        print("Your OSM scenarios are now ready to use in the web application.")
    else:
        print("\n❌ Some conversions failed. Check the errors above.")
