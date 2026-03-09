from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from pytz import timezone
import re

# =========================
# Konfiguration
# =========================

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

# =========================
# CSV lesen
# =========================

def read_csv_clean(path: Path) -> pd.DataFrame:
    last_error = None

    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(
                path,
                sep=";",
                encoding=encoding,
                encoding_errors="replace",
                engine="python",
                on_bad_lines="skip"
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise last_error

    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.dropna(axis=1, how="all")

    return df


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
# USC Namen kürzen
# =========================

def replace_usc_names(s, team):
    s = str(s)

    replacements = [
        ("USC Münster VIII", "USC8"),
        ("USC Münster VII", "USC7"),
        ("USC Münster VI", "USC6"),
        ("USC Münster V", "USC5"),
        ("USC Münster IV", "USC4"),
        ("USC Münster III", "USC3"),
        ("USC Münster II", "USC2"),
        ("USC Münster", "USC1"),
    ]

    for old, new in replacements:
        s = s.replace(old, new)

    return s


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

    df = read_csv_clean(file_path)

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
            df[col] = df.apply(
                lambda r: replace_usc_names(r[col], r["USC_Team"]),
                axis=1
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