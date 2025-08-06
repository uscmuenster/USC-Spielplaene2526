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

# Datei einlesen
with ics_path.open(encoding="utf-8") as f:
    content = f.read()

# Einzelne Events extrahieren
events = content.split("BEGIN:VEVENT")[1:]

# CSV-Datei schreiben
with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Datum", "Startzeit", "Gegner"])

    for event in events:
        lines = event.splitlines()
        summary_line = next((line for line in lines if line.startswith("SUMMARY:")), "")
        
        # Nur Heimspiele der Uni Baskets Münster
        if summary_line.startswith("SUMMARY:Uni Baskets Münster - "):
            # Gegner extrahieren
            gegner = summary_line.replace("SUMMARY:Uni Baskets Münster - ", "").strip()

            dtstart_line = next((line for line in lines if line.startswith("DTSTART;TZID=Europe/Berlin:")), "")
            if not dtstart_line:
                continue  # Überspringe Events ohne gültiges Startdatum

            dtstart_str = dtstart_line.split(":")[1]
            try:
                # Datum & Zeit in Berlin-Zeitzone
                dt_local = berlin.localize(datetime.strptime(dtstart_str, "%Y%m%dT%H%M"))
                datum = dt_local.strftime("%d.%m.%Y")
                startzeit = dt_local.strftime("%H:%M")
            except ValueError:
                continue  # Ungültiges Datumsformat

            writer.writerow([datum, startzeit, gegner])

print(f"✅ Heimspiele gespeichert in: {csv_path}")
