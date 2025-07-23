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
orte = sorted([o for o in df_all["Ort"].dropna().unique() if "münster" in o.lower()])

# HTML-Zeilen
table_rows = "\n".join(
    f"<tr data-gastgeber='{html.escape(row['Gastgeber'])}' data-spielrunde='{html.escape(row['Spielrunde'])}' data-ort='{html.escape(row['Ort'])}'>" +
    "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in [
        "Datum", "Uhrzeit", "Tag", "Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"
    ]) + "</tr>"
    for _, row in df_all.iterrows()
)

# HTML
html_code = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>USC Münster Spielplan 2025/26</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    .hidden {{ display: none; }}
    table {{ margin-top: 20px; }}
  </style>
</head>
<body class="p-3">
  <h1 class="mb-4">USC Münster – Spielplan 2025/26</h1>

  <div class="accordion mb-3" id="filterAccordion">
    <div class="accordion-item">
      <h2 class="accordion-header" id="headingFilters">
        <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseFilters" aria-expanded="true" aria-controls="collapseFilters">
          Filteroptionen anzeigen
        </button>
      </h2>
      <div id="collapseFilters" class="accordion-collapse collapse show" aria-labelledby="headingFilters" data-bs-parent="#filterAccordion">
        <div class="accordion-body">
          <div class="mb-2">
            <button class="btn btn-outline-primary me-2" onclick="filterHeim()">USC als Gastgeber</button>
            <select id="filterRunde" class="form-select d-inline w-auto me-2" onchange="filterRunde()">
              <option value="">Spielrunde wählen</option>
              {''.join(f"<option value='{html.escape(r)}'>{html.escape(r)}</option>" for r in spielrunden)}
            </select>
            <select id="filterOrt" class="form-select d-inline w-auto me-2" onchange="filterOrt()">
              <option value="">Ort wählen</option>
              {''.join(f"<option value='{html.escape(o)}'>{html.escape(o)}</option>" for o in orte)}
            </select>
            <button class="btn btn-outline-secondary" onclick="resetFilter()">Zurücksetzen</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="table-responsive">
    <table class="table table-bordered table-striped" id="spielplan">
      <thead class="table-light">
        <tr>
          <th>Datum</th><th>Uhrzeit</th><th>Tag</th>
          <th>Mannschaft 1</th><th>Mannschaft 2</th><th>SR</th>
          <th>Gastgeber</th><th>Ort</th><th>Spielrunde</th>
        </tr>
      </thead>
      <tbody>
        {table_rows}
      </tbody>
    </table>
  </div>

  <script>
    function filterHeim() {{
      document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
        row.classList.toggle("hidden", !(row.cells[3].textContent.includes("USC") || row.dataset.gastgeber.includes("USC")));
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
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Speichern
Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html_code, encoding="utf-8")
print("✅ HTML-Datei mit Bootstrap, Akkordeon und Filtern erstellt.")
