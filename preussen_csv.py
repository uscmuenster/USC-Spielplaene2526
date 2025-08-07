from pathlib import Path
from datetime import datetime
import csv
import pytz

# Ordner und Dateien
csv_dir = Path("csv_Baskets")
ics_file = csv_dir / "Preussen_2526.ics"
csv_file = csv_dir / "Preussen_2526_Heimspiele.csv"

# Zeitzone und Stichtag
berlin = pytz.timezone("Europe/Berlin")
stichtag = berlin.localize(datetime(2025, 8, 1))

# ICS-Datei prüfen
if not ics_file.exists():
    print(f"❌ ICS-Datei nicht gefunden: {ics_file}")
    exit(1)

# ICS-Inhalt lesen
with ics_file.open(encoding="utf-8") as f:
    content = f.read()

# Events extrahieren
events = content.split("BEGIN:VEVENT")[1:]
print(f"📅 Anzahl Events: {len(events)}")

heimspiele = []

for event in events:
    lines = event.strip().splitlines()

    # Gegnersuche: Nur Heimspiele von Preußen Münster
    summary_line = next((line for line in lines if "SUMMARY:SC Preußen Münster - " in line), None)
    if not summary_line:
        continue

    try:
        gegner_raw = summary_line.split("SUMMARY:SC Preußen Münster - ")[1].strip()
        gegner = gegner_raw.split(" | ")[0].strip()
    except Exception as e:
        print(f"⚠️ Gegner-Fehler: {e}")
        continue

    # DESCRIPTION vollständig zusammensetzen
    description_parts = []
    capture = False
    for line in lines:
        if line.startswith("DESCRIPTION:"):
            description_parts.append(line[len("DESCRIPTION:"):].strip())
            capture = True
        elif capture and (line == "" or line[0].isspace() or not line[0].isalpha()):
            description_parts.append(line.strip())
        elif capture:
            break
    description = " ".join(description_parts)
    termin_offen = "Der endgültige Spieltermin wurde noch nicht festgelegt" in description

    # DTSTART auslesen
    dtstart_line = next((line for line in lines if line.startswith("DTSTART")), None)
    if not dtstart_line:
        continue

    try:
        dt_raw = dtstart_line.split(":")[1]

        if "VALUE=DATE" in dtstart_line:
            # Nur Datum vorhanden → kein Zeitpunkt festgelegt
            dt = datetime.strptime(dt_raw, "%Y%m%d")
            dt = berlin.localize(dt)
            uhrzeit = "???"
        else:
            dt = datetime.strptime(dt_raw, "%Y%m%dT%H%M%S")
            dt = berlin.localize(dt)
            uhrzeit = "???" if termin_offen else dt.strftime("%H:%M")

        # Nur Spiele ab 01.08.2025
        if dt >= stichtag:
            heimspiele.append((dt.strftime("%d.%m.%Y"), uhrzeit, gegner))
    except Exception as e:
        print(f"⚠️ Fehler bei DTSTART: {e}")
        continue

# CSV schreiben
with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Datum", "Startzeit", "Gegner"])
    writer.writerows(heimspiele)

# Ergebnisanzeige
print(f"✅ Heimspiele extrahiert: {len(heimspiele)}")
print(f"💾 Datei gespeichert: {csv_file}")
