import weakref

from tokenizers.pre_tokenizers import PreTokenizer as _PreTokenizer


class PreTokenizer:
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
