"""
Configuration Module for Traffic Simulator

Handles path configuration for development, packaged (PyInstaller), and 
deployed environments. Provides automatic SUMO detection and validation.

Author: Traffic Simulator Team
Date: October 2025
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Configuration manager for Traffic Simulator"""
    
    def __init__(self):
        """Initialize configuration with automatic path detection"""
        # Detect if running from PyInstaller bundle
        self.is_frozen = getattr(sys, 'frozen', False)
        
        if self.is_frozen:
            # Running from PyInstaller bundle
            self.base_dir = Path(sys._MEIPASS)  # Temporary extraction dir
            self.app_dir = Path(sys.executable).parent  # Installation directory
        else:
            # Running from source
            self.base_dir = Path(__file__).parent
            self.app_dir = self.base_dir
        
        # Application directories
        self.networks_dir = self.app_dir / "networks"
        self.database_dir = self.app_dir / "data"
        self.sessions_dir = self.app_dir / "sessions"
        self.cache_dir = self.app_dir / "cache"
        
        # Frontend build directory
        if self.is_frozen:
            # In frozen app, frontend is in _MEIPASS/_internal
            meipass = Path(sys._MEIPASS)
            self.frontend_build_dir = meipass / "frontend" / "build"
        else:
            # In development, frontend is relative to backend
            self.frontend_build_dir = self.base_dir.parent / "frontend" / "build"
        
        # Database file
        self.database_path = self.database_dir / "traffic_simulator.db"
        
        # SUMO paths
        self.sumo_home = self._find_sumo_home()
        self.sumo_bin_path = self._find_sumo_bin()
        self.sumo_tools_path = self._find_sumo_tools()
        
        # Server configuration
        self.host = os.getenv('FLASK_HOST', '127.0.0.1')
        self.port = int(os.getenv('FLASK_PORT', 5000))
        self.debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true' and not self.is_frozen
        
        # Ensure required directories exist
        self._create_directories()
    
    def _find_sumo_home(self) -> Optional[Path]:
        """
        Find SUMO_HOME directory with multiple detection methods
        
        Priority:
        1. Bundled SUMO (in packaged app) - HIGHEST PRIORITY
        2. SUMO_HOME environment variable
        3. Common installation paths
        4. System PATH
        
        Returns:
            Path to SUMO_HOME or None if not found
        """
        # 1. Check bundled SUMO first (highest priority for packaged app)
        bundled_sumo = self.app_dir / "sumo"
        if bundled_sumo.exists() and (bundled_sumo / "bin").exists():
            print(f"Found bundled SUMO: {bundled_sumo}")
            return bundled_sumo
        
        # 2. Check environment variable (fallback for development)
        sumo_home = os.environ.get('SUMO_HOME')
        if sumo_home and Path(sumo_home).exists():
            print(f"Found SUMO_HOME from environment: {sumo_home}")
            return Path(sumo_home)
        
        # 3. Common Windows installation paths
        common_paths = [
            Path(r"C:\Program Files (x86)\Eclipse\Sumo"),
            Path(r"C:\Program Files\Eclipse\Sumo"),
            Path(r"C:\Program Files (x86)\SUMO"),
            Path(r"C:\Program Files\SUMO"),
            Path(r"C:\Sumo"),
        ]
        
        for path in common_paths:
            if path.exists() and (path / "bin").exists():
                print(f"Found SUMO at common path: {path}")
                return path
        
        # 4. Check if sumo-gui.exe is in system PATH
        sumo_gui_exe = shutil.which("sumo-gui.exe") or shutil.which("sumo-gui")
        if sumo_gui_exe:
            sumo_bin = Path(sumo_gui_exe).parent
            sumo_home_path = sumo_bin.parent
            if sumo_home_path.exists():
                print(f"Found SUMO from system PATH: {sumo_home_path}")
                return sumo_home_path
        
        print("WARNING: SUMO installation not found!")
        return None
    
    def _find_sumo_bin(self) -> Optional[Path]:
        """Find SUMO bin directory containing executables"""
        if self.sumo_home:
            bin_path = self.sumo_home / "bin"
            if bin_path.exists():
                return bin_path
        return None
    
    def _find_sumo_tools(self) -> Optional[Path]:
        """Find SUMO tools directory"""
        if self.sumo_home:
            tools_path = self.sumo_home / "tools"
            if tools_path.exists():
                return tools_path
        return None
    
    def get_sumo_binary(self, use_gui: bool = True) -> str:
        """
        Get path to SUMO executable
        
        Args:
            use_gui: If True, return path to sumo-gui, else sumo
            
        Returns:
            Full path to SUMO executable
            
        Raises:
            FileNotFoundError: If SUMO binary not found
        """
        if not self.sumo_bin_path:
            raise FileNotFoundError(
                "SUMO installation not found. Please install SUMO or set SUMO_HOME environment variable.\n"
                "Download from: https://sumo.dlr.de/docs/Installing/index.html"
            )
        
        binary_name = "sumo-gui.exe" if use_gui else "sumo.exe"
        binary_path = self.sumo_bin_path / binary_name
        
        if not binary_path.exists():
            # Try without .exe extension (for cross-platform compatibility)
            binary_name = "sumo-gui" if use_gui else "sumo"
            binary_path = self.sumo_bin_path / binary_name
        
        if not binary_path.exists():
            raise FileNotFoundError(f"SUMO binary not found: {binary_path}")
        
        return str(binary_path)
    
    def get_sumo_tool(self, tool_name: str) -> Optional[Path]:
        """
        Get path to a SUMO tool script
        
        Args:
            tool_name: Name of the tool (e.g., 'randomTrips.py')
            
        Returns:
            Path to tool script or None if not found
        """
        if not self.sumo_tools_path:
            return None
        
        tool_path = self.sumo_tools_path / tool_name
        if tool_path.exists():
            return tool_path
        
        # Try common tool locations
        for subdir in ['', 'trip', 'import', 'xml']:
            tool_path = self.sumo_tools_path / subdir / tool_name
            if tool_path.exists():
                return tool_path
        
        return None
    
    def _create_directories(self):
        """Create required directories if they don't exist"""
        directories = [
            self.database_dir,
            self.sessions_dir,
            self.cache_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_installation(self) -> Dict[str, Any]:
        """
        Validate the installation and return status
        
        Returns:
            Dictionary with validation results
        """
        status = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        # Check SUMO
        if not self.sumo_home:
            status['valid'] = False
            status['errors'].append("SUMO installation not found")
        else:
            status['info']['sumo_home'] = str(self.sumo_home)
            status['info']['sumo_version'] = self._get_sumo_version()
        
        # Check SUMO binaries
        try:
            self.get_sumo_binary(use_gui=True)
            status['info']['sumo_gui'] = 'found'
        except FileNotFoundError:
            status['valid'] = False
            status['errors'].append("sumo-gui executable not found")
        
        try:
            self.get_sumo_binary(use_gui=False)
            status['info']['sumo'] = 'found'
        except FileNotFoundError:
            status['warnings'].append("sumo executable not found (GUI only mode)")
        
        # Check directories
        if not self.networks_dir.exists():
            status['warnings'].append(f"Networks directory not found: {self.networks_dir}")
        else:
            network_count = len(list(self.networks_dir.iterdir()))
            status['info']['networks'] = network_count
        
        # Check frontend build
        if not self.frontend_build_dir.exists():
            status['warnings'].append("Frontend build not found (development mode)")
        else:
            status['info']['frontend'] = 'built'
        
        status['info']['mode'] = 'packaged' if self.is_frozen else 'development'
        status['info']['app_dir'] = str(self.app_dir)
        
        return status
    
    def _get_sumo_version(self) -> str:
        """Get SUMO version string"""
        try:
            import subprocess
            sumo_exe = self.get_sumo_binary(use_gui=False)
            result = subprocess.run(
                [sumo_exe, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract version from output (first line usually)
                version_line = result.stdout.split('\n')[0]
                return version_line.strip()
        except:
            pass
        return "unknown"
    
    def get_network_path(self, network_id: str) -> Path:
        """Get path to a network directory"""
        return self.networks_dir / network_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'is_frozen': self.is_frozen,
            'app_dir': str(self.app_dir),
            'base_dir': str(self.base_dir),
            'networks_dir': str(self.networks_dir),
            'database_dir': str(self.database_dir),
            'database_path': str(self.database_path),
            'sumo_home': str(self.sumo_home) if self.sumo_home else None,
            'sumo_bin_path': str(self.sumo_bin_path) if self.sumo_bin_path else None,
            'sumo_tools_path': str(self.sumo_tools_path) if self.sumo_tools_path else None,
            'host': self.host,
            'port': self.port,
            'debug': self.debug,
        }


# Global configuration instance
config = Config()


# Convenience functions
def get_sumo_binary(use_gui: bool = True) -> str:
    """Get path to SUMO executable"""
    return config.get_sumo_binary(use_gui)


def get_sumo_tool(tool_name: str) -> Optional[Path]:
    """Get path to SUMO tool"""
    return config.get_sumo_tool(tool_name)


def validate_installation() -> Dict[str, Any]:
    """Validate installation"""
    return config.validate_installation()


if __name__ == '__main__':
    """Test configuration"""
    print("=" * 60)
    print("Traffic Simulator Configuration Test")
    print("=" * 60)
    print()
    
    print("Configuration:")
    print("-" * 60)
    for key, value in config.to_dict().items():
        print(f"{key:20}: {value}")
    print()
    
    print("Validation:")
    print("-" * 60)
    validation = config.validate_installation()
    print(f"Valid: {validation['valid']}")
    
    if validation['errors']:
        print("\nErrors:")
        for error in validation['errors']:
            print(f"  ❌ {error}")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
    
    if validation['info']:
        print("\nInfo:")
        for key, value in validation['info'].items():
            print(f"  ℹ️  {key}: {value}")
    
    print()
    print("=" * 60)
