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
   - Verify installation: Open command prompt and run `sumo --help`

### Development Tools (Optional but Recommended)

- **VS Code** with extensions:
  - Python
  - Prettier
  - Tailwind CSS IntelliSense
- **Git** for version control

## Quick Start Guide

### 1. Backend Setup (Flask)

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies (already done via VS Code)
# The virtual environment is located at: .venv/Scripts/python.exe

# Verify SUMO installation
sumo --help
```

### 2. Frontend Setup (React)

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm start
```

### 3. Running the Application

#### Method 1: Using VS Code Tasks (Recommended)
1. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type "Tasks: Run Task"
3. Select "Start Traffic Simulator"

#### Method 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
.venv\Scripts\python.exe app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 4. Access the Application

- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **WebSocket**: ws://localhost:5000

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
- Check firewall settings
- Verify both applications are using correct ports

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
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── sumo_controller.py  # SUMO integration
│   ├── websocket_handler.py# Real-time communication
│   └── requirements.txt    # Python dependencies
├── frontend/               # React web application
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/         # Main page components
│   │   ├── utils/         # Helper functions
│   │   └── App.js         # Main application
│   └── package.json       # Node.js dependencies
├── sumo_data/             # SUMO simulation files
│   ├── networks/          # Network definitions (.net.xml)
│   └── scenarios/         # Simulation scenarios (.sumocfg)
└── README.md              # This documentation
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

1. **Take the Onboarding Tour**: Click "Take the Tour" on the home page
2. **Try Sample Simulation**: Use the predefined network and scenario
3. **Explore Features**: Test each section (Network → Configuration → Simulation → Analytics)
4. **Customize**: Modify configurations and observe changes
5. **Export Data**: Test the analytics export functionality

Happy simulating! 🚗📊
