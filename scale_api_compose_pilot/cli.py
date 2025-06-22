"""
CLI interface for TrueNAS Docker Management
"""

import os
import asyncio
import argparse
from pathlib import Path

from .manager import TrueNASDockerManager
from .exceptions import TrueNASError


async def deploy_command(args):
    """Deploy a Docker Compose stack to TrueNAS."""
    try:
        async with TrueNASDockerManager() as manager:
            result = await manager.deploy_compose_stack(args.compose_file, args.app_name)
            print(f"Successfully deployed {args.app_name}")
            print(f"Result: {result}")
            return 0
    except TrueNASError as e:
        print(f"TrueNAS Error: {e}")
        return 1
    except Exception as e:
        print(f"Error deploying stack: {e}")
        return 1


async def list_command(args):
    """List all apps on TrueNAS."""
    try:
        async with TrueNASDockerManager() as manager:
            apps = await manager.list_apps()
            print(f"Found {len(apps)} apps:")
            for app in apps:
                print(f"  - {app.get('name', 'Unknown')} (state: {app.get('state', 'Unknown')})")
            return 0
    except TrueNASError as e:
        print(f"TrueNAS Error: {e}")
        return 1
    except Exception as e:
        print(f"Error listing apps: {e}")
        return 1


async def start_command(args):
    """Start an app."""
    try:
        async with TrueNASDockerManager() as manager:
            result = await manager.start_app(args.app_name)
            print(f"Started app: {args.app_name}")
            print(f"Result: {result}")
            return 0
    except TrueNASError as e:
        print(f"TrueNAS Error: {e}")
        return 1
    except Exception as e:
        print(f"Error starting app: {e}")
        return 1


async def stop_command(args):
    """Stop an app."""
    try:
        async with TrueNASDockerManager() as manager:
            result = await manager.stop_app(args.app_name)
            print(f"Stopped app: {args.app_name}")
            print(f"Result: {result}")
            return 0
    except TrueNASError as e:
        print(f"TrueNAS Error: {e}")
        return 1
    except Exception as e:
        print(f"Error stopping app: {e}")
        return 1


async def delete_command(args):
    """Delete an app."""
    try:
        async with TrueNASDockerManager() as manager:
            # Confirm deletion
            if not args.force:
                confirm = input(f"Are you sure you want to delete app '{args.app_name}'? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Deletion cancelled")
                    return 0
            
            result = await manager.delete_app(args.app_name)
            print(f"Deleted app: {args.app_name}")
            print(f"Result: {result}")
            return 0
    except TrueNASError as e:
        print(f"TrueNAS Error: {e}")
        return 1
    except Exception as e:
        print(f"Error deleting app: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="TrueNAS Docker Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy a Docker Compose stack')
    deploy_parser.add_argument('compose_file', help='Path to docker-compose.yml file')
    deploy_parser.add_argument('app_name', help='Name for the TrueNAS app')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all apps')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start an app')
    start_parser.add_argument('app_name', help='Name of the app to start')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop an app')
    stop_parser.add_argument('app_name', help='Name of the app to stop')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an app')
    delete_parser.add_argument('app_name', help='Name of the app to delete')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run the appropriate command
    if args.command == 'deploy':
        return asyncio.run(deploy_command(args))
    elif args.command == 'list':
        return asyncio.run(list_command(args))
    elif args.command == 'start':
        return asyncio.run(start_command(args))
    elif args.command == 'stop':
        return asyncio.run(stop_command(args))
    elif args.command == 'delete':
        return asyncio.run(delete_command(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())