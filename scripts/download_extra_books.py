from pathlib import Path
import requests


BOOKS = [
    {
        "genre_group": "children",
        "title": "Heidi",
        "author": "Johanna Spyri",
        "gutenberg_id": "1448",
        "filename": "heidi.txt",
    },
    {
        "genre_group": "children",
        "title": "Black Beauty",
        "author": "Anna Sewell",
        "gutenberg_id": "271",
        "filename": "black_beauty.txt",
    },
    {
        "genre_group": "children",
        "title": "Anne of Green Gables",
        "author": "L. M. Montgomery",
        "gutenberg_id": "45",
        "filename": "anne_green_gables.txt",
    },
    {
        "genre_group": "children",
        "title": "Five Children and It",
        "author": "E. Nesbit",
        "gutenberg_id": "778",
        "filename": "five_children.txt",
    },
    {
        "genre_group": "children",
        "title": "The Wind in the Willows",
        "author": "Kenneth Grahame",
        "gutenberg_id": "27827",
        "filename": "wind_in_the_willows.txt",
    },
    {
        "genre_group": "gothic_horror",
        "title": "Carmilla",
        "author": "J. Sheridan Le Fanu",
        "gutenberg_id": "10007",
        "filename": "carmilla.txt",
    },
    {
        "genre_group": "gothic_horror",
        "title": "The Castle of Otranto",
        "author": "Horace Walpole",
        "gutenberg_id": "696",
        "filename": "castle_of_otranto.txt",
    },
    {
        "genre_group": "gothic_horror",
        "title": "The House of the Seven Gables",
        "author": "Nathaniel Hawthorne",
        "gutenberg_id": "77",
        "filename": "house_seven_gables.txt",
    },
    {
        "genre_group": "gothic_horror",
        "title": "The King in Yellow",
        "author": "Robert W. Chambers",
        "gutenberg_id": "8492",
        "filename": "king_in_yellow.txt",
    },
    {
        "genre_group": "gothic_horror",
        "title": "Vathek",
        "author": "William Beckford",
        "gutenberg_id": "7327",
        "filename": "vathek.txt",
    },
]


def get_gutenberg_url(gutenberg_id):
    return f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt"


def download_book(book):
    output_dir = Path("data") / "raw" / book["genre_group"]
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / book["filename"]
    url = get_gutenberg_url(book["gutenberg_id"])

    if output_path.exists():
        print(f"Already exists, skipping: {output_path}")
        return

    print(f"Downloading: {book['title']}")
    print(f"From: {url}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    text = response.text

    if len(text) < 1000:
        raise ValueError(f"Downloaded text seems too short for {book['title']}")

    output_path.write_text(text, encoding="utf-8")

    print(f"Saved to: {output_path}")
    print(f"Characters: {len(text)}")
    print("-" * 60)


def main():
    for book in BOOKS:
        download_book(book)

    print("Finished downloading extra Gutenberg books.")


if __name__ == "__main__":
    main()
