from icalendar import Calendar
from pathlib import Path
from datetime import datetime
import re

# Lokale .ics-Dateien für die Ligen
ICS_FILES = {
    "1. Bundesliga": "1. Bundesliga Frauen.ics"
    "Oberliga 2 NRW": "usc3.ics"
}

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]
events = []

for liga, file_path in ICS_FILES.items():
    with open(file_path, "rb") as f:
        cal = Calendar.from_ical(f.read())
        for vevent in cal.walk("VEVENT"):
            summary = str(vevent.get("SUMMARY", ""))
            if not any(kw in summary for kw in usc_keywords):
                continue  # Nur USC-Spiele berücksichtigen

            start = vevent["DTSTART"].dt
            date = start.date()
            time_str = start.strftime("%H:%M") if isinstance(start, datetime) else "01:00"
            location = str(vevent.get("LOCATION", "–"))

            # Heim und Gast extrahieren mit Regex
            match = re.search(r"^(.*?)\s*(?:-|vs)\s*(.*?)(?:,|$)", summary)
            if match:
                heim = match.group(1).strip()
                gast = match.group(2).strip()
            else:
                heim = summary.strip()
                gast = ""
                
            # Unerwünschte Zeichen (wie ".", ",", Leerzeichen) am Rand entfernen
            heim = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9ÄÖÜäöüß\- ]+$", "", heim)
            gast = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9ÄÖÜäöüß\- ]+$", "", gast)

            events.append((date, time_str, heim, gast, location.strip(), liga))

# Nach Datum und Uhrzeit sortieren
events.sort(key=lambda e: (e[0], e[1]))

# HTML-Tabelle generieren
rows = "\n".join(
    f"<tr><td>{d.strftime('%d.%m.%Y')}</td><td>{t}</td><td>{h}</td><td>{g}</td><td>{loc}</td><td>{lg}</td></tr>"
    for d, t, h, g, loc, lg in events
)

# HTML-Dokument schreiben
html = f"""<!doctype html>
<html lang="de"><head>
<meta charset="utf-8"><title>USC Münster Spielplan 2025/26</title>
<style>
body{{font-family:Arial,sans-serif;padding:20px}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left}}
th{{background:#f2f2f2}}
</style></head><body>
<h1>USC Münster – Spielplan 2025/26</h1>
<table><thead>
<tr><th>Datum</th><th>Zeit</th><th>Heim</th><th>Gast</th><th>Ort</th><th>Liga</th></tr>
</thead><tbody>
{rows}
</tbody></table></body></html>
"""

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print("✅ HTML-Datei nur mit USC-Spielen erfolgreich generiert.")
