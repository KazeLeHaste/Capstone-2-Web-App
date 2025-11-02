# OSM Web Wizard Launch Fix - Technical Summary

## Issue Description
The "Create New Network with OSM" feature in the network selection page was failing to launch the OSM Web Wizard when using the packaged `TrafficSimulator.exe`, but worked correctly when using `start.bat` in development mode.

**Error Message:** "OSM Web Wizard failed to start"

## Root Cause Analysis

### The Problem
In the packaged application (PyInstaller frozen executable), `sys.executable` returns the path to `TrafficSimulator.exe` instead of a Python interpreter. The original code in `osm_service.py` was attempting to run:

```python
cmd = [sys.executable, str(wizard_script), "--port", str(self.wizard_port)]
```

This resulted in trying to execute:
```
TrafficSimulator.exe osmWebWizard.py --port 8010
```

Which fails because:
1. `TrafficSimulator.exe` is not a Python interpreter
2. It cannot execute Python scripts like `osmWebWizard.py`

### Why It Worked in Development
In development mode, `sys.executable` correctly points to the Python interpreter (e.g., `.venv\Scripts\python.exe`), so the command works as expected.

## Solution Implemented

### Changes Made to `backend/osm_service.py`

#### 1. Added `get_python_executable()` Method
```python
def get_python_executable(self) -> str:
    """
    Get the appropriate Python executable for running SUMO tools
    
    In frozen/packaged apps, sys.executable points to the app executable,
    not a Python interpreter. We need to find the system Python.
    
    Returns:
        Path to Python executable
    """
    # Check if running in frozen/packaged mode
    if app_config.is_frozen:
        # In frozen mode, sys.executable is the app .exe, not Python
        # Try to find system Python
        python_exe = shutil.which('python.exe') or shutil.which('python')
        
        if python_exe:
            print(f"Found system Python for frozen app: {python_exe}")
            return python_exe
        else:
            # Fallback: try common Python installation paths
            common_python_paths = [
                Path(r"C:\Users") / os.environ.get('USERNAME', '') / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "python.exe",
                Path(r"C:\Users") / os.environ.get('USERNAME', '') / "AppData" / "Local" / "Programs" / "Python" / "Python312" / "python.exe",
                Path(r"C:\Users") / os.environ.get('USERNAME', '') / "AppData" / "Local" / "Programs" / "Python" / "Python311" / "python.exe",
                Path(r"C:\Python313\python.exe"),
                Path(r"C:\Python312\python.exe"),
                Path(r"C:\Python311\python.exe"),
            ]
            
            for py_path in common_python_paths:
                if py_path.exists():
                    print(f"Found Python at common path: {py_path}")
                    return str(py_path)
            
            raise FileNotFoundError(
                "Could not find Python executable. Please ensure Python is installed and added to PATH."
            )
    else:
        # In development mode, use the current Python interpreter
        return sys.executable
```

#### 2. Updated `launch_osm_wizard()` Method
Modified the command construction to use the new method and added environment variable setup:

```python
# Get the appropriate Python executable
try:
    python_exe = self.get_python_executable()
except FileNotFoundError as e:
    return {
        'success': False,
        'error': str(e),
        'details': 'Python is required to run OSM Web Wizard'
    }

# Prepare command to launch OSM Web Wizard
cmd = [
    python_exe,  # Use appropriate Python interpreter
    str(wizard_script),
    "--port", str(self.wizard_port)
]

print(f"Launching OSM Web Wizard with command: {' '.join(cmd)}")
print(f"Working directory: {self.osm_scenarios_dir}")
print(f"Python executable: {python_exe}")
print(f"Is frozen: {app_config.is_frozen}")

# Prepare environment variables
# Add SUMO_HOME to environment so osmWebWizard.py can find SUMO tools
env = os.environ.copy()
if app_config.sumo_home:
    env['SUMO_HOME'] = str(app_config.sumo_home)
    print(f"Set SUMO_HOME: {app_config.sumo_home}")

# Add SUMO tools to PYTHONPATH so imports work
if app_config.sumo_tools_path:
    python_path = env.get('PYTHONPATH', '')
    if python_path:
        env['PYTHONPATH'] = f"{app_config.sumo_tools_path}{os.pathsep}{python_path}"
    else:
        env['PYTHONPATH'] = str(app_config.sumo_tools_path)
    print(f"Set PYTHONPATH: {env['PYTHONPATH']}")

# Launch the process in the osm_scenarios directory
self.wizard_process = subprocess.Popen(
    cmd,
    cwd=str(self.osm_scenarios_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env,  # Pass environment with SUMO_HOME and PYTHONPATH
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
)
```

## Testing Results

### Test 1: Packaged Application (TrafficSimulator.exe)
```
Testing OSM Web Wizard launch...
Status Code: 200
Response: {
    'message': 'OSM Web Wizard launched successfully', 
    'port': 8010, 
    'process_id': 12220, 
    'success': True, 
    'url': 'http://localhost:8010'
}
✓ SUCCESS: OSM Web Wizard launched successfully!
```

**Python executable used:** `C:\Users\kgaqu\AppData\Local\Programs\Python\Python313\python.exe`
**Is frozen:** True
**SUMO_HOME:** `C:\Users\kgaqu\OneDrive\Documents\4th Year\Capstone 2\v10\dist\TrafficSimulator\sumo`

### Test 2: Development Mode (start.bat)
```
Testing OSM Web Wizard launch...
Status Code: 200
Response: {
    'message': 'OSM Web Wizard launched successfully', 
    'port': 8010, 
    'process_id': 5712, 
    'success': True, 
    'url': 'http://localhost:8010'
}
✓ SUCCESS: OSM Web Wizard launched successfully!
```

**Python executable used:** `C:\Users\kgaqu\OneDrive\Documents\4th Year\Capstone 2\v10\.venv\Scripts\python.exe`
**Is frozen:** False
**SUMO_HOME:** `C:\Program Files (x86)\Eclipse\Sumo`

## Key Improvements

1. **Automatic Python Detection:** The fix automatically detects the appropriate Python interpreter based on the execution context
2. **Fallback Mechanism:** If Python is not in PATH, the code checks common installation locations
3. **Environment Configuration:** Properly sets `SUMO_HOME` and `PYTHONPATH` to ensure `osmWebWizard.py` can find required SUMO tools
4. **Backward Compatibility:** The fix maintains full compatibility with development mode
5. **Enhanced Logging:** Added detailed logging to help diagnose any future issues

## Files Modified
- `backend/osm_service.py` (Lines 84-210)
  - Added `get_python_executable()` method
  - Updated `launch_osm_wizard()` to use the new method
  - Added environment variable configuration for SUMO_HOME and PYTHONPATH

## Rebuild Required
After implementing the fix, the application was rebuilt using:
```bash
pyinstaller --noconfirm traffic-simulator.spec
robocopy "C:\Program Files (x86)\Eclipse\Sumo" "dist\TrafficSimulator\sumo" /E
```

## Dependencies
- **System Python:** Users must have Python installed on their system (added to PATH or in common installation locations)
- **SUMO:** The bundled SUMO installation at `dist/TrafficSimulator/sumo/` must include the `tools/osmWebWizard.py` script

## Future Considerations
- Could bundle a minimal Python interpreter with the package if system Python is not guaranteed to be available
- Could add a settings option to specify a custom Python path
- Consider adding more detailed error messages if Python is not found

## Date Fixed
November 2, 2025

## Verification Status
✅ Tested and verified working in both packaged and development modes
✅ OSM Web Wizard launches successfully
✅ Port 8010 responds to connections
✅ No regression in development mode functionality
