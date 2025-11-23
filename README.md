# Bowl Pool

Calculates all possible paths to victory for bowl pool bettors. Reads data from Google Sheets and copies results to the clipboard as TSV-formatted text with every possible outcome scenario, including probabilities and winners.

## Requirements

- Python 3
- Google Sheets with three tabs: **Picks**, **Multipliers**, and **Bowls**
- Google service account credentials at `~/.config/gspread/service_account.json`
- Google Sheet shared with your service account email

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 src/main.py "My Bowl Pool Sheet"
```

Replace `"My Bowl Pool Sheet"` with the exact name of your Google Sheet (case-sensitive).

The script reads from three tabs in your sheet:
- **Picks** - bettor picks and points wagered
- **Multipliers** - team multipliers and adjusted probabilities
- **Bowls** - bowl information and game status

Results are copied to your clipboard as TSV-formatted text (tab-separated values). You can paste them directly into Google Sheets, where tabs will automatically separate into columns.

## Testing

```bash
python3 -m unittest discover
```
