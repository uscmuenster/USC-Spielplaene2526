from icalendar import Calendar
from pathlib import Path
from datetime import datetime

ICS_FILES = {
    "1. Bundesliga": "data/usc1.ics",
    "2. Bundesliga Nord": "data/usc2.ics",
    "Oberliga 2 NRW": "usc3.ics"
}

events = []

for liga, file_path in ICS_FILES.items():
    with open(file_path, "rb") as f:
        cal = Calendar.from_ical(f.read())
        for vevent in cal.walk("VEVENT"):
            start = vevent["DTSTART"].dt
            date = start.date()
            time_str = start.strftime("%H:%M") if isinstance(start, datetime) else "01:00"
            summary = vevent.get("SUMMARY", "–")
            location = vevent.get("LOCATION", "–")
            if " - " in summary:
                home, away = summary.split(" - ", 1)
            else:
                home, away = summary, ""
            events.append((date, time_str, home.strip(), away.strip(), location.strip(), liga))

events.sort(key=lambda e: (e[0], e[1]))

rows = "\n".join(
    f"<tr><td>{d.strftime('%d.%m.%Y')}</td><td>{t}</td><td>{h}</td><td>{a}</td><td>{loc}</td><td>{lg}</td></tr>"
    for d, t, h, a, loc, lg in events
)

html = f"""<!doctype html>
<html lang="de"><head>
<meta charset="utf-8"><title>USC Münster Spielplan 2025/26</title>
<style>
body{{font-family:Arial,sans-serif;padding:20px}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th,td{{border:1px solid #ccc;padding:8px;text-align:left}}
th{{background:#f2f2f2}}
</style></head><body>
<h1>USC Münster – Spielplan aus lokalen ICS-Dateien</h1>
<table><thead>
<tr><th>Datum</th><th>Zeit</th><th>Heim</th><th>Gast</th><th>Ort</th><th>Liga</th></tr>
</thead><tbody>
{rows}
</tbody></table></body></html>
"""

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print("✅ Lokale HTML-Datei erfolgreich generiert.")
