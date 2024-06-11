import json
import os
import re

from base64 import b64decode, b64encode
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

class FileType(Enum):
    GIF = b"GIF8"
    JFIF = b"\xff\xd8\xff\xe0"
    JPEG = b"\xff\xd8\xff\xdb"
    JSON_SANDWICH = b"\x00\x1d\xda|"  # 9binary + JSON + 8binary
    PNG = b"\x89PNG"
    RIFF = b"RIFF"
    SVG = b"<svg"
    WEBP = None
    WOFF = b"wOFF"
    WOF2 = b"wOF2"

    @classmethod
    def from_base64_encoded(cls, encoded) -> Optional["FileType"]:
        filetype = _MAGIC_BASE64.get(encoded[:5])
        match filetype:
            case cls.JFIF:
                return cls.JPEG
            case cls.WOF2:
                return cls.WOFF
            case other if other != cls.RIFF:
                return filetype
        subtype = b64decode(encoded[:16])[-4:].decode("ascii")
        return getattr(cls, subtype, filetype)

_MAGIC_BYTES = dict(
    (filetype.value, filetype)
    for filetype in FileType
    if filetype.value is not None
)

_MAGIC_BASE64 = dict(
    (b64encode(magic)[:5].decode("ascii"), filetype)
    for magic, filetype in _MAGIC_BYTES.items()
)

def _forced_b64decode(encoded, **kwargs):
    extra = "xA=="
    if (n := len(encoded) % 4):
        encoded += extra[n:]
    return b64decode(encoded, **kwargs)

def _try_decode(data, *args, **kwargs):
    try:
        return data.decode(*args, **kwargs)
    except UnicodeDecodeError:
        return None

FALSE_BASE64_ENCODED_UTF8 = {
    "666666666666666666em", # decodes to 5-character CJK!
    "InstanceEndEditable",  # => "{-jw\x1e\x12wDv+ZnW'
}

class Label(Enum):
    DECIMAL_NUMBER = auto()
    LOWERCASE_HEX = auto()
    UPPERCASE_HEX = auto()
    MIXED_CASE_HEX = auto()
    KNOWN_WORD = auto()
    NOT_BASE64 = auto()
    BASE64_ENCODED_GIF = auto()
    BASE64_ENCODED_JPEG = auto()
    BASE64_ENCODED_PNG = auto()
    BASE64_ENCODED_SVG = auto()
    BASE64_ENCODED_WEBP = auto()
    BASE64_ENCODED_WOFF = auto()
    BASE64_ENCODED_DATA = auto()
    BASE64_ENCODED_UTF8 = auto()
    BASE64_ENCODED_JSON_SANDWICH = auto()
    UNCATEGORIZABLE = auto()  # i.e. don't train on it!
    UNLABELLED = auto()

def label_for(token: str) -> Label:
    filetype = FileType.from_base64_encoded(token)
    if filetype is not None:
        return getattr(Label, f"BASE64_ENCODED_{filetype.name}")
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
    decoded_data = _forced_b64decode(token)
    decoded_utf8 = _try_decode(decoded_data, "utf-8")
    if decoded_utf8:
        # The probability that a random sequence of N bytes will be valid
        # UTF-8 approximates Pn ~ 0.87739479563671 * 0.56471777839234**N.
        # -- https://math.stackexchange.com/a/751707
        # That's <1% at 8 bytes, <0.1% at 12, <0.01% at 16, <0.001% at 20.
        #
        # Except, beware, "random" binary data encoded as base64 might be
        # structured in such a way that it decodes as valid UTF-8.  The
        # obvious example is some bytes which all have their MSB unset.
        # XXX is random *uppercase* text more likely to decode this way?
        # XXX filter on isprintable() ?
        if len(decoded_utf8) >= 12 and token not in FALSE_BASE64_ENCODED_UTF8:
            # I eyeballed all with 12 <= length < 20.  A lot of the decoded
            # utf-8 was garbage, but only the single false positive looked
            # to be anything other than keysmash, which is kind of what we're
            # trying to identify here so I think that's ok.
            return Label.BASE64_ENCODED_UTF8
        if len(token) >= 20 and token not in FALSE_BASE64_ENCODED_UTF8:
            # Actually it's len(token) that's the N in Pn above, but I've
            # eyeballed all those tokens now so I'm keeping the above code!
            # Much of the above comments still apply: a lot of the decoded
            # utf-8 looks like garbage but only one token in this length
            # range didn't look like keysmash ("666666666666666666em")
            return Label.BASE64_ENCODED_UTF8
        if len(token) >= 18 and token not in FALSE_BASE64_ENCODED_UTF8:
            # I eyeballed these too, the only non-keysmash token in this
            # range is the one with len(decoded_utf8) >= 12.  There look
            # to be a fair few where token is multiple concatenated words
            # below that threshold so that's really the limit I think.
            return Label.BASE64_ENCODED_UTF8
        if is_known_word(decoded_utf8):
            return Label.BASE64_ENCODED_UTF8
        try:
            _ = json.loads(decoded_utf8)
            return Label.BASE64_ENCODED_UTF8
        except json.JSONDecodeError:
            pass
        assert len(token) <= 20
        # ...fall through...
    if len(token) >= 128:
        if token.count("x") == len(token):
            return Label.UNCATEGORIZABLE
        if token.startswith("101110101010102"):
            return Label.NOT_BASE64
        # All eyeballed, all keysmash
        return Label.BASE64_ENCODED_DATA
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
        line = f"{num_tokens:>8}: {label.name}"
        if label is Label.UNLABELLED:
            line = f"{line} ({num_tokens / 11931.96:.1f}%)"
        print(line)

# NOTES:
# - not all source tokens are valid base64
# - some are hex/decimal (i.e. easily identifiable as not base64)
#
# make a training set with the same distribution of lengths?
# (with a each length bin having an equal number of b64/not b64?)
# - or, make the distribution flat with regards to length, so it
#   can't learn length as a discriminator
# - don't even have all base64 be a multiple of four bytes long
# - and def don't leave any equals signs in there!
#
# Things it'll be interesting to see what a classifier makes of:
# - FALSE_HEX
# - Label.MIXED_CASE_HEX
# - Tokens like CABEIABQAFAMBEQACEQEDEQH, CABEIABUAFQMBEQACEQEDEQH,
#   ACwAAAAAAQABAAACADs.
#   decode as valid UTF-8, but are more likely binary data whose
#   layout made decoding as valid UTF-8 more likely than random
#   chance.
# - "666666666666666666em" (decodes to 5-character CJK!)
# - the one that's ~1600 "x"s
# - 101110101010102000000062000000052000000062000000012dd33a6c1200000096200000000200000002300000000300000000300000006/TSPD/300000008TSPD (=long but not base64)
#
# Possible augmentation:
# - some MIXED_CASE_HEX are concatenated single-case hex: worth splitting?
