from datetime import datetime, timezone
import unittest

from src import main

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
    def setUp(self):
        self.bowls, self.bettors = main.read_file("sample_data/data.csv")

    def test_validate_path(self):
        self.assertFalse(main.validate_path(PATH_INVALID_ALAMO, self.bowls))
        self.assertFalse(main.validate_path(PATH_INVALID_NATTY, self.bowls))
        self.assertTrue(main.validate_path(PATH_VALID, self.bowls))

    def test_check_for_tie(self):
        self.assertFalse(main.check_for_tie(RESULTS_DICT, 100))
        self.assertTrue(main.check_for_tie(RESULTS_DICT_TIE, 100))

    def test_get_paths_to_victory(self):
        wins = 0
        prob = 0
        paths_to_victory = main.get_paths_to_victory(self.bowls, self.bettors)

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                wins += 1
                prob += path_dict["prob"]

        self.assertEqual(256, wins)
        self.assertAlmostEqual(1.0, prob)

    def test_get_output_file_name(self):
        self.assertEqual(
            main.get_output_file_name("/Users/Bugs/Documents/bowl_pool_20221228.csv"),
            "/tmp/bowl_pool_20221228.csv",
        )


if __name__ == "__main__":
    unittest.main()
