"""
03_analyse_results.py

Generate summary tables, robustness checks, qualitative word exhibit, and figures.

Input:
- data/processed/scored_chapters.csv

Outputs:
- tables/genre_summary.csv
- tables/book_summary.csv
- tables/robustness_summary.csv
- tables/word_exhibit.csv
- figures/figure1_distribution.png
- figures/figure2_genre_boxplot.png
- figures/figure3_bootstrap_difference.png
- figures/figure4_coverage_by_genre.png

Run from the repository root:
python src/03_analyse_results.py
"""

from pathlib import Path
import re
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from utils import tokenize

ROOT = Path(__file__).resolve().parents[1]
SCORED_PATH = ROOT / "data" / "processed" / "scored_chapters.csv"
LABMT_PATH = ROOT / "data" / "raw" / "labmt" / "labMT.csv"
TABLES_DIR = ROOT / "tables"
FIGURES_DIR = ROOT / "figures"

MIN_TOKEN_COUNT = 300
MIN_MATCHED_TOKEN_COUNT = 100
BOOTSTRAP_N = 10000
RANDOM_SEED = 42


def detect_column(columns, candidates):
    normalised = {col.lower().strip(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in normalised:
            return normalised[candidate.lower()]
    raise ValueError(f"Could not find any of these columns: {candidates}")


def load_labmt_table() -> pd.DataFrame:
    # labMT.csv has two metadata lines before the real header.
    labmt = pd.read_csv(LABMT_PATH, sep="	", skiprows=2, engine="python")

    word_col = detect_column(
        labmt.columns,
        ["word", "Word", "term", "words", "Words"]
    )

    score_col = detect_column(
        labmt.columns,
        [
            "happiness_average",
            "happiness average",
            "avg happiness",
            "happs",
            "score",
            "Happiness Average",
            "happiness"
        ],
    )

    out = labmt[[word_col, score_col]].copy()
    out.columns = ["word", "happiness_average"]
    out["word"] = out["word"].astype(str).str.lower().str.strip()
    out["happiness_average"] = pd.to_numeric(out["happiness_average"], errors="coerce")
    out = out.dropna(subset=["word", "happiness_average"]).drop_duplicates("word")
    return out


def make_word_exhibit(df: pd.DataFrame, labmt: pd.DataFrame) -> pd.DataFrame:
    score_lookup = dict(zip(labmt["word"], labmt["happiness_average"]))

    rows = []
    for genre, subset in df.groupby("genre_group"):
        counter = Counter()
        for text in subset["text"].astype(str):
            counter.update([t for t in tokenize(text) if t in score_lookup])

        common = pd.DataFrame(counter.most_common(500), columns=["word", "count"])
        common["happiness_average"] = common["word"].map(score_lookup)
        common["genre_group"] = genre
        rows.append(common)

    if not rows:
        return pd.DataFrame()

    freq = pd.concat(rows, ignore_index=True)

    # Candidate categories based on actual common words in the corpus.
    positive = freq[freq["happiness_average"] >= 7.0].sort_values(
        ["genre_group", "count"], ascending=[True, False]
    ).groupby("genre_group").head(5)

    negative = freq[freq["happiness_average"] <= 3.5].sort_values(
        ["genre_group", "count"], ascending=[True, False]
    ).groupby("genre_group").head(5)

    ambiguous_band = freq[
        (freq["happiness_average"] > 4.0) & (freq["happiness_average"] < 6.2)
    ].sort_values(["genre_group", "count"], ascending=[True, False]).groupby("genre_group").head(5)

    exhibit = pd.concat(
        [
            positive.assign(category="frequent_positive"),
            negative.assign(category="frequent_negative"),
            ambiguous_band.assign(category="frequent_mid_score_or_ambiguous"),
        ],
        ignore_index=True,
    )

    exhibit["interpretation_note"] = "Fill in manually after close reading the word in context."
    return exhibit[
        ["category", "word", "happiness_average", "count", "genre_group", "interpretation_note"]
    ]


def bootstrap_difference(children_values, gothic_values, n=BOOTSTRAP_N, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)

    children_values = np.asarray(children_values)
    gothic_values = np.asarray(gothic_values)

    diffs = []

    for _ in range(n):
        children_sample = rng.choice(children_values, size=len(children_values), replace=True)
        gothic_sample = rng.choice(gothic_values, size=len(gothic_values), replace=True)
        diffs.append(children_sample.mean() - gothic_sample.mean())

    diffs = np.asarray(diffs)
    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])

    return diffs, ci_low, ci_high

def save_distribution_plot(df: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    children = df.loc[df["genre_group"] == "children", "mean_happiness"].dropna()
    gothic = df.loc[df["genre_group"] == "gothic_horror", "mean_happiness"].dropna()

    plt.figure(figsize=(8, 5))
    plt.hist(children, bins=20, alpha=0.6, label="Children")
    plt.hist(gothic, bins=20, alpha=0.6, label="Gothic / horror")
    plt.xlabel("Mean labMT happiness score")
    plt.ylabel("Number of chapters")
    plt.title("Distribution of Chapter-Level labMT Happiness Scores")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "figure1_distribution.png", dpi=300)
    plt.close()

def save_boxplot(df: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    groups = [
        df.loc[df["genre_group"] == "children", "mean_happiness"].dropna(),
        df.loc[df["genre_group"] == "gothic_horror", "mean_happiness"].dropna(),
    ]

    plt.figure(figsize=(7, 5))
    plt.boxplot(groups, tick_labels=["Children", "Gothic / horror"])
    plt.ylabel("Mean labMT happiness score")
    plt.title("Chapter-Level labMT Happiness by Genre Group")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "figure2_genre_boxplot.png", dpi=300)
    plt.close()


def save_bootstrap_plot(diffs, ci_low, ci_high) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.hist(diffs, bins=40, alpha=0.8)
    plt.axvline(ci_low, linestyle="--", label=f"2.5% CI = {ci_low:.3f}")
    plt.axvline(ci_high, linestyle="--", label=f"97.5% CI = {ci_high:.3f}")
    plt.axvline(0, linestyle=":", label="No difference")
    plt.xlabel("Bootstrap difference in mean happiness")
    plt.ylabel("Frequency")
    plt.title("Bootstrap Distribution of Genre Difference")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "figure3_bootstrap_difference.png", dpi=300)
    plt.close()


def save_coverage_plot(df: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    groups = [
        df.loc[df["genre_group"] == "children", "coverage"].dropna(),
        df.loc[df["genre_group"] == "gothic_horror", "coverage"].dropna(),
    ]

    plt.figure(figsize=(7, 5))
    plt.boxplot(groups, tick_labels=["Children", "Gothic / horror"])
    plt.ylabel("labMT coverage")
    plt.title("labMT Coverage by Genre Group")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "figure4_coverage_by_genre.png", dpi=300)
    plt.close()

def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(SCORED_PATH)

    analysis_df = df[
        (df["token_count"] >= MIN_TOKEN_COUNT)
        & (df["matched_token_count"] >= MIN_MATCHED_TOKEN_COUNT)
        & df["mean_happiness"].notna()
    ].copy()

    print(f"Total chapters before exclusion: {len(df)}")
    print(f"Chapters retained for main analysis: {len(analysis_df)}")

    genre_summary = (
        analysis_df.groupby("genre_group")
        .agg(
            n_chapters=("mean_happiness", "size"),
            mean_happiness=("mean_happiness", "mean"),
            median_happiness=("mean_happiness", "median"),
            sd_happiness=("mean_happiness", "std"),
            mean_coverage=("coverage", "mean"),
            mean_word_count=("word_count", "mean"),
            mean_matched_tokens=("matched_token_count", "mean"),
        )
        .reset_index()
    )
    genre_summary.to_csv(TABLES_DIR / "genre_summary.csv", index=False)

    book_summary = (
        analysis_df.groupby(["genre_group", "title", "author"])
        .agg(
            n_chapters=("mean_happiness", "size"),
            mean_happiness=("mean_happiness", "mean"),
            median_happiness=("mean_happiness", "median"),
            mean_coverage=("coverage", "mean"),
            mean_word_count=("word_count", "mean"),
        )
        .reset_index()
    )
    book_summary.to_csv(TABLES_DIR / "book_summary.csv", index=False)

    children = analysis_df.loc[analysis_df["genre_group"] == "children", "mean_happiness"].dropna()
    gothic = analysis_df.loc[analysis_df["genre_group"] == "gothic_horror", "mean_happiness"].dropna()

    if len(children) == 0 or len(gothic) == 0:
        raise ValueError("One genre group has no retained chapters. Check thresholds or corpus parsing.")

    diffs, ci_low, ci_high = bootstrap_difference(children, gothic)
    observed_diff = children.mean() - gothic.mean()

    robustness_rows = [
        {
            "check": "main_chapter_level",
            "min_token_count": MIN_TOKEN_COUNT,
            "min_matched_token_count": MIN_MATCHED_TOKEN_COUNT,
            "n_children": len(children),
            "n_gothic_horror": len(gothic),
            "observed_difference_children_minus_gothic": observed_diff,
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
        }
    ]

    # Robustness check A: stricter matched-token threshold.
    strict_df = df[
        (df["token_count"] >= MIN_TOKEN_COUNT)
        & (df["matched_token_count"] >= 200)
        & df["mean_happiness"].notna()
    ].copy()
    strict_children = strict_df.loc[strict_df["genre_group"] == "children", "mean_happiness"].dropna()
    strict_gothic = strict_df.loc[strict_df["genre_group"] == "gothic_horror", "mean_happiness"].dropna()
    if len(strict_children) > 0 and len(strict_gothic) > 0:
        strict_diffs, strict_low, strict_high = bootstrap_difference(strict_children, strict_gothic)
        robustness_rows.append(
            {
                "check": "stricter_matched_token_threshold",
                "min_token_count": MIN_TOKEN_COUNT,
                "min_matched_token_count": 200,
                "n_children": len(strict_children),
                "n_gothic_horror": len(strict_gothic),
                "observed_difference_children_minus_gothic": strict_children.mean() - strict_gothic.mean(),
                "bootstrap_ci_low": strict_low,
                "bootstrap_ci_high": strict_high,
            }
        )

    # Robustness check B: book-level aggregation.
    book_level = book_summary.copy()
    book_children = book_level.loc[book_level["genre_group"] == "children", "mean_happiness"].dropna()
    book_gothic = book_level.loc[book_level["genre_group"] == "gothic_horror", "mean_happiness"].dropna()
    if len(book_children) > 0 and len(book_gothic) > 0:
        book_diffs, book_low, book_high = bootstrap_difference(book_children, book_gothic)
        robustness_rows.append(
            {
                "check": "book_level_aggregation",
                "min_token_count": None,
                "min_matched_token_count": None,
                "n_children": len(book_children),
                "n_gothic_horror": len(book_gothic),
                "observed_difference_children_minus_gothic": book_children.mean() - book_gothic.mean(),
                "bootstrap_ci_low": book_low,
                "bootstrap_ci_high": book_high,
            }
        )

    pd.DataFrame(robustness_rows).to_csv(TABLES_DIR / "robustness_summary.csv", index=False)

    save_distribution_plot(analysis_df)
    save_boxplot(analysis_df)
    save_bootstrap_plot(diffs, ci_low, ci_high)
    save_coverage_plot(analysis_df)

    labmt = load_labmt_table()
    word_exhibit = make_word_exhibit(analysis_df, labmt)
    word_exhibit.to_csv(TABLES_DIR / "word_exhibit.csv", index=False)

    print("\nGenre summary:")
    print(genre_summary)

    print("\nRobustness summary:")
    print(pd.DataFrame(robustness_rows))

    print("\nSaved tables and figures.")


if __name__ == "__main__":
    main()
