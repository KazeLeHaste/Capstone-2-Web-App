# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File for Traffic Simulator

This spec file packages the Traffic Simulator backend with all dependencies
into a single distributable application.

Build command:
    pyinstaller traffic-simulator.spec

Output:
    dist/TrafficSimulator/  (folder with executable and dependencies)

Author: Traffic Simulator Team
Date: October 2025
"""

import os
import sys
from pathlib import Path

# Get project paths
project_root = Path(os.getcwd())
backend_dir = project_root / 'backend'
frontend_build = project_root / 'frontend' / 'build'

# Verify paths exist
if not backend_dir.exists():
    raise FileNotFoundError(f"Backend directory not found: {backend_dir}")

print(f"Project root: {project_root}")
print(f"Backend dir: {backend_dir}")
print(f"Frontend build: {frontend_build}")

block_cipher = None

# Analysis: Find all Python files and dependencies
a = Analysis(
    # Main entry point
    [str(backend_dir / 'app.py')],
    
    # Additional paths to search for imports
    pathex=[str(backend_dir), str(project_root)],
    
    # Binary files (none needed for pure Python)
    binaries=[],
    
    # Data files to include
    datas=[
        # Network scenario files
        (str(backend_dir / 'networks'), 'networks'),
        
        # Frontend React build
        (str(frontend_build), 'frontend/build') if frontend_build.exists() else (str(backend_dir), 'frontend/build'),
        
        # Database package
        (str(backend_dir / 'database'), 'database'),
        
        # Utils package
        (str(backend_dir / 'utils'), 'utils'),
        
        # Configuration file
        (str(backend_dir / 'config.py'), '.'),
        
        # GUI settings file for SUMO
        (str(backend_dir / 'gui_settings.xml'), '.'),
    ],
    
    # Hidden imports (modules not auto-detected)
    hiddenimports=[
        # Flask and extensions
        'flask',
        'flask_cors',
        'flask_socketio',
        
        # SocketIO dependencies
        'engineio',
        'engineio.async_drivers.threading',
        'socketio',
        'python_socketio',
        
        # Database
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm',
        'sqlalchemy.sql',
        'sqlalchemy.sql.default_comparator',
        
        # Other dependencies
        'requests',
        'xml.etree.ElementTree',
        'pathlib',
        'json',
        'uuid',
        'threading',
        'tempfile',
        'datetime',
        'subprocess',
        'shutil',
        'webbrowser',
    ],
    
    # Hooks
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    
    # Modules to exclude (reduce size)
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'test',
        'unittest',
        'pytest',
    ],
    
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: Compress Python bytecode
pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

# EXE: Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],  # Don't bundle everything in one file (use COLLECT instead)
    exclude_binaries=True,  # Keep binaries separate for faster updates
    name='TrafficSimulator',
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,  # Don't strip symbols
    upx=True,  # Compress with UPX
    console=True,  # Keep console window for logging (set False for production)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'icon.ico') if (project_root / 'icon.ico').exists() else None,
)

# COLLECT: Gather all files into distribution folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TrafficSimulator'
)

print("\n" + "=" * 70)
print("PyInstaller Configuration Complete")
print("=" * 70)
print(f"Output will be in: dist/TrafficSimulator/")
print(f"Main executable: dist/TrafficSimulator/TrafficSimulator.exe")
print("=" * 70)
