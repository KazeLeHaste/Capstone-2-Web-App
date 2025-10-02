# Quick Start Guide - Traffic Simulator

**Get up and running in 5 minutes!** 🚀

## ⚡ Super Quick Start (Windows)

### 1. Prerequisites Check
```powershell
# Verify installations
python --version    # Should be 3.8+
node --version      # Should be 14+
sumo --help         # Should show SUMO help (if this fails, install SUMO first)
```

### 2. One-Command Setup
```powershell
# Clone, setup, and run everything
git clone <repository-url>
cd traffic-simulator
```

**Backend (Terminal 1):**
```powershell
cd backend
.\.venv\Scripts\activate    # Activate virtual environment
pip install -r requirements.txt
python app.py
```

**Frontend (Terminal 2):**
```powershell
cd frontend
npm install
npm start
```

### 3. Access Application
- 🌐 **Open**: http://localhost:3000
- ✅ **Check Status**: Green indicators on home page
- 🎯 **Start**: Click "Take the Tour" for guided walkthrough

---

## 🚀 5-Minute Demo Walkthrough

### Step 1: Configuration (30 seconds)
1. Go to **Configuration** tab
2. Keep default settings:
   - Duration: 30 minutes
   - Traffic Scale: 1.0x
   - Sublane Model: ✅ Enabled (0.8m resolution)
3. Click **Save Configuration**

### Step 2: Network Selection (30 seconds)
1. Go to **Network Selection** tab
2. Choose **"SM Molino Area"** (good for demo - 20 edges, 19 junctions)
3. Click **Select Network**

### Step 3: Launch Simulation (30 seconds)
1. Go to **Simulation** tab
2. Click **"Launch SUMO Simulation"**
3. Choose **"Enable GUI"** for visual experience
4. SUMO window opens automatically

### Step 4: Watch Live Data (3 minutes)
- 📊 **Real-time KPIs** update every 10 seconds
- 🚗 **Smooth lane changes** - vehicles glide between lanes (no teleporting!)
- 📈 **Live charts** show traffic flow, speed, density
- 🗺️ **Map view** displays traffic patterns

### Step 5: Analytics (30 seconds)
1. Go to **Analytics** tab after simulation
2. View comprehensive KPIs and AI recommendations
3. Export PDF report or download raw data

**Total Time: ~5 minutes** ✅

---

## 🎯 Key Features to Experience

### 🚗 Sublane Model in Action
- **Before**: Vehicles "teleported" between lanes instantly
- **After**: Smooth, realistic lane transitions taking 2-3 seconds
- **See it**: Watch SUMO GUI during simulation - vehicles glide naturally

### 📊 Real-Time Analytics
- Live KPI updates every 10 seconds
- 20+ traffic metrics (speed, flow, density, emissions)
- Interactive charts with zoom and hover details

### 🏢 Philippine Traffic Scenarios
- 7 real-world scenarios based on OpenStreetMap
- Authentic traffic patterns from Philippine locations
- Multiple vehicle types (cars, buses, trucks, motorcycles)

### 🔄 Multi-Session Support
- Run multiple simulations simultaneously
- Compare different configurations side-by-side
- Each session isolated with unique ports (8813+)

---

## 🛠️ Common Issues & Solutions

### SUMO Not Found
```powershell
# Add SUMO to PATH (Windows)
# 1. Find SUMO installation (usually C:\Program Files (x86)\Eclipse\Sumo\bin)
# 2. Add to system PATH environment variable
# 3. Restart terminal and test: sumo --help
```

### Port Already in Use
```powershell
# Kill processes using ports 3000 or 5000
netstat -ano | findstr :3000
taskkill /PID <process_id> /F
```

### WebSocket Connection Failed
- ✅ Start backend first, then frontend
- ✅ Check http://localhost:5000/api/status shows "online"
- ✅ Refresh browser if connection issues persist

### Virtual Environment Issues
```powershell
# If .venv doesn't exist, create it:
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📱 Next Steps After Quick Start

### Explore Advanced Features
1. **Multi-Session Testing**: Launch multiple simulations simultaneously
2. **Traffic Control**: Try adaptive vs fixed traffic light timing
3. **Vehicle Types**: Enable/disable different vehicle categories
4. **Network Comparison**: Test all 7 Philippine scenarios
5. **Analytics Deep Dive**: Explore all 20+ KPIs and AI recommendations

### Import New Networks
```powershell
# Use the OSM importer for new scenarios
cd osm_importer
python osm_scenario_importer.py --list
python osm_scenario_importer.py --import "New_Scenario" --name "my_scenario"
```

### Performance Tuning
- Adjust simulation step length (0.1 to 2.0 seconds)
- Modify traffic scale (0.5x to 3.0x)
- Configure lateral resolution (0.4 to 1.6m)

---

## 🆘 Get Help

### Documentation
- **README.md**: Complete feature overview and architecture
- **SETUP.md**: Detailed installation and troubleshooting
- **PROJECT_STATUS.md**: Current capabilities and metrics
- **osm_importer/README.md**: Network import guide

### Quick Checks
- ✅ Backend status: http://localhost:5000/api/status
- ✅ SUMO working: `sumo --help` in terminal
- ✅ Database created: Look for `backend/traffic_simulator.db`
- ✅ Networks available: Check `backend/networks/` has 7 folders

### Community
- Check GitHub issues for common problems
- Review SUMO documentation at sumo.dlr.de
- Ensure you have SUMO 1.19.0+ for sublane model support

---

**Happy Simulating!** 🚗📊🎯

*This quick start gets you from zero to running simulations in under 5 minutes.*