import json

from collections.abc import Iterable
from itertools import chain
from xml.dom import Node

from tokenizers import NormalizedString

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

    @property
    def special_tokens(self):
        return [
            value
            for attr, value in chain.from_iterable(
                    x.__dict__.items()
                    for x in (self.__class__, self._splitter)
            )
            if attr.endswith("token")
        ]

    def pre_tokenize_dom(self, buf: TokenBuffer, serialized: str):
        """Transform a serialized DOM into a sequence of tokens.
        """
        snapshot = json.loads(serialized)

        # Unpack the snapshot if what we have is a raw browser response
        if not any(key in snapshot for key in ("documents", "strings")):
            snapshot = snapshot.get("result", snapshot)

        emitter = TokenEmitter(self._splitter, snapshot)
        for document in snapshot["documents"]:
            nodes = document["nodes"]
            for node_index, node_values in enumerate(zip(
                    nodes["nodeType"],
                    nodes["nodeName"],
                    nodes["nodeValue"],
                    nodes["attributes"])):
                node_type, name_index, value_index, attr_indexes = node_values

                match node_type:
                    case Node.ELEMENT_NODE:
                        buf.append(self.elem_token)
                        buf.extend(emitter.emit(name_index))
                        for attr_index in range(0, len(attr_indexes), 2):
                            buf.append(self.attr_token)
                            buf.extend(emitter.emit(attr_indexes[attr_index]))
                            buf.extend(emitter.emit(attr_indexes[attr_index + 1]))

                    case Node.TEXT_NODE:
                        buf.extend(emitter.emit(value_index))

                    case Node.COMMENT_NODE:
                        buf.append(self.comm_token)
                        buf.extend(emitter.emit(value_index))


class TokenEmitter:
    def __init__(self, splitter: TextSplitter, snapshot: dict):
        self._splitter = splitter
        self._strings = snapshot["strings"]
        self._tokens = {}

    def emit(self, string_index: int) -> Iterable[NormalizedString]:
        """Emit tokens for one string in a DOM snapshot's string table.
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
