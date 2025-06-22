"""
Automatic dependency installer for Scale API Compose Pilot.

Handles installation of dependencies that aren't available on PyPI,
like the TrueNAS API client from GitHub.
"""

import subprocess
import sys
import importlib
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class DependencyInstaller:
    """Handles automatic installation of missing dependencies."""
    
    def __init__(self):
        self.missing_deps = []
        self.installed_deps = []
    
    def check_and_install_dependencies(self) -> bool:
        """
        Check for missing dependencies and install them automatically.
        
        Returns:
            bool: True if all dependencies are available, False otherwise
        """
        dependencies = [
            {
                'module': 'truenas_api_client',
                'install_cmd': 'git+https://github.com/truenas/api_client.git',
                'description': 'TrueNAS API Client'
            }
        ]
        
        all_available = True
        
        for dep in dependencies:
            if not self._check_module(dep['module']):
                print(f"📦 Installing {dep['description']}...")
                if self._install_dependency(dep['install_cmd'], dep['description']):
                    self.installed_deps.append(dep['description'])
                else:
                    self.missing_deps.append(dep['description'])
                    all_available = False
        
        return all_available
    
    def _check_module(self, module_name: str) -> bool:
        """Check if a module is available for import."""
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False
    
    def _install_dependency(self, install_cmd: str, description: str) -> bool:
        """Install a dependency using pip."""
        try:
            # Determine the correct pip command
            pip_cmd = self._get_pip_command()
            
            # Install the dependency
            cmd = [pip_cmd, 'install', install_cmd]
            
            print(f"   Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"   ✅ {description} installed successfully")
                return True
            else:
                print(f"   ❌ Failed to install {description}")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception installing {description}: {e}")
            return False
    
    def _get_pip_command(self) -> str:
        """Get the appropriate pip command for the current environment."""
        # Check if we're in a virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # In virtual environment, use pip directly
            return 'pip'
        else:
            # System Python, use pip with user flag or pip3
            return 'pip3'
    
    def get_installation_summary(self) -> str:
        """Get a summary of dependency installation results."""
        summary = []
        
        if self.installed_deps:
            summary.append(f"✅ Installed: {', '.join(self.installed_deps)}")
        
        if self.missing_deps:
            summary.append(f"❌ Failed to install: {', '.join(self.missing_deps)}")
            summary.append("\n🔧 Manual installation required:")
            summary.append("   pip install git+https://github.com/truenas/api_client.git")
        
        return '\n'.join(summary) if summary else "✅ All dependencies were already available"


def ensure_dependencies() -> bool:
    """
    Ensure all required dependencies are installed.
    
    Returns:
        bool: True if all dependencies are available
    """
    installer = DependencyInstaller()
    
    # Check and install missing dependencies
    success = installer.check_and_install_dependencies()
    
    # Print summary
    summary = installer.get_installation_summary()
    if summary:
        print(f"\n📋 Dependency Installation Summary:")
        print(summary)
    
    return success


def check_truenas_api_client() -> Tuple[bool, Optional[str]]:
    """
    Check if TrueNAS API client is available.
    
    Returns:
        Tuple of (is_available, error_message)
    """
    try:
        import truenas_api_client
        return True, None
    except ImportError as e:
        return False, str(e)


def install_truenas_api_client_with_fallback() -> bool:
    """
    Install TrueNAS API client with multiple fallback strategies.
    
    Returns:
        bool: True if installation succeeded
    """
    print("🔧 Installing TrueNAS API Client...")
    
    # Strategy 1: Direct pip install
    strategies = [
        {
            'name': 'Direct GitHub installation',
            'cmd': ['pip', 'install', 'git+https://github.com/truenas/api_client.git']
        },
        {
            'name': 'User-level installation',
            'cmd': ['pip', 'install', '--user', 'git+https://github.com/truenas/api_client.git']
        },
        {
            'name': 'Force reinstall',
            'cmd': ['pip', 'install', '--force-reinstall', 'git+https://github.com/truenas/api_client.git']
        }
    ]
    
    for strategy in strategies:
        print(f"   Trying: {strategy['name']}")
        try:
            result = subprocess.run(
                strategy['cmd'],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"   ✅ Success with {strategy['name']}")
                
                # Verify installation
                if check_truenas_api_client()[0]:
                    print("   ✅ TrueNAS API Client verified working")
                    return True
                else:
                    print("   ⚠️  Installation completed but import still fails")
            else:
                print(f"   ❌ Failed: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n❌ All installation strategies failed")
    print("🔧 Manual installation required:")
    print("   pip install git+https://github.com/truenas/api_client.git")
    
    return False


if __name__ == "__main__":
    # Test the dependency installer
    success = ensure_dependencies()
    if success:
        print("✅ All dependencies ready!")
    else:
        print("❌ Some dependencies missing")
        sys.exit(1)