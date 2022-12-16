import argparse
import csv
import itertools
from typing import Dict, List, Set, Tuple

Bowls = Dict[str, Set[str]]
Bettors = Dict[str, Dict[str, float]]
Picks = Tuple[str, str, str, str, str, str, str, str, str, str]

def read_file(file_name: str) -> Tuple[Bowls, Bettors]:

    bowls = {}
    bettors = {}
    first_row = True

    with open(file_name) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not first_row and row[0]:
                bowl = row[0]
                team = row[2]
                bettor = row[6]
                potential_points = float(row[8])
                pick = f"{bowl}_{team}"

                if bowl not in bowls:
                    bowls[bowl] = set()

                bowls[bowl].add(pick)

                if bettor not in bettors:
                    bettors[bettor] = {}

                bettors[bettor][pick] = potential_points

            first_row = False

    return bowls, bettors


def validate_winning_picks(winning_picks: Picks) -> bool:

    non_natty_winners = set()

    for pick in winning_picks:
        bowl, team = pick.split("_")
        if bowl != "Natty":
            non_natty_winners.add(team)
        else:
            natty_winner = team

    return natty_winner in non_natty_winners


def get_winner(winning_picks: Picks, bettors: Bettors) -> str:

    results = {}

    for bettor, pick_dict in bettors.items():
        if bettor not in results:
            results[bettor] = 0

        for winning_pick in winning_picks:
            results[bettor] += bettors[bettor][winning_pick]

    return max(results, key=results.get)


def get_paths_to_victory(bowls: Bowls, bettors: Bettors) -> Dict[str, int]:

    paths_to_victory = {}

    for winning_picks in itertools.product(*bowls.values()):
        if validate_winning_picks(winning_picks):
            winner = get_winner(winning_picks, bettors)
            if winner not in paths_to_victory:
                paths_to_victory[winner] = 1
            else:
                paths_to_victory[winner] += 1

    return paths_to_victory


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_file_name",
        help="The name of the CSV file to process",
    )
    args = parser.parse_args()

    bowls, bettors = read_file(args.csv_file_name)
    paths_to_victory = get_paths_to_victory(bowls, bettors)
    print(paths_to_victory)
