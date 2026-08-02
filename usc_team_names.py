"""Zentrale Erkennung und einheitliche Benennung der USC-Mannschaften."""
from __future__ import annotations

import re
from collections.abc import Mapping


SENIOR_NAME_REPLACEMENTS = (
    ("USC Münster VIII", "USC8"),
    ("USC Münster VII", "USC7"),
    ("USC Münster VI", "USC6"),
    ("USC Münster V", "USC5"),
    ("USC Münster IV", "USC4"),
    ("USC Münster III", "USC3"),
    ("USC Münster II", "USC2"),
    ("USC Münster", "USC1"),
)

USC_ROW_FIELDS = ("Heim", "Gast", "SR", "Gastgeber")


def split_team_codes(configured_team: str | None) -> list[str]:
    """Teilt eine Konfigurationsangabe wie ``USC4/USC5`` in Teamcodes."""

    return [code.strip() for code in (configured_team or "").split("/") if code.strip()]


def replace_usc_names(value: object, configured_team: str | None = None) -> str:
    """Kürzt USC-Namen und ordnet Jugend-Teamnummern ihrer Altersklasse zu."""

    result = str(value)
    for old, new in SENIOR_NAME_REPLACEMENTS:
        result = result.replace(old, new)

    team_codes = split_team_codes(configured_team)
    if team_codes and all("-U" in code for code in team_codes):
        for number, code in enumerate(team_codes, start=1):
            result = re.sub(rf"\bUSC{number}\b", code, result)

    return result


def get_usc_team(row: Mapping[str, object], configured_team: str | None) -> str:
    """Ermittelt die beteiligten Teamcodes anhand der zentralen Konfiguration."""

    team_codes = split_team_codes(configured_team)
    if len(team_codes) <= 1:
        return team_codes[0] if team_codes else ""

    text = " ".join(replace_usc_names(row.get(field, ""), configured_team) for field in USC_ROW_FIELDS)
    found = [code for code in team_codes if re.search(rf"\b{re.escape(code)}\b", text)]
    return "/".join(found) if found else "/".join(team_codes)
