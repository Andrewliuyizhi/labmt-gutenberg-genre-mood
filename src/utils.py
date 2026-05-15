"""
utils.py

Shared helper functions for the labMT Project Gutenberg genre mood project.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict


TOKEN_RE = re.compile(r"[A-Za-z]+")


def read_text(path: Path) -> str:
    """Read a text file with a forgiving UTF-8 setup."""
    return path.read_text(encoding="utf-8", errors="replace")


def strip_gutenberg_boilerplate(text: str) -> str:
    """
    Remove common Project Gutenberg header/footer material.

    Project Gutenberg files vary. This function handles the most common markers,
    but the output should still be sanity-checked for each text.
    """
    start_patterns = [
        r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .*? \*\*\*",
        r"\*\*\* START OF THIS PROJECT GUTENBERG EBOOK .*? \*\*\*",
        r"\*\*\*START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*",
        r"\*\*\*START OF THIS PROJECT GUTENBERG EBOOK.*?\*\*\*",
    ]
    end_patterns = [
        r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK .*? \*\*\*",
        r"\*\*\* END OF THIS PROJECT GUTENBERG EBOOK .*? \*\*\*",
        r"\*\*\*END OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*",
        r"\*\*\*END OF THIS PROJECT GUTENBERG EBOOK.*?\*\*\*",
    ]

    cleaned = text

    for pattern in start_patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[match.end():]
            break

    for pattern in end_patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE | re.DOTALL)
        if match:
            cleaned = cleaned[:match.start()]
            break

    return cleaned.strip()


def tokenize(text: str) -> List[str]:
    """Tokenise text into lowercase alphabetic tokens."""
    return [token.lower() for token in TOKEN_RE.findall(text)]


def word_count(text: str) -> int:
    """Count alphabetic tokens in a text."""
    return len(tokenize(text))


def split_into_chapters(text: str, chapter_pattern: str = "default") -> List[Dict[str, str]]:
    """
    Split a cleaned Project Gutenberg text into chapters.

    chapter_pattern options:
    - default: standard headings such as CHAPTER I, CHAPTER 1, CHAPTER ONE, or I. Title
    - allcaps_title: standalone all-capital chapter titles, used for Jekyll & Hyde
    - roman_only: standalone Roman numerals, used for The Turn of the Screw
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    if chapter_pattern == "allcaps_title":
        known_titles = [
            r"STORY OF THE DOOR",
            r"SEARCH FOR MR\.?\s+HYDE",
            r"DR\.?\s+JEKYLL WAS QUITE AT EASE",
            r"THE CAREW MURDER CASE",
            r"INCIDENT OF THE LETTER",
            r"INCIDENT OF DR\.?\s+LANYON",
            r"INCIDENT AT THE WINDOW",
            r"THE LAST NIGHT",
            r"DR\.?\s+LANYON['’]S NARRATIVE",
            r"HENRY JEKYLL['’]S FULL STATEMENT OF THE CASE",
        ]

        pattern = re.compile(
            r"(?im)^\s*(" + "|".join(known_titles) + r")\s*$"
        )

    elif chapter_pattern == "roman_only":
        roman_numbers = [
            "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
            "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII",
            "XIX", "XX", "XXI", "XXII", "XXIII", "XXIV"
        ]

        pattern = re.compile(
            r"(?im)^\s*(" + "|".join(roman_numbers) + r")\s*$"
        )

    else:
        pattern = re.compile(
            r"(?im)^\s*((chapter\s+([ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|twenty-one|twenty-two|twenty-three|twenty-four|twenty-five|twenty-six|twenty-seven|twenty-eight|twenty-nine|thirty|thirty-one|thirty-two|thirty-three|thirty-four|thirty-five|thirty-six|thirty-seven|thirty-eight|thirty-nine|forty)[^\n]*)|(([ivxlcdm]+|\d+)\.\s+[A-Z][^\n]+))\s*$"
        )

    matches = list(pattern.finditer(text))

    if len(matches) < 2:
        return [
            {
                "chapter_id": 1,
                "chapter_title": "full_text",
                "text": text.strip(),
            }
        ]

    chapters = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        chapter_title = match.group(1).strip()
        chapter_text = text[start:end].strip()

        if len(chapter_text.split()) > 100:
            chapters.append(
                {
                    "chapter_id": len(chapters) + 1,
                    "chapter_title": chapter_title,
                    "text": chapter_text,
                }
            )

    return chapters