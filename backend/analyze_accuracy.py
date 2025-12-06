"""
Analyze simulation accuracy against BTMD data
"""
import json

# BTMD Data from btmd_calibrator.py
BTMD_DATA = {
    "St Dominic Area": {
        "avg_veh_per_hour": 874,
        "peak_veh_per_hour": 974,
        "vehicle_distribution": {
            "passenger": 0.3445,
            "motorcycle": 0.3355,
            "truck": 0.1810,
            "jeepney": 0.0724,
            "bus": 0.0132
        }
    },
    "Bayanan Area": {
        "avg_veh_per_hour": 619,
        "peak_veh_per_hour": 763,
        "vehicle_distribution": {
            "passenger": 0.3565,
            "motorcycle": 0.2987,
            "truck": 0.1623,
            "jeepney": 0.0974,
            "bus": 0.0130
        }
    }
}

# Simulation results from screenshots
simulations = [
    {
        "name": "St Dominic Area 10x",
        "session": "session_1765022767983_ts8jaj6z7",
        "network": "St Dominic Area",
        "intensity": 10.0,
        "duration_hours": 2.0,
        "actual_vehicles": 1280
    },
    {
        "name": "St Dominic Area 1x",
        "session": "session_1765022842947_wis2bns2p",
        "network": "St Dominic Area",
        "intensity": 1.0,
        "duration_hours": 2.0,
        "actual_vehicles": 128
    },
    {
        "name": "Bayanan Area 10x",
        "session": "session_1765022874744_33qj5zf0z",
        "network": "Bayanan Area",
        "intensity": 10.0,
        "duration_hours": 2.0,
        "actual_vehicles": 1430
    }
]

print("=" * 80)
print("BTMD ACCURACY ANALYSIS")
print("=" * 80)
print()

for sim in simulations:
    network = sim["network"]
    btmd = BTMD_DATA[network]
    
    # Calculate expected vehicles based on intensity
    avg_vph = btmd["avg_veh_per_hour"]
    peak_vph = btmd["peak_veh_per_hour"]
    intensity = sim["intensity"]
    duration = sim["duration_hours"]
    
    # Interpolation formula: target = avg + (peak - avg) * (intensity - 1) / 9
    target_vph = avg_vph + (peak_vph - avg_vph) * (intensity - 1.0) / 9.0
    expected_vehicles = target_vph * duration
    
    # Calculate accuracy
    actual = sim["actual_vehicles"]
    accuracy = (min(actual, expected_vehicles) / max(actual, expected_vehicles)) * 100
    error = actual - expected_vehicles
    error_pct = (error / expected_vehicles) * 100
    
    print(f"📊 {sim['name']}")
    print(f"   Session: {sim['session']}")
    print(f"   Intensity: {intensity}x")
    print(f"   Duration: {duration} hours")
    print(f"   BTMD Average: {avg_vph} veh/hr")
    print(f"   BTMD Peak: {peak_vph} veh/hr")
    print(f"   Target (interpolated): {target_vph:.1f} veh/hr")
    print(f"   Expected Vehicles: {expected_vehicles:.0f}")
    print(f"   Actual Vehicles: {actual}")
    print(f"   Error: {error:+.0f} ({error_pct:+.1f}%)")
    print(f"   ⚠️  ACCURACY: {accuracy:.2f}%")
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("❌ The simulations are still using the OLD OSM trip files!")
print()
print("Evidence:")
print("  • St Dominic 1x: 128 vehicles (should be ~1,748)")
print("  • St Dominic 10x: 1,280 vehicles (should be ~1,948)")
print("  • Bayanan 10x: 1,430 vehicles (should be ~1,526)")
print()
print("All results show simple 10x multiplication of base OSM trips (~128 base).")
print("This indicates BTMD calibrated flows are NOT being generated.")
print()
print("Possible causes:")
print("  1. Backend server not restarted after code changes")
print("  2. btmd_flow_generator.py import failing silently")
print("  3. should_use_calibrated_flows() returning False")
print("  4. Error in flow generation being caught and ignored")
print()
print("Next steps:")
print("  1. Restart backend server: python backend/app.py")
print("  2. Check terminal output for '🎯 Generating BTMD-calibrated flows' message")
print("  3. Verify btmd_calibration.json is created in session folder")
print("  4. Verify osm.*.flows.xml files are generated (not just .trips.xml)")
print()

# Calculate overall accuracy across all simulations
print("=" * 80)
print("DETAILED ACCURACY CALCULATION")
print("=" * 80)
print()

total_accuracy = 0
for sim in simulations:
    network = sim["network"]
    btmd = BTMD_DATA[network]
    
    avg_vph = btmd["avg_veh_per_hour"]
    peak_vph = btmd["peak_veh_per_hour"]
    intensity = sim["intensity"]
    duration = sim["duration_hours"]
    
    target_vph = avg_vph + (peak_vph - avg_vph) * (intensity - 1.0) / 9.0
    expected_vehicles = target_vph * duration
    actual = sim["actual_vehicles"]
    
    accuracy = (min(actual, expected_vehicles) / max(actual, expected_vehicles)) * 100
    total_accuracy += accuracy
    
    print(f"{sim['name']}: {accuracy:.2f}%")

avg_accuracy = total_accuracy / len(simulations)
print()
print(f"📉 AVERAGE ACCURACY: {avg_accuracy:.2f}%")
print()
print("This is FAR BELOW the 90% target accuracy goal.")
print()
