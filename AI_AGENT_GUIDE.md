# AI Agent Usage Guide for Scale API Compose Pilot

This guide is specifically designed for AI assistants like Claude to effectively use the TrueNAS Docker Manager library.

## Quick Start for AI Agents

### 1. Import the AI Helper

```python
from scale_api_compose_pilot import AIHelper, create_ai_summary

# Get library overview
summary = create_ai_summary()
print(summary)  # Complete capability overview

# Initialize helper
helper = AIHelper()  # Uses environment variables
# OR
helper = AIHelper(host="truenas.local", api_key="your-key")
```

### 2. Check System Status (Always Start Here)

```python
# Get comprehensive system status
status = await helper.get_system_status()

# Status contains:
# - connected: bool
# - authenticated: bool  
# - apps: list of app details
# - app_count: int
# - running_apps: int
# - error: str or None

if status["error"]:
    print(f"Connection failed: {status['error']}")
else:
    print(f"Connected! Found {status['app_count']} apps, {status['running_apps']} running")
```

### 3. Deploy Applications from Strings

```python
# Deploy directly from YAML string (no file needed)
compose_yaml = """
services:
  nginx:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - ENV=production
    volumes:
      - /host/html:/usr/share/nginx/html
    restart: unless-stopped
"""

result = await helper.simple_deploy(compose_yaml, "my-nginx")

# Result contains:
# - success: bool
# - app_name: str
# - action: "created" or "updated"
# - message: str
# - error: str or None

if result["success"]:
    print(f"✅ {result['message']}")
else:
    print(f"❌ {result['error']}")
```

### 4. Batch Operations

```python
# Perform multiple operations efficiently
operations = [
    {"app": "nginx", "action": "start"},
    {"app": "postgres", "action": "stop"},
    {"app": "old-app", "action": "delete"},
    {"app": "nginx", "action": "status"}
]

results = await helper.app_operations(operations)

for result in results:
    app = result["app"]
    action = result["action"]
    if result["success"]:
        print(f"✅ {app}: {result['message']}")
    else:
        print(f"❌ {app} {action}: {result['error']}")
```

### 5. Validate Before Deploying

```python
# Validate Docker Compose without deploying
validation = helper.validate_compose(compose_yaml)

print(f"Valid: {validation['valid']}")
print(f"Services: {validation['services']}")
print(f"Supported features: {validation['supported_features']}")
print(f"Warnings: {validation['warnings']}")
print(f"Errors: {validation['errors']}")

# Only deploy if validation passes
if validation["valid"]:
    result = await helper.simple_deploy(compose_yaml, "app-name")
```

### 6. Generate Templates

```python
# Generate valid Docker Compose templates
template = helper.generate_compose_template(
    image="postgres:13",
    ports=["5432:5432"],
    environment={
        "POSTGRES_DB": "mydb",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password"
    },
    volumes=["/host/data:/var/lib/postgresql/data"]
)

print(template)  # Ready-to-use YAML
```

## AI Agent Best Practices

### 1. Always Check Status First

```python
async def safe_operation():
    helper = AIHelper()
    
    # Always check connection first
    status = await helper.get_system_status()
    if status["error"]:
        return {"error": f"Cannot connect: {status['error']}"}
    
    # Proceed with operations...
    return {"success": True}
```

### 2. Validate Before Deploying

```python
async def safe_deploy(compose_content, app_name):
    helper = AIHelper()
    
    # Validate first
    validation = helper.validate_compose(compose_content)
    if not validation["valid"]:
        return {
            "success": False,
            "error": f"Invalid compose: {validation['errors']}"
        }
    
    # Deploy if valid
    return await helper.simple_deploy(compose_content, app_name)
```

### 3. Use Structured Error Handling

```python
async def robust_deployment(compose_yaml, app_name):
    """Example of robust deployment with proper error handling."""
    helper = AIHelper()
    
    try:
        # Step 1: Check system
        status = await helper.get_system_status()
        if status["error"]:
            return {"step": "connection", "error": status["error"]}
        
        # Step 2: Validate compose
        validation = helper.validate_compose(compose_yaml)
        if not validation["valid"]:
            return {"step": "validation", "errors": validation["errors"]}
        
        # Step 3: Deploy
        result = await helper.simple_deploy(compose_yaml, app_name)
        if not result["success"]:
            return {"step": "deployment", "error": result["error"]}
        
        # Step 4: Verify deployment
        verify_ops = [{"app": app_name, "action": "status"}]
        verify_results = await helper.app_operations(verify_ops)
        
        return {
            "success": True,
            "action": result["action"],
            "message": result["message"],
            "final_status": verify_results[0]["message"]
        }
        
    except Exception as e:
        return {"step": "unexpected", "error": str(e)}
```

## Common AI Use Cases

### 1. Deploy Application from User Description

```python
async def deploy_from_description(description: str):
    """
    Example: "Deploy nginx web server on port 8080 with custom HTML"
    """
    # Generate appropriate compose based on description
    if "nginx" in description.lower():
        compose = helper.generate_compose_template(
            image="nginx:latest",
            ports=["8080:80"] if "8080" in description else ["80:80"],
            volumes=["/host/html:/usr/share/nginx/html"] if "custom" in description else None
        )
        
        return await helper.simple_deploy(compose, "nginx-web")
```

### 2. Health Check and Maintenance

```python
async def system_health_check():
    """Comprehensive system health check."""
    helper = AIHelper()
    
    status = await helper.get_system_status()
    
    health_report = {
        "system_healthy": status["connected"] and status["authenticated"],
        "total_apps": status["app_count"],
        "running_apps": status["running_apps"],
        "stopped_apps": status["app_count"] - status["running_apps"],
        "apps_needing_attention": []
    }
    
    # Check each app
    for app in status["apps"]:
        if app["state"] != "RUNNING":
            health_report["apps_needing_attention"].append({
                "name": app["name"],
                "state": app["state"],
                "action_needed": "restart" if app["state"] == "STOPPED" else "investigate"
            })
    
    return health_report
```

### 3. Bulk Application Management

```python
async def manage_application_suite(apps_config):
    """
    Deploy/manage multiple related applications.
    
    apps_config = [
        {"name": "database", "compose": "...", "action": "deploy"},
        {"name": "web", "compose": "...", "action": "deploy"},
        {"name": "old-app", "action": "delete"}
    ]
    """
    helper = AIHelper()
    results = []
    
    for app_config in apps_config:
        if app_config["action"] == "deploy":
            result = await helper.simple_deploy(
                app_config["compose"], 
                app_config["name"]
            )
        else:
            # Other actions (start, stop, delete)
            ops_result = await helper.app_operations([{
                "app": app_config["name"],
                "action": app_config["action"]
            }])
            result = ops_result[0]
        
        results.append({
            "app": app_config["name"],
            "action": app_config["action"],
            "success": result.get("success", False),
            "message": result.get("message", result.get("error"))
        })
    
    return results
```

## Error Handling for AI Agents

### Common Error Types and Responses

```python
async def handle_common_errors(operation_func):
    """Wrapper for common error handling patterns."""
    try:
        return await operation_func()
    except Exception as e:
        error_msg = str(e).lower()
        
        if "connection" in error_msg:
            return {
                "error_type": "connection",
                "suggestion": "Check TrueNAS host and network connectivity",
                "retry_possible": True
            }
        elif "authentication" in error_msg:
            return {
                "error_type": "authentication", 
                "suggestion": "Verify API key is valid and has proper permissions",
                "retry_possible": False
            }
        elif "single-service" in error_msg:
            return {
                "error_type": "compose_format",
                "suggestion": "Split multi-service compose into separate deployments",
                "retry_possible": True
            }
        else:
            return {
                "error_type": "unknown",
                "suggestion": "Check logs and verify system status",
                "retry_possible": False,
                "original_error": str(e)
            }
```

## Quick Reference for AI Agents

### Essential Methods Summary

| Method | Purpose | Returns | Use When |
|--------|---------|---------|----------|
| `get_system_status()` | Check connection and list apps | Status dict | Starting any operation |
| `simple_deploy(yaml, name)` | Deploy from string | Result dict | Deploying applications |
| `app_operations(ops_list)` | Batch app management | Results list | Multiple operations |
| `validate_compose(yaml)` | Check without deploying | Validation dict | Before deployment |
| `generate_compose_template()` | Create valid YAML | YAML string | Template generation |

### Return Value Patterns

All AI Helper methods return structured dictionaries with consistent patterns:

- **Success Operations**: `{"success": True, "message": "...", ...}`
- **Failed Operations**: `{"success": False, "error": "...", ...}`
- **Status Checks**: `{"connected": bool, "error": str|None, ...}`
- **Validation**: `{"valid": bool, "errors": [...], "warnings": [...]}`

This makes it easy for AI agents to parse results and take appropriate actions.

## Testing AI Integration

```python
# Test the AI helper functionality
async def test_ai_integration():
    from scale_api_compose_pilot import AIHelper, create_ai_summary
    
    print("🤖 AI Agent Integration Test")
    print("=" * 40)
    
    # Get library summary
    summary = create_ai_summary()
    print(f"Library: {summary['library_name']}")
    print(f"Purpose: {summary['purpose']}")
    
    # Test helper
    helper = AIHelper()
    
    # Check status
    status = await helper.get_system_status()
    print(f"Connected: {status['connected']}")
    print(f"Apps: {status['app_count']}")
    
    # Test validation
    test_compose = helper.generate_compose_template("nginx:latest", ["80:80"])
    validation = helper.validate_compose(test_compose)
    print(f"Template valid: {validation['valid']}")
    
    print("✅ AI integration working!")

# Run test
await test_ai_integration()
```

The AI Helper makes it much easier for AI agents to work with TrueNAS by providing:
- 🔍 **Clear validation** before operations
- 📊 **Structured responses** for easy parsing  
- 🛡️ **Robust error handling** with actionable messages
- 📝 **Template generation** for common scenarios
- 🔄 **Batch operations** for efficiency
- 📖 **Comprehensive documentation** for AI understanding