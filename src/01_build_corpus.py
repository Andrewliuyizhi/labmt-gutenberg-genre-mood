"""
01_build_corpus.py

Build a chapter-level corpus from raw Project Gutenberg text files.

Input:
- data/raw/gutenberg/metadata.csv
- data/raw/gutenberg/*.txt

Output:
- data/processed/chapters.csv

Run from the repository root:
python src/01_build_corpus.py
"""

from pathlib import Path
import pandas as pd

from utils import read_text, strip_gutenberg_boilerplate, split_into_chapters, word_count

ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "data" / "raw" / "metadata.csv"
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "processed" / "chapters.csv"


def main() -> None:
    metadata = pd.read_csv(METADATA_PATH)
    rows = []

    for _, book in metadata.iterrows():
        raw_path = RAW_DIR / book["filename"]
        if not raw_path.exists():
            raise FileNotFoundError(
                f"Missing raw text file: {raw_path}. "
                "Download it manually or run python src/00_download_sources.py."
            )

        raw_text = read_text(raw_path)
        clean_text = strip_gutenberg_boilerplate(raw_text)

        chapter_pattern = book.get("chapter_pattern", "default")
        chapters = split_into_chapters(clean_text, chapter_pattern=chapter_pattern)

        print(f'{book["title"]}: {len(chapters)} chapters using pattern = {chapter_pattern}')
        

        for chapter in chapters:
            text = chapter["text"]
            rows.append(
                {
                    "book_id": book["book_id"],
                    "title": book["title"],
                    "author": book["author"],
                    "genre_group": book["genre_group"],
                    "chapter_id": chapter["chapter_id"],
                    "chapter_title": chapter["chapter_title"],
                    "text": text,
                    "word_count": word_count(text),
                }
            )

    df = pd.DataFrame(rows)

    # Basic sanity checks printed to console.
    print("\nCorpus built.")
    print(f"Rows / chapters: {len(df)}")
    print("\nChapters per book:")
    print(df.groupby(["genre_group", "title"]).size())

    print("\nWord count summary by genre:")
    print(df.groupby("genre_group")["word_count"].describe())

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
