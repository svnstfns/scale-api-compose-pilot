"""
Installation method detection for Scale API Compose Pilot.

Detects how the package was installed (pip, homebrew, etc.) and 
adjusts dependency handling accordingly.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple


class InstallationDetector:
    """Detects how Scale API Compose Pilot was installed."""
    
    def __init__(self):
        self.installation_type = self._detect_installation_type()
        self.should_auto_install = self._should_auto_install_deps()
    
    def _detect_installation_type(self) -> str:
        """
        Detect the installation method.
        
        Returns:
            str: 'homebrew', 'pip', 'development', or 'unknown'
        """
        # Get the path to this module
        module_path = Path(__file__).resolve()
        
        # Check for Homebrew installation
        if self._is_homebrew_install(module_path):
            return 'homebrew'
        
        # Check for development installation
        if self._is_development_install(module_path):
            return 'development'
        
        # Check for pip installation
        if self._is_pip_install(module_path):
            return 'pip'
        
        return 'unknown'
    
    def _is_homebrew_install(self, module_path: Path) -> bool:
        """Check if installed via Homebrew."""
        homebrew_paths = [
            '/opt/homebrew/',           # Apple Silicon
            '/usr/local/Homebrew/',     # Intel Mac
            '/home/linuxbrew/',         # Linux
        ]
        
        module_str = str(module_path)
        return any(homebrew_path in module_str for homebrew_path in homebrew_paths)
    
    def _is_development_install(self, module_path: Path) -> bool:
        """Check if installed in development mode (pip install -e)."""
        # Look for setup.py or pyproject.toml in parent directories
        current = module_path.parent
        for _ in range(5):  # Check up to 5 levels up
            if (current / 'pyproject.toml').exists() or (current / 'setup.py').exists():
                # Check if there's a .git directory (development)
                if (current / '.git').exists():
                    return True
            current = current.parent
            if current == current.parent:  # Reached root
                break
        return False
    
    def _is_pip_install(self, module_path: Path) -> bool:
        """Check if installed via pip."""
        pip_indicators = [
            'site-packages',
            'dist-packages',
            '.egg',
        ]
        
        module_str = str(module_path)
        return any(indicator in module_str for indicator in pip_indicators)
    
    def _should_auto_install_deps(self) -> bool:
        """
        Determine if dependencies should be auto-installed.
        
        Returns:
            bool: True if auto-install should be attempted
        """
        # Check environment variable override
        no_auto_install = os.getenv('SCALE_COMPOSE_NO_AUTO_INSTALL', '').lower()
        if no_auto_install in ('true', '1', 'yes'):
            return False
        
        # Different behavior based on installation type
        if self.installation_type == 'homebrew':
            # Homebrew should have all dependencies bundled
            return False
        elif self.installation_type == 'development':
            # Development mode - allow auto-install
            return True
        elif self.installation_type == 'pip':
            # Pip installation - allow auto-install
            return True
        else:
            # Unknown installation - be conservative, allow auto-install
            return True
    
    def get_installation_info(self) -> dict:
        """Get detailed installation information."""
        return {
            'type': self.installation_type,
            'should_auto_install': self.should_auto_install,
            'python_executable': sys.executable,
            'module_path': str(Path(__file__).resolve()),
            'environment_vars': {
                'SCALE_COMPOSE_NO_AUTO_INSTALL': os.getenv('SCALE_COMPOSE_NO_AUTO_INSTALL'),
                'VIRTUAL_ENV': os.getenv('VIRTUAL_ENV'),
                'CONDA_DEFAULT_ENV': os.getenv('CONDA_DEFAULT_ENV'),
            }
        }
    
    def get_dependency_strategy(self) -> dict:
        """Get the recommended dependency installation strategy."""
        if self.installation_type == 'homebrew':
            return {
                'strategy': 'bundled',
                'message': 'Dependencies should be bundled with Homebrew formula',
                'fallback': 'Contact formula maintainer if dependencies are missing'
            }
        elif self.installation_type == 'development':
            return {
                'strategy': 'auto_install',
                'message': 'Auto-installing dependencies for development environment',
                'fallback': 'Manual install: pip install git+https://github.com/truenas/api_client.git'
            }
        elif self.installation_type == 'pip':
            return {
                'strategy': 'auto_install', 
                'message': 'Auto-installing missing dependencies',
                'fallback': 'Manual install: pip install git+https://github.com/truenas/api_client.git'
            }
        else:
            return {
                'strategy': 'auto_install',
                'message': 'Attempting auto-install for unknown installation type',
                'fallback': 'Manual install may be required'
            }


def detect_installation() -> Tuple[str, bool]:
    """
    Quick detection of installation type and auto-install preference.
    
    Returns:
        Tuple of (installation_type, should_auto_install)
    """
    detector = InstallationDetector()
    return detector.installation_type, detector.should_auto_install


def get_installation_guidance(installation_type: str) -> str:
    """Get user-friendly guidance based on installation type."""
    if installation_type == 'homebrew':
        return """
🍺 Homebrew Installation Detected

Dependencies should be automatically included with the Homebrew formula.
If you're missing dependencies, the formula may need updating.

🔧 Troubleshooting:
  brew reinstall scale-api-compose-pilot
  
🐛 If issues persist:
  Report to: https://github.com/svnstfns/scale-api-compose-pilot/issues
"""
    
    elif installation_type == 'development':
        return """
🛠️ Development Installation Detected

Auto-installation of dependencies is enabled.
You can disable it with: export SCALE_COMPOSE_NO_AUTO_INSTALL=true

🔧 Manual dependency install:
  pip install git+https://github.com/truenas/api_client.git
"""
    
    elif installation_type == 'pip':
        return """
📦 Pip Installation Detected

Dependencies will be auto-installed as needed.
You can disable auto-install with: export SCALE_COMPOSE_NO_AUTO_INSTALL=true

🔧 Manual dependency install:
  pip install git+https://github.com/truenas/api_client.git
"""
    
    else:
        return """
❓ Unknown Installation Type

Dependencies will be auto-installed if possible.
Set SCALE_COMPOSE_NO_AUTO_INSTALL=true to disable.

🔧 Manual dependency install:
  pip install git+https://github.com/truenas/api_client.git
"""


if __name__ == "__main__":
    detector = InstallationDetector()
    info = detector.get_installation_info()
    
    print("🔍 Installation Detection Results:")
    print(f"  Type: {info['type']}")
    print(f"  Auto-install: {info['should_auto_install']}")
    print(f"  Python: {info['python_executable']}")
    print(f"  Module: {info['module_path']}")
    
    strategy = detector.get_dependency_strategy()
    print(f"\n📋 Dependency Strategy: {strategy['strategy']}")
    print(f"  {strategy['message']}")
    
    print(get_installation_guidance(info['type']))