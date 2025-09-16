from src.data import download_data, load_movies, count_bw_color
from src.config import GOOGLE_FILE_ID, RAW_DIR

def main():
    # Try to download; if it fails (permissions/connection), use local data/raw
    try:
        downloaded = download_data(GOOGLE_FILE_ID)
    except Exception as e:
        print("-" * 60)
        print("Download failed (likely Drive permissions). Falling back to local file in data/raw.")
        print(f"Reason: {e}")
        print("-" * 60)
        downloaded = RAW_DIR  # this will make load_movies() scan data/raw for the first table file

    # Load and answer Q1
    df, table_path = load_movies(downloaded)
    counts, col = count_bw_color(df)

    print("-" * 60)
    print(f"Loaded {len(df):,} rows from: {table_path}")
    print(f"Detected color column: {col}")
    print("Counts (Color vs Black & White):")
    print(f"  Color:           {counts.get('Color', 0):,}")
    print(f"  Black & White:   {counts.get('Black & White', 0):,}")
    print(f"  Unknown/Other:   {counts.get('Unknown', 0):,}")
    print("-" * 60)

if __name__ == "__main__":
    main()
