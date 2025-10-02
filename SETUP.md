# Traffic Simulator Development Setup

## Prerequisites

Before running the Traffic Simulator, ensure you have the following installed:

### Required Software

1. **Python 3.8+**
   - Download from: https://www.python.org/downloads/
   - Make sure Python is added to your PATH

2. **Node.js 14+**
   - Download from: https://nodejs.org/
   - Includes npm package manager

3. **SUMO (Simulation of Urban MObility)**
   - Download from: https://sumo.dlr.de/docs/Installing/index.html
   - **Important**: Add SUMO to your system PATH
   - **Required Version**: 1.19.0+ for sublane model support
   - Verify installation: Open command prompt and run `sumo --help`

### Development Tools (Optional but Recommended)

- **VS Code** with extensions:
  - Python
  - Prettier
  - Tailwind CSS IntelliSense
- **Git** for version control

## Quick Start Guide

### 1. Backend Setup (Flask + SQLite)

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already active)
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Verify SUMO installation
sumo --help

# The SQLite database (traffic_simulator.db) will be created automatically on first run
```

### 2. Frontend Setup (React)

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server (with proxy to backend)
npm start
```

### 3. Running the Application

#### Method 1: Using VS Code Tasks (Recommended)
VS Code tasks are configured for this project:
- **Start Backend Server**: Runs Flask app with database initialization
- **Start Frontend Server**: Runs React development server with hot reload
- **Install Frontend Dependencies**: Runs npm install in frontend directory

Access via: `Ctrl+Shift+P` → "Tasks: Run Task" → Select desired task

#### Method 2: Manual Startup

**Terminal 1 - Backend (Flask + SQLite):**
```bash
cd backend
# Ensure virtual environment is activated
.\.venv\Scripts\python.exe app.py
```

**Terminal 2 - Frontend (React):**
```bash
cd frontend
npm start
```

#### Method 3: Production Build
```bash
# Build optimized frontend
cd frontend
npm run build

# Serve built frontend (optional - Flask can serve static files)
npx serve -s build -l 3000
```

### 4. Access the Application

- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **WebSocket**: ws://localhost:5000/socket.io/
- **Database**: SQLite file at `backend/traffic_simulator.db`

### 5. Application Workflow

1. **Home Page** (http://localhost:3000) - System status and onboarding
2. **Configuration** → Set SUMO parameters (timing, vehicles, traffic control, sublane model)
3. **Network Selection** → Choose from 7 Philippine traffic scenarios
4. **Simulation** → Launch SUMO with real-time monitoring and smooth lane changing
5. **Analytics** → View KPIs, charts, and AI recommendations

## Troubleshooting

### Common Issues

#### 1. SUMO Not Found
**Error**: "SUMO not detected" or "sumo command not found"

**Solution**:
- Ensure SUMO is installed correctly
- Add SUMO bin directory to your system PATH
- Restart your terminal/VS Code after PATH changes
- Test with: `sumo --help`

#### 2. Port Already in Use
**Error**: "Port 3000/5000 is already in use"

**Solution**:
- Kill existing processes using those ports
- Or change ports in configuration files

#### 3. Python Virtual Environment Issues
**Error**: Python packages not found

**Solution**:
- Ensure virtual environment is activated
- Use the full path: `.venv\Scripts\python.exe`
- Reinstall packages if needed

#### 4. Frontend Dependencies
**Error**: Node modules missing

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 5. WebSocket Connection Failed
**Error**: Real-time updates not working

**Solution**:
- Ensure backend is running before starting frontend
- Check firewall settings for ports 3000 and 5000
- Verify Flask-SocketIO is properly configured
- Check browser console for WebSocket connection errors

#### 6. Database Issues
**Error**: SQLite database errors or session data missing

**Solution**:
- Database is created automatically on first backend startup
- Delete `backend/traffic_simulator.db` to reset database
- Check file permissions in backend directory
- Ensure SQLAlchemy version compatibility (2.0+)

#### 7. Multi-Session Conflicts
**Error**: Sessions interfering with each other

**Solution**:
- Each session uses unique ports (8813, 8814, etc.)
- Check `backend/sessions/` directory for session isolation
- Restart backend to clear stuck sessions
- Ensure adequate system resources for concurrent simulations

### Windows-Specific Notes

- Use backslashes `\` in paths for Windows commands
- PowerShell may require execution policy changes for scripts
- Some antivirus software may block local servers

### Performance Tips

1. **For Development**:
   - Use Chrome DevTools for frontend debugging
   - Enable Flask debug mode (already enabled in development)
   - Monitor console for WebSocket connection status

2. **For Simulation**:
   - Start with smaller networks for testing
   - Adjust simulation step length for performance
   - Use appropriate traffic density settings

## Development Workflow

### 1. First-Time Setup
1. Follow the prerequisites installation
2. Run the quick start guide
3. Test with a sample simulation

### 2. Daily Development
1. Start VS Code in the project root
2. Use the "Start Traffic Simulator" task
3. Make changes and test in browser
4. Both frontend and backend support hot reloading

### 3. Testing Changes
1. Start with the home page and onboarding
2. Test network selection with sample data
3. Configure a basic simulation
4. Verify real-time visualization works
5. Check analytics and data export

## Project Structure Reference

```
traffic-simulator/
├── backend/                        # Flask backend with database
│   ├── app.py                     # Main Flask app (1662 lines) - comprehensive API
│   ├── enhanced_session_manager.py# Multi-session support (645 lines)
│   ├── simulation_manager.py      # Core workflow logic (3387 lines) with sublane model
│   ├── analytics_engine.py        # KPI analysis (1655 lines)
│   ├── websocket_handler.py       # Real-time communication
│   ├── multi_session_api.py       # V2 API endpoints
│   ├── osm_service.py             # OSM scenario management
│   ├── traffic_simulator.db       # SQLite database (auto-created)
│   ├── requirements.txt           # Python dependencies
│   ├── database/                  # Database layer
│   │   ├── models.py              # 8 SQLAlchemy models
│   │   └── service.py             # Database operations (787 lines)
│   ├── networks/                  # Philippine traffic scenarios
│   │   ├── bayanan_area/          # Complete SUMO network + metadata
│   │   ├── jollibee_molino_area/  # Complete SUMO network + metadata
│   │   ├── perpetual_molino_area/ # Complete SUMO network + metadata
│   │   ├── sm_bacoor_area/        # Complete SUMO network + metadata
│   │   ├── sm_molino_area/        # Complete SUMO network + metadata
│   │   ├── st_dominic_area/       # Complete SUMO network + metadata
│   │   └── statesfield_area/      # Complete SUMO network + metadata
│   └── sessions/                  # Dynamic session directories
├── frontend/                      # Modern React application
│   ├── src/
│   │   ├── components/           # 17 React components
│   │   ├── pages/               # 5 main pages (workflow-based)
│   │   ├── contexts/            # React context providers
│   │   └── utils/              # API clients and helpers
│   ├── package.json            # Dependencies (React 18, Socket.io, Charts)
│   └── public/                 # Static assets
├── osm_importer/               # Network import utility
│   ├── osm_scenario_importer.py# Tool for importing new OSM networks (1772 lines)
│   ├── osm_scenarios/          # Source OSM scenarios (7 Philippine areas)
│   └── README.md              # Import tool documentation
├── .venv/                      # Python virtual environment
├── README.md                   # Updated project documentation
└── SETUP.md                   # This detailed setup guide
```

## Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review browser console for JavaScript errors
3. Check Python terminal for backend errors
4. Verify SUMO installation with `sumo --help`
5. Ensure all prerequisites are properly installed

## Next Steps

Once you have the application running:

1. **System Check**: Verify backend and SUMO status on home page (http://localhost:3000)
2. **Onboarding Tour**: Click "Take the Tour" for guided workflow explanation
3. **Configuration First**: Start at /configuration to set SUMO parameters
4. **Network Selection**: Choose from 6 Philippine traffic scenarios (/network-selection)
5. **Live Simulation**: Launch and monitor simulation with real-time data (/simulation)
6. **Analytics Dashboard**: View comprehensive KPIs and AI recommendations (/analytics)
7. **Multi-Session Testing**: Try running multiple concurrent simulations
8. **Data Export**: Test PDF report generation and data downloads

### Key Features to Test:

- **Real-time Updates**: WebSocket data streaming during simulation
- **Sublane Model**: Smooth vehicle lane changing instead of teleporting
- **Traffic Control**: Fixed timer vs adaptive traffic light configurations  
- **Vehicle Types**: Enable/disable different vehicle categories
- **Session Isolation**: Multiple simulations running simultaneously
- **Database Persistence**: Session data stored and retrievable
- **Analytics Engine**: KPI calculations and recommendation generation
- **OSM Import**: Import new scenarios from OpenStreetMap using the osm_importer tool

Happy simulating! 🚗📊
