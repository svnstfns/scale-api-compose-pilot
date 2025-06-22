# Scale API Compose Pilot

Pilot Docker Compose workloads to TrueNAS Scale via WebSocket API - AI-friendly automation tool.

## Features

- 🐳 **Docker Compose Support**: Deploy Docker Compose stacks to TrueNAS Scale
- 🔌 **WebSocket API**: Uses TrueNAS Scale's modern WebSocket API (Electric Eel)
- 🛠️ **CLI Interface**: Easy-to-use command-line tool
- 📦 **Python Library**: Programmatic access for automation
- 🔒 **Authentication**: Secure API key authentication
- 🔄 **App Management**: Start, stop, delete, and update apps

## Installation

### Prerequisites

The TrueNAS API client is required but not available on PyPI. Install it first:

```bash
pip install git+https://github.com/truenas/api_client.git
```

### From PyPI (when published)

```bash
pip install scale-api-compose-pilot
```

### From Source

```bash
git clone https://github.com/svnstfns/scale-api-compose-pilot.git
cd scale-api-compose-pilot
pip install git+https://github.com/truenas/api_client.git  # Install API client first
pip install -e .
```

## Quick Start

### Environment Setup

Create a `.env` file:

```env
TRUENAS-HOST=your-truenas-host.local
TRUENAS-API-KEY=your-api-key-here
```

### CLI Usage

```bash
# List all apps
scale-compose list

# Deploy a Docker Compose stack
scale-compose deploy ./docker-compose.yml my-app

# Start/stop apps
scale-compose start my-app
scale-compose stop my-app

# Delete an app
scale-compose delete my-app --force
```

### Python Library Usage

```python
import asyncio
from scale_api_compose_pilot import TrueNASDockerManager

async def main():
    # Using environment variables
    async with TrueNASDockerManager() as manager:
        # List apps
        apps = await manager.list_apps()
        print(f"Found {len(apps)} apps")
        
        # Deploy Docker Compose
        await manager.deploy_compose_stack(
            './docker-compose.yml', 
            'my-app'
        )

# Or with explicit credentials
async def with_credentials():
    manager = TrueNASDockerManager(
        host="truenas.local",
        api_key="your-api-key"
    )
    
    await manager.connect()
    await manager.authenticate()
    
    try:
        apps = await manager.list_apps()
        print(f"Found {len(apps)} apps")
    finally:
        await manager.close()

asyncio.run(main())
```

## Docker Compose Support

### Supported Features

- ✅ Container images
- ✅ Port forwarding
- ✅ Environment variables
- ✅ Volume mounts
- ✅ Restart policies

### Limitations

- ❌ Multi-service compose files (single service only)
- ❌ Custom networks
- ❌ Build contexts
- ❌ Secrets and configs

### Example Compose File

```yaml
services:
  webapp:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - ENV=production
    volumes:
      - /host/data:/var/www/html
    restart: unless-stopped
```

## API Reference

### TrueNASDockerManager

#### Methods

- `connect()` - Establish WebSocket connection
- `authenticate()` - Authenticate with API key
- `list_apps()` - Get all installed apps
- `get_app_details(app_name)` - Get specific app details
- `create_app(app_config)` - Create new app
- `start_app(app_name)` - Start an app
- `stop_app(app_name)` - Stop an app
- `delete_app(app_name)` - Delete an app
- `deploy_compose_stack(file_path, app_name)` - Deploy Docker Compose
- `close()` - Close connection

#### Context Manager

```python
async with TrueNASDockerManager() as manager:
    # Automatically connects and authenticates
    apps = await manager.list_apps()
    # Automatically closes connection
```

## Error Handling

The library provides specific exception types:

```python
from scale_api_compose_pilot import (
    TrueNASConnectionError,
    TrueNASAuthenticationError, 
    TrueNASAPIError,
    DockerComposeError
)

try:
    async with TrueNASDockerManager() as manager:
        await manager.deploy_compose_stack('./compose.yml', 'app')
except TrueNASConnectionError:
    print("Failed to connect to TrueNAS")
except TrueNASAuthenticationError:
    print("Invalid API key")
except DockerComposeError:
    print("Invalid Docker Compose file")
except TrueNASAPIError as e:
    print(f"TrueNAS API error: {e}")
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/svnstfns/scale-api-compose-pilot.git
cd scale-api-compose-pilot
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black truenas_docker_manager/
```

### Type Checking

```bash
mypy truenas_docker_manager/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run the test suite
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0 (2024-12-22)

- Initial release
- Basic Docker Compose support
- CLI interface
- WebSocket API integration
- Async context manager support

## Requirements

- Python 3.8+
- TrueNAS Scale (Electric Eel or later)
- Valid TrueNAS API key

## Troubleshooting

### Connection Issues

1. Verify TrueNAS is accessible: `ping your-truenas-host`
2. Check API key validity in TrueNAS web interface
3. Ensure WebSocket endpoint is accessible: `curl -k wss://your-truenas-host/websocket`

### Docker Compose Issues

1. Ensure single-service compose files
2. Use official Docker images (no build contexts)
3. Check volume path permissions

### Common Errors

- `TrueNASConnectionError`: Check host and network connectivity
- `TrueNASAuthenticationError`: Verify API key
- `DockerComposeError`: Validate compose file format

For more help, see the [documentation](docs/) or open an [issue](https://github.com/sst/scale-compose-manager/issues).