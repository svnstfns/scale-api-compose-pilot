# app/status_display.py
import os
import sys
import time
import re
from typing import Dict, Any, Optional, List, Tuple
from threading import Lock


class StatusDisplay:
    """
    Eine Klasse zum Anzeigen von festen Status-Informationsvorlagen auf der Konsole
    mit visuellen Verbesserungen wie Progress Bars und ausgerichteten Doppelpunkten.
    """

    def __init__(self, title: str, template: List[str], update_interval: float = 0.5):
        """
        Initialisiert das Status-Display.

        Args:
            title: Titel des Status-Displays
            template: Liste von Zeichenketten mit Formatplatzhaltern für Werte
            update_interval: Minimale Zeit zwischen Bildschirmaktualisierungen in Sekunden
        """
        self.title = title
        self.template = template
        self.update_interval = update_interval
        self.values: Dict[str, Any] = {}
        self.last_update_time = 0
        self.lock = Lock()
        self.is_enabled = True

        # Erkennen, ob wir in einem Terminal laufen, das ANSI-Escape-Codes unterstützt
        self.supports_ansi = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

        # Terminalgröße speichern
        self.terminal_width = self._get_terminal_width()

        # Farben
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[32m',
            'blue': '\033[34m',
            'cyan': '\033[36m',
            'yellow': '\033[33m',
            'red': '\033[31m',
            'magenta': '\033[35m',
        }

        # Progress-Bar-Konfiguration
        self.progress_bar_width = max(20, self.terminal_width // 4)
        self.progress_chars = {
            'start': '[',
            'end': ']',
            'fill': '█',
            'empty': '·',
        }

    def _get_terminal_width(self) -> int:
        """Ermittelt die Terminalbreite, wenn möglich, oder standardmäßig 80."""
        try:
            return os.get_terminal_size().columns
        except (AttributeError, OSError):
            return 80

    def set_value(self, key: str, value: Any) -> None:
        """
        Setzt einen Wert, der in der Vorlage angezeigt werden soll.

        Args:
            key: Der Platzhalter-Schlüssel in der Vorlage
            value: Der anzuzeigende Wert
        """
        with self.lock:
            self.values[key] = value

            # Prüfen, ob es Zeit ist, das Display zu aktualisieren
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.update()
                self.last_update_time = current_time

    def set_multiple(self, values_dict: Dict[str, Any]) -> None:
        """
        Setzt mehrere Werte auf einmal und aktualisiert die Anzeige.

        Args:
            values_dict: Dictionary mit Schlüssel-Wert-Paaren zur Aktualisierung
        """
        with self.lock:
            self.values.update(values_dict)

            # Prüfen, ob es Zeit ist, das Display zu aktualisieren
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.update()
                self.last_update_time = current_time

    def _align_colons(self, lines: List[str]) -> List[str]:
        """
        Richtet den Text an Doppelpunkten aus.

        Args:
            lines: Liste von Textzeilen mit Doppelpunkten

        Returns:
            Liste mit ausgerichteten Textzeilen
        """
        # Finde die längste Beschriftung vor einem Doppelpunkt
        max_label_length = 0
        for line in lines:
            if ':' in line:
                label_length = line.find(':')
                max_label_length = max(max_label_length, label_length)

        # Richte die Doppelpunkte aus
        aligned_lines = []
        for line in lines:
            if ':' in line:
                label, value = line.split(':', 1)
                aligned_line = f"{label.ljust(max_label_length)}: {value.lstrip()}"
                aligned_lines.append(aligned_line)
            else:
                aligned_lines.append(line)

        return aligned_lines

    def _create_progress_bar(self, current: int, total: int) -> str:
        """
        Erstellt eine Progress-Bar.

        Args:
            current: Aktueller Wert
            total: Gesamtwert

        Returns:
            Formatierte Progress-Bar als String
        """
        if total <= 0:
            percentage = 0
        else:
            percentage = min(100, int((current / total) * 100))

        # Anzahl der zu füllenden Zeichen berechnen
        fill_count = int((self.progress_bar_width * percentage) / 100)
        empty_count = self.progress_bar_width - fill_count

        # Progress-Bar erstellen
        bar = (
            f"{self.progress_chars['start']}"
            f"{self.colors['green']}{self.progress_chars['fill'] * fill_count}{self.colors['reset']}"
            f"{self.progress_chars['empty'] * empty_count}"
            f"{self.progress_chars['end']} {percentage}%"
        )

        return bar

    def _process_special_formats(self, line: str) -> str:
        """
        Verarbeitet spezielle Formatierungen wie Progress-Bars in den Zeilen.

        Args:
            line: Zu verarbeitende Zeile

        Returns:
            Verarbeitete Zeile mit speziellen Formatierungen
        """
        # Progress Bar für "X von Y" Muster
        progress_pattern = r'(\d+) von (\d+)'
        if re.search(progress_pattern, line):
            match = re.search(progress_pattern, line)
            if match:
                current = int(match.group(1))
                total = int(match.group(2))
                progress_bar = self._create_progress_bar(current, total)

                # Füge die Progress-Bar am Ende der Zeile hinzu
                return f"{line} {progress_bar}"

        return line

    def _format_status(self, status: str) -> str:
        """
        Formatiert den Statustext mit Farben basierend auf Schlüsselwörtern.

        Args:
            status: Statustext

        Returns:
            Formatierter Statustext
        """
        lower_status = status.lower()

        if 'fehler' in lower_status or 'error' in lower_status:
            return f"{self.colors['red']}{status}{self.colors['reset']}"
        elif 'abgeschlossen' in lower_status or 'completed' in lower_status or 'erfolg' in lower_status:
            return f"{self.colors['green']}{status}{self.colors['reset']}"
        elif 'warte' in lower_status or 'pending' in lower_status or 'ausstehend' in lower_status:
            return f"{self.colors['yellow']}{status}{self.colors['reset']}"
        elif 'verarbeite' in lower_status or 'processing' in lower_status or 'indexing' in lower_status:
            return f"{self.colors['cyan']}{status}{self.colors['reset']}"
        else:
            return status

    def _format_parallel_status(self, sections: List[Tuple[str, str]]) -> List[str]:
        """
        Erstellt eine Visualisierung der parallelen Verarbeitung.

        Args:
            sections: Liste von (Sektionsname, Status) Tupeln

        Returns:
            Liste formatierter Zeilen für die parallele Verarbeitung
        """
        if not sections:
            return []

        result = [f"Parallele Verarbeitung ({len(sections)} aktiv):"]

        for name, status in sections:
            # Kürze zu lange Namen
            if len(name) > 25:
                name = name[:22] + "..."

            # Formatiere den Status
            formatted_status = self._format_status(status)

            # Füge eine Zeile für jede aktive Sektion hinzu
            result.append(f"  • {name.ljust(25)} - {formatted_status}")

        return result

    def update(self) -> None:
        """Erzwingt eine Aktualisierung der Anzeige unabhängig vom Intervall."""
        if not self.is_enabled:
            return

        with self.lock:
            # Bildschirm löschen und Cursor in die obere linke Ecke bewegen
            if self.supports_ansi:
                sys.stdout.write("\033[2J\033[H")
            else:
                # Für Terminals, die ANSI nicht unterstützen, einfach einen Separator drucken
                sys.stdout.write("\n" + "=" * self.terminal_width + "\n")

            # Titel zentriert und farbig ausgeben
            title_display = f" {self.title} "
            padding = max(0, (self.terminal_width - len(title_display)) // 2)
            if self.supports_ansi:
                formatted_title = f"{self.colors['bold']}{self.colors['blue']}{title_display}{self.colors['reset']}"
            else:
                formatted_title = title_display

            sys.stdout.write("=" * padding + formatted_title + "=" * padding + "\n\n")

            # Formatierte Zeilen vorbereiten
            formatted_lines = []

            # Jede Zeile der Vorlage mit eingesetzten Werten formatieren
            for line in self.template:
                try:
                    # Platzhalter durch Werte ersetzen
                    formatted_line = line.format(**self.values)

                    # Spezielle Formate verarbeiten (wie Progress-Bars)
                    processed_line = self._process_special_formats(formatted_line)

                    # Status speziell formatieren
                    if 'Status:' in processed_line:
                        label, value = processed_line.split(':', 1)
                        processed_line = f"{label}:{self._format_status(value)}"

                    formatted_lines.append(processed_line)
                except KeyError as e:
                    # Wenn ein Platzhalter noch keinen Wert hat, ihn als ausstehend anzeigen
                    formatted_lines.append(f"{line} (ausstehend: {e})")

            # Parallele Verarbeitung visualisieren, wenn vorhanden
            parallel_sections = []
            if 'active_threads' in self.values and self.values['active_threads'] > 0:
                # Sammle aktive Sektionen und ihre Status, wenn verfügbar
                if 'active_sections' in self.values:
                    parallel_sections = self.values['active_sections']
                    parallel_lines = self._format_parallel_status(parallel_sections)
                    formatted_lines.extend([''] + parallel_lines)

            # Richte die Doppelpunkte aus
            aligned_lines = self._align_colons(formatted_lines)

            # Gib jede formatierte Zeile aus
            for line in aligned_lines:
                sys.stdout.write(f"{line}\n")

            # Eine Fußzeile hinzufügen
            sys.stdout.write("\n" + "=" * self.terminal_width + "\n")
            sys.stdout.flush()

    def add_log_line(self, message: str) -> None:
        """
        Fügt eine Protokollmeldung unter dem Status-Display hinzu.

        Args:
            message: Die anzuzeigende Protokollmeldung
        """
        if not self.is_enabled:
            return

        with self.lock:
            # In eine neue Zeile unter dem Status-Display wechseln und die Nachricht ausgeben
            if self.supports_ansi:
                sys.stdout.write(f"\n{message}\n")
            else:
                sys.stdout.write(f"{message}\n")
            sys.stdout.flush()

    def enable(self) -> None:
        """Aktiviert das Status-Display."""
        self.is_enabled = True
        self.update()

    def disable(self) -> None:
        """Deaktiviert das Status-Display."""
        self.is_enabled = False

    def finish(self, final_message: Optional[str] = None) -> None:
        """
        Beendet das Status-Display und zeigt optional eine abschließende Nachricht an.

        Args:
            final_message: Optionale abschließende Nachricht
        """
        with self.lock:
            self.update()  # Endgültige Aktualisierung mit den neuesten Werten

            if final_message:
                if self.supports_ansi:
                    sys.stdout.write("\n\n")
                    # Formatiere die abschließende Nachricht farbig
                    formatted_message = f"{self.colors['bold']}{self.colors['green']}{final_message}{self.colors['reset']}"
                    sys.stdout.write(f"{formatted_message}\n")
                else:
                    sys.stdout.write("\n\n")
                    sys.stdout.write(f"{final_message}\n")
                sys.stdout.flush()

            self.disable()