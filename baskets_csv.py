from pathlib import Path
from datetime import datetime
import csv
import pytz

# Ordner und Dateien
csv_dir = Path("csv_Baskets")
ics_file = csv_dir / "Baskets_2526.ics"
csv_file = csv_dir / "Baskets_2526_Heimspiele.csv"

# Zeitzone
berlin = pytz.timezone("Europe/Berlin")

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

    # Gegner suchen
    summary_line = next((line for line in lines if line.startswith("SUMMARY:Uni Baskets Münster - ")), None)
    if not summary_line:
        continue

    gegner = summary_line.replace("SUMMARY:Uni Baskets Münster - ", "").strip()

    dtstart_line = next((line for line in lines if line.startswith("DTSTART;TZID=Europe/Berlin:")), None)
    if not dtstart_line:
        continue

    try:
        dt_str = dtstart_line.split(":")[1]
        dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")  # <-- jetzt korrekt mit Sekunden
        dt = berlin.localize(dt)
        heimspiele.append((dt.strftime("%d.%m.%Y"), dt.strftime("%H:%M"), gegner))
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
