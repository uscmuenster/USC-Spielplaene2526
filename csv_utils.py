from pathlib import Path

import pandas as pd


def read_semicolon_csv(path: Path) -> pd.DataFrame:
    """Read a SAMS CSV without silently replacing characters in team names."""
    last_error = None

    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(
                path,
                sep=";",
                encoding=encoding,
                engine="python",
                on_bad_lines="skip",
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
    return df.dropna(axis=1, how="all")
