import logging
import re

from base64 import b64decode
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import unquote

import magic

from unidecode import unidecode

from ..internal import json

logger = logging.getLogger(__name__)
debug = logger.debug


class MandatorySplit:  # pragma: no cover
    def __repr__(self):
        return "SPLIT"


SPLIT = MandatorySplit()

_B64_RE_S = r"(?:[A-Za-z0-9+/]{4}){"
_B64_RE_E = r",}(?:[A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?"


def base64_matcher(min_encoded_len=24):
    min_groups, extra = divmod(min_encoded_len, 4)
    if extra:  # pragma: no cover
        min_groups += 1
    return re.compile(f"^{_B64_RE_S}{min_groups}{_B64_RE_E}$")


class FalseBase64Error(RuntimeError):
    pass


@dataclass
class TextSplitter:
    base64_token: str = "[BASE64]"
    long_token: str = "[LONG]"

    @property
    def special_tokens(self) -> Iterable[str]:
        return (v for k, v in self.__dict__.items() if k.endswith("_token"))

    # Partially split into words, but retain the non-word characters
    # until everything's de-escaped and base64 is identified.
    # - `+/=` are allowed within words here to keep base64-encoded
    #   data in one "word".
    # - Apostrophes are... included for now XXX
    # - Underscores are included in "\w", so we have to handle them.
    BASE64_NONWORD = "+/="
    FIRST_SPLIT_RE = re.compile(rf"([^\w'’{BASE64_NONWORD}]+)")
    BASE64_NONWORD_RE = re.compile("[+/=]+")

    _TWOHEX = "[0-9a-fA-F]{2}"
    TWOHEX_RE = re.compile(_TWOHEX)
    JS_CHAR_ESCAPE_RE = re.compile(f"(?:x|u{_TWOHEX}){_TWOHEX}")
    ENTITY_STARTS = {"&", "&#"}
    ESCAPE_START_RE = re.compile(r".([&%\\])")
    PREFIXED_HEX_RE = re.compile(r"^(0x)([0-9a-f]+)([+/=]*)$", re.I)

    # XXX older bits
    MAXWORDLEN = 32
    WORD_RE = re.compile(r"(?:\w+['’]?)+")
    HEX_RE = re.compile(r"^(?:0x|[0-9a-f]{2})[0-9a-f]{6,}$", re.I)
    DIGIT_RE = re.compile(r"\d")
    LONGEST_URLISH = 1024  # XXX?
    URLISH_LOOKBACK = 5
    URLISH_THRESHOLD = 2  # XXX review?
    URLISH_THINGS = {
        "css",
        "href",
        "http",
        "https",
        "src",
        "static",
        "url",
        "www",
    }
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
        VERBOSE = logger.isEnabledFor(logging.DEBUG)
        if VERBOSE and len(text) < 4096:  # pragma: no cover
            debug("input: \x1B[44;36m%s\x1B[0m", text)

        splits = [text]
        cursor = 0
        last = None
        while cursor < len(splits):
            this = (cursor, len(splits))
            if this != last:
                loop = 100
            elif (loop := loop - 1) < 1:  # pragma: no cover
                raise RuntimeError("stuck?")
            last = this

            curr = splits[cursor]
            if VERBOSE:  # pragma: no cover
                if len(splits) < 32:
                    debug(" ".join(
                        f"""\x1B[{'48;5;15;1;31'
                        if index == cursor
                        else '48;5;248;30'}m{split}\x1B[0m"""
                        for index, split in enumerate(splits)))
                else:
                    debug("curr: %s", repr(curr))

            # Pop empty strings and whitespace
            cursor, is_changed = _pop_unless_nonempty(curr, cursor, splits)
            if is_changed:
                if VERBOSE:  # pragma: no cover
                    debug("it's whitespace or splits")
                continue

            # Are we looking at URL-encoding (`%xx` escapes)?
            if curr == "%":
                if VERBOSE:  # pragma: no cover
                    debug("it's urlencoded")
                cursor = self._sub_urlencoded(splits, cursor)
                continue

            # Are we looking at Javascript escaping?
            if curr[0] == "\\":
                if VERBOSE:  # pragma: no cover
                    debug("it's escaped")
                cursor = self._sub_js_escape(splits, cursor)
                continue

            # Are we looking at character entities?
            if curr in self.ENTITY_STARTS:
                if VERBOSE:  # pragma: no cover
                    debug("it's an entity")
                cursor = self._sub_html_entity(splits, cursor)
                continue

            # Split on "_" (have to do this b/c "\w" matches it)
            new_splits = curr.split("_")
            if len(new_splits) > 1:
                if VERBOSE:  # pragma: no cover
                    debug("it's stuff with underscores")
                splits[cursor:cursor+1] = new_splits
                continue

            # Are we looking at some prefixed hex?
            if (match := self.PREFIXED_HEX_RE.match(curr)):
                if VERBOSE:  # pragma: no cover
                    debug("prefixed hex")
                new_splits = [s for s in match.groups() if s]
                splits[cursor:cursor+1] = new_splits
                cursor += len(new_splits)
                continue

            # Are we looking at something that might be base64?
            if self.BASE64_RE.match(curr):
                cursor = self._sub_base64(splits, cursor)
                continue

            # Is the whole thing one word?
            words = self.WORD_RE.findall(curr)
            if len(words) == 1 and words[0] == curr:
                if not curr.isascii():
                    unidecoded = unidecode(curr)
                    if unidecoded == curr:  # pragma: no cover
                        debug("it's some non-ASCII that didn't change?")
                        cursor += 1  # skip it
                    else:
                        if VERBOSE:  # pragma: no cover
                            debug("it's some non-ASCII")
                        splits[cursor] = unidecoded
                    continue

                if VERBOSE:  # pragma: no cover
                    debug("it's a single word")
                cursor += 1
                continue
            # XXX mpve this split below the next?
            # XXX and make it drop *all* words at once
            # XXX (for performance)

            # Split on nonword except base64 and apostrophe
            new_splits = self.FIRST_SPLIT_RE.split(curr)
            start = 0
            limit = len(new_splits)
            while start < limit and not new_splits[start]:
                start += 1
            while start < limit and not new_splits[limit - 1]:
                limit -= 1
            if limit - start > 1:
                if VERBOSE:  # pragma: no cover
                    debug("it's splittable")
                splits[cursor:cursor+1] = new_splits[start:limit]
                continue

            # Is the whole thing just a blob of nonword smush?
            if not words:
                # Check for embedded escape sequences
                if len(curr) > 1 and (m := self.ESCAPE_START_RE.search(curr)):
                    if VERBOSE:  # pragma: no cover
                        debug("it's peelable")
                    limit = m.span(1)[0]
                    splits[cursor:cursor+1] = [curr[:limit], curr[limit:]]
                    continue

                if VERBOSE:  # pragma: no cover
                    debug("it's nonword smush")
                splits[cursor] = SPLIT
                cursor += 1
                continue

            # Do we have some words?
            if words:
                if VERBOSE:  # pragma: no cover
                    debug("it's some words")
                splits[cursor:cursor+1] = words + [SPLIT]
                continue

            if True:  # pragma: no cover
                print("done:", splits[:cursor])
                print("todo:", splits[cursor:])
                print("words:", words)
                raise NotImplementedError

        result = self._postprocess(splits)
        if VERBOSE:  # pragma: no cover
            result = list(result)
            if len(result) < 256:
                debug("output: %s", " ".join(
                    f"\x1B[44;36m{split}\x1B[0m"
                    for split in result
                ))
        return result

    def _sub_js_escape(self, splits, cursor):
        curr = splits[cursor]
        cursor_limit = cursor + 1

        # Ensure `curr` holds a complete sequence, minus the initial backslash
        if len(curr) > 1:
            # Trim the initial backslash
            curr = curr[1:]
        elif cursor_limit >= len(splits):
            # Terminal backslash
            splits.pop(cursor)
            return cursor
        else:  # curr == "\\"
            curr = splits[cursor_limit]
            cursor_limit += 1

        # Store what we want at `splits[cursor:cursor_limit]` in `result`.
        match curr[0]:
            case "'":
                result = [curr]

            case c if c in 'bfnrtv0"\\':
                result = [SPLIT, curr[1:]]  # split on the escaped character

            case c if c in "ux":
                matched = self.JS_CHAR_ESCAPE_RE.match(curr)
                if not matched:
                    result = [SPLIT, curr]  # split on the backslash
                else:
                    matched = matched.group(0)
                    result = [
                        f"{chr(int(matched[1:], 16))}{curr[len(matched):]}"]

            case _:
                result = [SPLIT, curr]  # split on the backslash

        # Merge result into the surrounding tokens as appropriate.
        return self._merge_result(splits, cursor, cursor_limit, result)

    def _sub_html_entity(self, splits, cursor):
        cursor_limit = cursor + 3
        if cursor_limit > len(splits):
            # Split on the "&" or "&#"
            splits[cursor] = SPLIT
            return cursor + 1

        curr, value, term = splits[cursor:cursor_limit]
        if not term or term[0] != ";":
            # Split on the "&" or "&#"
            splits[cursor] = SPLIT
            return cursor + 1
        trailer = term[1:]

        # Store what we want at `splits[cursor:cursor_limit]` in `result`.
        if curr == "&":
            if value == "apos":
                result = ["'"]
            elif value.isalnum():
                result = [SPLIT, ""]
            else:
                # Split on the "&" or "&#"
                splits[cursor] = SPLIT
                return cursor + 1
        elif value[0] in "xX":
            try:
                result = [chr(int(value[1:], 16))]
            except ValueError:
                # Split on the "&" or "&#"
                splits[cursor] = SPLIT
                return cursor + 1
        else:
            try:
                result = [chr(int(value))]
            except ValueError:
                # Split on the "&" or "&#"
                splits[cursor] = SPLIT
                return cursor + 1
        if trailer:
            splits.insert(cursor_limit, trailer)

        # Merge result into the surrounding tokens as appropriate.
        return self._merge_result(splits, cursor, cursor_limit, result)

    @staticmethod
    def _merge_result(
            splits: list,
            cursor: int,
            cursor_limit: int,
            result: list):
        """Overwrite `splits[cursor:cursor_limit]` with `result`,
        merging `result[0]` into `splits[cursor-1]` and
        `result[-1]` into `splits[cursor_limit]` where possible.
        """
        if cursor > 0:
            prev_split = splits[cursor - 1]
            if result[0] is SPLIT:
                if prev_split is SPLIT:
                    result.pop(0)
            elif prev_split is not SPLIT:
                result[0] = f"{prev_split}{result[0]}"
                cursor -= 1
        if cursor_limit < len(splits):
            result[-1] = f"{result[-1]}{splits[cursor_limit]}"
            cursor_limit += 1
        splits[cursor:cursor_limit] = result
        return cursor

    def _sub_urlencoded(self, splits, cursor):
        assert splits[cursor] == "%"
        parts = []
        while cursor < len(splits) and splits[cursor] == "%":
            splits.pop(cursor)  # will just drop "%" if not part of `%xx`
            if cursor >= len(splits):
                break
            curr = splits[cursor]
            if not self.TWOHEX_RE.match(curr):
                break
            parts.append("%")
            if len(curr) == 2:
                parts.append(curr)
                splits.pop(cursor)
                continue
            assert len(curr) > 2
            parts.append(curr[:2])
            splits[cursor] = curr[2:]
            break
        if not parts:
            return cursor
        parts = [unquote("".join(parts))]
        if cursor > 0 and splits[cursor - 1] is not SPLIT:
            cursor -= 1
            parts.insert(0, splits.pop(cursor))
        if cursor < len(splits):
            parts.append(splits.pop(cursor))
        splits.insert(cursor, "".join(parts))
        return cursor

    def _sub_base64(self, splits, cursor):
        curr = splits[cursor]
        try:
            # Is this part of a URL?  The last piece of domain and any number
            # of path components can blob together and look like valid base64.
            if self._is_urlish_looking_base64(splits, cursor):
                raise FalseBase64Error("part of a URL")

            # It's not obviously part of a URL, time to pull out the big guns
            splits[cursor:cursor + 1] = self._enter_base64(curr)
            if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
                if splits[cursor] == self.base64_token:
                    debug("it's base64?")
            cursor += 1
            return cursor

        except FalseBase64Error as e:
            debug("its %s that looked like base64", str(e))
            parts = self.BASE64_NONWORD_RE.split(curr, maxsplit=1)
            splits[cursor:cursor + 1] = parts
            if len(parts) == 1:
                cursor += 1  # whole token already processed
            return cursor

    def _is_urlish_looking_base64(self, splits, cursor):
        curr = splits[cursor]

        # Avoid processing giant blocks of base64.
        if len(curr) > self.LONGEST_URLISH:
            return False

        # Equals signs are not something we expect to see in URL paths.
        # We shouldn't be called without `curr` being valid base64,
        # which means we only have to check the last character because
        # if any characters in are "=" then the last character is "=".
        if curr[-1] == "=":
            return False

        # Plus signs are valid in URL paths, but they're hardly common,
        # so we assume this isn't a URL piece if we find any.  (Pluses
        # are common in the query string, but query strings don't often
        # look like base64, and they're split from the path by the "?"
        # so we don't have to consider that here.
        if "+" in curr:
            return False

        # Doubled slashes are not valid in this part of the URL.
        if "//" in curr:
            return False

        # Split what we have to look for URLish things.
        count = 0
        for split in self.WORD_RE.findall(curr.replace("_", " ")):
            if split not in self.URLISH_THINGS:
                continue
            count += 1
            if count >= self.URLISH_THRESHOLD:
                return True

        # Not quite looking URLish?  Try looking back...
        for index in range(cursor-1,
                           max(cursor-self.URLISH_LOOKBACK, -1),
                           -1):
            if splits[index] is SPLIT:
                continue
            if splits[index] not in self.URLISH_THINGS:
                if not splits[index].endswith("cdn"):
                    continue
            count += 1
            if count >= self.URLISH_THRESHOLD:
                return True

        return False

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
        return [self.base64_token, "utf-8"]

    def _enter_base64_binary(self, data, encoded):
        # Not out of false-positive territory yet
        full_magic = magic.from_buffer(data)
        easy_magic = full_magic.split(maxsplit=1)[0]
        if easy_magic in {"GIF", "zlib", "JPEG"}:
            return [self.base64_token, easy_magic]
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
        # non-standard comparison (observed phi >= twice random)
        if phi_o > phi_r * 2:
            raise FalseBase64Error("text")
        return [self.base64_token]

    def _postprocess(self, tokens: Iterable[str]) -> Iterable[str]:
        for token in tokens:
            if token is SPLIT:
                continue

            # self.WORD_RE allows words to end with apostrophes, which
            # is desirable during processing so as not to strip them
            # while we're part-way through building words from escaped
            # characters, but we have to drop them them from the final
            # tokenizer output to avoid filling the vocabulary with
            # terminal-quotes.
            token = token.rstrip("'")

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


def _pop_unless_nonempty(curr, cursor, splits):
    if curr is SPLIT:
        return cursor + 1, True

    if curr:
        if not curr[0].isspace():
            return cursor, False
        curr = curr.lstrip()

    if cursor > 0 and splits[cursor-1] is not SPLIT:
        if curr:
            splits[cursor:cursor+1] = [SPLIT, curr]
            cursor += 1
        else:
            splits[cursor] = SPLIT
    elif curr:
        splits[cursor] = curr
    else:
        splits.pop(cursor)
    return cursor, True
