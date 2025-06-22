"""
Test cases for TrueNAS Docker Manager.
"""

import pytest
from unittest.mock import Mock, patch
from scale_api_compose_pilot import TrueNASDockerManager
from scale_api_compose_pilot.exceptions import (
    TrueNASConnectionError,
    TrueNASAuthenticationError,
    DockerComposeError
)


def test_manager_initialization():
    """Test manager initialization with environment variables."""
    with patch.dict('os.environ', {'TRUENAS-HOST': 'test.local', 'TRUENAS-API-KEY': 'test-key'}):
        manager = TrueNASDockerManager()
        assert manager.host == 'test.local'
        assert manager.api_key == 'test-key'
        assert not manager.connected


def test_manager_initialization_with_params():
    """Test manager initialization with explicit parameters."""
    manager = TrueNASDockerManager(host='custom.local', api_key='custom-key')
    assert manager.host == 'custom.local'
    assert manager.api_key == 'custom-key'


def test_manager_initialization_missing_host():
    """Test manager initialization fails without host."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="TrueNAS host must be provided"):
            TrueNASDockerManager()


def test_manager_initialization_missing_api_key():
    """Test manager initialization fails without API key."""
    with patch.dict('os.environ', {'TRUENAS-HOST': 'test.local'}, clear=True):
        with pytest.raises(ValueError, match="TrueNAS API key must be provided"):
            TrueNASDockerManager()


def test_convert_compose_to_app_config():
    """Test Docker Compose to TrueNAS app config conversion."""
    compose_data = {
        'services': {
            'webapp': {
                'image': 'nginx:latest',
                'ports': ['8080:80'],
                'environment': {'ENV': 'prod'},
                'volumes': ['/host:/container']
            }
        }
    }
    
    config = TrueNASDockerManager._convert_compose_to_app_config(compose_data, 'test-app')
    
    assert config['name'] == 'test-app'
    assert config['image']['repository'] == 'nginx'
    assert config['image']['tag'] == 'latest'
    assert len(config['port_forwards']) == 1
    assert config['port_forwards'][0]['host_port'] == 8080
    assert config['port_forwards'][0]['container_port'] == 80
    assert config['environment']['ENV'] == 'prod'
    assert len(config['volumes']) == 1


def test_convert_compose_multi_service_error():
    """Test error when compose file has multiple services."""
    compose_data = {
        'services': {
            'webapp': {'image': 'nginx:latest'},
            'db': {'image': 'postgres:13'}
        }
    }
    
    with pytest.raises(DockerComposeError, match="only single-service compose files are supported"):
        TrueNASDockerManager._convert_compose_to_app_config(compose_data, 'test-app')


def test_convert_compose_no_image_error():
    """Test error when service has no image."""
    compose_data = {
        'services': {
            'webapp': {'ports': ['8080:80']}
        }
    }
    
    with pytest.raises(DockerComposeError, match="Service must specify an image"):
        TrueNASDockerManager._convert_compose_to_app_config(compose_data, 'test-app')


@pytest.mark.asyncio
async def test_connect_without_client():
    """Test connection error handling."""
    manager = TrueNASDockerManager(host='invalid.local', api_key='test-key')
    
    with patch('scale_api_compose_pilot.manager.Client') as mock_client:
        mock_client.side_effect = Exception("Connection failed")
        
        with pytest.raises(TrueNASConnectionError):
            await manager.connect()


def test_host_url_cleaning():
    """Test that URLs are properly cleaned."""
    manager = TrueNASDockerManager(host='https://test.local', api_key='test-key')
    assert manager.host == 'test.local'
    
    manager = TrueNASDockerManager(host='http://test.local', api_key='test-key') 
    assert manager.host == 'test.local'