from pathlib import Path
from datetime import datetime
import pandas as pd
import os

from schedule_utils import load_csv_robust, normalize_schedule_datetime, get_datetime_sort_columns


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
    "Datum und Uhrzeit": "Datum_Uhrzeit",
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

for file, team_code in csv_files:
    file_path = csv_dir / file
    df = load_csv_robust(file_path)
    df.columns = df.columns.str.strip()
    print(f"🔎 {file}: {df.columns.tolist()}")
    df = df.rename(columns=rename_map)
    df = normalize_schedule_datetime(df)

    def contains_usc(row):
        return any(usc.lower() in str(row[f]).lower() for f in ["Heim", "Gast", "SR", "Gastgeber"] for usc in usc_keywords)

    df = df[df.apply(contains_usc, axis=1)]

    def get_usc_team(row):
        text = f"{row['Heim']} {row['Gast']} {row['SR']} {row['Gastgeber']}".lower()
        if file == "Spielplan_Bezirksklasse_26_Frauen.csv":
            if "usc münster vi" in text:
                return "USC6"
            elif "usc münster v" in text:
                return "USC5"
            else:
                return "USC5/6"
        if file == "Spielplan_Kreisliga_Muenster_Frauen.csv":
            if "usc münster viii" in text:
                return "USC8"
            elif "usc münster vii" in text:
                return "USC7"
            elif "usc münster" in text:
                return "USC7/8"
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

    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

print("📊 Anzahl Spiele im df_all:", len(df_all))
print("🔍 Spalten:", df_all.columns.tolist())

def parse_datum(s):
    try:
        return datetime.strptime(s, "%d.%m.%Y")
    except:
        return pd.NaT

df_all["Datum_DT"] = df_all["Datum"].apply(parse_datum)
df_all = normalize_schedule_datetime(df_all)
tage_map = {
    "Monday": "Mo", "Tuesday": "Di", "Wednesday": "Mi", "Thursday": "Do",
    "Friday": "Fr", "Saturday": "Sa", "Sunday": "So"
}
df_all["Tag"] = df_all["Datum_DT"].dt.day_name().map(tage_map)

def format_uhrzeit(uhr):
    if uhr == "00:00:00":
        return "???"
    try:
        return datetime.strptime(uhr, "%H:%M:%S").strftime("%H:%M")
    except:
        return uhr

df_all["Uhrzeit"] = df_all["Uhrzeit"].apply(format_uhrzeit)

# Korrektur: "USC-U14-2 II" → "USC-U14-2"
for col in ["Heim", "Gast", "SR", "Gastgeber"]:
    df_all[col] = df_all[col].str.replace(r'\b(USC-[U\d]+-\d) II\b', r'\1', regex=True)

# Sortierung
sort_cols = get_datetime_sort_columns(df_all)
if sort_cols:
    df_all = df_all.sort_values(by=sort_cols)


# Prüfe DataFrame
print(f"🔍 Anzahl Zeilen: {len(df_all)}")
print(f"📄 Spalten: {df_all.columns.tolist()}")
print("📁 Aktuelles Arbeitsverzeichnis:", os.getcwd())

# Inhalt des Ordners anzeigen
print("📂 Ordnerinhalt:", os.listdir())

# Speicherort festlegen
csv_path = Path("docs/spielplan.csv")

# Versuche, die Datei zu schreiben
try:
    df_all.to_csv(csv_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"✅ CSV-Datei erfolgreich gespeichert unter: {csv_path.resolve()}")
except Exception as e:
    print("❌ Fehler beim Schreiben der CSV-Datei:", e)