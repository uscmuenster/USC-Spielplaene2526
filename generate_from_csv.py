from pathlib import Path
from datetime import datetime
import pandas as pd

# CSV-Dateipfade
csv_files = {
    "1. Bundesliga": "Spielplan_1._Bundesliga_Frauen.csv",
    "2. Bundesliga Nord": "Spielplan_2._Bundesliga_Frauen_Nord.csv",
    "Oberliga 2": "Spielplan_Oberliga_2_Frauen.csv",
    "Bezirksklasse 26": "Spielplan_Bezirksklasse_26_Frauen.csv"
}

# Einheitliche Spaltennamen
rename_map = {
    "Datum": "Datum",
    "Uhrzeit": "Uhrzeit",
    "Heim": "Mannschaft 1",
    "Gast": "Mannschaft 2",
    "SR": "Schiedsgericht",
    "Austragungsort": "Austragungsort",
    "Gastgeber": "Gastgeber",
    "Spielrunde": "Spielrunde"
}

# CSV-Dateien einlesen und verarbeiten
dfs = []
for liga_name, file_path in csv_files.items():
    df = pd.read_csv(file_path, sep=";", encoding="cp1252")
    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)
    df["Liga"] = liga_name
    dfs.append(df)

# Zusammenführen
df_all = pd.concat(dfs, ignore_index=True)

# Datum parsen und Wochentag einfügen
def parse_datum(datum_str):
    try:
        return datetime.strptime(datum_str, "%d.%m.%Y")
    except:
        return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum)
df_all["Wochentag"] = df_all["Datum_DT"].dt.strftime("%a").replace({"Sat": "Sa", "Sun": "So"})

# Uhrzeit "00:00" zu "offen"
df_all["Uhrzeit"] = df_all["Uhrzeit"].replace("00:00", "offen")

# Sortieren
df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

# Spaltenreihenfolge
df_result = df_all[[
    "Datum", "Uhrzeit", "Wochentag",
    "Mannschaft 1", "Mannschaft 2", "Schiedsgericht",
    "Gastgeber", "Austragungsort", "Spielrunde", "Liga"
]]

# HTML erzeugen
html_table = df_result.to_html(index=False, escape=False)
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

# HTML speichern
Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html, encoding="utf-8")
print("✅ HTML-Datei erfolgreich generiert: docs/index.html")
