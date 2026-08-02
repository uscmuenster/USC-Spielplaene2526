import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from team_config import get_csv_files, get_download_sources
from usc_team_names import get_usc_team, replace_usc_names, split_team_codes


class UscTeamNamesTest(unittest.TestCase):
    def test_splits_combined_configuration(self):
        self.assertEqual(split_team_codes("USC4/USC5"), ["USC4", "USC5"])

    def test_replaces_senior_roman_numerals(self):
        self.assertEqual(replace_usc_names("USC Münster V"), "USC5")

    def test_replaces_both_youth_teams_from_combined_source(self):
        configured_team = "USC-U14-1/USC-U14-2"
        self.assertEqual(replace_usc_names("USC Münster", configured_team), "USC-U14-1")
        self.assertEqual(replace_usc_names("USC Münster II", configured_team), "USC-U14-2")

    def test_detects_team_from_combined_source(self):
        row = {"Heim": "USC Münster IV", "Gast": "USC Münster V"}
        self.assertEqual(get_usc_team(row, "USC4/USC5"), "USC4/USC5")

    def test_detects_one_youth_team_from_combined_source(self):
        row = {"Heim": "USC Münster II", "Gast": "Auswärtsteam"}
        self.assertEqual(get_usc_team(row, "USC-U13-1/USC-U13-2"), "USC-U13-2")

    def test_team_config_keeps_combined_teams_and_skips_empty_downloads(self):
        with TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "teams.csv"
            config.write_text(
                "team;wettbewerb;link;datei\n"
                "USC4/USC5;BL;https://example.test/plan.csv;plan.csv\n"
                "USC1;Playoffs;;playoffs.csv\n",
                encoding="utf-8",
            )

            self.assertEqual(
                get_csv_files(config),
                [("plan.csv", "USC4/USC5"), ("playoffs.csv", "USC1")],
            )
            self.assertEqual(len(get_download_sources(config)), 1)


if __name__ == "__main__":
    unittest.main()
