# USC-Spielpläne 2025/26

Dieses Repository bündelt sämtliche Spielpläne der Mannschaften des USC Münster sowie ergänzende Informationen zu Heimspielen der Uni Baskets und von Preußen Münster. Die Rohdaten werden als CSV bzw. ICS eingespielt, durch mehrere Python-Skripte aufbereitet und anschließend in Form einer Webseite (`docs/index.html` / `docs/indexapp.html`), einer kombinierten CSV (`docs/spielplan.csv`) und einer ICS-Datei (`docs/usc_spielplan.ics`) veröffentlicht.

Alle HTML-/CSV-/ICS-Dateien werden aus den Python-Skripten generiert. Änderungen sind deshalb immer direkt in den Python-Dateien vorzunehmen; generierte Artefakte werden bei Bedarf neu erzeugt und eingecheckt.

## Verzeichnisstruktur

- `csvdata/` – Eingangsdaten aus dem SAMS-System (Semikolon-getrennte CSV mit Windows-1252-Kodierung).
- `csv_Baskets/` – heruntergeladene ICS-Dateien der Uni Baskets & Preußen sowie daraus erzeugte CSV-Auszüge.
- `docs/` – veröffentlichte Artefakte für GitHub Pages (`index.html`, `indexapp.html`, `index_trainer.html`, `spielplan.csv`, `usc_spielplan.ics`, Assets).
- `usc_spielplan.py` – generiert die HTML-Spielpläne für `index.html` und `indexapp.html` nur aus USC-Daten.
- `usc_baskets_preussen.py` – Variante der HTML-Generierung, die zusätzlich die Heimspiele der Uni Baskets und von Preußen Münster einbindet (`docs/index_trainer.html`).
- `generate_csv.py` – fasst alle USC-relevanten Begegnungen zu einer Sammel-CSV zusammen (`docs/spielplan.csv`).
- `usc_spielplan_ics.py` – erstellt eine ICS-Datei mit allen USC-Heimspielen (`docs/usc_spielplan.ics`).
- `baskets_csv.py` / `preussen_csv.py` – extrahieren aus den ICS-Dateien der Uni Baskets bzw. Preußen Münster deren Heimspiele als CSV.
- `.github/workflows/` – GitHub-Actions-Workflows zur Automatisierung von Downloads, Generierung und Veröffentlichung.
- `requirements.txt` – minimale Python-Abhängigkeiten für lokale Ausführungen.

## Voraussetzungen

- Python ≥ 3.10
- Empfohlene Installation der Abhängigkeiten (lokal identisch zu den GitHub-Actions):
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  pip install pandas pytz
  ```

> **Hinweis:** Die Skripte erwarten, dass sie aus dem Repository-Wurzelverzeichnis gestartet werden, damit relative Pfade zu `csvdata/`, `csv_Baskets/` und `docs/` stimmen.

## Datenquellen aktualisieren

### Volleyball-Spielpläne aus SAMS

1. Für jede USC-Mannschaft im SAMS-System eine CSV mit Semikolon als Trenner exportieren.
2. Die Dateien exakt so benennen wie in den Skripten hinterlegt (z. B. `Spielplan_1._Bundesliga_Frauen.csv`).
3. Die CSV-Dateien nach `csvdata/` kopieren und vorhandene Versionen überschreiben.
4. Falls neue Teams hinzukommen oder Dateinamen sich ändern, sowohl die `csv_files`-Listen in `usc_spielplan.py`, `usc_baskets_preussen.py`, `generate_csv.py` und `usc_spielplan_ics.py` als auch ggf. die Team-Code-Zuweisungen und Regex-Anpassungen aktualisieren.

### Uni Baskets & Preußen Münster (ICS)

1. Die GitHub-Actions laden die ICS-Dateien automatisch (siehe Workflow unten). Für manuelle Updates: ICS-Dateien nach `csv_Baskets/Baskets_2526.ics` bzw. `csv_Baskets/Preussen_2526.ics` speichern.
2. Skripte `baskets_csv.py` und `preussen_csv.py` ausführen, um Heimspiele nach CSV zu extrahieren.
3. Die erzeugten CSV-Dateien (`Baskets_2526_Heimspiele.csv`, `Preussen_2526_Heimspiele.csv`) dienen als Eingabe für `usc_baskets_preussen.py`.

## Python-Skripte im Detail

### `usc_spielplan.py`

- Liest alle konfigurierten CSVs aus `csvdata/`, filtert nach USC-Beteiligung (Team, Gastgeber, Schiedsgericht) und harmonisiert Namenskonventionen.
- Fügt Wochentagsspalten, formatiert Uhrzeiten und berechnet aus Satzdaten ein kompaktes Ergebnisformat.
- Entfernt bereits gespielte Begegnungen ohne USC-Beteiligung, damit der Fokus auf anstehenden Spielen liegt.
- Generiert zwei HTML-Dateien:
  - `docs/index.html` mit Standardschriftgrößen.
  - `docs/indexapp.html` mit reduzierter Typografie für mobile Ansichten.
- Anpassungspunkte:
  - `csv_files` für neue Ligen oder Umbenennungen.
  - Regex-Logik in `get_usc_team`/`replace_usc_names`, falls Namensschemata sich ändern.
  - Styling direkt im eingebetteten CSS.

### `usc_baskets_preussen.py`

- Gleicher Grundaufbau wie `usc_spielplan.py`, ergänzt jedoch um Heimspiele aus `csv_Baskets/Baskets_2526_Heimspiele.csv` und optional Preußen (`csv_Baskets/Preussen_2526_Heimspiele.csv`).
- Erzeugt `docs/index_trainer.html` als Sammelübersicht für Volleyball-, Basketball- und Fußball-Heimspiele.
- Erwartet, dass die CSVs bereits vorliegen (siehe Abschnitt „Uni Baskets & Preußen Münster (ICS)“). Fehlende Dateien werden still ignoriert.
- Enthält zusätzliche Filterlogik, die auch Nicht-USC-Veranstaltungen (Baskets/Preußen) nur so lange anzeigt, bis das Datum vergangen ist.

### `generate_csv.py`

- Fasst sämtliche USC-relevanten Begegnungen in `docs/spielplan.csv` zusammen (Semikolon-getrennt, UTF-8 mit BOM).
- Entfernt Nicht-USC-Spiele vollständig und vereinheitlicht Namensschreibweisen identisch zu `usc_spielplan.py`.
- Für spätere Auswertungen werden Datum, Uhrzeit und Wochentag normalisiert. Debug-Ausgaben im Terminal helfen bei Plausibilitätsprüfungen.

### `usc_spielplan_ics.py`

- Erstellt `docs/usc_spielplan.ics` und nimmt alle Spiele auf, bei denen USC als Gastgeber fungiert und gleichzeitig auf dem Feld steht.
- Start- und Endzeiten werden aus den CSV-Daten übernommen (Standarddauer 2 Stunden), die Zeitzonenbehandlung erfolgt via `pytz`.
- Anpassungen an Beschreibung, UID oder Filterkriterien sind im Abschnitt `generate_ics` möglich.

### `baskets_csv.py` & `preussen_csv.py`

- Parsen heruntergeladene ICS-Dateien und extrahieren nur die Heimspiele.
- `baskets_csv.py` erwartet, dass das ICS-SUMMARY-Feld mit „Uni Baskets Münster - …“ beginnt.
- `preussen_csv.py` berücksichtigt unsichere Termine (mit Stern) und ignoriert Einträge vor dem Stichtag 1. August 2025.
- Beide Skripte erzeugen kleine CSVs, die unverändert von `usc_baskets_preussen.py` übernommen werden.

## Manuelle Generierung der Artefakte

```bash
# 1. Webseite (USC-only)
python usc_spielplan.py

# 2. Traineransicht mit Baskets & Preußen
python usc_baskets_preussen.py

# 3. Aggregierte CSV
python generate_csv.py

# 4. ICS-Kalender
python usc_spielplan_ics.py

# 5. Optional: CSVs aus neuen ICS-Dateien erzeugen
python baskets_csv.py
python preussen_csv.py
```

Die Skripte können unabhängig voneinander laufen. Nach jeder Ausführung die entsprechenden Dateien in `docs/` prüfen und anschließend committen.

## Automatisierte GitHub-Workflows

### `.github/workflows/generate_csv.yml`

- Trigger: Push auf `Spielplan_*.csv`, manueller Workflow-Dispatch oder stündliche Ausführung.
- Schritte:
  1. Check-out mit PAT (`secrets.GH_PAT`).
  2. Installation von Python 3.10 und `pandas`.
  3. Ausführen von `generate_csv.py`.
  4. Commit & Push von `docs/spielplan.csv`.
- Anpassungen: Bei zusätzlichen Abhängigkeiten oder Dateipfaden die Installations- bzw. `git add`-Schritte erweitern.

### `.github/workflows/gesamtworkflow.yml`

- Trigger: manueller Start oder stündlich per Cron. Über `concurrency` wird ein paralleler Lauf verhindert.
- Ablauf in fünf Blöcken:
  1. **ICS-Download**: Löscht `csv_Baskets`, lädt ICS der Uni Baskets & Preußen und committed Änderungen.
  2. **CSV-Download**: Lädt alle Volleyball-Spielpläne nach `csvdata/` (feste URLs) und committed sie.
  3. **Baskets-CSV**: Wandelt das Baskets-ICS in eine Heimspiel-CSV um und committed das Ergebnis.
  4. **Preußen-CSV**: Gleiches Vorgehen für Preußen Münster.
  5. **HTML/ICS-Erstellung**: Führt `usc_baskets_preussen.py`, `usc_spielplan.py` und `usc_spielplan_ics.py` aus und committed die generierten Dateien in `docs/`.
- Jeder Block nutzt kurze Pausen (`sleep 30`), damit externe Systeme Updates verarbeiten können.
- Voraussetzungen: gültiges PAT in `secrets.GH_PAT` mit Schreibrechten, damit Commits aus dem Workflow möglich sind.

> **Tipp:** Falls zusätzliche Mannschaften aufgenommen werden oder URLs wechseln, zuerst die Python-Skripte aktualisieren und danach die entsprechenden Download-Abschnitte (URL-Listen, Dateinamen) im Workflow anpassen.

## Veröffentlichung über GitHub Pages

- GitHub Pages liefert den Inhalt von `docs/` unter <https://uscmuenster.github.io/USC-Spielplaene2526> aus.
- Nach lokalen Änderungen: Artefakte generieren, committen und pushen. GitHub Pages veröffentlicht automatisch die aktuelle Version des `docs/`-Verzeichnisses.
- Für Vorschauen kann eine lokale HTTP-Server-Instanz im `docs/`-Ordner gestartet werden (`python -m http.server`), um Layoutänderungen zu kontrollieren.

## Autor

Niels Westphal
