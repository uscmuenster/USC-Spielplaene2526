from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from pytz import timezone

# Verzeichnis mit den CSV-Dateien
csv_dir = Path("csvdata")
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

for file, team_code in csv_files:
    file_path = csv_dir / file
    if not file_path.exists():
        continue

    df = pd.read_csv(
        file_path,
        sep=";",
        encoding="cp1252",
        engine="python",
        on_bad_lines="skip"
    )

    df.columns = df.columns.astype(str).str.strip()
    df = df.rename(columns=rename_map)

    def contains_usc(row):
        return any(usc.lower() in str(row[f]).lower()
                   for f in ["Heim", "Gast", "SR", "Gastgeber"]
                   for usc in usc_keywords)

    df = df[df.apply(contains_usc, axis=1)]
    df["USC_Team"] = team_code

    # Namen bereinigen
    def replace_usc_names(s, team):
        s = str(s)
        replacements = [
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
        for old, new in replacements:
            s = s.replace(old, new)
        for old, new in team_specific.get(team, []):
            s = s.replace(old, new)
        return s

    for col in ["Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
        df[col] = df.apply(lambda row: replace_usc_names(row[col], row["USC_Team"]), axis=1)

    # Datum/Uhrzeit parsen
    def parse_dt(datum, uhrzeit):
        try:
            dt = datetime.strptime(f"{datum} {uhrzeit}", "%d.%m.%Y %H:%M:%S")
        except:
            try:
                dt = datetime.strptime(f"{datum} {uhrzeit}", "%d.%m.%Y %H:%M")
            except:
                return pd.NaT
        return dt

    df["DATETIME"] = df.apply(lambda row: parse_dt(row["Datum"], row["Uhrzeit"]), axis=1)
    df = df.dropna(subset=["DATETIME"])

    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)

# Filter: USC-Team ist Gastgeber UND Heim oder Gast ist USC-Team
def is_hosting_and_playing(row):
    gastgeber = str(row.get("Gastgeber", "")).strip()
    heim = str(row.get("Heim", "")).strip()
    gast = str(row.get("Gast", "")).strip()
    return gastgeber.startswith("USC") and (heim.startswith("USC") or gast.startswith("USC"))

df_all = df_all[df_all.apply(is_hosting_and_playing, axis=1)].sort_values(by="DATETIME")

# ICS-Datei erzeugen
def generate_ics(df, output_file="docs/usc_spielplan.ics"):
    berlin = timezone("Europe/Berlin")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//USC Münster//Spielplan//DE\n")
        for _, row in df.iterrows():
            start_dt = berlin.localize(row["DATETIME"])
            end_dt = start_dt + timedelta(hours=2)
            dtstart_utc = start_dt.astimezone(timezone("UTC")).strftime("%Y%m%dT%H%M%SZ")
            dtend_utc = end_dt.astimezone(timezone("UTC")).strftime("%Y%m%dT%H%M%SZ")
            dtstamp_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

            summary = f"{row['Heim']} vs. {row['Gast']}"
            location = row.get("Ort", "tbd").replace("\n", " ").strip()
            description = f"Gastgeber: {row.get('Gastgeber', '').strip()},\\n  {row.get('Spielrunde', '').strip()}"
            uid = f"{dtstart_utc}-{row['Heim'][:5]}-vs-{row['Gast'][:5]}@uscmuenster.de".replace(" ", "")

            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{dtstamp_utc}\n")
            f.write(f"DTSTART:{dtstart_utc}\n")
            f.write(f"DTEND:{dtend_utc}\n")
            f.write(f"SUMMARY:{summary}\n")
            f.write(f"LOCATION:{location}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write("END:VEVENT\n")
        f.write("END:VCALENDAR\n")

    print(f"✅ ICS-Datei '{output_file}' erfolgreich erstellt.")

# Aufruf
generate_ics(df_all)