import os
import re

from collections import defaultdict
from enum import Enum, auto
from typing import Optional

from datasets import load_dataset as _load_dataset

SOURCE_DATASETS = dict(
    unlabelled_tokens="gbenson/webui-tokens-unlabelled",
    english_valid_words="Maximax67/English-Valid-Words",
    wikipedia_title_words="gbenson/wikipedia-page-title-words",
)

def load_dataset(path: str, *args, **kwargs):
    _kwargs = {"split": "train"}
    _kwargs.update(kwargs)
    return _load_dataset(_dataset_path(path), *args, **_kwargs)

def _dataset_path(path, checkouts=os.path.expanduser("~/hf/datasets")):
    if os.path.exists(path):
        return path
    local_path = os.path.join(checkouts, path)
    if not os.path.exists(local_path):
        return path
    return local_path

_IS_HEX_RE = re.compile("^[0-9a-fA-F]+$")

def is_hex(token):
    return bool(_IS_HEX_RE.match(token))

FALSE_HEX = {
    "Ada95",
    "addFace",
    "Decaf377",
    "Ed448",
    "Ed25519",
    "Feb2019",
    "Feb24",
}

_KNOWN_WORDS_CACHE = os.path.expanduser("~/.cache/label_base64.words")
if os.path.exists(_KNOWN_WORDS_CACHE):
    with open(_KNOWN_WORDS_CACHE) as fp:
        _KNOWN_WORDS = set(line.rstrip() for line in fp.readlines())
else:
    _KNOWN_WORDS = dict(
        (row["Rank"], row["Word"])
        for row in load_dataset(
                SOURCE_DATASETS["english_valid_words"],
                "sorted_by_frequency"
        )
    )
    for rank, word in ((8932, "null"), (16351, "nan")):
        if _KNOWN_WORDS[rank] is None:
            _KNOWN_WORDS[rank] = word

    _KNOWN_WORDS = set(_KNOWN_WORDS.values())
    assert len(_KNOWN_WORDS) == 172782

    _KNOWN_WORDS.update(
        row["text"]
        for row in load_dataset(SOURCE_DATASETS["wikipedia_title_words"])
    )

    _four_same_re = re.compile(r"(.)\1\1\1", re.I)
    _KNOWN_WORDS = {
        word
        for word in _KNOWN_WORDS
        if not _four_same_re.search(word) or word.startswith("yyyymm")
    }
    assert all(word == word.lower() for word in _KNOWN_WORDS)
    with open(_KNOWN_WORDS_CACHE, "w") as fp:
        fp.writelines(f"{word}\n" for word in sorted(_KNOWN_WORDS))

def is_known_word(token):
    return token.lower() in _KNOWN_WORDS

class Label(Enum):
    DECIMAL_NUMBER = auto()
    LOWERCASE_HEX = auto()
    UPPERCASE_HEX = auto()
    MIXED_CASE_HEX = auto()
    KNOWN_WORD = auto()
    UNLABELLED = auto()

def label_for(token: str) -> Label:
    is_hex_token = is_hex(token)
    if is_hex_token:
        if token.isnumeric():
            return Label.DECIMAL_NUMBER
        if not token.isalpha():
            label = _label_for_hex(token)
            if label is not None:
                return label
        # ...fall through...
    if is_known_word(token):
        return Label.KNOWN_WORD
    if is_hex_token:
        label = _label_for_hex(token)
        if label is not None:
            return label
    return Label.UNLABELLED

def _label_for_hex(token: str) -> Optional[Label]:
    if token.islower():
        return Label.LOWERCASE_HEX
    if token.isupper():
        return Label.UPPERCASE_HEX
    if token not in FALSE_HEX:
        return Label.MIXED_CASE_HEX
    return None

def main():
    bins = defaultdict(int)
    for row in load_dataset(SOURCE_DATASETS["unlabelled_tokens"]):
        for token in row["text"].split("'"):
            if len(token) < 5:
                continue
            bins[label_for(token)] += 1

    for _, label, num_tokens in sorted(
            (label.value, label, num_tokens)
            for label, num_tokens in bins.items()):
        print(f"{num_tokens:>8}: {label.name}")

# NOTES:
# - not all source tokens are valid base64
# - some are hex/decimal (i.e. easily identifiable as not base64)
#
# make a training set with the same distribution of lengths?
# (with a each length bin having an equal number of b64/not b64?)
#
# Things it'll be interesting to see what a classifier makes of:
# - FALSE_HEX
# - Label.MIXED_CASE_HEX
#
# Possible augmentation:
# - some MIXED_CASE_HEX are concatenated single-case hex: worth splitting?
