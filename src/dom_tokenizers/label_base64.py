import os
import re

from collections import defaultdict
from enum import Enum, auto

from datasets import load_dataset as _load_dataset

SOURCE_DATASETS = dict(
    unlabelled_tokens="gbenson/webui-tokens-unlabelled",
    english_words="Maximax67/English-Valid-Words",
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
    "Decaf377",
    "Ed448",
    "Ed25519",
    "Feb2019",
    "Feb24",
}

#ENGLISH_WORDS = load_dataset(SOURCE_DATASETS["english_words"], "valid_words")

class Label(Enum):
    DECIMAL_NUMBER = auto()
    LOWERCASE_HEX = auto()
    UPPERCASE_HEX = auto()
    MIXED_CASE_HEX = auto()
    UNLABELLED = auto()

def label_for(token: str):
    if is_hex(token):
        if token.isnumeric():
            return Label.DECIMAL_NUMBER
        if not token.isalpha():
            if token.islower():
                return Label.LOWERCASE_HEX
            if token.isupper():
                return Label.UPPERCASE_HEX
            if token not in FALSE_HEX:
                return Label.MIXED_CASE_HEX
        # ...fall through...
    return Label.UNLABELLED

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
