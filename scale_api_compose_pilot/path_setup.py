"""
PATH setup utilities for Scale API Compose Pilot CLI.

Helps users set up their PATH to use scale-compose command globally.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


class PathSetup:
    """Handles PATH setup for the CLI command."""
    
    def __init__(self):
        self.cli_name = "scale-compose"
        self.package_name = "scale-api-compose-pilot"
    
    def get_current_cli_path(self) -> Optional[str]:
        """Get the current path to the CLI executable."""
        try:
            # Find where the CLI is installed
            result = subprocess.run(
                ["which", self.cli_name], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        # Fallback: check common locations
        possible_paths = [
            f"{sys.executable.replace('python', self.cli_name)}",
            f"{os.path.dirname(sys.executable)}/{self.cli_name}",
            f"{Path.home()}/.local/bin/{self.cli_name}",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def is_in_path(self) -> bool:
        """Check if the CLI is accessible via PATH."""
        try:
            result = subprocess.run(
                [self.cli_name, "--help"], 
                capture_output=True, 
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def get_shell_rc_files(self) -> List[Path]:
        """Get list of shell RC files to potentially update."""
        home = Path.home()
        rc_files = []
        
        # Common shell RC files
        candidates = [
            ".bashrc",
            ".bash_profile", 
            ".zshrc",
            ".profile",
            ".fish_config"
        ]
        
        for candidate in candidates:
            rc_file = home / candidate
            if rc_file.exists():
                rc_files.append(rc_file)
        
        return rc_files
    
    def suggest_path_setup(self) -> str:
        """Generate suggestions for setting up PATH."""
        cli_path = self.get_current_cli_path()
        
        if not cli_path:
            return """
❌ Could not locate scale-compose executable.

🔧 Try reinstalling:
   pip install --force-reinstall scale-api-compose-pilot

📍 Or install with user flag:
   pip install --user scale-api-compose-pilot
   
🛠️  Then add ~/.local/bin to your PATH"""
        
        cli_dir = os.path.dirname(cli_path)
        
        suggestions = [f"✅ Found scale-compose at: {cli_path}"]
        
        if not self.is_in_path():
            suggestions.extend([
                "",
                "⚠️  scale-compose is not in your PATH.",
                "",
                "🔧 To fix this, add the following to your shell configuration:",
                "",
                f'   export PATH="{cli_dir}:$PATH"',
                "",
                "📁 Add this line to one of these files:"
            ])
            
            rc_files = self.get_shell_rc_files()
            if rc_files:
                for rc_file in rc_files:
                    suggestions.append(f"   • {rc_file}")
            else:
                suggestions.extend([
                    "   • ~/.bashrc (for Bash)",
                    "   • ~/.zshrc (for Zsh)", 
                    "   • ~/.profile (universal)"
                ])
            
            suggestions.extend([
                "",
                "🔄 Then reload your shell:",
                "   source ~/.bashrc  # or ~/.zshrc, etc.",
                "",
                "✅ Or open a new terminal window"
            ])
        else:
            suggestions.append("\n✅ scale-compose is already in your PATH!")
        
        return "\n".join(suggestions)
    
    def create_desktop_entry(self) -> bool:
        """Create a desktop entry for GUI access (Linux)."""
        if sys.platform != "linux":
            return False
        
        try:
            desktop_dir = Path.home() / ".local/share/applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            cli_path = self.get_current_cli_path()
            if not cli_path:
                return False
            
            desktop_content = f"""[Desktop Entry]
Name=Scale API Compose Pilot
Comment=TrueNAS Scale Docker Compose deployment tool
Exec={cli_path} init
Icon=application-x-executable
Terminal=true
Type=Application
Categories=System;
Keywords=truenas;docker;compose;nas;
"""
            
            desktop_file = desktop_dir / "scale-compose-pilot.desktop"
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            desktop_file.chmod(0o755)
            
            return True
            
        except Exception:
            return False


def check_and_setup_path() -> str:
    """Check PATH setup and provide guidance."""
    setup = PathSetup()
    return setup.suggest_path_setup()


def create_installation_script() -> str:
    """Create a one-liner installation script for users."""
    script = '''#!/bin/bash
# Scale API Compose Pilot - One-line installer

echo "🚀 Installing Scale API Compose Pilot..."

# Install the package
pip install scale-api-compose-pilot

# Check if CLI is accessible
if command -v scale-compose &> /dev/null; then
    echo "✅ Installation successful!"
    echo "🎯 Run 'scale-compose init' to get started"
else
    echo "⚠️  Installation complete but CLI not in PATH"
    echo "🔧 Run 'scale-compose-check-path' for setup instructions"
fi
'''
    return script


def main():
    """Main entry point for the PATH check command."""
    print(check_and_setup_path())


if __name__ == "__main__":
    main()