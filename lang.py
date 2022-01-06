"""Deeper support for alternate languages and subsets."""

import itertools as itt
import math
import zipfile
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Iterable, Optional

import pystow
from english_words import english_words_alpha_set
from tqdm import tqdm

__all__ = [
    "get_words",
    "Language",
]

URL = "http://www.ids-mannheim.de/fileadmin/kl/derewo/derewo-v-ww-bll-320000g-2012-12-31-1.0.zip"


@lru_cache
def get_words(length: int, language: Optional[str] = None) -> set[str]:
    """Get words of a given length in a given language."""
    if language is None or language == "en":
        return {word.lower() for word in english_words_alpha_set if length == len(word)}
    elif language == "de":
        path = pystow.ensure("wordle", url=URL)
        rv = set()
        with zipfile.ZipFile(path) as zip_file:
            with zip_file.open("derewo-v-ww-bll-320000g-2012-12-31-1.0.txt", mode="r") as file:
                for line_bytes in file:
                    line = line_bytes.strip().decode("iso-8859-1")
                    if line.startswith("#") or "," in line:
                        continue
                    word, *_ = line.split()
                    rv.add(word)
        return {word.lower() for word in rv if length == len(word)}
    else:
        raise ValueError(f"Unhandled language: {language}")


def _exclusive(left: str, right: str) -> bool:
    """Return if two strings don't share any characters or have duplicates.

    >>> _exclusive("abc", "def")
    True
    >>> _exclusive("abcc", "def")
    False
    >>> _exclusive("abc", "cde")
    False
    """
    counter = Counter(left) + Counter(right)
    return 1 == counter.most_common(1)[0][1]


class Language:
    """Represents a language, and operations on indexing it."""

    def __init__(self, length: int, language: Optional[str] = None):
        """Instantiate a language.

        :param length: The length of the words. The canonical game uses 5.
        :param language: The language you want to play in (either en or de for now)
        """
        self.length = length
        self.language = language or "en"
        self.words = get_words(length=self.length, language=self.language)
        self.words_list = sorted(self.words)
        self.frequency = Counter(char for word in self.words for char in word)
        total = sum(self.frequency.values())
        self.frequency_norm = Counter(
            {char: count / total for char, count in self.frequency.items()}
        )

    def score_words(self, *words: str) -> float:
        """Score a set of words based on their unique letters weighted by their frequency."""
        chars = {char for word in words for char in word}
        return sum(self.frequency_norm[char] for char in chars)

    def get_index(self) -> dict[tuple[str, ...], list[str]]:
        """Create an index of words with no overlapping letters."""
        # The goal of the index is to make a list of acceptable choices
        index = defaultdict(list)
        for left, right in tqdm(
            itt.combinations(self.words_list, 2),
            desc="Initial index",
            unit_scale=True,
            unit="pair",
            total=math.comb(len(self.words_list), 2),
        ):
            if _exclusive(left, right):
                index[tuple([left])].append(right)
        return dict(index)

    def deepen_index(
        self, index: dict[tuple[str, ...], list[str]]
    ) -> dict[tuple[str, ...], list[str]]:
        """Deepen an index of words with no overlapping letters with one more word."""
        rv = defaultdict(list)
        for key, values in tqdm(index.items(), desc="Extending index"):
            for left, right in itt.combinations(values, 2):
                if _exclusive(left, right):
                    rv[(*key, left)].append(right)
        return dict(rv)

    def iter_k_tuples(self, k: int) -> Iterable[tuple[str, ...]]:
        """Unwrap an index and iterate over its word tuples.

        :param k: Number of words in the sequence
        """
        if k == 1:
            for word in self.words_list:
                yield (word,)
        else:
            index = self.get_index()
            for _ in range(k - 2):
                index = self.deepen_index(index)
            # unwind index
            for key, values in index.items():
                for value in values:
                    yield *key, value

    def get_top_words(
        self,
        *,
        k: int,
        n: Optional[int] = 30,
    ) -> list[tuple[tuple[str, ...], float]]:
        """Get the top n word sequences of length k."""
        scores = Counter({words: self.score_words(*words) for words in self.iter_k_tuples(k)})
        return scores.most_common(n)  # type:ignore
