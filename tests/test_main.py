from datetime import datetime, timezone
import unittest

from src import main

NATTY_BOWL_NAME = "Natty"
FIRST_ROUND_BOWL_NAMES = {"Citrus", "Sugar", "Rose", "ReliaQuest"}
PATH_INVALID_ALAMO = (
    "Alamo_Oklahoma",
    "Sun_Notre Dame",
    "Cotton_Missouri",
    "Orange_Georgia",
    "Peach_Ole Miss",
    "Citrus_Tennessee",
    "Sugar_Washington",
    "Rose_Michigan",
    "ReliaQuest_LSU",
    "Natty_Washington",
)
PATH_INVALID_NATTY = (
    "Alamo_Arizona",
    "Sun_Notre Dame",
    "Cotton_Missouri",
    "Orange_Georgia",
    "Peach_Ole Miss",
    "Citrus_Tennessee",
    "Sugar_Washington",
    "Rose_Michigan",
    "ReliaQuest_LSU",
    "Natty_Texas",
)
PATH_INVALID_NATTY_LOSERS = (
    "Alamo_Arizona",
    "Sun_Notre Dame",
    "Cotton_Missouri",
    "Orange_Georgia",
    "Peach_Ole Miss",
    "Citrus_Tennessee",
    "Sugar_Washington",
    "Rose_Michigan",
    "ReliaQuest_LSU",
    "Natty_Clemson",
)
PATH_VALID = (
    "Alamo_Arizona",
    "Sun_Notre Dame",
    "Cotton_Missouri",
    "Orange_Georgia",
    "Peach_Ole Miss",
    "Citrus_Tennessee",
    "Sugar_Washington",
    "Rose_Michigan",
    "ReliaQuest_LSU",
    "Natty_Washington",
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

    def test_get_teams_with_bye(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)

        self.assertEqual(len(main.get_teams_with_bye(bowls)), 4)

    def test_get_losers(self):
        self.assertEqual(
            main.get_losers("Clemson, Kansas State"), {"Clemson", "Kansas State"}
        )

    def test_validate_path(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)

        self.assertFalse(
            main.validate_path(
                PATH_INVALID_ALAMO,
                bowls,
                NATTY_BOWL_NAME,
                FIRST_ROUND_BOWL_NAMES,
                set(),
            )
        )
        self.assertFalse(
            main.validate_path(
                PATH_INVALID_NATTY,
                bowls,
                NATTY_BOWL_NAME,
                FIRST_ROUND_BOWL_NAMES,
                set(),
            )
        )
        self.assertFalse(
            main.validate_path(
                PATH_INVALID_NATTY_LOSERS,
                bowls,
                NATTY_BOWL_NAME,
                FIRST_ROUND_BOWL_NAMES,
                {"Clemson"},
            )
        )
        self.assertTrue(
            main.validate_path(
                PATH_VALID, bowls, NATTY_BOWL_NAME, FIRST_ROUND_BOWL_NAMES, set()
            )
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
        paths_to_victory = main.get_paths_to_victory(bowls, picks, set())

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                prob += path_dict["prob"]

        self.assertEqual(4096, wins)
        self.assertAlmostEqual(1.0, prob)

    def test_get_paths_to_victory_middle(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(bowls, picks, set())

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                prob += path_dict["prob"]

        self.assertEqual(8, wins)
        self.assertAlmostEqual(1.0, prob)

    def test_get_paths_to_victory_middle_with_losers(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/middle.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(
            bowls, picks, {"Clemson", "Michigan"}
        )

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                prob += path_dict["prob"]

        self.assertEqual(6, wins)
        self.assertAlmostEqual(1.0, prob)

    def test_get_paths_to_victory_end(self):
        multipliers = main.get_multipliers("sample_data/multipliers/multipliers.csv")
        bowls = main.get_bowls("sample_data/bowls/end.csv", multipliers)
        picks = main.get_picks("sample_data/picks/picks.csv", bowls)

        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(bowls, picks, set())

        self.assertEqual(len(paths_to_victory), 1)
        self.assertEqual(len(paths_to_victory["Daffy Duck"]), 1)
        self.assertEqual(paths_to_victory["Daffy Duck"][0]["prob"], 1.0)
        self.assertEqual(paths_to_victory["Daffy Duck"][0]["correct_picks"], 8)


if __name__ == "__main__":
    unittest.main()
