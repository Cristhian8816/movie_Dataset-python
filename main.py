from src.data import download_data, load_movies
from src.config import GOOGLE_FILE_ID, RAW_DIR
from src.analysis import (
    count_bw_color,
    movies_per_director,
    ten_least_criticized,
    twenty_longest_running,
)

def main():
    # Try Drive, fall back to local data/raw if permissions fail
    try:
        downloaded = download_data(GOOGLE_FILE_ID)
    except Exception as e:
        print("-" * 60)
        print("Download failed (Drive permissions). Using local data/raw instead.")
        print(f"Reason: {e}")
        print("-" * 60)
        downloaded = RAW_DIR

    df, table_path = load_movies(downloaded)
    print("=" * 72)
    print(f"Loaded {len(df):,} rows from: {table_path}")
    print("=" * 72)

    # Q1
    counts, color_col = count_bw_color(df)
    print("\n[Q1] How many Black & White and Color movies are in the list?")
    print(f"Detected color column: {color_col}")
    print(f"  Color:         {counts.get('Color', 0):,}")
    print(f"  Black & White: {counts.get('Black & White', 0):,}")
    print(f"  Unknown:       {counts.get('Unknown', 0):,}")

    # Q2
    counts_df, director_col = movies_per_director(df)
    print("\n[Q2] How many movies were produced by director in the list?")
    if director_col is None or counts_df.empty:
        print("  Could not find a 'director' column.")
    else:
        print(f"Detected director column: {director_col}")
        print(f"  Total unique directors: {len(counts_df):,}")
        print("  Top 10 directors by number of movies:")
        for _, row in counts_df.head(10).iterrows():
            print(f"    {row['director']}: {int(row['movie_count'])}")

    # Q3
    least_df, count_col, title_col = ten_least_criticized(df)
    print("\n[Q3] Which are the 10 less criticized movies in the list?")
    if count_col is None or least_df.empty:
        print("  Could not find a suitable 'critic reviews / reviews / votes' column.")
    else:
        print(f"Detected count column: {count_col} | title column: {title_col}")
        for _, row in least_df.iterrows():
            print(f"    {row['title']}  — {int(row['criticized_count'])}")

    # Q4
    long_df, runtime_col, title_col2 = twenty_longest_running(df)
    print("\n[Q4] Which are the 20 longest-running movies in the list?")
    if runtime_col is None or long_df.empty:
        print("  Could not find a suitable 'runtime/duration' column.")
    else:
        print(f"Detected runtime column: {runtime_col} | title column: {title_col2}")
        for _, row in long_df.iterrows():
            print(f"    {row['title']}  — {row['runtime_min']:.0f} min")

    print("\nDone.")
    print("=" * 72)

if __name__ == "__main__":
    main()
