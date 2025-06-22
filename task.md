# TrueNAS Scale Docker Management via WebSocket API

## Projektziel
Entwickle ein Tool zur Fernsteuerung von Docker-Containern auf TrueNAS Scale (Electric Eel) über die WebSocket-API.

## Systemumgebung
- **TrueNAS Scale Version**: Electric Eel
- **API-Präferenz**: WebSocket (REST-API ist deprecated)
- **Ziel-Funktionen**: Docker Compose Stacks erstellen, starten, stoppen, ändern

## Technische Anforderungen
- WebSocket-Verbindung zur TrueNAS Scale Middleware
- Authentifizierung über API-Key oder Session-Token
- Unterstützung für Docker Compose File Upload und Deployment
- Container-Status-Monitoring und Log-Abruf
- Robuste Fehlerbehandlung und Reconnection-Logic

## Erwartete Deliverables
1. Python-Script für WebSocket-Kommunikation mit TrueNAS
2. CLI-Interface für Docker-Stack-Management
3. Dokumentation der WebSocket-API-Endpunkte
4. Beispiel-Integration mit vorhandenen docker-compose.yml Files

## Forschungsaufgaben
- wenn nötig, Reverse Engineering der TrueNAS WebSocket-API durch Code-Analyse
- Identifikation der korrekten Nachrichtenformate und Parameter
- Test mit lokalen Docker Compose Projekt: /Users/sst/PycharmProjects/deploy2nas/samples/inventor
- Implementierung von Authentifizierung und Session-Management

## Besondere Herausforderungen
- API-KEY und HOST siehe /Users/sst/PycharmProjects/deploy2nas/.env
- WebSocket-API ist dokumentiert hier https://nas.pvnkn3t.lan:4443/api/docs/ vermutlich app.create und weitere
- vom hersteller git es einen api client: https://github.com/truenas/api_client'
- Die API MUSS über HTTPS angesprochen werden. tut man es nciht, wird sofort er API key gesperrt!
- Middleware-Protokoll muss durch Analyse verstanden werden
- Integration mit TrueNAS-spezifischen Docker-Features
- root-zugang per ssh für claude ist möglich, wenn es hilft das nas-system (speziell die docker-engine) zu analysieren

## Implementierungsstatus

### ✅ Abgeschlossene Deliverables

1. **Python-Script für WebSocket-Kommunikation** (`truenas_docker_manager.py`)
   - Vollständige WebSocket-Verbindung zur TrueNAS Scale Middleware
   - Robuste Authentifizierung über API-Key
   - Async/await-basierte Architektur für bessere Performance
   - Automatische Reconnection-Logic und Fehlerbehandlung

2. **CLI-Interface für Docker-Stack-Management** (`cli.py`)
   - Kommandozeilen-Tool mit folgenden Befehlen:
     - `deploy` - Docker Compose Stack deployment
     - `list` - Alle Apps auflisten
     - `start/stop/delete` - App-Lifecycle-Management
   - Vollständige Argumentvalidierung und Hilfe-System

3. **Test- und Entwicklungstools**
   - `testlogin.py` - Umfassende Verbindungstest mit Fallback-Optionen
   - `explore_api.py` - API-Methoden-Discovery und -Analyse
   - `debug_websocket.py` - WebSocket-Debugging-Utilities

### 🔧 Technische Features

- **Docker Compose zu TrueNAS App Konvertierung**: Automatische Umwandlung von docker-compose.yml zu TrueNAS-App-Konfiguration
- **SSL/TLS-Support**: Sowohl verifizierte als auch selbst-signierte Zertifikate unterstützt
- **Umfassende Fehlerbehandlung**: Graceful handling von Netzwerk-, Auth- und API-Fehlern
- **Logging**: Strukturiertes Logging für Debugging und Monitoring

### 📖 API Client Nutzung

#### Basis-Verbindung und Authentifizierung
```python
from truenas_api_client import Client

# WebSocket-Verbindung (empfohlen für Electric Eel)
with Client("wss://nas.pvnkn3t.lan/api/current", verify_ssl=False) as c:
    # API-Key Authentifizierung
    c.call("auth.login_with_api_key", "your-api-key-here")
    
    # API-Aufrufe tätigen
    system_info = c.call("system.info")
    apps = c.call("app.query")
```

#### Docker-Management via CLI
```bash
# Docker Compose Stack deployen
python cli.py deploy ./samples/inventor/docker-compose.yml my-app

# Apps verwalten
python cli.py list
python cli.py start my-app
python cli.py stop my-app
python cli.py delete my-app --force
```

#### Programmatische Nutzung
```python
from truenas_docker_manager import TrueNASDockerManager

manager = TrueNASDockerManager()
await manager.connect()
await manager.authenticate()

# Docker Compose deployen
await manager.deploy_compose_stack('./docker-compose.yml', 'my-app')

# App-Status überwachen
apps = await manager.list_apps()
for app in apps:
    print(f"{app['name']}: {app['state']}")
```

## Verbleibende Aufgaben

- [ ] Live-Test mit dem inventor-Beispielprojekt
- [ ] Erweiterte Docker Compose Feature-Unterstützung (networks, secrets, etc.)
- [ ] Container-Log-Streaming implementieren
- [ ] App-Update-Workflow verbessern
- [ ] Monitoring und Health-Check-Integration

## login mit api-key (Legacy-Beispiel)
```python
import websocket
from truenas_api_client import Client
from truenas_api_client.exc import ClientException

api_key='4-MjAQKzqmwabnyGjeljOHh7LKQ12WuuGDiHWszrfGIhSyVnqLCrZdsraEoDoTgKRa'

try:
    with Client("wss://nas.pvnkn3t.lan/websocket", verify_ssl=False) as c:
        # Authenticate using API key
        resp = c.call("auth.login_with_api_key", api_key)
        print("Authentication successful:", resp)
except ClientException as e:
    print(f"TrueNAS API Client error: {e}")
except Exception as e:
    print(f"Connection error: {e}")

```
