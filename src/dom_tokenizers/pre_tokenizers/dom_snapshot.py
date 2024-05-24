import json

from dataclasses import make_dataclass
from xml.dom import Node

from tokenizers import NormalizedString

from .compat_itertools import batched
from .pre_tokenizer import PreTokenizer
from .splitter import TextSplitter
from .token_buffer import TokenBuffer


class DOMSnapshotPreTokenizer(PreTokenizer):
    """Pre-tokenizer that consumes JSON-serialized DOM snapshots
    and emits tokenized representations of the snapshotted DOMs.
    """
    elem_token = "[TAG]"       # beginning of element name
    attr_token = "[ATTR]"      # beginning of attribute
    comm_token = "[COMMENT]"   # beginning of comment

    def pre_tokenize_dom(self, buf: TokenBuffer, serialized: str):
        """Transform a serialized DOM into a sequence of tokens.
        """
        snapshot = json.loads(serialized)

        # Unpack the snapshot if what we have is a raw browser response
        if not any(key in snapshot for key in ("documents", "strings")):
            snapshot = snapshot.get("result", snapshot)

        tokens = TokenCache(snapshot["strings"], self._splitter)

        for document in snapshot["documents"]:
            for node in _Node.each(document["nodes"]):
                match node.type:
                    case Node.ELEMENT_NODE:
                        buf.append(self.elem_token)
                        buf.extend(tokens[node.name_index])
                        for name_index, value_index in node.attr_indexes:
                            buf.append(self.attr_token)
                            buf.extend(tokens[name_index])
                            buf.extend(tokens[value_index])

                    case Node.TEXT_NODE:
                        buf.extend(tokens[node.value_index])

                    case Node.COMMENT_NODE:
                        buf.append(self.comm_token)
                        buf.extend(tokens[node.value_index])


class _BaseNode:
    FIELDS = {
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

    def __getitem__(self, string_index: int) -> list[NormalizedString]:
        """Return tokens for one string in a DOM snapshot's string table.
        """
        if string_index < 0:
            return []
        tokens = self._tokens.get(string_index)
        if tokens is not None:
            return tokens
        tokens = [
            NormalizedString(token)
            for token in self._splitter.split(self._strings[string_index])
        ]
        self._tokens[string_index] = tokens
        return tokens
