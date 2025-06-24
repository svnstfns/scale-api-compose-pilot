"""
CLI interface for TrueNAS Docker Management
"""

import os
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

from .manager import TrueNASDockerManager
from .exceptions import TrueNASError
from .discovery import scan_all, quick_scan
from .setup_wizard import run_setup_wizard
from .dependency_installer import ensure_dependencies
from .path_setup import check_and_setup_path
from . import __version__


async def deploy_command(args: argparse.Namespace) -> int:
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


async def list_command(args: argparse.Namespace) -> int:
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


async def start_command(args: argparse.Namespace) -> int:
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


async def stop_command(args: argparse.Namespace) -> int:
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


async def delete_command(args: argparse.Namespace) -> int:
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


def discover_command(args: argparse.Namespace) -> int:
    """Discover TrueNAS systems on the network."""
    try:
        print("🔍 Discovering TrueNAS Scale systems...")
        systems = scan_all(timeout=args.timeout)
        
        if systems:
            print(f"\n✅ Found {len(systems)} TrueNAS system(s):")
            for i, system in enumerate(systems, 1):
                print(f"  {i}. {system}")
                print(f"     Web Interface: {system.web_url}")
                print(f"     Services: {', '.join(system.services)}")
        else:
            print("❌ No TrueNAS systems found on the network.")
            print("\n🔧 Troubleshooting:")
            print("  - Ensure TrueNAS is running and on the same network")
            print("  - Check that mDNS is enabled on TrueNAS")
            print("  - Try increasing the timeout with --timeout")
            return 1
        
        return 0
    except Exception as e:
        print(f"Error during discovery: {e}")
        return 1


def init_command(args: argparse.Namespace) -> int:
    """Run the setup wizard."""
    try:
        print("🚀 Starting Scale API Compose Pilot Setup Wizard...")
        success = run_setup_wizard()
        return 0 if success else 1
    except Exception as e:
        print(f"Setup wizard failed: {e}")
        return 1


async def validate_command(args: argparse.Namespace) -> int:
    """Validate connection to TrueNAS."""
    try:
        print("🔧 Validating TrueNAS connection...")
        
        async with TrueNASDockerManager() as manager:
            print("✅ Connection established")
            print("✅ Authentication successful")
            
            # Test API access
            apps = await manager.list_apps()
            print(f"✅ API access working - found {len(apps)} apps")
            
            print("\n🎉 All checks passed! Your setup is working correctly.")
            return 0
            
    except TrueNASError as e:
        print(f"❌ TrueNAS Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("  - Run 'scale-compose init' to reconfigure")
        print("  - Check your .env file settings")
        print("  - Verify TrueNAS is accessible")
        return 1
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


def install_deps_command(args: argparse.Namespace) -> int:
    """Install missing dependencies."""
    try:
        print("📦 Checking and installing dependencies...")
        success = ensure_dependencies()
        
        if success:
            print("\n✅ All dependencies are ready!")
            return 0
        else:
            print("\n❌ Some dependencies failed to install")
            print("Please check the output above for manual installation instructions")
            return 1
            
    except Exception as e:
        print(f"❌ Dependency installation failed: {e}")
        return 1


def check_path_command(args: argparse.Namespace) -> int:
    """Check PATH setup for the CLI."""
    try:
        print("📏 Checking CLI PATH setup...")
        guidance = check_and_setup_path()
        print(guidance)
        return 0
    except Exception as e:
        print(f"❌ PATH check failed: {e}")
        return 1


def version_command(args: argparse.Namespace) -> int:
    """Show version information."""
    print(f"Scale API Compose Pilot v{__version__}")
    return 0


def diagnostics_command(args: argparse.Namespace) -> int:
    """Run diagnostic checks."""
    print("🔍 Running diagnostics...")
    print(f"✅ Version: {__version__}")
    print(f"✅ Python: {os.sys.version}")
    
    # Check environment variables
    host = os.getenv('TRUENAS_HOST')
    api_key = os.getenv('TRUENAS_API_KEY')
    
    print(f"🔧 Environment:")
    print(f"  - TRUENAS_HOST: {'✅ Set' if host else '❌ Not set'}")
    print(f"  - TRUENAS_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    
    # Check dependencies
    print("📦 Dependencies:")
    try:
        import truenas_api_client
        print("  - TrueNAS API Client: ✅ Available")
    except ImportError:
        print("  - TrueNAS API Client: ❌ Not installed")
    
    try:
        import zeroconf
        print("  - Zeroconf: ✅ Available")
    except ImportError:
        print("  - Zeroconf: ❌ Not installed")
    
    try:
        import yaml
        print("  - PyYAML: ✅ Available")
    except ImportError:
        print("  - PyYAML: ❌ Not installed")
    
    print("\n💡 For connection issues, run: scale-compose validate")
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="TrueNAS Docker Management CLI")
    parser.add_argument('--version', action='store_true', help='Show version information')
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
    
    # Discovery command
    discover_parser = subparsers.add_parser('discover', help='Discover TrueNAS systems on network')
    discover_parser.add_argument('--timeout', type=float, default=5.0, help='Discovery timeout in seconds')
    
    # Init command  
    init_parser = subparsers.add_parser('init', help='Run setup wizard')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate TrueNAS connection')
    
    # Install deps command
    deps_parser = subparsers.add_parser('install-deps', help='Install missing dependencies')
    
    # Check PATH command
    path_parser = subparsers.add_parser('check-path', help='Check CLI PATH setup')
    
    # Diagnostics command
    diag_parser = subparsers.add_parser('diagnostics', help='Run diagnostic checks')
    
    args = parser.parse_args()
    
    # Handle version flag
    if args.version:
        return version_command(args)
    
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
    elif args.command == 'discover':
        return discover_command(args)
    elif args.command == 'init':
        return init_command(args)
    elif args.command == 'validate':
        return asyncio.run(validate_command(args))
    elif args.command == 'install-deps':
        return install_deps_command(args)
    elif args.command == 'check-path':
        return check_path_command(args)
    elif args.command == 'diagnostics':
        return diagnostics_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())