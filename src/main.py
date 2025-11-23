import argparse
import csv
import io
import itertools
import os
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

import gspread
import pyperclip
from google.oauth2.service_account import Credentials
from google.auth.exceptions import GoogleAuthError

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
    """Convert a string to boolean. Returns True if string equals 'TRUE', False otherwise."""
    return s == "TRUE"


def convert_to_int(s: str) -> int:
    """Convert a string to integer. Returns 0 if conversion fails."""
    try:
        return int(s)
    except ValueError:
        return 0


def read_picks_row(row: List[Any]) -> PicksFileRow:
    """Parse a row from the picks worksheet into a PicksFileRow named tuple."""
    return PicksFileRow(
        row[0],
        row[2],
        row[6],
        convert_to_int(row[7]),
    )


def read_bowls_row(row: List[Any]) -> BowlsFileRow:
    """Parse a row from the bowls worksheet into a BowlsFileRow named tuple."""
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
    """Parse a row from the multipliers worksheet into a MultipliersFileRow named tuple."""
    return MultipliersFileRow(
        row[0],
        row[1],
        float(row[5]),
        float(row[6]),
    )


def get_google_sheets_client() -> Any:
    """Authenticate and return a Google Sheets client."""
    credentials_path = os.path.expanduser("~/.config/gspread/service_account.json")
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Google Sheets credentials not found at {credentials_path}. "
            "Please set up service account credentials. See README for instructions."
        )
    
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        return gspread.authorize(creds)
    except GoogleAuthError as e:
        raise GoogleAuthError(f"Failed to authenticate with Google Sheets: {e}")


def get_sheet_data(sheet_name: str, worksheet_name: str, client: Optional[Any] = None) -> List[List[str]]:
    """Get data from a specific worksheet in a Google Sheet by name.
    
    The sheet name must match exactly as it appears in Google Sheets, and the sheet
    must be shared with your service account email.
    """
    if client is None:
        client = get_google_sheets_client()
    
    try:
        # gspread searches through all sheets shared with the service account
        # and finds the one with the matching name
        sheet = client.open(sheet_name)
        worksheet = sheet.worksheet(worksheet_name)
        return worksheet.get_all_values()
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError(
            f"Google Sheet '{sheet_name}' not found. "
            "Make sure:\n"
            "  1. The sheet name matches exactly (case-sensitive)\n"
            "  2. The sheet is shared with your service account email"
        )
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(
            f"Worksheet '{worksheet_name}' not found in sheet '{sheet_name}'. "
            f"Make sure you have tabs named 'Picks', 'Multipliers', and 'Bowls'."
        )


def get_multipliers(sheet_name: str, client: Optional[Any] = None) -> Multipliers:
    """Load multipliers data from the 'Multipliers' worksheet.
    
    Returns a dictionary mapping bowl names to teams to their multiplier data.
    """
    multipliers = {}
    rows = get_sheet_data(sheet_name, "Multipliers", client)

    for r in rows[1:]:  # Skip header row
        row = read_multipliers_row(r)
        if row.bowl not in multipliers:
            multipliers[row.bowl] = {}
        multipliers[row.bowl][row.team] = {
            "adjusted_prob": row.adjusted_prob,
            "multiplier": row.multiplier,
        }

    return multipliers


def get_bowls(sheet_name: str, multipliers: Multipliers, client: Optional[Any] = None) -> Bowls:
    """Load bowls data from the 'Bowls' worksheet and merge with multipliers.
    
    Validates that multiplier counts match expected values for each bowl type.
    """
    bowls = {}
    rows = get_sheet_data(sheet_name, "Bowls", client)

    for r in rows[1:]:  # Skip header row
        row = read_bowls_row(r)
        bowls[row.bowl] = {
            "play_in": row.play_in,
            "quarter": row.quarter,
            "semi": row.semi,
            "natty": row.natty,
            "played": row.played,
            "teams": multipliers[row.bowl],
        }

        if row.played:
            assert row.winner
            bowls[row.bowl]["winner"] = row.winner

        # Validate multiplier counts
        if row.play_in:
            assert len(multipliers[row.bowl]) == 2
        if row.quarter:
            assert len(multipliers[row.bowl]) == 3
        if row.semi:
            assert len(multipliers[row.bowl]) == 6
        if row.natty:
            assert len(multipliers[row.bowl]) == 12

    return bowls


def get_picks(sheet_name: str, bowls: Bowls, client: Optional[Any] = None) -> Picks:
    """Load picks data from the 'Picks' worksheet and calculate points for each pick.
    
    For played games, only winning picks get points. For unplayed games, all picks
    get potential points based on their multiplier.
    """
    picks = {}
    rows = get_sheet_data(sheet_name, "Picks", client)

    for r in rows[1:]:  # Skip header row
        if not r[0] or r[0] in SPREADSHEET_DIVIDERS:
            continue

        row = read_picks_row(r)
        if row.bettor not in picks:
            picks[row.bettor] = {}
        if row.bowl not in picks[row.bettor]:
            picks[row.bettor][row.bowl] = {}

        bowl_data = bowls[row.bowl]
        team_data = bowl_data["teams"][row.team]
        
        if bowl_data["played"]:
            points = row.points_wagered * team_data["multiplier"] if row.team == bowl_data["winner"] else 0
        else:
            points = row.points_wagered * team_data["multiplier"]

        picks[row.bettor][row.bowl][row.team] = points

    return picks


def validate_path(path: Path, bowls: Bowls) -> bool:
    """Validate that a path (sequence of bowl_team selections) is logically consistent.
    
    Checks that:
    - Played games match actual winners
    - Teams eliminated in play-in games don't appear in quarterfinals
    - Teams eliminated in quarterfinals don't appear in semis
    - Teams eliminated in semis don't appear in the national championship
    """
    losers = set()

    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["played"]:
            if team != bowls[bowl]["winner"]:
                return False

        # play-in games
        if bowls[bowl]["play_in"]:
            for t in bowls[bowl]["teams"]:
                if t != team:
                    losers.add(t)

    # quarterfinals
    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["quarter"]:
            if team in losers:
                return False

            for t in bowls[bowl]["teams"]:
                if t != team:
                    losers.add(t)

    # semis
    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["semi"]:
            if team in losers:
                return False

            for t in bowls[bowl]["teams"]:
                if t != team:
                    losers.add(t)

    # natty
    for bowl_team in path:
        bowl, team = bowl_team.split("_")

        if bowls[bowl]["natty"]:
            if team in losers:
                return False

    return True


def get_winner(path: Path, picks: Picks) -> Money:
    """Calculate the winner(s) for a given path by summing scores for all bettors.
    
    Returns a Money named tuple with the winner name(s) and their score.
    If multiple bettors tie, they are sorted alphabetically and joined with commas.
    """
    scores = {}
    for bettor, pick_dict in picks.items():
        score = sum(pick_dict[bowl][team] for bowl, team in (bt.split("_") for bt in path))
        scores[bettor] = score

    max_score = max(scores.values())
    winners = sorted([bettor for bettor, score in scores.items() if score == max_score])
    return Money(", ".join(winners), max_score)


def get_bowl_team_list(bowls: Bowls) -> List[List[str]]:
    """Generate a list of all possible bowl_team combinations for each bowl.
    
    Returns a list where each element is a list of bowl_team strings for one bowl.
    Used to generate all possible paths via itertools.product.
    """
    return [[f"{bowl}_{team}" for team in bowl_dict["teams"]] for bowl, bowl_dict in bowls.items()]


def get_play_in_teams(bowls: Bowls) -> Set[str]:
    """Get the set of all teams that participate in play-in games."""
    return {team for bowl in bowls if bowls[bowl]["play_in"] for team in bowls[bowl]["teams"]}


# pyright: ignore [reportReturnType]
def get_team_with_bye(bowl: str, bowls: Bowls) -> str:
    """Find the team in a quarterfinal bowl that has a bye (didn't play in a play-in game).
    
    Quarterfinal bowls have 3 teams: one with a bye and two from play-in games.
    """
    play_in_teams = get_play_in_teams(bowls)
    if not bowls[bowl]["quarter"]:
        raise ValueError(f"The {bowl} Bowl is not a quarterfinal")
    for team in bowls[bowl]["teams"]:
        if team not in play_in_teams:
            return team
    raise ValueError(f"Every team playing in the {bowl} Bowl also has a play-in game")


def get_my_qf(team: str, bowls: Bowls) -> str:
    """Find which quarterfinal bowl a given team participates in."""
    for bowl in bowls:
        if bowls[bowl]["quarter"] and team in bowls[bowl]["teams"]:
            return bowl
    raise ValueError(f"Could not find quarterfinal for {team}")


def get_my_semi(team: str, bowls: Bowls) -> str:
    """Find which semifinal bowl a given team participates in."""
    for bowl in bowls:
        if bowls[bowl]["semi"] and team in bowls[bowl]["teams"]:
            return bowl
    raise ValueError(f"Could not find semi for {team}")


def get_prob(path: Path, bowls: Bowls) -> float:
    """Calculate the probability of a given path occurring.
    
    Handles conditional probabilities for playoff games where teams must advance
    through earlier rounds. For quarterfinals, semis, and natty, probabilities are
    normalized based on which teams actually made it to that round.
    """
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
    """Convert a path tuple to a dictionary mapping bowl names to team names."""
    return {bowl_team.split("_")[0]: bowl_team.split("_")[1] for bowl_team in path}


def get_outcome_dict(path: Path, prob: float, money: Money) -> Dict[str, Any]:
    """Create a dictionary representing a single outcome scenario.
    
    Contains the path (bowl -> team mappings), probability, and winning score.
    """
    return {
        "path": get_path_as_dict(path),
        "prob": prob,
        "winning_score": money.score,
    }


def get_paths_to_victory(bowls: Bowls, picks: Picks) -> Outcome:
    """Generate all valid paths to victory and calculate outcomes for each.
    
    Iterates through all possible combinations of bowl outcomes, validates each path,
    calculates probabilities and winners, and groups outcomes by winning bettor.
    """
    paths_to_victory = {}
    bowl_team_list = get_bowl_team_list(bowls)

    for path in itertools.product(*bowl_team_list):
        if validate_path(path, bowls):
            prob = get_prob(path, bowls)
            winner = get_winner(path, picks)
            if winner.bettor not in paths_to_victory:
                paths_to_victory[winner.bettor] = []
            paths_to_victory[winner.bettor].append(get_outcome_dict(path, prob, winner))

    return paths_to_victory




def get_row(is_first_row: bool, bowl_names: Optional[List[str]] = None, bettor: Optional[str] = None, path_dict: Optional[Dict[str, Any]] = None) -> List[Any]:
    """Generate a row for CSV output.
    
    If is_first_row is True, returns the header row. Otherwise, returns a data row
    with bettor name, winning score, probability, and team selections for each bowl.
    """
    if is_first_row:
        return ["bettor", "winning_score", "prob", *(bowl_names or [])]
    if path_dict is None or bettor is None or bowl_names is None:
        raise ValueError("bettor, path_dict, and bowl_names are required when is_first_row is False")
    return [bettor, path_dict["winning_score"], path_dict["prob"]] + [path_dict["path"][bowl_name] for bowl_name in bowl_names]


def write_to_clipboard(bowls: Bowls, outcome: Outcome) -> None:
    """Write all paths to victory to the clipboard as TSV-formatted text (tab-separated).
    
    Uses TSV format so the data can be easily pasted into Google Sheets, where tabs
    automatically separate into columns. Each row represents one possible outcome scenario
    with the winning bettor(s), their score, probability, and team selections for each bowl.
    """
    bowl_names = sorted(bowls.keys())
    
    # Create TSV in memory (tab-separated values)
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    # Write header row
    writer.writerow(get_row(is_first_row=True, bowl_names=bowl_names))
    
    # Write data rows
    for bettor, path_list in outcome.items():
        for path_dict in path_list:
            writer.writerow(get_row(is_first_row=False, bettor=bettor, path_dict=path_dict, bowl_names=bowl_names))
    
    # Copy to clipboard
    tsv_text = output.getvalue()
    pyperclip.copy(tsv_text)
    print(f"Results copied to clipboard as TSV ({len(tsv_text)} characters)")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate paths to victory for bowl pool bettors using Google Sheets."
    )
    parser.add_argument(
        "sheet_name",
        help="Name of the Google Sheet containing all data (with tabs: Picks, Multipliers, Bowls). "
             "The name must match exactly as it appears in Google Sheets.",
    )
    args = parser.parse_args()

    # Create Google Sheets client once and reuse it
    client = get_google_sheets_client()

    multipliers = get_multipliers(args.sheet_name, client)
    bowls = get_bowls(args.sheet_name, multipliers, client)
    picks = get_picks(args.sheet_name, bowls, client)
    paths_to_victory = get_paths_to_victory(bowls, picks)

    write_to_clipboard(bowls, paths_to_victory)
