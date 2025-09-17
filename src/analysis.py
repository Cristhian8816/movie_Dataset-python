import re
from typing import Optional, Tuple, List
import pandas as pd

# ----------------- generic helpers -----------------
def _find_col(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    pats = [re.compile(p, re.I) for p in patterns]
    cands = [c for c in df.columns if any(p.search(str(c)) for p in pats)]
    if not cands:
        return None
    return max(cands, key=lambda c: df[c].notna().sum())

def _title_col(df: pd.DataFrame) -> Optional[str]:
    return _find_col(df, [r"^title$", r"movie", r"name$"])

# ----------------- Q1: Color vs Black & White -----------------
def _infer_color_column(df: pd.DataFrame) -> Optional[str]:
    return _find_col(df, [r"color", r"b(?:lack)?.*white", r"b&w"])

def _standardize_color_series(df: pd.DataFrame, col: str) -> pd.Series:
    # NOTE: use .str.strip(), not .strip()
    s = df[col].astype(str).str.strip().str.lower()

    def map_value(x: str) -> str:
        if x in ("", "nan", "none", "null"):
            return "Unknown"
        if "black" in x and "white" in x:
            return "Black & White"
        if "b&w" in x or "b/w" in x:
            return "Black & White"
        if "mono" in x or "grayscale" in x or "greyscale" in x:
            return "Black & White"
        if "color" in x or "colour" in x or "colorized" in x:
            return "Color"
        if x == "bw":
            return "Black & White"
        return "Unknown"

    return s.map(map_value)

def count_bw_color(df: pd.DataFrame):
    """
    Returns (counts_dict, detected_color_column)
    counts_dict keys: 'Color', 'Black & White', 'Unknown'
    """
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
    title_col = _title_col(df) or df.columns[0]
    count_col = _find_col(df, [
        r"critic.*review", r"num.*critic", r"reviews? \(critic\)", r"critic_reviews", r"metacritic.*reviews"
    ]) or _find_col(df, [r"reviews", r"review_count", r"num_reviews"]) \
      or _find_col(df, [r"votes", r"imdb.*votes", r"user.*votes"])
    if count_col is None:
        return pd.DataFrame(columns=[title_col, "criticized_count"]), None, title_col
    counts = pd.to_numeric(df[count_col], errors="coerce")
    res = (df.assign(_count=counts)[[title_col, "_count"]]
             .dropna(subset=["_count"])
             .sort_values("_count", ascending=True)
             .head(10)
             .rename(columns={title_col: "title", "_count": "criticized_count"}))
    return res, count_col, title_col

# ----------------- Q4: 20 longest-running movies -----------------
_RUNTIME_PATS = [r"runtime", r"duration", r"length", r"running.?time", r"mins?", r"minutes?", r"time$"]

def _to_minutes(v) -> float:
    import numpy as np
    if pd.isna(v): return np.nan
    s = str(v).strip().lower()
    try:
        f = float(s); 
        if f > 0: return f
    except ValueError:
        pass
    m = re.search(r"(\d+(\.\d+)?)\s*(mins?|minutes?|m)\b", s)
    if m: return float(m.group(1))
    hm = re.search(r"(\d+)\s*h(?:ours?)?\s*(\d+)?\s*(m|mins?|minutes?)?", s)
    if hm:
        h = float(hm.group(1)); mm = float(hm.group(2) or 0)
        return h*60 + mm
    if ":" in s:
        parts = s.split(":")
        try:
            nums = [float(p) for p in parts]
        except ValueError:
            nums = [0.0]*len(parts)
        if len(nums) == 3: return nums[0]*60 + nums[1]
        if len(nums) == 2: return nums[0]*60 + nums[1]
    return float("nan")

def twenty_longest_running(df: pd.DataFrame):
    title_col = _title_col(df) or df.columns[0]
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
