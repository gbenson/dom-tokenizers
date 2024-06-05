import os

from collections import defaultdict
from dataclasses import make_dataclass
from xml.dom import Node

from tokenizers import NormalizedString

from ..internal import json
from .compat_itertools import batched
from .html import is_void_element
from .pre_tokenizer import PreTokenizer
from .splitter import TextSplitter, Flags as Split
from .token_buffer import TokenBuffer


class DOMSnapshotPreTokenizer(PreTokenizer):
    """Pre-tokenizer that consumes JSON-serialized DOM snapshots
    and emits tokenized representations of the snapshotted DOMs.
    """
    _SENTINEL = type("Sentinel", (), dict(index=-1))

    def pre_tokenize_dom(self, buf: TokenBuffer, serialized: str):
        """Transform a serialized DOM into a sequence of tokens.
        """
        snapshot = json.loads(serialized)

        # Unpack the snapshot if what we have is a raw browser response
        if not any(key in snapshot for key in ("documents", "strings")):
            snapshot = snapshot.get("result", snapshot)

        split = TokenCache(snapshot["strings"], self._splitter).get

        for document in snapshot["documents"]:
            stack = [self._SENTINEL]
            for node in _Node.each(document["nodes"]):
                while stack[-1].index != node.parent_index:
                    self._terminate(buf, split, stack.pop())

                match node.type:
                    case Node.ELEMENT_NODE:
                        buf.append("<")
                        buf.extend(split(node.name_index, Split.TAG_NAME))
                        for name_index, value_index in node.attr_indexes:
                            buf.append("_")
                            buf.extend(split(name_index, Split.ATTR_NAME))
                            buf.append("=")
                            buf.extend(split(value_index, Split.ATTR_VALUE))
                        buf.append(">")
                        stack.append(node)

                    case Node.TEXT_NODE:
                        buf.extend(split(node.value_index, Split.TEXT))

                    case Node.DOCUMENT_NODE:
                        stack.append(node)

                    case Node.COMMENT_NODE:
                        buf.append("<!--")
                        buf.extend(split(node.value_index, Split.COMMENT))
                        buf.append("-->")

                    case Node.DOCUMENT_TYPE_NODE:
                        buf.append("<!DOCTYPE")
                        buf.extend(split(node.name_index, Split.DOCTYPE))
                        public_index = document["publicId"]
                        if public_index >= 0:
                            buf.append("PUBLIC")
                            buf.extend(split(public_index, Split.DOCTYPE))
                        system_index = document["systemId"]
                        if system_index >= 0:
                            buf.extend(split(system_index, Split.DOCTYPE))
                        buf.append(">")

        for node in reversed(stack[2:]):
            self._terminate(buf, split, node)

    @staticmethod
    def _terminate(buf, split, node):
        tokens = split(node.name_index, Split.TAG_NAME)
        if is_void_element(tokens[-1].original):
            return
        buf.append("</")
        buf.extend(tokens)
        buf.append(">")


class _BaseNode:
    FIELDS = {
        "parentIndex": ("parent_index", int),
        "nodeType": ("type", int),
        "nodeName": ("name_index", int),
        "nodeValue": ("value_index", int),
        "attributes": ("_attr_indexes", list[int]),
    }

    @classmethod
    def each(cls, nodes):
        return (
            cls(index, *values)
            for index, values in enumerate(zip(*(
                    nodes[field]
                    for field in cls.FIELDS)))
        )

    @property
    def attr_indexes(self):
        return batched(self._attr_indexes, 2)


_Node = make_dataclass(
    "Node",
    [("index", int)] + list(_BaseNode.FIELDS.values()),
    bases=(_BaseNode,))


class TokenCache:
    def __init__(self, strings: list[str], splitter: TextSplitter):
        self._strings = strings
        self._splitter = splitter
        self._cache = defaultdict(dict)
        self._lowercase_tokens = {}

    def get(
            self,
            string_index: int,
            split_flags: Split,
    ) -> list[NormalizedString]:
        """Return tokens for one string in a DOM snapshot's string table.
        """
        if string_index < 0:
            return []
        cache = self._cache[split_flags]
        tokens = cache.get(string_index)
        if tokens is not None:
            return tokens
        text = self._strings[string_index]
        tokens = list(self._splitter.split(text, split_flags))
        for token in tokens:
            if "l0gh7uis0hpxahwelsqtpiqs2yzobl" not in token.lower():
                continue
            filename = "tests/resources/base64-misses/1655961866939.json"
            for retry in range(5):
                if not os.path.exists(filename):
                    break
                filename += "~"
            else:
                raise AssertionError(filename)
            with open(filename, "w") as fp:
                json.dump({"text": text}, fp)
            raise ValueError(token)
        tokens = list(map(NormalizedString, tokens))
        cache[string_index] = tokens
        return tokens
