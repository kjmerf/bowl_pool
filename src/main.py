import argparse
import csv
import itertools
import time
from typing import Any, Dict, List, NamedTuple, Set, Tuple

Bowls = Dict[str, Dict[str, Any]]
Multipliers = Dict[str, Dict[str, float]]
Picks = Dict[str, Dict[str, Dict[str, float]]]
Path = Tuple[str, str, str, str, str, str, str, str, str, str]
PathsToVictory = Dict[str, Dict[str, Any]]


class PicksFileRow(NamedTuple):
    bowl: str
    team: str
    bettor: str
    points_wagered: int


class BowlsFileRow(NamedTuple):
    bowl: str
    winner: str
    played: bool
    semi: bool
    natty: bool


class MultipliersFileRow(NamedTuple):
    bowl: str
    team: str
    adjusted_prob: float
    multiplier: float


def convert_to_bool(s: str) -> bool:

    return s == "TRUE"

def convert_to_int(s: str) -> int:

    try:
        return int(s)
    except ValueError:
        return 0


def read_picks_row(row: List[Any]) -> PicksFileRow:

    return PicksFileRow(
        row[0],
        row[2],
        row[6],
        convert_to_int(row[7]),
    )


def read_bowls_row(row: List[Any]) -> BowlsFileRow:

    return BowlsFileRow(
        row[0],
        row[2],
        convert_to_bool(row[3]),
        convert_to_bool(row[4]),
        convert_to_bool(row[5]),
    )


def read_multipliers_row(row: List[Any]) -> MultipliersFileRow:

    return MultipliersFileRow(
        row[0],
        row[1],
        float(row[5]),
        float(row[6]),
    )


def get_multipliers(multipliers_file_name: str) -> Multipliers:

    multipliers = {}
    first_row = True

    with open(multipliers_file_name) as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            if not first_row:
                row = read_multipliers_row(r)

                if row.bowl not in multipliers:
                    multipliers[row.bowl] = {}

                multipliers[row.bowl][row.team] = {}
                multipliers[row.bowl][row.team]["adjusted_prob"] = row.adjusted_prob
                multipliers[row.bowl][row.team]["multiplier"] = row.multiplier

            first_row = False

    return multipliers


def get_bowls(bowls_file_name: str, multipliers: Dict[str, str]) -> Bowls:

    bowls = {}
    first_row = True

    with open(bowls_file_name) as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            if not first_row:
                row = read_bowls_row(r)
                bowls[row.bowl] = {}

                if row.played:
                    assert row.winner
                    bowls[row.bowl]["winner"] = row.winner

                if row.natty:
                    assert len(multipliers[row.bowl]) == 4
                else:
                    assert len(multipliers[row.bowl]) == 2

                bowls[row.bowl]["semi"] = row.semi
                bowls[row.bowl]["natty"] = row.natty
                bowls[row.bowl]["played"] = row.played
                bowls[row.bowl]["teams"] = multipliers[row.bowl]

            first_row = False

    return bowls


def get_picks(picks_file_name: str, bowls: Bowls) -> Tuple[Bowls, Picks]:

    picks = {}
    first_row = True

    with open(picks_file_name) as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            if not first_row and r[0]:
                row = read_picks_row(r)

                if row.bettor not in picks:
                    picks[row.bettor] = {}

                if row.bowl not in picks[row.bettor]:
                    picks[row.bettor][row.bowl] = {}

                if bowls[row.bowl]["played"]:
                    if row.team == bowls[row.bowl]["winner"]:
                        points = (
                            row.points_wagered
                            * bowls[row.bowl]["teams"][row.team]["multiplier"]
                        )
                    else:
                        points = 0
                else:
                    points = (
                        row.points_wagered
                        * bowls[row.bowl]["teams"][row.team]["multiplier"]
                    )

                picks[row.bettor][row.bowl][row.team] = points

            first_row = False

    return picks


def validate_path(
    path: Path, bowls: Bowls, natty_bowl_name: str, semi_bowl_names: Set[str]
) -> bool:

    semi_losers = set()

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["played"]:
            if team != bowls[bowl]["winner"]:
                return False

        if bowl in semi_bowl_names:
            for t in bowls[bowl]["teams"]:
                if t != team:
                    semi_losers.add(t)

        if bowl == natty_bowl_name:
            natty_winner = team

    return natty_winner not in semi_losers


def check_for_tie(results: Dict[str, Dict[str, Any]], max_score: float) -> bool:

    winners = []

    for bettor, results_dict in results.items():
        if results_dict["score"] == max_score:
            winners.append(bettor)

    return len(winners) > 1


def get_winner(path: Path, picks: Picks) -> Tuple[str, float, int]:

    results = {}
    max_score = 0

    for bettor, pick_dict in picks.items():
        if bettor not in results:
            results[bettor] = {}
            results[bettor]["correct_picks"] = 0
            results[bettor]["score"] = 0

        for bowl_team in path:
            bowl, team = bowl_team.split("_")
            score = pick_dict[bowl][team]
            results[bettor]["correct_picks"] += 1 if score > 0 else 0
            results[bettor]["score"] += score

        if results[bettor]["score"] >= max_score:
            max_score = results[bettor]["score"]
            winner = bettor

    assert not check_for_tie(results, max_score)

    return winner, max_score, results[winner]["correct_picks"]


def get_bowl_team_list(bowls: Bowls) -> List[List[str]]:

    bowl_team_list = []

    for bowl, bowl_dict in bowls.items():
        btl = []
        for team in bowl_dict["teams"]:
            btl.append(f"{bowl}_{team}")
        bowl_team_list.append(btl)

    return bowl_team_list


def get_prob(
    path: Path, bowls: Bowls, natty_bowl_name: str, semi_bowl_names: Set[str]
) -> Dict[str, Any]:

    prob = 1.0
    semi_prob = 0.0
    semi_winners = {}

    for bowl_team in path:
        bowl, team = bowl_team.split("_")
        if bowl != natty_bowl_name:
            if not bowls[bowl]["played"]:
                prob *= bowls[bowl]["teams"][team]["adjusted_prob"]
        else:
            natty_winner = team

        if bowl in semi_bowl_names:
            semi_winners[bowl] = team

    if not bowls[natty_bowl_name]["played"]:
        for semi_bowl in semi_bowl_names:
            semi_winner = semi_winners[semi_bowl]
            semi_prob += bowls[natty_bowl_name]["teams"][semi_winner]["adjusted_prob"]

        prob *= (
            bowls[natty_bowl_name]["teams"][natty_winner]["adjusted_prob"] / semi_prob
        )

    return prob


def get_path_as_dict(path: Path) -> Dict[str, str]:

    path_as_dict = {}
    for bowl_team in path:
        bowl, team = bowl_team.split("_")
        path_as_dict[bowl] = team

    return path_as_dict


def get_playoffs(bowls: Bowls) -> Tuple[str, Set[str]]:

    semi_bowl_names = set()

    for bowl, bowl_dict in bowls.items():
        if bowl_dict["semi"]:
            semi_bowl_names.add(bowl)
        elif bowl_dict["natty"]:
            natty_bowl_name = bowl

    assert len(semi_bowl_names) == 2

    return natty_bowl_name, semi_bowl_names


def get_paths_to_victory(bowls: Bowls, picks: Picks) -> PathsToVictory:

    paths_to_victory = {}
    bowl_team_list = get_bowl_team_list(bowls)
    natty_bowl_name, semi_bowl_names = get_playoffs(bowls)

    for path in itertools.product(*bowl_team_list):
        if validate_path(path, bowls, natty_bowl_name, semi_bowl_names):
            prob = get_prob(path, bowls, natty_bowl_name, semi_bowl_names)
            winner, winning_score, correct_picks = get_winner(path, picks)

            if winner not in paths_to_victory:
                paths_to_victory[winner] = []

            path_dict = {
                "path": get_path_as_dict(path),
                "prob": prob,
                "winning_score": winning_score,
                "correct_picks": correct_picks,
            }
            paths_to_victory[winner].append(path_dict)

    return paths_to_victory


def get_output_file_name() -> str:

    epoch_time = int(time.time())
    return f"/tmp/bowl_pool_{epoch_time}.csv"


def get_row(**kwargs) -> List[Any]:

    if kwargs["is_first_row"]:
        return [
            "winner",
            "winning_score",
            "correct_picks",
            "prob",
            *kwargs["bowl_names"],
        ]
    else:
        path_dict = kwargs["path_dict"]
        row = []
        row.append(kwargs["winner"])
        row.append(path_dict["winning_score"])
        row.append(path_dict["correct_picks"])
        row.append(path_dict["prob"])

        for bowl_name in kwargs["bowl_names"]:
            row.append(path_dict["path"][bowl_name])

        return row


def write_to_file(
    bowls: Bowls, paths_to_victory: PathsToVictory, output_file_name: str
) -> None:

    bowl_names = list(bowls.keys())
    bowl_names.sort()

    with open(output_file_name, "w") as csv_file:
        writer = csv.writer(csv_file)
        first_row = get_row(is_first_row=True, bowl_names=bowl_names)
        writer.writerow(first_row)

        for winner, path_list in paths_to_victory.items():
            for path_dict in path_list:
                row = get_row(
                    winner=winner,
                    path_dict=path_dict,
                    bowl_names=bowl_names,
                    is_first_row=False,
                )
                writer.writerow(row)

    print(output_file_name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "picks_file_name",
        help="The name of the CSV file containing information about the picks",
    )
    parser.add_argument(
        "multipliers_file_name",
        help="The name of the CSV file containing information about the multipliers",
    )
    parser.add_argument(
        "bowls_file_name",
        help="The name of the CSV file containing information about the bowls",
    )
    parser.add_argument(
        "--output_file_name",
        help="The name of the CSV file to be written",
    )
    args = parser.parse_args()

    multipliers = get_multipliers(args.multipliers_file_name)
    bowls = get_bowls(args.bowls_file_name, multipliers)
    picks = get_picks(args.picks_file_name, bowls)
    paths_to_victory = get_paths_to_victory(bowls, picks)

    if args.output_file_name:
        output_file_name = args.output_file_name
    else:
        output_file_name = get_output_file_name()

    write_to_file(bowls, paths_to_victory, output_file_name)
