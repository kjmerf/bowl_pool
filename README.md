# Bowl Pool

Given Google Sheets with picks by bettors, you can use this repo to generate the paths to victory for each bettor.

## Setup

### Virtual Environment (Recommended)

It's recommended to use a virtual environment to isolate the project dependencies:

1. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate the virtual environment:**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **When you're done working, deactivate the virtual environment:**
   ```bash
   deactivate
   ```

### Installation (Without Virtual Environment)

If you prefer not to use a virtual environment, you can install dependencies directly:

```bash
pip install -r requirements.txt
```

## Google Sheets Setup

You need to set up authentication to access Google Sheets:

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google APIs**:
   - In the Google Cloud Console, go to "APIs & Services" > "Library"
   - Search for and enable both:
     - "Google Sheets API"
     - "Google Drive API" (required to search for sheets by name)

3. **Create a Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Give it a name (e.g., "bowl-pool-reader") and create it
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key" > Choose "JSON"
   - Download the JSON file

4. **Set up credentials**:
   - Create the directory: `mkdir -p ~/.config/gspread`
   - Move the downloaded JSON file to: `~/.config/gspread/service_account.json`

5. **Share your Google Sheet with the service account**:
   - Open your Google Sheet (the one containing all your data)
   - Click "Share" button
   - Add the service account email (found in the JSON file, looks like `your-service-account@project-id.iam.gserviceaccount.com`)
   - Give it "Viewer" permissions

## Usage

Your Google Sheet should have three tabs named exactly:
- **Picks** - contains the picks data
- **Multipliers** - contains the multipliers data
- **Bowls** - contains the bowls data

Run the script with the **exact name** of your Google Sheet (as it appears in Google Sheets):

```bash
python3 src/main.py "Bowl Pool 2025"
```

**Important:** The sheet name must match exactly (including capitalization and spaces). The script searches through all sheets shared with your service account to find the one with that name.

## Output

The output is a CSV file with every possible outcome including the winner for each scenario. The file is saved to `/tmp/bowl_pool_[timestamp].csv` and automatically opened.

## Testing

To run the unit tests:
```bash
python3 -m unittest discover
```

Note: The tests use mocking to simulate Google Sheets API calls and read test data from the `sample_data` directory. No actual Google Sheets credentials are required to run the tests.
