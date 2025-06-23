"""
Configuration management for Scale API Compose Pilot
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".scale-compose"
DEFAULT_CONFIG = {
    "truenas_host": "",
    "api_key": "",
    "timeout": 30.0,
    "verify_ssl": False,
    "auto_discovery": True,
    "default_restart_policy": "unless-stopped",
    "log_level": "INFO"
}


class Config:
    """Configuration manager for Scale API Compose Pilot."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file (defaults to ~/.scale-compose)
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                self._config.update(file_config)
                logger.debug(f"Loaded config from {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
        
        # Override with environment variables
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "TRUENAS_HOST": "truenas_host",
            "TRUENAS_API_KEY": "api_key",
            "TRUENAS_TIMEOUT": "timeout",
            "TRUENAS_VERIFY_SSL": "verify_ssl",
            "SCALE_COMPOSE_LOG_LEVEL": "log_level"
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert types for specific keys
                if config_key == "timeout":
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"Invalid timeout value: {value}")
                        continue
                elif config_key == "verify_ssl":
                    value = value.lower() in ("true", "1", "yes", "on")
                
                self._config[config_key] = value
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Create parent directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.debug(f"Saved config to {self.config_path}")
        except IOError as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration with dictionary.
        
        Args:
            config_dict: Dictionary of configuration values
        """
        self._config.update(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()
    
    @property
    def truenas_host(self) -> str:
        """Get TrueNAS host."""
        return self.get("truenas_host", "")
    
    @property
    def api_key(self) -> str:
        """Get TrueNAS API key."""
        return self.get("api_key", "")
    
    @property
    def timeout(self) -> float:
        """Get connection timeout."""
        return self.get("timeout", 30.0)
    
    @property
    def verify_ssl(self) -> bool:
        """Get SSL verification setting."""
        return self.get("verify_ssl", False)
    
    @property
    def auto_discovery(self) -> bool:
        """Get auto-discovery setting."""
        return self.get("auto_discovery", True)
    
    @property
    def default_restart_policy(self) -> str:
        """Get default restart policy."""
        return self.get("default_restart_policy", "unless-stopped")
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get("log_level", "INFO")


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns:
        Configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config() -> None:
    """Reset global configuration instance."""
    global _config_instance
    _config_instance = None