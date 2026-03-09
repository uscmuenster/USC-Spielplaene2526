from pathlib import Path
from datetime import datetime
import pandas as pd
import os


def load_csv_robust(file_path):
    """
    Robuster CSV-Loader:
    - erkennt HTML-Fehlerseiten
    - testet Encoding automatisch
    - ignoriert kaputte Quotes
    - überspringt defekte Zeilen
    """

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        head = f.read(1000).lower()

    if "<html" in head or "doctype" in head:
        raise RuntimeError(f"❌ Keine gültige CSV (HTML erhalten): {file_path}")

    last_error = None
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(
                file_path,
                sep=";",
                encoding=encoding,
                encoding_errors="replace",
                engine="python",
                quoting=3,
                on_bad_lines="skip"
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise RuntimeError(f"❌ CSV konnte nicht gelesen werden: {file_path}") from last_error

    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.replace('"', "", regex=False)
        .str.strip()
    )

    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.dropna(axis=1, how="all")

    return df


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

usc_keywords = ["usc münster", "usc muenster"]

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
    df = load_csv_robust(file_path)

    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)

    # Datum/Uhrzeit erzeugen wenn nur "Datum und Uhrzeit" existiert
    if "Datum und Uhrzeit" in df.columns:
        dt = pd.to_datetime(
            df["Datum und Uhrzeit"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip(),
            format="%d.%m.%Y %H:%M:%S",
            errors="coerce",
        )

        df["Datum"] = dt.dt.strftime("%d.%m.%Y")
        df["Uhrzeit"] = dt.dt.strftime("%H:%M")

    def contains_usc(row):

        text = " ".join(
            str(row.get(f, "")).lower()
            for f in ["Heim", "Gast", "SR", "Gastgeber"]
        )

        return any(k in text for k in usc_keywords)

    df = df[df.apply(contains_usc, axis=1)]

    def get_usc_team(row):

        text = f"{row.get('Heim','')} {row.get('Gast','')} {row.get('SR','')} {row.get('Gastgeber','')}".lower()

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
        df[col] = df.apply(lambda row: replace_usc_names(row.get(col, ""), row["USC_Team"]), axis=1)

    dfs.append(df)


df_all = pd.concat(dfs, ignore_index=True)

print("📊 Anzahl Spiele im df_all:", len(df_all))
print("🔍 Spalten:", df_all.columns.tolist())

df_all["Datum_DT"] = pd.to_datetime(
    df_all["Datum"],
    format="%d.%m.%Y",
    errors="coerce"
)

tage_map = {
    "Monday": "Mo",
    "Tuesday": "Di",
    "Wednesday": "Mi",
    "Thursday": "Do",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "So"
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

for col in ["Heim", "Gast", "SR", "Gastgeber"]:
    df_all[col] = df_all[col].str.replace(r'\b(USC-[U\d]+-\d) II\b', r'\1', regex=True)

df_all = df_all.sort_values(by=["Datum_DT", "Uhrzeit"])

print(f"🔍 Anzahl Zeilen: {len(df_all)}")
print(f"📄 Spalten: {df_all.columns.tolist()}")

print("📁 Aktuelles Arbeitsverzeichnis:", os.getcwd())
print("📂 Ordnerinhalt:", os.listdir())

csv_path = Path("docs/spielplan.csv")

try:
    df_all.to_csv(csv_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"✅ CSV-Datei erfolgreich gespeichert unter: {csv_path.resolve()}")
except Exception as e:
    print("❌ Fehler beim Schreiben der CSV-Datei:", e)