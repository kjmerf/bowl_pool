import argparse
import csv
import itertools
import time
from typing import Any, Dict, List, NamedTuple, Set, Tuple

Bowls = Dict[str, Dict[str, Any]]
Multipliers = Dict[str, Dict[str, float]]
Outcome = Dict[str, Dict[str, Any]]
Picks = Dict[str, Dict[str, Dict[str, float]]]
# the length of this tuple should be equal to the number of bowl games
Path = Tuple[str, ...]


SPREADSHEET_DIVIDERS = [
    "Non-playoff games",
    "Play-in games",
    "Quarterfinals",
    "Semis",
    "National Championship",
]


class PicksFileRow(NamedTuple):
    bowl: str
    team: str
    bettor: str
    points_wagered: int


class BowlsFileRow(NamedTuple):
    bowl: str
    winner: str
    played: bool
    play_in: bool
    quarter: bool
    semi: bool
    natty: bool


class MultipliersFileRow(NamedTuple):
    bowl: str
    team: str
    adjusted_prob: float
    multiplier: float


# class for bettors who are in the money
class Money(NamedTuple):
    bettor: str
    score: float


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
        convert_to_bool(row[6]),
        convert_to_bool(row[7]),
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


def get_bowls(bowls_file_name: str, multipliers: Multipliers) -> Bowls:

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

                if row.play_in:
                    assert len(multipliers[row.bowl]) == 2

                if row.quarter:
                    assert len(multipliers[row.bowl]) == 3

                if row.semi:
                    assert len(multipliers[row.bowl]) == 6

                if row.natty:
                    assert len(multipliers[row.bowl]) == 12

                bowls[row.bowl]["play_in"] = row.play_in
                bowls[row.bowl]["quarter"] = row.quarter
                bowls[row.bowl]["semi"] = row.semi
                bowls[row.bowl]["natty"] = row.natty
                bowls[row.bowl]["played"] = row.played
                bowls[row.bowl]["teams"] = multipliers[row.bowl]

            first_row = False

    return bowls


def get_picks(picks_file_name: str, bowls: Bowls) -> Picks:

    picks = {}
    first_row = True

    with open(picks_file_name) as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            if not first_row and r[0] and r[0] not in SPREADSHEET_DIVIDERS:
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
    path: Path,
    bowls: Bowls,
) -> bool:

    losers = set()

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["played"]:
            if team != bowls[bowl]["winner"]:
                return False

        if bowls[bowl]["play_in"]:
            for t in bowls[bowl]["teams"]:
                if t != team:
                    losers.add(t)

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["quarter"]:
            if team in losers:
                return False

            for t in bowls[bowl]["teams"]:
                if t != team:
                    losers.add(t)

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["semi"]:
            if team in losers:
                return False

            for t in bowls[bowl]["teams"]:
                if t != team:
                    losers.add(t)

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["natty"]:
            if team in losers:
                return False

    return True


def get_winner_and_loser(path: Path, picks: Picks) -> Tuple[Money, Money]:

    results = {}
    max_score = 0
    min_score = 10000
    winners = []
    losers = []

    for bettor, pick_dict in picks.items():
        if bettor not in results:
            results[bettor] = {}
            results[bettor]["score"] = 0

        for bowl_team in path:
            bowl, team = bowl_team.split("_")
            score = pick_dict[bowl][team]
            results[bettor]["score"] += score

        if results[bettor]["score"] >= max_score:
            max_score = results[bettor]["score"]

        if results[bettor]["score"] <= min_score:
            min_score = results[bettor]["score"]

    for bettor, stats in results.items():

        if stats["score"] == max_score:
            winners.append(bettor)

        if stats["score"] == min_score:
            losers.append(bettor)

        if len(winners) > 1:
            winners.sort()

        if len(losers) > 1:
            losers.sort()

    return Money(", ".join(winners), max_score), Money(", ".join(losers), min_score)


def get_bowl_team_list(bowls: Bowls) -> List[List[str]]:

    bowl_team_list = []

    for bowl, bowl_dict in bowls.items():
        btl = []
        for team in bowl_dict["teams"]:
            btl.append(f"{bowl}_{team}")
        bowl_team_list.append(btl)

    return bowl_team_list


def get_play_in_teams(bowls: Bowls) -> Set[str]:

    play_in_teams = set()

    for bowl in bowls:
        if bowls[bowl]["play_in"]:
            for team in bowls[bowl]["teams"]:
                play_in_teams.add(team)

    return play_in_teams


# pyright: ignore [reportReturnType]
def get_team_with_bye(bowl: str, bowls: Bowls) -> str:

    play_in_teams = get_play_in_teams(bowls)

    if not bowls[bowl]["quarter"]:
        raise ValueError(f"The {bowl} Bowl is not a quarterfinal")

    for team in bowls[bowl]["teams"]:
        if team not in play_in_teams:
            return team

    raise ValueError(f"Every team playing in the {bowl} Bowl also has a play-in game")


def get_my_qf(team: str, bowls: Bowls) -> str:

    for bowl in bowls:
        if bowls[bowl]["quarter"]:
            if team in bowls[bowl]["teams"]:
                return bowl

    raise ValueError(f"Could not find quarterfinal for {team}")


def get_my_semi(team: str, bowls: Bowls) -> str:

    for bowl in bowls:
        if bowls[bowl]["semi"]:
            if team in bowls[bowl]["teams"]:
                return bowl

    raise ValueError(f"Could not find semi for {team}")


def get_prob(
    path: Path,
    bowls: Bowls,
) -> float:

    qf_teams = {}
    semi_teams = {}
    natty_teams = []
    prob = 1.0

    for bowl in bowls:
        if bowls[bowl]["quarter"]:
            qf_teams[bowl] = [get_team_with_bye(bowl, bowls)]

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        # non-playoff games
        if (
            not bowls[bowl]["play_in"]
            and not bowls[bowl]["quarter"]
            and not bowls[bowl]["semi"]
            and not bowls[bowl]["natty"]
        ):

            if not bowls[bowl]["played"]:
                prob *= bowls[bowl]["teams"][team]["adjusted_prob"]

        # play-in games
        if bowls[bowl]["play_in"]:

            if not bowls[bowl]["played"]:
                prob *= bowls[bowl]["teams"][team]["adjusted_prob"]

            qf_bowl = get_my_qf(team, bowls)
            qf_teams[qf_bowl].append(team)

    # quarterfinals
    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["quarter"]:

            if not bowls[bowl]["played"]:

                total_prob_qf = 0.0
                for qf_team in qf_teams[bowl]:
                    total_prob_qf += bowls[bowl]["teams"][qf_team]["adjusted_prob"]

                prob *= bowls[bowl]["teams"][team]["adjusted_prob"] / total_prob_qf

            semi_bowl = get_my_semi(team, bowls)

            if semi_bowl not in semi_teams:
                semi_teams[semi_bowl] = [team]
            else:
                semi_teams[semi_bowl].append(team)

    # semis
    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["semi"]:

            if not bowls[bowl]["played"]:
                total_prob_semi = 0.0
                for semi_team in semi_teams[bowl]:
                    total_prob_semi += bowls[bowl]["teams"][semi_team]["adjusted_prob"]

                prob *= bowls[bowl]["teams"][team]["adjusted_prob"] / total_prob_semi

            natty_teams.append(team)

    # natty
    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["natty"]:

            if not bowls[bowl]["played"]:
                total_prob_natty = 0.0
                for natty_team in natty_teams:
                    total_prob_natty += bowls[bowl]["teams"][natty_team][
                        "adjusted_prob"
                    ]

                prob *= bowls[bowl]["teams"][team]["adjusted_prob"] / total_prob_natty

    return prob


def get_path_as_dict(path: Path) -> Dict[str, str]:

    path_as_dict = {}
    for bowl_team in path:
        bowl, team = bowl_team.split("_")
        path_as_dict[bowl] = team

    return path_as_dict


def get_outcome_dict(path: Path, prob: float, money: Money) -> Dict[str, Any]:

    return {
        "path": get_path_as_dict(path),
        "prob": prob,
        "winning_score": money.score,
    }


def get_outcomes(bowls: Bowls, picks: Picks) -> Tuple[Outcome, Outcome]:

    paths_to_victory = {}
    paths_to_defeat = {}
    bowl_team_list = get_bowl_team_list(bowls)

    for path in itertools.product(*bowl_team_list):
        if validate_path(path, bowls):
            prob = get_prob(
                path,
                bowls,
            )
            winner, loser = get_winner_and_loser(path, picks)

            if winner.bettor not in paths_to_victory:
                paths_to_victory[winner.bettor] = []

            outcome_dict_winner = get_outcome_dict(path, prob, winner)
            paths_to_victory[winner.bettor].append(outcome_dict_winner)

            if loser.bettor not in paths_to_defeat:
                paths_to_defeat[loser.bettor] = []

            outcome_dict_loser = get_outcome_dict(path, prob, loser)
            paths_to_defeat[loser.bettor].append(outcome_dict_loser)

    return paths_to_victory, paths_to_defeat


def get_output_file_name(epoch_time: int, winners: bool) -> str:

    if winners:
        suffix = "winners"
    else:
        suffix = "losers"

    return f"/tmp/bowl_pool_{epoch_time}_{suffix}.csv"


def get_row(**kwargs) -> List[Any]:

    if kwargs["is_first_row"]:
        return [
            "bettor",
            "winning_score",
            "prob",
            *kwargs["bowl_names"],
        ]
    else:
        path_dict = kwargs["path_dict"]
        row = []
        row.append(kwargs["bettor"])
        row.append(path_dict["winning_score"])
        row.append(path_dict["prob"])

        for bowl_name in kwargs["bowl_names"]:
            row.append(path_dict["path"][bowl_name])

        return row


def write_to_file(bowls: Bowls, outcome: Outcome, output_file_name: str) -> None:

    bowl_names = list(bowls.keys())
    bowl_names.sort()

    with open(output_file_name, "w") as csv_file:
        writer = csv.writer(csv_file)
        first_row = get_row(is_first_row=True, bowl_names=bowl_names)
        writer.writerow(first_row)

        for bettor, path_list in outcome.items():
            for path_dict in path_list:
                row = get_row(
                    bettor=bettor,
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
        "--output_file_name_winners",
        help="The name of the CSV file that contains the winners",
    )
    parser.add_argument(
        "--output_file_name_losers",
        help="The name of the CSV file that contains the losers",
    )
    args = parser.parse_args()

    multipliers = get_multipliers(args.multipliers_file_name)
    bowls = get_bowls(args.bowls_file_name, multipliers)
    picks = get_picks(args.picks_file_name, bowls)
    paths_to_victory, paths_to_defeat = get_outcomes(bowls, picks)

    epoch_time = int(time.time())

    if args.output_file_name_winners:
        output_file_name_winners = args.output_file_name_winners
    else:
        output_file_name_winners = get_output_file_name(epoch_time, True)

    if args.output_file_name_losers:
        output_file_name_losers = args.output_file_name_winners
    else:
        output_file_name_losers = get_output_file_name(epoch_time, False)

    write_to_file(bowls, paths_to_victory, output_file_name_winners)
    write_to_file(bowls, paths_to_defeat, output_file_name_losers)
