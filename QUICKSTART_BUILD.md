# Quick Start: Building the Installer

Fast-track guide to build your Traffic Simulator installer. For detailed information, see `DEPLOYMENT_INSTALLER.md`.

## Prerequisites Check

```powershell
# Check Python
python --version    # Should be 3.8+

# Check Node.js
node --version      # Should be 14+

# Install PyInstaller
pip install pyinstaller

# Install NSIS (for installer creation)
choco install nsis
```

---

## Build Commands (Copy-Paste Ready)

### 1. Build Frontend (5 min)

```powershell
cd frontend
npm install
npm run build
cd ..
```

### 2. Build Backend with PyInstaller (15 min)

```powershell
# From project root
pyinstaller traffic-simulator.spec
```

### 3. Download SUMO (One-time setup)

```powershell
# Create deployment folder
New-Item -ItemType Directory -Force -Path .\deployment

# Download SUMO 1.24.0 (or get latest from sumo.dlr.de)
$url = "https://sumo.dlr.de/releases/1.24.0/sumo-win64-1.24.0.zip"
Invoke-WebRequest -Uri $url -OutFile .\deployment\sumo.zip

# Extract
Expand-Archive .\deployment\sumo.zip .\deployment\
Rename-Item .\deployment\sumo-1.24.0 .\deployment\sumo
```

### 4. Copy SUMO to Distribution (2 min)

```powershell
Copy-Item .\deployment\sumo .\dist\TrafficSimulator\sumo -Recurse
```

### 5. Test the Package (5 min)

```powershell
cd dist\TrafficSimulator
.\TrafficSimulator.exe
# Press Ctrl+C to stop after testing
cd ..\..
```

### 6. Create NSIS Installer Script

Save this as `installer.nsi` in project root:

```nsis
!include "MUI2.nsh"

Name "Traffic Simulator"
OutFile "TrafficSimulator-Setup-v1.0.exe"
InstallDir "$PROGRAMFILES64\TrafficSimulator"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath $INSTDIR
    File /r "dist\TrafficSimulator\*.*"
    
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\sessions"
    
    CreateDirectory "$SMPROGRAMS\Traffic Simulator"
    CreateShortcut "$SMPROGRAMS\Traffic Simulator\Traffic Simulator.lnk" "$INSTDIR\TrafficSimulator.exe"
    CreateShortcut "$DESKTOP\Traffic Simulator.lnk" "$INSTDIR\TrafficSimulator.exe"
    
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "DisplayName" "Traffic Simulator"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator" "UninstallString" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\Traffic Simulator.lnk"
    RMDir /r "$SMPROGRAMS\Traffic Simulator"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TrafficSimulator"
SectionEnd
```

### 7. Build Installer (5 min)

```powershell
makensis installer.nsi
```

**Output:** `TrafficSimulator-Setup-v1.0.exe` (~500MB)

### 8. Test Installer

```powershell
.\TrafficSimulator-Setup-v1.0.exe
```

---

## One-Command Build (After Setup)

Once everything is set up, rebuild with one command:

```powershell
# Complete rebuild
cd frontend ; npm run build ; cd .. ; pyinstaller traffic-simulator.spec ; Copy-Item .\deployment\sumo .\dist\TrafficSimulator\sumo -Recurse ; makensis installer.nsi
```

---

## Troubleshooting

**Frontend build fails:**
```powershell
cd frontend
rm -r node_modules
npm install
npm run build
```

**PyInstaller fails:**
```powershell
pip install --upgrade pyinstaller
pyinstaller --clean traffic-simulator.spec
```

**SUMO not found in packaged app:**
```powershell
# Verify SUMO was copied
Test-Path dist\TrafficSimulator\sumo\bin\sumo-gui.exe
```

**Installer build fails:**
```powershell
# Check NSIS installed
makensis /VERSION
```

---

## File Checklist

Before building installer, verify these exist:

```powershell
# Frontend build
Test-Path frontend\build\index.html

# PyInstaller output
Test-Path dist\TrafficSimulator\TrafficSimulator.exe

# Bundled SUMO
Test-Path dist\TrafficSimulator\sumo\bin\sumo-gui.exe

# Networks
Test-Path dist\TrafficSimulator\networks

# Frontend in dist
Test-Path dist\TrafficSimulator\frontend\build\index.html
```

All should return `True`.

---

## Timeline

| Step | Time |
|------|------|
| Build frontend | 5 min |
| Build backend | 15 min |
| Copy SUMO | 2 min |
| Test | 5 min |
| Build installer | 5 min |
| **Total** | **32 min** |

(First time: +10 min for SUMO download)

---

## Distribution

**Upload to:**
- GitHub Releases
- Google Drive
- OneDrive
- University server

**Share download link** with installation instructions.

---

## Success Criteria

✅ Installer creates without errors  
✅ Double-click installer runs setup wizard  
✅ Application installs to Program Files  
✅ Desktop shortcut created  
✅ Double-click shortcut launches app  
✅ Browser opens automatically  
✅ Can start simulation  
✅ SUMO GUI opens  
✅ Uninstaller works  

---

*For detailed information, see `DEPLOYMENT_INSTALLER.md`*
