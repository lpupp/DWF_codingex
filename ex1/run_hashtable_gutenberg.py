from fixed_hash_table import FixedHashTable
import re
from typing import Iterator

# -----------------------------
# Dataset creation & example
# -----------------------------

# No digits, no punctuation, all lowercase, hyphenated words separated, no empty strings, 
# no sentence structure tokens, typos included and induced by processing (e.g., linebreak
# typos). See sandbox/corpus.ipynb for basic exploration and processing of text.
WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def tokenize(text: str) -> Iterator[str]:
    for m in WORD_RE.finditer(text):
        yield m.group(0).lower()


def load_gutenberg_text(url: str) -> str:
    """
    Download the text (requires internet at runtime).
    If you prefer offline, download the file once and read from disk.
    """
    import urllib.request
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def build_word_counts(words: Iterator[str], capacity: int = 200_000) -> FixedHashTable:
    """
    Build word-count using FixedHashTable.
    Capacity should exceed expected unique words
    """
    ht = FixedHashTable(capacity=capacity)
    for w in words:
        try:
            c = ht.get(w)
            ht.insert(w, c + 1)  # changed
        except KeyError:
            ht.insert(w, 1)  # new
    return ht


if __name__ == "__main__":
    URL = "https://www.gutenberg.org/files/98/98-0.txt"
    text = load_gutenberg_text(URL)
    words = tokenize(text)
    table = build_word_counts(words, capacity=32_768)

    # Example usage of required methods:
    print("Unique words:", table.size)
    print("Count('the'):", table.get("the"))
    print("Most recent change:", table.get_last())
    print("Least recent change:", table.get_first())

    # Show 10 sample items (arbitrary order due to probing)
    n = 0
    for k, v in table.items():
        print(k, v)
        n += 1
        if n == 10:
            break
