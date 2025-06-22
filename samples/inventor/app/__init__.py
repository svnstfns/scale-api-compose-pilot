# app/__init__.py
"""
VideoInventory - Ein System zur Inventarisierung und Verwaltung von Videodateien.

Dieses Paket enthält Module für:
- Konfiguration und Datenbankanbindung
- Entdeckung von Videoverzeichnissen
- Zählung und Indexierung von Dateien
- Metadatenverarbeitung für Videodateien
- Parallelverarbeitung mit Multithreading
- Statusanzeigen und Logging
"""

__version__ = '1.0.1'

# Importiere Hauptkomponenten für einfacheren Zugriff
from app.config import Config
from app.logger import setup_logger
from app.section_processor import SectionProcessor

