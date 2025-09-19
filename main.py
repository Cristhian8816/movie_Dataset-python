from src.data import download_data, load_movies
from src.config import GOOGLE_FILE_ID, RAW_DIR
from src.analysis import (
    count_bw_color,
    movies_per_director,
    ten_least_criticized,
    twenty_longest_running,
    top5_gross_highest,
    top5_gross_lowest,
    top3_budget_highest,
    top3_budget_lowest,
    release_year_extrema,
    best_reputation_directors,
    actor_rankings,
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

    # Q5
    top_gross_df, gross_col, tcol = top5_gross_highest(df)
    print("\n[Q5] Top 5 movies that raised more money (highest gross):")
    if gross_col is None or top_gross_df.empty:
        print("  Could not find a 'gross/revenue/box office' column.")
    else:
        print(f"Detected revenue column: {gross_col}")
        for _, row in top_gross_df.iterrows():
            print(f"    {row['title']}  — {int(row['value']):,}")

    # Q6
    low_gross_df, gross_col2, _ = top5_gross_lowest(df)
    print("\n[Q6] Top 5 movies that made the least money:")
    if gross_col2 is None or low_gross_df.empty:
        print("  Could not find a 'gross/revenue/box office' column.")
    else:
        print(f"Detected revenue column: {gross_col2}")
        for _, row in low_gross_df.iterrows():
            print(f"    {row['title']}  — {int(row['value']):,}")

    # Q7
    budget_hi_df, budget_col_hi, _ = top3_budget_highest(df)
    print("\n[Q7] Top 3 movies that cost more to produce (highest budget):")
    if budget_col_hi is None or budget_hi_df.empty:
        print("  Could not find a 'budget' column.")
    else:
        print(f"Detected budget column: {budget_col_hi}")
        for _, row in budget_hi_df.iterrows():
            print(f"    {row['title']}  — {int(row['value']):,}")

    # Q8
    budget_lo_df, budget_col_lo, _ = top3_budget_lowest(df)
    print("\n[Q8] Top 3 movies that cost less to produce (lowest budget):")
    if budget_col_lo is None or budget_lo_df.empty:
        print("  Could not find a 'budget' column.")
    else:
        print(f"Detected budget column: {budget_col_lo}")
        for _, row in budget_lo_df.iterrows():
            print(f"    {row['title']}  — {int(row['value']):,}")

    # Q9
    most_year, most_cnt, least_year, least_cnt, year_col = release_year_extrema(df)
    print("\n[Q9] Year with more movies released / year with less movies released:")
    if year_col is None:
        print("  Could not find a 'year' column.")
    else:
        print(f"Detected year column: {year_col}")
        if most_year is not None:
            print(f"  Most releases:  {most_year} — {most_cnt:,} movies")
        if least_year is not None:
            print(f"  Least releases: {least_year} — {least_cnt:,} movies")

    # Q10
    rep_df, dir_col, rating_col = best_reputation_directors(df, top=5, min_movies=3)
    print("\n[Q10] Top five best reputation directors (by average rating):")
    if dir_col is None or rating_col is None or rep_df.empty:
        print("  Could not compute (need director and rating columns).")
    else:
        print(f"Detected director column: {dir_col} | rating column: {rating_col}")
        for _, r in rep_df.iterrows():
            print(f"    {r['director']}: {r['avg_rating']:.2f} (over {int(r['movies'])} movies)")

    # Q11 (actor rankings)
    by_perf, by_social, best, name_cols, a_rating_col = actor_rankings(df, top=10)
    print("\n[Q11] Actor ranking")
    if not name_cols:
        print("  Could not find actor name columns.")
    else:
        print(f"Detected actor columns: {', '.join(name_cols)}")
        # a) number of movies
        print("  a) By number of movies performed:")
        if by_perf.empty:
            print("    No data.")
        else:
            for _, r in by_perf.iterrows():
                print(f"    {r['actor_name']}: {int(r['movie_count'])}")

        # b) social media influence
        print("  b) By social media influence (max Facebook likes):")
        if by_social.empty:
            print("    No Facebook-like data available.")
        else:
            for _, r in by_social.iterrows():
                print(f"    {r['actor_name']}: {int(r['max_facebook_likes'])}")

        # c) best movie
        print(f"  c) By best movie (highest rating{'' if a_rating_col is None else f' from {a_rating_col}'}):")
        if best.empty:
            print("    No ratings available.")
        else:
            for _, r in best.iterrows():
                print(f"    {r['actor_name']}: \"{r['best_movie']}\" — {r['best_rating']:.1f}")

    print("\nDone.")
    print("=" * 72)

if __name__ == "__main__":
    main()
