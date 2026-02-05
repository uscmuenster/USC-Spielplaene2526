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
    summary_line = next((line for line in lines if line.startswith("SUMMARY:")), None)
    if not summary_line:
        continue

    summary = summary_line.replace("SUMMARY:", "").strip()

    # Nur Heimspiele: "Uni Baskets Münster vs XYZ"
    if not summary.startswith("ProA Spiel Uni Baskets Münster vs "):
        continue

    gegner = summary.replace("ProA Spiel Uni Baskets Münster vs ", "").strip()

    dtstart_line = next(
        (line for line in lines if line.startswith("DTSTART")),
        None
    )
    if not dtstart_line:
        continue

    dt_str = dtstart_line.split(":")[1].strip()

    try:
        if len(dt_str) == 15:  # YYYYMMDDTHHMMSS
            dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%S")
        else:                  # YYYYMMDDTHHMM
            dt = datetime.strptime(dt_str, "%Y%m%dT%H%M")
        dt = berlin.localize(dt)
    except Exception as e:
        print(f"⚠️ Fehler beim Datum '{dt_str}': {e}")
        continue

# CSV schreiben
with csv_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Datum", "Startzeit", "Gegner"])
    writer.writerows(heimspiele)

# Ergebnis
print(f"✅ Heimspiele gefunden: {len(heimspiele)}")
print(f"💾 CSV geschrieben: {csv_file}")
