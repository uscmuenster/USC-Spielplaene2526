from pathlib import Path
from datetime import datetime
import pandas as pd

# CSV-Dateien mit Spielplänen
csv_files = [
    "Spielplan_1._Bundesliga_Frauen.csv",
    "Spielplan_2._Bundesliga_Frauen_Nord.csv",
    "Spielplan_Oberliga_2_Frauen.csv",
    "Spielplan_Bezirksklasse_26_Frauen.csv"
]

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]

# Spalten umbenennen
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

dfs = []

for file in csv_files:
    df = pd.read_csv(file, sep=";", encoding="cp1252")
    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# Nur USC-Spiele behalten
def contains_usc(*fields):
    return any(any(usc in str(field) for usc in usc_keywords) for field in fields)

df_all = df_all[df_all.apply(lambda row: contains_usc(row["Heim"], row["Gast"], row["SR"]), axis=1)]

# Datum umwandeln & Tag extrahieren
def parse_datum(datum_str):
    try:
        return datetime.strptime(datum_str, "%d.%m.%Y")
    except:
        return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum)
df_all["Tag"] = df_all["Datum_DT"].dt.strftime("%a").replace({"Sat": "Sa", "Sun": "So"})

# Uhrzeit 00:00 → offen
df_all["Uhrzeit"] = df_all["Uhrzeit"].replace("00:00", "offen")

# Sortieren
df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

# Spalten in gewünschter Reihenfolge
df_result = df_all[[
    "Datum", "Uhrzeit", "Tag",
    "Heim", "Gast", "SR",
    "Gastgeber", "Ort", "Spielrunde"
]]

# HTML-Tabelle erzeugen
html_table = df_result.to_html(index=False, escape=False)

# HTML-Dokument bauen
html = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>USC Münster Spielplan 2025/26</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>USC Münster – Spielplan 2025/26</h1>
  {html_table}
</body>
</html>
"""

# Speichern
Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print("✅ HTML-Datei erfolgreich generiert: docs/index.html")
