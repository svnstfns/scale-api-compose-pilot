# app/main_display.py
from app.status_display import StatusDisplay
import time
import threading


class MainDisplay:
    """
    Eine zentrale Statusanzeige für die Hauptverarbeitung, die den Gesamtstatus des Systems anzeigt.
    """

    def __init__(self):
        """Initialisiert die Hauptstatusanzeige."""
        self.start_time = time.time()
        self.current_section = ""
        self.total_files = 0
        self.processed_files = 0
        self.completed_sections = 0
        self.total_sections = 0
        self.current_activity = "Initialisiere..."
        self.lock = threading.Lock()

        # Setup der Anzeige
        self._setup_display()

    def _setup_display(self):
        """Richtet die Hauptstatusanzeige ein."""
        template = [
            "Abschnitt:               {current_section}",
            "Verarbeitet:             {processed_files} von {total_files} Dateien",
            "Verzeichnisfortschritt:  {completed_sections} von {total_sections} Abschnitten abgeschlossen",
            "Zeit bis jetzt:          {elapsed_time}",
            "Aktuelle Verarbeitung:   {current_activity}"
        ]

        self.display = StatusDisplay("VideoInventory Status", template)

        # Initialisiere die Anzeige mit Anfangswerten
        self.display.set_multiple({
            "current_section": "Wird geladen...",
            "processed_files": 0,
            "total_files": 0,
            "completed_sections": 0,
            "total_sections": 0,
            "elapsed_time": "00:00:00",
            "current_activity": "Initialisiere..."
        })

    def update_section(self, section_path: str):
        """
        Aktualisiert den aktuellen Abschnitt.

        Args:
            section_path: Pfad des aktuellen Abschnitts
        """
        with self.lock:
            self.current_section = section_path
            self._update_display()

    def update_file_progress(self, processed: int, total: int):
        """
        Aktualisiert den Dateien-Fortschritt.

        Args:
            processed: Anzahl der verarbeiteten Dateien
            total: Gesamtanzahl der Dateien
        """
        with self.lock:
            self.processed_files = processed
            self.total_files = total
            self._update_display()

    def update_section_progress(self, completed: int, total: int):
        """
        Aktualisiert den Abschnitts-Fortschritt.

        Args:
            completed: Anzahl der abgeschlossenen Abschnitte
            total: Gesamtanzahl der Abschnitte
        """
        with self.lock:
            self.completed_sections = completed
            self.total_sections = total
            self._update_display()

    def update_activity(self, activity: str):
        """
        Aktualisiert die aktuelle Aktivität.

        Args:
            activity: Beschreibung der aktuellen Aktivität
        """
        with self.lock:
            self.current_activity = activity
            self._update_display()

    def _update_display(self):
        """Aktualisiert die Anzeige mit den aktuellen Werten."""
        elapsed_time = time.time() - self.start_time
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

        self.display.set_multiple({
            "current_section": self.current_section,
            "processed_files": self.processed_files,
            "total_files": self.total_files,
            "completed_sections": self.completed_sections,
            "total_sections": self.total_sections,
            "elapsed_time": elapsed_str,
            "current_activity": self.current_activity
        })

    def finish(self, message: str = None):
        """
        Beendet die Anzeige mit einer optionalen Nachricht.

        Args:
            message: Abschlussnachricht (optional)
        """
        if message:
            self.display.finish(message)
        else:
            elapsed_time = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))

            self.display.finish(
                f"Verarbeitung abgeschlossen in {elapsed_str}\n"
                f"Verarbeitet: {self.processed_files} Dateien in {self.completed_sections} Abschnitten"
            )


# Beispiel für die Verwendung
if __name__ == "__main__":
    # Erstelle eine Instanz der Hauptanzeige
    main_display = MainDisplay()

    # Simuliere Verarbeitung
    for i in range(5):
        section = f"/mnt/cluster-01/datasets/video-{i + 1}"
        main_display.update_section(section)
        main_display.update_section_progress(i, 5)

        for j in range(100):
            main_display.update_file_progress(j, 100)
            main_display.update_activity(f"metadata_indexing" if j < 50 else "file_processing")
            time.sleep(0.05)

        # Simuliere Abschluss dieses Abschnitts
        main_display.update_file_progress(100, 100)
        time.sleep(1)

    # Abschluss der Anzeige
    main_display.finish("Alle Verarbeitungen erfolgreich abgeschlossen!")