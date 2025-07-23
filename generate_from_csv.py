from pathlib import Path
from datetime import datetime
import pandas as pd
import html

# CSV-Dateien
csv_files = [
    "Spielplan_1._Bundesliga_Frauen.csv",
    "Spielplan_2._Bundesliga_Frauen_Nord.csv",
    "Spielplan_Oberliga_2_Frauen.csv",
    "Spielplan_Bezirksklasse_26_Frauen.csv",
    "Spielplan_NRW-Liga_wU18.csv"
]

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]

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

# Nur USC-Spiele
def contains_usc(*fields):
    return any(any(usc in str(field) for usc in usc_keywords) for field in fields)

df_all = df_all[df_all.apply(lambda row: contains_usc(row["Heim"], row["Gast"], row["SR"]), axis=1)]

# Datum und Tag
def parse_datum(datum_str):
    try:
        return datetime.strptime(datum_str, "%d.%m.%Y")
    except:
        return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum)
df_all["Tag"] = df_all["Datum_DT"].dt.strftime("%a").replace({"Sat": "Sa", "Sun": "So"})

# Uhrzeit
df_all["Uhrzeit"] = df_all["Uhrzeit"].replace("00:00", "offen")

# Sortieren
df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

# Dropdown-Optionen
spielrunden = sorted(df_all["Spielrunde"].dropna().unique())
orte = sorted(df_all["Ort"].dropna().unique())

# HTML-Zeilen generieren
table_rows = "\n".join(
    f"<tr data-gastgeber='{html.escape(row['Gastgeber'])}' data-spielrunde='{html.escape(row['Spielrunde'])}' data-ort='{html.escape(row['Ort'])}'>" +
    "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in [
        "Datum", "Uhrzeit", "Tag", "Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"
    ]) + "</tr>"
    for _, row in df_all.iterrows()
)

# HTML-Seite aufbauen
html_code = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>USC Münster Spielplan 2025/26</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background: #f2f2f2; }}
    select, button {{ margin-right: 10px; padding: 5px; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>
  <h1>USC Münster – Spielplan 2025/26</h1>

  <div>
    <strong>Filter:</strong>
    <button onclick="filterHeim()">USC als Gastgeber</button>
    <select id="filterRunde" onchange="filterRunde()">
      <option value="">Spielrunde wählen</option>
      {''.join(f"<option value='{html.escape(r)}'>{html.escape(r)}</option>" for r in spielrunden)}
    </select>
    <select id="filterOrt" onchange="filterOrt()">
      <option value="">Ort wählen</option>
      {''.join(f"<option value='{html.escape(o)}'>{html.escape(o)}</option>" for o in orte)}
    </select>
    <button onclick="resetFilter()">Zurücksetzen</button>
  </div>

  <table id="spielplan">
    <thead>
      <tr><th>Datum</th><th>Uhrzeit</th><th>Tag</th><th>Mannschaft 1</th><th>Mannschaft 2</th><th>SR</th><th>Gastgeber</th><th>Ort</th><th>Spielrunde</th></tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>

<script>
function filterHeim() {{
  document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
    row.classList.toggle("hidden", !row.dataset.gastgeber.includes("USC Münster"));
  }});
}}

function filterRunde() {{
  let runde = document.getElementById("filterRunde").value;
  document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
    row.classList.toggle("hidden", runde && row.dataset.spielrunde !== runde);
  }});
}}

function filterOrt() {{
  let ort = document.getElementById("filterOrt").value;
  document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
    row.classList.toggle("hidden", ort && row.dataset.ort !== ort);
  }});
}}

function resetFilter() {{
  document.getElementById("filterRunde").value = "";
  document.getElementById("filterOrt").value = "";
  document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
    row.classList.remove("hidden");
  }});
}}
</script>

</body>
</html>
"""

# Speichern
Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html_code, encoding="utf-8")
print("✅ HTML-Datei mit interaktiven Filtern erstellt.")
