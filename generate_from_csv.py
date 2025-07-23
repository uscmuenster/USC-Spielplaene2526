from pathlib import Path
from datetime import datetime
import pandas as pd
import html

# CSV-Dateien mit zugewiesenem USC-Team
csv_files = [
    ("Spielplan_1._Bundesliga_Frauen.csv", "USC1"),
    ("Spielplan_2._Bundesliga_Frauen_Nord.csv", "USC2"),
    ("Spielplan_Oberliga_2_Frauen.csv", "USC3"),
    ("Spielplan_Bezirksklasse_26_Frauen.csv", "USC5/6"),
    ("Spielplan_NRW-Liga_wU18.csv", "USC-U18")
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

for file, usc_code in csv_files:
    df = pd.read_csv(f"/mnt/{file}", sep=";", encoding="cp1252")
    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)

    def team_involvement(row):
        return any(
            pd.notna(row.get(field)) and any(usc in str(row[field]) for usc in usc_keywords)
            for field in ["Heim", "Gast", "SR"]
        )

    df = df[df.apply(team_involvement, axis=1)]

    # USC-Team bestimmen
    def assign_usc_team(row):
        name = f"{row['Heim']} {row['Gast']} {row['SR']}"
        if usc_code == "USC5/6":
            if "V" in name:
                return "USC5"
            elif "VI" in name:
                return "USC6"
            return "USC5/6"
        return usc_code

    df["USC_Team"] = df.apply(assign_usc_team, axis=1)
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# Datum & Tag
def parse_datum(datum_str):
    try:
        return datetime.strptime(datum_str, "%d.%m.%Y")
    except:
        return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum)
df_all["Tag"] = df_all["Datum_DT"].dt.strftime("%a").replace({"Sat": "Sa", "Sun": "So"})

df_all["Uhrzeit"] = df_all["Uhrzeit"].replace("00:00", "offen")
df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

spielrunden = sorted(df_all["Spielrunde"].dropna().unique())
orte = sorted([o for o in df_all["Ort"].dropna().unique() if "münster" in o.lower()])
teams = sorted(df_all["USC_Team"].dropna().unique())

table_rows = "\n".join(
    f"<tr data-team='{html.escape(row['USC_Team'])}' data-spielrunde='{html.escape(row['Spielrunde'])}' data-ort='{html.escape(row['Ort'])}'>" +
    "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in [
        "Datum", "Uhrzeit", "Tag", "Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"
    ]) + "</tr>"
    for _, row in df_all.iterrows()
)

html_code = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>USC Münster Spielplan 2025/26</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    .hidden {{ display: none; }}
    th, td {{ white-space: nowrap; }}
  </style>
</head>
<body class="p-4">
  <div class="container">
    <h1 class="mb-4">USC Münster – Spielplan 2025/26</h1>

    <div class="accordion mb-3" id="filterAccordion">
      <div class="accordion-item">
        <h2 class="accordion-header" id="headingFilters">
          <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#filters" aria-expanded="true">
            Filter anzeigen
          </button>
        </h2>
        <div id="filters" class="accordion-collapse collapse show" aria-labelledby="headingFilters">
          <div class="accordion-body">
            <div class="row g-2">
              <div class="col-md-4">
                <label class="form-label">USC-Team:</label>
                <select class="form-select" id="filterTeam" onchange="filter()">
                  <option value="">Alle</option>
                  {''.join(f"<option value='{html.escape(t)}'>{html.escape(t)}</option>" for t in teams)}
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label">Spielrunde:</label>
                <select class="form-select" id="filterRunde" onchange="filter()">
                  <option value="">Alle</option>
                  {''.join(f"<option value='{html.escape(r)}'>{html.escape(r)}</option>" for r in spielrunden)}
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label">Ort (nur Münster):</label>
                <select class="form-select" id="filterOrt" onchange="filter()">
                  <option value="">Alle</option>
                  {''.join(f"<option value='{html.escape(o)}'>{html.escape(o)}</option>" for o in orte)}
                </select>
              </div>
            </div>
            <button class="btn btn-secondary mt-3" onclick="resetFilter()">Zurücksetzen</button>
          </div>
        </div>
      </div>
    </div>

    <div class="table-responsive">
      <table class="table table-bordered table-striped table-hover">
        <thead class="table-light">
          <tr><th>Datum</th><th>Uhrzeit</th><th>Tag</th><th>Mannschaft 1</th><th>Mannschaft 2</th><th>SR</th><th>Gastgeber</th><th>Ort</th><th>Spielrunde</th></tr>
        </thead>
        <tbody id="spielplan">
          {table_rows}
        </tbody>
      </table>
    </div>
  </div>

  <script>
    function filter() {{
      const team = document.getElementById("filterTeam").value;
      const runde = document.getElementById("filterRunde").value;
      const ort = document.getElementById("filterOrt").value;

      document.querySelectorAll("#spielplan tr").forEach(row => {{
        const show = (!team || row.dataset.team === team) &&
                     (!runde || row.dataset.spielrunde === runde) &&
                     (!ort || row.dataset.ort === ort);
        row.style.display = show ? "" : "none";
      }});
    }}

    function resetFilter() {{
      document.getElementById("filterTeam").value = "";
      document.getElementById("filterRunde").value = "";
      document.getElementById("filterOrt").value = "";
      filter();
    }}
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html_code, encoding="utf-8")