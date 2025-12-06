"""
Standardized Configuration System

Provides standardized simulation configurations to ensure consistent
baseline measurements across all networks. Addresses Root Cause #7
from the BTMD accuracy analysis.

Standard Configuration:
- Duration: 7200s (2 hours) - sufficient for capturing traffic patterns
- Traffic Scale: 1.0 - calibrated flows already have correct vehicle counts
- Traffic Control: "existing" - use current infrastructure
- Calibrated Flows: Use BTMD-calibrated flow files instead of OSM defaults

Author: Traffic Simulator Team
Date: December 2025
"""

from pathlib import Path
from typing import Dict, Any
import json


# Standard configuration for all simulations
STANDARD_CONFIG = {
    "simulation_duration": 7200,  # 2 hours in seconds
    "traffic_scale": 1.0,  # No scaling needed - flows are pre-calibrated
    "traffic_control": "existing",  # Use current traffic light infrastructure
    "use_calibrated_flows": True,  # Use BTMD-calibrated flows instead of OSM defaults
    "time_of_day": "morning_peak",  # Default to morning peak for consistency
    "data_collection": {
        "edge_data": True,
        "vehicle_tracking": True,
        "emissions": True,
        "trip_info": True
    }
}


class ConfigurationStandardizer:
    """
    Ensures all simulations use standardized, comparable configurations
    """
    
    def __init__(self, networks_dir: str = "networks"):
        """
        Initialize the configuration standardizer
        
        Args:
            networks_dir: Directory containing SUMO networks
        """
        self.networks_dir = Path(networks_dir)
    
    def get_standard_config(self, network_name: str = None, 
                           override_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get standardized configuration with optional network-specific overrides
        
        Args:
            network_name: Name of the network (optional)
            override_params: Parameters to override in standard config
            
        Returns:
            Standardized configuration dictionary
        """
        config = STANDARD_CONFIG.copy()
        
        # Add network name if provided
        if network_name:
            config["network_name"] = network_name
            
            # Check if network has calibrated flows
            network_path = self.networks_dir / network_name
            calibration_report = network_path / "calibration_report.json"
            
            if calibration_report.exists():
                with open(calibration_report) as f:
                    calib_data = json.load(f)
                config["calibration_info"] = {
                    "is_calibrated": True,
                    "target_vehicles": calib_data.get("target_total_vehicles", 0),
                    "calibration_date": calib_data.get("timestamp", "unknown")
                }
            else:
                config["calibration_info"] = {
                    "is_calibrated": False,
                    "warning": "Network not calibrated with BTMD data. Results may not match real-world traffic."
                }
        
        # Apply overrides if provided
        if override_params:
            config.update(override_params)
        
        return config
    
    def create_session_config(self, network_name: str, 
                            session_id: str,
                            user_overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a complete session configuration using standard settings
        
        Args:
            network_name: Name of the network to simulate
            session_id: Unique session identifier
            user_overrides: User-specified configuration overrides
            
        Returns:
            Complete session configuration
        """
        # Start with standard config
        config = self.get_standard_config(network_name)
        
        # Apply user overrides (but warn if deviating from standards)
        if user_overrides:
            # Check for deviations from standard
            deviations = []
            
            if "simulation_duration" in user_overrides and user_overrides["simulation_duration"] != 7200:
                deviations.append(f"simulation_duration: {user_overrides['simulation_duration']}s (standard: 7200s)")
            
            if "traffic_scale" in user_overrides and user_overrides["traffic_scale"] != 1.0:
                deviations.append(f"traffic_scale: {user_overrides['traffic_scale']} (standard: 1.0)")
            
            if "traffic_control" in user_overrides and user_overrides["traffic_control"] != "existing":
                deviations.append(f"traffic_control: {user_overrides['traffic_control']} (standard: existing)")
            
            if deviations:
                config["configuration_warnings"] = {
                    "message": "Configuration deviates from standardized baseline",
                    "deviations": deviations,
                    "impact": "Results may not be directly comparable with baseline measurements"
                }
            
            # Apply overrides
            config.update(user_overrides)
        
        # Add session metadata
        config["session_id"] = session_id
        config["configuration_version"] = "1.0.0"
        config["is_standardized"] = not bool(user_overrides)
        
        return config
    
    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a configuration and provide recommendations
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation result with recommendations
        """
        issues = []
        recommendations = []
        
        # Check simulation duration
        if config.get("simulation_duration", 0) < 3600:
            issues.append("Simulation duration less than 1 hour may not capture traffic patterns adequately")
            recommendations.append("Use 7200s (2 hours) for consistent baseline measurements")
        elif config.get("simulation_duration", 0) != 7200:
            recommendations.append("Standard duration is 7200s for comparability with BTMD data")
        
        # Check traffic scale
        if config.get("traffic_scale", 1.0) != 1.0:
            if config.get("use_calibrated_flows", False):
                issues.append("traffic_scale != 1.0 with calibrated flows will double-scale vehicles")
                recommendations.append("Set traffic_scale=1.0 when using calibrated flows")
            else:
                recommendations.append("Consider using calibrated flows with traffic_scale=1.0")
        
        # Check if network is calibrated
        if not config.get("use_calibrated_flows", False):
            issues.append("Not using calibrated flows - results may differ significantly from BTMD data")
            recommendations.append("Run btmd_calibrator.py to generate calibrated flows")
        
        # Check traffic control
        if config.get("traffic_control") == "fixed":
            recommendations.append("'existing' traffic control better matches real-world conditions")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "is_standardized": (
                config.get("simulation_duration") == 7200 and
                config.get("traffic_scale") == 1.0 and
                config.get("traffic_control") == "existing" and
                config.get("use_calibrated_flows", False)
            )
        }
    
    def standardize_all_networks(self) -> Dict[str, Any]:
        """
        Create standardized configurations for all networks
        
        Returns:
            Summary of standardization process
        """
        results = {
            "success": True,
            "networks": [],
            "errors": []
        }
        
        # Get all network directories
        if not self.networks_dir.exists():
            results["success"] = False
            results["errors"].append(f"Networks directory not found: {self.networks_dir}")
            return results
        
        for network_dir in self.networks_dir.iterdir():
            if network_dir.is_dir():
                network_name = network_dir.name
                
                try:
                    # Create standard config
                    config = self.get_standard_config(network_name)
                    
                    # Save to network directory
                    config_file = network_dir / "standard_config.json"
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    results["networks"].append({
                        "name": network_name,
                        "config_file": str(config_file),
                        "is_calibrated": config.get("calibration_info", {}).get("is_calibrated", False)
                    })
                    
                except Exception as e:
                    results["errors"].append({
                        "network": network_name,
                        "error": str(e)
                    })
        
        return results


def get_standard_session_config(network_name: str, session_id: str) -> Dict[str, Any]:
    """
    Convenience function to get a standard session configuration
    
    Args:
        network_name: Name of the network
        session_id: Session identifier
        
    Returns:
        Standardized session configuration
    """
    standardizer = ConfigurationStandardizer()
    return standardizer.create_session_config(network_name, session_id)


def validate_session_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate a session configuration
    
    Args:
        config: Configuration to validate
        
    Returns:
        Validation result
    """
    standardizer = ConfigurationStandardizer()
    return standardizer.validate_configuration(config)


# Configuration presets for different scenarios
CONFIG_PRESETS = {
    "standard_baseline": {
        "description": "Standard 2-hour baseline for BTMD comparison",
        "simulation_duration": 7200,
        "traffic_scale": 1.0,
        "traffic_control": "existing",
        "use_calibrated_flows": True,
        "time_of_day": "morning_peak"
    },
    "extended_observation": {
        "description": "Extended 4-hour observation period",
        "simulation_duration": 14400,
        "traffic_scale": 1.0,
        "traffic_control": "existing",
        "use_calibrated_flows": True,
        "time_of_day": "morning_peak"
    },
    "full_day_simulation": {
        "description": "Full 16-hour day simulation matching BTMD observation period",
        "simulation_duration": 57600,  # 16 hours
        "traffic_scale": 1.0,
        "traffic_control": "existing",
        "use_calibrated_flows": True,
        "time_of_day": "morning_peak"  # Will need temporal patterns
    },
    "rush_hour_focus": {
        "description": "1-hour rush hour focus for detailed analysis",
        "simulation_duration": 3600,
        "traffic_scale": 1.0,
        "traffic_control": "existing",
        "use_calibrated_flows": True,
        "time_of_day": "morning_peak"
    },
    "off_peak_comparison": {
        "description": "Off-peak period for comparison",
        "simulation_duration": 7200,
        "traffic_scale": 1.0,
        "traffic_control": "existing",
        "use_calibrated_flows": True,
        "time_of_day": "midday"
    }
}


def get_preset_config(preset_name: str, network_name: str = None) -> Dict[str, Any]:
    """
    Get a preset configuration
    
    Args:
        preset_name: Name of the preset
        network_name: Optional network name
        
    Returns:
        Preset configuration
    """
    if preset_name not in CONFIG_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(CONFIG_PRESETS.keys())}")
    
    config = CONFIG_PRESETS[preset_name].copy()
    
    if network_name:
        config["network_name"] = network_name
    
    return config


def main():
    """
    Command-line interface for configuration standardization
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Standardize network configurations')
    parser.add_argument('--standardize-all', action='store_true', 
                       help='Create standard configs for all networks')
    parser.add_argument('--list-presets', action='store_true',
                       help='List available configuration presets')
    parser.add_argument('--networks-dir', type=str, default='networks',
                       help='Networks directory (default: networks)')
    
    args = parser.parse_args()
    
    if args.list_presets:
        print("\nAvailable Configuration Presets:")
        print("="*70)
        for name, preset in CONFIG_PRESETS.items():
            print(f"\n{name}:")
            print(f"  Description: {preset['description']}")
            print(f"  Duration: {preset['simulation_duration']}s ({preset['simulation_duration']/3600:.1f} hours)")
            print(f"  Traffic Scale: {preset['traffic_scale']}")
            print(f"  Control: {preset['traffic_control']}")
            print(f"  Time: {preset['time_of_day']}")
        print("\n")
        return 0
    
    if args.standardize_all:
        standardizer = ConfigurationStandardizer(networks_dir=args.networks_dir)
        results = standardizer.standardize_all_networks()
        
        print("\nStandardization Results:")
        print("="*70)
        print(f"Successfully processed: {len(results['networks'])} networks")
        print(f"Errors: {len(results['errors'])}")
        
        if results['networks']:
            print("\nStandardized Networks:")
            for net in results['networks']:
                calib_status = "✅ Calibrated" if net['is_calibrated'] else "⚠️  Not calibrated"
                print(f"  {net['name']}: {calib_status}")
        
        if results['errors']:
            print("\nErrors:")
            for err in results['errors']:
                print(f"  {err['network']}: {err['error']}")
        
        return 0 if results['success'] else 1
    
    # If no action specified, show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
