# USC-Spielpläne 2025/26

Dieses Repository bündelt die Spielpläne der Mannschaften des USC Münster. Aus den aus dem SAMS-System exportierten CSV-Dateien werden eine Webseite, eine kombinierte CSV-Datei sowie eine ICS-Kalenderdatei erzeugt, die anschließend über GitHub Pages veröffentlicht werden können.

## Verzeichnisstruktur

- `csvdata/` – Eingangsdaten (SAMS-Exporte als `;`-separierte CSV mit Windows-1252-Kodierung).
- `docs/` – Ausgabedateien, die von GitHub Pages ausgeliefert werden (`index.html`, `indexapp.html`, `spielplan.csv`, `usc_spielplan.ics`, Assets).
- `usc_spielplan.py` – erzeugt die HTML-Ansicht inkl. Filterfunktionen.
- `generate_csv.py` – erstellt die konsolidierte CSV-Datei unter `docs/spielplan.csv`.
- `usc_spielplan_ics.py` – generiert eine Kalenderdatei (`docs/usc_spielplan.ics`).

## Voraussetzungen

- Python ≥ 3.10
- Installierte Abhängigkeiten:
  ```bash
  pip install -r requirements.txt
  pip install pandas pytz
  ```

## CSV-Dateien aktualisieren

1. Melde dich im SAMS-System an und exportiere für jede Mannschaft eine CSV-Datei mit Semikolon als Trennzeichen.
2. Benenne die Dateien gemäß der Konfiguration in den Skripten (z. B. `Spielplan_1._Bundesliga_Frauen.csv`).
3. Kopiere die Dateien in den Ordner `csvdata/` und ersetze vorhandene Versionen.

## Ausgaben erzeugen

Alle Skripte gehen davon aus, dass sie aus dem Projektwurzelverzeichnis gestartet werden.

1. **HTML-Seiten aktualisieren**
   ```bash
   python usc_spielplan.py
   ```
   Dadurch werden `docs/index.html` (Standardansicht) und `docs/indexapp.html` (kompaktere Ansicht) aktualisiert.

2. **CSV zusammenführen**
   ```bash
   python generate_csv.py
   ```
   Die aggregierte Datei liegt anschließend unter `docs/spielplan.csv` und kann zum Download auf der Webseite angeboten werden.

3. **Kalenderdatei erzeugen (optional)**
   ```bash
   python usc_spielplan_ics.py
   ```
   Die erzeugte Datei `docs/usc_spielplan.ics` enthält alle Termine für Kalender-Apps.

## Veröffentlichung

Die Inhalte des Ordners `docs/` werden von GitHub Pages bereitgestellt. Nach einem Commit und Push der aktualisierten Dateien werden die Änderungen unter https://uscmuenster.github.io/USC-Spielplaene2526 sichtbar.

## Autor

Niels Westphal
