from .internal.transformers import AutoTokenizer
from .pre_tokenizers import DOMSnapshotPreTokenizer


class DOMSnapshotTokenizer:
    @classmethod
    def from_pretrained(cls, *args, **kwargs):
        tokenizer = AutoTokenizer.from_pretrained(*args, **kwargs)
        DOMSnapshotPreTokenizer.hook_into(tokenizer)
        return tokenizer
