from __future__ import annotations

from pathlib import Path
import csv
import pandas as pd


def load_csv_robust(file_path: Path, sep: str = ";") -> pd.DataFrame:
    """Load schedule CSV files robustly and guard against HTML error bodies."""
    head = Path(file_path).read_text(encoding="utf-8", errors="ignore")[:2000].lower()
    if "<html" in head or "<!doctype" in head:
        raise RuntimeError(f"❌ Keine gültige CSV (HTML erhalten): {file_path}")

    last_error: Exception | None = None
    for enc in ("cp1252", "utf-8", "utf-8-sig", "latin1"):
        try:
            return pd.read_csv(
                file_path,
                sep=sep,
                encoding=enc,
                engine="python",
                quoting=csv.QUOTE_MINIMAL,
                on_bad_lines="skip",
            )
        except Exception as exc:  # noqa: PERF203
            last_error = exc

    # Fallback: falls einzelne Exporte kaputte Quote-Strukturen enthalten.
    for enc in ("cp1252", "utf-8", "utf-8-sig", "latin1"):
        try:
            return pd.read_csv(
                file_path,
                sep=sep,
                encoding=enc,
                engine="python",
                quoting=csv.QUOTE_NONE,
                on_bad_lines="skip",
            )
        except Exception as exc:  # noqa: PERF203
            last_error = exc

    raise RuntimeError(f"❌ CSV konnte nicht gelesen werden: {file_path}") from last_error


def normalize_schedule_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize Datum/Uhrzeit fields and build canonical DATETIME + Datum_DT columns."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    source_col = None
    if "Datum und Uhrzeit" in df.columns:
        source_col = "Datum und Uhrzeit"
    elif "Datum_Uhrzeit" in df.columns:
        source_col = "Datum_Uhrzeit"

    if source_col is not None:
        split_parts = df[source_col].astype(str).str.split(",", n=1)
        if "Datum" not in df.columns:
            df["Datum"] = ""
        if "Uhrzeit" not in df.columns:
            df["Uhrzeit"] = ""

        split_datum = split_parts.str[0].fillna("").astype(str).str.strip()
        split_uhrzeit = split_parts.str[1].fillna("").astype(str).str.strip()

        datum_missing = df["Datum"].astype(str).str.strip().eq("")
        uhrzeit_missing = df["Uhrzeit"].astype(str).str.strip().eq("")

        df.loc[datum_missing, "Datum"] = split_datum[datum_missing]
        df.loc[uhrzeit_missing, "Uhrzeit"] = split_uhrzeit[uhrzeit_missing]

    if "Datum" not in df.columns:
        df["Datum"] = ""
    if "Uhrzeit" not in df.columns:
        df["Uhrzeit"] = ""

    df["Datum"] = df["Datum"].astype(str).str.strip()
    df["Uhrzeit"] = df["Uhrzeit"].astype(str).str.replace(r"\s*Uhr$", "", regex=True).str.strip()

    datetime_input = df["Datum"].astype(str) + " " + df["Uhrzeit"].astype(str)
    df["DATETIME"] = pd.to_datetime(datetime_input, format="%d.%m.%Y %H:%M", errors="coerce")

    datetime_missing = df["DATETIME"].isna()
    if datetime_missing.any():
        df.loc[datetime_missing, "DATETIME"] = pd.to_datetime(
            datetime_input[datetime_missing],
            format="%d.%m.%Y %H:%M:%S",
            errors="coerce",
        )

    datetime_missing = df["DATETIME"].isna()
    if datetime_missing.any():
        df.loc[datetime_missing, "DATETIME"] = pd.to_datetime(
            datetime_input[datetime_missing],
            errors="coerce",
            dayfirst=True,
        )

    if "Datum_DT" not in df.columns:
        df["Datum_DT"] = pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce")
    else:
        df["Datum_DT"] = pd.to_datetime(df["Datum_DT"], errors="coerce")

    datum_missing = df["Datum_DT"].isna()
    if datum_missing.any():
        df.loc[datum_missing, "Datum_DT"] = pd.to_datetime(
            df.loc[datum_missing, "Datum"],
            errors="coerce",
            dayfirst=True,
        )

    return df


def get_datetime_sort_columns(df: pd.DataFrame) -> list[str]:
    if "DATETIME" in df.columns:
        return ["DATETIME", "Uhrzeit"] if "Uhrzeit" in df.columns else ["DATETIME"]
    if "Datum_DT" in df.columns:
        return ["Datum_DT", "Uhrzeit"] if "Uhrzeit" in df.columns else ["Datum_DT"]
    return ["Uhrzeit"] if "Uhrzeit" in df.columns else []
