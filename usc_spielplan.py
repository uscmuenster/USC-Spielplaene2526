from pathlib import Path
from datetime import datetime
import pandas as pd
import html
from pytz import timezone
import re

from usc_team_links import build_team_table_overview


def escape_text(value):
    """Wandelt Zellen- bzw. Attributwerte in sauber escapte Strings um."""

    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value)
    if text.strip().lower() == "nan":
        return ""
    return html.escape(text)

# Aktuelle MESZ-Zeit für Anzeige im HTML
mesz_time = datetime.now(timezone("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")
stand_info = f'<p class="text-muted mt-3">Stand: {mesz_time} Uhr</p>'
reload_button = """
<div class="text-center mt-5 mb-3">
  <button class="btn btn-outline-secondary" onclick="location.reload()">🔄 Seite neu laden</button>
</div>
"""

# Verzeichnis
csv_dir = Path("csvdata")

# CSV-Dateien mit zugehörigen USC-Codes
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
    # Kombi-Datum
    "Datum und Uhrzeit": "Datum_Uhrzeit",

    # Alternative Namen (falls andere Exporte kommen)
    "Datum": "Datum",
    "Uhrzeit": "Uhrzeit",
    "Spieltag": "Datum",
    "Uhrzeit Beginn": "Uhrzeit",
    "Beginn": "Uhrzeit",

    # Teams
    "Mannschaft 1": "Heim",
    "Mannschaft 2": "Gast",

    # Offizielle/Orga
    "Schiedsgericht": "SR",
    "Gastgeber": "Gastgeber",

    # Orte/Liga
    "Austragungsort": "Ort",
    "Spielrunde": "Spielrunde",

    # Ergebnis (deine Datei hat "Ergebnis" bereits)
    "Ergebnis": "Ergebnis",
}

dfs = []

for file, team_code in csv_files:
    file_path = csv_dir / file
    if not file_path.exists():
        print(f"⚠️ CSV fehlt, übersprungen: {file_path}")
        continue

    df = pd.read_csv(
        file_path,
        sep=";",
        encoding="cp1252",
        engine="python",      # toleranter Parser
        on_bad_lines="skip"   # defekte Zeilen überspringen
    )
    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)

    # --- Datum/Uhrzeit normalisieren ---
    if "Datum_Uhrzeit" in df.columns and ("Datum" not in df.columns or "Uhrzeit" not in df.columns):
        # Beispielwert: "20.09.2025, 15:00:00"
        parts = df["Datum_Uhrzeit"].astype(str).str.split(",", n=1, expand=True)

        df["Datum"] = parts[0].astype(str).str.strip()
        if parts.shape[1] > 1:
            df["Uhrzeit"] = parts[1].astype(str).str.strip()
        else:
            df["Uhrzeit"] = ""


    required_cols = {"Datum", "Uhrzeit", "Heim", "Gast"}
    missing = required_cols - set(df.columns)

    if missing:
        print(f"⚠️ CSV übersprungen ({file}): fehlende Spalten {missing}")
        continue


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

    # Ergebnis-Funktion: robust + saubere Ganzzahlen
    def get_result(row):
        try:
            if pd.isna(row.get("Satzpunkte")) or str(row["Satzpunkte"]).strip() == "":
                return ""
            satzstand = str(row["Satzpunkte"]).strip()
            saetze = []
            satzspalten = [
                ("Satz 1 - Ballpunkte 1", "Satz 1 - Ballpunkte 2"),
                ("Satz 2 - Ballpunkte 1", "Satz 2 - Ballpunkte 2"),
                ("Satz 3 - Ballpunkte 1", "Satz 3 - Ballpunkte 2"),
                ("Satz 4 - Ballpunkte 1", "Satz 4 - Ballpunkte 2"),
                ("Satz 5 - Ballpunkte 1", "Satz 5 - Ballpunkte 2"),
            ]
            for l, r in satzspalten:
                left = row.get(l, "")
                right = row.get(r, "")
                if pd.notna(left) and pd.notna(right) and str(left).strip() != "" and str(right).strip() != "":
                    try:
                        left_val = int(float(left))
                        right_val = int(float(right))
                        saetze.append(f"{left_val}:{right_val}")
                    except Exception:
                        saetze.append(f"{str(left).strip()}:{str(right).strip()}")
            return f"{satzstand} ({', '.join(saetze)})" if saetze else satzstand
        except Exception:
            return ""

    if "Satzpunkte" in df.columns:
        df["Ergebnis"] = df.apply(get_result, axis=1)

    cols = df.columns.tolist()
    if "Ergebnis" in cols:
        cols.remove("Ergebnis")
        pos = cols.index("Gastgeber") + 1
        cols = cols[:pos] + ["Ergebnis"] + cols[pos:]
        df = df[cols]

    dfs.append(df)
if not dfs:
    raise RuntimeError("❌ Keine gültigen CSV-Daten gefunden – Abbruch")

df_all = pd.concat(dfs, ignore_index=True)

def parse_datum(s):
    try:
        return datetime.strptime(str(s).strip(), "%d.%m.%Y")
    except Exception:
        return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum)
tage_map = {
    "Monday": "Mo", "Tuesday": "Di", "Wednesday": "Mi", "Thursday": "Do",
    "Friday": "Fr", "Saturday": "Sa", "Sunday": "So"
}
df_all["Tag"] = df_all["Datum_DT"].dt.day_name().map(tage_map)
df_all["Woche_Start"] = df_all["Datum_DT"].apply(lambda d: d - pd.to_timedelta(d.weekday(), unit="d"))
df_all["Woche_Ende"] = df_all["Woche_Start"] + pd.to_timedelta(6, unit="d")
df_all["Woche_Label"] = df_all.apply(
    lambda row: f"Mo {row['Woche_Start'].strftime('%d.%m.%Y')} – So {row['Woche_Ende'].strftime('%d.%m.%Y')}",
    axis=1
)

def format_uhrzeit(uhr):
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(str(uhr).strip(), fmt).strftime("%H:%M")
        except Exception:
            pass
    return "???"

df_all["Uhrzeit"] = df_all["Uhrzeit"].apply(format_uhrzeit)

def clean_all_names(row):
    for col in ["Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
        row[col] = replace_usc_names(row[col], row["USC_Team"])
    return row

df_all = df_all.apply(clean_all_names, axis=1)

for col in ["Heim", "Gast", "SR", "Gastgeber"]:
    df_all[col] = df_all[col].str.replace(r'\b(USC-[U\d]+-\d) II\b', r'\1', regex=True)

df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

# 🔴 Änderung 1: Vergangene Spiele mit Ergebnis ohne USC ausfiltern
now = datetime.now(timezone("Europe/Berlin")).replace(tzinfo=None)
df_all = df_all[~(
    (df_all["Ergebnis"].str.strip() != "") &
    (df_all["Datum_DT"] < now) &
    ~(df_all["Heim"].str.contains("USC")) &
    ~(df_all["Gast"].str.contains("USC"))
)]

spielrunden = sorted(df_all["Spielrunde"].dropna().unique())
orte = sorted([o for o in df_all["Ort"].dropna().unique() if "münster" in o.lower()])
teams = sorted(set(t for team in df_all["USC_Team"].dropna() for t in team.split("/")))
usc_team_codes = [team for team in teams if team.startswith("USC")]
wochen = sorted(
    {(row["Woche_Start"], row["Woche_Label"]) for _, row in df_all.iterrows()},
    key=lambda x: x[0]
)

columns_display = [
    "Datum",
    "Uhrzeit",
    "Tag",
    "Heim",
    "Gast",
    "SR",
    "Gastgeber",
    "Ergebnis",
    "Ort",
    "Spielrunde",
]
table_header_html = "".join(f"<th>{col}</th>" for col in columns_display)


def render_cells(row):
    return "".join(f"<td>{escape_text(row.get(col, ''))}</td>" for col in columns_display)

# Tabelle mit mehreren data-team Attributen
table_rows = "\n".join(
    "<tr "
    + f'data-teams="{escape_text(row["USC_Team"])}"'
    + f' data-spielrunde="{escape_text(row["Spielrunde"])}" data-ort="{escape_text(row["Ort"])}"'
    + f' data-week="{row["Woche_Start"].strftime("%Y-%m-%d")}" data-datum="{row["Datum_DT"].strftime("%Y-%m-%d")}">'
    + render_cells(row)
    + "</tr>"
    for _, row in df_all.iterrows()
)


team_tables_html = build_team_table_overview(usc_team_codes)

# HTML-Ausgabe
html_code = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>USC Münster Spielplan 2025/26</title>
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
    @media print {{
      body * {{ visibility: hidden; }}
      #spielplan, #spielplan * {{ visibility: visible; }}
      #spielplan {{ position: absolute; left: 0; top: 0; width: 100%; }}
    }}
  </style>
  <link rel="icon" type="image/png" href="favicon.png">
  <link rel="manifest" href="manifest.webmanifest">
  <meta name="theme-color" content="#008000">
</head>
<body class="p-4">
  <div class="container">
    <h1 class="mb-2">USC Münster – Spielplan 2025/26</h1>
    {stand_info}
    {team_tables_html}
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
            <div class="row g-2 mt-2">
              <div class="col-md-4">
                <label class="form-label">Woche (Mo–So):</label>
                <select class="form-select" id="filterWeek" onchange="filter()">
                  <option value="">Alle</option>
                  {''.join(f"<option value='{w[0].strftime('%Y-%m-%d')}'>{html.escape(w[1])}</option>" for w in wochen)}
                </select>
              </div>
              <div class="col-md-4 d-flex align-items-end" id="togglePastContainer">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" value="1" id="togglePast" onchange="filter()">
                  <label class="form-check-label" for="togglePast">Vergangene Spiele anzeigen</label>
                </div>
              </div>
            </div>
            <div class="mt-3">
              <button class="btn btn-secondary" onclick="resetFilter()">Zurücksetzen</button>
              <button class="btn btn-outline-primary" onclick="window.print()">🖨️ Drucken</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="table-responsive">
      <table class="table table-bordered" id="spielplan">
        <thead>
          <tr>{table_header_html}</tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
    <div class="mt-4">
      <a class="btn btn-success" href="spielplan.csv" download>📥 Gesamten Spielplan als CSV herunterladen</a>
    </div>
    {reload_button}
  </div>
  <script>
    function filter() {{
      const team = document.getElementById("filterTeam").value;
      const runde = document.getElementById("filterRunde").value;
      const ort = document.getElementById("filterOrt").value;
      const week = document.getElementById("filterWeek").value;
      const showPast = document.getElementById("togglePast").checked;
      const pastContainer = document.getElementById("togglePastContainer");
      if (pastContainer) {{
        pastContainer.style.display = week ? "none" : "flex";
      }}
      const now = new Date();
      const cutoff = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 10);
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      document.querySelectorAll("#spielplan tbody tr").forEach(row => {{
        const teamList = (row.dataset.teams || "").split("/");
        const matchTeam = !team || teamList.includes(team);
        const matchRunde = !runde || row.dataset.spielrunde === runde;
        const matchOrt = !ort || row.dataset.ort === ort;
        const matchWeek = !week || row.dataset.week === week;
        const rowDate = row.dataset.datum ? new Date(row.dataset.datum) : null;
        const isRecent = !rowDate || rowDate >= cutoff;
        const isFuture = !rowDate || rowDate >= today;
        const withinTime = week ? true : (showPast ? true : (isFuture || isRecent));
        row.style.display = (matchTeam && matchRunde && matchOrt && matchWeek && withinTime) ? "" : "none";
      }});
    }}
    function resetFilter() {{
      document.getElementById("filterTeam").value = "";
      document.getElementById("filterRunde").value = "";
      document.getElementById("filterOrt").value = "";
      document.getElementById("filterWeek").value = "";
      document.getElementById("togglePast").checked = false;
      filter();
    }}
    document.addEventListener("DOMContentLoaded", filter);
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('service-worker.js')
        .then(reg => console.log('✅ Service Worker registriert:', reg.scope))
        .catch(err => console.warn('❌ Service Worker Fehler:', err));
    }}
  </script>
</body>
</html>
"""

html_code = html_code.replace(
    ".btn-success {",
    """.btn-success {
  background-color: #01a83b !important;
  border-color: #01a83b !important;"""
) 
html_code = html_code.replace( 
    "</style>",
    """h1 { font-size: 1.2rem; margin-bottom: 0.5rem; }
.form-label { font-size: 0.7rem; }
.form-select { font-size: 0.7rem; padding: 0.25rem 0.5rem; }
.btn { font-size: 0.7rem; padding: 0.25rem 0.6rem; }
""" + "</style>"
)

# Standard-HTML erzeugen
Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html_code, encoding="utf-8")
print("✅ index.html erfolgreich erstellt.")

# App-Version mit kleinerer Schrift
html_code_app = html_code.replace("body { font-size: 0.8rem; }", "body { font-size: 0.6rem; }")

# Weitere Schriftgrößen im <style>-Block anpassen
html_code_app = html_code_app.replace(
    "</style>",
    """h1 { font-size: 1rem; margin-bottom: 0.5rem; }
.form-label { font-size: 0.7rem; }
.form-select { font-size: 0.7rem; padding: 0.25rem 0.5rem; }
.btn { font-size: 0.7rem; padding: 0.25rem 0.6rem; }
""" + "</style>"
)

# indexapp.html schreiben
Path("docs/indexapp.html").write_text(html_code_app, encoding="utf-8")
print("✅ indexapp.html erfolgreich erstellt (kleinere Schriftgröße + Filteranpassung).")
