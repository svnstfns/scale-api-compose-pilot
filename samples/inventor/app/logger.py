# app/logger.py
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from typing import Dict, Optional

# Globales Dictionary für Logger-Instanzen
_loggers: Dict[str, logging.Logger] = {}


def setup_logger(name: str, log_dir: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    Konfiguriert und gibt einen Logger zurück. Verwendet Cache, um doppelte Logger zu vermeiden.

    Args:
        name: Name des Loggers
        log_dir: Verzeichnis für die Logdateien (optional)
        log_level: Logging-Level (optional)

    Returns:
        Konfigurierter Logger
    """
    global _loggers

    # Prüfe, ob der Logger bereits existiert
    if name in _loggers:
        return _loggers[name]

    # Erstelle den Logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Entferne vorhandene Handler, falls es sie gibt
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Konsolen-Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Formatter für alle Handler
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Datei-Handler, falls ein Logverzeichnis angegeben wurde
    if log_dir:
        # Stelle sicher, dass das Logverzeichnis existiert
        os.makedirs(log_dir, exist_ok=True)

        # Erstelle eine Datei mit Zeitstempel
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")

        # Erstelle einen rotierenden Datei-Handler (max. 10MB pro Datei, 5 Backup-Dateien)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Speichere den Logger in der globalen Sammlung
    _loggers[name] = logger

    return logger


class Logger:
    """
    Logger-Klasse für abwärtskompatible API.
    """

    def __init__(self, log_dir: str = '/app/logs', log_file: str = 'app.log'):
        """
        Initialisiert den Logger mit einem bestimmten Verzeichnis und einer Datei.

        Args:
            log_dir: Verzeichnis für die Logdateien
            log_file: Name der Logdatei
        """
        self.log_dir = log_dir
        self.log_file = log_file.replace('.log', '')  # Entferne die .log-Endung
        self.logger = None

    def get_logger(self) -> logging.Logger:
        """
        Gibt eine Logger-Instanz zurück.

        Returns:
            Logger-Instanz
        """
        if self.logger is None:
            self.logger = setup_logger(self.log_file, self.log_dir)
        return self.logger