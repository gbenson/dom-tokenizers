import logging
import weakref

from abc import ABC, abstractmethod

from tokenizers import NormalizedString, PreTokenizedString
from tokenizers.pre_tokenizers import PreTokenizer as _PreTokenizer

from .token_buffer import TokenBuffer

logger = logging.getLogger(__name__)


class PreTokenizer(ABC):
    @classmethod
    def hook_into(cls, tokenizer):
        """Reconfigure `tokenizer` for DOM-aware pre-tokenization.
        """
        cls().bind_to(tokenizer)

    def __init__(self):
        self._tokenizer = None
        self._lowercase_output = False

    def bind_to(self, tokenizer):
        """Reconfigure `tokenizer` to pre-tokenize using `self`.
        """
        if self._tokenizer is not None:
            raise RuntimeError("already bound")
        try:
            backend = tokenizer.backend_tokenizer
        except AttributeError as e:
            raise TypeError("not a tokenizer") from e
        if hasattr(tokenizer, "dom_pre_tokenizer"):
            raise RuntimeError("already bound")

        # Set the cross-links first, to mark both objects as having
        # been bound and prevent either from binding/being bound to
        # anything else regardless of whether this binding succeeds
        # or fails.
        tokenizer.dom_pre_tokenizer = weakref.proxy(self)
        self._tokenizer = weakref.proxy(tokenizer)

        # Install ourself as the tokenizer's pre-tokenizer.
        backend.pre_tokenizer = _PreTokenizer.custom(self)

        # Attempt to detect and postpone any lowercasing applied to
        # our input until after the base64 detection and handling is
        # complete.
        if getattr(backend.normalizer, "lowercase", None) is True:
            backend.normalizer.lowercase = False
            self._lowercase_output = True

    # Entry point

    def pre_tokenize(self, pretok: PreTokenizedString):
        pretok.split(self._pre_tokenize_dom)
    pre_tokenize.__doc__ = _PreTokenizer.pre_tokenize.__doc__

    def _pre_tokenize_dom(
            self,
            index: int,
            split: NormalizedString,
    ) -> list[NormalizedString]:
        try:
            buf = TokenBuffer()
            self.pre_tokenize_dom(buf, split.original)
            return buf.tokens
        except Exception as e:
            logger.exception(f"{type(e).__name__} in pre-tokenizer:")
            raise

    @abstractmethod
    def pre_tokenize_dom(self, buf: TokenBuffer, serialized: str):
        """Transform a serialized DOM into a sequence of tokens.
        """
        raise NotImplementedError
