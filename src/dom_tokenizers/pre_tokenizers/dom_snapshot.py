from dataclasses import make_dataclass
from xml.dom import Node

from tokenizers import NormalizedString

from ..internal import json
from .compat_itertools import batched
from .html import is_void_element
from .pre_tokenizer import PreTokenizer
from .splitter import TextSplitter
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

        tokens = TokenCache(snapshot["strings"], self._splitter)

        for document in snapshot["documents"]:
            stack = [self._SENTINEL]
            for node in _Node.each(document["nodes"]):
                while stack[-1].index != node.parent_index:
                    self._terminate(buf, tokens, stack.pop())

                match node.type:
                    case Node.ELEMENT_NODE:
                        buf.append("<")
                        buf.extend(tokens.get(node.name_index, lowercase=True))
                        for name_index, value_index in node.attr_indexes:
                            buf.append("_")
                            buf.extend(tokens[name_index])
                            buf.append("=")
                            buf.extend(tokens[value_index])
                        buf.append(">")
                        stack.append(node)

                    case Node.TEXT_NODE:
                        buf.extend(tokens[node.value_index])

                    case Node.DOCUMENT_NODE:
                        stack.append(node)

                    case Node.COMMENT_NODE:
                        buf.append("<!--")
                        buf.extend(tokens[node.value_index])
                        buf.append("-->")

                    case Node.DOCUMENT_TYPE_NODE:
                        buf.append("<!DOCTYPE")
                        buf.extend(tokens[node.name_index])
                        public_index = document["publicId"]
                        if public_index >= 0:
                            buf.append("PUBLIC")
                            buf.extend(tokens[public_index])
                        system_index = document["systemId"]
                        if system_index >= 0:
                            buf.extend(tokens[system_index])
                        buf.append(">")

        for node in reversed(stack[2:]):
            self._terminate(buf, tokens, node)

    @staticmethod
    def _terminate(buf, tokens, node):
        tag = tokens._strings[node.name_index]
        if is_void_element(tag):
            return
        buf.append("</")
        buf.extend(tokens.get(node.name_index, lowercase=True))
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
        self._tokens = {}
        self._lowercase_tokens = {}

    def get(
            self,
            string_index: int,
            *,
            lowercase=False
    ) -> list[NormalizedString]:
        """Return tokens for one string in a DOM snapshot's string table.
        """
        if string_index < 0:
            return []
        cache = self._lowercase_tokens if lowercase else self._tokens
        tokens = cache.get(string_index)
        if tokens is not None:
            return tokens
        text = self._strings[string_index]
        if lowercase:
            text = text.lower()
        tokens = [
            NormalizedString(token)
            for token in self._splitter.split(text)
        ]
        cache[string_index] = tokens
        return tokens

    __getitem__ = get
