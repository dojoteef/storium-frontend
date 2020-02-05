"""
Additional utilities
"""
import string
from typing import List
from itertools import zip_longest

import regex as re


SENT_REGEX = re.compile(
    rf'(?<=\w\w[{string.punctuation}]*[.?!]+)(?:\s|\r\n)+(?="?[A-Z])'
)


def snake_case(name: str) -> str:
    """
    Convert name from CamelCase to snake_case
    See https://stackoverflow.com/a/1176023
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def grouper(iterable, n, fillvalue=None, padded=False):  # pylint:disable=invalid-name
    """
    See itertools recipes:
    https://docs.python.org/3/library/itertools.html#itertools-recipes
    Collect data into fixed-length chunks or blocks
    """
    args = [iter(iterable)] * n
    groups = zip_longest(*args, fillvalue=fillvalue)
    if padded:
        # keep the fill value
        return groups
    else:
        # ignore the fill value
        return [[x for x in group if x is not fillvalue] for group in groups]


def split_sentences(text: str) -> List[str]:
    """
    Split a text string into a number of sentences using a simple regex
    """
    return SENT_REGEX.split(text)


def overlap(a: List[str], b: List[str], threshold: int = 3) -> int:
    """
    Compute the set over overlapping strings in each set based on n-gram
    overlap where 'n' is defined by the passed in threshold.
    """

    def get_ngrams(text):
        """
        Get a set of all the ngrams in the text
        """
        return set(" ".join(g) for g in grouper(text.split(), threshold))

    sentence_overlaps = 0
    remaining = set(range(len(b)))
    for text in a:
        best_idx = -1
        best_overlap = 0
        ngrams = get_ngrams(text)
        for idx in remaining:
            ngram_overlap = len(ngrams & get_ngrams(b[idx]))
            if ngram_overlap > best_overlap:
                best_idx = idx
                best_overlap = ngram_overlap

        if best_idx >= 0:
            sentence_overlaps += 1
            remaining.remove(best_idx)

    return sentence_overlaps
