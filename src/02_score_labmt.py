"""
02_score_labmt.py

Score each chapter with labMT.

Inputs:
- data/processed/chapters.csv
- data/raw/labmt/labMT.csv

Output:
- data/processed/scored_chapters.csv

Run from the repository root:
python src/02_score_labmt.py
"""

from pathlib import Path
from typing import Dict
import pandas as pd
import numpy as np

from utils import tokenize

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_PATH = ROOT / "data" / "processed" / "chapters.csv"
LABMT_PATH = ROOT / "data" / "raw" / "labmt" / "labMT.csv"
OUT_PATH = ROOT / "data" / "processed" / "scored_chapters.csv"


def detect_column(columns, candidates):
    """Find the first matching column from a list of possible names."""
    normalised = {col.lower().strip(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in normalised:
            return normalised[candidate.lower()]
    raise ValueError(f"Could not find any of these columns: {candidates}")


def load_labmt_scores(path: Path) -> Dict[str, float]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing labMT file: {path}. "
            "Place a labMT CSV file at data/raw/labmt/labMT.csv."
        )

    # The labMT file used here is the original Data_Set_S1.txt format:
    # first 3 lines are metadata, then the real table starts.
    # It is whitespace-separated rather than comma-separated.
    try:
        labmt = pd.read_csv(path, sep=r"\s+", skiprows=3, engine="python")
    except Exception:
        # Fallback for a normal comma-separated CSV version
        labmt = pd.read_csv(path)

    word_col = detect_column(labmt.columns, ["word", "Word", "term"])
    score_col = detect_column(
        labmt.columns,
        ["happiness_average", "happiness average", "avg happiness", "happs", "score"],
    )

    labmt = labmt[[word_col, score_col]].copy()
    labmt.columns = ["word", "happiness_average"]
    labmt["word"] = labmt["word"].astype(str).str.lower().str.strip()
    labmt["happiness_average"] = pd.to_numeric(labmt["happiness_average"], errors="coerce")
    labmt = labmt.dropna(subset=["word", "happiness_average"])
    labmt = labmt.drop_duplicates(subset=["word"])

    return dict(zip(labmt["word"], labmt["happiness_average"]))


def score_text(text: str, scores: Dict[str, float]) -> dict:
    tokens = tokenize(text)
    token_count = len(tokens)

    matched_scores = [scores[t] for t in tokens if t in scores]
    matched_token_count = len(matched_scores)
    oov_token_count = token_count - matched_token_count
    coverage = matched_token_count / token_count if token_count else np.nan

    return {
        "token_count": token_count,
        "matched_token_count": matched_token_count,
        "oov_token_count": oov_token_count,
        "coverage": coverage,
        "mean_happiness": float(np.mean(matched_scores)) if matched_scores else np.nan,
        "median_happiness": float(np.median(matched_scores)) if matched_scores else np.nan,
    }


def main() -> None:
    chapters = pd.read_csv(CHAPTERS_PATH)
    scores = load_labmt_scores(LABMT_PATH)

    scored_rows = []
    for _, row in chapters.iterrows():
        result = score_text(str(row["text"]), scores)
        scored_rows.append(result)

    scored = pd.concat([chapters, pd.DataFrame(scored_rows)], axis=1)

    print("\nScoring complete.")
    print(f"Rows / chapters: {len(scored)}")
    print("\nCoverage summary by genre:")
    print(scored.groupby("genre_group")["coverage"].describe())

    print("\nHappiness summary by genre:")
    print(scored.groupby("genre_group")["mean_happiness"].describe())

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(OUT_PATH, index=False)
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
