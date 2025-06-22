# app/video_metadata.py
import os
import subprocess
import json
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Tuple
import time


class VideoMetadata:
    """
    Liest und schreibt Metadaten für Videodateien mit FFmpeg mit verbesserter Fehlerbehandlung.
    """

    def __init__(self, file_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialisiert den VideoMetadata-Handler mit einem Dateipfad.

        Args:
            file_path: Pfad zur Videodatei
            logger: Logger-Instance (optional)
        """
        self.file_path = file_path
        self.logger = logger or logging.getLogger(__name__)

        # Prüfe, ob FFmpeg installiert ist
        self._check_ffmpeg_installed()

    def _check_ffmpeg_installed(self) -> None:
        """
        Überprüft, ob FFmpeg und FFprobe installiert sind.
        Loggt eine Warnung, wenn eines der Programme nicht gefunden wird.
        """
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            self.logger.error(
                "FFmpeg oder FFprobe ist nicht installiert oder nicht im PATH. Video-Metadaten-Operationen werden fehlschlagen.")

    def get_metadata(self, key: str = None) -> Any:
        """
        Liest Metadaten aus der Videodatei.

        Args:
            key: Schlüssel des Metadaten-Eintrags (optional)
                 Wenn None, werden alle Metadaten zurückgegeben

        Returns:
            Wert des Metadaten-Eintrags, alle Metadaten als Dict, oder leerer String/Dict bei Fehler
        """
        try:
            # Verwende FFprobe, um Metadaten zu lesen
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                self.file_path
            ]

            max_retries = 3
            for retry in range(max_retries):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    metadata = json.loads(result.stdout)

                    # Wenn kein Schlüssel angegeben wurde, gib alle Metadaten zurück
                    if key is None:
                        return metadata

                    # Prüfe, ob der Schlüssel in den Format-Metadaten vorhanden ist
                    if 'format' in metadata and 'tags' in metadata['format']:
                        return metadata['format']['tags'].get(key, '')

                    return ''
                except subprocess.SubprocessError as e:
                    if retry < max_retries - 1:
                        self.logger.warning(
                            f"Fehler beim Lesen von Metadaten aus '{self.file_path}', Versuch {retry + 1}/{max_retries}: {str(e)}")
                        time.sleep(1)
                    else:
                        raise

            return '' if key else {}
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            self.logger.error(f"Fehler beim Lesen von Metadaten aus '{self.file_path}': {str(e)}")
            return '' if key else {}

    def add_metadata(self, key: str, value: str) -> bool:
        """
        Fügt oder aktualisiert einen Metadaten-Eintrag in der Videodatei.
        Verwendet einen temporären Pfad für die Sicherheit.

        Args:
            key: Schlüssel des Metadaten-Eintrags
            value: Wert des Metadaten-Eintrags

        Returns:
            True, wenn erfolgreich, sonst False
        """
        # Erstelle ein temporäres Verzeichnis für die Ausgabe
        with tempfile.TemporaryDirectory() as temp_dir:
            # Temporäre Ausgabedatei im temporären Verzeichnis
            temp_output = os.path.join(temp_dir, os.path.basename(self.file_path))

            try:
                # Verwende FFmpeg, um Metadaten zu schreiben
                cmd = [
                    'ffmpeg',
                    '-i', self.file_path,
                    '-c', 'copy',  # Kopiere alle Streams ohne Neukodierung
                    '-metadata', f"{key}={value}",
                    '-y',  # Überschreibe die Ausgabedatei, falls sie existiert
                    temp_output
                ]

                # Führe Befehl mit Fehlerbehandlung aus
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        subprocess.run(cmd, capture_output=True, check=True)

                        # Prüfe, ob die temporäre Datei erstellt wurde und eine vernünftige Größe hat
                        if not os.path.exists(temp_output) or os.path.getsize(temp_output) < 1000:
                            raise ValueError(
                                f"Die temporäre Ausgabedatei wurde nicht korrekt erstellt (Größe: {os.path.getsize(temp_output) if os.path.exists(temp_output) else 'nicht vorhanden'})")

                        # Ersetze die Originaldatei mit der aktualisierten Datei
                        shutil.move(temp_output, self.file_path)

                        self.logger.info(f"Metadaten '{key}={value}' zur Datei '{self.file_path}' hinzugefügt")
                        return True
                    except (subprocess.SubprocessError, IOError, OSError) as e:
                        if retry < max_retries - 1:
                            self.logger.warning(
                                f"Fehler beim Hinzufügen von Metadaten zu '{self.file_path}', Versuch {retry + 1}/{max_retries}: {str(e)}")
                            time.sleep(1)
                        else:
                            raise

                return False
            except (subprocess.SubprocessError, IOError, OSError, ValueError) as e:
                self.logger.error(f"Fehler beim Hinzufügen von Metadaten zu '{self.file_path}': {str(e)}")
                return False

    def get_video_info(self) -> Optional[Dict[str, Any]]:
        """
        Extrahiert grundlegende Videoinformationen aus der Datei.

        Returns:
            Dict mit Video-Informationen oder None bei Fehler
        """
        try:
            # Verwende FFprobe, um Videoinformationen zu extrahieren
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'v:0',  # Nur den ersten Videostream
                self.file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            if 'streams' not in data or not data['streams']:
                return None

            video_stream = data['streams'][0]

            # Extrahiere relevante Informationen
            info = {
                'codec': video_stream.get('codec_name', 'unknown'),
                'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                'duration': float(video_stream.get('duration', 0)),
                'bit_rate': int(video_stream.get('bit_rate', 0)) if 'bit_rate' in video_stream else 0,
                'frame_rate': self._parse_frame_rate(video_stream.get('r_frame_rate', '0/1'))
            }

            # Bestimme Qualitätskategorie
            width = video_stream.get('width', 0)
            if width >= 7680:  # 8K
                info['quality'] = '8K'
            elif width >= 3840:  # 4K
                info['quality'] = '4K'
            elif width >= 2560:  # 1440p
                info['quality'] = 'QHD'
            elif width >= 1920:  # 1080p
                info['quality'] = 'FHD'
            elif width >= 1280:  # 720p
                info['quality'] = 'HD'
            elif width >= 720:  # 480p
                info['quality'] = 'SD'
            else:
                info['quality'] = 'LD'  # Low Definition

            return info

        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Fehler beim Abrufen von Videoinformationen für '{self.file_path}': {str(e)}")
            return None

    def _parse_frame_rate(self, rate_str: str) -> float:
        """
        Parst einen Frame-Rate-String im Format 'num/den'.

        Args:
            rate_str: Frame-Rate als String im Format 'num/den'

        Returns:
            Frame-Rate als Float
        """
        try:
            num, den = map(int, rate_str.split('/'))
            if den == 0:
                return 0.0
            return num / den
        except (ValueError, ZeroDivisionError):
            return 0.0