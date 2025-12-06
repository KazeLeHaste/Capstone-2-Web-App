"""
Dynamic BTMD Flow Generator

Generates calibrated SUMO flow files at runtime based on user's traffic intensity setting.
Integrates with simulation_manager.py to provide accurate traffic volumes that scale
meaningfully from normal traffic (1x) to rush hour traffic (10x).

Author: Traffic Simulator Team
Date: December 2025
"""

import json
from pathlib import Path
from typing import Dict, Any
import sys

# Import the calibrator
sys.path.append(str(Path(__file__).parent))
from btmd_calibrator import BTMDCalibrator, BTMD_TRAFFIC_DATA


def generate_calibrated_flows_for_session(network_name: str,
                                         session_dir: Path,
                                         traffic_scale: float,
                                         simulation_duration: int = 7200) -> bool:
    """
    Generate calibrated flow files for a simulation session based on traffic scale
    
    Args:
        network_name: Name of the network
        session_dir: Session directory where flow files should be created
        traffic_scale: Traffic intensity from UI (1.0 = normal, 10.0 = rush hour)
        simulation_duration: Simulation duration in seconds (default: 7200)
        
    Returns:
        True if flow files were generated successfully, False otherwise
    """
    # Check if network has BTMD data
    if network_name not in BTMD_TRAFFIC_DATA:
        print(f"⚠️  No BTMD data for {network_name}, using default flows")
        return False
    
    try:
        # Create calibrator
        calibrator = BTMDCalibrator(networks_dir=str(session_dir.parent.parent / "networks"))
        
        # Calculate simulation hours
        simulation_hours = simulation_duration / 3600.0
        
        # Generate calibrated flows for this intensity
        # The session_dir is where we need to put the flows
        routes_dir = session_dir / "routes"
        routes_dir.mkdir(exist_ok=True)
        
        # Get BTMD data
        btmd_data = BTMD_TRAFFIC_DATA[network_name]
        
        # Calculate target using traffic intensity
        avg_veh_per_hour = btmd_data["avg_vehicles_per_hour"]
        peak_veh_per_hour = btmd_data["peak_hour_volume"]
        
        # Linear interpolation between average and peak
        intensity_factor = min(max(traffic_scale, 1.0), 10.0)
        target_veh_per_hour = int(avg_veh_per_hour + 
                                  (peak_veh_per_hour - avg_veh_per_hour) * 
                                  (intensity_factor - 1.0) / 9.0)
        
        total_vehicles = int(target_veh_per_hour * simulation_hours)
        
        # Get vehicle type proportions
        vehicle_mix = btmd_data["vehicle_mix"]
        
        # Calculate vehicles per type
        vehicles_per_type = {}
        for vtype, proportion in vehicle_mix.items():
            if vtype == "taxi":
                vehicles_per_type["passenger"] = vehicles_per_type.get("passenger", 0) + int(total_vehicles * proportion)
            else:
                vehicles_per_type[vtype] = int(total_vehicles * proportion)
        
        # Get edges from network file (copy from source network)
        source_network_path = session_dir.parent.parent / "networks" / network_name
        edges = calibrator._extract_network_edges(source_network_path, network_name)
        
        if not edges:
            print(f"⚠️  No edges found in network {network_name}")
            return False
        
        # Generate flow files in session directory
        calibrator._generate_calibrated_flows(
            network_path=session_dir,
            vehicles_per_type=vehicles_per_type,
            simulation_hours=simulation_hours,
            network_name=network_name
        )
        
        print(f"✅ Generated calibrated flows for {network_name}")
        print(f"   Intensity: {traffic_scale}x → {target_veh_per_hour} veh/hr ({total_vehicles} total)")
        print(f"   Breakdown: Passenger={vehicles_per_type.get('passenger', 0)}, "
              f"Motorcycle={vehicles_per_type.get('motorcycle', 0)}, "
              f"Truck={vehicles_per_type.get('truck', 0)}, "
              f"Jeepney={vehicles_per_type.get('jeepney', 0)}, "
              f"Bus={vehicles_per_type.get('bus', 0)}")
        
        # Create a metadata file to track what was generated
        metadata = {
            "network": network_name,
            "traffic_scale": traffic_scale,
            "simulation_duration": simulation_duration,
            "target_vehicles_per_hour": target_veh_per_hour,
            "total_vehicles": total_vehicles,
            "vehicle_breakdown": vehicles_per_type,
            "btmd_avg": avg_veh_per_hour,
            "btmd_peak": peak_veh_per_hour
        }
        
        metadata_file = session_dir / "btmd_calibration.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating calibrated flows: {e}")
        import traceback
        traceback.print_exc()
        return False


def should_use_calibrated_flows(network_name: str) -> bool:
    """
    Check if a network has BTMD calibration data available
    
    Args:
        network_name: Name of the network
        
    Returns:
        True if BTMD data is available for this network
    """
    return network_name in BTMD_TRAFFIC_DATA


def get_btmd_info(network_name: str) -> Dict[str, Any]:
    """
    Get BTMD calibration information for a network
    
    Args:
        network_name: Name of the network
        
    Returns:
        Dictionary with BTMD data or None if not available
    """
    if network_name in BTMD_TRAFFIC_DATA:
        return {
            "has_btmd_data": True,
            "avg_vehicles_per_hour": BTMD_TRAFFIC_DATA[network_name]["avg_vehicles_per_hour"],
            "peak_vehicles_per_hour": BTMD_TRAFFIC_DATA[network_name]["peak_hour_volume"],
            "intersection_name": BTMD_TRAFFIC_DATA[network_name]["name"]
        }
    else:
        return {
            "has_btmd_data": False
        }
