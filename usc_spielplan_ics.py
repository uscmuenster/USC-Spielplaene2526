from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from pytz import timezone

from csv_utils import read_semicolon_csv
from team_config import get_csv_files
from usc_team_names import replace_usc_names

# =========================
# Konfiguration
# =========================

csv_dir = Path("csvdata")

csv_files = get_csv_files()

usc_keywords = ["USC Münster", "USC Muenster", "USC MÜNSTER"]

# =========================
# CSV lesen
# =========================

# =========================
# USC prüfen
# =========================

def contains_usc(row):
    return any(
        usc.lower() in str(row[f]).lower()
        for f in ["Heim", "Gast", "SR", "Gastgeber"]
        for usc in usc_keywords
    )


# =========================
# CSVs einlesen
# =========================

rename_map = {
    "Datum": "Datum",
    "Uhrzeit": "Uhrzeit",
    "Mannschaft 1": "Heim",
    "Mannschaft 2": "Gast",
    "Schiedsgericht": "SR",
    "Gastgeber": "Gastgeber",
    "Austragungsort": "Ort",
    "Spielrunde": "Spielrunde",
}

dfs = []

for file, team_code in csv_files:

    file_path = csv_dir / file

    if not file_path.exists():
        continue

    df = read_semicolon_csv(file_path)

    df = df.rename(columns=rename_map)

    # Datum + Uhrzeit aus "Datum und Uhrzeit"
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

    # Datum als datetime
    df["Datum_DT"] = pd.to_datetime(
        df["Datum"],
        format="%d.%m.%Y",
        errors="coerce"
    )

    df = df[df.apply(contains_usc, axis=1)]

    df["USC_Team"] = team_code

    for col in ["Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
        if col in df.columns:
            # Series.map liefert auch bei einem leeren Filter stets eine Series.
            # DataFrame.apply(axis=1) liefert bei einem leeren DataFrame dagegen
            # je nach pandas-Version einen DataFrame, der keiner einzelnen Spalte
            # zugewiesen werden kann ("Columns must be same length as key").
            df[col] = df[col].map(
                lambda value: replace_usc_names(value, team_code)
            )

    dfs.append(df)

if not dfs:
    print("⚠️ Keine USC Spiele gefunden")
    exit()

df_all = pd.concat(dfs, ignore_index=True)

# =========================
# Sortieren (stabil)
# =========================

df_all["_sort_dt"] = df_all["Datum_DT"].fillna(pd.Timestamp.max)

df_all = (
    df_all
    .sort_values(by=["_sort_dt", "Uhrzeit"], kind="mergesort")
    .drop(columns="_sort_dt")
)

# =========================
# Heimspiele filtern
# =========================

def is_hosting(row):
    return str(row["Gastgeber"]).startswith("USC")

df_all = df_all[df_all.apply(is_hosting, axis=1)]

# =========================
# ICS erzeugen
# =========================

def generate_ics(df, output="docs/usc_spielplan.ics"):

    berlin = timezone("Europe/Berlin")
    utc = timezone("UTC")

    Path("docs").mkdir(exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:

        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//USC Münster//Spielplan//DE\n")

        for _, row in df.iterrows():

            if pd.isna(row["Datum_DT"]):
                continue

            try:
                time_part = row["Uhrzeit"] if row["Uhrzeit"] else "12:00"
                dt = datetime.strptime(
                    f"{row['Datum']} {time_part}",
                    "%d.%m.%Y %H:%M"
                )
            except Exception:
                continue

            start = berlin.localize(dt)
            end = start + timedelta(hours=2)

            f.write("BEGIN:VEVENT\n")

            f.write(
                f"UID:{start.strftime('%Y%m%dT%H%M')}-{row['Heim']}-vs-{row['Gast']}@usc\n"
            )

            f.write(
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
            )

            f.write(
                f"DTSTART:{start.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')}\n"
            )

            f.write(
                f"DTEND:{end.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')}\n"
            )

            f.write(f"SUMMARY:{row['Heim']} vs {row['Gast']}\n")

            f.write(
                f"LOCATION:{str(row['Ort']).replace(chr(10),' ')}\n"
            )

            f.write(
                "DESCRIPTION:"
                f"Spielrunde: {row['Spielrunde']}\\n"
                f"Gastgeber: {row['Gastgeber']}\n"
            )

            f.write("END:VEVENT\n")

        f.write("END:VCALENDAR\n")

    print(f"✅ ICS-Datei erfolgreich erstellt: {output}")


# =========================
# Start
# =========================

generate_ics(df_all)
