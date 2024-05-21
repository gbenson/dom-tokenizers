from typing_extensions import deprecated

from .internal.transformers import AutoTokenizer
from .pre_tokenizers import DOMSnapshotPreTokenizer


@deprecated("use `DOMSnapshotPreTokenizer` instead")
class DOMSnapshotTokenizer:
    @classmethod
    @deprecated("use `DOMSnapshotPreTokenizer.adapt()` instead")
    def from_pretrained(cls, *args, **kwargs):
        tokenizer = AutoTokenizer.from_pretrained(*args, **kwargs)
        DOMSnapshotPreTokenizer.hook_into(tokenizer)
        return tokenizer
