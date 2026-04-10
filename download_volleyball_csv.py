from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

from team_config import get_download_sources

CSV_DIR = Path("csvdata")


def download_file(url: str, target_path: Path) -> None:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as response:
        payload = response.read()

    head = payload[:1000].decode("latin1", errors="ignore").lower()
    if "<html" in head or "doctype" in head:
        raise RuntimeError(f"Ungültige CSV-Antwort für {target_path.name}")

    target_path.write_bytes(payload)


def main() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    for old_file in CSV_DIR.glob("*.csv"):
        old_file.unlink()

    sources = get_download_sources()
    for source in sources:
        target = CSV_DIR / source["datei"]
        print(f"⬇️ {source['team']} {source['wettbewerb']} -> {target.name}")
        download_file(source["link"], target)

    print("✅ Alle Volleyball-CSVs aktualisiert")


if __name__ == "__main__":
    main()
