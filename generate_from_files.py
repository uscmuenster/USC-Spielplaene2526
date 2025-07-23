from icalendar import Calendar
from pathlib import Path
from datetime import datetime
import re

ICS_FILES = {
    "1.BL": "usc1.ics",
    "2.BLN": "usc2.ics",
    "OL 2": "usc3.ics",
    "BK 26": "usc5.ics"
}

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]
all_events = []

# Alle Events aus allen Dateien einlesen
for liga, file_path in ICS_FILES.items():
    with open(file_path, "rb") as f:
        cal = Calendar.from_ical(f.read())
        for vevent in cal.walk("VEVENT"):
            summary = str(vevent.get("SUMMARY", ""))
            start = vevent["DTSTART"].dt
            date = start.date()
            time_str = start.strftime("%H:%M") if isinstance(start, datetime) else "01:00"
            location = str(vevent.get("LOCATION", "–")).strip()

            match = re.search(r"^(.*?)\s*(?:-|vs)\s*(.*?)(?:,|$)", summary)
            if match:
                heim = match.group(1).strip()
                gast = match.group(2).strip()
            else:
                heim = summary.strip()
                gast = ""

            heim = re.sub(r"^[^A-Za-z0-9ÄÖÜäöüß]+|[^A-Za-z0-9ÄÖÜäöüß\- ]+$", "", heim)
            gast = re.sub(r"^[^A-Za-z0-9ÄÖÜäöüß]+|[^A-Za-z0-9ÄÖÜäöüß\- ]+$", "", gast)

            all_events.append({
                "date": date,
                "time": time_str,
                "heim": heim,
                "gast": gast,
                "ort": location,
                "liga": liga,
                "summary": summary
            })

# Nur USC-Spiele
usc_events = [e for e in all_events if any(kw in e["summary"] for kw in usc_keywords)]

# Bemerkungen zuweisen
for i, event in enumerate(usc_events):
    bemerkung = ""
    for other in all_events:
        if other["date"] != event["date"] or other["ort"] != event["ort"]:
            continue
        if other == event:
            continue
        try:
            # Zeiten vergleichen
            t1 = datetime.strptime(event["time"], "%H:%M")
            t2 = datetime.strptime(other["time"], "%H:%M")
            delta = abs((t1 - t2).total_seconds()) / 60
            if delta <= 150:  # max. 2,5 Stunden Abstand
                if t2 > t1 and event["heim"].startswith("USC"):
                    bemerkung = "SR im Spiel danach"
                elif t2 < t1 and event["heim"].startswith("USC"):
                    bemerkung = "SR im Spiel vorher"
        except Exception as e:
            print("❌ Fehler beim Vergleich:", e)
            continue
    event["bemerkung"] = bemerkung

# Nach Datum und Zeit sortieren
usc_events.sort(key=lambda e: (e["date"], e["time"]))

# HTML-Tabellenzeilen bauen
rows = "\n".join(
    f"<tr><td>{e['date'].strftime('%d.%m.%Y')}</td><td>{e['time']}</td><td>{e['heim']}</td><td>{e['gast']}</td><td>{e['ort']}</td><td>{e['liga']}</td><td>{e['bemerkung']}</td></tr>"
    for e in usc_events
)

# HTML schreiben
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
<p>Anzahl gefundener USC-Spiele: {len(usc_events)}</p>
<table><thead>
<tr><th>Datum</th><th>Zeit</th><th>Heim</th><th>Gast</th><th>Ort</th><th>Liga</th><th>Bemerkung</th></tr>
</thead><tbody>
{rows}
</tbody></table></body></html>
"""

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print("✅ HTML-Datei erfolgreich generiert mit", len(usc_events), "USC-Spielen.")