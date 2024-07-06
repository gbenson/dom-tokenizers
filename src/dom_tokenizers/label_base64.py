import json
import os
import re

from base64 import b64encode
from collections import defaultdict
from collections.abc import Iterable
from enum import Enum, auto
from typing import Optional

from datasets import load_dataset as _load_dataset
from vec64 import CT, Span, base64_symbol_indexes, split as vec64_split

from .base64_labels import Label, KNOWN_LABELS
from .base64_skew import base64_probability
from .base64_words import GARBAGE_WORDS, MIXED_CASE_WORDS
from .internal.base64 import b64decode


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

    _KNOWN_WORDS = set(
        word
        for rank, word in _KNOWN_WORDS.items()
        if (len(word) > 3
            or (len(word) == 3 and rank < 20910)
            or (len(word) == 2 and rank < 10172)
            or (len(word) == 1 and rank < 91))
    )

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

_KNOWN_WORDS.difference_update(GARBAGE_WORDS)

_KNOWN_WORDS.update((
    "bg", "fb", "fn", "js", "px", "qr", "ui",

    "amt", "btn", "cdn", "css", "faq", "gif", "hex", "ids", "img", "ios",
    "jsp", "moz", "msg", "mui", "nav", "obj", "php", "pix", "rgb", "rss",
    "sdk", "seo", "sso", "svg", "txt", "uid", "uri", "url", "utf", "www",
    "xml", "dtd", "cto", "sha",

    "creds", "refetch", "ccbysa", "litespeed",

    "aarch64", "bzip2", "ipv4", "ipv6", "oauth2", "xfree86",
))

def is_known_word(token):
    return token.lower() in _KNOWN_WORDS

def label_for_number_or_word(token):
    candidate = token.lower()
    if candidate in _KNOWN_WORDS:
        return Label.KNOWN_WORD
    candidate = candidate.rstrip("0123456789")
    wordlen = len(candidate)
    numlen = len(token) - wordlen
    if numlen < 6:
        NOT_KNOWN_WORD = None
    elif wordlen < numlen:
        return Label.DECIMAL_NUMBER
    else:
        NOT_KNOWN_WORD = Label.DECIMAL_NUMBER
    cased_candidate = token[:wordlen]
    if candidate not in _KNOWN_WORDS:
        return NOT_KNOWN_WORD
    if not numlen:
        return Label.KNOWN_WORD
    # Be selective about case when we're comparing deindexed.
    if cased_candidate in MIXED_CASE_WORDS:
        return Label.KNOWN_WORD
    if cased_candidate.isupper() or cased_candidate.islower():
        return Label.KNOWN_WORD
    if cased_candidate == candidate.title():
        return Label.KNOWN_WORD
    if cased_candidate[-1] == "v" and (
            cased_candidate[:-1].isupper() and
            int(token[len(candidate):]) in range(1, 11)):
        return Label.KNOWN_WORD
    return NOT_KNOWN_WORD

def is_normally_cased(word):
    lower = word.lower()
    if word == lower:
        return True
    if word == word.upper():
        return True
    if word == lower.title():
        return True
    return False

_WORD_RE = re.compile(r"(?:[A-Za-z]+'?)+")

def is_delimited_known_words(token, *, cutoff=3, min_known_length=6):
    # Enforcing a minimum known length of 6 allows us to have the
    # low default cutoff of 3 without matching things which are a
    # just single five letter words, which gives false positives.
    # N.B. the next line with the <= is correct, whole word matches
    # are handled before this check is used, which means we can say
    # min_token_length = min_known_length + 1 since there must be
    # at least one non-word character in there.
    if len(token) <= min_known_length:
        return False

    known_words = [
        word
        for word in _WORD_RE.findall(token)
        if (wordlen := len(word)) >= 4
        and is_known_word(word)
        and (wordlen > 5 or is_normally_cased(word))
    ]
    if not known_words:
        return False
    known_lengths = list(map(len, known_words))
    if max(known_lengths) < 5:
        return False
    known_length = sum(known_lengths)
    if known_length < min_known_length:
        return False
    known_fraction = known_length / len(token)

    return max(known_lengths) * known_fraction > cutoff

_CAMEL_WORD_RE = re.compile(r"""
        (?: ^[a-z]+
           | [A-Z](?:[a-z]+|[A-Z]*)
        )
        [0-9]*(?=[A-Z]|$)""", re.X)

def camel_split(text):
    words = _CAMEL_WORD_RE.findall(text)
    if len(words) < 2:
        return None
    if "".join(words) != text:
        return None
    word_lengths = [len(word) for word in words]
    if max(word_lengths) <= 2:
        return None
    return words

_CAMEL_CUTOFF = 80  # junk very suddenly appears here!
# (actually not surprising: 80 = 1 + 4, so, 4smash + 1random letter)

def is_camelcase(token):
    words = camel_split(token)
    if not words:
        return False

    deindexed_words = [word.rstrip("0123456789") for word in words]
    word_is_known = [is_known_word(word) for word in deindexed_words]
    if not any(word_is_known):
        return False

    deindexed_lengths = list(map(len, deindexed_words))
    known_deindexed_lengths = [
        deindexed_length
        for deindexed_length, is_known in zip(
                deindexed_lengths, word_is_known)
        if is_known
    ]
    if max(known_deindexed_lengths) < 4:
        return False
    known_di = sum(known_deindexed_lengths)
    total_di = sum(deindexed_lengths)

    ratio = round(100 * known_di / total_di)
    return ratio > _CAMEL_CUTOFF

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

def _try_decode(data, *args, **kwargs):
    try:
        return data.decode(*args, **kwargs)
    except UnicodeDecodeError:
        return None

FALSE_BASE64_ENCODED_UTF8 = {
    "666666666666666666em", # decodes to 5-character CJK!
}

_DECIMAL_PREFIXED_STUFF_RE = re.compile("^\d{6,}")
_DECIMAL_SUFFIXED_STUFF_RE = re.compile("\d{6,}$")
_HEX_PREFIXED_STUFF_RE = re.compile("^[0-9a-f]{8,}")
_HEX_SUFFIXED_STUFF_RE = re.compile("[0-9a-f]{8,}$")

_FALSE_BASE64_ENCODED_ZEROS_RE = re.compile(r"/s\d+/")

def is_base64_encoded_zeros(token: str, splits: list[Span]) -> bool:
    if token[:4] in {"com/", "png/", "sam/"}:
        return False

    if (index := token.find("AAAA")) < 0:
        return False

    if index >= 3 and token[index-3:index] == "0x4":
        return False

    if splits[-1].ctype is not CT.LOWER:
        try:
            _ = int(token.lstrip("/"), 16)
            return False
        except ValueError:
            return True

    if (limit := splits[-1].start) < 3:
        return True

    if (start := token.rfind("/", 0, limit-1)) < 0:
        return True

    if _FALSE_BASE64_ENCODED_ZEROS_RE.match(token[start:limit]):
        return False

    return True

def interesting_splits(all_splits: list[Span]) -> Iterable[Span]:
    # Did everything end up in one unambiguous split?
    # If so then that one is the sole interesting split.
    if len(all_splits) == 1:
        yield all_splits[0]
        return

    # Did everything minus a bit of leading/trailing punctuation
    # end up on one unambiguous split?  If so then *that* one is
    # the sole interesting split.
    non_punct_splits = [
        split
        for split in all_splits
        if split.ctype != CT.PUNCT
    ]
    if len(non_punct_splits) == 1:
        yield non_punct_splits[0]
        return

    # Group splits by split location, so we have a list of candidate
    # splits of increasing length for each inter-punctuation region
    # of the token.
    splits_by_start = defaultdict(list)
    for split in non_punct_splits:
        splits_by_start[split.start].append(split)
    splits_by_start = list(splits_by_start.values())

    while splits_by_start:
        _, index, split = min(
            (split.probability, index, split)
            for index, split in enumerate(
                    splits[-1] for splits in splits_by_start
            )
        )
        yield split
        check = splits_by_start[index].pop()
        assert split is check
        splits_by_start = list(filter(None, splits_by_start))

_ALPHAHEX_WORD_PART_RE = re.compile(r"[a-f]{5,}")
_ALPHAHEX_WORDS_BY_PART = defaultdict(set)
for word in _KNOWN_WORDS:
    match = _ALPHAHEX_WORD_PART_RE.search(word)
    if not match:
        continue
    part = match.group()
    if part == word:
        continue
    _ALPHAHEX_WORDS_BY_PART[part].add(word)
del word, match, part

def is_alphahex_known_word_fragment(needle, haystack) -> bool:
    needles = _ALPHAHEX_WORDS_BY_PART.get(needle, ())
    for needle in needles:
        if needle in haystack:
            return True
    return False

def vec64_label_for(token: str, *, maxsplit: int = 32) -> Optional[Label]:
    symbols = base64_symbol_indexes(token)
    splits = vec64_split(symbols, maxsplit=maxsplit)

    if splits[-1].ctype is CT.BASE64:
        return Label.BASE64_ENCODED_DATA

    if is_base64_encoded_zeros(token, splits):
        return Label.BASE64_ENCODED_DATA

    # XXX note that some all-one-split CT.UPPER are keysmash, probably
    # from fragmented base64, so it's possible some CT.LOWER and *HEX
    # are too.  Maybe look for embedded words to confirm non-keysmash,
    # or maybe add a post-process check that tries to find tokens which
    # might be keysmash embedded in anything we've identified as base64
    # some other way.
    for span in interesting_splits(splits):
        if span.ctype is CT.ALNUM:
            continue  # too vague

        split = token[span.start:span.limit]

        is_whole_token = (
            (len(split) == len(token))
            or split == token.strip("+/=")
        )

        if not is_whole_token and span.probability > 1.5e-5:
            continue

        fraction = is_whole_token and 1 or (span.length / len(token))

        match span.ctype:
            case CT.DECIMAL:
                if is_whole_token:
                    return Label.DECIMAL_NUMBER
                if span.length >= 6:
                    return Label.DECIMAL_NUMBER

            case CT.LOWER:
                if is_known_word(split):
                    return Label.KNOWN_WORD
                if is_whole_token:
                    return Label.V64_LOWER
                return None  # XXX review

            case CT.UPPER:
                if is_known_word(split):
                    return Label.KNOWN_WORD
                if is_whole_token:
                    return Label.V64_UPPER
                return None  # XXX review

            case CT.LOWER_ALPHAHEX:
                if is_known_word(split):
                    return Label.KNOWN_WORD
                if is_whole_token:
                    return Label.LOWERCASE_HEX
                if is_alphahex_known_word_fragment(split, token):
                    return Label.KNOWN_WORD
                if len(split) < 6:
                    continue
                return Label.LOWERCASE_HEX

            case CT.UPPER_ALPHAHEX:
                if is_known_word(split):
                    return Label.KNOWN_WORD
                if is_whole_token:
                    return Label.UPPERCASE_HEX
                if is_alphahex_known_word_fragment(
                        split.lower(), token.lower()):
                    return Label.KNOWN_WORD
                if len(split) < 6:
                    continue
                if "AAAA" in split:
                    continue
                return Label.UPPERCASE_HEX

            case CT.ALPHAHEX:
                if is_known_word(split):
                    return Label.KNOWN_WORD
                if is_alphahex_known_word_fragment(
                        split.lower(), token.lower()):
                    return Label.KNOWN_WORD
                if is_camelcase(split):
                    return Label.CAMELCASE
                if len(split) < 6:
                    continue
                if "AAAA" in split:
                    continue
                assert is_whole_token
                return Label.MIXED_CASE_HEX

            case CT.LOWERHEX:
                return None  # XXX review
            case CT.UPPERHEX:
                return None  # XXX review
            case CT.HEX:
                return None  # XXX review
            case CT.ALPHA:
                return None  # XXX review
            case CT.LOWER_ALNUM:
                return None  # XXX review
            case CT.UPPER_ALNUM:
                return None  # XXX review

            case CT.PUNCT:
                assert len(split) == len(token)
                return Label.NOT_BASE64

        raise NotImplementedError(
            f"{span.ctype.name}:"
            f" {is_whole_token and 'full' or ('%4.1f%%' % (100*fraction))}"
            f" {span.probability} {token}")
    return None

def label_for(token: str) -> Label:
    filetype = FileType.from_base64_encoded(token)
    if filetype is not None:
        return getattr(Label, f"BASE64_ENCODED_{filetype.name}")

    label = vec64_label_for(token)
    if label is not None:
        return label

    if token.endswith("="):
        return Label.BASE64_ENCODED_DATA

    label = KNOWN_LABELS.get(token)
    if label is not None:
        return label

    # Ignore leading and trailing punctuation when looking for
    # decimal, hex, and known words in all their various forms.
    cleaned_token = token.lstrip("/+").rstrip("/+=")

    is_hex_token = is_hex(cleaned_token)
    if is_hex_token:
        if cleaned_token.isnumeric():
            return Label.DECIMAL_NUMBER
        if not cleaned_token.isalpha():
            return _label_for_hex(cleaned_token)
        # ...fall through...

    label = label_for_number_or_word(cleaned_token)
    if label:
        return label
    if is_delimited_known_words(cleaned_token):
        return Label.DELIMITED_WORDS
    if is_camelcase(cleaned_token):
        return Label.CAMELCASE

    if is_hex_token:
        return _label_for_hex(cleaned_token)

    dm = _DECIMAL_PREFIXED_STUFF_RE.match(cleaned_token)
    if (hm := _HEX_PREFIXED_STUFF_RE.match(cleaned_token)):
        if dm and len(dm.group()) >= len(hm.group()):
            return Label.DECIMAL_PREFIXED
        return Label.LOWERHEX_PREFIXED
    elif dm:
        return Label.DECIMAL_PREFIXED

    dm = _DECIMAL_SUFFIXED_STUFF_RE.search(cleaned_token)
    if (hm := _HEX_SUFFIXED_STUFF_RE.search(cleaned_token)):
        if dm and len(dm.group()) >= len(hm.group()):
            return Label.DECIMAL_SUFFIXED
        return Label.LOWERHEX_SUFFIXED
    elif dm:
        return Label.DECIMAL_SUFFIXED

    decoded_data = b64decode(token, fix_padding=True)
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
        if label_for_number_or_word(decoded_utf8):
            return Label.BASE64_ENCODED_UTF8
        try:
            _ = json.loads(decoded_utf8)
            return Label.BASE64_ENCODED_UTF8
        except json.JSONDecodeError:
            pass
        assert len(token) <= 20
        # ...fall through...
    assert not token.startswith("DID300000005https")
    if len(token) >= 128:
        if token.count("x") == len(token):
            return Label.NOT_BASE64
        assert not token.startswith("101110101010102")
        if token.startswith("573J8100L5093461D49F0C18L"):
            return Label.NOT_BASE64
        if token.upper() == token:
            assert base64_probability(token) < 0.41
            return Label.NOT_BASE64
        if token.startswith("lk5V736I0I0V2N2F234O3J4I7"):
            assert token[2:].upper() == token[2:]
            return Label.NOT_BASE64
        for prefix in ("+", "0x"):
            if not token.startswith(prefix):
                continue
            if not is_hex(token[len(prefix):]):
                continue
            assert token.lower() == token
            return Label.NOT_BASE64
        if (slash := token.rfind("/")) >= 0 and (
                slash * 2 < len(token) and
                len(token) - slash > 64):
            ending = token[slash + 1:]
            assert not is_hex(ending)
            if (p64 := base64_probability(ending)) > 0.74:
                return Label.BASE64_ENCODED_DATA
            assert p64 >= 0.59
            assert ending.upper() == ending
            return Label.NOT_BASE64  # XXX base32
        if token.startswith("rodents+monkeys+person+infected+"):
            return Label.NOT_BASE64
        # All eyeballed, all keysmash
        assert (base64_probability(token) > 0.59
                or "AAAAAAAAAAAAAAAAAA" in token)
        return Label.BASE64_ENCODED_DATA
    if token.startswith("landerForm"):
        _ = int(token[10:42], 16)
        return Label.CAMELCASE  # ish
    return Label.UNLABELLED

def _label_for_hex(token: str) -> Optional[Label]:
    if token.islower():
        return Label.LOWERCASE_HEX
    if token.isupper():
        return Label.UPPERCASE_HEX
    return Label.MIXED_CASE_HEX

# XXX look into these
_SPLITTER_FAIL_RE = re.compile(r"^(?:x|u00)(?:2[267]|3c|64)", re.I)

def main():
    bins = defaultdict(int)
    for row in load_dataset(SOURCE_DATASETS["unlabelled_tokens"]):
        text = row["text"]
        if len(text) < 5:
            continue
        while (match := _SPLITTER_FAIL_RE.match(text)):
            text = text[len(match.group(0)):]
            if len(text) < 5:
                break
        if len(text) < 5:
            continue
        for token in text.split("'"):
            if len(token) < 5:
                continue
            label = label_for(token)
            bins[label] += 1

    for _, label, num_tokens in sorted(
            (label.value, label, num_tokens)
            for label, num_tokens in bins.items()):
        line = f"{num_tokens:>8}: {label.name}"
        if label is Label.UNLABELLED:
            line = f"{line} ({num_tokens / 16168.15:.1f}%)"
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
# rather than the by-file-type taxonomy, maybe divide base64-encoded
# tokens into compressible and not?
#
# Things it'll be interesting to see what a classifier makes of:
# - Label.MIXED_CASE_HEX
# - Tokens like CABEIABQAFAMBEQACEQEDEQH, CABEIABUAFQMBEQACEQEDEQH,
#   ACwAAAAAAQABAAACADs.
#   decode as valid UTF-8, but are more likely binary data whose
#   layout made decoding as valid UTF-8 more likely than random
#   chance.
# - "666666666666666666em" (decodes to 5-character CJK!)
# - the one that's ~1600 "x"s
# - 1011101010101020...300000006/TSPD/300000008TSPD (=long but not base64)
# - "".join("1d2fe9f489591b866efe42250fb5b8e4962f39620bc2ec2762c68841d550"
#     "c1efc0ff55d0383623817683789ee52a808067b438a4c2c49f3c9fd47f5ab99ba0"
#     "2cZtbK192ipLnvPkJ4G9z6D7cTg616ptjDWARpGGUCwU" (=hex+tiny bit of b64)
#
# Possible augmentation:
# - some MIXED_CASE_HEX are concatenated single-case hex: worth splitting?
