from pathlib import Path
from datetime import datetime
import pandas as pd
import html
from pytz import timezone
import re

# Aktuelle MESZ-Zeit für Anzeige im HTML
mesz_time = datetime.now(timezone("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")
stand_info = f'<p class="text-muted mt-3">Stand: {mesz_time} MESZ</p>'
reload_button = """
<div class="text-center mt-5 mb-3">
  <button class="btn btn-outline-secondary" onclick="location.reload()">🔄 Seite neu laden</button>
</div>
"""

# Verzeichnisse
csv_dir = Path("csvdata")
baskets_file = Path("csv_Baskets/Baskets_2526_Heimspiele.csv")

# USC-Dateien mit zugehörigen Team-Codes
csv_files = [
    ("Spielplan_1._Bundesliga_Frauen.csv", "USC1"),
    ("Spielplan_2._Bundesliga_Frauen_Nord.csv", "USC2"),
    ("Spielplan_Oberliga_2_Frauen.csv", "USC3"),
    ("Spielplan_Bezirksliga_14_Frauen.csv", "USC4"),
    ("Spielplan_NRW-Liga_wU14.csv", "USC-U14-1"),
    ("Spielplan_NRW-Liga_wU16.csv", "USC-U16-1"),
    ("Spielplan_NRW-Liga_wU18.csv", "USC-U18"),
    ("Spielplan_Oberliga_5_wU14.csv", "USC-U14-2"),
    ("Spielplan_Oberliga_5_wU16.csv", "USC-U16-2"),
    ("Spielplan_Oberliga_6_wU13.csv", "USC-U13"),
    ("Spielplan_Bezirksklasse_26_Frauen.csv", None),
    ("Spielplan_Kreisliga_Muenster_Frauen.csv", None),
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

# 🟩 USC CSV-Dateien verarbeiten
for file, team_code in csv_files:
    file_path = csv_dir / file
    df = pd.read_csv(file_path, sep=";", encoding="cp1252")
    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)

    if "Ergebnis" not in df.columns:
        df["Ergebnis"] = ""

    def contains_usc(row):
        return any(usc.lower() in str(row[f]).lower() for f in ["Heim", "Gast", "SR", "Gastgeber"] for usc in usc_keywords)

    df = df[df.apply(contains_usc, axis=1)]

    def get_usc_team(row):
        text = f"{row['Heim']} {row['Gast']} {row['SR']} {row['Gastgeber']}".lower()
        teams = []
        if file == "Spielplan_Bezirksklasse_26_Frauen.csv":
            if re.search(r"\busc münster vi\b", text):
                teams.append("USC6")
            if re.search(r"\busc münster v\b", text):
                teams.append("USC5")
            return "/".join(teams)
        if file == "Spielplan_Kreisliga_Muenster_Frauen.csv":
            if re.search(r"\busc münster viii\b", text):
                teams.append("USC8")
            if re.search(r"\busc münster vii\b", text):
                teams.append("USC7")
            return "/".join(teams)
        return team_code

    df["USC_Team"] = df.apply(get_usc_team, axis=1)

    def replace_usc_names(s, team):
        s = str(s)
        global_replacements = [
            ("USC Münster VIII", "USC8"),
            ("USC Münster VII", "USC7"),
            ("USC Münster VI",  "USC6"),
            ("USC Münster V",   "USC5"),
            ("USC Münster IV",  "USC4"),
            ("USC Münster III", "USC3"),
            ("USC Münster II",  "USC2"),
            ("USC Münster",     "USC1"),
        ]
        team_specific = {
            "USC-U14-1": [("USC1", "USC-U14-1")],
            "USC-U14-2": [("USC2", "USC-U14-2")],
            "USC-U16-1": [("USC1", "USC-U16-1")],
            "USC-U16-2": [("USC2", "USC-U16-2")],
            "USC-U18":   [("USC1", "USC-U18")],
            "USC-U13":   [("USC1", "USC-U13")],
        }
        for old, new in global_replacements:
            s = s.replace(old, new)
        for old, new in team_specific.get(team, []):
            s = s.replace(old, new)
        return s

    for col in ["Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
        df[col] = df.apply(lambda row: replace_usc_names(row[col], row["USC_Team"]), axis=1)

    def get_result(row):
        try:
            if pd.isna(row.get("S")) or str(row["S"]).strip() == "":
                return ""
            satzstand = f"{row['S']}:{row['U']}"
            saetze = []
            satzspalten = [("V", "X"), ("Z", "AB"), ("AD", "AF"), ("AH", "AJ"), ("AL", "AN")]
            for l, r in satzspalten:
                left = str(row.get(l, "")).strip()
                right = str(row.get(r, "")).strip()
                if left and right and left.lower() != 'nan' and right.lower() != 'nan':
                    saetze.append(f"{left}:{right}")
            return f"{satzstand} ({', '.join(saetze)})" if saetze else satzstand
        except:
            return ""

    if all(col in df.columns for col in ["S", "U", "V", "X"]):
        df["Ergebnis"] = df.apply(get_result, axis=1)

    cols = df.columns.tolist()
    if "Ergebnis" in cols:
        cols.remove("Ergebnis")
        pos = cols.index("Gastgeber") + 1
        cols = cols[:pos] + ["Ergebnis"] + cols[pos:]
        df = df[cols]

    dfs.append(df)

# 🟧 Baskets CSV-Datei integrieren
df_baskets = pd.read_csv(baskets_file)
df_baskets["Heim"] = "Uni Baskets Münster"
df_baskets["Ort"] = "Sporthalle Berg Fidel (48153 Münster)"
df_baskets["Spielrunde"] = "Basketball Pro A"
df_baskets["SR"] = ""
df_baskets["Gastgeber"] = ""
df_baskets["Ergebnis"] = ""
df_baskets["USC_Team"] = "Baskets"
df_baskets = df_baskets.rename(columns={"Startzeit": "Uhrzeit", "Gegner": "Gast"})
df_baskets["Datum"] = df_baskets["Datum"].str.strip()
df_baskets["Uhrzeit"] = df_baskets["Uhrzeit"].str.strip()
df_baskets["Datum_DT"] = pd.to_datetime(df_baskets["Datum"], format="%d.%m.%Y", errors="coerce")
tage_map = {
    "Monday": "Mo", "Tuesday": "Di", "Wednesday": "Mi", "Thursday": "Do",
    "Friday": "Fr", "Saturday": "Sa", "Sunday": "So"
}
df_baskets["Tag"] = df_baskets["Datum_DT"].dt.day_name().map(tage_map)
df_baskets = df_baskets[[
    "Datum", "Uhrzeit", "Tag", "Heim", "Gast", "SR", "Gastgeber",
    "Ergebnis", "Ort", "Spielrunde", "Datum_DT", "USC_Team"
]]
dfs.append(df_baskets)

# 🔷 Gesamtdaten zusammenführen
df_all = pd.concat(dfs, ignore_index=True)
df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

# 🟦 HTML-Tabellenzeilen erzeugen
table_rows = "\n".join(
    "<tr " +
    f'data-teams="{html.escape(row["USC_Team"])}"' +
    f' data-spielrunde="{html.escape(row["Spielrunde"])}" data-ort="{html.escape(row["Ort"])}">' +
    "".join(f"<td>{html.escape(str(row.get(col, '')))}</td>" for col in [
        "Datum", "Uhrzeit", "Tag", "Heim", "Gast", "SR", "Gastgeber", "Ergebnis", "Ort", "Spielrunde"
    ]) + "</tr>"
    for _, row in df_all.iterrows()
)

# 🔷 Teams, Orte, Spielrunden extrahieren
spielrunden = sorted(df_all["Spielrunde"].dropna().unique())
orte = sorted([o for o in df_all["Ort"].dropna().unique() if "münster" in o.lower()])
teams = sorted(set(t for team in df_all["USC_Team"].dropna() for t in team.split("/")))

# HTML-Seite zusammenbauen
html_code = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>USC & Baskets Spielplan 2025/26</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ font-size: 0.8rem; }}
    th, td {{ white-space: nowrap; }}
    table tr {{ background-color: white; }}
    thead th {{ background-color: #f2f2f2 !important; color: #000; }}
    .accordion-button {{ background-color: #96d696 !important; }}
    #filters {{ background-color: #96d696 !important; }}
    #filters select, #filters label {{
      color: #000000;
      border-color: #96d696;
    }}
    .form-select:focus {{
      border-color: #28a745;
      box-shadow: 0 0 0 0.25rem rgba(40,167,69,.25);
    }}
  </style>
</head>
<body class="p-4">
  <div class="container">
    <h1 class="mb-2">USC & Baskets – Spielplan 2025/26</h1>
    {stand_info}
    <!-- FILTER, TABELLE, BUTTONS etc. -->
    <div class="table-responsive">
      <table class="table table-bordered" id="spielplan">
        <thead>
          <tr><th>Datum</th><th>Uhrzeit</th><th>Tag</th><th>Heim</th><th>Gast</th><th>SR</th><th>Gastgeber</th><th>Ergebnis</th><th>Ort</th><th>Spielrunde</th></tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
    {reload_button}
  </div>
  <script>
    function filter() {{
      const team = document.getElementById("filterTeam").value;
      const runde = document.getElementById("filterRunde").value;
      const ort = document.getElementById("filterOrt").value;
      document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
        const teamList = (row.dataset.teams || "").split("/");
        const matchTeam = !team || teamList.includes(team);
        const matchRunde = !runde || row.dataset.spielrunde === runde;
        const matchOrt = !ort || row.dataset.ort === ort;
        row.style.display = (matchTeam && matchRunde && matchOrt) ? "" : "none";
      }});
    }}
    function resetFilter() {{
      document.getElementById("filterTeam").value = "";
      document.getElementById("filterRunde").value = "";
      document.getElementById("filterOrt").value = "";
      filter();
    }}
  </script>
</body>
</html>
"""

# 🟩 HTML-Datei schreiben
Path("docs").mkdir(exist_ok=True)
Path("docs/index_trainer.html").write_text(html_code, encoding="utf-8")
print("✅ index_trainer.html erfolgreich erstellt.")
