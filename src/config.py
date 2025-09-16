from pathlib import Path

# Google Drive file id for the dataset (public share link id)
GOOGLE_FILE_ID = "1yjfZurxrTVTTTvEo-Uqkk-21_sqqzD4W"

# Folders
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure folders exist when module is imported
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
