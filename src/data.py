import re
import zipfile
from pathlib import Path
from typing import Tuple, Optional, Dict

import gdown
import pandas as pd

from .config import GOOGLE_FILE_ID, RAW_DIR


def download_data(file_id: str = GOOGLE_FILE_ID, out_dir: Path = RAW_DIR) -> Path:
    """
    Downloads a file (or folder/zip) from Google Drive by ID into out_dir.
    Returns the path to the downloaded item.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Let gdown decide filename; returns the downloaded file path.
    downloaded_path = gdown.download(id=file_id, output=str(out_dir), quiet=False, fuzzy=True)
    if downloaded_path is None:
        raise RuntimeError("Download failed. Check that the Google Drive link is public.")
    return Path(downloaded_path)


def _find_first_table_file(dirpath: Path) -> Optional[Path]:
    exts = (".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".json")
    for ext in exts:
        files = list(Path(dirpath).glob(f"**/*{ext}"))
        if files:
            return files[0]
    return None


def load_movies(downloaded_path: Path) -> Tuple[pd.DataFrame, Path]:
    """
    Given a path returned by download_data, locate a tabular file and load it.
    Supports CSV/TSV/XLS/XLSX/Parquet/JSON and ZIPs containing those.
    Returns (dataframe, actual_table_file_path).
    """
    p = Path(downloaded_path)

    if p.is_dir():
        table = _find_first_table_file(p)
        if table is None:
            raise FileNotFoundError("No table-like file found in the downloaded directory.")
        p = table

    elif p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p, "r") as zf:
            zf.extractall(p.parent)
        table = _find_first_table_file(p.parent)
        if table is None:
            raise FileNotFoundError("Zip extracted but no table-like file found.")
        p = table

    # Read based on extension
    suf = p.suffix.lower()
    if suf == ".csv":
        try:
            df = pd.read_csv(p, low_memory=False)
        except Exception:
            df = pd.read_csv(p, sep=None, engine="python", low_memory=False)
    elif suf == ".tsv":
        df = pd.read_csv(p, sep="\t", low_memory=False)
    elif suf in (".xlsx", ".xls"):
        df = pd.read_excel(p)
    elif suf == ".parquet":
        df = pd.read_parquet(p)
    elif suf == ".json":
        try:
            df = pd.read_json(p, lines=True)
        except ValueError:
            df = pd.read_json(p)
    else:
        raise ValueError(f"Unsupported file type: {suf}")

    return df, p


def _infer_color_column(df: pd.DataFrame) -> Optional[str]:
    """
    Heuristically pick a column that indicates movie color vs black & white.
    """
    candidates = [c for c in df.columns if re.search(r"color|b(?:lack)?.*white|b&w", str(c), re.I)]
    if not candidates:
        return None
    # prefer column with most non-null values
    best = max(candidates, key=lambda c: df[c].notna().sum())
    return best


def _standardize_color_series(df: pd.DataFrame, col: str) -> pd.Series:
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
        # fallbacks
        if x == "bw":
            return "Black & White"
        return "Unknown"

    return s.map(map_value)


def count_bw_color(df: pd.DataFrame) -> Tuple[Dict[str, int], Optional[str]]:
    """
    Return counts for Color vs Black & White (and Unknown), plus the detected column name.
    """
    col = _infer_color_column(df)
    if col is None:
        counts = {"Black & White": 0, "Color": 0, "Unknown": len(df)}
        return counts, None

    mapped = _standardize_color_series(df, col)
    counts = mapped.value_counts(dropna=False).to_dict()

    # Normalize keys
    for k in ["Black & White", "Color", "Unknown"]:
        counts.setdefault(k, 0)

    return counts, col
