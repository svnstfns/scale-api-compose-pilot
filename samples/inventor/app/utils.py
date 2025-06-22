# app/utils.py
import os
import shutil
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple


def human_readable_size(size_in_bytes: int) -> str:
    """
    Konvertiert eine Dateigröße von Bytes in ein menschenlesbares Format.

    Args:
        size_in_bytes: Größe der Datei in Bytes

    Returns:
        Menschenlesbare Dateigröße (z.B. '10.5 MB')
    """
    if size_in_bytes < 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"  # Falls die Datei größer als TB ist


def safe_filename(filename: str) -> str:
    """
    Ersetzt problematische Zeichen in Dateinamen.

    Args:
        filename: Originaler Dateiname

    Returns:
        Bereinigter Dateiname
    """
    # Ersetze problematische Zeichen durch Unterstriche
    problematic_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    safe_name = filename

    for char in problematic_chars:
        safe_name = safe_name.replace(char, '_')

    return safe_name


def calculate_file_hash(file_path: str, hash_type: str = 'sha256', chunk_size: int = 8192) -> Optional[str]:
    """
    Berechnet den Hash einer Datei.

    Args:
        file_path: Pfad zur Datei
        hash_type: Typ des Hashes (md5, sha1, sha256, etc.)
        chunk_size: Größe der zu lesenden Chunks

    Returns:
        Hash der Datei als hexadezimale Zeichenkette oder None bei Fehler
    """
    try:
        hash_func = getattr(hashlib, hash_type)()

        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            while chunk:
                hash_func.update(chunk)
                chunk = f.read(chunk_size)

        return hash_func.hexdigest()
    except (IOError, OSError, AttributeError) as e:
        # Log den Fehler, aber gib None zurück anstatt eine Exception zu werfen
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fehler beim Berechnen des Hashes für '{file_path}': {e}")
        return None


def safe_copy_file(source_path: str, target_path: str) -> Tuple[bool, Optional[str]]:
    """
    Kopiert eine Datei sicher mit Fehlerbehandlung.

    Args:
        source_path: Quellpfad
        target_path: Zielpfad

    Returns:
        Tuple aus (Erfolg, Fehlermeldung)
    """
    try:
        # Stelle sicher, dass das Zielverzeichnis existiert
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)

        # Kopiere die Datei
        shutil.copy2(source_path, target_path)
        return True, None
    except Exception as e:
        return False, str(e)


def safe_move_file(source_path: str, target_path: str) -> Tuple[bool, Optional[str]]:
    """
    Verschiebt eine Datei sicher mit Fehlerbehandlung.

    Args:
        source_path: Quellpfad
        target_path: Zielpfad

    Returns:
        Tuple aus (Erfolg, Fehlermeldung)
    """
    try:
        # Stelle sicher, dass das Zielverzeichnis existiert
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)

        # Verschiebe die Datei
        shutil.move(source_path, target_path)
        return True, None
    except Exception as e:
        return False, str(e)


def get_file_extension(filename: str) -> str:
    """
    Gibt die Dateierweiterung zurück.

    Args:
        filename: Dateiname

    Returns:
        Dateierweiterung ohne Punkt oder leere Zeichenkette
    """
    _, ext = os.path.splitext(filename)
    if ext.startswith('.'):
        ext = ext[1:]
    return ext.lower()


def is_video_file(filename: str) -> bool:
    """
    Prüft, ob es sich um eine Videodatei handelt.

    Args:
        filename: Dateiname

    Returns:
        True, wenn es sich um eine Videodatei handelt, sonst False
    """
    video_extensions = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'mpeg', 'mpg', 'm4v']
    ext = get_file_extension(filename)
    return ext in video_extensions


def is_mp4_file(filename: str) -> bool:
    """
    Prüft, ob es sich um eine MP4-Datei handelt.

    Args:
        filename: Dateiname

    Returns:
        True, wenn es sich um eine MP4-Datei handelt, sonst False
    """
    return get_file_extension(filename) == 'mp4'


def normalize_path(path: str) -> str:
    """
    Normalisiert einen Pfad für die konsistente Verarbeitung.

    Args:
        path: Originaler Pfad

    Returns:
        Normalisierter Pfad
    """
    # Konvertiere zu absolutem Pfad
    abs_path = os.path.abspath(path)

    # Normalisiere Pfadtrennzeichen
    norm_path = os.path.normpath(abs_path)

    return norm_path