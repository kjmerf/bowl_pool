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

class TestMain(unittest.TestCase):
    def setUp(self):
        self.bowls, self.bettors = main.read_file("sample_data/data.csv")

    def test_validate_path(self):
        self.assertFalse(main.validate_path(PATH_INVALID_ALAMO, self.bowls))
        self.assertFalse(main.validate_path(PATH_INVALID_NATTY, self.bowls))
        self.assertTrue(main.validate_path(PATH_VALID, self.bowls))

    def test_get_winner(self):
        self.assertEqual(
            main.get_winner(PATH_VALID, self.bettors), "Bugs Bunny"
        )

    def test_get_paths_to_victory(self):
        paths_to_victory = main.get_paths_to_victory(self.bowls, self.bettors)
        self.assertEqual(256, sum(paths_to_victory.values()))


if __name__ == "__main__":
    unittest.main()
