#!/usr/bin/env python3
"""
Test script for traffic control functionality.

This script tests:
1. Network analysis capabilities
2. netconvert traffic light modification
3. Traffic control configuration validation

Author: Traffic Simulator Team
Date: September 2025
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
import gzip
import xml.etree.ElementTree as ET

def test_netconvert_availability():
    """Test if netconvert is available and working"""
    print("Testing netconvert availability...")
    try:
        result = subprocess.run(['netconvert', '--help'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ netconvert is available and working")
            return True
        else:
            print("✗ netconvert returned error code:", result.returncode)
            return False
    except FileNotFoundError:
        print("✗ netconvert not found. Please install SUMO and add to PATH")
        return False
    except subprocess.TimeoutExpired:
        print("✗ netconvert timed out")
        return False

def analyze_network(network_path):
    """Analyze a network file for traffic light information"""
    print(f"\nAnalyzing network: {network_path}")
    
    try:
        # Load and parse the network file
        if str(network_path).endswith('.gz'):
            with gzip.open(network_path, 'rt') as f:
                content = f.read()
        else:
            with open(network_path, 'r') as f:
                content = f.read()
        
        root = ET.fromstring(content)
        
        # Count traffic lights and junctions
        tl_logics = root.findall('.//tlLogic')
        tl_junctions = root.findall('.//junction[@type="traffic_light"]')
        priority_junctions = root.findall('.//junction[@type="priority"]')
        
        print(f"  Traffic light logics: {len(tl_logics)}")
        print(f"  Traffic light junctions: {len(tl_junctions)}")
        print(f"  Priority junctions: {len(priority_junctions)}")
        
        # Show existing traffic light types
        for tl in tl_logics:
            print(f"    TL {tl.get('id')}: type={tl.get('type')}, phases={len(tl.findall('phase'))}")
        
        return len(tl_logics), len(priority_junctions)
        
    except Exception as e:
        print(f"✗ Error analyzing network: {e}")
        return 0, 0

def test_traffic_light_conversion(network_path, test_type="actuated"):
    """Test converting existing traffic lights to different types"""
    print(f"\nTesting traffic light conversion to {test_type}...")
    
    if not network_path.exists():
        print(f"✗ Network file not found: {network_path}")
        return False
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.net.xml', delete=False) as tmp_file:
            temp_output = Path(tmp_file.name)
        
        # Prepare input file (decompress if needed)
        if str(network_path).endswith('.gz'):
            with tempfile.NamedTemporaryFile(suffix='.net.xml', delete=False) as tmp_input:
                temp_input = Path(tmp_input.name)
            
            with gzip.open(network_path, 'rb') as f_in:
                with open(temp_input, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            input_file = temp_input
        else:
            input_file = network_path
        
        # Build command
        cmd = [
            'netconvert',
            '-s', str(input_file),
            '-o', str(temp_output),
            '--tls.rebuild',
            '--tls.default-type', test_type
        ]
        
        if test_type == 'actuated':
            cmd.extend(['--tls.min-dur', '5', '--tls.max-dur', '50'])
        
        print(f"  Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✓ Successfully converted traffic lights to {test_type}")
            
            # Analyze the result
            original_tls, _ = analyze_network(network_path) if network_path.exists() else (0, 0)
            new_tls, _ = analyze_network(temp_output)
            print(f"  Traffic lights: {original_tls} → {new_tls}")
            
            # Clean up temp files
            temp_output.unlink()
            if 'temp_input' in locals():
                temp_input.unlink()
            
            return True
        else:
            print(f"✗ netconvert failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing traffic light conversion: {e}")
        return False
    finally:
        # Clean up temp files
        if 'temp_output' in locals() and temp_output.exists():
            temp_output.unlink()
        if 'temp_input' in locals() and temp_input.exists():
            temp_input.unlink()

def test_priority_to_traffic_lights(network_path):
    """Test converting priority junctions to traffic lights"""
    print(f"\nTesting priority junction to traffic light conversion...")
    
    if not network_path.exists():
        print(f"✗ Network file not found: {network_path}")
        return False
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.net.xml', delete=False) as tmp_file:
            temp_output = Path(tmp_file.name)
        
        # Prepare input file (decompress if needed)
        if str(network_path).endswith('.gz'):
            with tempfile.NamedTemporaryFile(suffix='.net.xml', delete=False) as tmp_input:
                temp_input = Path(tmp_input.name)
            
            with gzip.open(network_path, 'rb') as f_in:
                with open(temp_input, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            input_file = temp_input
        else:
            input_file = network_path
        
        # Build command to add traffic lights to priority junctions
        cmd = [
            'netconvert',
            '-s', str(input_file),
            '-o', str(temp_output),
            '--tls.guess',
            '--tls.guess.threshold', '100',  # Lower threshold to catch more junctions
            '--tls.default-type', 'actuated'
        ]
        
        print(f"  Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Successfully ran priority-to-TLS conversion")
            
            # Analyze the results
            original_tls, original_priority = analyze_network(network_path)
            new_tls, new_priority = analyze_network(temp_output)
            
            print(f"  Traffic lights: {original_tls} → {new_tls} (+{new_tls - original_tls})")
            print(f"  Priority junctions: {original_priority} → {new_priority} ({original_priority - new_priority} converted)")
            
            # Clean up temp files
            temp_output.unlink()
            if 'temp_input' in locals():
                temp_input.unlink()
            
            return True
        else:
            print(f"✗ netconvert failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing priority-to-TLS conversion: {e}")
        return False
    finally:
        # Clean up temp files
        if 'temp_output' in locals() and temp_output.exists():
            temp_output.unlink()
        if 'temp_input' in locals() and temp_input.exists():
            temp_input.unlink()

def main():
    """Run all traffic control tests"""
    print("Traffic Control Functionality Test")
    print("=" * 50)
    
    # Test netconvert availability
    if not test_netconvert_availability():
        print("\nCannot proceed without netconvert. Please install SUMO.")
        return
    
    # Test with available networks
    networks_dir = Path("backend/networks")
    test_networks = [
        networks_dir / "sm_molino_area" / "sm_molino_area.net.xml.gz",
        networks_dir / "jollibee_molino_area" / "jollibee_molino_area.net.xml.gz"
    ]
    
    for network_path in test_networks:
        if network_path.exists():
            print(f"\n{'='*60}")
            print(f"Testing with network: {network_path.name}")
            print('='*60)
            
            # Analyze original network
            analyze_network(network_path)
            
            # Test converting existing traffic lights to actuated
            test_traffic_light_conversion(network_path, "actuated")
            
            # Test converting existing traffic lights to static
            test_traffic_light_conversion(network_path, "static")
            
            # Test adding traffic lights to priority junctions
            test_priority_to_traffic_lights(network_path)
            
        else:
            print(f"Network not found: {network_path}")
    
    print(f"\n{'='*60}")
    print("Traffic control testing completed!")
    print('='*60)

if __name__ == "__main__":
    main()