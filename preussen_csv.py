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

# Prüfen, ob ICS-Datei existiert
if not ics_file.exists():
    print(f"❌ ICS-Datei nicht gefunden: {ics_file}")
    exit(1)

# ICS-Inhalt lesen
with ics_file.open(encoding="utf-8") as f:
    content = f.read()

# Events extrahieren
events = content.split("BEGIN:VEVENT")[1:]
print(f"📅 Anzahl aller Events: {len(events)}")

heimspiele = []

for event in events:
    lines = event.strip().splitlines()

    # Nur Heimspiele von SC Preußen Münster
    summary_line = next((line for line in lines if "SUMMARY:SC Preußen Münster - " in line), None)
    if not summary_line:
        continue

    # Gegner extrahieren
    try:
        summary = summary_line.split("SUMMARY:SC Preußen Münster - ")[1].strip()
        gegner = summary.split(" | ")[0].strip()
    except Exception as e:
        print(f"⚠️ Fehler beim Gegner: {e}")
        continue

    # DESCRIPTION zusammensetzen (mehrzeilig)
    desc_lines = []
    desc_started = False
    for line in lines:
        if line.startswith("DESCRIPTION"):
            desc_lines.append(line.split("DESCRIPTION:")[1])
            desc_started = True
        elif desc_started and not line.startswith(tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
            desc_lines.append(line.strip())
        elif desc_started:
            break
    description = " ".join(desc_lines)
    termin_offen = "Der endgültige Spieltermin wurde noch nicht festgelegt" in description

    # DTSTART verarbeiten
    dtstart_line = next((line for line in lines if line.startswith("DTSTART")), None)
    if not dtstart_line:
        continue

    try:
        dt_str = dtstart_line.split(":")[1]

        if "VALUE=DATE" in dtstart_line:
            # Ganztägiger Eintrag ohne Uhrzeit
            dt = datetime.strptime(dt_str, "%Y%m%d")
            dt = berlin.localize(dt)
            uhrzeit = "???"
        else:
            # Termin mit Uhrzeit
            dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
            dt = berlin.localize(dt)
            uhrzeit = "???" if termin_offen else dt.strftime("%H:%M")

        if dt >= stichtag:
            heimspiele.append((dt.strftime("%d.%m.%Y"), uhrzeit, gegner))
    except Exception as e:
        print(f"⚠️ Fehler beim Datum: {e}")
        continue

# CSV schreiben
with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Datum", "Startzeit", "Gegner"])
    writer.writerows(heimspiele)

# Ergebnis
print(f"✅ Heimspiele gefunden: {len(heimspiele)}")
print(f"💾 CSV geschrieben: {csv_file}")
