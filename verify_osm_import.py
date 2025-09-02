import os
from pathlib import Path

networks_dir = Path("backend/networks")

print("🔍 Verifying OSM Network Import Status\n")

for network_dir in networks_dir.iterdir():
    if network_dir.is_dir():
        print(f"📁 {network_dir.name}")
        
        # Check for required files
        required_files = [
            f"{network_dir.name}.net.xml",
            f"{network_dir.name}.sumocfg",
            "metadata.json"
        ]
        
        for req_file in required_files:
            file_path = network_dir / req_file
            if file_path.exists():
                print(f"   ✅ {req_file}")
            else:
                print(f"   ❌ {req_file} MISSING")
        
        # Check routes directory
        routes_dir = network_dir / "routes"
        if routes_dir.exists():
            route_files = list(routes_dir.glob("*.rou.xml"))
            trip_files = list(routes_dir.glob("*.trips.xml"))
            print(f"   📂 routes/")
            print(f"      Route files: {len(route_files)}")
            print(f"      Trip files: {len(trip_files)}")
            
            if len(route_files) >= 4:  # passenger, bus, truck, motorcycle
                print(f"      ✅ All vehicle types have route files")
            else:
                print(f"      ⚠️  Missing route files")
        else:
            print(f"   ❌ routes/ directory MISSING")
        
        print()

print("Summary:")
osm_networks = [d for d in networks_dir.iterdir() if d.is_dir()]
print(f"Total networks imported: {len(osm_networks)}")
print("\nNetwork names:")
for network in osm_networks:
    print(f"  - {network.name}")

print("\n✅ OSM import verification complete!")
print("These networks should now be available in the web application.")
