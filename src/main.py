import argparse
import csv
import itertools
from typing import Any, Dict, List, NamedTuple, Set, Tuple

Bowls = Dict[str, Dict[str, Any]]
Bettors = Dict[str, Dict[str, Dict[str, float]]]
Path = Tuple[str, str, str, str, str, str, str, str, str, str]
PathsToVictory = Dict[str, Dict[str, Any]]


class Row(NamedTuple):
    bowl: str
    team: str
    adjusted_prob: float
    bettor: str
    potential_points: float
    actual_points: float
    played: bool
    is_playoff: bool
    is_natty: bool
    winner: str


def convert_to_bool(s: str) -> bool:

    return True if s == "TRUE" else False


def read_row(row: List[Any]) -> Row:

    return Row(
        row[0],
        row[2],
        float(row[4]),
        row[6],
        float(row[8]),
        float(row[10]),
        convert_to_bool(row[11]),
        convert_to_bool(row[12]),
        convert_to_bool(row[13]),
        row[14],
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
                    bowls[row.bowl]["teams"] = {}
                    bowls[row.bowl]["played"] = row.played
                    bowls[row.bowl]["is_playoff"] = row.is_playoff
                    bowls[row.bowl]["is_natty"] = row.is_natty

                bowls[row.bowl]["teams"][row.team] = row.adjusted_prob

                if row.played:
                    assert row.winner
                    bowls[row.bowl]["winner"] = row.winner

                if row.bettor not in bettors:
                    bettors[row.bettor] = {}

                if row.bowl not in bettors[row.bettor]:
                    bettors[row.bettor][row.bowl] = {}

                bettors[row.bettor][row.bowl][row.team] = (
                    row.actual_points if row.played else row.potential_points
                )

            first_row = False

    return bowls, bettors


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


def get_winner(path: Path, bettors: Bettors) -> Tuple[str, float, int]:

    results = {}
    max_score = 0

    for bettor, bettor_dict in bettors.items():
        if bettor not in results:
            results[bettor] = {}
            results[bettor]["correct_picks"] = 0
            results[bettor]["score"] = 0

        for bowl_team in path:
            bowl, team = bowl_team.split("_")
            score = bettor_dict[bowl][team]
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
                prob *= bowls[bowl]["teams"][team]
        else:
            natty_winner = team

        if bowl in semi_bowl_names:
            semi_winners[bowl] = team

    if not bowls[natty_bowl_name]["played"]:
        for semi_bowl in semi_bowl_names:
            semi_winner = semi_winners[semi_bowl]
            semi_prob += bowls[natty_bowl_name]["teams"][semi_winner]

        prob *= bowls[natty_bowl_name]["teams"][natty_winner] / semi_prob

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
        if bowl_dict["is_playoff"]:
            if bowl_dict["is_natty"]:
                natty_bowl_name = bowl
            else:
                semi_bowl_names.add(bowl)

    assert len(semi_bowl_names) == 2

    return natty_bowl_name, semi_bowl_names


def get_paths_to_victory(bowls: Bowls, bettors: Bettors) -> PathsToVictory:

    paths_to_victory = {}
    bowl_team_list = get_bowl_team_list(bowls)
    natty_bowl_name, semi_bowl_names = get_playoffs(bowls)

    for path in itertools.product(*bowl_team_list):
        if validate_path(path, bowls, natty_bowl_name, semi_bowl_names):
            prob = get_prob(path, bowls, natty_bowl_name, semi_bowl_names)
            winner, winning_score, correct_picks = get_winner(path, bettors)

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


def get_output_file_name(csv_file_name: str) -> str:

    file_name_suffix = csv_file_name.split("/")[-1]
    return f"/tmp/{file_name_suffix}"


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
    bowls: Bowls, paths_to_victory: PathsToVictory, csv_file_name: str
) -> None:

    file_name = get_output_file_name(csv_file_name)
    bowl_names = list(bowls.keys())
    bowl_names.sort()

    with open(file_name, "w") as csv_file:
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

    print(file_name)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_file_name",
        help="The name of the CSV file to process",
    )
    args = parser.parse_args()

    bowls, bettors = read_file(args.csv_file_name)
    paths_to_victory = get_paths_to_victory(bowls, bettors)
    write_to_file(bowls, paths_to_victory, args.csv_file_name)
