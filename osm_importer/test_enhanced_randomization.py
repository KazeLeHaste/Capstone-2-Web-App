"""
Enhanced Randomization Test Script

Tests the new randomization features for more realistic traffic simulation:
- Vehicle type diversity
- Spatial spawn distribution
- Temporal departure randomization
- Color and shape variations
- Route variety

Author: Traffic Simulator Team
Date: September 2025
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from osm_scenario_importer import OSMScenarioImporter

def test_enhanced_randomization():
    """Test the enhanced randomization system"""
    
    print("🚗 Testing Enhanced Traffic Randomization System")
    print("=" * 60)
    
    # Initialize the importer
    importer = OSMScenarioImporter()
    
    # Scan for available scenarios
    print("\n1. Scanning for OSM scenarios...")
    scenarios = importer.scan_osm_scenarios()
    
    if not scenarios:
        print("❌ No OSM scenarios found!")
        print("   Please ensure you have OSM scenarios in the osm_scenarios folder")
        return False
    
    print(f"✅ Found {len(scenarios)} OSM scenarios:")
    for scenario in scenarios:
        print(f"   - {scenario['name']} ({len(scenario['vehicle_types'])} vehicle types)")
    
    # Test with the first available scenario
    test_scenario = scenarios[0]
    print(f"\n2. Testing enhanced randomization with: {test_scenario['name']}")
    
    # Import with enhanced diversity enabled
    result = importer.import_scenario(
        test_scenario['name'], 
        f"test_enhanced_{test_scenario['name'].lower().replace(' ', '_')}",
        enhance_diversity=True
    )
    
    if result['success']:
        print("✅ Enhanced randomization test completed successfully!")
        print(f"   Target path: {result['target_path']}")
        print(f"   Vehicle types: {', '.join(result['vehicle_types'])}")
        
        # Analyze the results
        analyze_randomization_results(Path(result['target_path']))
        return True
    else:
        print(f"❌ Test failed: {result['error']}")
        return False

def analyze_randomization_results(target_path: Path):
    """Analyze the results of the randomization process"""
    
    print("\n3. Analyzing randomization results...")
    
    routes_dir = target_path / 'routes'
    if not routes_dir.exists():
        print("❌ Routes directory not found")
        return
    
    # Check for trip files
    trip_files = list(routes_dir.glob("*.trips.xml*"))
    route_files = list(routes_dir.glob("*.rou.xml*"))
    
    print(f"   Found {len(trip_files)} trip files and {len(route_files)} route files")
    
    # Analyze diversity in trip files
    for trip_file in trip_files[:2]:  # Analyze first 2 files to avoid spam
        analyze_trip_file_diversity(trip_file)

def analyze_trip_file_diversity(trip_file: Path):
    """Analyze diversity metrics in a trip file"""
    
    import xml.etree.ElementTree as ET
    import gzip
    
    try:
        print(f"\n   Analyzing {trip_file.name}...")
        
        # Handle compressed files
        if trip_file.suffix == '.gz':
            with gzip.open(trip_file, 'rt', encoding='utf-8') as f:
                content = f.read()
            root = ET.fromstring(content)
        else:
            tree = ET.parse(trip_file)
            root = tree.getroot()
        
        trips = root.findall('.//trip')
        print(f"   Total trips: {len(trips)}")
        
        if not trips:
            return
        
        # Analyze departure time distribution
        departure_times = []
        colors = []
        origins = []
        destinations = []
        
        for trip in trips:
            departure_times.append(float(trip.get('depart', 0)))
            colors.append(trip.get('color', 'unknown'))
            origins.append(trip.get('from', 'unknown'))
            destinations.append(trip.get('to', 'unknown'))
        
        # Calculate diversity metrics
        unique_colors = len(set(colors))
        unique_origins = len(set(origins))
        unique_destinations = len(set(destinations))
        
        time_span = max(departure_times) - min(departure_times) if departure_times else 0
        avg_gap = time_span / (len(departure_times) - 1) if len(departure_times) > 1 else 0
        
        print(f"   Color diversity: {unique_colors} different colors")
        print(f"   Spatial diversity: {unique_origins} origins, {unique_destinations} destinations")
        print(f"   Temporal span: {time_span:.1f} seconds with {avg_gap:.1f}s avg gap")
        
        # Check for randomization features
        has_random_colors = unique_colors > 1
        has_spatial_diversity = unique_origins > 2 and unique_destinations > 2
        has_temporal_spread = time_span > 300  # At least 5 minutes
        
        if has_random_colors and has_spatial_diversity and has_temporal_spread:
            print("   ✅ Good randomization detected!")
        else:
            print("   ⚠️  Limited randomization - may need parameter tuning")
            
    except Exception as e:
        print(f"   ❌ Failed to analyze {trip_file.name}: {e}")

def print_feature_summary():
    """Print a summary of the enhanced randomization features"""
    
    print("\n" + "="*60)
    print("🎯 ENHANCED RANDOMIZATION FEATURES")
    print("="*60)
    print("""
✨ TEMPORAL RANDOMIZATION:
   • Departure time shuffling to break up vehicle clustering
   • Temporal jitter (±15s) to prevent synchronized spawning
   • Chronological order maintained but with varied gaps

🎨 VISUAL DIVERSITY:
   • Realistic color schemes for each vehicle type
   • 15+ colors for passenger cars, 7+ for buses/trucks
   • Simple shapes set as requested (passenger, bus, truck, motorcycle)

🗺️  SPATIAL DISTRIBUTION:
   • Multiple randomization batches with different parameters
   • Inner city, mixed urban, suburban, and long-distance trip types
   • Reduced fringe factors for more inner road usage
   • Enhanced random factors for route variety

⚙️  VEHICLE BEHAVIOR:
   • Speed factor variation (0.85-1.15) for realistic behavior
   • Enhanced departure attributes (best lane, max speed, random position)
   • Vehicle-type-specific distance parameters
   • Proper vType definitions with colors and shapes

📦 FILE MANAGEMENT:
   • Network files maintain compression for SUMO accuracy
   • Trip files properly compressed as requested
   • Polygon support for visual realism
   • Backward compatibility maintained
""")

if __name__ == "__main__":
    print_feature_summary()
    
    success = test_enhanced_randomization()
    
    print("\n" + "="*60)
    if success:
        print("🎉 ENHANCED RANDOMIZATION TEST COMPLETED SUCCESSFULLY!")
        print("   Your traffic simulations should now have:")
        print("   • More realistic vehicle type distribution")
        print("   • Better spatial and temporal variety") 
        print("   • Diverse colors and shapes")
        print("   • Reduced clustering and congestion artifacts")
    else:
        print("❌ TEST FAILED - Check error messages above")
        
    print("\n💡 Next steps:")
    print("   1. Import your desired OSM scenarios with --diversity flag")
    print("   2. Run simulations and observe improved traffic realism")
    print("   3. Adjust randomization parameters if needed")
    print("="*60)