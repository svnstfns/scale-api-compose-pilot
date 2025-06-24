"""
TrueNAS Scale Setup Wizard

Interactive setup wizard for configuring Scale API Compose Pilot.
Includes auto-discovery and guided API key creation.
"""

import os
import sys
import webbrowser
import time
from typing import Optional, Dict, Any
from pathlib import Path

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from .discovery import TrueNASScanner, TrueNASSystem
from .manager import TrueNASDockerManager
from .exceptions import TrueNASConnectionError, TrueNASAuthenticationError
from .dependency_installer import ensure_dependencies


class SetupWizard:
    """Interactive setup wizard for Scale API Compose Pilot."""
    
    def __init__(self):
        self.config = {}
        self.env_file = Path(".env")
        
    def run(self) -> bool:
        """
        Run the complete setup wizard.
        
        Returns:
            True if setup completed successfully
        """
        print("🚀 Welcome to Scale API Compose Pilot Setup Wizard!")
        print("=" * 50)
        
        try:
            # Step 0: Ensure dependencies are installed
            print("\n📦 Checking dependencies...")
            if not ensure_dependencies():
                print("❌ Failed to install required dependencies")
                print("Please install manually and try again")
                return False
            
            # Step 1: Discover TrueNAS systems
            if not self._discover_truenas():
                return False
            
            # Step 2: Get API key
            if not self._setup_api_key():
                return False
            
            # Step 3: Test connection
            if not self._test_connection():
                return False
            
            # Step 4: Save configuration
            if not self._save_configuration():
                return False
            
            print("\n✅ Setup completed successfully!")
            print(f"Configuration saved to {self.env_file}")
            print("\nYou can now use Scale API Compose Pilot:")
            print("  scale-compose list")
            print("  scale-compose deploy docker-compose.yml my-app")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Setup failed: {e}")
            return False
    
    def _discover_truenas(self) -> bool:
        """Discover TrueNAS systems on the network."""
        print("\n🔍 Step 1: Discovering TrueNAS Scale systems...")
        
        # Check if user wants to skip discovery
        if self._ask_yes_no("Do you want to auto-discover TrueNAS systems? (y/n): "):
            scanner = TrueNASScanner(timeout=5.0)
            systems = scanner.scan_lan_for_truenas()
            
            if systems:
                print(f"\n✅ Found {len(systems)} TrueNAS system(s):")
                for i, system in enumerate(systems, 1):
                    print(f"  {i}. {system}")
                
                if len(systems) == 1:
                    # Auto-select single system
                    selected_system = systems[0]
                    print(f"\n→ Auto-selected: {selected_system}")
                else:
                    # Let user choose
                    while True:
                        try:
                            choice = int(input(f"\nSelect system (1-{len(systems)}): ")) - 1
                            if 0 <= choice < len(systems):
                                selected_system = systems[choice]
                                break
                            else:
                                print("Invalid choice. Please try again.")
                        except ValueError:
                            print("Please enter a number.")
                
                self.config['host'] = selected_system.ip_address
                self.config['web_url'] = selected_system.web_url
                return True
            else:
                print("❌ No TrueNAS systems found on the network.")
                print("You can manually enter the connection details.")
        
        # Manual entry
        return self._manual_host_entry()
    
    def _manual_host_entry(self) -> bool:
        """Manual host entry when auto-discovery fails."""
        print("\n📝 Manual TrueNAS Configuration:")
        
        while True:
            host = input("Enter TrueNAS hostname or IP address: ").strip()
            if host:
                # Test basic connectivity
                print(f"Testing connection to {host}...")
                
                scanner = TrueNASScanner()
                if scanner.verify_system(host):
                    print("✅ TrueNAS system verified!")
                    self.config['host'] = host
                    self.config['web_url'] = f"https://{host}"
                    return True
                else:
                    print(f"⚠️  Could not verify TrueNAS at {host}")
                    if self._ask_yes_no("Continue anyway? (y/n): "):
                        self.config['host'] = host
                        self.config['web_url'] = f"https://{host}"
                        return True
            else:
                print("Please enter a valid hostname or IP address.")
    
    def _setup_api_key(self) -> bool:
        """Guide user through API key creation."""
        print("\n🔑 Step 2: Setting up API Key...")
        print("\nTo use Scale API Compose Pilot, you need a TrueNAS API key.")
        
        # Check if user already has a key
        if self._ask_yes_no("Do you already have a TrueNAS API key? (y/n): "):
            return self._enter_existing_api_key()
        else:
            return self._create_new_api_key()
    
    def _enter_existing_api_key(self) -> bool:
        """Handle existing API key entry."""
        while True:
            api_key = input("Enter your TrueNAS API key: ").strip()
            if api_key:
                self.config['api_key'] = api_key
                return True
            else:
                print("Please enter a valid API key.")
    
    def _create_new_api_key(self) -> bool:
        """Guide user through creating a new API key."""
        print("\n📋 Creating a new API key:")
        print("1. I'll open the TrueNAS web interface for you")
        print("2. Log in to your TrueNAS system")
        print("3. Navigate to: Account (top-right) → API Keys")
        print("4. Click 'Add' to create a new API key")
        print("5. Give it a name like 'scale-compose-pilot'")
        print("6. Copy the generated key and paste it here")
        
        if not self._ask_yes_no("\nReady to open TrueNAS web interface? (y/n): "):
            return False
        
        # Open web interface
        web_url = self.config.get('web_url', f"https://{self.config['host']}")
        api_keys_url = f"{web_url}/ui/credentials/api-keys"
        
        try:
            print(f"\n🌐 Opening: {api_keys_url}")
            webbrowser.open(api_keys_url)
        except Exception as e:
            print(f"❌ Could not open web browser: {e}")
            print(f"Please manually navigate to: {api_keys_url}")
        
        print("\n⏳ Waiting for you to create the API key...")
        input("Press Enter when you have created the API key and are ready to enter it...")
        
        return self._enter_existing_api_key()
    
    def _test_connection(self) -> bool:
        """Test the connection with the provided credentials."""
        print("\n🔧 Step 3: Testing connection...")
        
        try:
            import asyncio
            
            # Run the async test
            success, message = asyncio.run(_test_connection_async(
                self.config['host'], 
                self.config['api_key']
            ))
            
            if success:
                print(f"✅ {message}")
                return True
            else:
                print(f"❌ Connection failed: {message}")
                print("\n🔧 Troubleshooting:")
                print("  - Check that the hostname/IP is correct")
                print("  - Ensure TrueNAS is running and accessible")
                print("  - Verify network connectivity")
                print("  - Verify the API key is correct")
                print("  - Run 'scale-compose validate' for detailed testing")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def _save_configuration(self) -> bool:
        """Save configuration to .env file and keyring."""
        print("\n💾 Step 4: Saving configuration...")
        
        # Prepare environment variables
        env_content = f"""# TrueNAS Scale Configuration
# Generated by Scale API Compose Pilot Setup Wizard

TRUENAS_HOST={self.config['host']}
TRUENAS_API_KEY={self.config['api_key']}
TRUENAS_SSL_VERIFY=true
"""
        
        try:
            # Save to .env file
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            
            print(f"✅ Configuration saved to {self.env_file}")
            
            # Optionally save to keyring for security
            if KEYRING_AVAILABLE and self._ask_yes_no("Save API key to secure keyring? (y/n): "):
                try:
                    keyring.set_password("scale-compose-pilot", self.config['host'], self.config['api_key'])
                    print("✅ API key saved to secure keyring")
                except Exception as e:
                    print(f"⚠️  Could not save to keyring: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def _ask_yes_no(self, question: str) -> bool:
        """Ask a yes/no question."""
        while True:
            answer = input(question).lower().strip()
            if answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")


def run_setup_wizard() -> bool:
    """
    Run the setup wizard.
    
    Returns:
        True if setup completed successfully
    """
    wizard = SetupWizard()
    return wizard.run()


# Fix the async issue in _test_connection by making it a separate function
async def _test_connection_async(host: str, api_key: str) -> tuple[bool, str]:
    """Test connection asynchronously."""
    try:
        manager = TrueNASDockerManager(host=host, api_key=api_key)
        
        await manager.connect()
        await manager.authenticate() 
        apps = await manager.list_apps()
        await manager.close()
        
        return True, f"Success! Found {len(apps)} apps."
        
    except Exception as e:
        return False, str(e)