# Traffic Simulator Web Application

A comprehensive web-based traffic simulation platform integrating SUMO (Simulation of Urban MObility) with a modern full-stack architecture featuring Python Flask backend, React frontend, and SQLite database.

## Project Overview

This application provides an enterprise-grade web interface for traffic simulation with advanced features:
- **Multi-session support** - Run multiple concurrent simulations
- **Database-driven architecture** - SQLite database for session management and analytics
- **Configuration-first workflow** - Configure parameters before network selection
- **Real-time visualization** - Live WebSocket data streaming and 2D map views
- **Advanced analytics** - Comprehensive KPI analysis with AI-powered recommendations
- **OSM network support** - 7 predefined Philippine traffic scenarios with sublane model for smooth lane changing

## Architecture

- **Backend**: Python Flask server with SQLite database and enhanced session management
- **Frontend**: React application with real-time WebSocket communication
- **Simulation**: SUMO traffic simulator with sublane model for realistic lane changing
- **Database**: SQLite with comprehensive schema for sessions, analytics, and KPIs
- **Multi-session**: Concurrent simulations with isolated resources and dynamic port allocation
- **OSM Import**: Automated import system for OpenStreetMap-based traffic scenarios

## Core Features

### SUMO Sublane Model ⭐
- **Smooth Lane Changes**: Vehicles transition gradually between lanes instead of teleporting
- **Realistic Lateral Movement**: Continuous vehicle positioning with 0.8m lateral resolution
- **Multi-Vehicle Lane Sharing**: Support for motorcycles and bicycles sharing lanes
- **Enhanced Visual Fidelity**: Realistic lane-changing maneuvers in SUMO GUI
### Adaptive Traffic Control System
- **Traffic-Responsive Control**: Automatically prioritizes busy roads with longer green times
- **Adaptive vs Fixed Control**: Choose between adaptive (responds to traffic demand) or fixed timing
- **Smart Junction Enhancement**: Convert priority intersections to adaptive traffic lights
- **Easy Configuration**: Simple UI controls with real-time parameter adjustment
- **SUMO Native Integration**: Uses netconvert for robust, stable traffic light modification

### Multi-Session Management
- **Concurrent Simulations**: Run multiple traffic simulations simultaneously
- **Session Isolation**: Each session gets dedicated resources and temporary directories
- **Database Integration**: All session data stored in SQLite with comprehensive tracking
- **Dynamic Resource Allocation**: Automatic port assignment (8813+) and cleanup

### Configuration-First Workflow
- **Parameter Setup**: Configure SUMO parameters before network selection
- **Traffic Control**: Fixed timer and adaptive traffic light management
- **Vehicle Configuration**: Customize vehicle types (passenger, bus, truck, motorcycle)
- **Network Preservation**: Original networks remain untouched, modifications applied to copies

### Real-Time Analytics & Visualization
- **Live Data Streaming**: WebSocket-based real-time simulation data
- **Comprehensive KPIs**: 20+ traffic metrics including speed, density, emissions
- **AI Recommendations**: Rule-based traffic optimization suggestions
- **Interactive Charts**: Time series analysis and comparative visualizations
- **Data Export**: PDF reports and data download capabilities

### Philippine Traffic Scenarios
- **7 OSM-Based Networks**: Bayanan Area, Jollibee Molino, Perpetual Molino, SM Bacoor, SM Molino, St. Dominic, Statesfield
- **Realistic Traffic Patterns**: Imported from OpenStreetMap with authentic vehicle flows
- **Multiple Vehicle Types**: Support for cars, buses, trucks, motorcycles
- **Configurable Parameters**: Modify traffic intensity, signal timing, and road conditions
- **Automated Import System**: Easy import of new OSM scenarios via `osm_importer` tool

## Quick Start

🚀 **New to the project?** Check out [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide!

### Prerequisites
- Python 3.8+
- Node.js 14+
- SUMO installation (1.19.0+ for sublane model support)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd traffic-simulator
   ```

2. **Setup Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start Backend Server**
   ```bash
   cd backend
   python app.py
   ```
   Backend runs on: http://localhost:5000

2. **Start Frontend Development Server**
   ```bash
   cd frontend
   npm start
   ```
   Frontend runs on: http://localhost:3000

### Usage Guide

1. **Home Page**: Start at the landing page with system status overview
2. **Onboarding**: Follow the guided tour for first-time users (configuration → network → simulation → analytics)
3. **Configuration**: Set SUMO parameters (timing, vehicles, traffic control, sublane model) first
4. **Network Selection**: Choose from 7 Philippine traffic scenarios
5. **Simulation Launch**: Start SUMO simulation with live visualization and smooth lane changing
6. **Analytics Dashboard**: View comprehensive KPIs, charts, and AI recommendations
7. **Data Export**: Download results as PDF reports or raw data files

## Project Structure

```
traffic-simulator/
├── backend/                        # Flask backend with database
│   ├── app.py                     # Main Flask application with comprehensive API
│   ├── enhanced_session_manager.py# Multi-session management system
│   ├── simulation_manager.py      # Core simulation workflow logic with sublane model
│   ├── analytics_engine.py        # KPI analysis and recommendations
│   ├── websocket_handler.py       # Real-time WebSocket communication
│   ├── multi_session_api.py       # V2 API endpoints for enhanced features
│   ├── osm_service.py             # OSM scenario import and management
│   ├── traffic_simulator.db       # SQLite database
│   ├── requirements.txt           # Python dependencies
│   ├── database/                  # Database models and services
│   │   ├── models.py              # SQLAlchemy models (8 core tables)
│   │   └── service.py             # Database operations layer
│   ├── networks/                  # Philippine traffic scenarios
│   │   ├── bayanan_area/          # Bayanan area network with metadata
│   │   ├── jollibee_molino_area/  # Jollibee Molino area network
│   │   ├── perpetual_molino_area/ # Perpetual Molino area network
│   │   ├── sm_bacoor_area/        # SM Bacoor area network
│   │   ├── sm_molino_area/        # SM Molino area network
│   │   ├── st_dominic_area/       # St. Dominic area network
│   │   └── statesfield_area/      # Statesfield area network
│   └── sessions/                  # Dynamic session directories (auto-created)
├── frontend/                      # React frontend with modern UI
│   ├── src/
│   │   ├── components/           # Reusable React components
│   │   │   ├── KPIDashboard.js   # Analytics dashboard component
│   │   │   ├── AnalyticsCharts.js# Chart visualizations
│   │   │   ├── MapVisualization.js# 2D traffic visualization
│   │   │   ├── OnboardingModal.js # User onboarding and tutorial
│   │   │   ├── SessionComparison.js# Multi-session comparison
│   │   │   ├── OSMScenarioScanner.js# OSM scenario management
│   │   │   └── ...               # 17 total components
│   │   ├── pages/               # Main application pages
│   │   │   ├── HomePage.js       # Landing page with system status
│   │   │   ├── ConfigurationPage.js# Parameter configuration with sublane settings
│   │   │   ├── NetworkSelectionPage.js# Network selection with OSM indicators
│   │   │   ├── SimulationPage.js # Live simulation monitoring
│   │   │   └── AnalyticsPage.js  # Post-simulation analytics
│   │   └── utils/               # Utility functions and API clients
│   └── package.json            # Node.js dependencies (React, Socket.io, Charts)
├── osm_importer/               # OSM scenario import utility
│   ├── osm_scenario_importer.py# Import tool for new networks (1772 lines)
│   ├── osm_scenarios/          # Source OSM scenarios (7 Philippine areas)
│   └── README.md              # Import tool documentation
├── README.md                   # This comprehensive documentation
├── QUICKSTART.md              # 5-minute setup guide  
├── SETUP.md                   # Detailed installation instructions
├── PROJECT_STATUS.md          # Current capabilities and metrics
└── DEPLOYMENT_STRATEGY.md     # Packaging and deployment options
```

## Technical Specifications

### Database Schema
- **Sessions**: Multi-session management with metadata and status tracking
- **Configurations**: SUMO parameters, vehicle types, and traffic control settings
- **Live Data**: Real-time simulation metrics streamed every 10 steps
- **KPIs**: 20+ key performance indicators including traffic flow and emissions
- **Analytics**: Time series data, trip information, and AI recommendations
- **Networks**: Metadata for Philippine traffic scenarios with vehicle type support

### Backend Architecture
- **Enhanced Session Manager**: Concurrent simulation support with resource isolation
- **Simulation Manager**: Configuration-first workflow with sublane model and network copying
- **Analytics Engine**: Post-simulation KPI calculation and rule-based recommendations  
- **Database Service**: Comprehensive SQLAlchemy ORM layer
- **WebSocket Handler**: Real-time data broadcasting to connected clients
- **OSM Service**: Automated import and management of OpenStreetMap scenarios

### Frontend Technology Stack
- **React 18.2**: Modern functional components with hooks
- **Socket.io Client**: Real-time WebSocket communication
- **React Router**: Multi-page application navigation
- **Recharts**: Interactive data visualization and charts
- **Leaflet**: 2D map visualization for traffic networks
- **Tailwind CSS**: Responsive utility-first styling
- **Lucide React**: Consistent icon library

## System Requirements

### Minimum Requirements
- **Python**: 3.8+ with pip
- **Node.js**: 14+ with npm
- **SUMO**: Latest version (1.19.0+) with TraCI support
- **RAM**: 4GB minimum, 8GB recommended for multiple sessions
- **Storage**: 2GB free space for databases and session files

### Supported Operating Systems
- Windows 10/11 (Primary development platform)
- macOS 10.15+ (Monterey recommended)
- Linux Ubuntu 20.04+ (or equivalent distributions)

## Troubleshooting

### Common Issues

1. **SUMO not found**: Ensure SUMO is installed and added to your system PATH
2. **Port conflicts**: Verify ports 3000, 5000, and 8813+ are available
3. **WebSocket connection failed**: Start backend before frontend, check firewall settings
4. **Database errors**: Ensure SQLite permissions and SQLAlchemy 2.0+ compatibility
5. **Multi-session conflicts**: Check session isolation in `backend/sessions/` directory
6. **Missing dependencies**: Run `pip install -r requirements.txt` and `npm install`

### Debug Mode
- **Backend**: Flask runs in debug mode by default during development
- **Frontend**: React development server includes hot reloading and error overlay
- **Database**: Check `traffic_simulator.db` file permissions and integrity
- **Sessions**: Monitor `backend/sessions/` for session directory creation
- **SUMO**: Check console output for TraCI connection and simulation errors

## Database Schema

The application uses SQLite with 8 core tables:

- **`sessions`** - Multi-session management with status tracking and resource allocation
- **`configurations`** - SUMO parameters, vehicle types, and traffic control settings  
- **`live_data`** - Real-time simulation metrics streamed every 10 simulation steps
- **`kpis`** - 20+ key performance indicators including traffic flow and emissions
- **`trips`** - Individual vehicle journey data with detailed metrics
- **`time_series`** - Temporal data for trend analysis and visualization
- **`recommendations`** - AI-generated traffic optimization suggestions
- **`networks`** - Metadata for Philippine traffic scenarios with vehicle support

## API Endpoints

### Core API (v1)
- `GET /api/status` - System and simulation status
- `GET /api/networks` - Available traffic networks
- `POST /api/simulation/start` - Launch simulation
- `GET /api/simulation/data` - Real-time simulation data
- `POST /api/simulation/save-config` - Save session configuration
- `POST /api/simulation/setup-network` - Copy and configure network

### Enhanced API (v2) 
- `POST /api/v2/sessions` - Create new session with enhanced management
- `POST /api/v2/sessions/{id}/launch` - Launch specific session
- `GET /api/v2/sessions` - List all active sessions
- `DELETE /api/v2/sessions/{id}` - Clean up session resources

## Philippine Traffic Networks

7 real-world traffic scenarios imported from OpenStreetMap:

1. **Bayanan Area** - Mixed residential and commercial area with diverse traffic patterns
2. **Jollibee Molino** - Commercial area with mixed traffic patterns and restaurants
3. **Perpetual Molino** - Educational area with school traffic and pedestrian activity
4. **SM Bacoor** - Shopping mall area with high pedestrian activity  
5. **SM Molino** - Major commercial district with bus routes
6. **St. Dominic** - Church and school area with periodic congestion
7. **Statesfield** - Residential subdivision with controlled access

Each network includes realistic vehicle flows, traffic light timing, and infrastructure data with full support for the sublane model.

## Contributing

1. Fork the repository from GitHub
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code style
4. Test thoroughly with multiple scenarios and networks
5. Update documentation if needed
6. Submit a pull request with clear description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support & Documentation

For questions, issues, or contributions:
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for 5-minute setup
- **Detailed Setup**: Check [SETUP.md](SETUP.md) for comprehensive installation guide
- **Current Status**: Review [PROJECT_STATUS.md](PROJECT_STATUS.md) for latest capabilities
- **Deployment**: See [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md) for packaging options
- **OSM Import**: Check [osm_importer/README.md](osm_importer/README.md) for network import guide
- **SUMO Integration**: Consult SUMO documentation at sumo.dlr.de
- **Database Questions**: Check SQLAlchemy 2.0+ documentation
- **Bug Reports**: Open an issue on GitHub with system info and error logs

---

**Built with ❤️ for traffic simulation and urban planning research in the Philippines.**
