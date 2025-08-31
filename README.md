# Traffic Simulator Web Application

A web-based traffic simulator integrating SUMO (Simulation of Urban MObility) with a Python Flask backend and React frontend.

## Project Overview

This application provides an intuitive web interface for traffic simulation, featuring:
- Welcoming home page with project introduction
- Guided onboarding flow for first-time users
- SUMO integration for realistic traffic simulation
- Live simulation data visualization
- 2D map view displaying real-time traffic state

## Architecture

- **Backend**: Python Flask server for SUMO integration and API endpoints
- **Frontend**: React application for user interface and visualization
- **Simulation**: SUMO traffic simulator running as subprocess

## Features

### Home Page & Introduction
- Clear explanation of project goals and traffic simulation benefits
- Integration overview between SUMO and web application
- User-friendly landing experience

### Onboarding & Guided Flow
- Step-by-step guide for first-time users
- Workflow explanation: network selection → configuration → simulation → analytics
- Interactive tutorial system

### Navigation & UI Structure
- Intuitive navigation between major sections
- Clear progression through simulation workflow
- Beginner-friendly interface design

### Simulation & Visualization
- Backend SUMO process management
- Live simulation data retrieval via WebSocket
- 2D map visualization of traffic state
- Real-time vehicle position updates

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- SUMO installation
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

1. **Home Page**: Start at the landing page to understand the application
2. **Onboarding**: Follow the guided tour for first-time setup
3. **Network Selection**: Choose from predefined SUMO networks
4. **Configuration**: Set simulation parameters
5. **Launch Simulation**: Start SUMO and view live traffic data
6. **Analytics**: Monitor simulation metrics and results

## Project Structure

```
traffic-simulator/
├── backend/                 # Flask backend
│   ├── app.py              # Main Flask application
│   ├── sumo_controller.py  # SUMO integration logic
│   ├── websocket_handler.py# WebSocket communication
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/         # Page components
│   │   └── utils/         # Utility functions
│   └── package.json       # Node.js dependencies
├── sumo_data/             # SUMO configuration files
│   ├── networks/          # Network definitions
│   └── scenarios/         # Simulation scenarios
└── README.md              # This file
```

## Development Guidelines

### Backend Development
- Flask serves API endpoints and manages SUMO processes
- WebSocket connections provide real-time data streaming
- Error handling includes detailed logging and user feedback
- SUMO communication via TraCI (Traffic Control Interface)

### Frontend Development
- React components follow functional programming patterns
- State management using React hooks
- Real-time updates via WebSocket connections
- Responsive design for various screen sizes

### SUMO Integration
- Subprocess management for SUMO instances
- TraCI API for simulation control and data retrieval
- Network and scenario file management
- Real-time vehicle and network state monitoring

## Troubleshooting

### Common Issues

1. **SUMO not found**: Ensure SUMO is installed and in your PATH
2. **Port conflicts**: Check that ports 3000 and 5000 are available
3. **WebSocket connection failed**: Verify backend is running before frontend
4. **Missing dependencies**: Run `pip install -r requirements.txt` and `npm install`

### Debug Mode
- Backend: Set `FLASK_DEBUG=1` environment variable
- Frontend: Development server includes hot reloading
- SUMO: Check console output for simulation errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues:
- Check the troubleshooting section
- Review SUMO documentation
- Open an issue on GitHub

---

Built with ❤️ for traffic simulation and urban planning research.
