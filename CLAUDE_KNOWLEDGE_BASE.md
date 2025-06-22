# Claude Knowledge Base - Scale API Compose Pilot

This file contains key learnings and insights from the development of Scale API Compose Pilot to preserve knowledge for future AI interactions.

## 🎯 Project Overview

**Scale API Compose Pilot** is an AI-friendly Docker Compose automation tool for TrueNAS Scale that "pilots" workloads safely to their destination through the WebSocket API.

- **Repository**: https://github.com/svnstfns/scale-api-compose-pilot
- **CLI Command**: `scale-compose`
- **Python Package**: `scale_api_compose_pilot`

## 🔧 Technical Architecture

### Core Components
1. **TrueNASDockerManager**: Main async management class
2. **AIHelper**: AI-friendly interface with structured responses
3. **CLI**: Command-line tool (`scale-compose`)
4. **Exceptions**: Custom error hierarchy for different failure types

### Key Design Patterns
- **Async Context Manager**: `async with TrueNASDockerManager()` for automatic cleanup
- **Structured Responses**: All methods return dicts with `success`, `error`, `message` keys
- **Validation First**: Always validate before deployment
- **Single-Service Focus**: TrueNAS Scale limitation, one service per compose file

## 🏗️ TrueNAS Scale Research Findings

### Storage Architecture (CRITICAL KNOWLEDGE)
```
/mnt/.ix-apps/
├── app_configs/           # App metadata and versions
├── app_mounts/           # IX volumes - TrueNAS managed persistent storage
├── docker/
│   ├── volumes/         # Docker named volumes (less preferred)
│   └── containers/      # Container runtime data
```

### Storage Patterns (USE THESE)
- **IX Volumes**: `/mnt/.ix-apps/app_mounts/{app}/{volume}/` - TrueNAS managed, preferred
- **Pool Bind Mounts**: `/mnt/pool/*` - User data on ZFS pools, safe
- **System Mounts**: Avoid `/etc`, `/usr`, `/var` - dangerous

### Network Architecture
- **Bridge**: `172.16.x.0/24` subnets, port forwarding to `nas-ip:31xxx`
- **Macvlan**: Direct LAN IPs `10.121.124.x`, for services needing dedicated IP
- **Host**: Direct host network, for special cases

### Conversion Rules (IMPLEMENT THESE)
```python
# Named volume → IX Volume (TrueNAS manages)
"app_data:/data" → {"type": "ix_volume", "mount_path": "/data"}

# Pool mount → Bind mount (user manages)  
"/mnt/pool/media:/media" → {"type": "host_path", "host_path": "/mnt/pool/media"}

# System mount → Warning
"/etc/config:/config" → Warning + allow with caution
```

## 📡 API Connection Details

### Working Configuration
- **URL Format**: `wss://nas.pvnkn3t.lan/websocket` (NOT `/api/current`)
- **SSL**: `verify_ssl=False` for self-signed certs
- **API Client**: `truenas_api_client` from GitHub (not on PyPI)

### Authentication Flow
```python
with Client("wss://host/websocket", verify_ssl=False) as client:
    client.call("auth.login_with_api_key", api_key)
    # Now authenticated for API calls
```

### Key API Methods Discovered
- `app.query` - List all apps
- `app.create` - Create new app
- `app.start/stop/delete` - Lifecycle management  
- `system.info` - System information
- `core.get_methods` - Discover available methods

## 🤖 AI-Friendly Design Principles

### Response Patterns
All methods return predictable structures:
```python
# Success response
{"success": True, "message": "App deployed", "action": "created"}

# Error response  
{"success": False, "error": "Connection failed", "step": "authentication"}

# Status response
{"connected": True, "app_count": 3, "running_apps": 2, "error": None}
```

### Validation Before Action
```python
# Always validate first
validation = helper.validate_compose(yaml_content)
if validation["valid"]:
    result = await helper.simple_deploy(yaml_content, app_name)
```

### Error Handling Strategy
- **Connection Errors**: Check host/network
- **Auth Errors**: Verify API key
- **Compose Errors**: Single-service limitation, validation issues
- **TrueNAS Errors**: App already exists, insufficient permissions

## 🎯 Successful Patterns

### CLI Usage That Works
```bash
# These commands are verified working
scale-compose list
scale-compose deploy nginx.yml my-nginx
scale-compose start my-nginx
scale-compose stop my-nginx
```

### Python Usage That Works
```python
# Verified pattern
from scale_api_compose_pilot import AIHelper

async with AIHelper() as helper:
    status = await helper.get_system_status()
    if status["connected"]:
        result = await helper.simple_deploy(compose_yaml, "app-name")
```

## 🚨 Known Limitations & Workarounds

### Single-Service Only
- **Limitation**: TrueNAS Scale requires one service per app
- **Workaround**: Split multi-service compose files
- **Detection**: Check `len(services) > 1` and error

### Build Contexts Not Supported
- **Limitation**: TrueNAS Scale uses pre-built images only
- **Workaround**: Use published Docker Hub images
- **Detection**: Check for `build:` key and warn

### Network Complexity
- **Limitation**: Complex networks not fully supported
- **Workaround**: Detect macvlan vs bridge, provide guidance
- **Detection**: Look for `networks:` with external references

## 🔮 Future Enhancement Areas

### High Priority
1. **Multi-Service Support**: Deploy related services as separate apps
2. **Resource Limits**: CPU/memory constraints from compose
3. **Health Checks**: Container health monitoring
4. **Log Streaming**: Real-time container logs

### Medium Priority  
1. **Custom Networks**: Better network configuration
2. **Secrets Management**: Handle sensitive data
3. **Update Workflows**: Rolling updates and rollbacks
4. **Backup Integration**: App data backup/restore

## 📚 Essential Files to Read First

When continuing this project:
1. `TRUENAS_SCALE_PATTERNS.md` - Storage/networking research
2. `scale_api_compose_pilot/manager.py` - Core conversion logic
3. `scale_api_compose_pilot/ai_helper.py` - AI-friendly interface
4. `AI_AGENT_GUIDE.md` - Usage patterns for AI agents
5. `examples/` - Working compose examples

## 🐛 Common Debugging Steps

### Connection Issues
1. Check `ssh -T root@nas.pvnkn3t.lan` connectivity
2. Verify WebSocket endpoint: `wss://host/websocket`
3. Test API key: `c.call("auth.login_with_api_key", key)`

### Deployment Issues  
1. Validate compose first: `helper.validate_compose()`
2. Check single-service requirement
3. Verify storage paths (`/mnt/pool/*` safe)
4. Check network configuration

### API Issues
1. Use `explore_api.py` to discover methods
2. Check `app.query` for existing apps
3. Monitor TrueNAS logs for detailed errors

## 🎖️ Achievement Unlocked

This project successfully:
- ✅ Created working TrueNAS Scale Docker automation
- ✅ Researched and documented TrueNAS internals  
- ✅ Built AI-friendly interfaces with structured responses
- ✅ Established proper Python package with CLI
- ✅ Deployed live to GitHub with clean examples
- ✅ Tested against real TrueNAS Scale system

The "pilot" metaphor perfectly captures the tool's essence: safely guiding Docker workloads to their destination on TrueNAS Scale! 🛩️