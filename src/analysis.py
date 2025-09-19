import re
from typing import Optional, Tuple, List
import numpy as np
import pandas as pd

# ----------------- generic helpers -----------------
def _find_col(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Pick the column whose name matches any regex in patterns, preferring the least-null one."""
    pats = [re.compile(p, re.I) for p in patterns]
    cands = [c for c in df.columns if any(p.search(str(c)) for p in pats)]
    if not cands:
        return None
    return max(cands, key=lambda c: df[c].notna().sum())

def _title_col(df: pd.DataFrame) -> str:
    return _find_col(df, [r"^title$", r"movie[_\s]?title", r"\btitle\b", r"movie", r"name$"]) or df.columns[0]

def _to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

# ----------------- Q1: Color vs Black & White -----------------
def _infer_color_column(df: pd.DataFrame) -> Optional[str]:
    return _find_col(df, [r"\bcolor\b", r"b(?:lack)?.*white", r"b&w"])

def _standardize_color_series(df: pd.DataFrame, col: str) -> pd.Series:
    # string ops must use .str.<method>
    s = df[col].astype(str).str.strip().str.lower()

    def map_value(x: str) -> str:
        if x in ("", "nan", "none", "null"):
            return "Unknown"
        if "black" in x and "white" in x:
            return "Black & White"
        if "b&w" in x or "b/w" in x or x == "bw":
            return "Black & White"
        if "mono" in x or "grayscale" in x or "greyscale" in x:
            return "Black & White"
        if "color" in x or "colour" in x or "colorized" in x:
            return "Color"
        return "Unknown"

    return s.map(map_value)

def count_bw_color(df: pd.DataFrame):
    """Return (counts_dict, detected_color_column)."""
    col = _infer_color_column(df)
    if col is None:
        return {"Black & White": 0, "Color": 0, "Unknown": len(df)}, None
    mapped = _standardize_color_series(df, col)
    counts = mapped.value_counts(dropna=False).to_dict()
    for k in ["Black & White", "Color", "Unknown"]:
        counts.setdefault(k, 0)
    return counts, col

# ----------------- Q2: Movies per director -----------------
def movies_per_director(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    col = _find_col(df, [r"director"])
    if col is None:
        return pd.DataFrame(columns=["director", "movie_count"]), None
    s = df[col].dropna().astype(str)
    s = s.str.replace(r"\s+and\s+", ",", regex=True).str.replace(r"[\/\|&;]", ",", regex=True)
    exploded = s.str.split(",").explode().str.strip()
    exploded = exploded[exploded != ""]
    counts = exploded.value_counts().rename_axis("director").reset_index(name="movie_count")
    return counts, col

# ----------------- Q3: 10 least criticized movies -----------------
def ten_least_criticized(df: pd.DataFrame):
    title_col = _title_col(df)
    count_col = _find_col(df, [
        r"critic.*review", r"num.*critic", r"reviews? \(critic\)", r"critic_reviews", r"metacritic.*reviews"
    ]) or _find_col(df, [r"\breviews?\b", r"review_count", r"num_reviews"]) \
      or _find_col(df, [r"\bvotes?\b", r"imdb.*votes", r"user.*votes"])
    if count_col is None:
        return pd.DataFrame(columns=[title_col, "criticized_count"]), None, title_col

    counts = _to_numeric(df[count_col])
    res = (df.assign(_count=counts)[[title_col, "_count"]]
             .dropna(subset=["_count"])
             .sort_values("_count", ascending=True)
             .head(10)
             .rename(columns={title_col: "title", "_count": "criticized_count"}))
    return res, count_col, title_col

# ----------------- Q4: 20 longest-running movies -----------------
_RUNTIME_PATS = [r"runtime", r"duration", r"length", r"running.?time", r"mins?", r"minutes?", r"time$"]

def _to_minutes(v) -> float:
    if pd.isna(v): return np.nan
    s = str(v).strip().lower()
    # number directly in minutes
    try:
        f = float(s)
        if f > 0:
            return f
    except ValueError:
        pass
    # '150 min' / '150m'
    m = re.search(r"(\d+(\.\d+)?)\s*(mins?|minutes?|m)\b", s)
    if m:
        return float(m.group(1))
    # '2h 30m'
    hm = re.search(r"(\d+)\s*h(?:ours?)?\s*(\d+)?\s*(m|mins?|minutes?)?", s)
    if hm:
        h = float(hm.group(1)); mm = float(hm.group(2) or 0)
        return h * 60 + mm
    # '1:45' or '02:30:00'
    if ":" in s:
        parts = s.split(":")
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            nums = [0.0] * len(parts)
        if len(nums) == 3:   # hh:mm:ss
            return nums[0] * 60 + nums[1]
        if len(nums) == 2:   # hh:mm
            return nums[0] * 60 + nums[1]
    return np.nan

def twenty_longest_running(df: pd.DataFrame):
    title_col = _title_col(df)
    runtime_col = _find_col(df, _RUNTIME_PATS)
    if runtime_col is None:
        return pd.DataFrame(columns=[title_col, "runtime_min"]), None, title_col
    minutes = df[runtime_col].map(_to_minutes)
    res = (df.assign(_runtime_min=minutes)[[title_col, "_runtime_min"]]
             .dropna(subset=["_runtime_min"])
             .sort_values("_runtime_min", ascending=False)
             .head(20)
             .rename(columns={title_col: "title", "_runtime_min": "runtime_min"}))
    return res, runtime_col, title_col

# ----------------- Q5/Q6: Gross (revenue) & Budget tops/bottoms -----------------
def _top_n_by_metric(df: pd.DataFrame, patterns: List[str], n: int, smallest: bool = False):
    title_col = _title_col(df)
    metric_col = _find_col(df, patterns)
    if metric_col is None:
        return pd.DataFrame(columns=[title_col, "value"]), None, title_col
    v = _to_numeric(df[metric_col])
    res = (df.assign(_val=v)[[title_col, "_val"]]
             .dropna(subset=["_val"])
             .sort_values("_val", ascending=smallest)
             .head(n)
             .rename(columns={title_col: "title", "_val": "value"}))
    return res, metric_col, title_col

def top5_gross_highest(df: pd.DataFrame):
    return _top_n_by_metric(df, [r"\bgross\b", r"revenue", r"box.?office", r"world.*gross", r"domestic.*gross"], 5, smallest=False)

def top5_gross_lowest(df: pd.DataFrame):
    return _top_n_by_metric(df, [r"\bgross\b", r"revenue", r"box.?office", r"world.*gross", r"domestic.*gross"], 5, smallest=True)

def top3_budget_highest(df: pd.DataFrame):
    return _top_n_by_metric(df, [r"\bbudget\b", r"production.*budget", r"cost"], 3, smallest=False)

def top3_budget_lowest(df: pd.DataFrame):
    return _top_n_by_metric(df, [r"\bbudget\b", r"production.*budget", r"cost"], 3, smallest=True)

# ----------------- Q7/Q8: Release year with most/least movies -----------------
def release_year_extrema(df: pd.DataFrame):
    year_col = _find_col(df, [r"\btitle[_\s]?year\b", r"release.*year", r"\byear\b"])
    if year_col is None:
        return None, None, None, None, None
    years = _to_numeric(df[year_col]).dropna().astype(int)
    if years.empty:
        return None, None, None, None, year_col
    counts = years.value_counts().sort_index()  # counts per year
    most_year = int(counts.idxmax())
    most_count = int(counts.max())
    least_year = int(counts.idxmin())
    least_count = int(counts.min())
    return most_year, most_count, least_year, least_count, year_col

# ----------------- Q9: Top five best-reputation directors -----------------
def best_reputation_directors(df: pd.DataFrame, top: int = 5, min_movies: int = 3):
    director_col = _find_col(df, [r"director"])
    rating_col = _find_col(df, [r"imdb.*score", r"\brating\b", r"\bscore\b", r"metascore", r"metacritic", r"tomato.*meter"])
    if director_col is None or rating_col is None:
        return pd.DataFrame(columns=["director", "avg_rating", "movies"]), director_col, rating_col

    ratings = _to_numeric(df[rating_col])
    grp = (df.assign(_rating=ratings)
             .dropna(subset=["_rating"])
             .groupby(director_col)["_rating"]
             .agg(avg_rating="mean", movies="count")
             .reset_index()
             .rename(columns={director_col: "director"}))

    # Require a reasonable body of work; relax if needed
    cur_min = min_movies
    while cur_min >= 1:
        subset = grp[grp["movies"] >= cur_min]
        if len(subset) >= top or cur_min == 1:
            break
        cur_min -= 1

    res = subset.sort_values(["avg_rating", "movies"], ascending=[False, False]).head(top)
    return res, director_col, rating_col

# ----------------- Q10: Actor rankings (performances, social influence, best movie) -----------------
def actor_rankings(df: pd.DataFrame, top: int = 10):
    title_col = _title_col(df)
    rating_col = _find_col(df, [r"imdb.*score", r"\brating\b", r"\bscore\b"])
    # find actor name columns
    name_cols = [c for c in df.columns if re.search(r"\bactor.*name\b|\bstar.*name\b|\bcast.*name\b", str(c), re.I)]
    if not name_cols:
        # Kaggle-style fallback
        for i in (1, 2, 3):
            c = f"actor_{i}_name"
            if c in df.columns:
                name_cols.append(c)
    frames = []
    for c in name_cols:
        # try to find a corresponding facebook likes column
        likes_col = None
        m = re.search(r"actor[_\s]*([0-9]+).*name", str(c), re.I)
        if m:
            guess = f"actor_{m.group(1)}_facebook_likes"
            if guess in df.columns:
                likes_col = guess
        if likes_col is None:
            # best-effort generic lookup
            likes_candidates = [col for col in df.columns if re.search(r"facebook.*likes", str(col), re.I) and m and m.group(1) in str(col)]
            likes_col = likes_candidates[0] if likes_candidates else None

        sub = pd.DataFrame({
            "actor_name": df[c].astype(str),
            "actor_facebook_likes": _to_numeric(df[likes_col]) if likes_col else np.nan,
            "title": df[title_col].astype(str),
            "rating": _to_numeric(df[rating_col]) if rating_col else np.nan,
        })
        frames.append(sub)

    if not frames:
        # nothing found
        empty = pd.DataFrame(columns=["actor_name"])
        return empty, empty, empty, name_cols, rating_col

    actors = pd.concat(frames, ignore_index=True)
    actors = actors[actors["actor_name"].notna() & (actors["actor_name"].str.strip() != "")]

    # a) by number of movies
    by_perf = (actors.groupby("actor_name").size()
                      .sort_values(ascending=False)
                      .reset_index(name="movie_count")
                      .head(top))

    # b) by social media influence (max fb likes observed)
    if actors["actor_facebook_likes"].notna().any():
        by_social = (actors.groupby("actor_name")["actor_facebook_likes"]
                            .max()
                            .sort_values(ascending=False)
                            .reset_index(name="max_facebook_likes")
                            .head(top))
    else:
        by_social = pd.DataFrame(columns=["actor_name", "max_facebook_likes"])

    # c) by best movie (highest rating)
    if "rating" in actors and actors["rating"].notna().any():
        sub = actors.dropna(subset=["rating"])
        idx = sub.groupby("actor_name")["rating"].idxmax()
        best = (sub.loc[idx, ["actor_name", "title", "rating"]]
                    .rename(columns={"title": "best_movie", "rating": "best_rating"})
                    .sort_values(["best_rating", "actor_name"], ascending=[False, True])
                    .head(top))
    else:
        best = pd.DataFrame(columns=["actor_name", "best_movie", "best_rating"])

    return by_perf, by_social, best, name_cols, rating_col
