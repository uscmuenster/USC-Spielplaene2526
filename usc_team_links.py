"""Hilfsfunktionen rund um die Verlinkung zu offiziellen USC-Tabellen."""
from __future__ import annotations

from html import escape
from typing import Iterable

BASE_URL = "https://ergebnisdienst.volleyball.nrw/"


def _nrw(path: str) -> str:
    """Erzeugt einen vollständigen Ergebnisdienst-Link aus einem relativen Pfad."""

    if path.startswith("http"):
        return path
    return f"{BASE_URL}{path.lstrip('/')}"


# Metadaten zu allen USC-Mannschaften inkl. Liga- und Tabellen-Links.
USC_TEAM_TABLE_INFO = {
    "USC1": {
        "name": "USC Münster I",
        "league": "1. Bundesliga Frauen",
        "url": "https://www.volleyball-bundesliga.de/cms/home/1_bundesliga_frauen/statistik/hauptrunde/tabelle_hauptrunde.xhtml",
        "order": 10,
    },
    "USC2": {
        "name": "USC Münster II",
        "league": "2. Bundesliga Frauen Nord",
        "url": "https://www.volleyball-bundesliga.de/cms/home/2_bundesliga_frauen/2_bundesliga_frauen_nord/tabellespielplan/tabelle.xhtml",
        "order": 20,
    },
    "USC3": {
        "name": "USC Münster III",
        "league": "Oberliga 2 Frauen",
        "url": _nrw("cms/home/erwachsene/oberligen/oberliga_frauen/oberliga_2.xhtml"),
        "order": 30,
    },
    "USC4": {
        "name": "USC Münster IV",
        "league": "Bezirksliga 14 Frauen",
        "url": _nrw("cms/home/erwachsene/bezirksligen/bezirksligen_frauen/bezirksliga_14_frauen.xhtml"),
        "order": 40,
    },
    "USC5": {
        "name": "USC Münster V",
        "league": "Bezirksklasse 26 Frauen",
        "url": _nrw("cms/home/erwachsene/bezirksklassen/bezirksklassen_frauen/bezirksklasse_26_frauen.xhtml"),
        "order": 50,
    },
    "USC6": {
        "name": "USC Münster VI",
        "league": "Bezirksklasse 26 Frauen",
        "url": _nrw("cms/home/erwachsene/bezirksklassen/bezirksklassen_frauen/bezirksklasse_26_frauen.xhtml"),
        "order": 55,
    },
    "USC7": {
        "name": "USC Münster VII",
        "league": "Kreisliga Münster Frauen",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/erwachsene/kreisligen/alle_kreisligen.xhtml?LeaguePresenter.view=resultTable&LeaguePresenter.matchSeriesId=95241488#samsCmsComponent_103072206",
        "order": 60,
    },
    "USC8": {
        "name": "USC Münster VIII",
        "league": "Kreisliga Münster Frauen",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/erwachsene/kreisligen/alle_kreisligen.xhtml?LeaguePresenter.view=resultTable&LeaguePresenter.matchSeriesId=95241488#samsCmsComponent_103072206",
        "order": 65,
    },
    "USC-U18": {
        "name": "USC Münster wU18",
        "league": "NRW-Liga wU18",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/jugend/u18/u18_weiblich/nrw_liga.xhtml",
        "order": 110,
    },
    "USC-U16-1": {
        "name": "USC Münster wU16 I",
        "league": "NRW-Liga wU16",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/jugend/u16/u16_weiblich/nrw_liga.xhtml",
        "order": 120,
    },
    "USC-U16-2": {
        "name": "USC Münster wU16 II",
        "league": "Oberliga 5 wU16",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/jugend/u16/u16_weiblich/oberliga_2.xhtml",
        "order": 130,
    },
    "USC-U14-1": {
        "name": "USC Münster wU14 I",
        "league": "NRW-Liga wU14",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/jugend/u14/u14_weiblich/nrw_liga.xhtml",
        "order": 140,
    },
    "USC-U14-2": {
        "name": "USC Münster wU14 II",
        "league": "Oberliga 5 wU14",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/jugend/u14/u14_weiblich/oberliga_5.xhtml",
        "order": 150,
    },
    "USC-U13": {
        "name": "USC Münster wU13",
        "league": "Oberliga 6 wU13",
        "url": "https://ergebnisdienst.volleyball.nrw/cms/home/jugend/u13/u13_weiblich/oberliga_6.xhtml",
        "order": 160,
    },
}


def build_team_table_overview(team_codes: Iterable[str]) -> str:
    """Erzeugt den HTML-Block mit der Tabellenübersicht inklusive Links."""

    unique_codes = sorted({code for code in team_codes if code}, key=lambda code: USC_TEAM_TABLE_INFO.get(code, {}).get("order", 999))
    if not unique_codes:
        return ""

    rows = []
    for code in unique_codes:
        info = USC_TEAM_TABLE_INFO.get(code)
        if info is None:
            link_html = '<span class="text-muted">Kein Link hinterlegt</span>'
            rows.append(f"<tr><td>{escape(code)}</td><td>-</td><td>{link_html}</td></tr>")
            continue

        team_name = info.get("name", code)
        league = info.get("league", "")
        url = info.get("url")
        if not url:
            path = info.get("path")
            if path:
                url = _nrw(path)

        if url:
            link_html = (
                f'<a href="{escape(url)}" class="link-dark" target="_blank" rel="noopener">'
                "Tabelle öffnen"
                "</a>"
            )
        else:
            link_html = '<span class="text-muted">Kein Link hinterlegt</span>'
        rows.append(f"<tr><td>{escape(team_name)}</td><td>{escape(league)}</td><td>{link_html}</td></tr>")

    rows_html = "".join(rows)

    return (
        "<div class=\"accordion mb-3\" id=\"teamTables\">\n"
        "  <div class=\"accordion-item\">\n"
        "    <h2 class=\"accordion-header\" id=\"headingTeamTables\">\n"
        "      <button class=\"accordion-button collapsed\" type=\"button\" data-bs-toggle=\"collapse\" data-bs-target=\"#collapseTeamTables\" aria-expanded=\"false\" aria-controls=\"collapseTeamTables\">\n"
        "        Tabellen der USC-Mannschaften\n"
        "      </button>\n"
        "    </h2>\n"
        "    <div id=\"collapseTeamTables\" class=\"accordion-collapse collapse\" aria-labelledby=\"headingTeamTables\">\n"
        "      <div class=\"accordion-body\">\n"
        "        <p class=\"mb-3\">Direkte Links zu den offiziellen Ergebnisdiensten der beteiligten Ligen.</p>\n"
        "        <div class=\"table-responsive\">\n"
        "          <table class=\"table table-sm table-striped mb-0\">\n"
        "            <thead>\n"
        "              <tr><th>Team</th><th>Liga</th><th>Ergebnisdienst</th></tr>\n"
        "            </thead>\n"
        "            <tbody>\n"
        f"              {rows_html}\n"
        "            </tbody>\n"
        "          </table>\n"
        "        </div>\n"
        "      </div>\n"
        "    </div>\n"
        "  </div>\n"
        "</div>\n"
    )
