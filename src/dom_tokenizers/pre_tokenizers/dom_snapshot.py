import json
import re

from base64 import b64decode
from collections import defaultdict
from collections.abc import Iterable
from functools import cached_property
from itertools import chain
from posixpath import commonprefix
from typing import List
from xml.dom import Node

import magic

from tokenizers import NormalizedString, PreTokenizedString


class DOMSnapshotPreTokenizer:
    """Pre-tokenizer that consumes JSON-serialized DOM snapshots
    and emits tokenized representations of the snapshotted DOMs.
    """
    bos_token = "[BOS]"        # beginning of sequence
    eos_token = "[EOS]"        # end of sequence
    sep_token = "[SEP]"        # separator between documents
    elem_token = "[TAG]"       # beginning of element name
    attr_token = "[ATTR]"      # beginning of attribute
    comm_token = "[COMMENT]"   # beginning of comment
    base64_token = "[BASE64]"  # beginning of some base64
    long_token = "[LONG]"      # elided long token

    @property
    def special_tokens(self):
        return [
            value
            for attr, value in self.__class__.__dict__.items()
            if attr.endswith("token")
        ]

    def pre_tokenize(self, pretok: PreTokenizedString):
        """Pre-tokenize a :class:`~tokenizers.PyPreTokenizedString` in-place.
        """
        pretok.split(self._split_json)

    def _split_json(self, i: int, s: NormalizedString) -> List[NormalizedString]:
        snapshot = json.loads(s.normalized)

        # Unpack the snapshot if what we have is a raw browser response
        if not any(key in snapshot for key in ("documents", "strings")):
            snapshot = snapshot.get("result", snapshot)

        return list(chain.from_iterable(self._split_serialized(snapshot)))

    def _split_serialized(self, snapshot: dict) -> Iterable[List[NormalizedString]]:
        emitter = TokenEmitter(self, snapshot)
        elem_token = [NormalizedString(self.elem_token)]
        attr_token = [NormalizedString(self.attr_token)]

        for document_index, document in enumerate(snapshot["documents"]):
            token = self.bos_token if document_index == 0 else self.sep_token
            yield [NormalizedString(token)]

            nodes = document["nodes"]
            for node_index, node_values in enumerate(zip(
                    nodes["nodeType"],
                    nodes["nodeName"],
                    nodes["nodeValue"],
                    nodes["attributes"])):
                node_type, name_index, value_index, attr_indexes = node_values

                match node_type:
                    case Node.ELEMENT_NODE:
                        yield elem_token
                        yield emitter.emit(name_index)
                        for attr_index in range(0, len(attr_indexes), 2):
                            yield attr_token
                            yield emitter.emit(attr_indexes[attr_index])
                            yield emitter.emit(attr_indexes[attr_index + 1])

                    case Node.TEXT_NODE:
                        yield emitter.emit(value_index)

                    case Node.COMMENT_NODE:
                        yield [NormalizedString(self.comm_token)]
                        yield emitter.emit(value_index)

        yield [NormalizedString(self.eos_token)]


_B64_RE_S = r"(?:[A-Za-z0-9+/]{4}){"
_B64_RE_E = r",}(?:[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?"


def base64_matcher(min_encoded_len=24):
    min_groups, extra = divmod(min_encoded_len, 4)
    if extra:
        min_groups += 1
    return re.compile(f"{_B64_RE_S}{min_groups}{_B64_RE_E}")


class TokenEmitter:
    MAXWORDLEN = 32
    WORD_RE = re.compile(
        r"[a-z0-9]+(?:[a-z0-9']*[a-z0-9])?")  # XXX English only :(
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

    def __init__(self, pretokenizer: DOMSnapshotPreTokenizer, snapshot: dict):
        self._pt = pretokenizer
        self._strings = snapshot["strings"]
        self._tokens = {}

    @cached_property
    def base64_token(self):
        return self._pt.base64_token

    @cached_property
    def long_token(self):
        return self._pt.long_token

    def emit(self, string_index: int) -> Iterable[NormalizedString]:
        """Emit tokens for one string in a DOM snapshot's string table.

        It splits on any non-alphanumeric character, but also tries
        to detect (and recurse into) base64-encoded date, of which
        there's a lot in just the 295 `interesting-dom-snapshots`.
        (Not dealing with base64 results in a whole load of "words"
        which are just fragments of base64.  It isn't easy though,
        lots of regular text is valid base64, we have to sniff.)
        """
        if string_index < 0:
            return []
        tokens = self._tokens.get(string_index)
        if tokens is not None:
            return tokens
        tokens = [
            NormalizedString(token)
            for token in self._postprocess(
                    chain.from_iterable(
                        self._split(
                            self._preprocess(
                                self._strings[string_index]))))
        ]
        self._tokens[string_index] = tokens
        return tokens

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
        return self.WORD_RE.findall(text.lower())

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
