from tokenizers.pre_tokenizers import PreTokenizer

from .internal.transformers import AutoTokenizer
from .pre_tokenizers import DOMSnapshotPreTokenizer


class Tokenizer:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        tokenizer = AutoTokenizer.from_pretrained(*args, **kwargs)
        impl = tokenizer.backend_tokenizer
        pt_impl = cls.PRE_TOKENIZER_CLASS()
        impl.pre_tokenizer = PreTokenizer.custom(pt_impl)
        tokenizer.backend_pre_tokenizer = pt_impl  # so we can find it
        return tokenizer


class DOMSnapshotTokenizer(Tokenizer):
    PRE_TOKENIZER_CLASS = DOMSnapshotPreTokenizer
