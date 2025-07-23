from pathlib import Path
from datetime import datetime
import pandas as pd
import requests

# CSV-URLs
csv_urls = [
    "https://www.volleyball-bundesliga.de/servlet/league/PlayingScheduleCsvExport?matchSeriesId=776309163",
    "https://www.volleyball-bundesliga.de/servlet/league/PlayingScheduleCsvExport?matchSeriesId=776311171",
    "https://ergebnisdienst.volleyball.nrw/servlet/league/PlayingScheduleCsvExport?matchSeriesId=95244340",
    "https://ergebnisdienst.volleyball.nrw/servlet/league/PlayingScheduleCsvExport?matchSeriesId=95243632"
]

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]

def download_csv(url):
    r = requests.get(url)
    r.encoding = 'cp1252'  # erwartete Kodierung der Quelle
    if r.status_code == 200:
        return pd.read_csv(pd.compat.StringIO(r.text), sep=";")
    else:
        print(f"⚠️ Fehler beim Download: {url} – Status {r.status_code}")
        return pd.DataFrame()

dfs = []
for url in csv_urls:
    print(f"📥 Lade CSV von: {url}")
    df = download_csv(url)
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# Vereinheitlichung der Spalten und Filter
rename_map = {
    "Datum": "Datum",
    "Uhrzeit": "Uhrzeit",
    "Mannschaft 1": "Heim",
    "Mannschaft 2": "Gast",
    "Schiedsgericht": "SR",
    "Gastgeber": "Gastgeber",
    "Austragungsort": "Ort",
    "Spielrunde": "Spielrunde"
}
df_all.columns = df_all.columns.str.strip()
df_all = df_all.rename(columns=rename_map)

def contains_usc(*fields):
    return any(any(usc in str(f) for usc in usc_keywords) for f in fields)

df_all = df_all[df_all.apply(lambda row: contains_usc(row.get("Heim", ""), row.get("Gast", ""), row.get("SR", "")), axis=1)]

df_all["Datum_DT"] = pd.to_datetime(df_all["Datum"], format="%d.%m.%Y", errors="coerce")
df_all["Tag"] = df_all["Datum_DT"].dt.strftime("%a").replace({"Sat": "Sa", "Sun": "So"})
df_all["Uhrzeit"] = df_all["Uhrzeit"].replace("00:00", "offen")

df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"], na_position="last")

df_result = df_all[[
    "Datum", "Uhrzeit", "Tag",
    "Heim", "Gast", "SR",
    "Gastgeber", "Ort", "Spielrunde"
]]

html_table = df_result.to_html(index=False, escape=False)
html = f"""<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><title>USC Münster Spielplan 2025/26</title>
<style>body{{font-family:Arial,sans-serif;padding:20px}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{border:1px solid #ccc;padding:8px;text-align:left}}th{{background:#f2f2f2}}</style>
</head><body>
<h1>USC Münster – Spielplan 2025/26</h1>
{html_table}
</body>
</html>"""

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print(f"✅ HTML-Datei generiert mit {len(df_result)} Spielen.")
