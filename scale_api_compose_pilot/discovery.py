"""
TrueNAS Scale Network Discovery Module

Auto-discovers TrueNAS Scale systems on the local network using:
1. mDNS/Bonjour service discovery
2. LAN scanning with HTTP fingerprinting
"""

import socket
import time
import logging
import subprocess
import ipaddress
import concurrent.futures
import requests
from typing import List, Dict, Optional, Set
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
    discovery_method: str = "mDNS"
    confidence: float = 1.0

    def __str__(self):
        return f"TrueNAS at {self.hostname} ({self.ip_address}:{self.port})"


# TrueNAS fingerprint patterns based on login page analysis
TRUENAS_FINGERPRINTS = {
    # CSS variables specific to TrueNAS
    'css_variables': [
        '--sidenav-width:240px',
        '--font-family-header:"Titillium Web"',
        '--font-family-body:"IBM Plex Sans"',
        '--font-family-monospace:"Droid Sans Mono"',
        'ix-dark',
        'mat-',
        'mdc-'
    ],
    # HTML attributes unique to TrueNAS
    'html_attributes': [
        'data-critters-container',
        'id="main-page-title"',
        'assets/favicons/apple-touch-icon.png',
        'msapplication-TileColor',
        'msapplication-config'
    ],
    # Font families used by TrueNAS
    'fonts': [
        'Titillium Web',
        'IBM Plex Sans',
        'Droid Sans Mono',
        'Roboto'
    ],
    # Angular Material components
    'angular_material': [
        '--mat-',
        '--mdc-',
        'mat-option',
        'mat-card',
        'angular',
        'material'
    ],
    # Color scheme indicators
    'color_scheme': [
        '#2d89ef',
        '#0095d5',
        '--primary:#',
        '--bg1:',
        '--fg1:'
    ]
}


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
        return self._fingerprint_truenas(ip_address, port)[0]

    def _fingerprint_truenas(self, ip_address: str, port: int = 443) -> tuple[bool, float]:
        """
        Advanced fingerprinting of TrueNAS systems using login page analysis.

        Args:
            ip_address: IP address to check
            port: Port to check (default: 443)

        Returns:
            Tuple of (is_truenas, confidence_score)
        """
        try:
            # Try both HTTPS and HTTP
            for scheme in ['https', 'http']:
                try:
                    url = f"{scheme}://{ip_address}:{port}"
                    response = requests.get(
                        url,
                        timeout=5,
                        verify=False,  # TrueNAS often uses self-signed certs
                        allow_redirects=True,
                        headers={'User-Agent': 'TrueNAS-Discovery/1.0'}
                    )

                    if response.status_code == 200:
                        return self._analyze_truenas_content(response.text)

                except Exception:
                    continue

            return False, 0.0

        except Exception as e:
            self.logger.debug(f"Fingerprinting failed for {ip_address}:{port}: {e}")
            return False, 0.0

    def _analyze_truenas_content(self, content: str) -> tuple[bool, float]:
        """
        Analyze HTTP response content for TrueNAS fingerprints.

        Args:
            content: HTML content to analyze

        Returns:
            Tuple of (is_truenas, confidence_score)
        """
        content_lower = content.lower()
        score = 0.0
        max_score = 0.0

        # Check each fingerprint category
        for category, patterns in TRUENAS_FINGERPRINTS.items():
            category_weight = {
                'css_variables': 0.3,
                'html_attributes': 0.25,
                'fonts': 0.2,
                'angular_material': 0.15,
                'color_scheme': 0.1
            }.get(category, 0.1)

            matches = sum(1 for pattern in patterns if pattern.lower() in content_lower)
            if matches > 0:
                category_score = (matches / len(patterns)) * category_weight
                score += category_score
                self.logger.debug(f"Fingerprint category '{category}': {matches}/{len(patterns)} matches")

            max_score += category_weight

        # Normalize score
        confidence = score / max_score if max_score > 0 else 0.0

        # Additional specific checks
        if 'titillium web' in content_lower and 'ibm plex sans' in content_lower:
            confidence += 0.1  # Strong font combination indicator

        if 'data-critters-container' in content_lower:
            confidence += 0.1  # Very specific to Angular apps like TrueNAS

        if '--sidenav-width:240px' in content_lower:
            confidence += 0.1  # Specific TrueNAS UI measurement

        # Consider it TrueNAS if confidence is above threshold
        is_truenas = confidence >= 0.3

        self.logger.debug(f"TrueNAS fingerprint confidence: {confidence:.2f}")
        return is_truenas, confidence

    def scan_lan_for_truenas(self, network: Optional[str] = None) -> List[TrueNASSystem]:
        """
        Scan LAN for TrueNAS systems using network scanning and HTTP fingerprinting.

        Args:
            network: Network CIDR to scan (e.g., '192.168.1.0/24').
                    If None, attempts to detect local network.

        Returns:
            List of discovered TrueNAS systems
        """
        if network is None:
            network = self._detect_local_network()
            if not network:
                self.logger.warning("Could not detect local network for scanning")
                return []

        self.logger.info(f"Scanning network {network} for TrueNAS systems...")

        try:
            network_obj = ipaddress.ip_network(network, strict=False)
            hosts = list(network_obj.hosts())

            # Limit scan to reasonable size
            if len(hosts) > 254:
                self.logger.warning(f"Network {network} too large ({len(hosts)} hosts), limiting scan")
                hosts = hosts[:254]

            discovered = []

            # Parallel scanning for speed
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                future_to_ip = {
                    executor.submit(self._scan_host_for_truenas, str(ip)): str(ip)
                    for ip in hosts
                }

                for future in concurrent.futures.as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result()
                        if result:
                            discovered.append(result)
                            self.logger.info(f"Found TrueNAS system via LAN scan: {result}")
                    except Exception as e:
                        self.logger.debug(f"Scan failed for {ip}: {e}")

            self.logger.info(f"LAN scan complete. Found {len(discovered)} TrueNAS systems")
            return discovered

        except Exception as e:
            self.logger.error(f"LAN scan failed: {e}")
            return []

    def _detect_local_network(self) -> Optional[str]:
        """
        Detect the local network CIDR for scanning.

        Returns:
            Network CIDR string or None if detection fails
        """
        try:
            # Get default route to determine local network
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Assume /24 network for most home/office networks
            network_parts = local_ip.split('.')
            network_base = '.'.join(network_parts[:3]) + '.0'
            return f"{network_base}/24"

        except Exception as e:
            self.logger.debug(f"Network detection failed: {e}")
            return None

    def _scan_host_for_truenas(self, ip: str) -> Optional[TrueNASSystem]:
        """
        Scan a single host for TrueNAS services.

        Args:
            ip: IP address to scan

        Returns:
            TrueNASSystem if found, None otherwise
        """
        # Check common TrueNAS ports
        ports = [443, 80]

        for port in ports:
            try:
                # Quick port check first
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, port))
                sock.close()

                if result == 0:  # Port is open
                    is_truenas, confidence = self._fingerprint_truenas(ip, port)
                    if is_truenas:
                        # Try to get hostname
                        try:
                            hostname = socket.gethostbyaddr(ip)[0]
                        except:
                            hostname = ip

                        scheme = 'https' if port == 443 else 'http'
                        web_url = f"{scheme}://{ip}:{port}" if port != 80 else f"{scheme}://{ip}"

                        return TrueNASSystem(
                            hostname=hostname,
                            ip_address=ip,
                            port=port,
                            web_url=web_url,
                            services=['http_scan'],
                            discovery_method='LAN_scan',
                            confidence=confidence
                        )
            except Exception:
                continue

        return None

    def discover_all_methods(self) -> List[TrueNASSystem]:
        """
        Discover TrueNAS systems using all available methods.

        Returns:
            List of all discovered TrueNAS systems from all methods
        """
        all_systems = []
        seen_ips = set()

        # Method 1: mDNS discovery
        if ZEROCONF_AVAILABLE:
            self.logger.info("Starting mDNS discovery...")
            mdns_systems = self.discover_systems()
            for system in mdns_systems:
                if system.ip_address not in seen_ips:
                    all_systems.append(system)
                    seen_ips.add(system.ip_address)

        # Method 2: LAN scanning
        self.logger.info("Starting LAN scanning...")
        lan_systems = self.scan_lan_for_truenas()
        for system in lan_systems:
            if system.ip_address not in seen_ips:
                all_systems.append(system)
                seen_ips.add(system.ip_address)

        # Sort by confidence score
        all_systems.sort(key=lambda s: s.confidence, reverse=True)

        self.logger.info(f"Discovery complete. Found {len(all_systems)} unique TrueNAS systems")
        return all_systems


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
