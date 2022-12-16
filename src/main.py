import argparse
import csv
import itertools
from typing import Any, Dict, List, NamedTuple, Set, Tuple

Bowls = Dict[str, Dict[str, Any]]
Bettors = Dict[str, Dict[str, Dict[str, float]]]
Path = Tuple[str, str, str, str, str, str, str, str, str, str]

"""
ipython sample_data/data.csv -i
"""


class Row(NamedTuple):
    bowl: str
    team: str
    bettor: str
    potential_points: float
    actual_points: float
    played: bool
    winner: str


def read_row(row: List[Any]) -> Row:

    return Row(
        row[0],
        row[2],
        row[6],
        float(row[8]),
        float(row[10]),
        True if row[11] == "TRUE" else False,
        row[12]
    )


def read_file(file_name: str) -> Tuple[Bowls, Bettors]:

    bowls = {}
    bettors = {}
    first_row = True

    with open(file_name) as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            if not first_row and r[0]:
                row = read_row(r)

                if row.bowl not in bowls:
                    bowls[row.bowl] = {}
                    bowls[row.bowl]["teams"] = set()

                bowls[row.bowl]["teams"].add(row.team)
                bowls[row.bowl]["played"] = row.played
                bowls[row.bowl]["winner"] = row.winner if row.played else ""

                if row.bettor not in bettors:
                    bettors[row.bettor] = {}

                if row.bowl not in bettors[row.bettor]:
                    bettors[row.bettor][row.bowl] = {}

                bettors[row.bettor][row.bowl][row.team] = (
                    row.actual_points if row.played else row.potential_points
                )

            first_row = False

    return bowls, bettors


def validate_path(path: Path, bowls: Bowls) -> bool:

    non_natty_winners = set()

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["played"]:
            if team != bowls[bowl]["winner"]:
                return False

        if bowl != "Natty":
            non_natty_winners.add(team)
        else:
            natty_winner = team

    return natty_winner in non_natty_winners


def get_winner(path: Path, bettors: Bettors) -> str:

    results = {}

    for bettor, bettor_dict in bettors.items():
        if bettor not in results:
            results[bettor] = 0

        for bowl_team in path:
            bowl, team = bowl_team.split("_")
            results[bettor] += bettor_dict[bowl][team]

    return max(results, key=results.get)


def get_bowl_team_list(bowls: Bowls) -> List[List[str]]:

    out = []

    for bowl, bowl_dict in bowls.items():
        bowl_team = []
        for team in bowl_dict["teams"]:
            bowl_team.append(f"{bowl}_{team}")
        out.append(bowl_team)

    return out


def get_paths_to_victory(bowls: Bowls, bettors: Bettors) -> Dict[str, int]:

    paths_to_victory = {}
    bowl_team_list = get_bowl_team_list(bowls)

    for path in itertools.product(*bowl_team_list):
        if validate_path(path, bowls):
            winner = get_winner(path, bettors)
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
