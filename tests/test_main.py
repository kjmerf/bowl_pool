import unittest

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


class TestMain(unittest.TestCase):

    def test_convert_to_bool(self):
        self.assertFalse(main.convert_to_bool("FALSE"))
        self.assertTrue(main.convert_to_bool("TRUE"))

    def test_get_play_in_teams(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)
        self.assertEqual(len(main.get_play_in_teams(bowls)), 8)

    def test_get_team_with_bye(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)
        self.assertEqual(main.get_team_with_bye("Fiesta", bowls), "Boise State")

    def test_get_my_qf(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)
        self.assertEqual(main.get_my_qf("Texas", bowls), "Peach")

    def test_get_my_semi(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)
        self.assertEqual(main.get_my_semi("Oregon", bowls), "Orange")

    def test_validate_path(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)

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

    def test_get_outcomes_start(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        losses = 0
        prob_of_win = 0
        prob_of_loss = 0

        paths_to_victory, paths_to_defeat = main.get_outcomes(bowls, picks)

        for _, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                # pyright: ignore [reportArgumentType, reportOperatorIssue]
                prob_of_win += path_dict["prob"]

        self.assertEqual(32768, wins)
        self.assertAlmostEqual(1.0, prob_of_win)

        for _, path_list in paths_to_defeat.items():
            for path_dict in path_list:
                losses += 1
                # pyright: ignore [reportArgumentType, reportOperatorIssue]
                prob_of_loss += path_dict["prob"]

        self.assertEqual(32768, losses)
        self.assertAlmostEqual(1.0, prob_of_loss)

    def test_get_paths_to_victory_middle(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        losses = 0
        prob_of_win = 0
        prob_of_loss = 0

        paths_to_victory, paths_to_defeat = main.get_outcomes(bowls, picks)

        for _, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                # pyright: ignore [reportArgumentType, reportOperatorIssue]
                prob_of_win += path_dict["prob"]

        self.assertEqual(64, wins)
        self.assertAlmostEqual(1.0, prob_of_win)

        for _, path_list in paths_to_defeat.items():
            for path_dict in path_list:
                losses += 1
                # pyright: ignore [reportArgumentType, reportOperatorIssue]
                prob_of_loss += path_dict["prob"]

        self.assertEqual(64, losses)
        self.assertAlmostEqual(1.0, prob_of_loss)

    def test_get_paths_to_victory_end(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/end.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        paths_to_victory, paths_to_defeat = main.get_outcomes(bowls, picks)

        self.assertEqual(len(paths_to_victory), 1)
        self.assertEqual(len(paths_to_victory["Elmer Fudd"]), 1)
        self.assertEqual(len(paths_to_defeat), 1)
        self.assertEqual(len(paths_to_defeat["Daffy Duck"]), 1)
        # pyright: ignore [reportArgumentType]
        self.assertEqual(paths_to_victory["Elmer Fudd"][0]["prob"], 1.0)
        # pyright: ignore [reportArgumentType]
        self.assertEqual(paths_to_defeat["Daffy Duck"][0]["prob"], 1.0)


if __name__ == "__main__":
    unittest.main()
