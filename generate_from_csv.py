from pathlib import Path from datetime import datetime import pandas as pd import html import re

CSV-Dateien + Zuordnung

csv_files = [ ("Spielplan_1._Bundesliga_Frauen.csv", "USC Münster", "USC1"), ("Spielplan_2._Bundesliga_Frauen_Nord.csv", "USC Münster II", "USC2"), ("Spielplan_Oberliga_2_Frauen.csv", "USC Münster III", "USC3"), ("Spielplan_Bezirksklasse_26_Frauen.csv", None, None), ("Spielplan_NRW-Liga_wU18.csv", "USC Münster", "U18") ]

rename_map = { "Datum": "Datum", "Uhrzeit": "Uhrzeit", "Mannschaft 1": "Heim", "Mannschaft 2": "Gast", "Schiedsgericht": "SR", "Gastgeber": "Gastgeber", "Austragungsort": "Ort", "Spielrunde": "Spielrunde" }

dfs = []

for file, keyword, team_code in csv_files: df = pd.read_csv(file, sep=";", encoding="cp1252") df.columns = df.columns.str.strip() df = df.rename(columns=rename_map)

# Nur USC-Spiele behalten
usc_keywords = ["usc münster", "usc muenster"]
def contains_usc(row):
    return any(kw in str(row[f]).lower() for f in ["Heim", "Gast", "SR", "Gastgeber"] for kw in usc_keywords)
df = df[df.apply(contains_usc, axis=1)]

# USC-Team bestimmen
def get_usc_team(row):
    text = f"{row['Heim']} {row['Gast']} {row['SR']} {row['Gastgeber']}`.lower()
    if file == "Spielplan_Bezirksklasse_26_Frauen.csv":
        if "usc münster vi" in text:
            return "USC6"
        elif "usc münster v" in text:
            return "USC5"
        else:
            return "USC5/6"
    if team_code == "U18":
        jugend = str(row.get("Spielrunde", ""))[-3:]
        return f"USC-{jugend.upper()}"
    return team_code

df["USC_Team"] = df.apply(get_usc_team, axis=1)

# Namen ersetzen in allen relevanten Spalten
def replace_names(s, team):
    s = str(s)
    replacements = [
        ("USC Münster VI", "USC6"),
        ("USC Münster V", "USC5"),
        ("USC Münster III", "USC3"),
        ("USC Münster II", "USC2"),
        ("USC Münster", team if team.startswith("USC-") else "USC1"),
    ]
    for old, new in replacements:
        s = re.sub(re.escape(old), new, s, flags=re.IGNORECASE)
    return s

for col in ["Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
    df[col] = df.apply(lambda row: replace_names(row[col], row["USC_Team"]), axis=1)

dfs.append(df)

Zusammenführen

df_all = pd.concat(dfs, ignore_index=True)

Datum & Tag

def parse_datum(s): try: return datetime.strptime(s, "%d.%m.%Y") except: return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum) tage_map = { "Monday": "Mo", "Tuesday": "Di", "Wednesday": "Mi", "Thursday": "Do", "Friday": "Fr", "Saturday": "Sa", "Sunday": "So" } df_all["Tag"] = df_all["Datum_DT"].dt.day_name().map(tage_map)

Uhrzeit formatieren

def clean_uhrzeit(u): if u == "00:00:00": return "offen" try: return datetime.strptime(u.strip(), "%H:%M:%S").strftime("%H:%M") except: return u

df_all["Uhrzeit"] = df_all["Uhrzeit"].apply(clean_uhrzeit)

Sortieren

df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

Dropdown-Filter

spielrunden = sorted(df_all["Spielrunde"].dropna().unique()) orte = sorted([o for o in df_all["Ort"].dropna().unique() if "münster" in o.lower()]) teams = sorted(df_all["USC_Team"].dropna().unique())

HTML-Tabelle

table_rows = "\n".join( f"<tr data-team='{html.escape(row['USC_Team'])}' data-spielrunde='{html.escape(row['Spielrunde'])}' data-ort='{html.escape(row['Ort'])}'>" + "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in [ "Datum", "Uhrzeit", "Tag", "Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde" ]) + "</tr>" for _, row in df_all.iterrows() )

HTML-Template

html_code = f"""<!doctype html>

<html lang=\"de\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>USC Münster Spielplan 2025/26</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
  <style>
    th, td {{ white-space: nowrap; }}
    @media print {{
      body * {{ visibility: hidden; }}
      #spielplan, #spielplan * {{ visibility: visible; }}
      #spielplan {{ position: absolute; left: 0; top: 0; width: 100%; }}
    }}
  </style>
</head>
<body class=\"p-4\">
  <div class=\"container\">
    <h1 class=\"mb-4\">USC Münster – Spielplan 2025/26</h1><div class=\"accordion mb-3\" id=\"filterAccordion\">
  <div class=\"accordion-item\">
    <h2 class=\"accordion-header\" id=\"headingFilters\">
      <button class=\"accordion-button\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#filters\" aria-expanded=\"true\">
        Filter anzeigen
      </button>
    </h2>
    <div id=\"filters\" class=\"accordion-collapse collapse show\">
      <div class=\"accordion-body\">
        <div class=\"row g-2\">
          <div class=\"col-md-4\">
            <label class=\"form-label\">USC-Team:</label>
            <select class=\"form-select\" id=\"filterTeam\" onchange=\"filter()\">
              <option value=\"\">Alle</option>
              {''.join(f"<option value='{html.escape(t)}'>{html.escape(t)}</option>" for t in teams)}
            </select>
          </div>
          <div class=\"col-md-4\">
            <label class=\"form-label\">Spielrunde:</label>
            <select class=\"form-select\" id=\"filterRunde\" onchange=\"filter()\">
              <option value=\"\">Alle</option>
              {''.join(f"<option value='{html.escape(r)}'>{html.escape(r)}</option>" for r in spielrunden)}
            </select>
          </div>
          <div class=\"col-md-4\">
            <label class=\"form-label\">Ort (nur Münster):</label>
            <select class=\"form-select\" id=\"filterOrt\" onchange=\"filter()\">
              <option value=\"\">Alle</option>
              {''.join(f"<option value='{html.escape(o)}'>{html.escape(o)}</option>" for o in orte)}
            </select>
          </div>
        </div>
        <div class=\"mt-3\">
          <button class=\"btn btn-secondary\" onclick=\"resetFilter()\">Zurücksetzen</button>
          <button class=\"btn btn-outline-primary\" onclick=\"window.print()\">🖨️ Drucken</button>
        </div>
      </div>
    </div>
  </div>
</div>

<div class=\"table-responsive\">
  <table class=\"table table-bordered table-striped table-hover\" id=\"spielplan\">
    <thead class=\"table-light\">
      <tr><th>Datum</th><th>Uhrzeit</th><th>Tag</th><th>Mannschaft 1</th><th>Mannschaft 2</th><th>SR</th><th>Gastgeber</th><th>Ort</th><th>Spielrunde</th></tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</div>

  </div>  <script>
    function filter() {{
      const team = document.getElementById("filterTeam").value;
      const runde = document.getElementById("filterRunde").value;
      const ort = document.getElementById("filterOrt").value;

      document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
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
  </script>  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script></body>
</html>
"""Speichern

Path("docs").mkdir(exist_ok=True) Path("docs/index.html").write_text(html_code, encoding="utf-8") print("✅ HTML-Datei erfolgreich erstellt.")

