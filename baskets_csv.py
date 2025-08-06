from pathlib import Path
from datetime import datetime
import csv
import pytz

# Ordnerpfad
csv_dir = Path("csv_Baskets")

# Eingabedatei (ICS)
ics_path = csv_dir / "Baskets_2526.ics"

# Ausgabedatei (CSV)
csv_path = csv_dir / "Baskets_2526_Heimspiele.csv"

# Zeitzone definieren
berlin = pytz.timezone("Europe/Berlin")

# Prüfe ob die Datei existiert
if not ics_path.exists():
    print(f"❌ ICS-Datei nicht gefunden: {ics_path}")
    exit(1)

# Datei einlesen
with ics_path.open(encoding="utf-8") as f:
    content = f.read()

# Events extrahieren
events = content.split("BEGIN:VEVENT")[1:]
print(f"🔍 Anzahl aller Events: {len(events)}")

heimspiel_count = 0

# CSV-Datei schreiben
with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Datum", "Startzeit", "Gegner"])

    for event in events:
        lines = event.splitlines()
        summary_line = next((line for line in lines if line.startswith("SUMMARY:")), "")

        if summary_line.startswith("SUMMARY:Uni Baskets Münster - "):
            gegner = summary_line.replace("SUMMARY:Uni Baskets Münster - ", "").strip()
            dtstart_line = next((line for line in lines if line.startswith("DTSTART;TZID=Europe/Berlin:")), "")

            if not dtstart_line:
                continue

            dtstart_str = dtstart_line.split(":")[1]
            try:
                dt_local = berlin.localize(datetime.strptime(dtstart_str, "%Y%m%dT%H%M"))
                datum = dt_local.strftime("%d.%m.%Y")
                startzeit = dt_local.strftime("%H:%M")
                writer.writerow([datum, startzeit, gegner])
                heimspiel_count += 1
            except ValueError:
                continue

print(f"✅ Heimspiele gefunden: {heimspiel_count}")
print(f"✅ CSV gespeichert unter: {csv_path}")
