# OSM Scenario Importer - Enhanced Randomization System

A sophisticated tool for importing OpenStreetMap-generated traffic scenarios with **enhanced randomization** for realistic traffic simulation.

## 🎯 Key Features

### Enhanced Randomization System
- **Temporal Diversity**: Departure time shuffling with jitter to prevent vehicle clustering
- **Spatial Distribution**: Multiple randomization batches targeting different road types
- **Visual Variety**: Realistic color schemes and proper vehicle shapes
- **Behavioral Realism**: Speed factor variation and enhanced departure attributes
- **File Compression**: Network files maintain compression for SUMO accuracy

### Original Features
- Complete OSM scenario import with all vehicle types
- Preserves realistic traffic patterns from OSM Web Wizard
- Prioritizes .trips.xml files for better timing accuracy
- Polygon support for visual realism
- Vehicle type filtering and configuration
- Network package compatibility with web app

## 🚗 Randomization Improvements

### Problem Addressed
The original system had issues with:
- Vehicles spawning in clusters of the same type
- Predictable origin-destination patterns
- Limited spatial distribution variety
- Repetitive visual appearance

### Solution Implementation

#### 1. **Multi-Batch Generation**
Creates 4 different randomization batches per vehicle type:
```python
# Inner city focus (reduced fringe factor)
fringe_factor: 1.5, random_factor: 1.4

# Mixed urban (balanced parameters)  
fringe_factor: 2.0, random_factor: 1.1

# Suburban/arterial focus
fringe_factor: 3.0, random_factor: 0.9

# Long distance trips
fringe_factor: 4.0, random_factor: 1.5
```

#### 2. **Temporal Randomization**
- Departure time shuffling to break clustering
- ±15 second temporal jitter to prevent synchronization
- Maintains chronological order with varied gaps

#### 3. **Visual Diversity**
```python
passenger_colors = [
    '255,255,255',  # White
    '128,128,128',  # Gray
    '255,0,0',      # Red
    '0,0,255',      # Blue
    # ... 15 total colors
]
```

#### 4. **Enhanced Vehicle Attributes**
- Speed factor variation: 0.85-1.15 for realistic behavior
- Department attributes: `departLane="best"`, `departPos="random"`
- Simple shapes as requested: passenger, bus, truck, motorcycle

## 📦 Installation & Usage

### Basic Usage
```bash
# List available OSM scenarios
python osm_scenario_importer.py --list

# Import with enhanced randomization
python osm_scenario_importer.py --import "Jollibee Molino Area" --name enhanced_traffic --diversity

# Import without randomization (preserve original)
python osm_scenario_importer.py --import "Jollibee Molino Area" --name original_traffic
```

### Test the System
```bash
# Run comprehensive randomization test
python test_enhanced_randomization.py
```

## 🔧 Configuration

### Vehicle-Specific Parameters
Each vehicle type has optimized randomization parameters:

```python
'passenger': {
    'min_distance': 200.0,    # Shorter trips for variety
    'fringe_factor': 1.5,     # More inner road usage
    'random_factor': 1.4,     # High randomness
}

'bus': {
    'min_distance': 400.0,    # Local routes
    'fringe_factor': 2.0,     # Balanced road usage
    'random_factor': 1.3,
}

'truck': {
    'min_distance': 500.0,    # Commercial routes
    'fringe_factor': 2.5,     # Prefer main roads
    'random_factor': 1.25,
}

'motorcycle': {
    'min_distance': 150.0,    # Maximum flexibility
    'fringe_factor': 1.0,     # Any road type
    'random_factor': 1.5,     # Maximum randomness
}
```

## 📁 File Structure

```
osm_scenarios/
├── Jollibee Molino Area/
│   ├── osm.net.xml.gz           # Network (compressed)
│   ├── osm.passenger.trips.xml  # Trip definitions
│   ├── osm.bus.trips.xml
│   ├── osm.truck.trips.xml
│   ├── osm.motorcycle.trips.xml
│   └── osm.poly.xml.gz          # Buildings/polygons

backend/networks/
├── enhanced_traffic/
│   ├── enhanced_traffic.net.xml.gz     # Compressed network
│   ├── enhanced_traffic.sumocfg        # SUMO configuration
│   ├── enhanced_traffic.poly.add.xml   # Visual elements
│   └── routes/
│       ├── osm.passenger.trips.xml.gz  # Enhanced trips (compressed)
│       ├── osm.bus.trips.xml.gz
│       └── ...
```

## 🎨 Randomization Results

### Expected Improvements
- **Vehicle Type Diversity**: Mixed vehicle types instead of clusters
- **Spatial Distribution**: Vehicles spawn across different road types
- **Temporal Variety**: Randomized departure times reduce congestion artifacts
- **Visual Realism**: 15+ vehicle colors, proper shapes
- **Route Variety**: Multiple origin-destination combinations

### Performance Metrics
The system generates:
- **4 randomization batches** per vehicle type
- **±15 second temporal jitter** for departure times
- **15+ color variations** for passenger vehicles
- **Multiple distance ranges** (150m-2000m) for trip variety

## 🔍 Technical Implementation

### Key Methods
- `_generate_realistic_diverse_trips()`: Main randomization orchestrator
- `_create_randomization_batches()`: Creates parameter variations
- `_apply_enhanced_randomization()`: Temporal and visual randomization
- `_enhance_vehicle_type_definition()`: vType enhancement with colors/shapes
- `_compress_trip_file()`: File compression for SUMO accuracy

### SUMO Integration
- Uses `randomTrips.py` with enhanced parameters
- Applies `duarouter` for route validation
- Maintains SUMO XML schema compliance
- Preserves OSM Web Wizard timing patterns

## 🚨 Important Notes

### File Compression
- Network files remain compressed (.net.xml.gz) for SUMO behavioral accuracy
- Trip files are compressed post-processing as requested
- Polygon files are decompressed for web app compatibility

### Backward Compatibility
- Original OSM files preserved as fallback
- Option to disable randomization (`--no-diversity`)
- Maintains existing network naming conventions

### Recommended Usage
1. **For Realistic Traffic**: Use `--diversity` flag for enhanced randomization
2. **For Research Reproducibility**: Avoid `--diversity` to preserve original patterns
3. **For Testing**: Use `test_enhanced_randomization.py` to verify improvements

## 🎯 Results Summary

The enhanced randomization system addresses your key concerns:

✅ **Vehicle Type Clustering**: Resolved with multi-batch generation
✅ **Predictable Destinations**: Resolved with spatial distribution variety  
✅ **Spawn Point Concentration**: Resolved with fringe factor reduction
✅ **Visual Monotony**: Resolved with 15+ colors and proper shapes
✅ **File Compression**: Network files maintain compression as requested

This creates more realistic traffic simulations with natural vehicle distribution, varied routes, and proper visual representation.

## 📚 Additional Resources

- [SUMO randomTrips.py Documentation](https://sumo.dlr.de/docs/Tools/Trip.html#randomtripspy)
- [Vehicle Type Parameters](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html)
- [OSM Web Wizard Guide](https://sumo.dlr.de/docs/Tutorials/OSMWebWizard.html)