"""
AI Agent Helper utilities for Scale API Compose Pilot.

This module provides AI-friendly interfaces and utilities to make it easier
for AI assistants to work with the Scale API Compose Pilot library.
"""

import json
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path

from .manager import TrueNASDockerManager
from .exceptions import TrueNASError


class AIHelper:
    """
    AI-friendly wrapper for TrueNAS Docker Manager operations.
    
    This class provides simplified, well-documented methods with clear
    return values and error handling designed for AI agents.
    """
    
    def __init__(self, host: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize AI Helper.
        
        Args:
            host: TrueNAS hostname/IP (optional, uses env var if not provided)
            api_key: TrueNAS API key (optional, uses env var if not provided)
        """
        self.manager = TrueNASDockerManager(host=host, api_key=api_key)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status in AI-friendly format.
        
        Returns:
            dict: {
                "connected": bool,
                "authenticated": bool,
                "apps": [{"name": str, "state": str, ...}],
                "app_count": int,
                "running_apps": int,
                "error": str or None
            }
        """
        result = {
            "connected": False,
            "authenticated": False,
            "apps": [],
            "app_count": 0,
            "running_apps": 0,
            "error": None
        }
        
        try:
            # Connect and authenticate
            await self.manager.connect()
            result["connected"] = True
            
            await self.manager.authenticate()
            result["authenticated"] = True
            
            # Get apps
            apps = await self.manager.list_apps()
            result["apps"] = apps
            result["app_count"] = len(apps)
            result["running_apps"] = len([app for app in apps if app.get('state') == 'RUNNING'])
            
        except TrueNASError as e:
            result["error"] = f"TrueNAS Error: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected Error: {str(e)}"
        finally:
            await self.manager.close()
        
        return result
    
    async def simple_deploy(self, compose_content: str, app_name: str) -> Dict[str, Any]:
        """
        Deploy a Docker Compose stack with simple string input.
        
        Args:
            compose_content: Docker Compose YAML as string
            app_name: Name for the TrueNAS app
            
        Returns:
            dict: {
                "success": bool,
                "app_name": str,
                "action": str,  # "created" or "updated"
                "message": str,
                "error": str or None
            }
        """
        result = {
            "success": False,
            "app_name": app_name,
            "action": None,
            "message": "",
            "error": None
        }
        
        try:
            # Parse YAML
            compose_data = yaml.safe_load(compose_content)
            
            async with self.manager as mgr:
                # Check if app exists
                existing = await mgr.get_app_details(app_name)
                action = "updated" if existing else "created"
                
                # Convert and deploy
                app_config = mgr._convert_compose_to_app_config(compose_data, app_name)
                
                if existing:
                    await mgr.update_app(app_name, app_config)
                else:
                    await mgr.create_app(app_config)
                
                result.update({
                    "success": True,
                    "action": action,
                    "message": f"Successfully {action} app '{app_name}'"
                })
                
        except Exception as e:
            result["error"] = str(e)
            result["message"] = f"Failed to deploy app '{app_name}': {str(e)}"
        
        return result
    
    async def app_operations(self, operations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Perform multiple app operations in batch.
        
        Args:
            operations: List of {"app": str, "action": str} dicts
                       Actions: "start", "stop", "delete", "status"
            
        Returns:
            list: [{"app": str, "action": str, "success": bool, "message": str, "error": str}]
        """
        results = []
        
        try:
            async with self.manager as mgr:
                for op in operations:
                    app_name = op.get("app")
                    action = op.get("action")
                    
                    result = {
                        "app": app_name,
                        "action": action,
                        "success": False,
                        "message": "",
                        "error": None
                    }
                    
                    try:
                        if action == "start":
                            await mgr.start_app(app_name)
                            result["message"] = f"Started app '{app_name}'"
                            result["success"] = True
                            
                        elif action == "stop":
                            await mgr.stop_app(app_name)
                            result["message"] = f"Stopped app '{app_name}'"
                            result["success"] = True
                            
                        elif action == "delete":
                            await mgr.delete_app(app_name)
                            result["message"] = f"Deleted app '{app_name}'"
                            result["success"] = True
                            
                        elif action == "status":
                            app_details = await mgr.get_app_details(app_name)
                            if app_details:
                                result["message"] = f"App '{app_name}' state: {app_details.get('state', 'Unknown')}"
                                result["success"] = True
                            else:
                                result["error"] = f"App '{app_name}' not found"
                                
                        else:
                            result["error"] = f"Unknown action: {action}"
                            
                    except Exception as e:
                        result["error"] = str(e)
                    
                    results.append(result)
                    
        except Exception as e:
            # If connection fails, mark all operations as failed
            for op in operations:
                results.append({
                    "app": op.get("app"),
                    "action": op.get("action"),
                    "success": False,
                    "message": "",
                    "error": f"Connection error: {str(e)}"
                })
        
        return results
    
    def validate_compose(self, compose_content: str) -> Dict[str, Any]:
        """
        Validate Docker Compose content without deploying.
        
        Args:
            compose_content: Docker Compose YAML as string
            
        Returns:
            dict: {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "services": List[str],
                "supported_features": List[str],
                "unsupported_features": List[str]
            }
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "services": [],
            "supported_features": [],
            "unsupported_features": []
        }
        
        try:
            # Parse YAML
            compose_data = yaml.safe_load(compose_content)
            
            if not isinstance(compose_data, dict):
                result["errors"].append("Invalid YAML format")
                return result
            
            services = compose_data.get('services', {})
            if not services:
                result["errors"].append("No services defined")
                return result
            
            result["services"] = list(services.keys())
            
            # Check for multi-service limitation
            if len(services) > 1:
                result["errors"].append("Only single-service compose files are supported")
                return result
            
            service_name, service_config = next(iter(services.items()))
            
            # Check required image
            if not service_config.get('image'):
                result["errors"].append("Service must specify an image")
                return result
            
            # Check supported features
            if 'image' in service_config:
                result["supported_features"].append("image")
            if 'ports' in service_config:
                result["supported_features"].append("ports")
            if 'environment' in service_config:
                result["supported_features"].append("environment")
            if 'volumes' in service_config:
                result["supported_features"].append("volumes")
            if 'restart' in service_config:
                result["supported_features"].append("restart")
            
            # Check unsupported features
            unsupported = ['build', 'networks', 'secrets', 'configs', 'deploy']
            for feature in unsupported:
                if feature in service_config:
                    result["unsupported_features"].append(feature)
                    result["warnings"].append(f"'{feature}' is not fully supported and will be ignored")
            
            # If we get here, it's valid
            result["valid"] = True
            
        except yaml.YAMLError as e:
            result["errors"].append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
        
        return result
    
    def generate_compose_template(self, 
                                image: str, 
                                ports: Optional[List[str]] = None,
                                environment: Optional[Dict[str, str]] = None,
                                volumes: Optional[List[str]] = None) -> str:
        """
        Generate a Docker Compose template compatible with TrueNAS.
        
        Args:
            image: Docker image (e.g., "nginx:latest")
            ports: List of port mappings (e.g., ["8080:80"])
            environment: Environment variables
            volumes: List of volume mappings (e.g., ["/host:/container"])
            
        Returns:
            str: Docker Compose YAML string
        """
        compose = {
            'services': {
                'app': {
                    'image': image,
                    'restart': 'unless-stopped'
                }
            }
        }
        
        if ports:
            compose['services']['app']['ports'] = ports
        
        if environment:
            compose['services']['app']['environment'] = environment
        
        if volumes:
            compose['services']['app']['volumes'] = volumes
        
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)


def create_ai_summary() -> Dict[str, Any]:
    """
    Create a comprehensive summary for AI agents about this library.
    
    Returns:
        dict: Complete information about the library's capabilities
    """
    return {
        "library_name": "scale-api-compose-pilot",
        "purpose": "Manage Docker containers on TrueNAS Scale via WebSocket API",
        "ai_friendly_features": [
            "Simple string-based Docker Compose deployment",
            "Batch operations with clear success/failure reporting",
            "Comprehensive validation before deployment",
            "Template generation for common use cases",
            "Structured error reporting",
            "Status checking with detailed information"
        ],
        "main_classes": {
            "TrueNASDockerManager": "Core management class with async context manager",
            "AIHelper": "Simplified interface designed for AI agents"
        },
        "key_methods": {
            "AIHelper.get_system_status()": "Get complete system status",
            "AIHelper.simple_deploy(compose_str, name)": "Deploy from string",
            "AIHelper.app_operations(operations_list)": "Batch operations",
            "AIHelper.validate_compose(compose_str)": "Validate without deploying",
            "AIHelper.generate_compose_template()": "Create valid templates"
        },
        "supported_compose_features": [
            "Single service only",
            "Docker images (no build contexts)",
            "Port forwarding",
            "Environment variables", 
            "Volume mounts",
            "Restart policies"
        ],
        "common_ai_usage_patterns": [
            "Check system status before operations",
            "Validate compose files before deployment",
            "Use batch operations for multiple apps",
            "Generate templates for common scenarios",
            "Handle errors gracefully with structured responses"
        ],
        "example_usage": {
            "check_status": "await AIHelper().get_system_status()",
            "deploy_nginx": "await AIHelper().simple_deploy(compose_yaml, 'my-nginx')",
            "batch_ops": "await AIHelper().app_operations([{'app': 'nginx', 'action': 'start'}])"
        }
    }