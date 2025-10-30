# Traffic Simulator - Installer Deployment Guide

Complete guide for building and deploying the Traffic Simulator as a standalone Windows installer with bundled SUMO.

## Overview

This deployment creates a professional Windows installer that includes:
- ✅ Traffic Simulator application (Python backend + React frontend)
- ✅ SUMO traffic simulator (bundled, no separate installation needed)
- ✅ All network scenarios and data files
- ✅ Desktop shortcuts and Start Menu integration
- ✅ Professional uninstaller

**Total installer size:** ~500-600MB (includes SUMO)

---

## Prerequisites

### Required Software

1. **Python 3.8+** with pip
2. **Node.js 14+** with npm
3. **SUMO** installed (for development and bundling)
4. **PyInstaller** for packaging Python
5. **NSIS (Nullsoft Scriptable Install System)** for creating installer

### Installation Commands

```powershell
# Install PyInstaller
pip install pyinstaller

# Install NSIS (using Chocolatey)
choco install nsis

# Or download manually from: https://nsis.sourceforge.io/Download
```

---

## Build Process

### Step 1: Prepare Frontend (5 minutes)

Build the React frontend for production:

```powershell
cd frontend
npm install
npm run build
```

**Output:** `frontend/build/` directory with optimized static files

**Verify:**
```powershell
Test-Path frontend\build\index.html
# Should return: True
```

---

### Step 2: Build Backend with PyInstaller (10-15 minutes)

Package the Python backend into a standalone executable:

```powershell
# From project root
pyinstaller traffic-simulator.spec
```

**What this does:**
- Bundles Python runtime + all dependencies
- Includes backend code, networks, and frontend build
- Creates `dist/TrafficSimulator/` folder
- Main executable: `dist/TrafficSimulator/TrafficSimulator.exe`

**Output structure:**
```
dist/TrafficSimulator/
├── TrafficSimulator.exe    # Main executable
├── networks/                # Traffic scenarios
├── frontend/build/          # React app
├── database/                # Database schemas
├── _internal/               # Python runtime and libraries
└── ... (other dependencies)
```

**Verify:**
```powershell
# Test the executable
cd dist\TrafficSimulator
.\TrafficSimulator.exe

# Should start server and open browser
# Press Ctrl+C to stop
```

---

### Step 3: Download and Prepare SUMO (One-time, 5 minutes)

Download the portable SUMO package:

1. Go to: https://sumo.dlr.de/docs/Downloads.html
2. Download: **sumo-win64-1.24.0.zip** (or latest version)
3. Extract to a temporary location

**Or use PowerShell:**
```powershell
# Create deployment folder
New-Item -ItemType Directory -Force -Path .\deployment

# Download SUMO (replace with latest version URL)
$sumoUrl = "https://sumo.dlr.de/releases/1.24.0/sumo-win64-1.24.0.zip"
$sumoZip = ".\deployment\sumo.zip"
Invoke-WebRequest -Uri $sumoUrl -OutFile $sumoZip

# Extract SUMO
Expand-Archive -Path $sumoZip -DestinationPath .\deployment\

# Rename folder
Rename-Item .\deployment\sumo-1.24.0 .\deployment\sumo
```

**SUMO structure should be:**
```
deployment/sumo/
├── bin/           # Executables (sumo.exe, sumo-gui.exe)
├── tools/         # Python tools
├── data/          # Data files
└── ...
```

---

### Step 4: Copy SUMO into Distribution (2 minutes)

Copy SUMO into the PyInstaller output:

```powershell
# Copy SUMO to dist folder
Copy-Item -Path .\deployment\sumo -Destination .\dist\TrafficSimulator\sumo -Recurse

# Verify SUMO is there
Test-Path .\dist\TrafficSimulator\sumo\bin\sumo-gui.exe
# Should return: True
```

**Final dist structure:**
```
dist/TrafficSimulator/
├── TrafficSimulator.exe
├── networks/
├── frontend/
├── sumo/                    # ← SUMO bundled here
│   ├── bin/
│   ├── tools/
│   └── data/
└── _internal/
```

---

### Step 5: Test the Complete Package (5 minutes)

Test that everything works together:

```powershell
cd dist\TrafficSimulator
.\TrafficSimulator.exe
```

**Expected behavior:**
1. Console window opens showing configuration
2. ✅ SUMO found at bundled location
3. ✅ Server starts on localhost:5000
4. ✅ Browser opens automatically
5. ✅ Application loads and works
6. ✅ Can start simulations with SUMO GUI

**Test checklist:**
- [ ] Application launches without errors
- [ ] Browser opens to app
- [ ] Can select a network scenario
- [ ] Can configure simulation parameters
- [ ] SUMO GUI opens when starting simulation
- [ ] Real-time data appears in dashboard
- [ ] Can stop simulation cleanly

---

### Step 6: Create NSIS Installer (10 minutes)

Create the Windows installer using NSIS:

1. **Create installer script** `installer.nsi`:

```nsis
; Traffic Simulator Installer Script
; Creates Windows installer with bundled SUMO

!include "MUI2.nsh"
!include "FileFunc.nsh"

;--------------------------------
; General Configuration

Name "Traffic Simulator"
OutFile "TrafficSimulator-Setup-v1.0.exe"
InstallDir "$PROGRAMFILES64\TrafficSimulator"
InstallDirRegKey HKCU "Software\TrafficSimulator" "InstallDir"
RequestExecutionLevel admin

; Size estimation
!define /math ESTIMATED_SIZE 600  ; 600 MB

;--------------------------------
; Modern UI Configuration

!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer-banner.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer-header.bmp"

;--------------------------------
; Pages

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer Sections

Section "Install"
    SetOutPath $INSTDIR
    
    DetailPrint "Installing Traffic Simulator..."
    
    ; Copy all files from dist\TrafficSimulator\
    File /r "dist\TrafficSimulator\*.*"
    
    DetailPrint "Creating shortcuts..."
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\Traffic Simulator"
    CreateShortcut "$SMPROGRAMS\Traffic Simulator\Traffic Simulator.lnk" "$INSTDIR\TrafficSimulator.exe" "" "$INSTDIR\TrafficSimulator.exe" 0
    CreateShortcut "$SMPROGRAMS\Traffic Simulator\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortcut "$DESKTOP\Traffic Simulator.lnk" "$INSTDIR\TrafficSimulator.exe"
    
    ; Create data directories
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\sessions"
    CreateDirectory "$INSTDIR\cache"
    
    DetailPrint "Registering application..."
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Write registry keys for uninstaller
    WriteRegStr HKCU "Software\TrafficSimulator" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "DisplayName" "Traffic Simulator"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "DisplayIcon" "$INSTDIR\TrafficSimulator.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "Publisher" "Traffic Simulator Team"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "DisplayVersion" "1.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "HelpLink" "https://github.com/your-repo"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "NoRepair" 1
    
    ; Calculate and write estimated size (in KB)
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "EstimatedSize" "$0"
    
    DetailPrint "Installation complete!"
    MessageBox MB_OK "Traffic Simulator has been successfully installed!$\n$\nA desktop shortcut has been created.$\n$\nNote: SUMO is bundled with this application - no separate installation needed."
    
SectionEnd

;--------------------------------
; Uninstaller Section

Section "Uninstall"
    DetailPrint "Uninstalling Traffic Simulator..."
    
    ; Remove files
    RMDir /r "$INSTDIR\networks"
    RMDir /r "$INSTDIR\frontend"
    RMDir /r "$INSTDIR\database"
    RMDir /r "$INSTDIR\sumo"
    RMDir /r "$INSTDIR\_internal"
    RMDir /r "$INSTDIR\data"
    RMDir /r "$INSTDIR\sessions"
    RMDir /r "$INSTDIR\cache"
    Delete "$INSTDIR\TrafficSimulator.exe"
    Delete "$INSTDIR\*.dll"
    Delete "$INSTDIR\*.pyd"
    Delete "$INSTDIR\uninstall.exe"
    
    ; Remove shortcuts
    Delete "$DESKTOP\Traffic Simulator.lnk"
    RMDir /r "$SMPROGRAMS\Traffic Simulator"
    
    ; Remove installation directory
    RMDir "$INSTDIR"
    
    ; Remove registry keys
    DeleteRegKey HKCU "Software\TrafficSimulator"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator"
    
    DetailPrint "Uninstallation complete!"
    MessageBox MB_OK "Traffic Simulator has been successfully uninstalled."
    
SectionEnd
```

2. **Build the installer:**

```powershell
# From project root
makensis installer.nsi
```

**Output:** `TrafficSimulator-Setup-v1.0.exe` (~500-600MB)

---

### Step 7: Test the Installer (10 minutes)

Test the complete installation process:

```powershell
# Run the installer
.\TrafficSimulator-Setup-v1.0.exe
```

**Test checklist:**
- [ ] Installer starts and shows welcome screen
- [ ] License agreement displays
- [ ] Can choose installation directory
- [ ] Installation completes without errors
- [ ] Desktop shortcut created
- [ ] Start Menu entry created
- [ ] Double-click desktop icon launches app
- [ ] Application works correctly
- [ ] Can run simulations with bundled SUMO
- [ ] Uninstaller works and removes everything

---

## Distribution

### File Hosting Options

1. **GitHub Releases**
   - Create a new release
   - Upload `TrafficSimulator-Setup-v1.0.exe`
   - Add release notes

2. **Google Drive / OneDrive**
   - Upload installer
   - Share link with "Anyone with link can download"

3. **University Server**
   - Contact IT to host the file
   - Provide download link in thesis

### Download Instructions for Users

Create a simple `DOWNLOAD.md`:

```markdown
# Download Traffic Simulator

## System Requirements
- Windows 10/11 (64-bit)
- 2GB RAM minimum, 4GB recommended
- 1GB free disk space
- Internet connection for initial download

## Installation

1. Download [TrafficSimulator-Setup-v1.0.exe](your-download-link)
2. Run the installer
3. Follow the installation wizard
4. Launch from desktop shortcut or Start Menu

## No Additional Software Needed
SUMO traffic simulator is bundled - no separate installation required!

## Support
For issues, contact: your-email@example.com
```

---

## Troubleshooting

### Build Issues

**Problem:** PyInstaller fails with "module not found"
```powershell
# Solution: Add to hiddenimports in .spec file
hiddenimports=['missing_module_name']
```

**Problem:** Frontend build not found
```powershell
# Solution: Build frontend first
cd frontend
npm run build
cd ..
```

**Problem:** SUMO not detected in packaged app
```powershell
# Solution: Verify SUMO copied correctly
Test-Path dist\TrafficSimulator\sumo\bin\sumo-gui.exe
```

### Runtime Issues

**Problem:** Application crashes on startup
- Check console output for errors
- Verify all files copied correctly
- Test on clean Windows VM

**Problem:** SUMO GUI doesn't open
- Check bundled SUMO path
- Verify sumo-gui.exe exists
- Check Windows Firewall settings

**Problem:** Database errors
- Ensure data/ directory has write permissions
- Check disk space

---

## File Sizes

| Component | Size |
|-----------|------|
| Python Backend (packaged) | ~50 MB |
| React Frontend (build) | ~5 MB |
| Network Scenarios | ~200 MB |
| SUMO (bundled) | ~250 MB |
| **Total Installer** | **~500-600 MB** |

---

## Development vs Production

| Aspect | Development | Production (Packaged) |
|--------|-------------|----------------------|
| Frontend | npm start | Served by Flask |
| Backend | python app.py | TrafficSimulator.exe |
| SUMO | System install | Bundled in app |
| Browser | Manual open | Auto-opens |
| Updates | Instant | Reinstall needed |

---

## License Compliance

**SUMO License:** Eclipse Public License 2.0 (EPL-2.0)
- ✅ Allows redistribution
- ✅ Allows bundling with applications
- ✅ Commercial use permitted
- ⚠️ Must include SUMO license file
- ⚠️ Must credit SUMO project

**Include in installer:**
- `LICENSE-SUMO.txt` - SUMO license
- `LICENSE.txt` - Your application license
- `CREDITS.txt` - Attribution to SUMO project

---

## Next Steps

1. ✅ Complete building and testing
2. ✅ Create icon files (icon.ico, installer graphics)
3. ✅ Write user documentation
4. ✅ Test on multiple Windows versions
5. ✅ Prepare distribution method
6. ✅ Document in thesis

---

## Quick Reference Commands

```powershell
# Complete build from scratch
cd frontend
npm install
npm run build
cd ..
pyinstaller traffic-simulator.spec
Copy-Item .\deployment\sumo .\dist\TrafficSimulator\sumo -Recurse
makensis installer.nsi

# Test installer
.\TrafficSimulator-Setup-v1.0.exe

# Quick test (without installer)
cd dist\TrafficSimulator
.\TrafficSimulator.exe
```

---

## Estimated Timeline

| Task | Time |
|------|------|
| Setup prerequisites | 30 min |
| Build frontend | 5 min |
| Build backend (PyInstaller) | 15 min |
| Download & prepare SUMO | 10 min |
| Copy SUMO to dist | 2 min |
| Test package | 5 min |
| Create NSIS script | 15 min |
| Build installer | 5 min |
| Test installer | 10 min |
| **TOTAL** | **~2 hours** |

---

*Good luck with your deployment!* 🚀
