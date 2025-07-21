import requests
from icalendar import Calendar
from datetime import datetime
from pathlib import Path
import time

ICS_URLS = {
    "1. Bundesliga": "https://www.volleyball-bundesliga.de/iCal/matchSeries/matches.ical?matchSeriesId=776309163&calenderType=ics",
    "2. Bundesliga Nord": "https://www.volleyball-bundesliga.de/iCal/matchSeries/matches.ical?matchSeriesId=776311171&calenderType=ics",
    "Oberliga 2 NRW": "https://ergebnisdienst.volleyball.nrw/iCal/matchSeries/matches.ical?matchSeriesId=95244340&calenderType=ics",
}

def get_ical_data(url, retries=3):
    for attempt in range(retries):
        try:
            return requests.get(url, timeout=30).content
        except requests.exceptions.RequestException:
            print(f"⚠️ Fehler bei Abruf von {url}, Versuch {attempt + 1} von {retries}")
            time.sleep(5)
    raise RuntimeError(f"❌ Fehlgeschlagen nach {retries} Versuchen: {url}")

def main():
    events = []
    for liga, url in ICS_URLS.items():
        print(f"🔄 Lade: {liga}")
        data = get_ical_data(url)
        cal = Calendar.from_ical(data)
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
        f"<tr><td>{d.strftime('%d.%m.%Y')}</td><td>{t}</td><td>{h}</td>"
        f"<td>{a}</td><td>{loc}</td><td>{lg}</td></tr>"
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
<h1>USC Münster – Spielplan Saison 2025/26</h1>
<table><thead>
<tr><th>Datum</th><th>Zeit</th><th>Heim</th><th>Gast</th><th>Ort</th><th>Liga</th></tr>
</thead><tbody>
{rows}
</tbody></table></body></html>"""

    Path("docs").mkdir(exist_ok=True)
    Path("docs/index.html").write_text(html, encoding="utf-8")
    print("✅ HTML-Datei wurde erstellt: docs/index.html")

if __name__ == "__main__":
    main()
