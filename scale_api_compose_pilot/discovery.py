
"""
TrueNAS Scale Network Scanner Module

Finds TrueNAS Scale systems on the local network using HTTP fingerprinting.
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

# No mDNS - user doesn't want it!

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
    # iXsystems-specific identifiers (highest priority)
    'ixsystems_branding': [
        'iX Systems',
        'ix-copyright-line',
        'ix-logo',
        'ixsystems',
        'truenas',
        'freenas'
    ],
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


# No mDNS classes - user doesn't want mDNS!


class TrueNASScanner:
    """TrueNAS Scale network scanner - HTTP fingerprinting only."""

    def __init__(self, timeout: float = 5.0):
        """
        Initialize scanner.

        Args:
            timeout: HTTP timeout in seconds
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

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
                    # Use browser-like headers to avoid TrueNAS security blocking
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    response = requests.get(
                        url,
                        timeout=5,
                        verify=False,  # TrueNAS often uses self-signed certs
                        allow_redirects=True,
                        headers=headers
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
        Simple approach: look for specific TrueNAS strings.

        Args:
            content: HTML content to analyze

        Returns:
            Tuple of (is_truenas, confidence_score)
        """
        content_lower = content.lower()
        
        # Simple TrueNAS identifiers - if ANY of these are found, it's TrueNAS
        truenas_strings = [
            'ix systems',
            'ix-copyright-line',
            'ix-logo',
            'ix-dark',  # Found in actual TrueNAS HTML
            'ix-root',  # Found in actual TrueNAS HTML
            'ixsystems',
            'truenas',
            'freenas'
        ]
        
        # Check for any TrueNAS identifier
        for identifier in truenas_strings:
            if identifier in content_lower:
                self.logger.debug(f"Found TrueNAS identifier: '{identifier}'")
                return True, 1.0  # High confidence when we find explicit TrueNAS strings
        
        # No TrueNAS identifiers found
        self.logger.debug("No TrueNAS identifiers found in content")
        return False, 0.0

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

    def scan_all(self) -> List[TrueNASSystem]:
        """
        Scan LAN for TrueNAS systems using HTTP fingerprinting only.

        Returns:
            List of all found TrueNAS systems
        """
        self.logger.info("Starting LAN scanning...")
        systems = self.scan_lan_for_truenas()
        
        # Sort by confidence score
        systems.sort(key=lambda s: s.confidence, reverse=True)
        
        self.logger.info(f"Scan complete. Found {len(systems)} TrueNAS systems")
        return systems


def quick_scan() -> Optional[TrueNASSystem]:
    """
    Quick scan function for finding a TrueNAS system.

    Returns:
        First found TrueNAS system or None
    """
    scanner = TrueNASScanner(timeout=3.0)
    systems = scanner.scan_lan_for_truenas()
    return systems[0] if systems else None


def scan_all(timeout: float = 5.0) -> List[TrueNASSystem]:
    """
    Scan all TrueNAS systems on the network.

    Args:
        timeout: HTTP timeout in seconds

    Returns:
        List of all found TrueNAS systems
    """
    scanner = TrueNASScanner(timeout=timeout)
    return scanner.scan_lan_for_truenas()
