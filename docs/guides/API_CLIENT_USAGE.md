# TrueNAS API Client Usage Guide

## Übersicht

Dieses Dokument zeigt verschiedene Verwendungsmuster für den TrueNAS API Client zur Verwaltung von Docker-Containern auf TrueNAS Scale (Electric Eel).

## Installation der Abhängigkeiten

```bash
pip install -r requirements.txt
```

## Basis-Konfiguration

Erstelle eine `.env` Datei mit deinen TrueNAS-Verbindungsdaten:

```env
TRUENAS-HOST=https://nas.pvnkn3t.lan:4443
TRUENAS-API-KEY=dein-api-key-hier
```

## API Client Verwendungsmuster

### 1. Direkte API Client Nutzung

```python
from truenas_api_client import Client
from truenas_api_client.exc import ClientException

# Basis-Verbindung
def connect_to_truenas(host, api_key):
    """Grundlegende Verbindung zu TrueNAS."""
    try:
        # Korrektes URL-Format für WebSocket
        uri = f"wss://{host}/api/current"
        
        with Client(uri=uri, verify_ssl=False) as client:
            # Authentifizierung
            client.call("auth.login_with_api_key", api_key)
            
            # System-Info abrufen
            system_info = client.call("system.info")
            print(f"TrueNAS Version: {system_info['version']}")
            
            return client
    except ClientException as e:
        print(f"Verbindungsfehler: {e}")
        return None
```

### 2. App-Management Operationen

```python
def list_apps(client):
    """Alle Apps auflisten."""
    apps = client.call("app.query")
    for app in apps:
        print(f"App: {app['name']} - Status: {app['state']}")
    return apps

def get_app_details(client, app_name):
    """Details einer spezifischen App abrufen."""
    apps = client.call("app.query", [["name", "=", app_name]])
    return apps[0] if apps else None

def start_stop_app(client, app_name, action):
    """App starten oder stoppen."""
    try:
        if action == "start":
            result = client.call("app.start", app_name)
        elif action == "stop":
            result = client.call("app.stop", app_name)
        else:
            raise ValueError("Action must be 'start' or 'stop'")
        
        print(f"App {app_name} {action}ed successfully")
        return result
    except Exception as e:
        print(f"Fehler beim {action} der App: {e}")
        return None
```

### 3. Docker Compose Integration

```python
import yaml

def create_app_from_compose(client, compose_file, app_name):
    """Erstelle TrueNAS App aus Docker Compose Datei."""
    
    with open(compose_file, 'r') as f:
        compose_data = yaml.safe_load(f)
    
    # Vereinfachte Konvertierung (für single-service containers)
    services = compose_data.get('services', {})
    service_name, service_config = next(iter(services.items()))
    
    # TrueNAS App-Konfiguration erstellen
    app_config = {
        "name": app_name,
        "catalog": "truecharts",  # oder custom catalog
        "train": "stable",
        "version": "latest",
        "config": {
            "image": {
                "repository": service_config['image'].split(':')[0],
                "tag": service_config['image'].split(':')[1] if ':' in service_config['image'] else 'latest'
            },
            "service": {
                "main": {
                    "ports": {
                        "main": {
                            "enabled": True,
                            "port": extract_port(service_config.get('ports', [])),
                            "protocol": "http"
                        }
                    }
                }
            },
            "env": service_config.get('environment', {}),
            "persistence": convert_volumes(service_config.get('volumes', []))
        }
    }
    
    try:
        result = client.call("app.create", app_config)
        print(f"App {app_name} erstellt: {result}")
        return result
    except Exception as e:
        print(f"Fehler beim Erstellen der App: {e}")
        return None
```

### 4. Erweiterte API-Exploration

```python
def explore_api_methods(client):
    """Verfügbare API-Methoden erkunden."""
    
    # Alle Methoden abrufen
    methods = client.call("core.get_methods")
    
    # Nach App-bezogenen Methoden filtern
    app_methods = [m for m in methods if 'app' in m.lower()]
    
    print("Verfügbare App-Methoden:")
    for method in sorted(app_methods):
        try:
            # Methoden-Signatur abrufen
            args = client.call("core.get_method_args", method)
            print(f"  {method}: {args}")
        except:
            print(f"  {method}: (Details nicht verfügbar)")

def get_system_resources(client):
    """System-Ressourcen und Status abrufen."""
    
    # CPU-Info
    cpu_info = client.call("system.cpu_info")
    print(f"CPU: {cpu_info}")
    
    # Memory-Info
    memory = client.call("system.memory_info") 
    print(f"Memory: {memory}")
    
    # Docker-Status (wenn verfügbar)
    try:
        docker_info = client.call("docker.status")
        print(f"Docker Status: {docker_info}")
    except:
        print("Docker-Status nicht verfügbar")
```

### 5. Fehlerbehandlung und Retry-Logic

```python
import time
from truenas_api_client.exc import CallTimeout

def robust_api_call(client, method, *args, max_retries=3, delay=1):
    """API-Aufruf mit Retry-Logic."""
    
    for attempt in range(max_retries):
        try:
            return client.call(method, *args)
        except CallTimeout:
            if attempt < max_retries - 1:
                print(f"Timeout bei Versuch {attempt + 1}, wiederhole in {delay}s...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise
        except Exception as e:
            print(f"API-Fehler bei Versuch {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise

def monitor_app_status(client, app_name, check_interval=5):
    """App-Status kontinuierlich überwachen."""
    
    while True:
        try:
            app = get_app_details(client, app_name)
            if app:
                print(f"{app_name}: {app['state']}")
                if app['state'] == 'RUNNING':
                    break
            time.sleep(check_interval)
        except KeyboardInterrupt:
            print("Monitoring beendet")
            break
        except Exception as e:
            print(f"Fehler beim Monitoring: {e}")
            time.sleep(check_interval)
```

## Praktische Verwendungsbeispiele

### Beispiel 1: Simple App-Deployment

```python
# Verbindung herstellen und App deployen
with Client("wss://nas.pvnkn3t.lan/api/current", verify_ssl=False) as client:
    client.call("auth.login_with_api_key", "your-api-key")
    
    # Docker Compose zu App konvertieren und deployen
    create_app_from_compose(client, "docker-compose.yml", "my-new-app")
    
    # Status überwachen
    monitor_app_status(client, "my-new-app")
```

### Beispiel 2: Batch-Operations

```python
def manage_apps_batch(client, app_operations):
    """Mehrere App-Operationen in einem Batch ausführen."""
    
    results = []
    for app_name, operation in app_operations.items():
        try:
            if operation == "start":
                result = client.call("app.start", app_name)
            elif operation == "stop":
                result = client.call("app.stop", app_name)
            elif operation == "restart":
                client.call("app.stop", app_name)
                time.sleep(2)
                result = client.call("app.start", app_name)
            
            results.append((app_name, operation, "success", result))
        except Exception as e:
            results.append((app_name, operation, "error", str(e)))
    
    return results

# Verwendung
operations = {
    "app1": "start",
    "app2": "stop", 
    "app3": "restart"
}

with Client("wss://nas.pvnkn3t.lan/api/current", verify_ssl=False) as client:
    client.call("auth.login_with_api_key", "your-api-key")
    results = manage_apps_batch(client, operations)
    
    for app, op, status, result in results:
        print(f"{app} {op}: {status} - {result}")
```

## Häufige Probleme und Lösungen

### 1. SSL-Zertifikat-Probleme
```python
# Für selbst-signierte Zertifikate
client = Client("wss://nas.pvnkn3t.lan/api/current", verify_ssl=False)
```

### 2. Verbindungs-Timeouts
```python
# Längere Timeouts für langsame Operationen
client = Client("wss://nas.pvnkn3t.lan/api/current", 
                verify_ssl=False, 
                call_timeout=60)
```

### 3. API-Key-Verwaltung
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('TRUENAS-API-KEY')
if not api_key:
    raise ValueError("TRUENAS-API-KEY nicht in .env gefunden")
```

## Hilfs-Funktionen

```python
def extract_port(ports_list):
    """Extrahiert den ersten Port aus einer Docker Compose Ports-Liste."""
    if not ports_list:
        return 80
    
    port_spec = ports_list[0]
    if isinstance(port_spec, str) and ':' in port_spec:
        return int(port_spec.split(':')[1])
    return 80

def convert_volumes(volumes_list):
    """Konvertiert Docker Compose Volumes zu TrueNAS Format."""
    persistence = {}
    
    for i, volume in enumerate(volumes_list):
        if isinstance(volume, str) and ':' in volume:
            host_path, container_path = volume.split(':', 1)
            persistence[f"volume{i}"] = {
                "enabled": True,
                "type": "hostPath",
                "hostPath": host_path,
                "mountPath": container_path
            }
    
    return persistence
```

## Weiterführende Ressourcen

- [TrueNAS Scale API Dokumentation](https://nas.pvnkn3t.lan:4443/api/docs/)
- [Offizieller API Client](https://github.com/truenas/api_client)
- [TrueNAS Scale Docker Documentation](https://www.truenas.com/docs/scale/)

## Testing und Debugging

```python
# Debug-Modus aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# API-Calls loggen
def debug_api_call(client, method, *args):
    print(f"API Call: {method} with args: {args}")
    result = client.call(method, *args)
    print(f"Result: {result}")
    return result
```