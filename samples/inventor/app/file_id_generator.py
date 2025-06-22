# app/file_id_generator.py
import os
import hashlib
import mimetypes
from typing import Optional
from app.utils import calculate_file_hash


class FileIDGenerator:
    """
    Generiert eindeutige IDs für Dateien basierend auf Pfad, Größe und Inhalt.
    """

    def __init__(self, file_path: str):
        """
        Initialisiert den Generator mit einem Dateipfad.

        Args:
            file_path: Pfad zur Datei
        """
        self.file_path = file_path

    def generate_file_id(self) -> str:
        """
        Generiert eine eindeutige ID für die Datei.
        Verwendet einen Algorithmus, der Pfad, Größe und einen partiellen Inhalts-Hash kombiniert.

        Returns:
            Eindeutige Datei-ID
        """
        # Absolute Pfad und Dateiname
        abs_path = os.path.abspath(self.file_path)

        # Dateigröße für zusätzliche Eindeutigkeit (falls vorhanden)
        try:
            file_size = os.path.getsize(self.file_path)
        except OSError:
            file_size = 0

        # Erstelle einen partiellen Hash des Dateianfangs (schneller als komplett)
        partial_content_hash = self._calculate_partial_hash()

        # Kombiniere Pfad, Größe und partiellen Hash zur Erstellung des Hashes
        hash_input = f"{abs_path}:{file_size}:{partial_content_hash}"

        # Erstelle einen SHA-256-Hash
        file_id = hashlib.sha256(hash_input.encode()).hexdigest()

        return file_id

    def _calculate_partial_hash(self, chunk_size: int = 4096, max_chunks: int = 5) -> str:
        """
        Berechnet einen partiellen Hash der Datei durch Lesen der ersten Chunks.

        Args:
            chunk_size: Größe jedes zu lesenden Chunks
            max_chunks: Maximale Anzahl von Chunks

        Returns:
            Partieller Hash als hexadezimale Zeichenkette
        """
        try:
            # Öffne Datei im Binärmodus
            with open(self.file_path, 'rb') as f:
                hasher = hashlib.md5()

                # Lese die ersten Chunks
                for _ in range(max_chunks):
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)

                return hasher.hexdigest()
        except (IOError, OSError):
            # Bei Fehlern gib einen leeren Hash zurück
            return "empty"

    def generate_content_hash(self) -> Optional[str]:
        """
        Berechnet einen vollständigen Inhaltshash der Datei.

        Returns:
            SHA-256-Hash des Dateiinhalts oder None bei einem Fehler
        """
        return calculate_file_hash(self.file_path)

    def is_probably_duplicate(self, other_file_path: str) -> bool:
        """
        Prüft, ob eine andere Datei wahrscheinlich ein Duplikat ist.

        Args:
            other_file_path: Pfad zur anderen Datei

        Returns:
            True, wenn die Dateien wahrscheinlich Duplikate sind, sonst False
        """
        # Prüfe zuerst die Dateigrößen
        try:
            size1 = os.path.getsize(self.file_path)
            size2 = os.path.getsize(other_file_path)

            if size1 != size2:
                return False

            # Prüfe MIME-Typen
            mime1, _ = mimetypes.guess_type(self.file_path)
            mime2, _ = mimetypes.guess_type(other_file_path)

            if mime1 != mime2:
                return False

            # Berechne partielle Hashes
            hash1 = self._calculate_partial_hash()
            other_generator = FileIDGenerator(other_file_path)
            hash2 = other_generator._calculate_partial_hash()

            return hash1 == hash2

        except (IOError, OSError):
            return False