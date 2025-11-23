import csv
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock gspread and pyperclip before importing main
mock_gspread = MagicMock()
mock_credentials = MagicMock()
mock_google_auth = MagicMock()
mock_pyperclip = MagicMock()

sys.modules['gspread'] = mock_gspread
sys.modules['google.oauth2.service_account'] = mock_credentials
sys.modules['google.auth.exceptions'] = mock_google_auth
sys.modules['pyperclip'] = mock_pyperclip

from src import main

PATH_INVALID_NON_PLAYOFF_ALAMO = (
    "Alamo_Colorado",
    "Austin_Clemson",
    "Beaver_Penn State",
    "Citrus_Illinois",
    "Cotton_Penn State",
    "Fiesta_Penn State",
    "Horseshoe_Ohio State",
    "Natty_Oregon",
    "Orange_Oregon",
    "Peach_Clemson",
    "PopTarts_Iowa State",
    "ReliaQuest_Alabama",
    "Rose_Oregon",
    "SouthBend_Notre Dame",
    "Sugar_Georgia",
)
PATH_INVALID_QUARTER_FIESTA = (
    "Alamo_BYU",
    "Austin_Clemson",
    "Beaver_Penn State",
    "Citrus_Illinois",
    "Cotton_Penn State",
    "Fiesta_SMU",
    "Horseshoe_Ohio State",
    "Natty_Oregon",
    "Orange_Oregon",
    "Peach_Clemson",
    "PopTarts_Iowa State",
    "ReliaQuest_Alabama",
    "Rose_Oregon",
    "SouthBend_Notre Dame",
    "Sugar_Georgia",
)
PATH_INVALID_SEMI_COTTON = (
    "Alamo_BYU",
    "Austin_Clemson",
    "Beaver_Penn State",
    "Citrus_Illinois",
    "Cotton_Indiana",
    "Fiesta_Penn State",
    "Horseshoe_Ohio State",
    "Natty_Oregon",
    "Orange_Oregon",
    "Peach_Clemson",
    "PopTarts_Iowa State",
    "ReliaQuest_Alabama",
    "Rose_Oregon",
    "SouthBend_Notre Dame",
    "Sugar_Georgia",
)
PATH_INVALID_NATTY = (
    "Alamo_BYU",
    "Austin_Clemson",
    "Beaver_Penn State",
    "Citrus_Illinois",
    "Cotton_Penn State",
    "Fiesta_Penn State",
    "Horseshoe_Ohio State",
    "Natty_Notre Dame",
    "Orange_Oregon",
    "Peach_Clemson",
    "PopTarts_Iowa State",
    "ReliaQuest_Alabama",
    "Rose_Oregon",
    "SouthBend_Notre Dame",
    "Sugar_Georgia",
)
PATH_VALID = (
    "Alamo_BYU",
    "Austin_Clemson",
    "Beaver_Penn State",
    "Citrus_Illinois",
    "Cotton_Penn State",
    "Fiesta_Penn State",
    "Horseshoe_Ohio State",
    "Natty_Oregon",
    "Orange_Oregon",
    "Peach_Clemson",
    "PopTarts_Iowa State",
    "ReliaQuest_Alabama",
    "Rose_Oregon",
    "SouthBend_Notre Dame",
    "Sugar_Georgia",
)


def read_csv_file(file_path: str) -> list:
    """Helper function to read CSV file and return as list of rows."""
    rows = []
    with open(file_path, "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rows.append(row)
    return rows


class TestMain(unittest.TestCase):

    def test_convert_to_bool(self):
        self.assertFalse(main.convert_to_bool("FALSE"))
        self.assertTrue(main.convert_to_bool("TRUE"))

    @patch("src.main.get_sheet_data")
    def test_get_play_in_teams(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/start.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        self.assertEqual(len(main.get_play_in_teams(bowls)), 8)

    @patch("src.main.get_sheet_data")
    def test_get_team_with_bye(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/start.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        self.assertEqual(main.get_team_with_bye("Fiesta", bowls), "Boise State")

    @patch("src.main.get_sheet_data")
    def test_get_my_qf(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/start.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        self.assertEqual(main.get_my_qf("Texas", bowls), "Peach")

    @patch("src.main.get_sheet_data")
    def test_get_my_semi(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/start.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        self.assertEqual(main.get_my_semi("Oregon", bowls), "Orange")

    @patch("src.main.get_sheet_data")
    def test_validate_path(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/middle.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)

        self.assertFalse(
            main.validate_path(
                PATH_INVALID_NON_PLAYOFF_ALAMO,
                bowls,
            )
        )
        self.assertFalse(
            main.validate_path(
                PATH_INVALID_QUARTER_FIESTA,
                bowls,
            )
        )
        self.assertFalse(
            main.validate_path(
                PATH_INVALID_SEMI_COTTON,
                bowls,
            )
        )
        self.assertFalse(
            main.validate_path(
                PATH_INVALID_NATTY,
                bowls,
            )
        )
        self.assertTrue(main.validate_path(PATH_VALID, bowls))

    @patch("src.main.get_sheet_data")
    def test_get_outcomes_start(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/start.csv"),
            read_csv_file("sample_data/picks/picks.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        picks = main.get_picks("mock_sheet_id", bowls)

        wins = 0
        losses = 0
        prob_of_win = 0
        prob_of_loss = 0

        paths_to_victory = main.get_paths_to_victory(bowls, picks)

        for _, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                # pyright: ignore [reportArgumentType, reportOperatorIssue]
                prob_of_win += path_dict["prob"]

        self.assertEqual(32768, wins)
        self.assertAlmostEqual(1.0, prob_of_win)

    @patch("src.main.get_sheet_data")
    def test_get_paths_to_victory_middle(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/middle.csv"),
            read_csv_file("sample_data/picks/picks.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        picks = main.get_picks("mock_sheet_id", bowls)

        wins = 0
        prob_of_win = 0

        paths_to_victory = main.get_paths_to_victory(bowls, picks)

        for _, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                # pyright: ignore [reportArgumentType, reportOperatorIssue]
                prob_of_win += path_dict["prob"]

        self.assertEqual(64, wins)
        self.assertAlmostEqual(1.0, prob_of_win)

    @patch("src.main.get_sheet_data")
    def test_get_paths_to_victory_end(self, mock_get_sheet_data):
        mock_get_sheet_data.side_effect = [
            read_csv_file("sample_data/multipliers/multipliers.csv"),
            read_csv_file("sample_data/bowls/end.csv"),
            read_csv_file("sample_data/picks/picks.csv"),
        ]
        multipliers = main.get_multipliers("mock_sheet_id")
        bowls = main.get_bowls("mock_sheet_id", multipliers)
        picks = main.get_picks("mock_sheet_id", bowls)

        paths_to_victory = main.get_paths_to_victory(bowls, picks)

        self.assertEqual(len(paths_to_victory), 1)
        self.assertEqual(len(paths_to_victory["Elmer Fudd"]), 1)
        # pyright: ignore [reportArgumentType]
        self.assertEqual(paths_to_victory["Elmer Fudd"][0]["prob"], 1.0)

if __name__ == "__main__":
    unittest.main()
