from datetime import datetime, timezone
import unittest

from src import main

EXPECTED_BETTORS = {
    "Bugs Bunny": {
        "Alamo_Washington": 0.0,
        "Alamo_Texas": 9.0,
        "Citrus_Purdue": 0.0,
        "Citrus_LSU": 2.7,
        "Cotton_Tulane": 0.0,
        "Cotton_USC": 16.4,
        "Fiesta_TCU": 38.0,
        "Fiesta_Michigan": 0.0,
        "Gator_South Carolina": 2.7,
        "Gator_Notre Dame": 0.0,
        "Orange_Tennessee": 0.0,
        "Orange_Clemson": 7.3,
        "Peach_Ohio State": 0.0,
        "Peach_Georgia": 4.3,
        "Rose_Penn State": 16.2,
        "Rose_Utah": 0.0,
        "Sugar_Kansas State": 0.0,
        "Sugar_Alabama": 12.5,
        "Natty_TCU": 0.0,
        "Natty_Ohio State": 0.0,
        "Natty_Michigan": 0.0,
        "Natty_Georgia": 7.7,
    },
    "Elmer Fudd": {
        "Alamo_Washington": 0.0,
        "Alamo_Texas": 10.5,
        "Citrus_Purdue": 0.0,
        "Citrus_LSU": 10.9,
        "Cotton_Tulane": 0.0,
        "Cotton_USC": 18.3,
        "Fiesta_TCU": 11.4,
        "Fiesta_Michigan": 0.0,
        "Gator_South Carolina": 5.3,
        "Gator_Notre Dame": 0.0,
        "Orange_Tennessee": 0.0,
        "Orange_Clemson": 5.8,
        "Peach_Ohio State": 0.0,
        "Peach_Georgia": 7.2,
        "Rose_Penn State": 0.0,
        "Rose_Utah": 15.9,
        "Sugar_Kansas State": 16.8,
        "Sugar_Alabama": 0.0,
        "Natty_TCU": 0.0,
        "Natty_Ohio State": 0.0,
        "Natty_Michigan": 0.0,
        "Natty_Georgia": 1.9,
    },
}
EXPECTED_BOWLS = {
    "Alamo": {"Alamo_Washington", "Alamo_Texas"},
    "Citrus": {"Citrus_Purdue", "Citrus_LSU"},
    "Cotton": {"Cotton_Tulane", "Cotton_USC"},
    "Fiesta": {"Fiesta_Michigan", "Fiesta_TCU"},
    "Gator": {"Gator_South Carolina", "Gator_Notre Dame"},
    "Orange": {"Orange_Tennessee", "Orange_Clemson"},
    "Peach": {"Peach_Ohio State", "Peach_Georgia"},
    "Rose": {"Rose_Penn State", "Rose_Utah"},
    "Sugar": {"Sugar_Kansas State", "Sugar_Alabama"},
    "Natty": {
        "Natty_Ohio State",
        "Natty_Georgia",
        "Natty_Michigan",
        "Natty_TCU",
    },
}
WINNING_PICKS_INVALID = (
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
WINNING_PICKS_VALID = (
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


class TestMain(unittest.TestCase):
    def test_read_file(self):
        bowls, bettors = main.read_file("sample_data/data.csv")
        self.assertDictEqual(bowls, EXPECTED_BOWLS)
        self.assertDictEqual(
            bettors,
            EXPECTED_BETTORS,
        )

    def test_validate_winning_picks(self):
        self.assertTrue(main.validate_winning_picks(WINNING_PICKS_VALID))
        self.assertFalse(main.validate_winning_picks(WINNING_PICKS_INVALID))

    def test_get_winner(self):
        self.assertEqual(
            main.get_winner(WINNING_PICKS_VALID, EXPECTED_BETTORS), "Bugs Bunny"
        )

    def test_get_paths_to_victory(self):
        paths_to_victory = main.get_paths_to_victory(EXPECTED_BOWLS, EXPECTED_BETTORS)
        self.assertDictEqual(
            paths_to_victory,
            {"Bugs Bunny": 523, "Elmer Fudd": 501},
        )
        self.assertEqual(1024, sum(paths_to_victory.values()))


if __name__ == "__main__":
    unittest.main()
