from icalendar import Calendar
from pathlib import Path
from datetime import datetime
import re

# Lokale .ics-Dateien für die Ligen
ICS_FILES = {
    "1.BL": "usc1.ics",
    "2.BLN": "usc2.ics",
    "OL2": "usc3.ics",
    "BK26": "usc5.ics"
}

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]
all_events = []

# Schritt 1: Alle Events einlesen (auch Nicht-USC-Spiele)
for liga, file_path in ICS_FILES.items():
    with open(file_path, "rb") as f:
        cal = Calendar.from_ical(f.read())
        for vevent in cal.walk("VEVENT"):
            summary = str(vevent.get("SUMMARY", ""))
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

            # Unerwünschte Zeichen entfernen
            heim = re.sub(r"^[^A-Za-z0-9ÄÖÜäöüß\- ]+|[^A-Za-z0-9ÄÖÜäöüß\- ]+$", "", heim)
            gast = re.sub(r"^[^A-Za-z0-9ÄÖÜäöüß\- ]+|[^A-Za-z0-9ÄÖÜäöüß\- ]+$", "", gast)

            all_events.append({
                "date": date,
                "time": time_str,
                "heim": heim,
                "gast": gast,
                "location": location.strip(),
                "liga": liga,
                "summary": summary
            })

# Schritt 2: Sortieren nach Datum + Uhrzeit
all_events.sort(key=lambda e: (e["date"], e["time"]))

# Schritt 3: Nur USC-Spiele extrahieren + Bemerkung setzen
usc_events = []

for idx, event in enumerate(all_events):
    if not any(kw in event["summary"] for kw in usc_keywords):
        continue

    bemerkung = ""

    # Spiel davor prüfen
    if idx > 0:
        prev = all_events[idx - 1]
        if (prev["date"] == event["date"] and
            prev["location"] == event["location"]):
            if event["heim"] in usc_keywords:
                bemerkung = "SR im Spiel vorher"

    # Spiel danach prüfen
    if idx < len(all_events) - 1:
        nxt = all_events[idx + 1]
        if (nxt["date"] == event["date"] and
            nxt["location"] == event["location"]):
            if event["heim"] in usc_keywords:
                bemerkung = "SR im Spiel danach"

    usc_events.append((
        event["date"],
        event["time"],
        event["heim"],
        event["gast"],
        event["location"],
        bemerkung,
        event["liga"]
    ))

# HTML-Tabelle generieren
rows = "\n".join(
    f"<tr><td>{d.strftime('%d.%m.%Y')}</td><td>{t}</td><td>{h}</td><td>{g}</td><td>{loc}</td><td>{bem}</td><td>{lg}</td></tr>"
    for d, t, h, g, loc, bem, lg in usc_events
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
<tr><th>Datum</th><th>Zeit</th><th>Heim</th><th>Gast</th><th>Ort</th><th>Bemerkung</th><th>Liga</th></tr>
</thead><tbody>
{rows}
</tbody></table></body></html>
"""

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print("✅ HTML-Datei mit Bemerkungen erfolgreich erstellt.")
