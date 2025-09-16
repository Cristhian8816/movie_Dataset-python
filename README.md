# Movie Analytics (Starter)

A small Python project to analyze a ~5k+ movies dataset from Google Drive and answer questions.

## Quickstart (Windows / PowerShell)

```powershell
# 1) go to your desired folder (e.g. C:\Users\Hewlett-Packard\Documents\Globant\Python)
# 2) unzip this project here and cd into the folder:
cd .\movie-analytics-starter

# 3) create & activate a virtualenv
python -m venv .venv
.\.venv\Scripts\Activate

# 4) install dependencies
pip install -r requirements.txt

# 5) run the first question (downloads the dataset automatically)
python main.py
```

If you prefer a one-liner for the first run on Windows, you can double–click `scripts\run_first_question.bat`.

## What it does

- Downloads the dataset from Google Drive using its file ID.
- Tries to load CSV/XLSX/TSV/Parquet/JSON (and ZIPs containing those).
- Heuristically detects a "color" column and counts Black & White vs Color movies.
- Prints the counts to the console.

## Project layout

```
movie-analytics-starter/
├─ src/
│  ├─ __init__.py
│  ├─ config.py          # file IDs and folder paths
│  └─ data.py            # download/load/inference utilities
├─ data/
│  ├─ raw/               # big/raw files (git-ignored)
│  └─ processed/         # derived/clean (kept small)
├─ scripts/
│  └─ run_first_question.bat
├─ main.py               # runs the first question
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## Next steps

- We'll add functions for each question and wire them into a CLI.
- We'll also add tests and simple notebooks if needed.
