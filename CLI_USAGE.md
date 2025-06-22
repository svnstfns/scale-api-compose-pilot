# TrueNAS Docker Management CLI - Benutzerhandbuch

## Übersicht

Das TrueNAS Docker Management CLI (`cli.py`) bietet eine einfache Kommandozeilen-Schnittstelle zur Verwaltung von Docker-Anwendungen auf TrueNAS Scale (Electric Eel) über die WebSocket-API.

## Installation und Setup

### Voraussetzungen

```bash
# Python-Abhängigkeiten installieren
pip install -r requirements.txt
```

### Konfiguration

Erstelle eine `.env` Datei im Projektverzeichnis:

```env
TRUENAS-HOST=nas.pvnkn3t.lan
TRUENAS-API-KEY=dein-api-key-hier
```

**Wichtig**: Der API-Key muss ohne Leerzeichen formatiert sein.

## Verfügbare Befehle

### 1. Apps auflisten

```bash
python cli.py list
```

**Ausgabe:**
```
Found 3 apps:
  - portainer2 (state: RUNNING)
  - alloy (state: CRASHED)
  - plex (state: RUNNING)
```

### 2. Docker Compose Stack deployen

```bash
python cli.py deploy <docker-compose-file> <app-name>
```

**Beispiel:**
```bash
python cli.py deploy ./samples/inventor/docker-compose.yml videoinventory
```

**Parameter:**
- `<docker-compose-file>`: Pfad zur docker-compose.yml Datei
- `<app-name>`: Name für die TrueNAS-App (muss eindeutig sein)

### 3. App starten

```bash
python cli.py start <app-name>
```

**Beispiel:**
```bash
python cli.py start videoinventory
```

### 4. App stoppen

```bash
python cli.py stop <app-name>
```

**Beispiel:**
```bash
python cli.py stop videoinventory
```

### 5. App löschen

```bash
python cli.py delete <app-name> [--force]
```

**Beispiele:**
```bash
# Mit Bestätigungsabfrage
python cli.py delete videoinventory

# Ohne Bestätigungsabfrage
python cli.py delete videoinventory --force
```

**Parameter:**
- `--force`: Überspringt die Bestätigungsabfrage

## Docker Compose Konvertierung

### Unterstützte Features

Das CLI konvertiert automatisch Docker Compose Dateien zu TrueNAS-App-Konfigurationen:

- ✅ **Container Images**: Standard Docker Images
- ✅ **Port Forwarding**: Host:Container Port-Mapping
- ✅ **Environment Variables**: Umgebungsvariablen
- ✅ **Volume Mounts**: Host-Pfad zu Container-Pfad Mapping
- ✅ **Restart Policies**: Automatischer Container-Neustart

### Einschränkungen

Aktuell **nicht unterstützt**:
- ❌ Multi-Service Compose Files (nur Single-Service)
- ❌ Custom Networks (außer Standard-Netzwerk)
- ❌ Build Contexts (nur fertige Images)
- ❌ Docker Secrets und Configs
- ❌ Resource Limits (CPU/Memory)
- ❌ Health Checks

### Beispiel einer unterstützten docker-compose.yml

```yaml
services:
  webapp:
    image: nginx:latest
    ports:
      - "8080:80"
    environment:
      - ENV=production
      - DEBUG=false
    volumes:
      - /host/data:/var/www/html
      - /host/logs:/var/log/nginx
    restart: unless-stopped
```

## Fehlerbehandlung

### Häufige Fehler

#### 1. Verbindungsfehler
```
Failed to connect to TrueNAS
```

**Lösung:**
- Überprüfe die `.env` Konfiguration
- Stelle sicher, dass TrueNAS erreichbar ist
- Verifiziere den API-Key

#### 2. Authentifizierungsfehler
```
Failed to authenticate with TrueNAS
```

**Lösung:**
- Überprüfe den API-Key auf Gültigkeit
- Stelle sicher, dass keine Leerzeichen im API-Key sind
- Erneuere den API-Key in TrueNAS falls nötig

#### 3. App bereits vorhanden
```
App 'myapp' already exists
```

**Lösung:**
- Verwende einen anderen App-Namen
- Lösche die bestehende App zuerst
- Oder verwende das Update-Feature (automatisch im deploy-Befehl)

#### 4. Docker Compose Konvertierungsfehler
```
Currently only single-service compose files are supported
```

**Lösung:**
- Teile Multi-Service Compose Files in separate Dateien auf
- Deploye jeden Service einzeln

## Erweiterte Nutzung

### Debugging

Aktiviere Logging für detaillierte Ausgaben:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Programmatische Nutzung

Das CLI kann auch als Python-Modul verwendet werden:

```python
from truenas_docker_manager import TrueNASDockerManager
import asyncio

async def main():
    manager = TrueNASDockerManager()
    
    await manager.connect()
    await manager.authenticate()
    
    # Apps auflisten
    apps = await manager.list_apps()
    print(f"Found {len(apps)} apps")
    
    # Docker Compose deployen
    await manager.deploy_compose_stack(
        './docker-compose.yml', 
        'my-app'
    )
    
    await manager.close()

asyncio.run(main())
```

### Batch-Operationen

Für Batch-Operationen mit mehreren Apps:

```bash
# Alle Apps auflisten und Status prüfen
python cli.py list

# Mehrere Apps nacheinander starten
python cli.py start app1
python cli.py start app2
python cli.py start app3

# Oder mit einem Shell-Script
#!/bin/bash
for app in app1 app2 app3; do
    python cli.py start "$app"
done
```

## Integration in CI/CD

### GitHub Actions Beispiel

```yaml
name: Deploy to TrueNAS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Deploy to TrueNAS
        env:
          TRUENAS_HOST: ${{ secrets.TRUENAS_HOST }}
          TRUENAS_API_KEY: ${{ secrets.TRUENAS_API_KEY }}
        run: |
          python cli.py deploy docker-compose.yml my-app
```

### Makefile Integration

```makefile
.PHONY: deploy start stop clean

deploy:
	python cli.py deploy docker-compose.yml $(APP_NAME)

start:
	python cli.py start $(APP_NAME)

stop:
	python cli.py stop $(APP_NAME)

clean:
	python cli.py delete $(APP_NAME) --force

status:
	python cli.py list
```

## Monitoring und Wartung

### App-Status überwachen

```bash
# Status aller Apps anzeigen
python cli.py list

# Spezifische App-Details (über programmatische API)
python -c "
import asyncio
from truenas_docker_manager import TrueNASDockerManager

async def get_app_details():
    manager = TrueNASDockerManager()
    await manager.connect()
    await manager.authenticate()
    
    details = await manager.get_app_details('myapp')
    print(f'App State: {details[\"state\"]}')
    print(f'Image: {details.get(\"image\", \"Unknown\")}')
    
    await manager.close()

asyncio.run(get_app_details())
"
```

### Log-Zugriff

Aktuell ist der direkte Log-Zugriff über das CLI nicht implementiert. Nutze die TrueNAS Web-UI oder SSH-Zugang für Log-Einsicht.

## Tipps und Best Practices

### 1. App-Naming
- Verwende aussagekräftige, kurze Namen
- Vermeide Sonderzeichen und Leerzeichen
- Nutze Versionierung bei Bedarf (z.B., `myapp-v1`)

### 2. Docker Compose Optimierung
- Halte Compose Files einfach (Single-Service)
- Verwende offizielle Docker Images wo möglich
- Dokumentiere Environment Variables

### 3. Deployment-Workflow
```bash
# 1. Teste lokal
docker-compose up -d

# 2. Deploye zu TrueNAS
python cli.py deploy docker-compose.yml myapp

# 3. Überprüfe Status
python cli.py list

# 4. Bei Problemen: Logs prüfen (über TrueNAS UI)
```

### 4. Backup und Recovery
- Sichere Docker Compose Files in Versionskontrolle
- Dokumentiere App-spezifische Konfigurationen
- Teste Recovery-Prozeduren regelmäßig

## Fehlerbehebung

### Verbindungsprobleme diagnostizieren

```bash
# 1. Netzwerk-Konnektivität testen
ping nas.pvnkn3t.lan

# 2. TrueNAS WebSocket-Endpunkt testen
curl -k wss://nas.pvnkn3t.lan/websocket

# 3. API-Key validieren
python -c "
from truenas_api_client import Client
with Client('wss://nas.pvnkn3t.lan/websocket', verify_ssl=False) as c:
    result = c.call('auth.login_with_api_key', 'your-api-key')
    print(f'Auth result: {result}')
"
```

### Performance-Optimierung

- Verwende `verify_ssl=False` nur für Entwicklung/Testing
- Implementiere Connection Pooling für häufige API-Aufrufe
- Nutze Batch-Operationen wo möglich

## Support und Weiterentwicklung

### Bekannte Limitationen
- Aktuell nur Single-Service Docker Compose Support
- Keine direkte Log-Stream-Funktionalität
- Begrenzte Resource-Management-Features

### Geplante Features
- Multi-Service Compose Support
- Container Log-Streaming
- Resource Limits und Health Checks
- Web-UI Integration

### Fehler melden
Bei Problemen oder Feature-Wünschen:
1. Prüfe die Dokumentation
2. Teste mit dem `explore_api.py` Script
3. Erstelle ein Issue mit detaillierter Beschreibung