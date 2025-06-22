#!/usr/bin/env python3
"""
Simple deployment example using Scale API Compose Pilot.
"""

import asyncio
from scale_api_compose_pilot import AIHelper


async def deploy_nginx_example():
    """Deploy a simple nginx web server."""
    
    # Docker Compose content as string
    compose_content = """
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
    
    helper = AIHelper()
    
    try:
        # Check system status first
        print("🔍 Checking TrueNAS connection...")
        status = await helper.get_system_status()
        
        if status["error"]:
            print(f"❌ Connection failed: {status['error']}")
            return
        
        print(f"✅ Connected! Found {status['app_count']} apps")
        
        # Validate compose file
        print("🔍 Validating Docker Compose...")
        validation = helper.validate_compose(compose_content)
        
        if not validation["valid"]:
            print(f"❌ Validation failed: {validation['errors']}")
            return
        
        print("✅ Compose file is valid")
        
        # Deploy the application
        print("🚀 Deploying nginx web server...")
        result = await helper.simple_deploy(compose_content, "nginx-web")
        
        if result["success"]:
            print(f"🎉 {result['message']}")
            print(f"   Action: {result['action']}")
        else:
            print(f"❌ Deployment failed: {result['error']}")
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(deploy_nginx_example())