# Traffic Simulator - Configuration-First Workflow

## Overview

This document describes the enhanced traffic simulation workflow that follows a configuration-first approach. Users configure simulation parameters before selecting networks, ensuring better session management and file isolation.

## Workflow Architecture

### 1. Configuration First Approach

The new workflow follows this sequence:
1. **Configuration Setup** - Users set simulation parameters
2. **Network Selection** - Choose from available networks
3. **Network Copying & Modification** - Apply configurations to copied network files
4. **Simulation Launch** - Start SUMO with configured parameters
5. **Live Monitoring** - Stream data and control simulation

### 2. Key Features

- **Session Isolation**: Each simulation gets its own directory with copied network files
- **Original File Preservation**: Original network files are never modified
- **Configuration Persistence**: Settings are saved and can be reused
- **Live Data Streaming**: Real-time statistics during simulation
- **SUMO Integration**: Direct integration with SUMO GUI and command-line tools

## Frontend Components

### SimulationSetupPage.js

The main configuration interface where users:
- Set simulation duration and timing parameters
- Configure traffic volume and vehicle types
- Define network modifications (speed limits, road closures)
- Set advanced SUMO parameters
- Save configuration to session

**Key Features:**
- Responsive design with sidebar summary
- Real-time parameter validation
- Session ID generation and management
- Configuration persistence

### NetworkSelectionPageEnhanced.js

Enhanced network selection that:
- Displays available SUMO networks with metadata
- Shows current configuration summary
- Handles network copying to session folders
- Applies saved configurations to selected networks

**Key Features:**
- Network preview and metadata display
- Configuration application status
- Error handling and validation
- Session management integration

### SimulationLaunchPage.js

Final step for simulation execution:
- Launches SUMO GUI with configured parameters
- Provides simulation controls (play, pause, stop)
- Displays live statistics and monitoring
- Handles result downloading and session cleanup

**Key Features:**
- Real-time simulation control
- Live data streaming and visualization
- Process management and monitoring
- Result export and download

## Backend Implementation

### SimulationManager.py

Core backend class handling:
- Session configuration storage
- Network file copying and modification
- SUMO process management
- Live data collection and streaming

**Key Methods:**
```python
save_session_config(session_id, config_data)    # Store configuration
get_available_networks()                         # List available networks
setup_session_network(session_id, network_path) # Copy and modify network
launch_simulation(session_id, config)           # Start SUMO process
get_simulation_stats(process_id)                 # Retrieve live data
```

### Flask API Endpoints

#### Configuration Management
- `POST /api/simulation/save-config` - Save session configuration
- `GET /api/networks/available` - Get available networks
- `POST /api/simulation/setup-network` - Copy and configure network

#### Simulation Control
- `POST /api/simulation/launch` - Start SUMO simulation
- `GET /api/simulation/stats/<process_id>` - Get live statistics
- `POST /api/simulation/stop/<process_id>` - Stop simulation
- `POST /api/simulation/pause/<process_id>` - Pause simulation
- `POST /api/simulation/resume/<process_id>` - Resume simulation

#### Session Management
- `GET /api/simulation/download-results/<session_id>` - Download results
- `DELETE /api/simulation/cleanup/<session_id>` - Clean up session

## Configuration Application

### Network Modifications

The system supports various network modifications:

#### Speed Limit Changes
```javascript
speedLimits: [
  { edgeId: "edge1", speedLimit: 30 }, // km/h
  { edgeId: "edge2", speedLimit: 50 }
]
```

#### Road Closures
```javascript
roadClosures: [
  { edgeId: "edge3", startTime: 300, endTime: 1800 } // seconds
]
```

#### Vehicle Types Configuration
```javascript
vehicleTypes: {
  passenger: { enabled: true, percentage: 75, maxSpeed: 50 },
  truck: { enabled: true, percentage: 15, maxSpeed: 40 },
  bus: { enabled: true, percentage: 10, maxSpeed: 45 }
}
```

### File Generation

For each session, the system generates:
- `network.net.xml` - Modified network file
- `routes.rou.xml` - Generated routes based on traffic settings
- `config.sumocfg` - SUMO configuration file
- `additional.add.xml` - Additional elements (closures, detectors)
- `session_metadata.json` - Session information and file references

## Session Management

### Directory Structure
```
sessions/
├── session_[timestamp]_[id]/
│   ├── config.json              # Original configuration
│   ├── session_metadata.json    # Session info
│   ├── network.net.xml         # Modified network
│   ├── routes.rou.xml          # Generated routes
│   ├── config.sumocfg          # SUMO config
│   ├── additional.add.xml      # Additional elements
│   └── outputs/                # Simulation outputs
│       ├── detector_output.xml
│       ├── tripinfo.xml
│       └── summary.xml
```

### Session Lifecycle
1. **Creation**: Generate unique session ID
2. **Configuration**: Save user parameters
3. **Network Setup**: Copy and modify network files
4. **Simulation**: Run SUMO with generated files
5. **Monitoring**: Collect and stream live data
6. **Cleanup**: Remove session files when complete

## Live Data Streaming

### WebSocket Events
- `config_saved` - Configuration saved successfully
- `network_setup_complete` - Network copied and configured
- `simulation_launched` - SUMO process started
- `simulation_stats` - Live simulation statistics
- `simulation_stopped` - Simulation terminated

### Statistics Collected
```javascript
{
  simulationTime: 1500,        // Current simulation time (seconds)
  totalVehicles: 150,          // Total vehicles in simulation
  runningVehicles: 45,         // Currently active vehicles
  waitingVehicles: 8,          // Vehicles waiting
  averageSpeed: 32.5,          // Average speed (km/h)
  averageWaitingTime: 12.3,    // Average waiting time (seconds)
  throughput: 120,             // Vehicles per hour
  emissions: {                 // Environmental data
    co2: 245.6,
    nox: 1.2,
    fuel: 89.4
  }
}
```

## Error Handling

### Frontend Error Management
- Configuration validation before saving
- Network selection verification
- Simulation launch error handling
- Real-time connection monitoring

### Backend Error Handling
- File system error management
- Process failure detection
- Resource cleanup on errors
- Comprehensive logging

## Security Considerations

### File System Safety
- Session isolation prevents cross-contamination
- Original files are never modified
- Automatic cleanup of temporary files
- Path validation and sanitization

### Process Management
- Process isolation and resource limits
- Automatic termination of abandoned processes
- Memory and CPU usage monitoring
- Secure subprocess execution

## Performance Optimization

### File Operations
- Efficient file copying using system calls
- Lazy loading of network metadata
- Compressed result archives
- Background cleanup processes

### Real-Time Data
- Efficient WebSocket communication
- Data aggregation and batching
- Client-side caching and buffering
- Optimized polling intervals

## Deployment Configuration

### Required Directories
```bash
backend/
├── networks/          # Original network files
├── sessions/          # Session-specific copies
└── temp/             # Temporary processing files
```

### Environment Variables
```bash
SUMO_HOME=/path/to/sumo
NETWORKS_DIR=./networks
SESSIONS_DIR=./sessions
MAX_CONCURRENT_SIMULATIONS=5
SESSION_TIMEOUT=3600
```

### SUMO Requirements
- SUMO 1.15+ installed and in PATH
- GUI support for visualization
- TraCI enabled for live data
- Python TraCI library installed

## Usage Examples

### 1. Basic Simulation Setup
```javascript
// Configure simulation
const config = {
  duration: 3600,
  trafficVolume: 0.7,
  vehicleTypes: {
    passenger: { enabled: true, percentage: 80 }
  }
};

// Save configuration
const session = await api.post('/api/simulation/save-config', {
  sessionId: 'session_123',
  config: config
});

// Select and setup network
const networkSetup = await api.post('/api/simulation/setup-network', {
  sessionId: 'session_123',
  networkId: 'urban_intersection',
  networkPath: './networks/urban_intersection.net.xml',
  config: config
});

// Launch simulation
const simulation = await api.post('/api/simulation/launch', {
  sessionId: 'session_123',
  sessionPath: networkSetup.sessionPath,
  config: config,
  enableGui: true
});
```

### 2. Network Modification Example
```javascript
const config = {
  speedLimits: [
    { edgeId: "arterial_ns1", speedLimit: 40 }
  ],
  roadClosures: [
    { edgeId: "residential1", startTime: 900, endTime: 1800 }
  ]
};
```

This configuration will:
- Reduce speed limit on arterial_ns1 to 40 km/h
- Close residential1 from 15 to 30 minutes into simulation

## Future Enhancements

### Planned Features
- Network editor integration
- Advanced traffic light programming
- Multi-scenario batch execution
- Result comparison and analysis
- Cloud deployment support
- Real-time collaboration features

### Integration Opportunities
- OpenStreetMap network import
- Traffic data integration
- Weather condition simulation
- Incident scenario modeling
- Public transit integration
