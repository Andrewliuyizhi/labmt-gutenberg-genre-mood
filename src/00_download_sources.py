"""
00_download_sources.py

Optional script to download Project Gutenberg raw text files listed in:
data/raw/gutenberg/metadata.csv

Run from the repository root:
python src/00_download_sources.py
"""

from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "data" / "raw" / "gutenberg" / "metadata.csv"
OUT_DIR = ROOT / "data" / "raw" / "gutenberg"


def main() -> None:
    metadata = pd.read_csv(METADATA_PATH)

    for _, row in metadata.iterrows():
        url = row["gutenberg_url"]
        filename = row["filename"]
        out_path = OUT_DIR / filename

        if out_path.exists():
            print(f"Skipping existing file: {out_path}")
            continue

        print(f"Downloading {url} -> {out_path}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        out_path.write_text(response.text, encoding="utf-8", errors="replace")

    print("Done.")


if __name__ == "__main__":
    main()
