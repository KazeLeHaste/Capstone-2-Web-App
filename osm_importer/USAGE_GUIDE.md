# Enhanced Randomization Usage Guide

This guide explains how to use the new enhanced randomization system to create more realistic traffic simulations.

## Quick Start

### 1. Test the Enhanced System
```bash
cd osm_importer
python test_enhanced_randomization.py
```

This will:
- Scan for available OSM scenarios
- Import one with enhanced randomization
- Analyze the results and show diversity metrics

### 2. Import Scenarios with Enhancement
```bash
# Import with enhanced randomization (recommended)
python osm_scenario_importer.py --import "Jollibee Molino Area" --name realistic_traffic --diversity

# Import without enhancement (preserves original patterns)  
python osm_scenario_importer.py --import "Jollibee Molino Area" --name original_traffic
```

### 3. Run Simulation
Use your existing simulation workflow with the new network files. The enhanced randomization will provide:
- More diverse vehicle spawning
- Better spatial distribution
- Realistic colors and shapes
- Reduced traffic clustering

## Before vs After Comparison

### Before Enhancement
❌ **Problems:**
- All passenger cars spawn together in groups
- Same origin-destination pairs repeatedly
- Limited color variety (mostly yellow)
- Predictable congestion patterns
- Vehicles cluster at same spawn points

### After Enhancement  
✅ **Improvements:**
- Mixed vehicle types spawn throughout simulation
- 4 different spatial distribution patterns per vehicle type
- 15+ realistic colors for passenger vehicles
- Temporal jitter prevents synchronized departures
- Routes span inner city, suburban, and arterial roads

## Configuration Options

### Vehicle Type Parameters
Each vehicle type has been optimized:

**Passenger Vehicles:**
- Focus on inner city routes (fringe_factor: 1.5)
- High randomness (random_factor: 1.4) 
- Shorter minimum distances (200m)
- Maximum color variety (15 colors)

**Buses:**
- Balanced urban coverage (fringe_factor: 2.0)
- Local route focus (min_distance: 400m)
- Transit-appropriate colors (yellow, blue, white)

**Trucks:**
- Commercial route preference (fringe_factor: 2.5)
- Longer routes (min_distance: 500m)
- Commercial vehicle colors

**Motorcycles:**
- Maximum flexibility (fringe_factor: 1.0)
- Shortest routes allowed (min_distance: 150m)
- Highest randomness factor (1.5)

### Temporal Randomization
- **Departure shuffling**: Breaks up vehicle clustering
- **±15 second jitter**: Prevents synchronized spawning  
- **Chronological order**: Maintains overall simulation flow

## Advanced Usage

### Custom Randomization
To modify randomization parameters, edit the `vehicle_params` dictionary in `osm_scenario_importer.py`:

```python
'passenger': {
    'min_distance': 200.0,    # Minimum trip distance
    'fringe_factor': 1.5,     # Road type preference (lower = inner roads)
    'random_factor': 1.4,     # Route randomness (higher = more variety)
}
```

### Batch Processing
Import multiple scenarios with enhancement:
```bash
for scenario in "Jollibee Molino Area" "SM Bacoor Area" "Perpetual Molino Area"; do
    python osm_scenario_importer.py --import "$scenario" --name "enhanced_${scenario// /_}" --diversity
done
```

### File Compression Control
The system automatically handles file compression:
- **Network files**: Remain compressed (.net.xml.gz) for SUMO accuracy
- **Trip files**: Compressed after processing (.trips.xml.gz)
- **Polygon files**: Decompressed for web app compatibility

## Quality Assurance

### Verification Metrics
The test script checks for:
- **Color diversity**: 5+ different colors per vehicle type
- **Spatial diversity**: 5+ different origin/destination edges
- **Temporal spread**: 300+ seconds time span
- **Randomization features**: Proper attribute settings

### Expected Results
Good randomization should show:
```
Color diversity: 12 different colors
Spatial diversity: 25 origins, 28 destinations  
Temporal span: 3247.3 seconds with 89.2s avg gap
✅ Good randomization detected!
```

## Troubleshooting

### Common Issues

**Issue:** Test fails with "No OSM scenarios found"
**Solution:** Ensure OSM scenarios exist in `osm_scenarios/` folder

**Issue:** Enhancement produces too much variety
**Solution:** Reduce `random_factor` parameters in vehicle config

**Issue:** Not enough spatial diversity
**Solution:** Reduce `fringe_factor` to encourage inner road usage

**Issue:** Compressed files cause problems
**Solution:** Ensure SUMO version supports .gz files (1.8.0+)

### Performance Optimization
- Use `--no-diversity` for faster imports when testing
- Enable `--diversity` only for final simulation runs
- Monitor memory usage with large networks (>10k edges)

## Best Practices

### When to Use Enhancement
✅ **Use `--diversity` for:**
- Final production simulations
- Realistic traffic flow analysis
- Visual demonstrations
- Research requiring natural variety

❌ **Avoid `--diversity` for:**
- Reproducible research experiments
- Performance testing
- Quick prototyping
- When original OSM patterns are preferred

### Simulation Setup
1. Import scenarios with `--diversity`
2. Verify randomization with test script
3. Configure SUMO with proper delay settings
4. Use SUMO-GUI to observe improved realism
5. Collect analytics on improved traffic flow

## Results Interpretation

### Traffic Flow Improvements
With enhanced randomization, expect:
- **Reduced artificial congestion** from vehicle clustering
- **More realistic lane usage** across all road types
- **Natural vehicle mix** throughout simulation
- **Better intersection behavior** with varied approach timing
- **Improved visual realism** for presentations/demos

### Analytics Impact
Enhanced randomization provides:
- More representative traffic density measurements
- Varied route choice patterns for analysis
- Realistic vehicle type distribution in data
- Natural temporal patterns in flow metrics

This enhanced system transforms your OSM scenarios from predictable patterns into realistic traffic simulations that better represent real-world conditions.