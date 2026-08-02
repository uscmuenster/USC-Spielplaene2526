import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from csv_utils import read_semicolon_csv


class ReadSemicolonCsvTest(unittest.TestCase):
    def test_preserves_cp1252_encoded_team_names(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "spielplan.csv"
            csv_path.write_bytes(
                'Mannschaft 1;Gastgeber\nUSC Münster;USC Münster\n'.encode("cp1252")
            )

            dataframe = read_semicolon_csv(csv_path)

            self.assertEqual(dataframe.loc[0, "Mannschaft 1"], "USC Münster")
            self.assertEqual(dataframe.loc[0, "Gastgeber"], "USC Münster")


if __name__ == "__main__":
    unittest.main()
