from datetime import datetime, timezone
import unittest

from src import main

NATTY_BOWL_NAME = "Natty"
SEMI_BOWL_NAMES = {"Fiesta", "Peach"}
PATH_INVALID_ALAMO = (
    "Alamo_Washington",
    "Citrus_LSU",
    "Cotton_Tulane",
    "Fiesta_TCU",
    "Gator_Notre Dame",
    "Orange_Tennessee",
    "Peach_Ohio State",
    "Rose_Penn State",
    "Sugar_Kansas State",
    "Natty_Georgia",
)
PATH_INVALID_NATTY = (
    "Alamo_Texas",
    "Citrus_LSU",
    "Cotton_Tulane",
    "Fiesta_TCU",
    "Gator_Notre Dame",
    "Orange_Tennessee",
    "Peach_Ohio State",
    "Rose_Penn State",
    "Sugar_Kansas State",
    "Natty_Georgia",
)
PATH_VALID = (
    "Alamo_Texas",
    "Citrus_LSU",
    "Cotton_Tulane",
    "Fiesta_TCU",
    "Gator_Notre Dame",
    "Orange_Tennessee",
    "Peach_Georgia",
    "Rose_Penn State",
    "Sugar_Kansas State",
    "Natty_Georgia",
)
RESULTS_DICT = {
    "Elmer Fudd": {"score": 95, "correct_picks": 6},
    "Bugs Bunny": {"score": 100, "correct_picks": 8},
    "Daffy Duck": {"score": 75, "correct_picks": 6},
}
RESULTS_DICT_TIE = {
    "Elmer Fudd": {"score": 100, "correct_picks": 6},
    "Bugs Bunny": {"score": 100, "correct_picks": 8},
    "Daffy Duck": {"score": 75, "correct_picks": 6},
}


class TestMain(unittest.TestCase):
    def test_convert_to_bool(self):
        self.assertFalse(main.convert_to_bool("FALSE"))
        self.assertTrue(main.convert_to_bool("TRUE"))

    def test_validate_path(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)

        self.assertFalse(
            main.validate_path(
                PATH_INVALID_ALAMO, bowls, NATTY_BOWL_NAME, SEMI_BOWL_NAMES
            )
        )
        self.assertFalse(
            main.validate_path(
                PATH_INVALID_NATTY, bowls, NATTY_BOWL_NAME, SEMI_BOWL_NAMES
            )
        )
        self.assertTrue(
            main.validate_path(PATH_VALID, bowls, NATTY_BOWL_NAME, SEMI_BOWL_NAMES)
        )

    def test_check_for_tie(self):
        self.assertFalse(main.check_for_tie(RESULTS_DICT, 100))
        self.assertTrue(main.check_for_tie(RESULTS_DICT_TIE, 100))

    def test_get_paths_to_victory_start(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/start.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(bowls, picks)

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                prob += path_dict["prob"]

        self.assertEqual(1024, wins)
        self.assertAlmostEqual(1.0, prob)

    def test_get_paths_to_victory_middle(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(bowls, picks)

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                prob += path_dict["prob"]

        self.assertEqual(8, wins)
        self.assertAlmostEqual(1.0, prob)

    def test_get_paths_to_victory_end(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/end.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(bowls, picks)

        self.assertEqual(len(paths_to_victory), 1)
        self.assertEqual(len(paths_to_victory["Road Runner"]), 1)
        self.assertEqual(paths_to_victory["Road Runner"][0]["prob"], 1.0)
        self.assertEqual(paths_to_victory["Road Runner"][0]["correct_picks"], 8)


if __name__ == "__main__":
    unittest.main()
