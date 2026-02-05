from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from pytz import timezone

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

usc_keywords = ["usc münster", "usc muenster", "usc münster"]

# =========================
# Hilfsfunktionen
# =========================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.astype(str).str.strip()

    df = df.rename(columns={
        "Datum und Uhrzeit": "Datum_Uhrzeit",
        "Spieltag": "Datum",
        "Uhrzeit Beginn": "Uhrzeit",
        "Beginn": "Uhrzeit",
        "Mannschaft 1": "Heim",
        "Mannschaft 2": "Gast",
        "Schiedsgericht": "SR",
        "Gastgeber": "Gastgeber",
        "Austragungsort": "Ort",
        "Spielrunde": "Spielrunde",
    })

    # Kombi-Datum auftrennen
    if "Datum_Uhrzeit" in df.columns and "Datum" not in df.columns:
        parts = df["Datum_Uhrzeit"].astype(str).str.split(",", n=1, expand=True)
        df["Datum"] = parts[0].str.strip()
        df["Uhrzeit"] = parts[1].str.strip() if parts.shape[1] > 1 else ""

    # Pflichtspalten garantieren
    for col in ["Datum", "Uhrzeit", "Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
        if col not in df.columns:
            df[col] = ""

    return df


def contains_usc(row) -> bool:
    text = " ".join(
        str(row[c]).lower()
        for c in ["Heim", "Gast", "SR", "Gastgeber"]
    )
    return any(k in text for k in usc_keywords)


def replace_usc_names(s: str, team: str) -> str:
    s = str(s)

    base = [
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

    for old, new in base:
        s = s.replace(old, new)

    for old, new in team_specific.get(team, []):
        s = s.replace(old, new)

    return s


# =========================
# CSVs einlesen
# =========================

dfs = []

for file, team_code in csv_files:
    path = csv_dir / file
    if not path.exists():
        continue

    df = pd.read_csv(
        path,
        sep=";",
        encoding="cp1252",
        engine="python",
        on_bad_lines="skip"
    )

    df = normalize_columns(df)
    df = df[df.apply(contains_usc, axis=1)]
    df["USC_Team"] = team_code

    for col in ["Heim", "Gast", "SR", "Gastgeber", "Ort", "Spielrunde"]:
        df[col] = df.apply(
            lambda r: replace_usc_names(r[col], r["USC_Team"]),
            axis=1
        )

    # Datum + Uhrzeit → DATETIME (robust, vektorisiert)
    df["DATETIME"] = pd.to_datetime(
        df["Datum"].astype(str).str.strip() + " " +
        df["Uhrzeit"].astype(str).str.strip(),
        format="%d.%m.%Y %H:%M:%S",
        errors="coerce"
    )

    mask = df["DATETIME"].isna()
    df.loc[mask, "DATETIME"] = pd.to_datetime(
        df.loc[mask, "Datum"].astype(str).str.strip() + " " +
        df.loc[mask, "Uhrzeit"].astype(str).str.strip(),
        format="%d.%m.%Y %H:%M",
        errors="coerce"
    )

    df = df.dropna(subset=["DATETIME"])
    dfs.append(df)

if not dfs:
    raise RuntimeError("❌ Keine gültigen Spiele gefunden")

df_all = pd.concat(dfs, ignore_index=True)

# =========================
# Heimspiele filtern
# =========================

def is_hosting_and_playing(row) -> bool:
    gastgeber = str(row["Gastgeber"]).startswith("USC")
    playing = str(row["Heim"]).startswith("USC") or str(row["Gast"]).startswith("USC")
    return gastgeber and playing


df_all = (
    df_all[df_all.apply(is_hosting_and_playing, axis=1)]
    .sort_values("DATETIME")
)

# =========================
# ICS erzeugen
# =========================

def generate_ics(df: pd.DataFrame, output="docs/usc_spielplan.ics"):
    berlin = timezone("Europe/Berlin")
    utc = timezone("UTC")

    Path("docs").mkdir(exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write("BEGIN:VCALENDAR\n")
        f.write("VERSION:2.0\n")
        f.write("PRODID:-//USC Münster//Spielplan//DE\n")

        for _, row in df.iterrows():
            start = berlin.localize(row["DATETIME"])
            end = start + timedelta(hours=2)

            uid = (
                f"{start.strftime('%Y%m%dT%H%M')}-"
                f"{row['Heim']}-vs-{row['Gast']}@usc"
            ).replace(" ", "")

            f.write("BEGIN:VEVENT\n")
            f.write(f"UID:{uid}\n")
            f.write(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n")
            f.write(f"DTSTART:{start.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')}\n")
            f.write(f"DTEND:{end.astimezone(utc).strftime('%Y%m%dT%H%M%SZ')}\n")
            f.write(f"SUMMARY:{row['Heim']} vs {row['Gast']}\n")
            f.write(f"LOCATION:{str(row['Ort']).replace(chr(10), ' ')}\n")
            f.write(
                "DESCRIPTION:"
                f"Gastgeber: {row['Gastgeber']}\\n"
                f"Spielrunde: {row['Spielrunde']}\n"
            )
            f.write("END:VEVENT\n")

        f.write("END:VCALENDAR\n")

    print(f"✅ ICS-Datei erfolgreich erstellt: {output}")


# =========================
# Start
# =========================

generate_ics(df_all)
