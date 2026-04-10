from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

TEAM_SOURCES_PATH = Path("config/team_sources.csv")


def load_team_sources(config_path: Path = TEAM_SOURCES_PATH) -> list[dict[str, str]]:
    """Lädt die Team-/Wettbewerbskonfiguration aus CSV (Semikolon-getrennt)."""

    if not config_path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei nicht gefunden: {config_path}")

    with config_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        expected = {"team", "wettbewerb", "link", "datei"}
        if reader.fieldnames is None:
            raise ValueError(f"Keine Kopfzeile in {config_path}")
        missing = expected - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Fehlende Spalten in {config_path}: {sorted(missing)}")

        rows: list[dict[str, str]] = []
        for row in reader:
            clean_row = {k: (v or "").strip() for k, v in row.items()}
            if not clean_row["datei"]:
                continue
            rows.append(clean_row)

    return rows


def get_csv_files(config_path: Path = TEAM_SOURCES_PATH) -> list[tuple[str, str | None]]:
    """Gibt (Dateiname, Teamcode)-Paare für die Spielplan-Skripte zurück."""

    csv_files: list[tuple[str, str | None]] = []
    for row in load_team_sources(config_path):
        team = row["team"]
        team_code = team if "/" not in team else None
        csv_files.append((row["datei"], team_code))
    return csv_files


def get_download_sources(config_path: Path = TEAM_SOURCES_PATH) -> list[dict[str, Any]]:
    """Gibt Download-Metadaten für CSV-Updates zurück."""

    return [
        {
            "team": row["team"],
            "wettbewerb": row["wettbewerb"],
            "link": row["link"],
            "datei": row["datei"],
        }
        for row in load_team_sources(config_path)
    ]
