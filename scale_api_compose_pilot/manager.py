"""
TrueNAS Docker Manager - Main management class.
"""

import os
import yaml
from typing import Dict, Optional
import logging
from dotenv import load_dotenv

# Handle TrueNAS API client import with auto-installation
try:
    from truenas_api_client import Client
except ImportError:
    print("🔧 TrueNAS API Client not found. Installing...")
    from .dependency_installer import install_truenas_api_client_with_fallback
    
    if install_truenas_api_client_with_fallback():
        from truenas_api_client import Client
        print("✅ TrueNAS API Client ready!")
    else:
        print("❌ Failed to install TrueNAS API Client")
        print("Please manually install with:")
        print("   pip install git+https://github.com/truenas/api_client.git")
        raise ImportError("TrueNAS API Client is required but not installed")

from .exceptions import (
    TrueNASConnectionError, 
    TrueNASAuthenticationError, 
    TrueNASAPIError,
    DockerComposeError
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TrueNASDockerManager:
    """TrueNAS Scale Docker management using the official API client."""
    
    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize TrueNAS Docker Manager.
        
        Args:
            host: TrueNAS hostname/IP (defaults to TRUENAS-HOST env var)
            api_key: TrueNAS API key (defaults to TRUENAS-API-KEY env var)
        """
        self.host = (host or os.getenv('TRUENAS_HOST', '')).replace('https://', '').replace('http://', '')
        self.api_key = api_key or os.getenv('TRUENAS_API_KEY')
        self.client = None
        self.connected = False
        
        if not self.host:
            raise ValueError("TrueNAS host must be provided via parameter or TRUENAS_HOST environment variable")
        if not self.api_key:
            raise ValueError("TrueNAS API key must be provided via parameter or TRUENAS_API_KEY environment variable")
        
    async def connect(self) -> bool:
        """
        Establish connection to TrueNAS.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            TrueNASConnectionError: If connection fails
        """
        uri = f"wss://{self.host}/websocket"
        logger.info(f"Connecting to {uri}")
        
        try:
            self.client = Client(uri=uri, verify_ssl=False)
            self.client.__enter__()
            logger.info("WebSocket connection established")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise TrueNASConnectionError(f"Failed to connect to TrueNAS: {e}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with TrueNAS using API key.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            TrueNASAuthenticationError: If authentication fails
        """
        if not self.client or not self.connected:
            raise TrueNASConnectionError("Not connected to TrueNAS")
            
        try:
            result = self.client.call("auth.login_with_api_key", self.api_key)
            if result:
                logger.info("Authentication successful")
                return True
            else:
                raise TrueNASAuthenticationError("Authentication failed - invalid API key")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise TrueNASAuthenticationError(f"Authentication failed: {e}")
    
    async def call_api(self, method: str, *args):
        """
        Make API call to TrueNAS.
        
        Args:
            method: API method name
            *args: Method arguments
            
        Returns:
            API response
            
        Raises:
            TrueNASAPIError: If API call fails
        """
        if not self.client or not self.connected:
            raise TrueNASConnectionError("Not connected to TrueNAS")
        
        try:
            return self.client.call(method, *args)
        except Exception as e:
            raise TrueNASAPIError(f"API call '{method}' failed: {e}")
    
    async def list_apps(self) -> list:
        """
        List all installed apps/containers.
        
        Returns:
            list: List of app dictionaries
        """
        return await self.call_api("app.query")
    
    async def get_app_details(self, app_name: str) -> Optional[Dict]:
        """
        Get details for a specific app.
        
        Args:
            app_name: Name of the app
            
        Returns:
            dict: App details or None if not found
        """
        apps = await self.list_apps()
        for app in apps:
            if app.get('name') == app_name:
                return app
        return None
    
    async def create_app(self, app_config: Dict):
        """
        Create a new app from configuration.
        
        Args:
            app_config: TrueNAS app configuration dictionary
            
        Returns:
            API response
        """
        return await self.call_api("app.create", app_config)
    
    async def start_app(self, app_name: str):
        """
        Start an app.
        
        Args:
            app_name: Name of the app to start
            
        Returns:
            API response
        """
        return await self.call_api("app.start", app_name)
    
    async def stop_app(self, app_name: str):
        """
        Stop an app.
        
        Args:
            app_name: Name of the app to stop
            
        Returns:
            API response
        """
        return await self.call_api("app.stop", app_name)
    
    async def delete_app(self, app_name: str):
        """
        Delete an app.
        
        Args:
            app_name: Name of the app to delete
            
        Returns:
            API response
        """
        return await self.call_api("app.delete", app_name)
    
    async def update_app(self, app_name: str, app_config: Dict):
        """
        Update an existing app.
        
        Args:
            app_name: Name of the app to update
            app_config: New app configuration
            
        Returns:
            API response
        """
        return await self.call_api("app.update", app_name, app_config)
    
    async def deploy_compose_stack(self, compose_file_path: str, app_name: str):
        """
        Deploy a Docker Compose stack as a TrueNAS app.
        
        Args:
            compose_file_path: Path to docker-compose.yml file
            app_name: Name for the TrueNAS app
            
        Returns:
            API response
            
        Raises:
            DockerComposeError: If compose file conversion fails
        """
        try:
            with open(compose_file_path, 'r') as f:
                compose_content = yaml.safe_load(f)
        except Exception as e:
            raise DockerComposeError(f"Failed to load compose file: {e}")
        
        # Convert Docker Compose to TrueNAS app configuration
        app_config = self._convert_compose_to_app_config(compose_content, app_name)
        
        # Check if app already exists
        existing_app = await self.get_app_details(app_name)
        
        if existing_app:
            logger.info(f"Updating existing app: {app_name}")
            return await self.update_app(app_name, app_config)
        else:
            logger.info(f"Creating new app: {app_name}")
            return await self.create_app(app_config)
    
    @staticmethod
    def _convert_compose_to_app_config(compose_data: Dict, app_name: str) -> Dict:
        """
        Convert Docker Compose format to TrueNAS app configuration.
        
        Args:
            compose_data: Docker compose data
            app_name: Name for the app
            
        Returns:
            dict: TrueNAS app configuration
            
        Raises:
            DockerComposeError: If conversion fails
        """
        services = compose_data.get('services', {})
        
        # For now, handle single service containers
        if len(services) != 1:
            raise DockerComposeError("Currently only single-service compose files are supported")
        
        service_name, service_config = next(iter(services.items()))
        
        # Extract image info
        image = service_config.get('image', '')
        if not image:
            raise DockerComposeError("Service must specify an image")
        
        image_parts = image.split(':')
        repository = image_parts[0]
        tag = image_parts[1] if len(image_parts) > 1 else 'latest'
        
        app_config = {
            "name": app_name,
            "image": {
                "repository": repository,
                "tag": tag
            },
            "port_forwards": [],
            "environment": service_config.get('environment', {}),
            "volumes": [],
            "restart_policy": "unless-stopped"
        }
        
        # Convert ports
        ports = service_config.get('ports', [])
        for port in ports:
            if isinstance(port, str) and ':' in port:
                try:
                    host_port, container_port = port.split(':')
                    app_config["port_forwards"].append({
                        "container_port": int(container_port),
                        "host_port": int(host_port)
                    })
                except ValueError as e:
                    raise DockerComposeError(f"Invalid port mapping '{port}': {e}")
        
        # Convert volumes
        volumes = service_config.get('volumes', [])
        for volume in volumes:
            if isinstance(volume, str) and ':' in volume:
                volume_parts = volume.split(':')
                if len(volume_parts) >= 2:
                    host_path = volume_parts[0]
                    container_path = volume_parts[1]
                    mode = volume_parts[2] if len(volume_parts) > 2 else "rw"
                    
                    app_config["volumes"].append({
                        "host_path": host_path,
                        "container_path": container_path,
                        "mode": mode
                    })
        
        return app_config
    
    async def close(self):
        """Close API client connection."""
        if self.client:
            try:
                self.client.__exit__(None, None, None)
                logger.info("API client connection closed")
            except Exception:
                pass
            finally:
                self.connected = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()