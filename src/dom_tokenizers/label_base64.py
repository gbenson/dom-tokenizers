import os
import re

from collections import defaultdict
from enum import Enum, auto
from typing import Optional

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

_WORDS_BY_RANK = dict(
    (row["Rank"], row["Word"])
    for row in load_dataset(
            SOURCE_DATASETS["english_words"],
            "sorted_by_frequency"
    )
)
for rank, word in ((8932, "null"), (16351, "nan")):
    if _WORDS_BY_RANK[rank] is None:
        _WORDS_BY_RANK[rank] = word

_RANKED_WORDS = dict(
    (word.lower(), rank)
    for rank, word in _WORDS_BY_RANK.items()
)

def is_english_word(token):
    return token.lower() in _RANKED_WORDS

_WORDS_BY_LENGTH = defaultdict(set)
for word in _RANKED_WORDS:
    if len(word) < 5:
        continue
    _WORDS_BY_LENGTH[len(word)].add(word)

_WORD_LENGTHS = list(sorted(_WORDS_BY_LENGTH))

class Label(Enum):
    DECIMAL_NUMBER = auto()
    LOWERCASE_HEX = auto()
    UPPERCASE_HEX = auto()
    MIXED_CASE_HEX = auto()
    ENGLISH_WORD = auto()
    UNLABELLED = auto()

FALSE_HEX = {
    "Ada95",
    "addFace",
    "Decaf377",
    "Ed448",
    "Ed25519",
    "Feb2019",
    "Feb24",
}

_log = open("unlabelled-words.log", "w")

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
    #if >100: almost all are base64
    # (24381 words!)
    # and 102968 30<len<100 words
    #
    #573J8100L5093461D49F0C18L583853L509389QL518325QQP0G00G0Q1EA52323000001010000G0P
    #573J8100L5093461D49F0C18L583854L509389QL514841QQP0G00G0Q1EA52323000001010000G0P
    #573J8100L5093461D49F0C18L714582L714580QL514838QQP0G00G0Q1EA52050000001010000G0P
    #
    #addItemToCartAmountEnteredForIsNotValidOrMissingDoNotIncludeWhenEnteringAmountA
    #addProductToCartAmountEnteredForNotValidOrMissingDoNotIncludeWhenEnteringAmount
    #addToCartHelperAmountEnteredForNotValidDoNotIncludeWhenEnteringAmountAmountMust
    #
    #com/senatorchriscoons/posts/pfbid02pXNWyxJuZmWJDqrU7CCMdEtjUCrgw8Pj7wYC8qRuRHcH
    #com/senatorchriscoons/posts/pfbid02uAnxMwEuraKxWtggBdMDnQHKZqNrqeH2HttBaPN6YUvv
    #com/senatorchriscoons/posts/pfbid02uYXTYGS4bnHJu86J8RHeRGJPpi3LjvLb7H63z4VyUGU1
    #com/static/56122b94e4b01402b90cce28/t/5612c0e8e4b0e1ea75381ffa/1444069613406/Me
    #com/static/5bf04054e74940effe961412/5bf044fe4ae237221b0dc997/62036c3ad02e511569
    #com/static/sitecss/53821f30e4b07bcdae103594/112/5eb4907835be1011d8740950/5eb490
    #com/static/sitecss/5a74bb4acd39c357ee3d714a/133/63a3a196f538ee2f45e104f5/63a3a1
    #com/transform/v3/eyJpdSI6Ijg1Y2E5YjAwYzY3YjlhMjc0ZmY3MzI0MTJjMmMzNzVkMjk1NTM3Yz
    #com/transform/v3/eyJpdSI6IjlhMTY1NzAwNGRkZmFjM2FlODI0OTEwMGE3ZDYwMTNkMzEyMzQyYj
    #com/transform/v3/eyJpdSI6IjliZjM3ZDk5YTYwYzA4N2NjMmVkYzljODk4ZmYzNTNiY2ZlNTlmMD
    #com/transform/v3/eyJpdSI6IjMwYjNjYjRjYjM3Mjk3ODcyZTE0NmM0ZTcwNjBiZDgyMDhhZWJiMj
    #com/transform/v3/eyJpdSI6IjQ3MzlhMTM2Yzc1OGRlZTE3NGYyYjU3YTcxOTU1ZjliNDllOTJiNW
    #com/transform/v3/eyJpdSI6IjRmNjExYTQxOWNiNDBkMWVhNTU4YWQ4YWFhYTg0MjAyMDk1NzkxNm
    #com/transform/v3/eyJpdSI6IjUzNjViY2U3YTVlMTE1ODA2MzE1NDEyODE2YzI4Y2U2ZTU0MmZlMD
    #com/transform/v3/eyJpdSI6IjVhNzY4ZGNmNTk0Nzc1ZTg4ZDQ3OTAyYzU5YzQ1ODBmNTZiZGMxOD
    #com/transform/v3/eyJpdSI6ImExOWEwN2QzODA1ZGU4ZWNiMGJlMWEwNmM5ZmVjM2Q1NGNjYTFkMT
    #com/transform/v3/eyJpdSI6ImU0OWExNzY2ODQxYjE0MzgwMzg1ZWE2OTY2YzE5YWYyODU5NjdmYT
    #com/v1/integrations/reodotdev/installations/81e38c589f33c88ac5a76a9ed22fd446ab8
    #
    #DID300000005https3000000b008db8e0f2bab200029e1f1d62028a8dd4fe82affaa6aca08273ca
    if is_english_word(token):
        return Label.ENGLISH_WORD
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
            label = label_for(token)
            bins[label] += 1
            if label != Label.UNLABELLED:
                continue
            if len(token) < 30 or len(token) >= 100:
                continue
            print(token[:80], file=_log)

    for _, label, num_tokens in sorted(
            (label.value, label, num_tokens)
            for label, num_tokens in bins.items()):
        print(f"{num_tokens:>8}: {label.name}")

    _log.close()

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
# - Alter base64 lengths so they're not mostly multiples of 4
