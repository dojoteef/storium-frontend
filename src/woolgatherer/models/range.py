"""
Defines the structure for ranges
"""
import string
import unicodedata
from enum import auto
from typing import Any, List, Optional, Type

import regex as re
from pydantic import BaseModel, Field, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from woolgatherer.models.utils import AutoNamedEnum


class RangeUnits(AutoNamedEnum):
    """
    When specifying the range of a suggestion, what units are we specifying the range
    in:

    - **words**: specify the range in words
    - **chars**: specify the range in characters
    - **sentences**: specify the range in sentences
    """

    words = auto()
    chars = auto()
    sentences = auto()

    SPLITTERS = {
        chars: lambda text: len(NFC(text)),
        words: lambda text: len(tokenize(text)),
        sentences: lambda text: len(split_sentences(text)),
    }

    def split_text(self, text):
        """
        Split text into range units
        """
        return RangeUnits.SPLITTERS[self](text)


SUBRANGE_REGEX_STR = r"((?<!=),)?(?P<start>\d+|(?!-(,|$)))-(?P<end>(\d+)?)"
RANGE_REGEX_STR = (
    f"(?P<unit>({'|'.join(RangeUnits)}))=(?P<ranges>({SUBRANGE_REGEX_STR})+)"
)

SUBRANGE_REGEX = regex = re.compile(SUBRANGE_REGEX_STR)
RANGE_REGEX = regex = re.compile(RANGE_REGEX_STR)
TOKENIZER_REGEX = re.compile(r"\w+|[^\w\s]+")
SENT_REGEX = re.compile(
    rf'(?<=\w\w[{string.punctuation}]*[.?!]+)(?:\s|\r\n)+(?="?[A-Z])'
)


class Subrange(BaseModel):
    """ A portion of a range, which may have a start and/or an end """

    start: Optional[int]
    end: Optional[int]


class Range(BaseModel):
    """ Definition of a range as defined in https://tools.ietf.org/html/rfc7233
    See also: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Range

    Note, the start and end of a range are inclusive. For example, to specify you want
    only the first word, an appropriate Range header would look like:

        Range: words=0-0
    """

    unit: RangeUnits = Field(RangeUnits.words, description=RangeUnits.__doc__)
    ranges: List[Subrange] = Field(
        [],
        description="""
A list of subranges as specified in RFC7233 (https://tools.ietf.org/html/rfc7233)
        """,
    )

    @classmethod
    def validate(cls: Type["Range"], value: Any) -> "Range":
        """ Validate the passed in value """
        if isinstance(value, str):
            match = RANGE_REGEX.fullmatch(value)
            if not match:
                raise ValidationError(
                    [
                        ErrorWrapper(
                            ValueError(f"Unable to parse Range!"), loc=cls.__name__
                        )
                    ],
                    cls,
                )

            match_groups = match.groupdict()
            return cls(
                unit=match_groups["unit"],
                ranges=[
                    Subrange(
                        **{k: int(v) if v else None for k, v in m.groupdict().items()}
                    )
                    for m in SUBRANGE_REGEX.finditer(match_groups["ranges"])
                ],
            )

        return super().validate(value)

    def __str__(self):
        """ Override the string method to return a range as specified by our regexes """
        ranges = ",".join(
            [
                ("" if r.start is None else str(r.start))
                + "-"
                + ("" if r.end is None else str(r.end))
                for r in self.ranges  # pylint:disable=not-an-iterable
            ]
        )
        return f"{self.unit.value}={ranges}"  # pylint:disable=no-member

    def is_finite(self) -> bool:
        """ A method to determine if the range is a finite range """
        if len(self.ranges) != 1:
            return False

        # pylint:disable=unsubscriptable-object
        return self.ranges[0].start is not None and self.ranges[0].end is not None
        # pylint:enable=unsubscriptable-object


def tokenize(text: str) -> List[str]:
    """
    Implement a simple tokenizer that seperates continguous word characters and
    punctuation.
    """
    return TOKENIZER_REGEX.findall(text)


def NFC(text):
    """
    Normalize the unicode string into NFC form

    Read more about that here:
    https://docs.python.org/3/library/unicodedata.html#unicodedata.normalize
    """
    return unicodedata.normalize("NFC", text)


def split_sentences(text: str) -> List[str]:
    """
    Split a text string into a number of sentences using a simple regex
    """
    return SENT_REGEX.split(text)


def compute_range(
    text: str, units: RangeUnits, max_length: int, chunk_size: int
) -> Range:
    """ Compute the range of the scene entry """
    ranges: List[Subrange] = []
    range_dict = {"unit": units, "ranges": ranges}

    text_len = len(units.split_text(text))
    remaining = max_length - text_len
    if remaining > 0:
        end = min(remaining, chunk_size)
        start = text_len if end == remaining else None
        end = start + remaining if start else end

        ranges.append(Subrange(start=start, end=end))

    return Range(**range_dict)
