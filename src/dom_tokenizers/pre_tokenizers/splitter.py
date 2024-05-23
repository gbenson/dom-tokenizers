import json
import re

from base64 import b64decode
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import chain
from posixpath import commonprefix

import magic

from unidecode import unidecode


_B64_RE_S = r"(?:[A-Za-z0-9+/]{4}){"
_B64_RE_E = r",}(?:[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?"


def base64_matcher(min_encoded_len=24):
    min_groups, extra = divmod(min_encoded_len, 4)
    if extra:
        min_groups += 1
    return re.compile(f"{_B64_RE_S}{min_groups}{_B64_RE_E}")


@dataclass
class TextSplitter:
    base64_token: str = "[BASE64]"
    long_token: str = "[LONG]"

    MAXWORDLEN = 32
    WORD_RE = re.compile(r"\w+(?:['’]\w+)*")
    ESCAPED_RE = re.compile(
        r"((?:%|\\x|\\u[0-9a-f]{2})[0-9a-f]{2})", re.I)
    HEX_RE = re.compile(r"^(?:0x|[0-9a-f]{2})[0-9a-f]{6,}$")
    DIGIT_RE = re.compile(r"\d")
    URLISH_RE = re.compile(r"(?:[a-z]+|[0-9a-f]+|[A-Z0-9]+)")
    SHORTEST_URLISH = 16
    LONGEST_PHITEST = 85
    BASE64_RE = base64_matcher()
    B64_PNG_RE = re.compile(r"iVBORw0KGg[o-r]")
    XML_HDR_RE = re.compile(r"<([a-z]{3,})\s+[a-z]+")

    def split(self, text: str) -> Iterable[str]:
        """Split a string into a sequence of tokens.

        It splits on any non-alphanumeric character, but also tries
        to detect (and recurse into) base64-encoded date, of which
        there's a lot in just the 295 `interesting-dom-snapshots`.
        (Not dealing with base64 results in a whole load of "words"
        which are just fragments of base64.  It isn't easy though,
        lots of regular text is valid base64, we have to sniff.)
        """
        return self._postprocess(
            chain.from_iterable(
                self._split(
                    self._preprocess(text))))

    def _preprocess(self, text):
        return "".join(
            self._unescape_char(s) if i & 1 else s
            for i, s in enumerate(self.ESCAPED_RE.split(text))
        )

    def _unescape_char(self, escaped):
        if escaped[0] == "%":
            escaped = "\\x" + escaped[1:]
        return eval(f'"{escaped}"')

    def _split(self, text):
        while text:
            match = self.BASE64_RE.search(text)
            if match is not None:
                start, limit = match.span()
            else:
                start = limit = len(text)
            if start > 0:
                yield self._split_words(text[:start])
            if limit > start:
                encoded = text[start:limit]
                matched = self._match_urlish_base64(encoded)
                if matched is not None:
                    limit = start + len(matched)
                    yield self._split_words(text[start:limit])
                else:
                    yield self._enter_base64(encoded)
            if limit == len(text):
                break
            text = text[limit:]

    def _split_words(self, text):
        # self.WORD_RE uses "\w" to match all unicode alphanumerics, but
        # that also matches "_" which we don't want, so we zap them here
        text = text.replace("_", " ")

        # We currently limit the characters in tokens to a small subset
        # of ASCII.  Allowing any uncode alphanumeric massively inflates
        # the tokenizer's base vocabulary, from 68 symbols to 1145 with
        # gbenson/interesting-dom-snapshots, and that's a small dataset
        # of which only a small fraction uses non-Latin alphabets.  If
        # nothing else this means we need a larger vocabulary and hence
        # more complex models, and it doesn't make sense to take that hit
        # without a more representative corpus or any way to create or
        # validate one.  Until then, we use unidecode to transliterate
        # non-ASCII characters, as a way to get meaning into embeddings
        # of non-Latin-alphabet texts.  It's by no means perfect, see
        # https://pypi.org/project/Unidecode/#frequently-asked-questions
        # for e.g. issues with CJK languages, but transliteration gets
        # at least some meaning, meaning we lose if we just drop all the
        # not-ASCII on the floor.  It also means we generate tokenizers
        # that can encode pretty much anything, from the BMP at least.
        words = []
        for word in self.WORD_RE.findall(text):
            if word.isascii():
                words.append(word)
            else:
                words.extend(self._split_words(unidecode(word)))
        return [word.lower() for word in words]

    def _match_urlish_base64(self, encoded):
        urlish = "/".join(self.URLISH_RE.findall(encoded))
        result = commonprefix((encoded, urlish))
        if len(result) < self.SHORTEST_URLISH:
            return None
        return result

    def _enter_base64(self, encoded):
        # Lots of false-positives here, try sniffing
        if self.B64_PNG_RE.match(encoded):
            return [self.base64_token, "png"]
        data = b64decode(encoded)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is not None:
            return self._enter_base64_utf8(text)
        return self._enter_base64_binary(data, encoded)

    def _enter_base64_utf8(self, text):
        # XXX recurse??
        match = self.XML_HDR_RE.match(text)
        if match is not None:
            if match.group(1) == "svg":
                return [self.base64_token, "svg"]
            return [self.base64_token, "xml"]
        try:
            _ = json.loads(text)
            return [self.base64_token, "json"]
        except json.JSONDecodeError:
            pass
        return [self.base64_token, "utf", "8"]

    def _enter_base64_binary(self, data, encoded):
        # Not out of false-positive territory yet
        full_magic = magic.from_buffer(data)
        easy_magic = full_magic.split(maxsplit=1)[0]
        if easy_magic in {"GIF", "zlib", "JPEG"}:
            return [self.base64_token, easy_magic.lower()]
        if " Web/P image" in full_magic:
            return [self.base64_token, "webp"]
        if full_magic.startswith("Web Open Font Format"):
            return [self.base64_token, "woff"]
        if len(encoded) > self.LONGEST_PHITEST:
            return [self.base64_token]
        # phi test for monoalphabeticity
        hist = defaultdict(int)
        for symbol in encoded:
            hist[symbol] += 1
        phi_o = sum(freq * (freq - 1) for freq in hist.values())
        N = len(encoded)
        phi_r = N * (N - 1) / 64
        # non-standard comparison (observed phi > twice random)
        if phi_o > phi_r * 2:
            return self._split_words(encoded)
        return [self.base64_token]

    def _postprocess(self, tokens: Iterable[str]) -> Iterable[str]:
        for token in tokens:
            if self.HEX_RE.match(token):
                yield self.long_token
                try:
                    _ = int(token)
                except ValueError:
                    yield "hex"
                yield "digits"
                continue

            if len(token) <= self.MAXWORDLEN:
                yield token
                continue

            yield self.long_token
            if self.DIGIT_RE.search(token):
                yield "alphanumeric"
            else:
                yield "alphabetic"
