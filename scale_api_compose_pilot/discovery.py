"""
TrueNAS Scale Network Discovery Module

Auto-discovers TrueNAS Scale systems on the local network using mDNS/Bonjour.
"""

import socket
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TrueNASSystem:
    """Represents a discovered TrueNAS Scale system."""
    hostname: str
    ip_address: str
    port: int
    web_url: str
    services: List[str]
    
    def __str__(self):
        return f"TrueNAS at {self.hostname} ({self.ip_address}:{self.port})"


class TrueNASDiscoveryListener(ServiceListener):
    """Service listener for TrueNAS Scale systems."""
    
    def __init__(self):
        self.discovered_systems: List[TrueNASSystem] = []
        self.logger = logging.getLogger(__name__)
    
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is discovered."""
        info = zc.get_service_info(type_, name)
        if info:
            self._process_service_info(info, type_)
    
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed."""
        pass
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated."""
        pass
    
    def _process_service_info(self, info, service_type: str) -> None:
        """Process discovered service information."""
        if not info.addresses:
            return
            
        # Extract basic info
        ip_address = socket.inet_ntoa(info.addresses[0])
        hostname = info.server.rstrip('.')
        port = info.port
        
        # Check if this looks like TrueNAS
        if self._is_truenas_service(info, service_type):
            # Check if we already have this system
            existing = next(
                (sys for sys in self.discovered_systems 
                 if sys.ip_address == ip_address), 
                None
            )
            
            if existing:
                # Add service type to existing system
                if service_type not in existing.services:
                    existing.services.append(service_type)
            else:
                # Create new system entry
                web_url = f"https://{ip_address}:{port}" if port != 80 else f"https://{ip_address}"
                
                system = TrueNASSystem(
                    hostname=hostname,
                    ip_address=ip_address,
                    port=port,
                    web_url=web_url,
                    services=[service_type]
                )
                
                self.discovered_systems.append(system)
                self.logger.info(f"Discovered TrueNAS system: {system}")
    
    def _is_truenas_service(self, info, service_type: str) -> bool:
        """Check if this service looks like TrueNAS."""
        # Check service type patterns
        truenas_service_patterns = [
            '_http._tcp.local.',
            '_device-info._tcp.local.',
            '_smb._tcp.local.'
        ]
        
        if service_type not in truenas_service_patterns:
            return False
        
        # Check hostname patterns
        hostname = info.server.lower()
        truenas_hostname_patterns = [
            'truenas',
            'nas',
            'freenas'  # Legacy
        ]
        
        # Check if hostname contains TrueNAS-related terms
        for pattern in truenas_hostname_patterns:
            if pattern in hostname:
                return True
        
        # Check TXT records for TrueNAS-specific info
        if info.properties:
            properties = {k.decode('utf-8').lower(): v.decode('utf-8').lower() 
                         for k, v in info.properties.items()}
            
            # Look for TrueNAS-specific properties
            if any(key in properties for key in ['truenas', 'freenas', 'ixsystems']):
                return True
                
            # Check for common TrueNAS service properties
            if service_type == '_http._tcp.local.':
                # Web interface usually runs on port 80 or 443
                if info.port in [80, 443]:
                    return True
        
        return False


class TrueNASDiscovery:
    """TrueNAS Scale network discovery service."""
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize discovery service.
        
        Args:
            timeout: Discovery timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        if not ZEROCONF_AVAILABLE:
            self.logger.warning(
                "zeroconf library not available. "
                "Install with: pip install zeroconf"
            )
    
    def discover_systems(self) -> List[TrueNASSystem]:
        """
        Discover TrueNAS Scale systems on the local network.
        
        Returns:
            List of discovered TrueNAS systems
        """
        if not ZEROCONF_AVAILABLE:
            self.logger.error("zeroconf library required for discovery")
            return []
        
        self.logger.info("Starting TrueNAS Scale discovery...")
        
        zeroconf = Zeroconf()
        listener = TrueNASDiscoveryListener()
        
        # Services to look for
        services = [
            "_http._tcp.local.",
            "_device-info._tcp.local.", 
            "_smb._tcp.local."
        ]
        
        browsers = []
        try:
            # Start service browsers
            for service in services:
                browser = ServiceBrowser(zeroconf, service, listener)
                browsers.append(browser)
            
            # Wait for discovery
            self.logger.info(f"Scanning for {self.timeout} seconds...")
            time.sleep(self.timeout)
            
            systems = listener.discovered_systems
            self.logger.info(f"Discovery complete. Found {len(systems)} TrueNAS systems")
            
            return systems
            
        except Exception as e:
            self.logger.error(f"Discovery failed: {e}")
            return []
        finally:
            # Clean up
            for browser in browsers:
                browser.cancel()
            zeroconf.close()
    
    def discover_single_system(self, timeout: Optional[float] = None) -> Optional[TrueNASSystem]:
        """
        Discover a single TrueNAS system (returns first found).
        
        Args:
            timeout: Optional timeout override
            
        Returns:
            First discovered TrueNAS system or None
        """
        if timeout:
            old_timeout = self.timeout
            self.timeout = timeout
        
        try:
            systems = self.discover_systems()
            return systems[0] if systems else None
        finally:
            if timeout:
                self.timeout = old_timeout
    
    def verify_system(self, ip_address: str, port: int = 443) -> bool:
        """
        Verify if a system at the given address is TrueNAS Scale.
        
        Args:
            ip_address: IP address to check
            port: Port to check (default: 443)
            
        Returns:
            True if system appears to be TrueNAS Scale
        """
        try:
            import requests
            
            # Try to access the web interface
            url = f"https://{ip_address}:{port}"
            response = requests.get(
                url, 
                timeout=5, 
                verify=False,  # TrueNAS often uses self-signed certs
                allow_redirects=True
            )
            
            # Check for TrueNAS-specific content
            content = response.text.lower()
            truenas_indicators = [
                'truenas',
                'ixsystems',
                'freenas',
                'scale'
            ]
            
            return any(indicator in content for indicator in truenas_indicators)
            
        except Exception as e:
            self.logger.debug(f"Verification failed for {ip_address}:{port}: {e}")
            return False


def quick_discover() -> Optional[TrueNASSystem]:
    """
    Quick discovery function for finding a TrueNAS system.
    
    Returns:
        First discovered TrueNAS system or None
    """
    discovery = TrueNASDiscovery(timeout=3.0)
    return discovery.discover_single_system()


def discover_all(timeout: float = 5.0) -> List[TrueNASSystem]:
    """
    Discover all TrueNAS systems on the network.
    
    Args:
        timeout: Discovery timeout in seconds
        
    Returns:
        List of all discovered TrueNAS systems
    """
    discovery = TrueNASDiscovery(timeout=timeout)
    return discovery.discover_systems()