# Database Implementation for Traffic Simulator

## Overview

The traffic simulator has been enhanced with a SQLite database to replace the previous file-based storage approach. This provides better data management, querying capabilities, and enables new features for session analytics and comparison.

## Database Schema

### Core Tables

#### `sessions`
- `id` (PRIMARY KEY): Session identifier
- `created_at`: Session creation timestamp  
- `updated_at`: Last update timestamp
- `status`: Session status (created, configured, running, completed, failed)
- `network_id`: Associated network identifier
- `network_name`: Network display name
- `session_path`: File system path to session directory
- `can_analyze`: Boolean indicating if analytics are available
- `completed_at`: Session completion timestamp

#### `configurations`
- `id` (AUTO INCREMENT PRIMARY KEY)
- `session_id` (FOREIGN KEY): Reference to sessions table
- Configuration parameters:
  - `sumo_begin`, `sumo_end`, `sumo_step_length`
  - `sumo_time_to_teleport`, `sumo_traffic_intensity`
  - `enabled_vehicles` (JSON): List of enabled vehicle types
  - `traffic_control_method`: Traffic control strategy
  - `traffic_control_config` (JSON): Traffic control parameters
  - `vehicle_types_config` (JSON): Vehicle type configurations

#### `kpis`
- `id` (AUTO INCREMENT PRIMARY KEY)
- `session_id` (FOREIGN KEY): Reference to sessions table
- Key Performance Indicators:
  - Vehicle counts: `total_vehicles_loaded`, `total_vehicles_completed`
  - Time metrics: `avg_travel_time`, `avg_waiting_time`, `simulation_duration`
  - Speed metrics: `avg_speed`, `avg_relative_speed`
  - Distance metrics: `avg_route_length`, `total_distance_traveled`
  - Performance metrics: `throughput`, `flow_rate`, `congestion_index`
  - Safety metrics: `total_teleports`, `total_collisions`
  - Environmental metrics: `total_co2`, `total_co`, `total_nox`

#### `live_data`
- `id` (AUTO INCREMENT PRIMARY KEY)
- `session_id` (FOREIGN KEY): Reference to sessions table
- Real-time metrics:
  - `simulation_time`: Current simulation time
  - `active_vehicles`: Number of active vehicles
  - `avg_speed`: Average vehicle speed
  - `throughput`: Vehicles per hour
  - `timestamp`: Data collection timestamp
  - `raw_data` (JSON): Additional metrics

#### `trips`
- Individual vehicle trip data
- `session_id` (FOREIGN KEY), `vehicle_id`, `vehicle_type`
- Trip metrics: `depart_time`, `arrival_time`, `duration`
- Performance: `route_length`, `waiting_time`, `time_loss`, `avg_speed`

#### `time_series`
- Temporal simulation data for trend analysis
- `session_id` (FOREIGN KEY), `time_step`
- Metrics: `running_vehicles`, `halting_vehicles`, `mean_speed`, `mean_waiting_time`

#### `recommendations`
- AI/rule-based traffic optimization suggestions
- `session_id` (FOREIGN KEY), `rule_id`, `priority`, `category`
- Content: `message`, `kpi_name`, `actual_value`, `threshold_value`

#### `networks`
- Network metadata and management
- `id` (PRIMARY KEY): Network identifier
- `name`, `description`, `path`: Network information
- `is_osm_scenario`: Boolean for OSM-based scenarios
- `vehicle_types` (JSON): Available vehicle types
- `last_used`: Last usage timestamp

## Data Flow

### 1. Session Creation & Configuration
```
Frontend → POST /api/simulation/save-config
    ↓
Backend: SimulationManager.save_session_config()
    ↓
Database: Insert into sessions + configurations tables
    ↓
File System: Backup JSON files (backward compatibility)
```

### 2. Network Setup
```
Frontend → POST /api/simulation/setup-network
    ↓
Backend: SimulationManager.setup_session_network()
    ↓
Database: Update session with network info + save/update network metadata
    ↓
File System: Copy network files to session directory
```

### 3. Live Simulation Data
```
SUMO TraCI → SimulationManager._start_data_collection_thread()
    ↓
Database: Batch insert into live_data table (every 10 steps)
    ↓
WebSocket: Broadcast to frontend (every step)
```

### 4. Simulation Completion & Analytics
```
SUMO Process End → SimulationManager._handle_simulation_completion()
    ↓
Analytics Engine: Parse XML outputs
    ↓
Database: Save KPIs, trips, time_series, recommendations
    ↓
Session Status: Update to 'completed' with can_analyze=true
```

## New API Endpoints

### Session Management
- `GET /api/sessions` - List recent sessions
- `GET /api/sessions/{id}` - Get session details with configuration
- `DELETE /api/sessions/{id}` - Delete session and related data

### Analytics (Database-Powered)
- `GET /api/sessions/{id}/analytics` - Get complete analytics from database
- `GET /api/sessions/{id}/live-data` - Get live data history

### Network Management
- `GET /api/networks/database` - Get networks from database

### Database Administration
- `GET /api/database/stats` - Database statistics
- `POST /api/database/cleanup` - Clean up old data

## Benefits

### 1. Enhanced Performance
- **Fast Queries**: SQL-based filtering and aggregation
- **Indexed Access**: Quick session and analytics retrieval
- **Batch Operations**: Efficient live data storage

### 2. New Capabilities
- **Cross-Session Analysis**: Compare multiple sessions
- **Historical Trends**: Time-based analysis across sessions
- **Advanced Filtering**: Search sessions by network, date, performance
- **Data Relationships**: Formal links between configurations and results

### 3. Improved Reliability
- **ACID Compliance**: Data consistency during concurrent operations
- **Transaction Safety**: Rollback on errors
- **Data Validation**: Database-level constraints
- **Backup Strategy**: File system backup for critical data

### 4. Scalability
- **Efficient Storage**: Normalized data structure
- **Query Optimization**: Database indexes for fast access
- **Memory Management**: Lazy loading and pagination
- **Cleanup Automation**: Automated old data removal

## Migration Strategy

### Backward Compatibility
- File-based operations maintained alongside database
- Existing JSON files still readable
- Gradual migration approach for old sessions

### Development Workflow
1. **Phase 1**: Database layer with parallel file operations ✓
2. **Phase 2**: New API endpoints leveraging database ✓
3. **Phase 3**: Frontend integration with new endpoints
4. **Phase 4**: Performance optimization and cleanup features

## Testing

Run the database implementation test:
```bash
cd backend
python test_database_implementation.py
```

This validates:
- Database initialization
- Session and configuration management
- Live data and analytics storage
- Network metadata handling
- API compatibility

## Database Location

- **Default Path**: `backend/traffic_simulator.db`
- **Format**: SQLite 3.x
- **Size**: Automatically managed with cleanup utilities
- **Backup**: Recommended periodic backup of .db file

## Dependencies

Added to `requirements.txt`:
- `SQLAlchemy==2.0.21` - ORM and database abstraction
- `alembic==1.12.0` - Database migrations (future use)

## Configuration

Database path can be customized in `DatabaseService` constructor:
```python
db_service = DatabaseService("/custom/path/to/database.db")
```

The system automatically creates all required tables on first startup.
